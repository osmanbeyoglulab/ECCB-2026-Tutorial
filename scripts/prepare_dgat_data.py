from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".tsv" or path.name.endswith(".txt"):
        return pd.read_csv(path, sep="\t", index_col=0)
    return pd.read_csv(path, index_col=0)


def _write_standard_csvs(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    spots = spots.copy()
    transcripts = transcripts.copy()
    proteins = proteins.copy()

    common = spots.index.intersection(transcripts.index).intersection(proteins.index)
    if common.empty:
        raise ValueError("No shared spot/cell IDs across spots, transcripts, and proteins.")

    spots = spots.loc[common]
    transcripts = transcripts.loc[common]
    proteins = proteins.loc[common]

    spots = spots.reset_index().rename(columns={spots.index.name or "index": "spot_id"})
    if "spot_id" not in spots.columns:
        spots = spots.rename(columns={spots.columns[0]: "spot_id"})

    spots.to_csv(output_dir / "spots.csv", index=False)
    transcripts.to_csv(output_dir / "transcripts.csv")
    proteins.to_csv(output_dir / "proteins.csv")


def _load_h5ad(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("Reading .h5ad files requires `anndata`. Install tutorial requirements first.") from exc

    adata = ad.read_h5ad(path)

    if "spatial" in adata.obsm:
        xy = np.asarray(adata.obsm["spatial"])
        spots = adata.obs.copy()
        spots["x"] = xy[:, 0]
        spots["y"] = xy[:, 1]
    else:
        spots = adata.obs.copy()
        x_col = next((col for col in ["x", "X", "array_row", "row"] if col in spots.columns), None)
        y_col = next((col for col in ["y", "Y", "array_col", "col"] if col in spots.columns), None)
        if x_col is None or y_col is None:
            raise ValueError(f"{path} does not contain obsm['spatial'] or recognizable coordinate columns.")
        spots = spots.rename(columns={x_col: "x", y_col: "y"})

    matrix = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    transcripts = pd.DataFrame(matrix, index=adata.obs_names, columns=adata.var_names)

    protein_key = next((key for key in ["protein", "proteins", "protein_expression", "ADT", "CITE"] if key in adata.obsm), None)
    if protein_key is None:
        raise ValueError(
            f"{path} does not contain protein values in obsm. Expected one of: protein, proteins, "
            "protein_expression, ADT, CITE."
        )

    protein_matrix = adata.obsm[protein_key]
    protein_matrix = protein_matrix.toarray() if hasattr(protein_matrix, "toarray") else np.asarray(protein_matrix)
    protein_names = None
    if f"{protein_key}_names" in adata.uns:
        protein_names = list(adata.uns[f"{protein_key}_names"])
    elif hasattr(protein_matrix, "columns"):
        protein_names = list(protein_matrix.columns)
    if protein_names is None:
        protein_names = [f"protein_{i + 1}" for i in range(protein_matrix.shape[1])]

    proteins = pd.DataFrame(protein_matrix, index=adata.obs_names, columns=protein_names)
    return spots[["x", "y"] + [col for col in spots.columns if col not in {"x", "y"}]], transcripts, proteins


def _find_first(root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(root.rglob(pattern))
        if matches:
            return matches[0]
    return None


def prepare_from_dgat_assets(asset_dir: Path, output_dir: Path) -> None:
    """Prepare tutorial CSVs from downloaded official DGAT data assets."""

    h5ad = _find_first(asset_dir, ["*.h5ad"])
    if h5ad is not None:
        spots, transcripts, proteins = _load_h5ad(h5ad)
        _write_standard_csvs(spots, transcripts, proteins, output_dir)
        print(f"Prepared tutorial data from {h5ad}")
        return

    spots_path = _find_first(asset_dir, ["*spot*.csv", "*coord*.csv", "*location*.csv", "*meta*.csv"])
    transcript_path = _find_first(asset_dir, ["*transcript*.csv", "*RNA*.csv", "*gene*.csv", "*expression*.csv"])
    protein_path = _find_first(asset_dir, ["*protein*.csv", "*ADT*.csv", "*CITE*.csv"])

    if not all([spots_path, transcript_path, protein_path]):
        raise FileNotFoundError(
            "Could not automatically identify official DGAT data files. Expected either a .h5ad file or "
            "CSV files for spots/coordinates, transcripts, and proteins under the asset directory.\n"
            f"Searched under: {asset_dir}"
        )

    spots = _read_table(spots_path)
    if "spot_id" in spots.columns:
        spots = spots.set_index("spot_id")
    if "x" not in spots.columns or "y" not in spots.columns:
        x_col = next((col for col in ["X", "array_row", "row", "pxl_col_in_fullres"] if col in spots.columns), None)
        y_col = next((col for col in ["Y", "array_col", "col", "pxl_row_in_fullres"] if col in spots.columns), None)
        if x_col is None or y_col is None:
            raise ValueError(f"Could not find x/y coordinate columns in {spots_path}")
        spots = spots.rename(columns={x_col: "x", y_col: "y"})

    transcripts = _read_table(transcript_path)
    proteins = _read_table(protein_path)
    _write_standard_csvs(spots, transcripts, proteins, output_dir)
    print(f"Prepared tutorial data from {asset_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare tutorial CSVs from official DGAT data assets.")
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=Path("external/DGAT_assets/DGAT_prediction_ST_data"),
        help="Directory containing official DGAT prediction data assets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory where tutorial CSV files should be written.",
    )
    args = parser.parse_args()

    prepare_from_dgat_assets(args.asset_dir, args.output_dir)


if __name__ == "__main__":
    main()
