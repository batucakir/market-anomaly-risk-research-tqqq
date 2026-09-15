# MODULE 30 — V10 CONTRACT
# Run in the same notebook, in module order.

# ==============================================================================
# V9 — FINAL REJECTION RECORD
# +
# V10 — BLOCK 1
# PRE-PERFORMANCE RESEARCH CONTRACT
# PROBABILISTIC MULTI-HORIZON TQQQ-RELATIVE ARCHITECTURE
# ==============================================================================
#
# V9
# ---
# V9 is CLOSED.
#
# Its result must not be repaired by:
#
#   - adding a stock cap,
#   - adding a Top-K rule,
#   - removing weak horizons,
#   - changing HGB parameters,
#   - forcing a TQQQ floor,
#   - changing transaction-cost assumptions,
#   - changing the universal prior.
#
#
# V10
# ---
# V10 is a NEW research generation.
#
# PRIMARY OBJECTIVE:
#
#       MAXIMIZE NET TERMINAL WEALTH RELATIVE TO TQQQ
#
#
# CENTRAL HYPOTHESIS:
#
# V9 showed that long-horizon cross-sectional ranking information can exist
# while raw predicted-return magnitudes are too noisy for direct cardinal
# portfolio optimization.
#
# V10 therefore:
#
#   1. Predicts the PROBABILITY that each stock beats TQQQ.
#   2. Keeps ALL seven pre-declared horizons.
#   3. Aggregates probability evidence across horizons.
#   4. Uses only positive probabilistic edge to construct the stock sleeve.
#   5. Does NOT impose a Top-K rule.
#   6. Does NOT impose a minimum position.
#   7. Does NOT impose a maximum stock weight.
#   8. Does NOT impose a sector cap.
#   9. Does NOT impose a risk cap.
#  10. Uses TQQQ as the core asset.
#  11. Uses a causal Cover-style universal allocator between:
#
#           TQQQ
#           V10 probabilistic stock sleeve
#
#  12. Applies transaction cost and nonlinear market impact at the
#      underlying-asset level.
#
#
# FINAL V10 RESEARCH PASS REQUIRES:
#
#   A. Full-history V10 net terminal wealth > TQQQ.
#
#   B. V10 also beats TQQQ over ALL pre-declared trailing windows:
#
#          1D
#          1W
#          1M
#          3M
#          6M
#          9M
#          12M
#          FULL HISTORY
#
# This rule is declared NOW, before V10 performance is observed.
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

V10_B1_REQUIRED = [

    # V9 final result
    "V9_RESEARCH_VERDICT",
    "V9_FINAL_WEALTH",
    "V9_TQQQ_FULL_COST_WEALTH",
    "V9_QQQ_FULL_COST_WEALTH",
    "V9_RELATIVE_WEALTH_VS_TQQQ",
    "V9_MINUS_TQQQ_PP",

    "V9_BLOCK3_RESEARCH_FINGERPRINT",
    "V9_BLOCK3_SPEC_FINGERPRINT",
    "V9_BLOCK2B_RESEARCH_FINGERPRINT",

    # accepted infrastructure
    "V9_BASE_PANEL",
    "V9_LIFECYCLE_PANEL",
    "V9_CALENDAR",
    "V9_EVALUATION_CALENDAR",

    "V9_TARGET_HORIZONS",
    "V9_MODEL_FEATURES",

    "V9_TRAIN_LOOKBACK_SESSIONS",
    "V9_PORTFOLIO_REBALANCE_SESSIONS",

    "V9_BASE_TCA_RATE",
    "V9_IMPACT_COEFFICIENT",
    "V9_REFERENCE_AUM_USD",

    "V9_CONTRACT_FINGERPRINT",
]


V10_B1_MISSING = [
    name
    for name in V10_B1_REQUIRED
    if name not in globals()
]


if V10_B1_MISSING:

    raise RuntimeError(
        "V10 Block 1 is missing required objects: "
        f"{V10_B1_MISSING}"
    )


