from __future__ import annotations

import numpy as np
import pandas as pd


def protein_correlations(observed: pd.DataFrame, predicted: pd.DataFrame) -> pd.DataFrame:
    """Compute per-protein Pearson and Spearman correlations."""

    common_spots = observed.index.intersection(predicted.index)
    common_proteins = observed.columns.intersection(predicted.columns)
    if common_spots.empty:
        raise ValueError("Observed and predicted protein tables have no shared spot/cell IDs.")
    if common_proteins.empty:
        raise ValueError(
            "Observed and predicted protein tables have no shared protein names. "
            "Confirm that ADT labels were normalized to the DGAT decoder gene-symbol convention."
        )
    rows = []
    for protein in common_proteins:
        y_true = observed.loc[common_spots, protein]
        y_pred = predicted.loc[common_spots, protein]
        y_true_rank = y_true.rank(method="average")
        y_pred_rank = y_pred.rank(method="average")
        rows.append(
            {
                "protein": protein,
                "pearson": y_true.corr(y_pred, method="pearson"),
                "spearman": y_true_rank.corr(y_pred_rank, method="pearson"),
            }
        )
    return pd.DataFrame(rows).sort_values("pearson", ascending=False)


def spatial_weights(coordinates: pd.DataFrame, radius: float | None = None) -> np.ndarray:
    """Build a binary spatial-neighborhood matrix."""

    xy = coordinates[["x", "y"]].to_numpy()
    distances = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    if radius is None:
        nearest = np.partition(distances, kth=1, axis=1)[:, 1]
        radius = float(np.median(nearest) * 1.8)
    weights = (distances <= radius).astype(float)
    np.fill_diagonal(weights, 0)
    return weights


def morans_i(values: pd.Series, coordinates: pd.DataFrame, radius: float | None = None) -> float:
    """Compute Moran's I for one spatial feature."""

    from scipy.spatial import cKDTree

    aligned_coordinates = coordinates.loc[values.index]
    xy = aligned_coordinates[["x", "y"]].to_numpy(dtype=float)
    tree = cKDTree(xy)
    if radius is None:
        nearest_distances, _ = tree.query(xy, k=2)
        radius = float(np.median(nearest_distances[:, 1]) * 1.8)
    pairs = tree.query_pairs(radius, output_type="ndarray")
    x = values.to_numpy(dtype=float)
    centered = x - x.mean()
    denominator = np.sum(centered**2)
    if denominator == 0 or len(pairs) == 0:
        return float("nan")
    numerator = 2.0 * np.sum(centered[pairs[:, 0]] * centered[pairs[:, 1]])
    weight_sum = 2.0 * len(pairs)
    return float((len(x) / weight_sum) * (numerator / denominator))
