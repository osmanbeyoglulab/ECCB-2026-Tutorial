# Hands-on tutorial

Self-contained DGAT spatial protein inference tutorial for ECCB 2026.

**Runtime:** [Google Colab](https://colab.research.google.com/) (preferred for participants).

**Dataset:** 10x Genomics CytAssist **Tonsil** paired RNA/ADT (`Tonsil_RNA.h5ad` / `Tonsil_ADT.h5ad`).

**Training:** skipped in the live path because of Colab compute limits; notebooks teach the
objective and load verified pretrained predictions.

**Notebooks:** committed with executed outputs so plots are visible inline on GitHub and in Colab.

## Start in Colab

1. Open Session 0 setup:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_00/00_colab_setup.ipynb)

2. Follow the worksheet: [`PARTICIPANT_SETUP.md`](PARTICIPANT_SETUP.md).

3. Continue through the six teaching notebooks below. Keep the same Colab runtime after setup.

| Session | Notebook | Colab |
| --- | --- | --- |
| 0 | `notebooks/session_00/00_colab_setup.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_00/00_colab_setup.ipynb) |
| 1A | `notebooks/session_01/01_data_preparation.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_01/01_data_preparation.ipynb) |
| 1B | `notebooks/session_01/02_spatial_context.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_01/02_spatial_context.ipynb) |
| 2A | `notebooks/session_02/01_dgat_model.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_02/01_dgat_model.ipynb) |
| 2B | `notebooks/session_02/02_predictions.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_02/02_predictions.ipynb) |
| 3A | `notebooks/session_03/01_quantitative_evaluation.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_03/01_quantitative_evaluation.ipynb) |
| 3B | `notebooks/session_03/02_interpretation.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_03/02_interpretation.ipynb) |

## Run order and checkpoints

Each teaching notebook contains one to three clearly labeled parts. Parts rediscover the tutorial
root and reload Tonsil inputs where needed, so an instructor can resume after a Colab interruption.
They write artifacts under `results/` or `data/processed/` and retain the existing completion
manifests under `checkpoints/session_XX/part_X_X.json`.

| Teaching notebook | Included parts and outputs |
| --- | --- |
| Session 0 setup | Colab environment + Tonsil assets ready |
| Session 1A data preparation | 1.1 validated object; 1.2 QC plus saved filtered and normalized datasets |
| Session 1B spatial context | 1.3 graphs, maps, and embeddings |
| Session 2A DGAT model | 2.1 graph inputs; 2.2 architecture; 2.3 five-loss discussion |
| Session 2B predictions | 2.4 prediction provenance; 2.5 prediction maps |
| Session 3A quantitative evaluation | 3.1 pointwise metrics; 3.2 spatial coherence |
| Session 3B interpretation | 3.3 landscapes and interpretation prompts |

### Resume behavior

- Prefer **artifact handoffs** under `data/processed/` when present.
- Session 2 Part 3 explains the official five-term objective; it does **not** train a model.
- Session 2 Part 4 loads the committed Tonsil prediction artifact.
- Official DGAT graphs are `spatial 6-NN ∪ molecular 10-NN` (RNA molecular neighbors use PCA when
  >1500 genes).
- **Training** preprocessing directly calls upstream `qc_control_cytassist` + `normalize` (700 genes, 35% MT,
  2.5% gene prevalence, encoding-gene keep list, RNA scale clip 10, protein CLR via
  `muon.prot.pp.clr` default `axis=0`).
- **ST inference** preprocessing matches `fill_genes` + `preprocess_ST`.
- Model teaching defaults: `hidden_dim=1024`, encoder `dropout=0.3`,
  train loss weights `(α,β,γ,δ,η)=(5,1,1,3,1)` with soft-zero threshold `0.015`.
- Public pretrained ST checkpoints use the **11,535-gene / 31-protein** common lists.

## Directory map

```text
hands-on_tutorial/
├── notebooks/
│   ├── session_00/          # Colab setup
│   ├── session_01/          # data preparation + spatial context
│   ├── session_02/          # model concepts + pretrained predictions
│   └── session_03/          # quantitative evaluation + interpretation
├── checkpoints/
├── data/
│   ├── raw/                 # committed Tonsil predictions (+ local downloads)
│   └── processed/
├── results/figures/
├── scripts/
├── src/dgat_tutorial/
├── docs/
├── environment.yml          # optional local Conda path
├── environment-dgat-cpu.yml # organizer official-DGAT env
├── requirements.txt
└── pyproject.toml
```

## Data and prediction provenance

Participant notebooks use the Tonsil `.h5ad` pair and committed
`data/raw/dgat_predictions.csv`. Colab Session 0 downloads measurements; it does **not** run
`protein_predict`. Organizers regenerate predictions with
`scripts/run_official_dgat_prediction.py` (see `data/raw/README_PREDICTIONS.md`).

```bash
bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil
```

Downloaded assets live under `external/DGAT_assets/` and remain ignored by Git.

## Maintainer-only prediction reproduction

```bash
conda env create -f environment-dgat-cpu.yml
conda activate eccb-dgat-official
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
bash scripts/download_dgat_assets.sh
PYTHONPATH=src python scripts/run_official_dgat_prediction.py \
  --rna-h5ad external/DGAT_assets/data/Tonsil_RNA.h5ad \
  --output data/raw/dgat_predictions.csv
```

## Re-execute notebooks with outputs (maintainers)

From `hands-on_tutorial/` after Tonsil assets are present:

```bash
bash scripts/execute_tutorial_notebooks.sh
```

This writes inline plots/outputs into the Session 1–3 notebooks (Session 0 Colab setup is not
batch-executed locally).

## What participants learn

1. validate a paired spatial RNA/protein object (Tonsil);
2. inspect CytAssist *training* QC vs ST *inference* prep;
3. build spatial ∪ molecular DGAT graphs;
4. construct the four DGAT modules;
5. understand the five weighted losses without running training;
6. load verified pretrained predictions;
7. evaluate on CLR-scaled observed proteins (correlation, spatial coherence, interpretation).

Organizer dry-run notes and the upload checklist are in [`docs/`](docs/).
