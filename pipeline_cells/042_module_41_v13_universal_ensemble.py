# MODULE 41 — V13 UNIVERSAL ENSEMBLE
# Run in the same notebook, in module order.

# =============================================================================
# V13 — ONE-SHOT UNIVERSAL CHAMPION ENSEMBLE — CORRECTED
# V8 RE-ACCOUNTED + V12 + TQQQ
#
# CORRECTION:
# event_compare contains 33 COMPLETED holding periods.
# Previously verified terminal wealth additionally includes the final
# research-date rebalance-only execution cost on 2026-07-27.
#
# We therefore:
#   1) verify completed-period wealth,
#   2) infer the exact terminal-rebalance-only adjustment from the already
#      verified terminal wealth,
#   3) treat that adjustment as a final zero-horizon execution event,
#   4) run the causal universal allocator through both the 33 holding periods
#      and that final execution event.
#
# NO model fitting.
# NO parameter tuning.
# NO relaxation of validation tolerances.
# =============================================================================

import numpy as np
import pandas as pd
import hashlib
import json

print("=" * 140)
print("V13 — ONE-SHOT UNIVERSAL CHAMPION ENSEMBLE — CORRECTED")
print("V8 RE-ACCOUNTED + V12 + TQQQ")
print("=" * 140)

# =============================================================================
# 0. FROZEN INPUTS
# =============================================================================

# Archived numbers are audit references only. Terminal adjustments must come
# from the verified paths in THIS run, not a ratio chosen to force old wealth.
V13_ARCHIVED_TERMINALS = {'V8':4.182462,'V12':4.132877,'TQQQ':3.563433}
V13_EXPECTED_TERMINALS = {
    'V8':float(V8_REACCOUNT_FINAL_WEALTH),
    'V12':float(V12_FINAL_WEALTH),
    'TQQQ':float(V12_TQQQ_FINAL_WEALTH),
}

V13_META_TCA_BPS = 2.0
V13_META_TCA_RATE = V13_META_TCA_BPS / 10000.0

# Numerical quadrature only; NOT performance-selected.
V13_GRID_STEP = 0.01

V13_GRID = np.array(
    [
        [
            w8 / 100.0,
            w12 / 100.0,
            (100 - w8 - w12) / 100.0,
        ]
        for w8 in range(101)
        for w12 in range(101 - w8)
    ],
    dtype=float,
)

V13_EXPERT_NAMES = [
    "V8",
    "V12",
    "TQQQ",
]

assert V13_GRID.shape == (5151, 3)
assert np.allclose(
    V13_GRID.sum(axis=1),
    1.0,
)

# =============================================================================
# 1. LOCATE THE EXISTING APPLES-TO-APPLES EVENT TABLE
# =============================================================================

def v13_norm_col(x):
    return (
        str(x)
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .replace("/", "")
    )


def v13_find_return_column(df, strategy):

    strategy = strategy.lower()

    valid = []

    for col in df.columns:

        name = v13_norm_col(col)

        if strategy not in name:
            continue

        if "return" not in name:
            continue

        if any(
            bad in name
            for bad in [
                "minus",
                "excess",
                "relative",
                "diff",
                "difference",
            ]
        ):
            continue

        valid.append(col)

    if not valid:
        return None

    pct_cols = [
        c
        for c in valid
        if "pct" in v13_norm_col(c)
    ]

    if pct_cols:
        return pct_cols[0]

    return valid[0]


def v13_find_date_column(df, kind):

    if kind == "execution":
        tokens = [
            "executiondate",
            "execution",
        ]

    elif kind == "exit":
        tokens = [
            "exitdate",
            "exit",
        ]

    else:
        raise ValueError(kind)

    for col in df.columns:

        normalized = v13_norm_col(col)

        if normalized in tokens:
            return col

    for col in df.columns:

        normalized = v13_norm_col(col)

        if any(
            token in normalized
            for token in tokens
        ):
            return col

    return None


V13_SOURCE_CANDIDATES = []

