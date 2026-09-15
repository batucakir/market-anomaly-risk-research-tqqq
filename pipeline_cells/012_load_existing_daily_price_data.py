# ==============================================================================
# LOAD EXISTING DAILY PRICE DATA
# ==============================================================================

import pickle


class M13NumpyCompatUnpickler(pickle.Unpickler):

    def find_class(self, module, name):

        # NumPy 2.x pickle path -> NumPy 1.x path
        if module == "numpy._core":
            module = "numpy.core"

        elif module.startswith("numpy._core."):
            module = (
                "numpy.core."
                + module[len("numpy._core."):]
            )

        return super().find_class(
            module,
            name,
        )


def m13_read_pickle_compat(path):

    path = Path(path)

    try:

        return pd.read_pickle(
            path
        )

    except ModuleNotFoundError as exc:

        if "numpy._core" not in str(exc):
            raise

        print(
            "[13-DATA] NumPy pickle compatibility mode."
        )

        with open(
            path,
            "rb",
        ) as handle:

            obj = (
                M13NumpyCompatUnpickler(
                    handle
                )
                .load()
            )

        return obj


def m13_load_raw_prices():

    if (
        "B38_ALL_PRICES" in globals()
        and isinstance(
            B38_ALL_PRICES,
            pd.DataFrame,
        )
        and not B38_ALL_PRICES.empty
    ):

        print(
            "[13-DATA] Using B38_ALL_PRICES already in memory."
        )

        return (
            B38_ALL_PRICES
            .copy()
        )

    cache_dir = Path(
        "./v4_cache"
    )

    candidates = []

    if cache_dir.exists():

        candidates.extend(
            cache_dir.glob(
                "block38b_daily_prices_*.pkl"
            )
        )

        candidates.extend(
            cache_dir.glob(
                "*daily_prices*.pkl"
            )
        )

    candidates = list(
        dict.fromkeys(
            candidates
        )
    )

    if not candidates:

        raise RuntimeError(
            "MODULE 13 could not find broad daily-price data. "
            "Neither B38_ALL_PRICES nor a v4_cache daily-price file exists."
        )

    cache_file = max(
        candidates,
        key=lambda p:
            p.stat().st_mtime,
    )

    print(
        f"[13-DATA] Loading daily-price cache: "
        f"{cache_file}"
    )

    data = (
        m13_read_pickle_compat(
            cache_file
        )
    )

    if not isinstance(
        data,
        pd.DataFrame,
    ):

        raise RuntimeError(
            "MODULE 13 daily-price cache did not contain a DataFrame."
        )

    if data.empty:

        raise RuntimeError(
            "MODULE 13 daily-price cache is empty."
        )

    print(
        f"[13-DATA] Loaded "
        f"{len(data):,} daily rows."
    )

    return data


M13_RAW_PRICES = (
    m13_load_raw_prices()
)
