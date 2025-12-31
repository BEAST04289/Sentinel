"""
Sentinel Document Processor - Enhanced with PyMuPDF and intelligent chunking
"""

import logging
import re
import uuid
from typing import List, Optional, Tuple
from datetime import datetime
from io import BytesIO

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try PyMuPDF first (faster), fallback to PyPDF2
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    try:
        import PyPDF2
        PYPDF2_AVAILABLE = True
    except:
        PYPDF2_AVAILABLE = False

# Company to ticker mappings
COMPANY_TICKERS = {
    "NVIDIA": "NVDA", "NVIDIA CORPORATION": "NVDA",
    "TESLA": "TSLA", "TESLA INC": "TSLA", "TESLA MOTORS": "TSLA",
    "APPLE": "AAPL", "APPLE INC": "AAPL",
    "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
    "MICROSOFT": "MSFT", "MICROSOFT CORPORATION": "MSFT",
    "META": "META", "META PLATFORMS": "META", "FACEBOOK": "META",
    "AMAZON": "AMZN", "AMAZON.COM": "AMZN",
    "AMD": "AMD", "ADVANCED MICRO DEVICES": "AMD",
    "INTEL": "INTC", "INTEL CORPORATION": "INTC",
}

# Risk keywords for salience scoring
HIGH_RISK_KEYWORDS = [
    "lawsuit", "litigation", "class action", "settlement",
    "investigation", "subpoena", "sec investigation", "doj",
    "earnings miss", "revenue decline", "guidance lowered",
    "recall", "safety concern", "regulatory action",
    "data breach", "cybersecurity", "hack", "breach",
    "executive departure", "ceo resign", "cfo resign",
    "bankruptcy", "chapter 11", "restructuring", "layoff",
    "patent infringement", "intellectual property",
    "fraud", "violation", "delisting", "going concern"
]

MEDIUM_RISK_KEYWORDS = [
    "delay", "postpone", "suspend", "warning",
    "concern", "issue", "problem", "challenge",
    "below expectations", "disappointed"
]


class ProcessedChunk(BaseModel):
    id: str
    text: str
    source: str
    ticker: Optional[str]
    timestamp: datetime
    chunk_index: int
    total_chunks: int
    salience: float
    metadata: dict = {}


def extract_ticker_from_text(text: str) -> Optional[str]:
    """Extract ticker from document text"""
    text_upper = text.upper()
    
    for ticker in COMPANY_TICKERS.values():
        if f"({ticker})" in text_upper or f" {ticker} " in text_upper:
            return ticker
    
    for company, ticker in COMPANY_TICKERS.items():
        if company in text_upper:
            return ticker
    
    return None


def extract_ticker_from_filename(filename: str) -> Optional[str]:
    """Extract ticker from filename"""
    filename_upper = filename.upper()
    for ticker in COMPANY_TICKERS.values():
        if filename_upper.startswith(ticker) or f"_{ticker}" in filename_upper:
            return ticker
    return None


def calculate_salience(text: str) -> float:
    """Calculate risk salience score (0-1)"""
    text_lower = text.lower()
    score = 0.0
    
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text_lower:
            score += 0.2
    
    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in text_lower:
            score += 0.1
    
    high_count = sum(1 for kw in HIGH_RISK_KEYWORDS if kw in text_lower)
    if high_count >= 3:
        score += 0.2
    
    return min(score, 1.0)


def intelligent_chunk_text(
    text: str,
    min_tokens: int = 100,
    max_tokens: int = 400,
    overlap_tokens: int = 50
) -> List[str]:
    """Intelligent chunking with sentence boundaries and overlap"""
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text)
    
    def estimate_tokens(s: str) -> int:
        return int(len(s.split()) * 1.3)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sent_tokens = estimate_tokens(sentence)
        
        if current_tokens + sent_tokens > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            if overlap_tokens > 0:
                overlap = []
                count = 0
                for s in reversed(current_chunk):
                    count += estimate_tokens(s)
                    overlap.insert(0, s)
                    if count >= overlap_tokens:
                        break
                current_chunk = overlap
                current_tokens = count
            else:
                current_chunk = []
                current_tokens = 0
        
        current_chunk.append(sentence)
        current_tokens += sent_tokens
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks if chunks else [text]


def parse_pdf(content: bytes) -> Tuple[str, dict]:
    """Parse PDF using PyMuPDF (fast) or PyPDF2 (fallback)"""
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = [page.get_text("text", sort=True) for page in doc]
            full_text = "\n\n".join(t for t in text_parts if t.strip())
            metadata = {"page_count": len(doc), "parser": "pymupdf"}
            doc.close()
            return full_text, metadata
        except Exception as e:
            logger.error(f"PyMuPDF failed: {e}")
    
    if PYPDF2_AVAILABLE:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(content))
            text_parts = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n\n".join(t for t in text_parts if t.strip())
            return full_text, {"page_count": len(reader.pages), "parser": "pypdf2"}
        except Exception as e:
            logger.error(f"PyPDF2 failed: {e}")
    
    return "", {"error": "No PDF parser available"}


def parse_text(content: bytes) -> Tuple[str, dict]:
    """Parse plain text"""
    try:
        text = content.decode('utf-8')
    except:
        text = content.decode('latin-1', errors='ignore')
    return text, {"encoding": "utf-8"}


async def process_document(
    content: bytes,
    filename: str,
    source: str = "upload"
) -> List[ProcessedChunk]:
    """Process document into chunks"""
    filename_lower = filename.lower()
    
    # Check if content is text (for mock data)
    is_text = False
    try:
        decoded = content.decode('utf-8')
        if decoded.strip() and not decoded.startswith('%PDF'):
            is_text = True
    except:
        pass
    
    if filename_lower.endswith('.pdf') and not is_text:
        text, meta = parse_pdf(content)
    else:
        text, meta = parse_text(content)
    
    if not text.strip():
        logger.warning(f"No text from {filename}")
        return []
    
    ticker = extract_ticker_from_filename(filename) or extract_ticker_from_text(text)
    chunks = intelligent_chunk_text(text)
    timestamp = datetime.now()
    
    processed = []
    for i, chunk_text in enumerate(chunks):
        salience = calculate_salience(chunk_text)
        chunk = ProcessedChunk(
            id=str(uuid.uuid4()),
            text=chunk_text,
            source=source,
            ticker=ticker,
            timestamp=timestamp,
            chunk_index=i,
            total_chunks=len(chunks),
            salience=salience,
            metadata={"filename": filename, **meta}
        )
        processed.append(chunk)
    
    max_salience = max(c.salience for c in processed) if processed else 0
    logger.info(f"Processed {filename}: {len(chunks)} chunks, ticker={ticker}, salience={max_salience:.2f}")
    
    return processed
