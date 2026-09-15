# MODULE 28 — V9 COST-AWARE STOCK SLEEVE
# Run in the same notebook, in module order.

# ==============================================================================
# V9 — BLOCK 2B
# COST-AWARE STOCK-SLEEVE CONSTRUCTION
# USING FROZEN / CACHED MULTI-HORIZON PREDICTIONS
# ==============================================================================
#
# IMPORTANT
# ---------
# NO MODEL IS FIT IN THIS BLOCK.
#
# V9 alpha predictions are already fixed by Block 2A.
#
# PRIMARY STOCK-SLEEVE OBJECTIVE
# ------------------------------
# Maximize predicted TQQQ-relative log-wealth growth
# net of:
#
#   1. Base linear transaction cost
#   2. Nonlinear liquidity / market-impact cost
#
#
# OPTIMIZATION
# ------------
#
# maximize:
#
#       sum_i mu_i * w_i
#
#       - c * sum_i |w_i - p_i|
#
#       - sum_i a_i * |w_i - p_i|^(3/2)
#
#
# subject to:
#
#       w_i >= 0
#       sum_i w_i = 1
#
#
# where:
#
#   mu_i = predicted 21-session TQQQ-relative log-growth
#   p_i  = pre-trade drifted portfolio weight
#   c    = base transaction-cost rate
#   a_i  = volatility / liquidity market-impact scale
#
#
# THERE IS NO:
#   - minimum stock weight
#   - maximum stock weight
#   - sector cap
#   - Top-K rule
#   - volatility target
#   - risk cap
#   - cash allocation
#
#
# A 100% single-stock solution is mathematically allowed.
#
# The only upper bound is the natural long-only simplex:
#
#       0 <= w_i <= 1
#
# which is NOT an externally imposed position cap.
#
#
# TERMINAL-DATE CONVENTION
# ------------------------
# The final 2026-07-27 rebalance is executed and therefore incurs
# transaction cost even though no subsequent holding-period return
# is observed inside the research window.
#
# This matches a terminal-wealth objective measured after execution.
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

V9_B2B_REQUIRED = [
    "V9_ALPHA_PREDICTIONS",
    "V9_MODEL_PANEL",
    "V9_LIFECYCLE_PANEL",
    "V9_PRICE_LOOKUP",
    "V9_TQQQ_PRICE_BY_DATE",
    "V9_EVALUATION_CALENDAR",
    "V9_TARGET_HORIZONS",
    "V9_ALPHA_SPEC_FINGERPRINT",
    "V9_CONTRACT_FINGERPRINT",
    "V9_REFERENCE_AUM_USD",
    "V9_BASE_TCA_RATE",
    "V9_IMPACT_COEFFICIENT",
]


V9_B2B_MISSING = [
    name
    for name in V9_B2B_REQUIRED
    if name not in globals()
]


if V9_B2B_MISSING:

    raise RuntimeError(
        "V9 Block 2B is missing required objects: "
        f"{V9_B2B_MISSING}"
    )


print("=" * 132)
print("V9 — BLOCK 2B")
print("COST-AWARE STOCK-SLEEVE CONSTRUCTION")
print("=" * 132)

print("\nNO MODEL FITTING WILL OCCUR IN THIS BLOCK.")


# ==============================================================================
# 1. STRICT PREDICTION INTEGRITY
# ==============================================================================

V9_ALPHA_PREDICTIONS = (
    V9_ALPHA_PREDICTIONS
    .copy()
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


V9_ALPHA_PREDICTIONS["Date"] = (
    pd.to_datetime(
        V9_ALPHA_PREDICTIONS["Date"]
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V9_ALPHA_PREDICTIONS[
    "Execution_Date"
] = (
    pd.to_datetime(
        V9_ALPHA_PREDICTIONS[
            "Execution_Date"
        ]
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V9_ALPHA_PREDICTIONS["Ticker"] = (
    V9_ALPHA_PREDICTIONS["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


if V9_ALPHA_PREDICTIONS.duplicated(
    [
        "Date",
        "Ticker",
    ]
).any():

    raise RuntimeError(
        "Duplicate V9 prediction ticker-date rows detected."
    )


V9_B2B_SIGNAL_DATES = (
    V9_ALPHA_PREDICTIONS[
        "Date"
    ]
    .drop_duplicates()
    .sort_values()
    .tolist()
)


if len(V9_B2B_SIGNAL_DATES) != 34:

    raise RuntimeError(
        "Unexpected number of V9 prediction dates: "
        f"{len(V9_B2B_SIGNAL_DATES)}"
    )


prediction_required_columns = [
    "Date",
    "Execution_Date",
    "Ticker",
    "Expected_Relative_Log_Growth_21",
    "Median_Dollar_Volume_60",
    "V9_Realized_Vol_60",
    "V9_Full_AUM_Impact_Scale",
]


missing_prediction_columns = [
    column
    for column in prediction_required_columns
    if column not in V9_ALPHA_PREDICTIONS.columns
]


if missing_prediction_columns:

    raise RuntimeError(
        "V9 predictions are missing columns: "
        f"{missing_prediction_columns}"
    )


# ==============================================================================
# 2. BUILD FAST EXACT PRICE LOOKUP
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


def v9b_exact_price(
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

        value = V9_PRICE_LOOKUP.loc[
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
# 3. BUILD LIFECYCLE EXECUTION-STATE LOOKUP
# ==============================================================================

V9_EXECUTION_STATE_LOOKUP = (
    V9_LIFECYCLE_PANEL[
        [
            "Ticker",
            "Date",
            "Median_Dollar_Volume_60",
            "V9_Realized_Vol_60",
        ]
    ]
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
    )
    .sort_index()
)


def v9b_impact_scale_from_state(
    ticker,
    signal_date,
):

    ticker = str(
        ticker
    ).upper().strip()

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    try:

        state = V9_EXECUTION_STATE_LOOKUP.loc[
            (
                ticker,
                signal_date,
            )
        ]

    except KeyError:

        return np.nan


    if isinstance(
        state,
        pd.DataFrame,
    ):

        state = state.iloc[-1]


    sigma = float(
        state[
            "V9_Realized_Vol_60"
        ]
    )


    adv = float(
        state[
            "Median_Dollar_Volume_60"
        ]
    )


    if (
        not np.isfinite(sigma)
        or
        not np.isfinite(adv)
        or
        adv <= 0
        or
        sigma < 0
    ):

        return np.nan


    return (
        V9_IMPACT_COEFFICIENT
        *
        sigma
        *
        np.sqrt(
            V9_REFERENCE_AUM_USD
            /
            adv
        )
    )


# ==============================================================================
# 4. PRE-PORTFOLIO EXACT-QUOTE VALIDATION
# ==============================================================================
#
# This runs before optimization.
#
# Every prediction candidate must have:
#
#   - an exact entry quote
#   - an exact next-rebalance quote when a later rebalance exists
#
# ==============================================================================

V9_B2B_QUOTE_AUDIT_ROWS = []


for event_number, signal_date in enumerate(
    V9_B2B_SIGNAL_DATES,
    start=1,
):

    section = (
        V9_ALPHA_PREDICTIONS[
            V9_ALPHA_PREDICTIONS[
                "Date"
            ]
            ==
            signal_date
        ]
    )


    execution_dates = (
        section[
            "Execution_Date"
        ]
        .dropna()
        .unique()
    )


    if len(execution_dates) != 1:

        raise RuntimeError(
            "A signal date does not map to exactly one "
            f"execution date: {signal_date}"
        )


    execution_date = pd.Timestamp(
        execution_dates[0]
    )


    if event_number < len(
        V9_B2B_SIGNAL_DATES
    ):

        next_signal_date = pd.Timestamp(
            V9_B2B_SIGNAL_DATES[
                event_number
            ]
        )


        next_section = (
            V9_ALPHA_PREDICTIONS[
                V9_ALPHA_PREDICTIONS[
                    "Date"
                ]
                ==
                next_signal_date
            ]
        )


        next_execution_date = pd.Timestamp(
            next_section[
                "Execution_Date"
            ].iloc[0]
        )

    else:

        next_execution_date = execution_date


    tickers = (
        section[
            "Ticker"
        ]
        .drop_duplicates()
        .tolist()
    )


    entry_missing = 0
    exit_missing = 0


    for ticker in tickers:

        if not np.isfinite(
            v9b_exact_price(
                ticker,
                execution_date,
            )
        ):

            entry_missing += 1


        if not np.isfinite(
            v9b_exact_price(
                ticker,
                next_execution_date,
            )
        ):

            exit_missing += 1


    V9_B2B_QUOTE_AUDIT_ROWS.append(
        {
            "Event":
                event_number,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                next_execution_date,

            "Prediction_Candidates":
                len(
                    tickers
                ),

            "Missing_Entry_Quotes":
                entry_missing,

            "Missing_Exit_Quotes":
                exit_missing,
        }
    )


V9_B2B_QUOTE_AUDIT = pd.DataFrame(
    V9_B2B_QUOTE_AUDIT_ROWS
)


if (
    V9_B2B_QUOTE_AUDIT[
        "Missing_Entry_Quotes"
    ].sum()
    !=
    0
    or
    V9_B2B_QUOTE_AUDIT[
        "Missing_Exit_Quotes"
    ].sum()
    !=
    0
):

    display(
        V9_B2B_QUOTE_AUDIT
    )

    raise RuntimeError(
        "Block 2B exact-price preflight failed. "
        "No portfolio performance was calculated."
    )


print(
    "\n[+] Block 2B exact-price preflight passed."
)


# ==============================================================================
# 5. FREEZE THE BLOCK 2B PORTFOLIO SPECIFICATION
# ==============================================================================

V9_STOCK_SLEEVE_SPEC = {

    "alpha_spec_fingerprint":
        V9_ALPHA_SPEC_FINGERPRINT,

    "contract_fingerprint":
        V9_CONTRACT_FINGERPRINT,

    "objective":
        (
            "MAX_PREDICTED_TQQQ_RELATIVE_LOG_GROWTH_"
            "MINUS_LINEAR_TCA_MINUS_SQRT_MARKET_IMPACT"
        ),

    "constraint":
        "LONG_ONLY_FULLY_INVESTED_SIMPLEX",

    "minimum_stock_weight":
        None,

    "maximum_stock_weight":
        None,

    "sector_cap":
        None,

    "top_k":
        None,

    "risk_cap":
        None,

    "cash_allowed":
        False,

    "base_tca_rate":
        float(
            V9_BASE_TCA_RATE
        ),

    "reference_aum_usd":
        float(
            V9_REFERENCE_AUM_USD
        ),

    "market_impact":
        (
            "SIGMA60_X_SQRT_AUM_OVER_ADV60_"
            "X_ABS_DELTA_WEIGHT_POWER_1P5"
        ),

    "impact_coefficient":
        float(
            V9_IMPACT_COEFFICIENT
        ),

    "rebalance_frequency":
        "21_SESSIONS",

    "terminal_rebalance_cost_included":
        True,

    "future_availability_filter":
        False,
}


V9_STOCK_SLEEVE_SPEC_STRING = json.dumps(
    V9_STOCK_SLEEVE_SPEC,
    sort_keys=True,
    default=str,
)


V9_STOCK_SLEEVE_SPEC_FINGERPRINT = (
    hashlib.sha256(
        V9_STOCK_SLEEVE_SPEC_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


print(
    "\nV9 stock-sleeve specification fingerprint:"
)

print(
    V9_STOCK_SLEEVE_SPEC_FINGERPRINT
)


# ==============================================================================
# 6. ANALYTIC COST-AWARE SIMPLEX SOLVER
# ==============================================================================
#
# Convex cost / concave objective.
#
# For a given Lagrange multiplier lambda, every asset has a closed-form
# optimal move around its drifted pre-trade weight.
#
# We solve lambda by bisection so that:
#
#       sum_i w_i = 1
#
# ==============================================================================

def v9b_cost_aware_simplex_solver(
    expected_growth,
    previous_weights,
    impact_scale,
    base_cost,
):

    mu = np.asarray(
        expected_growth,
        dtype=float,
    )


    previous = np.asarray(
        previous_weights,
        dtype=float,
    )


    impact = np.asarray(
        impact_scale,
        dtype=float,
    )


    if not (
        len(mu)
        ==
        len(previous)
        ==
        len(impact)
    ):

        raise ValueError(
            "Optimizer vectors have inconsistent lengths."
        )


    if len(mu) == 0:

        raise ValueError(
            "Optimizer received an empty candidate set."
        )


    if (
        not np.all(
            np.isfinite(mu)
        )
        or
        not np.all(
            np.isfinite(previous)
        )
        or
        not np.all(
            np.isfinite(impact)
        )
    ):

        raise ValueError(
            "Optimizer received non-finite input."
        )


    previous = np.maximum(
        previous,
        0.0,
    )


    impact = np.maximum(
        impact,
        1e-12,
    )


    base_cost = float(
        base_cost
    )


    def weights_at_lambda(
        lagrange_multiplier,
    ):

        relative_mu = (
            mu
            -
            lagrange_multiplier
        )


        weights = previous.copy()


        # ----------------------------------------------------------------------
        # BUY REGION
        # ----------------------------------------------------------------------

        buy_mask = (
            relative_mu
            >
            base_cost
        )


        if buy_mask.any():

            buy_capacity = (
                1.0
                -
                previous[
                    buy_mask
                ]
            )


            buy_ratio = (
                (
                    relative_mu[
                        buy_mask
                    ]
                    -
                    base_cost
                )
                /
                (
                    1.5
                    *
                    impact[
                        buy_mask
                    ]
                )
            )


            buy_ratio = np.maximum(
                buy_ratio,
                0.0,
            )


            # Avoid numerical overflow:
            # delta can never exceed remaining simplex capacity.

            max_ratio = np.sqrt(
                np.maximum(
                    buy_capacity,
                    0.0,
                )
            )


            buy_ratio = np.minimum(
                buy_ratio,
                max_ratio,
            )


            buy_delta = (
                buy_ratio ** 2
            )


            weights[
                buy_mask
            ] = (
                previous[
                    buy_mask
                ]
                +
                buy_delta
            )


        # ----------------------------------------------------------------------
        # SELL REGION
        # ----------------------------------------------------------------------

        sell_mask = (
            relative_mu
            <
            -base_cost
        )


        if sell_mask.any():

            sell_capacity = (
                previous[
                    sell_mask
                ]
            )


            sell_ratio = (
                (
                    -relative_mu[
                        sell_mask
                    ]
                    -
                    base_cost
                )
                /
                (
                    1.5
                    *
                    impact[
                        sell_mask
                    ]
                )
            )


            sell_ratio = np.maximum(
                sell_ratio,
                0.0,
            )


            max_ratio = np.sqrt(
                np.maximum(
                    sell_capacity,
                    0.0,
                )
            )


            sell_ratio = np.minimum(
                sell_ratio,
                max_ratio,
            )


            sell_delta = (
                sell_ratio ** 2
            )


            weights[
                sell_mask
            ] = (
                previous[
                    sell_mask
                ]
                -
                sell_delta
            )


        weights = np.clip(
            weights,
            0.0,
            1.0,
        )


        return weights


    # ==========================================================================
    # BRACKET THE LAGRANGE MULTIPLIER
    # ==========================================================================

    scale = max(
        1.0,
        float(
            np.max(
                np.abs(mu)
            )
        )
        *
        100.0,
    )


    lower = (
        float(
            np.min(mu)
        )
        -
        scale
    )


    upper = (
        float(
            np.max(mu)
        )
        +
        scale
    )


    for _ in range(100):

        if (
            weights_at_lambda(
                lower
            ).sum()
            >=
            1.0
        ):

            break

        lower -= scale
        scale *= 2.0


    scale = max(
        1.0,
        float(
            np.max(
                np.abs(mu)
            )
        )
        *
        100.0,
    )


    for _ in range(100):

        if (
            weights_at_lambda(
                upper
            ).sum()
            <=
            1.0
        ):

            break

        upper += scale
        scale *= 2.0


    # ==========================================================================
    # BISECTION
    # ==========================================================================

    for _ in range(160):

        middle = (
            lower
            +
            upper
        ) / 2.0


        candidate = (
            weights_at_lambda(
                middle
            )
        )


        total_weight = float(
            candidate.sum()
        )


        if total_weight > 1.0:

            lower = middle

        else:

            upper = middle


    final_lambda = (
        lower
        +
        upper
    ) / 2.0


    weights = (
        weights_at_lambda(
            final_lambda
        )
    )


    total_weight = float(
        weights.sum()
    )


    if (
        not np.isfinite(
            total_weight
        )
        or
        total_weight <= 0
    ):

        raise RuntimeError(
            "V9 simplex solver failed to produce "
            "a valid portfolio."
        )


    # Pure floating-point normalization only.

    weights = (
        weights
        /
        total_weight
    )


    if abs(
        weights.sum()
        -
        1.0
    ) > 1e-10:

        raise RuntimeError(
            "V9 simplex normalization failed."
        )


    if (
        weights < -1e-12
    ).any():

        raise RuntimeError(
            "V9 simplex generated a negative weight."
        )


    return (
        weights,
        final_lambda,
    )


# ==============================================================================
# 7. DRIFT HELPER
# ==============================================================================

def v9b_drift_weights(
    target_weights,
    start_date,
    end_date,
):

    if not target_weights:

        return {}


    start_date = pd.Timestamp(
        start_date
    )


    end_date = pd.Timestamp(
        end_date
    )


    drifted_values = {}


    for ticker, weight in (
        target_weights.items()
    ):

        start_price = v9b_exact_price(
            ticker,
            start_date,
        )


        end_price = v9b_exact_price(
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
                "Exact lifecycle quote missing while "
                f"drifting existing holding {ticker}: "
                f"{start_date.date()} -> "
                f"{end_date.date()}."
            )


        drifted_values[
            ticker
        ] = (
            float(weight)
            *
            end_price
            /
            start_price
        )


    total_value = float(
        sum(
            drifted_values.values()
        )
    )


    if (
        not np.isfinite(
            total_value
        )
        or
        total_value <= 0
    ):

        raise RuntimeError(
            "Invalid drifted portfolio value."
        )


    return {
        ticker:
            value
            /
            total_value

        for ticker, value
        in drifted_values.items()
    }


# ==============================================================================
# 8. BUILD COST-AWARE STOCK-SLEEVE TARGETS
# ==============================================================================

V9_STOCK_SLEEVE_TARGETS = {}

V9_STOCK_SLEEVE_DECISION_ROWS = []


previous_target = {}

previous_execution_date = None


for event_number, signal_date in enumerate(
    V9_B2B_SIGNAL_DATES,
    start=1,
):

    signal_date = pd.Timestamp(
        signal_date
    )


    section = (
        V9_ALPHA_PREDICTIONS[
            V9_ALPHA_PREDICTIONS[
                "Date"
            ]
            ==
            signal_date
        ]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=[
                "Execution_Date",
                "Expected_Relative_Log_Growth_21",
                "Median_Dollar_Volume_60",
                "V9_Realized_Vol_60",
                "V9_Full_AUM_Impact_Scale",
            ]
        )
        .drop_duplicates(
            "Ticker",
            keep="last",
        )
        .copy()
    )


    if section.empty:

        raise RuntimeError(
            "V9 has no usable predictions for "
            f"{signal_date.date()}."
        )


    execution_date = pd.Timestamp(
        section[
            "Execution_Date"
        ].iloc[0]
    )


    if (
        section[
            "Execution_Date"
        ].nunique()
        !=
        1
    ):

        raise RuntimeError(
            "Multiple execution dates found for "
            f"{signal_date.date()}."
        )


    # --------------------------------------------------------------------------
    # Drift previous holdings to current execution date.
    # --------------------------------------------------------------------------

    if not previous_target:

        drifted_previous = {}

    else:

        drifted_previous = (
            v9b_drift_weights(
                target_weights=previous_target,
                start_date=previous_execution_date,
                end_date=execution_date,
            )
        )


    section = (
        section
        .set_index(
            "Ticker"
        )
        .sort_index()
    )


    current_assets = (
        section.index.tolist()
    )


    current_asset_set = set(
        current_assets
    )


    # --------------------------------------------------------------------------
    # Existing holdings that are no longer current candidates.
    #
    # They are forced exits at THIS execution date.
    # Their future disappearance was NOT used ex ante.
    # --------------------------------------------------------------------------

    forced_exit_assets = [
        ticker
        for ticker
        in drifted_previous
        if ticker
        not in current_asset_set
    ]


    forced_exit_weight = float(
        sum(
            drifted_previous[
                ticker
            ]
            for ticker
            in forced_exit_assets
        )
    )


    previous_array = np.array(
        [
            drifted_previous.get(
                ticker,
                0.0,
            )
            for ticker
            in current_assets
        ],
        dtype=float,
    )


    mu = (
        section[
            "Expected_Relative_Log_Growth_21"
        ]
        .to_numpy(
            dtype=float
        )
    )


    impact_array = (
        section[
            "V9_Full_AUM_Impact_Scale"
        ]
        .to_numpy(
            dtype=float
        )
    )


    # --------------------------------------------------------------------------
    # Solve the current long-only fully-invested stock sleeve.
    # --------------------------------------------------------------------------

    (
        optimized_weights,
        lagrange_multiplier,
    ) = v9b_cost_aware_simplex_solver(
        expected_growth=mu,
        previous_weights=previous_array,
        impact_scale=impact_array,
        base_cost=V9_BASE_TCA_RATE,
    )


    # 1e-15 is only numerical serialization cleanup.
    # It is NOT an economic minimum-position rule.

    target_weights = {
        ticker:
            float(weight)

        for ticker, weight
        in zip(
            current_assets,
            optimized_weights,
        )

        if (
            np.isfinite(
                weight
            )
            and
            weight > 1e-15
        )
    }


    target_sum = float(
        sum(
            target_weights.values()
        )
    )


    if abs(
        target_sum
        -
        1.0
    ) > 1e-9:

        raise RuntimeError(
            "V9 target weights do not sum to one."
        )


    # ==========================================================================
    # EXACT TURNOVER
    # ==========================================================================

    all_names = (
        set(
            drifted_previous
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
                    ticker,
                    0.0,
                )
                -
                drifted_previous.get(
                    ticker,
                    0.0,
                )
            )
            for ticker
            in all_names
        )
    )


    # ==========================================================================
    # BASE TRANSACTION COST
    # ==========================================================================

    base_cost_fraction = (
        V9_BASE_TCA_RATE
        *
        turnover
    )


    # ==========================================================================
    # NONLINEAR MARKET IMPACT
    # ==========================================================================

    impact_cost_fraction = 0.0


    # --------------------------------------------------------------------------
    # Current candidate trades
    # --------------------------------------------------------------------------

    for ticker in current_assets:

        delta = abs(
            target_weights.get(
                ticker,
                0.0,
            )
            -
            drifted_previous.get(
                ticker,
                0.0,
            )
        )


        if delta <= 0:

            continue


        scale = float(
            section.loc[
                ticker,
                "V9_Full_AUM_Impact_Scale",
            ]
        )


        if (
            not np.isfinite(
                scale
            )
            or
            scale < 0
        ):

            raise RuntimeError(
                "Invalid impact scale for "
                f"{ticker} at "
                f"{signal_date.date()}."
            )


        impact_cost_fraction += (
            scale
            *
            (
                delta ** 1.5
            )
        )


    # --------------------------------------------------------------------------
    # Forced exits from former holdings
    # --------------------------------------------------------------------------

    for ticker in forced_exit_assets:

        delta = float(
            drifted_previous[
                ticker
            ]
        )


        scale = (
            v9b_impact_scale_from_state(
                ticker=ticker,
                signal_date=signal_date,
            )
        )


        if (
            not np.isfinite(
                scale
            )
            or
            scale < 0
        ):

            raise RuntimeError(
                "Missing causal execution state for "
                f"forced exit {ticker} at "
                f"{signal_date.date()}."
            )


        impact_cost_fraction += (
            scale
            *
            (
                delta ** 1.5
            )
        )


    total_cost_fraction = (
        base_cost_fraction
        +
        impact_cost_fraction
    )


    if (
        not np.isfinite(
            total_cost_fraction
        )
        or
        total_cost_fraction < 0
        or
        total_cost_fraction >= 1.0
    ):

        raise RuntimeError(
            "Invalid modeled V9 execution cost."
        )


    # ==========================================================================
    # PREDICTED PORTFOLIO ECONOMICS
    # ==========================================================================

    expected_gross_relative_log_growth = float(
        np.dot(
            optimized_weights,
            mu,
        )
    )


    expected_net_objective = (
        expected_gross_relative_log_growth
        -
        total_cost_fraction
    )


    # ==========================================================================
    # CONCENTRATION DIAGNOSTICS
    # ==========================================================================

    target_array = np.asarray(
        list(
            target_weights.values()
        ),
        dtype=float,
    )


    effective_n = float(
        1.0
        /
        np.sum(
            target_array ** 2
        )
    )


    max_name_weight = float(
        np.max(
            target_array
        )
    )


    top_ticker = max(
        target_weights,
        key=target_weights.get,
    )


    V9_STOCK_SLEEVE_TARGETS[
        execution_date
    ] = dict(
        target_weights
    )


    V9_STOCK_SLEEVE_DECISION_ROWS.append(
        {
            "Event":
                event_number,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Candidate_Names":
                len(
                    current_assets
                ),

            "Held_Names":
                len(
                    target_weights
                ),

            "Forced_Exit_Names":
                len(
                    forced_exit_assets
                ),

            "Forced_Exit_Weight_Pct":
                100.0
                *
                forced_exit_weight,

            "Turnover":
                turnover,

            "Base_TCA_bps":
                10000.0
                *
                base_cost_fraction,

            "Impact_Cost_bps":
                10000.0
                *
                impact_cost_fraction,

            "Total_Execution_Cost_bps":
                10000.0
                *
                total_cost_fraction,

            "Expected_Gross_Relative_Log_Growth_21":
                expected_gross_relative_log_growth,

            "Expected_Net_Objective":
                expected_net_objective,

            "Effective_N":
                effective_n,

            "Max_Name_Weight_Pct":
                100.0
                *
                max_name_weight,

            "Largest_Position":
                top_ticker,

            "Lagrange_Multiplier":
                lagrange_multiplier,

            "Weights":
                dict(
                    target_weights
                ),
        }
    )


    previous_target = dict(
        target_weights
    )


    previous_execution_date = (
        execution_date
    )


V9_STOCK_SLEEVE_DECISIONS = (
    pd.DataFrame(
        V9_STOCK_SLEEVE_DECISION_ROWS
    )
    .sort_values(
        "Execution_Date"
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 9. REALIZED EVENT RETURNS
# ==============================================================================

V9_STOCK_SLEEVE_REALIZED_ROWS = []


for event_index in range(
    len(
        V9_STOCK_SLEEVE_DECISIONS
    )
):

    event = (
        V9_STOCK_SLEEVE_DECISIONS
        .iloc[
            event_index
        ]
    )


    execution_date = pd.Timestamp(
        event[
            "Execution_Date"
        ]
    )


    # Final rebalance is included at terminal date.

    if (
        event_index
        <
        len(
            V9_STOCK_SLEEVE_DECISIONS
        )
        -
        1
    ):

        exit_date = pd.Timestamp(
            V9_STOCK_SLEEVE_DECISIONS
            .iloc[
                event_index + 1
            ][
                "Execution_Date"
            ]
        )

    else:

        exit_date = execution_date


    weights = (
        event[
            "Weights"
        ]
    )


    gross_multiplier = 0.0


    for ticker, weight in (
        weights.items()
    ):

        start_price = (
            v9b_exact_price(
                ticker,
                execution_date,
            )
        )


        end_price = (
            v9b_exact_price(
                ticker,
                exit_date,
            )
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
                "Missing realized lifecycle price for "
                f"{ticker}: "
                f"{execution_date.date()} -> "
                f"{exit_date.date()}."
            )


        gross_multiplier += (
            float(weight)
            *
            end_price
            /
            start_price
        )


    cost_fraction = (
        float(
            event[
                "Total_Execution_Cost_bps"
            ]
        )
        /
        10000.0
    )


    net_multiplier = (
        (
            1.0
            -
            cost_fraction
        )
        *
        gross_multiplier
    )


    tqqq_start = float(
        V9_TQQQ_PRICE_BY_DATE.loc[
            execution_date
        ]
    )


    tqqq_end = float(
        V9_TQQQ_PRICE_BY_DATE.loc[
            exit_date
        ]
    )


    tqqq_gross_multiplier = (
        tqqq_end
        /
        tqqq_start
    )


    # TQQQ buy-and-hold pays the base entry cost only once.

    if event_index == 0:

        tqqq_net_multiplier = (
            (
                1.0
                -
                V9_BASE_TCA_RATE
            )
            *
            tqqq_gross_multiplier
        )

    else:

        tqqq_net_multiplier = (
            tqqq_gross_multiplier
        )


    relative_multiplier = (
        net_multiplier
        /
        tqqq_net_multiplier
    )


    V9_STOCK_SLEEVE_REALIZED_ROWS.append(
        {
            "Event":
                int(
                    event[
                        "Event"
                    ]
                ),

            "Signal_Date":
                event[
                    "Signal_Date"
                ],

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Gross_Return":
                gross_multiplier
                -
                1.0,

            "Net_Return":
                net_multiplier
                -
                1.0,

            "TQQQ_Net_Return":
                tqqq_net_multiplier
                -
                1.0,

            "Net_Excess_pp":
                100.0
                *
                (
                    net_multiplier
                    -
                    tqqq_net_multiplier
                ),

            "Relative_Multiplier":
                relative_multiplier,

            "Turnover":
                event[
                    "Turnover"
                ],

            "Base_TCA_bps":
                event[
                    "Base_TCA_bps"
                ],

            "Impact_Cost_bps":
                event[
                    "Impact_Cost_bps"
                ],

            "Execution_Cost_bps":
                event[
                    "Total_Execution_Cost_bps"
                ],

            "Held_Names":
                event[
                    "Held_Names"
                ],

            "Effective_N":
                event[
                    "Effective_N"
                ],

            "Max_Name_Weight_Pct":
                event[
                    "Max_Name_Weight_Pct"
                ],

            "Largest_Position":
                event[
                    "Largest_Position"
                ],
        }
    )


V9_STOCK_SLEEVE_REALIZED = (
    pd.DataFrame(
        V9_STOCK_SLEEVE_REALIZED_ROWS
    )
)


# ==============================================================================
# 10. COMPOUND EXACT EVENT WEALTH
# ==============================================================================

V9_STOCK_SLEEVE_REALIZED[
    "Sleeve_Wealth"
] = (
    1.0
    +
    V9_STOCK_SLEEVE_REALIZED[
        "Net_Return"
    ]
).cumprod()


V9_STOCK_SLEEVE_REALIZED[
    "TQQQ_Wealth"
] = (
    1.0
    +
    V9_STOCK_SLEEVE_REALIZED[
        "TQQQ_Net_Return"
    ]
).cumprod()


V9_STOCK_SLEEVE_REALIZED[
    "Relative_Wealth"
] = (
    V9_STOCK_SLEEVE_REALIZED[
        "Sleeve_Wealth"
    ]
    /
    V9_STOCK_SLEEVE_REALIZED[
        "TQQQ_Wealth"
    ]
)


V9_STOCK_SLEEVE_FINAL_WEALTH = float(
    V9_STOCK_SLEEVE_REALIZED[
        "Sleeve_Wealth"
    ].iloc[-1]
)


V9_STOCK_SLEEVE_TQQQ_WEALTH = float(
    V9_STOCK_SLEEVE_REALIZED[
        "TQQQ_Wealth"
    ].iloc[-1]
)


V9_STOCK_SLEEVE_RELATIVE_WEALTH = float(
    V9_STOCK_SLEEVE_REALIZED[
        "Relative_Wealth"
    ].iloc[-1]
)


# ==============================================================================
# 11. TRANSACTION-COST COUNTERFACTUAL
# ==============================================================================

V9_STOCK_SLEEVE_REALIZED[
    "Gross_Wealth_No_Execution_Cost"
] = (
    1.0
    +
    V9_STOCK_SLEEVE_REALIZED[
        "Gross_Return"
    ]
).cumprod()


V9_STOCK_SLEEVE_GROSS_WEALTH = float(
    V9_STOCK_SLEEVE_REALIZED[
        "Gross_Wealth_No_Execution_Cost"
    ].iloc[-1]
)


V9_STOCK_SLEEVE_EXECUTION_WEALTH_DRAG_PP = (
    100.0
    *
    (
        V9_STOCK_SLEEVE_GROSS_WEALTH
        -
        V9_STOCK_SLEEVE_FINAL_WEALTH
    )
)


# ==============================================================================
# 12. STRICT OOS CROSS-SECTIONAL IC DIAGNOSTIC
# ==============================================================================

V9_HORIZON_IC_ROWS = []


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    prediction_column = (
        f"Pred_PerSession_{horizon_name}"
    )


    target_column = (
        f"Log_Relative_Wealth_{horizon_name}"
    )


    if (
        prediction_column
        not in V9_ALPHA_PREDICTIONS.columns
    ):

        raise RuntimeError(
            "Missing horizon prediction column: "
            f"{prediction_column}"
        )


    realized_targets = (
        V9_MODEL_PANEL[
            [
                "Date",
                "Ticker",
                target_column,
            ]
        ]
        .drop_duplicates(
            [
                "Date",
                "Ticker",
            ],
            keep="last",
        )
    )


    ic_panel = (
        V9_ALPHA_PREDICTIONS[
            [
                "Date",
                "Ticker",
                prediction_column,
            ]
        ]
        .merge(
            realized_targets,
            on=[
                "Date",
                "Ticker",
            ],
            how="left",
            validate="one_to_one",
        )
    )


    event_ics = []


    for _, cross_section in (
        ic_panel.groupby(
            "Date"
        )
    ):

        temp = (
            cross_section[
                [
                    prediction_column,
                    target_column,
                ]
            ]
            .dropna()
        )


        if len(temp) < 100:

            continue


        ic = (
            temp[
                prediction_column
            ]
            .corr(
                temp[
                    target_column
                ],
                method="spearman",
            )
        )


        if np.isfinite(ic):

            event_ics.append(
                float(ic)
            )


    event_ics = np.asarray(
        event_ics,
        dtype=float,
    )


    V9_HORIZON_IC_ROWS.append(
        {
            "Horizon":
                horizon_name,

            "Sessions":
                horizon_sessions,

            "IC_Events":
                len(
                    event_ics
                ),

            "Mean_Spearman_IC":
                (
                    float(
                        np.mean(
                            event_ics
                        )
                    )
                    if len(
                        event_ics
                    )
                    else np.nan
                ),

            "Median_Spearman_IC":
                (
                    float(
                        np.median(
                            event_ics
                        )
                    )
                    if len(
                        event_ics
                    )
                    else np.nan
                ),

            "Positive_IC_Pct":
                (
                    100.0
                    *
                    float(
                        np.mean(
                            event_ics > 0
                        )
                    )
                    if len(
                        event_ics
                    )
                    else np.nan
                ),
        }
    )


V9_HORIZON_IC = (
    pd.DataFrame(
        V9_HORIZON_IC_ROWS
    )
    .set_index(
        "Horizon"
    )
)


# ==============================================================================
# 13. CONCENTRATION / EXECUTION SUMMARY
# ==============================================================================

V9_STOCK_SLEEVE_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Research events",
            "Stock sleeve final wealth",
            "Same-calendar TQQQ final wealth",
            "Sleeve / TQQQ relative wealth",
            "Stock sleeve net return pct",
            "TQQQ net return pct",
            "Relative wealth gain pct",
            "Sleeve beat TQQQ event pct",
            "Mean event excess pp",
            "Median event excess pp",
            "Total turnover",
            "Mean turnover",
            "Mean base TCA bps",
            "Mean market-impact cost bps",
            "Mean total execution cost bps",
            "Median total execution cost bps",
            "Total event execution-cost bps",
            "Execution wealth drag pp",
            "Mean held names",
            "Median held names",
            "Mean effective N",
            "Median effective N",
            "Mean max-name weight pct",
            "Median max-name weight pct",
            "Maximum max-name weight pct",
            "Total forced-exit names",
        ],

        "Value": [
            len(
                V9_STOCK_SLEEVE_REALIZED
            ),

            V9_STOCK_SLEEVE_FINAL_WEALTH,

            V9_STOCK_SLEEVE_TQQQ_WEALTH,

            V9_STOCK_SLEEVE_RELATIVE_WEALTH,

            100.0
            *
            (
                V9_STOCK_SLEEVE_FINAL_WEALTH
                -
                1.0
            ),

            100.0
            *
            (
                V9_STOCK_SLEEVE_TQQQ_WEALTH
                -
                1.0
            ),

            100.0
            *
            (
                V9_STOCK_SLEEVE_RELATIVE_WEALTH
                -
                1.0
            ),

            100.0
            *
            (
                V9_STOCK_SLEEVE_REALIZED[
                    "Net_Excess_pp"
                ]
                >
                0
            ).mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Net_Excess_pp"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Net_Excess_pp"
            ].median(),

            V9_STOCK_SLEEVE_REALIZED[
                "Turnover"
            ].sum(),

            V9_STOCK_SLEEVE_REALIZED[
                "Turnover"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Base_TCA_bps"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Impact_Cost_bps"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Execution_Cost_bps"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Execution_Cost_bps"
            ].median(),

            V9_STOCK_SLEEVE_REALIZED[
                "Execution_Cost_bps"
            ].sum(),

            V9_STOCK_SLEEVE_EXECUTION_WEALTH_DRAG_PP,

            V9_STOCK_SLEEVE_REALIZED[
                "Held_Names"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Held_Names"
            ].median(),

            V9_STOCK_SLEEVE_REALIZED[
                "Effective_N"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Effective_N"
            ].median(),

            V9_STOCK_SLEEVE_REALIZED[
                "Max_Name_Weight_Pct"
            ].mean(),

            V9_STOCK_SLEEVE_REALIZED[
                "Max_Name_Weight_Pct"
            ].median(),

            V9_STOCK_SLEEVE_REALIZED[
                "Max_Name_Weight_Pct"
            ].max(),

            V9_STOCK_SLEEVE_DECISIONS[
                "Forced_Exit_Names"
            ].sum(),
        ],
    }
)


# ==============================================================================
# 14. LAST TARGET PORTFOLIO
# ==============================================================================

V9_LAST_STOCK_SLEEVE_EXECUTION_DATE = max(
    V9_STOCK_SLEEVE_TARGETS
)


V9_LAST_STOCK_SLEEVE_TARGET = (
    pd.Series(
        V9_STOCK_SLEEVE_TARGETS[
            V9_LAST_STOCK_SLEEVE_EXECUTION_DATE
        ],
        name="Weight",
    )
    .sort_values(
        ascending=False
    )
)


V9_LAST_STOCK_SLEEVE_TARGET_TABLE = (
    (
        100.0
        *
        V9_LAST_STOCK_SLEEVE_TARGET
    )
    .rename(
        "Weight_Pct"
    )
    .to_frame()
)


# ==============================================================================
# 15. BLOCK 2B RESEARCH FINGERPRINT
# ==============================================================================

V9_BLOCK2B_RESULT_PAYLOAD = {

    "stock_sleeve_spec_fingerprint":
        V9_STOCK_SLEEVE_SPEC_FINGERPRINT,

    "alpha_spec_fingerprint":
        V9_ALPHA_SPEC_FINGERPRINT,

    "contract_fingerprint":
        V9_CONTRACT_FINGERPRINT,

    "events":
        len(
            V9_STOCK_SLEEVE_REALIZED
        ),

    "final_wealth":
        V9_STOCK_SLEEVE_FINAL_WEALTH,

    "tqqq_wealth":
        V9_STOCK_SLEEVE_TQQQ_WEALTH,

    "relative_wealth":
        V9_STOCK_SLEEVE_RELATIVE_WEALTH,

    "total_turnover":
        float(
            V9_STOCK_SLEEVE_REALIZED[
                "Turnover"
            ].sum()
        ),

    "last_execution_date":
        str(
            V9_LAST_STOCK_SLEEVE_EXECUTION_DATE.date()
        ),
}


V9_BLOCK2B_RESEARCH_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            V9_BLOCK2B_RESULT_PAYLOAD,
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
# 16. OUTPUT — HORIZON IC
# ==============================================================================

print(
    "\n1) MULTI-HORIZON STRICT OOS IC"
)


display(
    V9_HORIZON_IC.round(
        6
    )
)


# ==============================================================================
# 17. OUTPUT — STOCK SLEEVE SUMMARY
# ==============================================================================

print(
    "\n2) COST-AWARE STOCK-SLEEVE ECONOMIC SUMMARY"
)


display(
    V9_STOCK_SLEEVE_SUMMARY.round(
        6
    )
)


# ==============================================================================
# 18. OUTPUT — FULL DECISION AUDIT
# ==============================================================================

print(
    "\n3) FULL STOCK-SLEEVE DECISION AUDIT"
)


display(
    V9_STOCK_SLEEVE_DECISIONS[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Candidate_Names",
            "Held_Names",
            "Forced_Exit_Names",
            "Forced_Exit_Weight_Pct",
            "Turnover",
            "Base_TCA_bps",
            "Impact_Cost_bps",
            "Total_Execution_Cost_bps",
            "Expected_Gross_Relative_Log_Growth_21",
            "Expected_Net_Objective",
            "Effective_N",
            "Max_Name_Weight_Pct",
            "Largest_Position",
        ]
    ]
    .round(
        6
    )
)


# ==============================================================================
# 19. OUTPUT — LAST 10 REALIZED EVENTS
# ==============================================================================

print(
    "\n4) LAST 10 REALIZED EVENTS"
)


display(
    V9_STOCK_SLEEVE_REALIZED[
        [
            "Execution_Date",
            "Exit_Date",
            "Gross_Return",
            "Net_Return",
            "TQQQ_Net_Return",
            "Net_Excess_pp",
            "Execution_Cost_bps",
            "Turnover",
            "Held_Names",
            "Effective_N",
            "Max_Name_Weight_Pct",
            "Largest_Position",
            "Sleeve_Wealth",
            "TQQQ_Wealth",
            "Relative_Wealth",
        ]
    ]
    .tail(
        10
    )
    .round(
        6
    )
)


# ==============================================================================
# 20. OUTPUT — FINAL TARGET
# ==============================================================================

print(
    "\n5) FINAL V9 STOCK-SLEEVE TARGET"
)

print(
    "Execution date:",
    V9_LAST_STOCK_SLEEVE_EXECUTION_DATE.date(),
)


display(
    V9_LAST_STOCK_SLEEVE_TARGET_TABLE
    .head(
        40
    )
    .round(
        6
    )
)


# ==============================================================================
# 21. OUTPUT — FINAL RESEARCH STATUS
# ==============================================================================

print(
    "\n6) BLOCK 2B RESEARCH FINGERPRINT"
)

print(
    V9_BLOCK2B_RESEARCH_FINGERPRINT
)


print("\nINTEGRITY:")
print("[+] No model was refitted.")
print("[+] Cached Block 2A predictions were used unchanged.")
print("[+] No minimum stock weight.")
print("[+] No arbitrary maximum stock weight.")
print("[+] No sector cap.")
print("[+] No Top-K selection rule.")
print("[+] No risk cap.")
print("[+] No strategic cash allocation.")
print("[+] Previous holdings were drifted using exact lifecycle prices.")
print("[+] Membership exits create causal forced exits only at rebalance.")
print("[+] Linear transaction cost is included.")
print("[+] Nonlinear liquidity / market impact is included.")
print("[+] Final research-date rebalance cost is included.")

print(
    "\nIMPORTANT:"
)

print(
    "Block 2B stock-sleeve architecture is now fixed. "
    "Its observed result must NOT be used to retune the sleeve."
)

print(
    "\nNEXT:"
)

print(
    "V9 BLOCK 3 — FROZEN THREE-WAY UNIVERSAL ALLOCATION:"
)

print(
    "TQQQ + QQQ + V9 COST-AWARE STOCK ALPHA SLEEVE."
)

print("=" * 132)
