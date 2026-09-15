# MODULE 29 — V9 UNIVERSAL ALLOCATOR
# Run in the same notebook, in module order.

# ==============================================================================
# V9 — BLOCK 3
# FROZEN THREE-WAY UNIVERSAL WEALTH ALLOCATOR
#
# TQQQ + QQQ + FROZEN V9 COST-AWARE STOCK ALPHA SLEEVE
# ==============================================================================
#
# PRIMARY OBJECTIVE
# -----------------
# MAXIMIZE NET TERMINAL WEALTH RELATIVE TO TQQQ.
#
#
# IMPORTANT
# ---------
# NO MODEL IS FIT HERE.
#
# NO STOCK-SLEEVE PARAMETER IS CHANGED.
#
# THE V9 STOCK SLEEVE PRODUCED BY BLOCK 2B IS USED EXACTLY AS FROZEN.
#
#
# UNIVERSAL ALLOCATOR
# -------------------
# Cover-style wealth-weighted ensemble over constant three-way allocations:
#
#       TQQQ
#       QQQ
#       V9_ALPHA
#
# Constant-mix experts live on the full long-only simplex:
#
#       w_TQQQ >= 0
#       w_QQQ  >= 0
#       w_ALPHA >= 0
#       sum(weights) = 1
#
#
# There is:
#
#       NO cash
#       NO leverage > 100%
#       NO risk cap
#       NO performance-selected allocation
#       NO hindsight best-mix trading
#
#
# NUMERICAL QUADRATURE
# --------------------
# 1 percentage-point simplex resolution.
#
# 101 edge points -> 5,151 constant-mix experts.
#
# This is a numerical integration resolution,
# NOT a performance-selected hyperparameter.
#
#
# CAUSAL ORDER
# ------------
# At every rebalance:
#
#   1. Expert wealth from PRIOR completed events determines posterior.
#   2. Posterior mean determines current V9 sleeve allocation.
#   3. Portfolio is executed.
#   4. Current event return is realized.
#   5. Expert wealth is updated.
#
# Current-period performance can therefore NEVER affect
# the allocation made for that same period.
#
#
# EXECUTION COSTS
# ---------------
# Costs are recomputed at the UNDERLYING ASSET level.
#
# Therefore:
#
#   - Block 2B stock-sleeve costs are NOT double-counted.
#   - Alpha sleeve impact scales naturally with actual allocation.
#   - TQQQ / QQQ trades receive the same execution-cost treatment.
#
#
# TERMINAL CONVENTION
# -------------------
# Final scheduled V9 rebalance is executed and its transaction cost is charged,
# matching the frozen Block 2B convention.
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

V9_B3_REQUIRED = [
    "V9_STOCK_SLEEVE_TARGETS",
    "V9_STOCK_SLEEVE_DECISIONS",
    "V9_STOCK_SLEEVE_REALIZED",

    "V9_LIFECYCLE_PANEL",

    "V9_BASE_TCA_RATE",
    "V9_IMPACT_COEFFICIENT",
    "V9_REFERENCE_AUM_USD",

    "V9_BLOCK2B_RESEARCH_FINGERPRINT",
    "V9_STOCK_SLEEVE_SPEC_FINGERPRINT",
    "V9_ALPHA_SPEC_FINGERPRINT",
    "V9_CONTRACT_FINGERPRINT",
]


V9_B3_MISSING = [
    name
    for name in V9_B3_REQUIRED
    if name not in globals()
]


if V9_B3_MISSING:

    raise RuntimeError(
        "V9 Block 3 is missing required objects: "
        f"{V9_B3_MISSING}"
    )


print("=" * 136)
print("V9 — BLOCK 3")
print("FROZEN THREE-WAY UNIVERSAL WEALTH ALLOCATOR")
print("TQQQ + QQQ + V9 COST-AWARE STOCK ALPHA SLEEVE")
print("=" * 136)

print("\nNO MODEL FITTING WILL OCCUR IN THIS BLOCK.")


# ==============================================================================
# 1. NORMALIZE LIFECYCLE DATA
# ==============================================================================

V9_B3_LIFECYCLE = (
    V9_LIFECYCLE_PANEL
    .copy()
)


