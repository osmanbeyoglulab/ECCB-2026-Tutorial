# ECCB DGAT Tutorial: complete setup before the session

Please complete these steps at least 24 hours before the tutorial. The DGAT data download took about 15 minutes on one review workstation and may take substantially longer on conference Wi-Fi.

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
bash scripts/download_dgat_assets.sh --data-only
bash scripts/download_dgat_assets.sh --data-only --check-only
jupyter lab
```

Download the organizer-provided prediction table and provenance sidecar and place them at:

```text
data/raw/dgat_predictions.csv
data/raw/dgat_predictions.metadata.json
```

Open the three notebooks and confirm that the kernel named **ECCB DGAT Tutorial** is available. Notebook 2 should report that it loaded precomputed DGAT predictions.

## Expected timing

- Environment creation: 5–15 minutes
- Data download: about 15 minutes on the review workstation; allow 30–60+ minutes on conference Wi-Fi
- Notebook 1: 3–8 minutes
- Notebook 2 with precomputed predictions: 1–3 minutes
- Notebook 3: 2–5 minutes

If setup fails, send the organizers your operating system, available RAM, the command that failed, and the complete error message before the tutorial.
