#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DATA_DIR="${ASSET_DIR}/data"
MODEL_DIR="${ASSET_DIR}/model_weights"
DATA_DRIVE_URL="https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C"
MODEL_DRIVE_URL="https://drive.google.com/drive/folders/1uRYhgVgUpkhpE9VTtUB5YmU_hRsf69oD"

mkdir -p "${DATA_DIR}" "${MODEL_DIR}"

if ! command -v gdown >/dev/null 2>&1; then
  echo "gdown is required. Install it with: python -m pip install gdown"
  exit 1
fi

download_folder() {
  local label="$1"
  local url="$2"
  local output_dir="$3"

  echo
  echo "Downloading ${label} from:"
  echo "${url}"
  echo "Output directory: ${output_dir}"

  if gdown --help 2>&1 | grep -q -- "--remaining-ok"; then
    gdown --folder "${url}" -O "${output_dir}" --remaining-ok
  else
    echo "Installed gdown does not support --remaining-ok; using compatible download mode."
    gdown --folder "${url}" -O "${output_dir}"
  fi
}

download_folder "DGAT data assets" "${DATA_DRIVE_URL}" "${DATA_DIR}"
download_folder "DGAT pretrained model weights" "${MODEL_DRIVE_URL}" "${MODEL_DIR}"

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
  echo "This means gdown did not download the model weights folder correctly,"
  echo "or the folder requires browser/manual download because of permissions/quota/shortcut handling."
  echo "Open the model-weights Drive folder manually and download it into ${MODEL_DIR}:"
  echo "  ${MODEL_DRIVE_URL}"
fi