V9_B3_LIFECYCLE["Date"] = (
    pd.to_datetime(
        V9_B3_LIFECYCLE["Date"],
        errors="coerce",
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V9_B3_LIFECYCLE["Ticker"] = (
    V9_B3_LIFECYCLE["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_B3_LIFECYCLE = (
    V9_B3_LIFECYCLE
    .replace(
        [np.inf, -np.inf],
        np.nan,
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
# 2. EXACT PRICE LOOKUP
# ==============================================================================

V9_B3_PRICE_LOOKUP = (
    V9_B3_LIFECYCLE[
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


def v9b3_exact_price(
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

        value = V9_B3_PRICE_LOOKUP.loc[
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
        or
        value <= 0
    ):

        return np.nan


    return value


# ==============================================================================
# 3. CAUSAL EXECUTION-STATE LOOKUP
# ==============================================================================

V9_B3_STATE_COLUMNS = [
    "Ticker",
    "Date",
    "Median_Dollar_Volume_60",
    "V9_Realized_Vol_60",
]


for column in V9_B3_STATE_COLUMNS:

    if column not in V9_B3_LIFECYCLE.columns:

        raise RuntimeError(
            "V9 lifecycle state is missing: "
            f"{column}"
        )


V9_B3_STATE = (
    V9_B3_LIFECYCLE[
        V9_B3_STATE_COLUMNS
    ]
    .copy()
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
)


V9_B3_STATE_GROUPS = {
    ticker:
        group.set_index(
            "Date"
        )[
            [
                "Median_Dollar_Volume_60",
                "V9_Realized_Vol_60",
            ]
        ]
        .sort_index()

    for ticker, group
    in V9_B3_STATE.groupby(
        "Ticker",
        sort=False,
    )
}


V9_B3_STATE_FALLBACK_COUNT = 0


def v9b3_impact_scale(
    ticker,
    signal_date,
):

    global V9_B3_STATE_FALLBACK_COUNT


    ticker = str(
        ticker
    ).upper().strip()

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    if ticker not in V9_B3_STATE_GROUPS:

        return np.nan


    history = (
        V9_B3_STATE_GROUPS[
            ticker
        ]
    )


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
            <=
            signal_date
        ]


        if prior.empty:

            return np.nan


        row = prior.iloc[-1]

        V9_B3_STATE_FALLBACK_COUNT += 1


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


    return (
        float(
            V9_IMPACT_COEFFICIENT
        )
        *
        sigma
        *
        np.sqrt(
            float(
                V9_REFERENCE_AUM_USD
            )
            /
            adv
        )
    )


# ==============================================================================
# 4. NORMALIZE FROZEN STOCK-SLEEVE DECISIONS
# ==============================================================================

V9_B3_DECISIONS = (
    V9_STOCK_SLEEVE_DECISIONS
    .copy()
    .sort_values(
        "Execution_Date"
    )
    .reset_index(
        drop=True
    )
)


for column in [
    "Signal_Date",
    "Execution_Date",
]:

    V9_B3_DECISIONS[
        column
    ] = (
        pd.to_datetime(
            V9_B3_DECISIONS[
                column
            ]
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


if len(
    V9_B3_DECISIONS
) != 34:

    raise RuntimeError(
        "V9 Block 3 expected exactly 34 frozen stock-sleeve decisions."
    )


V9_B3_EXECUTION_DATES = (
    V9_B3_DECISIONS[
        "Execution_Date"
    ].tolist()
)


V9_B3_SIGNAL_DATES = (
    V9_B3_DECISIONS[
        "Signal_Date"
    ].tolist()
)


# ==============================================================================
# 5. NORMALIZE FROZEN STOCK TARGETS
# ==============================================================================

V9_B3_STOCK_TARGETS = {}


for execution_date, target in (
    V9_STOCK_SLEEVE_TARGETS.items()
):

    execution_date = pd.Timestamp(
        execution_date
    ).normalize()


    clean_target = {
        str(ticker).upper().strip():
            float(weight)

        for ticker, weight
        in target.items()

        if (
            np.isfinite(
                float(weight)
            )
            and
            float(weight) > 0
        )
    }


    total = float(
        sum(
            clean_target.values()
        )
    )


    if (
        not np.isfinite(total)
        or
        total <= 0
    ):

        raise RuntimeError(
            "Invalid frozen stock-sleeve target at "
            f"{execution_date.date()}."
        )


    clean_target = {
        ticker:
            weight / total

        for ticker, weight
        in clean_target.items()
    }


    V9_B3_STOCK_TARGETS[
        execution_date
    ] = clean_target


for execution_date in V9_B3_EXECUTION_DATES:

    if (
        execution_date
        not in V9_B3_STOCK_TARGETS
    ):

        raise RuntimeError(
            "Frozen stock-sleeve target missing at "
            f"{execution_date.date()}."
        )


# ==============================================================================
# 6. QQQ / TQQQ EXACT-PRICE PREFLIGHT
# ==============================================================================

V9_B3_BENCHMARK_TICKERS = [
    "TQQQ",
    "QQQ",
]


V9_B3_BENCHMARK_PREFLIGHT_ROWS = []


for ticker in V9_B3_BENCHMARK_TICKERS:

    missing_execution_quotes = []


    for execution_date in V9_B3_EXECUTION_DATES:

        price = v9b3_exact_price(
            ticker,
            execution_date,
        )


        if not np.isfinite(
            price
        ):

            missing_execution_quotes.append(
                execution_date
            )


    V9_B3_BENCHMARK_PREFLIGHT_ROWS.append(
        {
            "Ticker":
                ticker,

            "Execution_Dates":
                len(
                    V9_B3_EXECUTION_DATES
                ),

            "Missing_Execution_Quotes":
                len(
                    missing_execution_quotes
                ),
        }
    )


V9_B3_BENCHMARK_PREFLIGHT = pd.DataFrame(
    V9_B3_BENCHMARK_PREFLIGHT_ROWS
)


if (
    V9_B3_BENCHMARK_PREFLIGHT[
        "Missing_Execution_Quotes"
    ].sum()
    !=
    0
):

    display(
        V9_B3_BENCHMARK_PREFLIGHT
    )

    raise RuntimeError(
        "QQQ/TQQQ exact-price preflight failed."
    )


print(
    "\n[+] TQQQ / QQQ exact-price preflight passed."
)


# ==============================================================================
# 7. PRECOMPUTE COMPONENT GROSS RETURNS
# ==============================================================================

V9_B3_COMPONENT_ROWS = []

V9_B3_ALPHA_END_VALUES = []


for event_index in range(
    len(
        V9_B3_EXECUTION_DATES
    )
):

    signal_date = pd.Timestamp(
        V9_B3_SIGNAL_DATES[
            event_index
        ]
    )


    execution_date = pd.Timestamp(
        V9_B3_EXECUTION_DATES[
            event_index
        ]
    )


    if (
        event_index
        <
        len(
            V9_B3_EXECUTION_DATES
        )
        -
        1
    ):

        exit_date = pd.Timestamp(
            V9_B3_EXECUTION_DATES[
                event_index + 1
            ]
        )

    else:

        exit_date = execution_date


    tqqq_start = v9b3_exact_price(
        "TQQQ",
        execution_date,
    )


    tqqq_end = v9b3_exact_price(
        "TQQQ",
        exit_date,
    )


    qqq_start = v9b3_exact_price(
        "QQQ",
        execution_date,
    )


    qqq_end = v9b3_exact_price(
        "QQQ",
        exit_date,
    )


    if not all(
        np.isfinite(
            [
                tqqq_start,
                tqqq_end,
                qqq_start,
                qqq_end,
            ]
        )
    ):

        raise RuntimeError(
            "Missing benchmark price while building V9 Block 3."
        )


    tqqq_multiplier = (
        tqqq_end
        /
        tqqq_start
    )


    qqq_multiplier = (
        qqq_end
        /
        qqq_start
    )


    stock_target = (
        V9_B3_STOCK_TARGETS[
            execution_date
        ]
    )


    alpha_end_values = {}

    alpha_multiplier = 0.0


    for ticker, weight in (
        stock_target.items()
    ):

        start_price = v9b3_exact_price(
            ticker,
            execution_date,
        )


        end_price = v9b3_exact_price(
            ticker,
            exit_date,
        )


        if (
            not np.isfinite(
                start_price
            )
            or
            not np.isfinite(
                end_price
            )
        ):

            raise RuntimeError(
                "Missing frozen alpha-sleeve price: "
                f"{ticker} | "
                f"{execution_date.date()} -> "
                f"{exit_date.date()}"
            )


        growth = (
            end_price
            /
            start_price
        )


        end_value = (
            float(weight)
            *
            growth
        )


        alpha_end_values[
            ticker
        ] = end_value


        alpha_multiplier += (
            end_value
        )


    if (
        not np.isfinite(
            alpha_multiplier
        )
        or
        alpha_multiplier <= 0
    ):

        raise RuntimeError(
            "Invalid gross alpha-sleeve multiplier."
        )


    V9_B3_ALPHA_END_VALUES.append(
        alpha_end_values
    )


    V9_B3_COMPONENT_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "TQQQ_Gross_Multiplier":
                tqqq_multiplier,

            "QQQ_Gross_Multiplier":
                qqq_multiplier,

            "Alpha_Gross_Multiplier":
                alpha_multiplier,
        }
    )


V9_B3_COMPONENT_RETURNS = pd.DataFrame(
    V9_B3_COMPONENT_ROWS
)


# ==============================================================================
# 8. FULL UNDERLYING EXECUTION PREFLIGHT
# ==============================================================================

V9_B3_EXECUTION_PREFLIGHT_ROWS = []


for event_index in range(
    len(
        V9_B3_EXECUTION_DATES
    )
):

    signal_date = pd.Timestamp(
        V9_B3_SIGNAL_DATES[
            event_index
        ]
    )


    current_execution = pd.Timestamp(
        V9_B3_EXECUTION_DATES[
            event_index
        ]
    )


    current_names = set(
        V9_B3_STOCK_TARGETS[
            current_execution
        ]
    )


    current_names.update(
        [
            "TQQQ",
            "QQQ",
        ]
    )


    if event_index > 0:

        previous_execution = pd.Timestamp(
            V9_B3_EXECUTION_DATES[
                event_index - 1
            ]
        )


        current_names.update(
            V9_B3_STOCK_TARGETS[
                previous_execution
            ].keys()
        )


    missing_scales = []


    for ticker in current_names:

        scale = v9b3_impact_scale(
            ticker,
            signal_date,
        )


        if not np.isfinite(
            scale
        ):

            missing_scales.append(
                ticker
            )


    V9_B3_EXECUTION_PREFLIGHT_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Signal_Date":
                signal_date,

            "Assets_Checked":
                len(
                    current_names
                ),

            "Missing_Impact_State":
                len(
                    missing_scales
                ),
        }
    )


V9_B3_EXECUTION_PREFLIGHT = pd.DataFrame(
    V9_B3_EXECUTION_PREFLIGHT_ROWS
)


if (
    V9_B3_EXECUTION_PREFLIGHT[
        "Missing_Impact_State"
    ].sum()
    !=
    0
):

    display(
        V9_B3_EXECUTION_PREFLIGHT
    )

    raise RuntimeError(
        "Underlying execution-state preflight failed. "
        "No V9 Block 3 performance has been calculated."
    )


print(
    "[+] Underlying execution-state preflight passed."
)


# ==============================================================================
# 9. FREEZE V9 BLOCK 3 SPECIFICATION BEFORE PERFORMANCE
# ==============================================================================

V9_UNIVERSAL_EDGE_INTERVALS = 100


V9_BLOCK3_SPEC = {

    "version":
        "V9_BLOCK3",

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH_VS_TQQQ",

    "components":
        (
            "TQQQ",
            "QQQ",
            "FROZEN_V9_STOCK_ALPHA_SLEEVE",
        ),

    "allocator":
        "COVER_STYLE_WEALTH_POSTERIOR",

    "expert_class":
        "CONSTANT_LONG_ONLY_THREE_WAY_MIXES",

    "prior":
        "UNIFORM_OVER_SIMPLEX_GRID",

    "simplex_edge_intervals":
        V9_UNIVERSAL_EDGE_INTERVALS,

    "allocation_rule":
        "PRE_EVENT_POSTERIOR_MEAN",

    "posterior_update":
        "AFTER_COMPLETED_REALIZED_EVENT_ONLY",

    "cash_allowed":
        False,

    "leverage_above_one":
        False,

    "risk_cap":
        None,

    "stock_sleeve_changed":
        False,

    "stock_sleeve_fingerprint":
        V9_STOCK_SLEEVE_SPEC_FINGERPRINT,

    "stock_sleeve_result_fingerprint":
        V9_BLOCK2B_RESEARCH_FINGERPRINT,

    "alpha_fingerprint":
        V9_ALPHA_SPEC_FINGERPRINT,

    "contract_fingerprint":
        V9_CONTRACT_FINGERPRINT,

    "base_tca_rate":
        float(
            V9_BASE_TCA_RATE
        ),

    "impact_coefficient":
        float(
            V9_IMPACT_COEFFICIENT
        ),

    "reference_aum_usd":
        float(
            V9_REFERENCE_AUM_USD
        ),

    "cost_accounting":
        "UNDERLYING_ASSET_LEVEL",

    "terminal_rebalance_cost":
        True,

    "post_result_tuning":
        False,
}


V9_BLOCK3_SPEC_STRING = json.dumps(
    V9_BLOCK3_SPEC,
    sort_keys=True,
    default=str,
)


V9_BLOCK3_SPEC_FINGERPRINT = (
    hashlib.sha256(
        V9_BLOCK3_SPEC_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


print(
    "\nV9 Block 3 specification fingerprint:"
)

print(
    V9_BLOCK3_SPEC_FINGERPRINT
)


# ==============================================================================
# 10. BUILD THE CONSTANT-MIX SIMPLEX GRID
# ==============================================================================

V9_EXPERT_ROWS = []


N = V9_UNIVERSAL_EDGE_INTERVALS


for tqqq_units in range(
    N + 1
):

    for qqq_units in range(
        N
        -
        tqqq_units
        +
        1
    ):

        alpha_units = (
            N
            -
            tqqq_units
            -
            qqq_units
        )


        V9_EXPERT_ROWS.append(
            (
                tqqq_units / N,
                qqq_units / N,
                alpha_units / N,
            )
        )


V9_EXPERT_GRID = np.asarray(
    V9_EXPERT_ROWS,
    dtype=float,
)


V9_EXPERT_TQQQ = (
    V9_EXPERT_GRID[
        :,
        0
    ]
)


V9_EXPERT_QQQ = (
    V9_EXPERT_GRID[
        :,
        1
    ]
)


V9_EXPERT_ALPHA = (
    V9_EXPERT_GRID[
        :,
        2
    ]
)


V9_EXPERT_COUNT = len(
    V9_EXPERT_GRID
)


if V9_EXPERT_COUNT != 5151:

    raise RuntimeError(
        "Unexpected V9 universal expert count."
    )


if not np.allclose(
    V9_EXPERT_GRID.sum(
        axis=1
    ),
    1.0,
):

    raise RuntimeError(
        "Universal expert grid does not lie on simplex."
    )


print(
    "Universal experts:",
    f"{V9_EXPERT_COUNT:,}",
)


# ==============================================================================
# 11. POSTERIOR HELPER
# ==============================================================================

def v9b3_posterior_probabilities(
    log_wealth,
):

    log_wealth = np.asarray(
        log_wealth,
        dtype=float,
    )


    maximum = float(
        np.max(
            log_wealth
        )
    )


    probabilities = np.exp(
        log_wealth
        -
        maximum
    )


    total = float(
        probabilities.sum()
    )


    if (
        not np.isfinite(total)
        or
        total <= 0
    ):

        raise RuntimeError(
            "Universal posterior normalization failed."
        )


    return (
        probabilities
        /
        total
    )


# ==============================================================================
# 12. ACTUAL PORTFOLIO TARGET HELPER
# ==============================================================================

def v9b3_underlying_target(
    sleeve_weights,
    stock_target,
):

    w_tqqq = float(
        sleeve_weights[0]
    )


    w_qqq = float(
        sleeve_weights[1]
    )


    w_alpha = float(
        sleeve_weights[2]
    )


    target = {}


    if w_tqqq > 0:

        target[
            "TQQQ"
        ] = w_tqqq


    if w_qqq > 0:

        target[
            "QQQ"
        ] = w_qqq


    if w_alpha > 0:

        for ticker, weight in (
            stock_target.items()
        ):

            target[
                ticker
            ] = (
                target.get(
                    ticker,
                    0.0,
                )
                +
                w_alpha
                *
                float(weight)
            )


    total = float(
        sum(
            target.values()
        )
    )


    if (
        not np.isfinite(total)
        or
        total <= 0
    ):

        raise RuntimeError(
            "Underlying target construction failed."
        )


    target = {
        ticker:
            weight / total

        for ticker, weight
        in target.items()

        if weight > 0
    }


    return target


# ==============================================================================
# 13. ACTUAL PORTFOLIO DRIFT HELPER
# ==============================================================================

def v9b3_drift_underlying(
    target,
    start_date,
    end_date,
):

    if not target:

        return {}


    values = {}


    for ticker, weight in (
        target.items()
    ):

        start_price = v9b3_exact_price(
            ticker,
            start_date,
        )


        end_price = v9b3_exact_price(
            ticker,
            end_date,
        )


        if (
            not np.isfinite(
                start_price
            )
            or
            not np.isfinite(
                end_price
            )
        ):

            raise RuntimeError(
                "Missing underlying price during V9 drift: "
                f"{ticker} | "
                f"{pd.Timestamp(start_date).date()} -> "
                f"{pd.Timestamp(end_date).date()}"
            )


        values[
            ticker
        ] = (
            float(weight)
            *
            end_price
            /
            start_price
        )


    total = float(
        sum(
            values.values()
        )
    )


    if (
        not np.isfinite(total)
        or
        total <= 0
    ):

        raise RuntimeError(
            "Invalid drifted underlying portfolio."
        )


    return {
        ticker:
            value / total

        for ticker, value
        in values.items()
    }


# ==============================================================================
# 14. ACTUAL EXECUTION COST HELPER
# ==============================================================================

def v9b3_execution_cost(
    previous_weights,
    target_weights,
    signal_date,
):

    names = (
        set(
            previous_weights
        )
        |
        set(
            target_weights
        )
    )


    turnover = 0.0

    impact_cost = 0.0


    for ticker in names:

        delta = (
            float(
                target_weights.get(
                    ticker,
                    0.0,
                )
            )
            -
            float(
                previous_weights.get(
                    ticker,
                    0.0,
                )
            )
        )


        absolute_delta = abs(
            delta
        )


        turnover += (
            absolute_delta
        )


        if absolute_delta <= 0:

            continue


        scale = v9b3_impact_scale(
            ticker,
            signal_date,
        )


        if (
            not np.isfinite(
                scale
            )
            or
            scale < 0
        ):

            raise RuntimeError(
                "Missing causal impact state for "
                f"{ticker} at "
                f"{pd.Timestamp(signal_date).date()}."
            )


        impact_cost += (
            scale
            *
            absolute_delta ** 1.5
        )


    base_cost = (
        float(
            V9_BASE_TCA_RATE
        )
        *
        turnover
    )


    total_cost = (
        base_cost
        +
        impact_cost
    )


    if (
        not np.isfinite(
            total_cost
        )
        or
        total_cost < 0
        or
        total_cost >= 1
    ):

        raise RuntimeError(
            "Invalid execution cost."
        )


    return (
        turnover,
        base_cost,
        impact_cost,
        total_cost,
    )


# ==============================================================================
# 15. ACTUAL GROSS HOLDING RETURN HELPER
# ==============================================================================

def v9b3_gross_multiplier(
    target,
    start_date,
    end_date,
):

    if start_date == end_date:

        return 1.0


    multiplier = 0.0


    for ticker, weight in (
        target.items()
    ):

        start_price = v9b3_exact_price(
            ticker,
            start_date,
        )


        end_price = v9b3_exact_price(
            ticker,
            end_date,
        )


        if (
            not np.isfinite(
                start_price
            )
            or
            not np.isfinite(
                end_price
            )
        ):

            raise RuntimeError(
                "Missing price during realized V9 portfolio return: "
                f"{ticker}"
            )


        multiplier += (
            float(weight)
            *
            end_price
            /
            start_price
        )


    return float(
        multiplier
    )


# ==============================================================================
# 16. EXPERT COST ENGINE
# ==============================================================================

def v9b3_expert_execution_cost_vector(
    event_index,
):

    signal_date = pd.Timestamp(
        V9_B3_SIGNAL_DATES[
            event_index
        ]
    )


    current_execution = pd.Timestamp(
        V9_B3_EXECUTION_DATES[
            event_index
        ]
    )


    current_stock = (
        V9_B3_STOCK_TARGETS[
            current_execution
        ]
    )


    # ==========================================================================
    # FIRST EVENT — ALL EXPERTS ENTER FROM CASH
    # ==========================================================================

    if event_index == 0:

        delta_tqqq = (
            V9_EXPERT_TQQQ
        )


        delta_qqq = (
            V9_EXPERT_QQQ
        )


        turnover = np.ones(
            V9_EXPERT_COUNT,
            dtype=float,
        )


        scale_tqqq = v9b3_impact_scale(
            "TQQQ",
            signal_date,
        )


        scale_qqq = v9b3_impact_scale(
            "QQQ",
            signal_date,
        )


        impact = (
            scale_tqqq
            *
            np.abs(
                delta_tqqq
            ) ** 1.5
            +
            scale_qqq
            *
            np.abs(
                delta_qqq
            ) ** 1.5
        )


        alpha_constant = 0.0


        for ticker, stock_weight in (
            current_stock.items()
        ):

            scale = v9b3_impact_scale(
                ticker,
                signal_date,
            )


            alpha_constant += (
                scale
                *
                float(
                    stock_weight
                ) ** 1.5
            )


        impact += (
            alpha_constant
            *
            V9_EXPERT_ALPHA ** 1.5
        )


        base = (
            float(
                V9_BASE_TCA_RATE
            )
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


    # ==========================================================================
    # LATER EVENTS
    # ==========================================================================

    previous_execution = pd.Timestamp(
        V9_B3_EXECUTION_DATES[
            event_index - 1
        ]
    )


    previous_component = (
        V9_B3_COMPONENT_RETURNS
        .iloc[
            event_index - 1
        ]
    )


    previous_tqqq_growth = float(
        previous_component[
            "TQQQ_Gross_Multiplier"
        ]
    )


    previous_qqq_growth = float(
        previous_component[
            "QQQ_Gross_Multiplier"
        ]
    )


    previous_alpha_growth = float(
        previous_component[
            "Alpha_Gross_Multiplier"
        ]
    )


    expert_previous_gross = (
        V9_EXPERT_TQQQ
        *
        previous_tqqq_growth
        +
        V9_EXPERT_QQQ
        *
        previous_qqq_growth
        +
        V9_EXPERT_ALPHA
        *
        previous_alpha_growth
    )


    if (
        ~np.isfinite(
            expert_previous_gross
        )
    ).any():

        raise RuntimeError(
            "Non-finite expert drift denominator."
        )


    if (
        expert_previous_gross
        <=
        0
    ).any():

        raise RuntimeError(
            "Non-positive expert drift denominator."
        )


    drift_tqqq = (
        V9_EXPERT_TQQQ
        *
        previous_tqqq_growth
        /
        expert_previous_gross
    )


    drift_qqq = (
        V9_EXPERT_QQQ
        *
        previous_qqq_growth
        /
        expert_previous_gross
    )


    delta_tqqq = (
        V9_EXPERT_TQQQ
        -
        drift_tqqq
    )


    delta_qqq = (
        V9_EXPERT_QQQ
        -
        drift_qqq
    )


    turnover = (
        np.abs(
            delta_tqqq
        )
        +
        np.abs(
            delta_qqq
        )
    )


    scale_tqqq = v9b3_impact_scale(
        "TQQQ",
        signal_date,
    )


    scale_qqq = v9b3_impact_scale(
        "QQQ",
        signal_date,
    )


    impact = (
        scale_tqqq
        *
        np.abs(
            delta_tqqq
        ) ** 1.5
        +
        scale_qqq
        *
        np.abs(
            delta_qqq
        ) ** 1.5
    )


    previous_alpha_end_values = (
        V9_B3_ALPHA_END_VALUES[
            event_index - 1
        ]
    )


    alpha_names = sorted(
        set(
            current_stock
        )
        |
        set(
            previous_alpha_end_values
        )
    )


    alpha_weight_column = (
        V9_EXPERT_ALPHA[
            :,
            None
        ]
    )


    denominator_column = (
        expert_previous_gross[
            :,
            None
        ]
    )


    current_coefficients = np.array(
        [
            current_stock.get(
                ticker,
                0.0,
            )
            for ticker in alpha_names
        ],
        dtype=float,
    )


    previous_end_coefficients = np.array(
        [
            previous_alpha_end_values.get(
                ticker,
                0.0,
            )
            for ticker in alpha_names
        ],
        dtype=float,
    )


    alpha_delta = (
        alpha_weight_column
        *
        (
            current_coefficients[
                None,
                :
            ]
            -
            previous_end_coefficients[
                None,
                :
            ]
            /
            denominator_column
        )
    )


    turnover += (
        np.abs(
            alpha_delta
        )
        .sum(
            axis=1
        )
    )


    alpha_scales = np.array(
        [
            v9b3_impact_scale(
                ticker,
                signal_date,
            )
            for ticker
            in alpha_names
        ],
        dtype=float,
    )


    if (
        ~np.isfinite(
            alpha_scales
        )
    ).any():

        bad_names = [
            ticker
            for ticker, scale
            in zip(
                alpha_names,
                alpha_scales,
            )
            if not np.isfinite(
                scale
            )
        ]


        raise RuntimeError(
            "Missing expert alpha impact state: "
            f"{bad_names[:20]}"
        )


    impact += (
        (
            np.abs(
                alpha_delta
            ) ** 1.5
        )
        *
        alpha_scales[
            None,
            :
        ]
    ).sum(
        axis=1
    )


    base = (
        float(
            V9_BASE_TCA_RATE
        )
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
# 17. UNIVERSAL WALK-FORWARD
# ==============================================================================

V9_EXPERT_LOG_WEALTH = np.zeros(
    V9_EXPERT_COUNT,
    dtype=float,
)


V9_UNIVERSAL_WEALTH = 1.0


V9_UNIVERSAL_PREVIOUS_TARGET = {}

V9_UNIVERSAL_PREVIOUS_EXECUTION = None


V9_UNIVERSAL_ROWS = []


for event_index in range(
    len(
        V9_B3_COMPONENT_RETURNS
    )
):

    component = (
        V9_B3_COMPONENT_RETURNS
        .iloc[
            event_index
        ]
    )


    signal_date = pd.Timestamp(
        component[
            "Signal_Date"
        ]
    )


    execution_date = pd.Timestamp(
        component[
            "Execution_Date"
        ]
    )


    exit_date = pd.Timestamp(
        component[
            "Exit_Date"
        ]
    )


    # ==========================================================================
    # PRE-EVENT POSTERIOR
    # ==========================================================================

    posterior = (
        v9b3_posterior_probabilities(
            V9_EXPERT_LOG_WEALTH
        )
    )


    posterior_mean = (
        posterior
        @
        V9_EXPERT_GRID
    )


    posterior_tqqq = float(
        posterior_mean[
            0
        ]
    )


    posterior_qqq = float(
        posterior_mean[
            1
        ]
    )


    posterior_alpha = float(
        posterior_mean[
            2
        ]
    )


    if abs(
        posterior_tqqq
        +
        posterior_qqq
        +
        posterior_alpha
        -
        1.0
    ) > 1e-10:

        raise RuntimeError(
            "Universal posterior allocation does not sum to one."
        )


    # ==========================================================================
    # BUILD ACTUAL UNDERLYING TARGET
    # ==========================================================================

    current_stock_target = (
        V9_B3_STOCK_TARGETS[
            execution_date
        ]
    )


    actual_target = (
        v9b3_underlying_target(
            sleeve_weights=posterior_mean,
            stock_target=current_stock_target,
        )
    )


    # ==========================================================================
    # DRIFT PREVIOUS ACTUAL HOLDINGS
    # ==========================================================================

    if (
        V9_UNIVERSAL_PREVIOUS_EXECUTION
        is None
    ):

        drifted_previous = {}

    else:

        drifted_previous = (
            v9b3_drift_underlying(
                target=V9_UNIVERSAL_PREVIOUS_TARGET,
                start_date=(
                    V9_UNIVERSAL_PREVIOUS_EXECUTION
                ),
                end_date=execution_date,
            )
        )


    # ==========================================================================
    # EXACT ACTUAL PORTFOLIO EXECUTION COST
    # ==========================================================================

    (
        actual_turnover,
        actual_base_cost,
        actual_impact_cost,
        actual_total_cost,
    ) = v9b3_execution_cost(
        previous_weights=drifted_previous,
        target_weights=actual_target,
        signal_date=signal_date,
    )


    # ==========================================================================
    # REALIZED ACTUAL PORTFOLIO RETURN
    # ==========================================================================

    actual_gross_multiplier = (
        v9b3_gross_multiplier(
            target=actual_target,
            start_date=execution_date,
            end_date=exit_date,
        )
    )


    actual_net_multiplier = (
        (
            1.0
            -
            actual_total_cost
        )
        *
        actual_gross_multiplier
    )


    if (
        not np.isfinite(
            actual_net_multiplier
        )
        or
        actual_net_multiplier <= 0
    ):

        raise RuntimeError(
            "Invalid V9 universal net multiplier."
        )


    V9_UNIVERSAL_WEALTH *= (
        actual_net_multiplier
    )


    # ==========================================================================
    # EXPERT CURRENT GROSS RETURNS
    # ==========================================================================

    tqqq_gross = float(
        component[
            "TQQQ_Gross_Multiplier"
        ]
    )


    qqq_gross = float(
        component[
            "QQQ_Gross_Multiplier"
        ]
    )


    alpha_gross = float(
        component[
            "Alpha_Gross_Multiplier"
        ]
    )


    expert_gross = (
        V9_EXPERT_TQQQ
        *
        tqqq_gross
        +
        V9_EXPERT_QQQ
        *
        qqq_gross
        +
        V9_EXPERT_ALPHA
        *
        alpha_gross
    )


    # ==========================================================================
    # EXPERT CURRENT EXECUTION COSTS
    # ==========================================================================

    (
        expert_turnover,
        expert_base_cost,
        expert_impact_cost,
        expert_total_cost,
    ) = (
        v9b3_expert_execution_cost_vector(
            event_index
        )
    )


    if (
        expert_total_cost
        >=
        1.0
    ).any():

        raise RuntimeError(
            "At least one universal expert has execution cost >= 100%."
        )


    expert_net_multiplier = (
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
            expert_net_multiplier
        )
    ).any():

        raise RuntimeError(
            "Non-finite expert net multiplier."
        )


    if (
        expert_net_multiplier
        <=
        0
    ).any():

        raise RuntimeError(
            "Non-positive expert net multiplier."
        )


    # ==========================================================================
    # POST-EVENT EXPERT UPDATE
    # ==========================================================================

    V9_EXPERT_LOG_WEALTH += np.log(
        expert_net_multiplier
    )


    post_posterior = (
        v9b3_posterior_probabilities(
            V9_EXPERT_LOG_WEALTH
        )
    )


    post_mean = (
        post_posterior
        @
        V9_EXPERT_GRID
    )


    effective_experts = float(
        1.0
        /
        np.sum(
            post_posterior ** 2
        )
    )


    max_expert_probability = float(
        np.max(
            post_posterior
        )
    )


    V9_UNIVERSAL_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Pre_TQQQ_Weight":
                posterior_tqqq,

            "Pre_QQQ_Weight":
                posterior_qqq,

            "Pre_Alpha_Weight":
                posterior_alpha,

            "Turnover":
                actual_turnover,

            "Base_TCA_bps":
                10000.0
                *
                actual_base_cost,

            "Impact_Cost_bps":
                10000.0
                *
                actual_impact_cost,

            "Total_Cost_bps":
                10000.0
                *
                actual_total_cost,

            "Gross_Return":
                actual_gross_multiplier
                -
                1.0,

            "Net_Return":
                actual_net_multiplier
                -
                1.0,

            "Wealth":
                V9_UNIVERSAL_WEALTH,

            "Post_TQQQ_Weight":
                float(
                    post_mean[
                        0
                    ]
                ),

            "Post_QQQ_Weight":
                float(
                    post_mean[
                        1
                    ]
                ),

            "Post_Alpha_Weight":
                float(
                    post_mean[
                        2
                    ]
                ),

            "Effective_Experts":
                effective_experts,

            "Largest_Expert_Posterior_Pct":
                100.0
                *
                max_expert_probability,
        }
    )


    V9_UNIVERSAL_PREVIOUS_TARGET = dict(
        actual_target
    )


    V9_UNIVERSAL_PREVIOUS_EXECUTION = (
        execution_date
    )


V9_UNIVERSAL_PATH = pd.DataFrame(
    V9_UNIVERSAL_ROWS
)


# ==============================================================================
# 18. FINAL EXPERT WEALTH
# ==============================================================================

V9_EXPERT_FINAL_WEALTH = np.exp(
    V9_EXPERT_LOG_WEALTH
)


V9_FINAL_POSTERIOR = (
    v9b3_posterior_probabilities(
        V9_EXPERT_LOG_WEALTH
    )
)


V9_FINAL_POSTERIOR_MEAN = (
    V9_FINAL_POSTERIOR
    @
    V9_EXPERT_GRID
)


V9_BEST_EXPERT_INDEX = int(
    np.argmax(
        V9_EXPERT_FINAL_WEALTH
    )
)


V9_BEST_EXPERT_WEIGHTS = (
    V9_EXPERT_GRID[
        V9_BEST_EXPERT_INDEX
    ]
)


V9_BEST_EXPERT_WEALTH = float(
    V9_EXPERT_FINAL_WEALTH[
        V9_BEST_EXPERT_INDEX
    ]
)


# ==============================================================================
# 19. SAME-CALENDAR BUY-AND-HOLD BENCHMARKS
# ==============================================================================

V9_B3_FIRST_SIGNAL = pd.Timestamp(
    V9_B3_SIGNAL_DATES[
        0
    ]
)


V9_B3_FIRST_EXECUTION = pd.Timestamp(
    V9_B3_EXECUTION_DATES[
        0
    ]
)


V9_B3_LAST_EXECUTION = pd.Timestamp(
    V9_B3_EXECUTION_DATES[
        -1
    ]
)


def v9b3_buy_hold_wealth(
    ticker,
):

    ticker = str(
        ticker
    ).upper()


    first_price = v9b3_exact_price(
        ticker,
        V9_B3_FIRST_EXECUTION,
    )


    last_price = v9b3_exact_price(
        ticker,
        V9_B3_LAST_EXECUTION,
    )


    scale = v9b3_impact_scale(
        ticker,
        V9_B3_FIRST_SIGNAL,
    )


    initial_cost = (
        float(
            V9_BASE_TCA_RATE
        )
        +
        scale
    )


    wealth = (
        (
            1.0
            -
            initial_cost
        )
        *
        last_price
        /
        first_price
    )


    base_only_wealth = (
        (
            1.0
            -
            float(
                V9_BASE_TCA_RATE
            )
        )
        *
        last_price
        /
        first_price
    )


    return (
        float(
            wealth
        ),
        float(
            base_only_wealth
        ),
        float(
            initial_cost
        ),
    )


(
    V9_TQQQ_FULL_COST_WEALTH,
    V9_TQQQ_BASE_ONLY_WEALTH,
    V9_TQQQ_INITIAL_COST,
) = v9b3_buy_hold_wealth(
    "TQQQ"
)


(
    V9_QQQ_FULL_COST_WEALTH,
    V9_QQQ_BASE_ONLY_WEALTH,
    V9_QQQ_INITIAL_COST,
) = v9b3_buy_hold_wealth(
    "QQQ"
)


# ==============================================================================
# 20. FINAL V9 ECONOMICS
# ==============================================================================

V9_FINAL_WEALTH = float(
    V9_UNIVERSAL_PATH[
        "Wealth"
    ].iloc[
        -1
    ]
)


V9_FINAL_RETURN_PCT = (
    100.0
    *
    (
        V9_FINAL_WEALTH
        -
        1.0
    )
)


V9_TQQQ_RETURN_PCT = (
    100.0
    *
    (
        V9_TQQQ_FULL_COST_WEALTH
        -
        1.0
    )
)


V9_QQQ_RETURN_PCT = (
    100.0
    *
    (
        V9_QQQ_FULL_COST_WEALTH
        -
        1.0
    )
)


V9_MINUS_TQQQ_PP = (
    100.0
    *
    (
        V9_FINAL_WEALTH
        -
        V9_TQQQ_FULL_COST_WEALTH
    )
)


V9_RELATIVE_WEALTH_VS_TQQQ = (
    V9_FINAL_WEALTH
    /
    V9_TQQQ_FULL_COST_WEALTH
)


V9_RELATIVE_GAIN_VS_TQQQ_PCT = (
    100.0
    *
    (
        V9_RELATIVE_WEALTH_VS_TQQQ
        -
        1.0
    )
)


# ==============================================================================
# 21. POSTERIOR / EXECUTION DIAGNOSTICS
# ==============================================================================

V9_BLOCK3_TOTAL_TURNOVER = float(
    V9_UNIVERSAL_PATH[
        "Turnover"
    ].sum()
)


V9_BLOCK3_MEAN_TURNOVER = float(
    V9_UNIVERSAL_PATH[
        "Turnover"
    ].mean()
)


V9_BLOCK3_MEAN_COST_BPS = float(
    V9_UNIVERSAL_PATH[
        "Total_Cost_bps"
    ].mean()
)


V9_BLOCK3_MEDIAN_COST_BPS = float(
    V9_UNIVERSAL_PATH[
        "Total_Cost_bps"
    ].median()
)


V9_BLOCK3_MEAN_TQQQ_WEIGHT = float(
    100.0
    *
    V9_UNIVERSAL_PATH[
        "Pre_TQQQ_Weight"
    ].mean()
)


V9_BLOCK3_MEAN_QQQ_WEIGHT = float(
    100.0
    *
    V9_UNIVERSAL_PATH[
        "Pre_QQQ_Weight"
    ].mean()
)


V9_BLOCK3_MEAN_ALPHA_WEIGHT = float(
    100.0
    *
    V9_UNIVERSAL_PATH[
        "Pre_Alpha_Weight"
    ].mean()
)


# ==============================================================================
# 22. FINAL RESULT TABLE
# ==============================================================================

V9_BLOCK3_RESULT_TABLE = pd.DataFrame(
    {
        "Metric": [

            "Research events",

            "Universal experts",

            "V9 final wealth",

            "V9 net return pct",

            "TQQQ BH full-cost wealth",

            "TQQQ BH full-cost return pct",

            "QQQ BH full-cost wealth",

            "QQQ BH full-cost return pct",

            "V9 minus TQQQ pp",

            "V9 / TQQQ relative wealth",

            "V9 relative gain vs TQQQ pct",

            "Mean TQQQ allocation pct",

            "Mean QQQ allocation pct",

            "Mean Alpha allocation pct",

            "Final posterior TQQQ pct",

            "Final posterior QQQ pct",

            "Final posterior Alpha pct",

            "Total turnover",

            "Mean turnover",

            "Mean execution cost bps",

            "Median execution cost bps",

            "Best constant expert wealth — hindsight only",

            "Best constant TQQQ pct — hindsight only",

            "Best constant QQQ pct — hindsight only",

            "Best constant Alpha pct — hindsight only",

            "Impact-state causal fallback count",
        ],

        "Value": [

            len(
                V9_UNIVERSAL_PATH
            ),

            V9_EXPERT_COUNT,

            V9_FINAL_WEALTH,

            V9_FINAL_RETURN_PCT,

            V9_TQQQ_FULL_COST_WEALTH,

            V9_TQQQ_RETURN_PCT,

            V9_QQQ_FULL_COST_WEALTH,

            V9_QQQ_RETURN_PCT,

            V9_MINUS_TQQQ_PP,

            V9_RELATIVE_WEALTH_VS_TQQQ,

            V9_RELATIVE_GAIN_VS_TQQQ_PCT,

            V9_BLOCK3_MEAN_TQQQ_WEIGHT,

            V9_BLOCK3_MEAN_QQQ_WEIGHT,

            V9_BLOCK3_MEAN_ALPHA_WEIGHT,

            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                0
            ],

            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                1
            ],

            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                2
            ],

            V9_BLOCK3_TOTAL_TURNOVER,

            V9_BLOCK3_MEAN_TURNOVER,

            V9_BLOCK3_MEAN_COST_BPS,

            V9_BLOCK3_MEDIAN_COST_BPS,

            V9_BEST_EXPERT_WEALTH,

            100.0
            *
            V9_BEST_EXPERT_WEIGHTS[
                0
            ],

            100.0
            *
            V9_BEST_EXPERT_WEIGHTS[
                1
            ],

            100.0
            *
            V9_BEST_EXPERT_WEIGHTS[
                2
            ],

            V9_B3_STATE_FALLBACK_COUNT,
        ],
    }
)


# ==============================================================================
# 23. RESEARCH VERDICT
# ==============================================================================

V9_BEATS_TQQQ = bool(
    V9_FINAL_WEALTH
    >
    V9_TQQQ_FULL_COST_WEALTH
)


V9_BEATS_QQQ = bool(
    V9_FINAL_WEALTH
    >
    V9_QQQ_FULL_COST_WEALTH
)


V9_RESEARCH_VERDICT = (
    "PASS"
    if V9_BEATS_TQQQ
    else
    "FAIL"
)


# ==============================================================================
# 24. FINAL RESEARCH FINGERPRINT
# ==============================================================================

V9_BLOCK3_RESULT_PAYLOAD = {

    "spec_fingerprint":
        V9_BLOCK3_SPEC_FINGERPRINT,

    "block2b_fingerprint":
        V9_BLOCK2B_RESEARCH_FINGERPRINT,

    "expert_count":
        V9_EXPERT_COUNT,

    "final_wealth":
        V9_FINAL_WEALTH,

    "tqqq_full_cost_wealth":
        V9_TQQQ_FULL_COST_WEALTH,

    "qqq_full_cost_wealth":
        V9_QQQ_FULL_COST_WEALTH,

    "relative_wealth_vs_tqqq":
        V9_RELATIVE_WEALTH_VS_TQQQ,

    "final_posterior_mean":
        V9_FINAL_POSTERIOR_MEAN.tolist(),

    "best_constant_expert_wealth_hindsight_only":
        V9_BEST_EXPERT_WEALTH,

    "best_constant_expert_weights_hindsight_only":
        V9_BEST_EXPERT_WEIGHTS.tolist(),

    "verdict":
        V9_RESEARCH_VERDICT,
}


V9_BLOCK3_RESEARCH_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            V9_BLOCK3_RESULT_PAYLOAD,
            sort_keys=True,
            default=str,
        )
        .encode(
            "utf-8"
        )
    )
    .hexdigest()
)


