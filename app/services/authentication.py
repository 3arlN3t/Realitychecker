"""
Authentication and authorization service for the Reality Checker application.

This module provides JWT-based authentication, password hashing, and role-based
access control for the admin dashboard.
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.utils.logging import get_logger

logger = get_logger(__name__)


class UserRole(Enum):
    """Enumeration for user roles in the system."""
    ADMIN = "admin"
    ANALYST = "analyst"


@dataclass
class User:
    """
    Dataclass representing a system user.
    
    Contains user information including credentials and role.
    """
    username: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not isinstance(self.role, UserRole):
            raise ValueError("Role must be a UserRole enum")


@dataclass
class AuthResult:
    """
    Dataclass representing authentication result.
    
    Contains authentication status and user information.
    """
    success: bool
    user: Optional[User] = None
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate auth result data after initialization."""
        if self.success and not self.user:
            raise ValueError("User must be provided for successful authentication")
        if self.success and not self.token:
            raise ValueError("Token must be provided for successful authentication")
        if not self.success and not self.error_message:
            raise ValueError("Error message must be provided for failed authentication")


@dataclass
class TokenValidation:
    """
    Dataclass representing token validation result.
    
    Contains validation status and decoded token information.
    """
    valid: bool
    user: Optional[User] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate token validation data after initialization."""
        if self.valid and not self.user:
            raise ValueError("User must be provided for valid token")
        if not self.valid and not self.error_message:
            raise ValueError("Error message must be provided for invalid token")


class PasswordHasher:
    """
    Utility class for password hashing and validation.
    
    Uses bcrypt for secure password hashing.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            str: Hashed password
            
        Raises:
            ValueError: If password is empty or too short
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            bool: True if password matches hash
        """
        if not password or not hashed_password:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False


class AuthenticationService:
    """
    Service class for handling authentication and authorization.
    
    Provides JWT token management, user authentication, and role-based access control.
    """
    
    def __init__(self):
        """Initialize the authentication service."""
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.token_expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        self.refresh_token_expiry_days = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))
        
        # In-memory user store (in production, this would be a database)
        self._users: Dict[str, Dict[str, Any]] = {}
        self._refresh_tokens: Dict[str, str] = {}  # refresh_token -> username
        
        # Initialize default admin user
        self._initialize_default_users()
        
        logger.info("Authentication service initialized")
    
    def _initialize_default_users(self) -> None:
        """Initialize default users from environment variables."""
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        # Create default admin user
        self._users[admin_username] = {
            "username": admin_username,
            "password_hash": PasswordHasher.hash_password(admin_password),
            "role": UserRole.ADMIN,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "is_active": True
        }
        
        # Create default analyst user if specified
        analyst_username = os.getenv("ANALYST_USERNAME")
        analyst_password = os.getenv("ANALYST_PASSWORD")
        
        if analyst_username and analyst_password:
            self._users[analyst_username] = {
                "username": analyst_username,
                "password_hash": PasswordHasher.hash_password(analyst_password),
                "role": UserRole.ANALYST,
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "is_active": True
            }
        
        logger.info(f"Initialized {len(self._users)} default users")
    
    async def authenticate_user(self, username: str, password: str) -> AuthResult:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            AuthResult: Authentication result with user info and tokens
        """
        try:
            # Input validation
            if not username or not password:
                return AuthResult(
                    success=False,
                    error_message="Username and password are required"
                )
            
            # Check if user exists
            user_data = self._users.get(username)
            if not user_data:
                logger.warning(f"Authentication failed: user not found - {username}")
                return AuthResult(
                    success=False,
                    error_message="Invalid username or password"
                )
            
            # Check if user is active
            if not user_data.get("is_active", True):
                logger.warning(f"Authentication failed: user inactive - {username}")
                return AuthResult(
                    success=False,
                    error_message="User account is inactive"
                )
            
            # Verify password
            if not PasswordHasher.verify_password(password, user_data["password_hash"]):
                logger.warning(f"Authentication failed: invalid password - {username}")
                return AuthResult(
                    success=False,
                    error_message="Invalid username or password"
                )
            
            # Create user object
            user = User(
                username=user_data["username"],
                role=user_data["role"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"],
                is_active=user_data["is_active"]
            )
            
            # Generate tokens
            token = self._generate_jwt_token(user)
            refresh_token = self._generate_refresh_token(user)
            
            # Update last login
            self._users[username]["last_login"] = datetime.now(timezone.utc)
            
            # Store refresh token
            self._refresh_tokens[refresh_token] = username
            
            logger.info(f"User authenticated successfully: {username}")
            
            return AuthResult(
                success=True,
                user=user,
                token=token,
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours)
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(
                success=False,
                error_message="Authentication service error"
            )
    
    def _generate_jwt_token(self, user: User) -> str:
        """
        Generate a JWT token for the user.
        
        Args:
            user: User to generate token for
            
        Returns:
            str: JWT token
        """
        now = datetime.now(timezone.utc)
        payload = {
            "username": user.username,
            "role": user.role.value,
            "iat": now,
            "exp": now + timedelta(hours=self.token_expiry_hours),
            "type": "access"
        }
        
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    def _generate_refresh_token(self, user: User) -> str:
        """
        Generate a refresh token for the user.
        
        Args:
            user: User to generate refresh token for
            
        Returns:
            str: Refresh token
        """
        now = datetime.now(timezone.utc)
        payload = {
            "username": user.username,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expiry_days),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    async def validate_jwt_token(self, token: str) -> TokenValidation:
        """
        Validate a JWT token and return user information.
        
        Args:
            token: JWT token to validate
            
        Returns:
            TokenValidation: Validation result with user info
        """
        try:
            if not token:
                return TokenValidation(
                    valid=False,
                    error_message="Token is required"
                )
            
            # Decode token
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "access":
                return TokenValidation(
                    valid=False,
                    error_message="Invalid token type"
                )
            
            # Get user information
            username = payload.get("username")
            if not username:
                return TokenValidation(
                    valid=False,
                    error_message="Invalid token payload"
                )
            
            # Check if user still exists and is active
            user_data = self._users.get(username)
            if not user_data or not user_data.get("is_active", True):
                return TokenValidation(
                    valid=False,
                    error_message="User not found or inactive"
                )
            
            # Create user object
            user = User(
                username=user_data["username"],
                role=user_data["role"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"],
                is_active=user_data["is_active"]
            )
            
            return TokenValidation(
                valid=True,
                user=user,
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            )
            
        except jwt.ExpiredSignatureError:
            return TokenValidation(
                valid=False,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return TokenValidation(
                valid=False,
                error_message="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return TokenValidation(
                valid=False,
                error_message="Token validation error"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            AuthResult: New authentication result with fresh tokens
        """
        try:
            if not refresh_token:
                return AuthResult(
                    success=False,
                    error_message="Refresh token is required"
                )
            
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                return AuthResult(
                    success=False,
                    error_message="Invalid refresh token type"
                )
            
            # Get username from token
            username = payload.get("username")
            if not username:
                return AuthResult(
                    success=False,
                    error_message="Invalid refresh token payload"
                )
            
            # Check if refresh token is still valid in our store
            if self._refresh_tokens.get(refresh_token) != username:
                return AuthResult(
                    success=False,
                    error_message="Refresh token not found or expired"
                )
            
            # Get user data
            user_data = self._users.get(username)
            if not user_data or not user_data.get("is_active", True):
                return AuthResult(
                    success=False,
                    error_message="User not found or inactive"
                )
            
            # Create user object
            user = User(
                username=user_data["username"],
                role=user_data["role"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"],
                is_active=user_data["is_active"]
            )
            
            # Generate new tokens
            new_token = self._generate_jwt_token(user)
            new_refresh_token = self._generate_refresh_token(user)
            
            # Remove old refresh token and store new one
            del self._refresh_tokens[refresh_token]
            self._refresh_tokens[new_refresh_token] = username
            
            logger.info(f"Token refreshed successfully: {username}")
            
            return AuthResult(
                success=True,
                user=user,
                token=new_token,
                refresh_token=new_refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours)
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_message="Refresh token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return AuthResult(
                success=False,
                error_message="Invalid refresh token"
            )
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(
                success=False,
                error_message="Token refresh error"
            )
    
    async def logout_user(self, token: str) -> bool:
        """
        Logout a user by invalidating their tokens.
        
        Args:
            token: Access token or refresh token to invalidate
            
        Returns:
            bool: True if logout was successful
        """
        try:
            # Try to decode the token to get username
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret_key,
                    algorithms=[self.jwt_algorithm],
                    options={"verify_exp": False}  # Don't verify expiration for logout
                )
                username = payload.get("username")
            except jwt.InvalidTokenError:
                # Token is invalid, but we'll still try to clean up
                username = None
            
            # Remove all refresh tokens for this user
            if username:
                tokens_to_remove = [
                    rt for rt, user in self._refresh_tokens.items()
                    if user == username
                ]
                for rt in tokens_to_remove:
                    del self._refresh_tokens[rt]
                
                logger.info(f"User logged out successfully: {username}")
            
            # Also try to remove the specific token if it's a refresh token
            if token in self._refresh_tokens:
                del self._refresh_tokens[token]
            
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """
        Check if a user has the required role permission.
        
        Args:
            user: User to check permissions for
            required_role: Required role for the operation
            
        Returns:
            bool: True if user has required permission
        """
        if not user or not user.is_active:
            return False
        
        # Admin role has access to everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Check specific role requirements
        return user.role == required_role
    
    def require_admin(self, user: User) -> bool:
        """
        Check if user has admin role.
        
        Args:
            user: User to check
            
        Returns:
            bool: True if user is admin
        """
        return self.check_permission(user, UserRole.ADMIN)
    
    def require_analyst_or_admin(self, user: User) -> bool:
        """
        Check if user has analyst or admin role.
        
        Args:
            user: User to check
            
        Returns:
            bool: True if user is analyst or admin
        """
        return (self.check_permission(user, UserRole.ANALYST) or 
                self.check_permission(user, UserRole.ADMIN))
    
    async def create_user(self, username: str, password: str, role: UserRole, 
                         created_by: User) -> AuthResult:
        """
        Create a new user (admin only operation).
        
        Args:
            username: Username for new user
            password: Password for new user
            role: Role for new user
            created_by: User creating the new user (must be admin)
            
        Returns:
            AuthResult: Result of user creation
        """
        try:
            # Check if creator has admin permissions
            if not self.require_admin(created_by):
                return AuthResult(
                    success=False,
                    error_message="Only administrators can create users"
                )
            
            # Validate input
            if not username or len(username) < 3:
                return AuthResult(
                    success=False,
                    error_message="Username must be at least 3 characters long"
                )
            
            if not password or len(password) < 8:
                return AuthResult(
                    success=False,
                    error_message="Password must be at least 8 characters long"
                )
            
            # Check if user already exists
            if username in self._users:
                return AuthResult(
                    success=False,
                    error_message="Username already exists"
                )
            
            # Create new user
            self._users[username] = {
                "username": username,
                "password_hash": PasswordHasher.hash_password(password),
                "role": role,
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "is_active": True
            }
            
            # Create user object
            user = User(
                username=username,
                role=role,
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            logger.info(f"User created successfully: {username} by {created_by.username}")
            
            return AuthResult(
                success=True,
                user=user
            )
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return AuthResult(
                success=False,
                error_message="User creation error"
            )
    
    async def deactivate_user(self, username: str, deactivated_by: User) -> bool:
        """
        Deactivate a user (admin only operation).
        
        Args:
            username: Username to deactivate
            deactivated_by: User performing the deactivation (must be admin)
            
        Returns:
            bool: True if deactivation was successful
        """
        try:
            # Check if deactivator has admin permissions
            if not self.require_admin(deactivated_by):
                logger.warning(f"Unauthorized user deactivation attempt by {deactivated_by.username}")
                return False
            
            # Check if user exists
            if username not in self._users:
                return False
            
            # Don't allow deactivating yourself
            if username == deactivated_by.username:
                logger.warning(f"User attempted to deactivate themselves: {username}")
                return False
            
            # Deactivate user
            self._users[username]["is_active"] = False
            
            # Remove all refresh tokens for this user
            tokens_to_remove = [
                rt for rt, user in self._refresh_tokens.items()
                if user == username
            ]
            for rt in tokens_to_remove:
                del self._refresh_tokens[rt]
            
            logger.info(f"User deactivated: {username} by {deactivated_by.username}")
            return True
            
        except Exception as e:
            logger.error(f"User deactivation error: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self._users)
    
    def get_active_user_count(self) -> int:
        """Get number of active users."""
        return sum(1 for user in self._users.values() if user.get("is_active", True))


# Global authentication service instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get the global authentication service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service