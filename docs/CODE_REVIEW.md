# Code Review

## What is strong

- Signal and execution dates are explicitly separated and checked.
- Point-in-time membership and quote availability receive dedicated audits.
- Transaction costs and turnover are visible in the portfolio path.
- Research versions use fingerprints and freeze states.
- The final results include independent replication and exact-value checks.
- Failures generally stop execution instead of silently substituting results.

## What should improve

1. The notebook depends heavily on shared global state. A missed or duplicated cell can change behavior. The release builder and integrity test detect exact duplicate source cells, but the underlying architecture remains stateful.
2. Several cells are tens of thousands of characters long. They should be split into importable modules with explicit inputs and return values.
3. Runtime package installation and network data repair make environment behavior less predictable.
4. Data and checkpoint paths are local and cache dependent. A versioned data manifest is needed for full reproducibility.
5. The repository has integrity tests but no affordable end-to-end test with a small fixture dataset.
6. Multiple accounting lineages coexist. The documentation now labels them, but accounting should eventually be implemented in one tested library.
7. True out-of-sample evaluation has not started. Research selection across V4-V16 remains a material statistical limitation.

Historical cell numbering is also irregular: Module 12 has no labelled model cell, Module 16 appears as both a compatibility patch and a historical Block 39 bridge, and later module numbers refer to version transitions rather than one consistent software package. The ordered cell manifest is therefore the reliable execution index.

## Publication judgment

The code is suitable for a private GitHub research archive after the release checks pass. Before presenting it as a publicly reproducible project, complete the data, dependency, licensing, and fixture-test work in `PUBLICATION_CHECKLIST.md`.
