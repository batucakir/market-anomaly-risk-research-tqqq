# ==============================================================================
# MODULE 11 — OOS RISK SIGNAL ECONOMIC VALIDATION
# ==============================================================================

required_objects = [
    "features_df",
    "wf_df",
    "risk_range_only",
    "RISK_MODEL_FINGERPRINT",
]

missing_objects = [
    name
    for name in required_objects
    if name not in globals()
]

if missing_objects:
    raise RuntimeError(
        "MODULE 11 missing required objects: "
        f"{missing_objects}"
    )


# ==============================================================================
# 1. BUILD SAME-SESSION FORWARD 3-BAR RETURN
# ==============================================================================

economic_df = (
    features_df[
        ["Intraday_Return"]
    ]
    .copy()
    .sort_index()
)

session_id = pd.Series(
    economic_df.index.normalize(),
    index=economic_df.index,
)

future_return_columns = []

for k in range(1, 4):

    column = f"_Forward_Return_{k}"

    economic_df[column] = (
        economic_df["Intraday_Return"]
        .groupby(session_id)
        .shift(-k)
    )

    future_return_columns.append(
        column
    )


economic_df["Forward_3_Return"] = (
    np.exp(
        economic_df[
            future_return_columns
        ]
        .sum(
            axis=1,
            min_count=3,
        )
    )
    - 1.0
)

economic_df = economic_df.drop(
    columns=future_return_columns
)


# ==============================================================================
# 2. COMMON STRICT-OOS SAMPLE
# ==============================================================================

risk_part = (
    risk_range_only[
        [
            "Predicted_Forward_RV",
            "Forward_RV_3",
        ]
    ]
    .copy()
)

hmm_columns = [
    "WF_Regime",
    "Continuous_Risk_Score",
    "P_High_Risk",
    "Regime_Confidence",
]

missing_hmm_columns = [
    column
    for column in hmm_columns
    if column not in wf_df.columns
]

if missing_hmm_columns:
    raise RuntimeError(
        "MODULE 11 missing HMM columns: "
        f"{missing_hmm_columns}"
    )


risk_validation = (
    risk_part
    .join(
        wf_df[hmm_columns],
        how="inner",
    )
    .join(
        economic_df[
            ["Forward_3_Return"]
        ],
        how="inner",
    )
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
    .dropna()
    .sort_index()
)


if risk_validation.empty:
    raise RuntimeError(
        "MODULE 11 produced no common OOS observations."
    )


# ==============================================================================
# 3. ECONOMIC TARGETS
# ==============================================================================

risk_validation[
    "Forward_3_Loss"
] = (
    -risk_validation[
        "Forward_3_Return"
    ]
).clip(
    lower=0.0
)

risk_validation[
    "Risk_Forecast_Error"
] = (
    risk_validation[
        "Forward_RV_3"
    ]
    -
    risk_validation[
        "Predicted_Forward_RV"
    ]
)


# ==============================================================================
# 4. SIGNAL / TARGET CORRELATION
# ==============================================================================

signal_columns = {
    "RANGE_RIDGE":
        "Predicted_Forward_RV",

    "HMM_CONTINUOUS":
        "Continuous_Risk_Score",

    "HMM_HIGH_PROB":
        "P_High_Risk",
}

target_columns = {
    "REALIZED_RV":
        "Forward_RV_3",

    "FORWARD_LOSS":
        "Forward_3_Loss",

    "FORWARD_RETURN":
        "Forward_3_Return",

    "RISK_FORECAST_ERROR":
        "Risk_Forecast_Error",
}


def build_signal_table(df):

    rows = []

    for signal_name, signal_column in signal_columns.items():

        for target_name, target_column in target_columns.items():

            rho = (
                df[
                    [
                        signal_column,
                        target_column,
                    ]
                ]
                .corr(
                    method="spearman"
                )
                .iloc[0, 1]
            )

            rows.append(
                {
                    "Signal":
                        signal_name,

                    "Target":
                        target_name,

                    "Spearman":
                        rho,

                    "Observations":
                        len(df),
                }
            )

    return (
        pd.DataFrame(rows)
        .set_index(
            [
                "Signal",
                "Target",
            ]
        )
    )


