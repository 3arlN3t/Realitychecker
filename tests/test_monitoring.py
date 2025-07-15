"""
Tests for monitoring and observability features.

This module tests metrics collection, error tracking, and health check functionality.
"""

import pytest
import time
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.utils.metrics import MetricsCollector, get_metrics_collector, reset_metrics_collector
from app.utils.error_tracking import (
    ErrorTracker, Alert, AlertType, AlertSeverity, 
    get_error_tracker, reset_error_tracker, log_alert_handler
)
from app.api.health import check_openai_health, check_twilio_health
from app.config import AppConfig


class TestMetricsCollector:
    """Test cases for the MetricsCollector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics_collector()
        self.metrics = MetricsCollector()
    
    def test_increment_counter(self):
        """Test counter increment functionality."""
        # Test basic counter increment
        self.metrics.increment_counter("test_counter")
        assert self.metrics._counters["test_counter"] == 1.0
        
        # Test increment with custom value
        self.metrics.increment_counter("test_counter", 5.0)
        assert self.metrics._counters["test_counter"] == 6.0
        
        # Test counter with labels
        self.metrics.increment_counter("http_requests", 1.0, {"method": "GET", "status": "200"})
        key = "http_requests{method=GET,status=200}"
        assert self.metrics._counters[key] == 1.0
    
    def test_set_gauge(self):
        """Test gauge setting functionality."""
        # Test basic gauge
        self.metrics.set_gauge("memory_usage", 75.5)
        assert self.metrics._gauges["memory_usage"] == 75.5
        
        # Test gauge with labels
        self.metrics.set_gauge("cpu_usage", 45.2, {"core": "0"})
        key = "cpu_usage{core=0}"
        assert self.metrics._gauges[key] == 45.2
    
    def test_record_histogram(self):
        """Test histogram recording functionality."""
        # Record some values
        self.metrics.record_histogram("response_time", 0.5)
        self.metrics.record_histogram("response_time", 1.2)
        self.metrics.record_histogram("response_time", 0.8)
        
        # Check that values are stored
        points = self.metrics._metrics["response_time"]
        assert len(points) == 3
        assert points[0].value == 0.5
        assert points[1].value == 1.2
        assert points[2].value == 0.8
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        with self.metrics.timer("operation_duration"):
            time.sleep(0.1)  # Sleep for 100ms
        
        # Check that duration was recorded
        points = self.metrics._metrics["operation_duration_duration_seconds"]
        assert len(points) == 1
        assert points[0].value >= 0.1  # Should be at least 100ms
    
    def test_record_request(self):
        """Test HTTP request recording."""
        self.metrics.record_request("GET", "/api/test", 200, 0.5)
        
        # Check counters
        assert self.metrics.request_count == 1
        assert self.metrics.error_count == 0
        assert len(self.metrics.response_times) == 1
        assert self.metrics.response_times[0] == 0.5
        
        # Test error request
        self.metrics.record_request("POST", "/api/error", 500, 1.0)
        assert self.metrics.request_count == 2
        assert self.metrics.error_count == 1
    
    def test_record_service_call(self):
        """Test service call recording."""
        # Successful call
        self.metrics.record_service_call("openai", "analyze", True, 2.5)
        
        assert self.metrics.service_calls["openai_analyze"] == 1
        assert self.metrics.service_errors["openai_analyze"] == 0
        assert len(self.metrics.service_response_times["openai_analyze"]) == 1
        
        # Failed call
        self.metrics.record_service_call("openai", "analyze", False, 5.0)
        
        assert self.metrics.service_calls["openai_analyze"] == 2
        assert self.metrics.service_errors["openai_analyze"] == 1
    
    def test_get_metric_summary(self):
        """Test metric summary calculation."""
        # Record some values
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for value in values:
            self.metrics.record_histogram("test_metric", value)
        
        summary = self.metrics.get_metric_summary("test_metric")
        
        assert summary is not None
        assert summary.count == 5
        assert summary.sum == 15.0
        assert summary.min == 1.0
        assert summary.max == 5.0
        assert summary.avg == 3.0
        assert summary.p50 == 3.0
    
    def test_get_current_metrics(self):
        """Test current metrics snapshot."""
        # Record some data
        self.metrics.record_request("GET", "/test", 200, 0.5)
        self.metrics.record_service_call("openai", "analyze", True, 1.0)
        
        metrics = self.metrics.get_current_metrics()
        
        assert "timestamp" in metrics
        assert "requests" in metrics
        assert "services" in metrics
        assert metrics["requests"]["total"] == 1
        assert metrics["requests"]["errors"] == 0
        assert "openai_analyze" in metrics["services"]
    
    def test_cleanup_old_metrics(self):
        """Test cleanup of old metric data."""
        # Record a metric
        self.metrics.record_histogram("test_metric", 1.0)
        
        # Manually set old timestamp
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        self.metrics._metrics["test_metric"][0].timestamp = old_time
        
        # Cleanup
        self.metrics.cleanup_old_metrics(max_age_hours=24)
        
        # Should be empty now
        assert len(self.metrics._metrics["test_metric"]) == 0


class TestErrorTracker:
    """Test cases for the ErrorTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_error_tracker()
        self.error_tracker = ErrorTracker(
            error_rate_threshold=5.0,  # Lower threshold for testing
            service_failure_threshold=2
        )
        self.alerts_received = []
        
        # Add test alert handler
        def test_handler(alert):
            self.alerts_received.append(alert)
        
        self.error_tracker.add_alert_handler(test_handler)
    
    def test_track_error(self):
        """Test error tracking functionality."""
        self.error_tracker.track_error(
            "ValueError",
            "Test error message",
            "test_component",
            "test-correlation-id",
            {"key": "value"}
        )
        
        # Check that error was stored
        errors = self.error_tracker._errors["test_component"]
        assert len(errors) == 1
        assert errors[0].error_type == "ValueError"
        assert errors[0].message == "Test error message"
        assert errors[0].correlation_id == "test-correlation-id"
    
    def test_error_rate_alert(self):
        """Test error rate alerting."""
        # Generate errors quickly to trigger rate alert
        for i in range(6):  # Above threshold of 5
            self.error_tracker.track_error(
                "TestError",
                f"Error {i}",
                "test_component"
            )
        
        # Should have triggered an alert
        assert len(self.alerts_received) > 0
        alert = self.alerts_received[0]
        assert alert.alert_type == AlertType.ERROR_RATE
        assert alert.severity == AlertSeverity.HIGH
    
    def test_service_failure_tracking(self):
        """Test service failure tracking and alerting."""
        # Record successful calls first
        self.error_tracker.track_service_call("test_service", "test_op", True, 1.0)
        assert len(self.alerts_received) == 0
        
        # Record failures
        self.error_tracker.track_service_call("test_service", "test_op", False, 2.0)
        self.error_tracker.track_service_call("test_service", "test_op", False, 2.0)
        
        # Should trigger service failure alert
        assert len(self.alerts_received) > 0
        alert = self.alerts_received[0]
        assert alert.alert_type == AlertType.SERVICE_FAILURE
        assert alert.severity == AlertSeverity.HIGH
    
    def test_critical_error_alert(self):
        """Test critical error alerting."""
        self.error_tracker.track_error(
            "CriticalError",
            "Critical system failure",
            "core_component",
            severity=AlertSeverity.CRITICAL
        )
        
        # Should immediately trigger critical alert
        assert len(self.alerts_received) > 0
        alert = self.alerts_received[0]
        assert alert.alert_type == AlertType.CONFIGURATION_ERROR
        assert alert.severity == AlertSeverity.CRITICAL
    
    def test_alert_cooldown(self):
        """Test alert cooldown to prevent spam."""
        # Trigger same alert multiple times
        for i in range(3):
            self.error_tracker.track_error(
                "TestError",
                "Same error",
                "test_component",
                severity=AlertSeverity.CRITICAL
            )
        
        # Should only have one alert due to cooldown
        assert len(self.alerts_received) == 1
    
    def test_get_error_summary(self):
        """Test error summary generation."""
        # Track some errors
        self.error_tracker.track_error("Error1", "Message 1", "comp1")
        self.error_tracker.track_error("Error2", "Message 2", "comp1")
        self.error_tracker.track_error("Error1", "Message 3", "comp2")
        
        summary = self.error_tracker.get_error_summary("comp1", hours=1)
        
        assert "components" in summary
        assert "comp1" in summary["components"]
        comp_summary = summary["components"]["comp1"]
        assert comp_summary["total_errors"] == 2
        assert "Error1" in comp_summary["error_types"]
        assert "Error2" in comp_summary["error_types"]
    
    def test_resolve_alert(self):
        """Test alert resolution."""
        # Create an alert
        self.error_tracker.track_error(
            "TestError",
            "Test message",
            "test_component",
            severity=AlertSeverity.CRITICAL
        )
        
        assert len(self.alerts_received) == 1
        alert = self.alerts_received[0]
        assert not alert.resolved
        
        # Resolve the alert
        self.error_tracker.resolve_alert(alert.id, "Fixed the issue")
        
        assert alert.resolved
        assert alert.resolved_at is not None
    
    def test_cleanup_old_data(self):
        """Test cleanup of old error data."""
        # Track an error
        self.error_tracker.track_error("TestError", "Message", "test_component")
        
        # Manually set old timestamp
        old_time = datetime.now(timezone.utc) - timedelta(hours=169)  # Older than 1 week
        self.error_tracker._errors["test_component"][0].timestamp = old_time
        
        # Cleanup
        self.error_tracker.cleanup_old_data(max_age_hours=168)  # 1 week
        
        # Should be empty now
        assert len(self.error_tracker._errors["test_component"]) == 0


