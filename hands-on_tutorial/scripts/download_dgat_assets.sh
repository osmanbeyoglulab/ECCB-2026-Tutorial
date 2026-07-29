#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/external/DGAT_assets"
DATA_DIR="${ASSET_DIR}/data"
MODEL_DIR="${ASSET_DIR}/model_weights"
DATA_DRIVE_URL="https://drive.google.com/drive/folders/1OhsfCrHFMMjI8kNCKZRWShMHVhgCJo8C"
MODEL_DRIVE_URL="https://drive.google.com/drive/folders/1uRYhgVgUpkhpE9VTtUB5YmU_hRsf69oD"
BREAST_ADT_ID="1AP3rMXqVSkFM5-mFCdHtiVHwOJ_6CmCp"
BREAST_RNA_ID="1NQ2YI2SlMerhro1QlyWb0JjiqxQ9Li3I"

EXPECTED_DATA_FILES=(
  "Breast_ADT.h5ad"
  "Breast_RNA.h5ad"
  "Glioblastoma_ADT.h5ad"
  "Glioblastoma_RNA.h5ad"
  "PBC-PR_6835-5A_ADT.h5ad"
  "PBC-PR_6835-5A_RNA.h5ad"
  "PBC_PR_6837_ADT.h5ad"
  "PBC_PR_6837_RNA.h5ad"
  "Tonsil_AddOns_ADT.h5ad"
  "Tonsil_AddOns_RNA.h5ad"
  "Tonsil_ADT.h5ad"
  "Tonsil_RNA.h5ad"
)

DOWNLOAD_DATA=1
DOWNLOAD_MODELS=1
FORCE=0
CHECK_ONLY=0
DATASET=""

usage() {
  echo "Usage: bash scripts/download_dgat_assets.sh [--data-only|--models-only] [--dataset Breast] [--force] [--check-only]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --data-only) DOWNLOAD_MODELS=0 ;;
    --models-only) DOWNLOAD_DATA=0 ;;
    --force) FORCE=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    --dataset)
      shift
      if [ "$#" -eq 0 ]; then
        echo "--dataset requires a value."
        usage
        exit 2
      fi
      DATASET="$1"
      if [ "${DATASET}" != "Breast" ]; then
        echo "Only --dataset Breast is currently supported by the participant shortcut."
        exit 2
      fi
      ;;
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

  if gdown --help 2>&1 | grep -q -- "--continue"; then
    echo "Resume mode enabled: completed files will be skipped after an interrupted download."
    gdown --folder "${url}" -O "${output_dir}" --continue
  else
    echo "WARNING: installed gdown does not support --continue; interrupted downloads may need a retry."
    gdown --folder "${url}" -O "${output_dir}"
  fi
}

download_file() {
  local label="$1"
  local file_id="$2"
  local destination="$3"

  if [ "${FORCE}" -eq 0 ] && [ -s "${destination}" ]; then
    echo "${label} already present; skipping."
    return
  fi
  echo "Downloading ${label} to ${destination}"
  if gdown --help 2>&1 | grep -q -- "--continue"; then
    gdown "https://drive.google.com/uc?id=${file_id}" -O "${destination}" --continue
  else
    gdown "https://drive.google.com/uc?id=${file_id}" -O "${destination}"
  fi
}

has_data() {
  local filename
  local expected_files=("${EXPECTED_DATA_FILES[@]}")
  if [ "${DATASET}" = "Breast" ]; then
    expected_files=("Breast_ADT.h5ad" "Breast_RNA.h5ad")
  fi
  for filename in "${expected_files[@]}"; do
    if [ ! -s "${DATA_DIR}/${filename}" ]; then
      return 1
    fi
  done
  return 0
}

has_models() {
  while IFS= read -r encoder_path; do
    if [ -f "$(dirname "${encoder_path}")/decoder_protein.pth" ]; then
      return 0
    fi
  done < <(find "${MODEL_DIR}" -name "encoder_mRNA.pth" -print)
  return 1
}

if [ "${DATASET}" = "Breast" ] && [ "${DOWNLOAD_MODELS}" -eq 0 ]; then
  echo "The participant Breast download is about 270 MB."
else
  echo "DGAT assets are a large download (about 15 minutes on a fast workstation in one review)."
fi
echo "Run this before the tutorial; conference Wi-Fi may take substantially longer."
echo "Existing complete asset folders are skipped. Use --force to download them again."

if [ "${CHECK_ONLY}" -eq 0 ]; then
  START_EPOCH="$(date +%s)"
  if [ "${DOWNLOAD_DATA}" -eq 1 ]; then
    if [ "${FORCE}" -eq 0 ] && has_data; then
      echo "Data assets already present; skipping download."
    elif [ "${DATASET}" = "Breast" ]; then
      download_file "Breast ADT data" "${BREAST_ADT_ID}" "${DATA_DIR}/Breast_ADT.h5ad"
      download_file "Breast RNA data" "${BREAST_RNA_ID}" "${DATA_DIR}/Breast_RNA.h5ad"
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
if [ "${DOWNLOAD_DATA}" -eq 1 ]; then
  echo "Checking downloaded DGAT data files..."
  H5AD_FILES="$(find "${DATA_DIR}" -name "*.h5ad" -print)"
  if [ -n "${H5AD_FILES}" ]; then
    echo "${H5AD_FILES}"
  else
    echo "WARNING: no .h5ad files found under ${DATA_DIR}"
  fi
  if has_data; then
    if [ "${DATASET}" = "Breast" ]; then
      echo "Both expected Breast DGAT data files are present."
    else
      echo "All ${#EXPECTED_DATA_FILES[@]} expected DGAT data files are present."
    fi
  else
    echo "WARNING: the DGAT data folder is incomplete. Re-run this command to resume the download."
  fi
fi

if [ "${DOWNLOAD_MODELS}" -eq 1 ]; then
  echo
  echo "Checking downloaded DGAT pretrained model weights..."
  WEIGHT_FILES="$(find "${MODEL_DIR}" \( -name "encoder_mRNA.pth" -o -name "decoder_protein.pth" \) -print)"
  if [ -n "${WEIGHT_FILES}" ]; then
    echo "${WEIGHT_FILES}"
    echo
    echo "Model weights found. The tutorial scripts can auto-discover their location."
  else
    echo "WARNING: no DGAT model weight files found under ${MODEL_DIR}"
    echo "Expected files include:"
    echo "  - encoder_mRNA.pth"
    echo "  - decoder_protein.pth"
    echo
    echo "This means gdown did not download the model weights folder correctly,"
    echo "or the folder requires browser/manual download because of permissions/quota/shortcut handling."
    echo "Open the model-weights Drive folder manually and download it into ${MODEL_DIR}:"
    echo "  ${MODEL_DRIVE_URL}"
  fi
fi

if [ "${DOWNLOAD_DATA}" -eq 1 ] && ! has_data; then
  exit 1
fi
if [ "${DOWNLOAD_MODELS}" -eq 1 ] && ! has_models; then
  exit 1
fi
