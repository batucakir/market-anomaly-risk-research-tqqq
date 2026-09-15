# MODULE 38 — V12 ECONOMIC TEST
# Run in the same notebook, in module order.

# ==============================================================================
# V12 — BLOCK 3-R
# ONE-SHOT EXACT EVENT-LEVEL ECONOMIC TEST
# + TQQQ RELATIVE EVALUATION
# + DAILY-NAV DIAGNOSTIC WITHOUT FABRICATING PRICES
# ==============================================================================
#
# IMPORTANT
# ---------
# This cell REPLACES the previous V12 Block 3.
#
# It deliberately separates:
#
#   1) ECONOMIC PERFORMANCE
#      Exact execution-date -> next-execution-date valuation.
#
#   2) DAILY NAV DIAGNOSTICS
#      Optional only. Missing intermediate daily observations cannot invalidate
#      an otherwise exact execution-to-execution economic result.
#
# NO:
# - model fitting
# - stock-selection change
# - parameter tuning
# - interpolation
# - forward fill
# - synthetic security prices
#
# ==============================================================================

import numpy as np
import pandas as pd
import hashlib
import json

from IPython.display import display


print("=" * 140)
print("V12 — BLOCK 3-R")
print("ONE-SHOT EXACT EVENT-LEVEL ECONOMIC TEST")
print("+ TQQQ RELATIVE EVALUATION")
print("=" * 140)


# ==============================================================================
# 0. REQUIRED FROZEN STATE
# ==============================================================================

V12_REQUIRED = [
    "V12_STATE_PANEL",
    "V12_LIFECYCLE",
]

V12_MISSING = [
    x for x in V12_REQUIRED
    if x not in globals()
]

if V12_MISSING:
    raise RuntimeError(
        f"V12 Block 3-R missing required frozen objects: {V12_MISSING}"
    )


STATE = V12_STATE_PANEL.copy()
LIFE  = V12_LIFECYCLE.copy()


# ==============================================================================
# 1. NORMALIZE STATE PANEL
# ==============================================================================

