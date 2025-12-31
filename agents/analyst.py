"""Analyst Agent - Deep-dive financial analysis

Triggered by Watchdog when high-salience events are detected.
Performs multi-hop RAG and generates structured risk thesis.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from agents.state import SentinelState
from data.vector_store import vector_store

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_openai_client():
    """Get OpenAI client with API key"""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
    if api_key and OPENAI_AVAILABLE:
        return AsyncOpenAI(api_key=api_key)
    return None


ANALYST_PROMPT = """You are a senior financial risk analyst. A material event has been detected for a portfolio company.

EVENT DETAILS:
- Company/Ticker: {ticker}
- Event Text: {event_text}
- Source: {source}
- Detection Time: {timestamp}

HISTORICAL CONTEXT:
{context}

ANALYSIS INSTRUCTIONS:
Analyze this event's potential impact on the stock. Consider:
1. Historical precedents for similar events
2. Financial materiality (impact on revenue, margins, market cap)
3. Timeline expectations for resolution
4. Management's track record handling similar issues

Provide your analysis in the following JSON format ONLY (no other text):
{{
    "risk_level": "HIGH" or "MEDIUM" or "LOW",
    "action": "SELL" or "REDUCE" or "HOLD" or "BUY",
    "confidence": 0.0 to 1.0,
    "reasoning": ["point 1", "point 2", "point 3"],
    "counter_thesis": "Why this assessment could be wrong"
}}

Be specific. Cite evidence. No hedging language."""


async def analyst_node_async(state: SentinelState) -> Dict[str, Any]:
    """
    Async analyst implementation.
    Performs deep analysis on detected events.
    """
    event = state.get("detected_event")
    alerts = state.get("alerts", [])
    
    if not event:
        logger.debug("Analyst: No event to analyze")
        return {}
    
    ticker = event.get("ticker", "UNKNOWN")
    event_text = event.get("text", "")
    source = event.get("source", "unknown")
    timestamp = event.get("timestamp", datetime.now().isoformat())
    
    logger.info(f"Analyst analyzing: {ticker}")
    
    # Get historical context via RAG
    try:
        context_docs = await vector_store.query(
            query_text=f"historical {ticker} risks lawsuits earnings",
            k=10,
            ticker_filter=ticker,
            time_window_seconds=86400 * 30  # Last 30 days
        )
        
        context = "\n".join([
            f"[{d.get('source')}]: {d.get('text', '')[:200]}"
            for d in context_docs
        ]) or "No historical context available."
        
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        context = "Unable to retrieve historical context."
    
    # Generate analysis with LLM
    client = get_openai_client()
    
    if client:
        try:
            prompt = ANALYST_PROMPT.format(
                ticker=ticker,
                event_text=event_text[:1000],
                source=source,
                timestamp=timestamp,
                context=context
            )
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for speed/cost
                messages=[
                    {"role": "system", "content": "You are a precise financial analyst. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Parse response
            content = response.choices[0].message.content
            # Extract JSON from response
            try:
                # Try to find JSON in response
                if "{" in content:
                    json_str = content[content.find("{"):content.rfind("}")+1]
                    thesis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found")
            except:
                # Fallback analysis
                thesis = {
                    "risk_level": "MEDIUM",
                    "action": "HOLD",
                    "confidence": 0.5,
                    "reasoning": ["Event detected but analysis inconclusive"],
                    "counter_thesis": "Limited data available"
                }
            
            logger.info(f"Analyst result: {thesis.get('action')} ({thesis.get('confidence'):.0%} confidence)")
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            thesis = {
                "risk_level": "MEDIUM",
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": [f"Analysis error: {str(e)[:50]}"],
                "counter_thesis": "Unable to complete full analysis"
            }
    else:
        # No LLM available - use rule-based analysis
        logger.warning("No LLM available, using rule-based analysis")
        
        salience = event.get("salience", 0.5)
        if salience > 0.7:
            thesis = {
                "risk_level": "HIGH",
                "action": "REDUCE",
                "confidence": 0.6,
                "reasoning": ["High-salience event detected", "Risk keywords present in document"],
                "counter_thesis": "Event may resolve favorably"
            }
        elif salience > 0.4:
            thesis = {
                "risk_level": "MEDIUM",
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": ["Moderate risk event detected"],
                "counter_thesis": "Event may not materially impact stock"
            }
        else:
            thesis = {
                "risk_level": "LOW",
                "action": "HOLD",
                "confidence": 0.7,
                "reasoning": ["Low-salience event"],
                "counter_thesis": "May be more significant than detected"
            }
    
    # Create alert record
    alert = {
        "id": event.get("id"),
        "ticker": ticker,
        "headline": event.get("headline", event_text[:100]),
        "risk_level": thesis.get("risk_level"),
        "action": thesis.get("action"),
        "confidence": thesis.get("confidence"),
        "reasoning": thesis.get("reasoning"),
        "counter_thesis": thesis.get("counter_thesis"),
        "timestamp": datetime.now().isoformat(),
        "source": source
    }
    
    # Add to alerts list
    new_alerts = [alert] + alerts[:99]  # Keep last 100 alerts
    
    return {
        "analysis": thesis,
        "recommendation": thesis.get("action"),
        "confidence": thesis.get("confidence"),
        "risk_level": thesis.get("risk_level"),
        "alerts": new_alerts
    }


def analyst_node(state: SentinelState) -> Dict[str, Any]:
    """
    Synchronous wrapper for LangGraph compatibility.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(analyst_node_async(state))
    finally:
        loop.close()
