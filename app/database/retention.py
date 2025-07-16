"""
Data retention and cleanup utilities for the Reality Checker WhatsApp bot.

This module provides utilities for managing data retention policies,
archiving old data, and cleaning up expired records.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logging import get_logger
from .database import get_database
from .models import (
    UserInteraction, SystemMetric, ErrorLog, AnalysisHistory,
    DataRetentionPolicy, WhatsAppUser
)

logger = get_logger(__name__)


class DataRetentionManager:
    """Manager for data retention policies and cleanup operations."""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_retention_policies(self) -> List[DataRetentionPolicy]:
        """
        Get all active retention policies.
        
        Returns:
            List of DataRetentionPolicy objects
        """
        async with self.db.get_session() as session:
            result = await session.execute(
                select(DataRetentionPolicy)
                .where(DataRetentionPolicy.is_active == True)
                .order_by(DataRetentionPolicy.table_name)
            )
            return result.scalars().all()
    
    async def apply_retention_policy(self, policy: DataRetentionPolicy) -> Dict[str, Any]:
        """
        Apply a retention policy to a specific table.
        
        Args:
            policy: DataRetentionPolicy to apply
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"Applying retention policy for table: {policy.table_name}")
        
        try:
            if policy.policy_type == "delete":
                return await self._delete_old_records(policy)
            elif policy.policy_type == "archive":
                return await self._archive_old_records(policy)
            else:
                logger.warning(f"Unknown policy type: {policy.policy_type}")
                return {
                    "status": "error",
                    "message": f"Unknown policy type: {policy.policy_type}",
                    "processed_count": 0
                }
        except Exception as e:
            logger.error(f"Error applying retention policy for {policy.table_name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "processed_count": 0
            }
    
    async def _delete_old_records(self, policy: DataRetentionPolicy) -> Dict[str, Any]:
        """
        Delete old records based on retention policy.
        
        Args:
            policy: DataRetentionPolicy to apply
            
        Returns:
            Dictionary with deletion results
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
        
        async with self.db.get_session() as session:
            # Get count of records to be deleted
            count_query = text(f"""
                SELECT COUNT(*) FROM {policy.table_name} 
                WHERE {policy.date_column or 'timestamp'} < :cutoff_date
            """)
            
            result = await session.execute(count_query, {"cutoff_date": cutoff_date})
            count = result.scalar()
            
            if count == 0:
                return {
                    "status": "success",
                    "message": "No records to delete",
                    "processed_count": 0
                }
            
            # Delete old records
            delete_query = text(f"""
                DELETE FROM {policy.table_name} 
                WHERE {policy.date_column or 'timestamp'} < :cutoff_date
            """)
            
            await session.execute(delete_query, {"cutoff_date": cutoff_date})
            await session.commit()
            
            # Update policy statistics
            policy.last_run = datetime.now(timezone.utc)
            policy.records_processed += count
            await session.commit()
            
            logger.info(f"Deleted {count} records from {policy.table_name}")
            
            return {
                "status": "success",
                "message": f"Deleted {count} records",
                "processed_count": count
            }
    
    async def _archive_old_records(self, policy: DataRetentionPolicy) -> Dict[str, Any]:
        """
        Archive old records to backup table.
        
        Args:
            policy: DataRetentionPolicy to apply
            
        Returns:
            Dictionary with archival results
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
        archive_table = f"{policy.table_name}_archive"
        
        async with self.db.get_session() as session:
            # Ensure archive table exists
            await self._ensure_archive_table_exists(session, policy.table_name)
            
            # Get count of records to be archived
            count_query = text(f"""
                SELECT COUNT(*) FROM {policy.table_name} 
                WHERE {policy.date_column or 'timestamp'} < :cutoff_date
            """)
            
            result = await session.execute(count_query, {"cutoff_date": cutoff_date})
            count = result.scalar()
            
            if count == 0:
                return {
                    "status": "success",
                    "message": "No records to archive",
                    "processed_count": 0
                }
            
            # Move records to archive table
            insert_query = text(f"""
                INSERT INTO {archive_table} 
                SELECT *, CURRENT_TIMESTAMP as archived_at
                FROM {policy.table_name}
                WHERE {policy.date_column or 'timestamp'} < :cutoff_date
            """)
            
            await session.execute(insert_query, {"cutoff_date": cutoff_date})
            
            # Delete original records
            delete_query = text(f"""
                DELETE FROM {policy.table_name} 
                WHERE {policy.date_column or 'timestamp'} < :cutoff_date
            """)
            
            await session.execute(delete_query, {"cutoff_date": cutoff_date})
            await session.commit()
            
            # Update policy statistics
            policy.last_run = datetime.now(timezone.utc)
            policy.records_processed += count
            await session.commit()
            
            logger.info(f"Archived {count} records from {policy.table_name}")
            
            return {
                "status": "success",
                "message": f"Archived {count} records",
                "processed_count": count
            }
    
    async def _ensure_archive_table_exists(self, session: AsyncSession, table_name: str):
        """
        Ensure archive table exists for the given table.
        
        Args:
            session: Database session
            table_name: Name of the source table
        """
        archive_table = f"{table_name}_archive"
        
        # Check if archive table exists
        check_query = text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=:table_name
        """)
        
        result = await session.execute(check_query, {"table_name": archive_table})
        exists = result.scalar() is not None
        
        if not exists:
            # Create archive table with same structure as original
            create_query = text(f"""
                CREATE TABLE {archive_table} AS 
                SELECT * FROM {table_name} WHERE 1=0
            """)
            await session.execute(create_query)
            
            # Add archived_at column
            alter_query = text(f"""
                ALTER TABLE {archive_table} 
                ADD COLUMN archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            await session.execute(alter_query)
            
            logger.info(f"Created archive table: {archive_table}")
    
    async def run_cleanup_job(self) -> Dict[str, Any]:
        """
        Run cleanup job for all active retention policies.
        
        Returns:
            Dictionary with cleanup results for all policies
        """
        logger.info("Starting data retention cleanup job")
        
        policies = await self.get_retention_policies()
        results = {}
        
        for policy in policies:
            try:
                result = await self.apply_retention_policy(policy)
                results[policy.table_name] = result
            except Exception as e:
                logger.error(f"Error processing policy for {policy.table_name}: {e}")
                results[policy.table_name] = {
                    "status": "error",
                    "message": str(e),
                    "processed_count": 0
                }
        
        # Generate summary
        total_processed = sum(r.get("processed_count", 0) for r in results.values())
        successful_policies = len([r for r in results.values() if r["status"] == "success"])
        
        logger.info(f"Cleanup job completed. Processed {total_processed} records across {successful_policies} policies")
        
        return {
            "status": "completed",
            "total_processed": total_processed,
            "successful_policies": successful_policies,
            "total_policies": len(policies),
            "policy_results": results
        }
    
    async def get_retention_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about data retention and cleanup.
        
        Returns:
            Dictionary with retention statistics
        """
        async with self.db.get_session() as session:
            # Get policy statistics
            policies = await self.get_retention_policies()
            
            policy_stats = []
            for policy in policies:
                # Get current record count
                count_query = text(f"SELECT COUNT(*) FROM {policy.table_name}")
                result = await session.execute(count_query)
                current_count = result.scalar()
                
                # Get archive table count if exists
                archive_count = 0
                archive_table = f"{policy.table_name}_archive"
                try:
                    archive_count_query = text(f"SELECT COUNT(*) FROM {archive_table}")
                    result = await session.execute(archive_count_query)
                    archive_count = result.scalar()
                except:
                    pass  # Archive table doesn't exist
                
                policy_stats.append({
                    "table_name": policy.table_name,
                    "policy_type": policy.policy_type,
                    "retention_days": policy.retention_days,
                    "current_records": current_count,
                    "archived_records": archive_count,
                    "last_run": policy.last_run.isoformat() if policy.last_run else None,
                    "total_processed": policy.records_processed
                })
            
            # Get database size information
            db_size_query = text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            result = await session.execute(db_size_query)
            db_size = result.scalar()
            
            return {
                "database_size_bytes": db_size,
                "total_policies": len(policies),
                "active_policies": len([p for p in policies if p.is_active]),
                "policy_statistics": policy_stats
            }
    
    async def create_retention_policy(
        self,
        table_name: str,
        retention_days: int,
        policy_type: str = "delete",
        date_column: Optional[str] = None
    ) -> DataRetentionPolicy:
        """
        Create a new retention policy.
        
        Args:
            table_name: Name of the table
            retention_days: Number of days to retain data
            policy_type: Type of policy ('delete' or 'archive')
            date_column: Column to use for date filtering
            
        Returns:
            Created DataRetentionPolicy object
        """
        async with self.db.get_session() as session:
            policy = DataRetentionPolicy(
                table_name=table_name,
                retention_days=retention_days,
                policy_type=policy_type,
                date_column=date_column
            )
            
            session.add(policy)
            await session.commit()
            await session.refresh(policy)
            
            logger.info(f"Created retention policy for {table_name}: {retention_days} days, {policy_type}")
            
            return policy
    
    async def update_retention_policy(
        self,
        policy_id: int,
        retention_days: Optional[int] = None,
        policy_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[DataRetentionPolicy]:
        """
        Update an existing retention policy.
        
        Args:
            policy_id: ID of the policy to update
            retention_days: New retention days
            policy_type: New policy type
            is_active: New active status
            
        Returns:
            Updated DataRetentionPolicy object or None
        """
        async with self.db.get_session() as session:
            policy = await session.get(DataRetentionPolicy, policy_id)
            
            if not policy:
                return None
            
            if retention_days is not None:
                policy.retention_days = retention_days
            if policy_type is not None:
                policy.policy_type = policy_type
            if is_active is not None:
                policy.is_active = is_active
            
            await session.commit()
            await session.refresh(policy)
            
            logger.info(f"Updated retention policy {policy_id} for {policy.table_name}")
            
            return policy


# Cleanup scheduler functions
async def schedule_cleanup_job():
    """
    Schedule periodic cleanup job.
    This function should be called from a background task scheduler.
    """
    retention_manager = DataRetentionManager()
    
    try:
        result = await retention_manager.run_cleanup_job()
        logger.info(f"Scheduled cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")
        raise


async def cleanup_expired_sessions():
    """
    Clean up expired user sessions and temporary data.
    """
    logger.info("Starting session cleanup")
    
    try:
        db = get_database()
        async with db.get_session() as session:
            # Clean up old temporary data (older than 24 hours)
            cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Update user last_seen for inactive users
            inactive_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            
            # This would be expanded based on actual session management needs
            logger.info("Session cleanup completed")
            
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise


async def optimize_database():
    """
    Optimize database performance by running maintenance tasks.
    """
    logger.info("Starting database optimization")
    
    try:
        db = get_database()
        async with db.get_session() as session:
            # Run VACUUM for SQLite to reclaim space
            await session.execute(text("VACUUM"))
            
            # Analyze tables for better query planning
            await session.execute(text("ANALYZE"))
            
            # Update statistics
            await session.commit()
            
            logger.info("Database optimization completed")
            
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise