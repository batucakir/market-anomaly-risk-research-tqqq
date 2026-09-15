# ==============================================================================
# MODULE 15 — HISTORICAL BLOCK 38B
# BROAD PIT UNIVERSE + DAILY MARKET DATA + CAUSAL ELIGIBILITY
#
# Historical architecture preserved.
#
# ONLY restoration patch:
#   compatibility-safe loader for the historical daily-price pickle.
#
# NO:
#   model change
#   universe-rule change
#   eligibility-rule change
#   parameter change
#   future-return filter
# ==============================================================================

import os
import sys
import time
import shutil
import tempfile
import subprocess
import importlib
import warnings

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from IPython.display import display


print("=" * 118)
print(
    "MODULE 15 / HISTORICAL BLOCK 38B — "
    "BROAD PIT UNIVERSE + DAILY DATA + CAUSAL ELIGIBILITY"
)
print("=" * 118)


# ==============================================================================
# 0. REQUIRED HISTORICAL OBJECTS
# ==============================================================================

M15_EXPECTED_V4_MASTER_FINGERPRINT = (
    "7f2b6040db974ee5d1df151d9fa49cab"
    "79dea945cd5fe19d442821a35b7c7bd8"
)


M15_REQUIRED = [
    "B38_PIT_RAW",
    "B38_PIT_START_DATE",
    "V4_COMPARISON_START",
    "V4_DATA_END_DATE",
    "V4_MASTER_FINGERPRINT",
]


M15_MISSING = [
    x
    for x in M15_REQUIRED
    if x not in globals()
]


if M15_MISSING:
    raise RuntimeError(
        "MODULE 15 missing required objects: "
        f"{M15_MISSING}. "
        "Modules 13 and 14 must run first."
    )


if B38_PIT_RAW.empty:
    raise RuntimeError(
        "B38_PIT_RAW is empty."
    )


if (
    V4_MASTER_FINGERPRINT
    !=
    M15_EXPECTED_V4_MASTER_FINGERPRINT
):
    raise RuntimeError(
        "\nV4 lineage mismatch.\n"
        f"Expected: {M15_EXPECTED_V4_MASTER_FINGERPRINT}\n"
        f"Actual  : {V4_MASTER_FINGERPRINT}\n"
        "STOP."
    )


print(
    "\n[15-LINEAGE] V4 master fingerprint verified:"
)

print(
    V4_MASTER_FINGERPRINT
)


# ==============================================================================
# 1. HISTORICAL DATE TYPES
# ==============================================================================

def m15_naive_date(x):

    x = pd.Timestamp(x)

    if x.tzinfo is not None:
        x = (
            x
            .tz_convert("America/New_York")
            .tz_localize(None)
        )

    return x.normalize()


B38_PIT_START_DATE = m15_naive_date(
    B38_PIT_START_DATE
)

V4_COMPARISON_START = m15_naive_date(
    V4_COMPARISON_START
)

V4_DATA_END_DATE = m15_naive_date(
    V4_DATA_END_DATE
)


# Historical Block38B warm-up.
# DATA warm-up only; not a trading parameter.

B38_PRICE_START_DATE = (
    B38_PIT_START_DATE
    -
    pd.Timedelta(days=400)
)


print(
    "\nPIT start          :",
    B38_PIT_START_DATE.date()
)

print(
    "Price warmup start :",
    B38_PRICE_START_DATE.date()
)

print(
    "Comparison start   :",
    V4_COMPARISON_START.date()
)

print(
    "Research end       :",
    V4_DATA_END_DATE.date()
)


# ==============================================================================
# 2. TICKER NORMALIZATION
# ==============================================================================

def b38b_normalize_ticker(ticker):

    if pd.isna(ticker):
        return None

    ticker = (
        str(ticker)
        .strip()
        .upper()
    )

    if ticker in {
        "",
        "NAN",
        "NONE",
    }:
        return None

    # Yahoo class-share convention.
    ticker = ticker.replace(
        ".",
        "-"
    )

    return ticker


# ==============================================================================
# 3. CLEAN EXACT PIT MEMBERSHIP
# ==============================================================================

pit = (
    B38_PIT_RAW
    .copy()
)


required_pit_columns = {
    "as_of",
    "ticker",
}


missing_pit_columns = (
    required_pit_columns
    -
    set(pit.columns)
)


if missing_pit_columns:
    raise RuntimeError(
        "B38_PIT_RAW missing columns: "
        f"{sorted(missing_pit_columns)}"
    )


pit[
    "Snapshot_AsOf"
] = pd.to_datetime(
    pit["as_of"],
    errors="coerce",
)


if getattr(
    pit["Snapshot_AsOf"].dt,
    "tz",
    None,
) is not None:

    pit[
        "Snapshot_AsOf"
    ] = (
        pit[
            "Snapshot_AsOf"
        ]
        .dt.tz_convert(
            "America/New_York"
        )
        .dt.tz_localize(None)
    )


pit[
    "Snapshot_AsOf"
] = (
    pit[
        "Snapshot_AsOf"
    ]
    .dt.normalize()
)


pit[
    "Ticker"
] = (
    pit[
        "ticker"
    ]
    .map(
        b38b_normalize_ticker
    )
)


