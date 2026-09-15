# Historical calendar check before the expensive V7 model fitting.
import pandas as pd
import numpy as np
if pd.Timestamp(B41_START_DATE).normalize() != pd.Timestamp("2023-10-18"):
    raise RuntimeError("Run corrected Module 17, then Modules 18-21 before Module 22.")
if pd.Timestamp(B41_END_DATE).normalize() != pd.Timestamp("2026-07-27"):
    raise RuntimeError("Historical end date is not 2026-07-27.")
_m22_tqqq = BLOCK41_SUMMARY.loc[
    BLOCK41_SUMMARY.Strategy == "TQQQ_BH_NET_2BPS", "Final_Wealth"
]
if len(_m22_tqqq) != 1 or abs(float(_m22_tqqq.iloc[0]) - 3.488303) > 0.00000051:
    raise RuntimeError("Historical open-based TQQQ does not match 3.488303. Check the price cache before fitting V7.")

# ==============================================================================
# MODULE 22 — HISTORICAL V7 ONE-SHOT
# Exact recovered V7 architecture; trading/model logic below is unchanged.
# ==============================================================================

# ==============================================================================
# V7 ONE-SHOT
# MULTI-HORIZON NONLINEAR ALPHA + TQQQ CORE + GROWTH/KELLY ALLOCATION
# ==============================================================================
#
# OBJECTIVE
# ---------
# MAXIMIZE NET COMPOUNDED PORTFOLIO WEALTH.
#
#
# DECISION FREQUENCY
# ------------------
# Every 21 trading sessions (~1 month).
#
#
# FOUR FORECAST HORIZONS
# ----------------------
#
#       21 sessions   ~ 1 month
#       63 sessions   ~ 3 months
#       126 sessions  ~ 6 months
#       252 sessions  ~ 1 year
#
#
# TARGET
# ------
# For every stock and horizon h:
#
#       log(stock forward return)
#       -
#       log(TQQQ forward return)
#
#
# MODEL
# -----
# Four separate HistGradientBoostingRegressor models.
#
# No hyperparameter search.
# sklearn default architecture.
#
#
# CROSS-HORIZON AGGREGATION
# -------------------------
# Predictions are:
#
#   1. dailyized
#   2. independently cross-sectionally ranked
#   3. combined by MEDIAN
#
# Median is used instead of an optimized blend.
#
#
# PORTFOLIO
# ---------
#
#       (1-f) * TQQQ
#       +
#       f * diversified alpha sleeve
#
# where
#
#       f = expected daily sleeve alpha / relative-return variance
#
# clipped naturally to [0,1].
#
# This is unlevered full-Kelly BETWEEN the alpha sleeve and TQQQ.
#
#
# ALPHA SLEEVE
# ------------
# No Top-K.
# No single-name cap.
# No sector cap.
#
# Stocks must have:
#
#       consensus rank > median
#       AND
#       positive expected TQQQ-relative return
#
# Weights increase smoothly with score and decrease with
# recent TQQQ-relative volatility.
#
#
# COST AWARENESS
# --------------
# Proposed overlay is accepted only if predicted incremental alpha
# exceeds its incremental transaction cost versus returning to 100% TQQQ.
#
#
# IMPORTANT
# ---------
# This remains a DEVELOPMENT BACKCAST because 2023-2026 has already
# been observed during prior model generations.
#
# If V7 wins:
#       FREEZE.
#
# If V7 loses:
#       DO NOT tune these horizons/models on the same history.
#
# ==============================================================================


import gc
import json
import hashlib
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import HistGradientBoostingRegressor

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V7_REQUIRED = [

    "B39_MODEL_PANEL",
    "B39_MODEL_FEATURES",

    "B41_OPEN_WIDE",
    "B41_CLOSE_WIDE",

    "B41_START_DATE",
    "B41_END_DATE",

    "B40_TCA_RATE",
    "B40_TCA_BPS",

    "BLOCK41_SUMMARY",

    "b41_realized_asset_returns",

    "V4_FINAL_RESEARCH_FINGERPRINT",
]


V7_MISSING = [

    obj
    for obj in V7_REQUIRED
    if obj not in globals()
]


if V7_MISSING:

    raise RuntimeError(

        "V7 missing required objects: "

        f"{V7_MISSING}"
    )


print("=" * 124)

print(
    "V7 — MULTI-HORIZON NONLINEAR ALPHA + TQQQ CORE + KELLY"
)

print("=" * 124)


# ==============================================================================
# 1. FROZEN ARCHITECTURE
# ==============================================================================

V7_HORIZONS = (
    21,
    63,
    126,
    252,
)


# Monthly portfolio decision.

V7_REBALANCE_SESSIONS = 21


# Models refit every quarter.
#
# This is computational scheduling, not alpha selection.

V7_REFIT_EVERY_DECISIONS = 3


# Weekly thinning of historical training observations.
#
# Portfolio still trades monthly.
#
# This materially reduces duplicated overlapping rows without selecting
# performance-based dates.

V7_TRAIN_SAMPLE_STEP = 5


# Relative-risk window.
# 63 sessions = the predefined 3-month horizon.

V7_RELATIVE_RISK_LOOKBACK = 63


V7_MIN_CURRENT_ASSETS = 500

V7_MIN_TRAIN_DATES = 20

V7_MIN_TRAIN_ROWS = 10_000


V7_START = pd.Timestamp(
    B41_START_DATE
).normalize()


V7_END = pd.Timestamp(
    B41_END_DATE
).normalize()


print(
    "\nDecision frequency :",
    V7_REBALANCE_SESSIONS,
    "sessions"
)

print(
    "Forecast horizons  :",
    V7_HORIZONS
)

print(
    "Nonlinear models   : 4 × HistGradientBoostingRegressor"
)

print(
    "Model search       : NONE"
)

print(
    "Core asset         : TQQQ"
)

print(
    "Cash               : NONE"
)

print(
    "Single-name cap    : NONE"
)

print(
    "Sector cap         : NONE"
)

print(
    "TCA                :",
    f"{B40_TCA_BPS:.2f} bps"
)

print(
    "\nIMPORTANT: DEVELOPMENT BACKCAST — NOT PROSPECTIVE OOS."
)


