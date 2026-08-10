from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_prediction_table(path: str | Path) -> pd.DataFrame:
    """Load the distributed DGAT prediction table."""

    path = Path(path)
    separator = "\t" if path.suffix == ".tsv" else ","
    return pd.read_csv(path, sep=separator, index_col=0)


def write_prediction_artifact(
    predictions: pd.DataFrame,
    path: str | Path,
    *,
    method: str,
    source: str,
    evaluation_note: str,
    extra_metadata: dict[str, object] | None = None,
) -> Path:
    """Write predictions and the provenance sidecar used by Notebook 3."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(path)
    metadata_path = path.with_suffix(".metadata.json")
    metadata: dict[str, object] = {
        "method": method,
        "source": source,
        "evaluation_note": evaluation_note,
        "rows": len(predictions),
        "proteins": predictions.shape[1],
        "protein_names": [str(name) for name in predictions.columns],
        "hidden_dim": 1024,
        "dropout_rate": 0.3,
        "spatial_knn_k": 6,
        "molecular_knn_k": 10,
        "rna_pca_variance": 0.85,
        "train_loss_weights": [5.0, 1.0, 1.0, 3.0, 1.0],
        "preprocessing": {
            "training_path": "qc_control_cytassist + normalize (MT/prevalence/CLR)",
            "inference_path": "fill_genes + preprocess_ST (min_genes=700; RNA normalize/scale only)",
            "min_genes": 700,
            "max_mt_pct": 35,
            "min_gene_prevalence": 0.025,
            "rna": "normalize_total(1e4) → log1p → scale(max_value=10)",
            "protein": "CLR (training / evaluation observations)",
        },
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata_path


def load_prediction_metadata(path: str | Path) -> dict[str, object] | None:
    """Load the prediction provenance sidecar when it is available."""

    metadata_path = Path(path).with_suffix(".metadata.json")
    if not metadata_path.exists():
        return None
    return json.loads(metadata_path.read_text(encoding="utf-8"))
