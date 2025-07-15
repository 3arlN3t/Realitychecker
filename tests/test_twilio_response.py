"""
Tests for the Twilio response service.

This module contains unit tests for the TwilioResponseService class,
testing message formatting, sending functionality, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from twilio.base.exceptions import TwilioException

from app.services.twilio_response import TwilioResponseService
from app.models.data_models import JobAnalysisResult, JobClassification, AppConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AppConfig(
        openai_api_key="test-openai-key",
        twilio_account_sid="test-account-sid",
        twilio_auth_token="test-auth-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO",
        webhook_validation=True
    )


@pytest.fixture
def sample_analysis_result():
    """Create a sample analysis result for testing."""
    return JobAnalysisResult(
        trust_score=75,
        classification=JobClassification.SUSPICIOUS,
        reasons=[
            "Company requests upfront payment",
            "Salary seems too high for requirements",
            "Limited company information available"
        ],
        confidence=0.85
    )


@pytest.fixture
def legit_analysis_result():
    """Create a legit job analysis result for testing."""
    return JobAnalysisResult(
        trust_score=90,
        classification=JobClassification.LEGIT,
        reasons=[
            "Well-established company with online presence",
            "Realistic salary expectations",
            "Clear job requirements and responsibilities"
        ],
        confidence=0.92
    )


@pytest.fixture
def scam_analysis_result():
    """Create a scam job analysis result for testing."""
    return JobAnalysisResult(
        trust_score=15,
        classification=JobClassification.LIKELY_SCAM,
        reasons=[
            "Requests personal financial information upfront",
            "Promises unrealistic earnings",
            "No verifiable company contact information"
        ],
        confidence=0.95
    )


class TestTwilioResponseService:
    """Test cases for TwilioResponseService."""
    
    @patch('app.services.twilio_response.Client')
    @patch('app.services.twilio_response.get_config')
    def test_init_with_config(self, mock_get_config, mock_client, mock_config):
        """Test service initialization with provided config."""
        service = TwilioResponseService(mock_config)
        
        mock_client.assert_called_once_with(
            mock_config.twilio_account_sid,
            mock_config.twilio_auth_token
        )
        mock_get_config.assert_not_called()
    
    @patch('app.services.twilio_response.Client')
    @patch('app.services.twilio_response.get_config')
    def test_init_without_config(self, mock_get_config, mock_client, mock_config):
        """Test service initialization without provided config."""
        mock_get_config.return_value = mock_config
        
        service = TwilioResponseService()
        
        mock_get_config.assert_called_once()
        mock_client.assert_called_once_with(
            mock_config.twilio_account_sid,
            mock_config.twilio_auth_token
        )
    
    @patch('app.services.twilio_response.Client')
    def test_send_analysis_result_success(self, mock_client, mock_config, sample_analysis_result):
        """Test successful sending of analysis result."""
        # Setup mock
        mock_message = Mock()
        mock_message.sid = "test-message-sid"
        mock_client.return_value.messages.create.return_value = mock_message
        
        service = TwilioResponseService(mock_config)
        result = service.send_analysis_result("whatsapp:+1987654321", sample_analysis_result)
        
        assert result is True
        mock_client.return_value.messages.create.assert_called_once()
        
        # Verify call arguments
        call_args = mock_client.return_value.messages.create.call_args
        assert call_args.kwargs['to'] == "whatsapp:+1987654321"
        assert call_args.kwargs['from_'] == "whatsapp:+1234567890"
        assert "*Trust Score:* 75/100" in call_args.kwargs['body']
        assert "Suspicious" in call_args.kwargs['body']
    
    @patch('app.services.twilio_response.Client')
    def test_send_analysis_result_twilio_exception(self, mock_client, mock_config, sample_analysis_result):
        """Test handling of Twilio exception when sending analysis result."""
        mock_client.return_value.messages.create.side_effect = TwilioException("API Error")
        
        service = TwilioResponseService(mock_config)
        result = service.send_analysis_result("whatsapp:+1987654321", sample_analysis_result)
        
        assert result is False
    
    @patch('app.services.twilio_response.Client')
    def test_send_analysis_result_general_exception(self, mock_client, mock_config, sample_analysis_result):
        """Test handling of general exception when sending analysis result."""
        mock_client.return_value.messages.create.side_effect = Exception("Unexpected error")
        
        service = TwilioResponseService(mock_config)
        result = service.send_analysis_result("whatsapp:+1987654321", sample_analysis_result)
        
        assert result is False
    
    @patch('app.services.twilio_response.Client')
    def test_send_error_message_success(self, mock_client, mock_config):
        """Test successful sending of error message."""
        mock_message = Mock()
        mock_message.sid = "test-error-message-sid"
        mock_client.return_value.messages.create.return_value = mock_message
        
        service = TwilioResponseService(mock_config)
        result = service.send_error_message("whatsapp:+1987654321", "pdf_processing")
        
        assert result is True
        mock_client.return_value.messages.create.assert_called_once()
        
        # Verify call arguments
        call_args = mock_client.return_value.messages.create.call_args
        assert call_args.kwargs['to'] == "whatsapp:+1987654321"
        assert "PDF Processing Error" in call_args.kwargs['body']
    
    @patch('app.services.twilio_response.Client')
    def test_send_welcome_message_success(self, mock_client, mock_config):
        """Test successful sending of welcome message."""
        mock_message = Mock()
        mock_message.sid = "test-welcome-message-sid"
        mock_client.return_value.messages.create.return_value = mock_message
        
        service = TwilioResponseService(mock_config)
        result = service.send_welcome_message("whatsapp:+1987654321")
        
        assert result is True
        mock_client.return_value.messages.create.assert_called_once()
        
        # Verify call arguments
        call_args = mock_client.return_value.messages.create.call_args
        assert call_args.kwargs['to'] == "whatsapp:+1987654321"
        assert "Welcome to Reality Checker" in call_args.kwargs['body']
    
    def test_format_analysis_message_suspicious(self, mock_config, sample_analysis_result):
        """Test formatting of suspicious job analysis message."""
        service = TwilioResponseService(mock_config)
        message = service._format_analysis_message(sample_analysis_result)
        
        assert "⚠️" in message  # Warning emoji for suspicious
        assert "*Trust Score:* 75/100" in message
        assert "*Classification:* Suspicious" in message
        assert "Company requests upfront payment" in message
        assert "Exercise caution" in message
        assert "85.0%" in message  # Confidence percentage
    
    def test_format_analysis_message_legit(self, mock_config, legit_analysis_result):
        """Test formatting of legitimate job analysis message."""
        service = TwilioResponseService(mock_config)
        message = service._format_analysis_message(legit_analysis_result)
        
        assert "✅" in message  # Check mark emoji for legit
        assert "*Trust Score:* 90/100" in message
        assert "*Classification:* Legit" in message
        assert "Well-established company" in message
        assert "appears legitimate" in message
    
    def test_format_analysis_message_scam(self, mock_config, scam_analysis_result):
        """Test formatting of scam job analysis message."""
        service = TwilioResponseService(mock_config)
        message = service._format_analysis_message(scam_analysis_result)
        
        assert "🚨" in message  # Alert emoji for scam
        assert "*Trust Score:* 15/100" in message
        assert "*Classification:* Likely Scam" in message
        assert "Requests personal financial information" in message
        assert "may be a scam" in message
    
    def test_get_error_message_pdf_processing(self, mock_config):
        """Test PDF processing error message."""
        service = TwilioResponseService(mock_config)
        message = service._get_error_message("pdf_processing")
        
        assert "PDF Processing Error" in message
        assert "valid PDF" in message
        assert "10MB" in message
    
    def test_get_error_message_analysis(self, mock_config):
        """Test analysis error message."""
        service = TwilioResponseService(mock_config)
        message = service._get_error_message("analysis")
        
        assert "Analysis Error" in message
        assert "analyzing the job posting" in message
    
    def test_get_error_message_general(self, mock_config):
        """Test general error message."""
        service = TwilioResponseService(mock_config)
        message = service._get_error_message("general")
        
        assert "Service Error" in message
        assert "technical difficulties" in message
    
    def test_get_error_message_unknown_type(self, mock_config):
        """Test unknown error type defaults to general message."""
        service = TwilioResponseService(mock_config)
        message = service._get_error_message("unknown_error_type")
        
        assert "Service Error" in message  # Should default to general
    
    def test_get_welcome_message(self, mock_config):
        """Test welcome message content."""
        service = TwilioResponseService(mock_config)
        message = service._get_welcome_message()
        
        assert "Welcome to Reality Checker" in message
        assert "job scams" in message
        assert "Trust score" in message
        assert "Stay safe" in message