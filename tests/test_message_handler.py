"""
Unit tests for the MessageHandlerService.

Tests the complete message processing workflows for both text and media messages,
including input validation, error handling, and service orchestration.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from dataclasses import dataclass

from app.services.message_handler import MessageHandlerService
from app.models.data_models import TwilioWebhookRequest, JobAnalysisResult, JobClassification, AppConfig
from app.services.pdf_processing import PDFProcessingError, PDFDownloadError, PDFExtractionError


@pytest.fixture
def mock_config():
    """Create a mock AppConfig for testing."""
    return AppConfig(
        openai_api_key="test-openai-key",
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO"
    )


@pytest.fixture
def sample_analysis_result():
    """Create a sample JobAnalysisResult for testing."""
    return JobAnalysisResult(
        trust_score=75,
        classification=JobClassification.SUSPICIOUS,
        reasons=[
            "Salary seems too high for entry level position",
            "Company contact information is limited",
            "Job requirements are vague"
        ],
        confidence=0.8
    )


@pytest.fixture
def text_webhook_request():
    """Create a sample text message webhook request."""
    return TwilioWebhookRequest(
        MessageSid="test-message-sid",
        From="whatsapp:+1987654321",
        To="whatsapp:+1234567890",
        Body="Software Engineer position at TechCorp. $150k salary, work from home, no experience required. Contact us immediately!",
        NumMedia=0
    )


@pytest.fixture
def pdf_webhook_request():
    """Create a sample PDF media webhook request."""
    return TwilioWebhookRequest(
        MessageSid="test-message-sid",
        From="whatsapp:+1987654321",
        To="whatsapp:+1234567890",
        Body="",
        NumMedia=1,
        MediaUrl0="https://api.twilio.com/media/test.pdf",
        MediaContentType0="application/pdf"
    )


class TestMessageHandlerService:
    """Test cases for MessageHandlerService."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_config):
        """Set up mocks for each test."""
        with patch('app.services.message_handler.PDFProcessingService') as mock_pdf_service, \
             patch('app.services.message_handler.OpenAIAnalysisService') as mock_openai_service, \
             patch('app.services.message_handler.TwilioResponseService') as mock_twilio_service:
            
            self.mock_pdf_service = mock_pdf_service.return_value
            self.mock_openai_service = mock_openai_service.return_value
            self.mock_twilio_service = mock_twilio_service.return_value
            
            self.handler = MessageHandlerService(mock_config)
            yield
    
    @pytest.mark.asyncio
    async def test_process_message_text_success(self, text_webhook_request, sample_analysis_result):
        """Test successful processing of text message."""
        # Setup mocks
        self.mock_openai_service.analyze_job_ad = AsyncMock(return_value=sample_analysis_result)
        self.mock_twilio_service.send_analysis_result = Mock(return_value=True)
        
        # Execute
        result = await self.handler.process_message(text_webhook_request)
        
        # Verify
        assert result is True
        self.mock_openai_service.analyze_job_ad.assert_called_once_with(text_webhook_request.Body)
        self.mock_twilio_service.send_analysis_result.assert_called_once_with(
            text_webhook_request.From, sample_analysis_result
        )
    
    @pytest.mark.asyncio
    async def test_process_message_pdf_success(self, pdf_webhook_request, sample_analysis_result):
        """Test successful processing of PDF message."""
        extracted_text = "Software Engineer job at TechCorp..."
        
        # Setup mocks
        self.mock_pdf_service.process_pdf_url = AsyncMock(return_value=extracted_text)
        self.mock_openai_service.analyze_job_ad = AsyncMock(return_value=sample_analysis_result)
        self.mock_twilio_service.send_analysis_result = Mock(return_value=True)
        
        # Execute
        result = await self.handler.process_message(pdf_webhook_request)
        
        # Verify
        assert result is True
        self.mock_pdf_service.process_pdf_url.assert_called_once_with(pdf_webhook_request.MediaUrl0)
        self.mock_openai_service.analyze_job_ad.assert_called_once_with(extracted_text)
        self.mock_twilio_service.send_analysis_result.assert_called_once_with(
            pdf_webhook_request.From, sample_analysis_result
        )
    
    @pytest.mark.asyncio
    async def test_handle_text_message_success(self, sample_analysis_result):
        """Test successful text message handling."""
        text = "Software Engineer position at Google. $120k salary, full benefits, 3+ years experience required."
        from_number = "whatsapp:+1987654321"
        
        # Setup mocks
        self.mock_openai_service.analyze_job_ad = AsyncMock(return_value=sample_analysis_result)
        self.mock_twilio_service.send_analysis_result = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_text_message(text, from_number)
        
        # Verify
        assert result is True
        self.mock_openai_service.analyze_job_ad.assert_called_once_with(text)
        self.mock_twilio_service.send_analysis_result.assert_called_once_with(from_number, sample_analysis_result)
    
    @pytest.mark.asyncio
    async def test_handle_text_message_too_short(self):
        """Test handling of text message that's too short."""
        text = "job"
        from_number = "whatsapp:+1987654321"
        
        # Mock the client and messages creation
        mock_message = Mock()
        mock_message.sid = "test-sid"
        self.mock_twilio_service.client = Mock()
        self.mock_twilio_service.client.messages.create = Mock(return_value=mock_message)
        
        # Execute
        result = await self.handler.handle_text_message(text, from_number)
        
        # Verify
        assert result is True
        self.mock_openai_service.analyze_job_ad.assert_not_called()
        self.mock_twilio_service.client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_text_message_help_request(self):
        """Test handling of help request."""
        text = "help"
        from_number = "whatsapp:+1987654321"
        
        # Setup mocks
        self.mock_twilio_service.send_welcome_message = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_text_message(text, from_number)
        
        # Verify
        assert result is True
        self.mock_twilio_service.send_welcome_message.assert_called_once_with(from_number)
        self.mock_openai_service.analyze_job_ad.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_text_message_openai_error(self):
        """Test handling of OpenAI analysis error."""
        text = "Software Engineer position at TechCorp. Great opportunity!"
        from_number = "whatsapp:+1987654321"
        
        # Setup mocks
        self.mock_openai_service.analyze_job_ad = AsyncMock(side_effect=Exception("OpenAI API error"))
        self.mock_twilio_service.send_error_message = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_text_message(text, from_number)
        
        # Verify
        assert result is True
        self.mock_twilio_service.send_error_message.assert_called_once_with(from_number, "analysis")
    
    @pytest.mark.asyncio
    async def test_handle_media_message_success(self, sample_analysis_result):
        """Test successful media message handling."""
        media_url = "https://api.twilio.com/media/test.pdf"
        media_content_type = "application/pdf"
        from_number = "whatsapp:+1987654321"
        extracted_text = "Software Engineer job posting..."
        
        # Setup mocks
        self.mock_pdf_service.process_pdf_url = AsyncMock(return_value=extracted_text)
        self.mock_openai_service.analyze_job_ad = AsyncMock(return_value=sample_analysis_result)
        self.mock_twilio_service.send_analysis_result = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_media_message(media_url, media_content_type, from_number)
        
        # Verify
        assert result is True
        self.mock_pdf_service.process_pdf_url.assert_called_once_with(media_url)
        self.mock_openai_service.analyze_job_ad.assert_called_once_with(extracted_text)
        self.mock_twilio_service.send_analysis_result.assert_called_once_with(from_number, sample_analysis_result)
    
    @pytest.mark.asyncio
    async def test_handle_media_message_unsupported_type(self):
        """Test handling of unsupported media type."""
        media_url = "https://api.twilio.com/media/test.jpg"
        media_content_type = "image/jpeg"
        from_number = "whatsapp:+1987654321"
        
        # Mock the client and messages creation
        mock_message = Mock()
        mock_message.sid = "test-sid"
        self.mock_twilio_service.client = Mock()
        self.mock_twilio_service.client.messages.create = Mock(return_value=mock_message)
        
        # Execute
        result = await self.handler.handle_media_message(media_url, media_content_type, from_number)
        
        # Verify
        assert result is True
        self.mock_pdf_service.process_pdf_url.assert_not_called()
        self.mock_twilio_service.client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_media_message_pdf_processing_error(self):
        """Test handling of PDF processing error."""
        media_url = "https://api.twilio.com/media/test.pdf"
        media_content_type = "application/pdf"
        from_number = "whatsapp:+1987654321"
        
        # Setup mocks
        self.mock_pdf_service.process_pdf_url = AsyncMock(side_effect=PDFProcessingError("PDF processing failed"))
        self.mock_twilio_service.send_error_message = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_media_message(media_url, media_content_type, from_number)
        
        # Verify
        assert result is True
        self.mock_twilio_service.send_error_message.assert_called_once_with(from_number, "pdf_processing")
    
    @pytest.mark.asyncio
    async def test_handle_media_message_openai_error(self, sample_analysis_result):
        """Test handling of OpenAI error during media processing."""
        media_url = "https://api.twilio.com/media/test.pdf"
        media_content_type = "application/pdf"
        from_number = "whatsapp:+1987654321"
        extracted_text = "Software Engineer job posting..."
        
        # Setup mocks
        self.mock_pdf_service.process_pdf_url = AsyncMock(return_value=extracted_text)
        self.mock_openai_service.analyze_job_ad = AsyncMock(side_effect=Exception("OpenAI API error"))
        self.mock_twilio_service.send_error_message = Mock(return_value=True)
        
        # Execute
        result = await self.handler.handle_media_message(media_url, media_content_type, from_number)
        
        # Verify
        assert result is True
        self.mock_twilio_service.send_error_message.assert_called_once_with(from_number, "analysis")
    
    def test_validate_text_content_valid(self):
        """Test text content validation with valid content."""
        valid_text = "Software Engineer position at Google. Looking for experienced developer with Python skills."
        assert self.handler._validate_text_content(valid_text) is True
    
    def test_validate_text_content_empty(self):
        """Test text content validation with empty content."""
        assert self.handler._validate_text_content("") is False
        assert self.handler._validate_text_content("   ") is False
        assert self.handler._validate_text_content(None) is False
    
    def test_validate_text_content_too_short(self):
        """Test text content validation with content that's too short."""
        short_text = "job"
        assert self.handler._validate_text_content(short_text) is False
    
    def test_validate_text_content_too_long(self):
        """Test text content validation with content that's too long."""
        long_text = "x" * 10001  # Exceeds 10k character limit
        assert self.handler._validate_text_content(long_text) is False
    
    def test_validate_media_type_valid_pdf(self):
        """Test media type validation with valid PDF types."""
        valid_types = [
            "application/pdf",
            "application/x-pdf",
            "application/PDF",
            "APPLICATION/PDF"
        ]
        
        for media_type in valid_types:
            assert self.handler._validate_media_type(media_type) is True
    
    def test_validate_media_type_invalid(self):
        """Test media type validation with invalid types."""
        invalid_types = [
            "image/jpeg",
            "image/png",
            "text/plain",
            "application/json",
            None,
            ""
        ]
        
        for media_type in invalid_types:
            assert self.handler._validate_media_type(media_type) is False
    
    def test_is_help_request_exact_matches(self):
        """Test help request detection with exact keyword matches."""
        help_keywords = ["help", "start", "hello", "hi", "how", "what", "info", "about"]
        
        for keyword in help_keywords:
            assert self.handler._is_help_request(keyword) is True
            assert self.handler._is_help_request(keyword.upper()) is True
            assert self.handler._is_help_request(f"  {keyword}  ") is True
    
    def test_is_help_request_short_messages(self):
        """Test help request detection in short messages."""
        help_messages = [
            "how does this work",
            "what is this",
            "hello there",
            "hi bot"
        ]
        
        for message in help_messages:
            assert self.handler._is_help_request(message) is True
    
    def test_is_help_request_long_messages(self):
        """Test that long messages are not considered help requests."""
        long_message = "This is a long job posting about a software engineer position that includes many details about the role and requirements."
        assert self.handler._is_help_request(long_message) is False
    
    def test_is_help_request_job_content(self):
        """Test that actual job content is not considered a help request."""
        job_content = "Software Engineer position at TechCorp"
        assert self.handler._is_help_request(job_content) is False


