# =============================================================================
# MODULE 03 — FEATURE ENGINEERING
# =============================================================================

def engineer_intraday_features(
    df: pd.DataFrame,
    z_window: int = 20,
    realized_vol_window: int = 10,
    ewma_span: int = 20,
    min_tod_history: int = 5,
) -> pd.DataFrame:

    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    features = df.copy().sort_index()

    session_date = pd.Series(
        features.index.date,
        index=features.index,
    )

    same_session = session_date.eq(
        session_date.shift(1)
    )

    log_close = np.log(
        features["Close"]
    )

    features["Intraday_Return"] = (
        log_close
        .diff()
        .where(same_session)
    )

    features["Overnight_Return"] = (
        np.log(features["Open"])
        -
        np.log(features["Close"].shift(1))
    ).where(~same_session)

    valid_returns = (
        features["Intraday_Return"]
        .dropna()
    )

    realized_vol = np.sqrt(
        valid_returns
        .pow(2)
        .rolling(
            window=realized_vol_window,
            min_periods=realized_vol_window,
        )
        .sum()
    )

    features["Realized_Vol_10"] = (
        realized_vol
        .reindex(features.index)
    )

    features["EWMA_Vol"] = (
        features["Intraday_Return"]
        .ewm(
            span=ewma_span,
            adjust=False,
            min_periods=ewma_span,
        )
        .std()
    )

    typical_price = (
        features["High"]
        + features["Low"]
        + features["Close"]
    ) / 3.0

    cumulative_tpv = (
        (typical_price * features["Volume"])
        .groupby(session_date)
        .cumsum()
    )

    cumulative_volume = (
        features["Volume"]
        .groupby(session_date)
        .cumsum()
    )

    features["Session_VWAP_Proxy"] = (
        cumulative_tpv
        / cumulative_volume
    )

    features["VWAP_Distance"] = (
        features["Close"]
        / features["Session_VWAP_Proxy"]
        - 1.0
    )

    rolling_mean = (
        valid_returns
        .rolling(
            window=z_window,
            min_periods=z_window,
        )
        .mean()
        .shift(1)
    )

    rolling_std = (
        valid_returns
        .rolling(
            window=z_window,
            min_periods=z_window,
        )
        .std(ddof=1)
        .shift(1)
    )

    prior_mean = (
        rolling_mean
        .reindex(features.index)
    )

    prior_std = (
        rolling_std
        .reindex(features.index)
        .where(lambda x: x > 1e-12)
    )

    features["Return_Surprise_Z"] = (
        features["Intraday_Return"]
        - prior_mean
    ) / prior_std

    surprise = (
        features["Return_Surprise_Z"]
    )

    features["Return_Surprise_SignedLog"] = (
        np.sign(surprise)
        * np.log1p(np.abs(surprise))
    )

    features["Log_Range"] = np.log(
        features["High"]
        / features["Low"]
    )

    tod_slot = (
        features.index
        .strftime("%H:%M")
    )

    prior_tod_median = (
        features["Volume"]
        .groupby(tod_slot)
        .transform(
            lambda series:
                series
                .shift(1)
                .expanding(
                    min_periods=min_tod_history
                )
                .median()
        )
    )

    features["Relative_Volume"] = (
        features["Volume"]
        / prior_tod_median
    )

    features["Log_Relative_Volume"] = np.log(
        features["Relative_Volume"]
    )

    eps = 1e-12

    features["Log_EWMA_Vol"] = np.log(
        features["EWMA_Vol"]
        .clip(lower=eps)
    )

    features["Log_Realized_Vol_10"] = np.log(
        features["Realized_Vol_10"]
        .clip(lower=eps)
    )

    model_features = [
        "Intraday_Return",
        "Return_Surprise_SignedLog",
        "Log_Range",
        "EWMA_Vol",
        "VWAP_Distance",
        "Log_Relative_Volume",
    ]

    features = (
        features
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=model_features
        )
    )

    return features


features_df = engineer_intraday_features(
    df_intraday
)

print(
    f"Features: {len(features_df):,} rows | "
    f"{features_df.index.min()} → {features_df.index.max()}"
)

display(
    features_df[
        [
            "Intraday_Return",
            "Overnight_Return",
            "VWAP_Distance",
            "Return_Surprise_Z",
            "Return_Surprise_SignedLog",
            "Log_Range",
            "Log_Relative_Volume",
            "Realized_Vol_10",
            "EWMA_Vol",
        ]
    ].tail()
)
