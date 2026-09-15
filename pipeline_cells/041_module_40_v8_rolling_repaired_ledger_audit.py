# MODULE 40 — V8 ROLLING REPAIRED-LEDGER AUDIT
# Run in the same notebook, in module order.

# ==============================================================================
# V8 — REPAIRED-LEDGER CHAMPION ROBUSTNESS AUDIT
# ALL CONTIGUOUS ROLLING EVENT WINDOWS vs TQQQ
# ==============================================================================
#
# PURPOSE
# -------
# Test the current champion, V8, across EVERY available contiguous
# completed holding-period window.
#
# NO model fitting.
# NO parameter tuning.
# NO architecture change.
# NO data download.
# NO daily NAV reconstruction.
#
# This is a diagnostic robustness audit only.
#
# ==============================================================================

import numpy as np
import pandas as pd
import hashlib
import json

from IPython.display import display


print("=" * 145)
print("V8 — REPAIRED-LEDGER CHAMPION ROBUSTNESS AUDIT")
print("ALL CONTIGUOUS ROLLING EVENT WINDOWS vs TQQQ")
print("=" * 145)


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

REQUIRED = [
    "V8_REACCOUNT_PATH",
    "TQQQ_PATH",
    "V8_REACCOUNT_FINAL_WEALTH",
    "V12_TQQQ_FINAL_WEALTH",
]

missing = [
    name
    for name in REQUIRED
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing required objects: {missing}"
    )


V8_PATH = (
    V8_REACCOUNT_PATH
    .copy()
    .reset_index(drop=True)
)

BENCH_PATH = (
    TQQQ_PATH
    .copy()
    .reset_index(drop=True)
)


# ==============================================================================
# 1. VALIDATE PATHS
# ==============================================================================

required_cols = [
    "Execution_Date",
    "Exit_Date",
    "Net_Return",
    "End_Wealth",
]

for name, frame in [
    ("V8", V8_PATH),
    ("TQQQ", BENCH_PATH),
]:

    missing_cols = [
        c
        for c in required_cols
        if c not in frame.columns
    ]

    if missing_cols:
        raise RuntimeError(
            f"{name} path missing columns: {missing_cols}"
        )


if len(V8_PATH) != len(BENCH_PATH):
    raise RuntimeError(
        "V8 and TQQQ event paths have different lengths."
    )


# Final row is the research-end rebalance with no completed holding period.
V8_COMPLETED = (
    V8_PATH.iloc[:-1]
    .copy()
    .reset_index(drop=True)
)

TQQQ_COMPLETED = (
    BENCH_PATH.iloc[:-1]
    .copy()
    .reset_index(drop=True)
)


N = len(V8_COMPLETED)

if N != len(TQQQ_COMPLETED):
    raise RuntimeError(
        "Completed V8/TQQQ path lengths do not match."
    )


if N < 1:
    raise RuntimeError(
        "No completed holding periods available."
    )


for frame in [
    V8_COMPLETED,
    TQQQ_COMPLETED,
]:

    frame["Execution_Date"] = (
        pd.to_datetime(frame["Execution_Date"])
        .dt.tz_localize(None)
        .dt.normalize()
    )

    frame["Exit_Date"] = (
        pd.to_datetime(frame["Exit_Date"])
        .dt.tz_localize(None)
        .dt.normalize()
    )

    frame["Net_Return"] = pd.to_numeric(
        frame["Net_Return"],
        errors="raise",
    )


if not np.all(
    V8_COMPLETED["Execution_Date"].values
    ==
    TQQQ_COMPLETED["Execution_Date"].values
):
    raise RuntimeError(
        "V8 and TQQQ execution calendars differ."
    )


if not np.all(
    V8_COMPLETED["Exit_Date"].values
    ==
    TQQQ_COMPLETED["Exit_Date"].values
):
    raise RuntimeError(
        "V8 and TQQQ exit calendars differ."
    )


print(
    f"\n[+] Completed holding periods: {N}"
)

print(
    "[+] V8 / TQQQ calendars match exactly."
)


# ==============================================================================
# 2. EXACT ROLLING-WINDOW ENGINE
# ==============================================================================

def rolling_window_audit(
    strategy_returns,
    benchmark_returns,
    execution_dates,
    exit_dates,
    periods,
):

    strategy_returns = np.asarray(
        strategy_returns,
        dtype=float,
    )

    benchmark_returns = np.asarray(
        benchmark_returns,
        dtype=float,
    )


    rows = []


    for start in range(
        0,
        len(strategy_returns) - periods + 1,
    ):

        end = start + periods


        strategy_growth = float(
            np.prod(
                1.0
                +
                strategy_returns[
                    start:end
                ]
            )
        )


        benchmark_growth = float(
            np.prod(
                1.0
                +
                benchmark_returns[
                    start:end
                ]
            )
        )


        strategy_return_pct = (
            100.0
            *
            (
                strategy_growth
                -
                1.0
            )
        )


        benchmark_return_pct = (
            100.0
            *
            (
                benchmark_growth
                -
                1.0
            )
        )


        excess_pp = (
            strategy_return_pct
            -
            benchmark_return_pct
        )


        rows.append(
            {
                "Start_Event":
                    start + 1,

                "End_Event":
                    end,

                "Start_Date":
                    execution_dates.iloc[start],

                "End_Date":
                    exit_dates.iloc[end - 1],

                "V8_Return_Pct":
                    strategy_return_pct,

                "TQQQ_Return_Pct":
                    benchmark_return_pct,

                "V8_Minus_TQQQ_pp":
                    excess_pp,

                "V8_Beats_TQQQ":
                    bool(
                        excess_pp > 0
                    ),
            }
        )


    return pd.DataFrame(
        rows
    )


