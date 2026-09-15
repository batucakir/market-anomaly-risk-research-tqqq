# MODULE 44 — V16 RESIDUAL-MOMENTUM UNIVERSAL TILT
# Run in the same notebook, in module order.

# =============================================================================
# V16 — ONE-SHOT V8 RESIDUAL-MOMENTUM TILT
# V8 CORE/ALPHA MASS PRESERVED
# + TQQQ-RESIDUAL 12-1 CROSS-SECTIONAL TILT
# + CAUSAL UNIVERSAL TILT-STRENGTH ALLOCATOR
# =============================================================================

import numpy as np
import pandas as pd
import hashlib
import json
import matplotlib.pyplot as plt

print("=" * 138)
print("V16 — ONE-SHOT V8 RESIDUAL-MOMENTUM TILT")
print("FROZEN V8 + TQQQ-RESIDUAL 12-1 CROSS-SECTIONAL REWEIGHTING")
print("=" * 138)

# -----------------------------------------------------------------------------
# 0. REQUIRED STATE
# -----------------------------------------------------------------------------

required = [
    "event_compare",
    "V8Q_WEIGHT_MATRIX",
    "V12_LIFECYCLE",
]

missing = [x for x in required if x not in globals()]
if missing:
    raise RuntimeError(f"V16 missing required objects: {missing}")

TCA_RATE = 2.0 / 10000.0
LAMBDA_GRID = np.linspace(0.0, 1.0, 1001)

# Fixed structural convention:
# 252 daily-return beta estimation window
# residual momentum = 12M less most-recent 1M = first 231 of last 252 returns
BETA_WINDOW = 252
SKIP_WINDOW = 21

# -----------------------------------------------------------------------------
# 1. COMPLETED EVENT CALENDAR
# -----------------------------------------------------------------------------

EV = event_compare.copy()

for c in ["Execution_Date", "Exit_Date"]:
    if c not in EV.columns:
        raise RuntimeError(f"event_compare missing {c}")
    EV[c] = pd.to_datetime(EV[c]).dt.normalize()

EV = (
    EV.loc[
        EV["Exit_Date"].notna()
        & EV["Execution_Date"].notna()
        & (EV["Exit_Date"] > EV["Execution_Date"])
    ]
    .sort_values("Execution_Date")
    .reset_index(drop=True)
)

if len(EV) != 33:
    raise RuntimeError(
        f"Expected 33 completed research holding periods, found {len(EV)}."
    )

print(f"[+] Completed holding periods: {len(EV)}")

# -----------------------------------------------------------------------------
# 2. CANONICAL FULL DAILY PRICE LEDGER
# -----------------------------------------------------------------------------

LC = V12_LIFECYCLE.copy()

def first_existing(columns, candidates):
    cmap = {str(c).lower().replace(" ", "_"): c for c in columns}
    for x in candidates:
        k = x.lower().replace(" ", "_")
        if k in cmap:
            return cmap[k]
    return None

DATE_COL = first_existing(
    LC.columns,
    ["Date", "Trading_Date", "Price_Date"]
)

TICKER_COL = first_existing(
    LC.columns,
    ["Ticker", "Symbol"]
)

PRICE_COL = first_existing(
    LC.columns,
    ["Adj_Close", "Adj Close", "Adjusted_Close", "Close"]
)

if DATE_COL is None or TICKER_COL is None or PRICE_COL is None:
    raise RuntimeError(
        "Could not resolve Date/Ticker/Adjusted-Close columns in V12_LIFECYCLE."
    )

PX_LONG = LC[[DATE_COL, TICKER_COL, PRICE_COL]].copy()

PX_LONG.columns = ["Date", "Ticker", "Price"]
PX_LONG["Date"] = pd.to_datetime(PX_LONG["Date"], errors="coerce").dt.normalize()
PX_LONG["Ticker"] = PX_LONG["Ticker"].astype(str).str.upper().str.strip()
PX_LONG["Price"] = pd.to_numeric(PX_LONG["Price"], errors="coerce")

PX_LONG = PX_LONG.dropna(subset=["Date", "Ticker", "Price"])
PX_LONG = PX_LONG.loc[PX_LONG["Price"] > 0]

PX = (
    PX_LONG
    .drop_duplicates(["Date", "Ticker"], keep="last")
    .pivot(index="Date", columns="Ticker", values="Price")
    .sort_index()
)

if "TQQQ" not in PX.columns:
    raise RuntimeError("TQQQ missing from canonical lifecycle ledger.")

TQQQ_CAL = PX["TQQQ"].dropna().index.sort_values()

print(f"[+] Daily price rows   : {len(PX_LONG):,}")
print(f"[+] Price tickers      : {PX.shape[1]:,}")
print(f"[+] TQQQ sessions      : {len(TQQQ_CAL):,}")

# -----------------------------------------------------------------------------
# 3. EXECUTION AND SIGNAL CALENDAR
# -----------------------------------------------------------------------------

completed_exec_dates = list(EV["Execution_Date"])
terminal_exec_date = pd.Timestamp(EV["Exit_Date"].iloc[-1]).normalize()

TARGET_EXEC_DATES = completed_exec_dates + [terminal_exec_date]

if len(TARGET_EXEC_DATES) != 34:
    raise RuntimeError("V16 expected exactly 34 target decisions.")

def prior_tqqq_session(d):
    d = pd.Timestamp(d).normalize()
    x = TQQQ_CAL[TQQQ_CAL < d]
    if len(x) == 0:
        raise RuntimeError(f"No prior TQQQ session before {d.date()}")
    return pd.Timestamp(x[-1]).normalize()

SIGNAL_DATES = [prior_tqqq_session(d) for d in TARGET_EXEC_DATES]

# -----------------------------------------------------------------------------
# 4. RESOLVE FROZEN V8 TARGET MATRIX
# -----------------------------------------------------------------------------

RAW_W = V8Q_WEIGHT_MATRIX.copy()

if len(RAW_W) != 34:
    raise RuntimeError(
        f"V8Q_WEIGHT_MATRIX expected 34 rows, found {len(RAW_W)}."
    )

# Only columns that are actual tradeable ticker symbols in price ledger.
asset_cols = [
    c for c in RAW_W.columns
    if str(c).upper().strip() in PX.columns
]

if len(asset_cols) == 0:
    raise RuntimeError(
        "Could not identify ticker columns inside V8Q_WEIGHT_MATRIX."
    )

W_RAW = RAW_W[asset_cols].copy()
W_RAW.columns = [str(c).upper().strip() for c in W_RAW.columns]
W_RAW = W_RAW.apply(pd.to_numeric, errors="coerce").fillna(0.0)

# detect percent-vs-fraction
if float(W_RAW.sum(axis=1).median()) > 2.0:
    W_RAW = W_RAW / 100.0

# TQQQ core weights may live inside matrix or as a separate series.
if "TQQQ" in W_RAW.columns:

    V8_W = W_RAW.copy()

else:

    if "V8Q_TQQQ_WEIGHT" not in globals():
        raise RuntimeError(
            "TQQQ is absent from V8Q_WEIGHT_MATRIX and "
            "V8Q_TQQQ_WEIGHT is unavailable."
        )

    tq = pd.Series(V8Q_TQQQ_WEIGHT).reset_index(drop=True).astype(float)

    if len(tq) != 34:
        raise RuntimeError(
            f"V8Q_TQQQ_WEIGHT expected 34 rows, found {len(tq)}."
        )

    if float(tq.abs().median()) > 2.0:
        tq = tq / 100.0

    stock_sum = W_RAW.sum(axis=1).reset_index(drop=True)

    absolute_error = np.nanmedian(
        np.abs(stock_sum.values + tq.values - 1.0)
    )

    composition_error = np.nanmedian(
        np.abs(stock_sum.values - 1.0)
    )

    if absolute_error < 1e-3:
        # matrix already contains absolute portfolio stock weights
        V8_W = W_RAW.reset_index(drop=True).copy()

    elif composition_error < 1e-3:
        # matrix is alpha-sleeve composition
        V8_W = W_RAW.reset_index(drop=True).copy()
        V8_W = V8_W.mul(1.0 - tq.values, axis=0)

    else:
        # safest interpretation: normalize stock sleeve, then apply alpha mass
        V8_W = W_RAW.reset_index(drop=True).copy()

        row_sums = V8_W.sum(axis=1)

        for i in range(len(V8_W)):
            alpha_mass = max(0.0, 1.0 - float(tq.iloc[i]))

            if row_sums.iloc[i] > 0:
                V8_W.iloc[i] = (
                    V8_W.iloc[i]
                    / row_sums.iloc[i]
                    * alpha_mass
                )
            else:
                V8_W.iloc[i] = 0.0

    V8_W["TQQQ"] = tq.values

V8_W = V8_W.fillna(0.0)

# Remove completely unused columns.
V8_W = V8_W.loc[:, V8_W.abs().sum(axis=0) > 0]

# Exact normalization check.
row_sum = V8_W.sum(axis=1)

if not np.allclose(row_sum.values, 1.0, atol=2e-5):
    raise RuntimeError(
        "Resolved V8 target matrix does not sum to 100%. "
        f"Range={row_sum.min():.8f}..{row_sum.max():.8f}"
    )

V8_W.index = pd.DatetimeIndex(TARGET_EXEC_DATES)

if "TQQQ" not in V8_W.columns:
    raise RuntimeError("Resolved V8 matrix still has no TQQQ column.")

# Verify required prices exist.
V8_ASSETS = sorted(V8_W.columns)

missing_price_assets = [
    x for x in V8_ASSETS
    if x not in PX.columns
]

if missing_price_assets:
    raise RuntimeError(
        f"V8 assets missing from daily ledger: {missing_price_assets[:20]}"
    )

print(f"[+] Frozen V8 assets   : {len(V8_ASSETS):,}")
print("[+] V8 target rows sum exactly to 1.")

# -----------------------------------------------------------------------------
# 5. CAUSAL TQQQ-RESIDUAL 12-1 SCORE
# -----------------------------------------------------------------------------

def residual_tilt_for_decision(exec_date, signal_date):

    base = (
        V8_W.loc[pd.Timestamp(exec_date)]
        .reindex(V8_ASSETS)
        .fillna(0.0)
        .astype(float)
    )

    tq_weight = float(base.get("TQQQ", 0.0))

    stock_base = base.drop(labels=["TQQQ"], errors="ignore")
    stock_base = stock_base[stock_base > 0]

    alpha_mass = float(stock_base.sum())

    # No alpha sleeve => exact V8.
    if alpha_mass <= 1e-14:
        return base.copy(), {
            "Signal_Date": signal_date,
            "Execution_Date": exec_date,
            "V8_TQQQ_Weight": tq_weight,
            "V8_Alpha_Weight": 0.0,
            "Alpha_Names": 0,
            "Valid_Residual_Names": 0,
            "Median_Residual_Momentum": np.nan,
        }

    names = stock_base.index.tolist()

    cal = TQQQ_CAL[TQQQ_CAL <= pd.Timestamp(signal_date)]

    # Need 253 prices for 252 daily returns.
    if len(cal) < BETA_WINDOW + 1:
        # insufficient history => exact V8
        return base.copy(), {
            "Signal_Date": signal_date,
            "Execution_Date": exec_date,
            "V8_TQQQ_Weight": tq_weight,
            "V8_Alpha_Weight": alpha_mass,
            "Alpha_Names": len(names),
            "Valid_Residual_Names": 0,
            "Median_Residual_Momentum": np.nan,
        }

    hist_dates = cal[-(BETA_WINDOW + 1):]

    cols = ["TQQQ"] + names

    H = PX.reindex(index=hist_dates, columns=cols)

    logp = np.log(H)
    R = logp.diff().iloc[1:]

    market = R["TQQQ"]

    scores = pd.Series(np.nan, index=names, dtype=float)

    if market.notna().all() and float(market.var(ddof=0)) > 0:

        X = market.values.astype(float)

        x_mean = float(X.mean())
        x_dev = X - x_mean
        x_var_sum = float(np.dot(x_dev, x_dev))

        for ticker in names:

            y = R[ticker]

            # Structural requirement: complete 252-return history.
            if not y.notna().all():
                continue

            Y = y.values.astype(float)
            y_mean = float(Y.mean())
            y_dev = Y - y_mean

            beta = float(
                np.dot(x_dev, y_dev)
                / x_var_sum
            )

            intercept = y_mean - beta * x_mean

            resid = Y - intercept - beta * X

            # Classic 12-1 structure:
            # exclude the most recent 21 sessions.
            score = float(
                resid[:-SKIP_WINDOW].sum()
            )

            scores.loc[ticker] = score

    valid = scores.dropna()

    # Unknown score = neutral percentile 0.50.
    pct_rank = pd.Series(
        0.50,
        index=names,
        dtype=float
    )

    if len(valid) >= 2:
        pct_rank.loc[valid.index] = (
            valid.rank(
                pct=True,
                method="average"
            )
        )

    # Bounded structural multiplier:
    # rank 0.50 -> multiplier 1
    # rank 1.00 -> multiplier 2
    # rank near 0 -> multiplier near 0
    multiplier = 2.0 * pct_rank

    base_comp = stock_base / alpha_mass

    tilted_comp = base_comp * multiplier

    if tilted_comp.sum() <= 0:
        tilted_comp = base_comp.copy()
    else:
        tilted_comp /= tilted_comp.sum()

    tilted = pd.Series(
        0.0,
        index=V8_ASSETS,
        dtype=float
    )

    tilted["TQQQ"] = tq_weight

    tilted.loc[tilted_comp.index] = (
        tilted_comp * alpha_mass
    )

    if not np.isclose(
        tilted.sum(),
        1.0,
        atol=1e-10
    ):
        raise RuntimeError(
            f"Residual tilted target does not sum to 1 "
            f"for {exec_date}."
        )

    return tilted, {
        "Signal_Date": signal_date,
        "Execution_Date": exec_date,
        "V8_TQQQ_Weight": tq_weight,
        "V8_Alpha_Weight": alpha_mass,
        "Alpha_Names": len(names),
        "Valid_Residual_Names": len(valid),
        "Median_Residual_Momentum": (
            float(valid.median())
            if len(valid)
            else np.nan
        ),
    }