# ==============================================================================
# 2. CANONICAL PRICES
# ==============================================================================

V7_OPEN = (
    B41_OPEN_WIDE
    .copy()
    .sort_index()
)


V7_CLOSE = (
    B41_CLOSE_WIDE
    .copy()
    .sort_index()
)


V7_OPEN.index = (

    pd.DatetimeIndex(
        V7_OPEN.index
    )
    .normalize()
)


V7_CLOSE.index = (

    pd.DatetimeIndex(
        V7_CLOSE.index
    )
    .normalize()
)


V7_OPEN = (

    V7_OPEN

    .groupby(
        level=0
    )

    .last()

    .sort_index()
)


V7_CLOSE = (

    V7_CLOSE

    .groupby(
        level=0
    )

    .last()

    .sort_index()
)


if "SPY" not in V7_CLOSE.columns:

    raise RuntimeError(
        "SPY missing from V7 prices."
    )


if "QQQ" not in V7_CLOSE.columns:

    raise RuntimeError(
        "QQQ missing from V7 prices."
    )


if "TQQQ" not in V7_CLOSE.columns:

    raise RuntimeError(
        "TQQQ missing from V7 prices."
    )


# Common market calendar.

V7_CALENDAR = (

    V7_CLOSE[
        "SPY"
    ]

    .dropna()

    .index

    .sort_values()
)


V7_OPEN = V7_OPEN.reindex(
    V7_CALENDAR
)


V7_CLOSE = V7_CLOSE.reindex(
    V7_CALENDAR
)


V7_RETURNS = (

    V7_CLOSE

    .pct_change(
        fill_method=None
    )
)


V7_TQQQ_RETURNS = (

    V7_RETURNS[
        "TQQQ"
    ]
)


V7_CALENDAR_POS = {

    pd.Timestamp(date):
        i

    for i, date in enumerate(
        V7_CALENDAR
    )
}


if V7_START not in V7_CALENDAR_POS:

    raise RuntimeError(
        f"V7 start {V7_START.date()} missing."
    )


if V7_END not in V7_CALENDAR_POS:

    raise RuntimeError(
        f"V7 end {V7_END.date()} missing."
    )


V7_START_POS = (
    V7_CALENDAR_POS[
        V7_START
    ]
)


V7_END_POS = (
    V7_CALENDAR_POS[
        V7_END
    ]
)


# ==============================================================================
# 3. MODEL PANEL
# ==============================================================================

V7_PANEL = (

    B39_MODEL_PANEL

    .copy()
)


V7_PANEL[
    "Date"
] = (

    pd.to_datetime(
        V7_PANEL[
            "Date"
        ]
    )

    .dt.normalize()
)


V7_PANEL = (

    V7_PANEL[

        (
            V7_PANEL[
                "Feature_Complete"
            ]
        )

        &

        (
            V7_PANEL[
                "Asset_Type"
            ]
            ==
            "STOCK"
        )
    ]

    .copy()
)


V7_PANEL[
    "Date_Pos"
] = (

    V7_PANEL[
        "Date"
    ]

    .map(
        V7_CALENDAR_POS
    )
)


V7_PANEL = (

    V7_PANEL

    .dropna(
        subset=[
            "Date_Pos"
        ]
    )

    .copy()
)


V7_PANEL[
    "Date_Pos"
] = (

    V7_PANEL[
        "Date_Pos"
    ]

    .astype(
        int
    )
)


# ==============================================================================
# 4. FAST WIDE -> LONG MAPPER
# ==============================================================================

def v7_map_wide_to_panel(
    wide,
    panel,
):

    row_idx = (

        wide.index

        .get_indexer(
            panel[
                "Date"
            ]
        )
    )


    col_idx = (

        wide.columns

        .get_indexer(
            panel[
                "Ticker"
            ]
        )
    )


    output = np.full(
        len(
            panel
        ),
        np.nan,
        dtype=float,
    )


    valid = (

        (row_idx >= 0)

        &

        (col_idx >= 0)
    )


    array = wide.to_numpy(
        dtype=float,
        copy=False,
    )


    output[
        valid
    ] = array[

        row_idx[
            valid
        ],

        col_idx[
            valid
        ],
    ]


    return output


# ==============================================================================
# 5. LONGER-HORIZON TREND FEATURES
# ==============================================================================

# Existing Block-39 features already contain:
#
#   1 / 5 / 20 / 60 / 120-day momentum
#   volatility
#   drawdown
#   gap
#   intraday move
#   liquidity
#   volume shock
#   market-state variables
#
# Add canonical 12-month and 12-1 momentum.

with np.errstate(
    divide="ignore",
    invalid="ignore",
):

    V7_RET252_WIDE = (

        V7_CLOSE

        /

        V7_CLOSE.shift(
            252
        )

        -

        1.0
    )


    V7_MOM12_1_WIDE = (

        V7_CLOSE.shift(
            21
        )

        /

        V7_CLOSE.shift(
            252
        )

        -

        1.0
    )


V7_PANEL[
    "V7_Ret252"
] = v7_map_wide_to_panel(

    V7_RET252_WIDE,

    V7_PANEL,
)


V7_PANEL[
    "V7_Mom12_1"
] = v7_map_wide_to_panel(

    V7_MOM12_1_WIDE,

    V7_PANEL,
)


del V7_RET252_WIDE
del V7_MOM12_1_WIDE

gc.collect()


V7_PANEL[
    "XS_V7_Ret252"
] = (

    V7_PANEL

    .groupby(
        "Date"
    )[
        "V7_Ret252"
    ]

    .rank(
        pct=True,
        method="average",
    )
)


V7_PANEL[
    "XS_V7_Mom12_1"
] = (

    V7_PANEL

    .groupby(
        "Date"
    )[
        "V7_Mom12_1"
    ]

    .rank(
        pct=True,
        method="average",
    )
)


# ==============================================================================
# 6. QQQ MULTI-HORIZON MARKET-STATE FEATURES
# ==============================================================================

QQQ_CLOSE = (
    V7_CLOSE[
        "QQQ"
    ]
)


