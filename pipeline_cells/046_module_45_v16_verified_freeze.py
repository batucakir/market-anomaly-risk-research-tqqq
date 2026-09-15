# MODULE 45 — V16 VERIFIED FREEZE
# Run in the same notebook, in module order.

# Verify computed values BEFORE the original freeze stores archived constants.
for _label,_actual,_expected in [('V16',V16_FINAL_WEALTH,4.365780),('V8 comparator',V16_RECOVERED_V8_FINAL,4.184169),('TQQQ comparator',TQQQ_COMPLETED_WEALTH,3.563433)]:
    if abs(float(_actual)-_expected)>0.00000051:
        raise RuntimeError(f'{_label} does not match the archived freeze: {_actual}. Freeze was not executed.')

# =============================================================================
# V16 — FINAL RESEARCH FREEZE + TRUE-OOS CONTRACT
# =============================================================================
#
# PURPOSE
# -------
# Freeze the successful V16 architecture exactly as observed.
#
# THIS BLOCK:
#   - does NOT refit anything
#   - does NOT recalculate research performance
#   - does NOT tune lambda
#   - does NOT use hindsight lambda=1.0
#   - does NOT modify V8
#   - creates a deterministic frozen snapshot for forward continuation
#
# TRUE OOS:
#   Research backcast ends: 2026-07-27
#   Architecture observed/frozen: 2026-09-13
#   Any market period already partially observable before freeze is NOT V16 OOS.
#   First scored V16 OOS portfolio must be generated strictly AFTER freeze.
# =============================================================================

import copy
import hashlib
import json
import pickle
import numpy as np
import pandas as pd

print("=" * 116)
print("V16 — FINAL RESEARCH FREEZE")
print("RESIDUAL-MOMENTUM TILT ON FROZEN V8")
print("+ TRUE FORWARD-OOS CONTRACT")
print("=" * 116)

# -----------------------------------------------------------------------------
# 1. FROZEN DATES / STATUS
# -----------------------------------------------------------------------------

V16_RESEARCH_BACKCAST_END = pd.Timestamp("2026-07-27")
V16_ARCHITECTURE_FREEZE_DATE = pd.Timestamp("2026-09-13")

# Conservative information cutoff:
# anything known up to the architecture-freeze date is treated as research info.
V16_INFORMATION_CUTOFF = pd.Timestamp("2026-09-13")

V16_STATUS = "FROZEN_RESEARCH_CHAMPION"
V16_TRUE_OOS_STATUS = "NOT_STARTED"

# -----------------------------------------------------------------------------
# 2. RESEARCH RESULT — VERIFY, DO NOT RECOMPUTE
# -----------------------------------------------------------------------------

# Values are the already-observed V16 result.
# They are NOT used as trading parameters.
V16_FROZEN_RESEARCH_RESULT = {
    "V16_completed_period_final_wealth": 4.365780,
    "V8_comparator_final_wealth":        4.184169,
    "TQQQ_comparator_final_wealth":      3.563433,
    "V16_minus_V8_pp":                  18.161096,
    "V16_minus_TQQQ_pp":                80.234643,
    "V16_over_V8_relative_wealth":       1.043404,
    "mean_residual_tilt_lambda_pct":    50.422551,
    "final_posterior_lambda_pct":       50.701749,
    "research_completed_periods":       33,
}

if not (
    V16_FROZEN_RESEARCH_RESULT["V16_completed_period_final_wealth"]
    >
    V16_FROZEN_RESEARCH_RESULT["V8_comparator_final_wealth"]
    >
    V16_FROZEN_RESEARCH_RESULT["TQQQ_comparator_final_wealth"]
):
    raise RuntimeError(
        "Frozen V16 research ranking is inconsistent. "
        "Freeze aborted."
    )

# -----------------------------------------------------------------------------
# 3. ARCHITECTURE CONTRACT
# -----------------------------------------------------------------------------

