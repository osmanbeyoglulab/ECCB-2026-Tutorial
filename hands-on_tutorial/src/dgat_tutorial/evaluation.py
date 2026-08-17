"""Evaluation metrics aligned with the published DGAT reporting emphasis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dgat_tutorial.alignment import require_exact_identifiers


def alignment_report(observed: pd.DataFrame, predicted: pd.DataFrame) -> dict[str, object]:
    """Report every missing/extra spot and protein ID before evaluation."""

    spots_only_obs = [str(i) for i in observed.index.difference(predicted.index)]
    spots_only_pred = [str(i) for i in predicted.index.difference(observed.index)]
    proteins_only_obs = [str(p) for p in observed.columns.difference(predicted.columns)]
    proteins_only_pred = [str(p) for p in predicted.columns.difference(observed.columns)]
    common_spots = list(observed.index.intersection(predicted.index))
    common_proteins = [str(p) for p in observed.columns.intersection(predicted.columns)]
    return {
        "n_common_spots": len(common_spots),
        "n_common_proteins": len(common_proteins),
        "spots_only_in_observed": spots_only_obs,
        "spots_only_in_predicted": spots_only_pred,
        "proteins_only_in_observed": proteins_only_obs,
        "proteins_only_in_predicted": proteins_only_pred,
        "proteins_evaluated": common_proteins,
    }


def _aligned_observation_tables(
    observed: pd.DataFrame,
    predicted: pd.DataFrame,
    *,
    require_exact_spots: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, object]]:
    """Align observed and predicted tables and always surface ID mismatches."""

    report = alignment_report(observed, predicted)
    if require_exact_spots:
        require_exact_identifiers(
            observed.index,
            predicted.index,
            left_name="observed spots",
            right_name="predicted spots",
        )
    if report["n_common_spots"] == 0:
        raise ValueError("Observed and predicted protein tables have no shared spot/cell IDs.")
    if report["n_common_proteins"] == 0:
        raise ValueError(
            "Observed and predicted protein tables have no shared protein names. "
            "Confirm that ADT labels were normalized to the DGAT decoder gene-symbol convention."
        )
    proteins = list(report["proteins_evaluated"])
    spot_index = observed.index.intersection(predicted.index)
    observed_aligned = observed.loc[spot_index, proteins]
    predicted_aligned = predicted.loc[spot_index, proteins]
    return observed_aligned, predicted_aligned, proteins, report


def protein_correlations(
    observed: pd.DataFrame,
    predicted: pd.DataFrame,
    *,
    require_exact_spots: bool = False,
) -> pd.DataFrame:
    """Compute per-protein Spearman, Pearson, and RMSE (DGAT-style pointwise metrics)."""

    observed_aligned, predicted_aligned, proteins, panel_report = _aligned_observation_tables(
        observed, predicted, require_exact_spots=require_exact_spots
    )
    print(
        "Alignment report before evaluation: "
        f"common_spots={panel_report['n_common_spots']}, "
        f"common_proteins={panel_report['n_common_proteins']}, "
        f"spots_only_observed={len(panel_report['spots_only_in_observed'])}, "
        f"spots_only_predicted={len(panel_report['spots_only_in_predicted'])}, "
        f"proteins_only_observed={panel_report['proteins_only_in_observed']}, "
        f"proteins_only_predicted={panel_report['proteins_only_in_predicted']}"
    )
    rows = []
    for protein in proteins:
        y_true = observed_aligned[protein].to_numpy(dtype=float)
        y_pred = predicted_aligned[protein].to_numpy(dtype=float)
        y_true_s = pd.Series(y_true)
        y_pred_s = pd.Series(y_pred)
        y_true_rank = y_true_s.rank(method="average")
        y_pred_rank = y_pred_s.rank(method="average")
        residual = y_pred - y_true
        rows.append(
            {
                "protein": protein,
                "spearman": float(y_true_rank.corr(y_pred_rank, method="pearson")),
                "pearson": float(y_true_s.corr(y_pred_s, method="pearson")),
                "rmse": float(np.sqrt(np.mean(residual**2))),
            }
        )
    return pd.DataFrame(rows).sort_values("spearman", ascending=False)


def corresponding_rna_baseline(
    transcripts: pd.DataFrame,
    observed_proteins: pd.DataFrame,
) -> pd.DataFrame:
    """Build a corresponding-RNA baseline by matching protein names to RNA genes when present."""

    require_exact_identifiers(
        transcripts.index,
        observed_proteins.index,
        left_name="transcript spots",
        right_name="observed protein spots",
    )
    columns = {}
    for protein in observed_proteins.columns:
        gene = str(protein)
        if gene in transcripts.columns:
            columns[protein] = transcripts[gene]
        else:
            base = gene.split("_")[0]
            if base in transcripts.columns:
                columns[protein] = transcripts[base]
    if not columns:
        raise ValueError("No corresponding RNA genes were found for the observed protein panel.")
    return pd.DataFrame(columns, index=observed_proteins.index)


def spatial_weights(coordinates: pd.DataFrame, radius: float | None = None) -> np.ndarray:
    """Build a binary spatial-neighborhood matrix."""

    from scipy.spatial import cKDTree

    xy = coordinates[["x", "y"]].to_numpy(dtype=float)
    tree = cKDTree(xy)
    if radius is None:
        nearest_distances, _ = tree.query(xy, k=2)
        radius = float(np.median(nearest_distances[:, 1]) * 1.8)
    pairs = tree.query_pairs(radius, output_type="ndarray")
    weights = np.zeros((len(xy), len(xy)), dtype=float)
    if len(pairs):
        weights[pairs[:, 0], pairs[:, 1]] = 1.0
        weights[pairs[:, 1], pairs[:, 0]] = 1.0
    return weights


def symmetric_knn_weights(coordinates: pd.DataFrame, n_neighbors: int = 6):
    """Build one symmetric binary kNN matrix shared by all tutorial Moran analyses."""

    xy = coordinates[["x", "y"]].to_numpy(dtype=float)
    if len(xy) < 2:
        raise ValueError("At least two spots are required.")
    if n_neighbors <= 0:
        raise ValueError("n_neighbors must be positive.")
    k = min(n_neighbors + 1, len(xy))
    distance_squared = ((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
    indices_with_self = np.argsort(distance_squared, axis=1, kind="stable")[:, :k]
    indices = np.stack([row[row != spot][:n_neighbors] for spot, row in enumerate(indices_with_self)])
    rows = np.repeat(np.arange(len(xy)), indices.shape[1])
    cols = indices.reshape(-1)
    weights = np.zeros((len(xy), len(xy)), dtype=np.uint8)
    weights[rows, cols] = 1
    return np.maximum(weights, weights.T)


def morans_i_from_weights(values: pd.Series, weights: np.ndarray) -> float:
    """Compute global Moran's I with an explicit, reusable weight matrix."""

    x = values.to_numpy(dtype=float)
    if weights.shape != (len(x), len(x)):
        raise ValueError("weights shape must match the number of values.")
    centered = x - x.mean()
    denominator = float(centered @ centered)
    weight_sum = float(weights.sum())
    if denominator == 0.0 or weight_sum == 0.0:
        return float("nan")
    return float((len(x) / weight_sum) * ((centered @ (weights @ centered)) / denominator))


