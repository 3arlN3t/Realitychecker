"""
Integration tests for Twilio API service.

These tests verify the integration between our application and the Twilio API,
using real API calls with test data to ensure proper functionality.
"""

import os
import pytest
from unittest.mock import patch, Mock
import json
from twilio.base.exceptions import TwilioRestException, TwilioException

from app.services.twilio_response import TwilioResponseService
from app.models.data_models import JobAnalysisResult, JobClassification, AppConfig
from tests.fixtures.job_ad_samples import TestPhoneNumbers


@pytest.fixture
def test_config():
    """Create a test configuration with real API keys from environment."""
    # Use real API keys for integration tests, but with fallback mocks
    return AppConfig(
        openai_api_key="test-openai-key",
        twilio_account_sid=os.environ.get("TWILIO_ACCOUNT_SID", "test-account-sid"),
        twilio_auth_token=os.environ.get("TWILIO_AUTH_TOKEN", "test-auth-token"),
        twilio_phone_number=os.environ.get("TWILIO_PHONE_NUMBER", "+1234567890"),
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO",
        webhook_validation=True
    )


@pytest.fixture
def twilio_service(test_config):
    """Create Twilio response service instance for testing."""
    return TwilioResponseService(test_config)


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


@pytest.mark.integration
class TestTwilioIntegration:
    """Integration tests for Twilio API service."""
    
    @pytest.mark.skipif(not (os.environ.get("TWILIO_ACCOUNT_SID") and 
                            os.environ.get("TWILIO_AUTH_TOKEN") and
                            os.environ.get("TWILIO_PHONE_NUMBER")),
                       reason="Skipping live API test: Twilio credentials not set")
    def test_live_api_connection(self, twilio_service):
        """Test that we can connect to the Twilio API with valid credentials."""
        # This test verifies we can establish a connection to the API
        try:
            # Just fetch account info to verify credentials
            account_info = twilio_service.client.api.accounts(twilio_service.client.account_sid).fetch()
            assert account_info.sid == twilio_service.client.account_sid
        except TwilioRestException as e:
            if e.code == 20003:  # Authentication Error
                pytest.fail("Authentication failed - check Twilio credentials")
            else:
                pytest.fail(f"Twilio API error occurred: {str(e)}")
    
    @pytest.mark.skipif(not (os.environ.get("TWILIO_ACCOUNT_SID") and 
                            os.environ.get("TWILIO_AUTH_TOKEN") and
                            os.environ.get("TWILIO_PHONE_NUMBER") and
                            os.environ.get("TEST_RECIPIENT_PHONE_NUMBER")),
                       reason="Skipping live message test: Required environment variables not set")
    def test_send_test_message(self, twilio_service):
        """Test sending a real test message via Twilio API."""
        # Only run this test if we have a test recipient number
        test_recipient = os.environ.get("TEST_RECIPIENT_PHONE_NUMBER")
        
        # Format with WhatsApp prefix if not already present
        if not test_recipient.startswith("whatsapp:"):
            test_recipient = f"whatsapp:{test_recipient}"
        
        # Send a test message
        result = twilio_service.client.messages.create(
            body="This is an automated test message from Reality Checker WhatsApp Bot.",
            from_=f"whatsapp:{twilio_service.config.twilio_phone_number.lstrip('+')}",
            to=test_recipient
        )
        
        # Verify the message was sent successfully
        assert result.sid is not None
        assert result.status in ["queued", "sending", "sent"]
    
    def test_message_formatting_suspicious(self, twilio_service, sample_analysis_result):
        """Test formatting of suspicious job analysis message."""
        message = twilio_service._format_analysis_message(sample_analysis_result)
        
        # Check for required elements in the message
        assert "⚠️" in message  # Warning emoji for suspicious
        assert "*Trust Score:* 75/100" in message
        assert "*Classification:* Suspicious" in message
        assert "Company requests upfront payment" in message
        assert "Exercise caution" in message
        assert "85.0%" in message  # Confidence percentage
        
        # Check message structure and readability
        assert message.count("\n\n") >= 2  # Should have paragraph breaks
        assert len(message) <= 1600  # WhatsApp message limit
    
    def test_message_formatting_legit(self, twilio_service, legit_analysis_result):
        """Test formatting of legitimate job analysis message."""
        message = twilio_service._format_analysis_message(legit_analysis_result)
        
        # Check for required elements in the message
        assert "✅" in message  # Check mark emoji for legit
        assert "*Trust Score:* 90/100" in message
        assert "*Classification:* Legit" in message
        assert "Well-established company" in message
        assert "appears legitimate" in message
        
        # Check message structure and readability
        assert message.count("\n\n") >= 2  # Should have paragraph breaks
        assert len(message) <= 1600  # WhatsApp message limit
    
    def test_message_formatting_scam(self, twilio_service, scam_analysis_result):
        """Test formatting of scam job analysis message."""
        message = twilio_service._format_analysis_message(scam_analysis_result)
        
        # Check for required elements in the message
        assert "🚨" in message  # Alert emoji for scam
        assert "*Trust Score:* 15/100" in message
        assert "*Classification:* Likely Scam" in message
        assert "Requests personal financial information" in message
        assert "may be a scam" in message
        
        # Check message structure and readability
        assert message.count("\n\n") >= 2  # Should have paragraph breaks
        assert len(message) <= 1600  # WhatsApp message limit
    
    def test_error_message_formatting(self, twilio_service):
        """Test formatting of error messages."""
        # Test different error types
        pdf_error = twilio_service._get_error_message("pdf_processing")
        analysis_error = twilio_service._get_error_message("analysis")
        general_error = twilio_service._get_error_message("general")
        
        # Check for required elements in the messages
        assert "PDF Processing Error" in pdf_error
        assert "Analysis Error" in analysis_error
        assert "Service Error" in general_error
        
        # Check message structure and readability
        assert len(pdf_error) <= 1600  # WhatsApp message limit
        assert len(analysis_error) <= 1600  # WhatsApp message limit
        assert len(general_error) <= 1600  # WhatsApp message limit
    
    def test_welcome_message_formatting(self, twilio_service):
        """Test formatting of welcome message."""
        welcome_message = twilio_service._get_welcome_message()
        
        # Check for required elements in the message
        assert "Welcome to Reality Checker" in welcome_message
        assert "job scams" in welcome_message
        assert "Trust score" in welcome_message
        
        # Check message structure and readability
        assert welcome_message.count("\n\n") >= 2  # Should have paragraph breaks
        assert len(welcome_message) <= 1600  # WhatsApp message limit
    
    @pytest.mark.skipif(not (os.environ.get("TWILIO_ACCOUNT_SID") and 
                            os.environ.get("TWILIO_AUTH_TOKEN") and
                            os.environ.get("TWILIO_PHONE_NUMBER")),
                       reason="Skipping live API test: Twilio credentials not set")
    def test_send_analysis_result_integration(self, twilio_service, sample_analysis_result):
        """Test sending analysis result via Twilio API with mocked recipient."""
        # Mock the messages.create method to avoid sending actual messages
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_message = Mock()
            mock_message.sid = "test-message-sid"
            mock_create.return_value = mock_message
            
            # Send the analysis result
            result = twilio_service.send_analysis_result(
                TestPhoneNumbers.LEGITIMATE_USER, 
                sample_analysis_result
            )
            
            # Verify the result
            assert result is True
            mock_create.assert_called_once()
            
            # Verify call arguments
            call_args = mock_create.call_args
            assert call_args.kwargs['to'] == TestPhoneNumbers.LEGITIMATE_USER
            assert call_args.kwargs['from_'].startswith("whatsapp:")
            assert "*Trust Score:* 75/100" in call_args.kwargs['body']
            assert "Suspicious" in call_args.kwargs['body']
    
    @pytest.mark.skipif(not (os.environ.get("TWILIO_ACCOUNT_SID") and 
                            os.environ.get("TWILIO_AUTH_TOKEN") and
                            os.environ.get("TWILIO_PHONE_NUMBER")),
                       reason="Skipping live API test: Twilio credentials not set")
    def test_send_error_message_integration(self, twilio_service):
        """Test sending error message via Twilio API with mocked recipient."""
        # Mock the messages.create method to avoid sending actual messages
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_message = Mock()
            mock_message.sid = "test-error-message-sid"
            mock_create.return_value = mock_message
            
            # Send the error message
            result = twilio_service.send_error_message(
                TestPhoneNumbers.SUSPICIOUS_USER, 
                "pdf_processing"
            )
            
            # Verify the result
            assert result is True
            mock_create.assert_called_once()
            
            # Verify call arguments
            call_args = mock_create.call_args
            assert call_args.kwargs['to'] == TestPhoneNumbers.SUSPICIOUS_USER
            assert call_args.kwargs['from_'].startswith("whatsapp:")
            assert "PDF Processing Error" in call_args.kwargs['body']
    
    @pytest.mark.skipif(not (os.environ.get("TWILIO_ACCOUNT_SID") and 
                            os.environ.get("TWILIO_AUTH_TOKEN") and
                            os.environ.get("TWILIO_PHONE_NUMBER")),
                       reason="Skipping live API test: Twilio credentials not set")
    def test_send_welcome_message_integration(self, twilio_service):
        """Test sending welcome message via Twilio API with mocked recipient."""
        # Mock the messages.create method to avoid sending actual messages
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_message = Mock()
            mock_message.sid = "test-welcome-message-sid"
            mock_create.return_value = mock_message
            
            # Send the welcome message
            result = twilio_service.send_welcome_message(
                TestPhoneNumbers.HELP_SEEKER
            )
            
            # Verify the result
            assert result is True
            mock_create.assert_called_once()
            
            # Verify call arguments
            call_args = mock_create.call_args
            assert call_args.kwargs['to'] == TestPhoneNumbers.HELP_SEEKER
            assert call_args.kwargs['from_'].startswith("whatsapp:")
            assert "Welcome to Reality Checker" in call_args.kwargs['body']


