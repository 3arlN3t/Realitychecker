"""
Integration tests for dashboard API endpoints.

This module tests all dashboard API endpoints including authentication,
authorization, data validation, and error handling.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.data_models import (
    DashboardOverview, AnalyticsTrends, UserList, SystemMetrics,
    ReportData, UserDetails, UserInteraction, JobAnalysisResult,
    JobClassification, UserRole, User
)


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Create mock admin user for testing."""
    return User(
        username="admin",
        role=UserRole.ADMIN,
        created_at=datetime.utcnow(),
        is_active=True
    )


@pytest.fixture
def mock_analyst_user():
    """Create mock analyst user for testing."""
    return User(
        username="analyst",
        role=UserRole.ANALYST,
        created_at=datetime.utcnow(),
        is_active=True
    )


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
        timestamp=datetime.utcnow()
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
        first_interaction=datetime.utcnow() - timedelta(days=7),
        last_interaction=datetime.utcnow() - timedelta(hours=2),
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
        timestamp=datetime.utcnow(),
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
        generated_at=datetime.utcnow(),
        period="2025-01-01 to 2025-01-31",
        data={"total_messages": 100, "success_rate": 95.0},
        export_format="json"
    )


class TestDashboardOverviewEndpoint:
    """Test cases for GET /api/dashboard/overview endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_get_dashboard_overview_success(self, mock_get_analytics, mock_get_user, 
                                          client, mock_admin_user, mock_dashboard_overview):
        """Test successful dashboard overview retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_requests"] == 1250
        assert data["requests_today"] == 45
        assert data["error_rate"] == 2.3
        assert data["system_health"] == "healthy"
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_dashboard_overview_unauthorized(self, mock_get_user, client):
        """Test dashboard overview with unauthorized user."""
        # Setup mock to raise HTTPException
        from fastapi import HTTPException
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Unauthorized")
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_get_dashboard_overview_service_error(self, mock_get_analytics, mock_get_user, 
                                                client, mock_admin_user):
        """Test dashboard overview with service error."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_dashboard_overview = AsyncMock(side_effect=Exception("Service error"))
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve dashboard overview" in response.json()["detail"]


class TestAnalyticsTrendsEndpoint:
    """Test cases for GET /api/analytics/trends endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_get_analytics_trends_success(self, mock_get_analytics, mock_get_user, 
                                        client, mock_analyst_user, mock_analytics_trends):
        """Test successful analytics trends retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_analytics_trends = AsyncMock(return_value=mock_analytics_trends)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/analytics/trends?period=week")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["period"] == "week"
        assert "classifications" in data
        assert "daily_counts" in data
        assert "peak_hours" in data
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_get_analytics_trends_with_custom_dates(self, mock_get_analytics, mock_get_user, 
                                                  client, mock_analyst_user, mock_analytics_trends):
        """Test analytics trends with custom date range."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_analytics_trends = AsyncMock(return_value=mock_analytics_trends)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request with custom dates
        start_date = "2025-01-01"
        end_date = "2025-01-31"
        response = client.get(f"/api/analytics/trends?period=month&start_date={start_date}&end_date={end_date}")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        mock_analytics_service.get_analytics_trends.assert_called_once()
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_analytics_trends_invalid_period(self, mock_get_user, client, mock_analyst_user):
        """Test analytics trends with invalid period."""
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with invalid period
        response = client.get("/api/analytics/trends?period=invalid")
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_analytics_trends_invalid_date_format(self, mock_get_user, client, mock_analyst_user):
        """Test analytics trends with invalid date format."""
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with invalid date format
        response = client.get("/api/analytics/trends?start_date=invalid-date")
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid start_date format" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_analytics_trends_invalid_date_range(self, mock_get_user, client, mock_analyst_user):
        """Test analytics trends with invalid date range."""
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with start_date after end_date
        response = client.get("/api/analytics/trends?start_date=2025-01-31&end_date=2025-01-01")
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date must be before end_date" in response.json()["detail"]


