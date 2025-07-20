#!/usr/bin/env python3
"""
Test script to debug Twilio message sending issues.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_send_message():
    """Test sending a message via Twilio to debug the 400 error."""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print("🧪 Testing Twilio Message Sending...")
    print(f"From: whatsapp:{from_number}")
    
    # You need to replace this with your actual WhatsApp number
    # Make sure you've joined the sandbox first!
    # Format must be "whatsapp:+1234567890" with country code
    to_number = input("Enter your WhatsApp number in format 'whatsapp:+1234567890': ")
    
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body="🧪 Test message from Reality Checker bot - PDF processing test",
            from_=f"whatsapp:{from_number}",
            to=to_number
        )
        
        print(f"✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print(f"   To: {to_number}")
        
    except TwilioException as e:
        print(f"❌ TwilioException: {e}")
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
            elif e.code == 21211:
                print("\n💡 Solution: Invalid 'to' phone number format")
                print("   Make sure to use format: whatsapp:+1234567890")

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Replace the 'to_number' with your actual WhatsApp number!")
    print("⚠️  Make sure you've joined the Twilio WhatsApp Sandbox first!")
    print()
    test_send_message()