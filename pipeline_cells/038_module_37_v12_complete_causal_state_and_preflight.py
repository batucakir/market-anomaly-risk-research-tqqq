# MODULE 37 — V12 COMPLETE CAUSAL STATE AND PREFLIGHT
# Run in the same notebook, in module order.

# ==============================================================================
# V12 — BLOCK 2
# FROZEN V7/V8 ALPHA-SLEEVE RESOLUTION
# + CAUSAL MARKET-STATE PANEL
# + PRE-PERFORMANCE EXECUTION PREFLIGHT
# ==============================================================================
#
# IMPORTANT
# ---------
# NO V12 PERFORMANCE IS CALCULATED HERE.
# NO MODEL IS FITTED.
# NO STOCK-SELECTION RULE IS CHANGED.
#
# The frozen alpha sleeve is reconstructed algebraically from the already
# existing V8 portfolio decomposition:
#
#     V8_portfolio =
#         (1 - alpha_weight) * TQQQ
#         +
#         alpha_weight * frozen_alpha_sleeve
#
# Therefore for non-TQQQ securities:
#
#     frozen_alpha_sleeve_weight_i
#         =
#     V8_portfolio_weight_i / alpha_weight
#
# This is a deterministic recovery of the already-observed V8 architecture,
# NOT a new stock-selection rule.
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


print("=" * 140)
print("V12 — BLOCK 2")
print("FROZEN V7/V8 ALPHA-SLEEVE RESOLUTION")
print("+ CAUSAL MARKET-STATE PANEL")
print("+ PRE-PERFORMANCE EXECUTION PREFLIGHT")
print("=" * 140)

print("\nNO MODEL FITTING.")
print("NO V12 PERFORMANCE CALCULATION.")


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V12_B2_REQUIRED = [

    "V12_RESEARCH_CONTRACT_FINGERPRINT",
    "V12_RESEARCH_CONTRACT",

    "V8_PATH",

    "V8Q_WEIGHT_MATRIX",
    "V8Q_ALPHA_WEIGHT",
    "V8Q_TQQQ_WEIGHT",

    "V10_LIFECYCLE_PANEL",

    "V10_BASE_TCA_RATE",
    "V10_IMPACT_COEFFICIENT",
    "V10_REFERENCE_AUM_USD",
]


V12_B2_MISSING = [
    name
    for name in V12_B2_REQUIRED
    if name not in globals()
]


if V12_B2_MISSING:

    raise RuntimeError(
        "V12 Block 2 is missing genuinely required objects: "
        f"{V12_B2_MISSING}"
    )


# ==============================================================================
# 1. CONTRACT LOCK CHECK
# ==============================================================================

if (
    V12_RESEARCH_CONTRACT[
        "version"
    ]
    !=
    "V12"
):

    raise RuntimeError(
        "V12 research contract is not active."
    )


if (
    V12_RESEARCH_CONTRACT[
        "status"
    ]
    !=
    "PRE_PERFORMANCE_LOCKED_RESEARCH_CHALLENGER"
):

    raise RuntimeError(
        "V12 contract is not in the expected pre-performance locked state."
    )


# ==============================================================================
# 2. NORMALIZE V8 PATH / DECISION DATES
# ==============================================================================

V12_V8_PATH = (
    V8_PATH
    .copy()
    .reset_index(
        drop=True
    )
)


V12_DATE_COLUMN_CANDIDATES = [
    "Execution_Date",
    "Date",
]


V12_EXECUTION_DATE_COLUMN = None


for candidate in V12_DATE_COLUMN_CANDIDATES:

    if candidate in V12_V8_PATH.columns:

        V12_EXECUTION_DATE_COLUMN = candidate

        break


if V12_EXECUTION_DATE_COLUMN is None:

    raise RuntimeError(
        "V8_PATH has no recognizable execution-date column."
    )


V12_EXECUTION_DATES = (
    pd.to_datetime(
        V12_V8_PATH[
            V12_EXECUTION_DATE_COLUMN
        ],
        errors="coerce",
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


if V12_EXECUTION_DATES.isna().any():

    raise RuntimeError(
        "V8 execution dates contain missing values."
    )


if len(
    V12_EXECUTION_DATES
) != 34:

    raise RuntimeError(
        "Expected exactly 34 frozen V8 decisions."
    )


if V12_EXECUTION_DATES.duplicated().any():

    raise RuntimeError(
        "Duplicate V8 execution dates detected."
    )


# ==============================================================================
# 3. NORMALIZE V8 WEIGHT MATRIX
# ==============================================================================

if not isinstance(
    V8Q_WEIGHT_MATRIX,
    pd.DataFrame,
):

    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX must be a DataFrame."
    )


V12_V8_WEIGHT_MATRIX = (
    V8Q_WEIGHT_MATRIX
    .copy()
)


if len(
    V12_V8_WEIGHT_MATRIX
) != 34:

    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX must contain 34 decision rows."
    )


# ------------------------------------------------------------------------------
# Align rows explicitly to the known V8 execution calendar.
#
# If matrix already uses dates as index, preserve them.
# Otherwise use the ordered V8_PATH execution dates.
# ------------------------------------------------------------------------------

try:

    matrix_dates = pd.to_datetime(
        V12_V8_WEIGHT_MATRIX.index,
        errors="coerce",
    )

    matrix_date_usable = (
        matrix_dates.notna().all()
        and
        len(
            pd.DatetimeIndex(
                matrix_dates
            ).unique()
        )
        ==
        34
    )

except Exception:

    matrix_date_usable = False


if matrix_date_usable:

    matrix_dates = (
        pd.DatetimeIndex(
            matrix_dates
        )
        .tz_localize(None)
        .normalize()
    )

    V12_V8_WEIGHT_MATRIX.index = (
        matrix_dates
    )


    expected_set = set(
        V12_EXECUTION_DATES
    )

    observed_set = set(
        V12_V8_WEIGHT_MATRIX.index
    )


    if observed_set != expected_set:

        # Row order / default integer index was likely converted to dates
        # incorrectly. Use the authoritative V8_PATH calendar instead.

        V12_V8_WEIGHT_MATRIX.index = (
            pd.DatetimeIndex(
                V12_EXECUTION_DATES
            )
        )

    else:

        V12_V8_WEIGHT_MATRIX = (
            V12_V8_WEIGHT_MATRIX
            .reindex(
                pd.DatetimeIndex(
                    V12_EXECUTION_DATES
                )
            )
        )

else:

    V12_V8_WEIGHT_MATRIX.index = (
        pd.DatetimeIndex(
            V12_EXECUTION_DATES
        )
    )


