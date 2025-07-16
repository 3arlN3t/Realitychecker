"""
Unit tests for the UserManagementService.

This module contains comprehensive tests for user management functionality
including interaction tracking, user blocking/unblocking, and user analytics.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.user_management import UserManagementService
from app.models.data_models import (
    AppConfig, UserDetails, UserInteraction, UserList, UserSearchCriteria,
    JobAnalysisResult, JobClassification
)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AppConfig(
        openai_api_key="test-key",
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO"
    )


@pytest.fixture
def user_service(mock_config):
    """Create a UserManagementService instance for testing."""
    return UserManagementService(mock_config)


@pytest.fixture
def sample_analysis_result():
    """Create a sample JobAnalysisResult for testing."""
    return JobAnalysisResult(
        trust_score=75,
        classification=JobClassification.LEGIT,
        reasons=["Legitimate company", "Reasonable salary", "Clear job description"],
        confidence=0.85
    )


class TestUserManagementService:
    """Test cases for UserManagementService."""
    
    @pytest.mark.asyncio
    async def test_record_interaction_new_user(self, user_service, sample_analysis_result):
        """Test recording interaction for a new user."""
        phone_number = "whatsapp:+1234567890"
        
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="text",
            message_content="Test job posting",
            analysis_result=sample_analysis_result,
            response_time=1.5,
            message_sid="MSG123"
        )
        
        # Verify user was created
        user = await user_service.get_user_details(phone_number)
        assert user is not None
        assert user.phone_number == phone_number
        assert user.total_requests == 1
        assert len(user.interaction_history) == 1
        
        # Verify interaction details
        interaction = user.interaction_history[0]
        assert interaction.message_type == "text"
        assert interaction.message_content == "Test job posting"
        assert interaction.analysis_result == sample_analysis_result
        assert interaction.response_time == 1.5
        assert interaction.message_sid == "MSG123"
        assert interaction.was_successful is True
    
    @pytest.mark.asyncio
    async def test_record_interaction_existing_user(self, user_service):
        """Test recording multiple interactions for existing user."""
        phone_number = "whatsapp:+1234567890"
        
        # First interaction
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="text",
            message_content="First message",
            response_time=1.0
        )
        
        # Second interaction
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="pdf",
            message_content="Second message",
            response_time=2.0,
            error="Processing failed"
        )
        
        # Verify user has both interactions
        user = await user_service.get_user_details(phone_number)
        assert user.total_requests == 2
        assert len(user.interaction_history) == 2
        
        # Verify interactions are ordered by timestamp
        interactions = user.get_recent_interactions()
        assert interactions[0].message_content == "Second message"
        assert interactions[1].message_content == "First message"
    
    @pytest.mark.asyncio
    async def test_record_interaction_with_error(self, user_service):
        """Test recording interaction with error."""
        phone_number = "whatsapp:+1234567890"
        
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="pdf",
            message_content="Failed PDF",
            response_time=0.5,
            error="PDF processing failed"
        )
        
        user = await user_service.get_user_details(phone_number)
        interaction = user.interaction_history[0]
        
        assert interaction.error == "PDF processing failed"
        assert interaction.was_successful is False
        assert interaction.analysis_result is None
    
    @pytest.mark.asyncio
    async def test_block_user(self, user_service):
        """Test blocking a user."""
        phone_number = "whatsapp:+1234567890"
        
        # Create user first
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="text",
            message_content="Test message"
        )
        
        # Block user
        result = await user_service.block_user(phone_number, "Spam messages")
        assert result is True
        
        # Verify user is blocked
        is_blocked = await user_service.is_user_blocked(phone_number)
        assert is_blocked is True
        
        user = await user_service.get_user_details(phone_number)
        assert user.blocked is True
        assert "Blocked: Spam messages" in user.notes
    
    @pytest.mark.asyncio
    async def test_block_nonexistent_user(self, user_service):
        """Test blocking a user that doesn't exist."""
        phone_number = "whatsapp:+9999999999"
        
        result = await user_service.block_user(phone_number, "Test reason")
        assert result is False
        
        is_blocked = await user_service.is_user_blocked(phone_number)
        assert is_blocked is False
    
    @pytest.mark.asyncio
    async def test_unblock_user(self, user_service):
        """Test unblocking a previously blocked user."""
        phone_number = "whatsapp:+1234567890"
        
        # Create and block user
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="text",
            message_content="Test message"
        )
        await user_service.block_user(phone_number, "Test block")
        
        # Unblock user
        result = await user_service.unblock_user(phone_number)
        assert result is True
        
        # Verify user is unblocked
        is_blocked = await user_service.is_user_blocked(phone_number)
        assert is_blocked is False
        
        user = await user_service.get_user_details(phone_number)
        assert user.blocked is False
        assert user.notes == "Unblocked"
    
    @pytest.mark.asyncio
    async def test_get_users_pagination(self, user_service):
        """Test getting users with pagination."""
        # Create multiple users
        for i in range(25):
            phone_number = f"whatsapp:+123456789{i:02d}"
            await user_service.record_interaction(
                phone_number=phone_number,
                message_type="text",
                message_content=f"Message from user {i}"
            )
        
        # Test first page
        user_list = await user_service.get_users(page=1, limit=10)
        assert len(user_list.users) == 10
        assert user_list.total == 25
        assert user_list.page == 1
        assert user_list.pages == 3
        assert user_list.limit == 10
        
        # Test second page
        user_list = await user_service.get_users(page=2, limit=10)
        assert len(user_list.users) == 10
        assert user_list.page == 2
        
        # Test last page
        user_list = await user_service.get_users(page=3, limit=10)
        assert len(user_list.users) == 5
        assert user_list.page == 3
    
    @pytest.mark.asyncio
    async def test_get_users_with_search_criteria(self, user_service):
        """Test getting users with search criteria."""
        # Create users with different characteristics
        phone1 = "whatsapp:+1111111111"
        phone2 = "whatsapp:+2222222222"
        phone3 = "whatsapp:+3333333333"
        
        # User 1: Multiple requests, no errors
        for _ in range(5):
            await user_service.record_interaction(
                phone_number=phone1,
                message_type="text",
                message_content="Good message"
            )
        
        # User 2: Few requests, with errors
        await user_service.record_interaction(
            phone_number=phone2,
            message_type="text",
            message_content="Bad message",
            error="Processing failed"
        )
        
        # User 3: Blocked user
        await user_service.record_interaction(
            phone_number=phone3,
            message_type="text",
            message_content="Spam message"
        )
        await user_service.block_user(phone3, "Spam")
        
        # Test filtering by minimum requests
        criteria = UserSearchCriteria(min_requests=3)
        user_list = await user_service.get_users(search_criteria=criteria)
        assert len(user_list.users) == 1
        assert user_list.users[0].phone_number == phone1
        
        # Test filtering by blocked status
        criteria = UserSearchCriteria(blocked=True)
        user_list = await user_service.get_users(search_criteria=criteria)
        assert len(user_list.users) == 1
        assert user_list.users[0].phone_number == phone3
        
        # Test filtering by errors
        criteria = UserSearchCriteria(has_errors=True)
        user_list = await user_service.get_users(search_criteria=criteria)
        assert len(user_list.users) == 1
        assert user_list.users[0].phone_number == phone2
    
    @pytest.mark.asyncio
    async def test_get_user_statistics(self, user_service, sample_analysis_result):
        """Test getting user statistics."""
        # Create users with various interactions
        phone1 = "whatsapp:+1111111111"
        phone2 = "whatsapp:+2222222222"
        phone3 = "whatsapp:+3333333333"
        
        # Recent active user
        await user_service.record_interaction(
            phone_number=phone1,
            message_type="text",
            message_content="Recent message",
            analysis_result=sample_analysis_result
        )
        
        # Old inactive user
        await user_service.record_interaction(
            phone_number=phone2,
            message_type="text",
            message_content="Old message"
        )
        # Manually set old timestamp
        user2 = await user_service.get_user_details(phone2)
        old_date = datetime.utcnow() - timedelta(days=45)
        user2.last_interaction = old_date
        user2.interaction_history[0].timestamp = old_date
        
        # Blocked user
        await user_service.record_interaction(
            phone_number=phone3,
            message_type="text",
            message_content="Blocked message",
            error="Failed"
        )
        await user_service.block_user(phone3, "Spam")
        
        # Get statistics
        stats = await user_service.get_user_statistics()
        
        assert stats["total_users"] == 3
        assert stats["blocked_users"] == 1
        assert stats["active_users_7d"] == 2  # phone1 and phone3 are recent
        assert stats["active_users_30d"] == 2
        assert stats["total_interactions"] == 3
        assert stats["successful_interactions"] == 1  # Only phone1 was successful
        assert stats["success_rate"] == 33.33  # 1/3 * 100
    
    @pytest.mark.asyncio
    async def test_cleanup_old_interactions(self, user_service):
        """Test cleaning up old interaction data."""
        phone_number = "whatsapp:+1234567890"
        
        # Create interactions with different timestamps
        now = datetime.utcnow()
        old_date = now - timedelta(days=100)
        recent_date = now - timedelta(days=30)
        
        # Create user and manually add interactions with different dates
        await user_service.record_interaction(
            phone_number=phone_number,
            message_type="text",
            message_content="Recent message"
        )
        
        user = await user_service.get_user_details(phone_number)
        
        # Add old interaction manually
        old_interaction = UserInteraction(
            timestamp=old_date,
            message_type="text",
            message_content="Old message"
        )
        user.interaction_history.append(old_interaction)
        
        # Add recent interaction manually
        recent_interaction = UserInteraction(
            timestamp=recent_date,
            message_type="text",
            message_content="Recent old message"
        )
        user.interaction_history.append(recent_interaction)
        
        # Should have 3 interactions total
        assert len(user.interaction_history) == 3
        
        # Cleanup interactions older than 90 days
        removed_count = await user_service.cleanup_old_interactions(days_to_keep=90)
        assert removed_count == 1
        
        # Should have 2 interactions remaining
        user = await user_service.get_user_details(phone_number)
        assert len(user.interaction_history) == 2
    
    @pytest.mark.asyncio
    async def test_search_users(self, user_service):
        """Test searching users by phone number."""
        # Create users
        phone1 = "whatsapp:+1111111111"
        phone2 = "whatsapp:+2222222222"
        phone3 = "whatsapp:+1111333333"
        
        await user_service.record_interaction(phone_number=phone1, message_type="text", message_content="Test")
        await user_service.record_interaction(phone_number=phone2, message_type="text", message_content="Test")
        await user_service.record_interaction(phone_number=phone3, message_type="text", message_content="Test")
        
        # Search for users with "1111" in phone number
        results = await user_service.search_users("1111")
        assert len(results) == 2
        phone_numbers = [user.phone_number for user in results]
        assert phone1 in phone_numbers
        assert phone3 in phone_numbers
        assert phone2 not in phone_numbers
        
        # Search for specific user
        results = await user_service.search_users("2222")
        assert len(results) == 1
        assert results[0].phone_number == phone2
    
    @pytest.mark.asyncio
    async def test_get_user_interaction_history(self, user_service, sample_analysis_result):
        """Test getting user interaction history."""
        phone_number = "whatsapp:+1234567890"
        
        # Create multiple interactions
        for i in range(15):
            await user_service.record_interaction(
                phone_number=phone_number,
                message_type="text",
                message_content=f"Message {i}",
                analysis_result=sample_analysis_result if i % 2 == 0 else None,
                error=None if i % 2 == 0 else f"Error {i}"
            )
        
        # Get limited history
        history = await user_service.get_user_interaction_history(phone_number, limit=10)
        assert len(history) == 10
        
        # Verify most recent first
        assert "Message 14" in history[0].message_content
        assert "Message 13" in history[1].message_content
        
        # Get all history
        history = await user_service.get_user_interaction_history(phone_number, limit=50)
        assert len(history) == 15
    
    @pytest.mark.asyncio
    async def test_thread_safety(self, user_service):
        """Test thread safety of user management operations."""
        phone_number = "whatsapp:+1234567890"
        
        # Create multiple concurrent interactions
        async def create_interaction(i):
            await user_service.record_interaction(
                phone_number=phone_number,
                message_type="text",
                message_content=f"Concurrent message {i}",
                response_time=0.1
            )
        
        # Run 10 concurrent interactions
        tasks = [create_interaction(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Verify all interactions were recorded
        user = await user_service.get_user_details(phone_number)
        assert user.total_requests == 10
        assert len(user.interaction_history) == 10


class TestUserDataModels:
    """Test cases for user-related data models."""
    
    def test_user_interaction_validation(self):
        """Test UserInteraction validation."""
        # Valid interaction
        interaction = UserInteraction(
            timestamp=datetime.utcnow(),
            message_type="text",
            response_time=1.5
        )
        assert interaction.message_type == "text"
        assert interaction.response_time == 1.5
        
        # Invalid message type
        with pytest.raises(ValueError, match="Message type must be"):
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="invalid",
                response_time=1.0
            )
        
        # Negative response time
        with pytest.raises(ValueError, match="Response time cannot be negative"):
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                response_time=-1.0
            )
    
    def test_user_interaction_content_truncation(self):
        """Test message content truncation for privacy."""
        long_content = "x" * 300
        interaction = UserInteraction(
            timestamp=datetime.utcnow(),
            message_type="text",
            message_content=long_content,
            response_time=1.0
        )
        
        # Content should be truncated to 200 chars + "..."
        assert len(interaction.message_content) == 203
        assert interaction.message_content.endswith("...")
    
    def test_user_details_validation(self):
        """Test UserDetails validation."""
        now = datetime.utcnow()
        
        # Valid user details
        user = UserDetails(
            phone_number="whatsapp:+1234567890",
            first_interaction=now,
            last_interaction=now,
            total_requests=5
        )
        assert user.phone_number == "whatsapp:+1234567890"
        assert user.total_requests == 5
        
        # Invalid phone number format
        with pytest.raises(ValueError, match="Phone number must be in WhatsApp format"):
            UserDetails(
                phone_number="+1234567890",  # Missing whatsapp: prefix
                first_interaction=now,
                last_interaction=now
            )
        
        # First interaction after last interaction
        with pytest.raises(ValueError, match="First interaction cannot be after last interaction"):
            UserDetails(
                phone_number="whatsapp:+1234567890",
                first_interaction=now,
                last_interaction=now - timedelta(hours=1)
            )
    
    def test_user_details_properties(self, sample_analysis_result):
        """Test UserDetails calculated properties."""
        now = datetime.utcnow()
        first_interaction = now - timedelta(days=10)
        last_interaction = now - timedelta(days=2)
        
        user = UserDetails(
            phone_number="whatsapp:+1234567890",
            first_interaction=first_interaction,
            last_interaction=last_interaction,
            total_requests=3
        )
        
        # Add interactions
        successful_interaction = UserInteraction(
            timestamp=now - timedelta(days=5),
            message_type="text",
            analysis_result=sample_analysis_result,
            response_time=1.0
        )
        
        failed_interaction = UserInteraction(
            timestamp=now - timedelta(days=3),
            message_type="text",
            error="Processing failed",
            response_time=0.5
        )
        
        user.interaction_history = [successful_interaction, failed_interaction]
        
        # Test calculated properties
        assert user.days_since_first_interaction == 10
        assert user.days_since_last_interaction == 2
        assert user.success_rate == 0.5  # 1 successful out of 2
        assert user.average_response_time == 1.0  # Only successful interaction counted
    
    def test_user_search_criteria_matching(self, sample_analysis_result):
        """Test UserSearchCriteria matching logic."""
        now = datetime.utcnow()
        
        # Create test user
        user = UserDetails(
            phone_number="whatsapp:+1234567890",
            first_interaction=now - timedelta(days=5),
            last_interaction=now - timedelta(days=1),
            total_requests=3,
            blocked=False
        )
        
        # Add interaction with error
        error_interaction = UserInteraction(
            timestamp=now - timedelta(days=2),
            message_type="text",
            error="Processing failed"
        )
        user.interaction_history = [error_interaction]
        
        # Test phone number matching
        criteria = UserSearchCriteria(phone_number="1234")
        assert criteria.matches_user(user) is True
        
        criteria = UserSearchCriteria(phone_number="9999")
        assert criteria.matches_user(user) is False
        
        # Test blocked status matching
        criteria = UserSearchCriteria(blocked=False)
        assert criteria.matches_user(user) is True
        
        criteria = UserSearchCriteria(blocked=True)
        assert criteria.matches_user(user) is False
        
        # Test request count matching
        criteria = UserSearchCriteria(min_requests=2, max_requests=5)
        assert criteria.matches_user(user) is True
        
        criteria = UserSearchCriteria(min_requests=5)
        assert criteria.matches_user(user) is False
        
        # Test error matching
        criteria = UserSearchCriteria(has_errors=True)
        assert criteria.matches_user(user) is True
        
        criteria = UserSearchCriteria(has_errors=False)
        assert criteria.matches_user(user) is False
    
    def test_user_list_validation(self):
        """Test UserList validation."""
        users = []
        
        # Valid user list
        user_list = UserList(
            users=users,
            total=0,
            page=1,
            pages=1,
            limit=20
        )
        assert user_list.total == 0
        assert user_list.page == 1
        
        # Invalid page number
        with pytest.raises(ValueError, match="Page number must be at least 1"):
            UserList(
                users=users,
                total=0,
                page=0,
                pages=1,
                limit=20
            )
        
        # Invalid limit
        with pytest.raises(ValueError, match="Limit must be at least 1"):
            UserList(
                users=users,
                total=0,
                page=1,
                pages=1,
                limit=0
            )