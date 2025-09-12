#!/usr/bin/env python3
"""
Test script to simulate Twilio PDF download and see what errors occur.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService, PDFDownloadError
from app.utils.error_handling import handle_error
from app.utils.logging import get_logger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

async def test_twilio_pdf_download():
    """Test PDF download with various Twilio-like URLs to see what errors occur."""
    
    print("🔍 Testing Twilio PDF Download Scenarios")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test scenarios that might cause issues
    test_scenarios = [
        {
            "name": "Invalid Twilio URL (404)",
            "url": "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test.pdf"
        },
        {
            "name": "Non-existent domain",
            "url": "https://nonexistent-domain-12345.com/test.pdf"
        },
        {
            "name": "Timeout URL (httpbin delay)",
            "url": "https://httpbin.org/delay/35"  # 35 second delay, should timeout
        },
        {
            "name": "Non-PDF content",
            "url": "https://httpbin.org/json"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print(f"URL: {scenario['url']}")
        
        try:
            # Try to download
            print("📥 Attempting download...")
            pdf_content = await pdf_service.download_pdf(scenario['url'])
            print(f"✅ Unexpected success! Size: {len(pdf_content)} bytes")
            
        except PDFDownloadError as e:
            print(f"❌ PDFDownloadError: {e}")
            
            # Test error handling
            print("🔧 Testing error handling...")
            user_message, error_info = handle_error(e)
            print(f"User message preview: {user_message[:100]}...")
            print(f"Error category: {error_info.category}")
            print(f"Should retry: {error_info.should_retry}")
            
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {e}")
            
            # Test error handling for unexpected errors
            print("🔧 Testing error handling for unexpected error...")
            user_message, error_info = handle_error(e)
            print(f"User message preview: {user_message[:100]}...")
            print(f"Error category: {error_info.category}")

async def test_error_classification():
    """Test how different error messages are classified."""
    
    print("\n🔍 Testing Error Classification")
    print("=" * 50)
    
    from app.utils.error_handling import ErrorHandler
    
    handler = ErrorHandler()
    
    # Test various error messages that might occur
    test_errors = [
        "Failed to download PDF: HTTP 404",
        "Failed to download PDF: HTTP 401", 
        "Failed to download PDF: HTTP 403",
        "Network error downloading PDF: Connection timeout",
        "PDF download timed out",
        "Downloaded file is not a valid PDF",
        "PDF file too large: 15000000 bytes (max: 10485760 bytes)"
    ]
    
    for error_msg in test_errors:
        print(f"\n📝 Error: {error_msg}")
        error = Exception(error_msg)
        error_key = handler._classify_error(error)
        error_info = handler.get_error_info(error_key)
        print(f"   Classified as: {error_key}")
        print(f"   Category: {error_info.category}")
        print(f"   User message starts with: {error_info.user_message[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_twilio_pdf_download())
    asyncio.run(test_error_classification())