@pytest.mark.integration
class TestTwilioErrorHandling:
    """Tests for Twilio service error handling."""
    
    def test_authentication_error_handling(self, test_config):
        """Test handling of authentication errors."""
        # Create config with invalid credentials
        invalid_config = AppConfig(
            openai_api_key="test-openai-key",
            twilio_account_sid="invalid-sid",
            twilio_auth_token="invalid-token",
            twilio_phone_number="+1234567890"
        )
        
        # Create service with invalid credentials
        service = TwilioResponseService(invalid_config)
        
        # Mock the messages.create method to simulate authentication error
        with patch.object(service.client.messages, 'create') as mock_create:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = json.dumps({"message": "Authentication error"})
            
            mock_create.side_effect = TwilioRestException(
                status=401,
                uri="/Messages",
                msg="Authentication error",
                code=20003,
                method="POST",
                details={}
            )
            
            # Attempt to send a message
            result = service.send_welcome_message(TestPhoneNumbers.LEGITIMATE_USER)
            
            # Verify the result
            assert result is False
            mock_create.assert_called_once()
    
    def test_rate_limit_error_handling(self, twilio_service):
        """Test handling of rate limit errors."""
        # Mock the messages.create method to simulate rate limit error
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_create.side_effect = TwilioRestException(
                status=429,
                uri="/Messages",
                msg="Too many requests",
                code=20429,
                method="POST",
                details={}
            )
            
            # Attempt to send a message
            result = twilio_service.send_welcome_message(TestPhoneNumbers.LEGITIMATE_USER)
            
            # Verify the result
            assert result is False
            mock_create.assert_called_once()
    
    def test_invalid_number_error_handling(self, twilio_service):
        """Test handling of invalid phone number errors."""
        # Mock the messages.create method to simulate invalid number error
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_create.side_effect = TwilioRestException(
                status=400,
                uri="/Messages",
                msg="Invalid 'To' phone number",
                code=21211,
                method="POST",
                details={}
            )
            
            # Attempt to send a message
            result = twilio_service.send_welcome_message("whatsapp:+1invalid")
            
            # Verify the result
            assert result is False
            mock_create.assert_called_once()
    
    def test_network_error_handling(self, twilio_service):
        """Test handling of network errors."""
        # Mock the messages.create method to simulate network error
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_create.side_effect = TwilioException("Connection error")
            
            # Attempt to send a message
            result = twilio_service.send_welcome_message(TestPhoneNumbers.LEGITIMATE_USER)
            
            # Verify the result
            assert result is False
            mock_create.assert_called_once()
    
    def test_general_exception_handling(self, twilio_service):
        """Test handling of general exceptions."""
        # Mock the messages.create method to simulate unexpected error
        with patch.object(twilio_service.client.messages, 'create') as mock_create:
            mock_create.side_effect = Exception("Unexpected error")
            
            # Attempt to send a message
            result = twilio_service.send_welcome_message(TestPhoneNumbers.LEGITIMATE_USER)
            
            # Verify the result
            assert result is False
            mock_create.assert_called_once()


