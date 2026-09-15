# MODULE 35 — V11 FOLLOW-THE-LEADER TEST
# Run in the same notebook, in module order.

# ==============================================================================
# V11 — BLOCK 3
# EXACT EXECUTION PREFLIGHT
# + CAUSAL TQQQ-FIRST FOLLOW-THE-LEADER ALLOCATOR
# + ONE-SHOT ECONOMIC TEST
# + DAILY NAV
# + ROLLING 1D / 1W / 1M / 3M / 6M / 9M / 12M ROBUSTNESS
# ==============================================================================

import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V11_B3_REQUIRED = [
    "V11_RESEARCH_CONTRACT_FINGERPRINT",
    "V11_BLOCK2_RESEARCH_FINGERPRINT",
    "V11_BLOCK2_SPEC_FINGERPRINT",
    "V11_RANK_SLEEVE_HASH",

    "V11_STOCK_SLEEVE_DECISIONS",
    "V11_STOCK_SLEEVE_TARGETS",

    "V10_LIFECYCLE_PANEL",
    "V10_BASE_TCA_RATE",
    "V10_IMPACT_COEFFICIENT",
    "V10_REFERENCE_AUM_USD",

    "V11_EVALUATION_WINDOWS",
    "V11_RESEARCH_BACKCAST_END",
]


V11_B3_MISSING = [
    name
    for name in V11_B3_REQUIRED
    if name not in globals()
]

if V11_B3_MISSING:
    raise RuntimeError(
        "V11 Block 3 is missing required objects: "
        f"{V11_B3_MISSING}"
    )


print("=" * 140)
print("V11 — BLOCK 3")
print("EXACT EXECUTION PREFLIGHT")
print("+ CAUSAL TQQQ-FIRST FOLLOW-THE-LEADER ALLOCATOR")
print("+ ONE-SHOT ECONOMIC TEST")
print("=" * 140)

print("\nNO MODEL FITTING WILL OCCUR IN THIS BLOCK.")


# ==============================================================================
# 1. LOCKED BLOCK-3 SPEC
# ==============================================================================

V11_FTL_GRID_POINTS = 1001

V11_BLOCK3_SPEC = {
    "version":
        "V11_BLOCK3",

    "research_contract_fingerprint":
        V11_RESEARCH_CONTRACT_FINGERPRINT,

    "block2_fingerprint":
        V11_BLOCK2_RESEARCH_FINGERPRINT,

    "rank_sleeve_hash":
        V11_RANK_SLEEVE_HASH,

    "core":
        "TQQQ",

    "satellite":
        "V11_RANK_ALPHA",

    "allocator":
        "CAUSAL_FOLLOW_THE_LEADER_CONSTANT_MIX",

    "initial_allocation":
        "100_PERCENT_TQQQ",

    "tie_break":
        "MORE_TQQQ",

    "expert_alpha_interval":
        "[0,1]",

    "grid_points":
        V11_FTL_GRID_POINTS,

    "base_tca_rate":
        float(V10_BASE_TCA_RATE),

    "impact_coefficient":
        float(V10_IMPACT_COEFFICIENT),

    "reference_aum_usd":
        float(V10_REFERENCE_AUM_USD),

    "cash_allowed":
        False,

    "leverage_above_100_pct":
        False,

    "post_result_changes_allowed":
        False,
}


V11_BLOCK3_SPEC_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V11_BLOCK3_SPEC,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
).hexdigest()


print(
    "\nV11 Block 3 specification fingerprint:"
)
print(
    V11_BLOCK3_SPEC_FINGERPRINT
)


# ==============================================================================
# 2. NORMALIZE LIFECYCLE PANEL
# ==============================================================================

V11_LIFECYCLE = (
    V10_LIFECYCLE_PANEL
    .copy()
)


required_cols = [
    "Ticker",
    "Date",
    "Adj_Close",
    "Median_Dollar_Volume_60",
    "V9_Realized_Vol_60",
]


missing_cols = [
    c
    for c in required_cols
    if c not in V11_LIFECYCLE.columns
]


if missing_cols:
    raise RuntimeError(
        f"Lifecycle panel missing columns: {missing_cols}"
    )


