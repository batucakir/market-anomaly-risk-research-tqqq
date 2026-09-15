# ==============================================================================
# MODULE 18 / HISTORICAL BLOCK 41
# FINAL SAME-CALENDAR NET-WEALTH BENCHMARK
# TIMEZONE-SAFE FINAL VERSION
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

B41_REQUIRED = [
    "BLOCK40_PATH",
    "B40_SCHEDULE",
    "B40_OPEN_WIDE",
    "B40_CLOSE_WIDE",
    "V4_DAILY_PANEL",
    "B40_TCA_RATE",
    "B40_TCA_BPS",
    "B40_FINAL_DATE",
    "BLOCK40_FINGERPRINT",
]


B41_MISSING = [
    x
    for x in B41_REQUIRED
    if x not in globals()
]


if B41_MISSING:
    raise RuntimeError(
        "BLOCK 41 missing required objects: "
        f"{B41_MISSING}"
    )


print("=" * 118)
print("BLOCK 41 — FINAL SAME-CALENDAR NET-WEALTH BENCHMARK")
print("=" * 118)


# ==============================================================================
# 1. CANONICAL DATETIME HELPERS
# ==============================================================================

def b41_naive_timestamp(value):

    ts = pd.Timestamp(value)

    if ts.tzinfo is not None:

        ts = (
            ts
            .tz_convert("America/New_York")
            .tz_localize(None)
        )

    return ts.normalize()


def b41_naive_datetime_series(series):

    result = pd.to_datetime(
        series,
        errors="coerce",
    )

    if getattr(
        result.dt,
        "tz",
        None,
    ) is not None:

        result = (
            result
            .dt.tz_convert(
                "America/New_York"
            )
            .dt.tz_localize(
                None
            )
        )

    return result.dt.normalize()


def b41_naive_datetime_index(index):

    idx = pd.DatetimeIndex(
        pd.to_datetime(
            index
        )
    )

    if idx.tz is not None:

        idx = (
            idx
            .tz_convert(
                "America/New_York"
            )
            .tz_localize(
                None
            )
        )

    return idx.normalize()


# ==============================================================================
# 2. CREATE LOCAL TIMEZONE-SAFE COPIES
# ==============================================================================

B41_OPEN_WIDE = (
    B40_OPEN_WIDE.copy()
)

B41_OPEN_WIDE.index = (
    b41_naive_datetime_index(
        B41_OPEN_WIDE.index
    )
)

B41_OPEN_WIDE = (
    B41_OPEN_WIDE
    .groupby(
        level=0
    )
    .last()
    .sort_index()
)


B41_CLOSE_WIDE = (
    B40_CLOSE_WIDE.copy()
)

B41_CLOSE_WIDE.index = (
    b41_naive_datetime_index(
        B41_CLOSE_WIDE.index
    )
)

B41_CLOSE_WIDE = (
    B41_CLOSE_WIDE
    .groupby(
        level=0
    )
    .last()
    .sort_index()
)


B41_DAILY_PANEL = (
    V4_DAILY_PANEL.copy()
)

B41_DAILY_PANEL[
    "Date"
] = b41_naive_datetime_series(
    B41_DAILY_PANEL[
        "Date"
    ]
)


B41_PATH = (
    BLOCK40_PATH.copy()
)

for column in [
    "Signal_Date",
    "Execution_Date",
    "Exit_Date",
]:

    B41_PATH[
        column
    ] = b41_naive_datetime_series(
        B41_PATH[
            column
        ]
    )


B41_SCHEDULE = (
    B40_SCHEDULE.copy()
)

for column in [
    "Signal_Date",
    "Execution_Date",
    "Next_Execution_Date",
    "Exit_Date",
]:

    if column in B41_SCHEDULE.columns:

        B41_SCHEDULE[
            column
        ] = b41_naive_datetime_series(
            B41_SCHEDULE[
                column
            ]
        )