class TestMessageHandlerServiceIntegration:
    """Integration tests for MessageHandlerService with real service interactions."""
    
    @pytest.mark.asyncio
    async def test_complete_text_workflow_integration(self, mock_config):
        """Test complete text message workflow with mocked external services."""
        # Create handler with real service instances but mocked external calls
        handler = MessageHandlerService(mock_config)
        
        # Mock external service calls
        with patch.object(handler.openai_service, 'analyze_job_ad') as mock_analyze, \
             patch.object(handler.twilio_service, 'send_analysis_result') as mock_send:
            
            # Setup mock responses
            analysis_result = JobAnalysisResult(
                trust_score=85,
                classification=JobClassification.LEGIT,
                reasons=["Legitimate company", "Realistic salary", "Detailed requirements"],
                confidence=0.9
            )
            mock_analyze.return_value = analysis_result
            mock_send.return_value = True
            
            # Create webhook request
            webhook_request = TwilioWebhookRequest(
                MessageSid="test-sid",
                From="whatsapp:+1987654321",
                To="whatsapp:+1234567890",
                Body="Software Engineer at Google. $120k salary, 3+ years experience required.",
                NumMedia=0
            )
            
            # Execute
            result = await handler.process_message(webhook_request)
            
            # Verify
            assert result is True
            mock_analyze.assert_called_once()
            mock_send.assert_called_once_with("whatsapp:+1987654321", analysis_result)
    
    @pytest.mark.asyncio
    async def test_complete_pdf_workflow_integration(self, mock_config):
        """Test complete PDF message workflow with mocked external services."""
        # Create handler with real service instances but mocked external calls
        handler = MessageHandlerService(mock_config)
        
        # Mock external service calls
        with patch.object(handler.pdf_service, 'process_pdf_url') as mock_pdf, \
             patch.object(handler.openai_service, 'analyze_job_ad') as mock_analyze, \
             patch.object(handler.twilio_service, 'send_analysis_result') as mock_send:
            
            # Setup mock responses
            extracted_text = "Software Engineer position at TechCorp..."
            analysis_result = JobAnalysisResult(
                trust_score=45,
                classification=JobClassification.SUSPICIOUS,
                reasons=["Vague job description", "No company details", "Unrealistic promises"],
                confidence=0.7
            )
            mock_pdf.return_value = extracted_text
            mock_analyze.return_value = analysis_result
            mock_send.return_value = True
            
            # Create webhook request
            webhook_request = TwilioWebhookRequest(
                MessageSid="test-sid",
                From="whatsapp:+1987654321",
                To="whatsapp:+1234567890",
                Body="",
                NumMedia=1,
                MediaUrl0="https://api.twilio.com/media/test.pdf",
                MediaContentType0="application/pdf"
            )
            
            # Execute
            result = await handler.process_message(webhook_request)
            
            # Verify
            assert result is True
            mock_pdf.assert_called_once_with("https://api.twilio.com/media/test.pdf")
            mock_analyze.assert_called_once_with(extracted_text)
            mock_send.assert_called_once_with("whatsapp:+1987654321", analysis_result)