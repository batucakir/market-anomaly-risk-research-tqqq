# ==============================================================================
# MODULE 17 / HISTORICAL BLOCK 40
# V4 NET-RETURN PORTFOLIO OPTIMIZER
#
# Historical Block-40 logic preserved.
# Internal B40_* / BLOCK40_* names intentionally preserved.
# ==============================================================================

import sys
import subprocess
import warnings
import time
import json
import hashlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.covariance import LedoitWolf
from IPython.display import display


# ==============================================================================
# 0. CVXPY — HISTORICAL PYTHON 3.9 ROUTE
# ==============================================================================

try:
    import cvxpy as cp

except ImportError:

    print(
        "[40-SETUP] Installing CVXPY for Python 3.9..."
    )

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "cvxpy<1.6",
        ]
    )

    import cvxpy as cp


print(
    "[40-SETUP] CVXPY version:",
    cp.__version__
)


# ==============================================================================
# 1. REQUIRED OBJECTS
# ==============================================================================

B40_REQUIRED = [

    "BLOCK39_PREDICTIONS",
    "B39_PRICE",
    "B39_PREDICTION_DATES",
    "BLOCK39_FINGERPRINT",

    "V4_MASTER_CONFIG",
    "V4_MASTER_FINGERPRINT",
    "V4_DATA_END_DATE",

    "B38_MIN_VALID_DAYS",
]


B40_MISSING = [
    x
    for x in B40_REQUIRED
    if x not in globals()
]


if B40_MISSING:

    raise RuntimeError(
        "BLOCK 40 missing required objects: "
        f"{B40_MISSING}"
    )


print("=" * 118)

print(
    "BLOCK 40 — V4 NET-RETURN PORTFOLIO OPTIMIZER"
)

print("=" * 118)


# ==============================================================================
# 2. PREDECLARED PORTFOLIO CONFIG
# ==============================================================================

B40_MODELS = {

    "RIDGE":
        "Mu_RIDGE",

    "HGB":
        "Mu_HGB",
}


B40_REBALANCE_EVERY = 5

B40_RISK_LOOKBACK = 60


B40_RISK_CAP_MULTIPLIER = float(
    V4_MASTER_CONFIG
    .portfolio_risk_cap_multiplier
)


B40_TCA_BPS = float(
    V4_MASTER_CONFIG
    .decision_tca_bps
)


B40_TCA_RATE = (
    B40_TCA_BPS
    /
    10000.0
)


B40_MIN_RISK_OBS = max(
    20,
    int(
        B38_MIN_VALID_DAYS
    )
    -
    1
)


B40_WEIGHT_EPS = 1e-8

B40_BINDING_TOL = 0.99


print(
    "\nRebalance frequency :",
    B40_REBALANCE_EVERY,
    "sessions"
)

print(
    "Risk lookback       :",
    B40_RISK_LOOKBACK,
    "sessions"
)

print(
    "Risk cap            :",
    f"{B40_RISK_CAP_MULTIPLIER:.2f} × EW"
)

print(
    "Transaction cost    :",
    f"{B40_TCA_BPS:.2f} bps"
)

print(
    "Single-name cap     : NONE"
)

print(
    "Sector cap          : NONE"
)

print(
    "Cash allowed        : TRUE"
)


# ==============================================================================
# 3. SOLVER SELECTION
# ==============================================================================

installed_solvers = set(
    cp.installed_solvers()
)


if "CLARABEL" in installed_solvers:

    B40_PRIMARY_SOLVER = "CLARABEL"

elif "ECOS" in installed_solvers:

    B40_PRIMARY_SOLVER = "ECOS"

elif "SCS" in installed_solvers:

    B40_PRIMARY_SOLVER = "SCS"

else:

    raise RuntimeError(
        "Block 40 requires a conic CVXPY solver. "
        f"Installed solvers={sorted(installed_solvers)}"
    )


print(
    "\nPrimary optimizer solver:",
    B40_PRIMARY_SOLVER
)


# ==============================================================================
# 4. CLEAN BLOCK-39 PREDICTIONS
# ==============================================================================

B40_PRED = (
    BLOCK39_PREDICTIONS
    .copy()
    .replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )
)


B40_PRED[
    "Date"
] = pd.to_datetime(
    B40_PRED[
        "Date"
    ]
)


B40_PRED = (
    B40_PRED

    .drop_duplicates(
        subset=[
            "Date",
            "Ticker",
        ],
        keep="last",
    )

    .sort_values(
        [
            "Date",
            "Ticker",
        ]
    )

    .reset_index(
        drop=True
    )
)


# SAME cross-section for RIDGE and HGB.

B40_PRED = (
    B40_PRED

    .dropna(
        subset=[
            "Mu_RIDGE",
            "Mu_HGB",
        ]
    )
)


# ==============================================================================
# 5. PRICE TABLES
# ==============================================================================

B40_PRICE = (
    B39_PRICE[
        [
            "Date",
            "Ticker",
            "Adj_Open",
            "Adj_Close",
            "Daily_Return",
        ]
    ]

    .copy()

    .replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )
)


B40_PRICE[
    "Date"
] = pd.to_datetime(
    B40_PRICE[
        "Date"
    ]
)


B40_OPEN_WIDE = (
    B40_PRICE

    .pivot(
        index="Date",
        columns="Ticker",
        values="Adj_Open",
    )

    .sort_index()
)


B40_CLOSE_WIDE = (
    B40_PRICE

    .pivot(
        index="Date",
        columns="Ticker",
        values="Adj_Close",
    )

    .sort_index()
)


B40_RETURN_WIDE = (
    B40_PRICE

    .pivot(
        index="Date",
        columns="Ticker",
        values="Daily_Return",
    )

    .sort_index()
)


