# MODULE 46 — V16 EXACT TARGET RECOVERY AND DEEP DIVE
# Run in the same notebook, in module order.

# ==============================================================================
# V16-RD1 — EXACT HISTORICAL TARGET-STATE RECOVERY
# ==============================================================================
#
# RETROACTIVE CHANGE — ANALYSIS INFRASTRUCTURE ONLY
#
# PURPOSE:
# Recover the exact historical V16 event-level portfolio targets that were
# actually used by the frozen V16 research engine.
#
# NO STRATEGY CHANGE.
# NO SIGNAL RECOMPUTATION.
# NO MODEL FITTING.
# NO PARAMETER CHANGE.
# NO LAMBDA RETUNING.
#
# Exact identity used by original V16:
#
#   V16_target_t
#       = V8_base_target_t
#       + pre_event_lambda_t
#         * (full_residual_tilt_target_t - V8_base_target_t)
#
# The original V16 research cell stored:
#   BASE_TARGETS
#   TILT_TARGETS
#   V8_ASSETS
#   V16_PATH["Pre_Lambda"]
#
# This block only gives that already-frozen state a canonical V16-prefixed name.
# ==============================================================================

import numpy as np
import pandas as pd
import hashlib


print("=" * 120)
print("V16-RD1 — EXACT HISTORICAL TARGET-STATE RECOVERY")
print("=" * 120)


# ==============================================================================
# 1. REQUIRED ORIGINAL V16 STATE
# ==============================================================================

required_objects = [
    "V16_PATH",
    "BASE_TARGETS",
    "TILT_TARGETS",
    "V8_ASSETS",
]

missing_objects = [
    name
    for name in required_objects
    if name not in globals()
]

if missing_objects:

    raise RuntimeError(
        "Exact V16 target recovery cannot proceed. "
        f"Missing original V16 objects: {missing_objects}"
    )


# ==============================================================================
# 2. CLEAN ORIGINAL V16 EVENT PATH
# ==============================================================================

P = V16_PATH.copy()


required_columns = [
    "Execution_Date",
    "Exit_Date",
    "Pre_Lambda",
]

missing_columns = [
    c
    for c in required_columns
    if c not in P.columns
]

if missing_columns:

    raise RuntimeError(
        f"V16_PATH is missing required columns: {missing_columns}"
    )


P["Execution_Date"] = (
    pd.to_datetime(
        P["Execution_Date"],
        errors="raise",
    )
    .dt.normalize()
)

P["Exit_Date"] = (
    pd.to_datetime(
        P["Exit_Date"],
        errors="raise",
    )
    .dt.normalize()
)

P["Pre_Lambda"] = (
    pd.to_numeric(
        P["Pre_Lambda"],
        errors="raise",
    )
)


P = (
    P
    .sort_values("Execution_Date")
    .reset_index(drop=True)
)


N_EVENTS = len(P)


if N_EVENTS != 33:

    raise RuntimeError(
        f"Expected 33 completed V16 holding periods, found {N_EVENTS}."
    )


print(
    f"\n[+] Completed V16 holding periods : {N_EVENTS}"
)


# ==============================================================================
# 3. LOAD THE EXACT PRE-PERFORMANCE TARGET ARRAYS
# ==============================================================================

BASE = np.asarray(
    BASE_TARGETS,
    dtype=float,
)

TILT = np.asarray(
    TILT_TARGETS,
    dtype=float,
)

ASSETS = [
    str(x).upper().strip()
    for x in list(V8_ASSETS)
]


if BASE.ndim != 2:

    raise RuntimeError(
        f"BASE_TARGETS must be 2D. Shape = {BASE.shape}"
    )


if TILT.ndim != 2:

    raise RuntimeError(
        f"TILT_TARGETS must be 2D. Shape = {TILT.shape}"
    )


if BASE.shape != TILT.shape:

    raise RuntimeError(
        "BASE_TARGETS and TILT_TARGETS shapes differ: "
        f"{BASE.shape} vs {TILT.shape}"
    )


if BASE.shape[1] != len(ASSETS):

    raise RuntimeError(
        "Asset dimension mismatch: "
        f"{BASE.shape[1]} target columns vs "
        f"{len(ASSETS)} V8_ASSETS."
    )


if BASE.shape[0] < N_EVENTS:

    raise RuntimeError(
        "Not enough target rows for the completed V16 history: "
        f"{BASE.shape[0]} < {N_EVENTS}"
    )


if "TQQQ" not in ASSETS:

    raise RuntimeError(
        "TQQQ is missing from the original V16 asset list."
    )


print(
    f"[+] Original target-array shape    : {BASE.shape}"
)

print(
    f"[+] Original asset count           : {len(ASSETS):,}"
)


# ==============================================================================
# 4. STRONG PRE-PERFORMANCE HASH AUDIT
# ==============================================================================

RECOVERED_PREPERFORMANCE_HASH = hashlib.sha256(
    np.round(
        np.concatenate(
            [
                BASE.ravel(),
                TILT.ravel(),
            ]
        ),
        14,
    ).tobytes()
).hexdigest()


print(
    "\n[+] Recovered pre-performance hash :",
    RECOVERED_PREPERFORMANCE_HASH,
)


if "V16_PREPERFORMANCE_HASH" in globals():

    print(
        "[+] Stored V16 pre-performance hash:",
        V16_PREPERFORMANCE_HASH,
    )

    if (
        RECOVERED_PREPERFORMANCE_HASH
        !=
        V16_PREPERFORMANCE_HASH
    ):

        raise RuntimeError(
            "STOP: BASE_TARGETS / TILT_TARGETS no longer match "
            "the original V16 pre-performance state."
        )

    print(
        "[+] PRE-PERFORMANCE HASH MATCH PASSED."
    )

else:

    print(
        "[i] V16_PREPERFORMANCE_HASH is not currently in RAM."
    )

    print(
        "[i] Structural/date/weight integrity checks will be used instead."
    )


# ==============================================================================
# 5. DATE-ALIGNMENT AUDIT
# ==============================================================================

V16_EXECUTION_DATES = pd.DatetimeIndex(
    P["Execution_Date"]
)


if "TARGET_EXEC_DATES" in globals():

    original_target_dates = pd.DatetimeIndex(
        pd.to_datetime(
            list(TARGET_EXEC_DATES),
            errors="raise",
        )
    ).normalize()

    if len(original_target_dates) < N_EVENTS:

        raise RuntimeError(
            "TARGET_EXEC_DATES is shorter than the V16 completed history."
        )

    original_completed_dates = (
        original_target_dates[
            :N_EVENTS
        ]
    )

    if not np.array_equal(
        original_completed_dates.values,
        V16_EXECUTION_DATES.values,
    ):

        audit = pd.DataFrame(
            {
                "V16_PATH_Execution_Date":
                    V16_EXECUTION_DATES,

                "Original_Target_Date":
                    original_completed_dates,
            }
        )

        display(audit)

        raise RuntimeError(
            "STOP: Original V16 target-row dates do not align "
            "with V16_PATH execution dates."
        )

    print(
        "\n[+] TARGET_EXEC_DATES alignment     : PASS"
    )

else:

    print(
        "\n[i] TARGET_EXEC_DATES not in RAM."
    )

    print(
        "[i] Original array row order will be validated "
        "against V16_PATH portfolio weights."
    )


# ==============================================================================
# 6. RECONSTRUCT EXACT ACTUAL V16 EVENT TARGETS
# ==============================================================================

LAMBDAS = (
    P["Pre_Lambda"]
    .to_numpy(dtype=float)
)


if (
    np.any(~np.isfinite(LAMBDAS))
    or
    np.any(LAMBDAS < -1e-12)
    or
    np.any(LAMBDAS > 1.0 + 1e-12)
):

    raise RuntimeError(
        "Invalid historical V16 Pre_Lambda values detected."
    )


BASE_COMPLETED = (
    BASE[
        :N_EVENTS
    ]
    .copy()
)

TILT_COMPLETED = (
    TILT[
        :N_EVENTS
    ]
    .copy()
)


V16_RECOVERED_TARGET_ARRAY = (
    BASE_COMPLETED
    +
    LAMBDAS[:, None]
    *
    (
        TILT_COMPLETED
        -
        BASE_COMPLETED
    )
)


if not np.isfinite(
    V16_RECOVERED_TARGET_ARRAY
).all():

    raise RuntimeError(
        "Recovered V16 target array contains non-finite values."
    )


minimum_weight = float(
    V16_RECOVERED_TARGET_ARRAY.min()
)


if minimum_weight < -1e-10:

    raise RuntimeError(
        "Recovered V16 targets contain economically negative weights: "
        f"minimum = {minimum_weight:.12f}"
    )


row_sums = (
    V16_RECOVERED_TARGET_ARRAY
    .sum(axis=1)
)


max_row_sum_error = float(
    np.max(
        np.abs(
            row_sums
            -
            1.0
        )
    )
)


if max_row_sum_error > 1e-9:

    raise RuntimeError(
        "Recovered V16 target rows do not sum to 1. "
        f"Maximum error = {max_row_sum_error:.12e}"
    )


print(
    f"\n[+] Maximum target row-sum error   : "
    f"{max_row_sum_error:.12e}"
)


# ==============================================================================
# 7. CANONICAL HISTORICAL V16 TARGET MATRIX
# ==============================================================================

V16_TARGET_MATRIX = pd.DataFrame(
    V16_RECOVERED_TARGET_ARRAY,
    index=
        V16_EXECUTION_DATES,
    columns=
        ASSETS,
)


V16_TARGET_MATRIX.index.name = (
    "Execution_Date"
)


# Also preserve the two frozen ingredients with explicit V16 names.

V16_BASE_TARGET_MATRIX = pd.DataFrame(
    BASE_COMPLETED,
    index=
        V16_EXECUTION_DATES,
    columns=
        ASSETS,
)

V16_BASE_TARGET_MATRIX.index.name = (
    "Execution_Date"
)


V16_FULL_RESIDUAL_TILT_TARGET_MATRIX = pd.DataFrame(
    TILT_COMPLETED,
    index=
        V16_EXECUTION_DATES,
    columns=
        ASSETS,
)

V16_FULL_RESIDUAL_TILT_TARGET_MATRIX.index.name = (
    "Execution_Date"
)


# ==============================================================================
# 8. TQQQ-MASS IDENTITY AUDIT
# ==============================================================================

tqqq_idx = ASSETS.index(
    "TQQQ"
)


recovered_tqqq_pct = (
    100.0
    *
    V16_RECOVERED_TARGET_ARRAY[
        :,
        tqqq_idx
    ]
)


if "V8_TQQQ_Weight_Pct" in P.columns:

    recorded_tqqq_pct = (
        pd.to_numeric(
            P[
                "V8_TQQQ_Weight_Pct"
            ],
            errors="raise",
        )
        .to_numpy(dtype=float)
    )


    tqqq_error = (
        recovered_tqqq_pct
        -
        recorded_tqqq_pct
    )


    max_tqqq_error = float(
        np.max(
            np.abs(
                tqqq_error
            )
        )
    )


    print(
        f"[+] Maximum TQQQ-weight identity error: "
        f"{max_tqqq_error:.12e} pp"
    )


    if max_tqqq_error > 1e-8:

        raise RuntimeError(
            "STOP: Recovered V16 targets do not reproduce "
            "the TQQQ weights recorded in V16_PATH."
        )


if "V8_Alpha_Weight_Pct" in P.columns:

    recovered_alpha_pct = (
        100.0
        -
        recovered_tqqq_pct
    )


    recorded_alpha_pct = (
        pd.to_numeric(
            P[
                "V8_Alpha_Weight_Pct"
            ],
            errors="raise",
        )
        .to_numpy(dtype=float)
    )


    alpha_error = (
        recovered_alpha_pct
        -
        recorded_alpha_pct
    )


    max_alpha_error = float(
        np.max(
            np.abs(
                alpha_error
            )
        )
    )


    print(
        f"[+] Maximum alpha-mass identity error : "
        f"{max_alpha_error:.12e} pp"
    )


    if max_alpha_error > 1e-8:

        raise RuntimeError(
            "STOP: Recovered V16 targets do not reproduce "
            "the alpha-sleeve weights recorded in V16_PATH."
        )


# ==============================================================================
# 9. TARGET-STATE HASH
# ==============================================================================

V16_HISTORICAL_TARGET_HASH = hashlib.sha256(
    np.round(
        V16_RECOVERED_TARGET_ARRAY,
        14,
    ).tobytes()
).hexdigest()


print(
    "\n[+] V16 historical target hash      :",
    V16_HISTORICAL_TARGET_HASH,
)


# ==============================================================================
# 10. RECOVERY AUDIT TABLE
# ==============================================================================

V16_TARGET_RECOVERY_AUDIT = pd.DataFrame(
    {
        "Execution_Date":
            V16_EXECUTION_DATES,

        "Pre_Lambda":
            LAMBDAS,

        "TQQQ_Weight_Pct":
            recovered_tqqq_pct,

        "Alpha_Weight_Pct":
            100.0
            -
            recovered_tqqq_pct,

        "Target_Row_Sum":
            row_sums,

        "Positive_Positions":
            (
                V16_RECOVERED_TARGET_ARRAY
                >
                1e-12
            )
            .sum(axis=1),

        "Max_Name_Weight_Pct":
            100.0
            *
            V16_RECOVERED_TARGET_ARRAY
            .max(axis=1),

        "Effective_N":
            1.0
            /
            np.sum(
                V16_RECOVERED_TARGET_ARRAY
                ** 2,
                axis=1,
            ),
    }
)


print(
    "\n1) V16 HISTORICAL TARGET RECOVERY AUDIT"
)

display(
    V16_TARGET_RECOVERY_AUDIT.round(
        8
    )
)


# ==============================================================================
# 11. FINAL HARD CHECKS
# ==============================================================================

if len(V16_TARGET_MATRIX) != 33:

    raise RuntimeError(
        "Recovered V16 target matrix does not contain 33 completed events."
    )


if not np.array_equal(
    V16_TARGET_MATRIX.index.values,
    V16_EXECUTION_DATES.values,
):

    raise RuntimeError(
        "Recovered V16 target matrix date index is incorrect."
    )


if "TQQQ" not in V16_TARGET_MATRIX.columns:

    raise RuntimeError(
        "Recovered V16 target matrix has no TQQQ column."
    )


print(
    "\n"
    +
    "=" * 120
)

print(
    "V16 HISTORICAL TARGET RECOVERY PASSED"
)

print(
    "=" * 120
)

print(
    f"[+] Events recovered       : {len(V16_TARGET_MATRIX)}"
)

print(
    f"[+] Assets                 : {V16_TARGET_MATRIX.shape[1]:,}"
)

print(
    f"[+] Research start         : "
    f"{V16_TARGET_MATRIX.index.min().date()}"
)

print(
    f"[+] Last holding execution : "
    f"{V16_TARGET_MATRIX.index.max().date()}"
)

print(
    "[+] Frozen V16 strategy was NOT changed."
)

print(
    "[+] No performance was used to reconstruct these weights."
)

print(
    "[+] No residual signal was recomputed."
)

print(
    "[+] No lambda was retuned."
)

print(
    "[+] V16_TARGET_MATRIX is now available for the deep-dive dashboard."
)

print("=" * 120)
# ==============================================================================
# V16 — FROZEN RESEARCH CHAMPION QUANT DEEP-DIVE DASHBOARD
#
# EXACT DAILY NAV / V8 + TQQQ + QQQ + SPY
# 1M / 3M / 6M / 12M
# RISK / DRAWDOWN / ATTRIBUTION / CONCENTRATION / TURNOVER
# RESIDUAL-MOMENTUM LAMBDA / V16-vs-V8 DECOMPOSITION
#
# DIAGNOSTIC / VISUALIZATION ONLY
#
# IMPORTANT:
#   - V16 ARCHITECTURE IS FROZEN.
#   - NO MODEL CHANGE.
#   - NO PARAMETER CHANGE.
#   - NO LAMBDA RETUNING.
#   - NO STOCK-SELECTION CHANGE.
#   - NO PERFORMANCE-DERIVED TRADING RULE.
# ==============================================================================

import re
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display


# ==============================================================================
# 0. HEADER / REQUIRED CORE STATE
# ==============================================================================

print("=" * 140)
print("V16 — FROZEN RESEARCH CHAMPION QUANT DEEP-DIVE DASHBOARD")
print("RESIDUAL-MOMENTUM TILT ON FROZEN V8")
print("=" * 140)

if "V16_PATH" not in globals():
    raise RuntimeError(
        "V16_PATH is missing. Run the frozen V16 research/freeze cells first."
    )

if "V16_FINAL_WEALTH" not in globals():
    raise RuntimeError(
        "V16_FINAL_WEALTH is missing. Run the frozen V16 research/freeze cells first."
    )

print("\nANALYSIS ONLY — FROZEN V16 STRATEGY IS NOT CHANGED.")

if "V16_MASTER_FREEZE_FINGERPRINT" in globals():
    print(
        "V16 master freeze fingerprint:",
        V16_MASTER_FREEZE_FINGERPRINT
    )
elif "V16_RESEARCH_FINGERPRINT" in globals():
    print(
        "V16 research fingerprint:",
        V16_RESEARCH_FINGERPRINT
    )


# ==============================================================================
# 1. GENERIC HELPERS
# ==============================================================================

def v16q_normalize_date_index(index):

    idx = pd.DatetimeIndex(
        pd.to_datetime(
            index,
            errors="coerce"
        )
    )

    if idx.tz is not None:

        idx = (
            idx
            .tz_convert("America/New_York")
            .tz_localize(None)
        )

    return idx.normalize()


