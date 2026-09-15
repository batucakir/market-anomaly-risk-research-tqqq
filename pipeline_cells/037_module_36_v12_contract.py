# MODULE 36 — V12 CONTRACT
# Run in the same notebook, in module order.

# ==============================================================================
# V12 — BLOCK 1-R
# PRE-PERFORMANCE RESEARCH CONTRACT
# DEPENDENCY-SAFE FINALIZATION
# ==============================================================================
#
# TECHNICAL FIX ONLY:
# The previous Block 1 incorrectly required a specific notebook variable name
# called V7_ALPHA_SLEEVE_TARGETS.
#
# V12 Block 1 does NOT need the actual sleeve target object yet.
# It only needs to freeze the architecture.
#
# The exact frozen V7/V8 sleeve object will be resolved and audited BEFORE
# any V12 performance is calculated in Block 2.
#
# NO MODEL FITTING.
# NO PERFORMANCE CALCULATION.
# NO ARCHITECTURE CHANGE.
# ==============================================================================

import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


print("=" * 140)
print("V11 — FINAL REJECTION RECORD")
print("+")
print("V12 — BLOCK 1-R")
print("PRE-PERFORMANCE RESEARCH CONTRACT")
print("=" * 140)


# ==============================================================================
# 1. REQUIRE ONLY OBJECTS ACTUALLY NEEDED AT CONTRACT STAGE
# ==============================================================================

V12_B1_REQUIRED = [

    # V11 final result
    "V11_RESEARCH_VERDICT",
    "V11_FINAL_WEALTH",
    "V11_TQQQ_FINAL_WEALTH",
    "V11_RELATIVE_WEALTH",
    "V11_MINUS_TQQQ_PP",
    "V11_BLOCK3_RESEARCH_FINGERPRINT",

    # Frozen successful architecture references
    "V8_PATH",
    "V8_RESEARCH_FINGERPRINT",
    "V8_CONFIG_STRING",
    "V7_FINGERPRINT",

    # Shared execution infrastructure
    "V10_LIFECYCLE_PANEL",
    "V10_BASE_TCA_RATE",
    "V10_IMPACT_COEFFICIENT",
    "V10_REFERENCE_AUM_USD",
]


V12_B1_MISSING = [
    name
    for name in V12_B1_REQUIRED
    if name not in globals()
]


if V12_B1_MISSING:
    raise RuntimeError(
        "V12 Block 1-R is missing genuinely required objects: "
        f"{V12_B1_MISSING}"
    )


# ==============================================================================
# 2. HARD-CHECK V11 FAILURE
# ==============================================================================

if str(V11_RESEARCH_VERDICT).upper() != "FAIL":
    raise RuntimeError(
        "V12 must not start unless V11 is formally rejected."
    )


# ==============================================================================
# 3. FREEZE V11 REJECTION
# ==============================================================================

V11_FINAL_REJECTION_RECORD = {

    "version":
        "V11",

    "status":
        "REJECTED",

    "final_wealth":
        float(V11_FINAL_WEALTH),

    "tqqq_final_wealth":
        float(V11_TQQQ_FINAL_WEALTH),

    "relative_wealth":
        float(V11_RELATIVE_WEALTH),

    "v11_minus_tqqq_pp":
        float(V11_MINUS_TQQQ_PP),

    "research_verdict":
        str(V11_RESEARCH_VERDICT),

    "block3_fingerprint":
        V11_BLOCK3_RESEARCH_FINGERPRINT,

    "economic_result":
        "DEGENERATED_TO_100_PERCENT_TQQQ",

    "post_result_modification_allowed":
        False,
}


V11_FINAL_REJECTION_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V11_FINAL_REJECTION_RECORD,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
).hexdigest()


# ==============================================================================
# 4. V12 PRIMARY OBJECTIVE
# ==============================================================================

V12_PRIMARY_OBJECTIVE = (
    "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_TQQQ"
)


# ==============================================================================
# 5. FROZEN INVESTABLE COMPONENT CONTRACT
# ==============================================================================

V12_COMPONENTS = {

    "core":
        "TQQQ",

    "satellite":
        "FROZEN_V7_V8_ALPHA_SLEEVE",

    "satellite_object_resolution":
        "DEFERRED_TO_PRE_PERFORMANCE_BLOCK_2_AUDIT",

    "stock_selection_refit":
        False,

    "stock_selection_retune":
        False,

    "satellite_definition_change_allowed":
        False,
}


