# MODULE 39 — V8 VERSUS V12 EXACT AUDIT
# Run in the same notebook, in module order.

# ==============================================================================
# V12 — BLOCK 4
# V8 vs V12 APPLES-TO-APPLES ECONOMIC AUDIT
# SAME CALENDAR + SAME EXACT PRICES + SAME LINEAR TCA
# + COST HEADROOM + MULTI-PERIOD ROBUSTNESS
# ==============================================================================
#
# PURPOSE
# -------
# Compare the two successful research architectures:
#
#   V8  = frozen universal TQQQ + V7 alpha-sleeve challenger
#   V12 = frozen V7/V8 alpha sleeve + causal market-state allocation
#
# IMPORTANT
# ---------
# NO model fitting.
# NO parameter tuning.
# NO architecture change.
# NO stock-selection change.
# NO use of future data.
# NO interpolation.
# NO forward filling.
#
# V8 is simply re-accounted on the CURRENT repaired lifecycle price ledger
# used by V12 so that V8, V12 and TQQQ are directly comparable.
#
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hashlib
import json

from IPython.display import display


print("=" * 145)
print("V12 — BLOCK 4")
print("V8 vs V12 APPLES-TO-APPLES ECONOMIC AUDIT")
print("=" * 145)


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

REQUIRED = [
    "V12_STATE_PANEL",
    "V12_LIFECYCLE",
    "V12_EVENT_PATH",
    "V12_TQQQ_EVENT_PATH",
    "V12_FINAL_WEALTH",
    "V12_TQQQ_FINAL_WEALTH",
    "V8Q_WEIGHT_MATRIX",
]

missing = [
    name
    for name in REQUIRED
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"V12 Block 4 missing required objects: {missing}"
    )


STATE = V12_STATE_PANEL.copy()
LIFE = V12_LIFECYCLE.copy()
V8_MATRIX_RAW = V8Q_WEIGHT_MATRIX.copy()


# ==============================================================================
# 1. NORMALIZE CALENDAR
# ==============================================================================

