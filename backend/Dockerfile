FROM python:3.11-slim

# Install system deps (sqlite, libgl for Pillow if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY src ./src

# Create runtime dirs
RUN mkdir -p /app/data /app/cache /app/cache/thumbs

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Environment for production
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false \
    DATA_DIR=/app/data \
    CACHE_DIR=/app/cache \
    THUMBNAILS_DIR=/app/cache/thumbs

# Run with gunicorn+uvicorn workers for prod
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
