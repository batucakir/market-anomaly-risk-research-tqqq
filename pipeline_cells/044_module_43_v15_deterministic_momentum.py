# MODULE 43 — V15 DETERMINISTIC MOMENTUM
# Run in the same notebook, in module order.

# =============================================================================
# V15 — ONE-SHOT DETERMINISTIC TQQQ-RELATIVE MOMENTUM CHALLENGER
#
# ARCHITECTURE
#   - Frozen PIT stock universe / existing liquidity eligibility
#   - 1M / 3M / 6M / 12M TQQQ-relative momentum
#   - Cross-sectional percentile ranks
#   - Composite = median of four horizon ranks
#   - Positive relative-momentum requirement
#   - Continuous rank-edge stock weights
#   - TQQQ core
#   - Cover-style universal constant-mix allocator
#   - 1001-point numerical integration grid
#   - Uniform prior
#   - Strict causal one-event posterior update
#   - 2 bps linear L1 transaction cost
#
# NO:
#   - model fitting
#   - parameter search
#   - Top-K
#   - minimum stock weight
#   - maximum stock weight
#   - sector cap
#   - risk cap
#   - TQQQ floor
#   - alpha cap
#   - strategic cash
#   - leverage above 100%
#
# PRIMARY TEST:
#   V15 vs repaired-ledger V8 champion vs TQQQ
#
# IMPORTANT:
#   The strategy specification is frozen BEFORE performance is calculated.
# =============================================================================

import hashlib
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# 0. CONSTANTS — PREDECLARED
# =============================================================================

V15_VERSION = "V15"

V15_MOMENTUM_HORIZONS = {
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252,
}

V15_RANK_BREAK_EVEN = 0.50

V15_GRID = np.linspace(
    0.0,
    1.0,
    1001,
)

V15_TCA_BPS = 2.0
V15_TCA_RATE = V15_TCA_BPS / 10000.0

V15_REFERENCE_AUM_USD = 100000.0

V15_SPEC = {
    "version": V15_VERSION,
    "objective": "MAX_NET_TERMINAL_WEALTH_RELATIVE_TO_V8_AND_TQQQ",
    "benchmark_1": "V8_REACCOUNTED_CHAMPION",
    "benchmark_2": "TQQQ",
    "stock_universe": "FROZEN_EXISTING_PIT_ELIGIBLE_STOCK_UNIVERSE",
    "liquidity_rule": "PRESERVE_EXISTING_ELIGIBILITY",
    "signal_execution": "SIGNAL_CLOSE_T__EXECUTE_CLOSE_T_PLUS_1",
    "momentum_horizons": V15_MOMENTUM_HORIZONS,
    "relative_momentum": "LOG_RETURN_STOCK_MINUS_LOG_RETURN_TQQQ",
    "cross_sectional_transform": "PERCENTILE_RANK",
    "horizon_aggregation": "MEDIAN",
    "rank_break_even": V15_RANK_BREAK_EVEN,
    "raw_relative_momentum_gate": "MEDIAN_RELATIVE_LOG_MOMENTUM_GT_0",
    "stock_weight_formula": "NORMALIZED_POSITIVE_COMPOSITE_RANK_EDGE",
    "top_k": None,
    "minimum_stock_weight": None,
    "maximum_stock_weight": None,
    "sector_cap": None,
    "risk_cap": None,
    "tqqq_floor": None,
    "alpha_cap": None,
    "cash": False,
    "leverage_above_100pct": False,
    "allocator": "COVER_STYLE_UNIVERSAL_CONSTANT_MIX",
    "universal_grid_points": 1001,
    "universal_prior": "UNIFORM",
    "posterior_update": "AFTER_COMPLETED_EVENT_ONLY",
    "tca_bps": V15_TCA_BPS,
    "tca_formula": "LINEAR_L1_TURNOVER",
    "missing_execution_order": "UNFILLED_WEIGHT_REMAINS_IN_TQQQ",
    "missing_terminal_quote": "LAST_OBSERVABLE_EXACT_QUOTE_THEN_CASH",
    "reference_aum_usd": V15_REFERENCE_AUM_USD,
}

V15_SPEC_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V15_SPEC,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
).hexdigest()

print("=" * 136)
print("V15 — ONE-SHOT DETERMINISTIC TQQQ-RELATIVE MOMENTUM CHALLENGER")
print("TQQQ CORE + RELATIVE-MOMENTUM STOCK SLEEVE + UNIVERSAL ALLOCATOR")
print("=" * 136)

print(
    "\nV15 specification fingerprint:",
    V15_SPEC_FINGERPRINT,
)


# =============================================================================
# 1. HELPER FUNCTIONS
# =============================================================================

def v15_flat_col(x):
    if isinstance(x, tuple):
        parts = [
            str(y)
            for y in x
            if str(y).lower()
            not in ("", "none", "nan")
        ]
        return "_".join(parts)

    return str(x)


def v15_norm_col(x):
    return "".join(
        ch.lower()
        for ch in str(x)
        if ch.isalnum()
    )


def v15_normalize_ticker(x):
    return (
        str(x)
        .strip()
        .upper()
        .replace(".", "-")
    )


def v15_prepare_sample(df):
    out = (
        df
        .head(300)
        .reset_index()
        .copy()
    )

    out.columns = [
        v15_flat_col(c)
        for c in out.columns
    ]

    return out


def v15_find_column(
    df,
    candidates,
):
    norm_map = {
        v15_norm_col(c): c
        for c in df.columns
    }

    for candidate in candidates:
        key = v15_norm_col(candidate)

        if key in norm_map:
            return norm_map[key]

    return None


def v15_find_date_column(df):
    col = v15_find_column(
        df,
        [
            "Date",
            "Trading_Date",
            "Market_Date",
            "Price_Date",
            "Session_Date",
            "Signal_Date",
        ],
    )

    if col is not None:
        return col

    for c in df.columns:
        s = df[c]

        if pd.api.types.is_datetime64_any_dtype(s):
            return c

    return None


def v15_find_ticker_column(df):
    return v15_find_column(
        df,
        [
            "Ticker",
            "Symbol",
            "Yahoo_Ticker",
            "Asset",
        ],
    )


def v15_find_price_column(df):
    return v15_find_column(
        df,
        [
            "Adj_Close",
            "Adj Close",
            "Adjusted_Close",
            "Adjusted Close",
            "Price",
            "Close",
        ],
    )


def v15_truthy(series):
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    if pd.api.types.is_numeric_dtype(series):
        return (
            pd.to_numeric(
                series,
                errors="coerce",
            )
            .fillna(0)
            .astype(float)
            > 0
        )

    return (
        series
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(
            [
                "TRUE",
                "1",
                "YES",
                "Y",
                "ELIGIBLE",
            ]
        )
    )


def v15_dict_turnover(
    target,
    previous,
):
    keys = (
        set(target.keys())
        |
        set(previous.keys())
    )

    return float(
        sum(
            abs(
                float(target.get(k, 0.0))
                -
                float(previous.get(k, 0.0))
            )
            for k in keys
        )
    )


def v15_series_return_pct(series):
    arr = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .dropna()
        .astype(float)
        .values
    )

    if len(arr) == 0:
        return np.nan

    return float(
        (
            np.prod(
                1.0
                +
                arr / 100.0
            )
            -
            1.0
        )
        *
        100.0
    )


