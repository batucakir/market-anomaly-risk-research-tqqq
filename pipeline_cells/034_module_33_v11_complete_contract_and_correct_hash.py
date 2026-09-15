# MODULE 33 — V11 COMPLETE CONTRACT AND CORRECT HASH
# Run in the same notebook, in module order.

# ==============================================================================
# V10 — FINAL REJECTION RECORD
# +
# V11 — BLOCK 1
# PRE-PERFORMANCE RESEARCH CONTRACT
#
# TQQQ-FIRST
# CROSS-SECTIONAL MULTI-HORIZON RANK ALPHA
# CAUSAL FOLLOW-THE-LEADER CONSTANT-MIX ALLOCATION
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V11_B1_REQUIRED = [

    # V10 final result
    "V10_RESEARCH_VERDICT",
    "V10_FINAL_WEALTH",
    "V10_TQQQ_FINAL_WEALTH",
    "V10_RELATIVE_WEALTH_VS_TQQQ",
    "V10_MINUS_TQQQ_PP",

    "V10_BLOCK3_RESEARCH_FINGERPRINT",
    "V10_BLOCK3_SPEC_FINGERPRINT",

    # Frozen V10 forecasts
    "V10_CLASSIFIER_PREDICTIONS",
    "V10_PREDICTIONS_HASH",
    "V10_BLOCK2_RESEARCH_FINGERPRINT",

    # Accepted infrastructure
    "V10_RESEARCH_CONTRACT_FINGERPRINT",
    "V10_INFRA_DATA_HASH",
    "V10_TARGET_HORIZONS",

    "V10_LIFECYCLE_PANEL",

    "V10_BASE_TCA_RATE",
    "V10_IMPACT_COEFFICIENT",
    "V10_REFERENCE_AUM_USD",

    "V10_RESEARCH_BACKCAST_END",
]


V11_B1_MISSING = [
    name
    for name in V11_B1_REQUIRED
    if name not in globals()
]


if V11_B1_MISSING:

    raise RuntimeError(
        "V11 Block 1 is missing required objects: "
        f"{V11_B1_MISSING}"
    )


print("=" * 140)
print("V10 — FINAL REJECTION RECORD")
print("+")
print("V11 — BLOCK 1")
print("PRE-PERFORMANCE RESEARCH CONTRACT")
print("=" * 140)


# ==============================================================================
# 1. HARD-CHECK V10 FAILURE
# ==============================================================================

if str(V10_RESEARCH_VERDICT).upper() != "FAIL":

    raise RuntimeError(
        "V11 must not start unless V10 is recorded as FAIL."
    )


if not (
    float(V10_FINAL_WEALTH)
    <
    float(V10_TQQQ_FINAL_WEALTH)
):

    raise RuntimeError(
        "V10 rejection consistency check failed."
    )


# ==============================================================================
# 2. IMMUTABLE V10 REJECTION RECORD
# ==============================================================================

V10_FINAL_REJECTION_RECORD = {

    "version":
        "V10",

    "status":
        "REJECTED",

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",

    "final_wealth":
        float(V10_FINAL_WEALTH),

    "tqqq_final_wealth":
        float(V10_TQQQ_FINAL_WEALTH),

    "relative_wealth_vs_tqqq":
        float(V10_RELATIVE_WEALTH_VS_TQQQ),

    "v10_minus_tqqq_pp":
        float(V10_MINUS_TQQQ_PP),

    "research_verdict":
        str(V10_RESEARCH_VERDICT),

    "block3_research_fingerprint":
        V10_BLOCK3_RESEARCH_FINGERPRINT,

    "block3_spec_fingerprint":
        V10_BLOCK3_SPEC_FINGERPRINT,

    "primary_failure":
        (
            "ABSOLUTE_PROBABILITY_THRESHOLDING_DISCARDED_PAYOFF_MAGNITUDE_"
            "AND_UNIVERSAL_ALLOCATION_DEPLOYED_TOO_MUCH_CAPITAL_TO_A_"
            "SLEEVE_THAT_DID_NOT_GENERATE_POSITIVE_RELATIVE_WEALTH"
        ),

    "post_result_modification_allowed":
        False,
}