V16_FROZEN_ARCHITECTURE = {
    "version": "V16",

    "status": V16_STATUS,

    "primary_objective":
        "MAX_NET_TERMINAL_WEALTH",

    "primary_comparator":
        "FROZEN_V8",

    "secondary_comparator":
        "TQQQ",

    # Base architecture
    "base_strategy":
        "FROZEN_V8",

    "core_asset":
        "TQQQ",

    "base_tqqq_alpha_allocation":
        "UNCHANGED_FROM_FROZEN_V8",

    # New V16 economic hypothesis
    "modification_scope":
        "CROSS_SECTIONAL_COMPOSITION_INSIDE_V8_ALPHA_SLEEVE_ONLY",

    "stock_tilt":
        "TQQQ_RESIDUAL_12_MINUS_1_CROSS_SECTIONAL_MOMENTUM",

    "residual_definition":
        "STOCK_RETURN_MINUS_TQQQ_RETURN",

    "momentum_skip":
        "MOST_RECENT_21_TRADING_SESSIONS_EXCLUDED",

    "signal_timing":
        "SIGNAL_CLOSE_INFORMATION_ONLY",

    # Lambda allocation
    "tilt_allocator":
        "CAUSAL_UNIVERSAL_PORTFOLIO",

    "lambda_domain":
        "[0,1]",

    "posterior_use":
        "PRE_EVENT_POSTERIOR_MEAN",

    "posterior_update":
        "AFTER_COMPLETED_HOLDING_PERIOD_ONLY",

    "hindsight_best_lambda":
        "DIAGNOSTIC_ONLY_NEVER_TRADING_PARAMETER",

    # Portfolio restrictions
    "cash_allowed": False,
    "leverage_above_100pct": False,

    "minimum_stock_weight": None,
    "maximum_stock_weight": None,
    "top_k": None,
    "sector_cap": None,
    "risk_cap": None,

    # Trading
    "rebalance_frequency_sessions": 21,
    "base_linear_tca_bps": 2.0,

    # Research discipline
    "post_result_parameter_changes_allowed": False,

    "forbidden_changes": [
        "change residual-momentum lookback",
        "change 21-session skip",
        "change residual definition",
        "change V8 core/alpha allocation engine",
        "change lambda allocation formula",
        "set lambda to hindsight optimum",
        "performance-weight momentum horizons",
        "introduce Top-K after seeing results",
        "introduce arbitrary stock cap",
        "introduce arbitrary sector cap",
        "introduce arbitrary risk cap",
        "introduce strategic cash",
        "increase leverage above 100 percent",
        "change TCA after seeing results",
        "select future rules from research-period winners",
    ],
}

# -----------------------------------------------------------------------------
# 4. SNAPSHOT CURRENT V16 CONTINUATION OBJECTS
# -----------------------------------------------------------------------------
#
# We freeze only economically relevant / continuation-relevant V16 objects.
# Huge raw price/lifecycle panels are intentionally NOT duplicated.
# -----------------------------------------------------------------------------

V16_KEEP_TOKENS = (
    "PATH",
    "TARGET",
    "WEIGHT",
    "LAMBDA",
    "GRID",
    "EXPERT",
    "POSTERIOR",
    "WEALTH",
    "RETURN",
    "EVENT",
    "CONFIG",
    "FINGERPRINT",
    "SPEC",
    "DRIFT",
    "SLEEVE",
)

V16_EXCLUDE_TOKENS = (
    "PRICE",
    "LIFECYCLE",
    "MODEL_PANEL",
    "DAILY_PANEL",
    "ALL_PRICES",
)

V16_STATE_OBJECT_NAMES = []

for _name in list(globals().keys()):

    if not _name.startswith("V16_"):
        continue

    if _name.startswith("V16_FROZEN_"):
        continue

    if _name in {
        "V16_RESEARCH_BACKCAST_END",
        "V16_ARCHITECTURE_FREEZE_DATE",
        "V16_INFORMATION_CUTOFF",
        "V16_STATUS",
        "V16_TRUE_OOS_STATUS",
        "V16_KEEP_TOKENS",
        "V16_EXCLUDE_TOKENS",
        "V16_STATE_OBJECT_NAMES",
    }:
        continue

    upper_name = _name.upper()

    if not any(token in upper_name for token in V16_KEEP_TOKENS):
        continue

    if any(token in upper_name for token in V16_EXCLUDE_TOKENS):
        continue

    V16_STATE_OBJECT_NAMES.append(_name)

V16_STATE_OBJECT_NAMES = sorted(set(V16_STATE_OBJECT_NAMES))

V16_FROZEN_CONTINUATION_STATE = {}

for _name in V16_STATE_OBJECT_NAMES:
    try:
        V16_FROZEN_CONTINUATION_STATE[_name] = copy.deepcopy(
            globals()[_name]
        )
    except Exception:
        # Hashable/read-only fallback.
        V16_FROZEN_CONTINUATION_STATE[_name] = globals()[_name]

print("\n1) CONTINUATION STATE SNAPSHOT")
print(f"[+] Frozen V16 continuation objects: "
      f"{len(V16_FROZEN_CONTINUATION_STATE):,}")

