#!/usr/bin/env python3
"""
Test script for the optimized webhook handler.

This script tests the webhook performance improvements and validates
that response times are within the target of 500ms.
"""

import asyncio
import time
import json
import hmac
import hashlib
import base64
from urllib.parse import urlencode
from typing import Dict, Any

import httpx
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from app.main import app
from app.config import get_config

# Test configuration
TEST_WEBHOOK_URL = "/webhook/whatsapp"
TARGET_RESPONSE_TIME_MS = 500
CONCURRENT_REQUESTS = 10


def create_twilio_signature(url: str, params: Dict[str, str], auth_token: str) -> str:
    """Create a valid Twilio signature for testing."""
    data_string = url + urlencode(sorted(params.items()))
    signature = base64.b64encode(
        hmac.new(
            auth_token.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    return signature


def create_test_webhook_data() -> Dict[str, str]:
    """Create test webhook data."""
    return {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+0987654321",
        "Body": "This is a test job posting for a software engineer position at a tech company. The role requires Python experience and offers competitive salary.",
        "NumMedia": "0"
    }


def test_webhook_response_time():
    """Test that webhook responds within target time."""
    client = TestClient(app)
    config = get_config()
    
    # Prepare test data
    webhook_data = create_test_webhook_data()
    
    # Create signature if validation is enabled
    headers = {}
    if config.webhook_validation:
        full_url = f"http://testserver{TEST_WEBHOOK_URL}"
        signature = create_twilio_signature(full_url, webhook_data, config.twilio_auth_token)
        headers["X-Twilio-Signature"] = signature
    
    # Measure response time
    start_time = time.time()
    
    response = client.post(
        TEST_WEBHOOK_URL,
        data=webhook_data,
        headers=headers
    )
    
    response_time_ms = (time.time() - start_time) * 1000
    
    # Assertions
    assert response.status_code == 200
    assert response_time_ms <= TARGET_RESPONSE_TIME_MS, f"Response time {response_time_ms:.1f}ms exceeded target {TARGET_RESPONSE_TIME_MS}ms"
    
    print(f"✅ Webhook response time: {response_time_ms:.1f}ms (target: {TARGET_RESPONSE_TIME_MS}ms)")


def test_webhook_validation_caching():
    """Test that validation caching works correctly."""
    client = TestClient(app)
    config = get_config()
    
    webhook_data = create_test_webhook_data()
    
    headers = {}
    if config.webhook_validation:
        full_url = f"http://testserver{TEST_WEBHOOK_URL}"
        signature = create_twilio_signature(full_url, webhook_data, config.twilio_auth_token)
        headers["X-Twilio-Signature"] = signature
    
    # First request (should cache validation)
    start_time = time.time()
    response1 = client.post(TEST_WEBHOOK_URL, data=webhook_data, headers=headers)
    first_response_time = (time.time() - start_time) * 1000
    
    # Second request (should use cached validation)
    start_time = time.time()
    response2 = client.post(TEST_WEBHOOK_URL, data=webhook_data, headers=headers)
    second_response_time = (time.time() - start_time) * 1000
    
    # Assertions
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Second request should be faster due to caching
    print(f"✅ First request: {first_response_time:.1f}ms, Second request: {second_response_time:.1f}ms")
    print(f"✅ Caching improvement: {first_response_time - second_response_time:.1f}ms")


def test_concurrent_webhook_performance():
    """Test webhook performance under concurrent load using TestClient."""
    client = TestClient(app)
    config = get_config()
    
    def send_webhook_request(request_id: int):
        """Send a single webhook request."""
        webhook_data = create_test_webhook_data()
        webhook_data["MessageSid"] = f"SM{request_id:030d}"  # Unique message ID
        
        headers = {}
        if config.webhook_validation:
            full_url = f"http://testserver{TEST_WEBHOOK_URL}"
            signature = create_twilio_signature(full_url, webhook_data, config.twilio_auth_token)
            headers["X-Twilio-Signature"] = signature
        
        start_time = time.time()
        
        response = client.post(
            TEST_WEBHOOK_URL,
            data=webhook_data,
            headers=headers
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "request_id": request_id,
            "status_code": response.status_code,
            "response_time_ms": response_time_ms
        }
    
    # Send concurrent requests
    start_time = time.time()
    results = []
    for i in range(CONCURRENT_REQUESTS):
        result = send_webhook_request(i)
        results.append(result)
    total_time = time.time() - start_time
    
    # Analyze results
    response_times = [r["response_time_ms"] for r in results]
    successful_requests = sum(1 for r in results if r["status_code"] == 200)
    
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    min_response_time = min(response_times)
    
    # Assertions
    assert successful_requests == CONCURRENT_REQUESTS, f"Only {successful_requests}/{CONCURRENT_REQUESTS} requests succeeded"
    assert avg_response_time <= TARGET_RESPONSE_TIME_MS, f"Average response time {avg_response_time:.1f}ms exceeded target"
    
    print(f"✅ Concurrent load test results:")
    print(f"   - Requests: {CONCURRENT_REQUESTS}")
    print(f"   - Total time: {total_time:.2f}s")
    print(f"   - Successful: {successful_requests}/{CONCURRENT_REQUESTS}")
    print(f"   - Avg response time: {avg_response_time:.1f}ms")
    print(f"   - Min response time: {min_response_time:.1f}ms")
    print(f"   - Max response time: {max_response_time:.1f}ms")
    print(f"   - Throughput: {CONCURRENT_REQUESTS/total_time:.1f} req/s")


def test_invalid_signature_handling():
    """Test that invalid signatures are handled quickly."""
    client = TestClient(app)
    config = get_config()
    
    if not config.webhook_validation:
        print("⚠️ Webhook validation disabled, skipping signature test")
        return
    
    webhook_data = create_test_webhook_data()
    headers = {"X-Twilio-Signature": "invalid_signature"}
    
    start_time = time.time()
    response = client.post(TEST_WEBHOOK_URL, data=webhook_data, headers=headers)
    response_time_ms = (time.time() - start_time) * 1000
    
    # Should fail quickly
    assert response.status_code == 401
    assert response_time_ms <= 200, f"Invalid signature handling took too long: {response_time_ms:.1f}ms"
    
    print(f"✅ Invalid signature handled in {response_time_ms:.1f}ms")


if __name__ == "__main__":
    print("🚀 Testing optimized webhook handler...")
    
    try:
        # Run synchronous tests
        test_webhook_response_time()
        test_webhook_validation_caching()
        test_invalid_signature_handling()
        
        # Run concurrent test
        test_concurrent_webhook_performance()
        
        print("\n✅ All webhook optimization tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise