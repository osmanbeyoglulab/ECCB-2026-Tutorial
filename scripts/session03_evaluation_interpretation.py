from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dgat_tutorial.data import find_dgat_h5ad, load_tutorial_data
from dgat_tutorial.dgat import run_demo_dgat_inference
from dgat_tutorial.evaluation import morans_i, protein_correlations
from dgat_tutorial.plotting import plot_correlation_bar, plot_spatial_feature


def main() -> None:
    parser = argparse.ArgumentParser(description="Session 3: evaluate spatial protein predictions.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--allow-demo", action="store_true", help="Use synthetic fallback data if no DGAT .h5ad is found.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = args.output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    dgat_h5ad = find_dgat_h5ad(args.data_dir)
    dataset = load_tutorial_data(args.data_dir, allow_demo=args.allow_demo)
    print(f"Loaded DGAT AnnData file: {dgat_h5ad}" if dgat_h5ad else "Loaded synthetic fallback data")

    spots = dataset.spots
    transcripts = dataset.transcripts
    proteins = dataset.proteins

    prediction_path = args.processed_dir / "predicted_proteins.csv"
    if prediction_path.exists():
        predicted_proteins = pd.read_csv(prediction_path, index_col=0)
    else:
        predicted_proteins = run_demo_dgat_inference(transcripts, proteins)

    common_spots = spots.index.intersection(proteins.index).intersection(predicted_proteins.index)
    spots = spots.loc[common_spots]
    proteins = proteins.loc[common_spots]
    transcripts = transcripts.loc[common_spots]
    predicted_proteins = predicted_proteins.loc[common_spots]

    correlations = protein_correlations(proteins, predicted_proteins)
    correlations.to_csv(args.output_dir / "session03_prediction_correlations.csv", index=False)

    plot_correlation_bar(correlations, metric="pearson")
    plt.tight_layout()
    plt.savefig(fig_dir / "session03_prediction_correlations.png", dpi=160)
    plt.close()

    moran_rows = []
    for protein in predicted_proteins.columns:
        moran_rows.append(
            {
                "protein": protein,
                "observed_morans_i": morans_i(proteins[protein], spots),
                "predicted_morans_i": morans_i(predicted_proteins[protein], spots),
            }
        )
    moran_table = pd.DataFrame(moran_rows)
    moran_table.to_csv(args.output_dir / "session03_morans_i.csv", index=False)

    sns.scatterplot(data=moran_table, x="observed_morans_i", y="predicted_morans_i", hue="protein", s=80)
    plt.axline((0, 0), slope=1, color="black", linewidth=0.8)
    plt.title("Observed vs predicted spatial coherence")
    plt.tight_layout()
    plt.savefig(fig_dir / "session03_morans_i.png", dpi=160)
    plt.close()

    protein = correlations.iloc[0]["protein"]
    gene = transcripts.columns[0]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    plot_spatial_feature(spots, transcripts[gene], f"Transcript {gene}", cmap="magma", ax=axes[0])
    plot_spatial_feature(spots, proteins[protein], f"Observed {protein}", cmap="viridis", ax=axes[1])
    plot_spatial_feature(spots, predicted_proteins[protein], f"Predicted {protein}", cmap="viridis", ax=axes[2])
    plt.tight_layout()
    plt.savefig(fig_dir / "session03_landscape_comparison.png", dpi=160)
    plt.close(fig)

    print(correlations.to_string(index=False))
    print(f"Wrote Session 3 outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
