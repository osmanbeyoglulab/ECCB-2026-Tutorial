# Hands-on Tutorial: Inferring Spatial Protein Landscapes with DGAT

The participant workflow consists of four restart-safe Google Colab notebooks using two complementary 10x Genomics spatial datasets. 
Sessions 1–2 use paired human tonsil RNA and antibody-derived tag (ADT) data generated with the 10x Genomics Visium CytAssist Gene and Protein Expression platform. 
The matched RNA and 31-protein measurements are used to train DGAT and evaluate its protein predictions. 
Session 3 uses the transcriptome-only 10x Genomics Visium human lymph node sample (V1_Human_Lymph_Node) to demonstrate spatial protein inference with a pretrained DGAT model.

## Notebook order

| Step | Purpose | Open in Colab |
| --- | --- | --- |
| 0 | Prepare Google Drive and the workshop environment | [Open Notebook 0](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb) |
| 1 | Prepare and explore matched spatial RNA and 31-protein ADT measurements | [Open Notebook 1](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb) |
| 2 | Construct the molecular-similarity and spatial-neighborhood graphs, train DGAT, and compare predicted proteins with measured ADT values | [Open Notebook 2](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb) |
| 3 | Apply pretrained DGAT to infer 31 spatial protein profiles and interpret germinal center–associated patterns | [Open Notebook 3](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb) |

Use Colab runtime version **2026.04 (Python 3.12)** throughout. Complete Notebook 0 before the workshop, then run Notebooks 1–3 in sequence.

## How persistence works

Notebook 0 stores the paired tonsil RNA–ADT files; the lymph node gene-expression matrix, spatial coordinates, H&E image, and germinal center (GC) annotations; the organizer-generated lymph node protein predictions; a combined file manifest; a Python package cache; and persistent workflow state under `MyDrive/ECCB2026`. 
Each subsequent notebook copies only the files it requires to the Colab virtual machine, installs pinned package versions, and loads saved checkpoints. 
If the runtime disconnects, reopen the same notebook, rerun its first cell, and resume from the first unfinished checkpoint. You do not need to rerun Notebook 0 or download the datasets again.

## Dataset roles

- **Human tonsil, Sessions 1–2:** The 10x Genomics Visium CytAssist Gene and Protein Expression dataset provides spatially matched RNA expression and experimentally measured ADT abundance for 31 proteins. These paired data support multimodal quality control and preprocessing, graph construction, DGAT model training, and direct evaluation of predicted proteins against measured protein abundance.
- **Human lymph node, Session 3:** The transcriptome-only 10x Genomics Visium dataset provides gene-expression counts, spatial coordinates, an H&E image, and manual GC annotations but no measured protein data. These inputs are analyzed with an organizer-generated matrix containing DGAT-inferred spatial abundance for the same 31-protein panel.
**Default inference path:** Session 3 verifies and loads the organizer-generated predictions for downstream spatial analysis. This workflow is designed to run on a free-tier CPU runtime.
**Optional reproducibility path:** At the end of Session 3, participants can download the released model weights and rerun the complete protein-inference workflow using a GPU runtime.
**The lymph-node sample** has no measured protein modality. Its GC overlap and Moran analyses are
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
