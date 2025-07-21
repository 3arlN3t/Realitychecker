"""
Structured logging utilities with correlation IDs for request tracking.

This module provides enhanced logging capabilities with correlation IDs,
structured JSON logging, and context management for better observability.
"""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Dict, Any, Optional
from datetime import datetime, timezone


# Context variable to store correlation ID across async calls
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = correlation_id_var.get() or 'no-correlation-id'
        return True


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize the structured formatter.
        
        Args:
            include_extra: Whether to include extra fields in log records
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation-id'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields if enabled
        if self.include_extra:
            # Add any extra fields that were passed to the logger
            extra_fields = {
                key: value for key, value in record.__dict__.items()
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info', 'correlation_id'
                }
            }
            if extra_fields:
                log_data['extra'] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", use_json: bool = False) -> None:
    """
    Set up application logging with correlation ID support.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON structured logging
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler()
    
    # Set up formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    handler.addFilter(correlation_filter)
    
    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Reduce noise from external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('twilio').setLevel(logging.WARNING)


def get_correlation_id() -> str:
    """
    Get the current correlation ID or generate a new one.
    
    Returns:
        str: Current correlation ID
    """
    correlation_id = correlation_id_var.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set a correlation ID for the current context.
    
    Args:
        correlation_id: Correlation ID to set, or None to generate a new one
        
    Returns:
        str: The correlation ID that was set
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_var.set(None)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance to use
        level: Logging level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **context: Additional context fields to include
    """
    logger.log(level, message, extra=context)


def sanitize_phone_number(phone_number: str) -> str:
    """
    Sanitize phone number or user ID for logging (mask middle digits).
    
    Args:
        phone_number: Phone number or user ID to sanitize
        
    Returns:
        str: Sanitized phone number or user ID
    """
    if not phone_number:
        return "[empty]"
    
    # Handle web user IDs
    if phone_number.startswith("web-"):
        # For web users, just return the prefix and mask the IP
        return "web-***"
    
    # Remove whatsapp: prefix if present
    clean_number = phone_number.replace("whatsapp:", "")
    
    # Mask middle digits for privacy
    if len(clean_number) > 6:
        return f"{clean_number[:3]}***{clean_number[-3:]}"
    else:
        return "***"


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data for logging.
    
    Args:
        data: Dictionary containing potentially sensitive data
        
    Returns:
        Dict[str, Any]: Sanitized data dictionary
    """
    sensitive_keys = {
        'api_key', 'token', 'password', 'secret', 'auth_token',
        'openai_api_key', 'twilio_auth_token', 'authorization'
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif key_lower in {'from', 'to'} and isinstance(value, str) and 'whatsapp:' in value:
            sanitized[key] = sanitize_phone_number(value)
        else:
            sanitized[key] = value
    
    return sanitized