for horizon in V7_HORIZONS:

    qqq_feature = (

        QQQ_CLOSE

        /

        QQQ_CLOSE.shift(
            horizon
        )

        -

        1.0
    )


    V7_PANEL[
        f"MKT_QQQ_Ret_{horizon}"
    ] = (

        V7_PANEL[
            "Date"
        ]

        .map(
            qqq_feature
        )
    )


QQQ_RETURN = (

    QQQ_CLOSE

    .pct_change(
        fill_method=None
    )
)


V7_QQQ_VOL21 = (

    QQQ_RETURN

    .rolling(
        21,
        min_periods=15,
    )

    .std()
)


V7_QQQ_VOL63 = (

    QQQ_RETURN

    .rolling(
        63,
        min_periods=40,
    )

    .std()
)


V7_PANEL[
    "MKT_QQQ_Vol21"
] = (

    V7_PANEL[
        "Date"
    ]

    .map(
        V7_QQQ_VOL21
    )
)


V7_PANEL[
    "MKT_QQQ_Vol63"
] = (

    V7_PANEL[
        "Date"
    ]

    .map(
        V7_QQQ_VOL63
    )
)


# ==============================================================================
# 7. MODEL FEATURES
# ==============================================================================

V7_FEATURES = (

    list(
        B39_MODEL_FEATURES
    )

    +

    [
        "XS_V7_Ret252",
        "XS_V7_Mom12_1",

        "MKT_QQQ_Ret_21",
        "MKT_QQQ_Ret_63",
        "MKT_QQQ_Ret_126",
        "MKT_QQQ_Ret_252",

        "MKT_QQQ_Vol21",
        "MKT_QQQ_Vol63",
    ]
)


# Remove duplicates while preserving order.

V7_FEATURES = list(
    dict.fromkeys(
        V7_FEATURES
    )
)


# ==============================================================================
# 8. EXACT MULTI-HORIZON TQQQ-RELATIVE TARGETS
# ==============================================================================

# Signal:
#       Close(t)
#
# Entry:
#       Open(t+1)
#
# Exit:
#       Close(t+h)
#
# Target:
#       stock log return - TQQQ log return


V7_ENTRY_OPEN = (

    V7_OPEN.shift(
        -1
    )
)


for horizon in V7_HORIZONS:

    print(
        f"[V7] Building {horizon}-session relative target..."
    )


    exit_close = (

        V7_CLOSE.shift(
            -horizon
        )
    )


    with np.errstate(
        divide="ignore",
        invalid="ignore",
    ):

        log_return = np.log(

            exit_close

            /

            V7_ENTRY_OPEN
        )


    tqqq_log_return = (

        log_return[
            "TQQQ"
        ]
    )


    relative_log_return = (

        log_return

        .sub(
            tqqq_log_return,
            axis=0,
        )
    )


    V7_PANEL[
        f"Target_Excess_{horizon}"
    ] = v7_map_wide_to_panel(

        relative_log_return,

        V7_PANEL,
    )


    # Training target is resolved at Date_Pos + horizon.

    V7_PANEL[
        f"Exit_Pos_{horizon}"
    ] = (

        V7_PANEL[
            "Date_Pos"
        ]

        +

        horizon
    )


    del exit_close
    del log_return
    del relative_log_return

    gc.collect()


del V7_ENTRY_OPEN

gc.collect()


# ==============================================================================
# 9. COMPLETE FEATURE PANEL
# ==============================================================================

V7_PANEL = (

    V7_PANEL

    .replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )
)


V7_PANEL[
    "V7_Feature_Complete"
] = (

    V7_PANEL[
        V7_FEATURES
    ]

    .notna()

    .all(
        axis=1
    )
)


V7_FEATURE_COUNTS = (

    V7_PANEL[

        V7_PANEL[
            "V7_Feature_Complete"
        ]
    ]

    .groupby(
        "Date"
    )[
        "Ticker"
    ]

    .nunique()
)


eligible_feature_dates = (

    V7_FEATURE_COUNTS[

        V7_FEATURE_COUNTS
        >=
        V7_MIN_CURRENT_ASSETS
    ]

    .index
)


if len(
    eligible_feature_dates
) == 0:

    raise RuntimeError(
        "No V7 feature-complete broad-universe dates."
    )


V7_TRAIN_ANCHOR_DATE = pd.Timestamp(

    eligible_feature_dates.min()
)


V7_TRAIN_ANCHOR_POS = (

    V7_CALENDAR_POS[
        V7_TRAIN_ANCHOR_DATE
    ]
)


print(
    "\nFeature-complete training anchor:",
    V7_TRAIN_ANCHOR_DATE.date()
)


# ==============================================================================
# 10. COMPUTATIONAL TRAINING SAMPLE
# ==============================================================================

V7_TRAIN_PANEL = (

    V7_PANEL[

        (
            V7_PANEL[
                "V7_Feature_Complete"
            ]
        )

        &

        (
            V7_PANEL[
                "Date_Pos"
            ]
            >=
            V7_TRAIN_ANCHOR_POS
        )

        &

        (

            (
                V7_PANEL[
                    "Date_Pos"
                ]

                -

                V7_TRAIN_ANCHOR_POS
            )

            %

            V7_TRAIN_SAMPLE_STEP

            ==
            0
        )
    ]

    .copy()
)


print(
    "Weekly-thinned training rows:",
    f"{len(V7_TRAIN_PANEL):,}"
)

print(
    "Training dates:",
    V7_TRAIN_PANEL[
        "Date"
    ]
    .nunique()
)


# ==============================================================================
# 11. MONTHLY EVALUATION SCHEDULE
# ==============================================================================

execution_positions = list(

    range(

        V7_START_POS,

        V7_END_POS + 1,

        V7_REBALANCE_SESSIONS,
    )
)


schedule_rows = []


for i, execution_pos in enumerate(
    execution_positions
):

    if execution_pos <= 0:

        continue


    signal_pos = (
        execution_pos
        -
        1
    )


    signal_date = pd.Timestamp(

        V7_CALENDAR[
            signal_pos
        ]
    )


    execution_date = pd.Timestamp(

        V7_CALENDAR[
            execution_pos
        ]
    )


    if i + 1 < len(
        execution_positions
    ):

        exit_date = pd.Timestamp(

            V7_CALENDAR[

                execution_positions[
                    i + 1
                ]
            ]
        )


        final_period = False


    else:

        exit_date = (
            V7_END
        )


        final_period = True


    schedule_rows.append(
        {

            "Signal_Pos":
                signal_pos,

            "Signal_Date":
                signal_date,

            "Execution_Pos":
                execution_pos,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Final_Period":
                final_period,
        }
    )


