#!/usr/bin/env python3
"""
Test script to simulate the complete webhook flow and identify where PDF download fails.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.models.data_models import TwilioWebhookRequest
from app.services.message_handler import MessageHandlerService
from app.utils.logging import get_logger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

async def test_webhook_flow():
    """Test the complete webhook flow with a simulated PDF message."""
    
    print("🔍 Testing Complete Webhook Flow")
    print("=" * 50)
    
    try:
        # Get configuration
        config = get_config()
        
        # Create message handler
        message_handler = MessageHandlerService(config)
        
        # Create a mock Twilio webhook request with PDF media
        # This simulates what would come from a real WhatsApp message with PDF
        mock_request = TwilioWebhookRequest(
            MessageSid="MM12345678901234567890123456789012",  # 34 chars
            From="whatsapp:+1234567890",
            To=f"whatsapp:{config.twilio_phone_number}",
            Body="",  # Empty body for media-only message
            NumMedia=1,
            MediaUrl0="https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test",
            MediaContentType0="application/pdf"
        )
        
        print(f"📨 Simulating webhook request:")
        print(f"   MessageSid: {mock_request.MessageSid}")
        print(f"   From: {mock_request.From}")
        print(f"   MediaUrl: {mock_request.MediaUrl0}")
        print(f"   ContentType: {mock_request.MediaContentType0}")
        
        # Mock the Twilio response service to avoid actually sending messages
        original_send_method = message_handler.twilio_service.send_analysis_result
        message_handler.twilio_service.send_analysis_result = AsyncMock(return_value=True)
        
        # Also mock the custom error message sending
        message_handler._send_custom_error_message = AsyncMock(return_value=True)
        
        print(f"\n📥 Processing message through MessageHandlerService...")
        
        # Process the message
        success = await message_handler.process_message(mock_request)
        
        print(f"✅ Message processing completed: {success}")
        
        # Check what methods were called
        if message_handler.twilio_service.send_analysis_result.called:
            print("📤 Analysis result would have been sent")
        elif message_handler._send_custom_error_message.called:
            print("📤 Error message would have been sent")
            # Get the call arguments to see what error message was sent
            call_args = message_handler._send_custom_error_message.call_args
            if call_args:
                error_message = call_args[0][1]  # Second argument is the message
                print(f"   Error message: {error_message[:100]}...")
        
        # Restore original method
        message_handler.twilio_service.send_analysis_result = original_send_method
        
    except Exception as e:
        print(f"❌ Error in webhook flow test: {e}")
        import traceback
        traceback.print_exc()

async def test_pdf_url_variations():
    """Test different PDF URL formats that might come from Twilio."""
    
    print("\n🔍 Testing PDF URL Variations")
    print("=" * 50)
    
    config = get_config()
    
    # Different URL formats that might come from Twilio
    test_urls = [
        # Standard Twilio media URL format
        f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM12345678901234567890123456789012/Media/ME12345678901234567890123456789012",
        
        # Media URL with .json extension
        f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM12345678901234567890123456789012/Media/ME12345678901234567890123456789012.json",
        
        # Shortened/redirect URL (sometimes Twilio uses these)
        "https://media.twiliocdn.com/test123456789",
        
        # URL with query parameters
        f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/MM12345678901234567890123456789012/Media/ME12345678901234567890123456789012?download=true",
    ]
    
    from app.services.pdf_processing import PDFProcessingService
    pdf_service = PDFProcessingService(config)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📋 Test {i}: {url[:80]}...")
        
        try:
            # Test if URL is recognized as Twilio URL
            is_twilio = pdf_service._is_twilio_media_url(url)
            print(f"   Recognized as Twilio URL: {is_twilio}")
            
            # Try to download (will likely fail but we can see the error)
            print(f"   Attempting download...")
            pdf_content = await pdf_service.download_pdf(url)
            print(f"   ✅ Unexpected success! Size: {len(pdf_content)} bytes")
            
        except Exception as e:
            print(f"   ❌ Expected error: {type(e).__name__}: {str(e)[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_webhook_flow())
    asyncio.run(test_pdf_url_variations())