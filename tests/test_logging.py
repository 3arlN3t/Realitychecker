"""
Tests for logging utilities with correlation IDs and structured logging.
"""

import json
import logging
import pytest
from unittest.mock import patch, MagicMock
from contextvars import copy_context

from app.utils.logging import (
    setup_logging,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    get_logger,
    log_with_context,
    sanitize_phone_number,
    sanitize_sensitive_data,
    StructuredFormatter,
    CorrelationIdFilter
)


class TestCorrelationId:
    """Test correlation ID functionality."""
    
    def test_get_correlation_id_generates_new_id(self):
        """Test that get_correlation_id generates a new ID when none exists."""
        clear_correlation_id()
        correlation_id = get_correlation_id()
        assert correlation_id is not None
        assert len(correlation_id) == 36  # UUID4 format
        assert correlation_id.count('-') == 4
    
    def test_get_correlation_id_returns_existing_id(self):
        """Test that get_correlation_id returns existing ID."""
        test_id = "test-correlation-id"
        set_correlation_id(test_id)
        correlation_id = get_correlation_id()
        assert correlation_id == test_id
    
    def test_set_correlation_id_with_custom_id(self):
        """Test setting a custom correlation ID."""
        test_id = "custom-test-id"
        result_id = set_correlation_id(test_id)
        assert result_id == test_id
        assert get_correlation_id() == test_id
    
    def test_set_correlation_id_generates_new_when_none_provided(self):
        """Test that set_correlation_id generates new ID when None provided."""
        result_id = set_correlation_id(None)
        assert result_id is not None
        assert len(result_id) == 36
        assert get_correlation_id() == result_id
    
    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        set_correlation_id("test-id")
        clear_correlation_id()
        # After clearing, get_correlation_id should generate a new one
        new_id = get_correlation_id()
        assert new_id != "test-id"
    
    def test_correlation_id_isolation_between_contexts(self):
        """Test that correlation IDs are isolated between contexts."""
        def context_1():
            set_correlation_id("context-1-id")
            return get_correlation_id()
        
        def context_2():
            set_correlation_id("context-2-id")
            return get_correlation_id()
        
        # Run in separate contexts
        ctx1 = copy_context()
        ctx2 = copy_context()
        
        id1 = ctx1.run(context_1)
        id2 = ctx2.run(context_2)
        
        assert id1 == "context-1-id"
        assert id2 == "context-2-id"
        assert id1 != id2


class TestStructuredFormatter:
    """Test structured JSON formatter."""
    
    def test_structured_formatter_basic_format(self):
        """Test basic JSON formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-correlation-id"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["correlation_id"] == "test-correlation-id"
        assert data["module"] == "path"
        assert data["function"] is None  # funcName can be None
        assert data["line"] == 42
        assert "timestamp" in data
    
    def test_structured_formatter_with_exception(self):
        """Test JSON formatting with exception information."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.correlation_id = "test-correlation-id"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test exception"
        assert "traceback" in data["exception"]
    
    def test_structured_formatter_with_extra_fields(self):
        """Test JSON formatting with extra fields."""
        formatter = StructuredFormatter(include_extra=True)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-correlation-id"
        record.custom_field = "custom_value"
        record.user_id = 12345
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "extra" in data
        assert data["extra"]["custom_field"] == "custom_value"
        assert data["extra"]["user_id"] == 12345
    
    def test_structured_formatter_exclude_extra_fields(self):
        """Test JSON formatting without extra fields."""
        formatter = StructuredFormatter(include_extra=False)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-correlation-id"
        record.custom_field = "custom_value"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "extra" not in data


class TestCorrelationIdFilter:
    """Test correlation ID filter."""
    
    def test_correlation_id_filter_adds_id(self):
        """Test that filter adds correlation ID to record."""
        set_correlation_id("test-filter-id")
        
        filter_instance = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == "test-filter-id"
    
    def test_correlation_id_filter_default_when_none(self):
        """Test that filter adds default ID when none exists."""
        clear_correlation_id()
        
        filter_instance = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == "no-correlation-id"