V7_SCHEDULE = pd.DataFrame(
    schedule_rows
)


print(
    "\nEvaluation decisions:",
    len(
        V7_SCHEDULE
    )
)


# ==============================================================================
# 12. NONLINEAR MODEL FACTORY
# ==============================================================================

def v7_make_model():

    # sklearn defaults.
    #
    # No grid search.
    # No performance-based parameter selection.

    return HistGradientBoostingRegressor(
        random_state=42,
    )


# ==============================================================================
# 13. PORTFOLIO HELPERS
# ==============================================================================

def v7_turnover(
    old_weights,
    new_weights,
):

    assets = (

        set(
            old_weights
        )

        |

        set(
            new_weights
        )
    )


    return float(

        sum(

            abs(

                new_weights.get(
                    asset,
                    0.0
                )

                -

                old_weights.get(
                    asset,
                    0.0
                )
            )

            for asset in assets
        )
    )


def v7_drift_weights(

    target_weights,

    realized_returns,

):

    end_values = {

        asset:

            weight

            *

            (
                1.0

                +

                realized_returns.get(
                    asset,
                    -1.0,
                )
            )

        for asset, weight
        in target_weights.items()
    }


    total = float(

        sum(
            end_values.values()
        )
    )


    if total <= 0:

        return {}


    return {

        asset:

            value

            /

            total

        for asset, value
        in end_values.items()

        if (

            np.isfinite(
                value
            )

            and

            value > 0
        )
    }


# ==============================================================================
# 14. WALK-FORWARD STATE
# ==============================================================================

V7_MODELS = {

    horizon:
        None

    for horizon in V7_HORIZONS
}


V7_WEALTH = 1.0

V7_PREVIOUS_WEIGHTS = {}

V7_PATH_ROWS = []

V7_WEIGHT_ROWS = []


# ==============================================================================
# 15. WALK FORWARD
# ==============================================================================

print(
    "\n[V7] Starting monthly nonlinear walk-forward..."
)


