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

## Quick Start

The default tutorial path uses one conda environment and the official DGAT `.h5ad` data assets. Official DGAT model execution is optional and described later.

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
bash scripts/download_dgat_assets.sh
jupyter lab
```

Open the notebooks in order:

1. `notebooks/01_environment_and_spatial_exploration.ipynb`
2. `notebooks/02_dgat_protein_inference_workflow.ipynb`
3. `notebooks/03_evaluation_and_interpretation.ipynb`

The default environment includes the packages needed for the tutorial notebooks, including JupyterLab, Scanpy, AnnData, Squidpy, scikit-learn, matplotlib, pandas, NumPy, SciPy, seaborn, and gdown. It intentionally does not directly install PyTorch Geometric or the full official DGAT dependency stack.

## Repository Contents

```text
.
├── notebooks/
│   ├── 01_environment_and_spatial_exploration.ipynb
│   ├── 02_dgat_protein_inference_workflow.ipynb
│   └── 03_evaluation_and_interpretation.ipynb
├── scripts/
│   ├── download_dgat_assets.sh
│   ├── session01_spatial_exploration.py
│   ├── session02_dgat_inference_workflow.py
│   ├── session03_evaluation_interpretation.py
│   ├── run_official_dgat_prediction.py
│   └── run_tutorial_demo.py
├── src/dgat_tutorial/
│   ├── data.py
│   ├── dgat.py
│   ├── evaluation.py
│   └── plotting.py
├── data/              # local data outputs, not committed
├── external/          # downloaded DGAT repo/assets, not committed
├── results/           # generated tables and figures, not committed
├── Dockerfile
├── environment.yml
├── requirements.txt
└── tutorial_checklist.md
```

## Download DGAT Data and Model Weights

The DGAT tutorial data and pretrained model weights are provided in separate Google Drive folders:

- Data: https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C
- Model weights: https://drive.google.com/drive/folders/1uRYhgVgUpkhpE9VTtUB5YmU_hRsf69oD

The Quick Start command downloads both folders with `gdown`:

```bash
bash scripts/download_dgat_assets.sh
```

The helper script downloads data into `external/DGAT_assets/data/`, model weights into `external/DGAT_assets/model_weights/`, and checks whether `.h5ad` files and DGAT model weight files were found. You can inspect the downloaded layout with:

```bash
ls external/DGAT_assets
find external/DGAT_assets -name "*.h5ad"
find external/DGAT_assets \( -name "encoder_mRNA.pth" -o -name "decoder_protein.pth" \)
```

If `gdown` cannot download a Google Drive folder because of permissions, quota, or shortcut handling, download the folders manually in a browser:

1. Download the complete data folder contents into `external/DGAT_assets/data/`.
2. Download the complete model-weight folder contents into `external/DGAT_assets/model_weights/`.

The tutorial scripts do not require copying or symlinking asset folders into `external/DGAT/`; they search under `external/DGAT_assets/` automatically.

## Tutorial Data

For the live tutorial, use the DGAT-provided `.h5ad` prediction data directly, matching the original DGAT workflow. After running `scripts/download_dgat_assets.sh`, the tutorial loader searches these locations automatically:

- `external/DGAT_assets/DGAT_prediction_ST_data/**/*.h5ad`
- `external/DGAT_assets/**/*.h5ad`
- `external/DGAT/DGAT_prediction_ST_data/**/*.h5ad`
- `data/raw/**/*.h5ad`

The DGAT Google Drive assets may provide paired AnnData files, for example an RNA file such as `Breast_RNA.h5ad` and an ADT/protein file such as `Breast_ADT.h5ad`. The scripts automatically pair RNA-like files with ADT/protein-like files when both are present in the downloaded asset directory.

For a single combined AnnData file, the expected structure is:

- transcript expression in `adata.X`;
- spatial coordinates in `adata.obsm["spatial"]` or coordinate columns in `adata.obs`;
- observed protein/ADT values in one of `adata.obsm["protein"]`, `adata.obsm["proteins"]`, `adata.obsm["protein_expression"]`, `adata.obsm["protein_expression_raw"]`, `adata.obsm["ADT"]`, or `adata.obsm["CITE"]`.

For paired AnnData files, the expected structure is:

- RNA/transcript expression in the RNA file's `adata.X`;
- ADT/protein expression in the ADT file's `adata.X`;
- shared observation IDs between the RNA and ADT files;
- spatial coordinates in the RNA file's `adata.obsm["spatial"]` or coordinate columns in `adata.obs`.

Optional precomputed DGAT predictions can be supplied as `data/raw/dgat_predictions.csv` or generated into `data/processed/predicted_proteins.csv` for the evaluation notebook.

Large raw datasets, checkpoints, and generated files are intentionally ignored by Git. The GitHub repository documents the official download rather than committing DGAT assets directly.

## Command-Line Tutorial Path

If you cannot run Jupyter on a remote server or HPC login node, run the same tutorial material as Python scripts:

```bash
bash scripts/download_dgat_assets.sh

