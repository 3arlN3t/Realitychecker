"""
Comprehensive tests for the enhanced AI analysis service.

Tests cover all enhanced capabilities including rule-based detection,
similarity checking, batch processing, streaming analysis, and feedback learning.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, List, Any

from app.services.enhanced_ai_analysis import EnhancedAIAnalysisService
from app.models.data_models import AppConfig, JobAnalysisResult, JobClassification


class TestEnhancedAIAnalysisService:
    """Test suite for EnhancedAIAnalysisService."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return AppConfig(
            openai_api_key="test_key",
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_phone_number="test_phone",
            openai_model="gpt-4",
            openai_fallback_model="gpt-3.5-turbo",
            enable_rule_based_detection=True,
            enable_similarity_checking=True,
            similarity_threshold=0.75,
            analysis_history_max_size=100,
            rule_based_confidence_threshold=0.7,
            enable_enhanced_analysis=True,
            batch_analysis_size=3,
            enable_streaming_analysis=True,
            enable_feedback_learning=True
        )
    
    @pytest.fixture
    def service(self, config):
        """Create a test service instance."""
        with patch('app.services.enhanced_ai_analysis.AsyncOpenAI'):
            return EnhancedAIAnalysisService(config)
    
    @pytest.fixture
    def mock_client(self, service):
        """Create a mock OpenAI client."""
        service.client = AsyncMock()
        return service.client
    
    @pytest.fixture
    def sample_job_text(self):
        """Sample job posting text for testing."""
        return """
        Senior Software Engineer Position
        
        We are seeking a qualified software engineer with:
        - Bachelor's degree in Computer Science
        - 5+ years of experience in Python development
        - Experience with FastAPI and databases
        - Strong problem-solving skills
        
        Responsibilities:
        - Develop and maintain web applications
        - Collaborate with cross-functional teams
        - Write clean, maintainable code
        - Participate in code reviews
        
        We offer competitive salary, health insurance, and 401k benefits.
        Please submit your resume and cover letter.
        """
    
    @pytest.fixture
    def scam_job_text(self):
        """Sample scam job posting for testing."""
        return """
        URGENT! Work from home opportunity!
        
        Earn $5000+ per week from home!
        No experience required!
        
        Just pay $199 training fee to get started.
        Contact us via WhatsApp only: +1234567890
        
        Limited time offer - Act now!
        Make money fast with our proven system!
        """
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result for testing."""
        return JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=[
                "Clear job requirements and responsibilities",
                "Standard benefits and hiring process mentioned",
                "Professional posting format and language"
            ],
            confidence=0.9
        )


class TestInitialization:
    """Test service initialization."""
    
    def test_service_initialization(self, service, config):
        """Test that service initializes correctly."""
        assert service.models["primary"] == config.openai_model
        assert service.models["fallback"] == config.openai_fallback_model
        assert service.analysis_history_max_size == config.analysis_history_max_size
        assert service.vectorizer is not None
        assert service.scam_patterns is not None
        assert isinstance(service.feedback_data, dict)
    
    def test_scam_patterns_initialization(self, service):
        """Test that scam patterns are properly initialized."""
        patterns = service.scam_patterns
        assert "high_risk_indicators" in patterns
        assert "medium_risk_indicators" in patterns
        assert "positive_indicators" in patterns
        
        # Check that patterns have required structure
        for pattern_list in patterns.values():
            for pattern in pattern_list:
                assert "pattern" in pattern
                assert "weight" in pattern
                assert "description" in pattern


class TestRuleBasedDetection:
    """Test rule-based detection functionality."""
    
    def test_high_risk_scam_detection(self, service, scam_job_text):
        """Test detection of high-risk scam indicators."""
        result = service._apply_rule_based_detection(scam_job_text)
        
        assert result is not None
        assert result.classification == JobClassification.LIKELY_SCAM
        assert result.trust_score < 50
        assert result.confidence > 0.7
        assert len(result.reasons) == 3
    
    def test_legitimate_job_detection(self, service, sample_job_text):
        """Test detection of legitimate job indicators."""
        result = service._apply_rule_based_detection(sample_job_text)
        
        # May return None if not enough patterns matched
        if result is not None:
            assert result.classification == JobClassification.LEGIT
            assert result.trust_score > 65
            assert len(result.reasons) == 3
    
    def test_empty_text_handling(self, service):
        """Test handling of empty or invalid text."""
        assert service._apply_rule_based_detection("") is None
        assert service._apply_rule_based_detection("   ") is None
        assert service._apply_rule_based_detection("short") is None
    
    def test_pattern_matching_accuracy(self, service):
        """Test accuracy of specific pattern matching."""
        # Test unrealistic salary pattern
        text = "Earn $5000 per week from home!"
        result = service._apply_rule_based_detection(text)
        assert result is not None
        assert result.classification == JobClassification.LIKELY_SCAM
        
        # Test upfront payment pattern
        text = "Great opportunity! Just pay $199 training fee to start."
        result = service._apply_rule_based_detection(text)
        assert result is not None
        assert result.classification == JobClassification.LIKELY_SCAM
        
        # Test legitimate indicators
        text = "Bachelor's degree required. Health insurance and 401k provided."
        result = service._apply_rule_based_detection(text)
        if result is not None:
            assert result.classification == JobClassification.LEGIT


class TestSimilarityChecking:
    """Test similarity checking functionality."""
    
    @pytest.mark.asyncio
    async def test_no_history_returns_none(self, service):
        """Test that no similarity check happens with empty history."""
        result = await service._check_similar_job_ads("Some job posting")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_short_text_returns_none(self, service):
        """Test that short text returns None."""
        result = await service._check_similar_job_ads("Short text")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_similarity_checking_with_history(self, service, sample_job_text, sample_analysis_result):
        """Test similarity checking with existing history."""
        # Add some history
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        # Test with similar text
        similar_text = sample_job_text.replace("Senior", "Junior")
        result = await service._check_similar_job_ads(similar_text)
        
        # Should find similarity
        if result is not None:
            assert len(result) == 2
            assert isinstance(result[0], JobAnalysisResult)
            assert isinstance(result[1], float)
            assert 0.0 <= result[1] <= 1.0
    
    @pytest.mark.asyncio
    async def test_similarity_threshold_enforcement(self, service, sample_job_text, sample_analysis_result):
        """Test that similarity threshold is enforced."""
        # Add history
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        # Test with very different text
        different_text = "Completely different job posting about cooking"
        result = await service._check_similar_job_ads(different_text)
        
        # Should not find similarity
        assert result is None


class TestAnalysisHistory:
    """Test analysis history management."""
    
    def test_add_to_history(self, service, sample_job_text, sample_analysis_result):
        """Test adding analysis results to history."""
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        assert len(service.analysis_history) == 1
        assert sample_job_text[:1000] in service.analysis_history
        assert len(service.analysis_history[sample_job_text[:1000]]) == 1
    
    def test_history_size_limit(self, service):
        """Test that history size is limited."""
        # Set small limit for testing
        service.analysis_history_max_size = 2
        
        # Add more items than limit
        for i in range(5):
            text = f"Job posting {i}"
            result = JobAnalysisResult(
                trust_score=50,
                classification=JobClassification.SUSPICIOUS,
                reasons=["Reason 1", "Reason 2", "Reason 3"],
                confidence=0.5
            )
            service._add_to_analysis_history(text, result)
        
        # Should only keep the maximum allowed
        assert len(service.analysis_history) <= 2
    
    def test_feedback_history_update(self, service, sample_job_text, sample_analysis_result):
        """Test updating history with feedback."""
        # Add original result
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        # Add feedback result
        feedback_result = JobAnalysisResult(
            trust_score=30,
            classification=JobClassification.LIKELY_SCAM,
            reasons=["Corrected reason 1", "Corrected reason 2", "Corrected reason 3"],
            confidence=1.0
        )
        service._add_to_analysis_history(sample_job_text, feedback_result, is_feedback=True)
        
        # Should have both results
        history = service.analysis_history[sample_job_text[:1000]]
        assert len(history) == 2
        assert history[-1] == feedback_result  # Feedback should be last


class TestResultCombination:
    """Test combining AI and rule-based results."""
    
    def test_combine_analysis_results(self, service):
        """Test combining AI and rule-based results."""
        ai_result = JobAnalysisResult(
            trust_score=70,
            classification=JobClassification.LEGIT,
            reasons=["AI reason 1", "AI reason 2", "AI reason 3"],
            confidence=0.8
        )
        
        rule_result = JobAnalysisResult(
            trust_score=40,
            classification=JobClassification.SUSPICIOUS,
            reasons=["Rule reason 1", "Rule reason 2", "Rule reason 3"],
            confidence=0.9
        )
        
        combined = service._combine_analysis_results(ai_result, rule_result)
        
        assert isinstance(combined, JobAnalysisResult)
        assert len(combined.reasons) == 3
        assert 0.0 <= combined.confidence <= 1.0
        assert 0 <= combined.trust_score <= 100
    
    def test_combine_with_different_classifications(self, service):
        """Test combining results with different classifications."""
        ai_result = JobAnalysisResult(
            trust_score=80,
            classification=JobClassification.LEGIT,
            reasons=["AI reason 1", "AI reason 2", "AI reason 3"],
            confidence=0.7
        )
        
        rule_result = JobAnalysisResult(
            trust_score=20,
            classification=JobClassification.LIKELY_SCAM,
            reasons=["Rule reason 1", "Rule reason 2", "Rule reason 3"],
            confidence=0.8
        )
        
        combined = service._combine_analysis_results(ai_result, rule_result)
        
        # Should include rule-based insight in reasons
        assert any("rule-based" in reason.lower() for reason in combined.reasons)


class TestBatchAnalysis:
    """Test batch analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_batch_analysis_empty_list(self, service):
        """Test batch analysis with empty list."""
        results = await service.analyze_job_ads_batch([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_batch_analysis_single_item(self, service, sample_job_text, mock_client):
        """Test batch analysis with single item."""
        # Mock the AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "trust_score": 85,
            "classification": "Legit",
            "reasons": ["Professional posting", "Clear requirements", "Standard benefits"],
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        results = await service.analyze_job_ads_batch([sample_job_text])
        
        assert len(results) == 1
        assert isinstance(results[0], JobAnalysisResult)
    
    @pytest.mark.asyncio
    async def test_batch_analysis_multiple_items(self, service, sample_job_text, scam_job_text, mock_client):
        """Test batch analysis with multiple items."""
        # Mock the AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "trust_score": 85,
            "classification": "Legit",
            "reasons": ["Professional posting", "Clear requirements", "Standard benefits"],
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        job_texts = [sample_job_text, scam_job_text]
        results = await service.analyze_job_ads_batch(job_texts)
        
        assert len(results) == 2
        assert all(isinstance(result, JobAnalysisResult) for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_analysis_with_failures(self, service, sample_job_text, mock_client):
        """Test batch analysis handles failures gracefully."""
        # Mock the AI to raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        results = await service.analyze_job_ads_batch([sample_job_text])
        
        assert len(results) == 1
        assert results[0].trust_score == 50  # Default fallback
        assert results[0].classification == JobClassification.SUSPICIOUS
        assert results[0].confidence == 0.1


class TestStreamingAnalysis:
    """Test streaming analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_streaming_analysis_callback(self, service, sample_job_text, mock_client):
        """Test streaming analysis with callback."""
        # Mock streaming response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = '{"trust_score": 85, "classification": "Legit", "reasons": ["test"], "confidence": 0.9}'
        
        mock_client.chat.completions.create.return_value = [mock_chunk]
        
        callback_data = []
        
        async def test_callback(data):
            callback_data.append(data)
        
        # Mock the parsing method
        service.parse_analysis_response = MagicMock(return_value=JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Test reason 1", "Test reason 2", "Test reason 3"],
            confidence=0.9
        ))
        
        result = await service.analyze_job_ads_streaming(sample_job_text, test_callback)
        
        assert isinstance(result, JobAnalysisResult)
        assert len(callback_data) > 0  # Should have received callbacks


class TestFeedbackLearning:
    """Test feedback learning functionality."""
    
    @pytest.mark.asyncio
    async def test_record_feedback_success(self, service, sample_job_text, sample_analysis_result):
        """Test successful feedback recording."""
        feedback = {
            "correct_classification": "Likely Scam",
            "correct_trust_score": 20,
            "comment": "This was actually a scam"
        }
        
        success = await service.record_feedback(sample_job_text, sample_analysis_result, feedback)
        
        assert success is True
        assert len(service.feedback_data) > 0
    
    @pytest.mark.asyncio
    async def test_record_feedback_updates_history(self, service, sample_job_text, sample_analysis_result):
        """Test that feedback updates analysis history."""
        feedback = {
            "correct_classification": "Likely Scam",
            "correct_trust_score": 20,
            "comment": "This was actually a scam"
        }
        
        await service.record_feedback(sample_job_text, sample_analysis_result, feedback)
        
        # Check that history was updated
        assert len(service.analysis_history) > 0
    
    def test_calculate_feedback_agreement_rate(self, service):
        """Test feedback agreement rate calculation."""
        # Add some feedback data
        service.feedback_data["Legit"] = [
            {
                "original_result": {"classification": "Legit"},
                "correct_classification": "Legit"
            },
            {
                "original_result": {"classification": "Legit"},
                "correct_classification": "Likely Scam"
            }
        ]
        
        agreement_rate = service._calculate_feedback_agreement_rate()
        assert agreement_rate == 0.5  # 1 out of 2 agreements


class TestAnalysisTemplates:
    """Test analysis template functionality."""
    
    def test_get_analysis_templates(self, service):
        """Test getting available analysis templates."""
        templates = service.get_analysis_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "model" in template
    
    @pytest.mark.asyncio
    async def test_analyze_with_standard_template(self, service, sample_job_text, mock_client):
        """Test analysis with standard template."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "trust_score": 85,
            "classification": "Legit",
            "reasons": ["Professional posting", "Clear requirements", "Standard benefits"],
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock the parsing method
        service.parse_analysis_response = MagicMock(return_value=JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Test reason 1", "Test reason 2", "Test reason 3"],
            confidence=0.9
        ))
        
        result = await service.analyze_with_template(sample_job_text, "standard")
        
        assert isinstance(result, JobAnalysisResult)
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_with_invalid_template(self, service, sample_job_text):
        """Test analysis with invalid template ID."""
        with pytest.raises(ValueError, match="Invalid template ID"):
            await service.analyze_with_template(sample_job_text, "invalid_template")


class TestAnalysisStatistics:
    """Test analysis statistics functionality."""
    
    def test_get_analysis_statistics_empty(self, service):
        """Test getting statistics with empty history."""
        stats = service.get_analysis_statistics()
        
        assert isinstance(stats, dict)
        assert "total_analyses" in stats
        assert "classifications" in stats
        assert "average_confidence" in stats
        assert "trust_score_distribution" in stats
        assert "feedback" in stats
        assert stats["total_analyses"] == 0
    
    def test_get_analysis_statistics_with_data(self, service, sample_job_text, sample_analysis_result):
        """Test getting statistics with analysis data."""
        # Add some analysis history
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        stats = service.get_analysis_statistics()
        
        assert stats["total_analyses"] == 1
        assert stats["classifications"]["Legit"] == 1
        assert stats["classifications"]["Suspicious"] == 0
        assert stats["classifications"]["Likely Scam"] == 0
        assert len(stats["trust_score_distribution"]) == 5
        assert stats["average_confidence"]["Legit"] == 0.9


class TestAnalysisValidation:
    """Test analysis result validation."""
    
    def test_validate_analysis_result_valid(self, service, sample_analysis_result):
        """Test validation of valid analysis result."""
        is_valid = service._validate_analysis_result(sample_analysis_result)
        assert is_valid is True
    
    def test_validate_analysis_result_low_confidence(self, service):
        """Test validation with low confidence result."""
        low_confidence_result = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.3  # Low confidence
        )
        
        is_valid = service._validate_analysis_result(low_confidence_result)
        assert is_valid is False
    
    def test_validate_analysis_result_inconsistent_classification(self, service):
        """Test validation with inconsistent classification and trust score."""
        inconsistent_result = JobAnalysisResult(
            trust_score=20,  # Low trust score
            classification=JobClassification.LEGIT,  # But classified as legit
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.8
        )
        
        is_valid = service._validate_analysis_result(inconsistent_result)
        assert is_valid is False
    
    def test_validate_analysis_result_poor_reasons(self, service):
        """Test validation with poor quality reasons."""
        poor_reasons_result = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Good job", "Yes", "Legitimate job"],  # Poor quality reasons
            confidence=0.8
        )
        
        is_valid = service._validate_analysis_result(poor_reasons_result)
        assert is_valid is False


