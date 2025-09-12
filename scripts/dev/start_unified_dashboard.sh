#!/bin/bash

# Reality Checker - Unified Dashboard Startup Script
# This script starts the FastAPI backend with the integrated dashboard

echo "🚀 Starting Reality Checker with Unified Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8000/dashboard"
echo "🔗 Admin shortcut available at: http://localhost:8000/admin"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# Load dashboard environment variables
if [ -f ".env.dashboard" ]; then
    echo "📋 Loading dashboard environment variables..."
    export $(cat .env.dashboard | grep -v '^#' | xargs)
fi

# Start the server with development mode enabled
echo "🔥 Starting FastAPI server with development mode..."
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo ""
echo "✅ Server started successfully!"
echo "🌐 Open your browser and navigate to:"
echo "   • Dashboard: http://localhost:8000/dashboard"
echo "   • Admin: http://localhost:8000/admin"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"