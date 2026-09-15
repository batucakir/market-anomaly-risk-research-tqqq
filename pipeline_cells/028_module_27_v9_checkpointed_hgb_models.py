# MODULE 27 — V9 CHECKPOINTED HGB MODELS
# Run in the same notebook, in module order.

# ==============================================================================
# V9 — BLOCK 2A
# LIFECYCLE-SAFE VALUATION POLICY
# + FULL FEATURE / TRAINING PREFLIGHT
# + CHECKPOINTED MULTI-HORIZON HGB PREDICTIONS
# ==============================================================================
#
# EXPENSIVE MODEL FITTING STARTS ONLY AFTER ALL PREFLIGHT CHECKS PASS.
#
# IMPORTANT
# ---------
# NO V9 PORTFOLIO PERFORMANCE IS CALCULATED IN THIS BLOCK.
#
# CHECKPOINTING
# -------------
# Each completed signal date is saved separately to disk.
#
# If execution is interrupted:
#   - rerun this same block;
#   - already completed signal dates are loaded from cache;
#   - only unfinished dates are fitted.
#
# LIFECYCLE POLICY
# ----------------
# Entry:
#   Exact execution-date quote is mandatory.
#
# Existing holding:
#   If an exact scheduled-rebalance quote disappears because the security
#   stops trading / changes lifecycle state, use its LAST OBSERVABLE
#   lifecycle Adj Close on or before the scheduled rebalance date.
#
# Economically, the position is treated as terminated at that last observable
# value and the proceeds earn 0% until the scheduled rebalance.
#
# This fallback:
#   - is NEVER used for new purchases;
#   - does NOT use future information;
#   - does NOT remove the stock ex ante;
#   - does NOT create a strategic cash allocation.
#
# ==============================================================================


import hashlib
import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from IPython.display import display
from sklearn.ensemble import HistGradientBoostingRegressor


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V9_B2A_REQUIRED = [
    "V9_LIFECYCLE_PANEL",
    "V9_BASE_PANEL",
    "V9_CALENDAR",
    "V9_EVALUATION_CALENDAR",
    "V9_EXECUTION_PREFLIGHT",
    "V9_EXECUTION_PREFLIGHT_MISSING",
    "V9_TARGET_HORIZONS",
    "V9_TRAIN_LOOKBACK_SESSIONS",
    "V9_PORTFOLIO_REBALANCE_SESSIONS",
    "V9_RESEARCH_CONTRACT",
    "V9_CONTRACT_FINGERPRINT",
]


V9_B2A_MISSING = [
    name
    for name in V9_B2A_REQUIRED
    if name not in globals()
]


if V9_B2A_MISSING:

    raise RuntimeError(
        "V9 Block 2A is missing required objects: "
        f"{V9_B2A_MISSING}"
    )


print("=" * 132)
print("V9 — BLOCK 2A")
print("LIFECYCLE-SAFE PREFLIGHT + CHECKPOINTED MULTI-HORIZON HGB")
print("=" * 132)


# ==============================================================================
# 1. NORMALIZE CORE TABLES
# ==============================================================================

