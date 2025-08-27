"""
Enhanced database connection pool management with performance optimizations.

This module provides advanced connection pooling, caching, and database
performance optimizations for the Reality Checker application.
"""

import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, text, pool
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
import redis.asyncio as redis
from redis.asyncio import Redis

from app.utils.logging import get_logger
from app.utils.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from app.config import get_config

logger = get_logger(__name__)


class ConnectionPoolManager:
    """
    Advanced connection pool manager with Redis caching, circuit breaker protection,
    and comprehensive performance monitoring.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize connection pool manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or self._get_database_url()
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.redis_client: Optional[Redis] = None
        self._initialized = False
        self._last_health_check = None
        self._connection_recycling_task = None
        
        # Enhanced connection statistics
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_size": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalidated": 0,
            "recycled": 0,
            "health_checks": 0,
            "failed_health_checks": 0,
            "circuit_breaker_trips": 0
        }
        
        # Circuit breaker for database connections
        self._db_circuit_breaker = None
        
        # Connection pool configuration
        self._pool_config = self._get_optimized_pool_config()
    
    def _get_optimized_pool_config(self) -> Dict[str, Any]:
        """
        Get optimized connection pool configuration based on environment and database type.
        
        Returns:
            Dictionary with optimized pool configuration
        """
        is_production = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
        is_postgresql = 'postgresql' in self.database_url
        
        if is_postgresql:
            # PostgreSQL optimized configuration
            base_pool_size = 10 if is_production else 5
            max_overflow = 20 if is_production else 10
            
            return {
                "pool_size": int(os.getenv('DB_POOL_SIZE', str(base_pool_size))),
                "max_overflow": int(os.getenv('DB_MAX_OVERFLOW', str(max_overflow))),
                "pool_timeout": int(os.getenv('DB_POOL_TIMEOUT', '15')),  # Reduced for faster failures
                "pool_recycle": int(os.getenv('DB_POOL_RECYCLE', '1800')),  # 30 minutes
                "pool_pre_ping": True,
                "pool_reset_on_return": "commit",  # Ensure clean state
                "connect_timeout": 10,  # Connection establishment timeout
                "command_timeout": 30,  # Query execution timeout
                "health_check_interval": 60,  # Health check every minute
                "utilization_warning_threshold": 0.8,  # Warn at 80% utilization
                "utilization_critical_threshold": 0.95,  # Critical at 95% utilization
            }
        else:
            # SQLite configuration (development)
            return {
                "pool_size": 1,  # SQLite doesn't support multiple connections well
                "max_overflow": 0,
                "pool_timeout": 10,
                "pool_recycle": 3600,  # 1 hour
                "pool_pre_ping": True,
                "connect_timeout": 5,
                "health_check_interval": 300,  # Health check every 5 minutes
                "utilization_warning_threshold": 0.8,
                "utilization_critical_threshold": 0.95,
            }
        
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        # Check for PostgreSQL configuration first
        if all(env_var in os.environ for env_var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']):
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME')
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        
        # Check for explicit DATABASE_URL
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')
        
        # Default to SQLite for development
        db_path = os.getenv('DATABASE_PATH', 'data/reality_checker.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"
    
    async def initialize(self):
        """Initialize connection pool, circuit breaker, and monitoring."""
        if self._initialized:
            return
        
        try:
            # Initialize circuit breaker for database connections
            self._initialize_circuit_breaker()
            
            # Initialize database engine with optimized connection pooling
            await self._initialize_database_engine()
            
            # Initialize Redis cache
            await self._initialize_redis_cache()
            
            # Setup connection pool monitoring
            self._setup_pool_monitoring()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._initialized = True
            logger.info("✅ Connection pool manager initialized successfully with circuit breaker protection")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool manager: {e}")
            raise
    
    def _initialize_circuit_breaker(self):
        """Initialize circuit breaker for database connections."""
        circuit_config = CircuitBreakerConfig(
            failure_threshold=int(os.getenv('DB_CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5')),
            recovery_timeout=int(os.getenv('DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60')),
            success_threshold=int(os.getenv('DB_CIRCUIT_BREAKER_SUCCESS_THRESHOLD', '3')),
            timeout=float(os.getenv('DB_CIRCUIT_BREAKER_TIMEOUT', '30.0')),
            expected_exception=Exception  # All database exceptions count as failures
        )
        
        self._db_circuit_breaker = get_circuit_breaker("database_connection", circuit_config)
        logger.info("Database connection circuit breaker initialized")
    
    async def _initialize_database_engine(self):
        """Initialize database engine with optimized settings."""
        config = self._pool_config
        
        if self.database_url.startswith('sqlite'):
            # SQLite configuration with WAL mode and optimizations
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": config["connect_timeout"],
                    "isolation_level": None  # Enable autocommit mode
                },
                # SQLite-specific optimizations
                pool_pre_ping=config["pool_pre_ping"],
                pool_recycle=config["pool_recycle"],
                execution_options={
                    "isolation_level": "AUTOCOMMIT"
                }
            )
            
            # SQLite pragma optimizations
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                # Enable WAL mode for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Optimize synchronization
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Increase cache size (in pages, negative = KB)
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                # Store temporary tables in memory
                cursor.execute("PRAGMA temp_store=MEMORY")
                # Optimize page size
                cursor.execute("PRAGMA page_size=4096")
                # Enable memory-mapped I/O
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                # Optimize locking mode
                cursor.execute("PRAGMA locking_mode=NORMAL")
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        else:
            # PostgreSQL configuration with optimized connection pooling
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                # Advanced connection pooling with optimized configuration
                poolclass=QueuePool,
                pool_size=config["pool_size"],
                max_overflow=config["max_overflow"],
                pool_timeout=config["pool_timeout"],
                pool_recycle=config["pool_recycle"],
                pool_pre_ping=config["pool_pre_ping"],
                pool_reset_on_return=config["pool_reset_on_return"],
                # Connection optimization
                connect_args={
                    "server_settings": {
                        "application_name": "reality_checker",
                        "jit": "off",  # Disable JIT for faster connection
                        "shared_preload_libraries": "",  # Reduce startup overhead
                        "max_connections": str(config["pool_size"] + config["max_overflow"] + 50),
                    },
                    "command_timeout": config["command_timeout"],
                    "prepared_statement_cache_size": 150,  # Increased for better caching
                    "statement_cache_size": 150,  # Add statement caching
                },
                # Execution options
                execution_options={
                    "isolation_level": "READ_COMMITTED"
                }
            )
        
        # Create session factory with optimizations
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            # Session-level optimizations
            autoflush=False,  # Manual flush control for better performance
            autocommit=False
        )
        
        logger.info(f"Database engine initialized with optimized pool configuration: {self._sanitize_url(self.database_url)}")
    
    async def _start_background_tasks(self):
        """Start background tasks for connection monitoring and recycling."""
        # Start connection health monitoring task
        self._connection_recycling_task = asyncio.create_task(
            self._connection_health_monitor()
        )
        logger.info("Background connection monitoring tasks started")
    
    async def _connection_health_monitor(self):
        """Background task to monitor connection health and perform recycling."""
        while self._initialized:
            try:
                await asyncio.sleep(self._pool_config["health_check_interval"])
                
                # Perform health check
                await self._perform_health_check()
                
                # Check pool utilization and log warnings
                await self._check_pool_utilization()
                
                # Recycle idle connections if needed
                await self._recycle_idle_connections()
                
            except asyncio.CancelledError:
                logger.info("Connection health monitor task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in connection health monitor: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _perform_health_check(self):
        """Perform connection pool health check."""
        try:
            self._connection_stats["health_checks"] += 1
            
            # Test database connection through circuit breaker
            async def test_connection():
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
            
            await self._db_circuit_breaker.call(test_connection)
            self._last_health_check = datetime.now()
            
        except Exception as e:
            self._connection_stats["failed_health_checks"] += 1
            logger.warning(f"Database health check failed: {e}")
    
    async def _check_pool_utilization(self):
        """Check pool utilization and log warnings if thresholds are exceeded."""
        if not self.engine or not hasattr(self.engine.pool, 'size'):
            return
        
        try:
            pool = self.engine.pool
            total_size = pool.size() + pool.overflow()
            checked_out = pool.checkedout()
            
            if total_size > 0:
                utilization = checked_out / total_size
                
                if utilization >= self._pool_config["utilization_critical_threshold"]:
                    logger.error(
                        f"CRITICAL: Database connection pool utilization at {utilization:.1%} "
                        f"({checked_out}/{total_size}). Consider scaling up."
                    )
                elif utilization >= self._pool_config["utilization_warning_threshold"]:
                    logger.warning(
                        f"WARNING: Database connection pool utilization at {utilization:.1%} "
                        f"({checked_out}/{total_size}). Monitor for scaling needs."
                    )
                
                # Update stats
                self._connection_stats["pool_utilization"] = utilization
                
        except Exception as e:
            logger.error(f"Error checking pool utilization: {e}")
    
    async def _recycle_idle_connections(self):
        """Recycle idle connections to maintain pool health."""
        if not self.engine:
            return
        
        try:
            # Different strategies based on pool type
            if hasattr(self.engine.pool, '_invalidate_time'):
                # Update invalidate time to force pre-ping checks on QueuePool
                self.engine.pool._invalidate_time = time.time()
                self._connection_stats["recycled"] += 1
                logger.debug("Triggered connection pool health validation")
            elif hasattr(self.engine.pool, 'size') and self.engine.pool.size() > 0:
                # For other pool types, just log the health check
                logger.debug("Connection pool health check completed")
            else:
                # For SQLite StaticPool, minimal logging
                logger.debug("Connection health monitoring active")
                
        except Exception as e:
            logger.error(f"Error recycling connections: {e}")
    
    async def _initialize_redis_cache(self):
        """Initialize Redis cache connection."""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                # Connection pool settings
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            logger.info("✅ Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis cache not available: {e}")
            self.redis_client = None
    
    def _setup_pool_monitoring(self):
        """Setup connection pool monitoring events."""
        if not self.engine:
            return
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._connection_stats["total_connections"] += 1
            logger.debug("Database connection established")
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self._connection_stats["active_connections"] += 1
            self._connection_stats["checked_out"] += 1
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            self._connection_stats["active_connections"] -= 1
        
        @event.listens_for(self.engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            self._connection_stats["invalidated"] += 1
            logger.warning(f"Database connection invalidated: {exception}")
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize database URL for logging."""
        if '://' in url:
            scheme, rest = url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                if ':' in credentials:
                    user, _ = credentials.split(':', 1)
                    return f"{scheme}://{user}:***@{host_part}"
        return url
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get optimized database session with circuit breaker protection and automatic cleanup.
        
        Yields:
            AsyncSession: Database session with performance optimizations
        """
        if not self._initialized:
            await self.initialize()
        
        # Use circuit breaker to protect session creation
        async def create_session():
            session = self.session_factory()
            try:
                # Enable query optimization hints
                await session.execute(text("-- Query optimization enabled"))
                return session
            except Exception:
                await session.close()
                raise
        
        session = await self._db_circuit_breaker.call(create_session)
        
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            # Circuit breaker will handle the failure tracking
            raise
        finally:
            await session.close()
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get cached result from Redis with timeout protection.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached result or None
        """
        if not self.redis_client:
            return None
        
        try:
            # Add 2-second timeout to prevent webhook blocking
            result = await asyncio.wait_for(
                self.redis_client.get(cache_key),
                timeout=2.0
            )
            if result:
                import json
                return json.loads(result)
        except asyncio.TimeoutError:
            logger.warning(f"Redis get operation timed out for key: {cache_key}")
            # Mark Redis as unavailable
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set_cached_result(self, cache_key: str, data: Any, ttl: int = 300):
        """
        Set cached result in Redis.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        if not self.redis_client:
            return
        
        try:
            import json
            await asyncio.wait_for(
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(data, default=str)
                ),
                timeout=2.0
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def invalidate_cache_pattern(self, pattern: str):
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Cache key pattern (e.g., "user:*")
        """
        if not self.redis_client:
            return
        
        try:
            keys = await asyncio.wait_for(
                self.redis_client.keys(pattern),
                timeout=2.0
            )
            if keys:
                await asyncio.wait_for(
                    self.redis_client.delete(*keys),
                    timeout=2.0
                )
                logger.info(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive connection pool statistics with utilization metrics.
        
        Returns:
            Dictionary with detailed pool statistics
        """
        stats = self._connection_stats.copy()
        
        # Add pool configuration
        stats["pool_config"] = self._pool_config.copy()
        
        # Add current pool state
        if self.engine and hasattr(self.engine.pool, 'size'):
            pool = self.engine.pool
            pool_size = pool.size()
            checked_out = pool.checkedout()
            checked_in = pool.checkedin()
            overflow = pool.overflow()
            invalid = pool.invalid()
            total_capacity = pool_size + overflow
            
            stats.update({
                "pool_size": pool_size,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
                "invalid": invalid,
                "total_capacity": total_capacity,
                "utilization": checked_out / total_capacity if total_capacity > 0 else 0,
                "available_connections": checked_in,
                "pool_exhausted": checked_out >= total_capacity
            })
        
        # Add circuit breaker status
        if self._db_circuit_breaker:
            stats["circuit_breaker"] = self._db_circuit_breaker.get_status()
        
        # Add health check information
        stats["last_health_check"] = (
            self._last_health_check.isoformat() if self._last_health_check else None
        )
        
        # Add Redis stats if available
        if self.redis_client:
            try:
                redis_info = await asyncio.wait_for(
                    self.redis_client.info(),
                    timeout=2.0
                )
                stats["redis"] = {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_redis_hit_rate(redis_info)
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
                stats["redis"] = {"status": "unavailable", "error": str(e)}
        else:
            stats["redis"] = {"status": "not_configured"}
        
        return stats
    
    def _calculate_redis_hit_rate(self, redis_info: Dict[str, Any]) -> float:
        """Calculate Redis cache hit rate."""
        hits = redis_info.get("keyspace_hits", 0)
        misses = redis_info.get("keyspace_misses", 0)
        total = hits + misses
        return hits / total if total > 0 else 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check with circuit breaker status.
        
        Returns:
            Health check results with detailed status information
        """
        health = {
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "connection_pool": {"status": "unknown"},
            "circuit_breaker": {"status": "unknown"}
        }
        
        # Database health check through circuit breaker
        try:
            async def db_health_test():
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
            
            await self._db_circuit_breaker.call(db_health_test)
            health["database"] = {
                "status": "healthy",
                "type": "postgresql" if "postgresql" in self.database_url else "sqlite",
                "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
            }
        except Exception as e:
            health["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "type": "postgresql" if "postgresql" in self.database_url else "sqlite"
            }
        
        # Circuit breaker status
        if self._db_circuit_breaker:
            cb_status = self._db_circuit_breaker.get_status()
            health["circuit_breaker"] = {
                "status": "healthy" if cb_status["state"] == "closed" else "degraded",
                "details": cb_status
            }
        
        # Redis health check
        if self.redis_client:
            try:
                await asyncio.wait_for(
                    self.redis_client.ping(),
                    timeout=2.0
                )
                health["redis"] = {"status": "healthy"}
            except asyncio.TimeoutError:
                health["redis"] = {
                    "status": "unhealthy",
                    "error": "Redis ping timeout"
                }
                # Mark Redis as unavailable
                self.redis_client = None
            except Exception as e:
                health["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health["redis"] = {"status": "not_configured"}
        
        # Connection pool health with utilization metrics
        try:
            pool_stats = await self.get_pool_stats()
            utilization = pool_stats.get("utilization", 0)
            
            if utilization >= self._pool_config["utilization_critical_threshold"]:
                pool_status = "critical"
            elif utilization >= self._pool_config["utilization_warning_threshold"]:
                pool_status = "warning"
            else:
                pool_status = "healthy"
            
            health["connection_pool"] = {
                "status": pool_status,
                "utilization": utilization,
                "stats": pool_stats
            }
        except Exception as e:
            health["connection_pool"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return health
    
    async def cleanup(self):
        """Clean up resources and stop background tasks."""
        logger.info("Cleaning up connection pool manager...")
        
        # Stop background tasks
        if self._connection_recycling_task:
            try:
                self._connection_recycling_task.cancel()
                await self._connection_recycling_task
                logger.info("✅ Background monitoring tasks stopped")
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"❌ Error stopping background tasks: {e}")
        
        # Close Redis connection
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing Redis connection: {e}")
        
        # Close database engine
        if self.engine:
            try:
                await self.engine.dispose()
                logger.info("✅ Database engine disposed")
            except Exception as e:
                logger.error(f"❌ Error disposing database engine: {e}")
        
        self._initialized = False
        logger.info("Connection pool manager cleanup completed")
    
    async def force_connection_recycling(self):
        """Force immediate connection recycling for maintenance."""
        if not self.engine:
            return
        
        try:
            # Different recycling strategies based on pool type
            if hasattr(self.engine.pool, 'invalidate'):
                # PostgreSQL QueuePool supports invalidate
                self.engine.pool.invalidate()
                self._connection_stats["recycled"] += 1
                logger.info("Forced connection pool recycling completed")
            elif hasattr(self.engine.pool, 'recreate'):
                # Some pools support recreate
                self.engine.pool.recreate()
                self._connection_stats["recycled"] += 1
                logger.info("Forced connection pool recreation completed")
            else:
                # For SQLite StaticPool, we can't invalidate but we can log
                logger.info("Connection recycling not supported for current pool type (SQLite StaticPool)")
                
        except Exception as e:
            logger.error(f"Error during forced connection recycling: {e}")
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        if self._db_circuit_breaker:
            return self._db_circuit_breaker.get_status()
        return {"status": "not_initialized"}
    
    async def test_connection_with_timeout(self, timeout: float = 5.0) -> bool:
        """
        Test database connection with specified timeout.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            async def test_query():
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
            
            await asyncio.wait_for(test_query(), timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False


# Global connection pool manager
_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get global connection pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


async def init_pool_manager():
    """Initialize global connection pool manager."""
    pool_manager = get_pool_manager()
    await pool_manager.initialize()
    return pool_manager


async def cleanup_pool_manager():
    """Cleanup global connection pool manager."""
    global _pool_manager
    if _pool_manager:
        await _pool_manager.cleanup()
        _pool_manager = None