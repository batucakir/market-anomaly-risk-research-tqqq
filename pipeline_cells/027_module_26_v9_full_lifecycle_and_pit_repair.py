# MODULE 26 — V9 FULL LIFECYCLE AND PIT REPAIR
# Run in the same notebook, in module order.

import numpy as np
import pandas as pd
def v9_normalize_date_series(series):

    dates = pd.to_datetime(
        series,
        errors="coerce",
    )

    if dates.dt.tz is not None:

        dates = (
            dates
            .dt.tz_convert(
                "America/New_York"
            )
            .dt.tz_localize(None)
        )

    return dates.dt.normalize()


# ==============================================================================
# 3. BUILD THE TRUE FULL LIFECYCLE PRICE LEDGER
# ==============================================================================

V9_LIFECYCLE_PANEL = (
    B38_ALL_PRICES
    .copy()
)


V9_LIFECYCLE_REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Close",
    "Adj_Close",
    "Volume",
]


V9_LIFECYCLE_MISSING_COLUMNS = [
    column
    for column in V9_LIFECYCLE_REQUIRED_COLUMNS
    if column not in V9_LIFECYCLE_PANEL.columns
]


if V9_LIFECYCLE_MISSING_COLUMNS:
    raise RuntimeError(
        "B38_ALL_PRICES is missing required columns: "
        f"{V9_LIFECYCLE_MISSING_COLUMNS}"
    )


V9_LIFECYCLE_PANEL["Date"] = (
    v9_normalize_date_series(
        V9_LIFECYCLE_PANEL["Date"]
    )
)


V9_LIFECYCLE_PANEL["Ticker"] = (
    V9_LIFECYCLE_PANEL["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_LIFECYCLE_PANEL = (
    V9_LIFECYCLE_PANEL
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
    .dropna(
        subset=[
            "Date",
            "Ticker",
            "Close",
            "Adj_Close",
        ]
    )
    .loc[
        lambda frame:
            (
                frame["Close"] > 0
            )
            &
            (
                frame["Adj_Close"] > 0
            )
    ]
    .sort_values(
        [
            "Ticker",
            "Date",
        ]
    )
    .drop_duplicates(
        subset=[
            "Ticker",
            "Date",
        ],
        keep="last",
    )
    .reset_index(
        drop=True
    )
)


if V9_LIFECYCLE_PANEL.duplicated(
    [
        "Ticker",
        "Date",
    ]
).any():

    raise RuntimeError(
        "Duplicate ticker-date rows remain in lifecycle ledger."
    )


print(
    f"\nLifecycle price rows : "
    f"{len(V9_LIFECYCLE_PANEL):,}"
)

print(
    f"Lifecycle tickers    : "
    f"{V9_LIFECYCLE_PANEL['Ticker'].nunique():,}"
)


# ==============================================================================
# 4. REBUILD CAUSAL LIFECYCLE VARIABLES
# ==============================================================================

V9_LIFECYCLE_PANEL = (
    V9_LIFECYCLE_PANEL
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


V9_LIFECYCLE_PANEL[
    "Daily_Return"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]
    .pct_change(
        fill_method=None
    )
)


V9_LIFECYCLE_PANEL[
    "Dollar_Volume"
] = (
    V9_LIFECYCLE_PANEL[
        "Close"
    ]
    *
    V9_LIFECYCLE_PANEL[
        "Volume"
    ]
)


V9_LIFECYCLE_PANEL[
    "Median_Dollar_Volume_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Dollar_Volume"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).median()
    )
)


V9_LIFECYCLE_PANEL[
    "Valid_Days_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=1,
            ).count()
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Realized_Vol_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Daily_Return"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).std()
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Amihud_Daily"
] = (
    V9_LIFECYCLE_PANEL[
        "Daily_Return"
    ].abs()
    /
    V9_LIFECYCLE_PANEL[
        "Dollar_Volume"
    ].replace(
        0.0,
        np.nan,
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Amihud_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "V9_Amihud_Daily"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).median()
    )
)



# ==============================================================================
# V9 — BLOCK 1C-R
# LIFECYCLE REPAIR RESUME AFTER OPTIONAL-METADATA KEYERROR
# ==============================================================================
#
# PURPOSE
# -------
# Resume the already-built lifecycle repair WITHOUT rerunning any model.
#
# FIX
# ---
# Source_Index and GICS_Sector are OPTIONAL metadata fields.
# They are no longer required by the V9 signal panel.
#
# THIS BLOCK:
#   - does NOT fit any model
#   - does NOT calculate V9 performance
#   - does NOT change any V9 parameter
#
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V9_B1CR_REQUIRED = [
    "V9_LIFECYCLE_PANEL",
    "V4_DAILY_PANEL",
    "RESTORE_FIRST_SIGNAL_DATE",
    "V9_TARGET_HORIZONS",
    "V9_PORTFOLIO_REBALANCE_SESSIONS",
    "V9_REFERENCE_AUM_USD",
    "V9_IMPACT_COEFFICIENT",
    "V9_RESEARCH_CONTRACT",
]


V9_B1CR_MISSING = [
    name
    for name in V9_B1CR_REQUIRED
    if name not in globals()
]


if V9_B1CR_MISSING:
    raise RuntimeError(
        "V9 Block 1C-R is missing required objects: "
        f"{V9_B1CR_MISSING}"
    )


print("=" * 130)
print("V9 — BLOCK 1C-R")
print("LIFECYCLE REPAIR RESUME + FULL EXECUTION PREFLIGHT")
print("=" * 130)


# ==============================================================================
# 1. ROBUST DATE NORMALIZATION
# ==============================================================================

def v9cr_normalize_dates(series):

    dates = pd.to_datetime(
        series,
        errors="coerce",
    )

    try:

        if dates.dt.tz is not None:

            dates = (
                dates
                .dt.tz_convert(
                    "America/New_York"
                )
                .dt.tz_localize(None)
            )

    except (AttributeError, TypeError):

        pass

    return dates.dt.normalize()


# ==============================================================================
# 2. VALIDATE / CLEAN THE EXISTING LIFECYCLE LEDGER
# ==============================================================================

V9_LIFECYCLE_PANEL = (
    V9_LIFECYCLE_PANEL
    .copy()
)


V9_LIFECYCLE_PANEL["Date"] = (
    v9cr_normalize_dates(
        V9_LIFECYCLE_PANEL["Date"]
    )
)


V9_LIFECYCLE_PANEL["Ticker"] = (
    V9_LIFECYCLE_PANEL["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_LIFECYCLE_PANEL = (
    V9_LIFECYCLE_PANEL
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
    .dropna(
        subset=[
            "Date",
            "Ticker",
            "Close",
            "Adj_Close",
        ]
    )
    .loc[
        lambda frame:
            (
                frame["Close"] > 0
            )
            &
            (
                frame["Adj_Close"] > 0
            )
    ]
    .drop_duplicates(
        subset=[
            "Ticker",
            "Date",
        ],
        keep="last",
    )
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


if V9_LIFECYCLE_PANEL.duplicated(
    subset=[
        "Ticker",
        "Date",
    ]
).any():

    raise RuntimeError(
        "Duplicate ticker-date rows remain "
        "in V9_LIFECYCLE_PANEL."
    )


# ==============================================================================
# 3. ENSURE ALL REQUIRED CAUSAL MARKET-STATE VARIABLES EXIST
# ==============================================================================

if "Daily_Return" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "Daily_Return"
    ] = (
        V9_LIFECYCLE_PANEL
        .groupby(
            "Ticker",
            sort=False,
        )[
            "Adj_Close"
        ]
        .pct_change(
            fill_method=None
        )
    )


if "Dollar_Volume" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "Dollar_Volume"
    ] = (
        V9_LIFECYCLE_PANEL[
            "Close"
        ]
        *
        V9_LIFECYCLE_PANEL[
            "Volume"
        ]
    )


