"""
embeddings/build_index.py — Build FAISS Vector Index for RecruitX

This script loads all candidates from the SQLite database, generates their text
representations, computes their embeddings, indexes them using FAISS,
saves the index and ID map to disk, and updates candidate tables with their
respective embedding ID.

Run this script from the project root:
    python embeddings/build_index.py
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to Python path so imports work when running directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from database.crud import get_all_candidates, update_candidate
from database.db_setup import get_db_connection
from embeddings.embedder import CandidateEmbedder
from embeddings.vector_store import CandidateVectorStore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths from .env
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/recruitx.db")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
FAISS_ID_MAP_PATH = os.getenv("FAISS_ID_MAP_PATH", "data/faiss_id_map.pkl")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))


def generate_candidate_text(candidate: dict) -> str:
    """
    Generate a rich, single-string text representation of a candidate.

    Args:
        candidate: Candidate dictionary from database.

    Returns:
        A formatted string describing candidate's location, skills, experience,
        education, and previous roles.
    """
    name = candidate.get("name", "").strip()
    location = candidate.get("location", "").strip()
    skills = candidate.get("skills", "").strip()
    experience = candidate.get("experience_years", 0)
    education = candidate.get("education", "").strip()
    previous_roles = candidate.get("previous_roles")

    text_parts = []
    if name:
        text_parts.append(f"Candidate: {name}.")
    if location:
        text_parts.append(f"Location: {location}.")
    if skills:
        text_parts.append(f"Skills: {skills}.")
    if experience is not None:
        text_parts.append(f"Experience: {experience} years.")
    if education:
        text_parts.append(f"Education: {education}.")
    if previous_roles:
        # Format roles nicely by replacing semicolons with commas if present
        roles_clean = str(previous_roles).replace(";", ",").strip()
        text_parts.append(f"Previous Roles: {roles_clean}.")

    return " ".join(text_parts)


def build_faiss_index() -> None:
    """
    Main execution pipeline to build or rebuild the FAISS vector index.
    """
    logger.info("=" * 60)
    logger.info("Starting FAISS Vector Index Build Pipeline")
    logger.info("=" * 60)

    # 1. Fetch candidates from DB
    logger.info("Connecting to database: %s", DATABASE_PATH)
    conn = get_db_connection(DATABASE_PATH)
    try:
        candidates = get_all_candidates(conn)
        candidate_count = len(candidates)
        logger.info("Fetched %d candidates from database.", candidate_count)

        if candidate_count == 0:
            logger.warning("No candidates found in database. Exiting pipeline.")
            return

        # 2. Generate candidate text representations
        texts = []
        candidate_ids = []
        for cand in candidates:
            text_rep = generate_candidate_text(cand)
            texts.append(text_rep)
            candidate_ids.append(cand["id"])

        # 3. Compute Embeddings
        logger.info("Initializing CandidateEmbedder...")
        embedder = CandidateEmbedder()
        logger.info("Generating embeddings in batch...")
        embeddings = embedder.embed_batch(texts)

        # 4. Populate FAISS Index
        logger.info("Initializing CandidateVectorStore...")
        vector_store = CandidateVectorStore(dimension=EMBEDDING_DIMENSION)
        logger.info("Adding embeddings to vector store...")
        vector_store.add_candidates(candidate_ids, embeddings)

        # 5. Save index and mapping to files
        logger.info("Saving index and ID map files...")
        vector_store.save(FAISS_INDEX_PATH, FAISS_ID_MAP_PATH)

        # 6. Update database with embedding_ids
        logger.info("Updating candidate records with embedding_id in SQLite...")
        updated_count = 0
        # In build_index, FAISS vector indices are sequential 0 to N-1
        for faiss_idx, candidate_id in vector_store.id_map.items():
            success = update_candidate(conn, candidate_id, embedding_id=faiss_idx)
            if success:
                updated_count += 1

        logger.info("Successfully updated %d candidates with embedding_ids in SQLite.", updated_count)

        # 7. Verification check
        assert updated_count == candidate_count, f"Updated count {updated_count} mismatch with total candidate count {candidate_count}."
        logger.info("=" * 60)
        logger.info("✅ FAISS Vector Index built successfully!")
        logger.info("   Index saved to: %s", FAISS_INDEX_PATH)
        logger.info("   ID Map saved to: %s", FAISS_ID_MAP_PATH)
        logger.info("   SQLite database updated with all embedding_ids.")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("❌ FAISS index build pipeline failed: %s", str(e), exc_info=True)
        raise
    finally:
        conn.close()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    build_faiss_index()