# ==============================================================================
# 3. DECLARED EVENT HORIZONS
# ==============================================================================

WINDOWS = [
    ("~1M", 1),
    ("~3M", 3),
    ("~6M", 6),
    ("~12M", 12),
    ("~24M", 24),
]


summary_rows = []
window_tables = {}


for label, periods in WINDOWS:

    if periods > N:
        continue


    table = rolling_window_audit(
        strategy_returns=
            V8_COMPLETED["Net_Return"],

        benchmark_returns=
            TQQQ_COMPLETED["Net_Return"],

        execution_dates=
            V8_COMPLETED["Execution_Date"],

        exit_dates=
            V8_COMPLETED["Exit_Date"],

        periods=
            periods,
    )


    window_tables[label] = table


    excess = table[
        "V8_Minus_TQQQ_pp"
    ]


    beat_rate = (
        100.0
        *
        table[
            "V8_Beats_TQQQ"
        ]
        .mean()
    )


    worst_idx = excess.idxmin()

    best_idx = excess.idxmax()


    summary_rows.append(
        {
            "Window":
                label,

            "Periods":
                periods,

            "Rolling_Windows":
                len(table),

            "Beat_Rate_Pct":
                beat_rate,

            "Mean_Excess_pp":
                float(
                    excess.mean()
                ),

            "Median_Excess_pp":
                float(
                    excess.median()
                ),

            "Minimum_Excess_pp":
                float(
                    excess.min()
                ),

            "Maximum_Excess_pp":
                float(
                    excess.max()
                ),

            "Worst_Window_Start":
                table.loc[
                    worst_idx,
                    "Start_Date"
                ],

            "Worst_Window_End":
                table.loc[
                    worst_idx,
                    "End_Date"
                ],

            "Best_Window_Start":
                table.loc[
                    best_idx,
                    "Start_Date"
                ],

            "Best_Window_End":
                table.loc[
                    best_idx,
                    "End_Date"
                ],

            "Strict_All_Windows_PASS":
                bool(
                    (
                        excess > 0
                    )
                    .all()
                ),

            "Majority_Windows_PASS":
                bool(
                    beat_rate > 50.0
                ),

            "Positive_Median_PASS":
                bool(
                    excess.median() > 0
                ),
        }
    )


V8_ALL_ROLLING_SUMMARY = pd.DataFrame(
    summary_rows
)


# ==============================================================================
# 4. FULL HISTORY
# ==============================================================================

full_v8_growth = float(
    np.prod(
        1.0
        +
        V8_COMPLETED[
            "Net_Return"
        ].values
    )
)


full_tqqq_growth = float(
    np.prod(
        1.0
        +
        TQQQ_COMPLETED[
            "Net_Return"
        ].values
    )
)


full_v8_return = (
    100.0
    *
    (
        full_v8_growth - 1.0
    )
)


full_tqqq_return = (
    100.0
    *
    (
        full_tqqq_growth - 1.0
    )
)


full_excess = (
    full_v8_return
    -
    full_tqqq_return
)


V8_FULL_HISTORY_AUDIT = pd.DataFrame(
    [
        {
            "Window":
                "FULL_COMPLETED",

            "Periods":
                N,

            "V8_Return_Pct":
                full_v8_return,

            "TQQQ_Return_Pct":
                full_tqqq_return,

            "V8_Minus_TQQQ_pp":
                full_excess,

            "PASS":
                bool(
                    full_excess > 0
                ),
        }
    ]
)


# ==============================================================================
# 5. DISPLAY SUMMARY
# ==============================================================================

print(
    "\n1) ALL ROLLING-WINDOW SUMMARY"
)

display(
    V8_ALL_ROLLING_SUMMARY
)


print(
    "\n2) FULL COMPLETED HISTORY"
)

display(
    V8_FULL_HISTORY_AUDIT
)


# ==============================================================================
# 6. FAILURE CONCENTRATION
# ==============================================================================

failure_rows = []


for label, table in window_tables.items():

    failed = (
        table[
            ~table[
                "V8_Beats_TQQQ"
            ]
        ]
        .copy()
    )


    for _, row in failed.iterrows():

        failure_rows.append(
            {
                "Window":
                    label,

                "Start_Date":
                    row[
                        "Start_Date"
                    ],

                "End_Date":
                    row[
                        "End_Date"
                    ],

                "V8_Return_Pct":
                    row[
                        "V8_Return_Pct"
                    ],

                "TQQQ_Return_Pct":
                    row[
                        "TQQQ_Return_Pct"
                    ],

                "V8_Minus_TQQQ_pp":
                    row[
                        "V8_Minus_TQQQ_pp"
                    ],
            }
        )


