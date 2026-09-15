# MODULE 47 — V16 $10,000 MULTI-HORIZON REPORT
# Run in the same notebook, in module order.

# ==============================================================================
# V16 — $10,000 MULTI-HORIZON WEALTH / RETURN LINE DASHBOARD
# ==============================================================================
#
# REPORTING ONLY — THE FROZEN V16 STRATEGY IS NOT CHANGED.
#
# Investment horizons:
#   SINCE INCEPTION
#   2 YEARS
#   12 MONTHS
#   YTD
#   9 MONTHS
#   6 MONTHS
#   3 MONTHS
#   1 MONTH
#   1 WEEK
#   1 DAY
#
# Outputs:
#   1. Multi-horizon return table (%)
#   2. Ending value of a hypothetical $10,000 investment
#   3. Dollar profit / loss table
#   4. Exact start-date audit
#   5. Strategy ranking by horizon
#   6. V16-specific $10,000 scorecard
#   7. Line chart — return by horizon
#   8. Line chart — ending value of $10,000 by horizon
#   9. Full-history $10,000 wealth path
#  10. V16 minus TQQQ active-return line chart
#  11. V16 minus V8 active-return line chart
#
# IMPORTANT:
# "SINCE INCEPTION" means the exact common start date available across the
# strategies in the daily comparison panel. No artificial 3-year label is used.
#
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.ticker import FuncFormatter, MultipleLocator
from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

if "V16Q_DAILY_CURVES" not in globals():

    raise RuntimeError(
        "V16Q_DAILY_CURVES was not found. "
        "Run the V16 deep-dive dashboard block first."
    )


V16MH_INITIAL_CAPITAL = 10_000.0


print("=" * 140)

print(
    "V16 — $10,000 MULTI-HORIZON WEALTH / RETURN LINE DASHBOARD"
)

print("=" * 140)

print(
    "\nREPORTING ONLY — THE FROZEN V16 STRATEGY IS NOT CHANGED."
)

print(
    f"Initial capital per horizon: "
    f"${V16MH_INITIAL_CAPITAL:,.0f}"
)


# ==============================================================================
# 1. CLEAN EXACT DAILY CURVES
# ==============================================================================

V16MH_CURVES = (
    V16Q_DAILY_CURVES
    .copy()
    .sort_index()
)


v16mh_index = pd.DatetimeIndex(
    V16MH_CURVES.index
)


if v16mh_index.tz is not None:

    v16mh_index = (
        v16mh_index
        .tz_convert(
            "America/New_York"
        )
        .tz_localize(None)
    )


V16MH_CURVES.index = (
    v16mh_index.normalize()
)


# Keep the final observation if duplicate calendar dates exist.

V16MH_CURVES = (
    V16MH_CURVES
    .groupby(
        level=0
    )
    .last()
    .sort_index()
)


# Add constant-cash benchmark.

V16MH_CURVES[
    "CASH"
] = 1.0


# Remove unusable columns.

v16mh_usable_columns = []


for column in V16MH_CURVES.columns:

    series = (
        V16MH_CURVES[
            column
        ]
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .dropna()
    )

    if len(series) >= 2:

        v16mh_usable_columns.append(
            column
        )


V16MH_CURVES = (
    V16MH_CURVES[
        v16mh_usable_columns
    ]
)


# ==============================================================================
# 2. STRATEGY DISPLAY ORDER
# ==============================================================================

V16MH_PREFERRED_ORDER = [

    "V16",
    "V8",
    "V7",
    "TQQQ",
    "QQQ",
    "SPY",
    "CASH",

]


v16mh_ordered_columns = [

    column

    for column
    in V16MH_PREFERRED_ORDER

    if column
    in V16MH_CURVES.columns

]


v16mh_ordered_columns += [

    column

    for column
    in V16MH_CURVES.columns

    if column
    not in v16mh_ordered_columns

]


V16MH_CURVES = (
    V16MH_CURVES[
        v16mh_ordered_columns
    ]
)


print(
    "\nStrategies included:"
)


for column in V16MH_CURVES.columns:

    print(
        f"  - {column}"
    )


# ==============================================================================
# 3. EXACT COMMON COMPARISON CALENDAR
# ==============================================================================

v16mh_first_dates = []
v16mh_last_dates = []


for column in V16MH_CURVES.columns:

    if column == "CASH":
        continue

    series = (
        V16MH_CURVES[
            column
        ]
        .dropna()
    )

    if series.empty:
        continue

    v16mh_first_dates.append(
        series.index.min()
    )

    v16mh_last_dates.append(
        series.index.max()
    )


if (
    not v16mh_first_dates
    or
    not v16mh_last_dates
):

    raise RuntimeError(
        "No valid common comparison calendar could be constructed."
    )


V16MH_COMMON_START = max(
    v16mh_first_dates
)

V16MH_COMMON_END = min(
    v16mh_last_dates
)


V16MH_CURVES = (
    V16MH_CURVES.loc[
        (
            V16MH_CURVES.index
            >=
            V16MH_COMMON_START
        )
        &
        (
            V16MH_CURVES.index
            <=
            V16MH_COMMON_END
        )
    ]
    .copy()
)


print(
    f"\nCommon comparison start : "
    f"{V16MH_COMMON_START.date()}"
)

print(
    f"Common comparison end   : "
    f"{V16MH_COMMON_END.date()}"
)

print(
    f"Calendar observations   : "
    f"{len(V16MH_CURVES):,}"
)


# ==============================================================================
# 4. HELPER FUNCTIONS
# ==============================================================================

