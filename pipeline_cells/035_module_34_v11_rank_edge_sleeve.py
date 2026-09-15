# MODULE 34 — V11 RANK-EDGE SLEEVE
# Run in the same notebook, in module order.

# ==============================================================================
# V11 — BLOCK 2
# CROSS-SECTIONAL SEVEN-HORIZON RANK PANEL
# + FROZEN RANK-EDGE STOCK SLEEVE
# ==============================================================================
#
# NO MODEL FITTING.
# NO PORTFOLIO PERFORMANCE.
# NO RETURN-BASED SELECTION.
#
# INPUT:
#   Frozen V10 seven-horizon HGB probabilities.
#
# TRANSFORMATION:
#   1. For each signal date and each horizon, convert probability to
#      contemporaneous cross-sectional percentile rank.
#
#   2. Composite rank = median of the seven horizon ranks.
#
#   3. Rank edge:
#
#          edge_i = max(composite_rank_i - 0.50, 0)
#
#   4. Stock-sleeve weights:
#
#          w_i = edge_i / sum(edge)
#
#
# NO:
#   minimum position size
#   maximum position size
#   Top-K
#   sector cap
#   risk cap
#   TQQQ floor
#   alpha cap
#   cash
#
# ==============================================================================


import hashlib
import json
import numpy as np
import pandas as pd

from IPython.display import display


# ==============================================================================
# 0. REQUIREMENTS
# ==============================================================================

V11_B2_REQUIRED = [
    "V11_RESEARCH_CONTRACT_FINGERPRINT",
    "V11_INPUT_PREDICTION_HASH",
    "V11_TARGET_HORIZONS",
    "V11_STOCK_SLEEVE_RULE",

    "V10_CLASSIFIER_PREDICTIONS",
    "V10_PREDICTIONS_HASH",
    "V10_BLOCK2_RESEARCH_FINGERPRINT",
]


V11_B2_MISSING = [
    name
    for name in V11_B2_REQUIRED
    if name not in globals()
]


if V11_B2_MISSING:

    raise RuntimeError(
        "V11 Block 2 is missing required objects: "
        f"{V11_B2_MISSING}"
    )


print("=" * 140)
print("V11 — BLOCK 2")
print("CROSS-SECTIONAL SEVEN-HORIZON RANK PANEL")
print("+ FROZEN RANK-EDGE STOCK SLEEVE")
print("=" * 140)

print("\nNO MODEL FITTING WILL OCCUR.")
print("NO V11 PORTFOLIO PERFORMANCE WILL BE CALCULATED.")


# ==============================================================================
# 1. DEFINE FROZEN INPUT COLUMNS
# ==============================================================================

V11_PROBABILITY_COLUMNS = [
    f"Prob_Beat_TQQQ_{horizon}"
    for horizon in V11_TARGET_HORIZONS
]


V11_REQUIRED_INPUT_COLUMNS = (
    [
        "Date",
        "Execution_Date",
        "Ticker",
    ]
    +
    V11_PROBABILITY_COLUMNS
    +
    [
        "Composite_Prob_Beat_TQQQ"
    ]
)


V11_B2_INPUT_MISSING = [
    column
    for column in V11_REQUIRED_INPUT_COLUMNS
    if column not in V10_CLASSIFIER_PREDICTIONS.columns
]


if V11_B2_INPUT_MISSING:

    raise RuntimeError(
        "Frozen V10 prediction object is missing columns: "
        f"{V11_B2_INPUT_MISSING}"
    )


# ==============================================================================
# 2. VERIFY FROZEN V10 FORECAST STATE AGAIN
# ==============================================================================
#
# IMPORTANT:
# This must reproduce the ORIGINAL V10 hash exactly.
# Do not normalize or sort before hashing.
# ==============================================================================

V11_B2_HASH_FRAME = (
    V10_CLASSIFIER_PREDICTIONS[
        V11_REQUIRED_INPUT_COLUMNS
    ]
    .copy()
)


V11_B2_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V11_B2_HASH_FRAME,
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V11_B2_INPUT_HASH = hashlib.sha256(
    V11_B2_HASH_VALUES.tobytes()
).hexdigest()


if (
    V11_B2_INPUT_HASH
    !=
    V10_PREDICTIONS_HASH
):

    raise RuntimeError(
        "Frozen V10 prediction state changed before V11 Block 2."
    )


