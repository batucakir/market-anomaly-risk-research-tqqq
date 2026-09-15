# ==============================================================================
# MODULE 16 / HISTORICAL BLOCK 39
# V4 MULTI-HORIZON ABSOLUTE-RETURN ALPHA ENGINE
#
# IMPORTANT:
# Historical Block-39 research logic is preserved exactly.
# Internal object names remain B39_* / BLOCK39_* intentionally,
# because historical Block 40 depends on those exact objects.
# ==============================================================================

# ==============================================================================
# BLOCK 39 — V4 MULTI-HORIZON ABSOLUTE-RETURN ALPHA ENGINE
# ==============================================================================
#
# OBJECTIVE
# ---------
# Produce strictly-causal expected DAILY return forecasts for the broad
# point-in-time V4 universe.
#
# Horizons:
#
#       1 session
#       5 sessions
#       20 sessions
#
# Signal:
#       completed Close(t)
#
# Execution assumption:
#       next session Open(t+1)
#
# Targets:
#
#       1D  = Open(t+1) -> Close(t+1)
#       5D  = Open(t+1) -> Close(t+5)
#       20D = Open(t+1) -> Close(t+20)
#
# Multi-horizon target:
#
#       mean dailyized log return across 1D / 5D / 20D
#
# Models:
#
#       1. RIDGE               = regularized linear baseline
#       2. HIST_GRADIENT_BOOST = nonlinear challenger
#
# NO:
#       - Huber dependency
#       - H3 dependency
#       - Block-22 dependency
#       - single-name cap
#       - sector cap
#       - future information
#       - same-sample hyperparameter search
#
# FINAL MODEL SELECTION IS NOT DONE HERE.
#
# Block 40 will push BOTH models through the SAME portfolio optimizer.
# Net portfolio wealth will decide.
# ==============================================================================


import time
import json
import hashlib
import warnings

import numpy as np
import pandas as pd

from scipy.stats import spearmanr

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

B39_REQUIRED = [

    "B38_ALL_PRICES",
    "V4_DAILY_PANEL",
    "V4_COMPARISON_START",
    "V4_DATA_END_DATE",
    "B38_PIT_START_DATE",
    "V4_MASTER_FINGERPRINT",
]


B39_MISSING = [

    x
    for x in B39_REQUIRED
    if x not in globals()
]


if B39_MISSING:

    raise RuntimeError(
        "BLOCK 39 missing required objects: "
        f"{B39_MISSING}"
    )


print("=" * 118)

print(
    "BLOCK 39 — V4 MULTI-HORIZON ABSOLUTE-RETURN ALPHA ENGINE"
)

print("=" * 118)


# ==============================================================================
# 1. FROZEN BLOCK-39 RESEARCH CONFIGURATION
# ==============================================================================

B39_HORIZONS = (
    1,
    5,
    20,
)


# One trading year of rolling model history.
#
# This is frozen BEFORE seeing Block-39 results.

B39_TRAIN_LOOKBACK_DAYS = 252


# Need at least half a trading year before fitting.

B39_MIN_TRAIN_DAYS = 126


# Monthly-ish refit.
#
# Models are reused between refits.

B39_REFIT_EVERY = 21


# Genuine broad cross-section requirement.

B39_MIN_PRED_ASSETS = 500


# Diagnostic top/bottom tail only.
# NOT a portfolio rule.

B39_DIAGNOSTIC_TAIL_FRAC = 0.10


B39_MODELS = (
    "RIDGE",
    "HGB",
)


B39_CONFIG = {

    "horizons_sessions":
        B39_HORIZONS,

    "train_lookback_days":
        B39_TRAIN_LOOKBACK_DAYS,

    "minimum_train_days":
        B39_MIN_TRAIN_DAYS,

    "refit_every_sessions":
        B39_REFIT_EVERY,

    "minimum_prediction_assets":
        B39_MIN_PRED_ASSETS,

    "execution":
        "NEXT_SESSION_OPEN",

    "target":
        "MEAN_DAILYIZED_LOG_RETURN_1D_5D_20D",

    "models":
        B39_MODELS,

    "hyperparameter_search":
        False,
}


print(
    "\nComparison start :",
    pd.Timestamp(
        V4_COMPARISON_START
    ).date()
)

