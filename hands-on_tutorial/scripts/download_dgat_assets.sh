#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${DGAT_ASSET_DIR:-${ROOT_DIR}/external/DGAT_assets}"
DATA_DIR="${ASSET_DIR}/data"
MODEL_DIR="${ASSET_DIR}/DGAT_pretrained_models/11535_gene_31_protein"

TONSIL_ADT_ID="1uBKoU_tH3kPjjJaf--D-u4B5ljVpOlwR"
TONSIL_RNA_ID="1tDYHTVdKfBYXIu6eznvsU16Qd4CnfWuW"
LN_SAMPLE="V1_Human_Lymph_Node"
LN_BASE="https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/${LN_SAMPLE}"
LN_MATRIX="${LN_SAMPLE}_filtered_feature_bc_matrix.h5"
LN_SPATIAL_ARCHIVE="${LN_SAMPLE}_spatial.tar.gz"
LN_GC="${LN_SAMPLE}_manual_GC_annot.csv"
LN_PREDICTION="${LN_SAMPLE}_DGAT_predicted_proteins.csv"
LN_METADATA="${LN_SAMPLE}_DGAT_predicted_proteins.metadata.json"
ENCODER_ID="1RPU7Ss-NtNp_q3u4R5zJGb3o2BdPXeFM"
DECODER_ID="10ZMcZFUf9421-LoWfPhZYWnA_kjfudRY"

DATASET="all"
FORCE=0
CHECK_ONLY=0
INCLUDE_MODEL=0

usage() {
  echo "Usage: bash scripts/download_dgat_assets.sh [--dataset all|Tonsil|V1_Human_Lymph_Node] [--force] [--check-only] [--include-model]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dataset) shift; DATASET="${1:-}" ;;
    --force) FORCE=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    --include-model) INCLUDE_MODEL=1 ;;
    --data-only) ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
  shift
done

case "${DATASET}" in
  all|Tonsil|V1_Human_Lymph_Node) ;;
  *) echo "Unsupported dataset: ${DATASET}"; usage; exit 2 ;;
esac

mkdir -p "${DATA_DIR}" "${MODEL_DIR}"

download_drive() {
  local label="$1" file_id="$2" destination="$3"
  if [ "${FORCE}" -eq 0 ] && [ -s "${destination}" ]; then
    echo "${label} already present; skipping."
    return
  fi
  command -v gdown >/dev/null || {
    echo "gdown is required. Install it with: python -m pip install gdown"
    exit 1
  }
  echo "Downloading ${label} ..."
  gdown "https://drive.google.com/uc?id=${file_id}" -O "${destination}"
  [ -s "${destination}" ] || { echo "ERROR: ${label} download is empty."; exit 1; }
}

download_url() {
  local label="$1" url="$2" destination="$3"
  if [ "${FORCE}" -eq 0 ] && [ -s "${destination}" ]; then
    echo "${label} already present; skipping."
    return
  fi
  command -v curl >/dev/null || { echo "curl is required."; exit 1; }
  echo "Downloading ${label} ..."
  curl --fail --location --retry 4 --retry-all-errors --continue-at - \
    --user-agent "Mozilla/5.0 (compatible; ECCB-2026-DGAT-tutorial)" \
    --output "${destination}.part" "${url}"
  mv "${destination}.part" "${destination}"
}

copy_tracked() {
  local label="$1" filename="$2"
  local source="${ROOT_DIR}/data/raw/${filename}"
  local alternate="${DGAT_PRECOMPUTED_DIR:-}/${filename}"
  if [ -s "${source}" ]; then
    cp "${source}" "${DATA_DIR}/${filename}"
  elif [ -n "${DGAT_PRECOMPUTED_DIR:-}" ] && [ -s "${alternate}" ]; then
    cp "${alternate}" "${DATA_DIR}/${filename}"
  else
    echo "ERROR: ${label} is missing from data/raw and DGAT_PRECOMPUTED_DIR."
    exit 1
  fi
}

download_tonsil() {
  download_drive "Tonsil RNA" "${TONSIL_RNA_ID}" "${DATA_DIR}/Tonsil_RNA.h5ad"
  download_drive "Tonsil ADT" "${TONSIL_ADT_ID}" "${DATA_DIR}/Tonsil_ADT.h5ad"
}

download_lymph_node() {
  download_url "lymph-node filtered count matrix" "${LN_BASE}/${LN_MATRIX}" "${DATA_DIR}/${LN_MATRIX}"
  download_url "lymph-node spatial/H&E archive" "${LN_BASE}/${LN_SPATIAL_ARCHIVE}" "${DATA_DIR}/${LN_SPATIAL_ARCHIVE}"
  rm -rf "${DATA_DIR}/spatial"
  tar -xzf "${DATA_DIR}/${LN_SPATIAL_ARCHIVE}" -C "${DATA_DIR}"
  copy_tracked "germinal-center annotation" "${LN_GC}"
  copy_tracked "validated lymph-node predictions" "${LN_PREDICTION}"
  copy_tracked "lymph-node prediction metadata" "${LN_METADATA}"
  if [ "${INCLUDE_MODEL}" -eq 1 ]; then
    download_drive "DGAT RNA encoder" "${ENCODER_ID}" "${MODEL_DIR}/encoder_mRNA.pth"
    download_drive "DGAT protein decoder" "${DECODER_ID}" "${MODEL_DIR}/decoder_protein.pth"
  fi
}

check_tonsil() {
  for path in "${DATA_DIR}/Tonsil_RNA.h5ad" "${DATA_DIR}/Tonsil_ADT.h5ad"; do
    [ -s "${path}" ] || { echo "ERROR: missing ${path}"; exit 1; }
  done
  shasum -a 256 "${DATA_DIR}/Tonsil_RNA.h5ad" "${DATA_DIR}/Tonsil_ADT.h5ad"
}

check_lymph_node() {
  local required=(
    "${DATA_DIR}/${LN_MATRIX}"
    "${DATA_DIR}/${LN_SPATIAL_ARCHIVE}"
    "${DATA_DIR}/${LN_GC}"
    "${DATA_DIR}/${LN_PREDICTION}"
    "${DATA_DIR}/${LN_METADATA}"
    "${DATA_DIR}/spatial/tissue_positions_list.csv"
    "${DATA_DIR}/spatial/tissue_hires_image.png"
  )
  for path in "${required[@]}"; do
    [ -s "${path}" ] || { echo "ERROR: missing ${path}"; exit 1; }
  done
  shasum -a 256 "${required[@]}"
  if [ "${INCLUDE_MODEL}" -eq 1 ]; then
    for path in "${MODEL_DIR}/encoder_mRNA.pth" "${MODEL_DIR}/decoder_protein.pth"; do
      [ -s "${path}" ] || { echo "ERROR: missing ${path}"; exit 1; }
    done
    shasum -a 256 "${MODEL_DIR}/encoder_mRNA.pth" "${MODEL_DIR}/decoder_protein.pth"
  fi
}

if [ "${CHECK_ONLY}" -eq 0 ]; then
  case "${DATASET}" in
    all) download_tonsil; download_lymph_node ;;
    Tonsil) download_tonsil ;;
    V1_Human_Lymph_Node) download_lymph_node ;;
  esac
fi

case "${DATASET}" in
  all) check_tonsil; check_lymph_node ;;
  Tonsil) check_tonsil ;;
  V1_Human_Lymph_Node) check_lymph_node ;;
esac

echo "Verified ${DATASET} tutorial assets under ${ASSET_DIR}."
