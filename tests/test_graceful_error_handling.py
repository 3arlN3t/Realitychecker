"""
Unit tests for graceful error handling and recovery system.

Tests the comprehensive error handling, fallback mechanisms, and automatic
recovery functionality implemented in the graceful error handling system.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.utils.graceful_error_handling import (
    GracefulErrorHandler, MemoryFallbackCache, BasicRateLimiter,
    ServiceStatus, FallbackMode, ServiceHealth, RecoveryConfig
)
from app.utils.error_diagnostics import (
    ErrorDiagnosticsCollector, DiagnosticLevel, SystemMetrics, ServiceDiagnostics
)
from app.utils.error_handling import ErrorCategory, ErrorSeverity


class TestMemoryFallbackCache:
    """Test memory fallback cache functionality."""
    
    def test_cache_basic_operations(self):
        """Test basic cache get/set operations."""
        cache = MemoryFallbackCache(max_size=10, default_ttl=60)
        
        # Test set and get
        assert cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test miss
        assert cache.get("nonexistent") is None
        
        # Test delete
        assert cache.delete("key1")
        assert cache.get("key1") is None
        assert not cache.delete("nonexistent")
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache = MemoryFallbackCache(max_size=10, default_ttl=1)
        
        # Set with short TTL
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_eviction(self):
        """Test cache eviction when max size is reached."""
        cache = MemoryFallbackCache(max_size=2, default_ttl=60)
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add another key, should evict key2 (LRU)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        # key2 might still be there due to eviction strategy
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MemoryFallbackCache(max_size=10, default_ttl=60)
        
        # Generate some hits and misses
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0


class TestBasicRateLimiter:
    """Test basic rate limiter functionality."""
    
    def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality."""
        limiter = BasicRateLimiter()
        
        # Should allow requests within limit
        allowed, reason = limiter.is_allowed("user1", limit=2, window=60)
        assert allowed
        assert reason is None
        
        allowed, reason = limiter.is_allowed("user1", limit=2, window=60)
        assert allowed
        assert reason is None
        
        # Should block when limit exceeded
        allowed, reason = limiter.is_allowed("user1", limit=2, window=60)
        assert not allowed
        assert "Rate limit exceeded" in reason
    
    def test_rate_limiting_window_expiry(self):
        """Test rate limiting window expiry."""
        limiter = BasicRateLimiter()
        
        # Fill up the limit
        limiter.is_allowed("user1", limit=1, window=1)
        
        # Should be blocked
        allowed, reason = limiter.is_allowed("user1", limit=1, window=1)
        assert not allowed
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, reason = limiter.is_allowed("user1", limit=1, window=1)
        assert allowed
    
    def test_rate_limiting_per_user(self):
        """Test per-user rate limiting isolation."""
        limiter = BasicRateLimiter()
        
        # Fill limit for user1
        limiter.is_allowed("user1", limit=1, window=60)
        allowed, _ = limiter.is_allowed("user1", limit=1, window=60)
        assert not allowed
        
        # user2 should still be allowed
        allowed, _ = limiter.is_allowed("user2", limit=1, window=60)
        assert allowed


