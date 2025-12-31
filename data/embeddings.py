"""
Sentinel Embeddings Service - Local embeddings with multiple model support
No API costs, works offline, fast inference
"""

import asyncio
import logging
from typing import List, Literal
from functools import lru_cache
import numpy as np

logger = logging.getLogger(__name__)

# Model configurations
EMBEDDING_MODELS = {
    "minilm": {
        "name": "all-MiniLM-L6-v2",
        "dimension": 384,
        "max_length": 512,
        "description": "Fast, lightweight, good for most use cases"
    },
    "mpnet": {
        "name": "all-mpnet-base-v2", 
        "dimension": 768,
        "max_length": 512,
        "description": "Higher quality, slightly slower"
    }
}

class EmbeddingService:
    """Local embedding service using sentence-transformers"""
    
    def __init__(self, model_type: Literal["minilm", "mpnet"] = "minilm"):
        self.model_type = model_type
        self.config = EMBEDDING_MODELS[model_type]
        self.dimension = self.config["dimension"]
        self.max_length = self.config["max_length"]
        self.model = None
        self._initialized = False
        
    def _load_model(self):
        """Lazy load model on first use"""
        if self._initialized:
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.config['name']}")
            self.model = SentenceTransformer(self.config["name"])
            self._initialized = True
            logger.info(f"✓ Model loaded: {self.dimension}D embeddings")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self._initialized = True
    
    async def encode(
        self, 
        texts: List[str], 
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """Generate embeddings for texts"""
        if not texts:
            return np.array([])
        
        self._load_model()
        
        if self.model is None:
            # Fallback: deterministic hash-based embeddings
            return self._fallback_encode(texts)
        
        # Truncate texts
        truncated = [t[:self.max_length * 4] for t in texts]
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                truncated,
                normalize_embeddings=normalize,
                batch_size=batch_size,
                show_progress_bar=False
            )
        )
        
        return embeddings
    
    async def encode_single(self, text: str) -> np.ndarray:
        """Encode single text"""
        embeddings = await self.encode([text])
        return embeddings[0] if len(embeddings) > 0 else np.zeros(self.dimension)
    
    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """Fallback encoding using hash"""
        embeddings = []
        for text in texts:
            np.random.seed(hash(text) % (2**32))
            emb = np.random.randn(self.dimension).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
        return np.array(embeddings)
    
    def get_info(self) -> dict:
        return {
            "model": self.config["name"],
            "dimension": self.dimension,
            "type": self.model_type,
            "loaded": self._initialized
        }

# Global singleton
_embedding_service = None

def get_embedding_service(model_type: str = "minilm") -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_type)
    return _embedding_service
