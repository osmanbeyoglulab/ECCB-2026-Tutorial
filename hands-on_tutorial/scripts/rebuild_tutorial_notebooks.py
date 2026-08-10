"""Rebuild the reader-facing ECCB tutorial notebooks with nbformat.

Run from ``hands-on_tutorial`` after editing this file. Keeping notebook source in
one generator makes substantial tutorial revisions reviewable and avoids manual
JSON editing.
"""

from __future__ import annotations

from pathlib import Path
import re
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]

BOOTSTRAP = """from pathlib import Path
import sys

# Locates the cloned tutorial in Google Colab after Session 0 setup.
candidates = [Path.cwd().resolve(), *Path.cwd().resolve().parents]
colab_root = Path("/content/ECCB-2026-Tutorial/hands-on_tutorial")
if colab_root.is_dir():
    candidates.insert(0, colab_root.resolve())

for candidate in candidates:
    if (candidate / "src" / "dgat_tutorial").is_dir():
        tutorial_root = candidate
        break
else:
    raise FileNotFoundError(
        "Could not find hands-on_tutorial/. In Colab, run notebooks/session_00/00_colab_setup.ipynb first."
    )

sys.path.insert(0, str(tutorial_root / "src"))

from dgat_tutorial.checkpoints import tutorial_paths, write_checkpoint

paths = tutorial_paths(tutorial_root)
print(f"Tutorial root: {paths.root}")"""

def md(source: str):
    return nbf.v4.new_markdown_cell(dedent(source).strip() + "\n")


def code(source: str):
    return nbf.v4.new_code_cell(dedent(source).strip() + "\n")


def write(relative_path: str, cells: list) -> None:
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.10"}
    destination = ROOT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, destination)


def combine_session_notebooks(
    destination: str,
    title: str,
    summary: str,
    source_paths: list[str],
) -> None:
    """Combine a session's independently authored parts into one reader-facing notebook.

    Keeping the part definitions below makes individual sections easy to review while the
    generated participant layout stays compact. The combined notebook keeps one bootstrap
    cell at the beginning and removes the copies from its component parts.
    """
    cells = [
        md(f"""
        # {title}

        {summary}

        Work through the parts in order. Each part ends by writing its existing JSON checkpoint,
        so the consolidation changes file organization without removing pause/resume milestones.
        """),
        code(BOOTSTRAP),
    ]
    metadata = None
    for source_path in source_paths:
        source = ROOT / source_path
        notebook = nbf.read(source, as_version=4)
        metadata = metadata or notebook.metadata
        for cell in notebook.cells:
            if cell.cell_type == "code" and "from dgat_tutorial.checkpoints import tutorial_paths, write_checkpoint" in cell.source:
                continue
            if cell.cell_type == "markdown":
                # The combined notebook owns the only H1; former notebook sections nest below it.
                cell.source = re.sub(r"^(#{1,5})(?=\s)", r"#\1", cell.source, flags=re.MULTILINE)
            cells.append(cell)

    combined = nbf.v4.new_notebook(cells=cells, metadata=metadata or {})
    target = ROOT / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(combined, target)

    for source_path in source_paths:
        source = ROOT / source_path
        if source != target:
            source.unlink()


write(
    "notebooks/session_01/01_load_and_validate.ipynb",
    [
        md("""
        # Session 1 · Part 1 — Build the tutorial data object

        **Goal:** load paired spatial RNA and protein measurements into one validated object. We use the
        lightweight `SpatialOmicsData` object. The
        object plays the same teaching role: it keeps observations, modalities, and coordinates aligned.

        By the end you should be able to explain why row identity and coordinate validation must happen
        before normalization or graph construction. Every tutorial section uses the same **10x Genomics
        CytAssist Tonsil** RNA/ADT pair downloaded during Session 0; there is no generated-data substitute.
        """),
        code(BOOTSTRAP),
        md("""
        ### Dataset — 10x Genomics CytAssist Human Tonsil

        This tutorial uses a **public Visium CytAssist FFPE Human Tonsil** sample with paired gene expression
        and protein (ADT) measurements (`CytAssist_FFPE_Protein_Expression_Human_Tonsil`).

        | Item | Detail |
        | --- | --- |
        | Technology | 10x Genomics Visium CytAssist on FFPE tissue |
        | Tissue | Human tonsil (immune secondary lymphoid organ with follicles / germinal centers) |
        | Modalities | Spatial RNA + antibody-derived tags (proteins) on the same spots |
        | Files | `Tonsil_RNA.h5ad`, `Tonsil_ADT.h5ad` (DGAT-packaged AnnData) |
        | Approximate size | ~4,200 spots × ~18,000 genes × 35 proteins (before QC) |
        | Why it is useful here | Paired RNA–protein labels let us validate imputed protein landscapes against measured ADT while still practicing an RNA→protein inference workflow |

        Tonsil is a structured tissue: B- and T-cell zones create clear spatial protein patterns (for example
        immune markers), which makes QC failures, graph neighborhoods, and prediction errors easier to interpret
        visually. Downstream notebooks keep this same sample; there is no synthetic substitute.
        """),
        md("## 1. Load all three linked tables"),
        code("""
        import numpy as np
        import pandas as pd

        from dgat_tutorial.data import find_dgat_h5ad_pair, load_tutorial_data
        from dgat_tutorial.processing import validate_modalities

        pair = find_dgat_h5ad_pair(paths.raw_data)
        dataset = load_tutorial_data(paths.raw_data)
        spots = dataset.spots.copy()
        # Keep all feature columns; validate_modalities will fail if non-numeric values appear.
        transcripts = dataset.transcripts.copy()
        proteins = dataset.proteins.copy()
        dropped_rna = [c for c in transcripts.columns if not pd.api.types.is_numeric_dtype(transcripts[c])]
        dropped_protein = [c for c in proteins.columns if not pd.api.types.is_numeric_dtype(proteins[c])]
        if dropped_rna or dropped_protein:
            raise TypeError(
                "Non-numeric feature columns detected; refuse silent drop. "
                f"RNA={dropped_rna}; protein={dropped_protein}"
            )
        source = f"RNA={pair[0]}, ADT={pair[1]}"

        print(type(dataset).__name__)
        print(f"Source: {source}")
        print(f"spots × genes: {transcripts.shape}; spots × proteins: {proteins.shape}")
        display(spots.head(3), transcripts.iloc[:3, :5], proteins.iloc[:3, :5])
        """),
        md("""
        ## 2. Validate the object

        DGAT assumes that row *i* in RNA, protein, and spatial coordinates is the same biological spot.
        The next call checks ordered IDs, duplicate IDs, finite numeric x/y coordinates, finite values, and
        non-negative abundance. A shape match alone is not sufficient.
        """),
        code("""
        validate_modalities(spots, transcripts, proteins)
        xy = spots[["x", "y"]].to_numpy(dtype=float)
        checks = pd.DataFrame({
            "check": [
                "ordered IDs match",
                "x/y columns present",
                "x/y finite numeric",
                "finite RNA",
                "finite protein",
                "non-negative values",
            ],
            "passed": [
                spots.index.equals(transcripts.index) and spots.index.equals(proteins.index),
                {"x", "y"}.issubset(spots.columns),
                bool(np.isfinite(xy).all()),
                np.isfinite(transcripts.to_numpy(dtype=float)).all(),
                np.isfinite(proteins.to_numpy(dtype=float)).all(),
                (transcripts.to_numpy(dtype=float) >= 0).all() and (proteins.to_numpy(dtype=float) >= 0).all(),
            ],
        })
        checks
        """),
        md("## 3. Record a reproducible input summary"),
        code("""
        summary = pd.DataFrame([{
            "source": source,
            "spots": len(spots),
            "genes": transcripts.shape[1],
            "proteins": proteins.shape[1],
            "has_xy_coordinates": {"x", "y"}.issubset(spots.columns),
            "all_validation_checks_passed": bool(checks["passed"].all()),
        }])
        summary_path = paths.results / "session01_dataset_summary.csv"
        summary.to_csv(summary_path, index=False)
        manifest = write_checkpoint("1.1", [summary_path], summary=summary.iloc[0].to_dict(), start=paths.root)
        summary
        """),
        md("""
        ## Check

        Continue only when every validation row is `True`. If IDs disagree, fix the upstream pairing—never
        sort modalities independently and hope they align.
        """),
    ],
)


