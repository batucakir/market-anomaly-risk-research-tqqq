# Reproducibility

## Recorded environment

The successful handoff run recorded:

- Python 3.9.13
- NumPy 1.26.4
- pandas 2.2.2
- scikit-learn 1.0.2
- SciPy 1.13.1
- CVXPY 1.5.4
- yfinance 0.2.54
- Matplotlib 3.9.4

The original environment also emitted warnings because `numexpr` 2.8.3 and `bottleneck` 1.3.5 were older than pandas requested. The release environment raises those optional dependencies to the compatible minimums.

## Frozen identifiers

- V8 research freeze fingerprint: `7c41083b3a091e10dcb460e6968458450b7dc464333fd20ae0b0744ad5dccec9`
- V16 research fingerprint: `c6dfd3997656a3dab6fbf14af30d48c2965bdb5a5e671de8a2f256a4aab4271`
- V16 master freeze fingerprint: `8d2ce2c6464cae2c25978fb6aab23972936591412a6090466e77a34b22bb406c`
- V16 pre-performance fingerprint: `aa858199025778bc61fe714c51e2632cb4586e8447fac277b0230b9980815635`
- V16 target hash: `7d69830af5f9ec207a6a34f2fd13bf25e92e2c6e6343ac098975f6d3b715c35c`

## Release validation

The lightweight release test checks that:

1. the notebook has no stored outputs or execution counters;
2. the duplicate Module 32 source cell has been removed;
3. Module 47 contains the official accounting correction;
4. Module 49 remains available for future handoffs;
5. every exported pipeline cell compiles under Python 3.9;
6. source hashes match the notebook manifest;
7. official V16, V8, and TQQQ values match the frozen results.

These checks establish release integrity. They do not rerun model fitting or independently reproduce market data.

## Exact rerun limitation

The historical run depended on local data and checkpoint caches that are not distributed. The upstream point-in-time package was installed from an unpinned Git branch when a cache was unavailable. Therefore this release preserves and audits the successful research state but does not yet provide a bit-for-bit clean-room reproduction from public inputs alone.
