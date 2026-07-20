from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from dgat_tutorial.dgat import (
    discover_dgat_model_dir,
    load_prediction_metadata,
    run_demo_dgat_inference,
    write_prediction_artifact,
)


class DgatTutorialTests(unittest.TestCase):
    def test_baseline_returns_out_of_fold_predictions(self) -> None:
        rng = np.random.default_rng(4)
        transcripts = pd.DataFrame(rng.lognormal(size=(40, 6)))
        proteins = pd.DataFrame(rng.normal(size=(40, 3)))
        predictions = run_demo_dgat_inference(transcripts, proteins)
        self.assertEqual(predictions.shape, proteins.shape)
        self.assertTrue(predictions.index.equals(transcripts.index))
        self.assertTrue(np.isfinite(predictions.to_numpy()).all())

    def test_prediction_artifact_includes_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.csv"
            predictions = pd.DataFrame({"CD3": [0.1, 0.2]}, index=["a", "b"])
            write_prediction_artifact(
                predictions,
                path,
                method="official_dgat",
                source="test.h5ad",
                evaluation_note="test note",
            )
            metadata = load_prediction_metadata(path)
            self.assertEqual(metadata["method"], "official_dgat")
            self.assertEqual(metadata["rows"], 2)

    def test_checkpoint_discovery_requires_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incomplete = root / "incomplete" / "10_gene_2_protein"
            incomplete.mkdir(parents=True)
            (incomplete / "encoder_mRNA.pth").touch()
            self.assertIsNone(discover_dgat_model_dir([root]))

            complete = root / "models" / "10_gene_2_protein"
            complete.mkdir(parents=True)
            (complete / "encoder_mRNA.pth").touch()
            (complete / "decoder_protein.pth").touch()
            self.assertEqual(discover_dgat_model_dir([root]), complete.parent)


if __name__ == "__main__":
    unittest.main()
