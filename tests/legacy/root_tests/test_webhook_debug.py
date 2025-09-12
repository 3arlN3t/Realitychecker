#!/usr/bin/env python3
"""
Debug script to test WhatsApp webhook processing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.models.data_models import TwilioWebhookRequest
from app.services.message_handler import MessageHandlerService
from app.dependencies import initialize_service_container

async def test_webhook_processing():
    """Test webhook processing with debug output"""
    print("🔍 Testing WhatsApp webhook processing...")
    
    try:
        # Initialize config and service container
        print("📋 Initializing configuration...")
        config = get_config()
        print(f"✅ Config loaded - OpenAI: {'✓' if config.openai_api_key else '✗'}, Twilio: {'✓' if config.twilio_auth_token else '✗'}")
        
        # Initialize services
        print("🏗️ Initializing service container...")
        service_container = initialize_service_container()
        print("✅ Service container initialized")
        
        # Get message handler
        print("🔧 Getting message handler...")
        message_handler = service_container.get_message_handler()
        print("✅ Message handler ready")
        
        # Create test webhook request
        print("📝 Creating test webhook request...")
        test_request = TwilioWebhookRequest(
            MessageSid="SM123456789TESTMESSAGE",
            From="whatsapp:+1234567890",
            To="whatsapp:+14155238886",
            Body="This is a test job posting: Work from home, make $5000 per week, no experience needed! Contact us now!",
            NumMedia=0
        )
        print(f"✅ Test request created - Body: {test_request.Body[:50]}...")
        
        # Process the message with timeout
        print("⚡ Processing message (with 30s timeout)...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await asyncio.wait_for(
                message_handler.process_message(test_request),
                timeout=30.0
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            print(f"✅ Message processed successfully in {processing_time:.2f}s - Result: {result}")
            
        except asyncio.TimeoutError:
            print("❌ Message processing timed out after 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Error during message processing: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return result
        
    except Exception as e:
        print(f"❌ Error in test setup: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting WhatsApp Analysis Debug Test\n")
    
    result = await test_webhook_processing()
    
    if result:
        print("\n✅ WhatsApp analysis is working correctly!")
    else:
        print("\n❌ WhatsApp analysis has issues that need to be fixed!")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())