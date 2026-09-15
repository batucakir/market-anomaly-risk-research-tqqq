# Data and Provenance

## Data used by the research

The notebook combines adjusted market prices, ETF prices, point-in-time universe information, and locally cached intermediate panels. The successful historical run used a Python 3.9 environment and local caches for the expensive point-in-time and model-fitting stages.

The handoff audit recorded 1,717 tickers with raw price data out of 2,041 requested, or 84.13%. Median point-in-time price coverage was 92.78%. A missing terminal HLX quote was restored from an archived notebook output and explicitly labelled in the audit trail.

## Repository policy

Raw downloaded market data, point-in-time membership data, model checkpoints, and local caches are excluded from version control. This avoids distributing data with uncertain redistribution rights and prevents large machine-specific artifacts from entering Git history.

The included CSV files are compact derived research results. They are insufficient to reconstruct the full model fit.

## External data behavior

The notebook contains a cache-first `pitindex` setup path and yfinance-based repair logic. Network downloads can change, fail, or be rate limited. The historical `pitindex` Git reference was not pinned to a commit, so an exact clean-room rerun cannot be claimed without the original cache or a verified source snapshot.

Before a public reproducibility release, record checksums for every required cache, document how each input was licensed and obtained, and replace runtime package installation with a locked environment build.
