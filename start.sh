#!/bin/bash

# Reality Checker WhatsApp Bot Startup Script
# This script sets up the complete development environment

echo "🚀 Starting Reality Checker WhatsApp Bot - Full Stack..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project root: $SCRIPT_DIR"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
echo "🐍 Python path: $PYTHONPATH"

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure environment variables are set."
fi

# Check if required directories exist
if [ ! -d "$SCRIPT_DIR/app" ]; then
    echo "❌ Error: app directory not found!"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/dashboard" ]; then
    echo "❌ Error: dashboard directory not found!"
    exit 1
fi

# Check if required commands are available
MISSING_COMMANDS=()

if ! command -v uvicorn &> /dev/null; then
    MISSING_COMMANDS+=("uvicorn (pip install uvicorn)")
fi

if ! command -v ngrok &> /dev/null; then
    MISSING_COMMANDS+=("ngrok (https://ngrok.com/download)")
fi

if ! command -v npm &> /dev/null; then
    MISSING_COMMANDS+=("npm (install Node.js)")
fi

if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis not found. Install with: brew install redis (optional for caching)"
fi

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo "❌ Missing required commands:"
    for cmd in "${MISSING_COMMANDS[@]}"; do
        echo "   - $cmd"
    done
    exit 1
fi

# Initialize database if needed
if [ ! -f "$SCRIPT_DIR/data/reality_checker.db" ]; then
    echo "🗄️  Initializing database..."
    mkdir -p "$SCRIPT_DIR/data"
    if [ -f "$SCRIPT_DIR/init_db.py" ]; then
        python "$SCRIPT_DIR/init_db.py"
    fi
fi

# Start Dashboard (React frontend)
echo "📊 Starting React Dashboard..."
cd "$SCRIPT_DIR/dashboard"
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dashboard dependencies..."
    npm install
fi
npm start > ../dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd "$SCRIPT_DIR"

# Start Redis (optional, for caching)
if command -v redis-server &> /dev/null; then
    echo "🔴 Starting Redis server..."
    redis-server --daemonize yes --port 6379 --logfile redis.log
    REDIS_STARTED=true
else
    echo "⚠️  Redis not available - caching disabled"
    REDIS_STARTED=false
fi

# Wait for dashboard to start
sleep 5

# Start ngrok tunnels
echo "🌐 Starting ngrok tunnels..."
# Tunnel for backend API
ngrok http 8000 --log=stdout > ngrok-api.log 2>&1 &
NGROK_API_PID=$!

# Tunnel for dashboard (if needed for external access)
ngrok http 3000 --log=stdout > ngrok-dashboard.log 2>&1 &
NGROK_DASHBOARD_PID=$!

# Wait for ngrok to start
sleep 3

# Get the ngrok URLs
API_NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok-free\.app' | head -1)
if [ -n "$API_NGROK_URL" ]; then
    echo "🔗 API Ngrok tunnel: $API_NGROK_URL"
    echo "📝 Use this URL for your WhatsApp webhook configuration"
else
    echo "⚠️  Could not retrieve API ngrok URL. Check ngrok-api.log for details"
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:8000"
cd "$SCRIPT_DIR"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down all services..."
    
    # Kill ngrok processes
    if [ -n "$NGROK_API_PID" ]; then
        kill $NGROK_API_PID 2>/dev/null
        echo "🔌 API Ngrok tunnel closed"
    fi
    
    if [ -n "$NGROK_DASHBOARD_PID" ]; then
        kill $NGROK_DASHBOARD_PID 2>/dev/null
        echo "🔌 Dashboard Ngrok tunnel closed"
    fi
    
    # Kill dashboard process
    if [ -n "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null
        echo "📊 Dashboard stopped"
    fi
    
    # Stop Redis if we started it
    if [ "$REDIS_STARTED" = true ]; then
        redis-cli shutdown 2>/dev/null || true
        echo "🔴 Redis stopped"
    fi
    
    # Kill any remaining processes on our ports
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:4040 | xargs kill -9 2>/dev/null || true
    lsof -ti:6379 | xargs kill -9 2>/dev/null || true
    
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Try to start with uvicorn
if command -v uvicorn &> /dev/null; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
else
    echo "❌ Error: uvicorn not found. Install it with: pip install uvicorn"
    cleanup
fi