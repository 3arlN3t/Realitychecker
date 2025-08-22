#!/usr/bin/env python3
"""
Database management CLI for the Reality Checker WhatsApp bot.

This script provides commands for database initialization, migration,
backup, and maintenance operations.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Database, get_database
from app.database.migrations import (
    run_migrations, create_migration, initialize_database,
    check_database_version
)
from app.database.backup import DatabaseBackupManager
from app.database.retention import DataRetentionManager
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def init_db():
    """Initialize the database with schema and initial data."""
    print("Initializing database...")
    try:
        await initialize_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    return True


async def check_db():
    """Check database version and status."""
    print("Checking database status...")
    try:
        db = get_database()
        health = await db.health_check()
        print(f"Database Status: {health['status']}")
        print(f"Database Type: {health['database_type']}")
        print(f"Initialized: {health['initialized']}")
        
        version_info = await check_database_version()
        print(f"Migration Status: {version_info['status']}")
        print(f"Current Revision: {version_info['current_revision']}")
        print(f"Needs Migration: {version_info['needs_migration']}")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    return True


async def migrate_db():
    """Run database migrations."""
    print("Running database migrations...")
    try:
        # Initialize database first
        db = get_database()
        await db.initialize()
        print("✅ Database migrations completed successfully!")
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False
    return True


def create_migration_file(message: str):
    """Create a new migration file."""
    print(f"Creating migration: {message}")
    try:
        create_migration(message, autogenerate=True)
        print("✅ Migration created successfully!")
    except Exception as e:
        print(f"❌ Migration creation failed: {e}")
        return False
    return True


async def backup_db(backup_name: str = None):
    """Create a database backup."""
    print("Creating database backup...")
    try:
        backup_manager = DatabaseBackupManager()
        result = await backup_manager.create_backup(backup_name)
        
        if result["status"] == "success":
            print(f"✅ Backup created successfully!")
            print(f"Backup Name: {result['backup_name']}")
            print(f"File Size: {result['file_size']} bytes")
            print(f"Path: {result['backup_path']}")
        else:
            print(f"❌ Backup failed: {result['message']}")
            return False
    except Exception as e:
        print(f"❌ Backup creation failed: {e}")
        return False
    return True


def list_backups():
    """List available backups."""
    print("Available backups:")
    try:
        backup_manager = DatabaseBackupManager()
        backups = backup_manager.list_backups()
        
        if not backups:
            print("No backups found.")
            return True
        
        print(f"{'Name':<20} {'Size':<15} {'Created':<25}")
        print("-" * 65)
        
        for backup in backups:
            size_mb = backup["file_size"] / (1024 * 1024)
            created = backup["created_at"][:19]  # Remove microseconds
            print(f"{backup['backup_name']:<20} {size_mb:.2f} MB{'':<7} {created}")
        
    except Exception as e:
        print(f"❌ Failed to list backups: {e}")
        return False
    return True


async def restore_db(backup_name: str):
    """Restore database from backup."""
    print(f"Restoring database from backup: {backup_name}")
    try:
        backup_manager = DatabaseBackupManager()
        result = await backup_manager.restore_backup(backup_name)
        
        if result["status"] == "success":
            print("✅ Database restored successfully!")
            print(f"Restored from: {result['backup_path']}")
        else:
            print(f"❌ Restore failed: {result['message']}")
            return False
    except Exception as e:
        print(f"❌ Database restore failed: {e}")
        return False
    return True


async def cleanup_data():
    """Run data retention cleanup."""
    print("Running data retention cleanup...")
    try:
        retention_manager = DataRetentionManager()
        result = await retention_manager.run_cleanup_job()
        
        if result["status"] == "completed":
            print("✅ Data cleanup completed successfully!")
            print(f"Total processed: {result['total_processed']} records")
            print(f"Successful policies: {result['successful_policies']}/{result['total_policies']}")
        else:
            print(f"❌ Data cleanup failed")
            return False
    except Exception as e:
        print(f"❌ Data cleanup failed: {e}")
        return False
    return True


async def show_stats():
    """Show database statistics."""
    print("Database Statistics:")
    try:
        db = get_database()
        async with db.get_session() as session:
            from app.database.repositories import (
                WhatsAppUserRepository, UserInteractionRepository,
                SystemMetricRepository, ErrorLogRepository
            )
            
            user_repo = WhatsAppUserRepository(session)
            interaction_repo = UserInteractionRepository(session)
            metric_repo = SystemMetricRepository(session)
            error_repo = ErrorLogRepository(session)
            
            # Get user stats
            user_stats = await user_repo.get_user_statistics()
            print(f"Users: {user_stats['total_users']} total, {user_stats['active_users']} active, {user_stats['blocked_users']} blocked")
            
            # Get interaction stats
            interaction_stats = await interaction_repo.get_interaction_statistics()
            print(f"Interactions: {interaction_stats['total_interactions']} total, {interaction_stats['success_rate']:.1f}% success rate")
            
            # Get latest metrics
            latest_metrics = await metric_repo.get_latest_metrics(1)
            if latest_metrics:
                metric = latest_metrics[0]
                print(f"Latest Metrics: CPU {metric.cpu_usage:.1f}%, Memory {metric.memory_usage:.1f}%, Disk {metric.disk_usage:.1f}%")
            
            # Get error stats
            error_stats = await error_repo.get_error_statistics()
            print(f"Errors (last 7 days): {error_stats['total_errors']}")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
        return False
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Database management CLI for Reality Checker WhatsApp bot")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database with schema and initial data")
    
    # Check command
    subparsers.add_parser("check", help="Check database status and version")
    
    # Migrate command
    subparsers.add_parser("migrate", help="Run database migrations")
    
    # Create migration command
    create_parser = subparsers.add_parser("create-migration", help="Create new migration file")
    create_parser.add_argument("message", help="Migration message/description")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument("--name", help="Custom backup name")
    
    # List backups command
    subparsers.add_parser("list-backups", help="List available backups")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database from backup")
    restore_parser.add_argument("backup_name", help="Name of backup to restore")
    
    # Cleanup command
    subparsers.add_parser("cleanup", help="Run data retention cleanup")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle commands
    if args.command == "init":
        success = asyncio.run(init_db())
    elif args.command == "check":
        success = asyncio.run(check_db())
    elif args.command == "migrate":
        success = asyncio.run(migrate_db())
    elif args.command == "create-migration":
        success = create_migration_file(args.message)
    elif args.command == "backup":
        success = asyncio.run(backup_db(args.name))
    elif args.command == "list-backups":
        success = list_backups()
    elif args.command == "restore":
        success = asyncio.run(restore_db(args.backup_name))
    elif args.command == "cleanup":
        success = asyncio.run(cleanup_data())
    elif args.command == "stats":
        success = asyncio.run(show_stats())
    else:
        parser.print_help()
        return
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()