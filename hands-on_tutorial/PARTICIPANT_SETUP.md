# Participant preparation

The hands-on tutorial runs in **Google Colab**. You do not need to install Python, Conda,
Jupyter, DGAT, CUDA, or any Python packages on your laptop. A GPU is not required.

## What to prepare

- A laptop and charger
- A current web browser
- A Google account with access to Google Drive and Google Colab
- At least 1 GB of free space in Google Drive
- A stable connection for the one-time dataset download
- Your Google two-factor authentication method, if enabled

## Before the workshop: run Notebook 0 once

1. Open [Notebook 0 — Prepare Google Drive](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb).
2. Choose **Runtime → Change runtime type → 2026.04 (Python 3.12)**.
3. Run every cell from top to bottom and approve the Google Drive mount.
4. Wait for `Drive preparation complete: /content/drive/MyDrive/ECCB2026`.
5. Keep `MyDrive/ECCB2026` in place. You may close the runtime after preparation.

Notebook 0 automatically downloads and verifies the paired Tonsil files
`Tonsil_RNA.h5ad` and `Tonsil_ADT.h5ad` (about 350 MB total). It also creates a wheel cache and
persistent folders for processed data, results, figures, and checkpoints. Do not download or move
these files manually.

## During the workshop

Open notebooks with the direct links below. Do not open `.ipynb` files from Colab's `/content`
Files pane; that pane may show a source preview instead of an executable notebook.

1. [Notebook 1 — Data and spatial context](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb)
2. [Notebook 2 — Model and predictions](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb)
3. [Notebook 3 — Evaluation and interpretation](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb)

Run the first bootstrap cell whenever a notebook receives a new runtime. It mounts Drive,
refreshes the tutorial checkout, copies the prepared dataset to fast local storage, installs only
missing packages, and reconnects your saved checkpoints.

## If the runtime disconnects

1. Reopen the same notebook from its direct Colab link.
2. Confirm runtime version 2026.04.
3. Rerun the first bootstrap cell.
4. Read the printed checkpoints and continue from the first unfinished part.

Do not repeat Notebook 0 or redownload the dataset unless the notebook reports that a Drive asset
is missing or incomplete.

## Troubleshooting

- **Notebook shows `<undefined>` or raw source:** close the Files-pane preview and use the direct
  Colab link above.
- **Missing Drive asset:** rerun Notebook 0. Complete files are skipped, and interrupted downloads
  resume when supported.
- **`ModuleNotFoundError: dgat_tutorial`:** rerun the first bootstrap cell in the current notebook.
- **Runtime reset:** rerun only the bootstrap, then continue from the first unfinished checkpoint.
- **Wrong dataset:** use the Tonsil participant workflow; do not substitute another sample.

Repository: <https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial>