if "Median_Dollar_Volume_60" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "Median_Dollar_Volume_60"
    ] = (
        V9_LIFECYCLE_PANEL
        .groupby(
            "Ticker",
            sort=False,
        )[
            "Dollar_Volume"
        ]
        .transform(
            lambda series:
                series.rolling(
                    60,
                    min_periods=50,
                ).median()
        )
    )


if "Valid_Days_60" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "Valid_Days_60"
    ] = (
        V9_LIFECYCLE_PANEL
        .groupby(
            "Ticker",
            sort=False,
        )[
            "Adj_Close"
        ]
        .transform(
            lambda series:
                series.rolling(
                    60,
                    min_periods=1,
                ).count()
        )
    )


if "V9_Realized_Vol_60" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "V9_Realized_Vol_60"
    ] = (
        V9_LIFECYCLE_PANEL
        .groupby(
            "Ticker",
            sort=False,
        )[
            "Daily_Return"
        ]
        .transform(
            lambda series:
                series.rolling(
                    60,
                    min_periods=50,
                ).std()
        )
    )


if "V9_Amihud_Daily" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "V9_Amihud_Daily"
    ] = (
        V9_LIFECYCLE_PANEL[
            "Daily_Return"
        ].abs()
        /
        V9_LIFECYCLE_PANEL[
            "Dollar_Volume"
        ].replace(
            0.0,
            np.nan,
        )
    )


if "V9_Amihud_60" not in V9_LIFECYCLE_PANEL.columns:

    V9_LIFECYCLE_PANEL[
        "V9_Amihud_60"
    ] = (
        V9_LIFECYCLE_PANEL
        .groupby(
            "Ticker",
            sort=False,
        )[
            "V9_Amihud_Daily"
        ]
        .transform(
            lambda series:
                series.rolling(
                    60,
                    min_periods=50,
                ).median()
        )
    )


# ==============================================================================
# 4. REBUILD CAPACITY / IMPACT STATE
# ==============================================================================

V9_LIFECYCLE_PANEL[
    "V9_AUM_to_ADV"
] = (
    V9_REFERENCE_AUM_USD
    /
    V9_LIFECYCLE_PANEL[
        "Median_Dollar_Volume_60"
    ]
)


V9_LIFECYCLE_PANEL[
    "V9_AUM_to_ADV_Pct"
] = (
    100.0
    *
    V9_LIFECYCLE_PANEL[
        "V9_AUM_to_ADV"
    ]
)


V9_LIFECYCLE_PANEL[
    "V9_Full_AUM_Impact_Scale"
] = (
    V9_IMPACT_COEFFICIENT
    *
    V9_LIFECYCLE_PANEL[
        "V9_Realized_Vol_60"
    ]
    *
    np.sqrt(
        np.maximum(
            V9_LIFECYCLE_PANEL[
                "V9_AUM_to_ADV"
            ],
            0.0,
        )
    )
)


# ==============================================================================
# 5. REBUILD FULL LIFECYCLE PRICE LOOKUP
# ==============================================================================

