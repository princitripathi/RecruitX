#!/usr/bin/env python3
"""
scripts/build_index.py — Build FAISS Vector Index for RecruitX

Loads all candidates from SQLite, generates embeddings, builds the FAISS
index, saves it to disk, and updates candidate records with embedding IDs.

Run from the project root:
    python scripts/build_index.py
"""

import logging
import shutil
import sys
import time
from pathlib import Path

# Add project root to Python path so imports work when running directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    DATABASE_PATH,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    FAISS_ID_MAP_PATH,
    FAISS_INDEX_PATH,
)
from database.crud import get_all_candidates, update_candidate
from database.db_setup import get_db_connection
from embeddings.build_index import generate_candidate_text
from embeddings.embedder import CandidateEmbedder
from embeddings.vector_store import CandidateVectorStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

MIN_FREE_DISK_MB = 200


def _check_disk_space() -> None:
    """Log a warning if disk space is critically low."""
    try:
        usage = shutil.disk_usage("/")
        free_mb = usage.free // (1024 * 1024)
        logger.info("Disk space: %d MB free", free_mb)
        if free_mb < MIN_FREE_DISK_MB:
            logger.warning(
                "Low disk space (%d MB free). Build may fail if disk runs out.",
                free_mb,
            )
    except Exception as e:
        logger.warning("Could not check disk space: %s", e)


def build_faiss_index() -> None:
    """
    Main execution pipeline to build or rebuild the FAISS vector index.
    """
    pipeline_start = time.time()
    logger.info("=" * 60)
    logger.info("Starting FAISS Vector Index Build Pipeline")
    logger.info("Model: %s | Dimension: %d", EMBEDDING_MODEL, EMBEDDING_DIMENSION)
    logger.info("=" * 60)

    _check_disk_space()

    # 1. Fetch candidates from DB
    step_start = time.time()
    logger.info("Connecting to database: %s", DATABASE_PATH)
    conn = get_db_connection(DATABASE_PATH)
    try:
        candidates = get_all_candidates(conn)
        candidate_count = len(candidates)
        logger.info(
            "Fetched %d candidates from database (%.1fs)",
            candidate_count, time.time() - step_start,
        )

        if candidate_count == 0:
            logger.warning("No candidates found in database. Exiting pipeline.")
            return

        # 2. Generate candidate text representations
        step_start = time.time()
        texts = []
        candidate_ids = []
        for cand in candidates:
            text_rep = generate_candidate_text(cand)
            texts.append(text_rep)
            candidate_ids.append(cand["id"])
        logger.info(
            "Generated %d text representations (%.1fs)",
            len(texts), time.time() - step_start,
        )

        # 3. Compute Embeddings
        step_start = time.time()
        logger.info("Initializing CandidateEmbedder (model=%s)...", EMBEDDING_MODEL)
        embedder = CandidateEmbedder(model_name=EMBEDDING_MODEL)
        logger.info("Generating embeddings in batch...")
        embeddings = embedder.embed_batch(texts)
        logger.info(
            "Computed %d embeddings (%.1fs)",
            len(embeddings), time.time() - step_start,
        )

        # 4. Populate FAISS Index
        step_start = time.time()
        logger.info("Initializing CandidateVectorStore...")
        vector_store = CandidateVectorStore(dimension=EMBEDDING_DIMENSION)
        logger.info("Adding embeddings to vector store...")
        vector_store.add_candidates(candidate_ids, embeddings)
        logger.info(
            "FAISS index populated with %d vectors (%.1fs)",
            vector_store.index.ntotal, time.time() - step_start,
        )

        # 5. Save index and mapping to files
        step_start = time.time()
        logger.info("Saving index and ID map files...")
        vector_store.save(FAISS_INDEX_PATH, FAISS_ID_MAP_PATH)
        logger.info("Saved to disk (%.1fs)", time.time() - step_start)

        # 6. Update database with embedding_ids
        step_start = time.time()
        logger.info("Updating candidate records with embedding_id in SQLite...")
        updated_count = 0
        for faiss_idx, candidate_id in vector_store.id_map.items():
            success = update_candidate(conn, candidate_id, embedding_id=faiss_idx)
            if success:
                updated_count += 1

        logger.info(
            "Updated %d candidates with embedding_ids (%.1fs)",
            updated_count, time.time() - step_start,
        )

        # 7. Verification check
        if updated_count != candidate_count:
            logger.error(
                "Verification failed: updated %d but expected %d",
                updated_count, candidate_count,
            )
            raise RuntimeError(
                f"Embedding ID update mismatch: {updated_count}/{candidate_count} "
                f"candidates updated"
            )

        elapsed = time.time() - pipeline_start
        logger.info("=" * 60)
        logger.info("FAISS Vector Index built successfully! (%.1fs total)", elapsed)
        logger.info("  Index: %s", FAISS_INDEX_PATH)
        logger.info("  ID Map: %s", FAISS_ID_MAP_PATH)
        logger.info("  Candidates indexed: %d", candidate_count)
        logger.info("=" * 60)

    except Exception as e:
        logger.error("FAISS index build pipeline failed: %s", str(e), exc_info=True)
        raise
    finally:
        conn.close()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    build_faiss_index()
