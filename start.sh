#!/bin/bash

# Simplified and Optimized Startup Script

echo "🚀 Starting Development Environment..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR"

# --- Dependency Checks ---
echo "🔍 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js for dashboard
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found. Please install Node.js 18+"
    exit 1
fi

# Check ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok not found. Please install ngrok for webhook tunneling"
    exit 1
fi

# Check netcat for port checking
if ! command -v nc &> /dev/null; then
    echo "❌ Error: nc (netcat) not found. Please install netcat"
    exit 1
fi

echo "✅ All dependencies found"

# --- Helper Function to Wait for Services ---
wait_for_port() {
    local port=$1
    local service_name=$2
    echo "⏳ Waiting for $service_name on port $port..."
    while ! nc -z localhost "$port"; do
        sleep 0.5
    done
    echo "✅ $service_name is ready!"
}

# --- Cleanup Function ---
cleanup() {
    echo "🛑 Shutting down services..."
    kill 0 # Kills all processes in the script's process group
    echo "✅ Services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# --- Kill Existing Processes ---
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:6379 | xargs kill -9 2>/dev/null || true
lsof -ti:4040 | xargs kill -9 2>/dev/null || true

# --- Start Services ---

# Start Redis (if available)
if command -v redis-server &> /dev/null; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes --port 6379 --logfile redis.log
    wait_for_port 6379 "Redis"
fi

# Start Dashboard
echo "📊 Starting React Dashboard..."
cd "$SCRIPT_DIR/dashboard"
npm start > ../dashboard.log 2>&1 &
cd "$SCRIPT_DIR"
wait_for_port 3000 "React Dashboard"

# Start ngrok
echo "🌐 Starting ngrok..."
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
wait_for_port 4040 "ngrok"

API_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok-free\.app')
echo "🔗 API URL: $API_URL"

# Configure webhook automatically
if [ -n "$API_URL" ]; then
    WEBHOOK_URL="$API_URL/webhook/whatsapp"
    echo "🔗 Webhook URL: $WEBHOOK_URL"
    
    # Run webhook configuration script
    if [ -f "auto_webhook_config.py" ]; then
        echo "⚙️ Configuring webhook..."
        python3 auto_webhook_config.py
    fi
fi

# Start FastAPI Server
echo "🐍 Starting FastAPI Server..."

# Validate required files exist
if [ ! -f "$SCRIPT_DIR/app/main.py" ]; then
    echo "❌ Error: app/main.py not found!"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure environment variables are set."
fi

# Check if uvicorn is installed
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "❌ Error: uvicorn not installed. Install it with: pip install uvicorn"
    exit 1
fi

# Start the FastAPI server with proper configuration
python3 -c "
import uvicorn
import sys
from pathlib import Path

try:
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        reload_dirs=[str(Path('$SCRIPT_DIR') / 'app')],
        log_level='info'
    )
except KeyboardInterrupt:
    print('\n👋 Server stopped by user')
    sys.exit(0)
except Exception as e:
    print(f'❌ Error starting server: {e}')
    sys.exit(1)
" &

wait_for_port 8000 "FastAPI Server"

echo "🎉 All services are running!"
echo ""
echo "📍 Service URLs:"
echo "   • API Server: http://localhost:8000"
echo "   • Dashboard: http://localhost:3000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
if [ -n "$API_URL" ]; then
    echo "   • Public API (ngrok): $API_URL"
fi
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait indefinitely until user interrupts
wait