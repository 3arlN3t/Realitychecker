# Multi-stage Dockerfile for Reality Checker WhatsApp Bot
# This Dockerfile builds both the backend API and frontend dashboard

# ============================================================================
# Stage 1: Build React Dashboard Frontend
# ============================================================================
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/dashboard

# Copy package files
COPY dashboard/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY dashboard/ ./

# Build the React application
RUN npm run build

# ============================================================================
# Stage 2: Python Backend Runtime
# ============================================================================
FROM python:3.11-slim AS backend

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dashboard/build ./static/

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]