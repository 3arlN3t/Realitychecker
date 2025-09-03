"""
Database repository classes for the Reality Checker WhatsApp bot.

This module provides repository classes for data access using the
repository pattern with SQLAlchemy.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.logging import get_logger
from .models import (
    WhatsAppUser, UserInteraction, SystemMetric, AnalysisHistory,
    SystemUser, ErrorLog, Configuration, DataRetentionPolicy,
    JobClassificationEnum, UserRoleEnum
)
from app.models.data_models import (
    UserDetails, UserInteraction as DataUserInteraction,
    JobAnalysisResult, JobClassification, UserRole, UserSearchCriteria
)

logger = get_logger(__name__)


class BaseRepository:
    """Base repository class with common functionality."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def commit(self):
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        await self.session.rollback()


class WhatsAppUserRepository(BaseRepository):
    """Repository for WhatsApp user data access."""
    
    async def get_by_phone_number(self, phone_number: str) -> Optional[WhatsAppUser]:
        """
        Get user by phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            WhatsAppUser object or None
        """
        result = await self.session.execute(
            select(WhatsAppUser).where(WhatsAppUser.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, phone_number: str, **kwargs) -> WhatsAppUser:
        """
        Create a new WhatsApp user.
        
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
        return user
    
    async def get_or_create_user(self, phone_number: str) -> WhatsAppUser:
        """
        Get existing user or create new one.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            WhatsAppUser object
        """
        logger.critical(f"🔥 DATABASE CHECK: Attempting to get/create user for phone: {phone_number[:8]}***")
        try:
            user = await self.get_by_phone_number(phone_number)
            if not user:
                logger.critical(f"🔥 DATABASE: User not found, creating new user for {phone_number[:8]}***")
                user = await self.create_user(phone_number)
                await self.commit()
                logger.critical(f"🔥 DATABASE: Successfully created and committed new user ID: {user.id}")
            else:
                logger.critical(f"🔥 DATABASE: Found existing user ID: {user.id}, total_requests: {user.total_requests}")
            return user
        except Exception as e:
            logger.critical(f"🔥 DATABASE ERROR in get_or_create_user: {str(e)}")
            await self.rollback()
            raise
    
    async def update_user_stats(self, user_id: int, interaction_successful: bool, response_time: float):
        """
        Update user statistics after interaction.
        
        Args:
            user_id: User ID
            interaction_successful: Whether interaction was successful
            response_time: Response time in seconds
        """
        logger.critical(f"🔥 DATABASE: Updating stats for user_id {user_id}, successful: {interaction_successful}, response_time: {response_time}")
        try:
            user = await self.session.get(WhatsAppUser, user_id)
            if user:
                old_total = user.total_requests
                user.total_requests += 1
                user.last_interaction = datetime.now(timezone.utc)
                
                if interaction_successful:
                    user.successful_requests += 1
                else:
                    user.failed_requests += 1
                
                # Update average response time
                if user.total_requests > 0:
                    user.avg_response_time = (
                        (user.avg_response_time * (user.total_requests - 1) + response_time) /
                        user.total_requests
                    )
                
                await self.commit()
                logger.critical(f"🔥 DATABASE: Successfully updated user {user_id} stats - total_requests: {old_total} -> {user.total_requests}")
            else:
                logger.critical(f"🔥 DATABASE ERROR: User {user_id} not found when updating stats")
        except Exception as e:
            logger.critical(f"🔥 DATABASE ERROR updating user stats: {str(e)}")
            await self.rollback()
            raise
    
    async def get_users_paginated(
        self, 
        page: int = 1, 
        limit: int = 10,
        search_criteria: Optional[UserSearchCriteria] = None
    ) -> tuple[List[WhatsAppUser], int]:
        """
        Get paginated list of users with optional filtering.
        
        Args:
            page: Page number (1-based)
            limit: Items per page
            search_criteria: Optional search criteria
            
        Returns:
            Tuple of (users_list, total_count)
        """
        logger.critical(f"🔥 DATABASE: Getting paginated users - page: {page}, limit: {limit}")
        try:
            query = select(WhatsAppUser)
            
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
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            total_count = total_result.scalar()
            
            # Get paginated results
            offset = (page - 1) * limit
            query = query.order_by(desc(WhatsAppUser.last_interaction)).offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            users = result.scalars().all()
            
            logger.critical(f"🔥 DATABASE: Found {total_count} total users, returning {len(users)} for this page")
            return list(users), total_count
        except Exception as e:
            logger.critical(f"🔥 DATABASE ERROR getting paginated users: {str(e)}")
            raise
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for dashboard.
        
        Returns:
            Dictionary with user statistics
        """
        # Total users
        total_users = await self.session.execute(select(func.count(WhatsAppUser.id)))
        total_users = total_users.scalar()
        
        # Active users (interacted in last 7 days)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        active_users = await self.session.execute(
            select(func.count(WhatsAppUser.id)).where(WhatsAppUser.last_interaction >= cutoff_date)
        )
        active_users = active_users.scalar()
        
        # Blocked users
        blocked_users = await self.session.execute(
            select(func.count(WhatsAppUser.id)).where(WhatsAppUser.blocked == True)
        )
        blocked_users = blocked_users.scalar()
        
        # Average requests per user
        avg_requests = await self.session.execute(select(func.avg(WhatsAppUser.total_requests)))
        avg_requests = avg_requests.scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "average_requests_per_user": round(avg_requests, 2)
        }
    
    async def block_user(self, user_id: int, notes: Optional[str] = None) -> bool:
        """
        Block a user.
        
        Args:
            user_id: User ID to block
            notes: Optional notes about blocking
            
        Returns:
            True if user was blocked, False if not found
        """
        user = await self.session.get(WhatsAppUser, user_id)
        if user:
            user.blocked = True
            user.notes = notes
            return True
        return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """
        Unblock a user.
        
        Args:
            user_id: User ID to unblock
            
        Returns:
            True if user was unblocked, False if not found
        """
        user = await self.session.get(WhatsAppUser, user_id)
        if user:
            user.blocked = False
            return True
        return False


