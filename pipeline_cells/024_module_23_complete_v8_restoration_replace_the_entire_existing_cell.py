# ==============================================================================
# MODULE 23 — COMPLETE V8 RESTORATION (REPLACE THE ENTIRE EXISTING CELL)
# ==============================================================================
# Start copying HERE. The V7 -> V8 bridge below is required, not optional.
# Run after the corrected Module 22. No V7 refit occurs in this cell.
# Includes: validated V7 bridge, original V8 one-shot, freeze/state patch,
# and recovered V16 lambda=0 historical comparator accounting.
# The old file module_23_v8.py lacks the bridge and is NOT this complete cell.
# ==============================================================================

# MODULE 23 INPUT REPAIR: build the old V7 decomposition schema locally.
# No legacy dashboard, V9, V10, V12 or V16 execution is required.
import numpy as np
import pandas as pd
class HistoricalReplicationError(RuntimeError):
    pass
if abs(float(V7_FINAL_WEALTH) - 3.709589) > 0.00000051:
    raise HistoricalReplicationError("V7 does not match historical 3.709589; V8 was not started.")
_RESTORE_EXPECTED_DATES = pd.DatetimeIndex(
    B41_CLOSE_WIDE['SPY'].dropna().loc['2023-10-18':'2026-07-27'].index
)[::21]
def _bridge(ns):
    """Map original V7 targets into the input schema of the original V8.

    No forecasts, resampling, cash substitution, or dates are inferred here.
    Every event is independently reconciled to the official V7 wealth path.
    """
    import numpy as np
    import pandas as pd

    path = ns['V7_PATH'].sort_values('Execution_Date').reset_index(drop=True)
    weights = ns['V7_WEIGHTS']
    expected_dates = ns['_RESTORE_EXPECTED_DATES']
    if not pd.DatetimeIndex(path.Execution_Date).equals(expected_dates):
        raise HistoricalReplicationError('V7 execution calendar differs from historical replay calendar.')
    events, assets = [], []
    previous, wealth = {}, 1.0
    for i, row in enumerate(path.itertuples(index=False)):
        w = weights.loc[weights.Execution_Date == row.Execution_Date]
        if w.Ticker.duplicated().any():
            raise HistoricalReplicationError('Duplicate V7 target ticker.')
        target = dict(zip(w.Ticker, w.Weight.astype(float)))
        if (not target or any(not np.isfinite(v) or v < 0 for v in target.values())
                or not np.isclose(sum(target.values()), 1.0, rtol=0, atol=1e-8)):
            raise HistoricalReplicationError('V7 targets are not a finite, fully invested portfolio.')
        returns = ns['b41_realized_asset_returns'](
            assets=sorted(set(target) | {'TQQQ'}),
            execution_date=row.Execution_Date, exit_date=row.Exit_Date,
            final_period=(i == len(path) - 1),
        )
        gross = sum(v * returns[k] for k, v in target.items())
        turnover = sum(abs(target.get(k, 0.0) - previous.get(k, 0.0))
                       for k in set(target) | set(previous))
        wealth *= (1 - ns['B40_TCA_RATE'] * turnover) * (1 + gross)
        if not (np.isclose(gross, row.Gross_Period_Return, rtol=1e-9, atol=1e-10)
                and np.isclose(turnover, row.Turnover, rtol=1e-9, atol=1e-10)
                and np.isclose(wealth, row.Wealth, rtol=1e-9, atol=1e-10)):
            raise HistoricalReplicationError(f'V7 event/asset reconciliation failed at {row.Execution_Date}.')
        previous = ns['v7_drift_weights'](target, returns)
        stock_weight = sum(v for k, v in target.items() if k != 'TQQQ')
        events.append(dict(Execution_Date=row.Execution_Date, Exit_Date=row.Exit_Date,
                           TQQQ_Return=returns['TQQQ'], Actual_Stock_Weight=stock_weight,
                           Official_Wealth=float(row.Wealth)))
        assets.extend(dict(Execution_Date=row.Execution_Date, Ticker=k,
                           Asset_Return=returns[k], Target_Weight=v)
                      for k, v in target.items())
    ns['V7D_EVENTS'] = pd.DataFrame(events)
    ns['V7D_ASSET_CONTRIBUTIONS'] = pd.DataFrame(assets)
_bridge(globals())

# ---- BEGIN HISTORICAL BLOCK 1 ----
# ==============================================================================
# V8 ONE-SHOT
# PARAMETER-FREE UNIVERSAL TQQQ + V7 ALPHA-SLEEVE META ALLOCATOR
# ==============================================================================
#
# OBJECTIVE
# ---------
# MAXIMIZE NET TERMINAL WEALTH
#
# STRUCTURAL CHANGE vs V7
# -----------------------
# KEEP:
#   - V7 stock-selection engine
#   - V7 alpha-sleeve constituents
#   - TQQQ as default/core asset
#   - 21-session decision calendar
#   - exact realized asset returns
#   - 2 bps transaction costs
#
# REMOVE FROM ALLOCATION:
#   - predicted-alpha magnitude as allocation size
#   - raw Kelly sizing
#   - bang-bang 0/100 sizing driven by noisy alpha magnitude
#
# REPLACE WITH:
#   - parameter-free universal wealth-weighted allocation
#   - uniform prior over every constant TQQQ/sleeve mix w in [0,1]
#   - posterior at t uses ONLY net wealth earned BEFORE t
#   - actual sleeve allocation = posterior mean w
#
# IMPORTANT
# ---------
# This is a RESEARCH BACKCAST.
# V8 design was informed by V7 diagnostics.
# Therefore 2023-2026 is NOT prospective V8 OOS.
#
# If it passes, V8 can be frozen as a NEW challenger.
# True V8 OOS begins only AFTER its freeze date.
#
# No parameter mining occurs inside this block.
#
# ==============================================================================


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hashlib

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V8_REQUIRED = [

    "V7D_EVENTS",
    "V7D_ASSET_CONTRIBUTIONS",

    "B40_TCA_RATE",
    "B40_TCA_BPS",

    "V7_FINGERPRINT",
]


V8_MISSING = [

    x
    for x in V8_REQUIRED
    if x not in globals()
]


if V8_MISSING:

    raise RuntimeError(

        "V8 missing required objects: "

        f"{V8_MISSING}"
    )


print("=" * 126)

print(
    "V8 — PARAMETER-FREE UNIVERSAL CORE-SATELLITE ALLOCATOR"
)

print("=" * 126)


print(
    "\nParent V7 fingerprint:",
    V7_FINGERPRINT
)


print(
    "\nObjective       : MAX NET TERMINAL WEALTH"
)

print(
    "Core            : TQQQ"
)

print(
    "Satellite       : V7 alpha sleeve when available"
)

print(
    "Meta allocator  : UNIVERSAL WEALTH POSTERIOR"
)

print(
    f"TCA             : {B40_TCA_BPS:.2f} bps"
)

print(
    "Parameter search: NONE"
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
    "\nIMPORTANT: RESEARCH BACKCAST — NOT PROSPECTIVE V8 OOS."
)


# ==============================================================================
# 1. CLEAN AUTHORITATIVE EVENT DATA
# ==============================================================================

V8_EVENTS_SOURCE = (

    V7D_EVENTS

    .copy()

    .sort_values(
        "Execution_Date"
    )

    .reset_index(
        drop=True
    )
)


V8_ASSET_SOURCE = (

    V7D_ASSET_CONTRIBUTIONS

    .copy()
)


for col in [

    "Execution_Date",
    "Exit_Date",

]:

    V8_EVENTS_SOURCE[
        col
    ] = (

        pd.to_datetime(
            V8_EVENTS_SOURCE[
                col
            ]
        )

        .dt.normalize()
    )


V8_ASSET_SOURCE[
    "Execution_Date"
] = (

    pd.to_datetime(
        V8_ASSET_SOURCE[
            "Execution_Date"
        ]
    )

    .dt.normalize()
)


# ==============================================================================
# 2. UNIVERSAL MIXTURE GRID
# ==============================================================================

# 1001 is numerical quadrature resolution only.
# It is NOT selected using performance.
#
# w = 0.00 -> 100% TQQQ
# w = 1.00 -> 100% available alpha sleeve

V8_GRID = np.linspace(

    0.0,

    1.0,

    1001,
)


V8_N_EXPERTS = len(
    V8_GRID
)


# Uniform prior.

V8_EXPERT_WEALTH = np.ones(

    V8_N_EXPERTS,

    dtype=float,
)


# Each expert's previous end-of-period drifted holdings:
#
# ticker -> vector of N_EXPERT weights

V8_EXPERT_PREV_DRIFT = {}


# Actual universal strategy previous drifted weights.

V8_PREV_DRIFT = {}


# ==============================================================================
# 3. RESULT STORAGE
# ==============================================================================

V8_RESTORED_TARGETS_BY_DATE = {}

V8_ROWS = []

V8_EXPERT_WEALTH_HISTORY = []

V8_WEALTH = 1.0

V8_TQQQ_WEALTH = 1.0


# ==============================================================================
# 4. HELPERS
# ==============================================================================

def v8_turnover_scalar(

    target,

    previous,

):

    assets = (

        set(
            target
        )

        |

        set(
            previous
        )
    )


    return float(

        sum(

            abs(

                target.get(
                    asset,
                    0.0
                )

                -

                previous.get(
                    asset,
                    0.0
                )
            )

            for asset in assets
        )
    )