# ==============================================================================
# 6. CAUSAL STATE DEFINITION
# ==============================================================================

V12_STATE_DEFINITION = {

    "tqqq_long_trend":
        "PRICE_OVER_SMA252_MINUS_1",

    "tqqq_medium_trend":
        "PRICE_OVER_SMA63_MINUS_1",

    "tqqq_realized_volatility":
        "TRAILING_63_SESSION_ANNUALIZED_VOL",

    "alpha_effective_n":
        "1_OVER_SUM_SQUARED_FROZEN_SLEEVE_WEIGHTS",

    "alpha_max_weight":
        "MAX_FROZEN_ALPHA_SLEEVE_WEIGHT",

    "future_information":
        False,

    "fitted_regime_model":
        False,

    "hmm":
        False,
}


# ==============================================================================
# 7. PARAMETER-FREE NORMALIZATION
# ==============================================================================

V12_STATE_NORMALIZATION = {

    "method":
        "CAUSAL_EXPANDING_PERCENTILE_RANK",

    "performance_tuned_thresholds":
        False,

    "fixed_numeric_state_thresholds":
        None,
}


# ==============================================================================
# 8. PREDECLARED ALLOCATION RULE
# ==============================================================================

V12_ALLOCATION_RULE = {

    "inputs": [

        "1_MINUS_TQQQ_LONG_TREND_PERCENTILE",

        "1_MINUS_TQQQ_MEDIUM_TREND_PERCENTILE",

        "TQQQ_VOLATILITY_PERCENTILE",

        "ALPHA_EFFECTIVE_N_PERCENTILE",

        "1_MINUS_ALPHA_MAX_WEIGHT_PERCENTILE",
    ],

    "aggregation":
        "MEDIAN",

    "alpha_weight":
        "MEDIAN_STATE_SCORE",

    "tqqq_weight":
        "1_MINUS_ALPHA_WEIGHT",

    "minimum_alpha_weight":
        None,

    "maximum_alpha_weight":
        None,

    "tqqq_floor":
        None,

    "cash":
        False,

    "leverage_above_100_pct":
        False,
}


# ==============================================================================
# 9. EXECUTION POLICY
# ==============================================================================

V12_EXECUTION_POLICY = {

    "signal_execution":
        "SIGNAL_CLOSE_T_EXECUTE_CLOSE_T_PLUS_1",

    "rebalance_sessions":
        21,

    "reference_aum_usd":
        float(V10_REFERENCE_AUM_USD),

    "base_tca_rate":
        float(V10_BASE_TCA_RATE),

    "impact_coefficient":
        float(V10_IMPACT_COEFFICIENT),

    "market_impact":
        "SIGMA60_X_SQRT_DOLLAR_TRADE_OVER_ADV60",

    "underlying_level_cost":
        True,

    "cash":
        False,

    "leverage_above_100_pct":
        False,
}


# ==============================================================================
# 10. ACCEPTANCE POLICY
# ==============================================================================

V12_EVALUATION_WINDOWS = {

    "1D": 1,

    "1W": 5,

    "1M": 21,

    "3M": 63,

    "6M": 126,

    "9M": 189,

    "12M": 252,
}


V12_ACCEPTANCE_POLICY = {

    "full_history_net_terminal_wealth_gt_tqqq":
        True,

    "rolling_windows":
        V12_EVALUATION_WINDOWS,

    "rolling_beat_rate_gt_50_pct":
        True,

    "rolling_median_excess_gt_zero":
        True,

    "transaction_costs_required":
        True,

    "market_impact_required":
        True,

    "post_result_parameter_change":
        False,
}


# ==============================================================================
# 11. FORBIDDEN POST-RESULT CHANGES
# ==============================================================================

