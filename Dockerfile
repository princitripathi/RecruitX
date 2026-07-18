# ── Stage 1: Builder ────────────────────────────────────────────────
# Install dependencies into a virtual env so we can copy it cleanly.
FROM python:3.12-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build essentials (some wheels need gcc)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create venv and install dependencies first (layer caching)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH" \
    DATABASE_PATH="data/recruitx.db" \
    FAISS_INDEX_PATH="data/faiss_index.bin" \
    FAISS_ID_MAP_PATH="data/faiss_id_map.pkl" \
    LOG_LEVEL="INFO"

# Copy the pre-built virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY config.py .
COPY agents/ agents/
COPY api/ api/
COPY database/ database/
COPY embeddings/ embeddings/
COPY scoring/ scoring/
COPY utils/ utils/
COPY scripts/ scripts/

# Copy sample data needed for db_setup.py at runtime
COPY data/sample_candidates.csv data/sample_candidates.csv
COPY data/sample_jds/ data/sample_jds/

# Create uploads directory (for resume uploads at runtime)
RUN mkdir -p uploads data

# Initialize the database at build time (tables + sample data)
RUN python database/db_setup.py

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