# ==============================================================================
# 4. CLEAN TICKER COLUMNS
# ==============================================================================

V12_V8_WEIGHT_MATRIX.columns = [
    str(column)
    .upper()
    .strip()

    for column
    in V12_V8_WEIGHT_MATRIX.columns
]


if len(
    set(
        V12_V8_WEIGHT_MATRIX.columns
    )
) != len(
    V12_V8_WEIGHT_MATRIX.columns
):

    # Consolidate duplicate normalized ticker columns safely.
    V12_V8_WEIGHT_MATRIX = (
        V12_V8_WEIGHT_MATRIX.T
        .groupby(
            level=0
        )
        .sum()
        .T
    )


V12_V8_WEIGHT_MATRIX = (
    V12_V8_WEIGHT_MATRIX
    .apply(
        pd.to_numeric,
        errors="coerce",
    )
    .fillna(
        0.0
    )
)


if (
    V12_V8_WEIGHT_MATRIX
    <
    -1e-12
).any().any():

    raise RuntimeError(
        "Negative V8 portfolio weight detected."
    )


V12_V8_WEIGHT_MATRIX = (
    V12_V8_WEIGHT_MATRIX
    .clip(
        lower=0.0
    )
)


# ==============================================================================
# 5. ALIGN V8 ALPHA / TQQQ WEIGHT SERIES
# ==============================================================================

def v12_align_34_series(
    source,
    name,
):

    if isinstance(
        source,
        pd.Series,
    ):

        values = pd.to_numeric(
            source,
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

    else:

        values = np.asarray(
            source,
            dtype=float,
        ).reshape(
            -1
        )


    if len(
        values
    ) != 34:

        raise RuntimeError(
            f"{name} must contain exactly 34 observations."
        )


    if not np.isfinite(
        values
    ).all():

        raise RuntimeError(
            f"{name} contains non-finite values."
        )


    return pd.Series(
        values,
        index=pd.DatetimeIndex(
            V12_EXECUTION_DATES
        ),
        name=name,
    )


V12_V8_ALPHA_WEIGHT = v12_align_34_series(
    V8Q_ALPHA_WEIGHT,
    "V8_Alpha_Weight",
)


V12_V8_TQQQ_WEIGHT = v12_align_34_series(
    V8Q_TQQQ_WEIGHT,
    "V8_TQQQ_Weight",
)


# ==============================================================================
# 6. DETERMINE SCALE: 0–1 OR 0–100
# ==============================================================================

def v12_to_fraction(
    series,
    name,
):

    max_value = float(
        series.abs().max()
    )


    if max_value <= 1.000001:

        result = series.astype(
            float
        ).copy()

        scale = "FRACTION"

    elif max_value <= 100.0001:

        result = (
            series.astype(
                float
            )
            /
            100.0
        )

        scale = "PERCENT"

    else:

        raise RuntimeError(
            f"Cannot infer scale of {name}."
        )


    if (
        result < -1e-10
    ).any() or (
        result > 1.0000001
    ).any():

        raise RuntimeError(
            f"{name} lies outside [0,1] after normalization."
        )


    return (
        result.clip(
            0.0,
            1.0,
        ),
        scale,
    )


(
    V12_V8_ALPHA_WEIGHT,
    V12_ALPHA_SCALE,
) = v12_to_fraction(
    V12_V8_ALPHA_WEIGHT,
    "V8Q_ALPHA_WEIGHT",
)


(
    V12_V8_TQQQ_WEIGHT,
    V12_TQQQ_SCALE,
) = v12_to_fraction(
    V12_V8_TQQQ_WEIGHT,
    "V8Q_TQQQ_WEIGHT",
)


# ==============================================================================
# 7. NORMALIZE V8 MATRIX SCALE
# ==============================================================================

V12_MATRIX_ROW_SUM = (
    V12_V8_WEIGHT_MATRIX
    .sum(
        axis=1
    )
)


V12_MEDIAN_MATRIX_SUM = float(
    V12_MATRIX_ROW_SUM.median()
)


if (
    0.99
    <=
    V12_MEDIAN_MATRIX_SUM
    <=
    1.01
):

    V12_MATRIX_SCALE = (
        "FRACTION"
    )


elif (
    99.0
    <=
    V12_MEDIAN_MATRIX_SUM
    <=
    101.0
):

    V12_V8_WEIGHT_MATRIX = (
        V12_V8_WEIGHT_MATRIX
        /
        100.0
    )

    V12_MATRIX_SCALE = (
        "PERCENT"
    )


else:

    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX does not appear to be normalized portfolio weights. "
        f"Median row sum = {V12_MEDIAN_MATRIX_SUM:.6f}"
    )


# ==============================================================================
# 8. VERIFY V8 PORTFOLIO WEIGHT SUM
# ==============================================================================

V12_MATRIX_ROW_SUM = (
    V12_V8_WEIGHT_MATRIX
    .sum(
        axis=1
    )
)


V12_MATRIX_SUM_MAX_ERROR = float(
    np.max(
        np.abs(
            V12_MATRIX_ROW_SUM
            -
            1.0
        )
    )
)


if (
    V12_MATRIX_SUM_MAX_ERROR
    >
    1e-6
):

    raise RuntimeError(
        "Frozen V8 portfolio matrix does not sum to 1 by decision. "
        f"Max error = {V12_MATRIX_SUM_MAX_ERROR:.12f}"
    )


# ==============================================================================
# 9. VERIFY V8 CORE / ALPHA IDENTITY
# ==============================================================================

V12_CORE_ALPHA_IDENTITY_ERROR = float(
    np.max(
        np.abs(
            V12_V8_TQQQ_WEIGHT
            +
            V12_V8_ALPHA_WEIGHT
            -
            1.0
        )
    )
)


if (
    V12_CORE_ALPHA_IDENTITY_ERROR
    >
    1e-6
):

    raise RuntimeError(
        "V8 TQQQ + Alpha decomposition does not sum to 1. "
        f"Max error = {V12_CORE_ALPHA_IDENTITY_ERROR:.12f}"
    )


# ==============================================================================
# 10. VERIFY MATRIX TQQQ COLUMN
# ==============================================================================

if "TQQQ" not in V12_V8_WEIGHT_MATRIX.columns:

    raise RuntimeError(
        "V8Q_WEIGHT_MATRIX has no TQQQ column."
    )


V12_MATRIX_TQQQ_ERROR = float(
    np.max(
        np.abs(
            V12_V8_WEIGHT_MATRIX[
                "TQQQ"
            ]
            -
            V12_V8_TQQQ_WEIGHT
        )
    )
)