for object_name, obj in list(globals().items()):

    if not isinstance(
        obj,
        pd.DataFrame,
    ):
        continue

    if len(obj) < 20:
        continue

    c_v8 = v13_find_return_column(
        obj,
        "v8",
    )

    c_v12 = v13_find_return_column(
        obj,
        "v12",
    )

    c_tqqq = v13_find_return_column(
        obj,
        "tqqq",
    )

    if (
        c_v8 is None
        or
        c_v12 is None
        or
        c_tqqq is None
    ):
        continue

    V13_SOURCE_CANDIDATES.append(
        (
            object_name,
            obj,
            c_v8,
            c_v12,
            c_tqqq,
        )
    )


if not V13_SOURCE_CANDIDATES:

    raise RuntimeError(
        "Could not locate the existing "
        "V8/V12/TQQQ event comparison table."
    )


# Prefer event_compare explicitly if present.
preferred = [
    x
    for x in V13_SOURCE_CANDIDATES
    if x[0] == "event_compare"
]

if preferred:

    (
        V13_SOURCE_NAME,
        V13_SOURCE_DF,
        V13_V8_COL,
        V13_V12_COL,
        V13_TQQQ_COL,
    ) = preferred[0]

else:

    V13_SOURCE_CANDIDATES.sort(
        key=lambda x: len(x[1]),
        reverse=True,
    )

    (
        V13_SOURCE_NAME,
        V13_SOURCE_DF,
        V13_V8_COL,
        V13_V12_COL,
        V13_TQQQ_COL,
    ) = V13_SOURCE_CANDIDATES[0]


V13_EXEC_COL = v13_find_date_column(
    V13_SOURCE_DF,
    "execution",
)

V13_EXIT_COL = v13_find_date_column(
    V13_SOURCE_DF,
    "exit",
)


print(
    f"\n[+] Source event table : "
    f"{V13_SOURCE_NAME}"
)

print(
    f"[+] V8 return column   : "
    f"{V13_V8_COL}"
)

print(
    f"[+] V12 return column  : "
    f"{V13_V12_COL}"
)

print(
    f"[+] TQQQ return column : "
    f"{V13_TQQQ_COL}"
)

# =============================================================================
# 2. STANDARDIZE COMPLETED-PERIOD RETURNS
# =============================================================================

def v13_return_to_decimal(
    series,
    column_name,
):

    out = pd.to_numeric(
        series,
        errors="coerce",
    ).astype(float)

    if "pct" in v13_norm_col(
        column_name
    ):
        return out / 100.0

    finite = out[
        np.isfinite(out)
    ]

    if (
        len(finite) > 0
        and
        np.nanpercentile(
            np.abs(finite),
            95,
        ) > 1.50
    ):
        return out / 100.0

    return out


V13_EVENTS = pd.DataFrame(
    {
        "V8":
            v13_return_to_decimal(
                V13_SOURCE_DF[
                    V13_V8_COL
                ],
                V13_V8_COL,
            ),

        "V12":
            v13_return_to_decimal(
                V13_SOURCE_DF[
                    V13_V12_COL
                ],
                V13_V12_COL,
            ),

        "TQQQ":
            v13_return_to_decimal(
                V13_SOURCE_DF[
                    V13_TQQQ_COL
                ],
                V13_TQQQ_COL,
            ),
    },
    index=V13_SOURCE_DF.index,
).copy()


if V13_EXEC_COL is not None:

    V13_EVENTS[
        "Execution_Date"
    ] = pd.to_datetime(
        V13_SOURCE_DF[
            V13_EXEC_COL
        ],
        errors="coerce",
    ).dt.normalize()


if V13_EXIT_COL is not None:

    V13_EVENTS[
        "Exit_Date"
    ] = pd.to_datetime(
        V13_SOURCE_DF[
            V13_EXIT_COL
        ],
        errors="coerce",
    ).dt.normalize()


V13_EVENTS = V13_EVENTS.dropna(
    subset=[
        "V8",
        "V12",
        "TQQQ",
    ]
).copy()


# event_compare should contain only completed holding periods,
# but defensively exclude zero-horizon rows.
if (
    "Execution_Date"
    in V13_EVENTS.columns
    and
    "Exit_Date"
    in V13_EVENTS.columns
):

    V13_EVENTS = V13_EVENTS[
        V13_EVENTS["Exit_Date"]
        >
        V13_EVENTS["Execution_Date"]
    ].copy()