def v8_drift_scalar(

    target,

    returns,

    gross_return,

):

    denom = (

        1.0

        +
        gross_return
    )


    if (

        not np.isfinite(
            denom
        )

        or

        denom <= 0
    ):

        return {}


    drifted = {}


    for asset, weight in (
        target.items()
    ):

        value = (

            weight

            *
            (
                1.0

                +
                returns[
                    asset
                ]
            )
        )


        if (

            np.isfinite(
                value
            )

            and

            value > 1e-15
        ):

            drifted[
                asset
            ] = (

                value

                /
                denom
            )


    return drifted


# ==============================================================================
# 5. WALK FORWARD
# ==============================================================================

for event_number, event in (

    V8_EVENTS_SOURCE.iterrows()
):

    execution_date = pd.Timestamp(

        event[
            "Execution_Date"
        ]
    )


    exit_date = pd.Timestamp(

        event[
            "Exit_Date"
        ]
    )


    # --------------------------------------------------------------------------
    # Reconstruct V7's available alpha sleeve on this date.
    # --------------------------------------------------------------------------

    event_assets = (

        V8_ASSET_SOURCE[

            V8_ASSET_SOURCE[
                "Execution_Date"
            ]
            ==
            execution_date
        ]

        .copy()
    )


    returns = {

        str(ticker):
            float(ret)

        for ticker, ret in zip(

            event_assets[
                "Ticker"
            ],

            event_assets[
                "Asset_Return"
            ],
        )
    }


    # TQQQ return is authoritative from decomposition,
    # even if V7 held 0% TQQQ during the event.

    returns[
        "TQQQ"
    ] = float(

        event[
            "TQQQ_Return"
        ]
    )


    stock_rows = (

        event_assets[

            event_assets[
                "Ticker"
            ]
            !=
            "TQQQ"
        ]

        .copy()
    )


    actual_stock_weight = float(

        event[
            "Actual_Stock_Weight"
        ]
    )


    sleeve_available = (

        actual_stock_weight
        >
        1e-10

        and

        not stock_rows.empty
    )


    if sleeve_available:

        sleeve_raw = {

            str(ticker):
                float(weight)

            for ticker, weight in zip(

                stock_rows[
                    "Ticker"
                ],

                stock_rows[
                    "Target_Weight"
                ],
            )

            if (

                np.isfinite(
                    weight
                )

                and

                weight > 0
            )
        }


        sleeve_total = float(

            sum(
                sleeve_raw.values()
            )
        )


        if sleeve_total <= 0:

            sleeve_available = False

            sleeve = {}


        else:

            sleeve = {

                ticker:

                    weight
                    /
                    sleeve_total

                for ticker, weight
                in sleeve_raw.items()
            }


    else:

        sleeve = {}


    # --------------------------------------------------------------------------
    # Realized sleeve return.
    # --------------------------------------------------------------------------

    tqqq_return = float(

        event[
            "TQQQ_Return"
        ]
    )


    if sleeve_available:

        sleeve_return = float(

            sum(

                weight

                *
                returns[
                    ticker
                ]

                for ticker, weight
                in sleeve.items()
            )
        )


        sleeve_excess = (

            sleeve_return

            -
            tqqq_return
        )


    else:

        sleeve_return = (
            tqqq_return
        )


        sleeve_excess = 0.0


    # ==========================================================================
    # 5A. UNIVERSAL POSTERIOR — INFORMATION AVAILABLE BEFORE THIS EVENT
    # ==========================================================================

    finite_wealth = np.where(

        np.isfinite(
            V8_EXPERT_WEALTH
        )

        &

        (
            V8_EXPERT_WEALTH > 0
        ),

        V8_EXPERT_WEALTH,

        0.0,
    )


    posterior_total = float(

        finite_wealth.sum()
    )


    if posterior_total <= 0:

        raise RuntimeError(

            "Universal posterior collapsed."
        )


    posterior = (

        finite_wealth

        /
        posterior_total
    )


    posterior_mean_w = float(

        np.sum(

            posterior

            *
            V8_GRID
        )
    )


    posterior_std_w = float(

        np.sqrt(

            np.sum(

                posterior

                *
                (
                    V8_GRID
                    -
                    posterior_mean_w
                )
                ** 2
            )
        )
    )


    # If no sleeve was produced by the underlying V7 selector,
    # no new hypothetical portfolio is invented.

    if sleeve_available:

        universal_w = (
            posterior_mean_w
        )


    else:

        universal_w = 0.0


    # ==========================================================================
    # 5B. ACTUAL V8 TARGET PORTFOLIO
    # ==========================================================================

    V8_TARGET = {}


    if sleeve_available:

        tqqq_weight = (

            1.0

            -
            universal_w
        )


        if tqqq_weight > 1e-15:

            V8_TARGET[
                "TQQQ"
            ] = tqqq_weight


        for ticker, sleeve_weight in (
            sleeve.items()
        ):

            weight = (

                universal_w

                *
                sleeve_weight
            )


            if weight > 1e-15:

                V8_TARGET[
                    ticker
                ] = (

                    V8_TARGET.get(
                        ticker,
                        0.0
                    )

                    +
                    weight
                )


    else:

        V8_TARGET = {

            "TQQQ":
                1.0
        }


    V8_RESTORED_TARGETS_BY_DATE[execution_date] = dict(V8_TARGET)

    target_sum = float(

        sum(
            V8_TARGET.values()
        )
    )


    if not np.isclose(

        target_sum,

        1.0,

        atol=1e-10,

    ):

        raise RuntimeError(

            f"V8 weights do not sum to one "
            f"at {execution_date.date()}: "
            f"{target_sum}"
        )


    # ==========================================================================
    # 5C. ACTUAL V8 TURNOVER + COST
    # ==========================================================================

    v8_turnover = (

        v8_turnover_scalar(

            target=
                V8_TARGET,

            previous=
                V8_PREV_DRIFT,
        )
    )


    v8_tca = (

        B40_TCA_RATE

        *
        v8_turnover
    )


    # ==========================================================================
    # 5D. ACTUAL V8 REALIZED RETURN
    # ==========================================================================

    v8_gross_return = float(

        sum(

            weight

            *
            returns[
                ticker
            ]

            for ticker, weight
            in V8_TARGET.items()
        )
    )


    v8_net_return = (

        (
            1.0
            -
            v8_tca
        )

        *
        (
            1.0
            +
            v8_gross_return
        )

        -
        1.0
    )


    wealth_before = (
        V8_WEALTH
    )


    V8_WEALTH *= (

        1.0

        +
        v8_net_return
    )


    # ==========================================================================
    # 5E. V8 DRIFT FOR NEXT TURNOVER
    # ==========================================================================

    V8_PREV_DRIFT = (

        v8_drift_scalar(

            target=
                V8_TARGET,

            returns=
                returns,

            gross_return=
                v8_gross_return,
        )
    )


    # ==========================================================================
    # 5F. TQQQ BUY & HOLD BENCHMARK
    # ==========================================================================

    if event_number == 0:

        tqqq_net_event = (

            (
                1.0
                -
                B40_TCA_RATE
            )

            *
            (
                1.0
                +
                tqqq_return
            )

            -
            1.0
        )


    else:

        tqqq_net_event = (
            tqqq_return
        )


    V8_TQQQ_WEALTH *= (

        1.0

        +
        tqqq_net_event
    )


    # ==========================================================================
    # 5G. UPDATE EVERY CONSTANT-MIX EXPERT
    # ==========================================================================

    #
    # Each expert w follows:
    #
    # target_t(w)
    #   = (1-w) TQQQ
    #     + w * sleeve_t
    #
    # whenever sleeve exists.
    #
    # If no sleeve is available:
    #   all experts hold TQQQ.
    #
    # Each expert pays its OWN exact turnover cost.
    #

    expert_target = {}


    if sleeve_available:

        expert_target[
            "TQQQ"
        ] = (

            1.0

            -
            V8_GRID
        )


        for ticker, sleeve_weight in (
            sleeve.items()
        ):

            expert_target[
                ticker
            ] = (

                V8_GRID

                *
                sleeve_weight
            )


    else:

        expert_target[
            "TQQQ"
        ] = np.ones(

            V8_N_EXPERTS,

            dtype=float,
        )


    expert_union_assets = (

        set(
            expert_target
        )

        |

        set(
            V8_EXPERT_PREV_DRIFT
        )
    )


    expert_turnover = np.zeros(

        V8_N_EXPERTS,

        dtype=float,
    )


    zeros = np.zeros(

        V8_N_EXPERTS,

        dtype=float,
    )


    for ticker in (
        expert_union_assets
    ):

        target_vector = (

            expert_target.get(
                ticker,
                zeros
            )
        )


        previous_vector = (

            V8_EXPERT_PREV_DRIFT.get(
                ticker,
                zeros
            )
        )


        expert_turnover += np.abs(

            target_vector

            -
            previous_vector
        )


    expert_tca = (

        B40_TCA_RATE

        *
        expert_turnover
    )


    if sleeve_available:

        expert_gross_return = (

            tqqq_return

            +

            V8_GRID

            *
            sleeve_excess
        )


    else:

        expert_gross_return = np.full(

            V8_N_EXPERTS,

            tqqq_return,

            dtype=float,
        )


    expert_net_growth = (

        (
            1.0

            -
            expert_tca
        )

        *
        (
            1.0

            +
            expert_gross_return
        )
    )


    if np.any(

        expert_net_growth <= 0
    ):

        raise RuntimeError(

            "A universal expert reached "
            "non-positive wealth."
        )


    V8_EXPERT_WEALTH *= (
        expert_net_growth
    )


    # ==========================================================================
    # 5H. EXPERT DRIFT
    # ==========================================================================

    expert_denom = (

        1.0

        +
        expert_gross_return
    )


    next_expert_drift = {}


    for ticker, target_vector in (
        expert_target.items()
    ):

        asset_return = float(

            returns[
                ticker
            ]
        )


        drift_vector = (

            target_vector

            *
            (
                1.0

                +
                asset_return
            )

            /
            expert_denom
        )


        if np.any(

            drift_vector
            >
            1e-15
        ):

            next_expert_drift[
                ticker
            ] = (
                drift_vector
            )


    V8_EXPERT_PREV_DRIFT = (
        next_expert_drift
    )


    # ==========================================================================
    # 5I. SAVE EVENT
    # ==========================================================================

    original_v7_overlay = float(

        event[
            "Actual_Stock_Weight"
        ]
    )


    V8_ROWS.append(
        {

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Sleeve_Available":
                sleeve_available,

            "Sleeve_Names":
                len(
                    sleeve
                ),

            "Posterior_Mean_Overlay":
                posterior_mean_w,

            "Posterior_Std_Overlay":
                posterior_std_w,

            "V8_Effective_Overlay":
                universal_w,

            "V7_Original_Overlay":
                original_v7_overlay,

            "TQQQ_Return":
                tqqq_return,

            "Sleeve_Return":
                sleeve_return,

            "Sleeve_Excess":
                sleeve_excess,

            "V8_Gross_Return":
                v8_gross_return,

            "V8_Turnover":
                v8_turnover,

            "V8_TCA":
                v8_tca,

            "V8_Net_Return":
                v8_net_return,

            "V8_Wealth_Before":
                wealth_before,

            "V8_Wealth":
                V8_WEALTH,

            "TQQQ_Wealth":
                V8_TQQQ_WEALTH,

            "V7_Official_Wealth":
                float(
                    event[
                        "Official_Wealth"
                    ]
                ),
        }
    )


    V8_EXPERT_WEALTH_HISTORY.append(

        V8_EXPERT_WEALTH.copy()
    )


