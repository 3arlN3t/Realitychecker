"""
Integration tests for external service interactions.

These tests verify the integration between our services and external APIs
like OpenAI and Twilio, using mocked responses that simulate real API behavior.
"""

import pytest
import json
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import openai
from twilio.base.exceptions import TwilioException

from app.services.openai_analysis import OpenAIAnalysisService
from app.services.twilio_response import TwilioResponseService
from app.services.pdf_processing import PDFProcessingService
from app.models.data_models import AppConfig, JobAnalysisResult, JobClassification


@pytest.fixture
def mock_config():
    """Create a mock configuration for integration tests."""
    return AppConfig(
        openai_api_key="test-openai-key",
        twilio_account_sid="test-twilio-sid",
        twilio_auth_token="test-twilio-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO"
    )


class TestOpenAIIntegration:
    """Integration tests for OpenAI service."""
    
    @pytest.mark.asyncio
    async def test_openai_successful_analysis_integration(self, mock_config):
        """Test successful OpenAI API integration with realistic response."""
        service = OpenAIAnalysisService(mock_config)
        
        # Mock OpenAI response that simulates real API behavior
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 85,
            "classification": "Legit",
            "reasons": [
                "Company has verifiable online presence and contact information",
                "Job description is detailed and matches industry standards",
                "Salary range is realistic for the position and location"
            ],
            "confidence": 0.9
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 150
        
        job_text = "Software Engineer position at Google Inc. We are seeking a talented developer..."
        
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response) as mock_create:
            result = await service.analyze_job_ad(job_text)
            
            # Verify API call was made with correct parameters
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            
            assert call_kwargs['model'] == 'gpt-4'
            assert call_kwargs['temperature'] == 0.3
            assert call_kwargs['max_tokens'] == 1000
            assert call_kwargs['timeout'] == 30.0
            assert len(call_kwargs['messages']) == 2
            assert call_kwargs['messages'][0]['role'] == 'system'
            assert call_kwargs['messages'][1]['role'] == 'user'
            assert job_text in call_kwargs['messages'][1]['content']
            
            # Verify result
            assert isinstance(result, JobAnalysisResult)
            assert result.trust_score == 85
            assert result.classification == JobClassification.LEGIT
            assert len(result.reasons) == 3
            assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_openai_rate_limit_handling_integration(self, mock_config):
        """Test OpenAI rate limit error handling."""
        service = OpenAIAnalysisService(mock_config)
        
        # Mock rate limit error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_body = {"error": {"message": "Rate limit exceeded"}}
        
        with patch.object(service.client.chat.completions, 'create', 
                         new_callable=AsyncMock, 
                         side_effect=openai.RateLimitError("Rate limit exceeded", response=mock_response, body=mock_body)):
            
            with pytest.raises(Exception, match="Service is temporarily busy"):
                await service.analyze_job_ad("Test job posting")
    
    @pytest.mark.asyncio
    async def test_openai_timeout_handling_integration(self, mock_config):
        """Test OpenAI timeout error handling."""
        service = OpenAIAnalysisService(mock_config)
        
        with patch.object(service.client.chat.completions, 'create',
                         new_callable=AsyncMock,
                         side_effect=openai.APITimeoutError("Request timed out")):
            
            with pytest.raises(Exception, match="Analysis service is currently unavailable"):
                await service.analyze_job_ad("Test job posting")
    
    @pytest.mark.asyncio
    async def test_openai_malformed_response_handling(self, mock_config):
        """Test handling of malformed OpenAI responses."""
        service = OpenAIAnalysisService(mock_config)
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "This is not valid JSON response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception, match="An error occurred while analyzing the job posting"):
                await service.analyze_job_ad("Test job posting")


