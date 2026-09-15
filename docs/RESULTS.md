# Results

## Official common-window comparison

The official result interval is 2023-10-18 through 2026-07-27. All dollar examples start with USD 10,000.

| Strategy | Final wealth | Net return | Ending value | Profit/loss | Event-mark max drawdown |
|---|---:|---:|---:|---:|---:|
| V16 | 4.3657796007 | 336.577960% | $43,657.80 | $33,657.80 | -35.259773% |
| V8 corrected comparator | 4.1841686378 | 318.416864% | $41,841.69 | $31,841.69 | -35.442280% |
| TQQQ comparator | 3.5634331693 | 256.343317% | $35,634.33 | $25,634.33 | -45.111888% |

V16 exceeds the corrected V8 comparator by 18.161096 percentage points of initial capital, or USD 1,816.11 on the USD 10,000 example. Its final wealth is 4.340431% higher than V8's.

## Why the notebook contains more than one V8 number

The two values answer different accounting questions.

| Label | Final wealth | Accounting |
|---|---:|---|
| Original V8 one-shot | 3.8610863723 | Open marks and multiplicative transaction costs |
| Corrected V8 comparator | 4.1841686378 | Close ledger, additive transaction costs, terminal rebalance |

The official multi-version comparison uses `4.184169` because it aligns V8 with the final comparator convention. The `3.861086` value remains in the archive as the original V8 research freeze. The `4.038149` value seen in an earlier diagnostic was the ex-post best constant sleeve-weight diagnostic and was never the V8 strategy result.

## Robustness snapshot

V16 beat V8 and TQQQ in the frozen trailing 1, 3, 6, 12, and 24 event-window summaries and over all 33 completed events. This does not establish prospective performance because the same historical research program produced and selected the versions.

## Canonical files

- `results/official_10000_summary.csv` contains all version-level values.
- `results/v16_robustness.csv` contains the frozen trailing-window comparison.
- `results/v8_rolling_summary.csv` records V8 rolling-window hit rates.
- `results/v8_replication_audit.csv` records the exact six-decimal replication checks.
