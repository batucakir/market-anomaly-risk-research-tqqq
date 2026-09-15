# ==============================================================================
# MODULE 20 / HISTORICAL V5
# ==============================================================================
# V5 FINAL — DIRECT-WEALTH CORE + RESIDUAL-MOMENTUM ENGINE
# ONE-SHOT DEVELOPMENT BACKCAST + FINAL BENCHMARK
# ==============================================================================
#
# OBJECTIVE
# ---------
# Maximize NET portfolio wealth directly.
#
#
# STRUCTURAL CHANGE VS V4
# -----------------------
#
# V4:
#     predict stock absolute return
#     -> large cross-sectional optimizer
#
# V5:
#     build economically distinct causal return sleeves
#     -> let prior NET sleeve wealth decide which sleeve leads
#
#
# PREDECLARED SLEEVES
# -------------------
#
# 1. TQQQ
# 2. QQQ
# 3. TQQQ_TSMOM
#       hold TQQQ iff trailing 252-session QQQ return > 0
#       otherwise CASH
#
# 4. RESIDUAL_MOMENTUM
#       trailing 12-1 month stock residual momentum vs SPY
#       standardized by residual volatility
#       no top-K
#       no name cap
#       positive half of cross-sectional ranks receives smooth rank weights
#
# 5. PIT_EW_STOCKS
#       broad causal stock-market exposure
#
# 6. CASH
#
#
# META RULE
# ---------
# Follow-the-Leader:
#
# At every rebalance:
#
#       choose the sleeve with the highest CAUSALLY accumulated
#       standalone NET wealth up to the PREVIOUS period.
#
# Each sleeve pays its own 2-bps turnover costs in its virtual record.
#
# Therefore the selector never sees current/future period returns.
#
#
# REBALANCE
# ---------
# 21 trading sessions.
#
# This is structurally matched to medium-horizon momentum;
# it is NOT selected from V4 results.
#
#
# IMPORTANT
# ---------
# This is a DEVELOPMENT BACKCAST, not new prospective OOS,
# because V5 architecture was defined after V4 results were observed.
#
# No further tuning is allowed from this backcast.
#
# ==============================================================================


import json
import hashlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display


# ==============================================================================
# 0. REQUIRED STATE
# ==============================================================================

V5_REQUIRED = [

    "B41_OPEN_WIDE",
    "B41_CLOSE_WIDE",
    "B41_DAILY_PANEL",

    "B41_START_DATE",
    "B41_END_DATE",

    "B40_TCA_RATE",
    "B40_TCA_BPS",

    "BLOCK41_SUMMARY",

    "b41_realized_asset_returns",

    "V4_FINAL_RESEARCH_FINGERPRINT",
]


V5_MISSING = [

    x
    for x in V5_REQUIRED
    if x not in globals()
]


if V5_MISSING:

    raise RuntimeError(

        "V5 missing required objects: "

        f"{V5_MISSING}"
    )


print("=" * 120)

print(
    "V5 FINAL — DIRECT-WEALTH CORE + RESIDUAL-MOMENTUM ENGINE"
)

print("=" * 120)


# ==============================================================================
# 1. FROZEN V5 ARCHITECTURE
# ==============================================================================

V5_REBALANCE_SESSIONS = 21

V5_TSMOM_LOOKBACK = 252

V5_RESMOM_TOTAL_LOOKBACK = 252

V5_RESMOM_SKIP_RECENT = 21

V5_RESMOM_MIN_OBS = 126


V5_EXPERTS = [

    "TQQQ",

    "QQQ",

    "TQQQ_TSMOM",

    "RESIDUAL_MOMENTUM",

    "PIT_EW_STOCKS",

    "CASH",
]


print(
    "\nRebalance       :",
    V5_REBALANCE_SESSIONS,
    "sessions"
)

print(
    "TSMOM horizon    :",
    V5_TSMOM_LOOKBACK,
    "sessions"
)

print(
    "Residual momentum:",
    "12-1 months"
)

print(
    "Transaction cost :",
    f"{B40_TCA_BPS:.2f} bps"
)

print(
    "Meta selector     : CAUSAL FOLLOW-THE-LEADER"
)

