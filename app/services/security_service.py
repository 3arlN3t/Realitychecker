"""
Security service for advanced security features.

This service provides comprehensive security features including:
- Account lockout and brute force protection
- Login attempt tracking and monitoring
- Suspicious activity detection
- Progressive delays for failed attempts
- IP-based blocking and monitoring
"""

import logging
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import ipaddress

from app.models.data_models import AppConfig, User
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.error_tracking import get_error_tracker, AlertSeverity


logger = get_logger(__name__)


class SecurityEventType(Enum):
    """Types of security events."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    IP_BLOCKED = "ip_blocked"
    MFA_BYPASS_ATTEMPT = "mfa_bypass_attempt"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_CHANGED = "password_changed"


@dataclass
class SecurityEvent:
    """Security event record."""
    event_type: SecurityEventType
    username: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class LoginAttempt:
    """Login attempt record."""
    username: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None


@dataclass
class AccountLockoutInfo:
    """Account lockout information."""
    username: str
    locked_at: datetime
    unlock_at: datetime
    failed_attempts: int
    last_attempt_ip: str
    lockout_reason: str


@dataclass
class BruteForceAttempt:
    """Brute force attempt tracking."""
    ip_address: str
    usernames_attempted: Set[str]
    first_attempt: datetime
    last_attempt: datetime
    total_attempts: int
    success_count: int


@dataclass
class SecurityMetrics:
    """Security metrics and statistics."""
    total_login_attempts: int
    successful_logins: int
    failed_logins: int
    account_lockouts: int
    brute_force_attempts: int
    blocked_ips: int
    suspicious_activities: int
    mfa_bypass_attempts: int


class SecurityService:
    """
    Advanced security service for account protection and monitoring.
    
    Provides comprehensive security features including account lockout,
    brute force protection, and suspicious activity detection.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the security service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Configuration settings
        self.max_login_attempts = getattr(config, 'max_login_attempts', 5)
        self.lockout_duration_minutes = getattr(config, 'lockout_duration_minutes', 30)
        self.progressive_delay_enabled = getattr(config, 'progressive_delay_enabled', True)
        self.brute_force_threshold = getattr(config, 'brute_force_threshold', 10)
        self.suspicious_activity_threshold = getattr(config, 'suspicious_activity_threshold', 20)
        self.ip_block_duration_minutes = getattr(config, 'ip_block_duration_minutes', 60)
        
        # In-memory storage for demo purposes
        # In production, this should be stored in a database with proper indexing
        self.login_attempts: Dict[str, List[LoginAttempt]] = defaultdict(list)
        self.account_lockouts: Dict[str, AccountLockoutInfo] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.security_events: List[SecurityEvent] = []
        self.brute_force_attempts: Dict[str, BruteForceAttempt] = {}
        
        # Rate limiting for progressive delays
        self.attempt_delays: Dict[str, float] = {}
        
        logger.info("Security service initialized")
    
    def _get_client_identifier(self, username: str, ip_address: str) -> str:
        """
        Generate a unique identifier for a client.
        
        Args:
            username: Username
            ip_address: IP address
            
        Returns:
            str: Unique client identifier
        """
        return hashlib.sha256(f"{username}:{ip_address}".encode()).hexdigest()[:16]
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP address is blocked.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            bool: True if IP is blocked
        """
        if ip_address not in self.blocked_ips:
            return False
        
        # Check if block has expired
        block_time = self.blocked_ips[ip_address]
        if datetime.utcnow() > block_time + timedelta(minutes=self.ip_block_duration_minutes):
            del self.blocked_ips[ip_address]
            return False
        
        return True
    
    def _block_ip(self, ip_address: str, reason: str) -> None:
        """
        Block an IP address.
        
        Args:
            ip_address: IP address to block
            reason: Reason for blocking
        """
        self.blocked_ips[ip_address] = datetime.utcnow()
        
        # Log security event
        self._log_security_event(
            SecurityEventType.IP_BLOCKED,
            "system",
            ip_address,
            "system",
            True,
            {"reason": reason}
        )
        
        logger.warning(f"IP {ip_address} blocked for {reason}")
    
    def _calculate_progressive_delay(self, username: str, ip_address: str, failed_attempts: int) -> float:
        """
        Calculate progressive delay for failed login attempts.
        
        Args:
            username: Username
            ip_address: IP address
            failed_attempts: Number of failed attempts
            
        Returns:
            float: Delay in seconds
        """
        if not self.progressive_delay_enabled:
            return 0.0
        
        # Base delay starts at 1 second and doubles for each attempt
        base_delay = 1.0
        max_delay = 30.0  # Maximum delay of 30 seconds
        
        delay = min(base_delay * (2 ** (failed_attempts - 1)), max_delay)
        return delay
    
    def _apply_progressive_delay(self, username: str, ip_address: str, failed_attempts: int) -> None:
        """
        Apply progressive delay for failed login attempts.
        
        Args:
            username: Username
            ip_address: IP address
            failed_attempts: Number of failed attempts
        """
        delay = self._calculate_progressive_delay(username, ip_address, failed_attempts)
        if delay > 0:
            client_id = self._get_client_identifier(username, ip_address)
            self.attempt_delays[client_id] = time.time() + delay
            time.sleep(delay)
    
    def _log_security_event(self, event_type: SecurityEventType, username: str, 
                           ip_address: str, user_agent: str, success: bool, 
                           metadata: Optional[Dict[str, any]] = None) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            username: Username involved
            ip_address: IP address
            user_agent: User agent string
            success: Whether the event was successful
            metadata: Additional metadata
        """
        event = SecurityEvent(
            event_type=event_type,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=success,
            metadata=metadata or {}
        )
        
        self.security_events.append(event)
        
        # Keep only last 10000 events to prevent memory issues
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]
        
        # Log to application logger
        log_with_context(
            logger,
            logging.INFO if success else logging.WARNING,
            f"Security event: {event_type.value}",
            username=username,
            ip_address=ip_address,
            success=success,
            metadata=metadata
        )
    
    def _detect_brute_force(self, ip_address: str, username: str) -> bool:
        """
        Detect brute force attack attempts.
        
        Args:
            ip_address: IP address
            username: Username
            
        Returns:
            bool: True if brute force attack detected
        """
        current_time = datetime.utcnow()
        
        # Update brute force tracking
        if ip_address not in self.brute_force_attempts:
            self.brute_force_attempts[ip_address] = BruteForceAttempt(
                ip_address=ip_address,
                usernames_attempted=set(),
                first_attempt=current_time,
                last_attempt=current_time,
                total_attempts=0,
                success_count=0
            )
        
        attempt = self.brute_force_attempts[ip_address]
        attempt.usernames_attempted.add(username)
        attempt.last_attempt = current_time
        attempt.total_attempts += 1
        
        # Check if this constitutes a brute force attack
        time_window = timedelta(minutes=15)  # 15-minute window
        if (current_time - attempt.first_attempt) <= time_window:
            if attempt.total_attempts >= self.brute_force_threshold:
                return True
            
            # Multiple usernames from same IP in short time
            if len(attempt.usernames_attempted) >= 5:
                return True
        
        return False
    
    def _detect_suspicious_activity(self, username: str, ip_address: str, user_agent: str) -> bool:
        """
        Detect suspicious activity patterns.
        
        Args:
            username: Username
            ip_address: IP address
            user_agent: User agent string
            
        Returns:
            bool: True if suspicious activity detected
        """
        current_time = datetime.utcnow()
        
        # Get recent login attempts for this user
        user_attempts = self.login_attempts.get(username, [])
        recent_attempts = [
            attempt for attempt in user_attempts
            if (current_time - attempt.timestamp) <= timedelta(hours=1)
        ]
        
        # Check for multiple IPs in short time
        recent_ips = set(attempt.ip_address for attempt in recent_attempts)
        if len(recent_ips) >= 3:
            return True
        
        # Check for unusual user agent patterns
        recent_user_agents = set(attempt.user_agent for attempt in recent_attempts)
        if len(recent_user_agents) >= 3:
            return True
        
        # Check for high frequency of attempts
        if len(recent_attempts) >= self.suspicious_activity_threshold:
            return True
        
        return False
    
    async def check_account_lockout(self, username: str) -> Optional[AccountLockoutInfo]:
        """
        Check if an account is locked out.
        
        Args:
            username: Username to check
            
        Returns:
            Optional[AccountLockoutInfo]: Lockout info if account is locked
        """
        if username not in self.account_lockouts:
            return None
        
        lockout_info = self.account_lockouts[username]
        
        # Check if lockout has expired
        if datetime.utcnow() >= lockout_info.unlock_at:
            # Remove expired lockout
            del self.account_lockouts[username]
            
            # Log unlock event
            self._log_security_event(
                SecurityEventType.ACCOUNT_UNLOCKED,
                username,
                lockout_info.last_attempt_ip,
                "system",
                True,
                {"auto_unlock": True}
            )
            
            return None
        
        return lockout_info
    
    async def record_login_attempt(self, username: str, ip_address: str, user_agent: str, 
                                 success: bool, failure_reason: Optional[str] = None) -> Dict[str, any]:
        """
        Record a login attempt and apply security measures.
        
        Args:
            username: Username
            ip_address: IP address
            user_agent: User agent string
            success: Whether login was successful
            failure_reason: Reason for failure if applicable
            
        Returns:
            Dict[str, any]: Security response with any applied measures
        """
        correlation_id = get_correlation_id()
        current_time = datetime.utcnow()
        
        # Check if IP is blocked
        if self._is_ip_blocked(ip_address):
            self._log_security_event(
                SecurityEventType.LOGIN_FAILED,
                username,
                ip_address,
                user_agent,
                False,
                {"reason": "IP blocked", "failure_reason": failure_reason}
            )
            return {
                "blocked": True,
                "reason": "IP address is temporarily blocked",
                "retry_after": self.ip_block_duration_minutes * 60
            }
        
        # Check if account is locked
        lockout_info = await self.check_account_lockout(username)
        if lockout_info:
            self._log_security_event(
                SecurityEventType.LOGIN_FAILED,
                username,
                ip_address,
                user_agent,
                False,
                {"reason": "Account locked", "failure_reason": failure_reason}
            )
            return {
                "blocked": True,
                "reason": "Account is temporarily locked",
                "retry_after": int((lockout_info.unlock_at - current_time).total_seconds())
            }
        
        # Record the login attempt
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=current_time,
            success=success,
            failure_reason=failure_reason
        )
        
        self.login_attempts[username].append(attempt)
        
        # Keep only last 100 attempts per user
        if len(self.login_attempts[username]) > 100:
            self.login_attempts[username] = self.login_attempts[username][-50:]
        
        # Log security event
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED
        self._log_security_event(
            event_type,
            username,
            ip_address,
            user_agent,
            success,
            {"failure_reason": failure_reason}
        )
        
        if success:
            # Clear any existing lockout on successful login
            if username in self.account_lockouts:
                del self.account_lockouts[username]
            return {"success": True}
        
        # Handle failed login attempt
        return await self._handle_failed_login(username, ip_address, user_agent, failure_reason)
    
    async def _handle_failed_login(self, username: str, ip_address: str, 
                                 user_agent: str, failure_reason: Optional[str]) -> Dict[str, any]:
        """
        Handle failed login attempt and apply security measures.
        
        Args:
            username: Username
            ip_address: IP address
            user_agent: User agent string
            failure_reason: Reason for failure
            
        Returns:
            Dict[str, any]: Security response
        """
        current_time = datetime.utcnow()
        
        # Count recent failed attempts
        user_attempts = self.login_attempts.get(username, [])
        recent_failures = [
            attempt for attempt in user_attempts
            if not attempt.success and 
            (current_time - attempt.timestamp) <= timedelta(hours=1)
        ]
        
        failed_attempts = len(recent_failures)
        
        # Apply progressive delay
        self._apply_progressive_delay(username, ip_address, failed_attempts)
        
        # Check for brute force attack
        if self._detect_brute_force(ip_address, username):
            self._block_ip(ip_address, "Brute force attack detected")
            self._log_security_event(
                SecurityEventType.BRUTE_FORCE_DETECTED,
                username,
                ip_address,
                user_agent,
                False,
                {"total_attempts": failed_attempts}
            )
        
        # Check for suspicious activity
        if self._detect_suspicious_activity(username, ip_address, user_agent):
            self._log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                username,
                ip_address,
                user_agent,
                False,
                {"pattern": "Multiple IPs or user agents"}
            )
        
        # Check if account should be locked
        if failed_attempts >= self.max_login_attempts:
            unlock_time = current_time + timedelta(minutes=self.lockout_duration_minutes)
            
            lockout_info = AccountLockoutInfo(
                username=username,
                locked_at=current_time,
                unlock_at=unlock_time,
                failed_attempts=failed_attempts,
                last_attempt_ip=ip_address,
                lockout_reason=f"Too many failed login attempts: {failed_attempts}"
            )
            
            self.account_lockouts[username] = lockout_info
            
            self._log_security_event(
                SecurityEventType.ACCOUNT_LOCKED,
                username,
                ip_address,
                user_agent,
                False,
                {
                    "failed_attempts": failed_attempts,
                    "lockout_duration_minutes": self.lockout_duration_minutes
                }
            )
            
            return {
                "blocked": True,
                "reason": f"Account locked due to {failed_attempts} failed login attempts",
                "retry_after": self.lockout_duration_minutes * 60
            }
        
        # Calculate remaining attempts
        remaining_attempts = self.max_login_attempts - failed_attempts
        
        return {
            "success": False,
            "failed_attempts": failed_attempts,
            "remaining_attempts": remaining_attempts,
            "lockout_warning": remaining_attempts <= 2
        }
    
    async def unlock_account(self, username: str, admin_user: str) -> bool:
        """
        Manually unlock an account (admin function).
        
        Args:
            username: Username to unlock
            admin_user: Admin user performing the unlock
            
        Returns:
            bool: True if account was unlocked
        """
        if username not in self.account_lockouts:
            return False
        
        lockout_info = self.account_lockouts[username]
        del self.account_lockouts[username]
        
        self._log_security_event(
            SecurityEventType.ACCOUNT_UNLOCKED,
            username,
            lockout_info.last_attempt_ip,
            "admin",
            True,
            {"admin_user": admin_user, "manual_unlock": True}
        )
        
        log_with_context(
            logger,
            logging.INFO,
            "Account manually unlocked",
            username=username,
            admin_user=admin_user
        )
        
        return True
    
    async def get_security_metrics(self) -> SecurityMetrics:
        """
        Get security metrics and statistics.
        
        Returns:
            SecurityMetrics: Security statistics
        """
        current_time = datetime.utcnow()
        last_24h = current_time - timedelta(hours=24)
        
        # Filter recent events
        recent_events = [
            event for event in self.security_events
            if event.timestamp >= last_24h
        ]
        
        # Count event types
        login_attempts = sum(1 for event in recent_events 
                           if event.event_type in [SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILED])
        successful_logins = sum(1 for event in recent_events 
                              if event.event_type == SecurityEventType.LOGIN_SUCCESS)
        failed_logins = sum(1 for event in recent_events 
                          if event.event_type == SecurityEventType.LOGIN_FAILED)
        account_lockouts = sum(1 for event in recent_events 
                             if event.event_type == SecurityEventType.ACCOUNT_LOCKED)
        brute_force_attempts = sum(1 for event in recent_events 
                                 if event.event_type == SecurityEventType.BRUTE_FORCE_DETECTED)
        suspicious_activities = sum(1 for event in recent_events 
                                  if event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY)
        mfa_bypass_attempts = sum(1 for event in recent_events 
                                if event.event_type == SecurityEventType.MFA_BYPASS_ATTEMPT)
        
        # Count currently blocked IPs
        blocked_ips = sum(1 for block_time in self.blocked_ips.values()
                        if current_time <= block_time + timedelta(minutes=self.ip_block_duration_minutes))
        
        return SecurityMetrics(
            total_login_attempts=login_attempts,
            successful_logins=successful_logins,
            failed_logins=failed_logins,
            account_lockouts=account_lockouts,
            brute_force_attempts=brute_force_attempts,
            blocked_ips=blocked_ips,
            suspicious_activities=suspicious_activities,
            mfa_bypass_attempts=mfa_bypass_attempts
        )
    
    async def get_locked_accounts(self) -> List[AccountLockoutInfo]:
        """
        Get list of currently locked accounts.
        
        Returns:
            List[AccountLockoutInfo]: List of locked accounts
        """
        current_time = datetime.utcnow()
        active_lockouts = []
        
        for username, lockout_info in list(self.account_lockouts.items()):
            if current_time < lockout_info.unlock_at:
                active_lockouts.append(lockout_info)
            else:
                # Remove expired lockout
                del self.account_lockouts[username]
        
        return active_lockouts
    
    async def get_blocked_ips(self) -> Dict[str, datetime]:
        """
        Get list of currently blocked IPs.
        
        Returns:
            Dict[str, datetime]: Dictionary of blocked IPs and block times
        """
        current_time = datetime.utcnow()
        active_blocks = {}
        
        for ip_address, block_time in list(self.blocked_ips.items()):
            if current_time <= block_time + timedelta(minutes=self.ip_block_duration_minutes):
                active_blocks[ip_address] = block_time
            else:
                # Remove expired block
                del self.blocked_ips[ip_address]
        
        return active_blocks
    
    async def get_recent_security_events(self, hours: int = 24, event_types: Optional[List[SecurityEventType]] = None) -> List[SecurityEvent]:
        """
        Get recent security events.
        
        Args:
            hours: Number of hours to look back
            event_types: Filter by specific event types
            
        Returns:
            List[SecurityEvent]: List of recent security events
        """
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=hours)
        
        events = [
            event for event in self.security_events
            if event.timestamp >= cutoff_time
        ]
        
        if event_types:
            events = [event for event in events if event.event_type in event_types]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)
    
    async def cleanup_old_data(self) -> None:
        """Clean up old security data to prevent memory leaks."""
        current_time = datetime.utcnow()
        cleanup_cutoff = current_time - timedelta(days=7)
        
        # Clean up old login attempts
        for username in list(self.login_attempts.keys()):
            self.login_attempts[username] = [
                attempt for attempt in self.login_attempts[username]
                if attempt.timestamp >= cleanup_cutoff
            ]
            if not self.login_attempts[username]:
                del self.login_attempts[username]
        
        # Clean up old security events
        self.security_events = [
            event for event in self.security_events
            if event.timestamp >= cleanup_cutoff
        ]
        
        # Clean up old brute force attempts
        for ip_address in list(self.brute_force_attempts.keys()):
            attempt = self.brute_force_attempts[ip_address]
            if attempt.last_attempt < cleanup_cutoff:
                del self.brute_force_attempts[ip_address]
        
        # Clean up expired IP blocks
        expired_blocks = [
            ip for ip, block_time in self.blocked_ips.items()
            if current_time > block_time + timedelta(minutes=self.ip_block_duration_minutes)
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]
        
        logger.info(f"Security data cleanup completed. Removed old data older than {cleanup_cutoff}")