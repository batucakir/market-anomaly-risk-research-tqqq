# =============================================================================
# MODULE 05 — REGIME MODEL DIAGNOSTICS
# =============================================================================

required = ["wf_df"]

missing = [
    name
    for name in required
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing dependencies: {missing}. "
        "Run Module 04 before Module 05."
    )


REGIME_NAMES = {
    0: "LOW",
    1: "ELEVATED",
    2: "HIGH",
}

PROBABILITY_COLUMNS = [
    "P_Low_Risk",
    "P_Elevated_Risk",
    "P_High_Risk",
]


window_count = int(
    wf_df["WF_Window_ID"]
    .nunique()
)

state_counts = (
    wf_df[
        [
            "WF_Window_ID",
            "Optimal_N",
        ]
    ]
    .drop_duplicates()
    ["Optimal_N"]
    .astype(int)
    .value_counts()
    .sort_index()
    .rename("Windows")
    .to_frame()
)

regime_distribution = (
    wf_df["WF_Regime"]
    .astype(int)
    .map(REGIME_NAMES)
    .value_counts(normalize=True)
    .mul(100)
    .rename("Share_Pct")
    .to_frame()
)

confidence_summary = (
    wf_df["Regime_Confidence"]
    .describe()
    .rename("Regime_Confidence")
    .to_frame()
)

entropy_summary = (
    wf_df["Posterior_Entropy"]
    .describe()
    .rename("Posterior_Entropy")
    .to_frame()
)

probability_sum = (
    wf_df[PROBABILITY_COLUMNS]
    .sum(axis=1)
)

max_probability_error = float(
    np.abs(
        probability_sum - 1.0
    ).max()
)


print(
    f"OOS bars: {len(wf_df):,} | "
    f"Windows: {window_count} | "
    f"{wf_df.index.min()} → {wf_df.index.max()}"
)

print(
    f"Maximum probability-sum error: "
    f"{max_probability_error:.2e}"
)

display(state_counts)
display(regime_distribution.round(2))
display(confidence_summary.round(4))
display(entropy_summary.round(4))