V12_FORBIDDEN_CHANGES = (

    "CHANGE_FROZEN_V7_V8_ALPHA_SLEEVE",

    "REMOVE_BAD_ALPHA_EVENTS",

    "ADD_ALPHA_GATE_AFTER_RESULT",

    "CHANGE_STATE_VARIABLES",

    "CHANGE_STATE_SIGNS",

    "CHANGE_MEDIAN_TO_MEAN_AFTER_RESULT",

    "FIT_STATE_COEFFICIENTS",

    "ADD_STATE_THRESHOLDS",

    "ADD_TQQQ_FLOOR",

    "ADD_ALPHA_CAP",

    "ADD_MINIMUM_STOCK_WEIGHT",

    "ADD_MAXIMUM_STOCK_WEIGHT",

    "ADD_TOP_K",

    "ADD_SECTOR_CAP",

    "ADD_RISK_CAP",

    "ADD_CASH",

    "ADD_LEVERAGE",

    "CHANGE_TCA",

    "CHANGE_MARKET_IMPACT_MODEL",

    "CHANGE_ACCEPTANCE_POLICY",
)


# ==============================================================================
# 12. RESEARCH CONTRACT
# ==============================================================================

V12_RESEARCH_CONTRACT = {

    "version":
        "V12",

    "status":
        "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",

    "primary_objective":
        V12_PRIMARY_OBJECTIVE,

    "benchmark":
        "TQQQ",

    "components":
        V12_COMPONENTS,

    "state_definition":
        V12_STATE_DEFINITION,

    "state_normalization":
        V12_STATE_NORMALIZATION,

    "allocation_rule":
        V12_ALLOCATION_RULE,

    "execution_policy":
        V12_EXECUTION_POLICY,

    "acceptance_policy":
        V12_ACCEPTANCE_POLICY,

    "source_v7_fingerprint":
        V7_FINGERPRINT,

    "source_v8_research_fingerprint":
        V8_RESEARCH_FINGERPRINT,

    "source_v11_rejection_fingerprint":
        V11_FINAL_REJECTION_FINGERPRINT,

    "frozen_satellite_object":
        "TO_BE_RESOLVED_BEFORE_PERFORMANCE",

    "post_result_changes_forbidden":
        V12_FORBIDDEN_CHANGES,
}


