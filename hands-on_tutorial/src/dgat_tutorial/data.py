from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SpatialOmicsData:
    """Container used by the tutorial notebooks."""

    spots: pd.DataFrame
    transcripts: pd.DataFrame
    proteins: pd.DataFrame


def load_tutorial_data(data_dir: str | Path) -> SpatialOmicsData:
    """Load the official paired Breast RNA and ADT AnnData files.

    The participant workflow intentionally has no generated-data substitute.
    Missing or incomplete Breast assets stop with an actionable setup error.
    """

    data_dir = Path(data_dir)
    h5ad_pair = find_dgat_h5ad_pair(data_dir)
    if h5ad_pair is not None:
        return load_paired_h5ad_dataset(*h5ad_pair)

    raise FileNotFoundError(
        "Missing the paired Breast RNA/ADT data required by this tutorial. Run "
        "`bash scripts/download_dgat_assets.sh --data-only --dataset Breast` and "
        "`bash scripts/download_dgat_assets.sh --data-only --dataset Breast --check-only` "
        "during Session 0, then rerun this notebook."
    )


def find_dgat_h5ad(data_dir: str | Path) -> Path | None:
    """Find a DGAT H5AD file in the expected tutorial locations."""

    matches = _find_h5ad_files(data_dir)
    if not matches:
        return None
    return _prefer_transcript_h5ad(matches)


def find_dgat_h5ad_pair(data_dir: str | Path) -> tuple[Path, Path] | None:
    """Find paired RNA and ADT/protein DGAT H5AD files."""

    matches = [path for path in _find_h5ad_files(data_dir) if "breast" in path.name.lower()]
    if len(matches) < 2:
        return None

    transcript_files = [path for path in matches if _looks_like_transcript_h5ad(path)]
    protein_files = [path for path in matches if _looks_like_protein_h5ad(path)]
    if not transcript_files or not protein_files:
        return None

    return transcript_files[0], protein_files[0]


def _find_h5ad_files(data_dir: str | Path) -> list[Path]:
    """Collect DGAT H5AD files from expected tutorial locations."""

    data_dir = Path(data_dir)
    repo_root = data_dir.parents[1] if data_dir.name == "raw" and data_dir.parent.name == "data" else Path.cwd()
    candidate_dirs = [
        data_dir,
        repo_root / "external" / "DGAT_assets" / "DGAT_prediction_ST_data",
        repo_root / "external" / "DGAT_assets",
        repo_root / "external" / "DGAT" / "DGAT_prediction_ST_data",
    ]
    matches = []
    for candidate_dir in candidate_dirs:
        if candidate_dir.exists():
            matches.extend(sorted(candidate_dir.rglob("*.h5ad")))
    return sorted(set(matches), key=lambda path: str(path))


def _looks_like_transcript_h5ad(path: Path) -> bool:
    name = path.name.lower()
    return any(token in name for token in ["rna", "gene", "transcript", "mrna", "gex"])


def _looks_like_protein_h5ad(path: Path) -> bool:
    name = path.name.lower()
    return any(token in name for token in ["adt", "protein", "cite", "antibody"])


def _prefer_transcript_h5ad(paths: list[Path]) -> Path:
    transcript_files = [path for path in paths if _looks_like_transcript_h5ad(path)]
    if transcript_files:
        return transcript_files[0]
    non_protein_files = [path for path in paths if not _looks_like_protein_h5ad(path)]
    if non_protein_files:
        return non_protein_files[0]
    return paths[0]


def _read_anndata(path: Path):
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("Reading DGAT .h5ad files requires `anndata`. Install the tutorial environment first.") from exc

    return ad.read_h5ad(path)


def _matrix_to_dataframe(adata) -> pd.DataFrame:
    matrix = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    return pd.DataFrame(matrix, index=adata.obs_names, columns=adata.var_names)


def _spots_from_anndata(adata, path: Path) -> pd.DataFrame:
    spots = adata.obs.copy()
    if "spatial" in adata.obsm:
        spatial = np.asarray(adata.obsm["spatial"])
        spots["x"] = spatial[:, 0]
        spots["y"] = spatial[:, 1]
    elif "x" not in spots.columns or "y" not in spots.columns:
        x_col = next((col for col in ["X", "array_row", "row", "pxl_col_in_fullres"] if col in spots.columns), None)
        y_col = next((col for col in ["Y", "array_col", "col", "pxl_row_in_fullres"] if col in spots.columns), None)
        if x_col is None or y_col is None:
            raise ValueError(f"{path} does not contain `obsm['spatial']` or recognizable coordinate columns.")
        spots = spots.rename(columns={x_col: "x", y_col: "y"})
    return spots


