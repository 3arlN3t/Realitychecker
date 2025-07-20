#!/usr/bin/env python3
"""
Debug script to test phone number validation.
"""

from app.utils.security import SecurityValidator

def test_phone_validation():
    """Test phone number validation with different formats."""
    
    validator = SecurityValidator()
    
    test_numbers = [
        "whatsapp:+15551234567",
        "whatsapp:+1234567890",
        "whatsapp:+14155238886",
        "+15551234567",
        "15551234567",
        "whatsapp:+1-555-123-4567",
    ]
    
    print("🔍 Testing Phone Number Validation")
    print("=" * 50)
    
    for number in test_numbers:
        is_valid, error = validator.validate_phone_number(number)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{status}: {number}")
        if error:
            print(f"   Error: {error}")
        print()

if __name__ == "__main__":
    test_phone_validation()