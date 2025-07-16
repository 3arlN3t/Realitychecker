"""
Database module for the Reality Checker WhatsApp bot.

This module provides database connectivity, models, and utilities for
persistent data storage using SQLAlchemy with SQLite and PostgreSQL support.
"""

from .database import Database, get_database
from .models import (
    WhatsAppUser, UserInteraction, SystemMetric, AnalysisHistory,
    SystemUser, ErrorLog, Configuration, DataRetentionPolicy,
    JobClassificationEnum, UserRoleEnum
)
from .migrations import run_migrations, create_migration
from .repositories import (
    WhatsAppUserRepository, UserInteractionRepository,
    SystemMetricRepository, ConfigurationRepository, ErrorLogRepository
)
from .retention import DataRetentionManager
from .backup import DatabaseBackupManager

__all__ = [
    "Database",
    "get_database",
    "WhatsAppUser", "UserInteraction", "SystemMetric", "AnalysisHistory",
    "SystemUser", "ErrorLog", "Configuration", "DataRetentionPolicy",
    "JobClassificationEnum", "UserRoleEnum",
    "run_migrations", "create_migration",
    "WhatsAppUserRepository", "UserInteractionRepository",
    "SystemMetricRepository", "ConfigurationRepository", "ErrorLogRepository",
    "DataRetentionManager",
    "DatabaseBackupManager",
]