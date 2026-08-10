# Session 0: Google Colab setup

The hands-on tutorial runs in **Google Colab**. Participants do not need a local Conda
environment or GPU. Full DGAT training is skipped because of Colab compute limits; Session 2
teaches the architecture and losses, then loads verified pretrained Tonsil predictions.

The example dataset is the **10x Genomics CytAssist Tonsil** paired RNA/ADT sample used by DGAT
(`Tonsil_RNA.h5ad` / `Tonsil_ADT.h5ad`).

## What participants need

- A Google account
- A current web browser
- Stable network for the first-time repo clone and ~350 MB Tonsil download

## Step 1 — Open the Colab setup notebook

Open this notebook in Colab (GitHub → Open in Colab, or use the badge in
[`README.md`](README.md)):

[`notebooks/session_00/00_colab_setup.ipynb`](notebooks/session_00/00_colab_setup.ipynb)

Run every cell top to bottom. It will:

1. clone this repository under `/content` (or refresh an existing clone);
2. `pip install` the lightweight tutorial package and dependencies;
3. download and verify the Tonsil RNA/ADT assets;
4. confirm that `data/raw/dgat_predictions.csv` is present.

Checkpoint: the final cell should print `Tutorial root: .../hands-on_tutorial` and
`Colab setup complete`.

## Step 2 — Keep the Colab runtime and open Session 1

Stay in the same Colab runtime (do not disconnect). Open the Session 1A notebook from the
cloned tree, or use the Open-in-Colab badges in [`README.md`](README.md).

Before the first Session notebook in a new Colab file, run the short bootstrap cell at the top
of that notebook (it rediscovers `hands-on_tutorial/`). If you started a **new** runtime, re-run
`00_colab_setup.ipynb` first.

Recommended order (two restart-friendly notebooks per teaching session):

1. `notebooks/session_01/01_data_preparation.ipynb`
2. `notebooks/session_01/02_spatial_context.ipynb`
3. `notebooks/session_02/01_dgat_model.ipynb` — includes the loss discussion; **training is skipped**
4. `notebooks/session_02/02_predictions.ipynb`
5. `notebooks/session_03/01_quantitative_evaluation.ipynb`
6. `notebooks/session_03/02_interpretation.ipynb`

## Step 3 — Confirm the inference artifact

In Session 2 Part 4, the notebook should print the DGAT method and evaluation caveat, then write
a processed prediction table with its provenance sidecar. Participants load the committed CSV;
they do **not** run official `protein_predict` during the workshop.

## Timing budget (Colab)

| Block | Typical time |
| --- | --- |
| Open setup notebook + clone/install | 3–8 min |
| Tonsil download (~350 MB) + check | 2–10+ min (network-dependent) |
| Sessions 1–3 guided execution | remainder of hands-on blocks |

If Colab disk or network fails, ask an instructor for the mirrored notebook runtime or the
pre-staged Tonsil assets.

## Optional local Conda path (organizers / offline)

Local Conda remains available for organizers and offline dry-runs:

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial/hands-on_tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil
jupyter lab
```

Participants in the live ECCB session should prefer Colab unless an instructor directs otherwise.

## Troubleshooting

- **`ModuleNotFoundError: dgat_tutorial` in Session 0:** make sure the setup notebook is
  up to date, then re-run its Step 2 cell. The cell explicitly exposes the editable package's
  `src/` directory to the already-running Colab kernel; a runtime restart is not required.
- **Tutorial root missing in a Session 1–3 notebook:** re-run `00_colab_setup.ipynb` in this
  runtime.
- **Runtime disconnected:** reconnect and re-run setup; Colab does not keep `/content` forever.
- **Wrong dataset:** do not substitute Breast or other samples for the Tonsil participant path.
- **Want to train DGAT:** not part of this tutorial. See the upstream
  [DGAT repository](https://github.com/osmanbeyoglulab/DGAT) and organizer docs.
