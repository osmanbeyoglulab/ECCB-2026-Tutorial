from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Participant tutorial sample (official DGAT training-asset filenames).
TUTORIAL_DATASET_NAME = "Tonsil"
TUTORIAL_RNA_FILENAME = "Tonsil_RNA.h5ad"
TUTORIAL_ADT_FILENAME = "Tonsil_ADT.h5ad"


@dataclass(frozen=True)
class SpatialOmicsData:
    """Container used by the tutorial notebooks."""

    spots: pd.DataFrame
    transcripts: pd.DataFrame
    proteins: pd.DataFrame


def load_tutorial_data(data_dir: str | Path) -> SpatialOmicsData:
    """Load the official paired Tonsil RNA and ADT AnnData files.

    The participant workflow intentionally has no generated-data substitute.
    Missing or incomplete Tonsil assets stop with an actionable setup error.
    """

    data_dir = Path(data_dir)
    h5ad_pair = find_dgat_h5ad_pair(data_dir)
    if h5ad_pair is not None:
        return load_paired_h5ad_dataset(*h5ad_pair)

    raise FileNotFoundError(
        "Missing the paired Tonsil RNA/ADT data required by this tutorial. Run "
        "`bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil` and "
        "`bash scripts/download_dgat_assets.sh --data-only --dataset Tonsil --check-only` "
        "during Session 0, then rerun this notebook."
    )


def find_dgat_h5ad(data_dir: str | Path) -> Path | None:
    """Find a DGAT H5AD file in the expected tutorial locations."""

    matches = _find_h5ad_files(data_dir)
    if not matches:
        return None
    return _prefer_transcript_h5ad(matches)


def find_dgat_h5ad_pair(data_dir: str | Path) -> tuple[Path, Path] | None:
    """Find the paired Tonsil RNA and ADT DGAT H5AD files used by this tutorial.

    Prefer exact ``Tonsil_RNA.h5ad`` / ``Tonsil_ADT.h5ad`` filenames and ignore
    ``Tonsil_AddOns_*`` assets that share the same tissue label.
    """

    matches = _find_h5ad_files(data_dir)
    if not matches:
        return None

    by_name = {path.name: path for path in matches}
    if TUTORIAL_RNA_FILENAME in by_name and TUTORIAL_ADT_FILENAME in by_name:
        return by_name[TUTORIAL_RNA_FILENAME], by_name[TUTORIAL_ADT_FILENAME]

    # Fallback: any non-AddOns Tonsil RNA/ADT pair under a shared directory.
    tonsil_matches = [
        path
        for path in matches
        if "tonsil" in path.name.lower() and "addons" not in path.name.lower()
    ]
    transcript_files = [path for path in tonsil_matches if _looks_like_transcript_h5ad(path)]
    protein_files = [path for path in tonsil_matches if _looks_like_protein_h5ad(path)]
    if not transcript_files or not protein_files:
        return None

    return transcript_files[0], protein_files[0]


def _find_h5ad_files(data_dir: str | Path) -> list[Path]:
    """Collect DGAT H5AD files from the requested directory and, when applicable, tutorial assets."""

    data_dir = Path(data_dir).resolve()
    matches: list[Path] = []
    if data_dir.exists():
        matches.extend(sorted(data_dir.rglob("*.h5ad")))

    tutorial_root = None
    for candidate in (data_dir, *data_dir.parents):
        if (candidate / "src" / "dgat_tutorial").is_dir() and (candidate / "scripts").is_dir():
            tutorial_root = candidate
            break

    # Only expand to ignored external asset folders when the caller is inside the tutorial tree.
    # Temporary working directories must not silently resolve unrelated assets via Path.cwd().
    if tutorial_root is not None and data_dir.is_relative_to(tutorial_root):
        for candidate_dir in (
            tutorial_root / "external" / "DGAT_assets" / "DGAT_prediction_ST_data",
            tutorial_root / "external" / "DGAT_assets",
            tutorial_root / "external" / "DGAT" / "DGAT_prediction_ST_data",
        ):
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

    from dgat_tutorial.alignment import require_exact_identifiers

    require_exact_identifiers(
        spots.index,
        transcripts.index,
        left_name=f"RNA spots ({transcript_path.name})",
        right_name=f"RNA matrix ({transcript_path.name})",
    )
    require_exact_identifiers(
        spots.index,
        proteins.index,
        left_name=f"RNA spots ({transcript_path.name})",
        right_name=f"ADT spots ({protein_path.name})",
    )
    if not spots.index.equals(transcripts.index):
        transcripts = transcripts.loc[spots.index]
    if not spots.index.equals(proteins.index):
        proteins = proteins.loc[spots.index]

    return SpatialOmicsData(
        spots=spots,
        transcripts=transcripts,
        proteins=proteins,
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
                "AnnData file such as `Tonsil_RNA.h5ad`. Make sure both files are downloaded in the same "
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

    from dgat_tutorial.alignment import require_exact_identifiers

    require_exact_identifiers(spots.index, transcripts.index, left_name="spots.csv", right_name="transcripts.csv")
    require_exact_identifiers(spots.index, proteins.index, left_name="spots.csv", right_name="proteins.csv")
    if not spots.index.equals(transcripts.index):
        transcripts = transcripts.loc[spots.index]
    if not spots.index.equals(proteins.index):
        proteins = proteins.loc[spots.index]
    return SpatialOmicsData(
        spots=spots,
        transcripts=transcripts,
        proteins=proteins,
    )
