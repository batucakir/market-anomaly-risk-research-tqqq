# ==============================================================================
# MODULE 13 — V4 MASTER ARCHITECTURE / ABSOLUTE-RETURN OBJECTIVE FREEZE
# Historical Block 37
# ==============================================================================

from dataclasses import dataclass, asdict
import hashlib
import json
import pandas as pd


# ==============================================================================
# 0. RECOVER EXACT HISTORICAL PARENT LINEAGE
# ==============================================================================

V3_RESEARCH_FINGERPRINT = (
    "d4eed6f0f5b158f6e33417feecf58a7"
    "af9f6b03b5173e90472037920f262c181"
)

EXPECTED_V4_MASTER_FINGERPRINT = (
    "7f2b6040db974ee5d1df151d9fa49cab"
    "79dea945cd5fe19d442821a35b7c7bd8"
)


# ==============================================================================
# 1. PARENT RESEARCH LINEAGE
# ==============================================================================

if "V3_RESEARCH_FINGERPRINT" not in globals():

    raise RuntimeError(
        "BLOCK 37 requires V3_RESEARCH_FINGERPRINT from the frozen V3 branch."
    )


V4_PARENT_FINGERPRINT = (
    V3_RESEARCH_FINGERPRINT
)


# ==============================================================================
# 2. FINAL PROJECT OBJECTIVE
# ==============================================================================

V4_PROJECT_OBJECTIVE = """
Build a causal multi-asset US-market trading system whose primary objective is
to maximize out-of-sample NET portfolio wealth.

At every decision time the system must:

1. define the currently investable US-market universe causally,
2. estimate multi-horizon expected absolute returns,
3. estimate forward asset risk and cross-asset covariance,
4. account for current holdings and transaction costs,
5. allow allocation to cash / defensive assets when risky opportunities are poor,
6. optimize portfolio weights for expected NET return,
7. allow concentration when economically justified,
8. treat TQQQ as a normal investable candidate rather than a benchmark-only asset,
9. evaluate all architecture changes strictly out of sample,
10. compare final wealth against QQQ, TQQQ, passive baskets and prior V3.
""".strip()


# ==============================================================================
# 3. V4 MASTER ARCHITECTURE
# ==============================================================================

V4_ARCHITECTURE = {

    "Universe":
        (
            "Broad causal US-listed liquid-equity / ETF universe. "
            "The old fixed 38-asset universe is benchmark-only."
        ),

    "Universe_Selection":
        (
            "Eligibility based on information available at each historical "
            "timestamp: liquidity, price, data depth and data quality. "
            "Never future return."
        ),

    "Primary_Alpha":
        "Multi-horizon expected ABSOLUTE return",

    "Primary_Horizons":
        (
            "1 trading session, 5 trading sessions, "
            "20 trading sessions"
        ),

    "Cross_Sectional_Information":
        (
            "May be used as predictive information, but the portfolio objective "
            "remains absolute net wealth."
        ),

    "H3_Role":
        (
            "Auxiliary / diagnostic short-horizon signal only. "
            "NOT the primary portfolio alpha engine."
        ),

    "Alpha_Model_Research":
        (
            "Predeclared regularized linear baseline plus one nonlinear "
            "challenger. Model promotion requires OOS economic value-add."
        ),

    "Model_Selection":
        (
            "Portfolio-level OOS NET wealth is the final criterion; "
            "IC alone cannot promote a model."
        ),

    "Forward_Risk":
        "Causal forward volatility forecast",

    "Dependence":
        "Shrinkage covariance / correlation estimation",

    "Risk_Control":
        "Portfolio-level forecast-risk budget only",

    "Portfolio_Objective":
        "Expected portfolio return minus expected transaction cost",

    "Long_Only":
        True,

    "Single_Name_Cap":
        "NONE",

    "Sector_Cap":
        "NONE",

    "Cash_Allowed":
        True,

    "Forced_Risky_Investment":
        False,

    "TQQQ":
        "NORMAL INVESTABLE CANDIDATE",

    "Portfolio_Leverage":
        (
            "No explicit margin leverage in V4 baseline. "
            "Leveraged ETFs may provide embedded leverage."
        ),

    "Holdings_State":
        "Current drift-adjusted holdings enter every optimization",

    "Transaction_Cost":
        "Explicit turnover-dependent trading cost",

    "Execution":
        (
            "Signal uses only completed information; "
            "execution occurs after signal availability."
        ),

    "Validation":
        "Strict chronological walk-forward OOS",

    "Primary_Metric":
        "Final NET portfolio wealth",

    "Secondary_Metrics":
        (
            "CAGR, max drawdown, Sharpe, turnover, "
            "cost drag and benchmark-relative wealth"
        ),
}