# ==============================================================================
# 6. MARKET CALENDAR
# ==============================================================================

B40_CALENDAR = (
    B40_PRICE.loc[
        B40_PRICE[
            "Ticker"
        ]
        ==
        "SPY",
        "Date",
    ]

    .drop_duplicates()

    .sort_values()

    .reset_index(
        drop=True
    )
)


if B40_CALENDAR.empty:

    raise RuntimeError(
        "SPY calendar missing."
    )


B40_FINAL_DATE = (
    B40_CALENDAR[
        B40_CALENDAR
        <=
        pd.Timestamp(
            V4_DATA_END_DATE
        )
    ]
    .max()
)


calendar_np = (
    B40_CALENDAR
    .to_numpy(
        dtype="datetime64[ns]"
    )
)


def b40_next_trading_day(
    signal_date,
):

    signal_np = np.datetime64(
        pd.Timestamp(
            signal_date
        )
    )


    idx = np.searchsorted(
        calendar_np,
        signal_np,
        side="right",
    )


    if idx >= len(
        calendar_np
    ):
        return pd.NaT


    return pd.Timestamp(
        calendar_np[
            idx
        ]
    )


# ==============================================================================
# 7. PREDECLARED REBALANCE SCHEDULE
# ==============================================================================

all_prediction_dates = (
    B40_PRED[
        "Date"
    ]

    .drop_duplicates()

    .sort_values()

    .reset_index(
        drop=True
    )
)


# Restored historical execution boundary, directly observed in the old
# V7/V8 audit. Do not shift the dates on already-computed portfolios.
B40_HISTORICAL_FIRST_EXECUTION = pd.Timestamp("2023-10-18")
all_prediction_dates = all_prediction_dates[
    all_prediction_dates.map(b40_next_trading_day) >= B40_HISTORICAL_FIRST_EXECUTION
].reset_index(drop=True)
if (all_prediction_dates.empty or
        b40_next_trading_day(all_prediction_dates.iloc[0]) != B40_HISTORICAL_FIRST_EXECUTION):
    raise RuntimeError("Historical 2023-10-17 signal / 2023-10-18 execution is unavailable in predictions.")

scheduled_signal_dates = list(
    all_prediction_dates.iloc[
        ::B40_REBALANCE_EVERY
    ]
)


schedule_rows = []


for signal_date in scheduled_signal_dates:

    execution_date = (
        b40_next_trading_day(
            signal_date
        )
    )


    if pd.isna(
        execution_date
    ):
        continue


    if execution_date > B40_FINAL_DATE:
        continue


    schedule_rows.append(
        {

            "Signal_Date":
                pd.Timestamp(
                    signal_date
                ),

            "Execution_Date":
                pd.Timestamp(
                    execution_date
                ),
        }
    )


B40_SCHEDULE = pd.DataFrame(
    schedule_rows
)


if B40_SCHEDULE.empty:

    raise RuntimeError(
        "Block 40 produced zero executable rebalances."
    )


B40_SCHEDULE = (
    B40_SCHEDULE

    .drop_duplicates(
        "Execution_Date"
    )

    .sort_values(
        "Execution_Date"
    )

    .reset_index(
        drop=True
    )
)


B40_SCHEDULE[
    "Next_Execution_Date"
] = (
    B40_SCHEDULE[
        "Execution_Date"
    ]
    .shift(
        -1
    )
)


B40_SCHEDULE[
    "Is_Final_Period"
] = (
    B40_SCHEDULE[
        "Next_Execution_Date"
    ]
    .isna()
)


B40_SCHEDULE[
    "Exit_Date"
] = (
    B40_SCHEDULE[
        "Next_Execution_Date"
    ]
)


B40_SCHEDULE.loc[
    B40_SCHEDULE[
        "Is_Final_Period"
    ],
    "Exit_Date",
] = B40_FINAL_DATE


print(
    "\nExecutable rebalances:",
    len(
        B40_SCHEDULE
    )
)

print(
    "First signal:",
    B40_SCHEDULE[
        "Signal_Date"
    ]
    .min()
    .date()
)

print(
    "First execution:",
    B40_SCHEDULE[
        "Execution_Date"
    ]
    .min()
    .date()
)

print(
    "Final valuation:",
    B40_FINAL_DATE.date()
)


# ==============================================================================
# 8. HOLDING-SESSION COUNT
# ==============================================================================

calendar_position = {

    pd.Timestamp(
        date
    ):
        i

    for i, date in enumerate(
        B40_CALENDAR
    )
}


def b40_holding_sessions(
    execution_date,
    exit_date,
    is_final,
):

    start_i = calendar_position[
        pd.Timestamp(
            execution_date
        )
    ]

    end_i = calendar_position[
        pd.Timestamp(
            exit_date
        )
    ]


    if is_final:

        # Open(start) -> Close(end)

        return max(
            1,
            end_i
            -
            start_i
            +
            1
        )


    # Open(start) -> Open(end)

    return max(
        1,
        end_i
        -
        start_i
    )


B40_SCHEDULE[
    "Holding_Sessions"
] = [

    b40_holding_sessions(
        execution_date=row.Execution_Date,
        exit_date=row.Exit_Date,
        is_final=row.Is_Final_Period,
    )

    for row in (
        B40_SCHEDULE.itertuples()
    )
]


# ==============================================================================
# 9. NUMERIC LEDOIT-WOLF RISK
# ==============================================================================

