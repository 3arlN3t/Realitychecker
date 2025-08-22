#!/usr/bin/env python3
"""
Test Twilio messaging directly.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def test_twilio_direct():
    """Test sending a message directly through Twilio."""
    print("🧪 Testing Twilio Direct Messaging")
    print("=" * 50)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print(f"Account SID: {account_sid}")
    print(f"From Number: {from_number}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials!")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Test with your WhatsApp number
        to_number = input("Enter your WhatsApp number (format: whatsapp:+1234567890): ").strip()
        
        if not to_number.startswith("whatsapp:"):
            to_number = "whatsapp:" + to_number if to_number.startswith("+") else "whatsapp:+" + to_number
        
        print(f"\n📤 Sending test message...")
        print(f"From: whatsapp:{from_number}")
        print(f"To: {to_number}")
        
        message = client.messages.create(
            body="🧪 Test message - PDF processing issue debug",
            from_=f"whatsapp:{from_number}",
            to=to_number
        )
        
        print(f"✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_twilio_direct()