#!/usr/bin/env python3
"""
Verification script for WhatsApp sandbox setup.
This script helps verify and troubleshoot WhatsApp integration issues.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import sys

# Load environment variables
load_dotenv()

def verify_whatsapp_setup():
    """Verify WhatsApp sandbox setup and configuration."""
    
    print("🔍 WhatsApp Integration Verification")
    print("=" * 50)
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print("📱 Twilio Configuration:")
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    print(f"From Number: {from_number}")
    print()
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials!")
        print("   Please check your .env file and ensure all Twilio variables are set.")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        print("✅ Twilio client initialized successfully")
        
        # Test account access
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Account access verified: {account.friendly_name}")
        print(f"   Account Status: {account.status}")
        
        # Check if this is a trial account
        if account.type == 'Trial':
            print("⚠️  This is a TRIAL account - WhatsApp sandbox limitations apply")
            print("   You must use the sandbox for testing")
        
        # Check WhatsApp sandbox configuration
        print("\n🔍 Checking WhatsApp sandbox configuration...")
        
        try:
            # Get WhatsApp sandbox information
            whatsapp_settings = client.messaging.v1.services.list(friendly_name="Messaging Service")
            
            if whatsapp_settings:
                print("✅ Found Messaging Services:")
                for service in whatsapp_settings:
                    print(f"   - {service.friendly_name} (SID: {service.sid})")
            else:
                print("⚠️  No WhatsApp Messaging Services found")
                print("   This might be normal for sandbox testing")
            
            # List available phone numbers
            print("\n📱 Available phone numbers:")
            incoming_numbers = client.incoming_phone_numbers.list()
            
            whatsapp_numbers = []
            for number in incoming_numbers:
                print(f"   {number.phone_number} - {number.friendly_name}")
                
                # Check if this number has WhatsApp capability
                if number.capabilities.get("sms", False):
                    whatsapp_numbers.append(number.phone_number)
            
            if not whatsapp_numbers:
                print("⚠️  No numbers with SMS capability found (required for WhatsApp)")
            
            # Check webhook configuration
            print("\n🌐 Checking webhook configuration...")
            
            for number in incoming_numbers:
                if number.phone_number == from_number or from_number in number.phone_number:
                    print(f"   Found configuration for {number.phone_number}:")
                    print(f"   SMS URL: {number.sms_url}")
                    
                    if not number.sms_url:
                        print("❌ No webhook URL configured for SMS/WhatsApp!")
                        print("   You need to set up a webhook URL in the Twilio console")
                    elif "webhook/whatsapp" not in number.sms_url:
                        print("⚠️  Webhook URL doesn't contain 'webhook/whatsapp' path")
                        print("   Make sure it points to your WhatsApp webhook endpoint")
                    else:
                        print("✅ Webhook URL appears to be configured correctly")
            
            # Provide sandbox instructions
            print("\n📋 WhatsApp Sandbox Instructions:")
            print("1. Users must join your sandbox before you can message them")
            print("2. To join, users must send the following message to your WhatsApp number:")
            print(f"   'join <sandbox-code>' to {from_number}")
            print("3. Find your sandbox code in the Twilio Console > Messaging > Try it > WhatsApp")
            print("4. Only after joining can you send messages to users")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking WhatsApp configuration: {e}")
            return False
            
    except TwilioException as e:
        print(f"❌ TwilioException: {e}")
        print(f"   Error Code: {getattr(e, 'code', 'N/A')}")
        print(f"   Error Message: {getattr(e, 'msg', str(e))}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_send_whatsapp():
    """Test sending a WhatsApp message to a specific number."""
    
    print("\n🧪 Testing WhatsApp Message Sending")
    print("=" * 50)
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials!")
        return False
    
    # Get recipient number from user
    to_number = input("\nEnter recipient WhatsApp number (format: whatsapp:+1234567890): ")
    
    if not to_number.startswith("whatsapp:+"):
        print("❌ Invalid number format! Must start with 'whatsapp:+'")
        to_number = "whatsapp:" + to_number if to_number.startswith("+") else "whatsapp:+" + to_number
        print(f"   Corrected format: {to_number}")
    
    try:
        client = Client(account_sid, auth_token)
        
        print(f"\nSending test message:")
        print(f"From: whatsapp:{from_number}")
        print(f"To: {to_number}")
        
        message = client.messages.create(
            body="🧪 Test message from Reality Checker WhatsApp bot",
            from_=f"whatsapp:{from_number}",
            to=to_number
        )
        
        print(f"\n✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        
        print("\n📱 Next steps:")
        print("1. Check if the message was received on the recipient's WhatsApp")
        print("2. If not received, make sure the recipient has joined your sandbox")
        print("3. The recipient must send 'join <your-sandbox-code>' to your WhatsApp number")
        
        return True
        
    except TwilioException as e:
        print(f"\n❌ TwilioException: {e}")
        print(f"   Error Code: {getattr(e, 'code', 'N/A')}")
        print(f"   Error Message: {getattr(e, 'msg', str(e))}")
        
        # Common error codes and solutions
        if hasattr(e, 'code'):
            if e.code == 63007:
                print("\n💡 Solution: Your 'from' number is not configured for WhatsApp")
                print("   Use the Twilio WhatsApp Sandbox number instead")
                print(f"   Make sure you're using: whatsapp:{from_number}")
            elif e.code == 63016:
                print("\n💡 Solution: The 'to' number hasn't joined the WhatsApp sandbox")
                print("   The recipient must send 'join <sandbox-code>' to your WhatsApp number first")
                print("   Find your sandbox code in the Twilio Console > Messaging > Try it > WhatsApp")
            elif e.code == 21211:
                print("\n💡 Solution: Invalid 'to' phone number format")
                print("   Make sure to use format: whatsapp:+1234567890")
                print("   Include the country code with + sign")
        
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def check_webhook_configuration():
    """Check if webhook is properly configured."""
    
    print("\n🌐 Webhook Configuration Check")
    print("=" * 50)
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not all([account_sid, auth_token]):
        print("❌ Missing Twilio credentials!")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # List available phone numbers
        incoming_numbers = client.incoming_phone_numbers.list()
        
        webhook_configured = False
        for number in incoming_numbers:
            print(f"\nPhone number: {number.phone_number}")
            print(f"SMS URL: {number.sms_url or 'Not configured'}")
            
            if number.sms_url:
                webhook_configured = True
                if "webhook/whatsapp" in number.sms_url:
                    print("✅ Webhook URL contains 'webhook/whatsapp' path")
                else:
                    print("⚠️  Webhook URL doesn't contain 'webhook/whatsapp' path")
                    print("   Make sure it points to your WhatsApp webhook endpoint")
            else:
                print("❌ No webhook URL configured!")
        
        if not webhook_configured:
            print("\n❌ No webhooks configured for any phone numbers!")
            print("   You need to set up a webhook URL in the Twilio console:")
            print("   1. Go to Twilio Console > Phone Numbers > Manage > Active Numbers")
            print("   2. Click on your WhatsApp-enabled number")
            print("   3. Scroll down to 'Messaging' section")
            print("   4. Set 'A MESSAGE COMES IN' webhook to your endpoint URL")
            print("   5. Format: https://your-domain.com/webhook/whatsapp")
            print("   6. For local testing, use ngrok to create a public URL")
        
        # Check if ngrok is running
        print("\n🔍 Checking for ngrok tunnels...")
        try:
            import requests
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200:
                tunnels = response.json()["tunnels"]
                if tunnels:
                    print("✅ Found active ngrok tunnels:")
                    for tunnel in tunnels:
                        print(f"   {tunnel['public_url']} -> {tunnel['config']['addr']}")
                        if "8000" in tunnel["config"]["addr"]:
                            print(f"   💡 Webhook URL should be: {tunnel['public_url']}/webhook/whatsapp")
                else:
                    print("❌ No active ngrok tunnels found")
            else:
                print("❌ Could not connect to ngrok API")
        except Exception:
            print("❌ ngrok doesn't appear to be running")
            print("   Start ngrok with: ngrok http 8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking webhook configuration: {e}")
        return False

def main():
    """Main function to run verification checks."""
    
    print("🔍 Reality Checker WhatsApp Integration Verification")
    print("=" * 70)
    print("This script will help diagnose WhatsApp integration issues")
    print()
    
    while True:
        print("\nSelect an option:")
        print("1. Verify WhatsApp sandbox setup")
        print("2. Test sending a WhatsApp message")
        print("3. Check webhook configuration")
        print("4. Run all checks")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            verify_whatsapp_setup()
        elif choice == "2":
            test_send_whatsapp()
        elif choice == "3":
            check_webhook_configuration()
        elif choice == "4":
            verify_whatsapp_setup()
            test_send_whatsapp()
            check_webhook_configuration()
        elif choice == "5":
            print("\nExiting verification script.")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()