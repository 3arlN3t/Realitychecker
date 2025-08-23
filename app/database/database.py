"""
Database configuration and connection management.

This module provides database connectivity using SQLAlchemy with support
for both SQLite (development) and PostgreSQL (production), enhanced with
connection pooling, caching, and performance optimizations.
"""

import os
import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event, text
from sqlalchemy.pool import StaticPool

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Create declarative base for models
Base = declarative_base()

class Database:
    """Enhanced database connection and session management with performance optimizations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection with enhanced pooling and caching.
        
        Args:
            database_url: Database connection URL. If None, will use environment variables.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.session_factory = None
        self._initialized = False
        self._pool_manager = None
        logger.info(f"Database configured with URL: {self._sanitize_url(self.database_url)}")
    
    def _get_database_url(self) -> str:
        """
        Get database URL from environment variables.
        
        Returns:
            Database connection URL
        """
        # Check for PostgreSQL configuration first
        if all(env_var in os.environ for env_var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']):
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME')
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        
        # Default to SQLite for development
        db_path = os.getenv('DATABASE_PATH', 'data/reality_checker.db')
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        return f"sqlite+aiosqlite:///{db_path}"
    
    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize database URL for logging (hide passwords).
        
        Args:
            url: Database URL to sanitize
            
        Returns:
            Sanitized URL safe for logging
        """
        if '://' in url:
            scheme, rest = url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                if ':' in credentials:
                    user, _ = credentials.split(':', 1)
                    return f"{scheme}://{user}:***@{host_part}"
        return url
    
    async def initialize(self):
        """Initialize database connection with enhanced pooling and optimizations."""
        if self._initialized:
            return
        
        try:
            # Initialize connection pool manager
            from .connection_pool import get_pool_manager
            self._pool_manager = get_pool_manager()
            await self._pool_manager.initialize()
            
            # Use the optimized engine from pool manager
            self.engine = self._pool_manager.engine
            self.session_factory = self._pool_manager.session_factory
            
            # Import models to ensure they are registered
            from .models import (
                WhatsAppUser, UserInteraction, SystemMetric, AnalysisHistory,
                SystemUser, ErrorLog, Configuration, DataRetentionPolicy
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Apply database optimizations
            from .query_optimizer import get_query_optimizer
            optimizer = get_query_optimizer()
            
            async with self.get_session() as session:
                await optimizer.optimize_user_queries(session)
                await optimizer.optimize_database_settings(session)
                await session.commit()
            
            # Initialize caching service
            from app.services.caching_service import init_caching_service
            await init_caching_service()
            
            self._initialized = True
            logger.info("✅ Enhanced database initialized successfully with pooling and caching")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced database: {e}")
            raise
    
    async def close(self):
        """Close database connection and cleanup resources."""
        if self._pool_manager:
            await self._pool_manager.cleanup()
            self._pool_manager = None
        
        if self.engine:
            await self.engine.dispose()
            
        self._initialized = False
        logger.info("✅ Enhanced database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get optimized database session with automatic cleanup and performance monitoring.
        
        Yields:
            AsyncSession: Enhanced database session
        """
        if not self._initialized:
            await self.initialize()
        
        # Use the pool manager's optimized session
        if self._pool_manager:
            async with self._pool_manager.get_session() as session:
                yield session
        else:
            # Fallback to standard session
            async with self.session_factory() as session:
                try:
                    yield session
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Database session error: {e}")
                    raise
                finally:
                    await session.close()
    
    async def health_check(self) -> dict:
        """
        Perform comprehensive database health check with performance metrics.
        
        Returns:
            Dict containing detailed health status information
        """
        try:
            if self._pool_manager:
                # Use enhanced health check from pool manager
                health_info = await self._pool_manager.health_check()
                
                # Add database-specific information
                health_info.update({
                    "database_type": "postgresql" if "postgresql" in self.database_url else "sqlite",
                    "connection_url": self._sanitize_url(self.database_url),
                    "initialized": self._initialized,
                    "enhanced_features": True
                })
                
                return health_info
            else:
                # Fallback health check
                async with self.get_session() as session:
                    result = await session.execute(text("SELECT 1"))
                    result.scalar()
                    
                    return {
                        "status": "healthy",
                        "database_type": "postgresql" if "postgresql" in self.database_url else "sqlite",
                        "connection_url": self._sanitize_url(self.database_url),
                        "initialized": self._initialized,
                        "enhanced_features": False
                    }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_type": "postgresql" if "postgresql" in self.database_url else "sqlite",
                "connection_url": self._sanitize_url(self.database_url),
                "initialized": self._initialized
            }
    
    async def execute_raw(self, query: str, params: Optional[dict] = None):
        """
        Execute raw SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            await session.commit()
            return result

# Global database instance
_database: Optional[Database] = None

def get_database() -> Database:
    """Get global database instance."""
    global _database
    if _database is None:
        _database = Database()
    return _database

async def init_database():
    """Initialize global database instance."""
    db = get_database()
    await db.initialize()
    return db

async def close_database():
    """Close global database instance."""
    global _database
    if _database:
        await _database.close()
        _database = None