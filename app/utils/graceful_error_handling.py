"""
Graceful Error Handling and Recovery System.

This module implements comprehensive error handling and recovery mechanisms
for the Reality Checker application, providing fallback mechanisms for Redis
unavailability, graceful degradation for rate limiting, automatic recovery
detection, and comprehensive error logging with actionable diagnostics.

Implements Requirements:
- 6.1: Create fallback mechanisms for Redis unavailability
- 6.2: Implement graceful degradation for rate limiting without Redis
- 6.3: Add automatic recovery detection and service restoration
- 6.4: Create comprehensive error logging with actionable diagnostics
- 6.5: Ensure webhook processing continues during Redis outages
- 6.6: Implement automatic recovery when services are restored
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
import logging

from app.utils.logging import get_logger, log_with_context, get_correlation_id
from app.utils.error_handling import ErrorCategory, ErrorSeverity, handle_error
from app.services.redis_connection_manager import get_redis_manager
from app.services.performance_monitor import get_performance_monitor

logger = get_logger(__name__)


class ServiceStatus(Enum):
    """Service availability status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"


class FallbackMode(Enum):
    """Types of fallback modes."""
    NONE = "none"
    MEMORY_CACHE = "memory_cache"
    BASIC_RATE_LIMITING = "basic_rate_limiting"
    SIMPLIFIED_PROCESSING = "simplified_processing"
    EMERGENCY_MODE = "emergency_mode"


@dataclass
class ServiceHealth:
    """Health status of a service."""
    service_name: str
    status: ServiceStatus
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    recovery_attempts: int = 0
    fallback_mode: FallbackMode = FallbackMode.NONE
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryConfig:
    """Configuration for service recovery."""
    max_failure_count: int = 5
    recovery_check_interval: int = 30  # seconds
    recovery_timeout: int = 300  # 5 minutes
    exponential_backoff_base: float = 2.0
    max_backoff_delay: int = 300  # 5 minutes
    health_check_timeout: float = 5.0


@dataclass
class FallbackMetrics:
    """Metrics for fallback operations."""
    fallback_activations: int = 0
    fallback_duration: float = 0.0
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    memory_cache_hits: int = 0
    memory_cache_misses: int = 0
    degraded_operations: int = 0


class MemoryFallbackCache:
    """In-memory cache for Redis fallback operations."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize memory fallback cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.metrics = FallbackMetrics()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from memory cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.metrics.memory_cache_misses += 1
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time > entry['expires_at']:
            del self.cache[key]
            del self.access_times[key]
            self.metrics.memory_cache_misses += 1
            return None
        
        # Update access time
        self.access_times[key] = current_time
        self.metrics.memory_cache_hits += 1
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in memory cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        ttl = ttl or self.default_ttl
        current_time = time.time()
        
        # Evict expired entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_expired()
            
            # If still full, evict least recently used
            if len(self.cache) >= self.max_size:
                self._evict_lru()
        
        self.cache[key] = {
            'value': value,
            'expires_at': current_time + ttl,
            'created_at': current_time
        }
        self.access_times[key] = current_time
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete value from memory cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed
        """
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_times.clear()
    
    def _evict_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.access_times[key]
    
    def _evict_lru(self):
        """Remove least recently used entries."""
        if not self.access_times:
            return
        
        # Remove 10% of entries (LRU)
        num_to_remove = max(1, len(self.cache) // 10)
        lru_keys = sorted(self.access_times.items(), key=lambda x: x[1])[:num_to_remove]
        
        for key, _ in lru_keys:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        active_entries = sum(
            1 for entry in self.cache.values()
            if current_time <= entry['expires_at']
        )
        
        total_requests = self.metrics.memory_cache_hits + self.metrics.memory_cache_misses
        hit_rate = (self.metrics.memory_cache_hits / max(1, total_requests)) * 100
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'hit_rate': hit_rate,
            'hits': self.metrics.memory_cache_hits,
            'misses': self.metrics.memory_cache_misses,
            'max_size': self.max_size
        }


