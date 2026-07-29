# ECCB 2026 Tutorial: Computational inference of spatial protein landscapes: methods, assumptions and pitfalls

This repository contains the lecture slides and hands-on materials for the ECCB 2026 tutorial on computational inference of spatial protein landscapes. The tutorial introduces spatial transcriptomics, spatial proteomics, and multimodal technologies; examines why spatial context matters for transcript-to-protein prediction; and presents the assumptions, evaluation strategies, and common pitfalls associated with computational protein inference. Participants will apply these concepts through a DGAT-based workflow using Python and Jupyter notebooks.

By the end of the tutorial, participants will be able to:

- Explain why protein abundance cannot always be inferred directly from RNA expression.
- Describe major spatial transcriptomics, spatial proteomics, and multimodal technologies.
- Understand how tissue architecture and spatial neighborhoods inform protein prediction.
- Compare spatial and non-spatial protein-inference approaches.
- Explain the molecular and spatial graph components of DGAT.
- Run a pretrained DGAT model on spatial transcriptomics data.
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
│   ├── Osmanbeyoglu_ECCB_Tutorial_2026.pdf
│   └── eccb_2026_dgat_tutorial_slides.pptx
├── hands-on_tutorial/
│   ├── notebooks/              # 3 sessions; expanded five-part DGAT workflow in Session 2
│   ├── checkpoints/            # generated completion manifests
│   ├── data/                   # committed predictions + local data
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

- [Download the PowerPoint presentation](overview/eccb_2026_dgat_tutorial_slides.pptx)
- [View or download the presentation PDF](overview/Osmanbeyoglu_ECCB_Tutorial_2026.pdf)

## Start here

- Presenters: open the [PowerPoint deck](overview/eccb_2026_dgat_tutorial_slides.pptx), the [PDF](overview/Osmanbeyoglu_ECCB_Tutorial_2026.pdf), or the [`overview/` guide](overview/README.md).
- Participants: begin with the instructor-led [`hands-on_tutorial/PARTICIPANT_SETUP.md`](hands-on_tutorial/PARTICIPANT_SETUP.md) worksheet during the tutorial.
- Instructors: use the run order and checkpoint map in [`hands-on_tutorial/README.md`](hands-on_tutorial/README.md).

Official DGAT repository: <https://github.com/osmanbeyoglulab/DGAT>

## Tutorial schedule

| Time | Session | Topic |
| --- | --- | --- |
| 09:00–09:15 | Motivation and challenges in spatial protein inference |
| 09:15–10:00 | Spatial omics technologies |
| 10:00–10:30 | Computational protein inference and DGAT |
| 10:30–10:45 | Coffee break |
| 10:45–11:15 | Hands-on Session 1 | Live environment setup, data download, QC, and normalization |
| 11:15–11:40 | Hands-on Session 2 | DGAT model construction, training, and inference |
| 11:40–12:00 | Hands-on Session 3 | Evaluation and interpretation |
| 12:00–12:20 | Best practices and future directions |
| 12:20–12:45 | Discussion and wrap-up |

The tutorial uses independently runnable parts (three in Sessions 1 and 3, five in the expanded DGAT-building/training Session 2). Every part reloads its required inputs and writes a small JSON completion manifest under `hands-on_tutorial/checkpoints/`, making the part boundaries usable as live-session checkpoints and restart points.