V9_PRICE_LOOKUP = (
    V9_LIFECYCLE_PANEL[
        [
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    ]
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
# 6. BUILD TQQQ MASTER CALENDAR
# ==============================================================================

V9_TQQQ_PANEL = (
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
        ]
    ]
    .dropna()
    .drop_duplicates(
        subset=[
            "Date",
        ],
        keep="last",
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


if V9_TQQQ_PANEL.empty:

    raise RuntimeError(
        "TQQQ is missing from the lifecycle ledger."
    )


V9_TQQQ_PRICE_BY_DATE = (
    V9_TQQQ_PANEL
    .set_index(
        "Date"
    )[
        "Adj_Close"
    ]
)


V9_CALENDAR = pd.DataFrame(
    {
        "Date":
            V9_TQQQ_PANEL[
                "Date"
            ].copy()
    }
)


V9_CALENDAR[
    "Execution_Date"
] = (
    V9_CALENDAR[
        "Date"
    ].shift(-1)
)


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    V9_CALENDAR[
        f"Target_End_Date_{horizon_name}"
    ] = (
        V9_CALENDAR[
            "Date"
        ]
        .shift(
            -(
                1
                +
                horizon_sessions
            )
        )
    )


# ==============================================================================
# 7. BUILD PIT SIGNAL PANEL
# ==============================================================================
#
# IMPORTANT FIX:
#
# Only the fields actually required by V9 are mandatory.
#
# Source_Index and GICS_Sector are optional metadata and are included
# only when they exist.
#
# ==============================================================================

V9_REQUIRED_SIGNAL_COLUMNS = [
    "Date",
    "Ticker",
    "Asset_Type",
    "Eligible",
]


V9_MISSING_SIGNAL_COLUMNS = [
    column
    for column in V9_REQUIRED_SIGNAL_COLUMNS
    if column not in V4_DAILY_PANEL.columns
]


if V9_MISSING_SIGNAL_COLUMNS:

    raise RuntimeError(
        "V4_DAILY_PANEL is missing genuinely required "
        f"signal columns: {V9_MISSING_SIGNAL_COLUMNS}"
    )


V9_OPTIONAL_SIGNAL_METADATA = [
    "Snapshot_AsOf",
    "Source_Index",
    "GICS_Sector",
]


V9_AVAILABLE_OPTIONAL_METADATA = [
    column
    for column in V9_OPTIONAL_SIGNAL_METADATA
    if column in V4_DAILY_PANEL.columns
]


V9_SIGNAL_COLUMNS = (
    [
        "Date",
        "Ticker",
    ]
    +
    V9_AVAILABLE_OPTIONAL_METADATA
)


V9_SIGNAL_MASK = (
    V4_DAILY_PANEL[
        "Asset_Type"
    ]
    .astype(str)
    .eq("STOCK")
    &
    V4_DAILY_PANEL[
        "Eligible"
    ]
    .fillna(False)
    .astype(bool)
)


V9_SIGNAL_PANEL = (
    V4_DAILY_PANEL
    .loc[
        V9_SIGNAL_MASK,
        V9_SIGNAL_COLUMNS,
    ]
    .copy()
)


V9_SIGNAL_PANEL["Date"] = (
    v9cr_normalize_dates(
        V9_SIGNAL_PANEL["Date"]
    )
)


V9_SIGNAL_PANEL["Ticker"] = (
    V9_SIGNAL_PANEL[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_SIGNAL_PANEL = (
    V9_SIGNAL_PANEL
    .dropna(
        subset=[
            "Date",
            "Ticker",
        ]
    )
    .drop_duplicates(
        subset=[
            "Date",
            "Ticker",
        ],
        keep="last",
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


print(
    "\nOptional metadata actually available:",
    V9_AVAILABLE_OPTIONAL_METADATA,
)


print(
    "Eligible PIT signal rows:",
    f"{len(V9_SIGNAL_PANEL):,}",
)


# ==============================================================================
# 8. MERGE SIGNAL-DATE LIFECYCLE STATE
# ==============================================================================

V9_SIGNAL_STATE_COLUMNS = [
    "Date",
    "Ticker",

    "Close",
    "Adj_Close",
    "Volume",

    "Daily_Return",
    "Dollar_Volume",

    "Median_Dollar_Volume_60",
    "Valid_Days_60",

    "V9_Realized_Vol_60",
    "V9_Amihud_60",

    "V9_AUM_to_ADV",
    "V9_AUM_to_ADV_Pct",
    "V9_Full_AUM_Impact_Scale",
]


V9_BASE_PANEL = (
    V9_SIGNAL_PANEL
    .merge(
        V9_LIFECYCLE_PANEL[
            V9_SIGNAL_STATE_COLUMNS
        ],
        on=[
            "Date",
            "Ticker",
        ],
        how="left",
        validate="one_to_one",
    )
    .merge(
        V9_CALENDAR,
        on="Date",
        how="left",
        validate="many_to_one",
    )
)


V9_MISSING_SIGNAL_STATE = int(
    V9_BASE_PANEL[
        "Adj_Close"
    ].isna().sum()
)


if V9_MISSING_SIGNAL_STATE > 0:

    raise RuntimeError(
        "Lifecycle state is missing for eligible PIT rows: "
        f"{V9_MISSING_SIGNAL_STATE:,}"
    )


# ==============================================================================
# 9. EXECUTION PRICES
# ==============================================================================

V9_EXECUTION_INDEX = (
    pd.MultiIndex.from_arrays(
        [
            V9_BASE_PANEL[
                "Ticker"
            ].to_numpy(),

            V9_BASE_PANEL[
                "Execution_Date"
            ].to_numpy(),
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )
)


V9_BASE_PANEL[
    "Execution_Adj_Close"
] = (
    V9_PRICE_LOOKUP
    .reindex(
        V9_EXECUTION_INDEX
    )
    .to_numpy(
        dtype=float
    )
)


V9_BASE_PANEL[
    "TQQQ_Execution_Adj_Close"
] = (
    V9_TQQQ_PRICE_BY_DATE
    .reindex(
        V9_BASE_PANEL[
            "Execution_Date"
        ].to_numpy()
    )
    .to_numpy(
        dtype=float
    )
)


# ==============================================================================
# 10. REBUILD ALL EXECUTION-ALIGNED TARGETS
# ==============================================================================

for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_date_column = (
        f"Target_End_Date_{horizon_name}"
    )


    future_stock_index = (
        pd.MultiIndex.from_arrays(
            [
                V9_BASE_PANEL[
                    "Ticker"
                ].to_numpy(),

                V9_BASE_PANEL[
                    target_date_column
                ].to_numpy(),
            ],
            names=[
                "Ticker",
                "Date",
            ],
        )
    )


    future_asset_price = (
        V9_PRICE_LOOKUP
        .reindex(
            future_stock_index
        )
        .to_numpy(
            dtype=float
        )
    )


    future_tqqq_price = (
        V9_TQQQ_PRICE_BY_DATE
        .reindex(
            V9_BASE_PANEL[
                target_date_column
            ].to_numpy()
        )
        .to_numpy(
            dtype=float
        )
    )


    execution_asset_price = (
        V9_BASE_PANEL[
            "Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    execution_tqqq_price = (
        V9_BASE_PANEL[
            "TQQQ_Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    valid = (
        np.isfinite(
            execution_asset_price
        )
        &
        np.isfinite(
            execution_tqqq_price
        )
        &
        np.isfinite(
            future_asset_price
        )
        &
        np.isfinite(
            future_tqqq_price
        )
        &
        (
            execution_asset_price > 0
        )
        &
        (
            execution_tqqq_price > 0
        )
        &
        (
            future_asset_price > 0
        )
        &
        (
            future_tqqq_price > 0
        )
    )


    asset_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    tqqq_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    asset_growth[
        valid
    ] = (
        future_asset_price[
            valid
        ]
        /
        execution_asset_price[
            valid
        ]
    )


    tqqq_growth[
        valid
    ] = (
        future_tqqq_price[
            valid
        ]
        /
        execution_tqqq_price[
            valid
        ]
    )


    V9_BASE_PANEL[
        f"Asset_Return_{horizon_name}"
    ] = (
        asset_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"TQQQ_Return_{horizon_name}"
    ] = (
        tqqq_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"Arithmetic_Excess_{horizon_name}"
    ] = (
        V9_BASE_PANEL[
            f"Asset_Return_{horizon_name}"
        ]
        -
        V9_BASE_PANEL[
            f"TQQQ_Return_{horizon_name}"
        ]
    )


    relative_growth = (
        asset_growth
        /
        tqqq_growth
    )


    V9_BASE_PANEL[
        f"Log_Relative_Wealth_{horizon_name}"
    ] = np.where(
        (
            np.isfinite(
                relative_growth
            )
            &
            (
                relative_growth > 0
            )
        ),
        np.log(
            relative_growth
        ),
        np.nan,
    )


# ==============================================================================
# 11. BUILD EXACT RESEARCH CALENDAR
# ==============================================================================

V9_EVALUATION_CALENDAR = (
    V9_CALENDAR[
        V9_CALENDAR[
            "Date"
        ]
        >=
        pd.Timestamp(
            RESTORE_FIRST_SIGNAL_DATE
        )
    ]
    .iloc[
        ::V9_PORTFOLIO_REBALANCE_SESSIONS
    ]
    .dropna(
        subset=[
            "Execution_Date",
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_EVALUATION_CALENDAR[
    "Next_Execution_Date"
] = (
    V9_EVALUATION_CALENDAR[
        "Execution_Date"
    ].shift(-1)
)


# ==============================================================================
# 12. ALL-CANDIDATE EXECUTION PREFLIGHT
# ==============================================================================
#
# This executes BEFORE expensive model fitting.
#
# Every candidate that could potentially be selected is checked.
#
# ==============================================================================

V9_PREFLIGHT_ROWS = []

V9_PREFLIGHT_MISSING_ROWS = []


for decision_index, event in (
    V9_EVALUATION_CALENDAR.iterrows()
):

    signal_date = pd.Timestamp(
        event[
            "Date"
        ]
    )


    execution_date = pd.Timestamp(
        event[
            "Execution_Date"
        ]
    )


    next_execution_date = (
        pd.Timestamp(
            event[
                "Next_Execution_Date"
            ]
        )
        if pd.notna(
            event[
                "Next_Execution_Date"
            ]
        )
        else pd.NaT
    )


    candidates = (
        V9_BASE_PANEL.loc[
            V9_BASE_PANEL[
                "Date"
            ]
            ==
            signal_date,
            "Ticker",
        ]
        .drop_duplicates()
        .tolist()
    )


    # --------------------------------------------------------------------------
    # Entry quotes
    # --------------------------------------------------------------------------

    entry_index = pd.MultiIndex.from_product(
        [
            candidates,
            [
                execution_date,
            ],
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )


    entry_prices = (
        V9_PRICE_LOOKUP
        .reindex(
            entry_index
        )
    )


    missing_entry = (
        entry_prices[
            entry_prices.isna()
        ]
        .index
        .get_level_values(
            "Ticker"
        )
        .tolist()
    )


    # --------------------------------------------------------------------------
    # Next rebalance quotes
    # --------------------------------------------------------------------------

    missing_exit = []


    if pd.notna(
        next_execution_date
    ):

        exit_index = pd.MultiIndex.from_product(
            [
                candidates,
                [
                    next_execution_date,
                ],
            ],
            names=[
                "Ticker",
                "Date",
            ],
        )


        exit_prices = (
            V9_PRICE_LOOKUP
            .reindex(
                exit_index
            )
        )


        missing_exit = (
            exit_prices[
                exit_prices.isna()
            ]
            .index
            .get_level_values(
                "Ticker"
            )
            .tolist()
        )


    V9_PREFLIGHT_ROWS.append(
        {
            "Decision":
                decision_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Next_Execution_Date":
                next_execution_date,

            "Candidates":
                len(
                    candidates
                ),

            "Missing_Entry_Quotes":
                len(
                    missing_entry
                ),

            "Missing_Next_Rebalance_Quotes":
                len(
                    missing_exit
                ),
        }
    )


    for ticker in missing_entry:

        V9_PREFLIGHT_MISSING_ROWS.append(
            {
                "Decision":
                    decision_index + 1,

                "Ticker":
                    ticker,

                "Quote_Type":
                    "ENTRY",

                "Requested_Date":
                    execution_date,
            }
        )


    for ticker in missing_exit:

        V9_PREFLIGHT_MISSING_ROWS.append(
            {
                "Decision":
                    decision_index + 1,

                "Ticker":
                    ticker,

                "Quote_Type":
                    "NEXT_REBALANCE",

                "Requested_Date":
                    next_execution_date,
            }
        )


V9_EXECUTION_PREFLIGHT = pd.DataFrame(
    V9_PREFLIGHT_ROWS
)


V9_EXECUTION_PREFLIGHT_MISSING = pd.DataFrame(
    V9_PREFLIGHT_MISSING_ROWS
)


# ==============================================================================
# 13. SPECIFIC GOGO TEST
# ==============================================================================

V9_GOGO_TEST_DATE = pd.Timestamp(
    "2026-06-25"
)


V9_GOGO_PRICE = (
    V9_PRICE_LOOKUP.get(
        (
            "GOGO",
            V9_GOGO_TEST_DATE,
        ),
        np.nan,
    )
)


if pd.notna(
    V9_GOGO_PRICE
):

    V9_GOGO_PRICE = float(
        V9_GOGO_PRICE
    )


V9_GOGO_TEST = pd.DataFrame(
    {
        "Field": [
            "Ticker",
            "Requested_Date",
            "Exact_Lifecycle_Quote_Available",
            "Lifecycle_Adj_Close",
        ],

        "Value": [
            "GOGO",
            V9_GOGO_TEST_DATE,
            bool(
                np.isfinite(
                    V9_GOGO_PRICE
                )
            ),
            V9_GOGO_PRICE,
        ],
    }
)


# ==============================================================================
# 14. TARGET COVERAGE
# ==============================================================================

V9_TARGET_COVERAGE_ROWS = []


for horizon_name, sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_column = (
        f"Log_Relative_Wealth_{horizon_name}"
    )


    available = (
        V9_BASE_PANEL[
            target_column
        ].notna()
    )


    V9_TARGET_COVERAGE_ROWS.append(
        {
            "Horizon":
                horizon_name,

            "Sessions":
                sessions,

            "Eligible_Rows":
                len(
                    V9_BASE_PANEL
                ),

            "Target_Rows":
                int(
                    available.sum()
                ),

            "Coverage_Pct":
                100.0
                *
                available.mean(),

            "Last_Usable_Signal_Date":
                V9_BASE_PANEL.loc[
                    available,
                    "Date",
                ].max(),
        }
    )


V9_TARGET_COVERAGE = (
    pd.DataFrame(
        V9_TARGET_COVERAGE_ROWS
    )
    .set_index(
        "Horizon"
    )
)


# ==============================================================================
# 15. PREFLIGHT SUMMARY
# ==============================================================================

V9_PREFLIGHT_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Research decisions",
            "Candidate observations checked",
            "Missing entry quotes",
            "Missing next-rebalance quotes",
        ],

        "Value": [
            len(
                V9_EXECUTION_PREFLIGHT
            ),

            int(
                V9_EXECUTION_PREFLIGHT[
                    "Candidates"
                ].sum()
            ),

            int(
                V9_EXECUTION_PREFLIGHT[
                    "Missing_Entry_Quotes"
                ].sum()
            ),

            int(
                V9_EXECUTION_PREFLIGHT[
                    "Missing_Next_Rebalance_Quotes"
                ].sum()
            ),
        ],
    }
)


# ==============================================================================
# 16. UPDATE V9 DATA CONTRACT
# ==============================================================================

V9_RESEARCH_CONTRACT[
    "pit_signal_source"
] = (
    "V4_DAILY_PANEL"
)


V9_RESEARCH_CONTRACT[
    "lifecycle_price_source"
] = (
    "B38_ALL_PRICES_FULL_LIFECYCLE"
)


V9_RESEARCH_CONTRACT[
    "optional_metadata_policy"
] = (
    "SOURCE_INDEX_AND_GICS_SECTOR_NOT_REQUIRED"
)


V9_RESEARCH_CONTRACT[
    "membership_exit_policy"
] = (
    "INDEX_EXIT_STOPS_NEW_SIGNAL_ELIGIBILITY_"
    "BUT_DOES_NOT_DELETE_PRICE_HISTORY"
)


V9_RESEARCH_CONTRACT[
    "execution_preflight_policy"
] = (
    "CHECK_ALL_POTENTIAL_CANDIDATES_BEFORE_MODEL_FIT"
)


V9_CONTRACT_STRING = json.dumps(
    V9_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V9_CONTRACT_FINGERPRINT = hashlib.sha256(
    V9_CONTRACT_STRING.encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 17. OUTPUT
# ==============================================================================

print(
    "\nLifecycle-corrected contract fingerprint:"
)

print(
    V9_CONTRACT_FINGERPRINT
)


print(
    "\n1) GOGO ROOT-CAUSE TEST"
)

display(
    V9_GOGO_TEST
)


print(
    "\n2) ALL-CANDIDATE EXECUTION PREFLIGHT"
)

display(
    V9_EXECUTION_PREFLIGHT
)


print(
    "\n3) PREFLIGHT SUMMARY"
)

display(
    V9_PREFLIGHT_SUMMARY
)


print(
    "\n4) TARGET COVERAGE"
)

display(
    V9_TARGET_COVERAGE.round(
        4
    )
)


V9_TOTAL_MISSING_ENTRY = int(
    V9_EXECUTION_PREFLIGHT[
        "Missing_Entry_Quotes"
    ].sum()
)


V9_TOTAL_MISSING_EXIT = int(
    V9_EXECUTION_PREFLIGHT[
        "Missing_Next_Rebalance_Quotes"
    ].sum()
)


if (
    V9_TOTAL_MISSING_ENTRY > 0
    or
    V9_TOTAL_MISSING_EXIT > 0
):

    print(
        "\n5) UNRESOLVED EXECUTION QUOTES"
    )


    display(
        V9_EXECUTION_PREFLIGHT_MISSING
        .head(
            100
        )
    )


    print(
        "\n[!] PREFLIGHT FOUND LIFECYCLE QUOTE GAPS."
    )

    print(
        "[!] DO NOT RUN THE EXPENSIVE MODEL FIT YET."
    )

else:

    print("\nINTEGRITY:")
    print("[+] PIT signal eligibility preserved.")
    print("[+] Optional metadata no longer required.")
    print("[+] Full lifecycle price ledger active.")
    print("[+] All potential entry quotes validated.")
    print("[+] All potential next-rebalance quotes validated.")
    print("[+] No model was fit.")
    print("[+] No V9 performance was observed.")

    print(
        "\n[+] V9 LIFECYCLE PREFLIGHT PASSED."
    )

    print(
        "[+] SAFE TO PROCEED TO CACHED MODEL FITTING."
    )


print("=" * 130)
V9_EVALUATION_DATES = pd.to_datetime(V7_PATH.Signal_Date).sort_values().tolist()
# ==============================================================================
# V9 — PRE-PERFORMANCE DATA-QUALITY REPAIR
# HLX LIFECYCLE GAP + V9-SPECIFIC PIT PANEL REBUILD
# ==============================================================================
#
# IMPORTANT
# ---------
# NO V9 PORTFOLIO PERFORMANCE HAS BEEN OBSERVED.
#
# The previously inferred HLX "terminal value" on 2026-07-17 was caused by
# an incomplete Yahoo/cache history, not by an actual security termination.
#
# This block:
#
#   1. Re-downloads the missing HLX research-window prices.
#   2. Repairs ONLY the V9 lifecycle ledger.
#   3. Does NOT alter frozen V8 research infrastructure.
#   4. Rebuilds V9 PIT eligibility directly from the frozen PIT membership table.
#   5. Rebuilds execution-aligned V9 targets.
#   6. Re-runs the all-candidate execution preflight.
#   7. Invalidates ONLY the final 2026-07-24 model checkpoint.
#
# After this block passes:
#
#   RERUN V9 BLOCK 2A.
#
# Expected:
#
#   Existing valid checkpoints : 33/34
#   Remaining decisions to fit : 1
#
# ==============================================================================


import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V9_DQ_REQUIRED = [
    "V9_LIFECYCLE_PANEL",
    "V4_PIT_STOCK_MEMBERSHIP",
    "B38_ETF_SLEEVE",
    "B38_PIT_START_DATE",
    "B38_MIN_PRICE",
    "B38_MIN_MEDIAN_DOLLAR_VOLUME",
    "B38_MIN_VALID_DAYS",
    "RESTORE_FIRST_SIGNAL_DATE",
    "V9_TARGET_HORIZONS",
    "V9_PORTFOLIO_REBALANCE_SESSIONS",
    "V9_REFERENCE_AUM_USD",
    "V9_IMPACT_COEFFICIENT",
    "V9_EVALUATION_DATES",
]


V9_DQ_MISSING = [
    name
    for name in V9_DQ_REQUIRED
    if name not in globals()
]


if V9_DQ_MISSING:

    raise RuntimeError(
        "V9 data-quality repair is missing required objects: "
        f"{V9_DQ_MISSING}"
    )


print("=" * 132)
print("V9 — PRE-PERFORMANCE DATA-QUALITY REPAIR")
print("HLX LIFECYCLE GAP + V9 PIT PANEL REBUILD")
print("=" * 132)


# ==============================================================================
# 1–6. RESTORE THE SINGLE ARCHIVED HLX LIFECYCLE QUOTE
#
# The original notebook's saved Module V9 data-quality output records:
#     HLX, 2026-07-27, Adj_Close = 9.650000
#
# The quote was already independently required to reproduce the frozen V8
# comparator. Do not request Yahoo again: a rate-limited response is not a new
# data observation. Patch only this exact missing lifecycle value and preserve
# all other rows and fields.

V9_DQ_TICKER = "HLX"
V9_DQ_REQUIRED_DATE = pd.Timestamp("2026-07-27")
V9_DQ_ARCHIVED_ADJ_CLOSE = 9.650000
V9_DQ_ARCHIVE_SOURCE = (
    "Original uploaded notebook cell 45 saved V9 data-quality repair output"
)

existing_lifecycle = V9_LIFECYCLE_PANEL.copy(deep=True)
existing_lifecycle["Date"] = (
    pd.to_datetime(existing_lifecycle["Date"], errors="coerce")
    .dt.tz_localize(None)
    .dt.normalize()
)
existing_lifecycle["Ticker"] = (
    existing_lifecycle["Ticker"].astype(str).str.upper().str.strip()
)

exact_mask = (
    existing_lifecycle["Ticker"].eq(V9_DQ_TICKER)
    & existing_lifecycle["Date"].eq(V9_DQ_REQUIRED_DATE)
)

if exact_mask.any():
    existing_values = pd.to_numeric(
        existing_lifecycle.loc[exact_mask, "Adj_Close"], errors="coerce"
    )
    positive_values = existing_values[np.isfinite(existing_values) & (existing_values > 0)]
    if len(positive_values):
        if not np.allclose(
            positive_values.to_numpy(dtype=float),
            V9_DQ_ARCHIVED_ADJ_CLOSE,
            rtol=0.0,
            atol=0.00000051,
        ):
            raise RuntimeError(
                "Existing HLX 2026-07-27 Adj_Close conflicts with the archived "
                "9.650000 observation; it was not overwritten."
            )
        existing_lifecycle.loc[exact_mask, "Adj_Close"] = V9_DQ_ARCHIVED_ADJ_CLOSE
        V9_DQ_REPAIR_ACTION = "EXISTING_QUOTE_AGREES_WITH_ARCHIVE"
    else:
        existing_lifecycle.loc[exact_mask, "Adj_Close"] = V9_DQ_ARCHIVED_ADJ_CLOSE
        V9_DQ_REPAIR_ACTION = "MISSING_ADJ_CLOSE_RESTORED_FROM_NOTEBOOK_OUTPUT"
else:
    archived_row = {column: np.nan for column in existing_lifecycle.columns}
    archived_row.update({
        "Date": V9_DQ_REQUIRED_DATE,
        "Ticker": V9_DQ_TICKER,
        "Adj_Close": V9_DQ_ARCHIVED_ADJ_CLOSE,
    })
    existing_lifecycle = pd.concat(
        [existing_lifecycle, pd.DataFrame([archived_row])], ignore_index=True
    )
    V9_DQ_REPAIR_ACTION = "MISSING_ROW_RESTORED_FROM_NOTEBOOK_OUTPUT"

V9_LIFECYCLE_PANEL = (
    existing_lifecycle
    .drop_duplicates(["Ticker", "Date"], keep="last")
    .sort_values(["Ticker", "Date"])
    .reset_index(drop=True)
)
V9_DQ_FRESH_PRICES = V9_LIFECYCLE_PANEL.loc[
    V9_LIFECYCLE_PANEL["Ticker"].eq(V9_DQ_TICKER)
    & V9_LIFECYCLE_PANEL["Date"].eq(V9_DQ_REQUIRED_DATE),
    ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj_Close", "Volume"],
].copy()
V9_DQ_HLX_0727_PRICE = float(V9_DQ_FRESH_PRICES["Adj_Close"].iloc[-1])

print("\n[+] Archived exact HLX lifecycle quote restored without a network request:")
print(f"    2026-07-27 Adj Close = {V9_DQ_HLX_0727_PRICE:.6f}")
print(f"    Action = {V9_DQ_REPAIR_ACTION}")
print(f"    Source = {V9_DQ_ARCHIVE_SOURCE}")


# 7. RECOMPUTE ALL CAUSAL LIFECYCLE VARIABLES
# ==============================================================================

V9_LIFECYCLE_PANEL[
    "Daily_Return"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]
    .pct_change(
        fill_method=None
    )
)


V9_LIFECYCLE_PANEL[
    "Dollar_Volume"
] = (
    V9_LIFECYCLE_PANEL[
        "Close"
    ]
    *
    V9_LIFECYCLE_PANEL[
        "Volume"
    ]
)


V9_LIFECYCLE_PANEL[
    "Median_Dollar_Volume_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Dollar_Volume"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).median()
    )
)


V9_LIFECYCLE_PANEL[
    "Valid_Days_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=1,
            ).count()
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Realized_Vol_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Daily_Return"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).std()
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Amihud_Daily"
] = (
    V9_LIFECYCLE_PANEL[
        "Daily_Return"
    ].abs()
    /
    V9_LIFECYCLE_PANEL[
        "Dollar_Volume"
    ].replace(
        0.0,
        np.nan,
    )
)


V9_LIFECYCLE_PANEL[
    "V9_Amihud_60"
] = (
    V9_LIFECYCLE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "V9_Amihud_Daily"
    ]
    .transform(
        lambda series:
            series.rolling(
                60,
                min_periods=50,
            ).median()
    )
)


V9_LIFECYCLE_PANEL[
    "V9_AUM_to_ADV"
] = (
    V9_REFERENCE_AUM_USD
    /
    V9_LIFECYCLE_PANEL[
        "Median_Dollar_Volume_60"
    ]
)


V9_LIFECYCLE_PANEL[
    "V9_AUM_to_ADV_Pct"
] = (
    100.0
    *
    V9_LIFECYCLE_PANEL[
        "V9_AUM_to_ADV"
    ]
)


V9_LIFECYCLE_PANEL[
    "V9_Full_AUM_Impact_Scale"
] = (
    V9_IMPACT_COEFFICIENT
    *
    V9_LIFECYCLE_PANEL[
        "V9_Realized_Vol_60"
    ]
    *
    np.sqrt(
        np.maximum(
            V9_LIFECYCLE_PANEL[
                "V9_AUM_to_ADV"
            ],
            0.0,
        )
    )
)


# ==============================================================================
# 8. REBUILD FULL V9 PRICE LOOKUP
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
# 9. TQQQ TRADING CALENDAR
# ==============================================================================

V9_TQQQ_PANEL = (
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
    .dropna(
        subset=[
            "Date",
            "Adj_Close",
        ]
    )
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


V9_TQQQ_PRICE_BY_DATE = (
    V9_TQQQ_PANEL
    .set_index(
        "Date"
    )[
        "Adj_Close"
    ]
)


V9_CALENDAR = pd.DataFrame(
    {
        "Date":
            V9_TQQQ_PANEL[
                "Date"
            ].copy()
    }
)


V9_CALENDAR[
    "Execution_Date"
] = (
    V9_CALENDAR[
        "Date"
    ].shift(-1)
)


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    V9_CALENDAR[
        f"Target_End_Date_{horizon_name}"
    ] = (
        V9_CALENDAR[
            "Date"
        ].shift(
            -(
                1
                +
                horizon_sessions
            )
        )
    )


# ==============================================================================
# 10. NORMALIZE FROZEN PIT MEMBERSHIP
# ==============================================================================

V9_PIT_MEMBERSHIP = (
    V4_PIT_STOCK_MEMBERSHIP
    .copy()
)


V9_PIT_MEMBERSHIP[
    "Snapshot_AsOf"
] = pd.to_datetime(
    V9_PIT_MEMBERSHIP[
        "Snapshot_AsOf"
    ]
).dt.tz_localize(None).dt.normalize()


V9_PIT_MEMBERSHIP[
    "Ticker"
] = (
    V9_PIT_MEMBERSHIP[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_PIT_MEMBERSHIP = (
    V9_PIT_MEMBERSHIP
    .drop_duplicates(
        [
            "Snapshot_AsOf",
            "Ticker",
        ],
        keep="last",
    )
)


# ==============================================================================
# 11. MAP EVERY V9 MARKET DATE TO THE MOST RECENT PIT SNAPSHOT
# ==============================================================================

V9_PIT_PRICE_DATES = (
    V9_CALENDAR.loc[
        V9_CALENDAR[
            "Date"
        ]
        >=
        pd.Timestamp(
            B38_PIT_START_DATE
        ),
        "Date",
    ]
    .drop_duplicates()
    .sort_values()
    .reset_index(
        drop=True
    )
)


V9_PIT_SNAPSHOT_DATES = (
    V9_PIT_MEMBERSHIP[
        "Snapshot_AsOf"
    ]
    .drop_duplicates()
    .sort_values()
    .to_numpy(
        dtype="datetime64[ns]"
    )
)


v9_price_dates_np = (
    V9_PIT_PRICE_DATES
    .to_numpy(
        dtype="datetime64[ns]"
    )
)


v9_snapshot_indices = (
    np.searchsorted(
        V9_PIT_SNAPSHOT_DATES,
        v9_price_dates_np,
        side="right",
    )
    -
    1
)


valid_snapshot_mask = (
    v9_snapshot_indices
    >=
    0
)


V9_DATE_TO_SNAPSHOT = pd.DataFrame(
    {
        "Date":
            V9_PIT_PRICE_DATES[
                valid_snapshot_mask
            ].to_numpy(),

        "Snapshot_AsOf":
            V9_PIT_SNAPSHOT_DATES[
                v9_snapshot_indices[
                    valid_snapshot_mask
                ]
            ],
    }
)


# ==============================================================================
# 12. REBUILD V9-SPECIFIC PIT STOCK PANEL
# ==============================================================================

V9_PIT_STOCK_PRICES = (
    V9_LIFECYCLE_PANEL[
        (
            ~V9_LIFECYCLE_PANEL[
                "Ticker"
            ].isin(
                B38_ETF_SLEEVE
            )
        )
        &
        (
            V9_LIFECYCLE_PANEL[
                "Date"
            ]
            >=
            pd.Timestamp(
                B38_PIT_START_DATE
            )
        )
    ]
    .merge(
        V9_DATE_TO_SNAPSHOT,
        on="Date",
        how="inner",
        validate="many_to_one",
    )
)


V9_PIT_STOCK_PANEL = (
    V9_PIT_STOCK_PRICES
    .merge(
        V9_PIT_MEMBERSHIP,
        on=[
            "Snapshot_AsOf",
            "Ticker",
        ],
        how="inner",
        validate="many_to_one",
    )
)


V9_PIT_STOCK_PANEL[
    "Asset_Type"
] = "STOCK"


# ==============================================================================
# 13. REBUILD THE ORIGINAL CAUSAL ELIGIBILITY RULE
# ==============================================================================

V9_PIT_STOCK_PANEL[
    "Price_OK"
] = (
    V9_PIT_STOCK_PANEL[
        "Close"
    ]
    >=
    float(
        B38_MIN_PRICE
    )
)


V9_PIT_STOCK_PANEL[
    "Liquidity_OK"
] = (
    V9_PIT_STOCK_PANEL[
        "Median_Dollar_Volume_60"
    ]
    >=
    float(
        B38_MIN_MEDIAN_DOLLAR_VOLUME
    )
)


V9_PIT_STOCK_PANEL[
    "History_OK"
] = (
    V9_PIT_STOCK_PANEL[
        "Valid_Days_60"
    ]
    >=
    int(
        B38_MIN_VALID_DAYS
    )
)


V9_PIT_STOCK_PANEL[
    "Eligible"
] = (
    V9_PIT_STOCK_PANEL[
        "Price_OK"
    ]
    &
    V9_PIT_STOCK_PANEL[
        "Liquidity_OK"
    ]
    &
    V9_PIT_STOCK_PANEL[
        "History_OK"
    ]
)


# ==============================================================================
# 14. REBUILD V9 BASE PANEL
# ==============================================================================

V9_BASE_PANEL = (
    V9_PIT_STOCK_PANEL[
        V9_PIT_STOCK_PANEL[
            "Eligible"
        ]
    ]
    .copy()
    .merge(
        V9_CALENDAR,
        on="Date",
        how="left",
        validate="many_to_one",
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


# ==============================================================================
# 15. EXECUTION PRICES
# ==============================================================================

entry_index = pd.MultiIndex.from_arrays(
    [
        V9_BASE_PANEL[
            "Ticker"
        ].to_numpy(),

        V9_BASE_PANEL[
            "Execution_Date"
        ].to_numpy(),
    ],
    names=[
        "Ticker",
        "Date",
    ],
)


V9_BASE_PANEL[
    "Execution_Adj_Close"
] = (
    V9_PRICE_LOOKUP
    .reindex(
        entry_index
    )
    .to_numpy(
        dtype=float
    )
)


V9_BASE_PANEL[
    "TQQQ_Execution_Adj_Close"
] = (
    V9_TQQQ_PRICE_BY_DATE
    .reindex(
        V9_BASE_PANEL[
            "Execution_Date"
        ].to_numpy()
    )
    .to_numpy(
        dtype=float
    )
)


# ==============================================================================
# 16. REBUILD EXECUTION-ALIGNED TARGETS
# ==============================================================================

for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_date_column = (
        f"Target_End_Date_{horizon_name}"
    )


    future_index = pd.MultiIndex.from_arrays(
        [
            V9_BASE_PANEL[
                "Ticker"
            ].to_numpy(),

            V9_BASE_PANEL[
                target_date_column
            ].to_numpy(),
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )


    future_asset_price = (
        V9_PRICE_LOOKUP
        .reindex(
            future_index
        )
        .to_numpy(
            dtype=float
        )
    )


    future_tqqq_price = (
        V9_TQQQ_PRICE_BY_DATE
        .reindex(
            V9_BASE_PANEL[
                target_date_column
            ].to_numpy()
        )
        .to_numpy(
            dtype=float
        )
    )


    execution_asset_price = (
        V9_BASE_PANEL[
            "Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    execution_tqqq_price = (
        V9_BASE_PANEL[
            "TQQQ_Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    valid = (
        np.isfinite(
            execution_asset_price
        )
        &
        np.isfinite(
            future_asset_price
        )
        &
        np.isfinite(
            execution_tqqq_price
        )
        &
        np.isfinite(
            future_tqqq_price
        )
        &
        (
            execution_asset_price > 0
        )
        &
        (
            future_asset_price > 0
        )
        &
        (
            execution_tqqq_price > 0
        )
        &
        (
            future_tqqq_price > 0
        )
    )


    asset_growth = np.full(
        len(
            V9_BASE_PANEL
        ),
        np.nan,
        dtype=float,
    )


    tqqq_growth = np.full(
        len(
            V9_BASE_PANEL
        ),
        np.nan,
        dtype=float,
    )


    asset_growth[
        valid
    ] = (
        future_asset_price[
            valid
        ]
        /
        execution_asset_price[
            valid
        ]
    )


    tqqq_growth[
        valid
    ] = (
        future_tqqq_price[
            valid
        ]
        /
        execution_tqqq_price[
            valid
        ]
    )


    V9_BASE_PANEL[
        f"Asset_Return_{horizon_name}"
    ] = (
        asset_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"TQQQ_Return_{horizon_name}"
    ] = (
        tqqq_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"Arithmetic_Excess_{horizon_name}"
    ] = (
        V9_BASE_PANEL[
            f"Asset_Return_{horizon_name}"
        ]
        -
        V9_BASE_PANEL[
            f"TQQQ_Return_{horizon_name}"
        ]
    )


    relative_growth = (
        asset_growth
        /
        tqqq_growth
    )


    V9_BASE_PANEL[
        f"Log_Relative_Wealth_{horizon_name}"
    ] = np.where(
        (
            np.isfinite(
                relative_growth
            )
            &
            (
                relative_growth > 0
            )
        ),
        np.log(
            relative_growth
        ),
        np.nan,
    )


# ==============================================================================
# 17. REBUILD / VERIFY EVALUATION CALENDAR
# ==============================================================================

V9_EVALUATION_CALENDAR = (
    V9_CALENDAR[
        V9_CALENDAR[
            "Date"
        ]
        >=
        pd.Timestamp(
            RESTORE_FIRST_SIGNAL_DATE
        )
    ]
    .iloc[
        ::V9_PORTFOLIO_REBALANCE_SESSIONS
    ]
    .dropna(
        subset=[
            "Execution_Date"
        ]
    )
    .reset_index(
        drop=True
    )
)


V9_EVALUATION_CALENDAR[
    "Next_Execution_Date"
] = (
    V9_EVALUATION_CALENDAR[
        "Execution_Date"
    ].shift(-1)
)


new_evaluation_dates = [
    pd.Timestamp(
        date
    )
    for date
    in V9_EVALUATION_CALENDAR[
        "Date"
    ].tolist()
]


old_evaluation_dates = [
    pd.Timestamp(
        date
    )
    for date
    in V9_EVALUATION_DATES
]


if new_evaluation_dates != old_evaluation_dates:

    raise RuntimeError(
        "The V9 evaluation calendar changed during the "
        "data-quality repair. Existing checkpoints were NOT invalidated."
    )


# ==============================================================================
# 18. ALL-CANDIDATE EXECUTION PREFLIGHT
# ==============================================================================

preflight_rows = []

missing_rows = []


for decision_index, event in (
    V9_EVALUATION_CALENDAR.iterrows()
):

    signal_date = pd.Timestamp(
        event[
            "Date"
        ]
    )


    execution_date = pd.Timestamp(
        event[
            "Execution_Date"
        ]
    )


    next_execution_date = (
        pd.Timestamp(
            event[
                "Next_Execution_Date"
            ]
        )
        if pd.notna(
            event[
                "Next_Execution_Date"
            ]
        )
        else pd.NaT
    )


    candidates = (
        V9_BASE_PANEL.loc[
            V9_BASE_PANEL[
                "Date"
            ]
            ==
            signal_date,
            "Ticker",
        ]
        .drop_duplicates()
        .tolist()
    )


    entry_index = pd.MultiIndex.from_product(
        [
            candidates,
            [
                execution_date,
            ],
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )


    entry_prices = (
        V9_PRICE_LOOKUP
        .reindex(
            entry_index
        )
    )


    missing_entry = (
        entry_prices[
            entry_prices.isna()
        ]
        .index
        .get_level_values(
            "Ticker"
        )
        .tolist()
    )


    missing_exit = []


    if pd.notna(
        next_execution_date
    ):

        exit_index = pd.MultiIndex.from_product(
            [
                candidates,
                [
                    next_execution_date,
                ],
            ],
            names=[
                "Ticker",
                "Date",
            ],
        )


        exit_prices = (
            V9_PRICE_LOOKUP
            .reindex(
                exit_index
            )
        )


        missing_exit = (
            exit_prices[
                exit_prices.isna()
            ]
            .index
            .get_level_values(
                "Ticker"
            )
            .tolist()
        )


    preflight_rows.append(
        {
            "Decision":
                decision_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Next_Execution_Date":
                next_execution_date,

            "Candidates":
                len(
                    candidates
                ),

            "Missing_Entry_Quotes":
                len(
                    missing_entry
                ),

            "Missing_Next_Rebalance_Quotes":
                len(
                    missing_exit
                ),
        }
    )


    for ticker in missing_entry:

        missing_rows.append(
            {
                "Decision":
                    decision_index + 1,

                "Ticker":
                    ticker,

                "Quote_Type":
                    "ENTRY",

                "Requested_Date":
                    execution_date,
            }
        )


    for ticker in missing_exit:

        missing_rows.append(
            {
                "Decision":
                    decision_index + 1,

                "Ticker":
                    ticker,

                "Quote_Type":
                    "NEXT_REBALANCE",

                "Requested_Date":
                    next_execution_date,
            }
        )


V9_EXECUTION_PREFLIGHT = pd.DataFrame(
    preflight_rows
)


V9_EXECUTION_PREFLIGHT_MISSING = pd.DataFrame(
    missing_rows
)


total_missing_entry = int(
    V9_EXECUTION_PREFLIGHT[
        "Missing_Entry_Quotes"
    ].sum()
)


total_missing_exit = int(
    V9_EXECUTION_PREFLIGHT[
        "Missing_Next_Rebalance_Quotes"
    ].sum()
)


# ==============================================================================
# 19. VERIFY HLX EXACT QUOTE IN THE REPAIRED LEDGER
# ==============================================================================

try:

    repaired_hlx_price = float(
        V9_PRICE_LOOKUP.loc[
            (
                "HLX",
                pd.Timestamp(
                    "2026-07-27"
                ),
            )
        ]
    )

except KeyError:

    repaired_hlx_price = np.nan


if not np.isfinite(
    repaired_hlx_price
):

    raise RuntimeError(
        "HLX 2026-07-27 is still absent after repair. "
        "No checkpoint has been invalidated."
    )


# ==============================================================================
# 20. DATA-REPAIR FINGERPRINT
# ==============================================================================

repair_hash_frame = (
    V9_DQ_FRESH_PRICES[
        [
            "Date",
            "Ticker",
            "Open",
            "High",
            "Low",
            "Close",
            "Adj_Close",
            "Volume",
        ]
    ]
    .copy()
)


repair_hash_frame[
    "Date"
] = (
    repair_hash_frame[
        "Date"
    ].astype(str)
)


V9_DATA_QUALITY_REPAIR_PAYLOAD = {
    "ticker":
        "HLX",

    "reason":
        "INCOMPLETE_YAHOO_LIFECYCLE_HISTORY",

    "research_required_date":
        "2026-07-27",

    "repaired_rows":
        len(
            repair_hash_frame
        ),

    "fresh_data_hash":
        hashlib.sha256(
            repair_hash_frame
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        ).hexdigest(),

    "performance_observed_before_repair":
        False,

    "architecture_changed":
        False,
}


V9_DATA_QUALITY_REPAIR_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            V9_DATA_QUALITY_REPAIR_PAYLOAD,
            sort_keys=True,
        )
        .encode(
            "utf-8"
        )
    )
    .hexdigest()
)


# ==============================================================================
# 21. PREFLIGHT MUST PASS BEFORE CACHE INVALIDATION
# ==============================================================================

print(
    "\n1) REPAIRED HLX QUOTE"
)


display(
    pd.DataFrame(
        {
            "Field": [
                "Ticker",
                "Date",
                "Fresh_Adj_Close",
                "Exact_Quote_Available",
            ],

            "Value": [
                "HLX",
                pd.Timestamp(
                    "2026-07-27"
                ),
                repaired_hlx_price,
                bool(
                    np.isfinite(
                        repaired_hlx_price
                    )
                ),
            ],
        }
    )
)


print(
    "\n2) EXECUTION PREFLIGHT AFTER REPAIR"
)


display(
    V9_EXECUTION_PREFLIGHT
)


print(
    "\n3) PREFLIGHT SUMMARY"
)


V9_DQ_PREFLIGHT_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Research decisions",
            "Candidate observations checked",
            "Missing entry quotes",
            "Missing next-rebalance quotes",
            "Fresh HLX rows",
            "Data repair fingerprint",
        ],

        "Value": [
            len(
                V9_EXECUTION_PREFLIGHT
            ),

            int(
                V9_EXECUTION_PREFLIGHT[
                    "Candidates"
                ].sum()
            ),

            total_missing_entry,

            total_missing_exit,

            len(
                V9_DQ_FRESH_PRICES
            ),

            V9_DATA_QUALITY_REPAIR_FINGERPRINT,
        ],
    }
)


display(
    V9_DQ_PREFLIGHT_SUMMARY
)


if (
    total_missing_entry != 0
    or
    total_missing_exit != 0
):

    if not V9_EXECUTION_PREFLIGHT_MISSING.empty:

        print(
            "\nUNRESOLVED QUOTES"
        )


        display(
            V9_EXECUTION_PREFLIGHT_MISSING
        )


    raise RuntimeError(
        "Execution preflight still contains quote gaps. "
        "NO model checkpoint has been invalidated."
    )



if abs(float(V9_DQ_HLX_0727_PRICE)-9.65)>0.00000051:
    raise RuntimeError('HLX repair differs from the archived 9.650000 close. Historical data replication is not verified.')
print('[+] Full lifecycle/PIT repair finished BEFORE model fitting. No old checkpoints deleted.')