def v16mh_last_observation_on_or_before(
    series,
    target_date,
):

    """
    Return the last valid observation on or before a requested date.
    """

    clean = (
        series
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

    eligible = (
        clean.loc[
            clean.index
            <=
            pd.Timestamp(
                target_date
            )
        ]
    )

    if eligible.empty:

        return (
            None,
            np.nan,
        )

    return (
        eligible.index[-1],
        float(
            eligible.iloc[-1]
        ),
    )


def v16mh_first_observation_on_or_after(
    series,
    target_date,
):

    """
    Return the first valid observation on or after a requested date.
    """

    clean = (
        series
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

    eligible = (
        clean.loc[
            clean.index
            >=
            pd.Timestamp(
                target_date
            )
        ]
    )

    if eligible.empty:

        return (
            None,
            np.nan,
        )

    return (
        eligible.index[0],
        float(
            eligible.iloc[0]
        ),
    )


def v16mh_get_anchor(
    horizon,
    end_date,
):

    """
    Convert a horizon label into the corresponding calendar anchor.
    """

    if horizon == "2Y":

        return (
            end_date
            -
            pd.DateOffset(
                years=2
            )
        )

    if horizon == "12M":

        return (
            end_date
            -
            pd.DateOffset(
                months=12
            )
        )

    if horizon == "YTD":

        return pd.Timestamp(
            year=
                end_date.year
                -
                1,
            month=12,
            day=31,
        )

    if horizon == "9M":

        return (
            end_date
            -
            pd.DateOffset(
                months=9
            )
        )

    if horizon == "6M":

        return (
            end_date
            -
            pd.DateOffset(
                months=6
            )
        )

    if horizon == "3M":

        return (
            end_date
            -
            pd.DateOffset(
                months=3
            )
        )

    if horizon == "1M":

        return (
            end_date
            -
            pd.DateOffset(
                months=1
            )
        )

    if horizon == "1W":

        return (
            end_date
            -
            pd.DateOffset(
                weeks=1
            )
        )

    return None


def v16mh_nice_step(
    maximum_value,
    candidates,
):

    """
    Select readable horizontal-grid spacing.
    """

    if (
        not np.isfinite(
            maximum_value
        )
        or
        maximum_value <= 0
    ):

        return candidates[0]

    target = (
        maximum_value
        /
        8.0
    )

    for step in candidates:

        if step >= target:

            return step

    return candidates[-1]


# ==============================================================================
# 5. HORIZON DEFINITIONS
# ==============================================================================

V16MH_HORIZONS = [

    "SINCE INCEPTION",
    "2Y",
    "12M",
    "YTD",
    "9M",
    "6M",
    "3M",
    "1M",
    "1W",
    "1D",

]


# ==============================================================================
# 6. CALCULATE EXACT MULTI-HORIZON ECONOMICS
# ==============================================================================

v16mh_rows = []


for horizon in V16MH_HORIZONS:

    for strategy in V16MH_CURVES.columns:

        series = (
            V16MH_CURVES[
                strategy
            ]
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

        if series.empty:
            continue


        (
            actual_end_date,
            end_nav,
        ) = (
            v16mh_last_observation_on_or_before(
                series,
                V16MH_COMMON_END,
            )
        )


        if actual_end_date is None:
            continue


        sufficient_history = True

        requested_start_date = (
            pd.NaT
        )


        # ----------------------------------------------------------------------
        # Since inception
        # ----------------------------------------------------------------------

        if horizon == "SINCE INCEPTION":

            requested_start_date = (
                V16MH_COMMON_START
            )

            (
                actual_start_date,
                start_nav,
            ) = (
                v16mh_first_observation_on_or_after(
                    series,
                    V16MH_COMMON_START,
                )
            )


        # ----------------------------------------------------------------------
        # One trading day
        # ----------------------------------------------------------------------

        elif horizon == "1D":

            end_location = (
                series.index.get_indexer(
                    [
                        actual_end_date
                    ]
                )[0]
            )

            if end_location < 1:

                sufficient_history = False

                actual_start_date = (
                    pd.NaT
                )

                start_nav = (
                    np.nan
                )

            else:

                requested_start_date = (
                    series.index[
                        end_location
                        -
                        1
                    ]
                )

                actual_start_date = (
                    series.index[
                        end_location
                        -
                        1
                    ]
                )

                start_nav = float(
                    series.iloc[
                        end_location
                        -
                        1
                    ]
                )


        # ----------------------------------------------------------------------
        # All other horizons
        # ----------------------------------------------------------------------

        else:

            requested_start_date = (
                v16mh_get_anchor(
                    horizon,
                    actual_end_date,
                )
            )

            if (
                requested_start_date
                <
                V16MH_COMMON_START
            ):

                sufficient_history = False

                actual_start_date = (
                    pd.NaT
                )

                start_nav = (
                    np.nan
                )

            else:

                (
                    actual_start_date,
                    start_nav,
                ) = (
                    v16mh_last_observation_on_or_before(
                        series,
                        requested_start_date,
                    )
                )

                if actual_start_date is None:

                    sufficient_history = False


        # ----------------------------------------------------------------------
        # Economics
        # ----------------------------------------------------------------------

        if (
            not sufficient_history
            or
            not np.isfinite(
                start_nav
            )
            or
            start_nav <= 0
            or
            not np.isfinite(
                end_nav
            )
            or
            end_nav <= 0
        ):

            wealth_multiple = (
                np.nan
            )

            return_pct = (
                np.nan
            )

            final_value_usd = (
                np.nan
            )

            profit_usd = (
                np.nan
            )

        else:

            wealth_multiple = (
                end_nav
                /
                start_nav
            )

            return_pct = (
                wealth_multiple
                -
                1.0
            ) * 100.0

            final_value_usd = (
                V16MH_INITIAL_CAPITAL
                *
                wealth_multiple
            )

            profit_usd = (
                final_value_usd
                -
                V16MH_INITIAL_CAPITAL
            )


        v16mh_rows.append(
            {

                "Horizon":
                    horizon,

                "Strategy":
                    strategy,

                "Requested_Start_Date":
                    requested_start_date,

                "Actual_Start_Date":
                    actual_start_date,

                "Actual_End_Date":
                    actual_end_date,

                "Start_NAV":
                    start_nav,

                "End_NAV":
                    end_nav,

                "Return_Pct":
                    return_pct,

                "Wealth_Multiple":
                    wealth_multiple,

                "Initial_Capital_USD":
                    V16MH_INITIAL_CAPITAL,

                "Final_Value_USD":
                    final_value_usd,

                "Profit_USD":
                    profit_usd,

                "Sufficient_History":
                    sufficient_history,

            }
        )


V16MH_DETAIL = pd.DataFrame(
    v16mh_rows
)


# ==============================================================================
# 7. RETURN TABLE
# ==============================================================================

V16MH_RETURN_TABLE = (
    V16MH_DETAIL
    .pivot(
        index=
            "Horizon",
        columns=
            "Strategy",
        values=
            "Return_Pct",
    )
    .reindex(
        V16MH_HORIZONS
    )
    .reindex(
        columns=
            v16mh_ordered_columns
    )
)


# ==============================================================================
# 8. FINAL-VALUE TABLE
# ==============================================================================

V16MH_VALUE_TABLE = (
    V16MH_DETAIL
    .pivot(
        index=
            "Horizon",
        columns=
            "Strategy",
        values=
            "Final_Value_USD",
    )
    .reindex(
        V16MH_HORIZONS
    )
    .reindex(
        columns=
            v16mh_ordered_columns
    )
)


# ==============================================================================
# 9. PROFIT TABLE
# ==============================================================================

V16MH_PROFIT_TABLE = (
    V16MH_DETAIL
    .pivot(
        index=
            "Horizon",
        columns=
            "Strategy",
        values=
            "Profit_USD",
    )
    .reindex(
        V16MH_HORIZONS
    )
    .reindex(
        columns=
            v16mh_ordered_columns
    )
)


# ==============================================================================
# 10. START-DATE TABLE
# ==============================================================================

V16MH_START_DATE_TABLE = (
    V16MH_DETAIL
    .pivot(
        index=
            "Horizon",
        columns=
            "Strategy",
        values=
            "Actual_Start_Date",
    )
    .reindex(
        V16MH_HORIZONS
    )
    .reindex(
        columns=
            v16mh_ordered_columns
    )
)


# ==============================================================================
# 11. STRATEGY RANKING BY HORIZON
# ==============================================================================

v16mh_ranking_rows = []


for horizon in V16MH_HORIZONS:

    horizon_returns = (
        V16MH_RETURN_TABLE
        .loc[
            horizon
        ]
        .dropna()
        .sort_values(
            ascending=False
        )
    )

    for rank, (
        strategy,
        return_pct,
    ) in enumerate(
        horizon_returns.items(),
        start=1,
    ):

        v16mh_ranking_rows.append(
            {

                "Horizon":
                    horizon,

                "Rank":
                    rank,

                "Strategy":
                    strategy,

                "Return_Pct":
                    float(
                        return_pct
                    ),

                "Final_Value_USD":
                    float(
                        V16MH_VALUE_TABLE.loc[
                            horizon,
                            strategy,
                        ]
                    ),

            }
        )


V16MH_RANKING_TABLE = pd.DataFrame(
    v16mh_ranking_rows
)


# ==============================================================================
# 12. DISPLAY — RETURN TABLE
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "1) MULTI-HORIZON NET RETURNS (%)"
)

print(
    "=" * 140
)


display(
    V16MH_RETURN_TABLE.round(
        2
    )
)


# ==============================================================================
# 13. DISPLAY — ENDING VALUE OF $10,000
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "2) ENDING VALUE OF A $10,000 INVESTMENT"
)

print(
    "=" * 140
)


V16MH_VALUE_DISPLAY = (
    V16MH_VALUE_TABLE.copy()
)


for column in V16MH_VALUE_DISPLAY.columns:

    V16MH_VALUE_DISPLAY[
        column
    ] = (
        V16MH_VALUE_DISPLAY[
            column
        ]
        .map(
            lambda value:
                f"${value:,.0f}"
                if pd.notna(
                    value
                )
                else "N/A"
        )
    )


display(
    V16MH_VALUE_DISPLAY
)


# ==============================================================================
# 14. DISPLAY — DOLLAR PROFIT / LOSS
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "3) DOLLAR PROFIT / LOSS FROM $10,000"
)

