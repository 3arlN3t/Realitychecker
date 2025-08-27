"""
Unit tests for Redis Connection Manager with Circuit Breaker.

Tests cover connection management, circuit breaker functionality,
health monitoring, and error handling scenarios.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.redis_connection_manager import (
    RedisConnectionManager,
    RedisConfig,
    CircuitBreaker,
    CircuitBreakerState,
    ConnectionMetrics,
    HealthStatus,
    get_redis_manager,
    init_redis_manager,
    cleanup_redis_manager
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker for testing."""
        return CircuitBreaker(failure_threshold=3, timeout=60)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state."""
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Mock successful function
        mock_func = AsyncMock(return_value="success")
        
        result = await circuit_breaker.call(mock_func, "arg1", key="value")
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures."""
        mock_func = AsyncMock(side_effect=Exception("Redis error"))
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(mock_func)
        
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, circuit_breaker):
        """Test circuit breaker blocks requests when open."""
        # Force circuit breaker to open state
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.failure_count = 5
        circuit_breaker.last_failure_time = time.time()
        
        mock_func = AsyncMock()
        
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(mock_func)
        
        # Function should not be called
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self, circuit_breaker):
        """Test circuit breaker transitions to half-open after timeout."""
        # Set circuit breaker to open state with old failure time
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.failure_count = 5
        circuit_breaker.last_failure_time = time.time() - 70  # 70 seconds ago
        
        mock_func = AsyncMock(return_value="success")
        
        result = await circuit_breaker.call(mock_func)
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self, circuit_breaker):
        """Test circuit breaker handles failure in half-open state."""
        # Set to half-open state
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        circuit_breaker.failure_count = 2
        
        mock_func = AsyncMock(side_effect=Exception("Still failing"))
        
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
        
        assert circuit_breaker.failure_count == 3
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN


class TestRedisConnectionManager:
    """Test Redis connection manager functionality."""
    
    @pytest.fixture
    def redis_config(self):
        """Create Redis configuration for testing."""
        return RedisConfig(
            primary_url="redis://localhost:6379/0",
            replica_urls=["redis://localhost:6380/0"],
            pool_size=10,
            max_connections=20,
            connection_timeout=2.0,
            socket_timeout=2.0,
            command_timeout=1.0,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout=30
        )
    
    @pytest.fixture
    def redis_manager(self, redis_config):
        """Create Redis connection manager for testing."""
        return RedisConnectionManager(redis_config)
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, redis_manager):
        """Test successful Redis connection manager initialization."""
        with patch('app.services.redis_connection_manager.ConnectionPool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.from_url.return_value = mock_pool
            
            with patch('app.services.redis_connection_manager.Redis') as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis_class.return_value = mock_redis
                
                success = await redis_manager.initialize()
                
                assert success is True
                assert redis_manager._initialized is True
                assert redis_manager._fallback_mode is False
                assert redis_manager.primary_client is not None
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, redis_manager):
        """Test Redis connection manager initialization failure."""
        with patch('app.services.redis_connection_manager.ConnectionPool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.from_url.return_value = mock_pool
            
            with patch('app.services.redis_connection_manager.Redis') as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
                mock_redis_class.return_value = mock_redis
                
                success = await redis_manager.initialize()
                
                assert success is False
                assert redis_manager._fallback_mode is True
                assert redis_manager.metrics.last_error is not None
    
    @pytest.mark.asyncio
    async def test_get_connection_success(self, redis_manager):
        """Test getting Redis connection successfully."""
        # Mock successful initialization
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        redis_manager.primary_client = mock_redis
        
        connection = await redis_manager.get_connection()
        
        assert connection is not None
        assert connection == mock_redis
    
    @pytest.mark.asyncio
    async def test_get_connection_fallback_mode(self, redis_manager):
        """Test getting connection in fallback mode."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = True
        
        connection = await redis_manager.get_connection()
        
        assert connection is None
    
    @pytest.mark.asyncio
    async def test_get_connection_circuit_breaker_open(self, redis_manager):
        """Test getting connection when circuit breaker is open."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        redis_manager.circuit_breaker.state = CircuitBreakerState.OPEN
        redis_manager.circuit_breaker.last_failure_time = time.time()
        
        connection = await redis_manager.get_connection()
        
        assert connection is None
        assert redis_manager._fallback_mode is True
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self, redis_manager):
        """Test successful Redis command execution."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value="test_value")
        redis_manager.primary_client = mock_redis
        
        result = await redis_manager.execute_command("get", "test_key")
        
        assert result == "test_value"
        assert redis_manager.metrics.successful_requests == 1
        assert redis_manager.metrics.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, redis_manager):
        """Test Redis command execution timeout."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(side_effect=asyncio.TimeoutError())
        redis_manager.primary_client = mock_redis
        
        result = await redis_manager.execute_command("get", "test_key")
        
        assert result is None
        assert redis_manager.metrics.failed_requests == 1
        assert redis_manager._fallback_mode is True
    
    @pytest.mark.asyncio
    async def test_execute_command_fallback_mode(self, redis_manager):
        """Test command execution in fallback mode."""
        redis_manager._fallback_mode = True
        
        result = await redis_manager.execute_command("get", "test_key")
        
        assert result is None
        assert redis_manager.metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, redis_manager):
        """Test health check when Redis is healthy."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.info = AsyncMock(return_value={
            'used_memory_human': '1.5MB',
            'connected_clients': 5
        })
        redis_manager.primary_client = mock_redis
        
        status = await redis_manager.health_check()
        
        assert status.is_healthy is True
        assert status.memory_usage == '1.5MB'
        assert status.connected_clients == 5
        assert status.response_time is not None
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, redis_manager):
        """Test health check when Redis is unhealthy."""
        redis_manager._fallback_mode = True
        
        status = await redis_manager.health_check()
        
        assert status.is_healthy is False
        assert status.memory_usage is None
        assert status.connected_clients is None
    
    @pytest.mark.asyncio
    async def test_health_check_connection_failure(self, redis_manager):
        """Test health check when get_connection fails."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock get_connection to return None (simulating connection failure)
        with patch.object(redis_manager, 'get_connection', return_value=None):
            status = await redis_manager.health_check()
            
            assert status.is_healthy is False
            assert status.last_failure is None  # No failure recorded since get_connection returned None
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, redis_manager):
        """Test getting connection metrics."""
        # Set up some test metrics
        redis_manager.metrics.total_requests = 100
        redis_manager.metrics.successful_requests = 95
        redis_manager.metrics.failed_requests = 5
        
        metrics = await redis_manager.get_metrics()
        
        assert metrics.total_requests == 100
        assert metrics.successful_requests == 95
        assert metrics.failed_requests == 5
        assert metrics.uptime_percentage == 95.0
    
    def test_is_available_true(self, redis_manager):
        """Test is_available returns True when Redis is available."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        assert redis_manager.is_available() is True
    
    def test_is_available_false_not_initialized(self, redis_manager):
        """Test is_available returns False when not initialized."""
        redis_manager._initialized = False
        redis_manager._fallback_mode = False
        
        assert redis_manager.is_available() is False
    
    def test_is_available_false_fallback_mode(self, redis_manager):
        """Test is_available returns False in fallback mode."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = True
        
        assert redis_manager.is_available() is False
    
    @pytest.mark.asyncio
    async def test_replica_failover(self, redis_manager):
        """Test failover to replica when primary fails."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock primary client that fails
        mock_primary = AsyncMock()
        mock_primary.ping = AsyncMock(side_effect=Exception("Primary failed"))
        redis_manager.primary_client = mock_primary
        
        # Mock replica client that works
        mock_replica = AsyncMock()
        mock_replica.ping = AsyncMock(return_value=True)
        redis_manager.replica_clients = [mock_replica]
        
        connection = await redis_manager.get_connection()
        
        assert connection == mock_replica
    
    @pytest.mark.asyncio
    async def test_cleanup(self, redis_manager):
        """Test cleanup of Redis connections."""
        # Mock connections
        mock_primary = AsyncMock()
        mock_replica = AsyncMock()
        redis_manager.primary_client = mock_primary
        redis_manager.replica_clients = [mock_replica]
        redis_manager._initialized = True
        
        # Mock health check task
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_task.cancel = MagicMock()
        redis_manager._health_check_task = mock_task
        
        await redis_manager.cleanup()
        
        assert redis_manager._initialized is False
        mock_task.cancel.assert_called_once()
        mock_primary.close.assert_called_once()
        mock_replica.close.assert_called_once()
        assert len(redis_manager.replica_clients) == 0


class TestGlobalRedisManager:
    """Test global Redis manager functions."""
    
    @pytest.mark.asyncio
    async def test_get_redis_manager_singleton(self):
        """Test that get_redis_manager returns singleton instance."""
        # Clean up any existing manager
        await cleanup_redis_manager()
        
        manager1 = get_redis_manager()
        manager2 = get_redis_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, RedisConnectionManager)
    
    @pytest.mark.asyncio
    async def test_init_redis_manager(self):
        """Test initialization of global Redis manager."""
        # Clean up any existing manager
        await cleanup_redis_manager()
        
        with patch.object(RedisConnectionManager, 'initialize') as mock_init:
            mock_init.return_value = True
            
            manager = await init_redis_manager()
            
            assert isinstance(manager, RedisConnectionManager)
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_redis_manager(self):
        """Test cleanup of global Redis manager."""
        # Initialize manager
        manager = get_redis_manager()
        
        with patch.object(manager, 'cleanup') as mock_cleanup:
            await cleanup_redis_manager()
            
            mock_cleanup.assert_called_once()


class TestRedisConfig:
    """Test Redis configuration."""
    
    def test_redis_config_defaults(self):
        """Test Redis configuration default values."""
        config = RedisConfig()
        
        assert config.primary_url == "redis://localhost:6379/0"
        assert config.replica_urls == []
        assert config.pool_size == 20
        assert config.max_connections == 50
        assert config.connection_timeout == 5.0
        assert config.socket_timeout == 5.0
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 60
    
    def test_redis_config_custom_values(self):
        """Test Redis configuration with custom values."""
        config = RedisConfig(
            primary_url="redis://custom:6379/1",
            replica_urls=["redis://replica1:6379/1", "redis://replica2:6379/1"],
            pool_size=30,
            max_connections=60,
            connection_timeout=10.0,
            circuit_breaker_threshold=10
        )
        
        assert config.primary_url == "redis://custom:6379/1"
        assert len(config.replica_urls) == 2
        assert config.pool_size == 30
        assert config.max_connections == 60
        assert config.connection_timeout == 10.0
        assert config.circuit_breaker_threshold == 10


class TestConnectionMetrics:
    """Test connection metrics functionality."""
    
    def test_connection_metrics_defaults(self):
        """Test connection metrics default values."""
        metrics = ConnectionMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.circuit_breaker_trips == 0
        assert metrics.average_response_time == 0.0
        assert metrics.uptime_percentage == 100.0
        assert metrics.last_error is None


class TestHealthStatus:
    """Test health status functionality."""
    
    def test_health_status_creation(self):
        """Test health status creation."""
        status = HealthStatus(
            is_healthy=True,
            state=CircuitBreakerState.CLOSED,
            error_count=0,
            last_success=datetime.now(timezone.utc),
            last_failure=None,
            response_time=0.05,
            memory_usage="2.1MB",
            connected_clients=10
        )
        
        assert status.is_healthy is True
        assert status.state == CircuitBreakerState.CLOSED
        assert status.error_count == 0
        assert status.response_time == 0.05
        assert status.memory_usage == "2.1MB"
        assert status.connected_clients == 10


class TestConnectionPoolBehavior:
    """Test connection pooling behavior under various conditions."""
    
    @pytest.fixture
    def redis_manager(self):
        """Create Redis connection manager with pool-specific config."""
        config = RedisConfig(
            primary_url="redis://localhost:6379/0",
            pool_size=5,
            max_connections=10,
            connection_timeout=2.0,
            command_timeout=1.0
        )
        return RedisConnectionManager(config)
    
    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_handling(self, redis_manager):
        """Test graceful handling when connection pool is exhausted."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client with connection pool
        mock_redis = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.max_connections = 5
        mock_pool._created_connections = [MagicMock() for _ in range(5)]  # Pool is full
        mock_redis.connection_pool = mock_pool
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection pool exhausted"))
        redis_manager.primary_client = mock_redis
        
        connection = await redis_manager.get_connection()
        
        assert connection is None
        assert redis_manager._fallback_mode is True
    
    @pytest.mark.asyncio
    async def test_connection_pool_metrics_tracking(self, redis_manager):
        """Test that connection pool metrics are properly tracked."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client with connection pool
        mock_redis = AsyncMock()
        mock_pool = MagicMock()
        mock_pool._created_connections = [MagicMock() for _ in range(3)]
        mock_redis.connection_pool = mock_pool
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.info = AsyncMock(return_value={'connected_clients': 3})
        redis_manager.primary_client = mock_redis
        
        metrics = await redis_manager.get_metrics()
        
        assert metrics.max_connections_used >= 3
        assert metrics.current_connections == 3
    
    @pytest.mark.asyncio
    async def test_connection_pool_health_monitoring(self, redis_manager):
        """Test connection pool health monitoring and recycling."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        redis_manager.primary_client = mock_redis
        
        # Simulate health check
        await redis_manager._perform_health_check()
        
        # Verify health check was performed
        mock_redis.ping.assert_called()
        assert redis_manager._last_health_check > 0


