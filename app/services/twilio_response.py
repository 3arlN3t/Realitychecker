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
        
        try:
            message_body = self._format_analysis_message(result)
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Analysis result sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                trust_score=result.trust_score,
                classification=result.classification_text,
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send analysis result",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
                error_type="TwilioException",
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending analysis result",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
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
        
        try:
            message_body = self._get_error_message(error_type)
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Error message sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send error message",
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                error=str(e),
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending error message",
                to_number=sanitize_phone_number(to_number),
                error_type=error_type,
                error=str(e),
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
        
        try:
            message_body = self._get_welcome_message()
            
            message = self.client.messages.create(
                body=message_body,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=to_number
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Welcome message sent successfully",
                message_sid=message.sid,
                to_number=sanitize_phone_number(to_number),
                correlation_id=correlation_id
            )
            return True
            
        except TwilioException as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send welcome message",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
                error_type="TwilioException",
                correlation_id=correlation_id
            )
            return False
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error sending welcome message",
                to_number=sanitize_phone_number(to_number),
                error=str(e),
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