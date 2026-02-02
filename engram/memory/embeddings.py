"""
EmbeddingEngine - Local embeddings using sentence-transformers

Provides CPU-based embeddings with no API costs.
"""

import numpy as np
from typing import Union, List

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingEngine:
    """
    Local embedding engine using sentence-transformers.
    
    Default model: all-MiniLM-L6-v2
    - Size: ~80MB
    - Dimension: 384
    - Speed: Fast on CPU
    - Quality: Good for semantic search
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding engine.
        
        Args:
            model_name: Sentence-transformers model name
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
    
    def encode(
        self,
        text: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode text to embedding vector(s).
        
        Args:
            text: Single text or list of texts
            normalize: Normalize embeddings to unit length
        
        Returns:
            Embedding vector(s) as numpy array
        """
        embeddings = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        return embeddings
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()