print("=" * 136)
print("V9 — FINAL REJECTION RECORD")
print("+")
print("V10 — BLOCK 1")
print("PRE-PERFORMANCE RESEARCH CONTRACT")
print("=" * 136)


# ==============================================================================
# 1. HARD-CHECK THE V9 VERDICT
# ==============================================================================

if str(
    V9_RESEARCH_VERDICT
).upper() != "FAIL":

    raise RuntimeError(
        "V10 must not start because V9 is not recorded as FAIL."
    )


if not (
    float(V9_FINAL_WEALTH)
    <
    float(V9_TQQQ_FULL_COST_WEALTH)
):

    raise RuntimeError(
        "V9 rejection consistency check failed."
    )


# ==============================================================================
# 2. IMMUTABLE V9 REJECTION RECORD
# ==============================================================================

V9_FINAL_REJECTION_RECORD = {

    "version":
        "V9",

    "status":
        "REJECTED",

    "primary_objective":
        "MAX_NET_RELATIVE_WEALTH_VS_TQQQ",

    "final_wealth":
        float(
            V9_FINAL_WEALTH
        ),

    "tqqq_full_cost_wealth":
        float(
            V9_TQQQ_FULL_COST_WEALTH
        ),

    "qqq_full_cost_wealth":
        float(
            V9_QQQ_FULL_COST_WEALTH
        ),

    "relative_wealth_vs_tqqq":
        float(
            V9_RELATIVE_WEALTH_VS_TQQQ
        ),

    "v9_minus_tqqq_pp":
        float(
            V9_MINUS_TQQQ_PP
        ),

    "research_verdict":
        str(
            V9_RESEARCH_VERDICT
        ),

    "final_research_fingerprint":
        V9_BLOCK3_RESEARCH_FINGERPRINT,

    "block3_spec_fingerprint":
        V9_BLOCK3_SPEC_FINGERPRINT,

    "stock_sleeve_result_fingerprint":
        V9_BLOCK2B_RESEARCH_FINGERPRINT,

    "primary_failure":
        (
            "POSITIVE_LONG_HORIZON_CROSS_SECTIONAL_INFORMATION_"
            "DID_NOT_TRANSLATE_TO_WEALTH_BECAUSE_CARDINAL_"
            "RETURN_MAGNITUDE_OPTIMIZATION_CREATED_EXTREME_"
            "CORNER_PORTFOLIOS"
        ),

    "post_result_modification_allowed":
        False,
}


V9_FINAL_REJECTION_STRING = json.dumps(
    V9_FINAL_REJECTION_RECORD,
    sort_keys=True,
    default=str,
)


V9_FINAL_REJECTION_FINGERPRINT = (
    hashlib.sha256(
        V9_FINAL_REJECTION_STRING.encode(
            "utf-8"
        )
    )
    .hexdigest()
)


print(
    "\nV9 final rejection fingerprint:"
)

print(
    V9_FINAL_REJECTION_FINGERPRINT
)


# ==============================================================================
# 3. V9 REJECTION SUMMARY
# ==============================================================================

V9_FINAL_REJECTION_TABLE = pd.DataFrame(
    {
        "Metric": [
            "Version",
            "Status",
            "V9 final wealth",
            "TQQQ final wealth",
            "QQQ final wealth",
            "V9 / TQQQ relative wealth",
            "V9 minus TQQQ pp",
            "Post-result modification allowed",
        ],

        "Value": [
            "V9",
            "REJECTED",

            float(
                V9_FINAL_WEALTH
            ),

            float(
                V9_TQQQ_FULL_COST_WEALTH
            ),

            float(
                V9_QQQ_FULL_COST_WEALTH
            ),

            float(
                V9_RELATIVE_WEALTH_VS_TQQQ
            ),

            float(
                V9_MINUS_TQQQ_PP
            ),

            False,
        ],
    }
)


print(
    "\n1) V9 FINAL REJECTION"
)

display(
    V9_FINAL_REJECTION_TABLE
)


# ==============================================================================
# 4. V10 RESEARCH DATES / INFORMATION POLICY
# ==============================================================================

V10_RESEARCH_BACKCAST_END = pd.Timestamp(
    "2026-07-27"
)


V10_INFORMATION_CUTOFF = pd.Timestamp(
    "2026-09-11"
)


V10_ARCHITECTURE_LOCK_DATE = pd.Timestamp(
    "2026-09-11"
)


V10_TRUE_OOS_STATUS = (
    "NOT_STARTED"
)


# ==============================================================================
# 5. RETAIN ACCEPTED CAUSAL INFRASTRUCTURE
# ==============================================================================

V10_BASE_PANEL = V9_BASE_PANEL

V10_LIFECYCLE_PANEL = V9_LIFECYCLE_PANEL

V10_CALENDAR = V9_CALENDAR

V10_EVALUATION_CALENDAR = (
    V9_EVALUATION_CALENDAR
)


V10_TARGET_HORIZONS = dict(
    V9_TARGET_HORIZONS
)


V10_MODEL_FEATURES = tuple(
    V9_MODEL_FEATURES
)


V10_TRAIN_LOOKBACK_SESSIONS = int(
    V9_TRAIN_LOOKBACK_SESSIONS
)


V10_REFIT_FREQUENCY_SESSIONS = int(
    V9_PORTFOLIO_REBALANCE_SESSIONS
)


V10_PORTFOLIO_REBALANCE_SESSIONS = int(
    V9_PORTFOLIO_REBALANCE_SESSIONS
)


V10_BASE_TCA_RATE = float(
    V9_BASE_TCA_RATE
)


V10_IMPACT_COEFFICIENT = float(
    V9_IMPACT_COEFFICIENT
)


V10_REFERENCE_AUM_USD = float(
    V9_REFERENCE_AUM_USD
)


# ==============================================================================
# 6. VERIFY THE SEVEN HORIZONS HAVE NOT CHANGED
# ==============================================================================

V10_EXPECTED_HORIZONS = {
    "1D": 1,
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "9M": 189,
    "12M": 252,
}


if V10_TARGET_HORIZONS != V10_EXPECTED_HORIZONS:

    raise RuntimeError(
        "V10 horizon contract differs from the frozen "
        "seven-horizon architecture."
    )


# ==============================================================================
# 7. PRE-DECLARE FINAL PERFORMANCE WINDOWS
# ==============================================================================

V10_ACCEPTANCE_WINDOWS = {

    "1D":
        1,

    "1W":
        5,

    "1M":
        21,

    "3M":
        63,

    "6M":
        126,

    "9M":
        189,

    "12M":
        252,

    "FULL":
        None,
}


# ==============================================================================
# 8. V10 MODEL FAMILY
# ==============================================================================
#
# Important:
#
# V10 does NOT regress future return magnitude.
#
# For each horizon h:
#
#     y_h = 1 if stock wealth > TQQQ wealth
#           0 otherwise
#
# The resulting probability is:
#
#     P(stock beats TQQQ over horizon h | causal information at signal date)
#
# ==============================================================================

V10_MODEL_FAMILY = (
    "HIST_GRADIENT_BOOSTING_CLASSIFIER"
)


V10_CLASSIFIER_PARAMS = {

    "loss":
        "log_loss",

    "learning_rate":
        0.1,

    "max_iter":
        100,

    "max_leaf_nodes":
        31,

    "max_depth":
        None,

    "min_samples_leaf":
        20,

    "l2_regularization":
        0.0,

    "max_bins":
        255,

    "early_stopping":
        "auto",

    "validation_fraction":
        0.1,

    "n_iter_no_change":
        10,

    "tol":
        1e-7,

    "random_state":
        0,
}


# ==============================================================================
# 9. V10 TARGET DEFINITION
# ==============================================================================

