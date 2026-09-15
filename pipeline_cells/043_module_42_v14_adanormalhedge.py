# MODULE 42 — V14 ADANORMALHEDGE
# Run in the same notebook, in module order.

# =============================================================================
# V14 — ONE-SHOT PARAMETER-FREE ADANORMALHEDGE CHAMPION ALLOCATOR
# V8 CHAMPION + TQQQ
#
# OBJECTIVE:
#   Beat the repaired-ledger V8 champion in net terminal wealth,
#   while preserving strict causal online allocation.
#
# ARCHITECTURE:
#   Expert 1 = frozen V8
#   Expert 2 = TQQQ
#   Allocator = AdaNormalHedge
#   No fitted model
#   No parameter search
#   No rolling-window tuning
#   No stock-selection changes
#   No leverage > 100%
#   No cash
#   No V8 modification
#
# IMPORTANT:
#   The research verdict uses ONLY the completed holding periods shared by
#   V8 and TQQQ. This avoids contaminating the test with terminal-only
#   rebalance accounting differences.
# =============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hashlib
import json

print("=" * 140)
print("V14 — ONE-SHOT PARAMETER-FREE ADANORMALHEDGE CHAMPION ALLOCATOR")
print("V8 RE-ACCOUNTED + TQQQ")
print("=" * 140)

# =============================================================================
# 1. REQUIRED INPUT
# =============================================================================

if "event_compare" not in globals():
    raise RuntimeError(
        "Required object 'event_compare' was not found. "
        "Run the completed V8/V12/TQQQ comparison block first."
    )

V14_SOURCE = event_compare.copy()

# -----------------------------------------------------------------------------
# Column resolver
# -----------------------------------------------------------------------------

def v14_find_column(df, exact_names=None, contains_all=None):
    exact_names = exact_names or []
    contains_all = contains_all or []

    for name in exact_names:
        if name in df.columns:
            return name

    for col in df.columns:
        text = str(col).upper()
        if all(token.upper() in text for token in contains_all):
            return col

    return None


V14_V8_RETURN_COL = v14_find_column(
    V14_SOURCE,
    exact_names=[
        "V8_Return_Pct",
        "V8_Net_Return_Pct",
        "V8_Return"
    ],
    contains_all=["V8", "RETURN"]
)

V14_TQQQ_RETURN_COL = v14_find_column(
    V14_SOURCE,
    exact_names=[
        "TQQQ_Return_Pct",
        "TQQQ_Net_Return_Pct",
        "TQQQ_Return"
    ],
    contains_all=["TQQQ", "RETURN"]
)

V14_EXECUTION_COL = v14_find_column(
    V14_SOURCE,
    exact_names=["Execution_Date"],
    contains_all=["EXECUTION", "DATE"]
)

V14_EXIT_COL = v14_find_column(
    V14_SOURCE,
    exact_names=["Exit_Date"],
    contains_all=["EXIT", "DATE"]
)

V14_SIGNAL_COL = v14_find_column(
    V14_SOURCE,
    exact_names=["Signal_Date"],
    contains_all=["SIGNAL", "DATE"]
)

if V14_V8_RETURN_COL is None:
    raise RuntimeError("Could not determine the V8 return column.")

if V14_TQQQ_RETURN_COL is None:
    raise RuntimeError("Could not determine the TQQQ return column.")

if V14_EXECUTION_COL is None:
    raise RuntimeError("Could not determine Execution_Date.")

print(f"[+] Source event table : event_compare")
print(f"[+] V8 return column   : {V14_V8_RETURN_COL}")
print(f"[+] TQQQ return column : {V14_TQQQ_RETURN_COL}")
print(f"[+] Execution column   : {V14_EXECUTION_COL}")
print(f"[+] Exit column        : {V14_EXIT_COL}")
print(f"[+] Signal column      : {V14_SIGNAL_COL}")

# =============================================================================
# 2. BUILD EXACT COMPLETED-HOLDING-PERIOD PANEL
# =============================================================================

V14_EVENTS = V14_SOURCE.copy()

V14_EVENTS[V14_EXECUTION_COL] = pd.to_datetime(
    V14_EVENTS[V14_EXECUTION_COL]
).dt.normalize()

