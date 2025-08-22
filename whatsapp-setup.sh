#!/bin/bash

# WhatsApp Setup Helper Script
# This script helps you complete the WhatsApp integration setup

echo "📱 WhatsApp Integration Setup Helper"
echo "===================================="

# Check if webhook config exists
if [ -f "webhook_config.txt" ]; then
    WEBHOOK_URL=$(cat webhook_config.txt)
    echo "✅ Found webhook URL: $WEBHOOK_URL"
else
    echo "❌ No webhook configuration found. Please run ./start.sh first."
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ No .env file found. Please create one with your Twilio credentials."
    exit 1
fi

echo ""
echo "🔧 Complete these steps to enable WhatsApp:"
echo ""
echo "1. 🌐 Open Twilio Console:"
echo "   https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn"
echo ""
echo "2. 📝 Configure Webhook:"
echo "   - When a message comes in: $WEBHOOK_URL"
echo "   - HTTP Method: POST"
echo ""
echo "3. 📱 Join WhatsApp Sandbox:"
echo "   - Send this message to: $TWILIO_PHONE_NUMBER"
echo "   - Message: join <your-sandbox-code>"
echo "   - (Find your sandbox code in the Twilio Console)"
echo ""
echo "4. 🧪 Test the Bot:"
echo "   - Send a job posting to: $TWILIO_PHONE_NUMBER"
echo "   - Example: 'Software Engineer at Google. Great salary!'"
echo ""

# Copy webhook URL to clipboard if available
if command -v pbcopy &> /dev/null; then
    echo "$WEBHOOK_URL" | pbcopy
    echo "📋 Webhook URL copied to clipboard!"
    echo ""
fi

echo "💡 Need help? Check the README.md or run: python3 setup_real_whatsapp.py"