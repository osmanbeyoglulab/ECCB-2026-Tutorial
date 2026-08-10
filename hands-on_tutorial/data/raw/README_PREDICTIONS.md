# Prediction artifacts

The participant notebooks load `dgat_predictions.csv` (and its `.metadata.json` sidecar).

The tutorial sample is the **10x Genomics CytAssist Tonsil** pair
(`Tonsil_RNA.h5ad` / `Tonsil_ADT.h5ad`). The previous Breast prediction table is archived as:

- `dgat_predictions.breast_archive.csv`
- `dgat_predictions.breast_archive.metadata.json`

## Regenerate Tonsil predictions (organizers)

Requires the official DGAT environment, cloned `external/DGAT`, pretrained weights, and Tonsil RNA.
The wrapper mirrors Demo3: `fill_genes` → `preprocess_ST` → `protein_predict`, using the public
**11,535-gene / 31-protein** common lists that match the released encoder/decoder widths.

```bash
bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil
# plus model weights (omit --data-only, or use --models-only)

conda activate eccb-dgat-official   # or your DGAT CPU/GPU env
git clone --depth 1 https://github.com/osmanbeyoglulab/DGAT.git external/DGAT

PYTHONPATH=src python scripts/run_official_dgat_prediction.py \
  --rna-h5ad external/DGAT_assets/data/Tonsil_RNA.h5ad \
  --model-save-dir external/DGAT_assets/model_weights \
  --output data/raw/dgat_predictions.csv \
  --tonsil-held-out unknown
```

Then update the sidecar fields before workshop release:

- `dataset`, `source`, `evaluation_note`
- checksums (`prediction_sha256`, encoder/decoder hashes)
- `dgat_commit`
- `tonsil_held_out` / `training_samples` (set explicitly; leave `null` only if unknown)
- `ordered_input_gene_list` / gene-count confirmation (`11535` for the public ST checkpoint)

Do not commit predictions produced without `fill_genes` + `preprocess_ST`.