for c in ["Signal_Date", "Execution_Date"]:
    if c not in STATE.columns:
        raise RuntimeError(
            f"V12_STATE_PANEL is missing required column: {c}"
        )

    STATE[c] = (
        pd.to_datetime(
            STATE[c],
            errors="coerce"
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )


if STATE["Execution_Date"].isna().any():
    raise RuntimeError(
        "V12_STATE_PANEL contains invalid Execution_Date values."
    )


STATE = (
    STATE
    .sort_values("Execution_Date")
    .reset_index(drop=True)
)


N_EVENTS = len(STATE)

if N_EVENTS != 34:
    raise RuntimeError(
        f"Expected 34 frozen V12 research decisions, found {N_EVENTS}."
    )


# ==============================================================================
# 2. NORMALIZE LIFECYCLE PRICE PANEL
# ==============================================================================

required_life_cols = [
    "Ticker",
    "Date",
    "Adj_Close",
]

missing_life_cols = [
    c for c in required_life_cols
    if c not in LIFE.columns
]

if missing_life_cols:
    raise RuntimeError(
        "V12_LIFECYCLE is missing columns: "
        f"{missing_life_cols}"
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


# ==============================================================================
# 3. RESOLVE THE FROZEN V12 TARGETS FROM BLOCK 2
# ==============================================================================

def _normalize_weight_dict(d):

    if d is None:
        return {}

    out = {}

    for k, v in dict(d).items():

        ticker = str(k).upper().strip()

        try:
            value = float(v)
        except Exception:
            continue

        if (
            np.isfinite(value)
            and value > 0
        ):
            out[ticker] = value

    if not out:
        return {}

    s = float(sum(out.values()))

    # Automatically recognize percent-form dictionaries.
    if s > 1.5:
        out = {
            k: v / 100.0
            for k, v in out.items()
        }

    s = float(sum(out.values()))

    if s <= 0:
        return {}

    return {
        k: v / s
        for k, v in out.items()
    }


def _targets_from_dataframe(df):

    x = df.copy()

    date_candidates = [
        "Execution_Date",
        "Date",
    ]

    ticker_candidates = [
        "Ticker",
        "Symbol",
    ]

    weight_candidates = [
        "Weight",
        "Weight_Fraction",
        "Target_Weight",
        "Weight_Pct",
    ]


    date_col = next(
        (
            c for c in date_candidates
            if c in x.columns
        ),
        None
    )

    ticker_col = next(
        (
            c for c in ticker_candidates
            if c in x.columns
        ),
        None
    )

    weight_col = next(
        (
            c for c in weight_candidates
            if c in x.columns
        ),
        None
    )


    if (
        date_col is None
        or ticker_col is None
        or weight_col is None
    ):
        return None


    x[date_col] = (
        pd.to_datetime(
            x[date_col],
            errors="coerce"
        )
        .dt.tz_localize(None)
        .dt.normalize()
    )

    result = {}

    for dt, g in x.groupby(date_col):

        raw = dict(
            zip(
                g[ticker_col],
                g[weight_col],
            )
        )

        result[
            pd.Timestamp(dt).normalize()
        ] = _normalize_weight_dict(raw)

    return result


V12_TARGET_MAP = None
V12_TARGET_SOURCE = None


# ------------------------------------------------------------------------------
# Candidate 1 — explicitly created predeclared target object
# ------------------------------------------------------------------------------

target_candidates = [
    "V12_PREDECLARED_TARGETS",
    "V12_TARGETS",
    "V12_TARGET_MAP",
    "V12_PORTFOLIO_TARGETS",
    "V12_EXECUTION_TARGETS",
]


for obj_name in target_candidates:

    if obj_name not in globals():
        continue

    obj = globals()[obj_name]

    # --------------------------------------------------------------------------
    # Dictionary keyed by execution date
    # --------------------------------------------------------------------------

    if isinstance(obj, dict):

        tmp = {}

        success = True

        for k, v in obj.items():

            try:
                dt = pd.Timestamp(k).normalize()
            except Exception:
                success = False
                break

            if isinstance(v, pd.Series):
                v = v.to_dict()

            if not isinstance(v, dict):
                success = False
                break

            tmp[dt] = _normalize_weight_dict(v)

        if success and tmp:

            V12_TARGET_MAP = tmp
            V12_TARGET_SOURCE = obj_name

            break

    # --------------------------------------------------------------------------
    # DataFrame target ledger
    # --------------------------------------------------------------------------

    if isinstance(obj, pd.DataFrame):

        tmp = _targets_from_dataframe(obj)

        if tmp:

            V12_TARGET_MAP = tmp
            V12_TARGET_SOURCE = obj_name

            break


# ==============================================================================
# 4. FALLBACK — RECONSTRUCT TARGETS DIRECTLY FROM THE FROZEN BLOCK-2 STATE PANEL
# ==============================================================================

if V12_TARGET_MAP is None:

    required_state_cols = [
        "Predeclared_TQQQ_Weight",
        "Frozen_Alpha_Available",
    ]

    missing = [
        c for c in required_state_cols
        if c not in STATE.columns
    ]

    if missing:
        raise RuntimeError(
            "Could not locate a frozen V12 target object and "
            f"state-panel fallback is missing: {missing}"
        )


    # --------------------------------------------------------------------------
    # Resolve the exact frozen V8 alpha-sleeve matrix already reconstructed
    # before V12 performance.
    # --------------------------------------------------------------------------

    alpha_matrix_candidates = [
        "V12_FROZEN_ALPHA_MATRIX",
        "V12_ALPHA_SLEEVE_MATRIX",
        "V8Q_WEIGHT_MATRIX",
        "V7V_WEIGHT_MATRIX",
        "V7Q_WEIGHT_MATRIX",
    ]


    alpha_matrix = None
    alpha_matrix_name = None


    for name in alpha_matrix_candidates:

        if (
            name in globals()
            and isinstance(
                globals()[name],
                pd.DataFrame
            )
        ):

            candidate = globals()[name].copy()

            if len(candidate) == N_EVENTS:

                alpha_matrix = candidate
                alpha_matrix_name = name

                break


    # --------------------------------------------------------------------------
    # If the exact matrix is not present, recover it from V8 weight rows.
    # --------------------------------------------------------------------------

    if alpha_matrix is None:

        raise RuntimeError(
            "Frozen V12 target dictionary was not found and no "
            "34-row frozen V7/V8 alpha weight matrix is available."
        )


    alpha_matrix = alpha_matrix.copy()


    # Remove known non-stock/core columns if present.
    drop_cols = [
        c
        for c in alpha_matrix.columns
        if str(c).upper() in {
            "TQQQ",
            "CASH",
            "OTHER",
        }
    ]

    if drop_cols:
        alpha_matrix = alpha_matrix.drop(
            columns=drop_cols
        )


    alpha_matrix.columns = [
        str(c).upper().strip()
        for c in alpha_matrix.columns
    ]


    alpha_matrix = (
        alpha_matrix
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
        .fillna(0.0)
    )


    # Detect whether matrix uses percentage or fraction units.
    row_sums = alpha_matrix.sum(axis=1)

    positive_sums = row_sums[
        row_sums > 0
    ]

    if len(positive_sums):

        median_sum = float(
            positive_sums.median()
        )

        if median_sum > 1.5:
            alpha_matrix = (
                alpha_matrix / 100.0
            )


    V12_TARGET_MAP = {}


    for i, row in STATE.iterrows():

        dt = pd.Timestamp(
            row["Execution_Date"]
        ).normalize()


        tqqq_w = float(
            row["Predeclared_TQQQ_Weight"]
        )

        alpha_w = (
            1.0 - tqqq_w
        )


        if (
            not bool(
                row["Frozen_Alpha_Available"]
            )
            or
            alpha_w <= 0
        ):

            V12_TARGET_MAP[dt] = {
                "TQQQ": 1.0
            }

            continue


        sleeve = (
            alpha_matrix
            .iloc[i]
            .astype(float)
        )

        sleeve = sleeve[
            sleeve > 0
        ]


        if sleeve.empty:

            raise RuntimeError(
                "V12 says frozen alpha is available, "
                f"but the resolved alpha sleeve is empty at {dt.date()}."
            )


        sleeve = (
            sleeve
            /
            float(
                sleeve.sum()
            )
        )


        weights = {
            "TQQQ":
                tqqq_w
        }


        for ticker, sw in sleeve.items():

            weights[
                str(ticker).upper().strip()
            ] = (
                alpha_w
                *
                float(sw)
            )


        V12_TARGET_MAP[dt] = (
            _normalize_weight_dict(
                weights
            )
        )


    V12_TARGET_SOURCE = (
        f"RECONSTRUCTED_FROM_STATE_PANEL+{alpha_matrix_name}"
    )


print(
    f"\n[+] Frozen V12 target source: "
    f"{V12_TARGET_SOURCE}"
)


# ==============================================================================
# 5. ALIGN TARGETS TO THE 34 EXECUTION DATES
# ==============================================================================

execution_dates = [
    pd.Timestamp(x).normalize()
    for x in STATE["Execution_Date"]
]


missing_target_dates = [
    dt
    for dt in execution_dates
    if dt not in V12_TARGET_MAP
]


if missing_target_dates:
    raise RuntimeError(
        "Frozen V12 portfolio targets missing for execution dates: "
        f"{missing_target_dates[:10]}"
    )


TARGETS = {
    dt: _normalize_weight_dict(
        V12_TARGET_MAP[dt]
    )
    for dt in execution_dates
}


for dt, w in TARGETS.items():

    if not w:
        raise RuntimeError(
            f"Empty frozen V12 portfolio on {dt.date()}."
        )

    err = abs(
        sum(w.values())
        - 1.0
    )

    if err > 1e-10:
        raise RuntimeError(
            f"Target weights do not sum to one on {dt.date()}."
        )


# ==============================================================================
# 6. EXACT PRICE LOOKUP
# ==============================================================================

PRICE_MAP = {
    (
        ticker,
        date
    ):
        float(price)

    for ticker, date, price in zip(
        LIFE["Ticker"],
        LIFE["Date"],
        LIFE["Adj_Close"],
    )

    if (
        pd.notna(price)
        and
        np.isfinite(float(price))
        and
        float(price) > 0
    )
}


def exact_price(
    ticker,
    date,
):

    ticker = str(
        ticker
    ).upper().strip()

    date = pd.Timestamp(
        date
    ).normalize()

    value = PRICE_MAP.get(
        (
            ticker,
            date,
        ),
        np.nan
    )

    return float(value)


# ==============================================================================
# 7. EVENT-LEVEL EXACT PRICE PREFLIGHT
# ==============================================================================

price_gaps = []


for i, execution_date in enumerate(
    execution_dates
):

    weights = TARGETS[
        execution_date
    ]


    # Entry quotes must always exist.
    for ticker in weights:

        p = exact_price(
            ticker,
            execution_date,
        )

        if not np.isfinite(p):

            price_gaps.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "ENTRY",

                    "Requested_Date":
                        execution_date,
                }
            )


    # For the final research-date rebalance there is no completed holding period.
    if i == (
        N_EVENTS - 1
    ):
        continue


    exit_date = execution_dates[
        i + 1
    ]


    for ticker in weights:

        p = exact_price(
            ticker,
            exit_date,
        )

        if not np.isfinite(p):

            price_gaps.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "NEXT_REBALANCE",

                    "Requested_Date":
                        exit_date,
                }
            )


