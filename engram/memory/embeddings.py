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
        normalize: bool = True,
        is_query: bool = False
    ) -> np.ndarray:
        """
        Encode text to embedding vector(s).
        
        Args:
            text: Single text or list of texts
            normalize: Normalize embeddings to unit length
            is_query: If True and using E5 model, add "query: " prefix
        
        Returns:
            Embedding vector(s) as numpy array
        """
        # E5 models require special prefixes
        if "e5-" in self.model_name.lower():
            if is_query:
                # Add "query: " prefix for search queries
                if isinstance(text, str):
                    text = f"query: {text}"
                else:
                    text = [f"query: {t}" for t in text]
            else:
                # Add "passage: " prefix for documents/memories
                if isinstance(text, str):
                    text = f"passage: {text}"
                else:
                    text = [f"passage: {t}" for t in text]
        
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