if (
    V11_B2_INPUT_HASH
    !=
    V11_INPUT_PREDICTION_HASH
):

    raise RuntimeError(
        "V11 Block 1 verified hash does not match Block 2 input."
    )


print(
    "\n[+] Frozen V10 forecast hash verified exactly."
)


del V11_B2_HASH_FRAME
del V11_B2_HASH_VALUES


# ==============================================================================
# 3. CREATE NORMALIZED WORKING COPY
# ==============================================================================

V11_RANK_PANEL = (
    V10_CLASSIFIER_PREDICTIONS[
        V11_REQUIRED_INPUT_COLUMNS
    ]
    .copy()
)


for column in [
    "Date",
    "Execution_Date",
]:

    dates = pd.to_datetime(
        V11_RANK_PANEL[column],
        errors="coerce",
    )

    try:

        dates = dates.dt.tz_localize(
            None
        )

    except (TypeError, AttributeError):

        pass

    V11_RANK_PANEL[column] = (
        dates.dt.normalize()
    )


V11_RANK_PANEL[
    "Ticker"
] = (
    V11_RANK_PANEL[
        "Ticker"
    ]
    .astype(str)
    .str.upper()
    .str.strip()
)


if V11_RANK_PANEL[
    [
        "Date",
        "Execution_Date",
        "Ticker",
    ]
].isna().any().any():

    raise RuntimeError(
        "V11 Block 2 found missing identity/date fields."
    )


if V11_RANK_PANEL.duplicated(
    [
        "Date",
        "Ticker",
    ]
).any():

    raise RuntimeError(
        "Duplicate ticker-date rows in V11 rank input."
    )


# ==============================================================================
# 4. PROBABILITY INTEGRITY
# ==============================================================================

for column in V11_PROBABILITY_COLUMNS:

    V11_RANK_PANEL[column] = pd.to_numeric(
        V11_RANK_PANEL[column],
        errors="coerce",
    )


V11_B2_PROB_MATRIX = (
    V11_RANK_PANEL[
        V11_PROBABILITY_COLUMNS
    ]
    .to_numpy(
        dtype=float
    )
)


if not np.isfinite(
    V11_B2_PROB_MATRIX
).all():

    raise RuntimeError(
        "Frozen V10 probabilities contain non-finite values."
    )


if (
    V11_B2_PROB_MATRIX < 0.0
).any() or (
    V11_B2_PROB_MATRIX > 1.0
).any():

    raise RuntimeError(
        "Frozen V10 probabilities lie outside [0,1]."
    )


del V11_B2_PROB_MATRIX


# ==============================================================================
# 5. SIGNAL / EXECUTION DATE INTEGRITY
# ==============================================================================

V11_B2_DATE_MAP = (
    V11_RANK_PANEL[
        [
            "Date",
            "Execution_Date",
        ]
    ]
    .drop_duplicates()
)


V11_B2_EXECUTION_COUNTS = (
    V11_B2_DATE_MAP
    .groupby(
        "Date"
    )[
        "Execution_Date"
    ]
    .nunique()
)


if (
    V11_B2_EXECUTION_COUNTS != 1
).any():

    raise RuntimeError(
        "At least one V11 signal date maps to multiple execution dates."
    )


if (
    V11_RANK_PANEL[
        "Date"
    ]
    .nunique()
    !=
    34
):

    raise RuntimeError(
        "V11 expected exactly 34 research decisions."
    )


# ==============================================================================
# 6. CROSS-SECTIONAL PERCENTILE RANKS
# ==============================================================================

V11_RANK_COLUMNS = []


for horizon in V11_TARGET_HORIZONS:

    probability_column = (
        f"Prob_Beat_TQQQ_{horizon}"
    )

    rank_column = (
        f"Rank_Beat_TQQQ_{horizon}"
    )


    V11_RANK_PANEL[
        rank_column
    ] = (
        V11_RANK_PANEL
        .groupby(
            "Date"
        )[
            probability_column
        ]
        .rank(
            method="average",
            pct=True,
            ascending=True,
        )
    )


    V11_RANK_COLUMNS.append(
        rank_column
    )


# ==============================================================================
# 7. RANK INTEGRITY
# ==============================================================================

V11_B2_RANK_MATRIX = (
    V11_RANK_PANEL[
        V11_RANK_COLUMNS
    ]
    .to_numpy(
        dtype=float
    )
)


if not np.isfinite(
    V11_B2_RANK_MATRIX
).all():

    raise RuntimeError(
        "V11 percentile-rank matrix contains non-finite values."
    )


if (
    V11_B2_RANK_MATRIX <= 0.0
).any() or (
    V11_B2_RANK_MATRIX > 1.0
).any():

    raise RuntimeError(
        "V11 percentile ranks lie outside (0,1]."
    )


# ==============================================================================
# 8. SEVEN-HORIZON MEDIAN RANK
# ==============================================================================

V11_RANK_PANEL[
    "Composite_Rank"
] = np.median(
    V11_B2_RANK_MATRIX,
    axis=1,
)


del V11_B2_RANK_MATRIX


if not np.isfinite(
    V11_RANK_PANEL[
        "Composite_Rank"
    ]
    .to_numpy(
        dtype=float
    )
).all():

    raise RuntimeError(
        "V11 composite rank contains non-finite values."
    )


# ==============================================================================
# 9. FROZEN RANK EDGE
# ==============================================================================

V11_RANK_BREAK_EVEN = 0.50


if float(
    V11_STOCK_SLEEVE_RULE[
        "rank_break_even"
    ]
) != V11_RANK_BREAK_EVEN:

    raise RuntimeError(
        "V11 rank break-even differs from locked contract."
    )


V11_RANK_PANEL[
    "Rank_Edge"
] = np.maximum(
    V11_RANK_PANEL[
        "Composite_Rank"
    ]
    .to_numpy(
        dtype=float
    )
    -
    V11_RANK_BREAK_EVEN,
    0.0,
)


# ==============================================================================
# 10. NORMALIZED STOCK-SLEEVE WEIGHTS
# ==============================================================================

V11_RANK_PANEL[
    "Sleeve_Weight"
] = 0.0


V11_STOCK_SLEEVE_TARGETS = {}

V11_STOCK_SLEEVE_ROWS = []


for event_number, (
    signal_date,
    section_index,
) in enumerate(
    V11_RANK_PANEL
    .groupby(
        "Date",
        sort=True,
    )
    .groups
    .items(),
    start=1,
):

    section = (
        V11_RANK_PANEL.loc[
            section_index
        ]
        .copy()
    )


    signal_date = pd.Timestamp(
        signal_date
    ).normalize()


    execution_dates = (
        section[
            "Execution_Date"
        ]
        .drop_duplicates()
        .tolist()
    )


    if len(
        execution_dates
    ) != 1:

        raise RuntimeError(
            "Signal date maps to multiple execution dates: "
            f"{signal_date.date()}"
        )


    execution_date = pd.Timestamp(
        execution_dates[0]
    ).normalize()


    edge = (
        section[
            "Rank_Edge"
        ]
        .to_numpy(
            dtype=float
        )
    )


    positive_mask = (
        edge > 0.0
    )


    positive_count = int(
        positive_mask.sum()
    )


    edge_sum = float(
        edge.sum()
    )


    if (
        not np.isfinite(
            edge_sum
        )
        or
        edge_sum < 0
    ):

        raise RuntimeError(
            "Invalid V11 rank-edge sum."
        )


    if edge_sum > 0.0:

        selected_index = (
            section.index[
                positive_mask
            ]
        )


        selected_weights = (
            edge[
                positive_mask
            ]
            /
            edge_sum
        )


        V11_RANK_PANEL.loc[
            selected_index,
            "Sleeve_Weight",
        ] = selected_weights


        selected_tickers = (
            section.loc[
                selected_index,
                "Ticker",
            ]
            .astype(str)
            .tolist()
        )


        target = {
            ticker:
                float(weight)

            for ticker, weight
            in zip(
                selected_tickers,
                selected_weights,
            )
        }


        target_total = float(
            sum(
                target.values()
            )
        )


        if not np.isclose(
            target_total,
            1.0,
            atol=1e-12,
            rtol=0.0,
        ):

            raise RuntimeError(
                "V11 stock-sleeve weights do not sum to 1."
            )


        weight_vector = np.asarray(
            list(
                target.values()
            ),
            dtype=float,
        )


        effective_n = float(
            1.0
            /
            np.sum(
                weight_vector ** 2
            )
        )


        max_weight = float(
            np.max(
                weight_vector
            )
        )


        largest_position = max(
            target,
            key=target.get,
        )


        satellite_available = True


    else:

        target = {}

        effective_n = np.nan

        max_weight = 0.0

        largest_position = None

        satellite_available = False


    V11_STOCK_SLEEVE_TARGETS[
        execution_date
    ] = dict(
        target
    )


    V11_STOCK_SLEEVE_ROWS.append(
        {
            "Event":
                event_number,

            "Signal_Date":
                signal_date,

            "Execution_Date":
                execution_date,

            "Candidate_Stocks":
                int(
                    len(
                        section
                    )
                ),

            "Positive_Rank_Edge_Stocks":
                positive_count,

            "Positive_Rank_Edge_Pct":
                (
                    100.0
                    *
                    positive_count
                    /
                    len(
                        section
                    )
                ),

            "Satellite_Available":
                satellite_available,

            "Mean_Composite_Rank":
                float(
                    section[
                        "Composite_Rank"
                    ].mean()
                ),

            "Median_Composite_Rank":
                float(
                    section[
                        "Composite_Rank"
                    ].median()
                ),

            "Max_Composite_Rank":
                float(
                    section[
                        "Composite_Rank"
                    ].max()
                ),

            "Effective_N":
                effective_n,

            "Max_Name_Weight_Pct":
                100.0
                *
                max_weight,

            "Largest_Position":
                largest_position,

            "Weight_Sum":
                (
                    float(
                        sum(
                            target.values()
                        )
                    )
                    if target
                    else
                    0.0
                ),
        }
    )


V11_STOCK_SLEEVE_DECISIONS = (
    pd.DataFrame(
        V11_STOCK_SLEEVE_ROWS
    )
    .sort_values(
        "Signal_Date"
    )
    .reset_index(
        drop=True
    )
)


# ==============================================================================
# 11. FINAL SLEEVE INTEGRITY
# ==============================================================================

if len(
    V11_STOCK_SLEEVE_DECISIONS
) != 34:

    raise RuntimeError(
        "V11 did not produce exactly 34 sleeve decisions."
    )


if (
    V11_STOCK_SLEEVE_DECISIONS[
        "Candidate_Stocks"
    ]
    <= 0
).any():

    raise RuntimeError(
        "At least one V11 decision has zero candidates."
    )


for execution_date, target in (
    V11_STOCK_SLEEVE_TARGETS.items()
):

    if target:

        weights = np.asarray(
            list(
                target.values()
            ),
            dtype=float,
        )


        if not np.isfinite(
            weights
        ).all():

            raise RuntimeError(
                "Non-finite V11 sleeve weight."
            )


        if (
            weights <= 0.0
        ).any():

            raise RuntimeError(
                "Non-positive position inside V11 active sleeve."
            )


        if not np.isclose(
            weights.sum(),
            1.0,
            atol=1e-12,
            rtol=0.0,
        ):

            raise RuntimeError(
                "Active V11 stock sleeve does not sum to 1."
            )


# ==============================================================================
# 12. CROSS-SECTIONAL SANITY AUDIT
# ==============================================================================

V11_RANK_AUDIT_ROWS = []


for signal_date, section in (
    V11_RANK_PANEL.groupby(
        "Date",
        sort=True,
    )
):

    V11_RANK_AUDIT_ROWS.append(
        {
            "Signal_Date":
                pd.Timestamp(
                    signal_date
                ),

            "Stocks":
                int(
                    len(
                        section
                    )
                ),

            "Composite_Rank_Mean":
                float(
                    section[
                        "Composite_Rank"
                    ].mean()
                ),

            "Composite_Rank_Median":
                float(
                    section[
                        "Composite_Rank"
                    ].median()
                ),

            "Composite_Rank_Min":
                float(
                    section[
                        "Composite_Rank"
                    ].min()
                ),

            "Composite_Rank_Max":
                float(
                    section[
                        "Composite_Rank"
                    ].max()
                ),

            "Positive_Edge_Stocks":
                int(
                    (
                        section[
                            "Rank_Edge"
                        ]
                        >
                        0
                    ).sum()
                ),

            "Sleeve_Weight_Sum":
                float(
                    section[
                        "Sleeve_Weight"
                    ].sum()
                ),
        }
    )


V11_RANK_AUDIT = pd.DataFrame(
    V11_RANK_AUDIT_ROWS
)


# ==============================================================================
# 13. CONCENTRATION SUMMARY
# ==============================================================================

V11_ACTIVE_SLEEVE_DECISIONS = (
    V11_STOCK_SLEEVE_DECISIONS.loc[
        V11_STOCK_SLEEVE_DECISIONS[
            "Satellite_Available"
        ]
    ]
)


if V11_ACTIVE_SLEEVE_DECISIONS.empty:

    raise RuntimeError(
        "V11 produced no active stock-sleeve decisions."
    )


