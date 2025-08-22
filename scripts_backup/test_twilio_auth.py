#!/usr/bin/env python3
"""
Test script to verify Twilio authentication and credentials.
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config

async def test_twilio_auth():
    """Test Twilio authentication by making a simple API call."""
    
    print("🔍 Testing Twilio Authentication")
    print("=" * 50)
    
    try:
        # Get configuration
        config = get_config()
        
        print(f"Account SID: {config.twilio_account_sid[:10]}...")
        print(f"Auth Token: {'*' * len(config.twilio_auth_token)}")
        print(f"Phone Number: {config.twilio_phone_number}")
        
        # Test basic Twilio API access
        print("\n📞 Testing Twilio API access...")
        
        # Make a simple API call to verify credentials
        url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}.json"
        auth = httpx.BasicAuth(config.twilio_account_sid, config.twilio_auth_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth)
            
            if response.status_code == 200:
                print("✅ Twilio authentication successful!")
                account_info = response.json()
                print(f"   Account Status: {account_info.get('status', 'unknown')}")
                print(f"   Account Type: {account_info.get('type', 'unknown')}")
            elif response.status_code == 401:
                print("❌ Twilio authentication failed - Invalid credentials")
                print(f"   Response: {response.text}")
            else:
                print(f"❌ Twilio API error: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing Twilio auth: {e}")

async def test_media_url_format():
    """Test what a typical Twilio media URL looks like."""
    
    print("\n🔍 Testing Media URL Format")
    print("=" * 50)
    
    try:
        config = get_config()
        
        # Example of what a real Twilio media URL looks like
        example_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Media/MEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        
        print(f"Example media URL format:")
        print(f"  {example_url}")
        
        print(f"\nURL components:")
        print(f"  Base: https://api.twilio.com/2010-04-01/Accounts/")
        print(f"  Account SID: {config.twilio_account_sid}")
        print(f"  Message SID: MMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (34 chars)")
        print(f"  Media SID: MEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (34 chars)")
        
        # Test authentication with a fake media URL (will 404 but should authenticate)
        print(f"\n📥 Testing authentication with fake media URL...")
        
        fake_media_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM00000000000000000000000000000000/Media/ME00000000000000000000000000000000"
        auth = httpx.BasicAuth(config.twilio_account_sid, config.twilio_auth_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(fake_media_url, auth=auth)
            
            if response.status_code == 404:
                print("✅ Authentication works (404 = authenticated but resource not found)")
            elif response.status_code == 401:
                print("❌ Authentication failed (401 = unauthorized)")
            else:
                print(f"🤔 Unexpected response: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"❌ Error testing media URL: {e}")

if __name__ == "__main__":
    asyncio.run(test_twilio_auth())
    asyncio.run(test_media_url_format())