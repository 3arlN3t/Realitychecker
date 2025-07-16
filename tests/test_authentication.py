"""
Security tests for authentication and authorization system.

Tests JWT token management, password hashing, role-based access control,
and security vulnerabilities.
"""

import pytest
import jwt
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.services.authentication import (
    AuthenticationService, PasswordHasher, UserRole, 
    User, AuthResult, TokenValidation
)
from app.models.data_models import User as UserModel, UserRole as UserRoleModel
from app.dependencies import get_current_user, require_admin_user, require_analyst_or_admin_user


class TestPasswordHasher:
    """Test password hashing and validation utilities."""
    
    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "testpassword123"
        hashed = PasswordHasher.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original
        assert hashed.startswith('$2b$')  # bcrypt format
    
    def test_hash_password_validation(self):
        """Test password validation during hashing."""
        # Test empty password
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            PasswordHasher.hash_password("")
        
        # Test short password
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            PasswordHasher.hash_password("short")
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = PasswordHasher.hash_password(password)
        
        # Correct password should verify
        assert PasswordHasher.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert PasswordHasher.verify_password("wrongpassword", hashed) is False
    
    def test_verify_password_edge_cases(self):
        """Test password verification edge cases."""
        # Empty password
        assert PasswordHasher.verify_password("", "somehash") is False
        
        # Empty hash
        assert PasswordHasher.verify_password("password", "") is False
        
        # Both empty
        assert PasswordHasher.verify_password("", "") is False
        
        # Invalid hash format
        assert PasswordHasher.verify_password("password", "invalid_hash") is False
    
    def test_password_hashing_consistency(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify the same password
        assert PasswordHasher.verify_password(password, hash1) is True
        assert PasswordHasher.verify_password(password, hash2) is True


class TestAuthenticationService:
    """Test authentication service functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'test-secret-key',
            'JWT_EXPIRY_HOURS': '1',
            'JWT_REFRESH_EXPIRY_DAYS': '1',
            'ADMIN_USERNAME': 'testadmin',
            'ADMIN_PASSWORD': 'testpassword123',
            'ANALYST_USERNAME': 'testanalyst',
            'ANALYST_PASSWORD': 'testpassword456'
        })
        self.env_patcher.start()
        
        # Create fresh service instance
        self.auth_service = AuthenticationService()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.env_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success_admin(self):
        """Test successful admin user authentication."""
        result = await self.auth_service.authenticate_user("testadmin", "testpassword123")
        
        assert result.success is True
        assert result.user is not None
        assert result.user.username == "testadmin"
        assert result.user.role == UserRole.ADMIN
        assert result.token is not None
        assert result.refresh_token is not None
        assert result.expires_at is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success_analyst(self):
        """Test successful analyst user authentication."""
        result = await self.auth_service.authenticate_user("testanalyst", "testpassword456")
        
        assert result.success is True
        assert result.user is not None
        assert result.user.username == "testanalyst"
        assert result.user.role == UserRole.ANALYST
        assert result.token is not None
        assert result.refresh_token is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username."""
        result = await self.auth_service.authenticate_user("nonexistent", "password")
        
        assert result.success is False
        assert result.user is None
        assert result.token is None
        assert result.error_message == "Invalid username or password"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        result = await self.auth_service.authenticate_user("testadmin", "wrongpassword")
        
        assert result.success is False
        assert result.user is None
        assert result.token is None
        assert result.error_message == "Invalid username or password"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_empty_credentials(self):
        """Test authentication with empty credentials."""
        # Empty username
        result = await self.auth_service.authenticate_user("", "password")
        assert result.success is False
        assert result.error_message == "Username and password are required"
        
        # Empty password
        result = await self.auth_service.authenticate_user("username", "")
        assert result.success is False
        assert result.error_message == "Username and password are required"
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_success(self):
        """Test successful JWT token validation."""
        # First authenticate to get a token
        auth_result = await self.auth_service.authenticate_user("testadmin", "testpassword123")
        token = auth_result.token
        
        # Validate the token
        validation_result = await self.auth_service.validate_jwt_token(token)
        
        assert validation_result.valid is True
        assert validation_result.user is not None
        assert validation_result.user.username == "testadmin"
        assert validation_result.error_message is None
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_invalid(self):
        """Test JWT token validation with invalid token."""
        validation_result = await self.auth_service.validate_jwt_token("invalid_token")
        
        assert validation_result.valid is False
        assert validation_result.user is None
        assert validation_result.error_message == "Invalid token"
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_expired(self):
        """Test JWT token validation with expired token."""
        # Create an expired token manually
        now = datetime.now(timezone.utc)
        payload = {
            "username": "testadmin",
            "role": "admin",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # Expired 1 hour ago
            "type": "access"
        }
        
        expired_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
        
        validation_result = await self.auth_service.validate_jwt_token(expired_token)
        
        assert validation_result.valid is False
        assert validation_result.user is None
        assert validation_result.error_message == "Token has expired"
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        # First authenticate to get tokens
        auth_result = await self.auth_service.authenticate_user("testadmin", "testpassword123")
        refresh_token = auth_result.refresh_token
        
        # Refresh the token
        refresh_result = await self.auth_service.refresh_token(refresh_token)
        
        assert refresh_result.success is True
        assert refresh_result.user is not None
        assert refresh_result.token is not None
        assert refresh_result.refresh_token is not None
        assert refresh_result.token != auth_result.token  # Should be different
        assert refresh_result.refresh_token != refresh_token  # Should be different
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """Test token refresh with invalid refresh token."""
        refresh_result = await self.auth_service.refresh_token("invalid_refresh_token")
        
        assert refresh_result.success is False
        assert refresh_result.user is None
        assert refresh_result.error_message == "Invalid refresh token"
    
    @pytest.mark.asyncio
    async def test_logout_user_success(self):
        """Test successful user logout."""
        # First authenticate to get tokens
        auth_result = await self.auth_service.authenticate_user("testadmin", "testpassword123")
        refresh_token = auth_result.refresh_token
        
        # Logout user
        logout_success = await self.auth_service.logout_user(refresh_token)
        assert logout_success is True
        
        # Try to use the refresh token after logout (should fail)
        refresh_result = await self.auth_service.refresh_token(refresh_token)
        assert refresh_result.success is False
    
    def test_check_permission_admin(self):
        """Test permission checking for admin user."""
        admin_user = User(
            username="admin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Admin should have admin permissions
        assert self.auth_service.check_permission(admin_user, UserRole.ADMIN) is True
        
        # Admin should also have analyst permissions
        assert self.auth_service.check_permission(admin_user, UserRole.ANALYST) is True
    
    def test_check_permission_analyst(self):
        """Test permission checking for analyst user."""
        analyst_user = User(
            username="analyst",
            role=UserRole.ANALYST,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Analyst should have analyst permissions
        assert self.auth_service.check_permission(analyst_user, UserRole.ANALYST) is True
        
        # Analyst should NOT have admin permissions
        assert self.auth_service.check_permission(analyst_user, UserRole.ADMIN) is False
    
    def test_check_permission_inactive_user(self):
        """Test permission checking for inactive user."""
        inactive_user = User(
            username="inactive",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=False
        )
        
        # Inactive user should not have any permissions
        assert self.auth_service.check_permission(inactive_user, UserRole.ADMIN) is False
        assert self.auth_service.check_permission(inactive_user, UserRole.ANALYST) is False
    
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation by admin."""
        admin_user = User(
            username="testadmin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        result = await self.auth_service.create_user(
            "newuser", "newpassword123", UserRole.ANALYST, admin_user
        )
        
        assert result.success is True
        assert result.user is not None
        assert result.user.username == "newuser"
        assert result.user.role == UserRole.ANALYST
    
    @pytest.mark.asyncio
    async def test_create_user_non_admin(self):
        """Test user creation by non-admin user (should fail)."""
        analyst_user = User(
            username="testanalyst",
            role=UserRole.ANALYST,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        result = await self.auth_service.create_user(
            "newuser", "newpassword123", UserRole.ANALYST, analyst_user
        )
        
        assert result.success is False
        assert result.error_message == "Only administrators can create users"
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username."""
        admin_user = User(
            username="testadmin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        result = await self.auth_service.create_user(
            "testadmin", "newpassword123", UserRole.ANALYST, admin_user
        )
        
        assert result.success is False
        assert result.error_message == "Username already exists"
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self):
        """Test successful user deactivation by admin."""
        admin_user = User(
            username="testadmin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        success = await self.auth_service.deactivate_user("testanalyst", admin_user)
        assert success is True
        
        # Try to authenticate deactivated user (should fail)
        auth_result = await self.auth_service.authenticate_user("testanalyst", "testpassword456")
        assert auth_result.success is False
        assert auth_result.error_message == "User account is inactive"
    
    @pytest.mark.asyncio
    async def test_deactivate_user_self(self):
        """Test user trying to deactivate themselves (should fail)."""
        admin_user = User(
            username="testadmin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        success = await self.auth_service.deactivate_user("testadmin", admin_user)
        assert success is False


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def setup_method(self):
        """Set up test environment."""
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key',
            'TWILIO_ACCOUNT_SID': 'AC123',
            'TWILIO_AUTH_TOKEN': 'test-token',
            'TWILIO_PHONE_NUMBER': '+1234567890',
            'JWT_SECRET_KEY': 'test-secret-key',
            'ADMIN_USERNAME': 'testadmin',
            'ADMIN_PASSWORD': 'testpassword123'
        })
        self.env_patcher.start()
        
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up test environment."""
        self.env_patcher.stop()
    
    def test_login_success(self):
        """Test successful login via API."""
        response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "admin"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_validation_error(self):
        """Test login with validation errors."""
        # Missing password
        response = self.client.post("/auth/login", json={
            "username": "testadmin"
        })
        assert response.status_code == 422
        
        # Short username
        response = self.client.post("/auth/login", json={
            "username": "ab",
            "password": "testpassword123"
        })
        assert response.status_code == 422
        
        # Short password
        response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "short"
        })
        assert response.status_code == 422
    
    def test_get_current_user_success(self):
        """Test getting current user info with valid token."""
        # First login to get token
        login_response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user info
        response = self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"
        assert data["is_active"] is True
    
    def test_get_current_user_no_token(self):
        """Test getting current user info without token."""
        response = self.client.get("/auth/me")
        
        assert response.status_code == 403  # No credentials provided
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user info with invalid token."""
        response = self.client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token"
        })
        
        assert response.status_code == 401
    
    def test_create_user_admin_success(self):
        """Test creating user as admin."""
        # First login as admin
        login_response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Create new user
        response = self.client.post("/auth/users", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "newpassword123",
                "role": "analyst"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "newuser"
        assert data["role"] == "analyst"
        assert data["is_active"] is True
    
    def test_create_user_invalid_role(self):
        """Test creating user with invalid role."""
        # First login as admin
        login_response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Try to create user with invalid role
        response = self.client.post("/auth/users", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "newpassword123",
                "role": "invalid_role"
            }
        )
        
        assert response.status_code == 400
    
    def test_auth_stats_admin_success(self):
        """Test getting auth stats as admin."""
        # First login as admin
        login_response = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Get auth stats
        response = self.client.get("/auth/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["inactive_users"], int)


class TestSecurityVulnerabilities:
    """Test for common security vulnerabilities."""
    
    def setup_method(self):
        """Set up test environment."""
        self.env_patcher = patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'test-secret-key',
            'ADMIN_USERNAME': 'testadmin',
            'ADMIN_PASSWORD': 'testpassword123'
        })
        self.env_patcher.start()
        
        self.auth_service = AuthenticationService()
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up test environment."""
        self.env_patcher.stop()
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection in username."""
        # Note: We're using in-memory storage, but test the principle
        malicious_usernames = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --"
        ]
        
        for username in malicious_usernames:
            response = self.client.post("/auth/login", json={
                "username": username,
                "password": "testpassword123"
            })
            # Should not crash and should return 401 (not found)
            assert response.status_code == 401
    
    def test_timing_attack_protection(self):
        """Test that authentication timing doesn't leak information."""
        import time
        
        # Test with non-existent user
        start_time = time.time()
        response1 = self.client.post("/auth/login", json={
            "username": "nonexistent_user_12345",
            "password": "testpassword123"
        })
        time1 = time.time() - start_time
        
        # Test with existing user but wrong password
        start_time = time.time()
        response2 = self.client.post("/auth/login", json={
            "username": "testadmin",
            "password": "wrongpassword"
        })
        time2 = time.time() - start_time
        
        # Both should return 401
        assert response1.status_code == 401
        assert response2.status_code == 401
        
        # Timing difference should be minimal (within reasonable bounds)
        # This is a basic check - in production, you'd want more sophisticated timing analysis
        time_diff = abs(time1 - time2)
        assert time_diff < 0.5  # Should complete within similar timeframes
    
    def test_jwt_secret_key_security(self):
        """Test JWT secret key security."""
        # Test that tokens signed with different keys are rejected
        auth_service_1 = AuthenticationService()
        
        # Create token with first service
        auth_result = auth_service_1.authenticate_user("testadmin", "testpassword123")
        token = auth_result.token
        
        # Try to validate with service using different secret
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'different-secret-key'}):
            auth_service_2 = AuthenticationService()
            validation_result = auth_service_2.validate_jwt_token(token)
            
            assert validation_result.valid is False
            assert "Invalid token" in validation_result.error_message
    
    def test_token_tampering_protection(self):
        """Test protection against token tampering."""
        # Get a valid token
        auth_result = self.auth_service.authenticate_user("testadmin", "testpassword123")
        valid_token = auth_result.token
        
        # Tamper with the token
        tampered_tokens = [
            valid_token[:-5] + "XXXXX",  # Change last 5 characters
            valid_token + "extra",        # Add extra characters
            valid_token[5:],             # Remove first 5 characters
            "Bearer " + valid_token,     # Add Bearer prefix
        ]
        
        for tampered_token in tampered_tokens:
            validation_result = self.auth_service.validate_jwt_token(tampered_token)
            assert validation_result.valid is False
    
    def test_password_brute_force_protection(self):
        """Test basic brute force protection (rate limiting would be handled by middleware)."""
        # Multiple failed attempts should still return consistent error messages
        failed_attempts = []
        
        for i in range(5):
            response = self.client.post("/auth/login", json={
                "username": "testadmin",
                "password": f"wrongpassword{i}"
            })
            failed_attempts.append(response.json())
        
        # All attempts should return the same error structure
        for attempt in failed_attempts:
            assert "detail" in attempt
            # Should not reveal whether user exists or not
            assert "Invalid username or password" in str(attempt["detail"]) or "Authentication failed" in str(attempt["detail"])
    
    def test_session_fixation_protection(self):
        """Test protection against session fixation attacks."""
        # Each login should generate a new token
        auth_result_1 = self.auth_service.authenticate_user("testadmin", "testpassword123")
        auth_result_2 = self.auth_service.authenticate_user("testadmin", "testpassword123")
        
        # Tokens should be different
        assert auth_result_1.token != auth_result_2.token
        assert auth_result_1.refresh_token != auth_result_2.refresh_token
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_protection(self):
        """Test protection against privilege escalation."""
        # Create an analyst user
        admin_user = User(
            username="testadmin",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        create_result = await self.auth_service.create_user(
            "testanalyst", "testpassword123", UserRole.ANALYST, admin_user
        )
        assert create_result.success is True
        
        # Analyst should not be able to create admin users
        analyst_user = User(
            username="testanalyst",
            role=UserRole.ANALYST,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        escalation_attempt = await self.auth_service.create_user(
            "malicious_admin", "password123", UserRole.ADMIN, analyst_user
        )
        
        assert escalation_attempt.success is False
        assert "Only administrators can create users" in escalation_attempt.error_message


if __name__ == "__main__":
    pytest.main([__file__])