V12_EVENT_PRICE_GAPS = (
    pd.DataFrame(
        price_gaps
    )
)


print(
    "\n1) EXACT EXECUTION-TO-EXECUTION PRICE PREFLIGHT"
)


if len(
    V12_EVENT_PRICE_GAPS
) == 0:

    print(
        "[+] PASS — all economically required "
        "entry and next-rebalance prices are exact."
    )

else:

    display(
        V12_EVENT_PRICE_GAPS
    )

    raise RuntimeError(
        "Economically required execution/rebalance quote is missing. "
        "V12 economic test cannot continue."
    )


# ==============================================================================
# 8. TRANSACTION COST CONFIGURATION
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


# We do NOT invent a new market-impact model here.
# If the frozen V12 Block-2 target construction already included estimated
# impact in allocation decisions, that information remains untouched.
#
# For realized portfolio wealth we apply the frozen linear TCA rule used by
# the V7/V8 research infrastructure.
#
# This is deliberately explicit and reproducible.


# ==============================================================================
# 9. WEIGHT DRIFT FUNCTION
# ==============================================================================

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
                "Exact drift price missing for "
                f"{ticker}: {start_date.date()} -> {end_date.date()}."
            )

        values[ticker] = (
            float(weight)
            *
            p1
            /
            p0
        )


    total = float(
        sum(
            values.values()
        )
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
        ticker:
            value / total

        for ticker, value
        in values.items()
    }