V10_TARGET_DEFINITION = {

    "type":
        "BINARY_TQQQ_RELATIVE_OUTPERFORMANCE",

    "label_rule":
        (
            "1_IF_EXECUTION_ALIGNED_STOCK_LOG_RELATIVE_WEALTH_"
            "VS_TQQQ_IS_GREATER_THAN_ZERO_ELSE_0"
        ),

    "seven_horizons":
        tuple(
            V10_TARGET_HORIZONS.items()
        ),

    "future_price_availability_filter":
        False,

    "execution_alignment":
        "SIGNAL_CLOSE_T_EXECUTE_CLOSE_T_PLUS_1",
}


# ==============================================================================
# 10. MULTI-HORIZON EVIDENCE AGGREGATION
# ==============================================================================
#
# No horizon is removed.
#
# No horizon is given a performance-selected weight.
#
# Composite probability:
#
#       median(
#           P_1D,
#           P_1W,
#           P_1M,
#           P_3M,
#           P_6M,
#           P_9M,
#           P_12M
#       )
#
# ==============================================================================

V10_MULTI_HORIZON_AGGREGATION = {

    "method":
        "MEDIAN_PROBABILITY",

    "horizon_weights":
        "NONE_EQUAL_STRUCTURAL_TREATMENT",

    "horizon_search":
        False,

    "post_result_horizon_removal":
        False,
}


# ==============================================================================
# 11. STOCK-SLEEVE CONSTRUCTION
# ==============================================================================
#
# Let:
#
#       p_i = median predicted probability that stock i beats TQQQ
#
#
# Positive evidence:
#
#       e_i = max(p_i - 0.5, 0)
#
#
# If at least one e_i > 0:
#
#       stock_weight_i = e_i / sum(e)
#
#
# If no stock has p_i > 0.5:
#
#       satellite is unavailable
#       portfolio remains 100% TQQQ
#
#
# IMPORTANT
# ---------
# 0.5 is not a tuned threshold.
#
# It is the natural probability break-even:
#
#       P(outperform) > P(underperform)
#
#
# There is NO:
#
#       minimum stock weight
#       maximum stock weight
#       Top-K
#       percentile cutoff
#       sector cap
#       volatility cap
#       risk cap
#
# ==============================================================================

V10_STOCK_SLEEVE_RULE = {

    "input":
        "MEDIAN_MULTI_HORIZON_BEAT_TQQQ_PROBABILITY",

    "edge":
        "MAX(PROBABILITY_MINUS_0P5,0)",

    "weighting":
        "NORMALIZED_POSITIVE_PROBABILITY_EDGE",

    "probability_break_even":
        0.5,

    "minimum_position_weight":
        None,

    "maximum_position_weight":
        None,

    "top_k":
        None,

    "percentile_cutoff":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "cash_inside_stock_sleeve":
        False,

    "no_positive_edge_policy":
        "SATELLITE_UNAVAILABLE_100_PERCENT_TQQQ",
}


# ==============================================================================
# 12. PORTFOLIO-LEVEL ALLOCATION
# ==============================================================================
#
# V10 deliberately does NOT reuse V9's three-way:
#
#       TQQQ + QQQ + alpha
#
#
# V10 contains:
#
#       TQQQ core
#       V10 probabilistic stock sleeve
#
#
# Allocation is causal Cover-style universal wealth aggregation over
# constant core/satellite mixes:
#
#       w_alpha in [0,1]
#
# with:
#
#       w_TQQQ = 1 - w_alpha
#
#
# Numerical quadrature uses 1001 points exactly as a numerical approximation
# of the continuous interval, not as a performance-tuned parameter.
#
# ==============================================================================

V10_UNIVERSAL_ALLOCATOR = {

    "components":
        (
            "TQQQ",
            "V10_PROBABILISTIC_ALPHA_SLEEVE",
        ),

    "allocator":
        "COVER_STYLE_UNIVERSAL_WEALTH_POSTERIOR",

    "constant_mix_interval":
        "[0,1]",

    "quadrature_points":
        1001,

    "prior":
        "UNIFORM",

    "actual_allocation":
        "PRE_EVENT_POSTERIOR_MEAN",

    "posterior_update":
        "AFTER_COMPLETED_REALIZED_HOLDING_PERIOD_ONLY",

    "mid_period_update":
        False,

    "cash_allowed":
        False,

    "leverage_above_100_pct":
        False,

    "tqqq_floor":
        None,

    "alpha_cap":
        None,

    "risk_cap":
        None,
}


