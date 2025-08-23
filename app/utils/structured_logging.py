"""
Enhanced structured logging utilities for better observability.

This module provides structured logging capabilities with consistent
formatting, correlation tracking, and integration with monitoring systems.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from app.utils.logging import get_correlation_id


@dataclass
class LogContext:
    """Structured log context information."""
    correlation_id: str
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None


class StructuredLogger:
    """Enhanced logger with structured output and context management."""
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        
        self._context_stack = []
    
    @contextmanager
    def context(self, **kwargs):
        """
        Context manager for adding structured context to logs.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self._context_stack.append(kwargs)
        try:
            yield
        finally:
            self._context_stack.pop()
    
    def _build_log_data(self, message: str, level: str, **kwargs) -> Dict[str, Any]:
        """Build structured log data."""
        # Start with base structure
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "correlation_id": get_correlation_id(),
            "logger": self.logger.name
        }
        
        # Add context from stack
        for context in self._context_stack:
            log_data.update(context)
        
        # Add provided kwargs
        log_data.update(kwargs)
        
        return log_data
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        if self.logger.isEnabledFor(logging.DEBUG):
            log_data = self._build_log_data(message, "DEBUG", **kwargs)
            self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        if self.logger.isEnabledFor(logging.INFO):
            log_data = self._build_log_data(message, "INFO", **kwargs)
            self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        if self.logger.isEnabledFor(logging.WARNING):
            log_data = self._build_log_data(message, "WARNING", **kwargs)
            self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        if self.logger.isEnabledFor(logging.ERROR):
            log_data = self._build_log_data(message, "ERROR", **kwargs)
            self.logger.error(json.dumps(log_data))
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        if self.logger.isEnabledFor(logging.CRITICAL):
            log_data = self._build_log_data(message, "CRITICAL", **kwargs)
            self.logger.critical(json.dumps(log_data))
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        **kwargs
    ):
        """Log HTTP request with structured data."""
        self.info(
            f"{method} {path} - {status_code}",
            request_method=method,
            request_path=path,
            response_status=status_code,
            response_time_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_service_call(
        self,
        service: str,
        operation: str,
        success: bool,
        duration: float,
        **kwargs
    ):
        """Log external service call with structured data."""
        level_method = self.info if success else self.error
        level_method(
            f"Service call: {service}.{operation} - {'success' if success else 'failed'}",
            service_name=service,
            service_operation=operation,
            call_success=success,
            call_duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        **kwargs
    ):
        """Log error with structured data and stack trace."""
        import traceback
        
        self.error(
            f"Error in {component}.{operation}: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            component=component,
            operation=operation,
            stack_trace=traceback.format_exc(),
            **kwargs
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        **kwargs
    ):
        """Log security event with structured data."""
        self.warning(
            f"Security event: {event_type}",
            security_event_type=event_type,
            security_severity=severity,
            security_description=description,
            **kwargs
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str,
        **kwargs
    ):
        """Log performance metric with structured data."""
        self.info(
            f"Performance metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs
        )


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # If the message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Create structured log entry
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)


# Global structured loggers
_structured_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        StructuredLogger instance
    """
    if name not in _structured_loggers:
        _structured_loggers[name] = StructuredLogger(name, level)
    return _structured_loggers[name]


def configure_structured_logging(level: int = logging.INFO, enable_json: bool = True):
    """
    Configure structured logging for the application.
    
    Args:
        level: Global logging level
        enable_json: Whether to enable JSON formatting
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    
    if enable_json:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('twilio').setLevel(logging.WARNING)


# Convenience functions
def log_api_request(method: str, path: str, status: int, duration: float, **kwargs):
    """Log API request with structured data."""
    logger = get_structured_logger("api")
    logger.log_request(method, path, status, duration, **kwargs)


def log_service_call(service: str, operation: str, success: bool, duration: float, **kwargs):
    """Log service call with structured data."""
    logger = get_structured_logger("services")
    logger.log_service_call(service, operation, success, duration, **kwargs)


def log_error(error: Exception, component: str, operation: str, **kwargs):
    """Log error with structured data."""
    logger = get_structured_logger("errors")
    logger.log_error(error, component, operation, **kwargs)


def log_security_event(event_type: str, severity: str, description: str, **kwargs):
    """Log security event with structured data."""
    logger = get_structured_logger("security")
    logger.log_security_event(event_type, severity, description, **kwargs)


def log_performance_metric(metric_name: str, value: Union[int, float], unit: str, **kwargs):
    """Log performance metric with structured data."""
    logger = get_structured_logger("metrics")
    logger.log_performance_metric(metric_name, value, unit, **kwargs)