# =============================================================================
# 2. REQUIRED COMPARISON TABLE
# =============================================================================

if (
    "event_compare"
    not in globals()
):
    raise RuntimeError(
        "V15 requires the previously verified "
        "`event_compare` table."
    )

V15_COMPARE = (
    event_compare
    .copy()
    .reset_index(drop=True)
)

required_compare_cols = [
    "Execution_Date",
    "Exit_Date",
    "V8_Return_Pct",
    "TQQQ_Return_Pct",
]

missing_compare_cols = [
    c
    for c in required_compare_cols
    if c
    not in V15_COMPARE.columns
]

if missing_compare_cols:
    raise RuntimeError(
        "event_compare is missing required columns: "
        f"{missing_compare_cols}"
    )

V15_COMPARE[
    "Execution_Date"
] = pd.to_datetime(
    V15_COMPARE[
        "Execution_Date"
    ]
).dt.normalize()

V15_COMPARE[
    "Exit_Date"
] = pd.to_datetime(
    V15_COMPARE[
        "Exit_Date"
    ]
).dt.normalize()

V15_COMPARE = (
    V15_COMPARE[
        V15_COMPARE[
            "Execution_Date"
        ].notna()
        &
        V15_COMPARE[
            "Exit_Date"
        ].notna()
        &
        (
            V15_COMPARE[
                "Exit_Date"
            ]
            >
            V15_COMPARE[
                "Execution_Date"
            ]
        )
    ]
    .sort_values(
        "Execution_Date"
    )
    .reset_index(drop=True)
)

if len(V15_COMPARE) == 0:
    raise RuntimeError(
        "No completed holding periods "
        "were found in event_compare."
    )

print(
    "\n[+] Completed holding periods:",
    len(V15_COMPARE),
)


# =============================================================================
# 3. RESOLVE FROZEN PIT ELIGIBILITY PANEL
# =============================================================================

V15_ELIGIBILITY_SOURCE_NAME = None
V15_ELIGIBILITY_SOURCE = None

preferred_eligibility_objects = [
    "V4_DAILY_PANEL",
    "V9_MODEL_PANEL",
]

for object_name in preferred_eligibility_objects:

    obj = globals().get(
        object_name,
        None,
    )

    if not isinstance(
        obj,
        pd.DataFrame,
    ):
        continue

    sample = v15_prepare_sample(
        obj
    )

    date_col = v15_find_date_column(
        sample
    )

    ticker_col = v15_find_ticker_column(
        sample
    )

    eligible_col = v15_find_column(
        sample,
        [
            "Eligible",
            "Is_Eligible",
            "PIT_Eligible",
        ],
    )

    if (
        date_col is not None
        and
        ticker_col is not None
        and
        eligible_col is not None
    ):
        V15_ELIGIBILITY_SOURCE_NAME = (
            object_name
        )

        V15_ELIGIBILITY_SOURCE = obj

        break


if V15_ELIGIBILITY_SOURCE is None:

    best_score = -np.inf

    for object_name, obj in list(
        globals().items()
    ):

        if not isinstance(
            obj,
            pd.DataFrame,
        ):
            continue

        if len(obj) < 10000:
            continue

        try:
            sample = (
                v15_prepare_sample(
                    obj
                )
            )
        except Exception:
            continue

        date_col = (
            v15_find_date_column(
                sample
            )
        )

        ticker_col = (
            v15_find_ticker_column(
                sample
            )
        )

        eligible_col = (
            v15_find_column(
                sample,
                [
                    "Eligible",
                    "Is_Eligible",
                    "PIT_Eligible",
                ],
            )
        )

        if (
            date_col is None
            or
            ticker_col is None
            or
            eligible_col is None
        ):
            continue

        score = math.log1p(
            len(obj)
        )

        name_upper = (
            object_name.upper()
        )

        if "PIT" in name_upper:
            score += 5.0

        if "DAILY" in name_upper:
            score += 3.0

        if score > best_score:
            best_score = score

            V15_ELIGIBILITY_SOURCE_NAME = (
                object_name
            )

            V15_ELIGIBILITY_SOURCE = obj


if V15_ELIGIBILITY_SOURCE is None:
    raise RuntimeError(
        "Could not locate a frozen PIT "
        "eligibility panel."
    )


V15_ELIG = (
    V15_ELIGIBILITY_SOURCE
    .reset_index()
    .copy()
)

V15_ELIG.columns = [
    v15_flat_col(c)
    for c in V15_ELIG.columns
]

V15_ELIG_DATE_COL = (
    v15_find_date_column(
        V15_ELIG
    )
)

V15_ELIG_TICKER_COL = (
    v15_find_ticker_column(
        V15_ELIG
    )
)

V15_ELIGIBLE_COL = (
    v15_find_column(
        V15_ELIG,
        [
            "Eligible",
            "Is_Eligible",
            "PIT_Eligible",
        ],
    )
)

V15_ASSET_TYPE_COL = (
    v15_find_column(
        V15_ELIG,
        [
            "Asset_Type",
            "Asset Type",
            "Security_Type",
            "Type",
        ],
    )
)

V15_ELIG[
    V15_ELIG_DATE_COL
] = pd.to_datetime(
    V15_ELIG[
        V15_ELIG_DATE_COL
    ],
    errors="coerce",
).dt.normalize()

V15_ELIG[
    V15_ELIG_TICKER_COL
] = (
    V15_ELIG[
        V15_ELIG_TICKER_COL
    ]
    .map(
        v15_normalize_ticker
    )
)

V15_ELIG = V15_ELIG[
    V15_ELIG[
        V15_ELIG_DATE_COL
    ].notna()
].copy()

V15_ELIG = V15_ELIG[
    v15_truthy(
        V15_ELIG[
            V15_ELIGIBLE_COL
        ]
    )
].copy()

if V15_ASSET_TYPE_COL is not None:

    stock_mask = (
        V15_ELIG[
            V15_ASSET_TYPE_COL
        ]
        .astype(str)
        .str.upper()
        .str.contains(
            "STOCK",
            na=False,
        )
    )

    if stock_mask.any():
        V15_ELIG = (
            V15_ELIG[
                stock_mask
            ]
            .copy()
        )


# =============================================================================
# 4. RESOLVE BEST AVAILABLE LIFECYCLE PRICE LEDGER
# =============================================================================

# The old V15-R2 repair chooses V12_LIFECYCLE first.
V15_PRICE_SOURCE_NAME = 'V12_LIFECYCLE'
V15_PRICE_SOURCE = V12_LIFECYCLE
if not {'Date','Ticker','Adj_Close'}.issubset(V15_PRICE_SOURCE.columns):
    raise RuntimeError('Canonical full V15 lifecycle ledger is incomplete.')

V15_PRICE = (
    V15_PRICE_SOURCE
    .reset_index()
    .copy()
)

V15_PRICE.columns = [
    v15_flat_col(c)
    for c in V15_PRICE.columns
]

V15_PRICE_DATE_COL = (
    v15_find_date_column(
        V15_PRICE
    )
)

V15_PRICE_TICKER_COL = (
    v15_find_ticker_column(
        V15_PRICE
    )
)

V15_PRICE_VALUE_COL = (
    v15_find_price_column(
        V15_PRICE
    )
)

V15_PRICE[
    V15_PRICE_DATE_COL
] = pd.to_datetime(
    V15_PRICE[
        V15_PRICE_DATE_COL
    ],
    errors="coerce",
).dt.normalize()

