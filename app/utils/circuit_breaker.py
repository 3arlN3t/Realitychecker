"""
Circuit breaker pattern implementation for external service calls.

This module provides circuit breaker functionality to prevent cascading failures
when external services are unavailable or responding slowly.
"""

import asyncio
import logging
import time
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker, AlertSeverity

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls are blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 30.0               # Request timeout in seconds
    expected_exception: type = Exception  # Exception type that counts as failure


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            config: Configuration for the circuit breaker
        """
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute a function call through the circuit breaker.
        
        Args:
            func: Async function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the function call
        """
        correlation_id = get_correlation_id()
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        with self._lock:
            # Check if we should attempt the call
            if not self._can_attempt():
                metrics.increment_counter(
                    "circuit_breaker_blocked_calls",
                    labels={"circuit": self.name}
                )
                
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Circuit breaker '{self.name}' is OPEN, blocking call",
                    circuit_state=self.state.value,
                    failure_count=self.failure_count,
                    correlation_id=correlation_id
                )
                
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Service is currently unavailable."
                )
            
            # If half-open, only allow one call at a time
            if self.state == CircuitState.HALF_OPEN:
                log_with_context(
                    logger,
                    logging.INFO,
                    f"Circuit breaker '{self.name}' is HALF_OPEN, testing service",
                    correlation_id=correlation_id
                )
        
        # Execute the call
        start_time = time.time()
        
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            duration = time.time() - start_time
            
            # Record success
            self._record_success()
            
            metrics.increment_counter(
                "circuit_breaker_successful_calls",
                labels={"circuit": self.name}
            )
            metrics.record_histogram(
                "circuit_breaker_call_duration",
                duration,
                labels={"circuit": self.name, "result": "success"}
            )
            
            log_with_context(
                logger,
                logging.DEBUG,
                f"Circuit breaker '{self.name}' call succeeded",
                duration_seconds=duration,
                circuit_state=self.state.value,
                correlation_id=correlation_id
            )
            
            return result
            
        except asyncio.TimeoutError as e:
            duration = time.time() - start_time
            
            self._record_failure()
            
            metrics.increment_counter(
                "circuit_breaker_failed_calls",
                labels={"circuit": self.name, "reason": "timeout"}
            )
            metrics.record_histogram(
                "circuit_breaker_call_duration",
                duration,
                labels={"circuit": self.name, "result": "timeout"}
            )
            
            error_tracker.track_error(
                "CircuitBreakerTimeout",
                f"Circuit breaker '{self.name}' call timed out after {self.config.timeout}s",
                f"circuit_breaker_{self.name}",
                correlation_id,
                {"timeout": self.config.timeout, "duration": duration},
                AlertSeverity.HIGH
            )
            
            log_with_context(
                logger,
                logging.ERROR,
                f"Circuit breaker '{self.name}' call timed out",
                timeout_seconds=self.config.timeout,
                duration_seconds=duration,
                circuit_state=self.state.value,
                failure_count=self.failure_count,
                correlation_id=correlation_id
            )
            
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Only count expected exceptions as failures
            if isinstance(e, self.config.expected_exception):
                self._record_failure()
                
                metrics.increment_counter(
                    "circuit_breaker_failed_calls",
                    labels={"circuit": self.name, "reason": "exception"}
                )
                
                error_tracker.track_error(
                    type(e).__name__,
                    f"Circuit breaker '{self.name}' call failed: {str(e)}",
                    f"circuit_breaker_{self.name}",
                    correlation_id,
                    {"exception_type": type(e).__name__, "duration": duration},
                    AlertSeverity.MEDIUM
                )
                
                log_with_context(
                    logger,
                    logging.ERROR,
                    f"Circuit breaker '{self.name}' call failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_seconds=duration,
                    circuit_state=self.state.value,
                    failure_count=self.failure_count,
                    correlation_id=correlation_id
                )
            else:
                # Unexpected exceptions don't count as failures
                log_with_context(
                    logger,
                    logging.ERROR,
                    f"Circuit breaker '{self.name}' unexpected error",
                    error=str(e),
                    error_type=type(e).__name__,
                    correlation_id=correlation_id
                )
            
            metrics.record_histogram(
                "circuit_breaker_call_duration",
                duration,
                labels={"circuit": self.name, "result": "error"}
            )
            
            raise
    
    def _can_attempt(self) -> bool:
        """Check if we can attempt a call based on current state."""
        now = datetime.now(timezone.utc)
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if (self.next_attempt_time and now >= self.next_attempt_time):
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    def _record_failure(self):
        """Record a failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now(timezone.utc)
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state goes back to open
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state."""
        self.state = CircuitState.OPEN
        self.next_attempt_time = (
            datetime.now(timezone.utc) + 
            timedelta(seconds=self.config.recovery_timeout)
        )
        
        log_with_context(
            logger,
            logging.WARNING,
            f"Circuit breaker '{self.name}' transitioned to OPEN",
            failure_count=self.failure_count,
            recovery_timeout=self.config.recovery_timeout,
            next_attempt_time=self.next_attempt_time.isoformat()
        )
        
        # Track circuit breaker opening as an alert
        error_tracker = get_error_tracker()
        error_tracker.track_error(
            "CircuitBreakerOpened",
            f"Circuit breaker '{self.name}' opened due to {self.failure_count} failures",
            f"circuit_breaker_{self.name}",
            get_correlation_id(),
            {
                "failure_count": self.failure_count,
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout
            },
            AlertSeverity.HIGH
        )
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        
        log_with_context(
            logger,
            logging.INFO,
            f"Circuit breaker '{self.name}' transitioned to HALF_OPEN",
            failure_count=self.failure_count
        )
    
    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        
        log_with_context(
            logger,
            logging.INFO,
            f"Circuit breaker '{self.name}' transitioned to CLOSED (recovered)"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the circuit breaker.
        
        Returns:
            Dict containing circuit breaker status
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "last_failure_time": (
                    self.last_failure_time.isoformat() 
                    if self.last_failure_time else None
                ),
                "next_attempt_time": (
                    self.next_attempt_time.isoformat() 
                    if self.next_attempt_time else None
                )
            }
    
    def force_open(self):
        """Manually force the circuit breaker to OPEN state."""
        with self._lock:
            self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.name}' manually forced to OPEN")
    
    def force_closed(self):
        """Manually force the circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' manually forced to CLOSED")


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        """Initialize the circuit breaker manager."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        logger.info("Circuit breaker manager initialized")
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            config: Configuration (uses default if None)
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig()
                self._breakers[name] = CircuitBreaker(name, config)
            
            return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers.
        
        Returns:
            Dict mapping breaker names to their status
        """
        with self._lock:
            return {
                name: breaker.get_status()
                for name, breaker in self._breakers.items()
            }
    
    def reset_all(self):
        """Reset all circuit breakers to CLOSED state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.force_closed()
            logger.info("All circuit breakers reset to CLOSED")


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get a circuit breaker by name.
    
    Args:
        name: Name of the circuit breaker
        config: Optional configuration
        
    Returns:
        CircuitBreaker instance
    """
    manager = get_circuit_breaker_manager()
    return manager.get_breaker(name, config)


def reset_circuit_breaker_manager():
    """Reset the global circuit breaker manager (useful for testing)."""
    global _circuit_breaker_manager
    _circuit_breaker_manager = None