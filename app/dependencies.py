"""
Dependency injection container for the Reality Checker application.

This module provides FastAPI dependencies for service injection and manages
service lifecycle, health checks, and configuration validation.
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from app.config import get_config, AppConfig
from app.services.message_handler import MessageHandlerService
from app.services.openai_analysis import OpenAIAnalysisService
from app.services.pdf_processing import PDFProcessingService
from app.services.twilio_response import TwilioResponseService
from app.services.user_management import UserManagementService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ServiceContainer:
    """Container for managing service instances and their dependencies."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the service container with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._services: Dict[str, Any] = {}
        self._health_checks: Dict[str, bool] = {}
        
    def get_pdf_service(self) -> PDFProcessingService:
        """Get or create PDF processing service instance."""
        if 'pdf_service' not in self._services:
            self._services['pdf_service'] = PDFProcessingService(self.config)
        return self._services['pdf_service']
    
    def get_openai_service(self) -> OpenAIAnalysisService:
        """Get or create OpenAI analysis service instance."""
        if 'openai_service' not in self._services:
            self._services['openai_service'] = OpenAIAnalysisService(self.config)
        return self._services['openai_service']
    
    def get_twilio_service(self) -> TwilioResponseService:
        """Get or create Twilio response service instance."""
        if 'twilio_service' not in self._services:
            self._services['twilio_service'] = TwilioResponseService(self.config)
        return self._services['twilio_service']
    
    def get_user_service(self) -> UserManagementService:
        """Get or create user management service instance."""
        if 'user_service' not in self._services:
            self._services['user_service'] = UserManagementService(self.config)
        return self._services['user_service']
    
    def get_message_handler(self) -> MessageHandlerService:
        """Get or create message handler service instance."""
        if 'message_handler' not in self._services:
            # Create message handler with injected dependencies
            pdf_service = self.get_pdf_service()
            openai_service = self.get_openai_service()
            twilio_service = self.get_twilio_service()
            user_service = self.get_user_service()
            
            # Create message handler with pre-initialized services
            message_handler = MessageHandlerService(self.config)
            message_handler.pdf_service = pdf_service
            message_handler.openai_service = openai_service
            message_handler.twilio_service = twilio_service
            message_handler.user_service = user_service
            
            self._services['message_handler'] = message_handler
        return self._services['message_handler']
    
    async def perform_health_checks(self) -> Dict[str, str]:
        """
        Perform health checks on all services.
        
        Returns:
            Dict mapping service names to their health status
        """
        health_status = {}
        
        # Check OpenAI configuration
        try:
            if self.config.openai_api_key and self.config.openai_api_key.startswith('sk-'):
                health_status['openai'] = 'connected'
            else:
                health_status['openai'] = 'not_configured'
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            health_status['openai'] = 'error'
        
        # Check Twilio configuration
        try:
            if (self.config.twilio_account_sid and 
                self.config.twilio_auth_token and 
                self.config.twilio_phone_number):
                health_status['twilio'] = 'connected'
            else:
                health_status['twilio'] = 'not_configured'
        except Exception as e:
            logger.warning(f"Twilio health check failed: {e}")
            health_status['twilio'] = 'error'
        
        # Check PDF processing service
        try:
            pdf_service = self.get_pdf_service()
            if pdf_service.max_size_bytes > 0:
                health_status['pdf_processing'] = 'ready'
            else:
                health_status['pdf_processing'] = 'error'
        except Exception as e:
            logger.warning(f"PDF processing health check failed: {e}")
            health_status['pdf_processing'] = 'error'
        
        self._health_checks = health_status
        return health_status
    
    def get_health_status(self) -> Dict[str, str]:
        """Get cached health status or return empty dict if not checked yet."""
        return self._health_checks.copy()
    
    async def cleanup(self):
        """Cleanup resources and close connections."""
        logger.info("Cleaning up service container resources")
        
        # Close any async clients or connections
        if 'openai_service' in self._services:
            try:
                openai_service = self._services['openai_service']
                if hasattr(openai_service, 'client') and hasattr(openai_service.client, 'close'):
                    await openai_service.client.close()
            except Exception as e:
                logger.warning(f"Error closing OpenAI client: {e}")
        
        # Clear service cache
        self._services.clear()
        self._health_checks.clear()
        
        logger.info("Service container cleanup completed")


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        config = get_config()
        _service_container = ServiceContainer(config)
    return _service_container


def reset_service_container():
    """Reset the global service container (useful for testing)."""
    global _service_container
    _service_container = None


# FastAPI dependency functions
@lru_cache()
def get_app_config() -> AppConfig:
    """FastAPI dependency to get application configuration."""
    return get_config()


def get_pdf_processing_service() -> PDFProcessingService:
    """FastAPI dependency to get PDF processing service."""
    container = get_service_container()
    return container.get_pdf_service()


def get_openai_analysis_service() -> OpenAIAnalysisService:
    """FastAPI dependency to get OpenAI analysis service."""
    container = get_service_container()
    return container.get_openai_service()


def get_twilio_response_service() -> TwilioResponseService:
    """FastAPI dependency to get Twilio response service."""
    container = get_service_container()
    return container.get_twilio_service()


def get_message_handler_service() -> MessageHandlerService:
    """FastAPI dependency to get message handler service."""
    container = get_service_container()
    return container.get_message_handler()


def get_user_management_service() -> UserManagementService:
    """FastAPI dependency to get user management service."""
    container = get_service_container()
    return container.get_user_service()