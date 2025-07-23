#!/usr/bin/env python3
"""
Debug script to test Twilio CDN URL recognition and handling.
"""

import asyncio
import logging
import sys
import os
import httpx

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService
from app.utils.logging import get_logger, setup_logging

# Set up logging
setup_logging("DEBUG")
logger = get_logger(__name__)

async def test_twilio_cdn_url_detection():
    """Test if the service correctly identifies Twilio CDN URLs."""
    
    print("🔍 Testing Twilio CDN URL Detection")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test URLs
    test_urls = [
        "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages/SM123/Media/ME123",
        "https://media.twiliocdn.com/AC123/SM123/ME123",
        "https://s3.amazonaws.com/com.twilio.prod.twilio-api/AC123/SM123/ME123",
        "https://content.twiliocdn.com/v1/AC123/SM123/ME123"
    ]
    
    for url in test_urls:
        is_twilio = pdf_service._is_twilio_media_url(url)
        print(f"URL: {url}")
        print(f"Detected as Twilio URL: {'✅ Yes' if is_twilio else '❌ No'}")
        print()

async def test_cdn_url_download():
    """Test downloading from different URL formats."""
    
    print("\n🔍 Testing URL Download")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test with a public PDF URL that should work
    test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    print(f"Testing with public URL: {test_url}")
    
    try:
        # Try to download
        print("📥 Attempting download...")
        pdf_content = await pdf_service.download_pdf(test_url)
        print(f"✅ Download successful! Size: {len(pdf_content)} bytes")
        print(f"PDF header: {pdf_content[:20].hex()}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

async def test_twilio_url_recognition_fix():
    """Test an improved Twilio URL recognition function."""
    
    print("\n🔧 Testing Improved Twilio URL Recognition")
    print("=" * 50)
    
    def is_twilio_media_url(url: str) -> bool:
        """
        Improved function to check if a URL is a Twilio media URL.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if this is a Twilio media URL
        """
        url_lower = url.lower()
        return ('twilio.com' in url_lower or 
                'twiliocdn.com' in url_lower or
                ('s3.amazonaws.com' in url_lower and 'twilio' in url_lower))
    
    # Test URLs
    test_urls = [
        "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages/SM123/Media/ME123",
        "https://media.twiliocdn.com/AC123/SM123/ME123",
        "https://s3.amazonaws.com/com.twilio.prod.twilio-api/AC123/SM123/ME123",
        "https://content.twiliocdn.com/v1/AC123/SM123/ME123",
        "https://example.com/not-twilio.pdf"
    ]
    
    for url in test_urls:
        is_twilio = is_twilio_media_url(url)
        print(f"URL: {url}")
        print(f"Detected as Twilio URL: {'✅ Yes' if is_twilio else '❌ No'}")
        print()

if __name__ == "__main__":
    asyncio.run(test_twilio_cdn_url_detection())
    asyncio.run(test_cdn_url_download())
    asyncio.run(test_twilio_url_recognition_fix())