class TestHealthChecks:
    """Test cases for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_check_openai_health_not_configured(self):
        """Test OpenAI health check when not configured."""
        config = AppConfig(
            openai_api_key="",  # Empty key
            twilio_account_sid="test",
            twilio_auth_token="test",
            twilio_phone_number="test"
        )
        
        result = await check_openai_health(config)
        
        assert result["status"] == "not_configured"
        assert "not configured" in result["message"]
        assert result["response_time_ms"] == 0
    
    @pytest.mark.asyncio
    async def test_check_openai_health_api_error(self):
        """Test OpenAI health check with API error."""
        config = AppConfig(
            openai_api_key="sk-test-key",
            twilio_account_sid="test",
            twilio_auth_token="test",
            twilio_phone_number="test"
        )
        
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            result = await check_openai_health(config)
            
            assert result["status"] == "degraded"
            assert "API error" in result["message"]
            assert result["response_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_check_twilio_health_not_configured(self):
        """Test Twilio health check when not configured."""
        config = AppConfig(
            openai_api_key="test",
            twilio_account_sid="",  # Empty SID
            twilio_auth_token="test",
            twilio_phone_number="test"
        )
        
        result = await check_twilio_health(config)
        
        assert result["status"] == "not_configured"
        assert "not configured" in result["message"]
        assert result["response_time_ms"] == 0
    
    @pytest.mark.asyncio
    async def test_check_twilio_health_success(self):
        """Test successful Twilio health check."""
        config = AppConfig(
            openai_api_key="test",
            twilio_account_sid="AC123",
            twilio_auth_token="test_token",
            twilio_phone_number="+1234567890"
        )
        
        with patch("twilio.rest.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_account = Mock()
            mock_account.status = "active"
            mock_client.api.accounts.return_value.fetch.return_value = mock_account
            
            result = await check_twilio_health(config)
            
            assert result["status"] == "healthy"
            assert "accessible" in result["message"]
            assert result["response_time_ms"] > 0
            assert result["account_status"] == "active"


class TestIntegration:
    """Integration tests for monitoring features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics_collector()
        reset_error_tracker()
    
    def test_metrics_and_error_tracking_integration(self):
        """Test integration between metrics and error tracking."""
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        # Simulate a service call failure
        metrics.record_service_call("test_service", "test_op", False, 2.5)
        error_tracker.track_service_call("test_service", "test_op", False, 2.5)
        
        # Check metrics
        current_metrics = metrics.get_current_metrics()
        assert "test_service_test_op" in current_metrics["services"]
        service_metrics = current_metrics["services"]["test_service_test_op"]
        assert service_metrics["errors"] == 1
        assert service_metrics["error_rate_percent"] == 100.0
        
        # Check error tracking
        summary = error_tracker.get_error_summary(hours=1)
        # Should have service failure tracking
        assert error_tracker._service_failures["test_service_test_op"] == 1
    
    def test_alert_handlers(self):
        """Test different alert handlers."""
        error_tracker = get_error_tracker()
        
        # Test log alert handler
        alerts_logged = []
        
        def test_log_handler(alert):
            alerts_logged.append(alert)
        
        error_tracker.add_alert_handler(test_log_handler)
        
        # Trigger an alert
        error_tracker.track_error(
            "TestError",
            "Test message",
            "test_component",
            severity=AlertSeverity.CRITICAL
        )
        
        # Should have logged the alert
        assert len(alerts_logged) == 1
        assert alerts_logged[0].severity == AlertSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_service_monitoring_workflow(self):
        """Test complete service monitoring workflow."""
        metrics = get_metrics_collector()
        error_tracker = get_error_tracker()
        
        # Simulate successful operations
        for i in range(5):
            metrics.record_service_call("openai", "analyze", True, 1.0 + i * 0.1)
            error_tracker.track_service_call("openai", "analyze", True, 1.0 + i * 0.1)
        
        # Simulate some failures
        for i in range(2):
            metrics.record_service_call("openai", "analyze", False, 5.0)
            error_tracker.track_service_call("openai", "analyze", False, 5.0)
        
        # Check metrics summary
        current_metrics = metrics.get_current_metrics()
        openai_metrics = current_metrics["services"]["openai_analyze"]
        
        assert openai_metrics["total_calls"] == 7
        assert openai_metrics["errors"] == 2
        assert openai_metrics["error_rate_percent"] == pytest.approx(28.57, rel=1e-2)
        
        # Check error tracking
        assert error_tracker._service_failures["openai_analyze"] == 2


if __name__ == "__main__":
    pytest.main([__file__])