class TestFallbackAnalysis:
    """Test fallback analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_with_rule_based(self, service, scam_job_text):
        """Test fallback analysis using rule-based detection."""
        fallback_result = await service._get_fallback_analysis(scam_job_text, "API Error")
        
        assert fallback_result is not None
        assert isinstance(fallback_result, JobAnalysisResult)
        # Should detect scam with rule-based patterns
        assert fallback_result.classification == JobClassification.LIKELY_SCAM
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_with_similar_jobs(self, service, sample_job_text, sample_analysis_result):
        """Test fallback analysis using similar job ads."""
        # Add history
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        # Test with similar text
        similar_text = sample_job_text.replace("Senior", "Junior")
        fallback_result = await service._get_fallback_analysis(similar_text, "API Error")
        
        # May find similar job if similarity is high enough
        if fallback_result is not None:
            assert isinstance(fallback_result, JobAnalysisResult)
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_default_suspicious(self, service):
        """Test fallback analysis returns default suspicious result."""
        # Test with neutral text that won't trigger rules or similarities
        neutral_text = "This is just a regular job posting with no special indicators"
        fallback_result = await service._get_fallback_analysis(neutral_text, "API Error")
        
        assert fallback_result is not None
        assert fallback_result.classification == JobClassification.SUSPICIOUS
        assert fallback_result.trust_score == 50
        assert fallback_result.confidence == 0.5
        assert "technical difficulties" in fallback_result.reasons[0].lower()


class TestSpecializedPrompts:
    """Test specialized prompt building."""
    
    def test_build_remote_work_prompt(self, service, sample_job_text):
        """Test building remote work specialized prompt."""
        prompt = service._build_remote_work_prompt(sample_job_text)
        
        assert isinstance(prompt, str)
        assert "remote work" in prompt.lower()
        assert "work from home" in prompt.lower()
        assert sample_job_text in prompt
    
    def test_build_high_salary_prompt(self, service, sample_job_text):
        """Test building high salary specialized prompt."""
        prompt = service._build_high_salary_prompt(sample_job_text)
        
        assert isinstance(prompt, str)
        assert "high salary" in prompt.lower()
        assert "salary" in prompt.lower()
        assert sample_job_text in prompt


class TestEnhancedAnalysisIntegration:
    """Test integration of enhanced analysis features."""
    
    @pytest.mark.asyncio
    async def test_enhanced_analysis_flow(self, service, sample_job_text, mock_client):
        """Test the complete enhanced analysis flow."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "trust_score": 85,
            "classification": "Legit",
            "reasons": ["Professional posting", "Clear requirements", "Standard benefits"],
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock the parsing method
        service.parse_analysis_response = MagicMock(return_value=JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Test reason 1", "Test reason 2", "Test reason 3"],
            confidence=0.9
        ))
        
        result = await service.analyze_job_ad(sample_job_text)
        
        assert isinstance(result, JobAnalysisResult)
        # Should have added to history
        assert len(service.analysis_history) > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_analysis_with_cached_result(self, service, sample_job_text, sample_analysis_result):
        """Test enhanced analysis with cached similar result."""
        # Add to history first
        service._add_to_analysis_history(sample_job_text, sample_analysis_result)
        
        # Mock the vectorizer to return high similarity
        with patch.object(service, '_check_similar_job_ads', return_value=(sample_analysis_result, 0.9)):
            result = await service.analyze_job_ad(sample_job_text)
        
        assert isinstance(result, JobAnalysisResult)
        assert result.confidence == 0.81  # 0.9 * 0.9 for cached results
    
    @pytest.mark.asyncio
    async def test_enhanced_analysis_fallback_on_primary_failure(self, service, sample_job_text, mock_client):
        """Test enhanced analysis falls back to secondary model on primary failure."""
        # Mock primary model to fail
        mock_client.chat.completions.create.side_effect = [
            Exception("Primary model failed"),
            MagicMock(choices=[MagicMock(message=MagicMock(content='{"trust_score": 50, "classification": "Suspicious", "reasons": ["Fallback analysis", "Secondary model used", "Review recommended"], "confidence": 0.7}'))])
        ]
        
        # Mock the parsing method
        service.parse_analysis_response = MagicMock(return_value=JobAnalysisResult(
            trust_score=50,
            classification=JobClassification.SUSPICIOUS,
            reasons=["Fallback analysis", "Secondary model used", "Review recommended"],
            confidence=0.7
        ))
        
        result = await service.analyze_job_ad(sample_job_text)
        
        assert isinstance(result, JobAnalysisResult)
        assert mock_client.chat.completions.create.call_count == 2  # Called twice (primary + fallback)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])