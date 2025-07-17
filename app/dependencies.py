"""
FastAPI dependencies for the Reality Checker application.

This module provides dependency injection for services, authentication, authorization,
and other common functionality.
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_config, AppConfig
from app.services.message_handler import MessageHandlerService
from app.services.pdf_processing import PDFProcessingService
from app.services.enhanced_ai_analysis import EnhancedAIAnalysisService
from app.services.twilio_response import TwilioResponseService
from app.services.user_management import UserManagementService
from app.services.analytics import AnalyticsService
from app.services.authentication import get_auth_service, AuthenticationService
from app.models.data_models import User, UserRole
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


class ServiceContainer:
    """
    Service container for dependency injection.
    
    Manages service instances and their dependencies.
    """
    
    def __init__(self, config: AppConfig):
        """Initialize the service container."""
        self._config: Optional[AppConfig] = config
        self._pdf_service: Optional[PDFProcessingService] = None
        self._openai_service: Optional[EnhancedAIAnalysisService] = None
        self._twilio_service: Optional[TwilioResponseService] = None
        self._message_handler: Optional[MessageHandlerService] = None
        self._user_management_service: Optional[UserManagementService] = None
        self._analytics_service: Optional[AnalyticsService] = None
        self._auth_service: Optional[AuthenticationService] = None
    
    def get_config(self) -> AppConfig:
        """Get application configuration."""
        if self._config is None:
            self._config = get_config()
        return self._config
    
    def get_pdf_service(self) -> PDFProcessingService:
        """Get PDF processing service."""
        if self._pdf_service is None:
            config = self.get_config()
            self._pdf_service = PDFProcessingService(config)
        return self._pdf_service
    
    def get_openai_service(self) -> EnhancedAIAnalysisService:
        """Get Enhanced AI analysis service."""
        if self._openai_service is None:
            config = self.get_config()
            self._openai_service = EnhancedAIAnalysisService(config)
        return self._openai_service
    
    def get_twilio_service(self) -> TwilioResponseService:
        """Get Twilio response service."""
        if self._twilio_service is None:
            config = self.get_config()
            self._twilio_service = TwilioResponseService(config)
        return self._twilio_service
    
    def get_message_handler(self) -> MessageHandlerService:
        """Get message handler service."""
        if self._message_handler is None:
            config = self.get_config()
            self._message_handler = MessageHandlerService(config)
        return self._message_handler
    
    def get_user_management_service(self) -> UserManagementService:
        """Get user management service."""
        if self._user_management_service is None:
            config = self.get_config()
            self._user_management_service = UserManagementService(config)
        return self._user_management_service
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service."""
        if self._analytics_service is None:
            config = self.get_config()
            user_management_service = self.get_user_management_service()
            self._analytics_service = AnalyticsService(config, user_management_service)
        return self._analytics_service
    
    def get_auth_service(self) -> AuthenticationService:
        """Get authentication service."""
        if self._auth_service is None:
            self._auth_service = get_auth_service()
        return self._auth_service
    
    async def perform_health_checks(self) -> Dict[str, str]:
        """
        Perform health checks on all services.
        
        Returns:
            Dict mapping service names to their health status
        """
        health_status = {}
        
        try:
            # Check OpenAI service
            openai_service = self.get_openai_service()
            openai_status = await openai_service.health_check()
            health_status["openai"] = openai_status
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            health_status["openai"] = "error"
        
        try:
            # Check Twilio service
            twilio_service = self.get_twilio_service()
            twilio_status = await twilio_service.health_check()
            health_status["twilio"] = twilio_status
        except Exception as e:
            logger.error(f"Twilio health check failed: {e}")
            health_status["twilio"] = "error"
        
        try:
            # Check PDF service
            pdf_service = self.get_pdf_service()
            health_status["pdf_processing"] = "ready"
        except Exception as e:
            logger.error(f"PDF service health check failed: {e}")
            health_status["pdf_processing"] = "error"
        
        try:
            # Check user management service
            user_service = self.get_user_management_service()
            health_status["user_management"] = "ready"
        except Exception as e:
            logger.error(f"User management health check failed: {e}")
            health_status["user_management"] = "error"
        
        try:
            # Check analytics service
            analytics_service = self.get_analytics_service()
            health_status["analytics"] = "ready"
        except Exception as e:
            logger.error(f"Analytics health check failed: {e}")
            health_status["analytics"] = "error"
        
        try:
            # Check authentication service
            auth_service = self.get_auth_service()
            health_status["authentication"] = "ready"
        except Exception as e:
            logger.error(f"Authentication health check failed: {e}")
            health_status["authentication"] = "error"
        
        return health_status
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up service container resources...")
        
        # Clean up services that need cleanup
        if self._twilio_service:
            try:
                await self._twilio_service.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Twilio service: {e}")
        
        if self._openai_service:
            try:
                await self._openai_service.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up OpenAI service: {e}")
        
        logger.info("Service container cleanup completed")


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container(config: AppConfig = Depends(get_config)) -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer(config)
    return _service_container


def reset_service_container():
    """Reset the global service container (for testing)."""
    global _service_container
    _service_container = None


def get_app_config() -> AppConfig:
    """Dependency to get application configuration."""
    return get_service_container().get_config()


def get_message_handler_service() -> MessageHandlerService:
    """Dependency to get message handler service."""
    return get_service_container().get_message_handler()


def get_pdf_processing_service() -> PDFProcessingService:
    """Dependency to get PDF processing service."""
    return get_service_container().get_pdf_service()


def get_openai_analysis_service() -> EnhancedAIAnalysisService:
    """Dependency to get Enhanced AI analysis service."""
    return get_service_container().get_openai_service()


def get_twilio_response_service() -> TwilioResponseService:
    """Dependency to get Twilio response service."""
    return get_service_container().get_twilio_service()


def get_user_management_service() -> UserManagementService:
    """Dependency to get user management service."""
    return get_service_container().get_user_management_service()


def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service."""
    return get_service_container().get_analytics_service()


# Authentication Dependencies

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Authentication service instance
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate the token
    validation_result = await auth_service.validate_jwt_token(credentials.credentials)
    
    if not validation_result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=validation_result.error_message or "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not validation_result.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return validation_result.user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


def require_admin_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> User:
    """
    Dependency to require admin user role.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service instance
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    if not auth_service.require_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def require_analyst_or_admin_user(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> User:
    """
    Dependency to require analyst or admin user role.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service instance
        
    Returns:
        User: Current user with analyst or admin role
        
    Raises:
        HTTPException: If user is not analyst or admin
    """
    if not auth_service.require_analyst_or_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or admin privileges required"
        )
    
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Dependency to optionally get the current user (for endpoints that work with or without auth).
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        auth_service: Authentication service instance
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Validate the token
        validation_result = auth_service.validate_jwt_token(credentials.credentials)
        
        if validation_result.valid and validation_result.user:
            return validation_result.user
    except Exception:
        # Ignore authentication errors for optional auth
        pass
    
    return None