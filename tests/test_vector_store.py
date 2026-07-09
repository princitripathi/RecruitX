import os
import tempfile
import pytest
import numpy as np
import faiss
from embeddings.vector_store import CandidateVectorStore

# Mock dimension for fast testing without needing actual models
TEST_DIMENSION = 3


def test_vector_store_initialization():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    assert store.dimension == TEST_DIMENSION
    assert store.index.ntotal == 0
    assert len(store.id_map) == 0


def test_vector_store_add_and_search():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    
    # Define candidates and their vectors
    # We will normalize these vectors manually for test predictability
    candidate_ids = [101, 102]
    # Candidate 101 is along X axis, 102 is along Y axis
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ]
    
    store.add_candidates(candidate_ids, embeddings)
    
    assert store.index.ntotal == 2
    assert store.id_map[0] == 101
    assert store.id_map[1] == 102
    
    # Query closest to X axis
    query = [0.9, 0.1, 0.0]
    results = store.search(query, top_k=2)
    
    assert len(results) == 2
    # Candidate 101 should be first (closer to query)
    assert results[0][0] == 101
    # Check similarity scores (should be between -1.0 and 1.0)
    assert results[0][1] > results[1][1]
    assert results[0][1] > 0.8
    
    # Query closest to Y axis
    query_y = [0.1, 0.9, 0.0]
    results_y = store.search(query_y, top_k=1)
    assert len(results_y) == 1
    assert results_y[0][0] == 102


def test_vector_store_empty_search():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    query = [1.0, 0.0, 0.0]
    results = store.search(query)
    assert results == []


def test_vector_store_add_mismatched_lengths():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    with pytest.raises(ValueError):
        store.add_candidates([101], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_vector_store_save_and_load():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    candidate_ids = [101, 102]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ]
    store.add_candidates(candidate_ids, embeddings)
    
    # Create temp files for saving
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test_index.bin")
        map_path = os.path.join(tmpdir, "test_map.pkl")
        
        # Save
        store.save(index_path, map_path)
        assert os.path.exists(index_path)
        assert os.path.exists(map_path)
        
        # Load in new store
        loaded_store = CandidateVectorStore(dimension=TEST_DIMENSION)
        loaded_store.load(index_path, map_path)
        
        assert loaded_store.index.ntotal == 2
        assert loaded_store.id_map[0] == 101
        assert loaded_store.id_map[1] == 102
        
        # Search on loaded store
        query = [0.9, 0.1, 0.0]
        results = loaded_store.search(query, top_k=1)
        assert len(results) == 1
        assert results[0][0] == 101


def test_vector_store_load_missing_files():
    store = CandidateVectorStore(dimension=TEST_DIMENSION)
    with pytest.raises(FileNotFoundError):
        store.load("non_existent_file.bin", "non_existent_file.pkl")


def test_vector_store_load_mismatched_dimension():
    store = CandidateVectorStore(dimension=5) # expected dimension is 5
    
    # Create an index with dimension 3 and save it
    temp_store = CandidateVectorStore(dimension=3)
    temp_store.add_candidates([1], [[1.0, 0.0, 0.0]])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test_index.bin")
        map_path = os.path.join(tmpdir, "test_map.pkl")
        
        temp_store.save(index_path, map_path)
        
        # Try loading with dimension 5 store
        with pytest.raises(ValueError):
            store.load(index_path, map_path)