# ==============================================================================
# 3. EXACT COMMON CALENDAR
# ==============================================================================

B41_START_DATE = b41_naive_timestamp(
    B41_SCHEDULE[
        "Execution_Date"
    ]
    .min()
)


B41_END_DATE = b41_naive_timestamp(
    B40_FINAL_DATE
)


B41_ELAPSED_YEARS = (
    (
        B41_END_DATE
        -
        B41_START_DATE
    ).days
    /
    365.25
)


print(
    "\nComparison start :",
    B41_START_DATE.date()
)

print(
    "Comparison end   :",
    B41_END_DATE.date()
)

print(
    "Elapsed years    :",
    round(
        B41_ELAPSED_YEARS,
        4,
    )
)

print(
    "Benchmark TCA    :",
    f"{B40_TCA_BPS:.2f} bps"
)

print(
    "Datetime standard: America/New_York calendar date -> tz-naive"
)


# ==============================================================================
# 4. PERFORMANCE HELPERS
# ==============================================================================

def b41_max_drawdown(
    wealth,
):

    wealth = (
        pd.Series(
            wealth,
            dtype=float,
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
    )

    if wealth.empty:
        return np.nan

    running_max = (
        wealth.cummax()
    )

    drawdown = (
        wealth
        /
        running_max
        -
        1.0
    )

    return float(
        drawdown.min()
    )


def b41_cagr(
    final_wealth,
):

    if (
        not np.isfinite(
            final_wealth
        )
        or
        final_wealth <= 0
        or
        B41_ELAPSED_YEARS <= 0
    ):

        return np.nan

    return float(
        final_wealth
        **
        (
            1.0
            /
            B41_ELAPSED_YEARS
        )
        -
        1.0
    )


# ==============================================================================
# 5. V4 RIDGE / HGB CURVES
# ==============================================================================

B41_V4_CURVES = {}


for model_name in [
    "RIDGE",
    "HGB",
]:

    section = (
        B41_PATH[
            B41_PATH[
                "Model"
            ]
            ==
            model_name
        ]
        .sort_values(
            "Exit_Date"
        )
        [
            [
                "Exit_Date",
                "Wealth",
            ]
        ]
        .dropna()
        .drop_duplicates(
            "Exit_Date",
            keep="last",
        )
    )


    curve = pd.Series(
        section[
            "Wealth"
        ]
        .to_numpy(
            dtype=float
        ),
        index=
            section[
                "Exit_Date"
            ],
        name=
            f"V4_{model_name}",
    )


    B41_V4_CURVES[
        model_name
    ] = curve


# ==============================================================================
# 6. SINGLE-ASSET BUY & HOLD
# ==============================================================================

def b41_buy_hold_curve(
    ticker,
):

    if ticker not in (
        B41_OPEN_WIDE.columns
    ):

        raise RuntimeError(
            f"{ticker} missing from open table."
        )


    if ticker not in (
        B41_CLOSE_WIDE.columns
    ):

        raise RuntimeError(
            f"{ticker} missing from close table."
        )


    if B41_START_DATE not in (
        B41_OPEN_WIDE.index
    ):

        raise RuntimeError(
            f"Start date {B41_START_DATE.date()} "
            "missing from open table."
        )


    entry_open = (
        B41_OPEN_WIDE.loc[
            B41_START_DATE,
            ticker
        ]
    )


    if (
        not np.isfinite(
            entry_open
        )
        or
        entry_open <= 0
    ):

        raise RuntimeError(
            f"{ticker} has invalid opening price "
            f"on {B41_START_DATE.date()}."
        )


    closes = (
        B41_CLOSE_WIDE[
            ticker
        ]
        .loc[
            (
                B41_CLOSE_WIDE.index
                >=
                B41_START_DATE
            )
            &
            (
                B41_CLOSE_WIDE.index
                <=
                B41_END_DATE
            )
        ]
        .dropna()
    )


    if closes.empty:

        raise RuntimeError(
            f"{ticker} benchmark has zero observations."
        )


    # Initial purchase costs 2 bps.
    # No terminal liquidation cost because all strategies
    # are marked-to-market.

    initial_capital_after_cost = (
        1.0
        -
        B40_TCA_RATE
    )


    wealth = (
        initial_capital_after_cost
        *
        closes
        /
        float(
            entry_open
        )
    )


    wealth.name = (
        f"{ticker}_BH_NET"
    )

    return wealth


B41_QQQ = b41_buy_hold_curve(
    "QQQ"
)

B41_TQQQ = b41_buy_hold_curve(
    "TQQQ"
)


# ==============================================================================
# 7. TIMEZONE-SAFE REALIZED RETURN HELPER
# ==============================================================================

def b41_realized_asset_returns(
    assets,
    execution_date,
    exit_date,
    final_period,
):

    assets = list(
        assets
    )

    if len(
        assets
    ) == 0:

        return {}


    execution_date = (
        b41_naive_timestamp(
            execution_date
        )
    )


    exit_date = (
        b41_naive_timestamp(
            exit_date
        )
    )


    entry = (
        B41_OPEN_WIDE
        .reindex(
            index=[
                execution_date
            ],
            columns=
                assets,
        )
        .iloc[
            0
        ]
    )


    exit_table = (
        B41_CLOSE_WIDE
        if final_period
        else
        B41_OPEN_WIDE
    )


    exit_price = (
        exit_table
        .reindex(
            index=[
                exit_date
            ],
            columns=
                assets,
        )
        .iloc[
            0
        ]
    )


    missing_exit = (
        ~np.isfinite(
            exit_price
        )
        |
        (
            exit_price
            <=
            0
        )
    )


    if missing_exit.any():

        missing_assets = list(
            exit_price.index[
                missing_exit
            ]
        )


        interval = (
            B41_CLOSE_WIDE.loc[
                (
                    B41_CLOSE_WIDE.index
                    >=
                    execution_date
                )
                &
                (
                    B41_CLOSE_WIDE.index
                    <=
                    exit_date
                ),
                missing_assets,
            ]
        )


        if not interval.empty:

            fallback = (
                interval
                .ffill()
                .iloc[
                    -1
                ]
            )


            exit_price.loc[
                missing_assets
            ] = (
                exit_price.loc[
                    missing_assets
                ]
                .fillna(
                    fallback
                )
            )


    realized = (
        exit_price
        /
        entry
        -
        1.0
    )


    invalid_entry = (
        ~np.isfinite(
            entry
        )
        |
        (
            entry
            <=
            0
        )
    )


    invalid_return = (
        ~np.isfinite(
            realized
        )
    )


    realized.loc[
        invalid_entry
        |
        invalid_return
    ] = -1.0


    realized = realized.clip(
        lower=-1.0
    )


    return {
        asset:
            float(
                realized.loc[
                    asset
                ]
            )
        for asset in assets
    }


# ==============================================================================
# 8. BROAD PIT EQUAL-WEIGHT BENCHMARK
# ==============================================================================

pit_ew_wealth = 1.0

pit_ew_previous_weights = {}

pit_ew_rows = []


for rebalance_no, row in enumerate(
    B41_SCHEDULE.itertuples(
        index=False
    ),
    start=1,
):

    signal_date = (
        b41_naive_timestamp(
            row.Signal_Date
        )
    )


    execution_date = (
        b41_naive_timestamp(
            row.Execution_Date
        )
    )


    exit_date = (
        b41_naive_timestamp(
            row.Exit_Date
        )
    )


    final_period = bool(
        row.Is_Final_Period
    )


    # Eligible at SIGNAL DATE only.

    eligible_assets = (
        B41_DAILY_PANEL.loc[
            (
                B41_DAILY_PANEL[
                    "Date"
                ]
                ==
                signal_date
            )
            &
            (
                B41_DAILY_PANEL[
                    "Eligible"
                ]
            ),
            "Ticker",
        ]
        .dropna()
        .drop_duplicates()
        .tolist()
    )


    if len(
        eligible_assets
    ) == 0:

        raise RuntimeError(
            "PIT equal-weight benchmark has zero "
            f"eligible assets at {signal_date.date()}."
        )


    # Require valid next-open execution.

    entry_open = (
        B41_OPEN_WIDE
        .reindex(
            index=[
                execution_date
            ],
            columns=
                eligible_assets,
        )
        .iloc[
            0
        ]
    )


    tradable = list(
        entry_open.index[
            np.isfinite(
                entry_open
            )
            &
            (
                entry_open
                >
                0
            )
        ]
    )


    if len(
        tradable
    ) == 0:

        raise RuntimeError(
            "PIT equal-weight has zero tradable assets "
            f"on {execution_date.date()}."
        )


    equal_weight = (
        1.0
        /
        len(
            tradable
        )
    )


    target_weights = {
        asset:
            equal_weight
        for asset in tradable
    }


    # Turnover including exits from disappeared securities.

    union_assets = (
        set(
            pit_ew_previous_weights
        )
        |
        set(
            target_weights
        )
    )


    turnover = float(
        sum(
            abs(
                target_weights.get(
                    asset,
                    0.0
                )
                -
                pit_ew_previous_weights.get(
                    asset,
                    0.0
                )
            )
            for asset in union_assets
        )
    )


    cost_fraction = (
        B40_TCA_RATE
        *
        turnover
    )


    wealth_after_cost = (
        pit_ew_wealth
        *
        (
            1.0
            -
            cost_fraction
        )
    )


    realized_returns = (
        b41_realized_asset_returns(
            assets=
                tradable,
            execution_date=
                execution_date,
            exit_date=
                exit_date,
            final_period=
                final_period,
        )
    )


    portfolio_return = float(
        sum(
            target_weights[
                asset
            ]
            *
            realized_returns[
                asset
            ]
            for asset in tradable
        )
    )


    period_factor = (
        1.0
        +
        portfolio_return
    )


    if period_factor <= 0:
        period_factor = 1e-12


    pit_ew_wealth = (
        wealth_after_cost
        *
        period_factor
    )


    # Drift holdings to next rebalance.

    end_values = {
        asset:
            target_weights[
                asset
            ]
            *
            (
                1.0
                +
                realized_returns[
                    asset
                ]
            )
        for asset in tradable
    }


    end_total = float(
        sum(
            end_values.values()
        )
    )


    if end_total > 0:

        pit_ew_previous_weights = {
            asset:
                value
                /
                end_total
            for asset, value
            in end_values.items()
            if (
                value
                /
                end_total
            )
            >
            1e-12
        }

    else:

        pit_ew_previous_weights = {}


    pit_ew_rows.append(
        {
            "Rebalance":
                rebalance_no,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Exit_Date":
                exit_date,

            "Assets":
                len(
                    tradable
                ),

            "Turnover":
                turnover,

            "Cost_Fraction":
                cost_fraction,

            "Period_Return":
                portfolio_return,

            "Wealth":
                pit_ew_wealth,
        }
    )


BLOCK41_PIT_EW_PATH = pd.DataFrame(
    pit_ew_rows
)


B41_PIT_EW = pd.Series(
    BLOCK41_PIT_EW_PATH[
        "Wealth"
    ]
    .to_numpy(
        dtype=float
    ),
    index=
        BLOCK41_PIT_EW_PATH[
            "Exit_Date"
        ],
    name=
        "PIT_EW_NET_2BPS",
)


# ==============================================================================
# 9. CASH
# ==============================================================================

B41_MARKET_INDEX = (
    B41_CLOSE_WIDE.index[
        (
            B41_CLOSE_WIDE.index
            >=
            B41_START_DATE
        )
        &
        (
            B41_CLOSE_WIDE.index
            <=
            B41_END_DATE
        )
    ]
)


B41_CASH = pd.Series(
    1.0,
    index=
        B41_MARKET_INDEX,
    name=
        "CASH",
)


# ==============================================================================
# 10. OPTIONAL FROZEN V3 FINDER
# ==============================================================================

def b41_prepare_v3_series(
    series,
):

    series = pd.Series(
        series
    ).copy()


    try:

        series.index = (
            b41_naive_datetime_index(
                series.index
            )
        )

    except Exception:

        return None


    series = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
    )


    series = (
        series
        .groupby(
            level=0
        )
        .last()
        .sort_index()
    )


    base_candidates = (
        series.loc[
            series.index
            <=
            B41_START_DATE
        ]
    )


    if base_candidates.empty:
        return None


    base_value = float(
        base_candidates.iloc[
            -1
        ]
    )


    if (
        not np.isfinite(
            base_value
        )
        or
        base_value <= 0
    ):

        return None


    comparison = (
        series.loc[
            (
                series.index
                >=
                B41_START_DATE
            )
            &
            (
                series.index
                <=
                B41_END_DATE
            )
        ]
        /
        base_value
    )


    if len(
        comparison
    ) < 2:

        return None


    comparison.name = (
        "FROZEN_V3"
    )


    return comparison