def b40_numeric_risk(
    weights,
    centered_returns,
    shrinkage,
    identity_variance,
):

    weights = np.asarray(
        weights,
        dtype=float,
    )


    if len(
        weights
    ) == 0:

        return 0.0


    t_obs = float(
        centered_returns.shape[
            0
        ]
    )


    factor_component = (
        centered_returns
        @
        weights
    )


    variance = (

        (
            1.0
            -
            shrinkage
        )

        *
        np.sum(
            factor_component ** 2
        )

        /
        t_obs

        +

        shrinkage
        *
        identity_variance
        *
        np.sum(
            weights ** 2
        )
    )


    return float(
        np.sqrt(
            max(
                variance,
                0.0,
            )
        )
    )


# ==============================================================================
# 10. RISK MODEL CONSTRUCTION
# ==============================================================================

def b40_build_risk_model(
    signal_date,
    candidate_assets,
):

    candidate_assets = list(
        candidate_assets
    )


    history = (
        B40_RETURN_WIDE.loc[
            B40_RETURN_WIDE.index
            <=
            signal_date,
            candidate_assets,
        ]

        .tail(
            B40_RISK_LOOKBACK
        )
    )


    if len(
        history
    ) < 20:

        return None


    valid_counts = (
        history
        .notna()
        .sum()
    )


    usable_assets = list(
        valid_counts[
            valid_counts
            >=
            B40_MIN_RISK_OBS
        ]
        .index
    )


    if len(
        usable_assets
    ) < 20:

        return None


    history = history[
        usable_assets
    ]


    # Missing observations replaced by each asset's trailing mean.
    trailing_means = (
        history.mean(
            axis=0,
            skipna=True,
        )
    )


    history = history.fillna(
        trailing_means
    )


    remaining_valid = (
        history
        .notna()
        .all(
            axis=0
        )
    )


    usable_assets = list(
        remaining_valid[
            remaining_valid
        ]
        .index
    )


    history = history[
        usable_assets
    ]


    X = history.to_numpy(
        dtype=float
    )


    if (
        X.shape[0] < 20
        or
        X.shape[1] < 20
    ):

        return None


    lw = LedoitWolf(
        assume_centered=False
    )

    lw.fit(
        X
    )


    shrinkage = float(
        lw.shrinkage_
    )


    X_centered = (
        X
        -
        X.mean(
            axis=0,
            keepdims=True,
        )
    )


    T = float(
        X_centered.shape[
            0
        ]
    )


    sample_variances = (
        np.sum(
            X_centered ** 2,
            axis=0,
        )
        /
        T
    )


    identity_variance = float(
        np.mean(
            sample_variances
        )
    )


    if (
        not np.isfinite(
            identity_variance
        )
        or
        identity_variance <= 0
    ):

        return None


    ew = (
        np.ones(
            len(
                usable_assets
            ),
            dtype=float,
        )
        /
        len(
            usable_assets
        )
    )


    ew_risk = b40_numeric_risk(

        weights=ew,

        centered_returns=
            X_centered,

        shrinkage=
            shrinkage,

        identity_variance=
            identity_variance,
    )


    risk_budget = (
        B40_RISK_CAP_MULTIPLIER
        *
        ew_risk
    )


    if (
        not np.isfinite(
            risk_budget
        )
        or
        risk_budget <= 0
    ):

        return None


    return {

        "assets":
            usable_assets,

        "X_centered":
            X_centered,

        "shrinkage":
            shrinkage,

        "identity_variance":
            identity_variance,

        "ew_risk":
            ew_risk,

        "risk_budget":
            risk_budget,
    }


# ==============================================================================
# 11. CONVEX NET-RETURN OPTIMIZER
# ==============================================================================

