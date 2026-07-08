import pytest
from embeddings.embedder import CandidateEmbedder, EMBEDDING_DIMENSION

def test_embed_text():
    embedder = CandidateEmbedder()
    text = "Python Developer with FastAPI experience"
    vector = embedder.embed_text(text)
    
    assert isinstance(vector, list)
    assert len(vector) == EMBEDDING_DIMENSION
    assert all(isinstance(x, float) for x in vector)

def test_embed_batch():
    embedder = CandidateEmbedder()
    texts = ["Python Developer", "Data Scientist with ML skills"]
    vectors = embedder.embed_batch(texts)
    
    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert len(vectors[0]) == EMBEDDING_DIMENSION
    assert len(vectors[1]) == EMBEDDING_DIMENSION

def test_embed_empty_text():
    embedder = CandidateEmbedder()
    with pytest.raises(ValueError):
        embedder.embed_text("")

def test_embed_empty_batch():
    embedder = CandidateEmbedder()
    with pytest.raises(ValueError):
        embedder.embed_batch([])
