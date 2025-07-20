#!/usr/bin/env python3
"""
Debug script to test PDF webhook processing by simulating a PDF upload.
"""

import asyncio
import logging
from app.models.data_models import TwilioWebhookRequest
from app.services.message_handler import MessageHandlerService
from app.config import get_config
from app.utils.logging import setup_logging

# Setup logging
setup_logging("DEBUG")
logger = logging.getLogger(__name__)

async def test_pdf_processing():
    """Test PDF processing with a simulated webhook request."""
    
    print("🧪 Testing PDF Processing...")
    
    # Create a simulated PDF webhook request
    # This simulates what Twilio sends when a PDF is uploaded
    pdf_request = TwilioWebhookRequest(
        MessageSid="SM_test_pdf_123",
        From="whatsapp:+1234567890",  # Your test number
        To="whatsapp:+14155238886",   # Sandbox number
        Body="",  # Empty body for PDF-only message
        NumMedia=1,  # 1 media attachment
        MediaUrl0="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # Test PDF URL
        MediaContentType0="application/pdf"
    )
    
    print(f"📋 Simulated Request:")
    print(f"   MessageSid: {pdf_request.MessageSid}")
    print(f"   From: {pdf_request.From}")
    print(f"   To: {pdf_request.To}")
    print(f"   Body: '{pdf_request.Body}'")
    print(f"   NumMedia: {pdf_request.NumMedia}")
    print(f"   MediaUrl0: {pdf_request.MediaUrl0}")
    print(f"   MediaContentType0: {pdf_request.MediaContentType0}")
    print(f"   has_media: {pdf_request.has_media}")
    print(f"   is_pdf_media: {pdf_request.is_pdf_media}")
    print()
    
    try:
        # Initialize message handler
        config = get_config()
        message_handler = MessageHandlerService(config)
        
        print("🔄 Processing PDF message...")
        success = await message_handler.process_message(pdf_request)
        
        if success:
            print("✅ PDF processing completed successfully!")
        else:
            print("❌ PDF processing failed!")
            
    except Exception as e:
        print(f"💥 Error during PDF processing: {e}")
        logger.exception("PDF processing error")

if __name__ == "__main__":
    asyncio.run(test_pdf_processing())