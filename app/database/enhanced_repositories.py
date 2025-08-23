"""
Enhanced repository classes with caching and performance optimizations.

This module provides high-performance repository classes that leverage
caching, query optimization, and bulk operations for better scalability.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSessionlalchemy.orm import selectinload

from app.utils.logging import get_logger
from app.database.repositories import BaseRepository
from app.database.query_optimizer import OptimizedRepository, get_query_optimizer
from app.services.caching_service import get_caching_service, CacheKey, cache_result
from app.database.models import (
    WhatsAppUser, UserInteraction, SystemMetric, AnalysisHistory,
    SystemUser, ErrorLog, Configuration, DataRetentionPolicy,
    JobClassificationEnum, UserRoleEnum
)
from app.models.data_models import (
    UserDetails, UserInteraction as DataUserInteraction,
    JobAnalysisResult, JobClassification, UserRole, UserSearchCriteria
)

logger = get_logger(__name__)


class EnhancedWhatsAppUserRepository(OptimizedRepository):
    """Enhanced WhatsApp user repository with caching and performance optimizations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.caching_service = get_caching_service()
    
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_by_phone_number(self, phone_number: str) -> Optional[WhatsAppUser]:
        """
        Get user by phone number with caching.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            WhatsAppUser object or None
        """
        query = select(WhatsAppUser).where(WhatsAppUser.phone_number == phone_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_user(self, phone_number: str, **kwargs) -> WhatsAppUser:
        """
        Create a new WhatsApp user with cache invalidation.
        
        Args:
            phone_number: User's phone number
            **kwargs: Additional user attributes
            
        Returns:
            Created WhatsAppUser object
        """
        user = WhatsAppUser(
            phone_number=phone_number,
            **kwargs
        )
        self.session.add(user)
        await self.session.flush()
        
        # Invalidate related caches
        await self.caching_service.invalidate_pattern(f"user:*")
        await self.caching_service.invalidate_pattern("dashboard:*")
        
        logger.info(f"Created new user: {user.sanitized_phone_number}")
        return user
    
    async def get_or_create_user(self, phone_number: str) -> WhatsAppUser:
        """
        Get existing user or create new one with optimized caching.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            WhatsAppUser object
        """
        # Try cache first
        cache_key = f"user:phone:{phone_number}"
        cached_user = await self.caching_service.get(cache_key)
        
        if cached_user:
            # Reconstruct user object from cache
            user = WhatsAppUser(**cached_user)
            return user
        
        # Query database
        user = await self.get_by_phone_number(phone_number)
        if not user:
            user = await self.create_user(phone_number)
        
        # Cache the user
        await self.caching_service.set(cache_key, user.__dict__, 300)
        
        return user
    
    @get_query_optimizer().track_query_performance("update_user_stats")
    async def update_user_stats(self, user_id: int, interaction_successful: bool, response_time: float):
        """
        Update user statistics with optimized query and cache invalidation.
        
        Args:
            user_id: User ID
            interaction_successful: Whether interaction was successful
            response_time: Response time in seconds
        """
        user = await self.session.get(WhatsAppUser, user_id)
        if user:
            user.total_requests += 1
            user.last_interaction = datetime.now(timezone.utc)
            
            if interaction_successful:
                user.successful_requests += 1
            else:
                user.failed_requests += 1
            
            # Update average response time using incremental calculation
            if user.total_requests > 0:
                user.avg_response_time = (
                    (user.avg_response_time * (user.total_requests - 1) + response_time) /
                    user.total_requests
                )
            
            # Invalidate user-related caches
            await self.caching_service.invalidate_pattern(f"user:*:{user_id}")
            await self.caching_service.invalidate_pattern(f"user:phone:{user.phone_number}")
    
    async def get_users_paginated_cached(
        self, 
        page: int = 1, 
        limit: int = 10,
        search_criteria: Optional[UserSearchCriteria] = None
    ) -> Tuple[List[WhatsAppUser], int]:
        """
        Get paginated list of users with caching and optimization.
        
        Args:
            page: Page number (1-based)
            limit: Items per page
            search_criteria: Optional search criteria
            
        Returns:
            Tuple of (users_list, total_count)
        """
        # Generate cache key based on parameters
        cache_key = f"users:paginated:{page}:{limit}:{hash(str(search_criteria))}"
        
        # Try cache first
        cached_result = await self.caching_service.get(cache_key)
        if cached_result:
            users_data, total_count = cached_result
            users = [WhatsAppUser(**user_data) for user_data in users_data]
            return users, total_count
        
        # Use optimized query
        query = self.optimizer.get_optimized_user_query(include_interactions=False)
        
        # Apply search criteria
        if search_criteria:
            if search_criteria.phone_number:
                query = query.where(WhatsAppUser.phone_number.contains(search_criteria.phone_number))
            if search_criteria.blocked is not None:
                query = query.where(WhatsAppUser.blocked == search_criteria.blocked)
            if search_criteria.min_requests is not None:
                query = query.where(WhatsAppUser.total_requests >= search_criteria.min_requests)
            if search_criteria.max_requests is not None:
                query = query.where(WhatsAppUser.total_requests <= search_criteria.max_requests)
            if search_criteria.days_since_last_interaction is not None:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=search_criteria.days_since_last_interaction)
                query = query.where(WhatsAppUser.last_interaction <= cutoff_date)
        
        # Execute paginated query
        users, total_count = await self.paginated_query(query, page, limit)
        
        # Cache the result
        users_data = [user.__dict__ for user in users]
        await self.caching_service.set(cache_key, (users_data, total_count), 180)  # 3 minutes
        
        return users, total_count
    
    @cache_result(ttl=600)  # Cache for 10 minutes
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics with caching and optimization.
        
        Returns:
            Dictionary with user statistics
        """
        # Use optimized bulk query
        stats_query = select(
            func.count(WhatsAppUser.id).label('total_users'),
            func.count(WhatsAppUser.id).filter(
                WhatsAppUser.last_interaction >= datetime.now(timezone.utc) - timedelta(days=7)
            ).label('active_users'),
            func.count(WhatsAppUser.id).filter(WhatsAppUser.blocked == True).label('blocked_users'),
            func.avg(WhatsAppUser.total_requests).label('avg_requests')
        )
        
        result = await self.session.execute(stats_query)
        row = result.first()
        
        return {
            "total_users": row.total_users or 0,
            "active_users": row.active_users or 0,
            "blocked_users": row.blocked_users or 0,
            "average_requests_per_user": round(row.avg_requests or 0, 2)
        }


class EnhancedUserInteractionRepository(OptimizedRepository):
    """Enhanced user interaction repository with performance optimizations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.caching_service = get_caching_service()
    
    async def create_interaction(
        self,
        user_id: int,
        message_sid: str,
        message_type: str,
        message_content: Optional[str] = None,
        media_url: Optional[str] = None,
        media_content_type: Optional[str] = None,
        **kwargs
    ) -> UserInteraction:
        """
        Create a new user interaction with cache invalidation.
        
        Args:
            user_id: User ID
            message_sid: Twilio message SID
            message_type: Message type ('text' or 'pdf')
            message_content: Message content (truncated)
            media_url: Media URL if present
            media_content_type: Media content type
            **kwargs: Additional interaction attributes
            
        Returns:
            Created UserInteraction object
        """
        interaction = UserInteraction(
            user_id=user_id,
            message_sid=message_sid,
            message_type=message_type,
            message_content=message_content[:200] if message_content else None,
            media_url=media_url,
            media_content_type=media_content_type,
            **kwargs
        )
        self.session.add(interaction)
        await self.session.flush()
        
        # Invalidate related caches
        await self.caching_service.invalidate_pattern(f"user_interactions:{user_id}:*")
        await self.caching_service.invalidate_pattern("analytics:*")
        await self.caching_service.invalidate_pattern("dashboard:*")
        
        return interaction
    
    @get_query_optimizer().track_query_performance("update_interaction_result")
    async def update_interaction_result(
        self,
        interaction_id: int,
        analysis_result: JobAnalysisResult,
        response_time: float,
        processing_time: float
    ):
        """
        Update interaction with analysis result and cache management.
        
        Args:
            interaction_id: Interaction ID
            analysis_result: Analysis result from OpenAI
            response_time: Total response time
            processing_time: Processing time
        """
        interaction = await self.session.get(UserInteraction, interaction_id)
        if interaction:
            interaction.trust_score = analysis_result.trust_score
            interaction.classification = JobClassificationEnum(analysis_result.classification.value)
            interaction.classification_reasons = {"reasons": analysis_result.reasons}
            interaction.confidence = analysis_result.confidence
            interaction.response_time = response_time
            interaction.processing_time = processing_time
            
            # Invalidate related caches
            await self.caching_service.invalidate_pattern(f"user_interactions:{interaction.user_id}:*")
            await self.caching_service.invalidate_pattern("analytics:*")
    
    @cache_result(ttl=180)  # Cache for 3 minutes
    async def get_user_interactions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[UserInteraction]:
        """
        Get user interactions with caching and optimization.
        
        Args:
            user_id: User ID
            limit: Maximum number of interactions
            offset: Offset for pagination
            
        Returns:
            List of UserInteraction objects
        """
        query = select(UserInteraction).where(
            UserInteraction.user_id == user_id
        ).order_by(
            desc(UserInteraction.timestamp)
        ).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_interaction_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get interaction statistics with optimized queries and caching.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with interaction statistics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Use optimized analytics query
        analytics_query = self.optimizer.get_optimized_analytics_query(days)
        
        # Execute bulk statistics query
        stats_query = select(
            func.count(UserInteraction.id).label('total_interactions'),
            func.count(UserInteraction.id).filter(
                UserInteraction.error_type.is_(None)
            ).label('successful_interactions'),
            func.avg(UserInteraction.response_time).label('avg_response_time')
        ).where(UserInteraction.timestamp >= cutoff_date)
        
        stats_result = await self.session.execute(stats_query)
        stats_row = stats_result.first()
        
        # Get classification breakdown
        classification_result = await self.session.execute(analytics_query)
        classification_breakdown = {}
        
        for row in classification_result:
            if row.classification:
                classification_breakdown[row.classification.value] = {
                    "count": row.count,
                    "avg_trust_score": round(row.avg_trust_score or 0, 2),
                    "avg_response_time": round(row.avg_response_time or 0, 2)
                }
        
        total_interactions = stats_row.total_interactions or 0
        successful_interactions = stats_row.successful_interactions or 0
        
        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "success_rate": (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0,
            "classification_breakdown": classification_breakdown,
            "average_response_time": round(stats_row.avg_response_time or 0, 2)
        }