def b41_find_v3_curve():

    value_names = [
        "V3_NET_2BPS",
        "V3_Net_2BPS",
        "V3_NET_WEALTH",
        "V3_Net_Wealth",
        "V3_Wealth",
        "Net_Wealth",
        "Wealth",
    ]


    date_names = [
        "Timestamp",
        "Date",
        "Exit_Date",
        "Execution_Date",
    ]


    candidates = []


    for object_name, obj in list(
        globals().items()
    ):

        upper_name = str(
            object_name
        ).upper()


        if not (
            "V3"
            in
            upper_name

            or

            "BLOCK28"
            in
            upper_name

            or

            "BLOCK29"
            in
            upper_name

            or

            "BLOCK30"
            in
            upper_name
        ):

            continue


        # ----------------------------------------------------------------------
        # SERIES
        # ----------------------------------------------------------------------

        if isinstance(
            obj,
            pd.Series,
        ):

            combined_name = (
                upper_name
                +
                " "
                +
                str(
                    obj.name
                    if obj.name is not None
                    else ""
                ).upper()
            )


            if not (
                "V3"
                in
                combined_name

                and

                (
                    "NET"
                    in
                    combined_name

                    or

                    "WEALTH"
                    in
                    combined_name
                )
            ):

                continue


            prepared = (
                b41_prepare_v3_series(
                    obj
                )
            )


            if prepared is not None:

                candidates.append(
                    (
                        len(
                            prepared
                        ),
                        object_name,
                        prepared,
                    )
                )


        # ----------------------------------------------------------------------
        # DATAFRAME
        # ----------------------------------------------------------------------

        elif isinstance(
            obj,
            pd.DataFrame,
        ):

            date_column = next(
                (
                    x
                    for x in date_names
                    if x in obj.columns
                ),
                None,
            )


            if date_column is None:
                continue


            value_column = next(
                (
                    x
                    for x in value_names
                    if x in obj.columns
                ),
                None,
            )


            if value_column is None:
                continue


            temp = (
                obj[
                    [
                        date_column,
                        value_column,
                    ]
                ]
                .dropna()
                .copy()
            )


            if temp.empty:
                continue


            temp_dates = (
                b41_naive_datetime_series(
                    temp[
                        date_column
                    ]
                )
            )


            raw_series = pd.Series(
                pd.to_numeric(
                    temp[
                        value_column
                    ],
                    errors="coerce",
                ).to_numpy(),
                index=
                    temp_dates,
            )


            prepared = (
                b41_prepare_v3_series(
                    raw_series
                )
            )


            if prepared is not None:

                candidates.append(
                    (
                        len(
                            prepared
                        ),
                        object_name,
                        prepared,
                    )
                )


    if not candidates:

        return (
            None,
            None,
        )


    candidates.sort(
        key=lambda x:
            x[
                0
            ],
        reverse=True,
    )


    _, source_name, curve = (
        candidates[
            0
        ]
    )


    return (
        source_name,
        curve,
    )