for period_no, row in enumerate(

    V7_SCHEDULE.itertuples(
        index=False
    ),

    start=1,

):

    signal_pos = int(
        row.Signal_Pos
    )


    signal_date = pd.Timestamp(
        row.Signal_Date
    )


    execution_date = pd.Timestamp(
        row.Execution_Date
    )


    exit_date = pd.Timestamp(
        row.Exit_Date
    )


    final_period = bool(
        row.Final_Period
    )


    # --------------------------------------------------------------------------
    # 15A. REFIT FOUR MODELS QUARTERLY
    # --------------------------------------------------------------------------

    refit_now = (

        period_no == 1

        or

        (
            (
                period_no
                -
                1
            )

            %

            V7_REFIT_EVERY_DECISIONS

            ==
            0
        )
    )


    if refit_now:

        print(
            f"[V7] REFIT @ {signal_date.date()}"
        )


        for horizon in V7_HORIZONS:

            target_col = (
                f"Target_Excess_{horizon}"
            )


            exit_pos_col = (
                f"Exit_Pos_{horizon}"
            )


            # STRICT:
            #
            # target must have fully resolved BEFORE current signal close.

            train = (

                V7_TRAIN_PANEL[

                    (
                        V7_TRAIN_PANEL[
                            exit_pos_col
                        ]
                        <
                        signal_pos
                    )

                    &

                    (
                        V7_TRAIN_PANEL[
                            target_col
                        ]
                        .notna()
                    )
                ]

                .dropna(
                    subset=
                        V7_FEATURES
                )

                .copy()
            )


            train_dates = (

                train[
                    "Date"
                ]
                .nunique()
            )


            if train_dates < V7_MIN_TRAIN_DATES:

                raise RuntimeError(

                    f"Horizon {horizon}: "
                    f"only {train_dates} resolved training dates "
                    f"at {signal_date.date()}."
                )


            if len(
                train
            ) < V7_MIN_TRAIN_ROWS:

                raise RuntimeError(

                    f"Horizon {horizon}: "
                    f"only {len(train):,} training rows."
                )


            X_train = (

                train[
                    V7_FEATURES
                ]

                .to_numpy(
                    dtype=np.float32
                )
            )


            # bps of log excess return.

            y_train = (

                train[
                    target_col
                ]

                .to_numpy(
                    dtype=np.float64
                )

                *

                10000.0
            )


            finite = (

                np.isfinite(
                    X_train
                )
                .all(
                    axis=1
                )

                &

                np.isfinite(
                    y_train
                )
            )


            X_train = X_train[
                finite
            ]


            y_train = y_train[
                finite
            ]


            model = (
                v7_make_model()
            )


            with warnings.catch_warnings():

                warnings.simplefilter(
                    "ignore"
                )


                model.fit(
                    X_train,
                    y_train,
                )


            V7_MODELS[
                horizon
            ] = model


            print(

                f"      h={horizon:3d}"
                f" | dates={train_dates:3d}"
                f" | rows={len(y_train):,}"
            )


    # --------------------------------------------------------------------------
    # 15B. CURRENT BROAD PIT CROSS-SECTION
    # --------------------------------------------------------------------------

    current = (

        V7_PANEL[

            (
                V7_PANEL[
                    "Date"
                ]
                ==
                signal_date
            )

            &

            (
                V7_PANEL[
                    "V7_Feature_Complete"
                ]
            )
        ]

        .dropna(
            subset=
                V7_FEATURES
        )

        .copy()
    )


    if len(
        current
    ) < V7_MIN_CURRENT_ASSETS:

        raise RuntimeError(

            f"Only {len(current)} V7 assets "
            f"at {signal_date.date()}."
        )


    X_current = (

        current[
            V7_FEATURES
        ]

        .to_numpy(
            dtype=np.float32
        )
    )


    # --------------------------------------------------------------------------
    # 15C. FOUR HORIZON FORECASTS
    # --------------------------------------------------------------------------

    rank_columns = []

    daily_prediction_columns = []


    for horizon in V7_HORIZONS:

        model = (
            V7_MODELS[
                horizon
            ]
        )


        if model is None:

            raise RuntimeError(
                f"Missing model for horizon {horizon}."
            )


        prediction = (

            model.predict(
                X_current
            )

            /

            10000.0
        )


        pred_col = (
            f"Pred_{horizon}"
        )


        daily_col = (
            f"Pred_Daily_{horizon}"
        )


        rank_col = (
            f"Pred_Rank_{horizon}"
        )


        current[
            pred_col
        ] = prediction


        current[
            daily_col
        ] = (

            prediction

            /

            float(
                horizon
            )
        )


        current[
            rank_col
        ] = (

            current[
                pred_col
            ]

            .rank(
                pct=True,
                method="average",
            )
        )


        rank_columns.append(
            rank_col
        )


        daily_prediction_columns.append(
            daily_col
        )


    # --------------------------------------------------------------------------
    # 15D. ROBUST CROSS-HORIZON CONSENSUS
    # --------------------------------------------------------------------------

    current[
        "Consensus_Rank"
    ] = (

        current[
            rank_columns
        ]

        .median(
            axis=1
        )
    )


    current[
        "Consensus_Daily_Excess"
    ] = (

        current[
            daily_prediction_columns
        ]

        .median(
            axis=1
        )
    )


    current[
        "Alpha_Score"
    ] = (

        current[
            "Consensus_Rank"
        ]

        -
        0.50
    )


    current[
        "Alpha_Score"
    ] = (

        current[
            "Alpha_Score"
        ]

        .clip(
            lower=0.0
        )
    )


    # Must also have positive expected TQQQ-relative return.

    alpha_candidates = (

        current[

            (
                current[
                    "Alpha_Score"
                ]
                >
                0
            )

            &

            (
                current[
                    "Consensus_Daily_Excess"
                ]
                >
                0
            )
        ]

        .copy()
    )


    # --------------------------------------------------------------------------
    # 15E. RELATIVE VOLATILITY
    # --------------------------------------------------------------------------

    if alpha_candidates.empty:

        alpha_sleeve = {}

        predicted_sleeve_daily_alpha = 0.0

        sleeve_relative_variance = np.nan

        raw_kelly_fraction = 0.0


    else:

        candidate_assets = (

            alpha_candidates[
                "Ticker"
            ]
            .tolist()
        )


        relative_history = (

            V7_RETURNS

            .loc[
                :
                signal_date,

                candidate_assets,
            ]

            .tail(
                V7_RELATIVE_RISK_LOOKBACK
            )

            .sub(
                V7_TQQQ_RETURNS
                .loc[
                    :
                    signal_date
                ]
                .tail(
                    V7_RELATIVE_RISK_LOOKBACK
                ),

                axis=0,
            )
        )


        relative_vol = (

            relative_history

            .std(
                axis=0,
                ddof=1,
            )
        )


        alpha_candidates[
            "Relative_Vol"
        ] = (

            alpha_candidates[
                "Ticker"
            ]

            .map(
                relative_vol
            )
        )


        alpha_candidates = (

            alpha_candidates[

                (
                    alpha_candidates[
                        "Relative_Vol"
                    ]
                    .notna()
                )

                &

                (
                    alpha_candidates[
                        "Relative_Vol"
                    ]
                    >
                    0
                )
            ]

            .copy()
        )


        if alpha_candidates.empty:

            alpha_sleeve = {}

            predicted_sleeve_daily_alpha = 0.0

            sleeve_relative_variance = np.nan

            raw_kelly_fraction = 0.0


        else:

            # --------------------------------------------------------------
            # Smooth score / relative-risk weighting.
            # --------------------------------------------------------------

            alpha_candidates[
                "Raw_Weight"
            ] = (

                alpha_candidates[
                    "Alpha_Score"
                ]

                /

                alpha_candidates[
                    "Relative_Vol"
                ]
            )


            raw_sum = float(

                alpha_candidates[
                    "Raw_Weight"
                ]
                .sum()
            )


            if (

                not np.isfinite(
                    raw_sum
                )

                or

                raw_sum <= 0
            ):

                alpha_sleeve = {}

                predicted_sleeve_daily_alpha = 0.0

                sleeve_relative_variance = np.nan

                raw_kelly_fraction = 0.0


            else:

                alpha_candidates[
                    "Sleeve_Weight"
                ] = (

                    alpha_candidates[
                        "Raw_Weight"
                    ]

                    /

                    raw_sum
                )


                alpha_sleeve = {

                    ticker:
                        float(
                            weight
                        )

                    for ticker, weight in zip(

                        alpha_candidates[
                            "Ticker"
                        ],

                        alpha_candidates[
                            "Sleeve_Weight"
                        ],
                    )
                }


                predicted_sleeve_daily_alpha = float(

                    np.sum(

                        alpha_candidates[
                            "Sleeve_Weight"
                        ]

                        *

                        alpha_candidates[
                            "Consensus_Daily_Excess"
                        ]
                    )
                )


                # ----------------------------------------------------------
                # Historical relative variance of CURRENT sleeve vs TQQQ.
                # ----------------------------------------------------------

                assets = list(
                    alpha_sleeve
                )


                weights = np.asarray(

                    [

                        alpha_sleeve[
                            asset
                        ]

                        for asset in assets
                    ],

                    dtype=float,
                )


                relative_matrix = (

                    V7_RETURNS

                    .loc[
                        :
                        signal_date,

                        assets,
                    ]

                    .tail(
                        V7_RELATIVE_RISK_LOOKBACK
                    )

                    .sub(

                        V7_TQQQ_RETURNS

                        .loc[
                            :
                            signal_date
                        ]

                        .tail(
                            V7_RELATIVE_RISK_LOOKBACK
                        ),

                        axis=0,
                    )

                    .fillna(
                        0.0
                    )
                )


                sleeve_relative_returns = (

                    relative_matrix

                    .to_numpy(
                        dtype=float
                    )

                    @

                    weights
                )


                sleeve_relative_variance = float(

                    np.var(

                        sleeve_relative_returns,

                        ddof=1,
                    )
                )


                # ----------------------------------------------------------
                # Growth/Kelly fraction.
                #
                # No fractional-Kelly tuning.
                #
                # No leverage beyond f=1.
                # ----------------------------------------------------------

                if (

                    np.isfinite(
                        sleeve_relative_variance
                    )

                    and

                    sleeve_relative_variance
                    >
                    0

                    and

                    predicted_sleeve_daily_alpha
                    >
                    0
                ):

                    raw_kelly_fraction = (

                        predicted_sleeve_daily_alpha

                        /

                        sleeve_relative_variance
                    )


                else:

                    raw_kelly_fraction = 0.0


    overlay_fraction = float(

        np.clip(

            raw_kelly_fraction,

            0.0,

            1.0,
        )
    )


    # --------------------------------------------------------------------------
    # 15F. PROPOSED TQQQ + ALPHA PORTFOLIO
    # --------------------------------------------------------------------------

    proposed_weights = {}


    if overlay_fraction < 1.0:

        proposed_weights[
            "TQQQ"
        ] = (

            1.0

            -
            overlay_fraction
        )


    for asset, sleeve_weight in (
        alpha_sleeve.items()
    ):

        proposed_weights[
            asset
        ] = (

            overlay_fraction

            *

            sleeve_weight
        )


    # Numerical cleanup.

    proposed_weights = {

        asset:
            float(
                weight
            )

        for asset, weight
        in proposed_weights.items()

        if weight > 1e-10
    }


    total_proposed = sum(
        proposed_weights.values()
    )


    if total_proposed > 0:

        proposed_weights = {

            asset:
                weight
                /
                total_proposed

            for asset, weight
            in proposed_weights.items()
        }


    else:

        proposed_weights = {
            "TQQQ":
                1.0
        }


    # --------------------------------------------------------------------------
    # 15G. TRANSACTION-COST-AWARE OPPORTUNITY-COST TEST
    # --------------------------------------------------------------------------

    pure_tqqq = {
        "TQQQ":
            1.0
    }


    proposed_turnover = v7_turnover(

        V7_PREVIOUS_WEIGHTS,

        proposed_weights,
    )


    tqqq_turnover = v7_turnover(

        V7_PREVIOUS_WEIGHTS,

        pure_tqqq,
    )


    incremental_tca = (

        B40_TCA_RATE

        *

        (
            proposed_turnover
            -
            tqqq_turnover
        )
    )


    expected_incremental_alpha = (

        overlay_fraction

        *

        predicted_sleeve_daily_alpha

        *

        V7_REBALANCE_SESSIONS
    )


    expected_incremental_net = (

        expected_incremental_alpha

        -

        incremental_tca
    )


    if expected_incremental_net > 0:

        target_weights = (
            proposed_weights
        )


        selected_mode = (
            "TQQQ_PLUS_ALPHA"
        )


    else:

        target_weights = (
            pure_tqqq
        )


        overlay_fraction = 0.0


        selected_mode = (
            "TQQQ_ONLY"
        )


    # --------------------------------------------------------------------------
    # 15H. EXECUTION AVAILABILITY
    # --------------------------------------------------------------------------

    execution_open = (

        V7_OPEN

        .reindex(

            index=[
                execution_date
            ],

            columns=
                list(
                    target_weights
                ),
        )

        .iloc[
            0
        ]
    )


    unavailable = [

        asset

        for asset in target_weights

        if (

            not np.isfinite(
                execution_open.get(
                    asset,
                    np.nan
                )
            )

            or

            execution_open.get(
                asset,
                np.nan
            )
            <=
            0
        )
    ]


    if unavailable:

        # Remove unavailable stock allocations and return that capital to TQQQ.

        returned_weight = float(

            sum(

                target_weights.pop(
                    asset
                )

                for asset in unavailable
            )
        )


        target_weights[
            "TQQQ"
        ] = (

            target_weights.get(
                "TQQQ",
                0.0,
            )

            +

            returned_weight
        )


    # --------------------------------------------------------------------------
    # 15I. REALIZED PERIOD RETURN
    # --------------------------------------------------------------------------

    actual_turnover = v7_turnover(

        V7_PREVIOUS_WEIGHTS,

        target_weights,
    )


    transaction_cost = (

        B40_TCA_RATE

        *

        actual_turnover
    )


    realized_returns = (

        b41_realized_asset_returns(

            assets=
                list(
                    target_weights
                ),

            execution_date=
                execution_date,

            exit_date=
                exit_date,

            final_period=
                final_period,
        )
    )


    portfolio_gross_return = float(

        sum(

            weight

            *

            realized_returns[
                asset
            ]

            for asset, weight
            in target_weights.items()
        )
    )


    period_factor = (

        (
            1.0
            -
            transaction_cost
        )

        *

        (
            1.0
            +
            portfolio_gross_return
        )
    )


    period_factor = max(

        period_factor,

        1e-12,
    )


    V7_WEALTH = (

        V7_WEALTH

        *

        period_factor
    )


    # --------------------------------------------------------------------------
    # 15J. DRIFT WEIGHTS
    # --------------------------------------------------------------------------

    V7_PREVIOUS_WEIGHTS = (

        v7_drift_weights(

            target_weights,

            realized_returns,
        )
    )


    # --------------------------------------------------------------------------
    # 15K. LOG PATH
    # --------------------------------------------------------------------------

    V7_PATH_ROWS.append(
        {

            "Period":
                period_no,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Mode":
                selected_mode,

            "Overlay_Fraction":
                overlay_fraction,

            "Alpha_Sleeve_Names":
                len(
                    alpha_sleeve
                ),

            "Predicted_Sleeve_Daily_Alpha":
                predicted_sleeve_daily_alpha,

            "Relative_Variance":
                sleeve_relative_variance,

            "Raw_Kelly":
                raw_kelly_fraction,

            "Expected_Incremental_Net":
                expected_incremental_net,

            "Turnover":
                actual_turnover,

            "TCA_Fraction":
                transaction_cost,

            "Gross_Period_Return":
                portfolio_gross_return,

            "Net_Period_Return":
                period_factor
                -
                1.0,

            "Wealth":
                V7_WEALTH,

            "Held_Names":
                len(
                    target_weights
                ),

            "TQQQ_Weight":
                target_weights.get(
                    "TQQQ",
                    0.0,
                ),

            "Max_Name_Weight":
                max(
                    target_weights.values()
                ),
        }
    )


    for asset, weight in (
        target_weights.items()
    ):

        V7_WEIGHT_ROWS.append(
            {

                "Execution_Date":
                    execution_date,

                "Ticker":
                    asset,

                "Weight":
                    weight,
            }
        )


    if (

        period_no == 1

        or

        period_no % 5 == 0

        or

        period_no
        ==
        len(
            V7_SCHEDULE
        )
    ):

        print(

            f"[V7] "
            f"{period_no:02d}/"
            f"{len(V7_SCHEDULE):02d}"
            f" | {signal_date.date()}"
            f" | mode={selected_mode}"
            f" | f={overlay_fraction:.3f}"
            f" | wealth={V7_WEALTH:.4f}"
        )


