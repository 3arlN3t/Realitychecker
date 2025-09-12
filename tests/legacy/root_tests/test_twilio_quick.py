#!/usr/bin/env python3
"""
Quick Twilio connection test.
"""
import asyncio
from app.config import get_config
from app.services.twilio_response import TwilioResponseService

async def test_twilio():
    """Test Twilio service configuration and connectivity."""
    print("🔧 Testing Twilio configuration...")
    
    config = get_config()
    print(f"Account SID: {config.twilio_account_sid}")
    print(f"Phone Number: {config.twilio_phone_number}")
    print(f"Auth Token: {'*' * len(config.twilio_auth_token) if config.twilio_auth_token else 'NOT SET'}")
    
    # Initialize Twilio service
    twilio_service = TwilioResponseService(config)
    print("✅ Twilio service initialized")
    
    # Test health check
    is_healthy = await twilio_service.health_check()
    if is_healthy:
        print("✅ Twilio health check passed")
    else:
        print("❌ Twilio health check failed")
        return False
    
    # Test sending a simple message 
    print("📱 Testing message send...")
    try:
        # Use a fake job analysis result for testing
        from app.models.data_models import JobAnalysisResult, JobClassification
        test_result = JobAnalysisResult(
            trust_score=8,
            classification=JobClassification.LEGIT,
            reasons=[
                "Clear job description provided",
                "Company information is verifiable", 
                "Professional contact details included"
            ],
            confidence=0.8
        )
        
        print(f"Test result type: {type(test_result)}")
        print(f"Classification: {test_result.classification}")
        print(f"Classification text: {test_result.classification_text}")
        
        success = await twilio_service.send_analysis_result(
            "whatsapp:+1234567890",  # Test number
            test_result
        )
        
        if success:
            print("✅ Message sent successfully!")
            return True
        else:
            print("❌ Failed to send message")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_twilio())
    if success:
        print("\n🎯 TWILIO TEST PASSED")
    else:
        print("\n💥 TWILIO TEST FAILED")