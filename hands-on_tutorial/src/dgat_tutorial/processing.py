"""Spatial omics preprocessing and graph construction aligned with official DGAT.

Two official preprocessing paths exist in ``external/DGAT/utils/Preprocessing.py``:

- **Training / paired CITE-seq:** ``qc_control_cytassist`` + ``normalize``
  (700 genes, MT < 35%, 2.5% gene prevalence, optional encoding-gene keep list,
  RNA scale clip 10, protein CLR).
- **ST inference:** ``preprocess_ST`` (min_genes=700 + RNA normalize/scale only;
  no MT filter, no gene prevalence filter, no protein CLR).

Graph topology mirrors ``external/DGAT/utils/Graph_utils.py``
(``create_pyg_data`` / ``build_knn_adj``).
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

# Official DGAT defaults (utils/Preprocessing.py qc_control_cytassist + normalize).
DGAT_MIN_GENES: int = 700
DGAT_MAX_MT_PCT: float = 35.0
DGAT_MIN_CELLS_FRACTION: float = 0.025
DGAT_RNA_TARGET_SUM: float = 10_000.0
DGAT_RNA_SCALE_MAX: float = 10.0

# Official DGAT graph hyper-parameters (utils/Graph_utils.py create_pyg_data).
DGAT_SPATIAL_KNN_K: int = 6
DGAT_MOLECULAR_KNN_K: int = 10
DGAT_RNA_PCA_FEATURE_THRESHOLD: int = 1500
DGAT_RNA_PCA_VARIANCE: float = 0.85


@dataclass(frozen=True)
class ProcessedSpatialOmics:
    """Raw and normalized modalities kept together for a transparent tutorial handoff."""

    spots: pd.DataFrame
    raw_transcripts: pd.DataFrame
    raw_proteins: pd.DataFrame
    normalized_transcripts: pd.DataFrame
    normalized_proteins: pd.DataFrame
    qc: pd.DataFrame


def _load_official_preprocessing_module(dgat_repo_dir: str | Path):
    """Load DGAT's own ``utils/Preprocessing.py`` from an explicit checkout."""

    preprocessing_path = Path(dgat_repo_dir) / "utils" / "Preprocessing.py"
    if not preprocessing_path.is_file():
        raise FileNotFoundError(
            f"Official DGAT preprocessing was not found at {preprocessing_path}. "
            "Clone https://github.com/osmanbeyoglulab/DGAT into external/DGAT."
        )
    spec = importlib.util.spec_from_file_location("_official_dgat_preprocessing", preprocessing_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load official DGAT preprocessing from {preprocessing_path}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_modalities_official_dgat(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    *,
    dgat_repo_dir: str | Path,
    min_genes: int = DGAT_MIN_GENES,
    max_mt_pct: float = DGAT_MAX_MT_PCT,
    remove_isotype_controls: bool = True,
) -> ProcessedSpatialOmics:
    """Preprocess paired data by directly calling the upstream DGAT functions.

    This is the reproducibility path used by the notebooks. It invokes
    ``qc_control_cytassist`` and ``normalize`` from the requested DGAT checkout;
    it does not reproduce their filtering or normalization logic locally.
    """

    validate_modalities(spots, transcripts, proteins)
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("Official DGAT preprocessing requires `anndata`.") from exc

    official = _load_official_preprocessing_module(dgat_repo_dir)
    rna = ad.AnnData(
        X=transcripts.to_numpy(dtype=float),
        obs=spots.copy(),
        var=pd.DataFrame(index=transcripts.columns.astype(str)),
    )
    protein = ad.AnnData(
        X=proteins.to_numpy(dtype=float),
        obs=pd.DataFrame(index=proteins.index.astype(str)),
        var=pd.DataFrame(index=proteins.columns.astype(str)),
    )
    rna.obs_names = transcripts.index.astype(str)
    protein.obs_names = proteins.index.astype(str)

    # preprocess_train_list cleans ADT labels before deriving the encoding-gene
    # keep-list and calling qc_control_cytassist for every training sample.
    protein.var_names = official.clean_protein_names(protein.var_names)
    if protein.var_names.has_duplicates:
        raise ValueError("Official DGAT protein-name cleaning produced duplicate labels.")
    encoding_genes = [
        gene
        for protein_name in protein.var_names
        for gene in rna.var_names
        if protein_name.split("_")[0] == gene.split("_")[0]
    ]
    rna, protein = official.qc_control_cytassist(
        rna,
        protein,
        min_genes=min_genes,
        max_mt_pct=max_mt_pct,
        remove_isotype=remove_isotype_controls,
        gene_to_keep_list=encoding_genes,
    )
    rna, protein = official.normalize(rna, protein)

    def frame(matrix, index, columns) -> pd.DataFrame:
        values = matrix.toarray() if hasattr(matrix, "toarray") else np.asarray(matrix)
        return pd.DataFrame(values, index=index, columns=columns)

    obs_names = pd.Index(rna.obs_names)
    raw_rna = frame(rna.layers["raw"], obs_names, rna.var_names)
    raw_protein = frame(protein.layers["raw"], obs_names, protein.var_names)
    normalized_rna = frame(rna.X, obs_names, rna.var_names)
    normalized_protein = frame(protein.X, obs_names, protein.var_names)
    filtered_spots = spots.copy()
    filtered_spots.index = filtered_spots.index.astype(str)
    filtered_spots = filtered_spots.loc[obs_names]
    return ProcessedSpatialOmics(
        spots=filtered_spots,
        raw_transcripts=raw_rna,
        raw_proteins=raw_protein,
        normalized_transcripts=normalized_rna,
        normalized_proteins=normalized_protein,
        qc=calculate_qc_metrics(raw_rna, raw_protein),
    )


def validate_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
) -> None:
    """Fail early when identifiers, coordinates, or measurement values are invalid."""

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("Spatial metadata must include x and y coordinates.")

    coordinates = spots[["x", "y"]].to_numpy(dtype=float)
    if not np.isfinite(coordinates).all():
        raise ValueError("Spatial x and y coordinates must be finite numeric values.")

    for label, table in (("spots", spots), ("transcripts", transcripts), ("proteins", proteins)):
        if table.index.has_duplicates:
            raise ValueError(f"{label} contains duplicate observation IDs.")
        if table.empty:
            raise ValueError(f"{label} is empty.")
    if not spots.index.equals(transcripts.index) or not spots.index.equals(proteins.index):
        raise ValueError("Spots, transcripts, and proteins must have identical ordered observation IDs.")
    for label, table in (("transcripts", transcripts), ("proteins", proteins)):
        values = table.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"{label} contains NaN or infinite values.")
        if (values < 0).any():
            raise ValueError(f"{label} contains negative values; expected non-negative abundance values.")