# ==============================================================================
# 16. RESULTS
# ==============================================================================

V7_PATH = pd.DataFrame(
    V7_PATH_ROWS
)


V7_WEIGHTS = pd.DataFrame(
    V7_WEIGHT_ROWS
)


if V7_PATH.empty:

    raise RuntimeError(
        "V7 produced zero evaluation observations."
    )


V7_FINAL_WEALTH = float(

    V7_PATH[
        "Wealth"
    ]
    .iloc[
        -1
    ]
)


V7_NET_RETURN_PCT = (

    100.0

    *

    (
        V7_FINAL_WEALTH
        -
        1.0
    )
)


V7_TOTAL_TURNOVER = float(

    V7_PATH[
        "Turnover"
    ]
    .sum()
)


V7_MEAN_OVERLAY = float(

    V7_PATH[
        "Overlay_Fraction"
    ]
    .mean()
)


V7_OVERLAY_ACTIVE_PCT = float(

    100.0

    *

    (
        V7_PATH[
            "Overlay_Fraction"
        ]
        >
        0
    )
    .mean()
)


# ==============================================================================
# 17. MARK-TO-MARK DRAWDOWN
# ==============================================================================

wealth_marks = pd.Series(

    [1.0]

    +

    V7_PATH[
        "Wealth"
    ]
    .tolist()
)


