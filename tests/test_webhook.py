"""
Integration tests for the Twilio webhook endpoint.

This module contains comprehensive tests for the WhatsApp webhook endpoint,
including signature validation, request processing, and error handling.
"""

import pytest
import hashlib
import hmac
import base64
from unittest.mock import Mock, AsyncMock, patch
from urllib.parse import urlencode

from fastapi.testclient import TestClient
from app.main import app
from app.models.data_models import TwilioWebhookRequest, JobAnalysisResult, JobClassification


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    config = Mock()
    config.webhook_validation = True
    config.twilio_auth_token = "test_auth_token"
    config.twilio_phone_number = "+1234567890"
    config.openai_api_key = "test_openai_key"
    config.twilio_account_sid = "test_account_sid"
    config.max_pdf_size_mb = 10
    config.openai_model = "gpt-4"
    config.log_level = "INFO"
    return config


@pytest.fixture
def sample_webhook_data():
    """Sample Twilio webhook data for testing."""
    return {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1987654321",
        "To": "whatsapp:+1234567890",
        "Body": "Software Engineer position at Google. Salary $150k. Remote work available.",
        "NumMedia": "0"
    }


@pytest.fixture
def sample_media_webhook_data():
    """Sample Twilio webhook data with media attachment."""
    return {
        "MessageSid": "SM1234567890abcdef1234567890abcdef",
        "From": "whatsapp:+1987654321",
        "To": "whatsapp:+1234567890",
        "Body": "",
        "NumMedia": "1",
        "MediaUrl0": "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test",
        "MediaContentType0": "application/pdf"
    }


