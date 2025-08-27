"""
Caching service for performance optimization.

This module provides intelligent caching for frequently accessed data,
analysis results, and computed values to improve application performance.
"""

import json
import hashlib
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from app.utils.logging import get_logger
from app.models.data_models import JobAnalysisResult, JobClassification
from app.services.redis_connection_manager import get_redis_manager

logger = get_logger(__name__)


class CacheKey:
    """Cache key generator with consistent naming."""
    
    @staticmethod
    def analysis_result(job_text: str) -> str:
        """Generate cache key for analysis results."""
        text_hash = hashlib.md5(job_text.encode()).hexdigest()
        return f"analysis:{text_hash}"
    
    @staticmethod
    def user_stats(phone_number: str) -> str:
        """Generate cache key for user statistics."""
        return f"user_stats:{phone_number}"
    
    @staticmethod
    def dashboard_overview() -> str:
        """Generate cache key for dashboard overview."""
        return "dashboard:overview"
    
    @staticmethod
    def analytics_trends(period: str) -> str:
        """Generate cache key for analytics trends."""
        return f"analytics:trends:{period}"
    
    @staticmethod
    def system_metrics() -> str:
        """Generate cache key for system metrics."""
        return "system:metrics"
    
    @staticmethod
    def user_interactions(user_id: int, page: int = 1) -> str:
        """Generate cache key for user interactions."""
        return f"user_interactions:{user_id}:{page}"