def v16q_normalize_date_series(series):

    s = pd.to_datetime(
        series,
        errors="coerce"
    )

    try:

        if s.dt.tz is not None:
            s = (
                s
                .dt.tz_convert("America/New_York")
                .dt.tz_localize(None)
            )

    except Exception:
        pass

    return s.dt.normalize()


def v16q_first_existing(columns, candidates):

    lower_map = {
        str(c).lower(): c
        for c in columns
    }

    for candidate in candidates:

        if candidate in columns:
            return candidate

        key = str(candidate).lower()

        if key in lower_map:
            return lower_map[key]

    return None


def v16q_is_ticker_name(x):

    s = str(x).strip()

    if not s:
        return False

    if len(s) > 12:
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z][A-Za-z0-9\.\-\^]{0,11}",
            s
        )
    )


def v16q_return_to_fraction(value, column_name=""):

    if pd.isna(value):
        return np.nan

    value = float(value)

    name = str(column_name).lower()

    if (
        "pct" in name
        or "percent" in name
    ):
        return value / 100.0

    if abs(value) > 2.0:
        return value / 100.0

    return value


def v16q_safe_numeric(x):

    return pd.to_numeric(
        x,
        errors="coerce"
    )


def v16q_show(title, obj, decimals=4):

    print("\n" + "=" * 140)
    print(title)
    print("=" * 140)

    if isinstance(obj, (pd.DataFrame, pd.Series)):
        display(
            obj.round(decimals)
        )
    else:
        print(obj)


# ==============================================================================
# 2. CLEAN V16 PATH
# ==============================================================================

V16Q_PATH_RAW = (
    V16_PATH
    .copy()
)

exec_col = v16q_first_existing(
    V16Q_PATH_RAW.columns,
    [
        "Execution_Date",
        "ExecutionDate",
        "Date",
    ]
)

exit_col = v16q_first_existing(
    V16Q_PATH_RAW.columns,
    [
        "Exit_Date",
        "ExitDate",
        "Next_Execution_Date",
    ]
)

signal_col = v16q_first_existing(
    V16Q_PATH_RAW.columns,
    [
        "Signal_Date",
        "SignalDate",
    ]
)

if exec_col is None:
    raise RuntimeError(
        "Could not identify V16 execution-date column."
    )

if exit_col is None:
    raise RuntimeError(
        "Could not identify V16 exit-date column."
    )

V16Q_PATH_RAW[exec_col] = (
    v16q_normalize_date_series(
        V16Q_PATH_RAW[exec_col]
    )
)

V16Q_PATH_RAW[exit_col] = (
    v16q_normalize_date_series(
        V16Q_PATH_RAW[exit_col]
    )
)

if signal_col is not None:

    V16Q_PATH_RAW[signal_col] = (
        v16q_normalize_date_series(
            V16Q_PATH_RAW[signal_col]
        )
    )

V16Q_PATH_RAW = (
    V16Q_PATH_RAW
    .sort_values(
        [exec_col, exit_col]
    )
    .reset_index(
        drop=True
    )
)

event_type_col = v16q_first_existing(
    V16Q_PATH_RAW.columns,
    [
        "Event_Type",
        "Type",
    ]
)

if event_type_col is not None:

    holding_mask = (
        V16Q_PATH_RAW[event_type_col]
        .astype(str)
        .str.upper()
        .str.contains("HOLD")
    )

    if not holding_mask.any():

        holding_mask = (
            V16Q_PATH_RAW[exit_col]
            >
            V16Q_PATH_RAW[exec_col]
        )

else:

    holding_mask = (
        V16Q_PATH_RAW[exit_col]
        >
        V16Q_PATH_RAW[exec_col]
    )

V16Q_PATH = (
    V16Q_PATH_RAW
    .loc[
        holding_mask
    ]
    .copy()
    .reset_index(
        drop=True
    )
)

V16Q_TERMINAL_ROWS = (
    V16Q_PATH_RAW
    .loc[
        ~holding_mask
    ]
    .copy()
)

V16Q_START = pd.Timestamp(
    V16Q_PATH[exec_col].min()
)

V16Q_RESEARCH_END = pd.Timestamp(
    V16Q_PATH[exit_col].max()
)

V16Q_EXEC_DATES = pd.DatetimeIndex(
    V16Q_PATH[exec_col]
)

print(
    f"\n[+] Completed V16 holding periods : {len(V16Q_PATH):,}"
)

print(
    f"[+] Research start               : {V16Q_START.date()}"
)

print(
    f"[+] Research end                 : {V16Q_RESEARCH_END.date()}"
)


# ==============================================================================
# 3. FIND / STANDARDIZE FULL DAILY PRICE LEDGER
# ==============================================================================

def v16q_price_long_from_object(obj):

    if not isinstance(
        obj,
        pd.DataFrame
    ):
        return None

    df = obj.copy()

    # --------------------------------------------------------------------------
    # MultiIndex columns: try extracting a price field.
    # --------------------------------------------------------------------------

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        field_names = [
            "Adj_Close",
            "Adj Close",
            "AdjClose",
            "Close",
        ]

        for level in range(
            df.columns.nlevels
        ):

            vals = [
                str(x)
                for x in df.columns.get_level_values(level)
            ]

            for field in field_names:

                matches = [
                    x
                    for x in set(vals)
                    if x.lower() == field.lower()
                ]

                if matches:

                    try:

                        sub = df.xs(
                            matches[0],
                            axis=1,
                            level=level
                        )

                        temp = (
                            sub
                            .copy()
                        )

                        temp.index = (
                            v16q_normalize_date_index(
                                temp.index
                            )
                        )

                        temp = (
                            temp
                            .groupby(
                                level=0
                            )
                            .last()
                            .sort_index()
                        )

                        long = (
                            temp
                            .stack(
                                dropna=False
                            )
                            .rename(
                                "Price"
                            )
                            .reset_index()
                        )

                        long.columns = [
                            "Date",
                            "Ticker",
                            "Price",
                        ]

                        return long

                    except Exception:
                        pass

    # --------------------------------------------------------------------------
    # MultiIndex index.
    # --------------------------------------------------------------------------

    if isinstance(
        df.index,
        pd.MultiIndex
    ):

        try:
            df = df.reset_index()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Long format.
    # --------------------------------------------------------------------------

    date_c = v16q_first_existing(
        df.columns,
        [
            "Date",
            "Trading_Date",
            "TradingDate",
            "Timestamp",
        ]
    )

    ticker_c = v16q_first_existing(
        df.columns,
        [
            "Ticker",
            "Symbol",
            "Asset",
        ]
    )

    price_c = v16q_first_existing(
        df.columns,
        [
            "Adj_Close",
            "Adj Close",
            "AdjClose",
            "Adjusted_Close",
            "Close",
        ]
    )

    if (
        date_c is not None
        and ticker_c is not None
        and price_c is not None
    ):

        out = df[
            [
                date_c,
                ticker_c,
                price_c,
            ]
        ].copy()

        out.columns = [
            "Date",
            "Ticker",
            "Price",
        ]

        out["Date"] = (
            v16q_normalize_date_series(
                out["Date"]
            )
        )

        out["Ticker"] = (
            out["Ticker"]
            .astype(str)
        )

        out["Price"] = (
            pd.to_numeric(
                out["Price"],
                errors="coerce"
            )
        )

        out = out.dropna(
            subset=[
                "Date",
                "Ticker",
                "Price",
            ]
        )

        return out

    # --------------------------------------------------------------------------
    # Wide daily matrix.
    # --------------------------------------------------------------------------

    try:

        idx = pd.to_datetime(
            df.index,
            errors="coerce"
        )

        valid_ratio = (
            pd.Series(idx)
            .notna()
            .mean()
        )

        median_year = (
            pd.Series(idx)
            .dropna()
            .dt.year
            .median()
        )

        ticker_cols = [
            c
            for c in df.columns
            if v16q_is_ticker_name(c)
        ]

        if (
            valid_ratio > 0.95
            and np.isfinite(median_year)
            and median_year >= 1990
            and len(ticker_cols) >= 2
        ):

            temp = (
                df[
                    ticker_cols
                ]
                .copy()
            )

            temp.index = (
                v16q_normalize_date_index(
                    temp.index
                )
            )

            long = (
                temp
                .stack(
                    dropna=False
                )
                .rename(
                    "Price"
                )
                .reset_index()
            )

            long.columns = [
                "Date",
                "Ticker",
                "Price",
            ]

            long["Price"] = (
                pd.to_numeric(
                    long["Price"],
                    errors="coerce"
                )
            )

            return long.dropna(
                subset=[
                    "Date",
                    "Ticker",
                    "Price",
                ]
            )

    except Exception:
        pass

    return None


V16Q_PRICE_PREFERENCE = [

    "V15_REPAIRED_LIFECYCLE_PRICE_LEDGER",
    "V12_LIFECYCLE",
    "V11_LIFECYCLE",
    "V10_LIFECYCLE_PANEL",
    "V10_B3_LIFECYCLE",
    "V9_B3_LIFECYCLE",
    "existing_lifecycle",
    "B38_ALL_PRICES",
    "B40_PRICE",
]

V16Q_PRICE_CANDIDATES = []

for name in V16Q_PRICE_PREFERENCE:

    if name not in globals():
        continue

    try:

        candidate = (
            v16q_price_long_from_object(
                globals()[name]
            )
        )

        if (
            candidate is None
            or candidate.empty
        ):
            continue

        tickers = set(
            candidate["Ticker"]
            .astype(str)
            .unique()
        )

        dates = (
            candidate["Date"]
            .nunique()
        )

        rows = len(candidate)

        tqqq_present = (
            "TQQQ" in tickers
        )

        score = (
            1000000
            * int(tqqq_present)
            +
            100
            * dates
            +
            min(
                rows,
                5_000_000
            )
            / 1000
        )

        V16Q_PRICE_CANDIDATES.append(
            {
                "Name":
                    name,

                "Object":
                    candidate,

                "Rows":
                    rows,

                "Dates":
                    dates,

                "Tickers":
                    len(tickers),

                "TQQQ":
                    tqqq_present,

                "Score":
                    score,
            }
        )

    except Exception:
        pass

if not V16Q_PRICE_CANDIDATES:

    raise RuntimeError(
        "No valid full-daily lifecycle price ledger could be located."
    )

V16Q_PRICE_META = (
    pd.DataFrame(
        [
            {
                k: v
                for k, v in x.items()
                if k != "Object"
            }
            for x in V16Q_PRICE_CANDIDATES
        ]
    )
    .sort_values(
        "Score",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)

V16Q_PRICE_WINNER_NAME = (
    V16Q_PRICE_META.iloc[0]["Name"]
)

V16Q_PRICE_LONG = next(
    x["Object"]
    for x in V16Q_PRICE_CANDIDATES
    if x["Name"] == V16Q_PRICE_WINNER_NAME
)

print(
    f"\n[+] Canonical daily price source : {V16Q_PRICE_WINNER_NAME}"
)

print(
    f"[+] Daily price rows             : {len(V16Q_PRICE_LONG):,}"
)

print(
    f"[+] Daily price tickers          : "
    f"{V16Q_PRICE_LONG['Ticker'].nunique():,}"
)

print(
    f"[+] Daily trading dates          : "
    f"{V16Q_PRICE_LONG['Date'].nunique():,}"
)


# ==============================================================================
# 4. FIND V16 EVENT-LEVEL TARGET WEIGHT MATRIX
# ==============================================================================

def v16q_coerce_target_matrix(
    obj,
    prefix="V16"
):

    # --------------------------------------------------------------------------
    # Dict: date -> weights.
    # --------------------------------------------------------------------------

    if isinstance(
        obj,
        dict
    ):

        rows = []

        for key, value in obj.items():

            if isinstance(
                value,
                pd.Series
            ):
                value = value.to_dict()

            if not isinstance(
                value,
                dict
            ):
                continue

            try:
                date = pd.Timestamp(key).normalize()
            except Exception:
                continue

            row = {
                "Execution_Date":
                    date
            }

            for ticker, weight in value.items():

                try:
                    row[str(ticker)] = float(weight)
                except Exception:
                    pass

            rows.append(
                row
            )

        if len(rows) >= 2:

            return (
                pd.DataFrame(rows)
                .set_index(
                    "Execution_Date"
                )
                .sort_index()
            )

        return None

    # --------------------------------------------------------------------------
    # List of records.
    # --------------------------------------------------------------------------

    if isinstance(
        obj,
        (list, tuple)
    ):

        try:
            obj = pd.DataFrame(obj)
        except Exception:
            return None

    if not isinstance(
        obj,
        pd.DataFrame
    ):
        return None

    df = obj.copy()

    # --------------------------------------------------------------------------
    # Column containing dict-like weights.
    # --------------------------------------------------------------------------

    dict_cols = []

    for c in df.columns:

        vals = (
            df[c]
            .dropna()
        )

        if vals.empty:
            continue

        sample = vals.iloc[0]

        if isinstance(
            sample,
            (dict, pd.Series)
        ):
            dict_cols.append(c)

    if dict_cols:

        date_c = v16q_first_existing(
            df.columns,
            [
                "Execution_Date",
                "Date",
                "Signal_Date",
            ]
        )

        if date_c is not None:

            rows = []

            for _, r in df.iterrows():

                try:

                    date = pd.Timestamp(
                        r[date_c]
                    ).normalize()

                except Exception:
                    continue

                weights = r[
                    dict_cols[0]
                ]

                if isinstance(
                    weights,
                    pd.Series
                ):
                    weights = weights.to_dict()

                if not isinstance(
                    weights,
                    dict
                ):
                    continue

                row = {
                    "Execution_Date":
                        date
                }

                for ticker, weight in weights.items():

                    try:
                        row[str(ticker)] = float(weight)
                    except Exception:
                        pass

                rows.append(row)

            if rows:

                return (
                    pd.DataFrame(rows)
                    .set_index(
                        "Execution_Date"
                    )
                    .sort_index()
                )

    # --------------------------------------------------------------------------
    # Long target format.
    # --------------------------------------------------------------------------

    date_c = v16q_first_existing(
        df.columns,
        [
            "Execution_Date",
            "Date",
            "Signal_Date",
        ]
    )

    ticker_c = v16q_first_existing(
        df.columns,
        [
            "Ticker",
            "Symbol",
            "Asset",
        ]
    )

    weight_c = v16q_first_existing(
        df.columns,
        [
            "Target_Weight",
            "Weight",
            "Portfolio_Weight",
            "Final_Weight",
            "Weight_Fraction",
            "V16_Weight",
            "TargetWeight",
        ]
    )

    if (
        date_c is not None
        and ticker_c is not None
        and weight_c is not None
    ):

        temp = df[
            [
                date_c,
                ticker_c,
                weight_c,
            ]
        ].copy()

        temp[date_c] = (
            v16q_normalize_date_series(
                temp[date_c]
            )
        )

        temp[weight_c] = (
            pd.to_numeric(
                temp[weight_c],
                errors="coerce"
            )
        )

        temp = temp.dropna()

        if not temp.empty:

            return (
                temp
                .pivot_table(
                    index=date_c,
                    columns=ticker_c,
                    values=weight_c,
                    aggfunc="sum"
                )
                .fillna(0.0)
                .sort_index()
            )

    # --------------------------------------------------------------------------
    # Wide target matrix.
    # --------------------------------------------------------------------------

    temp = df.copy()

    if date_c is not None:

        temp.index = (
            v16q_normalize_date_series(
                temp[date_c]
            )
        )

        temp = temp.drop(
            columns=[
                date_c
            ],
            errors="ignore"
        )

    else:

        try:

            idx = pd.to_datetime(
                temp.index,
                errors="coerce"
            )

            year_med = (
                pd.Series(idx)
                .dropna()
                .dt.year
                .median()
            )

            if (
                pd.Series(idx)
                .notna()
                .mean()
                <
                0.90
            ):
                return None

            if (
                not np.isfinite(year_med)
                or year_med < 1990
            ):
                return None

            temp.index = (
                v16q_normalize_date_index(
                    temp.index
                )
            )

        except Exception:
            return None

    ticker_cols = [
        c
        for c in temp.columns
        if v16q_is_ticker_name(c)
    ]

    if len(ticker_cols) < 2:
        return None

    temp = (
        temp[
            ticker_cols
        ]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
        .fillna(0.0)
    )

    return (
        temp
        .groupby(
            level=0
        )
        .last()
        .sort_index()
    )


def v16q_standardize_weight_matrix(
    matrix
):

    if matrix is None:
        return None

    m = matrix.copy()

    m.index = (
        v16q_normalize_date_index(
            m.index
        )
    )

    m = (
        m
        .groupby(
            level=0
        )
        .last()
        .sort_index()
    )

    m = (
        m
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
        .fillna(0.0)
    )

    m = m.loc[
        :,
        [
            c
            for c in m.columns
            if v16q_is_ticker_name(c)
        ]
    ]

    if m.empty:
        return None

    row_sum = (
        m.sum(axis=1)
    )

    positive = (
        row_sum > 0
    )

    if not positive.any():
        return None

    median_sum = float(
        row_sum.loc[
            positive
        ].median()
    )

    if 50 <= median_sum <= 150:

        m = m / 100.0
        row_sum = m.sum(axis=1)

    valid_sum = (
        row_sum > 1e-12
    )

    m.loc[
        valid_sum
    ] = (
        m.loc[
            valid_sum
        ]
        .div(
            row_sum.loc[
                valid_sum
            ],
            axis=0
        )
    )

    return m


V16Q_TARGET_CANDIDATES = []

explicit_target_names = [

    "V16_TARGET_MATRIX",
    "V16_WEIGHT_MATRIX",
    "V16_EVENT_TARGETS",
    "V16_EVENT_TARGET_WEIGHTS",
    "V16_TARGET_WEIGHTS",
    "V16_TARGETS",
    "V16_TARGET_ROWS",
    "V16_PORTFOLIO_TARGETS",
    "V16_PREDECLARED_TARGETS",
]

scan_target_names = []

for name, obj in list(
    globals().items()
):

    upper = str(name).upper()

    if not upper.startswith("V16"):
        continue

    if not any(
        token in upper
        for token in [
            "TARGET",
            "WEIGHT",
            "PORTFOLIO",
            "ALLOCATION",
        ]
    ):
        continue

    if name == "V16_FINAL_TARGET":
        continue

    scan_target_names.append(
        name
    )

target_names = []

for x in (
    explicit_target_names
    +
    scan_target_names
):

    if x not in target_names:
        target_names.append(x)

for name in target_names:

    if name not in globals():
        continue

    try:

        matrix = (
            v16q_coerce_target_matrix(
                globals()[name]
            )
        )

        matrix = (
            v16q_standardize_weight_matrix(
                matrix
            )
        )

        if (
            matrix is None
            or matrix.empty
        ):
            continue

        exec_overlap = len(
            matrix.index.intersection(
                V16Q_EXEC_DATES
            )
        )

        signal_overlap = 0

        if signal_col is not None:

            sig_dates = pd.DatetimeIndex(
                V16Q_PATH[signal_col]
            )

            signal_overlap = len(
                matrix.index.intersection(
                    sig_dates
                )
            )

        remapped = False

        if (
            signal_overlap > exec_overlap
            and signal_col is not None
        ):

            mapping = dict(
                zip(
                    V16Q_PATH[signal_col],
                    V16Q_PATH[exec_col]
                )
            )

            mapped_index = [
                mapping.get(
                    d,
                    d
                )
                for d in matrix.index
            ]

            matrix.index = (
                pd.DatetimeIndex(
                    mapped_index
                )
            )

            matrix = (
                matrix
                .groupby(
                    level=0
                )
                .last()
            )

            exec_overlap = len(
                matrix.index.intersection(
                    V16Q_EXEC_DATES
                )
            )

            remapped = True

        row_sums = (
            matrix.sum(
                axis=1
            )
        )

        row_sum_error = float(
            (
                row_sums
                -
                1.0
            )
            .abs()
            .median()
        )

        coverage = (
            exec_overlap
            /
            max(
                len(
                    V16Q_EXEC_DATES
                ),
                1
            )
        )

        score = (
            1000.0
            *
            coverage
            -
            100.0
            *
            row_sum_error
            +
            min(
                matrix.shape[1],
                2000
            )
            /
            2000.0
        )

        V16Q_TARGET_CANDIDATES.append(
            {
                "Name":
                    name,

                "Matrix":
                    matrix,

                "Execution_Overlap":
                    exec_overlap,

                "Coverage":
                    coverage,

                "Tickers":
                    matrix.shape[1],

                "Rows":
                    matrix.shape[0],

                "Signal_Remapped":
                    remapped,

                "Score":
                    score,
            }
        )

    except Exception:
        pass


if not V16Q_TARGET_CANDIDATES:

    print(
        "\n[!] Historical V16 event target matrix was not found as a "
        "named notebook object."
    )

    print(
        "[!] Target-dependent exact DAILY NAV / attribution sections "
        "cannot be certified."
    )

    V16Q_TARGET_MATRIX = None
    V16Q_TARGET_SOURCE = None

else:

    V16Q_TARGET_CANDIDATES.sort(
        key=lambda x:
            x["Score"],
        reverse=True
    )

    winner = (
        V16Q_TARGET_CANDIDATES[0]
    )

    V16Q_TARGET_MATRIX = (
        winner["Matrix"]
        .copy()
    )

    V16Q_TARGET_SOURCE = (
        winner["Name"]
    )

    print(
        f"\n[+] V16 historical target source : {V16Q_TARGET_SOURCE}"
    )

    print(
        f"[+] Execution-date coverage      : "
        f"{winner['Execution_Overlap']}/{len(V16Q_EXEC_DATES)}"
    )

    print(
        f"[+] Historical target tickers    : "
        f"{winner['Tickers']:,}"
    )


# ==============================================================================
# 5. BUILD DAILY WIDE PRICE MATRIX
# ==============================================================================

needed_tickers = {
    "TQQQ",
    "QQQ",
    "SPY",
}

if V16Q_TARGET_MATRIX is not None:

    needed_tickers.update(
        [
            str(x)
            for x in V16Q_TARGET_MATRIX.columns
        ]
    )

V16Q_PRICE_SUBSET = (
    V16Q_PRICE_LONG[
        V16Q_PRICE_LONG[
            "Ticker"
        ].isin(
            needed_tickers
        )
    ]
    .copy()
)

V16Q_PRICE_WIDE = (
    V16Q_PRICE_SUBSET
    .pivot_table(
        index="Date",
        columns="Ticker",
        values="Price",
        aggfunc="last"
    )
    .sort_index()
)

V16Q_PRICE_WIDE.index = (
    v16q_normalize_date_index(
        V16Q_PRICE_WIDE.index
    )
)

print(
    f"\n[+] Analysis price matrix        : "
    f"{V16Q_PRICE_WIDE.shape[0]:,} dates × "
    f"{V16Q_PRICE_WIDE.shape[1]:,} assets"
)


# ==============================================================================
# 6. EVENT ECONOMIC COLUMNS
# ==============================================================================

wealth_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "V16_Wealth",
        "End_Wealth",
        "Wealth",
    ]
)

turnover_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "Turnover",
        "V16_Turnover",
        "Total_Turnover",
    ]
)

tca_bps_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "TCA_bps",
        "V16_TCA_bps",
        "Cost_bps",
    ]
)

tca_frac_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "V16_TCA",
        "TCA",
        "Cost_Fraction",
    ]
)

net_ret_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "Net_Return_Pct",
        "V16_Return_Pct",
        "V16_Net_Return_Pct",
        "V16_Net_Return",
    ]
)

v8_ret_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "V8_Return_Pct",
        "V8_Net_Return_Pct",
        "V8_Return",
    ]
)

tqqq_ret_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "TQQQ_Return_Pct",
        "TQQQ_Net_Return_Pct",
        "TQQQ_Return",
    ]
)

lambda_col = v16q_first_existing(
    V16Q_PATH.columns,
    [
        "Pre_Lambda",
        "Lambda",
        "Residual_Lambda",
        "Tilt_Lambda",
    ]
)


def v16q_event_cost_fraction(row):

    if tca_bps_col is not None:

        value = row[
            tca_bps_col
        ]

        if pd.notna(value):
            return max(
                0.0,
                float(value)
                /
                10000.0
            )

    if tca_frac_col is not None:

        value = row[
            tca_frac_col
        ]

        if pd.notna(value):

            value = float(value)

            if abs(value) > 0.05:
                value = value / 10000.0

            return max(
                0.0,
                value
            )

    if (
        turnover_col is not None
        and "B40_TCA_RATE" in globals()
    ):

        return (
            float(
                row[
                    turnover_col
                ]
            )
            *
            float(
                B40_TCA_RATE
            )
        )

    return 0.0


# ==============================================================================
# 7. EXACT EXECUTION-TO-EXECUTION EVENT RECONSTRUCTION
# ==============================================================================

V16Q_EVENT_RECON = []
V16Q_DAILY_PARTS = []
V16Q_ATTRIBUTION_ROWS = []
V16Q_COST_ROWS = []

V16Q_DAILY_CERTIFIED = False
V16Q_ACCOUNTING_MODE = None
V16Q_MISSING_DAILY_MARKS = []

if (
    V16Q_TARGET_MATRIX is not None
    and wealth_col is not None
):

    event_temp = []

    # --------------------------------------------------------------------------
    # 7A. Calculate pure asset gross returns before choosing TCA accounting mode.
    # --------------------------------------------------------------------------

    for i, row in (
        V16Q_PATH.iterrows()
    ):

        execution_date = pd.Timestamp(
            row[
                exec_col
            ]
        )

        exit_date = pd.Timestamp(
            row[
                exit_col
            ]
        )

        if execution_date not in V16Q_TARGET_MATRIX.index:

            event_temp.append(
                {
                    "Index":
                        i,

                    "Execution_Date":
                        execution_date,

                    "Exit_Date":
                        exit_date,

                    "Valid":
                        False,

                    "Reason":
                        "MISSING_TARGET",
                }
            )

            continue

        w = (
            V16Q_TARGET_MATRIX
            .loc[
                execution_date
            ]
            .astype(float)
        )

        w = w[
            w > 1e-14
        ]

        if w.empty:

            event_temp.append(
                {
                    "Index":
                        i,

                    "Execution_Date":
                        execution_date,

                    "Exit_Date":
                        exit_date,

                    "Valid":
                        False,

                    "Reason":
                        "EMPTY_TARGET",
                }
            )

            continue

        w = w / w.sum()

        assets = list(
            w.index
        )

        entry = (
            V16Q_PRICE_WIDE
            .reindex(
                index=[
                    execution_date
                ],
                columns=assets
            )
            .iloc[0]
        )

        exit_price = (
            V16Q_PRICE_WIDE
            .reindex(
                index=[
                    exit_date
                ],
                columns=assets
            )
            .iloc[0]
        )

        bad_entry = (
            ~np.isfinite(
                entry
            )
            |
            (
                entry <= 0
            )
        )

        bad_exit = (
            ~np.isfinite(
                exit_price
            )
            |
            (
                exit_price <= 0
            )
        )

        if (
            bad_entry.any()
            or bad_exit.any()
        ):

            event_temp.append(
                {
                    "Index":
                        i,

                    "Execution_Date":
                        execution_date,

                    "Exit_Date":
                        exit_date,

                    "Valid":
                        False,

                    "Reason":
                        "MISSING_ECONOMIC_PRICE",

                    "Bad_Entry":
                        list(
                            entry.index[
                                bad_entry
                            ]
                        ),

                    "Bad_Exit":
                        list(
                            exit_price.index[
                                bad_exit
                            ]
                        ),
                }
            )

            continue

        asset_return = (
            exit_price
            /
            entry
            -
            1.0
        )

        gross_return = float(
            (
                w
                *
                asset_return
            )
            .sum()
        )

        event_temp.append(
            {
                "Index":
                    i,

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    exit_date,

                "Valid":
                    True,

                "Weights":
                    w,

                "Entry":
                    entry,

                "Exit":
                    exit_price,

                "Asset_Return":
                    asset_return,

                "Gross_Return":
                    gross_return,

                "Reported_Cost":
                    v16q_event_cost_fraction(
                        row
                    ),

                "Official_Wealth":
                    float(
                        row[
                            wealth_col
                        ]
                    ),
            }
        )

    valid_temp = [
        x
        for x in event_temp
        if x.get(
            "Valid",
            False
        )
    ]

    # --------------------------------------------------------------------------
    # 7B. Discover accounting convention.
    #     This is accounting verification, NOT strategy tuning.
    # --------------------------------------------------------------------------

    mode_errors = {}

    for mode in [
        "MULTIPLICATIVE_TCA",
        "ADDITIVE_TCA",
    ]:

        errors = []

        previous_official_wealth = 1.0

        for item in valid_temp:

            gross = (
                item[
                    "Gross_Return"
                ]
            )

            cost = (
                item[
                    "Reported_Cost"
                ]
            )

            if mode == "MULTIPLICATIVE_TCA":

                reconstructed = (
                    previous_official_wealth
                    *
                    (
                        1.0
                        -
                        cost
                    )
                    *
                    (
                        1.0
                        +
                        gross
                    )
                )

            else:

                reconstructed = (
                    previous_official_wealth
                    *
                    (
                        1.0
                        +
                        gross
                        -
                        cost
                    )
                )

            error = (
                reconstructed
                -
                item[
                    "Official_Wealth"
                ]
            )

            errors.append(
                abs(
                    error
                )
            )

            previous_official_wealth = (
                item[
                    "Official_Wealth"
                ]
            )

        mode_errors[
            mode
        ] = (
            max(
                errors
            )
            if errors
            else np.inf
        )

    V16Q_ACCOUNTING_MODE = min(
        mode_errors,
        key=
            mode_errors.get
    )

    print(
        f"\n[+] V16 accounting convention    : {V16Q_ACCOUNTING_MODE}"
    )

    print(
        "[+] Multiplicative max error     : "
        f"{mode_errors['MULTIPLICATIVE_TCA']:.12f}"
    )

    print(
        "[+] Additive max error           : "
        f"{mode_errors['ADDITIVE_TCA']:.12f}"
    )

    # --------------------------------------------------------------------------
    # 7C. Exact event reconstruction + daily marks.
    # --------------------------------------------------------------------------

    previous_official_wealth = 1.0

    for event_no, item in enumerate(
        valid_temp,
        start=1
    ):

        execution_date = (
            item[
                "Execution_Date"
            ]
        )

        exit_date = (
            item[
                "Exit_Date"
            ]
        )

        w = item[
            "Weights"
        ]

        entry = item[
            "Entry"
        ]

        gross = item[
            "Gross_Return"
        ]

        cost = item[
            "Reported_Cost"
        ]

        official_wealth = item[
            "Official_Wealth"
        ]

        if (
            V16Q_ACCOUNTING_MODE
            ==
            "MULTIPLICATIVE_TCA"
        ):

            wealth_after_cost = (
                previous_official_wealth
                *
                (
                    1.0
                    -
                    cost
                )
            )

            reconstructed_wealth = (
                wealth_after_cost
                *
                (
                    1.0
                    +
                    gross
                )
            )

            asset_base = (
                wealth_after_cost
            )

        else:

            wealth_after_cost = (
                previous_official_wealth
                *
                (
                    1.0
                    -
                    cost
                )
            )

            reconstructed_wealth = (
                previous_official_wealth
                *
                (
                    1.0
                    +
                    gross
                    -
                    cost
                )
            )

            asset_base = (
                previous_official_wealth
            )

        wealth_error = (
            reconstructed_wealth
            -
            official_wealth
        )

        V16Q_EVENT_RECON.append(
            {
                "Event":
                    event_no,

                "Execution_Date":
                    execution_date,

                "Exit_Date":
                    exit_date,

                "Gross_Return":
                    gross,

                "TCA_Fraction":
                    cost,

                "Official_Wealth":
                    official_wealth,

                "Reconstructed_Wealth":
                    reconstructed_wealth,

                "Wealth_Error":
                    wealth_error,

                "Abs_Wealth_Error":
                    abs(
                        wealth_error
                    ),
            }
        )

        V16Q_COST_ROWS.append(
            {
                "Event":
                    event_no,

                "Execution_Date":
                    execution_date,

                "Turnover":
                    (
                        float(
                            V16Q_PATH
                            .iloc[
                                item[
                                    "Index"
                                ]
                            ][
                                turnover_col
                            ]
                        )
                        if turnover_col is not None
                        else np.nan
                    ),

                "TCA_bps":
                    10000.0
                    *
                    cost,

                "Exact_TCA_Wealth_Contribution":
                    -
                    previous_official_wealth
                    *
                    cost,
            }
        )

        for asset in w.index:

            asset_return = float(
                item[
                    "Asset_Return"
                ][
                    asset
                ]
            )

            contribution = (
                asset_base
                *
                float(
                    w[
                        asset
                    ]
                )
                *
                asset_return
            )

            V16Q_ATTRIBUTION_ROWS.append(
                {
                    "Event":
                        event_no,

                    "Execution_Date":
                        execution_date,

                    "Exit_Date":
                        exit_date,

                    "Ticker":
                        asset,

                    "Bucket":
                        (
                            "TQQQ_CORE"
                            if asset == "TQQQ"
                            else "STOCK_SLEEVE"
                        ),

                    "Target_Weight":
                        float(
                            w[
                                asset
                            ]
                        ),

                    "Asset_Return":
                        asset_return,

                    "Arithmetic_Return_Contribution":
                        float(
                            w[
                                asset
                            ]
                        )
                        *
                        asset_return,

                    "Exact_Wealth_Contribution":
                        contribution,
                }
            )

        # ----------------------------------------------------------------------
        # DAILY NAV.
        #
        # Do NOT fabricate missing intermediate quotes.
        # A missing intermediate quote leaves that particular daily mark NaN.
        # Event-end economics remain exact and separately validated.
        # ----------------------------------------------------------------------

        final_holding_period = (
            event_no
            ==
            len(
                valid_temp
            )
        )

        if final_holding_period:

            mark_dates = (
                V16Q_PRICE_WIDE.index[
                    (
                        V16Q_PRICE_WIDE.index
                        >=
                        execution_date
                    )
                    &
                    (
                        V16Q_PRICE_WIDE.index
                        <=
                        exit_date
                    )
                ]
            )

        else:

            mark_dates = (
                V16Q_PRICE_WIDE.index[
                    (
                        V16Q_PRICE_WIDE.index
                        >=
                        execution_date
                    )
                    &
                    (
                        V16Q_PRICE_WIDE.index
                        <
                        exit_date
                    )
                ]
            )

        if len(
            mark_dates
        ):

            block = (
                V16Q_PRICE_WIDE
                .reindex(
                    index=
                        mark_dates,

                    columns=
                        list(
                            w.index
                        )
                )
                .copy()
            )

            relative = (
                block
                .div(
                    entry,
                    axis=1
                )
            )

            valid_row = (
                np.isfinite(
                    relative
                )
                .all(
                    axis=1
                )
            )

            if (
                ~valid_row
            ).any():

                bad_dates = list(
                    relative.index[
                        ~valid_row
                    ]
                )

                for d in bad_dates:

                    bad_assets = list(
                        relative.columns[
                            ~np.isfinite(
                                relative.loc[
                                    d
                                ]
                            )
                        ]
                    )

                    V16Q_MISSING_DAILY_MARKS.append(
                        {
                            "Execution_Date":
                                execution_date,

                            "Date":
                                d,

                            "Missing_Assets":
                                bad_assets,
                        }
                    )

            weighted_relative = (
                relative
                .mul(
                    w,
                    axis=1
                )
                .sum(
                    axis=1,
                    min_count=
                        len(
                            w
                        )
                )
            )

            if (
                V16Q_ACCOUNTING_MODE
                ==
                "MULTIPLICATIVE_TCA"
            ):

                daily_nav = (
                    previous_official_wealth
                    *
                    (
                        1.0
                        -
                        cost
                    )
                    *
                    weighted_relative
                )

            else:

                weighted_return = (
                    weighted_relative
                    -
                    1.0
                )

                daily_nav = (
                    previous_official_wealth
                    *
                    (
                        1.0
                        -
                        cost
                        +
                        weighted_return
                    )
                )

            V16Q_DAILY_PARTS.append(
                daily_nav
            )

        previous_official_wealth = (
            official_wealth
        )

    V16Q_VALIDATION = (
        pd.DataFrame(
            V16Q_EVENT_RECON
        )
    )

    V16Q_MAX_WEALTH_ERROR = float(
        V16Q_VALIDATION[
            "Abs_Wealth_Error"
        ]
        .max()
    )

    V16Q_DAILY_CERTIFIED = (
        V16Q_MAX_WEALTH_ERROR
        <
        5e-5
    )

    print(
        "\nDaily/event NAV reconstruction max wealth error:",
        f"{V16Q_MAX_WEALTH_ERROR:.12f}"
    )

    if V16Q_DAILY_CERTIFIED:

        print(
            "[+] EXACT EVENT ECONOMICS VALIDATION PASSED."
        )

    else:

        print(
            "[!] EVENT ECONOMICS DID NOT REPRODUCE WITH MACHINE-LEVEL "
            "TOLERANCE."
        )

        print(
            "[!] Dashboard continues, but DAILY certification is FALSE."
        )