# ==============================================================================
# 25. OUTPUT — RESULT
# ==============================================================================

print(
    "\n1) V9 FINAL ECONOMIC RESULT"
)


display(
    V9_BLOCK3_RESULT_TABLE.round(
        6
    )
)


# ==============================================================================
# 26. OUTPUT — FULL UNIVERSAL PATH
# ==============================================================================

print(
    "\n2) UNIVERSAL WALK-FORWARD PATH"
)


display(
    V9_UNIVERSAL_PATH[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Exit_Date",

            "Pre_TQQQ_Weight",
            "Pre_QQQ_Weight",
            "Pre_Alpha_Weight",

            "Turnover",

            "Base_TCA_bps",
            "Impact_Cost_bps",
            "Total_Cost_bps",

            "Gross_Return",
            "Net_Return",

            "Wealth",

            "Post_TQQQ_Weight",
            "Post_QQQ_Weight",
            "Post_Alpha_Weight",

            "Effective_Experts",
            "Largest_Expert_Posterior_Pct",
        ]
    ]
    .round(
        6
    )
)


# ==============================================================================
# 27. OUTPUT — FINAL POSTERIOR
# ==============================================================================

print(
    "\n3) FINAL CAUSAL POSTERIOR MEAN"
)


V9_FINAL_POSTERIOR_TABLE = pd.DataFrame(
    {
        "Sleeve": [
            "TQQQ",
            "QQQ",
            "V9_ALPHA",
        ],

        "Weight_Pct": [
            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                0
            ],

            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                1
            ],

            100.0
            *
            V9_FINAL_POSTERIOR_MEAN[
                2
            ],
        ],
    }
)