if (
    V12_MATRIX_TQQQ_ERROR
    >
    1e-6
):

    raise RuntimeError(
        "V8 weight matrix TQQQ column does not match V8Q_TQQQ_WEIGHT. "
        f"Max error = {V12_MATRIX_TQQQ_ERROR:.12f}"
    )


print(
    "\n[+] Frozen V8 core/alpha decomposition verified."
)


# ==============================================================================
# 11. RECONSTRUCT FROZEN ALPHA SLEEVE
# ==============================================================================

V12_FROZEN_ALPHA_SLEEVE_MATRIX = pd.DataFrame(
    0.0,
    index=V12_V8_WEIGHT_MATRIX.index,
    columns=[
        column
        for column
        in V12_V8_WEIGHT_MATRIX.columns
        if column != "TQQQ"
    ],
)


V12_FROZEN_ALPHA_AVAILABLE = pd.Series(
    False,
    index=V12_V8_WEIGHT_MATRIX.index,
    name="Alpha_Sleeve_Available",
)


V12_FROZEN_ALPHA_TARGETS = {}


for execution_date in (
    V12_V8_WEIGHT_MATRIX.index
):

    alpha_weight = float(
        V12_V8_ALPHA_WEIGHT.loc[
            execution_date
        ]
    )


    portfolio_row = (
        V12_V8_WEIGHT_MATRIX.loc[
            execution_date
        ]
        .drop(
            labels=[
                "TQQQ"
            ]
        )
    )


    satellite_mass = float(
        portfolio_row.sum()
    )


    if alpha_weight > 1e-12:

        identity_error = abs(
            satellite_mass
            -
            alpha_weight
        )


        if identity_error > 1e-6:

            raise RuntimeError(
                "V8 non-TQQQ portfolio mass does not equal frozen "
                "alpha allocation on "
                f"{execution_date.date()}. "
                f"Error={identity_error:.12f}"
            )


        sleeve = (
            portfolio_row
            /
            alpha_weight
        )


        sleeve = sleeve[
            sleeve > 1e-14
        ]


        sleeve_sum = float(
            sleeve.sum()
        )


        if not np.isclose(
            sleeve_sum,
            1.0,
            atol=1e-8,
            rtol=0.0,
        ):

            raise RuntimeError(
                "Recovered frozen alpha sleeve does not sum to 1 on "
                f"{execution_date.date()}."
            )


        sleeve = (
            sleeve
            /
            sleeve_sum
        )


        V12_FROZEN_ALPHA_SLEEVE_MATRIX.loc[
            execution_date,
            sleeve.index,
        ] = (
            sleeve.values
        )


        V12_FROZEN_ALPHA_AVAILABLE.loc[
            execution_date
        ] = True


        V12_FROZEN_ALPHA_TARGETS[
            pd.Timestamp(
                execution_date
            )
        ] = {
            str(ticker):
                float(weight)

            for ticker, weight
            in sleeve.items()
        }


    else:

        # V8 had no actual alpha capital in this event.
        #
        # We DO NOT invent a sleeve that cannot be proven from the frozen V8
        # portfolio state.

        if satellite_mass > 1e-8:

            raise RuntimeError(
                "V8 has non-TQQQ holdings despite zero reported alpha weight."
            )


        V12_FROZEN_ALPHA_TARGETS[
            pd.Timestamp(
                execution_date
            )
        ] = {}


# ==============================================================================
# 12. RECONSTRUCT V8 MATRIX FROM RECOVERED SLEEVE — EXACT VALIDATION
# ==============================================================================

V12_RECONSTRUCTED_V8_MATRIX = pd.DataFrame(
    0.0,
    index=V12_V8_WEIGHT_MATRIX.index,
    columns=V12_V8_WEIGHT_MATRIX.columns,
)


for execution_date in (
    V12_V8_WEIGHT_MATRIX.index
):

    alpha_weight = float(
        V12_V8_ALPHA_WEIGHT.loc[
            execution_date
        ]
    )

    tqqq_weight = float(
        V12_V8_TQQQ_WEIGHT.loc[
            execution_date
        ]
    )


    V12_RECONSTRUCTED_V8_MATRIX.loc[
        execution_date,
        "TQQQ",
    ] = tqqq_weight


    sleeve = V12_FROZEN_ALPHA_TARGETS[
        execution_date
    ]


    for ticker, weight in (
        sleeve.items()
    ):

        V12_RECONSTRUCTED_V8_MATRIX.loc[
            execution_date,
            ticker,
        ] = (
            alpha_weight
            *
            weight
        )


V12_V8_RECONSTRUCTION_MAX_ERROR = float(
    np.max(
        np.abs(
            V12_RECONSTRUCTED_V8_MATRIX
            .to_numpy(
                dtype=float
            )
            -
            V12_V8_WEIGHT_MATRIX
            .to_numpy(
                dtype=float
            )
        )
    )
)


if (
    V12_V8_RECONSTRUCTION_MAX_ERROR
    >
    1e-8
):

    raise RuntimeError(
        "Recovered alpha sleeve failed exact V8 portfolio reconstruction. "
        f"Max error={V12_V8_RECONSTRUCTION_MAX_ERROR:.12f}"
    )


print(
    "[+] Frozen alpha sleeve reconstructed from V8 exactly."
)


# ==============================================================================
# 13. ALPHA-SLEEVE CONCENTRATION STATE
# ==============================================================================

V12_ALPHA_STATE_ROWS = []


for execution_date in (
    V12_FROZEN_ALPHA_SLEEVE_MATRIX.index
):

    sleeve = (
        V12_FROZEN_ALPHA_SLEEVE_MATRIX.loc[
            execution_date
        ]
    )


    sleeve = sleeve[
        sleeve > 1e-14
    ]


    if sleeve.empty:

        effective_n = np.nan

        max_weight = np.nan

        names = 0

    else:

        weights = sleeve.to_numpy(
            dtype=float
        )


        effective_n = float(
            1.0
            /
            np.sum(
                weights ** 2
            )
        )


        max_weight = float(
            np.max(
                weights
            )
        )


        names = int(
            len(
                sleeve
            )
        )


    V12_ALPHA_STATE_ROWS.append(
        {
            "Execution_Date":
                pd.Timestamp(
                    execution_date
                ),

            "Alpha_Sleeve_Available":
                bool(
                    not sleeve.empty
                ),

            "Alpha_Names":
                names,

            "Alpha_Effective_N":
                effective_n,

            "Alpha_Max_Weight":
                max_weight,
        }
    )


