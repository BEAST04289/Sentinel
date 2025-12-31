"""
Sentinel Hybrid Vector Store - ChromaDB + FAISS for best of both worlds
ChromaDB: Persistence, metadata filtering
FAISS: Ultra-fast similarity search (<100ms)
"""

import asyncio
import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class Document(BaseModel):
    """Document model with metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    source: str
    ticker: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    salience: float = 0.0
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class HybridVectorStore:
    """Hybrid vector store with FAISS speed + ChromaDB persistence"""
    
    def __init__(
        self,
        collection_name: str = "sentinel_docs",
        persist_directory: str = "./chroma_db",
        embedding_dim: int = 384
    ):
        self.collection_name = collection_name
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(exist_ok=True)
        self.dimension = embedding_dim
        
        # In-memory storage
        self.documents: Dict[str, Document] = {}
        self.embeddings: List[np.ndarray] = []
        self.doc_ids: List[str] = []
        
        # FAISS index
        if FAISS_AVAILABLE:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
            logger.info(f"FAISS index created ({self.dimension}D)")
        else:
            self.faiss_index = None
            logger.warning("FAISS not available")
        
        # ChromaDB collection
        self.chroma_client = None
        self.collection = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client(Settings(
                    persist_directory=str(self.persist_dir),
                    anonymized_telemetry=False
                ))
                try:
                    self.collection = self.chroma_client.get_collection(collection_name)
                except:
                    self.collection = self.chroma_client.create_collection(collection_name)
                logger.info(f"ChromaDB collection: {collection_name}")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}")
        
        # Embedding service
        from data.embeddings import get_embedding_service
        self.embedding_service = get_embedding_service()
        
        # Sync ID mappings
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        
        self._lock = asyncio.Lock()
        logger.info(f"✓ HybridVectorStore initialized")
    
    async def add_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Add documents with embeddings"""
        start_time = time.time()
        
        if not documents:
            return {"documents_added": 0, "latency_ms": 0}
        
        async with self._lock:
            # Generate embeddings
            texts = [doc.text for doc in documents]
            embeddings = await self.embedding_service.encode(texts, normalize=True)
            
            for i, doc in enumerate(documents):
                emb = embeddings[i]
                
                # Store document
                self.documents[doc.id] = doc
                self.embeddings.append(emb)
                
                # Update mappings
                idx = len(self.doc_ids)
                self.doc_ids.append(doc.id)
                self.id_to_idx[doc.id] = idx
                self.idx_to_id[idx] = doc.id
                
                # Add to FAISS
                if self.faiss_index is not None:
                    self.faiss_index.add(np.array([emb], dtype=np.float32))
                
                # Add to ChromaDB
                if self.collection is not None:
                    try:
                        self.collection.add(
                            ids=[doc.id],
                            embeddings=[emb.tolist()],
                            documents=[doc.text],
                            metadatas=[{
                                "source": doc.source,
                                "ticker": doc.ticker or "UNKNOWN",
                                "timestamp": doc.timestamp.isoformat(),
                                "salience": doc.salience
                            }]
                        )
                    except:
                        pass
        
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"Added {len(documents)} docs in {latency_ms:.0f}ms")
        
        return {
            "documents_added": len(documents),
            "total_documents": len(self.doc_ids),
            "latency_ms": latency_ms
        }
    
    async def add_document(self, doc: Document) -> Dict[str, Any]:
        """Add single document"""
        return await self.add_documents([doc])
    
    async def query(
        self,
        query_text: str,
        k: int = 10,
        ticker_filter: Optional[str] = None,
        min_salience: Optional[float] = None,
        time_window_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query with filters"""
        if not self.doc_ids:
            return []
        
        start_time = time.time()
        
        # Generate query embedding
        query_emb = await self.embedding_service.encode_single(query_text)
        query_np = np.array([query_emb], dtype=np.float32)
        
        # Search with FAISS
        search_k = min(k * 5, len(self.doc_ids))
        
        if self.faiss_index is not None and self.faiss_index.ntotal > 0:
            scores, indices = self.faiss_index.search(query_np, search_k)
            scores = scores[0]
            indices = indices[0]
        else:
            # Fallback: numpy search
            emb_matrix = np.array(self.embeddings)
            scores = np.dot(emb_matrix, query_np[0])
            indices = np.argsort(scores)[::-1][:search_k]
            scores = scores[indices]
        
        # Filter and build results
        results = []
        now = datetime.now()
        
        for score, idx in zip(scores, indices):
            if idx == -1 or int(idx) >= len(self.doc_ids):
                continue
            
            doc_id = self.doc_ids[int(idx)]
            doc = self.documents.get(doc_id)
            if not doc:
                continue
            
            # Apply filters
            if ticker_filter and doc.ticker != ticker_filter:
                continue
            
            if min_salience and doc.salience < min_salience:
                continue
            
            if time_window_hours:
                age = (now - doc.timestamp).total_seconds() / 3600
                if age > time_window_hours:
                    continue
            
            results.append({
                "id": doc.id,
                "text": doc.text,
                "source": doc.source,
                "ticker": doc.ticker,
                "timestamp": doc.timestamp.isoformat(),
                "salience": doc.salience,
                "score": float(score),
                "metadata": doc.metadata
            })
            
            if len(results) >= k:
                break
        
        query_ms = (time.time() - start_time) * 1000
        logger.debug(f"Query: {len(results)} results in {query_ms:.0f}ms")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        tickers = set(d.ticker for d in self.documents.values() if d.ticker)
        return {
            "total_documents": len(self.doc_ids),
            "embedding_dimension": self.dimension,
            "faiss_available": FAISS_AVAILABLE,
            "chroma_available": CHROMA_AVAILABLE,
            "unique_tickers": sorted(list(tickers))
        }
    
    def clear(self):
        """Clear all documents"""
        self.documents.clear()
        self.embeddings.clear()
        self.doc_ids.clear()
        self.id_to_idx.clear()
        self.idx_to_id.clear()
        if self.faiss_index is not None:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
        logger.info("Vector store cleared")


# Global instance
_vector_store = None

def get_vector_store() -> HybridVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = HybridVectorStore()
    return _vector_store

# Legacy compatibility
vector_store = None

def init_vector_store():
    global vector_store
    vector_store = get_vector_store()
    return vector_store