drawdown = (

    wealth_marks

    /

    wealth_marks.cummax()

    -

    1.0
)


V7_MARK_MAX_DD_PCT = (

    100.0

    *

    drawdown.min()
)


# ==============================================================================
# 18. BENCHMARKS
# ==============================================================================

def v7_get_benchmark(
    strategy
):

    temp = (

        BLOCK41_SUMMARY[

            BLOCK41_SUMMARY[
                "Strategy"
            ]
            ==
            strategy
        ]
    )


    if temp.empty:

        return np.nan


    return float(

        temp[
            "Final_Wealth"
        ]
        .iloc[
            0
        ]
    )


V7_BENCHMARKS = {

    "TQQQ_BH_NET_2BPS":

        v7_get_benchmark(
            "TQQQ_BH_NET_2BPS"
        ),

    "QQQ_BH_NET_2BPS":

        v7_get_benchmark(
            "QQQ_BH_NET_2BPS"
        ),

    "PIT_EW_NET_2BPS":

        v7_get_benchmark(
            "PIT_EW_NET_2BPS"
        ),

    "V4_RIDGE":

        v7_get_benchmark(
            "V4_RIDGE"
        ),

    "CASH":

        1.0,
}


V7_STRONGEST_BENCHMARK = max(

    V7_BENCHMARKS,

    key=lambda strategy:
        V7_BENCHMARKS[
            strategy
        ],
)


V7_STRONGEST_BENCHMARK_WEALTH = (

    V7_BENCHMARKS[
        V7_STRONGEST_BENCHMARK
    ]
)


V7_MINUS_STRONGEST_PP = (

    100.0

    *

    (
        V7_FINAL_WEALTH

        -

        V7_STRONGEST_BENCHMARK_WEALTH
    )
)


V7_PASS = (

    V7_FINAL_WEALTH

    >

    V7_STRONGEST_BENCHMARK_WEALTH
)


# ==============================================================================
# 19. FINAL COMPARISON
# ==============================================================================

comparison_rows = [

    {

        "Strategy":
            "V7_MULTI_HORIZON_KELLY",

        "Final_Wealth":
            V7_FINAL_WEALTH,
    }
]


for strategy, wealth in (
    V7_BENCHMARKS.items()
):

    comparison_rows.append(
        {

            "Strategy":
                strategy,

            "Final_Wealth":
                wealth,
        }
    )


V7_COMPARISON = pd.DataFrame(
    comparison_rows
)


V7_COMPARISON[
    "Net_Return_Pct"
] = (

    100.0

    *

    (
        V7_COMPARISON[
            "Final_Wealth"
        ]

        -

        1.0
    )
)


