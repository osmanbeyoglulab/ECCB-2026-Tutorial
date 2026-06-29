#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DGAT_DIR="${ROOT_DIR}/external/DGAT"
DRIVE_URL="https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C"

mkdir -p "${ASSET_DIR}" "${DGAT_DIR}"

if ! command -v gdown >/dev/null 2>&1; then
  echo "gdown is required. Install it with: python -m pip install gdown"
  exit 1
fi

echo "Downloading official DGAT data/model assets from:"
echo "${DRIVE_URL}"
if gdown --help 2>&1 | grep -q -- "--remaining-ok"; then
  gdown --folder "${DRIVE_URL}" -O "${ASSET_DIR}" --remaining-ok
else
  echo "Installed gdown does not support --remaining-ok; using compatible download mode."
  gdown --folder "${DRIVE_URL}" -O "${ASSET_DIR}"
fi

echo
echo "Downloaded assets to: ${ASSET_DIR}"
echo "For official DGAT pretrained prediction, copy or symlink these folders beside the DGAT README:"
echo "  - DGAT_prediction_ST_data"
echo "  - DGAT_pretrained_models"
echo
echo "Expected DGAT repository location: ${DGAT_DIR}"