@pytest.mark.integration
class TestTwilioMessageFormatting:
    """Tests for Twilio message formatting and content."""
    
    def test_long_message_handling(self, twilio_service):
        """Test handling of very long messages that exceed WhatsApp limits."""
        # Create a very long analysis result
        long_reasons = [
            "This is a very long reason that exceeds the normal length of a reason. " * 10,
            "This is another very long reason with lots of details and explanations. " * 10,
            "This is the third very long reason that contains many words and characters. " * 10
        ]
        
        long_analysis = JobAnalysisResult(
            trust_score=50,
            classification=JobClassification.SUSPICIOUS,
            reasons=long_reasons,
            confidence=0.8
        )
        
        # Format the message
        message = twilio_service._format_analysis_message(long_analysis)
        
        # Verify the message is within WhatsApp limits
        assert len(message) <= 1600, "Message exceeds WhatsApp character limit"
        
        # Check that the message still contains key information
        assert "*Trust Score:* 50/100" in message
        assert "*Classification:* Suspicious" in message
        assert "This is a very" in message  # Part of the first reason
    
    def test_special_character_handling(self, twilio_service):
        """Test handling of special characters in messages."""
        # Create an analysis result with special characters
        special_reasons = [
            "Company website uses unusual URL: http://suspicious-site.com/apply?id=123&ref=45",
            "Email contains special characters: apply+jobs@example.com (ñ,é,ç)",
            "Contact details include symbols: Call +1-800-JOBS-NOW (24/7) for info!"
        ]
        
        special_analysis = JobAnalysisResult(
            trust_score=60,
            classification=JobClassification.SUSPICIOUS,
            reasons=special_reasons,
            confidence=0.75
        )
        
        # Format the message
        message = twilio_service._format_analysis_message(special_analysis)
        
        # Verify special characters are handled correctly
        assert "http://suspicious-site.com/apply?id=123&ref=45" in message
        assert "apply+jobs@example.com" in message
        assert "+1-800-JOBS-NOW" in message
    
    def test_emoji_handling(self, twilio_service):
        """Test handling of emojis in messages."""
        # Create analysis results for different classifications
        legit = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.9
        )
        
        suspicious = JobAnalysisResult(
            trust_score=50,
            classification=JobClassification.SUSPICIOUS,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.8
        )
        
        scam = JobAnalysisResult(
            trust_score=15,
            classification=JobClassification.LIKELY_SCAM,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.95
        )
        
        # Format the messages
        legit_message = twilio_service._format_analysis_message(legit)
        suspicious_message = twilio_service._format_analysis_message(suspicious)
        scam_message = twilio_service._format_analysis_message(scam)
        
        # Verify emojis are included correctly
        assert "✅" in legit_message
        assert "⚠️" in suspicious_message
        assert "🚨" in scam_message


if __name__ == "__main__":
    pytest.main(["-v", __file__])