def _is_mt_gene(gene_name: str) -> bool:
    return str(gene_name).startswith("MT-")


def _is_isotype_control(protein_name: str) -> bool:
    """Return True for ADT isotype controls removed in official DGAT QC."""

    name = str(protein_name)
    return (
        name.startswith("mouse_")
        or name.startswith("rat_")
        or name.startswith("mouse.")
        or name.startswith("rat.")
    )


def calculate_qc_metrics(transcripts: pd.DataFrame, proteins: pd.DataFrame) -> pd.DataFrame:
    """Calculate spot-level RNA and protein quality-control metrics.

    When mitochondrial genes (names starting with ``MT-``) are present, ``mt_pct`` is
    computed as in Scanpy's ``pct_counts_mt`` metric used by official DGAT QC.
    """

    rna_total = transcripts.sum(axis=1)
    mt_columns = [column for column in transcripts.columns if _is_mt_gene(column)]
    if mt_columns:
        mt_counts = transcripts.loc[:, mt_columns].sum(axis=1)
        mt_pct = (mt_counts / rna_total.replace(0, np.nan) * 100.0).fillna(0.0)
    else:
        mt_pct = pd.Series(0.0, index=transcripts.index, name="mt_pct")

    return pd.DataFrame(
        {
            "rna_total": rna_total,
            "genes_detected": (transcripts > 0).sum(axis=1),
            "mt_pct": mt_pct,
            "protein_total": proteins.sum(axis=1),
            "proteins_detected": (proteins > 0).sum(axis=1),
        },
        index=transcripts.index,
    )


