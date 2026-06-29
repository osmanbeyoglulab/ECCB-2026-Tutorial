#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DRIVE_URL="https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C"

mkdir -p "${ASSET_DIR}"

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
echo
echo "Checking downloaded DGAT data files..."
H5AD_FILES="$(find "${ASSET_DIR}" -name "*.h5ad" -print)"
if [ -n "${H5AD_FILES}" ]; then
  echo "${H5AD_FILES}"
else
  echo "WARNING: no .h5ad files found under ${ASSET_DIR}"
fi

echo
echo "Checking downloaded DGAT pretrained model weights..."
WEIGHT_FILES="$(find "${ASSET_DIR}" \( -name "encoder_mRNA.pth" -o -name "decoder_protein.pth" \) -print)"
if [ -n "${WEIGHT_FILES}" ]; then
  echo "${WEIGHT_FILES}"
  echo
  echo "Model weights found. The tutorial scripts can auto-discover their location."
else
  echo "WARNING: no DGAT model weight files found under ${ASSET_DIR}"
  echo "Expected files include:"
  echo "  - encoder_mRNA.pth"
  echo "  - decoder_protein.pth"
  echo
  echo "This means the Google Drive folder downloaded by gdown did not include the pretrained model weights,"
  echo "or gdown skipped them because of permissions/quota/shortcut handling."
  echo "Open the Drive folder manually and check whether a pretrained model folder is present:"
  echo "  ${DRIVE_URL}"
fi
