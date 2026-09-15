# =============================================================================
# MODULE 07 — CAUSAL FORWARD-RISK FORECAST
# =============================================================================

from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


required = ["features_df"]

missing = [
    name
    for name in required
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing dependencies: {missing}. "
        "Run Module 03 before Module 07."
    )


RANGE_ONLY_FEATURES = [
    "Log_Range",
]

BASE_RISK_FEATURES = [
    "EWMA_Vol",
    "Log_Range",
    "Abs_Intraday_Return",
    "VWAP_Distance",
    "Log_Relative_Volume",
    "Abs_Return_Surprise",
]


risk_model_df = (
    features_df
    .copy()
    .sort_index()
)

risk_model_df["Abs_Intraday_Return"] = (
    risk_model_df["Intraday_Return"].abs()
)

risk_model_df["Abs_Return_Surprise"] = (
    risk_model_df["Return_Surprise_SignedLog"].abs()
)


def build_forward_rv_target(
    df: pd.DataFrame,
    horizon: int = 3,
) -> pd.DataFrame:

    out = (
        df
        .copy()
        .sort_index()
    )

    sessions = pd.Series(
        out.index.normalize(),
        index=out.index,
    )

    future_returns = []

    for step in range(1, horizon + 1):
        column = f"_Future_Return_{step}"

        out[column] = (
            out["Intraday_Return"]
            .groupby(sessions)
            .shift(-step)
        )

        future_returns.append(column)

    target = f"Forward_RV_{horizon}"

    out[target] = np.sqrt(
        out[future_returns]
        .pow(2)
        .sum(
            axis=1,
            min_count=horizon,
        )
    )

    timestamps = pd.Series(
        out.index,
        index=out.index,
    )

    out["Target_End_Time"] = (
        timestamps
        .groupby(sessions)
        .shift(-horizon)
    )

    return out.drop(
        columns=future_returns
    )


def run_causal_risk_forecaster(
    df: pd.DataFrame,
    feature_columns: list[str],
    horizon: int = 3,
    min_train_targets: int = 60,
    retrain_every: int = 10,
    alpha: float = 1.0,
) -> pd.DataFrame:

    data = build_forward_rv_target(
        df,
        horizon=horizon,
    )

    target = f"Forward_RV_{horizon}"

    required_columns = (
        feature_columns
        + [
            target,
            "Target_End_Time",
        ]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing risk-model columns: {missing_columns}"
        )

    data = (
        data
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=feature_columns
        )
        .copy()
    )

    data["Predicted_Forward_RV"] = np.nan
    data["Train_Target_Count"] = np.nan

    model = None
    last_fit = None

    eps = 1e-12

    for i in range(len(data)):

        current_time = data.index[i]

        eligible = (
            (data.index < current_time)
            & data[target].notna()
            & data["Target_End_Time"].notna()
            & (
                data["Target_End_Time"]
                <= current_time
            )
        )

        train = data.loc[
            eligible
        ]

        if len(train) < min_train_targets:
            continue

        retrain = (
            model is None
            or last_fit is None
            or i - last_fit >= retrain_every
        )

        if retrain:

            X_train = (
                train[feature_columns]
                .to_numpy(dtype=float)
            )

            y_train = np.log(
                train[target]
                .clip(lower=eps)
                .to_numpy(dtype=float)
            )
            model = Pipeline(
                [
                    (
                        "scaler",
                        RobustScaler(),
                    ),
                    (
                        "ridge",
                        Ridge(
                            alpha=alpha,
                            solver="lsqr",
                        ),
                    ),
                ]
            )

            model.fit(
                X_train,
                y_train,
            )

            last_fit = i

        X_test = (
            data.iloc[[i]][feature_columns]
            .to_numpy(dtype=float)
        )

        prediction = float(
            np.exp(
                model.predict(X_test)[0]
            )
        )

        if not np.isfinite(prediction):
            continue

        data.at[
            current_time,
            "Predicted_Forward_RV",
        ] = prediction

        data.at[
            current_time,
            "Train_Target_Count",
        ] = len(train)

    return (
        data
        .dropna(
            subset=[
                "Predicted_Forward_RV",
                target,
            ]
        )
        .copy()
    )


def evaluate_risk_forecast(
    df: pd.DataFrame,
    horizon: int = 3,
) -> dict:

    target = f"Forward_RV_{horizon}"

    actual = df[target]
    predicted = df["Predicted_Forward_RV"]

    comparison = pd.concat(
        [
            actual.rename("Actual"),
            predicted.rename("Predicted"),
        ],
        axis=1,
    )

    spearman = (
        comparison
        .corr(method="spearman")
        .iloc[0, 1]
    )

    errors = (
        actual
        - predicted
    )

    return {
        "Observations": len(df),
        "Spearman_IC": spearman,
        "MAE": np.abs(errors).mean(),
        "RMSE": np.sqrt(
            np.square(errors).mean()
        ),
        "Min_Train_Targets": (
            df["Train_Target_Count"].min()
        ),
        "Max_Train_Targets": (
            df["Train_Target_Count"].max()
        ),
    }


risk_range_only = run_causal_risk_forecaster(
    risk_model_df,
    feature_columns=RANGE_ONLY_FEATURES,
    horizon=3,
    min_train_targets=60,
    retrain_every=10,
    alpha=1.0,
)

risk_base = run_causal_risk_forecaster(
    risk_model_df,
    feature_columns=BASE_RISK_FEATURES,
    horizon=3,
    min_train_targets=60,
    retrain_every=10,
    alpha=1.0,
)


common_index = (
    risk_range_only.index
    .intersection(
        risk_base.index
    )
)

range_eval = (
    risk_range_only
    .loc[common_index]
    .copy()
)

base_eval = (
    risk_base
    .loc[common_index]
    .copy()
)


risk_comparison = pd.DataFrame(
    {
        "RANGE_ONLY": evaluate_risk_forecast(
            range_eval,
            horizon=3,
        ),
        "BASE_FEATURES": evaluate_risk_forecast(
            base_eval,
            horizon=3,
        ),
    }
)


print(
    f"Forward-risk OOS rows: {len(common_index):,} | "
    f"{common_index.min()} → {common_index.max()}"
)

display(
    risk_comparison.round(6)
)
