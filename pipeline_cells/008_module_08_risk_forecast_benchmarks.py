# =============================================================================
# MODULE 08 — RISK FORECAST BENCHMARKS
# =============================================================================

required = [
    "risk_model_df",
    "range_eval",
    "build_forward_rv_target",
]

missing = [
    name
    for name in required
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing dependencies: {missing}. "
        "Run Module 07 before Module 08."
    )


benchmark_data = build_forward_rv_target(
    risk_model_df,
    horizon=3,
)

target = "Forward_RV_3"

benchmark_eval = (
    benchmark_data
    .loc[range_eval.index]
    .copy()
)


raw_range_ic = (
    benchmark_eval[
        [
            "Log_Range",
            target,
        ]
    ]
    .corr(method="spearman")
    .iloc[0, 1]
)


mean_predictions = []
median_predictions = []
persistence_predictions = []

for current_time in benchmark_eval.index:

    eligible = (
        (benchmark_data.index < current_time)
        & benchmark_data[target].notna()
        & benchmark_data["Target_End_Time"].notna()
        & (
            benchmark_data["Target_End_Time"]
            <= current_time
        )
    )

    history = (
        benchmark_data
        .loc[
            eligible,
            target,
        ]
    )

    if history.empty:
        mean_predictions.append(np.nan)
        median_predictions.append(np.nan)
        persistence_predictions.append(np.nan)
        continue

    mean_predictions.append(
        history.mean()
    )

    median_predictions.append(
        history.median()
    )

    persistence_predictions.append(
        history.iloc[-1]
    )


benchmark_eval["Historical_Mean_Pred"] = (
    mean_predictions
)

benchmark_eval["Historical_Median_Pred"] = (
    median_predictions
)

benchmark_eval["Persistence_Pred"] = (
    persistence_predictions
)

benchmark_eval["Range_Ridge_Pred"] = (
    range_eval["Predicted_Forward_RV"]
)


def evaluate_prediction(
    df: pd.DataFrame,
    prediction_column: str,
) -> dict:

    sample = (
        df[
            [
                target,
                prediction_column,
            ]
        ]
        .dropna()
    )

    actual = sample[target]
    predicted = sample[prediction_column]

    errors = actual - predicted

    return {
        "Observations": len(sample),
        "Spearman_IC": (
            sample
            .corr(method="spearman")
            .iloc[0, 1]
        ),
        "MAE": np.abs(errors).mean(),
        "RMSE": np.sqrt(
            np.square(errors).mean()
        ),
    }


benchmark_comparison = pd.DataFrame(
    {
        "RANGE_RIDGE": evaluate_prediction(
            benchmark_eval,
            "Range_Ridge_Pred",
        ),
        "HIST_MEAN": evaluate_prediction(
            benchmark_eval,
            "Historical_Mean_Pred",
        ),
        "HIST_MEDIAN": evaluate_prediction(
            benchmark_eval,
            "Historical_Median_Pred",
        ),
        "PERSISTENCE": evaluate_prediction(
            benchmark_eval,
            "Persistence_Pred",
        ),
    }
)


print(
    f"Raw Log_Range → Forward_RV_3 "
    f"Spearman IC: {raw_range_ic:.4f}"
)

display(
    benchmark_comparison.round(6)
)