for col in ["Signal_Date", "Execution_Date"]:

    if col not in STATE.columns:
        raise RuntimeError(
            f"V12_STATE_PANEL missing required column: {col}"
        )

    STATE[col] = (
        pd.to_datetime(
            STATE[col],
            errors="coerce"
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


STATE = (
    STATE
    .sort_values("Execution_Date")
    .reset_index(drop=True)
)


execution_dates = [
    pd.Timestamp(x).normalize()
    for x in STATE["Execution_Date"]
]


N_EVENTS = len(execution_dates)

if N_EVENTS != 34:
    raise RuntimeError(
        f"Expected 34 research decisions, found {N_EVENTS}."
    )


# ==============================================================================
# 2. NORMALIZE LIFECYCLE PRICE LEDGER
# ==============================================================================

life_required = [
    "Ticker",
    "Date",
    "Adj_Close",
]

life_missing = [
    c
    for c in life_required
    if c not in LIFE.columns
]

if life_missing:
    raise RuntimeError(
        f"V12_LIFECYCLE missing required columns: {life_missing}"
    )


LIFE["Ticker"] = (
    LIFE["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)

LIFE["Date"] = (
    pd.to_datetime(
        LIFE["Date"],
        errors="coerce"
    )
    .dt.tz_localize(None)
    .dt.normalize()
)

LIFE["Adj_Close"] = pd.to_numeric(
    LIFE["Adj_Close"],
    errors="coerce"
)


LIFE = (
    LIFE
    .dropna(
        subset=[
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    )
    .sort_values(
        ["Ticker", "Date"]
    )
    .drop_duplicates(
        ["Ticker", "Date"],
        keep="last"
    )
    .reset_index(drop=True)
)


PRICE_MAP = {
    (
        str(t).upper().strip(),
        pd.Timestamp(d).normalize(),
    ): float(p)

    for t, d, p in zip(
        LIFE["Ticker"],
        LIFE["Date"],
        LIFE["Adj_Close"],
    )

    if (
        np.isfinite(float(p))
        and
        float(p) > 0
    )
}


def exact_price(ticker, date):

    ticker = str(ticker).upper().strip()
    date = pd.Timestamp(date).normalize()

    return float(
        PRICE_MAP.get(
            (ticker, date),
            np.nan,
        )
    )


# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================

def normalize_weights(weights):

    out = {}

    for ticker, value in weights.items():

        try:
            value = float(value)
        except Exception:
            continue

        ticker = str(ticker).upper().strip()

        if (
            np.isfinite(value)
            and
            value > 0
        ):
            out[ticker] = value


    if not out:
        return {}


    total = float(
        sum(out.values())
    )


    if total > 1.5:

        out = {
            k: v / 100.0
            for k, v in out.items()
        }

        total = float(
            sum(out.values())
        )


    if total <= 0:
        return {}


    return {
        k: v / total
        for k, v in out.items()
    }


def normalize_weight_series(series):

    s = (
        pd.Series(series)
        .astype(float)
        .reset_index(drop=True)
    )

    finite = s[
        np.isfinite(s)
    ]

    if len(finite) == 0:
        raise RuntimeError(
            "Weight series contains no finite observations."
        )


    if float(
        finite.abs().median()
    ) > 1.5:

        s = s / 100.0


    return s.clip(
        lower=0.0,
        upper=1.0,
    )


def l1_turnover(old_weights, new_weights):

    names = (
        set(old_weights)
        |
        set(new_weights)
    )

    return float(
        sum(
            abs(
                float(
                    new_weights.get(
                        t,
                        0.0
                    )
                )
                -
                float(
                    old_weights.get(
                        t,
                        0.0
                    )
                )
            )

            for t in names
        )
    )


def drift_weights_exact(
    weights,
    start_date,
    end_date,
):

    values = {}


    for ticker, weight in weights.items():

        p0 = exact_price(
            ticker,
            start_date,
        )

        p1 = exact_price(
            ticker,
            end_date,
        )


        if (
            not np.isfinite(p0)
            or
            not np.isfinite(p1)
        ):

            raise RuntimeError(
                "Exact economically required drift price missing: "
                f"{ticker} | "
                f"{start_date.date()} -> {end_date.date()}"
            )


        values[ticker] = (
            float(weight)
            *
            p1 / p0
        )


    total = float(
        sum(values.values())
    )


    if (
        not np.isfinite(total)
        or
        total <= 0
    ):
        raise RuntimeError(
            "Invalid drifted portfolio value."
        )


    return {
        ticker: value / total
        for ticker, value in values.items()
    }


# ==============================================================================
# 4. RECONSTRUCT FROZEN V8 TARGETS
# ==============================================================================

if len(V8_MATRIX_RAW) != N_EVENTS:

    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX does not have the expected "
        f"{N_EVENTS} rows."
    )


V8_MATRIX = V8_MATRIX_RAW.copy()


# ------------------------------------------------------------------------------
# Keep only columns that contain numeric portfolio weights.
# ------------------------------------------------------------------------------

numeric_matrix = pd.DataFrame(
    index=V8_MATRIX.index
)


for col in V8_MATRIX.columns:

    converted = pd.to_numeric(
        V8_MATRIX[col],
        errors="coerce",
    )

    if converted.notna().any():

        numeric_matrix[
            str(col).upper().strip()
        ] = converted


V8_MATRIX = (
    numeric_matrix
    .fillna(0.0)
    .reset_index(drop=True)
)


# Remove obvious non-security aggregation columns.
for col in [
    "OTHER",
    "CASH",
    "ALPHA",
    "ALPHA_SLEEVE",
]:

    if col in V8_MATRIX.columns:

        V8_MATRIX = V8_MATRIX.drop(
            columns=[col]
        )


# Detect scale.
row_sums = V8_MATRIX.sum(
    axis=1
)

positive_sums = row_sums[
    row_sums > 0
]


if len(positive_sums) == 0:
    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX contains no usable weights."
    )


if float(
    positive_sums.median()
) > 1.5:

    V8_MATRIX = (
        V8_MATRIX / 100.0
    )


# ==============================================================================
# 5. RESOLVE V8 TQQQ SERIES
# ==============================================================================

if "TQQQ" in V8_MATRIX.columns:

    V8_TQQQ_FROM_MATRIX = (
        V8_MATRIX["TQQQ"]
        .astype(float)
        .reset_index(drop=True)
    )

else:

    V8_TQQQ_FROM_MATRIX = None


V8_TQQQ_SERIES = None


if "V8Q_TQQQ_WEIGHT" in globals():

    V8_TQQQ_SERIES = normalize_weight_series(
        V8Q_TQQQ_WEIGHT
    )


elif "V8Q_ALPHA_WEIGHT" in globals():

    alpha_series = normalize_weight_series(
        V8Q_ALPHA_WEIGHT
    )

    V8_TQQQ_SERIES = (
        1.0
        -
        alpha_series
    )


elif V8_TQQQ_FROM_MATRIX is not None:

    V8_TQQQ_SERIES = normalize_weight_series(
        V8_TQQQ_FROM_MATRIX
    )


else:

    raise RuntimeError(
        "Could not resolve the frozen V8 TQQQ-weight series."
    )


if len(V8_TQQQ_SERIES) != N_EVENTS:

    raise RuntimeError(
        "Resolved V8 TQQQ-weight series has incorrect length."
    )


# ==============================================================================
# 6. BUILD EXACT V8 PORTFOLIO TARGET MAP
# ==============================================================================

V8_TARGETS = {}


for i, execution_date in enumerate(
    execution_dates
):

    tqqq_w = float(
        V8_TQQQ_SERIES.iloc[i]
    )

    alpha_w = float(
        1.0
        -
        tqqq_w
    )


    row = (
        V8_MATRIX
        .iloc[i]
        .astype(float)
        .copy()
    )


    if "TQQQ" in row.index:
        row = row.drop(
            labels=["TQQQ"]
        )


    row = row[
        np.isfinite(row)
        &
        (row > 0)
    ]


    # --------------------------------------------------------------------------
    # 100% TQQQ event
    # --------------------------------------------------------------------------

    if (
        alpha_w <= 1e-12
        or
        len(row) == 0
    ):

        V8_TARGETS[
            execution_date
        ] = {
            "TQQQ": 1.0
        }

        continue


    stock_sum = float(
        row.sum()
    )


    # --------------------------------------------------------------------------
    # Matrix can be either:
    #
    # A) full-portfolio stock weights summing to alpha weight
    # B) normalized alpha-sleeve weights summing to one
    #
    # Detect structure from accounting identity only.
    # No performance information is used.
    # --------------------------------------------------------------------------

    direct_error = abs(
        stock_sum
        -
        alpha_w
    )

    sleeve_error = abs(
        stock_sum
        -
        1.0
    )


    if direct_error <= sleeve_error:

        stock_weights = row.copy()

    else:

        stock_weights = (
            row
            /
            stock_sum
            *
            alpha_w
        )


    weights = {
        "TQQQ":
            tqqq_w
    }


    for ticker, weight in stock_weights.items():

        weights[
            str(ticker).upper().strip()
        ] = float(weight)


    V8_TARGETS[
        execution_date
    ] = normalize_weights(
        weights
    )


# ==============================================================================
# 7. V8 STRUCTURAL AUDIT
# ==============================================================================

audit_rows = []


for i, dt in enumerate(
    execution_dates
):

    weights = V8_TARGETS[dt]

    audit_rows.append(
        {
            "Event":
                i + 1,

            "Execution_Date":
                dt,

            "Names":
                len(weights),

            "TQQQ_Weight_Pct":
                100.0
                *
                float(
                    weights.get(
                        "TQQQ",
                        0.0
                    )
                ),

            "Alpha_Weight_Pct":
                100.0
                *
                (
                    1.0
                    -
                    float(
                        weights.get(
                            "TQQQ",
                            0.0
                        )
                    )
                ),

            "Weight_Sum":
                float(
                    sum(
                        weights.values()
                    )
                ),
        }
    )


V8_REACCOUNT_TARGET_AUDIT = pd.DataFrame(
    audit_rows
)


max_weight_sum_error = float(
    (
        V8_REACCOUNT_TARGET_AUDIT[
            "Weight_Sum"
        ]
        -
        1.0
    )
    .abs()
    .max()
)


if max_weight_sum_error > 1e-10:

    raise RuntimeError(
        "V8 target reconstruction failed weight-sum validation."
    )


print(
    "\n[+] Frozen V8 target reconstruction passed."
)


# ==============================================================================
# 8. SAME TCA CONVENTION AS V12 BLOCK 3-R
# ==============================================================================

BASE_TCA_BPS = float(
    globals().get(
        "B40_TCA_BPS",
        2.0
    )
)

BASE_TCA_RATE = (
    BASE_TCA_BPS
    /
    10000.0
)


# ==============================================================================
# 9. EXACT V8 EXECUTION PREFLIGHT
# ==============================================================================

gaps = []


for i, dt in enumerate(
    execution_dates
):

    weights = V8_TARGETS[
        dt
    ]


    for ticker in weights:

        p = exact_price(
            ticker,
            dt,
        )

        if not np.isfinite(p):

            gaps.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "ENTRY",

                    "Requested_Date":
                        dt,
                }
            )


    if i == (
        N_EVENTS - 1
    ):
        continue


    next_dt = execution_dates[
        i + 1
    ]


    for ticker in weights:

        p = exact_price(
            ticker,
            next_dt,
        )

        if not np.isfinite(p):

            gaps.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "NEXT_REBALANCE",

                    "Requested_Date":
                        next_dt,
                }
            )


