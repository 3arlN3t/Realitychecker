#!/usr/bin/env python3
"""
Test script to verify webhook functionality.
"""

import requests
import json

def test_webhook():
    """Test the webhook endpoint with sample data."""
    
    webhook_url = "http://localhost:8000/webhook/whatsapp"
    
    # Test data that should work
    test_data = {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+14155238886",
        "Body": "This is a test job posting with enough content to pass validation checks and trigger analysis.",
        "NumMedia": "0"
    }
    
    print("Testing webhook endpoint...")
    print(f"URL: {webhook_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url,
            data=test_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test PASSED")
        else:
            print("❌ Webhook test FAILED")
            
    except requests.exceptions.Timeout:
        print("❌ Webhook test TIMED OUT (>30 seconds)")
    except Exception as e:
        print(f"❌ Webhook test ERROR: {e}")

if __name__ == "__main__":
    test_webhook()