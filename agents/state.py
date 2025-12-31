"""Sentinel Agent State - Shared state for LangGraph agents"""

from typing import TypedDict, Optional, List, Set, Literal
from datetime import datetime


class DetectedEvent(TypedDict):
    """Structure for detected financial events"""
    id: str
    text: str
    ticker: str
    source: str
    timestamp: str
    score: float
    headline: Optional[str]


class AnalysisResult(TypedDict):
    """Structure for analyst output"""
    risk_level: Literal["HIGH", "MEDIUM", "LOW"]
    action: Literal["SELL", "REDUCE", "HOLD", "BUY"]
    confidence: float
    reasoning: List[str]
    counter_thesis: str


class SentinelState(TypedDict):
    """
    Persistent state shared across all agent nodes.
    This state is checkpointed after every step.
    """
    # User's portfolio tickers
    portfolio: List[str]
    
    # Latest detected high-salience event
    detected_event: Optional[DetectedEvent]
    
    # Set of document IDs already processed (deduplication)
    seen_ids: List[str]  # Using list for JSON serialization
    
    # Analyst's analysis result
    analysis: Optional[AnalysisResult]
    
    # Recommended action
    recommendation: Optional[str]
    
    # Confidence score 0.0 - 1.0
    confidence: float
    
    # Risk level
    risk_level: Optional[str]
    
    # Loop counter to prevent infinite loops
    loop_count: int
    
    # List of generated alerts
    alerts: List[dict]