# ==============================================================================
# 6. FINAL DATAFRAMES
# ==============================================================================

V8_PATH = pd.DataFrame(
    V8_ROWS
)


V8_EXPERT_WEALTH_HISTORY = np.vstack(
    V8_EXPERT_WEALTH_HISTORY
)


# ==============================================================================
# 7. UNIVERSAL POSTERIOR AT END OF SAMPLE
# ==============================================================================

V8_FINAL_POSTERIOR = (

    V8_EXPERT_WEALTH

    /
    V8_EXPERT_WEALTH.sum()
)


V8_FINAL_POSTERIOR_MEAN = float(

    np.sum(

        V8_FINAL_POSTERIOR

        *
        V8_GRID
    )
)


V8_FINAL_POSTERIOR_STD = float(

    np.sqrt(

        np.sum(

            V8_FINAL_POSTERIOR

            *
            (
                V8_GRID
                -
                V8_FINAL_POSTERIOR_MEAN
            )
            ** 2
        )
    )
)


# ==============================================================================
# 8. EX-POST BEST CONSTANT MIX — DIAGNOSTIC ONLY
# ==============================================================================

V8_BEST_EXPERT_INDEX = int(

    np.argmax(
        V8_EXPERT_WEALTH
    )
)


V8_BEST_CONSTANT_W = float(

    V8_GRID[
        V8_BEST_EXPERT_INDEX
    ]
)


V8_BEST_CONSTANT_WEALTH = float(

    V8_EXPERT_WEALTH[
        V8_BEST_EXPERT_INDEX
    ]
)


# This value MUST NOT be turned into a fixed trading parameter.


# ==============================================================================
# 9. ECONOMIC METRICS
# ==============================================================================

def v8_event_drawdown(
    wealth
):

    wealth = pd.Series(
        wealth,
        dtype=float,
    )


    extended = pd.concat(

        [

            pd.Series(
                [1.0]
            ),

            wealth.reset_index(
                drop=True
            ),
        ],

        ignore_index=True,
    )


    dd = (

        extended

        /
        extended.cummax()

        -
        1.0
    )


    return float(
        dd.min()
    )


V8_FINAL_WEALTH = float(

    V8_PATH[
        "V8_Wealth"
    ]
    .iloc[
        -1
    ]
)


V8_FINAL_RETURN_PCT = (

    100.0

    *
    (
        V8_FINAL_WEALTH
        -
        1.0
    )
)


V8_TQQQ_FINAL_WEALTH = float(

    V8_PATH[
        "TQQQ_Wealth"
    ]
    .iloc[
        -1
    ]
)


V8_V7_FINAL_WEALTH = float(

    V8_PATH[
        "V7_Official_Wealth"
    ]
    .iloc[
        -1
    ]
)


V8_TOTAL_TURNOVER = float(

    V8_PATH[
        "V8_Turnover"
    ]
    .sum()
)


V8_MEAN_OVERLAY = float(

    V8_PATH[
        "V8_Effective_Overlay"
    ]
    .mean()
)


V8_ACTIVE_MEAN_OVERLAY = float(

    V8_PATH.loc[

        V8_PATH[
            "Sleeve_Available"
        ],

        "V8_Effective_Overlay",
    ]
    .mean()
)


V8_EVENT_MAX_DD = (

    100.0

    *
    v8_event_drawdown(

        V8_PATH[
            "V8_Wealth"
        ]
    )
)


V8_TQQQ_EVENT_MAX_DD = (

    100.0

    *
    v8_event_drawdown(

        V8_PATH[
            "TQQQ_Wealth"
        ]
    )
)


V8_BEATS_TQQQ = (

    V8_FINAL_WEALTH

    >
    V8_TQQQ_FINAL_WEALTH
)


V8_BEATS_V7 = (

    V8_FINAL_WEALTH

    >
    V8_V7_FINAL_WEALTH
)


# ==============================================================================
# 10. TABLE — FINAL RANKING
# ==============================================================================

V8_RANKING = pd.DataFrame(
    {

        "Strategy": [

            "V8_UNIVERSAL_META",
            "V7_KELLY",
            "TQQQ_BH_NET_2BPS",
            "BEST_CONSTANT_MIX_HINDSIGHT_ONLY",
        ],


        "Final_Wealth": [

            V8_FINAL_WEALTH,
            V8_V7_FINAL_WEALTH,
            V8_TQQQ_FINAL_WEALTH,
            V8_BEST_CONSTANT_WEALTH,
        ],
    }
)


V8_RANKING[
    "Net_Return_Pct"
] = (

    100.0

    *
    (
        V8_RANKING[
            "Final_Wealth"
        ]

        -
        1.0
    )
)