V4_PIT_STOCK_MEMBERSHIP = (

    pit[
        [
            "Snapshot_AsOf",
            "Ticker",
        ]
    ]

    .dropna()

    .drop_duplicates(
        subset=[
            "Snapshot_AsOf",
            "Ticker",
        ]
    )

    .sort_values(
        [
            "Snapshot_AsOf",
            "Ticker",
        ]
    )

    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 4. PIT SANITY
# ==============================================================================

B38_SNAPSHOT_COUNTS = (

    V4_PIT_STOCK_MEMBERSHIP

    .groupby(
        "Snapshot_AsOf"
    )[
        "Ticker"
    ]

    .nunique()
)


median_snapshot_count = float(
    B38_SNAPSHOT_COUNTS.median()
)


if not (
    1400
    <=
    median_snapshot_count
    <=
    1600
):
    raise RuntimeError(
        "PIT stock-universe sanity failed. "
        f"Median snapshot size="
        f"{median_snapshot_count:.0f}"
    )


print(
    "\nPIT snapshots       :",
    f"{len(B38_SNAPSHOT_COUNTS):,}"
)

print(
    "Historical stocks   :",
    f"{V4_PIT_STOCK_MEMBERSHIP['Ticker'].nunique():,}"
)

print(
    "Median PIT members  :",
    f"{median_snapshot_count:,.0f}"
)


# ==============================================================================
# 5. HISTORICAL PREDECLARED ETF SLEEVE
# ==============================================================================

B38_ETF_SLEEVE = (

    # Broad beta
    "SPY",
    "QQQ",
    "DIA",
    "IWM",

    # Sector ETFs
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",

    # Tactical leveraged candidate
    "TQQQ",
)


B38_HISTORICAL_STOCKS = tuple(

    sorted(

        V4_PIT_STOCK_MEMBERSHIP[
            "Ticker"
        ]
        .unique()
    )
)


V4_BROAD_UNIVERSE_TICKERS = tuple(

    sorted(

        set(
            B38_HISTORICAL_STOCKS
        )

        |

        set(
            B38_ETF_SLEEVE
        )
    )
)


print(
    "\nHistorical stock symbols :",
    f"{len(B38_HISTORICAL_STOCKS):,}"
)

print(
    "ETF candidates           :",
    f"{len(B38_ETF_SLEEVE):,}"
)

print(
    "Total download candidates:",
    f"{len(V4_BROAD_UNIVERSE_TICKERS):,}"
)

print(
    "TQQQ included            :",
    "TQQQ"
    in
    V4_BROAD_UNIVERSE_TICKERS
)


# ==============================================================================
# 6. EXACT HISTORICAL CAUSAL INVESTABILITY RULES
# ==============================================================================

B38_LIQUIDITY_LOOKBACK = 60

B38_MIN_VALID_DAYS = 50

B38_MIN_PRICE = 3.00

B38_MIN_MEDIAN_DOLLAR_VOLUME = (
    5_000_000.0
)


# Download mechanics only.

B38_BATCH_SIZE = 100

B38_RETRY_BATCH_SIZE = 20

B38_MAX_ATTEMPTS = 2


# ==============================================================================
# 7. HISTORICAL CACHE
# ==============================================================================

B38_CACHE_DIR = Path(
    "./v4_cache"
)

B38_CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


B38_CACHE_FILE = (

    B38_CACHE_DIR

    /

    (
        "block38b_daily_prices_"
        f"{B38_PRICE_START_DATE.strftime('%Y%m%d')}_"
        f"{V4_DATA_END_DATE.strftime('%Y%m%d')}.pkl"
    )
)


B38_COMPAT_CSV = (
    B38_CACHE_DIR
    /
    (
        "block38b_daily_prices_"
        f"{B38_PRICE_START_DATE.strftime('%Y%m%d')}_"
        f"{V4_DATA_END_DATE.strftime('%Y%m%d')}"
        "_py39_compat.csv"
    )
)


# ==============================================================================
# 8. PICKLE COMPATIBILITY LOADER
# ==============================================================================
#
# Historical-data restoration ONLY.
#
# Some previously generated cache files were serialized under a newer NumPy
# namespace ("numpy._core.*"), while this notebook runs Python 3.9 with an
# older NumPy namespace ("numpy.core.*").
#
# This changes ZERO research data/rules.
# ==============================================================================

def m15_install_numpy_pickle_aliases():

    alias_pairs = {

        "numpy._core":
            "numpy.core",

        "numpy._core.numeric":
            "numpy.core.numeric",

        "numpy._core.multiarray":
            "numpy.core.multiarray",

        "numpy._core.umath":
            "numpy.core.umath",

        "numpy._core.numerictypes":
            "numpy.core.numerictypes",

        "numpy._core.fromnumeric":
            "numpy.core.fromnumeric",

        "numpy._core._multiarray_umath":
            "numpy.core._multiarray_umath",
    }


    for old_name, local_name in (
        alias_pairs.items()
    ):

        try:

            if old_name not in sys.modules:

                sys.modules[
                    old_name
                ] = importlib.import_module(
                    local_name
                )

        except Exception:
            pass


def m15_convert_pickle_with_isolated_python(
    pickle_path,
    csv_path,
):

    uv = (
        globals().get(
            "uv_exe"
        )
        or
        shutil.which(
            "uv"
        )
    )


    if uv is None:

        raise RuntimeError(
            "Historical pickle requires compatibility conversion, "
            "but uv is unavailable. Module 14 should have installed it."
        )


    converter = r'''
import sys
import pandas as pd

source = sys.argv[1]
target = sys.argv[2]

df = pd.read_pickle(source)

if df is None or df.empty:
    raise RuntimeError("Historical price pickle is empty.")

df.to_csv(
    target,
    index=False,
)

print("ROWS=", len(df))
print("COLS=", list(df.columns))
'''


    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as f:

        f.write(
            converter
        )

        converter_path = (
            f.name
        )


    cmd = [
        uv,
        "run",

        "--python",
        "3.11",

        "--with",
        "pandas",

        "--with",
        "numpy",

        "python",
        converter_path,

        str(
            pickle_path
        ),

        str(
            csv_path
        ),
    ]


    try:

        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )


    except subprocess.CalledProcessError as exc:

        print(
            "\n========== CACHE CONVERTER STDOUT =========="
        )

        print(
            exc.stdout
        )

        print(
            "\n========== CACHE CONVERTER STDERR =========="
        )

        print(
            exc.stderr
        )


        raise RuntimeError(
            "Historical daily-price pickle compatibility "
            "conversion failed."
        ) from exc


    finally:

        try:
            os.remove(
                converter_path
            )
        except Exception:
            pass


    print(
        "\n[15-DATA] Compatibility conversion complete."
    )

    print(
        result.stdout
    )


def m15_load_historical_price_cache(
    cache_file,
):

    # --------------------------------------------------------------------------
    # Normal route
    # --------------------------------------------------------------------------

    try:

        data = pd.read_pickle(
            cache_file
        )

        return (
            data,
            "NATIVE_PICKLE"
        )


    except (
        ModuleNotFoundError,
        ImportError,
        AttributeError,
    ) as exc:

        print(
            "\n[15-DATA] Native pickle load hit "
            "NumPy/Python compatibility issue:"
        )

        print(
            type(exc).__name__,
            str(exc)
        )


    # --------------------------------------------------------------------------
    # Namespace alias route
    # --------------------------------------------------------------------------

    m15_install_numpy_pickle_aliases()


    try:

        data = pd.read_pickle(
            cache_file
        )

        return (
            data,
            "PICKLE_NAMESPACE_COMPAT"
        )


    except Exception as exc:

        print(
            "[15-DATA] Namespace compatibility retry did not succeed:"
        )

        print(
            type(exc).__name__,
            str(exc)
        )


    # --------------------------------------------------------------------------
    # Isolated Python 3.11 conversion route
    # --------------------------------------------------------------------------

    if not B38_COMPAT_CSV.exists():

        print(
            "\n[15-DATA] Converting historical cache under isolated Python 3.11..."
        )

        m15_convert_pickle_with_isolated_python(
            cache_file,
            B38_COMPAT_CSV,
        )


    data = pd.read_csv(
        B38_COMPAT_CSV,
        low_memory=False,
    )


    return (
        data,
        "ISOLATED_PY311_COMPAT_CSV"
    )


# ==============================================================================
# 9. YFINANCE OUTPUT PARSER
# ==============================================================================

def b38b_extract_ticker_frame(
    raw,
    ticker,
):

    if (
        raw is None
        or
        raw.empty
    ):
        return None


    if isinstance(
        raw.columns,
        pd.MultiIndex,
    ):

        level0 = set(
            map(
                str,
                raw.columns.get_level_values(0)
            )
        )

        level1 = set(
            map(
                str,
                raw.columns.get_level_values(1)
            )
        )


        if ticker in level0:

            try:
                return (
                    raw[
                        ticker
                    ]
                    .copy()
                )

            except Exception:
                return None


        if ticker in level1:

            try:

                return (
                    raw.xs(
                        ticker,
                        axis=1,
                        level=1,
                    )
                    .copy()
                )

            except Exception:
                return None


        return None


    return (
        raw.copy()
    )


# ==============================================================================
# 10. CLEAN ONE TICKER
# ==============================================================================

def b38b_clean_price_frame(
    ticker,
    frame,
):

    if (
        frame is None
        or
        frame.empty
    ):
        return None


    out = (
        frame.copy()
    )


    if isinstance(
        out.columns,
        pd.MultiIndex,
    ):

        out.columns = [
            str(x[0])
            for x in out.columns
        ]


    out.columns = [
        str(x).strip()
        for x in out.columns
    ]


    required = {
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    }


    if not required.issubset(
        set(
            out.columns
        )
    ):
        return None


    out = (
        out.reset_index()
    )


    first_col = (
        out.columns[0]
    )


    out = (
        out.rename(
            columns={
                first_col:
                    "Date"
            }
        )
    )


    date_series = pd.to_datetime(
        out[
            "Date"
        ],
        errors="coerce",
    )


    if getattr(
        date_series.dt,
        "tz",
        None,
    ) is not None:

        date_series = (
            date_series
            .dt.tz_convert(
                "America/New_York"
            )
            .dt.tz_localize(None)
        )


    out[
        "Date"
    ] = (
        date_series
        .dt.normalize()
    )


    for col in [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]:

        out[
            col
        ] = pd.to_numeric(
            out[
                col
            ],
            errors="coerce",
        )


    if (
        "Adj Close"
        in
        out.columns
    ):

        out[
            "Adj_Close"
        ] = pd.to_numeric(
            out[
                "Adj Close"
            ],
            errors="coerce",
        )

    else:

        out[
            "Adj_Close"
        ] = (
            out[
                "Close"
            ]
        )


    out[
        "Ticker"
    ] = ticker


    out = (

        out[
            [
                "Date",
                "Ticker",
                "Open",
                "High",
                "Low",
                "Close",
                "Adj_Close",
                "Volume",
            ]
        ]

        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        .dropna(
            subset=[
                "Date",
                "Close",
                "Adj_Close",
            ]
        )

        .drop_duplicates(
            subset=[
                "Date",
                "Ticker",
            ],
            keep="last",
        )

        .sort_values(
            "Date"
        )
    )


    out = out[
        (
            out[
                "Close"
            ]
            >
            0
        )
        &
        (
            out[
                "Adj_Close"
            ]
            >
            0
        )
    ]


    if out.empty:
        return None


    return out


# ==============================================================================
# 11. DOWNLOAD BATCH
# ==============================================================================

START_STRING = (
    B38_PRICE_START_DATE
    .strftime(
        "%Y-%m-%d"
    )
)