def load_paired_h5ad_dataset(transcript_path: str | Path, protein_path: str | Path) -> SpatialOmicsData:
    """Load DGAT assets split across RNA and ADT/protein AnnData files."""

    transcript_path = Path(transcript_path)
    protein_path = Path(protein_path)
    transcript_adata = _read_anndata(transcript_path)
    protein_adata = _read_anndata(protein_path)

    spots = _spots_from_anndata(transcript_adata, transcript_path)
    transcripts = _matrix_to_dataframe(transcript_adata)
    proteins = canonicalize_protein_columns(_matrix_to_dataframe(protein_adata))

    common = spots.index.intersection(transcripts.index).intersection(proteins.index)
    if common.empty:
        raise ValueError(
            f"No shared observations between {transcript_path} and {protein_path}. "
            "Check that RNA and ADT files are from the same DGAT dataset."
        )

    return SpatialOmicsData(
        spots=spots.loc[common],
        transcripts=transcripts.loc[common],
        proteins=proteins.loc[common],
    )


def load_h5ad_dataset(path: str | Path) -> SpatialOmicsData:
    """Load a DGAT AnnData file without converting it to CSV first."""

    path = Path(path)
    adata = _read_anndata(path)
    spots = _spots_from_anndata(adata, path)
    transcripts = _matrix_to_dataframe(adata)

    protein_key = next(
        (
            key
            for key in [
                "protein",
                "proteins",
                "protein_expression",
                "protein_expression_raw",
                "ADT",
                "CITE",
            ]
            if key in adata.obsm
        ),
        None,
    )
    if protein_key is None:
        if _looks_like_protein_h5ad(path):
            raise ValueError(
                f"{path} looks like an ADT/protein AnnData file. DGAT assets usually pair it with an RNA "
                "AnnData file such as `Breast_RNA.h5ad`. Make sure both files are downloaded in the same "
                "asset directory."
            )
        raise ValueError(
            f"{path} does not contain observed protein values in `.obsm`. "
            "Expected one of: protein, proteins, protein_expression, protein_expression_raw, ADT, CITE."
        )

    protein_matrix = adata.obsm[protein_key]
    if isinstance(protein_matrix, pd.DataFrame):
        proteins = protein_matrix.copy()
        proteins.index = adata.obs_names
    else:
        protein_matrix = protein_matrix.toarray() if hasattr(protein_matrix, "toarray") else np.asarray(protein_matrix)
        protein_names = _protein_names_from_anndata(adata, protein_key, protein_matrix.shape[1])
        proteins = pd.DataFrame(protein_matrix, index=adata.obs_names, columns=protein_names)
    proteins = canonicalize_protein_columns(proteins)

    return SpatialOmicsData(spots=spots, transcripts=transcripts, proteins=proteins)


def _protein_names_from_anndata(adata, protein_key: str, n_proteins: int) -> list[str]:
    for key in [
        f"{protein_key}_names",
        f"{protein_key}_features",
        "protein_names",
        "protein_features",
        "adt_names",
        "ADT_names",
    ]:
        if key in adata.uns:
            names = list(adata.uns[key])
            if len(names) == n_proteins:
                return [str(name) for name in names]
    return [f"protein_{i + 1}" for i in range(n_proteins)]


def canonicalize_protein_columns(proteins: pd.DataFrame) -> pd.DataFrame:
    """Align DGAT ADT labels with the gene-symbol names used by the decoder."""

    renamed: dict[object, str] = {}
    for column in proteins.columns:
        name = str(column)
        if name in {"PTPRC-1", "PTPRC-2"}:
            canonical = name.replace("-", "_")
        elif name.endswith("-1"):
            canonical = name[:-2]
        else:
            canonical = name.replace("-", "_")
        renamed[column] = canonical

    canonical_names = list(renamed.values())
    if len(canonical_names) != len(set(canonical_names)):
        raise ValueError("Protein-name normalization produced duplicate columns; inspect the ADT feature labels.")
    return proteins.rename(columns=renamed)


def load_csv_dataset(data_dir: str | Path) -> SpatialOmicsData:
    """Load a simple CSV dataset from data/raw.

    Expected files:
    - spots.csv with a spot_id column plus x and y columns.
    - transcripts.csv with spot IDs as the first column.
    - proteins.csv with spot IDs as the first column.
    """

    data_dir = Path(data_dir)
    spots = pd.read_csv(data_dir / "spots.csv").set_index("spot_id")
    transcripts = pd.read_csv(data_dir / "transcripts.csv", index_col=0)
    proteins = pd.read_csv(data_dir / "proteins.csv", index_col=0)

    common = spots.index.intersection(transcripts.index).intersection(proteins.index)
    return SpatialOmicsData(
        spots=spots.loc[common],
        transcripts=transcripts.loc[common],
        proteins=proteins.loc[common],
    )
