"""
Performance tests for concurrent request handling.

These tests verify that the application can handle multiple concurrent requests
efficiently and maintain performance under load.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.data_models import JobAnalysisResult, JobClassification


@pytest.fixture
def client():
    """Create test client for performance tests."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Mock configuration for performance tests."""
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


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for performance tests."""
    return JobAnalysisResult(
        trust_score=75,
        classification=JobClassification.LEGIT,
        reasons=["Professional description", "Realistic salary", "Clear requirements"],
        confidence=0.8
    )


class TestConcurrentRequestHandling:
    """Test concurrent request handling performance."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_concurrent_text_message_processing(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config, sample_analysis_result):
        """Test processing multiple concurrent text messages."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = sample_analysis_result
        mock_openai_service_class.return_value = mock_openai_service
        
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Prepare test data for concurrent requests
        num_requests = 10
        webhook_data_template = {
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Software Engineer position at TechCorp. Salary: $100k. Requirements: Python, 3+ years experience.",
            "NumMedia": "0"
        }
        
        def make_request(request_id):
            """Make a single webhook request."""
            data = webhook_data_template.copy()
            data["MessageSid"] = f"SM{request_id:030d}"
            
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=data)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        for result in results:
            assert result["status_code"] == 200
        
        # Verify performance metrics
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        # Performance assertions (adjust thresholds as needed)
        assert total_time < 10.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time}s exceeded threshold"
        assert max_response_time < 5.0, f"Max response time {max_response_time}s exceeded threshold"
        
        # Verify all requests were processed
        assert mock_openai_service.analyze_job_ad.call_count == num_requests
        assert mock_twilio_service.send_analysis_result.call_count == num_requests
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.pdf_processing.PDFProcessingService')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_concurrent_pdf_message_processing(self, mock_twilio_service_class, mock_openai_service_class, mock_pdf_service_class, mock_get_config, client, mock_config, sample_analysis_result):
        """Test processing multiple concurrent PDF messages."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        
        mock_pdf_service = AsyncMock()
        mock_pdf_service.process_pdf_url.return_value = "Extracted PDF text content for analysis"
        mock_pdf_service_class.return_value = mock_pdf_service
        
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = sample_analysis_result
        mock_openai_service_class.return_value = mock_openai_service
        
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Prepare test data for concurrent PDF requests
        num_requests = 5  # Fewer requests for PDF processing due to complexity
        webhook_data_template = {
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "",
            "NumMedia": "1",
            "MediaContentType0": "application/pdf"
        }
        
        def make_pdf_request(request_id):
            """Make a single PDF webhook request."""
            data = webhook_data_template.copy()
            data["MessageSid"] = f"SM{request_id:030d}"
            data["MediaUrl0"] = f"https://api.twilio.com/media/job-{request_id}.pdf"
            
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=data)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent PDF requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_pdf_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        for result in results:
            assert result["status_code"] == 200
        
        # Verify performance metrics (more lenient for PDF processing)
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        assert total_time < 15.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 5.0, f"Average response time {avg_response_time}s exceeded threshold"
        assert max_response_time < 10.0, f"Max response time {max_response_time}s exceeded threshold"
        
        # Verify all requests were processed
        assert mock_pdf_service.process_pdf_url.call_count == num_requests
        assert mock_openai_service.analyze_job_ad.call_count == num_requests
        assert mock_twilio_service.send_analysis_result.call_count == num_requests
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_mixed_concurrent_requests(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config, sample_analysis_result):
        """Test processing mixed types of concurrent requests."""
        # Setup mocks
        mock_get_config.return_value = mock_config
        
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = sample_analysis_result
        mock_openai_service_class.return_value = mock_openai_service
        
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service.send_welcome_message.return_value = True
        mock_message = Mock()
        mock_message.sid = "test-sid"
        mock_twilio_service.client = Mock()
        mock_twilio_service.client.messages.create.return_value = mock_message
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Prepare mixed request types
        requests_data = [
            # Text messages
            {
                "MessageSid": "SM1000000000000000000000000000001",
                "From": "whatsapp:+1987654321",
                "To": "whatsapp:+1234567890",
                "Body": "Software Engineer at Google. $120k salary.",
                "NumMedia": "0"
            },
            # Help request
            {
                "MessageSid": "SM1000000000000000000000000000002",
                "From": "whatsapp:+1987654322",
                "To": "whatsapp:+1234567890",
                "Body": "help",
                "NumMedia": "0"
            },
            # Short invalid message
            {
                "MessageSid": "SM1000000000000000000000000000003",
                "From": "whatsapp:+1987654323",
                "To": "whatsapp:+1234567890",
                "Body": "hi",
                "NumMedia": "0"
            },
            # Another text message
            {
                "MessageSid": "SM1000000000000000000000000000004",
                "From": "whatsapp:+1987654324",
                "To": "whatsapp:+1234567890",
                "Body": "Data Analyst position at TechCorp. Requirements: SQL, Python.",
                "NumMedia": "0"
            }
        ]
        
        def make_mixed_request(data):
            """Make a webhook request with given data."""
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=data)
            end_time = time.time()
            
            return {
                "message_sid": data["MessageSid"],
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Execute mixed concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_mixed_request, data) for data in requests_data]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == len(requests_data)
        for result in results:
            assert result["status_code"] == 200
        
        # Verify performance
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert total_time < 8.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 3.0, f"Average response time {avg_response_time}s exceeded threshold"