# yfinance end date is exclusive.

END_STRING = (

    V4_DATA_END_DATE
    +
    pd.Timedelta(
        days=1
    )

).strftime(
    "%Y-%m-%d"
)


def b38b_download_batch(
    tickers,
):

    tickers = list(
        tickers
    )


    if not tickers:
        return []


    raw = None


    for attempt in range(
        1,
        B38_MAX_ATTEMPTS + 1,
    ):

        try:

            with warnings.catch_warnings():

                warnings.simplefilter(
                    "ignore"
                )


                raw = yf.download(

                    tickers=tickers,

                    start=START_STRING,

                    end=END_STRING,

                    interval="1d",

                    auto_adjust=False,

                    actions=False,

                    progress=False,

                    group_by="ticker",

                    threads=True,
                )


            if (
                raw is not None
                and
                not raw.empty
            ):
                break


        except Exception:

            raw = None


        time.sleep(
            1.0
            *
            attempt
        )


    if (
        raw is None
        or
        raw.empty
    ):
        return []


    cleaned = []


    for ticker in tickers:

        section = (
            b38b_extract_ticker_frame(
                raw,
                ticker,
            )
        )


        section = (
            b38b_clean_price_frame(
                ticker,
                section,
            )
        )


        if (
            section is not None
            and
            not section.empty
        ):

            cleaned.append(
                section
            )


    return cleaned


# ==============================================================================
# 12. LOAD HISTORICAL DAILY-PRICE CACHE
# ==============================================================================

M15_CACHE_MODE = (
    "NO_CACHE"
)


if B38_CACHE_FILE.exists():

    print(
        "\n[15-DATA] Loading historical daily-price cache:"
    )

    print(
        B38_CACHE_FILE
    )


    (
        B38_ALL_PRICES,
        M15_CACHE_MODE,
    ) = (
        m15_load_historical_price_cache(
            B38_CACHE_FILE
        )
    )


    print(
        "[15-DATA] Cache mode:",
        M15_CACHE_MODE
    )


else:

    print(
        "\n[15-DATA] Historical daily-price cache not found."
    )

    print(
        "[15-DATA] Missing symbols will be downloaded using "
        "the original Block38B procedure."
    )


    B38_ALL_PRICES = pd.DataFrame(
        columns=[
            "Date",
            "Ticker",
            "Open",
            "High",
            "Low",
            "Close",
            "Adj_Close",
            "Volume",
        ]
    )


# ==============================================================================
# 13. NORMALIZE CACHE SCHEMA
# ==============================================================================

if (
    not B38_ALL_PRICES.empty
):

    required_cache_columns = [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj_Close",
        "Volume",
    ]


    missing_cache_columns = [
        x
        for x in required_cache_columns
        if x not in B38_ALL_PRICES.columns
    ]


    if missing_cache_columns:

        raise RuntimeError(
            "Historical Block38B cache has unexpected schema. "
            f"Missing={missing_cache_columns}"
        )


    B38_ALL_PRICES[
        "Date"
    ] = pd.to_datetime(
        B38_ALL_PRICES[
            "Date"
        ],
        errors="coerce",
    )


    if getattr(
        B38_ALL_PRICES[
            "Date"
        ].dt,
        "tz",
        None,
    ) is not None:

        B38_ALL_PRICES[
            "Date"
        ] = (
            B38_ALL_PRICES[
                "Date"
            ]
            .dt.tz_convert(
                "America/New_York"
            )
            .dt.tz_localize(None)
        )


    B38_ALL_PRICES[
        "Date"
    ] = (
        B38_ALL_PRICES[
            "Date"
        ]
        .dt.normalize()
    )


    B38_ALL_PRICES[
        "Ticker"
    ] = (
        B38_ALL_PRICES[
            "Ticker"
        ]
        .map(
            b38b_normalize_ticker
        )
    )


    for col in [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj_Close",
        "Volume",
    ]:

        B38_ALL_PRICES[
            col
        ] = pd.to_numeric(
            B38_ALL_PRICES[
                col
            ],
            errors="coerce",
        )


    B38_ALL_PRICES = (

        B38_ALL_PRICES

        .dropna(
            subset=[
                "Date",
                "Ticker",
                "Close",
                "Adj_Close",
            ]
        )

        .drop_duplicates(
            subset=[
                "Date",
                "Ticker",
            ],
            keep="last",
        )

        .sort_values(
            [
                "Ticker",
                "Date",
            ]
        )

        .reset_index(
            drop=True
        )
    )


# ==============================================================================
# 14. DETERMINE MISSING TICKERS
# ==============================================================================

already_downloaded = set(

    B38_ALL_PRICES[
        "Ticker"
    ]
    .dropna()
    .unique()
)


required_tickers = set(
    V4_BROAD_UNIVERSE_TICKERS
)


to_download = sorted(

    required_tickers
    -
    already_downloaded
)


print(
    "\n[15-DATA] Already cached:",
    f"{len(already_downloaded & required_tickers):,}"
)

print(
    "[15-DATA] Need download :",
    f"{len(to_download):,}"
)


# ==============================================================================
# 15. ORIGINAL PRIMARY BATCH DOWNLOAD
# ==============================================================================

if to_download:

    batches = [

        to_download[
            i:
            i
            +
            B38_BATCH_SIZE
        ]

        for i in range(
            0,
            len(
                to_download
            ),
            B38_BATCH_SIZE,
        )
    ]


    t0 = (
        time.time()
    )


    for batch_no, batch in enumerate(
        batches,
        start=1,
    ):

        print(
            f"[15-DATA] Batch "
            f"{batch_no:02d}/{len(batches):02d} "
            f"| {len(batch)} tickers"
        )


        parts = (
            b38b_download_batch(
                batch
            )
        )


        if parts:

            new_data = pd.concat(
                parts,
                ignore_index=True,
            )


            B38_ALL_PRICES = pd.concat(
                [
                    B38_ALL_PRICES,
                    new_data,
                ],
                ignore_index=True,
            )


            B38_ALL_PRICES = (

                B38_ALL_PRICES

                .drop_duplicates(
                    subset=[
                        "Date",
                        "Ticker",
                    ],
                    keep="last",
                )

                .sort_values(
                    [
                        "Ticker",
                        "Date",
                    ]
                )

                .reset_index(
                    drop=True
                )
            )


        # Historical checkpoint behavior.
        if (
            batch_no % 5 == 0
            or
            batch_no == len(
                batches
            )
        ):

            B38_ALL_PRICES.to_pickle(
                B38_CACHE_FILE
            )


        time.sleep(
            0.25
        )


    print(
        "\n[15-DATA] Primary download seconds:",
        round(
            time.time()
            -
            t0,
            1,
        )
    )


# ==============================================================================
# 16. ORIGINAL SMALL-BATCH RETRY
# ==============================================================================

downloaded_after_primary = set(

    B38_ALL_PRICES[
        "Ticker"
    ]
    .dropna()
    .unique()
)


missing_after_primary = sorted(

    required_tickers
    -
    downloaded_after_primary
)


print(
    "\n[15-DATA] Missing after primary:",
    f"{len(missing_after_primary):,}"
)


if missing_after_primary:

    retry_batches = [

        missing_after_primary[
            i:
            i
            +
            B38_RETRY_BATCH_SIZE
        ]

        for i in range(
            0,
            len(
                missing_after_primary
            ),
            B38_RETRY_BATCH_SIZE,
        )
    ]


    for batch_no, batch in enumerate(
        retry_batches,
        start=1,
    ):

        print(
            f"[15-RETRY] "
            f"{batch_no:02d}/{len(retry_batches):02d}"
        )


        parts = (
            b38b_download_batch(
                batch
            )
        )


        if parts:

            B38_ALL_PRICES = pd.concat(
                [
                    B38_ALL_PRICES,
                    *parts,
                ],
                ignore_index=True,
            )


        time.sleep(
            0.4
        )


    B38_ALL_PRICES = (

        B38_ALL_PRICES

        .drop_duplicates(
            subset=[
                "Date",
                "Ticker",
            ],
            keep="last",
        )

        .sort_values(
            [
                "Ticker",
                "Date",
            ]
        )

        .reset_index(
            drop=True
        )
    )


    # New pickle is now serialized by THIS environment,
    # removing the old NumPy compatibility issue permanently.
    B38_ALL_PRICES.to_pickle(
        B38_CACHE_FILE
    )


# ==============================================================================
# 17. FINAL RAW PRICE COVERAGE
# ==============================================================================

downloaded_tickers = set(

    B38_ALL_PRICES[
        "Ticker"
    ]
    .dropna()
    .unique()
)


B38_FINAL_MISSING_TICKERS = sorted(

    required_tickers
    -
    downloaded_tickers
)


B38_RAW_DOWNLOAD_COVERAGE = (

    len(
        required_tickers
        &
        downloaded_tickers
    )

    /

    len(
        required_tickers
    )
)


print(
    "\n[15-DATA] Requested :",
    f"{len(required_tickers):,}"
)

print(
    "[15-DATA] Available :",
    f"{len(required_tickers & downloaded_tickers):,}"
)

print(
    "[15-DATA] Raw coverage:",
    f"{100 * B38_RAW_DOWNLOAD_COVERAGE:.2f}%"
)

print(
    "[15-DATA] Missing     :",
    f"{len(B38_FINAL_MISSING_TICKERS):,}"
)


# ==============================================================================
# 18. PRICE / RETURN / LIQUIDITY FEATURES
# ==============================================================================

B38_ALL_PRICES = (

    B38_ALL_PRICES

    .sort_values(
        [
            "Ticker",
            "Date",
        ]
    )

    .reset_index(
        drop=True
    )
)


B38_ALL_PRICES[
    "Daily_Return"
] = (

    B38_ALL_PRICES

    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]

    .pct_change(
        fill_method=None
    )
)


B38_ALL_PRICES[
    "Dollar_Volume"
] = (

    B38_ALL_PRICES[
        "Close"
    ]

    *

    B38_ALL_PRICES[
        "Volume"
    ]
)


B38_ALL_PRICES[
    "Median_Dollar_Volume_60"
] = (

    B38_ALL_PRICES

    .groupby(
        "Ticker",
        sort=False,
    )[
        "Dollar_Volume"
    ]

    .transform(

        lambda x:

            x.rolling(
                window=(
                    B38_LIQUIDITY_LOOKBACK
                ),
                min_periods=(
                    B38_MIN_VALID_DAYS
                ),
            )
            .median()
    )
)


B38_ALL_PRICES[
    "Valid_Days_60"
] = (

    B38_ALL_PRICES

    .groupby(
        "Ticker",
        sort=False,
    )[
        "Adj_Close"
    ]

    .transform(

        lambda x:

            x.rolling(
                window=(
                    B38_LIQUIDITY_LOOKBACK
                ),
                min_periods=1,
            )
            .count()
    )
)


# ==============================================================================
# 19. MAP MARKET DATE -> STRICTLY PREVIOUS PIT SNAPSHOT
# ==============================================================================

B38_MARKET_DATES = (

    B38_ALL_PRICES.loc[

        B38_ALL_PRICES[
            "Date"
        ]
        >=
        B38_PIT_START_DATE,

        "Date",
    ]

    .drop_duplicates()

    .sort_values()

    .reset_index(
        drop=True
    )
)