print(
    "Single-name cap   : NONE"
)

print(
    "Sector cap        : NONE"
)

print(
    "\nIMPORTANT: DEVELOPMENT BACKCAST — NOT PROSPECTIVE OOS."
)


# ==============================================================================
# 2. CANONICAL MARKET DATA
# ==============================================================================

V5_OPEN = (

    B41_OPEN_WIDE
    .copy()
    .sort_index()
)


V5_CLOSE = (

    B41_CLOSE_WIDE
    .copy()
    .sort_index()
)


V5_RET = (

    V5_CLOSE
    .pct_change(
        fill_method=None
    )
)


V5_PANEL = (

    B41_DAILY_PANEL
    .copy()
)


V5_PANEL["Date"] = pd.to_datetime(
    V5_PANEL["Date"]
)


V5_START = pd.Timestamp(
    B41_START_DATE
)


V5_END = pd.Timestamp(
    B41_END_DATE
)


# ==============================================================================
# 3. MARKET CALENDAR
# ==============================================================================

if "SPY" not in V5_CLOSE.columns:

    raise RuntimeError(
        "SPY missing from V5 close matrix."
    )


if "QQQ" not in V5_CLOSE.columns:

    raise RuntimeError(
        "QQQ missing from V5 close matrix."
    )


if "TQQQ" not in V5_CLOSE.columns:

    raise RuntimeError(
        "TQQQ missing from V5 close matrix."
    )


V5_CALENDAR = (

    V5_CLOSE[
        "SPY"
    ]

    .dropna()
    .index
    .sort_values()
)


if V5_START not in V5_CALENDAR:

    raise RuntimeError(
        f"V5 start {V5_START.date()} missing from market calendar."
    )


eval_pos = int(

    V5_CALENDAR.get_loc(
        V5_START
    )
)


end_pos = int(

    V5_CALENDAR.get_loc(
        V5_END
    )
)


# Earliest point where 252-session momentum has enough history.

pit_dates = (

    V5_PANEL[
        "Date"
    ]

    .drop_duplicates()
    .sort_values()
)


first_pit_date = pd.Timestamp(
    pit_dates.min()
)


pit_pos = int(

    np.searchsorted(

        V5_CALENDAR.values,

        np.datetime64(
            first_pit_date
        ),

        side="left",
    )
)


minimum_history_pos = (

    pit_pos

    +

    V5_RESMOM_TOTAL_LOOKBACK

    +

    1
)


# ==============================================================================
# 4. MONTHLY-ALIGNED PREHISTORY + EVALUATION SCHEDULE
# ==============================================================================

# Work backward from the exact Block-41 start so the evaluation still begins
# on precisely the same date as QQQ/TQQQ/V4 benchmarks.

execution_positions = [
    eval_pos
]


p = (

    eval_pos

    -

    V5_REBALANCE_SESSIONS
)


while p >= minimum_history_pos:

    execution_positions.append(
        p
    )

    p -= V5_REBALANCE_SESSIONS


p = (

    eval_pos

    +

    V5_REBALANCE_SESSIONS
)


while p <= end_pos:

    execution_positions.append(
        p
    )

    p += V5_REBALANCE_SESSIONS


execution_positions = sorted(
    set(
        execution_positions
    )
)


V5_SCHEDULE_ROWS = []


for i, pos in enumerate(
    execution_positions
):

    if pos <= 0:
        continue


    execution_date = pd.Timestamp(
        V5_CALENDAR[pos]
    )


    signal_date = pd.Timestamp(

        V5_CALENDAR[
            pos - 1
        ]
    )


    if i + 1 < len(
        execution_positions
    ):

        next_execution = pd.Timestamp(

            V5_CALENDAR[
                execution_positions[
                    i + 1
                ]
            ]
        )


        exit_date = (
            next_execution
        )


        final_period = False


    else:

        exit_date = (
            V5_END
        )


        final_period = True


    V5_SCHEDULE_ROWS.append(
        {

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Final_Period":
                final_period,
        }
    )


V5_SCHEDULE = pd.DataFrame(
    V5_SCHEDULE_ROWS
)