V8_RANKING = (

    V8_RANKING

    .sort_values(
        "Final_Wealth",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


V8_RANKING.insert(

    0,

    "Rank",

    np.arange(
        1,
        len(
            V8_RANKING
        )
        +
        1
    ),
)


# ==============================================================================
# 11. OVERLAY COMPARISON TABLE
# ==============================================================================

V8_OVERLAY_AUDIT = (

    V8_PATH[
        [
            "Execution_Date",

            "Sleeve_Available",
            "Sleeve_Names",

            "V7_Original_Overlay",
            "V8_Effective_Overlay",

            "Posterior_Mean_Overlay",
            "Posterior_Std_Overlay",

            "Sleeve_Excess",

            "V8_Turnover",

            "V8_Net_Return",

            "V8_Wealth",
        ]
    ]

    .copy()
)


for col in [

    "V7_Original_Overlay",
    "V8_Effective_Overlay",
    "Posterior_Mean_Overlay",
    "Posterior_Std_Overlay",

]:

    V8_OVERLAY_AUDIT[
        col
        +
        "_Pct"
    ] = (

        100.0

        *
        V8_OVERLAY_AUDIT[
            col
        ]
    )


V8_OVERLAY_AUDIT[
    "Sleeve_Excess_Pct"
] = (

    100.0

    *
    V8_OVERLAY_AUDIT[
        "Sleeve_Excess"
    ]
)


V8_OVERLAY_AUDIT[
    "V8_Net_Return_Pct"
] = (

    100.0

    *
    V8_OVERLAY_AUDIT[
        "V8_Net_Return"
    ]
)


# ==============================================================================
# 12. UNIVERSAL REGRET
# ==============================================================================

V8_UNIVERSAL_REGRET_LOG = (

    np.log(
        V8_BEST_CONSTANT_WEALTH
    )

    -
    np.log(
        V8_FINAL_WEALTH
    )
)


V8_UNIVERSAL_VS_BEST_CONSTANT_PCT = (

    100.0

    *
    (
        V8_FINAL_WEALTH

        /
        V8_BEST_CONSTANT_WEALTH

        -
        1.0
    )
)


# ==============================================================================
# 13. FINGERPRINT
# ==============================================================================

V8_CONFIG_STRING = (

    "V8_UNIVERSAL_META|"

    f"parent={V7_FINGERPRINT}|"

    "core=TQQQ|"

    "satellite=V7_REALIZED_AVAILABLE_SLEEVE|"

    "meta=COVER_STYLE_WEALTH_POSTERIOR|"

    "prior=UNIFORM_0_1|"

    "quadrature=1001|"

    f"tca_bps={B40_TCA_BPS:.8f}|"

    "cash=NONE|"

    "risk_cap=NONE|"

    "name_cap=NONE|"

    "sector_cap=NONE"
)


V8_RESEARCH_FINGERPRINT = (

    hashlib

    .sha256(

        V8_CONFIG_STRING.encode(
            "utf-8"
        )
    )

    .hexdigest()
)


# ==============================================================================
# 14. PRINT
# ==============================================================================

print(
    "\n"
    +
    "=" * 126
)

print(
    "V8 — ONE-SHOT RESULTS"
)

print(
    "=" * 126
)


print(
    "\n1) FINAL NET-WEALTH RANKING"
)


display(

    V8_RANKING

    .round(
        6
    )
)


print(
    "\n2) UNIVERSAL ALLOCATION ECONOMICS"
)


V8_ECONOMICS = pd.DataFrame(
    {

        "Metric": [

            "V8 final wealth",

            "V8 net return pct",

            "TQQQ final wealth",

            "V7 final wealth",

            "V8 minus TQQQ pp",

            "V8 minus V7 pp",

            "Total V8 turnover",

            "Mean V8 overlay pct",

            "Mean V8 overlay when sleeve available pct",

            "V8 event-mark max DD pct",

            "TQQQ event-mark max DD pct",

            "Final posterior mean overlay pct",

            "Final posterior std pct",

            "Ex-post best constant sleeve weight pct",

            "Ex-post best constant wealth",

            "Universal vs best-constant wealth pct",

            "Log-regret vs best constant",
        ],


        "Value": [

            V8_FINAL_WEALTH,

            V8_FINAL_RETURN_PCT,

            V8_TQQQ_FINAL_WEALTH,

            V8_V7_FINAL_WEALTH,

            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                V8_TQQQ_FINAL_WEALTH
            ),

            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                V8_V7_FINAL_WEALTH
            ),

            V8_TOTAL_TURNOVER,

            100.0
            *
            V8_MEAN_OVERLAY,

            100.0
            *
            V8_ACTIVE_MEAN_OVERLAY,

            V8_EVENT_MAX_DD,

            V8_TQQQ_EVENT_MAX_DD,

            100.0
            *
            V8_FINAL_POSTERIOR_MEAN,

            100.0
            *
            V8_FINAL_POSTERIOR_STD,

            100.0
            *
            V8_BEST_CONSTANT_W,

            V8_BEST_CONSTANT_WEALTH,

            V8_UNIVERSAL_VS_BEST_CONSTANT_PCT,

            V8_UNIVERSAL_REGRET_LOG,
        ],
    }
)


display(

    V8_ECONOMICS

    .round(
        6
    )
)


print(
    "\n3) EVENT-BY-EVENT OVERLAY AUDIT"
)


display(

    V8_OVERLAY_AUDIT[
        [
            "Execution_Date",

            "Sleeve_Available",
            "Sleeve_Names",

            "V7_Original_Overlay_Pct",
            "V8_Effective_Overlay_Pct",

            "Posterior_Mean_Overlay_Pct",
            "Posterior_Std_Overlay_Pct",

            "Sleeve_Excess_Pct",

            "V8_Turnover",

            "V8_Net_Return_Pct",

            "V8_Wealth",
        ]
    ]

    .round(
        4
    )
)


# ==============================================================================
# 15. GRAPH — V8 vs V7 vs TQQQ
# ==============================================================================

plt.figure(
    figsize=(
        17,
        8,
    )
)


plt.plot(

    V8_PATH[
        "Exit_Date"
    ],

    V8_PATH[
        "V8_Wealth"
    ],

    marker="o",

    linewidth=2.7,

    label=
        "V8 Universal Meta",
)


plt.plot(

    V8_PATH[
        "Exit_Date"
    ],

    V8_PATH[
        "V7_Official_Wealth"
    ],

    linewidth=2.0,

    label=
        "V7 Kelly",
)


plt.plot(

    V8_PATH[
        "Exit_Date"
    ],

    V8_PATH[
        "TQQQ_Wealth"
    ],

    linewidth=2.0,

    label=
        "TQQQ Buy & Hold",
)


plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1,
)


plt.title(
    "V8 UNIVERSAL META vs V7 KELLY vs TQQQ",
    fontsize=15,
    fontweight="bold",
)


plt.ylabel(
    "Net Wealth"
)


plt.xlabel(
    "Date"
)


plt.legend()


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.30,
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 16. GRAPH — V7 vs V8 OVERLAY
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7,
    )
)


plt.plot(

    V8_PATH[
        "Execution_Date"
    ],

    100.0
    *
    V8_PATH[
        "V7_Original_Overlay"
    ],

    marker="o",

    linewidth=1.8,

    label=
        "V7 Kelly Overlay",
)


plt.plot(

    V8_PATH[
        "Execution_Date"
    ],

    100.0
    *
    V8_PATH[
        "V8_Effective_Overlay"
    ],

    marker="o",

    linewidth=2.5,

    label=
        "V8 Universal Overlay",
)


plt.axhline(
    50,
    linestyle="--",
    linewidth=1,
)


plt.ylim(
    -2,
    102,
)


plt.title(
    "V7 KELLY vs V8 UNIVERSAL ALPHA-SLEEVE ALLOCATION",
    fontsize=15,
    fontweight="bold",
)


plt.ylabel(
    "Alpha Sleeve Weight (%)"
)


plt.xlabel(
    "Execution Date"
)


plt.legend()


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.30,
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 17. GRAPH — FIXED-MIX EXPERT FINAL WEALTH FRONTIER
# ==============================================================================

plt.figure(
    figsize=(
        15,
        7,
    )
)


plt.plot(

    100.0
    *
    V8_GRID,

    V8_EXPERT_WEALTH,

    linewidth=2.3,

    label=
        "Constant-Mix Experts — hindsight diagnostic",
)


plt.axhline(

    V8_FINAL_WEALTH,

    linestyle="--",

    linewidth=2,

    label=
        f"V8 Universal = {V8_FINAL_WEALTH:.3f}",
)


plt.axhline(

    V8_TQQQ_FINAL_WEALTH,

    linestyle=":",

    linewidth=2,

    label=
        f"TQQQ = {V8_TQQQ_FINAL_WEALTH:.3f}",
)


plt.axvline(

    100.0
    *
    V8_BEST_CONSTANT_W,

    linestyle="--",

    linewidth=1,

    label=
        (
            "Hindsight best constant w "
            f"= {100*V8_BEST_CONSTANT_W:.1f}%"
        ),
)


plt.title(
    "V8 — CONSTANT TQQQ / ALPHA-SLEEVE MIX FRONTIER — DIAGNOSTIC ONLY",
    fontsize=15,
    fontweight="bold",
)


plt.xlabel(
    "Constant Alpha-Sleeve Weight (%)"
)


plt.ylabel(
    "Final Net Wealth"
)


plt.legend()


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.30,
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 18. GRAPH — FINAL UNIVERSAL POSTERIOR
# ==============================================================================

plt.figure(
    figsize=(
        15,
        7,
    )
)


plt.plot(

    100.0
    *
    V8_GRID,

    V8_FINAL_POSTERIOR,

    linewidth=2.3,
)


plt.axvline(

    100.0
    *
    V8_FINAL_POSTERIOR_MEAN,

    linestyle="--",

    linewidth=2,

    label=
        (
            "Posterior mean "
            f"= {100*V8_FINAL_POSTERIOR_MEAN:.1f}%"
        ),
)


plt.title(
    "V8 — FINAL UNIVERSAL POSTERIOR OVER ALPHA-SLEEVE WEIGHT",
    fontsize=15,
    fontweight="bold",
)


plt.xlabel(
    "Alpha-Sleeve Weight (%)"
)


plt.ylabel(
    "Posterior Probability Mass"
)


plt.legend()


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.30,
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 19. GRAPH — REALIZED ACTIVE RETURN
# ==============================================================================

V8_PATH[
    "V8_Active_vs_TQQQ"
] = (

    V8_PATH[
        "V8_Gross_Return"
    ]

    -
    V8_PATH[
        "TQQQ_Return"
    ]
)


plt.figure(
    figsize=(
        18,
        7,
    )
)


plt.bar(

    V8_PATH[
        "Execution_Date"
    ],

    100.0
    *
    V8_PATH[
        "V8_Active_vs_TQQQ"
    ],

    width=12,
)


plt.axhline(
    0,
    linewidth=1,
)


plt.title(
    "V8 — REALIZED GROSS ACTIVE RETURN vs TQQQ BY DECISION",
    fontsize=15,
    fontweight="bold",
)


plt.ylabel(
    "V8 - TQQQ Return (pp)"
)


plt.xlabel(
    "Execution Date"
)


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.30,
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 20. ONE-SHOT RESEARCH VERDICT
# ==============================================================================

