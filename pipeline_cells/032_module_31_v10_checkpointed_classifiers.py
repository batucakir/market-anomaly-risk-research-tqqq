# MODULE 31 — V10 CHECKPOINTED CLASSIFIERS
# Run in the same notebook, in module order.

# ==============================================================================
# V10 — BLOCK 2
# CHECKPOINTED SEVEN-HORIZON TQQQ-RELATIVE HGB CLASSIFIERS
# ==============================================================================
#
# PURPOSE
# -------
# For every stock and every horizon:
#
#       y_h = 1  if stock beats TQQQ
#             0  otherwise
#
# The model estimates:
#
#       P(stock beats TQQQ over horizon h | information at signal date)
#
#
# IMPORTANT
# ---------
# THIS BLOCK CALCULATES NO PORTFOLIO PERFORMANCE.
#
# It only produces strictly causal, walk-forward probability forecasts.
#
#
# CAUSAL TRAINING RULE
# --------------------
# For each evaluation signal date:
#
#   - use ONLY dates strictly before the signal date;
#   - require target end date <= signal date;
#   - use the most recent 252 fully matured signal dates;
#   - fit seven independently frozen HGB classifiers;
#   - predict the current PIT-eligible feature-complete cross-section.
#
#
# MULTI-HORIZON COMPOSITE
# -----------------------
# After all seven probabilities are generated:
#
#       Composite_Prob_Beat_TQQQ
#           = median of the seven horizon probabilities
#
# No horizon is removed.
# No horizon receives a performance-selected weight.
#
#
# CACHE SAFETY
# ------------
# Every checkpoint validates:
#
#   - V10 research-contract fingerprint
#   - V10 Block-2 specification fingerprint
#   - V10 infrastructure hash
#   - exact signal date
#   - exact current ticker cross-section
#   - required probability columns
#   - probability bounds
#
# A mismatched checkpoint is ignored and refitted.
#
# ==============================================================================


import gc
import hashlib
import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from IPython.display import display
from sklearn.ensemble import HistGradientBoostingClassifier


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V10_B2_REQUIRED = [
    "V10_RESEARCH_CONTRACT_FINGERPRINT",
    "V10_INFRA_DATA_HASH",
    "V10_RESEARCH_CONTRACT",
    "V10_CLASSIFIER_PARAMS",
    "V10_MODEL_FEATURES",
    "V10_TARGET_HORIZONS",
    "V10_TRAIN_LOOKBACK_SESSIONS",
    "V10_EVALUATION_CALENDAR",
    "V10_BASE_PANEL",
]


V10_B2_MISSING = [
    name
    for name in V10_B2_REQUIRED
    if name not in globals()
]


if V10_B2_MISSING:

    raise RuntimeError(
        "V10 Block 2 is missing required objects: "
        f"{V10_B2_MISSING}"
    )


print("=" * 138)
print("V10 — BLOCK 2")
print("CHECKPOINTED SEVEN-HORIZON TQQQ-RELATIVE HGB CLASSIFIERS")
print("=" * 138)

print("\nNO PORTFOLIO PERFORMANCE WILL BE CALCULATED IN THIS BLOCK.")


# ==============================================================================
# 1. DATE NORMALIZATION HELPER
# ==============================================================================

def v10b2_normalize_dates(series):

    values = pd.to_datetime(
        series,
        errors="coerce",
    )

    try:

        if values.dt.tz is not None:

            values = (
                values
                .dt.tz_localize(None)
            )

    except (AttributeError, TypeError):

        pass

    return values.dt.normalize()


# ==============================================================================
# 2. SOURCE MODEL PANEL
# ==============================================================================
#
# Prefer the already validated V9 model panel because V10 inherits the
# accepted PIT / feature infrastructure.
#
# If it is unavailable, fall back to V10_BASE_PANEL only if that object
# already contains every required model field.
#
# ==============================================================================

V10_REQUIRED_MODEL_COLUMNS = (
    [
        "Date",
        "Execution_Date",
        "Ticker",
    ]
    +
    list(
        V10_MODEL_FEATURES
    )
    +
    [
        f"Target_End_Date_{horizon}"
        for horizon
        in V10_TARGET_HORIZONS
    ]
    +
    [
        f"Log_Relative_Wealth_{horizon}"
        for horizon
        in V10_TARGET_HORIZONS
    ]
)


if (
    "V9_MODEL_PANEL" in globals()
    and
    all(
        column in V9_MODEL_PANEL.columns
        for column in V10_REQUIRED_MODEL_COLUMNS
    )
):

    V10_MODEL_PANEL = (
        V9_MODEL_PANEL
        .copy()
    )

    V10_MODEL_PANEL_SOURCE = (
        "V9_MODEL_PANEL"
    )


elif all(
    column in V10_BASE_PANEL.columns
    for column in V10_REQUIRED_MODEL_COLUMNS
):

    V10_MODEL_PANEL = (
        V10_BASE_PANEL
        .copy()
    )

    V10_MODEL_PANEL_SOURCE = (
        "V10_BASE_PANEL"
    )


else:

    missing_from_v9 = (
        [
            column
            for column in V10_REQUIRED_MODEL_COLUMNS
            if (
                "V9_MODEL_PANEL" not in globals()
                or
                column not in V9_MODEL_PANEL.columns
            )
        ]
    )

    missing_from_base = (
        [
            column
            for column in V10_REQUIRED_MODEL_COLUMNS
            if column not in V10_BASE_PANEL.columns
        ]
    )

    raise RuntimeError(
        "No complete V10 model panel is available.\n"
        f"Missing from V9_MODEL_PANEL: {missing_from_v9[:20]}\n"
        f"Missing from V10_BASE_PANEL: {missing_from_base[:20]}"
    )


print(
    "\nModel-panel source:",
    V10_MODEL_PANEL_SOURCE,
)


# ==============================================================================
# 3. NORMALIZE MODEL PANEL
# ==============================================================================

V10_MODEL_PANEL["Date"] = (
    v10b2_normalize_dates(
        V10_MODEL_PANEL[
            "Date"
        ]
    )
)


V10_MODEL_PANEL[
    "Execution_Date"
] = (
    v10b2_normalize_dates(
        V10_MODEL_PANEL[
            "Execution_Date"
        ]
    )
)