print(
    "=" * 140
)


V16MH_PROFIT_DISPLAY = (
    V16MH_PROFIT_TABLE.copy()
)


for column in V16MH_PROFIT_DISPLAY.columns:

    V16MH_PROFIT_DISPLAY[
        column
    ] = (
        V16MH_PROFIT_DISPLAY[
            column
        ]
        .map(
            lambda value:
                f"${value:+,.0f}"
                if pd.notna(
                    value
                )
                else "N/A"
        )
    )


display(
    V16MH_PROFIT_DISPLAY
)


# ==============================================================================
# 15. DISPLAY — EXACT START DATES
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "4) EXACT START DATE USED FOR EACH HORIZON"
)

print(
    "=" * 140
)


V16MH_DATE_DISPLAY = (
    V16MH_START_DATE_TABLE.copy()
)


for column in V16MH_DATE_DISPLAY.columns:

    V16MH_DATE_DISPLAY[
        column
    ] = (
        V16MH_DATE_DISPLAY[
            column
        ]
        .map(
            lambda value:
                pd.Timestamp(
                    value
                )
                .strftime(
                    "%Y-%m-%d"
                )
                if pd.notna(
                    value
                )
                else "N/A"
        )
    )


display(
    V16MH_DATE_DISPLAY
)


# ==============================================================================
# 16. DISPLAY — FULL RANKING
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "5) STRATEGY RANKING BY INVESTMENT HORIZON"
)

print(
    "=" * 140
)


display(
    V16MH_RANKING_TABLE.round(
        2
    )
)


# ==============================================================================
# 17. V16-SPECIFIC SCORECARD
# ==============================================================================

if "V16" in V16MH_RETURN_TABLE.columns:

    V16MH_V16_SCORECARD = pd.DataFrame(
        {

            "Return_Pct":
                V16MH_RETURN_TABLE[
                    "V16"
                ],

            "Final_Value_USD":
                V16MH_VALUE_TABLE[
                    "V16"
                ],

            "Profit_USD":
                V16MH_PROFIT_TABLE[
                    "V16"
                ],

        }
    )


    if "V8" in V16MH_RETURN_TABLE.columns:

        V16MH_V16_SCORECARD[
            "Excess_vs_V8_pp"
        ] = (
            V16MH_RETURN_TABLE[
                "V16"
            ]
            -
            V16MH_RETURN_TABLE[
                "V8"
            ]
        )


    if "TQQQ" in V16MH_RETURN_TABLE.columns:

        V16MH_V16_SCORECARD[
            "Excess_vs_TQQQ_pp"
        ] = (
            V16MH_RETURN_TABLE[
                "V16"
            ]
            -
            V16MH_RETURN_TABLE[
                "TQQQ"
            ]
        )


    print(
        "\n"
        +
        "=" * 140
    )

    print(
        "6) V16 $10,000 INVESTMENT SCORECARD"
    )

    print(
        "=" * 140
    )


    display(
        V16MH_V16_SCORECARD.round(
            2
        )
    )


# ==============================================================================
# 18. LINE CHART — MULTI-HORIZON RETURNS
# ==============================================================================

v16mh_x = np.arange(
    len(
        V16MH_HORIZONS
    )
)


v16mh_return_values = (
    V16MH_RETURN_TABLE
    .to_numpy(
        dtype=float
    )
)


v16mh_finite_return_values = (
    v16mh_return_values[
        np.isfinite(
            v16mh_return_values
        )
    ]
)


v16mh_max_abs_return = (
    float(
        np.max(
            np.abs(
                v16mh_finite_return_values
            )
        )
    )
    if len(
        v16mh_finite_return_values
    )
    else 1.0
)


v16mh_return_step = (
    v16mh_nice_step(
        v16mh_max_abs_return,
        [
            1,
            2,
            5,
            10,
            20,
            25,
            50,
            100,
            200,
            500,
        ],
    )
)


fig, ax = plt.subplots(
    figsize=(
        20,
        10
    )
)