write(
    "notebooks/session_01/02_quality_control.ipynb",
    [
        md("""
        # Session 1 · Part 2 — QC, filtering, and normalization

        **Goal:** apply the official **paired CITE-seq / training** preprocessing from
        `external/DGAT/utils/Preprocessing.py` (`qc_control_cytassist` + `normalize`):

        - keep spots with ≥700 detected genes
        - remove spots with mitochondrial UMIs ≥35%
        - keep genes detected in ≥2.5% of spots (plus encoding genes matched to the protein panel)
        - remove ADT isotype controls (`mouse_`/`rat_` prefixes)
        - RNA: library-size normalize to 10,000 → `log1p` → gene-wise scale with clip at 10
        - protein: CLR via ``muon.prot.pp.clr`` (default ``axis=0``: per protein across spots)

        **Important:** ST-only inference uses a lighter path (`preprocess_ST`: min_genes=700 +
        RNA normalize/scale; no MT filter, no gene-prevalence filter, no protein CLR). Session 2's
        official prediction wrapper follows that inference path. This notebook teaches the
        *training* CytAssist recipe used when both RNA and protein are observed.
        """),
        code(BOOTSTRAP),
        md("## 1. Calculate spot-level QC metrics"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd

        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.plotting import plot_qc_overview, plot_raw_vs_normalized
        from dgat_tutorial.processing import (
            DGAT_MAX_MT_PCT,
            DGAT_MIN_CELLS_FRACTION,
            DGAT_MIN_GENES,
            calculate_qc_metrics,
            process_modalities_official_dgat,
            validate_modalities,
        )

        dataset = load_tutorial_data(paths.raw_data)
        spots = dataset.spots.copy()
        # Keep every gene/protein column; do not silently drop via select_dtypes.
        transcripts = dataset.transcripts.apply(pd.to_numeric, errors="raise")
        proteins = dataset.proteins.apply(pd.to_numeric, errors="raise")
        validate_modalities(spots, transcripts, proteins)
        qc_before = calculate_qc_metrics(transcripts, proteins)
        qc_before.describe().T
        """),
        md("### Figure 1 — RNA and protein QC distributions"),
        code("""
        qc_figure, _ = plot_qc_overview(qc_before)
        qc_figure_path = paths.figures / "session01_qc_rna_and_protein.png"
        qc_figure.savefig(qc_figure_path, dpi=160, bbox_inches="tight")
        plt.show()
        """),
        md("""
        **How to read it:** low RNA totals and gene counts flag weak transcript capture; protein
        totals reveal a different assay channel. Official DGAT training then applies fixed CytAssist
        thresholds (700 genes, 35% MT, 2.5% gene prevalence) rather than sample-adaptive quantiles.
        """),
        md("## 2. Apply official DGAT training filters"),
        code("""
        processed = process_modalities_official_dgat(
            spots,
            transcripts,
            proteins,
            dgat_repo_dir=paths.root / "external" / "DGAT",
            min_genes=DGAT_MIN_GENES,
            max_mt_pct=DGAT_MAX_MT_PCT,
        )
        filtered_spots = processed.spots
        filtered_rna = processed.raw_transcripts
        filtered_protein = processed.raw_proteins
        keep_mask = spots.index.astype(str).isin(filtered_spots.index)
        filtering_summary = pd.DataFrame([{
            "min_genes": DGAT_MIN_GENES,
            "max_mt_pct": DGAT_MAX_MT_PCT,
            "min_gene_prevalence": DGAT_MIN_CELLS_FRACTION,
            "spots_before": len(spots), "spots_after": len(filtered_spots),
            "genes_before": transcripts.shape[1], "genes_after": filtered_rna.shape[1],
            "proteins_before": proteins.shape[1], "proteins_after": filtered_protein.shape[1],
        }])
        filtering_summary.T
        """),
        md("""
        ### Why do 35 protein features become 31?

        The original ADT matrix contains 31 biological protein targets plus four antibody isotype
        controls: `mouse_IgG2a`, `mouse_IgG1k`, `mouse_IgG2bk`, and `rat_IgG2a`. These controls help
        characterize nonspecific antibody background; they are not protein targets predicted by DGAT.
        The upstream call `qc_control_cytassist(..., remove_isotype=True)` removes features whose names
        start with `mouse_` or `rat_`, leaving the 31-protein panel used downstream.
        """),
        md("## 3. Official DGAT normalization"),
        code("""
        # These matrices were produced above by DGAT's own normalize(...).
        rna_normalized = processed.normalized_transcripts
        protein_normalized = processed.normalized_proteins

        normalization_checks = pd.DataFrame({
            "quantity": [
                "RNA gene-wise mean after scale",
                "mean CLR protein value per protein (muon axis=0)",
            ],
            "expected": ["≈0 after scale", "not necessarily 0 (axis=0 CLR)"],
            "observed_median": [
                float(rna_normalized.mean(axis=0).median()),
                float(protein_normalized.mean(axis=0).median()),
            ],
        })
        normalization_checks
        """),
        md("### Figure 2 — What normalization changes"),
        code("""
        rna_feature = filtered_rna.var(axis=0).idxmax()
        protein_feature = filtered_protein.var(axis=0).idxmax()
        rna_fig, _ = plot_raw_vs_normalized(filtered_rna, rna_normalized, rna_feature, "RNA")
        protein_fig, _ = plot_raw_vs_normalized(filtered_protein, protein_normalized, protein_feature, "protein")
        rna_norm_path = paths.figures / "session01_rna_raw_vs_normalized.png"
        protein_norm_path = paths.figures / "session01_protein_raw_vs_normalized.png"
        rna_fig.savefig(rna_norm_path, dpi=160, bbox_inches="tight")
        protein_fig.savefig(protein_norm_path, dpi=160, bbox_inches="tight")
        plt.show()
        """),
        md("## 4. Save processed matrices and a QC audit trail"),
        code("""
        qc_path = paths.results / "session01_spot_qc.csv"
        filtering_path = paths.results / "session01_filtering_summary.csv"
        filtered_spots_path = paths.processed_data / "filtered_spots.csv"
        filtered_rna_path = paths.processed_data / "filtered_rna_counts.csv"
        filtered_protein_path = paths.processed_data / "filtered_protein_counts.csv"
        rna_path = paths.processed_data / "rna_log_normalized.csv"
        protein_path = paths.processed_data / "protein_clr_normalized.csv"
        processed_manifest_path = paths.processed_data / "session01_preprocessing_outputs.csv"

        qc_before.assign(kept=keep_mask).to_csv(qc_path)
        filtering_summary.to_csv(filtering_path, index=False)
        filtered_spots.to_csv(filtered_spots_path)
        filtered_rna.to_csv(filtered_rna_path)
        filtered_protein.to_csv(filtered_protein_path)
        rna_normalized.to_csv(rna_path)
        protein_normalized.to_csv(protein_path)

        processed_outputs = pd.DataFrame([
            {
                "artifact": path.name,
                "stage": stage,
                "rows": table.shape[0],
                "columns": table.shape[1],
                "description": description,
            }
            for path, stage, table, description in [
                (filtered_spots_path, "filtered", filtered_spots, "Aligned spot metadata and x/y coordinates"),
                (filtered_rna_path, "filtered", filtered_rna, "RNA counts after spot and gene filtering"),
                (filtered_protein_path, "filtered", filtered_protein, "ADT counts after spot and isotype filtering"),
                (rna_path, "normalized", rna_normalized, "DGAT library-size/log1p/gene-scaled RNA"),
                (protein_path, "normalized", protein_normalized, "DGAT CLR-normalized protein values"),
            ]
        ])
        processed_outputs.to_csv(processed_manifest_path, index=False)

        processed_artifacts = [
            filtered_spots_path,
            filtered_rna_path,
            filtered_protein_path,
            rna_path,
            protein_path,
            processed_manifest_path,
        ]
        manifest = write_checkpoint(
            "1.2",
            [qc_path, filtering_path, *processed_artifacts, qc_figure_path, rna_norm_path, protein_norm_path],
            summary={
                "spots_kept": len(filtered_spots),
                "spots_removed": int((~keep_mask).sum()),
                "processed_data_files": len(processed_artifacts),
            },
            start=paths.root,
        )
        print(f"Processed data saved under: {paths.processed_data}")
        display(processed_outputs)
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        You should now be able to justify: (1) which spots/features were removed, (2) why RNA and protein
        use different transforms, and (3) why filtered counts remain available alongside normalized
        matrices for QC and auditability. Confirm the six files listed above exist in `data/processed/`.
        """),
    ],
)


write(
    "notebooks/session_01/03_spatial_neighborhoods.ipynb",
    [
        md("""
        # Session 1 · Part 3 — Spatial neighborhoods and exploratory structure

        **Goal:** construct the **official DGAT graphs** and inspect exploratory structure.

        Official DGAT (`utils/Graph_utils.py`) builds:

        1. a **spatial 6-NN** graph
        2. an **RNA molecular 10-NN** graph in PCA space (when >1500 genes; 85% variance)
        3. a **protein molecular 10-NN** graph in feature space

        The RNA encoder uses `spatial ∪ RNA-molecular` edges; the protein encoder uses
        `spatial ∪ protein-molecular` edges. This notebook visualizes the **spatial component
        only** for readability, then saves the **union** graphs that the encoders actually use.
        """),
        code(BOOTSTRAP),
        md("## 1. Reload and process the data independently"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA

        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.plotting import plot_spatial_feature, plot_spatial_knn_graph
        from dgat_tutorial.processing import build_dgat_graphs, knn_edge_index, process_modalities_official_dgat

        dataset = load_tutorial_data(paths.raw_data)
        processed = process_modalities_official_dgat(
            dataset.spots,
            dataset.transcripts,
            dataset.proteins,
            dgat_repo_dir=paths.root / "external" / "DGAT",
        )
        spots = processed.spots
        rna = processed.normalized_transcripts
        protein = processed.normalized_proteins
        graphs = build_dgat_graphs(spots, rna, protein)
        edge_index = graphs["spatial_edge_index"]
        print(
            f"Spatial 6-NN edges: {graphs['spatial_edge_index'].shape[1]}; "
            f"RNA union graph: {graphs['rna_edge_index'].shape[1]}; "
            f"protein union graph: {graphs['protein_edge_index'].shape[1]}"
        )
        """),
        md("""
        ### Figure 3 — Spatial neighborhood structure (one component of the encoder graph)

        Drawing every edge on all ~4,000 spots makes the local neighborhood structure
        unreadable, so this figure splits overview and zoom for the **spatial 6-NN**
        component only. Remember: each DGAT encoder also unions a molecular 10-NN graph.

        - **Left:** all spots as nodes (no edges), with a red box marking the corner region.
        - **Right:** undirected spatial 6-nearest-neighbor edges inside that corner.
        - **Highlight:** the red spot is a boundary example; the orange spots are its spatial
          neighbors in this teaching view. The full encoder edge set is larger once molecular
          neighbors are unioned (saved below as `rna_edge_index` / `protein_edge_index`).
        """),
        code("""
        fig, _ = plot_spatial_knn_graph(spots, edge_index, n_neighbors=6, zoom_corner="lower_left")
        graph_path = paths.figures / "session01_spatial_knn_graph.png"
        fig.savefig(graph_path, dpi=160, bbox_inches="tight")
        plt.show()
        """),
        md("### Figure 4 — Normalized RNA and protein landscapes"),
        code("""
        rna_features = rna.var(axis=0).nlargest(3).index
        protein_features = protein.var(axis=0).nlargest(3).index
        fig, axes = plt.subplots(2, 3, figsize=(13, 8))
        for ax, feature in zip(axes[0], rna_features):
            plot_spatial_feature(spots, rna[feature], f"Normalized RNA: {feature}", cmap="magma", ax=ax)
        for ax, feature in zip(axes[1], protein_features):
            plot_spatial_feature(spots, protein[feature], f"CLR protein: {feature}", cmap="viridis", ax=ax)
        figure_path = paths.figures / "session01_normalized_spatial_features.png"
        fig.savefig(figure_path, dpi=160, bbox_inches="tight")
        plt.show()
        """),
        md("""
        ### Figure 5 — Exploratory RNA and protein embeddings

        Colors are exploratory KMeans groups in PCA space (**not** curated cell-type labels).

        - **Left:** RNA PCA; spots share one of four RNA cluster colors (`0`–`3`).
        - **Middle:** protein PCA with its **own** four protein clusters (same palette, independent IDs).
        - **Right:** the RNA cluster colors from the left panel mapped back onto tissue coordinates.

        Use these panels only to check whether modality structure and spatial organization look coherent before moving to DGAT.
        """),
        code('''
        def pca_clusters(matrix, n_clusters=4, n_pcs=20):
            n_pcs = min(n_pcs, matrix.shape[0] - 1, matrix.shape[1])
            pcs = PCA(n_components=n_pcs, random_state=7).fit_transform(matrix)
            clusters = KMeans(n_clusters=min(n_clusters, len(matrix)), n_init=20, random_state=7).fit_predict(pcs)
            return pcs[:, :2], clusters  # visualize PC1/PC2; cluster in higher-D PC space


        def cluster_colors(labels, cmap_name="tab10"):
            """Map integer cluster IDs to stable discrete colors."""
            cmap = plt.get_cmap(cmap_name)
            return np.asarray([cmap(int(label) % 10) for label in labels])


        rna_pca, rna_cluster = pca_clusters(rna)
        protein_pca, protein_cluster = pca_clusters(protein)
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
        axes[0].scatter(rna_pca[:, 0], rna_pca[:, 1], c=cluster_colors(rna_cluster), s=20)
        axes[0].set_title("RNA PCA (exploratory clusters)")
        axes[0].set_xlabel("PC1")
        axes[0].set_ylabel("PC2")

        axes[1].scatter(protein_pca[:, 0], protein_pca[:, 1], c=cluster_colors(protein_cluster), s=20)
        axes[1].set_title("Protein PCA (exploratory clusters)")
        axes[1].set_xlabel("PC1")
        axes[1].set_ylabel("PC2")

        axes[2].scatter(spots["x"], spots["y"], c=cluster_colors(rna_cluster), s=20)
        axes[2].set_title("RNA clusters mapped to tissue")
        axes[2].set_xlabel("x")
        axes[2].set_ylabel("y")
        axes[2].set_aspect("equal")

        embedding_path = paths.figures / "session01_modality_pca_and_spatial_clusters.png"
        fig.tight_layout()
        fig.savefig(embedding_path, dpi=160, bbox_inches="tight")
        plt.show()
        '''),
        md("## Save the graph and checkpoint"),
        code("""
        edge_table = pd.DataFrame({"source": spots.index[edge_index[0]], "target": spots.index[edge_index[1]]})
        edge_path = paths.results / "session01_spatial_knn_edges.csv"
        edge_table.to_csv(edge_path, index=False)
        manifest = write_checkpoint(
            "1.3", [edge_path, graph_path, figure_path, embedding_path],
            summary={"nodes": len(spots), "directed_edges": edge_index.shape[1]}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Trace one spot from its normalized feature vector to its node and six outgoing spatial edges. DGAT's
        graph attention layers learn how much neighbor information to aggregate; the graph defines which
        neighbors are available.
        """),
    ],
)


