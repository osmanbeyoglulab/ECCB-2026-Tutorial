from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from dgat_tutorial.data import find_dgat_h5ad, find_dgat_h5ad_pair, load_tutorial_data
from dgat_tutorial.dgat import (
    load_prediction_table,
    load_prediction_metadata,
    run_demo_dgat_inference,
    run_official_dgat_prediction,
    write_prediction_artifact,
)
from dgat_tutorial.plotting import plot_spatial_feature


def main() -> None:
    parser = argparse.ArgumentParser(description="Session 2: DGAT protein inference workflow.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--predictions", type=Path, default=None, help="Optional precomputed DGAT prediction CSV/TSV.")
    parser.add_argument("--run-official-dgat", action="store_true", help="Run official DGAT protein_predict if no prediction table is found.")
    parser.add_argument(
        "--demo-baseline",
        action="store_true",
        help="Explicitly run the out-of-fold ridge baseline (not DGAT).",
    )
    parser.add_argument("--dgat-repo", type=Path, default=Path("external/DGAT"))
    parser.add_argument("--model-save-dir", type=Path, default=Path("external/DGAT_assets/DGAT_pretrained_models"))
    parser.add_argument("--pyg-data-dir", type=Path, default=Path("data/processed/dgat_pyg"))
    parser.add_argument("--common-gene", type=Path, default=None)
    parser.add_argument("--common-protein", type=Path, default=None)
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
    if args.run_official_dgat and args.demo_baseline:
        parser.error("Choose only one of --run-official-dgat and --demo-baseline.")

    if args.run_official_dgat:
        rna_h5ad = dgat_h5ad_pair[0] if dgat_h5ad_pair else dgat_h5ad
        if rna_h5ad is None:
            raise FileNotFoundError("Could not find RNA .h5ad for official DGAT prediction.")
        predicted_proteins = run_official_dgat_prediction(
            rna_h5ad_path=rna_h5ad,
            dgat_repo_dir=args.dgat_repo,
            model_save_dir=args.model_save_dir,
            pyg_data_dir=args.pyg_data_dir,
            common_gene_path=args.common_gene,
            common_protein_path=args.common_protein,
        )
        method = "official_dgat"
        source = str(rna_h5ad)
        evaluation_note = "Official pretrained DGAT inference."
        print("Generated predictions with official DGAT protein_predict.")
    elif args.demo_baseline:
        predicted_proteins = run_demo_dgat_inference(transcripts, proteins)
        method = "out_of_fold_ridge_baseline"
        source = "observed tutorial RNA/protein matrices"
        evaluation_note = "Not DGAT; each row is out-of-fold, so evaluation is not in-sample."
        print("Generated explicit out-of-fold ridge baseline (not DGAT).")
    elif prediction_path.exists():
        predicted_proteins = load_prediction_table(str(prediction_path))
        input_metadata = load_prediction_metadata(prediction_path)
        method = str(input_metadata["method"]) if input_metadata else "precomputed_dgat"
        source = str(input_metadata["source"]) if input_metadata else str(prediction_path)
        evaluation_note = (
            str(input_metadata["evaluation_note"])
            if input_metadata
            else "Evaluate only if this table was generated without fitting on the observed evaluation proteins."
        )
        print(f"Loaded precomputed DGAT predictions: {prediction_path}")
    else:
        raise FileNotFoundError(
            f"No precomputed DGAT prediction table found at {prediction_path}. "
            "Provide --predictions PATH, use --run-official-dgat in the separate Python 3.11 DGAT environment, "
            "or use --demo-baseline only for an explicitly labeled baseline."
        )

    output_path = args.processed_dir / "predicted_proteins.csv"
    write_prediction_artifact(
        predicted_proteins,
        output_path,
        method=method,
        source=source,
        evaluation_note=evaluation_note,
    )

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

    print(f"Wrote predictions and provenance to {output_path}")


if __name__ == "__main__":
    main()
