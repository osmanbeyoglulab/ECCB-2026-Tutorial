# ECCB 2026 Tutorial: DGAT — Inferring Spatial Protein Landscapes from Transcriptomics: Methods, Assumptions, and Pitfalls

This repository contains the lecture slides (PDF) and hands-on materials for the ECCB 2026 tutorial on computational inference of spatial protein landscapes. The tutorial introduces spatial transcriptomics, spatial proteomics, and multimodal technologies; examines why spatial context matters for transcript-to-protein prediction; and presents the assumptions, evaluation strategies, and common pitfalls associated with computational protein inference.

Participants work through a DGAT-based workflow in **Google Colab** using the **10x Genomics CytAssist Tonsil** example. Full model training is skipped because of compute constraints; notebooks teach the architecture and losses, then evaluate verified pretrained predictions. Notebooks are committed **with executed outputs** so figures are visible inline.

By the end of the tutorial, participants will be able to:

- Explain why protein abundance cannot always be inferred directly from RNA expression.
- Describe major spatial transcriptomics, spatial proteomics, and multimodal technologies.
- Understand how tissue architecture and spatial neighborhoods inform protein prediction.
- Compare spatial and non-spatial protein-inference approaches.
- Explain the molecular and spatial graph components of DGAT.
- Load verified pretrained DGAT predictions on Tonsil spatial transcriptomics data.
- Evaluate predictions using correlation, spatial coherence, and biological validation.
- Recognize dataset shift, batch effects, missing cell types, overinterpretation, and other common failure modes.

## Table of contents

- [Repository layout](#repository-layout)
- [Presentation materials](#presentation-materials)
- [Start here](#start-here)
- [Tutorial schedule](#tutorial-schedule)

## Repository layout

```text
.
├── overview/
│   └── Osmanbeyoglu_ECCB_Tutorial_2026.pdf
├── hands-on_tutorial/
│   ├── notebooks/              # Session 0 Colab setup + Sessions 1–3 (executed outputs)
│   ├── checkpoints/            # generated completion manifests
│   ├── data/                   # committed Tonsil predictions + local data
│   ├── scripts/                # command-line and organizer workflows
│   ├── src/dgat_tutorial/      # shared Python package
│   ├── results/                # generated tables and figures
│   ├── PARTICIPANT_SETUP.md
│   └── README.md
├── CITATION.cff
├── LICENSE
└── README.md
```

## Presentation materials

- [View or download the presentation PDF](overview/Osmanbeyoglu_ECCB_Tutorial_2026.pdf)

Lecture slides are distributed as PDF only (no PowerPoint in this repository).

## Start here

- Presenters: open the [PDF](overview/Osmanbeyoglu_ECCB_Tutorial_2026.pdf) or the [`overview/` guide](overview/README.md).
- Participants: follow [`hands-on_tutorial/PARTICIPANT_SETUP.md`](hands-on_tutorial/PARTICIPANT_SETUP.md) and start with the Colab setup notebook:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_00/00_colab_setup.ipynb)

- Instructors: run order and checkpoint map in [`hands-on_tutorial/README.md`](hands-on_tutorial/README.md).

Official DGAT repository: <https://github.com/osmanbeyoglulab/DGAT>

## Tutorial schedule

| Time | Session | Topic |
| --- | --- | --- |
| 09:00–09:15 | Motivation and challenges in spatial protein inference |
| 09:15–10:00 | Spatial omics technologies |
| 10:00–10:30 | Computational protein inference and DGAT |
| 10:30–10:45 | Coffee break |
| 10:45–11:15 | Hands-on Session 1 | Colab setup, Tonsil data, QC, and normalization |
| 11:15–11:40 | Hands-on Session 2 | DGAT architecture, loss discussion (no training), pretrained inference |
| 11:40–12:00 | Hands-on Session 3 | Evaluation and interpretation |
| 12:00–12:20 | Best practices and future directions |
| 12:20–12:45 | Discussion and wrap-up |

**Timing note:** participants should complete the Drive preparation notebook before the workshop.
Instructors should prioritize Session 1 validation + Session 2
architecture/provenance + Session 3 evaluation. Full DGAT training is out of scope for the live
Colab path.

The tutorial uses four participant-facing notebooks: one pre-workshop Drive preparation notebook
plus one restart-safe notebook per teaching session. Large assets and completion state persist in
Google Drive; each session runtime shallow-clones only the small code repository and installs only
missing session-specific packages.
