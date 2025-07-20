#!/usr/bin/env python3
"""
Script to update the Twilio webhook URL for WhatsApp integration.
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

# Load environment variables
load_dotenv()

def update_webhook_url(new_webhook_url):
    """
    Update the webhook URL for the Twilio phone number.
    
    Args:
        new_webhook_url: The new webhook URL to set
    """
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    print("🔄 Updating Twilio Webhook URL")
    print("=" * 50)
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    print(f"New Webhook URL: {new_webhook_url}")
    print()
    
    if not all([account_sid, auth_token]):
        print("❌ Missing Twilio credentials!")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        print("✅ Twilio client initialized successfully")
        
        # List available phone numbers
        incoming_numbers = client.incoming_phone_numbers.list()
        
        if not incoming_numbers:
            print("❌ No phone numbers found in your Twilio account!")
            return False
        
        updated = False
        for number in incoming_numbers:
            print(f"\nUpdating webhook for: {number.phone_number}")
            print(f"Current SMS URL: {number.sms_url or 'Not configured'}")
            
            try:
                # Update the webhook URL
                number.update(
                    sms_url=new_webhook_url,
                    sms_method='POST'
                )
                
                # Verify the update
                updated_number = client.incoming_phone_numbers(number.sid).fetch()
                print(f"✅ Updated SMS URL: {updated_number.sms_url}")
                updated = True
                
            except Exception as e:
                print(f"❌ Failed to update {number.phone_number}: {e}")
        
        if updated:
            print("\n✅ Webhook URL updated successfully!")
            print("   WhatsApp messages should now be forwarded to your application")
            return True
        else:
            print("\n❌ Failed to update any phone numbers")
            return False
            
    except TwilioException as e:
        print(f"❌ TwilioException: {e}")
        print(f"   Error Code: {getattr(e, 'code', 'N/A')}")
        print(f"   Error Message: {getattr(e, 'msg', str(e))}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Use the provided webhook URL or ask for input
    import sys
    
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    else:
        webhook_url = input("Enter the new webhook URL: ")
    
    # Ensure the URL ends with /webhook/whatsapp
    if not webhook_url.endswith("/webhook/whatsapp"):
        if webhook_url.endswith("/"):
            webhook_url += "webhook/whatsapp"
        else:
            webhook_url += "/webhook/whatsapp"
        print(f"URL adjusted to: {webhook_url}")
    
    update_webhook_url(webhook_url)