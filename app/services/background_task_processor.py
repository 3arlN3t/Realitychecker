"""
Background Task Processor for asynchronous message processing.

This module provides the BackgroundTaskProcessor class that implements a robust
task queue system with priority levels, retry logic, dead letter queue, and
resource management for the Reality Checker WhatsApp bot.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta, timezone
import logging
from concurrent.futures import ThreadPoolExecutor

from app.services.redis_connection_manager import get_redis_manager, RedisConnectionManager
from app.services.performance_monitor import get_performance_monitor
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.config import get_config

logger = get_logger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3


class TaskStatus(Enum):
    """Task processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class TaskQueueConfig:
    """Configuration for task queue system."""
    max_queue_size: int = 1000
    worker_count: int = 5
    batch_size: int = 10
    processing_timeout: int = 30
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    dead_letter_threshold: int = 5
    priority_levels: int = 3
    queue_check_interval: float = 0.1
    health_check_interval: int = 30
    metrics_interval: int = 60


@dataclass
class ProcessingTask:
    """Task data structure for background processing."""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    correlation_id: Optional[str] = None
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        if self.scheduled_at:
            data['scheduled_at'] = self.scheduled_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingTask':
        """Create task from dictionary."""
        data = data.copy()
        data['priority'] = TaskPriority(data['priority'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('scheduled_at'):
            data['scheduled_at'] = datetime.fromisoformat(data['scheduled_at'])
        return cls(**data)


@dataclass
class TaskResult:
    """Result of task processing."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class QueueStatus:
    """Current status of task queues."""
    pending_tasks: Dict[TaskPriority, int] = field(default_factory=dict)
    processing_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    dead_letter_tasks: int = 0
    active_workers: int = 0
    queue_depth: int = 0
    average_processing_time: float = 0.0
    last_processed: Optional[datetime] = None


class BackgroundTaskProcessor:
    """
    Background task processor with priority queues, retry logic, and dead letter queue.
    
    This class provides a robust task processing system that can handle message
    processing asynchronously while maintaining high availability and reliability.
    """
    
    def __init__(self, config: Optional[TaskQueueConfig] = None):
        """
        Initialize the background task processor.
        
        Args:
            config: Task queue configuration
        """
        self.config = config or self._load_config()
        self.redis_manager = get_redis_manager()
        self.performance_monitor = get_performance_monitor()
        
        # Task handlers registry
        self.task_handlers: Dict[str, Callable] = {}
        
        # Worker management
        self.workers: List[asyncio.Task] = []
        self.worker_pool = ThreadPoolExecutor(max_workers=self.config.worker_count)
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Metrics and monitoring
        self.metrics = {
            'tasks_queued': 0,
            'tasks_processed': 0,
            'tasks_failed': 0,
            'tasks_retried': 0,
            'average_processing_time': 0.0,
            'queue_depth': 0
        }
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        logger.info("BackgroundTaskProcessor initialized")
    
    def _load_config(self) -> TaskQueueConfig:
        """Load configuration from environment variables."""
        import os
        
        config = TaskQueueConfig()
        config.max_queue_size = int(os.getenv('TASK_QUEUE_MAX_SIZE', '1000'))
        config.worker_count = int(os.getenv('TASK_QUEUE_WORKERS', '5'))
        config.batch_size = int(os.getenv('TASK_QUEUE_BATCH_SIZE', '10'))
        config.processing_timeout = int(os.getenv('TASK_PROCESSING_TIMEOUT', '30'))
        config.retry_attempts = int(os.getenv('TASK_RETRY_ATTEMPTS', '3'))
        config.retry_backoff = float(os.getenv('TASK_RETRY_BACKOFF', '2.0'))
        config.dead_letter_threshold = int(os.getenv('TASK_DEAD_LETTER_THRESHOLD', '5'))
        
        return config
    
    def register_handler(self, task_type: str, handler: Callable):
        """
        Register a task handler for a specific task type.
        
        Args:
            task_type: Type of task to handle
            handler: Async function to handle the task
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def start(self):
        """Start the background task processor."""
        if self.is_running:
            logger.warning("BackgroundTaskProcessor is already running")
            return
        
        logger.info("Starting BackgroundTaskProcessor...")
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.config.worker_count):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker_task)
        
        # Start monitoring tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())
        
        logger.info(f"✅ BackgroundTaskProcessor started with {self.config.worker_count} workers")
    
    async def stop(self):
        """Stop the background task processor gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping BackgroundTaskProcessor...")
        self.is_running = False
        self.shutdown_event.set()
        
        # Cancel monitoring tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()
        
        # Wait for workers to finish current tasks
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Shutdown thread pool
        self.worker_pool.shutdown(wait=True)
        
        logger.info("✅ BackgroundTaskProcessor stopped")
    
    async def queue_task(self, task: ProcessingTask) -> str:
        """
        Queue a task for background processing.
        
        Args:
            task: Task to queue
            
        Returns:
            Task ID
            
        Raises:
            Exception: If queue is full or Redis is unavailable
        """
        correlation_id = task.correlation_id or get_correlation_id()
        
        try:
            # Check queue depth
            current_depth = await self._get_queue_depth()
            if current_depth >= self.config.max_queue_size:
                raise Exception(f"Task queue is full (depth: {current_depth})")
            
            # Set task ID if not provided
            if not task.task_id:
                task.task_id = str(uuid.uuid4())
            
            # Set correlation ID
            task.correlation_id = correlation_id
            
            # Serialize task
            task_data = json.dumps(task.to_dict())
            
            # Queue task in Redis with priority
            queue_key = self._get_queue_key(task.priority)
            
            if self.redis_manager.is_available():
                # Use Redis for persistent queuing
                await self.redis_manager.execute_command('lpush', queue_key, task_data)
                
                # Set task status
                await self._set_task_status(task.task_id, TaskStatus.PENDING)
                
                # Update metrics
                await self.redis_manager.execute_command('incr', 'task_queue:metrics:queued')
            else:
                # Fallback to in-memory processing if Redis is unavailable
                logger.warning("Redis unavailable, processing task immediately")
                asyncio.create_task(self._process_task_immediate(task))
            
            # Update local metrics
            self.metrics['tasks_queued'] += 1
            self.metrics['queue_depth'] = current_depth + 1
            
            log_with_context(
                logger,
                logging.INFO,
                "Task queued",
                task_id=task.task_id,
                task_type=task.task_type,
                priority=task.priority.name,
                queue_depth=current_depth + 1,
                correlation_id=correlation_id
            )
            
            return task.task_id
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to queue task",
                task_type=task.task_type,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop for processing tasks."""
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Get next task from queues (priority order)
                task = await self._get_next_task()
                
                if task:
                    await self._process_task(task, worker_id)
                else:
                    # No tasks available, wait briefly
                    await asyncio.sleep(self.config.queue_check_interval)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)  # Brief pause on error
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_task(self) -> Optional[ProcessingTask]:
        """Get the next task from priority queues."""
        if not self.redis_manager.is_available():
            return None
        
        # Check queues in priority order (HIGH -> NORMAL -> LOW)
        for priority in [TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue_key = self._get_queue_key(priority)
            
            try:
                # Pop task from queue
                task_data = await self.redis_manager.execute_command('rpop', queue_key)
                
                if task_data:
                    task_dict = json.loads(task_data)
                    task = ProcessingTask.from_dict(task_dict)
                    
                    # Check if task is scheduled for future execution
                    if task.scheduled_at and task.scheduled_at > datetime.now(timezone.utc):
                        # Re-queue for later
                        await self.redis_manager.execute_command('lpush', queue_key, task_data)
                        continue
                    
                    return task
                    
            except Exception as e:
                logger.warning(f"Error getting task from {priority.name} queue: {e}")
        
        return None
    
    async def _process_task(self, task: ProcessingTask, worker_id: str):
        """Process a single task with error handling and retry logic."""
        start_time = time.time()
        correlation_id = task.correlation_id or get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Processing task",
            task_id=task.task_id,
            task_type=task.task_type,
            worker_id=worker_id,
            attempt=task.attempts + 1,
            correlation_id=correlation_id
        )
        
        try:
            # Update task status
            await self._set_task_status(task.task_id, TaskStatus.PROCESSING)
            
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Process task with timeout
            result = await asyncio.wait_for(
                handler(task.payload),
                timeout=task.timeout
            )
            
            # Task completed successfully
            processing_time = time.time() - start_time
            
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                processing_time=processing_time
            )
            
            await self._handle_task_completion(task_result)
            
            # Update metrics
            self.metrics['tasks_processed'] += 1
            self._update_average_processing_time(processing_time)
            
            log_with_context(
                logger,
                logging.INFO,
                "Task completed",
                task_id=task.task_id,
                processing_time=round(processing_time, 3),
                correlation_id=correlation_id
            )
            
        except asyncio.TimeoutError:
            await self._handle_task_timeout(task, correlation_id)
        except Exception as e:
            await self._handle_task_error(task, e, correlation_id)
    
    async def _handle_task_timeout(self, task: ProcessingTask, correlation_id: str):
        """Handle task timeout."""
        log_with_context(
            logger,
            logging.WARNING,
            "Task timed out",
            task_id=task.task_id,
            timeout=task.timeout,
            correlation_id=correlation_id
        )
        
        error_msg = f"Task timed out after {task.timeout} seconds"
        await self._handle_task_failure(task, error_msg, correlation_id)
    
    async def _handle_task_error(self, task: ProcessingTask, error: Exception, correlation_id: str):
        """Handle task processing error."""
        log_with_context(
            logger,
            logging.ERROR,
            "Task processing error",
            task_id=task.task_id,
            error=str(error),
            correlation_id=correlation_id
        )
        
        await self._handle_task_failure(task, str(error), correlation_id)
    
    async def _handle_task_failure(self, task: ProcessingTask, error_msg: str, correlation_id: str):
        """Handle task failure with retry logic."""
        task.attempts += 1
        
        if task.attempts < task.max_attempts:
            # Retry task with exponential backoff
            delay = self.config.retry_backoff ** (task.attempts - 1)
            task.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            
            # Re-queue task for retry
            await self.queue_task(task)
            
            self.metrics['tasks_retried'] += 1
            
            log_with_context(
                logger,
                logging.INFO,
                "Task queued for retry",
                task_id=task.task_id,
                attempt=task.attempts,
                retry_delay=delay,
                correlation_id=correlation_id
            )
        else:
            # Move to dead letter queue
            await self._move_to_dead_letter_queue(task, error_msg)
            
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.DEAD_LETTER,
                error=error_msg
            )
            
            await self._handle_task_completion(task_result)
            
            self.metrics['tasks_failed'] += 1
            
            log_with_context(
                logger,
                logging.ERROR,
                "Task moved to dead letter queue",
                task_id=task.task_id,
                max_attempts=task.max_attempts,
                correlation_id=correlation_id
            )
    
    async def _move_to_dead_letter_queue(self, task: ProcessingTask, error_msg: str):
        """Move failed task to dead letter queue."""
        if not self.redis_manager.is_available():
            return
        
        dead_letter_data = {
            'task': task.to_dict(),
            'error': error_msg,
            'failed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await self.redis_manager.execute_command(
            'lpush',
            'task_queue:dead_letter',
            json.dumps(dead_letter_data)
        )
        
        await self._set_task_status(task.task_id, TaskStatus.DEAD_LETTER)
    
    async def _process_task_immediate(self, task: ProcessingTask):
        """Process task immediately when Redis is unavailable."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                await handler(task.payload)
                logger.info(f"Task {task.task_id} processed immediately (Redis fallback)")
            else:
                logger.error(f"No handler for task type {task.task_type}")
        except Exception as e:
            logger.error(f"Immediate task processing failed: {e}")
    
    async def _set_task_status(self, task_id: str, status: TaskStatus):
        """Set task status in Redis."""
        if self.redis_manager.is_available():
            await self.redis_manager.execute_command(
                'setex',
                f'task_queue:status:{task_id}',
                3600,  # 1 hour TTL
                status.value
            )
    
    async def _handle_task_completion(self, result: TaskResult):
        """Handle task completion."""
        # Store result in Redis if available
        if self.redis_manager.is_available():
            result_data = {
                'status': result.status.value,
                'result': result.result,
                'error': result.error,
                'processing_time': result.processing_time,
                'completed_at': result.completed_at.isoformat()
            }
            
            await self.redis_manager.execute_command(
                'setex',
                f'task_queue:result:{result.task_id}',
                3600,  # 1 hour TTL
                json.dumps(result_data)
            )
    
    def _get_queue_key(self, priority: TaskPriority) -> str:
        """Get Redis key for priority queue."""
        return f"task_queue:{priority.name.lower()}"
    
    async def _get_queue_depth(self) -> int:
        """Get total queue depth across all priorities."""
        if not self.redis_manager.is_available():
            return 0
        
        total_depth = 0
        for priority in TaskPriority:
            queue_key = self._get_queue_key(priority)
            depth = await self.redis_manager.execute_command('llen', queue_key)
            total_depth += depth or 0
        
        return total_depth
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric."""
        current_avg = self.metrics['average_processing_time']
        processed_count = self.metrics['tasks_processed']
        
        if processed_count == 1:
            self.metrics['average_processing_time'] = processing_time
        else:
            # Exponential moving average
            self.metrics['average_processing_time'] = (current_avg * 0.9) + (processing_time * 0.1)
    
    async def _health_check_loop(self):
        """Background health monitoring loop."""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5.0)
    
    async def _perform_health_check(self):
        """Perform health check on task processing system."""
        try:
            # Check queue depths
            queue_depth = await self._get_queue_depth()
            self.metrics['queue_depth'] = queue_depth
            
            # Check for stuck tasks (processing for too long)
            # This would require additional Redis tracking
            
            # Log health status
            if queue_depth > self.config.max_queue_size * 0.8:
                logger.warning(f"Task queue depth high: {queue_depth}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _metrics_loop(self):
        """Background metrics collection loop."""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.config.metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10.0)
    
    async def _collect_metrics(self):
        """Collect and report enhanced metrics."""
        try:
            # Get current queue status
            queue_status = await self.get_queue_status()
            
            # Calculate worker utilization
            active_workers = len([w for w in self.workers if not w.done()])
            worker_utilization = (active_workers / max(1, self.config.worker_count)) * 100
            
            # Detect backpressure conditions
            backpressure_detected = (
                queue_status.queue_depth > self.config.max_queue_size * 0.8 or
                worker_utilization > 90.0 or
                queue_status.average_processing_time > self.config.processing_timeout * 0.8
            )
            
            # Create enhanced task queue metrics
            from app.services.performance_monitor import TaskQueueMetrics
            task_metrics = TaskQueueMetrics(
                total_depth=queue_status.queue_depth,
                high_priority_depth=queue_status.pending_tasks.get(TaskPriority.HIGH, 0),
                normal_priority_depth=queue_status.pending_tasks.get(TaskPriority.NORMAL, 0),
                low_priority_depth=queue_status.pending_tasks.get(TaskPriority.LOW, 0),
                processing_tasks=queue_status.processing_tasks,
                failed_tasks=queue_status.failed_tasks,
                average_processing_time=queue_status.average_processing_time,
                backpressure_detected=backpressure_detected,
                worker_utilization=worker_utilization,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Record enhanced task queue metrics
            self.performance_monitor.record_task_queue_metrics(task_metrics)
            
            # Record individual metrics for backward compatibility
            self.performance_monitor.record_metric(
                "task_queue_depth",
                self.metrics['queue_depth'],
                "count"
            )
            
            self.performance_monitor.record_metric(
                "task_processing_time_avg",
                self.metrics['average_processing_time'],
                "seconds"
            )
            
            self.performance_monitor.record_metric(
                "tasks_processed_total",
                self.metrics['tasks_processed'],
                "count"
            )
            
            # Record backpressure detection
            if backpressure_detected:
                self.performance_monitor.record_metric(
                    "task_queue_backpressure_detected",
                    1,
                    "count",
                    {
                        "queue_depth": str(queue_status.queue_depth),
                        "worker_utilization": str(worker_utilization),
                        "avg_processing_time": str(queue_status.average_processing_time)
                    }
                )
            
        except Exception as e:
            logger.error(f"Enhanced metrics collection failed: {e}")
    
    async def get_queue_status(self) -> QueueStatus:
        """
        Get current queue status.
        
        Returns:
            Current queue status information
        """
        status = QueueStatus()
        
        try:
            if self.redis_manager.is_available():
                # Get queue depths by priority
                for priority in TaskPriority:
                    queue_key = self._get_queue_key(priority)
                    depth = await self.redis_manager.execute_command('llen', queue_key)
                    status.pending_tasks[priority] = depth or 0
                
                # Get processing count (approximate)
                status.processing_tasks = len([w for w in self.workers if not w.done()])
            
            # Update from local metrics
            status.queue_depth = self.metrics['queue_depth']
            status.completed_tasks = self.metrics['tasks_processed']
            status.failed_tasks = self.metrics['tasks_failed']
            status.active_workers = len([w for w in self.workers if not w.done()])
            status.average_processing_time = self.metrics['average_processing_time']
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
        
        return status


# Global task processor instance
_task_processor: Optional[BackgroundTaskProcessor] = None


def get_task_processor() -> BackgroundTaskProcessor:
    """Get global task processor instance."""
    global _task_processor
    if _task_processor is None:
        _task_processor = BackgroundTaskProcessor()
    return _task_processor


async def init_task_processor() -> BackgroundTaskProcessor:
    """Initialize global task processor."""
    processor = get_task_processor()
    await processor.start()
    return processor


async def cleanup_task_processor():
    """Cleanup global task processor."""
    global _task_processor
    if _task_processor:
        await _task_processor.stop()
        _task_processor = None