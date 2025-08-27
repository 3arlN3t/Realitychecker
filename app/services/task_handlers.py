"""
Task handlers for background processing.

This module provides task handlers that can be registered with the
BackgroundTaskProcessor to handle specific types of background tasks.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from app.models.data_models import TwilioWebhookRequest, AppConfig
from app.services.message_handler import MessageHandlerService
from app.services.background_task_processor import ProcessingTask, TaskPriority
from app.utils.logging import get_logger, log_with_context, sanitize_phone_number
from app.dependencies import get_message_handler_service, get_app_config

logger = get_logger(__name__)


class MessageProcessingTaskHandler:
    """Handler for message processing tasks."""
    
    def __init__(self):
        self.message_handler: Optional[MessageHandlerService] = None
        self.config: Optional[AppConfig] = None
    
    async def _ensure_dependencies(self):
        """Ensure dependencies are initialized."""
        if not self.message_handler:
            self.message_handler = get_message_handler_service()
        if not self.config:
            self.config = get_app_config()
    
    async def handle_message_processing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle message processing task.
        
        Args:
            payload: Task payload containing message data
            
        Returns:
            Processing result
        """
        await self._ensure_dependencies()
        
        try:
            # Extract message data from payload
            message_data = payload.get('message_data')
            if not message_data:
                raise ValueError("No message data in payload")
            
            # Create TwilioWebhookRequest from payload
            twilio_request = TwilioWebhookRequest(
                MessageSid=message_data['MessageSid'],
                From=message_data['From'],
                To=message_data['To'],
                Body=message_data.get('Body', ''),
                NumMedia=message_data.get('NumMedia', 0),
                MediaUrl0=message_data.get('MediaUrl0'),
                MediaContentType0=message_data.get('MediaContentType0')
            )
            
            correlation_id = payload.get('correlation_id')
            
            log_with_context(
                logger,
                logging.INFO,
                "Processing message task",
                message_sid=twilio_request.MessageSid,
                from_number=sanitize_phone_number(twilio_request.From),
                has_media=twilio_request.has_media,
                correlation_id=correlation_id
            )
            
            # Process the message
            success = await self.message_handler.process_message(twilio_request)
            
            result = {
                'success': success,
                'message_sid': twilio_request.MessageSid,
                'processed_at': payload.get('queued_at')
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "Message task completed",
                message_sid=twilio_request.MessageSid,
                success=success,
                correlation_id=correlation_id
            )
            
            return result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Message processing task failed",
                error=str(e),
                correlation_id=payload.get('correlation_id')
            )
            raise


