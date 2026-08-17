#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${DGAT_ASSET_DIR:-${ROOT_DIR}/external/DGAT_assets}"
DATA_DIR="${ASSET_DIR}/data"
MODEL_DIR="${ASSET_DIR}/DGAT_pretrained_models/11535_gene_31_protein"
SAMPLE="V1_Human_Lymph_Node"
TENX_BASE="https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/${SAMPLE}"
MATRIX_FILE="${SAMPLE}_filtered_feature_bc_matrix.h5"
SPATIAL_ARCHIVE="${SAMPLE}_spatial.tar.gz"
MATRIX_OUT="${DATA_DIR}/${MATRIX_FILE}"
SPATIAL_DIR="${DATA_DIR}/spatial"
GC_OUT="${DATA_DIR}/${SAMPLE}_manual_GC_annot.csv"
GC_SOURCE="${ROOT_DIR}/data/raw/${SAMPLE}_manual_GC_annot.csv"
PREDICTION_FILE="${SAMPLE}_DGAT_predicted_proteins.csv"
PREDICTION_METADATA_FILE="${SAMPLE}_DGAT_predicted_proteins.metadata.json"
PREDICTION_OUT="${DATA_DIR}/${PREDICTION_FILE}"
PREDICTION_METADATA_OUT="${DATA_DIR}/${PREDICTION_METADATA_FILE}"
PREDICTION_SOURCE="${ROOT_DIR}/data/raw/${PREDICTION_FILE}"
PREDICTION_METADATA_SOURCE="${ROOT_DIR}/data/raw/${PREDICTION_METADATA_FILE}"
PRECOMPUTED_DIR="${DGAT_PRECOMPUTED_DIR:-}"
ENCODER_ID="1RPU7Ss-NtNp_q3u4R5zJGb3o2BdPXeFM"
DECODER_ID="10ZMcZFUf9421-LoWfPhZYWnA_kjfudRY"

FORCE=0
CHECK_ONLY=0
INCLUDE_MODEL=0
usage() { echo "Usage: bash scripts/download_dgat_assets.sh [--force] [--check-only] [--include-model] [--dataset ${SAMPLE}]"; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    --data-only) ;;
    --include-model) INCLUDE_MODEL=1 ;;
    --dataset)
      shift
      [ "${1:-}" = "${SAMPLE}" ] || { echo "This tutorial uses ${SAMPLE}."; exit 2; }
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
  shift
done

mkdir -p "${DATA_DIR}" "${MODEL_DIR}"

download_url() {
  local label="$1" url="$2" destination="$3"
  if [ "${FORCE}" -eq 0 ] && [ -s "${destination}" ]; then echo "${label} already present; skipping."; return; fi
  echo "Downloading ${label} ..."
  curl --fail --location --retry 4 --retry-all-errors --continue-at - \
    --user-agent "Mozilla/5.0 (compatible; ECCB-2026-DGAT-tutorial)" \
    --output "${destination}.part" "${url}"
  mv "${destination}.part" "${destination}"
}

download_drive() {
  local label="$1" file_id="$2" destination="$3"
  if [ "${FORCE}" -eq 0 ] && [ -s "${destination}" ]; then echo "${label} already present; skipping."; return; fi
  echo "Downloading ${label} ..."
  gdown "https://drive.google.com/uc?id=${file_id}" -O "${destination}"
  [ -s "${destination}" ] || { echo "ERROR: ${label} download is empty."; exit 1; }
}

has_data() {
  [ -s "${MATRIX_OUT}" ] && [ -s "${SPATIAL_DIR}/tissue_positions_list.csv" ] && \
  [ -s "${SPATIAL_DIR}/tissue_hires_image.png" ] && [ -s "${GC_OUT}" ] && \
  [ -s "${PREDICTION_OUT}" ] && [ -s "${PREDICTION_METADATA_OUT}" ]
}

has_model() {
  [ -s "${MODEL_DIR}/encoder_mRNA.pth" ] && [ -s "${MODEL_DIR}/decoder_protein.pth" ]
}

copy_precomputed() {
  local source_dir=""
  if [ -s "${PREDICTION_SOURCE}" ] && [ -s "${PREDICTION_METADATA_SOURCE}" ]; then
    source_dir="${ROOT_DIR}/data/raw"
  elif [ -n "${PRECOMPUTED_DIR}" ] && [ -s "${PRECOMPUTED_DIR}/${PREDICTION_FILE}" ] && \
       [ -s "${PRECOMPUTED_DIR}/${PREDICTION_METADATA_FILE}" ]; then
    source_dir="${PRECOMPUTED_DIR}"
  else
    echo "ERROR: validated lymph-node predictions were not found."
    echo "Run the organizer prediction notebook, then either copy its CSV and metadata into"
    echo "${ROOT_DIR}/data/raw or set DGAT_PRECOMPUTED_DIR to its output directory."
    exit 1
  fi
  cp "${source_dir}/${PREDICTION_FILE}" "${PREDICTION_OUT}"
  cp "${source_dir}/${PREDICTION_METADATA_FILE}" "${PREDICTION_METADATA_OUT}"
}

if [ "${CHECK_ONLY}" -eq 0 ]; then
  command -v curl >/dev/null || { echo "curl is required."; exit 1; }
  [ -s "${GC_SOURCE}" ] || { echo "Missing tracked GC annotation: ${GC_SOURCE}"; exit 1; }
  download_url "lymph-node filtered count matrix" "${TENX_BASE}/${MATRIX_FILE}" "${MATRIX_OUT}"
  download_url "lymph-node spatial/H&E archive" "${TENX_BASE}/${SPATIAL_ARCHIVE}" "${DATA_DIR}/${SPATIAL_ARCHIVE}"
  tar -xzf "${DATA_DIR}/${SPATIAL_ARCHIVE}" -C "${DATA_DIR}"
  cp "${GC_SOURCE}" "${GC_OUT}"
  copy_precomputed
  if [ "${INCLUDE_MODEL}" -eq 1 ]; then
    command -v gdown >/dev/null || { echo "gdown is required. Install it with: python -m pip install gdown"; exit 1; }
    download_drive "DGAT RNA encoder" "${ENCODER_ID}" "${MODEL_DIR}/encoder_mRNA.pth"
    download_drive "DGAT protein decoder" "${DECODER_ID}" "${MODEL_DIR}/decoder_protein.pth"
  fi
fi

echo "Checking ${SAMPLE} assets under ${ASSET_DIR} ..."
if has_data; then
  shasum -a 256 "${MATRIX_OUT}" "${DATA_DIR}/${SPATIAL_ARCHIVE}" "${GC_OUT}" \
    "${PREDICTION_OUT}" "${PREDICTION_METADATA_OUT}"
  echo "Lymph-node counts, spatial image, GC labels, and precomputed predictions are present."
else
  echo "ERROR: ${SAMPLE} assets are incomplete. Rerun Session 0 to resume."
  exit 1
fi
if [ "${INCLUDE_MODEL}" -eq 1 ]; then
  has_model || { echo "ERROR: optional inference weights are incomplete."; exit 1; }
  shasum -a 256 "${MODEL_DIR}/encoder_mRNA.pth" "${MODEL_DIR}/decoder_protein.pth"
fi
