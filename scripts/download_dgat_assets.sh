#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DGAT_DIR="${ROOT_DIR}/external/DGAT"
DRIVE_URL="https://drive.google.com/drive/folders/1zmNNTUnF1zquu5zN-kRXu5qad6S8baF7"

mkdir -p "${ASSET_DIR}" "${DGAT_DIR}"

if ! command -v gdown >/dev/null 2>&1; then
  echo "gdown is required. Install it with: python -m pip install gdown"
  exit 1
fi

echo "Downloading official DGAT data/model assets..."
gdown --folder "${DRIVE_URL}" -O "${ASSET_DIR}" --remaining-ok

echo
echo "Downloaded assets to: ${ASSET_DIR}"
echo "For official DGAT pretrained prediction, copy or symlink these folders beside the DGAT README:"
echo "  - DGAT_prediction_ST_data"
echo "  - DGAT_pretrained_models"
echo
echo "Expected DGAT repository location: ${DGAT_DIR}"
