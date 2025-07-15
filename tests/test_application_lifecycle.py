"""
Integration tests for application lifecycle management.

Tests startup, shutdown, dependency injection, and service health checks.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_service_container, reset_service_container, ServiceContainer
from app.config import AppConfig
from app.services.message_handler import MessageHandlerService
from app.services.openai_analysis import OpenAIAnalysisService
from app.services.pdf_processing import PDFProcessingService
from app.services.twilio_response import TwilioResponseService


class TestApplicationLifecycle:
    """Test application startup and shutdown lifecycle."""
    
    def setup_method(self):
        """Reset service container before each test."""
        reset_service_container()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_service_container()
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890',
        'LOG_LEVEL': 'INFO'
    })
    def test_application_startup_success(self):
        """Test successful application startup with valid configuration."""
        with TestClient(app) as client:
            # Application should start successfully
            response = client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded"]
            assert "services" in health_data
            assert "timestamp" in health_data
            assert "version" in health_data
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': '',  # Missing required config
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    }, clear=True)
    def test_application_startup_missing_config(self):
        """Test application startup fails with missing configuration."""
        # Reset the config cache to pick up the new environment
        from app.config import config
        import app.config
        app.config.config = None
        
        with pytest.raises(ValueError, match="Missing required environment variables"):
            # This should fail during config validation
            AppConfig.from_env()
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    def test_service_container_initialization(self):
        """Test service container properly initializes all services."""
        config = AppConfig.from_env()
        container = ServiceContainer(config)
        
        # Test service creation
        pdf_service = container.get_pdf_service()
        assert isinstance(pdf_service, PDFProcessingService)
        assert pdf_service.config == config
        
        openai_service = container.get_openai_service()
        assert isinstance(openai_service, OpenAIAnalysisService)
        assert openai_service.config == config
        
        twilio_service = container.get_twilio_service()
        assert isinstance(twilio_service, TwilioResponseService)
        assert twilio_service.config == config
        
        message_handler = container.get_message_handler()
        assert isinstance(message_handler, MessageHandlerService)
        assert message_handler.config == config
        
        # Test service reuse (singleton behavior)
        assert container.get_pdf_service() is pdf_service
        assert container.get_openai_service() is openai_service
        assert container.get_twilio_service() is twilio_service
        assert container.get_message_handler() is message_handler
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    @pytest.mark.asyncio
    async def test_service_health_checks(self):
        """Test service health checks during startup."""
        config = AppConfig.from_env()
        container = ServiceContainer(config)
        
        health_status = await container.perform_health_checks()
        
        # Check expected services are present
        expected_services = ['openai', 'twilio', 'pdf_processing']
        for service in expected_services:
            assert service in health_status
        
        # OpenAI should be connected with valid key
        assert health_status['openai'] == 'connected'
        
        # Twilio should be connected with valid config
        assert health_status['twilio'] == 'connected'
        
        # PDF processing should be ready
        assert health_status['pdf_processing'] == 'ready'
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'invalid-key',  # Invalid key format
        'TWILIO_ACCOUNT_SID': 'AC123',  # Valid Twilio config
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    @pytest.mark.asyncio
    async def test_service_health_checks_failures(self):
        """Test service health checks with invalid configuration."""
        config = AppConfig.from_env()
        container = ServiceContainer(config)
        
        health_status = await container.perform_health_checks()
        
        # OpenAI should fail with invalid key format
        assert health_status['openai'] == 'not_configured'
        
        # Twilio should be connected with valid config
        assert health_status['twilio'] == 'connected'
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    @pytest.mark.asyncio
    async def test_service_container_cleanup(self):
        """Test service container cleanup during shutdown."""
        config = AppConfig.from_env()
        container = ServiceContainer(config)
        
        # Initialize services
        _ = container.get_pdf_service()
        _ = container.get_openai_service()
        _ = container.get_twilio_service()
        _ = container.get_message_handler()
        
        # Mock OpenAI client with close method
        openai_service = container.get_openai_service()
        openai_service.client = MagicMock()
        openai_service.client.close = AsyncMock()
        
        # Perform cleanup
        await container.cleanup()
        
        # Verify cleanup was called
        openai_service.client.close.assert_called_once()
        
        # Verify services are cleared
        assert len(container._services) == 0
        assert len(container._health_checks) == 0
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    def test_dependency_injection_in_endpoints(self):
        """Test that dependency injection works in API endpoints."""
        with TestClient(app) as client:
            # Test webhook endpoint with dependency injection
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "MessageSid": "SM123",
                    "From": "whatsapp:+1234567890",
                    "To": "whatsapp:+1987654321",
                    "Body": "test message",
                    "NumMedia": "0"
                }
            )
            
            # Should process without dependency injection errors
            # (May fail due to other reasons like Twilio signature validation)
            assert response.status_code in [200, 401]  # 401 for missing signature
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    def test_health_endpoint_with_service_container(self):
        """Test health endpoint uses service container for health checks."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Should include all expected fields
            required_fields = ["status", "timestamp", "services", "version", "uptime"]
            for field in required_fields:
                assert field in health_data
            
            # Should include service health status
            services = health_data["services"]
            expected_services = ["openai", "twilio", "pdf_processing"]
            for service in expected_services:
                assert service in services
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    def test_service_container_singleton_behavior(self):
        """Test that service container maintains singleton behavior."""
        # Get container multiple times
        container1 = get_service_container()
        container2 = get_service_container()
        
        # Should be the same instance
        assert container1 is container2
        
        # Services should be the same instances
        service1 = container1.get_pdf_service()
        service2 = container2.get_pdf_service()
        assert service1 is service2
    
    def test_service_container_reset(self):
        """Test service container reset functionality."""
        # Get initial container
        container1 = get_service_container()
        
        # Reset container
        reset_service_container()
        
        # Get new container
        container2 = get_service_container()
        
        # Should be different instances
        assert container1 is not container2


