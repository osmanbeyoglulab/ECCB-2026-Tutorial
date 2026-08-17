from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import unittest

from dgat_tutorial.data import load_gc_annotations
from dgat_tutorial.evaluation import (
    bivariate_morans_i_from_weights,
    morans_i_from_weights,
    symmetric_knn_weights,
)
from dgat_tutorial.processing import calculate_rna_qc_metrics, validate_modalities


class LymphNodeWorkflowTests(unittest.TestCase):
    def test_precomputed_prediction_contract(self):
        prediction_path = Path("data/raw/V1_Human_Lymph_Node_DGAT_predicted_proteins.csv")
        metadata_path = prediction_path.with_suffix(".metadata.json")
        predictions = pd.read_csv(prediction_path, index_col=0)
        metadata = json.loads(metadata_path.read_text())

        digest = hashlib.sha256(prediction_path.read_bytes()).hexdigest()
        recorded_digest = metadata.get("artifact_sha256") or metadata.get("prediction_sha256")
        self.assertEqual(metadata["dataset"], "V1_Human_Lymph_Node")
        self.assertEqual(digest, recorded_digest)
        self.assertEqual(predictions.shape, (metadata["rows"], metadata["proteins"]))
        self.assertTrue(predictions.index.is_unique)
        self.assertTrue(predictions.columns.is_unique)
        self.assertEqual(predictions.columns.tolist(), metadata["protein_names"])
        self.assertTrue({"CD19", "CXCR5", "PDCD1"}.issubset(predictions.columns))

    def test_tracked_gc_annotation_is_well_formed(self):
        labels = load_gc_annotations("data/raw/V1_Human_Lymph_Node_manual_GC_annot.csv")
        self.assertEqual(len(labels), 378)
        self.assertEqual(int(labels.sum()), 378)
        self.assertTrue(labels.index.is_unique)

    def test_rna_qc_counts_detected_genes_and_mitochondrial_fraction(self):
        rna = pd.DataFrame([[2, 0, 2], [0, 3, 0]], index=["a", "b"], columns=["MT-A", "CD19", "CXCR5"])
        qc = calculate_rna_qc_metrics(rna)
        self.assertEqual(qc.loc["a", "rna_total"], 4)
        self.assertEqual(qc.loc["a", "genes_detected"], 2)
        self.assertEqual(qc.loc["a", "mt_pct"], 50)
        self.assertEqual(qc.loc["b", "mt_pct"], 0)

    def test_paired_validation_rejects_transcript_only_input(self):
        spots = pd.DataFrame({"x": [0.0], "y": [0.0]}, index=["a"])
        rna = pd.DataFrame({"CD19": [1]}, index=["a"])
        with self.assertRaisesRegex(ValueError, "requires paired protein"):
            validate_modalities(spots, rna, None)

    def test_shared_six_neighbor_graph_is_symmetric(self):
        spots = pd.DataFrame({"x": np.arange(8.0), "y": np.zeros(8)})
        weights = symmetric_knn_weights(spots, n_neighbors=6)
        self.assertEqual(np.count_nonzero(weights != weights.T), 0)
        self.assertEqual(weights.diagonal().sum(), 0)

    def test_moran_synthetic_signals(self):
        spots = pd.DataFrame({"x": np.arange(30.0), "y": np.zeros(30)})
        weights = symmetric_knn_weights(spots, n_neighbors=2)
        gradient = pd.Series(np.arange(30.0))
        constant = pd.Series(np.ones(30))
        shuffled = gradient.sample(frac=1, random_state=7).reset_index(drop=True)
        self.assertTrue(np.isnan(morans_i_from_weights(constant, weights)))
        self.assertGreater(morans_i_from_weights(gradient, weights), morans_i_from_weights(shuffled, weights))

    def test_bivariate_moran_is_symmetric(self):
        spots = pd.DataFrame({"x": np.arange(12.0), "y": np.zeros(12)})
        weights = symmetric_knn_weights(spots, n_neighbors=2)
        a, b = pd.Series(np.arange(12.0)), pd.Series(np.arange(12.0) ** 2)
        self.assertTrue(np.isclose(bivariate_morans_i_from_weights(a, b, weights), bivariate_morans_i_from_weights(b, a, weights)))


if __name__ == "__main__":
    unittest.main()