snapshot_dates_np = (

    V4_PIT_STOCK_MEMBERSHIP[
        "Snapshot_AsOf"
    ]

    .drop_duplicates()

    .sort_values()

    .to_numpy(
        dtype="datetime64[ns]"
    )
)


market_dates_np = (

    B38_MARKET_DATES

    .to_numpy(
        dtype="datetime64[ns]"
    )
)


# CRITICAL historical causality:
# side="left" => snapshot must be STRICTLY earlier than trading date.

snapshot_idx = (

    np.searchsorted(
        snapshot_dates_np,
        market_dates_np,
        side="left",
    )

    -
    1
)


valid_mapping = (
    snapshot_idx
    >=
    0
)


B38_DATE_TO_SNAPSHOT = pd.DataFrame(
    {

        "Date":
            B38_MARKET_DATES[
                valid_mapping
            ]
            .to_numpy(),

        "Snapshot_AsOf":
            snapshot_dates_np[
                snapshot_idx[
                    valid_mapping
                ]
            ],
    }
)


if B38_DATE_TO_SNAPSHOT.empty:

    raise RuntimeError(
        "Could not map market dates to PIT snapshots."
    )


# ==============================================================================
# 20. STOCK PANEL — EXACT PIT MEMBERSHIP
# ==============================================================================

stock_price_rows = (

    B38_ALL_PRICES[

        (
            ~B38_ALL_PRICES[
                "Ticker"
            ]
            .isin(
                B38_ETF_SLEEVE
            )
        )

        &

        (
            B38_ALL_PRICES[
                "Date"
            ]
            >=
            B38_PIT_START_DATE
        )
    ]

    .copy()
)


stock_price_rows = (

    stock_price_rows

    .merge(
        B38_DATE_TO_SNAPSHOT,
        on="Date",
        how="inner",
        validate="many_to_one",
    )
)


B38_STOCK_PANEL = (

    stock_price_rows

    .merge(
        V4_PIT_STOCK_MEMBERSHIP,

        on=[
            "Snapshot_AsOf",
            "Ticker",
        ],

        how="inner",

        validate="many_to_one",
    )
)


B38_STOCK_PANEL[
    "Asset_Type"
] = "STOCK"


# ==============================================================================
# 21. ETF PANEL
# ==============================================================================

B38_ETF_PANEL = (

    B38_ALL_PRICES[

        (
            B38_ALL_PRICES[
                "Ticker"
            ]
            .isin(
                B38_ETF_SLEEVE
            )
        )

        &

        (
            B38_ALL_PRICES[
                "Date"
            ]
            >=
            B38_PIT_START_DATE
        )
    ]

    .copy()
)


B38_ETF_PANEL[
    "Snapshot_AsOf"
] = pd.NaT


B38_ETF_PANEL[
    "Asset_Type"
] = np.where(

    B38_ETF_PANEL[
        "Ticker"
    ]
    ==
    "TQQQ",

    "TACTICAL_LEVERAGED_ETF",

    "ETF",
)


# ==============================================================================
# 22. COMBINE STOCKS + ETF SLEEVE
# ==============================================================================

B38_COMMON_COLUMNS = [

    "Date",
    "Ticker",

    "Open",
    "High",
    "Low",
    "Close",
    "Adj_Close",
    "Volume",

    "Daily_Return",
    "Dollar_Volume",
    "Median_Dollar_Volume_60",
    "Valid_Days_60",

    "Snapshot_AsOf",
    "Asset_Type",
]


