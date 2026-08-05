"""Rebuild the reader-facing ECCB tutorial notebooks with nbformat.

Run from ``hands-on_tutorial`` after editing this file. Keeping notebook source in
one generator makes substantial tutorial revisions reviewable and avoids manual
JSON editing.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]

BOOTSTRAP = """from pathlib import Path
import sys

current = Path.cwd().resolve()
for candidate in (current, *current.parents):
    if (candidate / "src" / "dgat_tutorial").is_dir():
        tutorial_root = candidate
        break
else:
    raise FileNotFoundError("Start Jupyter inside the hands-on_tutorial directory.")

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


write(
    "notebooks/session_01/01_load_and_validate.ipynb",
    [
        md("""
        # Session 1 · Part 1 — Build the tutorial data object

        **Goal:** load paired spatial RNA and protein measurements into one validated object. We use the
        lightweight `SpatialOmicsData` object. The
        object plays the same teaching role: it keeps observations, modalities, and coordinates aligned.

        By the end you should be able to explain why row identity and coordinate validation must happen
        before normalization or graph construction. Every tutorial section uses the same official Breast
        RNA/ADT pair downloaded during Session 0; there is no generated-data substitute.
        """),
        code(BOOTSTRAP),
        md("## 1. Load all three linked tables"),
        code("""
        import numpy as np
        import pandas as pd

        from dgat_tutorial.data import find_dgat_h5ad_pair, load_tutorial_data
        from dgat_tutorial.processing import validate_modalities

        pair = find_dgat_h5ad_pair(paths.raw_data)
        dataset = load_tutorial_data(paths.raw_data)
        spots = dataset.spots.copy()
        transcripts = dataset.transcripts.select_dtypes(include=[np.number]).copy()
        proteins = dataset.proteins.select_dtypes(include=[np.number]).copy()
        source = f"RNA={pair[0]}, ADT={pair[1]}"

        print(type(dataset).__name__)
        print(f"Source: {source}")
        print(f"spots × genes: {transcripts.shape}; spots × proteins: {proteins.shape}")
        display(spots.head(3), transcripts.iloc[:3, :5], proteins.iloc[:3, :5])
        """),
        md("""
        ## 2. Validate the object

        DGAT assumes that row *i* in RNA, protein, and spatial coordinates is the same biological spot.
        The next call checks ordered IDs, duplicate IDs, coordinates, finite values, and non-negative abundance.
        A shape match alone is not sufficient.
        """),
        code("""
        validate_modalities(spots, transcripts, proteins)
        checks = pd.DataFrame({
            "check": ["ordered IDs match", "x/y coordinates", "finite RNA", "finite protein", "non-negative values"],
            "passed": [
                spots.index.equals(transcripts.index) and spots.index.equals(proteins.index),
                {"x", "y"}.issubset(spots.columns),
                np.isfinite(transcripts.to_numpy()).all(),
                np.isfinite(proteins.to_numpy()).all(),
                (transcripts.to_numpy() >= 0).all() and (proteins.to_numpy() >= 0).all(),
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

        **Goal:** make every data-processing decision visible. We calculate RNA and protein QC separately,
        visualize the distributions, apply transparent data-adaptive filters, normalize RNA with library-size
        scaling + `log1p`, and normalize protein with a centered log-ratio (CLR) transform.

        The quantile threshold below is a compact teaching default, not a universal biological cutoff. Inspect
        the figures and adapt it to the assay, tissue, and expected cell/spot content.
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
            calculate_qc_metrics, choose_qc_thresholds, filter_modalities,
            normalize_total_log1p, clr_normalize, validate_modalities,
        )

        dataset = load_tutorial_data(paths.raw_data)
        spots = dataset.spots.copy()
        transcripts = dataset.transcripts.select_dtypes(include=[np.number]).copy()
        proteins = dataset.proteins.select_dtypes(include=[np.number]).copy()
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
        **How to read it:** low RNA total and low detected-gene counts flag weak transcript capture; protein
        totals and detected proteins reveal a different assay channel and therefore need separate inspection.
        Large upper tails can be biological or technical—do not remove them automatically without context.
        """),
        md("## 2. Choose and apply explicit filters"),
        code("""
        LOWER_QUANTILE = 0.01
        thresholds = choose_qc_thresholds(qc_before, lower_quantile=LOWER_QUANTILE)
        filtered_spots, filtered_rna, filtered_protein, keep_mask = filter_modalities(
            spots, transcripts, proteins, thresholds,
            min_spots_per_gene=1, min_spots_per_protein=1,
        )
        filtering_summary = pd.DataFrame([{
            **thresholds,
            "spots_before": len(spots), "spots_after": len(filtered_spots),
            "genes_before": transcripts.shape[1], "genes_after": filtered_rna.shape[1],
            "proteins_before": proteins.shape[1], "proteins_after": filtered_protein.shape[1],
        }])
        filtering_summary.T
        """),
        md("## 3. Normalize each modality for its measurement process"),
        code("""
        rna_normalized = normalize_total_log1p(filtered_rna, target_sum=10_000)
        protein_normalized = clr_normalize(filtered_protein)

        normalization_checks = pd.DataFrame({
            "quantity": ["RNA target depth before log1p", "mean CLR protein value per spot"],
            "expected": [10_000.0, 0.0],
            "observed_median": [
                float(np.expm1(rna_normalized).sum(axis=1).median()),
                float(protein_normalized.mean(axis=1).median()),
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
        rna_path = paths.processed_data / "rna_log_normalized.csv"
        protein_path = paths.processed_data / "protein_clr_normalized.csv"
        qc_before.assign(kept=keep_mask).to_csv(qc_path)
        filtering_summary.to_csv(filtering_path, index=False)
        rna_normalized.to_csv(rna_path)
        protein_normalized.to_csv(protein_path)
        manifest = write_checkpoint(
            "1.2", [qc_path, filtering_path, rna_path, protein_path, qc_figure_path, rna_norm_path, protein_norm_path],
            summary={"spots_kept": len(filtered_spots), "spots_removed": int((~keep_mask).sum())}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        You should now be able to justify: (1) which spots/features were removed, (2) why RNA and protein
        use different transforms, and (3) why raw values must remain available for QC and auditability.
        """),
    ],
)


