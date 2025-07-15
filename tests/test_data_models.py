"""
Unit tests for data models in the Reality Checker WhatsApp bot.

Tests validation, serialization, and behavior of core data models.
"""

import pytest
import os
from unittest.mock import patch
from app.models.data_models import (
    TwilioWebhookRequest,
    JobAnalysisResult,
    JobClassification,
    AppConfig
)


class TestTwilioWebhookRequest:
    """Test cases for TwilioWebhookRequest dataclass."""
    
    def test_valid_text_message(self):
        """Test creating a valid text message request."""
        request = TwilioWebhookRequest(
            MessageSid="SM123456789",
            From="+1234567890",
            To="+0987654321",
            Body="Test job posting content",
            NumMedia=0
        )
        
        assert request.MessageSid == "SM123456789"
        assert request.From == "+1234567890"
        assert request.To == "+0987654321"
        assert request.Body == "Test job posting content"
        assert request.NumMedia == 0
        assert not request.has_media
        assert not request.is_pdf_media
    
    def test_valid_media_message(self):
        """Test creating a valid media message request."""
        request = TwilioWebhookRequest(
            MessageSid="SM123456789",
            From="+1234567890",
            To="+0987654321",
            Body="",
            NumMedia=1,
            MediaUrl0="https://api.twilio.com/media/123.pdf",
            MediaContentType0="application/pdf"
        )
        
        assert request.has_media
        assert request.is_pdf_media
        assert request.MediaUrl0 == "https://api.twilio.com/media/123.pdf"
        assert request.MediaContentType0 == "application/pdf"
    
    def test_missing_message_sid_raises_error(self):
        """Test that missing MessageSid raises ValueError."""
        with pytest.raises(ValueError, match="MessageSid is required"):
            TwilioWebhookRequest(
                MessageSid="",
                From="+1234567890",
                To="+0987654321",
                Body="Test",
                NumMedia=0
            )
    
    def test_missing_from_raises_error(self):
        """Test that missing From phone number raises ValueError."""
        with pytest.raises(ValueError, match="From phone number is required"):
            TwilioWebhookRequest(
                MessageSid="SM123456789",
                From="",
                To="+0987654321",
                Body="Test",
                NumMedia=0
            )
    
    def test_missing_to_raises_error(self):
        """Test that missing To phone number raises ValueError."""
        with pytest.raises(ValueError, match="To phone number is required"):
            TwilioWebhookRequest(
                MessageSid="SM123456789",
                From="+1234567890",
                To="",
                Body="Test",
                NumMedia=0
            )
    
    def test_negative_num_media_raises_error(self):
        """Test that negative NumMedia raises ValueError."""
        with pytest.raises(ValueError, match="NumMedia cannot be negative"):
            TwilioWebhookRequest(
                MessageSid="SM123456789",
                From="+1234567890",
                To="+0987654321",
                Body="Test",
                NumMedia=-1
            )
    
    def test_media_without_url_raises_error(self):
        """Test that NumMedia > 0 without MediaUrl0 raises ValueError."""
        with pytest.raises(ValueError, match="MediaUrl0 is required when NumMedia > 0"):
            TwilioWebhookRequest(
                MessageSid="SM123456789",
                From="+1234567890",
                To="+0987654321",
                Body="Test",
                NumMedia=1
            )
    
    def test_non_pdf_media(self):
        """Test media message that is not a PDF."""
        request = TwilioWebhookRequest(
            MessageSid="SM123456789",
            From="+1234567890",
            To="+0987654321",
            Body="",
            NumMedia=1,
            MediaUrl0="https://api.twilio.com/media/123.jpg",
            MediaContentType0="image/jpeg"
        )
        
        assert request.has_media
        assert not request.is_pdf_media


class TestJobAnalysisResult:
    """Test cases for JobAnalysisResult dataclass."""
    
    def test_valid_analysis_result(self):
        """Test creating a valid analysis result."""
        result = JobAnalysisResult(
            trust_score=75,
            classification=JobClassification.SUSPICIOUS,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.8
        )
        
        assert result.trust_score == 75
        assert result.classification == JobClassification.SUSPICIOUS
        assert result.classification_text == "Suspicious"
        assert len(result.reasons) == 3
        assert result.confidence == 0.8
    
    def test_trust_score_below_zero_raises_error(self):
        """Test that trust score below 0 raises ValueError."""
        with pytest.raises(ValueError, match="Trust score must be between 0 and 100"):
            JobAnalysisResult(
                trust_score=-1,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"]
            )
    
    def test_trust_score_above_hundred_raises_error(self):
        """Test that trust score above 100 raises ValueError."""
        with pytest.raises(ValueError, match="Trust score must be between 0 and 100"):
            JobAnalysisResult(
                trust_score=101,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"]
            )
    
    def test_invalid_classification_raises_error(self):
        """Test that invalid classification raises ValueError."""
        with pytest.raises(ValueError, match="Classification must be a JobClassification enum"):
            JobAnalysisResult(
                trust_score=50,
                classification="Invalid",  # type: ignore
                reasons=["Reason 1", "Reason 2", "Reason 3"]
            )
    
    def test_wrong_number_of_reasons_raises_error(self):
        """Test that wrong number of reasons raises ValueError."""
        with pytest.raises(ValueError, match="Exactly 3 reasons must be provided"):
            JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2"]  # Only 2 reasons
            )
    
    def test_empty_reason_raises_error(self):
        """Test that empty reason raises ValueError."""
        with pytest.raises(ValueError, match="All reasons must be non-empty strings"):
            JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "", "Reason 3"]  # Empty reason
            )
    
    def test_confidence_below_zero_raises_error(self):
        """Test that confidence below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"],
                confidence=-0.1
            )
    
    def test_confidence_above_one_raises_error(self):
        """Test that confidence above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"],
                confidence=1.1
            )
    
    def test_all_classification_types(self):
        """Test all classification enum values."""
        classifications = [
            (JobClassification.LEGIT, "Legit"),
            (JobClassification.SUSPICIOUS, "Suspicious"),
            (JobClassification.LIKELY_SCAM, "Likely Scam")
        ]
        
        for classification, expected_text in classifications:
            result = JobAnalysisResult(
                trust_score=50,
                classification=classification,
                reasons=["Reason 1", "Reason 2", "Reason 3"]
            )
            assert result.classification_text == expected_text


