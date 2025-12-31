# =============================================================================
# SENTINEL - Production Dockerfile
# Real-Time Financial Risk Agent
# =============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Sentinel Team"
LABEL description="Real-Time Financial Risk Agent with AI-powered analysis"
LABEL version="2.0.0"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash sentinel

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/sec_filings /app/chroma_db /app/logs && \
    chown -R sentinel:sentinel /app

# Switch to non-root user
USER sentinel

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
