"""
Simple integration tests for dashboard API endpoints.

This module tests the dashboard API endpoints with mocked dependencies
to avoid rate limiting and middleware issues.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dashboard import router
from app.models.data_models import (
    DashboardOverview, AnalyticsTrends, UserList, SystemMetrics,
    ReportData, UserDetails, UserRole, User
)


# Create a simple test app with just the dashboard router
test_app = FastAPI()
test_app.include_router(router)


@pytest.fixture
def client():
    """Create test client for dashboard API."""
    return TestClient(test_app)


@pytest.fixture
def mock_dashboard_overview():
    """Create mock dashboard overview data."""
    return DashboardOverview(
        total_requests=1250,
        requests_today=45,
        error_rate=2.3,
        avg_response_time=1.2,
        active_users=23,
        system_health="healthy",
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_analytics_trends():
    """Create mock analytics trends data."""
    return AnalyticsTrends(
        period="week",
        classifications={"Legit": 65, "Suspicious": 25, "Likely Scam": 10},
        daily_counts=[
            {"date": "2025-01-15", "count": 45},
            {"date": "2025-01-16", "count": 52}
        ],
        peak_hours=[9, 14, 20],
        user_engagement={
            "active_users": 23.0,
            "avg_interactions_per_user": 2.5,
            "repeat_user_rate": 65.2
        }
    )


@pytest.fixture
def mock_user_list():
    """Create mock user list data."""
    user_details = UserDetails(
        phone_number="whatsapp:+1234567890",
        first_interaction=datetime.now() - timedelta(days=7),
        last_interaction=datetime.now() - timedelta(hours=2),
        total_requests=5,
        blocked=False
    )
    
    return UserList(
        users=[user_details],
        total=1,
        page=1,
        pages=1,
        limit=20
    )


@pytest.fixture
def mock_system_metrics():
    """Create mock system metrics data."""
    return SystemMetrics(
        timestamp=datetime.now(),
        active_requests=3,
        requests_per_minute=12,
        error_rate=1.5,
        response_times={"p50": 0.8, "p95": 2.1, "p99": 3.5},
        service_status={"openai": "healthy", "twilio": "healthy"},
        memory_usage=45.2,
        cpu_usage=23.8
    )


@pytest.fixture
def mock_report_data():
    """Create mock report data."""
    return ReportData(
        report_type="usage_summary",
        generated_at=datetime.now(),
        period="2025-01-01 to 2025-01-31",
        data={"total_messages": 100, "success_rate": 95.0},
        export_format="json"
    )


class TestDashboardEndpoints:
    """Test dashboard API endpoints with mocked dependencies."""
    
    @patch('app.api.dashboard.get_analytics_service')
    def test_dashboard_overview_success(self, mock_get_analytics, client, mock_dashboard_overview):
        """Test successful dashboard overview retrieval."""
        # Setup mock
        mock_analytics_service = Mock()
        mock_analytics_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 1250
        assert data["requests_today"] == 45
        assert data["error_rate"] == 2.3
        assert data["system_health"] == "healthy"
    
    @patch('app.api.dashboard.get_analytics_service')
    def test_analytics_trends_success(self, mock_get_analytics, client, mock_analytics_trends):
        """Test successful analytics trends retrieval."""
        # Setup mock
        mock_analytics_service = Mock()
        mock_analytics_service.get_analytics_trends = AsyncMock(return_value=mock_analytics_trends)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/analytics/trends?period=week")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
        assert "classifications" in data
        assert "daily_counts" in data
        assert "peak_hours" in data
    
    @patch('app.api.dashboard.get_user_management_service')
    def test_users_list_success(self, mock_get_user_service, client, mock_user_list):
        """Test successful users list retrieval."""
        # Setup mock
        mock_user_service = Mock()
        mock_user_service.get_users = AsyncMock(return_value=mock_user_list)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        response = client.get("/api/users")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] == 1
    
    @patch('app.api.dashboard.get_metrics_collector')
    @patch('app.api.dashboard.get_error_tracker')
    def test_realtime_metrics_success(self, mock_get_error_tracker, mock_get_metrics, client):
        """Test successful real-time metrics retrieval."""
        # Setup mocks
        mock_metrics_collector = Mock()
        mock_metrics_collector.get_current_metrics.return_value = {
            "active_requests": 3,
            "requests_per_minute": 12,
            "response_time_p50": 0.8,
            "response_time_p95": 2.1,
            "response_time_p99": 3.5,
            "memory_usage": 45.2,
            "cpu_usage": 23.8
        }
        mock_get_metrics.return_value = mock_metrics_collector
        
        mock_error_tracker = Mock()
        mock_error_tracker.get_error_statistics.return_value = {"error_rate": 1.5}
        mock_get_error_tracker.return_value = mock_error_tracker
        
        # Make request
        response = client.get("/api/metrics/realtime")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "active_requests" in data
        assert "response_times" in data
        assert "service_status" in data
    
    def test_configuration_update_success(self, client):
        """Test successful configuration update."""
        # Make request
        config_updates = {
            "openai_model": "gpt-4-turbo",
            "max_pdf_size_mb": 15,
            "log_level": "DEBUG"
        }
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated_keys" in data
        assert set(data["updated_keys"]) == set(config_updates.keys())
    
    def test_configuration_update_invalid_keys(self, client):
        """Test configuration update with invalid keys."""
        # Make request with invalid keys
        config_updates = {"invalid_key": "value", "another_invalid": "value"}
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid configuration keys" in response.json()["detail"]
    
    def test_configuration_update_invalid_model(self, client):
        """Test configuration update with invalid OpenAI model."""
        # Make request with invalid model
        config_updates = {"openai_model": "invalid-model"}
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid OpenAI model" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_analytics_service')
    def test_report_generation_success(self, mock_get_analytics, client, mock_report_data):
        """Test successful report generation."""
        # Setup mock
        mock_analytics_service = Mock()
        mock_analytics_service.generate_report = AsyncMock(return_value=mock_report_data)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        report_params = {
            "report_type": "usage_summary",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-01-31T23:59:59",
            "export_format": "json"
        }
        response = client.post("/api/reports/generate", json=report_params)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "usage_summary"
        assert data["export_format"] == "json"
    
    def test_report_generation_missing_params(self, client):
        """Test report generation with missing parameters."""
        # Make request with missing parameters
        report_params = {"report_type": "usage_summary"}
        response = client.post("/api/reports/generate", json=report_params)
        
        # Assertions
        assert response.status_code == 400
        assert "Missing required parameters" in response.json()["detail"]
    
    def test_report_generation_invalid_date_format(self, client):
        """Test report generation with invalid date format."""
        # Make request with invalid date format
        report_params = {
            "report_type": "usage_summary",
            "start_date": "invalid-date",
            "end_date": "2025-01-31T23:59:59",
            "export_format": "json"
        }
        response = client.post("/api/reports/generate", json=report_params)
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]
    
    def test_report_generation_invalid_date_range(self, client):
        """Test report generation with invalid date range."""
        # Make request with start_date after end_date
        report_params = {
            "report_type": "usage_summary",
            "start_date": "2025-01-31T00:00:00",
            "end_date": "2025-01-01T23:59:59",
            "export_format": "json"
        }
        response = client.post("/api/reports/generate", json=report_params)
        
        # Assertions
        assert response.status_code == 400
        assert "start_date must be before end_date" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_user_management_service')
    def test_block_user_success(self, mock_get_user_service, client):
        """Test successful user blocking."""
        # Setup mock
        mock_user_service = Mock()
        mock_user_service.block_user = AsyncMock(return_value=True)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.post(f"/api/users/{phone_number}/block", json="Spam user")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phone_number"] == phone_number
    
    @patch('app.api.dashboard.get_user_management_service')
    def test_unblock_user_success(self, mock_get_user_service, client):
        """Test successful user unblocking."""
        # Setup mock
        mock_user_service = Mock()
        mock_user_service.unblock_user = AsyncMock(return_value=True)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.post(f"/api/users/{phone_number}/unblock")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phone_number"] == phone_number
    
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_user_details_success(self, mock_get_user_service, client):
        """Test successful user details retrieval."""
        # Setup mock
        user_details = UserDetails(
            phone_number="whatsapp:+1234567890",
            first_interaction=datetime.now() - timedelta(days=7),
            last_interaction=datetime.now() - timedelta(hours=2),
            total_requests=5,
            blocked=False
        )
        
        mock_user_service = Mock()
        mock_user_service.get_user_details = AsyncMock(return_value=user_details)
        mock_user_service.get_user_interaction_history = AsyncMock(return_value=[])
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.get(f"/api/users/{phone_number}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "recent_interactions" in data
        assert "statistics" in data
    
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_user_details_not_found(self, mock_get_user_service, client):
        """Test user details retrieval for non-existent user."""
        # Setup mock
        mock_user_service = Mock()
        mock_user_service.get_user_details = AsyncMock(return_value=None)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+9999999999"
        response = client.get(f"/api/users/{phone_number}")
        
        # Assertions
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestValidationAndErrorHandling:
    """Test validation and error handling."""
    
    def test_analytics_trends_invalid_period(self, client):
        """Test analytics trends with invalid period."""
        # Make request with invalid period
        response = client.get("/api/analytics/trends?period=invalid")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_analytics_trends_invalid_date_format(self, client):
        """Test analytics trends with invalid date format."""
        # Make request with invalid date format
        response = client.get("/api/analytics/trends?start_date=invalid-date")
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]
    
    def test_analytics_trends_invalid_date_range(self, client):
        """Test analytics trends with invalid date range."""
        # Make request with start_date after end_date
        response = client.get("/api/analytics/trends?start_date=2025-01-31&end_date=2025-01-01")
        
        # Assertions
        assert response.status_code == 400
        assert "start_date must be before end_date" in response.json()["detail"]
    
    def test_users_invalid_pagination(self, client):
        """Test users list with invalid pagination parameters."""
        # Make request with invalid page number
        response = client.get("/api/users?page=0")
        
        # Assertions
        assert response.status_code == 422
    
    def test_users_invalid_filter_range(self, client):
        """Test users list with invalid filter range."""
        # Make request with min_requests > max_requests
        response = client.get("/api/users?min_requests=10&max_requests=5")
        
        # Assertions
        assert response.status_code == 400
        assert "min_requests cannot be greater than max_requests" in response.json()["detail"]


class TestDataSerialization:
    """Test data serialization and response formats."""
    
    @patch('app.api.dashboard.get_analytics_service')
    def test_dashboard_overview_serialization(self, mock_get_analytics, client, mock_dashboard_overview):
        """Test dashboard overview data serialization."""
        # Setup mock
        mock_analytics_service = Mock()
        mock_analytics_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            "total_requests", "requests_today", "error_rate", 
            "avg_response_time", "active_users", "system_health", "timestamp"
        ]
        for field in required_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["error_rate"], float)
        assert isinstance(data["system_health"], str)
    
    @patch('app.api.dashboard.get_analytics_service')
    def test_analytics_trends_serialization(self, mock_get_analytics, client, mock_analytics_trends):
        """Test analytics trends data serialization."""
        # Setup mock
        mock_analytics_service = Mock()
        mock_analytics_service.get_analytics_trends = AsyncMock(return_value=mock_analytics_trends)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/analytics/trends")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "period" in data
        assert "classifications" in data
        assert "daily_counts" in data
        assert "peak_hours" in data
        assert "user_engagement" in data
        
        # Check classifications structure
        assert isinstance(data["classifications"], dict)
        assert "Legit" in data["classifications"]
        
        # Check daily counts structure
        assert isinstance(data["daily_counts"], list)
        if data["daily_counts"]:
            assert "date" in data["daily_counts"][0]
            assert "count" in data["daily_counts"][0]


if __name__ == "__main__":
    pytest.main([__file__])