for strategy in V16MH_RETURN_TABLE.columns:

    values = (
        V16MH_RETURN_TABLE[
            strategy
        ]
        .astype(float)
        .to_numpy()
    )


    ax.plot(
        v16mh_x,
        values,
        marker="o",
        markersize=7,
        linewidth=(
            3.0
            if strategy == "V16"
            else 2.0
        ),
        label=
            strategy,
    )


    for x_value, y_value in zip(
        v16mh_x,
        values,
    ):

        if np.isfinite(
            y_value
        ):

            ax.annotate(
                f"{y_value:+.1f}%",
                xy=(
                    x_value,
                    y_value
                ),
                xytext=(
                    0,
                    8
                ),
                textcoords=
                    "offset points",
                ha=
                    "center",
                fontsize=8,
            )


ax.axhline(
    0,
    linestyle="--",
    linewidth=1.3,
)


ax.set_xticks(
    v16mh_x
)


ax.set_xticklabels(
    V16MH_HORIZONS
)


ax.set_title(
    "V16 — MULTI-HORIZON NET RETURN COMPARISON",
    fontsize=17,
    fontweight="bold",
)


ax.set_xlabel(
    "Investment Horizon"
)


ax.set_ylabel(
    "Net Return (%)"
)


ax.yaxis.set_major_locator(
    MultipleLocator(
        v16mh_return_step
    )
)


ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.60,
)


ax.grid(
    axis="x",
    linestyle=":",
    linewidth=0.5,
    alpha=0.25,
)


ax.legend(
    ncol=3
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 19. LINE CHART — ENDING VALUE OF $10,000
# ==============================================================================

v16mh_value_values = (
    V16MH_VALUE_TABLE
    .to_numpy(
        dtype=float
    )
)


v16mh_finite_values = (
    v16mh_value_values[
        np.isfinite(
            v16mh_value_values
        )
    ]
)


v16mh_max_value = (
    float(
        np.max(
            v16mh_finite_values
        )
    )
    if len(
        v16mh_finite_values
    )
    else
        V16MH_INITIAL_CAPITAL
)


v16mh_value_step = (
    v16mh_nice_step(
        v16mh_max_value,
        [
            10_000,
            25_000,
            50_000,
            10_000,
            200_000,
            250_000,
            500_000,
            1_000_000,
            2_000_000,
        ],
    )
)


fig, ax = plt.subplots(
    figsize=(
        20,
        10
    )
)


for strategy in V16MH_VALUE_TABLE.columns:

    values = (
        V16MH_VALUE_TABLE[
            strategy
        ]
        .astype(float)
        .to_numpy()
    )


    ax.plot(
        v16mh_x,
        values,
        marker="o",
        markersize=7,
        linewidth=(
            3.0
            if strategy == "V16"
            else 2.0
        ),
        label=
            strategy,
    )


    for x_value, y_value in zip(
        v16mh_x,
        values,
    ):

        if np.isfinite(
            y_value
        ):

            ax.annotate(
                f"${y_value / 1000:,.0f}K",
                xy=(
                    x_value,
                    y_value
                ),
                xytext=(
                    0,
                    8
                ),
                textcoords=
                    "offset points",
                ha=
                    "center",
                fontsize=8,
            )


ax.axhline(
    V16MH_INITIAL_CAPITAL,
    linestyle="--",
    linewidth=1.3,
    label=
        "$100K Initial Capital",
)


ax.set_xticks(
    v16mh_x
)


ax.set_xticklabels(
    V16MH_HORIZONS
)


ax.set_title(
    "$10,000 INVESTED — ENDING PORTFOLIO VALUE BY HORIZON",
    fontsize=17,
    fontweight="bold",
)


ax.set_xlabel(
    "Investment Horizon"
)


ax.set_ylabel(
    "Ending Portfolio Value (USD)"
)


ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda value, position:
            f"${value / 1000:,.0f}K"
    )
)


ax.yaxis.set_major_locator(
    MultipleLocator(
        v16mh_value_step
    )
)


ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.60,
)


ax.grid(
    axis="x",
    linestyle=":",
    linewidth=0.5,
    alpha=0.25,
)


ax.legend(
    ncol=3
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 20. FULL-HISTORY DAILY WEALTH PATH — $10,000 INVESTED AT INCEPTION
# ==============================================================================

V16MH_FULL_WEALTH_PATHS = pd.DataFrame(
    index=
        V16MH_CURVES.index
)


for strategy in V16MH_CURVES.columns:

    series = (
        V16MH_CURVES[
            strategy
        ]
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


    if series.empty:
        continue


    (
        start_date,
        start_nav,
    ) = (
        v16mh_first_observation_on_or_after(
            series,
            V16MH_COMMON_START,
        )
    )


    if (
        start_date is None
        or
        not np.isfinite(
            start_nav
        )
        or
        start_nav <= 0
    ):

        continue


    normalized = (
        V16MH_INITIAL_CAPITAL
        *
        series
        /
        start_nav
    )


    V16MH_FULL_WEALTH_PATHS[
        strategy
    ] = (
        normalized
        .reindex(
            V16MH_FULL_WEALTH_PATHS.index
        )
    )


v16mh_full_values = (
    V16MH_FULL_WEALTH_PATHS
    .to_numpy(
        dtype=float
    )
)


v16mh_full_finite = (
    v16mh_full_values[
        np.isfinite(
            v16mh_full_values
        )
    ]
)


v16mh_full_max_value = (
    float(
        np.max(
            v16mh_full_finite
        )
    )
    if len(
        v16mh_full_finite
    )
    else
        V16MH_INITIAL_CAPITAL
)


v16mh_full_value_step = (
    v16mh_nice_step(
        v16mh_full_max_value,
        [
            10_000,
            25_000,
            50_000,
            10_000,
            200_000,
            250_000,
            500_000,
            1_000_000,
            2_000_000,
        ],
    )
)


fig, ax = plt.subplots(
    figsize=(
        20,
        10
    )
)


for strategy in (
    V16MH_FULL_WEALTH_PATHS.columns
):

    ax.plot(
        V16MH_FULL_WEALTH_PATHS.index,
        V16MH_FULL_WEALTH_PATHS[
            strategy
        ],
        linewidth=(
            3.0
            if strategy == "V16"
            else 2.0
        ),
        label=
            strategy,
    )


ax.axhline(
    V16MH_INITIAL_CAPITAL,
    linestyle="--",
    linewidth=1.3,
)


ax.set_title(
    "$10,000 INVESTED FROM THE BEGINNING OF THE COMMON DATA PERIOD",
    fontsize=17,
    fontweight="bold",
)


ax.set_xlabel(
    "Date"
)


ax.set_ylabel(
    "Portfolio Value (USD)"
)


ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda value, position:
            f"${value / 1000:,.0f}K"
    )
)


ax.yaxis.set_major_locator(
    MultipleLocator(
        v16mh_full_value_step
    )
)


ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.60,
)


ax.grid(
    axis="x",
    linestyle=":",
    linewidth=0.5,
    alpha=0.20,
)


ax.legend(
    ncol=3
)


plt.tight_layout()

plt.show()


# ==============================================================================
# 21. V16 MINUS TQQQ — ACTIVE RETURN BY HORIZON
# ==============================================================================

if (
    "V16"
    in V16MH_RETURN_TABLE.columns
    and
    "TQQQ"
    in V16MH_RETURN_TABLE.columns
):

    V16MH_V16_MINUS_TQQQ = (
        V16MH_RETURN_TABLE[
            "V16"
        ]
        -
        V16MH_RETURN_TABLE[
            "TQQQ"
        ]
    )


    v16mh_active_values = (
        V16MH_V16_MINUS_TQQQ
        .astype(float)
        .to_numpy()
    )


    finite_active = (
        v16mh_active_values[
            np.isfinite(
                v16mh_active_values
            )
        ]
    )


    v16mh_active_max = (
        float(
            np.max(
                np.abs(
                    finite_active
                )
            )
        )
        if len(
            finite_active
        )
        else 1.0
    )


    v16mh_active_step = (
        v16mh_nice_step(
            v16mh_active_max,
            [
                1,
                2,
                5,
                10,
                20,
                25,
                50,
                100,
            ],
        )
    )


    fig, ax = plt.subplots(
        figsize=(
            18,
            8
        )
    )


    ax.plot(
        v16mh_x,
        v16mh_active_values,
        marker="o",
        markersize=8,
        linewidth=2.5,
    )


    for x_value, y_value in zip(
        v16mh_x,
        v16mh_active_values,
    ):

        if np.isfinite(
            y_value
        ):

            ax.annotate(
                f"{y_value:+.2f} pp",
                xy=(
                    x_value,
                    y_value
                ),
                xytext=(
                    0,
                    9
                ),
                textcoords=
                    "offset points",
                ha=
                    "center",
                fontsize=9,
            )


    ax.axhline(
        0,
        linestyle="--",
        linewidth=1.3,
    )


    ax.set_xticks(
        v16mh_x
    )


    ax.set_xticklabels(
        V16MH_HORIZONS
    )


    ax.set_title(
        "V16 MINUS TQQQ — ACTIVE RETURN BY INVESTMENT HORIZON",
        fontsize=17,
        fontweight="bold",
    )


    ax.set_xlabel(
        "Investment Horizon"
    )


    ax.set_ylabel(
        "V16 − TQQQ (Percentage Points)"
    )


    ax.yaxis.set_major_locator(
        MultipleLocator(
            v16mh_active_step
        )
    )


    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.8,
        alpha=0.60,
    )


    ax.grid(
        axis="x",
        linestyle=":",
        linewidth=0.5,
        alpha=0.20,
    )


    plt.tight_layout()

    plt.show()


# ==============================================================================
# 22. V16 MINUS V8 — ACTIVE RETURN BY HORIZON
# ==============================================================================

if (
    "V16"
    in V16MH_RETURN_TABLE.columns
    and
    "V8"
    in V16MH_RETURN_TABLE.columns
):

    V16MH_V16_MINUS_V8 = (
        V16MH_RETURN_TABLE[
            "V16"
        ]
        -
        V16MH_RETURN_TABLE[
            "V8"
        ]
    )


    v16mh_v8_active_values = (
        V16MH_V16_MINUS_V8
        .astype(float)
        .to_numpy()
    )


    finite_v8_active = (
        v16mh_v8_active_values[
            np.isfinite(
                v16mh_v8_active_values
            )
        ]
    )


    v16mh_v8_active_max = (
        float(
            np.max(
                np.abs(
                    finite_v8_active
                )
            )
        )
        if len(
            finite_v8_active
        )
        else 1.0
    )


    v16mh_v8_active_step = (
        v16mh_nice_step(
            v16mh_v8_active_max,
            [
                0.25,
                0.5,
                1,
                2,
                5,
                10,
                20,
                25,
                50,
            ],
        )
    )


    fig, ax = plt.subplots(
        figsize=(
            18,
            8
        )
    )


    ax.plot(
        v16mh_x,
        v16mh_v8_active_values,
        marker="o",
        markersize=8,
        linewidth=2.5,
    )


    for x_value, y_value in zip(
        v16mh_x,
        v16mh_v8_active_values,
    ):

        if np.isfinite(
            y_value
        ):

            ax.annotate(
                f"{y_value:+.2f} pp",
                xy=(
                    x_value,
                    y_value
                ),
                xytext=(
                    0,
                    9
                ),
                textcoords=
                    "offset points",
                ha=
                    "center",
                fontsize=9,
            )


    ax.axhline(
        0,
        linestyle="--",
        linewidth=1.3,
    )


    ax.set_xticks(
        v16mh_x
    )


    ax.set_xticklabels(
        V16MH_HORIZONS
    )


    ax.set_title(
        "V16 MINUS V8 — ACTIVE RETURN BY INVESTMENT HORIZON",
        fontsize=17,
        fontweight="bold",
    )


    ax.set_xlabel(
        "Investment Horizon"
    )


    ax.set_ylabel(
        "V16 − V8 (Percentage Points)"
    )


    ax.yaxis.set_major_locator(
        MultipleLocator(
            v16mh_v8_active_step
        )
    )


    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.8,
        alpha=0.60,
    )


    ax.grid(
        axis="x",
        linestyle=":",
        linewidth=0.5,
        alpha=0.20,
    )


    plt.tight_layout()

    plt.show()


# ==============================================================================
# 23. CHAMPION MATRIX — WHO WINS EACH HORIZON?
# ==============================================================================

V16MH_CHAMPION_ROWS = []