V12_ALPHA_STATE = (
    pd.DataFrame(
        V12_ALPHA_STATE_ROWS
    )
    .set_index(
        "Execution_Date"
    )
)




# V12 sections 14–16: minimal contract-derived state adapter.
# Contract: PRICE_OVER_SMA252_MINUS_1, PRICE_OVER_SMA63_MINUS_1,
# TRAILING_63_SESSION_ANNUALIZED_VOL. Pandas sample standard deviation (ddof=1)
# of simple close returns is stated explicitly; unavailable original formatting
# is not represented as recovered verbatim source.
V12_LIFECYCLE = V10_LIFECYCLE_PANEL.copy()
V12_LIFECYCLE['Date'] = pd.to_datetime(V12_LIFECYCLE.Date).dt.tz_localize(None).dt.normalize()
V12_LIFECYCLE['Ticker'] = V12_LIFECYCLE.Ticker.astype(str).str.upper().str.strip()
V12_LIFECYCLE = V12_LIFECYCLE.sort_values(['Ticker','Date'])
if V12_LIFECYCLE.duplicated(['Ticker','Date']).any():
    raise RuntimeError('Duplicate canonical V12 lifecycle quotes.')
V12_TQQQ_PRICE = V12_LIFECYCLE.loc[V12_LIFECYCLE.Ticker=='TQQQ'].set_index('Date')['Adj_Close'].sort_index()
V12_TQQQ_PRICE = pd.to_numeric(V12_TQQQ_PRICE, errors='raise')
if not np.isfinite(V12_TQQQ_PRICE).all() or (V12_TQQQ_PRICE<=0).any():
    raise RuntimeError('Invalid canonical TQQQ series for V12 state.')
V12_TQQQ_LONG_TREND = V12_TQQQ_PRICE / V12_TQQQ_PRICE.rolling(252,min_periods=252).mean()-1.0
V12_TQQQ_MEDIUM_TREND = V12_TQQQ_PRICE / V12_TQQQ_PRICE.rolling(63,min_periods=63).mean()-1.0
V12_TQQQ_VOL63 = V12_TQQQ_PRICE.pct_change(fill_method=None).rolling(63,min_periods=63).std(ddof=1)*np.sqrt(252.0)

# ==============================================================================
# 17. MAP EXECUTION DATE -> SIGNAL DATE
# ==============================================================================
#
# Execution convention is frozen:
#
#     SIGNAL_AT_CLOSE_T
#     EXECUTE_AT_CLOSE_T_PLUS_1
#
# V8_PATH does not need to store Signal_Date explicitly.
# The signal date is deterministically reconstructed as the immediately
# preceding actual TQQQ trading session.
#
# NO PERFORMANCE INFORMATION IS USED.
# ==============================================================================

V12_TQQQ_TRADING_DATES = (
    pd.DatetimeIndex(
        V12_TQQQ_PRICE.index
    )
    .tz_localize(None)
    .normalize()
    .sort_values()
    .unique()
)


V12_SIGNAL_DATE_LIST = []


for execution_date in pd.DatetimeIndex(
    V12_EXECUTION_DATES
):

    execution_date = (
        pd.Timestamp(
            execution_date
        )
        .tz_localize(None)
        .normalize()
    )


    # Locate execution date on the actual TQQQ trading calendar.
    execution_position = (
        V12_TQQQ_TRADING_DATES
        .searchsorted(
            execution_date,
            side="left",
        )
    )


    # Execution date itself must be an actual TQQQ session.
    if (
        execution_position
        >=
        len(
            V12_TQQQ_TRADING_DATES
        )
        or
        V12_TQQQ_TRADING_DATES[
            execution_position
        ]
        !=
        execution_date
    ):

        raise RuntimeError(
            "V12 execution date is not an exact TQQQ trading session: "
            f"{execution_date.date()}"
        )


    # Need one completed trading session immediately before execution.
    if execution_position == 0:

        raise RuntimeError(
            "Insufficient TQQQ history before execution date: "
            f"{execution_date.date()}"
        )


    signal_date = pd.Timestamp(
        V12_TQQQ_TRADING_DATES[
            execution_position - 1
        ]
    )


    if not (
        signal_date
        <
        execution_date
    ):

        raise RuntimeError(
            "Non-causal V12 signal/execution ordering detected."
        )


    V12_SIGNAL_DATE_LIST.append(
        signal_date
    )


V12_SIGNAL_DATES = pd.Series(
    V12_SIGNAL_DATE_LIST,
    dtype="datetime64[ns]",
)


if len(
    V12_SIGNAL_DATES
) != len(
    V12_EXECUTION_DATES
):

    raise RuntimeError(
        "Signal/execution calendar length mismatch."
    )


if V12_SIGNAL_DATES.isna().any():

    raise RuntimeError(
        "Missing reconstructed V12 signal date."
    )


V12_SIGNAL_EXECUTION_MAP = pd.DataFrame(
    {
        "Signal_Date":
            V12_SIGNAL_DATES.to_numpy(),

        "Execution_Date":
            pd.DatetimeIndex(
                V12_EXECUTION_DATES
            ).to_numpy(),
    }
)


# ==============================================================================
# 17A. EXECUTION-ALIGNMENT AUDIT
# ==============================================================================

V12_SIGNAL_EXECUTION_MAP[
    "Signal_Before_Execution"
] = (
    V12_SIGNAL_EXECUTION_MAP[
        "Signal_Date"
    ]
    <
    V12_SIGNAL_EXECUTION_MAP[
        "Execution_Date"
    ]
)


if not V12_SIGNAL_EXECUTION_MAP[
    "Signal_Before_Execution"
].all():

    raise RuntimeError(
        "V12 signal/execution causality check failed."
    )


print(
    "\n[+] V12 signal dates reconstructed from the actual TQQQ trading calendar."
)

print(
    "[+] Convention verified: signal close T -> execution close next trading session."
)

display(
    V12_SIGNAL_EXECUTION_MAP.head(
        10
    )
)
# ==============================================================================
# V12 — BLOCK 2 CONTINUATION
# SECTIONS 18 -> END
#
# Run this AFTER the successful signal-date repair cell.
#
# NO MODEL FITTING.
# NO V12 PERFORMANCE CALCULATION.
# ==============================================================================

import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


print("=" * 140)
print("V12 — BLOCK 2 CONTINUATION")
print("CAUSAL STATE PANEL + PRE-PERFORMANCE EXECUTION PREFLIGHT")
print("=" * 140)


# ==============================================================================
# 0. CONTINUATION PREFLIGHT
# ==============================================================================

V12_CONT_REQUIRED = [
    "V12_SIGNAL_EXECUTION_MAP",
    "V12_TQQQ_PRICE",
    "V12_TQQQ_LONG_TREND",
    "V12_TQQQ_MEDIUM_TREND",
    "V12_TQQQ_VOL63",
    "V12_ALPHA_STATE",
    "V12_FROZEN_ALPHA_TARGETS",
    "V12_FROZEN_ALPHA_SLEEVE_MATRIX",
    "V12_V8_RECONSTRUCTION_MAX_ERROR",
    "V12_MATRIX_SCALE",
    "V12_ALPHA_SCALE",
    "V12_TQQQ_SCALE",
    "V12_MATRIX_SUM_MAX_ERROR",
    "V12_CORE_ALPHA_IDENTITY_ERROR",
    "V12_MATRIX_TQQQ_ERROR",
    "V12_FROZEN_ALPHA_AVAILABLE",
    "V12_LIFECYCLE",
    "V12_RESEARCH_CONTRACT_FINGERPRINT",
]


V12_CONT_MISSING = [
    name
    for name in V12_CONT_REQUIRED
    if name not in globals()
]


if V12_CONT_MISSING:
    raise RuntimeError(
        "V12 Block 2 continuation is missing prior Block 2 state: "
        f"{V12_CONT_MISSING}"
    )


if len(V12_SIGNAL_EXECUTION_MAP) != 34:
    raise RuntimeError(
        "Expected exactly 34 signal/execution mappings."
    )


if not V12_SIGNAL_EXECUTION_MAP[
    "Signal_Before_Execution"
].all():
    raise RuntimeError(
        "Signal/execution causality check failed."
    )


print("[+] Prior Block 2 state found.")
print("[+] 34/34 causal signal/execution mappings found.")


# ==============================================================================
# 18. RAW STATE PANEL
# ==============================================================================

V12_STATE_ROWS = []


for row in V12_SIGNAL_EXECUTION_MAP.itertuples(index=False):

    signal_date = pd.Timestamp(
        row.Signal_Date
    ).normalize()

    execution_date = pd.Timestamp(
        row.Execution_Date
    ).normalize()


    if signal_date not in V12_TQQQ_PRICE.index:
        raise RuntimeError(
            "Missing exact TQQQ signal-close observation: "
            f"{signal_date.date()}"
        )


    if execution_date not in V12_ALPHA_STATE.index:
        raise RuntimeError(
            "Missing frozen alpha state for execution date: "
            f"{execution_date.date()}"
        )


    alpha_state = V12_ALPHA_STATE.loc[
        execution_date
    ]


    long_trend = V12_TQQQ_LONG_TREND.loc[
        signal_date
    ]

    medium_trend = V12_TQQQ_MEDIUM_TREND.loc[
        signal_date
    ]

    vol63 = V12_TQQQ_VOL63.loc[
        signal_date
    ]


    if not np.isfinite(long_trend):
        raise RuntimeError(
            f"Missing 252-session TQQQ trend at {signal_date.date()}."
        )

    if not np.isfinite(medium_trend):
        raise RuntimeError(
            f"Missing 63-session TQQQ trend at {signal_date.date()}."
        )

    if not np.isfinite(vol63):
        raise RuntimeError(
            f"Missing 63-session TQQQ volatility at {signal_date.date()}."
        )


    alpha_available = bool(
        alpha_state[
            "Alpha_Sleeve_Available"
        ]
    )


    alpha_effective_n = (
        float(
            alpha_state[
                "Alpha_Effective_N"
            ]
        )
        if np.isfinite(
            alpha_state[
                "Alpha_Effective_N"
            ]
        )
        else np.nan
    )


    alpha_max_weight = (
        float(
            alpha_state[
                "Alpha_Max_Weight"
            ]
        )
        if np.isfinite(
            alpha_state[
                "Alpha_Max_Weight"
            ]
        )
        else np.nan
    )


    V12_STATE_ROWS.append(
        {
            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "TQQQ_Long_Trend":
                float(long_trend),

            "TQQQ_Medium_Trend":
                float(medium_trend),

            "TQQQ_Vol63":
                float(vol63),

            "Alpha_Sleeve_Available":
                alpha_available,

            "Alpha_Names":
                int(
                    alpha_state[
                        "Alpha_Names"
                    ]
                ),

            "Alpha_Effective_N":
                alpha_effective_n,

            "Alpha_Max_Weight":
                alpha_max_weight,
        }
    )


V12_STATE_PANEL = pd.DataFrame(
    V12_STATE_ROWS
).reset_index(
    drop=True
)


if len(V12_STATE_PANEL) != 34:
    raise RuntimeError(
        "V12 state panel must contain exactly 34 decisions."
    )


# ==============================================================================
# 19. CAUSAL EXPANDING PERCENTILE FUNCTION
# ==============================================================================

def v12_causal_expanding_percentile(values):

    values = pd.Series(
        values,
        dtype=float,
    )

    output = np.full(
        len(values),
        np.nan,
        dtype=float,
    )


    for i in range(len(values)):

        current = values.iloc[i]

        if not np.isfinite(current):
            continue


        history = (
            values.iloc[: i + 1]
            .dropna()
        )


        less = float(
            (history < current).sum()
        )

        equal = float(
            (history == current).sum()
        )


        output[i] = (
            less
            +
            0.5 * equal
        ) / float(
            len(history)
        )


    return pd.Series(
        output,
        index=values.index,
        dtype=float,
    )


# ==============================================================================
# 20. CAUSAL MARKET-STATE PERCENTILES
# ==============================================================================

V12_STATE_PANEL[
    "P_Long_Trend"
] = v12_causal_expanding_percentile(
    V12_STATE_PANEL[
        "TQQQ_Long_Trend"
    ]
)


V12_STATE_PANEL[
    "P_Medium_Trend"
] = v12_causal_expanding_percentile(
    V12_STATE_PANEL[
        "TQQQ_Medium_Trend"
    ]
)


V12_STATE_PANEL[
    "P_Vol63"
] = v12_causal_expanding_percentile(
    V12_STATE_PANEL[
        "TQQQ_Vol63"
    ]
)


# ==============================================================================
# 21. CAUSAL FROZEN-SLEEVE STATE PERCENTILES
# ==============================================================================

V12_STATE_PANEL[
    "P_Alpha_Effective_N"
] = v12_causal_expanding_percentile(
    V12_STATE_PANEL[
        "Alpha_Effective_N"
    ]
)


V12_STATE_PANEL[
    "P_Alpha_Max_Weight"
] = v12_causal_expanding_percentile(
    V12_STATE_PANEL[
        "Alpha_Max_Weight"
    ]
)


