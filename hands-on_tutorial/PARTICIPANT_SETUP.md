# Participant preparation

The hands-on tutorial runs in **Google Colab**. You do not need to install Python, Conda,
Jupyter, DGAT, CUDA, or any Python packages on your laptop. A GPU is not required.

## What to prepare

- A laptop and charger
- A current web browser
- A Google account with access to Google Drive and Google Colab
- At least 3 GB of free space in Google Drive
- A stable connection for the one-time dataset download
- Your Google two-factor authentication method, if enabled

## Before the workshop: run Notebook 0 once

1. Open [Notebook 0 — Prepare Google Drive](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/00_colab_setup.ipynb).
2. Choose **Runtime → Change runtime type → 2026.04 (Python 3.12)**.
3. Run every cell from top to bottom and approve the Google Drive mount.
4. Wait for `Drive preparation complete: /content/drive/MyDrive/ECCB2026`.
5. Keep `MyDrive/ECCB2026` in place. You may close the runtime after preparation.

### Opening Notebook 0 from the Colab home page

The direct Notebook 0 link above is the quickest option. If you are starting from the
[Google Colab home page](https://colab.research.google.com/), follow these steps instead:

1. Select **Upload notebook** to open the notebook picker.

   ![On the Colab home page, select Upload notebook.](assets/participant_setup/01_open_colab_notebook_picker.png)

2. Select **GitHub**, paste
   `https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial` into the search box, confirm that the
   branch is **main**, and select
   `hands-on_tutorial/notebooks/00_colab_setup.ipynb`.

   ![In the Colab notebook picker, select GitHub, paste the tutorial repository URL, and select Notebook 00.](assets/participant_setup/02_select_notebook_00_from_github.png)

Notebook 0 automatically downloads and verifies both tutorial datasets: paired Tonsil RNA/ADT for
Sessions 1–2, and the 10x `V1_Human_Lymph_Node` count matrix and spatial/H&E bundle for Session 3.
It also installs the tracked germinal-center annotation and organizer-validated lymph-node DGAT
prediction matrix, creates a wheel cache, and prepares persistent result and checkpoint folders.
Do not download or move these files manually.

Approximate preparation time is 5–10 minutes on a typical connection. For planning, allow 5–15
minutes each for Sessions 1–2 and 3–5 minutes for the default Session 3 analysis on a standard
free-tier CPU runtime (typically about 12 GB system RAM); no GPU memory is used. Sessions 1–2 write
large processed Tonsil matrices to Drive, which is why at least 3 GB of free space is recommended.
The optional full lymph-node inference rerun downloads about 350 MB of weights; allow approximately
15–30 minutes including setup on a GPU runtime with at least 12 GB system RAM and 8 GB GPU RAM.
These are planning estimates, and Colab hardware and runtime availability vary.

## During the workshop

Open notebooks with the direct links below. Do not open `.ipynb` files from Colab's `/content`
Files pane; that pane may show a source preview instead of an executable notebook.

1. [Notebook 1 — Data and spatial context](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/01_data_and_spatial.ipynb)
2. [Notebook 2 — Model and predictions](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/02_model_and_predictions.ipynb)
3. [Notebook 3 — Evaluation and interpretation](https://colab.research.google.com/github/osmanbeyoglulab/ECCB-2026-Tutorial/blob/main/hands-on_tutorial/notebooks/03_evaluation_and_interpretation.ipynb)

Run the first bootstrap cell whenever a notebook receives a new runtime. It mounts Drive,
refreshes the tutorial checkout, copies only the dataset required by that notebook to fast local
storage, installs the pinned packages, and reconnects saved checkpoints. Sessions 1–2 copy Tonsil;
Session 3 independently copies lymph node.

## If the runtime disconnects

1. Reopen the same notebook from its direct Colab link.
2. Confirm runtime version 2026.04.
3. Rerun the first bootstrap cell.
4. Read the printed checkpoints and continue from the first unfinished part.

Do not repeat Notebook 0 or redownload the dataset unless the notebook reports that a Drive asset
is missing or incomplete.

## Troubleshooting

- **Notebook shows `<undefined>` or raw source:** close the Files-pane preview and use the direct
  Colab link above.
- **Missing Drive asset:** rerun Notebook 0. Complete files are skipped, and interrupted downloads
  resume when supported.
- **`ModuleNotFoundError: dgat_tutorial`:** rerun the first bootstrap cell in the current notebook.
- **Runtime reset:** rerun only the bootstrap, then continue from the first unfinished checkpoint.
- **Wrong dataset:** Sessions 1–2 require paired `Tonsil_RNA.h5ad` and `Tonsil_ADT.h5ad`;
  Session 3 requires `V1_Human_Lymph_Node` RNA, spatial, GC-label, and prediction assets.
- **`muon`/`mudata` import error:** rerun the first bootstrap cell so the compatible pinned versions
  are installed, then restart the runtime if Colab requests it.
- **Optional full inference:** use a GPU runtime and enable the clearly labeled flag at the end of
  Session 3. It is not required for the participant workflow.

Repository: <https://github.com/osmanbeyoglulab/ECCB-2026-Tutorial>