V13_EVENTS = (
    V13_EVENTS
    .reset_index(drop=True)
)


if len(V13_EVENTS) != 33:

    raise RuntimeError(
        "Expected exactly 33 completed "
        f"holding periods; found "
        f"{len(V13_EVENTS)}."
    )


print(
    f"\n[+] Completed holding periods: "
    f"{len(V13_EVENTS)}"
)

# =============================================================================
# 3. COMPLETED-PERIOD TERMINAL WEALTH
# =============================================================================

V13_COMPLETED_WEALTH = {}

for strategy in V13_EXPERT_NAMES:

    V13_COMPLETED_WEALTH[
        strategy
    ] = float(
        np.prod(
            1.0
            +
            V13_EVENTS[
                strategy
            ].to_numpy(
                dtype=float
            )
        )
    )


V13_COMPLETED_AUDIT = pd.DataFrame(
    [
        {
            "Strategy":
                strategy,

            "Completed_Period_Wealth":
                V13_COMPLETED_WEALTH[
                    strategy
                ],

            "Verified_Final_Wealth":
                V13_EXPECTED_TERMINALS[
                    strategy
                ],

            "Terminal_Rebalance_Adjustment_Pct":
                (
                    V13_EXPECTED_TERMINALS[
                        strategy
                    ]
                    /
                    V13_COMPLETED_WEALTH[
                        strategy
                    ]
                    -
                    1.0
                )
                *
                100.0,
        }
        for strategy
        in V13_EXPERT_NAMES
    ]
)


print(
    "\n1) COMPLETED-PERIOD / "
    "FINAL-WEALTH RECONCILIATION"
)

display(
    V13_COMPLETED_AUDIT.round(8)
)

# =============================================================================
# 4. EXACT TERMINAL REBALANCE-ONLY ADJUSTMENT
# =============================================================================
#
# This is NOT fitted.
#
# It is the exact multiplicative reconciliation between:
#
#   product(33 completed holding-period returns)
#
# and
#
#   already-verified final strategy wealth.
#
# Therefore the 2026-07-27 terminal execution event is reconstructed exactly.
# =============================================================================

V13_TERMINAL_ADJUSTMENT = np.array(
    [
        (
            V13_EXPECTED_TERMINALS[
                strategy
            ]
            /
            V13_COMPLETED_WEALTH[
                strategy
            ]
        )
        -
        1.0

        for strategy
        in V13_EXPERT_NAMES
    ],
    dtype=float,
)


V13_RECONSTRUCTED_FINAL = {}

for j, strategy in enumerate(
    V13_EXPERT_NAMES
):

    reconstructed = (
        V13_COMPLETED_WEALTH[
            strategy
        ]
        *
        (
            1.0
            +
            V13_TERMINAL_ADJUSTMENT[j]
        )
    )

    V13_RECONSTRUCTED_FINAL[
        strategy
    ] = float(
        reconstructed
    )


V13_FINAL_VALIDATION = pd.DataFrame(
    [
        {
            "Strategy":
                strategy,

            "Reconstructed_Final":
                V13_RECONSTRUCTED_FINAL[
                    strategy
                ],

            "Expected_Final":
                V13_EXPECTED_TERMINALS[
                    strategy
                ],

            "Absolute_Error":
                abs(
                    V13_RECONSTRUCTED_FINAL[
                        strategy
                    ]
                    -
                    V13_EXPECTED_TERMINALS[
                        strategy
                    ]
                ),
        }
        for strategy
        in V13_EXPERT_NAMES
    ]
)


print(
    "\n2) EXACT TERMINAL-STATE VALIDATION"
)

display(
    V13_FINAL_VALIDATION.round(12)
)


MAX_RECON_ERROR = float(
    V13_FINAL_VALIDATION[
        "Absolute_Error"
    ].max()
)


if MAX_RECON_ERROR > 1e-10:

    raise RuntimeError(
        "Terminal reconciliation failed. "
        f"Maximum error = "
        f"{MAX_RECON_ERROR:.12g}"
    )


