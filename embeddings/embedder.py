import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_shared_model = None


class CandidateEmbedder:
    """
    A class to convert textual data into vector embeddings using SentenceTransformers.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        global _shared_model
        try:
            if _shared_model is not None:
                logger.info("Reusing cached SentenceTransformer model")
                self.model = _shared_model
            else:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading SentenceTransformer model: %s", model_name)
                _shared_model = SentenceTransformer(model_name)
                self.model = _shared_model
        except Exception as e:
            logger.error("Failed to initialize the embedding model: %s", str(e))
            raise RuntimeError(f"Could not load model {model_name}. Error: {e}")

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
            return embedding.tolist()
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
            return embeddings.tolist()
        except Exception as e:
            logger.error("Unexpected error during batch text embedding: %s", str(e))
            raise RuntimeError(f"Failed to embed batch text. Error: {e}")
