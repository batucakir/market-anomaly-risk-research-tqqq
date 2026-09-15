# Contributing

This repository currently represents a frozen research archive. Open an issue before changing model parameters, accounting conventions, execution timing, data sources, or frozen fingerprints.

For a proposed change:

1. State the research question and the causal information set.
2. Identify every affected module and frozen fingerprint.
3. Keep benchmark and strategy accounting on the same calendar and price convention.
4. Add a focused integrity check for any new invariant.
5. Run `python -m unittest discover -s tests -v`.
6. Report whether headline results changed and explain why.

Never commit API keys, account identifiers, raw licensed market data, local caches, or generated handoff archives.
