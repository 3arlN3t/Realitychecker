"""
Performance monitoring service for tracking application performance metrics.

This module provides comprehensive performance monitoring, including response times,
throughput, resource usage, and performance alerting.
"""

import time
import asyncio
import psutil
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class WebhookTimingBreakdown:
    """Detailed timing breakdown for webhook processing."""
    total_time: float
    validation_time: float
    signature_validation_time: float
    task_queuing_time: float
    response_preparation_time: float
    cache_lookup_time: float
    redis_operation_time: float
    timestamp: datetime
    message_sid: str
    within_500ms_target: bool
    within_2s_target: bool


@dataclass
class RedisOperationMetric:
    """Redis operation performance metric."""
    operation: str
    latency: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    connection_pool_size: int
    circuit_breaker_state: str


@dataclass
class TaskQueueMetrics:
    """Task queue depth and backpressure metrics."""
    total_depth: int
    high_priority_depth: int
    normal_priority_depth: int
    low_priority_depth: int
    processing_tasks: int
    failed_tasks: int
    average_processing_time: float
    backpressure_detected: bool
    worker_utilization: float
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_id: str
    severity: str  # warning, critical
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    context: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SystemResourceMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    timestamp: datetime


@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    active_requests: int
    requests_per_second: float
    avg_response_time: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    queue_size: int
    timestamp: datetime