class TestTwilioIntegration:
    """Integration tests for Twilio service."""
    
    def test_twilio_successful_message_send_integration(self, mock_config):
        """Test successful Twilio message sending integration."""
        service = TwilioResponseService(mock_config)
        
        # Mock successful Twilio response
        mock_message = Mock()
        mock_message.sid = "SM1234567890abcdef1234567890abcdef"
        mock_message.status = "queued"
        
        with patch.object(service.client.messages, 'create', return_value=mock_message) as mock_create:
            analysis_result = JobAnalysisResult(
                trust_score=75,
                classification=JobClassification.LEGIT,
                reasons=["Good company", "Realistic salary", "Clear requirements"],
                confidence=0.8
            )
            
            result = service.send_analysis_result("whatsapp:+1987654321", analysis_result)
            
            # Verify API call was made correctly
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            
            assert call_kwargs['from_'] == f"whatsapp:{mock_config.twilio_phone_number}"
            assert call_kwargs['to'] == "whatsapp:+1987654321"
            assert "75/100" in call_kwargs['body']
            assert "Legit" in call_kwargs['body']
            assert result is True
    
    def test_twilio_authentication_error_integration(self, mock_config):
        """Test Twilio authentication error handling."""
        service = TwilioResponseService(mock_config)
        
        # Mock Twilio authentication error
        with patch.object(service.client.messages, 'create', 
                         side_effect=TwilioException("Authentication failed")):
            
            analysis_result = JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.SUSPICIOUS,
                reasons=["Some concerns", "Needs verification", "Check details"],
                confidence=0.7
            )
            
            result = service.send_analysis_result("whatsapp:+1987654321", analysis_result)
            assert result is False
    
    def test_twilio_message_formatting_integration(self, mock_config):
        """Test Twilio message formatting for different classifications."""
        service = TwilioResponseService(mock_config)
        
        mock_message = Mock()
        mock_message.sid = "test-sid"
        
        test_cases = [
            (JobClassification.LEGIT, "✅ Legit"),
            (JobClassification.SUSPICIOUS, "⚠️ Suspicious"),
            (JobClassification.LIKELY_SCAM, "🚨 Likely Scam")
        ]
        
        for classification, expected_emoji in test_cases:
            with patch.object(service.client.messages, 'create', return_value=mock_message) as mock_create:
                analysis_result = JobAnalysisResult(
                    trust_score=50,
                    classification=classification,
                    reasons=["Reason 1", "Reason 2", "Reason 3"],
                    confidence=0.8
                )
                
                service.send_analysis_result("whatsapp:+1987654321", analysis_result)
                
                call_kwargs = mock_create.call_args.kwargs
                # Check for the classification text in the message body
                message_body = call_kwargs['body']
                if classification == JobClassification.LEGIT:
                    assert "Legit" in message_body
                elif classification == JobClassification.SUSPICIOUS:
                    assert "Suspicious" in message_body
                elif classification == JobClassification.LIKELY_SCAM:
                    assert "Likely Scam" in message_body


class TestPDFProcessingIntegration:
    """Integration tests for PDF processing service."""
    
    @pytest.mark.asyncio
    async def test_pdf_download_success_integration(self, mock_config):
        """Test successful PDF download integration."""
        service = PDFProcessingService(mock_config)
        
        # Mock successful HTTP response with PDF content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": "1024"}
        mock_response.content = b"%PDF-1.4 fake pdf content"
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response) as mock_get:
            result = await service.download_pdf("https://example.com/test.pdf")
            
            # Verify HTTP request was made correctly (check call was made)
            mock_get.assert_called_once()
            
            assert result == b"%PDF-1.4 fake pdf content"
    
    @pytest.mark.asyncio
    async def test_pdf_download_size_limit_integration(self, mock_config):
        """Test PDF download size limit enforcement."""
        service = PDFProcessingService(mock_config)
        
        # Mock response with oversized content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": str(15 * 1024 * 1024)}  # 15MB
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception, match="PDF file too large"):
                await service.download_pdf("https://example.com/large.pdf")
    
    @pytest.mark.asyncio
    async def test_pdf_download_network_error_integration(self, mock_config):
        """Test PDF download network error handling."""
        service = PDFProcessingService(mock_config)
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, side_effect=httpx.NetworkError("Connection failed")):
            with pytest.raises(Exception, match="Network error downloading PDF"):
                await service.download_pdf("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    async def test_pdf_text_extraction_integration(self, mock_config):
        """Test PDF text extraction integration."""
        service = PDFProcessingService(mock_config)
        
        # Mock PDF content that would be extracted
        fake_pdf_content = b"%PDF-1.4 fake pdf with text content"
        
        # Mock pdfplumber extraction
        mock_page = Mock()
        mock_page.extract_text.return_value = "Software Engineer position at TechCorp. Requirements: Python, 3+ years experience."
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            result = await service.extract_text(fake_pdf_content)
            
            assert result == "Software Engineer position at TechCorp. Requirements: Python, 3+ years experience."
    
    @pytest.mark.asyncio
    async def test_pdf_complete_processing_integration(self, mock_config):
        """Test complete PDF processing workflow integration."""
        service = PDFProcessingService(mock_config)
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": "2048"}
        mock_response.content = b"%PDF-1.4 fake pdf content"
        
        # Mock PDF extraction
        mock_page = Mock()
        mock_page.extract_text.return_value = "Data Analyst position at Analytics Corp. Salary: $80,000. Requirements: SQL, Python, statistics background."
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response), \
             patch('pdfplumber.open', return_value=mock_pdf):
            
            result = await service.process_pdf_url("https://example.com/job.pdf")
            
            assert result == "Data Analyst position at Analytics Corp. Salary: $80,000. Requirements: SQL, Python, statistics background."


