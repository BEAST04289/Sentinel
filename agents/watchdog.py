"""Watchdog Agent - Continuous portfolio monitoring

Always-on agent that polls the vector store for portfolio-relevant events.
Triggers the Analyst agent when high-salience events are detected.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from agents.state import SentinelState
from data.vector_store import vector_store
from data.document_processor import calculate_salience

logger = logging.getLogger(__name__)

# Salience threshold for triggering analyst
SALIENCE_THRESHOLD = 0.3


async def watchdog_node_async(state: SentinelState) -> Dict[str, Any]:
    """
    Async watchdog implementation.
    Polls vector store for portfolio-relevant events.
    """
    portfolio = state.get("portfolio", ["NVDA", "TSLA", "AAPL"])
    seen_ids = set(state.get("seen_ids", []))
    
    logger.info(f"Watchdog scanning for: {portfolio}")
    
    # Build query for portfolio
    query_text = f"material events risks lawsuits investigations earnings {' '.join(portfolio)}"
    
    try:
        # Query the vector store
        results = await vector_store.query(
            query_text=query_text,
            k=20,
            time_window_seconds=300  # Last 5 minutes
        )
        
        # Filter for new, high-salience events
        relevant_events = []
        for doc in results:
            doc_id = doc.get("id")
            ticker = doc.get("ticker")
            
            # Skip if already seen
            if doc_id in seen_ids:
                continue
            
            # Skip if not in portfolio
            if ticker and ticker not in portfolio:
                continue
            
            # Calculate salience
            salience = calculate_salience(doc.get("text", ""))
            
            if salience >= SALIENCE_THRESHOLD:
                relevant_events.append({
                    **doc,
                    "salience": salience,
                    "headline": doc.get("text", "")[:100] + "..."
                })
        
        if relevant_events:
            # Return the most relevant event
            event = max(relevant_events, key=lambda x: x.get("salience", 0))
            new_seen_ids = list(seen_ids | {event["id"]})
            
            logger.info(f"Watchdog detected event: {event.get('ticker')} (salience: {event.get('salience'):.2f})")
            
            return {
                "detected_event": event,
                "seen_ids": new_seen_ids,
                "loop_count": state.get("loop_count", 0) + 1
            }
        
        logger.debug("Watchdog: No new events detected")
        return {
            "detected_event": None,
            "loop_count": state.get("loop_count", 0) + 1
        }
        
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        return {
            "detected_event": None,
            "loop_count": state.get("loop_count", 0) + 1
        }


def watchdog_node(state: SentinelState) -> Dict[str, Any]:
    """
    Synchronous wrapper for LangGraph compatibility.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(watchdog_node_async(state))
    finally:
        loop.close()
