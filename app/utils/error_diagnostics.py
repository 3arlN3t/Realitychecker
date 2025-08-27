"""
Comprehensive Error Diagnostics and Actionable Logging.

This module provides detailed error diagnostics, actionable error messages,
and comprehensive logging for troubleshooting and monitoring the Reality
Checker application.

Implements Requirements:
- 6.4: Create comprehensive error logging with actionable diagnostics
- 6.5: Ensure webhook processing continues during Redis outages
- 6.6: Implement automatic recovery when services are restored
"""

import asyncio
import traceback
import sys
import psutil
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging

from app.utils.logging import get_logger, log_with_context, get_correlation_id
from app.utils.error_handling import ErrorCategory, ErrorSeverity
from app.services.redis_connection_manager import get_redis_manager
from app.services.performance_monitor import get_performance_monitor

logger = get_logger(__name__)


class DiagnosticLevel(Enum):
    """Diagnostic detail levels."""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class SystemMetrics:
    """System resource metrics for diagnostics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    load_average: Tuple[float, float, float]
    open_files: int
    network_connections: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ServiceDiagnostics:
    """Diagnostic information for a service."""
    service_name: str
    is_available: bool
    response_time_ms: Optional[float]
    error_message: Optional[str]
    last_success: Optional[datetime]
    failure_count: int
    connection_pool_size: Optional[int]
    active_connections: Optional[int]
    circuit_breaker_state: Optional[str]
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorDiagnostic:
    """Comprehensive error diagnostic information."""
    error_id: str
    timestamp: datetime
    correlation_id: str
    error_type: str
    error_message: str
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    stack_trace: str
    system_metrics: SystemMetrics
    service_diagnostics: List[ServiceDiagnostics]
    context: Dict[str, Any]
    actionable_steps: List[str]
    related_errors: List[str] = field(default_factory=list)
    resolution_suggestions: List[str] = field(default_factory=list)


class ErrorDiagnosticsCollector:
    """
    Comprehensive error diagnostics collector.
    
    Collects detailed diagnostic information for errors including system metrics,
    service health, and actionable troubleshooting steps.
    """
    
    def __init__(self):
        """Initialize error diagnostics collector."""
        self.redis_manager = get_redis_manager()
        self.performance_monitor = get_performance_monitor()
        self.error_history: List[ErrorDiagnostic] = []
        self.max_history_size = 1000
    
    async def collect_error_diagnostics(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        diagnostic_level: DiagnosticLevel = DiagnosticLevel.DETAILED
    ) -> ErrorDiagnostic:
        """
        Collect comprehensive error diagnostics.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            correlation_id: Correlation ID for tracking
            diagnostic_level: Level of diagnostic detail to collect
            
        Returns:
            ErrorDiagnostic: Comprehensive diagnostic information
        """
        correlation_id = correlation_id or get_correlation_id()
        error_id = f"error_{int(time.time() * 1000)}_{correlation_id[:8]}"
        
        # Classify error
        error_category, error_severity = self._classify_error(error)
        
        # Collect system metrics
        system_metrics = await self._collect_system_metrics()
        
        # Collect service diagnostics
        service_diagnostics = await self._collect_service_diagnostics(diagnostic_level)
        
        # Generate actionable steps
        actionable_steps = self._generate_actionable_steps(error, error_category, service_diagnostics)
        
        # Generate resolution suggestions
        resolution_suggestions = self._generate_resolution_suggestions(error, error_category, system_metrics)
        
        # Create diagnostic
        diagnostic = ErrorDiagnostic(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            error_type=type(error).__name__,
            error_message=str(error),
            error_category=error_category,
            error_severity=error_severity,
            stack_trace=self._get_formatted_traceback(error),
            system_metrics=system_metrics,
            service_diagnostics=service_diagnostics,
            context=context or {},
            actionable_steps=actionable_steps,
            resolution_suggestions=resolution_suggestions
        )
        
        # Find related errors
        diagnostic.related_errors = self._find_related_errors(diagnostic)
        
        # Store in history
        self._store_diagnostic(diagnostic)
        
        # Log comprehensive diagnostic
        await self._log_diagnostic(diagnostic, diagnostic_level)
        
        return diagnostic
    
    def _classify_error(self, error: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify error to determine category and severity."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Redis/Connection errors
        if any(keyword in error_str for keyword in ['redis', 'connection', 'timeout']):
            if 'timeout' in error_str:
                return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
            elif 'connection' in error_str:
                return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
            else:
                return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM
        
        # PDF processing errors
        if 'pdf' in error_str:
            return ErrorCategory.PDF_PROCESSING, ErrorSeverity.LOW
        
        # OpenAI errors
        if any(keyword in error_str for keyword in ['openai', 'gpt', 'api']):
            if 'rate limit' in error_str:
                return ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM
            else:
                return ErrorCategory.OPENAI_SERVICE, ErrorSeverity.MEDIUM
        
        # Twilio errors
        if 'twilio' in error_str:
            return ErrorCategory.TWILIO_SERVICE, ErrorSeverity.HIGH
        
        # Validation errors
        if any(keyword in error_str for keyword in ['validation', 'invalid', 'missing']):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        # System errors
        if any(keyword in error_type for keyword in ['memory', 'system', 'os']):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        
        # Default classification
        return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Load average (Unix-like systems)
            try:
                load_average = psutil.getloadavg()
            except AttributeError:
                # Windows doesn't have load average
                load_average = (0.0, 0.0, 0.0)
            
            # Process metrics
            process = psutil.Process()
            open_files = len(process.open_files())
            network_connections = len(process.connections())
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                load_average=load_average,
                open_files=open_files,
                network_connections=network_connections
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                load_average=(0.0, 0.0, 0.0),
                open_files=0,
                network_connections=0
            )
    
    async def _collect_service_diagnostics(self, diagnostic_level: DiagnosticLevel) -> List[ServiceDiagnostics]:
        """Collect diagnostics for all services."""
        diagnostics = []
        
        # Redis diagnostics
        redis_diag = await self._collect_redis_diagnostics(diagnostic_level)
        diagnostics.append(redis_diag)
        
        # Add other service diagnostics based on level
        if diagnostic_level in [DiagnosticLevel.DETAILED, DiagnosticLevel.COMPREHENSIVE]:
            # Could add OpenAI, Twilio, etc. diagnostics here
            pass
        
        return diagnostics
    
    async def _collect_redis_diagnostics(self, diagnostic_level: DiagnosticLevel) -> ServiceDiagnostics:
        """Collect Redis service diagnostics."""
        diagnostics = ServiceDiagnostics(
            service_name="redis",
            is_available=False,
            response_time_ms=None,
            error_message=None,
            last_success=None,
            failure_count=0,
            connection_pool_size=None,
            active_connections=None,
            circuit_breaker_state=None
        )
        
        try:
            # Check if Redis is available
            diagnostics.is_available = self.redis_manager.is_available()
            
            if diagnostics.is_available:
                # Measure response time
                start_time = time.time()
                health_status = await asyncio.wait_for(
                    self.redis_manager.health_check(),
                    timeout=5.0
                )
                response_time = (time.time() - start_time) * 1000
                
                diagnostics.response_time_ms = response_time
                diagnostics.last_success = health_status.last_success
                diagnostics.circuit_breaker_state = health_status.state.value
                
                # Get connection metrics
                if diagnostic_level == DiagnosticLevel.COMPREHENSIVE:
                    metrics = await self.redis_manager.get_metrics()
                    diagnostics.failure_count = metrics.failed_requests
                    diagnostics.active_connections = metrics.current_connections
                    diagnostics.additional_info = {
                        'total_requests': metrics.total_requests,
                        'successful_requests': metrics.successful_requests,
                        'uptime_percentage': metrics.uptime_percentage,
                        'average_response_time': metrics.average_response_time
                    }
            else:
                # Get error information
                metrics = await self.redis_manager.get_metrics()
                diagnostics.error_message = metrics.last_error
                diagnostics.failure_count = metrics.failed_requests
                diagnostics.last_success = None
                
        except Exception as e:
            diagnostics.error_message = str(e)
            diagnostics.is_available = False
        
        return diagnostics
    
    def _generate_actionable_steps(
        self,
        error: Exception,
        error_category: ErrorCategory,
        service_diagnostics: List[ServiceDiagnostics]
    ) -> List[str]:
        """Generate actionable troubleshooting steps."""
        steps = []
        
        # Redis-specific steps
        redis_diag = next((d for d in service_diagnostics if d.service_name == "redis"), None)
        if redis_diag and not redis_diag.is_available:
            steps.extend([
                "1. Check Redis server status: `redis-cli ping`",
                "2. Verify Redis connection configuration in environment variables",
                "3. Check network connectivity to Redis server",
                "4. Review Redis server logs for errors",
                "5. Consider restarting Redis service if necessary"
            ])
        
        # Connection/Network errors
        if error_category == ErrorCategory.NETWORK:
            steps.extend([
                "1. Check network connectivity and DNS resolution",
                "2. Verify firewall rules and port accessibility",
                "3. Test connection with curl or telnet",
                "4. Check for network timeouts in logs",
                "5. Consider increasing timeout values if appropriate"
            ])
        
        # System resource issues
        if error_category == ErrorCategory.SYSTEM:
            steps.extend([
                "1. Check system resource usage (CPU, memory, disk)",
                "2. Review application logs for resource exhaustion",
                "3. Monitor for memory leaks or excessive CPU usage",
                "4. Consider scaling resources if consistently high usage",
                "5. Check for disk space issues"
            ])
        
        # OpenAI API issues
        if error_category == ErrorCategory.OPENAI_SERVICE:
            steps.extend([
                "1. Check OpenAI API status at status.openai.com",
                "2. Verify API key configuration and permissions",
                "3. Review rate limiting and quota usage",
                "4. Test API connectivity with simple request",
                "5. Consider implementing retry logic with backoff"
            ])
        
        # Twilio service issues
        if error_category == ErrorCategory.TWILIO_SERVICE:
            steps.extend([
                "1. Check Twilio service status at status.twilio.com",
                "2. Verify Twilio credentials and webhook configuration",
                "3. Test webhook endpoint accessibility",
                "4. Review Twilio logs for delivery failures",
                "5. Check WhatsApp sandbox configuration if applicable"
            ])
        
        # PDF processing issues
        if error_category == ErrorCategory.PDF_PROCESSING:
            steps.extend([
                "1. Verify PDF file accessibility and format",
                "2. Check PDF file size and content type",
                "3. Test PDF processing with sample files",
                "4. Review PDF extraction library logs",
                "5. Consider fallback to text input for users"
            ])
        
        # General steps if no specific category matched
        if not steps:
            steps.extend([
                "1. Review application logs for detailed error information",
                "2. Check system resource usage and availability",
                "3. Verify external service connectivity and status",
                "4. Test with minimal reproduction case",
                "5. Consider restarting affected services"
            ])
        
        return steps
    
    def _generate_resolution_suggestions(
        self,
        error: Exception,
        error_category: ErrorCategory,
        system_metrics: SystemMetrics
    ) -> List[str]:
        """Generate resolution suggestions based on error and system state."""
        suggestions = []
        
        # High resource usage suggestions
        if system_metrics.cpu_percent > 80:
            suggestions.append("High CPU usage detected - consider scaling or optimizing CPU-intensive operations")
        
        if system_metrics.memory_percent > 85:
            suggestions.append("High memory usage detected - check for memory leaks or consider increasing memory allocation")
        
        if system_metrics.disk_usage_percent > 90:
            suggestions.append("Low disk space detected - clean up logs or temporary files")
        
        # Load average suggestions (Unix-like systems)
        if system_metrics.load_average[0] > psutil.cpu_count():
            suggestions.append("High system load detected - consider reducing concurrent operations")
        
        # Service-specific suggestions
        if error_category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Implement connection pooling and keep-alive for external services",
                "Add circuit breaker pattern for failing external services",
                "Consider increasing timeout values for network operations"
            ])
        
        if error_category == ErrorCategory.RATE_LIMIT:
            suggestions.extend([
                "Implement exponential backoff for rate-limited requests",
                "Consider request queuing to smooth out traffic spikes",
                "Review and optimize API usage patterns"
            ])
        
        if error_category == ErrorCategory.SYSTEM:
            suggestions.extend([
                "Monitor system resources and set up alerting",
                "Implement graceful degradation for resource exhaustion",
                "Consider horizontal scaling for high-load scenarios"
            ])
        
        return suggestions
    
    def _get_formatted_traceback(self, error: Exception) -> str:
        """Get formatted traceback for the error."""
        try:
            return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        except Exception:
            return f"Error getting traceback: {str(error)}"
    
    def _find_related_errors(self, diagnostic: ErrorDiagnostic) -> List[str]:
        """Find related errors in recent history."""
        related = []
        
        # Look for errors in the last 5 minutes with similar characteristics
        cutoff_time = diagnostic.timestamp - timedelta(minutes=5)
        
        for historical_error in self.error_history:
            if historical_error.timestamp < cutoff_time:
                continue
            
            # Check for same error type
            if historical_error.error_type == diagnostic.error_type:
                related.append(f"Similar {diagnostic.error_type} at {historical_error.timestamp.isoformat()}")
            
            # Check for same category
            elif historical_error.error_category == diagnostic.error_category:
                related.append(f"Related {diagnostic.error_category.value} error at {historical_error.timestamp.isoformat()}")
        
        return related[:5]  # Limit to 5 related errors
    
    def _store_diagnostic(self, diagnostic: ErrorDiagnostic):
        """Store diagnostic in history."""
        self.error_history.append(diagnostic)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    async def _log_diagnostic(self, diagnostic: ErrorDiagnostic, level: DiagnosticLevel):
        """Log comprehensive diagnostic information."""
        # Basic error logging
        log_context = {
            'error_id': diagnostic.error_id,
            'error_type': diagnostic.error_type,
            'error_category': diagnostic.error_category.value,
            'error_severity': diagnostic.error_severity.value,
            'correlation_id': diagnostic.correlation_id,
            'system_cpu_percent': diagnostic.system_metrics.cpu_percent,
            'system_memory_percent': diagnostic.system_metrics.memory_percent
        }
        
        # Add service diagnostics
        for service_diag in diagnostic.service_diagnostics:
            log_context[f'{service_diag.service_name}_available'] = service_diag.is_available
            if service_diag.response_time_ms:
                log_context[f'{service_diag.service_name}_response_time_ms'] = service_diag.response_time_ms
        
        # Log based on severity
        log_level = logging.ERROR if diagnostic.error_severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else logging.WARNING
        
        log_with_context(
            logger,
            log_level,
            f"Error diagnostic collected: {diagnostic.error_message}",
            **log_context
        )
        
        # Detailed logging for higher levels
        if level in [DiagnosticLevel.DETAILED, DiagnosticLevel.COMPREHENSIVE]:
            # Log actionable steps
            if diagnostic.actionable_steps:
                log_with_context(
                    logger,
                    logging.INFO,
                    "Actionable troubleshooting steps",
                    error_id=diagnostic.error_id,
                    steps=diagnostic.actionable_steps,
                    correlation_id=diagnostic.correlation_id
                )
            
            # Log resolution suggestions
            if diagnostic.resolution_suggestions:
                log_with_context(
                    logger,
                    logging.INFO,
                    "Resolution suggestions",
                    error_id=diagnostic.error_id,
                    suggestions=diagnostic.resolution_suggestions,
                    correlation_id=diagnostic.correlation_id
                )
        
        # Comprehensive logging
        if level == DiagnosticLevel.COMPREHENSIVE:
            # Log full system metrics
            log_with_context(
                logger,
                logging.DEBUG,
                "System metrics at error time",
                error_id=diagnostic.error_id,
                cpu_percent=diagnostic.system_metrics.cpu_percent,
                memory_percent=diagnostic.system_metrics.memory_percent,
                memory_available_mb=diagnostic.system_metrics.memory_available_mb,
                disk_usage_percent=diagnostic.system_metrics.disk_usage_percent,
                load_average=diagnostic.system_metrics.load_average,
                open_files=diagnostic.system_metrics.open_files,
                network_connections=diagnostic.system_metrics.network_connections,
                correlation_id=diagnostic.correlation_id
            )
            
            # Log stack trace
            log_with_context(
                logger,
                logging.DEBUG,
                "Error stack trace",
                error_id=diagnostic.error_id,
                stack_trace=diagnostic.stack_trace,
                correlation_id=diagnostic.correlation_id
            )
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of errors in the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        error_type_counts = {}
        
        for error in recent_errors:
            category_counts[error.error_category.value] = category_counts.get(error.error_category.value, 0) + 1
            severity_counts[error.error_severity.value] = severity_counts.get(error.error_severity.value, 0) + 1
            error_type_counts[error.error_type] = error_type_counts.get(error.error_type, 0) + 1
        
        return {
            'total_errors': len(recent_errors),
            'time_period_hours': hours,
            'category_breakdown': category_counts,
            'severity_breakdown': severity_counts,
            'error_type_breakdown': error_type_counts,
            'most_recent_error': recent_errors[-1].timestamp.isoformat() if recent_errors else None
        }


# Global diagnostics collector instance
_diagnostics_collector: Optional[ErrorDiagnosticsCollector] = None


def get_diagnostics_collector() -> ErrorDiagnosticsCollector:
    """Get global error diagnostics collector instance."""
    global _diagnostics_collector
    if _diagnostics_collector is None:
        _diagnostics_collector = ErrorDiagnosticsCollector()
    return _diagnostics_collector


async def collect_error_diagnostics(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    diagnostic_level: DiagnosticLevel = DiagnosticLevel.DETAILED
) -> ErrorDiagnostic:
    """
    Collect comprehensive error diagnostics using the global collector.
    
    Args:
        error: The exception that occurred
        context: Additional context about the error
        correlation_id: Correlation ID for tracking
        diagnostic_level: Level of diagnostic detail to collect
        
    Returns:
        ErrorDiagnostic: Comprehensive diagnostic information
    """
    collector = get_diagnostics_collector()
    return await collector.collect_error_diagnostics(error, context, correlation_id, diagnostic_level)