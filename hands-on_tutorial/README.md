# DGAT hands-on tutorial

The participant workflow uses four restart-safe Google Colab notebooks and two complementary
examples: paired **Tonsil RNA/ADT** for Sessions 1–2, followed by the transcript-only 10x Visium
**human lymph node** sample (`V1_Human_Lymph_Node`) in Session 3.

## Notebook order

| Step | Purpose | Open in Colab |
| --- | --- | --- |
| 0 | Prepare Google Drive once before the workshop | [Open Notebook 0](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb) |
| 1 | Prepare and explore paired Tonsil RNA and measured ADT | [Open Notebook 1](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb) |
| 2 | Build paired graphs, explain DGAT, and inspect Tonsil predictions | [Open Notebook 2](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb) |
| 3 | Apply pretrained DGAT to lymph node and interpret GC-associated spatial patterns | [Open Notebook 3](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb) |

Use Colab runtime version **2026.04 (Python 3.12)** throughout.

## How persistence works

Notebook 0 stores the paired Tonsil files, lymph-node matrix and spatial/H&E bundle, GC annotation,
validated precomputed lymph-node prediction matrix, a combined manifest, a Python wheel cache, and
persistent state under `MyDrive/ECCB2026`. Each notebook copies only its required dataset to the
Colab VM, installs the pinned packages it needs, and reconnects saved checkpoints.

If a runtime disconnects, reopen the same notebook, rerun its first cell, and continue from the
first unfinished checkpoint. You do not need to repeat Notebook 0 or redownload the dataset.

## Dataset roles

- **Tonsil, Sessions 1–2:** paired spatial RNA and measured ADT support multimodal QC,
  preprocessing, graph construction, and DGAT model instruction.
- **Human lymph node, Session 3:** transcript counts, spatial coordinates, H&E morphology, and
  manual GC annotations are aligned to a precomputed 31-protein DGAT prediction matrix.
- **Default inference path:** Session 3 validates and loads the organizer-generated predictions;
  this is designed for a free-tier CPU runtime.
- **Optional reproducibility path:** the end of Session 3 can download the released weights and
  rerun full inference in a GPU runtime.

The lymph-node sample has no measured protein modality. Its GC overlap and Moran analyses are
therefore **indirect biological evaluation**, not direct protein-level validation. Inferred proteins
remain model predictions, and spatial co-localization does not establish molecular interaction or
causality.

## Planning estimates

- Notebook 0: 5–10 minutes and approximately 400 MB of downloads.
- Sessions 1–2: 5–15 minutes each on a standard free-tier CPU runtime; allow about 12 GB system RAM.
- Session 3 default: 3–5 minutes on CPU with no GPU memory requirement.
- Optional Session 3 inference: 15–30 minutes including setup; use at least 12 GB system RAM and
  8 GB GPU RAM. Colab allocations and observed runtimes vary.

## Participant support

Read [PARTICIPANT_SETUP.md](PARTICIPANT_SETUP.md) before attending. It covers preparation,
direct notebook links, restart behavior, and common troubleshooting steps.