print(
    "\n"
    +
    "=" * 126
)

print(
    "V8 — ONE-SHOT RESEARCH VERDICT"
)

print(
    "=" * 126
)


print(

    f"\nV8 final wealth        : "
    f"{V8_FINAL_WEALTH:.6f}"
)


print(

    f"V7 final wealth        : "
    f"{V8_V7_FINAL_WEALTH:.6f}"
)


print(

    f"TQQQ final wealth      : "
    f"{V8_TQQQ_FINAL_WEALTH:.6f}"
)


print(

    f"\nV8 minus TQQQ          : "
    f"{100*(V8_FINAL_WEALTH - V8_TQQQ_FINAL_WEALTH):+.3f} pp"
)


print(

    f"V8 minus V7            : "
    f"{100*(V8_FINAL_WEALTH - V8_V7_FINAL_WEALTH):+.3f} pp"
)


print(

    f"\nBeats TQQQ             : "
    f"{V8_BEATS_TQQQ}"
)


print(

    f"Beats V7               : "
    f"{V8_BEATS_V7}"
)


print(
    "\nIMPORTANT:"
)


print(
    "The hindsight best constant sleeve weight is DIAGNOSTIC ONLY."
)


print(
    "It must NEVER be copied into the strategy as a fixed parameter."
)


if (

    V8_BEATS_TQQQ

    and

    V8_BEATS_V7
):

    print(
        "\nRESULT:"
    )

    print(
        "V8 UNIVERSAL META ALLOCATION IMPROVES BOTH V7 AND TQQQ "
        "ON THE RESEARCH BACKCAST."
    )

    print(
        "Architecture qualifies to be frozen as the NEXT challenger."
    )

    print(
        "True V8 OOS must begin only after the new freeze date."
    )


elif V8_BEATS_TQQQ:

    print(
        "\nRESULT:"
    )

    print(
        "V8 BEATS TQQQ BUT DOES NOT IMPROVE THE EXISTING V7 DEVELOPMENT RESULT."
    )

    print(
        "Do not promote it yet."
    )


else:

    print(
        "\nRESULT:"
    )

    print(
        "V8 UNIVERSAL META DOES NOT BEAT TQQQ."
    )

    print(
        "Reject this architecture without tuning the mixture."
    )


print(
    "\nV8 RESEARCH FINGERPRINT:"
)

print(
    V8_RESEARCH_FINGERPRINT
)


print(
    "\n[+] V8 ONE-SHOT COMPLETE."
)

print(
    "[+] NO MIXTURE PARAMETER WAS SELECTED FROM PERFORMANCE."
)

print(
    "=" * 126
)
# ---- END HISTORICAL BLOCK 1 ----

# Verify the base result before the original freeze proclaims success.
if abs(float(V8_FINAL_WEALTH) - 3.861086) > 0.00000051:
    raise HistoricalReplicationError("V8 one-shot differs from historical 3.861086; freeze not executed.")

# ---- BEGIN HISTORICAL BLOCK 2 ----
# ==============================================================================
# V8 — FINAL RESEARCH FREEZE
# STRICT PRE-FORWARD LOCK
# ==============================================================================
#
# PURPOSE
# -------
# Lock the exact V8 architecture that passed the one-shot research backcast.
#
# IMPORTANT TIMELINE
# ------------------
# Historical V8 backcast ends       : 2026-07-27
# V7 forward information observed   : through 2026-09-09
# V8 architecture freeze date       : 2026-09-10
#
# Therefore:
#
#   2023-10-18 -> 2026-07-27
#       = V8 RESEARCH BACKCAST
#
#   2026-08-25 current V7 cycle
#       = BRIDGE / CONTAMINATED-FOR-V8 period
#         because V8 architecture was designed while this period
#         was partially observable.
#
#   FIRST TRUE V8 OOS SCORE
#       = first COMPLETE V8 portfolio period whose allocation
#         is chosen AFTER the frozen bridge cycle has completed.
#
# NO PERFORMANCE OBSERVED AFTER THIS FREEZE MAY ALTER V8.
#
# ==============================================================================


import numpy as np
import pandas as pd
import hashlib
import json
import copy


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V8_FREEZE_REQUIRED = [

    "V8_PATH",
    "V8_GRID",

    "V8_EXPERT_WEALTH",

    "V8_FINAL_WEALTH",
    "V8_V7_FINAL_WEALTH",
    "V8_TQQQ_FINAL_WEALTH",

    "V8_RESEARCH_FINGERPRINT",
    "V8_CONFIG_STRING",

    "V7_FINGERPRINT",

    "B40_TCA_BPS",
    "B40_TCA_RATE",
]


V8_FREEZE_MISSING = [

    x
    for x in V8_FREEZE_REQUIRED
    if x not in globals()
]


if V8_FREEZE_MISSING:

    raise RuntimeError(

        "V8 freeze missing objects: "

        f"{V8_FREEZE_MISSING}"
    )


print("=" * 126)

print(
    "V8 — FINAL RESEARCH FREEZE"
)

print("=" * 126)


# ==============================================================================
# 1. FIXED DATES
# ==============================================================================

V8_RESEARCH_BACKCAST_END = pd.Timestamp(
    "2026-07-27"
)


V8_INFORMATION_CUTOFF = pd.Timestamp(
    "2026-09-09"
)


V8_FREEZE_DATE = pd.Timestamp(
    "2026-09-10"
)


# Current 2026-08-25 cycle was already partially observed
# during V8 architecture design.
#
# It therefore must NOT count as V8 OOS performance.

V8_BRIDGE_PERIOD_START = pd.Timestamp(
    "2026-08-25"
)


# ==============================================================================
# 2. HARD RESULT CHECK
# ==============================================================================

if not (

    V8_FINAL_WEALTH
    >
    V8_TQQQ_FINAL_WEALTH

):

    raise RuntimeError(

        "V8 cannot be frozen as challenger: "
        "research backcast does not beat TQQQ."
    )


if not (

    V8_FINAL_WEALTH
    >
    V8_V7_FINAL_WEALTH

):

    raise RuntimeError(

        "V8 cannot be frozen as challenger: "
        "research backcast does not beat V7."
    )


# ==============================================================================
# 3. EXACT FROZEN ARCHITECTURE
# ==============================================================================

V8_FROZEN_ARCHITECTURE = {

    # --------------------------------------------------------------------------
    # Identity
    # --------------------------------------------------------------------------

    "version":
        "V8",

    "status":
        "FROZEN_CHALLENGER",

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH",

    "parent_version":
        "V7",

    "parent_fingerprint":
        str(
            V7_FINGERPRINT
        ),


    # --------------------------------------------------------------------------
    # Calendar
    # --------------------------------------------------------------------------

    "decision_frequency_sessions":
        21,

    "research_backcast_end":
        str(
            V8_RESEARCH_BACKCAST_END.date()
        ),

    "information_cutoff":
        str(
            V8_INFORMATION_CUTOFF.date()
        ),

    "freeze_date":
        str(
            V8_FREEZE_DATE.date()
        ),

    "bridge_period_start":
        str(
            V8_BRIDGE_PERIOD_START.date()
        ),


    # --------------------------------------------------------------------------
    # Core / satellite
    # --------------------------------------------------------------------------

    "core_asset":
        "TQQQ",

    "satellite":
        "FROZEN_V7_ALPHA_SLEEVE_WHEN_AVAILABLE",

    "no_sleeve_policy":
        "100_PERCENT_TQQQ",

    "long_only":
        True,

    "cash_allowed":
        False,

    "leverage_above_100pct":
        False,


    # --------------------------------------------------------------------------
    # Universal allocation
    # --------------------------------------------------------------------------

    "allocator":
        "COVER_STYLE_UNIVERSAL_WEALTH_POSTERIOR",

    "expert_definition":
        "CONSTANT_TQQQ_ALPHA_SLEEVE_MIX",

    "expert_weight_min":
        0.0,

    "expert_weight_max":
        1.0,

    "quadrature_points":
        int(
            len(
                V8_GRID
            )
        ),

    "prior":
        "UNIFORM",

    "allocation_rule":
        "PRE_EVENT_POSTERIOR_MEAN",

    "posterior_update":
        "AFTER_REALIZED_HOLDING_PERIOD_ONLY",


    # --------------------------------------------------------------------------
    # Trading costs
    # --------------------------------------------------------------------------

    "transaction_cost_bps":
        float(
            B40_TCA_BPS
        ),

    "transaction_cost_model":
        "TCA_RATE_TIMES_L1_TURNOVER",

    "transaction_cost_rate":
        float(
            B40_TCA_RATE
        ),


    # --------------------------------------------------------------------------
    # Constraints
    # --------------------------------------------------------------------------

    "single_name_cap":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "cash_cap":
        None,


    # --------------------------------------------------------------------------
    # Explicitly forbidden
    # --------------------------------------------------------------------------

    "forbidden_post_freeze_changes": [

        "change decision frequency",

        "change TQQQ core",

        "change alpha sleeve definition",

        "change sleeve availability rule",

        "change universal prior",

        "change universal allocation formula",

        "replace posterior mean",

        "use hindsight best constant mix",

        "use 93.1 percent sleeve hindsight result",

        "change TCA after observing OOS",

        "add name cap",

        "add sector cap",

        "add risk cap",

        "change grid based on performance",

        "change model because of forward losses",

        "change model because of forward gains",
    ],
}