V4_DAILY_PANEL = (

    pd.concat(
        [
            B38_STOCK_PANEL[
                B38_COMMON_COLUMNS
            ],

            B38_ETF_PANEL[
                B38_COMMON_COLUMNS
            ],
        ],
        ignore_index=True,
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


if V4_DAILY_PANEL.empty:

    raise RuntimeError(
        "V4_DAILY_PANEL is empty after PIT membership join."
    )


# ==============================================================================
# 23. EXACT HISTORICAL CAUSAL ELIGIBILITY
# ==============================================================================

V4_DAILY_PANEL[
    "Price_OK"
] = (

    V4_DAILY_PANEL[
        "Close"
    ]
    >=
    B38_MIN_PRICE
)


V4_DAILY_PANEL[
    "Liquidity_OK"
] = (

    V4_DAILY_PANEL[
        "Median_Dollar_Volume_60"
    ]
    >=
    B38_MIN_MEDIAN_DOLLAR_VOLUME
)


V4_DAILY_PANEL[
    "History_OK"
] = (

    V4_DAILY_PANEL[
        "Valid_Days_60"
    ]
    >=
    B38_MIN_VALID_DAYS
)


V4_DAILY_PANEL[
    "Eligible"
] = (

    V4_DAILY_PANEL[
        "Price_OK"
    ]

    &

    V4_DAILY_PANEL[
        "Liquidity_OK"
    ]

    &

    V4_DAILY_PANEL[
        "History_OK"
    ]
)


# ==============================================================================
# 24. FINAL ELIGIBILITY PANEL
# ==============================================================================

V4_ELIGIBILITY_PANEL = (

    V4_DAILY_PANEL[
        [
            "Date",
            "Snapshot_AsOf",
            "Ticker",
            "Asset_Type",

            "Close",
            "Adj_Close",
            "Daily_Return",

            "Dollar_Volume",
            "Median_Dollar_Volume_60",
            "Valid_Days_60",

            "Price_OK",
            "Liquidity_OK",
            "History_OK",
            "Eligible",
        ]
    ]

    .copy()
)


# ==============================================================================
# 25. ELIGIBLE TICKERS BY DATE
# ==============================================================================

V4_ELIGIBLE_BY_DATE = {

    date:

        tuple(

            sorted(

                frame.loc[
                    frame[
                        "Eligible"
                    ],
                    "Ticker",
                ]
                .unique()
            )
        )

    for date, frame in (

        V4_ELIGIBILITY_PANEL

        .groupby(
            "Date",
            sort=True,
        )
    )
}


# ==============================================================================
# 26. DAILY UNIVERSE SIZE
# ==============================================================================

B38_DAILY_COUNTS = (

    V4_ELIGIBILITY_PANEL

    .groupby(
        "Date"
    )

    .agg(

        PIT_Available_Assets=(
            "Ticker",
            "nunique",
        ),

        Eligible_Assets=(
            "Eligible",
            "sum",
        ),
    )
)


# ==============================================================================
# 27. POINT-IN-TIME PRICE COVERAGE
# ==============================================================================

expected_stock_count = (

    V4_PIT_STOCK_MEMBERSHIP

    .groupby(
        "Snapshot_AsOf"
    )[
        "Ticker"
    ]

    .nunique()
)


observed_stock_count = (

    B38_STOCK_PANEL

    .groupby(
        "Date"
    )[
        "Ticker"
    ]

    .nunique()
)


B38_PIT_PRICE_COVERAGE = (
    B38_DATE_TO_SNAPSHOT
    .copy()
)


B38_PIT_PRICE_COVERAGE[
    "Expected_Stocks"
] = (

    B38_PIT_PRICE_COVERAGE[
        "Snapshot_AsOf"
    ]

    .map(
        expected_stock_count
    )
)


B38_PIT_PRICE_COVERAGE[
    "Observed_Stocks"
] = (

    B38_PIT_PRICE_COVERAGE[
        "Date"
    ]

    .map(
        observed_stock_count
    )

    .fillna(0)
)


B38_PIT_PRICE_COVERAGE[
    "Coverage_Pct"
] = (

    100.0

    *

    B38_PIT_PRICE_COVERAGE[
        "Observed_Stocks"
    ]

    /

    B38_PIT_PRICE_COVERAGE[
        "Expected_Stocks"
    ]
)


# ==============================================================================
# 28. COMPARISON-PERIOD AUDITS
# ==============================================================================

B38_V4_COUNTS = (

    B38_DAILY_COUNTS[

        B38_DAILY_COUNTS.index
        >=
        V4_COMPARISON_START
    ]
)


B38_V4_PRICE_COVERAGE = (

    B38_PIT_PRICE_COVERAGE[

        B38_PIT_PRICE_COVERAGE[
            "Date"
        ]
        >=
        V4_COMPARISON_START
    ]
)


if B38_V4_COUNTS.empty:

    raise RuntimeError(
        "No V4 universe observations overlap comparison period."
    )


if B38_V4_PRICE_COVERAGE.empty:

    raise RuntimeError(
        "No PIT coverage observations overlap comparison period."
    )


# ==============================================================================
# 29. TQQQ AUDIT
# ==============================================================================

B38_TQQQ_PANEL = (

    V4_DAILY_PANEL[

        V4_DAILY_PANEL[
            "Ticker"
        ]
        ==
        "TQQQ"
    ]

    .copy()
)


B38_TQQQ_COMPARISON = (

    B38_TQQQ_PANEL[

        B38_TQQQ_PANEL[
            "Date"
        ]
        >=
        V4_COMPARISON_START
    ]
)


B38_TQQQ_ELIGIBLE_DAYS = int(

    B38_TQQQ_COMPARISON[
        "Eligible"
    ]
    .sum()
)


# ==============================================================================
# 30. CORE AUDIT NUMBERS
# ==============================================================================

B38_UNIQUE_HISTORICAL_STOCKS = int(

    V4_PIT_STOCK_MEMBERSHIP[
        "Ticker"
    ]
    .nunique()
)


B38_UNIQUE_RISKY_CANDIDATES = int(

    len(
        V4_BROAD_UNIVERSE_TICKERS
    )
)


B38_MEDIAN_PIT_PRICE_COVERAGE = float(

    B38_V4_PRICE_COVERAGE[
        "Coverage_Pct"
    ]
    .median()
)


B38_MEDIAN_ELIGIBLE = float(

    B38_V4_COUNTS[
        "Eligible_Assets"
    ]
    .median()
)


B38_MIN_ELIGIBLE = int(

    B38_V4_COUNTS[
        "Eligible_Assets"
    ]
    .min()
)


B38_MAX_ELIGIBLE = int(

    B38_V4_COUNTS[
        "Eligible_Assets"
    ]
    .max()
)


B38_LATEST_ELIGIBLE = int(

    B38_V4_COUNTS[
        "Eligible_Assets"
    ]
    .iloc[-1]
)


# ==============================================================================
# 31. HARD HISTORICAL RESEARCH GATES
# ==============================================================================

if (
    "TQQQ"
    not in
    V4_BROAD_UNIVERSE_TICKERS
):

    raise RuntimeError(
        "TQQQ missing from V4 universe."
    )


if B38_TQQQ_COMPARISON.empty:

    raise RuntimeError(
        "TQQQ comparison-period price history missing."
    )


# Genuinely broad universe.

if B38_MEDIAN_ELIGIBLE < 500:

    raise RuntimeError(
        "Broad-universe gate failed: "
        f"median eligible assets="
        f"{B38_MEDIAN_ELIGIBLE:.0f}"
    )


# Data-integrity gate only.

if (
    B38_MEDIAN_PIT_PRICE_COVERAGE
    <
    90.0
):

    raise RuntimeError(
        "PIT price coverage is insufficient "
        "for clean research: "
        f"median="
        f"{B38_MEDIAN_PIT_PRICE_COVERAGE:.2f}%"
    )


# ==============================================================================
# 32. MASTER AUDIT
# ==============================================================================

V4_BLOCK38_DATA_AUDIT = pd.DataFrame(
    {

        "Metric": [

            "PIT start",

            "Comparison start",

            "Research end",

            "PIT snapshots",

            "Unique historical stocks",

            "ETF sleeve assets",

            "Unique risky candidates",

            "Raw Yahoo downloaded tickers",

            "Raw Yahoo ticker coverage pct",

            "Median comparison PIT price coverage pct",

            "Median eligible assets",

            "Minimum eligible assets",

            "Maximum eligible assets",

            "Latest eligible assets",

            "TQQQ comparison rows",

            "TQQQ eligible days",

            "Cache load mode",
        ],


        "Value": [

            B38_PIT_START_DATE,

            V4_COMPARISON_START,

            V4_DATA_END_DATE,

            len(
                B38_SNAPSHOT_COUNTS
            ),

            B38_UNIQUE_HISTORICAL_STOCKS,

            len(
                B38_ETF_SLEEVE
            ),

            B38_UNIQUE_RISKY_CANDIDATES,

            len(
                downloaded_tickers
            ),

            100.0
            *
            B38_RAW_DOWNLOAD_COVERAGE,

            B38_MEDIAN_PIT_PRICE_COVERAGE,

            B38_MEDIAN_ELIGIBLE,

            B38_MIN_ELIGIBLE,

            B38_MAX_ELIGIBLE,

            B38_LATEST_ELIGIBLE,

            len(
                B38_TQQQ_COMPARISON
            ),

            B38_TQQQ_ELIGIBLE_DAYS,

            M15_CACHE_MODE,
        ],
    }
)


# ==============================================================================
# 33. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 118
)

print(
    "MODULE 15 / BLOCK 38B — RESULTS"
)

print(
    "=" * 118
)


print(
    "\n1) MASTER AUDIT"
)


display(
    V4_BLOCK38_DATA_AUDIT
)


print(
    "\n2) ELIGIBLE UNIVERSE SIZE — V4 PERIOD"
)


display(

    B38_V4_COUNTS[
        "Eligible_Assets"
    ]

    .describe(
        percentiles=[
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
        ]
    )

    .to_frame(
        "Eligible_Assets"
    )
)


print(
    "\n3) PIT PRICE COVERAGE — V4 PERIOD"
)


display(

    B38_V4_PRICE_COVERAGE[
        "Coverage_Pct"
    ]

    .describe(
        percentiles=[
            0.05,
            0.50,
            0.95,
        ]
    )

    .to_frame(
        "Coverage_Pct"
    )
)


print(
    "\n4) LATEST 10 TRADING DAYS"
)


display(
    B38_V4_COUNTS.tail(
        10
    )
)


# ==============================================================================
# 34. LATEST ETF STATUS
# ==============================================================================

latest_date = (

    V4_DAILY_PANEL[
        "Date"
    ]
    .max()
)


print(
    f"\n5) ETF STATUS @ "
    f"{latest_date.date()}"
)


display(

    V4_DAILY_PANEL[

        (
            V4_DAILY_PANEL[
                "Date"
            ]
            ==
            latest_date
        )

        &

        (
            V4_DAILY_PANEL[
                "Asset_Type"
            ]
            !=
            "STOCK"
        )
    ]

    [
        [
            "Ticker",
            "Asset_Type",
            "Close",
            "Median_Dollar_Volume_60",
            "Eligible",
        ]
    ]

    .sort_values(
        "Ticker"
    )
)


# ==============================================================================
# 35. FINAL INTEGRITY
# ==============================================================================

latest_eligible = (

    V4_DAILY_PANEL[

        (
            V4_DAILY_PANEL[
                "Date"
            ]
            ==
            latest_date
        )

        &

        (
            V4_DAILY_PANEL[
                "Eligible"
            ]
        )
    ]
)


print(
    "\n"
    +
    "=" * 118
)

print(
    "MODULE 15 / BLOCK 38B — FINAL STATUS"
)

print(
    "=" * 118
)


print(
    f"\nHistorical PIT stocks       : "
    f"{B38_UNIQUE_HISTORICAL_STOCKS:,}"
)

print(
    f"Total risky candidates      : "
    f"{B38_UNIQUE_RISKY_CANDIDATES:,}"
)

print(
    f"Median PIT price coverage   : "
    f"{B38_MEDIAN_PIT_PRICE_COVERAGE:.2f}%"
)

print(
    f"Median eligible assets      : "
    f"{B38_MEDIAN_ELIGIBLE:,.0f}"
)

print(
    f"Latest eligible assets      : "
    f"{len(latest_eligible):,}"
)

print(
    f"TQQQ eligible days          : "
    f"{B38_TQQQ_ELIGIBLE_DAYS:,}"
)

print(
    f"TQQQ eligible latest date   : "
    f"{'TQQQ' in set(latest_eligible['Ticker'])}"
)

print(
    f"Daily panel rows            : "
    f"{len(V4_DAILY_PANEL):,}"
)

print(
    f"Daily-price cache mode      : "
    f"{M15_CACHE_MODE}"
)


print(
    "\n[+] MODULE 15 PASSED."
)

print(
    "[+] HISTORICAL BLOCK 38B CAUSAL PIT UNIVERSE RESTORED."
)

print(
    "[+] NO MODEL / UNIVERSE / ELIGIBILITY PARAMETER WAS CHANGED."
)

print(
    "[+] NEXT: MODULE 16 — EXACT HISTORICAL BLOCK 39."
)