# ==============================================================================
# 4. V4 BASELINE PORTFOLIO POLICY
# ==============================================================================

@dataclass(frozen=True)
class V4MasterConfig:

    horizon_1d_sessions: int = 1

    horizon_5d_sessions: int = 5

    horizon_20d_sessions: int = 20

    long_only: bool = True

    allow_cash: bool = True

    fully_invested_including_cash: bool = True

    max_name_weight: object = None

    max_sector_weight: object = None

    portfolio_risk_cap_multiplier: float = 2.00

    decision_tca_bps: float = 2.00

    tqqq_is_investable: bool = True

    cash_is_investable: bool = True


V4_MASTER_CONFIG = (
    V4MasterConfig()
)


# ==============================================================================
# 5. V4 ASSET CLASS POLICY
# ==============================================================================

V4_ASSET_POLICY = {

    "COMMON_STOCK":
        True,

    "LIQUID_STANDARD_ETF":
        True,

    "TQQQ":
        True,

    "CASH":
        True,

    "OPTIONS":
        False,

    "FUTURES":
        False,

    "SHORT_SELLING":
        False,

    "MARGIN_LEVERAGE":
        False,
}


# ==============================================================================
# 6. PORTFOLIO OBJECTIVE
# ==============================================================================

V4_OPTIMIZATION_OBJECTIVE = r"""
At decision time t:

            maximize_w

                  mu_t' w
                - TC(w, w_previous)

subject to:

            w_i >= 0

            sum(risky weights) + w_cash = 1

            portfolio forecast risk <= risk budget

            no hard single-name cap

            no hard sector cap

where:

    mu_t
        = causal multi-horizon expected absolute return

    TC(...)
        = expected transaction-cost penalty

    w_previous
        = drift-adjusted current holdings
""".strip()


# ==============================================================================
# 7. WHAT V4 EXPLICITLY REJECTS
# ==============================================================================

V4_REJECTED_ARCHITECTURE = [

    "Fixed 38 assets as the final production universe.",

    "H3 as the sole or dominant alpha horizon.",

    "Optimizing Information Coefficient instead of portfolio wealth.",

    "Mandatory 100% risky-asset exposure.",

    "Hard 20% single-name cap.",

    "Hard sector allocation cap.",

    "Treating TQQQ only as an external benchmark.",

    "Repeatedly tuning a failed alpha model on the same historical sample.",

    "Selecting universe members because they performed well ex post.",

    "Using future index membership or future liquidity information.",

    "Using hindsight best-stock identity as a trading signal.",
]


# ==============================================================================
# 8. V4 RESEARCH DISCIPLINE
# ==============================================================================

V4_RESEARCH_RULES = [

    (
        "Universe rules must be defined before evaluating portfolio returns."
    ),

    (
        "Universe eligibility may use only contemporaneously available "
        "liquidity / price / data-quality information."
    ),

    (
        "Alpha features must be causal."
    ),

    (
        "Targets must become trainable only after the target horizon has "
        "actually completed."
    ),

    (
        "No model is promoted from IC alone."
    ),

    (
        "The same-calendar portfolio backtest determines promotion."
    ),

    (
        "Failed model families are rejected rather than repeatedly tuned "
        "on the same test sample."
    ),

    (
        "Portfolio concentration is allowed when generated naturally by "
        "expected return and portfolio-risk economics."
    ),

    (
        "No arbitrary name or sector diversification constraint is introduced."
    ),

    (
        "Cash is a legitimate optimal portfolio allocation."
    ),

    (
        "All reported returns must include the declared transaction-cost model."
    ),

    (
        "Final V4 must be compared against V3, QQQ, TQQQ and passive universe "
        "benchmarks on exactly the same calendar."
    ),
]


# ==============================================================================
# 9. BENCHMARK POLICY
# ==============================================================================

V4_REQUIRED_BENCHMARKS = (

    "FROZEN_V3",

    "QQQ_BUY_HOLD",

    "TQQQ_BUY_HOLD",

    "BROAD_UNIVERSE_EQUAL_WEIGHT_BUY_HOLD",

    "CASH_OR_RISK_FREE",
)


# ==============================================================================
# 10. BLOCK ROADMAP
# ==============================================================================

V4_RESEARCH_ROADMAP = pd.DataFrame(
    {

        "Block": [
            37,
            38,
            39,
            40,
            41,
        ],

        "Purpose": [
            "Freeze V4 absolute-return architecture",
            "Build broad causal investable universe",
            "Build multi-horizon absolute-return alpha",
            "Build net-return portfolio optimizer",
            "Run strict same-calendar final benchmark",
        ],

        "Primary_Output": [
            "V4 architecture fingerprint",
            "Point-in-time eligible asset panel",
            "OOS expected-return forecasts",
            "Dynamic portfolio path",
            "V4 vs V3 / QQQ / TQQQ / passive wealth",
        ],
    }
)


