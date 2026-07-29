from __future__ import annotations

import argparse
import importlib
import platform
import sys
from pathlib import Path


REQUIRED_IMPORTS = [
    "anndata",
    "numpy",
    "pandas",
    "scipy",
    "torch",
    "torch_geometric",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the separate official-DGAT environment and files.")
    parser.add_argument("--dgat-repo", type=Path, default=Path("external/DGAT"))
    parser.add_argument("--asset-root", type=Path, default=Path("external/DGAT_assets"))
    args = parser.parse_args()

    failures: list[str] = []
    print(f"Python: {platform.python_version()} ({sys.executable})")
    if sys.version_info[:2] != (3, 11):
        failures.append("Official DGAT currently targets Python 3.11; activate eccb-dgat-official.")

    for module_name in REQUIRED_IMPORTS:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "installed")
            print(f"{module_name}: {version}")
        except Exception as exc:
            failures.append(f"Cannot import {module_name}: {exc}")

    entrypoint = args.dgat_repo / "Model" / "Train_and_Predict.py"
    print(f"DGAT code: {entrypoint}")
    if not entrypoint.exists():
        failures.append(f"Missing {entrypoint}; clone the official repository into external/DGAT.")

    h5ad_files = sorted(args.asset_root.rglob("*.h5ad")) if args.asset_root.exists() else []
    checkpoint_dirs = []
    if args.asset_root.exists():
        for encoder in args.asset_root.rglob("encoder_mRNA.pth"):
            if (encoder.parent / "decoder_protein.pth").exists():
                checkpoint_dirs.append(encoder.parent)
    print(f"H5AD files: {len(h5ad_files)}")
    print(f"Complete checkpoint directories: {len(checkpoint_dirs)}")
    if not h5ad_files:
        failures.append("No .h5ad files found under external/DGAT_assets.")
    if not checkpoint_dirs:
        failures.append("No directory contains both encoder_mRNA.pth and decoder_protein.pth.")

    if failures:
        print("\nPreflight failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("\nOfficial DGAT preflight passed.")


if __name__ == "__main__":
    main()
