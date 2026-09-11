# Production Azure Dockerfile for AI Job Bot (Playwright + Python + PostgreSQL)
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS_MODE=true

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Ensure Chromium browser binaries are installed
RUN playwright install chromium

# Copy application source code
COPY . .

# Ensure data directories exist
RUN mkdir -p data/tailored_resumes logs

# Default command to run daily application cycle
CMD ["python", "run_daily.py"]