else:

    V16Q_VALIDATION = pd.DataFrame()

    print(
        "\n[!] Exact V16 historical target reconstruction is unavailable."
    )


# ==============================================================================
# 8. DAILY V16 NAV + TERMINAL REBALANCE ADJUSTMENT
# ==============================================================================

if V16Q_DAILY_PARTS:

    V16Q_DAILY = (
        pd.concat(
            V16Q_DAILY_PARTS
        )
        .groupby(
            level=0
        )
        .last()
        .sort_index()
    )

    V16Q_DAILY.name = (
        "V16"
    )

    # --------------------------------------------------------------------------
    # Research V16 final wealth includes terminal rebalance if applicable.
    # --------------------------------------------------------------------------

    V16Q_FINAL_WEALTH = float(
        V16_FINAL_WEALTH
    )

    last_holding_wealth = float(
        V16Q_PATH[
            wealth_col
        ]
        .iloc[
            -1
        ]
    )

    V16Q_TERMINAL_REBALANCE_CONTRIBUTION = (
        V16Q_FINAL_WEALTH
        -
        last_holding_wealth
    )

    if (
        V16Q_RESEARCH_END
        in
        V16Q_DAILY.index
    ):

        V16Q_DAILY.loc[
            V16Q_RESEARCH_END
        ] = (
            V16Q_FINAL_WEALTH
        )

    else:

        V16Q_DAILY.loc[
            V16Q_RESEARCH_END
        ] = (
            V16Q_FINAL_WEALTH
        )

        V16Q_DAILY = (
            V16Q_DAILY
            .sort_index()
        )

else:

    V16Q_DAILY = None

    V16Q_FINAL_WEALTH = float(
        V16_FINAL_WEALTH
    )

    V16Q_TERMINAL_REBALANCE_CONTRIBUTION = np.nan


# ==============================================================================
# 9. TARGET WEIGHT / CONCENTRATION MATRIX
# ==============================================================================

if V16Q_TARGET_MATRIX is not None:

    V16Q_WEIGHT_MATRIX = (
        V16Q_TARGET_MATRIX
        .reindex(
            V16Q_EXEC_DATES
        )
        .fillna(0.0)
    )

    V16Q_WEIGHT_MATRIX.index.name = (
        "Execution_Date"
    )

    V16Q_EFFECTIVE_N = (
        1.0
        /
        (
            V16Q_WEIGHT_MATRIX
            ** 2
        )
        .sum(
            axis=1
        )
    )

    V16Q_MAX_NAME_WEIGHT = (
        100.0
        *
        V16Q_WEIGHT_MATRIX
        .max(
            axis=1
        )
    )

    V16Q_TQQQ_WEIGHT = (
        100.0
        *
        V16Q_WEIGHT_MATRIX
        .get(
            "TQQQ",
            pd.Series(
                0.0,
                index=
                    V16Q_WEIGHT_MATRIX.index
            )
        )
    )

    V16Q_STOCK_WEIGHT = (
        100.0
        -
        V16Q_TQQQ_WEIGHT
    )

    V16Q_CONCENTRATION = pd.DataFrame(
        {
            "Effective_N":
                V16Q_EFFECTIVE_N,

            "Max_Name_Weight_Pct":
                V16Q_MAX_NAME_WEIGHT,

            "TQQQ_Weight_Pct":
                V16Q_TQQQ_WEIGHT,

            "Stock_Sleeve_Weight_Pct":
                V16Q_STOCK_WEIGHT,
        }
    )

else:

    V16Q_WEIGHT_MATRIX = None
    V16Q_CONCENTRATION = pd.DataFrame()


# ==============================================================================
# 10. BENCHMARK DAILY CURVES
# ==============================================================================

def v16q_buy_hold(
    ticker
):

    if ticker not in V16Q_PRICE_WIDE.columns:
        return None

    s = (
        V16Q_PRICE_WIDE[
            ticker
        ]
        .loc[
            V16Q_START:
            V16Q_RESEARCH_END
        ]
        .dropna()
        .copy()
    )

    if s.empty:
        return None

    if V16Q_START not in s.index:
        return None

    tca_rate = float(
        globals().get(
            "B40_TCA_RATE",
            0.0002
        )
    )

    nav = (
        (
            1.0
            -
            tca_rate
        )
        *
        s
        /
        float(
            s.loc[
                V16Q_START
            ]
        )
    )

    nav.name = (
        ticker
    )

    return nav


V16Q_TQQQ = v16q_buy_hold(
    "TQQQ"
)

V16Q_QQQ = v16q_buy_hold(
    "QQQ"
)

V16Q_SPY = v16q_buy_hold(
    "SPY"
)


# ==============================================================================
# 11. OPTIONAL EXACT V8 DAILY CURVE FROM PREVIOUS DEEP-DIVE
# ==============================================================================

V16Q_V8 = None
V16Q_V8_SOURCE = None

v8_candidates = [

    "V8Q_DAILY",
    "V8_DAILY_NAV",
    "V8Q_DAILY_V8",
]

for candidate_name in v8_candidates:

    if (
        candidate_name in globals()
        and isinstance(
            globals()[
                candidate_name
            ],
            pd.Series
        )
    ):

        temp = (
            globals()[
                candidate_name
            ]
            .copy()
        )

        temp.index = (
            v16q_normalize_date_index(
                temp.index
            )
        )

        temp = (
            temp
            .loc[
                (
                    temp.index
                    >=
                    V16Q_START
                )
                &
                (
                    temp.index
                    <=
                    V16Q_RESEARCH_END
                )
            ]
            .sort_index()
        )

        if not temp.empty:

            temp.name = (
                "V8"
            )

            V16Q_V8 = temp
            V16Q_V8_SOURCE = candidate_name
            break

if (
    V16Q_V8 is None
    and "V8Q_DAILY_CURVES" in globals()
    and isinstance(
        V8Q_DAILY_CURVES,
        pd.DataFrame
    )
    and "V8" in V8Q_DAILY_CURVES.columns
):

    temp = (
        V8Q_DAILY_CURVES[
            "V8"
        ]
        .copy()
    )

    temp.index = (
        v16q_normalize_date_index(
            temp.index
        )
    )

    temp = (
        temp
        .loc[
            (
                temp.index
                >=
                V16Q_START
            )
            &
            (
                temp.index
                <=
                V16Q_RESEARCH_END
            )
        ]
        .sort_index()
    )

    if not temp.empty:

        temp.name = "V8"

        V16Q_V8 = temp
        V16Q_V8_SOURCE = (
            "V8Q_DAILY_CURVES['V8']"
        )

if V16Q_V8 is not None:

    print(
        f"\n[+] Exact V8 daily comparator    : {V16Q_V8_SOURCE}"
    )

else:

    print(
        "\n[i] Exact V8 daily curve not present in current RAM."
    )

    print(
        "[i] V8 remains available at event level from V16_PATH."
    )


# ==============================================================================
# 12. MASTER DAILY CURVES
# ==============================================================================

curve_dict = {}

if V16Q_DAILY is not None:
    curve_dict["V16"] = V16Q_DAILY

if V16Q_V8 is not None:
    curve_dict["V8"] = V16Q_V8

if V16Q_TQQQ is not None:
    curve_dict["TQQQ"] = V16Q_TQQQ

if V16Q_QQQ is not None:
    curve_dict["QQQ"] = V16Q_QQQ

if V16Q_SPY is not None:
    curve_dict["SPY"] = V16Q_SPY

V16Q_DAILY_CURVES = (
    pd.concat(
        curve_dict,
        axis=1
    )
    .sort_index()
)


# ==============================================================================
# 13. DAILY RETURN HELPER
# ==============================================================================

def v16q_returns(nav):

    nav = nav.dropna()

    if nav.empty:
        return pd.Series(dtype=float)

    ret = (
        nav
        .pct_change(
            fill_method=None
        )
    )

    ret.iloc[0] = (
        nav.iloc[0]
        -
        1.0
    )

    return ret


V16Q_DAILY_RETURNS = pd.DataFrame(
    index=
        V16Q_DAILY_CURVES.index
)

for col in (
    V16Q_DAILY_CURVES.columns
):

    V16Q_DAILY_RETURNS[
        col
    ] = (
        v16q_returns(
            V16Q_DAILY_CURVES[
                col
            ]
        )
    )


# ==============================================================================
# 14. MONTHLY / YEARLY RETURNS
# ==============================================================================

V16Q_MONTHLY_NAV = (
    V16Q_DAILY_CURVES
    .resample("M")
    .last()
)

V16Q_MONTHLY_RETURNS = (
    V16Q_MONTHLY_NAV
    .pct_change(
        fill_method=None
    )
)

if len(
    V16Q_MONTHLY_RETURNS
):

    V16Q_MONTHLY_RETURNS.iloc[0] = (
        V16Q_MONTHLY_NAV.iloc[0]
        -
        1.0
    )

V16Q_MONTHLY_RETURNS_PCT = (
    100.0
    *
    V16Q_MONTHLY_RETURNS
)

V16Q_YEARLY_NAV = (
    V16Q_DAILY_CURVES
    .resample("Y")
    .last()
)

V16Q_YEARLY_RETURNS = (
    V16Q_YEARLY_NAV
    .pct_change(
        fill_method=None
    )
)

if len(
    V16Q_YEARLY_RETURNS
):

    V16Q_YEARLY_RETURNS.iloc[0] = (
        V16Q_YEARLY_NAV.iloc[0]
        -
        1.0
    )

V16Q_YEARLY_RETURNS_PCT = (
    100.0
    *
    V16Q_YEARLY_RETURNS
)

V16Q_YEARLY_RETURNS_PCT.index = (
    V16Q_YEARLY_RETURNS_PCT.index.year
)


# ==============================================================================
# 15. DRAWDOWN / STREAK / CAPTURE HELPERS
# ==============================================================================

def v16q_drawdown_series(nav):

    nav = nav.dropna()

    if nav.empty:
        return nav

    initial_date = (
        nav.index[0]
        -
        pd.Timedelta(
            days=1
        )
    )

    extended = pd.concat(
        [
            pd.Series(
                [1.0],
                index=[
                    initial_date
                ]
            ),
            nav,
        ]
    )

    dd = (
        extended
        /
        extended.cummax()
        -
        1.0
    )

    return dd.iloc[1:]


def v16q_max_drawdown(nav):

    dd = v16q_drawdown_series(
        nav
    )

    if dd.empty:
        return np.nan

    return float(
        dd.min()
    )


def v16q_max_streak(condition):

    condition = (
        condition
        .fillna(False)
        .astype(bool)
    )

    if not condition.any():
        return 0

    groups = (
        condition
        !=
        condition.shift(1)
    ).cumsum()

    runs = (
        condition
        .groupby(
            groups
        )
        .sum()
    )

    return int(
        runs.max()
    )


def v16q_geometric_mean(r):

    r = (
        pd.Series(r)
        .dropna()
    )

    if r.empty:
        return np.nan

    growth = float(
        (
            1.0
            +
            r
        )
        .prod()
    )

    if growth <= 0:
        return np.nan

    return (
        growth
        **
        (
            1.0
            /
            len(r)
        )
        -
        1.0
    )


def v16q_capture_ratios(
    strategy_monthly,
    benchmark_monthly
):

    pair = (
        pd.concat(
            [
                strategy_monthly.rename(
                    "strategy"
                ),
                benchmark_monthly.rename(
                    "benchmark"
                ),
            ],
            axis=1
        )
        .dropna()
    )

    up = (
        pair[
            "benchmark"
        ]
        >
        0
    )

    down = (
        pair[
            "benchmark"
        ]
        <
        0
    )

    up_s = (
        v16q_geometric_mean(
            pair.loc[
                up,
                "strategy"
            ]
        )
    )

    up_b = (
        v16q_geometric_mean(
            pair.loc[
                up,
                "benchmark"
            ]
        )
    )

    down_s = (
        v16q_geometric_mean(
            pair.loc[
                down,
                "strategy"
            ]
        )
    )

    down_b = (
        v16q_geometric_mean(
            pair.loc[
                down,
                "benchmark"
            ]
        )
    )

    up_capture = (
        100.0
        *
        up_s
        /
        up_b
        if (
            np.isfinite(up_s)
            and
            np.isfinite(up_b)
            and
            abs(up_b) > 1e-12
        )
        else np.nan
    )

    down_capture = (
        100.0
        *
        down_s
        /
        down_b
        if (
            np.isfinite(down_s)
            and
            np.isfinite(down_b)
            and
            abs(down_b) > 1e-12
        )
        else np.nan
    )

    return (
        up_capture,
        down_capture
    )


V16Q_DRAWDOWN = pd.DataFrame(
    index=
        V16Q_DAILY_CURVES.index
)

for col in (
    V16Q_DAILY_CURVES.columns
):

    V16Q_DRAWDOWN[
        col
    ] = (
        v16q_drawdown_series(
            V16Q_DAILY_CURVES[
                col
            ]
        )
    )


# ==============================================================================
# 16. PERFORMANCE / RISK METRICS
# ==============================================================================

