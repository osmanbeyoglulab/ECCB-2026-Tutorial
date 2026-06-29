from __future__ import annotations

import argparse
from pathlib import Path

from dgat_tutorial.data import find_dgat_h5ad, find_dgat_h5ad_pair
from dgat_tutorial.dgat import run_official_dgat_prediction


def main() -> None:
    parser = argparse.ArgumentParser(description="Run official DGAT pretrained protein prediction.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--rna-h5ad", type=Path, default=None, help="RNA AnnData file. Defaults to downloaded DGAT RNA .h5ad.")
    parser.add_argument("--dgat-repo", type=Path, default=Path("external/DGAT"))
    parser.add_argument("--model-save-dir", type=Path, default=Path("external/DGAT_assets/DGAT_pretrained_models"))
    parser.add_argument("--pyg-data-dir", type=Path, default=Path("data/processed/dgat_pyg"))
    parser.add_argument("--common-gene", type=Path, default=None)
    parser.add_argument("--common-protein", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/processed/predicted_proteins.csv"))
    args = parser.parse_args()

    rna_h5ad = args.rna_h5ad
    if rna_h5ad is None:
        pair = find_dgat_h5ad_pair(args.data_dir)
        rna_h5ad = pair[0] if pair is not None else find_dgat_h5ad(args.data_dir)
    if rna_h5ad is None:
        raise FileNotFoundError("Could not find a DGAT RNA .h5ad file. Pass --rna-h5ad explicitly.")

    predictions = run_official_dgat_prediction(
        rna_h5ad_path=rna_h5ad,
        dgat_repo_dir=args.dgat_repo,
        model_save_dir=args.model_save_dir,
        pyg_data_dir=args.pyg_data_dir,
        common_gene_path=args.common_gene,
        common_protein_path=args.common_protein,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output)
    print(f"Wrote official DGAT predictions to {args.output}")


if __name__ == "__main__":
    main()
