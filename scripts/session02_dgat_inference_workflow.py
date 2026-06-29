from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from dgat_tutorial.data import find_dgat_h5ad, find_dgat_h5ad_pair, load_tutorial_data
from dgat_tutorial.dgat import load_prediction_table, run_demo_dgat_inference
from dgat_tutorial.plotting import plot_spatial_feature


def main() -> None:
    parser = argparse.ArgumentParser(description="Session 2: DGAT protein inference workflow.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--predictions", type=Path, default=None, help="Optional precomputed DGAT prediction CSV/TSV.")
    parser.add_argument("--allow-demo", action="store_true", help="Use synthetic fallback data if no DGAT .h5ad is found.")
    args = parser.parse_args()

    args.processed_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = args.output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    dgat_h5ad_pair = find_dgat_h5ad_pair(args.data_dir)
    dgat_h5ad = find_dgat_h5ad(args.data_dir)
    dataset = load_tutorial_data(args.data_dir, allow_demo=args.allow_demo)
    if dgat_h5ad_pair:
        print(f"Loaded DGAT AnnData files: RNA={dgat_h5ad_pair[0]}, ADT={dgat_h5ad_pair[1]}")
    else:
        print(f"Loaded DGAT AnnData file: {dgat_h5ad}" if dgat_h5ad else "Loaded synthetic fallback data")

    spots = dataset.spots
    transcripts = dataset.transcripts
    proteins = dataset.proteins
    common_spots = spots.index.intersection(transcripts.index).intersection(proteins.index)
    spots = spots.loc[common_spots]
    transcripts = transcripts.loc[common_spots]
    proteins = proteins.loc[common_spots]

    prediction_path = args.predictions or args.data_dir / "dgat_predictions.csv"
    if prediction_path.exists():
        predicted_proteins = load_prediction_table(str(prediction_path))
        print(f"Loaded precomputed DGAT predictions: {prediction_path}")
    else:
        predicted_proteins = run_demo_dgat_inference(transcripts, proteins)
        print("Generated demo DGAT-like predictions because no prediction table was found.")

    predicted_proteins.to_csv(args.processed_dir / "predicted_proteins.csv")

    proteins_to_plot = list(predicted_proteins.columns[:4])
    n_cols = min(4, len(proteins_to_plot))
    fig, axes = plt.subplots(1, n_cols, figsize=(4 * n_cols, 4))
    if n_cols == 1:
        axes = [axes]
    for ax, protein in zip(axes, proteins_to_plot):
        plot_spatial_feature(spots, predicted_proteins[protein], f"Predicted {protein}", ax=ax)
    plt.tight_layout()
    plt.savefig(fig_dir / "session02_predicted_proteins.png", dpi=160)
    plt.close(fig)

    print(f"Wrote predictions to {args.processed_dir / 'predicted_proteins.csv'}")


if __name__ == "__main__":
    main()
