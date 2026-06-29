from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dgat_tutorial.data import find_dgat_h5ad, load_tutorial_data
from dgat_tutorial.plotting import plot_spatial_feature


def summarize_features(matrix: pd.DataFrame, feature_type: str, n: int = 10) -> pd.DataFrame:
    numeric = matrix.select_dtypes(include=[np.number])
    summary = pd.DataFrame(
        {
            "feature": numeric.columns,
            "feature_type": feature_type,
            "mean": numeric.mean(axis=0).to_numpy(),
            "variance": numeric.var(axis=0).to_numpy(),
            "nonzero_fraction": (numeric > 0).mean(axis=0).to_numpy(),
        }
    )
    return summary.sort_values("variance", ascending=False).head(n)


def top_variable_features(matrix: pd.DataFrame, n: int = 3) -> list[str]:
    numeric = matrix.select_dtypes(include=[np.number])
    return numeric.var(axis=0).sort_values(ascending=False).head(n).index.tolist()


def main() -> None:
    parser = argparse.ArgumentParser(description="Session 1: spatial data exploration.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--allow-demo", action="store_true", help="Use synthetic fallback data if no DGAT .h5ad is found.")
    args = parser.parse_args()

    fig_dir = args.output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dgat_h5ad = find_dgat_h5ad(args.data_dir)
    dataset = load_tutorial_data(args.data_dir, allow_demo=args.allow_demo)
    print(f"Loaded DGAT AnnData file: {dgat_h5ad}" if dgat_h5ad else "Loaded synthetic fallback data")

    spots = dataset.spots
    transcripts = dataset.transcripts
    proteins = dataset.proteins

    transcript_values = transcripts.select_dtypes(include=[np.number])
    protein_values = proteins.select_dtypes(include=[np.number])
    transcript_library_size = transcript_values.sum(axis=1)
    detected_genes = (transcript_values > 0).sum(axis=1)
    protein_total = protein_values.sum(axis=1)
    detected_proteins = (protein_values > 0).sum(axis=1)

    dataset_summary = pd.DataFrame(
        {
            "spots": [len(spots)],
            "genes": [transcript_values.shape[1]],
            "proteins": [protein_values.shape[1]],
            "median_transcript_library_size": [transcript_library_size.median()],
            "median_detected_genes": [detected_genes.median()],
            "median_protein_total": [protein_total.median()],
            "median_detected_proteins": [detected_proteins.median()],
        }
    )
    dataset_summary.to_csv(args.output_dir / "session01_dataset_summary.csv", index=False)
    summarize_features(transcripts, "transcript").to_csv(args.output_dir / "session01_top_transcripts.csv", index=False)
    summarize_features(proteins, "protein").to_csv(args.output_dir / "session01_top_proteins.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.5))
    axes[0].hist(transcript_library_size, bins=30, color="#2f2f2f")
    axes[0].set_title("Transcript library size")
    axes[0].set_xlabel("Total transcript signal")
    axes[0].set_ylabel("Spots")
    axes[1].hist(detected_genes, bins=30, color="#5b7f95")
    axes[1].set_title("Detected genes per spot")
    axes[1].set_xlabel("Genes with value > 0")
    axes[2].hist(protein_total, bins=30, color="#b45a3c")
    axes[2].set_title("Protein signal per spot")
    axes[2].set_xlabel("Total protein signal")
    plt.tight_layout()
    plt.savefig(fig_dir / "session01_basic_statistics.png", dpi=160)
    plt.close(fig)

    transcript_features = top_variable_features(transcripts, n=3)
    protein_features = top_variable_features(proteins, n=3)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for row, (label, matrix, features, cmap) in enumerate(
        [("Transcript", transcripts, transcript_features, "magma"), ("Protein", proteins, protein_features, "viridis")]
    ):
        for col, feature in enumerate(features):
            plot_spatial_feature(spots, matrix[feature], f"{label}: {feature}", cmap=cmap, ax=axes[row, col])
    plt.tight_layout()
    plt.savefig(fig_dir / "session01_spatial_features.png", dpi=160)
    plt.close(fig)

    xy = spots[["x", "y"]].to_numpy()
    distance_matrix = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    neighbor_indices = np.argsort(distance_matrix, axis=1)[:, :7]
    distances = np.take_along_axis(distance_matrix, neighbor_indices, axis=1)
    neighbors = pd.DataFrame(
        {
            "spot_id": spots.index,
            "mean_neighbor_distance": distances[:, 1:].mean(axis=1),
            "nearest_neighbor": spots.index[neighbor_indices[:, 1]],
        }
    ).set_index("spot_id")
    neighbors.to_csv(args.output_dir / "session01_spatial_neighbors.csv")

    ax = spots.plot.scatter(x="x", y="y", c=neighbors["mean_neighbor_distance"], cmap="cividis", figsize=(5, 4))
    ax.set_title("Mean distance to 6 nearest neighbors")
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(fig_dir / "session01_neighborhood_distances.png", dpi=160)
    plt.close()

    print(dataset_summary.round(2).to_string(index=False))
    print(f"Wrote Session 1 outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
