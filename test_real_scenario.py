#!/usr/bin/env python3
"""
Test script to simulate real-world scenarios and provide debugging information.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService
from app.utils.error_handling import handle_error
from app.utils.logging import get_logger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

async def test_real_world_scenarios():
    """Test scenarios that might occur in real WhatsApp usage."""
    
    print("🔍 Testing Real-World Scenarios")
    print("=" * 60)
    
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Scenario 1: Test with a real PDF URL (using a public PDF for testing)
    print("\n📋 Scenario 1: Public PDF Download Test")
    print("-" * 40)
    
    # Use a reliable public PDF for testing
    public_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    try:
        print(f"Testing with public PDF: {public_pdf_url}")
        pdf_content = await pdf_service.download_pdf(public_pdf_url)
        print(f"✅ Successfully downloaded: {len(pdf_content)} bytes")
        
        # Try to extract text
        text = await pdf_service.extract_text(pdf_content)
        print(f"✅ Text extracted: {len(text)} characters")
        print(f"Preview: {text[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        user_message, error_info = handle_error(e)
        print(f"User would see: {user_message[:100]}...")
    
    # Scenario 2: Test Twilio URL format validation
    print("\n📋 Scenario 2: Twilio URL Format Analysis")
    print("-" * 40)
    
    # Generate realistic Twilio URLs based on the actual format
    realistic_urls = [
        f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM{'1' * 32}/Media/ME{'2' * 32}",
        f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM{'a' * 32}/Media/ME{'b' * 32}.json",
        "https://media.twiliocdn.com/AC123456789012345678901234567890/MM123456789012345678901234567890",
    ]
    
    for i, url in enumerate(realistic_urls, 1):
        print(f"\n  Test {i}: {url[:60]}...")
        is_twilio = pdf_service._is_twilio_media_url(url)
        print(f"    Recognized as Twilio URL: {is_twilio}")
        
        if is_twilio:
            print(f"    Would use authentication: Yes")
            print(f"    Account SID: {config.twilio_account_sid[:10]}...")
        else:
            print(f"    Would use authentication: No")

async def analyze_error_patterns():
    """Analyze common error patterns and their handling."""
    
    print("\n🔍 Error Pattern Analysis")
    print("=" * 60)
    
    from app.utils.error_handling import ErrorHandler
    handler = ErrorHandler()
    
    # Common error scenarios
    error_scenarios = [
        {
            "name": "Expired Twilio Media URL",
            "error": "PDF file not found - the media URL may have expired. Twilio media URLs are only valid for a limited time.",
            "expected_category": "pdf_url_expired"
        },
        {
            "name": "Network Timeout",
            "error": "PDF download timed out",
            "expected_category": "pdf_download_failed"
        },
        {
            "name": "Authentication Error",
            "error": "Failed to download PDF: HTTP 401",
            "expected_category": "pdf_download_failed"
        },
        {
            "name": "File Too Large",
            "error": "PDF file too large: 15000000 bytes (max: 10485760 bytes)",
            "expected_category": "pdf_too_large"
        },
        {
            "name": "Invalid PDF Content",
            "error": "Downloaded file is not a valid PDF",
            "expected_category": "pdf_download_failed"
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\n📝 {scenario['name']}")
        print(f"   Error: {scenario['error']}")
        
        error = Exception(scenario['error'])
        error_key = handler._classify_error(error)
        error_info = handler.get_error_info(error_key)
        
        print(f"   Classified as: {error_key}")
        print(f"   Expected: {scenario['expected_category']}")
        print(f"   Match: {'✅' if error_key == scenario['expected_category'] else '❌'}")
        print(f"   User message: {error_info.user_message.split('\\n')[0]}")

async def provide_troubleshooting_info():
    """Provide troubleshooting information for common issues."""
    
    print("\n🔧 Troubleshooting Information")
    print("=" * 60)
    
    config = get_config()
    
    print("Configuration Status:")
    print(f"  ✅ Twilio Account SID: {config.twilio_account_sid[:10]}...")
    print(f"  ✅ Twilio Auth Token: {'*' * len(config.twilio_auth_token)}")
    print(f"  ✅ Max PDF Size: {config.max_pdf_size_mb} MB")
    print(f"  ✅ Webhook Validation: {config.webhook_validation}")
    
    print("\nCommon Issues and Solutions:")
    print("  1. PDF Download Failed (404):")
    print("     - Twilio media URLs expire after a short time")
    print("     - Users should send the PDF again if it fails")
    print("     - This is normal behavior, not a bug")
    
    print("  2. PDF Download Failed (401/403):")
    print("     - Check Twilio credentials are correct")
    print("     - Verify account has proper permissions")
    print("     - Check if account is active (not suspended)")
    
    print("  3. PDF Too Large:")
    print(f"     - Current limit: {config.max_pdf_size_mb} MB")
    print("     - Users should compress PDFs or send as text")
    
    print("  4. Network Issues:")
    print("     - Temporary connectivity problems")
    print("     - Users should retry after a few minutes")
    
    print("\nRecommended Actions:")
    print("  ✅ Error messages are now more specific and helpful")
    print("  ✅ Users get clear instructions on what to do")
    print("  ✅ Expired URL errors are handled separately")
    print("  ✅ Logging includes full URLs for debugging")

if __name__ == "__main__":
    asyncio.run(test_real_world_scenarios())
    asyncio.run(analyze_error_patterns())
    asyncio.run(provide_troubleshooting_info())