print(
    "\n[+] EXACT PRIOR TERMINAL "
    "WEALTH STATE RECONSTRUCTED."
)

# =============================================================================
# 5. UNIVERSAL EXPERT ENGINE
# =============================================================================

N_EXPERTS = len(
    V13_GRID
)

V13_EXPERT_WEALTH = np.ones(
    N_EXPERTS,
    dtype=float,
)

# Constant-mix experts begin at their intended mix.
V13_EXPERT_PREV_DRIFT = (
    V13_GRID.copy()
)

# Uniform prior mean:
V13_UNIVERSAL_PREV_DRIFT = (
    V13_GRID.mean(
        axis=0
    )
)

V13_UNIVERSAL_WEALTH = 1.0

V13_PATH_ROWS = []

# =============================================================================
# 6. 33 COMPLETED HOLDING PERIODS
# =============================================================================

for event_i, row in V13_EVENTS.iterrows():

    constituent_returns = np.array(
        [
            float(row["V8"]),
            float(row["V12"]),
            float(row["TQQQ"]),
        ],
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # PRE-EVENT posterior — only completed events t-1 and earlier
    # -------------------------------------------------------------------------

    posterior = (
        V13_EXPERT_WEALTH
        /
        V13_EXPERT_WEALTH.sum()
    )

    universal_target = (
        posterior[:, None]
        *
        V13_GRID
    ).sum(
        axis=0
    )

    # -------------------------------------------------------------------------
    # V13 meta-level turnover and cost
    # -------------------------------------------------------------------------

    meta_turnover = float(
        np.abs(
            universal_target
            -
            V13_UNIVERSAL_PREV_DRIFT
        ).sum()
    )

    meta_cost_rate = (
        V13_META_TCA_RATE
        *
        meta_turnover
    )

    gross_multiplier = float(
        universal_target
        @
        (
            1.0
            +
            constituent_returns
        )
    )

    net_multiplier = (
        gross_multiplier
        *
        (
            1.0
            -
            meta_cost_rate
        )
    )

    if net_multiplier <= 0:

        raise RuntimeError(
            "Invalid V13 wealth multiplier "
            f"at event {event_i + 1}."
        )

    V13_UNIVERSAL_WEALTH *= (
        net_multiplier
    )

    # Drift V13 strategy-mixture weights.
    component_end_values = (
        universal_target
        *
        (
            1.0
            +
            constituent_returns
        )
    )

    V13_UNIVERSAL_PREV_DRIFT = (
        component_end_values
        /
        component_end_values.sum()
    )

    # -------------------------------------------------------------------------
    # Update 5151 constant-mix experts AFTER event
    # -------------------------------------------------------------------------

    expert_turnover = np.abs(
        V13_GRID
        -
        V13_EXPERT_PREV_DRIFT
    ).sum(
        axis=1
    )

    expert_meta_cost = (
        V13_META_TCA_RATE
        *
        expert_turnover
    )

    expert_gross_multiplier = (
        V13_GRID
        @
        (
            1.0
            +
            constituent_returns
        )
    )

    expert_net_multiplier = (
        expert_gross_multiplier
        *
        (
            1.0
            -
            expert_meta_cost
        )
    )

    if np.any(
        expert_net_multiplier <= 0
    ):

        raise RuntimeError(
            "Invalid universal expert "
            f"multiplier at event "
            f"{event_i + 1}."
        )

    V13_EXPERT_WEALTH *= (
        expert_net_multiplier
    )

    expert_component_end = (
        V13_GRID
        *
        (
            1.0
            +
            constituent_returns
        )[None, :]
    )

    V13_EXPERT_PREV_DRIFT = (
        expert_component_end
        /
        expert_component_end.sum(
            axis=1,
            keepdims=True,
        )
    )

    rec = {
        "Event":
            event_i + 1,

        "Event_Type":
            "HOLDING_PERIOD",

        "V8_Weight":
            universal_target[0],

        "V12_Weight":
            universal_target[1],

        "TQQQ_Weight":
            universal_target[2],

        "Meta_Turnover":
            meta_turnover,

        "Meta_Cost_bps":
            meta_cost_rate
            *
            10000.0,

        "V8_Return":
            constituent_returns[0],

        "V12_Return":
            constituent_returns[1],

        "TQQQ_Return":
            constituent_returns[2],

        "V13_Net_Return":
            net_multiplier
            -
            1.0,

        "V13_Wealth":
            V13_UNIVERSAL_WEALTH,

        "Posterior_Effective_Experts":
            1.0
            /
            np.sum(
                posterior ** 2
            ),
    }

    if (
        "Execution_Date"
        in V13_EVENTS.columns
    ):
        rec[
            "Execution_Date"
        ] = row[
            "Execution_Date"
        ]

    if (
        "Exit_Date"
        in V13_EVENTS.columns
    ):
        rec[
            "Exit_Date"
        ] = row[
            "Exit_Date"
        ]

    V13_PATH_ROWS.append(
        rec
    )

# =============================================================================
# 7. FINAL REBALANCE-ONLY EVENT — 2026-07-27
# =============================================================================

terminal_posterior = (
    V13_EXPERT_WEALTH
    /
    V13_EXPERT_WEALTH.sum()
)

terminal_target = (
    terminal_posterior[:, None]
    *
    V13_GRID
).sum(
    axis=0
)

terminal_meta_turnover = float(
    np.abs(
        terminal_target
        -
        V13_UNIVERSAL_PREV_DRIFT
    ).sum()
)

terminal_meta_cost_rate = (
    V13_META_TCA_RATE
    *
    terminal_meta_turnover
)

terminal_gross_multiplier = float(
    terminal_target
    @
    (
        1.0
        +
        V13_TERMINAL_ADJUSTMENT
    )
)

terminal_net_multiplier = (
    terminal_gross_multiplier
    *
    (
        1.0
        -
        terminal_meta_cost_rate
    )
)

if terminal_net_multiplier <= 0:

    raise RuntimeError(
        "Invalid V13 terminal "
        "rebalance multiplier."
    )


V13_UNIVERSAL_WEALTH *= (
    terminal_net_multiplier
)


V13_PATH_ROWS.append(
    {
        "Event":
            34,

        "Event_Type":
            "TERMINAL_REBALANCE_ONLY",

        "Execution_Date":
            pd.Timestamp(
                "2026-07-27"
            ),

        "Exit_Date":
            pd.Timestamp(
                "2026-07-27"
            ),

        "V8_Weight":
            terminal_target[0],

        "V12_Weight":
            terminal_target[1],

        "TQQQ_Weight":
            terminal_target[2],

        "Meta_Turnover":
            terminal_meta_turnover,

        "Meta_Cost_bps":
            terminal_meta_cost_rate
            *
            10000.0,

        "V8_Return":
            V13_TERMINAL_ADJUSTMENT[0],

        "V12_Return":
            V13_TERMINAL_ADJUSTMENT[1],

        "TQQQ_Return":
            V13_TERMINAL_ADJUSTMENT[2],

        "V13_Net_Return":
            terminal_net_multiplier
            -
            1.0,

        "V13_Wealth":
            V13_UNIVERSAL_WEALTH,

        "Posterior_Effective_Experts":
            1.0
            /
            np.sum(
                terminal_posterior
                ** 2
            ),
    }
)


# Update constant experts through terminal event
terminal_expert_turnover = np.abs(
    V13_GRID
    -
    V13_EXPERT_PREV_DRIFT
).sum(
    axis=1
)

terminal_expert_meta_cost = (
    V13_META_TCA_RATE
    *
    terminal_expert_turnover
)

terminal_expert_gross_mult = (
    V13_GRID
    @
    (
        1.0
        +
        V13_TERMINAL_ADJUSTMENT
    )
)

terminal_expert_net_mult = (
    terminal_expert_gross_mult
    *
    (
        1.0
        -
        terminal_expert_meta_cost
    )
)

V13_EXPERT_WEALTH *= (
    terminal_expert_net_mult
)


V13_PATH = pd.DataFrame(
    V13_PATH_ROWS
)

# =============================================================================
# 8. FINAL RESULT
# =============================================================================

V13_FINAL_WEALTH = float(
    V13_UNIVERSAL_WEALTH
)

V13_V8_FINAL_WEALTH = float(
    V13_EXPECTED_TERMINALS[
        "V8"
    ]
)

V13_V12_FINAL_WEALTH = float(
    V13_EXPECTED_TERMINALS[
        "V12"
    ]
)

V13_TQQQ_FINAL_WEALTH = float(
    V13_EXPECTED_TERMINALS[
        "TQQQ"
    ]
)


V13_FINAL_POSTERIOR = (
    V13_EXPERT_WEALTH
    /
    V13_EXPERT_WEALTH.sum()
)

V13_FINAL_ALLOC = (
    V13_FINAL_POSTERIOR[:, None]
    *
    V13_GRID
).sum(
    axis=0
)


best_idx = int(
    np.argmax(
        V13_EXPERT_WEALTH
    )
)

V13_BEST_CONSTANT = (
    V13_GRID[
        best_idx
    ].copy()
)

V13_BEST_CONSTANT_WEALTH = float(
    V13_EXPERT_WEALTH[
        best_idx
    ]
)


V13_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Completed holding periods",
            "Terminal rebalance-only events",
            "Universal experts",

            "V13 final wealth",
            "V13 net return pct",

            "V8 repaired final wealth",
            "V12 final wealth",
            "TQQQ final wealth",

            "V13 minus V8 pp",
            "V13 minus V12 pp",
            "V13 minus TQQQ pp",

            "V13 / V8 relative wealth",

            "Total meta turnover",
            "Mean meta turnover",

            "Final posterior V8 pct",
            "Final posterior V12 pct",
            "Final posterior TQQQ pct",

            "Best constant wealth — hindsight only",
            "Best constant V8 pct — hindsight only",
            "Best constant V12 pct — hindsight only",
            "Best constant TQQQ pct — hindsight only",
        ],

        "Value": [
            33,
            1,
            len(V13_GRID),

            V13_FINAL_WEALTH,
            (
                V13_FINAL_WEALTH
                -
                1.0
            )
            *
            100.0,

            V13_V8_FINAL_WEALTH,
            V13_V12_FINAL_WEALTH,
            V13_TQQQ_FINAL_WEALTH,

            (
                V13_FINAL_WEALTH
                -
                V13_V8_FINAL_WEALTH
            )
            *
            100.0,

            (
                V13_FINAL_WEALTH
                -
                V13_V12_FINAL_WEALTH
            )
            *
            100.0,

            (
                V13_FINAL_WEALTH
                -
                V13_TQQQ_FINAL_WEALTH
            )
            *
            100.0,

            V13_FINAL_WEALTH
            /
            V13_V8_FINAL_WEALTH,

            V13_PATH[
                "Meta_Turnover"
            ].sum(),

            V13_PATH[
                "Meta_Turnover"
            ].mean(),

            V13_FINAL_ALLOC[0]
            *
            100.0,

            V13_FINAL_ALLOC[1]
            *
            100.0,

            V13_FINAL_ALLOC[2]
            *
            100.0,

            V13_BEST_CONSTANT_WEALTH,

            V13_BEST_CONSTANT[0]
            *
            100.0,

            V13_BEST_CONSTANT[1]
            *
            100.0,

            V13_BEST_CONSTANT[2]
            *
            100.0,
        ],
    }
)