print(
    "\nPrehistory begins :",
    V5_SCHEDULE[
        "Execution_Date"
    ]
    .min()
    .date()
)

print(
    "Evaluation begins :",
    V5_START.date()
)

print(
    "Evaluation ends   :",
    V5_END.date()
)


# ==============================================================================
# 5. ELIGIBLE STOCKS
# ==============================================================================

def v5_eligible_stocks(
    signal_date
):

    section = (

        V5_PANEL[

            (
                V5_PANEL[
                    "Date"
                ]
                ==
                signal_date
            )

            &

            (
                V5_PANEL[
                    "Eligible"
                ]
            )

            &

            (
                V5_PANEL[
                    "Asset_Type"
                ]
                ==
                "STOCK"
            )
        ]
    )


    assets = [

        ticker

        for ticker in (

            section[
                "Ticker"
            ]
            .dropna()
            .drop_duplicates()
            .tolist()
        )

        if ticker in V5_CLOSE.columns
    ]


    return assets


# ==============================================================================
# 6. NORMALIZE WEIGHTS
# ==============================================================================

def v5_normalize(
    raw
):

    clean = {

        asset:
            max(
                float(weight),
                0.0
            )

        for asset, weight in raw.items()

        if (
            np.isfinite(
                weight
            )

            and

            weight > 0
        )
    }


    total = sum(
        clean.values()
    )


    if total <= 0:

        return {}


    return {

        asset:
            weight / total

        for asset, weight in clean.items()
    }


# ==============================================================================
# 7. EXECUTION-PRICE FILTER
# ==============================================================================

def v5_make_tradable(

    weights,

    execution_date,
):

    if not weights:

        return {}


    assets = list(
        weights.keys()
    )


    entry = (

        V5_OPEN
        .reindex(

            index=[
                execution_date
            ],

            columns=
                assets,
        )

        .iloc[
            0
        ]
    )


    valid = [

        asset

        for asset in assets

        if (

            np.isfinite(
                entry.get(
                    asset,
                    np.nan
                )
            )

            and

            entry.get(
                asset,
                np.nan
            )
            >
            0
        )
    ]


    if not valid:

        return {}


    risky_target = min(

        1.0,

        sum(
            weights.values()
        )
    )


    kept = {

        asset:
            weights[
                asset
            ]

        for asset in valid
    }


    kept_sum = sum(
        kept.values()
    )


    if kept_sum <= 0:

        return {}


    return {

        asset:

            value

            /

            kept_sum

            *

            risky_target

        for asset, value in kept.items()
    }


# ==============================================================================
# 8. TQQQ TIME-SERIES MOMENTUM SLEEVE
# ==============================================================================

def v5_tqqq_tsmom(
    signal_date
):

    history = (

        V5_CLOSE[
            "QQQ"
        ]

        .loc[
            :
            signal_date
        ]

        .dropna()

        .tail(
            V5_TSMOM_LOOKBACK
            +
            1
        )
    )


    if len(
        history
    ) < (

        V5_TSMOM_LOOKBACK
        +
        1
    ):

        return {}


    trailing_return = (

        history.iloc[
            -1
        ]

        /

        history.iloc[
            0
        ]

        -

        1.0
    )


    if trailing_return > 0:

        return {
            "TQQQ":
                1.0
        }


    return {}


# ==============================================================================
# 9. RESIDUAL MOMENTUM SLEEVE
# ==============================================================================