write(
    "notebooks/session_01/03_spatial_neighborhoods.ipynb",
    [
        md("""
        # Session 1 · Part 3 — Spatial neighborhoods and exploratory structure

        **Goal:** connect normalized molecular measurements to tissue coordinates. We construct the spatial
        kNN graph DGAT-style models consume, visualize its edges, map variable features, and use PCA only as
        an exploratory downstream view—not as evidence of cell types by itself.
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
        from dgat_tutorial.processing import knn_edge_index, process_modalities

        dataset = load_tutorial_data(paths.raw_data)
        processed = process_modalities(
            dataset.spots,
            dataset.transcripts.select_dtypes(include=[np.number]),
            dataset.proteins.select_dtypes(include=[np.number]),
        )
        spots = processed.spots
        rna = processed.normalized_transcripts
        protein = processed.normalized_proteins
        edge_index = knn_edge_index(spots, n_neighbors=6)
        print(f"Graph: {len(spots)} nodes, {edge_index.shape[1]} directed edges")
        """),
        md("""
        ### Figure 3 — The spatial graph passed to a graph encoder

        Drawing every edge on all ~4,000 spots makes the local neighborhood structure
        unreadable, so this figure splits overview and zoom:

        - **Left:** all spots as nodes (no edges), with a red box marking the corner region.
        - **Right:** undirected 6-nearest-neighbor edges inside that corner.
        - **Highlight:** the red spot is a boundary example; the orange spots are its six
          nearest neighbors. At a tissue corner those neighbors all lie inward, which is
          the local connectivity a graph encoder can attend over.
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
        code("""
        def pca_clusters(matrix, n_clusters=4):
            embedding = PCA(n_components=2, random_state=7).fit_transform(matrix)
            clusters = KMeans(n_clusters=min(n_clusters, len(matrix)), n_init=20, random_state=7).fit_predict(embedding)
            return embedding, clusters


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
        """),
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
        samples provide both modalities. This notebook uses the same official Breast RNA/ADT pair as Session 1,
        so the tensor dimensions and graph construction correspond to the real tutorial dataset.
        """),
        code(BOOTSTRAP),
        md("## 1. Process paired modalities"),
        code("""
        import numpy as np
        import pandas as pd

        from dgat_tutorial.data import find_dgat_h5ad_pair, load_tutorial_data
        from dgat_tutorial.processing import knn_edge_index, process_modalities

        pair = find_dgat_h5ad_pair(paths.raw_data)
        dataset = load_tutorial_data(paths.raw_data)
        processed = process_modalities(
            dataset.spots,
            dataset.transcripts.select_dtypes(include=[np.number]),
            dataset.proteins.select_dtypes(include=[np.number]),
        )
        source = f"RNA={pair[0]}, ADT={pair[1]}"
        """),
        md("## 2. Construct the RNA and protein graph inputs"),
        code("""
        # The official pipeline stores these as PyTorch Geometric HeteroData node/edge types.
        # Here we expose the arrays first so dimensions and alignment are easy to inspect.
        x_rna = processed.normalized_transcripts.to_numpy(dtype=np.float32)
        x_protein = processed.normalized_proteins.to_numpy(dtype=np.float32)
        rna_edge_index = knn_edge_index(processed.spots, n_neighbors=6)
        protein_edge_index = knn_edge_index(processed.spots, n_neighbors=6)

        graph_summary = pd.DataFrame([
            {"graph": "RNA", "nodes": len(x_rna), "node_features": x_rna.shape[1], "directed_edges": rna_edge_index.shape[1]},
            {"graph": "protein", "nodes": len(x_protein), "node_features": x_protein.shape[1], "directed_edges": protein_edge_index.shape[1]},
        ])
        graph_summary
        """),
        md("""
        ## 3. Understand the training and inference handoff

        During training, paired RNA/protein graphs produce two latent representations. During inference, only
        the RNA graph is encoded; its latent representation is sent through the trained protein decoder.

        `RNA graph → RNA encoder → shared latent → protein decoder → predicted proteins`
        """),
        code("""
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
        ## Check

        Both graphs must have the same node count and ordering in paired training data. Feature counts differ:
        RNA nodes carry genes and protein nodes carry ADTs. Edge arrays use integer node positions and have
        shape `2 × number_of_edges`.
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
        from dgat_tutorial.teaching import official_dgat_component_table

        dataset = load_tutorial_data(paths.raw_data)
        numeric_rna = dataset.transcripts.select_dtypes(include=[np.number])
        numeric_protein = dataset.proteins.select_dtypes(include=[np.number])
        common_genes = list(numeric_rna.columns)
        common_proteins = list(numeric_protein.columns)
        HIDDEN_DIM = 512
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
            encoder_rna = GATEncoder(in_channels=len(common_genes), hidden_dim=HIDDEN_DIM, dropout=0.4)
            decoder_rna = Decoder_mRNA(HIDDEN_DIM, len(common_genes), dropout=0)
            encoder_protein = GATEncoder(in_channels=len(common_proteins), hidden_dim=HIDDEN_DIM, dropout=0.4)
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
        # Session 2 · Part 3 — Train DGAT end to end

        **Goal:** connect the four modules to five losses, four optimizers, backpropagation, evaluation, and
        checkpoints. The complete official run is opt-in because conference laptops should use the lightweight
        environment and verified precomputed predictions. The training code remains visible and runnable in the
        separate `eccb-dgat-official` environment.
        """),
        code(BOOTSTRAP),
        md("## 1. Decompose the training objective"),
        code("""
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

        from dgat_tutorial.teaching import official_dgat_loss_table, weighted_training_objective

        loss_table = official_dgat_loss_table()
        loss_table
        """),
        md("""
        The scalar objective is

        $L = \\alpha L_{RNA-recon} + \\beta L_{protein-recon} + \\gamma L_{align}
        + \\delta L_{RNA\\rightarrow protein} + \\epsilon L_{protein\\rightarrow RNA}$.

        The RNA→protein term directly trains the path used at inference. Reconstruction and reverse-direction
        losses regularize the shared representation; alignment encourages paired spots to occupy similar latent
        positions. Always log the components separately—a falling total can hide a failing task.
        """),
        code("""
        example_logged_terms = dict(
            rna_reconstruction=0.42, protein_reconstruction=0.31, latent_alignment=0.08,
            protein_prediction=0.37, rna_prediction=0.46,
        )
        example_total = weighted_training_objective(**example_logged_terms)
        print(f"Example arithmetic check (not a fitted result): total loss = {example_total:.2f}")
        """),
        md("## 2. Inspect one real training step"),
        code("""
        def dgat_training_step(batch, modules, optimizers, rmse_loss, mse_loss, weights):
            # Readable mirror of the upstream DGAT optimization step.
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
            total = sum(weight * loss for weight, loss in zip(weights, losses.values()))
            total.backward()
            for module in modules:
                torch.nn.utils.clip_grad_norm_(module.parameters(), max_norm=1.0)
            for optimizer in optimizers:
                optimizer.step()
            return {name: float(value.detach()) for name, value in losses.items()} | {"total": float(total.detach())}

        print("The function is defined for inspection. It is called by the epoch loop only in the official environment.")
        """),
        md("### Figure 7 — Training, validation, and checkpoint workflow"),
        code("""
        fig, ax = plt.subplots(figsize=(12, 3.2)); ax.set_xlim(0, 12); ax.set_ylim(0, 3); ax.axis("off")
        labels = ["paired samples", "normalize + graphs", "forward pass", "5 losses", "backprop + clip", "validate", "save best"]
        colors = ["#d9eaf7", "#d9eaf7", "#e4d7f4", "#fde2cd", "#f5b97f", "#d7ecd9", "#eeeeee"]
        xs = [0.15, 1.9, 3.65, 5.4, 7.15, 8.9, 10.65]
        for x, label, color in zip(xs, labels, colors):
            patch = FancyBboxPatch((x, 1.0), 1.25, 0.85, boxstyle="round,pad=0.04", facecolor=color, edgecolor="#333")
            ax.add_patch(patch); ax.text(x+0.625, 1.425, label, ha="center", va="center", fontsize=8.5)
        for left in xs[:-1]:
            ax.add_patch(FancyArrowPatch((left+1.25,1.425),(left+1.75,1.425),arrowstyle="->",mutation_scale=11))
        ax.add_patch(FancyArrowPatch((9.5,0.95),(3.9,0.85),connectionstyle="arc3,rad=-0.22",arrowstyle="->",mutation_scale=12))
        ax.text(6.7, 0.22, "repeat epochs; stop/select using held-out samples", ha="center", fontsize=9)
        workflow_path = paths.figures / "session02_training_workflow.png"
        fig.savefig(workflow_path, dpi=180, bbox_inches="tight"); plt.show()
        """),
        md("## 3. Run the official training workflow (opt in)"),
        code("""
        RUN_FULL_TRAINING = False  # set True only in the eccb-dgat-official environment

        if RUN_FULL_TRAINING:
            import anndata as ad
            import importlib
            import sys

            dgat_repo = paths.root / "external" / "DGAT"
            training_data = paths.root / "external" / "DGAT_assets" / "DGAT_training_datasets"
            if not dgat_repo.is_dir() or not training_data.is_dir():
                raise FileNotFoundError("Clone official DGAT and download DGAT_training_datasets first.")
            sys.path.insert(0, str(dgat_repo))
            train_and_predict = importlib.import_module("Model.Train_and_Predict")

            # Replace the glob patterns only if your asset release uses different names.
            rna_files = sorted(training_data.rglob("*RNA*.h5ad"))
            protein_files = sorted(training_data.rglob("*protein*.h5ad")) + sorted(training_data.rglob("*ADT*.h5ad"))
            if not rna_files or not protein_files:
                raise FileNotFoundError("Could not find paired RNA and protein/ADT H5AD files.")
            train_rna = [ad.read_h5ad(path) for path in rna_files]
            train_protein = [ad.read_h5ad(path) for path in protein_files]
            if len(train_rna) != len(train_protein):
                raise ValueError("Pair RNA and protein files by sample before training.")

            model_components = train_and_predict.train(train_rna, train_protein, str(paths.processed_data / "dgat_pyg"))
            print(model_components.keys())
        else:
            print("Full training skipped. Continue to Part 4 for verified pretrained predictions.")
        """),
        md("""
        ## 4. What a trustworthy training run must save

        Save train/validation sample IDs, common gene/protein lists, preprocessing parameters, random seed,
        per-epoch component losses, validation correlations, and all four state dictionaries. Split by biological
        sample—not random spots—to avoid spatial and donor leakage. The tutorial's committed predictions remain
        separate from observed evaluation proteins.
        """),
        code("""
        loss_path = paths.results / "session02_dgat_loss_terms.csv"
        loss_table.to_csv(loss_path, index=False)
        manifest = write_checkpoint(
            "2.3", [loss_path, workflow_path],
            summary={"loss_terms": len(loss_table), "full_training_executed": RUN_FULL_TRAINING}, start=paths.root,
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
        # Session 2 · Part 4 — Run the pretrained inference handoff

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
        proteins_to_plot = list(predicted.var(axis=0).nlargest(min(4, predicted.shape[1])).index)
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
        for ax, protein in zip(axes.ravel(), proteins_to_plot):
            plot_spatial_feature(spots, predicted[protein], f"Predicted {protein}", ax=ax)
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

        **Goal:** quantify how well inferred abundance tracks measured abundance for every protein. Pearson
        correlation emphasizes linear agreement; Spearman correlation emphasizes rank agreement. Neither checks
        whether the predicted tissue pattern is spatially coherent—that is Part 2.

        This is an evaluation notebook: it requires the matching official Breast RNA/ADT assets and never pairs
        the committed predictions with any other observations.
        """),
        code(BOOTSTRAP),
        md("## 1. Align observed and predicted proteins and read provenance"),
        code("""
        import matplotlib.pyplot as plt
        import numpy as np

        from dgat_tutorial.checkpoints import preferred_prediction_path
        from dgat_tutorial.data import load_tutorial_data
        from dgat_tutorial.dgat import load_prediction_metadata, load_prediction_table
        from dgat_tutorial.evaluation import protein_correlations
        from dgat_tutorial.plotting import plot_correlation_bar

        dataset = load_tutorial_data(paths.raw_data)
        prediction_path = preferred_prediction_path(paths)
        predicted = load_prediction_table(str(prediction_path))
        metadata = load_prediction_metadata(prediction_path)
        if metadata:
            print(f"Prediction method: {metadata['method']}")
            print(f"Evaluation note: {metadata['evaluation_note']}")

        common_spots = dataset.proteins.index.intersection(predicted.index)
        common_proteins = dataset.proteins.columns.intersection(predicted.columns)
        if common_spots.empty or common_proteins.empty:
            raise ValueError("Observed and predicted tables must share spot IDs and canonical protein names.")
        observed = dataset.proteins.loc[common_spots, common_proteins]
        predicted = predicted.loc[common_spots, common_proteins]
        correlations = protein_correlations(observed, predicted)
        correlations
        """),
        md("### Figure 10 — Accuracy across the complete protein panel"),
        code("""
        ax = plot_correlation_bar(correlations, metric="pearson")
        ax.set_title("Per-protein pointwise accuracy")
        correlation_bar_path = paths.figures / "session03_prediction_correlations.png"
        plt.tight_layout(); plt.savefig(correlation_bar_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("### Figure 11 — Observed versus predicted abundance for representative proteins"),
        code("""
        ranked = correlations.sort_values("pearson")
        representative = list(dict.fromkeys([
            ranked.iloc[-1]["protein"], ranked.iloc[len(ranked)//2]["protein"], ranked.iloc[0]["protein"]
        ]))
        fig, axes = plt.subplots(1, len(representative), figsize=(4 * len(representative), 3.6), squeeze=False)
        for ax, protein in zip(axes.ravel(), representative):
            ax.scatter(observed[protein], predicted[protein], s=10, alpha=0.45, color="#3b7a78")
            ax.set(xlabel="observed", ylabel="predicted", title=f"{protein}\\nPearson={observed[protein].corr(predicted[protein]):.2f}")
        scatter_path = paths.figures / "session03_observed_vs_predicted_scatter.png"
        fig.tight_layout(); fig.savefig(scatter_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        **How to read it:** a high correlation with a compressed prediction range can still underestimate
        biological extremes. Outliers may be technical, but they can also identify rare regions worth inspecting
        spatially. Avoid summarizing a 31-protein panel with only its mean correlation.
        """),
        code("""
        table_path = paths.results / "session03_prediction_correlations.csv"
        correlations.to_csv(table_path, index=False)
        manifest = write_checkpoint(
            "3.1", [table_path, correlation_bar_path, scatter_path],
            summary={"spots": len(common_spots), "proteins_evaluated": len(correlations)}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Name a high-, middle-, and low-performing protein and describe whether errors look like noise, range
        compression, or systematic bias. Carry those examples into the spatial evaluation.
        """),
    ],
)


write(
    "notebooks/session_03/02_spatial_coherence.ipynb",
    [
        md("""
        # Session 3 · Part 2 — Evaluate spatial coherence

        **Goal:** test whether DGAT preserves local tissue structure. Moran's I compares nearby values under a
        spatial-neighborhood definition: positive values indicate similar neighbors, values near zero indicate
        spatial randomness, and negative values indicate local dissimilarity. This complements—not replaces—
        pointwise correlation.
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
        from dgat_tutorial.evaluation import morans_i

        dataset = load_tutorial_data(paths.raw_data)
        predicted = load_prediction_table(str(preferred_prediction_path(paths)))
        common_spots = dataset.spots.index.intersection(dataset.proteins.index).intersection(predicted.index)
        common_proteins = dataset.proteins.columns.intersection(predicted.columns)
        if common_spots.empty or common_proteins.empty:
            raise ValueError("Observed and predicted data do not share both spot IDs and protein names.")
        spots = dataset.spots.loc[common_spots]
        observed = dataset.proteins.loc[common_spots, common_proteins]
        predicted = predicted.loc[common_spots, common_proteins]
        """),
        md("## 2. Calculate observed and predicted Moran's I with the same neighborhood rule"),
        code("""
        moran_table = pd.DataFrame([
            {"protein": protein,
             "observed_morans_i": morans_i(observed[protein], spots),
             "predicted_morans_i": morans_i(predicted[protein], spots)}
            for protein in common_proteins
        ])
        moran_table["difference"] = moran_table["predicted_morans_i"] - moran_table["observed_morans_i"]
        moran_table.sort_values("difference")
        """),
        md("### Figure 12 — Observed versus predicted spatial coherence"),
        code("""
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.scatterplot(data=moran_table, x="observed_morans_i", y="predicted_morans_i", hue="protein", s=70, ax=ax)
        limits = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
        ax.plot(limits, limits, color="black", linewidth=0.8, linestyle="--")
        ax.set_title("Spatial coherence: points on the line are preserved")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7, frameon=False)
        moran_scatter_path = paths.figures / "session03_morans_i.png"
        fig.tight_layout(); fig.savefig(moran_scatter_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("### Figure 13 — Which proteins are over-smoothed or under-smoothed?"),
        code("""
        ordered = moran_table.sort_values("difference")
        fig, ax = plt.subplots(figsize=(7, max(4, 0.24 * len(ordered))))
        colors = ["#b65f3c" if value < 0 else "#4c78a8" for value in ordered["difference"]]
        ax.barh(ordered["protein"], ordered["difference"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set(xlabel="predicted Moran's I − observed Moran's I", title="Spatial smoothing bias by protein")
        difference_path = paths.figures / "session03_morans_i_difference.png"
        fig.tight_layout(); fig.savefig(difference_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        Positive differences can indicate over-smoothing; negative differences can indicate lost spatial signal.
        Interpretation depends on the graph radius and tissue geometry, so report the neighborhood rule and compare
        proteins under the same rule.
        """),
        code("""
        table_path = paths.results / "session03_morans_i.csv"
        moran_table.to_csv(table_path, index=False)
        manifest = write_checkpoint(
            "3.2", [table_path, moran_scatter_path, difference_path],
            summary={"proteins_evaluated": len(moran_table)}, start=paths.root,
        )
        print(f"Checkpoint written: {manifest}")
        """),
        md("""
        ## Check

        Find one protein whose pointwise correlation and spatial-coherence result agree, and one where they tell
        different stories. The disagreement is often the most useful result.
        """),
    ],
)


write(
    "notebooks/session_03/03_interpret_landscapes.ipynb",
    [
        md("""
        # Session 3 · Part 3 — Interpret inferred molecular landscapes

        **Goal:** move from scores to biological and technical interpretation. We select a well-predicted protein,
        identify the RNA feature most associated with its measured abundance, compare four spatial maps, and
        derive an exploratory embedding from the complete inferred protein panel.
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
        from dgat_tutorial.processing import normalize_total_log1p

        dataset = load_tutorial_data(paths.raw_data)
        predicted = load_prediction_table(str(preferred_prediction_path(paths)))
        common_spots = dataset.spots.index.intersection(dataset.proteins.index).intersection(predicted.index)
        if common_spots.empty:
            raise ValueError("Observed and predicted data have no shared spot IDs.")
        spots = dataset.spots.loc[common_spots]
        observed = dataset.proteins.loc[common_spots]
        predicted = predicted.loc[common_spots]
        transcripts = normalize_total_log1p(dataset.transcripts.loc[common_spots].select_dtypes(include=[np.number]))

        correlations = protein_correlations(observed, predicted)
        protein = correlations.iloc[0]["protein"]
        gene_correlations = transcripts.corrwith(observed[protein]).dropna().sort_values(key=abs, ascending=False)
        gene = gene_correlations.index[0]
        print(f"Selected protein {protein} (best Pearson); associated transcript {gene} (|r| maximum).")
        """),
        md("### Figure 14 — Transcript, measured protein, inferred protein, and residual"),
        code("""
        residual = predicted[protein] - observed[protein]
        limit = float(np.abs(residual).max())
        fig, axes = plt.subplots(1, 4, figsize=(17, 4))
        plot_spatial_feature(spots, transcripts[gene], f"Normalized RNA: {gene}", cmap="magma", ax=axes[0])
        plot_spatial_feature(spots, observed[protein], f"Observed: {protein}", ax=axes[1])
        plot_spatial_feature(spots, predicted[protein], f"Predicted: {protein}", ax=axes[2])
        residual_scatter = axes[3].scatter(spots["x"], spots["y"], c=residual, cmap="coolwarm", vmin=-limit, vmax=limit, s=24)
        axes[3].set(title="Residual (predicted − observed)", xlabel="x", ylabel="y", aspect="equal")
        plt.colorbar(residual_scatter, ax=axes[3], fraction=0.046, pad=0.04)
        landscape_path = paths.figures / "session03_landscape_comparison.png"
        fig.tight_layout(); fig.savefig(landscape_path, dpi=160, bbox_inches="tight"); plt.show()
        """),
        md("""
        **How to read it:** spatially localized residuals may reveal tissue boundaries, composition shifts,
        antibody effects, or a domain shift. Transcript–protein discordance can be biological because translation,
        trafficking, and degradation separate RNA abundance from surface-protein abundance.
        """),
        md("### Figure 15 — Downstream structure inferred from the full protein panel"),
        code("""
        scaled = (predicted - predicted.mean(axis=0)) / (predicted.std(axis=0) + 1e-8)
        embedding = PCA(n_components=2, random_state=7).fit_transform(scaled)
        n_clusters = min(6, max(2, len(predicted) // 100))
        clusters = KMeans(n_clusters=n_clusters, n_init=20, random_state=7).fit_predict(embedding)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].scatter(embedding[:, 0], embedding[:, 1], c=clusters, cmap="tab10", s=14)
        axes[0].set(title="PCA of inferred protein panel", xlabel="PC1", ylabel="PC2")
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
            "3.3", [landscape_path, embedding_path, prompt_path],
            summary={"transcript": gene, "protein": protein, "exploratory_clusters": n_clusters}, start=paths.root,
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


print("Rebuilt all Session 1–3 tutorial notebooks.")
