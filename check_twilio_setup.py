#!/usr/bin/env python3
"""
Check current Twilio WhatsApp setup and configuration.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def check_twilio_setup():
    """Check the current Twilio WhatsApp configuration."""
    print("🔍 Checking Twilio WhatsApp Setup")
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
        
        print("\n📞 Checking phone numbers...")
        incoming_numbers = client.incoming_phone_numbers.list()
        
        for number in incoming_numbers:
            print(f"\n📋 Phone Number: {number.phone_number}")
            print(f"   Friendly Name: {number.friendly_name}")
            print(f"   SMS URL: {number.sms_url}")
            print(f"   SMS Method: {number.sms_method}")
            print(f"   Voice URL: {number.voice_url}")
            print(f"   Capabilities: SMS={number.capabilities.get('sms', False)}, Voice={number.capabilities.get('voice', False)}")
            
            if number.phone_number == from_number:
                print("   ✅ This is your configured number!")
                if not number.sms_url:
                    print("   ⚠️  No SMS webhook URL configured!")
                elif "webhook/whatsapp" not in number.sms_url:
                    print("   ⚠️  SMS webhook URL doesn't contain 'webhook/whatsapp'")
                else:
                    print("   ✅ SMS webhook URL looks correct")
        
        print("\n📱 Checking WhatsApp Sandbox...")
        try:
            # Try to get WhatsApp sandbox settings
            sandbox_settings = client.messaging.services.list()
            if sandbox_settings:
                print(f"   Found {len(sandbox_settings)} messaging service(s)")
                for service in sandbox_settings:
                    print(f"   - Service SID: {service.sid}")
                    print(f"   - Friendly Name: {service.friendly_name}")
            else:
                print("   No messaging services found")
        except Exception as e:
            print(f"   Could not check messaging services: {e}")
        
        print("\n📊 Current webhook configuration:")
        print(f"   Expected: https://a991bb31b1f1.ngrok-free.app/webhook/whatsapp")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_twilio_setup()