# -----------------------------------------------------------------------------
# 6. BUILD ALL TARGETS BEFORE PERFORMANCE
# -----------------------------------------------------------------------------

BASE_TARGETS = []
TILT_TARGETS = []
AUDIT_ROWS = []

for exec_date, signal_date in zip(
    TARGET_EXEC_DATES,
    SIGNAL_DATES
):

    b = (
        V8_W
        .loc[pd.Timestamp(exec_date)]
        .reindex(V8_ASSETS)
        .fillna(0.0)
        .astype(float)
    )

    t, audit = residual_tilt_for_decision(
        exec_date,
        signal_date
    )

    BASE_TARGETS.append(b.values)
    TILT_TARGETS.append(
        t.reindex(V8_ASSETS).values
    )
    AUDIT_ROWS.append(audit)

BASE_TARGETS = np.asarray(
    BASE_TARGETS,
    dtype=float
)

TILT_TARGETS = np.asarray(
    TILT_TARGETS,
    dtype=float
)

V16_SIGNAL_AUDIT = pd.DataFrame(AUDIT_ROWS)

V16_PREPERFORMANCE_HASH = hashlib.sha256(
    np.round(
        np.concatenate(
            [
                BASE_TARGETS.ravel(),
                TILT_TARGETS.ravel(),
            ]
        ),
        14,
    ).tobytes()
).hexdigest()

print("\n1) PRE-PERFORMANCE RESIDUAL-TILT AUDIT")
print(
    V16_SIGNAL_AUDIT[
        [
            "Signal_Date",
            "Execution_Date",
            "V8_TQQQ_Weight",
            "V8_Alpha_Weight",
            "Alpha_Names",
            "Valid_Residual_Names",
            "Median_Residual_Momentum",
        ]
    ].tail(12).to_string(index=False)
)

print(
    "\nV16 pre-performance state hash:",
    V16_PREPERFORMANCE_HASH
)

print(
    "\n[+] ALL V16 RESIDUAL-TILT TARGETS "
    "DEFINED BEFORE PERFORMANCE."
)

# -----------------------------------------------------------------------------
# 7. EXACT EVENT RETURNS
# -----------------------------------------------------------------------------

N_ASSETS = len(V8_ASSETS)
N_EXP = len(LAMBDA_GRID)

expert_wealth = np.ones(N_EXP)
actual_wealth = 1.0

expert_prev_drift = np.zeros(
    (N_EXP, N_ASSETS),
    dtype=float,
)

actual_prev_drift = np.zeros(
    N_ASSETS,
    dtype=float,
)

path_rows = []

