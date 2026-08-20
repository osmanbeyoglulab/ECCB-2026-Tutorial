from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Sessions 1-2 use paired Tonsil RNA/ADT. Session 3 uses a separate,
# transcript-only lymph-node sample for pretrained-model inference.
TUTORIAL_DATASET_NAME = "Tonsil"
TUTORIAL_RNA_FILENAME = "Tonsil_RNA.h5ad"
TUTORIAL_ADT_FILENAME = "Tonsil_ADT.h5ad"
LYMPH_NODE_DATASET_NAME = "V1_Human_Lymph_Node"
LYMPH_NODE_MATRIX_FILENAME = "V1_Human_Lymph_Node_filtered_feature_bc_matrix.h5"
LYMPH_NODE_SPATIAL_DIRNAME = "spatial"
LYMPH_NODE_GC_FILENAME = "V1_Human_Lymph_Node_manual_GC_annot.csv"


@dataclass(frozen=True)
class SpatialOmicsData:
    """Container used by the tutorial notebooks."""

    spots: pd.DataFrame
    transcripts: pd.DataFrame
    proteins: pd.DataFrame | None = None
    image_path: Path | None = None
    scale_factors: dict[str, float] | None = None


def load_tutorial_data(data_dir: str | Path) -> SpatialOmicsData:
    """Load the paired Tonsil RNA/ADT sample used in Sessions 1-2.

    The participant workflow intentionally has no generated-data substitute.
    Missing or incomplete Tonsil assets stop with an actionable setup error.
    """

    return load_tonsil_tutorial_data(data_dir)


def load_tonsil_tutorial_data(data_dir: str | Path) -> SpatialOmicsData:
    """Load the exact paired Tonsil files distributed for the tutorial."""

    data_dir = Path(data_dir)
    pair = find_dgat_h5ad_pair(data_dir)
    if pair is not None:
        return load_paired_h5ad_dataset(*pair)

    raise FileNotFoundError(
        "Missing paired Tonsil RNA/ADT files. Run Session 0 or "
        "`bash scripts/download_dgat_assets.sh --dataset Tonsil`, then rerun this notebook."
    )


def load_lymph_node_tutorial_data(data_dir: str | Path) -> SpatialOmicsData:
    """Load the transcript-only 10x lymph-node sample used in Session 3."""

    data_dir = Path(data_dir)
    matrix_path = data_dir / LYMPH_NODE_MATRIX_FILENAME
    spatial_dir = data_dir / LYMPH_NODE_SPATIAL_DIRNAME
    if matrix_path.is_file() and spatial_dir.is_dir():
        return load_10x_visium_dataset(matrix_path, spatial_dir)

    raise FileNotFoundError(
        "Missing the 10x V1_Human_Lymph_Node data required by this tutorial. Run "
        "`bash scripts/download_dgat_assets.sh --dataset V1_Human_Lymph_Node` and "
        "`bash scripts/download_dgat_assets.sh --dataset V1_Human_Lymph_Node --check-only` "
        "during Session 0, then rerun this notebook."
    )


def load_10x_visium_dataset(matrix_path: str | Path, spatial_dir: str | Path) -> SpatialOmicsData:
    """Load the filtered GEX matrix, coordinates, and image metadata for 10x Visium."""

    try:
        import scanpy as sc
    except ImportError as exc:
        raise ImportError("Reading the lymph-node 10x matrix requires `scanpy`.") from exc

    matrix_path = Path(matrix_path)
    spatial_dir = Path(spatial_dir)
    adata = sc.read_10x_h5(matrix_path, gex_only=True)
    adata.var_names_make_unique()
    positions_path = spatial_dir / "tissue_positions_list.csv"
    if not positions_path.is_file():
        positions_path = spatial_dir / "tissue_positions.csv"
    if not positions_path.is_file():
        raise FileNotFoundError(f"No tissue positions CSV was found under {spatial_dir}.")
    positions = pd.read_csv(
        positions_path,
        header=None,
        names=["barcode", "in_tissue", "array_row", "array_col", "pxl_row_in_fullres", "pxl_col_in_fullres"],
        index_col="barcode",
    )
    positions.index = positions.index.astype(str)
    positions = positions.loc[positions["in_tissue"].astype(int).eq(1)]
    common = adata.obs_names.intersection(positions.index, sort=False)
    if common.empty:
        raise ValueError("The lymph-node count matrix and tissue-position file have no shared barcodes.")
    adata = adata[common].copy()
    positions = positions.loc[common]

    spots = positions.copy()
    spots["x"] = spots["pxl_col_in_fullres"].astype(float)
    spots["y"] = spots["pxl_row_in_fullres"].astype(float)
    import json

    scale_path = spatial_dir / "scalefactors_json.json"
    scale_factors = json.loads(scale_path.read_text()) if scale_path.is_file() else None
    image_path = next(
        (path for path in (spatial_dir / "tissue_hires_image.png", spatial_dir / "tissue_lowres_image.png") if path.is_file()),
        None,
    )
    return SpatialOmicsData(
        spots=spots,
        transcripts=_matrix_to_dataframe(adata),
        proteins=None,
        image_path=image_path,
        scale_factors=scale_factors,
    )


def load_gc_annotations(path: str | Path) -> pd.Series:
    """Load the tracked list of manual germinal-center-positive barcodes."""

    path = Path(path)
    labels = pd.read_csv(path, index_col="Barcode")["GC"]
    labels.index = labels.index.astype(str)
    if labels.index.has_duplicates:
        raise ValueError(f"{path} contains duplicate barcodes.")
    unexpected = sorted(set(labels.dropna().astype(str)) - {"GC"})
    if unexpected:
        raise ValueError(f"Unexpected germinal-center labels in {path}: {unexpected}")
    return labels.eq("GC").rename("germinal_center")


def find_dgat_h5ad(data_dir: str | Path) -> Path | None:
    """Find a DGAT H5AD file in the expected tutorial locations."""

    matches = _find_h5ad_files(data_dir)
    if not matches:
        return None
    return _prefer_transcript_h5ad(matches)


def find_dgat_h5ad_pair(data_dir: str | Path) -> tuple[Path, Path] | None:
    """Find paired Tonsil RNA and ADT files, preferring the exact release names."""

    matches = _find_h5ad_files(data_dir)
    if not matches:
        return None

    by_name = {path.name: path for path in matches}
    if TUTORIAL_RNA_FILENAME in by_name and TUTORIAL_ADT_FILENAME in by_name:
        return by_name[TUTORIAL_RNA_FILENAME], by_name[TUTORIAL_ADT_FILENAME]

    tonsil_matches = [
        path for path in matches
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
                "paired RNA AnnData file. Make sure both files are in the same "
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
