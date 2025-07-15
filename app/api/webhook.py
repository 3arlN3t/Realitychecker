"""
Twilio webhook endpoint for WhatsApp message processing.

This module provides the webhook endpoint that receives incoming WhatsApp messages
from Twilio and processes them through the message handling service.
"""

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

logger = logging.getLogger(__name__)

# Create router for webhook endpoints
router = APIRouter(prefix="/webhook", tags=["webhook"])


def get_message_handler() -> MessageHandlerService:
    """Dependency to get MessageHandlerService instance."""
    config = get_config()
    return MessageHandlerService(config)


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
        logger.warning(f"Invalid Twilio signature. Expected: {expected_signature}, Got: {signature}")
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
    message_handler: MessageHandlerService = Depends(get_message_handler)
) -> PlainTextResponse:
    """
    Twilio WhatsApp webhook endpoint for processing incoming messages.
    
    This endpoint receives webhook requests from Twilio when users send messages
    to the WhatsApp bot. It validates the request, processes the message content,
    and returns an appropriate response.
    
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
    logger.info(f"Received webhook request: MessageSid={MessageSid}, From={From}, NumMedia={NumMedia}")
    
    try:
        # Get configuration for signature validation
        config = get_config()
        
        # Prepare form data for signature validation
        form_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": str(NumMedia)
        }
        
        # Add media parameters if present
        if MediaUrl0:
            form_data["MediaUrl0"] = MediaUrl0
        if MediaContentType0:
            form_data["MediaContentType0"] = MediaContentType0
        
        # Validate Twilio signature for security
        if not validate_twilio_signature(request, form_data, config):
            logger.error(f"Webhook signature validation failed for MessageSid: {MessageSid}")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )
        
        # Create and validate Twilio webhook request object
        try:
            twilio_request = TwilioWebhookRequest(
                MessageSid=MessageSid,
                From=From,
                To=To,
                Body=Body,
                NumMedia=NumMedia,
                MediaUrl0=MediaUrl0,
                MediaContentType0=MediaContentType0
            )
        except ValueError as e:
            logger.error(f"Invalid webhook request data: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Process the message through the message handler service
        logger.info(f"Processing message {MessageSid} through MessageHandlerService")
        success = await message_handler.process_message(twilio_request)
        
        if success:
            logger.info(f"Successfully processed message {MessageSid}")
        else:
            logger.warning(f"Failed to process message {MessageSid}")
        
        # Return empty response as expected by Twilio
        # Twilio expects HTTP 200 with empty body to acknowledge receipt
        return PlainTextResponse("", status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, auth failures)
        raise
        
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
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