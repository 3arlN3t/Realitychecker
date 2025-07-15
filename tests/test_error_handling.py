"""
Tests for comprehensive error handling utilities.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    ErrorInfo,
    ErrorHandler,
    error_handler,
    handle_error,
    get_fallback_response
)


class TestErrorInfo:
    """Test ErrorInfo dataclass."""
    
    def test_error_info_creation(self):
        """Test creating ErrorInfo instance."""
        error_info = ErrorInfo(
            category=ErrorCategory.PDF_PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            user_message="Test user message",
            technical_message="Test technical message",
            should_retry=True,
            retry_delay_seconds=30,
            fallback_available=True
        )
        
        assert error_info.category == ErrorCategory.PDF_PROCESSING
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.user_message == "Test user message"
        assert error_info.technical_message == "Test technical message"
        assert error_info.should_retry is True
        assert error_info.retry_delay_seconds == 30
        assert error_info.fallback_available is True
    
    def test_error_info_defaults(self):
        """Test ErrorInfo with default values."""
        error_info = ErrorInfo(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW,
            user_message="Test message",
            technical_message="Technical message"
        )
        
        assert error_info.should_retry is False
        assert error_info.retry_delay_seconds is None
        assert error_info.fallback_available is False


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_get_error_info_existing_key(self):
        """Test getting error info for existing key."""
        handler = ErrorHandler()
        error_info = handler.get_error_info("pdf_download_failed")
        
        assert error_info.category == ErrorCategory.PDF_PROCESSING
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "PDF Download Failed" in error_info.user_message
        assert error_info.should_retry is True
        assert error_info.retry_delay_seconds == 30
    
    def test_get_error_info_nonexistent_key(self):
        """Test getting error info for non-existent key returns default."""
        handler = ErrorHandler()
        error_info = handler.get_error_info("nonexistent_error")
        
        assert error_info.category == ErrorCategory.SYSTEM
        assert error_info.severity == ErrorSeverity.HIGH
        assert "System Error" in error_info.user_message
    
    def test_classify_error_pdf_processing(self):
        """Test error classification for PDF processing errors."""
        handler = ErrorHandler()
        
        # Test PDF download error
        error = Exception("Failed to download PDF from URL")
        error_key = handler._classify_error(error)
        assert error_key == "pdf_download_failed"
        
        # Test PDF too large error
        error = Exception("PDF file too large: 15MB")
        error_key = handler._classify_error(error)
        assert error_key == "pdf_too_large"
        
        # Test PDF extraction error
        error = Exception("Failed to extract text from PDF")
        error_key = handler._classify_error(error)
        assert error_key == "pdf_extraction_failed"
        
        # Test PDF no content error
        error = Exception("PDF contains no extractable text content")
        error_key = handler._classify_error(error)
        assert error_key == "pdf_no_content"
    
    def test_classify_error_openai_service(self):
        """Test error classification for OpenAI service errors."""
        handler = ErrorHandler()
        
        # Test OpenAI timeout
        error = Exception("OpenAI API request timed out")
        error_key = handler._classify_error(error)
        assert error_key == "openai_timeout"
        
        # Test rate limit
        error = Exception("OpenAI rate limit exceeded")
        error_key = handler._classify_error(error)
        assert error_key == "openai_rate_limit"
        
        # Test invalid response
        error = Exception("Invalid response format from OpenAI")
        error_key = handler._classify_error(error)
        assert error_key == "openai_invalid_response"
        
        # Test general OpenAI error
        error = Exception("OpenAI API error occurred")
        error_key = handler._classify_error(error)
        assert error_key == "openai_api_error"
    
    def test_classify_error_twilio_service(self):
        """Test error classification for Twilio service errors."""
        handler = ErrorHandler()
        
        # Test Twilio auth error
        error = Exception("Twilio authentication failed")
        error_key = handler._classify_error(error)
        assert error_key == "twilio_auth_failed"
        
        # Test general Twilio error
        error = Exception("Failed to send WhatsApp message")
        error_key = handler._classify_error(error)
        assert error_key == "twilio_send_failed"
    
    def test_classify_error_network_errors(self):
        """Test error classification for network errors."""
        handler = ErrorHandler()
        
        # Test timeout error
        error = Exception("Request timeout occurred")
        error_key = handler._classify_error(error)
        assert error_key == "network_timeout"
        
        # Test connection error
        error = Exception("Network connection failed")
        error_key = handler._classify_error(error)
        assert error_key == "network_error"
    
    def test_classify_error_validation_errors(self):
        """Test error classification for validation errors."""
        handler = ErrorHandler()
        
        # Test content too short
        error = Exception("Content is too short for analysis")
        error_key = handler._classify_error(error)
        assert error_key == "content_too_short"
        
        # Test unsupported media
        error = Exception("Unsupported media type received")
        error_key = handler._classify_error(error)
        assert error_key == "unsupported_media"
    
    def test_classify_error_configuration_errors(self):
        """Test error classification for configuration errors."""
        handler = ErrorHandler()
        
        # Test configuration error
        error = Exception("Missing required environment variable")
        error_key = handler._classify_error(error)
        assert error_key == "configuration_error"
    
    def test_classify_error_default_system_error(self):
        """Test error classification defaults to system error."""
        handler = ErrorHandler()
        
        # Test unknown error
        error = Exception("Some unknown error occurred")
        error_key = handler._classify_error(error)
        assert error_key == "system_error"
    
    @patch('app.utils.error_handling.log_with_context')
    def test_handle_error_with_context(self, mock_log):
        """Test handling error with context information."""
        handler = ErrorHandler()
        error = Exception("Test error for handling")
        context = {"user_id": "test_user", "action": "test_action"}
        correlation_id = "test-correlation-id"
        
        user_message, error_info = handler.handle_error(error, context, correlation_id)
        
        # Verify logging was called
        mock_log.assert_called_once()
        
        # Verify return values
        assert isinstance(user_message, str)
        assert isinstance(error_info, ErrorInfo)
        assert error_info.category == ErrorCategory.SYSTEM
    
    @patch('app.utils.error_handling.log_with_context')
    def test_handle_error_without_context(self, mock_log):
        """Test handling error without context information."""
        handler = ErrorHandler()
        error = Exception("PDF download failed")
        
        user_message, error_info = handler.handle_error(error)
        
        # Verify logging was called
        mock_log.assert_called_once()
        
        # Verify return values
        assert "PDF Download Failed" in user_message
        assert error_info.category == ErrorCategory.PDF_PROCESSING
    
    def test_get_fallback_response_openai_service(self):
        """Test getting fallback response for OpenAI service errors."""
        handler = ErrorHandler()
        
        fallback = handler.get_fallback_response(ErrorCategory.OPENAI_SERVICE)
        
        assert fallback is not None
        assert "Basic Analysis Available" in fallback
        assert "Red Flags" in fallback
        assert "Good Signs" in fallback
    
    def test_get_fallback_response_no_fallback(self):
        """Test getting fallback response for category without fallback."""
        handler = ErrorHandler()
        
        fallback = handler.get_fallback_response(ErrorCategory.PDF_PROCESSING)
        
        assert fallback is None


class TestGlobalErrorHandling:
    """Test global error handling functions."""
    
    @patch('app.utils.error_handling.error_handler.handle_error')
    def test_handle_error_function(self, mock_handle_error):
        """Test global handle_error function."""
        mock_handle_error.return_value = ("Test message", MagicMock())
        
        error = Exception("Test error")
        context = {"test": "context"}
        correlation_id = "test-id"
        
        result = handle_error(error, context, correlation_id)
        
        mock_handle_error.assert_called_once_with(error, context, correlation_id)
        assert result[0] == "Test message"
    
    @patch('app.utils.error_handling.error_handler.get_fallback_response')
    def test_get_fallback_response_function(self, mock_get_fallback):
        """Test global get_fallback_response function."""
        mock_get_fallback.return_value = "Fallback message"
        
        result = get_fallback_response(ErrorCategory.OPENAI_SERVICE)
        
        mock_get_fallback.assert_called_once_with(ErrorCategory.OPENAI_SERVICE)
        assert result == "Fallback message"


class TestErrorScenarios:
    """Test specific error scenarios."""
    
    def test_pdf_processing_error_scenario(self):
        """Test complete PDF processing error scenario."""
        handler = ErrorHandler()
        
        # Simulate PDF download failure
        error = Exception("Failed to download PDF: HTTP 404")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.PDF_PROCESSING
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is True
        assert "PDF Download Failed" in user_message
        assert "Network connectivity issues" in user_message
    
    def test_openai_rate_limit_error_scenario(self):
        """Test OpenAI rate limit error scenario."""
        handler = ErrorHandler()
        
        # Simulate rate limit error
        error = Exception("OpenAI rate limit exceeded for requests")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.RATE_LIMIT
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is True
        assert error_info.retry_delay_seconds == 300
        assert "Service Busy" in user_message
    
    def test_twilio_authentication_error_scenario(self):
        """Test Twilio authentication error scenario."""
        handler = ErrorHandler()
        
        # Simulate authentication error
        error = Exception("Twilio authentication failed - invalid credentials")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.AUTHENTICATION
        assert error_info.severity == ErrorSeverity.CRITICAL
        assert error_info.should_retry is False
        assert "Service Authentication Error" in user_message
    
    def test_network_timeout_error_scenario(self):
        """Test network timeout error scenario."""
        handler = ErrorHandler()
        
        # Simulate network timeout
        error = Exception("Request timeout after 30 seconds")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.should_retry is True
        assert error_info.retry_delay_seconds == 30
        assert "Network Timeout" in user_message
    
    def test_validation_error_scenario(self):
        """Test validation error scenario."""
        handler = ErrorHandler()
        
        # Simulate content too short error
        error = Exception("Content is too short for meaningful analysis")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.LOW
        assert error_info.should_retry is False
        assert "Content Too Short" in user_message
        assert "Job title and description" in user_message
    
    def test_system_error_scenario(self):
        """Test system error scenario."""
        handler = ErrorHandler()
        
        # Simulate unexpected system error
        error = Exception("Unexpected internal error occurred")
        user_message, error_info = handler.handle_error(error)
        
        assert error_info.category == ErrorCategory.SYSTEM
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.should_retry is True
        assert error_info.retry_delay_seconds == 120
        assert "System Error" in user_message


class TestErrorMessageContent:
    """Test error message content and formatting."""
    
    def test_pdf_error_messages_are_user_friendly(self):
        """Test that PDF error messages are user-friendly."""
        handler = ErrorHandler()
        
        # Test various PDF errors
        pdf_errors = [
            "pdf_download_failed",
            "pdf_too_large", 
            "pdf_extraction_failed",
            "pdf_no_content"
        ]
        
        for error_key in pdf_errors:
            error_info = handler.get_error_info(error_key)
            message = error_info.user_message
            
            # Check for user-friendly elements
            assert "❌" in message or "📎" in message  # Emoji
            assert "Please" in message or "Try" in message  # Helpful language
            assert not any(tech_term in message.lower() for tech_term in [
                "exception", "traceback", "api", "http", "bytes"
            ])  # No technical jargon
    
    def test_openai_error_messages_are_user_friendly(self):
        """Test that OpenAI error messages are user-friendly."""
        handler = ErrorHandler()
        
        openai_errors = [
            "openai_timeout",
            "openai_rate_limit",
            "openai_api_error",
            "openai_invalid_response"
        ]
        
        for error_key in openai_errors:
            error_info = handler.get_error_info(error_key)
            message = error_info.user_message
            
            # Check for user-friendly elements
            assert any(emoji in message for emoji in ["⏱️", "🚦", "🔧", "🤖"])
            assert "Please" in message or "try again" in message.lower()
            assert "OpenAI" not in message  # Don't expose internal service names
    
    def test_error_messages_provide_actionable_guidance(self):
        """Test that error messages provide actionable guidance."""
        handler = ErrorHandler()
        
        # Test errors that should provide specific guidance
        guidance_errors = [
            ("content_too_short", ["Job title", "Company name", "Salary"]),
            ("unsupported_media", ["PDF file", "copy and paste"]),
            ("pdf_too_large", ["smaller PDF", "split", "text"]),
            ("pdf_extraction_failed", ["password-protected", "images", "text"])
        ]
        
        for error_key, expected_guidance in guidance_errors:
            error_info = handler.get_error_info(error_key)
            message = error_info.user_message.lower()
            
            # Check that expected guidance is present
            for guidance in expected_guidance:
                assert guidance.lower() in message
    
    def test_fallback_response_content(self):
        """Test fallback response content is helpful."""
        handler = ErrorHandler()
        
        fallback = handler.get_fallback_response(ErrorCategory.OPENAI_SERVICE)
        
        assert fallback is not None
        assert "🚩" in fallback  # Red flags section
        assert "✅" in fallback  # Good signs section
        assert len(fallback.split("•")) >= 8  # Multiple bullet points
        assert "try again later" in fallback.lower()


class TestErrorHandlerIntegration:
    """Test error handler integration scenarios."""
    
    @patch('app.utils.logging.get_correlation_id')
    @patch('app.utils.error_handling.log_with_context')
    def test_complete_error_handling_flow(self, mock_log, mock_correlation_id):
        """Test complete error handling flow."""
        mock_correlation_id.return_value = "integration-test-id"
        
        handler = ErrorHandler()
        
        # Simulate a complex error scenario
        error = Exception("Failed to download PDF: network timeout after 30s")
        context = {
            "user_id": "test_user",
            "file_size": "5MB",
            "attempt": 2
        }
        
        user_message, error_info = handler.handle_error(error, context, "test-correlation-id")
        
        # Verify error classification
        assert error_info.category == ErrorCategory.PDF_PROCESSING
        assert error_info.should_retry is True
        
        # Verify logging was called with proper context
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        
        # Check logging parameters
        assert call_args[1]["error_category"] == ErrorCategory.PDF_PROCESSING.value
        assert call_args[1]["correlation_id"] == "test-correlation-id"
        assert "user_id" in call_args[1]
        
        # Verify user message is appropriate
        assert "PDF Download Failed" in user_message
        assert "try again" in user_message.lower()
    
    def test_error_severity_logging_levels(self):
        """Test that error severity maps to appropriate logging levels."""
        handler = ErrorHandler()
        
        # Test different severity levels
        severity_tests = [
            ("pdf_download_failed", ErrorSeverity.MEDIUM),
            ("twilio_auth_failed", ErrorSeverity.CRITICAL),
            ("content_too_short", ErrorSeverity.LOW),
            ("system_error", ErrorSeverity.HIGH)
        ]
        
        for error_key, expected_severity in severity_tests:
            error_info = handler.get_error_info(error_key)
            assert error_info.severity == expected_severity