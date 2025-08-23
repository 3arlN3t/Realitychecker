"""
Twilio response service for sending WhatsApp messages.

This module handles sending formatted responses back to users via Twilio's
WhatsApp API, including analysis results and error messages.
"""

import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from app.models.data_models import JobAnalysisResult, AppConfig
from app.config import get_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context, sanitize_phone_number
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker, AlertSeverity

logger = get_logger(__name__)


class TwilioResponseService:
    """Service for sending WhatsApp messages via Twilio."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the Twilio response service.
        
        Args:
            config: Application configuration. If None, loads from environment.
        """
        self.config = config or get_config()
        self.client = Client(
            self.config.twilio_account_sid,
            self.config.twilio_auth_token
        )
    
    def send_analysis_result(self, to_number: str, result: JobAnalysisResult) -> bool:
        """
        Send job analysis result to user via WhatsApp.
        
        Args:
            to_number: Recipient's WhatsApp number (format: whatsapp:+1234567890)
            result: Analysis result containing trust score and classification
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        import time
        start_time = time.time()
        
        try:
            message_body = self._format_analysis_message(result)
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_message", True, duration)
            error_tracker.track_service_call("twilio", "send_message", True, duration)
            
            log_with_context(
                logger,
                logging.INFO,
                "Analysis result sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                trust_score=result.trust_score,
                classification=result.classification_text,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_message", False, duration)
            error_tracker.track_service_call("twilio", "send_message", False, duration)
            error_tracker.track_error(
                "TwilioException",
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_analysis_result", "duration": duration},
                severity=AlertSeverity.HIGH
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send analysis result",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
                error_type="TwilioException",
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_message", False, duration)
            error_tracker.track_service_call("twilio", "send_message", False, duration)
            error_tracker.track_error(
                type(e).__name__,
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_analysis_result", "duration": duration},
                severity=AlertSeverity.HIGH
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending analysis result",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
    
    def send_error_message(self, to_number: str, error_type: str = "general") -> bool:
        """
        Send error message to user via WhatsApp.
        
        Args:
            to_number: Recipient's WhatsApp number (format: whatsapp:+1234567890)
            error_type: Type of error ("pdf_processing", "analysis", "general")
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        import time
        start_time = time.time()
        
        try:
            message_body = self._get_error_message(error_type)
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_error_message", True, duration)
            error_tracker.track_service_call("twilio", "send_error_message", True, duration)
            
            log_with_context(
                logger,
                logging.INFO,
                "Error message sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_error_message", False, duration)
            error_tracker.track_service_call("twilio", "send_error_message", False, duration)
            error_tracker.track_error(
                "TwilioException",
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_error_message", "error_type": error_type, "duration": duration},
                severity=AlertSeverity.MEDIUM
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send error message",
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_error_message", False, duration)
            error_tracker.track_service_call("twilio", "send_error_message", False, duration)
            error_tracker.track_error(
                type(e).__name__,
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_error_message", "error_type": error_type, "duration": duration},
                severity=AlertSeverity.MEDIUM
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending error message",
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
    
    def send_welcome_message(self, to_number: str) -> bool:
        """
        Send welcome/help message to user via WhatsApp.
        
        Args:
            to_number: Recipient's WhatsApp number (format: whatsapp:+1234567890)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        import time
        start_time = time.time()
        
        try:
            message_body = self._get_welcome_message()
            
            # Debug logging
            logger.info(f"Sending welcome message to {sanitize_phone_number(to_number)}")
            logger.info(f"Using Twilio phone number: {self.config.twilio_phone_number}")
            logger.info(f"Using Twilio account SID: {self.config.twilio_account_sid[:5]}...")
            
            # Check if to_number already has whatsapp: prefix
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
                logger.info(f"Added whatsapp: prefix to number: {sanitize_phone_number(to_number)}")
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_welcome_message", True, duration)
            error_tracker.track_service_call("twilio", "send_welcome_message", True, duration)
            
            log_with_context(
                logger,
                logging.INFO,
                "Welcome message sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_welcome_message", False, duration)
            error_tracker.track_service_call("twilio", "send_welcome_message", False, duration)
            error_tracker.track_error(
                "TwilioException",
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_welcome_message", "duration": duration},
                severity=AlertSeverity.MEDIUM
            )
            
            # Get more detailed error information
            error_code = getattr(e, 'code', 'unknown')
            error_status = getattr(e, 'status', 'unknown')
            error_msg = str(e)
            error_details = {}
            
            # Try to extract more details from the exception
            if hasattr(e, 'msg'):
                error_details['msg'] = e.msg
            if hasattr(e, 'uri'):
                error_details['uri'] = e.uri
            if hasattr(e, 'details'):
                error_details['details'] = e.details
            if hasattr(e, 'more_info'):
                error_details['more_info'] = e.more_info
            
            # Print the full exception for debugging
            import traceback
            logger.error(f"Twilio Exception: {error_msg}")
            logger.error(f"Twilio Exception Code: {error_code}")
            logger.error(f"Twilio Exception Status: {error_status}")
            logger.error(f"Twilio Exception Details: {error_details}")
            logger.error(f"Twilio Exception Traceback: {traceback.format_exc()}")
            
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send welcome message",
                to_number=sanitize_phone_number(to_number),
                error=error_msg,
                error_code=error_code,
                error_status=error_status,
                error_details=error_details,
                error_type="TwilioException",
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_service_call("twilio", "send_welcome_message", False, duration)
            error_tracker.track_service_call("twilio", "send_welcome_message", False, duration)
            error_tracker.track_error(
                type(e).__name__,
                str(e),
                "twilio_service",
                correlation_id,
                {"operation": "send_welcome_message", "duration": duration},
                severity=AlertSeverity.MEDIUM
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending welcome message",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            return False
    
    def _format_analysis_message(self, result: JobAnalysisResult) -> str:
        """
        Format analysis result into a user-friendly message.
        
        Args:
            result: Analysis result to format
            
        Returns:
            str: Formatted message string
        """
        # Determine emoji based on classification
        emoji_map = {
            "Legit": "✅",
            "Suspicious": "⚠️", 
            "Likely Scam": "🚨"
        }
        
        emoji = emoji_map.get(result.classification_text, "❓")
        
        message = f"{emoji} *Job Analysis Result*\n\n"
        message += f"*Trust Score:* {result.trust_score}/100\n"
        message += f"*Classification:* {result.classification_text}\n\n"
        message += "*Key Findings:*\n"
        
        for i, reason in enumerate(result.reasons, 1):
            message += f"{i}. {reason}\n"
        
        message += f"\n*Confidence:* {result.confidence:.1%}\n\n"
        
        # Add recommendation based on classification
        if result.classification_text == "Legit":
            message += "💡 This job appears legitimate, but always verify details independently."
        elif result.classification_text == "Suspicious":
            message += "💡 Exercise caution. Research the company and verify all details before proceeding."
        else:  # Likely Scam
            message += "💡 Strong indicators suggest this may be a scam. Avoid sharing personal information."
        
        return message
    
    def _get_error_message(self, error_type: str) -> str:
        """
        Get appropriate error message based on error type.
        
        Args:
            error_type: Type of error that occurred
            
        Returns:
            str: Error message string
        """
        error_messages = {
            "pdf_processing": (
                "❌ *PDF Processing Error*\n\n"
                "I couldn't process your PDF file. Please ensure:\n"
                "• The file is a valid PDF\n"
                "• The file size is under 10MB\n"
                "• The PDF contains readable text\n\n"
                "Try sending the job details as text instead."
            ),
            "analysis": (
                "❌ *Analysis Error*\n\n"
                "I encountered an issue analyzing the job posting. "
                "This might be due to:\n"
                "• Insufficient job details\n"
                "• Temporary service issues\n\n"
                "Please try again or send more detailed job information."
            ),
            "general": (
                "❌ *Service Error*\n\n"
                "I'm experiencing technical difficulties. "
                "Please try again in a few moments.\n\n"
                "If the problem persists, send 'help' for assistance."
            )
        }
        
        return error_messages.get(error_type, error_messages["general"])
    
    def _get_welcome_message(self) -> str:
        """
        Get welcome/help message for users.
        
        Returns:
            str: Welcome message string
        """
        return (
            "👋 *Welcome to Reality Checker!*\n\n"
            "I help you identify potential job scams by analyzing job postings.\n\n"
            "*How to use:*\n"
            "• Send me job details as text\n"
            "• Or attach a PDF with the job posting\n\n"
            "I'll analyze the posting and provide:\n"
            "✅ Trust score (0-100)\n"
            "✅ Risk classification\n"
            "✅ Key warning signs or positive indicators\n\n"
            "*Stay safe!* Always verify job details independently."
        )
    
    async def health_check(self) -> dict:
        """
        Check the health of the Twilio service.
        
        Returns:
            dict: Health status information
        """
        try:
            # Check if required configuration is present
            if not self.config.twilio_account_sid or self.config.twilio_account_sid == "AC":
                return {
                    "status": "unhealthy",
                    "service": "twilio",
                    "account_sid": self.config.twilio_account_sid,
                    "auth_token_configured": False,
                    "from_number": self.config.twilio_phone_number,
                    "error": "Twilio Account SID not configured"
                }
            
            if not self.config.twilio_auth_token:
                return {
                    "status": "unhealthy",
                    "service": "twilio",
                    "account_sid": self.config.twilio_account_sid,
                    "auth_token_configured": False,
                    "from_number": self.config.twilio_phone_number,
                    "error": "Twilio Auth Token not configured"
                }
            
            if not self.config.twilio_phone_number:
                return {
                    "status": "unhealthy",
                    "service": "twilio",
                    "account_sid": self.config.twilio_account_sid,
                    "auth_token_configured": True,
                    "from_number": self.config.twilio_phone_number,
                    "error": "Twilio from number not configured"
                }
            
            # For now, just check configuration without making API calls
            # API calls will be tested during actual usage
            return {
                "status": "healthy",
                "service": "twilio",
                "account_sid": self.config.twilio_account_sid,
                "auth_token_configured": True,
                "from_number": self.config.twilio_phone_number,
                "note": "Configuration validated, API calls will be tested during usage"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "twilio",
                "account_sid": self.config.twilio_account_sid,
                "auth_token_configured": bool(self.config.twilio_auth_token),
                "from_number": self.config.twilio_phone_number,
                "error": str(e)
            }
    
    async def cleanup(self):
        """
        Clean up resources used by the Twilio service.
        
        This method handles graceful cleanup of any resources, connections,
        or background tasks used by the service.
        """
        correlation_id = get_correlation_id()
        
        try:
            log_with_context(
                logger,
                logging.INFO,
                "Cleaning up Twilio service resources",
                correlation_id=correlation_id
            )
            
            # Close any HTTP connections that might be held by the Twilio client
            if hasattr(self.client, '_http_client') and self.client._http_client:
                try:
                    # The Twilio client uses httpx internally, close it if possible
                    if hasattr(self.client._http_client, 'close'):
                        await self.client._http_client.close()
                except Exception as e:
                    logger.warning(f"Could not close Twilio HTTP client: {e}")
            
            # Clear any cached data or references
            self.client = None
            
            log_with_context(
                logger,
                logging.INFO,
                "Twilio service cleanup completed successfully",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Error during Twilio service cleanup",
                error=str(e),
                correlation_id=correlation_id
            )