"""
Initialization module for graceful error handling system.

This module provides initialization and cleanup functions for the graceful
error handling and recovery system.
"""

import asyncio
import logging
from typing import Optional

from app.utils.logging import get_logger
from app.utils.graceful_error_handling import init_graceful_error_handler, cleanup_graceful_error_handler
from app.utils.error_diagnostics import get_diagnostics_collector

logger = get_logger(__name__)


async def initialize_graceful_error_handling() -> bool:
    """
    Initialize the graceful error handling system.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        logger.info("Initializing graceful error handling system...")
        
        # Initialize graceful error handler
        graceful_handler = await init_graceful_error_handler()
        
        # Initialize diagnostics collector
        diagnostics_collector = get_diagnostics_collector()
        
        logger.info("✅ Graceful error handling system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize graceful error handling system: {e}")
        return False


async def cleanup_graceful_error_handling():
    """Clean up the graceful error handling system."""
    try:
        logger.info("Cleaning up graceful error handling system...")
        
        # Cleanup graceful error handler
        await cleanup_graceful_error_handler()
        
        logger.info("✅ Graceful error handling system cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Error during graceful error handling cleanup: {e}")


def setup_error_handling_for_app(app):
    """
    Set up error handling for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    @app.on_event("startup")
    async def startup_graceful_error_handling():
        """Initialize graceful error handling on app startup."""
        await initialize_graceful_error_handling()
    
    @app.on_event("shutdown")
    async def shutdown_graceful_error_handling():
        """Cleanup graceful error handling on app shutdown."""
        await cleanup_graceful_error_handling()