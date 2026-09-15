# MODULE 32 — V10 PROBABILITY SLEEVE AND ALLOCATOR
# Run in the same notebook, in module order.

# ==============================================================================
# V10 — BLOCK 3
# FROZEN PROBABILITY-EDGE STOCK SLEEVE
# +
# CAUSAL TQQQ / ALPHA UNIVERSAL WEALTH ALLOCATOR
# +
# EXACT DAILY NAV / STRICT MULTI-WINDOW ACCEPTANCE TEST
# ==============================================================================
#
# THIS IS THE ONE-SHOT V10 ECONOMIC TEST.
#
# NO MODEL IS FIT HERE.
# NO V10 PARAMETER IS CHANGED HERE.
#
#
# FROZEN STOCK-SLEEVE RULE
# ------------------------
#
# For stock i:
#
#       p_i = median of seven HGB probabilities
#
#       edge_i = max(p_i - 0.50, 0)
#
# If at least one positive edge exists:
#
#       stock_weight_i = edge_i / sum(edge)
#
# Otherwise:
#
#       satellite unavailable
#       portfolio = 100% TQQQ
#
#
# THERE IS NO:
#
#       minimum stock weight
#       maximum stock weight
#       Top-K
#       percentile filter
#       sector cap
#       risk cap
#       strategic cash
#       leverage above 100%
#
#
# UNIVERSAL ALLOCATOR
# -------------------
#
# 1001 constant-mix experts:
#
#       w_alpha in [0, 1]
#       w_TQQQ  = 1 - w_alpha
#
# Uniform prior.
#
# Actual allocation at event t =
# PRE-EVENT wealth-weighted posterior mean.
#
# Posterior is updated only AFTER event t is completed.
#
#
# EXECUTION COST
# --------------
#
# Computed at UNDERLYING ASSET level:
#
#       base linear TCA
#       +
#       sigma60 * sqrt(AUM / ADV60) * |delta_weight|^(3/2)
#
# The alpha sleeve is NOT charged separately and then charged again.
#
#
# DAILY NAV
# ---------
#
# Exact event-end wealth is reconstructed into a daily NAV.
#
# At rebalance dates:
#
#       1. old portfolio earns return through current close
#       2. rebalance occurs at current close
#       3. transaction cost is charged
#       4. reported close NAV is POST-TRADE wealth
#
#
# FINAL ACCEPTANCE CONTRACT
# -------------------------
#
# V10 PASS requires:
#
#       V10 > TQQQ over FULL research history
#
# AND
#
#       V10 > TQQQ over every predeclared trailing window:
#
#           1D
#           1W
#           1M
#           3M
#           6M
#           9M
#           12M
#
# No post-result repair is allowed.
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

V10_B3_REQUIRED = [
    "V10_CLASSIFIER_PREDICTIONS",
    "V10_PREDICTIONS_HASH",
    "V10_BLOCK2_RESEARCH_FINGERPRINT",
    "V10_RESEARCH_CONTRACT_FINGERPRINT",
    "V10_INFRA_DATA_HASH",

    "V10_TARGET_HORIZONS",
    "V10_ACCEPTANCE_WINDOWS",

    "V10_LIFECYCLE_PANEL",

    "V10_BASE_TCA_RATE",
    "V10_IMPACT_COEFFICIENT",
    "V10_REFERENCE_AUM_USD",

    "V10_RESEARCH_BACKCAST_END",
]


V10_B3_MISSING = [
    name
    for name in V10_B3_REQUIRED
    if name not in globals()
]


if V10_B3_MISSING:

    raise RuntimeError(
        "V10 Block 3 is missing required objects: "
        f"{V10_B3_MISSING}"
    )


print("=" * 140)
print("V10 — BLOCK 3")
print("FROZEN PROBABILITY-EDGE STOCK SLEEVE")
print("+ TQQQ UNIVERSAL ALLOCATOR")
print("+ EXACT DAILY NAV / STRICT ACCEPTANCE TEST")
print("=" * 140)

print("\nNO MODEL FITTING WILL OCCUR IN THIS BLOCK.")


# ==============================================================================
# 1. FROZEN BLOCK-3 SPECIFICATION
# ==============================================================================

V10_UNIVERSAL_GRID_POINTS = 1001


V10_BLOCK3_SPEC = {

    "version":
        "V10_BLOCK3",

    "research_contract_fingerprint":
        V10_RESEARCH_CONTRACT_FINGERPRINT,

    "block2_result_fingerprint":
        V10_BLOCK2_RESEARCH_FINGERPRINT,

    "prediction_hash":
        V10_PREDICTIONS_HASH,

    "infrastructure_hash":
        V10_INFRA_DATA_HASH,

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",

    "core":
        "TQQQ",

    "satellite":
        "V10_PROBABILITY_EDGE_STOCK_SLEEVE",

    "probability_input":
        "MEDIAN_OF_SEVEN_HORIZON_PROBABILITIES",

    "stock_edge_rule":
        "MAX(PROBABILITY_MINUS_0P50,0)",

    "stock_weight_rule":
        "NORMALIZED_POSITIVE_EDGE",

    "no_positive_edge_policy":
        "ONE_HUNDRED_PERCENT_TQQQ",

    "minimum_stock_weight":
        None,

    "maximum_stock_weight":
        None,

    "top_k":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "cash_allowed":
        False,

    "leverage_above_one":
        False,

    "allocator":
        "COVER_STYLE_WEALTH_POSTERIOR",

    "expert_class":
        "CONSTANT_TQQQ_ALPHA_MIX",

    "expert_alpha_interval":
        "[0,1]",

    "quadrature_points":
        V10_UNIVERSAL_GRID_POINTS,

    "prior":
        "UNIFORM",

    "actual_allocation":
        "PRE_EVENT_POSTERIOR_MEAN",

    "posterior_update":
        "AFTER_COMPLETED_EVENT_ONLY",

    "base_tca_rate":
        float(
            V10_BASE_TCA_RATE
        ),

    "impact_coefficient":
        float(
            V10_IMPACT_COEFFICIENT
        ),

    "reference_aum_usd":
        float(
            V10_REFERENCE_AUM_USD
        ),

    "cost_level":
        "UNDERLYING_ASSET",

    "terminal_rebalance_cost":
        True,

    "acceptance_windows":
        V10_ACCEPTANCE_WINDOWS,

    "post_result_tuning":
        False,
}


V10_BLOCK3_SPEC_STRING = json.dumps(
    V10_BLOCK3_SPEC,
    sort_keys=True,
    default=str,
)


V10_BLOCK3_SPEC_FINGERPRINT = hashlib.sha256(
    V10_BLOCK3_SPEC_STRING.encode(
        "utf-8"
    )
).hexdigest()


print(
    "\nV10 Block 3 specification fingerprint:"
)

print(
    V10_BLOCK3_SPEC_FINGERPRINT
)


# ==============================================================================
# 2. NORMALIZE PREDICTIONS
# ==============================================================================

V10_B3_PREDICTIONS = (
    V10_CLASSIFIER_PREDICTIONS
    .copy()
)


