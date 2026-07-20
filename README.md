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

### Complete this before the tutorial

Do not wait for the conference network. In one review, downloading the full data and model bundle took about **15 minutes on a workstation** and may take substantially longer on conference Wi-Fi. The participant shortcut now fetches only the roughly 270 MB Breast pair, but participants should still complete setup at least 24 hours before the session, open all three notebooks, and run the asset check.

The participant path uses a lightweight Python 3.10 environment, official DGAT `.h5ad` data, and the repository-provided table of precomputed **official DGAT** predictions. It does not train or run DGAT during the live session.

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only
jupyter lab
```

The repository includes verified Breast predictions at `data/raw/dgat_predictions.csv` and a provenance sidecar recording the DGAT commit and checkpoint hashes. Notebook 2 stops with a clear message if either participant input is absent; it never silently substitutes a fitted ridge model.

If Conda reports that `eccb-dgat-tutorial` already exists, update the existing environment instead of recreating it:

```bash
conda env update -n eccb-dgat-tutorial -f environment.yml --prune
conda activate eccb-dgat-tutorial
```

Open the notebooks in order:

1. `notebooks/01_environment_and_spatial_exploration.ipynb`
2. `notebooks/02_dgat_protein_inference_workflow.ipynb`
3. `notebooks/03_evaluation_and_interpretation.ipynb`

The default environment includes the packages needed for the tutorial notebooks. It intentionally excludes PyTorch and PyTorch Geometric; official DGAT inference uses the separate Python 3.11 environment described below.

## System Requirements and Planning Runtimes

### Participant path (recommended)

- 64-bit macOS, Linux, or Windows with WSL2; Conda or Mamba; a current browser.
- 4 CPU cores and 16 GB RAM recommended (8 GB is the practical minimum).
- 10 GB free disk space recommended for environments, downloaded data, and outputs.
- No GPU is required because the live path loads precomputed DGAT predictions.

The observed values below come from the 20 July 2026 clean-room run on an Apple-silicon Mac. Allow additional time on older systems and for first-time package/data downloads.

| Step | Observed / planning time | Observed peak memory | Notes |
| --- | ---: | ---: | --- |
| Create tutorial environment | Plan 5–15 min | — | Mostly package download/solve time |
| Download Breast DGAT data (~270 MB) | Network-dependent | — | Run before the conference; interrupted transfers resume |
| Notebook 1 | 14–39 sec | 2.0 GB | Data loading and spatial exploration |
| Notebook 2, precomputed predictions | 7–9 sec | 1.0 GB | Alignment and plotting; no model fitting |
| Notebook 3 | 8–12 sec | 0.9 GB | Evaluation and spatial metrics |

Notebook 2 no longer writes full transcript and protein matrices to CSV; those redundant writes were a major avoidable source of memory pressure and disk activity.

### Official DGAT inference (optional, advanced)

- Use the separate `eccb-dgat-official` environment with Python 3.11.
- 16 GB RAM is the minimum recommendation; 32 GB and an NVIDIA GPU are preferred for larger datasets.
- CPU execution is supported upstream but can be substantially slower. Runtime depends on tissue size, graph construction, storage, and accelerator; benchmark the exact dataset before relying on it.
- Run official inference before the tutorial or on pre-arranged workstation/HPC infrastructure. Do not make the live session depend on installing or running the model.

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
├── environment-dgat-cpu.yml
├── environment.yml
├── requirements.txt
└── tutorial_checklist.md
```

## Download DGAT Data and Model Weights

The DGAT tutorial data and pretrained model weights are provided in separate Google Drive folders:

- Data: https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C
- Model weights: https://drive.google.com/drive/folders/1uRYhgVgUpkhpE9VTtUB5YmU_hRsf69oD

Download only the data needed by participants:

```bash
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
```

The participant shortcut downloads only the Breast RNA/ADT pair used by the notebooks. Organizers preparing other datasets or official predictions can download the full data folder and checkpoints by omitting `--data-only` and `--dataset`. The downloader resumes interrupted transfers, skips complete existing assets, supports `--force`, reports elapsed time, and offers a no-download check:

```bash
bash scripts/download_dgat_assets.sh
bash scripts/download_dgat_assets.sh --check-only
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

The committed Breast prediction table is loaded from `data/raw/dgat_predictions.csv`. Organizers can regenerate it into `data/processed/predicted_proteins.csv` with the optional official workflow below.

Large raw datasets, checkpoints, and generated files are intentionally ignored by Git. The GitHub repository documents the official download rather than committing DGAT assets directly.

## Command-Line Tutorial Path

If you cannot run Jupyter on a remote server or HPC login node, run the same tutorial material as Python scripts:

```bash
bash scripts/download_dgat_assets.sh

PYTHONPATH=src python scripts/session01_spatial_exploration.py
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py
PYTHONPATH=src python scripts/session03_evaluation_interpretation.py
```

If you want to test the code before the DGAT assets finish downloading, use synthetic data and explicitly request the out-of-fold ridge baseline:

```bash
PYTHONPATH=src python scripts/session01_spatial_exploration.py --allow-demo
PYTHONPATH=src python scripts/session02_dgat_inference_workflow.py --allow-demo --demo-baseline
PYTHONPATH=src python scripts/session03_evaluation_interpretation.py --allow-demo --demo-baseline
```

The baseline is not DGAT. It produces out-of-fold predictions so Notebook 3 does not evaluate rows used to fit their own predictions.

Script outputs are written to:

- `results/session01_dataset_summary.csv`
- `results/session01_top_transcripts.csv`
- `results/session01_top_proteins.csv`
- `results/session01_spatial_neighbors.csv`
- `data/processed/predicted_proteins.csv`
- `results/session03_prediction_correlations.csv`
- `results/session03_morans_i.csv`
- `results/figures/*.png`

## Optional: Official DGAT Prediction in a Separate Environment

The default tutorial environment is designed for smooth notebook execution and data exploration. It does not install the full official DGAT dependency stack.

The official DGAT repository currently targets Python 3.11 and pins SciPy 1.16.0. Do not install its requirements into the Python 3.10 tutorial environment. Create the dedicated environment instead:

```bash
conda env create -f environment-dgat-cpu.yml
conda activate eccb-dgat-official
```

First clone the official DGAT repository into `external/`:

```bash
mkdir -p external
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT
```

Download both data and model weights, then run the preflight check:

```bash
bash scripts/download_dgat_assets.sh
PYTHONPATH=src python scripts/check_dgat_environment.py
```

The supplied environment is CPU-oriented. For CUDA, create a separate Python 3.11 environment, install the PyTorch build matching the cluster's driver/toolkit, and then install the remaining packages from the upstream `requirements_torch_ready.txt`. Check the machine first:

```bash
nvcc -V
nvidia-smi
```

CUDA availability differs across laptops, clusters, and partitions. Install a PyTorch build that matches the CUDA version you will actually use. Use the official PyTorch selector as the source of truth:

https://pytorch.org/get-started/locally/

CUDA example (replace this command with the current selector output for your machine):

```bash
# Example only; choose the correct CUDA build for your machine.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r external/DGAT/requirements_torch_ready.txt
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

Prepare the two participant files without discarding provenance:

```bash
cp data/processed/predicted_proteins.csv data/raw/dgat_predictions.csv
cp data/processed/predicted_proteins.metadata.json data/raw/dgat_predictions.metadata.json
```

The wrapper calls DGAT's own `Model.Train_and_Predict.protein_predict(...)`. It uses the downloaded RNA `.h5ad` file, resolves compatible feature lists, requires both expected weight files, adapts the flat Google Drive checkpoint layout to DGAT's nested directory convention without duplicating files when hard links are supported, handles DGAT's AnnData return value, and writes the prediction table plus a provenance sidecar.

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

## Explicit Baseline Demo

The repository includes a lightweight script demo using synthetic spatial-CITE-seq-like data and an out-of-fold ridge baseline. This is not DGAT and is only for verifying the environment and output format.

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
- Regenerate and verify `data/raw/dgat_predictions.csv` only when the selected data, upstream DGAT commit, or checkpoints change.
- Confirm the official DGAT checkpoint and data download works on a clean machine.
- Confirm the notebooks can read the downloaded DGAT `.h5ad` file directly.
- Replace the planning runtime ranges with measurements from the final assets and reference machine.
- Render or execute all notebooks once before upload.