if V16_STATE_OBJECT_NAMES:
    for _name in V16_STATE_OBJECT_NAMES:
        print(f"    - {_name}")
else:
    print(
        "[!] No named continuation objects matched the automatic filter.\n"
        "    Architecture/result freeze is still valid; forward block will\n"
        "    reconstruct state from the frozen V16 specification if required."
    )

# -----------------------------------------------------------------------------
# 5. FREEZE RELEVANT V8 FOUNDATION STATE AS REFERENCE
# -----------------------------------------------------------------------------

V16_V8_REFERENCE_NAMES = []

for _name in list(globals().keys()):

    if not _name.startswith("V8"):
        continue

    upper_name = _name.upper()

    if not any(
        token in upper_name
        for token in (
            "TARGET",
            "WEIGHT",
            "PATH",
            "GRID",
            "EXPERT",
            "POSTERIOR",
            "DRIFT",
            "FINGERPRINT",
        )
    ):
        continue

    if any(
        token in upper_name
        for token in (
            "PRICE",
            "LIFECYCLE",
            "ALL_PRICES",
        )
    ):
        continue

    V16_V8_REFERENCE_NAMES.append(_name)

V16_V8_REFERENCE_NAMES = sorted(set(V16_V8_REFERENCE_NAMES))

V16_FROZEN_V8_REFERENCE_STATE = {}

for _name in V16_V8_REFERENCE_NAMES:
    try:
        V16_FROZEN_V8_REFERENCE_STATE[_name] = copy.deepcopy(
            globals()[_name]
        )
    except Exception:
        V16_FROZEN_V8_REFERENCE_STATE[_name] = globals()[_name]

print("\n2) FROZEN V8 FOUNDATION REFERENCE")
print(f"[+] Referenced V8 state objects: "
      f"{len(V16_FROZEN_V8_REFERENCE_STATE):,}")

# -----------------------------------------------------------------------------
# 6. DETERMINISTIC STATE HASHES
# -----------------------------------------------------------------------------

def v16_object_hash(obj):
    """
    Stable-enough notebook freeze hash.
    Used only to detect future accidental mutation.
    """
    try:
        payload = pickle.dumps(
            obj,
            protocol=pickle.HIGHEST_PROTOCOL
        )
    except Exception:
        payload = repr(obj).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


V16_CONTINUATION_OBJECT_HASHES = {
    name: v16_object_hash(obj)
    for name, obj
    in V16_FROZEN_CONTINUATION_STATE.items()
}

V16_V8_REFERENCE_OBJECT_HASHES = {
    name: v16_object_hash(obj)
    for name, obj
    in V16_FROZEN_V8_REFERENCE_STATE.items()
}

# Architecture fingerprint
V16_ARCHITECTURE_JSON = json.dumps(
    V16_FROZEN_ARCHITECTURE,
    sort_keys=True,
    separators=(",", ":"),
    default=str,
)

V16_ARCHITECTURE_HASH = hashlib.sha256(
    V16_ARCHITECTURE_JSON.encode("utf-8")
).hexdigest()

# Research-result fingerprint
V16_RESEARCH_RESULT_JSON = json.dumps(
    V16_FROZEN_RESEARCH_RESULT,
    sort_keys=True,
    separators=(",", ":"),
    default=str,
)

V16_RESEARCH_RESULT_HASH = hashlib.sha256(
    V16_RESEARCH_RESULT_JSON.encode("utf-8")
).hexdigest()

# Master freeze fingerprint
V16_FREEZE_PAYLOAD = {
    "architecture_hash":
        V16_ARCHITECTURE_HASH,

    "research_result_hash":
        V16_RESEARCH_RESULT_HASH,

    "continuation_object_hashes":
        V16_CONTINUATION_OBJECT_HASHES,

    "v8_reference_hashes":
        V16_V8_REFERENCE_OBJECT_HASHES,

    "research_backcast_end":
        str(V16_RESEARCH_BACKCAST_END.date()),

    "information_cutoff":
        str(V16_INFORMATION_CUTOFF.date()),

    "architecture_freeze_date":
        str(V16_ARCHITECTURE_FREEZE_DATE.date()),
}

V16_FREEZE_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V16_FREEZE_PAYLOAD,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
).hexdigest()

# -----------------------------------------------------------------------------
# 7. TRUE FORWARD-OOS POLICY
# -----------------------------------------------------------------------------