class PerformanceMonitor:
    """
    Comprehensive performance monitoring service.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.caching_service = None
        self.pool_manager = None
        
        # Metrics storage
        self.metrics_buffer = deque(maxlen=1000)  # Keep last 1000 metrics
        self.request_times = deque(maxlen=100)    # Keep last 100 request times
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        
        # Enhanced metrics storage for detailed monitoring
        self.webhook_timings = deque(maxlen=500)  # Keep last 500 webhook timings
        self.redis_operations = deque(maxlen=1000)  # Keep last 1000 Redis operations
        self.task_queue_metrics = deque(maxlen=100)  # Keep last 100 queue snapshots
        self.active_alerts = {}  # Active alerts by alert_id
        
        # Performance thresholds - Requirements 4.1, 4.2, 4.3
        self.thresholds = {
            # Webhook response time thresholds (Requirement 4.1)
            "webhook_response_time_warning": 1.0,    # 1 second warning
            "webhook_response_time_critical": 3.0,   # 3 seconds critical
            "webhook_500ms_target": 0.5,             # 500ms target
            "webhook_2s_requirement": 2.0,           # 2s requirement
            
            # Redis operation thresholds (Requirement 4.2)
            "redis_operation_warning": 0.1,          # 100ms warning
            "redis_operation_critical": 0.5,         # 500ms critical
            "redis_failure_rate_warning": 5.0,       # 5% failure rate
            "redis_failure_rate_critical": 10.0,     # 10% failure rate
            
            # Task queue thresholds (Requirement 4.4)
            "task_queue_depth_warning": 500,         # 500 tasks warning
            "task_queue_depth_critical": 800,        # 800 tasks critical
            "task_processing_time_warning": 10.0,    # 10 seconds warning
            "task_processing_time_critical": 30.0,   # 30 seconds critical
            "worker_utilization_warning": 80.0,      # 80% utilization warning
            "worker_utilization_critical": 95.0,     # 95% utilization critical
            
            # System resource thresholds
            "cpu_warning": 80.0,             # 80%
            "cpu_critical": 95.0,            # 95%
            "memory_warning": 80.0,          # 80%
            "memory_critical": 95.0,         # 95%
            "error_rate_warning": 5.0,       # 5%
            "error_rate_critical": 10.0,     # 10%
        }
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_task = None
        self._alert_handlers = []
        
        # Thread-safe counters
        self._lock = threading.Lock()
        self._active_requests = 0
        self._total_requests = 0
        self._total_errors = 0
    
    def _get_caching_service(self):
        """Lazy initialization of caching service to avoid circular imports."""
        if self.caching_service is None:
            from app.services.caching_service import get_caching_service
            self.caching_service = get_caching_service()
        return self.caching_service
    
    def _get_pool_manager(self):
        """Lazy initialization of pool manager to avoid circular imports."""
        if self.pool_manager is None:
            from app.database.connection_pool import get_pool_manager
            self.pool_manager = get_pool_manager()
        return self.pool_manager
    
    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """
        Add alert handler for performance issues.
        
        Args:
            handler: Function to handle alerts
        """
        self._alert_handlers.append(handler)
    
    def record_request_start(self) -> str:
        """
        Record the start of a request.
        
        Returns:
            Request ID for tracking
        """
        with self._lock:
            self._active_requests += 1
            self._total_requests += 1
        
        request_id = f"req_{int(time.time() * 1000000)}"
        return request_id
    
    def record_request_end(self, request_id: str, response_time: float, success: bool = True):
        """
        Record the end of a request.
        
        Args:
            request_id: Request ID from record_request_start
            response_time: Response time in seconds
            success: Whether the request was successful
        """
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            
            if not success:
                self._total_errors += 1
        
        # Record response time
        self.request_times.append(response_time)
        
        # Record metric
        self.record_metric(
            "request_response_time",
            response_time,
            "seconds",
            {"request_id": request_id, "success": str(success)}
        )
        
        # Check for performance alerts with updated thresholds
        if response_time > self.thresholds["webhook_response_time_critical"]:
            self._trigger_alert("critical", f"Very slow response time: {response_time:.2f}s", {
                "response_time": response_time,
                "request_id": request_id,
                "threshold": self.thresholds["webhook_response_time_critical"]
            })
        elif response_time > self.thresholds["webhook_response_time_warning"]:
            self._trigger_alert("warning", f"Slow response time: {response_time:.2f}s", {
                "response_time": response_time,
                "request_id": request_id,
                "threshold": self.thresholds["webhook_response_time_warning"]
            })
    
    def record_webhook_timing_breakdown(self, timing_breakdown: WebhookTimingBreakdown):
        """
        Record detailed webhook timing breakdown for performance analysis.
        
        Implements Requirement 4.1: Add webhook response time tracking with detailed timing breakdowns
        
        Args:
            timing_breakdown: Detailed timing breakdown of webhook processing
        """
        # Store timing breakdown
        self.webhook_timings.append(timing_breakdown)
        
        # Record individual timing metrics
        self.record_metric(
            "webhook_total_time",
            timing_breakdown.total_time,
            "seconds",
            {
                "message_sid": timing_breakdown.message_sid,
                "within_500ms": str(timing_breakdown.within_500ms_target),
                "within_2s": str(timing_breakdown.within_2s_target)
            }
        )
        
        self.record_metric("webhook_validation_time", timing_breakdown.validation_time, "seconds")
        self.record_metric("webhook_signature_validation_time", timing_breakdown.signature_validation_time, "seconds")
        self.record_metric("webhook_task_queuing_time", timing_breakdown.task_queuing_time, "seconds")
        self.record_metric("webhook_cache_lookup_time", timing_breakdown.cache_lookup_time, "seconds")
        self.record_metric("webhook_redis_operation_time", timing_breakdown.redis_operation_time, "seconds")
        
        # Check webhook-specific performance thresholds
        if timing_breakdown.total_time > self.thresholds["webhook_2s_requirement"]:
            self._trigger_alert("critical", 
                f"Webhook exceeded 2-second requirement: {timing_breakdown.total_time:.3f}s", {
                    "total_time": timing_breakdown.total_time,
                    "message_sid": timing_breakdown.message_sid,
                    "requirement": "2.1",
                    "threshold": self.thresholds["webhook_2s_requirement"],
                    "breakdown": {
                        "validation": timing_breakdown.validation_time,
                        "signature_validation": timing_breakdown.signature_validation_time,
                        "task_queuing": timing_breakdown.task_queuing_time,
                        "cache_lookup": timing_breakdown.cache_lookup_time,
                        "redis_operations": timing_breakdown.redis_operation_time
                    }
                })
        elif timing_breakdown.total_time > self.thresholds["webhook_500ms_target"]:
            self._trigger_alert("warning", 
                f"Webhook exceeded 500ms target: {timing_breakdown.total_time:.3f}s", {
                    "total_time": timing_breakdown.total_time,
                    "message_sid": timing_breakdown.message_sid,
                    "requirement": "2.2",
                    "threshold": self.thresholds["webhook_500ms_target"],
                    "breakdown": {
                        "validation": timing_breakdown.validation_time,
                        "signature_validation": timing_breakdown.signature_validation_time,
                        "task_queuing": timing_breakdown.task_queuing_time,
                        "cache_lookup": timing_breakdown.cache_lookup_time,
                        "redis_operations": timing_breakdown.redis_operation_time
                    }
                })
        
        logger.debug(f"Webhook timing recorded: {timing_breakdown.total_time:.3f}s total, "
                    f"validation: {timing_breakdown.validation_time:.3f}s, "
                    f"queuing: {timing_breakdown.task_queuing_time:.3f}s")
    
    def record_redis_operation(self, operation: str, latency: float, success: bool, 
                              error_message: Optional[str] = None, 
                              connection_pool_size: int = 0,
                              circuit_breaker_state: str = "unknown"):
        """
        Record Redis operation performance metrics.
        
        Implements Requirement 4.2: Implement Redis operation monitoring with latency measurements
        
        Args:
            operation: Redis operation name (e.g., 'get', 'set', 'lpush')
            latency: Operation latency in seconds
            success: Whether the operation succeeded
            error_message: Error message if operation failed
            connection_pool_size: Current connection pool size
            circuit_breaker_state: Current circuit breaker state
        """
        redis_metric = RedisOperationMetric(
            operation=operation,
            latency=latency,
            success=success,
            error_message=error_message,
            timestamp=datetime.utcnow(),
            connection_pool_size=connection_pool_size,
            circuit_breaker_state=circuit_breaker_state
        )
        
        # Store Redis operation metric
        self.redis_operations.append(redis_metric)
        
        # Record detailed metrics
        self.record_metric(
            f"redis_operation_latency_{operation}",
            latency,
            "seconds",
            {
                "success": str(success),
                "circuit_breaker_state": circuit_breaker_state,
                "pool_size": str(connection_pool_size)
            }
        )
        
        # Check Redis operation thresholds
        if success:
            if latency > self.thresholds["redis_operation_critical"]:
                self._trigger_alert("critical", 
                    f"Redis {operation} operation very slow: {latency:.3f}s", {
                        "operation": operation,
                        "latency": latency,
                        "threshold": self.thresholds["redis_operation_critical"],
                        "circuit_breaker_state": circuit_breaker_state,
                        "pool_size": connection_pool_size
                    })
            elif latency > self.thresholds["redis_operation_warning"]:
                self._trigger_alert("warning", 
                    f"Redis {operation} operation slow: {latency:.3f}s", {
                        "operation": operation,
                        "latency": latency,
                        "threshold": self.thresholds["redis_operation_warning"],
                        "circuit_breaker_state": circuit_breaker_state,
                        "pool_size": connection_pool_size
                    })
        else:
            # Record Redis operation failure
            self._trigger_alert("warning", 
                f"Redis {operation} operation failed: {error_message}", {
                    "operation": operation,
                    "error": error_message,
                    "circuit_breaker_state": circuit_breaker_state,
                    "pool_size": connection_pool_size
                })
        
        # Check Redis failure rate
        self._check_redis_failure_rate()
        
        logger.debug(f"Redis operation recorded: {operation} - {latency:.3f}s - {'success' if success else 'failed'}")
    
    def record_task_queue_metrics(self, queue_metrics: TaskQueueMetrics):
        """
        Record task queue depth and backpressure metrics.
        
        Implements Requirement 4.4: Add task queue depth monitoring and backpressure detection
        
        Args:
            queue_metrics: Task queue metrics snapshot
        """
        # Store queue metrics
        self.task_queue_metrics.append(queue_metrics)
        
        # Record individual queue metrics
        self.record_metric("task_queue_total_depth", queue_metrics.total_depth, "count")
        self.record_metric("task_queue_high_priority_depth", queue_metrics.high_priority_depth, "count")
        self.record_metric("task_queue_normal_priority_depth", queue_metrics.normal_priority_depth, "count")
        self.record_metric("task_queue_low_priority_depth", queue_metrics.low_priority_depth, "count")
        self.record_metric("task_queue_processing_tasks", queue_metrics.processing_tasks, "count")
        self.record_metric("task_queue_failed_tasks", queue_metrics.failed_tasks, "count")
        self.record_metric("task_queue_avg_processing_time", queue_metrics.average_processing_time, "seconds")
        self.record_metric("task_queue_worker_utilization", queue_metrics.worker_utilization, "percent")
        
        # Check task queue thresholds
        if queue_metrics.total_depth > self.thresholds["task_queue_depth_critical"]:
            self._trigger_alert("critical", 
                f"Task queue depth critical: {queue_metrics.total_depth} tasks", {
                    "total_depth": queue_metrics.total_depth,
                    "high_priority": queue_metrics.high_priority_depth,
                    "normal_priority": queue_metrics.normal_priority_depth,
                    "low_priority": queue_metrics.low_priority_depth,
                    "threshold": self.thresholds["task_queue_depth_critical"],
                    "backpressure_detected": queue_metrics.backpressure_detected
                })
        elif queue_metrics.total_depth > self.thresholds["task_queue_depth_warning"]:
            self._trigger_alert("warning", 
                f"Task queue depth high: {queue_metrics.total_depth} tasks", {
                    "total_depth": queue_metrics.total_depth,
                    "high_priority": queue_metrics.high_priority_depth,
                    "normal_priority": queue_metrics.normal_priority_depth,
                    "low_priority": queue_metrics.low_priority_depth,
                    "threshold": self.thresholds["task_queue_depth_warning"],
                    "backpressure_detected": queue_metrics.backpressure_detected
                })
        
        # Check worker utilization
        if queue_metrics.worker_utilization > self.thresholds["worker_utilization_critical"]:
            self._trigger_alert("critical", 
                f"Worker utilization critical: {queue_metrics.worker_utilization:.1f}%", {
                    "worker_utilization": queue_metrics.worker_utilization,
                    "processing_tasks": queue_metrics.processing_tasks,
                    "threshold": self.thresholds["worker_utilization_critical"]
                })
        elif queue_metrics.worker_utilization > self.thresholds["worker_utilization_warning"]:
            self._trigger_alert("warning", 
                f"Worker utilization high: {queue_metrics.worker_utilization:.1f}%", {
                    "worker_utilization": queue_metrics.worker_utilization,
                    "processing_tasks": queue_metrics.processing_tasks,
                    "threshold": self.thresholds["worker_utilization_warning"]
                })
        
        # Check average processing time
        if queue_metrics.average_processing_time > self.thresholds["task_processing_time_critical"]:
            self._trigger_alert("critical", 
                f"Task processing time critical: {queue_metrics.average_processing_time:.1f}s", {
                    "average_processing_time": queue_metrics.average_processing_time,
                    "threshold": self.thresholds["task_processing_time_critical"]
                })
        elif queue_metrics.average_processing_time > self.thresholds["task_processing_time_warning"]:
            self._trigger_alert("warning", 
                f"Task processing time high: {queue_metrics.average_processing_time:.1f}s", {
                    "average_processing_time": queue_metrics.average_processing_time,
                    "threshold": self.thresholds["task_processing_time_warning"]
                })
        
        # Check for backpressure
        if queue_metrics.backpressure_detected:
            self._trigger_alert("warning", 
                "Task queue backpressure detected", {
                    "total_depth": queue_metrics.total_depth,
                    "worker_utilization": queue_metrics.worker_utilization,
                    "average_processing_time": queue_metrics.average_processing_time
                })
        
        logger.debug(f"Task queue metrics recorded: depth={queue_metrics.total_depth}, "
                    f"utilization={queue_metrics.worker_utilization:.1f}%, "
                    f"backpressure={queue_metrics.backpressure_detected}")
    
    def _check_redis_failure_rate(self):
        """Check Redis failure rate and trigger alerts if thresholds exceeded."""
        if len(self.redis_operations) < 10:  # Need at least 10 operations for meaningful rate
            return
        
        # Calculate failure rate over last 100 operations
        recent_operations = list(self.redis_operations)[-100:]
        total_operations = len(recent_operations)
        failed_operations = sum(1 for op in recent_operations if not op.success)
        failure_rate = (failed_operations / total_operations) * 100
        
        if failure_rate > self.thresholds["redis_failure_rate_critical"]:
            self._trigger_alert("critical", 
                f"Redis failure rate critical: {failure_rate:.1f}%", {
                    "failure_rate": failure_rate,
                    "failed_operations": failed_operations,
                    "total_operations": total_operations,
                    "threshold": self.thresholds["redis_failure_rate_critical"]
                })
        elif failure_rate > self.thresholds["redis_failure_rate_warning"]:
            self._trigger_alert("warning", 
                f"Redis failure rate high: {failure_rate:.1f}%", {
                    "failure_rate": failure_rate,
                    "failed_operations": failed_operations,
                    "total_operations": total_operations,
                    "threshold": self.thresholds["redis_failure_rate_warning"]
                })
    
    def record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Metric unit
            tags: Optional tags for the metric
        """
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics_buffer.append(metric)
        logger.debug(f"Recorded metric: {name}={value}{unit}")
    
    async def get_system_metrics(self) -> SystemResourceMetrics:
        """
        Get current system resource metrics.
        
        Returns:
            SystemResourceMetrics object
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network statistics
            network = psutil.net_io_counters()
            
            # Database connections
            pool_manager = self._get_pool_manager()
            pool_stats = await pool_manager.get_pool_stats()
            active_connections = pool_stats.get("active_connections", 0)
            
            metrics = SystemResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=active_connections,
                timestamp=datetime.utcnow()
            )
            
            # Check for system resource alerts
            if cpu_percent > self.thresholds["cpu_critical"]:
                self._trigger_alert("critical", f"Critical CPU usage: {cpu_percent:.1f}%", {
                    "cpu_percent": cpu_percent,
                    "threshold": self.thresholds["cpu_critical"]
                })
            elif cpu_percent > self.thresholds["cpu_warning"]:
                self._trigger_alert("warning", f"High CPU usage: {cpu_percent:.1f}%", {
                    "cpu_percent": cpu_percent,
                    "threshold": self.thresholds["cpu_warning"]
                })
            
            if memory.percent > self.thresholds["memory_critical"]:
                self._trigger_alert("critical", f"Critical memory usage: {memory.percent:.1f}%", {
                    "memory_percent": memory.percent,
                    "threshold": self.thresholds["memory_critical"]
                })
            elif memory.percent > self.thresholds["memory_warning"]:
                self._trigger_alert("warning", f"High memory usage: {memory.percent:.1f}%", {
                    "memory_percent": memory.percent,
                    "threshold": self.thresholds["memory_warning"]
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            # Return default metrics on error
            return SystemResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                active_connections=0,
                timestamp=datetime.utcnow()
            )
    
    async def get_application_metrics(self) -> ApplicationMetrics:
        """
        Get current application metrics.
        
        Returns:
            ApplicationMetrics object
        """
        try:
            # Calculate requests per second (last minute)
            current_time = time.time()
            recent_requests = sum(1 for t in self.request_times if current_time - t < 60)
            requests_per_second = recent_requests / 60.0
            
            # Calculate average response time
            if self.request_times:
                avg_response_time = sum(self.request_times) / len(self.request_times)
            else:
                avg_response_time = 0.0
            
            # Calculate error rate
            if self._total_requests > 0:
                error_rate = (self._total_errors / self._total_requests) * 100
            else:
                error_rate = 0.0
            
            # Get cache hit rate
            caching_service = self._get_caching_service()
            cache_stats = await caching_service.get_cache_stats()
            cache_hit_rate = cache_stats.get("hit_rate", 0.0)
            
            # Get database connection count
            pool_manager = self._get_pool_manager()
            pool_stats = await pool_manager.get_pool_stats()
            database_connections = pool_stats.get("active_connections", 0)
            
            metrics = ApplicationMetrics(
                active_requests=self._active_requests,
                requests_per_second=requests_per_second,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                cache_hit_rate=cache_hit_rate,
                database_connections=database_connections,
                queue_size=0,  # TODO: Implement queue monitoring
                timestamp=datetime.utcnow()
            )
            
            # Check for application alerts
            if error_rate > self.thresholds["error_rate_critical"]:
                self._trigger_alert("critical", f"Critical error rate: {error_rate:.1f}%", {
                    "error_rate": error_rate,
                    "threshold": self.thresholds["error_rate_critical"]
                })
            elif error_rate > self.thresholds["error_rate_warning"]:
                self._trigger_alert("warning", f"High error rate: {error_rate:.1f}%", {
                    "error_rate": error_rate,
                    "threshold": self.thresholds["error_rate_warning"]
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get application metrics: {e}")
            # Return default metrics on error
            return ApplicationMetrics(
                active_requests=0,
                requests_per_second=0.0,
                avg_response_time=0.0,
                error_rate=0.0,
                cache_hit_rate=0.0,
                database_connections=0,
                queue_size=0,
                timestamp=datetime.utcnow()
            )
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary with enhanced metrics.
        
        Returns:
            Dictionary with performance summary
        """
        system_metrics = await self.get_system_metrics()
        app_metrics = await self.get_application_metrics()
        
        # Get recent metrics from buffer
        recent_metrics = [m for m in self.metrics_buffer if 
                         (datetime.utcnow() - m.timestamp).total_seconds() < 300]  # Last 5 minutes
        
        # Get webhook timing summary
        webhook_summary = self.get_webhook_timing_summary()
        
        # Get Redis operation summary
        redis_summary = self.get_redis_operation_summary()
        
        # Get task queue summary
        task_queue_summary = self.get_task_queue_summary()
        
        # Get alert summary
        alert_summary = self.get_alert_summary()
        
        return {
            "system": asdict(system_metrics),
            "application": asdict(app_metrics),
            "webhook_performance": webhook_summary,
            "redis_performance": redis_summary,
            "task_queue_performance": task_queue_summary,
            "alerts": alert_summary,
            "recent_metrics_count": len(recent_metrics),
            "monitoring_active": self._monitoring_active,
            "thresholds": self.thresholds,
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "buffer_size": len(self.metrics_buffer)
        }
    
    def get_webhook_timing_summary(self) -> Dict[str, Any]:
        """
        Get detailed webhook timing analysis.
        
        Implements Requirement 4.1: Add webhook response time tracking with detailed timing breakdowns
        
        Returns:
            Dictionary with webhook timing analysis
        """
        if not self.webhook_timings:
            return {
                "total_webhooks": 0,
                "average_total_time": 0.0,
                "p50_total_time": 0.0,
                "p95_total_time": 0.0,
                "p99_total_time": 0.0,
                "within_500ms_percentage": 0.0,
                "within_2s_percentage": 0.0,
                "timing_breakdown": {}
            }
        
        timings = list(self.webhook_timings)
        total_times = [t.total_time for t in timings]
        total_times.sort()
        
        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return 0.0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] * (1 - c) + data[f + 1] * c
            return data[f]
        
        p50 = percentile(total_times, 50)
        p95 = percentile(total_times, 95)
        p99 = percentile(total_times, 99)
        
        # Calculate target compliance
        within_500ms = sum(1 for t in timings if t.within_500ms_target)
        within_2s = sum(1 for t in timings if t.within_2s_target)
        
        # Calculate average breakdown times
        avg_breakdown = {
            "validation_time": sum(t.validation_time for t in timings) / len(timings),
            "signature_validation_time": sum(t.signature_validation_time for t in timings) / len(timings),
            "task_queuing_time": sum(t.task_queuing_time for t in timings) / len(timings),
            "response_preparation_time": sum(t.response_preparation_time for t in timings) / len(timings),
            "cache_lookup_time": sum(t.cache_lookup_time for t in timings) / len(timings),
            "redis_operation_time": sum(t.redis_operation_time for t in timings) / len(timings)
        }
        
        return {
            "total_webhooks": len(timings),
            "average_total_time": sum(total_times) / len(total_times),
            "p50_total_time": p50,
            "p95_total_time": p95,
            "p99_total_time": p99,
            "within_500ms_percentage": (within_500ms / len(timings)) * 100,
            "within_2s_percentage": (within_2s / len(timings)) * 100,
            "timing_breakdown": avg_breakdown,
            "recent_timings": [
                {
                    "message_sid": t.message_sid,
                    "total_time": t.total_time,
                    "within_500ms": t.within_500ms_target,
                    "within_2s": t.within_2s_target,
                    "timestamp": t.timestamp.isoformat()
                }
                for t in timings[-10:]  # Last 10 webhook calls
            ]
        }
    
    def get_redis_operation_summary(self) -> Dict[str, Any]:
        """
        Get Redis operation performance summary.
        
        Implements Requirement 4.2: Implement Redis operation monitoring with latency measurements
        
        Returns:
            Dictionary with Redis operation analysis
        """
        if not self.redis_operations:
            return {
                "total_operations": 0,
                "success_rate": 0.0,
                "average_latency": 0.0,
                "operations_by_type": {},
                "circuit_breaker_trips": 0
            }
        
        operations = list(self.redis_operations)
        successful_ops = [op for op in operations if op.success]
        failed_ops = [op for op in operations if not op.success]
        
        # Calculate success rate
        success_rate = (len(successful_ops) / len(operations)) * 100 if operations else 0
        
        # Calculate average latency for successful operations
        avg_latency = sum(op.latency for op in successful_ops) / len(successful_ops) if successful_ops else 0
        
        # Group by operation type
        operations_by_type = {}
        for op in operations:
            if op.operation not in operations_by_type:
                operations_by_type[op.operation] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "avg_latency": 0.0,
                    "max_latency": 0.0
                }
            
            op_stats = operations_by_type[op.operation]
            op_stats["total"] += 1
            
            if op.success:
                op_stats["successful"] += 1
                current_avg = op_stats["avg_latency"]
                op_stats["avg_latency"] = (current_avg * (op_stats["successful"] - 1) + op.latency) / op_stats["successful"]
                op_stats["max_latency"] = max(op_stats["max_latency"], op.latency)
            else:
                op_stats["failed"] += 1
        
        # Count circuit breaker state changes
        circuit_breaker_trips = len([op for op in operations if op.circuit_breaker_state == "open"])
        
        return {
            "total_operations": len(operations),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": success_rate,
            "average_latency": avg_latency,
            "operations_by_type": operations_by_type,
            "circuit_breaker_trips": circuit_breaker_trips,
            "recent_operations": [
                {
                    "operation": op.operation,
                    "latency": op.latency,
                    "success": op.success,
                    "error": op.error_message,
                    "circuit_breaker_state": op.circuit_breaker_state,
                    "timestamp": op.timestamp.isoformat()
                }
                for op in operations[-20:]  # Last 20 operations
            ]
        }
    
    def get_task_queue_summary(self) -> Dict[str, Any]:
        """
        Get task queue performance summary.
        
        Implements Requirement 4.4: Add task queue depth monitoring and backpressure detection
        
        Returns:
            Dictionary with task queue analysis
        """
        if not self.task_queue_metrics:
            return {
                "current_depth": 0,
                "average_depth": 0.0,
                "max_depth": 0,
                "backpressure_events": 0,
                "average_processing_time": 0.0,
                "worker_utilization": 0.0
            }
        
        metrics = list(self.task_queue_metrics)
        latest_metrics = metrics[-1] if metrics else None
        
        # Calculate averages
        avg_depth = sum(m.total_depth for m in metrics) / len(metrics)
        max_depth = max(m.total_depth for m in metrics)
        avg_processing_time = sum(m.average_processing_time for m in metrics) / len(metrics)
        avg_worker_utilization = sum(m.worker_utilization for m in metrics) / len(metrics)
        
        # Count backpressure events
        backpressure_events = sum(1 for m in metrics if m.backpressure_detected)
        
        return {
            "current_depth": latest_metrics.total_depth if latest_metrics else 0,
            "current_high_priority": latest_metrics.high_priority_depth if latest_metrics else 0,
            "current_normal_priority": latest_metrics.normal_priority_depth if latest_metrics else 0,
            "current_low_priority": latest_metrics.low_priority_depth if latest_metrics else 0,
            "average_depth": avg_depth,
            "max_depth": max_depth,
            "backpressure_events": backpressure_events,
            "average_processing_time": avg_processing_time,
            "current_processing_time": latest_metrics.average_processing_time if latest_metrics else 0,
            "worker_utilization": avg_worker_utilization,
            "current_worker_utilization": latest_metrics.worker_utilization if latest_metrics else 0,
            "processing_tasks": latest_metrics.processing_tasks if latest_metrics else 0,
            "failed_tasks": latest_metrics.failed_tasks if latest_metrics else 0,
            "backpressure_detected": latest_metrics.backpressure_detected if latest_metrics else False,
            "recent_snapshots": [
                {
                    "total_depth": m.total_depth,
                    "processing_tasks": m.processing_tasks,
                    "worker_utilization": m.worker_utilization,
                    "backpressure_detected": m.backpressure_detected,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in metrics[-10:]  # Last 10 snapshots
            ]
        }
    
    def _trigger_alert(self, severity: str, message: str, context: Dict[str, Any]):
        """
        Trigger performance alert with enhanced alert management.
        
        Implements Requirement 4.3: Create performance threshold alerts for critical metrics
        
        Args:
            severity: Alert severity (warning, critical)
            message: Alert message
            context: Alert context data
        """
        import uuid
        
        # Create alert ID based on metric and context to prevent duplicate alerts
        metric_key = context.get('operation', context.get('metric_name', 'unknown'))
        alert_key = f"{severity}_{metric_key}_{hash(message)}"
        
        # Check if similar alert is already active (prevent spam)
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            # Update existing alert timestamp and context
            existing_alert.timestamp = datetime.utcnow()
            existing_alert.context.update(context)
            return
        
        # Create new alert
        alert = PerformanceAlert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            metric_name=metric_key,
            current_value=context.get('latency', context.get('total_depth', context.get('response_time', 0))),
            threshold_value=context.get('threshold', 0),
            message=message,
            context=context,
            timestamp=datetime.utcnow()
        )
        
        # Store active alert
        self.active_alerts[alert_key] = alert
        
        # Enhanced alert data
        alert_data = {
            "alert_id": alert.alert_id,
            "severity": severity,
            "message": message,
            "context": context,
            "timestamp": alert.timestamp.isoformat(),
            "component": "performance_monitor",
            "metric_name": metric_key,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value
        }
        
        # Log alert with appropriate level
        if severity == "critical":
            logger.error(f"🚨 CRITICAL Performance Alert: {message}")
        else:
            logger.warning(f"⚠️  Performance Alert [{severity}]: {message}")
        
        # Record alert as metric
        self.record_metric(
            f"alert_{severity}_triggered",
            1,
            "count",
            {"metric": metric_key, "alert_id": alert.alert_id}
        )
        
        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                handler(message, alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        # Auto-resolve alerts after some time for transient issues
        asyncio.create_task(self._schedule_alert_resolution(alert_key, alert, 300))  # 5 minutes
    
    async def _schedule_alert_resolution(self, alert_key: str, alert: PerformanceAlert, delay_seconds: int):
        """Schedule automatic alert resolution for transient issues."""
        try:
            await asyncio.sleep(delay_seconds)
            
            # Check if alert is still active and should be auto-resolved
            if alert_key in self.active_alerts and not self.active_alerts[alert_key].resolved:
                # Check if the condition that triggered the alert has been resolved
                should_resolve = await self._check_alert_resolution_condition(alert)
                
                if should_resolve:
                    self.resolve_alert(alert_key, "Auto-resolved: condition no longer met")
        except Exception as e:
            logger.error(f"Error in alert resolution scheduling: {e}")
    
    async def _check_alert_resolution_condition(self, alert: PerformanceAlert) -> bool:
        """Check if the condition that triggered an alert has been resolved."""
        try:
            # For webhook response time alerts
            if "webhook" in alert.metric_name and "response_time" in alert.context:
                recent_timings = list(self.webhook_timings)[-10:]  # Last 10 webhook calls
                if recent_timings:
                    avg_recent_time = sum(t.total_time for t in recent_timings) / len(recent_timings)
                    return avg_recent_time <= alert.threshold_value
            
            # For Redis operation alerts
            elif "redis" in alert.metric_name and "latency" in alert.context:
                recent_ops = [op for op in self.redis_operations if op.operation == alert.context.get('operation', '')][-10:]
                if recent_ops:
                    avg_recent_latency = sum(op.latency for op in recent_ops if op.success) / max(1, len([op for op in recent_ops if op.success]))
                    return avg_recent_latency <= alert.threshold_value
            
            # For task queue alerts
            elif "task_queue" in alert.metric_name:
                recent_metrics = list(self.task_queue_metrics)[-3:]  # Last 3 snapshots
                if recent_metrics:
                    if "depth" in alert.metric_name:
                        avg_depth = sum(m.total_depth for m in recent_metrics) / len(recent_metrics)
                        return avg_depth <= alert.threshold_value
                    elif "utilization" in alert.metric_name:
                        avg_util = sum(m.worker_utilization for m in recent_metrics) / len(recent_metrics)
                        return avg_util <= alert.threshold_value
            
            return False
        except Exception as e:
            logger.error(f"Error checking alert resolution condition: {e}")
            return False
    
    def resolve_alert(self, alert_key: str, resolution_message: str = "Manually resolved"):
        """
        Resolve an active alert.
        
        Args:
            alert_key: Alert key to resolve
            resolution_message: Message describing how the alert was resolved
        """
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            logger.info(f"✅ Alert resolved: {alert.message} - {resolution_message}")
            
            # Record alert resolution
            self.record_metric(
                f"alert_{alert.severity}_resolved",
                1,
                "count",
                {"metric": alert.metric_name, "alert_id": alert.alert_id}
            )
            
            # Remove from active alerts
            del self.active_alerts[alert_key]
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """
        Get list of currently active alerts.
        
        Returns:
            List of active performance alerts
        """
        return list(self.active_alerts.values())
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get summary of alert activity.
        
        Returns:
            Dictionary with alert summary statistics
        """
        active_alerts = list(self.active_alerts.values())
        
        return {
            "total_active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in active_alerts if a.severity == "warning"]),
            "alerts_by_metric": {
                metric: len([a for a in active_alerts if a.metric_name == metric])
                for metric in set(a.metric_name for a in active_alerts)
            },
            "oldest_alert": min([a.timestamp for a in active_alerts], default=None),
            "newest_alert": max([a.timestamp for a in active_alerts], default=None)
        }
    
    async def start_monitoring(self, interval: int = 30):
        """
        Start continuous performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            logger.warning("Performance monitoring is already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info(f"Started performance monitoring with {interval}s interval")
    
    async def stop_monitoring(self):
        """Stop continuous performance monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self, interval: int):
        """
        Main monitoring loop.
        
        Args:
            interval: Monitoring interval in seconds
        """
        while self._monitoring_active:
            try:
                # Collect system metrics
                system_metrics = await self.get_system_metrics()
                self.record_metric("cpu_percent", system_metrics.cpu_percent, "%")
                self.record_metric("memory_percent", system_metrics.memory_percent, "%")
                self.record_metric("disk_usage_percent", system_metrics.disk_usage_percent, "%")
                
                # Collect application metrics
                app_metrics = await self.get_application_metrics()
                self.record_metric("active_requests", app_metrics.active_requests, "count")
                self.record_metric("requests_per_second", app_metrics.requests_per_second, "rps")
                self.record_metric("avg_response_time", app_metrics.avg_response_time, "seconds")
                self.record_metric("error_rate", app_metrics.error_rate, "%")
                self.record_metric("cache_hit_rate", app_metrics.cache_hit_rate, "%")
                
                # Cache the metrics for dashboard
                caching_service = self._get_caching_service()
                await caching_service.set(
                    "performance:system_metrics",
                    asdict(system_metrics),
                    60  # 1 minute TTL
                )
                
                await caching_service.set(
                    "performance:app_metrics",
                    asdict(app_metrics),
                    60  # 1 minute TTL
                )
                
                logger.debug("Performance metrics collected and cached")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next interval
            await asyncio.sleep(interval)
    
    async def cleanup(self):
        """Clean up monitoring resources."""
        await self.stop_monitoring()
        self.metrics_buffer.clear()
        self.request_times.clear()
        self.error_counts.clear()
        self.request_counts.clear()
        logger.info("Performance monitor cleaned up")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


async def init_performance_monitor():
    """Initialize and start performance monitoring."""
    monitor = get_performance_monitor()
    await monitor.start_monitoring(30)  # 30-second intervals
    return monitor