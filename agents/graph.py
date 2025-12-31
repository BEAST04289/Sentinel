"""Sentinel Agent Graph - LangGraph orchestration

Defines the agent workflow graph with Watchdog → Analyst routing.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from agents.state import SentinelState
from agents.watchdog import watchdog_node
from agents.analyst import analyst_node

logger = logging.getLogger(__name__)


def should_analyze(state: SentinelState) -> Literal["analyst", "watchdog", "end"]:
    """
    Conditional edge: decide whether to analyze or continue monitoring.
    """
    # If we have a detected event, analyze it
    if state.get("detected_event"):
        return "analyst"
    
    # Safety: prevent infinite loops
    if state.get("loop_count", 0) > 100:
        logger.warning("Loop limit reached, stopping")
        return "end"
    
    # Continue monitoring
    return "watchdog"


def build_sentinel_graph() -> StateGraph:
    """
    Build the Sentinel agent graph.
    
    Graph structure:
    
    START → watchdog → (event?) → analyst → watchdog
                    ↘ (no event) ↗
    """
    # Create graph with state schema
    builder = StateGraph(SentinelState)
    
    # Add nodes
    builder.add_node("watchdog", watchdog_node)
    builder.add_node("analyst", analyst_node)
    
    # Set entry point
    builder.set_entry_point("watchdog")
    
    # Add conditional edges from watchdog
    builder.add_conditional_edges(
        "watchdog",
        should_analyze,
        {
            "analyst": "analyst",
            "watchdog": "watchdog",
            "end": END
        }
    )
    
    # After analysis, return to monitoring
    builder.add_edge("analyst", "watchdog")
    
    return builder


def get_compiled_graph():
    """Get the compiled graph ready for execution"""
    builder = build_sentinel_graph()
    return builder.compile()


# Pre-built graph instance
sentinel_graph = None


def get_sentinel_graph():
    """Get or create the sentinel graph"""
    global sentinel_graph
    if sentinel_graph is None:
        sentinel_graph = get_compiled_graph()
    return sentinel_graph


def create_initial_state(portfolio: list = None) -> SentinelState:
    """Create initial state for a new agent run"""
    return {
        "portfolio": portfolio or ["NVDA", "TSLA", "AAPL"],
        "detected_event": None,
        "seen_ids": [],
        "analysis": None,
        "recommendation": None,
        "confidence": 0.0,
        "risk_level": None,
        "loop_count": 0,
        "alerts": []
    }
