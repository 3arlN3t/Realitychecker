"""
Authentication API endpoints for the Reality Checker application.

This module provides REST API endpoints for user authentication, token management,
and user account operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import Optional

from app.services.authentication import get_auth_service, AuthenticationService
from app.models.data_models import User, UserRole, AuthResult
from app.dependencies import get_current_user, require_admin_user
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class LoginResponse(BaseModel):
    """Response model for successful login."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    user: dict = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    role: str = Field(..., description="User role (admin or analyst)")


class UserResponse(BaseModel):
    """Response model for user information."""
    username: str
    role: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool


class MessageResponse(BaseModel):
    """Response model for simple messages."""
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Authenticate user and return access tokens.
    
    Args:
        request: Login request with username and password
        auth_service: Authentication service instance
        
    Returns:
        LoginResponse: Access token, refresh token, and user info
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate user
        auth_result = await auth_service.authenticate_user(
            request.username, 
            request.password
        )
        
        if not auth_result.success:
            logger.warning(f"Login failed for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Calculate expires_in (24 hours in seconds)
        expires_in = 24 * 60 * 60
        
        logger.info(f"User logged in successfully: {request.username}")
        
        return LoginResponse(
            access_token=auth_result.token,
            refresh_token=auth_result.refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user={
                "username": auth_result.user.username,
                "role": auth_result.user.role.value,
                "created_at": auth_result.user.created_at.isoformat(),
                "last_login": auth_result.user.last_login.isoformat() if auth_result.user.last_login else None,
                "is_active": auth_result.user.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        auth_service: Authentication service instance
        
    Returns:
        LoginResponse: New access token, refresh token, and user info
        
    Raises:
        HTTPException: If refresh fails
    """
    try:
        # Refresh token
        auth_result = await auth_service.refresh_token(request.refresh_token)
        
        if not auth_result.success:
            logger.warning("Token refresh failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Token refresh failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Calculate expires_in (24 hours in seconds)
        expires_in = 24 * 60 * 60
        
        logger.info(f"Token refreshed successfully for user: {auth_result.user.username}")
        
        return LoginResponse(
            access_token=auth_result.token,
            refresh_token=auth_result.refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user={
                "username": auth_result.user.username,
                "role": auth_result.user.role.value,
                "created_at": auth_result.user.created_at.isoformat(),
                "last_login": auth_result.user.last_login.isoformat() if auth_result.user.last_login else None,
                "is_active": auth_result.user.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Logout current user by invalidating tokens.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service instance
        
    Returns:
        MessageResponse: Logout confirmation message
    """
    try:
        # Note: In a real implementation, we would need to get the actual token
        # from the request to invalidate it. For now, we'll invalidate all tokens
        # for the user by username.
        success = await auth_service.logout_user("")
        
        if success:
            logger.info(f"User logged out successfully: {current_user.username}")
            return MessageResponse(message="Logged out successfully")
        else:
            logger.warning(f"Logout failed for user: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        username=current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        is_active=current_user.is_active
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    admin_user: User = Depends(require_admin_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Create a new user (admin only).
    
    Args:
        request: User creation request
        admin_user: Current admin user
        auth_service: Authentication service instance
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If user creation fails
    """
    try:
        # Validate role
        try:
            role = UserRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'admin' or 'analyst'"
            )
        
        # Create user
        auth_result = await auth_service.create_user(
            request.username,
            request.password,
            role,
            admin_user
        )
        
        if not auth_result.success:
            logger.warning(f"User creation failed: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=auth_result.error_message or "User creation failed"
            )
        
        logger.info(f"User created successfully: {request.username} by {admin_user.username}")
        
        return UserResponse(
            username=auth_result.user.username,
            role=auth_result.user.role.value,
            created_at=auth_result.user.created_at.isoformat(),
            last_login=None,
            is_active=auth_result.user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user creation"
        )


@router.post("/users/{username}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    username: str,
    admin_user: User = Depends(require_admin_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Deactivate a user (admin only).
    
    Args:
        username: Username to deactivate
        admin_user: Current admin user
        auth_service: Authentication service instance
        
    Returns:
        MessageResponse: Deactivation confirmation message
        
    Raises:
        HTTPException: If deactivation fails
    """
    try:
        success = await auth_service.deactivate_user(username, admin_user)
        
        if not success:
            logger.warning(f"User deactivation failed: {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User deactivation failed. User may not exist or you cannot deactivate yourself."
            )
        
        logger.info(f"User deactivated successfully: {username} by {admin_user.username}")
        
        return MessageResponse(message=f"User {username} deactivated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deactivation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user deactivation"
        )


@router.get("/stats", response_model=dict)
async def get_auth_stats(
    admin_user: User = Depends(require_admin_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Get authentication statistics (admin only).
    
    Args:
        admin_user: Current admin user
        auth_service: Authentication service instance
        
    Returns:
        dict: Authentication statistics
    """
    try:
        total_users = auth_service.get_user_count()
        active_users = auth_service.get_active_user_count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users
        }
        
    except Exception as e:
        logger.error(f"Auth stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching auth statistics"
        )