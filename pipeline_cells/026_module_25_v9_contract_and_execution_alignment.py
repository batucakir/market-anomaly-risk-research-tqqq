# MODULE 25 — V9 CONTRACT AND EXECUTION ALIGNMENT
# Run in the same notebook, in module order.

# ==============================================================================
# V9 — BLOCK 1
# RESEARCH CONTRACT + TQQQ-RELATIVE TARGET ENGINE
# + EXECUTION-AWARE MARKET STATE
# ==============================================================================
#
# PRIMARY OBJECTIVE
# -----------------
# Maximize NET RELATIVE WEALTH versus TQQQ.
#
# V9 IS A NEW RESEARCH CHALLENGER.
# V8 REMAINS FROZEN AND UNCHANGED.
#
# CORE DESIGN PRINCIPLES
# ----------------------
# - Point-in-time S&P Composite 1500 universe.
# - Existing investability rules remain unchanged.
# - No minimum stock weight.
# - No maximum stock weight.
# - No sector cap.
# - No volatility / drawdown / risk cap.
# - No arbitrary Top-K rule.
# - No cash sleeve.
# - TQQQ remains the benchmark and investable core.
# - QQQ is an investable lower-beta core alternative.
# - Stock alpha is trained directly against TQQQ-relative wealth growth.
# - Execution capacity is represented economically, not through arbitrary
#   position caps.
#
# FIXED TARGET HORIZONS
# ---------------------
# 1D, 1W, 1M, 3M, 6M, 9M, 12M
#
# YTD and since-inception remain evaluation horizons rather than ML targets.
#
# IMPORTANT
# ---------
# This block DOES NOT backtest V9.
# It therefore exposes no V9 performance result that could be used to tune
# the architecture before the model is implemented.
#
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIRED OBJECTS
# ==============================================================================

V9_B1_REQUIRED = [
    "V4_DAILY_PANEL",
    "B38_MIN_PRICE",
    "B38_MIN_MEDIAN_DOLLAR_VOLUME",
    "B38_MIN_VALID_DAYS",
    "B40_TCA_BPS",
]


V9_B1_MISSING = [
    name
    for name in V9_B1_REQUIRED
    if name not in globals()
]


if V9_B1_MISSING:
    raise RuntimeError(
        "V9 Block 1 is missing required objects: "
        f"{V9_B1_MISSING}"
    )


# ==============================================================================
# 1. V9 PRE-DECLARED RESEARCH CONTRACT
# ==============================================================================

V9_VERSION = "V9"

V9_STATUS = "RESEARCH_CHALLENGER"

V9_PRIMARY_OBJECTIVE = (
    "MAX_NET_RELATIVE_WEALTH_VS_TQQQ"
)


# V9 architecture is being designed with information available
# through 2026-09-09.
#
# Therefore historical replay is development research only.

V9_INFORMATION_CUTOFF = pd.Timestamp(
    "2026-09-09"
)

V9_DESIGN_DATE = pd.Timestamp(
    "2026-09-10"
)


# $100k is the fixed research capacity scale.
#
# It is NOT a position cap.
# It is used only to translate portfolio weights into dollar order sizes.

V9_REFERENCE_AUM_USD = 100_000.0


# Preserve the existing baseline transaction-cost component.

V9_BASE_TCA_BPS = float(
    B40_TCA_BPS
)

V9_BASE_TCA_RATE = (
    V9_BASE_TCA_BPS
    /
    10000.0
)


# Square-root market-impact coefficient.
#
# Fixed ex ante at unity.
# It is NOT fitted or selected from V9 backtest performance.
#
# Future stress tests may vary this for diagnostics,
# but V9's main specification remains 1.0.

V9_IMPACT_COEFFICIENT = 1.0


# Existing liquidity-history window.
# Reuse the already-frozen universe convention rather than inventing
# another performance-selected lookback.

V9_LIQUIDITY_LOOKBACK = 60

V9_MIN_VALID_DAYS = int(
    B38_MIN_VALID_DAYS
)


# Model training cadence inherited from the successful V7 architecture.

V9_TRAIN_LOOKBACK_SESSIONS = 252

V9_REFIT_EVERY_SESSIONS = 21

V9_PORTFOLIO_REBALANCE_SESSIONS = 21


# Fixed multi-horizon target family.

V9_TARGET_HORIZONS = {
    "1D": 1,
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "9M": 189,
    "12M": 252,
}


# Final evaluation family.
#
# These are reporting / robustness horizons.
# They are not individually optimized.

V9_EVALUATION_HORIZONS = (
    "1D",
    "1W",
    "1M",
    "3M",
    "6M",
    "9M",
    "12M",
    "YTD",
    "SINCE_INCEPTION",
)


V9_RESEARCH_CONTRACT = {

    "version":
        V9_VERSION,

    "status":
        V9_STATUS,

    "design_date":
        str(V9_DESIGN_DATE.date()),

    "information_cutoff":
        str(V9_INFORMATION_CUTOFF.date()),

    "primary_objective":
        V9_PRIMARY_OBJECTIVE,

    "benchmark":
        "TQQQ",

    "investable_core_assets":
        (
            "TQQQ",
            "QQQ",
        ),

    "stock_universe":
        "POINT_IN_TIME_SP_COMPOSITE_1500",

    "existing_min_price":
        float(B38_MIN_PRICE),

    "existing_min_median_dollar_volume":
        float(
            B38_MIN_MEDIAN_DOLLAR_VOLUME
        ),

    "existing_min_valid_days":
        int(B38_MIN_VALID_DAYS),

    "reference_aum_usd":
        V9_REFERENCE_AUM_USD,

    "minimum_position_weight":
        None,

    "maximum_position_weight":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "volatility_target":
        None,

    "cash_allowed":
        False,

    "top_k_rule":
        None,

    "target_definition":
        (
            "LOG_RELATIVE_WEALTH_GROWTH_VS_TQQQ"
        ),

    "target_horizons":
        V9_TARGET_HORIZONS,

    "training_lookback_sessions":
        V9_TRAIN_LOOKBACK_SESSIONS,

    "refit_every_sessions":
        V9_REFIT_EVERY_SESSIONS,

    "portfolio_rebalance_sessions":
        V9_PORTFOLIO_REBALANCE_SESSIONS,

    "horizon_aggregation":
        (
            "MEDIAN_OF_PREDICTED_LOG_RELATIVE_"
            "GROWTH_PER_SESSION"
        ),

    "alpha_model_policy":
        (
            "ONE_FIXED_HIST_GRADIENT_BOOSTING_"
            "REGRESSOR_PER_HORIZON"
        ),

    "stock_sleeve_objective":
        (
            "MAX_EXPECTED_TQQQ_RELATIVE_GROWTH_"
            "NET_OF_EXECUTION_COST"
        ),

    "base_tca_bps":
        V9_BASE_TCA_BPS,

    "impact_model":
        (
            "SIGMA60_X_SQRT_ORDER_NOTIONAL_OVER_ADV60"
        ),

    "impact_coefficient":
        V9_IMPACT_COEFFICIENT,

    "core_allocator":
        (
            "UNIVERSAL_WEALTH_POSTERIOR_OVER_"
            "TQQQ_QQQ_ALPHA_SIMPLEX"
        ),

    "no_alpha_sleeve_policy":
        (
            "REDIRECT_ALPHA_COMPONENT_TO_TQQQ"
        ),

    "evaluation_horizons":
        V9_EVALUATION_HORIZONS,

    "same_sample_parameter_search":
        False,

    "hindsight_weight_selection":
        False,

    "post_result_parameter_tuning":
        False,
}


# ==============================================================================
# 2. CONTRACT FINGERPRINT
# ==============================================================================

V9_CONTRACT_STRING = json.dumps(
    V9_RESEARCH_CONTRACT,
    sort_keys=True,
    default=str,
)