def dgat_qc_thresholds(n_obs: int) -> dict[str, float | int]:
    """Return fixed QC thresholds from official DGAT ``qc_control_cytassist``."""

    if n_obs <= 0:
        raise ValueError("n_obs must be positive.")
    return {
        "min_genes_detected": DGAT_MIN_GENES,
        "max_mt_pct": DGAT_MAX_MT_PCT,
        "min_spots_per_gene": max(1, int(np.ceil(n_obs * DGAT_MIN_CELLS_FRACTION))),
    }


def choose_qc_thresholds(qc: pd.DataFrame, lower_quantile: float = 0.01) -> dict[str, float]:
    """Return data-adaptive teaching thresholds; inspect plots before accepting them."""

    if not 0 <= lower_quantile < 0.5:
        raise ValueError("lower_quantile must be between 0 and 0.5.")
    return {
        "min_rna_total": float(qc["rna_total"].quantile(lower_quantile)),
        "min_genes_detected": float(qc["genes_detected"].quantile(lower_quantile)),
        "min_protein_total": float(qc["protein_total"].quantile(lower_quantile)),
        "min_proteins_detected": float(qc["proteins_detected"].quantile(lower_quantile)),
    }


def filter_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    thresholds: dict[str, float],
    *,
    min_spots_per_gene: int = 1,
    min_spots_per_protein: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Filter low-quality observations and rarely detected features in both modalities.

    This teaching helper accepts arbitrary thresholds (for example quantile-based cutoffs).
    For official DGAT QC, use :func:`filter_modalities_dgat` or :func:`process_modalities`.
    """

    qc = calculate_qc_metrics(transcripts, proteins)
    keep_spots = (
        (qc["rna_total"] >= thresholds["min_rna_total"])
        & (qc["genes_detected"] >= thresholds["min_genes_detected"])
        & (qc["protein_total"] >= thresholds["min_protein_total"])
        & (qc["proteins_detected"] >= thresholds["min_proteins_detected"])
    )
    kept_ids = qc.index[keep_spots]
    filtered_transcripts = transcripts.loc[kept_ids]
    filtered_proteins = proteins.loc[kept_ids]
    keep_genes = (filtered_transcripts > 0).sum(axis=0) >= min_spots_per_gene
    keep_proteins = (filtered_proteins > 0).sum(axis=0) >= min_spots_per_protein
    return (
        spots.loc[kept_ids].copy(),
        filtered_transcripts.loc[:, keep_genes].copy(),
        filtered_proteins.loc[:, keep_proteins].copy(),
        keep_spots,
    )


def filter_modalities_dgat(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    *,
    min_genes: int = DGAT_MIN_GENES,
    max_mt_pct: float = DGAT_MAX_MT_PCT,
    min_cells_fraction: float = DGAT_MIN_CELLS_FRACTION,
    remove_isotype_controls: bool = True,
    gene_to_keep_list: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Apply official DGAT spot/gene/protein filtering (``qc_control_cytassist``).

    When ``gene_to_keep_list`` is provided (official training path: protein-coding /
    encoding genes paired to the common protein panel), those genes are retained even
    if they fall below the prevalence threshold — matching upstream ``gene_to_keep_list``.
    """

    n_obs = len(transcripts)
    min_spots_per_gene = max(1, int(np.ceil(n_obs * min_cells_fraction)))
    keep_genes = (transcripts > 0).sum(axis=0) >= min_spots_per_gene
    if gene_to_keep_list is not None:
        force_keep = transcripts.columns.isin(gene_to_keep_list)
        keep_genes = keep_genes | force_keep
    filtered_transcripts = transcripts.loc[:, keep_genes].copy()

    qc = calculate_qc_metrics(filtered_transcripts, proteins)
    keep_spots = (qc["genes_detected"] >= min_genes) & (qc["mt_pct"] < max_mt_pct)
    kept_ids = qc.index[keep_spots]

    filtered_spots = spots.loc[kept_ids].copy()
    filtered_transcripts = filtered_transcripts.loc[kept_ids]
    filtered_proteins = proteins.loc[kept_ids].copy()

    if remove_isotype_controls:
        protein_keep = [column for column in filtered_proteins.columns if not _is_isotype_control(column)]
        filtered_proteins = filtered_proteins.loc[:, protein_keep]

    return filtered_spots, filtered_transcripts, filtered_proteins, keep_spots