def b40_solve_portfolio(
    assets,
    mu_daily,
    holding_sessions,
    previous_weights,
    risk_model,
):

    assets = list(
        assets
    )


    n = len(
        assets
    )


    if n == 0:

        return {

            "weights":
                {},

            "status":
                "CASH_ONLY_NO_ASSETS",

            "forecast_risk":
                0.0,

            "risk_to_budget":
                0.0,

            "expected_return":
                0.0,

            "expected_net_objective":
                0.0,
        }


    mu_daily = np.asarray(
        mu_daily,
        dtype=float,
    )


    # Predicted DAILY -> scheduled holding-period return.

    safe_mu_daily = np.maximum(
        mu_daily,
        -0.95,
    )


    mu_period = np.expm1(

        np.log1p(
            safe_mu_daily
        )

        *
        float(
            holding_sessions
        )
    )


    previous_vector = np.asarray(
        [

            float(
                previous_weights.get(
                    asset,
                    0.0,
                )
            )

            for asset in assets
        ],
        dtype=float,
    )


    w = cp.Variable(
        n,
        nonneg=True,
    )


    expected_return_expr = (
        mu_period
        @
        w
    )


    turnover_expr = cp.norm1(
        w
        -
        previous_vector
    )


    expected_net_expr = (
        expected_return_expr
        -
        B40_TCA_RATE
        *
        turnover_expr
    )


    Xc = risk_model[
        "X_centered"
    ]


    shrink = float(
        risk_model[
            "shrinkage"
        ]
    )


    identity_variance = float(
        risk_model[
            "identity_variance"
        ]
    )


    T = float(
        Xc.shape[
            0
        ]
    )


    forecast_variance_expr = (

        (
            1.0
            -
            shrink
        )

        /
        T

        *
        cp.sum_squares(
            Xc
            @
            w
        )

        +

        shrink
        *
        identity_variance
        *
        cp.sum_squares(
            w
        )
    )


    risk_budget_sq = (
        float(
            risk_model[
                "risk_budget"
            ]
        )
        ** 2
    )


    constraints = [

        cp.sum(
            w
        )
        <=
        1.0,

        forecast_variance_expr
        <=
        risk_budget_sq,
    ]


    problem = cp.Problem(

        cp.Maximize(
            expected_net_expr
        ),

        constraints,
    )


    solver_attempts = [
        B40_PRIMARY_SOLVER
    ]


    if (
        B40_PRIMARY_SOLVER
        !=
        "SCS"
        and
        "SCS"
        in
        installed_solvers
    ):

        solver_attempts.append(
            "SCS"
        )


    solved = False
    final_status = None


    for solver_name in solver_attempts:

        try:

            with warnings.catch_warnings():

                warnings.simplefilter(
                    "ignore"
                )

                problem.solve(
                    solver=
                        solver_name,
                    warm_start=
                        False,
                    verbose=
                        False,
                )


            final_status = (
                problem.status
            )


            if problem.status in [
                cp.OPTIMAL,
                cp.OPTIMAL_INACCURATE,
            ]:

                solved = True
                break

        except Exception:

            continue


    if (
        not solved
        or
        w.value is None
    ):

        return {

            "weights":
                {},

            "status":
                (
                    final_status
                    if final_status is not None
                    else "SOLVER_FAILURE"
                ),

            "forecast_risk":
                0.0,

            "risk_to_budget":
                0.0,

            "expected_return":
                0.0,

            "expected_net_objective":
                0.0,
        }


    solution = np.asarray(
        w.value,
        dtype=float,
    )


    solution[
        ~np.isfinite(
            solution
        )
    ] = 0.0


    solution = np.maximum(
        solution,
        0.0,
    )


    total_weight = float(
        solution.sum()
    )


    if total_weight > 1.0:

        solution = (
            solution
            /
            total_weight
        )


    forecast_risk = b40_numeric_risk(

        weights=
            solution,

        centered_returns=
            Xc,

        shrinkage=
            shrink,

        identity_variance=
            identity_variance,
    )


    risk_budget = float(
        risk_model[
            "risk_budget"
        ]
    )


    # Historical numerical cleanup:
    # scale risky sleeve toward CASH if solver tolerance breaches budget.

    if forecast_risk > (
        risk_budget
        *
        1.0005
    ):

        scaling = (
            risk_budget
            /
            forecast_risk
        )


        solution = (
            solution
            *
            scaling
        )


        forecast_risk = (
            b40_numeric_risk(

                weights=
                    solution,

                centered_returns=
                    Xc,

                shrinkage=
                    shrink,

                identity_variance=
                    identity_variance,
            )
        )


    result_weights = {

        asset:
            float(
                weight
            )

        for asset, weight in zip(
            assets,
            solution
        )

        if weight
        >
        B40_WEIGHT_EPS
    }


    solution_turnover = float(
        np.abs(
            solution
            -
            previous_vector
        )
        .sum()
    )


    expected_return = float(
        mu_period
        @
        solution
    )


    expected_net = (
        expected_return
        -
        B40_TCA_RATE
        *
        solution_turnover
    )


    return {

        "weights":
            result_weights,

        "status":
            str(
                problem.status
            ),

        "forecast_risk":
            forecast_risk,

        "risk_to_budget":
            (
                forecast_risk
                /
                risk_budget
            ),

        "expected_return":
            expected_return,

        "expected_net_objective":
            expected_net,
    }


# ==============================================================================
# 12. REALIZED HOLDING-PERIOD RETURN
# ==============================================================================