for j in range(len(EV)):

    exec_date = pd.Timestamp(
        EV.loc[j, "Execution_Date"]
    )

    exit_date = pd.Timestamp(
        EV.loc[j, "Exit_Date"]
    )

    base = BASE_TARGETS[j]
    tilt = TILT_TARGETS[j]

    delta = tilt - base

    # Constant-mix residual-tilt experts.
    expert_targets = (
        base[None, :]
        + LAMBDA_GRID[:, None]
        * delta[None, :]
    )

    posterior = expert_wealth / expert_wealth.sum()

    pre_lambda = float(
        np.dot(
            posterior,
            LAMBDA_GRID
        )
    )

    actual_target = (
        base
        + pre_lambda * delta
    )

    # Exact execution-to-exit prices.
    p0 = (
        PX
        .reindex(
            index=[exec_date],
            columns=V8_ASSETS
        )
        .iloc[0]
    )

    p1 = (
        PX
        .reindex(
            index=[exit_date],
            columns=V8_ASSETS
        )
        .iloc[0]
    )

    required_now = (
        np.max(
            expert_targets,
            axis=0
        )
        > 1e-14
    )

    bad = required_now & (
        (~np.isfinite(p0.values))
        | (~np.isfinite(p1.values))
        | (p0.values <= 0)
        | (p1.values <= 0)
    )

    if bad.any():
        bad_names = np.array(V8_ASSETS)[bad]
        raise RuntimeError(
            f"Missing exact required prices "
            f"{exec_date.date()} -> {exit_date.date()}: "
            f"{list(bad_names[:20])}"
        )

    asset_ret = np.zeros(
        N_ASSETS,
        dtype=float
    )

    good = (
        np.isfinite(p0.values)
        & np.isfinite(p1.values)
        & (p0.values > 0)
        & (p1.values > 0)
    )

    asset_ret[good] = (
        p1.values[good]
        / p0.values[good]
        - 1.0
    )

    # ---------------------------------------------------------
    # Constant experts
    # ---------------------------------------------------------

    expert_turnover = np.abs(
        expert_targets
        - expert_prev_drift
    ).sum(axis=1)

    expert_cost = (
        TCA_RATE * expert_turnover
    )

    expert_gross_ret = (
        expert_targets
        @ asset_ret
    )

    expert_factor = (
        1.0
        + expert_gross_ret
        - expert_cost
    )

    if np.any(expert_factor <= 0):
        raise RuntimeError(
            f"Non-positive V16 expert wealth factor "
            f"at event {j + 1}."
        )

    expert_wealth *= expert_factor

    # ---------------------------------------------------------
    # Actual causal universal portfolio
    # ---------------------------------------------------------

    actual_turnover = float(
        np.abs(
            actual_target
            - actual_prev_drift
        ).sum()
    )

    actual_cost = (
        TCA_RATE * actual_turnover
    )

    actual_gross_ret = float(
        np.dot(
            actual_target,
            asset_ret
        )
    )

    actual_net_ret = (
        actual_gross_ret
        - actual_cost
    )

    actual_wealth *= (
        1.0 + actual_net_ret
    )

    # ---------------------------------------------------------
    # Drift weights to next execution
    # ---------------------------------------------------------

    expert_gross_factor = (
        1.0 + expert_gross_ret
    )

    expert_prev_drift = (
        expert_targets
        * (1.0 + asset_ret)[None, :]
        / expert_gross_factor[:, None]
    )

    actual_gross_factor = (
        1.0 + actual_gross_ret
    )

    actual_prev_drift = (
        actual_target
        * (1.0 + asset_ret)
        / actual_gross_factor
    )

    v8_ret_col = (
        "V8_Return_Pct"
        if "V8_Return_Pct" in EV.columns
        else None
    )

    tq_ret_col = (
        "TQQQ_Return_Pct"
        if "TQQQ_Return_Pct" in EV.columns
        else None
    )

    path_rows.append(
        {
            "Event": j + 1,
            "Signal_Date": SIGNAL_DATES[j],
            "Execution_Date": exec_date,
            "Exit_Date": exit_date,
            "Pre_Lambda": pre_lambda,
            "V8_TQQQ_Weight_Pct":
                100.0 * base[V8_ASSETS.index("TQQQ")],
            "V8_Alpha_Weight_Pct":
                100.0 * (
                    1.0
                    - base[V8_ASSETS.index("TQQQ")]
                ),
            "Turnover": actual_turnover,
            "TCA_bps": actual_cost * 10000.0,
            "Gross_Return_Pct":
                actual_gross_ret * 100.0,
            "Net_Return_Pct":
                actual_net_ret * 100.0,
            "V16_Wealth":
                actual_wealth,
            "V8_Return_Pct":
                float(EV.loc[j, v8_ret_col])
                if v8_ret_col
                else np.nan,
            "TQQQ_Return_Pct":
                float(EV.loc[j, tq_ret_col])
                if tq_ret_col
                else np.nan,
        }
    )