if V14_EXIT_COL is not None:
    V14_EVENTS[V14_EXIT_COL] = pd.to_datetime(
        V14_EVENTS[V14_EXIT_COL]
    ).dt.normalize()

if V14_SIGNAL_COL is not None:
    V14_EVENTS[V14_SIGNAL_COL] = pd.to_datetime(
        V14_EVENTS[V14_SIGNAL_COL]
    ).dt.normalize()

V14_EVENTS[V14_V8_RETURN_COL] = pd.to_numeric(
    V14_EVENTS[V14_V8_RETURN_COL],
    errors="coerce"
)

V14_EVENTS[V14_TQQQ_RETURN_COL] = pd.to_numeric(
    V14_EVENTS[V14_TQQQ_RETURN_COL],
    errors="coerce"
)

V14_EVENTS = V14_EVENTS.dropna(
    subset=[
        V14_EXECUTION_COL,
        V14_V8_RETURN_COL,
        V14_TQQQ_RETURN_COL
    ]
).copy()

# Keep only genuine holding periods.
if V14_EXIT_COL is not None:
    V14_EVENTS = V14_EVENTS[
        V14_EVENTS[V14_EXIT_COL].notna()
        &
        (
            V14_EVENTS[V14_EXIT_COL]
            >
            V14_EVENTS[V14_EXECUTION_COL]
        )
    ].copy()

V14_EVENTS = (
    V14_EVENTS
    .sort_values(V14_EXECUTION_COL)
    .reset_index(drop=True)
)

if len(V14_EVENTS) < 10:
    raise RuntimeError(
        f"Only {len(V14_EVENTS)} completed periods were found. "
        "V14 stopped before performance calculation."
    )

# Returns are stored in percentage points.
V14_V8_RET = (
    V14_EVENTS[V14_V8_RETURN_COL]
    .to_numpy(dtype=float)
    / 100.0
)

V14_TQQQ_RET = (
    V14_EVENTS[V14_TQQQ_RETURN_COL]
    .to_numpy(dtype=float)
    / 100.0
)

V14_EXPERT_RET = np.column_stack(
    [
        V14_V8_RET,
        V14_TQQQ_RET
    ]
)

V14_EXPERT_GROSS = 1.0 + V14_EXPERT_RET

if (
    ~np.isfinite(V14_EXPERT_GROSS)
).any():
    raise RuntimeError(
        "Non-finite expert gross returns detected."
    )

if (
    V14_EXPERT_GROSS <= 0.0
).any():
    raise RuntimeError(
        "An expert holding-period gross return is <= 0. "
        "AdaNormalHedge test stopped."
    )

V14_N = len(V14_EVENTS)

print(f"\n[+] Completed holding periods: {V14_N}")

# =============================================================================
# 3. CAUSAL MATURITY MAP
# =============================================================================
#
# Allocation for event t may use ONLY outcomes that were fully observable
# before the event-t signal.
#
# If Signal_Date exists:
#     update event j only when Exit_Date_j <= Signal_Date_t.
#
# Otherwise:
#     use a strict one-event-delayed convention:
#     event t can update through event t-2 only.
#
# This avoids using an event return that finishes on the same close at which
# the next portfolio is executed.
# =============================================================================

if (
    V14_SIGNAL_COL is not None
    and
    V14_EXIT_COL is not None
):

    V14_SIGNAL_DATES = (
        V14_EVENTS[V14_SIGNAL_COL]
        .to_numpy()
    )

    V14_EXIT_DATES = (
        V14_EVENTS[V14_EXIT_COL]
        .to_numpy()
    )

    V14_USE_SIGNAL_CAUSALITY = True

else:

    V14_SIGNAL_DATES = None
    V14_EXIT_DATES = None
    V14_USE_SIGNAL_CAUSALITY = False

print(
    "[+] Causal update convention:",
    (
        "SIGNAL-DATE MATURITY"
        if V14_USE_SIGNAL_CAUSALITY
        else
        "STRICT ONE-EVENT DELAY"
    )
)

