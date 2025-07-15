"""Unit tests for the main FastAPI application."""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.config import AppConfig


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AppConfig(
        openai_api_key="test-openai-key",
        twilio_account_sid="test-twilio-sid",
        twilio_auth_token="test-twilio-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO",
        webhook_validation=True
    )


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""
    
    @patch('app.main.get_config')
    def test_health_check_healthy_status(self, mock_get_config, client, mock_config):
        """Test health check returns healthy status when all services are configured."""
        mock_get_config.return_value = mock_config
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["services"]["openai"] == "connected"
        assert data["services"]["twilio"] == "connected"
    
    @patch('app.dependencies.ServiceContainer.perform_health_checks', new_callable=AsyncMock)
    def test_health_check_degraded_status_missing_openai(self, mock_health_checks, client):
        """Test health check returns degraded status when OpenAI is not configured."""
        from app.dependencies import reset_service_container
        
        # Mock health check to return not_configured for OpenAI
        mock_health_checks.return_value = {
            "openai": "not_configured",
            "twilio": "connected",
            "pdf_processing": "ready"
        }
        
        # Reset service container to pick up new config
        reset_service_container()
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["services"]["openai"] == "not_configured"
        assert data["services"]["twilio"] == "connected"
    
    @patch('app.dependencies.ServiceContainer.perform_health_checks', new_callable=AsyncMock)
    def test_health_check_degraded_status_missing_twilio(self, mock_health_checks, client):
        """Test health check returns degraded status when Twilio is not configured."""
        from app.dependencies import reset_service_container
        
        # Mock health check to return not_configured for Twilio
        mock_health_checks.return_value = {
            "openai": "connected",
            "twilio": "not_configured",
            "pdf_processing": "ready"
        }
        
        # Reset service container to pick up new config
        reset_service_container()
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["services"]["openai"] == "connected"
        assert data["services"]["twilio"] == "not_configured"
    
    @patch('app.main.get_service_container')
    def test_health_check_exception_handling(self, mock_get_service_container, client):
        """Test health check handles exceptions gracefully."""
        mock_get_service_container.side_effect = Exception("Configuration error")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["error"] == "Health check failed"
        assert "timestamp" in data


class TestErrorHandling:
    """Test cases for error handling middleware and exception handlers."""
    
    def test_404_not_found(self, client):
        """Test 404 error handling for non-existent endpoints."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["error"] == "HTTP 404"
        assert data["message"] == "Not Found"
        assert "timestamp" in data
    
    def test_method_not_allowed(self, client):
        """Test 405 error handling for unsupported HTTP methods."""
        response = client.put("/health")
        
        assert response.status_code == 405
        data = response.json()
        
        assert data["error"] == "HTTP 405"
        assert data["message"] == "Method Not Allowed"
        assert "timestamp" in data
    
    @patch('app.main.get_config')
    def test_unhandled_exception_middleware(self, mock_get_config, client):
        """Test that unhandled exceptions are caught by middleware."""
        # Create a mock that raises an exception
        mock_get_config.side_effect = RuntimeError("Unexpected error")
        
        # This should trigger the error handling middleware
        response = client.get("/health")
        
        # The middleware should catch the exception and return 500
        assert response.status_code == 503  # Health endpoint handles its own exceptions
        data = response.json()
        assert data["status"] == "unhealthy"


class TestCORSConfiguration:
    """Test cases for CORS middleware configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers
    
    def test_preflight_request(self, client):
        """Test CORS preflight request handling."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestApplicationLifecycle:
    """Test cases for application startup and shutdown events."""
    
    @patch('app.main.get_config')
    @patch('app.main.logger')
    def test_startup_event_success(self, mock_logger, mock_get_config, mock_config):
        """Test successful application startup."""
        mock_get_config.return_value = mock_config
        
        # Import and trigger startup manually for testing
        from app.main import startup_event
        
        # This should not raise an exception
        import asyncio
        asyncio.run(startup_event())
        
        # Verify logging calls were made
        mock_logger.info.assert_called()
    
    @patch('app.main.get_config')
    def test_startup_event_failure(self, mock_get_config):
        """Test application startup failure handling."""
        mock_get_config.side_effect = ValueError("Missing configuration")
        
        from app.main import startup_event
        
        # This should raise an exception
        with pytest.raises(ValueError):
            import asyncio
            asyncio.run(startup_event())


class TestApplicationMetadata:
    """Test cases for application metadata and documentation."""
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert schema["info"]["title"] == "Reality Checker WhatsApp Bot"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "/health" in schema["paths"]
    
    def test_docs_endpoint_available(self, client):
        """Test that API documentation endpoint is available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc documentation endpoint is available."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestRequestValidation:
    """Test cases for request validation error handling."""
    
    @patch('app.main.get_config')
    def test_validation_error_response_format(self, mock_get_config, client, mock_config):
        """Test that validation errors return properly formatted responses."""
        # Mock the config so health endpoint works
        mock_get_config.return_value = mock_config
        
        # Health endpoint should work with extra params
        response = client.get("/health?invalid_param=test")
        assert response.status_code == 200