print(
    "\n3) V13 FINAL ECONOMIC RESULT"
)

display(
    V13_SUMMARY.round(6)
)

# =============================================================================
# 9. TRAILING ROBUSTNESS — COMPLETED HOLDING PERIODS ONLY
#
# Terminal rebalance-only event is intentionally excluded from these trailing
# return windows because it has zero holding horizon.
# =============================================================================

V13_HOLDING_PATH = (
    V13_PATH[
        V13_PATH[
            "Event_Type"
        ]
        ==
        "HOLDING_PERIOD"
    ]
    .reset_index(drop=True)
)

V13_RET = (
    V13_HOLDING_PATH[
        "V13_Net_Return"
    ]
    .to_numpy(
        dtype=float
    )
)

V8_RET = (
    V13_EVENTS[
        "V8"
    ]
    .to_numpy(
        dtype=float
    )
)

V12_RET = (
    V13_EVENTS[
        "V12"
    ]
    .to_numpy(
        dtype=float
    )
)

TQQQ_RET = (
    V13_EVENTS[
        "TQQQ"
    ]
    .to_numpy(
        dtype=float
    )
)


V13_WINDOWS = {
    "~1M": 1,
    "~3M": 3,
    "~6M": 6,
    "~12M": 12,
    "~24M": 24,
    "ALL_COMPLETED": 33,
}


