from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from dgat_tutorial.data import canonicalize_protein_columns, find_dgat_h5ad_pair, load_tutorial_data
from dgat_tutorial.checkpoints import find_tutorial_root, preferred_prediction_path, write_checkpoint
from dgat_tutorial.dgat import (
    discover_dgat_model_dir,
    load_prediction_metadata,
    prepare_dgat_model_layout,
    run_demo_dgat_inference,
    write_prediction_artifact,
)
from dgat_tutorial.processing import (
    calculate_qc_metrics,
    clr_normalize,
    knn_edge_index,
    normalize_total_log1p,
)
from dgat_tutorial.teaching import official_dgat_loss_table, weighted_training_objective


class DgatTutorialTests(unittest.TestCase):
    def test_tutorial_root_is_discovered_from_nested_notebook_directory(self) -> None:
        root = Path(__file__).resolve().parents[1]
        nested = root / "notebooks" / "session_03"
        self.assertEqual(find_tutorial_root(nested), root)

    def test_checkpoint_manifest_records_artifacts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            artifact = Path(tmp) / "artifact.csv"
            artifact.touch()
            manifest = write_checkpoint("9.9", [artifact], summary={"ok": True}, start=root)
            try:
                self.assertTrue(manifest.exists())
                self.assertIn('"part": "9.9"', manifest.read_text())
                self.assertIn('"exists": true', manifest.read_text())
            finally:
                manifest.unlink(missing_ok=True)
                manifest.parent.rmdir()

    def test_committed_predictions_are_the_default_checkpoint_fallback(self) -> None:
        root = Path(__file__).resolve().parents[1]
        from dgat_tutorial.checkpoints import tutorial_paths

        paths = tutorial_paths(root)
        expected = paths.processed_data / "predicted_proteins.csv"
        if not expected.exists():
            expected = paths.raw_data / "dgat_predictions.csv"
        self.assertEqual(preferred_prediction_path(paths), expected)

    def test_dgat_adt_protein_names_are_canonicalized(self) -> None:
        proteins = pd.DataFrame(
            [[1.0, 2.0, 3.0, 4.0]],
            columns=["CD163-1", "HLA-DRA", "PTPRC-1", "PTPRC-2"],
        )
        normalized = canonicalize_protein_columns(proteins)
        self.assertEqual(list(normalized.columns), ["CD163", "HLA_DRA", "PTPRC_1", "PTPRC_2"])

    def test_missing_breast_data_stops_instead_of_generating_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(FileNotFoundError, "paired Breast RNA/ADT"):
                load_tutorial_data(tmp)

    def test_tutorial_pair_discovery_selects_breast_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Skin_RNA.h5ad").touch()
            (root / "Skin_ADT.h5ad").touch()
            self.assertIsNone(find_dgat_h5ad_pair(root))

            breast_rna = root / "Breast_RNA.h5ad"
            breast_adt = root / "Breast_ADT.h5ad"
            breast_rna.touch()
            breast_adt.touch()
            self.assertEqual(find_dgat_h5ad_pair(root), (breast_rna, breast_adt))

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

    def test_flat_checkpoint_layout_is_adapted_without_changing_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "model_weights"
            adapter = Path(tmp) / "adapter"
            root.mkdir()
            (root / "encoder_mRNA.pth").write_bytes(b"encoder")
            (root / "decoder_protein.pth").write_bytes(b"decoder")

            resolved = prepare_dgat_model_layout(
                root,
                gene_count=17_434,
                protein_count=31,
                adapter_root=adapter,
            )

            nested = adapter / "17434_gene_31_protein"
            self.assertEqual(resolved, adapter)
            self.assertEqual((nested / "encoder_mRNA.pth").read_bytes(), b"encoder")
            self.assertEqual((nested / "decoder_protein.pth").read_bytes(), b"decoder")
            self.assertTrue((root / "encoder_mRNA.pth").exists())

    def test_processing_preserves_labels_and_normalizes_rna_depth(self) -> None:
        matrix = pd.DataFrame([[1.0, 3.0], [2.0, 8.0]], index=["a", "b"], columns=["g1", "g2"])
        normalized = normalize_total_log1p(matrix, target_sum=100.0)
        recovered_depth = np.expm1(normalized).sum(axis=1)
        np.testing.assert_allclose(recovered_depth, [100.0, 100.0])
        self.assertTrue(normalized.index.equals(matrix.index))
        self.assertTrue(normalized.columns.equals(matrix.columns))

    def test_protein_clr_is_centered_per_spot(self) -> None:
        proteins = pd.DataFrame([[0.0, 1.0, 3.0], [2.0, 2.0, 2.0]])
        normalized = clr_normalize(proteins)
        np.testing.assert_allclose(normalized.mean(axis=1), [0.0, 0.0], atol=1e-12)

    def test_qc_and_graph_outputs_have_teaching_shapes(self) -> None:
        transcripts = pd.DataFrame([[1.0, 0.0], [2.0, 1.0], [0.0, 2.0]])
        proteins = pd.DataFrame([[1.0], [0.0], [3.0]])
        qc = calculate_qc_metrics(transcripts, proteins)
        self.assertEqual(list(qc.columns), ["rna_total", "genes_detected", "protein_total", "proteins_detected"])
        coordinates = pd.DataFrame({"x": [0.0, 1.0, 0.0], "y": [0.0, 0.0, 1.0]})
        edge_index = knn_edge_index(coordinates, n_neighbors=2)
        self.assertEqual(edge_index.shape, (2, 6))

    def test_five_term_training_objective_is_explicit(self) -> None:
        self.assertEqual(len(official_dgat_loss_table()), 5)
        total = weighted_training_objective(1, 2, 3, 4, 5, weights=(1, 1, 1, 2, 0))
        self.assertEqual(total, 14.0)


if __name__ == "__main__":
    unittest.main()
