#!/usr/bin/env python3
"""
Debug script to test Twilio configuration and identify the exact error.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_twilio_config():
    """Test Twilio configuration and send a test message."""
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print("🔍 Testing Twilio Configuration...")
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    print(f"From Number: {from_number}")
    print()
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials!")
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
            print("⚠️  This is a TRIAL account - limited functionality")
        
        # List available phone numbers
        print("\n📱 Available phone numbers:")
        incoming_numbers = client.incoming_phone_numbers.list()
        for number in incoming_numbers:
            print(f"   {number.phone_number} - {number.friendly_name}")
        
        # Check WhatsApp capability
        print(f"\n🔍 Checking WhatsApp capability for {from_number}...")
        
        # For sandbox testing, we need to use a different verified number
        # Let's try to send a test message to a different number (you'll need to replace this)
        test_to_number = "whatsapp:+1234567890"  # Replace with your actual WhatsApp number
        
        print(f"\n📤 Attempting to send test message...")
        print(f"From: whatsapp:{from_number}")
        print(f"To: {test_to_number}")
        
        message = client.messages.create(
            body="🧪 Test message from Reality Checker bot",
            from_=f"whatsapp:{from_number}",
            to=test_to_number
        )
        
        print(f"✅ Test message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        
        return True
        
    except TwilioException as e:
        print(f"❌ TwilioException: {e}")
        print(f"   Error Code: {getattr(e, 'code', 'N/A')}")
        print(f"   Error Message: {getattr(e, 'msg', str(e))}")
        print(f"   More Info: {getattr(e, 'more_info', 'N/A')}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_twilio_config()
    if success:
        print("\n🎉 Twilio configuration is working!")
    else:
        print("\n💥 Twilio configuration has issues that need to be resolved.")