class UserInteractionRepository(BaseRepository):
    """Repository for user interaction data access."""
    
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
        Create a new user interaction.
        
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
        logger.critical(f"🔥 DATABASE: Creating interaction for user_id {user_id}, type: {message_type}, sid: {message_sid}")
        try:
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
            logger.critical(f"🔥 DATABASE: Successfully created interaction ID: {interaction.id}")
            return interaction
        except Exception as e:
            logger.critical(f"🔥 DATABASE ERROR creating interaction: {str(e)}")
            await self.rollback()
            raise
    
    async def update_interaction_result(
        self,
        interaction_id: int,
        analysis_result: JobAnalysisResult,
        response_time: float,
        processing_time: float
    ):
        """
        Update interaction with analysis result.
        
        Args:
            interaction_id: Interaction ID
            analysis_result: Analysis result from OpenAI
            response_time: Total response time
            processing_time: Processing time
        """
        interaction = await self.session.get(UserInteraction, interaction_id)
        if interaction:
            # Convert trust_score from 0-100 integer to 0.0-1.0 float for database storage
            interaction.trust_score = analysis_result.trust_score / 100.0
            
            # Map JobClassification to JobClassificationEnum
            classification_map = {
                JobClassification.LEGIT: JobClassificationEnum.LEGITIMATE,
                JobClassification.SUSPICIOUS: JobClassificationEnum.SUSPICIOUS,
                JobClassification.LIKELY_SCAM: JobClassificationEnum.SCAM
            }
            interaction.classification = classification_map.get(analysis_result.classification, JobClassificationEnum.SUSPICIOUS)
            
            interaction.classification_reasons = {"reasons": analysis_result.reasons}
            interaction.confidence = analysis_result.confidence
            interaction.response_time = response_time
            interaction.processing_time = processing_time
    
    async def update_interaction_error(
        self,
        interaction_id: int,
        error_type: str,
        error_message: str,
        response_time: float
    ):
        """
        Update interaction with error information.
        
        Args:
            interaction_id: Interaction ID
            error_type: Error type
            error_message: Error message
            response_time: Response time when error occurred
        """
        interaction = await self.session.get(UserInteraction, interaction_id)
        if interaction:
            interaction.error_type = error_type
            interaction.error_message = error_message
            interaction.response_time = response_time
    
    async def get_user_interactions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[UserInteraction]:
        """
        Get user interactions with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of interactions
            offset: Offset for pagination
            
        Returns:
            List of UserInteraction objects
        """
        result = await self.session.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(desc(UserInteraction.timestamp))
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_interaction_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get interaction statistics for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with interaction statistics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total interactions
        total_interactions = await self.session.execute(
            select(func.count(UserInteraction.id))
            .where(UserInteraction.timestamp >= cutoff_date)
        )
        total_interactions = total_interactions.scalar()
        
        # Successful interactions
        successful_interactions = await self.session.execute(
            select(func.count(UserInteraction.id))
            .where(
                and_(
                    UserInteraction.timestamp >= cutoff_date,
                    UserInteraction.error_type.is_(None)
                )
            )
        )
        successful_interactions = successful_interactions.scalar()
        
        # Classification breakdown
        classification_stats = await self.session.execute(
            select(
                UserInteraction.classification,
                func.count(UserInteraction.id).label('count')
            )
            .where(
                and_(
                    UserInteraction.timestamp >= cutoff_date,
                    UserInteraction.classification.is_not(None)
                )
            )
            .group_by(UserInteraction.classification)
        )
        
        classification_breakdown = {}
        for row in classification_stats:
            classification_breakdown[row.classification.value] = row.count
        
        # Average response time
        avg_response_time = await self.session.execute(
            select(func.avg(UserInteraction.response_time))
            .where(UserInteraction.timestamp >= cutoff_date)
        )
        avg_response_time = avg_response_time.scalar() or 0
        
        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "success_rate": (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0,
            "classification_breakdown": classification_breakdown,
            "average_response_time": round(avg_response_time, 2)
        }