write(
    "notebooks/session_02/01_prepare_inputs.ipynb",
    [
        md("""
        # Session 2 · Part 1 — Prepare paired graphs for DGAT

        **Goal:** turn aligned, normalized RNA and protein measurements into the two graph inputs used during
        training. A spatial transcriptomics prediction sample has RNA only; paired spatial CITE-seq training
        samples provide both modalities. This notebook uses the same official Tonsil RNA/ADT pair as Session 1,
        so the tensor dimensions and graph construction correspond to the real tutorial dataset.
        """),
        code(BOOTSTRAP),
        md("## 1. Process paired modalities"),
        code("""
        import numpy as np
        import pandas as pd

        from dgat_tutorial.data import find_dgat_h5ad_pair, load_tutorial_data
        from dgat_tutorial.processing import build_dgat_graphs, knn_edge_index, process_modalities_official_dgat

        pair = find_dgat_h5ad_pair(paths.raw_data)
        dataset = load_tutorial_data(paths.raw_data)
        processed = process_modalities_official_dgat(
            dataset.spots,
            dataset.transcripts,
            dataset.proteins,
            dgat_repo_dir=paths.root / "external" / "DGAT",
        )
        source = f"RNA={pair[0]}, ADT={pair[1]}"
        """),
        md("## 2. Construct and save the RNA and protein graph inputs"),
        code("""
        # The official pipeline stores these as PyTorch Geometric HeteroData node/edge types.
        # Here we expose the arrays first so dimensions and alignment are easy to inspect.
        x_rna = processed.normalized_transcripts.to_numpy(dtype=np.float32)
        x_protein = processed.normalized_proteins.to_numpy(dtype=np.float32)
        graphs = build_dgat_graphs(
            processed.spots,
            processed.normalized_transcripts,
            processed.normalized_proteins,
        )
        rna_edge_index = graphs["rna_edge_index"]
        protein_edge_index = graphs["protein_edge_index"]
        spatial_edge_index = graphs["spatial_edge_index"]
        print(
            "DGAT graphs = spatial 6-NN ∪ molecular 10-NN "
            f"(RNA PCA if >1500 genes). "
            f"spatial={spatial_edge_index.shape[1]}, "
            f"rna_union={rna_edge_index.shape[1]}, "
            f"protein_union={protein_edge_index.shape[1]}"
        )

        graph_summary = pd.DataFrame([
            {"graph": "RNA", "nodes": len(x_rna), "node_features": x_rna.shape[1], "directed_edges": rna_edge_index.shape[1]},
            {"graph": "protein", "nodes": len(x_protein), "node_features": x_protein.shape[1], "directed_edges": protein_edge_index.shape[1]},
        ])
        display(graph_summary)

        # Save the node-order mapping, graph summary, RNA union edges, and checkpoint metadata.
        ids_path = paths.processed_data / "aligned_spot_ids.csv"
        summary_path = paths.results / "session02_graph_input_summary.csv"
        edge_path = paths.processed_data / "rna_spatial_edge_index.csv"
        pd.DataFrame({"spot_id": processed.spots.index}).to_csv(ids_path, index=False)
        graph_summary.assign(source=source).to_csv(summary_path, index=False)
        pd.DataFrame(rna_edge_index.T, columns=["source_index", "target_index"]).to_csv(edge_path, index=False)
        manifest = write_checkpoint(
            "2.1", [ids_path, summary_path, edge_path],
            summary={"source": source, "spots": len(processed.spots), "genes": x_rna.shape[1], "proteins": x_protein.shape[1]},
            start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## 3. Understand the training and inference handoff

        During training, paired RNA/protein graphs produce two latent representations. During inference, only
        the RNA graph is encoded; its latent representation is sent through the trained protein decoder.

        `RNA graph → RNA encoder → shared latent → protein decoder → predicted proteins`
        """),
        md("""
        ## Check

        Both graphs must have the same node count and ordering in paired training data. Feature counts differ:
        RNA nodes carry genes and protein nodes carry ADTs. Edge arrays use integer node positions and have
        shape `2 × number_of_edges`.
        """),
        md("""
        ### Why does this RNA graph have 17,434 features while the pretrained model expects 11,535?

        The two counts come from two different upstream DGAT training workflows:

        - **17,434 genes:** `Demo1_Train.ipynb` trains on **Tonsil alone**. After
          `preprocess_train_list` applies CytAssist QC, 17,434 Tonsil genes remain. This tutorial uses that
          same single-sample preprocessing to demonstrate how a paired RNA/protein training graph is built.
        - **11,535 genes:** `Pretrain_DGAT.ipynb` creates the public pretrained model from **six paired
          datasets**: Tonsil, Tonsil AddOns, Breast, Glioblastoma, PBC-PR_6835-5A, and PBC_PR_6837.
          `preprocess_train_list` first finds genes shared by the input datasets, applies the 2.5% gene
          prevalence and spot-level QC within each dataset (while retaining protein-encoding genes), and then
          intersects the post-QC gene sets again. That final sorted intersection contains 11,535 genes and is
          saved upstream as `common_gene_11535.txt`. The 31-protein panel is derived analogously as the common
          post-QC protein set.

        Consequently, 11,535 is not an arbitrary truncation of the Tonsil matrix: it is the cross-dataset
        feature vocabulary on which the public checkpoint was trained, and it fixes the RNA encoder's input
        width and gene order. A 17,434-feature matrix cannot be passed directly to that encoder. During real
        pretrained inference, `fill_genes` selects and reorders the RNA matrix to `common_gene_11535.txt` and
        inserts zeros for missing panel genes; `preprocess_ST` then normalizes it before graph construction.
        Thus, the graph above illustrates the one-sample paired-training workflow, not the exact matrix supplied
        to the six-dataset public checkpoint.
        """),
    ],
)


