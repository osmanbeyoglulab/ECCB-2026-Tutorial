# Session 0: prepare Google Drive for Colab

The hands-on tutorial runs in **Google Colab**. Participants do not need a local Conda
environment or GPU. Full DGAT training is skipped because of Colab compute limits; Session 2
teaches the architecture and losses, then loads verified pretrained Tonsil predictions.

The example dataset is the **10x Genomics CytAssist Tonsil** paired RNA/ADT sample used by DGAT
(`Tonsil_RNA.h5ad` / `Tonsil_ADT.h5ad`).

## What participants need

- A Google account
- A current web browser
- Stable network for the first-time repo clone and ~350 MB Tonsil download
- Colab runtime version **2026.04** selected under Runtime → Change runtime type

## Step 1 — Before the workshop, open the Drive preparation notebook

Open this notebook in Colab (GitHub → Open in Colab, or use the badge in
[`README.md`](README.md)):

[`notebooks/session_00/00_colab_setup.ipynb`](notebooks/session_00/00_colab_setup.ipynb)

Run every cell top to bottom. It will:

1. mount your Google Drive and create `MyDrive/ECCB2026/`;
2. shallow-clone the small tutorial repository into the temporary Colab VM;
3. download the Tonsil RNA/ADT assets directly into Drive;
4. compute and save SHA-256 checksums in `asset_manifest.json`;
5. cache the Colab add-on wheels used by Sessions 1–2 for the current Python version;
6. create persistent folders for processed data, results, figures, and checkpoints.

Checkpoint: the final cell should print `Drive preparation complete: .../MyDrive/ECCB2026`.
You may then close the Session 0 runtime; the downloaded files remain in Drive.

## Step 2 — During the workshop, open one notebook per session

Use the Open-in-Colab links in [`README.md`](README.md). Do not open `.ipynb` files from
Colab's `/content` Files pane: that pane shows a source preview, not an executable notebook.

Run the first bootstrap cell whenever a session notebook receives a new runtime. It:

1. mounts `MyDrive/ECCB2026`;
2. shallow-clones the repository into `/content` when absent;
3. copies the two pre-staged H5AD files from Drive to fast local VM storage;
4. adds `src/` to Python's import path without installing the tutorial package;
5. installs only missing session-specific packages, preferring the Drive wheel cache;
6. reconnects processed outputs and checkpoints under `MyDrive/ECCB2026/state`.

Recommended order:

1. `notebooks/session_01/session_01_data_and_spatial.ipynb`
2. `notebooks/session_02/session_02_model_and_predictions.ipynb` — **training is skipped**
3. `notebooks/session_03/session_03_evaluation_and_interpretation.ipynb`

The Python environment itself remains temporary—this is a Colab limitation—but the bootstrap is
small. Sessions 1 and 2 install only `anndata`, `scanpy`, and `muon` when missing. Session 3
requires `anndata` and otherwise uses the Colab base environment, with small fallbacks for
Seaborn or scikit-learn if absent.

## Step 3 — Confirm the inference artifact

In Session 2 Part 4, the notebook should print the DGAT method and evaluation caveat, then write
a processed prediction table with its provenance sidecar. Participants load the committed CSV;
they do **not** run official `protein_predict` during the workshop.

## Timing budget (Colab)

| Block | Typical time |
| --- | --- |
| Pre-workshop Drive download (~350 MB), checksum, and wheel cache | 5–20+ min once |
| New-session bootstrap | usually under a few minutes |
| Copy Tonsil data from Drive to local Colab storage | network/Drive dependent, no public redownload |
| Sessions 1–3 guided execution | remainder of hands-on blocks |

If Colab disk or network fails, ask an instructor for the mirrored notebook runtime or the
pre-staged Tonsil assets.

## Optional local Conda path (organizers / offline)

Local Conda remains available for organizers and offline dry-runs:

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial/hands-on_tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil
jupyter lab
```

Participants in the live ECCB session should prefer Colab unless an instructor directs otherwise.

## Troubleshooting

- **An `.ipynb` opened as source with `<undefined>` cells:** close the Files-pane preview and use
  the notebook's Open-in-Colab link from `README.md`.
- **Drive asset missing:** rerun Session 0; completed files are skipped and interrupted downloads
  resume when supported by `gdown`.
- **`ModuleNotFoundError: dgat_tutorial`:** rerun the first bootstrap cell in the current session
  notebook. It adds the cloned `src/` directory directly to `sys.path`.
- **Runtime disconnected:** reopen the same session notebook, rerun its bootstrap, and jump to the
  first unfinished part listed by the printed checkpoints.
- **Wrong dataset:** do not substitute Breast or other samples for the Tonsil participant path.
- **Want to train DGAT:** not part of this tutorial. See the upstream
  [DGAT repository](https://github.com/osmanbeyoglulab/DGAT) and organizer docs.