V8_REACCOUNT_PRICE_GAPS = pd.DataFrame(
    gaps
)


if len(
    V8_REACCOUNT_PRICE_GAPS
) > 0:

    print(
        "\n[!] V8 exact economic preflight failed:"
    )

    display(
        V8_REACCOUNT_PRICE_GAPS
    )

    raise RuntimeError(
        "Frozen V8 cannot be re-accounted exactly "
        "on the repaired lifecycle ledger."
    )


print(
    "[+] Frozen V8 exact execution/rebalance-price preflight passed."
)


# ==============================================================================
# 10. EXACT PORTFOLIO WALK-FORWARD ENGINE
# ==============================================================================

def run_exact_event_path(
    targets,
    strategy_name,
):

    wealth = 1.0
    previous_drifted = {}

    rows = []


    for i, dt in enumerate(
        execution_dates
    ):

        target = targets[
            dt
        ]


        turnover = l1_turnover(
            previous_drifted,
            target,
        )


        cost_rate = (
            BASE_TCA_RATE
            *
            turnover
        )


        # ----------------------------------------------------------------------
        # Final research-date rebalance:
        # include cost of reaching the final target,
        # but there is no future holding-period return.
        # ----------------------------------------------------------------------

        if i == (
            N_EVENTS - 1
        ):

            gross_return = 0.0

            net_return = (
                -cost_rate
            )

            wealth *= (
                1.0
                +
                net_return
            )


            rows.append(
                {
                    "Strategy":
                        strategy_name,

                    "Event":
                        i + 1,

                    "Signal_Date":
                        STATE.loc[
                            i,
                            "Signal_Date"
                        ],

                    "Execution_Date":
                        dt,

                    "Exit_Date":
                        dt,

                    "Names":
                        len(target),

                    "TQQQ_Weight":
                        float(
                            target.get(
                                "TQQQ",
                                0.0
                            )
                        ),

                    "Alpha_Weight":
                        float(
                            1.0
                            -
                            target.get(
                                "TQQQ",
                                0.0
                            )
                        ),

                    "Turnover":
                        turnover,

                    "TCA_bps":
                        10000.0
                        *
                        cost_rate,

                    "Gross_Return":
                        gross_return,

                    "Net_Return":
                        net_return,

                    "End_Wealth":
                        wealth,
                }
            )

            continue


        next_dt = execution_dates[
            i + 1
        ]


        gross_growth = 0.0


        for ticker, weight in target.items():

            p0 = exact_price(
                ticker,
                dt,
            )

            p1 = exact_price(
                ticker,
                next_dt,
            )


            gross_growth += (
                float(weight)
                *
                p1 / p0
            )


        gross_return = (
            gross_growth
            -
            1.0
        )


        net_growth = (
            gross_growth
            *
            (
                1.0
                -
                cost_rate
            )
        )


        net_return = (
            net_growth
            -
            1.0
        )


        wealth *= (
            net_growth
        )


        previous_drifted = (
            drift_weights_exact(
                target,
                dt,
                next_dt,
            )
        )


        rows.append(
            {
                "Strategy":
                    strategy_name,

                "Event":
                    i + 1,

                "Signal_Date":
                    STATE.loc[
                        i,
                        "Signal_Date"
                    ],

                "Execution_Date":
                    dt,

                "Exit_Date":
                    next_dt,

                "Names":
                    len(target),

                "TQQQ_Weight":
                    float(
                        target.get(
                            "TQQQ",
                            0.0
                        )
                    ),

                "Alpha_Weight":
                    float(
                        1.0
                        -
                        target.get(
                            "TQQQ",
                            0.0
                        )
                    ),

                "Turnover":
                    turnover,

                "TCA_bps":
                    10000.0
                    *
                    cost_rate,

                "Gross_Return":
                    gross_return,

                "Net_Return":
                    net_return,

                "End_Wealth":
                    wealth,
            }
        )


    return pd.DataFrame(
        rows
    )