risk_signal_full = (
    build_signal_table(
        risk_validation
    )
)


# ==============================================================================
# 5. NON-OVERLAPPING 3-BAR ROBUSTNESS
# ==============================================================================

non_overlap_indices = []

for _, section in risk_validation.groupby(
    risk_validation.index.normalize(),
    sort=True,
):

    non_overlap_indices.extend(
        section.index[::3]
    )


risk_validation_nonoverlap = (
    risk_validation
    .loc[
        non_overlap_indices
    ]
    .copy()
)


risk_signal_nonoverlap = (
    build_signal_table(
        risk_validation_nonoverlap
    )
)


# ==============================================================================
# 6. REGIME ECONOMIC PROFILE
# ==============================================================================

REGIME_NAMES = {
    0: "LOW",
    1: "ELEVATED",
    2: "HIGH",
}

risk_validation[
    "Regime"
] = (
    risk_validation[
        "WF_Regime"
    ]
    .round()
    .astype(int)
    .map(
        REGIME_NAMES
    )
)


regime_economic_profile = (
    risk_validation
    .groupby(
        "Regime"
    )
    .agg(
        Observations=(
            "Forward_RV_3",
            "size",
        ),

        Mean_Predicted_RV=(
            "Predicted_Forward_RV",
            "mean",
        ),

        Mean_Realized_RV=(
            "Forward_RV_3",
            "mean",
        ),

        Mean_Forward_Return=(
            "Forward_3_Return",
            "mean",
        ),

        Median_Forward_Return=(
            "Forward_3_Return",
            "median",
        ),

        Mean_Forward_Loss=(
            "Forward_3_Loss",
            "mean",
        ),

        Negative_Return_Pct=(
            "Forward_3_Return",
            lambda x:
                100.0
                *
                (x < 0).mean(),
        ),

        Mean_Risk_Forecast_Error=(
            "Risk_Forecast_Error",
            "mean",
        ),
    )
)


regime_order = [
    regime
    for regime in [
        "LOW",
        "ELEVATED",
        "HIGH",
    ]
    if regime in regime_economic_profile.index
]

regime_economic_profile = (
    regime_economic_profile
    .reindex(
        regime_order
    )
)


# ==============================================================================
# 7. OUTPUT
# ==============================================================================

print("=" * 100)
print("MODULE 11 — OOS RISK SIGNAL ECONOMIC VALIDATION")
print("=" * 100)

print(
    f"\nFrozen risk fingerprint : "
    f"{RISK_MODEL_FINGERPRINT}"
)

print(
    f"Common OOS observations : "
    f"{len(risk_validation)}"
)

print(
    f"Non-overlapping sample  : "
    f"{len(risk_validation_nonoverlap)}"
)

print(
    "\n1) SIGNAL INFORMATION — FULL COMMON OOS SAMPLE"
)

display(
    risk_signal_full.round(6)
)

print(
    "\n2) SIGNAL INFORMATION — NON-OVERLAPPING 3-BAR SAMPLE"
)

display(
    risk_signal_nonoverlap.round(6)
)

print(
    "\n3) HMM REGIME ECONOMIC PROFILE"
)

display(
    regime_economic_profile.round(6)
)

print(
    "\nInterpretation:"
)

print(
    "  RANGE_RIDGE is the frozen forward-volatility forecast."
)

print(
    "  HMM variables are tested as descriptive risk information only."
)

print(
    "  No exposure threshold or position-sizing rule is introduced."
)

print(
    "  HMM value beyond RANGE_RIDGE should appear in "
    "Risk_Forecast_Error or downside relationships."
)

print(
    "\n[+] MODULE 11 COMPLETE."
)