V10_FINAL_REJECTION_STRING = json.dumps(
    V10_FINAL_REJECTION_RECORD,
    sort_keys=True,
    default=str,
)


V10_FINAL_REJECTION_FINGERPRINT = hashlib.sha256(
    V10_FINAL_REJECTION_STRING.encode("utf-8")
).hexdigest()


print("\nV10 final rejection fingerprint:")
print(V10_FINAL_REJECTION_FINGERPRINT)


# ==============================================================================
# 3. V10 REJECTION SUMMARY
# ==============================================================================

V10_FINAL_REJECTION_TABLE = pd.DataFrame(
    {
        "Metric": [
            "Version",
            "Status",
            "V10 final wealth",
            "TQQQ final wealth",
            "V10 / TQQQ relative wealth",
            "V10 minus TQQQ pp",
            "Post-result modification allowed",
        ],

        "Value": [
            "V10",
            "REJECTED",
            float(V10_FINAL_WEALTH),
            float(V10_TQQQ_FINAL_WEALTH),
            float(V10_RELATIVE_WEALTH_VS_TQQQ),
            float(V10_MINUS_TQQQ_PP),
            False,
        ],
    }
)


print("\n1) V10 FINAL REJECTION")
display(V10_FINAL_REJECTION_TABLE)


# ==============================================================================
# 4. V11 INFORMATION / RESEARCH STATUS
# ==============================================================================

V11_RESEARCH_BACKCAST_END = pd.Timestamp(
    V10_RESEARCH_BACKCAST_END
).normalize()


V11_INFORMATION_CUTOFF = pd.Timestamp(
    "2026-09-11"
)


V11_ARCHITECTURE_LOCK_DATE = pd.Timestamp(
    "2026-09-11"
)


V11_TRUE_OOS_STATUS = (
    "NOT_STARTED"
)


# ==============================================================================
# 5. FROZEN FORECAST SOURCE
# ==============================================================================
#
# IMPORTANT
# ---------
# V11 does NOT refit the HGB classifiers.
#
# It uses the already-frozen V10 seven-horizon probability predictions.
#
# But V11 does NOT trust the absolute probability calibration.
#
# Instead, each horizon probability is converted into a contemporaneous
# cross-sectional percentile rank.
#
# ==============================================================================

V11_FORECAST_SOURCE = {

    "source":
        "FROZEN_V10_HGB_CLASSIFIER_PREDICTIONS",

    "source_prediction_hash":
        V10_PREDICTIONS_HASH,

    "source_block2_fingerprint":
        V10_BLOCK2_RESEARCH_FINGERPRINT,

    "model_refit":
        False,

    "absolute_probability_used_for_weighting":
        False,

    "cross_sectional_rank_only":
        True,
}


# ==============================================================================
# 6. SEVEN HORIZONS REMAIN FROZEN
# ==============================================================================

V11_TARGET_HORIZONS = dict(
    V10_TARGET_HORIZONS
)


V11_EXPECTED_HORIZONS = {
    "1D": 1,
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "9M": 189,
    "12M": 252,
}


if V11_TARGET_HORIZONS != V11_EXPECTED_HORIZONS:

    raise RuntimeError(
        "V11 horizon contract differs from the frozen seven-horizon set."
    )


# ==============================================================================
# 7. CROSS-SECTIONAL RANK TRANSFORMATION
# ==============================================================================
#
# At every signal date and for every horizon:
#
#       rank_i,h =
#           percentile rank of P(stock_i beats TQQQ)
#
# Then:
#
#       composite_rank_i =
#           median(rank_i,1D ... rank_i,12M)
#
#
# This deliberately removes:
#
#       probability-level calibration dependence
#
# while retaining:
#
#       cross-sectional relative ordering
#
# ==============================================================================

V11_RANK_TRANSFORMATION = {

    "per_horizon_transform":
        "CROSS_SECTIONAL_PERCENTILE_RANK",

    "rank_method":
        "AVERAGE",

    "rank_range":
        "(0,1]",

    "multi_horizon_aggregation":
        "MEDIAN_OF_SEVEN_PERCENTILE_RANKS",

    "horizon_weights":
        None,

    "horizon_removal":
        None,

    "performance_selected_horizons":
        False,
}


# ==============================================================================
# 8. STOCK-SLEEVE CONSTRUCTION
# ==============================================================================
#
# Let:
#
#       r_i = median multi-horizon percentile rank
#
#
# Define rank edge:
#
#       e_i = max(r_i - 0.50, 0)
#
#
# If sum(e_i) > 0:
#
#       w_i = e_i / sum(e)
#
#
# This is NOT a Top-K rule.
#
# The number of stocks is determined continuously by the cross-sectional
# rank distribution.
#
#
# NO:
#       minimum position
#       maximum position
#       Top-K
#       sector cap
#       risk cap
#
# ==============================================================================

V11_STOCK_SLEEVE_RULE = {

    "input":
        "MEDIAN_SEVEN_HORIZON_CROSS_SECTIONAL_PERCENTILE_RANK",

    "rank_break_even":
        0.50,

    "edge":
        "MAX(COMPOSITE_RANK_MINUS_0P50,0)",

    "weighting":
        "NORMALIZED_POSITIVE_RANK_EDGE",

    "minimum_position_weight":
        None,

    "maximum_position_weight":
        None,

    "top_k":
        None,

    "percentile_selection_parameter":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "cash_inside_sleeve":
        False,
}


# ==============================================================================
# 9. BENCHMARK-FIRST ALLOCATION
# ==============================================================================
#
# V10 weakness:
#
# A uniform Cover prior began near 50% Alpha before Alpha had earned any
# benchmark-relative evidence.
#
#
# V11 rule:
#
# At event t, using ONLY completed events 1...(t-1):
#
#   1. Evaluate a continuous class of constant TQQQ / Alpha mixes.
#
#   2. Include full underlying-asset execution cost in each expert.
#
#   3. Select the constant mix with the greatest historical NET wealth.
#
#   4. If there is a tie, choose the mix with MORE TQQQ.
#
#
# Therefore:
#
#       Event 1 = 100% TQQQ
#
# because no Alpha evidence exists yet.
#
#
# This is causal Follow-The-Leader.
#
# It contains no learning rate, risk-aversion parameter or posterior prior.
#
# ==============================================================================

V11_ALLOCATOR = {

    "components":
        (
            "TQQQ",
            "V11_RANK_ALPHA_SLEEVE",
        ),

    "method":
        "CAUSAL_FOLLOW_THE_LEADER_CONSTANT_MIX",

    "expert_alpha_interval":
        "[0,1]",

    "numerical_grid_points":
        1001,

    "grid_role":
        "NUMERICAL_APPROXIMATION_ONLY",

    "decision_rule":
        (
            "PRE_EVENT_SELECT_PRIOR_NET_WEALTH_MAXIMIZING_CONSTANT_MIX"
        ),

    "initial_allocation":
        "100_PERCENT_TQQQ",

    "tie_break":
        "MORE_TQQQ",

    "uses_current_event_return":
        False,

    "uses_future_event_return":
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
# 10. EXECUTION POLICY
# ==============================================================================

V11_EXECUTION_POLICY = {

    "reference_aum_usd":
        float(V10_REFERENCE_AUM_USD),

    "base_tca_rate":
        float(V10_BASE_TCA_RATE),

    "impact_coefficient":
        float(V10_IMPACT_COEFFICIENT),

    "impact_model":
        "SIGMA60_X_SQRT_ACTUAL_DOLLAR_TRADE_OVER_ADV60",

    "transaction_cost_level":
        "UNDERLYING_ASSET",

    "exact_entry_quote_required":
        True,

    "future_availability_filter":
        False,

    "causal_lifecycle_handling":
        True,
}


# ==============================================================================
# 11. V11 PERFORMANCE EVALUATION POLICY
# ==============================================================================
#
# IMPORTANT METHODOLOGICAL CHANGE
# -------------------------------
#
# V10 used one trailing observation for each horizon:
#
#       e.g. the final 1D return only.
#
# V11 will evaluate "performance at a horizon" across ALL rolling windows
# of that length.
#
#
# For each horizon H:
#
#       rolling_hit_rate =
#           P(V11 return_H > TQQQ return_H)
#
#       median_rolling_excess =
#           median(V11 return_H - TQQQ return_H)
#
#
# FULL-HISTORY wealth remains the PRIMARY objective.
#
#
# PASS requires:
#
#   1. V11 full-history net terminal wealth > TQQQ
#
#   2. At every horizon:
#
#          rolling beat rate > 50%
#
#      AND
#
#          median rolling excess > 0
#
#
# No single terminal day can determine the robustness verdict.
#
# ==============================================================================

V11_EVALUATION_WINDOWS = {
    "1D": 1,
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "9M": 189,
    "12M": 252,
}


V11_ACCEPTANCE_POLICY = {

    "primary_objective":
        "FULL_HISTORY_NET_TERMINAL_WEALTH_GT_TQQQ",

    "primary_requirement":
        True,

    "rolling_horizon_requirement":
        True,

    "rolling_windows":
        V11_EVALUATION_WINDOWS,

    "rolling_beat_rate_requirement":
        "STRICTLY_GREATER_THAN_50_PERCENT",

    "median_rolling_excess_requirement":
        "STRICTLY_GREATER_THAN_ZERO",

    "latest_trailing_windows":
        "DIAGNOSTIC_ONLY",

    "full_history_tqqq_dominance":
        True,

    "transaction_costs_required":
        True,

    "market_impact_required":
        True,

    "post_result_parameter_changes":
        False,
}


# ==============================================================================
# 12. FORBIDDEN POST-RESULT CHANGES
# ==============================================================================

V11_FORBIDDEN_POST_RESULT_CHANGES = (

    "REFIT_V10_CLASSIFIERS",

    "REMOVE_A_HORIZON",

    "REWEIGHT_HORIZONS",

    "CHANGE_RANK_BREAK_EVEN",

    "ADD_TOP_K",

    "ADD_MINIMUM_POSITION_WEIGHT",

    "ADD_MAXIMUM_POSITION_WEIGHT",

    "ADD_SECTOR_CAP",

    "ADD_RISK_CAP",

    "ADD_TQQQ_FLOOR",

    "ADD_ALPHA_CAP",

    "CHANGE_FTL_TO_ANOTHER_ALLOCATOR",

    "CHANGE_TIE_BREAK",

    "CHANGE_GRID_RESOLUTION_FOR_PERFORMANCE",

    "CHANGE_TRANSACTION_COST",

    "CHANGE_MARKET_IMPACT_MODEL",

    "CHANGE_ACCEPTANCE_RULE_AFTER_RESULT",
)



# ==============================================================================
# V11 — BLOCK 1-R
# HASH VALIDATION REPAIR + RESEARCH CONTRACT FINALIZATION
# ==============================================================================
#
# RETROACTIVE TECHNICAL FIX ONLY
#
# ROOT CAUSE:
# V10_PREDICTIONS_HASH was originally calculated from:
#
#   Date
#   Execution_Date
#   Ticker
#   7 horizon probability columns
#   Composite_Prob_Beat_TQQQ
#
# The previous V11 integrity check accidentally omitted the composite column.
#
# THIS PATCH:
#   - does NOT refit any model
#   - does NOT change any prediction
#   - does NOT change V11 architecture
#   - does NOT calculate V11 performance
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


print("=" * 140)
print("V11 — BLOCK 1-R")
print("HASH VALIDATION REPAIR + RESEARCH CONTRACT FINALIZATION")
print("=" * 140)


# ==============================================================================
# 1. REQUIREMENTS
# ==============================================================================

V11_B1R_REQUIRED = [
    "V10_CLASSIFIER_PREDICTIONS",
    "V10_PREDICTIONS_HASH",
    "V10_FINAL_REJECTION_FINGERPRINT",
    "V10_RESEARCH_CONTRACT_FINGERPRINT",
    "V10_BLOCK2_RESEARCH_FINGERPRINT",
    "V10_INFRA_DATA_HASH",

    "V11_FORECAST_SOURCE",
    "V11_TARGET_HORIZONS",
    "V11_RANK_TRANSFORMATION",
    "V11_STOCK_SLEEVE_RULE",
    "V11_ALLOCATOR",
    "V11_EXECUTION_POLICY",
    "V11_ACCEPTANCE_POLICY",
    "V11_FORBIDDEN_POST_RESULT_CHANGES",

    "V11_RESEARCH_BACKCAST_END",
    "V11_INFORMATION_CUTOFF",
    "V11_ARCHITECTURE_LOCK_DATE",
    "V11_TRUE_OOS_STATUS",
    "V11_EVALUATION_WINDOWS",
]


V11_B1R_MISSING = [
    name
    for name in V11_B1R_REQUIRED
    if name not in globals()
]


if V11_B1R_MISSING:
    raise RuntimeError(
        "V11 Block 1-R is missing objects created before the prior "
        f"hash-check failure: {V11_B1R_MISSING}"
    )


# ==============================================================================
# 2. RECONSTRUCT THE EXACT ORIGINAL V10 HASH COLUMN SET
# ==============================================================================

if "V10_PROBABILITY_COLUMNS" in globals():

    V11_HASH_PROBABILITY_COLUMNS = list(
        V10_PROBABILITY_COLUMNS
    )

else:

    V11_HASH_PROBABILITY_COLUMNS = [
        f"Prob_Beat_TQQQ_{horizon}"
        for horizon in V11_TARGET_HORIZONS
    ]


if "V10_COMPOSITE_COLUMN" in globals():

    V11_HASH_COMPOSITE_COLUMN = str(
        V10_COMPOSITE_COLUMN
    )

else:

    V11_HASH_COMPOSITE_COLUMN = (
        "Composite_Prob_Beat_TQQQ"
    )


V11_EXACT_V10_HASH_COLUMNS = (
    [
        "Date",
        "Execution_Date",
        "Ticker",
    ]
    +
    V11_HASH_PROBABILITY_COLUMNS
    +
    [
        V11_HASH_COMPOSITE_COLUMN
    ]
)


V11_HASH_MISSING_COLUMNS = [
    column
    for column in V11_EXACT_V10_HASH_COLUMNS
    if column not in V10_CLASSIFIER_PREDICTIONS.columns
]


if V11_HASH_MISSING_COLUMNS:
    raise RuntimeError(
        "Cannot reproduce the original V10 prediction hash. "
        f"Missing columns: {V11_HASH_MISSING_COLUMNS}"
    )


# ==============================================================================
# 3. EXACTLY REPRODUCE THE ORIGINAL V10 HASH
# ==============================================================================
#
# IMPORTANT:
# Do NOT sort, normalize, transform, cast or otherwise alter this frame.
#
# We hash the original frozen V10 object in exactly the same column order
# used when V10_PREDICTIONS_HASH was created.
# ==============================================================================

V11_INPUT_HASH_FRAME = (
    V10_CLASSIFIER_PREDICTIONS[
        V11_EXACT_V10_HASH_COLUMNS
    ]
    .copy()
)


V11_INPUT_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V11_INPUT_HASH_FRAME,
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V11_INPUT_PREDICTION_HASH = hashlib.sha256(
    V11_INPUT_HASH_VALUES.tobytes()
).hexdigest()


V11_HASH_MATCH = bool(
    V11_INPUT_PREDICTION_HASH
    ==
    V10_PREDICTIONS_HASH
)


print("\n1) FROZEN FORECAST HASH VALIDATION")

V11_HASH_AUDIT = pd.DataFrame(
    {
        "Field": [
            "Stored V10 prediction hash",
            "Recomputed exact V10 hash",
            "Hash match",
            "Rows hashed",
            "Columns hashed",
            "Composite column included",
        ],

        "Value": [
            V10_PREDICTIONS_HASH,
            V11_INPUT_PREDICTION_HASH,
            V11_HASH_MATCH,
            len(V11_INPUT_HASH_FRAME),
            len(V11_EXACT_V10_HASH_COLUMNS),
            V11_HASH_COMPOSITE_COLUMN,
        ],
    }
)

display(V11_HASH_AUDIT)


if not V11_HASH_MATCH:

    raise RuntimeError(
        "TRUE V10 forecast-state mismatch detected. "
        "The original V10 prediction object no longer matches its stored hash."
    )


print(
    "\n[+] EXACT ORIGINAL V10 PREDICTION HASH MATCHED."
)


del V11_INPUT_HASH_FRAME
del V11_INPUT_HASH_VALUES


# ==============================================================================
# 4. FINALIZE V11 MASTER CONTRACT
# ==============================================================================

V11_RESEARCH_CONTRACT = {

    "version":
        "V11",

    "status":
        "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",

    "architecture_generation":
        "NEW_GENERATION_NOT_A_V10_PATCH",

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",

    "benchmark":
        "TQQQ",

    "core":
        "TQQQ",

    "satellite":
        "CROSS_SECTIONAL_MULTI_HORIZON_RANK_ALPHA",

    "forecast_source":
        V11_FORECAST_SOURCE,

    "target_horizons":
        V11_TARGET_HORIZONS,

    "rank_transformation":
        V11_RANK_TRANSFORMATION,

    "stock_sleeve_rule":
        V11_STOCK_SLEEVE_RULE,

    "allocator":
        V11_ALLOCATOR,

    "execution_policy":
        V11_EXECUTION_POLICY,

    "acceptance_policy":
        V11_ACCEPTANCE_POLICY,

    "research_backcast_end":
        str(
            V11_RESEARCH_BACKCAST_END.date()
        ),

    "information_cutoff":
        str(
            V11_INFORMATION_CUTOFF.date()
        ),

    "architecture_lock_date":
        str(
            V11_ARCHITECTURE_LOCK_DATE.date()
        ),

    "true_oos_status":
        V11_TRUE_OOS_STATUS,

    "source_v10_rejection_fingerprint":
        V10_FINAL_REJECTION_FINGERPRINT,

    "source_v10_contract_fingerprint":
        V10_RESEARCH_CONTRACT_FINGERPRINT,

    "source_v10_prediction_hash":
        V10_PREDICTIONS_HASH,

    "verified_input_prediction_hash":
        V11_INPUT_PREDICTION_HASH,

    "infrastructure_hash":
        V10_INFRA_DATA_HASH,

    "forbidden_post_result_changes":
        V11_FORBIDDEN_POST_RESULT_CHANGES,
}


V11_RESEARCH_CONTRACT_STRING = json.dumps(
    V11_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V11_RESEARCH_CONTRACT_FINGERPRINT = hashlib.sha256(
    V11_RESEARCH_CONTRACT_STRING.encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 5. MASTER AUDIT
# ==============================================================================

V11_MASTER_AUDIT = pd.DataFrame(
    {
        "Metric": [
            "Version",
            "Status",
            "Primary objective",
            "Benchmark",
            "Default portfolio",
            "Forecast source",
            "New model fitting",
            "Absolute probability level used for weights",
            "Cross-sectional ranking used",
            "Horizons",
            "Horizon aggregation",
            "Rank break-even",
            "Minimum stock weight",
            "Maximum stock weight",
            "Top-K",
            "Sector cap",
            "Risk cap",
            "TQQQ floor",
            "Alpha cap",
            "Cash allowed",
            "Leverage above 100%",
            "Allocator",
            "Initial allocation",
            "Allocator tie-break",
            "Constant-mix grid points",
            "Research backcast end",
            "Information cutoff",
            "Architecture lock date",
            "True OOS status",
            "Frozen V10 hash verified",
        ],

        "Value": [
            "V11",
            "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",
            "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ",
            "TQQQ",
            "100% TQQQ",
            "FROZEN V10 CLASSIFIER OUTPUTS",
            False,
            False,
            True,
            tuple(V11_TARGET_HORIZONS.keys()),
            "MEDIAN OF 7 CROSS-SECTIONAL RANKS",
            0.50,
            "NONE",
            "NONE",
            "NONE",
            "NONE",
            "NONE",
            "NONE",
            "NONE",
            False,
            False,
            "CAUSAL FOLLOW-THE-LEADER CONSTANT MIX",
            "100% TQQQ",
            "MORE TQQQ",
            1001,
            V11_RESEARCH_BACKCAST_END.date(),
            V11_INFORMATION_CUTOFF.date(),
            V11_ARCHITECTURE_LOCK_DATE.date(),
            V11_TRUE_OOS_STATUS,
            V11_HASH_MATCH,
        ],
    }
)


# ==============================================================================
# 6. ACCEPTANCE CONTRACT
# ==============================================================================

V11_ACCEPTANCE_WINDOW_TABLE = pd.DataFrame(
    {
        "Horizon":
            list(
                V11_EVALUATION_WINDOWS.keys()
            ),

        "Trading_Sessions":
            list(
                V11_EVALUATION_WINDOWS.values()
            ),

        "Rolling_Beat_Rate_Requirement":
            [
                "> 50%"
                for _ in V11_EVALUATION_WINDOWS
            ],

        "Median_Rolling_Excess_Requirement":
            [
                "> 0"
                for _ in V11_EVALUATION_WINDOWS
            ],
    }
)


# ==============================================================================
# 7. FINAL OUTPUT
# ==============================================================================

print("\n2) V11 MASTER RESEARCH AUDIT")

display(
    V11_MASTER_AUDIT
)


print(
    "\n3) V11 ROLLING-HORIZON ACCEPTANCE CONTRACT"
)

display(
    V11_ACCEPTANCE_WINDOW_TABLE
)


print(
    "\n4) VERIFIED FROZEN V10 FORECAST HASH"
)

print(
    V11_INPUT_PREDICTION_HASH
)


print(
    "\n5) V11 RESEARCH CONTRACT FINGERPRINT"
)

print(
    V11_RESEARCH_CONTRACT_FINGERPRINT
)


print("\nINTEGRITY:")

print("[+] Previous hash-check bug corrected.")
print("[+] Original V10 forecast object matches its stored hash exactly.")
print("[+] No prediction was modified.")
print("[+] No model was refitted.")
print("[+] No V11 performance has been calculated.")
print("[+] V11 architecture is unchanged.")
print("[+] V11 remains a new generation, not a V10 patch.")
print("[+] All seven horizons remain frozen.")
print("[+] Cross-sectional percentile ranking remains frozen.")
print("[+] Rank-edge threshold remains exactly 0.50.")
print("[+] No minimum position weight.")
print("[+] No maximum position weight.")
print("[+] No Top-K rule.")
print("[+] No sector cap.")
print("[+] No risk cap.")
print("[+] No TQQQ floor.")
print("[+] No alpha cap.")
print("[+] No cash.")
print("[+] No leverage above 100%.")
print("[+] Initial V11 allocation remains 100% TQQQ.")
print("[+] Alpha must earn allocation causally from completed prior events.")
print("[+] Full-history terminal wealth remains the primary objective.")


print("\nV10 STATUS:")
print("REJECTED / CLOSED")


print("\nV11 STATUS:")
print("PRE-PERFORMANCE ARCHITECTURE LOCKED")


print("\nNEXT:")
print(
    "V11 BLOCK 2 — CROSS-SECTIONAL SEVEN-HORIZON RANK PANEL "
    "+ FROZEN RANK-EDGE STOCK SLEEVE."
)

print(
    "NO MODEL FITTING IS REQUIRED."
)


print("=" * 140)
