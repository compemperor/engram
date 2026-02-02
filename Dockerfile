FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
# Use CPU-only torch to avoid CUDA bloat
RUN pip install --no-cache-dir torch==2.5.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY engram/ ./engram/

# Create data directory
RUN mkdir -p /data/memories

# Expose API port
EXPOSE 8765

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MEMORY_PATH=/data/memories

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8765/health')" || exit 1

# Run Engram API
CMD ["python", "-m", "engram", "--host", "0.0.0.0", "--port", "8765"]