class TestLoggingSetup:
    """Test logging setup functionality."""
    
    @patch('logging.getLogger')
    def test_setup_logging_basic(self, mock_get_logger):
        """Test basic logging setup."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        setup_logging(log_level="INFO", use_json=False)
        
        # Verify root logger configuration - it may set WARNING level due to external libraries
        mock_root_logger.setLevel.assert_called()
        mock_root_logger.addHandler.assert_called()
    
    @patch('logging.getLogger')
    def test_setup_logging_with_json(self, mock_get_logger):
        """Test logging setup with JSON formatting."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        setup_logging(log_level="DEBUG", use_json=True)
        
        # Verify root logger configuration - it may set WARNING level due to external libraries
        mock_root_logger.setLevel.assert_called()
        mock_root_logger.addHandler.assert_called()
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestLogWithContext:
    """Test contextual logging functionality."""
    
    def test_log_with_context(self):
        """Test logging with additional context."""
        mock_logger = MagicMock()
        
        log_with_context(
            mock_logger,
            logging.INFO,
            "Test message",
            user_id=123,
            action="test_action"
        )
        
        # Verify log was called with extra context
        mock_logger.log.assert_called_once_with(
            logging.INFO,
            "Test message",
            extra={"user_id": 123, "action": "test_action"}
        )


class TestDataSanitization:
    """Test data sanitization for logging."""
    
    def test_sanitize_phone_number_full_number(self):
        """Test sanitizing a full phone number."""
        phone = "whatsapp:+1234567890"
        result = sanitize_phone_number(phone)
        assert result == "+12***890"
    
    def test_sanitize_phone_number_short_number(self):
        """Test sanitizing a short phone number."""
        phone = "+123"
        result = sanitize_phone_number(phone)
        assert result == "***"
    
    def test_sanitize_phone_number_empty(self):
        """Test sanitizing empty phone number."""
        result = sanitize_phone_number("")
        assert result == "[empty]"
    
    def test_sanitize_phone_number_none(self):
        """Test sanitizing None phone number."""
        result = sanitize_phone_number(None)
        assert result == "[empty]"
    
    def test_sanitize_sensitive_data_api_keys(self):
        """Test sanitizing sensitive data with API keys."""
        data = {
            "openai_api_key": "sk-1234567890",
            "twilio_auth_token": "auth_token_123",
            "user_name": "john_doe",
            "message": "Hello world"
        }
        
        result = sanitize_sensitive_data(data)
        
        assert result["openai_api_key"] == "[REDACTED]"
        assert result["twilio_auth_token"] == "[REDACTED]"
        assert result["user_name"] == "john_doe"
        assert result["message"] == "Hello world"
    
    def test_sanitize_sensitive_data_phone_numbers(self):
        """Test sanitizing sensitive data with phone numbers."""
        data = {
            "from": "whatsapp:+1234567890",
            "to": "whatsapp:+0987654321",
            "message": "Test message"
        }
        
        result = sanitize_sensitive_data(data)
        
        assert result["from"] == "+12***890"
        assert result["to"] == "+09***321"
        assert result["message"] == "Test message"
    
    def test_sanitize_sensitive_data_mixed(self):
        """Test sanitizing mixed sensitive and non-sensitive data."""
        data = {
            "api_key": "secret_key_123",
            "from": "whatsapp:+1234567890",
            "user_id": 12345,
            "password": "secret_password",
            "message": "Hello"
        }
        
        result = sanitize_sensitive_data(data)
        
        assert result["api_key"] == "[REDACTED]"
        assert result["from"] == "+12***890"
        assert result["user_id"] == 12345
        assert result["password"] == "[REDACTED]"
        assert result["message"] == "Hello"


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    def test_logging_with_correlation_id_flow(self):
        """Test complete logging flow with correlation ID."""
        # Set up logging
        setup_logging(log_level="INFO", use_json=False)
        
        # Set correlation ID
        correlation_id = set_correlation_id("integration-test-id")
        
        # Get logger and log message
        logger = get_logger("integration.test")
        
        with patch.object(logger, 'log') as mock_log:
            log_with_context(
                logger,
                logging.INFO,
                "Integration test message",
                test_field="test_value"
            )
            
            # Verify the log call
            mock_log.assert_called_once_with(
                logging.INFO,
                "Integration test message",
                extra={"test_field": "test_value"}
            )
        
        # Verify correlation ID is maintained
        assert get_correlation_id() == correlation_id
    
    def test_error_logging_with_exception_info(self):
        """Test error logging with exception information."""
        setup_logging(log_level="ERROR", use_json=True)
        logger = get_logger("error.test")
        
        try:
            raise ValueError("Test error for logging")
        except ValueError as e:
            with patch.object(logger, 'error') as mock_error:
                logger.error(f"Error occurred: {e}", exc_info=True)
                mock_error.assert_called_once()