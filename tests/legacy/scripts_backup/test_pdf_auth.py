#!/usr/bin/env python3
"""
Test PDF authentication for Twilio URLs.
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_pdf_auth():
    """Test PDF download with proper Twilio authentication."""
    print("🧪 Testing PDF Authentication")
    print("=" * 50)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'NOT SET'}")
    
    # Test various PDF URL patterns
    test_urls = [
        "https://api.twilio.com/2010-04-01/Accounts/TEST/Messages/TEST/Media/TEST",
        "https://media.twiliocdn.com/TEST.pdf",
        "https://example.com/test.pdf"  # Non-Twilio URL for comparison
    ]
    
    timeout = httpx.Timeout(30.0)
    
    for url in test_urls:
        print(f"\n🔗 Testing URL: {url}")
        
        try:
            # Test both with and without auth
            auth = httpx.BasicAuth(account_sid, auth_token)
            headers = {
                'Accept': 'application/pdf, application/octet-stream, */*',
                'User-Agent': 'Reality-Checker-Bot/1.0'
            }
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                print("   🔓 Trying without authentication...")
                try:
                    response = await client.get(url, headers=headers)
                    print(f"   ✅ No auth: {response.status_code} - {len(response.content)} bytes")
                except Exception as e:
                    print(f"   ❌ No auth: {e}")
                
                print("   🔐 Trying with authentication...")
                try:
                    response = await client.get(url, auth=auth, headers=headers)
                    print(f"   ✅ With auth: {response.status_code} - {len(response.content)} bytes")
                except Exception as e:
                    print(f"   ❌ With auth: {e}")
                    
        except Exception as e:
            print(f"   ❌ General error: {e}")
    
    print("\n📋 Test Summary:")
    print("This test shows how PDF downloads behave with different authentication methods.")
    print("Real Twilio PDF URLs will require proper authentication.")

if __name__ == "__main__":
    asyncio.run(test_pdf_auth())