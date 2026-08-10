#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${DGAT_ASSET_DIR:-${ROOT_DIR}/external/DGAT_assets}"
DATA_DIR="${ASSET_DIR}/data"
TONSIL_ADT_ID="1uBKoU_tH3kPjjJaf--D-u4B5ljVpOlwR"
TONSIL_RNA_ID="1tDYHTVdKfBYXIu6eznvsU16Qd4CnfWuW"

FORCE=0
CHECK_ONLY=0

usage() {
  echo "Usage: bash scripts/download_dgat_assets.sh [--force] [--check-only]"
}

# Keep accepting the original participant command while limiting this public
# script to the Tonsil data used by the tutorial.
while [ "$#" -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    --data-only) ;;
    --dataset)
      shift
      if [ "${1:-}" != "Tonsil" ]; then
        echo "This participant tutorial supports only the Tonsil dataset."
        exit 2
      fi
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
  shift
done

mkdir -p "${DATA_DIR}"

has_data() {
  [ -s "${DATA_DIR}/Tonsil_RNA.h5ad" ] && [ -s "${DATA_DIR}/Tonsil_ADT.h5ad" ]
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

  if [ ! -s "${destination}" ]; then
    echo "ERROR: failed to download ${label} (empty or missing: ${destination})."
    exit 1
  fi
}

if [ "${CHECK_ONLY}" -eq 0 ]; then
  if ! command -v gdown >/dev/null 2>&1; then
    echo "gdown is required. Install it with: python -m pip install gdown"
    exit 1
  fi

  echo "The participant Tonsil download is about 350 MB."
  echo "Existing complete files are skipped; interrupted downloads resume when supported."
  download_file "Tonsil ADT data" "${TONSIL_ADT_ID}" "${DATA_DIR}/Tonsil_ADT.h5ad"
  download_file "Tonsil RNA data" "${TONSIL_RNA_ID}" "${DATA_DIR}/Tonsil_RNA.h5ad"
fi

echo
echo "Checking Tonsil data files under ${DATA_DIR} ..."
if has_data; then
  ls -lh "${DATA_DIR}/Tonsil_RNA.h5ad" "${DATA_DIR}/Tonsil_ADT.h5ad"
  echo "Both expected Tonsil files are present."
else
  echo "ERROR: the Tonsil data folder is incomplete. Rerun Notebook 0 to resume."
  exit 1
fi