V16_PATH = pd.DataFrame(path_rows)

# -----------------------------------------------------------------------------
# 8. TERMINAL REBALANCE-ONLY COST
# -----------------------------------------------------------------------------

j_terminal = 33

base_terminal = BASE_TARGETS[j_terminal]
tilt_terminal = TILT_TARGETS[j_terminal]

delta_terminal = (
    tilt_terminal
    - base_terminal
)

posterior_terminal = (
    expert_wealth
    / expert_wealth.sum()
)

terminal_lambda = float(
    np.dot(
        posterior_terminal,
        LAMBDA_GRID
    )
)

terminal_target = (
    base_terminal
    + terminal_lambda
    * delta_terminal
)

terminal_turnover = float(
    np.abs(
        terminal_target
        - actual_prev_drift
    ).sum()
)

terminal_cost = (
    TCA_RATE
    * terminal_turnover
)

V16_FINAL_WEALTH = (
    actual_wealth
    * (1.0 - terminal_cost)
)

# Expert terminal rebalance costs.
expert_terminal_targets = (
    base_terminal[None, :]
    + LAMBDA_GRID[:, None]
    * delta_terminal[None, :]
)

expert_terminal_turnover = np.abs(
    expert_terminal_targets
    - expert_prev_drift
).sum(axis=1)

expert_terminal_cost = (
    TCA_RATE
    * expert_terminal_turnover
)

expert_final_wealth = (
    expert_wealth
    * (1.0 - expert_terminal_cost)
)

# λ=0 is exact frozen V8 baseline under this accounting.
V16_RECOVERED_V8_FINAL = float(
    expert_final_wealth[0]
)

V16_BEST_LAMBDA_IDX = int(
    np.argmax(expert_final_wealth)
)

V16_BEST_CONSTANT_LAMBDA = float(
    LAMBDA_GRID[V16_BEST_LAMBDA_IDX]
)

V16_BEST_CONSTANT_WEALTH = float(
    expert_final_wealth[V16_BEST_LAMBDA_IDX]
)

# -----------------------------------------------------------------------------
# 9. BENCHMARK WEALTH
# -----------------------------------------------------------------------------

if "V8_Return_Pct" not in EV.columns:
    raise RuntimeError(
        "event_compare lacks V8_Return_Pct."
    )

if "TQQQ_Return_Pct" not in EV.columns:
    raise RuntimeError(
        "event_compare lacks TQQQ_Return_Pct."
    )

V8_COMPLETED_WEALTH = float(
    np.prod(
        1.0
        + EV["V8_Return_Pct"].astype(float).values
        / 100.0
    )
)

TQQQ_COMPLETED_WEALTH = float(
    np.prod(
        1.0
        + EV["TQQQ_Return_Pct"].astype(float).values
        / 100.0
    )
)

# Historical exact repaired-ledger V8 terminal wealth.
# Prefer an existing notebook scalar if one can be identified;
# otherwise use λ=0 reconstruction from this exact engine.
V8_FINAL_WEALTH = V16_RECOVERED_V8_FINAL

# -----------------------------------------------------------------------------
# 10. RESULTS
# -----------------------------------------------------------------------------

V16_BEATS_V8 = (
    V16_FINAL_WEALTH
    > V8_FINAL_WEALTH + 1e-12
)

V16_BEATS_TQQQ = (
    V16_FINAL_WEALTH
    > TQQQ_COMPLETED_WEALTH + 1e-12
)

