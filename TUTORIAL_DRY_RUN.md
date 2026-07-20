# Participant dry-run log

This log records a clean-room setup from the remote repository on an Apple-silicon Mac. Repository defects are separated from machine- or test-harness-specific conditions.

## Run started: 20 July 2026

| Step | Result | Obstacle and disposition |
| --- | --- | --- |
| Push reviewed changes | Passed | Commit `478635b` pushed to `origin/main`. |
| Clone with the README HTTPS URL | Blocked locally | HTTPS connections to `github.com` timed out on this machine, while SSH worked. This is a local network/transport condition; validation continued with the SSH URL. |
| Clone with SSH | Passed, slow | Checkout completed at `478635b`; elapsed time was approximately 14 minutes on this connection. |
| `conda env create -f environment.yml` | Blocked by existing local state | An environment named `eccb-dgat-tutorial` already existed. Validation continued with an isolated prefix. The README should document update/recreate options for repeat users. |
| Isolated Conda environment | Passed | Created from `environment.yml` under the dry-run directory with Python 3.10. |
| Data-only download | Failed once, then passed manually | Google Drive returned `SSL: UNEXPECTED_EOF_WHILE_READING` after four files. The downloader incorrectly treated any single H5AD as a complete download and would skip a retry. Fixed to use `gdown --continue` and require all 12 expected H5AD files. Resumed download completed with 1.8 GB of data. |
| Data-only asset check | Passed with misleading warning | The old script warned that model weights were absent during the participant-only check. Fixed so only requested asset categories are checked. |
| Notebook 1 | Passed | Official Breast RNA/ADT data loaded: 4,169 spots, 18,085 genes, 35 proteins. The initial execution took 50 seconds. The status message named only RNA although ADT was also used; this was corrected. |
| Notebook 2 | Initially blocked | `data/raw/dgat_predictions.csv` was not distributed or downloadable. The default correctly refused to substitute ridge regression; the verified official prediction artifact is now committed. |
| Official DGAT environment | Passed | The separate Python 3.11 environment installed PyTorch 2.0.1, PyTorch Geometric 2.6.1, and SciPy 1.16.0 successfully on Apple silicon. |
| Official model download | Passed | Four checkpoint files downloaded; the largest encoder file is approximately 333 MB. |
| Official DGAT source clone | Passed, very slow | A full clone was abandoned because history transferred at roughly 80–120 KB/s. A shallow clone completed and is now the documented organizer command. |
| Official prediction wrapper, first run | Failed | Google Drive supplies flat weight files, but upstream `protein_predict` requires a `17434_gene_31_protein/` subdirectory. Fixed by generating a hard-linked compatibility layout while continuing to call the official function. |
| Official prediction wrapper, second run | Failed | The flat encoder is trained on 11,535 genes, but filename sorting selected `common_gene_17434.txt`. Fixed by reading the encoder input width and decoder branch count directly from the downloaded state dictionaries. |
| Official prediction wrapper, third run | Passed | Official CPU inference completed on Breast RNA in 28 seconds and wrote 4,169 × 31 predictions with provenance. |
| Notebook 2 with official predictions | Passed | Loaded the paired Breast data and official precomputed predictions. The final clean runs took 7–9 seconds after filesystem caches were warm. |
| Notebook 3, first official run | Failed | Breast ADT labels use forms such as `CD163-1`, `HLA-DRA`, and `PTPRC-1`, while DGAT predicts `CD163`, `HLA_DRA`, and `PTPRC_1`. Added deterministic ADT-name normalization and a clear error when no proteins overlap. |
| Notebook 3 after protein-name fix | Passed | Evaluated all 31 predicted proteins in 11 seconds. Pearson correlations ranged from −0.288 to 0.711 rather than the prior near-perfect in-sample baseline values. |
| Prediction distribution | Fixed | Added the verified 4,169 × 31 Breast prediction table and provenance sidecar to `data/raw/`, including DGAT commit and checkpoint SHA-256 values. |
| Participant download scope | Improved | The original participant command downloaded all 12 H5AD files (1.8 GB), although the tutorial uses Breast only. Added `--dataset Breast`, reducing the required data transfer to roughly 270 MB while preserving the full organizer download path. |

## Test-harness-only condition

The managed execution sandbox initially denied Jupyter's localhost kernel socket. Re-running with local kernel networking permitted resolved it; this is not a tutorial repository defect.

During the final repetition, the already-created isolated environment was reused and its editable package install was repointed to the new clone. Pip's build-isolation subprocess initially could not resolve PyPI inside the restricted sandbox; the same command passed when network access was permitted. A new participant following `conda env create -f environment.yml` does not perform this extra repointing step. The validation command also supplied an unsupported nbconvert `ExecutePreprocessor.cwd` option for Notebook 1; nbconvert ignored it, the notebook found the repository correctly, and the option was removed from the remaining test commands. Neither condition requires a repository change.

## Final measured notebook pass

All three current notebooks executed top-to-bottom with the official Breast data and official DGAT predictions. Observed peak resident memory was approximately 2.0 GB for Notebook 1, 1.0 GB for Notebook 2, and 0.9 GB for Notebook 3.

## Final remote-clone repetition

After fix commit `809f02b` was pushed to `origin/main`, a new shallow SSH clone was created in an isolated temporary directory and verified at exactly that commit. The committed prediction table SHA-256 matched its provenance sidecar (`d28edda9f85bcf851d475d1b903de32fec925c05d798fecb585e723312c683b7`). The README participant download command fetched only `Breast_ADT.h5ad` and `Breast_RNA.h5ad` (approximately 270 MB) in 156 seconds, and the documented `--check-only` command passed without requesting model weights.

The three notebooks then passed in order with fresh kernels:

| Notebook | Elapsed time | Verified result |
| --- | ---: | --- |
| 1 | 42.4 s | Loaded 4,169 spots, 18,085 genes, and 35 measured proteins from the paired Breast files. |
| 2 | 7.6 s | Loaded the repository-provided official DGAT predictions and aligned all 4,169 spots. |
| 3 | 8.3 s | Evaluated 31 shared proteins; Pearson correlations ranged from -0.288 to 0.711 and Moran's I completed for every protein. |

No additional repository defect was found in the final remote-clone participant path.