def b40_realized_asset_returns(
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


    entry = (
        B40_OPEN_WIDE

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
        B40_CLOSE_WIDE
        if final_period
        else B40_OPEN_WIDE
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


        interval_close = (
            B40_CLOSE_WIDE.loc[
                (
                    B40_CLOSE_WIDE.index
                    >=
                    execution_date
                )
                &
                (
                    B40_CLOSE_WIDE.index
                    <=
                    exit_date
                ),
                missing_assets,
            ]
        )


        if not interval_close.empty:

            fallback = (
                interval_close
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


    invalid = (
        ~np.isfinite(
            realized
        )
    )


    # Historical conservative convention.
    realized.loc[
        invalid
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
# 13. STATE INITIALIZATION
# ==============================================================================

B40_STATES = {}


for model_name in B40_MODELS:

    B40_STATES[
        model_name
    ] = {

        "wealth":
            1.0,

        # Risky weights only.
        # Missing fraction = CASH.
        "weights":
            {},
    }


B40_PATH_ROWS = []

B40_WEIGHT_ROWS = []


B40_SOLVER_FAILURES = {

    model:
        0

    for model in B40_MODELS
}


# ==============================================================================
# 14. WALK-FORWARD PORTFOLIO SIMULATION
# ==============================================================================

print(
    "\n[40] Starting portfolio walk-forward..."
)


simulation_start = time.time()


for rebalance_no, schedule_row in enumerate(

    B40_SCHEDULE.itertuples(
        index=False
    ),

    start=1,
):

    signal_date = pd.Timestamp(
        schedule_row.Signal_Date
    )

    execution_date = pd.Timestamp(
        schedule_row.Execution_Date
    )

    exit_date = pd.Timestamp(
        schedule_row.Exit_Date
    )

    is_final_period = bool(
        schedule_row.Is_Final_Period
    )

    holding_sessions = int(
        schedule_row.Holding_Sessions
    )


    forecast = (
        B40_PRED[
            B40_PRED[
                "Date"
            ]
            ==
            signal_date
        ][
            [
                "Ticker",
                "Asset_Type",
                "Mu_RIDGE",
                "Mu_HGB",
            ]
        ]
        .copy()
    )


    if forecast.empty:
        continue


    # Execution-time quote availability.

    execution_open = (
        B40_OPEN_WIDE

        .reindex(
            index=[
                execution_date
            ],
            columns=
                forecast[
                    "Ticker"
                ]
                .tolist(),
        )

        .iloc[
            0
        ]
    )


    execution_valid_assets = set(

        execution_open.index[
            np.isfinite(
                execution_open
            )
            &
            (
                execution_open
                >
                0
            )
        ]
    )


    forecast = (
        forecast[
            forecast[
                "Ticker"
            ]
            .isin(
                execution_valid_assets
            )
        ]
        .copy()
    )


    if len(
        forecast
    ) < 20:

        raise RuntimeError(
            "Too few executable forecast assets "
            f"at {signal_date.date()}: "
            f"{len(forecast)}"
        )


    risk_model = b40_build_risk_model(

        signal_date=
            signal_date,

        candidate_assets=
            forecast[
                "Ticker"
            ]
            .tolist(),
    )


    if risk_model is None:

        raise RuntimeError(
            "Risk model construction failed "
            f"at {signal_date.date()}."
        )


    risk_assets = (
        risk_model[
            "assets"
        ]
    )


    forecast = (
        forecast

        .set_index(
            "Ticker"
        )

        .reindex(
            risk_assets
        )

        .dropna(
            subset=[
                "Mu_RIDGE",
                "Mu_HGB",
            ]
        )

        .reset_index()
    )


    final_assets = (
        forecast[
            "Ticker"
        ]
        .tolist()
    )


    risk_index = {

        asset:
            i

        for i, asset in enumerate(
            risk_assets
        )
    }


    keep_idx = [

        risk_index[
            asset
        ]

        for asset in final_assets
    ]


    risk_model_local = {

        **risk_model,

        "assets":
            final_assets,

        "X_centered":
            risk_model[
                "X_centered"
            ][
                :,
                keep_idx
            ],
    }


    # Exact candidate intersection EW reference.

    n_final = len(
        final_assets
    )


    ew_local = (
        np.ones(
            n_final
        )
        /
        n_final
    )


    ew_local_risk = b40_numeric_risk(

        weights=
            ew_local,

        centered_returns=
            risk_model_local[
                "X_centered"
            ],

        shrinkage=
            risk_model_local[
                "shrinkage"
            ],

        identity_variance=
            risk_model_local[
                "identity_variance"
            ],
    )


    risk_model_local[
        "ew_risk"
    ] = ew_local_risk


    risk_model_local[
        "risk_budget"
    ] = (
        B40_RISK_CAP_MULTIPLIER
        *
        ew_local_risk
    )


    # ==========================================================================
    # IDENTICAL PORTFOLIO CONSTRUCTION FOR RIDGE AND HGB
    # ==========================================================================

    for model_name, mu_column in (
        B40_MODELS.items()
    ):

        state = B40_STATES[
            model_name
        ]


        previous_weights = dict(
            state[
                "weights"
            ]
        )


        wealth_before_trade = float(
            state[
                "wealth"
            ]
        )


        mu_daily = (
            forecast[
                mu_column
            ]
            .to_numpy(
                dtype=float
            )
        )


        solution = b40_solve_portfolio(

            assets=
                final_assets,

            mu_daily=
                mu_daily,

            holding_sessions=
                holding_sessions,

            previous_weights=
                previous_weights,

            risk_model=
                risk_model_local,
        )


        if solution[
            "status"
        ] not in [
            "optimal",
            "optimal_inaccurate",
        ]:

            B40_SOLVER_FAILURES[
                model_name
            ] += 1


        target_weights = dict(
            solution[
                "weights"
            ]
        )


        # Includes liquidation of a previous holding
        # that dropped from today's eligible set.

        union_assets = (
            set(
                previous_weights
            )
            |
            set(
                target_weights
            )
        )


        actual_turnover = float(
            sum(
                abs(
                    target_weights.get(
                        asset,
                        0.0,
                    )
                    -
                    previous_weights.get(
                        asset,
                        0.0,
                    )
                )

                for asset in union_assets
            )
        )


        transaction_cost_fraction = (
            B40_TCA_RATE
            *
            actual_turnover
        )


        transaction_cost_amount = (
            wealth_before_trade
            *
            transaction_cost_fraction
        )


        wealth_after_cost = (
            wealth_before_trade
            *
            (
                1.0
                -
                transaction_cost_fraction
            )
        )


        realized_returns = (
            b40_realized_asset_returns(

                assets=
                    target_weights.keys(),

                execution_date=
                    execution_date,

                exit_date=
                    exit_date,

                final_period=
                    is_final_period,
            )
        )


        risky_growth_contribution = float(
            sum(
                weight
                *
                realized_returns[
                    asset
                ]

                for asset, weight in (
                    target_weights.items()
                )
            )
        )


        gross_holding_factor = (
            1.0
            +
            risky_growth_contribution
        )


        if gross_holding_factor <= 0:

            gross_holding_factor = (
                1e-12
            )


        wealth_after_period = (
            wealth_after_cost
            *
            gross_holding_factor
        )


        period_net_return = (
            (
                1.0
                -
                transaction_cost_fraction
            )
            *
            gross_holding_factor
            -
            1.0
        )


        # Drift holdings to the next execution point.

        cash_weight_target = max(
            0.0,
            1.0
            -
            sum(
                target_weights.values()
            )
        )


        risky_end_values = {

            asset:
                weight
                *
                (
                    1.0
                    +
                    realized_returns[
                        asset
                    ]
                )

            for asset, weight in (
                target_weights.items()
            )
        }


        end_total_relative = (
            cash_weight_target
            +
            sum(
                risky_end_values.values()
            )
        )


        if end_total_relative <= 0:

            next_weights = {}


        else:

            next_weights = {

                asset:
                    value
                    /
                    end_total_relative

                for asset, value in (
                    risky_end_values.items()
                )

                if (
                    value
                    /
                    end_total_relative
                )
                >
                B40_WEIGHT_EPS
            }


        B40_STATES[
            model_name
        ] = {

            "wealth":
                wealth_after_period,

            "weights":
                next_weights,
        }


        max_weight = (
            max(
                target_weights.values()
            )
            if target_weights
            else
            0.0
        )


        risky_weight = float(
            sum(
                target_weights.values()
            )
        )


        cash_weight = max(
            0.0,
            1.0
            -
            risky_weight
        )


        effective_n = (
            1.0
            /
            sum(
                w ** 2
                for w in (
                    target_weights.values()
                )
            )
            if target_weights
            else
            0.0
        )


        B40_PATH_ROWS.append(
            {

                "Model":
                    model_name,

                "Rebalance":
                    rebalance_no,

                "Signal_Date":
                    signal_date,

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    exit_date,

                "Holding_Sessions":
                    holding_sessions,

                "Candidate_Assets":
                    len(
                        final_assets
                    ),

                "Solver_Status":
                    solution[
                        "status"
                    ],

                "EW_Risk":
                    risk_model_local[
                        "ew_risk"
                    ],

                "Risk_Budget":
                    risk_model_local[
                        "risk_budget"
                    ],

                "Portfolio_Risk":
                    solution[
                        "forecast_risk"
                    ],

                "Risk_to_Budget":
                    solution[
                        "risk_to_budget"
                    ],

                "Expected_Return":
                    solution[
                        "expected_return"
                    ],

                "Expected_Net_Objective":
                    solution[
                        "expected_net_objective"
                    ],

                "Turnover":
                    actual_turnover,

                "TCA_Fraction":
                    transaction_cost_fraction,

                "TCA_Amount":
                    transaction_cost_amount,

                "Risky_Weight":
                    risky_weight,

                "Cash_Weight":
                    cash_weight,

                "Max_Name_Weight":
                    max_weight,

                "Effective_N":
                    effective_n,

                "Held_Names":
                    len(
                        target_weights
                    ),

                "Period_Net_Return":
                    period_net_return,

                "Wealth":
                    wealth_after_period,
            }
        )


        for asset, weight in (
            target_weights.items()
        ):

            B40_WEIGHT_ROWS.append(
                {

                    "Model":
                        model_name,

                    "Signal_Date":
                        signal_date,

                    "Execution_Date":
                        execution_date,

                    "Ticker":
                        asset,

                    "Weight":
                        weight,
                }
            )


    if (
        rebalance_no == 1

        or
        rebalance_no % 10 == 0

        or
        rebalance_no
        ==
        len(
            B40_SCHEDULE
        )
    ):

        ridge_wealth = (
            B40_STATES[
                "RIDGE"
            ][
                "wealth"
            ]
        )


        hgb_wealth = (
            B40_STATES[
                "HGB"
            ][
                "wealth"
            ]
        )


        print(
            f"[40] "
            f"{rebalance_no:03d}/"
            f"{len(B40_SCHEDULE):03d} "
            f"| {signal_date.date()} "
            f"| RIDGE={ridge_wealth:.4f} "
            f"| HGB={hgb_wealth:.4f}"
        )


print(
    "\nPortfolio simulation seconds:",
    round(
        time.time()
        -
        simulation_start,
        1,
    )
)


# ==============================================================================
# 15. OUTPUT TABLES
# ==============================================================================

BLOCK40_PATH = pd.DataFrame(
    B40_PATH_ROWS
)


BLOCK40_WEIGHTS = pd.DataFrame(
    B40_WEIGHT_ROWS
)


if BLOCK40_PATH.empty:

    raise RuntimeError(
        "Block 40 produced zero portfolio observations."
    )


# ==============================================================================
# 16. PERFORMANCE HELPER
# ==============================================================================

def b40_max_drawdown(
    wealth_series,
):

    wealth_series = pd.Series(
        wealth_series,
        dtype=float,
    )


    running_max = (
        wealth_series.cummax()
    )


    drawdown = (
        wealth_series
        /
        running_max
        -
        1.0
    )


    return float(
        drawdown.min()
    )


# ==============================================================================
# 17. MODEL SUMMARY
# ==============================================================================

summary_rows = []


first_execution = (
    BLOCK40_PATH[
        "Execution_Date"
    ]
    .min()
)


final_exit = (
    BLOCK40_PATH[
        "Exit_Date"
    ]
    .max()
)


elapsed_years = (
    (
        final_exit
        -
        first_execution
    ).days
    /
    365.25
)


for model_name, section in (
    BLOCK40_PATH
    .groupby(
        "Model"
    )
):

    section = (
        section
        .sort_values(
            "Exit_Date"
        )
    )


    final_wealth = float(
        section[
            "Wealth"
        ]
        .iloc[
            -1
        ]
    )


    total_return = (
        final_wealth
        -
        1.0
    )


    CAGR = (
        final_wealth
        **
        (
            1.0
            /
            elapsed_years
        )
        -
        1.0
        if elapsed_years > 0
        else np.nan
    )


    valid_period = (
        (
            section[
                "Period_Net_Return"
            ]
            >
            -1.0
        )
        &
        (
            section[
                "Holding_Sessions"
            ]
            >
            0
        )
    )


    daily_equivalent = np.expm1(

        np.log1p(
            section.loc[
                valid_period,
                "Period_Net_Return"
            ]
        )

        /

        section.loc[
            valid_period,
            "Holding_Sessions"
        ]
    )


    sharpe = (
        np.sqrt(
            252.0
        )
        *
        daily_equivalent.mean()
        /
        daily_equivalent.std(
            ddof=1
        )
        if (
            len(
                daily_equivalent
            )
            >
            2
            and
            daily_equivalent.std(
                ddof=1
            )
            >
            0
        )
        else np.nan
    )


    summary_rows.append(
        {

            "Model":
                model_name,

            "Rebalances":
                len(
                    section
                ),

            "Final_Wealth":
                final_wealth,

            "Net_Return_Pct":
                100.0
                *
                total_return,

            "CAGR_Pct":
                100.0
                *
                CAGR,

            "Diagnostic_Sharpe":
                sharpe,

            "Max_Drawdown_Pct":
                100.0
                *
                b40_max_drawdown(
                    section[
                        "Wealth"
                    ]
                ),

            "Total_Turnover":
                section[
                    "Turnover"
                ]
                .sum(),

            "Mean_Turnover":
                section[
                    "Turnover"
                ]
                .mean(),

            "TCA_Amount_vs_Initial_Pct":
                100.0
                *
                section[
                    "TCA_Amount"
                ]
                .sum(),

            "Mean_Cash_Weight_Pct":
                100.0
                *
                section[
                    "Cash_Weight"
                ]
                .mean(),

            "Mean_Risky_Weight_Pct":
                100.0
                *
                section[
                    "Risky_Weight"
                ]
                .mean(),

            "Mean_Max_Name_Weight_Pct":
                100.0
                *
                section[
                    "Max_Name_Weight"
                ]
                .mean(),

            "Maximum_Name_Weight_Pct":
                100.0
                *
                section[
                    "Max_Name_Weight"
                ]
                .max(),

            "Mean_Effective_N":
                section[
                    "Effective_N"
                ]
                .mean(),

            "Mean_Held_Names":
                section[
                    "Held_Names"
                ]
                .mean(),

            "Risk_Cap_Binding_Pct":
                100.0
                *
                (
                    section[
                        "Risk_to_Budget"
                    ]
                    >=
                    B40_BINDING_TOL
                )
                .mean(),

            "Solver_Failures":
                B40_SOLVER_FAILURES[
                    model_name
                ],
        }
    )


BLOCK40_SUMMARY = (
    pd.DataFrame(
        summary_rows
    )
    .set_index(
        "Model"
    )
)


# ==============================================================================
# 18. YEARLY PERFORMANCE
# ==============================================================================

yearly_rows = []


for model_name, section in (
    BLOCK40_PATH
    .groupby(
        "Model"
    )
):

    section = (
        section
        .sort_values(
            "Exit_Date"
        )
        .copy()
    )


    section[
        "Year"
    ] = (
        section[
            "Exit_Date"
        ]
        .dt.year
    )


    for year, year_section in (
        section.groupby(
            "Year"
        )
    ):

        year_growth = float(
            np.prod(
                1.0
                +
                year_section[
                    "Period_Net_Return"
                ]
            )
        )


        yearly_rows.append(
            {

                "Year":
                    int(
                        year
                    ),

                "Model":
                    model_name,

                "Net_Return_Pct":
                    100.0
                    *
                    (
                        year_growth
                        -
                        1.0
                    ),

                "Turnover":
                    year_section[
                        "Turnover"
                    ]
                    .sum(),

                "Mean_Cash_Pct":
                    100.0
                    *
                    year_section[
                        "Cash_Weight"
                    ]
                    .mean(),

                "Mean_Max_Name_Pct":
                    100.0
                    *
                    year_section[
                        "Max_Name_Weight"
                    ]
                    .mean(),

                "Risk_Binding_Pct":
                    100.0
                    *
                    (
                        year_section[
                            "Risk_to_Budget"
                        ]
                        >=
                        B40_BINDING_TOL
                    )
                    .mean(),
            }
        )


BLOCK40_YEARLY = pd.DataFrame(
    yearly_rows
)


# ==============================================================================
# 19. WEALTH TABLE
# ==============================================================================

BLOCK40_WEALTH_WIDE = (
    BLOCK40_PATH

    .pivot(
        index="Exit_Date",
        columns="Model",
        values="Wealth",
    )

    .sort_index()
)


# ==============================================================================
# 20. TQQQ PORTFOLIO PARTICIPATION
# ==============================================================================

if not BLOCK40_WEIGHTS.empty:

    BLOCK40_TQQQ = (
        BLOCK40_WEIGHTS[
            BLOCK40_WEIGHTS[
                "Ticker"
            ]
            ==
            "TQQQ"
        ]

        .groupby(
            "Model"
        )

        .agg(

            TQQQ_Allocation_Events=(
                "Weight",
                "size",
            ),

            Mean_TQQQ_Weight=(
                "Weight",
                "mean",
            ),

            Max_TQQQ_Weight=(
                "Weight",
                "max",
            ),
        )
    )


    BLOCK40_TQQQ[
        "Mean_TQQQ_Weight_Pct"
    ] = (
        100.0
        *
        BLOCK40_TQQQ[
            "Mean_TQQQ_Weight"
        ]
    )


    BLOCK40_TQQQ[
        "Max_TQQQ_Weight_Pct"
    ] = (
        100.0
        *
        BLOCK40_TQQQ[
            "Max_TQQQ_Weight"
        ]
    )


else:

    BLOCK40_TQQQ = (
        pd.DataFrame()
    )


# ==============================================================================
# 21. SOLVER FAILURE GATE
# ==============================================================================

failure_rates = {

    model:
        B40_SOLVER_FAILURES[
            model
        ]
        /
        len(
            B40_SCHEDULE
        )

    for model in B40_MODELS
}


if any(
    rate > 0.05
    for rate in failure_rates.values()
):

    raise RuntimeError(
        "Block 40 solver failure rate exceeded 5%. "
        f"{failure_rates}"
    )


# ==============================================================================
# 22. BLOCK-40 FINGERPRINT
# ==============================================================================

B40_CONFIG = {

    "parent_alpha_fingerprint":
        BLOCK39_FINGERPRINT,

    "rebalance_every":
        B40_REBALANCE_EVERY,

    "risk_lookback":
        B40_RISK_LOOKBACK,

    "minimum_risk_observations":
        B40_MIN_RISK_OBS,

    "risk_cap_multiplier":
        B40_RISK_CAP_MULTIPLIER,

    "tca_bps":
        B40_TCA_BPS,

    "long_only":
        True,

    "cash_allowed":
        True,

    "single_name_cap":
        None,

    "sector_cap":
        None,

    "cash_expected_return":
        0.0,

    "cash_realized_return":
        0.0,

    "risk_model":
        "LEDOIT_WOLF_SHRINKAGE",

    "objective":
        "EXPECTED_RETURN_MINUS_TRANSACTION_COST",
}


BLOCK40_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            B40_CONFIG,
            sort_keys=True,
            default=str,
        ).encode(
            "utf-8"
        )
    )
    .hexdigest()
)


# ==============================================================================
# 23. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 118
)

