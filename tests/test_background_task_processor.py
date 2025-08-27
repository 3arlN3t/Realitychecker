"""
Unit tests for BackgroundTaskProcessor.

Tests the task queue system with priority levels, retry logic,
dead letter queue, and resource management.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from app.services.background_task_processor import (
    BackgroundTaskProcessor, ProcessingTask, TaskPriority, TaskStatus, 
    TaskQueueConfig, TaskResult, QueueStatus
)
from app.services.task_handlers import (
    create_message_processing_task, create_timeout_notification_task,
    create_interaction_recording_task
)
from app.models.data_models import TwilioWebhookRequest


class TestBackgroundTaskProcessor:
    """Test cases for BackgroundTaskProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a test task processor."""
        config = TaskQueueConfig(
            max_queue_size=10,
            worker_count=2,
            processing_timeout=1,
            retry_attempts=2,
            retry_backoff=0.1,
            dead_letter_threshold=3
        )
        
        processor = BackgroundTaskProcessor(config)
        
        # Mock Redis manager to avoid Redis dependency
        processor.redis_manager = Mock()
        processor.redis_manager.is_available.return_value = False
        
        return processor
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample processing task."""
        return ProcessingTask(
            task_id="test_task_1",
            task_type="test_handler",
            payload={"data": "test"},
            priority=TaskPriority.NORMAL
        )
    
    def test_task_serialization(self, sample_task):
        """Test task serialization and deserialization."""
        # Test to_dict
        task_dict = sample_task.to_dict()
        assert task_dict['task_id'] == "test_task_1"
        assert task_dict['task_type'] == "test_handler"
        assert task_dict['priority'] == TaskPriority.NORMAL.value
        assert 'created_at' in task_dict
        
        # Test from_dict
        restored_task = ProcessingTask.from_dict(task_dict)
        assert restored_task.task_id == sample_task.task_id
        assert restored_task.task_type == sample_task.task_type
        assert restored_task.priority == sample_task.priority
        assert restored_task.payload == sample_task.payload
    
    def test_config_loading(self):
        """Test configuration loading from environment."""
        with patch.dict('os.environ', {
            'TASK_QUEUE_MAX_SIZE': '500',
            'TASK_QUEUE_WORKERS': '10',
            'TASK_PROCESSING_TIMEOUT': '60'
        }):
            processor = BackgroundTaskProcessor()
            assert processor.config.max_queue_size == 500
            assert processor.config.worker_count == 10
            assert processor.config.processing_timeout == 60
    
    def test_handler_registration(self, processor):
        """Test task handler registration."""
        async def test_handler(payload):
            return {"result": "success"}
        
        processor.register_handler("test_type", test_handler)
        assert "test_type" in processor.task_handlers
        assert processor.task_handlers["test_type"] == test_handler
    
    @pytest.mark.asyncio
    async def test_processor_lifecycle(self, processor):
        """Test processor start and stop lifecycle."""
        assert not processor.is_running
        
        # Start processor
        await processor.start()
        assert processor.is_running
        assert len(processor.workers) == processor.config.worker_count
        
        # Stop processor
        await processor.stop()
        assert not processor.is_running
        assert processor.shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_task_queuing_redis_unavailable(self, processor, sample_task):
        """Test task queuing when Redis is unavailable (fallback mode)."""
        # Mock immediate processing
        processor._process_task_immediate = AsyncMock()
        
        task_id = await processor.queue_task(sample_task)
        
        assert task_id == sample_task.task_id
        assert processor.metrics['tasks_queued'] == 1
        processor._process_task_immediate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_queuing_redis_available(self, processor, sample_task):
        """Test task queuing when Redis is available."""
        # Mock Redis as available
        processor.redis_manager.is_available.return_value = True
        processor.redis_manager.execute_command = AsyncMock()
        processor._get_queue_depth = AsyncMock(return_value=0)
        processor._set_task_status = AsyncMock()
        
        task_id = await processor.queue_task(sample_task)
        
        assert task_id == sample_task.task_id
        assert processor.metrics['tasks_queued'] == 1
        
        # Verify Redis operations were called
        processor.redis_manager.execute_command.assert_called()
        processor._set_task_status.assert_called_with(sample_task.task_id, TaskStatus.PENDING)
    
    @pytest.mark.asyncio
    async def test_queue_full_rejection(self, processor, sample_task):
        """Test task rejection when queue is full."""
        processor._get_queue_depth = AsyncMock(return_value=processor.config.max_queue_size)
        
        with pytest.raises(Exception, match="Task queue is full"):
            await processor.queue_task(sample_task)
    
    @pytest.mark.asyncio
    async def test_task_processing_success(self, processor):
        """Test successful task processing."""
        # Register test handler
        async def success_handler(payload):
            return {"status": "completed", "data": payload}
        
        processor.register_handler("success_task", success_handler)
        
        task = ProcessingTask(
            task_id="success_test",
            task_type="success_task",
            payload={"test": "data"}
        )
        
        # Mock Redis operations
        processor._set_task_status = AsyncMock()
        processor._handle_task_completion = AsyncMock()
        
        await processor._process_task(task, "test_worker")
        
        # Verify task completion was handled
        processor._handle_task_completion.assert_called_once()
        call_args = processor._handle_task_completion.call_args[0][0]
        assert call_args.status == TaskStatus.COMPLETED
        assert call_args.task_id == "success_test"
    
    @pytest.mark.asyncio
    async def test_task_processing_failure(self, processor):
        """Test task processing failure and retry logic."""
        # Register failing handler
        async def failing_handler(payload):
            raise Exception("Task failed")
        
        processor.register_handler("failing_task", failing_handler)
        processor.queue_task = AsyncMock()  # Mock re-queuing for retry
        processor._move_to_dead_letter_queue = AsyncMock()
        processor._handle_task_completion = AsyncMock()
        
        task = ProcessingTask(
            task_id="failing_test",
            task_type="failing_task",
            payload={"test": "data"},
            max_attempts=2
        )
        
        # Mock Redis operations
        processor._set_task_status = AsyncMock()
        
        await processor._process_task(task, "test_worker")
        
        # Should retry (attempts < max_attempts)
        processor.queue_task.assert_called_once()
        assert task.attempts == 1
    
    @pytest.mark.asyncio
    async def test_task_timeout_handling(self, processor):
        """Test task timeout handling."""
        # Register slow handler
        async def slow_handler(payload):
            await asyncio.sleep(2.0)  # Longer than processor timeout
            return {"status": "completed"}
        
        processor.register_handler("slow_task", slow_handler)
        processor.queue_task = AsyncMock()  # Mock re-queuing for retry
        processor._set_task_status = AsyncMock()
        
        task = ProcessingTask(
            task_id="timeout_test",
            task_type="slow_task",
            payload={"test": "data"},
            timeout=0.1  # Very short timeout
        )
        
        await processor._process_task(task, "test_worker")
        
        # Should retry due to timeout
        processor.queue_task.assert_called_once()
        assert task.attempts == 1
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue(self, processor):
        """Test dead letter queue functionality."""
        # Register failing handler
        async def failing_handler(payload):
            raise Exception("Permanent failure")
        
        processor.register_handler("dead_letter_task", failing_handler)
        processor._move_to_dead_letter_queue = AsyncMock()
        processor._handle_task_completion = AsyncMock()
        processor._set_task_status = AsyncMock()
        
        task = ProcessingTask(
            task_id="dead_letter_test",
            task_type="dead_letter_task",
            payload={"test": "data"},
            max_attempts=1,
            attempts=1  # Already at max attempts
        )
        
        await processor._process_task(task, "test_worker")
        
        # Should move to dead letter queue
        processor._move_to_dead_letter_queue.assert_called_once()
        processor._handle_task_completion.assert_called_once()
        
        call_args = processor._handle_task_completion.call_args[0][0]
        assert call_args.status == TaskStatus.DEAD_LETTER
    
    @pytest.mark.asyncio
    async def test_queue_status(self, processor):
        """Test queue status reporting."""
        # Mock Redis operations
        processor.redis_manager.is_available.return_value = True
        processor.redis_manager.execute_command = AsyncMock(return_value=5)
        
        # Start processor to have active workers
        await processor.start()
        
        status = await processor.get_queue_status()
        
        assert isinstance(status, QueueStatus)
        assert status.active_workers > 0
        assert TaskPriority.HIGH in status.pending_tasks
        assert TaskPriority.NORMAL in status.pending_tasks
        assert TaskPriority.LOW in status.pending_tasks
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_priority_queue_keys(self, processor):
        """Test priority queue key generation."""
        high_key = processor._get_queue_key(TaskPriority.HIGH)
        normal_key = processor._get_queue_key(TaskPriority.NORMAL)
        low_key = processor._get_queue_key(TaskPriority.LOW)
        
        assert high_key == "task_queue:high"
        assert normal_key == "task_queue:normal"
        assert low_key == "task_queue:low"
    
    @pytest.mark.asyncio
    async def test_metrics_update(self, processor):
        """Test metrics updating."""
        initial_queued = processor.metrics['tasks_queued']
        initial_processed = processor.metrics['tasks_processed']
        
        # Simulate task queuing
        processor.metrics['tasks_queued'] += 1
        assert processor.metrics['tasks_queued'] == initial_queued + 1
        
        # Simulate task processing
        processor.metrics['tasks_processed'] += 1
        processor._update_average_processing_time(0.5)
        
        assert processor.metrics['tasks_processed'] == initial_processed + 1
        assert processor.metrics['average_processing_time'] > 0