V9_LIFECYCLE_PANEL = (
    V9_LIFECYCLE_PANEL
    .copy()
    .sort_values(
        [
            "Ticker",
            "Date",
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_LIFECYCLE_PANEL["Date"] = (
    pd.to_datetime(
        V9_LIFECYCLE_PANEL["Date"]
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V9_LIFECYCLE_PANEL["Ticker"] = (
    V9_LIFECYCLE_PANEL["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_BASE_PANEL = (
    V9_BASE_PANEL
    .copy()
)


for date_column in [
    "Date",
    "Execution_Date",
]:

    V9_BASE_PANEL[
        date_column
    ] = (
        pd.to_datetime(
            V9_BASE_PANEL[
                date_column
            ]
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


for horizon_name in V9_TARGET_HORIZONS:

    date_column = (
        f"Target_End_Date_{horizon_name}"
    )

    V9_BASE_PANEL[
        date_column
    ] = (
        pd.to_datetime(
            V9_BASE_PANEL[
                date_column
            ]
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


V9_BASE_PANEL["Ticker"] = (
    V9_BASE_PANEL["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


# ==============================================================================
# 2. REBUILD EXACT FULL-LIFECYCLE PRICE LOOKUP
# ==============================================================================

V9_PRICE_LOOKUP = (
    V9_LIFECYCLE_PANEL[
        [
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    ]
    .dropna()
    .drop_duplicates(
        [
            "Ticker",
            "Date",
        ],
        keep="last",
    )
    .set_index(
        [
            "Ticker",
            "Date",
        ]
    )[
        "Adj_Close"
    ]
    .sort_index()
)


# ==============================================================================
# 3. LIFECYCLE VALUATION HELPER
# ==============================================================================

def v9_last_observable_price(
    ticker,
    scheduled_date,
    not_before=None,
):

    ticker = str(
        ticker
    ).upper().strip()

    scheduled_date = pd.Timestamp(
        scheduled_date
    ).normalize()


    history = (
        V9_LIFECYCLE_PANEL[
            (
                V9_LIFECYCLE_PANEL[
                    "Ticker"
                ]
                ==
                ticker
            )
            &
            (
                V9_LIFECYCLE_PANEL[
                    "Date"
                ]
                <=
                scheduled_date
            )
        ][
            [
                "Date",
                "Adj_Close",
            ]
        ]
        .dropna()
    )


    if not_before is not None:

        not_before = pd.Timestamp(
            not_before
        ).normalize()

        history = (
            history[
                history[
                    "Date"
                ]
                >=
                not_before
            ]
        )


    if history.empty:

        return (
            pd.NaT,
            np.nan,
        )


    history = (
        history
        .sort_values(
            "Date"
        )
    )


    final_row = (
        history.iloc[
            -1
        ]
    )


    price = float(
        final_row[
            "Adj_Close"
        ]
    )


    if (
        not np.isfinite(
            price
        )
        or
        price <= 0
    ):

        return (
            pd.NaT,
            np.nan,
        )


    return (
        pd.Timestamp(
            final_row[
                "Date"
            ]
        ),
        price,
    )


# ==============================================================================
# 4. RESOLVE ALL PREFLIGHT LIFECYCLE GAPS
# ==============================================================================
#
# Missing ENTRY quote:
#     fatal — we cannot execute the trade.
#
# Missing scheduled valuation quote:
#     use the last observable lifecycle quote after entry.
#
# ==============================================================================

V9_LIFECYCLE_RESOLUTION_ROWS = []


if not V9_EXECUTION_PREFLIGHT_MISSING.empty:

    for _, missing_row in (
        V9_EXECUTION_PREFLIGHT_MISSING
        .iterrows()
    ):

        decision = int(
            missing_row[
                "Decision"
            ]
        )


        ticker = str(
            missing_row[
                "Ticker"
            ]
        )


        quote_type = str(
            missing_row[
                "Quote_Type"
            ]
        )


        requested_date = pd.Timestamp(
            missing_row[
                "Requested_Date"
            ]
        )


        event_match = (
            V9_EXECUTION_PREFLIGHT[
                V9_EXECUTION_PREFLIGHT[
                    "Decision"
                ]
                ==
                decision
            ]
        )


        if event_match.empty:

            raise RuntimeError(
                "Could not map lifecycle gap to "
                f"decision {decision}."
            )


        event = (
            event_match.iloc[
                0
            ]
        )


        entry_date = pd.Timestamp(
            event[
                "Execution_Date"
            ]
        )


        if quote_type == "ENTRY":

            resolved_date = pd.NaT
            resolved_price = np.nan
            status = "UNRESOLVED_ENTRY"

        else:

            (
                resolved_date,
                resolved_price,
            ) = v9_last_observable_price(
                ticker=ticker,
                scheduled_date=requested_date,
                not_before=entry_date,
            )


            status = (
                "LAST_OBSERVABLE_TERMINAL_VALUE"
                if np.isfinite(
                    resolved_price
                )
                else
                "UNRESOLVED"
            )


        if pd.notna(
            resolved_date
        ):

            tqqq_dates = (
                pd.DatetimeIndex(
                    V9_CALENDAR[
                        "Date"
                    ]
                )
            )


            stale_sessions = int(
                (
                    (
                        tqqq_dates
                        >
                        resolved_date
                    )
                    &
                    (
                        tqqq_dates
                        <=
                        requested_date
                    )
                )
                .sum()
            )

        else:

            stale_sessions = np.nan


        V9_LIFECYCLE_RESOLUTION_ROWS.append(
            {
                "Decision":
                    decision,

                "Ticker":
                    ticker,

                "Quote_Type":
                    quote_type,

                "Entry_Date":
                    entry_date,

                "Scheduled_Date":
                    requested_date,

                "Resolved_Date":
                    resolved_date,

                "Resolved_Adj_Close":
                    resolved_price,

                "Trading_Sessions_To_Scheduled_Date":
                    stale_sessions,

                "Resolution":
                    status,
            }
        )


V9_LIFECYCLE_RESOLUTIONS = pd.DataFrame(
    V9_LIFECYCLE_RESOLUTION_ROWS
)


if not V9_LIFECYCLE_RESOLUTIONS.empty:

    print(
        "\n1) LIFECYCLE GAP RESOLUTION"
    )

    display(
        V9_LIFECYCLE_RESOLUTIONS
    )


    unresolved = (
        V9_LIFECYCLE_RESOLUTIONS[
            V9_LIFECYCLE_RESOLUTIONS[
                "Resolution"
            ]
            .isin(
                [
                    "UNRESOLVED",
                    "UNRESOLVED_ENTRY",
                ]
            )
        ]
    )


    if not unresolved.empty:

        raise RuntimeError(
            "Lifecycle quote gaps remain unresolved. "
            "Model fitting has NOT started."
        )


else:

    print(
        "\n1) LIFECYCLE GAP RESOLUTION"
    )

    print(
        "[+] No lifecycle quote gaps require resolution."
    )


# ==============================================================================
# 5. LOCK LIFECYCLE VALUATION POLICY
# ==============================================================================

V9_HOLDING_VALUATION_POLICY = {

    "new_position_entry":
        "EXACT_EXECUTION_DATE_QUOTE_REQUIRED",

    "scheduled_holding_valuation":
        "EXACT_QUOTE_IF_AVAILABLE",

    "missing_scheduled_holding_quote":
        (
            "LAST_OBSERVABLE_LIFECYCLE_ADJ_CLOSE_"
            "ON_OR_BEFORE_SCHEDULED_DATE"
        ),

    "post_terminal_value_return":
        "ZERO_UNTIL_SCHEDULED_REBALANCE",

    "economic_interpretation":
        "FORCED_NON_STRATEGIC_CASH_PROCEEDS",

    "future_availability_used_for_signal_selection":
        False,

    "future_missing_quote_exclusion":
        False,
}


V9_RESEARCH_CONTRACT[
    "holding_valuation_policy"
] = V9_HOLDING_VALUATION_POLICY


V9_CONTRACT_STRING = json.dumps(
    V9_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V9_CONTRACT_FINGERPRINT = (
    hashlib.sha256(
        V9_CONTRACT_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


print(
    "\nLifecycle-safe contract fingerprint:"
)

print(
    V9_CONTRACT_FINGERPRINT
)


# ==============================================================================
# 6. BUILD FULL-LIFECYCLE STOCK FEATURES
# ==============================================================================

V9_FEATURE_SOURCE = (
    V9_LIFECYCLE_PANEL
    .copy()
    .sort_values(
        [
            "Ticker",
            "Date",
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_MOMENTUM_WINDOWS = (
    1,
    5,
    21,
    63,
    126,
    252,
)


price_group = (
    V9_FEATURE_SOURCE
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]
)


return_group = (
    V9_FEATURE_SOURCE
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Daily_Return"
    ]
)


for window in V9_MOMENTUM_WINDOWS:

    lagged_price = (
        price_group.shift(
            window
        )
    )


    V9_FEATURE_SOURCE[
        f"V9_LogMom_{window}"
    ] = np.log(
        V9_FEATURE_SOURCE[
            "Adj_Close"
        ]
        /
        lagged_price
    )


V9_FEATURE_SOURCE[
    "V9_Vol_20"
] = (
    return_group
    .transform(
        lambda series:
            series.rolling(
                20,
                min_periods=15,
            ).std()
    )
)


V9_FEATURE_SOURCE[
    "V9_Vol_60"
] = (
    return_group
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).std()
    )
)


V9_FEATURE_SOURCE[
    "V9_Max_63"
] = (
    price_group
    .transform(
        lambda series:
            series.rolling(
                63,
                min_periods=42,
            ).max()
    )
)


V9_FEATURE_SOURCE[
    "V9_Max_252"
] = (
    price_group
    .transform(
        lambda series:
            series.rolling(
                252,
                min_periods=126,
            ).max()
    )
)


V9_FEATURE_SOURCE[
    "V9_Drawdown_63"
] = (
    V9_FEATURE_SOURCE[
        "Adj_Close"
    ]
    /
    V9_FEATURE_SOURCE[
        "V9_Max_63"
    ]
    -
    1.0
)


V9_FEATURE_SOURCE[
    "V9_Drawdown_252"
] = (
    V9_FEATURE_SOURCE[
        "Adj_Close"
    ]
    /
    V9_FEATURE_SOURCE[
        "V9_Max_252"
    ]
    -
    1.0
)


V9_FEATURE_SOURCE[
    "V9_Log_ADV60"
] = np.log(
    V9_FEATURE_SOURCE[
        "Median_Dollar_Volume_60"
    ]
    .clip(
        lower=1.0
    )
)


V9_FEATURE_SOURCE[
    "V9_Log_Relative_Volume"
] = np.log(
    (
        V9_FEATURE_SOURCE[
            "Dollar_Volume"
        ]
        /
        V9_FEATURE_SOURCE[
            "Median_Dollar_Volume_60"
        ]
    )
    .clip(
        lower=1e-8
    )
)


V9_FEATURE_SOURCE[
    "V9_Log_Amihud60"
] = np.log(
    V9_FEATURE_SOURCE[
        "V9_Amihud_60"
    ]
    .clip(
        lower=1e-16
    )
)


# ==============================================================================
# 7. BUILD TQQQ MARKET-STATE FEATURES
# ==============================================================================

V9_MARKET_STATE = (
    V9_LIFECYCLE_PANEL[
        V9_LIFECYCLE_PANEL[
            "Ticker"
        ]
        ==
        "TQQQ"
    ][
        [
            "Date",
            "Adj_Close",
            "Daily_Return",
        ]
    ]
    .drop_duplicates(
        "Date",
        keep="last",
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


for window in V9_MOMENTUM_WINDOWS:

    V9_MARKET_STATE[
        f"V9_TQQQ_LogMom_{window}"
    ] = np.log(
        V9_MARKET_STATE[
            "Adj_Close"
        ]
        /
        V9_MARKET_STATE[
            "Adj_Close"
        ]
        .shift(
            window
        )
    )


V9_MARKET_STATE[
    "V9_TQQQ_Vol_20"
] = (
    V9_MARKET_STATE[
        "Daily_Return"
    ]
    .rolling(
        20,
        min_periods=15,
    )
    .std()
)


V9_MARKET_STATE[
    "V9_TQQQ_Vol_60"
] = (
    V9_MARKET_STATE[
        "Daily_Return"
    ]
    .rolling(
        60,
        min_periods=50,
    )
    .std()
)


V9_MARKET_STATE[
    "V9_TQQQ_Max_63"
] = (
    V9_MARKET_STATE[
        "Adj_Close"
    ]
    .rolling(
        63,
        min_periods=42,
    )
    .max()
)


V9_MARKET_STATE[
    "V9_TQQQ_Max_252"
] = (
    V9_MARKET_STATE[
        "Adj_Close"
    ]
    .rolling(
        252,
        min_periods=126,
    )
    .max()
)


V9_MARKET_STATE[
    "V9_TQQQ_Drawdown_63"
] = (
    V9_MARKET_STATE[
        "Adj_Close"
    ]
    /
    V9_MARKET_STATE[
        "V9_TQQQ_Max_63"
    ]
    -
    1.0
)


V9_MARKET_STATE[
    "V9_TQQQ_Drawdown_252"
] = (
    V9_MARKET_STATE[
        "Adj_Close"
    ]
    /
    V9_MARKET_STATE[
        "V9_TQQQ_Max_252"
    ]
    -
    1.0
)


# ==============================================================================
# 8. MERGE FEATURES INTO THE PIT-ELIGIBLE SIGNAL PANEL
# ==============================================================================

V9_STOCK_FEATURE_COLUMNS = [
    "Date",
    "Ticker",

    "V9_LogMom_1",
    "V9_LogMom_5",
    "V9_LogMom_21",
    "V9_LogMom_63",
    "V9_LogMom_126",
    "V9_LogMom_252",

    "V9_Vol_20",
    "V9_Vol_60",

    "V9_Drawdown_63",
    "V9_Drawdown_252",

    "V9_Log_ADV60",
    "V9_Log_Relative_Volume",
    "V9_Log_Amihud60",
]


V9_MODEL_PANEL = (
    V9_BASE_PANEL
    .merge(
        V9_FEATURE_SOURCE[
            V9_STOCK_FEATURE_COLUMNS
        ],
        on=[
            "Date",
            "Ticker",
        ],
        how="left",
        validate="one_to_one",
    )
)


V9_MARKET_FEATURE_COLUMNS = [
    "Date",

    "V9_TQQQ_LogMom_1",
    "V9_TQQQ_LogMom_5",
    "V9_TQQQ_LogMom_21",
    "V9_TQQQ_LogMom_63",
    "V9_TQQQ_LogMom_126",
    "V9_TQQQ_LogMom_252",

    "V9_TQQQ_Vol_20",
    "V9_TQQQ_Vol_60",

    "V9_TQQQ_Drawdown_63",
    "V9_TQQQ_Drawdown_252",
]


V9_MODEL_PANEL = (
    V9_MODEL_PANEL
    .merge(
        V9_MARKET_STATE[
            V9_MARKET_FEATURE_COLUMNS
        ],
        on="Date",
        how="left",
        validate="many_to_one",
    )
)


# ==============================================================================
# 9. RELATIVE-MOMENTUM FEATURES
# ==============================================================================

for window in V9_MOMENTUM_WINDOWS:

    V9_MODEL_PANEL[
        f"V9_RelMom_{window}"
    ] = (
        V9_MODEL_PANEL[
            f"V9_LogMom_{window}"
        ]
        -
        V9_MODEL_PANEL[
            f"V9_TQQQ_LogMom_{window}"
        ]
    )


# ==============================================================================
# 10. CROSS-SECTIONAL RANK FEATURES
# ==============================================================================

V9_RAW_STOCK_FEATURES = [
    "V9_RelMom_1",
    "V9_RelMom_5",
    "V9_RelMom_21",
    "V9_RelMom_63",
    "V9_RelMom_126",
    "V9_RelMom_252",

    "V9_Vol_20",
    "V9_Vol_60",

    "V9_Drawdown_63",
    "V9_Drawdown_252",

    "V9_Log_ADV60",
    "V9_Log_Relative_Volume",
    "V9_Log_Amihud60",
]


V9_XS_FEATURES = []


for feature in V9_RAW_STOCK_FEATURES:

    rank_name = (
        f"XS_{feature}"
    )


    V9_MODEL_PANEL[
        rank_name
    ] = (
        V9_MODEL_PANEL
        .groupby(
            "Date"
        )[
            feature
        ]
        .rank(
            pct=True,
            method="average",
        )
    )


    V9_XS_FEATURES.append(
        rank_name
    )


V9_MARKET_FEATURES = [
    "V9_TQQQ_LogMom_1",
    "V9_TQQQ_LogMom_5",
    "V9_TQQQ_LogMom_21",
    "V9_TQQQ_LogMom_63",
    "V9_TQQQ_LogMom_126",
    "V9_TQQQ_LogMom_252",

    "V9_TQQQ_Vol_20",
    "V9_TQQQ_Vol_60",

    "V9_TQQQ_Drawdown_63",
    "V9_TQQQ_Drawdown_252",
]


V9_MODEL_FEATURES = (
    V9_XS_FEATURES
    +
    V9_MARKET_FEATURES
)


# ==============================================================================
# 11. MODEL SPECIFICATION — LOCK BEFORE PERFORMANCE
# ==============================================================================

V9_HGB_PARAMS = {

    "loss":
        "squared_error",

    "learning_rate":
        0.1,

    "max_iter":
        100,

    "max_leaf_nodes":
        31,

    "max_depth":
        None,

    "min_samples_leaf":
        20,

    "l2_regularization":
        0.0,

    "max_bins":
        255,

    "early_stopping":
        "auto",

    "validation_fraction":
        0.1,

    "n_iter_no_change":
        10,

    "tol":
        1e-7,

    "random_state":
        0,
}


V9_ALPHA_SPEC = {

    "contract_fingerprint":
        V9_CONTRACT_FINGERPRINT,

    "model_family":
        "HIST_GRADIENT_BOOSTING_REGRESSOR",

    "models":
        "ONE_FIXED_MODEL_PER_HORIZON",

    "target":
        (
            "EXECUTION_ALIGNED_TQQQ_RELATIVE_"
            "LOG_WEALTH_GROWTH_PER_SESSION"
        ),

    "target_horizons":
        dict(
            V9_TARGET_HORIZONS
        ),

    "features":
        tuple(
            V9_MODEL_FEATURES
        ),

    "hgb_params":
        dict(
            V9_HGB_PARAMS
        ),

    "training_dates":
        (
            "LAST_252_FULLY_MATURED_SIGNAL_DATES"
        ),

    "date_weighting":
        "EQUAL_TOTAL_WEIGHT_PER_SIGNAL_DATE",

    "horizon_aggregation":
        (
            "MEDIAN_OF_PREDICTED_PER_SESSION_"
            "LOG_RELATIVE_GROWTH"
        ),

    "post_result_tuning":
        False,
}


V9_ALPHA_SPEC_STRING = json.dumps(
    V9_ALPHA_SPEC,
    sort_keys=True,
    default=str,
)


V9_ALPHA_SPEC_FINGERPRINT = (
    hashlib.sha256(
        V9_ALPHA_SPEC_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


print(
    "\nV9 alpha specification fingerprint:"
)

print(
    V9_ALPHA_SPEC_FINGERPRINT
)


print(
    "Model feature count:",
    len(
        V9_MODEL_FEATURES
    ),
)


# ==============================================================================
# 12. FINAL EVALUATION CALENDAR
# ==============================================================================

V9_MODEL_EVALUATION_CALENDAR = (
    V9_EVALUATION_CALENDAR[
        [
            "Date",
            "Execution_Date",
        ]
    ]
    .copy()
    .dropna()
    .drop_duplicates(
        "Date",
        keep="last",
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


V9_EVALUATION_DATES = (
    V9_MODEL_EVALUATION_CALENDAR[
        "Date"
    ]
    .tolist()
)


if not V9_EVALUATION_DATES:

    raise RuntimeError(
        "V9 evaluation calendar is empty."
    )


# ==============================================================================
# 13. BUILD FAST DATE-INDEX MAP
# ==============================================================================

V9_MODEL_PANEL = (
    V9_MODEL_PANEL
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
    .sort_values(
        [
            "Date",
            "Ticker",
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_DATE_ROW_INDICES = (
    V9_MODEL_PANEL
    .groupby(
        "Date",
        sort=False,
    )
    .indices
)


V9_MODEL_PANEL_DATES = (
    pd.DatetimeIndex(
        V9_MODEL_PANEL[
            "Date"
        ]
        .drop_duplicates()
        .sort_values()
    )
)


# ==============================================================================
# 14. COMPLETE PRE-FIT VALIDATION
# ==============================================================================
#
# EVERYTHING BELOW THIS SECTION MUST PASS BEFORE ANY HGB MODEL IS FIT.
#
# ==============================================================================

V9_PREFIT_ROWS = []


for signal_date in V9_EVALUATION_DATES:

    signal_date = pd.Timestamp(
        signal_date
    )


    if signal_date not in V9_DATE_ROW_INDICES:

        V9_PREFIT_ROWS.append(
            {
                "Signal_Date":
                    signal_date,

                "Check":
                    "CURRENT_FEATURES",

                "Horizon":
                    "ALL",

                "Value":
                    0,

                "Status":
                    "FAIL",
            }
        )

        continue


    current_indices = (
        V9_DATE_ROW_INDICES[
            signal_date
        ]
    )


    current = (
        V9_MODEL_PANEL.iloc[
            current_indices
        ]
        .dropna(
            subset=V9_MODEL_FEATURES
        )
    )


    V9_PREFIT_ROWS.append(
        {
            "Signal_Date":
                signal_date,

            "Check":
                "CURRENT_FEATURES",

            "Horizon":
                "ALL",

            "Value":
                len(
                    current
                ),

            "Status":
                (
                    "PASS"
                    if len(
                        current
                    ) > 0
                    else
                    "FAIL"
                ),
        }
    )


# Earliest evaluation date is the most restrictive
# training-history check. Later dates have weakly more
# matured historical information.

first_signal_date = pd.Timestamp(
    min(
        V9_EVALUATION_DATES
    )
)


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_end_column = (
        f"Target_End_Date_{horizon_name}"
    )


    target_column = (
        f"Log_Relative_Wealth_{horizon_name}"
    )


    mature_date_mask = (
        (
            V9_MODEL_PANEL[
                "Date"
            ]
            <
            first_signal_date
        )
        &
        (
            V9_MODEL_PANEL[
                target_end_column
            ]
            <=
            first_signal_date
        )
    )


    mature_dates = (
        V9_MODEL_PANEL.loc[
            mature_date_mask
            &
            V9_MODEL_PANEL[
                target_column
            ].notna(),
            "Date",
        ]
        .drop_duplicates()
        .sort_values()
    )


    mature_date_count = len(
        mature_dates
    )


    V9_PREFIT_ROWS.append(
        {
            "Signal_Date":
                first_signal_date,

            "Check":
                "MATURE_TRAINING_HISTORY",

            "Horizon":
                horizon_name,

            "Value":
                mature_date_count,

            "Status":
                (
                    "PASS"
                    if mature_date_count
                    >=
                    V9_TRAIN_LOOKBACK_SESSIONS
                    else
                    "FAIL"
                ),
        }
    )


V9_PREFIT_AUDIT = pd.DataFrame(
    V9_PREFIT_ROWS
)


print(
    "\n2) COMPLETE PRE-FIT AUDIT"
)


display(
    V9_PREFIT_AUDIT
)


if (
    V9_PREFIT_AUDIT[
        "Status"
    ]
    !=
    "PASS"
).any():

    raise RuntimeError(
        "V9 pre-fit validation failed. "
        "NO HGB model has been fitted."
    )


print(
    "\n[+] ALL DATA / FEATURE / TRAINING PREFLIGHT CHECKS PASSED."
)


# ==============================================================================
# 15. CHECKPOINT DIRECTORY — TEST WRITABILITY BEFORE FITTING
# ==============================================================================

V9_CACHE_ROOT = (
    Path.cwd()
    /
    "restored_v9_cache"
)


V9_CACHE_DIR = (
    V9_CACHE_ROOT
    /
    (
        "block2a_"
        +
        V9_ALPHA_SPEC_FINGERPRINT[
            :16
        ]
    )
)


V9_CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


V9_CACHE_WRITE_TEST = (
    V9_CACHE_DIR
    /
    ".write_test"
)


try:

    with open(
        V9_CACHE_WRITE_TEST,
        "wb",
    ) as handle:

        handle.write(
            b"V9"
        )


    V9_CACHE_WRITE_TEST.unlink()


except Exception as error:

    raise RuntimeError(
        "V9 checkpoint directory is not writable. "
        "NO model fitting has started."
    ) from error


print(
    "\nCheckpoint directory:"
)

print(
    V9_CACHE_DIR
)


print(
    "[+] Checkpoint directory is writable."
)


# ==============================================================================
# 16. CHECKPOINT HELPERS
# ==============================================================================

def v9_checkpoint_path(
    signal_date,
):

    signal_date = pd.Timestamp(
        signal_date
    )

    return (
        V9_CACHE_DIR
        /
        (
            "prediction_"
            +
            signal_date.strftime(
                "%Y%m%d"
            )
            +
            ".pkl"
        )
    )


def v9_atomic_pickle_dump(
    payload,
    destination,
):

    destination = Path(
        destination
    )


    temporary = destination.with_suffix(
        ".tmp"
    )


    with open(
        temporary,
        "wb",
    ) as handle:

        pickle.dump(
            payload,
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )


    os.replace(
        temporary,
        destination,
    )


def v9_load_valid_checkpoint(
    signal_date,
):

    path = v9_checkpoint_path(
        signal_date
    )


    if not path.exists():

        return None


    try:

        with open(
            path,
            "rb",
        ) as handle:

            payload = pickle.load(
                handle
            )


    except Exception:

        return None


    if not isinstance(
        payload,
        dict,
    ):

        return None


    if (
        payload.get(
            "alpha_spec_fingerprint"
        )
        !=
        V9_ALPHA_SPEC_FINGERPRINT
    ):

        return None


    cached_date = pd.Timestamp(
        payload.get(
            "signal_date"
        )
    ).normalize()


    expected_date = pd.Timestamp(
        signal_date
    ).normalize()


    if cached_date != expected_date:

        return None


    predictions = payload.get(
        "predictions"
    )


    if not isinstance(
        predictions,
        pd.DataFrame,
    ):

        return None


    required_prediction_columns = [
        "Date",
        "Execution_Date",
        "Ticker",
        "Expected_Relative_Log_Growth_21",
    ]


    if any(
        column
        not in predictions.columns
        for column
        in required_prediction_columns
    ):

        return None


    return payload


# ==============================================================================
# 17. CHECK EXISTING CACHE BEFORE FITTING
# ==============================================================================

existing_cache_dates = []


for signal_date in V9_EVALUATION_DATES:

    cached = v9_load_valid_checkpoint(
        signal_date
    )


    if cached is not None:

        existing_cache_dates.append(
            pd.Timestamp(
                signal_date
            )
        )


print(
    "\nExisting valid checkpoints:",
    f"{len(existing_cache_dates)}/"
    f"{len(V9_EVALUATION_DATES)}",
)


print(
    "Remaining decisions to fit:",
    (
        len(
            V9_EVALUATION_DATES
        )
        -
        len(
            existing_cache_dates
        )
    ),
)


# ==============================================================================
# 18. CHECKPOINTED WALK-FORWARD MODEL FITTING
# ==============================================================================

V9_NEWLY_FITTED_DATES = []

V9_LOADED_FROM_CACHE_DATES = []


for decision_number, signal_date in enumerate(
    V9_EVALUATION_DATES,
    start=1,
):

    signal_date = pd.Timestamp(
        signal_date
    )


    # --------------------------------------------------------------------------
    # Try checkpoint first.
    # --------------------------------------------------------------------------

    cached_payload = (
        v9_load_valid_checkpoint(
            signal_date
        )
    )


    if cached_payload is not None:

        V9_LOADED_FROM_CACHE_DATES.append(
            signal_date
        )


        print(
            f"[V9] Decision "
            f"{decision_number:02d}/"
            f"{len(V9_EVALUATION_DATES):02d} "
            f"| signal={signal_date.date()} "
            f"| CACHE"
        )


        continue


    # --------------------------------------------------------------------------
    # Current prediction cross-section.
    # --------------------------------------------------------------------------

    current_indices = (
        V9_DATE_ROW_INDICES[
            signal_date
        ]
    )


    current = (
        V9_MODEL_PANEL.iloc[
            current_indices
        ]
        .dropna(
            subset=V9_MODEL_FEATURES
        )
        .copy()
    )


    if current.empty:

        raise RuntimeError(
            "Unexpected empty current feature cross-section "
            f"at {signal_date.date()}."
        )


    current_predictions = (
        current[
            [
                "Date",
                "Execution_Date",
                "Ticker",

                "Adj_Close",
                "Median_Dollar_Volume_60",

                "V9_Realized_Vol_60",
                "V9_Amihud_60",
                "V9_AUM_to_ADV",
                "V9_Full_AUM_Impact_Scale",
            ]
        ]
        .copy()
    )


    decision_fit_audit = []


    print(
        f"[V9] Decision "
        f"{decision_number:02d}/"
        f"{len(V9_EVALUATION_DATES):02d} "
        f"| signal={signal_date.date()} "
        f"| stocks={len(current):,} "
        f"| FITTING"
    )


    # --------------------------------------------------------------------------
    # Seven fixed horizons.
    # --------------------------------------------------------------------------

    for horizon_name, horizon_sessions in (
        V9_TARGET_HORIZONS.items()
    ):

        target_column = (
            f"Log_Relative_Wealth_{horizon_name}"
        )


        target_end_column = (
            f"Target_End_Date_{horizon_name}"
        )


        # ----------------------------------------------------------------------
        # Select fully matured historical dates using the calendar,
        # not future stock availability.
        # ----------------------------------------------------------------------

        matured_date_rows = (
            V9_MODEL_PANEL[
                (
                    V9_MODEL_PANEL[
                        "Date"
                    ]
                    <
                    signal_date
                )
                &
                (
                    V9_MODEL_PANEL[
                        target_end_column
                    ]
                    <=
                    signal_date
                )
                &
                (
                    V9_MODEL_PANEL[
                        target_column
                    ].notna()
                )
            ][
                "Date"
            ]
            .drop_duplicates()
            .sort_values()
        )


        if (
            len(
                matured_date_rows
            )
            <
            V9_TRAIN_LOOKBACK_SESSIONS
        ):

            raise RuntimeError(
                "Unexpected insufficient matured history "
                f"for {horizon_name} at "
                f"{signal_date.date()}."
            )


        selected_dates = (
            matured_date_rows.iloc[
                -V9_TRAIN_LOOKBACK_SESSIONS:
            ]
        )


        # ----------------------------------------------------------------------
        # Use the pre-built date -> row-index map.
        # ----------------------------------------------------------------------

        selected_index_parts = [
            V9_DATE_ROW_INDICES[
                pd.Timestamp(
                    date
                )
            ]
            for date in selected_dates
            if pd.Timestamp(
                date
            )
            in V9_DATE_ROW_INDICES
        ]


        if not selected_index_parts:

            raise RuntimeError(
                "Training index construction failed."
            )


        selected_indices = np.concatenate(
            selected_index_parts
        )


        train = (
            V9_MODEL_PANEL.iloc[
                selected_indices
            ]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .dropna(
                subset=(
                    V9_MODEL_FEATURES
                    +
                    [
                        target_column,
                    ]
                )
            )
            .copy()
        )


        if train.empty:

            raise RuntimeError(
                "Training sample unexpectedly empty "
                f"for {horizon_name}."
            )


        train[
            "V9_Model_Target"
        ] = (
            train[
                target_column
            ]
            /
            float(
                horizon_sessions
            )
        )


        # ----------------------------------------------------------------------
        # Equal total influence for each historical signal date.
        # ----------------------------------------------------------------------

        date_counts = (
            train
            .groupby(
                "Date"
            )[
                "Ticker"
            ]
            .transform(
                "count"
            )
            .astype(float)
        )


        sample_weight = (
            1.0
            /
            date_counts
        )


        sample_weight = (
            sample_weight
            /
            sample_weight.mean()
        )


        X_train = (
            train[
                V9_MODEL_FEATURES
            ]
            .to_numpy(
                dtype=float
            )
        )


        y_train = (
            train[
                "V9_Model_Target"
            ]
            .to_numpy(
                dtype=float
            )
        )


        X_current = (
            current[
                V9_MODEL_FEATURES
            ]
            .to_numpy(
                dtype=float
            )
        )


        if (
            not np.all(
                np.isfinite(
                    X_train
                )
            )
            or
            not np.all(
                np.isfinite(
                    y_train
                )
            )
            or
            not np.all(
                np.isfinite(
                    X_current
                )
            )
        ):

            raise RuntimeError(
                "Non-finite model matrix survived pre-fit cleaning."
            )


        model = HistGradientBoostingRegressor(
            **V9_HGB_PARAMS
        )


        model.fit(
            X_train,
            y_train,
            sample_weight=(
                sample_weight.to_numpy(
                    dtype=float
                )
            ),
        )


        prediction = model.predict(
            X_current
        )


        if not np.all(
            np.isfinite(
                prediction
            )
        ):

            raise RuntimeError(
                "Non-finite HGB predictions produced."
            )


        current_predictions[
            f"Pred_PerSession_{horizon_name}"
        ] = prediction


        decision_fit_audit.append(
            {
                "Signal_Date":
                    signal_date,

                "Horizon":
                    horizon_name,

                "Training_Dates":
                    len(
                        selected_dates
                    ),

                "Training_Rows":
                    len(
                        train
                    ),

                "Prediction_Rows":
                    len(
                        current
                    ),
            }
        )


    # --------------------------------------------------------------------------
    # Fixed multi-horizon aggregation.
    # --------------------------------------------------------------------------

    prediction_columns = [
        f"Pred_PerSession_{horizon_name}"
        for horizon_name
        in V9_TARGET_HORIZONS
    ]


    if current_predictions[
        prediction_columns
    ].isna().any().any():

        raise RuntimeError(
            "A completed decision contains missing horizon predictions."
        )


    current_predictions[
        "Pred_PerSession_Median"
    ] = (
        current_predictions[
            prediction_columns
        ]
        .median(
            axis=1
        )
    )


    current_predictions[
        "Expected_Relative_Log_Growth_21"
    ] = (
        current_predictions[
            "Pred_PerSession_Median"
        ]
        *
        V9_PORTFOLIO_REBALANCE_SESSIONS
    )


    # --------------------------------------------------------------------------
    # Save ONLY after the entire decision completed successfully.
    # --------------------------------------------------------------------------

    checkpoint_payload = {

        "alpha_spec_fingerprint":
            V9_ALPHA_SPEC_FINGERPRINT,

        "contract_fingerprint":
            V9_CONTRACT_FINGERPRINT,

        "signal_date":
            signal_date,

        "predictions":
            current_predictions,

        "fit_audit":
            pd.DataFrame(
                decision_fit_audit
            ),
    }


    v9_atomic_pickle_dump(
        checkpoint_payload,
        v9_checkpoint_path(
            signal_date
        ),
    )


    V9_NEWLY_FITTED_DATES.append(
        signal_date
    )


    print(
        "     [+] decision checkpoint saved"
    )


# ==============================================================================
# 19. RELOAD EVERY DECISION FROM DISK
# ==============================================================================
#
# The final in-memory result is constructed ONLY from validated checkpoints.
#
# ==============================================================================

V9_ALL_PREDICTION_PARTS = []

V9_ALL_FIT_AUDIT_PARTS = []


for signal_date in V9_EVALUATION_DATES:

    payload = v9_load_valid_checkpoint(
        signal_date
    )


    if payload is None:

        raise RuntimeError(
            "Missing or invalid final checkpoint for "
            f"{pd.Timestamp(signal_date).date()}."
        )


    V9_ALL_PREDICTION_PARTS.append(
        payload[
            "predictions"
        ]
    )


    V9_ALL_FIT_AUDIT_PARTS.append(
        payload[
            "fit_audit"
        ]
    )


V9_ALPHA_PREDICTIONS = (
    pd.concat(
        V9_ALL_PREDICTION_PARTS,
        ignore_index=True,
    )
    .sort_values(
        [
            "Date",
            "Ticker",
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_MODEL_FIT_AUDIT = (
    pd.concat(
        V9_ALL_FIT_AUDIT_PARTS,
        ignore_index=True,
    )
    .sort_values(
        [
            "Signal_Date",
            "Horizon",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 20. FINAL CHECKPOINT INTEGRITY
# ==============================================================================

expected_dates = set(
    pd.Timestamp(
        date
    )
    for date
    in V9_EVALUATION_DATES
)


actual_dates = set(
    pd.Timestamp(
        date
    )
    for date
    in V9_ALPHA_PREDICTIONS[
        "Date"
    ].unique()
)


if actual_dates != expected_dates:

    missing_dates = sorted(
        expected_dates
        -
        actual_dates
    )


    extra_dates = sorted(
        actual_dates
        -
        expected_dates
    )


    raise RuntimeError(
        "Final checkpoint calendar mismatch. "
        f"Missing={missing_dates}, "
        f"Extra={extra_dates}"
    )


if V9_ALPHA_PREDICTIONS.duplicated(
    [
        "Date",
        "Ticker",
    ]
).any():

    raise RuntimeError(
        "Duplicate prediction ticker-date rows detected."
    )


# ==============================================================================
# 21. NON-PERFORMANCE SUMMARY
# ==============================================================================

V9_BLOCK2A_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Evaluation decisions",
            "Target horizons",
            "Model features",
            "Prediction rows",
            "Decisions loaded from previous cache",
            "Decisions newly fitted",
            "Final valid checkpoints",
            "Lifecycle quote gaps resolved",
            "V9 portfolio performance calculated",
        ],

        "Value": [
            len(
                V9_EVALUATION_DATES
            ),

            len(
                V9_TARGET_HORIZONS
            ),

            len(
                V9_MODEL_FEATURES
            ),

            len(
                V9_ALPHA_PREDICTIONS
            ),

            len(
                V9_LOADED_FROM_CACHE_DATES
            ),

            len(
                V9_NEWLY_FITTED_DATES
            ),

            len(
                actual_dates
            ),

            len(
                V9_LIFECYCLE_RESOLUTIONS
            ),

            False,
        ],
    }
)


print(
    "\n3) BLOCK 2A FINAL SUMMARY"
)


display(
    V9_BLOCK2A_SUMMARY
)


print(
    "\n4) MODEL FIT AUDIT — LAST 14 ROWS"
)


display(
    V9_MODEL_FIT_AUDIT
    .tail(
        14
    )
)


print("\nINTEGRITY:")
print("[+] GOGO lifecycle problem is repaired.")
print("[+] HLX-style disappearance is handled causally.")
print("[+] Exact quotes are mandatory for every new purchase.")
print("[+] PIT eligibility remains causal.")
print("[+] Full lifecycle history is used for features and labels.")
print("[+] Seven fixed horizons are preserved.")
print("[+] 252 fully matured dates are used for every fit.")
print("[+] Every completed decision is checkpointed to disk.")
print("[+] Interrupted execution can resume without refitting completed dates.")
print("[+] No V9 portfolio performance has been calculated.")

print(
    "\nNEXT:"
)

print(
    "V9 BLOCK 2B — COST-AWARE STOCK-SLEEVE CONSTRUCTION "
    "USING THE CACHED PREDICTIONS."
)

print("=" * 132)
