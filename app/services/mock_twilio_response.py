"""
Mock Twilio response service for development and testing.

This service simulates Twilio responses without actually sending messages,
useful for testing the bot logic without needing a real WhatsApp setup.
"""

import logging
from typing import Optional
from app.models.data_models import JobAnalysisResult, AppConfig
from app.utils.logging import get_logger, get_correlation_id, log_with_context

logger = get_logger(__name__)


class MockTwilioResponseService:
    """Mock service that simulates Twilio responses for development."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the mock Twilio response service."""
        self.config = config
        self.sent_messages = []  # Store messages for testing
        
    def send_analysis_result(self, to_number: str, result: JobAnalysisResult) -> bool:
        """
        Mock sending job analysis result to user.
        
        Args:
            to_number: Recipient's WhatsApp number
            result: Analysis result containing trust score and classification
            
        Returns:
            bool: Always True for mock service
        """
        correlation_id = get_correlation_id()
        
        message_body = self._format_analysis_message(result)
        
        # Store the message for testing/debugging
        self.sent_messages.append({
            "to": to_number,
            "type": "analysis_result",
            "body": message_body,
            "result": result,
            "timestamp": correlation_id
        })
        
        log_with_context(
            logger,
            logging.INFO,
            "MOCK: Analysis result would be sent",
            to_number=to_number[-4:] + "****",  # Mask phone number
            trust_score=result.trust_score,
            classification=result.classification_text,
            correlation_id=correlation_id
        )
        
        # Print the message that would be sent
        print(f"\n📱 MOCK WhatsApp Message to {to_number[-4:]}****:")
        print("=" * 50)
        print(message_body)
        print("=" * 50)
        
        return True
        
    def send_error_message(self, to_number: str, error_type: str = "general") -> bool:
        """
        Mock sending error message to user.
        
        Args:
            to_number: Recipient's WhatsApp number
            error_type: Type of error
            
        Returns:
            bool: Always True for mock service
        """
        correlation_id = get_correlation_id()
        
        message_body = self._get_error_message(error_type)
        
        self.sent_messages.append({
            "to": to_number,
            "type": "error",
            "body": message_body,
            "error_type": error_type,
            "timestamp": correlation_id
        })
        
        log_with_context(
            logger,
            logging.INFO,
            "MOCK: Error message would be sent",
            to_number=to_number[-4:] + "****",
            error_type=error_type,
            correlation_id=correlation_id
        )
        
        print(f"\n📱 MOCK WhatsApp Error Message to {to_number[-4:]}****:")
        print("=" * 50)
        print(message_body)
        print("=" * 50)
        
        return True
    
    def send_welcome_message(self, to_number: str) -> bool:
        """
        Mock sending welcome message to user.
        
        Args:
            to_number: Recipient's WhatsApp number
            
        Returns:
            bool: Always True for mock service
        """
        correlation_id = get_correlation_id()
        
        message_body = self._get_welcome_message()
        
        self.sent_messages.append({
            "to": to_number,
            "type": "welcome",
            "body": message_body,
            "timestamp": correlation_id
        })
        
        log_with_context(
            logger,
            logging.INFO,
            "MOCK: Welcome message would be sent",
            to_number=to_number[-4:] + "****",
            correlation_id=correlation_id
        )
        
        print(f"\n📱 MOCK WhatsApp Welcome Message to {to_number[-4:]}****:")
        print("=" * 50)
        print(message_body)
        print("=" * 50)
        
        return True
    
    def _format_analysis_message(self, result: JobAnalysisResult) -> str:
        """Format analysis result into a user-friendly message."""
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
        
        if result.classification_text == "Legit":
            message += "💡 This job appears legitimate, but always verify details independently."
        elif result.classification_text == "Suspicious":
            message += "💡 Exercise caution. Research the company and verify all details before proceeding."
        else:
            message += "💡 Strong indicators suggest this may be a scam. Avoid sharing personal information."
        
        return message
    
    def _get_error_message(self, error_type: str) -> str:
        """Get appropriate error message based on error type."""
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
        """Get welcome/help message for users."""
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
        """Mock health check that always returns healthy."""
        return {
            "status": "healthy",
            "service": "mock_twilio",
            "note": "Mock service for development - always returns success"
        }
    
    def get_sent_messages(self) -> list:
        """Get all messages that would have been sent (for testing)."""
        return self.sent_messages
    
    def clear_sent_messages(self):
        """Clear the sent messages list."""
        self.sent_messages.clear()