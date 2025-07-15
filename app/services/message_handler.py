"""
Message handling orchestration service for the Reality Checker WhatsApp bot.

This module provides the MessageHandlerService class that coordinates the complete
analysis workflow for both text and media messages from WhatsApp users.
"""

import logging
from typing import Optional

from app.models.data_models import TwilioWebhookRequest, JobAnalysisResult, AppConfig
from app.services.pdf_processing import PDFProcessingService, PDFProcessingError
from app.services.openai_analysis import OpenAIAnalysisService
from app.services.twilio_response import TwilioResponseService


logger = logging.getLogger(__name__)


class MessageHandlerService:
    """
    Service for orchestrating the complete message processing workflow.
    
    This service coordinates between PDF processing, OpenAI analysis, and Twilio
    response services to handle both text and media messages from WhatsApp users.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the message handler service.
        
        Args:
            config: Application configuration containing API keys and settings
        """
        self.config = config
        self.pdf_service = PDFProcessingService(config)
        self.openai_service = OpenAIAnalysisService(config)
        self.twilio_service = TwilioResponseService(config)
        
    async def process_message(self, twilio_request: TwilioWebhookRequest) -> bool:
        """
        Process incoming WhatsApp message and send analysis response.
        
        Args:
            twilio_request: Validated Twilio webhook request data
            
        Returns:
            bool: True if message was processed and response sent successfully
        """
        logger.info(f"Processing message from {twilio_request.From}, "
                   f"has_media: {twilio_request.has_media}")
        
        try:
            # Determine message type and process accordingly
            if twilio_request.has_media:
                success = await self.handle_media_message(
                    twilio_request.MediaUrl0,
                    twilio_request.MediaContentType0,
                    twilio_request.From
                )
            else:
                success = await self.handle_text_message(
                    twilio_request.Body,
                    twilio_request.From
                )
            
            logger.info(f"Message processing completed. Success: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}")
            # Send generic error message to user
            return self.twilio_service.send_error_message(
                twilio_request.From, 
                "general"
            )
    
    async def handle_text_message(self, text: str, from_number: str) -> bool:
        """
        Handle text message processing with direct analysis.
        
        Args:
            text: Message text content to analyze
            from_number: Sender's WhatsApp number (format: whatsapp:+1234567890)
            
        Returns:
            bool: True if message was processed and response sent successfully
        """
        logger.info(f"Handling text message from {from_number}")
        
        try:
            # Check for help/welcome requests first (before validation)
            if self._is_help_request(text):
                logger.info(f"Sending welcome message to {from_number}")
                return self.twilio_service.send_welcome_message(from_number)
            
            # Validate text content for job analysis
            if not self._validate_text_content(text):
                logger.warning(f"Invalid text content from {from_number}")
                return self._send_content_validation_error(from_number)
            
            # Analyze job ad text
            logger.info(f"Starting OpenAI analysis for text message from {from_number}")
            analysis_result = await self.openai_service.analyze_job_ad(text)
            
            # Send analysis result back to user
            logger.info(f"Sending analysis result to {from_number}")
            return self.twilio_service.send_analysis_result(from_number, analysis_result)
            
        except ValueError as e:
            logger.error(f"Validation error processing text message: {e}")
            return self.twilio_service.send_error_message(from_number, "analysis")
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            return self.twilio_service.send_error_message(from_number, "analysis")
    
    async def handle_media_message(self, media_url: str, media_content_type: Optional[str], from_number: str) -> bool:
        """
        Handle media message processing with PDF download and extraction.
        
        Args:
            media_url: URL to download the media file from
            media_content_type: MIME type of the media file
            from_number: Sender's WhatsApp number (format: whatsapp:+1234567890)
            
        Returns:
            bool: True if message was processed and response sent successfully
        """
        logger.info(f"Handling media message from {from_number}, type: {media_content_type}")
        
        try:
            # Validate media type
            if not self._validate_media_type(media_content_type):
                logger.warning(f"Unsupported media type from {from_number}: {media_content_type}")
                return self._send_media_type_error(from_number, media_content_type)
            
            # Process PDF and extract text
            logger.info(f"Starting PDF processing for {from_number}")
            extracted_text = await self.pdf_service.process_pdf_url(media_url)
            
            # Analyze extracted text
            logger.info(f"Starting OpenAI analysis for PDF content from {from_number}")
            analysis_result = await self.openai_service.analyze_job_ad(extracted_text)
            
            # Send analysis result back to user
            logger.info(f"Sending analysis result to {from_number}")
            return self.twilio_service.send_analysis_result(from_number, analysis_result)
            
        except PDFProcessingError as e:
            logger.error(f"PDF processing error: {e}")
            return self.twilio_service.send_error_message(from_number, "pdf_processing")
            
        except ValueError as e:
            logger.error(f"Validation error processing media message: {e}")
            return self.twilio_service.send_error_message(from_number, "analysis")
            
        except Exception as e:
            logger.error(f"Error processing media message: {e}")
            return self.twilio_service.send_error_message(from_number, "analysis")
    
    def _validate_text_content(self, text: str) -> bool:
        """
        Validate text message content for analysis.
        
        Args:
            text: Text content to validate
            
        Returns:
            bool: True if content is valid for analysis
        """
        if not text or not text.strip():
            logger.debug("Text content is empty")
            return False
        
        # Check minimum length for meaningful job ad analysis
        min_length = 20
        if len(text.strip()) < min_length:
            logger.debug(f"Text too short: {len(text.strip())} chars (min: {min_length})")
            return False
        
        # Check maximum length to prevent abuse
        max_length = 10000  # 10k characters should be sufficient for job ads
        if len(text.strip()) > max_length:
            logger.debug(f"Text too long: {len(text.strip())} chars (max: {max_length})")
            return False
        
        return True
    
    def _validate_media_type(self, media_content_type: Optional[str]) -> bool:
        """
        Validate media content type for processing.
        
        Args:
            media_content_type: MIME type of the media file
            
        Returns:
            bool: True if media type is supported
        """
        if not media_content_type:
            logger.debug("No media content type provided")
            return False
        
        # Only support PDF files for now
        supported_types = [
            'application/pdf',
            'application/x-pdf',
            'application/acrobat',
            'applications/vnd.pdf',
            'text/pdf',
            'text/x-pdf'
        ]
        
        media_type_lower = media_content_type.lower()
        is_supported = any(supported_type in media_type_lower for supported_type in supported_types)
        
        if not is_supported:
            logger.debug(f"Unsupported media type: {media_content_type}")
        
        return is_supported
    
    def _is_help_request(self, text: str) -> bool:
        """
        Check if the text message is a help/welcome request.
        
        Args:
            text: Text content to check
            
        Returns:
            bool: True if this is a help request
        """
        help_keywords = ['help', 'start', 'hello', 'hi', 'how', 'what', 'info', 'about']
        text_lower = text.lower().strip()
        
        # Check for exact matches or short messages with help keywords
        if text_lower in help_keywords:
            return True
        
        # Check for help requests in short messages
        if len(text_lower) < 50:
            return any(keyword in text_lower for keyword in help_keywords)
        
        return False
    
    def _send_content_validation_error(self, from_number: str) -> bool:
        """
        Send content validation error message to user.
        
        Args:
            from_number: Recipient's WhatsApp number
            
        Returns:
            bool: True if message sent successfully
        """
        error_message = (
            "❌ *Content Too Short*\n\n"
            "Please send more detailed job information for analysis. "
            "Include details like:\n"
            "• Job title and description\n"
            "• Company name\n"
            "• Salary/compensation\n"
            "• Requirements and responsibilities\n\n"
            "Or send 'help' for more information."
        )
        
        try:
            message = self.twilio_service.client.messages.create(
                body=error_message,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=from_number
            )
            logger.info(f"Content validation error sent. Message SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send content validation error: {e}")
            return False
    
    def _send_media_type_error(self, from_number: str, media_type: Optional[str]) -> bool:
        """
        Send media type error message to user.
        
        Args:
            from_number: Recipient's WhatsApp number
            media_type: The unsupported media type
            
        Returns:
            bool: True if message sent successfully
        """
        error_message = (
            "❌ *Unsupported File Type*\n\n"
            f"I can only process PDF files, but you sent: {media_type or 'unknown type'}\n\n"
            "Please:\n"
            "• Send the job posting as a PDF file\n"
            "• Or copy and paste the job details as text\n\n"
            "Send 'help' for more information."
        )
        
        try:
            message = self.twilio_service.client.messages.create(
                body=error_message,
                from_=f"whatsapp:{self.config.twilio_phone_number}",
                to=from_number
            )
            logger.info(f"Media type error sent. Message SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send media type error: {e}")
            return False