
"""
Message handling orchestration service for the Reality Checker WhatsApp bot.

This module provides the MessageHandlerService class that coordinates the complete
analysis workflow for both text and media messages from WhatsApp users.
"""

import logging
import asyncio
from typing import Optional

from app.models.data_models import TwilioWebhookRequest, JobAnalysisResult, AppConfig, AnalysisResult, MessageType
from app.services.pdf_processing import (
    PDFProcessingService, PDFProcessingError, PDFDownloadError, 
    PDFExtractionError, PDFValidationError
)
from app.services.enhanced_ai_analysis import EnhancedAIAnalysisService
from app.services.twilio_response import TwilioResponseService
from app.services.user_management import UserManagementService
from app.utils.logging import get_logger, get_correlation_id, log_with_context, sanitize_phone_number
from app.utils.error_handling import handle_error, get_fallback_response, ErrorCategory
import time


logger = get_logger(__name__)


class MessageHandlerService:
    """
    Service for orchestrating the complete message processing workflow.
    
    This service coordinates between PDF processing, OpenAI analysis, and Twilio
    response services to handle both text and media messages from WhatsApp users.
    """
    
    def __init__(self, config: AppConfig, twilio_service=None, pdf_service=None, openai_service=None, user_service=None):
        """
        Initialize the message handler service.
        
        Args:
            config: Application configuration containing API keys and settings
            twilio_service: Optional Twilio service instance (for dependency injection)
            pdf_service: Optional PDF service instance (for dependency injection)
            openai_service: Optional OpenAI service instance (for dependency injection)
            user_service: Optional user management service instance (for dependency injection)
        """
        self.config = config
        self.pdf_service = pdf_service or PDFProcessingService(config)
        self.openai_service = openai_service or EnhancedAIAnalysisService(config)
        self.twilio_service = twilio_service or TwilioResponseService(config)
        self.user_service = user_service or UserManagementService(config)
        
    async def process_message(self, twilio_request: TwilioWebhookRequest) -> bool:
        """
        Process incoming WhatsApp message and send analysis response.
        
        Args:
            twilio_request: Validated Twilio webhook request data
            
        Returns:
            bool: True if message was processed and response sent successfully
        """
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Processing message",
            from_number=sanitize_phone_number(twilio_request.From),
            has_media=twilio_request.has_media,
            message_sid=twilio_request.MessageSid,
            correlation_id=correlation_id
        )
        
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
            
            log_with_context(
                logger,
                logging.INFO,
                "Message processing completed",
                success=success,
                message_sid=twilio_request.MessageSid,
                correlation_id=correlation_id
            )
            return success
            
        except Exception as e:
            # Use centralized error handling
            user_message, error_info = handle_error(
                e,
                {
                    "from_number": sanitize_phone_number(twilio_request.From),
                    "message_sid": twilio_request.MessageSid,
                    "has_media": twilio_request.has_media,
                    "component": "message_processing"
                },
                correlation_id
            )
            
            # Try to send error message to user
            try:
                return await self._send_error_with_fallback(twilio_request.From, error_info)
            except Exception as fallback_error:
                log_with_context(
                    logger,
                    logging.CRITICAL,
                    "Failed to send error message to user",
                    original_error=str(e),
                    fallback_error=str(fallback_error),
                    from_number=sanitize_phone_number(twilio_request.From),
                    correlation_id=correlation_id
                )
                return False
    
    async def handle_text_message(self, text: str, from_number: str) -> bool:
        """
        Handle text message processing with direct analysis.
        
        Args:
            text: Message text content to analyze
            from_number: Sender's WhatsApp number (format: whatsapp:+1234567890)
            
        Returns:
            bool: True if message was processed and response sent successfully
        """
        correlation_id = get_correlation_id()
        start_time = time.time()
        analysis_result = None
        error_message = None
        
        log_with_context(
            logger,
            logging.INFO,
            "Handling text message",
            from_number=sanitize_phone_number(from_number),
            text_length=len(text) if text else 0,
            correlation_id=correlation_id
        )
        
        try:
            # Check if user is blocked (with timeout)
            try:
                is_blocked = await asyncio.wait_for(
                    self.user_service.is_user_blocked(from_number),
                    timeout=1.0  # 1 second timeout for user blocking check
                )
                if is_blocked:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Blocked user attempted to send message",
                        from_number=sanitize_phone_number(from_number),
                        correlation_id=correlation_id
                    )
                    return True  # Silently ignore blocked users
            except asyncio.TimeoutError:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "User blocking check timed out, proceeding with analysis",
                    from_number=sanitize_phone_number(from_number),
                    correlation_id=correlation_id
                )
                # Continue processing if blocking check times out
            
            # Check for help/welcome requests first (before validation)
            if self._is_help_request(text):
                log_with_context(
                    logger,
                    logging.INFO,
                    "Sending welcome message",
                    from_number=sanitize_phone_number(from_number),
                    correlation_id=correlation_id
                )
                success = await asyncio.wait_for(
                self.twilio_service.send_welcome_message(from_number),
                timeout=5.0  # 5 second timeout for Twilio API
            )
                
                # Record help interaction (non-blocking)
                response_time = time.time() - start_time
                asyncio.create_task(self._record_interaction_safe(
                    phone_number=from_number,
                    message_type="text",
                    message_content="help request",
                    response_time=response_time
                ))
                
                return success
            
            # Validate text content for job analysis
            if not self._validate_text_content(text):
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Invalid text content",
                    from_number=sanitize_phone_number(from_number),
                    text_length=len(text) if text else 0,
                    correlation_id=correlation_id
                )
                
                error_message = "Content validation failed"
                success = await self._send_content_validation_error(from_number)
                
                # Record validation error interaction (non-blocking)
                response_time = time.time() - start_time
                asyncio.create_task(self._record_interaction_safe(
                    phone_number=from_number,
                    message_type="text",
                    message_content=text[:100] if text else None,
                    response_time=response_time,
                    error=error_message
                ))
                
                return success
            
            # Analyze job ad text with timeout protection
            log_with_context(
                logger,
                logging.INFO,
                "Starting OpenAI analysis for text message",
                from_number=sanitize_phone_number(from_number),
                correlation_id=correlation_id
            )
            analysis_result = await asyncio.wait_for(
                self.openai_service.analyze_job_ad(text),
                timeout=12.0  # 12 second timeout for entire analysis
            )
            
            # Send analysis result back to user
            log_with_context(
                logger,
                logging.INFO,
                "Sending analysis result",
                from_number=sanitize_phone_number(from_number),
                trust_score=analysis_result.trust_score,
                classification=analysis_result.classification_text,
                correlation_id=correlation_id
            )
            success = await asyncio.wait_for(
                self.twilio_service.send_analysis_result(from_number, analysis_result),
                timeout=5.0  # 5 second timeout for Twilio API
            )
            
            # Record successful interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="text",
                message_content=text[:100] if text else None,
                analysis_result=analysis_result,
                response_time=response_time
            ))
            
            return success
            
        except asyncio.TimeoutError:
            # Handle timeout specifically
            log_with_context(
                logger,
                logging.ERROR,
                "Analysis timed out",
                from_number=sanitize_phone_number(from_number),
                correlation_id=correlation_id
            )
            error_message = "Analysis timeout"
            success = await self._send_custom_error_message(
                from_number,
                "⏱️ *Analysis Taking Too Long*\n\n"
                "The job analysis is taking longer than expected. "
                "This might be due to high demand or complex content.\n\n"
                "Please try again in a few minutes, or send a shorter job description."
            )
            
            # Record timeout interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="text",
                message_content=text[:100] if text else None,
                response_time=response_time,
                error=error_message
            ))
            
            return success
            
        except Exception as e:
            # Use centralized error handling
            user_message, error_info = handle_error(
                e,
                {
                    "from_number": sanitize_phone_number(from_number),
                    "text_length": len(text) if text else 0,
                    "component": "text_message_processing"
                },
                correlation_id
            )
            
            error_message = str(e)
            success = await self._send_error_with_fallback(from_number, error_info)
            
            # Record error interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="text",
                message_content=text[:100] if text else None,
                response_time=response_time,
                error=error_message
            ))
            
            return success
    
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
        correlation_id = get_correlation_id()
        start_time = time.time()
        analysis_result = None
        error_message = None
        
        log_with_context(
            logger,
            logging.INFO,
            "Handling media message",
            from_number=sanitize_phone_number(from_number),
            media_type=media_content_type,
            correlation_id=correlation_id
        )
        
        try:
            # Check if user is blocked (with timeout)
            try:
                is_blocked = await asyncio.wait_for(
                    self.user_service.is_user_blocked(from_number),
                    timeout=1.0  # 1 second timeout for user blocking check
                )
                if is_blocked:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Blocked user attempted to send media message",
                        from_number=sanitize_phone_number(from_number),
                        correlation_id=correlation_id
                    )
                    return True  # Silently ignore blocked users
            except asyncio.TimeoutError:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "User blocking check timed out, proceeding with analysis",
                    from_number=sanitize_phone_number(from_number),
                    correlation_id=correlation_id
                )
                # Continue processing if blocking check times out
            
            # Validate media type
            if not self._validate_media_type(media_content_type):
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Unsupported media type",
                    from_number=sanitize_phone_number(from_number),
                    media_type=media_content_type,
                    correlation_id=correlation_id
                )
                
                error_message = f"Unsupported media type: {media_content_type}"
                success = await self._send_media_type_error(from_number, media_content_type)
                
                # Record media type error interaction (non-blocking)
                response_time = time.time() - start_time
                asyncio.create_task(self._record_interaction_safe(
                    phone_number=from_number,
                    message_type="pdf",
                    message_content=f"media_type: {media_content_type}",
                    response_time=response_time,
                    error=error_message
                ))
                
                return success
            
            # Process PDF and extract text
            log_with_context(
                logger,
                logging.INFO,
                "Starting PDF processing",
                from_number=sanitize_phone_number(from_number),
                correlation_id=correlation_id
            )
            try:
                extracted_text = await self.pdf_service.process_pdf_url(media_url)
            except (PDFDownloadError, PDFExtractionError, PDFValidationError, PDFProcessingError) as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "PDF processing failed",
                    from_number=sanitize_phone_number(from_number),
                    error=str(e),
                    error_type=type(e).__name__,
                    correlation_id=correlation_id
                )
                error_message = str(e)
                # Use enhanced error handling instead of generic error message
                user_message, error_info = handle_error(e)
                await self._send_custom_error_message(from_number, user_message)
                return False
            
            # Analyze extracted text with timeout protection
            log_with_context(
                logger,
                logging.INFO,
                "Starting OpenAI analysis for PDF content",
                from_number=sanitize_phone_number(from_number),
                text_length=len(extracted_text),
                correlation_id=correlation_id
            )
            analysis_result = await asyncio.wait_for(
                self.openai_service.analyze_job_ad(extracted_text),
                timeout=12.0  # 12 second timeout for entire analysis
            )
            
            # Send analysis result back to user
            log_with_context(
                logger,
                logging.INFO,
                "Sending analysis result",
                from_number=sanitize_phone_number(from_number),
                trust_score=analysis_result.trust_score,
                classification=analysis_result.classification_text,
                correlation_id=correlation_id
            )
            success = await asyncio.wait_for(
                self.twilio_service.send_analysis_result(from_number, analysis_result),
                timeout=5.0  # 5 second timeout for Twilio API
            )
            
            # Record successful interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="pdf",
                message_content=extracted_text[:100] if extracted_text else None,
                analysis_result=analysis_result,
                response_time=response_time
            ))
            
            return success
            
        except asyncio.TimeoutError:
            # Handle timeout specifically
            log_with_context(
                logger,
                logging.ERROR,
                "PDF analysis timed out",
                from_number=sanitize_phone_number(from_number),
                correlation_id=correlation_id
            )
            error_message = "PDF analysis timeout"
            success = await self._send_custom_error_message(
                from_number,
                "⏱️ *Analysis Taking Too Long*\n\n"
                "The PDF analysis is taking longer than expected. "
                "This might be due to high demand or complex content.\n\n"
                "Please try again in a few minutes, or send the job details as text instead."
            )
            
            # Record timeout interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="pdf",
                message_content=f"media_url: {media_url}",
                response_time=response_time,
                error=error_message
            ))
            
            return success
            
        except Exception as e:
            # Use centralized error handling
            user_message, error_info = handle_error(
                e,
                {
                    "from_number": sanitize_phone_number(from_number),
                    "media_type": media_content_type,
                    "component": "media_message_processing"
                },
                correlation_id
            )
            
            error_message = str(e)
            success = await self._send_error_with_fallback(from_number, error_info)
            
            # Record error interaction (non-blocking)
            response_time = time.time() - start_time
            asyncio.create_task(self._record_interaction_safe(
                phone_number=from_number,
                message_type="pdf",
                message_content=f"media_url: {media_url}",
                response_time=response_time,
                error=error_message
            ))
            
            return success
    
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
    
    async def _send_error_with_fallback(self, from_number: str, error_info) -> bool:
        """
        Send error message to user with fallback response if available.
        
        Args:
            from_number: Recipient's WhatsApp number
            error_info: ErrorInfo object containing error details
            
        Returns:
            bool: True if message sent successfully
        """
        correlation_id = get_correlation_id()
        
        try:
            # Try to send the primary error message
            success = await self._send_custom_error_message(from_number, error_info.user_message)
            
            if success:
                return True
            
            # If primary message failed and fallback is available, try fallback
            if error_info.fallback_available:
                fallback_message = get_fallback_response(error_info.category)
                if fallback_message:
                    log_with_context(
                        logger,
                        logging.INFO,
                        "Sending fallback response",
                        from_number=sanitize_phone_number(from_number),
                        error_category=error_info.category.value,
                        correlation_id=correlation_id
                    )
                    return await self._send_custom_error_message(from_number, fallback_message)
            
            # Last resort: try generic error message
            return await self._send_custom_error_message(
                from_number,
                "⚠️ I'm experiencing technical difficulties. Please try again later."
            )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send error message with fallback",
                from_number=sanitize_phone_number(from_number),
                error=str(e),
                correlation_id=correlation_id
            )
            return False
    
    async def _send_custom_error_message(self, from_number: str, message: str) -> bool:
        """
        Send a custom error message to user.
        
        Args:
            from_number: Recipient's WhatsApp number
            message: Error message to send
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            # Ensure the from_number has the whatsapp: prefix
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
                logger.info(f"Added whatsapp: prefix to number: {sanitize_phone_number(from_number)}")
            
            # Use asyncio.wait_for to add timeout to Twilio API call
            import asyncio
            
            def send_twilio_message():
                return self.twilio_service.client.messages.create(
                    body=message,
                    from_=f"whatsapp:{self.config.twilio_phone_number}",
                    to=from_number
                )
            
            # Add 3-second timeout and run in thread pool to prevent blocking
            twilio_message = await asyncio.wait_for(
                asyncio.to_thread(send_twilio_message),
                timeout=3.0
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Custom error message sent",
                message_sid=twilio_message.sid,
                from_number=sanitize_phone_number(from_number),
                correlation_id=get_correlation_id()
            )
            return True
            
        except asyncio.TimeoutError:
            log_with_context(
                logger,
                logging.ERROR,
                "Twilio API call timed out",
                from_number=sanitize_phone_number(from_number),
                correlation_id=get_correlation_id()
            )
            return False
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to send custom error message",
                from_number=sanitize_phone_number(from_number),
                error=str(e),
                correlation_id=get_correlation_id()
            )
            return False
    
    async def _send_content_validation_error(self, from_number: str) -> bool:
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
        
        return await self._send_custom_error_message(from_number, error_message)
    
    async def _send_media_type_error(self, from_number: str, media_type: Optional[str]) -> bool:
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
        
        return await self._send_custom_error_message(from_number, error_message)
    
    async def _record_interaction_safe(self, **kwargs):
        """
        Record user interaction with timeout protection to prevent blocking.
        
        This method wraps the user_service.record_interaction call with a timeout
        to ensure database operations don't block the webhook response.
        """
        try:
            await asyncio.wait_for(
                self.user_service.record_interaction(**kwargs),
                timeout=2.0  # 2 second timeout for database operations
            )
        except asyncio.TimeoutError:
            log_with_context(
                logger,
                logging.WARNING,
                "Database interaction recording timed out",
                phone_number=sanitize_phone_number(kwargs.get('phone_number', 'unknown')),
                correlation_id=get_correlation_id()
            )
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to record interaction",
                error=str(e),
                phone_number=sanitize_phone_number(kwargs.get('phone_number', 'unknown')),
                correlation_id=get_correlation_id()
            )
    
    async def process_web_message(self, message_data: dict) -> AnalysisResult:
        """
        Process web-based message for job ad analysis.
        
        Args:
            message_data: Dictionary containing message information with keys:
                - message_type: MessageType (TEXT or PDF)
                - content: Text content or PDF bytes
                - user_id: Web user identifier
                - source: 'web'
                - analysis_id: Unique analysis identifier
                - correlation_id: Request correlation ID
                - filename: (optional) PDF filename
                
        Returns:
            AnalysisResult: Analysis results with trust score and reasoning
        """
        correlation_id = message_data.get('correlation_id')
        start_time = time.time()
        
        log_with_context(
            logger,
            logging.INFO,
            "Processing web message",
            user_id=message_data['user_id'],
            message_type=message_data['message_type'].value,
            analysis_id=message_data['analysis_id'],
            correlation_id=correlation_id
        )
        
        try:
            # Extract content based on message type
            if message_data['message_type'] == MessageType.PDF:
                # Process PDF content
                log_with_context(
                    logger,
                    logging.INFO,
                    "Processing PDF content for web analysis",
                    analysis_id=message_data['analysis_id'],
                    filename=message_data.get('filename'),
                    correlation_id=correlation_id
                )
                
                # Extract text from PDF bytes
                extracted_text = await self.pdf_service.process_pdf_bytes(
                    message_data['content'],
                    filename=message_data.get('filename', 'upload.pdf')
                )
                
                content_to_analyze = extracted_text
                
            else:
                # Use text content directly
                content_to_analyze = message_data['content']
                
                # Validate text content
                if not self._validate_text_content(content_to_analyze):
                    raise ValueError("Text content is too short or invalid for analysis")
            
            # Analyze the content using OpenAI
            log_with_context(
                logger,
                logging.INFO,
                "Starting OpenAI analysis for web content",
                analysis_id=message_data['analysis_id'],
                content_length=len(content_to_analyze),
                correlation_id=correlation_id
            )
            
            analysis_result = await self.openai_service.analyze_job_ad(content_to_analyze)
            
            try:
                # Record the interaction in the database
                response_time = time.time() - start_time
                await self.user_service.record_interaction(
                    phone_number=message_data['user_id'],  # Use user_id as identifier
                    message_type=message_data['message_type'].value.lower(),
                    message_content=content_to_analyze[:100] if content_to_analyze else None,
                    analysis_result=analysis_result,
                    response_time=response_time,
                    source='web'  # Mark as web source
                )
            except Exception as record_error:
                # Log the error but continue processing
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Failed to record web interaction",
                    error=str(record_error),
                    user_id=message_data['user_id'],
                    correlation_id=correlation_id
                )
            
            # Convert JobAnalysisResult to AnalysisResult for web response
            web_result = AnalysisResult(
                trust_score=analysis_result.trust_score,
                classification=analysis_result.classification_text,
                reasoning=analysis_result.reasoning,
                timestamp=analysis_result.timestamp
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Web analysis completed successfully",
                analysis_id=message_data['analysis_id'],
                trust_score=web_result.trust_score,
                classification=web_result.classification,
                processing_time=response_time,
                correlation_id=correlation_id
            )
            
            return web_result
            
        except Exception as e:
            # Handle errors
            response_time = time.time() - start_time
            error_message = str(e)
            
            try:
                # Record error interaction
                await self.user_service.record_interaction(
                    phone_number=message_data['user_id'],
                    message_type=message_data['message_type'].value.lower(),
                    message_content=str(message_data['content'])[:100] if message_data.get('content') else None,
                    response_time=response_time,
                    error=error_message,
                    source='web'
                )
            except Exception as record_error:
                # Log the error but continue processing
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Failed to record web error interaction",
                    error=str(record_error),
                    original_error=error_message,
                    user_id=message_data['user_id'],
                    correlation_id=correlation_id
                )
            
            log_with_context(
                logger,
                logging.ERROR,
                "Web analysis failed",
                analysis_id=message_data['analysis_id'],
                error=error_message,
                error_type=type(e).__name__,
                processing_time=response_time,
                correlation_id=correlation_id
            )
            
            # Re-raise the exception to be handled by the API endpoint
            raise