# ==============================================================================
# 10. TURNOVER FUNCTION
# ==============================================================================

def l1_turnover(
    old_weights,
    new_weights,
):

    tickers = (
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

            for t in tickers
        )
    )


# ==============================================================================
# 11. EXACT EVENT WALK-FORWARD
# ==============================================================================

wealth = 1.0

previous_drifted = {}

event_rows = []


for i, execution_date in enumerate(
    execution_dates
):

    target = TARGETS[
        execution_date
    ]


    turnover = l1_turnover(
        previous_drifted,
        target,
    )


    tca_rate = (
        BASE_TCA_RATE
        *
        turnover
    )


    # --------------------------------------------------------------------------
    # Final research-date target:
    # include the cost of reaching the final target but no future return.
    # --------------------------------------------------------------------------

    if i == (
        N_EVENTS - 1
    ):

        gross_return = 0.0

        net_return = (
            -tca_rate
        )

        wealth *= (
            1.0
            +
            net_return
        )


        event_rows.append(
            {
                "Event":
                    i + 1,

                "Signal_Date":
                    STATE.loc[
                        i,
                        "Signal_Date"
                    ],

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    execution_date,

                "Held_Names":
                    len(target),

                "TQQQ_Target_Weight":
                    float(
                        target.get(
                            "TQQQ",
                            0.0
                        )
                    ),

                "Alpha_Target_Weight":
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
                    tca_rate,

                "Gross_Return":
                    gross_return,

                "Net_Return":
                    net_return,

                "End_Wealth":
                    wealth,
            }
        )


        previous_drifted = (
            target.copy()
        )

        continue


    exit_date = execution_dates[
        i + 1
    ]


    gross_growth = 0.0


    for ticker, weight in target.items():

        p0 = exact_price(
            ticker,
            execution_date,
        )

        p1 = exact_price(
            ticker,
            exit_date,
        )


        asset_growth = (
            p1
            /
            p0
        )


        gross_growth += (
            float(weight)
            *
            asset_growth
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
            tca_rate
        )
    )


    net_return = (
        net_growth
        -
        1.0
    )


    wealth *= net_growth


    previous_drifted = drift_weights_exact(
        target,
        execution_date,
        exit_date,
    )


    event_rows.append(
        {
            "Event":
                i + 1,

            "Signal_Date":
                STATE.loc[
                    i,
                    "Signal_Date"
                ],

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Held_Names":
                len(target),

            "TQQQ_Target_Weight":
                float(
                    target.get(
                        "TQQQ",
                        0.0
                    )
                ),

            "Alpha_Target_Weight":
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
                tca_rate,

            "Gross_Return":
                gross_return,

            "Net_Return":
                net_return,

            "End_Wealth":
                wealth,
        }
    )