class NotificationTaskHandler:
    """Handler for notification tasks."""
    
    async def handle_timeout_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle timeout notification task.
        
        Args:
            payload: Task payload containing notification data
            
        Returns:
            Notification result
        """
        try:
            from_number = payload.get('from_number')
            message_sid = payload.get('message_sid')
            
            if not from_number:
                raise ValueError("No from_number in payload")
            
            log_with_context(
                logger,
                logging.INFO,
                "Sending timeout notification",
                from_number=sanitize_phone_number(from_number),
                message_sid=message_sid,
                correlation_id=payload.get('correlation_id')
            )
            
            # Import here to avoid circular imports
            from app.services.twilio_response import TwilioResponseService
            from app.config import get_config
            
            config = get_config()
            twilio_service = TwilioResponseService(config)
            
            timeout_message = (
                "⏱️ *Processing Timeout*\n\n"
                "Your message is taking longer than expected to process. "
                "This might be due to high demand or complex content.\n\n"
                "Please try again in a few minutes."
            )
            
            # Send timeout notification
            success = await self._send_notification(
                twilio_service, 
                from_number, 
                timeout_message
            )
            
            result = {
                'success': success,
                'from_number': from_number,
                'message_sid': message_sid,
                'notification_type': 'timeout'
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "Timeout notification sent",
                success=success,
                from_number=sanitize_phone_number(from_number),
                correlation_id=payload.get('correlation_id')
            )
            
            return result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Timeout notification task failed",
                error=str(e),
                correlation_id=payload.get('correlation_id')
            )
            raise
    
    async def handle_error_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle error notification task.
        
        Args:
            payload: Task payload containing error notification data
            
        Returns:
            Notification result
        """
        try:
            from_number = payload.get('from_number')
            error_message = payload.get('error_message', 'An error occurred while processing your message.')
            message_sid = payload.get('message_sid')
            
            if not from_number:
                raise ValueError("No from_number in payload")
            
            log_with_context(
                logger,
                logging.INFO,
                "Sending error notification",
                from_number=sanitize_phone_number(from_number),
                message_sid=message_sid,
                correlation_id=payload.get('correlation_id')
            )
            
            # Import here to avoid circular imports
            from app.services.twilio_response import TwilioResponseService
            from app.config import get_config
            
            config = get_config()
            twilio_service = TwilioResponseService(config)
            
            # Send error notification
            success = await self._send_notification(
                twilio_service, 
                from_number, 
                error_message
            )
            
            result = {
                'success': success,
                'from_number': from_number,
                'message_sid': message_sid,
                'notification_type': 'error'
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "Error notification sent",
                success=success,
                from_number=sanitize_phone_number(from_number),
                correlation_id=payload.get('correlation_id')
            )
            
            return result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Error notification task failed",
                error=str(e),
                correlation_id=payload.get('correlation_id')
            )
            raise
    
    async def _send_notification(self, twilio_service, from_number: str, message: str) -> bool:
        """Send notification message with timeout protection."""
        try:
            # Ensure the from_number has the whatsapp: prefix
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            
            # Send message with timeout
            def send_message():
                return twilio_service.client.messages.create(
                    body=message,
                    from_=f"whatsapp:{twilio_service.config.twilio_phone_number}",
                    to=from_number
                )
            
            twilio_message = await asyncio.wait_for(
                asyncio.to_thread(send_message),
                timeout=5.0  # 5 second timeout
            )
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("Notification send timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False


class AnalyticsTaskHandler:
    """Handler for analytics and metrics tasks."""
    
    async def handle_interaction_recording(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle interaction recording task.
        
        Args:
            payload: Task payload containing interaction data
            
        Returns:
            Recording result
        """
        try:
            interaction_data = payload.get('interaction_data')
            if not interaction_data:
                raise ValueError("No interaction data in payload")
            
            log_with_context(
                logger,
                logging.INFO,
                "Recording interaction",
                phone_number=sanitize_phone_number(interaction_data.get('phone_number', '')),
                message_type=interaction_data.get('message_type'),
                correlation_id=payload.get('correlation_id')
            )
            
            # Import here to avoid circular imports
            from app.services.analytics import AnalyticsService
            from app.config import get_config
            
            config = get_config()
            analytics_service = AnalyticsService(config)
            
            # Record interaction
            success = await analytics_service.record_interaction(
                phone_number=interaction_data.get('phone_number'),
                message_type=interaction_data.get('message_type'),
                message_content=interaction_data.get('message_content'),
                analysis_result=interaction_data.get('analysis_result'),
                response_time=interaction_data.get('response_time'),
                error=interaction_data.get('error')
            )
            
            result = {
                'success': success,
                'interaction_type': interaction_data.get('message_type'),
                'recorded_at': payload.get('queued_at')
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "Interaction recorded",
                success=success,
                correlation_id=payload.get('correlation_id')
            )
            
            return result
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Interaction recording task failed",
                error=str(e),
                correlation_id=payload.get('correlation_id')
            )
            raise


# Task handler instances
message_handler = MessageProcessingTaskHandler()
notification_handler = NotificationTaskHandler()
analytics_handler = AnalyticsTaskHandler()


def register_default_handlers(task_processor):
    """Register default task handlers with the task processor."""
    # Message processing handlers
    task_processor.register_handler('process_message', message_handler.handle_message_processing)
    
    # Notification handlers
    task_processor.register_handler('timeout_notification', notification_handler.handle_timeout_notification)
    task_processor.register_handler('error_notification', notification_handler.handle_error_notification)
    
    # Analytics handlers
    task_processor.register_handler('record_interaction', analytics_handler.handle_interaction_recording)
    
    logger.info("Default task handlers registered")


async def create_message_processing_task(
    twilio_request: TwilioWebhookRequest,
    correlation_id: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL
) -> ProcessingTask:
    """
    Create a message processing task.
    
    Args:
        twilio_request: Twilio webhook request data
        correlation_id: Optional correlation ID for tracking
        priority: Task priority level
        
    Returns:
        ProcessingTask ready for queuing
    """
    from datetime import datetime, timezone
    
    payload = {
        'message_data': {
            'MessageSid': twilio_request.MessageSid,
            'From': twilio_request.From,
            'To': twilio_request.To,
            'Body': twilio_request.Body,
            'NumMedia': twilio_request.NumMedia,
            'MediaUrl0': twilio_request.MediaUrl0,
            'MediaContentType0': twilio_request.MediaContentType0
        },
        'correlation_id': correlation_id,
        'queued_at': datetime.now(timezone.utc).isoformat()
    }
    
    return ProcessingTask(
        task_id=f"msg_{twilio_request.MessageSid}",
        task_type='process_message',
        payload=payload,
        priority=priority,
        correlation_id=correlation_id,
        timeout=30  # 30 second timeout for message processing
    )


async def create_timeout_notification_task(
    from_number: str,
    message_sid: str,
    correlation_id: Optional[str] = None
) -> ProcessingTask:
    """
    Create a timeout notification task.
    
    Args:
        from_number: User's phone number
        message_sid: Original message SID
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        ProcessingTask ready for queuing
    """
    from datetime import datetime, timezone
    import uuid
    
    payload = {
        'from_number': from_number,
        'message_sid': message_sid,
        'correlation_id': correlation_id,
        'queued_at': datetime.now(timezone.utc).isoformat()
    }
    
    return ProcessingTask(
        task_id=f"timeout_{uuid.uuid4().hex[:8]}",
        task_type='timeout_notification',
        payload=payload,
        priority=TaskPriority.HIGH,  # High priority for user notifications
        correlation_id=correlation_id,
        timeout=10  # 10 second timeout for notifications
    )


async def create_interaction_recording_task(
    phone_number: str,
    message_type: str,
    message_content: Optional[str] = None,
    analysis_result=None,
    response_time: Optional[float] = None,
    error: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> ProcessingTask:
    """
    Create an interaction recording task.
    
    Args:
        phone_number: User's phone number
        message_type: Type of message (text, pdf, etc.)
        message_content: Message content (truncated)
        analysis_result: Analysis result if available
        response_time: Response time in seconds
        error: Error message if any
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        ProcessingTask ready for queuing
    """
    from datetime import datetime, timezone
    import uuid
    
    # Serialize analysis result if provided
    analysis_data = None
    if analysis_result:
        try:
            analysis_data = {
                'trust_score': getattr(analysis_result, 'trust_score', None),
                'classification_text': getattr(analysis_result, 'classification_text', None),
                'summary': getattr(analysis_result, 'summary', None)
            }
        except Exception:
            analysis_data = None
    
    payload = {
        'interaction_data': {
            'phone_number': phone_number,
            'message_type': message_type,
            'message_content': message_content,
            'analysis_result': analysis_data,
            'response_time': response_time,
            'error': error
        },
        'correlation_id': correlation_id,
        'queued_at': datetime.now(timezone.utc).isoformat()
    }
    
    return ProcessingTask(
        task_id=f"analytics_{uuid.uuid4().hex[:8]}",
        task_type='record_interaction',
        payload=payload,
        priority=TaskPriority.LOW,  # Low priority for analytics
        correlation_id=correlation_id,
        timeout=15  # 15 second timeout for analytics
    )