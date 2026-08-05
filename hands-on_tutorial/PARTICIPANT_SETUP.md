# Session 0: live environment and data setup

Complete this worksheet **during the tutorial with the instructor**. Environment creation, data download,
validation, and the first notebook are teaching activities—not prerequisites.

## What participants need when they arrive

- A laptop with 4 CPU cores, 16 GB RAM recommended, and 10 GB free disk space
- macOS, Linux, or Windows with WSL2
- Conda or Mamba installed
- Git and a current web browser
- Network access for cloning the repository, creating the environment, and downloading about 270 MB

No GPU and no pre-created Python environment are required.

## Step 1 — Clone the tutorial repository

The instructor first explains the repository layout and then everyone runs:

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial/hands-on_tutorial
```

Checkpoint: `pwd` should end in `hands-on_tutorial` and `ls` should show `environment.yml`, `notebooks/`,
`scripts/`, and `src/`.

## Step 2 — Create the participant environment

The instructor explains why the lightweight participant environment is separate from the optional full DGAT
training environment.

```bash
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
python --version
```

Checkpoint: Python should be 3.10 and the shell prompt should show `eccb-dgat-tutorial`.

If the environment already exists, update it during the same session:

```bash
conda env update -n eccb-dgat-tutorial -f environment.yml --prune
conda activate eccb-dgat-tutorial
```

## Step 3 — Download and verify the Breast dataset

The data download is part of the data-provenance lesson. The instructor explains which files are measurements,
which predictions are committed, and why observed proteins must not be used as model inputs during evaluation.

```bash
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only
```

The repository already contains the verified prediction artifact and its metadata sidecar:

```text
data/raw/dgat_predictions.csv
data/raw/dgat_predictions.metadata.json
```

Checkpoint: the asset check passes and both prediction files exist. Do not replace them with locally fitted
baseline outputs.

## Step 4 — Launch Jupyter and select the tutorial kernel

```bash
jupyter lab
```

Open `notebooks/session_01/01_load_and_validate.ipynb` and select **ECCB DGAT Tutorial**. Run the notebook with
the instructor. It should report the paired Breast data source, spatial coordinates, and passing validation checks.

## Step 5 — Confirm the inference artifact

Open `notebooks/session_02/04_load_predictions.ipynb`. It should print the DGAT method and evaluation caveat,
then write a processed prediction table with its provenance sidecar.

## Live-session timing budget

- Repository clone and orientation: 3–5 minutes
- Environment creation: 5–15 minutes
- Breast data download and asset verification: 3–10 minutes, depending on the tutorial network
- Jupyter launch, kernel selection, and first validation notebook: 5 minutes

The instructor should have a local mirror of the repository, Conda packages, and Breast data available if the
venue network is unreliable. That contingency is organizer infrastructure; participants still perform and learn
the setup workflow during the session.

## Troubleshooting during the session

If a command fails, stop at that checkpoint and share the operating system, command, and complete error with an
instructor. Do not silently switch environments or substitute another dataset for the official Breast workflow.
