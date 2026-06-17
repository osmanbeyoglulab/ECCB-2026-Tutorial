from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_spatial_feature(
    spots: pd.DataFrame,
    values: pd.Series,
    title: str,
    cmap: str = "viridis",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Scatter a molecular feature over spatial coordinates."""

    if ax is None:
        _, ax = plt.subplots(figsize=(5, 4))
    aligned = values.loc[spots.index]
    scatter = ax.scatter(spots["x"], spots["y"], c=aligned, s=28, cmap=cmap, edgecolor="none")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    return ax


def plot_correlation_bar(correlations: pd.DataFrame, metric: str = "pearson") -> plt.Axes:
    """Plot per-protein correlation scores."""

    _, ax = plt.subplots(figsize=(6, 3.5))
    ordered = correlations.sort_values(metric)
    ax.barh(ordered["protein"], ordered[metric], color="#3b7a78")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlim(-1, 1)
    ax.set_xlabel(f"{metric.title()} correlation")
    ax.set_ylabel("Protein")
    ax.set_title("Observed vs inferred protein expression")
    return ax