for horizon in V16MH_HORIZONS:

    valid = (
        V16MH_RETURN_TABLE
        .loc[
            horizon
        ]
        .dropna()
    )


    # Cash is useful as a benchmark but should not hide the risky-strategy winner.
    risky = (
        valid.drop(
            labels=[
                "CASH"
            ],
            errors="ignore"
        )
    )


    if risky.empty:

        continue


    winner = (
        risky.idxmax()
    )

    winner_return = float(
        risky.max()
    )


    row = {

        "Horizon":
            horizon,

        "Winner":
            winner,

        "Winner_Return_Pct":
            winner_return,

        "V16_Is_Winner":
            winner == "V16",

    }


    if "V16" in valid.index:

        row[
            "V16_Return_Pct"
        ] = float(
            valid[
                "V16"
            ]
        )


    if "V8" in valid.index:

        row[
            "V16_Minus_V8_pp"
        ] = float(
            valid.get(
                "V16",
                np.nan
            )
            -
            valid[
                "V8"
            ]
        )


    if "TQQQ" in valid.index:

        row[
            "V16_Minus_TQQQ_pp"
        ] = float(
            valid.get(
                "V16",
                np.nan
            )
            -
            valid[
                "TQQQ"
            ]
        )


    V16MH_CHAMPION_ROWS.append(
        row
    )


V16MH_CHAMPION_TABLE = pd.DataFrame(
    V16MH_CHAMPION_ROWS
)


print(
    "\n"
    +
    "=" * 140
)

print(
    "7) HORIZON CHAMPION MATRIX"
)

print(
    "=" * 140
)


display(
    V16MH_CHAMPION_TABLE.round(
        2
    )
)


# ==============================================================================
# 24. FINAL TEXT SCORECARD
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "$10,000 MULTI-HORIZON SCORECARD"
)

print(
    "=" * 140
)


print(
    f"\nCommon start date : "
    f"{V16MH_COMMON_START.date()}"
)

print(
    f"Common end date   : "
    f"{V16MH_COMMON_END.date()}"
)

print(
    f"Initial capital   : "
    f"${V16MH_INITIAL_CAPITAL:,.0f}"
)


if "V16" in V16MH_RETURN_TABLE.columns:

    print(
        "\nV16 MULTI-HORIZON RESULTS"
    )


    for horizon in V16MH_HORIZONS:

        return_pct = (
            V16MH_RETURN_TABLE.loc[
                horizon,
                "V16",
            ]
        )

        final_value = (
            V16MH_VALUE_TABLE.loc[
                horizon,
                "V16",
            ]
        )

        profit = (
            V16MH_PROFIT_TABLE.loc[
                horizon,
                "V16",
            ]
        )


        if pd.isna(
            return_pct
        ):

            print(
                f"{horizon:>18} : "
                "N/A — insufficient history"
            )

        else:

            text = (
                f"{horizon:>18} : "
                f"{return_pct:+8.2f}%"
                f" | Final = ${final_value:,.0f}"
                f" | P/L = ${profit:+,.0f}"
            )


            if (
                "V8"
                in V16MH_RETURN_TABLE.columns
                and
                pd.notna(
                    V16MH_RETURN_TABLE.loc[
                        horizon,
                        "V8",
                    ]
                )
            ):

                excess_v8 = (
                    return_pct
                    -
                    V16MH_RETURN_TABLE.loc[
                        horizon,
                        "V8",
                    ]
                )

                text += (
                    f" | vs V8 = "
                    f"{excess_v8:+.2f} pp"
                )


            if (
                "TQQQ"
                in V16MH_RETURN_TABLE.columns
                and
                pd.notna(
                    V16MH_RETURN_TABLE.loc[
                        horizon,
                        "TQQQ",
                    ]
                )
            ):

                excess_tqqq = (
                    return_pct
                    -
                    V16MH_RETURN_TABLE.loc[
                        horizon,
                        "TQQQ",
                    ]
                )

                text += (
                    f" | vs TQQQ = "
                    f"{excess_tqqq:+.2f} pp"
                )


            print(
                text
            )

from pathlib import Path
from IPython.display import display


print("\n" + "=" * 140)
print("MODULE 47 — OFFICIAL ACCOUNTING CORRECTION")
print("=" * 140)


# ==============================================================================
# 1. REQUIRED FROZEN RESULTS
# ==============================================================================

V16MH_FIX_REQUIRED = [
    "RESTORED_VERSION_RESULTS",
    "V16MH_RETURN_TABLE",
    "V16MH_VALUE_TABLE",
    "V16MH_START_DATE_TABLE",
]

V16MH_FIX_MISSING = [
    name
    for name in V16MH_FIX_REQUIRED
    if name not in globals()
]

if V16MH_FIX_MISSING:
    raise RuntimeError(
        "Module 47 accounting correction is missing required objects: "
        f"{V16MH_FIX_MISSING}"
    )

for strategy in ["V8", "V16", "TQQQ"]:
    if strategy not in RESTORED_VERSION_RESULTS:
        raise RuntimeError(
            f"Official result registry is missing {strategy}."
        )


# ==============================================================================
# 2. HISTORICAL REPLICATION GATE
# ==============================================================================

V16MH_FIX_HISTORICAL_EXPECTED_6DP = {
    "V8": 4.184169,
    "V16": 4.365780,
    "TQQQ": 3.563433,
}

V16MH_FIX_REPLICATION_AUDIT = pd.DataFrame(
    [
        {
            "Strategy": strategy,
            "Current_Run_Final_Wealth": float(
                RESTORED_VERSION_RESULTS[strategy]["final_wealth"]
            ),
            "Historical_Expected_6dp": expected,
            "Matches_6dp": (
                round(
                    float(
                        RESTORED_VERSION_RESULTS[strategy]["final_wealth"]
                    ),
                    6,
                )
                == expected
            ),
        }
        for strategy, expected in V16MH_FIX_HISTORICAL_EXPECTED_6DP.items()
    ]
)

if not bool(V16MH_FIX_REPLICATION_AUDIT["Matches_6dp"].all()):
    raise RuntimeError(
        "Official V8/V16/TQQQ replication gate failed. "
        "No reporting correction was applied."
    )


# V8 and V16 may be compared directly only under identical dates and accounting.
v8_result = RESTORED_VERSION_RESULTS["V8"]
v16_result = RESTORED_VERSION_RESULTS["V16"]

V16MH_FIX_SAME_BASIS = (
    pd.Timestamp(v8_result["first_execution"])
    == pd.Timestamp(v16_result["first_execution"])
    and pd.Timestamp(v8_result["end"])
    == pd.Timestamp(v16_result["end"])
    and str(v8_result["basis"])
    == str(v16_result["basis"])
)

if not V16MH_FIX_SAME_BASIS:
    raise RuntimeError(
        "Official V8 and V16 results do not share the same dates and accounting basis."
    )

print("\n1) OFFICIAL HISTORICAL REPLICATION GATE")
display(V16MH_FIX_REPLICATION_AUDIT.round(6))


# ==============================================================================
# 3. OFFICIAL SINCE-INCEPTION VALUES
# ==============================================================================

V16MH_FIX_INITIAL_CAPITAL = 10_000.0