# ==============================================================================
# 22. PREDECLARED SCORE COMPONENTS
# ==============================================================================

V12_STATE_PANEL[
    "Score_Weak_Long_Trend"
] = (
    1.0
    -
    V12_STATE_PANEL[
        "P_Long_Trend"
    ]
)


V12_STATE_PANEL[
    "Score_Weak_Medium_Trend"
] = (
    1.0
    -
    V12_STATE_PANEL[
        "P_Medium_Trend"
    ]
)


V12_STATE_PANEL[
    "Score_High_Volatility"
] = (
    V12_STATE_PANEL[
        "P_Vol63"
    ]
)


V12_STATE_PANEL[
    "Score_High_Alpha_Breadth"
] = (
    V12_STATE_PANEL[
        "P_Alpha_Effective_N"
    ]
)


V12_STATE_PANEL[
    "Score_Low_Alpha_Concentration"
] = (
    1.0
    -
    V12_STATE_PANEL[
        "P_Alpha_Max_Weight"
    ]
)


V12_SCORE_COMPONENT_COLUMNS = [
    "Score_Weak_Long_Trend",
    "Score_Weak_Medium_Trend",
    "Score_High_Volatility",
    "Score_High_Alpha_Breadth",
    "Score_Low_Alpha_Concentration",
]


# ==============================================================================
# 23. LOCKED V12 ALLOCATION
# ==============================================================================

V12_STATE_PANEL[
    "Predeclared_Alpha_Weight"
] = 0.0


for idx in V12_STATE_PANEL.index:

    alpha_available = bool(
        V12_STATE_PANEL.loc[
            idx,
            "Alpha_Sleeve_Available",
        ]
    )


    if not alpha_available:

        V12_STATE_PANEL.loc[
            idx,
            "Predeclared_Alpha_Weight",
        ] = 0.0

        continue


    score_components = (
        V12_STATE_PANEL.loc[
            idx,
            V12_SCORE_COMPONENT_COLUMNS,
        ]
        .to_numpy(
            dtype=float
        )
    )


    if not np.isfinite(
        score_components
    ).all():

        raise RuntimeError(
            "Missing V12 allocation-state component "
            f"at decision {idx + 1}."
        )


    alpha_weight = float(
        np.median(
            score_components
        )
    )


    if not (
        0.0
        <=
        alpha_weight
        <=
        1.0
    ):

        raise RuntimeError(
            "V12 alpha weight outside [0,1]."
        )


    V12_STATE_PANEL.loc[
        idx,
        "Predeclared_Alpha_Weight",
    ] = alpha_weight


V12_STATE_PANEL[
    "Predeclared_TQQQ_Weight"
] = (
    1.0
    -
    V12_STATE_PANEL[
        "Predeclared_Alpha_Weight"
    ]
)


allocation_identity_error = float(
    np.max(
        np.abs(
            V12_STATE_PANEL[
                "Predeclared_TQQQ_Weight"
            ]
            +
            V12_STATE_PANEL[
                "Predeclared_Alpha_Weight"
            ]
            -
            1.0
        )
    )
)


if allocation_identity_error > 1e-12:
    raise RuntimeError(
        "V12 TQQQ/Alpha allocation identity failed."
    )


# ==============================================================================
# 24. CONSTRUCT PREDECLARED PORTFOLIO TARGETS
# ==============================================================================

V12_PREDECLARED_TARGETS = {}


for row in V12_STATE_PANEL.itertuples(index=False):

    execution_date = pd.Timestamp(
        row.Execution_Date
    ).normalize()

    alpha_weight = float(
        row.Predeclared_Alpha_Weight
    )

    tqqq_weight = float(
        row.Predeclared_TQQQ_Weight
    )


    sleeve = V12_FROZEN_ALPHA_TARGETS[
        execution_date
    ]


    target = {}


    if tqqq_weight > 1e-14:
        target["TQQQ"] = tqqq_weight


    if alpha_weight > 1e-14:

        if not sleeve:
            raise RuntimeError(
                "Positive V12 alpha weight assigned when frozen "
                "alpha sleeve is unavailable."
            )


        sleeve_sum = float(
            sum(
                sleeve.values()
            )
        )


        if not np.isclose(
            sleeve_sum,
            1.0,
            atol=1e-8,
            rtol=0.0,
        ):
            raise RuntimeError(
                "Frozen alpha sleeve does not sum to 1."
            )


        for ticker, sleeve_weight in sleeve.items():

            portfolio_weight = (
                alpha_weight
                *
                float(sleeve_weight)
            )


            if portfolio_weight > 1e-14:
                target[
                    str(ticker).upper().strip()
                ] = (
                    target.get(
                        str(ticker).upper().strip(),
                        0.0,
                    )
                    +
                    portfolio_weight
                )


    total_weight = float(
        sum(
            target.values()
        )
    )


    if not np.isclose(
        total_weight,
        1.0,
        atol=1e-10,
        rtol=0.0,
    ):
        raise RuntimeError(
            "V12 predeclared target does not sum to 1 on "
            f"{execution_date.date()}. "
            f"Sum={total_weight:.12f}"
        )


    V12_PREDECLARED_TARGETS[
        execution_date
    ] = target


# ==============================================================================
# 25. EXACT PRICE LOOKUP
# ==============================================================================