def v16q_metrics(
    nav,
    benchmark_nav=None
):

    nav = nav.dropna()

    if len(nav) < 2:
        return {}

    ret = (
        v16q_returns(
            nav
        )
        .dropna()
    )

    elapsed_years = (
        (
            nav.index[-1]
            -
            nav.index[0]
        ).days
        /
        365.25
    )

    final_wealth = float(
        nav.iloc[-1]
    )

    total_return = (
        final_wealth
        -
        1.0
    )

    cagr = (
        final_wealth
        **
        (
            1.0
            /
            elapsed_years
        )
        -
        1.0
        if elapsed_years > 0
        else np.nan
    )

    daily_std = float(
        ret.std(
            ddof=1
        )
    )

    annual_vol = (
        daily_std
        *
        np.sqrt(252)
    )

    sharpe = (
        ret.mean()
        /
        daily_std
        *
        np.sqrt(252)
        if daily_std > 0
        else np.nan
    )

    downside_dev = (
        np.sqrt(
            np.mean(
                np.minimum(
                    ret.to_numpy(),
                    0.0
                )
                ** 2
            )
        )
        *
        np.sqrt(252)
    )

    sortino = (
        (
            ret.mean()
            *
            252
        )
        /
        downside_dev
        if downside_dev > 0
        else np.nan
    )

    max_dd = (
        v16q_max_drawdown(
            nav
        )
    )

    calmar = (
        cagr
        /
        abs(max_dd)
        if (
            np.isfinite(max_dd)
            and
            max_dd < 0
        )
        else np.nan
    )

    dd = (
        v16q_drawdown_series(
            nav
        )
    )

    ulcer = (
        np.sqrt(
            np.mean(
                dd
                .dropna()
                .to_numpy()
                ** 2
            )
        )
        if not dd.empty
        else np.nan
    )

    var95 = float(
        ret.quantile(
            0.05
        )
    )

    cvar95 = (
        float(
            ret[
                ret <= var95
            ]
            .mean()
        )
        if (
            ret <= var95
        ).any()
        else np.nan
    )

    q95 = float(
        ret.quantile(
            0.95
        )
    )

    q05 = float(
        ret.quantile(
            0.05
        )
    )

    tail_ratio = (
        q95
        /
        abs(q05)
        if abs(q05) > 1e-12
        else np.nan
    )

    positive = ret[
        ret > 0
    ]

    negative = ret[
        ret < 0
    ]

    omega = (
        positive.sum()
        /
        abs(
            negative.sum()
        )
        if abs(
            negative.sum()
        ) > 1e-12
        else np.nan
    )

    gain_loss = (
        positive.mean()
        /
        abs(
            negative.mean()
        )
        if (
            not positive.empty
            and
            not negative.empty
            and
            abs(
                negative.mean()
            ) > 1e-12
        )
        else np.nan
    )

    result = {

        "Final_Wealth":
            final_wealth,

        "Total_Return_Pct":
            100.0
            *
            total_return,

        "CAGR_Pct":
            100.0
            *
            cagr,

        "Annualized_Vol_Pct":
            100.0
            *
            annual_vol,

        "Sharpe_rf0":
            sharpe,

        "Sortino_rf0":
            sortino,

        "Max_Drawdown_Pct":
            100.0
            *
            max_dd,

        "Calmar":
            calmar,

        "Ulcer_Index_Pct":
            100.0
            *
            ulcer,

        "Positive_Days_Pct":
            100.0
            *
            (
                ret > 0
            )
            .mean(),

        "Best_Day_Pct":
            100.0
            *
            ret.max(),

        "Worst_Day_Pct":
            100.0
            *
            ret.min(),

        "Daily_VaR95_Pct":
            100.0
            *
            var95,

        "Daily_CVaR95_Pct":
            100.0
            *
            cvar95,

        "Tail_Ratio_95_5":
            tail_ratio,

        "Omega_0":
            omega,

        "Gain_Loss_Ratio":
            gain_loss,

        "Skew":
            ret.skew(),

        "Excess_Kurtosis":
            ret.kurt(),

        "Lag1_Autocorrelation":
            ret.autocorr(
                lag=1
            ),

        "Longest_Win_Streak":
            v16q_max_streak(
                ret > 0
            ),

        "Longest_Loss_Streak":
            v16q_max_streak(
                ret < 0
            ),
    }

    if benchmark_nav is not None:

        benchmark_ret = (
            v16q_returns(
                benchmark_nav
            )
        )

        pair = (
            pd.concat(
                [
                    ret.rename(
                        "strategy"
                    ),
                    benchmark_ret.rename(
                        "benchmark"
                    ),
                ],
                axis=1
            )
            .dropna()
        )

        if len(pair) > 10:

            benchmark_var = (
                pair[
                    "benchmark"
                ]
                .var(
                    ddof=1
                )
            )

            beta = (
                pair[
                    "strategy"
                ]
                .cov(
                    pair[
                        "benchmark"
                    ]
                )
                /
                benchmark_var
                if benchmark_var > 0
                else np.nan
            )

            alpha_daily = (
                pair[
                    "strategy"
                ]
                .mean()
                -
                beta
                *
                pair[
                    "benchmark"
                ]
                .mean()
            )

            active = (
                pair[
                    "strategy"
                ]
                -
                pair[
                    "benchmark"
                ]
            )

            active_std = float(
                active.std(
                    ddof=1
                )
            )

            tracking_error = (
                active_std
                *
                np.sqrt(252)
            )

            information_ratio = (
                active.mean()
                /
                active_std
                *
                np.sqrt(252)
                if active_std > 0
                else np.nan
            )

            strategy_month = (
                nav
                .resample("M")
                .last()
                .pct_change(
                    fill_method=None
                )
            )

            benchmark_month = (
                benchmark_nav
                .resample("M")
                .last()
                .pct_change(
                    fill_method=None
                )
            )

            up_capture, down_capture = (
                v16q_capture_ratios(
                    strategy_month,
                    benchmark_month
                )
            )

            result.update(
                {

                    "Beta_vs_TQQQ":
                        beta,

                    "Correlation_vs_TQQQ":
                        pair[
                            "strategy"
                        ]
                        .corr(
                            pair[
                                "benchmark"
                            ]
                        ),

                    "Annualized_Alpha_vs_TQQQ_Pct":
                        100.0
                        *
                        alpha_daily
                        *
                        252,

                    "Tracking_Error_Pct":
                        100.0
                        *
                        tracking_error,

                    "Information_Ratio":
                        information_ratio,

                    "Daily_Beat_TQQQ_Pct":
                        100.0
                        *
                        (
                            active > 0
                        )
                        .mean(),

                    "Average_Daily_Excess_bps":
                        10000.0
                        *
                        active.mean(),

                    "Up_Capture_Pct":
                        up_capture,

                    "Down_Capture_Pct":
                        down_capture,
                }
            )

    return result


V16Q_METRIC_ROWS = []

for strategy in (
    V16Q_DAILY_CURVES.columns
):

    nav = (
        V16Q_DAILY_CURVES[
            strategy
        ]
        .dropna()
    )

    benchmark = (
        None
        if strategy == "TQQQ"
        else V16Q_TQQQ
    )

    metrics = (
        v16q_metrics(
            nav,
            benchmark_nav=
                benchmark
        )
    )

    metrics[
        "Strategy"
    ] = strategy

    V16Q_METRIC_ROWS.append(
        metrics
    )

V16Q_PERFORMANCE_TABLE = (
    pd.DataFrame(
        V16Q_METRIC_ROWS
    )
    .set_index(
        "Strategy"
    )
)


# ==============================================================================
# 17. MONTHLY STATISTICS
# ==============================================================================

monthly_rows = []

for strategy in (
    V16Q_MONTHLY_RETURNS.columns
):

    r = (
        V16Q_MONTHLY_RETURNS[
            strategy
        ]
        .dropna()
    )

    row = {

        "Strategy":
            strategy,

        "Months":
            len(r),

        "Mean_Month_Pct":
            100.0
            *
            r.mean(),

        "Median_Month_Pct":
            100.0
            *
            r.median(),

        "Monthly_Vol_Pct":
            100.0
            *
            r.std(
                ddof=1
            ),

        "Positive_Months_Pct":
            100.0
            *
            (
                r > 0
            )
            .mean(),

        "Best_Month_Pct":
            100.0
            *
            r.max(),

        "Worst_Month_Pct":
            100.0
            *
            r.min(),
    }

    if (
        strategy != "TQQQ"
        and
        "TQQQ"
        in V16Q_MONTHLY_RETURNS.columns
    ):

        pair = (
            pd.concat(
                [
                    r.rename(
                        "strategy"
                    ),
                    V16Q_MONTHLY_RETURNS[
                        "TQQQ"
                    ].rename(
                        "TQQQ"
                    ),
                ],
                axis=1
            )
            .dropna()
        )

        row[
            "Beat_TQQQ_Months_Pct"
        ] = (
            100.0
            *
            (
                pair[
                    "strategy"
                ]
                >
                pair[
                    "TQQQ"
                ]
            )
            .mean()
        )

        row[
            "Mean_Monthly_Excess_Pct"
        ] = (
            100.0
            *
            (
                pair[
                    "strategy"
                ]
                -
                pair[
                    "TQQQ"
                ]
            )
            .mean()
        )

    monthly_rows.append(
        row
    )

V16Q_MONTHLY_STATS = (
    pd.DataFrame(
        monthly_rows
    )
    .set_index(
        "Strategy"
    )
)


# ==============================================================================
# 18. 1M / 3M / 6M / 12M HORIZON ANALYSIS
# ==============================================================================

V16Q_HORIZONS = {

    "1M":
        21,

    "3M":
        63,

    "6M":
        126,

    "12M":
        252,
}

V16Q_ROLLING_RETURNS = {}
V16Q_HORIZON_ROWS = []

if (
    "V16" in V16Q_DAILY_CURVES.columns
    and
    "TQQQ" in V16Q_DAILY_CURVES.columns
):

    pair_cols = [
        "V16",
        "TQQQ",
    ]

    if "V8" in V16Q_DAILY_CURVES.columns:
        pair_cols.append(
            "V8"
        )

    pair_nav = (
        V16Q_DAILY_CURVES[
            pair_cols
        ]
        .dropna(
            subset=[
                "V16",
                "TQQQ",
            ]
        )
    )

    for label, days in (
        V16Q_HORIZONS.items()
    ):

        rolling = (
            pair_nav
            /
            pair_nav.shift(
                days
            )
            -
            1.0
        )

        rolling[
            "V16_minus_TQQQ"
        ] = (
            rolling[
                "V16"
            ]
            -
            rolling[
                "TQQQ"
            ]
        )

        if "V8" in rolling.columns:

            rolling[
                "V16_minus_V8"
            ] = (
                rolling[
                    "V16"
                ]
                -
                rolling[
                    "V8"
                ]
            )

        V16Q_ROLLING_RETURNS[
            label
        ] = rolling

        valid = (
            rolling
            .dropna(
                subset=[
                    "V16",
                    "TQQQ",
                    "V16_minus_TQQQ",
                ]
            )
        )

        if valid.empty:
            continue

        latest = (
            valid.iloc[
                -1
            ]
        )

        row = {

            "Horizon":
                label,

            "Trading_Days":
                days,

            "Latest_V16_Return_Pct":
                100.0
                *
                latest[
                    "V16"
                ],

            "Latest_TQQQ_Return_Pct":
                100.0
                *
                latest[
                    "TQQQ"
                ],

            "Latest_Excess_vs_TQQQ_Pct":
                100.0
                *
                latest[
                    "V16_minus_TQQQ"
                ],

            "V16_Beat_TQQQ_Window_Pct":
                100.0
                *
                (
                    valid[
                        "V16_minus_TQQQ"
                    ]
                    >
                    0
                )
                .mean(),

            "Mean_Excess_vs_TQQQ_Pct":
                100.0
                *
                valid[
                    "V16_minus_TQQQ"
                ]
                .mean(),

            "Median_Excess_vs_TQQQ_Pct":
                100.0
                *
                valid[
                    "V16_minus_TQQQ"
                ]
                .median(),

            "Best_Excess_vs_TQQQ_Pct":
                100.0
                *
                valid[
                    "V16_minus_TQQQ"
                ]
                .max(),

            "Worst_Excess_vs_TQQQ_Pct":
                100.0
                *
                valid[
                    "V16_minus_TQQQ"
                ]
                .min(),
        }

        if (
            "V16_minus_V8"
            in valid.columns
        ):

            v8_valid = (
                valid[
                    "V16_minus_V8"
                ]
                .dropna()
            )

            if not v8_valid.empty:

                row.update(
                    {

                        "Latest_Excess_vs_V8_Pct":
                            100.0
                            *
                            latest[
                                "V16_minus_V8"
                            ],

                        "V16_Beat_V8_Window_Pct":
                            100.0
                            *
                            (
                                v8_valid > 0
                            )
                            .mean(),

                        "Mean_Excess_vs_V8_Pct":
                            100.0
                            *
                            v8_valid.mean(),

                        "Median_Excess_vs_V8_Pct":
                            100.0
                            *
                            v8_valid.median(),
                    }
                )

        V16Q_HORIZON_ROWS.append(
            row
        )

V16Q_HORIZON_TABLE = (
    pd.DataFrame(
        V16Q_HORIZON_ROWS
    )
)


# ==============================================================================
# 19. 63-DAY ROLLING RISK
# ==============================================================================

V16Q_ROLLING_WINDOW = 63

rolling_cols = [
    c
    for c in [
        "V16",
        "V8",
        "TQQQ",
        "QQQ",
    ]
    if c in V16Q_DAILY_RETURNS.columns
]

V16Q_ROLLING_VOL = (
    V16Q_DAILY_RETURNS[
        rolling_cols
    ]
    .rolling(
        V16Q_ROLLING_WINDOW
    )
    .std()
    *
    np.sqrt(252)
    *
    100.0
)

V16Q_ROLLING_SHARPE = (
    V16Q_DAILY_RETURNS[
        rolling_cols
    ]
    .rolling(
        V16Q_ROLLING_WINDOW
    )
    .mean()
    /
    V16Q_DAILY_RETURNS[
        rolling_cols
    ]
    .rolling(
        V16Q_ROLLING_WINDOW
    )
    .std()
    *
    np.sqrt(252)
)

if (
    "V16" in V16Q_DAILY_RETURNS.columns
    and
    "TQQQ" in V16Q_DAILY_RETURNS.columns
):

    V16Q_ROLLING_BETA = (
        V16Q_DAILY_RETURNS[
            "V16"
        ]
        .rolling(
            V16Q_ROLLING_WINDOW
        )
        .cov(
            V16Q_DAILY_RETURNS[
                "TQQQ"
            ]
        )
        /
        V16Q_DAILY_RETURNS[
            "TQQQ"
        ]
        .rolling(
            V16Q_ROLLING_WINDOW
        )
        .var()
    )

    V16Q_ROLLING_CORR = (
        V16Q_DAILY_RETURNS[
            "V16"
        ]
        .rolling(
            V16Q_ROLLING_WINDOW
        )
        .corr(
            V16Q_DAILY_RETURNS[
                "TQQQ"
            ]
        )
    )

    V16Q_ACTIVE_DAILY = (
        V16Q_DAILY_RETURNS[
            "V16"
        ]
        -
        V16Q_DAILY_RETURNS[
            "TQQQ"
        ]
    )

    V16Q_ROLLING_INFO_RATIO = (
        V16Q_ACTIVE_DAILY
        .rolling(
            V16Q_ROLLING_WINDOW
        )
        .mean()
        /
        V16Q_ACTIVE_DAILY
        .rolling(
            V16Q_ROLLING_WINDOW
        )
        .std()
        *
        np.sqrt(252)
    )

else:

    V16Q_ROLLING_BETA = pd.Series(dtype=float)
    V16Q_ROLLING_CORR = pd.Series(dtype=float)
    V16Q_ACTIVE_DAILY = pd.Series(dtype=float)
    V16Q_ROLLING_INFO_RATIO = pd.Series(dtype=float)


# ==============================================================================
# 20. RELATIVE WEALTH
# ==============================================================================

if (
    "V16" in V16Q_DAILY_CURVES.columns
    and
    "TQQQ" in V16Q_DAILY_CURVES.columns
):

    V16Q_RELATIVE_TQQQ = (
        V16Q_DAILY_CURVES[
            "V16"
        ]
        /
        V16Q_DAILY_CURVES[
            "TQQQ"
        ]
    )

else:

    V16Q_RELATIVE_TQQQ = pd.Series(
        dtype=float
    )

if (
    "V16" in V16Q_DAILY_CURVES.columns
    and
    "V8" in V16Q_DAILY_CURVES.columns
):

    V16Q_RELATIVE_V8 = (
        V16Q_DAILY_CURVES[
            "V16"
        ]
        /
        V16Q_DAILY_CURVES[
            "V8"
        ]
    )

else:

    V16Q_RELATIVE_V8 = pd.Series(
        dtype=float
    )


# ==============================================================================
# 21. DRAWDOWN EPISODES
# ==============================================================================

def v16q_drawdown_episodes(nav):

    nav = nav.dropna()

    if nav.empty:
        return pd.DataFrame()

    rows = []

    peak_value = 1.0

    peak_date = (
        nav.index[0]
        -
        pd.Timedelta(
            days=1
        )
    )

    in_dd = False

    for date, value in (
        nav.items()
    ):

        if value >= peak_value:

            if in_dd:

                rows.append(
                    {

                        "Peak_Date":
                            current_peak_date,

                        "Trough_Date":
                            trough_date,

                        "Recovery_Date":
                            date,

                        "Drawdown_Pct":
                            100.0
                            *
                            (
                                trough_value
                                /
                                current_peak_value
                                -
                                1.0
                            ),

                        "Peak_to_Trough_Days":
                            (
                                trough_date
                                -
                                current_peak_date
                            ).days,

                        "Recovery_Days":
                            (
                                date
                                -
                                current_peak_date
                            ).days,
                    }
                )

                in_dd = False

            peak_value = value
            peak_date = date

        else:

            if not in_dd:

                in_dd = True

                current_peak_value = (
                    peak_value
                )

                current_peak_date = (
                    peak_date
                )

                trough_value = value
                trough_date = date

            elif value < trough_value:

                trough_value = value
                trough_date = date

    if in_dd:

        rows.append(
            {

                "Peak_Date":
                    current_peak_date,

                "Trough_Date":
                    trough_date,

                "Recovery_Date":
                    pd.NaT,

                "Drawdown_Pct":
                    100.0
                    *
                    (
                        trough_value
                        /
                        current_peak_value
                        -
                        1.0
                    ),

                "Peak_to_Trough_Days":
                    (
                        trough_date
                        -
                        current_peak_date
                    ).days,

                "Recovery_Days":
                    np.nan,
            }
        )

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            "Drawdown_Pct"
        )
        .reset_index(
            drop=True
        )
    )


if "V16" in V16Q_DAILY_CURVES.columns:

    V16Q_DRAWDOWN_EPISODES = (
        v16q_drawdown_episodes(
            V16Q_DAILY_CURVES[
                "V16"
            ]
        )
    )

else:

    V16Q_DRAWDOWN_EPISODES = pd.DataFrame()


# ==============================================================================
# 22. BEST / WORST DAYS
# ==============================================================================

daily_compare_cols = [
    c
    for c in [
        "V16",
        "V8",
        "TQQQ",
        "QQQ",
    ]
    if c in V16Q_DAILY_RETURNS.columns
]

V16Q_DAILY_COMPARE = (
    V16Q_DAILY_RETURNS[
        daily_compare_cols
    ]
    .copy()
)

if (
    "V16" in V16Q_DAILY_COMPARE.columns
    and
    "TQQQ" in V16Q_DAILY_COMPARE.columns
):

    V16Q_DAILY_COMPARE[
        "V16_minus_TQQQ"
    ] = (
        V16Q_DAILY_COMPARE[
            "V16"
        ]
        -
        V16Q_DAILY_COMPARE[
            "TQQQ"
        ]
    )

if (
    "V16" in V16Q_DAILY_COMPARE.columns
    and
    "V8" in V16Q_DAILY_COMPARE.columns
):

    V16Q_DAILY_COMPARE[
        "V16_minus_V8"
    ] = (
        V16Q_DAILY_COMPARE[
            "V16"
        ]
        -
        V16Q_DAILY_COMPARE[
            "V8"
        ]
    )