def bivariate_morans_i_from_weights(
    values_a: pd.Series, values_b: pd.Series, weights: np.ndarray
) -> float:
    """Compute symmetric bivariate Moran's I using one explicit spatial graph."""

    a = values_a.to_numpy(dtype=float)
    b = values_b.to_numpy(dtype=float)
    if len(a) != len(b) or weights.shape != (len(a), len(a)):
        raise ValueError("Aligned values and a matching square weight matrix are required.")
    a = a - a.mean()
    b = b - b.mean()
    denominator = float(np.sqrt((a @ a) * (b @ b)))
    weight_sum = float(weights.sum())
    if denominator == 0.0 or weight_sum == 0.0:
        return float("nan")
    forward = float(a @ (weights @ b))
    reverse = float(b @ (weights @ a))
    return float((len(a) / weight_sum) * ((forward + reverse) / (2.0 * denominator)))


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


def bivariate_morans_i(
    values_a: pd.Series,
    values_b: pd.Series,
    coordinates: pd.DataFrame,
    radius: float | None = None,
) -> float:
    """Compute a simple bivariate Moran's I between two aligned spatial features."""

    from scipy.spatial import cKDTree

    common = values_a.index.intersection(values_b.index)
    aligned = coordinates.loc[common]
    xy = aligned[["x", "y"]].to_numpy(dtype=float)
    tree = cKDTree(xy)
    if radius is None:
        nearest_distances, _ = tree.query(xy, k=2)
        radius = float(np.median(nearest_distances[:, 1]) * 1.8)
    pairs = tree.query_pairs(radius, output_type="ndarray")
    a = values_a.loc[common].to_numpy(dtype=float)
    b = values_b.loc[common].to_numpy(dtype=float)
    a_c = a - a.mean()
    b_c = b - b.mean()
    denominator = np.sqrt(np.sum(a_c**2) * np.sum(b_c**2))
    if denominator == 0 or len(pairs) == 0:
        return float("nan")
    numerator = np.sum(a_c[pairs[:, 0]] * b_c[pairs[:, 1]] + a_c[pairs[:, 1]] * b_c[pairs[:, 0]])
    weight_sum = 2.0 * len(pairs)
    return float((len(a) / weight_sum) * (numerator / denominator))


def residual_morans_i(
    observed: pd.Series,
    predicted: pd.Series,
    coordinates: pd.DataFrame,
    radius: float | None = None,
) -> float:
    """Moran's I of prediction residuals (predicted - observed)."""

    common = observed.index.intersection(predicted.index)
    residual = predicted.loc[common] - observed.loc[common]
    residual.name = "residual"
    return morans_i(residual, coordinates.loc[common], radius=radius)