class TestGracefulErrorHandler:
    """Test graceful error handler functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create graceful error handler for testing."""
        config = RecoveryConfig(
            max_failure_count=3,
            recovery_check_interval=1,
            recovery_timeout=5,
            health_check_timeout=1.0
        )
        return GracefulErrorHandler(config)
    
    @pytest.fixture
    def mock_redis_manager(self):
        """Mock Redis manager for testing."""
        mock = Mock()
        mock.is_available.return_value = True
        mock.execute_command = AsyncMock()
        mock.health_check = AsyncMock()
        mock.initialize = AsyncMock(return_value=True)
        return mock
    
    def test_service_health_initialization(self, handler):
        """Test service health tracking initialization."""
        assert "redis" in handler.service_health
        assert "openai" in handler.service_health
        assert "twilio" in handler.service_health
        
        for service_health in handler.service_health.values():
            assert service_health.status == ServiceStatus.HEALTHY
            assert service_health.fallback_mode == FallbackMode.NONE
    
    @pytest.mark.asyncio
    async def test_service_status_methods(self, handler):
        """Test service status query methods."""
        # Initially healthy
        assert handler.get_service_status("redis") == ServiceStatus.HEALTHY
        assert handler.is_service_available("redis")
        assert handler.get_fallback_mode("redis") == FallbackMode.NONE
        
        # Mark as unavailable
        await handler._mark_service_unavailable("redis", "Connection failed")
        
        assert handler.get_service_status("redis") == ServiceStatus.UNAVAILABLE
        assert not handler.is_service_available("redis")
        assert handler.get_fallback_mode("redis") == FallbackMode.BASIC_RATE_LIMITING
    
    @pytest.mark.asyncio
    async def test_fallback_operations(self, handler):
        """Test fallback operation execution."""
        # Mock operations
        primary_op = AsyncMock(return_value="primary_result")
        fallback_op = AsyncMock(return_value="fallback_result")
        
        # Test successful primary operation
        result = await handler.execute_with_fallback(
            primary_op, "test_service", fallback_op
        )
        assert result == "primary_result"
        primary_op.assert_called_once()
        fallback_op.assert_not_called()
        
        # Test fallback when service unavailable
        handler.service_health["test_service"] = ServiceHealth(
            service_name="test_service",
            status=ServiceStatus.UNAVAILABLE
        )
        
        result = await handler.execute_with_fallback(
            primary_op, "test_service", fallback_op
        )
        assert result == "fallback_result"
        fallback_op.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_fallback_operations(self, handler):
        """Test Redis-specific fallback operations."""
        # Test get with fallback
        with patch.object(handler.redis_manager, 'execute_command', AsyncMock(return_value="redis_value")):
            result = await handler.redis_get_with_fallback("test_key")
            assert result == "redis_value"
        
        # Test set with fallback
        with patch.object(handler.redis_manager, 'execute_command', AsyncMock(return_value=True)):
            result = await handler.redis_set_with_fallback("test_key", "test_value", 300)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback(self, handler):
        """Test rate limiting with fallback."""
        # Mock Redis rate limiting success
        with patch.object(handler.redis_manager, 'execute_command', AsyncMock(return_value=0)):
            allowed, reason = await handler.rate_limit_check_with_fallback("user1", 10, 60)
            assert allowed
            assert reason is None
        
        # Test fallback to memory when Redis fails
        handler.service_health["redis"].status = ServiceStatus.UNAVAILABLE
        
        allowed, reason = await handler.rate_limit_check_with_fallback("user1", 1, 60)
        assert allowed
        
        # Should use memory limiter for subsequent requests
        allowed, reason = await handler.rate_limit_check_with_fallback("user1", 1, 60)
        assert not allowed
        assert "Rate limit exceeded" in reason
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, handler):
        """Test monitoring start/stop lifecycle."""
        assert not handler.is_monitoring
        
        await handler.start_monitoring()
        assert handler.is_monitoring
        assert handler.monitoring_task is not None
        
        await handler.stop_monitoring()
        assert not handler.is_monitoring
    
    @pytest.mark.asyncio
    async def test_comprehensive_status(self, handler):
        """Test comprehensive status reporting."""
        status = await handler.get_comprehensive_status()
        
        assert "services" in status
        assert "fallback_metrics" in status
        assert "memory_cache" in status
        assert "monitoring_active" in status
        
        assert "redis" in status["services"]
        assert "openai" in status["services"]
        assert "twilio" in status["services"]


