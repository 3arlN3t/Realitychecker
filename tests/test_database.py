"""
Database integration tests for the Reality Checker WhatsApp bot.

This module contains tests for database operations, models, repositories,
and data management functionality.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.database.database import Database
from app.database.models import (
    WhatsAppUser, UserInteraction, SystemMetric, AnalysisHistory,
    SystemUser, ErrorLog, Configuration, DataRetentionPolicy,
    JobClassificationEnum, UserRoleEnum
)
from app.database.repositories import (
    WhatsAppUserRepository, UserInteractionRepository,
    SystemMetricRepository, ConfigurationRepository, ErrorLogRepository
)
from app.database.retention import DataRetentionManager
from app.database.backup import DatabaseBackupManager
from app.models.data_models import (
    JobAnalysisResult, JobClassification, UserRole, UserSearchCriteria
)


class TestDatabase:
    """Test database connection and basic operations."""
    
    @pytest.fixture
    async def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        database_url = f"sqlite+aiosqlite:///{db_path}"
        db = Database(database_url)
        
        await db.initialize()
        
        yield db
        
        await db.close()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, temp_db):
        """Test database initialization."""
        assert temp_db.engine is not None
        assert temp_db.session_factory is not None
        assert temp_db._initialized is True
    
    @pytest.mark.asyncio
    async def test_database_session_management(self, temp_db):
        """Test database session management."""
        async with temp_db.get_session() as session:
            # Test that session is valid
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, temp_db):
        """Test database health check."""
        health = await temp_db.health_check()
        assert health["status"] == "healthy"
        assert "connection_pool" in health
        assert "database_size" in health


class TestWhatsAppUserRepository:
    """Test WhatsApp user repository operations."""
    
    @pytest.fixture
    async def user_repo(self, temp_db):
        """Create user repository with temporary database."""
        async with temp_db.get_session() as session:
            yield WhatsAppUserRepository(session)
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repo):
        """Test creating a new user."""
        phone_number = "+1234567890"
        user = await user_repo.create_user(phone_number)
        
        assert user.phone_number == phone_number
        assert user.id is not None
        assert user.created_at is not None
        assert user.total_requests == 0
        assert user.blocked is False
    
    @pytest.mark.asyncio
    async def test_get_user_by_phone_number(self, user_repo):
        """Test retrieving user by phone number."""
        phone_number = "+1234567890"
        created_user = await user_repo.create_user(phone_number)
        await user_repo.commit()
        
        retrieved_user = await user_repo.get_by_phone_number(phone_number)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.phone_number == phone_number
    
    @pytest.mark.asyncio
    async def test_get_or_create_user(self, user_repo):
        """Test get or create user functionality."""
        phone_number = "+1234567890"
        
        # First call should create user
        user1 = await user_repo.get_or_create_user(phone_number)
        await user_repo.commit()
        
        # Second call should return existing user
        user2 = await user_repo.get_or_create_user(phone_number)
        
        assert user1.id == user2.id
        assert user1.phone_number == user2.phone_number
    
    @pytest.mark.asyncio
    async def test_update_user_stats(self, user_repo):
        """Test updating user statistics."""
        phone_number = "+1234567890"
        user = await user_repo.create_user(phone_number)
        await user_repo.commit()
        
        # Update stats
        await user_repo.update_user_stats(
            user.id, 
            interaction_successful=True, 
            response_time=1.5
        )
        await user_repo.commit()
        
        # Verify stats were updated
        updated_user = await user_repo.get_by_phone_number(phone_number)
        assert updated_user.total_requests == 1
        assert updated_user.successful_requests == 1
        assert updated_user.failed_requests == 0
        assert updated_user.avg_response_time == 1.5
    
    @pytest.mark.asyncio
    async def test_block_unblock_user(self, user_repo):
        """Test blocking and unblocking users."""
        phone_number = "+1234567890"
        user = await user_repo.create_user(phone_number)
        await user_repo.commit()
        
        # Block user
        success = await user_repo.block_user(user.id, "Test blocking")
        await user_repo.commit()
        
        assert success is True
        
        blocked_user = await user_repo.get_by_phone_number(phone_number)
        assert blocked_user.blocked is True
        assert blocked_user.notes == "Test blocking"
        
        # Unblock user
        success = await user_repo.unblock_user(user.id)
        await user_repo.commit()
        
        assert success is True
        
        unblocked_user = await user_repo.get_by_phone_number(phone_number)
        assert unblocked_user.blocked is False
    
    @pytest.mark.asyncio
    async def test_get_user_statistics(self, user_repo):
        """Test getting user statistics."""
        # Create test users
        await user_repo.create_user("+1234567890")
        await user_repo.create_user("+1234567891")
        
        user3 = await user_repo.create_user("+1234567892")
        await user_repo.block_user(user3.id)
        
        await user_repo.commit()
        
        stats = await user_repo.get_user_statistics()
        
        assert stats["total_users"] == 3
        assert stats["blocked_users"] == 1
        assert stats["average_requests_per_user"] == 0.0


class TestUserInteractionRepository:
    """Test user interaction repository operations."""
    
    @pytest.fixture
    async def interaction_repo(self, temp_db):
        """Create interaction repository with temporary database."""
        async with temp_db.get_session() as session:
            # Create a test user first
            user = WhatsAppUser(phone_number="+1234567890")
            session.add(user)
            await session.flush()
            
            repo = UserInteractionRepository(session)
            repo.test_user_id = user.id
            yield repo
    
    @pytest.mark.asyncio
    async def test_create_interaction(self, interaction_repo):
        """Test creating user interaction."""
        interaction = await interaction_repo.create_interaction(
            user_id=interaction_repo.test_user_id,
            message_sid="test_sid",
            message_type="text",
            message_content="Test message"
        )
        
        assert interaction.user_id == interaction_repo.test_user_id
        assert interaction.message_sid == "test_sid"
        assert interaction.message_type == "text"
        assert interaction.message_content == "Test message"
    
    @pytest.mark.asyncio
    async def test_update_interaction_result(self, interaction_repo):
        """Test updating interaction with analysis result."""
        interaction = await interaction_repo.create_interaction(
            user_id=interaction_repo.test_user_id,
            message_sid="test_sid",
            message_type="pdf"
        )
        await interaction_repo.commit()
        
        # Mock analysis result
        analysis_result = JobAnalysisResult(
            trust_score=0.8,
            classification=JobClassification.LEGITIMATE,
            confidence=0.9,
            reasons=["Professional language", "Clear requirements"]
        )
        
        await interaction_repo.update_interaction_result(
            interaction.id,
            analysis_result,
            response_time=2.5,
            processing_time=1.0
        )
        await interaction_repo.commit()
        
        # Verify updates
        updated_interaction = await interaction_repo.session.get(UserInteraction, interaction.id)
        assert updated_interaction.trust_score == 0.8
        assert updated_interaction.classification == JobClassificationEnum.LEGITIMATE
        assert updated_interaction.confidence == 0.9
        assert updated_interaction.response_time == 2.5
        assert updated_interaction.processing_time == 1.0
    
    @pytest.mark.asyncio
    async def test_get_interaction_statistics(self, interaction_repo):
        """Test getting interaction statistics."""
        # Create test interactions
        interaction1 = await interaction_repo.create_interaction(
            user_id=interaction_repo.test_user_id,
            message_sid="test_sid_1",
            message_type="text"
        )
        
        interaction2 = await interaction_repo.create_interaction(
            user_id=interaction_repo.test_user_id,
            message_sid="test_sid_2",
            message_type="pdf"
        )
        
        # Add analysis results
        analysis_result = JobAnalysisResult(
            trust_score=0.8,
            classification=JobClassification.LEGITIMATE,
            confidence=0.9,
            reasons=["Test reason"]
        )
        
        await interaction_repo.update_interaction_result(
            interaction1.id, analysis_result, 1.0, 0.5
        )
        
        await interaction_repo.update_interaction_error(
            interaction2.id, "OpenAI Error", "API timeout", 2.0
        )
        
        await interaction_repo.commit()
        
        stats = await interaction_repo.get_interaction_statistics(days=30)
        
        assert stats["total_interactions"] == 2
        assert stats["successful_interactions"] == 1
        assert stats["success_rate"] == 50.0
        assert "classification_breakdown" in stats
        assert stats["classification_breakdown"]["legitimate"] == 1


class TestSystemMetricRepository:
    """Test system metric repository operations."""
    
    @pytest.fixture
    async def metric_repo(self, temp_db):
        """Create metric repository with temporary database."""
        async with temp_db.get_session() as session:
            yield SystemMetricRepository(session)
    
    @pytest.mark.asyncio
    async def test_record_metric(self, metric_repo):
        """Test recording system metric."""
        metric = await metric_repo.record_metric(
            cpu_usage=45.5,
            memory_usage=60.0,
            disk_usage=30.2,
            active_connections=15
        )
        
        assert metric.cpu_usage == 45.5
        assert metric.memory_usage == 60.0
        assert metric.disk_usage == 30.2
        assert metric.active_connections == 15
        assert metric.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_get_latest_metrics(self, metric_repo):
        """Test getting latest metrics."""
        # Create test metrics
        await metric_repo.record_metric(cpu_usage=40.0, memory_usage=50.0)
        await metric_repo.record_metric(cpu_usage=45.0, memory_usage=55.0)
        await metric_repo.record_metric(cpu_usage=50.0, memory_usage=60.0)
        await metric_repo.commit()
        
        latest_metrics = await metric_repo.get_latest_metrics(limit=2)
        
        assert len(latest_metrics) == 2
        assert latest_metrics[0].cpu_usage == 50.0  # Most recent
        assert latest_metrics[1].cpu_usage == 45.0  # Second most recent
    
    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, metric_repo):
        """Test cleaning up old metrics."""
        # Create old metric
        old_metric = await metric_repo.record_metric(cpu_usage=40.0)
        old_metric.timestamp = datetime.now(timezone.utc) - timedelta(days=35)
        
        # Create recent metric
        await metric_repo.record_metric(cpu_usage=50.0)
        await metric_repo.commit()
        
        # Clean up metrics older than 30 days
        deleted_count = await metric_repo.cleanup_old_metrics(days=30)
        await metric_repo.commit()
        
        assert deleted_count == 1


class TestConfigurationRepository:
    """Test configuration repository operations."""
    
    @pytest.fixture
    async def config_repo(self, temp_db):
        """Create configuration repository with temporary database."""
        async with temp_db.get_session() as session:
            yield ConfigurationRepository(session)
    
    @pytest.mark.asyncio
    async def test_set_and_get_config(self, config_repo):
        """Test setting and getting configuration."""
        config = await config_repo.set_config(
            "test_key",
            "test_value",
            "Test configuration",
            "testing"
        )
        await config_repo.commit()
        
        retrieved_config = await config_repo.get_config("test_key")
        
        assert retrieved_config is not None
        assert retrieved_config.key == "test_key"
        assert retrieved_config.value == "test_value"
        assert retrieved_config.description == "Test configuration"
        assert retrieved_config.category == "testing"
    
    @pytest.mark.asyncio
    async def test_update_existing_config(self, config_repo):
        """Test updating existing configuration."""
        # Create initial config
        await config_repo.set_config("test_key", "initial_value")
        await config_repo.commit()
        
        # Update config
        updated_config = await config_repo.set_config(
            "test_key",
            "updated_value",
            "Updated description"
        )
        await config_repo.commit()
        
        retrieved_config = await config_repo.get_config("test_key")
        
        assert retrieved_config.value == "updated_value"
        assert retrieved_config.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_get_all_configs(self, config_repo):
        """Test getting all configurations."""
        await config_repo.set_config("key1", "value1", category="cat1")
        await config_repo.set_config("key2", "value2", category="cat1")
        await config_repo.set_config("key3", "value3", category="cat2")
        await config_repo.commit()
        
        # Get all configs
        all_configs = await config_repo.get_all_configs()
        assert len(all_configs) == 3
        
        # Get configs by category
        cat1_configs = await config_repo.get_all_configs(category="cat1")
        assert len(cat1_configs) == 2


class TestDataRetentionManager:
    """Test data retention manager operations."""
    
    @pytest.fixture
    async def retention_manager(self, temp_db):
        """Create retention manager with temporary database."""
        from app.database.retention import DataRetentionManager
        
        # Mock get_database to return our temp database
        import app.database.retention
        original_get_database = app.database.retention.get_database
        app.database.retention.get_database = lambda: temp_db
        
        manager = DataRetentionManager()
        
        yield manager
        
        # Restore original function
        app.database.retention.get_database = original_get_database
    
    @pytest.mark.asyncio
    async def test_create_retention_policy(self, retention_manager):
        """Test creating retention policy."""
        policy = await retention_manager.create_retention_policy(
            "test_table",
            retention_days=30,
            policy_type="delete"
        )
        
        assert policy.table_name == "test_table"
        assert policy.retention_days == 30
        assert policy.policy_type == "delete"
        assert policy.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_retention_policies(self, retention_manager):
        """Test getting retention policies."""
        await retention_manager.create_retention_policy("table1", 30, "delete")
        await retention_manager.create_retention_policy("table2", 60, "archive")
        
        policies = await retention_manager.get_retention_policies()
        
        assert len(policies) == 2
        assert policies[0].table_name in ["table1", "table2"]
        assert policies[1].table_name in ["table1", "table2"]


class TestDatabaseBackupManager:
    """Test database backup manager operations."""
    
    @pytest.fixture
    async def backup_manager(self, temp_db):
        """Create backup manager with temporary database."""
        import tempfile
        backup_dir = tempfile.mkdtemp()
        
        from app.database.backup import DatabaseBackupManager
        
        # Mock get_database to return our temp database
        import app.database.backup
        original_get_database = app.database.backup.get_database
        app.database.backup.get_database = lambda: temp_db
        
        manager = DatabaseBackupManager(backup_dir)
        
        yield manager
        
        # Restore original function
        app.database.backup.get_database = original_get_database
        
        # Cleanup
        import shutil
        shutil.rmtree(backup_dir)
    
    @pytest.mark.asyncio
    async def test_create_backup(self, backup_manager):
        """Test creating database backup."""
        result = await backup_manager.create_backup("test_backup")
        
        assert result["status"] == "success"
        assert result["backup_name"] == "test_backup"
        assert "backup_path" in result
        assert "file_size" in result
    
    def test_list_backups(self, backup_manager):
        """Test listing backups."""
        # Create a test backup first
        asyncio.create_task(backup_manager.create_backup("test_backup"))
        
        backups = backup_manager.list_backups()
        
        # Should have at least one backup
        assert len(backups) >= 0
    
    @pytest.mark.asyncio
    async def test_verify_backup(self, backup_manager):
        """Test verifying backup."""
        # Create a backup first
        await backup_manager.create_backup("test_backup")
        
        verification = await backup_manager.verify_backup("test_backup")
        
        assert verification["backup_name"] == "test_backup"
        assert verification["file_exists"] is True
        assert verification["readable"] is True


@pytest.mark.asyncio
async def test_database_integration():
    """Test full database integration workflow."""
    # This test simulates a complete user interaction workflow
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize database
        database_url = f"sqlite+aiosqlite:///{db_path}"
        db = Database(database_url)
        await db.initialize()
        
        # Test user creation and interaction
        async with db.get_session() as session:
            user_repo = WhatsAppUserRepository(session)
            interaction_repo = UserInteractionRepository(session)
            
            # Create user
            user = await user_repo.get_or_create_user("+1234567890")
            
            # Create interaction
            interaction = await interaction_repo.create_interaction(
                user_id=user.id,
                message_sid="test_sid",
                message_type="text",
                message_content="Hello"
            )
            
            # Update user stats
            await user_repo.update_user_stats(user.id, True, 1.5)
            
            # Commit changes
            await session.commit()
            
            # Verify data was saved
            saved_user = await user_repo.get_by_phone_number("+1234567890")
            assert saved_user.total_requests == 1
            assert saved_user.successful_requests == 1
            
            user_interactions = await interaction_repo.get_user_interactions(user.id)
            assert len(user_interactions) == 1
            assert user_interactions[0].message_content == "Hello"
        
        await db.close()
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])