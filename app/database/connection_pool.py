"""
Enhanced database connection pool management with performance optimizations.

This module provides advanced connection pooling, caching, and database
performance optimizations for the Reality Checker application.
"""

import os
import asyncio
import logging
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
from app.config import get_config

logger = get_logger(__name__)


class ConnectionPoolManager:
    """
    Advanced connection pool manager with Redis caching and performance monitoring.
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
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_size": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalidated": 0
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
        """Initialize connection pool and Redis cache."""
        if self._initialized:
            return
        
        try:
            # Initialize database engine with optimized connection pooling
            await self._initialize_database_engine()
            
            # Initialize Redis cache
            await self._initialize_redis_cache()
            
            # Setup connection pool monitoring
            self._setup_pool_monitoring()
            
            self._initialized = True
            logger.info("✅ Connection pool manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool manager: {e}")
            raise
    
    async def _initialize_database_engine(self):
        """Initialize database engine with optimized settings."""
        if self.database_url.startswith('sqlite'):
            # SQLite configuration with WAL mode and optimizations
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                    "isolation_level": None  # Enable autocommit mode
                },
                # SQLite-specific optimizations
                pool_pre_ping=True,
                pool_recycle=3600,
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
            # Optimized defaults for production workloads
            pool_size = int(os.getenv('DB_POOL_SIZE', '15'))  # Reduced from 20 for better resource usage
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '25'))  # Reduced from 30
            pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '20'))  # Reduced from 30 for faster timeouts
            pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # Reduced from 3600 (30min vs 1hr)
            
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                # Advanced connection pooling
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=True,
                # Connection optimization
                connect_args={
                    "server_settings": {
                        "application_name": "reality_checker",
                        "jit": "off",  # Disable JIT for faster connection
                        "shared_preload_libraries": "",  # Reduce startup overhead
                        "max_connections": "200",  # Ensure server can handle pool + overflow
                    },
                    "command_timeout": 45,  # Reduced from 60 for faster timeouts
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
        
        logger.info(f"Database engine initialized: {self._sanitize_url(self.database_url)}")
    
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
        Get optimized database session with automatic cleanup.
        
        Yields:
            AsyncSession: Database session with performance optimizations
        """
        if not self._initialized:
            await self.initialize()
        
        session = self.session_factory()
        try:
            # Enable query optimization hints
            await session.execute(text("-- Query optimization enabled"))
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get cached result from Redis.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached result or None
        """
        if not self.redis_client:
            return None
        
        try:
            result = await self.redis_client.get(cache_key)
            if result:
                import json
                return json.loads(result)
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
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str)
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
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = self._connection_stats.copy()
        
        if self.engine and hasattr(self.engine.pool, 'size'):
            stats.update({
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "invalid": self.engine.pool.invalid()
            })
        
        # Add Redis stats if available
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info()
                stats["redis_connected_clients"] = redis_info.get("connected_clients", 0)
                stats["redis_used_memory"] = redis_info.get("used_memory_human", "0B")
                stats["redis_keyspace_hits"] = redis_info.get("keyspace_hits", 0)
                stats["redis_keyspace_misses"] = redis_info.get("keyspace_misses", 0)
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health check results
        """
        health = {
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "connection_pool": {"status": "unknown"}
        }
        
        # Database health check
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                health["database"] = {
                    "status": "healthy",
                    "type": "postgresql" if "postgresql" in self.database_url else "sqlite"
                }
        except Exception as e:
            health["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Redis health check
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis"] = {"status": "healthy"}
            except Exception as e:
                health["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health["redis"] = {"status": "not_configured"}
        
        # Connection pool health
        try:
            pool_stats = await self.get_pool_stats()
            health["connection_pool"] = {
                "status": "healthy",
                "stats": pool_stats
            }
        except Exception as e:
            health["connection_pool"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return health
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up connection pool manager...")
        
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