def v5_residual_momentum(
    signal_date
):

    assets = (

        v5_eligible_stocks(
            signal_date
        )
    )


    if len(
        assets
    ) < 50:

        return {}


    required_columns = (

        assets

        +

        [
            "SPY"
        ]
    )


    history = (

        V5_RET
        .loc[
            :
            signal_date,

            required_columns,
        ]

        .tail(
            V5_RESMOM_TOTAL_LOOKBACK
        )
    )


    if len(
        history
    ) < V5_RESMOM_MIN_OBS:

        return {}


    # 12-1 momentum:
    #
    # do not use the latest month.

    formation = (

        history

        .iloc[
            :
            -
            V5_RESMOM_SKIP_RECENT
        ]

        .copy()
    )


    market = (

        formation[
            "SPY"
        ]
    )


    scores = {}


    for asset in assets:

        y = formation[
            asset
        ]


        valid = (

            y.notna()

            &

            market.notna()
        )


        n = int(
            valid.sum()
        )


        if n < V5_RESMOM_MIN_OBS:

            continue


        yy = (

            y.loc[
                valid
            ]

            .to_numpy(
                dtype=float
            )
        )


        mm = (

            market.loc[
                valid
            ]

            .to_numpy(
                dtype=float
            )
        )


        m_var = np.var(
            mm
        )


        if (

            not np.isfinite(
                m_var
            )

            or

            m_var <= 1e-12
        ):

            continue


        beta = (

            np.cov(
                yy,
                mm,
                ddof=0,
            )[
                0,
                1
            ]

            /

            m_var
        )


        alpha = (

            np.mean(
                yy
            )

            -

            beta

            *

            np.mean(
                mm
            )
        )


        residual = (

            yy

            -

            alpha

            -

            beta

            *

            mm
        )


        residual_vol = np.std(
            residual,
            ddof=1
        )


        if (

            not np.isfinite(
                residual_vol
            )

            or

            residual_vol <= 1e-8
        ):

            continue


        # Standardized cumulative residual momentum.

        score = (

            np.sum(
                residual
            )

            /

            residual_vol
        )


        if np.isfinite(
            score
        ):

            scores[
                asset
            ] = float(
                score
            )


    if len(
        scores
    ) < 50:

        return {}


    score_series = pd.Series(
        scores
    )


    ranks = (

        score_series

        .rank(
            pct=True,
            method="average",
        )
    )


    # No arbitrary Top-K.
    #
    # Smooth positive-half ranking:
    #
    # percentile 50% -> weight signal 0
    # percentile 100% -> weight signal 0.5

    raw_weight = (

        ranks

        -

        0.50

    ).clip(
        lower=0.0
    )


    raw_weight = raw_weight[
        raw_weight > 0
    ]


    return v5_normalize(

        raw_weight
        .to_dict()
    )


# ==============================================================================
# 10. PIT BROAD STOCK SLEEVE
# ==============================================================================

def v5_pit_ew(
    signal_date
):

    assets = (

        v5_eligible_stocks(
            signal_date
        )
    )


    if not assets:

        return {}


    weight = (

        1.0

        /

        len(
            assets
        )
    )


    return {

        asset:
            weight

        for asset in assets
    }


# ==============================================================================
# 11. ALL EXPERT TARGETS
# ==============================================================================

def v5_build_targets(

    signal_date,

    execution_date,
):

    raw = {

        "TQQQ":

            {
                "TQQQ":
                    1.0
            },


        "QQQ":

            {
                "QQQ":
                    1.0
            },


        "TQQQ_TSMOM":

            v5_tqqq_tsmom(
                signal_date
            ),


        "RESIDUAL_MOMENTUM":

            v5_residual_momentum(
                signal_date
            ),


        "PIT_EW_STOCKS":

            v5_pit_ew(
                signal_date
            ),


        "CASH":

            {},
    }


    return {

        name:

            v5_make_tradable(

                weights,

                execution_date,
            )

        for name, weights in raw.items()
    }


# ==============================================================================
# 12. PORTFOLIO ADVANCE
# ==============================================================================

