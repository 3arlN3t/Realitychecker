"""
Database migration utilities for the Reality Checker WhatsApp bot.

This module provides utilities for running database migrations
using Alembic.
"""

import os
import asyncio
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from app.utils.logging import get_logger
from .database import get_database

logger = get_logger(__name__)


def get_alembic_config() -> Config:
    """
    Get Alembic configuration.
    
    Returns:
        Config: Alembic configuration object
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    alembic_ini = project_root / "alembic.ini"
    
    if not alembic_ini.exists():
        raise FileNotFoundError(f"Alembic configuration file not found: {alembic_ini}")
    
    config = Config(str(alembic_ini))
    
    # Update the database URL in the config
    from .database import Database
    db = Database()
    config.set_main_option("sqlalchemy.url", db.database_url)
    
    return config


def run_migrations():
    """
    Run database migrations using Alembic.
    
    This function should be called during application startup to ensure
    the database schema is up to date.
    """
    try:
        config = get_alembic_config()
        command.upgrade(config, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}")
        raise


def create_migration(message: str, autogenerate: bool = True):
    """
    Create a new migration file.
    
    Args:
        message: Migration message/description
        autogenerate: Whether to auto-generate migration from model changes
    """
    try:
        config = get_alembic_config()
        command.revision(config, message=message, autogenerate=autogenerate)
        logger.info(f"Created migration: {message}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise


def get_migration_history():
    """
    Get migration history.
    
    Returns:
        List of migration history entries
    """
    try:
        config = get_alembic_config()
        return command.history(config)
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        raise


def get_current_revision():
    """
    Get current database revision.
    
    Returns:
        Current revision identifier
    """
    try:
        config = get_alembic_config()
        return command.current(config)
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        raise


async def check_database_version():
    """
    Check if database schema is up to date.
    
    Returns:
        dict: Database version information
    """
    try:
        db = get_database()
        async with db.get_session() as session:
            # Check if alembic_version table exists
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            )
            alembic_table_exists = result.scalar() is not None
            
            if not alembic_table_exists:
                return {
                    "status": "not_initialized",
                    "message": "Database not initialized with Alembic",
                    "current_revision": None,
                    "needs_migration": True
                }
            
            # Get current revision from database
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            current_revision = result.scalar()
            
            return {
                "status": "initialized",
                "message": "Database initialized with Alembic",
                "current_revision": current_revision,
                "needs_migration": False  # In production, you'd check against expected revision
            }
    except Exception as e:
        logger.error(f"Failed to check database version: {e}")
        return {
            "status": "error",
            "message": f"Error checking database version: {e}",
            "current_revision": None,
            "needs_migration": True
        }


async def initialize_database():
    """
    Initialize database with initial schema and data.
    
    This function creates the database schema and inserts initial data
    if the database is empty.
    """
    try:
        db = get_database()
        await db.initialize()
        
        # Check if we need to run migrations
        version_info = await check_database_version()
        
        if version_info["needs_migration"]:
            logger.info("Running database migrations...")
            run_migrations()
            
            # Insert initial data
            await insert_initial_data()
        
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def insert_initial_data():
    """
    Insert initial data into the database.
    
    This function inserts default configurations, users, and other
    initial data required for the application to function.
    """
    try:
        db = get_database()
        async with db.get_session() as session:
            # Import models
            from .models import SystemUser, Configuration, DataRetentionPolicy
            from ..models.data_models import UserRole
            import bcrypt
            
            # Check if admin user exists
            admin_exists = await session.get(SystemUser, 1)
            if not admin_exists:
                # Create default admin user
                password_hash = bcrypt.hashpw(
                    "admin123".encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                admin_user = SystemUser(
                    username="admin",
                    password_hash=password_hash,
                    role=UserRole.ADMIN
                )
                session.add(admin_user)
                logger.info("Created default admin user")
            
            # Insert default configurations
            default_configs = [
                {
                    "key": "max_pdf_size_mb",
                    "value": "10",
                    "description": "Maximum PDF file size in MB",
                    "category": "processing"
                },
                {
                    "key": "rate_limit_per_minute",
                    "value": "10",
                    "description": "Rate limit per minute per user",
                    "category": "rate_limiting"
                },
                {
                    "key": "rate_limit_per_hour",
                    "value": "100",
                    "description": "Rate limit per hour per user",
                    "category": "rate_limiting"
                },
                {
                    "key": "openai_model",
                    "value": "gpt-4",
                    "description": "OpenAI model to use for analysis",
                    "category": "ai"
                },
                {
                    "key": "log_level",
                    "value": "INFO",
                    "description": "Application log level",
                    "category": "logging"
                },
                {
                    "key": "data_retention_days",
                    "value": "90",
                    "description": "Default data retention period in days",
                    "category": "data_management"
                }
            ]
            
            for config_data in default_configs:
                existing_config = await session.execute(
                    text("SELECT id FROM configurations WHERE key = :key"),
                    {"key": config_data["key"]}
                )
                if not existing_config.scalar():
                    config = Configuration(**config_data)
                    session.add(config)
            
            # Insert default data retention policies
            retention_policies = [
                {
                    "table_name": "user_interactions",
                    "retention_days": 365,
                    "policy_type": "archive"
                },
                {
                    "table_name": "system_metrics",
                    "retention_days": 30,
                    "policy_type": "delete"
                },
                {
                    "table_name": "error_logs",
                    "retention_days": 90,
                    "policy_type": "delete"
                },
                {
                    "table_name": "analysis_history",
                    "retention_days": 730,
                    "policy_type": "archive"
                }
            ]
            
            for policy_data in retention_policies:
                existing_policy = await session.execute(
                    text("SELECT id FROM data_retention_policies WHERE table_name = :table_name"),
                    {"table_name": policy_data["table_name"]}
                )
                if not existing_policy.scalar():
                    policy = DataRetentionPolicy(**policy_data)
                    session.add(policy)
            
            await session.commit()
            logger.info("Initial data inserted successfully")
            
    except Exception as e:
        logger.error(f"Failed to insert initial data: {e}")
        raise


async def create_backup_table(table_name: str):
    """
    Create a backup table for data archival.
    
    Args:
        table_name: Name of the table to create backup for
    """
    try:
        db = get_database()
        async with db.get_session() as session:
            backup_table_name = f"{table_name}_archive"
            
            # Create backup table with same structure
            await session.execute(
                text(f"CREATE TABLE IF NOT EXISTS {backup_table_name} AS SELECT * FROM {table_name} WHERE 1=0")
            )
            
            # Add archived_at column
            await session.execute(
                text(f"ALTER TABLE {backup_table_name} ADD COLUMN archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            )
            
            await session.commit()
            logger.info(f"Created backup table: {backup_table_name}")
            
    except Exception as e:
        logger.error(f"Failed to create backup table for {table_name}: {e}")
        raise