V12_RESEARCH_CONTRACT_STRING = json.dumps(
    V12_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V12_RESEARCH_CONTRACT_FINGERPRINT = hashlib.sha256(
    V12_RESEARCH_CONTRACT_STRING.encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 13. SEARCH NOTEBOOK FOR POSSIBLE FROZEN SLEEVE OBJECTS
# ==============================================================================
#
# IMPORTANT:
# We are NOT selecting one here.
# We are only inventorying existing V7/V8 objects so Block 2 can validate them.
# ==============================================================================

V12_SLEEVE_OBJECT_CANDIDATES = []


for object_name, object_value in globals().copy().items():

    upper_name = str(
        object_name
    ).upper()

    if (
        (
            upper_name.startswith("V7")
            or
            upper_name.startswith("V8")
        )
        and
        (
            "SLEEVE" in upper_name
            or
            "TARGET" in upper_name
            or
            "WEIGHT" in upper_name
        )
    ):

        try:
            object_type = type(
                object_value
            ).__name__

            object_length = (
                len(object_value)
                if hasattr(
                    object_value,
                    "__len__",
                )
                else
                np.nan
            )

        except Exception:

            object_type = type(
                object_value
            ).__name__

            object_length = np.nan


        V12_SLEEVE_OBJECT_CANDIDATES.append(
            {
                "Object":
                    object_name,

                "Type":
                    object_type,

                "Length":
                    object_length,
            }
        )


V12_SLEEVE_OBJECT_CANDIDATES = pd.DataFrame(
    V12_SLEEVE_OBJECT_CANDIDATES
)


if not V12_SLEEVE_OBJECT_CANDIDATES.empty:

    V12_SLEEVE_OBJECT_CANDIDATES = (
        V12_SLEEVE_OBJECT_CANDIDATES
        .sort_values(
            "Object"
        )
        .reset_index(
            drop=True
        )
    )


# ==============================================================================
# 14. MASTER AUDIT
# ==============================================================================

V12_MASTER_AUDIT = pd.DataFrame(
    {
        "Metric": [

            "Version",

            "Status",

            "Primary objective",

            "Benchmark",

            "Core",

            "Satellite",

            "Frozen satellite resolved yet",

            "Stock-selection refit",

            "HMM",

            "State normalization",

            "State aggregation",

            "Rebalance sessions",

            "Minimum alpha weight",

            "Maximum alpha weight",

            "TQQQ floor",

            "Minimum stock weight",

            "Maximum stock weight",

            "Top-K",

            "Sector cap",

            "Risk cap",

            "Cash allowed",

            "Leverage above 100%",

            "Base TCA bps",

            "Reference AUM USD",

            "Post-result modification allowed",
        ],

        "Value": [

            "V12",

            "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER",

            V12_PRIMARY_OBJECTIVE,

            "TQQQ",

            "TQQQ",

            "FROZEN V7/V8 ALPHA SLEEVE",

            False,

            False,

            False,

            "CAUSAL EXPANDING PERCENTILE",

            "MEDIAN",

            21,

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            "NONE",

            False,

            False,

            10000.0
            *
            float(
                V10_BASE_TCA_RATE
            ),

            float(
                V10_REFERENCE_AUM_USD
            ),

            False,
        ],
    }
)


# ==============================================================================
# 15. OUTPUT
# ==============================================================================

print("\n1) V11 FINAL REJECTION")

display(
    pd.DataFrame(
        {
            "Metric": [

                "Version",

                "Status",

                "V11 final wealth",

                "TQQQ final wealth",

                "V11 relative wealth",

                "V11 minus TQQQ pp",

                "Economic result",
            ],

            "Value": [

                "V11",

                "REJECTED",

                float(
                    V11_FINAL_WEALTH
                ),

                float(
                    V11_TQQQ_FINAL_WEALTH
                ),

                float(
                    V11_RELATIVE_WEALTH
                ),

                float(
                    V11_MINUS_TQQQ_PP
                ),

                "100% TQQQ CLONE",
            ],
        }
    )
)


print("\n2) V12 MASTER RESEARCH AUDIT")

display(
    V12_MASTER_AUDIT
)


print(
    "\n3) EXISTING V7 / V8 SLEEVE-RELATED NOTEBOOK OBJECTS"
)


if V12_SLEEVE_OBJECT_CANDIDATES.empty:

    print(
        "No obvious sleeve-named objects were found. "
        "Block 2 will reconstruct the frozen sleeve from existing V7/V8 state."
    )

else:

    display(
        V12_SLEEVE_OBJECT_CANDIDATES
    )


print("\n4) V12 STATE FORMULA")

print(
    "Alpha weight = median("
)

print(
    "    1 - percentile(TQQQ / SMA252 - 1),"
)

print(
    "    1 - percentile(TQQQ / SMA63 - 1),"
)

print(
    "    percentile(TQQQ trailing 63d volatility),"
)

print(
    "    percentile(alpha sleeve effective N),"
)

print(
    "    1 - percentile(alpha sleeve max-name weight)"
)

print(
    ")"
)


print(
    "\n5) V11 FINAL REJECTION FINGERPRINT"
)

print(
    V11_FINAL_REJECTION_FINGERPRINT
)


print(
    "\n6) V12 RESEARCH CONTRACT FINGERPRINT"
)

print(
    V12_RESEARCH_CONTRACT_FINGERPRINT
)


print("\nINTEGRITY:")

print(
    "[+] Previous dependency-name bug removed."
)

print(
    "[+] V11 is permanently rejected."
)

print(
    "[+] V12 is a new research generation."
)

print(
    "[+] V12 architecture is now locked BEFORE performance."
)

print(
    "[+] Frozen V7/V8 satellite definition cannot be changed."
)

print(
    "[+] Exact notebook sleeve object will be resolved before performance."
)

print(
    "[+] No model was fitted."
)

print(
    "[+] No stock-selection rule was changed."
)

print(
    "[+] No performance was calculated."
)

print(
    "[+] No HMM."
)

print(
    "[+] No fitted state coefficient."
)

print(
    "[+] No performance-tuned threshold."
)

print(
    "[+] No minimum alpha weight."
)

print(
    "[+] No maximum alpha weight."
)

print(
    "[+] No TQQQ floor."
)

print(
    "[+] No minimum stock weight."
)

print(
    "[+] No maximum stock weight."
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


print("\nNEXT:")

print(
    "V12 BLOCK 2 — FROZEN V7/V8 SLEEVE OBJECT RESOLUTION "
    "+ CAUSAL STATE PANEL + EXECUTION PREFLIGHT."
)

print(
    "BLOCK 2 MUST RESOLVE AND VERIFY THE EXISTING SLEEVE "
    "BEFORE ANY V12 RETURN IS CALCULATED."
)

print("=" * 140)