V8_ROLLING_FAILURES = pd.DataFrame(
    failure_rows
)


if len(
    V8_ROLLING_FAILURES
) > 0:

    V8_ROLLING_FAILURES = (
        V8_ROLLING_FAILURES
        .sort_values(
            "V8_Minus_TQQQ_pp"
        )
        .reset_index(drop=True)
    )


    print(
        "\n3) WORST 20 ROLLING UNDERPERFORMANCE WINDOWS"
    )

    display(
        V8_ROLLING_FAILURES.head(
            20
        )
    )

else:

    print(
        "\n3) NO ROLLING WINDOW UNDERPERFORMANCE FOUND."
    )


# ==============================================================================
# 7. ROBUSTNESS SCORECARD
# ==============================================================================

strict_passes = int(
    V8_ALL_ROLLING_SUMMARY[
        "Strict_All_Windows_PASS"
    ].sum()
)


majority_passes = int(
    V8_ALL_ROLLING_SUMMARY[
        "Majority_Windows_PASS"
    ].sum()
)


median_passes = int(
    V8_ALL_ROLLING_SUMMARY[
        "Positive_Median_PASS"
    ].sum()
)


total_horizons = len(
    V8_ALL_ROLLING_SUMMARY
)


all_strict = bool(
    strict_passes
    ==
    total_horizons
)


all_majority = bool(
    majority_passes
    ==
    total_horizons
)


all_positive_median = bool(
    median_passes
    ==
    total_horizons
)


full_pass = bool(
    full_excess > 0
)


V8_ROBUSTNESS_SCORECARD = pd.DataFrame(
    [
        (
            "Declared rolling horizons",
            total_horizons,
        ),

        (
            "Horizons with >50% beat rate",
            majority_passes,
        ),

        (
            "Horizons with positive median excess",
            median_passes,
        ),

        (
            "Horizons with 100% rolling-window dominance",
            strict_passes,
        ),

        (
            "Full-history TQQQ dominance",
            full_pass,
        ),

        (
            "All horizons majority PASS",
            all_majority,
        ),

        (
            "All horizons positive-median PASS",
            all_positive_median,
        ),

        (
            "All horizons strict 100% dominance PASS",
            all_strict,
        ),
    ],
    columns=[
        "Metric",
        "Value",
    ],
)


print(
    "\n4) ROBUSTNESS SCORECARD"
)

display(
    V8_ROBUSTNESS_SCORECARD
)


# ==============================================================================
# 8. FINGERPRINT
# ==============================================================================

fingerprint_payload = {
    "version":
        "V8_REPAIRED_LEDGER_ROLLING_AUDIT",

    "completed_periods":
        int(N),

    "v8_full_growth":
        round(
            full_v8_growth,
            12,
        ),

    "tqqq_full_growth":
        round(
            full_tqqq_growth,
            12,
        ),

    "full_excess_pp":
        round(
            full_excess,
            12,
        ),

    "strict_passes":
        strict_passes,

    "majority_passes":
        majority_passes,

    "median_passes":
        median_passes,

    "total_horizons":
        total_horizons,
}


V8_REPAIRED_ROLLING_AUDIT_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            sort_keys=True,
        )
        .encode()
    )
    .hexdigest()
)


print(
    "\n5) AUDIT FINGERPRINT"
)

print(
    V8_REPAIRED_ROLLING_AUDIT_FINGERPRINT
)


# ==============================================================================
# 9. FINAL VERDICT
# ==============================================================================

print(
    "\nVERDICT:"
)

print(
    f"V8 full history beats TQQQ               : {full_pass}"
)

print(
    f"All horizons >50% rolling beat rate      : {all_majority}"
)

print(
    f"All horizons positive median excess      : {all_positive_median}"
)

print(
    f"All rolling windows beat TQQQ strictly   : {all_strict}"
)


if (
    full_pass
    and
    all_majority
    and
    all_positive_median
):

    print(
        "\n[+] V8 shows broad TQQQ-relative robustness."
    )

else:

    print(
        "\n[!] V8 advantage is not uniformly robust across horizons."
    )


if all_strict:

    print(
        "[+] Extremely strong result: every tested rolling window beats TQQQ."
    )

else:

    print(
        "[i] Some historical rolling windows still underperform TQQQ."
    )

    print(
        "[i] Do NOT tune V8 using those failed windows."
    )


print(
    "\nINTEGRITY:"
)

print(
    "[+] V8 architecture unchanged."
)

print(
    "[+] V12 architecture unchanged."
)

print(
    "[+] No model fit."
)

print(
    "[+] No parameter search."
)

print(
    "[+] No performance-derived trading rule."
)

print(
    "[+] Only completed exact economic holding periods were evaluated."
)

print("=" * 145)