class TestTaskHandlers:
    """Test cases for task handlers."""
    
    def test_create_message_processing_task(self):
        """Test message processing task creation."""
        twilio_request = TwilioWebhookRequest(
            MessageSid="test_sid",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Test message",
            NumMedia=0
        )
        
        task = asyncio.run(create_message_processing_task(
            twilio_request, 
            "test_correlation_id", 
            TaskPriority.HIGH
        ))
        
        assert task.task_id == "msg_test_sid"
        assert task.task_type == "process_message"
        assert task.priority == TaskPriority.HIGH
        assert task.correlation_id == "test_correlation_id"
        assert task.payload['message_data']['MessageSid'] == "test_sid"
        assert task.payload['message_data']['From'] == "whatsapp:+1234567890"
        assert task.payload['message_data']['Body'] == "Test message"
    
    def test_create_timeout_notification_task(self):
        """Test timeout notification task creation."""
        task = asyncio.run(create_timeout_notification_task(
            "whatsapp:+1234567890",
            "test_message_sid",
            "test_correlation_id"
        ))
        
        assert task.task_type == "timeout_notification"
        assert task.priority == TaskPriority.HIGH
        assert task.correlation_id == "test_correlation_id"
        assert task.payload['from_number'] == "whatsapp:+1234567890"
        assert task.payload['message_sid'] == "test_message_sid"
        assert task.timeout == 10
    
    def test_create_interaction_recording_task(self):
        """Test interaction recording task creation."""
        task = asyncio.run(create_interaction_recording_task(
            "whatsapp:+1234567890",
            "text",
            "Test message content",
            None,  # No analysis result
            1.5,   # Response time
            None,  # No error
            "test_correlation_id"
        ))
        
        assert task.task_type == "record_interaction"
        assert task.priority == TaskPriority.LOW
        assert task.correlation_id == "test_correlation_id"
        
        interaction_data = task.payload['interaction_data']
        assert interaction_data['phone_number'] == "whatsapp:+1234567890"
        assert interaction_data['message_type'] == "text"
        assert interaction_data['message_content'] == "Test message content"
        assert interaction_data['response_time'] == 1.5
        assert interaction_data['error'] is None
    
    def test_create_interaction_recording_task_with_analysis(self):
        """Test interaction recording task creation with analysis result."""
        # Mock analysis result
        analysis_result = Mock()
        analysis_result.trust_score = 85
        analysis_result.classification_text = "Legitimate"
        analysis_result.summary = "This appears to be a legitimate job posting"
        
        task = asyncio.run(create_interaction_recording_task(
            "whatsapp:+1234567890",
            "text",
            "Job posting content",
            analysis_result,
            2.3,
            None,
            "test_correlation_id"
        ))
        
        interaction_data = task.payload['interaction_data']
        analysis_data = interaction_data['analysis_result']
        
        assert analysis_data['trust_score'] == 85
        assert analysis_data['classification_text'] == "Legitimate"
        assert analysis_data['summary'] == "This appears to be a legitimate job posting"