print(
    "BLOCK 40 — RESULTS"
)

print(
    "=" * 118
)


print(
    "\n1) NET PORTFOLIO PERFORMANCE"
)


display(
    BLOCK40_SUMMARY
    .round(
        6
    )
)


print(
    "\n2) YEAR-BY-YEAR"
)


display(
    BLOCK40_YEARLY
    .round(
        6
    )
)


print(
    "\n3) TQQQ PORTFOLIO PARTICIPATION"
)


if BLOCK40_TQQQ.empty:

    print(
        "TQQQ received zero portfolio weight."
    )

else:

    display(
        BLOCK40_TQQQ
        .round(
            6
        )
    )


print(
    "\n4) LATEST PORTFOLIO — RIDGE"
)


latest_ridge_date = (
    BLOCK40_WEIGHTS.loc[
        BLOCK40_WEIGHTS[
            "Model"
        ]
        ==
        "RIDGE",
        "Execution_Date",
    ]
    .max()
)


latest_ridge = (
    BLOCK40_WEIGHTS[
        (
            BLOCK40_WEIGHTS[
                "Model"
            ]
            ==
            "RIDGE"
        )
        &
        (
            BLOCK40_WEIGHTS[
                "Execution_Date"
            ]
            ==
            latest_ridge_date
        )
    ]

    .sort_values(
        "Weight",
        ascending=False,
    )
)


