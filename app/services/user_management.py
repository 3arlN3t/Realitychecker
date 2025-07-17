"""
User management service for the Reality Checker WhatsApp bot.

This module provides the UserManagementService class for tracking WhatsApp user
interactions, managing user sessions, and providing user blocking/unblocking functionality.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import threading
from collections import defaultdict
import math

from app.models.data_models import (
    UserDetails, UserInteraction, UserList, UserSearchCriteria,
    JobAnalysisResult, AppConfig
)
from app.utils.logging import get_logger, log_with_context, sanitize_phone_number


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
        self._users: Dict[str, UserDetails] = {}
        self._blocked_users: set = set()
        self._lock = threading.RLock()  # Thread-safe operations
        
        logger.info("UserManagementService initialized")
    
    async def record_interaction(self, 
                               phone_number: str,
                               message_type: str,
                               message_content: Optional[str] = None,
                               analysis_result: Optional[JobAnalysisResult] = None,
                               response_time: float = 0.0,
                               error: Optional[str] = None,
                               message_sid: Optional[str] = None) -> None:
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
        """
        with self._lock:
            try:
                # Create interaction record
                interaction = UserInteraction(
                    timestamp=datetime.utcnow(),
                    message_type=message_type,
                    message_content=message_content,
                    analysis_result=analysis_result,
                    response_time=response_time,
                    error=error,
                    message_sid=message_sid
                )
                
                # Get or create user
                user = self._get_or_create_user(phone_number)
                
                # Add interaction to user history
                user.add_interaction(interaction)
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "User interaction recorded",
                    phone_number=sanitize_phone_number(phone_number),
                    message_type=message_type,
                    success=interaction.was_successful,
                    response_time=response_time,
                    total_requests=user.total_requests
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
        with self._lock:
            user = self._users.get(phone_number)
            if user:
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Retrieved user details",
                    phone_number=sanitize_phone_number(phone_number),
                    total_requests=user.total_requests,
                    blocked=user.blocked
                )
            return user
    
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
        with self._lock:
            try:
                # Get all users
                all_users = list(self._users.values())
                
                # Apply search criteria if provided
                if search_criteria:
                    filtered_users = [
                        user for user in all_users 
                        if search_criteria.matches_user(user)
                    ]
                else:
                    filtered_users = all_users
                
                # Sort users by last interaction (most recent first)
                filtered_users.sort(key=lambda u: u.last_interaction, reverse=True)
                
                # Calculate pagination
                total_users = len(filtered_users)
                total_pages = math.ceil(total_users / limit) if total_users > 0 else 1
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                
                # Get page of users
                page_users = filtered_users[start_idx:end_idx]
                
                user_list = UserList(
                    users=page_users,
                    total=total_users,
                    page=page,
                    pages=total_pages,
                    limit=limit
                )
                
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Retrieved user list",
                    total_users=total_users,
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
        with self._lock:
            try:
                user = self._users.get(phone_number)
                if not user:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Attempted to block non-existent user",
                        phone_number=sanitize_phone_number(phone_number)
                    )
                    return False
                
                # Block the user
                user.blocked = True
                user.notes = f"Blocked: {reason}" if reason else "Blocked"
                self._blocked_users.add(phone_number)
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "User blocked",
                    phone_number=sanitize_phone_number(phone_number),
                    reason=reason
                )
                
                return True
                
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
        with self._lock:
            try:
                user = self._users.get(phone_number)
                if not user:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Attempted to unblock non-existent user",
                        phone_number=sanitize_phone_number(phone_number)
                    )
                    return False
                
                # Unblock the user
                user.blocked = False
                user.notes = "Unblocked"
                self._blocked_users.discard(phone_number)
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "User unblocked",
                    phone_number=sanitize_phone_number(phone_number)
                )
                
                return True
                
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
        with self._lock:
            return phone_number in self._blocked_users
    
    async def get_user_statistics(self) -> Dict[str, any]:
        """
        Get overall user statistics and insights.
        
        Returns:
            Dictionary containing user statistics
        """
        with self._lock:
            try:
                total_users = len(self._users)
                blocked_users = len(self._blocked_users)
                active_users_7d = 0
                active_users_30d = 0
                total_interactions = 0
                successful_interactions = 0
                
                now = datetime.utcnow()
                seven_days_ago = now - timedelta(days=7)
                thirty_days_ago = now - timedelta(days=30)
                
                # Calculate statistics
                for user in self._users.values():
                    total_interactions += user.total_requests
                    
                    # Count successful interactions
                    successful_interactions += sum(
                        1 for interaction in user.interaction_history 
                        if interaction.was_successful
                    )
                    
                    # Count active users
                    if user.last_interaction >= seven_days_ago:
                        active_users_7d += 1
                    if user.last_interaction >= thirty_days_ago:
                        active_users_30d += 1
                
                success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
                
                statistics = {
                    "total_users": total_users,
                    "blocked_users": blocked_users,
                    "active_users_7d": active_users_7d,
                    "active_users_30d": active_users_30d,
                    "total_interactions": total_interactions,
                    "successful_interactions": successful_interactions,
                    "success_rate": round(success_rate, 2),
                    "average_requests_per_user": round(total_interactions / total_users, 2) if total_users > 0 else 0
                }
                
                log_with_context(
                    logger,
                    logging.DEBUG,
                    "Generated user statistics",
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
        with self._lock:
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
    
    def _get_or_create_user(self, phone_number: str) -> UserDetails:
        """
        Get existing user or create a new one.
        
        Args:
            phone_number: User's WhatsApp phone number
            
        Returns:
            UserDetails object for the user
        """
        user = self._users.get(phone_number)
        if not user:
            now = datetime.utcnow()
            user = UserDetails(
                phone_number=phone_number,
                first_interaction=now,
                last_interaction=now,
                total_requests=0,
                blocked=phone_number in self._blocked_users
            )
            self._users[phone_number] = user
            
            log_with_context(
                logger,
                logging.INFO,
                "New user created",
                phone_number=sanitize_phone_number(phone_number)
            )
        
        return user
    
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
        with self._lock:
            user = self._users.get(phone_number)
            if not user:
                return []
            
            return user.get_recent_interactions(limit)
    
    async def search_users(self, query: str) -> List[UserDetails]:
        """
        Search users by phone number or other criteria.
        
        Args:
            query: Search query (phone number fragment)
            
        Returns:
            List of matching UserDetails objects
        """
        with self._lock:
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
        
        with self._lock:
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