write(
    "notebooks/session_02/02_build_dgat_model.ipynb",
    [
        md("""
        # Session 2 · Part 2 — Create every DGAT model component

        **Goal:** understand and instantiate the four modules that are trained jointly. This lesson follows the
        official `Model/dgat.py`: separate RNA and protein graph-attention encoders, an RNA decoder, and a
        branched protein decoder. The lightweight path prints the architecture and creates a figure; an optional
        cell instantiates the real PyTorch modules when the official DGAT environment and repository are present.
        """),
        code(BOOTSTRAP),
        md("## 1. Set dimensions from the processed data"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.teaching import (
            DGAT_PRETRAINED_GENE_COUNT,
            DGAT_PRETRAINED_PROTEIN_COUNT,
            official_dgat_component_table,
        )

        dataset = load_tutorial_data(paths.raw_data)
        # Teaching dimensions follow the public pretrained ST checkpoint (Demo3 uses 11535 genes /
        # 31 proteins). The Tonsil AnnData has a broader gene panel; inference zero-fills to the
        # common-gene list via official fill_genes before protein_predict.
        gene_list_path = paths.root / "external" / "DGAT" / "resources" / f"common_gene_{DGAT_PRETRAINED_GENE_COUNT}.txt"
        protein_list_path = paths.root / "external" / "DGAT" / "resources" / f"common_protein_{DGAT_PRETRAINED_PROTEIN_COUNT}.txt"
        if gene_list_path.exists() and protein_list_path.exists():
            common_genes = [line.strip() for line in gene_list_path.read_text().splitlines() if line.strip()]
            common_proteins = [line.strip() for line in protein_list_path.read_text().splitlines() if line.strip()]
            print(f"Using official common lists: {len(common_genes)} genes, {len(common_proteins)} proteins")
        else:
            common_genes = list(dataset.transcripts.columns)[:DGAT_PRETRAINED_GENE_COUNT]
            common_proteins = list(dataset.proteins.columns)[:DGAT_PRETRAINED_PROTEIN_COUNT]
            print(
                "Official common_gene/protein lists not found under external/DGAT/resources/; "
                f"using the first {len(common_genes)} genes / {len(common_proteins)} proteins from Tonsil for the architecture table."
            )
        HIDDEN_DIM = 1024  # official Train_and_Predict.py
        component_table = official_dgat_component_table(len(common_genes), common_proteins, HIDDEN_DIM)
        component_table
        """),
        md("""
        ## 2. Read the architecture from left to right

        1. Each encoder performs three graph-attention stages with skip projections and LayerNorm.
        2. After the first GAT stage, 16 feature-attention heads learn channel gates and their mean reweights the
           2048-dimensional representation.
        3. Both encoders end in the same latent dimension so paired RNA and protein spots can be aligned.
        4. The protein decoder shares two layers, then uses one output branch per protein. This lets proteins
           share signal while retaining protein-specific prediction heads.
        """),
        md("### Figure 6 — DGAT architecture and inference path"),
        code("""
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")

        def box(x, y, w, h, label, color):
            patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333333")
            ax.add_patch(patch); ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=9)
        def arrow(x1, y1, x2, y2, style="-"):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12,
                                         linewidth=1.2, linestyle=style, color="#333333"))

        box(0.3, 4.1, 1.6, 1.0, "RNA graph\\nX_RNA, E_RNA", "#d9eaf7")
        box(2.5, 4.1, 2.0, 1.0, "RNA GAT encoder", "#96c5e8")
        box(5.2, 4.1, 1.6, 1.0, "z_RNA", "#e4d7f4")
        box(0.3, 1.0, 1.6, 1.0, "Protein graph\\nX_P, E_P", "#fde2cd")
        box(2.5, 1.0, 2.0, 1.0, "Protein GAT encoder", "#f5b97f")
        box(5.2, 1.0, 1.6, 1.0, "z_protein", "#e4d7f4")
        box(8.0, 4.1, 1.6, 1.0, "RNA decoder", "#d7ecd9")
        box(8.0, 1.0, 1.6, 1.0, "Protein decoder", "#d7ecd9")
        box(10.2, 4.1, 1.5, 1.0, "RNA output", "#eeeeee")
        box(10.2, 1.0, 1.5, 1.0, "Protein output", "#eeeeee")
        for start, end in [((1.9,4.6),(2.5,4.6)),((4.5,4.6),(5.2,4.6)),((1.9,1.5),(2.5,1.5)),
                           ((4.5,1.5),(5.2,1.5)),((6.8,4.6),(8.0,4.6)),((9.6,4.6),(10.2,4.6)),
                           ((6.8,1.5),(8.0,1.5)),((9.6,1.5),(10.2,1.5))]: arrow(*start,*end)
        arrow(6.8, 4.4, 8.0, 1.8, "--")
        arrow(6.8, 1.7, 8.0, 4.3, "--")
        ax.text(7.25, 3.0, "cross-modal\\nprediction", ha="center", va="center", fontsize=9)
        ax.text(6.0, 3.0, "latent alignment", ha="center", va="center", fontsize=9, rotation=90)
        ax.plot([6.0,6.0],[2.0,4.1], color="#6b4c9a", linestyle=":", linewidth=2)
        architecture_path = paths.figures / "session02_dgat_architecture.png"
        fig.savefig(architecture_path, dpi=180, bbox_inches="tight")
        plt.show()
        """),
        md("## 3. Instantiate the official modules (optional official environment)"),
        code("""
        # This is the exact constructor pattern used by the upstream training workflow.
        # It executes only when external/DGAT and torch/torch_geometric are available.
        dgat_repo = paths.root / "external" / "DGAT"
        try:
            import torch
            sys.path.insert(0, str(dgat_repo))
            from Model.dgat import GATEncoder, Decoder_Protein, Decoder_mRNA
            OFFICIAL_READY = dgat_repo.is_dir()
        except (ImportError, OSError):
            OFFICIAL_READY = False

        if OFFICIAL_READY:
            encoder_rna = GATEncoder(in_channels=len(common_genes), hidden_dim=HIDDEN_DIM, dropout=0.3)
            decoder_rna = Decoder_mRNA(HIDDEN_DIM, len(common_genes), dropout=0)
            encoder_protein = GATEncoder(in_channels=len(common_proteins), hidden_dim=HIDDEN_DIM, dropout=0.3)
            decoder_protein = Decoder_Protein(HIDDEN_DIM, common_proteins, dropout=0)
            modules = {"RNA encoder": encoder_rna, "RNA decoder": decoder_rna,
                       "protein encoder": encoder_protein, "protein decoder": decoder_protein}
            for name, module in modules.items():
                print(f"{name:18s}: {sum(p.numel() for p in module.parameters()):,} parameters")
        else:
            print("Architecture lesson complete. To instantiate modules, use environment-dgat-cpu.yml and clone DGAT to external/DGAT.")
        """),
        code("""
        component_path = paths.results / "session02_dgat_components.csv"
        component_table.to_csv(component_path, index=False)
        manifest = write_checkpoint(
            "2.2", [component_path, architecture_path],
            summary={"modules": len(component_table), "official_modules_instantiated": OFFICIAL_READY}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Point to the exact inference route in the figure: **RNA graph → RNA encoder → z_RNA → protein
        decoder**. The protein encoder and RNA decoder are training-time partners that make the shared latent
        space learnable; they are not needed to impute protein on an RNA-only sample.
        """),
    ],
)


write(
    "notebooks/session_02/03_train_dgat.ipynb",
    [
        md("""
        # Session 2 · Part 3 — Training objective (discussion; training skipped)

        **Goal:** connect the four modules to five losses, four optimizers, backpropagation, evaluation, and
        checkpoints — conceptually. **This tutorial does not train DGAT** (Colab / workshop compute limits).
        We inspect the official objective and a pedagogical training step, then continue to pretrained
        predictions in Part 4. Full training belongs in the upstream
        [DGAT repository](https://github.com/osmanbeyoglulab/DGAT), not the live session.
        """),
        code(BOOTSTRAP),
        md("## 1. Decompose the training objective"),
        code("""
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

        from dgat_tutorial.teaching import (
            DGAT_TRAIN_LOSS_WEIGHTS,
            official_dgat_loss_table,
            official_dgat_optimizer_table,
            weighted_training_objective,
        )

        loss_table = official_dgat_loss_table()
        display(loss_table)
        display(official_dgat_optimizer_table())
        print(f"DGAT training coefficients (α,β,γ,δ,η): {DGAT_TRAIN_LOSS_WEIGHTS}")
        """),
        md("""
        The DGAT **training loop** uses five coefficients:

        $$
        (\\alpha,\\beta,\\gamma,\\delta,\\eta)=(5,1,1,3,1).
        $$

        Its scalar training objective is

        $$
        \\begin{aligned}
        \\mathcal{L}_{\\mathrm{train}} ={}&
        5\\,\\mathcal{L}_{\\mathrm{RNA\\ recon}}
        + \\widetilde{\\beta}\\,\\mathcal{L}_{\\mathrm{protein\\ recon}}
        + \\widetilde{\\gamma}\\,\\mathcal{L}_{\\mathrm{alignment}} \\\\
        &+ \\widetilde{\\delta}\\,\\mathcal{L}_{\\mathrm{RNA}\\rightarrow\\mathrm{protein}}
        + 1\\,\\mathcal{L}_{\\mathrm{protein}\\rightarrow\\mathrm{RNA}},
        \\end{aligned}
        $$

        Each corresponding
        effective coefficient—$\\widetilde{\\beta}$, $\\widetilde{\\gamma}$, or
        $\\widetilde{\\delta}$—is replaced by zero when its unweighted loss is below $0.015$.
        The RNA-reconstruction coefficient $\\alpha=5$ and protein→RNA coefficient $\\eta=1$
        are not subject to this soft-zero rule.

        The RNA→protein term directly trains the path used at inference. Always log the components
        separately—a falling total can hide a failing task.
        """),
        code("""
        example_logged_terms = dict(
            rna_reconstruction=0.42, protein_reconstruction=0.31, latent_alignment=0.08,
            protein_prediction=0.37, rna_prediction=0.46,
        )
        example_total = weighted_training_objective(**example_logged_terms)
        print("Actual upstream training calculation for these example loss values:")
        print("5×0.42 + 1×0.31 + 1×0.08 + 3×0.37 + 1×0.46")
        print(f"Total training loss = {example_total:.2f}")
        print("All five example losses exceed 0.015, so no coefficient is soft-zeroed.")
        """),
        md("""
        ## 2. Inspect one real training step (pedagogical mirror)

        This cell is for reading and discussion. It is **not** a complete training loop: it does not load
        batches, run epochs, validate on a held-out sample, or save checkpoints. The figure below contrasts
        the **recommended** held-out validate/save-best workflow (dashed) with what upstream
        `Train_and_Predict.train(...)` currently exposes (solid boxes only through backprop + EB early stop).
        """),
        code("""
        try:
            import torch
        except ImportError:
            torch = None

        from dgat_tutorial.teaching import DGAT_LOSS_SOFT_THRESHOLD, DGAT_TRAIN_LOSS_WEIGHTS, apply_soft_loss_weights

        def dgat_training_step(batch, modules, optimizers, rmse_loss, mse_loss, weights=DGAT_TRAIN_LOSS_WEIGHTS):
            # Readable mirror of the upstream DGAT optimization step (not invoked in the tutorial path).
            if torch is None:
                raise ImportError("torch is required to execute dgat_training_step; use eccb-dgat-official.")
            encoder_rna, decoder_rna, encoder_protein, decoder_protein = modules
            for optimizer in optimizers:
                optimizer.zero_grad()

            x_rna = batch["mRNA"].x
            e_rna = batch[("mRNA", "mRNA_knn", "mRNA")].edge_index
            x_protein = batch["protein"].x
            e_protein = batch[("protein", "protein_knn", "protein")].edge_index

            z_rna = encoder_rna(x_rna, e_rna)
            z_protein = encoder_protein(x_protein, e_protein)

            losses = {
                "rna_reconstruction": rmse_loss(decoder_rna(z_rna), x_rna),
                "protein_reconstruction": rmse_loss(decoder_protein(z_protein), x_protein),
                "latent_alignment": mse_loss(z_rna, z_protein),
                "protein_prediction": rmse_loss(decoder_protein(z_rna), x_protein),
                "rna_prediction": rmse_loss(decoder_rna(z_protein), x_rna),
            }
            effective = apply_soft_loss_weights(
                float(losses["protein_reconstruction"].detach()),
                float(losses["latent_alignment"].detach()),
                float(losses["protein_prediction"].detach()),
                weights=weights,
                soft_threshold=DGAT_LOSS_SOFT_THRESHOLD,
            )
            total = sum(weight * loss for weight, loss in zip(effective, losses.values()))
            total.backward()
            for module in modules:
                torch.nn.utils.clip_grad_norm_(module.parameters(), max_norm=1.0)
            for optimizer in optimizers:
                optimizer.step()
            return {name: float(value.detach()) for name, value in losses.items()} | {"total": float(total.detach())}

        print(f"torch={'unavailable' if torch is None else torch.__version__}")
        print(f"Default train weights α,β,γ,δ,η = {DGAT_TRAIN_LOSS_WEIGHTS}; soft-threshold = {DGAT_LOSS_SOFT_THRESHOLD}")
        print("dgat_training_step is defined for inspection only; the tutorial does not call it.")
        """),
        md("### Figure 7 — Upstream training path vs recommended validation loop"),
        code("""
        fig, ax = plt.subplots(figsize=(12, 3.6)); ax.set_xlim(0, 12); ax.set_ylim(0, 3.4); ax.axis("off")
        labels = ["paired samples", "normalize + graphs", "forward pass", "5 losses", "backprop + clip", "EB early stop"]
        colors = ["#d9eaf7", "#d9eaf7", "#e4d7f4", "#fde2cd", "#f5b97f", "#d7ecd9"]
        xs = [0.2, 2.1, 4.0, 5.9, 7.8, 9.7]
        for x, label, color in zip(xs, labels, colors):
            patch = FancyBboxPatch((x, 1.35), 1.55, 0.9, boxstyle="round,pad=0.04", facecolor=color, edgecolor="#333")
            ax.add_patch(patch); ax.text(x+0.775, 1.8, label, ha="center", va="center", fontsize=8.5)
        for left in xs[:-1]:
            ax.add_patch(FancyArrowPatch((left+1.55,1.8),(left+1.9,1.8),arrowstyle="->",mutation_scale=11))
        # Recommended but not implemented in upstream train()
        for x, label in [(7.8, "held-out validate"), (9.7, "save best")]:
            patch = FancyBboxPatch((x, 0.15), 1.55, 0.75, boxstyle="round,pad=0.04", facecolor="#f7f7f7",
                                   edgecolor="#666", linestyle="--")
            ax.add_patch(patch); ax.text(x+0.775, 0.525, label, ha="center", va="center", fontsize=8, color="#444")
        ax.text(6.0, 3.15, "solid = upstream train(); dashed = recommended publication workflow (not in train())",
                ha="center", fontsize=9)
        workflow_path = paths.figures / "session02_training_workflow.png"
        fig.savefig(workflow_path, dpi=180, bbox_inches="tight"); plt.show()
        """),
        md("""
        ## 3. Training is skipped in this tutorial

        Colab and the live workshop do **not** launch `Train_and_Predict.train(...)`. Reasons:

        - official training needs multi-sample CITE-seq assets, substantial CPU/GPU time, and the separate
          DGAT dependency stack;
        - the participant path evaluates **verified pretrained** Tonsil predictions instead.

        Organizers who need to reproduce weights should use the upstream DGAT demos outside this tutorial.
        """),
        code("""
        print("Full DGAT training is skipped in the Colab / workshop path.")
        print("Continue to Part 4 to load verified pretrained Tonsil predictions.")
        """),
        md("""
        ## 4. What a trustworthy training run must save (for later study)

        If you train DGAT later, save train/validation sample IDs, common gene/protein lists, preprocessing
        parameters, random seed, per-epoch component losses, validation correlations, and all four state
        dictionaries. Split by biological sample—not random spots—to avoid spatial and donor leakage. This
        tutorial's committed predictions remain separate from observed evaluation proteins.
        """),
        code("""
        loss_path = paths.results / "session02_dgat_loss_terms.csv"
        loss_table.to_csv(loss_path, index=False)
        manifest = write_checkpoint(
            "2.3", [loss_path, workflow_path],
            summary={"loss_terms": len(loss_table), "full_training_executed": False, "runtime": "colab_skip_training"},
            start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Before moving on, explain why validation must hold out whole samples, which loss directly supervises
        protein imputation, and which two modules are needed for RNA-only inference.
        """),
    ],
)


write(
    "notebooks/session_02/04_load_predictions.ipynb",
    [
        md("""
        # Session 2 · Part 4 — Load and validate pretrained predictions

        **Goal:** use a verified DGAT artifact after learning how it was built and trained. Conference laptops
        load committed official predictions for speed and reproducibility; the organizer command below can
        regenerate them from the RNA graph and saved RNA-encoder/protein-decoder weights.
        """),
        code(BOOTSTRAP),
        md("## 1. Inspect prediction provenance before trusting values"),
        code("""
        from dgat_tutorial.dgat import load_prediction_metadata, load_prediction_table, write_prediction_artifact

        source_path = paths.raw_data / "dgat_predictions.csv"
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing verified prediction table: {source_path}")
        predicted_proteins = load_prediction_table(str(source_path))
        metadata = load_prediction_metadata(source_path)
        if metadata is None:
            raise FileNotFoundError(f"Missing provenance sidecar for {source_path}")
        display(metadata, predicted_proteins.head())
        """),
        md("""
        ## 2. The inference operation represented by this artifact

        ```python
        z_rna = encoder_rna(x_rna, rna_edge_index)
        predicted_protein = decoder_protein(z_rna)
        ```

        To regenerate with official assets, run `scripts/run_official_dgat_prediction.py` in the separate official
        environment. That script discovers the matching common-feature lists and checkpoint layout, then calls
        upstream `Model.Train_and_Predict.protein_predict`.
        """),
        code("""
        output_path = paths.processed_data / "predicted_proteins.csv"
        metadata_path = write_prediction_artifact(
            predicted_proteins, output_path,
            method=str(metadata["method"]), source=str(metadata["source"]),
            evaluation_note=str(metadata["evaluation_note"]),
        )
        manifest = write_checkpoint(
            "2.4", [output_path, metadata_path],
            summary={"spots": len(predicted_proteins), "proteins": predicted_proteins.shape[1]}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Do not evaluate a model on protein values that were used to train or select it. Read the sidecar's
        evaluation note and confirm that spot IDs and protein names match the target dataset.
        """),
    ],
)


write(
    "notebooks/session_02/05_visualize_predictions.ipynb",
    [
        md("""
        # Session 2 · Part 5 — Visualize inferred protein landscapes

        **Goal:** inspect prediction distributions and spatial patterns before calculating accuracy metrics.
        A plausible-looking map is not proof of correctness; it is a diagnostic for range compression, isolated
        artifacts, tissue-edge effects, and expected regional structure.
        """),
        code(BOOTSTRAP),
        md("## 1. Align predictions to spatial coordinates"),
        code("""
        import matplotlib.pyplot as plt

        from dgat_tutorial.checkpoints import preferred_prediction_path
        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.dgat import load_prediction_table
        from dgat_tutorial.plotting import plot_spatial_feature

        dataset = load_tutorial_data(paths.raw_data)
        prediction_path = preferred_prediction_path(paths)
        predicted = load_prediction_table(str(prediction_path))
        common_spots = dataset.spots.index.intersection(predicted.index)
        if common_spots.empty:
            raise ValueError("Spatial data and predictions have no shared spot IDs; check that the assets match.")
        spots = dataset.spots.loc[common_spots]
        predicted = predicted.loc[common_spots]
        print(f"Aligned {len(common_spots)} spots and {predicted.shape[1]} predicted proteins")
        """),
        md("### Figure 8 — Prediction distributions"),
        code("""
        # Prefer robust IQR over variance so a few outlier spots do not dominate feature selection.
        iqr = predicted.quantile(0.75) - predicted.quantile(0.25)
        proteins_to_plot = list(iqr.nlargest(min(4, predicted.shape[1])).index)
        fig, axes = plt.subplots(1, len(proteins_to_plot), figsize=(3.2 * len(proteins_to_plot), 3.2))
        axes = [axes] if len(proteins_to_plot) == 1 else axes
        for ax, protein in zip(axes, proteins_to_plot):
            ax.hist(predicted[protein], bins=30, color="#4c78a8")
            ax.set_title(protein); ax.set_xlabel("predicted abundance"); ax.set_ylabel("spots")
        distribution_path = paths.figures / "session02_prediction_distributions.png"
        fig.tight_layout(); fig.savefig(distribution_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("### Figure 9 — Predicted spatial protein maps"),
        code("""
        n_cols = 2
        n_rows = (len(proteins_to_plot) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(9, 4 * n_rows), squeeze=False)
        # Shared color scale across the selected panel for fair visual comparison.
        shared_vmin = float(predicted[proteins_to_plot].min().min())
        shared_vmax = float(predicted[proteins_to_plot].max().max())
        for ax, protein in zip(axes.ravel(), proteins_to_plot):
            plot_spatial_feature(
                spots, predicted[protein], f"Predicted {protein}", ax=ax, vmin=shared_vmin, vmax=shared_vmax
            )
        for ax in axes.ravel()[len(proteins_to_plot):]: ax.axis("off")
        spatial_path = paths.figures / "session02_predicted_protein_maps.png"
        fig.tight_layout(); fig.savefig(spatial_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        code("""
        manifest = write_checkpoint(
            "2.5", [prediction_path, distribution_path, spatial_path],
            summary={"spots": len(common_spots), "proteins_plotted": proteins_to_plot}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Identify one map worth evaluating and one possible artifact. Then continue to Session 3, where observed
        proteins are used for pointwise correlation, spatial coherence, and side-by-side landscape comparison.
        """),
    ],
)


write(
    "notebooks/session_03/01_correlation_evaluation.ipynb",
    [
        md("""
        # Session 3 · Part 1 — Evaluate pointwise prediction accuracy

        **Goal:** quantify how well inferred abundance tracks measured abundance for every protein. Published
        DGAT reporting emphasized **Spearman correlation and RMSE**; Pearson is retained as a secondary linear
        check. Neither metric alone proves spatial concordance—that is Part 2.

        This is an evaluation notebook: it requires the matching official Tonsil RNA/ADT assets and never pairs
        the committed predictions with any other observations. Before treating Tonsil as held-out accuracy,
        confirm with the DGAT authors that Tonsil was excluded from training and checkpoint selection
        (`tonsil_held_out` in the prediction metadata).
        """),
        code(BOOTSTRAP),
        md("## 1. Align observed and predicted proteins and read provenance"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd

        from dgat_tutorial.checkpoints import preferred_prediction_path
        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.dgat import load_prediction_metadata, load_prediction_table
        from dgat_tutorial.evaluation import (
            alignment_report,
            corresponding_rna_baseline,
            protein_correlations,
        )
        from dgat_tutorial.plotting import plot_correlation_bar
        from dgat_tutorial.processing import normalize_rna_dgat, prepare_evaluation_proteins

        dataset = load_tutorial_data(paths.raw_data)
        prediction_path = preferred_prediction_path(paths)
        predicted = load_prediction_table(str(prediction_path))
        metadata = load_prediction_metadata(prediction_path)
        if metadata:
            print(f"Prediction method: {metadata.get('method')}")
            print(f"tonsil_held_out: {metadata.get('tonsil_held_out')}")
            print(f"training_samples: {metadata.get('training_samples')}")
            print(f"Evaluation note: {metadata.get('evaluation_note')}")
            if metadata.get("tonsil_held_out") is not True:
                print(
                    "WARNING: tonsil_held_out is not True in the sidecar. "
                    "Do not treat these scores as confirmed held-out accuracy."
                )

        # DGAT predictions are on the CLR protein scale used in training/evaluation.
        # Score against CLR-normalized observed ADT (never raw counts).
        observed_raw = dataset.proteins
        report = alignment_report(observed_raw, predicted)
        print(report)
        if report["spots_only_in_observed"] or report["spots_only_in_predicted"]:
            print("WARNING: spot ID sets differ; evaluation uses the intersection and reports mismatches above.")
        if report["proteins_only_in_observed"] or report["proteins_only_in_predicted"]:
            print("WARNING: protein panels differ; only shared proteins are scored.")

        common_spots = observed_raw.index.intersection(predicted.index)
        common_proteins = list(report["proteins_evaluated"])
        if not len(common_spots) or not common_proteins:
            raise ValueError("Observed and predicted tables must share spot IDs and canonical protein names.")
        observed = prepare_evaluation_proteins(observed_raw.loc[common_spots, common_proteins])
        predicted = predicted.loc[common_spots, common_proteins]

        scale_summary = pd.DataFrame({
            "observed_clr_mean": observed.mean(),
            "predicted_mean": predicted.mean(),
            "observed_clr_std": observed.std(),
            "predicted_std": predicted.std(),
        })
        display(scale_summary.head())

        correlations = protein_correlations(observed, predicted)
        correlations
        """),
        md("### Figure 10 — Accuracy across the complete protein panel (Spearman)"),
        code("""
        ax = plot_correlation_bar(correlations, metric="spearman")
        ax.set_title("Per-protein Spearman accuracy (DGAT-style)")
        correlation_bar_path = paths.figures / "session03_prediction_correlations.png"
        plt.tight_layout(); plt.savefig(correlation_bar_path, dpi=160, bbox_inches="tight"); plt.show()

        rmse_summary = correlations[["protein", "spearman", "pearson", "rmse"]].copy()
        print(
            "Panel summary: "
            f"median Spearman={rmse_summary['spearman'].median():.3f}, "
            f"median Pearson={rmse_summary['pearson'].median():.3f}, "
            f"median RMSE={rmse_summary['rmse'].median():.3f}"
        )
        display(rmse_summary.head(10))
        """),
        md("## 2. Corresponding-RNA baseline (nonspatial)"),
        code("""
        # Use the same RNA normalize/scale recipe as DGAT training for a fairer nonspatial baseline.
        # Compare ranks (Spearman) primarily; RMSE across RNA vs CLR-protein units remains secondary.
        transcripts = normalize_rna_dgat(dataset.transcripts.loc[common_spots])
        rna_baseline = corresponding_rna_baseline(transcripts, observed)
        rna_correlations = protein_correlations(observed[rna_baseline.columns], rna_baseline)
        comparison = (
            correlations.set_index("protein")[["spearman", "rmse"]]
            .join(rna_correlations.set_index("protein")[["spearman", "rmse"]], rsuffix="_rna")
            .rename(columns={"spearman": "spearman_dgat", "rmse": "rmse_dgat",
                             "spearman_rna": "spearman_rna", "rmse_rna": "rmse_rna"})
            .dropna()
            .sort_values("spearman_dgat", ascending=False)
        )
        print(f"Corresponding-RNA baseline proteins matched: {len(comparison)}")
        display(comparison.head(10))
        baseline_path = paths.results / "session03_dgat_vs_rna_baseline.csv"
        comparison.to_csv(baseline_path)
        """),
        md("### Figure 11 — Observed versus predicted abundance for representative proteins"),
        code("""
        ranked = correlations.sort_values("spearman")
        representative = list(dict.fromkeys([
            ranked.iloc[-1]["protein"], ranked.iloc[len(ranked)//2]["protein"], ranked.iloc[0]["protein"]
        ]))
        fig, axes = plt.subplots(1, len(representative), figsize=(4 * len(representative), 3.6), squeeze=False)
        for ax, protein in zip(axes.ravel(), representative):
            row = correlations.set_index("protein").loc[protein]
            ax.scatter(observed[protein], predicted[protein], s=10, alpha=0.45, color="#3b7a78")
            lims = [
                min(observed[protein].min(), predicted[protein].min()),
                max(observed[protein].max(), predicted[protein].max()),
            ]
            ax.plot(lims, lims, color="black", linewidth=0.8, linestyle="--")
            ax.set(
                xlabel="observed", ylabel="predicted",
                title=f"{protein}\\nSpearman={row['spearman']:.2f}; RMSE={row['rmse']:.2f}",
            )
            ax.set_aspect("equal", adjustable="box")
        scatter_path = paths.figures / "session03_observed_vs_predicted_scatter.png"
        fig.tight_layout(); fig.savefig(scatter_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        **How to read it:** a high Spearman with a compressed prediction range can still underestimate
        biological extremes (check RMSE and the diagonal). Outliers may be technical, but they can also identify
        rare regions worth inspecting spatially. Avoid summarizing a 31-protein panel with only its mean correlation.
        """),
        code("""
        table_path = paths.results / "session03_prediction_correlations.csv"
        correlations.to_csv(table_path, index=False)
        manifest = write_checkpoint(
            "3.1", [table_path, baseline_path, correlation_bar_path, scatter_path],
            summary={
                "spots": len(common_spots),
                "proteins_evaluated": len(correlations),
                "median_spearman": float(correlations["spearman"].median()),
                "median_rmse": float(correlations["rmse"].median()),
            },
            start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Name a high-, middle-, and low-performing protein by Spearman/RMSE and describe whether errors look like
        noise, range compression, or systematic bias. Note whether DGAT beats the corresponding-RNA baseline.
        """),
    ],
)


write(
    "notebooks/session_03/02_spatial_coherence.ipynb",
    [
        md("""
        # Session 3 · Part 2 — Evaluate spatial coherence

        **Goal:** test whether DGAT preserves local tissue structure. Comparing univariate Moran's I for
        observed versus predicted values shows whether the two matrices have similar *overall autocorrelation*.
        That is **not** the same as spatial concordance: a highly smoothed but misplaced prediction can still
        match Moran's I. We therefore also report residual Moran's I and a simple bivariate Moran's I between
        observed and predicted maps.
        """),
        code(BOOTSTRAP),
        md("## 1. Load aligned observations, predictions, and coordinates"),
        code("""
        import matplotlib.pyplot as plt
        import pandas as pd
        import seaborn as sns

        from dgat_tutorial.checkpoints import preferred_prediction_path
        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.dgat import load_prediction_table
        from dgat_tutorial.evaluation import (
            alignment_report,
            bivariate_morans_i,
            morans_i,
            residual_morans_i,
        )

        from dgat_tutorial.processing import prepare_evaluation_proteins

        dataset = load_tutorial_data(paths.raw_data)
        predicted = load_prediction_table(str(preferred_prediction_path(paths)))
        report = alignment_report(dataset.proteins, predicted)
        print(report)
        common_spots = dataset.spots.index.intersection(dataset.proteins.index).intersection(predicted.index)
        common_proteins = list(report["proteins_evaluated"])
        if not len(common_spots) or not common_proteins:
            raise ValueError("Observed and predicted data do not share both spot IDs and protein names.")
        spots = dataset.spots.loc[common_spots]
        observed = prepare_evaluation_proteins(dataset.proteins.loc[common_spots, common_proteins])
        predicted = predicted.loc[common_spots, common_proteins]
        """),
        md("## 2. Calculate observed/predicted Moran's I plus residual and bivariate concordance"),
        code("""
        moran_table = pd.DataFrame([
            {
                "protein": protein,
                "observed_morans_i": morans_i(observed[protein], spots),
                "predicted_morans_i": morans_i(predicted[protein], spots),
                "residual_morans_i": residual_morans_i(observed[protein], predicted[protein], spots),
                "bivariate_morans_i": bivariate_morans_i(observed[protein], predicted[protein], spots),
            }
            for protein in common_proteins
        ])
        moran_table["difference"] = moran_table["predicted_morans_i"] - moran_table["observed_morans_i"]
        moran_table.sort_values("difference")
        """),
        md("### Figure 12 — Observed versus predicted spatial autocorrelation"),
        code("""
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.scatterplot(data=moran_table, x="observed_morans_i", y="predicted_morans_i", hue="protein", s=70, ax=ax)
        limits = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
        ax.plot(limits, limits, color="black", linewidth=0.8, linestyle="--")
        ax.set_title("Univariate Moran's I (autocorrelation similarity ≠ spatial concordance)")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7, frameon=False)
        moran_scatter_path = paths.figures / "session03_morans_i.png"
        fig.tight_layout(); fig.savefig(moran_scatter_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("### Figure 13 — Smoothing bias and residual spatial structure"),
        code("""
        ordered = moran_table.sort_values("difference")
        fig, axes = plt.subplots(1, 2, figsize=(12, max(4, 0.24 * len(ordered))))
        colors = ["#b65f3c" if value < 0 else "#4c78a8" for value in ordered["difference"]]
        axes[0].barh(ordered["protein"], ordered["difference"], color=colors)
        axes[0].axvline(0, color="black", linewidth=0.8)
        axes[0].set(xlabel="predicted Moran's I − observed Moran's I", title="Smoothing bias")
        ordered_res = moran_table.sort_values("residual_morans_i")
        axes[1].barh(ordered_res["protein"], ordered_res["residual_morans_i"], color="#6b7b8c")
        axes[1].axvline(0, color="black", linewidth=0.8)
        axes[1].set(xlabel="Moran's I of residuals", title="Spatially structured errors")
        difference_path = paths.figures / "session03_morans_i_difference.png"
        fig.tight_layout(); fig.savefig(difference_path, dpi=160, bbox_inches="tight"); plt.show()
        print(
            "Median bivariate Moran's I (observed vs predicted): "
            f"{moran_table['bivariate_morans_i'].median():.3f}"
        )
        """),
        md("""
        Positive univariate differences can indicate over-smoothing; negative differences can indicate lost
        spatial signal. Residual Moran's I near zero suggests unstructured errors; large residual Moran's I
        suggests spatially localized mistakes. Interpretation depends on the neighborhood radius and tissue
        geometry—report the rule and compare proteins under the same rule. Stronger tests (permutation p-values,
        spatial-lag correlation, neighborhood sensitivity) are recommended before publication.
        """),
        code("""
        table_path = paths.results / "session03_morans_i.csv"
        moran_table.to_csv(table_path, index=False)
        manifest = write_checkpoint(
            "3.2", [table_path, moran_scatter_path, difference_path],
            summary={
                "proteins_evaluated": len(moran_table),
                "median_bivariate_morans_i": float(moran_table["bivariate_morans_i"].median()),
            },
            start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Find one protein whose pointwise correlation and spatial-coherence result agree, and one where they tell
        different stories. Prefer residual or bivariate Moran when univariate Moran's I alone looks reassuring.
        """),
    ],
)


write(
    "notebooks/session_03/03_interpret_landscapes.ipynb",
    [
        md("""
        # Session 3 · Part 3 — Interpret inferred molecular landscapes

        **Goal:** move from scores to biological and technical interpretation. We select a well-predicted protein
        by Spearman, identify the RNA feature most associated with its measured abundance, compare four spatial
        maps on shared color scales, and derive an exploratory embedding from the complete inferred protein panel.
        Clustering uses a higher-dimensional PC space; PC1/PC2 are for visualization only.
        """),
        code(BOOTSTRAP),
        md("## 1. Select a protein and a transcript using explicit evidence"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA

        from dgat_tutorial.checkpoints import preferred_prediction_path
        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.dgat import load_prediction_table
        from dgat_tutorial.evaluation import protein_correlations
        from dgat_tutorial.plotting import plot_spatial_feature
        from dgat_tutorial.processing import normalize_rna_dgat, prepare_evaluation_proteins

        dataset = load_tutorial_data(paths.raw_data)
        predicted = load_prediction_table(str(preferred_prediction_path(paths)))
        common_spots = dataset.spots.index.intersection(dataset.proteins.index).intersection(predicted.index)
        if common_spots.empty:
            raise ValueError("Observed and predicted data have no shared spot IDs.")
        spots = dataset.spots.loc[common_spots]
        observed = prepare_evaluation_proteins(dataset.proteins.loc[common_spots])
        predicted = predicted.loc[common_spots]
        transcripts = normalize_rna_dgat(dataset.transcripts.loc[common_spots])

        correlations = protein_correlations(observed, predicted)
        protein = correlations.sort_values("spearman", ascending=False).iloc[0]["protein"]
        gene_correlations = transcripts.corrwith(observed[protein]).dropna().sort_values(key=abs, ascending=False)
        gene = gene_correlations.index[0]
        print(f"Selected protein {protein} (best Spearman on CLR scale); associated transcript {gene} (|r| maximum).")
        """),
        md("""
        ### Figure 14 — Demo2-inspired RNA, observed-protein, and predicted-protein marker panel

        Upstream `Demo2_Predict.ipynb` visualizes PAX5, MS4A1, and PDCD1 RNA alongside DGAT
        predictions. Because this Tonsil dataset also includes measured ADT, we add the observed protein
        as a third view. Each row follows one marker from RNA to measured protein to inferred protein.
        """),
        code("""
        marker_panel = ["PAX5", "MS4A1", "PDCD1"]
        missing_rna = [marker for marker in marker_panel if marker not in transcripts.columns]
        missing_observed = [marker for marker in marker_panel if marker not in observed.columns]
        missing_predicted = [marker for marker in marker_panel if marker not in predicted.columns]
        if missing_rna or missing_observed or missing_predicted:
            raise KeyError(
                "Marker panel is incomplete: "
                f"RNA missing={missing_rna}, observed protein missing={missing_observed}, "
                f"predicted protein missing={missing_predicted}"
            )

        fig, axes = plt.subplots(len(marker_panel), 3, figsize=(12, 10), squeeze=False)
        for row, marker in enumerate(marker_panel):
            # RNA has a different measurement scale. Observed and predicted protein share a row-wise scale.
            protein_vmin = float(min(observed[marker].min(), predicted[marker].min()))
            protein_vmax = float(max(observed[marker].max(), predicted[marker].max()))
            plot_spatial_feature(
                spots, transcripts[marker], f"{marker} RNA", cmap="magma", ax=axes[row, 0]
            )
            plot_spatial_feature(
                spots, observed[marker], f"Observed {marker} protein", ax=axes[row, 1],
                vmin=protein_vmin, vmax=protein_vmax,
            )
            plot_spatial_feature(
                spots, predicted[marker], f"Predicted {marker} protein", ax=axes[row, 2],
                vmin=protein_vmin, vmax=protein_vmax,
            )
        marker_panel_path = paths.figures / "session03_demo2_marker_panel.png"
        fig.tight_layout(); fig.savefig(marker_panel_path, dpi=180, bbox_inches="tight"); plt.show()
        """),
        md("""
        **How to read it:** compare spatial location rather than raw color between the RNA and protein
        columns because their scales differ. Within each row, observed and predicted protein use the same
        color limits, so range compression, missing regions, and over-smoothed predictions are visible.
        Similar RNA and protein maps are possible, but disagreement can reflect translation, trafficking,
        degradation, antibody behavior, or model error.
        """),
        md("### Figure 15 — Transcript, measured protein, inferred protein, and residual"),
        code("""
        residual = predicted[protein] - observed[protein]
        limit = float(np.abs(residual).max())
        shared_vmin = float(min(observed[protein].min(), predicted[protein].min()))
        shared_vmax = float(max(observed[protein].max(), predicted[protein].max()))
        fig, axes = plt.subplots(1, 4, figsize=(17, 4))
        plot_spatial_feature(spots, transcripts[gene], f"Normalized RNA: {gene}", cmap="magma", ax=axes[0])
        plot_spatial_feature(
            spots, observed[protein], f"Observed: {protein}", ax=axes[1], vmin=shared_vmin, vmax=shared_vmax
        )
        plot_spatial_feature(
            spots, predicted[protein], f"Predicted: {protein}", ax=axes[2], vmin=shared_vmin, vmax=shared_vmax
        )
        residual_scatter = axes[3].scatter(spots["x"], spots["y"], c=residual, cmap="coolwarm", vmin=-limit, vmax=limit, s=24)
        axes[3].set(title="Residual (predicted − observed)", xlabel="x", ylabel="y", aspect="equal")
        plt.colorbar(residual_scatter, ax=axes[3], fraction=0.046, pad=0.04)
        landscape_path = paths.figures / "session03_landscape_comparison.png"
        fig.tight_layout(); fig.savefig(landscape_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        **How to read it:** spatially localized residuals may reveal tissue boundaries, composition shifts,
        antibody effects, or a domain shift. Transcript–protein discordance can be biological because translation,
        trafficking, and degradation separate RNA abundance from surface-protein abundance. Observed and predicted
        maps share one color scale so intensity differences are visually comparable.
        """),
        md("### Figure 16 — Downstream structure inferred from the full protein panel"),
        code("""
        scaled = (predicted - predicted.mean(axis=0)) / (predicted.std(axis=0) + 1e-8)
        n_pcs = min(20, scaled.shape[0] - 1, scaled.shape[1])
        pcs = PCA(n_components=n_pcs, random_state=7).fit_transform(scaled)
        # Arbitrary exploratory k; assess stability before biological claims.
        n_clusters = min(6, max(2, len(predicted) // 100))
        clusters = KMeans(n_clusters=n_clusters, n_init=20, random_state=7).fit_predict(pcs)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].scatter(pcs[:, 0], pcs[:, 1], c=clusters, cmap="tab10", s=14)
        axes[0].set(title=f"PCA viz (clustered in {n_pcs} PCs)", xlabel="PC1", ylabel="PC2")
        axes[1].scatter(spots["x"], spots["y"], c=clusters, cmap="tab10", s=18)
        axes[1].set(title="Inferred-protein clusters in tissue", xlabel="x", ylabel="y", aspect="equal")
        embedding_path = paths.figures / "session03_inferred_protein_embedding.png"
        fig.tight_layout(); fig.savefig(embedding_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        These clusters are hypotheses, not validated cell types. Annotate them only after checking marker panels,
        spatial context, robustness to cluster count, and agreement with observed modalities or orthogonal data.
        """),
        code("""
        prompts = (
            "# Session 3 interpretation prompts\\n\\n"
            "- Which proteins are accurate pointwise but spatially over-smoothed?\\n"
            "- Where are residuals spatially localized, and what technical or biological process could explain them?\\n"
            "- Which multi-protein clusters are stable and supported by known marker combinations?\\n"
            "- What donor, batch, antibody, tissue-boundary, or cell-composition effects could mislead evaluation?\\n"
            "- What held-out dataset would best test generalization?\\n"
        )
        prompt_path = paths.results / "session03_interpretation_prompts.md"
        prompt_path.write_text(prompts, encoding="utf-8")
        manifest = write_checkpoint(
            "3.3", [marker_panel_path, landscape_path, embedding_path, prompt_path],
            summary={"transcript": gene, "protein": protein, "exploratory_clusters": n_clusters, "n_pcs": n_pcs},
            start=paths.root,
        )
        print(prompts); print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Next steps

        A complete analysis now has three evidence layers: per-protein accuracy, spatial fidelity, and biological
        interpretation. Before publication, repeat all three on held-out biological samples and include uncertainty
        or replicate variability—not only a single fitted map.
        """),
    ],
)


combine_session_notebooks(
    "notebooks/session_01/01_data_preparation.ipynb",
    "Session 1A — Data preparation",
    "Load and validate the paired Tonsil data, then apply the official DGAT quality-control and normalization workflow.",
    [
        "notebooks/session_01/01_load_and_validate.ipynb",
        "notebooks/session_01/02_quality_control.ipynb",
    ],
)

combine_session_notebooks(
    "notebooks/session_01/02_spatial_context.ipynb",
    "Session 1B — Spatial context",
    "Build spatial and molecular neighborhoods, inspect feature maps, and explore modality structure.",
    [
        "notebooks/session_01/03_spatial_neighborhoods.ipynb",
    ],
)

combine_session_notebooks(
    "notebooks/session_02/01_dgat_model.ipynb",
    "Session 2A — DGAT model",
    "Prepare graph inputs and inspect the DGAT architecture and five-term training objective without launching full training.",
    [
        "notebooks/session_02/01_prepare_inputs.ipynb",
        "notebooks/session_02/02_build_dgat_model.ipynb",
        "notebooks/session_02/03_train_dgat.ipynb",
    ],
)

combine_session_notebooks(
    "notebooks/session_02/02_predictions.ipynb",
    "Session 2B — Pretrained predictions",
    "Load, validate, and visualize the verified pretrained DGAT prediction artifact.",
    [
        "notebooks/session_02/04_load_predictions.ipynb",
        "notebooks/session_02/05_visualize_predictions.ipynb",
    ],
)

combine_session_notebooks(
    "notebooks/session_03/01_quantitative_evaluation.ipynb",
    "Session 3A — Quantitative evaluation",
    "Evaluate inferred proteins with pointwise accuracy metrics and spatial-coherence diagnostics.",
    [
        "notebooks/session_03/01_correlation_evaluation.ipynb",
        "notebooks/session_03/02_spatial_coherence.ipynb",
    ],
)

combine_session_notebooks(
    "notebooks/session_03/02_interpretation.ipynb",
    "Session 3B — Interpretation",
    "Interpret inferred molecular landscapes, residual structure, exploratory clusters, and important limitations.",
    [
        "notebooks/session_03/03_interpret_landscapes.ipynb",
    ],
)

print("Rebuilt six compact Colab teaching notebooks.")