display(
    latest_ridge

    .head(
        25
    )

    .assign(
        Weight_Pct=lambda x:
            100.0
            *
            x[
                "Weight"
            ]
    )

    [
        [
            "Ticker",
            "Weight_Pct",
        ]
    ]

    .round(
        4
    )
)


print(
    "\n5) LATEST PORTFOLIO — HGB"
)


latest_hgb_date = (
    BLOCK40_WEIGHTS.loc[
        BLOCK40_WEIGHTS[
            "Model"
        ]
        ==
        "HGB",
        "Execution_Date",
    ]
    .max()
)


latest_hgb = (
    BLOCK40_WEIGHTS[
        (
            BLOCK40_WEIGHTS[
                "Model"
            ]
            ==
            "HGB"
        )
        &
        (
            BLOCK40_WEIGHTS[
                "Execution_Date"
            ]
            ==
            latest_hgb_date
        )
    ]

    .sort_values(
        "Weight",
        ascending=False,
    )
)


display(
    latest_hgb

    .head(
        25
    )

    .assign(
        Weight_Pct=lambda x:
            100.0
            *
            x[
                "Weight"
            ]
    )

    [
        [
            "Ticker",
            "Weight_Pct",
        ]
    ]

    .round(
        4
    )
)


# ==============================================================================
# 24. WEALTH CURVE
# ==============================================================================

