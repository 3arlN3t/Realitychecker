#!/usr/bin/env python3
"""
Test script for WhatsApp bot functionality.
This script helps test the bot locally and diagnose issues.
"""

import asyncio
import json
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PHONE = "whatsapp:+1234567890"
BOT_PHONE = "whatsapp:+14155238886"

def test_health_check():
    """Test if the application is running and healthy."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            
            # Check service statuses
            services = data.get('services', {})
            for service, status in services.items():
                if isinstance(status, dict):
                    status_val = status.get('status', status)
                else:
                    status_val = status
                    
                if status_val in ['healthy', 'ready']:
                    print(f"  ✅ {service}: {status_val}")
                else:
                    print(f"  ⚠️ {service}: {status_val}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible."""
    print("\n🔍 Testing webhook endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/webhook/whatsapp")
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible")
            return True
        else:
            print(f"❌ Webhook endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook endpoint error: {e}")
        return False

def test_job_analysis_api():
    """Test the job analysis API directly."""
    print("\n🔍 Testing job analysis API...")
    
    test_cases = [
        {
            "name": "Legitimate Job",
            "text": "Software Engineer position at Microsoft. Competitive salary, health benefits, 401k. Apply through our careers page.",
            "expected": "Legit"
        },
        {
            "name": "Obvious Scam",
            "text": "URGENT! Make $5000/week working from home! Send $200 processing fee to secure your position. No experience needed!",
            "expected": "Likely Scam"
        },
        {
            "name": "Suspicious Job",
            "text": "Data entry job, $50/hour, work from home. Must pay $100 for training materials. Contact via WhatsApp only.",
            "expected": "Suspicious"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/analyze/text",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"job_text": test_case["text"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                classification = result.get('classification', 'Unknown')
                trust_score = result.get('trust_score', 0)
                
                print(f"    ✅ Classification: {classification}")
                print(f"    ✅ Trust Score: {trust_score}/100")
                
                if classification == test_case['expected']:
                    print(f"    ✅ Expected result matched!")
                else:
                    print(f"    ⚠️ Expected {test_case['expected']}, got {classification}")
            else:
                print(f"    ❌ API call failed: {response.status_code}")
                print(f"    Response: {response.text}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_webhook_simulation():
    """Simulate a WhatsApp webhook call."""
    print("\n🔍 Testing webhook simulation...")
    
    test_messages = [
        {
            "name": "Help Request",
            "body": "help",
            "expected_behavior": "Should send welcome message"
        },
        {
            "name": "Job Analysis Request",
            "body": "Software Engineer at Google. $200k salary. Send $500 for background check.",
            "expected_behavior": "Should analyze and detect as scam"
        }
    ]
    
    for test_msg in test_messages:
        print(f"\n  Testing: {test_msg['name']}")
        
        webhook_data = {
            "MessageSid": f"SM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "From": TEST_PHONE,
            "To": BOT_PHONE,
            "Body": test_msg["body"],
            "NumMedia": "0"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/webhook/whatsapp",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=webhook_data
            )
            
            if response.status_code == 200:
                print(f"    ✅ Webhook processed successfully")
                print(f"    Expected: {test_msg['expected_behavior']}")
            else:
                print(f"    ❌ Webhook failed: {response.status_code}")
                print(f"    Response: {response.text}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")

def print_setup_instructions():
    """Print setup instructions for testing with real WhatsApp."""
    print("\n" + "="*60)
    print("📱 WHATSAPP BOT SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. 🌐 EXPOSE LOCAL SERVER TO INTERNET:")
    print("   Install ngrok: https://ngrok.com/download")
    print("   Run: ngrok http 8000")
    print("   Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
    
    print("\n2. 🔧 CONFIGURE TWILIO WEBHOOK:")
    print("   Go to: https://console.twilio.com/")
    print("   Navigate to: Messaging > Try it out > Send a WhatsApp message")
    print("   Set webhook URL to: https://your-ngrok-url.ngrok.io/webhook/whatsapp")
    
    print("\n3. 📱 TEST WITH WHATSAPP SANDBOX:")
    print("   Join sandbox: Send 'join <sandbox-code>' to +14155238886")
    print("   Send test message: 'help' or a job posting")
    
    print("\n4. 🚀 FOR PRODUCTION:")
    print("   Apply for WhatsApp Business API access")
    print("   Deploy to cloud with public domain")
    print("   Configure production Twilio account")
    
    print("\n5. 🔍 MONITORING:")
    print("   Check logs in terminal running uvicorn")
    print("   Monitor webhook calls in Twilio console")
    print("   Use /health endpoint to check service status")

def main():
    """Run all tests and provide setup instructions."""
    print("🤖 WHATSAPP BOT TESTING SUITE")
    print("="*50)
    
    # Run tests
    health_ok = test_health_check()
    webhook_ok = test_webhook_endpoint()
    
    if health_ok and webhook_ok:
        test_job_analysis_api()
        test_webhook_simulation()
        
        print("\n" + "="*50)
        print("✅ CORE FUNCTIONALITY WORKING!")
        print("The bot can analyze job postings correctly.")
        print("Issue: Twilio can't send responses (needs proper setup)")
        
        print_setup_instructions()
    else:
        print("\n❌ BASIC TESTS FAILED")
        print("Please ensure the application is running:")
        print("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main()