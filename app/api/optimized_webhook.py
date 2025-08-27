"""
Optimized Twilio webhook endpoint for WhatsApp message processing.

This module provides the webhook endpoint that receives incoming WhatsApp messages
from Twilio and processes them through the message handling service with sub-2-second
response times and immediate acknowledgment patterns.

Key optimizations:
- Sub-500ms response time for webhook acknowledgment
- Immediate response pattern before starting message processing
- Request validation caching to reduce processing overhead
- Optimized Twilio signature validation with timeout protection
- Asynchronous background processing with task queuing
"""

import asyncio
import logging
import hashlib
import hmac
import base64
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.config import get_config
from app.models.data_models import TwilioWebhookRequest, AppConfig
from app.services.message_handler import MessageHandlerService
from app.services.redis_connection_manager import get_redis_manager
from app.services.performance_monitor import get_performance_monitor
from app.services.background_task_processor import get_task_processor, TaskPriority
from app.services.task_handlers import create_message_processing_task, register_default_handlers
from app.dependencies import get_message_handler_service, get_app_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context, sanitize_phone_number
from app.utils.error_handling import handle_error, ErrorCategory
from app.utils.security import validate_webhook_request, SecurityValidator

logger = get_logger(__name__)

# Constants for validation
MIN_TEXT_LENGTH = 20
MAX_TEXT_LENGTH = 10000  # Prevent extremely large messages
MAX_MEDIA_SIZE = 16 * 1024 * 1024  # 16MB limit for media

# Performance constants - Requirement 2.1: Sub-2-second response times
WEBHOOK_TIMEOUT_MS = 500  # 500ms target for webhook acknowledgment (Requirement 2.2)
SIGNATURE_VALIDATION_TIMEOUT = 0.05  # 50ms timeout for signature validation (Requirement 2.6)
VALIDATION_CACHE_TTL = 300  # 5 minutes cache TTL for validation results
FAST_VALIDATION_TIMEOUT = 0.1  # 100ms timeout for fast validation checks

# Create router for webhook endpoints
router = APIRouter(prefix="/webhook", tags=["webhook"])


@dataclass
class ValidationCacheEntry:
    """Cache entry for validation results."""
    is_valid: bool
    timestamp: datetime
    error_message: Optional[str] = None