V15_PRICE[
    V15_PRICE_TICKER_COL
] = (
    V15_PRICE[
        V15_PRICE_TICKER_COL
    ]
    .map(
        v15_normalize_ticker
    )
)

V15_PRICE[
    V15_PRICE_VALUE_COL
] = pd.to_numeric(
    V15_PRICE[
        V15_PRICE_VALUE_COL
    ],
    errors="coerce",
)

V15_PRICE = (
    V15_PRICE[
        V15_PRICE[
            V15_PRICE_DATE_COL
        ].notna()
        &
        V15_PRICE[
            V15_PRICE_TICKER_COL
        ].notna()
        &
        V15_PRICE[
            V15_PRICE_VALUE_COL
        ].notna()
        &
        (
            V15_PRICE[
                V15_PRICE_VALUE_COL
            ]
            >
            0
        )
    ][
        [
            V15_PRICE_DATE_COL,
            V15_PRICE_TICKER_COL,
            V15_PRICE_VALUE_COL,
        ]
    ]
    .drop_duplicates(
        subset=[
            V15_PRICE_DATE_COL,
            V15_PRICE_TICKER_COL,
        ],
        keep="last",
    )
)

V15_PRICE_WIDE = (
    V15_PRICE
    .pivot(
        index=V15_PRICE_DATE_COL,
        columns=V15_PRICE_TICKER_COL,
        values=V15_PRICE_VALUE_COL,
    )
    .sort_index()
)

if (
    "TQQQ"
    not in V15_PRICE_WIDE.columns
):
    raise RuntimeError(
        "TQQQ is missing from the selected "
        "daily price ledger."
    )


V15_TQQQ_CALENDAR = (
    V15_PRICE_WIDE[
        "TQQQ"
    ]
    .dropna()
    .index
    .sort_values()
)


# =============================================================================
# 5. DATA SOURCE AUDIT
# =============================================================================

print(
    "\n[+] Frozen PIT eligibility source :",
    V15_ELIGIBILITY_SOURCE_NAME,
)

print(
    "[+] Lifecycle price source       :",
    V15_PRICE_SOURCE_NAME,
)

print(
    "[+] Price rows                   :",
    f"{len(V15_PRICE):,}",
)

print(
    "[+] Price tickers                :",
    f"{V15_PRICE[V15_PRICE_TICKER_COL].nunique():,}",
)

print(
    "[+] TQQQ trading sessions        :",
    f"{len(V15_TQQQ_CALENDAR):,}",
)


# =============================================================================
# 6. SIGNAL DATE RECONSTRUCTION
# =============================================================================

def v15_previous_tqqq_session(
    execution_date,
):

    execution_date = pd.Timestamp(
        execution_date
    ).normalize()

    loc = V15_TQQQ_CALENDAR.searchsorted(
        execution_date,
        side="left",
    )

    if loc <= 0:
        raise RuntimeError(
            f"No prior TQQQ trading session "
            f"before {execution_date.date()}."
        )

    return pd.Timestamp(
        V15_TQQQ_CALENDAR[
            loc - 1
        ]
    ).normalize()


V15_COMPARE[
    "Signal_Date"
] = V15_COMPARE[
    "Execution_Date"
].map(
    v15_previous_tqqq_session
)

if not (
    V15_COMPARE[
        "Signal_Date"
    ]
    <
    V15_COMPARE[
        "Execution_Date"
    ]
).all():
    raise RuntimeError(
        "Signal/execution causality check failed."
    )


# =============================================================================
# 7. ELIGIBLE STOCK LOOKUP
# =============================================================================

V15_ELIG_DATES = np.sort(
    V15_ELIG[
        V15_ELIG_DATE_COL
    ]
    .dropna()
    .unique()
)


