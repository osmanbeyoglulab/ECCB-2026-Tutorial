#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DATA_DIR="${ASSET_DIR}/data"
MODEL_DIR="${ASSET_DIR}/model_weights"
DATA_DRIVE_URL="https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C"
MODEL_DRIVE_URL="https://drive.google.com/drive/folders/1uRYhgVgUpkhpE9VTtUB5YmU_hRsf69oD"

DOWNLOAD_DATA=1
DOWNLOAD_MODELS=1
FORCE=0
CHECK_ONLY=0

usage() {
  echo "Usage: bash scripts/download_dgat_assets.sh [--data-only|--models-only] [--force] [--check-only]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --data-only) DOWNLOAD_MODELS=0 ;;
    --models-only) DOWNLOAD_DATA=0 ;;
    --force) FORCE=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
  shift
done

mkdir -p "${DATA_DIR}" "${MODEL_DIR}"

if [ "${CHECK_ONLY}" -eq 0 ] && ! command -v gdown >/dev/null 2>&1; then
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

has_data() {
  find "${DATA_DIR}" -name "*.h5ad" -print -quit | grep -q .
}

has_models() {
  while IFS= read -r encoder_path; do
    if [ -f "$(dirname "${encoder_path}")/decoder_protein.pth" ]; then
      return 0
    fi
  done < <(find "${MODEL_DIR}" -name "encoder_mRNA.pth" -print)
  return 1
}

echo "DGAT assets are a large download (about 15 minutes on a fast workstation in one review)."
echo "Run this before the tutorial; conference Wi-Fi may take substantially longer."
echo "Existing complete asset folders are skipped. Use --force to download them again."

if [ "${CHECK_ONLY}" -eq 0 ]; then
  START_EPOCH="$(date +%s)"
  if [ "${DOWNLOAD_DATA}" -eq 1 ]; then
    if [ "${FORCE}" -eq 0 ] && has_data; then
      echo "Data assets already present; skipping download."
    else
      download_folder "DGAT data assets" "${DATA_DRIVE_URL}" "${DATA_DIR}"
    fi
  fi
  if [ "${DOWNLOAD_MODELS}" -eq 1 ]; then
    if [ "${FORCE}" -eq 0 ] && has_models; then
      echo "Model weights already present; skipping download."
    else
      download_folder "DGAT pretrained model weights" "${MODEL_DRIVE_URL}" "${MODEL_DIR}"
    fi
  fi
  END_EPOCH="$(date +%s)"
  echo "Download/check elapsed time: $((END_EPOCH - START_EPOCH)) seconds"
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
  echo "This means gdown did not download the model weights folder correctly,"
  echo "or the folder requires browser/manual download because of permissions/quota/shortcut handling."
  echo "Open the model-weights Drive folder manually and download it into ${MODEL_DIR}:"
  echo "  ${MODEL_DRIVE_URL}"
fi

if [ "${DOWNLOAD_DATA}" -eq 1 ] && ! has_data; then
  exit 1
fi
if [ "${DOWNLOAD_MODELS}" -eq 1 ] && ! has_models; then
  exit 1
fi