plt.figure(
    figsize=(
        14,
        7,
    )
)


for model_name in B40_MODELS:

    if model_name in (
        BLOCK40_WEALTH_WIDE.columns
    ):

        plt.plot(

            BLOCK40_WEALTH_WIDE.index,

            BLOCK40_WEALTH_WIDE[
                model_name
            ],

            label=
                model_name,

            linewidth=
                2,
        )


plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1,
)


plt.title(
    "Block 40 — V4 Net Portfolio Wealth"
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
# 25. PORTFOLIO VERDICT
# ==============================================================================

ridge_final = float(
    BLOCK40_SUMMARY.loc[
        "RIDGE",
        "Final_Wealth",
    ]
)


hgb_final = float(
    BLOCK40_SUMMARY.loc[
        "HGB",
        "Final_Wealth",
    ]
)


portfolio_leader = (
    "RIDGE"
    if ridge_final > hgb_final
    else "HGB"
)


print(
    "\n"
    +
    "=" * 118
)


print(
    "BLOCK 40 — PORTFOLIO VERDICT"
)


print(
    "=" * 118
)


print(
    f"\nRIDGE final wealth : "
    f"{ridge_final:.6f}"
)


print(
    f"HGB final wealth   : "
    f"{hgb_final:.6f}"
)


print(
    f"\nCurrent V4 portfolio leader: "
    f"{portfolio_leader}"
)


print(
    "\nIMPORTANT:"
)


print(
    "This is NOT yet the final strategy verdict."
)


print(
    "Block 41 will compare the exact same calendar against:"
)


print(
    "  - Frozen V3"
)

print(
    "  - QQQ buy & hold"
)

print(
    "  - TQQQ buy & hold"
)

print(
    "  - broad PIT passive benchmark"
)

print(
    "  - cash"
)


print(
    "\nBLOCK 40 FINGERPRINT:"
)


print(
    BLOCK40_FINGERPRINT
)


print(
    "\n[+] BLOCK 40 PASSED."
)


print(
    "[+] NEXT: BLOCK 41 — FINAL SAME-CALENDAR NET-WEALTH BENCHMARK."
)