# ==============================================================================
# 11. RE-ACCOUNT FROZEN V8
# ==============================================================================

V8_REACCOUNT_PATH = run_exact_event_path(
    V8_TARGETS,
    "V8_REACCOUNTED",
)


V8_REACCOUNT_FINAL_WEALTH = float(
    V8_REACCOUNT_PATH[
        "End_Wealth"
    ].iloc[-1]
)


V8_REACCOUNT_RETURN_PCT = (
    100.0
    *
    (
        V8_REACCOUNT_FINAL_WEALTH
        -
        1.0
    )
)


# ==============================================================================
# 12. CURRENT V12 / TQQQ PATHS
# ==============================================================================

V12_PATH = (
    V12_EVENT_PATH
    .copy()
    .reset_index(drop=True)
)


TQQQ_PATH = (
    V12_TQQQ_EVENT_PATH
    .copy()
    .reset_index(drop=True)
)


if (
    len(V12_PATH) != N_EVENTS
    or
    len(TQQQ_PATH) != N_EVENTS
):

    raise RuntimeError(
        "V12/TQQQ event-path length mismatch."
    )


# ==============================================================================
# 13. APPLES-TO-APPLES TERMINAL COMPARISON
# ==============================================================================

comparison = pd.DataFrame(
    [
        {
            "Strategy":
                "V12",

            "Final_Wealth":
                float(
                    V12_FINAL_WEALTH
                ),

            "Net_Return_Pct":
                100.0
                *
                (
                    float(
                        V12_FINAL_WEALTH
                    )
                    -
                    1.0
                ),

            "Vs_TQQQ_pp":
                100.0
                *
                (
                    float(
                        V12_FINAL_WEALTH
                    )
                    -
                    float(
                        V12_TQQQ_FINAL_WEALTH
                    )
                ),

            "Relative_Wealth_vs_TQQQ":
                float(
                    V12_FINAL_WEALTH
                )
                /
                float(
                    V12_TQQQ_FINAL_WEALTH
                ),
        },

        {
            "Strategy":
                "V8_REACCOUNTED",

            "Final_Wealth":
                V8_REACCOUNT_FINAL_WEALTH,

            "Net_Return_Pct":
                V8_REACCOUNT_RETURN_PCT,

            "Vs_TQQQ_pp":
                100.0
                *
                (
                    V8_REACCOUNT_FINAL_WEALTH
                    -
                    float(
                        V12_TQQQ_FINAL_WEALTH
                    )
                ),

            "Relative_Wealth_vs_TQQQ":
                V8_REACCOUNT_FINAL_WEALTH
                /
                float(
                    V12_TQQQ_FINAL_WEALTH
                ),
        },

        {
            "Strategy":
                "TQQQ",

            "Final_Wealth":
                float(
                    V12_TQQQ_FINAL_WEALTH
                ),

            "Net_Return_Pct":
                100.0
                *
                (
                    float(
                        V12_TQQQ_FINAL_WEALTH
                    )
                    -
                    1.0
                ),

            "Vs_TQQQ_pp":
                0.0,

            "Relative_Wealth_vs_TQQQ":
                1.0,
        },
    ]
)