# =============================================================================
# 4. ADANORMALHEDGE
# =============================================================================
#
# AdaNormalHedge:
#
#   Phi(R,C) = exp( [R]_+^2 / (3C) )
#
# Prediction weight uses:
#
#   w(R,C)
#     = 0.5 * [
#           Phi(R + 1, C + 1)
#           -
#           Phi(R - 1, C + 1)
#       ]
#
# Expert losses must lie in [0,1].
#
# We construct a parameter-free relative loss from expert gross wealth:
#
#   relative_score_i = gross_i / sum(gross)
#   loss_i           = 1 - relative_score_i
#
# Therefore:
#   better wealth outcome -> lower loss.
#
# No return threshold, learning rate, volatility target, or fitted parameter.
# =============================================================================

def v14_adanormal_weight(R, C):

    Rp = np.maximum(R + 1.0, 0.0)
    Rm = np.maximum(R - 1.0, 0.0)

    denom = 3.0 * (C + 1.0)

    phi_plus = np.exp(
        np.minimum(
            (Rp * Rp) / denom,
            700.0
        )
    )

    phi_minus = np.exp(
        np.minimum(
            (Rm * Rm) / denom,
            700.0
        )
    )

    return 0.5 * (
        phi_plus
        -
        phi_minus
    )


def v14_current_allocation(R, C, prior):

    raw = (
        prior
        *
        v14_adanormal_weight(
            R,
            C
        )
    )

    if (
        (not np.isfinite(raw).all())
        or
        raw.sum() <= 0.0
    ):
        raw = prior.copy()

    p = raw / raw.sum()

    p = np.maximum(
        p,
        0.0
    )

    p = p / p.sum()

    return p


# Equal prior is the canonical uninformative expert prior.
V14_PRIOR = np.array(
    [
        0.5,   # V8
        0.5    # TQQQ
    ],
    dtype=float
)

V14_R = np.zeros(
    2,
    dtype=float
)

V14_C = np.zeros(
    2,
    dtype=float
)

# =============================================================================
# 5. FIXED EXECUTION-COST CONVENTION
# =============================================================================

V14_BASE_TCA_BPS = 2.0
V14_BASE_TCA_RATE = (
    V14_BASE_TCA_BPS
    / 10000.0
)

# =============================================================================
# 6. WALK-FORWARD TEST
# =============================================================================

V14_PROCESSED_OUTCOMES = set()

V14_DECISION_WEIGHTS = []
V14_DRIFTED_WEIGHTS = []
V14_ROWS = []

V14_WEALTH = 1.0

V14_PREVIOUS_DRIFTED_WEIGHT = None


def v14_update_learner(event_index):

    global V14_R, V14_C

    gross = V14_EXPERT_GROSS[
        event_index
    ].copy()

    # Parameter-free bounded relative loss.
    score = (
        gross
        /
        gross.sum()
    )

    expert_loss = (
        1.0
        -
        score
    )

    p_used = np.asarray(
        V14_DECISION_WEIGHTS[
            event_index
        ],
        dtype=float
    )

    portfolio_loss = float(
        np.dot(
            p_used,
            expert_loss
        )
    )

    regret = (
        portfolio_loss
        -
        expert_loss
    )

    V14_R[:] = (
        V14_R
        +
        regret
    )

    V14_C[:] = (
        V14_C
        +
        np.abs(regret)
    )


