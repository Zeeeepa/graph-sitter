# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[all]"

# Copy application code
COPY . .

# Create volume for sandbox environments
VOLUME /tmp/sandboxes

# Expose port
EXPOSE 8000

# Run migrations and start application
CMD alembic upgrade head && uvicorn src.app.main:app --host 0.0.0.0 --port 8000