# ==============================================================================
# 13. EXECUTION / CAPACITY POLICY
# ==============================================================================

V10_EXECUTION_POLICY = {

    "reference_aum_usd":
        V10_REFERENCE_AUM_USD,

    "base_tca_rate":
        V10_BASE_TCA_RATE,

    "impact_coefficient":
        V10_IMPACT_COEFFICIENT,

    "impact_model":
        (
            "SIGMA60_X_SQRT_ACTUAL_DOLLAR_TRADE_OVER_ADV60"
        ),

    "transaction_cost_level":
        "UNDERLYING_ASSET",

    "stock_liquidity_filter":
        "PRESERVE_EXISTING_CAUSAL_PIT_ELIGIBILITY",

    "new_purchase_exact_quote_required":
        True,

    "future_availability_filter":
        False,

    "membership_exit_handling":
        "CAUSAL_AT_EXECUTION_ONLY",
}


# ==============================================================================
# 14. FINAL PASS / FAIL CONTRACT
# ==============================================================================

V10_ACCEPTANCE_POLICY = {

    "primary_requirement":
        (
            "FULL_HISTORY_NET_TERMINAL_WEALTH_STRICTLY_GREATER_THAN_"
            "SAME_CALENDAR_FULL_COST_TQQQ"
        ),

    "strict_multi_window_requirement":
        (
            "V10_NET_RETURN_STRICTLY_GREATER_THAN_TQQQ_NET_RETURN_"
            "FOR_EVERY_PREDECLARED_WINDOW"
        ),

    "windows":
        tuple(
            V10_ACCEPTANCE_WINDOWS.items()
        ),

    "final_pass_requires_primary":
        True,

    "final_pass_requires_all_windows":
        True,

    "transaction_costs_required":
        True,

    "market_impact_required":
        True,

    "hindsight_best_mix_can_determine_verdict":
        False,

    "post_result_parameter_changes":
        False,
}


# ==============================================================================
# 15. FORBIDDEN POST-RESULT CHANGES
# ==============================================================================

V10_FORBIDDEN_POST_RESULT_CHANGES = (

    "REMOVE_A_HORIZON",

    "REWEIGHT_HORIZONS",

    "CHANGE_0P5_BREAK_EVEN",

    "ADD_TOP_K",

    "ADD_MINIMUM_POSITION",

    "ADD_MAXIMUM_POSITION",

    "ADD_SECTOR_CAP",

    "ADD_RISK_CAP",

    "ADD_TQQQ_FLOOR",

    "ADD_ALPHA_CAP",

    "CHANGE_CLASSIFIER_PARAMETERS",

    "CHANGE_TRAIN_LOOKBACK",

    "CHANGE_REBALANCE_FREQUENCY",

    "CHANGE_TRANSACTION_COST",

    "CHANGE_IMPACT_MODEL",

    "CHANGE_UNIVERSAL_PRIOR",

    "USE_HINDSIGHT_BEST_CONSTANT_MIX",

)


# ==============================================================================
# 16. V10 DATA-INFRASTRUCTURE SIGNATURE
# ==============================================================================
#
# Hash the key V10 PIT / execution structure so later blocks can verify
# that the research population has not silently changed.
#
# ==============================================================================

V10_SIGNATURE_COLUMNS = [
    "Date",
    "Ticker",
    "Execution_Date",
    "Adj_Close",
    "Median_Dollar_Volume_60",
]


V10_SIGNATURE_MISSING = [
    column
    for column in V10_SIGNATURE_COLUMNS
    if column not in V10_BASE_PANEL.columns
]


if V10_SIGNATURE_MISSING:

    raise RuntimeError(
        "V10 infrastructure signature is missing columns: "
        f"{V10_SIGNATURE_MISSING}"
    )


V10_SIGNATURE_FRAME = (
    V10_BASE_PANEL[
        V10_SIGNATURE_COLUMNS
    ]
    .copy()
)


for column in [
    "Date",
    "Execution_Date",
]:

    V10_SIGNATURE_FRAME[
        column
    ] = (
        pd.to_datetime(
            V10_SIGNATURE_FRAME[
                column
            ],
            errors="coerce",
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


V10_SIGNATURE_FRAME[
    "Ticker"
] = (
    V10_SIGNATURE_FRAME[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V10_INFRA_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V10_SIGNATURE_FRAME,
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V10_INFRA_DATA_HASH = (
    hashlib.sha256(
        V10_INFRA_HASH_VALUES.tobytes()
    )
    .hexdigest()
)


del V10_SIGNATURE_FRAME
del V10_INFRA_HASH_VALUES


# ==============================================================================
# 17. V10 MASTER RESEARCH CONTRACT
# ==============================================================================

V10_RESEARCH_CONTRACT = {

    "version":
        "V10",

    "status":
        "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",

    "architecture_generation":
        "NEW_GENERATION_NOT_A_V9_PATCH",

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",

    "benchmark":
        "TQQQ",

    "core":
        "TQQQ",

    "satellite":
        "PROBABILISTIC_MULTI_HORIZON_STOCK_SLEEVE",

    "research_backcast_end":
        str(
            V10_RESEARCH_BACKCAST_END.date()
        ),

    "information_cutoff":
        str(
            V10_INFORMATION_CUTOFF.date()
        ),

    "architecture_lock_date":
        str(
            V10_ARCHITECTURE_LOCK_DATE.date()
        ),

    "true_oos_status":
        V10_TRUE_OOS_STATUS,

    "source_v9_contract_fingerprint":
        V9_CONTRACT_FINGERPRINT,

    "source_v9_rejection_fingerprint":
        V9_FINAL_REJECTION_FINGERPRINT,

    "infrastructure_data_hash":
        V10_INFRA_DATA_HASH,

    "target_horizons":
        V10_TARGET_HORIZONS,

    "training_lookback_sessions":
        V10_TRAIN_LOOKBACK_SESSIONS,

    "refit_frequency_sessions":
        V10_REFIT_FREQUENCY_SESSIONS,

    "rebalance_frequency_sessions":
        V10_PORTFOLIO_REBALANCE_SESSIONS,

    "model_family":
        V10_MODEL_FAMILY,

    "classifier_params":
        V10_CLASSIFIER_PARAMS,

    "target_definition":
        V10_TARGET_DEFINITION,

    "multi_horizon_aggregation":
        V10_MULTI_HORIZON_AGGREGATION,

    "stock_sleeve_rule":
        V10_STOCK_SLEEVE_RULE,

    "universal_allocator":
        V10_UNIVERSAL_ALLOCATOR,

    "execution_policy":
        V10_EXECUTION_POLICY,

    "acceptance_policy":
        V10_ACCEPTANCE_POLICY,

    "forbidden_post_result_changes":
        V10_FORBIDDEN_POST_RESULT_CHANGES,
}


V10_RESEARCH_CONTRACT_STRING = json.dumps(
    V10_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V10_RESEARCH_CONTRACT_FINGERPRINT = (
    hashlib.sha256(
        V10_RESEARCH_CONTRACT_STRING.encode(
            "utf-8"
        )
    )
    .hexdigest()
)


# ==============================================================================
# 18. MASTER AUDIT TABLE
# ==============================================================================

V10_MASTER_AUDIT = pd.DataFrame(
    {
        "Metric": [

            "Version",

            "Status",

            "Primary objective",

            "Benchmark",

            "Core",

            "Satellite",

            "Model family",

            "Target type",

            "Target horizons",

            "Model features",

            "Training lookback sessions",

            "Refit frequency sessions",

            "Portfolio rebalance sessions",

            "Minimum stock weight",

            "Maximum stock weight",

            "Top-K",

            "Sector cap",

            "Risk cap",

            "TQQQ floor",

            "Alpha cap",

            "Cash allowed",

            "Leverage above 100%",

            "Universal quadrature points",

            "Base TCA bps",

            "Reference AUM USD",

            "Research backcast end",

            "Information cutoff",

            "Architecture lock date",

            "True OOS status",

            "Strict all-window TQQQ dominance required",
        ],

        "Value": [

            "V10",

            "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",

            "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",

            "TQQQ",

            "TQQQ",

            "PROBABILISTIC_STOCK_ALPHA",

            V10_MODEL_FAMILY,

            "P(STOCK_BEATS_TQQQ)",

            tuple(
                V10_TARGET_HORIZONS.keys()
            ),

            len(
                V10_MODEL_FEATURES
            ),

            V10_TRAIN_LOOKBACK_SESSIONS,

            V10_REFIT_FREQUENCY_SESSIONS,

            V10_PORTFOLIO_REBALANCE_SESSIONS,

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            False,

            False,

            V10_UNIVERSAL_ALLOCATOR[
                "quadrature_points"
            ],

            10000.0
            *
            V10_BASE_TCA_RATE,

            V10_REFERENCE_AUM_USD,

            V10_RESEARCH_BACKCAST_END.date(),

            V10_INFORMATION_CUTOFF.date(),

            V10_ARCHITECTURE_LOCK_DATE.date(),

            V10_TRUE_OOS_STATUS,

            True,
        ],
    }
)


# ==============================================================================
# 19. OUTPUT
# ==============================================================================

print(
    "\n2) V10 MASTER RESEARCH AUDIT"
)


display(
    V10_MASTER_AUDIT
)


print(
    "\n3) V10 ACCEPTANCE WINDOWS"
)


V10_ACCEPTANCE_WINDOW_TABLE = pd.DataFrame(
    {
        "Window": list(
            V10_ACCEPTANCE_WINDOWS.keys()
        ),

        "Trading_Sessions": list(
            V10_ACCEPTANCE_WINDOWS.values()
        ),

        "Requirement": [
            "V10 > TQQQ"
            for _ in V10_ACCEPTANCE_WINDOWS
        ],
    }
)


display(
    V10_ACCEPTANCE_WINDOW_TABLE
)


print(
    "\n4) V10 INFRASTRUCTURE HASH"
)

print(
    V10_INFRA_DATA_HASH
)


print(
    "\n5) V10 RESEARCH CONTRACT FINGERPRINT"
)

print(
    V10_RESEARCH_CONTRACT_FINGERPRINT
)


print("\nINTEGRITY:")
print("[+] V9 is permanently rejected as designed.")
print("[+] V10 is a new research generation, not a V9 patch.")
print("[+] PIT stock universe is preserved.")
print("[+] Existing liquidity eligibility is preserved.")
print("[+] Signal close and execution close remain separated.")
print("[+] Seven target horizons are preserved.")
print("[+] No weak horizon was removed.")
print("[+] Raw predicted return magnitude will NOT determine stock weights.")
print("[+] V10 predicts probability of beating TQQQ.")
print("[+] Probability break-even is structurally fixed at 0.50.")
print("[+] No minimum position weight.")
print("[+] No maximum stock weight.")
print("[+] No Top-K rule.")
print("[+] No sector cap.")
print("[+] No risk cap.")
print("[+] No TQQQ floor.")
print("[+] No alpha cap.")
print("[+] No cash.")
print("[+] No leverage above 100%.")
print("[+] Transaction cost and market impact remain mandatory.")
print("[+] Final acceptance windows are declared before performance.")
print("[+] No V10 performance has been observed.")

print(
    "\nV9 STATUS:"
)

print(
    "REJECTED / CLOSED"
)


print(
    "\nV10 STATUS:"
)

print(
    "PRE-PERFORMANCE ARCHITECTURE LOCKED"
)


print(
    "\nNEXT:"
)

print(
    "V10 BLOCK 2 — CHECKPOINTED SEVEN-HORIZON "
    "TQQQ-RELATIVE HGB CLASSIFIERS."
)

print("=" * 136)
