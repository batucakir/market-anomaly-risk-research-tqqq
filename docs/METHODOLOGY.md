# Methodology

## Scope

The notebook records a sequence of research versions rather than one production model. V4 through V16 test different portfolio and overlay constructions on a common historical research period. V9 through V15 were historically rejected; V16 produced the strongest frozen historical result.

## Causality and execution

The later-version convention is signal at the completed close on trading session T and execution at the close of the next actual trading session. Calendar reconstruction uses the TQQQ trading calendar and asserts that each signal date precedes its execution date.

The earlier V4 lineage uses its original next-open accounting. Results from different accounting lineages are labelled explicitly and should not be treated as interchangeable.

## V8

V8 uses TQQQ as its core and the frozen V7 alpha sleeve when that sleeve is available. A parameter-free universal wealth posterior determines the overlay weight. The research objective is maximum net terminal wealth with a 2 basis point transaction-cost assumption and a 21-session decision frequency.

Two V8 values appear in the historical record:

- `3.861086` is the original one-shot result under open-based, multiplicative-cost accounting.
- `4.184169` is the recovered close-ledger comparator using additive transaction costs and the terminal rebalance convention used in the final V16 comparison.

## V16

V16 keeps the frozen V8 core and adds a residual-momentum tilt. Its signal is a 12-month minus 1-month residual momentum measure. The allocation is learned through a universal wealth mixture without a tuned fixed lambda. The official final wealth includes the terminal rebalance cost.

## Controls

The notebook contains point-in-time membership checks, signal/execution causality assertions, exact lifecycle quote checks, checkpoint fingerprints, frozen state hashes, solver failure gates, benchmark alignment checks, and independent end-state replication tables.

## Interpretation

The results are research backcasts. The freeze states explicitly record that true out-of-sample evaluation had not started. Selection across many versions creates research-selection risk even when individual calculations are causal.
