# Publication Checklist

## Ready in this release

- Clean notebook with stored outputs removed
- Duplicate source-cell detection enabled in the release builder and integrity test
- Official Module 47 accounting correction retained
- Module 49 handoff exporter retained
- Reviewable Python exports for every ordered code cell
- README, methodology, result, accounting, data, and reproducibility documentation
- Compact derived result tables and a headline figure
- Secret and local-artifact exclusions
- Lightweight continuous-integration checks

## Required before making the repository public

- Select and add a license.
- Decide whether your name or organization should appear in `CITATION.cff`.
- Confirm that every included derived result may be redistributed.
- Pin the exact `pitindex` source revision or archive a licensed input snapshot with checksums.
- Add a small synthetic or redistributable fixture dataset for an end-to-end smoke test.
- Replace runtime package installation with a locked setup step.
- Review all claims and charts for research-only wording.
- Enable GitHub branch protection and require the integrity workflow before merging.

## Recommended first GitHub release

Create the repository as private. Upload this prepared tree, run the GitHub Actions integrity workflow, and review the rendered notebook and chart. Change visibility only after the public-release items above are resolved.
