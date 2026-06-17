from __future__ import annotations

import numpy as np
import pandas as pd


def run_demo_dgat_inference(
    transcripts: pd.DataFrame,
    reference_proteins: pd.DataFrame,
    random_state: int = 7,
) -> pd.DataFrame:
    """Return DGAT-like protein predictions for tutorial dry runs.

    This lightweight baseline keeps the notebooks executable without the official
    DGAT environment. For the live tutorial, use the official DGAT repository:
    https://github.com/osmanbeyoglulab/DGAT
    """

    rng = np.random.default_rng(random_state)
    x = np.log1p(transcripts.to_numpy(dtype=float))
    y = reference_proteins.to_numpy(dtype=float)

    x_mean = x.mean(axis=0, keepdims=True)
    x_std = x.std(axis=0, keepdims=True) + 1e-8
    y_mean = y.mean(axis=0, keepdims=True)
    y_std = y.std(axis=0, keepdims=True) + 1e-8
    x_scaled = (x - x_mean) / x_std
    y_scaled = (y - y_mean) / y_std

    x_design = np.column_stack([np.ones(x_scaled.shape[0]), x_scaled])
    ridge = 0.25 * np.eye(x_design.shape[1])
    ridge[0, 0] = 0
    coefficients = np.linalg.solve(x_design.T @ x_design + ridge, x_design.T @ y_scaled)
    predicted = x_design @ coefficients
    predicted = predicted * y_std + y_mean
    predicted += rng.normal(scale=0.03, size=predicted.shape)

    return pd.DataFrame(predicted, index=transcripts.index, columns=reference_proteins.columns)


def load_prediction_table(path: str) -> pd.DataFrame:
    """Load precomputed DGAT predictions from CSV or TSV."""

    sep = "\t" if path.endswith(".tsv") else ","
    return pd.read_csv(path, sep=sep, index_col=0)