class TestServiceIntegrationChain:
    """Integration tests for service interaction chains."""
    
    @pytest.mark.asyncio
    async def test_pdf_to_analysis_integration_chain(self, mock_config):
        """Test complete integration chain from PDF processing to OpenAI analysis."""
        pdf_service = PDFProcessingService(mock_config)
        openai_service = OpenAIAnalysisService(mock_config)
        
        # Mock PDF processing
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": "1024"}
        mock_response.content = b"%PDF-1.4 fake pdf content"
        
        mock_page = Mock()
        extracted_text = "Marketing Manager position at StartupCorp. Salary: $70,000-$90,000. Requirements: 2+ years marketing experience, social media expertise."
        mock_page.extract_text.return_value = extracted_text
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        # Mock OpenAI analysis
        mock_openai_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 80,
            "classification": "Legit",
            "reasons": [
                "Professional job description with clear requirements",
                "Realistic salary range for marketing position",
                "Company information appears legitimate"
            ],
            "confidence": 0.85
        })
        mock_choice.message = mock_message
        mock_openai_response.choices = [mock_choice]
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response), \
             patch('pdfplumber.open', return_value=mock_pdf), \
             patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_openai_response):
            
            # Process PDF
            pdf_text = await pdf_service.process_pdf_url("https://example.com/marketing-job.pdf")
            assert pdf_text == extracted_text
            
            # Analyze extracted text
            analysis_result = await openai_service.analyze_job_ad(pdf_text)
            
            assert analysis_result.trust_score == 80
            assert analysis_result.classification == JobClassification.LEGIT
            assert len(analysis_result.reasons) == 3
            assert analysis_result.confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_analysis_to_response_integration_chain(self, mock_config):
        """Test integration chain from OpenAI analysis to Twilio response."""
        openai_service = OpenAIAnalysisService(mock_config)
        twilio_service = TwilioResponseService(mock_config)
        
        # Mock OpenAI analysis
        mock_openai_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 15,
            "classification": "Likely Scam",
            "reasons": [
                "Requests upfront payment for job materials",
                "Unrealistic salary promises with no experience required",
                "Uses high-pressure tactics and urgency"
            ],
            "confidence": 0.95
        })
        mock_choice.message = mock_message
        mock_openai_response.choices = [mock_choice]
        
        # Mock Twilio response
        mock_twilio_message = Mock()
        mock_twilio_message.sid = "SM1234567890abcdef1234567890abcdef"
        
        job_text = "URGENT! Make $5000/week from home! Send $200 for starter kit NOW!"
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_openai_response), \
             patch.object(twilio_service.client.messages, 'create', return_value=mock_twilio_message) as mock_twilio_create:
            
            # Analyze job text
            analysis_result = await openai_service.analyze_job_ad(job_text)
            
            # Send analysis result
            success = twilio_service.send_analysis_result("whatsapp:+1987654321", analysis_result)
            
            assert success is True
            
            # Verify Twilio message content
            mock_twilio_create.assert_called_once()
            call_kwargs = mock_twilio_create.call_args.kwargs
            
            assert "15/100" in call_kwargs['body']  # Check for trust score value
            assert "Likely Scam" in call_kwargs['body']
            assert "Requests upfront payment" in call_kwargs['body']


class TestExternalServiceFailureRecovery:
    """Integration tests for external service failure recovery."""
    
    @pytest.mark.asyncio
    async def test_openai_failure_graceful_degradation(self, mock_config):
        """Test graceful degradation when OpenAI service fails."""
        service = OpenAIAnalysisService(mock_config)
        
        # Test different types of failures
        failure_scenarios = [
            (openai.APITimeoutError("Timeout"), "Analysis service is currently unavailable"),
            (openai.RateLimitError("Rate limit", response=Mock(status_code=429), body={}), "Service is temporarily busy"),
            (openai.APIError("API Error", request=Mock(), body={}), "Unable to analyze the job posting")
        ]
        
        for exception, expected_message in failure_scenarios:
            with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock, side_effect=exception):
                with pytest.raises(Exception, match=expected_message):
                    await service.analyze_job_ad("Test job posting")
    
    def test_twilio_failure_graceful_degradation(self, mock_config):
        """Test graceful degradation when Twilio service fails."""
        service = TwilioResponseService(mock_config)
        
        analysis_result = JobAnalysisResult(
            trust_score=50,
            classification=JobClassification.SUSPICIOUS,
            reasons=["Test reason 1", "Test reason 2", "Test reason 3"],
            confidence=0.7
        )
        
        # Test different Twilio failures
        with patch.object(service.client.messages, 'create', side_effect=TwilioException("Service unavailable")):
            result = service.send_analysis_result("whatsapp:+1987654321", analysis_result)
            assert result is False
        
        with patch.object(service.client.messages, 'create', side_effect=Exception("Network error")):
            result = service.send_analysis_result("whatsapp:+1987654321", analysis_result)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__])