V11_STOCK_SLEEVE_CONCENTRATION = pd.DataFrame(
    {
        "Metric": [

            "Research decisions",

            "Active satellite decisions",

            "Active satellite pct",

            "Mean candidate stocks",

            "Median candidate stocks",

            "Mean positive-edge stocks",

            "Median positive-edge stocks",

            "Minimum positive-edge stocks",

            "Maximum positive-edge stocks",

            "Mean effective N",

            "Median effective N",

            "Minimum effective N",

            "Maximum effective N",

            "Mean max-name weight pct",

            "Median max-name weight pct",

            "Maximum max-name weight pct",
        ],

        "Value": [

            len(
                V11_STOCK_SLEEVE_DECISIONS
            ),

            len(
                V11_ACTIVE_SLEEVE_DECISIONS
            ),

            100.0
            *
            len(
                V11_ACTIVE_SLEEVE_DECISIONS
            )
            /
            len(
                V11_STOCK_SLEEVE_DECISIONS
            ),

            V11_STOCK_SLEEVE_DECISIONS[
                "Candidate_Stocks"
            ].mean(),

            V11_STOCK_SLEEVE_DECISIONS[
                "Candidate_Stocks"
            ].median(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Positive_Rank_Edge_Stocks"
            ].mean(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Positive_Rank_Edge_Stocks"
            ].median(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Positive_Rank_Edge_Stocks"
            ].min(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Positive_Rank_Edge_Stocks"
            ].max(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Effective_N"
            ].mean(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Effective_N"
            ].median(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Effective_N"
            ].min(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Effective_N"
            ].max(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Max_Name_Weight_Pct"
            ].mean(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Max_Name_Weight_Pct"
            ].median(),

            V11_ACTIVE_SLEEVE_DECISIONS[
                "Max_Name_Weight_Pct"
            ].max(),
        ],
    }
)


# ==============================================================================
# 14. FINAL STOCK SLEEVE
# ==============================================================================

V11_FINAL_EXECUTION_DATE = (
    V11_STOCK_SLEEVE_DECISIONS[
        "Execution_Date"
    ]
    .iloc[
        -1
    ]
)


V11_FINAL_STOCK_SLEEVE = pd.Series(
    V11_STOCK_SLEEVE_TARGETS[
        V11_FINAL_EXECUTION_DATE
    ],
    name="Weight",
).sort_values(
    ascending=False
)


V11_FINAL_STOCK_SLEEVE_TABLE = (
    100.0
    *
    V11_FINAL_STOCK_SLEEVE
).rename(
    "Weight_Pct"
).to_frame()


# ==============================================================================
# 15. BLOCK-2 SPECIFICATION FINGERPRINT
# ==============================================================================

V11_BLOCK2_SPEC = {

    "version":
        "V11_BLOCK2",

    "research_contract_fingerprint":
        V11_RESEARCH_CONTRACT_FINGERPRINT,

    "input_prediction_hash":
        V11_B2_INPUT_HASH,

    "source_v10_block2_fingerprint":
        V10_BLOCK2_RESEARCH_FINGERPRINT,

    "horizons":
        V11_TARGET_HORIZONS,

    "per_horizon_transform":
        "CROSS_SECTIONAL_PERCENTILE_RANK",

    "rank_method":
        "AVERAGE",

    "rank_pct":
        True,

    "aggregation":
        "MEDIAN_OF_SEVEN_RANKS",

    "rank_break_even":
        0.50,

    "edge_rule":
        "MAX(COMPOSITE_RANK_MINUS_0P50,0)",

    "weighting":
        "NORMALIZED_POSITIVE_RANK_EDGE",

    "minimum_stock_weight":
        None,

    "maximum_stock_weight":
        None,

    "top_k":
        None,

    "sector_cap":
        None,

    "risk_cap":
        None,

    "portfolio_performance_calculated":
        False,
}


V11_BLOCK2_SPEC_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V11_BLOCK2_SPEC,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()


# ==============================================================================
# 16. RESULT HASH
# ==============================================================================

V11_BLOCK2_HASH_COLUMNS = (
    [
        "Date",
        "Execution_Date",
        "Ticker",
    ]
    +
    V11_RANK_COLUMNS
    +
    [
        "Composite_Rank",
        "Rank_Edge",
        "Sleeve_Weight",
    ]
)