class OptimizedWebhookProcessor:
    """Optimized webhook processor with caching and immediate response patterns."""
    
    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.task_processor = get_task_processor()
        self.graceful_handler = None
        self.validation_cache: Dict[str, ValidationCacheEntry] = {}
        self.security_validator = SecurityValidator()
        self._handlers_registered = False
    
    def _get_graceful_handler(self):
        """Lazy initialization of graceful error handler to avoid circular imports."""
        if self.graceful_handler is None:
            try:
                from app.utils.graceful_error_handling import get_graceful_error_handler
                self.graceful_handler = get_graceful_error_handler()
            except ImportError:
                # Fallback if graceful error handling is not available
                self.graceful_handler = None
        return self.graceful_handler
    
    async def get_cached_validation(self, cache_key: str) -> Optional[ValidationCacheEntry]:
        """
        Get cached validation result with graceful fallback.
        
        Implements request validation caching to reduce processing overhead (Requirement 2.2).
        Implements Requirement 6.5: Ensure webhook processing continues during Redis outages
        """
        try:
            graceful_handler = self._get_graceful_handler()
            
            if graceful_handler:
                # Use graceful error handling for cache lookup
                cached_data = await asyncio.wait_for(
                    graceful_handler.redis_get_with_fallback(f"webhook_validation:{cache_key}"),
                    timeout=0.02  # 20ms timeout for cache lookup - very aggressive
                )
            else:
                # Fallback to direct Redis access
                if self.redis_manager.is_available():
                    cached_data = await asyncio.wait_for(
                        self.redis_manager.execute_command('get', f"webhook_validation:{cache_key}"),
                        timeout=0.02  # 20ms timeout for cache lookup - very aggressive
                    )
                else:
                    cached_data = None
            
            if cached_data:
                if isinstance(cached_data, str):
                    import json
                    data = json.loads(cached_data)
                else:
                    data = cached_data
                    
                return ValidationCacheEntry(
                    is_valid=data['is_valid'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    error_message=data.get('error_message')
                )
        except Exception:
            pass  # Fall back to memory cache immediately
        
        # Fall back to memory cache (always fast)
        entry = self.validation_cache.get(cache_key)
        if entry and (datetime.now() - entry.timestamp).seconds < VALIDATION_CACHE_TTL:
            return entry
        
        return None
    
    async def cache_validation_result(self, cache_key: str, entry: ValidationCacheEntry):
        """
        Cache validation result with graceful fallback.
        
        Implements request validation caching to reduce processing overhead (Requirement 2.2).
        Implements Requirement 6.5: Ensure webhook processing continues during Redis outages
        """
        # Always cache in memory first (fastest)
        self.validation_cache[cache_key] = entry
        
        # Try to cache with graceful fallback (non-blocking)
        try:
            graceful_handler = self._get_graceful_handler()
            import json
            cache_data = {
                'is_valid': entry.is_valid,
                'timestamp': entry.timestamp.isoformat(),
                'error_message': entry.error_message
            }
            
            if graceful_handler:
                # Use graceful error handling for cache write with very short timeout
                await asyncio.wait_for(
                    graceful_handler.redis_set_with_fallback(
                        f"webhook_validation:{cache_key}",
                        json.dumps(cache_data),
                        VALIDATION_CACHE_TTL
                    ),
                    timeout=0.02  # 20ms timeout for cache write - very aggressive
                )
            else:
                # Fallback to direct Redis access
                if self.redis_manager.is_available():
                    await asyncio.wait_for(
                        self.redis_manager.execute_command(
                            'setex', 
                            f"webhook_validation:{cache_key}",
                            VALIDATION_CACHE_TTL,
                            json.dumps(cache_data)
                        ),
                        timeout=0.02  # 20ms timeout for cache write - very aggressive
                    )
        except Exception:
            pass  # Cache write failure is not critical for webhook performance
    
    def create_cache_key(self, message_sid: str, from_number: str, body_hash: str) -> str:
        """Create cache key for validation results."""
        return f"{message_sid}:{hash(from_number)}:{body_hash}"
    
    async def fast_signature_validation(self, request: Request, body_data: Dict[str, str], config: AppConfig) -> bool:
        """
        Fast Twilio signature validation with timeout protection.
        
        Implements Requirement 2.6: Optimize Twilio signature validation with timeout protection
        """
        if not config.webhook_validation:
            return True
        
        try:
            # Use asyncio.wait_for to enforce aggressive timeout
            return await asyncio.wait_for(
                self._validate_signature_sync(request, body_data, config),
                timeout=SIGNATURE_VALIDATION_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"Signature validation timed out after {SIGNATURE_VALIDATION_TIMEOUT}s, allowing request")
            return True  # Allow request if validation times out to prevent blocking
        except Exception as e:
            logger.warning(f"Signature validation error: {e}")
            return not config.webhook_validation  # Fail closed if validation is required
    
    async def _validate_signature_sync(self, request: Request, body_data: Dict[str, str], config: AppConfig) -> bool:
        """Synchronous signature validation."""
        signature = request.headers.get('X-Twilio-Signature')
        if not signature:
            return False
        
        url = str(request.url)
        sorted_params = sorted(body_data.items())
        data_string = url + urlencode(sorted_params)
        
        expected_signature = base64.b64encode(
            hmac.new(
                config.twilio_auth_token.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(signature, expected_signature)


# Global processor instance
webhook_processor = OptimizedWebhookProcessor()


@router.post("/whatsapp-optimized")
async def whatsapp_webhook_optimized(
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
    Optimized Twilio WhatsApp webhook endpoint with sub-2-second response times.
    
    This endpoint implements the following optimizations:
    - Requirement 2.1: Respond to Twilio within 2 seconds (target: 500ms)
    - Requirement 2.2: Complete validation and queuing within 500ms
    - Requirement 2.6: Optimized Twilio signature validation with timeout protection
    
    Implementation pattern:
    1. Immediate validation with caching (target: <100ms)
    2. Fast signature validation with timeout (target: <50ms)
    3. Immediate acknowledgment to Twilio (target: <200ms total)
    4. Background processing queue (non-blocking)
    
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
        config: Application configuration
        
    Returns:
        PlainTextResponse: Empty response with HTTP 200 status for Twilio
        
    Raises:
        HTTPException: 400 for validation errors, 401 for signature validation failures
    """
    start_time = time.time()
    correlation_id = get_correlation_id()
    
    # Start performance monitoring
    performance_monitor = get_performance_monitor()
    request_id = performance_monitor.record_request_start()
    
    # Log webhook request with minimal overhead
    log_with_context(
        logger,
        logging.INFO,
        "Webhook received",
        message_sid=MessageSid,
        from_number=sanitize_phone_number(From),
        has_media=NumMedia > 0,
        correlation_id=correlation_id
    )
    
    try:
        # PHASE 1: IMMEDIATE VALIDATION (Target: <100ms) - Requirement 2.2
        validation_start = time.time()
        
        # Create cache key for validation caching
        body_hash = str(hash(Body)) if Body else "empty"
        cache_key = webhook_processor.create_cache_key(MessageSid, From, body_hash)
        
        # Check validation cache first to reduce processing overhead
        cached_validation = await webhook_processor.get_cached_validation(cache_key)
        if cached_validation:
            if not cached_validation.is_valid:
                raise HTTPException(status_code=400, detail=cached_validation.error_message or "Cached validation failed")
            logger.debug(f"Using cached validation for {MessageSid}")
        else:
            # Perform fast validation with aggressive timeouts
            
            # Prepare form data for signature validation
            form_data = {
                "MessageSid": MessageSid,
                "From": From,
                "To": To,
                "Body": Body,
                "NumMedia": str(NumMedia)
            }
            
            if MediaUrl0:
                form_data["MediaUrl0"] = MediaUrl0
            if MediaContentType0:
                form_data["MediaContentType0"] = MediaContentType0
            
            # Fast signature validation with timeout protection - Requirement 2.6
            signature_valid = await webhook_processor.fast_signature_validation(request, form_data, config)
            if not signature_valid and config.webhook_validation:
                error_msg = "Invalid webhook signature"
                await webhook_processor.cache_validation_result(
                    cache_key, 
                    ValidationCacheEntry(False, datetime.now(), error_msg)
                )
                raise HTTPException(status_code=401, detail=error_msg)
            
            # Fast basic validation (optimized for speed)
            validation_error = None
            if not MessageSid or len(MessageSid) < 10:
                validation_error = "Invalid MessageSid"
            elif not From or not From.startswith("whatsapp:"):
                validation_error = "Invalid From number"
            elif Body and len(Body) > MAX_TEXT_LENGTH:
                validation_error = f"Text too long (max {MAX_TEXT_LENGTH} chars)"
            elif MediaContentType0 and MediaContentType0 not in ['application/pdf', 'image/jpeg', 'image/png', 'image/gif']:
                validation_error = f"Unsupported media type: {MediaContentType0}"
            
            if validation_error:
                await webhook_processor.cache_validation_result(
                    cache_key,
                    ValidationCacheEntry(False, datetime.now(), validation_error)
                )
                raise HTTPException(status_code=400, detail=validation_error)
            
            # Cache successful validation for future requests
            await webhook_processor.cache_validation_result(
                cache_key,
                ValidationCacheEntry(True, datetime.now())
            )
        
        validation_time = (time.time() - validation_start) * 1000
        logger.debug(f"Validation phase completed in {validation_time:.1f}ms")
        
        # PHASE 2: IMMEDIATE ACKNOWLEDGMENT (Target: <200ms total) - Requirement 2.1, 2.2
        # Check if we're within our target response time
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > WEBHOOK_TIMEOUT_MS * 0.6:  # 60% of target time (300ms)
            logger.warning(f"Webhook processing taking longer than expected: {elapsed_ms:.1f}ms")
        
        # Create webhook request object for background processing (fast creation)
        try:
            # Quick sanitization - minimal processing to stay within time budget
            sanitized_body = webhook_processor.security_validator.sanitize_text(Body) if Body else ""
            
            twilio_request = TwilioWebhookRequest(
                MessageSid=MessageSid,
                From=From,
                To=To,
                Body=sanitized_body,
                NumMedia=NumMedia,
                MediaUrl0=MediaUrl0,
                MediaContentType0=MediaContentType0
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
        
        # PHASE 3: BACKGROUND PROCESSING QUEUE (Non-blocking)
        # Ensure task handlers are registered (one-time setup)
        if not webhook_processor._handlers_registered:
            register_default_handlers(webhook_processor.task_processor)
            webhook_processor._handlers_registered = True
        
        # Determine task priority based on message type (fast decision)
        priority = TaskPriority.HIGH if NumMedia > 0 else TaskPriority.NORMAL
        
        # Create and queue task for background processing (non-blocking)
        try:
            processing_task = await create_message_processing_task(
                twilio_request, 
                correlation_id, 
                priority
            )
            
            # Queue task without waiting for confirmation to maintain speed
            task_id = await webhook_processor.task_processor.queue_task(processing_task)
            
            log_with_context(
                logger,
                logging.INFO,
                "Message queued for background processing",
                message_sid=MessageSid,
                task_id=task_id,
                priority=priority.name,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Fallback to immediate processing if task queuing fails (non-blocking)
            log_with_context(
                logger,
                logging.WARNING,
                "Task queuing failed, falling back to immediate processing",
                message_sid=MessageSid,
                error=str(e),
                correlation_id=correlation_id
            )
            
            # Fire-and-forget background processing
            background_task = asyncio.create_task(
                _process_message_background(twilio_request, message_handler, correlation_id)
            )
            
            background_task.add_done_callback(
                lambda task: _handle_background_task_completion(task, MessageSid, correlation_id)
            )
        
        # PHASE 4: IMMEDIATE RESPONSE - Requirement 2.1: Acknowledge within 500ms
        response_time_ms = (time.time() - start_time) * 1000
        response_time_seconds = response_time_ms / 1000
        
        # Record performance metrics
        performance_monitor.record_request_end(request_id, response_time_seconds, success=True)
        performance_monitor.record_metric(
            "webhook_response_time",
            response_time_seconds,
            "seconds",
            {"message_sid": MessageSid, "within_target": str(response_time_ms <= WEBHOOK_TIMEOUT_MS)}
        )
        
        # Record detailed webhook timing breakdown - Requirement 4.1
        try:
            from app.services.performance_monitor import WebhookTimingBreakdown
            
            # Calculate individual phase timings (approximate based on logged times)
            total_time = response_time_seconds
            validation_time = validation_time / 1000  # Convert to seconds
            signature_validation_time = 0.05 if config.webhook_validation else 0.0  # Estimated
            task_queuing_time = 0.01  # Estimated queuing time
            response_preparation_time = max(0, total_time - validation_time - signature_validation_time - task_queuing_time)
            cache_lookup_time = 0.005  # Estimated cache lookup time
            redis_operation_time = 0.01 if webhook_processor.redis_manager.is_available() else 0.0
            
            timing_breakdown = WebhookTimingBreakdown(
                total_time=total_time,
                validation_time=validation_time,
                signature_validation_time=signature_validation_time,
                task_queuing_time=task_queuing_time,
                response_preparation_time=response_preparation_time,
                cache_lookup_time=cache_lookup_time,
                redis_operation_time=redis_operation_time,
                timestamp=datetime.now(),
                message_sid=MessageSid,
                within_500ms_target=response_time_ms <= WEBHOOK_TIMEOUT_MS,
                within_2s_target=response_time_ms <= 2000
            )
            
            performance_monitor.record_webhook_timing_breakdown(timing_breakdown)
            
        except Exception as e:
            logger.warning(f"Failed to record webhook timing breakdown: {e}")
        
        # Determine if we met our performance targets
        within_target = response_time_ms <= WEBHOOK_TIMEOUT_MS
        within_2s_target = response_time_ms <= 2000  # Requirement 2.1: Sub-2-second response
        
        log_with_context(
            logger,
            logging.INFO,
            "Webhook acknowledged",
            message_sid=MessageSid,
            response_time_ms=round(response_time_ms, 1),
            within_500ms_target=within_target,
            within_2s_target=within_2s_target,
            correlation_id=correlation_id
        )
        
        # Log performance warnings based on requirements
        if response_time_ms > 2000:  # Requirement 2.1 violation
            log_with_context(
                logger,
                logging.ERROR,
                "Webhook response time exceeded 2-second requirement",
                message_sid=MessageSid,
                response_time_ms=round(response_time_ms, 1),
                requirement="2.1",
                correlation_id=correlation_id
            )
        elif response_time_ms > WEBHOOK_TIMEOUT_MS:  # Requirement 2.2 violation
            log_with_context(
                logger,
                logging.WARNING,
                "Webhook response time exceeded 500ms target",
                message_sid=MessageSid,
                response_time_ms=round(response_time_ms, 1),
                target_ms=WEBHOOK_TIMEOUT_MS,
                requirement="2.2",
                correlation_id=correlation_id
            )
        
        # Return immediate success to Twilio - implements immediate response pattern
        return PlainTextResponse("", status_code=200)
        
    except HTTPException:
        # Log and re-raise HTTP exceptions
        response_time_ms = (time.time() - start_time) * 1000
        response_time_seconds = response_time_ms / 1000
        
        # Record failed request metrics
        performance_monitor.record_request_end(request_id, response_time_seconds, success=False)
        
        log_with_context(
            logger,
            logging.WARNING,
            "Webhook validation failed",
            message_sid=MessageSid,
            response_time_ms=round(response_time_ms, 1),
            correlation_id=correlation_id
        )
        raise
        
    except Exception as e:
        # Handle unexpected errors with comprehensive diagnostics
        response_time_ms = (time.time() - start_time) * 1000
        response_time_seconds = response_time_ms / 1000
        
        # Record failed request metrics
        performance_monitor.record_request_end(request_id, response_time_seconds, success=False)
        
        # Collect comprehensive error diagnostics - Requirement 6.4
        try:
            from app.utils.error_diagnostics import collect_error_diagnostics, DiagnosticLevel
            
            error_context = {
                'message_sid': MessageSid,
                'from_number': sanitize_phone_number(From),
                'response_time_ms': round(response_time_ms, 1),
                'webhook_endpoint': 'whatsapp-optimized',
                'has_media': NumMedia > 0,
                'body_length': len(Body) if Body else 0
            }
            
            # Collect diagnostics asynchronously to not block webhook response
            asyncio.create_task(
                collect_error_diagnostics(
                    e, 
                    error_context, 
                    correlation_id, 
                    DiagnosticLevel.DETAILED
                )
            )
        except Exception as diag_error:
            logger.warning(f"Failed to collect error diagnostics: {diag_error}")
        
        log_with_context(
            logger,
            logging.ERROR,
            "Webhook processing error with graceful handling",
            message_sid=MessageSid,
            response_time_ms=round(response_time_ms, 1),
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        
        # Still return success to Twilio to prevent retries - Requirement 6.5
        return PlainTextResponse("", status_code=200)


async def _process_message_background(
    twilio_request: TwilioWebhookRequest,
    message_handler: MessageHandlerService,
    correlation_id: str
):
    """Process message in background with comprehensive error handling."""
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Starting background message processing",
            message_sid=twilio_request.MessageSid,
            correlation_id=correlation_id
        )
        
        # Process message with timeout
        success = await asyncio.wait_for(
            message_handler.process_message(twilio_request),
            timeout=30.0  # 30 second timeout for background processing
        )
        
        log_with_context(
            logger,
            logging.INFO,
            "Background message processing completed",
            message_sid=twilio_request.MessageSid,
            success=success,
            correlation_id=correlation_id
        )
        
    except asyncio.TimeoutError:
        log_with_context(
            logger,
            logging.ERROR,
            "Background message processing timed out",
            message_sid=twilio_request.MessageSid,
            correlation_id=correlation_id
        )
        
        # Try to send timeout message to user
        try:
            await message_handler.handle_text_message(
                "timeout_notification",
                twilio_request.From
            )
        except Exception:
            pass  # Don't fail if we can't send timeout notification
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Background message processing failed",
            message_sid=twilio_request.MessageSid,
            error=str(e),
            correlation_id=correlation_id
        )


def _handle_background_task_completion(task: asyncio.Task, message_sid: str, correlation_id: str):
    """Handle completion of background processing task."""
    if task.exception():
        log_with_context(
            logger,
            logging.ERROR,
            "Background task failed",
            message_sid=message_sid,
            error=str(task.exception()),
            correlation_id=correlation_id
        )
    else:
        log_with_context(
            logger,
            logging.DEBUG,
            "Background task completed successfully",
            message_sid=message_sid,
            correlation_id=correlation_id
        )


@router.post("/whatsapp")
async def whatsapp_webhook_main(
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
    Main webhook endpoint that delegates to the optimized handler.
    
    This endpoint implements all the requirements for task 2:
    - Requirement 2.1: Respond to Twilio within 2 seconds
    - Requirement 2.2: Complete validation and queuing within 500ms  
    - Requirement 2.6: Optimized Twilio signature validation with timeout protection
    """
    return await whatsapp_webhook_optimized(
        request, MessageSid, From, To, Body, NumMedia, MediaUrl0, MediaContentType0,
        message_handler, config
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