V7_COMPARISON = (

    V7_COMPARISON

    .sort_values(
        "Final_Wealth",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 20. LATEST PORTFOLIO
# ==============================================================================

V7_LATEST_EXECUTION = (

    V7_WEIGHTS[
        "Execution_Date"
    ]
    .max()
)


V7_LATEST_PORTFOLIO = (

    V7_WEIGHTS[

        V7_WEIGHTS[
            "Execution_Date"
        ]
        ==
        V7_LATEST_EXECUTION
    ]

    .copy()
)


V7_LATEST_PORTFOLIO[
    "Weight_Pct"
] = (

    100.0

    *

    V7_LATEST_PORTFOLIO[
        "Weight"
    ]
)


V7_LATEST_PORTFOLIO = (

    V7_LATEST_PORTFOLIO

    .sort_values(
        "Weight",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 21. FINGERPRINT
# ==============================================================================

V7_CONFIG = {

    "parent":
        V4_FINAL_RESEARCH_FINGERPRINT,

    "objective":
        "MAX_NET_COMPOUNDED_WEALTH",

    "forecast_horizons":
        V7_HORIZONS,

    "decision_frequency":
        V7_REBALANCE_SESSIONS,

    "models":
        "4x_SKLEARN_DEFAULT_HIST_GRADIENT_BOOSTING",

    "cross_horizon_aggregation":
        "MEDIAN_DAILYIZED_FORECAST_AND_MEDIAN_RANK",

    "core":
        "TQQQ",

    "allocation":
        "FULL_KELLY_BETWEEN_TQQQ_AND_ALPHA_SLEEVE",

    "relative_variance_window":
        V7_RELATIVE_RISK_LOOKBACK,

    "alpha_sleeve":
        "POSITIVE_CONSENSUS_HALF_SCORE_DIVIDED_BY_RELATIVE_VOL",

    "transaction_cost_gate":
        True,

    "tca_bps":
        B40_TCA_BPS,

    "single_name_cap":
        None,

    "sector_cap":
        None,

    "cash":
        False,
}


V7_FINGERPRINT = hashlib.sha256(

    json.dumps(

        V7_CONFIG,

        sort_keys=True,

        default=str,

    ).encode(
        "utf-8"
    )

).hexdigest()


# ==============================================================================
# 22. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 124
)

print(
    "V7 — FINAL RESULTS"
)

print(
    "=" * 124
)


print(
    "\n1) SAME-CALENDAR NET WEALTH"
)


display(

    V7_COMPARISON

    .round(
        6
    )
)


print(
    "\n2) PORTFOLIO ECONOMICS"
)


V7_ECONOMICS = pd.DataFrame(
    {

        "Metric": [

            "Final wealth",

            "Net return pct",

            "Observed rebalance-mark max DD pct",

            "Total turnover",

            "Portfolio decisions",

            "Mean alpha overlay fraction",

            "Overlay-active periods pct",

            "Mean TQQQ weight pct",

            "Mean held names",

            "Mean max-name weight pct",
        ],


        "Value": [

            V7_FINAL_WEALTH,

            V7_NET_RETURN_PCT,

            V7_MARK_MAX_DD_PCT,

            V7_TOTAL_TURNOVER,

            len(
                V7_PATH
            ),

            V7_MEAN_OVERLAY,

            V7_OVERLAY_ACTIVE_PCT,

            100.0
            *
            V7_PATH[
                "TQQQ_Weight"
            ]
            .mean(),

            V7_PATH[
                "Held_Names"
            ]
            .mean(),

            100.0
            *
            V7_PATH[
                "Max_Name_Weight"
            ]
            .mean(),
        ],
    }
)


display(

    V7_ECONOMICS

    .round(
        6
    )
)


print(
    "\n3) PORTFOLIO MODE USAGE"
)


V7_MODE_USAGE = (

    V7_PATH[
        "Mode"
    ]

    .value_counts()

    .rename_axis(
        "Mode"
    )

    .to_frame(
        "Periods"
    )
)


V7_MODE_USAGE[
    "Pct"
] = (

    100.0

    *

    V7_MODE_USAGE[
        "Periods"
    ]

    /

    len(
        V7_PATH
    )
)


display(

    V7_MODE_USAGE

    .round(
        4
    )
)


print(
    f"\n4) LATEST PORTFOLIO @ "
    f"{V7_LATEST_EXECUTION.date()}"
)


display(

    V7_LATEST_PORTFOLIO

    .head(
        30
    )

    [
        [
            "Ticker",
            "Weight_Pct",
        ]
    ]

    .round(
        4
    )
)


# ==============================================================================
# 23. WEALTH GRAPH
# ==============================================================================

plt.figure(
    figsize=(
        15,
        8,
    )
)


plt.plot(

    V7_PATH[
        "Exit_Date"
    ],

    V7_PATH[
        "Wealth"
    ],

    linewidth=
        2.5,

    label=
        "V7_MULTI_HORIZON_KELLY",
)


if (
    "BLOCK41_WEALTH_CURVES"
    in globals()
):

    for benchmark in [

        "TQQQ_BH_NET_2BPS",
        "QQQ_BH_NET_2BPS",
        "PIT_EW_NET_2BPS",
        "V4_RIDGE",

    ]:

        if benchmark in (
            BLOCK41_WEALTH_CURVES.columns
        ):

            plt.plot(

                BLOCK41_WEALTH_CURVES.index,

                BLOCK41_WEALTH_CURVES[
                    benchmark
                ],

                linewidth=
                    1.4,

                label=
                    benchmark,
            )


plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1,
)


plt.title(
    "V7 — 1M / 3M / 6M / 12M Nonlinear Alpha + TQQQ Core"
)


plt.xlabel(
    "Date"
)


plt.ylabel(
    "Net Wealth"
)


plt.legend()


plt.grid(
    alpha=0.25
)


plt.show()


# ==============================================================================
# 24. FINAL OBJECTIVE VERDICT
# ==============================================================================

print(
    "\n"
    +
    "=" * 124
)

print(
    "V7 — ONE-SHOT OBJECTIVE VERDICT"
)

print(
    "=" * 124
)


print(
    f"\nV7 final wealth        : "
    f"{V7_FINAL_WEALTH:.6f}"
)


print(
    f"V7 net return          : "
    f"{V7_NET_RETURN_PCT:+.2f}%"
)


print(
    f"Strongest benchmark    : "
    f"{V7_STRONGEST_BENCHMARK}"
)


print(
    f"Benchmark final wealth : "
    f"{V7_STRONGEST_BENCHMARK_WEALTH:.6f}"
)


print(
    f"V7 minus strongest     : "
    f"{V7_MINUS_STRONGEST_PP:+.3f} pp"
)


print(
    f"\nDEVELOPMENT BACKCAST PASS: "
    f"{V7_PASS}"
)


if V7_PASS:

    print(
        "\nRESULT:"
    )

    print(
        "V7 PRODUCES POSITIVE NET VALUE ABOVE EVERY PREDECLARED BENCHMARK."
    )

    print(
        "FREEZE V7. NO MORE 2023-2026 TUNING."
    )

    print(
        "NEXT OBSERVATIONS BECOME TRUE FORWARD OOS."
    )


else:

    print(
        "\nRESULT:"
    )

    print(
        "V7 DOES NOT BEAT THE STRONGEST BENCHMARK."
    )

    print(
        "DO NOT RETUNE THESE HORIZONS OR MODEL PARAMETERS ON THIS SAMPLE."
    )


print(
    "\nV7 FINGERPRINT:"
)


print(
    V7_FINGERPRINT
)


print(
    "\n[+] V7 ONE-SHOT COMPLETE."
)

print(
    "=" * 124
)
