# ECCB 2026 Tutorial: Computational inference of spatial protein landscapes: methods, assumptions and pitfalls

This repository contains the lecture slides and hands-on materials for the ECCB 2026 tutorial on computational inference of spatial protein landscapes. The tutorial introduces spatial transcriptomics, spatial proteomics, and multimodal technologies; examines why spatial context matters for transcript-to-protein prediction; and presents the assumptions, evaluation strategies, and common pitfalls associated with computational protein inference.

By the end of the tutorial, participants will be able to:

- Explain why protein abundance cannot always be inferred directly from RNA expression.
- Describe major spatial transcriptomics, spatial proteomics, and multimodal technologies.
- Understand how tissue architecture and spatial neighborhoods inform protein prediction.
- Compare spatial and non-spatial protein-inference approaches.
- Explain the molecular and spatial graph components of DGAT.
- Load and inspect pretrained DGAT predictions on spatial transcriptomics data.
- Evaluate predictions using correlation, spatial coherence, and biological validation.
- Recognize dataset shift, batch effects, missing cell types, overinterpretation, and other common failure modes.

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
| 09:00–09:15 | Motivation and challenges in spatial protein inference |
| 09:15–10:00 | Spatial omics technologies |
| 10:00–10:30 | Computational protein inference and DGAT |
| 10:30–10:45 | Coffee break |
| 10:45–11:15 | Hands-on Session 1: lymph-node morphology, GC labels, and RNA QC |
| 11:15–11:40 | Hands-on Session 2: validated precomputed DGAT predictions |
| 11:40–12:00 | Hands-on Session 3: evaluation and interpretation |
| 12:00–12:20 | Best practices and future directions |
| 12:20–12:45 | Discussion and wrap-up |
