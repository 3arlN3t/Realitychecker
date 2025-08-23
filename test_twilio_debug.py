#!/usr/bin/env python3
"""
Debug script to test Twilio WhatsApp messaging
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.models.data_models import JobAnalysisResult, JobClassification
from app.services.twilio_response import TwilioResponseService

def test_twilio_service():
    """Test Twilio service with debug output"""
    print("🔍 Testing Twilio WhatsApp messaging...")
    
    try:
        # Initialize config and service
        print("📋 Initializing Twilio service...")
        config = get_config()
        twilio_service = TwilioResponseService(config)
        
        print(f"✅ Twilio service initialized:")
        print(f"   Account SID: {config.twilio_account_sid}")
        print(f"   Phone Number: {config.twilio_phone_number}")
        print(f"   Auth Token: {'✓ Set' if config.twilio_auth_token else '✗ Missing'}")
        
        # Create test analysis result
        print("\n📝 Creating test analysis result...")
        test_result = JobAnalysisResult(
            trust_score=25,
            classification=JobClassification.LIKELY_SCAM,
            reasons=["Unrealistic salary promises", "Upfront payment required", "Too good to be true claims"],
            confidence=0.85
        )
        print(f"✅ Test result created - Trust Score: {test_result.trust_score}")
        
        # Test sending to a test number (this will fail in sandbox, but we can see the error)
        print("\n⚡ Testing message send...")
        test_number = "whatsapp:+1234567890"
        
        try:
            success = twilio_service.send_analysis_result(test_number, test_result)
            
            if success:
                print("✅ Message sent successfully!")
            else:
                print("❌ Message sending failed (check logs for details)")
                
        except Exception as e:
            print(f"❌ Exception during message send: {e}")
            import traceback
            traceback.print_exc()
        
        # Test error message sending
        print("\n⚡ Testing error message send...")
        try:
            success = twilio_service.send_error_message(test_number, "general")
            
            if success:
                print("✅ Error message sent successfully!")
            else:
                print("❌ Error message sending failed")
                
        except Exception as e:
            print(f"❌ Exception during error message send: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in Twilio test setup: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Starting Twilio WhatsApp Debug Test\n")
    
    result = test_twilio_service()
    
    if result:
        print("\n✅ Twilio test completed - check output for details!")
    else:
        print("\n❌ Twilio test failed!")
    
    return result

if __name__ == "__main__":
    main()