"""
Unit tests for OpenAI analysis service.

Tests the OpenAIAnalysisService class with mocked OpenAI responses
and various error scenarios.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
import openai

from app.services.openai_analysis import OpenAIAnalysisService
from app.models.data_models import AppConfig, JobAnalysisResult, JobClassification


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AppConfig(
        openai_api_key="test-api-key",
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_phone_number="+1234567890",
        openai_model="gpt-4"
    )


@pytest.fixture
def openai_service(mock_config):
    """Create OpenAI analysis service instance for testing."""
    return OpenAIAnalysisService(mock_config)


@pytest.fixture
def legitimate_job_text():
    """Sample legitimate job posting text."""
    return """
    Software Engineer - Google Inc.
    
    We are seeking a talented Software Engineer to join our team in Mountain View, CA.
    
    Responsibilities:
    - Design and develop scalable software solutions
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    
    Requirements:
    - Bachelor's degree in Computer Science
    - 3+ years of experience in software development
    - Proficiency in Python, Java, or C++
    
    Salary: $120,000 - $180,000 per year
    Benefits: Health insurance, 401k, stock options
    
    Contact: careers@google.com
    """


@pytest.fixture
def suspicious_job_text():
    """Sample suspicious job posting text."""
    return """
    Work From Home - Easy Money!
    
    Make $5000 per week working from home! No experience needed!
    
    Just send us $200 for training materials and start earning immediately!
    
    Contact: easymoney123@gmail.com
    """


@pytest.fixture
def scam_job_text():
    """Sample scam job posting text."""
    return """
    URGENT! Make $10,000/month from home!
    
    Send $500 for starter kit NOW! Limited time offer!
    
    No questions asked! Guaranteed income!
    
    Wire money to: Western Union Account 123456
    """


class TestOpenAIAnalysisService:
    """Test cases for OpenAI analysis service."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        service = OpenAIAnalysisService(mock_config)
        assert service.config == mock_config
        assert service.model == "gpt-4"
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_analyze_job_ad_legitimate(self, openai_service, legitimate_job_text):
        """Test analysis of legitimate job posting."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 85,
            "classification": "Legit",
            "reasons": [
                "Company has verifiable online presence",
                "Job description is detailed and professional",
                "Salary range is realistic for the position"
            ],
            "confidence": 0.9
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await openai_service.analyze_job_ad(legitimate_job_text)
            
            assert isinstance(result, JobAnalysisResult)
            assert result.trust_score == 85
            assert result.classification == JobClassification.LEGIT
            assert len(result.reasons) == 3
            assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_analyze_job_ad_suspicious(self, openai_service, suspicious_job_text):
        """Test analysis of suspicious job posting."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 45,
            "classification": "Suspicious",
            "reasons": [
                "Unrealistic income promises without clear job duties",
                "Requests upfront payment for training materials",
                "Uses unprofessional email address"
            ],
            "confidence": 0.8
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await openai_service.analyze_job_ad(suspicious_job_text)
            
            assert result.trust_score == 45
            assert result.classification == JobClassification.SUSPICIOUS
            assert len(result.reasons) == 3
    
    @pytest.mark.asyncio
    async def test_analyze_job_ad_scam(self, openai_service, scam_job_text):
        """Test analysis of scam job posting."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "trust_score": 5,
            "classification": "Likely Scam",
            "reasons": [
                "Demands immediate upfront payment",
                "Uses high-pressure tactics and urgency",
                "Requests wire transfer to untraceable account"
            ],
            "confidence": 0.95
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await openai_service.analyze_job_ad(scam_job_text)
            
            assert result.trust_score == 5
            assert result.classification == JobClassification.LIKELY_SCAM
            assert len(result.reasons) == 3
    
    @pytest.mark.asyncio
    async def test_analyze_empty_job_text(self, openai_service):
        """Test analysis with empty job text."""
        with pytest.raises(ValueError, match="Job text cannot be empty"):
            await openai_service.analyze_job_ad("")
        
        with pytest.raises(ValueError, match="Job text cannot be empty"):
            await openai_service.analyze_job_ad("   ")
    
    @pytest.mark.asyncio
    async def test_openai_timeout_error(self, openai_service, legitimate_job_text):
        """Test handling of OpenAI timeout error."""
        with patch.object(openai_service.client.chat.completions, 'create', 
                         new_callable=AsyncMock, side_effect=openai.APITimeoutError("Request timed out")):
            with pytest.raises(Exception, match="Analysis service is currently unavailable"):
                await openai_service.analyze_job_ad(legitimate_job_text)
    
    @pytest.mark.asyncio
    async def test_openai_rate_limit_error(self, openai_service, legitimate_job_text):
        """Test handling of OpenAI rate limit error."""
        # Create a mock response and body for the exception
        mock_response = Mock()
        mock_response.status_code = 429
        mock_body = {"error": {"message": "Rate limit exceeded"}}
        
        with patch.object(openai_service.client.chat.completions, 'create',
                         new_callable=AsyncMock, side_effect=openai.RateLimitError("Rate limit exceeded", response=mock_response, body=mock_body)):
            with pytest.raises(Exception, match="Service is temporarily busy"):
                await openai_service.analyze_job_ad(legitimate_job_text)
    
    @pytest.mark.asyncio
    async def test_openai_api_error(self, openai_service, legitimate_job_text):
        """Test handling of general OpenAI API error."""
        mock_request = Mock()
        mock_body = {"error": {"message": "API error"}}
        with patch.object(openai_service.client.chat.completions, 'create',
                         new_callable=AsyncMock, side_effect=openai.APIError("API error", request=mock_request, body=mock_body)):
            with pytest.raises(Exception, match="Unable to analyze the job posting"):
                await openai_service.analyze_job_ad(legitimate_job_text)
    
    @pytest.mark.asyncio
    async def test_empty_openai_response(self, openai_service, legitimate_job_text):
        """Test handling of empty OpenAI response."""
        mock_response = Mock()
        mock_response.choices = []
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception, match="Empty response from OpenAI API"):
                await openai_service.analyze_job_ad(legitimate_job_text)
    
    def test_build_analysis_prompt(self, openai_service):
        """Test prompt building functionality."""
        job_text = "Test job posting"
        prompt = openai_service.build_analysis_prompt(job_text)
        
        assert "Test job posting" in prompt
        assert "trust_score" in prompt
        assert "classification" in prompt
        assert "reasons" in prompt
        assert "confidence" in prompt
        assert "Legit" in prompt
        assert "Suspicious" in prompt
        assert "Likely Scam" in prompt
    
    def test_parse_analysis_response_valid(self, openai_service):
        """Test parsing valid analysis response."""
        response_text = json.dumps({
            "trust_score": 75,
            "classification": "Legit",
            "reasons": ["Reason 1", "Reason 2", "Reason 3"],
            "confidence": 0.85
        })
        
        result = openai_service.parse_analysis_response(response_text)
        
        assert result.trust_score == 75
        assert result.classification == JobClassification.LEGIT
        assert result.reasons == ["Reason 1", "Reason 2", "Reason 3"]
        assert result.confidence == 0.85
    
    def test_parse_analysis_response_with_extra_text(self, openai_service):
        """Test parsing response with extra text around JSON."""
        response_text = f"""
        Here's my analysis:
        
        {json.dumps({
            "trust_score": 60,
            "classification": "Suspicious", 
            "reasons": ["Red flag 1", "Red flag 2", "Red flag 3"],
            "confidence": 0.7
        })}
        
        Hope this helps!
        """
        
        result = openai_service.parse_analysis_response(response_text)
        
        assert result.trust_score == 60
        assert result.classification == JobClassification.SUSPICIOUS
    
    def test_parse_analysis_response_invalid_json(self, openai_service):
        """Test parsing invalid JSON response."""
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response("Not valid JSON")
    
    def test_parse_analysis_response_missing_fields(self, openai_service):
        """Test parsing response with missing required fields."""
        response_text = json.dumps({
            "trust_score": 80,
            "classification": "Legit"
            # Missing reasons and confidence
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)
    
    def test_parse_analysis_response_invalid_classification(self, openai_service):
        """Test parsing response with invalid classification."""
        response_text = json.dumps({
            "trust_score": 80,
            "classification": "Invalid Classification",
            "reasons": ["Reason 1", "Reason 2", "Reason 3"],
            "confidence": 0.8
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)
    
    def test_parse_analysis_response_invalid_trust_score(self, openai_service):
        """Test parsing response with invalid trust score."""
        response_text = json.dumps({
            "trust_score": 150,  # Invalid: > 100
            "classification": "Legit",
            "reasons": ["Reason 1", "Reason 2", "Reason 3"],
            "confidence": 0.8
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)
    
    def test_parse_analysis_response_invalid_reasons_count(self, openai_service):
        """Test parsing response with wrong number of reasons."""
        response_text = json.dumps({
            "trust_score": 80,
            "classification": "Legit",
            "reasons": ["Only one reason"],  # Should be exactly 3
            "confidence": 0.8
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)
    
    def test_parse_analysis_response_empty_reasons(self, openai_service):
        """Test parsing response with empty reasons."""
        response_text = json.dumps({
            "trust_score": 80,
            "classification": "Legit",
            "reasons": ["Good reason", "", "Another reason"],  # Empty string
            "confidence": 0.8
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)
    
    def test_parse_analysis_response_invalid_confidence(self, openai_service):
        """Test parsing response with invalid confidence value."""
        response_text = json.dumps({
            "trust_score": 80,
            "classification": "Legit",
            "reasons": ["Reason 1", "Reason 2", "Reason 3"],
            "confidence": 1.5  # Invalid: > 1.0
        })
        
        with pytest.raises(Exception, match="Invalid analysis response format"):
            openai_service.parse_analysis_response(response_text)


class TestOpenAIAnalysisServiceIntegration:
    """Integration tests for OpenAI analysis service."""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, openai_service, legitimate_job_text):
        """Test complete analysis workflow with mocked OpenAI."""
        expected_response = {
            "trust_score": 90,
            "classification": "Legit",
            "reasons": [
                "Professional company with verifiable presence",
                "Detailed job requirements and responsibilities",
                "Realistic compensation and benefits package"
            ],
            "confidence": 0.92
        }
        
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(expected_response)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(openai_service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response) as mock_create:
            result = await openai_service.analyze_job_ad(legitimate_job_text)
            
            # Verify OpenAI was called with correct parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            
            assert call_args.kwargs['model'] == 'gpt-4'
            assert call_args.kwargs['temperature'] == 0.3
            assert call_args.kwargs['max_tokens'] == 1000
            assert call_args.kwargs['timeout'] == 30.0
            assert len(call_args.kwargs['messages']) == 2
            assert legitimate_job_text in call_args.kwargs['messages'][1]['content']
            
            # Verify result
            assert result.trust_score == 90
            assert result.classification == JobClassification.LEGIT
            assert len(result.reasons) == 3
            assert result.confidence == 0.92