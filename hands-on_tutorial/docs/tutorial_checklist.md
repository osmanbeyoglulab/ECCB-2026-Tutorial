# Tutorial Upload Checklist

Use this checklist before uploading the draft repository for ECCB committee review.

## Content

- [x] README explains Colab-first setup, Tonsil example, schedule, and notebook order.
- [ ] Each teaching notebook runs from top to bottom in a fresh Colab runtime (or local Conda).
- [x] Each Session 1–3 part can restart from its heading without in-memory state from an earlier part.
- [x] Dataset access instructions use the 10x Genomics CytAssist Tonsil DGAT assets.
- [x] Notebooks are committed with executed inline outputs/plots.
- [x] Full DGAT training is skipped in the participant path (discussion + pretrained predictions only).
- [x] Lecture slides are PDF-only under `overview/` (no PowerPoint).
- [x] Developer `tests/` tree is not part of the public repository package.
- [x] Precomputed official **Tonsil** predictions are available as `data/raw/dgat_predictions.csv`.
- [ ] Prediction sidecar `tonsil_held_out` confirmed with authors before presenting held-out accuracy (currently `null` / unknown).
- [ ] Session 0 Colab setup has been timed on conference Wi-Fi / reference accounts.
- [ ] Common failure modes are documented in notebook markdown cells.

## Technical

- [ ] Colab Session 0 setup notebook completes on a clean runtime.
- [ ] Optional local `conda env create -f environment.yml` still succeeds for organizers.
- [x] Notebooks discover the `hands-on_tutorial/` root (local or `/content/...` Colab path).
- [ ] Each part writes its JSON completion manifest under `checkpoints/`.
- [ ] Generated files are written under `results/` or `data/processed/`.
- [ ] Large generated files / `.h5ad` / checkpoints remain ignored by `.gitignore`.
- [ ] No private paths, credentials, or unpublished data are committed.
- [x] Session 2, Part 3 teaches losses without launching training.
- [x] Session 2, Part 4 loads precomputed official DGAT predictions and never substitutes the ridge baseline.
- [x] Session 3, Part 1 CLR-normalizes observed ADT before metrics and prints held-out provenance caveats.

## Review Package

- [ ] Repository has a clear title and short description on GitHub.
- [ ] A release, tag, or commit hash is shared with the committee.
- [ ] License and citation information are included if required by collaborators.
- [ ] Contact information for tutorial organizers is easy to find.
