"""
api/main.py — FastAPI Application Entry Point for RecruitX

This module initializes the FastAPI application, configures middleware,
includes all route routers, and defines the health check endpoint.

Usage:
    uvicorn api.main:app --reload --port 8000

Or from the project root:
    python -m uvicorn api.main:app --reload --port 8000
"""

import gc
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import HealthResponse
from api.routes import candidates, chat, interviews, recruitment, resumes

# Load environment variables before anything else
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)

# Application metadata from .env
APP_NAME = os.getenv("APP_NAME", "RecruitX")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Autonomous Multi-Agent AI Recruitment System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================
# CORS Middleware
# Allow origins from CORS_ORIGINS env var (comma-separated)
# or default to "*" for local development (Streamlit on :8501).
# Override in production via Render dashboard env vars.
# ============================================================

cors_origins_str = os.getenv("CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_str.split(",")] if cors_origins_str else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Include Route Routers
# ============================================================

app.include_router(recruitment.router)
app.include_router(candidates.router)
app.include_router(resumes.router)
app.include_router(chat.router)
app.include_router(interviews.router)


# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Pre-load heavy AI models and indexes at startup to avoid per-request latency spikes."""
    # Limit torch/OpenMP threads to 1 to minimize per-thread memory (~30-50MB saved)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass

    logger.info("=" * 60)
    logger.info("%s v%s starting up", APP_NAME, APP_VERSION)
    logger.info("API docs: http://localhost:%d/docs", API_PORT)
    logger.info("=" * 60)

    # Pre-load SentenceTransformer model (~80MB) into memory once
    try:
        from embeddings.embedder import preload_model
        preload_model()
    except Exception as e:
        logger.warning("Could not pre-load SentenceTransformer model: %s", e)

    # Pre-load FAISS index into memory once
    try:
        from embeddings.vector_store import preload_index
        preload_index(
            index_path=os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin"),
            map_path=os.getenv("FAISS_ID_MAP_PATH", "data/faiss_id_map.pkl"),
            dimension=int(os.getenv("EMBEDDING_DIMENSION", "384")),
        )
    except Exception as e:
        logger.warning("Could not pre-load FAISS index: %s", e)

    # Pre-initialize the orchestrator singleton (creates agents + LLM chains once)
    try:
        from api.routes.recruitment import _init_orchestrator
        _init_orchestrator()
    except Exception as e:
        logger.warning("Could not pre-initialize orchestrator: %s", e)

    gc.collect()
    logger.info("Startup pre-loading complete")


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.

    Returns basic application status information. Used by monitoring
    systems and the frontend to verify the API is running.

    Returns:
        HealthResponse with status, app name, and version.
    """
    return HealthResponse(
        status="ok",
        app=APP_NAME,
        version=APP_VERSION,
    )