print(
    "Research end     :",
    pd.Timestamp(
        V4_DATA_END_DATE
    ).date()
)

print(
    "Train lookback   :",
    B39_TRAIN_LOOKBACK_DAYS,
    "sessions"
)

print(
    "Refit frequency  :",
    B39_REFIT_EVERY,
    "sessions"
)

print(
    "Models           :",
    B39_MODELS
)

print(
    "\nNO PORTFOLIO PARAMETER IS CHANGED."
)


# ==============================================================================
# 2. BUILD CLEAN PRICE RESEARCH FRAME
# ==============================================================================

required_price_columns = [

    "Date",
    "Ticker",

    "Open",
    "High",
    "Low",
    "Close",
    "Adj_Close",
    "Volume",

    "Daily_Return",
    "Median_Dollar_Volume_60",
]


missing_price_columns = [

    x
    for x in required_price_columns
    if x not in B38_ALL_PRICES.columns
]


if missing_price_columns:

    raise RuntimeError(
        "B38_ALL_PRICES missing columns: "
        f"{missing_price_columns}"
    )


B39_PRICE = (

    B38_ALL_PRICES[
        required_price_columns
    ]

    .copy()

    .replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
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


B39_PRICE[
    "Date"
] = pd.to_datetime(
    B39_PRICE[
        "Date"
    ]
)


# ==============================================================================
# 3. ADJUSTED OPEN
# ==============================================================================

# yfinance gives raw OHLC plus adjusted close.
#
# Adjustment factor maps raw Open onto the same adjusted price basis
# as Adj_Close.

B39_PRICE[
    "Adjustment_Factor"
] = (

    B39_PRICE[
        "Adj_Close"
    ]

    /

    B39_PRICE[
        "Close"
    ]
)


B39_PRICE[
    "Adj_Open"
] = (

    B39_PRICE[
        "Open"
    ]

    *

    B39_PRICE[
        "Adjustment_Factor"
    ]
)


B39_PRICE.loc[

    ~np.isfinite(
        B39_PRICE[
            "Adj_Open"
        ]
    )

    |

    (
        B39_PRICE[
            "Adj_Open"
        ]
        <=
        0
    ),

    "Adj_Open",

] = np.nan


# ==============================================================================
# 4. CAUSAL ASSET FEATURES
# ==============================================================================

g = B39_PRICE.groupby(
    "Ticker",
    sort=False,
)


for horizon in [
    1,
    5,
    20,
    60,
    120,
]:

    lagged = g[
        "Adj_Close"
    ].shift(
        horizon
    )


    B39_PRICE[
        f"Ret_{horizon}"
    ] = (

        B39_PRICE[
            "Adj_Close"
        ]

        /

        lagged

        -

        1.0
    )


# ------------------------------------------------------------------------------
# Realized historical volatility
# ------------------------------------------------------------------------------

B39_PRICE[
    "Vol_20"
] = (

    g[
        "Daily_Return"
    ]

    .transform(

        lambda s:

            s.rolling(
                window=20,
                min_periods=15,
            )
            .std()
    )
)


B39_PRICE[
    "Vol_60"
] = (

    g[
        "Daily_Return"
    ]

    .transform(

        lambda s:

            s.rolling(
                window=60,
                min_periods=40,
            )
            .std()
    )
)


# ------------------------------------------------------------------------------
# Distance from trailing high
# ------------------------------------------------------------------------------

B39_PRICE[
    "High_60"
] = (

    g[
        "Adj_Close"
    ]

    .transform(

        lambda s:

            s.rolling(
                window=60,
                min_periods=40,
            )
            .max()
    )
)


B39_PRICE[
    "Drawdown_60"
] = (

    B39_PRICE[
        "Adj_Close"
    ]

    /

    B39_PRICE[
        "High_60"
    ]

    -

    1.0
)


# ------------------------------------------------------------------------------
# Same-day price action
# ------------------------------------------------------------------------------

B39_PRICE[
    "Intraday_Return"
] = (

    B39_PRICE[
        "Adj_Close"
    ]

    /

    B39_PRICE[
        "Adj_Open"
    ]

    -

    1.0
)


previous_close = g[
    "Adj_Close"
].shift(
    1
)


B39_PRICE[
    "Gap_Return"
] = (

    B39_PRICE[
        "Adj_Open"
    ]

    /

    previous_close

    -

    1.0
)


# ------------------------------------------------------------------------------
# Historical intraday range
# ------------------------------------------------------------------------------

B39_PRICE[
    "Daily_Range"
] = (

    B39_PRICE[
        "High"
    ]

    -

    B39_PRICE[
        "Low"
    ]

) / B39_PRICE[
    "Close"
]


B39_PRICE[
    "Range_20"
] = (

    g[
        "Daily_Range"
    ]

    .transform(

        lambda s:

            s.rolling(
                window=20,
                min_periods=15,
            )
            .mean()
    )
)


# ------------------------------------------------------------------------------
# Liquidity / volume state
# ------------------------------------------------------------------------------

B39_PRICE[
    "Log_Dollar_Volume_60"
] = np.log1p(

    B39_PRICE[
        "Median_Dollar_Volume_60"
    ]
)


B39_PRICE[
    "Median_Volume_20"
] = (

    g[
        "Volume"
    ]

    .transform(

        lambda s:

            s.rolling(
                window=20,
                min_periods=15,
            )
            .median()
    )
)


B39_PRICE[
    "Volume_Ratio_20"
] = (

    B39_PRICE[
        "Volume"
    ]

    /

    B39_PRICE[
        "Median_Volume_20"
    ]

    -

    1.0
)


# ==============================================================================
# 5. MARKET REGIME FEATURES — SPY
# ==============================================================================

B39_SPY = (

    B39_PRICE[

        B39_PRICE[
            "Ticker"
        ]
        ==
        "SPY"
    ]

    [
        [
            "Date",
            "Ret_1",
            "Ret_5",
            "Ret_20",
            "Vol_20",
            "Drawdown_60",
        ]
    ]

    .drop_duplicates(
        "Date"
    )

    .rename(
        columns={

            "Ret_1":
                "MKT_Ret_1",

            "Ret_5":
                "MKT_Ret_5",

            "Ret_20":
                "MKT_Ret_20",

            "Vol_20":
                "MKT_Vol_20",

            "Drawdown_60":
                "MKT_Drawdown_60",
        }
    )
)


if B39_SPY.empty:

    raise RuntimeError(
        "SPY market-regime history is missing."
    )


B39_PRICE = (

    B39_PRICE

    .merge(

        B39_SPY,

        on="Date",

        how="left",

        validate="many_to_one",
    )
)


# ==============================================================================
# 6. EXACT FORWARD EXECUTION TARGETS
# ==============================================================================

# Entry:
#
#       next session adjusted Open
#
# Exit:
#
#       adjusted Close after h sessions
#
# All shift operations are ticker-local.


B39_PRICE[
    "Entry_Date"
] = g[
    "Date"
].shift(
    -1
)


B39_PRICE[
    "Entry_Adj_Open"
] = g[
    "Adj_Open"
].shift(
    -1
)


for horizon in B39_HORIZONS:

    B39_PRICE[
        f"Exit_Date_{horizon}D"
    ] = g[
        "Date"
    ].shift(
        -horizon
    )


    B39_PRICE[
        f"Exit_Adj_Close_{horizon}D"
    ] = g[
        "Adj_Close"
    ].shift(
        -horizon
    )


    B39_PRICE[
        f"Target_{horizon}D"
    ] = (

        B39_PRICE[
            f"Exit_Adj_Close_{horizon}D"
        ]

        /

        B39_PRICE[
            "Entry_Adj_Open"
        ]

        -

        1.0
    )


# Maximum-horizon target availability.

B39_PRICE[
    "Target_Available_Date"
] = B39_PRICE[
    "Exit_Date_20D"
]


# ==============================================================================
# 7. DAILYIZE MULTI-HORIZON TARGET
# ==============================================================================

for horizon in B39_HORIZONS:

    target = B39_PRICE[
        f"Target_{horizon}D"
    ]


    valid_target = (

        np.isfinite(
            target
        )

        &

        (
            target
            >
            -0.999999
        )
    )


    B39_PRICE[
        f"Target_LogDaily_{horizon}D"
    ] = np.nan


    B39_PRICE.loc[

        valid_target,

        f"Target_LogDaily_{horizon}D",

    ] = (

        np.log1p(

            B39_PRICE.loc[
                valid_target,
                f"Target_{horizon}D"
            ]
        )

        /

        float(
            horizon
        )
    )


B39_PRICE[
    "Target_Composite_LogDaily"
] = (

    B39_PRICE[
        [
            "Target_LogDaily_1D",
            "Target_LogDaily_5D",
            "Target_LogDaily_20D",
        ]
    ]

    .mean(
        axis=1,
        skipna=False,
    )
)


B39_PRICE[
    "Target_Composite_Daily"
] = np.expm1(

    B39_PRICE[
        "Target_Composite_LogDaily"
    ]
)


# ==============================================================================
# 8. JOIN POINT-IN-TIME ELIGIBILITY
# ==============================================================================

B39_ELIGIBILITY = (

    V4_DAILY_PANEL[
        [
            "Date",
            "Ticker",
            "Asset_Type",
            "Eligible",
        ]
    ]

    .drop_duplicates(
        [
            "Date",
            "Ticker",
        ]
    )
)


B39_SIGNAL_PANEL = (

    B39_ELIGIBILITY

    .merge(

        B39_PRICE[
            [
                "Date",
                "Ticker",

                "Ret_1",
                "Ret_5",
                "Ret_20",
                "Ret_60",
                "Ret_120",

                "Vol_20",
                "Vol_60",

                "Drawdown_60",

                "Intraday_Return",
                "Gap_Return",

                "Range_20",

                "Log_Dollar_Volume_60",
                "Volume_Ratio_20",

                "MKT_Ret_1",
                "MKT_Ret_5",
                "MKT_Ret_20",
                "MKT_Vol_20",
                "MKT_Drawdown_60",

                "Target_1D",
                "Target_5D",
                "Target_20D",

                "Target_Composite_Daily",

                "Target_Available_Date",
            ]
        ],

        on=[
            "Date",
            "Ticker",
        ],

        how="left",

        validate="one_to_one",
    )
)


B39_SIGNAL_PANEL = (

    B39_SIGNAL_PANEL[
        B39_SIGNAL_PANEL[
            "Eligible"
        ]
    ]

    .copy()
)


# ==============================================================================
# 9. CROSS-SECTIONAL NORMALIZATION
# ==============================================================================

# Asset-specific information is represented as same-day percentile ranks.

B39_ASSET_RAW_FEATURES = [

    "Ret_1",
    "Ret_5",
    "Ret_20",
    "Ret_60",
    "Ret_120",

    "Vol_20",
    "Vol_60",

    "Drawdown_60",

    "Intraday_Return",
    "Gap_Return",

    "Range_20",

    "Log_Dollar_Volume_60",
    "Volume_Ratio_20",
]


B39_XS_FEATURES = []


for feature in B39_ASSET_RAW_FEATURES:

    output = (
        f"XS_{feature}"
    )


    B39_SIGNAL_PANEL[
        output
    ] = (

        B39_SIGNAL_PANEL

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


    B39_XS_FEATURES.append(
        output
    )


B39_MARKET_FEATURES = [

    "MKT_Ret_1",
    "MKT_Ret_5",
    "MKT_Ret_20",
    "MKT_Vol_20",
    "MKT_Drawdown_60",
]


B39_MODEL_FEATURES = (

    B39_XS_FEATURES

    +

    B39_MARKET_FEATURES
)


# ==============================================================================
# 10. FINAL MODEL PANEL
# ==============================================================================

B39_MODEL_PANEL = (

    B39_SIGNAL_PANEL

    .replace(
        [
            np.inf,
            -np.inf,
        ],
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


for column in B39_MODEL_FEATURES:

    B39_MODEL_PANEL[
        column
    ] = pd.to_numeric(

        B39_MODEL_PANEL[
            column
        ],

        errors="coerce",

    ).astype(
        "float32"
    )


# ==============================================================================
# 11. PREDICTION DATES
# ==============================================================================

B39_FEATURE_COMPLETE = (

    B39_MODEL_PANEL[
        B39_MODEL_FEATURES
    ]

    .notna()

    .all(
        axis=1
    )
)


B39_MODEL_PANEL[
    "Feature_Complete"
] = B39_FEATURE_COMPLETE


B39_DATE_COUNTS = (

    B39_MODEL_PANEL[
        B39_MODEL_PANEL[
            "Feature_Complete"
        ]
    ]

    .groupby(
        "Date"
    )[
        "Ticker"
    ]

    .nunique()
)


B39_PREDICTION_DATES = (

    B39_DATE_COUNTS[

        (
            B39_DATE_COUNTS.index
            >=
            pd.Timestamp(
                V4_COMPARISON_START
            )
        )

        &

        (
            B39_DATE_COUNTS
            >=
            B39_MIN_PRED_ASSETS
        )
    ]

    .index

    .sort_values()
)


if len(
    B39_PREDICTION_DATES
) == 0:

    raise RuntimeError(
        "BLOCK 39 has zero valid prediction dates."
    )


print(
    "\nEligible prediction dates:",
    f"{len(B39_PREDICTION_DATES):,}"
)


# ==============================================================================
# 12. MODEL FACTORIES — NO PARAMETER SEARCH
# ==============================================================================

def b39_make_ridge():

    return Pipeline(
        [
            (
                "scale",
                StandardScaler(),
            ),

            (
                "ridge",
                Ridge(),
            ),
        ]
    )


def b39_make_hgb():

    return HistGradientBoostingRegressor(
        random_state=42,
    )


# ==============================================================================
# 13. STRICT WALK-FORWARD
# ==============================================================================

prediction_parts = []

ridge_model = None
hgb_model = None

last_refit_index = None

successful_refits = 0

t0 = time.time()


for date_index, prediction_date in enumerate(
    B39_PREDICTION_DATES
):

    current = (

        B39_MODEL_PANEL[

            (
                B39_MODEL_PANEL[
                    "Date"
                ]
                ==
                prediction_date
            )

            &

            (
                B39_MODEL_PANEL[
                    "Feature_Complete"
                ]
            )
        ]

        .copy()
    )


    if len(
        current
    ) < B39_MIN_PRED_ASSETS:

        continue


    need_refit = (

        ridge_model is None

        or

        hgb_model is None

        or

        last_refit_index is None

        or

        (
            date_index
            -
            last_refit_index
        )
        >=
        B39_REFIT_EVERY
    )


    if need_refit:

        eligible_train = (

            B39_MODEL_PANEL[

                (
                    B39_MODEL_PANEL[
                        "Target_Available_Date"
                    ]
                    <
                    prediction_date
                )

                &

                (
                    B39_MODEL_PANEL[
                        "Target_Composite_Daily"
                    ]
                    .notna()
                )

                &

                (
                    B39_MODEL_PANEL[
                        "Feature_Complete"
                    ]
                )
            ]

            .copy()
        )


        available_train_dates = (

            eligible_train[
                "Date"
            ]

            .drop_duplicates()

            .sort_values()
        )


        if len(
            available_train_dates
        ) < B39_MIN_TRAIN_DAYS:

            continue


        selected_train_dates = (

            available_train_dates

            .tail(
                B39_TRAIN_LOOKBACK_DAYS
            )
        )


        train = (

            eligible_train[

                eligible_train[
                    "Date"
                ]
                .isin(
                    selected_train_dates
                )
            ]

            .copy()
        )


        if train[
            "Date"
        ].nunique() < B39_MIN_TRAIN_DAYS:

            continue


        X_train = (

            train[
                B39_MODEL_FEATURES
            ]

            .to_numpy(
                dtype=np.float32
            )
        )


        y_train_bps = (

            train[
                "Target_Composite_Daily"
            ]

            .to_numpy(
                dtype=np.float64
            )

            *

            10000.0
        )


        finite_train = (

            np.isfinite(
                X_train
            )
            .all(
                axis=1
            )

            &

            np.isfinite(
                y_train_bps
            )
        )


        X_train = X_train[
            finite_train
        ]


        y_train_bps = y_train_bps[
            finite_train
        ]


        if len(
            y_train_bps
        ) < 10000:

            continue


        ridge_model = (
            b39_make_ridge()
        )


        hgb_model = (
            b39_make_hgb()
        )


        with warnings.catch_warnings():

            warnings.simplefilter(
                "ignore"
            )


            ridge_model.fit(
                X_train,
                y_train_bps,
            )


            hgb_model.fit(
                X_train,
                y_train_bps,
            )


        last_refit_index = (
            date_index
        )


        successful_refits += 1


        print(
            f"[39] REFIT "
            f"{successful_refits:02d} "
            f"| {prediction_date.date()} "
            f"| dates={len(selected_train_dates):3d} "
            f"| rows={len(y_train_bps):,}"
        )


    if (
        ridge_model is None
        or
        hgb_model is None
    ):

        continue


    X_current = (

        current[
            B39_MODEL_FEATURES
        ]

        .to_numpy(
            dtype=np.float32
        )
    )


    ridge_pred_bps = (

        ridge_model.predict(
            X_current
        )
    )


    hgb_pred_bps = (

        hgb_model.predict(
            X_current
        )
    )


    result = current[
        [
            "Date",
            "Ticker",
            "Asset_Type",

            "Target_1D",
            "Target_5D",
            "Target_20D",

            "Target_Composite_Daily",

            "Target_Available_Date",
        ]
    ].copy()


    result[
        "Mu_RIDGE"
    ] = (

        ridge_pred_bps

        /

        10000.0
    )


    result[
        "Mu_HGB"
    ] = (

        hgb_pred_bps

        /

        10000.0
    )


    prediction_parts.append(
        result
    )


if not prediction_parts:

    raise RuntimeError(
        "BLOCK 39 produced zero OOS predictions."
    )


BLOCK39_PREDICTIONS = (

    pd.concat(
        prediction_parts,
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


print(
    "\nWalk-forward seconds:",
    round(
        time.time() - t0,
        1,
    )
)


print(
    "Successful refits:",
    successful_refits
)


print(
    "Prediction rows:",
    f"{len(BLOCK39_PREDICTIONS):,}"
)


print(
    "Prediction dates:",
    f"{BLOCK39_PREDICTIONS['Date'].nunique():,}"
)


# ==============================================================================
# 14. OOS DIAGNOSTICS
# ==============================================================================

diagnostic_rows = []


for prediction_date, section in (

    BLOCK39_PREDICTIONS

    .groupby(
        "Date",
        sort=True,
    )
):

    n_assets = len(
        section
    )


    if n_assets < B39_MIN_PRED_ASSETS:

        continue


    tail_n = max(

        1,

        int(
            np.ceil(
                n_assets
                *
                B39_DIAGNOSTIC_TAIL_FRAC
            )
        ),
    )


    for model_name, prediction_column in [
        (
            "RIDGE",
            "Mu_RIDGE",
        ),
        (
            "HGB",
            "Mu_HGB",
        ),
    ]:

        pred = section[
            prediction_column
        ].to_numpy(
            dtype=float
        )


        record = {

            "Date":
                prediction_date,

            "Year":
                pd.Timestamp(
                    prediction_date
                ).year,

            "Model":
                model_name,

            "Assets":
                n_assets,
        }


        for target_name, target_column in [

            (
                "Composite",
                "Target_Composite_Daily",
            ),

            (
                "1D",
                "Target_1D",
            ),

            (
                "5D",
                "Target_5D",
            ),

            (
                "20D",
                "Target_20D",
            ),
        ]:

            realized = section[
                target_column
            ].to_numpy(
                dtype=float
            )


            valid = (

                np.isfinite(
                    pred
                )

                &

                np.isfinite(
                    realized
                )
            )


            if valid.sum() >= 20:

                ic = spearmanr(

                    pred[
                        valid
                    ],

                    realized[
                        valid
                    ],

                ).statistic


            else:

                ic = np.nan


            record[
                f"IC_{target_name}"
            ] = ic


        valid_1d = (

            np.isfinite(
                pred
            )

            &

            np.isfinite(

                section[
                    "Target_1D"
                ]

                .to_numpy(
                    dtype=float
                )
            )
        )


        if valid_1d.sum() >= 20:

            temp_pred = pred[
                valid_1d
            ]


            temp_realized = (

                section[
                    "Target_1D"
                ]

                .to_numpy(
                    dtype=float
                )[
                    valid_1d
                ]
            )


            effective_tail_n = min(

                tail_n,

                max(
                    1,

                    len(
                        temp_pred
                    )
                    //
                    2,
                )
            )


            order = np.argsort(
                temp_pred
            )


            bottom_idx = order[
                :effective_tail_n
            ]


            top_idx = order[
                -effective_tail_n:
            ]


            top_return = float(

                np.mean(
                    temp_realized[
                        top_idx
                    ]
                )
            )


            bottom_return = float(

                np.mean(
                    temp_realized[
                        bottom_idx
                    ]
                )
            )


            record[
                "Top10_1D_bps"
            ] = (

                top_return
                *
                10000.0
            )


            record[
                "Bottom10_1D_bps"
            ] = (

                bottom_return
                *
                10000.0
            )


            record[
                "TopMinusBottom_1D_bps"
            ] = (

                (
                    top_return
                    -
                    bottom_return
                )

                *

                10000.0
            )


        else:

            record[
                "Top10_1D_bps"
            ] = np.nan


            record[
                "Bottom10_1D_bps"
            ] = np.nan


            record[
                "TopMinusBottom_1D_bps"
            ] = np.nan


        diagnostic_rows.append(
            record
        )


BLOCK39_DIAGNOSTICS = pd.DataFrame(
    diagnostic_rows
)


# ==============================================================================
# 15. GLOBAL SUMMARY
# ==============================================================================

summary_rows = []


for model_name, section in (

    BLOCK39_DIAGNOSTICS

    .groupby(
        "Model"
    )
):

    summary_rows.append(
        {

            "Model":
                model_name,

            "Events":
                len(
                    section
                ),

            "Mean_Composite_IC":
                section[
                    "IC_Composite"
                ]
                .mean(),

            "Median_Composite_IC":
                section[
                    "IC_Composite"
                ]
                .median(),

            "Positive_Composite_IC_Pct":
                (
                    section[
                        "IC_Composite"
                    ]
                    >
                    0
                )
                .mean()
                *
                100.0,

            "Mean_1D_IC":
                section[
                    "IC_1D"
                ]
                .mean(),

            "Mean_5D_IC":
                section[
                    "IC_5D"
                ]
                .mean(),

            "Mean_20D_IC":
                section[
                    "IC_20D"
                ]
                .mean(),

            "Mean_Top10_1D_bps":
                section[
                    "Top10_1D_bps"
                ]
                .mean(),

            "Mean_Bottom10_1D_bps":
                section[
                    "Bottom10_1D_bps"
                ]
                .mean(),

            "Mean_TopBottom_1D_bps":
                section[
                    "TopMinusBottom_1D_bps"
                ]
                .mean(),

            "Positive_TopBottom_Pct":
                (
                    section[
                        "TopMinusBottom_1D_bps"
                    ]
                    >
                    0
                )
                .mean()
                *
                100.0,
        }
    )


BLOCK39_SUMMARY = (

    pd.DataFrame(
        summary_rows
    )

    .set_index(
        "Model"
    )
)


# ==============================================================================
# 16. YEAR-BY-YEAR STABILITY
# ==============================================================================

BLOCK39_YEARLY = (

    BLOCK39_DIAGNOSTICS

    .groupby(
        [
            "Year",
            "Model",
        ]
    )

    .agg(

        Events=(
            "Date",
            "size",
        ),

        Composite_IC=(
            "IC_Composite",
            "mean",
        ),

        IC_1D=(
            "IC_1D",
            "mean",
        ),

        IC_5D=(
            "IC_5D",
            "mean",
        ),

        IC_20D=(
            "IC_20D",
            "mean",
        ),

        Top10_1D_bps=(
            "Top10_1D_bps",
            "mean",
        ),

        TopBottom_1D_bps=(
            "TopMinusBottom_1D_bps",
            "mean",
        ),
    )

    .reset_index()
)


# ==============================================================================
# 17. LATEST FORECAST SNAPSHOT
# ==============================================================================

B39_LATEST_DATE = (

    BLOCK39_PREDICTIONS[
        "Date"
    ]

    .max()
)


BLOCK39_LATEST_FORECASTS = (

    BLOCK39_PREDICTIONS[

        BLOCK39_PREDICTIONS[
            "Date"
        ]
        ==
        B39_LATEST_DATE
    ]

    [
        [
            "Ticker",
            "Asset_Type",
            "Mu_RIDGE",
            "Mu_HGB",
        ]
    ]

    .copy()
)


BLOCK39_LATEST_FORECASTS[
    "RIDGE_bps"
] = (

    BLOCK39_LATEST_FORECASTS[
        "Mu_RIDGE"
    ]

    *

    10000.0
)


BLOCK39_LATEST_FORECASTS[
    "HGB_bps"
] = (

    BLOCK39_LATEST_FORECASTS[
        "Mu_HGB"
    ]

    *

    10000.0
)


# ==============================================================================
# 18. TQQQ FORECAST AUDIT
# ==============================================================================

BLOCK39_TQQQ = (

    BLOCK39_PREDICTIONS[

        BLOCK39_PREDICTIONS[
            "Ticker"
        ]
        ==
        "TQQQ"
    ]

    [
        [
            "Date",
            "Mu_RIDGE",
            "Mu_HGB",
            "Target_1D",
        ]
    ]

    .copy()
)


# ==============================================================================
# 19. BLOCK-39 FINGERPRINT
# ==============================================================================

B39_FINGERPRINT_PAYLOAD = {

    "parent":
        V4_MASTER_FINGERPRINT,

    "config":
        B39_CONFIG,

    "features":
        B39_MODEL_FEATURES,
}


BLOCK39_FINGERPRINT = (

    hashlib.sha256(

        json.dumps(

            B39_FINGERPRINT_PAYLOAD,

            sort_keys=True,

            default=str,

        ).encode(
            "utf-8"
        )
    )

    .hexdigest()
)


# ==============================================================================
# 20. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 118
)


print(
    "BLOCK 39 — RESULTS"
)


print(
    "=" * 118
)


print(
    "\n1) STRICT OOS ALPHA SUMMARY"
)


display(
    BLOCK39_SUMMARY.round(
        6
    )
)


print(
    "\n2) YEAR-BY-YEAR STABILITY"
)


display(
    BLOCK39_YEARLY.round(
        6
    )
)


print(
    f"\n3) LATEST RIDGE TOP-20 @ "
    f"{B39_LATEST_DATE.date()}"
)


display(

    BLOCK39_LATEST_FORECASTS

    .sort_values(
        "RIDGE_bps",
        ascending=False,
    )

    .head(
        20
    )

    [
        [
            "Ticker",
            "Asset_Type",
            "RIDGE_bps",
            "HGB_bps",
        ]
    ]

    .round(
        4
    )
)


print(
    f"\n4) LATEST HGB TOP-20 @ "
    f"{B39_LATEST_DATE.date()}"
)


display(

    BLOCK39_LATEST_FORECASTS

    .sort_values(
        "HGB_bps",
        ascending=False,
    )

    .head(
        20
    )

    [
        [
            "Ticker",
            "Asset_Type",
            "RIDGE_bps",
            "HGB_bps",
        ]
    ]

    .round(
        4
    )
)


print(
    "\n5) TQQQ LATEST FORECAST"
)


display(

    BLOCK39_TQQQ

    .tail(
        10
    )

    .assign(

        RIDGE_bps=lambda x:
            x[
                "Mu_RIDGE"
            ]
            *
            10000.0,

        HGB_bps=lambda x:
            x[
                "Mu_HGB"
            ]
            *
            10000.0,
    )

    [
        [
            "Date",
            "RIDGE_bps",
            "HGB_bps",
            "Target_1D",
        ]
    ]

    .round(
        6
    )
)


print(
    "\nBLOCK 39 FINGERPRINT:"
)


print(
    BLOCK39_FINGERPRINT
)


print(
    "\n"
    +
    "=" * 118
)


print(
    "BLOCK 39 — RESEARCH VERDICT"
)


print(
    "=" * 118
)


print(
    "\nNO MODEL IS SELECTED HERE."
)


print(
    "RIDGE and HGB both proceed to the SAME portfolio optimizer."
)


print(
    "IC / top-tail diagnostics are descriptive only."
)


print(
    "The final criterion remains OUT-OF-SAMPLE NET PORTFOLIO WEALTH."
)


print(
    "\n[+] BLOCK 39 PASSED."
)


print(
    "[+] NEXT: BLOCK 40 — NET-RETURN PORTFOLIO OPTIMIZER."
)
