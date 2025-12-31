"""
Sentinel API - FastAPI Backend with Real-Time Alerts
Production-ready server with streaming updates
"""

import os
import sys
import logging
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.pipeline import process_upload, get_pipeline_status, get_recent_events
from data.vector_store import get_vector_store
from data.document_processor import calculate_salience
from mock_data.mock_filings import MOCK_FILINGS, get_mock_filing_content, list_mock_filings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Alerts store
alerts_store: List[dict] = []

# Agent state
agent_state = {
    "portfolio": ["NVDA", "TSLA", "AAPL"],
    "status": "monitoring",
    "last_scan": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("🛡️ Sentinel starting up...")
    # Initialize vector store
    get_vector_store()
    yield
    logger.info("Sentinel shutting down...")


app = FastAPI(
    title="Sentinel - Real-Time Financial Risk Agent",
    description="Event-driven RAG for financial risk monitoring",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Models ==========

class QueryRequest(BaseModel):
    query: str
    k: int = 10
    ticker: Optional[str] = None
    time_window_hours: Optional[int] = None


class PortfolioUpdate(BaseModel):
    tickers: List[str]


class SimulateEventRequest(BaseModel):
    filename: str


# ========== Health & Status ==========

@app.get("/")
async def root():
    return {"message": "Sentinel API is running", "docs": "/docs", "dashboard": "/dashboard"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.get("/api/status")
async def get_status():
    pipeline_status = get_pipeline_status()
    vector_store = get_vector_store()
    store_stats = vector_store.get_stats()
    
    return {
        "pipeline": pipeline_status,
        "vector_store": store_stats,
        "agent": agent_state,
        "alerts_count": len(alerts_store)
    }


# ========== Document Upload ==========

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename or "unknown.txt"
        
        logger.info(f"📄 Processing upload: {filename} ({len(content)} bytes)")
        
        result = await process_upload(content, filename)
        
        if result["status"] == "success":
            await check_and_generate_alert(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate")
async def simulate_event(request: SimulateEventRequest):
    content = get_mock_filing_content(request.filename)
    
    if not content:
        raise HTTPException(status_code=404, detail=f"Mock filing not found: {request.filename}")
    
    logger.info(f"🎬 Simulating: {request.filename}")
    
    result = await process_upload(content, request.filename)
    
    if result["status"] == "success":
        await check_and_generate_alert(result)
    
    return result


@app.get("/api/mock-filings")
async def get_mock_filings():
    return {"filings": list_mock_filings()}


# ========== Query ==========

@app.post("/api/query")
async def query_vector_store(request: QueryRequest):
    try:
        vector_store = get_vector_store()
        results = await vector_store.query(
            query_text=request.query,
            k=request.k,
            ticker_filter=request.ticker,
            time_window_hours=request.time_window_hours
        )
        
        return {"query": request.query, "results": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Alerts & Events ==========

@app.get("/api/alerts")
async def get_alerts():
    return {"alerts": alerts_store[:20]}


@app.get("/api/events")
async def get_events():
    return {"events": get_recent_events()}


# ========== Portfolio ==========

@app.get("/api/portfolio")
async def get_portfolio():
    return {"portfolio": agent_state["portfolio"]}


@app.post("/api/portfolio")
async def update_portfolio(update: PortfolioUpdate):
    agent_state["portfolio"] = update.tickers
    logger.info(f"Portfolio updated: {update.tickers}")
    return {"portfolio": agent_state["portfolio"]}


# ========== Alert Generation ==========

async def check_and_generate_alert(upload_result: dict):
    """Check if uploaded document should trigger an alert"""
    ticker = upload_result.get("ticker")
    filename = upload_result.get("filename", "")
    
    # Only alert for portfolio stocks
    if ticker not in agent_state["portfolio"]:
        return
    
    # Get document from vector store
    vector_store = get_vector_store()
    doc_ids = upload_result.get("document_ids", [])
    if not doc_ids:
        return
    
    doc = vector_store.documents.get(doc_ids[0])
    if not doc:
        return
    
    salience = doc.salience if hasattr(doc, 'salience') else calculate_salience(doc.text)
    
    # Threshold for alerting
    if salience < 0.3:
        return
    
    # Determine risk level and action
    if salience >= 0.7:
        risk_level = "HIGH"
        action = "REDUCE"
    elif salience >= 0.5:
        risk_level = "MEDIUM"
        action = "HOLD"
    else:
        risk_level = "LOW"
        action = "HOLD"
    
    # Get headline from mock data if available
    headline = doc.text[:150] + "..."
    for mock in MOCK_FILINGS:
        if mock["filename"] == filename:
            headline = mock["headline"]
            break
    
    # Generate reasoning
    reasoning = [
        f"Document matched portfolio ticker: {ticker}",
        f"Risk salience score: {salience:.2f}",
        f"Indexed in {upload_result.get('latency_ms', 0):.0f}ms"
    ]
    
    if salience >= 0.7:
        reasoning.append("High-risk keywords detected: lawsuit, investigation, or similar")
    elif salience >= 0.5:
        reasoning.append("Medium-risk content identified")
    
    alert = {
        "id": doc_ids[0],
        "ticker": ticker,
        "headline": headline,
        "filename": filename,
        "risk_level": risk_level,
        "action": action,
        "confidence": min(0.5 + salience * 0.5, 0.95),
        "salience": salience,
        "latency_ms": upload_result.get("latency_ms", 0),
        "timestamp": datetime.now().isoformat(),
        "reasoning": reasoning
    }
    
    alerts_store.insert(0, alert)
    if len(alerts_store) > 100:
        alerts_store.pop()
    
    logger.info(f"🚨 Alert generated: {ticker} - {risk_level} - {action}")


# ========== Dashboard ==========

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "ui", "dashboard.html")
    
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head><title>Sentinel</title></head>
<body style="background:#09090b;color:#fff;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;">
    <div style="text-align:center;">
        <h1 style="font-size:48px;">🛡️</h1>
        <h2>Sentinel Dashboard</h2>
        <p>Dashboard file not found. Check ui/dashboard.html</p>
        <a href="/docs" style="color:#6366f1;">API Docs</a>
    </div>
</body>
</html>
    """)


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🛡️ Starting Sentinel on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
