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

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "No Python interpreter found. Activate the tutorial environment first."
  exit 1
fi

"${PYTHON_BIN}" <<'PY'
from pathlib import Path
import nbformat
from nbclient import NotebookClient

notebooks = [
    "notebooks/session_01/session_01_data_and_spatial.ipynb",
    "notebooks/session_02/session_02_model_and_predictions.ipynb",
    "notebooks/session_03/session_03_evaluation_and_interpretation.ipynb",
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
