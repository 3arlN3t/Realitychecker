import pytest

pytest.mark.skip(reason="This is a development script, not a pytest test file.")

#!/usr/bin/env python3
"""
Development testing script for Reality Checker WhatsApp Bot.
Run this script while your development server is running to test all endpoints.
"""

import requests
import json
import time
from urllib.parse import urlencode

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Status: {data['status']}")
            print("Service Status:")
            for service, status in data['services'].items():
                emoji = "✅" if status in ['connected', 'ready'] else "⚠️"
                print(f"  {emoji} {service}: {status}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook_get():
    """Test the webhook GET endpoint."""
    print("\n📞 Testing Webhook GET Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/webhook/whatsapp", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook Status: {data['status']}")
            print(f"✅ Message: {data['message']}")
            return True
        else:
            print(f"❌ Webhook GET failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook GET error: {e}")
        return False

def test_webhook_post(test_name, body_data):
    """Test the webhook POST endpoint with given data."""
    print(f"\n📨 Testing: {test_name}")
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            f"{BASE_URL}/webhook/whatsapp", 
            data=urlencode(body_data),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ {test_name}: Success (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️ {test_name}: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ {test_name} error: {e}")
        return False

def main():
    """Run all development tests."""
    print("🚀 Reality Checker WhatsApp Bot - Development Testing")
    print("=" * 60)
    
    # Check if server is running
    print("🔍 Checking if development server is running...")
    try:
        requests.get(BASE_URL, timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server is not running!")
        print("Please start the server with:")
        print("python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print("\n" + "=" * 60)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    # Test webhook GET
    webhook_get_ok = test_webhook_get()
    
    # Test webhook POST with different scenarios
    test_cases = [
        ("Help Request", {
            'MessageSid': 'SM1234567890abcdef1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+17087405918',
            'Body': 'help',
            'NumMedia': '0'
        }),
        
        ("Legitimate Job", {
            'MessageSid': 'SM2234567890abcdef1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+17087405918',
            'Body': 'Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience, Bachelor\'s degree in Computer Science. Contact: hr@google.com for application details.',
            'NumMedia': '0'
        }),
        
        ("Suspicious Job", {
            'MessageSid': 'SM3234567890abcdef1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+17087405918',
            'Body': 'URGENT! Make $5000/week working from home! No experience needed! Just send $99 registration fee to get started immediately!',
            'NumMedia': '0'
        }),
        
        ("Likely Scam", {
            'MessageSid': 'SM4234567890abcdef1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+17087405918',
            'Body': 'Congratulations! You\'ve been selected for a $10,000/month data entry job! Send your SSN, bank details, and $200 processing fee to secure your position today!',
            'NumMedia': '0'
        }),
        
        ("Short Invalid Message", {
            'MessageSid': 'SM5234567890abcdef1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+17087405918',
            'Body': 'hi',
            'NumMedia': '0'
        })
    ]
    
    webhook_post_results = []
    for test_name, test_data in test_cases:
        result = test_webhook_post(test_name, test_data)
        webhook_post_results.append(result)
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 2 + len(test_cases)  # health + webhook_get + webhook_posts
    passed_tests = sum([health_ok, webhook_get_ok] + webhook_post_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your application is working perfectly!")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check the logs above for details.")
    
    print("\n📍 Available Endpoints:")
    print(f"  - Health: {BASE_URL}/health")
    print(f"  - API Docs: {BASE_URL}/docs")
    print(f"  - Webhook: {BASE_URL}/webhook/whatsapp")

if __name__ == "__main__":
    main()