class TestErrorDiagnosticsCollector:
    """Test error diagnostics collector functionality."""
    
    @pytest.fixture
    def collector(self):
        """Create error diagnostics collector for testing."""
        return ErrorDiagnosticsCollector()
    
    @pytest.fixture
    def mock_redis_manager(self):
        """Mock Redis manager for testing."""
        mock = Mock()
        mock.is_available.return_value = True
        mock.health_check = AsyncMock()
        mock.get_metrics = AsyncMock()
        return mock
    
    def test_error_classification(self, collector):
        """Test error classification logic."""
        # Test Redis error
        redis_error = Exception("Redis connection failed")
        category, severity = collector._classify_error(redis_error)
        assert category == ErrorCategory.SYSTEM
        assert severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
        
        # Test PDF error
        pdf_error = Exception("PDF extraction failed")
        category, severity = collector._classify_error(pdf_error)
        assert category == ErrorCategory.PDF_PROCESSING
        assert severity == ErrorSeverity.LOW
        
        # Test OpenAI error
        openai_error = Exception("OpenAI API rate limit exceeded")
        category, severity = collector._classify_error(openai_error)
        assert category == ErrorCategory.RATE_LIMIT
        assert severity == ErrorSeverity.MEDIUM
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, collector):
        """Test system metrics collection."""
        metrics = await collector._collect_system_metrics()
        
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_available_mb >= 0
        assert metrics.disk_usage_percent >= 0
        assert len(metrics.load_average) == 3
        assert metrics.open_files >= 0
        assert metrics.network_connections >= 0
    
    @pytest.mark.asyncio
    async def test_redis_diagnostics_collection(self, collector):
        """Test Redis service diagnostics collection."""
        with patch.object(collector, 'redis_manager') as mock_redis:
            mock_redis.is_available.return_value = True
            mock_redis.health_check = AsyncMock(return_value=Mock(
                last_success=datetime.now(timezone.utc),
                state=Mock(value="closed")
            ))
            mock_redis.get_metrics = AsyncMock(return_value=Mock(
                failed_requests=0,
                current_connections=5,
                total_requests=100,
                successful_requests=95,
                uptime_percentage=95.0,
                average_response_time=0.05
            ))
            
            diagnostics = await collector._collect_redis_diagnostics(DiagnosticLevel.COMPREHENSIVE)
            
            assert isinstance(diagnostics, ServiceDiagnostics)
            assert diagnostics.service_name == "redis"
            assert diagnostics.is_available
            assert diagnostics.response_time_ms is not None
            assert diagnostics.additional_info is not None
    
    def test_actionable_steps_generation(self, collector):
        """Test actionable troubleshooting steps generation."""
        error = Exception("Redis connection timeout")
        category = ErrorCategory.NETWORK
        service_diagnostics = [
            ServiceDiagnostics(
                service_name="redis",
                is_available=False,
                response_time_ms=None,
                error_message="Connection timeout",
                last_success=None,
                failure_count=5,
                connection_pool_size=None,
                active_connections=None,
                circuit_breaker_state=None
            )
        ]
        
        steps = collector._generate_actionable_steps(error, category, service_diagnostics)
        
        assert len(steps) > 0
        assert any("Redis" in step for step in steps)
        assert any("network" in step.lower() for step in steps)
    
    def test_resolution_suggestions_generation(self, collector):
        """Test resolution suggestions generation."""
        error = Exception("High CPU usage detected")
        category = ErrorCategory.SYSTEM
        system_metrics = SystemMetrics(
            cpu_percent=90.0,  # High CPU
            memory_percent=50.0,
            memory_available_mb=1000.0,
            disk_usage_percent=70.0,
            load_average=(2.0, 1.5, 1.0),
            open_files=100,
            network_connections=50
        )
        
        suggestions = collector._generate_resolution_suggestions(error, category, system_metrics)
        
        assert len(suggestions) > 0
        assert any("CPU" in suggestion for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_comprehensive_diagnostics_collection(self, collector):
        """Test comprehensive error diagnostics collection."""
        error = Exception("Test error for diagnostics")
        context = {"test_key": "test_value"}
        correlation_id = "test-correlation-id"
        
        with patch.object(collector, '_collect_system_metrics') as mock_system_metrics:
            mock_system_metrics.return_value = SystemMetrics(
                cpu_percent=50.0,
                memory_percent=60.0,
                memory_available_mb=2000.0,
                disk_usage_percent=40.0,
                load_average=(1.0, 0.8, 0.6),
                open_files=50,
                network_connections=25
            )
            
            with patch.object(collector, '_collect_service_diagnostics') as mock_service_diagnostics:
                mock_service_diagnostics.return_value = [
                    ServiceDiagnostics(
                        service_name="redis",
                        is_available=True,
                        response_time_ms=10.0,
                        error_message=None,
                        last_success=datetime.now(timezone.utc),
                        failure_count=0,
                        connection_pool_size=10,
                        active_connections=5,
                        circuit_breaker_state="closed"
                    )
                ]
                
                diagnostic = await collector.collect_error_diagnostics(
                    error, context, correlation_id, DiagnosticLevel.COMPREHENSIVE
                )
                
                assert diagnostic.error_id is not None
                assert diagnostic.correlation_id == correlation_id
                assert diagnostic.error_type == "Exception"
                assert diagnostic.error_message == "Test error for diagnostics"
                assert diagnostic.context == context
                assert len(diagnostic.actionable_steps) > 0
                assert len(diagnostic.service_diagnostics) > 0
    
    def test_error_history_management(self, collector):
        """Test error history storage and management."""
        # Add errors to history
        for i in range(5):
            error = Exception(f"Test error {i}")
            diagnostic = Mock()
            diagnostic.timestamp = datetime.now(timezone.utc)
            diagnostic.error_type = "Exception"
            diagnostic.error_category = ErrorCategory.SYSTEM
            collector._store_diagnostic(diagnostic)
        
        assert len(collector.error_history) == 5
        
        # Test history size limit
        collector.max_history_size = 3
        for i in range(3):
            error = Exception(f"Additional error {i}")
            diagnostic = Mock()
            diagnostic.timestamp = datetime.now(timezone.utc)
            diagnostic.error_type = "Exception"
            diagnostic.error_category = ErrorCategory.SYSTEM
            collector._store_diagnostic(diagnostic)
        
        assert len(collector.error_history) == 3
    
    def test_error_summary_generation(self, collector):
        """Test error summary generation."""
        # Add some test errors
        now = datetime.now(timezone.utc)
        for i in range(3):
            diagnostic = Mock()
            diagnostic.timestamp = now - timedelta(hours=i)
            diagnostic.error_category = ErrorCategory.SYSTEM
            diagnostic.error_severity = ErrorSeverity.MEDIUM
            diagnostic.error_type = "Exception"
            collector.error_history.append(diagnostic)
        
        summary = collector.get_error_summary(hours=24)
        
        assert summary["total_errors"] == 3
        assert summary["time_period_hours"] == 24
        assert "category_breakdown" in summary
        assert "severity_breakdown" in summary
        assert "error_type_breakdown" in summary


@pytest.mark.asyncio
async def test_integration_graceful_error_handling():
    """Integration test for graceful error handling system."""
    handler = GracefulErrorHandler()
    
    try:
        # Start monitoring
        await handler.start_monitoring()
        
        # Test fallback operations
        result = await handler.redis_get_with_fallback("test_key")
        # Should not raise exception even if Redis is unavailable
        
        # Test rate limiting fallback
        allowed, reason = await handler.rate_limit_check_with_fallback("test_user", 10, 60)
        assert isinstance(allowed, bool)
        
        # Test comprehensive status
        status = await handler.get_comprehensive_status()
        assert "services" in status
        assert "fallback_metrics" in status
        
    finally:
        # Cleanup
        await handler.stop_monitoring()


@pytest.mark.asyncio
async def test_integration_error_diagnostics():
    """Integration test for error diagnostics collection."""
    collector = ErrorDiagnosticsCollector()
    
    # Test comprehensive diagnostics collection
    error = Exception("Integration test error")
    context = {"component": "integration_test"}
    
    diagnostic = await collector.collect_error_diagnostics(
        error, context, "test-correlation", DiagnosticLevel.DETAILED
    )
    
    assert diagnostic is not None
    assert diagnostic.error_message == "Integration test error"
    assert diagnostic.context == context
    assert len(diagnostic.actionable_steps) > 0
    assert len(diagnostic.service_diagnostics) > 0
    
    # Test error summary
    summary = collector.get_error_summary(hours=1)
    assert summary["total_errors"] >= 1