V16MH_OFFICIAL_SINCE_INCEPTION = pd.DataFrame(
    [
        {
            "Strategy": strategy,
            "Start": pd.Timestamp(result["first_execution"]).date(),
            "End": pd.Timestamp(result["end"]).date(),
            "Final_Wealth": float(result["final_wealth"]),
            "Net_Return_Pct": 100.0 * (
                float(result["final_wealth"]) - 1.0
            ),
            "Ending_Value_USD": V16MH_FIX_INITIAL_CAPITAL
            * float(result["final_wealth"]),
            "Profit_Loss_USD": V16MH_FIX_INITIAL_CAPITAL
            * (float(result["final_wealth"]) - 1.0),
            "Accounting": str(result["basis"]),
        }
        for strategy, result in [
            ("V16", RESTORED_VERSION_RESULTS["V16"]),
            ("V8", RESTORED_VERSION_RESULTS["V8"]),
            ("TQQQ", RESTORED_VERSION_RESULTS["TQQQ"]),
        ]
    ]
).sort_values(
    "Final_Wealth",
    ascending=False,
).reset_index(drop=True)

V16MH_OFFICIAL_SINCE_INCEPTION.insert(
    0,
    "Rank",
    np.arange(1, len(V16MH_OFFICIAL_SINCE_INCEPTION) + 1),
)

V16MH_OFFICIAL_V16_V8 = pd.DataFrame(
    [
        {
            "V8_Ending_Value_USD": V16MH_FIX_INITIAL_CAPITAL
            * float(v8_result["final_wealth"]),
            "V16_Ending_Value_USD": V16MH_FIX_INITIAL_CAPITAL
            * float(v16_result["final_wealth"]),
            "V16_Minus_V8_USD": V16MH_FIX_INITIAL_CAPITAL
            * (
                float(v16_result["final_wealth"])
                - float(v8_result["final_wealth"])
            ),
            "V16_Minus_V8_Return_pp": 100.0
            * (
                float(v16_result["final_wealth"])
                - float(v8_result["final_wealth"])
            ),
            "V16_Over_V8_Relative_Wealth_Pct": 100.0
            * (
                float(v16_result["final_wealth"])
                / float(v8_result["final_wealth"])
                - 1.0
            ),
        }
    ]
)

print("\n2) OFFICIAL $10,000 SINCE-INCEPTION RESULTS")
display(V16MH_OFFICIAL_SINCE_INCEPTION.round(6))

print("\n3) OFFICIAL V16 VS V8 — IDENTICAL CLOSE/ADDITIVE-TCA BASIS")
display(V16MH_OFFICIAL_V16_V8.round(6))


# ==============================================================================
# 4. AUDIT THE EARLIER MODULE-47 SINCE-INCEPTION DISPLAY
# ==============================================================================

V16MH_FIX_PRIOR_DISPLAY_AUDIT_ROWS = []

for strategy in ["V16", "V8", "TQQQ"]:
    official_value = (
        V16MH_FIX_INITIAL_CAPITAL
        * float(RESTORED_VERSION_RESULTS[strategy]["final_wealth"])
    )

    prior_value = np.nan

    if (
        "SINCE INCEPTION" in V16MH_VALUE_TABLE.index
        and strategy in V16MH_VALUE_TABLE.columns
    ):
        prior_value = float(
            V16MH_VALUE_TABLE.loc[
                "SINCE INCEPTION",
                strategy,
            ]
        )

    source_note = (
        "Official close-ledger path"
        if strategy != "V8"
        else "Earlier Module-47 V8 column used the original open-based daily path"
    )

    V16MH_FIX_PRIOR_DISPLAY_AUDIT_ROWS.append(
        {
            "Strategy": strategy,
            "Earlier_Module47_USD": prior_value,
            "Official_USD": official_value,
            "Earlier_Minus_Official_USD": (
                prior_value - official_value
                if np.isfinite(prior_value)
                else np.nan
            ),
            "Explanation": source_note,
        }
    )

V16MH_FIX_PRIOR_DISPLAY_AUDIT = pd.DataFrame(
    V16MH_FIX_PRIOR_DISPLAY_AUDIT_ROWS
)

print("\n4) EARLIER MODULE-47 DISPLAY AUDIT")
display(V16MH_FIX_PRIOR_DISPLAY_AUDIT.round(6))

print(
    "[i] The earlier since-inception normalization divided every series by "
    "its first already-invested daily mark, removing the first period's move."
)
print(
    "[i] Its V8 daily column came from the original open-based V8 diagnostic, "
    "so it was not the official close-ledger V8 comparator."
)


# ==============================================================================
# 5. DAILY-HORIZON COMPARABILITY AUDIT
# ==============================================================================

V16MH_DAILY_HORIZON_AUDIT_ROWS = []

for horizon in V16MH_RETURN_TABLE.index:
    if horizon == "SINCE INCEPTION":
        continue

    v16_return = (
        float(V16MH_RETURN_TABLE.loc[horizon, "V16"])
        if "V16" in V16MH_RETURN_TABLE.columns
        and pd.notna(V16MH_RETURN_TABLE.loc[horizon, "V16"])
        else np.nan
    )

    tqqq_return = (
        float(V16MH_RETURN_TABLE.loc[horizon, "TQQQ"])
        if "TQQQ" in V16MH_RETURN_TABLE.columns
        and pd.notna(V16MH_RETURN_TABLE.loc[horizon, "TQQQ"])
        else np.nan
    )

    v16_start = pd.NaT
    tqqq_start = pd.NaT

    if horizon in V16MH_START_DATE_TABLE.index:
        if "V16" in V16MH_START_DATE_TABLE.columns:
            v16_start = pd.to_datetime(
                V16MH_START_DATE_TABLE.loc[horizon, "V16"],
                errors="coerce",
            )
        if "TQQQ" in V16MH_START_DATE_TABLE.columns:
            tqqq_start = pd.to_datetime(
                V16MH_START_DATE_TABLE.loc[horizon, "TQQQ"],
                errors="coerce",
            )

    comparable = bool(
        pd.notna(v16_start)
        and pd.notna(tqqq_start)
        and v16_start == tqqq_start
        and np.isfinite(v16_return)
        and np.isfinite(tqqq_return)
    )

    V16MH_DAILY_HORIZON_AUDIT_ROWS.append(
        {
            "Horizon": horizon,
            "V16_Start": (
                v16_start.date()
                if pd.notna(v16_start)
                else pd.NaT
            ),
            "TQQQ_Start": (
                tqqq_start.date()
                if pd.notna(tqqq_start)
                else pd.NaT
            ),
            "Same_Start_Date": comparable,
            "V16_Return_Pct": (
                v16_return
                if comparable
                else np.nan
            ),
            "TQQQ_Return_Pct": (
                tqqq_return
                if comparable
                else np.nan
            ),
            "V16_Minus_TQQQ_pp": (
                v16_return - tqqq_return
                if comparable
                else np.nan
            ),
            "Status": (
                "COMPARABLE"
                if comparable
                else "UNAVAILABLE — DAILY START DATES DIFFER"
            ),
        }
    )

