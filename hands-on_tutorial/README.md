# DGAT hands-on tutorial

The participant workflow uses four restart-safe Google Colab notebooks and the 10x Genomics
CytAssist **Tonsil** paired RNA/ADT dataset.

## Notebook order

| Step | Purpose | Open in Colab |
| --- | --- | --- |
| 0 | Prepare Google Drive once before the workshop | [Open Notebook 0](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb) |
| 1 | Validate data, apply QC/normalization, and build spatial context | [Open Notebook 1](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb) |
| 2 | Study DGAT architecture/losses and load pretrained predictions | [Open Notebook 2](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb) |
| 3 | Evaluate pointwise accuracy, spatial coherence, and interpretation | [Open Notebook 3](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb) |

Use Colab runtime version **2026.04 (Python 3.12)** throughout.

## How persistence works

Notebook 0 stores the Tonsil assets, a verified manifest, a Python wheel cache, and persistent
state under `MyDrive/ECCB2026`. Each teaching notebook may use a fresh Colab runtime. Its first
cell mounts Drive, refreshes the small repository checkout, copies the dataset to fast local VM
storage, installs only missing packages, and reconnects saved checkpoints.

If a runtime disconnects, reopen the same notebook, rerun its first cell, and continue from the
first unfinished checkpoint. You do not need to repeat Notebook 0 or redownload the dataset.

## Dataset and prediction artifact

- Measurements: `Tonsil_RNA.h5ad` and `Tonsil_ADT.h5ad`, downloaded automatically by Notebook 0
- Predictions: the committed `data/raw/dgat_predictions.csv` and its provenance metadata
- Live training: intentionally skipped because of workshop time and Colab compute limits

The notebooks teach the public DGAT graph construction, architecture, and five-term objective,
then evaluate verified pretrained predictions rather than training a model during the workshop.

## Participant support

Read [PARTICIPANT_SETUP.md](PARTICIPANT_SETUP.md) before attending. It covers preparation,
direct notebook links, restart behavior, and common troubleshooting steps.