B41_V3_SOURCE_OBJECT, B41_V3 = (
    b41_find_v3_curve()
)


# ==============================================================================
# 11. ALL BENCHMARK CURVES
# ==============================================================================

B41_CURVES = {

    "V4_RIDGE":
        B41_V4_CURVES[
            "RIDGE"
        ],

    "V4_HGB":
        B41_V4_CURVES[
            "HGB"
        ],

    "QQQ_BH_NET_2BPS":
        B41_QQQ,

    "TQQQ_BH_NET_2BPS":
        B41_TQQQ,

    "PIT_EW_NET_2BPS":
        B41_PIT_EW,

    "CASH":
        B41_CASH,
}


if B41_V3 is not None:

    B41_CURVES[
        "FROZEN_V3"
    ] = (
        B41_V3
    )


# ==============================================================================
# 12. FINAL NET-WEALTH SUMMARY
# ==============================================================================

summary_rows = []


for strategy_name, raw_curve in (
    B41_CURVES.items()
):

    curve = (
        pd.Series(
            raw_curve,
            dtype=float,
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
        .sort_index()
    )


    if curve.empty:
        continue


    final_wealth = float(
        curve.iloc[
            -1
        ]
    )


    summary_rows.append(
        {
            "Strategy":
                strategy_name,

            "Final_Wealth":
                final_wealth,

            "Net_Return_Pct":
                100.0
                *
                (
                    final_wealth
                    -
                    1.0
                ),

            "CAGR_Pct":
                100.0
                *
                b41_cagr(
                    final_wealth
                ),

            "Observed_Path_MaxDD_Pct":
                100.0
                *
                b41_max_drawdown(
                    curve
                ),

            "Observations":
                len(
                    curve
                ),
        }
    )


BLOCK41_SUMMARY = (
    pd.DataFrame(
        summary_rows
    )
    .sort_values(
        "Final_Wealth",
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


BLOCK41_SUMMARY.insert(
    0,
    "Rank",
    np.arange(
        1,
        len(
            BLOCK41_SUMMARY
        )
        +
        1
    ),
)


# ==============================================================================
# 13. V4 LEADER
# ==============================================================================

ridge_final = float(
    BLOCK41_SUMMARY.loc[
        BLOCK41_SUMMARY[
            "Strategy"
        ]
        ==
        "V4_RIDGE",
        "Final_Wealth",
    ]
    .iloc[
        0
    ]
)


hgb_final = float(
    BLOCK41_SUMMARY.loc[
        BLOCK41_SUMMARY[
            "Strategy"
        ]
        ==
        "V4_HGB",
        "Final_Wealth",
    ]
    .iloc[
        0
    ]
)


if ridge_final >= hgb_final:

    B41_V4_LEADER = (
        "V4_RIDGE"
    )

    B41_V4_LEADER_WEALTH = (
        ridge_final
    )

else:

    B41_V4_LEADER = (
        "V4_HGB"
    )

    B41_V4_LEADER_WEALTH = (
        hgb_final
    )


# ==============================================================================
# 14. STRONGEST EX-ANTE BENCHMARK
# ==============================================================================

B41_PRIMARY_BENCHMARKS = [
    "QQQ_BH_NET_2BPS",
    "TQQQ_BH_NET_2BPS",
    "PIT_EW_NET_2BPS",
    "CASH",
]


available_benchmarks = (
    BLOCK41_SUMMARY[
        BLOCK41_SUMMARY[
            "Strategy"
        ]
        .isin(
            B41_PRIMARY_BENCHMARKS
        )
    ]
)


if available_benchmarks.empty:

    raise RuntimeError(
        "No primary benchmark is available."
    )


best_benchmark_row = (
    available_benchmarks
    .sort_values(
        "Final_Wealth",
        ascending=False,
    )
    .iloc[
        0
    ]
)


B41_STRONGEST_BENCHMARK = (
    best_benchmark_row[
        "Strategy"
    ]
)


B41_STRONGEST_BENCHMARK_WEALTH = float(
    best_benchmark_row[
        "Final_Wealth"
    ]
)


B41_V4_MINUS_BEST_BENCHMARK_PP = (
    100.0
    *
    (
        B41_V4_LEADER_WEALTH
        -
        B41_STRONGEST_BENCHMARK_WEALTH
    )
)


B41_BEATS_STRONGEST_BENCHMARK = (
    B41_V4_LEADER_WEALTH
    >
    B41_STRONGEST_BENCHMARK_WEALTH
)


# ==============================================================================
# 15. PAIRWISE TABLE
# ==============================================================================

pairwise_rows = []


pairwise_benchmarks = list(
    B41_PRIMARY_BENCHMARKS
)


if B41_V3 is not None:

    pairwise_benchmarks.append(
        "FROZEN_V3"
    )


for benchmark in (
    pairwise_benchmarks
):

    temp = (
        BLOCK41_SUMMARY[
            BLOCK41_SUMMARY[
                "Strategy"
            ]
            ==
            benchmark
        ]
    )


    if temp.empty:
        continue


    benchmark_wealth = float(
        temp[
            "Final_Wealth"
        ]
        .iloc[
            0
        ]
    )


    pairwise_rows.append(
        {
            "Benchmark":
                benchmark,

            "Benchmark_Final_Wealth":
                benchmark_wealth,

            "V4_Leader_Final_Wealth":
                B41_V4_LEADER_WEALTH,

            "V4_minus_Benchmark_pp":
                100.0
                *
                (
                    B41_V4_LEADER_WEALTH
                    -
                    benchmark_wealth
                ),

            "V4_Beats":
                B41_V4_LEADER_WEALTH
                >
                benchmark_wealth,
        }
    )


BLOCK41_PAIRWISE = pd.DataFrame(
    pairwise_rows
)


# ==============================================================================
# 16. PIT-EW AUDIT
# ==============================================================================

BLOCK41_PIT_EW_AUDIT = pd.DataFrame(
    {
        "Metric": [
            "Rebalances",
            "Final wealth",
            "Net return pct",
            "Total turnover",
            "Mean turnover",
            "Mean assets",
            "Minimum assets",
            "Maximum assets",
        ],

        "Value": [
            len(
                BLOCK41_PIT_EW_PATH
            ),

            float(
                BLOCK41_PIT_EW_PATH[
                    "Wealth"
                ]
                .iloc[
                    -1
                ]
            ),

            100.0
            *
            (
                float(
                    BLOCK41_PIT_EW_PATH[
                        "Wealth"
                    ]
                    .iloc[
                        -1
                    ]
                )
                -
                1.0
            ),

            BLOCK41_PIT_EW_PATH[
                "Turnover"
            ]
            .sum(),

            BLOCK41_PIT_EW_PATH[
                "Turnover"
            ]
            .mean(),

            BLOCK41_PIT_EW_PATH[
                "Assets"
            ]
            .mean(),

            BLOCK41_PIT_EW_PATH[
                "Assets"
            ]
            .min(),

            BLOCK41_PIT_EW_PATH[
                "Assets"
            ]
            .max(),
        ],
    }
)


# ==============================================================================
# 17. VISUALIZATION FRAME
# ==============================================================================

BLOCK41_WEALTH_CURVES = pd.DataFrame(
    index=
        B41_MARKET_INDEX
)


for strategy_name, raw_curve in (
    B41_CURVES.items()
):

    curve = (
        pd.Series(
            raw_curve,
            dtype=float,
        )
        .sort_index()
    )


    display_curve = pd.Series(
        np.nan,
        index=
            B41_MARKET_INDEX,
        dtype=float,
    )


    display_curve.loc[
        B41_START_DATE
    ] = 1.0


    common = (
        curve.index
        .intersection(
            B41_MARKET_INDEX
        )
    )


    display_curve.loc[
        common
    ] = curve.loc[
        common
    ]


    BLOCK41_WEALTH_CURVES[
        strategy_name
    ] = (
        display_curve
        .ffill()
    )


# ==============================================================================
# 18. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 118
)

print(
    "BLOCK 41 — FINAL BENCHMARK RESULTS"
)

print(
    "=" * 118
)


print(
    "\n1) FINAL SAME-CALENDAR NET-WEALTH RANKING"
)


display(
    BLOCK41_SUMMARY
    .round(
        6
    )
)


print(
    "\n2) V4 LEADER vs BENCHMARKS"
)


display(
    BLOCK41_PAIRWISE
    .round(
        6
    )
)


print(
    "\n3) BROAD PIT EQUAL-WEIGHT AUDIT"
)


display(
    BLOCK41_PIT_EW_AUDIT
    .round(
        6
    )
)


print(
    "\n4) FROZEN V3 STATUS"
)


if B41_V3 is None:

    print(
        "Frozen V3 same-calendar wealth path "
        "was not found unambiguously."
    )

else:

    print(
        "Frozen V3 source object:",
        B41_V3_SOURCE_OBJECT
    )


# ==============================================================================
# 19. FINAL WEALTH GRAPH
# ==============================================================================

plt.figure(
    figsize=(
        15,
        8,
    )
)


for column in (
    BLOCK41_WEALTH_CURVES.columns
):

    plt.plot(
        BLOCK41_WEALTH_CURVES.index,
        BLOCK41_WEALTH_CURVES[
            column
        ],
        label=
            column,
        linewidth=
            1.8,
    )


plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1,
)


plt.title(
    "Block 41 — Final Same-Calendar Net Wealth Benchmark"
)


plt.xlabel(
    "Date"
)


plt.ylabel(
    "Net Wealth"
)


plt.legend()


plt.grid(
    alpha=0.25
)


plt.show()


# ==============================================================================
# 20. FINAL OBJECTIVE VERDICT
# ==============================================================================

print(
    "\n"
    +
    "=" * 118
)

print(
    "BLOCK 41 — OBJECTIVE VERDICT"
)

print(
    "=" * 118
)


print(
    f"\nV4 portfolio leader    : "
    f"{B41_V4_LEADER}"
)


print(
    f"V4 final wealth        : "
    f"{B41_V4_LEADER_WEALTH:.6f}"
)


print(
    f"\nStrongest benchmark    : "
    f"{B41_STRONGEST_BENCHMARK}"
)


print(
    f"Benchmark final wealth : "
    f"{B41_STRONGEST_BENCHMARK_WEALTH:.6f}"
)


print(
    f"\nV4 minus strongest     : "
    f"{B41_V4_MINUS_BEST_BENCHMARK_PP:+.3f} pp"
)


print(
    f"\nV4 beats strongest     : "
    f"{B41_BEATS_STRONGEST_BENCHMARK}"
)


if B41_BEATS_STRONGEST_BENCHMARK:

    print(
        "\nRESULT:"
    )

    print(
        "V4 PASSES THE PRIMARY NET-WEALTH OBJECTIVE."
    )

else:

    print(
        "\nRESULT:"
    )

    print(
        "V4 FAILS THE PRIMARY NET-WEALTH OBJECTIVE."
    )


print(
    "\nNo model or parameter was changed by this benchmark."
)


print(
    "\n[+] BLOCK 41 COMPLETE."
)


print(
    "[+] NEXT AND FINAL: BLOCK 42 — GO / NO-GO + RESEARCH FREEZE."
)