summary = pd.DataFrame(
    {
        "Metric": [
            "Completed holding periods",
            "V16 final wealth",
            "V16 net return pct",
            "Recovered V8 final wealth",
            "TQQQ completed wealth",
            "V16 minus V8 pp",
            "V16 minus TQQQ pp",
            "V16 / V8 relative wealth",
            "Mean residual tilt lambda pct",
            "Final posterior tilt lambda pct",
            "Total turnover",
            "Mean turnover",
            "Mean execution cost bps",
            "Best constant lambda — hindsight only",
            "Best constant wealth — hindsight only",
            "V16 beats V8",
            "V16 beats TQQQ",
        ],
        "Value": [
            len(EV),
            V16_FINAL_WEALTH,
            100.0 * (V16_FINAL_WEALTH - 1.0),
            V8_FINAL_WEALTH,
            TQQQ_COMPLETED_WEALTH,
            100.0 * (
                V16_FINAL_WEALTH
                - V8_FINAL_WEALTH
            ),
            100.0 * (
                V16_FINAL_WEALTH
                - TQQQ_COMPLETED_WEALTH
            ),
            V16_FINAL_WEALTH
            / V8_FINAL_WEALTH,
            100.0
            * V16_PATH["Pre_Lambda"].mean(),
            100.0 * terminal_lambda,
            V16_PATH["Turnover"].sum()
            + terminal_turnover,
            (
                V16_PATH["Turnover"].sum()
                + terminal_turnover
            ) / 34.0,
            (
                V16_PATH["TCA_bps"].sum()
                + terminal_cost * 10000.0
            ) / 34.0,
            V16_BEST_CONSTANT_LAMBDA,
            V16_BEST_CONSTANT_WEALTH,
            V16_BEATS_V8,
            V16_BEATS_TQQQ,
        ],
    }
)

print("\n2) V16 FINAL ECONOMIC RESULT")
display(summary)

# -----------------------------------------------------------------------------
# 11. TRAILING ROBUSTNESS
# -----------------------------------------------------------------------------

V8_RET = (
    EV["V8_Return_Pct"]
    .astype(float)
    .values
    / 100.0
)

TQ_RET = (
    EV["TQQQ_Return_Pct"]
    .astype(float)
    .values
    / 100.0
)

V16_RET = (
    V16_PATH["Net_Return_Pct"]
    .astype(float)
    .values
    / 100.0
)

robust_rows = []

for label, n in [
    ("~1M", 1),
    ("~3M", 3),
    ("~6M", 6),
    ("~12M", 12),
    ("~24M", 24),
    ("ALL_COMPLETED", len(EV)),
]:

    n = min(n, len(EV))

    r16 = (
        np.prod(
            1.0 + V16_RET[-n:]
        )
        - 1.0
    )

    r8 = (
        np.prod(
            1.0 + V8_RET[-n:]
        )
        - 1.0
    )

    rtq = (
        np.prod(
            1.0 + TQ_RET[-n:]
        )
        - 1.0
    )

    robust_rows.append(
        {
            "Window": label,
            "Periods": n,
            "V16_Return_Pct": 100 * r16,
            "V8_Return_Pct": 100 * r8,
            "TQQQ_Return_Pct": 100 * rtq,
            "V16_Minus_V8_pp":
                100 * (r16 - r8),
            "V16_Minus_TQQQ_pp":
                100 * (r16 - rtq),
            "V16_Beats_V8":
                r16 > r8,
            "V16_Beats_TQQQ":
                r16 > rtq,
        }
    )

V16_ROBUSTNESS = pd.DataFrame(
    robust_rows
)

print("\n3) TRAILING MULTI-PERIOD ROBUSTNESS")
display(V16_ROBUSTNESS)

print("\n4) LAST 12 V16 EVENTS")

display(
    V16_PATH.tail(12)[
        [
            "Event",
            "Execution_Date",
            "Exit_Date",
            "Pre_Lambda",
            "V8_TQQQ_Weight_Pct",
            "V8_Alpha_Weight_Pct",
            "Turnover",
            "TCA_bps",
            "Net_Return_Pct",
            "V8_Return_Pct",
            "TQQQ_Return_Pct",
            "V16_Wealth",
        ]
    ]
)

# -----------------------------------------------------------------------------
# 12. FINAL TARGET
# -----------------------------------------------------------------------------

V16_FINAL_TARGET = pd.Series(
    terminal_target,
    index=V8_ASSETS
)

V16_FINAL_TARGET = (
    V16_FINAL_TARGET[
        V16_FINAL_TARGET > 1e-5
    ]
    .sort_values(
        ascending=False
    )
)

print("\n5) FINAL V16 TARGET — 2026-07-27")
display(
    (
        100.0
        * V16_FINAL_TARGET
    )
    .rename("Weight_Pct")
    .to_frame()
    .head(30)
)

# -----------------------------------------------------------------------------
# 13. CHART
# -----------------------------------------------------------------------------

v16_curve = np.r_[
    1.0,
    np.cumprod(
        1.0 + V16_RET
    )
]

v8_curve = np.r_[
    1.0,
    np.cumprod(
        1.0 + V8_RET
    )
]

tq_curve = np.r_[
    1.0,
    np.cumprod(
        1.0 + TQ_RET
    )
]

