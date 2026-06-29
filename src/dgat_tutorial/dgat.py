from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def run_demo_dgat_inference(
    transcripts: pd.DataFrame,
    reference_proteins: pd.DataFrame,
    random_state: int = 7,
) -> pd.DataFrame:
    """Return DGAT-like protein predictions for tutorial dry runs.

    This lightweight baseline keeps the notebooks executable without the official
    DGAT environment. For the live tutorial, use the official DGAT repository:
    https://github.com/osmanbeyoglulab/DGAT
    """

    rng = np.random.default_rng(random_state)
    x = np.log1p(transcripts.to_numpy(dtype=float))
    y = reference_proteins.to_numpy(dtype=float)

    x_mean = x.mean(axis=0, keepdims=True)
    x_std = x.std(axis=0, keepdims=True) + 1e-8
    y_mean = y.mean(axis=0, keepdims=True)
    y_std = y.std(axis=0, keepdims=True) + 1e-8
    x_scaled = (x - x_mean) / x_std
    y_scaled = (y - y_mean) / y_std

    x_design = np.column_stack([np.ones(x_scaled.shape[0]), x_scaled])
    ridge = 0.25 * np.eye(x_design.shape[1])
    ridge[0, 0] = 0
    coefficients = np.linalg.solve(x_design.T @ x_design + ridge, x_design.T @ y_scaled)
    predicted = x_design @ coefficients
    predicted = predicted * y_std + y_mean
    predicted += rng.normal(scale=0.03, size=predicted.shape)

    return pd.DataFrame(predicted, index=transcripts.index, columns=reference_proteins.columns)


def load_prediction_table(path: str) -> pd.DataFrame:
    """Load precomputed DGAT predictions from CSV or TSV."""

    sep = "\t" if path.endswith(".tsv") else ","
    return pd.read_csv(path, sep=sep, index_col=0)


def run_official_dgat_prediction(
    rna_h5ad_path: str | Path,
    dgat_repo_dir: str | Path = "external/DGAT",
    model_save_dir: str | Path = "external/DGAT_assets/DGAT_pretrained_models",
    pyg_data_dir: str | Path = "data/processed/dgat_pyg",
    common_gene_path: str | Path | None = None,
    common_protein_path: str | Path | None = None,
) -> pd.DataFrame:
    """Run the official DGAT pretrained spatial protein prediction workflow.

    This calls ``Model.Train_and_Predict.protein_predict`` from the official
    DGAT repository. The returned prediction table has spots/cells as rows and
    predicted proteins as columns.
    """

    rna_h5ad_path = Path(rna_h5ad_path)
    dgat_repo_dir = Path(dgat_repo_dir)
    model_save_dir = Path(model_save_dir)
    pyg_data_dir = Path(pyg_data_dir)

    if not dgat_repo_dir.exists():
        raise FileNotFoundError(
            f"Official DGAT repository not found at {dgat_repo_dir}. "
            "Clone it with: git clone https://github.com/osmanbeyoglulab/DGAT.git external/DGAT"
        )
    if not rna_h5ad_path.exists():
        raise FileNotFoundError(f"RNA AnnData file not found: {rna_h5ad_path}")
    if not model_save_dir.exists():
        raise FileNotFoundError(f"DGAT pretrained model directory not found: {model_save_dir}")

    common_gene_path, common_protein_path = resolve_dgat_resource_files(
        dgat_repo_dir=dgat_repo_dir,
        model_save_dir=model_save_dir,
        common_gene_path=common_gene_path,
        common_protein_path=common_protein_path,
    )
    common_gene = read_feature_list(common_gene_path)
    common_protein = read_feature_list(common_protein_path)

    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("Official DGAT prediction requires `anndata` in the active environment.") from exc

    sys.path.insert(0, str(dgat_repo_dir.resolve()))
    try:
        train_and_predict = importlib.import_module("Model.Train_and_Predict")
    except Exception as exc:
        raise ImportError(
            "Could not import `Model.Train_and_Predict` from the official DGAT repository. "
            "Check that DGAT dependencies are installed in this environment."
        ) from exc

    adata = ad.read_h5ad(rna_h5ad_path)
    available_genes = [gene for gene in common_gene if gene in adata.var_names]
    if not available_genes:
        raise ValueError(
            f"None of the genes in {common_gene_path} were found in {rna_h5ad_path}. "
            "Check that the common gene file matches the pretrained model."
        )
    if len(available_genes) != len(common_gene):
        missing = len(common_gene) - len(available_genes)
        raise ValueError(
            f"{missing} genes from {common_gene_path} were absent from {rna_h5ad_path}. "
            "DGAT pretrained checkpoints are keyed by the exact common-gene count, so the RNA file, "
            "common gene list, and model directory must match."
        )
    adata = adata[:, available_genes].copy()

    pyg_data_dir.mkdir(parents=True, exist_ok=True)
    predictions = train_and_predict.protein_predict(
        adata,
        available_genes,
        common_protein,
        str(model_save_dir),
        str(pyg_data_dir),
    )
    predictions = pd.DataFrame(predictions, index=adata.obs_names)
    return predictions