def v15_eligible_stocks(
    signal_date,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()

    loc = np.searchsorted(
        V15_ELIG_DATES,
        np.datetime64(
            signal_date
        ),
        side="right",
    ) - 1

    if loc < 0:
        raise RuntimeError(
            f"No causal PIT eligibility snapshot "
            f"exists on or before {signal_date.date()}."
        )

    used_date = pd.Timestamp(
        V15_ELIG_DATES[
            loc
        ]
    ).normalize()

    rows = V15_ELIG[
        V15_ELIG[
            V15_ELIG_DATE_COL
        ]
        ==
        used_date
    ]

    tickers = (
        rows[
            V15_ELIG_TICKER_COL
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    tickers = [
        x
        for x in tickers
        if (
            x != "TQQQ"
            and
            x in V15_PRICE_WIDE.columns
        )
    ]

    return (
        used_date,
        tickers,
    )


# =============================================================================
# 8. MOMENTUM SLEEVE CONSTRUCTION
# =============================================================================

def v15_calendar_lag_date(
    signal_date,
    sessions,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()

    loc = V15_TQQQ_CALENDAR.searchsorted(
        signal_date,
        side="right",
    ) - 1

    if loc < 0:
        return None

    lag_loc = (
        loc
        -
        int(sessions)
    )

    if lag_loc < 0:
        return None

    return pd.Timestamp(
        V15_TQQQ_CALENDAR[
            lag_loc
        ]
    ).normalize()


def v15_build_sleeve(
    signal_date,
    execution_date,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()

    execution_date = pd.Timestamp(
        execution_date
    ).normalize()

    eligibility_date, tickers = (
        v15_eligible_stocks(
            signal_date
        )
    )

    if len(tickers) == 0:

        return {
            "Signal_Date": signal_date,
            "Eligibility_Date": eligibility_date,
            "Candidates": 0,
            "Complete_Momentum_Stocks": 0,
            "Positive_Edge_Stocks": 0,
            "Intended_Weights": {},
            "Executable_Weights": {},
            "Unfilled_Sleeve_Mass": 0.0,
            "Composite_Rank_Median": np.nan,
            "Raw_Relative_Momentum_Median": np.nan,
        }

    lag_dates = {}

    for horizon_name, sessions in (
        V15_MOMENTUM_HORIZONS.items()
    ):

        lag_date = (
            v15_calendar_lag_date(
                signal_date,
                sessions,
            )
        )

        if lag_date is None:
            raise RuntimeError(
                f"Insufficient history for "
                f"{horizon_name} at "
                f"{signal_date.date()}."
            )

        lag_dates[
            horizon_name
        ] = lag_date

    needed_dates = [
        signal_date
    ] + list(
        lag_dates.values()
    )

    for date in needed_dates:

        if (
            date
            not in V15_PRICE_WIDE.index
        ):
            raise RuntimeError(
                f"Required market date "
                f"{date.date()} is missing "
                f"from the price ledger."
            )

    if (
        signal_date
        not in V15_PRICE_WIDE.index
    ):
        raise RuntimeError(
            f"Signal date {signal_date.date()} "
            "missing from price ledger."
        )

    tqqq_now = float(
        V15_PRICE_WIDE.loc[
            signal_date,
            "TQQQ",
        ]
    )

    if (
        not np.isfinite(
            tqqq_now
        )
        or
        tqqq_now <= 0
    ):
        raise RuntimeError(
            "Invalid TQQQ signal-date price."
        )

    rel_momentum = {}

    for horizon_name, lag_date in (
        lag_dates.items()
    ):

        tqqq_lag = float(
            V15_PRICE_WIDE.loc[
                lag_date,
                "TQQQ",
            ]
        )

        if (
            not np.isfinite(
                tqqq_lag
            )
            or
            tqqq_lag <= 0
        ):
            raise RuntimeError(
                f"Invalid TQQQ lag price "
                f"for {horizon_name}."
            )

        stock_now = (
            V15_PRICE_WIDE.loc[
                signal_date
            ]
            .reindex(
                tickers
            )
            .astype(float)
        )

        stock_lag = (
            V15_PRICE_WIDE.loc[
                lag_date
            ]
            .reindex(
                tickers
            )
            .astype(float)
        )

        valid = (
            stock_now.notna()
            &
            stock_lag.notna()
            &
            (
                stock_now
                >
                0
            )
            &
            (
                stock_lag
                >
                0
            )
        )

        values = pd.Series(
            np.nan,
            index=tickers,
            dtype=float,
        )

        values.loc[
            valid
        ] = (
            np.log(
                stock_now.loc[
                    valid
                ]
                /
                stock_lag.loc[
                    valid
                ]
            )
            -
            math.log(
                tqqq_now
                /
                tqqq_lag
            )
        )

        rel_momentum[
            horizon_name
        ] = values

    rel_df = pd.DataFrame(
        rel_momentum
    )

    rel_df = rel_df[
        rel_df.notna().all(
            axis=1
        )
    ].copy()

    if len(rel_df) == 0:

        return {
            "Signal_Date": signal_date,
            "Eligibility_Date": eligibility_date,
            "Candidates": len(tickers),
            "Complete_Momentum_Stocks": 0,
            "Positive_Edge_Stocks": 0,
            "Intended_Weights": {},
            "Executable_Weights": {},
            "Unfilled_Sleeve_Mass": 0.0,
            "Composite_Rank_Median": np.nan,
            "Raw_Relative_Momentum_Median": np.nan,
        }

    rank_df = (
        rel_df
        .rank(
            axis=0,
            pct=True,
            method="average",
        )
    )

    composite_rank = (
        rank_df
        .median(
            axis=1
        )
    )

    raw_relative_median = (
        rel_df
        .median(
            axis=1
        )
    )

    positive_mask = (
        (
            composite_rank
            >
            V15_RANK_BREAK_EVEN
        )
        &
        (
            raw_relative_median
            >
            0.0
        )
    )

    rank_edge = (
        composite_rank[
            positive_mask
        ]
        -
        V15_RANK_BREAK_EVEN
    )

    if (
        len(rank_edge) == 0
        or
        float(
            rank_edge.sum()
        )
        <= 0
    ):

        intended_weights = {}

    else:

        intended_weights = (
            rank_edge
            /
            float(
                rank_edge.sum()
            )
        ).to_dict()

    executable_weights = {}
    unfilled_mass = 0.0

    for ticker, weight in (
        intended_weights.items()
    ):

        if (
            execution_date
            in V15_PRICE_WIDE.index
            and
            ticker
            in V15_PRICE_WIDE.columns
        ):

            px = (
                V15_PRICE_WIDE.at[
                    execution_date,
                    ticker,
                ]
            )

        else:
            px = np.nan

        if (
            np.isfinite(
                px
            )
            and
            float(px) > 0
        ):
            executable_weights[
                ticker
            ] = float(
                weight
            )

        else:
            # Causal execution-day fallback:
            # the unfilled order remains in TQQQ.
            unfilled_mass += float(
                weight
            )

    return {
        "Signal_Date": signal_date,
        "Eligibility_Date": eligibility_date,
        "Candidates": len(tickers),
        "Complete_Momentum_Stocks": len(rel_df),
        "Positive_Edge_Stocks": len(intended_weights),
        "Intended_Weights": intended_weights,
        "Executable_Weights": executable_weights,
        "Unfilled_Sleeve_Mass": float(unfilled_mass),
        "Composite_Rank_Median": float(
            composite_rank.median()
        ),
        "Raw_Relative_Momentum_Median": float(
            raw_relative_median.median()
        ),
    }


# =============================================================================
# 9. BUILD ALL SIGNAL-DATE SLEEVES BEFORE PERFORMANCE
# =============================================================================

V15_SLEEVES = []
V15_SLEEVE_AUDIT_ROWS = []

for event_id, row in (
    V15_COMPARE.iterrows()
):

    sleeve = v15_build_sleeve(
        row[
            "Signal_Date"
        ],
        row[
            "Execution_Date"
        ],
    )

    V15_SLEEVES.append(
        sleeve
    )

    V15_SLEEVE_AUDIT_ROWS.append(
        {
            "Event": event_id + 1,
            "Signal_Date": sleeve[
                "Signal_Date"
            ],
            "Execution_Date": row[
                "Execution_Date"
            ],
            "Eligibility_Date": sleeve[
                "Eligibility_Date"
            ],
            "Candidates": sleeve[
                "Candidates"
            ],
            "Complete_Momentum_Stocks": sleeve[
                "Complete_Momentum_Stocks"
            ],
            "Positive_Edge_Stocks": sleeve[
                "Positive_Edge_Stocks"
            ],
            "Executable_Stocks": len(
                sleeve[
                    "Executable_Weights"
                ]
            ),
            "Unfilled_Sleeve_Mass_Pct":
                100.0
                *
                sleeve[
                    "Unfilled_Sleeve_Mass"
                ],
            "Composite_Rank_Median":
                sleeve[
                    "Composite_Rank_Median"
                ],
            "Median_Relative_Log_Momentum":
                sleeve[
                    "Raw_Relative_Momentum_Median"
                ],
        }
    )

V15_SLEEVE_AUDIT = pd.DataFrame(
    V15_SLEEVE_AUDIT_ROWS
)

print(
    "\n1) V15 PRE-PERFORMANCE STOCK-SLEEVE AUDIT"
)

display(
    V15_SLEEVE_AUDIT
)

print(
    "\n[+] ALL V15 STOCK SLEEVES WERE "
    "DEFINED BEFORE PERFORMANCE."
)


# =============================================================================
# 10. FREEZE SLEEVE STATE
# =============================================================================

V15_SLEEVE_STATE_HASH_PAYLOAD = []

for sleeve in V15_SLEEVES:

    V15_SLEEVE_STATE_HASH_PAYLOAD.append(
        {
            "Signal_Date":
                str(
                    sleeve[
                        "Signal_Date"
                    ].date()
                ),
            "Candidates":
                sleeve[
                    "Candidates"
                ],
            "Complete_Momentum_Stocks":
                sleeve[
                    "Complete_Momentum_Stocks"
                ],
            "Positive_Edge_Stocks":
                sleeve[
                    "Positive_Edge_Stocks"
                ],
            "Weights":
                sorted(
                    (
                        str(k),
                        round(
                            float(v),
                            14,
                        ),
                    )
                    for k, v in sleeve[
                        "Intended_Weights"
                    ].items()
                ),
        }
    )

V15_SLEEVE_STATE_HASH = hashlib.sha256(
    json.dumps(
        V15_SLEEVE_STATE_HASH_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()

print(
    "\nV15 frozen sleeve-state hash:",
    V15_SLEEVE_STATE_HASH,
)


# =============================================================================
# 11. PRICE RETURN HELPER
# =============================================================================

def v15_asset_return(
    ticker,
    execution_date,
    exit_date,
):

    ticker = (
        v15_normalize_ticker(
            ticker
        )
    )

    execution_date = pd.Timestamp(
        execution_date
    ).normalize()

    exit_date = pd.Timestamp(
        exit_date
    ).normalize()

    if (
        ticker
        not in V15_PRICE_WIDE.columns
    ):
        raise RuntimeError(
            f"{ticker} missing from price ledger."
        )

    if (
        execution_date
        not in V15_PRICE_WIDE.index
    ):
        raise RuntimeError(
            f"Execution date {execution_date.date()} "
            f"missing from price ledger."
        )

    entry_price = (
        V15_PRICE_WIDE.at[
            execution_date,
            ticker,
        ]
    )

    if (
        not np.isfinite(
            entry_price
        )
        or
        float(entry_price) <= 0
    ):
        raise RuntimeError(
            f"Missing execution price for "
            f"{ticker} on "
            f"{execution_date.date()}."
        )

    exact_exit = False
    terminal_date = exit_date

    if (
        exit_date
        in V15_PRICE_WIDE.index
    ):

        exit_price = (
            V15_PRICE_WIDE.at[
                exit_date,
                ticker,
            ]
        )

        if (
            np.isfinite(
                exit_price
            )
            and
            float(exit_price) > 0
        ):
            exact_exit = True

        else:
            exit_price = np.nan

    else:
        exit_price = np.nan

    if not np.isfinite(
        exit_price
    ):

        history = (
            V15_PRICE_WIDE.loc[
                (
                    V15_PRICE_WIDE.index
                    >=
                    execution_date
                )
                &
                (
                    V15_PRICE_WIDE.index
                    <=
                    exit_date
                ),
                ticker,
            ]
            .dropna()
        )

        history = history[
            history > 0
        ]

        if len(history) == 0:
            raise RuntimeError(
                f"No observable lifecycle price "
                f"for {ticker} between "
                f"{execution_date.date()} and "
                f"{exit_date.date()}."
            )

        terminal_date = (
            history.index[-1]
        )

        exit_price = float(
            history.iloc[-1]
        )

    simple_return = (
        float(exit_price)
        /
        float(entry_price)
        -
        1.0
    )

    return {
        "Return": float(
            simple_return
        ),
        "Exact_Exit": bool(
            exact_exit
        ),
        "Terminal_Date": pd.Timestamp(
            terminal_date
        ).normalize(),
    }


# =============================================================================
# 12. UNIVERSAL EXPERT ENGINE
# =============================================================================

K = len(
    V15_GRID
)

V15_EXPERT_WEALTH = np.ones(
    K,
    dtype=float,
)

V15_EXPERT_PREV_DRIFT = {}

V15_ACTUAL_PREV_DRIFT = {}

V15_WEALTH = 1.0

V15_EVENT_ROWS = []

V15_REALIZED_TARGETS = []

V15_FORCED_TERMINAL_COUNT = 0


for event_id, row in (
    V15_COMPARE.iterrows()
):

    execution_date = pd.Timestamp(
        row[
            "Execution_Date"
        ]
    ).normalize()

    exit_date = pd.Timestamp(
        row[
            "Exit_Date"
        ]
    ).normalize()

    sleeve = V15_SLEEVES[
        event_id
    ]

    sleeve_weights = dict(
        sleeve[
            "Executable_Weights"
        ]
    )

    unfilled_mass = float(
        sleeve[
            "Unfilled_Sleeve_Mass"
        ]
    )

    sleeve_available = (
        len(
            sleeve_weights
        )
        >
        0
    )

    # -------------------------------------------------------------------------
    # Posterior BEFORE current event
    # -------------------------------------------------------------------------

    posterior = (
        V15_EXPERT_WEALTH
        /
        V15_EXPERT_WEALTH.sum()
    )

    pre_alpha_weight = float(
        np.dot(
            posterior,
            V15_GRID,
        )
    )

    if not sleeve_available:
        pre_alpha_weight = 0.0

    pre_tqqq_weight = (
        1.0
        -
        pre_alpha_weight
    )

    # -------------------------------------------------------------------------
    # Actual portfolio target
    # -------------------------------------------------------------------------

    actual_target = {}

    if sleeve_available:

        fillable_mass = float(
            sum(
                sleeve_weights.values()
            )
        )

        stock_alpha_mass = (
            pre_alpha_weight
            *
            fillable_mass
        )

        actual_target[
            "TQQQ"
        ] = (
            1.0
            -
            stock_alpha_mass
        )

        for ticker, weight in (
            sleeve_weights.items()
        ):

            actual_target[
                ticker
            ] = (
                pre_alpha_weight
                *
                float(weight)
            )

    else:

        actual_target = {
            "TQQQ": 1.0
        }

    actual_target = {
        k: float(v)
        for k, v in (
            actual_target.items()
        )
        if abs(float(v)) > 1e-15
    }

    target_sum = float(
        sum(
            actual_target.values()
        )
    )

    if abs(
        target_sum
        -
        1.0
    ) > 1e-10:
        raise RuntimeError(
            f"V15 target weights do not sum "
            f"to one at event {event_id + 1}: "
            f"{target_sum:.12f}"
        )

    V15_REALIZED_TARGETS.append(
        actual_target.copy()
    )

    actual_turnover = (
        v15_dict_turnover(
            actual_target,
            V15_ACTUAL_PREV_DRIFT,
        )
    )

    actual_cost = (
        actual_turnover
        *
        V15_TCA_RATE
    )

    # -------------------------------------------------------------------------
    # Returns for all assets appearing in this event
    # -------------------------------------------------------------------------

    current_assets = set(
        actual_target.keys()
    )

    for ticker in (
        sleeve_weights.keys()
    ):
        current_assets.add(
            ticker
        )

    asset_returns = {}
    asset_exact_exit = {}

    for ticker in sorted(
        current_assets
    ):

        result = (
            v15_asset_return(
                ticker,
                execution_date,
                exit_date,
            )
        )

        asset_returns[
            ticker
        ] = result[
            "Return"
        ]

        asset_exact_exit[
            ticker
        ] = result[
            "Exact_Exit"
        ]

        if (
            ticker
            !=
            "TQQQ"
            and
            not result[
                "Exact_Exit"
            ]
        ):
            V15_FORCED_TERMINAL_COUNT += 1

    # -------------------------------------------------------------------------
    # Actual V15 gross / net return
    # -------------------------------------------------------------------------

    actual_gross = float(
        sum(
            actual_target[
                ticker
            ]
            *
            asset_returns[
                ticker
            ]
            for ticker in (
                actual_target
            )
        )
    )

    actual_net = (
        actual_gross
        -
        actual_cost
    )

    if (
        1.0
        +
        actual_net
        <=
        0
    ):
        raise RuntimeError(
            "V15 wealth became non-positive."
        )

    V15_WEALTH *= (
        1.0
        +
        actual_net
    )

    # -------------------------------------------------------------------------
    # Actual end-of-period drift
    # -------------------------------------------------------------------------

    actual_denom = (
        1.0
        +
        actual_gross
    )

    new_actual_drift = {}
    actual_cash = 0.0

    for ticker, weight in (
        actual_target.items()
    ):

        end_component = (
            float(weight)
            *
            (
                1.0
                +
                asset_returns[
                    ticker
                ]
            )
            /
            actual_denom
        )

        if (
            ticker
            !=
            "TQQQ"
            and
            not asset_exact_exit[
                ticker
            ]
        ):

            actual_cash += (
                end_component
            )

        else:

            new_actual_drift[
                ticker
            ] = (
                new_actual_drift.get(
                    ticker,
                    0.0,
                )
                +
                end_component
            )

    if actual_cash > 1e-15:
        new_actual_drift[
            "__FORCED_CASH__"
        ] = actual_cash

    V15_ACTUAL_PREV_DRIFT = (
        new_actual_drift
    )

    # -------------------------------------------------------------------------
    # Constant-mix universal experts
    # -------------------------------------------------------------------------

    if sleeve_available:

        fillable_mass = float(
            sum(
                sleeve_weights.values()
            )
        )

        expert_target = {}

        expert_stock_mass = (
            V15_GRID
            *
            fillable_mass
        )

        expert_target[
            "TQQQ"
        ] = (
            1.0
            -
            expert_stock_mass
        )

        for ticker, weight in (
            sleeve_weights.items()
        ):

            expert_target[
                ticker
            ] = (
                V15_GRID
                *
                float(weight)
            )

    else:

        expert_target = {
            "TQQQ":
                np.ones(
                    K,
                    dtype=float,
                )
        }

    all_exp_assets = (
        set(
            expert_target.keys()
        )
        |
        set(
            V15_EXPERT_PREV_DRIFT.keys()
        )
    )

    expert_turnover = np.zeros(
        K,
        dtype=float,
    )

    for ticker in (
        all_exp_assets
    ):

        target_vector = (
            expert_target.get(
                ticker,
                np.zeros(
                    K,
                    dtype=float,
                ),
            )
        )

        previous_vector = (
            V15_EXPERT_PREV_DRIFT.get(
                ticker,
                np.zeros(
                    K,
                    dtype=float,
                ),
            )
        )

        expert_turnover += np.abs(
            target_vector
            -
            previous_vector
        )

    expert_cost = (
        expert_turnover
        *
        V15_TCA_RATE
    )

    expert_gross = np.zeros(
        K,
        dtype=float,
    )

    for ticker, target_vector in (
        expert_target.items()
    ):

        if ticker not in asset_returns:

            result = (
                v15_asset_return(
                    ticker,
                    execution_date,
                    exit_date,
                )
            )

            asset_returns[
                ticker
            ] = (
                result[
                    "Return"
                ]
            )

            asset_exact_exit[
                ticker
            ] = (
                result[
                    "Exact_Exit"
                ]
            )

        expert_gross += (
            target_vector
            *
            asset_returns[
                ticker
            ]
        )

    expert_net = (
        expert_gross
        -
        expert_cost
    )

    if np.any(
        1.0
        +
        expert_net
        <=
        0
    ):
        raise RuntimeError(
            "A V15 universal expert "
            "became non-positive."
        )

    V15_EXPERT_WEALTH *= (
        1.0
        +
        expert_net
    )

    expert_denom = (
        1.0
        +
        expert_gross
    )

    new_expert_drift = {}
    expert_cash = np.zeros(
        K,
        dtype=float,
    )

    for ticker, target_vector in (
        expert_target.items()
    ):

        component = (
            target_vector
            *
            (
                1.0
                +
                asset_returns[
                    ticker
                ]
            )
            /
            expert_denom
        )

        if (
            ticker
            !=
            "TQQQ"
            and
            not asset_exact_exit[
                ticker
            ]
        ):

            expert_cash += (
                component
            )

        else:

            new_expert_drift[
                ticker
            ] = component.copy()

    if np.any(
        expert_cash > 1e-15
    ):

        new_expert_drift[
            "__FORCED_CASH__"
        ] = (
            expert_cash.copy()
        )

    V15_EXPERT_PREV_DRIFT = (
        new_expert_drift
    )

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    V15_EVENT_ROWS.append(
        {
            "Event": event_id + 1,
            "Signal_Date":
                row[
                    "Signal_Date"
                ],
            "Execution_Date":
                execution_date,
            "Exit_Date":
                exit_date,
            "Sleeve_Available":
                sleeve_available,
            "Candidate_Stocks":
                sleeve[
                    "Candidates"
                ],
            "Positive_Edge_Stocks":
                sleeve[
                    "Positive_Edge_Stocks"
                ],
            "Executable_Stocks":
                len(
                    sleeve_weights
                ),
            "Pre_TQQQ_Weight":
                pre_tqqq_weight,
            "Pre_Alpha_Weight":
                pre_alpha_weight,
            "Turnover":
                actual_turnover,
            "TCA_bps":
                actual_cost
                *
                10000.0,
            "Gross_Return_Pct":
                actual_gross
                *
                100.0,
            "V15_Return_Pct":
                actual_net
                *
                100.0,
            "V15_Wealth":
                V15_WEALTH,
            "V8_Return_Pct":
                float(
                    row[
                        "V8_Return_Pct"
                    ]
                ),
            "TQQQ_Return_Pct":
                float(
                    row[
                        "TQQQ_Return_Pct"
                    ]
                ),
            "V15_Minus_V8_pp":
                actual_net
                *
                100.0
                -
                float(
                    row[
                        "V8_Return_Pct"
                    ]
                ),
            "V15_Minus_TQQQ_pp":
                actual_net
                *
                100.0
                -
                float(
                    row[
                        "TQQQ_Return_Pct"
                    ]
                ),
        }
    )


V15_PATH = pd.DataFrame(
    V15_EVENT_ROWS
)


# =============================================================================
# 13. BENCHMARK WEALTH
# =============================================================================

V15_PATH[
    "V8_Wealth"
] = (
    1.0
    +
    V15_PATH[
        "V8_Return_Pct"
    ]
    /
    100.0
).cumprod()

V15_PATH[
    "TQQQ_Wealth"
] = (
    1.0
    +
    V15_PATH[
        "TQQQ_Return_Pct"
    ]
    /
    100.0
).cumprod()


V15_FINAL_WEALTH = float(
    V15_PATH[
        "V15_Wealth"
    ].iloc[-1]
)

V15_V8_FINAL_WEALTH = float(
    V15_PATH[
        "V8_Wealth"
    ].iloc[-1]
)

V15_TQQQ_FINAL_WEALTH = float(
    V15_PATH[
        "TQQQ_Wealth"
    ].iloc[-1]
)


# =============================================================================
# 14. FINAL ECONOMIC RESULT
# =============================================================================

V15_FINAL_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Completed holding periods",
            "V15 final wealth",
            "V15 net return pct",
            "V8 completed-period wealth",
            "V8 completed-period return pct",
            "TQQQ completed-period wealth",
            "TQQQ completed-period return pct",
            "V15 minus V8 pp",
            "V15 minus TQQQ pp",
            "V15 / V8 relative wealth",
            "V15 / TQQQ relative wealth",
            "Mean Alpha allocation pct",
            "Median Alpha allocation pct",
            "Mean TQQQ allocation pct",
            "Total turnover",
            "Mean turnover",
            "Mean execution cost bps",
            "Forced terminal-price events",
        ],
        "Value": [
            len(
                V15_PATH
            ),
            V15_FINAL_WEALTH,
            (
                V15_FINAL_WEALTH
                -
                1.0
            )
            *
            100.0,
            V15_V8_FINAL_WEALTH,
            (
                V15_V8_FINAL_WEALTH
                -
                1.0
            )
            *
            100.0,
            V15_TQQQ_FINAL_WEALTH,
            (
                V15_TQQQ_FINAL_WEALTH
                -
                1.0
            )
            *
            100.0,
            (
                V15_FINAL_WEALTH
                -
                V15_V8_FINAL_WEALTH
            )
            *
            100.0,
            (
                V15_FINAL_WEALTH
                -
                V15_TQQQ_FINAL_WEALTH
            )
            *
            100.0,
            (
                V15_FINAL_WEALTH
                /
                V15_V8_FINAL_WEALTH
            ),
            (
                V15_FINAL_WEALTH
                /
                V15_TQQQ_FINAL_WEALTH
            ),
            V15_PATH[
                "Pre_Alpha_Weight"
            ].mean()
            *
            100.0,
            V15_PATH[
                "Pre_Alpha_Weight"
            ].median()
            *
            100.0,
            V15_PATH[
                "Pre_TQQQ_Weight"
            ].mean()
            *
            100.0,
            V15_PATH[
                "Turnover"
            ].sum(),
            V15_PATH[
                "Turnover"
            ].mean(),
            V15_PATH[
                "TCA_bps"
            ].mean(),
            V15_FORCED_TERMINAL_COUNT,
        ],
    }
)

print(
    "\n2) V15 FINAL ECONOMIC RESULT"
)

display(
    V15_FINAL_SUMMARY
)


# =============================================================================
# 15. MULTI-PERIOD ROBUSTNESS
# =============================================================================

window_specs = [
    ("~1M", 1),
    ("~3M", 3),
    ("~6M", 6),
    ("~12M", 12),
    ("~24M", 24),
    ("ALL_COMPLETED", len(V15_PATH)),
]

window_rows = []

for window_name, periods in (
    window_specs
):

    periods = min(
        periods,
        len(V15_PATH),
    )

    sample = (
        V15_PATH
        .tail(
            periods
        )
    )

    v15_ret = (
        v15_series_return_pct(
            sample[
                "V15_Return_Pct"
            ]
        )
    )

    v8_ret = (
        v15_series_return_pct(
            sample[
                "V8_Return_Pct"
            ]
        )
    )

    tqqq_ret = (
        v15_series_return_pct(
            sample[
                "TQQQ_Return_Pct"
            ]
        )
    )

    window_rows.append(
        {
            "Window":
                window_name,
            "Periods":
                periods,
            "V15_Return_Pct":
                v15_ret,
            "V8_Return_Pct":
                v8_ret,
            "TQQQ_Return_Pct":
                tqqq_ret,
            "V15_Minus_V8_pp":
                v15_ret
                -
                v8_ret,
            "V15_Minus_TQQQ_pp":
                v15_ret
                -
                tqqq_ret,
            "V15_Beats_V8":
                bool(
                    v15_ret
                    >
                    v8_ret
                ),
            "V15_Beats_TQQQ":
                bool(
                    v15_ret
                    >
                    tqqq_ret
                ),
        }
    )

V15_ROBUSTNESS = pd.DataFrame(
    window_rows
)

print(
    "\n3) V15 TRAILING MULTI-PERIOD ROBUSTNESS"
)

display(
    V15_ROBUSTNESS
)


# =============================================================================
# 16. LAST 12 EVENTS
# =============================================================================

print(
    "\n4) LAST 12 V15 EVENTS"
)

display(
    V15_PATH[
        [
            "Event",
            "Execution_Date",
            "Exit_Date",
            "Positive_Edge_Stocks",
            "Executable_Stocks",
            "Pre_TQQQ_Weight",
            "Pre_Alpha_Weight",
            "Turnover",
            "TCA_bps",
            "V15_Return_Pct",
            "V8_Return_Pct",
            "TQQQ_Return_Pct",
            "V15_Minus_V8_pp",
            "V15_Minus_TQQQ_pp",
            "V15_Wealth",
        ]
    ]
    .tail(
        12
    )
)


# =============================================================================
# 17. FINAL UNIVERSAL POSTERIOR
# =============================================================================

V15_FINAL_POSTERIOR = (
    V15_EXPERT_WEALTH
    /
    V15_EXPERT_WEALTH.sum()
)

V15_FINAL_ALPHA_WEIGHT = float(
    np.dot(
        V15_FINAL_POSTERIOR,
        V15_GRID,
    )
)

V15_FINAL_POSTERIOR_SUMMARY = (
    pd.DataFrame(
        {
            "Sleeve": [
                "TQQQ",
                "V15_RELATIVE_MOMENTUM_ALPHA",
            ],
            "Weight_Pct": [
                (
                    1.0
                    -
                    V15_FINAL_ALPHA_WEIGHT
                )
                *
                100.0,
                V15_FINAL_ALPHA_WEIGHT
                *
                100.0,
            ],
        }
    )
)

print(
    "\n5) FINAL CAUSAL UNIVERSAL POSTERIOR MEAN"
)

display(
    V15_FINAL_POSTERIOR_SUMMARY
)


# =============================================================================
# 18. $100,000 TERMINAL VALUE
# =============================================================================

V15_CAPITAL_TABLE = pd.DataFrame(
    {
        "Strategy": [
            "V15",
            "V8_REACCOUNTED",
            "TQQQ",
        ],
        "Initial_Capital_USD": [
            V15_REFERENCE_AUM_USD,
            V15_REFERENCE_AUM_USD,
            V15_REFERENCE_AUM_USD,
        ],
        "Final_Wealth_Multiple": [
            V15_FINAL_WEALTH,
            V15_V8_FINAL_WEALTH,
            V15_TQQQ_FINAL_WEALTH,
        ],
        "Final_Portfolio_Value_USD": [
            V15_REFERENCE_AUM_USD
            *
            V15_FINAL_WEALTH,
            V15_REFERENCE_AUM_USD
            *
            V15_V8_FINAL_WEALTH,
            V15_REFERENCE_AUM_USD
            *
            V15_TQQQ_FINAL_WEALTH,
        ],
        "Net_Profit_USD": [
            V15_REFERENCE_AUM_USD
            *
            (
                V15_FINAL_WEALTH
                -
                1.0
            ),
            V15_REFERENCE_AUM_USD
            *
            (
                V15_V8_FINAL_WEALTH
                -
                1.0
            ),
            V15_REFERENCE_AUM_USD
            *
            (
                V15_TQQQ_FINAL_WEALTH
                -
                1.0
            ),
        ],
    }
)

print(
    "\n6) $100,000 CAPITAL COMPARISON"
)

display(
    V15_CAPITAL_TABLE
)


# =============================================================================
# 19. WEALTH GRAPH
# =============================================================================

plt.figure(
    figsize=(16, 8)
)

plt.plot(
    V15_PATH[
        "Exit_Date"
    ],
    V15_PATH[
        "V15_Wealth"
    ],
    label="V15 Relative-Momentum Challenger",
    linewidth=2.4,
)

plt.plot(
    V15_PATH[
        "Exit_Date"
    ],
    V15_PATH[
        "V8_Wealth"
    ],
    label="V8 Champion",
    linewidth=2.4,
)

plt.plot(
    V15_PATH[
        "Exit_Date"
    ],
    V15_PATH[
        "TQQQ_Wealth"
    ],
    label="TQQQ",
    linewidth=2.2,
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1.2,
)

plt.title(
    "V15 vs V8 vs TQQQ — COMPLETED-PERIOD NET WEALTH"
)

plt.xlabel(
    "Date"
)

plt.ylabel(
    "Wealth Multiple"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================================
# 20. RELATIVE WEALTH GRAPH
# =============================================================================

plt.figure(
    figsize=(16, 7)
)

plt.plot(
    V15_PATH[
        "Exit_Date"
    ],
    (
        V15_PATH[
            "V15_Wealth"
        ]
        /
        V15_PATH[
            "V8_Wealth"
        ]
    ),
    label="V15 / V8",
    linewidth=2.4,
)

plt.plot(
    V15_PATH[
        "Exit_Date"
    ],
    (
        V15_PATH[
            "V15_Wealth"
        ]
        /
        V15_PATH[
            "TQQQ_Wealth"
        ]
    ),
    label="V15 / TQQQ",
    linewidth=2.4,
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1.2,
)

plt.title(
    "V15 — RELATIVE WEALTH"
)

plt.xlabel(
    "Date"
)

plt.ylabel(
    "Relative Wealth"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================================
# 21. ALLOCATION GRAPH
# =============================================================================

plt.figure(
    figsize=(16, 7)
)

plt.plot(
    V15_PATH[
        "Execution_Date"
    ],
    V15_PATH[
        "Pre_TQQQ_Weight"
    ]
    *
    100.0,
    label="TQQQ Weight",
    linewidth=2.2,
)

plt.plot(
    V15_PATH[
        "Execution_Date"
    ],
    V15_PATH[
        "Pre_Alpha_Weight"
    ]
    *
    100.0,
    label="Relative-Momentum Alpha Weight",
    linewidth=2.2,
)

plt.axhline(
    50.0,
    linestyle="--",
    linewidth=1.0,
)

plt.title(
    "V15 — CAUSAL UNIVERSAL ALLOCATION"
)

plt.xlabel(
    "Execution Date"
)

plt.ylabel(
    "Portfolio Weight (%)"
)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.show()


# =============================================================================
# 22. RESEARCH FINGERPRINT
# =============================================================================

V15_RESULT_PAYLOAD = {
    "spec_fingerprint":
        V15_SPEC_FINGERPRINT,
    "sleeve_state_hash":
        V15_SLEEVE_STATE_HASH,
    "final_wealth":
        round(
            V15_FINAL_WEALTH,
            12,
        ),
    "v8_final_wealth":
        round(
            V15_V8_FINAL_WEALTH,
            12,
        ),
    "tqqq_final_wealth":
        round(
            V15_TQQQ_FINAL_WEALTH,
            12,
        ),
    "events":
        len(
            V15_PATH
        ),
}

V15_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V15_RESULT_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()

print(
    "\n7) V15 RESEARCH FINGERPRINT"
)

print(
    V15_RESEARCH_FINGERPRINT
)


# =============================================================================
# 23. FINAL ONE-SHOT VERDICT
# =============================================================================

V15_BEATS_V8 = (
    V15_FINAL_WEALTH
    >
    V15_V8_FINAL_WEALTH
)

V15_BEATS_TQQQ = (
    V15_FINAL_WEALTH
    >
    V15_TQQQ_FINAL_WEALTH
)

V15_ALL_WINDOWS_BEAT_V8 = bool(
    V15_ROBUSTNESS[
        "V15_Beats_V8"
    ].all()
)

V15_ALL_WINDOWS_BEAT_TQQQ = bool(
    V15_ROBUSTNESS[
        "V15_Beats_TQQQ"
    ].all()
)


print(
    "\n"
    +
    "=" * 136
)

print(
    "V15 ONE-SHOT RESEARCH VERDICT"
)

print(
    "=" * 136
)

print(
    f"V15 final wealth          : "
    f"{V15_FINAL_WEALTH:.6f}"
)

print(
    f"V8 champion wealth        : "
    f"{V15_V8_FINAL_WEALTH:.6f}"
)

print(
    f"TQQQ wealth               : "
    f"{V15_TQQQ_FINAL_WEALTH:.6f}"
)

print(
    f"V15 minus V8              : "
    f"{(V15_FINAL_WEALTH - V15_V8_FINAL_WEALTH) * 100.0:+.6f} pp"
)

print(
    f"V15 minus TQQQ            : "
    f"{(V15_FINAL_WEALTH - V15_TQQQ_FINAL_WEALTH) * 100.0:+.6f} pp"
)

print(
    f"V15 beats V8              : "
    f"{V15_BEATS_V8}"
)

print(
    f"V15 beats TQQQ            : "
    f"{V15_BEATS_TQQQ}"
)

print(
    f"All declared windows > V8 : "
    f"{V15_ALL_WINDOWS_BEAT_V8}"
)

print(
    f"All windows > TQQQ        : "
    f"{V15_ALL_WINDOWS_BEAT_TQQQ}"
)


if V15_BEATS_V8:

    print(
        "\n[+] V15 BEATS THE V8 CHAMPION "
        "ON COMPLETED-PERIOD NET TERMINAL WEALTH."
    )

    if V15_ALL_WINDOWS_BEAT_V8:

        print(
            "[+] V15 ALSO BEATS V8 IN EVERY "
            "DECLARED TRAILING WINDOW."
        )

        print(
            "[+] V15 QUALIFIES FOR "
            "CHAMPION-CHALLENGER VALIDATION."
        )

    else:

        print(
            "[!] V15 BEATS V8 IN TERMINAL WEALTH "
            "BUT NOT IN EVERY TRAILING WINDOW."
        )

        print(
            "[!] DO NOT TUNE V15. "
            "INSPECT THE FROZEN RESULT ONLY."
        )

else:

    print(
        "\n[-] V15 DOES NOT BEAT V8."
    )

    print(
        "[-] REJECT V15 AS DESIGNED."
    )

    print(
        "[-] DO NOT PATCH OR RETUNE IT."
    )

    print(
        "[+] V8 REMAINS THE FROZEN CHAMPION."
    )


print(
    "\nINTEGRITY:"
)

print(
    "[+] No forecasting model was fitted."
)

print(
    "[+] Frozen PIT eligibility was preserved."
)

print(
    "[+] Existing liquidity eligibility was preserved."
)

print(
    "[+] Signal information ends before execution."
)

print(
    "[+] Four horizons were fixed before performance."
)

print(
    "[+] Cross-sectional ranks were calculated contemporaneously."
)

print(
    "[+] Raw positive TQQQ-relative momentum was required."
)

print(
    "[+] No Top-K rule."
)

print(
    "[+] No minimum stock weight."
)

print(
    "[+] No maximum stock weight."
)

print(
    "[+] No sector cap."
)

print(
    "[+] No risk cap."
)

print(
    "[+] No TQQQ floor."
)

print(
    "[+] No alpha cap."
)

print(
    "[+] No strategic cash."
)

print(
    "[+] No leverage above 100%."
)

print(
    "[+] Universal allocation used only prior completed events."
)

print(
    "[+] Linear transaction cost was included."
)

print(
    "[+] No V15 parameter may be changed after observing this result."
)

print(
    "=" * 136
)
restored_register('V15', V15_FINAL_WEALTH, V15_PATH, 'V15_Wealth', 'Close / original V15 costs and completed periods', 'Historically rejected')
