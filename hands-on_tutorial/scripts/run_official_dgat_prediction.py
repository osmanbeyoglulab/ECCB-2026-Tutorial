from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from dgat_tutorial.data import find_dgat_h5ad, find_dgat_h5ad_pair
from dgat_tutorial.dgat import (
    discover_dgat_model_dir,
    resolve_dgat_resource_files,
    run_official_dgat_prediction,
    write_prediction_artifact,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(repo: Path) -> str | None:
    if not (repo / ".git").exists():
        return None
    try:
        return (
            subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True)
            .strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run official DGAT pretrained protein prediction.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--rna-h5ad", type=Path, default=None, help="RNA AnnData file. Defaults to downloaded DGAT RNA .h5ad.")
    parser.add_argument("--dgat-repo", type=Path, default=Path("external/DGAT"))
    parser.add_argument(
        "--model-save-dir",
        type=Path,
        default=Path("external/DGAT_assets/model_weights"),
        help="Directory containing encoder_mRNA.pth and decoder_protein.pth (or a nested gene/protein folder).",
    )
    parser.add_argument("--pyg-data-dir", type=Path, default=Path("data/processed/dgat_pyg"))
    parser.add_argument("--common-gene", type=Path, default=None)
    parser.add_argument("--common-protein", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/processed/predicted_proteins.csv"))
    parser.add_argument(
        "--tonsil-held-out",
        choices=["true", "false", "unknown"],
        default="unknown",
        help="Provenance flag written into the sidecar. Use unknown unless authors confirmed held-out status.",
    )
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

    model_dir = discover_dgat_model_dir(
        [
            args.model_save_dir,
            args.model_save_dir.parent,
            args.dgat_repo / "DGAT_pretrained_models",
            Path("external") / "DGAT_assets",
        ]
    )
    gene_path, protein_path = resolve_dgat_resource_files(
        dgat_repo_dir=args.dgat_repo,
        model_save_dir=model_dir or args.model_save_dir,
        common_gene_path=args.common_gene,
        common_protein_path=args.common_protein,
    )
    held_out = {"true": True, "false": False, "unknown": None}[args.tonsil_held_out]
    encoder_path = None if model_dir is None else next(model_dir.rglob("encoder_mRNA.pth"), None)
    decoder_path = None if model_dir is None else next(model_dir.rglob("decoder_protein.pth"), None)

    write_prediction_artifact(
        predictions,
        args.output,
        method="official_dgat",
        source=str(rna_h5ad),
        evaluation_note=(
            "Official pretrained DGAT inference via fill_genes + preprocess_ST + protein_predict. "
            "Before treating Tonsil scores as held-out accuracy, confirm exclusion from training/"
            "checkpoint selection with the DGAT authors."
        ),
        extra_metadata={
            "dataset": "Tonsil" if "tonsil" in Path(rna_h5ad).name.lower() else Path(rna_h5ad).stem,
            "dgat_commit": _git_commit(args.dgat_repo),
            "prediction_sha256": None,  # filled below after write
            "encoder_mrna_sha256": _sha256(encoder_path) if encoder_path and encoder_path.is_file() else None,
            "decoder_protein_sha256": _sha256(decoder_path) if decoder_path and decoder_path.is_file() else None,
            "common_gene_file": str(gene_path),
            "common_protein_file": str(protein_path),
            "ordered_input_gene_count": len(
                [line for line in gene_path.read_text().splitlines() if line.strip()]
            ),
            "tonsil_held_out": held_out,
            "training_samples": None,
            "inference_preprocessing": "fill_genes + preprocess_ST",
        },
    )
    # Recompute prediction hash now that the CSV exists.
    metadata_path = args.output.with_suffix(".metadata.json")
    import json

    metadata = json.loads(metadata_path.read_text())
    metadata["prediction_sha256"] = _sha256(args.output)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote official DGAT predictions and provenance to {args.output}")


if __name__ == "__main__":
    main()