def read_feature_list(path: str | Path) -> list[str]:
    """Read one feature name per line."""

    path = Path(path)
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def resolve_dgat_resource_files(
    dgat_repo_dir: str | Path,
    model_save_dir: str | Path,
    common_gene_path: str | Path | None = None,
    common_protein_path: str | Path | None = None,
) -> tuple[Path, Path]:
    """Resolve common gene/protein lists compatible with DGAT pretrained models."""

    dgat_repo_dir = Path(dgat_repo_dir)
    model_save_dir = Path(model_save_dir)
    if common_gene_path is not None and common_protein_path is not None:
        return Path(common_gene_path), Path(common_protein_path)

    gene_count, protein_count = infer_feature_counts_from_model_dir(model_save_dir)
    search_dirs = [
        dgat_repo_dir / "resources",
        dgat_repo_dir,
        model_save_dir,
        model_save_dir.parent,
    ]

    resolved_gene = Path(common_gene_path) if common_gene_path is not None else None
    resolved_protein = Path(common_protein_path) if common_protein_path is not None else None

    if resolved_gene is None:
        resolved_gene = find_common_feature_file(search_dirs, "common_gene", gene_count)
    if resolved_protein is None:
        resolved_protein = find_common_feature_file(search_dirs, "common_protein", protein_count)

    if resolved_gene is None:
        raise FileNotFoundError("Could not find `common_gene_*.txt`. Pass `--common-gene` explicitly.")
    if resolved_protein is None:
        raise FileNotFoundError("Could not find `common_protein_*.txt`. Pass `--common-protein` explicitly.")
    return resolved_gene, resolved_protein


def infer_feature_counts_from_model_dir(model_save_dir: str | Path) -> tuple[int | None, int | None]:
    """Infer feature counts from directories like `17434_gene_31_protein`."""

    model_save_dir = Path(model_save_dir)
    pattern = re.compile(r"(?P<genes>\d+)_gene_(?P<proteins>\d+)_protein")
    for path in sorted(model_save_dir.glob("*_gene_*_protein")):
        match = pattern.fullmatch(path.name)
        if match:
            return int(match.group("genes")), int(match.group("proteins"))
    return None, None


def find_common_feature_file(search_dirs: list[Path], prefix: str, count: int | None) -> Path | None:
    """Find a common feature list, preferring the count matching the model directory."""

    candidates = []
    for search_dir in search_dirs:
        if search_dir.exists():
            candidates.extend(sorted(search_dir.rglob(f"{prefix}_*.txt")))
    if not candidates:
        return None
    if count is not None:
        for candidate in candidates:
            if candidate.name == f"{prefix}_{count}.txt":
                return candidate
    return sorted(candidates)[-1]
