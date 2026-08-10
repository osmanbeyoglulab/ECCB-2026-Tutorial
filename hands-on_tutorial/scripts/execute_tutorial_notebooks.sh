#!/usr/bin/env bash
# Execute Session 1–3 notebooks in order, keeping inline outputs for GitHub/Colab review.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -d src/dgat_tutorial ]]; then
  echo "Run this script from a complete hands-on_tutorial checkout."
  exit 1
fi

export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
mkdir -p results/figures data/processed checkpoints/session_01 checkpoints/session_02 checkpoints/session_03

python <<'PY'
from pathlib import Path
import nbformat
from nbclient import NotebookClient

notebooks = [
    "notebooks/session_01/01_data_preparation.ipynb",
    "notebooks/session_01/02_spatial_context.ipynb",
    "notebooks/session_02/01_dgat_model.ipynb",
    "notebooks/session_02/02_predictions.ipynb",
    "notebooks/session_03/01_quantitative_evaluation.ipynb",
    "notebooks/session_03/02_interpretation.ipynb",
]

root = Path.cwd()
for rel in notebooks:
    path = root / rel
    print(f"\n=== Executing {rel} ===", flush=True)
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=1800,
        kernel_name="python3",
        resources={"metadata": {"path": str(root)}},
    )
    client.execute()
    nbformat.write(nb, path)
    print(f"Saved outputs: {rel}", flush=True)

print("\nAll Session 1–3 notebooks executed with outputs saved inplace.")
PY
