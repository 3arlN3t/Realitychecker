"""
Database backup and recovery utilities for the Reality Checker WhatsApp bot.

This module provides utilities for creating backups, restoring from backups,
and managing backup schedules.
"""

import os
import shutil
import gzip
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy import text, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logging import get_logger
from .database import get_database
from .models import Base

logger = get_logger(__name__)


class DatabaseBackupManager:
    """Manager for database backup and recovery operations."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.db = get_database()
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a full database backup.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Dictionary with backup information
        """
        if not backup_name:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        logger.info(f"Creating database backup: {backup_name}")
        
        try:
            backup_path = self.backup_dir / f"{backup_name}.sql.gz"
            
            # Create SQL dump
            sql_dump = await self._create_sql_dump()
            
            # Compress and save
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                f.write(sql_dump)
            
            # Create metadata file
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "database_url": self.db.database_url,
                "file_size": backup_path.stat().st_size,
                "tables": await self._get_table_info()
            }
            
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "metadata_path": str(metadata_path),
                "file_size": backup_path.stat().st_size,
                "created_at": metadata["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {
                "status": "error",
                "message": str(e),
                "backup_name": backup_name
            }
    
    async def _create_sql_dump(self) -> str:
        """
        Create SQL dump of the database.
        
        Returns:
            SQL dump as string
        """
        async with self.db.get_session() as session:
            # Get all table names
            tables = await self._get_table_names(session)
            
            sql_dump = []
            sql_dump.append("-- Database backup created at " + datetime.now(timezone.utc).isoformat())
            sql_dump.append("-- Reality Checker WhatsApp Bot Database")
            sql_dump.append("")
            
            # Add table schema and data
            for table in tables:
                # Get table schema
                schema = await self._get_table_schema(session, table)
                sql_dump.append(f"-- Table: {table}")
                sql_dump.append(schema)
                sql_dump.append("")
                
                # Get table data
                data = await self._get_table_data(session, table)
                if data:
                    sql_dump.extend(data)
                    sql_dump.append("")
            
            return "\n".join(sql_dump)
    
    async def _get_table_names(self, session: AsyncSession) -> List[str]:
        """Get all table names from the database."""
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        )
        return [row[0] for row in result.fetchall()]
    
    async def _get_table_schema(self, session: AsyncSession, table_name: str) -> str:
        """Get CREATE TABLE statement for a table."""
        result = await session.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": table_name}
        )
        schema = result.scalar()
        return f"{schema};" if schema else ""
    
    async def _get_table_data(self, session: AsyncSession, table_name: str) -> List[str]:
        """Get INSERT statements for table data."""
        try:
            # Get column names
            result = await session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            
            # Get all data
            result = await session.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            
            if not rows:
                return []
            
            insert_statements = []
            for row in rows:
                # Format values for SQL insert
                values = []
                for value in row:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # Escape single quotes
                        escaped = value.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    else:
                        values.append(f"'{str(value)}'")
                
                columns_str = ", ".join(columns)
                values_str = ", ".join(values)
                insert_statements.append(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")
            
            return insert_statements
            
        except Exception as e:
            logger.warning(f"Failed to get data for table {table_name}: {e}")
            return []
    
    async def _get_table_info(self) -> Dict[str, Any]:
        """Get information about all tables."""
        async with self.db.get_session() as session:
            tables = await self._get_table_names(session)
            table_info = {}
            
            for table in tables:
                try:
                    # Get row count
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = result.scalar()
                    
                    table_info[table] = {
                        "row_count": row_count
                    }
                except Exception as e:
                    logger.warning(f"Failed to get info for table {table}: {e}")
                    table_info[table] = {
                        "row_count": 0,
                        "error": str(e)
                    }
            
            return table_info
    
    async def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Restore database from backup.
        
        Args:
            backup_name: Name of the backup to restore
            
        Returns:
            Dictionary with restore information
        """
        logger.info(f"Restoring database from backup: {backup_name}")
        
        try:
            backup_path = self.backup_dir / f"{backup_name}.sql.gz"
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            
            if not backup_path.exists():
                return {
                    "status": "error",
                    "message": f"Backup file not found: {backup_path}"
                }
            
            # Read metadata
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Read backup file
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                sql_dump = f.read()
            
            # Execute restore
            await self._execute_restore(sql_dump)
            
            logger.info(f"Database restored successfully from backup: {backup_name}")
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "metadata": metadata,
                "restored_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return {
                "status": "error",
                "message": str(e),
                "backup_name": backup_name
            }
    
    async def _execute_restore(self, sql_dump: str):
        """Execute SQL dump to restore database."""
        async with self.db.get_session() as session:
            # Split SQL dump into individual statements
            statements = [stmt.strip() for stmt in sql_dump.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.startswith('--'):
                    continue  # Skip comments
                
                try:
                    await session.execute(text(statement))
                except Exception as e:
                    logger.warning(f"Failed to execute statement: {statement[:100]}... Error: {e}")
            
            await session.commit()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql.gz"):
            backup_name = backup_file.stem.replace('.sql', '')
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            
            backup_info = {
                "backup_name": backup_name,
                "backup_path": str(backup_file),
                "file_size": backup_file.stat().st_size,
                "created_at": datetime.fromtimestamp(
                    backup_file.stat().st_ctime, 
                    tz=timezone.utc
                ).isoformat()
            }
            
            # Add metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    backup_info.update(metadata)
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {backup_name}: {e}")
            
            backups.append(backup_info)
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Delete a backup.
        
        Args:
            backup_name: Name of the backup to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            backup_path = self.backup_dir / f"{backup_name}.sql.gz"
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            
            if not backup_path.exists():
                return {
                    "status": "error",
                    "message": f"Backup not found: {backup_name}"
                }
            
            # Delete backup file
            backup_path.unlink()
            
            # Delete metadata file if exists
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted backup: {backup_name}")
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "message": "Backup deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "backup_name": backup_name
            }
    
    def cleanup_old_backups(self, keep_count: int = 10) -> Dict[str, Any]:
        """
        Clean up old backups, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return {
                    "status": "success",
                    "message": f"No cleanup needed. Found {len(backups)} backups, keeping {keep_count}",
                    "deleted_count": 0
                }
            
            # Delete oldest backups
            backups_to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                result = self.delete_backup(backup["backup_name"])
                if result["status"] == "success":
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            
            return {
                "status": "success",
                "message": f"Cleaned up {deleted_count} old backups",
                "deleted_count": deleted_count,
                "remaining_count": len(backups) - deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return {
                "status": "error",
                "message": str(e),
                "deleted_count": 0
            }
    
    async def verify_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Verify the integrity of a backup.
        
        Args:
            backup_name: Name of the backup to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            backup_path = self.backup_dir / f"{backup_name}.sql.gz"
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            
            if not backup_path.exists():
                return {
                    "status": "error",
                    "message": f"Backup file not found: {backup_path}"
                }
            
            verification_results = {
                "backup_name": backup_name,
                "file_exists": True,
                "file_size": backup_path.stat().st_size,
                "readable": False,
                "metadata_exists": metadata_path.exists(),
                "sql_valid": False
            }
            
            # Test if file is readable
            try:
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1KB
                    verification_results["readable"] = True
                    verification_results["sql_valid"] = "CREATE TABLE" in content or "INSERT INTO" in content
            except Exception as e:
                verification_results["read_error"] = str(e)
            
            # Verify metadata
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    verification_results["metadata_valid"] = True
                    verification_results["metadata"] = metadata
                except Exception as e:
                    verification_results["metadata_valid"] = False
                    verification_results["metadata_error"] = str(e)
            
            # Overall status
            if verification_results["readable"] and verification_results["sql_valid"]:
                verification_results["status"] = "valid"
            else:
                verification_results["status"] = "invalid"
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify backup {backup_name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "backup_name": backup_name
            }


# Backup scheduling functions
async def schedule_backup_job(backup_name: Optional[str] = None):
    """
    Schedule a backup job.
    This function should be called from a background task scheduler.
    
    Args:
        backup_name: Optional custom backup name
    """
    backup_manager = DatabaseBackupManager()
    
    try:
        result = await backup_manager.create_backup(backup_name)
        logger.info(f"Scheduled backup completed: {result}")
        
        # Clean up old backups
        cleanup_result = backup_manager.cleanup_old_backups()
        logger.info(f"Backup cleanup completed: {cleanup_result}")
        
        return result
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")
        raise


async def create_emergency_backup():
    """
    Create an emergency backup before critical operations.
    """
    backup_manager = DatabaseBackupManager()
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"emergency_backup_{timestamp}"
    
    try:
        result = await backup_manager.create_backup(backup_name)
        logger.info(f"Emergency backup created: {result}")
        return result
    except Exception as e:
        logger.error(f"Emergency backup failed: {e}")
        raise