comparison[
    "Vs_V8_pp"
] = (
    100.0
    *
    (
        comparison[
            "Final_Wealth"
        ]
        -
        V8_REACCOUNT_FINAL_WEALTH
    )
)


comparison = (
    comparison
    .sort_values(
        "Final_Wealth",
        ascending=False,
    )
    .reset_index(drop=True)
)


print(
    "\n1) APPLES-TO-APPLES TERMINAL WEALTH"
)

display(
    comparison
)


# ==============================================================================
# 14. ORIGINAL FROZEN V8 RECORD — REFERENCE ONLY
# ==============================================================================

original_v8_wealth = np.nan


for name in [
    "V8_FINAL_WEALTH",
    "V8_FROZEN_FINAL_WEALTH",
]:

    if name in globals():

        try:

            original_v8_wealth = float(
                globals()[name]
            )

            break

        except Exception:

            pass


if np.isfinite(
    original_v8_wealth
):

    print(
        "\nOriginal frozen V8 research wealth "
        "(historical record only): "
        f"{original_v8_wealth:.6f}"
    )

    print(
        "Current repaired-ledger V8 wealth: "
        f"{V8_REACCOUNT_FINAL_WEALTH:.6f}"
    )


# ==============================================================================
# 15. MULTI-PERIOD COMPLETED-HOLDING ROBUSTNESS
# ==============================================================================

V8_COMPLETED = (
    V8_REACCOUNT_PATH.iloc[
        :-1
    ]
    .copy()
)

V12_COMPLETED = (
    V12_PATH.iloc[
        :-1
    ]
    .copy()
)

TQQQ_COMPLETED = (
    TQQQ_PATH.iloc[
        :-1
    ]
    .copy()
)


if not (
    len(V8_COMPLETED)
    ==
    len(V12_COMPLETED)
    ==
    len(TQQQ_COMPLETED)
    ==
    33
):
    raise RuntimeError(
        "Expected exactly 33 completed holding periods."
    )


window_specs = [
    ("~1M", 1),
    ("~3M", 3),
    ("~6M", 6),
    ("~12M", 12),
    ("~24M", 24),
    ("ALL_COMPLETED", 33),
]


window_rows = []


for label, n in window_specs:

    v12_growth = float(
        np.prod(
            1.0
            +
            V12_COMPLETED[
                "Net_Return"
            ]
            .iloc[-n:]
            .values
        )
    )

    v8_growth = float(
        np.prod(
            1.0
            +
            V8_COMPLETED[
                "Net_Return"
            ]
            .iloc[-n:]
            .values
        )
    )

    tqqq_growth = float(
        np.prod(
            1.0
            +
            TQQQ_COMPLETED[
                "Net_Return"
            ]
            .iloc[-n:]
            .values
        )
    )


    window_rows.append(
        {
            "Window":
                label,

            "Periods":
                n,

            "V12_Return_Pct":
                100.0
                *
                (
                    v12_growth
                    -
                    1.0
                ),

            "V8_Return_Pct":
                100.0
                *
                (
                    v8_growth
                    -
                    1.0
                ),

            "TQQQ_Return_Pct":
                100.0
                *
                (
                    tqqq_growth
                    -
                    1.0
                ),

            "V12_minus_TQQQ_pp":
                100.0
                *
                (
                    v12_growth
                    -
                    tqqq_growth
                ),

            "V8_minus_TQQQ_pp":
                100.0
                *
                (
                    v8_growth
                    -
                    tqqq_growth
                ),

            "V12_minus_V8_pp":
                100.0
                *
                (
                    v12_growth
                    -
                    v8_growth
                ),

            "V12_Beats_TQQQ":
                bool(
                    v12_growth
                    >
                    tqqq_growth
                ),

            "V12_Beats_V8":
                bool(
                    v12_growth
                    >
                    v8_growth
                ),
        }
    )


V12_V8_WINDOW_AUDIT = pd.DataFrame(
    window_rows
)


print(
    "\n2) MULTI-PERIOD ROBUSTNESS"
)

display(
    V12_V8_WINDOW_AUDIT
)


# ==============================================================================
# 16. EVENT-LEVEL COMPARISON
# ==============================================================================

event_compare = pd.DataFrame(
    {
        "Execution_Date":
            V12_COMPLETED[
                "Execution_Date"
            ]
            .values,

        "Exit_Date":
            V12_COMPLETED[
                "Exit_Date"
            ]
            .values,

        "V12_Return_Pct":
            100.0
            *
            V12_COMPLETED[
                "Net_Return"
            ]
            .values,

        "V8_Return_Pct":
            100.0
            *
            V8_COMPLETED[
                "Net_Return"
            ]
            .values,

        "TQQQ_Return_Pct":
            100.0
            *
            TQQQ_COMPLETED[
                "Net_Return"
            ]
            .values,
    }
)


event_compare[
    "V12_minus_TQQQ_pp"
] = (
    event_compare[
        "V12_Return_Pct"
    ]
    -
    event_compare[
        "TQQQ_Return_Pct"
    ]
)


event_compare[
    "V12_minus_V8_pp"
] = (
    event_compare[
        "V12_Return_Pct"
    ]
    -
    event_compare[
        "V8_Return_Pct"
    ]
)


V12_BEAT_TQQQ_EVENT_PCT = (
    100.0
    *
    (
        event_compare[
            "V12_minus_TQQQ_pp"
        ]
        >
        0
    )
    .mean()
)


V12_BEAT_V8_EVENT_PCT = (
    100.0
    *
    (
        event_compare[
            "V12_minus_V8_pp"
        ]
        >
        0
    )
    .mean()
)


print(
    "\n3) EVENT-LEVEL SUMMARY"
)

display(
    pd.DataFrame(
        [
            (
                "V12 beat TQQQ event pct",
                V12_BEAT_TQQQ_EVENT_PCT,
            ),

            (
                "V12 beat V8 event pct",
                V12_BEAT_V8_EVENT_PCT,
            ),

            (
                "V12 mean excess vs TQQQ pp",
                event_compare[
                    "V12_minus_TQQQ_pp"
                ].mean(),
            ),

            (
                "V12 median excess vs TQQQ pp",
                event_compare[
                    "V12_minus_TQQQ_pp"
                ].median(),
            ),

            (
                "V12 mean excess vs V8 pp",
                event_compare[
                    "V12_minus_V8_pp"
                ].mean(),
            ),

            (
                "V12 median excess vs V8 pp",
                event_compare[
                    "V12_minus_V8_pp"
                ].median(),
            ),
        ],
        columns=[
            "Metric",
            "Value",
        ],
    )
)


print(
    "\nLast 12 completed events:"
)

display(
    event_compare.tail(
        12
    )
)


# ==============================================================================
# 17. COST HEADROOM
# ==============================================================================

# ------------------------------------------------------------------------------
# This does NOT estimate nonlinear market impact.
#
# It asks a cleaner question:
#
# "How much ADDITIONAL uniform execution drag per completed holding period
#  could V12 absorb before terminal wealth falls to the comparator?"
#
# This is a diagnostic safety margin only.
# ------------------------------------------------------------------------------

completed_periods = len(
    V12_COMPLETED
)


def equivalent_extra_cost_headroom(
    source_wealth,
    comparator_wealth,
    periods,
):

    source_wealth = float(
        source_wealth
    )

    comparator_wealth = float(
        comparator_wealth
    )


    if (
        source_wealth <= 0
        or
        comparator_wealth <= 0
    ):
        return {
            "Cumulative_Wealth_Drag_Pct":
                np.nan,

            "Equivalent_Extra_Cost_bps_Per_Period":
                np.nan,
        }


    if source_wealth <= comparator_wealth:

        return {
            "Cumulative_Wealth_Drag_Pct":
                0.0,

            "Equivalent_Extra_Cost_bps_Per_Period":
                0.0,
        }


    cumulative_drag = (
        1.0
        -
        comparator_wealth
        /
        source_wealth
    )


    per_period_drag = (
        1.0
        -
        (
            comparator_wealth
            /
            source_wealth
        )
        **
        (
            1.0
            /
            periods
        )
    )


    return {
        "Cumulative_Wealth_Drag_Pct":
            100.0
            *
            cumulative_drag,

        "Equivalent_Extra_Cost_bps_Per_Period":
            10000.0
            *
            per_period_drag,
    }


