"""
agents/candidate_ranker.py — Candidate Ranker Agent for RecruitX

This agent takes a search query (from JD Analyst), embeds it using the
CandidateEmbedder, searches the FAISS vector store for semantically similar
candidates, and returns ranked results with normalized semantic scores.

The orchestrator agent calls this agent after the JD Analyst Agent to find
the top K candidates that match the job description semantically.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from embeddings.embedder import CandidateEmbedder
from embeddings.vector_store import CandidateVectorStore

# Load environment variables so os.getenv() works
load_dotenv()

logger = logging.getLogger(__name__)

# Default paths and config from .env
DEFAULT_FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
DEFAULT_FAISS_ID_MAP_PATH = os.getenv("FAISS_ID_MAP_PATH", "data/faiss_id_map.pkl")
DEFAULT_EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
DEFAULT_TOP_K = int(os.getenv("MAX_CANDIDATES_PER_SEARCH", "20"))


class CandidateRankerAgent:
    """
    Agent that searches for the best matching candidates using semantic search.

    Uses the FAISS vector store to find candidates whose embeddings are most
    similar to the search query embedding, then normalizes the cosine similarity
    scores to a 0-100 range.
    """

    def __init__(
        self,
        embedder: Optional[CandidateEmbedder] = None,
        vector_store: Optional[CandidateVectorStore] = None,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        index_path: str = DEFAULT_FAISS_INDEX_PATH,
        id_map_path: str = DEFAULT_FAISS_ID_MAP_PATH,
    ):
        """
        Initialize the Candidate Ranker Agent.

        Accepts optional pre-configured embedder and vector_store for
        dependency injection (useful for testing). If not provided,
        creates them from scratch and loads the FAISS index from disk.

        Args:
            embedder: CandidateEmbedder instance (created automatically if None)
            vector_store: CandidateVectorStore instance (created and loaded if None)
            dimension: Embedding dimension (default: 384)
            index_path: Path to the FAISS index binary file
            id_map_path: Path to the FAISS ID mapping pickle file

        Raises:
            FileNotFoundError: If FAISS index or ID map files don't exist
        """
        logger.info("ENTER CandidateRankerAgent")

        self.dimension = dimension
        self.index_path = index_path
        self.id_map_path = id_map_path

        # Initialize or use injected embedder
        if embedder is not None:
            self.embedder = embedder
            logger.info("Using injected embedder")
        else:
            logger.info("Initializing CandidateEmbedder...")
            self.embedder = CandidateEmbedder()

        # Initialize or use injected vector store
        if vector_store is not None:
            self.vector_store = vector_store
            logger.info("Using injected vector store")
        else:
            logger.info("Loading FAISS index from disk...")
            self.vector_store = CandidateVectorStore(dimension=self.dimension)
            self.vector_store.load(self.index_path, self.id_map_path)

        logger.info(
            "Initialized CandidateRankerAgent with %d vectors in FAISS index",
            self.vector_store.index.ntotal,
        )
        logger.info("EXIT CandidateRankerAgent")

    def rank_candidates(
        self,
        search_query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Tuple[int, float]]:
        """
        Search for the top K candidates matching the query.

        Steps:
            1. Embed the search query using CandidateEmbedder
            2. Search the FAISS vector store for nearest neighbors
            3. Normalize cosine similarity scores from [-1, 1] to [0, 100]

        Args:
            search_query: Text query string (from JDAnalysis.search_query)
            top_k: Number of top candidates to return (default: from .env)

        Returns:
            List of (candidate_id, semantic_score) tuples sorted by score descending.
            Semantic scores are normalized to 0-100 range.

        Raises:
            ValueError: If search_query is empty or invalid
            RuntimeError: If embedding or search fails
        """
        if not search_query or not isinstance(search_query, str) or not search_query.strip():
            logger.error("Empty or invalid search query provided")
            raise ValueError("Search query must be a non-empty string")

        search_query = search_query.strip()

        try:
            # Step 1: Embed the query
            logger.info("Embedding search query (top_k=%d)...", top_k)
            query_vector = self.embedder.embed_text(search_query)

            # Step 2: Search FAISS index
            logger.info("Searching FAISS vector store...")
            raw_results = self.vector_store.search(query_vector, top_k=top_k)

            if not raw_results:
                logger.info("No candidates found matching the query")
                return []

            # Step 3: Normalize scores from [-1, 1] to [0, 100]
            normalized_results: List[Tuple[int, float]] = []
            for candidate_id, raw_score in raw_results:
                # Cosine similarity ranges from -1 to 1
                # Normalize to 0-100: ((score + 1) / 2) * 100
                normalized_score = round(((raw_score + 1.0) / 2.0) * 100.0, 2)
                normalized_results.append((candidate_id, normalized_score))

            logger.info(
                "Found %d candidates. Top score: %.2f",
                len(normalized_results),
                normalized_results[0][1] if normalized_results else 0,
            )

            return normalized_results

        except ValueError as e:
            logger.error("Invalid input for candidate ranking: %s", str(e))
            raise
        except FileNotFoundError as e:
            logger.error("FAISS index files not found: %s", str(e))
            raise RuntimeError(f"FAISS index not loaded: {e}")
        except Exception as e:
            logger.error("Failed to rank candidates: %s", str(e), exc_info=True)
            raise RuntimeError(f"Candidate ranking failed: {e}")