V16MH_DAILY_HORIZON_AUDIT = pd.DataFrame(
    V16MH_DAILY_HORIZON_AUDIT_ROWS
).set_index("Horizon")

print("\n5) DAILY-HORIZON V16 VS TQQQ COMPARABILITY")
display(V16MH_DAILY_HORIZON_AUDIT.round(6))

if (
    "1D" in V16MH_DAILY_HORIZON_AUDIT.index
    and not bool(
        V16MH_DAILY_HORIZON_AUDIT.loc[
            "1D",
            "Same_Start_Date",
        ]
    )
):
    print(
        "[i] The earlier V16 1D figure is withdrawn because the prior exact "
        "daily V16 mark is missing."
    )

if (
    "1W" in V16MH_DAILY_HORIZON_AUDIT.index
    and not bool(
        V16MH_DAILY_HORIZON_AUDIT.loc[
            "1W",
            "Same_Start_Date",
        ]
    )
):
    print(
        "[i] The earlier V16 1W figure is withdrawn because its actual start "
        "date differs from the benchmark start date."
    )


# ==============================================================================
# 6. OFFICIAL EVENT-MARK WEALTH CHART
# ==============================================================================

fig, ax = plt.subplots(
    figsize=(16, 8)
)

V16MH_OFFICIAL_EVENT_PATHS = {}

for strategy, color, width in [
    ("V16", "tab:blue", 3.0),
    ("V8", "tab:orange", 2.4),
    ("TQQQ", "tab:green", 2.0),
]:
    result = RESTORED_VERSION_RESULTS[strategy]
    marks = (
        result["marks"]
        .copy()
        .sort_values("Date")
    )
    marks["Date"] = pd.to_datetime(marks["Date"])

    plot_dates = [
        pd.Timestamp(result["first_execution"])
    ] + list(marks["Date"])

    plot_values = V16MH_FIX_INITIAL_CAPITAL * np.r_[
        1.0,
        marks["Wealth"].to_numpy(dtype=float),
    ]

    official_path = pd.DataFrame(
        {
            "Date": plot_dates,
            "Value_USD": plot_values,
        }
    ).drop_duplicates(
        "Date",
        keep="last",
    ).sort_values("Date")

    V16MH_OFFICIAL_EVENT_PATHS[strategy] = official_path

    ax.plot(
        official_path["Date"],
        official_path["Value_USD"],
        marker="o" if strategy in ["V16", "V8"] else None,
        markersize=4,
        linewidth=width,
        color=color,
        label=(
            f"{strategy} — ${official_path['Value_USD'].iloc[-1]:,.2f}"
        ),
    )

ax.axhline(
    V16MH_FIX_INITIAL_CAPITAL,
    color="gray",
    linestyle="--",
    linewidth=1,
)

ax.set_title(
    "$10,000 — OFFICIAL SAME-BASIS EVENT-MARK WEALTH",
    fontsize=15,
    fontweight="bold",
)
ax.set_xlabel("Valuation Date")
ax.set_ylabel("Portfolio Value (USD)")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
plt.show()


# ==============================================================================
# 7. SAVE CORRECTED REPORTING TABLES
# ==============================================================================

V16MH_FIX_REPORT_DIR = Path("restored_reports")
V16MH_FIX_REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

V16MH_OFFICIAL_SINCE_INCEPTION.to_csv(
    V16MH_FIX_REPORT_DIR / "official_since_inception_10000.csv",
    index=False,
)

V16MH_OFFICIAL_V16_V8.to_csv(
    V16MH_FIX_REPORT_DIR / "official_v16_vs_v8_10000.csv",
    index=False,
)

V16MH_FIX_PRIOR_DISPLAY_AUDIT.to_csv(
    V16MH_FIX_REPORT_DIR / "module47_prior_display_audit.csv",
    index=False,
)

V16MH_DAILY_HORIZON_AUDIT.to_csv(
    V16MH_FIX_REPORT_DIR / "daily_horizon_comparability.csv",
)

fig.savefig(
    V16MH_FIX_REPORT_DIR / "official_v16_v8_tqqq_10000.png",
    dpi=180,
    bbox_inches="tight",
)

for strategy, path in V16MH_OFFICIAL_EVENT_PATHS.items():
    path.to_csv(
        V16MH_FIX_REPORT_DIR
        / f"official_{strategy.lower()}_event_wealth_10000.csv",
        index=False,
    )


print("\n" + "=" * 140)
print("CORRECTED REPORTING VERDICT")
print("=" * 140)
print(
    f"Official V16 final wealth : {float(v16_result['final_wealth']):.6f}"
)
print(
    f"Official V8 final wealth  : {float(v8_result['final_wealth']):.6f}"
)
print(
    "V16 minus V8             : "
    f"{100.0 * (float(v16_result['final_wealth']) - float(v8_result['final_wealth'])):+.6f} pp"
)
print(
    "[+] The official chart now terminates at the frozen V16 and V8 results."
)
print(
    "[+] Earlier Module-47 tables remain preserved as diagnostics and are not "
    "used as official since-inception results."
)
print(
    "[+] No strategy object, parameter, target, or frozen fingerprint changed."
)
print(
    f"[+] Corrected reports saved to {V16MH_FIX_REPORT_DIR.resolve()}"
)
print("=" * 140)

# ==============================================================================
# 25. FINAL INTEGRITY
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "INTEGRITY"
)

print(
    "=" * 140
)

print(
    "[+] Frozen V16 architecture unchanged."
)

print(
    "[+] Frozen V8 comparator unchanged."
)

print(
    "[+] Exact daily curves from V16Q_DAILY_CURVES used."
)

print(
    "[+] No model fitted."
)

print(
    "[+] No parameter changed."
)

print(
    "[+] No residual-momentum rule changed."
)

print(
    "[+] No lambda retuning."
)

print(
    "[+] No performance-derived trading rule."
)

print(
    "[+] $10,000 figures are reporting transformations only."
)

print(
    "[+] SINCE INCEPTION uses the exact common comparison start date."
)

print(
    "[+] V16 TRUE OOS status is unchanged."
)

print(
    "\n[+] V16 MULTI-HORIZON $10,000 LINE DASHBOARD COMPLETE."
)

print("=" * 140)