headroom_tqqq = (
    equivalent_extra_cost_headroom(
        V12_FINAL_WEALTH,
        V12_TQQQ_FINAL_WEALTH,
        completed_periods,
    )
)


headroom_v8 = (
    equivalent_extra_cost_headroom(
        V12_FINAL_WEALTH,
        V8_REACCOUNT_FINAL_WEALTH,
        completed_periods,
    )
)


V12_COST_HEADROOM = pd.DataFrame(
    [
        {
            "Comparator":
                "TQQQ",

            **headroom_tqqq,
        },

        {
            "Comparator":
                "V8_REACCOUNTED",

            **headroom_v8,
        },
    ]
)


print(
    "\n4) V12 ADDITIONAL EXECUTION-COST HEADROOM"
)

display(
    V12_COST_HEADROOM
)


# ==============================================================================
# 18. TURNOVER / ALLOCATION COMPARISON
# ==============================================================================

allocation_compare = pd.DataFrame(
    [
        {
            "Strategy":
                "V12",

            "Total_Turnover":
                float(
                    V12_PATH[
                        "Turnover"
                    ].sum()
                ),

            "Mean_Turnover":
                float(
                    V12_PATH[
                        "Turnover"
                    ].mean()
                ),

            "Mean_TQQQ_Weight_Pct":
                100.0
                *
                float(
                    V12_PATH[
                        "TQQQ_Target_Weight"
                    ].mean()
                ),

            "Mean_Alpha_Weight_Pct":
                100.0
                *
                float(
                    V12_PATH[
                        "Alpha_Target_Weight"
                    ].mean()
                ),
        },

        {
            "Strategy":
                "V8_REACCOUNTED",

            "Total_Turnover":
                float(
                    V8_REACCOUNT_PATH[
                        "Turnover"
                    ].sum()
                ),

            "Mean_Turnover":
                float(
                    V8_REACCOUNT_PATH[
                        "Turnover"
                    ].mean()
                ),

            "Mean_TQQQ_Weight_Pct":
                100.0
                *
                float(
                    V8_REACCOUNT_PATH[
                        "TQQQ_Weight"
                    ].mean()
                ),

            "Mean_Alpha_Weight_Pct":
                100.0
                *
                float(
                    V8_REACCOUNT_PATH[
                        "Alpha_Weight"
                    ].mean()
                ),
        },
    ]
)


print(
    "\n5) ALLOCATION / TURNOVER COMPARISON"
)

display(
    allocation_compare
)


# ==============================================================================
# 19. TERMINAL-WEALTH LINE CHART
# ==============================================================================

plot_dates = pd.to_datetime(
    V12_PATH[
        "Exit_Date"
    ]
)


plt.figure(
    figsize=(15, 7)
)

plt.plot(
    plot_dates,
    V12_PATH[
        "End_Wealth"
    ],
    label="V12",
    linewidth=2.2,
)

plt.plot(
    plot_dates,
    V8_REACCOUNT_PATH[
        "End_Wealth"
    ],
    label="V8 — re-accounted",
    linewidth=2.0,
)

plt.plot(
    plot_dates,
    TQQQ_PATH[
        "End_Wealth"
    ],
    label="TQQQ",
    linewidth=2.0,
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1.0,
)

plt.title(
    "V12 vs V8 vs TQQQ — EXACT EVENT-LEVEL NET WEALTH"
)

plt.ylabel(
    "Wealth Multiple"
)

