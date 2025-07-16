"""
Tests for monitoring API endpoints.

This module tests the monitoring API endpoints for real-time metrics and data.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.utils.metrics import get_metrics_collector, reset_metrics_collector
from app.utils.error_tracking import get_error_tracker, reset_error_tracker


class TestMonitoringAPI:
    """Test cases for the monitoring API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for API requests."""
        return {"Authorization": "Bearer test_token"}
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics_collector()
        reset_error_tracker()
    
    def test_active_requests_endpoint_auth(self, client):
        """Test active requests endpoint authentication."""
        # Test without auth header
        response = client.get("/monitoring/active-requests")
        assert response.status_code == 401
        
        # Test with invalid token
        with patch("app.api.monitoring.get_auth_service") as mock_get_auth:
            mock_auth_service = AsyncMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Mock token validation - invalid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=False)
            
            response = client.get(
                "/monitoring/active-requests",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401
    
    def test_active_requests_endpoint(self, client, auth_headers):
        """Test active requests endpoint."""
        # Mock authentication service
        with patch("app.api.monitoring.get_auth_service") as mock_get_auth:
            mock_auth_service = AsyncMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Mock token validation - valid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=True, user_id="test_user")
            
            # Make request
            response = client.get("/monitoring/active-requests", headers=auth_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "active_requests" in data
            assert isinstance(data["active_requests"], list)
            assert "queue_depth" in data
            assert "processing_capacity" in data
    
    def test_error_rates_endpoint(self, client, auth_headers):
        """Test error rates endpoint."""
        # Mock authentication service
        with patch("app.api.monitoring.get_auth_service") as mock_get_auth:
            mock_auth_service = AsyncMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Mock token validation - valid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=True, user_id="test_user")
            
            # Make request
            response = client.get("/monitoring/error-rates", headers=auth_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "period" in data
            assert "error_rates" in data
            assert isinstance(data["error_rates"], list)
            
            # Test with period parameter
            response = client.get("/monitoring/error-rates?period=day", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "day"
    
    def test_response_times_endpoint(self, client, auth_headers):
        """Test response times endpoint."""
        # Mock authentication service
        with patch("app.api.monitoring.get_auth_service") as mock_get_auth:
            mock_auth_service = AsyncMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Mock token validation - valid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=True, user_id="test_user")
            
            # Record some metrics
            metrics = get_metrics_collector()
            metrics.record_request("GET", "/test", 200, 0.5)
            metrics.record_service_call("openai", "analyze", True, 1.2)
            
            # Make request
            response = client.get("/monitoring/response-times", headers=auth_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "period" in data
            assert "response_times" in data
            assert isinstance(data["response_times"], list)
            assert "services" in data
            assert "current" in data
            assert data["current"]["total_requests"] == 1
            
            # Test with period parameter
            response = client.get("/monitoring/response-times?period=week", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "week"


if __name__ == "__main__":
    pytest.main([__file__])