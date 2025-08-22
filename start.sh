#!/bin/bash

# Reality Checker WhatsApp Bot - Complete Development Environment Startup
# This script starts all services and configures WhatsApp integration

echo "🚀 Starting Reality Checker WhatsApp Bot Development Environment..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR"

# Parse command line arguments
SKIP_WHATSAPP_SETUP=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-whatsapp)
            SKIP_WHATSAPP_SETUP=true
            shift
            ;;
        --quiet)
            QUIET_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-whatsapp    Skip WhatsApp integration setup"
            echo "  --quiet           Minimize output"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# --- Dependency Checks ---
if [ "$QUIET_MODE" = false ]; then
    echo "🔍 Checking dependencies..."
fi

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

if [ "$QUIET_MODE" = false ]; then
    echo "✅ All dependencies found"
fi

# --- Helper Functions ---
wait_for_port() {
    local port=$1
    local service_name=$2
    if [ "$QUIET_MODE" = false ]; then
        echo "⏳ Waiting for $service_name on port $port..."
    fi
    local timeout=30
    local count=0
    while ! nc -z localhost "$port" 2>/dev/null; do
        sleep 0.5
        count=$((count + 1))
        if [ $count -ge $((timeout * 2)) ]; then
            echo "❌ Timeout waiting for $service_name on port $port"
            return 1
        fi
    done
    if [ "$QUIET_MODE" = false ]; then
        echo "✅ $service_name is ready!"
    fi
    return 0
}

check_twilio_credentials() {
    if [ "$QUIET_MODE" = false ]; then
        echo "🔍 Checking Twilio credentials..."
    fi
    
    if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ] || [ -z "$TWILIO_PHONE_NUMBER" ]; then
        if [ "$QUIET_MODE" = false ]; then
            echo "⚠️  Twilio credentials not found in .env file"
        fi
        return 1
    fi
    
    # Basic format validation
    if [[ ! "$TWILIO_ACCOUNT_SID" =~ ^AC[a-f0-9]{32}$ ]]; then
        if [ "$QUIET_MODE" = false ]; then
            echo "⚠️  Invalid Twilio Account SID format"
        fi
        return 1
    fi
    
    if [ "$QUIET_MODE" = false ]; then
        echo "✅ Twilio credentials found and formatted correctly"
    fi
    return 0
}

get_ngrok_url() {
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
            local url=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https' and '8000' in tunnel.get('config', {}).get('addr', ''):
            print(tunnel['public_url'])
            break
except: pass
" 2>/dev/null)
            if [ -n "$url" ]; then
                echo "$url"
                return 0
            fi
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

configure_whatsapp_webhook() {
    local webhook_url="$1"
    
    if [ "$QUIET_MODE" = false ]; then
        echo "🔧 Configuring WhatsApp webhook..."
    fi
    
    # Save webhook URL for reference
    echo "$webhook_url/webhook/whatsapp" > webhook_config.txt
    
    if [ "$QUIET_MODE" = false ]; then
        echo ""
        echo "📋 WhatsApp Webhook Configuration:"
        echo "   Webhook URL: $webhook_url/webhook/whatsapp"
        echo "   HTTP Method: POST"
        echo "   WhatsApp Number: $TWILIO_PHONE_NUMBER"
        echo ""
        echo "🔧 To complete WhatsApp setup:"
        echo "1. Go to: https://console.twilio.com/"
        echo "2. Navigate to: Messaging > Try it out > Send a WhatsApp message"
        echo "3. In the 'Sandbox Configuration' section:"
        echo "   - Set 'When a message comes in' to: $webhook_url/webhook/whatsapp"
        echo "   - Set HTTP method to: POST"
        echo "4. Save the configuration"
        echo ""
        echo "📱 To test with WhatsApp:"
        echo "1. Send 'join <sandbox-code>' to: $TWILIO_PHONE_NUMBER"
        echo "2. Then send job postings for analysis!"
        echo ""
    fi
    
    # Copy webhook URL to clipboard if available
    if command -v pbcopy &> /dev/null; then
        echo "$webhook_url/webhook/whatsapp" | pbcopy
        if [ "$QUIET_MODE" = false ]; then
            echo "📋 Webhook URL copied to clipboard!"
        fi
    fi
}

# --- Cleanup Function ---
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill processes on known ports more gracefully
    for port in 3000 8000 4040 6379; do
        if lsof -ti:$port >/dev/null 2>&1; then
            lsof -ti:$port | xargs kill -TERM 2>/dev/null || true
        fi
    done
    
    # Wait a moment, then force kill if needed
    sleep 2
    for port in 3000 8000 4040 6379; do
        if lsof -ti:$port >/dev/null 2>&1; then
            lsof -ti:$port | xargs kill -KILL 2>/dev/null || true
        fi
    done
    
    echo "✅ Services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# --- Kill Existing Processes ---
if [ "$QUIET_MODE" = false ]; then
    echo "🧹 Cleaning up existing processes..."
fi
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:6379 | xargs kill -9 2>/dev/null || true
lsof -ti:4040 | xargs kill -9 2>/dev/null || true

# --- Start Services ---

# Start Redis (if available)
if command -v redis-server &> /dev/null; then
    if [ "$QUIET_MODE" = false ]; then
        echo "🔴 Starting Redis..."
    fi
    redis-server --daemonize yes --port 6379 --logfile redis.log 2>/dev/null || true
    if wait_for_port 6379 "Redis"; then
        if [ "$QUIET_MODE" = false ]; then
            echo "✅ Redis started successfully"
        fi
    else
        if [ "$QUIET_MODE" = false ]; then
            echo "⚠️ Redis failed to start, continuing without it"
        fi
    fi
fi

# Start Dashboard
if [ "$QUIET_MODE" = false ]; then
    echo "📊 Starting React Dashboard..."
fi

if [ -d "dashboard" ]; then
    cd "$SCRIPT_DIR/dashboard"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        if [ "$QUIET_MODE" = false ]; then
            echo "📦 Installing dashboard dependencies..."
        fi
        npm install >/dev/null 2>&1
    fi
    
    npm start > ../dashboard.log 2>&1 &
    cd "$SCRIPT_DIR"
    
    if wait_for_port 3000 "React Dashboard"; then
        if [ "$QUIET_MODE" = false ]; then
            echo "✅ Dashboard started successfully"
        fi
    else
        echo "❌ Dashboard failed to start"
        exit 1
    fi
else
    if [ "$QUIET_MODE" = false ]; then
        echo "⚠️ Dashboard directory not found, skipping dashboard startup"
    fi
fi

# Start ngrok
if [ "$QUIET_MODE" = false ]; then
    echo "🌐 Starting ngrok tunnel..."
fi
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
if ! wait_for_port 4040 "ngrok"; then
    echo "❌ Failed to start ngrok. Please install ngrok or check if port 4040 is available."
    exit 1
fi

# Get ngrok public URL
if [ "$QUIET_MODE" = false ]; then
    echo "🔗 Getting ngrok public URL..."
fi

API_URL=$(get_ngrok_url)
if [ -n "$API_URL" ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo "✅ Public API URL: $API_URL"
    fi
    
    # Load environment variables for WhatsApp setup
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Configure WhatsApp webhook if not skipped
    if [ "$SKIP_WHATSAPP_SETUP" = false ]; then
        if check_twilio_credentials; then
            configure_whatsapp_webhook "$API_URL"
        else
            if [ "$QUIET_MODE" = false ]; then
                echo "⚠️  Skipping WhatsApp setup due to missing/invalid Twilio credentials"
                echo "   Please check your .env file and ensure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER are set"
            fi
        fi
    else
        if [ "$QUIET_MODE" = false ]; then
            echo "⏭️  Skipping WhatsApp setup (--skip-whatsapp flag used)"
        fi
    fi
else
    echo "⚠️  Could not get ngrok public URL. WhatsApp webhook setup skipped."
    echo "   You can manually configure the webhook later using: ./whatsapp-setup.sh"
fi

# Start FastAPI Server
if [ "$QUIET_MODE" = false ]; then
    echo "🐍 Starting FastAPI Server..."
fi

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

# Start the FastAPI server
if [ "$QUIET_MODE" = true ]; then
    # Run in background for quiet mode
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
else
    # Run with output for normal mode
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
fi

if ! wait_for_port 8000 "FastAPI Server"; then
    echo "❌ Failed to start FastAPI server. Check server.log for details."
    exit 1
fi

# Perform health check
if [ "$QUIET_MODE" = false ]; then
    echo "🏥 Performing health check..."
fi

sleep 2  # Give server time to fully initialize

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    if [ "$QUIET_MODE" = false ]; then
        echo "✅ Health check passed - all services are healthy"
    fi
else
    echo "⚠️  Health check failed - some services may not be ready"
    if [ "$QUIET_MODE" = false ]; then
        echo "   You can check http://localhost:8000/health for details"
    fi
fi

echo ""
echo "🎉 Reality Checker WhatsApp Bot is ready!"
echo ""
echo "📍 Service URLs:"
echo "   • Web Interface: http://localhost:8000"
echo "   • API Server: http://localhost:8000"
echo "   • Dashboard: http://localhost:3000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
if [ -n "$API_URL" ]; then
    echo "   • Public API (ngrok): $API_URL"
    echo "   • WhatsApp Webhook: $API_URL/webhook/whatsapp"
fi
echo ""
echo "📊 Log Files:"
echo "   • API Server: server.log (if running in background)"
echo "   • Dashboard: dashboard.log"
echo "   • ngrok: ngrok.log"
if command -v redis-server &> /dev/null; then
    echo "   • Redis: redis.log"
fi
echo ""
if [ "$SKIP_WHATSAPP_SETUP" = false ] && [ -n "$API_URL" ] && check_twilio_credentials >/dev/null 2>&1; then
    echo "🔗 WhatsApp Integration:"
    echo "   • Webhook configured for: $TWILIO_PHONE_NUMBER"
    echo "   • Complete setup in Twilio Console (see instructions above)"
    echo "   • Test by sending 'join <code>' to your Twilio WhatsApp number"
    echo "   • Or run: ./whatsapp-setup.sh for step-by-step instructions"
    echo ""
fi
echo "💡 Quick Test:"
echo "   curl -X POST http://localhost:8000/api/analyze/text \\"
echo "        -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "        -d 'job_text=Software Engineer at Google. Send \$500 for background check.'"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait indefinitely until user interrupts
wait