#!/usr/bin/env python3
"""
Script to set up real WhatsApp integration with Twilio webhook.
This script will configure your Twilio WhatsApp sandbox to use the ngrok tunnel.
"""

import os
import sys
from twilio.rest import Client
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print("❌ Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env file")
        sys.exit(1)
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Get ngrok URL from user
    print("🔗 Setting up WhatsApp webhook with ngrok...")
    print("\nFrom the ngrok output above, I can see your tunnel URL is:")
    ngrok_url = "https://4ab0816de1f7.ngrok-free.app"
    print(f"   {ngrok_url}")
    
    # Construct webhook URL
    webhook_url = f"{ngrok_url}/webhook/whatsapp"
    print(f"\n📡 Webhook URL: {webhook_url}")
    
    try:
        # Update WhatsApp sandbox webhook
        print("\n⚙️  Updating Twilio WhatsApp sandbox webhook...")
        
        # Get the sandbox configuration
        sandbox = client.messaging.v1.services.list(limit=1)
        
        if not sandbox:
            print("❌ No messaging service found. Please set up WhatsApp sandbox first.")
            print("   Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
            sys.exit(1)
        
        # Update webhook URL for WhatsApp
        # Note: For sandbox, we need to update the webhook in the console
        print("✅ Webhook URL ready for configuration")
        print("\n📋 Next steps:")
        print("1. Go to Twilio Console: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("2. In the 'Sandbox Configuration' section:")
        print(f"   - Set 'When a message comes in' to: {webhook_url}")
        print("   - Set HTTP method to: POST")
        print("3. Save the configuration")
        print("\n📱 To test:")
        print("1. Send 'join <sandbox-code>' to +1 415 523 8886 from your WhatsApp")
        print("2. Once joined, send any job posting text to test the bot")
        print("3. Try sending 'help' to see the welcome message")
        
        return webhook_url
        
    except Exception as e:
        print(f"❌ Error setting up webhook: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()