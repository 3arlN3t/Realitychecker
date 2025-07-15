"""
Pytest configuration and shared fixtures for comprehensive test suite.

This module provides shared test configuration, fixtures, and utilities
for all test modules in the Reality Checker WhatsApp Bot test suite.
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.models.data_models import AppConfig, JobAnalysisResult, JobClassification
from tests.fixtures.job_ad_samples import JobAdFixtures, WebhookDataFixtures, TestPhoneNumbers
from tests.fixtures.pdf_samples import PDFFixtures, MockPDFResponses, PDFExtractionMocks


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Configuration fixtures
@pytest.fixture
def mock_config():
    """Create a mock AppConfig for testing."""
    return AppConfig(
        openai_api_key="test-openai-key-12345",
        twilio_account_sid="test-twilio-sid-12345",
        twilio_auth_token="test-twilio-token-12345",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=10,
        openai_model="gpt-4",
        log_level="INFO"
    )


@pytest.fixture
def test_config():
    """Create a test configuration with environment variables."""
    test_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "TWILIO_ACCOUNT_SID": "test-twilio-sid",
        "TWILIO_AUTH_TOKEN": "test-twilio-token",
        "TWILIO_PHONE_NUMBER": "+1234567890",
        "MAX_PDF_SIZE_MB": "10",
        "OPENAI_MODEL": "gpt-4",
        "LOG_LEVEL": "INFO"
    }
    
    with patch.dict(os.environ, test_env):
        yield AppConfig.from_env()


# Job analysis result fixtures
@pytest.fixture
def legitimate_analysis_result():
    """Create a legitimate job analysis result."""
    return JobAnalysisResult(
        trust_score=85,
        classification=JobClassification.LEGIT,
        reasons=[
            "Company has verifiable online presence and contact information",
            "Job description is detailed and matches industry standards",
            "Salary range is realistic for the position and location"
        ],
        confidence=0.9
    )


@pytest.fixture
def suspicious_analysis_result():
    """Create a suspicious job analysis result."""
    return JobAnalysisResult(
        trust_score=45,
        classification=JobClassification.SUSPICIOUS,
        reasons=[
            "Unrealistic income promises without clear job duties",
            "Requests upfront payment for training materials",
            "Uses unprofessional email address"
        ],
        confidence=0.8
    )


@pytest.fixture
def scam_analysis_result():
    """Create a scam job analysis result."""
    return JobAnalysisResult(
        trust_score=15,
        classification=JobClassification.LIKELY_SCAM,
        reasons=[
            "Demands immediate upfront payment",
            "Uses high-pressure tactics and urgency",
            "Requests wire transfer to untraceable account"
        ],
        confidence=0.95
    )


# Job ad fixtures
@pytest.fixture
def job_ad_samples():
    """Provide access to job advertisement samples."""
    return JobAdFixtures()


@pytest.fixture
def legitimate_job_text():
    """Get a legitimate job posting text."""
    return JobAdFixtures.LEGITIMATE_JOBS[0].content


@pytest.fixture
def suspicious_job_text():
    """Get a suspicious job posting text."""
    return JobAdFixtures.SUSPICIOUS_JOBS[0].content


@pytest.fixture
def scam_job_text():
    """Get a scam job posting text."""
    return JobAdFixtures.SCAM_JOBS[0].content


# PDF fixtures
@pytest.fixture
def pdf_samples():
    """Provide access to PDF samples."""
    return PDFFixtures()


@pytest.fixture
def valid_pdf_sample():
    """Get a valid PDF sample."""
    return PDFFixtures.VALID_PDF_SAMPLES[0]


@pytest.fixture
def invalid_pdf_sample():
    """Get an invalid PDF sample."""
    return PDFFixtures.INVALID_PDF_SAMPLES[0]


# Webhook data fixtures
@pytest.fixture
def webhook_data_factory():
    """Factory for creating webhook data."""
    return WebhookDataFixtures()


@pytest.fixture
def test_phone_numbers():
    """Provide test phone numbers."""
    return TestPhoneNumbers()


# Service mock fixtures
@pytest.fixture
def mock_openai_service():
    """Create a mock OpenAI service."""
    service = AsyncMock()
    service.analyze_job_ad = AsyncMock()
    return service


@pytest.fixture
def mock_twilio_service():
    """Create a mock Twilio service."""
    service = Mock()
    service.send_analysis_result = Mock(return_value=True)
    service.send_welcome_message = Mock(return_value=True)
    service.send_error_message = Mock(return_value=True)
    
    # Mock Twilio client
    mock_message = Mock()
    mock_message.sid = "test-message-sid"
    service.client = Mock()
    service.client.messages.create = Mock(return_value=mock_message)
    
    return service


@pytest.fixture
def mock_pdf_service():
    """Create a mock PDF processing service."""
    service = AsyncMock()
    service.process_pdf_url = AsyncMock()
    service.download_pdf = AsyncMock()
    service.extract_text = AsyncMock()
    return service


@pytest.fixture
def mock_message_handler():
    """Create a mock message handler service."""
    handler = AsyncMock()
    handler.process_message = AsyncMock(return_value=True)
    handler.handle_text_message = AsyncMock(return_value=True)
    handler.handle_media_message = AsyncMock(return_value=True)
    return handler


# HTTP client mocks
@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for external requests."""
    client = AsyncMock()
    return client


# Database and storage mocks (if needed in future)
@pytest.fixture
def mock_database():
    """Create a mock database connection."""
    db = Mock()
    return db


# Temporary file fixtures
@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        # Write minimal PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n9\n%%EOF"
        temp_file.write(pdf_content)
        temp_file.flush()
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass


# Test data generators
@pytest.fixture
def generate_test_message_sids():
    """Generate unique message SIDs for testing."""
    counter = 0
    
    def _generate():
        nonlocal counter
        counter += 1
        return f"SM{counter:030d}"
    
    return _generate


@pytest.fixture
def generate_webhook_data():
    """Generate webhook data for testing."""
    def _generate(message_type="text", body="Test message", from_number=None):
        from_number = from_number or TestPhoneNumbers.LEGITIMATE_USER
        message_sid = f"SM{hash(body) % 1000000:030d}"
        
        if message_type == "text":
            return WebhookDataFixtures.create_text_webhook_data(message_sid, from_number, body)
        elif message_type == "media":
            return WebhookDataFixtures.create_media_webhook_data(
                message_sid, from_number, "https://example.com/test.pdf"
            )
        elif message_type == "help":
            return WebhookDataFixtures.create_help_webhook_data(message_sid, from_number)
        else:
            raise ValueError(f"Unknown message type: {message_type}")
    
    return _generate


# Performance testing fixtures
@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests."""
    metrics = {
        "response_times": [],
        "memory_usage": [],
        "cpu_usage": [],
        "request_count": 0
    }
    
    def add_response_time(time_ms):
        metrics["response_times"].append(time_ms)
        metrics["request_count"] += 1
    
    def add_memory_usage(memory_mb):
        metrics["memory_usage"].append(memory_mb)
    
    def get_average_response_time():
        if not metrics["response_times"]:
            return 0
        return sum(metrics["response_times"]) / len(metrics["response_times"])
    
    def get_max_response_time():
        return max(metrics["response_times"]) if metrics["response_times"] else 0
    
    metrics["add_response_time"] = add_response_time
    metrics["add_memory_usage"] = add_memory_usage
    metrics["get_average_response_time"] = get_average_response_time
    metrics["get_max_response_time"] = get_max_response_time
    
    return metrics


# Error simulation fixtures
@pytest.fixture
def simulate_openai_errors():
    """Simulate various OpenAI API errors."""
    import openai
    
    def _create_error(error_type):
        if error_type == "timeout":
            return openai.APITimeoutError("Request timed out")
        elif error_type == "rate_limit":
            mock_response = Mock()
            mock_response.status_code = 429
            return openai.RateLimitError("Rate limit exceeded", response=mock_response, body={})
        elif error_type == "api_error":
            return openai.APIError("API error", request=Mock(), body={})
        elif error_type == "auth_error":
            return openai.AuthenticationError("Invalid API key")
        else:
            return Exception(f"Unknown error type: {error_type}")
    
    return _create_error


@pytest.fixture
def simulate_twilio_errors():
    """Simulate various Twilio API errors."""
    from twilio.base.exceptions import TwilioException, TwilioRestException
    
    def _create_error(error_type):
        if error_type == "auth_error":
            return TwilioRestException(401, "https://api.twilio.com", "Authentication failed")
        elif error_type == "rate_limit":
            return TwilioRestException(429, "https://api.twilio.com", "Rate limit exceeded")
        elif error_type == "service_error":
            return TwilioException("Service unavailable")
        else:
            return Exception(f"Unknown error type: {error_type}")
    
    return _create_error


@pytest.fixture
def simulate_network_errors():
    """Simulate various network errors."""
    import httpx
    
    def _create_error(error_type):
        if error_type == "timeout":
            return httpx.TimeoutException("Request timed out")
        elif error_type == "connection":
            return httpx.ConnectError("Connection failed")
        elif error_type == "network":
            return httpx.NetworkError("Network error")
        else:
            return Exception(f"Unknown error type: {error_type}")
    
    return _create_error


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG"
    }
    
    with patch.dict(os.environ, test_env):
        yield


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Perform any necessary cleanup
    # This could include clearing caches, resetting global state, etc.


# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=JobAdFixtures.get_all_samples())
def all_job_samples(request):
    """Parametrized fixture that provides all job samples."""
    return request.param


@pytest.fixture(params=PDFFixtures.get_all_samples())
def all_pdf_samples(request):
    """Parametrized fixture that provides all PDF samples."""
    return request.param


@pytest.fixture(params=[
    JobClassification.LEGIT,
    JobClassification.SUSPICIOUS,
    JobClassification.LIKELY_SCAM
])
def all_classifications(request):
    """Parametrized fixture that provides all job classifications."""
    return request.param


# Utility functions for tests
def assert_analysis_result_valid(result: JobAnalysisResult):
    """Assert that an analysis result is valid."""
    assert isinstance(result, JobAnalysisResult)
    assert 0 <= result.trust_score <= 100
    assert result.classification in [JobClassification.LEGIT, JobClassification.SUSPICIOUS, JobClassification.LIKELY_SCAM]
    assert len(result.reasons) == 3
    assert all(reason.strip() for reason in result.reasons)
    assert 0.0 <= result.confidence <= 1.0


def assert_webhook_data_valid(data: Dict[str, Any]):
    """Assert that webhook data is valid."""
    required_fields = ["MessageSid", "From", "To", "Body", "NumMedia"]
    for field in required_fields:
        assert field in data
    
    assert data["MessageSid"].startswith("SM")
    assert data["From"].startswith("whatsapp:")
    assert data["To"].startswith("whatsapp:")
    assert isinstance(data["NumMedia"], str)
    assert data["NumMedia"].isdigit()


# Export utility functions
__all__ = [
    "assert_analysis_result_valid",
    "assert_webhook_data_valid"
]