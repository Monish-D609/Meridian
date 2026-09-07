# Meridian Backend — Dockerfile
# Optimized for Railway free tier (minimal image size, fast startup)

FROM python:3.11-slim

# Install system deps for psycopg2 + sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (small English model for claim extraction)
RUN python -m spacy download en_core_web_sm || true

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var automatically)
EXPOSE 8000

# Start with uvicorn (Railway uses the PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