def create_twilio_signature(url: str, params: dict, auth_token: str) -> str:
    """
    Create a valid Twilio signature for testing.
    
    Args:
        url: The webhook URL
        params: POST parameters
        auth_token: Twilio auth token
        
    Returns:
        Base64-encoded HMAC-SHA1 signature
    """
    # Sort parameters by key as Twilio does
    sorted_params = sorted(params.items())
    data_string = url + urlencode(sorted_params)
    
    # Create HMAC-SHA1 signature
    signature = base64.b64encode(
        hmac.new(
            auth_token.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    return signature


class TestWebhookEndpoint:
    """Test cases for the webhook endpoint."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_get_request(self, mock_handler_class, mock_get_config, client):
        """Test GET request to webhook endpoint."""
        response = client.get("/webhook/whatsapp")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "WhatsApp webhook endpoint is operational" in data["message"]
        assert data["methods"] == "POST"
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_post_text_message_success(
        self, mock_handler_class, mock_get_config, client, mock_config, sample_webhook_data
    ):
        """Test successful processing of text message webhook."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_handler = AsyncMock()
        mock_handler.process_message.return_value = True
        mock_handler_class.return_value = mock_handler
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_webhook_data, mock_config.twilio_auth_token)
        
        # Make request with signature
        response = client.post(
            "/webhook/whatsapp",
            data=sample_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        assert response.status_code == 200
        assert response.text == ""
        
        # Verify message handler was called
        mock_handler.process_message.assert_called_once()
        call_args = mock_handler.process_message.call_args[0][0]
        assert isinstance(call_args, TwilioWebhookRequest)
        assert call_args.MessageSid == sample_webhook_data["MessageSid"]
        assert call_args.From == sample_webhook_data["From"]
        assert call_args.Body == sample_webhook_data["Body"]
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_post_media_message_success(
        self, mock_handler_class, mock_get_config, client, mock_config, sample_media_webhook_data
    ):
        """Test successful processing of media message webhook."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_handler = AsyncMock()
        mock_handler.process_message.return_value = True
        mock_handler_class.return_value = mock_handler
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_media_webhook_data, mock_config.twilio_auth_token)
        
        # Make request with signature
        response = client.post(
            "/webhook/whatsapp",
            data=sample_media_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        assert response.status_code == 200
        assert response.text == ""
        
        # Verify message handler was called
        mock_handler.process_message.assert_called_once()
        call_args = mock_handler.process_message.call_args[0][0]
        assert isinstance(call_args, TwilioWebhookRequest)
        assert call_args.has_media is True
        assert call_args.MediaUrl0 == sample_media_webhook_data["MediaUrl0"]
        assert call_args.MediaContentType0 == sample_media_webhook_data["MediaContentType0"]
    
    @patch('app.api.webhook.get_config')
    def test_webhook_invalid_signature(self, mock_get_config, client, mock_config, sample_webhook_data):
        """Test webhook request with invalid signature."""
        mock_get_config.return_value = mock_config
        
        # Make request with invalid signature
        response = client.post(
            "/webhook/whatsapp",
            data=sample_webhook_data,
            headers={"X-Twilio-Signature": "invalid_signature"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["message"] == "Invalid webhook signature"
    
    @patch('app.api.webhook.get_config')
    def test_webhook_missing_signature(self, mock_get_config, client, mock_config, sample_webhook_data):
        """Test webhook request with missing signature header."""
        mock_get_config.return_value = mock_config
        
        # Make request without signature header
        response = client.post("/webhook/whatsapp", data=sample_webhook_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["message"] == "Invalid webhook signature"
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_signature_validation_disabled(
        self, mock_handler_class, mock_get_config, client, mock_config, sample_webhook_data
    ):
        """Test webhook when signature validation is disabled."""
        # Disable signature validation
        mock_config.webhook_validation = False
        mock_get_config.return_value = mock_config
        
        mock_handler = AsyncMock()
        mock_handler.process_message.return_value = True
        mock_handler_class.return_value = mock_handler
        
        # Make request without signature
        response = client.post("/webhook/whatsapp", data=sample_webhook_data)
        
        assert response.status_code == 200
        mock_handler.process_message.assert_called_once()
    
    @patch('app.api.webhook.get_config')
    def test_webhook_missing_required_fields(self, mock_get_config, client, mock_config):
        """Test webhook request with missing required fields."""
        mock_get_config.return_value = mock_config
        
        # Create incomplete data
        incomplete_data = {
            "MessageSid": "SM1234567890abcdef1234567890abcdef",
            # Missing From, To, Body, NumMedia
        }
        
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, incomplete_data, mock_config.twilio_auth_token)
        
        response = client.post(
            "/webhook/whatsapp",
            data=incomplete_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_invalid_data_validation(
        self, mock_handler_class, mock_get_config, client, mock_config
    ):
        """Test webhook request with invalid data that fails model validation."""
        mock_get_config.return_value = mock_config
        
        # Create data that will fail TwilioWebhookRequest validation
        invalid_data = {
            "MessageSid": "",  # Empty MessageSid should fail validation
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Test message",
            "NumMedia": "0"
        }
        
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, invalid_data, mock_config.twilio_auth_token)
        
        response = client.post(
            "/webhook/whatsapp",
            data=invalid_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "details" in data  # Custom validation handler uses "details"
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_message_handler_failure(
        self, mock_handler_class, mock_get_config, client, mock_config, sample_webhook_data
    ):
        """Test webhook when message handler fails to process message."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_handler = AsyncMock()
        mock_handler.process_message.return_value = False  # Simulate failure
        mock_handler_class.return_value = mock_handler
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_webhook_data, mock_config.twilio_auth_token)
        
        # Make request
        response = client.post(
            "/webhook/whatsapp",
            data=sample_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        # Should still return 200 (Twilio expects this)
        assert response.status_code == 200
        mock_handler.process_message.assert_called_once()
    
    @patch('app.api.webhook.get_config')
    @patch('app.api.webhook.MessageHandlerService')
    def test_webhook_message_handler_exception(
        self, mock_handler_class, mock_get_config, client, mock_config, sample_webhook_data
    ):
        """Test webhook when message handler raises an exception."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_handler = AsyncMock()
        mock_handler.process_message.side_effect = Exception("Processing failed")
        mock_handler_class.return_value = mock_handler
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_webhook_data, mock_config.twilio_auth_token)
        
        # Make request
        response = client.post(
            "/webhook/whatsapp",
            data=sample_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error processing webhook" in data["message"]


class TestSignatureValidation:
    """Test cases for Twilio signature validation."""
    
    def test_signature_validation_success(self):
        """Test successful signature validation."""
        from app.api.webhook import validate_twilio_signature
        
        # Mock request and config
        request = Mock()
        request.url = "https://example.com/webhook/whatsapp"
        request.headers = {"X-Twilio-Signature": ""}
        
        config = Mock()
        config.webhook_validation = True
        config.twilio_auth_token = "test_token"
        
        body_data = {"param1": "value1", "param2": "value2"}
        
        # Create valid signature
        url = str(request.url)
        sorted_params = sorted(body_data.items())
        data_string = url + urlencode(sorted_params)
        expected_signature = base64.b64encode(
            hmac.new(
                config.twilio_auth_token.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        request.headers["X-Twilio-Signature"] = expected_signature
        
        result = validate_twilio_signature(request, body_data, config)
        assert result is True
    
    def test_signature_validation_disabled(self):
        """Test signature validation when disabled."""
        from app.api.webhook import validate_twilio_signature
        
        request = Mock()
        config = Mock()
        config.webhook_validation = False
        
        result = validate_twilio_signature(request, {}, config)
        assert result is True
    
    def test_signature_validation_missing_header(self):
        """Test signature validation with missing header."""
        from app.api.webhook import validate_twilio_signature
        
        request = Mock()
        request.headers = {}  # No signature header
        
        config = Mock()
        config.webhook_validation = True
        
        result = validate_twilio_signature(request, {}, config)
        assert result is False
    
    def test_signature_validation_invalid_signature(self):
        """Test signature validation with invalid signature."""
        from app.api.webhook import validate_twilio_signature
        
        request = Mock()
        request.url = "https://example.com/webhook/whatsapp"
        request.headers = {"X-Twilio-Signature": "invalid_signature"}
        
        config = Mock()
        config.webhook_validation = True
        config.twilio_auth_token = "test_token"
        
        result = validate_twilio_signature(request, {"test": "data"}, config)
        assert result is False


class TestWebhookIntegration:
    """Integration tests for complete webhook processing flow."""
    
    @patch('app.services.message_handler.MessageHandlerService.process_message')
    @patch('app.api.webhook.get_config')
    def test_complete_webhook_flow_text_message(
        self, mock_get_config, mock_process_message, client, mock_config, sample_webhook_data
    ):
        """Test complete webhook processing flow for text message."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_process_message.return_value = True
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_webhook_data, mock_config.twilio_auth_token)
        
        # Make request
        response = client.post(
            "/webhook/whatsapp",
            data=sample_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.text == ""
        
        # Verify processing was called
        mock_process_message.assert_called_once()
    
    @patch('app.services.message_handler.MessageHandlerService.process_message')
    @patch('app.api.webhook.get_config')
    def test_complete_webhook_flow_media_message(
        self, mock_get_config, mock_process_message, client, mock_config, sample_media_webhook_data
    ):
        """Test complete webhook processing flow for media message."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        mock_process_message.return_value = True
        
        # Create valid signature
        url = "http://testserver/webhook/whatsapp"
        signature = create_twilio_signature(url, sample_media_webhook_data, mock_config.twilio_auth_token)
        
        # Make request
        response = client.post(
            "/webhook/whatsapp",
            data=sample_media_webhook_data,
            headers={"X-Twilio-Signature": signature}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.text == ""
        
        # Verify processing was called
        mock_process_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])