"""Tests for security utilities and validation."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.utils.security import (
    SecurityValidator, 
    validate_webhook_request,
    MAX_TEXT_LENGTH,
    MAX_URL_LENGTH,
    MAX_PHONE_LENGTH
)
from app.middleware.rate_limiting import RateLimiter, RateLimitConfig
from app.main import app


class TestSecurityValidator:
    """Test cases for SecurityValidator class."""
    
    def test_sanitize_text_removes_html_tags(self):
        """Test that HTML tags are removed from text."""
        validator = SecurityValidator()
        
        # Test basic HTML removal - bleach removes tags but keeps content
        dirty_text = "<script>alert('xss')</script>Hello World"
        clean_text = validator.sanitize_text(dirty_text)
        assert "Hello World" in clean_text
        assert "<script>" not in clean_text
        assert "</script>" not in clean_text
        
        # Test multiple tags
        dirty_text = "<div><p>Hello</p><span>World</span></div>"
        clean_text = validator.sanitize_text(dirty_text)
        assert "Hello" in clean_text
        assert "World" in clean_text
        assert "<div>" not in clean_text
        assert "<p>" not in clean_text
    
    def test_sanitize_text_removes_excessive_whitespace(self):
        """Test that excessive whitespace is normalized."""
        validator = SecurityValidator()
        
        dirty_text = "Hello    \n\n\n   World   \t\t  "
        clean_text = validator.sanitize_text(dirty_text)
        assert clean_text == "Hello World"
    
    def test_sanitize_text_handles_empty_input(self):
        """Test sanitization of empty or None input."""
        validator = SecurityValidator()
        
        assert validator.sanitize_text("") == ""
        assert validator.sanitize_text(None) == ""
        assert validator.sanitize_text("   ") == ""
    
    def test_validate_text_content_detects_suspicious_patterns(self):
        """Test detection of suspicious patterns in text."""
        validator = SecurityValidator()
        
        # Test script injection
        is_valid, error = validator.validate_text_content("<script>alert('xss')</script>")
        assert not is_valid
        assert "malicious patterns" in error
        
        # Test SQL injection
        is_valid, error = validator.validate_text_content("'; DROP TABLE users; --")
        assert not is_valid
        assert "malicious patterns" in error
        
        # Test command injection
        is_valid, error = validator.validate_text_content("test; rm -rf /")
        assert not is_valid
        assert "malicious patterns" in error
    
    def test_validate_text_content_length_limits(self):
        """Test text length validation."""
        validator = SecurityValidator()
        
        # Test empty content
        is_valid, error = validator.validate_text_content("")
        assert not is_valid
        assert "Empty content" in error
        
        # Test content too long
        long_text = "a" * (MAX_TEXT_LENGTH + 1)
        is_valid, error = validator.validate_text_content(long_text)
        assert not is_valid
        assert "too long" in error
        
        # Test valid length
        valid_text = "This is a legitimate job posting with reasonable content length."
        is_valid, error = validator.validate_text_content(valid_text)
        assert is_valid
        assert error is None
    
    def test_validate_text_content_spam_detection(self):
        """Test spam content detection."""
        validator = SecurityValidator()
        
        # Test excessive character repetition
        spam_text = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        is_valid, error = validator.validate_text_content(spam_text)
        assert not is_valid
        assert "spam" in error
        
        # Test excessive word repetition
        spam_text = "buy now " * 50
        is_valid, error = validator.validate_text_content(spam_text)
        assert not is_valid
        assert "spam" in error
    
    def test_validate_url_format(self):
        """Test URL format validation."""
        validator = SecurityValidator()
        
        # Test valid URLs
        valid_urls = [
            "https://example.com/file.pdf",
            "http://test.com/document.pdf",
            "https://subdomain.example.com/path/file.pdf"
        ]
        
        for url in valid_urls:
            is_valid, error = validator.validate_url(url)
            assert is_valid, f"URL should be valid: {url}"
            assert error is None
        
        # Test invalid URLs
        invalid_urls = [
            "",
            "ftp://example.com/file.pdf",  # Wrong protocol
            "javascript:alert('xss')",     # Malicious protocol
            "http://",                     # No hostname
            "not-a-url"                    # Invalid format
        ]
        
        for url in invalid_urls:
            is_valid, error = validator.validate_url(url)
            assert not is_valid, f"URL should be invalid: {url}"
            assert error is not None
    
    def test_validate_url_length_limit(self):
        """Test URL length validation."""
        validator = SecurityValidator()
        
        # Test URL too long
        long_url = "https://example.com/" + "a" * MAX_URL_LENGTH
        is_valid, error = validator.validate_url(long_url)
        assert not is_valid
        assert "too long" in error
    
    def test_validate_phone_number_format(self):
        """Test phone number validation."""
        validator = SecurityValidator()
        
        # Test valid WhatsApp phone numbers
        valid_phones = [
            "whatsapp:+1234567890",
            "whatsapp:+4471234567",  # Shorter UK number
            "whatsapp:+123456789012"  # 12 digits (within 15 limit)
        ]
        
        for phone in valid_phones:
            is_valid, error = validator.validate_phone_number(phone)
            assert is_valid, f"Phone should be valid: {phone}"
            assert error is None
        
        # Test invalid phone numbers
        invalid_phones = [
            "",
            "+1234567890",              # Missing whatsapp: prefix
            "whatsapp:1234567890",      # Missing + sign
            "whatsapp:+123abc",         # Contains letters
            "whatsapp:+123",            # Too short
            "whatsapp:+" + "1" * 20     # Too long
        ]
        
        for phone in invalid_phones:
            is_valid, error = validator.validate_phone_number(phone)
            assert not is_valid, f"Phone should be invalid: {phone}"
            assert error is not None
    
    def test_validate_message_sid_format(self):
        """Test Twilio message SID validation."""
        validator = SecurityValidator()
        
        # Test valid message SID
        valid_sid = "SM" + "a" * 32
        is_valid, error = validator.validate_message_sid(valid_sid)
        assert is_valid
        assert error is None
        
        # Test invalid message SIDs
        invalid_sids = [
            "",
            "SM123",                    # Too short
            "AC" + "a" * 32,           # Wrong prefix
            "SM" + "z" * 32,           # Invalid hex characters
            "SM" + "a" * 31,           # Wrong length
        ]
        
        for sid in invalid_sids:
            is_valid, error = validator.validate_message_sid(sid)
            assert not is_valid, f"SID should be invalid: {sid}"
            assert error is not None
    
    def test_sanitize_for_logging(self):
        """Test data sanitization for logging."""
        validator = SecurityValidator()
        
        sensitive_data = {
            "password": "secret123",
            "api_key": "sk-1234567890",
            "twilio_auth_token": "auth_token_123",
            "normal_field": "normal_value",
            "long_text": "a" * 200
        }
        
        sanitized = validator.sanitize_for_logging(sensitive_data)
        
        # Check sensitive fields are redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["twilio_auth_token"] == "[REDACTED]"
        
        # Check normal fields are preserved
        assert sanitized["normal_field"] == "normal_value"
        
        # Check long text is truncated
        assert len(sanitized["long_text"]) <= 103  # 100 chars + "..."


class TestWebhookValidation:
    """Test cases for webhook request validation."""
    
    def test_validate_webhook_request_valid_data(self):
        """Test validation of valid webhook request data."""
        is_valid, error = validate_webhook_request(
            message_sid="SM" + "a" * 32,
            from_number="whatsapp:+1234567890",
            to_number="whatsapp:+0987654321",
            body="This is a legitimate job posting",
            media_url="https://example.com/file.pdf"
        )
        
        assert is_valid
        assert error is None
    
    def test_validate_webhook_request_invalid_message_sid(self):
        """Test validation with invalid message SID."""
        is_valid, error = validate_webhook_request(
            message_sid="invalid_sid",
            from_number="whatsapp:+1234567890",
            to_number="whatsapp:+0987654321",
            body="Test message"
        )
        
        assert not is_valid
        assert "Invalid message SID" in error
    
    def test_validate_webhook_request_invalid_phone_numbers(self):
        """Test validation with invalid phone numbers."""
        # Invalid sender phone
        is_valid, error = validate_webhook_request(
            message_sid="SM" + "a" * 32,
            from_number="invalid_phone",
            to_number="whatsapp:+0987654321",
            body="Test message"
        )
        
        assert not is_valid
        assert "Invalid sender phone" in error
        
        # Invalid recipient phone
        is_valid, error = validate_webhook_request(
            message_sid="SM" + "a" * 32,
            from_number="whatsapp:+1234567890",
            to_number="invalid_phone",
            body="Test message"
        )
        
        assert not is_valid
        assert "Invalid recipient phone" in error
    
    def test_validate_webhook_request_malicious_content(self):
        """Test validation with malicious content."""
        is_valid, error = validate_webhook_request(
            message_sid="SM" + "a" * 32,
            from_number="whatsapp:+1234567890",
            to_number="whatsapp:+0987654321",
            body="<script>alert('xss')</script>",
            media_url="javascript:alert('xss')"
        )
        
        assert not is_valid
        assert "malicious patterns" in error or "Invalid media URL" in error


class TestRateLimiter:
    """Test cases for rate limiting functionality."""
    
    def test_rate_limiter_allows_requests_within_limits(self):
        """Test that requests within limits are allowed."""
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            burst_limit=3,
            burst_window=10
        )
        limiter = RateLimiter(config)
        
        # Should allow first few requests
        for i in range(3):
            allowed, reason = limiter.is_allowed("test_client")
            assert allowed, f"Request {i+1} should be allowed"
            assert reason is None
    
    def test_rate_limiter_blocks_burst_limit(self):
        """Test that burst limit is enforced."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=50,
            burst_limit=2,
            burst_window=10
        )
        limiter = RateLimiter(config)
        
        # Allow first 2 requests
        for i in range(2):
            allowed, reason = limiter.is_allowed("test_client")
            assert allowed
        
        # Block 3rd request (exceeds burst limit)
        allowed, reason = limiter.is_allowed("test_client")
        assert not allowed
        assert "Burst limit exceeded" in reason
    
    def test_rate_limiter_blocks_minute_limit(self):
        """Test that per-minute limit is enforced."""
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=50,
            burst_limit=5,
            burst_window=10
        )
        limiter = RateLimiter(config)
        
        # Allow first 2 requests
        for i in range(2):
            allowed, reason = limiter.is_allowed("test_client")
            assert allowed
        
        # Block 3rd request (exceeds minute limit)
        allowed, reason = limiter.is_allowed("test_client")
        assert not allowed
        assert "Rate limit exceeded" in reason
        assert "per minute" in reason
    
    def test_rate_limiter_different_clients(self):
        """Test that different clients have separate limits."""
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=10,
            burst_limit=2,
            burst_window=10
        )
        limiter = RateLimiter(config)
        
        # Client 1 uses up their limit
        for i in range(2):
            allowed, reason = limiter.is_allowed("client1")
            assert allowed
        
        # Client 1 is now blocked
        allowed, reason = limiter.is_allowed("client1")
        assert not allowed
        
        # Client 2 should still be allowed
        allowed, reason = limiter.is_allowed("client2")
        assert allowed
    
    def test_rate_limiter_get_stats(self):
        """Test rate limiter statistics."""
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            burst_limit=3,
            burst_window=10
        )
        limiter = RateLimiter(config)
        
        # Make some requests
        for i in range(2):
            limiter.is_allowed("test_client")
        
        # Check stats
        stats = limiter.get_stats("test_client")
        assert stats["burst_count"] == 2
        assert stats["minute_count"] == 2
        assert stats["hour_count"] == 2
        assert stats["burst_limit"] == 3
        assert stats["minute_limit"] == 5
        assert stats["hour_limit"] == 20
    
    def test_rate_limiter_cleanup(self):
        """Test cleanup of old entries."""
        config = RateLimitConfig()
        limiter = RateLimiter(config)
        
        # Add some requests with old timestamp
        with patch('time.time', return_value=1000):  # Old timestamp
            limiter.is_allowed("test_client")
        
        # Verify client exists
        assert "test_client" in limiter._requests
        
        # Mock current time to be much later and cleanup
        with patch('time.time', return_value=5000):  # Much later
            limiter.cleanup_old_entries()
        
        # Client should be removed after cleanup
        assert "test_client" not in limiter._requests


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_rate_limiting_middleware_integration(self):
        """Test rate limiting middleware with FastAPI."""
        client = TestClient(app)
        
        # Make requests to webhook endpoint
        webhook_data = {
            "MessageSid": "SM" + "a" * 32,
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+0987654321",
            "Body": "Test job posting",
            "NumMedia": "0"
        }
        
        # First few requests should succeed (or fail for other reasons, not rate limiting)
        for i in range(3):
            response = client.post("/webhook/whatsapp", data=webhook_data)
            # Should not be rate limited (status 429)
            assert response.status_code != 429
    
    def test_security_headers_applied(self):
        """Test that security headers are applied to responses."""
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        
        # Check header values
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_webhook_input_sanitization(self):
        """Test that webhook input is sanitized."""
        client = TestClient(app)
        
        # Send malicious content
        webhook_data = {
            "MessageSid": "SM" + "a" * 32,
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+0987654321",
            "Body": "<script>alert('xss')</script>Legitimate job content",
            "NumMedia": "0"
        }
        
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Should not return 400 due to malicious content being sanitized
        # (may fail for other reasons like missing services, but not input validation)
        assert response.status_code != 400 or "malicious patterns" not in response.text


@pytest.fixture
def mock_security_validator():
    """Mock SecurityValidator for testing."""
    with patch('app.utils.security.SecurityValidator') as mock:
        validator_instance = Mock()
        validator_instance.sanitize_text.return_value = "sanitized text"
        validator_instance.validate_text_content.return_value = (True, None)
        validator_instance.validate_url.return_value = (True, None)
        validator_instance.validate_phone_number.return_value = (True, None)
        validator_instance.validate_message_sid.return_value = (True, None)
        mock.return_value = validator_instance
        yield validator_instance


class TestSecurityMocks:
    """Test security functionality with mocked dependencies."""
    
    def test_webhook_validation_with_mocked_security(self, mock_security_validator):
        """Test webhook validation with mocked security validator."""
        from app.utils.security import validate_webhook_request
        
        # Should pass validation with mocked validator
        is_valid, error = validate_webhook_request(
            "test_sid", "test_from", "test_to", "test_body", "test_url"
        )
        
        assert is_valid
        assert error is None
        
        # Verify security validator methods were called
        mock_security_validator.validate_message_sid.assert_called_once()
        mock_security_validator.validate_phone_number.assert_called()
        mock_security_validator.validate_text_content.assert_called_once()
        mock_security_validator.validate_url.assert_called_once()