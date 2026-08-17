# ECCB 2026 Tutorial: DGAT — Inferring Spatial Protein Landscapes from Transcriptomics

This repository contains the participant materials for the ECCB 2026 tutorial on computational
inference of spatial protein landscapes. The hands-on workflow runs in **Google Colab** using the
10x Genomics Visium **V1 Human Lymph Node** transcript-only dataset.

Participants use organizer-validated precomputed DGAT predictions by default. Complete inference
is available as an optional GPU reproducibility section; no measured lymph-node protein modality is
used for direct accuracy evaluation.

## Start here

Complete Notebook 0 before the workshop, then open one notebook per teaching session.

| Step | Notebook | Open in Colab |
| --- | --- | --- |
| Pre-work | `00_colab_setup.ipynb` | [Prepare Google Drive](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb) |
| Session 1 | `01_data_and_spatial.ipynb` | [Data and spatial context](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb) |
| Session 2 | `02_model_and_predictions.ipynb` | [Model and predictions](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb) |
| Session 3 | `03_evaluation_and_interpretation.ipynb` | [Evaluation and interpretation](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb) |

Use Colab runtime version **2026.04 (Python 3.12)** for all four notebooks. Full preparation and
troubleshooting instructions are in the
[participant setup guide](hands-on_tutorial/PARTICIPANT_SETUP.md).

## What participants need

- A laptop and charger
- A current web browser
- A Google account with Google Drive access
- At least 1 GB of free Google Drive space
- A stable connection for the one-time pre-workshop download

No local Python, Conda, Jupyter, CUDA, or GPU installation is required.

## Tutorial materials

- [Participant setup guide](hands-on_tutorial/PARTICIPANT_SETUP.md)
- [Hands-on overview](hands-on_tutorial/README.md)
- [Presentation PDF](overview/Osmanbeyoglu_ECCB_Tutorial_2026_hands_on_with_outputs.pdf)
- [Official DGAT repository](https://github.com/osmanbeyoglulab/DGAT)

## Tutorial schedule

| Time | Topic |
| --- | --- |
| 09:00–10:30 | Spatial omics technologies, protein inference, and DGAT |
| 10:30–10:45 | Coffee break |
| 10:45–11:15 | Session 1: lymph-node morphology, GC labels, and RNA QC |
| 11:15–11:40 | Session 2: validated precomputed DGAT predictions |
| 11:40–12:00 | Session 3: evaluation and interpretation |
| 12:00–12:45 | Best practices, future directions, discussion, and wrap-up |

## Learning outcomes

By the end of the tutorial, participants will be able to:

- explain why RNA abundance does not always predict protein abundance;
- describe how molecular and spatial graphs are used by DGAT;
- assess transcriptomic coverage for RNA-only spatial inference;
- load and inspect pretrained spatial protein predictions;
- evaluate predictions using anatomical and spatial diagnostics; and
- recognize dataset shift, batch effects, missing cell types, and overinterpretation risks.