class CachingService:
    """
    Intelligent caching service with TTL management and cache warming.
    """
    
    def __init__(self):
        """Initialize caching service."""
        self.redis_manager = None
        self.graceful_handler = None
        self.default_ttl = 300  # 5 minutes
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def _get_redis_manager(self):
        """Lazy initialization of Redis manager to avoid circular imports."""
        if self.redis_manager is None:
            self.redis_manager = get_redis_manager()
        return self.redis_manager
    
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
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with graceful fallback.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            graceful_handler = self._get_graceful_handler()
            
            if graceful_handler:
                result = await graceful_handler.redis_get_with_fallback(key)
            else:
                # Fallback to direct Redis access
                redis_manager = self._get_redis_manager()
                result = await redis_manager.execute_command("get", key)
            
            if result is not None:
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                # Parse JSON if it's a string
                if isinstance(result, str):
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return result
                return result
            else:
                self.cache_stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with graceful fallback.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            graceful_handler = self._get_graceful_handler()
            
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            if graceful_handler:
                result = await graceful_handler.redis_set_with_fallback(key, value, ttl)
            else:
                # Fallback to direct Redis access
                redis_manager = self._get_redis_manager()
                result = await redis_manager.execute_command("setex", key, ttl, value)
                result = result is not None
            
            if result:
                self.cache_stats["sets"] += 1
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
                return True
            return False
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis_manager = self._get_redis_manager()
            result = await redis_manager.execute_command("delete", key)
            if result is not None:
                self.cache_stats["deletes"] += 1
                logger.debug(f"Cache delete: {key}")
                return True
            return False
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Cache key pattern
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis_manager = self._get_redis_manager()
            
            # Get keys matching pattern
            keys = await redis_manager.execute_command("keys", pattern)
            if keys and len(keys) > 0:
                # Delete all matching keys
                result = await redis_manager.execute_command("delete", *keys)
                if result is not None:
                    logger.info(f"Cache pattern invalidated: {pattern} ({len(keys)} keys)")
                    return True
            return True  # No keys to delete is also success
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.warning(f"Cache pattern invalidation error for '{pattern}': {e}")
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable, 
        ttl: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        Get value from cache or compute and set it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
            *args: Arguments for factory function
            **kwargs: Keyword arguments for factory function
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Use a lock to prevent race conditions in concurrent scenarios
        lock_key = f"lock:{key}"
        
        # Check cache again after acquiring conceptual lock
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Compute value using factory function
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory(*args, **kwargs)
            else:
                value = factory(*args, **kwargs)
            
            # Cache the computed value
            await self.set(key, value, ttl)
            return value
            
        except Exception as e:
            logger.error(f"Error computing value for cache key '{key}': {e}")
            raise
    
    async def cache_analysis_result(
        self, 
        job_text: str, 
        result: JobAnalysisResult,
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """
        Cache analysis result for job text.
        
        Args:
            job_text: Job advertisement text
            result: Analysis result
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully
        """
        try:
            # Validate inputs
            if not job_text or not job_text.strip():
                logger.warning("Cannot cache analysis result: empty job text")
                return False
            
            if not result:
                logger.warning("Cannot cache analysis result: empty result")
                return False
            
            # Limit job text length for cache key generation
            if len(job_text) > 10000:  # 10KB limit
                logger.warning("Job text too long for caching, truncating")
                job_text = job_text[:10000]
            
            cache_key = CacheKey.analysis_result(job_text)
            
            # Convert result to cacheable format
            cacheable_result = {
                "trust_score": result.trust_score,
                "classification": result.classification.value,
                "reasons": result.reasons,
                "confidence": result.confidence,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            return await self.set(cache_key, cacheable_result, ttl)
            
        except Exception as e:
            logger.error(f"Error caching analysis result: {e}")
            return False
    
    async def get_cached_analysis_result(self, job_text: str) -> Optional[JobAnalysisResult]:
        """
        Get cached analysis result for job text.
        
        Args:
            job_text: Job advertisement text
            
        Returns:
            Cached analysis result or None
        """
        cache_key = CacheKey.analysis_result(job_text)
        cached_data = await self.get(cache_key)
        
        if cached_data:
            try:
                return JobAnalysisResult(
                    trust_score=cached_data["trust_score"],
                    classification=JobClassification(cached_data["classification"]),
                    reasons=cached_data["reasons"],
                    confidence=cached_data["confidence"]
                )
            except Exception as e:
                logger.warning(f"Error deserializing cached analysis result: {e}")
                # Invalidate corrupted cache entry
                await self.delete(cache_key)
        
        return None
    
    async def warm_cache(self, analytics_service=None, metrics_collector=None):
        """
        Warm up cache with frequently accessed data.
        
        Args:
            analytics_service: Optional analytics service instance to avoid circular imports
            metrics_collector: Optional metrics collector instance to avoid circular imports
        """
        logger.info("Starting cache warming...")
        
        try:
            # Cache dashboard overview if analytics service is provided
            if analytics_service:
                overview_key = CacheKey.dashboard_overview()
                if not await self.get(overview_key):
                    try:
                        overview = await analytics_service.get_dashboard_overview()
                        await self.set(overview_key, overview.__dict__, 600)  # 10 minutes
                        logger.info("✅ Dashboard overview cached")
                    except Exception as e:
                        logger.warning(f"Failed to warm dashboard overview cache: {e}")
            
            # Cache system metrics if metrics collector is provided
            if metrics_collector:
                metrics_key = CacheKey.system_metrics()
                if not await self.get(metrics_key):
                    try:
                        current_metrics = await metrics_collector.get_current_metrics()
                        await self.set(metrics_key, current_metrics, 60)  # 1 minute
                        logger.info("✅ System metrics cached")
                    except Exception as e:
                        logger.warning(f"Failed to warm system metrics cache: {e}")
            
            logger.info("Cache warming completed")
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache_stats.copy()
        
        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = (stats["hits"] / total_requests) * 100
        else:
            stats["hit_rate"] = 0
        
        # Add Redis stats if available
        try:
            redis_manager = self._get_redis_manager()
            redis_metrics = await redis_manager.get_metrics()
            health_status = await redis_manager.health_check()
            
            stats["redis_total_requests"] = redis_metrics.total_requests
            stats["redis_successful_requests"] = redis_metrics.successful_requests
            stats["redis_failed_requests"] = redis_metrics.failed_requests
            stats["redis_uptime_percentage"] = redis_metrics.uptime_percentage
            stats["redis_average_response_time"] = redis_metrics.average_response_time
            stats["redis_is_available"] = redis_manager.is_available()
            stats["redis_circuit_breaker_state"] = health_status.state.value
            stats["redis_memory"] = health_status.memory_usage or "Unknown"
            stats["redis_connected_clients"] = health_status.connected_clients or 0
        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def cleanup_expired_cache(self):
        """
        Clean up expired cache entries (Redis handles this automatically).
        """
        logger.info("Cache cleanup completed (handled by Redis TTL)")


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None, max_key_length: int = 250):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
        max_key_length: Maximum length for cache keys to prevent memory issues
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation with length limits
                    func_name = func.__name__
                    # Limit args string length to prevent excessive memory usage
                    args_str = str(args)[:500] + str(sorted(kwargs.items()))[:500]
                    key_hash = hashlib.md5(args_str.encode()).hexdigest()
                    cache_key = f"func:{func_name}:{key_hash}"
                
                # Ensure cache key doesn't exceed maximum length
                if len(cache_key) > max_key_length:
                    cache_key = cache_key[:max_key_length-8] + hashlib.md5(cache_key.encode()).hexdigest()[:8]
                
                # Get caching service
                caching_service = get_caching_service()
                
                # Try to get from cache
                cached_result = await caching_service.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Compute result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache result
                await caching_service.set(cache_key, result, ttl)
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache decorator error for function '{func.__name__}': {e}")
                # Fall back to executing function without caching
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global caching service instance
_caching_service: Optional[CachingService] = None


def get_caching_service() -> CachingService:
    """Get global caching service instance."""
    global _caching_service
    if _caching_service is None:
        _caching_service = CachingService()
    return _caching_service


async def init_caching_service():
    """Initialize global caching service."""
    caching_service = get_caching_service()
    await caching_service.warm_cache()
    return caching_service