class SystemMetricRepository(BaseRepository):
    """Repository for system metrics data access."""
    
    async def record_metric(self, **kwargs) -> SystemMetric:
        """
        Record a new system metric.
        
        Args:
            **kwargs: Metric attributes
            
        Returns:
            Created SystemMetric object
        """
        metric = SystemMetric(**kwargs)
        self.session.add(metric)
        await self.session.flush()
        return metric
    
    async def get_latest_metrics(self, limit: int = 1) -> List[SystemMetric]:
        """
        Get the latest system metrics.
        
        Args:
            limit: Number of metrics to return
            
        Returns:
            List of SystemMetric objects
        """
        result = await self.session.execute(
            select(SystemMetric)
            .order_by(desc(SystemMetric.timestamp))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_metrics_for_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[SystemMetric]:
        """
        Get system metrics for a specific period.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of SystemMetric objects
        """
        result = await self.session.execute(
            select(SystemMetric)
            .where(
                and_(
                    SystemMetric.timestamp >= start_date,
                    SystemMetric.timestamp <= end_date
                )
            )
            .order_by(SystemMetric.timestamp)
        )
        return result.scalars().all()
    
    async def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        Clean up old system metrics.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.session.execute(
            select(func.count(SystemMetric.id))
            .where(SystemMetric.timestamp < cutoff_date)
        )
        count = result.scalar()
        
        if count > 0:
            await self.session.execute(
                text("DELETE FROM system_metrics WHERE timestamp < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
        
        return count


class ConfigurationRepository(BaseRepository):
    """Repository for configuration data access."""
    
    async def get_config(self, key: str) -> Optional[Configuration]:
        """
        Get configuration by key.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration object or None
        """
        result = await self.session.execute(
            select(Configuration).where(Configuration.key == key)
        )
        return result.scalar_one_or_none()
    
    async def set_config(self, key: str, value: str, description: Optional[str] = None, category: str = "general") -> Configuration:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Configuration description
            category: Configuration category
            
        Returns:
            Configuration object
        """
        config = await self.get_config(key)
        if config:
            config.value = value
            if description:
                config.description = description
            config.category = category
        else:
            config = Configuration(
                key=key,
                value=value,
                description=description,
                category=category
            )
            self.session.add(config)
        
        await self.session.flush()
        return config
    
    async def get_all_configs(self, category: Optional[str] = None) -> List[Configuration]:
        """
        Get all configurations, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of Configuration objects
        """
        query = select(Configuration)
        if category:
            query = query.where(Configuration.category == category)
        
        result = await self.session.execute(query.order_by(Configuration.key))
        return result.scalars().all()


class ErrorLogRepository(BaseRepository):
    """Repository for error log data access."""
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        severity: str = "ERROR",
        **kwargs
    ) -> ErrorLog:
        """
        Log an error.
        
        Args:
            error_type: Error type
            error_message: Error message
            component: Component where error occurred
            severity: Error severity
            **kwargs: Additional error attributes
            
        Returns:
            Created ErrorLog object
        """
        error_log = ErrorLog(
            error_type=error_type,
            error_message=error_message,
            component=component,
            severity=severity,
            **kwargs
        )
        self.session.add(error_log)
        await self.session.flush()
        return error_log
    
    async def get_recent_errors(self, limit: int = 100) -> List[ErrorLog]:
        """
        Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of ErrorLog objects
        """
        result = await self.session.execute(
            select(ErrorLog)
            .order_by(desc(ErrorLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_error_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get error statistics for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with error statistics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total errors
        total_errors = await self.session.execute(
            select(func.count(ErrorLog.id))
            .where(ErrorLog.timestamp >= cutoff_date)
        )
        total_errors = total_errors.scalar()
        
        # Errors by component
        component_stats = await self.session.execute(
            select(
                ErrorLog.component,
                func.count(ErrorLog.id).label('count')
            )
            .where(ErrorLog.timestamp >= cutoff_date)
            .group_by(ErrorLog.component)
        )
        
        component_breakdown = {}
        for row in component_stats:
            component_breakdown[row.component] = row.count
        
        # Errors by severity
        severity_stats = await self.session.execute(
            select(
                ErrorLog.severity,
                func.count(ErrorLog.id).label('count')
            )
            .where(ErrorLog.timestamp >= cutoff_date)
            .group_by(ErrorLog.severity)
        )
        
        severity_breakdown = {}
        for row in severity_stats:
            severity_breakdown[row.severity] = row.count
        
        return {
            "total_errors": total_errors,
            "component_breakdown": component_breakdown,
            "severity_breakdown": severity_breakdown
        }