display(
    V9_FINAL_POSTERIOR_TABLE.round(
        6
    )
)


# ==============================================================================
# 28. OUTPUT — HINDSIGHT CONSTANT MIX
# ==============================================================================

print(
    "\n4) BEST CONSTANT MIX — HINDSIGHT DIAGNOSTIC ONLY"
)


V9_BEST_CONSTANT_TABLE = pd.DataFrame(
    {
        "Sleeve": [
            "TQQQ",
            "QQQ",
            "V9_ALPHA",
        ],

        "Weight_Pct": (
            100.0
            *
            V9_BEST_EXPERT_WEIGHTS
        ),
    }
)


display(
    V9_BEST_CONSTANT_TABLE.round(
        6
    )
)


print(
    "Best constant wealth:",
    f"{V9_BEST_EXPERT_WEALTH:.6f}",
)


print(
    "\nTHIS CONSTANT MIX IS EX-POST AND MUST NEVER "
    "BE USED AS A V9 TRADING PARAMETER."
)


# ==============================================================================
# 29. OUTPUT — BENCHMARK ACCOUNTING CHECK
# ==============================================================================

print(
    "\n5) BENCHMARK EXECUTION-COST ACCOUNTING"
)


V9_BENCHMARK_COST_TABLE = pd.DataFrame(
    {
        "Benchmark": [
            "TQQQ",
            "QQQ",
        ],

        "Full_Cost_Wealth": [
            V9_TQQQ_FULL_COST_WEALTH,
            V9_QQQ_FULL_COST_WEALTH,
        ],

        "Base_2bps_Only_Wealth": [
            V9_TQQQ_BASE_ONLY_WEALTH,
            V9_QQQ_BASE_ONLY_WEALTH,
        ],

        "Initial_Full_Cost_bps": [
            10000.0
            *
            V9_TQQQ_INITIAL_COST,

            10000.0
            *
            V9_QQQ_INITIAL_COST,
        ],
    }
)