class TestHealthEndpointPerformance:
    """Test health endpoint performance under load."""
    
    def test_health_endpoint_concurrent_requests(self, client):
        """Test health endpoint performance with concurrent requests."""
        num_requests = 20
        
        def make_health_request(request_id):
            """Make a single health check request."""
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent health requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        for result in results:
            assert result["status_code"] == 200
        
        # Verify performance (health endpoint should be very fast)
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        assert total_time < 5.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 0.5, f"Average response time {avg_response_time}s exceeded threshold"
        assert max_response_time < 1.0, f"Max response time {max_response_time}s exceeded threshold"


class TestAsyncServicePerformance:
    """Test async service performance."""
    
    @pytest.mark.asyncio
    async def test_openai_service_concurrent_analysis(self, mock_config, sample_analysis_result):
        """Test OpenAI service handling concurrent analysis requests."""
        from app.services.openai_analysis import OpenAIAnalysisService
        
        service = OpenAIAnalysisService(mock_config)
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"trust_score": 75, "classification": "Legit", "reasons": ["Good", "Valid", "Professional"], "confidence": 0.8}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        job_texts = [
            "Software Engineer at Google",
            "Data Analyst at Microsoft", 
            "Product Manager at Apple",
            "DevOps Engineer at Amazon",
            "UX Designer at Facebook"
        ]
        
        async def analyze_job(text):
            """Analyze a single job posting."""
            start_time = time.time()
            with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
                result = await service.analyze_job_ad(text)
            end_time = time.time()
            
            return {
                "text": text,
                "result": result,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent analyses
        start_time = time.time()
        tasks = [analyze_job(text) for text in job_texts]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all analyses completed
        assert len(results) == len(job_texts)
        for result in results:
            assert isinstance(result["result"], JobAnalysisResult)
            assert result["result"].trust_score == 75
        
        # Verify performance
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        assert total_time < 3.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 1.0, f"Average response time {avg_response_time}s exceeded threshold"
        assert max_response_time < 2.0, f"Max response time {max_response_time}s exceeded threshold"
    
    @pytest.mark.asyncio
    async def test_pdf_service_concurrent_processing(self, mock_config):
        """Test PDF service handling concurrent processing requests."""
        from app.services.pdf_processing import PDFProcessingService
        
        service = PDFProcessingService(mock_config)
        
        # Mock HTTP responses and PDF extraction
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": "1024"}
        mock_response.content = b"%PDF-1.4 fake content"
        
        mock_page = Mock()
        mock_page.extract_text.return_value = "Extracted job posting text"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        pdf_urls = [
            "https://example.com/job1.pdf",
            "https://example.com/job2.pdf",
            "https://example.com/job3.pdf"
        ]
        
        async def process_pdf(url):
            """Process a single PDF."""
            start_time = time.time()
            with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response), \
                 patch('pdfplumber.open', return_value=mock_pdf):
                result = await service.process_pdf_url(url)
            end_time = time.time()
            
            return {
                "url": url,
                "result": result,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent PDF processing
        start_time = time.time()
        tasks = [process_pdf(url) for url in pdf_urls]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all processing completed
        assert len(results) == len(pdf_urls)
        for result in results:
            assert result["result"] == "Extracted job posting text"
        
        # Verify performance
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        
        assert total_time < 5.0, f"Total time {total_time}s exceeded threshold"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time}s exceeded threshold"


class TestMemoryAndResourceUsage:
    """Test memory and resource usage under load."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_memory_usage_under_load(self, mock_twilio_service_class, mock_openai_service_class, mock_get_config, client, mock_config, sample_analysis_result):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        # Setup mocks
        mock_get_config.return_value = mock_config
        
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = sample_analysis_result
        mock_openai_service_class.return_value = mock_openai_service
        
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute many requests
        num_requests = 50
        webhook_data_template = {
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "Body": "Software Engineer position with various requirements and details.",
            "NumMedia": "0"
        }
        
        for i in range(num_requests):
            data = webhook_data_template.copy()
            data["MessageSid"] = f"SM{i:030d}"
            response = client.post("/webhook/whatsapp", data=data)
            assert response.status_code == 200
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100, f"Memory increased by {memory_increase}MB, which may indicate a memory leak"


if __name__ == "__main__":
    pytest.main([__file__])