class TestTaskProcessorIntegration:
    """Integration tests for task processor with handlers."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_message_processing(self):
        """Test end-to-end message processing workflow."""
        # Create processor with test config
        config = TaskQueueConfig(
            max_queue_size=10,
            worker_count=1,
            processing_timeout=5,
            retry_attempts=1
        )
        
        processor = BackgroundTaskProcessor(config)
        
        # Mock Redis as unavailable for immediate processing
        processor.redis_manager = Mock()
        processor.redis_manager.is_available.return_value = False
        
        # Mock message handler
        message_processed = False
        
        async def mock_message_handler(payload):
            nonlocal message_processed
            message_processed = True
            return {"success": True, "message_sid": payload['message_data']['MessageSid']}
        
        processor.register_handler("process_message", mock_message_handler)
        
        # Create message processing task
        twilio_request = TwilioWebhookRequest(
            MessageSid="integration_test_sid",
            From="whatsapp:+1234567890",
            To="whatsapp:+0987654321",
            Body="Integration test message",
            NumMedia=0
        )
        
        task = await create_message_processing_task(twilio_request, "integration_test")
        
        # Queue and process task
        task_id = await processor.queue_task(task)
        
        # Wait a moment for immediate processing
        await asyncio.sleep(0.1)
        
        assert task_id == "msg_integration_test_sid"
        assert message_processed
        
        # Cleanup
        if processor.is_running:
            await processor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])