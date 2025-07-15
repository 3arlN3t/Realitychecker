"""
Comprehensive error handling utilities for the Reality Checker application.

This module provides centralized error handling, user-friendly error messages,
and fallback responses for external service failures.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.utils.logging import get_logger, log_with_context


logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur in the application."""
    
    VALIDATION = "validation"
    PDF_PROCESSING = "pdf_processing"
    OPENAI_SERVICE = "openai_service"
    TWILIO_SERVICE = "twilio_service"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """Information about an error for logging and response generation."""
    
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    should_retry: bool = False
    retry_delay_seconds: Optional[int] = None
    fallback_available: bool = False


class ErrorHandler:
    """Centralized error handler for the application."""
    
    def __init__(self):
        """Initialize the error handler with predefined error mappings."""
        self._error_mappings = self._build_error_mappings()
    
    def _build_error_mappings(self) -> Dict[str, ErrorInfo]:
        """Build mappings from error patterns to ErrorInfo objects."""
        return {
            # PDF Processing Errors
            "pdf_download_failed": ErrorInfo(
                category=ErrorCategory.PDF_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "❌ *PDF Download Failed*\n\n"
                    "I couldn't download your PDF file. This might be due to:\n"
                    "• Network connectivity issues\n"
                    "• File access restrictions\n"
                    "• Temporary server problems\n\n"
                    "Please try again or send the job details as text instead."
                ),
                technical_message="Failed to download PDF from media URL",
                should_retry=True,
                retry_delay_seconds=30
            ),
            
            "pdf_too_large": ErrorInfo(
                category=ErrorCategory.PDF_PROCESSING,
                severity=ErrorSeverity.LOW,
                user_message=(
                    "❌ *PDF File Too Large*\n\n"
                    "Your PDF file is too large to process (max 10MB).\n\n"
                    "Please:\n"
                    "• Send a smaller PDF file\n"
                    "• Copy and paste the job details as text\n"
                    "• Split large documents into smaller sections"
                ),
                technical_message="PDF file exceeds maximum size limit",
                should_retry=False
            ),
            
            "pdf_extraction_failed": ErrorInfo(
                category=ErrorCategory.PDF_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "❌ *PDF Processing Error*\n\n"
                    "I couldn't extract text from your PDF. This might be because:\n"
                    "• The PDF is password-protected\n"
                    "• The PDF contains only images\n"
                    "• The file is corrupted\n\n"
                    "Please try sending the job details as text instead."
                ),
                technical_message="Failed to extract text content from PDF",
                should_retry=False
            ),
            
            "pdf_no_content": ErrorInfo(
                category=ErrorCategory.PDF_PROCESSING,
                severity=ErrorSeverity.LOW,
                user_message=(
                    "❌ *No Text Found*\n\n"
                    "Your PDF doesn't contain readable text for analysis.\n\n"
                    "Please:\n"
                    "• Send a PDF with text content\n"
                    "• Copy and paste the job details as text\n"
                    "• Check if the PDF is image-based"
                ),
                technical_message="PDF contains no extractable text content",
                should_retry=False
            ),
            
            # OpenAI Service Errors
            "openai_timeout": ErrorInfo(
                category=ErrorCategory.OPENAI_SERVICE,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "⏱️ *Analysis Timeout*\n\n"
                    "The analysis is taking longer than expected.\n\n"
                    "Please try again in a few moments. If the problem persists, "
                    "try sending a shorter job description."
                ),
                technical_message="OpenAI API request timed out",
                should_retry=True,
                retry_delay_seconds=60
            ),
            
            "openai_rate_limit": ErrorInfo(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "🚦 *Service Busy*\n\n"
                    "I'm currently handling many requests.\n\n"
                    "Please wait a few minutes and try again. "
                    "Thank you for your patience!"
                ),
                technical_message="OpenAI API rate limit exceeded",
                should_retry=True,
                retry_delay_seconds=300
            ),
            
            "openai_api_error": ErrorInfo(
                category=ErrorCategory.OPENAI_SERVICE,
                severity=ErrorSeverity.HIGH,
                user_message=(
                    "🔧 *Analysis Service Unavailable*\n\n"
                    "The job analysis service is temporarily unavailable.\n\n"
                    "Please try again later. If the problem persists, "
                    "contact support for assistance."
                ),
                technical_message="OpenAI API returned an error",
                should_retry=True,
                retry_delay_seconds=120,
                fallback_available=True
            ),
            
            "openai_invalid_response": ErrorInfo(
                category=ErrorCategory.OPENAI_SERVICE,
                severity=ErrorSeverity.HIGH,
                user_message=(
                    "🤖 *Analysis Error*\n\n"
                    "I received an unexpected response while analyzing your job posting.\n\n"
                    "Please try again. If the issue continues, "
                    "try rephrasing your job description."
                ),
                technical_message="OpenAI API returned invalid or unparseable response",
                should_retry=True,
                retry_delay_seconds=30
            ),
            
            # Twilio Service Errors
            "twilio_send_failed": ErrorInfo(
                category=ErrorCategory.TWILIO_SERVICE,
                severity=ErrorSeverity.HIGH,
                user_message=(
                    "📱 *Message Delivery Failed*\n\n"
                    "I couldn't send the analysis results to you.\n\n"
                    "This might be a temporary issue. Please try sending "
                    "your request again."
                ),
                technical_message="Failed to send WhatsApp message via Twilio",
                should_retry=True,
                retry_delay_seconds=60
            ),
            
            "twilio_auth_failed": ErrorInfo(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.CRITICAL,
                user_message=(
                    "🔐 *Service Authentication Error*\n\n"
                    "There's a configuration issue with the messaging service.\n\n"
                    "Please contact support for assistance."
                ),
                technical_message="Twilio authentication failed",
                should_retry=False
            ),
            
            # Network Errors
            "network_timeout": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "🌐 *Network Timeout*\n\n"
                    "The request timed out due to network issues.\n\n"
                    "Please check your connection and try again."
                ),
                technical_message="Network request timed out",
                should_retry=True,
                retry_delay_seconds=30
            ),
            
            "network_error": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                user_message=(
                    "🌐 *Network Error*\n\n"
                    "There was a network connectivity issue.\n\n"
                    "Please try again in a few moments."
                ),
                technical_message="Network connectivity error",
                should_retry=True,
                retry_delay_seconds=60
            ),
            
            # Validation Errors
            "content_too_short": ErrorInfo(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                user_message=(
                    "📝 *Content Too Short*\n\n"
                    "Please provide more detailed job information for analysis.\n\n"
                    "Include details like:\n"
                    "• Job title and description\n"
                    "• Company name\n"
                    "• Salary/compensation\n"
                    "• Requirements and responsibilities"
                ),
                technical_message="Job content is too short for meaningful analysis",
                should_retry=False
            ),
            
            "unsupported_media": ErrorInfo(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                user_message=(
                    "📎 *Unsupported File Type*\n\n"
                    "I can only process PDF files.\n\n"
                    "Please:\n"
                    "• Send the job posting as a PDF file\n"
                    "• Or copy and paste the job details as text"
                ),
                technical_message="Unsupported media type received",
                should_retry=False
            ),
            
            # System Errors
            "system_error": ErrorInfo(
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message=(
                    "⚠️ *System Error*\n\n"
                    "An unexpected error occurred while processing your request.\n\n"
                    "Please try again. If the problem persists, "
                    "contact support for assistance."
                ),
                technical_message="Unexpected system error",
                should_retry=True,
                retry_delay_seconds=120
            ),
            
            "configuration_error": ErrorInfo(
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.CRITICAL,
                user_message=(
                    "⚙️ *Service Configuration Error*\n\n"
                    "There's a configuration issue with the service.\n\n"
                    "Please contact support for assistance."
                ),
                technical_message="Application configuration error",
                should_retry=False
            )
        }
    
    def get_error_info(self, error_key: str) -> ErrorInfo:
        """
        Get error information for a specific error key.
        
        Args:
            error_key: Key identifying the type of error
            
        Returns:
            ErrorInfo: Information about the error
        """
        return self._error_mappings.get(error_key, self._error_mappings["system_error"])
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Tuple[str, ErrorInfo]:
        """
        Handle an error and return appropriate user message and error info.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            correlation_id: Correlation ID for tracking
            
        Returns:
            Tuple[str, ErrorInfo]: User message and error information
        """
        error_key = self._classify_error(error)
        error_info = self.get_error_info(error_key)
        
        # Log the error with context
        log_context = {
            "error_category": error_info.category.value,
            "error_severity": error_info.severity.value,
            "error_key": error_key,
            "should_retry": error_info.should_retry,
            "correlation_id": correlation_id
        }
        
        if context:
            log_context.update(context)
        
        log_with_context(
            logger,
            logging.ERROR if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else logging.WARNING,
            f"{error_info.technical_message}: {str(error)}",
            **log_context
        )
        
        return error_info.user_message, error_info
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify an error to determine the appropriate error key.
        
        Args:
            error: The exception to classify
            
        Returns:
            str: Error key for looking up error information
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # PDF Processing Errors
        if "pdf" in error_str:
            if "download" in error_str or "fetch" in error_str:
                return "pdf_download_failed"
            elif "too large" in error_str or "size" in error_str:
                return "pdf_too_large"
            elif "no content" in error_str or "no extractable" in error_str or "empty" in error_str:
                return "pdf_no_content"
            elif "extract" in error_str or "text" in error_str:
                return "pdf_extraction_failed"
            else:
                return "pdf_extraction_failed"
        
        # OpenAI Errors
        if "openai" in error_str or "gpt" in error_str:
            if "timeout" in error_str or "timed out" in error_str:
                return "openai_timeout"
            elif "rate limit" in error_str or "quota" in error_str:
                return "openai_rate_limit"
            elif "invalid" in error_str or "parse" in error_str:
                return "openai_invalid_response"
            else:
                return "openai_api_error"
        
        # Twilio Errors
        if "twilio" in error_str or "whatsapp" in error_str:
            if "auth" in error_str or "unauthorized" in error_str:
                return "twilio_auth_failed"
            else:
                return "twilio_send_failed"
        
        # Network Errors
        if any(keyword in error_str for keyword in ["timeout", "connection", "network", "dns"]):
            if "timeout" in error_str:
                return "network_timeout"
            else:
                return "network_error"
        
        # Validation Errors
        if any(keyword in error_str for keyword in ["too short", "short for", "validation", "invalid"]):
            if "short" in error_str or "length" in error_str:
                return "content_too_short"
            elif "media" in error_str or "file" in error_str:
                return "unsupported_media"
            else:
                return "content_too_short"
        
        # Media type errors
        if "unsupported" in error_str and ("media" in error_str or "file" in error_str):
            return "unsupported_media"
        
        # Configuration Errors
        if any(keyword in error_str for keyword in ["config", "environment", "missing", "required"]):
            return "configuration_error"
        
        # Default to system error
        return "system_error"
    
    def get_fallback_response(self, error_category: ErrorCategory) -> Optional[str]:
        """
        Get a fallback response when external services are unavailable.
        
        Args:
            error_category: Category of error that occurred
            
        Returns:
            Optional[str]: Fallback response message, if available
        """
        fallback_responses = {
            ErrorCategory.OPENAI_SERVICE: (
                "🤖 *Basic Analysis Available*\n\n"
                "While our AI analysis is temporarily unavailable, "
                "here are some general tips for identifying job scams:\n\n"
                "🚩 *Red Flags:*\n"
                "• Requests for upfront payments\n"
                "• Unrealistic salary promises\n"
                "• Poor grammar/spelling\n"
                "• Vague job descriptions\n"
                "• Pressure to act quickly\n\n"
                "✅ *Good Signs:*\n"
                "• Verifiable company information\n"
                "• Realistic salary ranges\n"
                "• Clear job requirements\n"
                "• Professional communication\n\n"
                "Please try again later for detailed AI analysis."
            )
        }
        
        return fallback_responses.get(error_category)


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> Tuple[str, ErrorInfo]:
    """
    Handle an error using the global error handler.
    
    Args:
        error: The exception that occurred
        context: Additional context about the error
        correlation_id: Correlation ID for tracking
        
    Returns:
        Tuple[str, ErrorInfo]: User message and error information
    """
    return error_handler.handle_error(error, context, correlation_id)


def get_fallback_response(error_category: ErrorCategory) -> Optional[str]:
    """
    Get a fallback response for the given error category.
    
    Args:
        error_category: Category of error that occurred
        
    Returns:
        Optional[str]: Fallback response message, if available
    """
    return error_handler.get_fallback_response(error_category)