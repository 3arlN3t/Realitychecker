"""
Database query optimization utilities.

This module provides query optimization, indexing strategies, and
performance monitoring for database operations.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager

from sqlalchemy import text, Index, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.utils.logging import get_logger
from app.database.connection_pool import get_pool_manager

logger = get_logger(__name__)


class QueryOptimizer:
    """
    Database query optimization and performance monitoring.
    """
    
    def __init__(self):
        """Initialize query optimizer."""
        self.pool_manager = get_pool_manager()
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second
        
    def track_query_performance(self, query_name: str):
        """
        Decorator to track query performance.
        
        Args:
            query_name: Name of the query for tracking
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Track query statistics
                    if query_name not in self.query_stats:
                        self.query_stats[query_name] = {
                            "count": 0,
                            "total_time": 0,
                            "avg_time": 0,
                            "max_time": 0,
                            "min_time": float('inf'),
                            "slow_queries": 0
                        }
                    
                    stats = self.query_stats[query_name]
                    stats["count"] += 1
                    stats["total_time"] += execution_time
                    stats["avg_time"] = stats["total_time"] / stats["count"]
                    stats["max_time"] = max(stats["max_time"], execution_time)
                    stats["min_time"] = min(stats["min_time"], execution_time)
                    
                    if execution_time > self.slow_query_threshold:
                        stats["slow_queries"] += 1
                        logger.warning(
                            f"Slow query detected: {query_name} took {execution_time:.3f}s"
                        )
                    
                    logger.debug(f"Query {query_name} executed in {execution_time:.3f}s")
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"Query {query_name} failed after {execution_time:.3f}s: {e}")
                    raise
            
            return wrapper
        return decorator
    
    async def optimize_user_queries(self, session: AsyncSession):
        """
        Apply optimizations for user-related queries.
        
        Args:
            session: Database session
        """
        # Create indexes for frequently queried columns
        indexes_to_create = [
            "CREATE INDEX IF NOT EXISTS idx_whatsapp_users_phone_lookup ON whatsapp_users(phone_number) WHERE blocked = false",
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_recent ON user_interactions(user_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_classification_stats ON user_interactions(classification, timestamp) WHERE error_type IS NULL",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_recent ON system_metrics(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_error_logs_recent ON error_logs(timestamp DESC, severity)",
        ]
        
        for index_sql in indexes_to_create:
            try:
                await session.execute(text(index_sql))
                logger.debug(f"Index created/verified: {index_sql}")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
    
    async def analyze_table_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Analyze table statistics for optimization insights.
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with table statistics
        """
        stats = {}
        
        try:
            # Get table row counts
            tables = [
                "whatsapp_users",
                "user_interactions", 
                "system_metrics",
                "error_logs",
                "analysis_history"
            ]
            
            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    stats[table] = {"row_count": count}
                except Exception as e:
                    logger.warning(f"Failed to get count for table {table}: {e}")
                    stats[table] = {"row_count": 0, "error": str(e)}
            
            # Get database size information
            try:
                if "postgresql" in str(session.bind.url):
                    # PostgreSQL specific queries
                    result = await session.execute(text("""
                        SELECT 
                            schemaname,
                            tablename,
                            attname,
                            n_distinct,
                            correlation
                        FROM pg_stats 
                        WHERE schemaname = 'public'
                        ORDER BY tablename, attname
                    """))
                    
                    pg_stats = []
                    for row in result:
                        pg_stats.append({
                            "table": row.tablename,
                            "column": row.attname,
                            "distinct_values": row.n_distinct,
                            "correlation": row.correlation
                        })
                    
                    stats["postgresql_stats"] = pg_stats
                
                else:
                    # SQLite specific queries
                    result = await session.execute(text("PRAGMA database_list"))
                    db_info = [dict(row._mapping) for row in result]
                    stats["sqlite_info"] = db_info
                    
            except Exception as e:
                logger.warning(f"Failed to get database statistics: {e}")
        
        except Exception as e:
            logger.error(f"Failed to analyze table statistics: {e}")
        
        return stats
    
    def get_optimized_user_query(self, include_interactions: bool = False) -> Select:
        """
        Get optimized query for user data retrieval.
        
        Args:
            include_interactions: Whether to include user interactions
            
        Returns:
            Optimized SQLAlchemy select query
        """
        from app.database.models import WhatsAppUser, UserInteraction
        
        query = select(WhatsAppUser)
        
        if include_interactions:
            # Use selectinload for better performance with large datasets
            query = query.options(
                selectinload(WhatsAppUser.interactions).options(
                    # Limit interactions to recent ones
                    selectinload(UserInteraction).limit(10)
                )
            )
        
        return query
    
    def get_optimized_analytics_query(self, days: int = 30) -> Select:
        """
        Get optimized query for analytics data.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Optimized analytics query
        """
        from app.database.models import UserInteraction
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Optimized query with proper indexing hints
        query = select(
            UserInteraction.classification,
            func.count(UserInteraction.id).label('count'),
            func.avg(UserInteraction.trust_score).label('avg_trust_score'),
            func.avg(UserInteraction.response_time).label('avg_response_time')
        ).where(
            UserInteraction.timestamp >= cutoff_date
        ).group_by(
            UserInteraction.classification
        )
        
        return query
    
    async def optimize_database_settings(self, session: AsyncSession):
        """
        Apply database-specific optimizations.
        
        Args:
            session: Database session
        """
        try:
            if "postgresql" in str(session.bind.url):
                # PostgreSQL optimizations
                optimizations = [
                    "SET work_mem = '256MB'",
                    "SET maintenance_work_mem = '512MB'",
                    "SET effective_cache_size = '1GB'",
                    "SET random_page_cost = 1.1",
                    "SET seq_page_cost = 1.0"
                ]
                
                for optimization in optimizations:
                    try:
                        await session.execute(text(optimization))
                        logger.debug(f"Applied PostgreSQL optimization: {optimization}")
                    except Exception as e:
                        logger.warning(f"Failed to apply optimization {optimization}: {e}")
            
            else:
                # SQLite optimizations (already applied in connection_pool.py)
                logger.debug("SQLite optimizations applied at connection level")
                
        except Exception as e:
            logger.error(f"Failed to optimize database settings: {e}")
    
    async def cleanup_old_data(self, session: AsyncSession, days: int = 90):
        """
        Clean up old data to maintain performance.
        
        Args:
            session: Database session
            days: Number of days to retain data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cleanup_queries = [
            # Clean up old system metrics (keep last 30 days)
            f"DELETE FROM system_metrics WHERE timestamp < '{cutoff_date - timedelta(days=60)}'",
            
            # Clean up old error logs (keep last 90 days)
            f"DELETE FROM error_logs WHERE timestamp < '{cutoff_date}'",
            
            # Clean up old analysis history (keep last 90 days)
            f"DELETE FROM analysis_history WHERE timestamp < '{cutoff_date}'",
        ]
        
        for query in cleanup_queries:
            try:
                result = await session.execute(text(query))
                deleted_count = result.rowcount
                logger.info(f"Cleaned up {deleted_count} old records: {query}")
            except Exception as e:
                logger.error(f"Failed to cleanup old data: {e}")
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """
        Get query performance statistics.
        
        Returns:
            Dictionary with query statistics
        """
        return {
            "query_stats": self.query_stats,
            "slow_query_threshold": self.slow_query_threshold,
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "total_slow_queries": sum(stats["slow_queries"] for stats in self.query_stats.values())
        }


class OptimizedRepository:
    """
    Base repository class with query optimizations.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize optimized repository."""
        self.session = session
        self.optimizer = QueryOptimizer()
    
    @asynccontextmanager
    async def optimized_transaction(self):
        """
        Context manager for optimized database transactions.
        """
        try:
            # Apply session-level optimizations
            await self.session.execute(text("-- Optimized transaction start"))
            yield self.session
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Optimized transaction failed: {e}")
            raise
    
    async def bulk_insert(self, model_class, data_list: List[Dict[str, Any]]) -> int:
        """
        Perform optimized bulk insert.
        
        Args:
            model_class: SQLAlchemy model class
            data_list: List of data dictionaries
            
        Returns:
            Number of inserted records
        """
        if not data_list:
            return 0
        
        try:
            # Use bulk insert for better performance
            objects = [model_class(**data) for data in data_list]
            self.session.add_all(objects)
            await self.session.flush()
            
            logger.info(f"Bulk inserted {len(objects)} {model_class.__name__} records")
            return len(objects)
            
        except Exception as e:
            logger.error(f"Bulk insert failed for {model_class.__name__}: {e}")
            raise
    
    async def paginated_query(
        self, 
        query: Select, 
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[List[Any], int]:
        """
        Execute paginated query with optimization.
        
        Args:
            query: SQLAlchemy select query
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Tuple of (results, total_count)
        """
        # Get total count efficiently
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        
        result = await self.session.execute(paginated_query)
        items = result.scalars().all()
        
        return list(items), total_count


# Global query optimizer instance
_query_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer instance."""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer