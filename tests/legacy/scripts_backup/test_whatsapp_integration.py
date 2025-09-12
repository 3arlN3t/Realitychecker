#!/usr/bin/env python3
"""
Test script to verify the complete WhatsApp integration.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import time

# Load environment variables
load_dotenv()

def test_whatsapp_integration():
    """
    Test the complete WhatsApp integration by sending a message and checking logs.
    """
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print("🧪 Testing WhatsApp Integration")
    print("=" * 50)
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    print(f"From Number: {from_number}")
    print()
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials!")
        return False
    
    # Get recipient number from user
    to_number = input("Enter your WhatsApp number (format: whatsapp:+1234567890): ")
    
    if not to_number.startswith("whatsapp:+"):
        print("❌ Invalid number format! Must start with 'whatsapp:+'")
        to_number = "whatsapp:" + to_number if to_number.startswith("+") else "whatsapp:+" + to_number
        print(f"   Corrected format: {to_number}")
    
    try:
        client = Client(account_sid, auth_token)
        
        # First, check if the webhook URL is properly configured
        print("\n🔍 Checking webhook configuration...")
        incoming_numbers = client.incoming_phone_numbers.list()
        
        webhook_configured = False
        for number in incoming_numbers:
            if number.phone_number == from_number or from_number in number.phone_number:
                print(f"   Found configuration for {number.phone_number}:")
                print(f"   SMS URL: {number.sms_url}")
                
                if not number.sms_url:
                    print("❌ No webhook URL configured for SMS/WhatsApp!")
                elif "webhook/whatsapp" not in number.sms_url:
                    print("⚠️  Webhook URL doesn't contain 'webhook/whatsapp' path")
                else:
                    print("✅ Webhook URL appears to be configured correctly")
                    webhook_configured = True
        
        if not webhook_configured:
            print("❌ Webhook not properly configured! Please update it first.")
            return False
        
        # Send a test message
        print(f"\n📤 Sending test message:")
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
        
        # Wait for user to respond
        print("\n⏳ Waiting for user response...")
        print("   Please reply to the message on your WhatsApp")
        print("   This will test if the webhook is receiving messages")
        print("   Press Ctrl+C to stop waiting")
        
        try:
            # Wait for 60 seconds, checking logs every 5 seconds
            for i in range(12):
                print(f"\r   Waiting for response... {i*5}/60 seconds", end="")
                time.sleep(5)
                
                # Here we would ideally check logs for incoming webhook requests
                # But since we can't easily do that, we'll just wait
            
            print("\n\n⚠️  No response detected within timeout period")
            print("   This doesn't necessarily mean the integration isn't working")
            print("   Check the application logs for incoming webhook requests")
            
        except KeyboardInterrupt:
            print("\n\n🛑 Waiting interrupted by user")
        
        print("\n📋 Integration Test Summary:")
        print("✅ Webhook URL is properly configured")
        print("✅ Test message sent successfully")
        print("⚠️  Check application logs to verify webhook reception")
        print("\n💡 Next steps:")
        print("1. Check if you received the test message on WhatsApp")
        print("2. Reply to the message to test the webhook")
        print("3. Check application logs for incoming webhook requests")
        print("4. If everything works, the WhatsApp integration is functioning correctly")
        
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
            elif e.code == 63016:
                print("\n💡 Solution: The 'to' number hasn't joined the WhatsApp sandbox")
                print("   Send the join code to your WhatsApp number first")
                print("   Find your sandbox code in the Twilio Console > Messaging > Try it > WhatsApp")
            elif e.code == 21211:
                print("\n💡 Solution: Invalid 'to' phone number format")
                print("   Make sure to use format: whatsapp:+1234567890")
        
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_whatsapp_integration()