# =============================================================================
# MODULE 06 — HMM WINDOW DIAGNOSTICS
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
        "Run Module 04 before Module 06."
    )


regime_names = {
    0: "LOW",
    1: "ELEVATED",
    2: "HIGH",
}


hmm_diag = (
    wf_df
    .copy()
    .sort_index()
)

hmm_diag["Regime_Name"] = (
    hmm_diag["WF_Regime"]
    .astype(int)
    .map(regime_names)
)

hmm_diag["Confidence_GE_0999"] = (
    hmm_diag["Regime_Confidence"] >= 0.999
)

hmm_diag["Confidence_GE_09999"] = (
    hmm_diag["Regime_Confidence"] >= 0.9999
)


window_quality = (
    hmm_diag
    .groupby("WF_Window_ID")
    .agg(
        Bars=("WF_Regime", "size"),
        Optimal_N=("Optimal_N", "first"),
        Mean_Confidence=("Regime_Confidence", "mean"),
        Median_Confidence=("Regime_Confidence", "median"),
        Min_Confidence=("Regime_Confidence", "min"),
        Confidence_GE_0999_Pct=("Confidence_GE_0999", "mean"),
        Confidence_GE_09999_Pct=("Confidence_GE_09999", "mean"),
        Mean_Entropy=("Posterior_Entropy", "mean"),
        Median_Entropy=("Posterior_Entropy", "median"),
    )
)

window_quality[
    "Confidence_GE_0999_Pct"
] *= 100

window_quality[
    "Confidence_GE_09999_Pct"
] *= 100


window_regime_pct = (
    pd.crosstab(
        hmm_diag["WF_Window_ID"],
        hmm_diag["Regime_Name"],
        normalize="index",
    )
    .mul(100)
    .reindex(
        columns=[
            "LOW",
            "ELEVATED",
            "HIGH",
        ],
        fill_value=0.0,
    )
)


certainty_summary = pd.DataFrame(
    {
        "Metric": [
            "Confidence >= 0.999",
            "Confidence >= 0.9999",
            "Entropy < 1e-6",
        ],
        "Share_Pct": [
            100.0
            * hmm_diag["Confidence_GE_0999"].mean(),

            100.0
            * hmm_diag["Confidence_GE_09999"].mean(),

            100.0
            * (
                hmm_diag["Posterior_Entropy"] < 1e-6
            ).mean(),
        ],
    }
)


print("HMM window diagnostics")

display(
    window_quality.round(4)
)

display(
    window_regime_pct.round(2)
)

display(
    certainty_summary.round(2)
)