V11_LIFECYCLE["Date"] = (
    pd.to_datetime(
        V11_LIFECYCLE["Date"],
        errors="coerce",
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V11_LIFECYCLE["Ticker"] = (
    V11_LIFECYCLE["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V11_LIFECYCLE = (
    V11_LIFECYCLE
    .dropna(
        subset=[
            "Ticker",
            "Date",
        ]
    )
    .drop_duplicates(
        [
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


# ==============================================================================
# 3. PRICE LOOKUP
# ==============================================================================

V11_PRICE_LOOKUP = (
    V11_LIFECYCLE[
        [
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    ]
    .dropna(
        subset=[
            "Adj_Close"
        ]
    )
    .set_index(
        [
            "Ticker",
            "Date",
        ]
    )["Adj_Close"]
    .sort_index()
)


def v11_exact_price(
    ticker,
    date,
):

    ticker = str(
        ticker
    ).upper().strip()

    date = pd.Timestamp(
        date
    ).normalize()

    try:
        value = V11_PRICE_LOOKUP.loc[
            (
                ticker,
                date,
            )
        ]

    except KeyError:
        return np.nan

    if isinstance(
        value,
        pd.Series,
    ):
        value = value.iloc[-1]

    value = float(
        value
    )

    if (
        not np.isfinite(value)
        or value <= 0
    ):
        return np.nan

    return value


# ==============================================================================
# 4. EXECUTION-STATE LOOKUP
# ==============================================================================

V11_STATE_GROUPS = {}

for ticker, group in (
    V11_LIFECYCLE[
        [
            "Ticker",
            "Date",
            "Median_Dollar_Volume_60",
            "V9_Realized_Vol_60",
        ]
    ]
    .groupby(
        "Ticker",
        sort=False,
    )
):
    V11_STATE_GROUPS[ticker] = (
        group
        .set_index("Date")[
            [
                "Median_Dollar_Volume_60",
                "V9_Realized_Vol_60",
            ]
        ]
        .sort_index()
    )


def v11_impact_scale(
    ticker,
    signal_date,
):

    ticker = str(
        ticker
    ).upper().strip()

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()

    if ticker not in V11_STATE_GROUPS:
        return np.nan

    history = V11_STATE_GROUPS[
        ticker
    ]

    if signal_date in history.index:

        row = history.loc[
            signal_date
        ]

        if isinstance(
            row,
            pd.DataFrame,
        ):
            row = row.iloc[-1]

    else:

        prior = history.loc[
            history.index
            <= signal_date
        ]

        if prior.empty:
            return np.nan

        row = prior.iloc[-1]


    adv = float(
        row[
            "Median_Dollar_Volume_60"
        ]
    )

    sigma = float(
        row[
            "V9_Realized_Vol_60"
        ]
    )


    if (
        not np.isfinite(adv)
        or
        not np.isfinite(sigma)
        or
        adv <= 0
        or
        sigma < 0
    ):
        return np.nan


    return float(
        V10_IMPACT_COEFFICIENT
        *
        sigma
        *
        np.sqrt(
            V10_REFERENCE_AUM_USD
            /
            adv
        )
    )


# ==============================================================================
# 5. DECISION CALENDAR
# ==============================================================================

V11_DECISIONS = (
    V11_STOCK_SLEEVE_DECISIONS
    .sort_values(
        "Execution_Date"
    )
    .reset_index(
        drop=True
    )
)


if len(
    V11_DECISIONS
) != 34:
    raise RuntimeError(
        "Expected 34 V11 decisions."
    )


# ==============================================================================
# 6. PRE-PERFORMANCE EXACT QUOTE PREFLIGHT
# ==============================================================================

preflight_rows = []
unresolved = []


for i in range(
    len(
        V11_DECISIONS
    )
):

    row = V11_DECISIONS.iloc[i]

    signal_date = pd.Timestamp(
        row["Signal_Date"]
    )

    execution_date = pd.Timestamp(
        row["Execution_Date"]
    )

    if i < len(V11_DECISIONS) - 1:

        next_execution_date = pd.Timestamp(
            V11_DECISIONS.iloc[
                i + 1
            ]["Execution_Date"]
        )

    else:

        next_execution_date = execution_date


    sleeve = V11_STOCK_SLEEVE_TARGETS[
        execution_date
    ]


    tickers = set(
        sleeve.keys()
    )

    tickers.add(
        "TQQQ"
    )


    missing_entry = 0
    missing_exit = 0
    missing_state = 0


    for ticker in tickers:

        p0 = v11_exact_price(
            ticker,
            execution_date,
        )

        p1 = v11_exact_price(
            ticker,
            next_execution_date,
        )

        scale = v11_impact_scale(
            ticker,
            signal_date,
        )


        if not np.isfinite(
            p0
        ):

            missing_entry += 1

            unresolved.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "ENTRY",

                    "Requested_Date":
                        execution_date,
                }
            )


        if not np.isfinite(
            p1
        ):

            missing_exit += 1

            unresolved.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "NEXT_REBALANCE",

                    "Requested_Date":
                        next_execution_date,
                }
            )


        if not np.isfinite(
            scale
        ):
            missing_state += 1


    preflight_rows.append(
        {
            "Event":
                i + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Next_Execution_Date":
                next_execution_date,

            "Stock_Names":
                len(
                    sleeve
                ),

            "Missing_Entry_Quotes":
                missing_entry,

            "Missing_Next_Rebalance_Quotes":
                missing_exit,

            "Missing_Impact_States":
                missing_state,
        }
    )


V11_PREFLIGHT = pd.DataFrame(
    preflight_rows
)


if (
    V11_PREFLIGHT[
        "Missing_Entry_Quotes"
    ].sum()
    != 0
    or
    V11_PREFLIGHT[
        "Missing_Next_Rebalance_Quotes"
    ].sum()
    != 0
    or
    V11_PREFLIGHT[
        "Missing_Impact_States"
    ].sum()
    != 0
):

    print(
        "\n[!] V11 PREFLIGHT FAILED."
    )

    display(
        V11_PREFLIGHT
    )

    if unresolved:

        print(
            "\nUNRESOLVED QUOTES:"
        )

        display(
            pd.DataFrame(
                unresolved
            )
        )

    raise RuntimeError(
        "V11 stopped BEFORE performance calculation."
    )


print(
    "\n[+] FULL V11 EXECUTION PREFLIGHT PASSED."
)


# ==============================================================================
# 7. PRECOMPUTE EVENT GROWTH MAPS
# ==============================================================================

V11_EVENT_GROWTH = []


for i in range(
    len(
        V11_DECISIONS
    )
):

    row = V11_DECISIONS.iloc[i]

    execution_date = pd.Timestamp(
        row["Execution_Date"]
    )

    if i < len(V11_DECISIONS) - 1:

        exit_date = pd.Timestamp(
            V11_DECISIONS.iloc[
                i + 1
            ]["Execution_Date"]
        )

    else:

        exit_date = execution_date


    sleeve = V11_STOCK_SLEEVE_TARGETS[
        execution_date
    ]


    names = set(
        sleeve.keys()
    )

    names.add(
        "TQQQ"
    )


    growth_map = {}


    for ticker in names:

        p0 = v11_exact_price(
            ticker,
            execution_date,
        )

        p1 = v11_exact_price(
            ticker,
            exit_date,
        )

        growth_map[
            ticker
        ] = (
            p1
            /
            p0
        )


    V11_EVENT_GROWTH.append(
        growth_map
    )


# ==============================================================================
# 8. EXPERT GRID
# ==============================================================================

V11_EXPERT_ALPHA = np.linspace(
    0.0,
    1.0,
    V11_FTL_GRID_POINTS,
)


V11_EXPERT_TQQQ = (
    1.0
    -
    V11_EXPERT_ALPHA
)


# ==============================================================================
# 9. TARGET BUILDERS
# ==============================================================================

def v11_actual_target(
    alpha_weight,
    sleeve,
):

    if not sleeve:
        return {
            "TQQQ": 1.0
        }

    target = {
        "TQQQ":
            1.0
            -
            alpha_weight
    }

    for ticker, sleeve_weight in sleeve.items():

        target[ticker] = (
            target.get(
                ticker,
                0.0,
            )
            +
            alpha_weight
            *
            sleeve_weight
        )

    target = {
        k: float(v)
        for k, v in target.items()
        if v > 0
    }

    total = sum(
        target.values()
    )

    return {
        k: v / total
        for k, v in target.items()
    }


def v11_expert_targets(
    sleeve,
):

    result = {
        "TQQQ":
            V11_EXPERT_TQQQ.copy()
    }

    for ticker, sleeve_weight in sleeve.items():

        result[ticker] = (
            V11_EXPERT_ALPHA
            *
            float(
                sleeve_weight
            )
        )

    return result


# ==============================================================================
# 10. COST FUNCTIONS
# ==============================================================================

def v11_actual_cost(
    previous_drift,
    target,
    signal_date,
):

    names = (
        set(previous_drift)
        |
        set(target)
    )

    turnover = 0.0
    impact = 0.0

    for ticker in names:

        delta = (
            target.get(
                ticker,
                0.0,
            )
            -
            previous_drift.get(
                ticker,
                0.0,
            )
        )

        abs_delta = abs(
            delta
        )

        turnover += abs_delta

        if abs_delta == 0:
            continue

        scale = v11_impact_scale(
            ticker,
            signal_date,
        )

        if not np.isfinite(
            scale
        ):
            raise RuntimeError(
                f"Missing impact state: {ticker}"
            )

        impact += (
            scale
            *
            abs_delta ** 1.5
        )


    base = (
        V10_BASE_TCA_RATE
        *
        turnover
    )

    total = (
        base
        +
        impact
    )

    return (
        float(turnover),
        float(base),
        float(impact),
        float(total),
    )


def v11_expert_cost(
    previous_drift,
    target,
    signal_date,
):

    zero = np.zeros(
        V11_FTL_GRID_POINTS
    )

    turnover = np.zeros(
        V11_FTL_GRID_POINTS
    )

    impact = np.zeros(
        V11_FTL_GRID_POINTS
    )

    names = (
        set(previous_drift)
        |
        set(target)
    )


    for ticker in names:

        current = target.get(
            ticker,
            zero,
        )

        previous = previous_drift.get(
            ticker,
            zero,
        )

        delta = current - previous

        abs_delta = np.abs(
            delta
        )

        turnover += abs_delta

        if not np.any(
            abs_delta > 0
        ):
            continue

        scale = v11_impact_scale(
            ticker,
            signal_date,
        )

        if not np.isfinite(
            scale
        ):
            raise RuntimeError(
                f"Missing expert impact state: {ticker}"
            )

        impact += (
            scale
            *
            abs_delta ** 1.5
        )


    base = (
        V10_BASE_TCA_RATE
        *
        turnover
    )

    total = (
        base
        +
        impact
    )

    return (
        turnover,
        base,
        impact,
        total,
    )


# ==============================================================================
# 11. DRIFT HELPERS
# ==============================================================================

def v11_drift_actual(
    target,
    growth_map,
):

    values = {
        ticker:
            weight
            *
            growth_map[ticker]

        for ticker, weight
        in target.items()
    }

    total = sum(
        values.values()
    )

    return {
        ticker:
            value / total
        for ticker, value
        in values.items()
    }


def v11_drift_experts(
    target,
    growth_map,
):

    end_values = {}
    total = np.zeros(
        V11_FTL_GRID_POINTS
    )

    for ticker, weights in target.items():

        values = (
            weights
            *
            growth_map[ticker]
        )

        end_values[
            ticker
        ] = values

        total += values


    return {
        ticker:
            values / total
        for ticker, values
        in end_values.items()
    }


# ==============================================================================
# 12. FOLLOW-THE-LEADER WALK-FORWARD
# ==============================================================================

V11_EXPERT_WEALTH = np.ones(
    V11_FTL_GRID_POINTS
)


V11_EXPERT_PREVIOUS_DRIFT = {}
V11_ACTUAL_PREVIOUS_DRIFT = {}

V11_WEALTH = 1.0

V11_PATH_ROWS = []
V11_ACTUAL_TARGETS = {}


for i in range(
    len(
        V11_DECISIONS
    )
):

    row = V11_DECISIONS.iloc[i]

    signal_date = pd.Timestamp(
        row["Signal_Date"]
    )

    execution_date = pd.Timestamp(
        row["Execution_Date"]
    )


    if i < len(V11_DECISIONS) - 1:

        exit_date = pd.Timestamp(
            V11_DECISIONS.iloc[
                i + 1
            ]["Execution_Date"]
        )

    else:

        exit_date = execution_date


    sleeve = V11_STOCK_SLEEVE_TARGETS[
        execution_date
    ]

    growth_map = V11_EVENT_GROWTH[i]


    # --------------------------------------------------------------------------
    # CAUSAL FTL SELECTION
    # --------------------------------------------------------------------------
    #
    # At t=0 all experts have wealth=1.
    #
    # Tie-break is MORE TQQQ => smallest alpha weight.
    #
    # np.argmax returns first maximum, so this exactly implements the tie-break.
    # --------------------------------------------------------------------------

    leader_index = int(
        np.argmax(
            V11_EXPERT_WEALTH
        )
    )

    alpha_weight = float(
        V11_EXPERT_ALPHA[
            leader_index
        ]
    )

    tqqq_weight = (
        1.0
        -
        alpha_weight
    )


    # --------------------------------------------------------------------------
    # ACTUAL TARGET
    # --------------------------------------------------------------------------

    target = v11_actual_target(
        alpha_weight,
        sleeve,
    )


    V11_ACTUAL_TARGETS[
        execution_date
    ] = dict(
        target
    )


    (
        turnover,
        base_cost,
        impact_cost,
        total_cost,
    ) = v11_actual_cost(
        V11_ACTUAL_PREVIOUS_DRIFT,
        target,
        signal_date,
    )


    wealth_before_trade = float(
        V11_WEALTH
    )


    wealth_after_trade = (
        wealth_before_trade
        *
        (
            1.0
            -
            total_cost
        )
    )


    gross_multiplier = sum(
        target[ticker]
        *
        growth_map[ticker]

        for ticker in target
    )


    net_multiplier = (
        (
            1.0
            -
            total_cost
        )
        *
        gross_multiplier
    )


    V11_WEALTH *= net_multiplier


    # --------------------------------------------------------------------------
    # EXPERT UPDATE
    # --------------------------------------------------------------------------

    expert_target = v11_expert_targets(
        sleeve
    )


    (
        expert_turnover,
        expert_base,
        expert_impact,
        expert_total_cost,
    ) = v11_expert_cost(
        V11_EXPERT_PREVIOUS_DRIFT,
        expert_target,
        signal_date,
    )


    expert_gross = np.zeros(
        V11_FTL_GRID_POINTS
    )


    for ticker, weights in expert_target.items():

        expert_gross += (
            weights
            *
            growth_map[ticker]
        )


    expert_net = (
        (
            1.0
            -
            expert_total_cost
        )
        *
        expert_gross
    )


    if (
        ~np.isfinite(
            expert_net
        )
    ).any() or (
        expert_net <= 0
    ).any():

        raise RuntimeError(
            "Invalid V11 expert wealth update."
        )


    V11_EXPERT_WEALTH *= expert_net


    # --------------------------------------------------------------------------
    # END-OF-EVENT LEADER
    # --------------------------------------------------------------------------

    next_leader_index = int(
        np.argmax(
            V11_EXPERT_WEALTH
        )
    )


    next_alpha_weight = float(
        V11_EXPERT_ALPHA[
            next_leader_index
        ]
    )


    V11_PATH_ROWS.append(
        {
            "Event":
                i + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Selected_Leader_Index":
                leader_index,

            "Pre_Event_TQQQ_Weight":
                tqqq_weight,

            "Pre_Event_Alpha_Weight":
                alpha_weight,

            "Turnover":
                turnover,

            "Base_TCA_bps":
                10000.0
                *
                base_cost,

            "Impact_Cost_bps":
                10000.0
                *
                impact_cost,

            "Total_Cost_bps":
                10000.0
                *
                total_cost,

            "Gross_Return":
                gross_multiplier
                -
                1.0,

            "Net_Return":
                net_multiplier
                -
                1.0,

            "Wealth_Before_Trade":
                wealth_before_trade,

            "Wealth_After_Trade":
                wealth_after_trade,

            "End_Wealth":
                V11_WEALTH,

            "Next_Leader_Alpha_Weight":
                next_alpha_weight,

            "Best_Expert_Wealth_To_Date":
                float(
                    V11_EXPERT_WEALTH[
                        next_leader_index
                    ]
                ),
        }
    )


    V11_ACTUAL_PREVIOUS_DRIFT = (
        v11_drift_actual(
            target,
            growth_map,
        )
    )


    V11_EXPERT_PREVIOUS_DRIFT = (
        v11_drift_experts(
            expert_target,
            growth_map,
        )
    )


V11_PATH = pd.DataFrame(
    V11_PATH_ROWS
)


# ==============================================================================
# 13. SAME-CALENDAR FULL-COST TQQQ
# ==============================================================================

first_signal = pd.Timestamp(
    V11_DECISIONS[
        "Signal_Date"
    ].iloc[0]
)

first_execution = pd.Timestamp(
    V11_DECISIONS[
        "Execution_Date"
    ].iloc[0]
)

last_execution = pd.Timestamp(
    V11_DECISIONS[
        "Execution_Date"
    ].iloc[-1]
)


tqqq_first_price = v11_exact_price(
    "TQQQ",
    first_execution,
)

tqqq_last_price = v11_exact_price(
    "TQQQ",
    last_execution,
)


tqqq_initial_impact = v11_impact_scale(
    "TQQQ",
    first_signal,
)


tqqq_initial_cost = (
    V10_BASE_TCA_RATE
    +
    tqqq_initial_impact
)


V11_TQQQ_FINAL_WEALTH = (
    (
        1.0
        -
        tqqq_initial_cost
    )
    *
    tqqq_last_price
    /
    tqqq_first_price
)


V11_FINAL_WEALTH = float(
    V11_PATH[
        "End_Wealth"
    ].iloc[-1]
)


# ==============================================================================
# 14. EVENT WEALTH RECONCILIATION
# ==============================================================================

reconstructed = (
    (
        1.0
        +
        V11_PATH[
            "Net_Return"
        ]
    )
    .cumprod()
)


V11_EVENT_WEALTH_ERROR = float(
    np.max(
        np.abs(
            reconstructed.values
            -
            V11_PATH[
                "End_Wealth"
            ].values
        )
    )
)


if V11_EVENT_WEALTH_ERROR > 1e-10:
    raise RuntimeError(
        "V11 event wealth reconstruction failed."
    )


# ==============================================================================
# 15. DAILY MARKET CALENDAR
# ==============================================================================

V11_DAILY_CALENDAR = pd.DatetimeIndex(
    V11_LIFECYCLE.loc[
        (
            V11_LIFECYCLE[
                "Ticker"
            ]
            ==
            "TQQQ"
        )
        &
        (
            V11_LIFECYCLE[
                "Date"
            ]
            >=
            first_execution
        )
        &
        (
            V11_LIFECYCLE[
                "Date"
            ]
            <=
            last_execution
        )
        &
        V11_LIFECYCLE[
            "Adj_Close"
        ].notna(),
        "Date",
    ]
    .drop_duplicates()
    .sort_values()
)


# ==============================================================================
# 16. DAILY PRICES FOR ACTUALLY HELD ASSETS
# ==============================================================================

used_assets = {
    "TQQQ"
}


for target in V11_ACTUAL_TARGETS.values():
    used_assets.update(
        target.keys()
    )


V11_DAILY_PRICES = {}


for ticker in sorted(
    used_assets
):

    series = (
        V11_LIFECYCLE.loc[
            V11_LIFECYCLE[
                "Ticker"
            ]
            ==
            ticker,
            [
                "Date",
                "Adj_Close",
            ],
        ]
        .dropna(
            subset=[
                "Adj_Close"
            ]
        )
        .drop_duplicates(
            "Date",
            keep="last",
        )
        .set_index(
            "Date"
        )[
            "Adj_Close"
        ]
        .sort_index()
        .reindex(
            V11_DAILY_CALENDAR
        )
        .ffill()
    )

    V11_DAILY_PRICES[
        ticker
    ] = series


# ==============================================================================
# 17. DAILY V11 NAV
# ==============================================================================

daily_nav_values = {}


for i in range(
    len(
        V11_PATH
    )
):

    event = V11_PATH.iloc[i]

    execution_date = pd.Timestamp(
        event["Execution_Date"]
    )

    target = V11_ACTUAL_TARGETS[
        execution_date
    ]

    wealth_after_trade = float(
        event[
            "Wealth_After_Trade"
        ]
    )


    if i < len(V11_PATH) - 1:

        next_execution = pd.Timestamp(
            V11_PATH.iloc[
                i + 1
            ][
                "Execution_Date"
            ]
        )

        dates = V11_DAILY_CALENDAR[
            (
                V11_DAILY_CALENDAR
                >= execution_date
            )
            &
            (
                V11_DAILY_CALENDAR
                < next_execution
            )
        ]

    else:

        dates = pd.DatetimeIndex(
            [
                execution_date
            ]
        )


    for date in dates:

        multiplier = 0.0

        for ticker, weight in target.items():

            series = V11_DAILY_PRICES[
                ticker
            ]

            p0 = series.loc[
                execution_date
            ]

            pt = series.loc[
                date
            ]


            if (
                not np.isfinite(p0)
                or
                not np.isfinite(pt)
                or
                p0 <= 0
                or
                pt <= 0
            ):
                raise RuntimeError(
                    f"Daily NAV price gap: {ticker}"
                )


            multiplier += (
                weight
                *
                pt
                /
                p0
            )


        daily_nav_values[
            date
        ] = (
            wealth_after_trade
            *
            multiplier
        )


V11_DAILY_NAV = pd.Series(
    daily_nav_values,
    name="V11",
).sort_index()


V11_DAILY_NAV.loc[
    last_execution
] = float(
    V11_PATH[
        "Wealth_After_Trade"
    ].iloc[-1]
)


V11_DAILY_NAV = (
    V11_DAILY_NAV
    .sort_index()
)


# ==============================================================================
# 18. DAILY TQQQ NAV
# ==============================================================================

tqqq_daily_prices = V11_DAILY_PRICES[
    "TQQQ"
]


V11_TQQQ_DAILY_NAV = (
    (
        1.0
        -
        tqqq_initial_cost
    )
    *
    tqqq_daily_prices
    /
    tqqq_first_price
)


V11_TQQQ_DAILY_NAV.name = (
    "TQQQ"
)


V11_DAILY_COMPARISON = pd.concat(
    [
        V11_DAILY_NAV,
        V11_TQQQ_DAILY_NAV,
    ],
    axis=1,
    join="inner",
).dropna()


# ==============================================================================
# 19. DAILY TERMINAL RECONCILIATION
# ==============================================================================

V11_DAILY_FINAL_ERROR = abs(
    float(
        V11_DAILY_COMPARISON[
            "V11"
        ].iloc[-1]
    )
    -
    V11_FINAL_WEALTH
)


V11_TQQQ_DAILY_FINAL_ERROR = abs(
    float(
        V11_DAILY_COMPARISON[
            "TQQQ"
        ].iloc[-1]
    )
    -
    V11_TQQQ_FINAL_WEALTH
)


if (
    V11_DAILY_FINAL_ERROR > 1e-10
    or
    V11_TQQQ_DAILY_FINAL_ERROR > 1e-10
):
    raise RuntimeError(
        "V11 daily NAV failed terminal reconciliation."
    )


# ==============================================================================
# 20. ROLLING WINDOW ROBUSTNESS
# ==============================================================================

V11_ROLLING_ROWS = []


for horizon, sessions in (
    V11_EVALUATION_WINDOWS.items()
):

    sessions = int(
        sessions
    )


    v11_growth = (
        V11_DAILY_COMPARISON[
            "V11"
        ]
        /
        V11_DAILY_COMPARISON[
            "V11"
        ].shift(
            sessions
        )
        -
        1.0
    )


    tqqq_growth = (
        V11_DAILY_COMPARISON[
            "TQQQ"
        ]
        /
        V11_DAILY_COMPARISON[
            "TQQQ"
        ].shift(
            sessions
        )
        -
        1.0
    )


    excess = (
        v11_growth
        -
        tqqq_growth
    )


    valid = excess.dropna()


    if valid.empty:
        raise RuntimeError(
            f"No valid rolling windows for {horizon}."
        )


    beat_rate = float(
        (
            valid > 0
        ).mean()
    )


    median_excess = float(
        valid.median()
    )


    mean_excess = float(
        valid.mean()
    )


    V11_ROLLING_ROWS.append(
        {
            "Horizon":
                horizon,

            "Trading_Sessions":
                sessions,

            "Rolling_Windows":
                len(
                    valid
                ),

            "Beat_Rate_Pct":
                100.0
                *
                beat_rate,

            "Mean_Excess_Pct":
                100.0
                *
                mean_excess,

            "Median_Excess_Pct":
                100.0
                *
                median_excess,

            "Best_Excess_Pct":
                100.0
                *
                valid.max(),

            "Worst_Excess_Pct":
                100.0
                *
                valid.min(),

            "Beat_Rate_PASS":
                bool(
                    beat_rate > 0.50
                ),

            "Median_Excess_PASS":
                bool(
                    median_excess > 0.0
                ),

            "Window_PASS":
                bool(
                    beat_rate > 0.50
                    and
                    median_excess > 0.0
                ),
        }
    )


V11_ROLLING_AUDIT = pd.DataFrame(
    V11_ROLLING_ROWS
)


# ==============================================================================
# 21. FULL-HISTORY RESULT
# ==============================================================================

V11_NET_RETURN_PCT = (
    100.0
    *
    (
        V11_FINAL_WEALTH
        -
        1.0
    )
)


V11_TQQQ_RETURN_PCT = (
    100.0
    *
    (
        V11_TQQQ_FINAL_WEALTH
        -
        1.0
    )
)


V11_MINUS_TQQQ_PP = (
    100.0
    *
    (
        V11_FINAL_WEALTH
        -
        V11_TQQQ_FINAL_WEALTH
    )
)


V11_RELATIVE_WEALTH = (
    V11_FINAL_WEALTH
    /
    V11_TQQQ_FINAL_WEALTH
)


V11_FULL_PASS = bool(
    V11_FINAL_WEALTH
    >
    V11_TQQQ_FINAL_WEALTH
)


V11_ROLLING_PASS = bool(
    V11_ROLLING_AUDIT[
        "Window_PASS"
    ].all()
)


V11_RESEARCH_VERDICT = (
    "PASS"
    if (
        V11_FULL_PASS
        and
        V11_ROLLING_PASS
    )
    else
    "FAIL"
)


# ==============================================================================
# 22. FTL / ALLOCATION DIAGNOSTICS
# ==============================================================================

V11_TOTAL_TURNOVER = float(
    V11_PATH[
        "Turnover"
    ].sum()
)


V11_MEAN_ALPHA_WEIGHT_PCT = float(
    100.0
    *
    V11_PATH[
        "Pre_Event_Alpha_Weight"
    ].mean()
)


V11_MEDIAN_ALPHA_WEIGHT_PCT = float(
    100.0
    *
    V11_PATH[
        "Pre_Event_Alpha_Weight"
    ].median()
)


V11_ALPHA_ACTIVE_EVENTS = int(
    (
        V11_PATH[
            "Pre_Event_Alpha_Weight"
        ]
        >
        0
    ).sum()
)


V11_FINAL_LEADER_ALPHA_PCT = float(
    100.0
    *
    V11_PATH[
        "Next_Leader_Alpha_Weight"
    ].iloc[-1]
)


# ==============================================================================
# 23. HINDSIGHT BEST CONSTANT EXPERT
# ==============================================================================

best_idx = int(
    np.argmax(
        V11_EXPERT_WEALTH
    )
)


V11_BEST_CONSTANT_ALPHA_PCT = float(
    100.0
    *
    V11_EXPERT_ALPHA[
        best_idx
    ]
)


V11_BEST_CONSTANT_TQQQ_PCT = (
    100.0
    -
    V11_BEST_CONSTANT_ALPHA_PCT
)


V11_BEST_CONSTANT_WEALTH = float(
    V11_EXPERT_WEALTH[
        best_idx
    ]
)


# ==============================================================================
# 24. FINAL RESULT TABLE
# ==============================================================================

V11_FINAL_RESULT_TABLE = pd.DataFrame(
    {
        "Metric": [
            "Research decisions",
            "V11 final wealth",
            "V11 net return pct",
            "TQQQ full-cost wealth",
            "TQQQ full-cost return pct",
            "V11 minus TQQQ pp",
            "V11 / TQQQ relative wealth",
            "Mean Alpha allocation pct",
            "Median Alpha allocation pct",
            "Alpha active events",
            "Final FTL leader Alpha pct",
            "Total turnover",
            "Mean execution cost bps",
            "Median execution cost bps",
            "Best constant expert wealth — hindsight only",
            "Best constant Alpha pct — hindsight only",
            "Best constant TQQQ pct — hindsight only",
            "Event wealth max error",
            "Daily V11 terminal error",
            "Daily TQQQ terminal error",
            "Full-history PASS",
            "All rolling horizons PASS",
            "V11 research verdict",
        ],

        "Value": [
            len(
                V11_PATH
            ),

            V11_FINAL_WEALTH,

            V11_NET_RETURN_PCT,

            V11_TQQQ_FINAL_WEALTH,

            V11_TQQQ_RETURN_PCT,

            V11_MINUS_TQQQ_PP,

            V11_RELATIVE_WEALTH,

            V11_MEAN_ALPHA_WEIGHT_PCT,

            V11_MEDIAN_ALPHA_WEIGHT_PCT,

            V11_ALPHA_ACTIVE_EVENTS,

            V11_FINAL_LEADER_ALPHA_PCT,

            V11_TOTAL_TURNOVER,

            V11_PATH[
                "Total_Cost_bps"
            ].mean(),

            V11_PATH[
                "Total_Cost_bps"
            ].median(),

            V11_BEST_CONSTANT_WEALTH,

            V11_BEST_CONSTANT_ALPHA_PCT,

            V11_BEST_CONSTANT_TQQQ_PCT,

            V11_EVENT_WEALTH_ERROR,

            V11_DAILY_FINAL_ERROR,

            V11_TQQQ_DAILY_FINAL_ERROR,

            V11_FULL_PASS,

            V11_ROLLING_PASS,

            V11_RESEARCH_VERDICT,
        ],
    }
)


# ==============================================================================
# 25. FINAL TARGET
# ==============================================================================

V11_FINAL_TARGET = (
    pd.Series(
        V11_ACTUAL_TARGETS[
            last_execution
        ]
    )
    .sort_values(
        ascending=False
    )
)


V11_FINAL_TARGET_TABLE = (
    100.0
    *
    V11_FINAL_TARGET
).rename(
    "Weight_Pct"
).to_frame()


# ==============================================================================
# 26. RESULT FINGERPRINT
# ==============================================================================

V11_RESULT_PAYLOAD = {

    "block3_spec_fingerprint":
        V11_BLOCK3_SPEC_FINGERPRINT,

    "block2_fingerprint":
        V11_BLOCK2_RESEARCH_FINGERPRINT,

    "rank_sleeve_hash":
        V11_RANK_SLEEVE_HASH,

    "final_wealth":
        V11_FINAL_WEALTH,

    "tqqq_final_wealth":
        V11_TQQQ_FINAL_WEALTH,

    "relative_wealth":
        V11_RELATIVE_WEALTH,

    "full_pass":
        V11_FULL_PASS,

    "rolling_pass":
        V11_ROLLING_PASS,

    "verdict":
        V11_RESEARCH_VERDICT,
}


V11_BLOCK3_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V11_RESULT_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
).hexdigest()


# ==============================================================================
# 27. OUTPUT
# ==============================================================================

print(
    "\n1) V11 FINAL ECONOMIC RESULT"
)

display(
    V11_FINAL_RESULT_TABLE.round(
        6
    )
)


print(
    "\n2) V11 ROLLING HORIZON ROBUSTNESS"
)

display(
    V11_ROLLING_AUDIT.round(
        6
    )
)


print(
    "\n3) V11 FOLLOW-THE-LEADER PATH"
)

display(
    V11_PATH[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Exit_Date",
            "Pre_Event_TQQQ_Weight",
            "Pre_Event_Alpha_Weight",
            "Turnover",
            "Base_TCA_bps",
            "Impact_Cost_bps",
            "Total_Cost_bps",
            "Gross_Return",
            "Net_Return",
            "End_Wealth",
            "Next_Leader_Alpha_Weight",
            "Best_Expert_Wealth_To_Date",
        ]
    ].round(
        6
    )
)


print(
    "\n4) FINAL EXECUTED V11 PORTFOLIO"
)

print(
    "Execution date:",
    last_execution.date(),
)

display(
    V11_FINAL_TARGET_TABLE.head(
        50
    ).round(
        6
    )
)


print(
    "\n5) DAILY NAV VALIDATION"
)

display(
    pd.DataFrame(
        {
            "Metric": [
                "Daily observations",
                "First date",
                "Last date",
                "V11 terminal NAV",
                "V11 event wealth",
                "V11 terminal error",
                "TQQQ terminal NAV",
                "TQQQ terminal wealth",
                "TQQQ terminal error",
            ],

            "Value": [
                len(
                    V11_DAILY_COMPARISON
                ),

                V11_DAILY_COMPARISON.index[0],

                V11_DAILY_COMPARISON.index[-1],

                float(
                    V11_DAILY_COMPARISON[
                        "V11"
                    ].iloc[-1]
                ),

                V11_FINAL_WEALTH,

                V11_DAILY_FINAL_ERROR,

                float(
                    V11_DAILY_COMPARISON[
                        "TQQQ"
                    ].iloc[-1]
                ),

                V11_TQQQ_FINAL_WEALTH,

                V11_TQQQ_DAILY_FINAL_ERROR,
            ],
        }
    )
)


print(
    "\n6) V11 BLOCK 3 RESEARCH FINGERPRINT"
)

print(
    V11_BLOCK3_RESEARCH_FINGERPRINT
)


print(
    "\nRESEARCH VERDICT:"
)

print(
    "V11 beats TQQQ full history :",
    V11_FULL_PASS,
)

print(
    "V11 passes all rolling windows:",
    V11_ROLLING_PASS,
)

print(
    "V11 result                  :",
    V11_RESEARCH_VERDICT,
)


print(
    "\nINTEGRITY:"
)

print(
    "[+] No model was refitted."
)

print(
    "[+] Frozen V11 rank sleeve was used unchanged."
)

print(
    "[+] Event 1 allocation was 100% TQQQ."
)

print(
    "[+] FTL used only previously completed event wealth."
)

print(
    "[+] Tie-break favored more TQQQ."
)

print(
    "[+] No minimum position size."
)

print(
    "[+] No maximum position size."
)

print(
    "[+] No Top-K."
)

print(
    "[+] No sector cap."
)

print(
    "[+] No risk cap."
)

print(
    "[+] No cash."
)

print(
    "[+] No leverage above 100%."
)

print(
    "[+] Underlying-level execution cost included."
)

print(
    "[+] Daily NAV reconciled exactly."
)

print(
    "[+] Rolling robustness used all available windows."
)

print(
    "[+] No single latest-day result determines robustness."
)


print(
    "\nFINAL RULE:"
)

print(
    "DO NOT MODIFY V11 AFTER OBSERVING THIS RESULT."
)

print(
    "If FAIL, close V11 and any new hypothesis becomes V12."
)

print(
    "If PASS, freeze V11 as a research challenger and start true OOS."
)

print("=" * 140)
restored_register('V11', V11_FINAL_WEALTH, V11_PATH, 'End_Wealth', 'Close / original linear + impact costs', 'Historically rejected')
