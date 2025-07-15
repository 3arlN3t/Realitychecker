"""
End-to-end tests simulating complete WhatsApp interactions.

These tests simulate the complete flow from receiving a WhatsApp message
through Twilio webhook to sending the analysis response back to the user.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.data_models import JobAnalysisResult, JobClassification


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Mock application configuration for E2E tests."""
    config = Mock()
    config.webhook_validation = False  # Disable for easier testing
    config.twilio_auth_token = "test_auth_token"
    config.twilio_phone_number = "+1234567890"
    config.twilio_account_sid = "test_account_sid"
    config.openai_api_key = "test_openai_key"
    config.max_pdf_size_mb = 10
    config.openai_model = "gpt-4"
    config.log_level = "INFO"
    return config


class TestEndToEndWhatsAppFlow:
    """End-to-end tests for complete WhatsApp message processing flows."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_legitimate_job_complete_flow(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config):
        """Test complete flow for legitimate job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        legitimate_analysis = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=[
                "Company has verifiable online presence and contact information",
                "Job description is detailed and matches industry standards", 
                "Salary range is realistic for the position and location"
            ],
            confidence=0.9
        )
        mock_openai_service.analyze_job_ad.return_value = legitimate_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate legitimate job posting webhook
        webhook_data = {
            "MessageSid": "SM1234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience, Bachelor's degree in Computer Science. Contact: hr@google.com for application details.",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify OpenAI analysis was called
        mock_openai_service.analyze_job_ad.assert_called_once()
        call_args = mock_openai_service.analyze_job_ad.call_args[0][0]
        assert "Software Engineer position at Google" in call_args
        
        # Verify Twilio response was sent
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            "whatsapp:+1987654321", legitimate_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_suspicious_job_complete_flow(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config):
        """Test complete flow for suspicious job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        suspicious_analysis = JobAnalysisResult(
            trust_score=45,
            classification=JobClassification.SUSPICIOUS,
            reasons=[
                "Unrealistic income promises without clear job duties",
                "Requests upfront payment for training materials",
                "Uses unprofessional email address"
            ],
            confidence=0.8
        )
        mock_openai_service.analyze_job_ad.return_value = suspicious_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate suspicious job posting webhook
        webhook_data = {
            "MessageSid": "SM2234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "URGENT! Make $5000/week working from home! No experience needed! Just send $99 registration fee to get started immediately! Contact WhatsApp: +1234567890",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify analysis and response
        mock_openai_service.analyze_job_ad.assert_called_once()
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            "whatsapp:+1987654321", suspicious_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_scam_job_complete_flow(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config):
        """Test complete flow for scam job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        scam_analysis = JobAnalysisResult(
            trust_score=5,
            classification=JobClassification.LIKELY_SCAM,
            reasons=[
                "Demands immediate upfront payment",
                "Uses high-pressure tactics and urgency",
                "Requests wire transfer to untraceable account"
            ],
            confidence=0.95
        )
        mock_openai_service.analyze_job_ad.return_value = scam_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate scam job posting webhook
        webhook_data = {
            "MessageSid": "SM3234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Congratulations! You've been selected for a $10,000/month data entry job! Send your SSN, bank details, and $200 processing fee to secure your position today!",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify analysis and response
        mock_openai_service.analyze_job_ad.assert_called_once()
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            "whatsapp:+1987654321", scam_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_pdf_job_complete_flow(self, mock_twilio_service_class, mock_openai_service_class, mock_pdf_service_class, mock_get_config, client, mock_config):
        """Test complete flow for PDF job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup PDF service mock
        mock_pdf_service = AsyncMock()
        extracted_text = "Software Engineer position at TechCorp. We are looking for a skilled developer to join our team. Salary: $100,000-$130,000. Requirements: 5+ years experience, Python, JavaScript. Contact: jobs@techcorp.com"
        mock_pdf_service.process_pdf_url.return_value = extracted_text
        mock_pdf_service_class.return_value = mock_pdf_service
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        pdf_analysis = JobAnalysisResult(
            trust_score=75,
            classification=JobClassification.LEGIT,
            reasons=[
                "Professional job description with clear requirements",
                "Realistic salary range for the position",
                "Company contact information provided"
            ],
            confidence=0.85
        )
        mock_openai_service.analyze_job_ad.return_value = pdf_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate PDF job posting webhook
        webhook_data = {
            "MessageSid": "SM4234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/media/test-job-posting.pdf",
            "MediaContentType0": "application/pdf"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify PDF processing was called
        mock_pdf_service.process_pdf_url.assert_called_once_with("https://api.twilio.com/media/test-job-posting.pdf")
        
        # Verify analysis was called with extracted text
        mock_openai_service.analyze_job_ad.assert_called_once_with(extracted_text)
        
        # Verify response was sent
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            "whatsapp:+1987654321", pdf_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_help_request_complete_flow(self, mock_twilio_service_class, mock_get_config, client, mock_config):
        """Test complete flow for help request."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_welcome_message.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate help request webhook
        webhook_data = {
            "MessageSid": "SM5234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "help",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify welcome message was sent
        mock_twilio_service.send_welcome_message.assert_called_once_with("whatsapp:+1987654321")
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_invalid_message_complete_flow(self, mock_twilio_service_class, mock_get_config, client, mock_config):
        """Test complete flow for invalid/too short message."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_message = Mock()
        mock_message.sid = "test-sid"
        mock_twilio_service.client = Mock()
        mock_twilio_service.client.messages.create.return_value = mock_message
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate invalid message webhook
        webhook_data = {
            "MessageSid": "SM6234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "hi",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify error message was sent
        mock_twilio_service.client.messages.create.assert_called_once()


class TestEndToEndErrorScenarios:
    """End-to-end tests for error scenarios."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_openai_service_failure_flow(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config):
        """Test complete flow when OpenAI service fails."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock to fail
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.side_effect = Exception("OpenAI API error")
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_message = Mock()
        mock_message.sid = "test-sid"
        mock_twilio_service.client = Mock()
        mock_twilio_service.client.messages.create.return_value = mock_message
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate job posting webhook
        webhook_data = {
            "MessageSid": "SM7234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Software Engineer position at TechCorp. Great opportunity!",
            "NumMedia": "0"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response (should still be 200 for Twilio)
        assert response.status_code == 200
        
        # Verify error message was sent
        mock_twilio_service.client.messages.create.assert_called_once()
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_pdf_processing_failure_flow(self, mock_twilio_service_class, mock_pdf_service_class, mock_get_config, client, mock_config):
        """Test complete flow when PDF processing fails."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup PDF service mock to fail
        mock_pdf_service = AsyncMock()
        mock_pdf_service.process_pdf_url.side_effect = Exception("PDF processing failed")
        mock_pdf_service_class.return_value = mock_pdf_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_message = Mock()
        mock_message.sid = "test-sid"
        mock_twilio_service.client = Mock()
        mock_twilio_service.client.messages.create.return_value = mock_message
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate PDF webhook
        webhook_data = {
            "MessageSid": "SM8234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/media/corrupted.pdf",
            "MediaContentType0": "application/pdf"
        }
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify error message was sent
        mock_twilio_service.client.messages.create.assert_called_once()


class TestEndToEndMultipleMessages:
    """Test handling multiple messages in sequence."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_multiple_messages_from_same_user(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config):
        """Test handling multiple messages from the same user."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        analysis_results = [
            JobAnalysisResult(
                trust_score=85,
                classification=JobClassification.LEGIT,
                reasons=["Legitimate company", "Realistic salary", "Detailed requirements"],
                confidence=0.9
            ),
            JobAnalysisResult(
                trust_score=25,
                classification=JobClassification.LIKELY_SCAM,
                reasons=["Requests upfront payment", "Unrealistic promises", "Poor grammar"],
                confidence=0.85
            )
        ]
        mock_openai_service.analyze_job_ad.side_effect = analysis_results
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # First message - legitimate job
        webhook_data_1 = {
            "MessageSid": "SM9234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Software Engineer at Google. $120k salary, 3+ years experience required.",
            "NumMedia": "0"
        }
        
        response_1 = client.post("/webhook/whatsapp", data=webhook_data_1)
        assert response_1.status_code == 200
        
        # Second message - scam job
        webhook_data_2 = {
            "MessageSid": "SM0234567890abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Make $10000 per week! Send $500 now for training materials!",
            "NumMedia": "0"
        }
        
        response_2 = client.post("/webhook/whatsapp", data=webhook_data_2)
        assert response_2.status_code == 200
        
        # Verify both analyses were called
        assert mock_openai_service.analyze_job_ad.call_count == 2
        
        # Verify both responses were sent
        assert mock_twilio_service.send_analysis_result.call_count == 2
        
        # Verify correct analyses were sent
        call_args_list = mock_twilio_service.send_analysis_result.call_args_list
        assert call_args_list[0][0][1] == analysis_results[0]  # First call with legitimate result
        assert call_args_list[1][0][1] == analysis_results[1]  # Second call with scam result


if __name__ == "__main__":
    pytest.main([__file__])