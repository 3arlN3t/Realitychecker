#!/bin/bash

# Production Mode - WhatsApp Bot with Performance Optimizations
echo "🚀 Starting WhatsApp Bot (Production Mode with Performance Optimizations)"

# Set production environment
export DEVELOPMENT_MODE=false
export USE_MOCK_TWILIO=false
export WEBHOOK_VALIDATION=true

# Performance optimizations
export WEBHOOK_TIMEOUT=2.0
export WEBHOOK_ACKNOWLEDGMENT_TIMEOUT=0.5
export TASK_QUEUE_MAX_SIZE=1000
export TASK_QUEUE_WORKER_COUNT=5
export PERFORMANCE_MONITORING_ENABLED=true

# Redis optimizations
export REDIS_POOL_SIZE=20
export REDIS_MAX_CONNECTIONS=50
export REDIS_CONNECTION_TIMEOUT=5.0
export REDIS_SOCKET_TIMEOUT=5.0

# Database optimizations
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=30
export DB_POOL_TIMEOUT=30

# Check if Gunicorn is available for better production performance
if command -v gunicorn &> /dev/null; then
    echo "🐍 Starting API server with Gunicorn (production)..."
    gunicorn app.main:app \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
else
    echo "🐍 Starting API server with Uvicorn (production)..."
    python3 -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4
fi

echo "✅ Production server started on port 8000"