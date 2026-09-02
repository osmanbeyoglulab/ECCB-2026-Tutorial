"""Compact Session 1 to Session 2 handoff utilities.

The handoff is written to the Colab VM first and copied to Google Drive once.
This avoids slow, repeated writes of very wide tables through the Drive mount.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


SESSION1_HANDOFF_FILENAME = "session01_handoff.npz"


@dataclass(frozen=True)
class Session1Handoff:
    """Arrays required to inspect the paired DGAT inputs in Session 2."""

    spot_ids: np.ndarray
    coordinates: np.ndarray
    gene_names: np.ndarray
    protein_names: np.ndarray
    rna: np.ndarray
    protein: np.ndarray
    spatial_edge_index: np.ndarray
    rna_edge_index: np.ndarray
    protein_edge_index: np.ndarray


def _validate_edge_index(name: str, edge_index: np.ndarray, n_spots: int) -> None:
    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError(f"{name} must have shape (2, E); got {edge_index.shape}.")
    if edge_index.size and (edge_index.min() < 0 or edge_index.max() >= n_spots):
        raise ValueError(f"{name} contains a node outside 0..{n_spots - 1}.")


def validate_session1_handoff(handoff: Session1Handoff) -> None:
    """Validate dimensions, identifiers, values, and graph bounds."""

    n_spots = len(handoff.spot_ids)
    if n_spots == 0:
        raise ValueError("The Session 1 handoff contains no spots.")
    if len(np.unique(handoff.spot_ids)) != n_spots:
        raise ValueError("The Session 1 handoff contains duplicate spot IDs.")
    if handoff.coordinates.shape != (n_spots, 2):
        raise ValueError(
            f"coordinates must have shape ({n_spots}, 2); got {handoff.coordinates.shape}."
        )
    if handoff.rna.shape != (n_spots, len(handoff.gene_names)):
        raise ValueError("RNA dimensions do not match the stored spot and gene identifiers.")
    if handoff.protein.shape != (n_spots, len(handoff.protein_names)):
        raise ValueError("Protein dimensions do not match the stored spot and protein identifiers.")
    for name, values in (
        ("coordinates", handoff.coordinates),
        ("RNA", handoff.rna),
        ("protein", handoff.protein),
    ):
        if not np.isfinite(values).all():
            raise ValueError(f"{name} contains NaN or infinite values.")
    for name, edge_index in (
        ("spatial_edge_index", handoff.spatial_edge_index),
        ("rna_edge_index", handoff.rna_edge_index),
        ("protein_edge_index", handoff.protein_edge_index),
    ):
        _validate_edge_index(name, edge_index, n_spots)


def write_session1_handoff(
    local_path: str | Path,
    persistent_path: str | Path,
    *,
    spots: pd.DataFrame,
    rna: pd.DataFrame,
    protein: pd.DataFrame,
    graphs: dict[str, np.ndarray],
) -> Path:
    """Write one local NPZ bundle, then copy it once to persistent storage."""

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("spots must contain x and y coordinates.")
    if not spots.index.equals(rna.index) or not spots.index.equals(protein.index):
        raise ValueError("spots, RNA, and protein must have identical ordered spot IDs.")

    handoff = Session1Handoff(
        spot_ids=spots.index.astype(str).to_numpy(dtype=str),
        coordinates=spots[["x", "y"]].to_numpy(dtype=np.float32),
        gene_names=rna.columns.astype(str).to_numpy(dtype=str),
        protein_names=protein.columns.astype(str).to_numpy(dtype=str),
        rna=rna.to_numpy(dtype=np.float32),
        protein=protein.to_numpy(dtype=np.float32),
        spatial_edge_index=np.asarray(graphs["spatial_edge_index"], dtype=np.int64),
        rna_edge_index=np.asarray(graphs["rna_edge_index"], dtype=np.int64),
        protein_edge_index=np.asarray(graphs["protein_edge_index"], dtype=np.int64),
    )
    validate_session1_handoff(handoff)

    local_path = Path(local_path)
    persistent_path = Path(persistent_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_local = local_path.with_name(f".{local_path.name}.writing")
    with temporary_local.open("wb") as handle:
        # Deliberately uncompressed: local serialization is fast, and the final
        # artifact is copied to Drive with one sequential transfer.
        np.savez(
            handle,
            spot_ids=handoff.spot_ids,
            coordinates=handoff.coordinates,
            gene_names=handoff.gene_names,
            protein_names=handoff.protein_names,
            rna=handoff.rna,
            protein=handoff.protein,
            spatial_edge_index=handoff.spatial_edge_index,
            rna_edge_index=handoff.rna_edge_index,
            protein_edge_index=handoff.protein_edge_index,
        )
    os.replace(temporary_local, local_path)

    if local_path.resolve() != persistent_path.resolve():
        persistent_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_persistent = persistent_path.with_name(f".{persistent_path.name}.copying")
        shutil.copyfile(local_path, temporary_persistent)
        os.replace(temporary_persistent, persistent_path)
    return persistent_path


def copy_handoff_to_local(persistent_path: str | Path, local_path: str | Path) -> Path:
    """Copy a complete persistent handoff to the local runtime when needed."""

    persistent_path = Path(persistent_path)
    local_path = Path(local_path)
    if not persistent_path.is_file() or persistent_path.stat().st_size == 0:
        raise FileNotFoundError(
            f"Missing {persistent_path}. Complete Session 1 graph construction first."
        )
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.is_file():
        local_stat = local_path.stat()
        persistent_stat = persistent_path.stat()
        if (
            local_stat.st_size == persistent_stat.st_size
            and local_stat.st_mtime_ns >= persistent_stat.st_mtime_ns
        ):
            return local_path
    temporary_local = local_path.with_name(f".{local_path.name}.copying")
    shutil.copyfile(persistent_path, temporary_local)
    os.replace(temporary_local, local_path)
    return local_path


def load_session1_handoff(path: str | Path) -> Session1Handoff:
    """Load and validate a Session 1 NPZ handoff without pickle."""

    path = Path(path)
    required = {
        "spot_ids",
        "coordinates",
        "gene_names",
        "protein_names",
        "rna",
        "protein",
        "spatial_edge_index",
        "rna_edge_index",
        "protein_edge_index",
    }
    with np.load(path, allow_pickle=False) as bundle:
        missing = sorted(required.difference(bundle.files))
        if missing:
            raise ValueError(f"Session 1 handoff is missing arrays: {missing}")
        handoff = Session1Handoff(**{name: bundle[name] for name in required})
    validate_session1_handoff(handoff)
    return handoff