def normalize_total_log1p(matrix: pd.DataFrame, target_sum: float = DGAT_RNA_TARGET_SUM) -> pd.DataFrame:
    """Library-size normalize every spot to ``target_sum`` and apply log(1+x)."""

    library_size = matrix.sum(axis=1).replace(0, np.nan)
    normalized = matrix.div(library_size, axis=0).mul(target_sum)
    normalized = np.log1p(normalized).fillna(0.0)
    return pd.DataFrame(normalized, index=matrix.index, columns=matrix.columns)


def scale_genes(matrix: pd.DataFrame, *, max_value: float = DGAT_RNA_SCALE_MAX) -> pd.DataFrame:
    """Gene-wise zero-center and scale to unit variance, clipping to ``[-max_value, max_value]``.

    Matches ``scanpy.pp.scale(adata, max_value=10)`` used in official DGAT normalization.
    """

    values = matrix.to_numpy(dtype=float)
    mean = values.mean(axis=0)
    std = values.std(axis=0, ddof=1)
    std = np.where(std == 0.0, 1.0, std)
    scaled = (values - mean) / std
    if max_value is not None:
        scaled = np.clip(scaled, -max_value, max_value)
    return pd.DataFrame(scaled, index=matrix.index, columns=matrix.columns)


def normalize_rna_dgat(
    matrix: pd.DataFrame,
    *,
    target_sum: float = DGAT_RNA_TARGET_SUM,
    scale_max_value: float = DGAT_RNA_SCALE_MAX,
) -> pd.DataFrame:
    """Official DGAT RNA normalization: total-count normalize, log1p, then gene scaling."""

    return scale_genes(
        normalize_total_log1p(matrix, target_sum=target_sum),
        max_value=scale_max_value,
    )


def clr_normalize(matrix: pd.DataFrame) -> pd.DataFrame:
    """Centered log-ratio normalization matching official ``muon.prot.pp.clr``.

    Official DGAT calls ``pt.pp.clr(pdata)`` with muon's default ``axis=0``:
    for each protein (column), divide by the geometric mean across spots and
    then ``log1p``. That is **not** the per-spot compositional CLR (axis=1).
    """

    try:
        import anndata as ad
        from muon.prot import pp as prot_pp
    except ImportError:
        values = matrix.astype(float).to_numpy()
        # Dense reimplementation of muon.prot.pp.clr(..., axis=0).
        geo = np.exp(np.log1p(values).sum(axis=0, keepdims=True) / values.shape[0])
        normalized = np.log1p(values / geo)
        return pd.DataFrame(normalized, index=matrix.index, columns=matrix.columns)

    adata = ad.AnnData(matrix.astype(float).to_numpy())
    adata.obs_names = matrix.index.astype(str)
    adata.var_names = matrix.columns.astype(str)
    prot_pp.clr(adata, axis=0)
    values = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    return pd.DataFrame(values, index=matrix.index, columns=matrix.columns)


def encoding_genes_for_proteins(gene_names: list[str] | pd.Index, protein_names: list[str] | pd.Index) -> list[str]:
    """Return RNA genes whose leading token matches a protein name (official training keep-list)."""

    gene_names = [str(name) for name in gene_names]
    protein_tokens = {str(name).split("_")[0] for name in protein_names}
    return [gene for gene in gene_names if gene.split("_")[0] in protein_tokens]


