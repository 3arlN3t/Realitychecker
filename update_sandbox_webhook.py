#!/usr/bin/env python3
"""
Update Twilio WhatsApp Sandbox webhook URL.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def update_sandbox_webhook():
    """Update the WhatsApp sandbox webhook URL."""
    print("🔄 Updating Twilio WhatsApp Sandbox Webhook")
    print("=" * 50)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    webhook_url = "https://a991bb31b1f1.ngrok-free.app/webhook/whatsapp"
    
    print(f"Account SID: {account_sid}")
    print(f"Webhook URL: {webhook_url}")
    
    try:
        client = Client(account_sid, auth_token)
        
        # Update the WhatsApp sandbox settings
        print("\n📱 Updating WhatsApp sandbox configuration...")
        
        # Get and update sandbox settings
        sandbox = client.messaging.v1.services.create(
            friendly_name="Reality Checker WhatsApp Bot",
            inbound_request_url=webhook_url,
            inbound_method='POST'
        )
        
        print(f"✅ Sandbox updated successfully!")
        print(f"   Service SID: {sandbox.sid}")
        print(f"   Webhook URL: {webhook_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Try alternative approach - updating phone number directly
        try:
            print("\n🔄 Trying alternative approach...")
            numbers = client.incoming_phone_numbers.list()
            
            for number in numbers:
                if "+14155238886" in number.phone_number:
                    number.update(
                        sms_url=webhook_url,
                        sms_method='POST'
                    )
                    print(f"✅ Updated sandbox number {number.phone_number}")
                    return True
            
            print("❌ Sandbox number not found in phone numbers")
            return False
            
        except Exception as e2:
            print(f"❌ Alternative approach failed: {e2}")
            return False

if __name__ == "__main__":
    update_sandbox_webhook()