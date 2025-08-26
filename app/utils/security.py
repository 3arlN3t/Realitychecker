"""Security utilities for input sanitization and validation."""

import re
import bleach
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = []  # No HTML tags allowed in our use case
ALLOWED_ATTRIBUTES = {}
ALLOWED_PROTOCOLS = ['http', 'https']

# Content validation patterns
SUSPICIOUS_PATTERNS = [
    # Script injection attempts
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',
    r'onload\s*=',
    r'onerror\s*=',
    r'onclick\s*=',
    
    # SQL injection patterns
    r'union\s+select',
    r'drop\s+table',
    r'delete\s+from',
    r'insert\s+into',
    r'update\s+.*\s+set',
    
    # Command injection patterns
    r';\s*rm\s+',
    r';\s*cat\s+',
    r';\s*ls\s+',
    r'&&\s*rm\s+',
    r'\|\s*rm\s+',
    
    # Path traversal
    r'\.\./',
    r'\.\.\\',
    
    # Suspicious URLs
    r'data:text/html',
    r'data:application/javascript',
]

# Compile patterns for better performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]

# Maximum content lengths
MAX_TEXT_LENGTH = 50000  # 50KB for job ad text
MAX_URL_LENGTH = 2048    # Standard URL length limit
MAX_PHONE_LENGTH = 30    # International phone number format (increased for whatsapp: prefix)