def prepare_evaluation_proteins(proteins: pd.DataFrame) -> pd.DataFrame:
    """CLR-normalize observed ADT so evaluation matches the DGAT protein scale."""

    return clr_normalize(proteins)


def process_modalities(
    spots: pd.DataFrame,
    transcripts: pd.DataFrame,
    proteins: pd.DataFrame,
    *,
    min_genes: int = DGAT_MIN_GENES,
    max_mt_pct: float = DGAT_MAX_MT_PCT,
    min_cells_fraction: float = DGAT_MIN_CELLS_FRACTION,
    remove_isotype_controls: bool = True,
    gene_to_keep_list: list[str] | None = None,
    rna_target_sum: float = DGAT_RNA_TARGET_SUM,
    rna_scale_max_value: float = DGAT_RNA_SCALE_MAX,
) -> ProcessedSpatialOmics:
    """Validate, filter with official *training* CytAssist QC, and normalize paired data.

    For ST-only inference preprocessing (no MT / prevalence filters), use the official
    ``preprocess_ST`` path used by the upstream pretrained inference workflow.
    """

    validate_modalities(spots, transcripts, proteins)
    if gene_to_keep_list is None:
        gene_to_keep_list = encoding_genes_for_proteins(transcripts.columns, proteins.columns)
    filtered_spots, filtered_transcripts, filtered_proteins, _ = filter_modalities_dgat(
        spots,
        transcripts,
        proteins,
        min_genes=min_genes,
        max_mt_pct=max_mt_pct,
        min_cells_fraction=min_cells_fraction,
        remove_isotype_controls=remove_isotype_controls,
        gene_to_keep_list=gene_to_keep_list,
    )
    filtered_qc = calculate_qc_metrics(filtered_transcripts, filtered_proteins)
    return ProcessedSpatialOmics(
        spots=filtered_spots,
        raw_transcripts=filtered_transcripts,
        raw_proteins=filtered_proteins,
        normalized_transcripts=normalize_rna_dgat(
            filtered_transcripts,
            target_sum=rna_target_sum,
            scale_max_value=rna_scale_max_value,
        ),
        normalized_proteins=clr_normalize(filtered_proteins),
        qc=filtered_qc,
    )


