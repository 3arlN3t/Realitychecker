#!/bin/bash

# Quick Start Script for WhatsApp Bot Development
# Simplified version for rapid testing

echo "🚀 Quick Start - WhatsApp Bot"

# Kill existing processes
lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
lsof -ti:4040 | xargs -r kill -9 2>/dev/null || true
lsof -ti:4041 | xargs -r kill -9 2>/dev/null || true

# Start FastAPI server
echo "🐍 Starting FastAPI..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3

# Start ngrok
echo "🌐 Starting ngrok..."
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    # Try alternative port
    NGROK_URL=$(curl -s http://localhost:4041/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null)
fi

if [ -n "$NGROK_URL" ]; then
    WEBHOOK_URL="$NGROK_URL/webhook/whatsapp"
    
    echo ""
    echo "✅ Services Ready!"
    echo "🔗 Webhook URL: $WEBHOOK_URL"
    echo ""
    echo "📋 Configure in Twilio Console:"
    echo "https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn"
    echo ""
    echo "Press Ctrl+C to stop"
    
    # Save to clipboard if available
    if command -v pbcopy &> /dev/null; then
        echo "$WEBHOOK_URL" | pbcopy
        echo "📋 Webhook URL copied to clipboard!"
    fi
else
    echo "❌ Failed to get ngrok URL"
fi

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill 0; exit 0' SIGINT SIGTERM
wait