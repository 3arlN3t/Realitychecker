#!/usr/bin/env python3
"""
Simple test for the optimized webhook handler.
"""

import time
from fastapi.testclient import TestClient
from app.main import app

def test_basic_webhook():
    """Test basic webhook functionality."""
    client = TestClient(app)
    
    webhook_data = {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+0987654321",
        "Body": "This is a test job posting for a software engineer position at a tech company. The role requires Python experience and offers competitive salary.",
        "NumMedia": "0"
    }
    
    print(f"Sending POST request to /webhook/whatsapp with data: {webhook_data}")
    
    start_time = time.time()
    response = client.post("/webhook/whatsapp", data=webhook_data)
    response_time_ms = (time.time() - start_time) * 1000
    
    print(f"Response status: {response.status_code}")
    print(f"Response time: {response_time_ms:.1f}ms")
    print(f"Response body: '{response.text}'")
    print(f"Response headers: {dict(response.headers)}")
    
    # Check if it's the optimized endpoint by looking for empty response
    if response.status_code == 200 and response.text == "":
        print("✅ Optimized webhook endpoint is working!")
    elif response.status_code == 200 and "status" in response.text:
        print("⚠️ Hitting GET endpoint instead of POST")
        # Try with explicit content-type
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        start_time = time.time()
        response = client.post("/webhook/whatsapp", data=webhook_data, headers=headers)
        response_time_ms = (time.time() - start_time) * 1000
        print(f"Retry - Response status: {response.status_code}")
        print(f"Retry - Response time: {response_time_ms:.1f}ms")
        print(f"Retry - Response body: '{response.text}'")
    
    assert response.status_code == 200
    assert response_time_ms < 1000  # Should be under 1 second
    
    return response_time_ms

if __name__ == "__main__":
    print("🚀 Testing basic webhook functionality...")
    
    try:
        response_time = test_basic_webhook()
        print(f"✅ Webhook test passed! Response time: {response_time:.1f}ms")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise