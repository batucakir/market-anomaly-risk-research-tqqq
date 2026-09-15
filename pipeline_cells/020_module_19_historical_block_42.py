# ==============================================================================
# MODULE 19 / HISTORICAL BLOCK 42
# FINAL GO / NO-GO + V4 RESEARCH FREEZE
# ==============================================================================

# ==============================================================================
# BLOCK 42 — FINAL GO / NO-GO + V4 RESEARCH FREEZE
# ==============================================================================
#
# PURPOSE
# -------
# Close the V4 research generation WITHOUT post-hoc tuning.
#
# This block:
#
#   - records the final economic verdict,
#   - freezes accepted infrastructure,
#   - rejects failed alpha / portfolio challengers,
#   - preserves research lineage,
#   - prevents accidental promotion of V4,
#   - states what must happen before a future V5 can be tested.
#
#
# NO:
#
#   model refit
#   parameter optimization
#   portfolio rerun
#   alpha change
#   benchmark change
#
# ==============================================================================


import json
import hashlib
from datetime import datetime

import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

B42_REQUIRED = [

    "BLOCK41_SUMMARY",
    "BLOCK41_PAIRWISE",

    "B41_V4_LEADER",
    "B41_V4_LEADER_WEALTH",

    "B41_STRONGEST_BENCHMARK",
    "B41_STRONGEST_BENCHMARK_WEALTH",

    "B41_BEATS_STRONGEST_BENCHMARK",

    "BLOCK40_FINGERPRINT",
    "BLOCK39_FINGERPRINT",

    "V4_MASTER_FINGERPRINT",
]


B42_MISSING = [

    x

    for x in B42_REQUIRED

    if x not in globals()
]


if B42_MISSING:

    raise RuntimeError(

        "BLOCK 42 missing required objects: "

        f"{B42_MISSING}"
    )


print("=" * 120)

print(
    "BLOCK 42 — FINAL GO / NO-GO + V4 RESEARCH FREEZE"
)

print("=" * 120)


# ==============================================================================
# 1. FINAL PERFORMANCE EXTRACTION
# ==============================================================================

def b42_get_wealth(
    strategy,
):

    row = (

        BLOCK41_SUMMARY[

            BLOCK41_SUMMARY[
                "Strategy"
            ]
            ==
            strategy
        ]
    )


    if row.empty:

        return np.nan


    return float(

        row[
            "Final_Wealth"
        ]
        .iloc[
            0
        ]
    )


B42_RIDGE_WEALTH = (

    b42_get_wealth(
        "V4_RIDGE"
    )
)


B42_HGB_WEALTH = (

    b42_get_wealth(
        "V4_HGB"
    )
)


B42_QQQ_WEALTH = (

    b42_get_wealth(
        "QQQ_BH_NET_2BPS"
    )
)


B42_TQQQ_WEALTH = (

    b42_get_wealth(
        "TQQQ_BH_NET_2BPS"
    )
)


B42_PIT_EW_WEALTH = (

    b42_get_wealth(
        "PIT_EW_NET_2BPS"
    )
)


B42_CASH_WEALTH = (

    b42_get_wealth(
        "CASH"
    )
)


# ==============================================================================
# 2. OBJECTIVE TESTS
# ==============================================================================

B42_TESTS = {

    "V4_positive_absolute_return":

        (
            B41_V4_LEADER_WEALTH
            >
            1.0
        ),


    "V4_beats_cash":

        (
            B41_V4_LEADER_WEALTH
            >
            B42_CASH_WEALTH
        ),


    "V4_beats_QQQ":

        (
            B41_V4_LEADER_WEALTH
            >
            B42_QQQ_WEALTH
        ),


    "V4_beats_TQQQ":

        (
            B41_V4_LEADER_WEALTH
            >
            B42_TQQQ_WEALTH
        ),


    "V4_beats_broad_PIT_EW":

        (
            B41_V4_LEADER_WEALTH
            >
            B42_PIT_EW_WEALTH
        ),


    "V4_beats_strongest_benchmark":

        bool(
            B41_BEATS_STRONGEST_BENCHMARK
        ),
}


# ==============================================================================
# 3. PRIMARY GO / NO-GO
# ==============================================================================

# Ultimate project objective:
#
#       maximize OOS NET portfolio wealth
#
# A V4 research generation cannot be promoted when it loses to the
# strongest ex-ante benchmark.
#
# In this run it also loses to QQQ and broad PIT-EW, removing ambiguity.

B42_GO = bool(

    B42_TESTS[
        "V4_beats_strongest_benchmark"
    ]
)


B42_DECISION = (

    "GO"

    if B42_GO

    else

    "NO-GO"
)


B42_PROMOTION_STATUS = (

    "PROMOTED_TO_RESEARCH_CHAMPION"

    if B42_GO

    else

    "REJECTED_NOT_FOR_PRODUCTION"
)


# ==============================================================================
# 4. ACCEPTED INFRASTRUCTURE
# ==============================================================================

# These components worked as research infrastructure and do NOT depend
# on V4's alpha winning economically.

B42_ACCEPTED_COMPONENTS = [

    "Strict causal / walk-forward research discipline.",

    "Point-in-time S&P Composite 1500 universe infrastructure.",

    "Broad dynamic investable universe instead of fixed 38 assets.",

    "Causal trailing liquidity and data-quality eligibility.",

    "TQQQ treated as a normal investable candidate.",

    "No arbitrary single-name cap.",

    "No arbitrary sector cap.",

    "Cash as a valid portfolio allocation.",

    "Explicit transaction-cost accounting.",

    "Causal covariance / portfolio-risk estimation.",

    "Same-calendar benchmark framework.",

    "Benchmark comparison using net wealth as the primary objective.",
]


# ==============================================================================
# 5. REJECTED V4 COMPONENTS
# ==============================================================================

B42_REJECTED_COMPONENTS = [

    "V4 Ridge multi-horizon absolute-return alpha as production alpha.",

    "V4 HistGradientBoosting multi-horizon alpha.",

    "Current 1D / 5D / 20D feature-to-return specification as sufficient alpha.",

    "Current V4 alpha + optimizer combination.",

    "Promotion based only on positive IC.",

    "Promotion based only on positive absolute strategy return.",

    "Any post-hoc tuning of V4 using the already-observed Block-41 sample.",
]


# ==============================================================================
# 6. FINAL ECONOMIC DIAGNOSIS
# ==============================================================================

B42_DIAGNOSIS = {

    "V4_leader":
        B41_V4_LEADER,

    "V4_leader_final_wealth":
        B41_V4_LEADER_WEALTH,

    "Strongest_benchmark":
        B41_STRONGEST_BENCHMARK,

    "Strongest_benchmark_final_wealth":
        B41_STRONGEST_BENCHMARK_WEALTH,

    "QQQ_final_wealth":
        B42_QQQ_WEALTH,

    "TQQQ_final_wealth":
        B42_TQQQ_WEALTH,

    "Broad_PIT_EW_final_wealth":
        B42_PIT_EW_WEALTH,

    "Cash_final_wealth":
        B42_CASH_WEALTH,

    "V4_minus_QQQ_pp":

        100.0
        *
        (
            B41_V4_LEADER_WEALTH
            -
            B42_QQQ_WEALTH
        ),

    "V4_minus_TQQQ_pp":

        100.0
        *
        (
            B41_V4_LEADER_WEALTH
            -
            B42_TQQQ_WEALTH
        ),

    "V4_minus_Broad_PIT_EW_pp":

        100.0
        *
        (
            B41_V4_LEADER_WEALTH
            -
            B42_PIT_EW_WEALTH
        ),
}


# ==============================================================================
# 7. FUTURE-RESEARCH RULE
# ==============================================================================

B42_NEXT_GENERATION_RULES = [

    (
        "Do NOT optimize V4 hyperparameters against the completed "
        "2023-10-18 -> 2026-07-27 benchmark."
    ),

    (
        "Do NOT change the 5-session rebalance interval because Block 41 "
        "revealed weak performance."
    ),

    (
        "Do NOT change the 2x EW risk budget because Block 41 revealed "
        "weak performance."
    ),

    (
        "Do NOT add or remove factors merely because their historical "
        "performance is now known."
    ),

    (
        "The next research generation must be structurally different, "
        "not another patch to Ridge/HGB."
    ),

    (
        "The PIT universe, data-integrity framework, cost model and "
        "same-calendar benchmark framework should be reused."
    ),

    (
        "Any future model promotion must again be determined by "
        "out-of-sample NET portfolio wealth."
    ),
]


# ==============================================================================
# 8. RESEARCH FREEZE RECORD
# ==============================================================================

B42_FREEZE_RECORD = {

    "Project_Objective":

        "MAXIMIZE_OUT_OF_SAMPLE_NET_PORTFOLIO_WEALTH",


    "Decision":

        B42_DECISION,


    "Promotion_Status":

        B42_PROMOTION_STATUS,


    "V4_Leader":

        B41_V4_LEADER,


    "V4_Final_Wealth":

        B41_V4_LEADER_WEALTH,


    "Strongest_Benchmark":

        B41_STRONGEST_BENCHMARK,


    "Strongest_Benchmark_Final_Wealth":

        B41_STRONGEST_BENCHMARK_WEALTH,


    "Tests":

        B42_TESTS,


    "Accepted_Infrastructure":

        B42_ACCEPTED_COMPONENTS,


    "Rejected_V4_Components":

        B42_REJECTED_COMPONENTS,


    "Next_Generation_Rules":

        B42_NEXT_GENERATION_RULES,


    "Parent_Fingerprints": {

        "V4_Master":
            V4_MASTER_FINGERPRINT,

        "Block39_Alpha":
            BLOCK39_FINGERPRINT,

        "Block40_Portfolio":
            BLOCK40_FINGERPRINT,
    },
}


# ==============================================================================
# 9. FINAL RESEARCH FINGERPRINT
# ==============================================================================

BLOCK42_FINGERPRINT = (

    hashlib.sha256(

        json.dumps(

            B42_FREEZE_RECORD,

            sort_keys=True,

            default=str,

        ).encode(
            "utf-8"
        )
    )

    .hexdigest()
)


V4_FINAL_RESEARCH_FINGERPRINT = (
    BLOCK42_FINGERPRINT
)


# ==============================================================================
# 10. HUMAN-READABLE TEST TABLE
# ==============================================================================

BLOCK42_TEST_TABLE = pd.DataFrame(
    {

        "Test": [

            "Positive absolute net return",

            "Beats cash",

            "Beats QQQ",

            "Beats TQQQ",

            "Beats broad PIT equal-weight",

            "Beats strongest benchmark",
        ],


        "Pass": [

            B42_TESTS[
                "V4_positive_absolute_return"
            ],

            B42_TESTS[
                "V4_beats_cash"
            ],

            B42_TESTS[
                "V4_beats_QQQ"
            ],

            B42_TESTS[
                "V4_beats_TQQQ"
            ],

            B42_TESTS[
                "V4_beats_broad_PIT_EW"
            ],

            B42_TESTS[
                "V4_beats_strongest_benchmark"
            ],
        ],
    }
)


# ==============================================================================
# 11. ECONOMIC COMPARISON TABLE
# ==============================================================================

BLOCK42_ECONOMIC_TABLE = pd.DataFrame(
    {

        "Strategy": [

            "TQQQ Buy & Hold",

            "QQQ Buy & Hold",

            "Broad PIT Equal Weight",

            "V4 Ridge",

            "Cash",

            "V4 HGB",
        ],


        "Final_Wealth": [

            B42_TQQQ_WEALTH,

            B42_QQQ_WEALTH,

            B42_PIT_EW_WEALTH,

            B42_RIDGE_WEALTH,

            B42_CASH_WEALTH,

            B42_HGB_WEALTH,
        ],
    }
)


BLOCK42_ECONOMIC_TABLE[
    "Net_Return_Pct"
] = (

    100.0

    *

    (
        BLOCK42_ECONOMIC_TABLE[
            "Final_Wealth"
        ]

        -

        1.0
    )
)


BLOCK42_ECONOMIC_TABLE = (

    BLOCK42_ECONOMIC_TABLE

    .sort_values(
        "Final_Wealth",
        ascending=False,
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 12. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 120
)

print(
    "BLOCK 42 — FINAL ECONOMIC RESULT"
)

print(
    "=" * 120
)


display(

    BLOCK42_ECONOMIC_TABLE
    .round(
        6
    )
)


print(
    "\nOBJECTIVE TESTS"
)


display(
    BLOCK42_TEST_TABLE
)


print(
    "\nFINAL DECISION:"
)


print(
    B42_DECISION
)


print(
    "\nPROMOTION STATUS:"
)


print(
    B42_PROMOTION_STATUS
)


print(
    "\nV4 LEADER:"
)


print(
    f"{B41_V4_LEADER} "
    f"| final wealth = "
    f"{B41_V4_LEADER_WEALTH:.6f}"
)


print(
    "\nSTRONGEST BENCHMARK:"
)


print(
    f"{B41_STRONGEST_BENCHMARK} "
    f"| final wealth = "
    f"{B41_STRONGEST_BENCHMARK_WEALTH:.6f}"
)


print(
    "\nECONOMIC GAPS:"
)


print(

    f"V4 vs QQQ       : "
    f"{B42_DIAGNOSIS['V4_minus_QQQ_pp']:+.3f} pp"
)


print(

    f"V4 vs TQQQ      : "
    f"{B42_DIAGNOSIS['V4_minus_TQQQ_pp']:+.3f} pp"
)


print(

    f"V4 vs Broad PIT : "
    f"{B42_DIAGNOSIS['V4_minus_Broad_PIT_EW_pp']:+.3f} pp"
)


print(
    "\nACCEPTED RESEARCH INFRASTRUCTURE:"
)


for i, item in enumerate(
    B42_ACCEPTED_COMPONENTS,
    start=1,
):

    print(
        f"{i:2d}. {item}"
    )


print(
    "\nREJECTED V4 COMPONENTS:"
)


for i, item in enumerate(
    B42_REJECTED_COMPONENTS,
    start=1,
):

    print(
        f"{i:2d}. {item}"
    )


print(
    "\nFUTURE RESEARCH RULES:"
)


for i, item in enumerate(
    B42_NEXT_GENERATION_RULES,
    start=1,
):

    print(
        f"{i:2d}. {item}"
    )


print(
    "\nFINAL RESEARCH FINGERPRINT:"
)


print(
    V4_FINAL_RESEARCH_FINGERPRINT
)


print(
    "\n"
    +
    "=" * 120
)


if B42_GO:

    print(
        "[+] V4 RESEARCH GENERATION PASSED."
    )


    print(
        "[+] CHAMPION FROZEN."
    )


else:

    print(
        "[-] V4 RESEARCH GENERATION REJECTED."
    )


    print(
        "[-] V4 MUST NOT BE DEPLOYED OR POST-HOC TUNED."
    )


print(
    "[+] BLOCK 42 COMPLETE."
)


print(
    "[+] V4 RESEARCH GENERATION CLOSED."
)


print(
    "=" * 120
)