# ==============================================================================
# 4. LOCK RESEARCH RESULTS
# ==============================================================================

V8_FROZEN_RESEARCH_RESULTS = {

    "V8_final_wealth":
        float(
            V8_FINAL_WEALTH
        ),

    "V8_net_return_pct":
        float(
            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                1.0
            )
        ),

    "V7_final_wealth":
        float(
            V8_V7_FINAL_WEALTH
        ),

    "TQQQ_final_wealth":
        float(
            V8_TQQQ_FINAL_WEALTH
        ),

    "V8_minus_V7_pp":
        float(

            100.0

            *
            (
                V8_FINAL_WEALTH
                -
                V8_V7_FINAL_WEALTH
            )
        ),

    "V8_minus_TQQQ_pp":
        float(

            100.0

            *
            (
                V8_FINAL_WEALTH
                -
                V8_TQQQ_FINAL_WEALTH
            )
        ),
}


# ==============================================================================
# 5. LOCK UNIVERSAL LEARNING STATE
# ==============================================================================

# This is the posterior state produced by historical V8 research events.
#
# It becomes the immutable starting state for continuation.

V8_FROZEN_GRID = (

    np.asarray(
        V8_GRID,
        dtype=float,
    )

    .copy()
)


V8_FROZEN_EXPERT_WEALTH = (

    np.asarray(
        V8_EXPERT_WEALTH,
        dtype=float,
    )

    .copy()
)


V8_FROZEN_POSTERIOR = (

    V8_FROZEN_EXPERT_WEALTH

    /
    V8_FROZEN_EXPERT_WEALTH.sum()
)


V8_FROZEN_POSTERIOR_MEAN = float(

    np.sum(

        V8_FROZEN_POSTERIOR

        *
        V8_FROZEN_GRID
    )
)


V8_FROZEN_POSTERIOR_STD = float(

    np.sqrt(

        np.sum(

            V8_FROZEN_POSTERIOR

            *
            (
                V8_FROZEN_GRID
                -
                V8_FROZEN_POSTERIOR_MEAN
            )
            ** 2
        )
    )
)


# ==============================================================================
# 6. FREEZE HISTORICAL PATH
# ==============================================================================

V8_FROZEN_RESEARCH_PATH = (

    V8_PATH

    .copy(
        deep=True
    )
)


# ==============================================================================
# 7. BUILD STRICT FREEZE FINGERPRINT
# ==============================================================================

freeze_payload = {

    "architecture":
        V8_FROZEN_ARCHITECTURE,

    "research_results":
        V8_FROZEN_RESEARCH_RESULTS,

    "parent_v8_research_fingerprint":
        str(
            V8_RESEARCH_FINGERPRINT
        ),

    "parent_v8_config":
        str(
            V8_CONFIG_STRING
        ),

    "posterior_mean":
        V8_FROZEN_POSTERIOR_MEAN,

    "posterior_std":
        V8_FROZEN_POSTERIOR_STD,

    "grid_size":
        int(
            len(
                V8_FROZEN_GRID
            )
        ),
}


freeze_serialized = json.dumps(

    freeze_payload,

    sort_keys=True,

    separators=(
        ",",
        ":",
    ),
)


V8_FREEZE_FINGERPRINT = (

    hashlib

    .sha256(

        freeze_serialized.encode(
            "utf-8"
        )
    )

    .hexdigest()
)


# ==============================================================================
# 8. RESEARCH / OOS CLASSIFICATION
# ==============================================================================

V8_EVALUATION_POLICY = {

    "research_backcast":

        (
            "All V8 results through 2026-07-27 "
            "are development/research backcast."
        ),

    "bridge_period":

        (
            "The portfolio cycle beginning 2026-08-25 "
            "is NOT scored as true V8 OOS because "
            "part of that period was observed before "
            "the V8 architecture freeze."
        ),

    "true_oos_start":

        (
            "The first scored V8 OOS portfolio is the "
            "first full portfolio decision made after "
            "the bridge period has completed."
        ),

    "future_updates":

        (
            "After freeze, posterior wealth may update "
            "only according to the already-frozen "
            "universal algorithm using completed "
            "realized portfolio periods."
        ),
}


# ==============================================================================
# 9. STATUS TABLE
# ==============================================================================

V8_FREEZE_STATUS = pd.DataFrame(
    {

        "Field": [

            "Version",

            "Status",

            "Primary objective",

            "Core",

            "Satellite",

            "Decision frequency",

            "TCA bps",

            "Research final wealth",

            "Research net return pct",

            "Research TQQQ wealth",

            "Research V7 wealth",

            "V8 minus TQQQ pp",

            "V8 minus V7 pp",

            "Frozen posterior mean sleeve pct",

            "Frozen posterior std pct",

            "Research backcast end",

            "Information cutoff",

            "Freeze date",

            "Bridge period start",

            "True OOS status",
        ],


        "Value": [

            "V8",

            "FROZEN_CHALLENGER",

            "MAX_NET_TERMINAL_WEALTH",

            "TQQQ",

            "V7 alpha sleeve",

            "21 sessions",

            B40_TCA_BPS,

            V8_FINAL_WEALTH,

            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                1.0
            ),

            V8_TQQQ_FINAL_WEALTH,

            V8_V7_FINAL_WEALTH,

            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                V8_TQQQ_FINAL_WEALTH
            ),

            100.0
            *
            (
                V8_FINAL_WEALTH
                -
                V8_V7_FINAL_WEALTH
            ),

            100.0
            *
            V8_FROZEN_POSTERIOR_MEAN,

            100.0
            *
            V8_FROZEN_POSTERIOR_STD,

            str(
                V8_RESEARCH_BACKCAST_END.date()
            ),

            str(
                V8_INFORMATION_CUTOFF.date()
            ),

            str(
                V8_FREEZE_DATE.date()
            ),

            str(
                V8_BRIDGE_PERIOD_START.date()
            ),

            "NOT STARTED YET",
        ],
    }
)


print(
    "\n"
    +
    "=" * 126
)

print(
    "V8 — FROZEN STATUS"
)

print(
    "=" * 126
)


display(
    V8_FREEZE_STATUS
)


# ==============================================================================
# 10. FINAL ASSERTIONS
# ==============================================================================

assert (

    V8_FROZEN_ARCHITECTURE[
        "transaction_cost_bps"
    ]

    ==
    float(
        B40_TCA_BPS
    )
)


assert (

    V8_FROZEN_ARCHITECTURE[
        "quadrature_points"
    ]

    ==
    len(
        V8_FROZEN_GRID
    )
)


assert np.isclose(

    V8_FROZEN_POSTERIOR.sum(),

    1.0,

    atol=1e-12,
)


assert (

    V8_FINAL_WEALTH
    >
    V8_TQQQ_FINAL_WEALTH
)


assert (

    V8_FINAL_WEALTH
    >
    V8_V7_FINAL_WEALTH
)


# ==============================================================================
# 11. FINAL FREEZE MESSAGE
# ==============================================================================

print(
    "\n"
    +
    "=" * 126
)

print(
    "V8 — RESEARCH FREEZE COMPLETE"
)

print(
    "=" * 126
)


print(

    f"\nV8 research final wealth : "
    f"{V8_FINAL_WEALTH:.6f}"
)


print(

    f"V8 research net return   : "
    f"{100*(V8_FINAL_WEALTH-1):+.2f}%"
)


print(

    f"V8 minus TQQQ            : "
    f"{100*(V8_FINAL_WEALTH-V8_TQQQ_FINAL_WEALTH):+.3f} pp"
)


print(

    f"V8 minus V7              : "
    f"{100*(V8_FINAL_WEALTH-V8_V7_FINAL_WEALTH):+.3f} pp"
)


print(

    f"\nFrozen posterior mean    : "
    f"{100*V8_FROZEN_POSTERIOR_MEAN:.2f}% alpha sleeve"
)


print(

    f"Frozen posterior std     : "
    f"{100*V8_FROZEN_POSTERIOR_STD:.2f}%"
)


print(
    "\nV8 FREEZE FINGERPRINT:"
)

print(
    V8_FREEZE_FINGERPRINT
)


print(
    "\nSTATUS:"
)

print(
    "V8 RESEARCH OBJECTIVE = PASS"
)

print(
    "V8 ARCHITECTURE       = LOCKED"
)

print(
    "V8 TRUE OOS           = NOT STARTED"
)


print(
    "\nRULE:"
)

print(
    "NO V8 PARAMETER OR ARCHITECTURE MAY CHANGE "
    "AFTER OBSERVING FUTURE PERFORMANCE."
)


print(
    "\n[+] V8 IS NOW THE FROZEN CHALLENGER."
)

print(
    "[+] TQQQ REMAINS THE LIVE BENCHMARK / INCUMBENT UNTIL V8 EARNS OOS PROMOTION."
)

print(
    "=" * 126
)
# ---- END HISTORICAL BLOCK 2 ----

# ---- BEGIN HISTORICAL BLOCK 3 ----
# ==============================================================================
# V8 — FROZEN CONTINUATION-STATE PATCH
# ==============================================================================
# TECHNICAL STATE-CONTINUITY PATCH ONLY.
# Preserve exact drifted portfolio states for future transaction-cost continuation.
# No architecture, research result, posterior, allocation rule, or TCA change.

