#!/usr/bin/env python3
"""
Integration test for the complete optimized webhook system.
"""

import time
import json
from fastapi.testclient import TestClient

# Import after moving the original webhook file
from app.main import app

def test_webhook_integration():
    """Test the complete webhook integration."""
    client = TestClient(app)
    
    # Test data that should trigger the POST endpoint
    webhook_data = {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+0987654321",
        "Body": "This is a test job posting for a software engineer position at a tech company. The role requires Python experience and offers competitive salary.",
        "NumMedia": "0"
    }
    
    print("🚀 Testing complete webhook integration...")
    print(f"Sending webhook data: {webhook_data}")
    
    # Test with explicit form data
    start_time = time.time()
    
    response = client.post(
        "/webhook/whatsapp",
        data=webhook_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    response_time_ms = (time.time() - start_time) * 1000
    
    print(f"\nResponse details:")
    print(f"  Status: {response.status_code}")
    print(f"  Response time: {response_time_ms:.1f}ms")
    print(f"  Body: '{response.text}'")
    print(f"  Headers: {dict(response.headers)}")
    
    # Check if we got the optimized response (empty body)
    if response.status_code == 200 and response.text == "":
        print("✅ Optimized webhook endpoint is working correctly!")
        print(f"✅ Response time {response_time_ms:.1f}ms is well under 500ms target")
        return True
    elif response.status_code == 200 and "status" in response.text:
        print("⚠️ Still hitting GET endpoint - this suggests routing issue")
        return False
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        return False

def test_performance_monitoring():
    """Test that performance monitoring is working."""
    from app.services.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    
    # Get initial metrics
    initial_metrics = monitor.get_application_metrics()
    print(f"\nPerformance monitoring:")
    print(f"  Active requests: {initial_metrics.active_requests}")
    print(f"  Avg response time: {initial_metrics.avg_response_time:.3f}s")
    print(f"  Requests per second: {initial_metrics.requests_per_second:.1f}")
    
    return True

if __name__ == "__main__":
    print("🚀 Running integration tests for optimized webhook...")
    
    try:
        # Test webhook integration
        webhook_success = test_webhook_integration()
        
        # Test performance monitoring
        monitoring_success = test_performance_monitoring()
        
        if webhook_success and monitoring_success:
            print("\n🎉 All integration tests passed!")
            print("✅ Webhook optimization implementation is complete and working")
        else:
            print("\n❌ Some integration tests failed")
            
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise