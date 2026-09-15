# =============================================================================
# MODULE 09 — NON-OVERLAPPING OOS ROBUSTNESS
# =============================================================================

required = [
    "benchmark_eval",
    "evaluate_prediction",
]

missing = [
    name
    for name in required
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing dependencies: {missing}. "
        "Run Module 08 before Module 09."
    )


HORIZON = 3

non_overlap_df = (
    benchmark_eval
    .copy()
    .sort_index()
)

non_overlap_df["Session_ID"] = (
    non_overlap_df.index.normalize()
)


selected_indices = []

for _, session in non_overlap_df.groupby("Session_ID"):

    session = session.sort_index()

    selected_indices.extend(
        session.iloc[::HORIZON].index
    )


non_overlap_eval = (
    non_overlap_df
    .loc[selected_indices]
    .sort_index()
    .copy()
)


raw_range_non_overlap_ic = (
    non_overlap_eval[
        [
            "Log_Range",
            target,
        ]
    ]
    .corr(method="spearman")
    .iloc[0, 1]
)


non_overlap_comparison = pd.DataFrame(
    {
        "RANGE_RIDGE": evaluate_prediction(
            non_overlap_eval,
            "Range_Ridge_Pred",
        ),
        "HIST_MEAN": evaluate_prediction(
            non_overlap_eval,
            "Historical_Mean_Pred",
        ),
        "HIST_MEDIAN": evaluate_prediction(
            non_overlap_eval,
            "Historical_Median_Pred",
        ),
        "PERSISTENCE": evaluate_prediction(
            non_overlap_eval,
            "Persistence_Pred",
        ),
    }
)


print(
    f"Overlapping observations: "
    f"{len(benchmark_eval):,}"
)

print(
    f"Non-overlapping observations: "
    f"{len(non_overlap_eval):,}"
)

print(
    f"Raw Log_Range → {target} "
    f"non-overlap Spearman IC: "
    f"{raw_range_non_overlap_ic:.4f}"
)

display(
    non_overlap_comparison.round(6)
)