class TestUsersEndpoint:
    """Test cases for GET /api/users endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_users_success(self, mock_get_user_service, mock_get_user, 
                             client, mock_analyst_user, mock_user_list):
        """Test successful users list retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_user_service = Mock()
        mock_user_service.get_users = AsyncMock(return_value=mock_user_list)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        response = client.get("/api/users")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] == 1
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_users_with_pagination(self, mock_get_user_service, mock_get_user, 
                                     client, mock_analyst_user, mock_user_list):
        """Test users list with pagination parameters."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_user_service = Mock()
        mock_user_service.get_users = AsyncMock(return_value=mock_user_list)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request with pagination
        response = client.get("/api/users?page=2&limit=10")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        mock_user_service.get_users.assert_called_once()
        call_args = mock_user_service.get_users.call_args
        assert call_args[1]["page"] == 2
        assert call_args[1]["limit"] == 10
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_users_with_filters(self, mock_get_user_service, mock_get_user, 
                                  client, mock_analyst_user, mock_user_list):
        """Test users list with filters."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_user_service = Mock()
        mock_user_service.get_users = AsyncMock(return_value=mock_user_list)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request with filters
        response = client.get("/api/users?blocked=false&min_requests=1&max_requests=10")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        mock_user_service.get_users.assert_called_once()
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_users_invalid_pagination(self, mock_get_user, client, mock_analyst_user):
        """Test users list with invalid pagination parameters."""
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with invalid page number
        response = client.get("/api/users?page=0")
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.dashboard.get_current_user')
    def test_get_users_invalid_filter_range(self, mock_get_user, client, mock_analyst_user):
        """Test users list with invalid filter range."""
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with min_requests > max_requests
        response = client.get("/api/users?min_requests=10&max_requests=5")
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "min_requests cannot be greater than max_requests" in response.json()["detail"]


