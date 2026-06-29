"""Utilities for the ECCB DGAT tutorial notebooks."""

from .data import SpatialOmicsData, find_dgat_h5ad, load_demo_data, load_h5ad_dataset, load_tutorial_data
from .dgat import run_demo_dgat_inference
from .evaluation import morans_i, protein_correlations

__all__ = [
    "SpatialOmicsData",
    "find_dgat_h5ad",
    "load_demo_data",
    "load_h5ad_dataset",
    "load_tutorial_data",
    "morans_i",
    "protein_correlations",
    "run_demo_dgat_inference",
]