PYTHONPATH=src python scripts/session01_spatial_exploration.py
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py
PYTHONPATH=src python scripts/session03_evaluation_interpretation.py
```

If you want to test the code before the DGAT assets finish downloading, add `--allow-demo`:

```bash
PYTHONPATH=src python scripts/session01_spatial_exploration.py --allow-demo
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py --allow-demo
PYTHONPATH=src python scripts/session03_evaluation_interpretation.py --allow-demo
```

Script outputs are written to:

- `results/session01_dataset_summary.csv`
- `results/session01_top_transcripts.csv`
- `results/session01_top_proteins.csv`
- `results/session01_spatial_neighbors.csv`
- `data/processed/predicted_proteins.csv`
- `results/session03_prediction_correlations.csv`
- `results/session03_morans_i.csv`
- `results/figures/*.png`

## Optional: Official DGAT Prediction

The default tutorial environment is designed for smooth notebook execution and data exploration. It does not install the full official DGAT dependency stack.

Install the optional DGAT dependencies only if you want to run the pretrained official DGAT workflow with:

```bash
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py --run-official-dgat
```

First clone the official DGAT repository into `external/`:

```bash
mkdir -p external
git clone https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
```

Then install the full official DGAT dependency stack in the active tutorial environment. The official DGAT code imports PyTorch Geometric (`torch_geometric`), so the default tutorial dependencies are not sufficient for `--run-official-dgat`. Install PyTorch first, because the correct PyTorch wheel depends on your CUDA runtime.

Check which CUDA toolkit and driver are visible on the machine:

```bash
nvcc -V
nvidia-smi
```

CUDA availability differs across laptops, clusters, and partitions. Install a PyTorch build that matches the CUDA version you will actually use. Use the official PyTorch selector as the source of truth:

https://pytorch.org/get-started/locally/

CPU-only example:

```bash
pip install torch torchvision torchaudio
pip install -r external/DGAT/requirements_CPU.txt
```

CUDA example, replace the PyTorch command with the one matching your CUDA version from the PyTorch selector:

```bash
# Example only; choose the correct CUDA build for your machine.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r external/DGAT/requirements_CUDA.txt
```

Verify the core imports before running official DGAT prediction:

```bash
python - <<'PY'
import torch
import torch_geometric
print("torch:", torch.__version__)
print("torch_geometric:", torch_geometric.__version__)
print("cuda available:", torch.cuda.is_available())
PY
```

Then run official prediction:

```bash
PYTHONPATH=src python scripts/run_official_dgat_prediction.py \
  --dgat-repo external/DGAT \
  --output data/processed/predicted_proteins.csv
```

The wrapper calls DGAT's own `Model.Train_and_Predict.protein_predict(...)`. It uses the downloaded RNA `.h5ad` file, resolves compatible `common_gene_*.txt` and `common_protein_*.txt` files from the DGAT repository/model assets, auto-discovers pretrained weights by searching for `encoder_mRNA.pth` and `decoder_protein.pth`, and writes:

```text
data/processed/predicted_proteins.csv
```

Treat the official DGAT repository as the source of truth because dependency pins may change.

## Optional: Docker Fallback

Docker is provided as a fallback for participants who cannot get conda working locally. The Docker image builds the default tutorial environment only; it does not include the optional official DGAT/PyTorch Geometric stack.

```bash
docker build -t eccb-dgat-tutorial .
docker run --rm -it -p 8888:8888 -v "$PWD":/workspace eccb-dgat-tutorial
```

Then open the JupyterLab URL printed in the terminal, or visit:

```text
http://localhost:8888/lab
```

The volume mount lets downloaded assets and generated results persist in your local checkout.

## Optional: Pip Installation

Conda is the recommended setup for tutorial participants. If you already have a compatible Python environment, you can install the default notebook dependencies with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