class SecurityValidator:
    """Security validation and sanitization utilities."""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text input by removing HTML tags and suspicious content.
        
        Args:
            text: Raw text input to sanitize
            
        Returns:
            Sanitized text safe for processing
        """
        if not text:
            return ""
        
        # Remove HTML tags and attributes
        sanitized = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True
        )
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    @staticmethod
    def validate_text_content(text: str) -> tuple[bool, Optional[str]]:
        """
        Validate text content for suspicious patterns and length limits.
        
        Args:
            text: Text content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text:
            return False, "Empty content not allowed"
        
        # Check length limits
        if len(text) > MAX_TEXT_LENGTH:
            return False, f"Content too long (max {MAX_TEXT_LENGTH} characters)"
        
        # Check for suspicious patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(text):
                logger.warning(f"Suspicious pattern detected in text content: {pattern.pattern}")
                return False, "Content contains potentially malicious patterns"
        
        # Check for excessive repetition (potential spam)
        if SecurityValidator._is_spam_content(text):
            return False, "Content appears to be spam"
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL for security and format compliance.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "Empty URL not allowed"
        
        # Check length
        if len(url) > MAX_URL_LENGTH:
            return False, f"URL too long (max {MAX_URL_LENGTH} characters)"
        
        try:
            parsed = urlparse(url)
            
            # Must have valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False, "URL must use HTTP or HTTPS protocol"
            
            # Must have valid hostname
            if not parsed.netloc:
                return False, "URL must have valid hostname"
            
            # Check for suspicious patterns in URL
            for pattern in COMPILED_PATTERNS:
                if pattern.search(url):
                    logger.warning(f"Suspicious pattern detected in URL: {pattern.pattern}")
                    return False, "URL contains potentially malicious patterns"
            
            return True, None
            
        except Exception as e:
            logger.warning(f"URL validation error: {e}")
            return False, "Invalid URL format"
    
    @staticmethod
    def validate_phone_number(phone: str) -> tuple[bool, Optional[str]]:
        """
        Validate phone number format for WhatsApp integration.
        
        Accepts WhatsApp phone numbers in formats:
        - whatsapp:+1234567890
        - whatsapp:1234567890
        - whatsapp:+1 (234) 567-8900 (with basic formatting)
        
        Args:
            phone: Phone number to validate (must start with 'whatsapp:')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Empty phone number not allowed"
        
        # Check length
        if len(phone) > MAX_PHONE_LENGTH:
            return False, f"Phone number too long (max {MAX_PHONE_LENGTH} characters)"
        
        # WhatsApp phone numbers should start with 'whatsapp:'
        if not phone.startswith('whatsapp:'):
            return False, "Invalid WhatsApp phone number format"
        
        # Extract the actual phone number part
        phone_part = phone.replace('whatsapp:', '')
        
        # Check if we have any phone number after the prefix
        if not phone_part:
            return False, "No phone number provided after 'whatsapp:' prefix"
        
        # Handle both +1234567890 and 1234567890 formats
        if phone_part.startswith('+'):
            phone_part = phone_part[1:]
        
        # Should contain only digits (allow some special characters like spaces, dashes, parentheses)
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone_part)
        if not clean_phone.isdigit():
            return False, "Phone number should contain only digits and basic formatting"
        
        # Should be reasonable length (7-15 digits for international numbers)
        if len(clean_phone) < 7 or len(clean_phone) > 15:
            return False, "Phone number length invalid"
        
        return True, None
    
    @staticmethod
    def validate_message_sid(message_sid: str) -> tuple[bool, Optional[str]]:
        """
        Validate Twilio message SID format.
        
        Args:
            message_sid: Message SID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message_sid:
            return False, "Empty message SID not allowed"
        
        # Check basic length and format requirements
        if len(message_sid) < 3:
            return False, "Message SID too short"
        
        # Check for maximum reasonable length
        if len(message_sid) > 100:
            return False, "Message SID too long"
        
        # Standard Twilio message SIDs: SM + 32 hex chars
        if message_sid.startswith('SM') and len(message_sid) == 34:
            # Should be SM followed by 32 hex characters
            hex_part = message_sid[2:]
            if re.match(r'^[A-Fa-f0-9]{32}$', hex_part):
                return True, None
            else:
                return False, "Invalid message SID format"
        
        # Allow test SIDs for development
        elif (message_sid.startswith('test_') or 
              message_sid.startswith('TEST_')):
            if re.match(r'^[A-Za-z0-9_]+$', message_sid):
                return True, None
            else:
                return False, "Test message SID contains invalid characters"
        
        # Allow other Twilio SID formats (MM, MG, etc.)
        elif re.match(r'^[A-Z]{2}[A-Fa-f0-9]{32}$', message_sid):
            return True, None
        
        # Be more lenient for development/testing
        elif re.match(r'^[A-Za-z0-9_\-]+$', message_sid) and len(message_sid) >= 10:
            return True, None
        
        else:
            return False, "Invalid Twilio message SID format"
    
    @staticmethod
    def _is_spam_content(text: str) -> bool:
        """
        Check if content appears to be spam based on repetition patterns.
        
        Args:
            text: Text to check for spam patterns
            
        Returns:
            True if content appears to be spam
        """
        # Check for excessive character repetition
        if re.search(r'(.)\1{20,}', text):  # Same character repeated 20+ times
            return True
        
        # Check for excessive word repetition
        words = text.lower().split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # If any word appears more than 30% of the time, likely spam
            max_count = max(word_counts.values())
            if max_count > len(words) * 0.3:
                return True
        
        return False
    
    @staticmethod
    def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data for safe logging by removing sensitive information.
        
        Args:
            data: Dictionary containing data to sanitize
            
        Returns:
            Sanitized dictionary safe for logging
        """
        sanitized = {}
        sensitive_keys = {
            'password', 'token', 'key', 'secret', 'auth', 'credential',
            'twilio_auth_token', 'openai_api_key', 'api_key'
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive information
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized


def validate_webhook_request(
    message_sid: str,
    from_number: str,
    to_number: str,
    body: str,
    media_url: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Comprehensive validation for Twilio webhook requests.
    
    Args:
        message_sid: Twilio message SID
        from_number: Sender's phone number
        to_number: Recipient's phone number
        body: Message body text
        media_url: Optional media URL
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = SecurityValidator()
    
    # Validate message SID
    valid, error = validator.validate_message_sid(message_sid)
    if not valid:
        return False, f"Invalid message SID: {error}"
    
    # Validate phone numbers
    valid, error = validator.validate_phone_number(from_number)
    if not valid:
        return False, f"Invalid sender phone: {error}"
    
    valid, error = validator.validate_phone_number(to_number)
    if not valid:
        return False, f"Invalid recipient phone: {error}"
    
    # Validate message body if present
    if body:
        valid, error = validator.validate_text_content(body)
        if not valid:
            return False, f"Invalid message body: {error}"
    
    # Validate media URL if present
    if media_url:
        valid, error = validator.validate_url(media_url)
        if not valid:
            return False, f"Invalid media URL: {error}"
    
    return True, None