for t in range(V14_N):

    # -------------------------------------------------------------------------
    # 6A. Update learner ONLY with outcomes mature before this decision.
    # -------------------------------------------------------------------------

    if V14_USE_SIGNAL_CAUSALITY:

        current_signal = pd.Timestamp(
            V14_SIGNAL_DATES[t]
        )

        for j in range(t):

            if j in V14_PROCESSED_OUTCOMES:
                continue

            prior_exit = pd.Timestamp(
                V14_EXIT_DATES[j]
            )

            if prior_exit <= current_signal:

                v14_update_learner(j)

                V14_PROCESSED_OUTCOMES.add(j)

    else:

        mature_index = t - 2

        if (
            mature_index >= 0
            and
            mature_index not in V14_PROCESSED_OUTCOMES
        ):

            v14_update_learner(
                mature_index
            )

            V14_PROCESSED_OUTCOMES.add(
                mature_index
            )

    # -------------------------------------------------------------------------
    # 6B. Pre-event allocation
    # -------------------------------------------------------------------------

    p = v14_current_allocation(
        V14_R,
        V14_C,
        V14_PRIOR
    )

    V14_DECISION_WEIGHTS.append(
        p.copy()
    )

    # -------------------------------------------------------------------------
    # 6C. Meta-level turnover
    # -------------------------------------------------------------------------

    if V14_PREVIOUS_DRIFTED_WEIGHT is None:

        # Underlying V8/TQQQ returns already contain their own first-entry
        # execution accounting. Do not double-charge initial establishment.
        turnover = 0.0

    else:

        turnover = float(
            np.abs(
                p
                -
                V14_PREVIOUS_DRIFTED_WEIGHT
            ).sum()
        )

    meta_cost_rate = (
        V14_BASE_TCA_RATE
        *
        turnover
    )

    # -------------------------------------------------------------------------
    # 6D. Event gross return
    # -------------------------------------------------------------------------

    expert_gross = (
        V14_EXPERT_GROSS[t]
    )

    portfolio_gross_before_meta_cost = float(
        np.dot(
            p,
            expert_gross
        )
    )

    portfolio_gross_after_meta_cost = (
        portfolio_gross_before_meta_cost
        *
        (
            1.0
            -
            meta_cost_rate
        )
    )

    event_net_return = (
        portfolio_gross_after_meta_cost
        -
        1.0
    )

    V14_WEALTH *= (
        1.0
        +
        event_net_return
    )

    # -------------------------------------------------------------------------
    # 6E. Drift sleeve weights through the holding period
    # -------------------------------------------------------------------------

    drifted = (
        p
        *
        expert_gross
    )

    drifted = (
        drifted
        /
        drifted.sum()
    )

    V14_DRIFTED_WEIGHTS.append(
        drifted.copy()
    )

    V14_PREVIOUS_DRIFTED_WEIGHT = (
        drifted.copy()
    )

    row = {
        "Event":
            t + 1,

        "Execution_Date":
            V14_EVENTS.loc[
                t,
                V14_EXECUTION_COL
            ],

        "V8_Weight_Pct":
            100.0
            *
            p[0],

        "TQQQ_Weight_Pct":
            100.0
            *
            p[1],

        "Meta_Turnover":
            turnover,

        "Meta_Cost_bps":
            10000.0
            *
            meta_cost_rate,

        "V8_Return_Pct":
            100.0
            *
            V14_V8_RET[t],

        "TQQQ_Return_Pct":
            100.0
            *
            V14_TQQQ_RET[t],

        "V14_Net_Return_Pct":
            100.0
            *
            event_net_return,

        "V14_Wealth":
            V14_WEALTH,

        "Processed_Outcomes_Before_Decision":
            len(
                V14_PROCESSED_OUTCOMES
            )
    }

    if V14_EXIT_COL is not None:
        row["Exit_Date"] = (
            V14_EVENTS.loc[
                t,
                V14_EXIT_COL
            ]
        )

    if V14_SIGNAL_COL is not None:
        row["Signal_Date"] = (
            V14_EVENTS.loc[
                t,
                V14_SIGNAL_COL
            ]
        )

    V14_ROWS.append(
        row
    )


V14_PATH = pd.DataFrame(
    V14_ROWS
)

# =============================================================================
# 7. APPLES-TO-APPLES COMPLETED-PERIOD WEALTH
# =============================================================================

V14_FINAL_WEALTH = float(
    V14_WEALTH
)

V14_V8_COMPLETED_WEALTH = float(
    np.prod(
        1.0
        +
        V14_V8_RET
    )
)

V14_TQQQ_COMPLETED_WEALTH = float(
    np.prod(
        1.0
        +
        V14_TQQQ_RET
    )
)

V14_FINAL_RETURN_PCT = (
    100.0
    *
    (
        V14_FINAL_WEALTH
        -
        1.0
    )
)

V14_V8_RETURN_PCT = (
    100.0
    *
    (
        V14_V8_COMPLETED_WEALTH
        -
        1.0
    )
)

V14_TQQQ_RETURN_PCT = (
    100.0
    *
    (
        V14_TQQQ_COMPLETED_WEALTH
        -
        1.0
    )
)

V14_MINUS_V8_PP = (
    V14_FINAL_RETURN_PCT
    -
    V14_V8_RETURN_PCT
)

V14_MINUS_TQQQ_PP = (
    V14_FINAL_RETURN_PCT
    -
    V14_TQQQ_RETURN_PCT
)

V14_BEATS_V8 = bool(
    V14_FINAL_WEALTH
    >
    V14_V8_COMPLETED_WEALTH
)

V14_BEATS_TQQQ = bool(
    V14_FINAL_WEALTH
    >
    V14_TQQQ_COMPLETED_WEALTH
)

# =============================================================================
# 8. TRAILING WINDOW ROBUSTNESS
# =============================================================================

V14_NET_RET = (
    V14_PATH[
        "V14_Net_Return_Pct"
    ].to_numpy(dtype=float)
    / 100.0
)

V14_WINDOWS = [
    ("~1M", 1),
    ("~3M", 3),
    ("~6M", 6),
    ("~12M", 12),
    ("~24M", 24)
]

V14_ROBUSTNESS_ROWS = []

for label, periods in V14_WINDOWS:

    if periods > V14_N:
        continue

    v14_r = (
        np.prod(
            1.0
            +
            V14_NET_RET[-periods:]
        )
        -
        1.0
    )

    v8_r = (
        np.prod(
            1.0
            +
            V14_V8_RET[-periods:]
        )
        -
        1.0
    )

    tqqq_r = (
        np.prod(
            1.0
            +
            V14_TQQQ_RET[-periods:]
        )
        -
        1.0
    )

    V14_ROBUSTNESS_ROWS.append(
        {
            "Window":
                label,

            "Periods":
                periods,

            "V14_Return_Pct":
                100.0
                *
                v14_r,

            "V8_Return_Pct":
                100.0
                *
                v8_r,

            "TQQQ_Return_Pct":
                100.0
                *
                tqqq_r,

            "V14_Minus_V8_pp":
                100.0
                *
                (
                    v14_r
                    -
                    v8_r
                ),

            "V14_Minus_TQQQ_pp":
                100.0
                *
                (
                    v14_r
                    -
                    tqqq_r
                ),

            "V14_Beats_V8":
                bool(
                    v14_r
                    >
                    v8_r
                ),

            "V14_Beats_TQQQ":
                bool(
                    v14_r
                    >
                    tqqq_r
                )
        }
    )

V14_ROBUSTNESS_ROWS.append(
    {
        "Window":
            "ALL_COMPLETED",

        "Periods":
            V14_N,

        "V14_Return_Pct":
            V14_FINAL_RETURN_PCT,

        "V8_Return_Pct":
            V14_V8_RETURN_PCT,

        "TQQQ_Return_Pct":
            V14_TQQQ_RETURN_PCT,

        "V14_Minus_V8_pp":
            V14_MINUS_V8_PP,

        "V14_Minus_TQQQ_pp":
            V14_MINUS_TQQQ_PP,

        "V14_Beats_V8":
            V14_BEATS_V8,

        "V14_Beats_TQQQ":
            V14_BEATS_TQQQ
    }
)

V14_ROBUSTNESS = pd.DataFrame(
    V14_ROBUSTNESS_ROWS
)

V14_ALL_WINDOWS_BEAT_TQQQ = bool(
    V14_ROBUSTNESS[
        "V14_Beats_TQQQ"
    ].all()
)

V14_ALL_WINDOWS_BEAT_V8 = bool(
    V14_ROBUSTNESS[
        "V14_Beats_V8"
    ].all()
)

# =============================================================================
# 9. SUMMARY
# =============================================================================

V14_TOTAL_META_TURNOVER = float(
    V14_PATH[
        "Meta_Turnover"
    ].sum()
)

V14_MEAN_META_TURNOVER = float(
    V14_PATH[
        "Meta_Turnover"
    ].mean()
)

V14_MEAN_V8_WEIGHT = float(
    V14_PATH[
        "V8_Weight_Pct"
    ].mean()
)

V14_MEAN_TQQQ_WEIGHT = float(
    V14_PATH[
        "TQQQ_Weight_Pct"
    ].mean()
)

V14_SUMMARY = pd.DataFrame(
    [
        [
            "Completed holding periods",
            V14_N
        ],
        [
            "V14 final wealth",
            V14_FINAL_WEALTH
        ],
        [
            "V14 net return pct",
            V14_FINAL_RETURN_PCT
        ],
        [
            "V8 completed-period wealth",
            V14_V8_COMPLETED_WEALTH
        ],
        [
            "V8 completed-period return pct",
            V14_V8_RETURN_PCT
        ],
        [
            "TQQQ completed-period wealth",
            V14_TQQQ_COMPLETED_WEALTH
        ],
        [
            "TQQQ completed-period return pct",
            V14_TQQQ_RETURN_PCT
        ],
        [
            "V14 minus V8 pp",
            V14_MINUS_V8_PP
        ],
        [
            "V14 minus TQQQ pp",
            V14_MINUS_TQQQ_PP
        ],
        [
            "V14 / V8 relative wealth",
            (
                V14_FINAL_WEALTH
                /
                V14_V8_COMPLETED_WEALTH
            )
        ],
        [
            "Mean V8 allocation pct",
            V14_MEAN_V8_WEIGHT
        ],
        [
            "Mean TQQQ allocation pct",
            V14_MEAN_TQQQ_WEIGHT
        ],
        [
            "Total meta turnover",
            V14_TOTAL_META_TURNOVER
        ],
        [
            "Mean meta turnover",
            V14_MEAN_META_TURNOVER
        ],
        [
            "V14 beats V8",
            V14_BEATS_V8
        ],
        [
            "V14 beats TQQQ",
            V14_BEATS_TQQQ
        ],
        [
            "All declared windows beat V8",
            V14_ALL_WINDOWS_BEAT_V8
        ],
        [
            "All declared windows beat TQQQ",
            V14_ALL_WINDOWS_BEAT_TQQQ
        ]
    ],
    columns=[
        "Metric",
        "Value"
    ]
)

print("\n1) V14 FINAL ECONOMIC RESULT")
display(
    V14_SUMMARY
)

print("\n2) TRAILING MULTI-PERIOD ROBUSTNESS")
display(
    V14_ROBUSTNESS
)

print("\n3) LAST 12 V14 EVENTS")
display(
    V14_PATH.tail(12)
)

# =============================================================================
# 10. WEALTH PATH
# =============================================================================

V14_V8_WEALTH_PATH = np.cumprod(
    1.0
    +
    V14_V8_RET
)

V14_TQQQ_WEALTH_PATH = np.cumprod(
    1.0
    +
    V14_TQQQ_RET
)

V14_WEALTH_PATH = (
    V14_PATH[
        "V14_Wealth"
    ].to_numpy(dtype=float)
)

if V14_EXIT_COL is not None:
    V14_PLOT_DATES = pd.to_datetime(
        V14_EVENTS[
            V14_EXIT_COL
        ]
    )
else:
    V14_PLOT_DATES = pd.to_datetime(
        V14_EVENTS[
            V14_EXECUTION_COL
        ]
    )

plt.figure(
    figsize=(15, 7)
)

plt.plot(
    V14_PLOT_DATES,
    V14_WEALTH_PATH,
    linewidth=2.4,
    label="V14 AdaNormalHedge"
)

plt.plot(
    V14_PLOT_DATES,
    V14_V8_WEALTH_PATH,
    linewidth=2.1,
    label="V8 Champion"
)

plt.plot(
    V14_PLOT_DATES,
    V14_TQQQ_WEALTH_PATH,
    linewidth=2.1,
    label="TQQQ"
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1.0
)

plt.title(
    "V14 vs V8 vs TQQQ — COMPLETED-PERIOD NET WEALTH"
)

plt.xlabel(
    "Date"
)

plt.ylabel(
    "Wealth Multiple"
)

plt.grid(
    True,
    alpha=0.25
)

plt.legend()

plt.tight_layout()
plt.show()

# =============================================================================
# 11. ALLOCATION PATH
# =============================================================================

plt.figure(
    figsize=(15, 6)
)

plt.plot(
    V14_EVENTS[
        V14_EXECUTION_COL
    ],
    V14_PATH[
        "V8_Weight_Pct"
    ],
    linewidth=2.1,
    label="V8 Weight"
)

