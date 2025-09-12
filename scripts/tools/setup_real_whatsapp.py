#!/usr/bin/env python3
"""
Setup script for real WhatsApp integration with Twilio.
This script helps configure and test the WhatsApp bot with real Twilio services.
"""

import os
import sys
import requests
import json
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

def check_twilio_credentials():
    """Check if Twilio credentials are valid."""
    print("🔍 Checking Twilio credentials...")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, phone_number]):
        print("❌ Missing Twilio credentials in .env file")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Test API access by fetching account info
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Twilio Account: {account.friendly_name}")
        print(f"✅ Account Status: {account.status}")
        
        # Check WhatsApp phone number
        print(f"✅ WhatsApp Number: {phone_number}")
        
        return True
        
    except TwilioException as e:
        print(f"❌ Twilio API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_ngrok_tunnel():
    """Set up ngrok tunnel for webhook access."""
    print("\n🌐 Setting up ngrok tunnel...")
    
    # Check if ngrok is running
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        tunnels = response.json().get('tunnels', [])
        
        for tunnel in tunnels:
            if tunnel.get('proto') == 'https' and '8000' in tunnel.get('config', {}).get('addr', ''):
                public_url = tunnel['public_url']
                print(f"✅ Found existing ngrok tunnel: {public_url}")
                return public_url
                
    except requests.exceptions.RequestException:
        pass
    
    print("⚠️ No ngrok tunnel found. Please run:")
    print("   ngrok http 8000")
    print("   Then run this script again.")
    return None

def configure_twilio_webhook(webhook_url):
    """Configure Twilio webhook URL for WhatsApp."""
    print(f"\n🔧 Configuring Twilio webhook...")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    try:
        client = Client(account_sid, auth_token)
        
        # For sandbox, we need to configure the webhook URL manually
        # This is typically done through the Twilio Console
        webhook_endpoint = f"{webhook_url}/webhook/whatsapp"
        
        print(f"📋 Webhook Configuration:")
        print(f"   Webhook URL: {webhook_endpoint}")
        print(f"   HTTP Method: POST")
        print(f"   WhatsApp Number: {phone_number}")
        
        print("\n🔧 Manual Configuration Required:")
        print("1. Go to: https://console.twilio.com/")
        print("2. Navigate to: Messaging > Try it out > Send a WhatsApp message")
        print("3. In the 'Sandbox Configuration' section:")
        print(f"   - Set 'When a message comes in' to: {webhook_endpoint}")
        print("   - Set HTTP method to: POST")
        print("4. Save the configuration")
        
        return webhook_endpoint
        
    except Exception as e:
        print(f"❌ Error configuring webhook: {e}")
        return None

def test_webhook_endpoint(webhook_url):
    """Test if the webhook endpoint is accessible."""
    print(f"\n🧪 Testing webhook endpoint...")
    
    webhook_endpoint = f"{webhook_url}/webhook/whatsapp"
    
    try:
        # Test GET request
        response = requests.get(webhook_endpoint, timeout=10)
        if response.status_code == 200:
            print(f"✅ Webhook endpoint is accessible: {webhook_endpoint}")
            return True
        else:
            print(f"❌ Webhook returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach webhook endpoint: {e}")
        return False

def test_local_server():
    """Test if local server is running."""
    print("\n🔍 Testing local server...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local server is running: {data.get('status', 'unknown')}")
            
            # Check service statuses
            services = data.get('services', {})
            for service, status in services.items():
                if isinstance(status, dict):
                    status_val = status.get('status', status)
                else:
                    status_val = status
                    
                if status_val in ['healthy', 'ready']:
                    print(f"  ✅ {service}: {status_val}")
                else:
                    print(f"  ⚠️ {service}: {status_val}")
            
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Local server not accessible: {e}")
        print("Please start the server with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return False

def join_whatsapp_sandbox():
    """Provide instructions for joining WhatsApp sandbox."""
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print(f"\n📱 WhatsApp Sandbox Setup:")
    print("To test with real WhatsApp, you need to join the Twilio sandbox:")
    print()
    print("1. Open WhatsApp on your phone")
    print(f"2. Send a message to: {phone_number}")
    print("3. The message should be: join <sandbox-code>")
    print("   (You'll find the sandbox code in your Twilio Console)")
    print()
    print("4. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print("5. Find your sandbox code and send: join <code>")
    print()
    print("Example: join shadow-thumb")
    print()
    print("Once joined, you can send job postings to the bot for analysis!")

def create_test_script():
    """Create a test script for WhatsApp functionality."""
    test_script = '''#!/usr/bin/env python3
"""
Test script for real WhatsApp functionality.
Run this after setting up the webhook to test the bot.
"""

import requests
import time

def test_webhook_with_real_data():
    """Test webhook with realistic WhatsApp data."""
    
    # Test data that mimics real Twilio webhook
    test_data = {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",  # Replace with your phone number
        "To": "whatsapp:+14155238886",   # Twilio sandbox number
        "Body": "Software Engineer position at Google. $200k salary. Send $500 for background check.",
        "NumMedia": "0"
    }
    
    print("🧪 Testing webhook with realistic data...")
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook/whatsapp",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
            print("Check your WhatsApp for the bot's response.")
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_webhook_with_real_data()
'''
    
    with open('test_real_whatsapp.py', 'w') as f:
        f.write(test_script)
    
    print(f"\n📝 Created test_real_whatsapp.py for testing")

def main():
    """Main setup function."""
    print("🤖 REAL WHATSAPP SETUP FOR DEVELOPMENT")
    print("=" * 50)
    
    # Step 1: Check Twilio credentials
    if not check_twilio_credentials():
        print("\n❌ Setup failed: Invalid Twilio credentials")
        sys.exit(1)
    
    # Step 2: Check local server
    if not test_local_server():
        print("\n❌ Setup failed: Local server not running")
        sys.exit(1)
    
    # Step 3: Set up ngrok tunnel
    webhook_url = setup_ngrok_tunnel()
    if not webhook_url:
        print("\n❌ Setup failed: No ngrok tunnel available")
        sys.exit(1)
    
    # Step 4: Test webhook endpoint
    if not test_webhook_endpoint(webhook_url):
        print("\n❌ Setup failed: Webhook endpoint not accessible")
        sys.exit(1)
    
    # Step 5: Configure Twilio webhook
    webhook_endpoint = configure_twilio_webhook(webhook_url)
    if not webhook_endpoint:
        print("\n❌ Setup failed: Could not configure webhook")
        sys.exit(1)
    
    # Step 6: Provide sandbox instructions
    join_whatsapp_sandbox()
    
    # Step 7: Create test script
    create_test_script()
    
    print("\n" + "=" * 50)
    print("✅ SETUP COMPLETE!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Configure webhook URL in Twilio Console (see instructions above)")
    print("2. Join WhatsApp sandbox using your phone")
    print("3. Send test messages to the bot")
    print("4. Run: python3 test_real_whatsapp.py (for additional testing)")
    print()
    print(f"🔗 Your webhook URL: {webhook_endpoint}")
    print("📱 Monitor logs in your server terminal")
    print("🎯 Ready for real WhatsApp testing!")

if __name__ == "__main__":
    main()