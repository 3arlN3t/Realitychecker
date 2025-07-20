#!/usr/bin/env python3
"""
Debug actual phone number formats from WhatsApp.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.utils.security import SecurityValidator

def test_phone_formats():
    """Test various phone number formats that might come from WhatsApp."""
    print("🔍 Testing Real Phone Number Formats")
    print("=" * 50)
    
    validator = SecurityValidator()
    
    # Various possible formats from WhatsApp
    test_numbers = [
        "whatsapp:+17087405918",      # Expected format
        "whatsapp:+1 708 740 5918",   # With spaces
        "whatsapp:+1-708-740-5918",   # With hyphens
        "whatsapp:+1(708)740-5918",   # With parentheses
        "+17087405918",               # Without whatsapp: prefix
        "17087405918",                # No + or whatsapp:
        "whatsapp:17087405918",       # Missing +
        "whatsapp:+170-87-40-59-18",  # International format
    ]
    
    for number in test_numbers:
        is_valid, error = validator.validate_phone_number(number)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{status}: '{number}'")
        if error:
            print(f"   Error: {error}")
        print()

if __name__ == "__main__":
    test_phone_formats()