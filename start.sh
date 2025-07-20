#!/bin/bash

# Simplified and Optimized Startup Script

echo "🚀 Starting Development Environment..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR"

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
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

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

# Start FastAPI Server using run_server.py
echo "🐍 Starting FastAPI Server..."
python3 run_server.py &
wait_for_port 8000 "FastAPI Server"

# Fallback cleanup
cleanup