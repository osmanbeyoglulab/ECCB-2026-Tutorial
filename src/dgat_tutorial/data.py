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


def load_demo_data(n_spots: int = 260, random_state: int = 7) -> SpatialOmicsData:
    """Create a compact spatial-CITE-seq-like dataset for offline tutorial use."""

    rng = np.random.default_rng(random_state)
    side = int(np.ceil(np.sqrt(n_spots)))
    grid_x, grid_y = np.meshgrid(np.arange(side), np.arange(side))
    coords = np.column_stack([grid_x.ravel(), grid_y.ravel()])[:n_spots].astype(float)
    coords += rng.normal(scale=0.08, size=coords.shape)

    center = coords.mean(axis=0)
    distance = np.linalg.norm(coords - center, axis=1)
    radial = (distance - distance.min()) / (distance.max() - distance.min())
    left_right = (coords[:, 0] - coords[:, 0].min()) / np.ptp(coords[:, 0])
    top_bottom = (coords[:, 1] - coords[:, 1].min()) / np.ptp(coords[:, 1])

    spots = pd.DataFrame(
        {
            "spot_id": [f"spot_{i:03d}" for i in range(n_spots)],
            "x": coords[:, 0],
            "y": coords[:, 1],
            "region": np.where(radial < 0.42, "core", np.where(left_right > 0.55, "right edge", "left edge")),
        }
    ).set_index("spot_id")

    latent = np.column_stack([radial, left_right, top_bottom])
    gene_names = [f"Gene{i:02d}" for i in range(1, 25)]
    gene_weights = rng.normal(size=(latent.shape[1], len(gene_names)))
    gene_signal = latent @ gene_weights + rng.normal(scale=0.35, size=(n_spots, len(gene_names)))
    transcripts = pd.DataFrame(
        np.exp(gene_signal - gene_signal.min(axis=0) + 0.2),
        index=spots.index,
        columns=gene_names,
    )

    protein_names = ["CD3", "CD19", "EPCAM", "COL1A1", "PDL1", "KI67"]
    protein_weights = rng.normal(size=(len(gene_names), len(protein_names)))
    protein_signal = np.log1p(transcripts.to_numpy()) @ protein_weights / len(gene_names)
    protein_signal += np.column_stack(
        [
            1.6 * (1 - radial),
            1.4 * left_right,
            1.4 * (1 - left_right),
            1.6 * radial,
            1.2 * top_bottom,
            1.2 * (1 - top_bottom),
        ]
    )
    protein_signal += rng.normal(scale=0.12, size=protein_signal.shape)
    proteins = pd.DataFrame(
        protein_signal - protein_signal.min(axis=0),
        index=spots.index,
        columns=protein_names,
    )

    return SpatialOmicsData(spots=spots, transcripts=transcripts, proteins=proteins)


def load_tutorial_data(data_dir: str | Path, allow_demo: bool = True) -> SpatialOmicsData:
    """Load tutorial data, preferring official DGAT .h5ad files.

    DGAT's original notebooks use AnnData/H5AD files directly. This loader
    first searches the downloaded DGAT asset locations for ``*.h5ad`` files.
    CSV loading is kept only as a fallback for local exported tables.
    """

    data_dir = Path(data_dir)
    h5ad_path = find_dgat_h5ad(data_dir)
    if h5ad_path is not None:
        return load_h5ad_dataset(h5ad_path)

    expected = [data_dir / name for name in ["spots.csv", "transcripts.csv", "proteins.csv"]]
    if all(path.exists() for path in expected):
        return load_csv_dataset(data_dir)
    if allow_demo:
        return load_demo_data()

    raise FileNotFoundError(
        "Missing tutorial data. Download the DGAT Google Drive assets with "
        "`bash scripts/download_dgat_assets.sh`, then keep the .h5ad files under "
        "`external/DGAT_assets/` or copy one into `data/raw/`."
    )


def find_dgat_h5ad(data_dir: str | Path) -> Path | None:
    """Find the first DGAT H5AD file in the expected tutorial locations."""

    data_dir = Path(data_dir)
    repo_root = data_dir.parents[1] if data_dir.name == "raw" and data_dir.parent.name == "data" else Path.cwd()
    candidate_dirs = [
        data_dir,
        repo_root / "external" / "DGAT_assets" / "DGAT_prediction_ST_data",
        repo_root / "external" / "DGAT_assets",
        repo_root / "external" / "DGAT" / "DGAT_prediction_ST_data",
    ]
    for candidate_dir in candidate_dirs:
        if candidate_dir.exists():
            matches = sorted(candidate_dir.rglob("*.h5ad"))
            if matches:
                return matches[0]
    return None


def load_h5ad_dataset(path: str | Path) -> SpatialOmicsData:
    """Load a DGAT AnnData file without converting it to CSV first."""

    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("Reading DGAT .h5ad files requires `anndata`. Install the tutorial environment first.") from exc

    path = Path(path)
    adata = ad.read_h5ad(path)

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

    matrix = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    transcripts = pd.DataFrame(matrix, index=adata.obs_names, columns=adata.var_names)

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
