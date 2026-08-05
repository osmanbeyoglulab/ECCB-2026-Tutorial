from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProcessedSpatialOmics:
    """Raw and normalized modalities kept together for a transparent tutorial handoff."""

    spots: pd.DataFrame
    raw_transcripts: pd.DataFrame
    raw_proteins: pd.DataFrame
    normalized_transcripts: pd.DataFrame
    normalized_proteins: pd.DataFrame
    qc: pd.DataFrame


def validate_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
) -> None:
    """Fail early when identifiers, coordinates, or measurement values are invalid."""

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("Spatial metadata must include x and y coordinates.")
    for label, table in (("spots", spots), ("transcripts", transcripts), ("proteins", proteins)):
        if table.index.has_duplicates:
            raise ValueError(f"{label} contains duplicate observation IDs.")
        if table.empty:
            raise ValueError(f"{label} is empty.")
    if not spots.index.equals(transcripts.index) or not spots.index.equals(proteins.index):
        raise ValueError("Spots, transcripts, and proteins must have identical ordered observation IDs.")
    for label, table in (("transcripts", transcripts), ("proteins", proteins)):
        values = table.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"{label} contains NaN or infinite values.")
        if (values < 0).any():
            raise ValueError(f"{label} contains negative values; expected non-negative abundance values.")


def calculate_qc_metrics(transcripts: pd.DataFrame, proteins: pd.DataFrame) -> pd.DataFrame:
    """Calculate spot-level RNA and protein quality-control metrics."""

    return pd.DataFrame(
        {
            "rna_total": transcripts.sum(axis=1),
            "genes_detected": (transcripts > 0).sum(axis=1),
            "protein_total": proteins.sum(axis=1),
            "proteins_detected": (proteins > 0).sum(axis=1),
        },
        index=transcripts.index,
    )


def choose_qc_thresholds(qc: pd.DataFrame, lower_quantile: float = 0.01) -> dict[str, float]:
    """Return data-adaptive teaching thresholds; inspect plots before accepting them."""

    if not 0 <= lower_quantile < 0.5:
        raise ValueError("lower_quantile must be between 0 and 0.5.")
    return {
        "min_rna_total": float(qc["rna_total"].quantile(lower_quantile)),
        "min_genes_detected": float(qc["genes_detected"].quantile(lower_quantile)),
        "min_protein_total": float(qc["protein_total"].quantile(lower_quantile)),
        "min_proteins_detected": float(qc["proteins_detected"].quantile(lower_quantile)),
    }


def filter_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    thresholds: dict[str, float],
    *,
    min_spots_per_gene: int = 1,
    min_spots_per_protein: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Filter low-quality observations and rarely detected features in both modalities."""

    qc = calculate_qc_metrics(transcripts, proteins)
    keep_spots = (
        (qc["rna_total"] >= thresholds["min_rna_total"])
        & (qc["genes_detected"] >= thresholds["min_genes_detected"])
        & (qc["protein_total"] >= thresholds["min_protein_total"])
        & (qc["proteins_detected"] >= thresholds["min_proteins_detected"])
    )
    kept_ids = qc.index[keep_spots]
    filtered_transcripts = transcripts.loc[kept_ids]
    filtered_proteins = proteins.loc[kept_ids]
    keep_genes = (filtered_transcripts > 0).sum(axis=0) >= min_spots_per_gene
    keep_proteins = (filtered_proteins > 0).sum(axis=0) >= min_spots_per_protein
    return (
        spots.loc[kept_ids].copy(),
        filtered_transcripts.loc[:, keep_genes].copy(),
        filtered_proteins.loc[:, keep_proteins].copy(),
        keep_spots,
    )


def normalize_total_log1p(matrix: pd.DataFrame, target_sum: float = 10_000.0) -> pd.DataFrame:
    """Library-size normalize every spot to ``target_sum`` and apply log(1+x)."""

    library_size = matrix.sum(axis=1).replace(0, np.nan)
    normalized = matrix.div(library_size, axis=0).mul(target_sum)
    normalized = np.log1p(normalized).fillna(0.0)
    return pd.DataFrame(normalized, index=matrix.index, columns=matrix.columns)


def clr_normalize(matrix: pd.DataFrame) -> pd.DataFrame:
    """Centered log-ratio normalization for non-negative ADT/protein abundances."""

    logged = np.log1p(matrix.astype(float))
    return logged.sub(logged.mean(axis=1), axis=0)


def process_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    *,
    lower_quantile: float = 0.01,
    rna_target_sum: float = 10_000.0,
) -> ProcessedSpatialOmics:
    """Validate, filter, and normalize paired spatial RNA and protein data."""

    validate_modalities(spots, transcripts, proteins)
    raw_qc = calculate_qc_metrics(transcripts, proteins)
    thresholds = choose_qc_thresholds(raw_qc, lower_quantile=lower_quantile)
    filtered_spots, filtered_transcripts, filtered_proteins, _ = filter_modalities(
        spots, transcripts, proteins, thresholds
    )
    filtered_qc = calculate_qc_metrics(filtered_transcripts, filtered_proteins)
    return ProcessedSpatialOmics(
        spots=filtered_spots,
        raw_transcripts=filtered_transcripts,
        raw_proteins=filtered_proteins,
        normalized_transcripts=normalize_total_log1p(filtered_transcripts, target_sum=rna_target_sum),
        normalized_proteins=clr_normalize(filtered_proteins),
        qc=filtered_qc,
    )


def knn_edge_index(coordinates: pd.DataFrame, n_neighbors: int = 6) -> np.ndarray:
    """Build the directed 2 x E edge-index array consumed by graph neural networks."""

    xy = coordinates[["x", "y"]].to_numpy(dtype=float)
    if len(xy) < 2:
        raise ValueError("At least two observations are required to construct a graph.")
    k = min(n_neighbors + 1, len(xy))
    squared_distances = ((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
    indices = np.argsort(squared_distances, axis=1, kind="stable")[:, :k]
    sources = np.repeat(np.arange(len(xy)), k - 1)
    targets = indices[:, 1:].reshape(-1)
    return np.vstack([sources, targets]).astype(np.int64)
