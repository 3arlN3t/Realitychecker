"""
End-to-end tests for complete user workflows.

These tests simulate complete user interactions with the WhatsApp bot,
from receiving a message to sending the analysis response.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.data_models import JobAnalysisResult, JobClassification
from tests.fixtures.job_ad_samples import JobAdFixtures, WebhookDataFixtures, TestPhoneNumbers
from tests.fixtures.pdf_samples import PDFFixtures, MockPDFResponses, PDFExtractionMocks


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


@pytest.mark.e2e
class TestCompleteUserWorkflows:
    """End-to-end tests for complete user workflows."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    @patch('app.services.message_handler.MessageHandlerService.process_message')
    def test_first_time_user_workflow(self, mock_process_message, mock_twilio_service_class, 
                                     mock_openai_service_class, mock_get_config, client, mock_config):
        """Test workflow for a first-time user sending a job ad."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup message handler mock
        mock_process_message.return_value = "Success"
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_welcome_message.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate first-time user sending "hello" message
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM1234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body="hello"
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify welcome message was sent
        mock_twilio_service.send_welcome_message.assert_called_once_with(
            TestPhoneNumbers.LEGITIMATE_USER
        )
        
        # Now simulate the same user sending a job ad
        job_sample = JobAdFixtures.LEGITIMATE_JOBS[0]
        
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
        mock_twilio_service.send_analysis_result.return_value = True
        
        # Simulate job ad message
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM2234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=job_sample.content
        )
        
        # Reset mocks
        mock_process_message.reset_mock()
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify message was processed
        mock_process_message.assert_called_once()
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_pdf_upload_workflow(self, mock_twilio_service_class, mock_openai_service_class, 
                               mock_pdf_service_class, mock_get_config, client, mock_config):
        """Test workflow for a user uploading a PDF job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup PDF service mock
        mock_pdf_service = AsyncMock()
        pdf_sample = PDFFixtures.VALID_PDF_SAMPLES[0]
        mock_pdf_service.process_pdf_url.return_value = pdf_sample.extracted_text
        mock_pdf_service_class.return_value = mock_pdf_service
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        pdf_analysis = JobAnalysisResult(
            trust_score=80,
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
        webhook_data = WebhookDataFixtures.create_media_webhook_data(
            message_sid="SM3234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            media_url=pdf_sample.url
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify PDF processing was called
        mock_pdf_service.process_pdf_url.assert_called_once_with(pdf_sample.url)
        
        # Verify analysis was called with extracted text
        mock_openai_service.analyze_job_ad.assert_called_once_with(pdf_sample.extracted_text)
        
        # Verify response was sent
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            TestPhoneNumbers.LEGITIMATE_USER, pdf_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_suspicious_job_workflow(self, mock_twilio_service_class, mock_openai_service_class, 
                                   mock_get_config, client, mock_config):
        """Test workflow for a user sending a suspicious job posting."""
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
        job_sample = JobAdFixtures.SUSPICIOUS_JOBS[0]
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM4234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.SUSPICIOUS_USER,
            body=job_sample.content
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify analysis and response
        mock_openai_service.analyze_job_ad.assert_called_once_with(job_sample.content)
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            TestPhoneNumbers.SUSPICIOUS_USER, suspicious_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_scam_job_workflow(self, mock_twilio_service_class, mock_openai_service_class, 
                             mock_get_config, client, mock_config):
        """Test workflow for a user sending a scam job posting."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        scam_analysis = JobAnalysisResult(
            trust_score=10,
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
        job_sample = JobAdFixtures.SCAM_JOBS[0]
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM5234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.SCAM_VICTIM,
            body=job_sample.content
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify analysis and response
        mock_openai_service.analyze_job_ad.assert_called_once_with(job_sample.content)
        mock_twilio_service.send_analysis_result.assert_called_once_with(
            TestPhoneNumbers.SCAM_VICTIM, scam_analysis
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_corrupted_pdf_workflow(self, mock_twilio_service_class, mock_pdf_service_class, 
                                  mock_get_config, client, mock_config):
        """Test workflow for a user uploading a corrupted PDF."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup PDF service mock
        mock_pdf_service = AsyncMock()
        mock_pdf_service.process_pdf_url.side_effect = Exception("PDF processing failed")
        mock_pdf_service_class.return_value = mock_pdf_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_error_message.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate corrupted PDF webhook
        pdf_sample = PDFFixtures.INVALID_PDF_SAMPLES[0]  # Corrupted file
        webhook_data = WebhookDataFixtures.create_media_webhook_data(
            message_sid="SM6234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            media_url=pdf_sample.url
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify PDF processing was called
        mock_pdf_service.process_pdf_url.assert_called_once_with(pdf_sample.url)
        
        # Verify error message was sent
        mock_twilio_service.send_error_message.assert_called_once()
        call_args = mock_twilio_service.send_error_message.call_args
        assert call_args[0][0] == TestPhoneNumbers.LEGITIMATE_USER
        assert call_args[0][1] == "pdf_processing"
"""    
@patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_openai_error_workflow(self, mock_twilio_service_class, mock_openai_service_class, 
                                 mock_get_config, client, mock_config):
        """Test workflow when OpenAI API fails."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock to fail
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.side_effect = Exception("OpenAI API error")
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_error_message.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate job posting webhook
        job_sample = JobAdFixtures.LEGITIMATE_JOBS[0]
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM7234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=job_sample.content
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify OpenAI service was called
        mock_openai_service.analyze_job_ad.assert_called_once_with(job_sample.content)
        
        # Verify error message was sent
        mock_twilio_service.send_error_message.assert_called_once()
        call_args = mock_twilio_service.send_error_message.call_args
        assert call_args[0][0] == TestPhoneNumbers.LEGITIMATE_USER
        assert call_args[0][1] == "analysis"
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_help_request_workflow(self, mock_twilio_service_class, mock_get_config, client, mock_config):
        """Test workflow for a user requesting help."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_welcome_message.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate help request webhook
        webhook_data = WebhookDataFixtures.create_help_webhook_data(
            message_sid="SM8234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.HELP_SEEKER
        )
        
        # Send webhook request
        response = client.post("/webhook/whatsapp", data=webhook_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify welcome message was sent
        mock_twilio_service.send_welcome_message.assert_called_once_with(
            TestPhoneNumbers.HELP_SEEKER
        )
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_multiple_requests_workflow(self, mock_twilio_service_class, mock_openai_service_class, 
                                      mock_get_config, client, mock_config):
        """Test workflow for a user sending multiple job ads in sequence."""
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
        
        # Simulate first job ad
        job_sample1 = JobAdFixtures.LEGITIMATE_JOBS[0]
        webhook_data1 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM9234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.REPEAT_USER,
            body=job_sample1.content
        )
        
        # Send first webhook request
        response1 = client.post("/webhook/whatsapp", data=webhook_data1)
        assert response1.status_code == 200
        
        # Verify first analysis and response
        assert mock_openai_service.analyze_job_ad.call_count == 1
        assert mock_twilio_service.send_analysis_result.call_count == 1
        
        # Simulate second job ad
        job_sample2 = JobAdFixtures.SCAM_JOBS[0]
        webhook_data2 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM0234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.REPEAT_USER,
            body=job_sample2.content
        )
        
        # Send second webhook request
        response2 = client.post("/webhook/whatsapp", data=webhook_data2)
        assert response2.status_code == 200
        
        # Verify second analysis and response
        assert mock_openai_service.analyze_job_ad.call_count == 2
        assert mock_twilio_service.send_analysis_result.call_count == 2
        
        # Verify correct analyses were sent
        call_args_list = mock_twilio_service.send_analysis_result.call_args_list
        assert call_args_list[0][0][1] == analysis_results[0]  # First call with legitimate result
        assert call_args_list[1][0][1] == analysis_results[1]  # Second call with scam result


@pytest.mark.e2e
class TestErrorRecoveryWorkflows:
    """Tests for error recovery workflows."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_recovery_after_pdf_error(self, mock_twilio_service_class, mock_openai_service_class, 
                                    mock_pdf_service_class, mock_get_config, client, mock_config):
        """Test workflow recovery after a PDF processing error."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup PDF service mock to fail first, then succeed
        mock_pdf_service = AsyncMock()
        mock_pdf_service.process_pdf_url.side_effect = [
            Exception("PDF processing failed"),  # First call fails
            PDFFixtures.VALID_PDF_SAMPLES[0].extracted_text  # Second call succeeds
        ]
        mock_pdf_service_class.return_value = mock_pdf_service
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        pdf_analysis = JobAnalysisResult(
            trust_score=80,
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
        mock_twilio_service.send_error_message.return_value = True
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate first PDF upload (will fail)
        pdf_sample = PDFFixtures.INVALID_PDF_SAMPLES[0]
        webhook_data1 = WebhookDataFixtures.create_media_webhook_data(
            message_sid="SM1234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            media_url=pdf_sample.url
        )
        
        # Send first webhook request
        response1 = client.post("/webhook/whatsapp", data=webhook_data1)
        assert response1.status_code == 200
        
        # Verify error message was sent
        assert mock_twilio_service.send_error_message.call_count == 1
        
        # Simulate second PDF upload (will succeed)
        pdf_sample2 = PDFFixtures.VALID_PDF_SAMPLES[0]
        webhook_data2 = WebhookDataFixtures.create_media_webhook_data(
            message_sid="SM2234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            media_url=pdf_sample2.url
        )
        
        # Send second webhook request
        response2 = client.post("/webhook/whatsapp", data=webhook_data2)
        assert response2.status_code == 200
        
        # Verify analysis was called and response was sent
        mock_openai_service.analyze_job_ad.assert_called_once_with(pdf_sample2.extracted_text)
        assert mock_twilio_service.send_analysis_result.call_count == 1
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_recovery_after_openai_error(self, mock_twilio_service_class, mock_openai_service_class, 
                                       mock_get_config, client, mock_config):
        """Test workflow recovery after an OpenAI API error."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock to fail first, then succeed
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.side_effect = [
            Exception("OpenAI API error"),  # First call fails
            JobAnalysisResult(  # Second call succeeds
                trust_score=85,
                classification=JobClassification.LEGIT,
                reasons=["Legitimate company", "Realistic salary", "Detailed requirements"],
                confidence=0.9
            )
        ]
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_error_message.return_value = True
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Simulate first job ad (will fail analysis)
        job_sample = JobAdFixtures.LEGITIMATE_JOBS[0]
        webhook_data1 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM3234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=job_sample.content
        )
        
        # Send first webhook request
        response1 = client.post("/webhook/whatsapp", data=webhook_data1)
        assert response1.status_code == 200
        
        # Verify error message was sent
        assert mock_twilio_service.send_error_message.call_count == 1
        
        # Simulate second job ad (same content, will succeed)
        webhook_data2 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM4234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=job_sample.content
        )
        
        # Send second webhook request
        response2 = client.post("/webhook/whatsapp", data=webhook_data2)
        assert response2.status_code == 200
        
        # Verify analysis was called twice and success response was sent
        assert mock_openai_service.analyze_job_ad.call_count == 2
        assert mock_twilio_service.send_analysis_result.call_count == 1


