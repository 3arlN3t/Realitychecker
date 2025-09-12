#!/usr/bin/env python3
"""
Debug script to test webhook validation with sample data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.security import validate_webhook_request

def test_webhook_validation():
    """
    Test webhook validation with various sample inputs.
    
    Tests different scenarios including:
    - Standard Twilio message SID formats
    - Different phone number formats (with/without + prefix)
    - Messages with and without media
    - Various SID formats (SM, MM, test SIDs)
    """
    
    # Test cases with different formats
    test_cases = [
        {
            "name": "Standard Twilio format",
            "message_sid": "SM1234567890abcdef1234567890abcdef",
            "from_number": "whatsapp:+1234567890",
            "to_number": "whatsapp:+0987654321",
            "body": "This is a test job posting with enough content to pass validation checks.",
            "media_url": None
        },
        {
            "name": "With media",
            "message_sid": "SM1234567890abcdef1234567890abcdef",
            "from_number": "whatsapp:+1234567890",
            "to_number": "whatsapp:+0987654321",
            "body": "",
            "media_url": "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
        },
        {
            "name": "Different SID format",
            "message_sid": "MM1234567890abcdef1234567890abcdef",
            "from_number": "whatsapp:+1234567890",
            "to_number": "whatsapp:+0987654321",
            "body": "Another test job posting with sufficient content for analysis.",
            "media_url": None
        },
        {
            "name": "Test SID",
            "message_sid": "test_message_12345",
            "from_number": "whatsapp:+1234567890",
            "to_number": "whatsapp:+0987654321",
            "body": "Test job posting content for development testing purposes.",
            "media_url": None
        },
        {
            "name": "Phone without plus",
            "message_sid": "SM1234567890abcdef1234567890abcdef",
            "from_number": "whatsapp:1234567890",
            "to_number": "whatsapp:0987654321",
            "body": "Job posting content without plus sign in phone numbers.",
            "media_url": None
        }
    ]
    
    print("Testing webhook validation...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print("-" * 30)
        
        is_valid, error_message = validate_webhook_request(
            test_case["message_sid"],
            test_case["from_number"],
            test_case["to_number"],
            test_case["body"],
            test_case["media_url"]
        )
        
        try:
            if is_valid:
                print("✅ VALID")
            else:
                print(f"❌ INVALID: {error_message}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
        
        print(f"   MessageSid: {test_case['message_sid']}")
        print(f"   From: {test_case['from_number']}")
        print(f"   To: {test_case['to_number']}")
        print(f"   Body length: {len(test_case['body']) if test_case['body'] else 0}")
        print(f"   Media URL: {test_case['media_url'] is not None}")

if __name__ == "__main__":
    test_webhook_validation()