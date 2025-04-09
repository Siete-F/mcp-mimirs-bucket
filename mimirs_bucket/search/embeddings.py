"""
Embedding service for generating and manipulating text embeddings.
"""

import logging
import numpy as np
from typing import List, Union
import importlib.util

# Configure standard logging for this module
logger = logging.getLogger("mimirs_bucket.embeddings")

def truncate_vector_for_display(vector: Union[List[float], np.ndarray], max_elements: int = 20) -> str:
    """
    Truncate a vector for display purposes.
    
    Args:
        vector: The vector to truncate
        max_elements: Maximum number of elements to show
        
    Returns:
        String representation of the truncated vector
    """
    if isinstance(vector, np.ndarray):
        vector = vector.tolist()
        
    if not vector:
        return "[]"
        
    if len(vector) <= max_elements:
        return str(vector)
    
    # Truncate the vector
    truncated = vector[:max_elements]
    truncated_str = str(truncated).rstrip(']') + ", ... ]"
    
    return f"{truncated_str} (length: {len(vector)})"


class EmbeddingService:
    """
    Service for generating vector embeddings from text using various models.
    
    This service provides methods to convert text into semantic vector embeddings
    that can be used for similarity search in the knowledge base.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service with the specified model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Default dimension for all-MiniLM-L6-v2
        
        # Try to load sentence-transformers
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Attempt to load the embedding model.
        
        Falls back to a simpler approach if the required libraries aren't available.
        """
        try:
            # Check if sentence-transformers is available
            if importlib.util.find_spec("sentence_transformers") is not None:
                # Import the library
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                
                # Get actual dimension from model
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Initialized embedding model: {self.model_name} (dim={self.dimension})")
            else:
                logger.warning("sentence-transformers not installed. Using fallback method.")
                self.model = None
        except Exception as e:
            logger.warning(f"Error loading embedding model: {e}. Using fallback method.")
            self.model = None
    
    def get_embeddings(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the given text.
        
        Args:
            text: Input text or list of texts to embed
            
        Returns:
            Embedding vectors as numpy array
        """
        if self.model is None:
            # Use fallback method if no model is available
            return self._fallback_embeddings(text)
        
        # Generate embeddings with the model
        try:
            return self.model.encode(text, normalize_embeddings=True)

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}. Falling back to simple method.")
            return self._fallback_embeddings(text)
    
    def _fallback_embeddings(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate simple fallback embeddings when no model is available.
        
        This uses a very basic approach that produces deterministic vectors
        based on word frequencies. Not as good as proper embeddings but
        provides some basic functionality.
        
        Args:
            text: Input text or list of texts
            
        Returns:
            Simple embedding vectors
        """
        # Convert to list if single string
        texts = [text] if isinstance(text, str) else text
        
        # Generate a simple embedding based on character frequencies
        # Not semantically meaningful but provides a deterministic vector
        embeddings = []
        
        for t in texts:
            # Start with zeros
            embedding = np.zeros(self.dimension, dtype=np.float32)
            
            if t:
                # Simple character frequency encoding
                for i, char in enumerate(t):
                    # Use character code to update vector elements
                    pos = ord(char) % self.dimension
                    embedding[pos] += 1.0 / (i + 1)  # Weight by position
                
                # Normalize
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
            
            embeddings.append(embedding)
        
        return np.array(embeddings[0] if isinstance(text, str) else embeddings)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def euclidean_distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Euclidean distance (lower is more similar)
        """
        return np.linalg.norm(vec1 - vec2)


# Create a singleton instance
_embedding_service = EmbeddingService()

def get_embeddings(text: Union[str, List[str]]) -> List[float]:
    """
    Get embeddings for text, returning them as a list of floats.
    
    This is a convenience function that handles the conversion from
    numpy arrays to Python lists for easier serialization.
    
    Args:
        text: Input text or list of texts to embed
        
    Returns:
        List of embedding values as float
    """
    embeddings = _embedding_service.get_embeddings(text)
    
    # Convert to list of floats for easier serialization
    if isinstance(text, str):
        return embeddings.tolist()
    else:
        return [emb.tolist() for emb in embeddings]
