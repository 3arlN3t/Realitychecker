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
        
        # Performance thresholds
        self.thresholds = {
            "response_time_warning": 2.0,    # 2 seconds
            "response_time_critical": 5.0,   # 5 seconds
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
        
        # Check for performance alerts
        if response_time > self.thresholds["response_time_critical"]:
            self._trigger_alert("critical", f"Very slow response time: {response_time:.2f}s", {
                "response_time": response_time,
                "request_id": request_id,
                "threshold": self.thresholds["response_time_critical"]
            })
        elif response_time > self.thresholds["response_time_warning"]:
            self._trigger_alert("warning", f"Slow response time: {response_time:.2f}s", {
                "response_time": response_time,
                "request_id": request_id,
                "threshold": self.thresholds["response_time_warning"]
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
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        system_metrics = await self.get_system_metrics()
        app_metrics = await self.get_application_metrics()
        
        # Get recent metrics from buffer
        recent_metrics = [m for m in self.metrics_buffer if 
                         (datetime.utcnow() - m.timestamp).total_seconds() < 300]  # Last 5 minutes
        
        return {
            "system": asdict(system_metrics),
            "application": asdict(app_metrics),
            "recent_metrics_count": len(recent_metrics),
            "monitoring_active": self._monitoring_active,
            "thresholds": self.thresholds,
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "buffer_size": len(self.metrics_buffer)
        }
    
    def _trigger_alert(self, severity: str, message: str, context: Dict[str, Any]):
        """
        Trigger performance alert.
        
        Args:
            severity: Alert severity (warning, critical)
            message: Alert message
            context: Alert context data
        """
        alert_data = {
            "severity": severity,
            "message": message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "component": "performance_monitor"
        }
        
        logger.warning(f"Performance alert [{severity}]: {message}")
        
        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                handler(message, alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
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