import copy
import hashlib
import json
import numpy as np

V8_PATCH_REQUIRED = [
    "V8_FREEZE_FINGERPRINT",
    "V8_EXPERT_PREV_DRIFT",
    "V8_PREV_DRIFT",
]

V8_PATCH_MISSING = [
    name
    for name in V8_PATCH_REQUIRED
    if name not in globals()
]

if V8_PATCH_MISSING:
    raise RuntimeError(
        "V8 continuation-state patch is missing objects: "
        f"{V8_PATCH_MISSING}"
    )

# 1. FREEZE EXACT EXPERT DRIFT STATE

V8_FROZEN_EXPERT_PREV_DRIFT = {
    str(ticker): np.asarray(values, dtype=float).copy()
    for ticker, values in V8_EXPERT_PREV_DRIFT.items()
}

# 2. FREEZE EXACT ACTUAL V8 DRIFT STATE

V8_FROZEN_PREV_DRIFT = copy.deepcopy(V8_PREV_DRIFT)

# 3. DETERMINISTIC STATE HASHES

def v8_hash_expert_drift(state):
    hasher = hashlib.sha256()

    for ticker in sorted(state):
        hasher.update(ticker.encode("utf-8"))

        array = np.asarray(state[ticker], dtype="<f8")

        hasher.update(
            np.asarray(array.shape, dtype="<i8").tobytes()
        )

        hasher.update(array.tobytes())

    return hasher.hexdigest()


def v8_hash_portfolio_drift(state):
    hasher = hashlib.sha256()

    if not isinstance(state, dict):
        raise TypeError(
            "V8_PREV_DRIFT is expected to be a dictionary."
        )

    for ticker in sorted(state):
        hasher.update(str(ticker).encode("utf-8"))

        hasher.update(
            np.asarray([float(state[ticker])], dtype="<f8").tobytes()
        )

    return hasher.hexdigest()


V8_FROZEN_EXPERT_DRIFT_HASH = v8_hash_expert_drift(
    V8_FROZEN_EXPERT_PREV_DRIFT
)

V8_FROZEN_ACTUAL_DRIFT_HASH = v8_hash_portfolio_drift(
    V8_FROZEN_PREV_DRIFT
)

# 4. CONTINUATION FINGERPRINT

V8_CONTINUATION_STATE_PAYLOAD = {
    "base_freeze_fingerprint": V8_FREEZE_FINGERPRINT,
    "expert_drift_hash": V8_FROZEN_EXPERT_DRIFT_HASH,
    "actual_drift_hash": V8_FROZEN_ACTUAL_DRIFT_HASH,
    "expert_drift_assets": len(V8_FROZEN_EXPERT_PREV_DRIFT),
    "actual_drift_assets": len(V8_FROZEN_PREV_DRIFT),
    "purpose": "EXACT_FORWARD_TRANSACTION_COST_CONTINUATION",
}

V8_CONTINUATION_STATE_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V8_CONTINUATION_STATE_PAYLOAD,
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()

# 5. OUTPUT

print("=" * 120)
print("V8 — FROZEN CONTINUATION-STATE PATCH")
print("=" * 120)

print("\nBase freeze fingerprint       :", V8_FREEZE_FINGERPRINT)
print("Expert drift assets          :", len(V8_FROZEN_EXPERT_PREV_DRIFT))
print("Actual V8 drift assets       :", len(V8_FROZEN_PREV_DRIFT))
print("Expert drift state hash      :", V8_FROZEN_EXPERT_DRIFT_HASH)
print("Actual drift state hash      :", V8_FROZEN_ACTUAL_DRIFT_HASH)
print("Continuation fingerprint     :", V8_CONTINUATION_STATE_FINGERPRINT)
print("\n[+] V8 CONTINUATION STATE IS NOW COMPLETE.")
print("[+] V8 ARCHITECTURE AND RESEARCH RESULTS ARE UNCHANGED.")
print("=" * 120)

# ---- END HISTORICAL BLOCK 3 ----



# =============================================================================
# MODULE 23 — FINAL V8 COMPARATOR ACCOUNTING RECOVERED FROM THE OLD V16 CELL
# =============================================================================
# This is the lambda=0 comparator, not a new allocator. The original V8 target
# weights are fixed. No posterior is retrained on the close-based ledger.
# The original one-shot freeze and its drift snapshot remain separate.

def v8_replay_frozen_targets(targets, close_prices, tca_rate):
    import numpy as np
    import pandas as pd

    targets = targets.copy().sort_index()
    close_prices = close_prices.copy().sort_index()
    if targets.index.has_duplicates or close_prices.index.has_duplicates:
        raise RuntimeError('Duplicate dates in frozen targets or close ledger.')
    if targets.columns.has_duplicates or close_prices.columns.has_duplicates:
        raise RuntimeError('Duplicate ticker columns in frozen targets or close ledger.')
    if len(targets) < 2 or not np.isfinite(targets.to_numpy()).all():
        raise RuntimeError('Invalid frozen target matrix.')
    if (targets.to_numpy() < 0).any() or not np.allclose(targets.sum(axis=1), 1., rtol=0, atol=2e-5):
        raise RuntimeError('Frozen targets must be long-only and fully invested.')
    assets = targets.columns
    previous = np.zeros(len(assets))
    wealth = 1.0
    rows = []
    for j in range(len(targets) - 1):
        start, end = targets.index[j:j+2]
        target = targets.iloc[j].to_numpy(dtype=float)
        p0 = close_prices.reindex(index=[start], columns=assets).iloc[0].to_numpy(dtype=float)
        p1 = close_prices.reindex(index=[end], columns=assets).iloc[0].to_numpy(dtype=float)
        good = np.isfinite(p0) & np.isfinite(p1) & (p0 > 0) & (p1 > 0)
        bad = (target > 1e-14) & ~good  # same numerical threshold as old V16
        if bad.any():
            raise RuntimeError(f'Missing exact lifecycle prices {start} -> {end}: {list(assets[bad])}. No fill or download substitution applied.')
        returns = np.zeros(len(assets))
        returns[good] = p1[good] / p0[good] - 1.0
        turnover = float(np.abs(target - previous).sum())
        cost = tca_rate * turnover
        gross = float(target @ returns)
        # Exact old V16 lambda=0 expression; intentionally not multiplicative TCA.
        factor = 1.0 + gross - cost
        if factor <= 0 or 1 + gross <= 0:
            raise RuntimeError('Nonpositive accounting factor.')
        wealth *= factor
        previous = target * (1 + returns) / (1 + gross)
        rows.append(dict(Execution_Date=start, Exit_Date=end, Gross_Return=gross,
                         Turnover=turnover, TCA_Fraction=cost, Net_Return=gross-cost,
                         Wealth=wealth, Terminal_Cost_Only=False))
    completed_wealth = wealth
    final_target = targets.iloc[-1].to_numpy(dtype=float)
    turnover = float(np.abs(final_target - previous).sum())
    cost = tca_rate * turnover
    if cost >= 1:
        raise RuntimeError('Invalid terminal rebalance cost.')
    wealth *= 1.0 - cost
    rows.append(dict(Execution_Date=targets.index[-1], Exit_Date=targets.index[-1],
                     Gross_Return=0., Turnover=turnover, TCA_Fraction=cost,
                     Net_Return=-cost, Wealth=wealth, Terminal_Cost_Only=True))
    return pd.DataFrame(rows), completed_wealth, wealth, previous


def v8_restore_archived_lifecycle_quote(close_prices):
    """Restore the recorded missing quote, only in the final accounting ledger.

    Source: uploaded original notebook, cell 45 (zero-based), saved output
    'V9 — PRE-PERFORMANCE DATA-QUALITY REPAIR':
        2026-07-27 Adj Close = 9.650000
    This is an archived market-data observation, NOT a fitted strategy parameter.
    Only printed precision is available; original binary precision is not claimed.
    Do not change the original B41/B38 price tables or the frozen V8 targets.
    """
    import numpy as np
    import pandas as pd
    prices = close_prices.copy()
    date = pd.Timestamp('2026-07-27')
    if date not in prices.index or 'HLX' not in prices.columns:
        raise RuntimeError('Expected historical HLX ledger row/column is absent; cannot safely apply the single-quote repair.')
    old = prices.loc[date, 'HLX']
    if np.isfinite(old) and float(old) > 0:
        if abs(float(old) - 9.65) > 0.00000051:
            raise RuntimeError(f'Existing HLX close {old} conflicts with archived 9.650000; it was not overwritten.')
        action = 'EXISTING_QUOTE_AGREES_WITH_ARCHIVE'
    else:
        prices.loc[date, 'HLX'] = 9.65
        action = 'MISSING_QUOTE_RESTORED_FROM_NOTEBOOK_OUTPUT'
    audit = {'Ticker': 'HLX', 'Date': '2026-07-27', 'Adj_Close': float(prices.loc[date, 'HLX']),
             'Action': action, 'Source': 'Original notebook cell 45 saved V9 data-quality repair output',
             'Recorded_Decimals': 6, 'Original_Binary_Precision_Available': False}
    return prices, audit