class TestServiceDependencyInjection:
    """Test dependency injection for individual services."""
    
    def setup_method(self):
        """Reset service container before each test."""
        reset_service_container()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_service_container()
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    })
    def test_message_handler_service_injection(self):
        """Test message handler service gets properly injected dependencies."""
        container = get_service_container()
        message_handler = container.get_message_handler()
        
        # Should have all required service dependencies
        assert hasattr(message_handler, 'pdf_service')
        assert hasattr(message_handler, 'openai_service')
        assert hasattr(message_handler, 'twilio_service')
        
        # Dependencies should be proper service instances
        assert isinstance(message_handler.pdf_service, PDFProcessingService)
        assert isinstance(message_handler.openai_service, OpenAIAnalysisService)
        assert isinstance(message_handler.twilio_service, TwilioResponseService)
        
        # All services should share the same config
        config = message_handler.config
        assert message_handler.pdf_service.config is config
        assert message_handler.openai_service.config is config
        assert message_handler.twilio_service.config is config
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'TWILIO_ACCOUNT_SID': 'AC123',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_PHONE_NUMBER': '+1234567890',
        'MAX_PDF_SIZE_MB': '5',
        'OPENAI_MODEL': 'gpt-3.5-turbo'
    })
    def test_service_configuration_injection(self):
        """Test services receive proper configuration through injection."""
        # Reset the config cache to pick up the new environment
        import app.config
        app.config.config = None
        
        # Create a fresh config and container with the patched environment
        config = AppConfig.from_env()
        container = ServiceContainer(config)
        
        pdf_service = container.get_pdf_service()
        assert pdf_service.config.max_pdf_size_mb == 5
        assert pdf_service.max_size_bytes == 5 * 1024 * 1024
        
        openai_service = container.get_openai_service()
        assert openai_service.config.openai_model == 'gpt-3.5-turbo'
        assert openai_service.model == 'gpt-3.5-turbo'
        
        twilio_service = container.get_twilio_service()
        assert twilio_service.config.twilio_phone_number == '+1234567890'