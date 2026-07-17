import gc
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_shared_model = None


def _configure_torch_threads() -> None:
    """
    Limit PyTorch to a single CPU thread to minimize memory overhead.
    On Render Free (512MB) each extra thread allocates ~30-50MB of scratch space.
    """
    try:
        import torch
        torch.set_num_threads(1)
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    except ImportError:
        pass


def preload_model(model_name: str = EMBEDDING_MODEL_NAME) -> None:
    """
    Eagerly load the SentenceTransformer model into the shared singleton cache.
    Call this once at application startup to avoid per-request loading overhead.
    Uses torch.float32 explicitly and single-thread to minimize memory.
    """
    global _shared_model
    if _shared_model is not None:
        return
    _configure_torch_threads()
    from sentence_transformers import SentenceTransformer
    logger.info("Pre-loading SentenceTransformer model: %s", model_name)
    _shared_model = SentenceTransformer(model_name)
    logger.info("SentenceTransformer model loaded successfully")


class CandidateEmbedder:
    """
    A class to convert textual data into vector embeddings using SentenceTransformers.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        logger.info("ENTER CandidateEmbedder")

        global _shared_model
        try:
            if _shared_model is not None:
                logger.info("Reusing cached SentenceTransformer model")
                self.model = _shared_model
            else:
                _configure_torch_threads()
                logger.info("STEP 1")
                from sentence_transformers import SentenceTransformer
                logger.info("STEP 2")

                logger.info("STEP 3")
                _shared_model = SentenceTransformer(model_name)
                logger.info("STEP 4")

                logger.info("Loading SentenceTransformer model: %s", model_name)
                self.model = _shared_model
        except Exception as e:
            logger.error("Failed to initialize the embedding model: %s", str(e))
            raise RuntimeError(f"Could not load model {model_name}. Error: {e}")

        logger.info("EXIT CandidateEmbedder")

    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text string into a vector embedding.
        Args:
            text: The input string to embed.
        Returns:
            A list of floats representing the embedding vector.
        Raises:
            ValueError: If the input text is empty or invalid.
            RuntimeError: If encoding fails.
        """
        if not text or not isinstance(text, str):
            logger.error("Invalid input text provided for embedding.")
            raise ValueError("Input text must be a non-empty string.")

        try:
            embedding = self.model.encode(text)
            result = embedding.tolist()
            del embedding
            gc.collect()
            return result
        except Exception as e:
            logger.error("Unexpected error during text embedding: %s", str(e))
            raise RuntimeError(f"Failed to embed text. Error: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a batch of text strings into vector embeddings.
        Args:
            texts: A list of input strings to embed.
        Returns:
            A list of embedding vectors (lists of floats).
        Raises:
            ValueError: If the input is not a list or is empty.
            RuntimeError: If encoding fails.
        """
        if not texts or not isinstance(texts, list):
            logger.error("Invalid input provided for batch embedding.")
            raise ValueError("Input must be a non-empty list of strings.")

        try:
            embeddings = self.model.encode(texts)
            result = embeddings.tolist()
            del embeddings
            gc.collect()
            return result
        except Exception as e:
            logger.error("Unexpected error during batch text embedding: %s", str(e))
            raise RuntimeError(f"Failed to embed batch text. Error: {e}")
