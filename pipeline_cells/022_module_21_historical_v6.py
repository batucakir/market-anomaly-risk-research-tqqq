# ==============================================================================
# MODULE 21 / HISTORICAL V6
# TQQQ BENCHMARK-PLUS RELATIVE-ALPHA ENGINE
#
# Historical V6 research logic preserved.
# No parameter / architecture change.
# ==============================================================================

import json
import hashlib
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V6_REQUIRED = [
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


V6_MISSING = [
    x
    for x in V6_REQUIRED
    if x not in globals()
]


if V6_MISSING:
    raise RuntimeError(
        "V6 missing required objects: "
        f"{V6_MISSING}"
    )


print("=" * 120)

print(
    "V6 ONE-SHOT — TQQQ BENCHMARK-PLUS RELATIVE-ALPHA ENGINE"
)

print("=" * 120)


# ==============================================================================
# 1. FROZEN CONFIGURATION
# ==============================================================================

V6_HOLDING_SESSIONS = 21

V6_MIN_TRAIN_EVENTS = 12

V6_MIN_CURRENT_STOCKS = 500


V6_START = pd.Timestamp(
    B41_START_DATE
).normalize()


V6_END = pd.Timestamp(
    B41_END_DATE
).normalize()


print(
    "\nObjective       : MAX NET WEALTH"
)

print(
    "Default asset   : TQQQ"
)

print(
    "Prediction      : 21-session EXCESS RETURN vs TQQQ"
)

print(
    "Rebalance       :",
    V6_HOLDING_SESSIONS,
    "sessions"
)

print(
    "TCA             :",
    f"{B40_TCA_BPS:.2f} bps"
)

print(
    "Cash            : NONE"
)

print(
    "Risk cap        : NONE"
)

print(
    "Name cap        : NONE"
)

print(
    "Sector cap      : NONE"
)

print(
    "\nIMPORTANT: DEVELOPMENT BACKCAST — NOT PROSPECTIVE OOS."
)


# ==============================================================================
# 2. CLEAN PRICE MATRICES
# ==============================================================================

V6_OPEN = (
    B41_OPEN_WIDE
    .copy()
    .sort_index()
)


V6_CLOSE = (
    B41_CLOSE_WIDE
    .copy()
    .sort_index()
)


V6_OPEN.index = pd.DatetimeIndex(
    V6_OPEN.index
).normalize()


V6_CLOSE.index = pd.DatetimeIndex(
    V6_CLOSE.index
).normalize()


V6_OPEN = (
    V6_OPEN
    .groupby(level=0)
    .last()
    .sort_index()
)


V6_CLOSE = (
    V6_CLOSE
    .groupby(level=0)
    .last()
    .sort_index()
)


if "SPY" not in V6_CLOSE.columns:
    raise RuntimeError(
        "SPY missing from V6 prices."
    )


if "TQQQ" not in V6_CLOSE.columns:
    raise RuntimeError(
        "TQQQ missing from V6 prices."
    )


# ==============================================================================
# 3. MARKET CALENDAR
# ==============================================================================

V6_CALENDAR = (
    V6_CLOSE[
        "SPY"
    ]
    .dropna()
    .index
    .sort_values()
)


calendar_values = V6_CALENDAR.to_numpy(
    dtype="datetime64[ns]"
)


calendar_position = {
    pd.Timestamp(date): i
    for i, date in enumerate(
        V6_CALENDAR
    )
}


if V6_START not in calendar_position:
    raise RuntimeError(
        f"V6 start {V6_START.date()} missing from calendar."
    )


if V6_END not in calendar_position:
    raise RuntimeError(
        f"V6 end {V6_END.date()} missing from calendar."
    )


start_pos = calendar_position[
    V6_START
]


end_pos = calendar_position[
    V6_END
]


# ==============================================================================
# 4. CLEAN MODEL PANEL
# ==============================================================================

V6_MODEL_PANEL = (
    B39_MODEL_PANEL
    .copy()
)


V6_MODEL_PANEL[
    "Date"
] = pd.to_datetime(
    V6_MODEL_PANEL[
        "Date"
    ]
).dt.normalize()


if "Feature_Complete" not in (
    V6_MODEL_PANEL.columns
):
    raise RuntimeError(
        "B39_MODEL_PANEL missing Feature_Complete."
    )


V6_MODEL_PANEL = (
    V6_MODEL_PANEL[
        (
            V6_MODEL_PANEL[
                "Feature_Complete"
            ]
        )
        &
        (
            V6_MODEL_PANEL[
                "Asset_Type"
            ]
            ==
            "STOCK"
        )
    ]
    .copy()
)


# ==============================================================================
# 5. EVENT SCHEDULE
# ==============================================================================

feature_dates = (
    V6_MODEL_PANEL[
        "Date"
    ]
    .drop_duplicates()
    .sort_values()
)


first_feature_date = pd.Timestamp(
    feature_dates.min()
)


first_feature_pos = int(
    np.searchsorted(
        calendar_values,
        np.datetime64(
            first_feature_date
        ),
        side="left",
    )
)


# Need 252 sessions for 12-1 momentum.

minimum_execution_pos = max(
    first_feature_pos
    +
    253,
    253,
)


# Align all historical research events to the exact evaluation-start anchor.

execution_positions = [
    start_pos
]


p = (
    start_pos
    -
    V6_HOLDING_SESSIONS
)


while p >= minimum_execution_pos:

    execution_positions.append(
        p
    )

    p -= V6_HOLDING_SESSIONS


p = (
    start_pos
    +
    V6_HOLDING_SESSIONS
)


while p <= end_pos:

    execution_positions.append(
        p
    )

    p += V6_HOLDING_SESSIONS


execution_positions = sorted(
    set(
        execution_positions
    )
)


schedule_rows = []


for pos in execution_positions:

    if pos <= 0:
        continue


    signal_pos = (
        pos - 1
    )


    signal_date = pd.Timestamp(
        V6_CALENDAR[
            signal_pos
        ]
    )


    execution_date = pd.Timestamp(
        V6_CALENDAR[
            pos
        ]
    )


    next_pos = (
        pos
        +
        V6_HOLDING_SESSIONS
    )


    if next_pos <= end_pos:

        exit_date = pd.Timestamp(
            V6_CALENDAR[
                next_pos
            ]
        )

        final_period = False


    else:

        exit_date = (
            V6_END
        )

        final_period = True


    schedule_rows.append(
        {
            "Signal_Pos":
                signal_pos,

            "Signal_Date":
                signal_date,

            "Execution_Pos":
                pos,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Final_Period":
                final_period,
        }
    )


V6_SCHEDULE = pd.DataFrame(
    schedule_rows
)


print(
    "\nHistorical event start:",
    V6_SCHEDULE[
        "Execution_Date"
    ]
    .min()
    .date()
)

print(
    "Evaluation start      :",
    V6_START.date()
)

print(
    "Evaluation end        :",
    V6_END.date()
)


# ==============================================================================
# 6. EXTRA CAUSAL MOMENTUM FEATURES
# ==============================================================================

def v6_add_long_momentum_features(
    frame,
    signal_pos,
):

    if frame.empty:
        return frame


    assets = (
        frame[
            "Ticker"
        ]
        .tolist()
    )


    if signal_pos < 252:
        return pd.DataFrame()


    current_close = (
        V6_CLOSE
        .iloc[
            signal_pos
        ]
        .reindex(
            assets
        )
    )


    close_21 = (
        V6_CLOSE
        .iloc[
            signal_pos
            -
            21
        ]
        .reindex(
            assets
        )
    )


    close_252 = (
        V6_CLOSE
        .iloc[
            signal_pos
            -
            252
        ]
        .reindex(
            assets
        )
    )


    ret_252 = (
        current_close
        /
        close_252
        -
        1.0
    )


    momentum_12_1 = (
        close_21
        /
        close_252
        -
        1.0
    )


    frame = frame.copy()


    frame[
        "V6_Ret252"
    ] = frame[
        "Ticker"
    ].map(
        ret_252
    )


    frame[
        "V6_Mom12_1"
    ] = frame[
        "Ticker"
    ].map(
        momentum_12_1
    )


    frame[
        "XS_V6_Ret252"
    ] = (
        frame[
            "V6_Ret252"
        ]
        .rank(
            pct=True,
            method="average",
        )
    )


    frame[
        "XS_V6_Mom12_1"
    ] = (
        frame[
            "V6_Mom12_1"
        ]
        .rank(
            pct=True,
            method="average",
        )
    )


    return frame


# ==============================================================================
# 7. BUILD ONE EVENT CROSS-SECTION
# ==============================================================================

V6_FEATURES = (
    list(
        B39_MODEL_FEATURES
    )
    +
    [
        "XS_V6_Ret252",
        "XS_V6_Mom12_1",
    ]
)


def v6_event_frame(
    schedule_row,
):

    signal_date = pd.Timestamp(
        schedule_row.Signal_Date
    )


    execution_date = pd.Timestamp(
        schedule_row.Execution_Date
    )


    exit_date = pd.Timestamp(
        schedule_row.Exit_Date
    )


    signal_pos = int(
        schedule_row.Signal_Pos
    )


    current = (
        V6_MODEL_PANEL[
            V6_MODEL_PANEL[
                "Date"
            ]
            ==
            signal_date
        ]
        [
            [
                "Date",
                "Ticker",
            ]
            +
            list(
                B39_MODEL_FEATURES
            )
        ]
        .copy()
    )


    if current.empty:
        return None


    current = v6_add_long_momentum_features(
        current,
        signal_pos,
    )


    if current.empty:
        return None


    current = (
        current
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna(
            subset=
                V6_FEATURES
        )
    )


    if len(
        current
    ) < 100:

        return None


    assets = current[
        "Ticker"
    ].tolist()


    if execution_date not in (
        V6_OPEN.index
    ):
        return None


    entry = (
        V6_OPEN
        .loc[
            execution_date
        ]
        .reindex(
            assets
        )
    )


    # Training target only exists for regular open->open periods.
    # The final incomplete evaluation period is still predictable/tradable
    # but is never used as training data.

    if not bool(
        schedule_row.Final_Period
    ):

        if exit_date not in (
            V6_OPEN.index
        ):

            target = pd.Series(
                np.nan,
                index=
                    assets,
            )

            tqqq_target = np.nan


        else:

            exit_price = (
                V6_OPEN
                .loc[
                    exit_date
                ]
                .reindex(
                    assets
                )
            )


            tqqq_entry = (
                V6_OPEN
                .loc[
                    execution_date,
                    "TQQQ"
                ]
            )


            tqqq_exit = (
                V6_OPEN
                .loc[
                    exit_date,
                    "TQQQ"
                ]
            )


            valid_tqqq = (
                np.isfinite(
                    tqqq_entry
                )
                and
                np.isfinite(
                    tqqq_exit
                )
                and
                tqqq_entry > 0
                and
                tqqq_exit > 0
            )


            if valid_tqqq:

                tqqq_target = (
                    np.log(
                        tqqq_exit
                        /
                        tqqq_entry
                    )
                )


                valid_assets = (
                    np.isfinite(
                        entry
                    )
                    &
                    np.isfinite(
                        exit_price
                    )
                    &
                    (
                        entry > 0
                    )
                    &
                    (
                        exit_price > 0
                    )
                )


                target = pd.Series(
                    np.nan,
                    index=
                        assets,
                )


                target.loc[
                    valid_assets
                ] = (
                    np.log(
                        exit_price.loc[
                            valid_assets
                        ]
                        /
                        entry.loc[
                            valid_assets
                        ]
                    )
                    -
                    tqqq_target
                )


            else:

                target = pd.Series(
                    np.nan,
                    index=
                        assets,
                )


    else:

        target = pd.Series(
            np.nan,
            index=
                assets,
        )


    current[
        "Target_Excess_Log"
    ] = (
        current[
            "Ticker"
        ]
        .map(
            target
        )
    )


    current[
        "Signal_Date"
    ] = signal_date


    current[
        "Execution_Date"
    ] = execution_date


    current[
        "Exit_Date"
    ] = exit_date


    return current


# ==============================================================================
# 8. PRECOMPUTE EVENT DATA
# ==============================================================================

print(
    "\n[V6] Building causal monthly event panel..."
)


V6_EVENT_FRAMES = {}


for row in V6_SCHEDULE.itertuples(
    index=False
):

    frame = v6_event_frame(
        row
    )


    if frame is not None:

        V6_EVENT_FRAMES[
            pd.Timestamp(
                row.Execution_Date
            )
        ] = frame


print(
    "[V6] Event frames:",
    len(
        V6_EVENT_FRAMES
    )
)


# ==============================================================================
# 9. MODEL FACTORY
# ==============================================================================

def v6_model():

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


# ==============================================================================
# 10. WALK-FORWARD RELATIVE-ALPHA PORTFOLIO
# ==============================================================================

V6_WEALTH = 1.0

V6_HELD_ASSET = None

V6_PATH_ROWS = []

V6_PREDICTION_ROWS = []


evaluation_schedule = (
    V6_SCHEDULE[
        V6_SCHEDULE[
            "Execution_Date"
        ]
        >=
        V6_START
    ]
    .copy()
)


print(
    "\n[V6] Starting benchmark-plus walk-forward..."
)


for period_no, row in enumerate(
    evaluation_schedule.itertuples(
        index=False
    ),
    start=1,
):

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


    current = (
        V6_EVENT_FRAMES.get(
            execution_date
        )
    )


    if current is None:

        raise RuntimeError(
            "Missing V6 prediction event at "
            f"{execution_date.date()}."
        )


    # --------------------------------------------------------------------------
    # STRICT TRAINING SET
    #
    # Only events whose target exit had already occurred by SIGNAL CLOSE.
    # --------------------------------------------------------------------------

    train_parts = []

    train_event_count = 0


    for historical_execution, historical_frame in (
        V6_EVENT_FRAMES.items()
    ):

        if historical_execution >= execution_date:
            continue


        historical_exit = pd.Timestamp(
            historical_frame[
                "Exit_Date"
            ]
            .iloc[
                0
            ]
        )


        if historical_exit > signal_date:
            continue


        resolved = (
            historical_frame
            .dropna(
                subset=
                    V6_FEATURES
                    +
                    [
                        "Target_Excess_Log"
                    ]
            )
        )


        if resolved.empty:
            continue


        train_parts.append(
            resolved
        )

        train_event_count += 1


    if train_event_count < V6_MIN_TRAIN_EVENTS:

        raise RuntimeError(
            "Insufficient resolved training history "
            f"at {signal_date.date()}: "
            f"{train_event_count} events."
        )


    train = pd.concat(
        train_parts,
        ignore_index=True,
    )


    X_train = (
        train[
            V6_FEATURES
        ]
        .to_numpy(
            dtype=float
        )
    )


    # Fit in bps of log excess return.

    y_train = (
        train[
            "Target_Excess_Log"
        ]
        .to_numpy(
            dtype=float
        )
        *
        10000.0
    )


    valid_train = (
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
        valid_train
    ]


    y_train = y_train[
        valid_train
    ]


    if len(
        y_train
    ) < 5000:

        raise RuntimeError(
            "Too few V6 training rows at "
            f"{signal_date.date()}: "
            f"{len(y_train):,}"
        )


    model = v6_model()


    with warnings.catch_warnings():

        warnings.simplefilter(
            "ignore"
        )


        model.fit(
            X_train,
            y_train,
        )


    # --------------------------------------------------------------------------
    # CURRENT PREDICTIONS
    # --------------------------------------------------------------------------

    prediction_section = (
        current
        .dropna(
            subset=
                V6_FEATURES
        )
        .copy()
    )


    if len(
        prediction_section
    ) < V6_MIN_CURRENT_STOCKS:

        raise RuntimeError(
            "V6 current cross-section too small "
            f"at {signal_date.date()}: "
            f"{len(prediction_section)}"
        )


    X_current = (
        prediction_section[
            V6_FEATURES
        ]
        .to_numpy(
            dtype=float
        )
    )


    prediction_section[
        "Predicted_Excess_Log"
    ] = (
        model.predict(
            X_current
        )
        /
        10000.0
    )


    # --------------------------------------------------------------------------
    # TQQQ is the explicit zero-excess benchmark.
    # --------------------------------------------------------------------------

    candidate_mu = {
        ticker:
            float(mu)
        for ticker, mu in zip(
            prediction_section[
                "Ticker"
            ],
            prediction_section[
                "Predicted_Excess_Log"
            ],
        )
        if np.isfinite(
            mu
        )
    }


    candidate_mu[
        "TQQQ"
    ] = 0.0


    # --------------------------------------------------------------------------
    # Execution-open availability.
    # --------------------------------------------------------------------------

    execution_prices = (
        V6_OPEN
        .reindex(
            index=[
                execution_date
            ],
            columns=
                list(
                    candidate_mu.keys()
                ),
        )
        .iloc[
            0
        ]
    )


    valid_candidates = {
        ticker:
            mu
        for ticker, mu
        in candidate_mu.items()
        if (
            np.isfinite(
                execution_prices.get(
                    ticker,
                    np.nan
                )
            )
            and
            execution_prices.get(
                ticker,
                np.nan
            )
            >
            0
        )
    }


    if "TQQQ" not in valid_candidates:

        raise RuntimeError(
            f"TQQQ unavailable on "
            f"{execution_date.date()}."
        )


    # --------------------------------------------------------------------------
    # EXACT MAX-NET RELATIVE-RETURN DECISION
    #
    # Keeping current asset:
    #     no transaction cost.
    #
    # Switching from one fully invested asset to another:
    #     sell 100% + buy 100% => turnover = 2.
    #
    # Initial allocation from cash:
    #     turnover = 1 for every candidate, so it does not affect ranking.
    # --------------------------------------------------------------------------

    objective = {}


    for ticker, mu in (
        valid_candidates.items()
    ):

        if V6_HELD_ASSET is None:

            switching_penalty = (
                B40_TCA_RATE
            )


        elif ticker == V6_HELD_ASSET:

            switching_penalty = 0.0


        else:

            switching_penalty = (
                2.0
                *
                B40_TCA_RATE
            )


        objective[
            ticker
        ] = (
            mu
            -
            switching_penalty
        )


    chosen_asset = max(
        objective,
        key=
            objective.get
    )


    chosen_mu = (
        valid_candidates[
            chosen_asset
        ]
    )


    chosen_objective = (
        objective[
            chosen_asset
        ]
    )


    # --------------------------------------------------------------------------
    # ACTUAL TURNOVER
    # --------------------------------------------------------------------------

    if V6_HELD_ASSET is None:

        turnover = 1.0


    elif chosen_asset == V6_HELD_ASSET:

        turnover = 0.0


    else:

        turnover = 2.0


    cost_fraction = (
        B40_TCA_RATE
        *
        turnover
    )


    # --------------------------------------------------------------------------
    # ACTUAL REALIZED RETURN
    # --------------------------------------------------------------------------

    realized = (
        b41_realized_asset_returns(
            assets=[
                chosen_asset
            ],
            execution_date=
                execution_date,
            exit_date=
                exit_date,
            final_period=
                final_period,
        )
    )


    realized_return = float(
        realized[
            chosen_asset
        ]
    )


    period_factor = (
        (
            1.0
            -
            cost_fraction
        )
        *
        (
            1.0
            +
            realized_return
        )
    )


    period_factor = max(
        period_factor,
        1e-12,
    )


    V6_WEALTH = (
        V6_WEALTH
        *
        period_factor
    )


    previous_asset = (
        V6_HELD_ASSET
    )


    V6_HELD_ASSET = (
        chosen_asset
    )


    # --------------------------------------------------------------------------
    # FORENSICS
    # --------------------------------------------------------------------------

    best_stock_row = (
        prediction_section
        .sort_values(
            "Predicted_Excess_Log",
            ascending=False,
        )
        .iloc[
            0
        ]
    )


    V6_PATH_ROWS.append(
        {
            "Period":
                period_no,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Previous_Asset":
                previous_asset,

            "Chosen_Asset":
                chosen_asset,

            "Chosen_Predicted_Excess":
                chosen_mu,

            "Chosen_Objective_After_TCA":
                chosen_objective,

            "Realized_Return":
                realized_return,

            "Turnover":
                turnover,

            "Cost_Fraction":
                cost_fraction,

            "Period_Net_Return":
                period_factor
                -
                1.0,

            "Wealth":
                V6_WEALTH,

            "Training_Events":
                train_event_count,

            "Training_Rows":
                len(
                    y_train
                ),

            "Current_Stocks":
                len(
                    prediction_section
                ),

            "Best_Predicted_Stock":
                best_stock_row[
                    "Ticker"
                ],

            "Best_Stock_Excess":
                best_stock_row[
                    "Predicted_Excess_Log"
                ],
        }
    )


    # Store top predictions for audit.

    top_predictions = (
        prediction_section
        .sort_values(
            "Predicted_Excess_Log",
            ascending=False,
        )
        .head(
            10
        )
    )


    for rank_no, pred_row in enumerate(
        top_predictions.itertuples(
            index=False
        ),
        start=1,
    ):

        V6_PREDICTION_ROWS.append(
            {
                "Signal_Date":
                    signal_date,

                "Rank":
                    rank_no,

                "Ticker":
                    pred_row.Ticker,

                "Predicted_Excess_Log":
                    pred_row.Predicted_Excess_Log,
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
            evaluation_schedule
        )
    ):

        print(
            f"[V6] "
            f"{period_no:02d}/"
            f"{len(evaluation_schedule):02d} "
            f"| {signal_date.date()} "
            f"| asset={chosen_asset:<6} "
            f"| wealth={V6_WEALTH:.4f}"
        )


# ==============================================================================
# 11. RESULTS
# ==============================================================================

V6_PATH = pd.DataFrame(
    V6_PATH_ROWS
)


V6_TOP_PREDICTIONS = pd.DataFrame(
    V6_PREDICTION_ROWS
)


if V6_PATH.empty:

    raise RuntimeError(
        "V6 produced zero evaluation periods."
    )


V6_FINAL_WEALTH = float(
    V6_PATH[
        "Wealth"
    ]
    .iloc[
        -1
    ]
)


V6_NET_RETURN_PCT = (
    100.0
    *
    (
        V6_FINAL_WEALTH
        -
        1.0
    )
)


V6_TOTAL_TURNOVER = float(
    V6_PATH[
        "Turnover"
    ]
    .sum()
)


# ==============================================================================
# 12. DRAWDOWN AT PORTFOLIO MARKS
# ==============================================================================

v6_mark_wealth = pd.Series(
    [
        1.0
    ]
    +
    V6_PATH[
        "Wealth"
    ]
    .tolist()
)


V6_MARK_DD = (
    v6_mark_wealth
    /
    v6_mark_wealth.cummax()
    -
    1.0
)


V6_OBSERVED_MAX_DD_PCT = (
    100.0
    *
    V6_MARK_DD.min()
)


# ==============================================================================
# 13. BENCHMARKS
# ==============================================================================

def v6_benchmark(
    name
):

    row = (
        BLOCK41_SUMMARY[
            BLOCK41_SUMMARY[
                "Strategy"
            ]
            ==
            name
        ]
    )


    if row.empty:

        return np.nan


    return float(
        row[
            "Final_Wealth"
        ]
        .iloc[
            0
        ]
    )


V6_BENCHMARKS = {

    "TQQQ_BH_NET_2BPS":
        v6_benchmark(
            "TQQQ_BH_NET_2BPS"
        ),

    "QQQ_BH_NET_2BPS":
        v6_benchmark(
            "QQQ_BH_NET_2BPS"
        ),

    "PIT_EW_NET_2BPS":
        v6_benchmark(
            "PIT_EW_NET_2BPS"
        ),

    "V4_RIDGE":
        v6_benchmark(
            "V4_RIDGE"
        ),

    "CASH":
        1.0,
}


V6_STRONGEST_BENCHMARK = max(
    V6_BENCHMARKS,
    key=lambda x:
        V6_BENCHMARKS[
            x
        ],
)


V6_STRONGEST_BENCHMARK_WEALTH = (
    V6_BENCHMARKS[
        V6_STRONGEST_BENCHMARK
    ]
)


V6_MINUS_STRONGEST_PP = (
    100.0
    *
    (
        V6_FINAL_WEALTH
        -
        V6_STRONGEST_BENCHMARK_WEALTH
    )
)


V6_PASS = (
    V6_FINAL_WEALTH
    >
    V6_STRONGEST_BENCHMARK_WEALTH
)


# ==============================================================================
# 14. COMPARISON TABLE
# ==============================================================================

comparison_rows = [
    {
        "Strategy":
            "V6_RELATIVE_ALPHA",

        "Final_Wealth":
            V6_FINAL_WEALTH,
    }
]


for name, wealth in (
    V6_BENCHMARKS.items()
):

    comparison_rows.append(
        {
            "Strategy":
                name,

            "Final_Wealth":
                wealth,
        }
    )


V6_COMPARISON = pd.DataFrame(
    comparison_rows
)


V6_COMPARISON[
    "Net_Return_Pct"
] = (
    100.0
    *
    (
        V6_COMPARISON[
            "Final_Wealth"
        ]
        -
        1.0
    )
)


V6_COMPARISON = (
    V6_COMPARISON
    .sort_values(
        "Final_Wealth",
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 15. ASSET-USAGE TABLE
# ==============================================================================

V6_ASSET_USAGE = (
    V6_PATH[
        "Chosen_Asset"
    ]
    .value_counts()
    .rename_axis(
        "Ticker"
    )
    .to_frame(
        "Periods"
    )
)


V6_ASSET_USAGE[
    "Pct"
] = (
    100.0
    *
    V6_ASSET_USAGE[
        "Periods"
    ]
    /
    len(
        V6_PATH
    )
)


# ==============================================================================
# 16. LATEST DECISION
# ==============================================================================

V6_LATEST = (
    V6_PATH
    .tail(
        1
    )
    [
        [
            "Signal_Date",
            "Execution_Date",
            "Chosen_Asset",
            "Chosen_Predicted_Excess",
            "Best_Predicted_Stock",
            "Best_Stock_Excess",
            "Wealth",
        ]
    ]
)


# ==============================================================================
# 17. FINGERPRINT
# ==============================================================================

V6_CONFIG = {

    "parent":
        V4_FINAL_RESEARCH_FINGERPRINT,

    "objective":
        "MAX_NET_WEALTH_RELATIVE_TO_TQQQ",

    "target":
        "21_SESSION_STOCK_LOG_RETURN_MINUS_TQQQ_LOG_RETURN",

    "holding_sessions":
        V6_HOLDING_SESSIONS,

    "model":
        "RIDGE_DEFAULT",

    "training":
        "EXPANDING_STRICT_WALK_FORWARD",

    "minimum_training_events":
        V6_MIN_TRAIN_EVENTS,

    "features":
        V6_FEATURES,

    "default_asset":
        "TQQQ",

    "cash":
        False,

    "risk_cap":
        None,

    "single_name_cap":
        None,

    "sector_cap":
        None,

    "tca_bps":
        B40_TCA_BPS,
}


V6_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V6_CONFIG,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 18. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 120
)

print(
    "V6 — FINAL RESULTS"
)

print(
    "=" * 120
)


print(
    "\n1) SAME-CALENDAR NET WEALTH"
)


display(
    V6_COMPARISON
    .round(
        6
    )
)


print(
    "\n2) ASSET USAGE"
)


display(
    V6_ASSET_USAGE
    .round(
        4
    )
)


print(
    "\n3) LATEST DECISION"
)


display(
    V6_LATEST
    .round(
        6
    )
)


print(
    "\n4) ECONOMICS"
)


V6_ECONOMICS = pd.DataFrame(
    {
        "Metric": [
            "Final wealth",
            "Net return pct",
            "Observed rebalance-mark max DD pct",
            "Total turnover",
            "Rebalances",
            "Number of distinct held assets",
        ],

        "Value": [
            V6_FINAL_WEALTH,
            V6_NET_RETURN_PCT,
            V6_OBSERVED_MAX_DD_PCT,
            V6_TOTAL_TURNOVER,
            len(
                V6_PATH
            ),
            V6_PATH[
                "Chosen_Asset"
            ]
            .nunique(),
        ],
    }
)


display(
    V6_ECONOMICS
    .round(
        6
    )
)


# ==============================================================================
# 19. WEALTH GRAPH
# ==============================================================================

plt.figure(
    figsize=(
        15,
        8,
    )
)


plt.plot(
    V6_PATH[
        "Exit_Date"
    ],
    V6_PATH[
        "Wealth"
    ],
    linewidth=
        2.5,
    label=
        "V6_RELATIVE_ALPHA",
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
    "V6 — TQQQ Benchmark-Plus Relative Alpha"
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
# 20. ONE-SHOT OBJECTIVE VERDICT
# ==============================================================================

print(
    "\n"
    +
    "=" * 120
)

print(
    "V6 — ONE-SHOT OBJECTIVE VERDICT"
)

print(
    "=" * 120
)


print(
    f"\nV6 final wealth        : "
    f"{V6_FINAL_WEALTH:.6f}"
)


print(
    f"V6 net return          : "
    f"{V6_NET_RETURN_PCT:+.2f}%"
)


print(
    f"Strongest benchmark    : "
    f"{V6_STRONGEST_BENCHMARK}"
)


print(
    f"Benchmark final wealth : "
    f"{V6_STRONGEST_BENCHMARK_WEALTH:.6f}"
)


print(
    f"V6 minus strongest     : "
    f"{V6_MINUS_STRONGEST_PP:+.3f} pp"
)


print(
    f"\nDEVELOPMENT BACKCAST PASS: "
    f"{V6_PASS}"
)


if V6_PASS:

    print(
        "\nRESULT:"
    )

    print(
        "V6 ADDS POSITIVE NET ALPHA ABOVE TQQQ."
    )

    print(
        "FREEZE V6 NOW."
    )

    print(
        "DO NOT RETUNE 2023-2026."
    )

    print(
        "NEXT NEW DATA BECOMES TRUE FORWARD OOS."
    )


else:

    print(
        "\nRESULT:"
    )

    print(
        "V6 DOES NOT ADD NET ALPHA ABOVE TQQQ."
    )

    print(
        "DO NOT PARAMETER-MINE THIS HISTORY."
    )


print(
    "\nV6 FINGERPRINT:"
)


print(
    V6_FINGERPRINT
)


print(
    "\n[+] V6 ONE-SHOT COMPLETE."
)

print(
    "=" * 120
)
