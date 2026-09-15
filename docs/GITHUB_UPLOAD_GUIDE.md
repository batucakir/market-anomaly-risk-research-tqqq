# GitHub Upload Guide

## Recommended repository settings

- Repository name: `market-anomaly-risk-research`
- Initial visibility: Private
- Description: `Causal US equity and ETF allocation research with frozen V8/V16 accounting audits.`
- Topics: `quantitative-finance`, `backtesting`, `portfolio-allocation`, `time-series`, `research`, `jupyter-notebook`
- Default branch: `main`
- Initial release tag after verification: `v0.1.0-research`

Do not ask GitHub to create a README, `.gitignore`, or license when creating the empty repository. Those files are already handled here, except for the license decision.

## Upload with Git

Set your Git identity once if it is not already configured:

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR VERIFIED GITHUB EMAIL"
```

From the prepared project directory:

```bash
git init -b main
python -m unittest discover -s tests -v
git add .
git status
git commit -m "Create audited research release"
git remote add origin https://github.com/YOUR-USER/market-anomaly-risk-research.git
git push -u origin main
```

Use a GitHub personal access token or an SSH key if Git asks for authentication. Do not place the token inside a notebook, configuration file, command history example, or commit.

## Review immediately after upload

1. Confirm that the README renders on the repository front page.
2. Open `notebooks/research_pipeline.ipynb` and confirm GitHub renders 51 cells with no stored outputs.
3. Open the Actions tab and verify that `Release integrity` passes.
4. Confirm that no `v4_cache`, `restored_*_cache`, `.pkl`, handoff ZIP, or raw data file appears in the repository.
5. Check the final chart endpoint and the `results/official_10000_summary.csv` values.
6. Add the repository description and topics.

## Repository protections

For a private one-person research repository, enable branch protection after the first push:

- Require a pull request before merging into `main`.
- Require the `validate` status check.
- Block force pushes and branch deletion.
- Enable secret scanning if your GitHub plan exposes it.

## License decision

Keep the repository private until you choose the intended rights:

- MIT is simple and permissive if you want broad reuse.
- Apache-2.0 is permissive and includes an explicit patent grant.
- No public open-source license is appropriate if you want to keep reuse restricted; in that case, keep the repository private or obtain legal advice for a custom license.

After selecting a license, add a root `LICENSE` file and update the README. Do not add a license merely to make the page look complete.

## First release

After the integrity workflow passes and the repository has been reviewed, create a GitHub release named `v0.1.0-research`. State that it is a historical research archive, identify the common research window, and link to `docs/RESULTS.md` and `docs/REPRODUCIBILITY.md`.

Do not attach raw data, caches, checkpoint files, or the full notebook handoff ZIP to the release.
