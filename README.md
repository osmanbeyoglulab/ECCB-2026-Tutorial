# ECCB 2026 Tutorial: Spatial Protein Inference with DGAT

Presentation and hands-on materials for the ECCB tutorial on preparing spatial omics data, running DGAT protein-inference workflows, and evaluating inferred spatial protein landscapes.

The repository follows the presentation-first organization of the [ECCB 2024 tutorial repository](https://github.com/osmanbeyoglulab/ECCB-2024-Tutorial): the overview material is separate from a self-contained hands-on tutorial.

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
│   ├── notebooks/              # 3 sessions × 3 independent parts
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
- Participants: complete [`hands-on_tutorial/PARTICIPANT_SETUP.md`](hands-on_tutorial/PARTICIPANT_SETUP.md) before the tutorial.
- Instructors: use the run order and checkpoint map in [`hands-on_tutorial/README.md`](hands-on_tutorial/README.md).

Official DGAT repository: <https://github.com/osmanbeyoglulab/DGAT>

## Tutorial schedule

| Time | Session | Topic |
| --- | --- | --- |
| 10:45–11:05 | Hands-on Session 1 | Environment and spatial exploration |
| 11:05–11:35 | Hands-on Session 2 | DGAT protein-inference workflow |
| 11:35–12:00 | Hands-on Session 3 | Evaluation and interpretation |

Each session is divided into three independently runnable parts. Every part reloads its required inputs and writes a small JSON completion manifest under `hands-on_tutorial/checkpoints/`, making the part boundaries usable as live-session checkpoints and restart points.
