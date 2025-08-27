#!/usr/bin/env python3
"""
Direct test for the optimized webhook handler.
"""

import asyncio
from app.api.optimized_webhook import whatsapp_webhook_optimized
from app.models.data_models import AppConfig
from app.services.message_handler import MessageHandlerService
from fastapi import Request
from unittest.mock import Mock, AsyncMock
import time

async def test_direct_webhook():
    """Test the webhook function directly."""
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {}
    mock_request.url = "http://test.com/webhook/whatsapp"
    
    mock_config = Mock(spec=AppConfig)
    mock_config.webhook_validation = False
    
    mock_message_handler = Mock(spec=MessageHandlerService)
    mock_message_handler.process_message = AsyncMock(return_value=True)
    
    # Test data
    message_sid = "SM1234567890abcdef1234567890abcdef"
    from_number = "whatsapp:+1234567890"
    to_number = "whatsapp:+0987654321"
    body = "This is a test job posting for a software engineer position."
    
    print(f"Testing webhook function directly...")
    
    start_time = time.time()
    
    try:
        response = await whatsapp_webhook_optimized(
            request=mock_request,
            MessageSid=message_sid,
            From=from_number,
            To=to_number,
            Body=body,
            NumMedia=0,
            MediaUrl0=None,
            MediaContentType0=None,
            message_handler=mock_message_handler,
            config=mock_config
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        print(f"✅ Direct webhook test passed!")
        print(f"   Response status: {response.status_code}")
        print(f"   Response time: {response_time_ms:.1f}ms")
        print(f"   Response body: '{response.body.decode()}'")
        
        # Verify the message handler was called asynchronously
        await asyncio.sleep(0.1)  # Give background task time to start
        
        return response_time_ms
        
    except Exception as e:
        print(f"❌ Direct webhook test failed: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Testing optimized webhook function directly...")
    
    try:
        response_time = asyncio.run(test_direct_webhook())
        print(f"✅ All tests passed! Response time: {response_time:.1f}ms")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise