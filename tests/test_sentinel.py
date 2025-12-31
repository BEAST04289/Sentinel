"""Test suite for Sentinel"""

import pytest
import asyncio
from datetime import datetime


def test_document_processor_chunking():
    """Test text chunking works correctly"""
    from data.document_processor import chunk_text
    
    # Short text should stay as one chunk
    short_text = "This is a short text."
    chunks = chunk_text(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    
    # Long text should be split
    long_text = " ".join(["word"] * 500)
    chunks = chunk_text(long_text)
    assert len(chunks) > 1


def test_ticker_extraction_from_filename():
    """Test ticker extraction from filenames"""
    from data.document_processor import extract_ticker_from_filename
    
    assert extract_ticker_from_filename("NVDA_8K.pdf") == "NVDA"
    assert extract_ticker_from_filename("TSLA_Recall.txt") == "TSLA"
    assert extract_ticker_from_filename("random.pdf") is None


def test_ticker_extraction_from_text():
    """Test ticker extraction from document text"""
    from data.document_processor import extract_ticker_from_text
    
    assert extract_ticker_from_text("NVIDIA Corporation (NVDA) filed...") == "NVDA"
    assert extract_ticker_from_text("Tesla announced...") == "TSLA"
    assert extract_ticker_from_text("Some random text") is None


def test_salience_calculation():
    """Test salience score calculation"""
    from data.document_processor import calculate_salience
    
    # High risk text
    high_risk = "class action lawsuit filed against company for patent infringement"
    assert calculate_salience(high_risk) >= 0.3
    
    # Low risk text
    low_risk = "quarterly earnings report shows steady growth"
    assert calculate_salience(low_risk) < 0.3


def test_mock_filings_available():
    """Test mock filings are properly configured"""
    from mock_data.mock_filings import MOCK_FILINGS, list_mock_filings
    
    assert len(MOCK_FILINGS) >= 3
    
    filings_list = list_mock_filings()
    assert len(filings_list) >= 3
    
    # Check required fields
    for filing in filings_list:
        assert "filename" in filing
        assert "ticker" in filing
        assert "headline" in filing


def test_sentinel_state_structure():
    """Test agent state structure"""
    from agents.state import SentinelState
    from agents.graph import create_initial_state
    
    state = create_initial_state(["NVDA", "TSLA"])
    
    assert state["portfolio"] == ["NVDA", "TSLA"]
    assert state["detected_event"] is None
    assert state["loop_count"] == 0
    assert isinstance(state["alerts"], list)


@pytest.mark.asyncio
async def test_vector_store_add_and_query():
    """Test vector store basic operations"""
    from data.vector_store import VectorStore, Document
    
    store = VectorStore()
    
    # Add a document
    doc = Document(
        id="test-123",
        text="NVIDIA announces new AI chip with breakthrough performance",
        source="test",
        ticker="NVDA",
        timestamp=datetime.now()
    )
    
    latency = await store.add_document(doc)
    assert latency > 0
    
    # Query should return it
    results = await store.query("NVIDIA AI chip", k=5)
    assert len(results) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
