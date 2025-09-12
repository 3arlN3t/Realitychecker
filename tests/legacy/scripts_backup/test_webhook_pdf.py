#!/usr/bin/env python3
"""
Script to test PDF webhook processing directly.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.services.message_handler import MessageHandlerService
from app.models.data_models import TwilioWebhookRequest
from app.config import get_config

async def test_pdf_webhook():
    """Test PDF webhook processing directly."""
    print("🧪 Testing PDF Webhook Processing")
    print("=" * 50)
    
    try:
        # Initialize services
        config = get_config()
        message_handler = MessageHandlerService(config)
        print("✅ Message handler initialized")
        
        # Test with a real PDF URL (you can replace this)
        test_pdf_url = input("Enter a PDF URL to test (or press Enter for mock): ").strip()
        
        if not test_pdf_url:
            test_pdf_url = "https://example.com/test.pdf"
            print(f"ℹ️  Using mock URL: {test_pdf_url}")
        
        # Create mock Twilio request
        twilio_request = TwilioWebhookRequest(
            MessageSid="TEST_MSG_SID_12345",
            From="whatsapp:+1234567890",
            To="whatsapp:+14155238886",
            Body="",
            NumMedia=1,
            MediaUrl0=test_pdf_url,
            MediaContentType0="application/pdf"
        )
        
        print(f"📄 Testing PDF processing with URL: {test_pdf_url}")
        
        # Process the message
        success = await message_handler.process_message(twilio_request)
        
        if success:
            print("✅ PDF webhook processing completed successfully!")
        else:
            print("❌ PDF webhook processing failed!")
        
    except Exception as e:
        print(f"❌ PDF webhook test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pdf_webhook())