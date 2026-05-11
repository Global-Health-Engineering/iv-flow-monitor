# Reproducible runtime for the Dripito validation analysis pipeline.
#
# Pinned to a specific Python image (by digest, not just tag) so the
# environment is byte-stable across machines and time. All Python
# dependencies are hash-locked in requirements.txt.
#
# Build:
#   docker build -t dripito-analysis .
# Run via compose (recommended):
#   docker compose up regenerate-figures-sample
#   docker compose up regenerate-figures

# python:3.12.7-slim-bookworm — pinned Python version + Debian release.
# To pin further by digest, run `docker pull python:3.12.7-slim-bookworm`,
# read the digest from `docker inspect`, and append @sha256:<digest>.
FROM python:3.12.7-slim-bookworm

# System deps for headless matplotlib (no GUI backend needed)
ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /work

# Install hash-locked Python deps in a single layer.
# --require-hashes refuses to install anything without a matching hash.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --require-hashes -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copy in the analysis pipeline. Data and figures are mounted at runtime
# (see docker-compose.yml), not baked into the image, so the same image
# runs against sample data and against the real campaign dataset.
COPY scripts/ /work/scripts/
COPY notebooks/ /work/notebooks/

# Default command: execute the validation notebook headlessly.
# docker-compose overrides DATA_DIR + SAMPLE_MODE per service.
CMD ["python", "-m", "papermill", \
     "/work/notebooks/validation.ipynb", \
     "/work/notebooks/validation_executed.ipynb", \
     "--cwd", "/work/notebooks"]