for horizon_name in V10_TARGET_HORIZONS:

    target_end_column = (
        f"Target_End_Date_{horizon_name}"
    )

    V10_MODEL_PANEL[
        target_end_column
    ] = (
        v10b2_normalize_dates(
            V10_MODEL_PANEL[
                target_end_column
            ]
        )
    )


V10_MODEL_PANEL[
    "Ticker"
] = (
    V10_MODEL_PANEL[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


V10_MODEL_PANEL = (
    V10_MODEL_PANEL
    .dropna(
        subset=[
            "Date",
            "Ticker",
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
            "Date",
            "Ticker",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 4. NORMALIZE FEATURE COLUMNS WITHOUT CREATING A HUGE TEMPORARY MATRIX
# ==============================================================================

for feature in V10_MODEL_FEATURES:

    V10_MODEL_PANEL[
        feature
    ] = pd.to_numeric(
        V10_MODEL_PANEL[
            feature
        ],
        errors="coerce",
    )

    values = (
        V10_MODEL_PANEL[
            feature
        ]
        .to_numpy(
            dtype=float,
            copy=False,
        )
    )

    finite = np.isfinite(
        values
    )

    if not finite.all():

        V10_MODEL_PANEL.loc[
            ~finite,
            feature,
        ] = np.nan


# ==============================================================================
# 5. FEATURE-COMPLETE MASK
# ==============================================================================

V10_FEATURE_COMPLETE = np.ones(
    len(
        V10_MODEL_PANEL
    ),
    dtype=bool,
)


for feature in V10_MODEL_FEATURES:

    V10_FEATURE_COMPLETE &= (
        V10_MODEL_PANEL[
            feature
        ]
        .notna()
        .to_numpy()
    )


V10_MODEL_PANEL[
    "__V10_FEATURE_COMPLETE"
] = V10_FEATURE_COMPLETE


del V10_FEATURE_COMPLETE


# ==============================================================================
# 6. BUILD BINARY LABELS
# ==============================================================================

V10_LABEL_COLUMNS = {}


for horizon_name in V10_TARGET_HORIZONS:

    source_target = (
        f"Log_Relative_Wealth_{horizon_name}"
    )

    label_column = (
        f"Beat_TQQQ_{horizon_name}"
    )


    source_values = pd.to_numeric(
        V10_MODEL_PANEL[
            source_target
        ],
        errors="coerce",
    )


    label = pd.Series(
        np.nan,
        index=V10_MODEL_PANEL.index,
        dtype=float,
    )


    valid_target = (
        source_values.notna()
        &
        np.isfinite(
            source_values.to_numpy(
                dtype=float,
                copy=False,
            )
        )
    )


    label.loc[
        valid_target
    ] = (
        source_values.loc[
            valid_target
        ]
        >
        0.0
    ).astype(
        np.int8
    )


    V10_MODEL_PANEL[
        label_column
    ] = label


    V10_LABEL_COLUMNS[
        horizon_name
    ] = label_column


# ==============================================================================
# 7. EVALUATION CALENDAR
# ==============================================================================

V10_B2_EVALUATION_CALENDAR = (
    V10_EVALUATION_CALENDAR
    .copy()
)


V10_B2_EVALUATION_CALENDAR[
    "Date"
] = (
    v10b2_normalize_dates(
        V10_B2_EVALUATION_CALENDAR[
            "Date"
        ]
    )
)


V10_B2_EVALUATION_CALENDAR[
    "Execution_Date"
] = (
    v10b2_normalize_dates(
        V10_B2_EVALUATION_CALENDAR[
            "Execution_Date"
        ]
    )
)


V10_B2_EVALUATION_CALENDAR = (
    V10_B2_EVALUATION_CALENDAR
    .dropna(
        subset=[
            "Date",
            "Execution_Date",
        ]
    )
    .drop_duplicates(
        "Date",
        keep="last",
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


V10_EVALUATION_DATES = [
    pd.Timestamp(date)
    for date
    in V10_B2_EVALUATION_CALENDAR[
        "Date"
    ].tolist()
]


if len(
    V10_EVALUATION_DATES
) != 34:

    raise RuntimeError(
        "V10 Block 2 expected 34 evaluation decisions, "
        f"found {len(V10_EVALUATION_DATES)}."
    )


# ==============================================================================
# 8. VERIFY CURRENT CROSS-SECTIONS
# ==============================================================================

V10_CURRENT_FEATURE_COUNTS = (
    V10_MODEL_PANEL.loc[
        V10_MODEL_PANEL[
            "__V10_FEATURE_COMPLETE"
        ]
    ]
    .groupby(
        "Date"
    )[
        "Ticker"
    ]
    .nunique()
)


V10_CURRENT_AUDIT_ROWS = []


for signal_date in V10_EVALUATION_DATES:

    current_count = int(
        V10_CURRENT_FEATURE_COUNTS.get(
            signal_date,
            0,
        )
    )


    if current_count <= 0:

        raise RuntimeError(
            "No feature-complete current stocks at "
            f"{signal_date.date()}."
        )


    V10_CURRENT_AUDIT_ROWS.append(
        {
            "Signal_Date":
                signal_date,

            "Feature_Complete_Stocks":
                current_count,

            "Status":
                "PASS",
        }
    )


V10_CURRENT_FEATURE_AUDIT = pd.DataFrame(
    V10_CURRENT_AUDIT_ROWS
)


# ==============================================================================
# 9. DATE-LEVEL TARGET-END METADATA
# ==============================================================================

V10_DATE_TARGET_META = (
    V10_MODEL_PANEL[
        [
            "Date",
        ]
        +
        [
            f"Target_End_Date_{horizon}"
            for horizon
            in V10_TARGET_HORIZONS
        ]
    ]
    .drop_duplicates(
        "Date",
        keep="last",
    )
    .sort_values(
        "Date"
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 10. PRECOMPUTE VALID TRAINING ROW COUNTS BY DATE / HORIZON
# ==============================================================================

V10_HORIZON_DAILY_TRAIN_STATS = {}


for horizon_name in V10_TARGET_HORIZONS:

    label_column = (
        V10_LABEL_COLUMNS[
            horizon_name
        ]
    )


    valid_mask = (
        V10_MODEL_PANEL[
            "__V10_FEATURE_COMPLETE"
        ]
        &
        V10_MODEL_PANEL[
            label_column
        ]
        .notna()
    )


    temp = (
        V10_MODEL_PANEL.loc[
            valid_mask,
            [
                "Date",
                label_column,
            ],
        ]
        .copy()
    )


    temp[
        "__Positive"
    ] = (
        temp[
            label_column
        ]
        .astype(
            np.int8
        )
    )


    daily = (
        temp
        .groupby(
            "Date"
        )
        .agg(
            Rows=(
                label_column,
                "size",
            ),
            Positives=(
                "__Positive",
                "sum",
            ),
        )
    )


    daily[
        "Negatives"
    ] = (
        daily[
            "Rows"
        ]
        -
        daily[
            "Positives"
        ]
    )


    V10_HORIZON_DAILY_TRAIN_STATS[
        horizon_name
    ] = daily


    del temp


# ==============================================================================
# 11. SELECT EXACT 252 FULLY MATURED TRAINING DATES
# ==============================================================================

V10_SELECTED_TRAIN_DATES = {}

V10_PREFIT_AUDIT_ROWS = []


for signal_date in V10_EVALUATION_DATES:

    current_rows = (
        int(
            V10_CURRENT_FEATURE_COUNTS.get(
                signal_date,
                0,
            )
        )
    )


    for horizon_name in V10_TARGET_HORIZONS:

        target_end_column = (
            f"Target_End_Date_{horizon_name}"
        )


        matured_dates = (
            V10_DATE_TARGET_META.loc[
                (
                    V10_DATE_TARGET_META[
                        "Date"
                    ]
                    <
                    signal_date
                )
                &
                (
                    V10_DATE_TARGET_META[
                        target_end_column
                    ]
                    .notna()
                )
                &
                (
                    V10_DATE_TARGET_META[
                        target_end_column
                    ]
                    <=
                    signal_date
                ),
                "Date",
            ]
            .drop_duplicates()
            .sort_values()
        )


        if (
            len(
                matured_dates
            )
            <
            V10_TRAIN_LOOKBACK_SESSIONS
        ):

            raise RuntimeError(
                "Insufficient fully matured history for "
                f"{signal_date.date()} / {horizon_name}: "
                f"{len(matured_dates)} dates."
            )


        selected_dates = (
            matured_dates.iloc[
                -V10_TRAIN_LOOKBACK_SESSIONS:
            ]
            .tolist()
        )


        if len(
            selected_dates
        ) != V10_TRAIN_LOOKBACK_SESSIONS:

            raise RuntimeError(
                "Training-date selection failed."
            )


        V10_SELECTED_TRAIN_DATES[
            (
                signal_date,
                horizon_name,
            )
        ] = tuple(
            pd.Timestamp(date)
            for date
            in selected_dates
        )


        daily_stats = (
            V10_HORIZON_DAILY_TRAIN_STATS[
                horizon_name
            ]
            .reindex(
                selected_dates
            )
            .fillna(0)
        )


        training_rows = int(
            daily_stats[
                "Rows"
            ].sum()
        )


        positives = int(
            daily_stats[
                "Positives"
            ].sum()
        )


        negatives = int(
            daily_stats[
                "Negatives"
            ].sum()
        )


        if training_rows <= 0:

            raise RuntimeError(
                "Zero training rows for "
                f"{signal_date.date()} / {horizon_name}."
            )


        if (
            positives <= 0
            or
            negatives <= 0
        ):

            raise RuntimeError(
                "HGB classifier would have only one class for "
                f"{signal_date.date()} / {horizon_name}. "
                f"Positive={positives}, Negative={negatives}"
            )


        positive_rate = (
            positives
            /
            training_rows
        )


        V10_PREFIT_AUDIT_ROWS.append(
            {
                "Signal_Date":
                    signal_date,

                "Horizon":
                    horizon_name,

                "Training_Dates":
                    len(
                        selected_dates
                    ),

                "Training_Rows":
                    training_rows,

                "Positive_Rows":
                    positives,

                "Negative_Rows":
                    negatives,

                "Positive_Rate":
                    positive_rate,

                "Prediction_Rows":
                    current_rows,

                "Status":
                    "PASS",
            }
        )


V10_PREFIT_AUDIT = pd.DataFrame(
    V10_PREFIT_AUDIT_ROWS
)


print(
    "\n1) COMPLETE PRE-FIT AUDIT"
)


display(
    V10_PREFIT_AUDIT[
        [
            "Signal_Date",
            "Horizon",
            "Training_Dates",
            "Training_Rows",
            "Positive_Rate",
            "Prediction_Rows",
            "Status",
        ]
    ]
    .head(
        20
    )
    .round(
        6
    )
)


print(
    "\n[+] ALL FEATURE / MATURITY / TWO-CLASS PREFIT CHECKS PASSED."
)


# ==============================================================================
# RUNTIME COMPATIBILITY — SCIKIT-LEARN LOSS NAME
# ==============================================================================
# Keep V10_CLASSIFIER_PARAMS and every research/specification fingerprint
# unchanged. scikit-learn 1.0 calls the same binary logistic loss
# "binary_crossentropy"; later releases call it "log_loss". Only the keyword
# passed to the installed library is translated after a pre-fit validation.

def v10_validate_runtime_classifier_params(params):
    probe = HistGradientBoostingClassifier(**params)
    if hasattr(probe, "_validate_parameters"):
        probe._validate_parameters()
    else:
        probe.fit(
            np.asarray([[0.0], [1.0], [2.0], [3.0]]),
            np.asarray([0, 0, 1, 1], dtype=np.int8),
        )


V10_RUNTIME_CLASSIFIER_PARAMS = dict(V10_CLASSIFIER_PARAMS)
V10_RUNTIME_LOSS_TRANSLATED = False
try:
    v10_validate_runtime_classifier_params(V10_RUNTIME_CLASSIFIER_PARAMS)
except ValueError as original_error:
    if V10_RUNTIME_CLASSIFIER_PARAMS.get("loss") != "log_loss":
        raise
    candidate_params = dict(V10_RUNTIME_CLASSIFIER_PARAMS)
    candidate_params["loss"] = "binary_crossentropy"
    try:
        v10_validate_runtime_classifier_params(candidate_params)
    except Exception:
        raise original_error
    V10_RUNTIME_CLASSIFIER_PARAMS = candidate_params
    V10_RUNTIME_LOSS_TRANSLATED = True

if V10_CLASSIFIER_PARAMS.get("loss") != "log_loss":
    raise RuntimeError("The frozen V10 research loss specification changed.")
print(
    "[V10 runtime compatibility] frozen loss=log_loss | library loss="
    f"{V10_RUNTIME_CLASSIFIER_PARAMS['loss']} | "
    f"translated={V10_RUNTIME_LOSS_TRANSLATED}"
)


# ==============================================================================
# 12. BLOCK-2 SPECIFICATION FINGERPRINT
# ==============================================================================

V10_BLOCK2_CACHE_SCHEMA_VERSION = (
    "V10_B2_CLASSIFIER_V1_2026_09_11"
)


V10_BLOCK2_SPEC = {

    "schema_version":
        V10_BLOCK2_CACHE_SCHEMA_VERSION,

    "research_contract_fingerprint":
        V10_RESEARCH_CONTRACT_FINGERPRINT,

    "infrastructure_hash":
        V10_INFRA_DATA_HASH,

    "model_family":
        "HistGradientBoostingClassifier",

    "classifier_params":
        V10_CLASSIFIER_PARAMS,

    "features":
        list(
            V10_MODEL_FEATURES
        ),

    "target_horizons":
        V10_TARGET_HORIZONS,

    "target":
        "BINARY_STOCK_BEATS_TQQQ",

    "training_rule":
        (
            "LAST_252_FULLY_MATURED_SIGNAL_DATES_"
            "TARGET_END_LE_SIGNAL_DATE"
        ),

    "current_prediction_rule":
        "CURRENT_SIGNAL_DATE_FEATURE_COMPLETE_PIT_STOCKS",

    "multi_horizon_composite":
        "MEDIAN_OF_SEVEN_PROBABILITIES",

    "portfolio_performance_calculated":
        False,
}


V10_BLOCK2_SPEC_STRING = json.dumps(
    V10_BLOCK2_SPEC,
    sort_keys=True,
    default=str,
)


V10_BLOCK2_SPEC_FINGERPRINT = (
    hashlib.sha256(
        V10_BLOCK2_SPEC_STRING.encode(
            "utf-8"
        )
    )
    .hexdigest()
)


print(
    "\nV10 Block 2 specification fingerprint:"
)

print(
    V10_BLOCK2_SPEC_FINGERPRINT
)


# ==============================================================================
# 13. CHECKPOINT DIRECTORY
# ==============================================================================

V10_CACHE_ROOT = (
    Path.home()
    /
    "Downloads"
    /
    "restored_v10_cache"
)


V10_CACHE_DIR = (
    V10_CACHE_ROOT
    /
    (
        "block2_"
        +
        V10_BLOCK2_SPEC_FINGERPRINT[
            :16
        ]
        +
        "_"
        +
        V10_INFRA_DATA_HASH[
            :12
        ]
    )
)


V10_CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


if not os.access(
    V10_CACHE_DIR,
    os.W_OK,
):

    raise RuntimeError(
        "V10 checkpoint directory is not writable: "
        f"{V10_CACHE_DIR}"
    )


print(
    "\nCheckpoint directory:"
)

print(
    V10_CACHE_DIR
)

print(
    "[+] Checkpoint directory is writable."
)


# ==============================================================================
# 14. CHECKPOINT HELPERS
# ==============================================================================

def v10_ticker_hash(
    tickers,
):

    normalized = sorted(
        str(ticker)
        .upper()
        .strip()

        for ticker
        in tickers
    )


    payload = "\n".join(
        normalized
    )


    return (
        hashlib.sha256(
            payload.encode(
                "utf-8"
            )
        )
        .hexdigest()
    )


def v10_checkpoint_path(
    signal_date,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    return (
        V10_CACHE_DIR
        /
        (
            "decision_"
            +
            signal_date.strftime(
                "%Y%m%d"
            )
            +
            ".pkl"
        )
    )


def v10_atomic_pickle_dump(
    payload,
    path,
):

    path = Path(
        path
    )


    temp_path = path.with_suffix(
        ".tmp"
    )


    with open(
        temp_path,
        "wb",
    ) as handle:

        pickle.dump(
            payload,
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )


    os.replace(
        temp_path,
        path,
    )


def v10_load_checkpoint(
    signal_date,
):

    path = (
        v10_checkpoint_path(
            signal_date
        )
    )


    if not path.exists():

        return None


    try:

        with open(
            path,
            "rb",
        ) as handle:

            payload = pickle.load(
                handle
            )

    except Exception:

        return None


    return payload


# ==============================================================================
# 15. CURRENT CROSS-SECTION HELPER
# ==============================================================================

V10_MODEL_PANEL_BY_DATE = (
    V10_MODEL_PANEL
    .set_index(
        "Date",
        drop=False,
    )
    .sort_index()
)


def v10_current_cross_section(
    signal_date,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    try:

        current = (
            V10_MODEL_PANEL_BY_DATE.loc[
                [
                    signal_date
                ]
            ]
            .copy()
        )

    except KeyError:

        raise RuntimeError(
            "Signal date absent from V10 model panel: "
            f"{signal_date.date()}"
        )


    current = (
        current[
            current[
                "__V10_FEATURE_COMPLETE"
            ]
        ]
        .drop_duplicates(
            "Ticker",
            keep="last",
        )
        .sort_values(
            "Ticker"
        )
        .reset_index(
            drop=True
        )
    )


    if current.empty:

        raise RuntimeError(
            "No current prediction rows for "
            f"{signal_date.date()}."
        )


    execution_dates = (
        current[
            "Execution_Date"
        ]
        .dropna()
        .unique()
    )


    if len(
        execution_dates
    ) != 1:

        raise RuntimeError(
            "Current signal date does not map to exactly "
            f"one execution date: {signal_date.date()}"
        )


    return current


# ==============================================================================
# 16. CHECKPOINT VALIDATION
# ==============================================================================

V10_PROBABILITY_COLUMNS = [
    f"Prob_Beat_TQQQ_{horizon}"
    for horizon
    in V10_TARGET_HORIZONS
]


V10_COMPOSITE_COLUMN = (
    "Composite_Prob_Beat_TQQQ"
)


def v10_checkpoint_is_valid(
    payload,
    signal_date,
    current,
):

    if not isinstance(
        payload,
        dict,
    ):

        return False


    required_keys = [
        "schema_version",
        "block2_spec_fingerprint",
        "research_contract_fingerprint",
        "infrastructure_hash",
        "signal_date",
        "current_ticker_hash",
        "predictions",
        "fit_audit",
    ]


    if any(
        key not in payload
        for key in required_keys
    ):

        return False


    if (
        payload[
            "schema_version"
        ]
        !=
        V10_BLOCK2_CACHE_SCHEMA_VERSION
    ):

        return False


    if (
        payload[
            "block2_spec_fingerprint"
        ]
        !=
        V10_BLOCK2_SPEC_FINGERPRINT
    ):

        return False


    if (
        payload[
            "research_contract_fingerprint"
        ]
        !=
        V10_RESEARCH_CONTRACT_FINGERPRINT
    ):

        return False


    if (
        payload[
            "infrastructure_hash"
        ]
        !=
        V10_INFRA_DATA_HASH
    ):

        return False


    if (
        pd.Timestamp(
            payload[
                "signal_date"
            ]
        ).normalize()
        !=
        pd.Timestamp(
            signal_date
        ).normalize()
    ):

        return False


    current_hash = (
        v10_ticker_hash(
            current[
                "Ticker"
            ]
            .tolist()
        )
    )


    if (
        payload[
            "current_ticker_hash"
        ]
        !=
        current_hash
    ):

        return False


    predictions = (
        payload[
            "predictions"
        ]
    )


    audit = (
        payload[
            "fit_audit"
        ]
    )


    if not isinstance(
        predictions,
        pd.DataFrame,
    ):

        return False


    if not isinstance(
        audit,
        pd.DataFrame,
    ):

        return False


    required_prediction_columns = (
        [
            "Date",
            "Execution_Date",
            "Ticker",
        ]
        +
        V10_PROBABILITY_COLUMNS
        +
        [
            V10_COMPOSITE_COLUMN
        ]
    )


    if any(
        column not in predictions.columns
        for column in required_prediction_columns
    ):

        return False


    if (
        len(
            predictions
        )
        !=
        len(
            current
        )
    ):

        return False


    if predictions.duplicated(
        "Ticker"
    ).any():

        return False


    if set(
        predictions[
            "Ticker"
        ]
    ) != set(
        current[
            "Ticker"
        ]
    ):

        return False


    if (
        set(
            audit[
                "Horizon"
            ]
        )
        !=
        set(
            V10_TARGET_HORIZONS
        )
    ):

        return False


    probability_matrix = (
        predictions[
            V10_PROBABILITY_COLUMNS
            +
            [
                V10_COMPOSITE_COLUMN
            ]
        ]
        .to_numpy(
            dtype=float
        )
    )


    if not np.isfinite(
        probability_matrix
    ).all():

        return False


    if (
        probability_matrix < 0.0
    ).any():

        return False


    if (
        probability_matrix > 1.0
    ).any():

        return False


    return True


# ==============================================================================
# 17. VALID-CHECKPOINT AUDIT BEFORE FITTING
# ==============================================================================

V10_VALID_CACHE_DATES = []

V10_INVALID_CACHE_DATES = []


for signal_date in V10_EVALUATION_DATES:

    current = (
        v10_current_cross_section(
            signal_date
        )
    )


    payload = (
        v10_load_checkpoint(
            signal_date
        )
    )


    if (
        payload is not None
        and
        v10_checkpoint_is_valid(
            payload=payload,
            signal_date=signal_date,
            current=current,
        )
    ):

        V10_VALID_CACHE_DATES.append(
            signal_date
        )


    else:

        if payload is not None:

            invalid_path = (
                v10_checkpoint_path(
                    signal_date
                )
            )


            try:

                invalid_path.unlink()

            except FileNotFoundError:

                pass


        V10_INVALID_CACHE_DATES.append(
            signal_date
        )


print(
    f"\nExisting valid checkpoints: "
    f"{len(V10_VALID_CACHE_DATES)}/"
    f"{len(V10_EVALUATION_DATES)}"
)

print(
    "Remaining decisions to fit:",
    len(
        V10_INVALID_CACHE_DATES
    ),
)


# ==============================================================================
# 18. FIT / LOAD EVERY DECISION
# ==============================================================================

V10_DECISION_PREDICTIONS = []

V10_MODEL_FIT_AUDIT_PARTS = []


for decision_number, signal_date in enumerate(
    V10_EVALUATION_DATES,
    start=1,
):

    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    current = (
        v10_current_cross_section(
            signal_date
        )
    )


    checkpoint = (
        v10_load_checkpoint(
            signal_date
        )
    )


    if (
        checkpoint is not None
        and
        v10_checkpoint_is_valid(
            payload=checkpoint,
            signal_date=signal_date,
            current=current,
        )
    ):

        print(
            f"[V10] Decision "
            f"{decision_number:02d}/"
            f"{len(V10_EVALUATION_DATES):02d} "
            f"| signal={signal_date.date()} "
            f"| stocks={len(current):,} "
            f"| CACHE"
        )


        V10_DECISION_PREDICTIONS.append(
            checkpoint[
                "predictions"
            ]
            .copy()
        )


        V10_MODEL_FIT_AUDIT_PARTS.append(
            checkpoint[
                "fit_audit"
            ]
            .copy()
        )


        continue


    # ==========================================================================
    # NEW FIT
    # ==========================================================================

    print(
        f"[V10] Decision "
        f"{decision_number:02d}/"
        f"{len(V10_EVALUATION_DATES):02d} "
        f"| signal={signal_date.date()} "
        f"| stocks={len(current):,} "
        f"| FITTING"
    )


    execution_date = pd.Timestamp(
        current[
            "Execution_Date"
        ].iloc[
            0
        ]
    ).normalize()


    prediction_frame = pd.DataFrame(
        {
            "Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Ticker":
                current[
                    "Ticker"
                ]
                .to_numpy(),
        }
    )


    current_X = (
        current[
            list(
                V10_MODEL_FEATURES
            )
        ]
        .to_numpy(
            dtype=np.float32,
            copy=True,
        )
    )


    if not np.isfinite(
        current_X
    ).all():

        raise RuntimeError(
            "Non-finite current feature matrix after "
            f"feature-complete filtering: {signal_date.date()}"
        )


    decision_audit_rows = []


    for horizon_name in V10_TARGET_HORIZONS:

        label_column = (
            V10_LABEL_COLUMNS[
                horizon_name
            ]
        )


        selected_dates = (
            V10_SELECTED_TRAIN_DATES[
                (
                    signal_date,
                    horizon_name,
                )
            ]
        )


        try:

            training = (
                V10_MODEL_PANEL_BY_DATE.loc[
                    list(
                        selected_dates
                    )
                ]
                .copy()
            )

        except KeyError as error:

            raise RuntimeError(
                "A selected training date disappeared from "
                f"the model panel: {signal_date.date()} / "
                f"{horizon_name}"
            ) from error


        training = (
            training[
                training[
                    "__V10_FEATURE_COMPLETE"
                ]
                &
                training[
                    label_column
                ]
                .notna()
            ]
        )


        if training.empty:

            raise RuntimeError(
                "Empty training sample for "
                f"{signal_date.date()} / {horizon_name}"
            )


        actual_training_dates = (
            training[
                "Date"
            ]
            .drop_duplicates()
            .nunique()
        )


        if (
            actual_training_dates
            !=
            V10_TRAIN_LOOKBACK_SESSIONS
        ):

            raise RuntimeError(
                "Training sample lost one or more selected dates for "
                f"{signal_date.date()} / {horizon_name}: "
                f"{actual_training_dates}"
            )


        X_train = (
            training[
                list(
                    V10_MODEL_FEATURES
                )
            ]
            .to_numpy(
                dtype=np.float32,
                copy=True,
            )
        )


        y_train = (
            training[
                label_column
            ]
            .to_numpy(
                dtype=np.int8,
                copy=True,
            )
        )


        if not np.isfinite(
            X_train
        ).all():

            raise RuntimeError(
                "Non-finite training feature matrix for "
                f"{signal_date.date()} / {horizon_name}"
            )


        classes = np.unique(
            y_train
        )


        if not np.array_equal(
            classes,
            np.array(
                [
                    0,
                    1,
                ],
                dtype=np.int8,
            )
        ):

            raise RuntimeError(
                "Classifier training sample does not contain "
                "both classes for "
                f"{signal_date.date()} / {horizon_name}. "
                f"Classes={classes.tolist()}"
            )


        classifier = (
            HistGradientBoostingClassifier(
                **V10_RUNTIME_CLASSIFIER_PARAMS
            )
        )


        classifier.fit(
            X_train,
            y_train,
        )


        positive_class_index = np.where(
            classifier.classes_
            ==
            1
        )[0]


        if len(
            positive_class_index
        ) != 1:

            raise RuntimeError(
                "Could not identify positive HGB class."
            )


        probabilities = (
            classifier
            .predict_proba(
                current_X
            )[
                :,
                int(
                    positive_class_index[
                        0
                    ]
                )
            ]
        )


        probabilities = np.asarray(
            probabilities,
            dtype=float,
        )


        if not np.isfinite(
            probabilities
        ).all():

            raise RuntimeError(
                "Classifier produced non-finite probabilities for "
                f"{signal_date.date()} / {horizon_name}"
            )


        if (
            probabilities < 0.0
        ).any() or (
            probabilities > 1.0
        ).any():

            raise RuntimeError(
                "Classifier produced probabilities outside [0,1]."
            )


        prediction_column = (
            f"Prob_Beat_TQQQ_{horizon_name}"
        )


        prediction_frame[
            prediction_column
        ] = probabilities


        positive_rate = float(
            y_train.mean()
        )


        decision_audit_rows.append(
            {
                "Signal_Date":
                    signal_date,

                "Execution_Date":
                    execution_date,

                "Horizon":
                    horizon_name,

                "Training_Dates":
                    int(
                        actual_training_dates
                    ),

                "Training_Rows":
                    int(
                        len(
                            training
                        )
                    ),

                "Positive_Rows":
                    int(
                        y_train.sum()
                    ),

                "Negative_Rows":
                    int(
                        len(
                            y_train
                        )
                        -
                        y_train.sum()
                    ),

                "Training_Positive_Rate":
                    positive_rate,

                "Prediction_Rows":
                    int(
                        len(
                            current
                        )
                    ),

                "Mean_Predicted_Probability":
                    float(
                        np.mean(
                            probabilities
                        )
                    ),

                "Median_Predicted_Probability":
                    float(
                        np.median(
                            probabilities
                        )
                    ),

                "Std_Predicted_Probability":
                    float(
                        np.std(
                            probabilities,
                            ddof=0,
                        )
                    ),

                "Min_Predicted_Probability":
                    float(
                        np.min(
                            probabilities
                        )
                    ),

                "Max_Predicted_Probability":
                    float(
                        np.max(
                            probabilities
                        )
                    ),
            }
        )


        del training
        del X_train
        del y_train
        del classifier
        del probabilities

        gc.collect()


    # ==========================================================================
    # MULTI-HORIZON MEDIAN PROBABILITY
    # ==========================================================================

    probability_matrix = (
        prediction_frame[
            V10_PROBABILITY_COLUMNS
        ]
        .to_numpy(
            dtype=float
        )
    )


    prediction_frame[
        V10_COMPOSITE_COLUMN
    ] = np.median(
        probability_matrix,
        axis=1,
    )


    if not np.isfinite(
        prediction_frame[
            V10_COMPOSITE_COLUMN
        ]
        .to_numpy(
            dtype=float
        )
    ).all():

        raise RuntimeError(
            "Composite V10 probability contains non-finite values."
        )


    decision_audit = pd.DataFrame(
        decision_audit_rows
    )


    current_ticker_hash = (
        v10_ticker_hash(
            prediction_frame[
                "Ticker"
            ]
            .tolist()
        )
    )


    checkpoint_payload = {

        "schema_version":
            V10_BLOCK2_CACHE_SCHEMA_VERSION,

        "block2_spec_fingerprint":
            V10_BLOCK2_SPEC_FINGERPRINT,

        "research_contract_fingerprint":
            V10_RESEARCH_CONTRACT_FINGERPRINT,

        "infrastructure_hash":
            V10_INFRA_DATA_HASH,

        "signal_date":
            signal_date,

        "execution_date":
            execution_date,

        "current_ticker_hash":
            current_ticker_hash,

        "prediction_rows":
            len(
                prediction_frame
            ),

        "horizons":
            tuple(
                V10_TARGET_HORIZONS.keys()
            ),

        "predictions":
            prediction_frame,

        "fit_audit":
            decision_audit,
    }


    checkpoint_path = (
        v10_checkpoint_path(
            signal_date
        )
    )


    v10_atomic_pickle_dump(
        checkpoint_payload,
        checkpoint_path,
    )


    # Reload once and validate the file that was actually written.

    saved_payload = (
        v10_load_checkpoint(
            signal_date
        )
    )


    if not v10_checkpoint_is_valid(
        payload=saved_payload,
        signal_date=signal_date,
        current=current,
    ):

        raise RuntimeError(
            "Newly written V10 checkpoint failed validation: "
            f"{signal_date.date()}"
        )


    print(
        "      [+] decision checkpoint saved"
    )


    V10_DECISION_PREDICTIONS.append(
        prediction_frame.copy()
    )


    V10_MODEL_FIT_AUDIT_PARTS.append(
        decision_audit.copy()
    )


    del prediction_frame
    del decision_audit
    del current_X
    del checkpoint_payload
    del saved_payload

    gc.collect()


# ==============================================================================
# 19. ASSEMBLE ALL 34 DECISIONS
# ==============================================================================

V10_CLASSIFIER_PREDICTIONS = (
    pd.concat(
        V10_DECISION_PREDICTIONS,
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


V10_MODEL_FIT_AUDIT = (
    pd.concat(
        V10_MODEL_FIT_AUDIT_PARTS,
        ignore_index=True,
    )
    .sort_values(
        [
            "Signal_Date",
            "Horizon",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 20. FINAL CHECKPOINT REVALIDATION
# ==============================================================================

V10_FINAL_VALID_CHECKPOINTS = 0


for signal_date in V10_EVALUATION_DATES:

    current = (
        v10_current_cross_section(
            signal_date
        )
    )


    payload = (
        v10_load_checkpoint(
            signal_date
        )
    )


    if v10_checkpoint_is_valid(
        payload=payload,
        signal_date=signal_date,
        current=current,
    ):

        V10_FINAL_VALID_CHECKPOINTS += 1


if (
    V10_FINAL_VALID_CHECKPOINTS
    !=
    len(
        V10_EVALUATION_DATES
    )
):

    raise RuntimeError(
        "V10 Block 2 finished without 34/34 valid checkpoints."
    )


# ==============================================================================
# 21. GLOBAL PREDICTION INTEGRITY
# ==============================================================================

if V10_CLASSIFIER_PREDICTIONS.duplicated(
    [
        "Date",
        "Ticker",
    ]
).any():

    raise RuntimeError(
        "Duplicate ticker-date rows in assembled V10 predictions."
    )


if (
    V10_CLASSIFIER_PREDICTIONS[
        "Date"
    ]
    .nunique()
    !=
    len(
        V10_EVALUATION_DATES
    )
):

    raise RuntimeError(
        "Assembled V10 predictions do not contain all 34 decisions."
    )


all_probability_columns = (
    V10_PROBABILITY_COLUMNS
    +
    [
        V10_COMPOSITE_COLUMN
    ]
)


all_probabilities = (
    V10_CLASSIFIER_PREDICTIONS[
        all_probability_columns
    ]
    .to_numpy(
        dtype=float
    )
)


if not np.isfinite(
    all_probabilities
).all():

    raise RuntimeError(
        "Assembled V10 predictions contain non-finite probabilities."
    )


if (
    all_probabilities < 0.0
).any() or (
    all_probabilities > 1.0
).any():

    raise RuntimeError(
        "Assembled V10 probabilities are outside [0,1]."
    )


# ==============================================================================
# 22. NON-PERFORMANCE PROBABILITY DIAGNOSTICS
# ==============================================================================

V10_PROBABILITY_SUMMARY_ROWS = []


for horizon_name in V10_TARGET_HORIZONS:

    column = (
        f"Prob_Beat_TQQQ_{horizon_name}"
    )


    values = (
        V10_CLASSIFIER_PREDICTIONS[
            column
        ]
        .to_numpy(
            dtype=float
        )
    )


    V10_PROBABILITY_SUMMARY_ROWS.append(
        {
            "Horizon":
                horizon_name,

            "Rows":
                len(
                    values
                ),

            "Mean_Probability":
                float(
                    np.mean(
                        values
                    )
                ),

            "Median_Probability":
                float(
                    np.median(
                        values
                    )
                ),

            "Std_Probability":
                float(
                    np.std(
                        values
                    )
                ),

            "Pct_Above_0_50":
                100.0
                *
                float(
                    np.mean(
                        values
                        >
                        0.50
                    )
                ),

            "Min_Probability":
                float(
                    np.min(
                        values
                    )
                ),

            "Max_Probability":
                float(
                    np.max(
                        values
                    )
                ),
        }
    )


V10_PROBABILITY_SUMMARY = pd.DataFrame(
    V10_PROBABILITY_SUMMARY_ROWS
).set_index(
    "Horizon"
)


# ==============================================================================
# 23. DECISION-LEVEL COMPOSITE PROBABILITY AUDIT
# ==============================================================================

V10_COMPOSITE_DECISION_ROWS = []


for signal_date, section in (
    V10_CLASSIFIER_PREDICTIONS.groupby(
        "Date",
        sort=True,
    )
):

    values = (
        section[
            V10_COMPOSITE_COLUMN
        ]
        .to_numpy(
            dtype=float
        )
    )


    V10_COMPOSITE_DECISION_ROWS.append(
        {
            "Signal_Date":
                pd.Timestamp(
                    signal_date
                ),

            "Stocks":
                len(
                    section
                ),

            "Mean_Composite_Probability":
                float(
                    np.mean(
                        values
                    )
                ),

            "Median_Composite_Probability":
                float(
                    np.median(
                        values
                    )
                ),

            "Stocks_Above_0_50":
                int(
                    np.sum(
                        values
                        >
                        0.50
                    )
                ),

            "Pct_Above_0_50":
                100.0
                *
                float(
                    np.mean(
                        values
                        >
                        0.50
                    )
                ),

            "Maximum_Composite_Probability":
                float(
                    np.max(
                        values
                    )
                ),
        }
    )


V10_COMPOSITE_DECISION_AUDIT = (
    pd.DataFrame(
        V10_COMPOSITE_DECISION_ROWS
    )
)


# ==============================================================================
# 24. BLOCK-2 RESULT FINGERPRINT
# ==============================================================================

V10_PREDICTION_HASH_FRAME = (
    V10_CLASSIFIER_PREDICTIONS[
        [
            "Date",
            "Execution_Date",
            "Ticker",
        ]
        +
        V10_PROBABILITY_COLUMNS
        +
        [
            V10_COMPOSITE_COLUMN
        ]
    ]
    .copy()
)


V10_PREDICTION_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V10_PREDICTION_HASH_FRAME,
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V10_PREDICTIONS_HASH = (
    hashlib.sha256(
        V10_PREDICTION_HASH_VALUES.tobytes()
    )
    .hexdigest()
)


V10_BLOCK2_RESULT_PAYLOAD = {

    "block2_spec_fingerprint":
        V10_BLOCK2_SPEC_FINGERPRINT,

    "research_contract_fingerprint":
        V10_RESEARCH_CONTRACT_FINGERPRINT,

    "infrastructure_hash":
        V10_INFRA_DATA_HASH,

    "prediction_hash":
        V10_PREDICTIONS_HASH,

    "evaluation_decisions":
        len(
            V10_EVALUATION_DATES
        ),

    "prediction_rows":
        len(
            V10_CLASSIFIER_PREDICTIONS
        ),

    "horizons":
        tuple(
            V10_TARGET_HORIZONS.keys()
        ),

    "model_features":
        len(
            V10_MODEL_FEATURES
        ),

    "portfolio_performance_calculated":
        False,
}


V10_BLOCK2_RESEARCH_FINGERPRINT = (
    hashlib.sha256(
        json.dumps(
            V10_BLOCK2_RESULT_PAYLOAD,
            sort_keys=True,
            default=str,
        )
        .encode(
            "utf-8"
        )
    )
    .hexdigest()
)


del V10_PREDICTION_HASH_FRAME
del V10_PREDICTION_HASH_VALUES


# ==============================================================================
# 25. FINAL SUMMARY
# ==============================================================================

V10_BLOCK2_SUMMARY = pd.DataFrame(
    {
        "Metric": [

            "Evaluation decisions",

            "Target horizons",

            "Model features",

            "Prediction rows",

            "Final valid checkpoints",

            "Training dates per fit",

            "Portfolio performance calculated",

            "Prediction hash",

            "Block 2 research fingerprint",
        ],

        "Value": [

            len(
                V10_EVALUATION_DATES
            ),

            len(
                V10_TARGET_HORIZONS
            ),

            len(
                V10_MODEL_FEATURES
            ),

            len(
                V10_CLASSIFIER_PREDICTIONS
            ),

            V10_FINAL_VALID_CHECKPOINTS,

            V10_TRAIN_LOOKBACK_SESSIONS,

            False,

            V10_PREDICTIONS_HASH,

            V10_BLOCK2_RESEARCH_FINGERPRINT,
        ],
    }
)


print(
    "\n2) V10 BLOCK 2 FINAL SUMMARY"
)


display(
    V10_BLOCK2_SUMMARY
)


print(
    "\n3) MODEL FIT AUDIT — LAST 14 ROWS"
)


display(
    V10_MODEL_FIT_AUDIT
    .tail(
        14
    )
    .round(
        6
    )
)


print(
    "\n4) PREDICTED PROBABILITY DISTRIBUTION"
)


display(
    V10_PROBABILITY_SUMMARY.round(
        6
    )
)


print(
    "\n5) COMPOSITE PROBABILITY — LAST 10 DECISIONS"
)


display(
    V10_COMPOSITE_DECISION_AUDIT
    .tail(
        10
    )
    .round(
        6
    )
)


print(
    "\nINTEGRITY:"
)

print(
    "[+] Seven frozen horizons were modeled."
)

print(
    "[+] Every target is binary TQQQ-relative outperformance."
)

print(
    "[+] Every fit uses exactly 252 fully matured signal dates."
)

print(
    "[+] No target end date occurs after its model signal date."
)

print(
    "[+] Current predictions use only feature-complete PIT stocks."
)

print(
    "[+] HGB probabilities, not raw return magnitudes, are produced."
)

print(
    "[+] Multi-horizon composite is the frozen median probability."
)

print(
    "[+] No horizon was removed or performance-weighted."
)

print(
    "[+] No minimum position rule was introduced."
)

print(
    "[+] No maximum position rule was introduced."
)

print(
    "[+] No Top-K rule was introduced."
)

print(
    "[+] No sector or risk cap was introduced."
)

print(
    "[+] Every completed decision is checkpointed to disk."
)

print(
    "[+] Cache validity is tied to the V10 contract and infrastructure."
)

print(
    "[+] Interrupted execution can resume from completed decisions."
)

print(
    "[+] NO V10 PORTFOLIO PERFORMANCE HAS BEEN CALCULATED."
)


print(
    "\nNEXT:"
)

print(
    "V10 BLOCK 3 — FROZEN PROBABILITY-EDGE STOCK SLEEVE "
    "+ TQQQ UNIVERSAL ALLOCATOR."
)

print("=" * 138)