V12_PRICE_LOOKUP = (
    V12_LIFECYCLE[
        [
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    ]
    .copy()
)


V12_PRICE_LOOKUP[
    "Ticker"
] = (
    V12_PRICE_LOOKUP[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V12_PRICE_LOOKUP[
    "Date"
] = (
    pd.to_datetime(
        V12_PRICE_LOOKUP[
            "Date"
        ],
        errors="coerce",
    )
    .dt.tz_localize(None)
    .dt.normalize()
)


V12_PRICE_LOOKUP = (
    V12_PRICE_LOOKUP
    .dropna(
        subset=[
            "Ticker",
            "Date",
            "Adj_Close",
        ]
    )
    .drop_duplicates(
        [
            "Ticker",
            "Date",
        ],
        keep="last",
    )
    .set_index(
        [
            "Ticker",
            "Date",
        ]
    )[
        "Adj_Close"
    ]
    .sort_index()
)


def v12_exact_price(ticker, date):

    ticker = str(
        ticker
    ).upper().strip()

    date = pd.Timestamp(
        date
    ).normalize()


    try:

        value = V12_PRICE_LOOKUP.loc[
            (
                ticker,
                date,
            )
        ]

    except KeyError:

        return np.nan


    if isinstance(
        value,
        pd.Series,
    ):
        value = value.iloc[-1]


    try:
        value = float(value)

    except Exception:
        return np.nan


    if (
        not np.isfinite(value)
        or
        value <= 0
    ):
        return np.nan


    return value


# ==============================================================================
# 26. EXECUTION PREFLIGHT
# ==============================================================================

V12_EXECUTION_DATES_FINAL = list(
    pd.to_datetime(
        V12_STATE_PANEL[
            "Execution_Date"
        ]
    )
)


V12_PREFLIGHT_ROWS = []
V12_UNRESOLVED_QUOTES = []


for i, execution_date in enumerate(
    V12_EXECUTION_DATES_FINAL
):

    execution_date = pd.Timestamp(
        execution_date
    ).normalize()


    target = V12_PREDECLARED_TARGETS[
        execution_date
    ]


    if i < len(
        V12_EXECUTION_DATES_FINAL
    ) - 1:

        next_execution_date = pd.Timestamp(
            V12_EXECUTION_DATES_FINAL[
                i + 1
            ]
        ).normalize()

    else:

        # Final research-date target has no completed forward holding period.
        # We only require its entry prices here.
        next_execution_date = pd.NaT


    missing_entry = 0
    missing_next = 0


    for ticker in target.keys():

        entry_price = v12_exact_price(
            ticker,
            execution_date,
        )


        if not np.isfinite(
            entry_price
        ):

            missing_entry += 1

            V12_UNRESOLVED_QUOTES.append(
                {
                    "Event":
                        i + 1,

                    "Ticker":
                        ticker,

                    "Quote_Type":
                        "ENTRY",

                    "Requested_Date":
                        execution_date,
                }
            )


        if pd.notna(
            next_execution_date
        ):

            next_price = v12_exact_price(
                ticker,
                next_execution_date,
            )


            if not np.isfinite(
                next_price
            ):

                missing_next += 1

                V12_UNRESOLVED_QUOTES.append(
                    {
                        "Event":
                            i + 1,

                        "Ticker":
                            ticker,

                        "Quote_Type":
                            "NEXT_REBALANCE",

                        "Requested_Date":
                            next_execution_date,
                    }
                )


    V12_PREFLIGHT_ROWS.append(
        {
            "Event":
                i + 1,

            "Signal_Date":
                V12_STATE_PANEL.loc[
                    i,
                    "Signal_Date",
                ],

            "Execution_Date":
                execution_date,

            "Next_Execution_Date":
                next_execution_date,

            "Frozen_Alpha_Available":
                bool(
                    V12_STATE_PANEL.loc[
                        i,
                        "Alpha_Sleeve_Available",
                    ]
                ),

            "Alpha_Names":
                int(
                    V12_STATE_PANEL.loc[
                        i,
                        "Alpha_Names",
                    ]
                ),

            "Predeclared_TQQQ_Weight_Pct":
                100.0
                *
                float(
                    V12_STATE_PANEL.loc[
                        i,
                        "Predeclared_TQQQ_Weight",
                    ]
                ),

            "Predeclared_Alpha_Weight_Pct":
                100.0
                *
                float(
                    V12_STATE_PANEL.loc[
                        i,
                        "Predeclared_Alpha_Weight",
                    ]
                ),

            "Portfolio_Names":
                int(
                    len(target)
                ),

            "Missing_Entry_Quotes":
                int(
                    missing_entry
                ),

            "Missing_Next_Rebalance_Quotes":
                int(
                    missing_next
                ),
        }
    )


V12_EXECUTION_PREFLIGHT = pd.DataFrame(
    V12_PREFLIGHT_ROWS
)


V12_TOTAL_MISSING_ENTRY = int(
    V12_EXECUTION_PREFLIGHT[
        "Missing_Entry_Quotes"
    ].sum()
)


V12_TOTAL_MISSING_EXIT = int(
    V12_EXECUTION_PREFLIGHT[
        "Missing_Next_Rebalance_Quotes"
    ].sum()
)


# ==============================================================================
# 27. STRICT PREFLIGHT VERDICT
# ==============================================================================

if (
    V12_TOTAL_MISSING_ENTRY > 0
    or
    V12_TOTAL_MISSING_EXIT > 0
):

    print(
        "\n[!] EXECUTION PREFLIGHT FOUND UNRESOLVED QUOTES."
    )


    display(
        V12_EXECUTION_PREFLIGHT
    )


    if len(
        V12_UNRESOLVED_QUOTES
    ) > 0:

        display(
            pd.DataFrame(
                V12_UNRESOLVED_QUOTES
            )
        )


    raise RuntimeError(
        "V12 stopped BEFORE performance calculation because "
        "execution-price preflight did not pass."
    )


print(
    "[+] V12 execution-price preflight passed."
)


# ==============================================================================
# 28. FROZEN SLEEVE HASH
# ==============================================================================

V12_SLEEVE_HASH_FRAME = (
    V12_FROZEN_ALPHA_SLEEVE_MATRIX
    .sort_index()
    .sort_index(
        axis=1
    )
)


V12_SLEEVE_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V12_SLEEVE_HASH_FRAME,
        index=True,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V12_FROZEN_ALPHA_SLEEVE_HASH = (
    hashlib.sha256(
        V12_SLEEVE_HASH_VALUES.tobytes()
    ).hexdigest()
)


# ==============================================================================
# 29. STATE PANEL HASH
# ==============================================================================

V12_STATE_HASH_COLUMNS = [
    "Signal_Date",
    "Execution_Date",
    "TQQQ_Long_Trend",
    "TQQQ_Medium_Trend",
    "TQQQ_Vol63",
    "Alpha_Sleeve_Available",
    "Alpha_Names",
    "Alpha_Effective_N",
    "Alpha_Max_Weight",
    "P_Long_Trend",
    "P_Medium_Trend",
    "P_Vol63",
    "P_Alpha_Effective_N",
    "P_Alpha_Max_Weight",
    "Predeclared_Alpha_Weight",
    "Predeclared_TQQQ_Weight",
]


V12_STATE_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V12_STATE_PANEL[
            V12_STATE_HASH_COLUMNS
        ],
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V12_STATE_PANEL_HASH = hashlib.sha256(
    V12_STATE_HASH_VALUES.tobytes()
).hexdigest()


V12_BLOCK2_PAYLOAD = {

    "contract_fingerprint":
        V12_RESEARCH_CONTRACT_FINGERPRINT,

    "frozen_alpha_sleeve_hash":
        V12_FROZEN_ALPHA_SLEEVE_HASH,

    "state_panel_hash":
        V12_STATE_PANEL_HASH,

    "v8_reconstruction_max_error":
        float(
            V12_V8_RECONSTRUCTION_MAX_ERROR
        ),

    "decisions":
        34,

    "missing_entry_quotes":
        V12_TOTAL_MISSING_ENTRY,

    "missing_next_rebalance_quotes":
        V12_TOTAL_MISSING_EXIT,

    "performance_calculated":
        False,
}


V12_BLOCK2_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V12_BLOCK2_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 30. OUTPUT
# ==============================================================================

print(
    "\n1) FROZEN V8 ALPHA-SLEEVE RESOLUTION AUDIT"
)


display(
    pd.DataFrame(
        {
            "Metric": [
                "Research decisions",
                "V8 matrix scale",
                "V8 alpha series scale",
                "V8 TQQQ series scale",
                "Portfolio row-sum max error",
                "TQQQ + Alpha identity max error",
                "Matrix TQQQ identity max error",
                "V8 exact reconstruction max error",
                "Recovered active alpha decisions",
                "Frozen alpha sleeve hash",
            ],

            "Value": [
                34,
                V12_MATRIX_SCALE,
                V12_ALPHA_SCALE,
                V12_TQQQ_SCALE,
                V12_MATRIX_SUM_MAX_ERROR,
                V12_CORE_ALPHA_IDENTITY_ERROR,
                V12_MATRIX_TQQQ_ERROR,
                V12_V8_RECONSTRUCTION_MAX_ERROR,
                int(
                    V12_FROZEN_ALPHA_AVAILABLE.sum()
                ),
                V12_FROZEN_ALPHA_SLEEVE_HASH,
            ],
        }
    )
)


print(
    "\n2) V12 CAUSAL STATE PANEL"
)


display(
    V12_STATE_PANEL[
        [
            "Signal_Date",
            "Execution_Date",
            "TQQQ_Long_Trend",
            "TQQQ_Medium_Trend",
            "TQQQ_Vol63",
            "Alpha_Sleeve_Available",
            "Alpha_Names",
            "Alpha_Effective_N",
            "Alpha_Max_Weight",
            "P_Long_Trend",
            "P_Medium_Trend",
            "P_Vol63",
            "P_Alpha_Effective_N",
            "P_Alpha_Max_Weight",
            "Predeclared_TQQQ_Weight",
            "Predeclared_Alpha_Weight",
        ]
    ].round(
        6
    )
)


print(
    "\n3) V12 PREDECLARED ALLOCATION SUMMARY"
)


V12_ALLOCATION_SUMMARY = pd.DataFrame(
    {
        "Metric": [
            "Mean Alpha weight pct",
            "Median Alpha weight pct",
            "Minimum Alpha weight pct",
            "Maximum Alpha weight pct",
            "Mean TQQQ weight pct",
            "Median TQQQ weight pct",
            "Alpha available decisions",
            "100% TQQQ decisions",
        ],

        "Value": [
            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_Alpha_Weight"
            ].mean(),

            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_Alpha_Weight"
            ].median(),

            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_Alpha_Weight"
            ].min(),

            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_Alpha_Weight"
            ].max(),

            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_TQQQ_Weight"
            ].mean(),

            100.0
            *
            V12_STATE_PANEL[
                "Predeclared_TQQQ_Weight"
            ].median(),

            int(
                V12_STATE_PANEL[
                    "Alpha_Sleeve_Available"
                ].sum()
            ),

            int(
                np.isclose(
                    V12_STATE_PANEL[
                        "Predeclared_Alpha_Weight"
                    ],
                    0.0,
                    atol=1e-14,
                ).sum()
            ),
        ],
    }
)


