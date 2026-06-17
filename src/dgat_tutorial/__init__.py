"""Utilities for the ECCB DGAT tutorial notebooks."""

from .data import SpatialOmicsData, load_demo_data
from .dgat import run_demo_dgat_inference
from .evaluation import morans_i, protein_correlations

__all__ = [
    "SpatialOmicsData",
    "load_demo_data",
    "morans_i",
    "protein_correlations",
    "run_demo_dgat_inference",
]