if "V16" in V16Q_DAILY_COMPARE.columns:

    V16Q_BEST_DAYS = (
        100.0
        *
        V16Q_DAILY_COMPARE
        .nlargest(
            10,
            "V16"
        )
    )

    V16Q_WORST_DAYS = (
        100.0
        *
        V16Q_DAILY_COMPARE
        .nsmallest(
            10,
            "V16"
        )
    )

else:

    V16Q_BEST_DAYS = pd.DataFrame()
    V16Q_WORST_DAYS = pd.DataFrame()

if "V16_minus_TQQQ" in V16Q_DAILY_COMPARE.columns:

    V16Q_BEST_ACTIVE_DAYS = (
        100.0
        *
        V16Q_DAILY_COMPARE
        .nlargest(
            10,
            "V16_minus_TQQQ"
        )
    )

    V16Q_WORST_ACTIVE_DAYS = (
        100.0
        *
        V16Q_DAILY_COMPARE
        .nsmallest(
            10,
            "V16_minus_TQQQ"
        )
    )

else:

    V16Q_BEST_ACTIVE_DAYS = pd.DataFrame()
    V16Q_WORST_ACTIVE_DAYS = pd.DataFrame()


# ==============================================================================
# 23. DECISION AUDIT
# ==============================================================================

V16Q_DECISIONS = (
    V16Q_PATH[
        [
            c
            for c in [
                signal_col,
                exec_col,
                exit_col,
                lambda_col,
                turnover_col,
                tca_bps_col,
                net_ret_col,
                v8_ret_col,
                tqqq_ret_col,
                wealth_col,
            ]
            if c is not None
        ]
    ]
    .copy()
)

rename_map = {

    exec_col:
        "Execution_Date",

    exit_col:
        "Exit_Date",
}

if signal_col is not None:
    rename_map[
        signal_col
    ] = "Signal_Date"

if lambda_col is not None:
    rename_map[
        lambda_col
    ] = "Pre_Lambda"

if turnover_col is not None:
    rename_map[
        turnover_col
    ] = "Turnover"

if tca_bps_col is not None:
    rename_map[
        tca_bps_col
    ] = "TCA_bps"

if net_ret_col is not None:
    rename_map[
        net_ret_col
    ] = "V16_Return"

if v8_ret_col is not None:
    rename_map[
        v8_ret_col
    ] = "V8_Return"

if tqqq_ret_col is not None:
    rename_map[
        tqqq_ret_col
    ] = "TQQQ_Return"

if wealth_col is not None:
    rename_map[
        wealth_col
    ] = "V16_Wealth"

V16Q_DECISIONS = (
    V16Q_DECISIONS
    .rename(
        columns=
            rename_map
    )
)

if "V16_Return" in V16Q_DECISIONS.columns:

    V16Q_DECISIONS[
        "V16_Return_Pct"
    ] = [
        100.0
        *
        v16q_return_to_fraction(
            x,
            net_ret_col
        )
        for x in V16Q_DECISIONS[
            "V16_Return"
        ]
    ]

if "V8_Return" in V16Q_DECISIONS.columns:

    V16Q_DECISIONS[
        "V8_Return_Pct"
    ] = [
        100.0
        *
        v16q_return_to_fraction(
            x,
            v8_ret_col
        )
        for x in V16Q_DECISIONS[
            "V8_Return"
        ]
    ]

if "TQQQ_Return" in V16Q_DECISIONS.columns:

    V16Q_DECISIONS[
        "TQQQ_Return_Pct"
    ] = [
        100.0
        *
        v16q_return_to_fraction(
            x,
            tqqq_ret_col
        )
        for x in V16Q_DECISIONS[
            "TQQQ_Return"
        ]
    ]

if (
    "V16_Return_Pct"
    in V16Q_DECISIONS.columns
    and
    "V8_Return_Pct"
    in V16Q_DECISIONS.columns
):

    V16Q_DECISIONS[
        "V16_minus_V8_pp"
    ] = (
        V16Q_DECISIONS[
            "V16_Return_Pct"
        ]
        -
        V16Q_DECISIONS[
            "V8_Return_Pct"
        ]
    )

if (
    "V16_Return_Pct"
    in V16Q_DECISIONS.columns
    and
    "TQQQ_Return_Pct"
    in V16Q_DECISIONS.columns
):

    V16Q_DECISIONS[
        "V16_minus_TQQQ_pp"
    ] = (
        V16Q_DECISIONS[
            "V16_Return_Pct"
        ]
        -
        V16Q_DECISIONS[
            "TQQQ_Return_Pct"
        ]
    )

if (
    "TCA_bps"
    not in V16Q_DECISIONS.columns
):

    V16Q_DECISIONS[
        "TCA_bps"
    ] = [
        10000.0
        *
        v16q_event_cost_fraction(
            row
        )
        for _, row in V16Q_PATH.iterrows()
    ]


# ==============================================================================
# 24. ATTRIBUTION / TURNOVER / TCA
# ==============================================================================

if V16Q_ATTRIBUTION_ROWS:

    V16Q_ATTRIBUTION_DETAIL = (
        pd.DataFrame(
            V16Q_ATTRIBUTION_ROWS
        )
    )

    V16Q_ASSET_ATTRIBUTION = (
        V16Q_ATTRIBUTION_DETAIL
        .groupby(
            "Ticker"
        )
        .agg(
            Exact_Wealth_Contribution=
                (
                    "Exact_Wealth_Contribution",
                    "sum"
                ),

            Mean_Target_Weight=
                (
                    "Target_Weight",
                    "mean"
                ),

            Decisions_Held=
                (
                    "Execution_Date",
                    "nunique"
                ),
        )
        .sort_values(
            "Exact_Wealth_Contribution",
            ascending=False
        )
    )

    V16Q_ASSET_ATTRIBUTION[
        "Exact_Wealth_Contribution_PctInitial"
    ] = (
        100.0
        *
        V16Q_ASSET_ATTRIBUTION[
            "Exact_Wealth_Contribution"
        ]
    )

    V16Q_BUCKET_ATTRIBUTION = (
        V16Q_ATTRIBUTION_DETAIL
        .groupby(
            "Bucket"
        )
        .agg(
            Exact_Wealth_Contribution=
                (
                    "Exact_Wealth_Contribution",
                    "sum"
                )
        )
    )

    V16Q_BUCKET_ATTRIBUTION[
        "Pct_of_Initial"
    ] = (
        100.0
        *
        V16Q_BUCKET_ATTRIBUTION[
            "Exact_Wealth_Contribution"
        ]
    )

else:

    V16Q_ATTRIBUTION_DETAIL = pd.DataFrame()
    V16Q_ASSET_ATTRIBUTION = pd.DataFrame()
    V16Q_BUCKET_ATTRIBUTION = pd.DataFrame()


if V16Q_COST_ROWS:

    V16Q_COST = (
        pd.DataFrame(
            V16Q_COST_ROWS
        )
    )

    V16Q_COST[
        "Year"
    ] = (
        V16Q_COST[
            "Execution_Date"
        ]
        .dt.year
    )

    V16Q_YEARLY_COST = (
        V16Q_COST
        .groupby(
            "Year"
        )
        .agg(
            Turnover=
                (
                    "Turnover",
                    "sum"
                ),

            TCA_bps=
                (
                    "TCA_bps",
                    "sum"
                ),

            Exact_TCA_Wealth_Contribution=
                (
                    "Exact_TCA_Wealth_Contribution",
                    "sum"
                ),
        )
    )

    V16Q_TOTAL_TCA_CONTRIBUTION = float(
        V16Q_COST[
            "Exact_TCA_Wealth_Contribution"
        ]
        .sum()
    )

else:

    V16Q_COST = pd.DataFrame()
    V16Q_YEARLY_COST = pd.DataFrame()
    V16Q_TOTAL_TCA_CONTRIBUTION = np.nan


if not V16Q_ATTRIBUTION_DETAIL.empty:

    V16Q_TOTAL_ASSET_CONTRIBUTION = float(
        V16Q_ATTRIBUTION_DETAIL[
            "Exact_Wealth_Contribution"
        ]
        .sum()
    )

    V16Q_ATTRIBUTION_RECONSTRUCTED_FINAL = (
        1.0
        +
        V16Q_TOTAL_ASSET_CONTRIBUTION
        +
        V16Q_TOTAL_TCA_CONTRIBUTION
        +
        (
            V16Q_TERMINAL_REBALANCE_CONTRIBUTION
            if np.isfinite(
                V16Q_TERMINAL_REBALANCE_CONTRIBUTION
            )
            else 0.0
        )
    )

    V16Q_ATTRIBUTION_ERROR = (
        V16Q_ATTRIBUTION_RECONSTRUCTED_FINAL
        -
        V16Q_FINAL_WEALTH
    )

else:

    V16Q_TOTAL_ASSET_CONTRIBUTION = np.nan
    V16Q_ATTRIBUTION_RECONSTRUCTED_FINAL = np.nan
    V16Q_ATTRIBUTION_ERROR = np.nan


# ==============================================================================
# 25. FIND V8 TARGET MATRIX FOR TRUE RESIDUAL-TILT COMPARISON
# ==============================================================================

V16Q_V8_WEIGHT_MATRIX = None
V16Q_V8_TARGET_SOURCE = None

if (
    "V8Q_WEIGHT_MATRIX"
    in globals()
    and
    isinstance(
        V8Q_WEIGHT_MATRIX,
        pd.DataFrame
    )
):

    V16Q_V8_WEIGHT_MATRIX = (
        V8Q_WEIGHT_MATRIX
        .copy()
    )

    V16Q_V8_WEIGHT_MATRIX.index = (
        v16q_normalize_date_index(
            V16Q_V8_WEIGHT_MATRIX.index
        )
    )

    V16Q_V8_TARGET_SOURCE = (
        "V8Q_WEIGHT_MATRIX"
    )

else:

    possible_v8_names = [

        "V8_TARGET_MATRIX",
        "V8_WEIGHT_MATRIX",
        "V8_TARGETS",
        "V8_EVENT_TARGETS",
        "V8_TARGET_WEIGHTS",
    ]

    for name in possible_v8_names:

        if name not in globals():
            continue

        temp = (
            v16q_coerce_target_matrix(
                globals()[name],
                prefix="V8"
            )
        )

        temp = (
            v16q_standardize_weight_matrix(
                temp
            )
        )

        if temp is not None:

            V16Q_V8_WEIGHT_MATRIX = temp
            V16Q_V8_TARGET_SOURCE = name
            break


# ==============================================================================
# 26. RESIDUAL-TILT WEIGHT DIFFERENCE / CONTRIBUTION
# ==============================================================================

V16Q_RESIDUAL_EVENT = pd.DataFrame()
V16Q_RESIDUAL_TICKER = pd.DataFrame()

if (
    V16Q_WEIGHT_MATRIX is not None
    and
    V16Q_V8_WEIGHT_MATRIX is not None
):

    residual_rows = []
    residual_ticker_rows = []

    for i, row in (
        V16Q_PATH.iterrows()
    ):

        d = pd.Timestamp(
            row[
                exec_col
            ]
        )

        exit_d = pd.Timestamp(
            row[
                exit_col
            ]
        )

        if (
            d not in V16Q_WEIGHT_MATRIX.index
            or
            d not in V16Q_V8_WEIGHT_MATRIX.index
        ):
            continue

        union = sorted(
            set(
                V16Q_WEIGHT_MATRIX.columns
            )
            |
            set(
                V16Q_V8_WEIGHT_MATRIX.columns
            )
        )

        w16 = (
            V16Q_WEIGHT_MATRIX
            .reindex(
                columns=union,
                fill_value=0.0
            )
            .loc[
                d
            ]
        )

        w8 = (
            V16Q_V8_WEIGHT_MATRIX
            .reindex(
                columns=union,
                fill_value=0.0
            )
            .loc[
                d
            ]
        )

        delta = (
            w16
            -
            w8
        )

        active_assets = (
            delta[
                delta.abs()
                >
                1e-14
            ]
            .index
        )

        delta_l1 = float(
            delta.abs()
            .sum()
        )

        return_effect = np.nan

        if len(
            active_assets
        ):

            entry = (
                V16Q_PRICE_WIDE
                .reindex(
                    index=[
                        d
                    ],
                    columns=
                        active_assets
                )
                .iloc[
                    0
                ]
            )

            exit_price = (
                V16Q_PRICE_WIDE
                .reindex(
                    index=[
                        exit_d
                    ],
                    columns=
                        active_assets
                )
                .iloc[
                    0
                ]
            )

            valid = (
                np.isfinite(
                    entry
                )
                &
                np.isfinite(
                    exit_price
                )
                &
                (
                    entry > 0
                )
                &
                (
                    exit_price > 0
                )
            )

            if valid.any():

                ar = (
                    exit_price[
                        valid
                    ]
                    /
                    entry[
                        valid
                    ]
                    -
                    1.0
                )

                return_effect = float(
                    (
                        delta[
                            valid.index[
                                valid
                            ]
                        ]
                        *
                        ar
                    )
                    .sum()
                )

                for ticker in ar.index:

                    residual_ticker_rows.append(
                        {

                            "Execution_Date":
                                d,

                            "Exit_Date":
                                exit_d,

                            "Ticker":
                                ticker,

                            "V16_Weight":
                                float(
                                    w16[
                                        ticker
                                    ]
                                ),

                            "V8_Weight":
                                float(
                                    w8[
                                        ticker
                                    ]
                                ),

                            "Delta_Weight":
                                float(
                                    delta[
                                        ticker
                                    ]
                                ),

                            "Asset_Return":
                                float(
                                    ar[
                                        ticker
                                    ]
                                ),

                            "Delta_Weight_x_Return":
                                float(
                                    delta[
                                        ticker
                                    ]
                                    *
                                    ar[
                                        ticker
                                    ]
                                ),
                        }
                    )

        residual_rows.append(
            {

                "Execution_Date":
                    d,

                "Exit_Date":
                    exit_d,

                "Residual_Tilt_L1":
                    delta_l1,

                "Residual_Tilt_OneWay":
                    0.5
                    *
                    delta_l1,

                "Residual_Tilt_Return_Effect_Pct":
                    (
                        100.0
                        *
                        return_effect
                        if np.isfinite(
                            return_effect
                        )
                        else np.nan
                    ),

                "Pre_Lambda":
                    (
                        float(
                            row[
                                lambda_col
                            ]
                        )
                        if (
                            lambda_col is not None
                            and pd.notna(
                                row[
                                    lambda_col
                                ]
                            )
                        )
                        else np.nan
                    ),
            }
        )

    V16Q_RESIDUAL_EVENT = (
        pd.DataFrame(
            residual_rows
        )
    )

    if residual_ticker_rows:

        V16Q_RESIDUAL_TICKER_DETAIL = (
            pd.DataFrame(
                residual_ticker_rows
            )
        )

        V16Q_RESIDUAL_TICKER = (
            V16Q_RESIDUAL_TICKER_DETAIL
            .groupby(
                "Ticker"
            )
            .agg(
                Sum_DeltaWeight_x_Return=
                    (
                        "Delta_Weight_x_Return",
                        "sum"
                    ),

                Mean_Delta_Weight=
                    (
                        "Delta_Weight",
                        "mean"
                    ),

                Max_Overweight=
                    (
                        "Delta_Weight",
                        "max"
                    ),

                Max_Underweight=
                    (
                        "Delta_Weight",
                        "min"
                    ),

                Events=
                    (
                        "Execution_Date",
                        "nunique"
                    ),
            )
            .sort_values(
                "Sum_DeltaWeight_x_Return",
                ascending=False
            )
        )

    print(
        f"\n[+] V8 historical target comparator: "
        f"{V16Q_V8_TARGET_SOURCE}"
    )

else:

    print(
        "\n[i] Historical V8 per-security target matrix not found."
    )

    print(
        "[i] V16-vs-V8 event returns remain available, "
        "but exact weight-delta decomposition is skipped."
    )


# ==============================================================================
# 27. MONTHLY HEATMAP MATRICES
# ==============================================================================

if "V16" in V16Q_MONTHLY_RETURNS_PCT.columns:

    v16_monthly = (
        V16Q_MONTHLY_RETURNS_PCT[
            "V16"
        ]
        .dropna()
        .to_frame(
            "Return"
        )
    )

    v16_monthly[
        "Year"
    ] = (
        v16_monthly.index.year
    )

    v16_monthly[
        "Month"
    ] = (
        v16_monthly.index.month
    )

    V16Q_MONTH_HEATMAP = (
        v16_monthly
        .pivot(
            index=
                "Year",

            columns=
                "Month",

            values=
                "Return"
        )
        .reindex(
            columns=
                range(
                    1,
                    13
                )
        )
    )

else:

    V16Q_MONTH_HEATMAP = pd.DataFrame()


if (
    "V16" in V16Q_MONTHLY_RETURNS_PCT.columns
    and
    "TQQQ" in V16Q_MONTHLY_RETURNS_PCT.columns
):

    active_monthly = (
        (
            V16Q_MONTHLY_RETURNS_PCT[
                "V16"
            ]
            -
            V16Q_MONTHLY_RETURNS_PCT[
                "TQQQ"
            ]
        )
        .dropna()
        .to_frame(
            "Return"
        )
    )

    active_monthly[
        "Year"
    ] = (
        active_monthly.index.year
    )

    active_monthly[
        "Month"
    ] = (
        active_monthly.index.month
    )

    V16Q_ACTIVE_HEATMAP = (
        active_monthly
        .pivot(
            index=
                "Year",

            columns=
                "Month",

            values=
                "Return"
        )
        .reindex(
            columns=
                range(
                    1,
                    13
                )
        )
    )

else:

    V16Q_ACTIVE_HEATMAP = pd.DataFrame()


# ==============================================================================
# 28. CORE TABLES — SAME DEPTH AS OLD V8 DASHBOARD
# ==============================================================================