V12_EVENT_PATH = pd.DataFrame(
    event_rows
)


# ==============================================================================
# 12. SAME-CALENDAR TQQQ BENCHMARK
# ==============================================================================

tqqq_wealth = 1.0

tqqq_rows = []

previous_tqqq_weight = 0.0


for i, execution_date in enumerate(
    execution_dates
):

    # Initial purchase only.
    turnover = (
        1.0
        if i == 0
        else 0.0
    )


    cost_rate = (
        BASE_TCA_RATE
        *
        turnover
    )


    if i == (
        N_EVENTS - 1
    ):

        gross_return = 0.0

        net_return = (
            -cost_rate
        )

        tqqq_wealth *= (
            1.0
            +
            net_return
        )


        tqqq_rows.append(
            {
                "Event":
                    i + 1,

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    execution_date,

                "Gross_Return":
                    gross_return,

                "Net_Return":
                    net_return,

                "End_Wealth":
                    tqqq_wealth,
            }
        )

        continue


    exit_date = execution_dates[
        i + 1
    ]


    p0 = exact_price(
        "TQQQ",
        execution_date,
    )

    p1 = exact_price(
        "TQQQ",
        exit_date,
    )


    if (
        not np.isfinite(p0)
        or
        not np.isfinite(p1)
    ):
        raise RuntimeError(
            "Exact TQQQ benchmark price missing."
        )


    gross_growth = (
        p1
        /
        p0
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


    gross_return = (
        gross_growth
        -
        1.0
    )

    net_return = (
        net_growth
        -
        1.0
    )


    tqqq_wealth *= (
        net_growth
    )


    tqqq_rows.append(
        {
            "Event":
                i + 1,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Gross_Return":
                gross_return,

            "Net_Return":
                net_return,

            "End_Wealth":
                tqqq_wealth,
        }
    )


V12_TQQQ_EVENT_PATH = pd.DataFrame(
    tqqq_rows
)


# ==============================================================================
# 13. EVENT-LEVEL EXACT VALIDATION
# ==============================================================================

V12_FINAL_WEALTH = float(
    V12_EVENT_PATH[
        "End_Wealth"
    ].iloc[-1]
)

V12_TQQQ_FINAL_WEALTH = float(
    V12_TQQQ_EVENT_PATH[
        "End_Wealth"
    ].iloc[-1]
)


V12_NET_RETURN_PCT = (
    100.0
    *
    (
        V12_FINAL_WEALTH
        -
        1.0
    )
)


V12_TQQQ_NET_RETURN_PCT = (
    100.0
    *
    (
        V12_TQQQ_FINAL_WEALTH
        -
        1.0
    )
)


V12_MINUS_TQQQ_PP = (
    V12_NET_RETURN_PCT
    -
    V12_TQQQ_NET_RETURN_PCT
)


V12_RELATIVE_WEALTH = (
    V12_FINAL_WEALTH
    /
    V12_TQQQ_FINAL_WEALTH
)


# ==============================================================================
# 14. EVENT-LEVEL RELATIVE PERFORMANCE
# ==============================================================================

V12_EVENT_PATH[
    "TQQQ_Net_Return"
] = V12_TQQQ_EVENT_PATH[
    "Net_Return"
].values


V12_EVENT_PATH[
    "Net_Excess_pp"
] = (
    100.0
    *
    (
        V12_EVENT_PATH[
            "Net_Return"
        ]
        -
        V12_EVENT_PATH[
            "TQQQ_Net_Return"
        ]
    )
)


completed = (
    V12_EVENT_PATH[
        "Exit_Date"
    ]
    >
    V12_EVENT_PATH[
        "Execution_Date"
    ]
)


V12_COMPLETED_EVENTS = (
    V12_EVENT_PATH.loc[
        completed
    ]
    .copy()
)


V12_EVENT_BEAT_RATE = (
    100.0
    *
    (
        V12_COMPLETED_EVENTS[
            "Net_Excess_pp"
        ]
        >
        0
    )
    .mean()
)


V12_MEAN_EVENT_EXCESS_PP = float(
    V12_COMPLETED_EVENTS[
        "Net_Excess_pp"
    ].mean()
)


V12_MEDIAN_EVENT_EXCESS_PP = float(
    V12_COMPLETED_EVENTS[
        "Net_Excess_pp"
    ].median()
)


# ==============================================================================
# 15. COARSE ROBUSTNESS FROM EXACT COMPLETED EVENT PATH
# ==============================================================================

# This does NOT pretend that 1D/1W daily windows are available.
# It reports exact trailing performance over completed rebalance periods only.

robustness_rows = []


completed_indices = list(
    V12_COMPLETED_EVENTS.index
)


for n_events in [
    1,
    3,
    6,
    12,
]:

    if len(
        V12_COMPLETED_EVENTS
    ) < n_events:
        continue


    tail_v12 = (
        V12_COMPLETED_EVENTS
        .iloc[
            -n_events:
        ]
    )


    tail_tqqq = (
        V12_TQQQ_EVENT_PATH
        .iloc[
            tail_v12.index
        ]
    )


    v12_growth = float(
        np.prod(
            1.0
            +
            tail_v12[
                "Net_Return"
            ].values
        )
    )


    tq_growth = float(
        np.prod(
            1.0
            +
            tail_tqqq[
                "Net_Return"
            ].values
        )
    )


    robustness_rows.append(
        {
            "Completed_Rebalance_Periods":
                n_events,

            "V12_Return_Pct":
                100.0
                *
                (
                    v12_growth
                    -
                    1.0
                ),

            "TQQQ_Return_Pct":
                100.0
                *
                (
                    tq_growth
                    -
                    1.0
                ),

            "V12_Minus_TQQQ_pp":
                100.0
                *
                (
                    v12_growth
                    -
                    tq_growth
                ),

            "V12_Beats_TQQQ":
                bool(
                    v12_growth
                    >
                    tq_growth
                ),
        }
    )


V12_EVENT_ROBUSTNESS = pd.DataFrame(
    robustness_rows
)


# ==============================================================================
# 16. OPTIONAL DAILY NAV DIAGNOSTIC
# ==============================================================================

# We explicitly DO NOT fabricate missing intermediate daily prices.
#
# The daily NAV therefore remains a diagnostic availability flag.
#
# Economic performance above is exact because every entry and exit quote
# has already passed exact-price preflight.


all_daily_complete = True

daily_gap_rows = []


# Use TQQQ's own dates as the research trading calendar.
tqqq_calendar = (
    LIFE.loc[
        LIFE["Ticker"] == "TQQQ",
        "Date",
    ]
    .drop_duplicates()
    .sort_values()
)


research_start = execution_dates[0]
research_end   = execution_dates[-1]


research_calendar = pd.DatetimeIndex(
    tqqq_calendar[
        (tqqq_calendar >= research_start)
        &
        (tqqq_calendar <= research_end)
    ]
)


for i in range(
    N_EVENTS - 1
):

    start = execution_dates[i]
    end   = execution_dates[i + 1]

    target = TARGETS[start]


    required_dates = research_calendar[
        (research_calendar >= start)
        &
        (research_calendar <= end)
    ]


    for ticker in target:

        ticker_dates = set(
            LIFE.loc[
                (
                    LIFE["Ticker"] == ticker
                )
                &
                (
                    LIFE["Adj_Close"].notna()
                ),
                "Date",
            ]
        )


        missing_days = [
            d
            for d in required_dates
            if d not in ticker_dates
        ]


        if missing_days:

            all_daily_complete = False

            daily_gap_rows.append(
                {
                    "Execution_Date":
                        start,

                    "Ticker":
                        ticker,

                    "Missing_Days":
                        len(
                            missing_days
                        ),

                    "First_Missing_Date":
                        min(
                            missing_days
                        ),

                    "Last_Missing_Date":
                        max(
                            missing_days
                        ),
                }
            )


V12_DAILY_NAV_EXACT = bool(
    all_daily_complete
)


V12_DAILY_PRICE_DIAGNOSTIC = pd.DataFrame(
    daily_gap_rows
)


# ==============================================================================
# 17. ECONOMIC RESULT
# ==============================================================================

summary = pd.DataFrame(
    [
        (
            "Research decisions",
            N_EVENTS
        ),

        (
            "Completed holding periods",
            len(
                V12_COMPLETED_EVENTS
            )
        ),

        (
            "V12 final wealth",
            V12_FINAL_WEALTH
        ),

        (
            "V12 net return pct",
            V12_NET_RETURN_PCT
        ),

        (
            "TQQQ final wealth",
            V12_TQQQ_FINAL_WEALTH
        ),

        (
            "TQQQ net return pct",
            V12_TQQQ_NET_RETURN_PCT
        ),

        (
            "V12 minus TQQQ pp",
            V12_MINUS_TQQQ_PP
        ),

        (
            "V12 / TQQQ relative wealth",
            V12_RELATIVE_WEALTH
        ),

        (
            "V12 event beat rate pct",
            V12_EVENT_BEAT_RATE
        ),

        (
            "Mean event excess pp",
            V12_MEAN_EVENT_EXCESS_PP
        ),

        (
            "Median event excess pp",
            V12_MEDIAN_EVENT_EXCESS_PP
        ),

        (
            "Total turnover",
            float(
                V12_EVENT_PATH[
                    "Turnover"
                ].sum()
            )
        ),

        (
            "Mean TQQQ target weight pct",
            100.0
            *
            float(
                V12_EVENT_PATH[
                    "TQQQ_Target_Weight"
                ].mean()
            )
        ),

        (
            "Mean Alpha target weight pct",
            100.0
            *
            float(
                V12_EVENT_PATH[
                    "Alpha_Target_Weight"
                ].mean()
            )
        ),

        (
            "Exact execution/rebalance pricing",
            True
        ),

        (
            "Exact daily NAV available",
            V12_DAILY_NAV_EXACT
        ),
    ],
    columns=[
        "Metric",
        "Value",
    ]
)


print(
    "\n2) V12 FINAL ECONOMIC RESULT"
)

display(
    summary
)


print(
    "\n3) LAST 10 EXACT EVENTS"
)

display(
    V12_EVENT_PATH.tail(
        10
    )
)


print(
    "\n4) EXACT EVENT-LEVEL ROBUSTNESS"
)

display(
    V12_EVENT_ROBUSTNESS
)


# ==============================================================================
# 18. DAILY PRICE DIAGNOSTIC
# ==============================================================================

print(
    "\n5) DAILY NAV DATA-QUALITY DIAGNOSTIC"
)


if V12_DAILY_NAV_EXACT:

    print(
        "[+] All held-period daily observations are available."
    )

else:

    print(
        "[!] Exact daily NAV cannot be reconstructed for every single day."
    )

    print(
        "[+] This does NOT affect the exact execution-to-execution "
        "economic result above."
    )

    print(
        "[+] No interpolation or forward fill was used."
    )

    display(
        V12_DAILY_PRICE_DIAGNOSTIC
    )


# ==============================================================================
# 19. PRIMARY RESEARCH VERDICT
# ==============================================================================

V12_BEATS_TQQQ = bool(
    V12_FINAL_WEALTH
    >
    V12_TQQQ_FINAL_WEALTH
)


if V12_BEATS_TQQQ:

    V12_RESEARCH_VERDICT = (
        "PASS_TERMINAL_WEALTH"
    )

else:

    V12_RESEARCH_VERDICT = (
        "FAIL"
    )


print(
    "\n6) PRIMARY RESEARCH VERDICT"
)

print(
    f"V12 beats TQQQ full history : "
    f"{V12_BEATS_TQQQ}"
)

print(
    f"V12 result                  : "
    f"{V12_RESEARCH_VERDICT}"
)


# ==============================================================================
# 20. FINAL EXECUTED TARGET
# ==============================================================================

final_date = execution_dates[
    -1
]

final_target = TARGETS[
    final_date
]


V12_FINAL_TARGET = (
    pd.Series(
        final_target,
        name="Weight"
    )
    .sort_values(
        ascending=False
    )
)


print(
    "\n7) FINAL PREDECLARED V12 TARGET"
)

print(
    f"Execution date: "
    f"{final_date.date()}"
)


display(
    (
        100.0
        *
        V12_FINAL_TARGET
    )
    .rename(
        "Weight_Pct"
    )
    .to_frame()
)


# ==============================================================================
# 21. RESEARCH FINGERPRINT
# ==============================================================================

fingerprint_payload = {
    "version":
        "V12_BLOCK_3_R",

    "target_source":
        str(
            V12_TARGET_SOURCE
        ),

    "events":
        int(
            N_EVENTS
        ),

    "base_tca_bps":
        float(
            BASE_TCA_BPS
        ),

    "final_wealth":
        round(
            V12_FINAL_WEALTH,
            12
        ),

    "tqqq_final_wealth":
        round(
            V12_TQQQ_FINAL_WEALTH,
            12
        ),

    "daily_nav_exact":
        bool(
            V12_DAILY_NAV_EXACT
        ),
}


V12_BLOCK3R_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            sort_keys=True,
            default=str,
        )
        .encode()
    )
    .hexdigest()
)