V11_BLOCK2_HASH_FRAME = (
    V11_RANK_PANEL[
        V11_BLOCK2_HASH_COLUMNS
    ]
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


V11_BLOCK2_HASH_VALUES = (
    pd.util.hash_pandas_object(
        V11_BLOCK2_HASH_FRAME,
        index=False,
    )
    .to_numpy(
        dtype=np.uint64
    )
)


V11_RANK_SLEEVE_HASH = hashlib.sha256(
    V11_BLOCK2_HASH_VALUES.tobytes()
).hexdigest()


V11_BLOCK2_RESULT_PAYLOAD = {

    "spec_fingerprint":
        V11_BLOCK2_SPEC_FINGERPRINT,

    "contract_fingerprint":
        V11_RESEARCH_CONTRACT_FINGERPRINT,

    "frozen_input_hash":
        V11_B2_INPUT_HASH,

    "rank_sleeve_hash":
        V11_RANK_SLEEVE_HASH,

    "prediction_rows":
        len(
            V11_RANK_PANEL
        ),

    "decisions":
        len(
            V11_STOCK_SLEEVE_DECISIONS
        ),

    "portfolio_performance_calculated":
        False,
}


V11_BLOCK2_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        V11_BLOCK2_RESULT_PAYLOAD,
        sort_keys=True,
        default=str,
    ).encode(
        "utf-8"
    )
).hexdigest()


del V11_BLOCK2_HASH_FRAME
del V11_BLOCK2_HASH_VALUES


# ==============================================================================
# 17. OUTPUT
# ==============================================================================

print(
    "\n1) V11 STOCK-SLEEVE DECISION AUDIT"
)


display(
    V11_STOCK_SLEEVE_DECISIONS[
        [
            "Event",
            "Signal_Date",
            "Execution_Date",
            "Candidate_Stocks",
            "Positive_Rank_Edge_Stocks",
            "Positive_Rank_Edge_Pct",
            "Satellite_Available",
            "Median_Composite_Rank",
            "Max_Composite_Rank",
            "Effective_N",
            "Max_Name_Weight_Pct",
            "Largest_Position",
            "Weight_Sum",
        ]
    ].round(
        6
    )
)


print(
    "\n2) V11 STOCK-SLEEVE CONCENTRATION SUMMARY"
)


display(
    V11_STOCK_SLEEVE_CONCENTRATION.round(
        6
    )
)


print(
    "\n3) V11 RANK PANEL — LAST 10 DECISIONS"
)


display(
    V11_RANK_AUDIT
    .tail(
        10
    )
    .round(
        6
    )
)


print(
    "\n4) FINAL V11 STOCK SLEEVE"
)

print(
    "Execution date:",
    pd.Timestamp(
        V11_FINAL_EXECUTION_DATE
    ).date()
)


display(
    V11_FINAL_STOCK_SLEEVE_TABLE
    .head(
        30
    )
    .round(
        6
    )
)


print(
    "\n5) V11 BLOCK 2 SPECIFICATION FINGERPRINT"
)

print(
    V11_BLOCK2_SPEC_FINGERPRINT
)


print(
    "\n6) V11 RANK-SLEEVE HASH"
)

print(
    V11_RANK_SLEEVE_HASH
)


print(
    "\n7) V11 BLOCK 2 RESEARCH FINGERPRINT"
)

print(
    V11_BLOCK2_RESEARCH_FINGERPRINT
)


print("\nINTEGRITY:")

print(
    "[+] Frozen V10 forecast hash matched exactly."
)

print(
    "[+] No HGB model was fitted."
)

print(
    "[+] No probability forecast was changed."
)

print(
    "[+] All seven horizons were retained."
)

print(
    "[+] Each horizon was ranked only within its contemporaneous cross-section."
)

print(
    "[+] Composite score is the median of seven percentile ranks."
)

print(
    "[+] Rank break-even is exactly 0.50."
)

print(
    "[+] Stock weights are normalized positive rank edges."
)

print(
    "[+] No minimum position size."
)

print(
    "[+] No maximum position size."
)

print(
    "[+] No Top-K selection."
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
    "[+] No portfolio return has been calculated."
)

print(
    "[+] No V11 performance has been observed."
)


print("\nNEXT:")

print(
    "V11 BLOCK 3 — EXACT EXECUTION PREFLIGHT + "
    "CAUSAL TQQQ-FIRST FOLLOW-THE-LEADER ALLOCATOR + "
    "ONE-SHOT ECONOMIC TEST."
)

print("=" * 140)