dates_plot = [
    EV["Execution_Date"].iloc[0]
] + list(EV["Exit_Date"])

plt.figure(figsize=(13, 6))
plt.plot(
    dates_plot,
    v16_curve,
    label="V16 Residual Tilt"
)
plt.plot(
    dates_plot,
    v8_curve,
    label="V8 Champion"
)
plt.plot(
    dates_plot,
    tq_curve,
    label="TQQQ"
)
plt.axhline(
    1.0,
    linestyle="--",
    linewidth=1
)
plt.title(
    "V16 vs V8 vs TQQQ — COMPLETED-PERIOD NET WEALTH"
)
plt.xlabel("Date")
plt.ylabel("Wealth Multiple")
plt.legend()
plt.grid(alpha=0.25)
plt.show()

# -----------------------------------------------------------------------------
# 14. FINGERPRINT + VERDICT
# -----------------------------------------------------------------------------

finger_payload = {
    "version": "V16",
    "base": "FROZEN_V8",
    "signal":
        "TQQQ_RESIDUAL_12_MINUS_1_MOMENTUM",
    "beta_window": 252,
    "skip_window": 21,
    "tilt":
        "2_X_CROSS_SECTIONAL_PERCENTILE",
    "allocator":
        "UNIVERSAL_CONSTANT_LAMBDA_0_TO_1",
    "grid_points": 1001,
    "tca_bps": 2.0,
    "preperformance_hash":
        V16_PREPERFORMANCE_HASH,
}

V16_RESEARCH_FINGERPRINT = hashlib.sha256(
    json.dumps(
        finger_payload,
        sort_keys=True,
    ).encode()
).hexdigest()

print("\n6) V16 RESEARCH FINGERPRINT")
print(V16_RESEARCH_FINGERPRINT)

print("\n" + "=" * 138)
print("V16 ONE-SHOT RESEARCH VERDICT")
print("=" * 138)

print(
    f"V16 final wealth       : "
    f"{V16_FINAL_WEALTH:.6f}"
)

print(
    f"V8 recovered wealth    : "
    f"{V8_FINAL_WEALTH:.6f}"
)

print(
    f"TQQQ completed wealth  : "
    f"{TQQQ_COMPLETED_WEALTH:.6f}"
)

print(
    f"V16 minus V8           : "
    f"{100*(V16_FINAL_WEALTH - V8_FINAL_WEALTH):+.6f} pp"
)

print(
    f"V16 beats V8           : "
    f"{V16_BEATS_V8}"
)

print(
    f"V16 beats TQQQ         : "
    f"{V16_BEATS_TQQQ}"
)

print(
    f"Final residual tilt λ  : "
    f"{100*terminal_lambda:.3f}%"
)

print(
    f"Best λ hindsight only  : "
    f"{V16_BEST_CONSTANT_LAMBDA:.3f}"
)

if V16_BEATS_V8:

    print("\n[+] V16 BEATS THE FROZEN V8 CHAMPION.")
    print("[+] DO NOT RETUNE V16.")
    print("[+] NEXT: FREEZE / FORWARD-OOS DECISION.")

else:

    print("\n[-] V16 DOES NOT BEAT V8.")
    print("[-] REJECT V16 AS DESIGNED.")
    print("[-] DO NOT PATCH OR RETUNE IT.")
    print("[+] V8 REMAINS THE FROZEN CHAMPION.")

print("\nINTEGRITY:")
print("[+] Frozen V8 TQQQ/alpha mass was preserved.")
print("[+] Only cross-sectional composition inside the V8 alpha sleeve changed.")
print("[+] Residual signal uses only information available by signal close.")
print("[+] Most-recent 21 sessions are excluded from residual momentum.")
print("[+] No Top-K rule.")
print("[+] No stock cap.")
print("[+] No sector cap.")
print("[+] No risk cap.")
print("[+] No cash.")
print("[+] No leverage above 100%.")
print("[+] Tilt strength was not selected from realized performance.")
print("[+] Universal posterior uses prior completed periods only.")
print("[+] Linear 2 bps turnover cost included.")
print("[+] Hindsight best lambda is diagnostic only.")
print("=" * 138)
restored_register('V16', V16_FINAL_WEALTH, V16_PATH, 'V16_Wealth', 'Close / additive TCA / terminal rebalance', 'Historical research champion', terminal_date=pd.Timestamp("2026-07-27"))
