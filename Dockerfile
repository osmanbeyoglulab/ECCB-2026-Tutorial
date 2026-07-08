FROM continuumio/miniconda3:24.9.2-0

WORKDIR /workspace

COPY environment.yml pyproject.toml README.md ./
COPY src ./src
COPY notebooks ./notebooks
COPY scripts ./scripts
COPY tutorial_checklist.md ./

RUN conda env create -f environment.yml && conda clean -afy

EXPOSE 8888

CMD ["conda", "run", "--no-capture-output", "-n", "eccb-dgat-tutorial", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=", "--ServerApp.password="]
