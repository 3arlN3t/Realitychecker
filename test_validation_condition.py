#!/usr/bin/env python3
"""
Test the validation condition logic used in the webhook endpoint.

This script validates the specific text length validation logic:
sanitized_body and text_length < MIN_TEXT_LENGTH

The condition fails (raises 400 error) when:
- sanitized_body is truthy (not empty after sanitization)
- AND text_length < MIN_TEXT_LENGTH (20 characters)
"""

import sys
sys.path.append('.')

from app.utils.security import SecurityValidator
from app.api.webhook import MIN_TEXT_LENGTH  # Import the actual constant

def test_validation_conditions():
    """Test the exact validation conditions used in the webhook."""
    
    test_cases = [
        # Edge cases for validation logic
        ("", "empty string"),
        ("   ", "whitespace only"),
        ("test", "short text (4 chars)"),
        ("a" * 19, "exactly 19 characters"),
        ("a" * 20, "exactly 20 characters"),
        ("a" * 21, "exactly 21 characters"),
        ("Software Engineer position", "valid text (26 chars)"),
        ("  valid text with spaces  ", "text with leading/trailing spaces"),
        
        # Security test cases
        ("<script>alert('xss')</script>", "HTML content"),
        ("javascript:alert('xss')", "javascript injection"),
        ("' OR 1=1 --", "SQL injection attempt"),
        (None, "None value"),
    ]
    
    security_validator = SecurityValidator()
    
    print(f"MIN_TEXT_LENGTH = {MIN_TEXT_LENGTH}")
    print("=" * 60)
    
    for body, description in test_cases:
        print(f"\n🔍 Testing: {description}")
        print(f"  Original Body: {repr(body)}")
        
        # Handle None case
        if body is None:
            sanitized_body = ""
            text_length = 0
        else:
            # Simulate the webhook logic exactly
            sanitized_body = security_validator.sanitize_text(body) if body else ""
            text_length = len(sanitized_body.strip()) if sanitized_body else 0
        
        print(f"  Sanitized Body: {repr(sanitized_body)}")
        print(f"  Text Length: {text_length}")
        print(f"  sanitized_body truthy: {bool(sanitized_body)}")
        print(f"  text_length < MIN_TEXT_LENGTH: {text_length < MIN_TEXT_LENGTH}")
        
        # The actual condition from webhook
        should_fail = sanitized_body and text_length < MIN_TEXT_LENGTH
        print(f"  Should fail validation: {should_fail}")
        
        if should_fail:
            print(f"  ❌ Would raise 400 error: 'Message too short'")
        else:
            print(f"  ✅ Would pass validation")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("- Empty/None messages: PASS (allowed)")
    print("- Whitespace-only messages: PASS (sanitized to empty)")
    print("- Messages 1-19 chars after sanitization: FAIL (too short)")
    print("- Messages 20+ chars after sanitization: PASS (valid length)")

if __name__ == "__main__":
    test_validation_conditions()