class BasicRateLimiter:
    """Basic in-memory rate limiter for Redis fallback."""
    
    def __init__(self):
        """Initialize basic rate limiter."""
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, identifier: str, limit: int = 10, window: int = 60) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Client identifier
            limit: Request limit
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, reason)
        """
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Clean up old requests
        requests = self.requests[identifier]
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Check limit
        if len(requests) >= limit:
            return False, f"Rate limit exceeded ({limit} requests per {window}s)"
        
        # Record request
        requests.append(current_time)
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        return True, None
    
    def _cleanup_old_entries(self):
        """Clean up old rate limiting entries."""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep 1 hour of history
        
        identifiers_to_remove = []
        for identifier, requests in self.requests.items():
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Remove empty identifiers
            if not requests:
                identifiers_to_remove.append(identifier)
        
        for identifier in identifiers_to_remove:
            del self.requests[identifier]


class GracefulErrorHandler:
    """
    Comprehensive error handling and recovery system.
    
    Implements graceful degradation, fallback mechanisms, and automatic recovery
    for Redis and other external service failures.
    """
    
    def __init__(self, config: Optional[RecoveryConfig] = None):
        """
        Initialize graceful error handler.
        
        Args:
            config: Recovery configuration
        """
        self.config = config or RecoveryConfig()
        self.redis_manager = get_redis_manager()
        self.performance_monitor = get_performance_monitor()
        
        # Service health tracking
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # Fallback mechanisms
        self.memory_cache = MemoryFallbackCache()
        self.basic_rate_limiter = BasicRateLimiter()
        
        # Recovery management
        self.recovery_tasks: Dict[str, asyncio.Task] = {}
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.fallback_metrics = FallbackMetrics()
        
        # Initialize service health
        self._initialize_service_health()
        
        logger.info("GracefulErrorHandler initialized")
    
    def _initialize_service_health(self):
        """Initialize service health tracking."""
        services = ['redis', 'openai', 'twilio', 'pdf_processing']
        
        for service in services:
            self.service_health[service] = ServiceHealth(
                service_name=service,
                status=ServiceStatus.HEALTHY
            )
    
    async def start_monitoring(self):
        """Start background monitoring for service recovery."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Graceful error handler monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Cancel recovery tasks
        for task in self.recovery_tasks.values():
            task.cancel()
        
        if self.recovery_tasks:
            await asyncio.gather(*self.recovery_tasks.values(), return_exceptions=True)
        
        self.recovery_tasks.clear()
        logger.info("✅ Graceful error handler monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop for service health and recovery."""
        while self.is_monitoring:
            try:
                await self._check_service_health()
                await self._attempt_service_recovery()
                await asyncio.sleep(self.config.recovery_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5.0)
    
    async def _check_service_health(self):
        """Check health of all monitored services."""
        # Check Redis health
        await self._check_redis_health()
        
        # Update metrics
        await self._update_health_metrics()
    
    async def _check_redis_health(self):
        """Check Redis service health."""
        service_health = self.service_health['redis']
        
        try:
            # Perform health check with timeout
            health_status = await asyncio.wait_for(
                self.redis_manager.health_check(),
                timeout=self.config.health_check_timeout
            )
            
            if health_status.is_healthy:
                await self._mark_service_healthy('redis')
            else:
                await self._mark_service_degraded('redis', "Redis health check failed")
                
        except Exception as e:
            await self._mark_service_unavailable('redis', str(e))
    
    async def _mark_service_healthy(self, service_name: str):
        """Mark service as healthy and handle recovery."""
        service_health = self.service_health[service_name]
        previous_status = service_health.status
        
        service_health.status = ServiceStatus.HEALTHY
        service_health.last_success = datetime.now(timezone.utc)
        service_health.failure_count = 0
        service_health.error_message = None
        
        # Handle recovery from degraded/unavailable state
        if previous_status in [ServiceStatus.DEGRADED, ServiceStatus.UNAVAILABLE, ServiceStatus.RECOVERING]:
            await self._handle_service_recovery(service_name, previous_status)
    
    async def _mark_service_degraded(self, service_name: str, error_message: str):
        """Mark service as degraded."""
        service_health = self.service_health[service_name]
        
        if service_health.status == ServiceStatus.HEALTHY:
            logger.warning(f"Service {service_name} degraded: {error_message}")
            
            service_health.status = ServiceStatus.DEGRADED
            service_health.failure_count += 1
            service_health.error_message = error_message
            service_health.last_failure = datetime.now(timezone.utc)
            
            # Enable appropriate fallback mode
            await self._enable_fallback_mode(service_name, FallbackMode.MEMORY_CACHE)
    
    async def _mark_service_unavailable(self, service_name: str, error_message: str):
        """Mark service as unavailable and enable fallback."""
        service_health = self.service_health[service_name]
        previous_status = service_health.status
        
        service_health.status = ServiceStatus.UNAVAILABLE
        service_health.failure_count += 1
        service_health.error_message = error_message
        service_health.last_failure = datetime.now(timezone.utc)
        
        if previous_status != ServiceStatus.UNAVAILABLE:
            log_with_context(
                logger,
                logging.ERROR,
                f"Service {service_name} unavailable",
                service=service_name,
                error=error_message,
                failure_count=service_health.failure_count,
                correlation_id=get_correlation_id()
            )
            
            # Enable appropriate fallback mode
            if service_name == 'redis':
                await self._enable_fallback_mode(service_name, FallbackMode.BASIC_RATE_LIMITING)
            else:
                await self._enable_fallback_mode(service_name, FallbackMode.SIMPLIFIED_PROCESSING)
    
    async def _enable_fallback_mode(self, service_name: str, fallback_mode: FallbackMode):
        """Enable fallback mode for a service."""
        service_health = self.service_health[service_name]
        previous_mode = service_health.fallback_mode
        
        service_health.fallback_mode = fallback_mode
        self.fallback_metrics.fallback_activations += 1
        
        log_with_context(
            logger,
            logging.WARNING,
            f"Fallback mode enabled for {service_name}",
            service=service_name,
            fallback_mode=fallback_mode.value,
            previous_mode=previous_mode.value,
            correlation_id=get_correlation_id()
        )
        
        # Record fallback activation metric
        self.performance_monitor.record_metric(
            "service_fallback_activated",
            1,
            "count",
            {
                "service": service_name,
                "fallback_mode": fallback_mode.value,
                "failure_count": str(service_health.failure_count)
            }
        )
    
    async def _handle_service_recovery(self, service_name: str, previous_status: ServiceStatus):
        """Handle service recovery from degraded/unavailable state."""
        service_health = self.service_health[service_name]
        
        # Disable fallback mode
        service_health.fallback_mode = FallbackMode.NONE
        self.fallback_metrics.successful_recoveries += 1
        
        log_with_context(
            logger,
            logging.INFO,
            f"Service {service_name} recovered",
            service=service_name,
            previous_status=previous_status.value,
            recovery_attempts=service_health.recovery_attempts,
            correlation_id=get_correlation_id()
        )
        
        # Record recovery metric
        self.performance_monitor.record_metric(
            "service_recovery_successful",
            1,
            "count",
            {
                "service": service_name,
                "previous_status": previous_status.value,
                "recovery_attempts": str(service_health.recovery_attempts)
            }
        )
        
        # Clear memory cache if Redis recovered
        if service_name == 'redis':
            self.memory_cache.clear()
            logger.info("Memory cache cleared after Redis recovery")
    
    async def _attempt_service_recovery(self):
        """Attempt recovery for unavailable services."""
        for service_name, service_health in self.service_health.items():
            if service_health.status == ServiceStatus.UNAVAILABLE:
                await self._attempt_single_service_recovery(service_name)
    
    async def _attempt_single_service_recovery(self, service_name: str):
        """Attempt recovery for a single service."""
        service_health = self.service_health[service_name]
        
        # Check if recovery task is already running
        if service_name in self.recovery_tasks and not self.recovery_tasks[service_name].done():
            return
        
        # Calculate backoff delay
        backoff_delay = min(
            self.config.exponential_backoff_base ** service_health.recovery_attempts,
            self.config.max_backoff_delay
        )
        
        # Check if enough time has passed since last failure
        if service_health.last_failure:
            time_since_failure = (datetime.now(timezone.utc) - service_health.last_failure).total_seconds()
            if time_since_failure < backoff_delay:
                return
        
        # Start recovery task
        self.recovery_tasks[service_name] = asyncio.create_task(
            self._recovery_task(service_name)
        )
    
    async def _recovery_task(self, service_name: str):
        """Recovery task for a specific service."""
        service_health = self.service_health[service_name]
        service_health.status = ServiceStatus.RECOVERING
        service_health.recovery_attempts += 1
        
        log_with_context(
            logger,
            logging.INFO,
            f"Attempting recovery for {service_name}",
            service=service_name,
            attempt=service_health.recovery_attempts,
            correlation_id=get_correlation_id()
        )
        
        try:
            # Attempt service-specific recovery
            if service_name == 'redis':
                await self._recover_redis()
            
            # Recovery successful if we reach here
            await self._mark_service_healthy(service_name)
            
        except Exception as e:
            self.fallback_metrics.failed_recoveries += 1
            
            log_with_context(
                logger,
                logging.WARNING,
                f"Recovery attempt failed for {service_name}",
                service=service_name,
                attempt=service_health.recovery_attempts,
                error=str(e),
                correlation_id=get_correlation_id()
            )
            
            # Mark as unavailable again
            service_health.status = ServiceStatus.UNAVAILABLE
            service_health.last_failure = datetime.now(timezone.utc)
    
    async def _recover_redis(self):
        """Attempt Redis recovery."""
        # Try to reinitialize Redis connection
        success = await self.redis_manager.initialize()
        if not success:
            raise Exception("Redis initialization failed")
        
        # Test basic operations
        await self.redis_manager.execute_command('ping')
        
        logger.info("Redis recovery successful")
    
    async def _update_health_metrics(self):
        """Update health metrics for monitoring."""
        healthy_services = sum(
            1 for health in self.service_health.values()
            if health.status == ServiceStatus.HEALTHY
        )
        
        degraded_services = sum(
            1 for health in self.service_health.values()
            if health.status == ServiceStatus.DEGRADED
        )
        
        unavailable_services = sum(
            1 for health in self.service_health.values()
            if health.status == ServiceStatus.UNAVAILABLE
        )
        
        # Record service health metrics
        self.performance_monitor.record_metric("services_healthy", healthy_services, "count")
        self.performance_monitor.record_metric("services_degraded", degraded_services, "count")
        self.performance_monitor.record_metric("services_unavailable", unavailable_services, "count")
        
        # Record fallback metrics
        self.performance_monitor.record_metric(
            "fallback_operations_total",
            self.fallback_metrics.fallback_activations,
            "count"
        )
    
    # Fallback operation methods
    
    async def execute_with_fallback(
        self,
        operation: Callable,
        service_name: str,
        fallback_operation: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with fallback handling.
        
        Args:
            operation: Primary operation to execute
            service_name: Name of the service being used
            fallback_operation: Fallback operation if primary fails
            *args: Arguments for operations
            **kwargs: Keyword arguments for operations
            
        Returns:
            Result of primary or fallback operation
        """
        service_health = self.service_health.get(service_name)
        
        # If service is known to be unavailable, use fallback immediately
        if service_health and service_health.status == ServiceStatus.UNAVAILABLE:
            if fallback_operation:
                self.fallback_metrics.degraded_operations += 1
                return await self._execute_fallback(fallback_operation, *args, **kwargs)
            else:
                raise Exception(f"Service {service_name} unavailable and no fallback provided")
        
        # Try primary operation
        try:
            result = await self._execute_operation(operation, *args, **kwargs)
            
            # Mark service as healthy if it was degraded
            if service_health and service_health.status == ServiceStatus.DEGRADED:
                await self._mark_service_healthy(service_name)
            
            return result
            
        except Exception as e:
            # Mark service as degraded/unavailable
            await self._mark_service_unavailable(service_name, str(e))
            
            # Try fallback if available
            if fallback_operation:
                self.fallback_metrics.degraded_operations += 1
                return await self._execute_fallback(fallback_operation, *args, **kwargs)
            else:
                raise
    
    async def _execute_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with proper async handling."""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            return operation(*args, **kwargs)
    
    async def _execute_fallback(self, fallback_operation: Callable, *args, **kwargs) -> Any:
        """Execute fallback operation with proper async handling."""
        if asyncio.iscoroutinefunction(fallback_operation):
            return await fallback_operation(*args, **kwargs)
        else:
            return fallback_operation(*args, **kwargs)
    
    # Redis fallback methods - Requirement 6.1: Fallback mechanisms for Redis unavailability
    
    async def redis_get_with_fallback(self, key: str) -> Optional[Any]:
        """Get value from Redis with memory cache fallback."""
        async def redis_get():
            return await self.redis_manager.execute_command('get', key)
        
        def memory_get():
            return self.memory_cache.get(key)
        
        return await self.execute_with_fallback(redis_get, 'redis', memory_get)
    
    async def redis_set_with_fallback(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with memory cache fallback."""
        async def redis_set():
            if ttl:
                return await self.redis_manager.execute_command('setex', key, ttl, value)
            else:
                return await self.redis_manager.execute_command('set', key, value)
        
        def memory_set():
            return self.memory_cache.set(key, value, ttl)
        
        return await self.execute_with_fallback(redis_set, 'redis', memory_set)
    
    # Rate limiting fallback - Requirement 6.2: Graceful degradation for rate limiting
    
    async def rate_limit_check_with_fallback(
        self,
        identifier: str,
        limit: int = 10,
        window: int = 60
    ) -> Tuple[bool, Optional[str]]:
        """Check rate limit with fallback to basic in-memory limiting."""
        async def redis_rate_limit():
            # Use Redis-based rate limiting
            redis_manager = self.redis_manager
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use sliding window with Redis
            count = await redis_manager.execute_command(
                'zcount', f'rate_limit:{identifier}', window_start, current_time
            )
            
            if count and count >= limit:
                return False, f"Rate limit exceeded ({limit} requests per {window}s)"
            
            # Add current request
            await redis_manager.execute_command(
                'zadd', f'rate_limit:{identifier}', current_time, f'{current_time}:{identifier}'
            )
            await redis_manager.execute_command('expire', f'rate_limit:{identifier}', window * 2)
            
            # Clean up old entries
            await redis_manager.execute_command(
                'zremrangebyscore', f'rate_limit:{identifier}', 0, window_start
            )
            
            return True, None
        
        def memory_rate_limit():
            return self.basic_rate_limiter.is_allowed(identifier, limit, window)
        
        return await self.execute_with_fallback(redis_rate_limit, 'redis', memory_rate_limit)
    
    # Service status methods
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get current status of a service."""
        service_health = self.service_health.get(service_name)
        return service_health.status if service_health else ServiceStatus.UNAVAILABLE
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if service is available (healthy or degraded)."""
        status = self.get_service_status(service_name)
        return status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def get_fallback_mode(self, service_name: str) -> FallbackMode:
        """Get current fallback mode for a service."""
        service_health = self.service_health.get(service_name)
        return service_health.fallback_mode if service_health else FallbackMode.NONE
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all services and fallback mechanisms."""
        status = {
            'services': {},
            'fallback_metrics': {
                'activations': self.fallback_metrics.fallback_activations,
                'successful_recoveries': self.fallback_metrics.successful_recoveries,
                'failed_recoveries': self.fallback_metrics.failed_recoveries,
                'degraded_operations': self.fallback_metrics.degraded_operations
            },
            'memory_cache': self.memory_cache.get_stats(),
            'monitoring_active': self.is_monitoring
        }
        
        for service_name, service_health in self.service_health.items():
            status['services'][service_name] = {
                'status': service_health.status.value,
                'fallback_mode': service_health.fallback_mode.value,
                'failure_count': service_health.failure_count,
                'recovery_attempts': service_health.recovery_attempts,
                'last_success': service_health.last_success.isoformat() if service_health.last_success else None,
                'last_failure': service_health.last_failure.isoformat() if service_health.last_failure else None,
                'error_message': service_health.error_message
            }
        
        return status


# Global graceful error handler instance
_graceful_error_handler: Optional[GracefulErrorHandler] = None


def get_graceful_error_handler() -> GracefulErrorHandler:
    """Get global graceful error handler instance."""
    global _graceful_error_handler
    if _graceful_error_handler is None:
        _graceful_error_handler = GracefulErrorHandler()
    return _graceful_error_handler


async def init_graceful_error_handler() -> GracefulErrorHandler:
    """Initialize global graceful error handler."""
    handler = get_graceful_error_handler()
    await handler.start_monitoring()
    return handler


async def cleanup_graceful_error_handler():
    """Cleanup global graceful error handler."""
    global _graceful_error_handler
    if _graceful_error_handler:
        await _graceful_error_handler.stop_monitoring()
        _graceful_error_handler = None