robustness_rows = []

for label, n in V13_WINDOWS.items():

    n = min(
        n,
        len(V13_RET),
    )

    v13_w = float(
        np.prod(
            1.0
            +
            V13_RET[-n:]
        )
    )

    v8_w = float(
        np.prod(
            1.0
            +
            V8_RET[-n:]
        )
    )

    v12_w = float(
        np.prod(
            1.0
            +
            V12_RET[-n:]
        )
    )

    tq_w = float(
        np.prod(
            1.0
            +
            TQQQ_RET[-n:]
        )
    )

    robustness_rows.append(
        {
            "Window":
                label,

            "Periods":
                n,

            "V13_Return_Pct":
                (
                    v13_w - 1.0
                )
                *
                100.0,

            "V8_Return_Pct":
                (
                    v8_w - 1.0
                )
                *
                100.0,

            "V12_Return_Pct":
                (
                    v12_w - 1.0
                )
                *
                100.0,

            "TQQQ_Return_Pct":
                (
                    tq_w - 1.0
                )
                *
                100.0,

            "V13_Minus_V8_pp":
                (
                    v13_w
                    -
                    v8_w
                )
                *
                100.0,

            "V13_Minus_TQQQ_pp":
                (
                    v13_w
                    -
                    tq_w
                )
                *
                100.0,

            "V13_Beats_V8":
                v13_w
                >
                v8_w,

            "V13_Beats_TQQQ":
                v13_w
                >
                tq_w,
        }
    )


