#!/usr/bin/env python3
"""
Automatic Twilio Webhook Configuration Script
This script attempts to automatically configure the Twilio webhook URL
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from twilio.rest import Client

def get_ngrok_url():
    """Get the current ngrok URL"""
    try:
        # Try default port first
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
        
        # Try alternative port
        response = requests.get('http://localhost:4041/api/tunnels', timeout=5)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
                    
    except Exception as e:
        print(f"❌ Error getting ngrok URL: {e}")
    
    return None

def configure_twilio_webhook(webhook_url):
    """Configure Twilio webhook URL"""
    try:
        # Load environment variables
        load_dotenv()
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            print("❌ Twilio credentials not found in .env file")
            return False
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        print(f"🔧 Configuring webhook: {webhook_url}")
        
        # For sandbox, we need to update the webhook URL
        # Note: This typically requires manual configuration in the console
        # But we can provide instructions and validate the setup
        
        # Test if the webhook URL is accessible
        try:
            test_response = requests.get(f"{webhook_url.replace('/webhook/whatsapp', '/health')}", timeout=10)
            if test_response.status_code == 200:
                print("✅ Webhook URL is accessible")
            else:
                print(f"⚠️ Webhook URL returned status: {test_response.status_code}")
        except Exception as e:
            print(f"⚠️ Could not test webhook URL: {e}")
        
        # For production, you would update the webhook like this:
        # messaging_service = client.messaging.services.list(limit=1)[0]
        # messaging_service.update(inbound_request_url=webhook_url)
        
        print("✅ Webhook configuration ready")
        return True
        
    except Exception as e:
        print(f"❌ Error configuring webhook: {e}")
        return False

def main():
    print("🔗 Automatic Webhook Configuration")
    print("=" * 40)
    
    # Get ngrok URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Could not retrieve ngrok URL")
        print("Make sure ngrok is running: ngrok http 8000")
        sys.exit(1)
    
    webhook_url = f"{ngrok_url}/webhook/whatsapp"
    
    print(f"🌐 ngrok URL: {ngrok_url}")
    print(f"🔗 Webhook URL: {webhook_url}")
    
    # Configure webhook
    if configure_twilio_webhook(webhook_url):
        print("\n📋 Manual Configuration Required:")
        print("1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("2. In 'Sandbox Configuration':")
        print(f"   - Set 'When a message comes in' to: {webhook_url}")
        print("   - Set HTTP method to: POST")
        print("3. Save the configuration")
        
        print("\n📱 Testing:")
        print("1. Join sandbox: Send 'join <code>' to +1 415 523 8886")
        print("2. Test: Send 'help' to the bot")
        
        # Save configuration
        config = {
            "ngrok_url": ngrok_url,
            "webhook_url": webhook_url,
            "twilio_console": "https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn",
            "timestamp": str(os.popen('date').read().strip())
        }
        
        with open('current_webhook_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Configuration saved to: current_webhook_config.json")
        
        # Copy to clipboard if available (macOS)
        if os.system('which pbcopy > /dev/null 2>&1') == 0:
            os.system(f'echo "{webhook_url}" | pbcopy')
            print("📋 Webhook URL copied to clipboard!")
    
    else:
        print("❌ Failed to configure webhook")
        sys.exit(1)

if __name__ == "__main__":
    main()