for column in [
    "Date",
    "Execution_Date",
]:

    V10_B3_PREDICTIONS[
        column
    ] = (
        pd.to_datetime(
            V10_B3_PREDICTIONS[
                column
            ],
            errors="coerce",
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


V10_B3_PREDICTIONS[
    "Ticker"
] = (
    V10_B3_PREDICTIONS[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V10_B3_PREDICTIONS = (
    V10_B3_PREDICTIONS
    .dropna(
        subset=[
            "Date",
            "Execution_Date",
            "Ticker",
            "Composite_Prob_Beat_TQQQ",
        ]
    )
    .drop_duplicates(
        [
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


if (
    V10_B3_PREDICTIONS[
        "Date"
    ]
    .nunique()
    !=
    34
):

    raise RuntimeError(
        "V10 Block 3 expected 34 prediction dates."
    )


prob_values = (
    V10_B3_PREDICTIONS[
        "Composite_Prob_Beat_TQQQ"
    ]
    .to_numpy(
        dtype=float
    )
)


if not np.isfinite(
    prob_values
).all():

    raise RuntimeError(
        "Composite probability contains non-finite values."
    )


if (
    prob_values < 0
).any() or (
    prob_values > 1
).any():

    raise RuntimeError(
        "Composite probabilities are outside [0,1]."
    )


# ==============================================================================
# 3. BUILD FROZEN PROBABILITY-EDGE STOCK SLEEVES
# ==============================================================================

V10_STOCK_SLEEVE_TARGETS = {}

V10_STOCK_SLEEVE_ROWS = []


for event_number, (
    signal_date,
    section,
) in enumerate(
    V10_B3_PREDICTIONS.groupby(
        "Date",
        sort=True,
    ),
    start=1,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    execution_dates = (
        section[
            "Execution_Date"
        ]
        .drop_duplicates()
        .tolist()
    )


    if len(
        execution_dates
    ) != 1:

        raise RuntimeError(
            "A V10 signal date maps to multiple execution dates: "
            f"{signal_date.date()}"
        )


    execution_date = pd.Timestamp(
        execution_dates[
            0
        ]
    ).normalize()


    probabilities = (
        section[
            "Composite_Prob_Beat_TQQQ"
        ]
        .to_numpy(
            dtype=float
        )
    )


    edges = np.maximum(
        probabilities
        -
        0.50,
        0.0,
    )


    positive_mask = (
        edges > 0
    )


    positive_count = int(
        positive_mask.sum()
    )


    edge_sum = float(
        edges.sum()
    )


    if edge_sum > 0:

        selected = (
            section.loc[
                positive_mask,
                [
                    "Ticker",
                    "Composite_Prob_Beat_TQQQ",
                ],
            ]
            .copy()
        )


        selected[
            "Edge"
        ] = edges[
            positive_mask
        ]


        selected[
            "Weight"
        ] = (
            selected[
                "Edge"
            ]
            /
            edge_sum
        )


        target = {
            str(row.Ticker):
                float(
                    row.Weight
                )

            for row
            in selected.itertuples(
                index=False
            )
        }


        satellite_available = True


        target_weights = np.asarray(
            list(
                target.values()
            ),
            dtype=float,
        )


        effective_n = float(
            1.0
            /
            np.sum(
                target_weights ** 2
            )
        )


        max_name_weight = float(
            np.max(
                target_weights
            )
        )


        largest_position = max(
            target,
            key=target.get,
        )


    else:

        target = {}

        satellite_available = False

        effective_n = np.nan

        max_name_weight = 0.0

        largest_position = None


    V10_STOCK_SLEEVE_TARGETS[
        execution_date
    ] = dict(
        target
    )


    V10_STOCK_SLEEVE_ROWS.append(
        {
            "Event":
                event_number,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Candidate_Stocks":
                int(
                    len(
                        section
                    )
                ),

            "Positive_Edge_Stocks":
                positive_count,

            "Positive_Edge_Pct":
                100.0
                *
                positive_count
                /
                len(
                    section
                ),

            "Satellite_Available":
                satellite_available,

            "Mean_Composite_Probability":
                float(
                    probabilities.mean()
                ),

            "Median_Composite_Probability":
                float(
                    np.median(
                        probabilities
                    )
                ),

            "Maximum_Composite_Probability":
                float(
                    probabilities.max()
                ),

            "Effective_N":
                effective_n,

            "Max_Stock_Weight_Pct":
                100.0
                *
                max_name_weight,

            "Largest_Stock_Position":
                largest_position,

            "Weights":
                dict(
                    target
                ),
        }
    )


V10_STOCK_SLEEVE_DECISIONS = (
    pd.DataFrame(
        V10_STOCK_SLEEVE_ROWS
    )
    .sort_values(
        "Execution_Date"
    )
    .reset_index(
        drop=True
    )
)


if len(
    V10_STOCK_SLEEVE_DECISIONS
) != 34:

    raise RuntimeError(
        "V10 stock sleeve did not produce 34 decisions."
    )


# ==============================================================================
# 4. NORMALIZE LIFECYCLE PANEL
# ==============================================================================

V10_B3_LIFECYCLE = (
    V10_LIFECYCLE_PANEL
    .copy()
)


required_lifecycle_columns = [
    "Ticker",
    "Date",
    "Adj_Close",
    "Median_Dollar_Volume_60",
    "V9_Realized_Vol_60",
]


missing_lifecycle_columns = [
    column
    for column
    in required_lifecycle_columns
    if column
    not in V10_B3_LIFECYCLE.columns
]


if missing_lifecycle_columns:

    raise RuntimeError(
        "V10 lifecycle panel is missing required columns: "
        f"{missing_lifecycle_columns}"
    )


V10_B3_LIFECYCLE[
    "Date"
] = (
    pd.to_datetime(
        V10_B3_LIFECYCLE[
            "Date"
        ],
        errors="coerce",
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V10_B3_LIFECYCLE[
    "Ticker"
] = (
    V10_B3_LIFECYCLE[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V10_B3_LIFECYCLE = (
    V10_B3_LIFECYCLE
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
# 5. EXACT PRICE LOOKUP
# ==============================================================================

V10_B3_PRICE_LOOKUP = (
    V10_B3_LIFECYCLE[
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
    )[
        "Adj_Close"
    ]
    .sort_index()
)


def v10b3_exact_price(
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

        value = V10_B3_PRICE_LOOKUP.loc[
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
        not np.isfinite(
            value
        )
        or
        value <= 0
    ):

        return np.nan


    return value


# ==============================================================================
# 6. CAUSAL EXECUTION-STATE LOOKUP
# ==============================================================================

V10_B3_STATE_GROUPS = {}


for ticker, group in (
    V10_B3_LIFECYCLE[
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

    V10_B3_STATE_GROUPS[
        ticker
    ] = (
        group
        .set_index(
            "Date"
        )[
            [
                "Median_Dollar_Volume_60",
                "V9_Realized_Vol_60",
            ]
        ]
        .sort_index()
    )


V10_B3_IMPACT_CACHE = {}

V10_B3_STATE_FALLBACK_COUNT = 0


def v10b3_impact_scale(
    ticker,
    signal_date,
):

    global V10_B3_STATE_FALLBACK_COUNT


    ticker = str(
        ticker
    ).upper().strip()

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    key = (
        ticker,
        signal_date,
    )


    if key in V10_B3_IMPACT_CACHE:

        return V10_B3_IMPACT_CACHE[
            key
        ]


    if ticker not in V10_B3_STATE_GROUPS:

        V10_B3_IMPACT_CACHE[
            key
        ] = np.nan

        return np.nan


    history = (
        V10_B3_STATE_GROUPS[
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

            V10_B3_IMPACT_CACHE[
                key
            ] = np.nan

            return np.nan


        row = prior.iloc[-1]

        V10_B3_STATE_FALLBACK_COUNT += 1


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
        not np.isfinite(
            adv
        )
        or
        not np.isfinite(
            sigma
        )
        or
        adv <= 0
        or
        sigma < 0
    ):

        V10_B3_IMPACT_CACHE[
            key
        ] = np.nan

        return np.nan


    scale = (
        float(
            V10_IMPACT_COEFFICIENT
        )
        *
        sigma
        *
        np.sqrt(
            float(
                V10_REFERENCE_AUM_USD
            )
            /
            adv
        )
    )


    V10_B3_IMPACT_CACHE[
        key
    ] = float(
        scale
    )


    return float(
        scale
    )


# ==============================================================================
# 7. EXECUTION CALENDAR
# ==============================================================================

V10_B3_SIGNAL_DATES = (
    V10_STOCK_SLEEVE_DECISIONS[
        "Signal_Date"
    ]
    .tolist()
)


V10_B3_EXECUTION_DATES = (
    V10_STOCK_SLEEVE_DECISIONS[
        "Execution_Date"
    ]
    .tolist()
)


if any(
    V10_B3_EXECUTION_DATES[
        i
    ]
    >=
    V10_B3_EXECUTION_DATES[
        i + 1
    ]
    for i
    in range(
        len(
            V10_B3_EXECUTION_DATES
        )
        -
        1
    )
):

    raise RuntimeError(
        "V10 execution dates are not strictly increasing."
    )


# ==============================================================================
# 8. FULL PRICE / LIFECYCLE PREFLIGHT
# ==============================================================================
#
# IMPORTANT:
#
# No performance is calculated before this completes.
#
# Every stock that would actually enter the frozen stock sleeve must have:
#
#       exact entry quote
#       exact next-rebalance quote
#
# The final event requires only the terminal execution quote.
#
# ==============================================================================

V10_B3_PRICE_PREFLIGHT_ROWS = []

V10_B3_UNRESOLVED_QUOTES = []


for event_index in range(
    len(
        V10_STOCK_SLEEVE_DECISIONS
    )
):

    row = (
        V10_STOCK_SLEEVE_DECISIONS
        .iloc[
            event_index
        ]
    )


    signal_date = pd.Timestamp(
        row[
            "Signal_Date"
        ]
    )


    execution_date = pd.Timestamp(
        row[
            "Execution_Date"
        ]
    )


    if (
        event_index
        <
        len(
            V10_STOCK_SLEEVE_DECISIONS
        )
        -
        1
    ):

        next_execution_date = pd.Timestamp(
            V10_STOCK_SLEEVE_DECISIONS
            .iloc[
                event_index + 1
            ][
                "Execution_Date"
            ]
        )

    else:

        next_execution_date = execution_date


    stock_target = (
        V10_STOCK_SLEEVE_TARGETS[
            execution_date
        ]
    )


    names_to_check = set(
        stock_target.keys()
    )


    names_to_check.add(
        "TQQQ"
    )


    missing_entry = 0

    missing_exit = 0

    missing_impact = 0


    for ticker in names_to_check:

        entry_price = v10b3_exact_price(
            ticker,
            execution_date,
        )


        exit_price = v10b3_exact_price(
            ticker,
            next_execution_date,
        )


        impact_scale = v10b3_impact_scale(
            ticker,
            signal_date,
        )


        if not np.isfinite(
            entry_price
        ):

            missing_entry += 1

            V10_B3_UNRESOLVED_QUOTES.append(
                {
                    "Event":
                        event_index + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "ENTRY",

                    "Requested_Date":
                        execution_date,
                }
            )


        if not np.isfinite(
            exit_price
        ):

            missing_exit += 1

            V10_B3_UNRESOLVED_QUOTES.append(
                {
                    "Event":
                        event_index + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "NEXT_REBALANCE",

                    "Requested_Date":
                        next_execution_date,
                }
            )


        if not np.isfinite(
            impact_scale
        ):

            missing_impact += 1


    V10_B3_PRICE_PREFLIGHT_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Next_Execution_Date":
                next_execution_date,

            "Satellite_Available":
                bool(
                    row[
                        "Satellite_Available"
                    ]
                ),

            "Stock_Names":
                len(
                    stock_target
                ),

            "Missing_Entry_Quotes":
                missing_entry,

            "Missing_Next_Rebalance_Quotes":
                missing_exit,

            "Missing_Impact_States":
                missing_impact,
        }
    )


V10_B3_PRICE_PREFLIGHT = pd.DataFrame(
    V10_B3_PRICE_PREFLIGHT_ROWS
)


if (
    V10_B3_PRICE_PREFLIGHT[
        "Missing_Entry_Quotes"
    ].sum()
    !=
    0
    or
    V10_B3_PRICE_PREFLIGHT[
        "Missing_Next_Rebalance_Quotes"
    ].sum()
    !=
    0
    or
    V10_B3_PRICE_PREFLIGHT[
        "Missing_Impact_States"
    ].sum()
    !=
    0
):

    print(
        "\n[!] V10 BLOCK 3 PREFLIGHT FAILED."
    )


    display(
        V10_B3_PRICE_PREFLIGHT
    )


    if V10_B3_UNRESOLVED_QUOTES:

        print(
            "\nUNRESOLVED EXACT QUOTES:"
        )

        display(
            pd.DataFrame(
                V10_B3_UNRESOLVED_QUOTES
            )
        )


    raise RuntimeError(
        "V10 Block 3 stopped BEFORE performance calculation. "
        "Resolve lifecycle / execution-state gaps first."
    )


print(
    "\n[+] FULL V10 PRICE / LIFECYCLE / EXECUTION PREFLIGHT PASSED."
)


# ==============================================================================
# 9. PRECOMPUTE EVENT GROWTH MAPS
# ==============================================================================

V10_B3_EVENT_GROWTH = []

V10_STOCK_SLEEVE_GROSS_ROWS = []


for event_index in range(
    len(
        V10_STOCK_SLEEVE_DECISIONS
    )
):

    row = (
        V10_STOCK_SLEEVE_DECISIONS
        .iloc[
            event_index
        ]
    )


    execution_date = pd.Timestamp(
        row[
            "Execution_Date"
        ]
    )


    if (
        event_index
        <
        len(
            V10_STOCK_SLEEVE_DECISIONS
        )
        -
        1
    ):

        exit_date = pd.Timestamp(
            V10_STOCK_SLEEVE_DECISIONS
            .iloc[
                event_index + 1
            ][
                "Execution_Date"
            ]
        )

    else:

        exit_date = execution_date


    stock_target = (
        V10_STOCK_SLEEVE_TARGETS[
            execution_date
        ]
    )


    names = set(
        stock_target
    )

    names.add(
        "TQQQ"
    )


    growth_map = {}


    for ticker in names:

        start_price = v10b3_exact_price(
            ticker,
            execution_date,
        )


        end_price = v10b3_exact_price(
            ticker,
            exit_date,
        )


        growth_map[
            ticker
        ] = (
            end_price
            /
            start_price
        )


    tqqq_growth = float(
        growth_map[
            "TQQQ"
        ]
    )


    if stock_target:

        alpha_growth = float(
            sum(
                weight
                *
                growth_map[
                    ticker
                ]

                for ticker, weight
                in stock_target.items()
            )
        )

    else:

        alpha_growth = tqqq_growth


    V10_B3_EVENT_GROWTH.append(
        growth_map
    )


    V10_STOCK_SLEEVE_GROSS_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Satellite_Available":
                bool(
                    stock_target
                ),

            "Alpha_Gross_Return_Pct":
                100.0
                *
                (
                    alpha_growth
                    -
                    1.0
                ),

            "TQQQ_Gross_Return_Pct":
                100.0
                *
                (
                    tqqq_growth
                    -
                    1.0
                ),

            "Alpha_Minus_TQQQ_pp":
                100.0
                *
                (
                    alpha_growth
                    -
                    tqqq_growth
                ),
        }
    )


V10_STOCK_SLEEVE_GROSS_AUDIT = pd.DataFrame(
    V10_STOCK_SLEEVE_GROSS_ROWS
)


# ==============================================================================
# 10. UNIVERSAL EXPERT GRID
# ==============================================================================

V10_EXPERT_ALPHA_WEIGHT = np.linspace(
    0.0,
    1.0,
    V10_UNIVERSAL_GRID_POINTS,
    dtype=float,
)


V10_EXPERT_TQQQ_WEIGHT = (
    1.0
    -
    V10_EXPERT_ALPHA_WEIGHT
)


if len(
    V10_EXPERT_ALPHA_WEIGHT
) != 1001:

    raise RuntimeError(
        "V10 universal expert grid must contain 1001 points."
    )


# ==============================================================================
# 11. POSTERIOR HELPER
# ==============================================================================

def v10b3_posterior(
    log_wealth,
):

    log_wealth = np.asarray(
        log_wealth,
        dtype=float,
    )


    anchor = float(
        np.max(
            log_wealth
        )
    )


    probabilities = np.exp(
        log_wealth
        -
        anchor
    )


    total = float(
        probabilities.sum()
    )


    if (
        not np.isfinite(
            total
        )
        or
        total <= 0
    ):

        raise RuntimeError(
            "V10 posterior normalization failed."
        )


    return (
        probabilities
        /
        total
    )


# ==============================================================================
# 12. ACTUAL UNDERLYING TARGET HELPER
# ==============================================================================

def v10b3_actual_target(
    alpha_weight,
    stock_target,
):

    alpha_weight = float(
        alpha_weight
    )


    if not stock_target:

        return {
            "TQQQ":
                1.0
        }


    target = {
        "TQQQ":
            1.0
            -
            alpha_weight
    }


    for ticker, sleeve_weight in (
        stock_target.items()
    ):

        contribution = (
            alpha_weight
            *
            float(
                sleeve_weight
            )
        )


        if contribution > 0:

            target[
                ticker
            ] = (
                target.get(
                    ticker,
                    0.0,
                )
                +
                contribution
            )


    target = {
        ticker:
            float(weight)

        for ticker, weight
        in target.items()

        if weight > 0
    }


    total = float(
        sum(
            target.values()
        )
    )


    if (
        not np.isfinite(
            total
        )
        or
        total <= 0
    ):

        raise RuntimeError(
            "Invalid V10 actual target."
        )


    return {
        ticker:
            weight / total

        for ticker, weight
        in target.items()
    }


# ==============================================================================
# 13. EXPERT TARGET HELPER
# ==============================================================================

def v10b3_expert_target(
    stock_target,
):

    target = {}


    if not stock_target:

        target[
            "TQQQ"
        ] = np.ones(
            V10_UNIVERSAL_GRID_POINTS,
            dtype=float,
        )


        return target


    target[
        "TQQQ"
    ] = (
        V10_EXPERT_TQQQ_WEIGHT.copy()
    )


    for ticker, sleeve_weight in (
        stock_target.items()
    ):

        target[
            ticker
        ] = (
            V10_EXPERT_ALPHA_WEIGHT
            *
            float(
                sleeve_weight
            )
        )


    return target


# ==============================================================================
# 14. ACTUAL EXECUTION COST
# ==============================================================================

def v10b3_actual_execution_cost(
    previous_drift,
    target,
    signal_date,
):

    names = (
        set(
            previous_drift
        )
        |
        set(
            target
        )
    )


    turnover = 0.0

    impact_cost = 0.0


    for ticker in names:

        delta = (
            float(
                target.get(
                    ticker,
                    0.0,
                )
            )
            -
            float(
                previous_drift.get(
                    ticker,
                    0.0,
                )
            )
        )


        abs_delta = abs(
            delta
        )


        turnover += abs_delta


        if abs_delta <= 0:

            continue


        scale = v10b3_impact_scale(
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
                "Missing execution impact state for "
                f"{ticker} at "
                f"{pd.Timestamp(signal_date).date()}."
            )


        impact_cost += (
            scale
            *
            abs_delta ** 1.5
        )


    base_cost = (
        float(
            V10_BASE_TCA_RATE
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
            "Invalid actual V10 execution cost."
        )


    return (
        float(
            turnover
        ),
        float(
            base_cost
        ),
        float(
            impact_cost
        ),
        float(
            total_cost
        ),
    )


# ==============================================================================
# 15. EXPERT EXECUTION COST VECTOR
# ==============================================================================

def v10b3_expert_execution_cost(
    previous_drift,
    target,
    signal_date,
):

    names = (
        set(
            previous_drift
        )
        |
        set(
            target
        )
    )


    turnover = np.zeros(
        V10_UNIVERSAL_GRID_POINTS,
        dtype=float,
    )


    impact_cost = np.zeros(
        V10_UNIVERSAL_GRID_POINTS,
        dtype=float,
    )


    zero = np.zeros(
        V10_UNIVERSAL_GRID_POINTS,
        dtype=float,
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


        delta = (
            current
            -
            previous
        )


        abs_delta = np.abs(
            delta
        )


        turnover += abs_delta


        if not np.any(
            abs_delta > 0
        ):

            continue


        scale = v10b3_impact_scale(
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
                "Missing expert execution state for "
                f"{ticker} at "
                f"{pd.Timestamp(signal_date).date()}."
            )


        impact_cost += (
            scale
            *
            abs_delta ** 1.5
        )


    base_cost = (
        float(
            V10_BASE_TCA_RATE
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
        ~np.isfinite(
            total_cost
        )
    ).any():

        raise RuntimeError(
            "Expert execution cost contains non-finite values."
        )


    if (
        total_cost < 0
    ).any() or (
        total_cost >= 1
    ).any():

        raise RuntimeError(
            "Invalid expert execution cost."
        )


    return (
        turnover,
        base_cost,
        impact_cost,
        total_cost,
    )


# ==============================================================================
# 16. TARGET HOLDING GROSS MULTIPLIER
# ==============================================================================

def v10b3_actual_gross_multiplier(
    target,
    growth_map,
):

    multiplier = float(
        sum(
            weight
            *
            growth_map[
                ticker
            ]

            for ticker, weight
            in target.items()
        )
    )


    if (
        not np.isfinite(
            multiplier
        )
        or
        multiplier <= 0
    ):

        raise RuntimeError(
            "Invalid actual portfolio gross multiplier."
        )


    return multiplier


def v10b3_expert_gross_multiplier(
    target,
    growth_map,
):

    multiplier = np.zeros(
        V10_UNIVERSAL_GRID_POINTS,
        dtype=float,
    )


    for ticker, weight_vector in (
        target.items()
    ):

        multiplier += (
            weight_vector
            *
            growth_map[
                ticker
            ]
        )


    if (
        ~np.isfinite(
            multiplier
        )
    ).any() or (
        multiplier <= 0
    ).any():

        raise RuntimeError(
            "Invalid expert gross multiplier."
        )


    return multiplier


# ==============================================================================
# 17. DRIFT TARGETS TO EVENT END
# ==============================================================================

def v10b3_drift_actual(
    target,
    growth_map,
):

    values = {
        ticker:
            float(weight)
            *
            float(
                growth_map[
                    ticker
                ]
            )

        for ticker, weight
        in target.items()
    }


    total = float(
        sum(
            values.values()
        )
    )


    if (
        not np.isfinite(
            total
        )
        or
        total <= 0
    ):

        raise RuntimeError(
            "Invalid actual drift."
        )


    return {
        ticker:
            value / total

        for ticker, value
        in values.items()
    }


def v10b3_drift_experts(
    target,
    growth_map,
):

    total = np.zeros(
        V10_UNIVERSAL_GRID_POINTS,
        dtype=float,
    )


    end_values = {}


    for ticker, weights in (
        target.items()
    ):

        values = (
            weights
            *
            float(
                growth_map[
                    ticker
                ]
            )
        )


        end_values[
            ticker
        ] = values


        total += values


    if (
        ~np.isfinite(
            total
        )
    ).any() or (
        total <= 0
    ).any():

        raise RuntimeError(
            "Invalid expert drift denominator."
        )


    return {
        ticker:
            values
            /
            total

        for ticker, values
        in end_values.items()
    }


# ==============================================================================
# 18. UNIVERSAL WALK-FORWARD
# ==============================================================================

V10_EXPERT_LOG_WEALTH = np.zeros(
    V10_UNIVERSAL_GRID_POINTS,
    dtype=float,
)


V10_EXPERT_PREVIOUS_DRIFT = {}

V10_ACTUAL_PREVIOUS_DRIFT = {}


V10_UNIVERSAL_WEALTH = 1.0


V10_UNIVERSAL_ROWS = []

V10_ACTUAL_TARGETS = {}


for event_index in range(
    len(
        V10_STOCK_SLEEVE_DECISIONS
    )
):

    decision = (
        V10_STOCK_SLEEVE_DECISIONS
        .iloc[
            event_index
        ]
    )


    signal_date = pd.Timestamp(
        decision[
            "Signal_Date"
        ]
    )


    execution_date = pd.Timestamp(
        decision[
            "Execution_Date"
        ]
    )


    if (
        event_index
        <
        len(
            V10_STOCK_SLEEVE_DECISIONS
        )
        -
        1
    ):

        exit_date = pd.Timestamp(
            V10_STOCK_SLEEVE_DECISIONS
            .iloc[
                event_index + 1
            ][
                "Execution_Date"
            ]
        )

    else:

        exit_date = execution_date


    stock_target = (
        V10_STOCK_SLEEVE_TARGETS[
            execution_date
        ]
    )


    growth_map = (
        V10_B3_EVENT_GROWTH[
            event_index
        ]
    )


    # ==========================================================================
    # PRE-EVENT POSTERIOR
    # ==========================================================================

    posterior = v10b3_posterior(
        V10_EXPERT_LOG_WEALTH
    )


    pre_alpha_weight = float(
        np.dot(
            posterior,
            V10_EXPERT_ALPHA_WEIGHT,
        )
    )


    pre_tqqq_weight = (
        1.0
        -
        pre_alpha_weight
    )


    if not stock_target:

        effective_alpha_weight = 0.0

        effective_tqqq_weight = 1.0

    else:

        effective_alpha_weight = (
            pre_alpha_weight
        )

        effective_tqqq_weight = (
            pre_tqqq_weight
        )


    # ==========================================================================
    # ACTUAL TARGET
    # ==========================================================================

    actual_target = v10b3_actual_target(
        alpha_weight=pre_alpha_weight,
        stock_target=stock_target,
    )


    V10_ACTUAL_TARGETS[
        execution_date
    ] = dict(
        actual_target
    )


    # ==========================================================================
    # ACTUAL EXECUTION COST
    # ==========================================================================

    (
        actual_turnover,
        actual_base_cost,
        actual_impact_cost,
        actual_total_cost,
    ) = v10b3_actual_execution_cost(
        previous_drift=V10_ACTUAL_PREVIOUS_DRIFT,
        target=actual_target,
        signal_date=signal_date,
    )


    wealth_before_trade = float(
        V10_UNIVERSAL_WEALTH
    )


    wealth_after_trade = (
        wealth_before_trade
        *
        (
            1.0
            -
            actual_total_cost
        )
    )


    # ==========================================================================
    # ACTUAL HOLDING RETURN
    # ==========================================================================

    actual_gross_multiplier = (
        v10b3_actual_gross_multiplier(
            target=actual_target,
            growth_map=growth_map,
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


    V10_UNIVERSAL_WEALTH *= (
        actual_net_multiplier
    )


    # ==========================================================================
    # EXPERT TARGETS
    # ==========================================================================

    expert_target = (
        v10b3_expert_target(
            stock_target
        )
    )


    (
        expert_turnover,
        expert_base_cost,
        expert_impact_cost,
        expert_total_cost,
    ) = (
        v10b3_expert_execution_cost(
            previous_drift=(
                V10_EXPERT_PREVIOUS_DRIFT
            ),
            target=expert_target,
            signal_date=signal_date,
        )
    )


    expert_gross_multiplier = (
        v10b3_expert_gross_multiplier(
            target=expert_target,
            growth_map=growth_map,
        )
    )


    expert_net_multiplier = (
        (
            1.0
            -
            expert_total_cost
        )
        *
        expert_gross_multiplier
    )


    if (
        ~np.isfinite(
            expert_net_multiplier
        )
    ).any() or (
        expert_net_multiplier <= 0
    ).any():

        raise RuntimeError(
            "Invalid V10 expert net multiplier."
        )


    # ==========================================================================
    # POST-EVENT EXPERT UPDATE
    # ==========================================================================

    V10_EXPERT_LOG_WEALTH += np.log(
        expert_net_multiplier
    )


    post_posterior = v10b3_posterior(
        V10_EXPERT_LOG_WEALTH
    )


    post_alpha_weight = float(
        np.dot(
            post_posterior,
            V10_EXPERT_ALPHA_WEIGHT,
        )
    )


    post_tqqq_weight = (
        1.0
        -
        post_alpha_weight
    )


    effective_experts = float(
        1.0
        /
        np.sum(
            post_posterior ** 2
        )
    )


    largest_expert_probability = float(
        np.max(
            post_posterior
        )
    )


    # ==========================================================================
    # SAVE EVENT
    # ==========================================================================

    V10_UNIVERSAL_ROWS.append(
        {
            "Event":
                event_index + 1,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Satellite_Available":
                bool(
                    stock_target
                ),

            "Stock_Names":
                len(
                    stock_target
                ),

            "Pre_Posterior_TQQQ_Weight":
                pre_tqqq_weight,

            "Pre_Posterior_Alpha_Weight":
                pre_alpha_weight,

            "Effective_TQQQ_Weight":
                effective_tqqq_weight,

            "Effective_Alpha_Weight":
                effective_alpha_weight,

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

            "Wealth_Before_Trade":
                wealth_before_trade,

            "Wealth_After_Trade":
                wealth_after_trade,

            "End_Wealth":
                V10_UNIVERSAL_WEALTH,

            "Post_Posterior_TQQQ_Weight":
                post_tqqq_weight,

            "Post_Posterior_Alpha_Weight":
                post_alpha_weight,

            "Effective_Experts":
                effective_experts,

            "Largest_Expert_Posterior_Pct":
                100.0
                *
                largest_expert_probability,
        }
    )


    # ==========================================================================
    # DRIFT STATES FOR NEXT EVENT
    # ==========================================================================

    V10_ACTUAL_PREVIOUS_DRIFT = (
        v10b3_drift_actual(
            target=actual_target,
            growth_map=growth_map,
        )
    )


    V10_EXPERT_PREVIOUS_DRIFT = (
        v10b3_drift_experts(
            target=expert_target,
            growth_map=growth_map,
        )
    )


V10_UNIVERSAL_PATH = pd.DataFrame(
    V10_UNIVERSAL_ROWS
)


# ==============================================================================
# 19. FINAL EXPERT / POSTERIOR STATE
# ==============================================================================

V10_EXPERT_FINAL_WEALTH = np.exp(
    V10_EXPERT_LOG_WEALTH
)


V10_FINAL_POSTERIOR = v10b3_posterior(
    V10_EXPERT_LOG_WEALTH
)


V10_FINAL_POSTERIOR_ALPHA = float(
    np.dot(
        V10_FINAL_POSTERIOR,
        V10_EXPERT_ALPHA_WEIGHT,
    )
)


V10_FINAL_POSTERIOR_TQQQ = (
    1.0
    -
    V10_FINAL_POSTERIOR_ALPHA
)


V10_BEST_CONSTANT_INDEX = int(
    np.argmax(
        V10_EXPERT_FINAL_WEALTH
    )
)


V10_BEST_CONSTANT_ALPHA_WEIGHT = float(
    V10_EXPERT_ALPHA_WEIGHT[
        V10_BEST_CONSTANT_INDEX
    ]
)


V10_BEST_CONSTANT_TQQQ_WEIGHT = (
    1.0
    -
    V10_BEST_CONSTANT_ALPHA_WEIGHT
)


V10_BEST_CONSTANT_WEALTH = float(
    V10_EXPERT_FINAL_WEALTH[
        V10_BEST_CONSTANT_INDEX
    ]
)


# ==============================================================================
# 20. SAME-CALENDAR FULL-COST TQQQ BUY-AND-HOLD
# ==============================================================================

V10_FIRST_SIGNAL_DATE = pd.Timestamp(
    V10_STOCK_SLEEVE_DECISIONS[
        "Signal_Date"
    ].iloc[
        0
    ]
)


V10_FIRST_EXECUTION_DATE = pd.Timestamp(
    V10_STOCK_SLEEVE_DECISIONS[
        "Execution_Date"
    ].iloc[
        0
    ]
)


V10_LAST_EXECUTION_DATE = pd.Timestamp(
    V10_STOCK_SLEEVE_DECISIONS[
        "Execution_Date"
    ].iloc[
        -1
    ]
)


V10_TQQQ_INITIAL_PRICE = v10b3_exact_price(
    "TQQQ",
    V10_FIRST_EXECUTION_DATE,
)


V10_TQQQ_FINAL_PRICE = v10b3_exact_price(
    "TQQQ",
    V10_LAST_EXECUTION_DATE,
)


V10_TQQQ_INITIAL_IMPACT = (
    v10b3_impact_scale(
        "TQQQ",
        V10_FIRST_SIGNAL_DATE,
    )
)


V10_TQQQ_INITIAL_COST = (
    float(
        V10_BASE_TCA_RATE
    )
    +
    V10_TQQQ_INITIAL_IMPACT
)


if (
    not np.isfinite(
        V10_TQQQ_INITIAL_COST
    )
    or
    V10_TQQQ_INITIAL_COST < 0
    or
    V10_TQQQ_INITIAL_COST >= 1
):

    raise RuntimeError(
        "Invalid TQQQ benchmark initial cost."
    )


V10_TQQQ_FINAL_WEALTH = (
    (
        1.0
        -
        V10_TQQQ_INITIAL_COST
    )
    *
    V10_TQQQ_FINAL_PRICE
    /
    V10_TQQQ_INITIAL_PRICE
)


V10_FINAL_WEALTH = float(
    V10_UNIVERSAL_PATH[
        "End_Wealth"
    ].iloc[
        -1
    ]
)


# ==============================================================================
# 21. EXACT TERMINAL-WEALTH ACCOUNTING CHECK
# ==============================================================================

V10_RECONSTRUCTED_EVENT_WEALTH = (
    (
        1.0
        +
        V10_UNIVERSAL_PATH[
            "Net_Return"
        ]
    )
    .cumprod()
)


V10_EVENT_WEALTH_MAX_ERROR = float(
    np.max(
        np.abs(
            V10_RECONSTRUCTED_EVENT_WEALTH
            -
            V10_UNIVERSAL_PATH[
                "End_Wealth"
            ]
            .to_numpy(
                dtype=float
            )
        )
    )
)


if V10_EVENT_WEALTH_MAX_ERROR > 1e-10:

    raise RuntimeError(
        "V10 event wealth reconstruction failed."
    )


# ==============================================================================
# 22. DAILY MARKET CALENDAR
# ==============================================================================

V10_DAILY_CALENDAR = (
    V10_B3_LIFECYCLE.loc[
        (
            V10_B3_LIFECYCLE[
                "Ticker"
            ]
            ==
            "TQQQ"
        )
        &
        (
            V10_B3_LIFECYCLE[
                "Date"
            ]
            >=
            V10_FIRST_EXECUTION_DATE
        )
        &
        (
            V10_B3_LIFECYCLE[
                "Date"
            ]
            <=
            V10_LAST_EXECUTION_DATE
        )
        &
        (
            V10_B3_LIFECYCLE[
                "Adj_Close"
            ]
            .notna()
        ),
        "Date",
    ]
    .drop_duplicates()
    .sort_values()
)


V10_DAILY_CALENDAR = pd.DatetimeIndex(
    V10_DAILY_CALENDAR
)


if (
    V10_FIRST_EXECUTION_DATE
    not in V10_DAILY_CALENDAR
    or
    V10_LAST_EXECUTION_DATE
    not in V10_DAILY_CALENDAR
):

    raise RuntimeError(
        "V10 daily calendar does not cover the full research interval."
    )


# ==============================================================================
# 23. BUILD DAILY PRICE SERIES ONLY FOR ACTUALLY USED ASSETS
# ==============================================================================

V10_USED_ASSETS = set(
    [
        "TQQQ"
    ]
)


for target in V10_ACTUAL_TARGETS.values():

    V10_USED_ASSETS.update(
        target.keys()
    )


V10_DAILY_PRICE_SERIES = {}


for ticker in sorted(
    V10_USED_ASSETS
):

    raw_series = (
        V10_B3_LIFECYCLE.loc[
            V10_B3_LIFECYCLE[
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
    )


    aligned = (
        raw_series
        .reindex(
            V10_DAILY_CALENDAR
        )
        .ffill()
    )


    V10_DAILY_PRICE_SERIES[
        ticker
    ] = aligned


# ==============================================================================
# 24. DAILY V10 NAV RECONSTRUCTION
# ==============================================================================

V10_DAILY_NAV_VALUES = {}


for event_index in range(
    len(
        V10_UNIVERSAL_PATH
    )
):

    event = (
        V10_UNIVERSAL_PATH
        .iloc[
            event_index
        ]
    )


    execution_date = pd.Timestamp(
        event[
            "Execution_Date"
        ]
    )


    target = (
        V10_ACTUAL_TARGETS[
            execution_date
        ]
    )


    wealth_after_trade = float(
        event[
            "Wealth_After_Trade"
        ]
    )


    if (
        event_index
        <
        len(
            V10_UNIVERSAL_PATH
        )
        -
        1
    ):

        next_execution_date = pd.Timestamp(
            V10_UNIVERSAL_PATH
            .iloc[
                event_index + 1
            ][
                "Execution_Date"
            ]
        )


        segment_dates = (
            V10_DAILY_CALENDAR[
                (
                    V10_DAILY_CALENDAR
                    >=
                    execution_date
                )
                &
                (
                    V10_DAILY_CALENDAR
                    <
                    next_execution_date
                )
            ]
        )

    else:

        segment_dates = pd.DatetimeIndex(
            [
                execution_date
            ]
        )


    for date in segment_dates:

        gross_multiplier = 0.0


        for ticker, weight in (
            target.items()
        ):

            price_series = (
                V10_DAILY_PRICE_SERIES[
                    ticker
                ]
            )


            entry_price = price_series.loc[
                execution_date
            ]


            current_price = price_series.loc[
                date
            ]


            if (
                not np.isfinite(
                    entry_price
                )
                or
                not np.isfinite(
                    current_price
                )
                or
                entry_price <= 0
                or
                current_price <= 0
            ):

                raise RuntimeError(
                    "Daily V10 NAV price gap: "
                    f"{ticker} | "
                    f"{execution_date.date()} -> "
                    f"{pd.Timestamp(date).date()}"
                )


            gross_multiplier += (
                float(
                    weight
                )
                *
                current_price
                /
                entry_price
            )


        V10_DAILY_NAV_VALUES[
            date
        ] = (
            wealth_after_trade
            *
            gross_multiplier
        )


    # The NEXT execution-date value is intentionally not written here.
    # It will be written by the next event AFTER its rebalance cost.


V10_DAILY_NAV = pd.Series(
    V10_DAILY_NAV_VALUES,
    name="V10",
).sort_index()


# Ensure terminal post-trade wealth is exactly represented.

V10_DAILY_NAV.loc[
    V10_LAST_EXECUTION_DATE
] = (
    V10_UNIVERSAL_PATH[
        "Wealth_After_Trade"
    ].iloc[
        -1
    ]
)


V10_DAILY_NAV = (
    V10_DAILY_NAV
    .sort_index()
)


# ==============================================================================
# 25. DAILY TQQQ BUY-AND-HOLD NAV
# ==============================================================================

V10_TQQQ_DAILY_PRICES = (
    V10_DAILY_PRICE_SERIES[
        "TQQQ"
    ]
)


V10_TQQQ_DAILY_NAV = (
    (
        1.0
        -
        V10_TQQQ_INITIAL_COST
    )
    *
    V10_TQQQ_DAILY_PRICES
    /
    float(
        V10_TQQQ_INITIAL_PRICE
    )
)


V10_TQQQ_DAILY_NAV.name = (
    "TQQQ"
)


# ==============================================================================
# 26. ALIGN DAILY NAVS
# ==============================================================================

V10_DAILY_COMPARISON = pd.concat(
    [
        V10_DAILY_NAV,
        V10_TQQQ_DAILY_NAV,
    ],
    axis=1,
    join="inner",
).dropna()


if V10_DAILY_COMPARISON.empty:

    raise RuntimeError(
        "V10 daily NAV comparison is empty."
    )


if (
    V10_DAILY_COMPARISON.index[
        -1
    ]
    !=
    V10_LAST_EXECUTION_DATE
):

    raise RuntimeError(
        "Daily NAV does not end on final research execution date."
    )


V10_DAILY_FINAL_ERROR = abs(
    float(
        V10_DAILY_COMPARISON[
            "V10"
        ].iloc[
            -1
        ]
    )
    -
    V10_FINAL_WEALTH
)


V10_TQQQ_DAILY_FINAL_ERROR = abs(
    float(
        V10_DAILY_COMPARISON[
            "TQQQ"
        ].iloc[
            -1
        ]
    )
    -
    V10_TQQQ_FINAL_WEALTH
)


if (
    V10_DAILY_FINAL_ERROR
    >
    1e-10
):

    raise RuntimeError(
        "V10 daily NAV does not reconcile to terminal wealth."
    )


if (
    V10_TQQQ_DAILY_FINAL_ERROR
    >
    1e-10
):

    raise RuntimeError(
        "TQQQ daily NAV does not reconcile to benchmark wealth."
    )


# ==============================================================================
# 27. STRICT PREDECLARED ACCEPTANCE WINDOWS
# ==============================================================================

V10_ACCEPTANCE_ROWS = []


for window_name, sessions in (
    V10_ACCEPTANCE_WINDOWS.items()
):

    if window_name == "FULL":

        v10_return = (
            V10_FINAL_WEALTH
            -
            1.0
        )


        tqqq_return = (
            V10_TQQQ_FINAL_WEALTH
            -
            1.0
        )


        start_date = (
            V10_FIRST_EXECUTION_DATE
        )


    else:

        sessions = int(
            sessions
        )


        if (
            len(
                V10_DAILY_COMPARISON
            )
            <
            sessions + 1
        ):

            raise RuntimeError(
                "Insufficient daily observations for "
                f"{window_name} acceptance test."
            )


        end_row = (
            V10_DAILY_COMPARISON
            .iloc[
                -1
            ]
        )


        start_row = (
            V10_DAILY_COMPARISON
            .iloc[
                -(
                    sessions
                    +
                    1
                )
            ]
        )


        start_date = (
            V10_DAILY_COMPARISON
            .index[
                -(
                    sessions
                    +
                    1
                )
            ]
        )


        v10_return = (
            float(
                end_row[
                    "V10"
                ]
            )
            /
            float(
                start_row[
                    "V10"
                ]
            )
            -
            1.0
        )


        tqqq_return = (
            float(
                end_row[
                    "TQQQ"
                ]
            )
            /
            float(
                start_row[
                    "TQQQ"
                ]
            )
            -
            1.0
        )


    excess_pp = (
        100.0
        *
        (
            v10_return
            -
            tqqq_return
        )
    )


    passed = bool(
        v10_return
        >
        tqqq_return
    )


    V10_ACCEPTANCE_ROWS.append(
        {
            "Window":
                window_name,

            "Trading_Sessions":
                sessions,

            "Start_Date":
                start_date,

            "End_Date":
                V10_LAST_EXECUTION_DATE,

            "V10_Return_Pct":
                100.0
                *
                v10_return,

            "TQQQ_Return_Pct":
                100.0
                *
                tqqq_return,

            "V10_Minus_TQQQ_pp":
                excess_pp,

            "PASS":
                passed,
        }
    )


V10_ACCEPTANCE_TABLE = pd.DataFrame(
    V10_ACCEPTANCE_ROWS
)


# ==============================================================================
# 28. FINAL RESEARCH VERDICT
# ==============================================================================

V10_FULL_HISTORY_PASS = bool(
    V10_ACCEPTANCE_TABLE.loc[
        V10_ACCEPTANCE_TABLE[
            "Window"
        ]
        ==
        "FULL",
        "PASS",
    ]
    .iloc[
        0
    ]
)


V10_ALL_WINDOWS_PASS = bool(
    V10_ACCEPTANCE_TABLE[
        "PASS"
    ].all()
)


V10_FAILED_WINDOWS = (
    V10_ACCEPTANCE_TABLE.loc[
        ~V10_ACCEPTANCE_TABLE[
            "PASS"
        ],
        "Window",
    ]
    .tolist()
)


V10_RESEARCH_VERDICT = (
    "PASS"
    if (
        V10_FULL_HISTORY_PASS
        and
        V10_ALL_WINDOWS_PASS
    )
    else
    "FAIL"
)


V10_BEATS_TQQQ_FULL_HISTORY = (
    V10_FULL_HISTORY_PASS
)


# ==============================================================================
# 29. PERFORMANCE SUMMARY
# ==============================================================================

V10_FINAL_RETURN_PCT = (
    100.0
    *
    (
        V10_FINAL_WEALTH
        -
        1.0
    )
)


V10_TQQQ_RETURN_PCT = (
    100.0
    *
    (
        V10_TQQQ_FINAL_WEALTH
        -
        1.0
    )
)


V10_MINUS_TQQQ_PP = (
    100.0
    *
    (
        V10_FINAL_WEALTH
        -
        V10_TQQQ_FINAL_WEALTH
    )
)


V10_RELATIVE_WEALTH_VS_TQQQ = (
    V10_FINAL_WEALTH
    /
    V10_TQQQ_FINAL_WEALTH
)


V10_RELATIVE_GAIN_VS_TQQQ_PCT = (
    100.0
    *
    (
        V10_RELATIVE_WEALTH_VS_TQQQ
        -
        1.0
    )
)


V10_TOTAL_TURNOVER = float(
    V10_UNIVERSAL_PATH[
        "Turnover"
    ].sum()
)


V10_MEAN_EXECUTION_COST_BPS = float(
    V10_UNIVERSAL_PATH[
        "Total_Cost_bps"
    ].mean()
)


V10_MEDIAN_EXECUTION_COST_BPS = float(
    V10_UNIVERSAL_PATH[
        "Total_Cost_bps"
    ].median()
)


V10_MEAN_EFFECTIVE_ALPHA_PCT = float(
    100.0
    *
    V10_UNIVERSAL_PATH[
        "Effective_Alpha_Weight"
    ].mean()
)


V10_MEAN_EFFECTIVE_TQQQ_PCT = (
    100.0
    -
    V10_MEAN_EFFECTIVE_ALPHA_PCT
)


V10_LAST_EXECUTED_ALPHA_PCT = float(
    100.0
    *
    V10_UNIVERSAL_PATH[
        "Effective_Alpha_Weight"
    ].iloc[
        -1
    ]
)


V10_LAST_EXECUTED_TQQQ_PCT = (
    100.0
    -
    V10_LAST_EXECUTED_ALPHA_PCT
)


# ==============================================================================
# 30. STOCK-SLEEVE CONCENTRATION SUMMARY
# ==============================================================================

available_rows = (
    V10_STOCK_SLEEVE_DECISIONS[
        V10_STOCK_SLEEVE_DECISIONS[
            "Satellite_Available"
        ]
    ]
)


V10_STOCK_SLEEVE_CONCENTRATION = pd.DataFrame(
    {
        "Metric": [

            "Research decisions",

            "Satellite available decisions",

            "Satellite available pct",

            "Mean positive-edge stocks",

            "Median positive-edge stocks",

            "Minimum positive-edge stocks",

            "Maximum positive-edge stocks",

            "Mean effective N when available",

            "Median effective N when available",

            "Mean max stock weight pct",

            "Median max stock weight pct",

            "Maximum max stock weight pct",
        ],

        "Value": [

            len(
                V10_STOCK_SLEEVE_DECISIONS
            ),

            len(
                available_rows
            ),

            100.0
            *
            len(
                available_rows
            )
            /
            len(
                V10_STOCK_SLEEVE_DECISIONS
            ),

            available_rows[
                "Positive_Edge_Stocks"
            ].mean(),

            available_rows[
                "Positive_Edge_Stocks"
            ].median(),

            available_rows[
                "Positive_Edge_Stocks"
            ].min(),

            available_rows[
                "Positive_Edge_Stocks"
            ].max(),

            available_rows[
                "Effective_N"
            ].mean(),

            available_rows[
                "Effective_N"
            ].median(),

            available_rows[
                "Max_Stock_Weight_Pct"
            ].mean(),

            available_rows[
                "Max_Stock_Weight_Pct"
            ].median(),

            available_rows[
                "Max_Stock_Weight_Pct"
            ].max(),
        ],
    }
)


# ==============================================================================
# 31. FINAL TARGET PORTFOLIO
# ==============================================================================

V10_FINAL_EXECUTED_TARGET = pd.Series(
    V10_ACTUAL_TARGETS[
        V10_LAST_EXECUTION_DATE
    ],
    name="Weight",
).sort_values(
    ascending=False
)


V10_FINAL_EXECUTED_TARGET_TABLE = (
    (
        100.0
        *
        V10_FINAL_EXECUTED_TARGET
    )
    .rename(
        "Weight_Pct"
    )
    .to_frame()
)


# ==============================================================================
# 32. FINAL RESULT TABLE
# ==============================================================================

V10_FINAL_RESULT_TABLE = pd.DataFrame(
    {
        "Metric": [

            "Research decisions",

            "Universal experts",

            "V10 final wealth",

            "V10 net return pct",

            "TQQQ full-cost wealth",

            "TQQQ full-cost return pct",

            "V10 minus TQQQ pp",

            "V10 / TQQQ relative wealth",

            "V10 relative gain vs TQQQ pct",

            "Mean effective TQQQ allocation pct",

            "Mean effective Alpha allocation pct",

            "Last executed TQQQ allocation pct",

            "Last executed Alpha allocation pct",

            "Final posterior TQQQ pct",

            "Final posterior Alpha pct",

            "Total turnover",

            "Mean execution cost bps",

            "Median execution cost bps",

            "Best constant expert wealth — hindsight only",

            "Best constant TQQQ pct — hindsight only",

            "Best constant Alpha pct — hindsight only",

            "Daily NAV reconstruction max terminal error",

            "Event wealth reconstruction max error",

            "Impact-state causal fallback count",

            "Full-history requirement passed",

            "All declared windows passed",

            "V10 research verdict",
        ],

        "Value": [

            len(
                V10_UNIVERSAL_PATH
            ),

            V10_UNIVERSAL_GRID_POINTS,

            V10_FINAL_WEALTH,

            V10_FINAL_RETURN_PCT,

            V10_TQQQ_FINAL_WEALTH,

            V10_TQQQ_RETURN_PCT,

            V10_MINUS_TQQQ_PP,

            V10_RELATIVE_WEALTH_VS_TQQQ,

            V10_RELATIVE_GAIN_VS_TQQQ_PCT,

            V10_MEAN_EFFECTIVE_TQQQ_PCT,

            V10_MEAN_EFFECTIVE_ALPHA_PCT,

            V10_LAST_EXECUTED_TQQQ_PCT,

            V10_LAST_EXECUTED_ALPHA_PCT,

            100.0
            *
            V10_FINAL_POSTERIOR_TQQQ,

            100.0
            *
            V10_FINAL_POSTERIOR_ALPHA,

            V10_TOTAL_TURNOVER,

            V10_MEAN_EXECUTION_COST_BPS,

            V10_MEDIAN_EXECUTION_COST_BPS,

            V10_BEST_CONSTANT_WEALTH,

            100.0
            *
            V10_BEST_CONSTANT_TQQQ_WEIGHT,

            100.0
            *
            V10_BEST_CONSTANT_ALPHA_WEIGHT,

            max(
                V10_DAILY_FINAL_ERROR,
                V10_TQQQ_DAILY_FINAL_ERROR,
            ),

            V10_EVENT_WEALTH_MAX_ERROR,

            V10_B3_STATE_FALLBACK_COUNT,

            V10_FULL_HISTORY_PASS,

            V10_ALL_WINDOWS_PASS,

            V10_RESEARCH_VERDICT,
        ],
    }
)


# ==============================================================================
# 33. RESEARCH FINGERPRINT
# ==============================================================================

V10_BLOCK3_RESULT_PAYLOAD = {

    "block3_spec_fingerprint":
        V10_BLOCK3_SPEC_FINGERPRINT,

    "block2_result_fingerprint":
        V10_BLOCK2_RESEARCH_FINGERPRINT,

    "prediction_hash":
        V10_PREDICTIONS_HASH,

    "final_wealth":
        V10_FINAL_WEALTH,

    "tqqq_final_wealth":
        V10_TQQQ_FINAL_WEALTH,

    "relative_wealth":
        V10_RELATIVE_WEALTH_VS_TQQQ,

    "final_posterior_alpha":
        V10_FINAL_POSTERIOR_ALPHA,

    "best_constant_alpha_hindsight":
        V10_BEST_CONSTANT_ALPHA_WEIGHT,

    "best_constant_wealth_hindsight":
        V10_BEST_CONSTANT_WEALTH,

    "failed_windows":
        V10_FAILED_WINDOWS,

    "verdict":
        V10_RESEARCH_VERDICT,
}


V10_BLOCK3_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V10_BLOCK3_RESULT_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 34. OUTPUT — STOCK-SLEEVE CONSTRUCTION
# ==============================================================================

print(
    "\n1) V10 PROBABILITY-EDGE STOCK-SLEEVE AUDIT"
)


display(
    V10_STOCK_SLEEVE_DECISIONS[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Candidate_Stocks",
            "Positive_Edge_Stocks",
            "Positive_Edge_Pct",
            "Satellite_Available",
            "Median_Composite_Probability",
            "Maximum_Composite_Probability",
            "Effective_N",
            "Max_Stock_Weight_Pct",
            "Largest_Stock_Position",
        ]
    ]
    .round(
        6
    )
)


# ==============================================================================
# 35. OUTPUT — CONCENTRATION
# ==============================================================================

print(
    "\n2) STOCK-SLEEVE CONCENTRATION SUMMARY"
)


display(
    V10_STOCK_SLEEVE_CONCENTRATION.round(
        6
    )
)


# ==============================================================================
# 36. OUTPUT — FINAL ECONOMIC RESULT
# ==============================================================================

print(
    "\n3) V10 FINAL ECONOMIC RESULT"
)


display(
    V10_FINAL_RESULT_TABLE.round(
        6
    )
)


# ==============================================================================
# 37. OUTPUT — STRICT ACCEPTANCE WINDOWS
# ==============================================================================

print(
    "\n4) STRICT PREDECLARED TQQQ-DOMINANCE WINDOWS"
)


display(
    V10_ACCEPTANCE_TABLE.round(
        6
    )
)


# ==============================================================================
# 38. OUTPUT — UNIVERSAL PATH
# ==============================================================================

print(
    "\n5) UNIVERSAL WALK-FORWARD PATH"
)


display(
    V10_UNIVERSAL_PATH[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Exit_Date",

            "Satellite_Available",
            "Stock_Names",

            "Pre_Posterior_TQQQ_Weight",
            "Pre_Posterior_Alpha_Weight",

            "Effective_TQQQ_Weight",
            "Effective_Alpha_Weight",

            "Turnover",

            "Base_TCA_bps",
            "Impact_Cost_bps",
            "Total_Cost_bps",

            "Gross_Return",
            "Net_Return",

            "End_Wealth",

            "Post_Posterior_TQQQ_Weight",
            "Post_Posterior_Alpha_Weight",

            "Effective_Experts",
            "Largest_Expert_Posterior_Pct",
        ]
    ]
    .round(
        6
    )
)


# ==============================================================================
# 39. OUTPUT — LAST 10 ALPHA EVENTS
# ==============================================================================

print(
    "\n6) LAST 10 STOCK-SLEEVE GROSS EVENTS VS TQQQ"
)


display(
    V10_STOCK_SLEEVE_GROSS_AUDIT
    .tail(
        10
    )
    .round(
        6
    )
)


# ==============================================================================
# 40. OUTPUT — FINAL POSTERIOR
# ==============================================================================

print(
    "\n7) FINAL CAUSAL UNIVERSAL POSTERIOR"
)


V10_FINAL_POSTERIOR_TABLE = pd.DataFrame(
    {
        "Sleeve": [
            "TQQQ",
            "V10_ALPHA",
        ],

        "Weight_Pct": [
            100.0
            *
            V10_FINAL_POSTERIOR_TQQQ,

            100.0
            *
            V10_FINAL_POSTERIOR_ALPHA,
        ],
    }
)


display(
    V10_FINAL_POSTERIOR_TABLE.round(
        6
    )
)


# ==============================================================================
# 41. OUTPUT — HINDSIGHT CONSTANT MIX
# ==============================================================================

print(
    "\n8) BEST CONSTANT MIX — HINDSIGHT DIAGNOSTIC ONLY"
)


V10_BEST_CONSTANT_TABLE = pd.DataFrame(
    {
        "Sleeve": [
            "TQQQ",
            "V10_ALPHA",
        ],

        "Weight_Pct": [
            100.0
            *
            V10_BEST_CONSTANT_TQQQ_WEIGHT,

            100.0
            *
            V10_BEST_CONSTANT_ALPHA_WEIGHT,
        ],
    }
)


display(
    V10_BEST_CONSTANT_TABLE.round(
        6
    )
)


print(
    "Best constant wealth:",
    f"{V10_BEST_CONSTANT_WEALTH:.6f}",
)


print(
    "THIS IS EX-POST DIAGNOSTIC ONLY AND MUST NEVER "
    "BECOME A V10 PARAMETER."
)


# ==============================================================================
# 42. OUTPUT — FINAL EXECUTED PORTFOLIO
# ==============================================================================

print(
    "\n9) FINAL EXECUTED V10 PORTFOLIO"
)

print(
    "Execution date:",
    V10_LAST_EXECUTION_DATE.date(),
)


display(
    V10_FINAL_EXECUTED_TARGET_TABLE
    .head(
        50
    )
    .round(
        6
    )
)


# ==============================================================================
# 43. OUTPUT — DAILY NAV VALIDATION
# ==============================================================================

print(
    "\n10) DAILY NAV VALIDATION"
)


V10_DAILY_NAV_VALIDATION = pd.DataFrame(
    {
        "Metric": [

            "Daily observations",

            "First daily NAV date",

            "Last daily NAV date",

            "V10 terminal NAV",

            "V10 event terminal wealth",

            "V10 terminal error",

            "TQQQ terminal NAV",

            "TQQQ benchmark terminal wealth",

            "TQQQ terminal error",
        ],

        "Value": [

            len(
                V10_DAILY_COMPARISON
            ),

            V10_DAILY_COMPARISON
            .index[
                0
            ],

            V10_DAILY_COMPARISON
            .index[
                -1
            ],

            float(
                V10_DAILY_COMPARISON[
                    "V10"
                ]
                .iloc[
                    -1
                ]
            ),

            V10_FINAL_WEALTH,

            V10_DAILY_FINAL_ERROR,

            float(
                V10_DAILY_COMPARISON[
                    "TQQQ"
                ]
                .iloc[
                    -1
                ]
            ),

            V10_TQQQ_FINAL_WEALTH,

            V10_TQQQ_DAILY_FINAL_ERROR,
        ],
    }
)


display(
    V10_DAILY_NAV_VALIDATION
)


# ==============================================================================
# 44. FINAL STATUS
# ==============================================================================

print(
    "\n11) V10 BLOCK 3 RESEARCH FINGERPRINT"
)

print(
    V10_BLOCK3_RESEARCH_FINGERPRINT
)


print(
    "\nRESEARCH VERDICT:"
)

print(
    "V10 beats TQQQ full history :",
    V10_FULL_HISTORY_PASS,
)

print(
    "V10 beats TQQQ all windows  :",
    V10_ALL_WINDOWS_PASS,
)

print(
    "Failed windows               :",
    V10_FAILED_WINDOWS,
)

print(
    "V10 result                   :",
    V10_RESEARCH_VERDICT,
)


print(
    "\nINTEGRITY:"
)

print(
    "[+] No classifier was refitted."
)

print(
    "[+] Block 2 probabilities were used unchanged."
)

print(
    "[+] Seven-horizon median probability was preserved."
)

print(
    "[+] Probability break-even remained exactly 0.50."
)

print(
    "[+] No horizon was removed."
)

print(
    "[+] No horizon was performance-weighted."
)

print(
    "[+] No minimum stock weight."
)

print(
    "[+] No maximum stock weight."
)

print(
    "[+] No Top-K rule."
)

print(
    "[+] No sector cap."
)

print(
    "[+] No risk cap."
)

print(
    "[+] No TQQQ floor."
)

print(
    "[+] No alpha cap."
)

print(
    "[+] No strategic cash."
)

print(
    "[+] No leverage above 100%."
)

print(
    "[+] Universal allocation used only prior completed events."
)

print(
    "[+] Execution costs were computed at underlying-asset level."
)

print(
    "[+] Nonlinear liquidity / market impact was included."
)

print(
    "[+] Daily NAV reconciles exactly to event terminal wealth."
)

print(
    "[+] All acceptance windows were declared before performance."
)


print(
    "\nFINAL RULE:"
)

print(
    "DO NOT MODIFY V10 AFTER OBSERVING THIS RESULT."
)


print(
    "If V10 passes FULL + ALL WINDOWS, freeze it as a research challenger."
)

print(
    "Otherwise reject V10 as designed and treat any new hypothesis as V11."
)


print("=" * 140)
restored_register('V10', V10_FINAL_WEALTH, V10_UNIVERSAL_PATH, 'End_Wealth', 'Close / original linear + impact costs', 'Historically rejected')