v16q_show(
    "1) EXACT DAILY / EVENT NAV VALIDATION",
    (
        V16Q_VALIDATION
        .tail(10)
        if not V16Q_VALIDATION.empty
        else pd.DataFrame(
            {
                "Status":
                    [
                        "Historical target matrix unavailable"
                    ]
            }
        )
    ),
    10
)

v16q_show(
    "2) INSTITUTIONAL PERFORMANCE / RISK TABLE",
    V16Q_PERFORMANCE_TABLE,
    4
)

v16q_show(
    "3) 1M / 3M / 6M / 12M HORIZON AUDIT",
    V16Q_HORIZON_TABLE,
    4
)

v16q_show(
    "4) MONTHLY STATISTICS",
    V16Q_MONTHLY_STATS,
    4
)

v16q_show(
    "5) MONTHLY RETURNS (%)",
    V16Q_MONTHLY_RETURNS_PCT,
    2
)

v16q_show(
    "6) YEAR-BY-YEAR RETURNS (%)",
    V16Q_YEARLY_RETURNS_PCT,
    2
)

v16q_show(
    "7) FIVE WORST V16 DRAWDOWN EPISODES",
    (
        V16Q_DRAWDOWN_EPISODES
        .head(5)
        if not V16Q_DRAWDOWN_EPISODES.empty
        else V16Q_DRAWDOWN_EPISODES
    ),
    3
)

v16q_show(
    "8) TEN BEST V16 DAYS (%)",
    V16Q_BEST_DAYS,
    3
)

v16q_show(
    "9) TEN WORST V16 DAYS (%)",
    V16Q_WORST_DAYS,
    3
)

v16q_show(
    "10) TEN BEST ACTIVE DAYS vs TQQQ (%)",
    V16Q_BEST_ACTIVE_DAYS,
    3
)

v16q_show(
    "11) TEN WORST ACTIVE DAYS vs TQQQ (%)",
    V16Q_WORST_ACTIVE_DAYS,
    3
)

v16q_show(
    "12) FULL V16 DECISION AUDIT",
    V16Q_DECISIONS,
    4
)

v16q_show(
    "13) CONCENTRATION",
    (
        V16Q_CONCENTRATION
        .describe()
        if not V16Q_CONCENTRATION.empty
        else V16Q_CONCENTRATION
    ),
    4
)

v16q_show(
    "14) YEARLY TURNOVER / TCA",
    V16Q_YEARLY_COST,
    5
)

v16q_show(
    "15) TQQQ CORE vs STOCK SLEEVE — EXACT WEALTH CONTRIBUTION",
    V16Q_BUCKET_ATTRIBUTION,
    6
)

v16q_show(
    "16) TOP 20 POSITIVE ASSET CONTRIBUTORS",
    (
        V16Q_ASSET_ATTRIBUTION
        .head(20)
        if not V16Q_ASSET_ATTRIBUTION.empty
        else V16Q_ASSET_ATTRIBUTION
    ),
    6
)

v16q_show(
    "17) TOP 20 NEGATIVE ASSET CONTRIBUTORS",
    (
        V16Q_ASSET_ATTRIBUTION
        .sort_values(
            "Exact_Wealth_Contribution"
        )
        .head(20)
        if not V16Q_ASSET_ATTRIBUTION.empty
        else V16Q_ASSET_ATTRIBUTION
    ),
    6
)

v16q_show(
    "18) V16 RESIDUAL-TILT EVENT AUDIT",
    V16Q_RESIDUAL_EVENT,
    6
)

v16q_show(
    "19) RESIDUAL-TILT TICKER ATTRIBUTION",
    (
        V16Q_RESIDUAL_TICKER
        .head(25)
        if not V16Q_RESIDUAL_TICKER.empty
        else V16Q_RESIDUAL_TICKER
    ),
    6
)


# ==============================================================================
# 29. GRAPH 1 — EXACT DAILY CUMULATIVE NET RETURN
# ==============================================================================

plt.figure(
    figsize=(
        18,
        8
    )
)

for strategy in (
    V16Q_DAILY_CURVES.columns
):

    plt.plot(
        V16Q_DAILY_CURVES.index,
        100.0
        *
        (
            V16Q_DAILY_CURVES[
                strategy
            ]
            -
            1.0
        ),
        linewidth=(
            2.8
            if strategy == "V16"
            else 1.5
        ),
        label=
            strategy
    )

