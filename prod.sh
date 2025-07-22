#!/bin/bash

# Production Mode - WhatsApp Bot without ngrok
echo "🚀 Starting WhatsApp Bot (Production Mode)"

# Set production environment
export DEVELOPMENT_MODE=false
export USE_MOCK_TWILIO=false
export WEBHOOK_VALIDATION=true

# Start FastAPI in production mode
echo "🐍 Starting API server (production)..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

echo "✅ Production server started on port 8000"