def _build_knn_adjacency(
    features: np.ndarray,
    k: int,
    *,
    apply_pca: bool = False,
    variance: float = DGAT_RNA_PCA_VARIANCE,
) -> np.ndarray:
    """Build a directed kNN adjacency with self-loops (official ``build_knn_adj``)."""

    matrix = np.asarray(features, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("features must be a 2D array.")
    n_obs = matrix.shape[0]
    if n_obs == 0:
        raise ValueError("At least one observation is required to construct a graph.")
    if k <= 0:
        raise ValueError("k must be positive.")

    if apply_pca and matrix.shape[1] > DGAT_RNA_PCA_FEATURE_THRESHOLD:
        pca = PCA(n_components=variance, svd_solver="full")
        matrix = pca.fit_transform(matrix)

    neighbor_count = min(k, n_obs)
    nbrs = NearestNeighbors(n_neighbors=neighbor_count, algorithm="ball_tree").fit(matrix)
    _, indices = nbrs.kneighbors(matrix)

    adjacency = np.zeros((n_obs, n_obs), dtype=np.float32)
    for row, neighbors in enumerate(indices):
        adjacency[row, neighbors] = 1.0
    adjacency += np.eye(n_obs, dtype=np.float32)
    return adjacency


def _adjacency_to_edge_index(adjacency: np.ndarray) -> np.ndarray:
    """Convert a weighted adjacency matrix to a directed COO edge index."""

    sources, targets = np.nonzero(adjacency)
    if sources.size == 0:
        raise ValueError("Adjacency matrix has no edges.")
    return np.vstack([sources, targets]).astype(np.int64)


def _union_adjacency(*adjacency_matrices: np.ndarray) -> np.ndarray:
    """Union edges from multiple adjacency matrices (official DGAT graph addition)."""

    if not adjacency_matrices:
        raise ValueError("At least one adjacency matrix is required.")
    stacked = np.stack(adjacency_matrices, axis=0)
    return (stacked.sum(axis=0) > 0).astype(np.float32)


def build_dgat_graphs(
    spots: pd.DataFrame,
    rna_features: pd.DataFrame,
    protein_features: pd.DataFrame,
    *,
    spatial_k: int = DGAT_SPATIAL_KNN_K,
    molecular_k: int = DGAT_MOLECULAR_KNN_K,
    rna_pca_variance: float = DGAT_RNA_PCA_VARIANCE,
) -> dict[str, np.ndarray]:
    """Build official DGAT spatial/molecular graphs and return PyG-style edge indices.

    Graph topology matches ``utils/Graph_utils.py:create_pyg_data``:

    - spatial kNN with ``k=6`` on ``(x, y)`` coordinates
    - RNA molecular kNN with ``k=10`` (PCA when ``n_features > 1500``)
    - protein molecular kNN with ``k=10`` without PCA
    - modality graphs are unions of spatial and molecular neighbors, with self-loops
    """

    if not {"x", "y"}.issubset(spots.columns):
        raise ValueError("spots must include x and y coordinates.")
    if len(spots) != len(rna_features) or len(spots) != len(protein_features):
        raise ValueError("spots, rna_features, and protein_features must have the same number of rows.")
    if len(spots) < 1:
        raise ValueError("At least one observation is required to construct graphs.")

    spatial = spots[["x", "y"]].to_numpy(dtype=float)
    rna_matrix = rna_features.to_numpy(dtype=float)
    protein_matrix = protein_features.to_numpy(dtype=float)

    spatial_adjacency = _build_knn_adjacency(spatial, spatial_k, apply_pca=False)
    rna_molecular_adjacency = _build_knn_adjacency(
        rna_matrix,
        molecular_k,
        apply_pca=True,
        variance=rna_pca_variance,
    )
    protein_molecular_adjacency = _build_knn_adjacency(protein_matrix, molecular_k, apply_pca=False)

    rna_adjacency = _union_adjacency(spatial_adjacency, rna_molecular_adjacency)
    protein_adjacency = _union_adjacency(spatial_adjacency, protein_molecular_adjacency)

    return {
        "spatial_edge_index": _adjacency_to_edge_index(spatial_adjacency),
        "rna_molecular_edge_index": _adjacency_to_edge_index(rna_molecular_adjacency),
        "protein_molecular_edge_index": _adjacency_to_edge_index(protein_molecular_adjacency),
        "rna_edge_index": _adjacency_to_edge_index(rna_adjacency),
        "protein_edge_index": _adjacency_to_edge_index(protein_adjacency),
    }


def knn_edge_index(coordinates: pd.DataFrame, n_neighbors: int = DGAT_SPATIAL_KNN_K) -> np.ndarray:
    """Build a directed spatial kNN edge index of ``n_neighbors`` *other* spots (no self-loops).

    Visualization / teaching helper only. Official DGAT ``build_knn_adj`` requests
    ``k`` neighbors from sklearn (which usually includes self as nearest) and then
    adds an identity term again. Encoders consume the **spatial ∪ molecular** union
    graphs from :func:`build_dgat_graphs`, not this spatial-only view.
    """

    xy = coordinates[["x", "y"]].to_numpy(dtype=float)
    n_obs = len(xy)
    if n_obs < 2:
        raise ValueError("At least two observations are required to construct a graph.")
    if n_neighbors <= 0:
        raise ValueError("n_neighbors must be positive.")

    neighbor_count = min(n_neighbors + 1, n_obs)
    nbrs = NearestNeighbors(n_neighbors=neighbor_count, algorithm="ball_tree").fit(xy)
    _, indices = nbrs.kneighbors(xy)

    sources = np.repeat(np.arange(n_obs), neighbor_count - 1)
    targets = indices[:, 1:].reshape(-1)
    return np.vstack([sources, targets]).astype(np.int64)
