from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SpatialOmicsData:
    """Container used by the tutorial notebooks."""

    spots: pd.DataFrame
    transcripts: pd.DataFrame
    proteins: pd.DataFrame


def load_demo_data(n_spots: int = 260, random_state: int = 7) -> SpatialOmicsData:
    """Create a compact spatial-CITE-seq-like dataset for offline tutorial use."""

    rng = np.random.default_rng(random_state)
    side = int(np.ceil(np.sqrt(n_spots)))
    grid_x, grid_y = np.meshgrid(np.arange(side), np.arange(side))
    coords = np.column_stack([grid_x.ravel(), grid_y.ravel()])[:n_spots].astype(float)
    coords += rng.normal(scale=0.08, size=coords.shape)

    center = coords.mean(axis=0)
    distance = np.linalg.norm(coords - center, axis=1)
    radial = (distance - distance.min()) / (distance.max() - distance.min())
    left_right = (coords[:, 0] - coords[:, 0].min()) / np.ptp(coords[:, 0])
    top_bottom = (coords[:, 1] - coords[:, 1].min()) / np.ptp(coords[:, 1])

    spots = pd.DataFrame(
        {
            "spot_id": [f"spot_{i:03d}" for i in range(n_spots)],
            "x": coords[:, 0],
            "y": coords[:, 1],
            "region": np.where(radial < 0.42, "core", np.where(left_right > 0.55, "right edge", "left edge")),
        }
    ).set_index("spot_id")

    latent = np.column_stack([radial, left_right, top_bottom])
    gene_names = [f"Gene{i:02d}" for i in range(1, 25)]
    gene_weights = rng.normal(size=(latent.shape[1], len(gene_names)))
    gene_signal = latent @ gene_weights + rng.normal(scale=0.35, size=(n_spots, len(gene_names)))
    transcripts = pd.DataFrame(
        np.exp(gene_signal - gene_signal.min(axis=0) + 0.2),
        index=spots.index,
        columns=gene_names,
    )

    protein_names = ["CD3", "CD19", "EPCAM", "COL1A1", "PDL1", "KI67"]
    protein_weights = rng.normal(size=(len(gene_names), len(protein_names)))
    protein_signal = np.log1p(transcripts.to_numpy()) @ protein_weights / len(gene_names)
    protein_signal += np.column_stack(
        [
            1.6 * (1 - radial),
            1.4 * left_right,
            1.4 * (1 - left_right),
            1.6 * radial,
            1.2 * top_bottom,
            1.2 * (1 - top_bottom),
        ]
    )
    protein_signal += rng.normal(scale=0.12, size=protein_signal.shape)
    proteins = pd.DataFrame(
        protein_signal - protein_signal.min(axis=0),
        index=spots.index,
        columns=protein_names,
    )

    return SpatialOmicsData(spots=spots, transcripts=transcripts, proteins=proteins)


def load_csv_dataset(data_dir: str | Path) -> SpatialOmicsData:
    """Load a simple CSV dataset from data/raw.

    Expected files:
    - spots.csv with a spot_id column plus x and y columns.
    - transcripts.csv with spot IDs as the first column.
    - proteins.csv with spot IDs as the first column.
    """

    data_dir = Path(data_dir)
    spots = pd.read_csv(data_dir / "spots.csv").set_index("spot_id")
    transcripts = pd.read_csv(data_dir / "transcripts.csv", index_col=0)
    proteins = pd.read_csv(data_dir / "proteins.csv", index_col=0)

    common = spots.index.intersection(transcripts.index).intersection(proteins.index)
    return SpatialOmicsData(
        spots=spots.loc[common],
        transcripts=transcripts.loc[common],
        proteins=proteins.loc[common],
    )
