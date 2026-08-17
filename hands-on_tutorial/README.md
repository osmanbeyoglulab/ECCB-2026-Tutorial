# DGAT hands-on tutorial

The participant workflow uses four restart-safe Google Colab notebooks and one public 10x Genomics
Visium **human lymph node** transcriptomics sample (`V1_Human_Lymph_Node`).

## Notebook order

| Step | Purpose | Open in Colab |
| --- | --- | --- |
| 0 | Prepare Google Drive once before the workshop | [Open Notebook 0](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb) |
| 1 | Introduce the lymph node, align GC labels, and evaluate RNA coverage | [Open Notebook 1](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb) |
| 2 | Validate and load the precomputed lymph-node predictions | [Open Notebook 2](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb) |
| 3 | Interpret markers, GC clusters, and spatial coherence | [Open Notebook 3](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb) |

Use Colab runtime version **2026.04 (Python 3.12)** throughout.

## How persistence works

Notebook 0 stores the lymph-node matrix, spatial/H&E bundle, GC annotation, validated precomputed
prediction matrix, a verified manifest, a Python wheel cache, and persistent
state under `MyDrive/ECCB2026`. Each teaching notebook may use a fresh Colab runtime. Its first
cell mounts Drive, refreshes the small repository checkout, copies the dataset to fast local VM
storage, installs only missing packages, and reconnects saved checkpoints.

If a runtime disconnects, reopen the same notebook, rerun its first cell, and continue from the
first unfinished checkpoint. You do not need to repeat Notebook 0 or redownload the dataset.

## Dataset and prediction artifact

- Measurements: transcript counts, spatial coordinates, and H&E image from the public 10x `V1_Human_Lymph_Node` release
- Annotation: tracked manual germinal-center labels, aligned explicitly to the 10x barcodes
- Predictions: generated and validated in advance by the organizers, then checked and loaded in Notebook 2
- Full inference: retained in Notebook 2 as an optional GPU reproducibility section
- Live training: intentionally skipped because of workshop time and Colab compute limits

The notebooks follow the same lymph-node sample from RNA input through prediction and biological
interpretation. Inferred proteins are predictions, not measurements; the hands-on analysis therefore
emphasizes spatial and anatomical coherence rather than pointwise protein accuracy.

## Participant support

Read [PARTICIPANT_SETUP.md](PARTICIPANT_SETUP.md) before attending. It covers preparation,
direct notebook links, restart behavior, and common troubleshooting steps.
