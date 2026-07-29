from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def run_demo_dgat_inference(
    transcripts: pd.DataFrame,
    reference_proteins: pd.DataFrame,
    random_state: int = 7,
    n_splits: int = 5,
    max_observations: int = 2_000,
) -> pd.DataFrame:
    """Return out-of-fold ridge predictions for tutorial dry runs.

    This is deliberately not called DGAT. Every row is predicted by a model that
    was fitted without that row, avoiding the in-sample leakage present in the
    original tutorial fallback. It remains a baseline for environment checks;
    use official or precomputed DGAT predictions for the tutorial results.
    """

    x = np.log1p(transcripts.to_numpy(dtype=float))
    y = reference_proteins.to_numpy(dtype=float)
    if len(x) < 2:
        raise ValueError("The out-of-fold ridge baseline requires at least two observations.")
    if len(x) > max_observations:
        raise ValueError(
            f"The optional ridge baseline is limited to {max_observations:,} observations to avoid "
            "unexpected memory/CPU load. Use precomputed or official DGAT predictions for the full dataset."
        )

    n_splits = min(n_splits, len(x))
    predicted = np.empty_like(y, dtype=float)
    rng = np.random.default_rng(random_state)
    folds = np.array_split(rng.permutation(len(x)), n_splits)
    all_indices = np.arange(len(x))
    for test_idx in folds:
        train_idx = np.setdiff1d(all_indices, test_idx, assume_unique=True)
        x_train, x_test = x[train_idx], x[test_idx]
        y_train = y[train_idx]
        x_mean = x_train.mean(axis=0, keepdims=True)
        x_std = x_train.std(axis=0, keepdims=True) + 1e-8
        y_mean = y_train.mean(axis=0, keepdims=True)
        y_std = y_train.std(axis=0, keepdims=True) + 1e-8
        x_train_scaled = (x_train - x_mean) / x_std
        x_test_scaled = (x_test - x_mean) / x_std
        y_train_scaled = (y_train - y_mean) / y_std

        alpha = 0.25
        if x_train_scaled.shape[1] <= x_train_scaled.shape[0]:
            gram = x_train_scaled.T @ x_train_scaled
            coefficients = np.linalg.solve(
                gram + alpha * np.eye(gram.shape[0]),
                x_train_scaled.T @ y_train_scaled,
            )
            scaled_prediction = x_test_scaled @ coefficients
        else:
            gram = x_train_scaled @ x_train_scaled.T
            dual = np.linalg.solve(
                gram + alpha * np.eye(gram.shape[0]),
                y_train_scaled,
            )
            scaled_prediction = (x_test_scaled @ x_train_scaled.T) @ dual
        predicted[test_idx] = scaled_prediction * y_std + y_mean

    return pd.DataFrame(predicted, index=transcripts.index, columns=reference_proteins.columns)


def load_prediction_table(path: str) -> pd.DataFrame:
    """Load precomputed DGAT predictions from CSV or TSV."""

    sep = "\t" if path.endswith(".tsv") else ","
    return pd.read_csv(path, sep=sep, index_col=0)


def write_prediction_artifact(
    predictions: pd.DataFrame,
    path: str | Path,
    *,
    method: str,
    source: str,
    evaluation_note: str,
) -> Path:
    """Write predictions plus a small provenance sidecar used by Session 3."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(path)
    metadata_path = path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "method": method,
                "source": source,
                "evaluation_note": evaluation_note,
                "rows": len(predictions),
                "proteins": predictions.shape[1],
            },
            indent=2,
        )
        + "\n"
    )
    return metadata_path


def load_prediction_metadata(path: str | Path) -> dict[str, object] | None:
    """Load a prediction provenance sidecar when one is available."""

    metadata_path = Path(path).with_suffix(".metadata.json")
    if not metadata_path.exists():
        return None
    return json.loads(metadata_path.read_text())


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
    discovered_model_dir = discover_dgat_model_dir(
        [
            model_save_dir,
            model_save_dir.parent,
            dgat_repo_dir / "DGAT_pretrained_models",
            dgat_repo_dir,
            Path("external") / "DGAT_assets",
        ]
    )
    if discovered_model_dir is None:
        raise FileNotFoundError(
            f"No compatible DGAT checkpoints were found under {model_save_dir} or the standard asset locations. "
            "Both encoder_mRNA.pth and decoder_protein.pth must be present in the same checkpoint directory."
        )
    if discovered_model_dir != model_save_dir:
        print(f"Using discovered DGAT pretrained model directory: {discovered_model_dir}")
    model_save_dir = discovered_model_dir

    common_gene_path, common_protein_path = resolve_dgat_resource_files(
        dgat_repo_dir=dgat_repo_dir,
        model_save_dir=model_save_dir,
        common_gene_path=common_gene_path,
        common_protein_path=common_protein_path,
    )
    common_gene = read_feature_list(common_gene_path)
    common_protein = read_feature_list(common_protein_path)
    model_save_dir = prepare_dgat_model_layout(
        model_save_dir,
        gene_count=len(common_gene),
        protein_count=len(common_protein),
        adapter_root=pyg_data_dir / "checkpoint_layout",
    )

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
    if hasattr(predictions, "X"):
        matrix = predictions.X.toarray() if hasattr(predictions.X, "toarray") else np.asarray(predictions.X)
        columns = [str(name) for name in predictions.var_names]
        index = predictions.obs_names
    else:
        matrix = np.asarray(predictions)
        columns = common_protein
        index = adata.obs_names
    return pd.DataFrame(matrix, index=index, columns=columns)


def prepare_dgat_model_layout(
    model_save_dir: str | Path,
    *,
    gene_count: int,
    protein_count: int,
    adapter_root: str | Path,
) -> Path:
    """Provide the nested checkpoint layout required by DGAT ``protein_predict``.

    Google Drive currently supplies flat checkpoint files, while upstream DGAT
    looks below ``<genes>_gene_<proteins>_protein``. Hard links avoid duplicating
    the large encoder; copying is a portable fallback when links are unavailable.
    """

    model_save_dir = Path(model_save_dir)
    checkpoint_name = f"{gene_count}_gene_{protein_count}_protein"
    nested_dir = model_save_dir / checkpoint_name
    required_files = ("encoder_mRNA.pth", "decoder_protein.pth")
    if all((nested_dir / filename).is_file() for filename in required_files):
        return model_save_dir

    if not all((model_save_dir / filename).is_file() for filename in required_files):
        raise FileNotFoundError(
            f"DGAT checkpoints are incomplete under {model_save_dir}; expected both "
            "encoder_mRNA.pth and decoder_protein.pth."
        )

    adapter_root = Path(adapter_root)
    adapter_dir = adapter_root / checkpoint_name
    adapter_dir.mkdir(parents=True, exist_ok=True)
    for filename in required_files:
        source = model_save_dir / filename
        destination = adapter_dir / filename
        if destination.exists():
            continue
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
    print(f"Using DGAT checkpoint compatibility layout: {adapter_dir}")
    return adapter_root


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
    if gene_count is None or protein_count is None:
        checkpoint_counts = infer_feature_counts_from_flat_checkpoints(model_save_dir)
        if checkpoint_counts is not None:
            gene_count, protein_count = checkpoint_counts
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


def infer_feature_counts_from_flat_checkpoints(model_save_dir: str | Path) -> tuple[int, int] | None:
    """Infer gene/protein counts from the flat public DGAT checkpoints."""

    model_save_dir = Path(model_save_dir)
    encoder_path = model_save_dir / "encoder_mRNA.pth"
    decoder_path = model_save_dir / "decoder_protein.pth"
    if not encoder_path.is_file() or not decoder_path.is_file():
        return None
    try:
        import torch
    except ImportError as exc:
        raise ImportError("Inspecting flat DGAT checkpoints requires PyTorch in the official environment.") from exc

    encoder_state = torch.load(encoder_path, map_location="cpu")
    input_weight = encoder_state.get("conv1.lin.weight")
    if input_weight is None or input_weight.ndim != 2:
        raise ValueError(f"Could not infer the DGAT gene count from {encoder_path}.")
    gene_count = int(input_weight.shape[1])

    decoder_state = torch.load(decoder_path, map_location="cpu")
    protein_names = {
        key.split(".")[1]
        for key in decoder_state
        if key.startswith("protein_branches.") and len(key.split(".")) > 2
    }
    if not protein_names:
        raise ValueError(f"Could not infer the DGAT protein count from {decoder_path}.")
    return gene_count, len(protein_names)


def infer_feature_counts_from_model_dir(model_save_dir: str | Path) -> tuple[int | None, int | None]:
    """Infer feature counts from directories like `17434_gene_31_protein`."""

    model_save_dir = Path(model_save_dir)
    pattern = re.compile(r"(?P<genes>\d+)_gene_(?P<proteins>\d+)_protein")
    for path in sorted(model_save_dir.glob("*_gene_*_protein")):
        match = pattern.fullmatch(path.name)
        if match:
            return int(match.group("genes")), int(match.group("proteins"))
    return None, None


def discover_dgat_model_dir(search_roots: list[Path]) -> Path | None:
    """Find the root directory that should be passed to DGAT protein_predict."""

    candidate_checkpoint_dirs = []
    for root in search_roots:
        if not root.exists():
            continue
        for encoder_path in root.rglob("encoder_mRNA.pth"):
            checkpoint_dir = encoder_path.parent
            if (checkpoint_dir / "decoder_protein.pth").exists():
                candidate_checkpoint_dirs.append(checkpoint_dir)

    if not candidate_checkpoint_dirs:
        return None

    candidate_checkpoint_dirs = sorted(set(candidate_checkpoint_dirs), key=lambda path: str(path))
    checkpoint_dir = candidate_checkpoint_dirs[0]
    if re.fullmatch(r"\d+_gene_\d+_protein", checkpoint_dir.name):
        return checkpoint_dir.parent
    return checkpoint_dir


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