V9_CONTRACT_FINGERPRINT = (
    hashlib.sha256(
        V9_CONTRACT_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


# ==============================================================================
# 3. CLEAN SOURCE PANEL
# ==============================================================================

V9_SOURCE_PANEL = (
    V4_DAILY_PANEL
    .copy()
)


V9_REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Asset_Type",
    "Adj_Close",
    "Daily_Return",
    "Dollar_Volume",
    "Median_Dollar_Volume_60",
    "Valid_Days_60",
    "Eligible",
]


V9_MISSING_COLUMNS = [
    column
    for column in V9_REQUIRED_COLUMNS
    if column not in V9_SOURCE_PANEL.columns
]


if V9_MISSING_COLUMNS:
    raise RuntimeError(
        "V9 source panel is missing columns: "
        f"{V9_MISSING_COLUMNS}"
    )


V9_SOURCE_PANEL["Date"] = (
    pd.to_datetime(
        V9_SOURCE_PANEL["Date"]
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V9_SOURCE_PANEL["Ticker"] = (
    V9_SOURCE_PANEL["Ticker"]
    .astype(str)
    .str.upper()
    .str.strip()
)


V9_SOURCE_PANEL = (
    V9_SOURCE_PANEL
    .sort_values(
        [
            "Ticker",
            "Date",
        ]
    )
    .reset_index(
        drop=True
    )
)


duplicate_count = int(
    V9_SOURCE_PANEL.duplicated(
        subset=[
            "Ticker",
            "Date",
        ]
    ).sum()
)


if duplicate_count > 0:
    raise RuntimeError(
        "V9 source panel contains duplicate "
        f"ticker-date rows: {duplicate_count}"
    )


# ==============================================================================
# 4. RESEARCH BACKCAST END
# ==============================================================================

V9_RESEARCH_BACKCAST_END = (
    V9_SOURCE_PANEL["Date"].max()
)


# ==============================================================================
# 5. CAUSAL EXECUTION-STATE VARIABLES
# ==============================================================================

V9_SOURCE_PANEL[
    "V9_Abs_Return"
] = (
    V9_SOURCE_PANEL[
        "Daily_Return"
    ]
    .abs()
)


V9_SOURCE_PANEL[
    "V9_Amihud_Daily"
] = (
    V9_SOURCE_PANEL[
        "V9_Abs_Return"
    ]
    /
    V9_SOURCE_PANEL[
        "Dollar_Volume"
    ].replace(
        0.0,
        np.nan,
    )
)


# Trailing realized volatility.

V9_SOURCE_PANEL[
    "V9_Realized_Vol_60"
] = (
    V9_SOURCE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "Daily_Return"
    ]
    .transform(
        lambda series:
            series.rolling(
                window=V9_LIQUIDITY_LOOKBACK,
                min_periods=V9_MIN_VALID_DAYS,
            ).std()
    )
)


# Trailing Amihud illiquidity estimate.
#
# This is a causal diagnostic / execution input.

V9_SOURCE_PANEL[
    "V9_Amihud_60"
] = (
    V9_SOURCE_PANEL
    .groupby(
        "Ticker",
        sort=False,
    )[
        "V9_Amihud_Daily"
    ]
    .transform(
        lambda series:
            series.rolling(
                window=V9_LIQUIDITY_LOOKBACK,
                min_periods=V9_MIN_VALID_DAYS,
            ).median()
    )
)


# Portfolio-size / liquidity relationship.
#
# This does NOT remove a stock from the universe.

V9_SOURCE_PANEL[
    "V9_AUM_to_ADV"
] = (
    V9_REFERENCE_AUM_USD
    /
    V9_SOURCE_PANEL[
        "Median_Dollar_Volume_60"
    ]
)


V9_SOURCE_PANEL[
    "V9_AUM_to_ADV_Pct"
] = (
    100.0
    *
    V9_SOURCE_PANEL[
        "V9_AUM_to_ADV"
    ]
)


# Square-root impact scale for investing the entire research AUM.
#
# For a future order weight |dw|,
#
# impact fraction approximately scales as:
#
#     sigma_60
#     * sqrt(
#           |dw| * AUM / ADV_60
#       )
#
# No position is capped here.

V9_SOURCE_PANEL[
    "V9_Full_AUM_Impact_Scale"
] = (
    V9_IMPACT_COEFFICIENT
    *
    V9_SOURCE_PANEL[
        "V9_Realized_Vol_60"
    ]
    *
    np.sqrt(
        np.maximum(
            V9_SOURCE_PANEL[
                "V9_AUM_to_ADV"
            ],
            0.0,
        )
    )
)


# ==============================================================================
# 6. VERIFY EXISTING ELIGIBILITY LOGIC
# ==============================================================================

V9_ELIGIBLE_STOCK_CHECK = (
    V9_SOURCE_PANEL[
        (
            V9_SOURCE_PANEL[
                "Asset_Type"
            ]
            ==
            "STOCK"
        )
        &
        (
            V9_SOURCE_PANEL[
                "Eligible"
            ]
        )
    ]
    .copy()
)


if V9_ELIGIBLE_STOCK_CHECK.empty:
    raise RuntimeError(
        "No eligible PIT stocks were found."
    )


price_violations = int(
    (
        V9_ELIGIBLE_STOCK_CHECK[
            "Adj_Close"
        ]
        <= 0
    ).sum()
)


liquidity_violations = int(
    (
        V9_ELIGIBLE_STOCK_CHECK[
            "Median_Dollar_Volume_60"
        ]
        <
        float(
            B38_MIN_MEDIAN_DOLLAR_VOLUME
        )
    ).sum()
)


history_violations = int(
    (
        V9_ELIGIBLE_STOCK_CHECK[
            "Valid_Days_60"
        ]
        <
        int(
            B38_MIN_VALID_DAYS
        )
    ).sum()
)


if (
    price_violations
    or liquidity_violations
    or history_violations
):

    raise RuntimeError(
        "Existing universe eligibility integrity "
        "check failed."
    )


# ==============================================================================
# 7. BUILD EXACT TQQQ TRADING CALENDAR
# ==============================================================================

V9_TQQQ_PANEL = (
    V9_SOURCE_PANEL[
        V9_SOURCE_PANEL[
            "Ticker"
        ]
        ==
        "TQQQ"
    ][
        [
            "Date",
            "Adj_Close",
        ]
    ]
    .dropna()
    .drop_duplicates(
        subset=[
            "Date"
        ]
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


if V9_TQQQ_PANEL.empty:
    raise RuntimeError(
        "TQQQ is missing from V9 source data."
    )


V9_CALENDAR = pd.DataFrame(
    {
        "Date":
            V9_TQQQ_PANEL[
                "Date"
            ]
            .copy()
    }
)


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    V9_CALENDAR[
        f"Target_Date_{horizon_name}"
    ] = (
        V9_CALENDAR[
            "Date"
        ]
        .shift(
            -horizon_sessions
        )
    )


# ==============================================================================
# 8. CREATE CURRENT ELIGIBLE STOCK RESEARCH PANEL
# ==============================================================================

V9_BASE_PANEL = (
    V9_SOURCE_PANEL[
        (
            V9_SOURCE_PANEL[
                "Asset_Type"
            ]
            ==
            "STOCK"
        )
        &
        (
            V9_SOURCE_PANEL[
                "Eligible"
            ]
        )
    ]
    .copy()
)


V9_BASE_PANEL = (
    V9_BASE_PANEL
    .merge(
        V9_CALENDAR,
        on="Date",
        how="left",
        validate="many_to_one",
    )
)


# ==============================================================================
# 9. EXACT PRICE LOOKUPS
# ==============================================================================

V9_PRICE_LOOKUP = (
    V9_SOURCE_PANEL[
        [
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    ]
    .set_index(
        [
            "Ticker",
            "Date",
        ]
    )[
        "Adj_Close"
    ]
)


V9_TQQQ_PRICE_BY_DATE = (
    V9_TQQQ_PANEL
    .set_index(
        "Date"
    )[
        "Adj_Close"
    ]
)


# Current TQQQ price aligned with every stock row.

V9_BASE_PANEL[
    "TQQQ_Adj_Close"
] = (
    V9_TQQQ_PRICE_BY_DATE
    .reindex(
        V9_BASE_PANEL[
            "Date"
        ]
        .to_numpy()
    )
    .to_numpy()
)


# ==============================================================================
# 10. BUILD MULTI-HORIZON TQQQ-RELATIVE WEALTH TARGETS
# ==============================================================================

for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_date_column = (
        f"Target_Date_{horizon_name}"
    )


    future_asset_index = pd.MultiIndex.from_arrays(
        [
            V9_BASE_PANEL[
                "Ticker"
            ].to_numpy(),

            V9_BASE_PANEL[
                target_date_column
            ].to_numpy(),
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )


    future_asset_price = (
        V9_PRICE_LOOKUP
        .reindex(
            future_asset_index
        )
        .to_numpy(
            dtype=float
        )
    )


    future_tqqq_price = (
        V9_TQQQ_PRICE_BY_DATE
        .reindex(
            V9_BASE_PANEL[
                target_date_column
            ]
            .to_numpy()
        )
        .to_numpy(
            dtype=float
        )
    )


    current_asset_price = (
        V9_BASE_PANEL[
            "Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    current_tqqq_price = (
        V9_BASE_PANEL[
            "TQQQ_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    valid = (
        np.isfinite(
            current_asset_price
        )
        &
        np.isfinite(
            future_asset_price
        )
        &
        np.isfinite(
            current_tqqq_price
        )
        &
        np.isfinite(
            future_tqqq_price
        )
        &
        (
            current_asset_price > 0
        )
        &
        (
            future_asset_price > 0
        )
        &
        (
            current_tqqq_price > 0
        )
        &
        (
            future_tqqq_price > 0
        )
    )


    asset_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    tqqq_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    relative_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    asset_growth[
        valid
    ] = (
        future_asset_price[
            valid
        ]
        /
        current_asset_price[
            valid
        ]
    )


    tqqq_growth[
        valid
    ] = (
        future_tqqq_price[
            valid
        ]
        /
        current_tqqq_price[
            valid
        ]
    )


    relative_growth[
        valid
    ] = (
        asset_growth[
            valid
        ]
        /
        tqqq_growth[
            valid
        ]
    )


    V9_BASE_PANEL[
        f"Asset_Return_{horizon_name}"
    ] = (
        asset_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"TQQQ_Return_{horizon_name}"
    ] = (
        tqqq_growth
        -
        1.0
    )


    # Arithmetic excess return retained only for diagnostics.

    V9_BASE_PANEL[
        f"Arithmetic_Excess_{horizon_name}"
    ] = (
        V9_BASE_PANEL[
            f"Asset_Return_{horizon_name}"
        ]
        -
        V9_BASE_PANEL[
            f"TQQQ_Return_{horizon_name}"
        ]
    )


    # PRIMARY V9 TARGET:
    #
    #     log(
    #         Asset future wealth
    #         /
    #         TQQQ future wealth
    #     )
    #
    # This is directly aligned with multiplicative
    # relative-wealth maximization.

    V9_BASE_PANEL[
        f"Log_Relative_Wealth_{horizon_name}"
    ] = np.where(
        (
            np.isfinite(
                relative_growth
            )
            &
            (
                relative_growth > 0
            )
        ),
        np.log(
            relative_growth
        ),
        np.nan,
    )


# ==============================================================================
# 11. STRICT TARGET-DATE CAUSALITY CHECK
# ==============================================================================

for horizon_name in V9_TARGET_HORIZONS:

    target_column = (
        f"Target_Date_{horizon_name}"
    )


    valid_dates = (
        V9_BASE_PANEL[
            [
                "Date",
                target_column,
            ]
        ]
        .dropna()
    )


    if (
        valid_dates[
            target_column
        ]
        <=
        valid_dates[
            "Date"
        ]
    ).any():

        raise RuntimeError(
            "Forward target-date causality failure "
            f"for {horizon_name}."
        )


# ==============================================================================
# 12. EXECUTION-STATE COLUMNS
# ==============================================================================

V9_EXECUTION_COLUMNS = [
    "V9_Realized_Vol_60",
    "V9_Amihud_60",
    "V9_AUM_to_ADV",
    "V9_AUM_to_ADV_Pct",
    "V9_Full_AUM_Impact_Scale",
]


# ==============================================================================
# 13. TARGET COVERAGE AUDIT
# ==============================================================================

V9_TARGET_COVERAGE_ROWS = []


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_column = (
        f"Log_Relative_Wealth_{horizon_name}"
    )


    available = (
        V9_BASE_PANEL[
            target_column
        ]
        .notna()
    )


    V9_TARGET_COVERAGE_ROWS.append(
        {
            "Horizon":
                horizon_name,

            "Sessions":
                horizon_sessions,

            "Eligible_Rows":
                len(
                    V9_BASE_PANEL
                ),

            "Target_Rows":
                int(
                    available.sum()
                ),

            "Target_Coverage_Pct":
                100.0
                *
                available.mean(),

            "First_Target_Date":
                V9_BASE_PANEL.loc[
                    available,
                    "Date",
                ].min(),

            "Last_Target_Date":
                V9_BASE_PANEL.loc[
                    available,
                    "Date",
                ].max(),
        }
    )


V9_TARGET_COVERAGE = (
    pd.DataFrame(
        V9_TARGET_COVERAGE_ROWS
    )
    .set_index(
        "Horizon"
    )
)


# ==============================================================================
# 14. LIQUIDITY / CAPACITY AUDIT
# ==============================================================================

V9_LIQUIDITY_AUDIT_SOURCE = (
    V9_BASE_PANEL[
        [
            "Median_Dollar_Volume_60",
            "V9_AUM_to_ADV_Pct",
            "V9_Realized_Vol_60",
            "V9_Amihud_60",
            "V9_Full_AUM_Impact_Scale",
        ]
    ]
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
)


V9_LIQUIDITY_AUDIT = (
    V9_LIQUIDITY_AUDIT_SOURCE
    .describe(
        percentiles=[
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99,
        ]
    )
    .T
)


# ==============================================================================
# 15. DAILY ELIGIBLE UNIVERSE SIZE
# ==============================================================================

V9_DAILY_UNIVERSE_SIZE = (
    V9_BASE_PANEL
    .groupby(
        "Date"
    )[
        "Ticker"
    ]
    .nunique()
)


# ==============================================================================
# 16. MASTER AUDIT
# ==============================================================================

V9_BLOCK1_AUDIT = pd.DataFrame(
    {
        "Metric": [
            "V9 status",
            "Primary objective",
            "Benchmark",
            "Research backcast end",
            "Information cutoff",
            "Reference AUM USD",
            "Existing minimum price",
            "Existing minimum median dollar volume",
            "Existing minimum valid days",
            "Minimum position weight",
            "Maximum position weight",
            "Sector cap",
            "Risk cap",
            "Cash allowed",
            "Target horizons",
            "Training lookback sessions",
            "Refit frequency sessions",
            "Portfolio rebalance sessions",
            "Base TCA bps",
            "Impact coefficient",
            "Eligible PIT stock rows",
            "Unique eligible stocks",
            "Median eligible stocks per date",
            "Minimum eligible stocks per date",
            "Maximum eligible stocks per date",
        ],

        "Value": [
            V9_STATUS,
            V9_PRIMARY_OBJECTIVE,
            "TQQQ",
            V9_RESEARCH_BACKCAST_END,
            V9_INFORMATION_CUTOFF,
            V9_REFERENCE_AUM_USD,
            B38_MIN_PRICE,
            B38_MIN_MEDIAN_DOLLAR_VOLUME,
            B38_MIN_VALID_DAYS,
            "NONE",
            "NONE",
            "NONE",
            "NONE",
            False,
            tuple(
                V9_TARGET_HORIZONS.keys()
            ),
            V9_TRAIN_LOOKBACK_SESSIONS,
            V9_REFIT_EVERY_SESSIONS,
            V9_PORTFOLIO_REBALANCE_SESSIONS,
            V9_BASE_TCA_BPS,
            V9_IMPACT_COEFFICIENT,
            len(V9_BASE_PANEL),
            V9_BASE_PANEL[
                "Ticker"
            ].nunique(),
            V9_DAILY_UNIVERSE_SIZE.median(),
            V9_DAILY_UNIVERSE_SIZE.min(),
            V9_DAILY_UNIVERSE_SIZE.max(),
        ],
    }
)


# ==============================================================================
# 17. FINAL INTEGRITY GATES
# ==============================================================================

if "TQQQ" in set(
    V9_BASE_PANEL[
        "Ticker"
    ]
):
    raise RuntimeError(
        "TQQQ incorrectly entered the stock alpha panel."
    )


if len(V9_BASE_PANEL) == 0:
    raise RuntimeError(
        "V9 base panel is empty."
    )


if (
    V9_DAILY_UNIVERSE_SIZE.median()
    <= 0
):
    raise RuntimeError(
        "V9 daily universe is invalid."
    )


# No arbitrary portfolio restriction may appear in the contract.

for forbidden_key in [
    "minimum_position_weight",
    "maximum_position_weight",
    "sector_cap",
    "risk_cap",
    "top_k_rule",
]:

    if (
        V9_RESEARCH_CONTRACT[
            forbidden_key
        ]
        is not None
    ):

        raise RuntimeError(
            "Forbidden arbitrary V9 constraint detected: "
            f"{forbidden_key}"
        )


# ==============================================================================
# 18. OUTPUT
# ==============================================================================

print("=" * 130)
print("V9 — BLOCK 1")
print("RESEARCH CONTRACT + TQQQ-RELATIVE TARGET ENGINE")
print("=" * 130)


print(
    "\nV9 contract fingerprint:",
    V9_CONTRACT_FINGERPRINT,
)


print(
    "\n1) V9 MASTER AUDIT"
)

display(
    V9_BLOCK1_AUDIT
)


print(
    "\n2) MULTI-HORIZON TARGET COVERAGE"
)

display(
    V9_TARGET_COVERAGE.round(4)
)


print(
    "\n3) LIQUIDITY / CAPACITY STATE"
)

display(
    V9_LIQUIDITY_AUDIT.round(8)
)


print(
    "\n4) DAILY ELIGIBLE STOCK UNIVERSE"
)

display(
    V9_DAILY_UNIVERSE_SIZE
    .describe(
        percentiles=[
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
        ]
    )
    .to_frame(
        "Eligible_Stocks"
    )
)


print("\nINTEGRITY:")
print("[+] Point-in-time stock universe preserved.")
print("[+] Existing liquidity eligibility preserved.")
print("[+] No minimum position size.")
print("[+] No maximum single-name weight.")
print("[+] No sector cap.")
print("[+] No risk cap.")
print("[+] No arbitrary Top-K stock count.")
print("[+] TQQQ-relative wealth targets built causally.")
print("[+] Execution-capacity variables built causally.")
print("[+] NO V9 PERFORMANCE HAS BEEN VIEWED YET.")

print(
    "\nNEXT:"
)

print(
    "V9 BLOCK 2 — FIXED MULTI-HORIZON HGB "
    "ALPHA + EXECUTION-COST-AWARE STOCK SLEEVE."
)

print("=" * 130)
# ==============================================================================
# V9 — BLOCK 1B
# PRE-PERFORMANCE EXECUTION-ALIGNMENT PATCH
# ==============================================================================
#
# IMPORTANT
# ---------
# NO V9 PERFORMANCE HAS BEEN OBSERVED.
#
# This is a causality / execution-alignment correction only.
#
# Signal:
#       close of session t
#
# Execution:
#       close of next trading session t+1
#
# Forward targets:
#       execution close -> execution close + H sessions
#
# This prevents the model from receiving the untradeable t -> t+1 move
# inside its forecast target.
#
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V9_B1B_REQUIRED = [
    "V9_SOURCE_PANEL",
    "V9_TARGET_HORIZONS",
    "V9_RESEARCH_CONTRACT",
    "V9_PRICE_LOOKUP",
    "V9_TQQQ_PANEL",
]


V9_B1B_MISSING = [
    name
    for name in V9_B1B_REQUIRED
    if name not in globals()
]


if V9_B1B_MISSING:
    raise RuntimeError(
        "V9 Block 1B is missing required objects: "
        f"{V9_B1B_MISSING}"
    )


# ==============================================================================
# 1. LOCK EXECUTION CONVENTION
# ==============================================================================

V9_SIGNAL_TO_EXECUTION_LAG = 1

V9_EXECUTION_CONVENTION = (
    "SIGNAL_AT_CLOSE_T__EXECUTE_AT_CLOSE_T_PLUS_1"
)


V9_RESEARCH_CONTRACT[
    "signal_information_time"
] = "SESSION_T_CLOSE"


V9_RESEARCH_CONTRACT[
    "execution_lag_sessions"
] = V9_SIGNAL_TO_EXECUTION_LAG


V9_RESEARCH_CONTRACT[
    "execution_price"
] = "NEXT_SESSION_ADJ_CLOSE"


V9_RESEARCH_CONTRACT[
    "target_start"
] = "EXECUTION_SESSION_ADJ_CLOSE"


V9_RESEARCH_CONTRACT[
    "target_end"
] = (
    "EXECUTION_SESSION_PLUS_H_SESSIONS_ADJ_CLOSE"
)


# ==============================================================================
# 2. REBUILD TQQQ CALENDAR
# ==============================================================================

V9_CALENDAR = (
    V9_TQQQ_PANEL[
        [
            "Date",
        ]
    ]
    .drop_duplicates()
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


V9_CALENDAR[
    "Execution_Date"
] = (
    V9_CALENDAR[
        "Date"
    ]
    .shift(
        -V9_SIGNAL_TO_EXECUTION_LAG
    )
)


for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    V9_CALENDAR[
        f"Target_End_Date_{horizon_name}"
    ] = (
        V9_CALENDAR[
            "Date"
        ]
        .shift(
            -(
                V9_SIGNAL_TO_EXECUTION_LAG
                +
                horizon_sessions
            )
        )
    )


# ==============================================================================
# 3. REBUILD ELIGIBLE STOCK PANEL
# ==============================================================================

V9_BASE_PANEL = (
    V9_SOURCE_PANEL[
        (
            V9_SOURCE_PANEL[
                "Asset_Type"
            ]
            ==
            "STOCK"
        )
        &
        (
            V9_SOURCE_PANEL[
                "Eligible"
            ]
        )
    ]
    .copy()
)


V9_BASE_PANEL = (
    V9_BASE_PANEL
    .merge(
        V9_CALENDAR,
        on="Date",
        how="left",
        validate="many_to_one",
    )
)


# ==============================================================================
# 4. TQQQ PRICE LOOKUP
# ==============================================================================

V9_TQQQ_PRICE_BY_DATE = (
    V9_TQQQ_PANEL
    .set_index(
        "Date"
    )[
        "Adj_Close"
    ]
)


# ==============================================================================
# 5. EXECUTION PRICES
# ==============================================================================

execution_stock_index = (
    pd.MultiIndex.from_arrays(
        [
            V9_BASE_PANEL[
                "Ticker"
            ].to_numpy(),

            V9_BASE_PANEL[
                "Execution_Date"
            ].to_numpy(),
        ],
        names=[
            "Ticker",
            "Date",
        ],
    )
)


V9_BASE_PANEL[
    "Execution_Adj_Close"
] = (
    V9_PRICE_LOOKUP
    .reindex(
        execution_stock_index
    )
    .to_numpy(
        dtype=float
    )
)


V9_BASE_PANEL[
    "TQQQ_Execution_Adj_Close"
] = (
    V9_TQQQ_PRICE_BY_DATE
    .reindex(
        V9_BASE_PANEL[
            "Execution_Date"
        ].to_numpy()
    )
    .to_numpy(
        dtype=float
    )
)


# ==============================================================================
# 6. REBUILD ALL FORWARD TARGETS
# ==============================================================================

for horizon_name, horizon_sessions in (
    V9_TARGET_HORIZONS.items()
):

    end_date_column = (
        f"Target_End_Date_{horizon_name}"
    )


    future_stock_index = (
        pd.MultiIndex.from_arrays(
            [
                V9_BASE_PANEL[
                    "Ticker"
                ].to_numpy(),

                V9_BASE_PANEL[
                    end_date_column
                ].to_numpy(),
            ],
            names=[
                "Ticker",
                "Date",
            ],
        )
    )


    future_asset_price = (
        V9_PRICE_LOOKUP
        .reindex(
            future_stock_index
        )
        .to_numpy(
            dtype=float
        )
    )


    future_tqqq_price = (
        V9_TQQQ_PRICE_BY_DATE
        .reindex(
            V9_BASE_PANEL[
                end_date_column
            ].to_numpy()
        )
        .to_numpy(
            dtype=float
        )
    )


    execution_asset_price = (
        V9_BASE_PANEL[
            "Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    execution_tqqq_price = (
        V9_BASE_PANEL[
            "TQQQ_Execution_Adj_Close"
        ]
        .to_numpy(
            dtype=float
        )
    )


    valid = (
        np.isfinite(
            execution_asset_price
        )
        &
        np.isfinite(
            future_asset_price
        )
        &
        np.isfinite(
            execution_tqqq_price
        )
        &
        np.isfinite(
            future_tqqq_price
        )
        &
        (
            execution_asset_price > 0
        )
        &
        (
            future_asset_price > 0
        )
        &
        (
            execution_tqqq_price > 0
        )
        &
        (
            future_tqqq_price > 0
        )
    )


    asset_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    tqqq_growth = np.full(
        len(V9_BASE_PANEL),
        np.nan,
        dtype=float,
    )


    asset_growth[
        valid
    ] = (
        future_asset_price[
            valid
        ]
        /
        execution_asset_price[
            valid
        ]
    )


    tqqq_growth[
        valid
    ] = (
        future_tqqq_price[
            valid
        ]
        /
        execution_tqqq_price[
            valid
        ]
    )


    V9_BASE_PANEL[
        f"Asset_Return_{horizon_name}"
    ] = (
        asset_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"TQQQ_Return_{horizon_name}"
    ] = (
        tqqq_growth
        -
        1.0
    )


    V9_BASE_PANEL[
        f"Arithmetic_Excess_{horizon_name}"
    ] = (
        V9_BASE_PANEL[
            f"Asset_Return_{horizon_name}"
        ]
        -
        V9_BASE_PANEL[
            f"TQQQ_Return_{horizon_name}"
        ]
    )


    relative_growth = (
        asset_growth
        /
        tqqq_growth
    )


    V9_BASE_PANEL[
        f"Log_Relative_Wealth_{horizon_name}"
    ] = np.where(
        (
            np.isfinite(
                relative_growth
            )
            &
            (
                relative_growth > 0
            )
        ),
        np.log(
            relative_growth
        ),
        np.nan,
    )


# ==============================================================================
# 7. CAUSALITY VALIDATION
# ==============================================================================

for horizon_name in (
    V9_TARGET_HORIZONS
):

    target_end = (
        V9_BASE_PANEL[
            f"Target_End_Date_{horizon_name}"
        ]
    )


    valid = (
        target_end.notna()
        &
        V9_BASE_PANEL[
            "Execution_Date"
        ].notna()
    )


    if (
        V9_BASE_PANEL.loc[
            valid,
            "Execution_Date",
        ]
        <=
        V9_BASE_PANEL.loc[
            valid,
            "Date",
        ]
    ).any():

        raise RuntimeError(
            "Execution lag causality failure."
        )


    if (
        target_end.loc[
            valid
        ]
        <=
        V9_BASE_PANEL.loc[
            valid,
            "Execution_Date",
        ]
    ).any():

        raise RuntimeError(
            "Forward target causality failure "
            f"for {horizon_name}."
        )


# ==============================================================================
# 8. REBUILD TARGET COVERAGE
# ==============================================================================

coverage_rows = []


for horizon_name, sessions in (
    V9_TARGET_HORIZONS.items()
):

    target_column = (
        f"Log_Relative_Wealth_{horizon_name}"
    )


    available = (
        V9_BASE_PANEL[
            target_column
        ]
        .notna()
    )


    coverage_rows.append(
        {
            "Horizon":
                horizon_name,

            "Sessions":
                sessions,

            "Target_Rows":
                int(
                    available.sum()
                ),

            "Coverage_Pct":
                100.0
                *
                available.mean(),

            "Last_Usable_Signal_Date":
                V9_BASE_PANEL.loc[
                    available,
                    "Date",
                ].max(),
        }
    )


V9_TARGET_COVERAGE = (
    pd.DataFrame(
        coverage_rows
    )
    .set_index(
        "Horizon"
    )
)


# ==============================================================================
# 9. RE-FINGERPRINT CONTRACT
# ==============================================================================

V9_CONTRACT_STRING = (
    json.dumps(
        V9_RESEARCH_CONTRACT,
        sort_keys=True,
        default=str,
    )
)


V9_CONTRACT_FINGERPRINT = (
    hashlib.sha256(
        V9_CONTRACT_STRING.encode(
            "utf-8"
        )
    ).hexdigest()
)


# ==============================================================================
# 10. OUTPUT
# ==============================================================================

print("=" * 125)
print("V9 — BLOCK 1B")
print("PRE-PERFORMANCE EXECUTION-ALIGNMENT PATCH")
print("=" * 125)


print(
    "\nExecution convention :",
    V9_EXECUTION_CONVENTION,
)


print(
    "New contract fingerprint:",
    V9_CONTRACT_FINGERPRINT,
)


print(
    "\nTARGET COVERAGE AFTER EXECUTION ALIGNMENT"
)


display(
    V9_TARGET_COVERAGE.round(4)
)


print(
    "\n[+] SIGNAL DATE AND EXECUTION DATE ARE NOW SEPARATED."
)

print(
    "[+] ALL ML TARGETS BEGIN AT THE FIRST EXECUTABLE SESSION."
)

print(
    "[+] NO V9 PERFORMANCE HAS BEEN OBSERVED."
)

print("=" * 125)
