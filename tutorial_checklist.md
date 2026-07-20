# Tutorial Upload Checklist

Use this checklist before uploading the draft repository for ECCB committee review.

## Content

- [ ] README explains the tutorial goal, schedule, setup, and notebook order.
- [ ] Each notebook runs from top to bottom in a fresh environment.
- [ ] Dataset access instructions are clear and legally shareable.
- [ ] Any real data files are either small enough for GitHub or replaced by download instructions.
- [ ] DGAT model weights are either included only if permitted or downloaded by documented instructions.
- [ ] Official DGAT repository setup has been tested from a clean environment.
- [ ] Official DGAT `.h5ad` prediction data loads directly in the tutorial notebooks.
- [ ] Precomputed fallback predictions are available as `data/raw/dgat_predictions.csv`.
- [ ] Precomputed predictions include provenance and were not fitted on the evaluation rows.
- [ ] `PARTICIPANT_SETUP.md` is sent at least one week in advance with a 24-hour setup deadline.
- [ ] Expected runtime and peak memory are measured on the final assets and a clean reference machine.
- [ ] Common failure modes are documented in notebook markdown cells.

## Technical

- [ ] `conda env create -f environment.yml` succeeds.
- [ ] `pip install -r requirements.txt` succeeds.
- [ ] `conda env create -f environment-dgat-cpu.yml` succeeds separately on Python 3.11.
- [ ] `PYTHONPATH=src python scripts/check_dgat_environment.py` passes with official assets.
- [ ] Notebooks use relative paths from the repository root.
- [ ] Generated files are written under `results/` or `data/processed/`.
- [ ] Large generated files are ignored by `.gitignore`.
- [ ] No private paths, credentials, or unpublished data are committed.
- [ ] Notebook 2 defaults to precomputed official DGAT predictions, never to the ridge baseline.
- [ ] Notebook 3 prints the prediction method and evaluation caveat before metrics.

## Review Package

- [ ] Repository has a clear title and short description on GitHub.
- [ ] A release, tag, or commit hash is shared with the committee.
- [ ] License and citation information are included if required by collaborators.
- [ ] Contact information for tutorial organizers is easy to find.
