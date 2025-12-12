# Backend Dockerfile for Sonotheia Enhanced
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Install Python dependencies (Optimized for CPU-only Torch)
# Copy requirements
COPY requirements.txt .

# 1. Install Core Numerical Libs (Binary Wheels, Fast)
RUN pip install --no-cache-dir numpy scipy pandas

# 2. Install PyTorch CPU (Heavy, but isolated to prevent resolution limits)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 3. Install remaining dependencies (FastAPI, etc)
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code
# Copy application code into 'backend' directory to preserve package structure
COPY . backend/

# Set PYTHONPATH so 'backend' is recognized as a package
ENV PYTHONPATH=/app

# Expose port (Internal documentation)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; import os; import httpx; port = os.getenv('PORT', '8000'); sys.exit(0 if httpx.get(f'http://localhost:{port}/', timeout=5).status_code == 200 else 1)" || exit 1

# Run the application using shell form to allow variable expansion
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
