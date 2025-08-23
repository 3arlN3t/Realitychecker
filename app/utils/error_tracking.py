"""
Error tracking and alerting system for monitoring application health.

This module provides error tracking, alerting, and notification capabilities
for monitoring application errors and performance issues.
"""

import json
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Deque
from enum import Enum

from app.utils.logging import get_logger, sanitize_sensitive_data
from app.utils.metrics import get_metrics_collector

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts that can be triggered."""
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    SERVICE_FAILURE = "service_failure"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    SECURITY_INCIDENT = "security_incident"
    DATA_QUALITY = "data_quality"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class ErrorEvent:
    """Represents an error event for tracking."""
    timestamp: datetime
    error_type: str
    message: str
    component: str
    correlation_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM


@dataclass
class Alert:
    """Represents an alert that should be sent."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ErrorTracker:
    """Tracks errors and generates alerts based on configurable thresholds."""
    
    def __init__(
        self,
        max_errors_per_component: int = 1000,
        error_rate_threshold: float = 10.0,  # errors per minute
        response_time_threshold: float = 5.0,  # seconds
        service_failure_threshold: int = 3  # consecutive failures
    ):
        """
        Initialize the error tracker.
        
        Args:
            max_errors_per_component: Maximum errors to track per component
            error_rate_threshold: Error rate threshold for alerting (per minute)
            response_time_threshold: Response time threshold for alerting (seconds)
            service_failure_threshold: Consecutive failures before alerting
        """
        self.max_errors = max_errors_per_component
        self.error_rate_threshold = error_rate_threshold
        self.response_time_threshold = response_time_threshold
        self.service_failure_threshold = service_failure_threshold
        
        self._lock = threading.RLock()
        self._errors: Dict[str, Deque[ErrorEvent]] = defaultdict(
            lambda: deque(maxlen=self.max_errors)
        )
        self._alerts: Dict[str, Alert] = {}
        self._alert_handlers: List[Callable[[Alert], None]] = []
        
        # Service failure tracking
        self._service_failures: Dict[str, int] = defaultdict(int)
        self._last_service_success: Dict[str, datetime] = {}
        
        # Alert suppression to prevent spam
        self._alert_cooldowns: Dict[str, datetime] = {}
        self._cooldown_duration = timedelta(minutes=15)
        
        logger.info("Error tracker initialized")
    
    def track_error(
        self,
        error_type: str,
        message: str,
        component: str,
        correlation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        severity: AlertSeverity = AlertSeverity.MEDIUM
    ):
        """
        Track an error event.
        
        Args:
            error_type: Type of error (e.g., 'ValidationError', 'APIError')
            message: Error message
            component: Component where error occurred
            correlation_id: Request correlation ID
            context: Additional context information
            stack_trace: Stack trace if available
            severity: Error severity level
        """
        with self._lock:
            # Sanitize context data
            safe_context = sanitize_sensitive_data(context or {})
            
            error_event = ErrorEvent(
                timestamp=datetime.now(timezone.utc),
                error_type=error_type,
                message=message,
                component=component,
                correlation_id=correlation_id,
                context=safe_context,
                stack_trace=stack_trace,
                severity=severity
            )
            
            # Store error
            self._errors[component].append(error_event)
            
            # Update metrics
            metrics = get_metrics_collector()
            metrics.increment_counter(
                "errors_total",
                labels={
                    "component": component,
                    "error_type": error_type,
                    "severity": severity.value
                }
            )
            
            # Check for alert conditions
            self._check_alert_conditions(component, error_event)
            
            logger.warning(
                f"Error tracked: {error_type} in {component}",
                extra={
                    "error_type": error_type,
                    "component": component,
                    "correlation_id": correlation_id,
                    "severity": severity.value
                }
            )
    
    def track_service_call(self, service: str, operation: str, success: bool, duration: float):
        """
        Track a service call for failure detection.
        
        Args:
            service: Service name
            operation: Operation name
            success: Whether the call was successful
            duration: Call duration in seconds
        """
        with self._lock:
            service_key = f"{service}_{operation}"
            
            if success:
                self._service_failures[service_key] = 0
                self._last_service_success[service_key] = datetime.now(timezone.utc)
                
                # Check if we should resolve a service failure alert
                alert_key = f"service_failure_{service_key}"
                if alert_key in self._alerts and not self._alerts[alert_key].resolved:
                    self._resolve_alert(alert_key, "Service recovered")
            else:
                self._service_failures[service_key] += 1
                
                # Check for service failure alert
                if self._service_failures[service_key] >= self.service_failure_threshold:
                    self._create_alert(
                        AlertType.SERVICE_FAILURE,
                        AlertSeverity.HIGH,
                        f"Service {service} failing",
                        f"Service {service} operation {operation} has failed "
                        f"{self._service_failures[service_key]} consecutive times",
                        {
                            "service": service,
                            "operation": operation,
                            "consecutive_failures": self._service_failures[service_key]
                        }
                    )
            
            # Check response time threshold
            if duration > self.response_time_threshold:
                self._create_alert(
                    AlertType.RESPONSE_TIME,
                    AlertSeverity.MEDIUM,
                    f"Slow response from {service}",
                    f"Service {service} operation {operation} took {duration:.2f}s "
                    f"(threshold: {self.response_time_threshold}s)",
                    {
                        "service": service,
                        "operation": operation,
                        "duration": duration,
                        "threshold": self.response_time_threshold
                    }
                )
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        Add an alert handler function.
        
        Args:
            handler: Function that will be called when alerts are created
        """
        self._alert_handlers.append(handler)
        logger.info(f"Added alert handler: {handler.__name__}")
    
    def get_error_summary(self, component: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for monitoring.
        
        Args:
            component: Specific component to get errors for (None for all)
            hours: Number of hours to look back
            
        Returns:
            Dict containing error summary
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with self._lock:
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_hours": hours,
                "components": {}
            }
            
            components_to_check = [component] if component else self._errors.keys()
            
            for comp in components_to_check:
                if comp not in self._errors:
                    continue
                
                recent_errors = [
                    error for error in self._errors[comp]
                    if error.timestamp >= cutoff_time
                ]
                
                if not recent_errors:
                    continue
                
                # Group by error type
                error_types = defaultdict(int)
                severity_counts = defaultdict(int)
                
                for error in recent_errors:
                    error_types[error.error_type] += 1
                    severity_counts[error.severity.value] += 1
                
                summary["components"][comp] = {
                    "total_errors": len(recent_errors),
                    "error_rate_per_hour": len(recent_errors) / hours,
                    "error_types": dict(error_types),
                    "severity_breakdown": dict(severity_counts),
                    "latest_error": recent_errors[-1].timestamp.isoformat() if recent_errors else None
                }
            
            return summary
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active (unresolved) alerts.
        
        Returns:
            List of active alerts
        """
        with self._lock:
            return [alert for alert in self._alerts.values() if not alert.resolved]
    
    def resolve_alert(self, alert_id: str, resolution_message: str = "Manually resolved"):
        """
        Manually resolve an alert.
        
        Args:
            alert_id: ID of the alert to resolve
            resolution_message: Message describing the resolution
        """
        with self._lock:
            self._resolve_alert(alert_id, resolution_message)
    
    def cleanup_old_data(self, max_age_hours: int = 168):  # 1 week default
        """
        Clean up old error data and resolved alerts.
        
        Args:
            max_age_hours: Maximum age of data to keep in hours
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        with self._lock:
            # Clean up old errors
            for component, errors in self._errors.items():
                while errors and errors[0].timestamp < cutoff_time:
                    errors.popleft()
            
            # Clean up old resolved alerts
            old_alerts = [
                alert_id for alert_id, alert in self._alerts.items()
                if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time
            ]
            
            for alert_id in old_alerts:
                del self._alerts[alert_id]
            
            # Clean up old cooldowns
            old_cooldowns = [
                key for key, timestamp in self._alert_cooldowns.items()
                if timestamp < cutoff_time
            ]
            
            for key in old_cooldowns:
                del self._alert_cooldowns[key]
            
            logger.info(f"Cleaned up error tracking data older than {max_age_hours} hours")
    
    def _check_alert_conditions(self, component: str, error_event: ErrorEvent):
        """Check if error conditions warrant an alert."""
        # Check error rate
        recent_errors = [
            error for error in self._errors[component]
            if error.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=1)
        ]
        
        if len(recent_errors) >= self.error_rate_threshold:
            self._create_alert(
                AlertType.ERROR_RATE,
                AlertSeverity.HIGH,
                f"High error rate in {component}",
                f"Component {component} has {len(recent_errors)} errors in the last minute "
                f"(threshold: {self.error_rate_threshold})",
                {
                    "component": component,
                    "error_count": len(recent_errors),
                    "threshold": self.error_rate_threshold
                }
            )
        
        # Check for critical errors
        if error_event.severity == AlertSeverity.CRITICAL:
            self._create_alert(
                AlertType.CONFIGURATION_ERROR,
                AlertSeverity.CRITICAL,
                f"Critical error in {component}",
                f"Critical error: {error_event.message}",
                {
                    "component": component,
                    "error_type": error_event.error_type,
                    "correlation_id": error_event.correlation_id
                }
            )
    
    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        context: Dict[str, Any]
    ):
        """Create and process a new alert."""
        alert_key = f"{alert_type.value}_{hash(title)}"
        
        # Check cooldown to prevent spam
        if alert_key in self._alert_cooldowns:
            if datetime.now(timezone.utc) < self._alert_cooldowns[alert_key]:
                return  # Still in cooldown
        
        alert = Alert(
            id=alert_key,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc),
            context=context
        )
        
        self._alerts[alert_key] = alert
        self._alert_cooldowns[alert_key] = datetime.now(timezone.utc) + self._cooldown_duration
        
        # Notify alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}", exc_info=True)
        
        logger.error(
            f"Alert created: {title}",
            extra={
                "alert_type": alert_type.value,
                "severity": severity.value,
                "alert_id": alert_key
            }
        )
    
    def _resolve_alert(self, alert_id: str, resolution_message: str):
        """Resolve an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            
            logger.info(
                f"Alert resolved: {alert.title} - {resolution_message}",
                extra={
                    "alert_id": alert_id,
                    "resolution": resolution_message
                }
            )


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def reset_error_tracker():
    """Reset the global error tracker (useful for testing)."""
    global _error_tracker
    _error_tracker = None


# Alert handler functions
def log_alert_handler(alert: Alert):
    """Simple alert handler that logs alerts."""
    logger.critical(
        f"ALERT: {alert.title}",
        extra={
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "context": alert.context
        }
    )


def webhook_alert_handler(webhook_url: str):
    """
    Create a webhook alert handler.
    
    Args:
        webhook_url: URL to send webhook notifications to
        
    Returns:
        Alert handler function
    """
    def handler(alert: Alert):
        """Send alert to webhook."""
        try:
            import httpx
            
            payload = {
                "alert_id": alert.id,
                "type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "context": alert.context
            }
            
            # Send webhook (fire and forget)
            # In production, you might want to use a queue for reliability
            with httpx.Client(timeout=5.0) as client:
                response = client.post(webhook_url, json=payload)
                response.raise_for_status()
                
            logger.info(f"Alert sent to webhook: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send alert to webhook: {e}")
    
    return handler