class TestCircuitBreakerRecoveryScenarios:
    """Test circuit breaker activation and recovery scenarios."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker with specific settings for recovery testing."""
        return CircuitBreaker(failure_threshold=2, timeout=1)  # Short timeout for testing
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_gradual_recovery(self, circuit_breaker):
        """Test circuit breaker gradual recovery after partial success."""
        # Cause one failure (not enough to open circuit)
        mock_func = AsyncMock(side_effect=Exception("Temporary error"))
        with pytest.raises(Exception):
            await circuit_breaker.call(mock_func)
        
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        
        # Now succeed - should reduce failure count
        mock_func.side_effect = None
        mock_func.return_value = "success"
        result = await circuit_breaker.call(mock_func)
        
        assert result == "success"
        assert circuit_breaker.failure_count == 0  # Should be reduced
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_after_timeout(self, circuit_breaker):
        """Test circuit breaker recovery after timeout period."""
        # Force circuit breaker to open
        mock_func = AsyncMock(side_effect=Exception("Redis error"))
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(mock_func)
        
        assert circuit_breaker.get_state() == CircuitBreakerState.OPEN
        
        # Wait for timeout period
        await asyncio.sleep(1.1)  # Slightly longer than timeout
        
        # Should transition to half-open and then closed on success
        mock_func.side_effect = None
        mock_func.return_value = "recovered"
        result = await circuit_breaker.call(mock_func)
        
        assert result == "recovered"
        assert circuit_breaker.get_state() == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_access(self, circuit_breaker):
        """Test circuit breaker behavior under concurrent access."""
        # Force circuit breaker to open
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.last_failure_time = time.time()
        
        mock_func = AsyncMock()
        
        # Multiple concurrent calls should all fail
        tasks = [circuit_breaker.call(mock_func) for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should raise exceptions
        for result in results:
            assert isinstance(result, Exception)
            assert "Circuit breaker is OPEN" in str(result)
        
        # Function should not be called at all
        mock_func.assert_not_called()


class TestErrorHandlingAndFallbackMechanisms:
    """Test error handling and fallback mechanisms."""
    
    @pytest.fixture
    def redis_manager(self):
        """Create Redis connection manager for error testing."""
        config = RedisConfig(
            primary_url="redis://localhost:6379/0",
            replica_urls=["redis://localhost:6380/0", "redis://localhost:6381/0"],
            connection_timeout=1.0,
            command_timeout=0.5,
            circuit_breaker_threshold=2
        )
        return RedisConnectionManager(config)
    
    @pytest.mark.asyncio
    async def test_fallback_to_multiple_replicas(self, redis_manager):
        """Test fallback behavior with multiple replica connections."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock primary that fails
        mock_primary = AsyncMock()
        mock_primary.ping = AsyncMock(side_effect=Exception("Primary failed"))
        redis_manager.primary_client = mock_primary
        
        # Mock first replica that fails
        mock_replica1 = AsyncMock()
        mock_replica1.ping = AsyncMock(side_effect=Exception("Replica 1 failed"))
        
        # Mock second replica that works
        mock_replica2 = AsyncMock()
        mock_replica2.ping = AsyncMock(return_value=True)
        
        redis_manager.replica_clients = [mock_replica1, mock_replica2]
        
        connection = await redis_manager.get_connection()
        
        assert connection == mock_replica2
        mock_primary.ping.assert_called_once()
        mock_replica1.ping.assert_called_once()
        mock_replica2.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_reconnection(self, redis_manager):
        """Test exponential backoff during reconnection attempts."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = True
        
        # Mock Redis client that initially fails then succeeds
        mock_redis = AsyncMock()
        ping_calls = 0
        
        def ping_side_effect():
            nonlocal ping_calls
            ping_calls += 1
            if ping_calls <= 2:
                raise Exception("Connection failed")
            return True
        
        mock_redis.ping = AsyncMock(side_effect=ping_side_effect)
        redis_manager.primary_client = mock_redis
        
        # Simulate health check that should trigger recovery
        await redis_manager._perform_health_check()
        
        # Should have attempted ping and failed, staying in fallback mode
        assert redis_manager._fallback_mode is True
        assert ping_calls >= 1
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_during_redis_outage(self, redis_manager):
        """Test graceful degradation when Redis is completely unavailable."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = True
        
        # All Redis operations should return None gracefully
        result1 = await redis_manager.execute_command("get", "key1")
        result2 = await redis_manager.execute_command("set", "key2", "value2")
        result3 = await redis_manager.execute_command("incr", "counter")
        
        assert result1 is None
        assert result2 is None
        assert result3 is None
        
        # Metrics should not be incremented for fallback operations
        assert redis_manager.metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_automatic_recovery_detection(self, redis_manager):
        """Test automatic recovery detection and service restoration."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = True
        
        # Mock Redis client that becomes available
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        redis_manager.primary_client = mock_redis
        
        # Simulate health check that detects recovery
        await redis_manager._perform_health_check()
        
        # Should exit fallback mode
        assert redis_manager._fallback_mode is False
        mock_redis.ping.assert_called()
    
    @pytest.mark.asyncio
    async def test_detailed_error_logging_and_diagnostics(self, redis_manager):
        """Test detailed error logging with actionable diagnostics."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client that fails with specific error
        mock_redis = AsyncMock()
        specific_error = Exception("READONLY You can't write against a read only replica")
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.set = AsyncMock(side_effect=specific_error)
        redis_manager.primary_client = mock_redis
        
        result = await redis_manager.execute_command("set", "key", "value")
        
        assert result is None
        assert redis_manager.metrics.last_error == str(specific_error)
        assert redis_manager.metrics.last_error_time is not None
        assert redis_manager.metrics.failed_requests == 1


class TestRedisUrlValidationAndSecurity:
    """Test Redis URL validation and security measures."""
    
    @pytest.fixture
    def redis_manager(self):
        """Create Redis connection manager for security testing."""
        return RedisConnectionManager()
    
    def test_redis_url_validation_valid_urls(self, redis_manager):
        """Test validation of valid Redis URLs."""
        valid_urls = [
            "redis://localhost:6379/0",
            "redis://user:pass@localhost:6379/0",
            "rediss://secure.redis.com:6380/1",
            "redis://192.168.1.100:6379/0",
            "redis://redis.example.com:6379/0?timeout=5"
        ]
        
        for url in valid_urls:
            assert redis_manager._validate_redis_url(url) is True
    
    def test_redis_url_validation_invalid_urls(self, redis_manager):
        """Test validation rejects invalid Redis URLs."""
        invalid_urls = [
            "http://localhost:6379/0",  # Wrong protocol
            "redis://localhost/0",      # Missing port
            "redis://localhost:abc/0",  # Invalid port
            "localhost:6379",           # Missing protocol
            "",                         # Empty string
            "redis://",                 # Incomplete URL
        ]
        
        for url in invalid_urls:
            assert redis_manager._validate_redis_url(url) is False
    
    def test_redis_url_sanitization(self, redis_manager):
        """Test Redis URL sanitization for logging."""
        url_with_credentials = "redis://user:password@localhost:6379/0"
        sanitized = redis_manager._sanitize_url(url_with_credentials)
        
        assert "password" not in sanitized
        assert "user" not in sanitized
        assert "***" in sanitized
        assert "localhost:6379/0" in sanitized
    
    def test_redis_url_sanitization_no_credentials(self, redis_manager):
        """Test Redis URL sanitization without credentials."""
        url_without_credentials = "redis://localhost:6379/0"
        sanitized = redis_manager._sanitize_url(url_without_credentials)
        
        assert sanitized == url_without_credentials


class TestPerformanceMetricsIntegration:
    """Test integration with performance monitoring system."""
    
    @pytest.fixture
    def redis_manager(self):
        """Create Redis connection manager for performance testing."""
        config = RedisConfig(command_timeout=0.1)  # Very short timeout for testing
        return RedisConnectionManager(config)
    
    @pytest.mark.asyncio
    async def test_redis_operation_metrics_recording(self, redis_manager):
        """Test that Redis operations are properly recorded in performance metrics."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value="test_value")
        redis_manager.primary_client = mock_redis
        
        # Mock performance monitor
        with patch('app.services.performance_monitor.get_performance_monitor') as mock_get_monitor:
            mock_monitor = MagicMock()
            mock_get_monitor.return_value = mock_monitor
            
            # Execute command
            result = await redis_manager.execute_command("get", "test_key")
            
            assert result == "test_value"
            # Verify performance metrics were recorded
            mock_monitor.record_redis_operation.assert_called_once()
            
            # Check the call arguments
            call_args = mock_monitor.record_redis_operation.call_args
            assert call_args[1]['operation'] == 'get'
            assert call_args[1]['success'] is True
            assert call_args[1]['latency'] > 0
    
    @pytest.mark.asyncio
    async def test_redis_operation_failure_metrics(self, redis_manager):
        """Test that Redis operation failures are properly recorded."""
        redis_manager._initialized = True
        redis_manager._fallback_mode = False
        
        # Mock Redis client that fails
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.set = AsyncMock(side_effect=Exception("Redis operation failed"))
        redis_manager.primary_client = mock_redis
        
        # Mock performance monitor
        with patch('app.services.performance_monitor.get_performance_monitor') as mock_get_monitor:
            mock_monitor = MagicMock()
            mock_get_monitor.return_value = mock_monitor
            
            # Execute command that fails
            result = await redis_manager.execute_command("set", "key", "value")
            
            assert result is None
            # Verify failure metrics were recorded
            mock_monitor.record_redis_operation.assert_called_once()
            
            # Check the call arguments
            call_args = mock_monitor.record_redis_operation.call_args
            assert call_args[1]['operation'] == 'set'
            assert call_args[1]['success'] is False
            assert call_args[1]['error_message'] == 'Redis operation failed'


@pytest.mark.asyncio
async def test_integration_with_mock_redis():
    """Integration test with mock Redis server."""
    config = RedisConfig(
        primary_url="redis://localhost:6379/0",
        connection_timeout=1.0,
        command_timeout=0.5,
        circuit_breaker_threshold=2
    )
    
    manager = RedisConnectionManager(config)
    
    with patch('app.services.redis_connection_manager.ConnectionPool') as mock_pool_class:
        mock_pool = AsyncMock()
        mock_pool_class.from_url.return_value = mock_pool
        
        with patch('app.services.redis_connection_manager.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value="test_value")
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.info = AsyncMock(return_value={
                'used_memory_human': '1MB',
                'connected_clients': 1
            })
            mock_redis_class.return_value = mock_redis
            
            # Test initialization
            success = await manager.initialize()
            assert success is True
            
            # Test command execution
            result = await manager.execute_command("get", "test_key")
            assert result == "test_value"
            
            # Test health check
            status = await manager.health_check()
            assert status.is_healthy is True
            
            # Test metrics
            metrics = await manager.get_metrics()
            assert metrics.total_requests == 1
            assert metrics.successful_requests == 1
            
            # Test availability
            assert manager.is_available() is True
            
            # Test cleanup
            await manager.cleanup()
            assert manager._initialized is False