def v5_advance(

    wealth,

    previous_weights,

    target_weights,

    realized_returns,
):

    union_assets = (

        set(
            previous_weights
        )

        |

        set(
            target_weights
        )
    )


    turnover = float(

        sum(

            abs(

                target_weights.get(
                    asset,
                    0.0
                )

                -

                previous_weights.get(
                    asset,
                    0.0
                )
            )

            for asset in union_assets
        )
    )


    cost_fraction = (

        B40_TCA_RATE

        *

        turnover
    )


    risky_return = float(

        sum(

            weight

            *

            realized_returns.get(
                asset,
                -1.0
            )

            for asset, weight in (
                target_weights.items()
            )
        )
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
            risky_return
        )
    )


    period_factor = max(

        period_factor,

        1e-12
    )


    new_wealth = (

        wealth

        *

        period_factor
    )


    cash_weight = max(

        0.0,

        1.0

        -

        sum(
            target_weights.values()
        )
    )


    end_risky_values = {

        asset:

            weight

            *

            (
                1.0

                +

                realized_returns.get(
                    asset,
                    -1.0
                )
            )

        for asset, weight
        in target_weights.items()
    }


    end_total = (

        cash_weight

        +

        sum(
            end_risky_values.values()
        )
    )


    if end_total <= 0:

        drifted_weights = {}


    else:

        drifted_weights = {

            asset:

                value

                /

                end_total

            for asset, value
            in end_risky_values.items()

            if (

                np.isfinite(
                    value
                )

                and

                value > 0
            )
        }


    return {

        "wealth":
            new_wealth,

        "weights":
            drifted_weights,

        "turnover":
            turnover,

        "cost_fraction":
            cost_fraction,

        "risky_return":
            risky_return,

        "period_factor":
            period_factor,
    }


# ==============================================================================
# 13. EXPERT STATE
# ==============================================================================

expert_state = {

    expert: {

        "wealth":
            1.0,

        "weights":
            {},
    }

    for expert in V5_EXPERTS
}


# Actual V5 portfolio only begins on exact Block-41 evaluation start.

actual_state = {

    "wealth":
        1.0,

    "weights":
        {},
}


V5_PATH_ROWS = []

V5_EXPERT_ROWS = []

V5_SELECTION_ROWS = []


# ==============================================================================
# 14. WALK FORWARD
# ==============================================================================

print(
    "\n[V5] Running causal expert prehistory + evaluation..."
)


