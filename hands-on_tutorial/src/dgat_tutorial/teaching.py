from __future__ import annotations

import pandas as pd


# Official training hyperparameters from external/DGAT/Model/Train_and_Predict.py
DGAT_HIDDEN_DIM: int = 1024
DGAT_ENCODER_DROPOUT: float = 0.3
# Note: GATEncoder.__init__ defaults dropout=0.4 in Model/dgat.py, but training
# instantiates encoders with dropout_rate=0.3 from Train_and_Predict.py.

# Coefficients actually used by the training objective in Train_and_Predict.py.
DGAT_TRAIN_LOSS_WEIGHTS: tuple[float, float, float, float, float] = (5.0, 1.0, 1.0, 3.0, 1.0)
DGAT_LOSS_SOFT_THRESHOLD: float = 0.015
DGAT_ENCODER_LR: float = 5e-4
DGAT_DECODER_LR: float = 1e-4
DGAT_ENCODER_WEIGHT_DECAY: float = 2e-5
DGAT_DECODER_WEIGHT_DECAY: float = 1e-5
DGAT_LR_DECAY_FACTOR: float = 0.8
DGAT_LR_DECAY_INTERVAL: int = 10
DGAT_MAX_EPOCHS: int = 100
DGAT_WARMUP_EPOCHS: int = 50
DGAT_EB_THRESHOLD: float = 0.96
# Public pretrained ST checkpoints used by Demo3_Predict_ST.ipynb
DGAT_PRETRAINED_GENE_COUNT: int = 11_535
DGAT_PRETRAINED_PROTEIN_COUNT: int = 31


def official_dgat_component_table(
    n_genes: int,
    protein_names: list[str],
    hidden_dim: int = DGAT_HIDDEN_DIM,
    encoder_dropout: float = DGAT_ENCODER_DROPOUT,
) -> pd.DataFrame:
    """Summarize the four trainable modules in the official DGAT implementation."""

    return pd.DataFrame(
        [
            {
                "module": "RNA GAT encoder",
                "input": (
                    f"{n_genes} RNA features + union(spatial 6-NN, RNA molecular 10-NN in PCA space)"
                ),
                "main_layers": (
                    f"GAT 2048 → GAT 1024 → GAT latent; residuals, LayerNorm, feature attention; "
                    f"dropout={encoder_dropout}"
                ),
                "output": f"{hidden_dim}-D shared latent z_RNA",
            },
            {
                "module": "Protein GAT encoder",
                "input": (
                    f"{len(protein_names)} proteins + union(spatial 6-NN, protein molecular 10-NN)"
                ),
                "main_layers": (
                    f"same GAT encoder design, separately learned weights; dropout={encoder_dropout}"
                ),
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
                "main_layers": (
                    f"shared MLP {hidden_dim} → 512 → 256, then one 256 → 64 → 1 branch per protein"
                ),
                "output": "reconstructed/predicted protein panel",
            },
        ]
    )


def official_dgat_loss_table() -> pd.DataFrame:
    """Describe the five objectives combined by the upstream DGAT training loop."""

    weights = DGAT_TRAIN_LOSS_WEIGHTS
    return pd.DataFrame(
        [
            ("RNA reconstruction", "RMSE(D_RNA(z_RNA), X_RNA)", weights[0], "keeps RNA latent informative"),
            (
                "Protein reconstruction",
                "RMSE(D_protein(z_protein), X_protein)",
                weights[1],
                "keeps protein latent informative; soft-zeroed if < 0.015",
            ),
            (
                "Latent alignment",
                "MSE(z_RNA, z_protein)",
                weights[2],
                "puts paired modalities in a shared space; soft-zeroed if < 0.015",
            ),
            (
                "RNA → protein prediction",
                "RMSE(D_protein(z_RNA), X_protein)",
                weights[3],
                "trains the inference path used on ST data; soft-zeroed if < 0.015",
            ),
            (
                "Protein → RNA prediction",
                "RMSE(D_RNA(z_protein), X_RNA)",
                weights[4],
                "regularizes cross-modal correspondence",
            ),
        ],
        columns=["loss", "formula", "train_weight", "role"],
    )


def official_dgat_optimizer_table() -> pd.DataFrame:
    """Summarize official optimizer / schedule settings from Train_and_Predict.py."""

    return pd.DataFrame(
        [
            ("RNA / protein encoders", f"Adam lr={DGAT_ENCODER_LR}", f"weight_decay={DGAT_ENCODER_WEIGHT_DECAY}"),
            ("RNA / protein decoders", f"Adam lr={DGAT_DECODER_LR}", f"weight_decay={DGAT_DECODER_WEIGHT_DECAY}"),
            ("LR schedule", f"×{DGAT_LR_DECAY_FACTOR} every {DGAT_LR_DECAY_INTERVAL} epochs", "all four optimizers"),
            ("Epoch budget", f"max {DGAT_MAX_EPOCHS}", f"EB early stop after warmup={DGAT_WARMUP_EPOCHS}, threshold={DGAT_EB_THRESHOLD}"),
            ("Grad clip", "max_norm=1.0", "each module after backward"),
        ],
        columns=["setting", "value", "notes"],
    )


def apply_soft_loss_weights(
    protein_reconstruction: float,
    latent_alignment: float,
    protein_prediction: float,
    weights: tuple[float, float, float, float, float] = DGAT_TRAIN_LOSS_WEIGHTS,
    soft_threshold: float = DGAT_LOSS_SOFT_THRESHOLD,
) -> tuple[float, float, float, float, float]:
    """Return effective (α, β, γ, δ, η) after upstream soft-zeroing rules."""

    alpha, beta, gamma, delta, eta = weights
    effective_beta = 0.0 if protein_reconstruction < soft_threshold else beta
    effective_gamma = 0.0 if latent_alignment < soft_threshold else gamma
    effective_delta = 0.0 if protein_prediction < soft_threshold else delta
    return alpha, effective_beta, effective_gamma, effective_delta, eta


def weighted_training_objective(
    rna_reconstruction: float,
    protein_reconstruction: float,
    latent_alignment: float,
    protein_prediction: float,
    rna_prediction: float,
    weights: tuple[float, float, float, float, float] = DGAT_TRAIN_LOSS_WEIGHTS,
    *,
    apply_soft_threshold: bool = True,
    soft_threshold: float = DGAT_LOSS_SOFT_THRESHOLD,
) -> float:
    """Compute the scalar five-term DGAT objective for a logged training step.

    Defaults match the upstream *training* loop weights (α=5, β=1, γ=1, δ=3, η=1)
    and the soft-zero rule for β/γ/δ when a term falls below ``soft_threshold``.
    """

    if apply_soft_threshold:
        weights = apply_soft_loss_weights(
            protein_reconstruction,
            latent_alignment,
            protein_prediction,
            weights=weights,
            soft_threshold=soft_threshold,
        )
    terms = (
        rna_reconstruction,
        protein_reconstruction,
        latent_alignment,
        protein_prediction,
        rna_prediction,
    )
    return float(sum(weight * term for weight, term in zip(weights, terms, strict=True)))
