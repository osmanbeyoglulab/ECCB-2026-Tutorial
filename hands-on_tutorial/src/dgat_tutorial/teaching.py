from __future__ import annotations

import pandas as pd


def official_dgat_component_table(
    n_genes: int,
    protein_names: list[str],
    hidden_dim: int = 512,
) -> pd.DataFrame:
    """Summarize the four trainable modules in the official DGAT implementation."""

    return pd.DataFrame(
        [
            {
                "module": "RNA GAT encoder",
                "input": f"{n_genes} RNA features + RNA kNN edges",
                "main_layers": "GAT 2048 → GAT 1024 → GAT latent; residuals, LayerNorm, feature attention",
                "output": f"{hidden_dim}-D shared latent z_RNA",
            },
            {
                "module": "Protein GAT encoder",
                "input": f"{len(protein_names)} proteins + protein kNN edges",
                "main_layers": "same GAT encoder design, separately learned weights",
                "output": f"{hidden_dim}-D shared latent z_protein",
            },
            {
                "module": "RNA decoder",
                "input": "either shared latent",
                "main_layers": f"MLP {hidden_dim} → 512 → 1024 → {n_genes}; residuals and LayerNorm",
                "output": "reconstructed/predicted RNA",
            },
            {
                "module": "Protein decoder",
                "input": "either shared latent",
                "main_layers": "shared MLP 512 → 256, then one 256 → 64 → 1 branch per protein",
                "output": "reconstructed/predicted protein panel",
            },
        ]
    )


def official_dgat_loss_table() -> pd.DataFrame:
    """Describe the five objectives combined by the upstream DGAT training loop."""

    return pd.DataFrame(
        [
            ("RNA reconstruction", "RMSE(D_RNA(z_RNA), X_RNA)", "keeps RNA latent informative"),
            ("Protein reconstruction", "RMSE(D_protein(z_protein), X_protein)", "keeps protein latent informative"),
            ("Latent alignment", "MSE(z_RNA, z_protein)", "puts paired modalities in a shared space"),
            ("RNA → protein prediction", "RMSE(D_protein(z_RNA), X_protein)", "trains the inference path used on ST data"),
            ("Protein → RNA prediction", "RMSE(D_RNA(z_protein), X_RNA)", "regularizes cross-modal correspondence"),
        ],
        columns=["loss", "formula", "role"],
    )


def weighted_training_objective(
    rna_reconstruction: float,
    protein_reconstruction: float,
    latent_alignment: float,
    protein_prediction: float,
    rna_prediction: float,
    weights: tuple[float, float, float, float, float] = (1.0, 1.0, 1.0, 1.0, 1.0),
) -> float:
    """Compute the scalar five-term DGAT objective for a logged training step."""

    terms = (
        rna_reconstruction,
        protein_reconstruction,
        latent_alignment,
        protein_prediction,
        rna_prediction,
    )
    return float(sum(weight * term for weight, term in zip(weights, terms, strict=True)))
