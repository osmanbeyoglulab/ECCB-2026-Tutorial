from __future__ import annotations

from pathlib import Path

from dgat_tutorial.data import load_demo_data
from dgat_tutorial.dgat import run_demo_dgat_inference
from dgat_tutorial.evaluation import protein_correlations


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    processed_dir = repo_root / "data" / "processed"
    results_dir = repo_root / "results"
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_demo_data()
    predictions = run_demo_dgat_inference(dataset.transcripts, dataset.proteins)
    correlations = protein_correlations(dataset.proteins, predictions)

    dataset.spots.to_csv(processed_dir / "demo_spots.csv")
    dataset.transcripts.to_csv(processed_dir / "demo_transcripts.csv")
    dataset.proteins.to_csv(processed_dir / "demo_observed_proteins.csv")
    predictions.to_csv(processed_dir / "predicted_proteins.csv")
    correlations.to_csv(results_dir / "demo_prediction_correlations.csv", index=False)

    print("Demo predictions written to data/processed/predicted_proteins.csv")
    print("Demo correlations written to results/demo_prediction_correlations.csv")
    print(correlations.to_string(index=False))


if __name__ == "__main__":
    main()