display(
    V12_ALLOCATION_SUMMARY.round(
        6
    )
)


print(
    "\n4) EXECUTION PREFLIGHT"
)


display(
    V12_EXECUTION_PREFLIGHT.round(
        6
    )
)


print(
    "\n5) EXECUTION PREFLIGHT SUMMARY"
)


display(
    pd.DataFrame(
        {
            "Metric": [
                "Research decisions",
                "Missing entry quotes",
                "Missing next-rebalance quotes",
                "Performance calculated",
            ],

            "Value": [
                34,
                V12_TOTAL_MISSING_ENTRY,
                V12_TOTAL_MISSING_EXIT,
                False,
            ],
        }
    )
)


# ==============================================================================
# FINAL PREDECLARED TARGET
# ==============================================================================

V12_FINAL_EXECUTION_DATE = pd.Timestamp(
    V12_STATE_PANEL[
        "Execution_Date"
    ].iloc[
        -1
    ]
).normalize()


V12_FINAL_TARGET_TABLE = (
    pd.Series(
        V12_PREDECLARED_TARGETS[
            V12_FINAL_EXECUTION_DATE
        ],
        name="Weight",
    )
    *
    100.0
).sort_values(
    ascending=False
).rename(
    "Weight_Pct"
).to_frame()


print(
    "\n6) FINAL PREDECLARED V12 TARGET"
)

print(
    "Execution date:",
    V12_FINAL_EXECUTION_DATE.date()
)


display(
    V12_FINAL_TARGET_TABLE
    .head(
        50
    )
    .round(
        6
    )
)


print(
    "\n7) V12 BLOCK 2 RESEARCH FINGERPRINT"
)

print(
    V12_BLOCK2_RESEARCH_FINGERPRINT
)


print("\nINTEGRITY:")

print(
    "[+] Frozen V8 sleeve reconstruction remains unchanged."
)

print(
    "[+] Signal dates use the actual prior TQQQ trading session."
)

print(
    "[+] State variables use signal-date information only."
)

print(
    "[+] Expanding percentile normalization is causal."
)

print(
    "[+] Locked median-state allocation rule was used unchanged."
)

print(
    "[+] No model was fitted."
)

print(
    "[+] No stock-selection rule was changed."
)

print(
    "[+] No minimum stock weight."
)

print(
    "[+] No maximum stock weight."
)

print(
    "[+] No Top-K."
)

print(
    "[+] No sector cap."
)

print(
    "[+] No risk cap."
)

print(
    "[+] No TQQQ floor."
)

print(
    "[+] No alpha cap."
)

print(
    "[+] No cash."
)

print(
    "[+] No leverage above 100%."
)

print(
    "[+] Exact execution preflight passed."
)

print(
    "[+] NO V12 PORTFOLIO PERFORMANCE HAS BEEN CALCULATED."
)


print("\nNEXT:")

print(
    "V12 BLOCK 3 — ONE-SHOT EXACT ECONOMIC TEST + "
    "DAILY NAV + TQQQ RELATIVE ROBUSTNESS."
)

print("=" * 140)
