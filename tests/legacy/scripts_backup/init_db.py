#!/usr/bin/env python3
"""Simple database initialization script for the Reality Checker WhatsApp bot."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_database
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def init_database():
    """Initialize the database."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Get database instance
        db = get_database()
        
        # Initialize database (creates tables)
        await db.initialize()
        
        print("✅ Database initialized successfully!")
        
        # Test basic operations
        async with db.get_session() as session:
            from app.database.models import Configuration
            
            # Try to create a test configuration
            config = Configuration(
                key="test_key",
                value="test_value",
                description="Test configuration"
            )
            session.add(config)
            await session.commit()
            
            print("✅ Database operations test passed!")
            
            # Clean up test data
            await session.delete(config)
            await session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)