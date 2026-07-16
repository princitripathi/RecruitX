"""
embeddings/vector_store.py — FAISS Vector Store Management for RecruitX

This module provides the CandidateVectorStore class, which manages the FAISS index
and the mapping between FAISS vector indices and SQLite candidate IDs.
"""

import os
import pickle
import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

_faiss_cache = {}


def preload_index(
    index_path: str,
    map_path: str,
    dimension: int = 384,
) -> None:
    """
    Eagerly load the FAISS index into the module-level cache.
    Call this once at application startup to avoid per-request disk I/O.
    """
    cache_key = (os.path.abspath(index_path), os.path.abspath(map_path))
    if cache_key in _faiss_cache:
        return
    if not os.path.exists(index_path) or not os.path.exists(map_path):
        logger.warning("FAISS index files not found at startup — skipping preload")
        return
    store = CandidateVectorStore(dimension=dimension)
    store.load(index_path, map_path)
    logger.info("Pre-loaded FAISS index with %d vectors", store.index.ntotal)


class CandidateVectorStore:
    """
    Manages a FAISS index and the metadata mapping between FAISS positions
    and candidate database IDs.
    """

    def __init__(self, dimension: int = 384):
        """
        Initialize the vector store.

        Args:
            dimension: The dimension of the embedding vectors.
        """
        import faiss
        self.dimension = dimension
        # Using Inner Product (IndexFlatIP) because after L2 normalization,
        # the inner product is mathematically equivalent to Cosine Similarity.
        self.index = faiss.IndexFlatIP(dimension)
        # Dictionary mapping: FAISS vector index (int) -> SQLite candidate ID (int)
        self.id_map: Dict[int, int] = {}

    def add_candidates(self, candidate_ids: List[int], embeddings: List[List[float]]) -> None:
        """
        Add candidate embeddings to the FAISS index and record their mapping.

        Args:
            candidate_ids: List of candidate IDs from the SQLite database.
            embeddings: List of candidate embedding vectors.

        Raises:
            ValueError: If lengths of ids and embeddings do not match.
        """
        if not candidate_ids or not embeddings:
            logger.warning("No candidates or embeddings provided to add to vector store.")
            return

        if len(candidate_ids) != len(embeddings):
            logger.error("Length mismatch: %d IDs and %d embeddings.", len(candidate_ids), len(embeddings))
            raise ValueError("The number of candidate IDs must match the number of embeddings.")

        import faiss
        import numpy as np
        # Convert to float32 numpy array
        embeddings_np = np.array(embeddings, dtype=np.float32)

        # Normalize the vectors to unit length so that inner product equals cosine similarity
        faiss.normalize_L2(embeddings_np)

        start_idx = self.index.ntotal
        self.index.add(embeddings_np)

        # Map FAISS vector position to actual candidate ID
        for i, cid in enumerate(candidate_ids):
            self.id_map[start_idx + i] = cid

        logger.info("Added %d vectors to FAISS index. New total: %d", len(candidate_ids), self.index.ntotal)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search the index for the closest candidate embeddings.

        Args:
            query_embedding: The embedding vector of the search query.
            top_k: Number of nearest neighbors to return.

        Returns:
            List of tuples: (candidate_id, cosine_similarity_score) sorted by score descending.
        """
        if self.index.ntotal == 0:
            logger.warning("Search called on an empty FAISS index.")
            return []

        import faiss
        import numpy as np
        # Convert query embedding to 2D numpy float32 array
        query_np = np.array([query_embedding], dtype=np.float32)

        # Normalize query vector to unit length
        faiss.normalize_L2(query_np)

        # Perform the search
        similarities, indices = self.index.search(query_np, top_k)

        results = []
        # similarities shape: (1, top_k), indices shape: (1, top_k)
        for score, idx in zip(similarities[0], indices[0]):
            if idx == -1:
                # -1 indicates not enough items in index to fill top_k
                continue

            candidate_id = self.id_map.get(int(idx))
            if candidate_id is not None:
                # Inner product of L2 normalized vectors is Cosine Similarity
                results.append((candidate_id, float(score)))

        # Sort descending by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def save(self, index_path: str, map_path: str) -> None:
        """
        Save the FAISS index and the ID mapping to disk.

        Args:
            index_path: Filepath where the FAISS index will be saved.
            map_path: Filepath where the pickle ID map will be saved.
        """
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(map_path)), exist_ok=True)

        import faiss
        faiss.write_index(self.index, index_path)
        with open(map_path, "wb") as f:
            pickle.dump(self.id_map, f)

        logger.info("Saved FAISS index to %s and ID map to %s", index_path, map_path)

    def load(self, index_path: str, map_path: str) -> None:
        """
        Load the FAISS index and the ID mapping from disk.
        Uses a module-level cache to avoid repeated disk reads.

        Args:
            index_path: Filepath to load the FAISS index from.
            map_path: Filepath to load the ID map from.
        """
        cache_key = (os.path.abspath(index_path), os.path.abspath(map_path))

        if cache_key in _faiss_cache:
            cached_index, cached_map = _faiss_cache[cache_key]
            if cached_index.d != self.dimension:
                raise ValueError(f"Cached index dimension {cached_index.d} does not match expected {self.dimension}")
            self.index = cached_index
            self.id_map = cached_map
            logger.info("Reusing cached FAISS index with %d vectors", self.index.ntotal)
            return

        if not os.path.exists(index_path):
            logger.error("FAISS index file not found: %s", index_path)
            raise FileNotFoundError(f"FAISS index file not found: {index_path}")

        if not os.path.exists(map_path):
            logger.error("ID mapping file not found: %s", map_path)
            raise FileNotFoundError(f"ID mapping file not found: {map_path}")

        import faiss
        self.index = faiss.read_index(index_path)
        with open(map_path, "rb") as f:
            self.id_map = pickle.load(f)

        if self.index.d != self.dimension:
            logger.error("Loaded index dimension %d does not match expected %d", self.index.d, self.dimension)
            raise ValueError(f"Loaded index dimension {self.index.d} does not match expected {self.dimension}")

        _faiss_cache[cache_key] = (self.index, self.id_map)
        logger.info("Loaded FAISS index and ID map with %d vectors", self.index.ntotal)
