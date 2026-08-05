# Hands-on tutorial

This directory is a self-contained, executable tutorial for DGAT spatial protein inference. Run setup commands from this directory so paths are consistent in Jupyter, scripts, tests, and Docker.

## Session 0 — live setup

Environment creation and data acquisition are part of the tutorial. At the beginning of the session, the
instructor will explain and run each command with participants:

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial/hands-on_tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only
jupyter lab
```

Do not run these steps in advance. The instructor will pause after environment creation and after the asset check
so setup problems can be resolved as a group. The live worksheet is [`PARTICIPANT_SETUP.md`](PARTICIPANT_SETUP.md).

## Run order and checkpoints

Every notebook is independently runnable after the live Session 0 checkpoint. It discovers the tutorial root, reloads the source data it needs, writes named artifacts under `results/` or `data/processed/`, and records completion in `checkpoints/session_XX/part_X_X.json`.

| Part | Notebook | Output checkpoint |
| --- | --- | --- |
| 1.1 | `notebooks/session_01/01_load_and_validate.ipynb` | validated multi-modal data-object summary |
| 1.2 | `notebooks/session_01/02_quality_control.ipynb` | RNA/protein QC, filtering audit, normalized matrices, and figures |
| 1.3 | `notebooks/session_01/03_spatial_neighborhoods.ipynb` | spatial graph, normalized feature maps, and modality embeddings |
| 2.1 | `notebooks/session_02/01_prepare_inputs.ipynb` | paired graph dimensions, aligned IDs, and edge index |
| 2.2 | `notebooks/session_02/02_build_dgat_model.ipynb` | four-module architecture table and figure |
| 2.3 | `notebooks/session_02/03_train_dgat.ipynb` | five-loss training workflow and optional official training call |
| 2.4 | `notebooks/session_02/04_load_predictions.ipynb` | prediction matrix and provenance sidecar |
| 2.5 | `notebooks/session_02/05_visualize_predictions.ipynb` | prediction distributions and spatial maps |
| 3.1 | `notebooks/session_03/01_correlation_evaluation.ipynb` | correlation table and figure |
| 3.2 | `notebooks/session_03/02_spatial_coherence.ipynb` | Moran's I table and figure |
| 3.3 | `notebooks/session_03/03_interpret_landscapes.ipynb` | landscape figure and discussion prompts |

### Resume behavior

- Parts never depend on in-memory state from an earlier notebook.
- Every data-consuming notebook requires the official paired Breast RNA/ADT files downloaded during Session 0.
- Session 2, Part 3 defines and explains a complete optimization step. The upstream full-data training call is opt-in and requires the separate official environment and training assets.
- Session 2, Part 4 can run without earlier parts because it validates the committed prediction artifact directly.
- Session 2, Part 5 and all Session 3 parts prefer `data/processed/predicted_proteins.csv` when it exists, then fall back to the committed `data/raw/dgat_predictions.csv`.
- If the Breast RNA/ADT pair is missing or incomplete, the notebooks stop with the Session 0 download and verification commands.
- Session 2 Parts 4–5 and Session 3 require the official matching DGAT data and predictions; they never mix datasets.

To reset only the generated checkpoints, remove the JSON files inside `checkpoints/session_*/`. The source notebooks and committed data are unaffected.

## Directory map

```text
hands-on_tutorial/
├── notebooks/
│   ├── session_01/
│   ├── session_02/
│   └── session_03/
├── checkpoints/
│   ├── session_01/
│   ├── session_02/
│   └── session_03/
├── data/
│   ├── raw/
│   └── processed/
├── results/figures/
├── scripts/
├── src/dgat_tutorial/
├── tests/
├── docs/
├── environment.yml
├── environment-dgat-cpu.yml
├── requirements.txt
└── pyproject.toml
```

## Data and prediction provenance

The participant path uses the official DGAT `.h5ad` data and the committed verified prediction table at `data/raw/dgat_predictions.csv`. Its adjacent metadata sidecar records method, source, evaluation caveat, DGAT commit, and checkpoint hashes. The notebooks never silently fit a model to evaluation proteins.

Download the participant data only:

```bash
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
```

Repository maintainers can reproduce all supported assets outside the participant workflow:

```bash
bash scripts/download_dgat_assets.sh
bash scripts/download_dgat_assets.sh --check-only
```

Downloaded assets live under `external/DGAT_assets/` and remain ignored by Git.

## Command-line path

The existing session scripts provide a non-Jupyter route:

```bash
PYTHONPATH=src python scripts/session01_spatial_exploration.py
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py
PYTHONPATH=src python scripts/session03_evaluation_interpretation.py
```

## Maintainer-only DGAT artifact reproduction

This route documents how the committed prediction artifact was produced. It is not a participant prerequisite or
an environment-setup step in the tutorial. Participants create only the lightweight environment during Session 0.

```bash
conda env create -f environment-dgat-cpu.yml
conda activate eccb-dgat-official
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
bash scripts/download_dgat_assets.sh
PYTHONPATH=src python scripts/check_dgat_environment.py
PYTHONPATH=src python scripts/run_official_dgat_prediction.py --help
```

Do not install the official DGAT dependency stack into the lightweight participant environment.

## What participants learn

The notebook sequence now exposes the complete path instead of starting from a saved model:

1. validate a paired spatial RNA/protein object;
2. inspect modality-specific QC and visualize filtering/normalization effects;
3. create the spatial kNN edge index;
4. construct the RNA encoder, protein encoder, RNA decoder, and branched protein decoder;
5. combine reconstruction, alignment, and cross-modal prediction losses in the training loop;
6. understand validation, checkpointing, and RNA-only inference; and
7. generate QC, predicted-landscape, correlation, spatial-coherence, and interpretation figures.

## Verification

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m compileall src scripts
```

Organizer dry-run notes and the upload checklist are in [`docs/`](docs/).
