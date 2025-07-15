"""
Application metrics collection for performance monitoring and observability.

This module provides metrics collection capabilities including request counters,
response times, error rates, and service health metrics.
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Deque
from contextlib import contextmanager
from enum import Enum

from app.utils.logging import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class MetricsCollector:
    """Thread-safe metrics collector for application observability."""
    
    def __init__(self, max_points_per_metric: int = 1000):
        """
        Initialize the metrics collector.
        
        Args:
            max_points_per_metric: Maximum number of data points to keep per metric
        """
        self.max_points = max_points_per_metric
        self._lock = threading.RLock()
        self._metrics: Dict[str, Deque[MetricPoint]] = defaultdict(
            lambda: deque(maxlen=self.max_points)
        )
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        
        # Request metrics
        self.request_count = 0
        self.error_count = 0
        self.response_times: Deque[float] = deque(maxlen=1000)
        
        # Service metrics
        self.service_calls: Dict[str, int] = defaultdict(int)
        self.service_errors: Dict[str, int] = defaultdict(int)
        self.service_response_times: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=100)
        )
        
        logger.info("Metrics collector initialized")
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._counters[key] += value
            
            # Also store as time series data
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.now(timezone.utc),
                value=self._counters[key],
                labels=labels or {}
            ))
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Current value
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._gauges[key] = value
            
            # Also store as time series data
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.now(timezone.utc),
                value=value,
                labels=labels or {}
            ))
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a histogram metric value.
        
        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.now(timezone.utc),
                value=value,
                labels=labels or {}
            ))
    
    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Args:
            name: Metric name
            labels: Optional labels for the metric
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_histogram(f"{name}_duration_seconds", duration, labels)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """
        Record HTTP request metrics.
        
        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        with self._lock:
            self.request_count += 1
            self.response_times.append(duration)
            
            if status_code >= 400:
                self.error_count += 1
            
            # Record detailed metrics
            labels = {
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code)
            }
            
            self.increment_counter("http_requests_total", labels=labels)
            self.record_histogram("http_request_duration_seconds", duration, labels)
            
            if status_code >= 400:
                self.increment_counter("http_requests_errors_total", labels=labels)
    
    def record_service_call(self, service: str, operation: str, success: bool, duration: float):
        """
        Record external service call metrics.
        
        Args:
            service: Service name (e.g., 'openai', 'twilio')
            operation: Operation name (e.g., 'analyze', 'send_message')
            success: Whether the call was successful
            duration: Call duration in seconds
        """
        with self._lock:
            key = f"{service}_{operation}"
            self.service_calls[key] += 1
            self.service_response_times[key].append(duration)
            
            if not success:
                self.service_errors[key] += 1
            
            # Record detailed metrics
            labels = {
                "service": service,
                "operation": operation,
                "success": str(success).lower()
            }
            
            self.increment_counter("service_calls_total", labels=labels)
            self.record_histogram("service_call_duration_seconds", duration, labels)
            
            if not success:
                self.increment_counter("service_calls_errors_total", labels=labels)
    
    def get_metric_summary(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.
        
        Args:
            name: Metric name
            labels: Optional labels filter
            
        Returns:
            MetricSummary or None if metric not found
        """
        with self._lock:
            key = self._build_metric_key(name, labels)
            points = self._metrics.get(key)
            
            if not points:
                return None
            
            values = [p.value for p in points]
            values.sort()
            
            count = len(values)
            if count == 0:
                return None
            
            return MetricSummary(
                count=count,
                sum=sum(values),
                min=min(values),
                max=max(values),
                avg=sum(values) / count,
                p50=self._percentile(values, 0.5),
                p95=self._percentile(values, 0.95),
                p99=self._percentile(values, 0.99)
            )
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary containing current metrics
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            
            # Calculate error rate
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            # Calculate average response time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            # Service health metrics
            service_health = {}
            for service_op, calls in self.service_calls.items():
                errors = self.service_errors.get(service_op, 0)
                error_rate_service = (errors / max(calls, 1)) * 100
                
                response_times = self.service_response_times.get(service_op, [])
                avg_time = sum(response_times) / len(response_times) if response_times else 0
                
                service_health[service_op] = {
                    "total_calls": calls,
                    "errors": errors,
                    "error_rate_percent": round(error_rate_service, 2),
                    "avg_response_time_seconds": round(avg_time, 3)
                }
            
            return {
                "timestamp": now.isoformat(),
                "uptime_seconds": (now - datetime.now(timezone.utc)).total_seconds(),
                "requests": {
                    "total": self.request_count,
                    "errors": self.error_count,
                    "error_rate_percent": round(error_rate, 2),
                    "avg_response_time_seconds": round(avg_response_time, 3)
                },
                "services": service_health,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges)
            }
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """
        Clean up old metric data points.
        
        Args:
            max_age_hours: Maximum age of metrics to keep in hours
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        with self._lock:
            for metric_name, points in self._metrics.items():
                # Remove old points
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()
            
            logger.info(f"Cleaned up metrics older than {max_age_hours} hours")
    
    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Build a unique key for a metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0.0
        
        index = int(percentile * (len(values) - 1))
        return values[index]


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector():
    """Reset the global metrics collector (useful for testing)."""
    global _metrics_collector
    _metrics_collector = None