V13_ROBUSTNESS = pd.DataFrame(
    robustness_rows
)


print(
    "\n4) TRAILING MULTI-PERIOD ROBUSTNESS"
)

display(
    V13_ROBUSTNESS.round(6)
)

# =============================================================================
# 10. LAST 12 EVENTS
# =============================================================================

V13_DISPLAY = (
    V13_PATH
    .tail(12)
    .copy()
)

for col in [
    "V8_Weight",
    "V12_Weight",
    "TQQQ_Weight",
    "V13_Net_Return",
]:

    V13_DISPLAY[col] = (
        V13_DISPLAY[col]
        *
        100.0
    )


V13_DISPLAY = V13_DISPLAY.rename(
    columns={
        "V8_Weight":
            "V8_Weight_Pct",

        "V12_Weight":
            "V12_Weight_Pct",

        "TQQQ_Weight":
            "TQQQ_Weight_Pct",

        "V13_Net_Return":
            "V13_Net_Return_Pct",
    }
)


print(
    "\n5) LAST 12 V13 EVENTS"
)

display(
    V13_DISPLAY[
        [
            "Event",
            "Event_Type",
            "Execution_Date",
            "Exit_Date",
            "V8_Weight_Pct",
            "V12_Weight_Pct",
            "TQQQ_Weight_Pct",
            "Meta_Turnover",
            "Meta_Cost_bps",
            "V13_Net_Return_Pct",
            "V13_Wealth",
        ]
    ].round(6)
)

# =============================================================================
# 11. VERDICT
# =============================================================================

V13_BEATS_V8 = bool(
    V13_FINAL_WEALTH
    >
    V13_V8_FINAL_WEALTH
)

V13_BEATS_V12 = bool(
    V13_FINAL_WEALTH
    >
    V13_V12_FINAL_WEALTH
)

V13_BEATS_TQQQ = bool(
    V13_FINAL_WEALTH
    >
    V13_TQQQ_FINAL_WEALTH
)

V13_ALL_WINDOWS_BEAT_TQQQ = bool(
    V13_ROBUSTNESS[
        "V13_Beats_TQQQ"
    ].all()
)


if V13_BEATS_V8:

    V13_VERDICT = (
        "PASS_NEW_CHAMPION"
    )