V16_OOS_POLICY = {
    "research_history":
        "2023-10-18 through 2026-07-27 is research/backcast only",

    "architecture_freeze_date":
        "2026-09-13",

    "information_cutoff":
        "2026-09-13",

    "already_observed_market_data":
        "NOT eligible for V16 OOS scoring",

    "first_true_oos_decision":
        (
            "first scheduled V16 signal generated strictly after "
            "the architecture freeze using only information available "
            "at that signal close"
        ),

    "first_true_oos_execution":
        (
            "next trading-session execution following that fresh "
            "post-freeze signal"
        ),

    "scoring_rule":
        (
            "score only complete post-freeze holding periods; "
            "never score an already-partially-observed cycle"
        ),

    "posterior_rule":
        (
            "universal posterior may update only after an entire "
            "holding period has completed"
        ),

    "incumbent_comparators":
        [
            "FROZEN_V8",
            "TQQQ",
        ],

    "promotion_objective":
        "NET_TERMINAL_WEALTH",

    "research_retuning_after_freeze":
        False,
}

# -----------------------------------------------------------------------------
# 8. HUMAN-READABLE FREEZE RECORD
# -----------------------------------------------------------------------------

V16_FREEZE_STATUS = pd.DataFrame(
    [
        ["Version", "V16"],
        ["Status", V16_STATUS],
        [
            "Primary objective",
            "MAX_NET_TERMINAL_WEALTH",
        ],
        [
            "Research backcast end",
            str(V16_RESEARCH_BACKCAST_END.date()),
        ],
        [
            "Architecture freeze date",
            str(V16_ARCHITECTURE_FREEZE_DATE.date()),
        ],
        [
            "Information cutoff",
            str(V16_INFORMATION_CUTOFF.date()),
        ],
        [
            "Research final wealth",
            V16_FROZEN_RESEARCH_RESULT[
                "V16_completed_period_final_wealth"
            ],
        ],
        [
            "Frozen V8 wealth",
            V16_FROZEN_RESEARCH_RESULT[
                "V8_comparator_final_wealth"
            ],
        ],
        [
            "TQQQ wealth",
            V16_FROZEN_RESEARCH_RESULT[
                "TQQQ_comparator_final_wealth"
            ],
        ],
        [
            "V16 minus V8 pp",
            V16_FROZEN_RESEARCH_RESULT[
                "V16_minus_V8_pp"
            ],
        ],
        [
            "V16 minus TQQQ pp",
            V16_FROZEN_RESEARCH_RESULT[
                "V16_minus_TQQQ_pp"
            ],
        ],
        [
            "Mean residual lambda pct",
            V16_FROZEN_RESEARCH_RESULT[
                "mean_residual_tilt_lambda_pct"
            ],
        ],
        [
            "Final posterior lambda pct",
            V16_FROZEN_RESEARCH_RESULT[
                "final_posterior_lambda_pct"
            ],
        ],
        [
            "Hindsight lambda used",
            False,
        ],
        [
            "Post-result tuning allowed",
            False,
        ],
        [
            "True OOS status",
            V16_TRUE_OOS_STATUS,
        ],
        [
            "Frozen continuation objects",
            len(V16_FROZEN_CONTINUATION_STATE),
        ],
        [
            "Frozen V8 reference objects",
            len(V16_FROZEN_V8_REFERENCE_STATE),
        ],
    ],
    columns=["Metric", "Value"],
)

print("\n3) FINAL V16 FREEZE STATUS")
display(V16_FREEZE_STATUS)

print("\n4) FREEZE FINGERPRINTS")
print(
    "V16 architecture hash :",
    V16_ARCHITECTURE_HASH
)
print(
    "V16 research hash     :",
    V16_RESEARCH_RESULT_HASH
)
print(
    "V16 MASTER FREEZE     :",
    V16_FREEZE_FINGERPRINT
)

print("\n5) TRUE-OOS CONTRACT")
for key, value in V16_OOS_POLICY.items():
    print(f"{key}: {value}")

print("\n" + "=" * 116)
print("V16 FREEZE COMPLETE")
print("=" * 116)

print(
    "\n[+] V16 is now the FROZEN RESEARCH CHAMPION."
)
print(
    "[+] V8 remains the frozen shadow comparator."
)
print(
    "[+] TQQQ remains the market benchmark."
)
print(
    "[+] No V16 parameter may be changed after this point."
)
print(
    "[+] Historical V16 performance remains RESEARCH/BACKCAST."
)
print(
    "[+] TRUE V16 OOS HAS NOT STARTED YET."
)
print(
    "[+] The next step is ONE forward block:"
)
print(
    "    generate the first fresh post-freeze V16 decision, "
    "then track V16 vs V8 vs TQQQ without retuning."
)
print("=" * 116)