plt.plot(
    V14_EVENTS[
        V14_EXECUTION_COL
    ],
    V14_PATH[
        "TQQQ_Weight_Pct"
    ],
    linewidth=2.1,
    label="TQQQ Weight"
)

plt.axhline(
    50.0,
    linestyle="--",
    linewidth=1.0
)

plt.ylim(
    -2,
    102
)

plt.title(
    "V14 — CAUSAL ADANORMALHEDGE ALLOCATION"
)

plt.xlabel(
    "Execution Date"
)

plt.ylabel(
    "Portfolio Weight (%)"
)

plt.grid(
    True,
    alpha=0.25
)

plt.legend()

plt.tight_layout()
plt.show()

# =============================================================================
# 12. FINGERPRINT
# =============================================================================

V14_SPEC = {
    "version":
        "V14",

    "architecture":
        "PARAMETER_FREE_ADANORMALHEDGE",

    "experts":
        [
            "FROZEN_V8_REACCOUNTED",
            "TQQQ"
        ],

    "expert_prior":
        [
            0.5,
            0.5
        ],

    "loss_mapping":
        "1_MINUS_GROSS_RETURN_SHARE",

    "causal_update":
        (
            "SIGNAL_DATE_MATURITY"
            if V14_USE_SIGNAL_CAUSALITY
            else
            "STRICT_ONE_EVENT_DELAY"
        ),

    "base_tca_bps":
        V14_BASE_TCA_BPS,

    "cash":
        False,

    "leverage_above_100":
        False,

    "parameter_search":
        False,

    "model_fit":
        False,

    "stock_selection_change":
        False
}

V14_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V14_SPEC,
        sort_keys=True
    ).encode()
).hexdigest()

print("\n4) V14 RESEARCH FINGERPRINT")
print(
    V14_RESEARCH_FINGERPRINT
)

# =============================================================================
# 13. ONE-SHOT VERDICT
# =============================================================================

if (
    V14_BEATS_V8
    and
    V14_BEATS_TQQQ
):

    V14_RESULT = (
        "PASS_TO_CHALLENGE_V8"
    )

else:

    V14_RESULT = (
        "FAIL_TO_BEAT_V8"
    )

print("\n" + "=" * 140)
print("V14 ONE-SHOT RESEARCH VERDICT")
print("=" * 140)

print(
    f"V14 final wealth       : {V14_FINAL_WEALTH:.6f}"
)

print(
    f"V8 completed wealth    : {V14_V8_COMPLETED_WEALTH:.6f}"
)

print(
    f"TQQQ completed wealth  : {V14_TQQQ_COMPLETED_WEALTH:.6f}"
)

print(
    f"V14 minus V8           : {V14_MINUS_V8_PP:+.6f} pp"
)

print(
    f"V14 minus TQQQ         : {V14_MINUS_TQQQ_PP:+.6f} pp"
)

print(
    f"V14 beats V8           : {V14_BEATS_V8}"
)

print(
    f"V14 beats TQQQ         : {V14_BEATS_TQQQ}"
)

print(
    f"All windows beat V8    : {V14_ALL_WINDOWS_BEAT_V8}"
)

print(
    f"All windows beat TQQQ  : {V14_ALL_WINDOWS_BEAT_TQQQ}"
)

print(
    f"V14 RESULT             : {V14_RESULT}"
)

print("\nINTEGRITY:")
print("[+] Frozen V8 returns were not changed.")
print("[+] TQQQ returns were not changed.")
print("[+] No model was fitted.")
print("[+] No learning rate was selected.")
print("[+] No rolling lookback was selected.")
print("[+] No threshold was fitted.")
print("[+] No performance-based parameter search occurred.")
print("[+] Meta allocation used only causally matured outcomes.")
print("[+] Underlying execution costs remain inside V8/TQQQ returns.")
print("[+] Additional meta turnover cost was charged.")
print("[+] No cash.")
print("[+] No leverage above 100%.")
print("[+] No post-result V14 modification is permitted.")

print("=" * 140)
restored_register('V14', V14_FINAL_WEALTH, V14_PATH, 'V14_Wealth', 'Close / completed periods, no terminal rebalance', 'Historically rejected')
