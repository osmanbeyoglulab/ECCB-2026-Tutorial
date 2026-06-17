from __future__ import annotations

import numpy as np
import pandas as pd


def protein_correlations(observed: pd.DataFrame, predicted: pd.DataFrame) -> pd.DataFrame:
    """Compute per-protein Pearson and Spearman correlations."""

    common_spots = observed.index.intersection(predicted.index)
    common_proteins = observed.columns.intersection(predicted.columns)
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

    aligned_coordinates = coordinates.loc[values.index]
    weights = spatial_weights(aligned_coordinates, radius=radius)
    x = values.to_numpy(dtype=float)
    centered = x - x.mean()
    numerator = np.sum(weights * np.outer(centered, centered))
    denominator = np.sum(centered**2)
    if denominator == 0 or weights.sum() == 0:
        return float("nan")
    return float((len(x) / weights.sum()) * (numerator / denominator))
