# =============================================================================
# MODULE 02 — INTRADAY DATA INGESTION
# =============================================================================

from pathlib import Path

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(
    ticker: str,
    interval: str,
    period: str,
) -> Path:
    return CACHE_DIR / f"{ticker}_{interval}_{period}.pkl"


def _validate_intraday_data(
    df: pd.DataFrame,
    ticker: str,
) -> pd.DataFrame:

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns for {ticker}: {missing_columns}"
        )

    df = (
        df[required_columns]
        .copy()
        .sort_index()
    )

    df = df.loc[
        ~df.index.duplicated(keep="last")
    ]

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df.index = df.index.tz_convert(MARKET_TZ)

    invalid_ohlc = (
        (df["High"] < df["Low"])
        | (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
        | (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
    )

    if invalid_ohlc.any():
        logger.warning(
            "%d invalid OHLC bars removed for %s.",
            int(invalid_ohlc.sum()),
            ticker,
        )

        df = df.loc[~invalid_ohlc]

    df = df.loc[
        df["Volume"] > 0
    ]

    if df.empty:
        raise ValueError(
            f"No valid intraday bars remain for {ticker}."
        )

    return df


def fetch_intraday_us_data(
    ticker: str,
    interval: str = INTERVAL,
    period: str = PERIOD,
    refresh: bool = False,
) -> pd.DataFrame:

    cache_file = _cache_path(
        ticker,
        interval,
        period,
    )

    if cache_file.exists() and not refresh:
        logger.info(
            "Loading %s from cache.",
            ticker,
        )

        df = pd.read_pickle(
            cache_file
        )

        return _validate_intraday_data(
            df,
            ticker,
        )

    logger.info(
        "Downloading %s | interval=%s | period=%s",
        ticker,
        interval,
        period,
    )

    try:
        df = yf.download(
            ticker,
            interval=interval,
            period=period,
            auto_adjust=True,
            prepost=False,
            actions=False,
            repair=True,
            progress=False,
            threads=False,
            multi_level_index=False,
            timeout=30,
        )
    except Exception as exc:

        if cache_file.exists():
            logger.warning(
                "Download failed for %s. Using cached data.",
                ticker,
            )

            return _validate_intraday_data(
                pd.read_pickle(cache_file),
                ticker,
            )

        raise RuntimeError(
            f"Failed to download intraday data for {ticker}."
        ) from exc

    if df.empty:

        if cache_file.exists():
            logger.warning(
                "Empty response for %s. Using cached data.",
                ticker,
            )

            return _validate_intraday_data(
                pd.read_pickle(cache_file),
                ticker,
            )

        raise RuntimeError(
            f"No intraday data returned for {ticker}. "
            "Yahoo may be rate limited."
        )

    df = _validate_intraday_data(
        df,
        ticker,
    )

    df.to_pickle(
        cache_file
    )

    logger.info(
        "Loaded %d bars for %s.",
        len(df),
        ticker,
    )

    return df


df_intraday = fetch_intraday_us_data(
    REGIME_TICKER
)

display(
    df_intraday.tail()
)
