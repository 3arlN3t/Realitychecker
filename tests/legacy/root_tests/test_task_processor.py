#!/usr/bin/env python3
"""
Test script for the BackgroundTaskProcessor implementation.

This script tests the task queue system with priority levels, retry logic,
and dead letter queue functionality.
"""

import asyncio
import json
import time
from datetime import datetime, timezone

from app.services.background_task_processor import (
    BackgroundTaskProcessor, ProcessingTask, TaskPriority, TaskStatus, TaskQueueConfig
)
from app.services.redis_connection_manager import init_redis_manager
from app.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


async def test_task_handler(payload):
    """Test task handler that simulates message processing."""
    task_type = payload.get('task_type', 'unknown')
    delay = payload.get('delay', 0.1)
    should_fail = payload.get('should_fail', False)
    
    logger.info(f"Processing {task_type} task with {delay}s delay")
    
    # Simulate processing time
    await asyncio.sleep(delay)
    
    if should_fail:
        raise Exception(f"Simulated failure for {task_type} task")
    
    return {
        'processed_at': datetime.now(timezone.utc).isoformat(),
        'task_type': task_type,
        'success': True
    }


async def test_timeout_handler(payload):
    """Test handler that times out."""
    delay = payload.get('delay', 5.0)
    logger.info(f"Starting timeout test with {delay}s delay")
    
    # This will timeout if delay > task timeout
    await asyncio.sleep(delay)
    
    return {'completed': True}


async def main():
    """Main test function."""
    logger.info("🚀 Starting BackgroundTaskProcessor tests...")
    
    try:
        # Initialize Redis connection manager
        await init_redis_manager()
        logger.info("✅ Redis connection manager initialized")
        
        # Create task processor with test configuration
        config = TaskQueueConfig(
            max_queue_size=100,
            worker_count=3,
            processing_timeout=2,
            retry_attempts=2,
            retry_backoff=1.0,
            dead_letter_threshold=3
        )
        
        processor = BackgroundTaskProcessor(config)
        
        # Register test handlers
        processor.register_handler('test_task', test_task_handler)
        processor.register_handler('timeout_task', test_timeout_handler)
        
        # Start the processor
        await processor.start()
        logger.info("✅ Task processor started")
        
        # Test 1: Basic task processing
        logger.info("\n📋 Test 1: Basic task processing")
        
        tasks = []
        for i in range(5):
            task = ProcessingTask(
                task_id=f"test_{i}",
                task_type='test_task',
                payload={
                    'task_type': f'basic_test_{i}',
                    'delay': 0.2,
                    'should_fail': False
                },
                priority=TaskPriority.NORMAL
            )
            task_id = await processor.queue_task(task)
            tasks.append(task_id)
            logger.info(f"Queued task: {task_id}")
        
        # Wait for tasks to complete
        await asyncio.sleep(2.0)
        
        # Check queue status
        status = await processor.get_queue_status()
        logger.info(f"Queue status: {status.completed_tasks} completed, {status.failed_tasks} failed")
        
        # Test 2: Priority handling
        logger.info("\n🔥 Test 2: Priority handling")
        
        # Queue low priority tasks first
        for i in range(3):
            task = ProcessingTask(
                task_id=f"low_{i}",
                task_type='test_task',
                payload={
                    'task_type': f'low_priority_{i}',
                    'delay': 0.5,
                    'should_fail': False
                },
                priority=TaskPriority.LOW
            )
            await processor.queue_task(task)
        
        # Queue high priority tasks
        for i in range(2):
            task = ProcessingTask(
                task_id=f"high_{i}",
                task_type='test_task',
                payload={
                    'task_type': f'high_priority_{i}',
                    'delay': 0.1,
                    'should_fail': False
                },
                priority=TaskPriority.HIGH
            )
            await processor.queue_task(task)
        
        # Wait for processing
        await asyncio.sleep(3.0)
        
        # Test 3: Retry logic
        logger.info("\n🔄 Test 3: Retry logic")
        
        failing_task = ProcessingTask(
            task_id="failing_task",
            task_type='test_task',
            payload={
                'task_type': 'failing_test',
                'delay': 0.1,
                'should_fail': True
            },
            priority=TaskPriority.NORMAL,
            max_attempts=3
        )
        
        await processor.queue_task(failing_task)
        
        # Wait for retries to complete
        await asyncio.sleep(5.0)
        
        # Test 4: Timeout handling
        logger.info("\n⏱️ Test 4: Timeout handling")
        
        timeout_task = ProcessingTask(
            task_id="timeout_task",
            task_type='timeout_task',
            payload={
                'delay': 5.0  # This will timeout (processor timeout is 2s)
            },
            priority=TaskPriority.NORMAL,
            timeout=2
        )
        
        await processor.queue_task(timeout_task)
        
        # Wait for timeout
        await asyncio.sleep(4.0)
        
        # Test 5: Queue status and metrics
        logger.info("\n📊 Test 5: Queue status and metrics")
        
        final_status = await processor.get_queue_status()
        logger.info(f"Final queue status:")
        logger.info(f"  - Completed tasks: {final_status.completed_tasks}")
        logger.info(f"  - Failed tasks: {final_status.failed_tasks}")
        logger.info(f"  - Dead letter tasks: {final_status.dead_letter_tasks}")
        logger.info(f"  - Active workers: {final_status.active_workers}")
        logger.info(f"  - Average processing time: {final_status.average_processing_time:.3f}s")
        
        # Test 6: Load test
        logger.info("\n🚀 Test 6: Load test")
        
        start_time = time.time()
        load_tasks = []
        
        for i in range(20):
            task = ProcessingTask(
                task_id=f"load_{i}",
                task_type='test_task',
                payload={
                    'task_type': f'load_test_{i}',
                    'delay': 0.1,
                    'should_fail': i % 10 == 0  # 10% failure rate
                },
                priority=TaskPriority.NORMAL if i % 2 == 0 else TaskPriority.HIGH
            )
            task_id = await processor.queue_task(task)
            load_tasks.append(task_id)
        
        # Wait for all tasks to complete
        await asyncio.sleep(8.0)
        
        load_time = time.time() - start_time
        final_status = await processor.get_queue_status()
        
        logger.info(f"Load test completed in {load_time:.2f}s")
        logger.info(f"Throughput: {len(load_tasks) / load_time:.2f} tasks/second")
        
        # Stop the processor
        await processor.stop()
        logger.info("✅ Task processor stopped")
        
        logger.info("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup Redis
        from app.services.redis_connection_manager import cleanup_redis_manager
        await cleanup_redis_manager()
        logger.info("✅ Redis connection manager cleaned up")


if __name__ == "__main__":
    asyncio.run(main())