V8_ONE_SHOT_FINAL_WEALTH = float(V8_FINAL_WEALTH)
V8_FINAL_TARGET_MATRIX = pd.DataFrame.from_dict(
    V8_RESTORED_TARGETS_BY_DATE, orient='index'
).fillna(0.0).sort_index()
V8_FINAL_TARGET_MATRIX.index = pd.DatetimeIndex(V8_FINAL_TARGET_MATRIX.index)

# B41_CLOSE_WIDE derives from B38_ALL_PRICES, before eligibility filtering.
# This supplies full price histories, not only dates when a stock was eligible.
# It must reproduce the archived close-ledger result; missing prices stop here.
V8_FINAL_CLOSE_LEDGER = B41_CLOSE_WIDE.copy()
V8_FINAL_CLOSE_LEDGER.index = pd.DatetimeIndex([
    b41_naive_timestamp(d) for d in V8_FINAL_CLOSE_LEDGER.index
])
V8_FINAL_CLOSE_LEDGER, V8_HLX_REPAIR_AUDIT = v8_restore_archived_lifecycle_quote(
    V8_FINAL_CLOSE_LEDGER
)
print('[V8 archived lifecycle repair]', V8_HLX_REPAIR_AUDIT)
if len(V8_FINAL_TARGET_MATRIX) != 34:
    raise RuntimeError('Final historical accounting requires 34 targets / 33 completed periods.')

(V8_FINAL_RESEARCH_PATH, V8_FINAL_COMPLETED_WEALTH,
 V8_FINAL_RESEARCH_WEALTH, V8_FINAL_PRE_TERMINAL_DRIFT) = v8_replay_frozen_targets(
    V8_FINAL_TARGET_MATRIX, V8_FINAL_CLOSE_LEDGER, B40_TCA_RATE
)
V8_FINAL_TQQQ_TARGETS = pd.DataFrame({'TQQQ': 1.0}, index=V8_FINAL_TARGET_MATRIX.index)
# The old V16 cell takes TQQQ from event_compare (the V12 audit), rather than
# from its lambda expert engine. V12 uses multiplicative cost. Preserve that
# historical comparison exactly, even though V16's V8 comparator uses additive
# period cost. Fully invested TQQQ has only its initial entry turnover.
_v8_tq_prices = V8_FINAL_CLOSE_LEDGER.reindex(
    index=V8_FINAL_TARGET_MATRIX.index, columns=['TQQQ']
)['TQQQ']
if not np.isfinite(_v8_tq_prices).all() or (_v8_tq_prices <= 0).any():
    raise RuntimeError('Missing exact TQQQ close-ledger price.')
V8_FINAL_TQQQ_WEALTH = float(
    (1.0 - B40_TCA_RATE) * _v8_tq_prices.iloc[-1] / _v8_tq_prices.iloc[0]
)
V8_V12_STYLE_REACCOUNT_WEALTH = float(np.prod(
    (1.0 + V8_FINAL_RESEARCH_PATH.Gross_Return)
    * (1.0 - V8_FINAL_RESEARCH_PATH.TCA_Fraction)
))
V8_FINAL_REPLICATION_AUDIT = pd.DataFrame([
    {'Stage': 'Original V8 one-shot', 'Actual': V8_ONE_SHOT_FINAL_WEALTH, 'Historical': 3.861086},
    {'Stage': 'V16 lambda=0 V8 comparator', 'Actual': V8_FINAL_RESEARCH_WEALTH, 'Historical': 4.184169},
    {'Stage': 'Close-ledger TQQQ comparator', 'Actual': V8_FINAL_TQQQ_WEALTH, 'Historical': 3.563433},
])
V8_FINAL_REPLICATION_AUDIT['Matches_6dp'] = (
    V8_FINAL_REPLICATION_AUDIT.Actual - V8_FINAL_REPLICATION_AUDIT.Historical
).abs() <= 0.00000051
print('\nV8 — ORIGINAL ONE-SHOT AND FINAL HISTORICAL COMPARATOR')
display(V8_FINAL_REPLICATION_AUDIT)
print('Final V8 research wealth:', format(V8_FINAL_RESEARCH_WEALTH, '.6f'))
print('Final TQQQ comparator  :', format(V8_FINAL_TQQQ_WEALTH, '.6f'))
print('V12-style V8 accounting:', format(V8_V12_STYLE_REACCOUNT_WEALTH, '.6f'))



if not V8_FINAL_REPLICATION_AUDIT.Matches_6dp.all():
    raise RuntimeError(
        'Accounting code restored, but historical data/targets are not yet numerically matched. '
        'Do not treat the run as a successful historical replication or retune parameters. '
        'The original repaired lifecycle ledger may differ from this daily-price cache.'
    )
print('[+] All three published historical wealth references match at six decimal places.')


# Replace the previous reporting-only appendix at the end of Module 23
# with this entire file. Do not remove the strategy or restoration code.
# All paths are copied; no targets, prices, or strategy results are modified.


def _v8_final_comparison_plot(namespace):
    required = [
        'V8_FINAL_RESEARCH_PATH', 'V8_FINAL_RESEARCH_WEALTH',
        'V8_FINAL_CLOSE_LEDGER', 'V8_FINAL_TQQQ_WEALTH',
        'V7_PATH', 'B40_TCA_RATE',
    ]
    missing = [name for name in required if name not in namespace]
    if missing:
        raise RuntimeError('Missing comparison inputs: ' + ', '.join(missing))

    v8 = namespace['V8_FINAL_RESEARCH_PATH'].copy(deep=True)
    v7 = namespace['V7_PATH'].copy(deep=True)
    final_v8 = float(namespace['V8_FINAL_RESEARCH_WEALTH'])
    dates = pd.DatetimeIndex(pd.to_datetime(v8['Exit_Date']))
    start = pd.Timestamp(v8['Execution_Date'].iloc[0])
    v8_values = v8['Wealth'].to_numpy(dtype=float)
    if not np.isclose(v8_values[-1], final_v8, rtol=0, atol=1e-10):
        raise RuntimeError('Final V8 path and final wealth disagree.')

    if 'Exit_Date' not in v7 or 'Wealth' not in v7:
        raise RuntimeError('V7_PATH requires exact Exit_Date and Wealth columns.')
    v7_dates = pd.DatetimeIndex(pd.to_datetime(v7['Exit_Date']))
    v7_values = v7['Wealth'].to_numpy(dtype=float)
    v7_start = pd.Timestamp(v7['Execution_Date'].iloc[0])

    prices = namespace['V8_FINAL_CLOSE_LEDGER']['TQQQ'].copy()
    p0 = float(prices.loc[start])
    tq_prices = prices.reindex(dates).to_numpy(dtype=float)
    if not np.isfinite(p0) or p0 <= 0 or not np.isfinite(tq_prices).all() or (tq_prices <= 0).any():
        raise RuntimeError('Missing or invalid exact TQQQ close prices.')
    tq_values = (1.0 - float(namespace['B40_TCA_RATE'])) * tq_prices / p0
    if not np.isclose(tq_values[-1], float(namespace['V8_FINAL_TQQQ_WEALTH']), rtol=0, atol=1e-10):
        raise RuntimeError('TQQQ curve and final comparator disagree.')
    if dates.isna().any() or v7_dates.isna().any():
        raise RuntimeError('Missing valuation dates.')
    for values in (v8_values, v7_values, tq_values):
        if not len(values) or not np.isfinite(values).all() or (values <= 0).any():
            raise RuntimeError('Invalid comparison wealth path.')

    with plt.rc_context({'axes.facecolor': 'white', 'figure.facecolor': 'white'}):
        fig, ax = plt.subplots(figsize=(16, 7))
        ax.plot([start] + list(dates), np.r_[1., v8_values],
                color='tab:blue', marker='o', markersize=4, linewidth=2,
                label='V8 Universal Meta — final close accounting')
        ax.plot([v7_start] + list(v7_dates), np.r_[1., v7_values],
                color='tab:orange', linewidth=1.7,
                label='V7 Kelly — original open accounting')
        ax.plot([start] + list(dates), np.r_[1., tq_values],
                color='tab:green', linewidth=1.7,
                label='TQQQ Buy & Hold — close comparator')
        ax.axhline(1.0, color='tab:blue', linestyle='--', linewidth=1, alpha=.7)
        ax.annotate(f'{final_v8:.6f}', (dates[-1], v8_values[-1]),
                    xytext=(-75, 12), textcoords='offset points', color='tab:blue')
        ax.set_title('V8 UNIVERSAL META vs V7 KELLY vs TQQQ', fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Net Wealth')
        ax.grid(alpha=.25, linestyle='--')
        ax.legend(loc='upper left')
        fig.text(.5, .015,
                 'Historical accounting comparison: V8 and TQQQ use closes; V7 retains its original open-based accounting. '
                 'Event valuation points, not daily NAV.',
                 ha='center', fontsize=9)
        fig.tight_layout(rect=(0, .045, 1, 1))
        plt.show()

    print(f'V8 final wealth       : {final_v8:.6f} | net return: {100*(final_v8-1):+.4f}%')
    print(f'V7 original wealth    : {v7_values[-1]:.6f}')
    print(f'TQQQ close comparator : {tq_values[-1]:.6f}')
    print('Different historical accounting conventions are retained; this is not a harmonized execution comparison.')


_v8_final_comparison_plot(globals())
