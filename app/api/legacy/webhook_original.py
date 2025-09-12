"""
Twilio webhook endpoint for WhatsApp message processing.

This module provides the webhook endpoint that receives incoming WhatsApp messages
from Twilio and processes them through the message handling service.
"""

import asyncio
import logging
import hashlib
import hmac
import base64
from typing import Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.config import get_config
from app.models.data_models import TwilioWebhookRequest, AppConfig
from app.services.message_handler import MessageHandlerService
from app.dependencies import get_message_handler_service, get_app_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context, sanitize_phone_number
from app.utils.error_handling import handle_error, ErrorCategory
from app.utils.security import validate_webhook_request, SecurityValidator

logger = get_logger(__name__)

# Constants for validation
MIN_TEXT_LENGTH = 20
MAX_TEXT_LENGTH = 10000  # Prevent extremely large messages
MAX_MEDIA_SIZE = 16 * 1024 * 1024  # 16MB limit for media

# Create router for webhook endpoints
router = APIRouter(prefix="/webhook", tags=["webhook"])


def validate_twilio_signature(
    request: Request,
    body_data: Dict[str, str],
    config: AppConfig
) -> bool:
    """
    Validate Twilio webhook signature for security.
    
    Args:
        request: FastAPI request object containing headers
        body_data: Form data from the webhook request
        config: Application configuration containing Twilio auth token
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not config.webhook_validation:
        logger.debug("Webhook signature validation is disabled")
        return True
    
    # Get the signature from headers
    signature = request.headers.get('X-Twilio-Signature')
    if not signature:
        logger.warning("Missing X-Twilio-Signature header")
        return False
    
    # Get the full URL (Twilio uses the full URL for signature calculation)
    url = str(request.url)
    
    # Create the expected signature
    # Twilio concatenates the URL with the POST parameters (sorted by key)
    sorted_params = sorted(body_data.items())
    data_string = url + urlencode(sorted_params)
    
    # Create HMAC-SHA1 signature
    expected_signature = base64.b64encode(
        hmac.new(
            config.twilio_auth_token.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    # Compare signatures
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning("Invalid Twilio signature detected")
    else:
        logger.debug("Twilio signature validation successful")
    
    return is_valid


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
    message_handler: MessageHandlerService = Depends(get_message_handler_service),
    config: AppConfig = Depends(get_app_config)
) -> PlainTextResponse:
    """
    Twilio WhatsApp webhook endpoint for processing incoming messages.
    
    This endpoint receives webhook requests from Twilio when users send messages
    to the WhatsApp bot. It validates the request, processes the message content
    asynchronously in the background, and returns an immediate response to Twilio.
    
    Args:
        request: FastAPI request object for signature validation
        MessageSid: Unique identifier for the message from Twilio
        From: Sender's WhatsApp number (format: whatsapp:+1234567890)
        To: Bot's WhatsApp number (format: whatsapp:+1234567890)
        Body: Text content of the message (empty for media-only messages)
        NumMedia: Number of media attachments (0 for text-only messages)
        MediaUrl0: URL of the first media attachment (if any)
        MediaContentType0: MIME type of the first media attachment (if any)
        message_handler: Injected MessageHandlerService instance
        
    Returns:
        PlainTextResponse: Empty response with HTTP 200 status for Twilio
        
    Raises:
        HTTPException: 400 for validation errors, 401 for signature validation failures
    """
    correlation_id = get_correlation_id()
    
    # Log webhook request with sanitized phone numbers
    log_with_context(
        logger,
        logging.INFO,
        "Received webhook request",
        message_sid=MessageSid,
        from_number=sanitize_phone_number(From),
        num_media=NumMedia,
        has_body=bool(Body.strip()),
        correlation_id=correlation_id
    )
    
    try:
        # Prepare form data for signature validation
        form_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": str(NumMedia)
        }
        
        # Add media parameters if present and validate media content
        if MediaUrl0:
            form_data["MediaUrl0"] = MediaUrl0
            # Basic URL validation for media
            if not MediaUrl0.startswith(('https://', 'http://')):
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Invalid media URL format",
                    message_sid=MessageSid,
                    from_number=sanitize_phone_number(From),
                    correlation_id=correlation_id
                )
                raise HTTPException(
                    status_code=400,
                    detail="Invalid media URL format"
                )
        if MediaContentType0:
            form_data["MediaContentType0"] = MediaContentType0
            # Validate allowed media types
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'text/plain']
            if MediaContentType0 not in allowed_types:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Unsupported media type",
                    message_sid=MessageSid,
                    from_number=sanitize_phone_number(From),
                    media_type=MediaContentType0,
                    correlation_id=correlation_id
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported media type: {MediaContentType0}"
                )
        
        # Log MessageSid for debugging validation issues
        log_with_context(
            logger,
            logging.DEBUG,
            "Validating webhook request",
            message_sid=MessageSid,
            message_sid_length=len(MessageSid),
            message_sid_prefix=MessageSid[:5] if len(MessageSid) >= 5 else MessageSid,
            from_number=sanitize_phone_number(From),
            correlation_id=correlation_id
        )
        
        # Validate Twilio signature for security FIRST (most important security check)
        if not validate_twilio_signature(request, form_data, config):
            log_with_context(
                logger,
                logging.ERROR,
                "Webhook signature validation failed",
                message_sid=MessageSid,
                from_number=sanitize_phone_number(From),
                webhook_validation_enabled=config.webhook_validation,
                correlation_id=correlation_id
            )
            # Only fail if webhook validation is strictly enabled
            if config.webhook_validation:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )
        
        # Validate webhook request data for security
        is_valid, validation_error = validate_webhook_request(
            MessageSid, From, To, Body, MediaUrl0
        )
        if not is_valid:
            log_with_context(
                logger,
                logging.ERROR,
                "Webhook request validation failed",
                message_sid=MessageSid,
                message_sid_length=len(MessageSid),
                message_sid_prefix=MessageSid[:5] if len(MessageSid) >= 5 else MessageSid,
                from_number=sanitize_phone_number(From),
                to_number=sanitize_phone_number(To),
                body_length=len(Body) if Body else 0,
                has_media=NumMedia > 0,
                media_url=MediaUrl0[:50] + "..." if MediaUrl0 and len(MediaUrl0) > 50 else MediaUrl0,
                media_type=MediaContentType0,
                validation_error=validation_error,
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {validation_error}"
            )
        
        # Sanitize input data early (reuse validator instance if possible)
        security_validator = SecurityValidator()
        sanitized_body = security_validator.sanitize_text(Body) if Body else ""
        
        # Early validation for text content length to avoid expensive processing
        text_length = len(sanitized_body.strip()) if sanitized_body else 0
        if sanitized_body and text_length < MIN_TEXT_LENGTH:
            log_with_context(
                logger,
                logging.WARNING,
                "Text content too short for analysis",
                message_sid=MessageSid,
                from_number=sanitize_phone_number(From),
                text_length=text_length,
                correlation_id=correlation_id
            )
            # Send helpful message asynchronously and return success to Twilio
            task = asyncio.create_task(message_handler.handle_text_message(
                "help", From  # Trigger help message for short content
            ))
            # Add error handling for the background task
            task.add_done_callback(lambda t: logger.error(f"Help message task failed: {t.exception()}") if t.exception() else None)
            return PlainTextResponse("", status_code=200)
        
        # Validate maximum text length to prevent abuse
        if sanitized_body and text_length > MAX_TEXT_LENGTH:
            log_with_context(
                logger,
                logging.WARNING,
                "Text content too long for analysis",
                message_sid=MessageSid,
                from_number=sanitize_phone_number(From),
                text_length=text_length,
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=400,
                detail=f"Text content too long. Maximum {MAX_TEXT_LENGTH} characters allowed."
            )
        
        # Create and validate Twilio webhook request object with sanitized data
        try:
            twilio_request = TwilioWebhookRequest(
                MessageSid=MessageSid,
                From=From,
                To=To,
                Body=sanitized_body,  # Use sanitized body
                NumMedia=NumMedia,
                MediaUrl0=MediaUrl0,
                MediaContentType0=MediaContentType0
            )
        except ValueError as e:
            user_message, error_info = handle_error(
                e,
                {
                    "message_sid": MessageSid,
                    "from_number": sanitize_phone_number(From),
                    "component": "webhook_validation"
                },
                correlation_id
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Process the message through the message handler service
        log_with_context(
            logger,
            logging.INFO,
            "Processing message through MessageHandlerService",
            message_sid=MessageSid,
            correlation_id=correlation_id
        )
        
        # Process message asynchronously to avoid blocking Twilio webhook
        # This implements a fire-and-forget pattern for better webhook performance
        task = asyncio.create_task(message_handler.process_message(twilio_request))
        
        # Add error handling for the background task
        def handle_task_completion(task_result):
            if task_result.exception():
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Background message processing failed",
                    message_sid=MessageSid,
                    correlation_id=correlation_id,
                    error=str(task_result.exception())
                )
            else:
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Background message processing completed successfully",
                    message_sid=MessageSid,
                    correlation_id=correlation_id
                )
        
        task.add_done_callback(handle_task_completion)
        
        # Return immediate success to Twilio (they expect quick response)
        log_with_context(
            logger,
            logging.INFO,
            "Webhook acknowledged, processing message asynchronously",
            message_sid=MessageSid,
            correlation_id=correlation_id
        )
        
        # Return empty response as expected by Twilio
        # Twilio expects HTTP 200 with empty body to acknowledge receipt
        return PlainTextResponse("", status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, auth failures)
        raise
        
    except Exception as e:
        # Handle unexpected errors with centralized error handler
        user_message, error_info = handle_error(
            e,
            {
                "message_sid": MessageSid,
                "from_number": sanitize_phone_number(From),
                "component": "webhook_processing",
                "has_media": NumMedia > 0,
                "text_length": len(Body) if Body else 0
            },
            correlation_id
        )
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing webhook"
        )


@router.get("/whatsapp")
async def whatsapp_webhook_get() -> Dict[str, str]:
    """
    Handle GET requests to the webhook endpoint.
    
    This endpoint is useful for testing webhook connectivity and
    can be used by monitoring systems to verify the endpoint is accessible.
    
    Returns:
        Dict containing status information
    """
    logger.info("Received GET request to webhook endpoint")
    return {
        "status": "active",
        "message": "WhatsApp webhook endpoint is operational",
        "methods": "POST"
    }