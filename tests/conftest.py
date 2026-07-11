"""
tests/conftest.py — Shared fixtures for RecruitX integration tests (Phase 16)

Creates a temporary SQLite database with sample candidates and a FAISS vector
index once per test session. All integration tests share the same environment,
with only LLM/OpenRouter calls mocked at the test-function level.
"""

import atexit
import os
import shutil
import tempfile

# ---------------------------------------------------------------------------
# Module-level: set environment variables BEFORE any application modules are
# imported.  These override .env values and ensure all real components
# (orchestrator, ranker, scoring engine, CRUD) point to test paths.
# ---------------------------------------------------------------------------
_INTEGRATION_TMPDIR = tempfile.mkdtemp(prefix="recruitx_int_")
os.environ["DATABASE_PATH"] = os.path.join(_INTEGRATION_TMPDIR, "test.db")
os.environ["FAISS_INDEX_PATH"] = os.path.join(_INTEGRATION_TMPDIR, "faiss_index.bin")
os.environ["FAISS_ID_MAP_PATH"] = os.path.join(_INTEGRATION_TMPDIR, "faiss_id_map.pkl")


@atexit.register
def _cleanup_tmpdir():
    shutil.rmtree(_INTEGRATION_TMPDIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# Imports (safe now — env vars are set)
# ---------------------------------------------------------------------------
import pytest

from agents.candidate_ranker import CandidateRankerAgent
from agents.jd_analyst import JDAnalysis
from database import crud
from database.db_setup import (
    create_indexes,
    create_tables,
    get_db_connection,
    load_sample_data,
)
from embeddings.embedder import CandidateEmbedder
from embeddings.vector_store import CandidateVectorStore

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CSV = os.path.join(PROJECT_ROOT, "data", "sample_candidates.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_candidate_texts(candidates):
    """Build text representations for embedding (mirrors build_index.py)."""
    texts = []
    for c in candidates:
        parts = []
        if c.get("name"):
            parts.append(f"Candidate: {c['name']}.")
        if c.get("location"):
            parts.append(f"Location: {c['location']}.")
        if c.get("skills"):
            parts.append(f"Skills: {c['skills']}.")
        if c.get("experience_years") is not None:
            parts.append(f"Experience: {c['experience_years']} years.")
        if c.get("education"):
            parts.append(f"Education: {c['education']}.")
        if c.get("previous_roles"):
            roles = str(c["previous_roles"]).replace(";", ",").strip()
            parts.append(f"Previous Roles: {roles}.")
        texts.append(" ".join(parts))
    return texts


DEFAULT_JD_ANALYSIS = JDAnalysis(
    required_skills=["Python", "FastAPI", "PostgreSQL", "SQL"],
    preferred_skills=["AWS", "Docker"],
    min_experience_years=3.0,
    education_required="Bachelor's in Computer Science",
    seniority_level="Senior",
    role_summary="Senior Python Developer to build scalable applications.",
    search_query="Senior Python Developer FastAPI PostgreSQL AWS Docker",
)


# ---------------------------------------------------------------------------
# Session-scoped fixture: one-time DB + FAISS setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def integration_env():
    """Build and return temporary SQLite database and FAISS index.

    Yields a dictionary with:
        db_path, faiss_index_path, faiss_map_path,
        candidates (list of dicts),
        embedder, vector_store, ranker (pre-configured CandidateRankerAgent).
    """
    db_path = os.environ["DATABASE_PATH"]
    faiss_index_path = os.environ["FAISS_INDEX_PATH"]
    faiss_map_path = os.environ["FAISS_ID_MAP_PATH"]

    # ---- Database ----
    conn = get_db_connection(db_path)
    create_tables(conn)
    create_indexes(conn)
    load_sample_data(conn, SAMPLE_CSV)
    candidates = crud.get_all_candidates(conn)
    conn.close()

    # ---- FAISS index ----
    embedder = CandidateEmbedder()
    vector_store = CandidateVectorStore(dimension=384)
    texts = _generate_candidate_texts(candidates)
    candidate_ids = [c["id"] for c in candidates]
    embeddings = embedder.embed_batch(texts)
    vector_store.add_candidates(candidate_ids, embeddings)
    vector_store.save(faiss_index_path, faiss_map_path)

    # ---- Pre-built ranker (avoids loading from disk in pipeline tests) ----
    ranker = CandidateRankerAgent(embedder=embedder, vector_store=vector_store)

    yield {
        "db_path": db_path,
        "faiss_index_path": faiss_index_path,
        "faiss_map_path": faiss_map_path,
        "candidates": candidates,
        "embedder": embedder,
        "vector_store": vector_store,
        "ranker": ranker,
    }