display(
    V9_BENCHMARK_COST_TABLE.round(
        6
    )
)


# ==============================================================================
# 30. FINAL STATUS
# ==============================================================================

print(
    "\n6) V9 BLOCK 3 RESEARCH FINGERPRINT"
)

print(
    V9_BLOCK3_RESEARCH_FINGERPRINT
)


print("\nRESEARCH VERDICT:")
print(
    "V9 beats TQQQ :",
    V9_BEATS_TQQQ,
)

print(
    "V9 beats QQQ  :",
    V9_BEATS_QQQ,
)

print(
    "V9 result     :",
    V9_RESEARCH_VERDICT,
)


print("\nINTEGRITY:")
print("[+] No HGB model was fitted.")
print("[+] Block 2A predictions were not changed.")
print("[+] Block 2B stock-sleeve targets were not changed.")
print("[+] No stock cap was introduced.")
print("[+] No minimum position size was introduced.")
print("[+] No Top-K rule was introduced.")
print("[+] No horizon was removed after observing performance.")
print("[+] No cash allocation.")
print("[+] No leverage above 100%.")
print("[+] Universal allocation uses only prior completed events.")
print("[+] Transaction costs are computed at underlying asset level.")
print("[+] Alpha-sleeve costs are not double-counted.")
print("[+] TQQQ and QQQ receive consistent execution-cost treatment.")
print("[+] Hindsight best constant mix is diagnostic only.")

print(
    "\nFINAL RULE:"
)

print(
    "DO NOT MODIFY V9 AFTER THIS RESULT."
)

print(
    "If V9 beats TQQQ, freeze it as a research challenger."
)

print(
    "If V9 does not beat TQQQ, reject V9 as designed."
)

print("=" * 136)
restored_register('V9', V9_FINAL_WEALTH, V9_UNIVERSAL_PATH, 'Wealth', 'Close / original linear + impact costs', 'Historically rejected')
