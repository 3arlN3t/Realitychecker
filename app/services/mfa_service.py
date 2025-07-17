"""
Multi-Factor Authentication (MFA) service for the Reality Checker application.

This service provides TOTP-based two-factor authentication capabilities including:
- Secret generation and QR code creation
- TOTP token verification
- Backup codes generation and management
- MFA enrollment and management
"""

import logging
import secrets
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import base64
import io

import pyotp
import qrcode
from qrcode.image.pil import PilImage

from app.models.data_models import AppConfig, User
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.error_tracking import get_error_tracker, AlertSeverity


logger = get_logger(__name__)


@dataclass
class MFAEnrollmentData:
    """Data structure for MFA enrollment."""
    secret: str
    qr_code_data: str
    backup_codes: List[str]
    enrollment_token: str


@dataclass
class MFAVerificationResult:
    """Result of MFA verification."""
    valid: bool
    error_message: Optional[str] = None
    backup_code_used: bool = False
    remaining_backup_codes: int = 0


@dataclass
class MFAStatus:
    """MFA status for a user."""
    enabled: bool
    enrolled: bool
    backup_codes_remaining: int
    last_used: Optional[datetime] = None
    recovery_codes_generated: int = 0


class MFAService:
    """
    Service for managing Multi-Factor Authentication.
    
    Provides TOTP-based 2FA with backup codes and recovery mechanisms.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the MFA service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.issuer = getattr(config, 'mfa_issuer', 'Reality-Checker')
        self.backup_codes_count = getattr(config, 'mfa_backup_codes_count', 10)
        self.totp_window = getattr(config, 'mfa_totp_window', 1)  # 30-second windows
        self.enrollment_token_expiry = getattr(config, 'mfa_enrollment_token_expiry_minutes', 10)
        
        # In-memory storage for demo purposes
        # In production, this should be stored in a database
        self.user_mfa_data: Dict[str, Dict[str, Any]] = {}
        self.enrollment_tokens: Dict[str, Dict[str, Any]] = {}
        self.used_backup_codes: Dict[str, set] = {}
        
        logger.info("MFA service initialized")
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.
        
        Returns:
            str: Base32-encoded secret
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """
        Generate QR code for TOTP setup.
        
        Args:
            user: User object
            secret: TOTP secret
            
        Returns:
            str: Base64-encoded QR code image
        """
        correlation_id = get_correlation_id()
        
        try:
            # Create TOTP URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user.username,
                issuer_name=self.issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            log_with_context(
                logger,
                logging.INFO,
                "QR code generated for MFA setup",
                username=user.username,
                correlation_id=correlation_id
            )
            
            return img_data
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate QR code",
                username=user.username,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    def generate_backup_codes(self, count: Optional[int] = None) -> List[str]:
        """
        Generate backup codes for MFA recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List[str]: List of backup codes
        """
        if count is None:
            count = self.backup_codes_count
        
        backup_codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)
        
        return backup_codes
    
    async def start_mfa_enrollment(self, user: User) -> MFAEnrollmentData:
        """
        Start MFA enrollment process for a user.
        
        Args:
            user: User to enroll
            
        Returns:
            MFAEnrollmentData: Enrollment data including secret and QR code
        """
        correlation_id = get_correlation_id()
        
        try:
            # Generate secret and backup codes
            secret = self.generate_secret()
            backup_codes = self.generate_backup_codes()
            
            # Generate QR code
            qr_code_data = self.generate_qr_code(user, secret)
            
            # Create enrollment token
            enrollment_token = secrets.token_urlsafe(32)
            
            # Store enrollment data temporarily
            self.enrollment_tokens[enrollment_token] = {
                'username': user.username,
                'secret': secret,
                'backup_codes': backup_codes,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(minutes=self.enrollment_token_expiry)
            }
            
            log_with_context(
                logger,
                logging.INFO,
                "MFA enrollment started",
                username=user.username,
                backup_codes_count=len(backup_codes),
                correlation_id=correlation_id
            )
            
            return MFAEnrollmentData(
                secret=secret,
                qr_code_data=qr_code_data,
                backup_codes=backup_codes,
                enrollment_token=enrollment_token
            )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to start MFA enrollment",
                username=user.username,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def complete_mfa_enrollment(self, enrollment_token: str, totp_code: str) -> bool:
        """
        Complete MFA enrollment by verifying TOTP code.
        
        Args:
            enrollment_token: Enrollment token from start_mfa_enrollment
            totp_code: TOTP code from authenticator app
            
        Returns:
            bool: True if enrollment completed successfully
        """
        correlation_id = get_correlation_id()
        
        try:
            # Validate enrollment token
            if enrollment_token not in self.enrollment_tokens:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Invalid enrollment token",
                    token=enrollment_token[:8] + "...",
                    correlation_id=correlation_id
                )
                return False
            
            enrollment_data = self.enrollment_tokens[enrollment_token]
            
            # Check if token is expired
            if datetime.utcnow() > enrollment_data['expires_at']:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Enrollment token expired",
                    username=enrollment_data['username'],
                    correlation_id=correlation_id
                )
                del self.enrollment_tokens[enrollment_token]
                return False
            
            # Verify TOTP code
            secret = enrollment_data['secret']
            if not self._verify_totp_code(secret, totp_code):
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Invalid TOTP code during enrollment",
                    username=enrollment_data['username'],
                    correlation_id=correlation_id
                )
                return False
            
            # Complete enrollment
            username = enrollment_data['username']
            self.user_mfa_data[username] = {
                'secret': secret,
                'backup_codes': set(enrollment_data['backup_codes']),
                'enabled': True,
                'enrolled': True,
                'enrolled_at': datetime.utcnow(),
                'last_used': None,
                'recovery_codes_generated': 1
            }
            
            # Initialize used backup codes set
            self.used_backup_codes[username] = set()
            
            # Clean up enrollment token
            del self.enrollment_tokens[enrollment_token]
            
            log_with_context(
                logger,
                logging.INFO,
                "MFA enrollment completed successfully",
                username=username,
                correlation_id=correlation_id
            )
            
            return True
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to complete MFA enrollment",
                error=str(e),
                correlation_id=correlation_id
            )
            return False
    
    def _verify_totp_code(self, secret: str, totp_code: str) -> bool:
        """
        Verify TOTP code against secret.
        
        Args:
            secret: TOTP secret
            totp_code: Code to verify
            
        Returns:
            bool: True if code is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(totp_code, valid_window=self.totp_window)
        except Exception:
            return False
    
    def _verify_backup_code(self, username: str, backup_code: str) -> bool:
        """
        Verify backup code for user.
        
        Args:
            username: Username
            backup_code: Backup code to verify
            
        Returns:
            bool: True if backup code is valid and unused
        """
        if username not in self.user_mfa_data:
            return False
        
        user_data = self.user_mfa_data[username]
        used_codes = self.used_backup_codes.get(username, set())
        
        # Check if code exists and hasn't been used
        if backup_code in user_data['backup_codes'] and backup_code not in used_codes:
            # Mark code as used
            used_codes.add(backup_code)
            self.used_backup_codes[username] = used_codes
            return True
        
        return False
    
    async def verify_mfa_token(self, user: User, token: str) -> MFAVerificationResult:
        """
        Verify MFA token (TOTP or backup code).
        
        Args:
            user: User object
            token: TOTP code or backup code
            
        Returns:
            MFAVerificationResult: Verification result
        """
        correlation_id = get_correlation_id()
        username = user.username
        
        try:
            # Check if user has MFA enabled
            if username not in self.user_mfa_data:
                log_with_context(
                    logger,
                    logging.WARNING,
                    "MFA verification attempted for user without MFA",
                    username=username,
                    correlation_id=correlation_id
                )
                return MFAVerificationResult(
                    valid=False,
                    error_message="MFA not enabled for this user"
                )
            
            user_data = self.user_mfa_data[username]
            
            if not user_data['enabled']:
                return MFAVerificationResult(
                    valid=False,
                    error_message="MFA is disabled for this user"
                )
            
            # First try TOTP verification
            if self._verify_totp_code(user_data['secret'], token):
                # Update last used timestamp
                user_data['last_used'] = datetime.utcnow()
                
                # Calculate remaining backup codes
                used_codes = len(self.used_backup_codes.get(username, set()))
                remaining_codes = len(user_data['backup_codes']) - used_codes
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "MFA TOTP verification successful",
                    username=username,
                    correlation_id=correlation_id
                )
                
                return MFAVerificationResult(
                    valid=True,
                    backup_code_used=False,
                    remaining_backup_codes=remaining_codes
                )
            
            # If TOTP fails, try backup code
            if self._verify_backup_code(username, token):
                # Update last used timestamp
                user_data['last_used'] = datetime.utcnow()
                
                # Calculate remaining backup codes
                used_codes = len(self.used_backup_codes.get(username, set()))
                remaining_codes = len(user_data['backup_codes']) - used_codes
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "MFA backup code verification successful",
                    username=username,
                    remaining_backup_codes=remaining_codes,
                    correlation_id=correlation_id
                )
                
                return MFAVerificationResult(
                    valid=True,
                    backup_code_used=True,
                    remaining_backup_codes=remaining_codes
                )
            
            # Both TOTP and backup code failed
            log_with_context(
                logger,
                logging.WARNING,
                "MFA verification failed",
                username=username,
                correlation_id=correlation_id
            )
            
            return MFAVerificationResult(
                valid=False,
                error_message="Invalid MFA token"
            )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "MFA verification error",
                username=username,
                error=str(e),
                correlation_id=correlation_id
            )
            return MFAVerificationResult(
                valid=False,
                error_message="MFA verification failed"
            )
    
    async def get_mfa_status(self, user: User) -> MFAStatus:
        """
        Get MFA status for a user.
        
        Args:
            user: User object
            
        Returns:
            MFAStatus: Current MFA status
        """
        username = user.username
        
        if username not in self.user_mfa_data:
            return MFAStatus(
                enabled=False,
                enrolled=False,
                backup_codes_remaining=0
            )
        
        user_data = self.user_mfa_data[username]
        used_codes = len(self.used_backup_codes.get(username, set()))
        remaining_codes = len(user_data['backup_codes']) - used_codes
        
        return MFAStatus(
            enabled=user_data['enabled'],
            enrolled=user_data['enrolled'],
            backup_codes_remaining=remaining_codes,
            last_used=user_data.get('last_used'),
            recovery_codes_generated=user_data.get('recovery_codes_generated', 0)
        )
    
    async def disable_mfa(self, user: User) -> bool:
        """
        Disable MFA for a user.
        
        Args:
            user: User object
            
        Returns:
            bool: True if MFA was disabled successfully
        """
        correlation_id = get_correlation_id()
        username = user.username
        
        try:
            if username in self.user_mfa_data:
                self.user_mfa_data[username]['enabled'] = False
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "MFA disabled for user",
                    username=username,
                    correlation_id=correlation_id
                )
                
                return True
            
            return False
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to disable MFA",
                username=username,
                error=str(e),
                correlation_id=correlation_id
            )
            return False
    
    async def regenerate_backup_codes(self, user: User) -> List[str]:
        """
        Regenerate backup codes for a user.
        
        Args:
            user: User object
            
        Returns:
            List[str]: New backup codes
        """
        correlation_id = get_correlation_id()
        username = user.username
        
        try:
            if username not in self.user_mfa_data:
                raise ValueError("MFA not enabled for this user")
            
            # Generate new backup codes
            new_backup_codes = self.generate_backup_codes()
            
            # Update user data
            self.user_mfa_data[username]['backup_codes'] = set(new_backup_codes)
            self.user_mfa_data[username]['recovery_codes_generated'] += 1
            
            # Clear used backup codes
            self.used_backup_codes[username] = set()
            
            log_with_context(
                logger,
                logging.INFO,
                "Backup codes regenerated",
                username=username,
                new_codes_count=len(new_backup_codes),
                correlation_id=correlation_id
            )
            
            return new_backup_codes
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to regenerate backup codes",
                username=username,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def is_mfa_required(self, user: User) -> bool:
        """
        Check if MFA is required for a user.
        
        Args:
            user: User object
            
        Returns:
            bool: True if MFA is required
        """
        # Check if MFA is globally enabled
        mfa_enabled = getattr(self.config, 'enable_mfa', False)
        if not mfa_enabled:
            return False
        
        # Check if user has MFA enabled
        username = user.username
        if username not in self.user_mfa_data:
            return False
        
        return self.user_mfa_data[username]['enabled']
    
    async def cleanup_expired_tokens(self) -> None:
        """Clean up expired enrollment tokens."""
        current_time = datetime.utcnow()
        expired_tokens = [
            token for token, data in self.enrollment_tokens.items()
            if current_time > data['expires_at']
        ]
        
        for token in expired_tokens:
            username = self.enrollment_tokens[token]['username']
            log_with_context(
                logger,
                logging.INFO,
                "Cleaning up expired enrollment token",
                username=username,
                token=token[:8] + "..."
            )
            del self.enrollment_tokens[token]
    
    async def get_mfa_statistics(self) -> Dict[str, Any]:
        """
        Get MFA usage statistics.
        
        Returns:
            Dict[str, Any]: MFA statistics
        """
        total_users = len(self.user_mfa_data)
        enabled_users = sum(1 for data in self.user_mfa_data.values() if data['enabled'])
        
        # Calculate backup code usage
        backup_code_stats = {}
        for username, user_data in self.user_mfa_data.items():
            used_codes = len(self.used_backup_codes.get(username, set()))
            total_codes = len(user_data['backup_codes'])
            backup_code_stats[username] = {
                'used': used_codes,
                'remaining': total_codes - used_codes,
                'total': total_codes
            }
        
        return {
            'total_users_with_mfa': total_users,
            'enabled_users': enabled_users,
            'enrollment_rate': enabled_users / max(1, total_users),
            'active_enrollment_tokens': len(self.enrollment_tokens),
            'backup_code_usage': backup_code_stats
        }