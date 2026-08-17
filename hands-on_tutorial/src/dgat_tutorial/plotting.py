from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


def plot_spatial_feature(
    spots: pd.DataFrame,
    values: pd.Series,
    title: str,
    cmap: str = "viridis",
    ax: plt.Axes | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    add_colorbar: bool = True,
) -> plt.Axes:
    """Scatter a molecular feature over spatial coordinates."""

    if ax is None:
        _, ax = plt.subplots(figsize=(5, 4))
    aligned = values.loc[spots.index]
    scatter = ax.scatter(
        spots["x"],
        spots["y"],
        c=aligned,
        s=28,
        cmap=cmap,
        edgecolor="none",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_title(title)
    ax.set_xlabel("Tissue x coordinate")
    ax.set_ylabel("Tissue y coordinate")
    ax.set_aspect("equal")
    if add_colorbar:
        plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    return ax


def _undirected_edge_pairs(edge_index: np.ndarray) -> np.ndarray:
    """Collapse a directed edge index to unique undirected endpoint pairs."""

    pairs = np.sort(np.asarray(edge_index, dtype=int).T, axis=1)
    return np.unique(pairs, axis=0)


def _choose_zoom_window(
    xy: np.ndarray,
    *,
    target_nodes: int = 70,
    corner: str = "lower_left",
) -> tuple[float, float, float, float, np.ndarray]:
    """Pick a compact window at a tissue corner or other boundary special case.

    Interior zooms mostly show a regular hexagonal mesh. Corner/edge regions make the
    kNN construction more instructive: neighborhoods become asymmetric and some spots
    have all six neighbors on one side of the tissue outline.

    Returns
    -------
    x0, x1, y0, y1, tip
        Axis-aligned window and the corner tip used to seed it.
    """

    n_spots = len(xy)
    if n_spots == 0:
        raise ValueError("Cannot choose a zoom window for an empty coordinate array.")

    x_min, y_min = xy.min(axis=0)
    x_max, y_max = xy.max(axis=0)
    corners = {
        "lower_left": np.array([x_min, y_min], dtype=float),
        "lower_right": np.array([x_max, y_min], dtype=float),
        "upper_left": np.array([x_min, y_max], dtype=float),
        "upper_right": np.array([x_max, y_max], dtype=float),
    }
    if corner == "auto":
        # Prefer the corner whose nearest spots are closest to the bounding-box tip.
        best_name = "lower_left"
        best_score = np.inf
        for name, candidate_tip in corners.items():
            nearest = np.partition(np.linalg.norm(xy - candidate_tip, axis=1), min(19, n_spots - 1))[
                : min(20, n_spots)
            ]
            score = float(nearest.mean())
            if score < best_score:
                best_score = score
                best_name = name
        corner = best_name
    if corner not in corners:
        raise ValueError(f"Unsupported corner={corner!r}; expected one of {sorted(corners)} or 'auto'.")

    tip = corners[corner]
    seed = int(np.argmin(np.linalg.norm(xy - tip, axis=1)))
    seed_xy = xy[seed]

    span = max(float(np.ptp(xy[:, 0])), float(np.ptp(xy[:, 1])), 1.0)
    half = max(span * 0.03, 1.0)
    x0 = y0 = x1 = y1 = 0.0
    for _ in range(24):
        x0, x1 = seed_xy[0] - half, seed_xy[0] + half
        y0, y1 = seed_xy[1] - half, seed_xy[1] + half
        mask = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
        count = int(mask.sum())
        if count >= target_nodes or half >= span:
            break
        half *= 1.35
    return float(x0), float(x1), float(y0), float(y1), tip


def plot_spatial_knn_graph(
    spots: pd.DataFrame,
    edge_index: np.ndarray,
    *,
    n_neighbors: int = 6,
    target_zoom_nodes: int = 70,
    zoom_corner: str = "auto",
) -> tuple[plt.Figure, np.ndarray]:
    """Show the tissue-wide node layout and a zoomed corner/edge kNN neighborhood.

    Drawing every edge over thousands of spots hides the graph structure. The overview
    panel therefore shows only the nodes (tissue coverage), while the zoom panel draws
    undirected edges at a tissue corner so participants can see asymmetric neighborhoods
    that arise at the boundary. One example boundary spot and its neighbors are highlighted.
    """

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("spots must contain x and y columns.")
    xy = spots[["x", "y"]].to_numpy(dtype=float)
    directed = np.asarray(edge_index, dtype=int)
    undirected = _undirected_edge_pairs(directed)
    x0, x1, y0, y1, tip = _choose_zoom_window(
        xy, target_nodes=target_zoom_nodes, corner=zoom_corner
    )
    in_zoom = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
    zoom_idx = np.flatnonzero(in_zoom)
    if zoom_idx.size == 0:
        raise ValueError("Zoom window contains no spots.")

    # Highlight the actual corner tip spot; its six neighbors all lie inward.
    example = int(zoom_idx[np.argmin(np.linalg.norm(xy[zoom_idx] - tip, axis=1))])
    example_neighbors = directed[1, directed[0] == example]

    # Keep the corner framing, but expand just enough to show the full example neighborhood.
    focus_idx = np.unique(np.concatenate([zoom_idx, example_neighbors, np.asarray([example])]))
    pad = 0.08 * max(float(np.ptp(xy[focus_idx, 0])), float(np.ptp(xy[focus_idx, 1])), 1.0)
    view_x0 = float(xy[focus_idx, 0].min() - pad)
    view_x1 = float(xy[focus_idx, 0].max() + pad)
    view_y0 = float(xy[focus_idx, 1].min() - pad)
    view_y1 = float(xy[focus_idx, 1].max() + pad)
    in_view = (
        (xy[:, 0] >= view_x0)
        & (xy[:, 0] <= view_x1)
        & (xy[:, 1] >= view_y0)
        & (xy[:, 1] <= view_y1)
    )
    view_edges = undirected[in_view[undirected[:, 0]] & in_view[undirected[:, 1]]]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    axes[0].scatter(xy[:, 0], xy[:, 1], s=4, color="#24527a", alpha=0.55, linewidths=0, zorder=2)
    axes[0].add_patch(
        Rectangle(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            fill=False,
            edgecolor="#c44e52",
            linewidth=1.6,
            zorder=3,
        )
    )
    axes[0].set(
        title=f"Tissue overview ({len(spots)} nodes)",
        xlabel="x",
        ylabel="y",
        aspect="equal",
    )
    axes[0].text(
        0.02,
        0.98,
        "Corner zoom →",
        transform=axes[0].transAxes,
        va="top",
        ha="left",
        color="#c44e52",
        fontsize=9,
    )

    if view_edges.size:
        starts = xy[view_edges[:, 0]]
        ends = xy[view_edges[:, 1]]
        segments = np.concatenate(
            [starts[:, None, :], ends[:, None, :], np.full((len(view_edges), 1, 2), np.nan)],
            axis=1,
        ).reshape(-1, 2)
        axes[1].plot(
            segments[:, 0],
            segments[:, 1],
            color="#b0b0b0",
            linewidth=0.7,
            alpha=0.75,
            solid_capstyle="round",
            zorder=1,
        )

    axes[1].scatter(
        xy[in_view, 0],
        xy[in_view, 1],
        s=36,
        color="#24527a",
        edgecolors="white",
        linewidths=0.45,
        zorder=2,
    )
    if example_neighbors.size:
        for neighbor in example_neighbors:
            axes[1].plot(
                [xy[example, 0], xy[neighbor, 0]],
                [xy[example, 1], xy[neighbor, 1]],
                color="#c44e52",
                linewidth=2.0,
                zorder=3,
            )
        axes[1].scatter(
            xy[example_neighbors, 0],
            xy[example_neighbors, 1],
            s=55,
            color="#f0a202",
            edgecolors="white",
            linewidths=0.6,
            zorder=4,
        )
    axes[1].scatter(
        xy[example, 0],
        xy[example, 1],
        s=90,
        color="#c44e52",
        edgecolors="white",
        linewidths=0.8,
        zorder=5,
    )
    axes[1].set(
        title=f"Corner {n_neighbors}-NN neighborhood ({int(in_view.sum())} nodes)",
        xlabel="x",
        ylabel="y",
        aspect="equal",
        xlim=(view_x0, view_x1),
        ylim=(view_y0, view_y1),
    )
    axes[1].text(
        0.02,
        0.02,
        f"{len(view_edges)} undirected edges in view",
        transform=axes[1].transAxes,
        va="bottom",
        ha="left",
        fontsize=9,
        color="#444444",
    )

    fig.suptitle(
        f"Spatial {n_neighbors}-nearest-neighbor graph for the graph encoder",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    return fig, axes


def plot_spatial_molecular_neighborhoods(
    spots: pd.DataFrame,
    spatial_edge_index: np.ndarray,
    rna_molecular_edge_index: np.ndarray,
    protein_molecular_edge_index: np.ndarray,
    *,
    focal_index: int | None = None,
    focal_corner: str = "lower_left",
) -> tuple[plt.Figure, np.ndarray]:
    """Compare one spot's spatial, RNA, and protein neighborhoods on the tissue.

    All three panels use the same focal node and coordinate limits. Self-loops are
    omitted from the highlighted sets so each colored node represents another spot
    linked to the focal spot through the corresponding directed graph.
    """

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("spots must contain x and y columns.")
    xy = spots[["x", "y"]].to_numpy(dtype=float)
    if len(xy) == 0:
        raise ValueError("Cannot plot neighborhoods for an empty spot table.")

    if focal_index is None:
        _, _, _, _, tip = _choose_zoom_window(xy, target_nodes=70, corner=focal_corner)
        focal_index = int(np.argmin(np.linalg.norm(xy - tip, axis=1)))
    if not 0 <= focal_index < len(xy):
        raise IndexError(f"focal_index={focal_index} is outside 0..{len(xy) - 1}.")

    def outgoing_neighbors(edge_index: np.ndarray) -> np.ndarray:
        directed = np.asarray(edge_index, dtype=int)
        if directed.ndim != 2 or directed.shape[0] != 2:
            raise ValueError("Each edge_index must have shape (2, number_of_edges).")
        neighbors = directed[1, directed[0] == focal_index]
        return np.unique(neighbors[neighbors != focal_index])

    panels = [
        ("Spatial neighborhood", spatial_edge_index, "#f0a202"),
        ("RNA molecular neighborhood", rna_molecular_edge_index, "#4c78a8"),
        ("Protein molecular neighborhood", protein_molecular_edge_index, "#59a14f"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharex=True, sharey=True)
    for ax, (title, panel_edges, neighbor_color) in zip(axes, panels):
        neighbors = outgoing_neighbors(panel_edges)
        ax.scatter(
            xy[:, 0],
            xy[:, 1],
            s=7,
            color="#c7c7c7",
            alpha=0.45,
            linewidths=0,
            zorder=1,
        )
        for neighbor in neighbors:
            ax.plot(
                [xy[focal_index, 0], xy[neighbor, 0]],
                [xy[focal_index, 1], xy[neighbor, 1]],
                color=neighbor_color,
                linewidth=1.35,
                alpha=0.8,
                zorder=2,
            )
        if neighbors.size:
            ax.scatter(
                xy[neighbors, 0],
                xy[neighbors, 1],
                s=48,
                color=neighbor_color,
                edgecolors="white",
                linewidths=0.65,
                zorder=3,
            )
        ax.scatter(
            xy[focal_index, 0],
            xy[focal_index, 1],
            s=95,
            color="#c44e52",
            edgecolors="white",
            linewidths=0.9,
            zorder=4,
        )
        ax.set(
            title=f"{title}\n({len(neighbors)} other spots)",
            xlabel="Tissue x coordinate",
            aspect="equal",
        )

    axes[0].set_ylabel("Tissue y coordinate")
    focal_label = str(spots.index[focal_index])
    fig.suptitle(
        f"One focal spot across DGAT neighborhood components: {focal_label}",
        y=1.02,
        fontsize=12,
    )
    fig.legend(
        handles=[
            Line2D(
                [0], [0], marker="o", color="none", markerfacecolor="#c44e52",
                markeredgecolor="white", markersize=9, label="same focal spot",
            ),
            Line2D(
                [0], [0], marker="o", color="#f0a202", markerfacecolor="#f0a202",
                markersize=7, label="spatial neighbor",
            ),
            Line2D(
                [0], [0], marker="o", color="#4c78a8", markerfacecolor="#4c78a8",
                markersize=7, label="RNA neighbor",
            ),
            Line2D(
                [0], [0], marker="o", color="#59a14f", markerfacecolor="#59a14f",
                markersize=7, label="protein neighbor",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.01),
        ncol=4,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig, axes


def plot_correlation_bar(correlations: pd.DataFrame, metric: str = "spearman") -> plt.Axes:
    """Plot per-protein correlation or error scores with readable protein labels."""

    if metric not in correlations.columns:
        raise ValueError(f"Metric {metric!r} not found in correlations table.")
    ascending = metric.lower() == "rmse"
    ordered = correlations.sort_values(metric, ascending=ascending)
    n_proteins = len(ordered)
    # Grow with the number of proteins so y-tick labels do not stack into a dense wall.
    height = max(4.5, 0.32 * n_proteins)
    _, ax = plt.subplots(figsize=(7.5, height))
    ax.barh(ordered["protein"], ordered[metric], color="#3b7a78", height=0.7)
    if metric.lower() != "rmse":
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlim(-1, 1)
    ax.set_xlabel(metric.replace("_", " ").title())
    # Tick labels already name each protein; a separate "Protein" axis title adds clutter.
    ax.set_ylabel("")
    ax.set_title("Observed vs inferred protein expression")
    ax.tick_params(axis="y", labelsize=8, length=0, pad=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    return ax


def plot_qc_overview(qc: pd.DataFrame) -> tuple[plt.Figure, np.ndarray]:
    """Plot separate RNA and protein QC distributions for spot-level threshold selection."""

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    panels = [
        ("rna_total", "RNA library size", "#30343f"),
        ("genes_detected", "Genes detected per spot", "#4c78a8"),
        ("protein_total", "Total protein signal", "#b65f3c"),
        ("proteins_detected", "Proteins detected per spot", "#72a06a"),
    ]
    for ax, (column, title, color) in zip(axes.ravel(), panels):
        ax.hist(qc[column], bins=30, color=color, edgecolor="white", linewidth=0.4)
        ax.axvline(qc[column].median(), color="black", linestyle="--", linewidth=1, label="median")
        ax.set_title(title)
        ax.set_xlabel(column.replace("_", " "))
        ax.set_ylabel("spots")
    axes[0, 0].legend(frameon=False)
    fig.suptitle("Data QC: inspect RNA and protein modalities separately", y=1.02)
    fig.tight_layout()
    return fig, axes


def plot_raw_vs_normalized(
    raw: pd.DataFrame,
    normalized: pd.DataFrame,
    feature_name: str,
    modality: str,
) -> tuple[plt.Figure, np.ndarray]:
    """Make normalization effects visible instead of treating processing as a hidden step."""

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].hist(raw[feature_name], bins=30, color="#8c8c8c")
    axes[0].set_title(f"Raw {modality}: {feature_name}")
    axes[1].hist(normalized[feature_name], bins=30, color="#3977a3")
    axes[1].set_title(f"Normalized {modality}: {feature_name}")
    for ax in axes:
        ax.set_xlabel("abundance")
        ax.set_ylabel("spots")
    fig.tight_layout()
    return fig, axes