class TestAppConfig:
    """Test cases for AppConfig dataclass."""
    
    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = AppConfig(
            openai_api_key="sk-test123",
            twilio_account_sid="AC123456789",
            twilio_auth_token="auth_token_123",
            twilio_phone_number="+1234567890"
        )
        
        assert config.openai_api_key == "sk-test123"
        assert config.twilio_account_sid == "AC123456789"
        assert config.twilio_auth_token == "auth_token_123"
        assert config.twilio_phone_number == "+1234567890"
        assert config.max_pdf_size_mb == 10  # Default value
        assert config.openai_model == "gpt-4"  # Default value
        assert config.log_level == "INFO"  # Default value
        assert config.webhook_validation is True  # Default value
    
    def test_custom_optional_values(self):
        """Test configuration with custom optional values."""
        config = AppConfig(
            openai_api_key="sk-test123",
            twilio_account_sid="AC123456789",
            twilio_auth_token="auth_token_123",
            twilio_phone_number="+1234567890",
            max_pdf_size_mb=20,
            openai_model="gpt-3.5-turbo",
            log_level="DEBUG",
            webhook_validation=False
        )
        
        assert config.max_pdf_size_mb == 20
        assert config.openai_model == "gpt-3.5-turbo"
        assert config.log_level == "DEBUG"
        assert config.webhook_validation is False
    
    def test_missing_openai_key_raises_error(self):
        """Test that missing OpenAI API key raises ValueError."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            AppConfig(
                openai_api_key="",
                twilio_account_sid="AC123456789",
                twilio_auth_token="auth_token_123",
                twilio_phone_number="+1234567890"
            )
    
    def test_missing_twilio_sid_raises_error(self):
        """Test that missing Twilio Account SID raises ValueError."""
        with pytest.raises(ValueError, match="Twilio Account SID is required"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="",
                twilio_auth_token="auth_token_123",
                twilio_phone_number="+1234567890"
            )
    
    def test_missing_twilio_token_raises_error(self):
        """Test that missing Twilio Auth Token raises ValueError."""
        with pytest.raises(ValueError, match="Twilio Auth Token is required"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="AC123456789",
                twilio_auth_token="",
                twilio_phone_number="+1234567890"
            )
    
    def test_missing_twilio_phone_raises_error(self):
        """Test that missing Twilio phone number raises ValueError."""
        with pytest.raises(ValueError, match="Twilio phone number is required"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="AC123456789",
                twilio_auth_token="auth_token_123",
                twilio_phone_number=""
            )
    
    def test_invalid_pdf_size_raises_error(self):
        """Test that invalid PDF size raises ValueError."""
        with pytest.raises(ValueError, match="Max PDF size must be positive"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="AC123456789",
                twilio_auth_token="auth_token_123",
                twilio_phone_number="+1234567890",
                max_pdf_size_mb=0
            )
    
    def test_empty_openai_model_raises_error(self):
        """Test that empty OpenAI model raises ValueError."""
        with pytest.raises(ValueError, match="OpenAI model is required"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="AC123456789",
                twilio_auth_token="auth_token_123",
                twilio_phone_number="+1234567890",
                openai_model=""
            )
    
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            AppConfig(
                openai_api_key="sk-test123",
                twilio_account_sid="AC123456789",
                twilio_auth_token="auth_token_123",
                twilio_phone_number="+1234567890",
                log_level="INVALID"
            )
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-env-test",
        "TWILIO_ACCOUNT_SID": "AC-env-test",
        "TWILIO_AUTH_TOKEN": "token-env-test",
        "TWILIO_PHONE_NUMBER": "+1-env-test",
        "MAX_PDF_SIZE_MB": "15",
        "OPENAI_MODEL": "gpt-3.5-turbo",
        "LOG_LEVEL": "DEBUG",
        "WEBHOOK_VALIDATION": "false"
    })
    def test_from_env_with_all_vars(self):
        """Test creating config from environment variables."""
        config = AppConfig.from_env()
        
        assert config.openai_api_key == "sk-env-test"
        assert config.twilio_account_sid == "AC-env-test"
        assert config.twilio_auth_token == "token-env-test"
        assert config.twilio_phone_number == "+1-env-test"
        assert config.max_pdf_size_mb == 15
        assert config.openai_model == "gpt-3.5-turbo"
        assert config.log_level == "DEBUG"
        assert config.webhook_validation is False
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_with_defaults(self):
        """Test creating config from environment with default values (will fail validation)."""
        # This test verifies that from_env loads defaults but validation will fail
        # when required environment variables are missing
        with pytest.raises(ValueError):
            AppConfig.from_env()
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-valid",
        "TWILIO_ACCOUNT_SID": "AC-valid",
        "TWILIO_AUTH_TOKEN": "token-valid",
        "TWILIO_PHONE_NUMBER": "+1-valid"
    })
    def test_from_env_validation_success(self):
        """Test that from_env creates valid config when env vars are set."""
        config = AppConfig.from_env()
        # Should not raise any validation errors
        assert config.openai_api_key == "sk-valid"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_validation_failure(self):
        """Test that from_env config fails validation with missing required vars."""
        with pytest.raises(ValueError):
            AppConfig.from_env()