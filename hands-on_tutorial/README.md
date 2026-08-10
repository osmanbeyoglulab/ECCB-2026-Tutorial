# Hands-on tutorial

Self-contained DGAT spatial protein inference tutorial for ECCB 2026.

**Runtime:** [Google Colab](https://colab.research.google.com/) (preferred for participants).

**Dataset:** 10x Genomics CytAssist **Tonsil** paired RNA/ADT (`Tonsil_RNA.h5ad` / `Tonsil_ADT.h5ad`).

**Training:** skipped in the live path because of Colab compute limits; notebooks teach the
objective and load verified pretrained predictions.

**Notebooks:** committed with executed outputs so plots are visible inline on GitHub and in Colab.

## Start in Colab

1. Before the workshop, open Session 0 and prepare Google Drive:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_00/00_colab_setup.ipynb)

2. Follow the worksheet: [`PARTICIPANT_SETUP.md`](PARTICIPANT_SETUP.md).

   Use Colab runtime version **2026.04** (Python 3.12) for preparation and all three sessions.

3. During the workshop, open one notebook per teaching session. Each notebook may use a fresh
   Colab runtime; data and completed artifacts persist under `MyDrive/ECCB2026`.

| Session | Notebook | Colab |
| --- | --- | --- |
| 0 | `notebooks/session_00/00_colab_setup.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_00/00_colab_setup.ipynb) |
| 1 | `notebooks/session_01/session_01_data_and_spatial.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_01/session_01_data_and_spatial.ipynb) |
| 2 | `notebooks/session_02/session_02_model_and_predictions.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_02/session_02_model_and_predictions.ipynb) |
| 3 | `notebooks/session_03/session_03_evaluation_and_interpretation.ipynb` | [Open](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/session_03/session_03_evaluation_and_interpretation.ipynb) |

## Run order and checkpoints

Each session notebook begins with a restart-safe bootstrap. In Colab it mounts Drive, shallow-clones
the small code repository, copies the pre-staged Tonsil files to fast local storage, and installs only
missing session-specific packages. Outputs and completion manifests are written to
`MyDrive/ECCB2026/state/`.

| Teaching notebook | Included parts and outputs |
| --- | --- |
| Session 0 preparation | Drive assets, checksums, wheel cache, and persistent state folders |
| Session 1 data + spatial | 1.1 validated object; 1.2 QC/normalization; 1.3 graphs, maps, and embeddings |
| Session 2 model + predictions | 2.1 graph inputs; 2.2 architecture; 2.3 losses; 2.4 provenance; 2.5 maps |
| Session 3 evaluation + interpretation | 3.1 pointwise metrics; 3.2 spatial coherence; 3.3 interpretation |

### Resume behavior

- Rerun only the first bootstrap cell after a runtime reset, then jump to the first unfinished part
  shown by its checkpoint. Parts reload their required inputs instead of relying on earlier memory.
- Colab state lives under `MyDrive/ECCB2026/state`; local runs continue using repository paths.
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
│   ├── session_00/          # pre-workshop Drive preparation
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
├── requirements-colab.txt   # cached Colab add-ons (Sessions 1–2; Session 3 uses a subset)
├── requirements.txt
└── pyproject.toml
```

## Data and prediction provenance

Participant notebooks use the Tonsil `.h5ad` pair and committed
`data/raw/dgat_predictions.csv`. Colab Session 0 downloads measurements to
`MyDrive/ECCB2026/assets/DGAT_assets/data`; it does **not** run `protein_predict`. Organizers regenerate predictions with
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