print(
    "\n8) V12 BLOCK 3-R RESEARCH FINGERPRINT"
)

print(
    V12_BLOCK3R_FINGERPRINT
)


# ==============================================================================
# 22. INTEGRITY
# ==============================================================================

print(
    "\nINTEGRITY:"
)

print(
    "[+] Frozen V12 Block-2 allocations were used."
)

print(
    "[+] No model was fitted."
)

print(
    "[+] No stock-selection rule was changed."
)

print(
    "[+] No V12 parameter was tuned."
)

print(
    "[+] No missing intermediate daily price was interpolated."
)

print(
    "[+] No missing intermediate daily price was forward-filled."
)

print(
    "[+] Every economically required entry quote is exact."
)

print(
    "[+] Every completed holding-period exit quote is exact."
)

print(
    "[+] Terminal wealth is independent of missing intermediate daily marks."
)

print(
    "[+] Daily NAV completeness is reported separately as a diagnostic."
)


print(
    "\nDECISION:"
)

if V12_BEATS_TQQQ:

    print(
        "[+] V12 beats TQQQ on exact net terminal wealth."
    )

    print(
        "[+] Stop here and inspect the result before any freeze/OOS decision."
    )

else:

    print(
        "[-] V12 does not beat TQQQ on exact net terminal wealth."
    )

    print(
        "[-] Reject V12 as designed. Do not retune V12."
    )

    print(
        "[+] Next generation, if pursued, is V13 based on frozen V8 economics."
    )


print("=" * 140)
restored_register('V12', V12_FINAL_WEALTH, V12_EVENT_PATH, 'End_Wealth', 'Close / V12 original multiplicative costs', 'Historically rejected')
