"""Verified precomputed DGAT graph assets shared by Sessions 1 and 2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np


PRECOMPUTED_GRAPH_DIRNAME = "precomputed_graphs"
PRECOMPUTED_GRAPH_FILENAMES = (
    "aligned_spot_ids.npy",
    "spatial_edge_index.npy",
    "rna_edge_index.npy",
    "protein_edge_index.npy",
    "metadata.json",
)


@dataclass(frozen=True)
class PrecomputedGraphs:
    """Ordered spot identifiers and the three DGAT encoder graph inputs."""

    spot_ids: np.ndarray
    spatial_edge_index: np.ndarray
    rna_edge_index: np.ndarray
    protein_edge_index: np.ndarray
    metadata: dict


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def graph_asset_paths(directory: str | Path) -> list[Path]:
    directory = Path(directory)
    return [directory / filename for filename in PRECOMPUTED_GRAPH_FILENAMES]


def copy_precomputed_graphs_to_local(
    persistent_directory: str | Path,
    local_directory: str | Path,
) -> Path:
    """Copy the small verified graph bundle from Drive to the local runtime."""

    persistent_directory = Path(persistent_directory)
    local_directory = Path(local_directory)
    missing = [path for path in graph_asset_paths(persistent_directory) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing precomputed graph assets: {missing}. Rerun the updated Session 0 notebook."
        )
    local_directory.mkdir(parents=True, exist_ok=True)
    for source in graph_asset_paths(persistent_directory):
        destination = local_directory / source.name
        if destination.is_file():
            source_stat = source.stat()
            destination_stat = destination.stat()
            if (
                source_stat.st_size == destination_stat.st_size
                and destination_stat.st_mtime_ns >= source_stat.st_mtime_ns
            ):
                continue
        temporary = destination.with_name(f".{destination.name}.copying")
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    return local_directory


def load_precomputed_graphs(
    directory: str | Path,
    *,
    expected_spot_ids: np.ndarray | None = None,
) -> PrecomputedGraphs:
    """Load graph arrays and enforce checksums, shapes, bounds, and spot order."""

    directory = Path(directory)
    metadata_path = directory / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    spot_path = directory / metadata["spot_order_file"]
    if _sha256(spot_path) != metadata["spot_order_sha256"]:
        raise IOError(f"Checksum mismatch for {spot_path}")
    spot_ids = np.load(spot_path, allow_pickle=False).astype(str)
    if spot_ids.shape != (int(metadata["spots"]),):
        raise ValueError(f"Unexpected precomputed spot-ID shape: {spot_ids.shape}")
    if len(np.unique(spot_ids)) != len(spot_ids):
        raise ValueError("Precomputed graph spot IDs are not unique.")
    if expected_spot_ids is not None:
        expected = np.asarray(expected_spot_ids).astype(str)
        if not np.array_equal(spot_ids, expected):
            raise ValueError(
                "Precomputed graph spot order does not match the processed Tonsil matrices."
            )

    arrays = {}
    for filename, specification in metadata["graphs"].items():
        path = directory / filename
        if _sha256(path) != specification["sha256"]:
            raise IOError(f"Checksum mismatch for {path}")
        edge_index = np.load(path, allow_pickle=False)
        expected_shape = tuple(int(value) for value in specification["shape"])
        if edge_index.shape != expected_shape or str(edge_index.dtype) != specification["dtype"]:
            raise ValueError(
                f"Unexpected {filename} contract: shape={edge_index.shape}, "
                f"dtype={edge_index.dtype}."
            )
        if edge_index.ndim != 2 or edge_index.shape[0] != 2:
            raise ValueError(f"{filename} must have shape (2, E).")
        if edge_index.size and (edge_index.min() < 0 or edge_index.max() >= len(spot_ids)):
            raise ValueError(f"{filename} contains an out-of-range node index.")
        arrays[filename] = edge_index

    return PrecomputedGraphs(
        spot_ids=spot_ids,
        spatial_edge_index=arrays["spatial_edge_index.npy"],
        rna_edge_index=arrays["rna_edge_index.npy"],
        protein_edge_index=arrays["protein_edge_index.npy"],
        metadata=metadata,
    )
