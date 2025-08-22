#!/usr/bin/env python3
"""
Test script to verify the fix for Twilio URL recognition.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService

async def test_twilio_url_recognition():
    """Test if the service correctly identifies all Twilio URL formats."""
    
    print("🔍 Testing Twilio URL Recognition Fix")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test URLs - all of these should be recognized as Twilio URLs
    test_urls = [
        "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages/SM123/Media/ME123",
        "https://media.twiliocdn.com/AC123/SM123/ME123",
        "https://s3.amazonaws.com/com.twilio.prod.twilio-api/AC123/SM123/ME123",
        "https://content.twiliocdn.com/v1/AC123/SM123/ME123"
    ]
    
    all_passed = True
    
    for url in test_urls:
        is_twilio = pdf_service._is_twilio_media_url(url)
        print(f"URL: {url}")
        print(f"Detected as Twilio URL: {'✅ Yes' if is_twilio else '❌ No'}")
        
        if not is_twilio:
            all_passed = False
            print("❌ FAILED: This URL should be recognized as a Twilio URL")
        print()
    
    # Test non-Twilio URLs - these should NOT be recognized as Twilio URLs
    non_twilio_urls = [
        "https://example.com/document.pdf",
        "https://drive.google.com/file/d/123/view",
        "https://s3.amazonaws.com/not-twilio/document.pdf"
    ]
    
    for url in non_twilio_urls:
        is_twilio = pdf_service._is_twilio_media_url(url)
        print(f"URL: {url}")
        print(f"Detected as Twilio URL: {'✅ Yes' if is_twilio else '❌ No'}")
        
        if is_twilio:
            all_passed = False
            print("❌ FAILED: This URL should NOT be recognized as a Twilio URL")
        print()
    
    if all_passed:
        print("✅ All tests passed! The URL recognition fix is working correctly.")
    else:
        print("❌ Some tests failed. The URL recognition fix needs adjustment.")

if __name__ == "__main__":
    asyncio.run(test_twilio_url_recognition())