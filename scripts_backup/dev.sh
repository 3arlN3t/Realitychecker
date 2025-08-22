#!/bin/bash

# Development Mode - WhatsApp Bot with Dashboard and ngrok
echo "🚀 Starting Reality Checker Development Environment"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper function to wait for services
wait_for_port() {
    local port=$1
    local service_name=$2
    echo "⏳ Waiting for $service_name on port $port..."
    local timeout=30
    local count=0
    while ! nc -z localhost "$port" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            echo "❌ Timeout waiting for $service_name on port $port"
            return 1
        fi
    done
    echo "✅ $service_name is ready!"
}

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:4040 | xargs kill -9 2>/dev/null || true
lsof -ti:6379 | xargs kill -9 2>/dev/null || true

# Start Redis (if available)
if command -v redis-server &> /dev/null; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes --port 6379 --logfile redis.log 2>/dev/null || true
    if wait_for_port 6379 "Redis"; then
        echo "✅ Redis started successfully"
    else
        echo "⚠️ Redis failed to start, continuing without it"
    fi
fi

# Start React Dashboard
echo "📊 Starting React Dashboard..."
if [ -d "dashboard" ]; then
    cd dashboard
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing dashboard dependencies..."
        npm install
    fi
    npm start > ../dashboard.log 2>&1 &
    cd "$SCRIPT_DIR"
    if wait_for_port 3000 "React Dashboard"; then
        echo "✅ Dashboard started successfully"
    else
        echo "❌ Dashboard failed to start"
    fi
else
    echo "⚠️ Dashboard directory not found, skipping dashboard startup"
fi

# Start FastAPI
echo "🐍 Starting API server..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
if wait_for_port 8000 "FastAPI Server"; then
    echo "✅ API server started successfully"
else
    echo "❌ API server failed to start"
    exit 1
fi

# Start ngrok
echo "🌐 Starting ngrok tunnel..."
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
if wait_for_port 4040 "ngrok"; then
    echo "✅ ngrok tunnel started successfully"
else
    echo "❌ ngrok failed to start"
fi

sleep 2

# Get webhook URL
WEBHOOK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel['public_url'] + '/webhook/whatsapp')
            break
except: pass
")

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📍 Service URLs:"
echo "   • Dashboard: http://localhost:3000"
echo "   • API Server: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"

if [ -n "$WEBHOOK_URL" ]; then
    echo "   • Public API (ngrok): ${WEBHOOK_URL%/webhook/whatsapp}"
    echo ""
    echo "🔗 Webhook URL for Twilio:"
    echo "   $WEBHOOK_URL"
    echo ""
    echo "📋 Twilio Console: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn"
    
    # Copy to clipboard (macOS)
    if command -v pbcopy &> /dev/null; then
        echo "$WEBHOOK_URL" | pbcopy
        echo "📋 Webhook URL copied to clipboard!"
    fi
else
    echo "   • ngrok: ❌ Failed to get public URL"
fi

echo ""
echo "📊 Log files:"
echo "   • API Server: server.log"
echo "   • Dashboard: dashboard.log"
echo "   • ngrok: ngrok.log"
if command -v redis-server &> /dev/null; then
    echo "   • Redis: redis.log"
fi

echo ""
echo "Press Ctrl+C to stop all services"
trap 'echo ""; echo "🛑 Stopping all services..."; kill 0; exit 0' SIGINT SIGTERM
wait