# ==============================================================================
# 11. CREATE MASTER ARCHITECTURE FINGERPRINT
# ==============================================================================

V4_FREEZE_PAYLOAD = {

    "Parent":
        V4_PARENT_FINGERPRINT,

    "Objective":
        V4_PROJECT_OBJECTIVE,

    "Architecture":
        V4_ARCHITECTURE,

    "Config":
        asdict(
            V4_MASTER_CONFIG
        ),

    "Asset_Policy":
        V4_ASSET_POLICY,

    "Optimization_Objective":
        V4_OPTIMIZATION_OBJECTIVE,

    "Rejected":
        V4_REJECTED_ARCHITECTURE,

    "Research_Rules":
        V4_RESEARCH_RULES,

    "Benchmarks":
        V4_REQUIRED_BENCHMARKS,
}


V4_FREEZE_JSON = json.dumps(

    V4_FREEZE_PAYLOAD,

    sort_keys=True,

    indent=2,

    default=str,
)


V4_MASTER_FINGERPRINT = (

    hashlib.sha256(

        V4_FREEZE_JSON.encode(
            "utf-8"
        )
    )
    .hexdigest()
)


# ==============================================================================
# 12. INTEGRITY ASSERTIONS
# ==============================================================================

assert (
    V4_MASTER_CONFIG.max_name_weight
    is None
)


assert (
    V4_MASTER_CONFIG.max_sector_weight
    is None
)


assert (
    V4_MASTER_CONFIG.allow_cash
    is True
)


assert (
    V4_MASTER_CONFIG.tqqq_is_investable
    is True
)


assert (
    V4_MASTER_CONFIG.long_only
    is True
)


# ==============================================================================
# 13. HISTORICAL FINGERPRINT GATE
# ==============================================================================

if (
    V4_PARENT_FINGERPRINT
    !=
    V3_RESEARCH_FINGERPRINT
):

    raise RuntimeError(
        "V4 parent fingerprint mismatch."
    )


if (
    V4_MASTER_FINGERPRINT
    !=
    EXPECTED_V4_MASTER_FINGERPRINT
):

    raise RuntimeError(
        "\nHISTORICAL V4 MASTER FINGERPRINT MISMATCH.\n"
        f"Expected: {EXPECTED_V4_MASTER_FINGERPRINT}\n"
        f"Actual  : {V4_MASTER_FINGERPRINT}\n"
        "STOP. Do not continue to Module 14."
    )


# ==============================================================================
# 14. OUTPUT
# ==============================================================================

print(
    "=" * 120
)


print(
    "MODULE 13 / HISTORICAL BLOCK 37 — "
    "V4 MASTER ARCHITECTURE / ABSOLUTE-RETURN OBJECTIVE FREEZE"
)


print(
    "=" * 120
)


print(
    "\nPROJECT OBJECTIVE\n"
)


print(
    V4_PROJECT_OBJECTIVE
)


print(
    "\nV4 MASTER ARCHITECTURE\n"
)


for key, value in (
    V4_ARCHITECTURE.items()
):

    print(
        f"{key:<28}: {value}"
    )


print(
    "\nV4 MASTER CONFIG\n"
)


display(

    pd.DataFrame(
        [
            asdict(
                V4_MASTER_CONFIG
            )
        ]
    )
    .T
    .rename(
        columns={
            0:
                "Frozen_Value"
        }
    )
)


print(
    "\nPORTFOLIO OBJECTIVE\n"
)


print(
    V4_OPTIMIZATION_OBJECTIVE
)


print(
    "\nREJECTED ARCHITECTURE\n"
)


for idx, item in enumerate(
    V4_REJECTED_ARCHITECTURE,
    start=1,
):

    print(
        f"{idx:2d}. {item}"
    )


print(
    "\nV4 RESEARCH RULES\n"
)


for idx, item in enumerate(
    V4_RESEARCH_RULES,
    start=1,
):

    print(
        f"{idx:2d}. {item}"
    )


print(
    "\nV4 ROADMAP\n"
)


display(
    V4_RESEARCH_ROADMAP
)


print(
    "\nPARENT V3 FINGERPRINT:"
)


print(
    V4_PARENT_FINGERPRINT
)


print(
    "\nV4 MASTER ARCHITECTURE FINGERPRINT:"
)


print(
    V4_MASTER_FINGERPRINT
)


print(
    "\n[+] MODULE 13 PASSED."
)


print(
    "[+] HISTORICAL BLOCK 37 FINGERPRINT MATCHED EXACTLY."
)


print(
    "[+] V3 is now benchmark-only."
)


print(
    "[+] NEXT: MODULE 14 — EXACT BLOCK 38A PITINDEX BRIDGE."
)