plt.axhline(
    0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "V16 — EXACT DAILY CUMULATIVE NET RETURN",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Cumulative Net Return (%)"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 30. GRAPH 2 — DAILY RETURNS
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

for strategy in [
    c
    for c in [
        "V16",
        "V8",
        "TQQQ"
    ]
    if c in V16Q_DAILY_RETURNS.columns
]:

    plt.plot(
        V16Q_DAILY_RETURNS.index,
        100.0
        *
        V16Q_DAILY_RETURNS[
            strategy
        ],
        linewidth=(
            1.2
            if strategy == "V16"
            else 0.8
        ),
        alpha=(
            1.0
            if strategy == "V16"
            else 0.65
        ),
        label=
            strategy
    )

plt.axhline(
    0,
    linewidth=1
)

plt.title(
    "V16 vs V8 vs TQQQ — DAILY RETURNS",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Daily Return (%)"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 31. GRAPH 3 — MONTHLY RETURN BARS
# ==============================================================================

plot_cols = [
    c
    for c in [
        "V16",
        "V8",
        "TQQQ",
        "QQQ"
    ]
    if c in V16Q_MONTHLY_RETURNS_PCT.columns
]

monthly_plot = (
    V16Q_MONTHLY_RETURNS_PCT[
        plot_cols
    ]
    .dropna(
        how="all"
    )
)

x = np.arange(
    len(
        monthly_plot
    )
)

n_cols = max(
    len(
        plot_cols
    ),
    1
)

width = (
    0.8
    /
    n_cols
)

plt.figure(
    figsize=(
        20,
        8
    )
)

for j, strategy in enumerate(
    plot_cols
):

    offset = (
        j
        -
        (
            n_cols
            -
            1
        )
        /
        2
    ) * width

    plt.bar(
        x
        +
        offset,
        monthly_plot[
            strategy
        ],
        width=
            width,
        label=
            strategy
    )

plt.axhline(
    0,
    linewidth=1
)

plt.xticks(
    x,
    [
        date.strftime(
            "%Y-%m"
        )
        for date in (
            monthly_plot.index
        )
    ],
    rotation=90
)

plt.title(
    "V16 vs V8 vs TQQQ vs QQQ — MONTHLY RETURNS",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Monthly Return (%)"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 32. GRAPH 4 — DAILY DRAWDOWN
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

for strategy in [
    c
    for c in [
        "V16",
        "V8",
        "TQQQ",
        "QQQ"
    ]
    if c in V16Q_DRAWDOWN.columns
]:

    plt.plot(
        V16Q_DRAWDOWN.index,
        100.0
        *
        V16Q_DRAWDOWN[
            strategy
        ],
        linewidth=(
            2.5
            if strategy == "V16"
            else 1.5
        ),
        label=
            strategy
    )

plt.axhline(
    0,
    linewidth=1
)

plt.title(
    "V16 — DAILY UNDERWATER / DRAWDOWN",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Drawdown (%)"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 33. GRAPH 5 — RELATIVE WEALTH
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

if not V16Q_RELATIVE_TQQQ.empty:

    plt.plot(
        V16Q_RELATIVE_TQQQ.index,
        V16Q_RELATIVE_TQQQ,
        linewidth=2.5,
        label=
            "V16 / TQQQ"
    )

if not V16Q_RELATIVE_V8.empty:

    plt.plot(
        V16Q_RELATIVE_V8.index,
        V16Q_RELATIVE_V8,
        linewidth=2.2,
        label=
            "V16 / V8"
    )

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "V16 — RELATIVE WEALTH",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Relative Wealth"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 34. GRAPH 6 — ROLLING EXCESS 1M/3M/6M/12M
# ==============================================================================

plt.figure(
    figsize=(
        18,
        8
    )
)

for label in [
    "1M",
    "3M",
    "6M",
    "12M",
]:

    if label not in V16Q_ROLLING_RETURNS:
        continue

    rolling = (
        V16Q_ROLLING_RETURNS[
            label
        ]
    )

    plt.plot(
        rolling.index,
        100.0
        *
        rolling[
            "V16_minus_TQQQ"
        ],
        linewidth=1.8,
        label=
            label
    )

plt.axhline(
    0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "V16 — ROLLING EXCESS RETURN vs TQQQ — 1M / 3M / 6M / 12M",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "V16 - TQQQ Return (pp)"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 35. GRAPH 7 — 63-DAY VOLATILITY
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

for strategy in (
    V16Q_ROLLING_VOL.columns
):

    plt.plot(
        V16Q_ROLLING_VOL.index,
        V16Q_ROLLING_VOL[
            strategy
        ],
        linewidth=(
            2.4
            if strategy == "V16"
            else 1.5
        ),
        label=
            strategy
    )

plt.title(
    "63-DAY ROLLING ANNUALIZED VOLATILITY",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Annualized Volatility (%)"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 36. GRAPH 8 — 63-DAY SHARPE
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

for strategy in (
    V16Q_ROLLING_SHARPE.columns
):

    plt.plot(
        V16Q_ROLLING_SHARPE.index,
        V16Q_ROLLING_SHARPE[
            strategy
        ],
        linewidth=(
            2.4
            if strategy == "V16"
            else 1.5
        ),
        label=
            strategy
    )

plt.axhline(
    0,
    linewidth=1
)

plt.title(
    "63-DAY ROLLING SHARPE — RF = 0",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Rolling Sharpe"
)

plt.xlabel(
    "Date"
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 37. GRAPH 9 — ROLLING BETA
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

plt.plot(
    V16Q_ROLLING_BETA.index,
    V16Q_ROLLING_BETA,
    linewidth=2.4
)

plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1
)

plt.axhline(
    0.0,
    linewidth=1
)

plt.title(
    "V16 — 63-DAY ROLLING BETA vs TQQQ",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Beta"
)

plt.xlabel(
    "Date"
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 38. GRAPH 10 — ROLLING CORRELATION
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

plt.plot(
    V16Q_ROLLING_CORR.index,
    V16Q_ROLLING_CORR,
    linewidth=2.4
)

plt.axhline(
    0,
    linewidth=1
)

plt.ylim(
    -1.05,
    1.05
)

plt.title(
    "V16 — 63-DAY ROLLING CORRELATION vs TQQQ",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Correlation"
)

plt.xlabel(
    "Date"
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 39. GRAPH 11 — ROLLING INFORMATION RATIO
# ==============================================================================

plt.figure(
    figsize=(
        18,
        7
    )
)

plt.plot(
    V16Q_ROLLING_INFO_RATIO.index,
    V16Q_ROLLING_INFO_RATIO,
    linewidth=2.3
)

plt.axhline(
    0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "V16 — 63-DAY ROLLING INFORMATION RATIO vs TQQQ",
    fontsize=15,
    fontweight="bold"
)

plt.ylabel(
    "Information Ratio"
)

plt.xlabel(
    "Date"
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.25
)

plt.tight_layout()
plt.show()


# ==============================================================================
# 40. GRAPH 12 — CAUSAL RESIDUAL-TILT LAMBDA
# ==============================================================================

if "Pre_Lambda" in V16Q_DECISIONS.columns:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.plot(
        V16Q_DECISIONS[
            "Execution_Date"
        ],
        100.0
        *
        V16Q_DECISIONS[
            "Pre_Lambda"
        ],
        marker="o",
        linewidth=2.4,
        label=
            "Pre-event universal residual λ"
    )

    plt.axhline(
        50.0,
        linestyle="--",
        linewidth=1
    )

    plt.title(
        "V16 — CAUSAL UNIVERSAL RESIDUAL-MOMENTUM TILT λ",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Residual Tilt λ (%)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.legend()

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 41. GRAPH 13 — V16 EXCESS vs V8 BY DECISION
# ==============================================================================

if "V16_minus_V8_pp" in V16Q_DECISIONS.columns:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.bar(
        V16Q_DECISIONS[
            "Execution_Date"
        ],
        V16Q_DECISIONS[
            "V16_minus_V8_pp"
        ],
        width=12
    )

    plt.axhline(
        0,
        linewidth=1
    )

    plt.title(
        "V16 — REALIZED NET EXCESS vs FROZEN V8 BY DECISION",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "V16 - V8 Return (pp)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 42. GRAPH 14 — V16 ACTIVE RETURN vs TQQQ
# ==============================================================================

if "V16_minus_TQQQ_pp" in V16Q_DECISIONS.columns:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.bar(
        V16Q_DECISIONS[
            "Execution_Date"
        ],
        V16Q_DECISIONS[
            "V16_minus_TQQQ_pp"
        ],
        width=12
    )

    plt.axhline(
        0,
        linewidth=1
    )

    plt.title(
        "V16 — REALIZED NET ACTIVE RETURN vs TQQQ BY DECISION",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "V16 - TQQQ Return (pp)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 43. GRAPH 15 — TURNOVER
# ==============================================================================

if "Turnover" in V16Q_DECISIONS.columns:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.bar(
        V16Q_DECISIONS[
            "Execution_Date"
        ],
        V16Q_DECISIONS[
            "Turnover"
        ],
        width=12
    )

    plt.title(
        "V16 — TURNOVER BY PORTFOLIO DECISION",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "L1 Turnover"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 44. GRAPH 16 — EFFECTIVE N
# ==============================================================================

if not V16Q_CONCENTRATION.empty:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.plot(
        V16Q_CONCENTRATION.index,
        V16Q_CONCENTRATION[
            "Effective_N"
        ],
        marker="o",
        linewidth=2.3
    )

    plt.title(
        "V16 — EFFECTIVE NUMBER OF HOLDINGS",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Effective N = 1 / Σw²"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 45. GRAPH 17 — TQQQ CORE + MAX POSITION
# ==============================================================================

if not V16Q_CONCENTRATION.empty:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.plot(
        V16Q_CONCENTRATION.index,
        V16Q_CONCENTRATION[
            "TQQQ_Weight_Pct"
        ],
        marker="o",
        linewidth=2.3,
        label=
            "TQQQ Core Weight"
    )

    plt.plot(
        V16Q_CONCENTRATION.index,
        V16Q_CONCENTRATION[
            "Max_Name_Weight_Pct"
        ],
        marker="o",
        linewidth=1.8,
        label=
            "Largest Position"
    )

    plt.title(
        "V16 — TQQQ CORE AND PORTFOLIO CONCENTRATION",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Weight (%)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.legend()

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 46. GRAPH 18 — MONTHLY RETURN HEATMAP
# ==============================================================================

if not V16Q_MONTH_HEATMAP.empty:

    heat = (
        V16Q_MONTH_HEATMAP
        .to_numpy(
            dtype=float
        )
    )

    limit = float(
        np.nanmax(
            np.abs(
                heat
            )
        )
    )

    fig, ax = plt.subplots(
        figsize=(
            14,
            5
        )
    )

    image = ax.imshow(
        heat,
        aspect="auto",
        cmap="coolwarm",
        vmin=
            -limit,
        vmax=
            limit
    )

    ax.set_title(
        "V16 — MONTHLY RETURN HEATMAP (%)",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xticks(
        np.arange(12)
    )

    ax.set_xticklabels(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    )

    ax.set_yticks(
        np.arange(
            len(
                V16Q_MONTH_HEATMAP.index
            )
        )
    )

    ax.set_yticklabels(
        V16Q_MONTH_HEATMAP.index
    )

    for i in range(
        heat.shape[0]
    ):

        for j in range(
            heat.shape[1]
        ):

            value = heat[
                i,
                j
            ]

            if np.isfinite(
                value
            ):

                ax.text(
                    j,
                    i,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=9
                )

    fig.colorbar(
        image,
        ax=ax,
        label=
            "Monthly Return (%)"
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 47. GRAPH 19 — MONTHLY ACTIVE RETURN HEATMAP
# ==============================================================================

if not V16Q_ACTIVE_HEATMAP.empty:

    heat = (
        V16Q_ACTIVE_HEATMAP
        .to_numpy(
            dtype=float
        )
    )

    limit = float(
        np.nanmax(
            np.abs(
                heat
            )
        )
    )

    fig, ax = plt.subplots(
        figsize=(
            14,
            5
        )
    )

    image = ax.imshow(
        heat,
        aspect="auto",
        cmap="coolwarm",
        vmin=
            -limit,
        vmax=
            limit
    )

    ax.set_title(
        "V16 MINUS TQQQ — MONTHLY ACTIVE RETURN (%)",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xticks(
        np.arange(12)
    )

    ax.set_xticklabels(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    )

    ax.set_yticks(
        np.arange(
            len(
                V16Q_ACTIVE_HEATMAP.index
            )
        )
    )

    ax.set_yticklabels(
        V16Q_ACTIVE_HEATMAP.index
    )

    for i in range(
        heat.shape[0]
    ):

        for j in range(
            heat.shape[1]
        ):

            value = heat[
                i,
                j
            ]

            if np.isfinite(
                value
            ):

                ax.text(
                    j,
                    i,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=9
                )

    fig.colorbar(
        image,
        ax=ax,
        label=
            "V16 - TQQQ Return (pp)"
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 48. GRAPH 20 — DAILY RETURN DISTRIBUTION
# ==============================================================================

if "V16" in V16Q_DAILY_RETURNS.columns:

    plt.figure(
        figsize=(
            13,
            7
        )
    )

    plt.hist(
        100.0
        *
        V16Q_DAILY_RETURNS[
            "V16"
        ]
        .dropna(),
        bins=50,
        alpha=0.55,
        density=True,
        label=
            "V16"
    )

    if "TQQQ" in V16Q_DAILY_RETURNS.columns:

        plt.hist(
            100.0
            *
            V16Q_DAILY_RETURNS[
                "TQQQ"
            ]
            .dropna(),
            bins=50,
            alpha=0.40,
            density=True,
            label=
                "TQQQ"
        )

    if "V8" in V16Q_DAILY_RETURNS.columns:

        plt.hist(
            100.0
            *
            V16Q_DAILY_RETURNS[
                "V8"
            ]
            .dropna(),
            bins=50,
            alpha=0.30,
            density=True,
            label=
                "V8"
        )

    plt.axvline(
        0,
        linewidth=1
    )

    plt.title(
        "V16 vs V8 vs TQQQ — DAILY RETURN DISTRIBUTION",
        fontsize=15,
        fontweight="bold"
    )

    plt.xlabel(
        "Daily Return (%)"
    )

    plt.ylabel(
        "Density"
    )

    plt.legend()

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 49. GRAPH 21 — TOP POSITIVE EXACT WEALTH CONTRIBUTORS
# ==============================================================================

if not V16Q_ASSET_ATTRIBUTION.empty:

    positive = (
        V16Q_ASSET_ATTRIBUTION
        .head(15)
        .sort_values(
            "Exact_Wealth_Contribution_PctInitial"
        )
    )

    plt.figure(
        figsize=(
            12,
            8
        )
    )

    plt.barh(
        positive.index,
        positive[
            "Exact_Wealth_Contribution_PctInitial"
        ]
    )

    plt.title(
        "V16 — TOP POSITIVE EXACT WEALTH CONTRIBUTORS",
        fontsize=15,
        fontweight="bold"
    )

    plt.xlabel(
        "Contribution (% of Initial Capital)"
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 50. GRAPH 22 — TOP NEGATIVE EXACT WEALTH CONTRIBUTORS
# ==============================================================================

if not V16Q_ASSET_ATTRIBUTION.empty:

    negative = (
        V16Q_ASSET_ATTRIBUTION
        .sort_values(
            "Exact_Wealth_Contribution"
        )
        .head(15)
        .sort_values(
            "Exact_Wealth_Contribution_PctInitial",
            ascending=False
        )
    )

    plt.figure(
        figsize=(
            12,
            8
        )
    )

    plt.barh(
        negative.index,
        negative[
            "Exact_Wealth_Contribution_PctInitial"
        ]
    )

    plt.title(
        "V16 — TOP NEGATIVE EXACT WEALTH CONTRIBUTORS",
        fontsize=15,
        fontweight="bold"
    )

    plt.xlabel(
        "Contribution (% of Initial Capital)"
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 51. GRAPH 23 — CORE vs STOCK-SLEEVE CONTRIBUTION
# ==============================================================================

if not V16Q_BUCKET_ATTRIBUTION.empty:

    plt.figure(
        figsize=(
            9,
            6
        )
    )

    plt.bar(
        V16Q_BUCKET_ATTRIBUTION.index,
        V16Q_BUCKET_ATTRIBUTION[
            "Pct_of_Initial"
        ]
    )

    plt.axhline(
        0,
        linewidth=1
    )

    plt.title(
        "V16 — TQQQ CORE vs STOCK SLEEVE EXACT WEALTH CONTRIBUTION",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Contribution (% of Initial Capital)"
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 52. EXTRA GRAPH 24 — EVENT WEALTH V16 / V8 / TQQQ
# ==============================================================================

event_plot = pd.DataFrame(
    {
        "Execution_Date":
            V16Q_DECISIONS[
                "Execution_Date"
            ]
    }
)

if "V16_Wealth" in V16Q_DECISIONS.columns:

    event_plot[
        "V16"
    ] = (
        V16Q_DECISIONS[
            "V16_Wealth"
        ]
        .astype(float)
    )

if "V8_Return_Pct" in V16Q_DECISIONS.columns:

    event_plot[
        "V8"
    ] = (
        1.0
        +
        V16Q_DECISIONS[
            "V8_Return_Pct"
        ]
        /
        100.0
    ).cumprod()

if "TQQQ_Return_Pct" in V16Q_DECISIONS.columns:

    event_plot[
        "TQQQ"
    ] = (
        1.0
        +
        V16Q_DECISIONS[
            "TQQQ_Return_Pct"
        ]
        /
        100.0
    ).cumprod()

if event_plot.shape[1] > 1:

    plt.figure(
        figsize=(
            18,
            8
        )
    )

    for c in [
        x
        for x in [
            "V16",
            "V8",
            "TQQQ"
        ]
        if x in event_plot.columns
    ]:

        plt.plot(
            event_plot[
                "Execution_Date"
            ],
            event_plot[
                c
            ],
            marker="o",
            linewidth=(
                2.7
                if c == "V16"
                else 1.8
            ),
            label=
                c
        )

    plt.axhline(
        1.0,
        linestyle="--",
        linewidth=1
    )

    plt.title(
        "V16 vs V8 vs TQQQ — EXACT EVENT-LEVEL NET WEALTH",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Wealth Multiple"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.legend()

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 53. EXTRA GRAPH 25 — RESIDUAL-TILT DISTANCE FROM V8
# ==============================================================================

if not V16Q_RESIDUAL_EVENT.empty:

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.plot(
        V16Q_RESIDUAL_EVENT[
            "Execution_Date"
        ],
        100.0
        *
        V16Q_RESIDUAL_EVENT[
            "Residual_Tilt_OneWay"
        ],
        marker="o",
        linewidth=2.3
    )

    plt.title(
        "V16 — RESIDUAL-MOMENTUM COMPOSITION TILT AWAY FROM V8",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "One-way Weight Reallocation (%)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 54. EXTRA GRAPH 26 — RESIDUAL TILT RETURN EFFECT
# ==============================================================================

if (
    not V16Q_RESIDUAL_EVENT.empty
    and
    "Residual_Tilt_Return_Effect_Pct"
    in V16Q_RESIDUAL_EVENT.columns
):

    plt.figure(
        figsize=(
            18,
            7
        )
    )

    plt.bar(
        V16Q_RESIDUAL_EVENT[
            "Execution_Date"
        ],
        V16Q_RESIDUAL_EVENT[
            "Residual_Tilt_Return_Effect_Pct"
        ],
        width=12
    )

    plt.axhline(
        0,
        linewidth=1
    )

    plt.title(
        "V16 — PURE RESIDUAL COMPOSITION RETURN EFFECT vs V8",
        fontsize=15,
        fontweight="bold"
    )

    plt.ylabel(
        "Δweight × Asset Return (pp)"
    )

    plt.xlabel(
        "Execution Date"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.25
    )

    plt.tight_layout()
    plt.show()


# ==============================================================================
# 55. EXTRA GRAPH 27 — LAMBDA vs REALIZED V16−V8 EXCESS
# ==============================================================================

if (
    "Pre_Lambda"
    in V16Q_DECISIONS.columns
    and
    "V16_minus_V8_pp"
    in V16Q_DECISIONS.columns
):

    scatter = (
        V16Q_DECISIONS[
            [
                "Pre_Lambda",
                "V16_minus_V8_pp",
            ]
        ]
        .dropna()
    )

    if not scatter.empty:

        corr_lambda_excess = (
            scatter[
                "Pre_Lambda"
            ]
            .corr(
                scatter[
                    "V16_minus_V8_pp"
                ]
            )
        )

        plt.figure(
            figsize=(
                10,
                7
            )
        )

        plt.scatter(
            100.0
            *
            scatter[
                "Pre_Lambda"
            ],
            scatter[
                "V16_minus_V8_pp"
            ],
            s=60
        )

        plt.axhline(
            0,
            linewidth=1
        )

        plt.title(
            "V16 — PRE-EVENT λ vs REALIZED EXCESS vs V8\n"
            f"Correlation = {corr_lambda_excess:.3f}",
            fontsize=14,
            fontweight="bold"
        )

        plt.xlabel(
            "Pre-event Residual λ (%)"
        )

        plt.ylabel(
            "V16 - V8 Return (pp)"
        )

        plt.grid(
            linestyle="--",
            alpha=0.25
        )

        plt.tight_layout()
        plt.show()

else:

    corr_lambda_excess = np.nan


# ==============================================================================
# 56. FINAL V16 TARGET
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "FINAL FROZEN V16 TARGET"
)

print(
    "=" * 140
)

if "V16_FINAL_TARGET" in globals():

    try:

        final_target = (
            V16_FINAL_TARGET
            .copy()
        )

        if isinstance(
            final_target,
            dict
        ):

            final_target = pd.Series(
                final_target,
                name=
                    "Weight"
            )

        if isinstance(
            final_target,
            pd.DataFrame
        ):

            display(
                final_target
            )

        elif isinstance(
            final_target,
            pd.Series
        ):

            display(
                (
                    100.0
                    *
                    final_target
                )
                .rename(
                    "Weight_Pct"
                )
                .sort_values(
                    ascending=False
                )
                .to_frame()
                .round(6)
            )

        else:

            print(
                final_target
            )

    except Exception:

        print(
            V16_FINAL_TARGET
        )

else:

    print(
        "[i] V16_FINAL_TARGET not present."
    )


# ==============================================================================
# 57. FINAL SUMMARY
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "V16 — DEEP-DIVE SUMMARY"
)

print(
    "=" * 140
)

if "V16" in V16Q_PERFORMANCE_TABLE.index:

    v16 = (
        V16Q_PERFORMANCE_TABLE
        .loc[
            "V16"
        ]
    )

    print(
        f"\nFinal wealth                   : "
        f"{V16Q_FINAL_WEALTH:.6f}"
    )

    print(
        f"Total return                   : "
        f"{100*(V16Q_FINAL_WEALTH-1):+.2f}%"
    )

    print(
        f"CAGR                           : "
        f"{v16['CAGR_Pct']:+.2f}%"
    )

    print(
        f"Annualized volatility          : "
        f"{v16['Annualized_Vol_Pct']:.2f}%"
    )

    print(
        f"Sharpe                         : "
        f"{v16['Sharpe_rf0']:.3f}"
    )

    print(
        f"Sortino                        : "
        f"{v16['Sortino_rf0']:.3f}"
    )

    print(
        f"TRUE DAILY max drawdown        : "
        f"{v16['Max_Drawdown_Pct']:.2f}%"
    )

    print(
        f"Calmar                         : "
        f"{v16['Calmar']:.3f}"
    )

    print(
        f"Ulcer index                    : "
        f"{v16['Ulcer_Index_Pct']:.2f}%"
    )

    print(
        f"Beta vs TQQQ                   : "
        f"{v16.get('Beta_vs_TQQQ', np.nan):.3f}"
    )

    print(
        f"Correlation vs TQQQ            : "
        f"{v16.get('Correlation_vs_TQQQ', np.nan):.3f}"
    )

    print(
        f"Tracking error                 : "
        f"{v16.get('Tracking_Error_Pct', np.nan):.2f}%"
    )

    print(
        f"Information ratio              : "
        f"{v16.get('Information_Ratio', np.nan):.3f}"
    )

    print(
        f"Average daily excess           : "
        f"{v16.get('Average_Daily_Excess_bps', np.nan):+.3f} bps"
    )

    print(
        f"Monthly up capture             : "
        f"{v16.get('Up_Capture_Pct', np.nan):.2f}%"
    )

    print(
        f"Monthly down capture           : "
        f"{v16.get('Down_Capture_Pct', np.nan):.2f}%"
    )

    print(
        f"Daily VaR 95%                  : "
        f"{v16['Daily_VaR95_Pct']:.2f}%"
    )

    print(
        f"Daily CVaR 95%                 : "
        f"{v16['Daily_CVaR95_Pct']:.2f}%"
    )

    print(
        f"Tail ratio                     : "
        f"{v16['Tail_Ratio_95_5']:.3f}"
    )

    print(
        f"Omega                          : "
        f"{v16['Omega_0']:.3f}"
    )

if turnover_col is not None:

    print(
        f"\nTotal turnover                 : "
        f"{V16Q_PATH[turnover_col].sum():.3f}x"
    )

if np.isfinite(
    V16Q_TOTAL_TCA_CONTRIBUTION
):

    print(
        f"Total exact TCA wealth drag    : "
        f"{100*V16Q_TOTAL_TCA_CONTRIBUTION:.3f} pp"
    )

if not V16Q_CONCENTRATION.empty:

    print(
        f"Mean stock-sleeve weight       : "
        f"{V16Q_STOCK_WEIGHT.mean():.2f}%"
    )

    print(
        f"Mean TQQQ weight               : "
        f"{V16Q_TQQQ_WEIGHT.mean():.2f}%"
    )

    print(
        f"Mean effective N               : "
        f"{V16Q_EFFECTIVE_N.mean():.2f}"
    )

    print(
        f"Median effective N             : "
        f"{V16Q_EFFECTIVE_N.median():.2f}"
    )

    print(
        f"Mean max-name weight           : "
        f"{V16Q_MAX_NAME_WEIGHT.mean():.2f}%"
    )

if lambda_col is not None:

    lambda_series = (
        pd.to_numeric(
            V16Q_PATH[
                lambda_col
            ],
            errors="coerce"
        )
        .dropna()
    )

    if not lambda_series.empty:

        print(
            f"\nMean residual λ                : "
            f"{100*lambda_series.mean():.3f}%"
        )

        print(
            f"Final pre-event λ              : "
            f"{100*lambda_series.iloc[-1]:.3f}%"
        )

if np.isfinite(
    corr_lambda_excess
):

    print(
        f"λ vs realized V16-V8 corr      : "
        f"{corr_lambda_excess:.3f}"
    )

if np.isfinite(
    V16Q_TOTAL_ASSET_CONTRIBUTION
):

    print(
        f"\nExact asset contribution       : "
        f"{V16Q_TOTAL_ASSET_CONTRIBUTION:+.6f}"
    )

    print(
        f"Exact TCA contribution         : "
        f"{V16Q_TOTAL_TCA_CONTRIBUTION:+.6f}"
    )

    print(
        f"Terminal rebalance contribution: "
        f"{V16Q_TERMINAL_REBALANCE_CONTRIBUTION:+.6f}"
    )

    print(
        f"Attribution identity error     : "
        f"{V16Q_ATTRIBUTION_ERROR:.12f}"
    )


# ------------------------------------------------------------------------------
# V8 EVENT-LEVEL CHAMPION COMPARISON
# ------------------------------------------------------------------------------

V16Q_V8_COMPLETED_WEALTH = np.nan
V16Q_TQQQ_COMPLETED_WEALTH = np.nan

if "V8_Return_Pct" in V16Q_DECISIONS.columns:

    V16Q_V8_COMPLETED_WEALTH = float(
        (
            1.0
            +
            V16Q_DECISIONS[
                "V8_Return_Pct"
            ]
            /
            100.0
        )
        .prod()
    )

if "TQQQ_Return_Pct" in V16Q_DECISIONS.columns:

    V16Q_TQQQ_COMPLETED_WEALTH = float(
        (
            1.0
            +
            V16Q_DECISIONS[
                "TQQQ_Return_Pct"
            ]
            /
            100.0
        )
        .prod()
    )

if np.isfinite(
    V16Q_V8_COMPLETED_WEALTH
):

    print(
        f"\nV8 completed-period wealth     : "
        f"{V16Q_V8_COMPLETED_WEALTH:.6f}"
    )

    print(
        f"V16 minus V8 terminal pp       : "
        f"{100*(V16Q_FINAL_WEALTH-V16Q_V8_COMPLETED_WEALTH):+.3f} pp"
    )

if np.isfinite(
    V16Q_TQQQ_COMPLETED_WEALTH
):

    print(
        f"TQQQ completed-period wealth   : "
        f"{V16Q_TQQQ_COMPLETED_WEALTH:.6f}"
    )

    print(
        f"V16 minus TQQQ terminal pp     : "
        f"{100*(V16Q_FINAL_WEALTH-V16Q_TQQQ_COMPLETED_WEALTH):+.3f} pp"
    )


# ==============================================================================
# 58. DATA QUALITY / INTEGRITY
# ==============================================================================

print(
    "\n"
    +
    "=" * 140
)

print(
    "DATA QUALITY / INTEGRITY"
)

print(
    "=" * 140
)

print(
    f"[+] Daily certification status       : "
    f"{V16Q_DAILY_CERTIFIED}"
)

print(
    f"[+] V16 target source                : "
    f"{V16Q_TARGET_SOURCE}"
)

print(
    f"[+] Price source                     : "
    f"{V16Q_PRICE_WINNER_NAME}"
)

print(
    f"[+] TCA accounting convention        : "
    f"{V16Q_ACCOUNTING_MODE}"
)

print(
    f"[+] Missing intermediate daily marks : "
    f"{len(V16Q_MISSING_DAILY_MARKS):,}"
)

if V16Q_MISSING_DAILY_MARKS:

    display(
        pd.DataFrame(
            V16Q_MISSING_DAILY_MARKS
        )
        .head(30)
    )

print(
    "\n[+] V16 architecture unchanged."
)

print(
    "[+] Frozen V8 foundation unchanged."
)

print(
    "[+] No forecasting model fitted."
)

print(
    "[+] No parameter tuned."
)

print(
    "[+] No residual-momentum horizon changed."
)

print(
    "[+] No lambda selected from these results."
)

print(
    "[+] No stock-selection rule changed."
)

print(
    "[+] No missing intermediate quote was interpolated."
)

print(
    "[+] No forward fill was used."
)

print(
    "[+] This cell is analysis / diagnostics only."
)

print(
    "[+] TRUE POST-FREEZE V16 OOS STATUS remains unchanged."
)

print(
    "\n[+] V16 DEEP-DIVE DASHBOARD COMPLETE."
)

print(
    "=" * 140
)
