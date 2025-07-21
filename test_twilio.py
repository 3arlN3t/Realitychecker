#!/usr/bin/env python3
"""
Test script to verify Twilio credentials and send a test message.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import sys

def test_twilio_credentials():
    """Test Twilio credentials and send a test message."""
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not account_sid or not auth_token or not from_number:
        print("❌ Missing Twilio credentials in environment variables")
        print(f"TWILIO_ACCOUNT_SID: {'✅ Set' if account_sid else '❌ Missing'}")
        print(f"TWILIO_AUTH_TOKEN: {'✅ Set' if auth_token else '❌ Missing'}")
        print(f"TWILIO_PHONE_NUMBER: {'✅ Set' if from_number else '❌ Missing'}")
        return False
    
    print(f"Testing Twilio credentials:")
    print(f"- Account SID: {account_sid[:5]}...")
    print(f"- Auth Token: {auth_token[:5]}...")
    print(f"- From Number: {from_number}")
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Get account info to verify credentials
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Successfully authenticated with Twilio")
        print(f"- Account Status: {account.status}")
        print(f"- Account Type: {account.type}")
        
        # List available phone numbers
        incoming_phone_numbers = client.incoming_phone_numbers.list(limit=5)
        print(f"\nAvailable phone numbers:")
        for number in incoming_phone_numbers:
            print(f"- {number.phone_number} ({number.friendly_name})")
            print(f"  Capabilities: {number.capabilities}")
        
        # Check if the from_number is in the list of available numbers
        from_number_found = any(number.phone_number == from_number or 
                               number.phone_number == f"+{from_number.lstrip('+')}" 
                               for number in incoming_phone_numbers)
        
        if not from_number_found:
            print(f"\n⚠️ Warning: {from_number} not found in the first 5 available numbers")
        
        # Test sending a message if a to_number is provided
        if len(sys.argv) > 1:
            to_number = sys.argv[1]
            print(f"\nSending test message to {to_number}...")
            
            # Ensure WhatsApp prefix for both numbers
            if not from_number.startswith("whatsapp:"):
                whatsapp_from = f"whatsapp:{from_number}"
            else:
                whatsapp_from = from_number
                
            if not to_number.startswith("whatsapp:"):
                whatsapp_to = f"whatsapp:{to_number}"
            else:
                whatsapp_to = to_number
            
            message = client.messages.create(
                body="This is a test message from Reality Checker WhatsApp Bot",
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            print(f"✅ Message sent successfully!")
            print(f"- Message SID: {message.sid}")
            print(f"- Status: {message.status}")
        else:
            print("\nℹ️ No recipient number provided. Skipping message test.")
            print("To send a test message, run: python test_twilio.py whatsapp:+1234567890")
        
        return True
        
    except TwilioException as e:
        print(f"❌ Twilio Exception: {str(e)}")
        if hasattr(e, 'code'):
            print(f"- Error Code: {e.code}")
        if hasattr(e, 'msg'):
            print(f"- Error Message: {e.msg}")
        if hasattr(e, 'status'):
            print(f"- Status: {e.status}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_twilio_credentials()