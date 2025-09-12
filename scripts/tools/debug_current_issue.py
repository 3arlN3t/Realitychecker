#!/usr/bin/env python3
"""
Debug the current 400 error issue.

Usage:
    python debug_current_issue.py

This script tests:
- Server health endpoint responsiveness  
- Webhook timing with short text (should trigger early validation)
- Response analysis for performance debugging

Requirements:
    pip install requests

Expected behavior:
- Health check should respond quickly
- Short text webhook should fail fast (<1s) if early validation works
"""

import sys
import time

try:
    import requests
except ImportError:
    print("❌ requests library not found. Install with: pip install requests")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"
WEBHOOK_TIMEOUT = 20
HEALTH_TIMEOUT = 5

def test_webhook_with_timing():
    """Test webhook with detailed timing."""
    print("🔍 Testing current webhook behavior...")
    
    # Test with short text that should trigger early validation
    data = {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+14155238886",
        "Body": "test",  # 4 characters - should fail early validation
        "NumMedia": "0"
    }
    
    print(f"📝 Sending: {data}")
    
    start_time = time.perf_counter()
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/whatsapp",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=WEBHOOK_TIMEOUT
        )
        
        duration = time.perf_counter() - start_time
        print(f"✅ Response received in {duration:.2f}s")
        print(f"📊 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if duration < 1.0:
            print("✅ Fast response - early validation working!")
        elif duration > 10.0:
            print("❌ Slow response - early validation NOT working")
        else:
            print("⚠️  Medium response - partial improvement")
            
    except requests.exceptions.Timeout:
        duration = time.perf_counter() - start_time
        print(f"❌ Request timed out after {duration:.2f}s")
    except Exception as e:
        duration = time.perf_counter() - start_time
        print(f"❌ Error after {duration:.2f}s: {e}")

def test_server_health():
    """Test if server is responding normally."""
    print("\n🔍 Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=HEALTH_TIMEOUT)
        print(f"✅ Health check: {response.status_code}")
        print(f"📝 Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    test_server_health()
    test_webhook_with_timing()