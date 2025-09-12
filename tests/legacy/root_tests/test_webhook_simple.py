#!/usr/bin/env python3
"""
Simple webhook test script to verify WhatsApp webhook functionality.
"""
import asyncio
import sys
from app.config import get_config
from app.models.data_models import TwilioWebhookRequest
from app.services.message_handler import MessageHandlerService

async def test_webhook_simple():
    """Test the webhook with a simple message."""
    print("🚀 Starting simple webhook test...")
    
    # Get configuration
    config = get_config()
    print(f"✅ Configuration loaded - OpenAI model: {config.openai_model}")
    
    # Create a simple webhook request
    test_request = TwilioWebhookRequest(
        MessageSid="SMtest123456789012345678901234",
        From="whatsapp:+1234567890",
        To="whatsapp:+14155238886",
        Body="This is a test job posting for a software engineer position",
        NumMedia=0,
        MediaUrl0=None,
        MediaContentType0=None
    )
    
    print(f"📝 Test request created - Body: '{test_request.Body}'")
    
    # Initialize message handler
    message_handler = MessageHandlerService(config)
    print("✅ Message handler initialized")
    
    # Process the message
    print("🔄 Processing message...")
    success = await message_handler.process_message(test_request)
    
    if success:
        print("✅ SUCCESS: Message processed successfully!")
        print("🎉 OpenAI analysis should have been triggered")
    else:
        print("❌ FAILED: Message processing failed")
        return False
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_webhook_simple()
        if success:
            print("\n🎯 WEBHOOK TEST PASSED")
            return 0
        else:
            print("\n💥 WEBHOOK TEST FAILED")
            return 1
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)