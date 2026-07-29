# Hands-on tutorial

This directory is a self-contained, executable tutorial for DGAT spatial protein inference. Run setup commands from this directory so paths are consistent in Jupyter, scripts, tests, and Docker.

## Quick start

Complete the data download before the conference; the live tutorial should not depend on conference Wi-Fi.

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial/hands-on_tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only
jupyter lab
```

For detailed participant preparation and troubleshooting, see [`PARTICIPANT_SETUP.md`](PARTICIPANT_SETUP.md).

## Run order and checkpoints

Every notebook is independently runnable after participant setup. It discovers the tutorial root, reloads the source data it needs, writes named artifacts under `results/` or `data/processed/`, and records completion in `checkpoints/session_XX/part_X_X.json`.

| Part | Notebook | Output checkpoint |
| --- | --- | --- |
| 1.1 | `notebooks/session_01/01_load_and_validate.ipynb` | dataset summary |
| 1.2 | `notebooks/session_01/02_quality_control.ipynb` | QC tables and figure |
| 1.3 | `notebooks/session_01/03_spatial_neighborhoods.ipynb` | neighborhood table and spatial figures |
| 2.1 | `notebooks/session_02/01_prepare_inputs.ipynb` | aligned spot IDs and input summary |
| 2.2 | `notebooks/session_02/02_load_predictions.ipynb` | prediction matrix and provenance sidecar |
| 2.3 | `notebooks/session_02/03_visualize_predictions.ipynb` | predicted-protein spatial figure |
| 3.1 | `notebooks/session_03/01_correlation_evaluation.ipynb` | correlation table and figure |
| 3.2 | `notebooks/session_03/02_spatial_coherence.ipynb` | Moran's I table and figure |
| 3.3 | `notebooks/session_03/03_interpret_landscapes.ipynb` | landscape figure and discussion prompts |

### Resume behavior

- Parts never depend on in-memory state from an earlier notebook.
- Session 2, Part 2 can run without Part 1 because it validates the committed prediction artifact directly.
- Session 2, Part 3 and all Session 3 parts prefer `data/processed/predicted_proteins.csv` when it exists, then fall back to the committed `data/raw/dgat_predictions.csv`.
- Session 1 permits a clearly labeled synthetic fallback for environment checks.
- Sessions 2 and 3 require the official matching DGAT data; they fail with an actionable error instead of mixing predictions with synthetic observations.

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

Organizers can download all supported data and model weights:

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

For a synthetic environment smoke test with an explicitly labeled out-of-fold ridge baseline:

```bash
PYTHONPATH=src python scripts/run_tutorial_demo.py
```

The baseline is not DGAT and must not be presented as a DGAT result.

## Official DGAT inference (organizers, optional)

Official inference uses a separate Python 3.11 environment and should be run before the live session:

```bash
conda env create -f environment-dgat-cpu.yml
conda activate eccb-dgat-official
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
bash scripts/download_dgat_assets.sh
PYTHONPATH=src python scripts/check_dgat_environment.py
PYTHONPATH=src python scripts/run_official_dgat_prediction.py --help
```

Do not install the official DGAT dependency stack into the lightweight participant environment.

## Verification

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m compileall src scripts
```

Organizer dry-run notes and the upload checklist are in [`docs/`](docs/).