class TestRealtimeMetricsEndpoint:
    """Test cases for GET /api/metrics/realtime endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_metrics_collector')
    @patch('app.api.dashboard.get_error_tracker')
    def test_get_realtime_metrics_success(self, mock_get_error_tracker, mock_get_metrics, 
                                        mock_get_user, client, mock_analyst_user):
        """Test successful real-time metrics retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
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
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timestamp" in data
        assert "active_requests" in data
        assert "response_times" in data
        assert "service_status" in data
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_metrics_collector')
    def test_get_realtime_metrics_service_error(self, mock_get_metrics, mock_get_user, 
                                              client, mock_analyst_user):
        """Test real-time metrics with service error."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_get_metrics.side_effect = Exception("Metrics service error")
        
        # Make request
        response = client.get("/api/metrics/realtime")
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestConfigurationEndpoint:
    """Test cases for POST /api/config endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    def test_update_configuration_success(self, mock_get_user, client, mock_admin_user):
        """Test successful configuration update."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        
        # Make request
        config_updates = {
            "openai_model": "gpt-4-turbo",
            "max_pdf_size_mb": 15,
            "log_level": "DEBUG"
        }
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "updated_keys" in data
        assert set(data["updated_keys"]) == set(config_updates.keys())
    
    @patch('app.api.dashboard.get_current_user')
    def test_update_configuration_non_admin(self, mock_get_user, client, mock_analyst_user):
        """Test configuration update with non-admin user."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
        # Make request
        config_updates = {"openai_model": "gpt-4-turbo"}
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_update_configuration_invalid_keys(self, mock_get_user, client, mock_admin_user):
        """Test configuration update with invalid keys."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        
        # Make request with invalid keys
        config_updates = {"invalid_key": "value", "another_invalid": "value"}
        response = client.post("/api/config", json=config_updates)
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid configuration keys" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_update_configuration_invalid_values(self, mock_get_user, client, mock_admin_user):
        """Test configuration update with invalid values."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        
        # Test invalid OpenAI model
        config_updates = {"openai_model": "invalid-model"}
        response = client.post("/api/config", json=config_updates)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test invalid PDF size
        config_updates = {"max_pdf_size_mb": -5}
        response = client.post("/api/config", json=config_updates)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test invalid log level
        config_updates = {"log_level": "INVALID"}
        response = client.post("/api/config", json=config_updates)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestReportGenerationEndpoint:
    """Test cases for POST /api/reports/generate endpoint."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_generate_report_success(self, mock_get_analytics, mock_get_user, 
                                   client, mock_analyst_user, mock_report_data):
        """Test successful report generation."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
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
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["report_type"] == "usage_summary"
        assert data["export_format"] == "json"
    
    @patch('app.api.dashboard.get_current_user')
    def test_generate_report_missing_params(self, mock_get_user, client, mock_analyst_user):
        """Test report generation with missing parameters."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
        # Make request with missing parameters
        report_params = {"report_type": "usage_summary"}
        response = client.post("/api/reports/generate", json=report_params)
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing required parameters" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_generate_report_invalid_dates(self, mock_get_user, client, mock_analyst_user):
        """Test report generation with invalid dates."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
        # Test invalid date format
        report_params = {
            "report_type": "usage_summary",
            "start_date": "invalid-date",
            "end_date": "2025-01-31T23:59:59",
            "export_format": "json"
        }
        response = client.post("/api/reports/generate", json=report_params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test start_date after end_date
        report_params = {
            "report_type": "usage_summary",
            "start_date": "2025-01-31T00:00:00",
            "end_date": "2025-01-01T23:59:59",
            "export_format": "json"
        }
        response = client.post("/api/reports/generate", json=report_params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date must be before end_date" in response.json()["detail"]


class TestUserManagementEndpoints:
    """Test cases for user management endpoints."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_block_user_success(self, mock_get_user_service, mock_get_user, 
                              client, mock_admin_user):
        """Test successful user blocking."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_user_service = Mock()
        mock_user_service.block_user = AsyncMock(return_value=True)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.post(f"/api/users/{phone_number}/block", json="Spam user")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["phone_number"] == phone_number
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_unblock_user_success(self, mock_get_user_service, mock_get_user, 
                                client, mock_admin_user):
        """Test successful user unblocking."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_user_service = Mock()
        mock_user_service.unblock_user = AsyncMock(return_value=True)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.post(f"/api/users/{phone_number}/unblock")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["phone_number"] == phone_number
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_user_details_success(self, mock_get_user_service, mock_get_user, 
                                    client, mock_analyst_user):
        """Test successful user details retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
        user_details = UserDetails(
            phone_number="whatsapp:+1234567890",
            first_interaction=datetime.utcnow() - timedelta(days=7),
            last_interaction=datetime.utcnow() - timedelta(hours=2),
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
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert "recent_interactions" in data
        assert "statistics" in data
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_user_management_service')
    def test_get_user_details_not_found(self, mock_get_user_service, mock_get_user, 
                                      client, mock_analyst_user):
        """Test user details retrieval for non-existent user."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_user_service = Mock()
        mock_user_service.get_user_details = AsyncMock(return_value=None)
        mock_get_user_service.return_value = mock_user_service
        
        # Make request
        phone_number = "whatsapp:+9999999999"
        response = client.get(f"/api/users/{phone_number}")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_block_user_non_admin(self, mock_get_user, client, mock_analyst_user):
        """Test user blocking with non-admin user."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        
        # Make request
        phone_number = "whatsapp:+1234567890"
        response = client.post(f"/api/users/{phone_number}/block", json="Spam user")
        
        # Assertions
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in response.json()["detail"]


class TestAuthenticationAndAuthorization:
    """Test cases for authentication and authorization."""
    
    @patch('app.api.dashboard.get_current_user')
    def test_unauthorized_access(self, mock_get_user, client):
        """Test unauthorized access to protected endpoints."""
        from fastapi import HTTPException
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Unauthorized")
        
        # Test various endpoints
        endpoints = [
            "/api/dashboard/overview",
            "/api/analytics/trends",
            "/api/users",
            "/api/metrics/realtime"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.api.dashboard.get_current_user')
    def test_insufficient_privileges(self, mock_get_user, client):
        """Test access with insufficient privileges."""
        # Create user with no role (should fail authorization checks)
        mock_user = User(
            username="user",
            role=UserRole.ANALYST,  # Analyst trying to access admin-only endpoints
            created_at=datetime.utcnow(),
            is_active=True
        )
        mock_get_user.return_value = mock_user
        
        # Test admin-only endpoints
        admin_endpoints = [
            ("/api/config", "post", {"openai_model": "gpt-4"}),
            ("/api/users/whatsapp:+1234567890/block", "post", "reason"),
            ("/api/users/whatsapp:+1234567890/unblock", "post", None)
        ]
        
        for endpoint, method, data in admin_endpoints:
            if method == "post":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == status.HTTP_403_FORBIDDEN


class TestErrorHandling:
    """Test cases for error handling in dashboard endpoints."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_service_unavailable_error(self, mock_get_analytics, mock_get_user, 
                                     client, mock_admin_user):
        """Test handling of service unavailable errors."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_get_analytics.side_effect = Exception("Service unavailable")
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve dashboard overview" in response.json()["detail"]
    
    @patch('app.api.dashboard.get_current_user')
    def test_validation_errors(self, mock_get_user, client, mock_admin_user):
        """Test handling of validation errors."""
        mock_get_user.return_value = mock_admin_user
        
        # Test invalid query parameters
        response = client.get("/api/users?page=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        response = client.get("/api/users?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        response = client.get("/api/users?limit=200")  # Exceeds max limit
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDataSerialization:
    """Test cases for data serialization and response formats."""
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_dashboard_overview_serialization(self, mock_get_analytics, mock_get_user, 
                                            client, mock_admin_user, mock_dashboard_overview):
        """Test dashboard overview data serialization."""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/dashboard/overview")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
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
    
    @patch('app.api.dashboard.get_current_user')
    @patch('app.api.dashboard.get_analytics_service')
    def test_analytics_trends_serialization(self, mock_get_analytics, mock_get_user, 
                                          client, mock_analyst_user, mock_analytics_trends):
        """Test analytics trends data serialization."""
        # Setup mocks
        mock_get_user.return_value = mock_analyst_user
        mock_analytics_service = Mock()
        mock_analytics_service.get_analytics_trends = AsyncMock(return_value=mock_analytics_trends)
        mock_get_analytics.return_value = mock_analytics_service
        
        # Make request
        response = client.get("/api/analytics/trends")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
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