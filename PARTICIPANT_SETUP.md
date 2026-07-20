# ECCB DGAT Tutorial: complete setup before the session

Please complete these steps at least 24 hours before the tutorial. The participant command downloads only the roughly 270 MB Breast dataset, but unstable conference Wi-Fi can still interrupt large-file transfers.

## Recommended computer

- 4 CPU cores, 16 GB RAM, and 10 GB free disk space
- macOS, Linux, or Windows with WSL2
- Conda or Mamba and a current web browser
- No GPU is required for the participant workflow

## Setup

```bash
git clone https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial.git
cd ECCB-2026-Tutorial
conda env create -f environment.yml
conda activate eccb-dgat-tutorial
bash scripts/download_dgat_assets.sh --data-only --dataset Breast
bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only
jupyter lab
```

The repository clone already contains both verified Breast prediction files. Confirm that they are present:

```text
data/raw/dgat_predictions.csv
data/raw/dgat_predictions.metadata.json
```

Do not replace them with locally fitted baseline outputs.

Open the three notebooks and confirm that the kernel named **ECCB DGAT Tutorial** is available. Notebook 2 should report that it loaded precomputed DGAT predictions.

## Expected timing

- Environment creation: 5–15 minutes
- Breast data download: about 270 MB; complete it before traveling and re-run the same command if the connection is interrupted
- Notebook 1: 14–39 seconds observed; allow up to a few minutes on older laptops
- Notebook 2 with precomputed predictions: 7–9 seconds observed
- Notebook 3: 8–12 seconds observed

Peak memory observed during the clean-room run was approximately 2.0 GB. The 8 GB minimum leaves room for Jupyter, the browser, Conda, and operating-system overhead; 16 GB remains recommended.

If setup fails, send the organizers your operating system, available RAM, the command that failed, and the complete error message before the tutorial.