@pytest.mark.e2e
class TestConcurrentRequestsWorkflow:
    """Tests for handling concurrent requests."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_concurrent_requests_from_different_users(self, mock_twilio_service_class, 
                                                   mock_openai_service_class, mock_get_config, 
                                                   client, mock_config):
        """Test handling concurrent requests from different users."""
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
            ),
            JobAnalysisResult(
                trust_score=60,
                classification=JobClassification.SUSPICIOUS,
                reasons=["Vague job description", "Limited company details", "Unusual application process"],
                confidence=0.75
            )
        ]
        mock_openai_service.analyze_job_ad.side_effect = analysis_results
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Create webhook data for different users
        webhook_data1 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM7234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=JobAdFixtures.LEGITIMATE_JOBS[0].content
        )
        
        webhook_data2 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM8234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.SCAM_VICTIM,
            body=JobAdFixtures.SCAM_JOBS[0].content
        )
        
        webhook_data3 = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM9234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.SUSPICIOUS_USER,
            body=JobAdFixtures.SUSPICIOUS_JOBS[0].content
        )
        
        # Send concurrent webhook requests
        # Note: In a real test, we would use asyncio.gather or threading to make truly concurrent requests
        # For this test, we'll simulate by sending them sequentially but checking that all were processed
        response1 = client.post("/webhook/whatsapp", data=webhook_data1)
        response2 = client.post("/webhook/whatsapp", data=webhook_data2)
        response3 = client.post("/webhook/whatsapp", data=webhook_data3)
        
        # Verify all responses were successful
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # Verify all analyses were called
        assert mock_openai_service.analyze_job_ad.call_count == 3
        
        # Verify all responses were sent
        assert mock_twilio_service.send_analysis_result.call_count == 3
        
        # Verify correct responses were sent to correct users
        call_args_list = mock_twilio_service.send_analysis_result.call_args_list
        assert TestPhoneNumbers.LEGITIMATE_USER in str(call_args_list[0])
        assert TestPhoneNumbers.SCAM_VICTIM in str(call_args_list[1])
        assert TestPhoneNumbers.SUSPICIOUS_USER in str(call_args_list[2])


if __name__ == "__main__":
    pytest.main(["-v", __file__])