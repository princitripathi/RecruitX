from unittest.mock import MagicMock

import pytest

from agents.candidate_ranker import CandidateRankerAgent


class MockEmbedder:
    """Mock embedder that returns a fixed 384-dim vector without loading a real model."""

    def embed_text(self, text: str):
        if not text or not text.strip():
            raise ValueError("Input text must be a non-empty string.")
        return [0.1] * 384


class MockVectorStore:
    """Mock vector store that returns predefined results without needing FAISS."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = MagicMock()
        self.index.ntotal = 50

    def search(self, query_vector, top_k: int = 5):
        # Return (candidate_id, cosine_similarity) tuples
        # Cosine similarity ranges from -1 to 1
        return [
            (1, 0.92),
            (2, 0.75),
            (3, 0.60),
            (4, 0.30),
            (5, -0.10),
        ][:top_k]

    def load(self, index_path: str, map_path: str):
        pass


SAMPLE_QUERY = "Senior Python Developer with FastAPI and SQL experience"


def test_rank_candidates_returns_normalized_scores():
    """Test that raw cosine similarity scores are normalized to 0-100."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    results = agent.rank_candidates(SAMPLE_QUERY, top_k=3)

    assert len(results) == 3
    # Result 1: cosine_sim=0.92 -> ((0.92 + 1) / 2) * 100 = 96.0
    assert results[0][0] == 1
    assert results[0][1] == 96.0

    # Result 2: cosine_sim=0.75 -> ((0.75 + 1) / 2) * 100 = 87.5
    assert results[1][0] == 2
    assert results[1][1] == 87.5

    # Result 3: cosine_sim=0.60 -> ((0.60 + 1) / 2) * 100 = 80.0
    assert results[2][0] == 3
    assert results[2][1] == 80.0


def test_rank_candidates_returns_sorted_by_score():
    """Test that results are sorted by score descending."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    results = agent.rank_candidates(SAMPLE_QUERY, top_k=5)

    for i in range(len(results) - 1):
        assert results[i][1] >= results[i + 1][1]


def test_rank_candidates_score_range():
    """Test that scores are in valid 0-100 range."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    results = agent.rank_candidates(SAMPLE_QUERY, top_k=5)

    for _, score in results:
        assert 0.0 <= score <= 100.0


def test_rank_candidates_negative_cosine():
    """Test that negative cosine similarity maps to low score."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    results = agent.rank_candidates(SAMPLE_QUERY, top_k=5)

    # The 5th result has cosine_sim=-0.10 -> ((-0.10 + 1) / 2) * 100 = 45.0
    assert results[4][0] == 5
    assert results[4][1] == 45.0


def test_rank_candidates_empty_query():
    """Test that empty query raises ValueError."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    with pytest.raises(ValueError, match="non-empty"):
        agent.rank_candidates("")

    with pytest.raises(ValueError, match="non-empty"):
        agent.rank_candidates("   ")

    with pytest.raises(ValueError, match="non-empty"):
        agent.rank_candidates(None)  # type: ignore


def test_rank_candidates_empty_store():
    """Test that empty vector store returns empty list."""
    empty_store = MockVectorStore()
    empty_store.index.ntotal = 0
    empty_store.search = lambda query_vector, top_k=5: []

    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=empty_store,
    )

    results = agent.rank_candidates(SAMPLE_QUERY, top_k=5)
    assert results == []


def test_rank_candidates_top_k_respected():
    """Test that top_k limits the number of results."""
    agent = CandidateRankerAgent(
        embedder=MockEmbedder(),
        vector_store=MockVectorStore(),
    )

    results_2 = agent.rank_candidates(SAMPLE_QUERY, top_k=2)
    assert len(results_2) == 2

    results_1 = agent.rank_candidates(SAMPLE_QUERY, top_k=1)
    assert len(results_1) == 1


def test_rank_candidates_embedder_failure():
    """Test that embedder failure propagates as error."""
    class FailingEmbedder:
        def embed_text(self, text):
            raise RuntimeError("Model loading failed")

    agent = CandidateRankerAgent(
        embedder=FailingEmbedder(),
        vector_store=MockVectorStore(),
    )

    with pytest.raises(RuntimeError, match="Candidate ranking failed"):
        agent.rank_candidates(SAMPLE_QUERY)


def test_rank_candidates_injected_dependencies():
    """Test that injected embedder and vector store are used correctly."""
    embedder = MockEmbedder()
    vector_store = MockVectorStore()

    agent = CandidateRankerAgent(
        embedder=embedder,
        vector_store=vector_store,
    )

    assert agent.embedder is embedder
    assert agent.vector_store is vector_store
    assert agent.vector_store.index.ntotal == 50
