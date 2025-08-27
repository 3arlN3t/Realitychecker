"""
Redis Connection Manager with Circuit Breaker Pattern.

This module provides robust Redis connectivity with automatic failover,
circuit breaker pattern, and comprehensive monitoring for the Reality Checker application.
"""

import asyncio
import time
import json
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, timezone
import logging

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import (
    ConnectionError, TimeoutError, RedisError,
    BusyLoadingError, ReadOnlyError
)

from app.utils.logging import get_logger
from app.config import get_config

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    primary_url: str = "redis://localhost:6379/0"
    replica_urls: List[str] = field(default_factory=list)
    sentinel_urls: List[str] = field(default_factory=list)
    pool_size: int = 20
    max_connections: int = 50
    connection_timeout: float = 5.0
    socket_timeout: float = 5.0
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 120
    command_timeout: float = 5.0  # More conservative timeout for stability


@dataclass
class ConnectionMetrics:
    """Redis connection metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_breaker_trips: int = 0
    average_response_time: float = 0.0
    current_connections: int = 0
    max_connections_used: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime_percentage: float = 100.0


@dataclass
class HealthStatus:
    """Redis health status."""
    is_healthy: bool
    state: CircuitBreakerState
    error_count: int
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    response_time: Optional[float]
    memory_usage: Optional[str]
    connected_clients: Optional[int]


class CircuitBreaker:
    """Circuit breaker implementation for Redis operations."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying half-open state
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise ConnectionError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
            except Exception as e:
                await self._on_failure()
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    async def _on_success(self):
        """Handle successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker reset to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED and self.failure_count > 0:
            # Gradually reduce failure count on successful operations
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state


class RedisConnectionManager:
    """
    Redis connection manager with circuit breaker, health monitoring, and automatic failover.
    """
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """
        Initialize Redis connection manager.
        
        Args:
            config: Redis configuration
        """
        self.config = config or self._load_config()
        self.primary_client: Optional[Redis] = None
        self.replica_clients: List[Redis] = []
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )
        self.metrics = ConnectionMetrics()
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_check = 0.0
        self._fallback_mode = False
        
    def _load_config(self) -> RedisConfig:
        """Load Redis configuration from environment."""
        import os
        
        config = RedisConfig()
        config.primary_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        config.pool_size = int(os.getenv('REDIS_POOL_SIZE', '20'))
        config.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
        config.connection_timeout = float(os.getenv('REDIS_CONNECTION_TIMEOUT', '5.0'))
        config.socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0'))
        config.command_timeout = float(os.getenv('REDIS_COMMAND_TIMEOUT', '2.0'))
        config.circuit_breaker_threshold = int(os.getenv('REDIS_CB_THRESHOLD', '5'))
        config.circuit_breaker_timeout = int(os.getenv('REDIS_CB_TIMEOUT', '60'))
        
        # Parse replica URLs if provided
        replica_urls = os.getenv('REDIS_REPLICA_URLS', '')
        if replica_urls:
            config.replica_urls = [url.strip() for url in replica_urls.split(',')]
        
        return config
    
    async def initialize(self) -> bool:
        """
        Initialize Redis connections with error handling.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        try:
            logger.info("Initializing Redis connection manager...")
            
            # Initialize primary connection
            success = await self._initialize_primary_connection()
            if not success:
                logger.warning("Primary Redis connection failed, enabling fallback mode")
                self._fallback_mode = True
                return False
            
            # Initialize replica connections if configured
            await self._initialize_replica_connections()
            
            # Start health monitoring
            self._start_health_monitoring()
            
            self._initialized = True
            logger.info("✅ Redis connection manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connection manager: {e}")
            self._fallback_mode = True
            return False
    
    async def _initialize_primary_connection(self) -> bool:
        """Initialize primary Redis connection."""
        try:
            # Validate Redis URL format for security
            if not self._validate_redis_url(self.config.primary_url):
                raise ValueError(f"Invalid Redis URL format: {self._sanitize_url(self.config.primary_url)}")
            
            # Create connection pool with optimized settings
            pool = ConnectionPool.from_url(
                self.config.primary_url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.connection_timeout,
                retry_on_timeout=True,
                health_check_interval=self.config.health_check_interval,
                encoding="utf-8",
                decode_responses=True
            )
            
            self.primary_client = Redis(connection_pool=pool)
            
            # Test connection with timeout
            await asyncio.wait_for(
                self.primary_client.ping(),
                timeout=self.config.connection_timeout
            )
            
            logger.info(f"Primary Redis connection established: {self._sanitize_url(self.config.primary_url)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize primary Redis connection: {e}")
            self.metrics.last_error = str(e)
            self.metrics.last_error_time = datetime.now(timezone.utc)
            return False
    
    async def _initialize_replica_connections(self):
        """Initialize replica Redis connections."""
        for replica_url in self.config.replica_urls:
            try:
                pool = ConnectionPool.from_url(
                    replica_url,
                    max_connections=self.config.max_connections // 2,  # Fewer connections for replicas
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.connection_timeout,
                    retry_on_timeout=True,
                    encoding="utf-8",
                    decode_responses=True
                )
                
                replica_client = Redis(connection_pool=pool)
                await asyncio.wait_for(
                    replica_client.ping(),
                    timeout=self.config.connection_timeout
                )
                
                self.replica_clients.append(replica_client)
                logger.info(f"Replica Redis connection established: {self._sanitize_url(replica_url)}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize replica Redis connection {replica_url}: {e}")
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize Redis URL for logging."""
        if '://' in url and '@' in url:
            scheme, rest = url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                return f"{scheme}://***@{host_part}"
        return url
    
    def _validate_redis_url(self, url: str) -> bool:
        """Validate Redis URL format for security."""
        import re
        # Basic Redis URL validation pattern
        redis_url_pattern = r'^redis(s)?://([^:@]+:[^:@]+@)?[^:@/]+:\d+(/\d+)?(\?.*)?$'
        return bool(re.match(redis_url_pattern, url))
    
    def _start_health_monitoring(self):
        """Start background health monitoring task."""
        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_monitor_loop())
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while self._initialized:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _perform_health_check(self):
        """Perform health check on Redis connections."""
        self._last_health_check = time.time()
        
        # Check primary connection
        if self.primary_client:
            try:
                start_time = time.time()
                await asyncio.wait_for(
                    self.primary_client.ping(),
                    timeout=self.config.command_timeout
                )
                response_time = time.time() - start_time
                
                # Update metrics
                self.metrics.average_response_time = (
                    self.metrics.average_response_time * 0.9 + response_time * 0.1
                )
                
                # If we were in fallback mode, try to recover
                if self._fallback_mode:
                    self._fallback_mode = False
                    logger.info("✅ Recovered from Redis fallback mode")
                
            except Exception as e:
                logger.warning(f"Primary Redis health check failed: {e}")
                self.metrics.failed_requests += 1
                self.metrics.last_error = str(e)
                self.metrics.last_error_time = datetime.now(timezone.utc)
                
                # Enable fallback mode if not already enabled
                if not self._fallback_mode:
                    self._fallback_mode = True
                    logger.warning("⚠️ Enabling Redis fallback mode due to health check failure")
    
    async def get_connection(self) -> Optional[Redis]:
        """
        Get Redis connection with circuit breaker protection.
        
        Returns:
            Redis client or None if unavailable
        """
        if not self._initialized or self._fallback_mode:
            return None
        
        try:
            # Use circuit breaker to protect against cascading failures
            return await self.circuit_breaker.call(self._get_healthy_connection)
        except Exception as e:
            logger.warning(f"Failed to get Redis connection: {e}")
            self._fallback_mode = True
            return None
    
    async def _get_healthy_connection(self) -> Redis:
        """Get a healthy Redis connection."""
        if self.primary_client:
            # Skip ping if we recently confirmed it's healthy
            current_time = time.time()
            if current_time - self._last_health_check < 30.0:  # Use cached health status for 30 seconds
                return self.primary_client
            
            # Quick health check with reasonable timeout
            try:
                await asyncio.wait_for(
                    self.primary_client.ping(),
                    timeout=2.0  # More reasonable timeout
                )
                return self.primary_client
            except Exception:
                pass
        
        # Try replica connections if primary fails
        for replica in self.replica_clients:
            try:
                await asyncio.wait_for(
                    replica.ping(),
                    timeout=0.5
                )
                return replica
            except Exception:
                continue
        
        raise ConnectionError("No healthy Redis connections available")
    
    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """
        Execute Redis command with timeout and error handling.
        
        Args:
            command: Redis command name
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            Command result or None if failed
        """
        if self._fallback_mode:
            logger.debug(f"Skipping Redis command '{command}' - in fallback mode")
            return None
        
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            client = await self.get_connection()
            if not client:
                return None
            
            # Execute command with timeout
            result = await asyncio.wait_for(
                getattr(client, command.lower())(*args, **kwargs),
                timeout=self.config.command_timeout
            )
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Update success metrics
            self.metrics.successful_requests += 1
            self.metrics.average_response_time = (
                self.metrics.average_response_time * 0.9 + latency * 0.1
            )
            
            # Record Redis operation performance metrics
            await self._record_redis_operation_metric(command, latency, True)
            
            return result
            
        except asyncio.TimeoutError:
            latency = time.time() - start_time
            error_msg = f"Redis command '{command}' timed out after {self.config.command_timeout}s"
            logger.warning(error_msg)
            self.metrics.failed_requests += 1
            self._fallback_mode = True
            
            # Record timeout as failed operation
            await self._record_redis_operation_metric(command, latency, False, error_msg)
            return None
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Redis command '{command}' failed: {e}"
            logger.warning(error_msg)
            self.metrics.failed_requests += 1
            self.metrics.last_error = str(e)
            self.metrics.last_error_time = datetime.now(timezone.utc)
            
            # Record failed operation
            await self._record_redis_operation_metric(command, latency, False, str(e))
            return None
    
    async def _record_redis_operation_metric(self, operation: str, latency: float, success: bool, error_message: Optional[str] = None):
        """
        Record Redis operation metrics with performance monitor.
        
        Implements Requirement 4.2: Implement Redis operation monitoring with latency measurements
        """
        try:
            # Get performance monitor (lazy import to avoid circular dependencies)
            from app.services.performance_monitor import get_performance_monitor
            performance_monitor = get_performance_monitor()
            
            # Get current connection pool size
            pool_size = 0
            if self.primary_client and hasattr(self.primary_client, 'connection_pool'):
                pool_size = getattr(self.primary_client.connection_pool, 'max_connections', 0)
            
            # Record the operation
            performance_monitor.record_redis_operation(
                operation=operation,
                latency=latency,
                success=success,
                error_message=error_message,
                connection_pool_size=pool_size,
                circuit_breaker_state=self.circuit_breaker.get_state().value
            )
        except Exception as e:
            # Don't fail Redis operations due to monitoring issues
            logger.debug(f"Failed to record Redis operation metric: {e}")
    
    async def health_check(self) -> HealthStatus:
        """
        Perform comprehensive health check.
        
        Returns:
            Current health status
        """
        status = HealthStatus(
            is_healthy=False,
            state=self.circuit_breaker.get_state(),
            error_count=self.metrics.failed_requests,
            last_success=None,
            last_failure=self.metrics.last_error_time,
            response_time=None,
            memory_usage=None,
            connected_clients=None
        )
        
        if self._fallback_mode:
            return status
        
        try:
            client = await self.get_connection()
            if not client:
                return status
            
            # Perform health check with timing
            start_time = time.time()
            await asyncio.wait_for(
                client.ping(),
                timeout=self.config.command_timeout
            )
            response_time = time.time() - start_time
            
            # Get Redis info
            info = await asyncio.wait_for(
                client.info(),
                timeout=self.config.command_timeout
            )
            
            status.is_healthy = True
            status.last_success = datetime.now(timezone.utc)
            status.response_time = response_time
            status.memory_usage = info.get('used_memory_human', 'Unknown')
            status.connected_clients = info.get('connected_clients', 0)
            
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            status.last_failure = datetime.now(timezone.utc)
        
        return status
    
    async def get_metrics(self) -> ConnectionMetrics:
        """
        Get current connection metrics.
        
        Returns:
            Current metrics
        """
        # Calculate uptime percentage
        total_requests = self.metrics.total_requests
        if total_requests > 0:
            self.metrics.uptime_percentage = (
                self.metrics.successful_requests / total_requests * 100
            )
        
        # Update current connections and pool metrics
        try:
            if self.primary_client and not self._fallback_mode:
                info = await asyncio.wait_for(
                    self.primary_client.info(),
                    timeout=1.0
                )
                self.metrics.current_connections = info.get('connected_clients', 0)
                
                # Track max connections used for capacity planning
                if hasattr(self.primary_client, 'connection_pool'):
                    pool = self.primary_client.connection_pool
                    if hasattr(pool, '_created_connections'):
                        current_pool_size = len(pool._created_connections)
                        self.metrics.max_connections_used = max(
                            self.metrics.max_connections_used, 
                            current_pool_size
                        )
        except Exception:
            pass
        
        return self.metrics
    
    def is_available(self) -> bool:
        """
        Check if Redis is currently available.
        
        Returns:
            True if Redis is available, False otherwise
        """
        return self._initialized and not self._fallback_mode
    
    async def cleanup(self):
        """Clean up Redis connections and resources."""
        logger.info("Cleaning up Redis connection manager...")
        
        self._initialized = False
        
        # Cancel health monitoring
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except (asyncio.CancelledError, TypeError):
                # TypeError can occur if task is a mock in tests
                pass
        
        # Close primary connection
        if self.primary_client:
            try:
                await self.primary_client.close()
                logger.info("✅ Primary Redis connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing primary Redis connection: {e}")
        
        # Close replica connections
        for i, replica in enumerate(self.replica_clients):
            try:
                await replica.close()
                logger.info(f"✅ Replica Redis connection {i+1} closed")
            except Exception as e:
                logger.error(f"❌ Error closing replica Redis connection {i+1}: {e}")
        
        self.replica_clients.clear()
        logger.info("Redis connection manager cleanup completed")


# Global Redis connection manager instance
_redis_manager: Optional[RedisConnectionManager] = None


def get_redis_manager() -> RedisConnectionManager:
    """Get global Redis connection manager instance."""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisConnectionManager()
    return _redis_manager


async def init_redis_manager() -> RedisConnectionManager:
    """Initialize global Redis connection manager."""
    manager = get_redis_manager()
    await manager.initialize()
    return manager


async def cleanup_redis_manager():
    """Cleanup global Redis connection manager."""
    global _redis_manager
    if _redis_manager:
        await _redis_manager.cleanup()
        _redis_manager = None