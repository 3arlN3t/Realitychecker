#!/usr/bin/env python3
"""
Debug script to test the actual PDF download issue in production.
"""

import asyncio
import logging
import sys
import os
import httpx

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService, PDFDownloadError
from app.utils.logging import get_logger

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

async def test_twilio_auth():
    """Test Twilio authentication."""
    print("🔑 Testing Twilio Authentication")
    print("=" * 50)
    
    config = get_config()
    
    print(f"Account SID: {config.twilio_account_sid[:10]}...")
    print(f"Auth Token: {config.twilio_auth_token[:10]}...")
    print(f"Phone Number: {config.twilio_phone_number}")
    
    # Test basic Twilio API access
    test_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}.json"
    
    try:
        auth = httpx.BasicAuth(config.twilio_account_sid, config.twilio_auth_token)
        async with httpx.AsyncClient() as client:
            response = await client.get(test_url, auth=auth)
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Twilio authentication successful!")
            account_data = response.json()
            print(f"Account friendly name: {account_data.get('friendly_name', 'N/A')}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")

async def test_pdf_service_directly():
    """Test the PDF service with a non-existent URL to see the exact error."""
    print("\n🔧 Testing PDF Service Error Handling")
    print("=" * 50)
    
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test with a realistic but non-existent Twilio media URL
    test_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/SMtest123456789/Media/MEtest123456789"
    
    print(f"Testing URL: {test_url}")
    
    try:
        pdf_content = await pdf_service.download_pdf(test_url)
        print(f"✅ Unexpected success: {len(pdf_content)} bytes")
        
    except PDFDownloadError as e:
        print(f"❌ PDFDownloadError: {e}")
        print("This is the expected error type for PDF downloads.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")

async def test_url_validation():
    """Test URL validation logic."""
    print("\n🔍 Testing URL Validation")
    print("=" * 50)
    
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    test_urls = [
        "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test",
        "https://media.twiliocdn.com/some-media-file.pdf",
        "https://example.com/malicious.pdf",
        "http://api.twilio.com/test.pdf",  # HTTP instead of HTTPS
        "",  # Empty URL
        None  # None URL
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            if url is None:
                print("❌ None URL - will cause error")
                continue
                
            # Test URL validation first
            from app.utils.security import SecurityValidator
            validator = SecurityValidator()
            is_valid, error = validator.validate_url(url)
            
            print(f"URL validation: {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
            
            if is_valid:
                # Test if it's detected as Twilio URL
                is_twilio = pdf_service._is_twilio_media_url(url)
                print(f"Is Twilio URL: {'✅ Yes' if is_twilio else '❌ No'}")
                
        except Exception as e:
            print(f"❌ Error testing URL: {e}")

if __name__ == "__main__":
    asyncio.run(test_twilio_auth())
    asyncio.run(test_pdf_service_directly())
    asyncio.run(test_url_validation())