class EnhancedSystemMetricRepository(OptimizedRepository):
    """Enhanced system metrics repository with bulk operations and caching."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.caching_service = get_caching_service()
    
    async def record_metrics_batch(self, metrics_list: List[Dict[str, Any]]) -> int:
        """
        Record multiple system metrics in batch for better performance.
        
        Args:
            metrics_list: List of metric dictionaries
            
        Returns:
            Number of metrics recorded
        """
        if not metrics_list:
            return 0
        
        # Use bulk insert for better performance
        count = await self.bulk_insert(SystemMetric, metrics_list)
        
        # Invalidate metrics cache
        await self.caching_service.invalidate_pattern("system:metrics*")
        
        return count
    
    @cache_result(ttl=60)  # Cache for 1 minute
    async def get_latest_metrics(self, limit: int = 1) -> List[SystemMetric]:
        """
        Get the latest system metrics with caching.
        
        Args:
            limit: Number of metrics to return
            
        Returns:
            List of SystemMetric objects
        """
        query = select(SystemMetric).order_by(
            desc(SystemMetric.timestamp)
        ).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    @get_query_optimizer().track_query_performance("cleanup_old_metrics")
    async def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        Clean up old system metrics with optimized bulk delete.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Use optimized bulk delete
        delete_query = text("""
            DELETE FROM system_metrics 
            WHERE timestamp < :cutoff_date
        """)
        
        result = await self.session.execute(delete_query, {"cutoff_date": cutoff_date})
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old system metrics")
            # Invalidate metrics cache
            await self.caching_service.invalidate_pattern("system:metrics*")
        
        return deleted_count


class EnhancedAnalyticsRepository(OptimizedRepository):
    """Enhanced analytics repository with advanced caching and aggregations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.caching_service = get_caching_service()
    
    @cache_result(ttl=600)  # Cache for 10 minutes
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics with caching.
        
        Returns:
            Dictionary with dashboard metrics
        """
        # Use complex aggregation query for efficiency
        dashboard_query = select(
            # User metrics
            func.count(func.distinct(WhatsAppUser.id)).label('total_users'),
            func.count(func.distinct(WhatsAppUser.id)).filter(
                WhatsAppUser.last_interaction >= datetime.now(timezone.utc) - timedelta(days=7)
            ).label('active_users'),
            
            # Interaction metrics
            func.count(UserInteraction.id).label('total_interactions'),
            func.count(UserInteraction.id).filter(
                UserInteraction.timestamp >= datetime.now(timezone.utc) - timedelta(days=1)
            ).label('interactions_today'),
            
            # Performance metrics
            func.avg(UserInteraction.response_time).label('avg_response_time'),
            func.count(UserInteraction.id).filter(
                UserInteraction.error_type.is_not(None)
            ).label('error_count')
        ).select_from(
            WhatsAppUser.__table__.outerjoin(UserInteraction.__table__)
        )
        
        result = await self.session.execute(dashboard_query)
        row = result.first()
        
        return {
            "total_users": row.total_users or 0,
            "active_users": row.active_users or 0,
            "total_interactions": row.total_interactions or 0,
            "interactions_today": row.interactions_today or 0,
            "avg_response_time": round(row.avg_response_time or 0, 2),
            "error_count": row.error_count or 0,
            "success_rate": (
                ((row.total_interactions or 0) - (row.error_count or 0)) / 
                (row.total_interactions or 1) * 100
            )
        }
    
    @cache_result(ttl=1800)  # Cache for 30 minutes
    async def get_classification_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get classification trends with advanced caching.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with classification trends
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Daily classification trends
        trends_query = select(
            func.date(UserInteraction.timestamp).label('date'),
            UserInteraction.classification,
            func.count(UserInteraction.id).label('count'),
            func.avg(UserInteraction.trust_score).label('avg_trust_score')
        ).where(
            and_(
                UserInteraction.timestamp >= cutoff_date,
                UserInteraction.classification.is_not(None)
            )
        ).group_by(
            func.date(UserInteraction.timestamp),
            UserInteraction.classification
        ).order_by(
            func.date(UserInteraction.timestamp)
        )
        
        result = await self.session.execute(trends_query)
        
        trends = {}
        for row in result:
            date_str = row.date.isoformat()
            if date_str not in trends:
                trends[date_str] = {}
            
            trends[date_str][row.classification.value] = {
                "count": row.count,
                "avg_trust_score": round(row.avg_trust_score or 0, 2)
            }
        
        return trends


# Factory functions for enhanced repositories
def get_enhanced_user_repository(session: AsyncSession) -> EnhancedWhatsAppUserRepository:
    """Get enhanced WhatsApp user repository."""
    return EnhancedWhatsAppUserRepository(session)


def get_enhanced_interaction_repository(session: AsyncSession) -> EnhancedUserInteractionRepository:
    """Get enhanced user interaction repository."""
    return EnhancedUserInteractionRepository(session)


def get_enhanced_metrics_repository(session: AsyncSession) -> EnhancedSystemMetricRepository:
    """Get enhanced system metrics repository."""
    return EnhancedSystemMetricRepository(session)


def get_enhanced_analytics_repository(session: AsyncSession) -> EnhancedAnalyticsRepository:
    """Get enhanced analytics repository."""
    return EnhancedAnalyticsRepository(session)