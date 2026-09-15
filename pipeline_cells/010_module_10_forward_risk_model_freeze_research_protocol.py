# ==============================================================================
# MODULE 10 — FORWARD-RISK MODEL FREEZE / RESEARCH PROTOCOL
# ==============================================================================

import hashlib
import json


# ==============================================================================
# 1. REQUIRED OBJECTS
# ==============================================================================

required_objects = [
    "RANGE_ONLY_FEATURES",
    "BASE_RISK_FEATURES",
    "risk_range_only",
    "risk_base",
    "range_eval",
    "base_eval",
    "risk_comparison",
    "build_forward_rv_target",
    "run_causal_risk_forecaster",
]

missing_objects = [
    name
    for name in required_objects
    if name not in globals()
]

if missing_objects:
    raise RuntimeError(
        "MODULE 10 missing required objects: "
        f"{missing_objects}"
    )


# ==============================================================================
# 2. FROZEN CONFIGURATION
# ==============================================================================

RISK_FORECAST_VERSION = "RISK_V1_RANGE_RIDGE"

RISK_FORECAST_MODEL = "RANGE_RIDGE"

RISK_FORECAST_FEATURES = tuple(
    RANGE_ONLY_FEATURES
)

RISK_FORECAST_HORIZON = 3
RISK_FORECAST_MIN_TRAIN_TARGETS = 60
RISK_FORECAST_REFIT_EVERY = 10
RISK_FORECAST_RIDGE_ALPHA = 1.0

RISK_FORECAST_ARCHITECTURE = {
    "Version":
        RISK_FORECAST_VERSION,

    "Model":
        RISK_FORECAST_MODEL,

    "Features":
        list(
            RISK_FORECAST_FEATURES
        ),

    "Target":
        "Forward 3-bar same-session realized volatility",

    "Horizon_Bars":
        RISK_FORECAST_HORIZON,

    "Minimum_Training_Targets":
        RISK_FORECAST_MIN_TRAIN_TARGETS,

    "Refit_Every":
        RISK_FORECAST_REFIT_EVERY,

    "Ridge_Alpha":
        RISK_FORECAST_RIDGE_ALPHA,

    "Ridge_Solver":
        "lsqr",

    "Target_Transform":
        "log",

    "Inverse_Transform":
        "exp",

    "Target_Availability_Rule":
        "Target_End_Time <= current_time",

    "Session_Aware_Target":
        True,

    "Post_Hoc_Tuning_Allowed":
        False,
}


# ==============================================================================
# 3. RESEARCH STATUS
# ==============================================================================

RISK_FORECAST_RESEARCH_STATUS = {
    "Primary_Model":
        "RANGE_RIDGE",

    "Secondary_Model":
        "BASE_FEATURES",

    "Base_Features":
        list(
            BASE_RISK_FEATURES
        ),

    "Benchmarks": [
        "RAW_LOG_RANGE",
        "HIST_MEAN",
        "HIST_MEDIAN",
        "PERSISTENCE",
    ],

    "Non_Overlap_Rule":
        "Every third forecast origin within session",

    "Selection_Note":
        (
            "RANGE_RIDGE remains the frozen primary model. "
            "Non-overlapping results are robustness evidence only."
        ),

    "Sizing_Rule":
        None,

    "Trading_Rule":
        None,
}


# ==============================================================================
# 4. SAFETY CHECKS
# ==============================================================================

if RISK_FORECAST_FEATURES != ("Log_Range",):
    raise RuntimeError(
        "Frozen RANGE_RIDGE feature set changed."
    )

if RISK_FORECAST_HORIZON != 3:
    raise RuntimeError(
        "Frozen risk horizon must remain 3 bars."
    )

if RISK_FORECAST_MIN_TRAIN_TARGETS != 60:
    raise RuntimeError(
        "Frozen minimum training history changed."
    )

if RISK_FORECAST_REFIT_EVERY != 10:
    raise RuntimeError(
        "Frozen refit frequency changed."
    )

if not np.isclose(
    RISK_FORECAST_RIDGE_ALPHA,
    1.0,
):
    raise RuntimeError(
        "Frozen Ridge alpha changed."
    )

if (
    RISK_FORECAST_RESEARCH_STATUS["Sizing_Rule"]
    is not None
):
    raise RuntimeError(
        "MODULE 10 must not introduce position sizing."
    )

if (
    RISK_FORECAST_RESEARCH_STATUS["Trading_Rule"]
    is not None
):
    raise RuntimeError(
        "MODULE 10 must not introduce a trading rule."
    )


# ==============================================================================
# 5. FINGERPRINT
# ==============================================================================

RISK_FREEZE_PAYLOAD = {
    "Architecture":
        RISK_FORECAST_ARCHITECTURE,

    "Research_Status":
        RISK_FORECAST_RESEARCH_STATUS,
}

RISK_FREEZE_JSON = json.dumps(
    RISK_FREEZE_PAYLOAD,
    sort_keys=True,
    separators=(",", ":"),
)

RISK_MODEL_FINGERPRINT = hashlib.sha256(
    RISK_FREEZE_JSON.encode("utf-8")
).hexdigest()


# ==============================================================================
# 6. FUTURE RESEARCH PROTOCOL
# ==============================================================================

RISK_RESEARCH_PROTOCOL = [
    "Do not change the frozen feature set after seeing future results.",
    "Do not change the 3-bar horizon after seeing future results.",
    "Do not retune Ridge alpha on the current sample.",
    "Do not use the non-overlapping sample for post-hoc model selection.",
    "Do not convert forecast risk into arbitrary exposure thresholds.",
    "Do not use HMM states as an automatic sizing rule.",
    "Test any new risk model as a separate challenger.",
    "Test any sizing or trading rule separately.",
]


# ==============================================================================
# 7. OUTPUT
# ==============================================================================

print("=" * 100)
print("MODULE 10 — FORWARD-RISK MODEL FREEZE / RESEARCH PROTOCOL")
print("=" * 100)

print(
    f"\nVersion       : {RISK_FORECAST_VERSION}"
)

print(
    f"Primary model : {RISK_FORECAST_MODEL}"
)

print(
    f"Features      : {list(RISK_FORECAST_FEATURES)}"
)

print(
    f"Horizon       : {RISK_FORECAST_HORIZON} bars"
)

print(
    f"Min train     : {RISK_FORECAST_MIN_TRAIN_TARGETS}"
)

print(
    f"Refit every   : {RISK_FORECAST_REFIT_EVERY}"
)

print(
    f"Ridge alpha   : {RISK_FORECAST_RIDGE_ALPHA}"
)

print(
    f"Fingerprint   : {RISK_MODEL_FINGERPRINT}"
)

print("\nResearch status:")
print("  Forward-risk forecasting layer is frozen.")
print("  No position-sizing rule is frozen.")
print("  No trading rule is introduced.")
print("  Non-overlapping results remain robustness evidence only.")

print("\nFuture protocol:")

for rule in RISK_RESEARCH_PROTOCOL:
    print(f"  - {rule}")

print("\n[+] MODULE 10 COMPLETE.")
