"""
Unit tests for webhook optimization components.

Tests the optimized webhook handler components to ensure they meet
the sub-2-second response time requirements.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.api.optimized_webhook import OptimizedWebhookProcessor, ValidationCacheEntry
from app.services.redis_connection_manager import RedisConnectionManager
from app.services.performance_monitor import PerformanceMonitor
from app.services.background_task_processor import BackgroundTaskProcessor


class TestOptimizedWebhookProcessor:
    """Test cases for OptimizedWebhookProcessor."""
    
    @pytest.fixture
    def mock_redis_manager(self):
        """Mock Redis connection manager."""
        mock = Mock(spec=RedisConnectionManager)
        mock.is_available.return_value = True
        mock.execute_command = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_task_processor(self):
        """Mock background task processor."""
        mock = Mock(spec=BackgroundTaskProcessor)
        mock.queue_task = AsyncMock(return_value="task_123")
        return mock
    
    @pytest.fixture
    def processor(self, mock_redis_manager, mock_task_processor):
        """Create OptimizedWebhookProcessor instance with mocks."""
        processor = OptimizedWebhookProcessor()
        processor.redis_manager = mock_redis_manager
        processor.task_processor = mock_task_processor
        return processor
    
    @pytest.mark.asyncio
    async def test_validation_cache_memory_fallback(self, processor):
        """Test validation cache falls back to memory when Redis is unavailable."""
        # Setup
        cache_key = "test_key"
        entry = ValidationCacheEntry(True, datetime.now())
        
        # Mock Redis failure
        processor.redis_manager.execute_command.side_effect = Exception("Redis error")
        
        # Cache entry in memory
        processor.validation_cache[cache_key] = entry
        
        # Test retrieval
        result = await processor.get_cached_validation(cache_key)
        
        assert result is not None
        assert result.is_valid == True
    
    @pytest.mark.asyncio
    async def test_validation_cache_redis_timeout(self, processor):
        """Test validation cache handles Redis timeouts gracefully."""
        # Setup
        cache_key = "test_key"
        
        # Mock Redis timeout
        async def slow_redis_call(*args, **kwargs):
            await asyncio.sleep(0.1)  # Longer than timeout
            return None
        
        processor.redis_manager.execute_command.side_effect = slow_redis_call
        
        # Test with timeout
        start_time = time.time()
        result = await processor.get_cached_validation(cache_key)
        elapsed = time.time() - start_time
        
        # Should timeout quickly and return None
        assert result is None
        assert elapsed < 0.05  # Should be much faster than Redis call
    
    @pytest.mark.asyncio
    async def test_fast_signature_validation_timeout(self, processor):
        """Test signature validation respects timeout limits."""
        from fastapi import Request
        
        # Mock request and config
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "test_signature"
        mock_request.url = "http://test.com/webhook"
        
        # Mock config object
        config = Mock()
        config.webhook_validation = True
        config.twilio_auth_token = "test_token"
        
        body_data = {"test": "data"}
        
        # Mock slow validation
        async def slow_validation(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return True
        
        processor._validate_signature_sync = slow_validation
        
        # Test with timeout
        start_time = time.time()
        result = await processor.fast_signature_validation(mock_request, body_data, config)
        elapsed = time.time() - start_time
        
        # Should timeout and allow request
        assert result == True  # Allows request on timeout
        assert elapsed < 0.1  # Should respect timeout
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, processor):
        """Test cache key generation is consistent and unique."""
        # Test same inputs produce same key
        key1 = processor.create_cache_key("MSG123", "whatsapp:+1234567890", "hash123")
        key2 = processor.create_cache_key("MSG123", "whatsapp:+1234567890", "hash123")
        assert key1 == key2
        
        # Test different inputs produce different keys
        key3 = processor.create_cache_key("MSG456", "whatsapp:+1234567890", "hash123")
        assert key1 != key3
        
        key4 = processor.create_cache_key("MSG123", "whatsapp:+0987654321", "hash123")
        assert key1 != key4
        
        key5 = processor.create_cache_key("MSG123", "whatsapp:+1234567890", "hash456")
        assert key1 != key5


class TestWebhookPerformanceRequirements:
    """Test webhook performance requirements."""
    
    @pytest.mark.asyncio
    async def test_validation_cache_performance(self):
        """Test validation caching reduces processing time."""
        processor = OptimizedWebhookProcessor()
        
        # Mock Redis to be available but slow
        processor.redis_manager = Mock()
        processor.redis_manager.is_available.return_value = True
        
        async def slow_redis_get(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms delay to make difference more obvious
            return None
        
        processor.redis_manager.execute_command.side_effect = slow_redis_get
        
        cache_key = "test_performance"
        
        # First call - should be slower (cache miss)
        start_time = time.time()
        result1 = await processor.get_cached_validation(cache_key)
        first_call_time = time.time() - start_time
        
        # Add to memory cache
        entry = ValidationCacheEntry(True, datetime.now())
        processor.validation_cache[cache_key] = entry
        
        # Second call - should be faster (cache hit)
        start_time = time.time()
        result2 = await processor.get_cached_validation(cache_key)
        second_call_time = time.time() - start_time
        
        # Cache hit should be significantly faster
        assert result2 is not None
        # The cache hit should be much faster since it doesn't hit Redis timeout
        assert second_call_time < 0.03  # Less than 30ms (much faster than Redis)
        # Just verify the first call took some time (due to Redis timeout)
        print(f"First call: {first_call_time:.3f}s, Second call: {second_call_time:.3f}s")
        assert first_call_time > 0.01  # First call should take some time
    
    @pytest.mark.asyncio
    async def test_signature_validation_timeout_protection(self):
        """Test signature validation timeout protection."""
        from app.api.optimized_webhook import SIGNATURE_VALIDATION_TIMEOUT
        
        processor = OptimizedWebhookProcessor()
        
        # Mock slow signature validation
        async def slow_validation(*args, **kwargs):
            await asyncio.sleep(SIGNATURE_VALIDATION_TIMEOUT * 2)  # Exceed timeout
            return True
        
        processor._validate_signature_sync = slow_validation
        
        # Test timeout protection
        start_time = time.time()
        result = await processor.fast_signature_validation(Mock(), {}, Mock())
        elapsed = time.time() - start_time
        
        # Should timeout and return True (allow request)
        assert result == True
        assert elapsed <= SIGNATURE_VALIDATION_TIMEOUT * 1.5  # Some tolerance for test execution
    
    def test_performance_constants_meet_requirements(self):
        """Test that performance constants meet the requirements."""
        from app.api.optimized_webhook import (
            WEBHOOK_TIMEOUT_MS, 
            SIGNATURE_VALIDATION_TIMEOUT,
            FAST_VALIDATION_TIMEOUT
        )
        
        # Requirement 2.1: Sub-2-second response times
        assert WEBHOOK_TIMEOUT_MS <= 2000, "Webhook timeout should be <= 2000ms for Requirement 2.1"
        
        # Requirement 2.2: 500ms target for validation and queuing
        assert WEBHOOK_TIMEOUT_MS <= 500, "Webhook timeout should be <= 500ms for Requirement 2.2"
        
        # Requirement 2.6: Optimized signature validation with timeout protection
        assert SIGNATURE_VALIDATION_TIMEOUT <= 0.1, "Signature validation timeout should be <= 100ms"
        assert FAST_VALIDATION_TIMEOUT <= 0.1, "Fast validation timeout should be <= 100ms"


class TestWebhookIntegration:
    """Integration tests for webhook optimization."""
    
    @pytest.mark.asyncio
    async def test_webhook_response_time_simulation(self):
        """Simulate webhook processing to test response time."""
        from app.api.optimized_webhook import OptimizedWebhookProcessor
        
        processor = OptimizedWebhookProcessor()
        
        # Mock all dependencies to be fast
        processor.redis_manager = Mock()
        processor.redis_manager.is_available.return_value = True
        processor.redis_manager.execute_command = AsyncMock(return_value=None)
        
        processor.task_processor = Mock()
        processor.task_processor.queue_task = AsyncMock(return_value="task_123")
        
        # Simulate validation caching workflow
        cache_key = "test_simulation"
        
        start_time = time.time()
        
        # Step 1: Check cache (miss)
        cached_result = await processor.get_cached_validation(cache_key)
        assert cached_result is None
        
        # Step 2: Cache validation result
        entry = ValidationCacheEntry(True, datetime.now())
        await processor.cache_validation_result(cache_key, entry)
        
        # Step 3: Check cache (hit)
        cached_result = await processor.get_cached_validation(cache_key)
        assert cached_result is not None
        
        total_time = time.time() - start_time
        
        # Should complete validation workflow quickly
        assert total_time < 0.1, f"Validation workflow took {total_time:.3f}s, should be < 0.1s"
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self):
        """Test validation performance under concurrent load."""
        processor = OptimizedWebhookProcessor()
        
        # Mock fast Redis
        processor.redis_manager = Mock()
        processor.redis_manager.is_available.return_value = True
        processor.redis_manager.execute_command = AsyncMock(return_value=None)
        
        # Create multiple concurrent validation requests
        async def validate_request(request_id: int):
            cache_key = f"concurrent_test_{request_id}"
            entry = ValidationCacheEntry(True, datetime.now())
            
            start_time = time.time()
            await processor.cache_validation_result(cache_key, entry)
            result = await processor.get_cached_validation(cache_key)
            elapsed = time.time() - start_time
            
            return elapsed, result is not None
        
        # Run 10 concurrent validations
        start_time = time.time()
        tasks = [validate_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All should succeed
        assert all(success for _, success in results)
        
        # Individual operations should be fast
        max_individual_time = max(elapsed for elapsed, _ in results)
        assert max_individual_time < 0.05, f"Slowest validation took {max_individual_time:.3f}s"
        
        # Total time should be reasonable for concurrent execution
        assert total_time < 0.2, f"Concurrent validations took {total_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])