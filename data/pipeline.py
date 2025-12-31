"""
Sentinel Pipeline - Enhanced with metrics tracking and percentiles
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field

from data.vector_store import get_vector_store, Document
from data.document_processor import process_document, calculate_salience

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Track pipeline performance metrics with percentiles"""
    documents_processed: int = 0
    documents_failed: int = 0
    total_latency_ms: float = 0
    avg_latency_ms: float = 0
    last_event_time: Optional[datetime] = None
    latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def record_success(self, latency_ms: float):
        self.documents_processed += 1
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.documents_processed
        self.latencies.append(latency_ms)
        self.last_event_time = datetime.now()
    
    def record_failure(self):
        self.documents_failed += 1
        self.last_event_time = datetime.now()
    
    def get_percentiles(self) -> Dict[str, float]:
        if not self.latencies:
            return {"p50": 0, "p95": 0, "p99": 0}
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        return {
            "p50": sorted_lat[int(n * 0.5)] if n > 0 else 0,
            "p95": sorted_lat[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_lat[int(n * 0.99)] if n > 0 else 0
        }
    
    @property
    def success_rate(self) -> float:
        total = self.documents_processed + self.documents_failed
        return self.documents_processed / total if total > 0 else 1.0


# Global metrics
metrics = PipelineMetrics()

# Recent events for dashboard
recent_events: deque = deque(maxlen=100)


async def process_upload(
    content: bytes,
    filename: str,
    source: str = "upload"
) -> Dict[str, Any]:
    """Process uploaded file content and index"""
    start_time = time.time()
    
    try:
        # Process into chunks
        chunks = await process_document(content, filename, source=source)
        
        if not chunks:
            metrics.record_failure()
            return {"status": "error", "message": "No content extracted"}
        
        # Convert to Documents
        vector_store = get_vector_store()
        documents = [
            Document(
                id=chunk.id,
                text=chunk.text,
                source=chunk.source,
                ticker=chunk.ticker,
                timestamp=chunk.timestamp,
                metadata=chunk.metadata,
                salience=chunk.salience
            )
            for chunk in chunks
        ]
        
        # Add to vector store
        result = await vector_store.add_documents(documents)
        
        # Calculate total latency
        total_time_ms = (time.time() - start_time) * 1000
        metrics.record_success(total_time_ms)
        
        # Get max salience
        max_salience = max(c.salience for c in chunks)
        
        # Create event record
        event_record = {
            "id": chunks[0].id,
            "filename": filename,
            "ticker": chunks[0].ticker,
            "chunks": len(chunks),
            "latency_ms": total_time_ms,
            "salience": max_salience,
            "timestamp": datetime.now().isoformat(),
            "status": "indexed"
        }
        
        recent_events.appendleft(event_record)
        
        logger.info(
            f"✅ Processed: {filename} in {total_time_ms:.0f}ms "
            f"({len(chunks)} chunks, salience: {max_salience:.2f})"
        )
        
        return {
            "status": "success",
            "filename": filename,
            "chunks": len(chunks),
            "ticker": chunks[0].ticker,
            "latency_ms": total_time_ms,
            "salience": max_salience,
            "document_ids": [c.id for c in chunks]
        }
        
    except Exception as e:
        metrics.record_failure()
        logger.error(f"❌ Error processing {filename}: {e}")
        return {"status": "error", "message": str(e)}


def get_pipeline_status() -> Dict[str, Any]:
    """Get current pipeline status and metrics"""
    vector_store = get_vector_store()
    stats = vector_store.get_stats()
    percentiles = metrics.get_percentiles()
    
    return {
        "status": "running",
        "documents_processed": metrics.documents_processed,
        "documents_failed": metrics.documents_failed,
        "success_rate": round(metrics.success_rate, 3),
        "avg_latency_ms": round(metrics.avg_latency_ms, 2),
        "latency_percentiles": percentiles,
        "last_event": metrics.last_event_time.isoformat() if metrics.last_event_time else None,
        "vector_store": stats
    }


def get_recent_events(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent indexing events"""
    return list(recent_events)[:limit]