for period_no, row in enumerate(

    V5_SCHEDULE.itertuples(
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


    # --------------------------------------------------------------------------
    # Build each sleeve using information available at signal time.
    # --------------------------------------------------------------------------

    targets = (

        v5_build_targets(

            signal_date=
                signal_date,

            execution_date=
                execution_date,
        )
    )


    # --------------------------------------------------------------------------
    # Leader is chosen BEFORE current-period returns are seen.
    # --------------------------------------------------------------------------

    leader_before_period = max(

        V5_EXPERTS,

        key=lambda name:

            expert_state[
                name
            ][
                "wealth"
            ],
    )


    expert_wealth_before = {

        name:

            float(
                expert_state[
                    name
                ][
                    "wealth"
                ]
            )

        for name in V5_EXPERTS
    }


    # --------------------------------------------------------------------------
    # One realized-return map for union of all expert holdings.
    # --------------------------------------------------------------------------

    union_assets = set()


    for weights in targets.values():

        union_assets.update(
            weights.keys()
        )


    realized_returns = (

        b41_realized_asset_returns(

            assets=
                list(
                    union_assets
                ),

            execution_date=
                execution_date,

            exit_date=
                exit_date,

            final_period=
                final_period,
        )

        if union_assets

        else {}
    )


    # ======================================================================
    # ACTUAL V5 PORTFOLIO
    # ======================================================================

    if execution_date >= V5_START:

        chosen_target = targets[
            leader_before_period
        ]


        actual_result = v5_advance(

            wealth=
                actual_state[
                    "wealth"
                ],

            previous_weights=
                actual_state[
                    "weights"
                ],

            target_weights=
                chosen_target,

            realized_returns=
                realized_returns,
        )


        actual_state = {

            "wealth":
                actual_result[
                    "wealth"
                ],

            "weights":
                actual_result[
                    "weights"
                ],
        }


        V5_PATH_ROWS.append(
            {

                "Period":
                    period_no,

                "Signal_Date":
                    signal_date,

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    exit_date,

                "Leader":
                    leader_before_period,

                "Wealth":
                    actual_state[
                        "wealth"
                    ],

                "Turnover":
                    actual_result[
                        "turnover"
                    ],

                "Cost_Fraction":
                    actual_result[
                        "cost_fraction"
                    ],

                "Period_Return_Net":

                    actual_result[
                        "period_factor"
                    ]
                    -
                    1.0,

                "Held_Names":
                    len(
                        chosen_target
                    ),

                "Max_Name_Weight":

                    (
                        max(
                            chosen_target.values()
                        )

                        if chosen_target

                        else
                        0.0
                    ),
            }
        )


        V5_SELECTION_ROWS.append(
            {

                "Execution_Date":
                    execution_date,

                "Leader":
                    leader_before_period,

                **{

                    f"Wealth_{name}":

                        expert_wealth_before[
                            name
                        ]

                    for name in V5_EXPERTS
                },
            }
        )


    # ======================================================================
    # UPDATE EVERY EXPERT AFTER THE PERIOD
    # ======================================================================

    for expert in V5_EXPERTS:

        result = v5_advance(

            wealth=
                expert_state[
                    expert
                ][
                    "wealth"
                ],

            previous_weights=
                expert_state[
                    expert
                ][
                    "weights"
                ],

            target_weights=
                targets[
                    expert
                ],

            realized_returns=
                realized_returns,
        )


        expert_state[
            expert
        ] = {

            "wealth":
                result[
                    "wealth"
                ],

            "weights":
                result[
                    "weights"
                ],
        }


        V5_EXPERT_ROWS.append(
            {

                "Date":
                    exit_date,

                "Expert":
                    expert,

                "Wealth":
                    result[
                        "wealth"
                    ],

                "Turnover":
                    result[
                        "turnover"
                    ],

                "Net_Period_Return":

                    result[
                        "period_factor"
                    ]
                    -
                    1.0,
            }
        )


# ==============================================================================
# 15. OUTPUT TABLES
# ==============================================================================

V5_PATH = pd.DataFrame(
    V5_PATH_ROWS
)


V5_EXPERT_PATH = pd.DataFrame(
    V5_EXPERT_ROWS
)


V5_SELECTIONS = pd.DataFrame(
    V5_SELECTION_ROWS
)


if V5_PATH.empty:

    raise RuntimeError(
        "V5 produced zero evaluation observations."
    )


# ==============================================================================
# 16. PERFORMANCE
# ==============================================================================

V5_FINAL_WEALTH = float(

    V5_PATH[
        "Wealth"
    ]
    .iloc[
        -1
    ]
)


V5_NET_RETURN_PCT = (

    100.0

    *

    (
        V5_FINAL_WEALTH
        -
        1.0
    )
)


elapsed_years = (

    (
        V5_END
        -
        V5_START
    ).days

    /

    365.25
)


V5_CAGR_PCT = (

    100.0

    *

    (
        V5_FINAL_WEALTH

        **

        (
            1.0
            /
            elapsed_years
        )

        -

        1.0
    )
)


wealth_with_initial = pd.Series(

    [1.0]

    +

    V5_PATH[
        "Wealth"
    ]
    .tolist()
)


V5_DRAWDOWN = (

    wealth_with_initial

    /

    wealth_with_initial.cummax()

    -

    1.0
)


V5_MAX_DD_PCT = (

    100.0

    *

    V5_DRAWDOWN.min()
)


V5_TOTAL_TURNOVER = float(

    V5_PATH[
        "Turnover"
    ]
    .sum()
)


V5_SELECTION_COUNTS = (

    V5_PATH[
        "Leader"
    ]

    .value_counts()

    .rename_axis(
        "Leader"
    )

    .to_frame(
        "Periods"
    )
)


V5_SELECTION_COUNTS[
    "Pct"
] = (

    100.0

    *

    V5_SELECTION_COUNTS[
        "Periods"
    ]

    /

    len(
        V5_PATH
    )
)


# ==============================================================================
# 17. FINAL EXPERT WEALTH
# ==============================================================================

V5_FINAL_EXPERT_WEALTH = pd.DataFrame(
    {

        "Expert":
            V5_EXPERTS,

        "Final_Virtual_Wealth":

            [

                expert_state[
                    name
                ][
                    "wealth"
                ]

                for name in V5_EXPERTS
            ],
    }
)


V5_FINAL_EXPERT_WEALTH = (

    V5_FINAL_EXPERT_WEALTH

    .sort_values(
        "Final_Virtual_Wealth",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 18. SAME-CALENDAR BENCHMARK EXTRACTION
# ==============================================================================

def v5_benchmark_wealth(
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


V5_BENCHMARKS = {

    "TQQQ_BH_NET_2BPS":

        v5_benchmark_wealth(
            "TQQQ_BH_NET_2BPS"
        ),

    "QQQ_BH_NET_2BPS":

        v5_benchmark_wealth(
            "QQQ_BH_NET_2BPS"
        ),

    "PIT_EW_NET_2BPS":

        v5_benchmark_wealth(
            "PIT_EW_NET_2BPS"
        ),

    "V4_RIDGE":

        v5_benchmark_wealth(
            "V4_RIDGE"
        ),

    "CASH":

        1.0,
}


V5_STRONGEST_BENCHMARK = max(

    V5_BENCHMARKS,

    key=lambda x:

        V5_BENCHMARKS[
            x
        ]
)


V5_STRONGEST_BENCHMARK_WEALTH = (

    V5_BENCHMARKS[
        V5_STRONGEST_BENCHMARK
    ]
)


V5_MINUS_STRONGEST_PP = (

    100.0

    *

    (
        V5_FINAL_WEALTH

        -

        V5_STRONGEST_BENCHMARK_WEALTH
    )
)


V5_BACKCAST_PASS = (

    V5_FINAL_WEALTH

    >

    V5_STRONGEST_BENCHMARK_WEALTH
)


# ==============================================================================
# 19. FINAL COMPARISON TABLE
# ==============================================================================

comparison_rows = [

    {

        "Strategy":
            "V5_DIRECT_WEALTH",

        "Final_Wealth":
            V5_FINAL_WEALTH,
    }
]


for name, wealth in (
    V5_BENCHMARKS.items()
):

    comparison_rows.append(
        {

            "Strategy":
                name,

            "Final_Wealth":
                wealth,
        }
    )


V5_FINAL_COMPARISON = pd.DataFrame(
    comparison_rows
)


V5_FINAL_COMPARISON[
    "Net_Return_Pct"
] = (

    100.0

    *

    (
        V5_FINAL_COMPARISON[
            "Final_Wealth"
        ]

        -

        1.0
    )
)


V5_FINAL_COMPARISON = (

    V5_FINAL_COMPARISON

    .sort_values(
        "Final_Wealth",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 20. LATEST ACTUAL PORTFOLIO
# ==============================================================================

V5_LATEST_WEIGHTS = pd.DataFrame(
    {

        "Ticker":

            list(
                actual_state[
                    "weights"
                ].keys()
            ),

        "Weight":

            list(
                actual_state[
                    "weights"
                ].values()
            ),
    }
)


if not V5_LATEST_WEIGHTS.empty:

    V5_LATEST_WEIGHTS[
        "Weight_Pct"
    ] = (

        100.0

        *

        V5_LATEST_WEIGHTS[
            "Weight"
        ]
    )


    V5_LATEST_WEIGHTS = (

        V5_LATEST_WEIGHTS

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

V5_CONFIG = {

    "parent":
        V4_FINAL_RESEARCH_FINGERPRINT,

    "rebalance_sessions":
        V5_REBALANCE_SESSIONS,

    "tsmom_lookback":
        V5_TSMOM_LOOKBACK,

    "resmom_total_lookback":
        V5_RESMOM_TOTAL_LOOKBACK,

    "resmom_skip_recent":
        V5_RESMOM_SKIP_RECENT,

    "resmom_min_obs":
        V5_RESMOM_MIN_OBS,

    "meta_selector":
        "CAUSAL_FOLLOW_THE_LEADER",

    "experts":
        V5_EXPERTS,

    "tca_bps":
        B40_TCA_BPS,

    "single_name_cap":
        None,

    "sector_cap":
        None,
}


V5_FINGERPRINT = hashlib.sha256(

    json.dumps(
        V5_CONFIG,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )

).hexdigest()


# ==============================================================================
# 22. RESULTS
# ==============================================================================

print(
    "\n"
    +
    "=" * 120
)

print(
    "V5 FINAL — RESULTS"
)

print(
    "=" * 120
)


print(
    "\n1) FINAL SAME-CALENDAR WEALTH"
)


display(

    V5_FINAL_COMPARISON
    .round(
        6
    )
)


print(
    "\n2) V5 ECONOMICS"
)


V5_ECONOMICS = pd.DataFrame(
    {

        "Metric": [

            "Final wealth",

            "Net return pct",

            "CAGR pct",

            "Observed max drawdown pct",

            "Total turnover",

            "Rebalances",

            "Mean held names",

            "Mean max-name weight pct",
        ],


        "Value": [

            V5_FINAL_WEALTH,

            V5_NET_RETURN_PCT,

            V5_CAGR_PCT,

            V5_MAX_DD_PCT,

            V5_TOTAL_TURNOVER,

            len(
                V5_PATH
            ),

            V5_PATH[
                "Held_Names"
            ]
            .mean(),

            100.0
            *
            V5_PATH[
                "Max_Name_Weight"
            ]
            .mean(),
        ],
    }
)


display(
    V5_ECONOMICS.round(
        6
    )
)


print(
    "\n3) CAUSAL LEADER USAGE"
)


display(

    V5_SELECTION_COUNTS
    .round(
        4
    )
)


print(
    "\n4) STANDALONE EXPERT NET WEALTH"
)


display(

    V5_FINAL_EXPERT_WEALTH
    .round(
        6
    )
)


print(
    "\n5) LATEST ACTUAL PORTFOLIO"
)


if V5_LATEST_WEIGHTS.empty:

    print(
        "100% CASH"
    )


else:

    display(

        V5_LATEST_WEIGHTS

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

    V5_PATH[
        "Exit_Date"
    ],

    V5_PATH[
        "Wealth"
    ],

    label=
        "V5_DIRECT_WEALTH",

    linewidth=
        2.5,
)


# Existing Block-41 benchmark curves if available.

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

                label=
                    benchmark,

                linewidth=
                    1.4,
            )


plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1,
)


plt.title(
    "V5 — Direct-Wealth Engine vs Same-Calendar Benchmarks"
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
# 24. ONE-SHOT VERDICT
# ==============================================================================

print(
    "\n"
    +
    "=" * 120
)

print(
    "V5 FINAL — ONE-SHOT OBJECTIVE VERDICT"
)

print(
    "=" * 120
)


print(
    f"\nV5 final wealth          : "
    f"{V5_FINAL_WEALTH:.6f}"
)


print(
    f"V5 net return            : "
    f"{V5_NET_RETURN_PCT:+.2f}%"
)


print(
    f"Strongest benchmark      : "
    f"{V5_STRONGEST_BENCHMARK}"
)


print(
    f"Benchmark final wealth   : "
    f"{V5_STRONGEST_BENCHMARK_WEALTH:.6f}"
)


print(
    f"V5 minus strongest       : "
    f"{V5_MINUS_STRONGEST_PP:+.3f} pp"
)


print(
    f"\nDevelopment backcast PASS: "
    f"{V5_BACKCAST_PASS}"
)


if V5_BACKCAST_PASS:

    print(
        "\nRESULT:"
    )

    print(
        "V5 BEATS EVERY PREDECLARED SAME-CALENDAR BENCHMARK."
    )

    print(
        "FREEZE THIS ARCHITECTURE NOW."
    )

    print(
        "DO NOT RETUNE IT ON 2023-2026."
    )

    print(
        "ONLY DATA ARRIVING AFTER THIS FREEZE COUNTS AS TRUE FORWARD OOS."
    )


else:

    print(
        "\nRESULT:"
    )

    print(
        "V5 DOES NOT BEAT THE STRONGEST BENCHMARK."
    )

    print(
        "DO NOT PATCH PARAMETERS ON THIS SAME SAMPLE."
    )


print(
    "\nV5 FINGERPRINT:"
)


print(
    V5_FINGERPRINT
)


print(
    "\n[+] V5 ONE-SHOT TEST COMPLETE."
)

print(
    "[+] NO ADDITIONAL DIAGNOSTIC BLOCK IS REQUIRED."
)

print(
    "=" * 120
)