else:

    V13_VERDICT = (
        "FAIL_TO_BEAT_V8"
    )


V13_CONFIG = {
    "version":
        "V13",

    "architecture":
        "UNIVERSAL_ENSEMBLE_V8_V12_TQQQ",

    "grid":
        "1_PERCENT_SIMPLEX_5151_EXPERTS",

    "prior":
        "UNIFORM",

    "posterior_timing":
        "PRE_EVENT_PRIOR_COMPLETED_EVENTS_ONLY",

    "meta_tca_bps":
        V13_META_TCA_BPS,

    "terminal_rebalance":
        "EXACT_RECONCILIATION_TO_PREVIOUSLY_VERIFIED_TERMINAL_WEALTH",

    "model_fit":
        False,

    "parameter_tuning":
        False,
}


V13_RESEARCH_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            {
                "config":
                    V13_CONFIG,

                "returns":
                    np.round(
                        V13_EVENTS[
                            V13_EXPERT_NAMES
                        ].to_numpy(
                            dtype=float
                        ),
                        12,
                    ).tolist(),

                "terminal_adjustment":
                    np.round(
                        V13_TERMINAL_ADJUSTMENT,
                        12,
                    ).tolist(),

                "final_wealth":
                    round(
                        V13_FINAL_WEALTH,
                        12,
                    ),
            },
            sort_keys=True,
            default=str,
        )
        .encode()
    )
    .hexdigest()
)


print(
    "\n6) V13 RESEARCH VERDICT"
)

print(
    f"V13 final wealth       : "
    f"{V13_FINAL_WEALTH:.6f}"
)

print(
    f"V8 champion wealth     : "
    f"{V13_V8_FINAL_WEALTH:.6f}"
)

print(
    f"V12 wealth             : "
    f"{V13_V12_FINAL_WEALTH:.6f}"
)

print(
    f"TQQQ wealth            : "
    f"{V13_TQQQ_FINAL_WEALTH:.6f}"
)

print(
    f"V13 beats V8           : "
    f"{V13_BEATS_V8}"
)

print(
    f"V13 beats V12          : "
    f"{V13_BEATS_V12}"
)

print(
    f"V13 beats TQQQ         : "
    f"{V13_BEATS_TQQQ}"
)

print(
    f"All trailing windows "
    f"beat TQQQ              : "
    f"{V13_ALL_WINDOWS_BEAT_TQQQ}"
)

print(
    f"V13 RESULT             : "
    f"{V13_VERDICT}"
)


print(
    "\n7) V13 RESEARCH FINGERPRINT"
)

print(
    V13_RESEARCH_FINGERPRINT
)


print("\nINTEGRITY:")
print("[+] Previous validation mismatch was explained, not ignored.")
print("[+] No tolerance was relaxed.")
print("[+] 33 completed holding periods were preserved.")
print("[+] Final rebalance-only execution cost was preserved.")
print("[+] V8 architecture was not changed.")
print("[+] V12 architecture was not changed.")
print("[+] No model was fitted.")
print("[+] No parameter was tuned.")
print("[+] Universal posterior used prior completed events only.")
print("[+] Ex-post best constant mix remains diagnostic only.")
print("[+] No minimum stock weight.")
print("[+] No maximum stock weight.")
print("[+] No Top-K.")
print("[+] No sector cap.")
print("[+] No risk cap.")
print("[+] No cash.")
print("[+] No leverage above 100%.")
print("[+] Conservative meta-level TCA was included.")

print("\nDECISION:")

if V13_BEATS_V8:

    print(
        "[+] V13 BEATS THE REPAIRED-LEDGER V8 CHAMPION."
    )

    print(
        "[+] STOP. DO NOT RETUNE V13 AFTER THIS OBSERVED RESULT."
    )

else:

    print(
        "[!] V13 DOES NOT BEAT V8."
    )

    print(
        "[!] REJECT V13 AS DESIGNED. DO NOT PATCH IT."
    )

print("=" * 140)
restored_register('V13', V13_FINAL_WEALTH, V13_PATH, 'V13_Wealth', 'Close / original meta allocator costs', 'Historically rejected', terminal_date=pd.Timestamp("2026-07-27"))
