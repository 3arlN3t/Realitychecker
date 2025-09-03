"""
User management service for the Reality Checker WhatsApp bot.

This module provides the UserManagementService class for tracking WhatsApp user
interactions, managing user sessions, and providing user blocking/unblocking functionality.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import threading
import asyncio
from collections import defaultdict
import math

from app.models.data_models import (
    UserDetails, UserInteraction, UserList, UserSearchCriteria,
    JobAnalysisResult, AppConfig, JobClassification
)
from app.utils.logging import get_logger, log_with_context, sanitize_phone_number
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from app.database.repositories import WhatsAppUserRepository, UserInteractionRepository
from app.database.models import WhatsAppUser, UserInteraction as DBUserInteraction, JobClassificationEnum


logger = get_logger(__name__)


class UserManagementService:
    """
    Service for managing WhatsApp user interactions and session tracking.
    
    This service provides functionality for:
    - Tracking user interactions and maintaining session history
    - User blocking/unblocking functionality
    - User search and filtering capabilities
    - User analytics and insights
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the user management service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Create simple database connection without complex initialization
        db_path = os.getenv('DATABASE_PATH', 'data/reality_checker.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        database_url = f"sqlite+aiosqlite:///{db_path}"
        
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
        logger.info("UserManagementService initialized with direct database connection")
    
    async def record_interaction(self, 
                               phone_number: str,
                               message_type: str,
                               message_content: Optional[str] = None,
                               analysis_result: Optional[JobAnalysisResult] = None,
                               response_time: float = 0.0,
                               error: Optional[str] = None,
                               message_sid: Optional[str] = None,
                               source: str = "whatsapp") -> None:
        """
        Record a user interaction with the bot.
        
        Args:
            phone_number: User's WhatsApp phone number (format: whatsapp:+1234567890)
            message_type: Type of message ("text" or "pdf")
            message_content: Content of the message (truncated for privacy)
            analysis_result: Result of job ad analysis if successful
            response_time: Time taken to process the request in seconds
            error: Error message if processing failed
            message_sid: Twilio message SID for tracking
            source: Source of the interaction ("whatsapp" or "web")
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                interaction_repo = UserInteractionRepository(session)
                
                # Get or create user
                user = await user_repo.get_or_create_user(phone_number)
                
                # Create interaction record
                interaction = await interaction_repo.create_interaction(
                    user_id=user.id,
                    message_sid=message_sid or f"web-{datetime.utcnow().timestamp()}",
                    message_type=message_type,
                    message_content=message_content
                )
                
                # Update interaction with results or error
                if analysis_result:
                    # Convert trust_score from 0-100 to 0.0-1.0 for database storage
                    db_analysis_result = JobAnalysisResult(
                        trust_score=analysis_result.trust_score,
                        classification=analysis_result.classification,
                        reasons=analysis_result.reasons,
                        confidence=analysis_result.confidence,
                        timestamp=analysis_result.timestamp
                    )
                    await interaction_repo.update_interaction_result(
                        interaction.id,
                        db_analysis_result,
                        response_time,
                        response_time  # processing_time same as response_time for now
                    )
                elif error:
                    await interaction_repo.update_interaction_error(
                        interaction.id,
                        "processing_error",
                        error,
                        response_time
                    )
                
                # Update user statistics
                await user_repo.update_user_stats(
                    user.id,
                    analysis_result is not None and error is None,
                    response_time
                )
                
                await session.commit()
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "User interaction recorded in database",
                    phone_number=sanitize_phone_number(phone_number),
                    message_type=message_type,
                    source=source,
                    success=analysis_result is not None and error is None,
                    response_time=response_time,
                    user_id=user.id
                )
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to record user interaction",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            raise
    
    async def get_user_details(self, phone_number: str) -> Optional[UserDetails]:
        """
        Get detailed information about a specific user.
        
        Args:
            phone_number: User's WhatsApp phone number
            
        Returns:
            UserDetails object if user exists, None otherwise
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                interaction_repo = UserInteractionRepository(session)
                
                db_user = await user_repo.get_by_phone_number(phone_number)
                if not db_user:
                    return None
                
                # Get recent interactions
                db_interactions = await interaction_repo.get_user_interactions(
                    db_user.id, limit=50
                )
                
                # Convert to UserDetails format
                interactions = []
                for db_interaction in db_interactions:
                    # Convert classification enum back to JobClassification
                    analysis_result = None
                    if db_interaction.classification and db_interaction.trust_score is not None:
                        classification_map = {
                            JobClassificationEnum.LEGITIMATE: JobClassification.LEGIT,
                            JobClassificationEnum.SUSPICIOUS: JobClassification.SUSPICIOUS,
                            JobClassificationEnum.SCAM: JobClassification.LIKELY_SCAM
                        }
                        
                        analysis_result = JobAnalysisResult(
                            trust_score=int(db_interaction.trust_score * 100),  # Convert back to 0-100 scale
                            classification=classification_map.get(db_interaction.classification, JobClassification.SUSPICIOUS),
                            reasons=db_interaction.classification_reasons.get("reasons", []) if db_interaction.classification_reasons else [],
                            confidence=db_interaction.confidence or 0.0,
                            timestamp=db_interaction.timestamp
                        )
                    
                    interaction = UserInteraction(
                        timestamp=db_interaction.timestamp,
                        message_type=db_interaction.message_type,
                        message_content=db_interaction.message_content,
                        analysis_result=analysis_result,
                        response_time=db_interaction.response_time or 0.0,
                        error=db_interaction.error_message,
                        message_sid=db_interaction.message_sid,
                        source="whatsapp" if not db_interaction.message_sid.startswith("web-") else "web"
                    )
                    interactions.append(interaction)
                
                user_details = UserDetails(
                    phone_number=db_user.phone_number,
                    first_interaction=db_user.created_at,
                    last_interaction=db_user.last_interaction,
                    total_requests=db_user.total_requests,
                    blocked=db_user.blocked,
                    interaction_history=interactions,
                    notes=db_user.notes
                )
                
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Retrieved user details from database",
                    phone_number=sanitize_phone_number(phone_number),
                    total_requests=user_details.total_requests,
                    blocked=user_details.blocked
                )
                
                return user_details
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to get user details",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            return None
    
    async def get_users(self, 
                       page: int = 1, 
                       limit: int = 20, 
                       search_criteria: Optional[UserSearchCriteria] = None) -> UserList:
        """
        Get a paginated list of users with optional filtering.
        
        Args:
            page: Page number (1-based)
            limit: Number of users per page
            search_criteria: Optional search and filter criteria
            
        Returns:
            UserList object with paginated results
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                interaction_repo = UserInteractionRepository(session)
                
                # Get paginated users from database
                db_users, total_count = await user_repo.get_users_paginated(
                    page=page,
                    limit=limit,
                    search_criteria=search_criteria
                )
                
                # Convert to UserDetails format
                users = []
                for db_user in db_users:
                    # Get recent interactions for each user
                    db_interactions = await interaction_repo.get_user_interactions(
                        db_user.id, limit=10  # Limit to recent interactions for performance
                    )
                    
                    # Convert interactions
                    interactions = []
                    for db_interaction in db_interactions:
                        analysis_result = None
                        if db_interaction.classification and db_interaction.trust_score is not None:
                            classification_map = {
                                JobClassificationEnum.LEGITIMATE: JobClassification.LEGIT,
                                JobClassificationEnum.SUSPICIOUS: JobClassification.SUSPICIOUS,
                                JobClassificationEnum.SCAM: JobClassification.LIKELY_SCAM
                            }
                            
                            analysis_result = JobAnalysisResult(
                                trust_score=int(db_interaction.trust_score * 100),
                                classification=classification_map.get(db_interaction.classification, JobClassification.SUSPICIOUS),
                                reasons=db_interaction.classification_reasons.get("reasons", []) if db_interaction.classification_reasons else [],
                                confidence=db_interaction.confidence or 0.0,
                                timestamp=db_interaction.timestamp
                            )
                        
                        interaction = UserInteraction(
                            timestamp=db_interaction.timestamp,
                            message_type=db_interaction.message_type,
                            message_content=db_interaction.message_content,
                            analysis_result=analysis_result,
                            response_time=db_interaction.response_time or 0.0,
                            error=db_interaction.error_message,
                            message_sid=db_interaction.message_sid,
                            source="whatsapp" if not db_interaction.message_sid.startswith("web-") else "web"
                        )
                        interactions.append(interaction)
                    
                    user_details = UserDetails(
                        phone_number=db_user.phone_number,
                        first_interaction=db_user.created_at,
                        last_interaction=db_user.last_interaction,
                        total_requests=db_user.total_requests,
                        blocked=db_user.blocked,
                        interaction_history=interactions,
                        notes=db_user.notes
                    )
                    users.append(user_details)
                
                # Calculate total pages
                total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
                
                user_list = UserList(
                    users=users,
                    total=total_count,
                    page=page,
                    pages=total_pages,
                    limit=limit
                )
                
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Retrieved user list from database",
                    total_users=total_count,
                    page=page,
                    limit=limit,
                    filtered=search_criteria is not None
                )
                
                return user_list
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to retrieve user list",
                page=page,
                limit=limit,
                error=str(e)
            )
            raise
    
    async def block_user(self, phone_number: str, reason: Optional[str] = None) -> bool:
        """
        Block a user from using the bot.
        
        Args:
            phone_number: User's WhatsApp phone number
            reason: Optional reason for blocking
            
        Returns:
            bool: True if user was successfully blocked
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                
                db_user = await user_repo.get_by_phone_number(phone_number)
                if not db_user:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Attempted to block non-existent user",
                        phone_number=sanitize_phone_number(phone_number)
                    )
                    return False
                
                # Block the user
                notes = f"Blocked: {reason}" if reason else "Blocked"
                success = await user_repo.block_user(db_user.id, notes)
                
                if success:
                    await session.commit()
                    log_with_context(
                        logger,
                        logging.INFO,
                        "User blocked in database",
                        phone_number=sanitize_phone_number(phone_number),
                        reason=reason
                    )
                
                return success
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to block user",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            return False
    
    async def unblock_user(self, phone_number: str) -> bool:
        """
        Unblock a previously blocked user.
        
        Args:
            phone_number: User's WhatsApp phone number
            
        Returns:
            bool: True if user was successfully unblocked
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                
                db_user = await user_repo.get_by_phone_number(phone_number)
                if not db_user:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Attempted to unblock non-existent user",
                        phone_number=sanitize_phone_number(phone_number)
                    )
                    return False
                
                # Unblock the user
                success = await user_repo.unblock_user(db_user.id)
                
                if success:
                    await session.commit()
                    log_with_context(
                        logger,
                        logging.INFO,
                        "User unblocked in database",
                        phone_number=sanitize_phone_number(phone_number)
                    )
                
                return success
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to unblock user",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            return False
    
    async def is_user_blocked(self, phone_number: str) -> bool:
        """
        Check if a user is currently blocked.
        
        Args:
            phone_number: User's WhatsApp phone number
            
        Returns:
            bool: True if user is blocked
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                
                db_user = await user_repo.get_by_phone_number(phone_number)
                return db_user.blocked if db_user else False
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to check if user is blocked",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            return False
    
    async def get_user_statistics(self) -> Dict[str, any]:
        """
        Get overall user statistics and insights.
        
        Returns:
            Dictionary containing user statistics
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                interaction_repo = UserInteractionRepository(session)
                
                # Get user statistics from database
                user_stats = await user_repo.get_user_statistics()
                
                # Get interaction statistics
                interaction_stats = await interaction_repo.get_interaction_statistics(days=30)
                
                # Calculate active users for different periods
                now = datetime.utcnow()
                seven_days_ago = now - timedelta(days=7)
                thirty_days_ago = now - timedelta(days=30)
                
                # Get active users count (this could be optimized with a direct query)
                from sqlalchemy import select, func, and_
                from app.database.models import WhatsAppUser
                
                # Active users in last 7 days
                result_7d = await session.execute(
                    select(func.count(WhatsAppUser.id))
                    .where(WhatsAppUser.last_interaction >= seven_days_ago)
                )
                active_users_7d = result_7d.scalar()
                
                # Active users in last 30 days
                result_30d = await session.execute(
                    select(func.count(WhatsAppUser.id))
                    .where(WhatsAppUser.last_interaction >= thirty_days_ago)
                )
                active_users_30d = result_30d.scalar()
                
                statistics = {
                    "total_users": user_stats["total_users"],
                    "blocked_users": user_stats["blocked_users"],
                    "active_users_7d": active_users_7d,
                    "active_users_30d": active_users_30d,
                    "total_interactions": interaction_stats["total_interactions"],
                    "successful_interactions": interaction_stats["successful_interactions"],
                    "success_rate": round(interaction_stats["success_rate"], 2),
                    "average_requests_per_user": user_stats["average_requests_per_user"]
                }
                
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Generated user statistics from database",
                    **statistics
                )
                
                return statistics
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate user statistics",
                error=str(e)
            )
            raise
    
    async def cleanup_old_interactions(self, days_to_keep: int = 90) -> int:
        """
        Clean up old interaction data to manage memory usage.
        
        Args:
            days_to_keep: Number of days of interaction history to keep
            
        Returns:
            int: Number of interactions removed
        """
        async with self._lock:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                total_removed = 0
                
                for user in self._users.values():
                    original_count = len(user.interaction_history)
                    user.interaction_history = [
                        interaction for interaction in user.interaction_history
                        if interaction.timestamp >= cutoff_date
                    ]
                    removed = original_count - len(user.interaction_history)
                    total_removed += removed
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "Cleaned up old interactions",
                    days_to_keep=days_to_keep,
                    interactions_removed=total_removed
                )
                
                return total_removed
                
            except Exception as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    "Failed to cleanup old interactions",
                    error=str(e)
                )
                raise
    

    
    async def get_user_interaction_history(self, 
                                         phone_number: str, 
                                         limit: int = 50) -> List[UserInteraction]:
        """
        Get interaction history for a specific user.
        
        Args:
            phone_number: User's WhatsApp phone number
            limit: Maximum number of interactions to return
            
        Returns:
            List of UserInteraction objects, most recent first
        """
        try:
            async with self.session_factory() as session:
                user_repo = WhatsAppUserRepository(session)
                interaction_repo = UserInteractionRepository(session)
                
                db_user = await user_repo.get_by_phone_number(phone_number)
                if not db_user:
                    return []
                
                db_interactions = await interaction_repo.get_user_interactions(
                    db_user.id, limit=limit
                )
                
                # Convert to UserInteraction format
                interactions = []
                for db_interaction in db_interactions:
                    analysis_result = None
                    if db_interaction.classification and db_interaction.trust_score is not None:
                        classification_map = {
                            JobClassificationEnum.LEGITIMATE: JobClassification.LEGIT,
                            JobClassificationEnum.SUSPICIOUS: JobClassification.SUSPICIOUS,
                            JobClassificationEnum.SCAM: JobClassification.LIKELY_SCAM
                        }
                        
                        analysis_result = JobAnalysisResult(
                            trust_score=int(db_interaction.trust_score * 100),
                            classification=classification_map.get(db_interaction.classification, JobClassification.SUSPICIOUS),
                            reasons=db_interaction.classification_reasons.get("reasons", []) if db_interaction.classification_reasons else [],
                            confidence=db_interaction.confidence or 0.0,
                            timestamp=db_interaction.timestamp
                        )
                    
                    interaction = UserInteraction(
                        timestamp=db_interaction.timestamp,
                        message_type=db_interaction.message_type,
                        message_content=db_interaction.message_content,
                        analysis_result=analysis_result,
                        response_time=db_interaction.response_time or 0.0,
                        error=db_interaction.error_message,
                        message_sid=db_interaction.message_sid,
                        source="whatsapp" if not db_interaction.message_sid.startswith("web-") else "web"
                    )
                    interactions.append(interaction)
                
                return interactions
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to get user interaction history",
                phone_number=sanitize_phone_number(phone_number),
                error=str(e)
            )
            return []
    
    async def search_users(self, query: str) -> List[UserDetails]:
        """
        Search users by phone number or other criteria.
        
        Args:
            query: Search query (phone number fragment)
            
        Returns:
            List of matching UserDetails objects
        """
        async with self._lock:
            matching_users = []
            query_lower = query.lower()
            
            for user in self._users.values():
                if (query_lower in user.phone_number.lower() or
                    (user.notes and query_lower in user.notes.lower())):
                    matching_users.append(user)
            
            # Sort by last interaction
            matching_users.sort(key=lambda u: u.last_interaction, reverse=True)
            
            log_with_context(
                logger,
                logging.DEBUG,
                "User search completed",
                query=query,
                results_count=len(matching_users)
            )
            
            return matching_users

    async def get_user_retention(self,
                                 cohort_period: str = "monthly",
                                 retention_periods: List[int] = [1, 7, 30]) -> Dict[str, Any]:
        
        async with self._lock:
            cohorts = defaultdict(list)
            for user in self._users.values():
                cohort_key = user.first_interaction.strftime("%Y-%m")
                cohorts[cohort_key].append(user)

            retention_data = {}
            for cohort_key, cohort_users in cohorts.items():
                cohort_start_date = datetime.strptime(cohort_key, "%Y-%m")
                retention_data[cohort_key] = {
                    "cohort_size": len(cohort_users),
                    "retention": {}
                }
                for period in retention_periods:
                    retention_end_date = cohort_start_date + timedelta(days=period)
                    retained_users = 0
                    for user in cohort_users:
                        for interaction in user.interaction_history:
                            if interaction.timestamp >= retention_end_date:
                                retained_users += 1
                                break
                    retention_rate = (retained_users / len(cohort_users)) * 100 if cohort_users else 0
                    retention_data[cohort_key]["retention"][f"{period}d"] = round(retention_rate, 2)
            
            return retention_data