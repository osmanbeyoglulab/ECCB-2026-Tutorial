# ECCB Tutorial: Spatial Protein Inference with DGAT

Draft tutorial materials for review by the ECCB Tutorials and Workshops Committee.

This repository contains hands-on material for a 75-minute tutorial on preparing spatial omics data, running DGAT protein inference workflows, and evaluating inferred spatial protein landscapes.

Official DGAT repository: https://github.com/osmanbeyoglulab/DGAT

## Schedule

| Time | Session | Topic |
| --- | --- | --- |
| 10:45-11:05 | Hands-on Session 1 | Environment setup and spatial data exploration |
| 11:05-11:35 | Hands-on Session 2 | Running DGAT protein inference workflows |
| 11:35-12:00 | Hands-on Session 3 | Evaluation and interpretation of spatial protein predictions |

## Repository Contents

```text
.
├── notebooks/
│   ├── 01_environment_and_spatial_exploration.ipynb
│   ├── 02_dgat_protein_inference_workflow.ipynb
│   └── 03_evaluation_and_interpretation.ipynb
├── src/dgat_tutorial/
│   ├── data.py
│   ├── evaluation.py
│   ├── plotting.py
│   └── dgat.py
├── data/
│   ├── raw/          # downloaded or user-provided input data, not committed
│   └── processed/    # generated intermediate files, not committed
├── scripts/
│   ├── download_dgat_assets.sh
│   └── run_tutorial_demo.py
├── results/
│   └── figures/      # generated figures, not committed
├── environment.yml
├── requirements.txt
└── tutorial_checklist.md
```

## Quick Start for the Tutorial Notebooks

Create the environment with conda:

```bash
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
python -m ipykernel install --user --name eccb-dgat-tutorial --display-name "ECCB DGAT Tutorial"
jupyter lab
```

Or use pip in an existing Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

Open the notebooks in order:

1. `notebooks/01_environment_and_spatial_exploration.ipynb`
2. `notebooks/02_dgat_protein_inference_workflow.ipynb`
3. `notebooks/03_evaluation_and_interpretation.ipynb`

The intended tutorial path uses the official DGAT `.h5ad` data assets directly. The notebooks still have a small synthetic fallback for environment checks, but the final tutorial should be run from the DGAT files downloaded from Google Drive.

## Official DGAT Setup

This tutorial repository does not vendor DGAT model code. It wraps the official DGAT implementation with teaching notebooks for data preparation, visualization, and evaluation.

Clone the official DGAT repository into `external/`:

```bash
mkdir -p external
git clone https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
```

Then follow the current installation instructions in the official DGAT README. At the time these tutorial materials were prepared, the official README described a Python 3.11 setup and separate CPU/CUDA requirements files. Treat the official repository as the source of truth because dependency pins may change.

Recommended local layout:

```text
eccb-dgat-tutorial/
├── external/
│   ├── DGAT/
│   └── DGAT_assets/
├── data/
│   ├── raw/
│   └── processed/
└── notebooks/
```

## Download DGAT Checkpoints and Data

The original DGAT repository provides tutorial data and checkpoint assets through this Google Drive folder:

https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C

Download the full folder before the tutorial. For pretrained prediction, the key assets are expected to include:

- `DGAT_prediction_ST_data`
- `DGAT_pretrained_models`

Option A: download manually from the browser.

1. Open the Google Drive folder above.
2. Download the complete folder contents.
3. Place the downloaded contents under `external/DGAT_assets/`.

Option B: download with `gdown`.

```bash
python -m pip install gdown
bash scripts/download_dgat_assets.sh
```

The helper script downloads the Drive folder into `external/DGAT_assets/`. After download, check that the expected asset folders exist:

```bash
ls external/DGAT_assets
```

For the official DGAT pretrained prediction notebooks/scripts, copy or symlink the required folders beside the official DGAT README in `external/DGAT/`, matching the upstream instructions:

```bash
ln -s ../DGAT_assets/DGAT_prediction_ST_data external/DGAT/DGAT_prediction_ST_data
ln -s ../DGAT_assets/DGAT_pretrained_models external/DGAT/DGAT_pretrained_models
```

If symlinks are inconvenient on your platform, copy those folders instead.

## Tutorial Data

For the live tutorial, use the DGAT-provided `.h5ad` prediction data directly, matching the original DGAT workflow. After running `scripts/download_dgat_assets.sh`, the tutorial loader searches these locations automatically:

- `external/DGAT_assets/DGAT_prediction_ST_data/**/*.h5ad`
- `external/DGAT_assets/**/*.h5ad`
- `external/DGAT/DGAT_prediction_ST_data/**/*.h5ad`
- `data/raw/**/*.h5ad`

The expected AnnData structure is:

- transcript expression in `adata.X`;
- spatial coordinates in `adata.obsm["spatial"]` or coordinate columns in `adata.obs`;
- observed protein/ADT values in one of `adata.obsm["protein"]`, `adata.obsm["proteins"]`, `adata.obsm["protein_expression"]`, `adata.obsm["protein_expression_raw"]`, `adata.obsm["ADT"]`, or `adata.obsm["CITE"]`.

Optional precomputed DGAT predictions can still be supplied as `data/raw/dgat_predictions.csv` or generated into `data/processed/predicted_proteins.csv` for the evaluation notebook.

Large raw datasets, checkpoints, and generated files are intentionally ignored by Git. The GitHub repository should document the official download rather than committing DGAT assets directly.

## DGAT Prediction Output Contract

Session 2 and Session 3 expect precomputed predictions in this format:

- File: `data/raw/dgat_predictions.csv`
- Rows: spot/cell IDs matching the `.h5ad` observation names
- Columns: protein names
- Values: inferred protein expression values

Example:

```csv
spot_id,CD3,CD19,EPCAM,COL1A1,PDL1,KI67
spot_000,0.41,1.22,0.08,2.31,0.55,0.74
spot_001,0.39,1.18,0.10,2.27,0.61,0.79
```

For the live tutorial, run the official DGAT prediction workflow once as a demonstration, then let everyone continue from `data/raw/dgat_predictions.csv`. This keeps the tutorial focused on spatial data preparation, predicted protein landscapes, and biological interpretation instead of installation troubleshooting.

## Script Demo

The repository includes a lightweight script demo that uses synthetic spatial-CITE-seq-like data. This is not the official DGAT model and should only be used to verify the tutorial environment and output format when DGAT assets are not yet downloaded.

```bash
PYTHONPATH=src python scripts/run_tutorial_demo.py
```

Outputs:

- `data/processed/demo_spots.csv`
- `data/processed/demo_transcripts.csv`
- `data/processed/demo_observed_proteins.csv`
- `data/processed/predicted_proteins.csv`
- `results/demo_prediction_correlations.csv`

## Jupyter Notebook Demo

The main tutorial is notebook-based. Start Jupyter Lab:

```bash
jupyter lab
```

Run the notebooks in order:

1. `notebooks/01_environment_and_spatial_exploration.ipynb`
   - environment check
   - spatial transcript/protein data loading
   - coordinate and neighborhood exploration
2. `notebooks/02_dgat_protein_inference_workflow.ipynb`
   - input alignment
   - official DGAT prediction handoff
   - `data/raw/dgat_predictions.csv` fallback
   - predicted protein visualization
3. `notebooks/03_evaluation_and_interpretation.ipynb`
   - Pearson/Spearman evaluation
   - Moran's I spatial coherence
   - transcript versus observed and inferred protein comparison
   - biological interpretation prompts

## Learning Objectives

By the end of the tutorial, participants should be able to:

- Load and inspect spatial transcriptomics and spatial-CITE-seq data in Python.
- Visualize transcript, protein, and neighborhood-level spatial structure.
- Prepare model inputs for DGAT-style protein inference workflows.
- Run a pretrained inference workflow or load prepared predictions.
- Evaluate predictions using correlation metrics and spatial autocorrelation.
- Interpret successes, failures, and common biological pitfalls.

## Before Uploading to GitHub

See `tutorial_checklist.md` for a review checklist aligned with the 1 July draft-materials deadline.

Minimum items to finalize before committee review:

- Choose the exact official DGAT notebook or command to demonstrate live.
- Generate a real `data/raw/dgat_predictions.csv` from the tutorial dataset.
- Confirm the official DGAT checkpoint and data download works on a clean machine.
- Confirm the notebooks can read the downloaded DGAT `.h5ad` file directly.
- Record expected runtime and whether CPU is sufficient.
- Render or execute all notebooks once before upload.