plt.xlabel(
    "Date"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# ==============================================================================
# 20. RELATIVE-WEALTH LINE CHART
# ==============================================================================

relative_v12 = (
    V12_PATH[
        "End_Wealth"
    ].values
    /
    TQQQ_PATH[
        "End_Wealth"
    ].values
)


relative_v8 = (
    V8_REACCOUNT_PATH[
        "End_Wealth"
    ].values
    /
    TQQQ_PATH[
        "End_Wealth"
    ].values
)


plt.figure(
    figsize=(15, 7)
)

plt.plot(
    plot_dates,
    relative_v12,
    label="V12 / TQQQ",
    linewidth=2.2,
)

plt.plot(
    plot_dates,
    relative_v8,
    label="V8 / TQQQ",
    linewidth=2.0,
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1.2,
)

plt.title(
    "RELATIVE WEALTH vs TQQQ"
)

plt.ylabel(
    "Relative Wealth"
)

plt.xlabel(
    "Date"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# ==============================================================================
# 21. TQQQ / ALPHA ALLOCATION LINE CHART
# ==============================================================================

plt.figure(
    figsize=(15, 7)
)

plt.plot(
    V12_PATH[
        "Execution_Date"
    ],
    100.0
    *
    V12_PATH[
        "TQQQ_Target_Weight"
    ],
    label="V12 TQQQ",
    linewidth=2.0,
)

plt.plot(
    V12_PATH[
        "Execution_Date"
    ],
    100.0
    *
    V12_PATH[
        "Alpha_Target_Weight"
    ],
    label="V12 Alpha",
    linewidth=2.0,
)

plt.plot(
    V8_REACCOUNT_PATH[
        "Execution_Date"
    ],
    100.0
    *
    V8_REACCOUNT_PATH[
        "TQQQ_Weight"
    ],
    label="V8 TQQQ",
    linewidth=1.5,
    linestyle="--",
)

plt.plot(
    V8_REACCOUNT_PATH[
        "Execution_Date"
    ],
    100.0
    *
    V8_REACCOUNT_PATH[
        "Alpha_Weight"
    ],
    label="V8 Alpha",
    linewidth=1.5,
    linestyle="--",
)

plt.axhline(
    50.0,
    linestyle=":",
    linewidth=1.0,
)

plt.title(
    "V12 vs V8 — TQQQ / ALPHA ALLOCATION"
)

plt.ylabel(
    "Portfolio Weight (%)"
)

plt.xlabel(
    "Execution Date"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# ==============================================================================
# 22. PRIMARY COMPARATIVE VERDICT
# ==============================================================================

V12_BEATS_CURRENT_TQQQ = bool(
    float(
        V12_FINAL_WEALTH
    )
    >
    float(
        V12_TQQQ_FINAL_WEALTH
    )
)


V12_BEATS_REACCOUNTED_V8 = bool(
    float(
        V12_FINAL_WEALTH
    )
    >
    float(
        V8_REACCOUNT_FINAL_WEALTH
    )
)


V8_BEATS_CURRENT_TQQQ = bool(
    float(
        V8_REACCOUNT_FINAL_WEALTH
    )
    >
    float(
        V12_TQQQ_FINAL_WEALTH
    )
)


print(
    "\n6) COMPARATIVE RESEARCH VERDICT"
)

print(
    f"V12 beats TQQQ          : "
    f"{V12_BEATS_CURRENT_TQQQ}"
)

print(
    f"V12 beats V8            : "
    f"{V12_BEATS_REACCOUNTED_V8}"
)

print(
    f"V8 beats TQQQ           : "
    f"{V8_BEATS_CURRENT_TQQQ}"
)


# ==============================================================================
# 23. FINGERPRINT
# ==============================================================================

payload = {
    "version":
        "V12_BLOCK_4",

    "events":
        int(
            N_EVENTS
        ),

    "completed_periods":
        int(
            completed_periods
        ),

    "base_tca_bps":
        float(
            BASE_TCA_BPS
        ),

    "v12_final_wealth":
        round(
            float(
                V12_FINAL_WEALTH
            ),
            12,
        ),

    "v8_reaccount_final_wealth":
        round(
            float(
                V8_REACCOUNT_FINAL_WEALTH
            ),
            12,
        ),

    "tqqq_final_wealth":
        round(
            float(
                V12_TQQQ_FINAL_WEALTH
            ),
            12,
        ),

    "v12_beats_v8":
        bool(
            V12_BEATS_REACCOUNTED_V8
        ),

    "v12_beats_tqqq":
        bool(
            V12_BEATS_CURRENT_TQQQ
        ),
}


V12_BLOCK4_FINGERPRINT = hashlib.sha256(
    json.dumps(
        payload,
        sort_keys=True,
    )
    .encode()
).hexdigest()


print(
    "\n7) V12 BLOCK 4 FINGERPRINT"
)

print(
    V12_BLOCK4_FINGERPRINT
)


# ==============================================================================
# 24. INTEGRITY
# ==============================================================================

print(
    "\nINTEGRITY:"
)

print(
    "[+] V8 architecture was NOT changed."
)

print(
    "[+] V12 architecture was NOT changed."
)

print(
    "[+] No model was fitted."
)

print(
    "[+] No parameter was tuned."
)

print(
    "[+] No stock-selection rule was changed."
)

print(
    "[+] Both V8 and V12 use the same repaired lifecycle price ledger."
)

print(
    "[+] Both V8 and V12 use the same execution calendar."
)

print(
    "[+] Both V8 and V12 use the same linear TCA convention."
)

print(
    "[+] TQQQ uses the same repaired lifecycle ledger."
)

print(
    "[+] No intermediate missing daily price was fabricated."
)

print(
    "[+] Cost headroom is diagnostic only and is NOT a trading parameter."
)


print(
    "\nNEXT:"
)

if (
    V12_BEATS_CURRENT_TQQQ
    and
    V12_BEATS_REACCOUNTED_V8
):

    print(
        "[+] V12 is the leading research architecture."
    )

    print(
        "[+] Next step: final execution-cost consistency audit, "
        "then freeze V12."
    )

else:

    print(
        "[!] V12 is not superior to both frozen comparators "
        "under identical accounting."
    )

    print(
        "[!] Do not modify V12 after observing this result."
    )


print("=" * 145)
