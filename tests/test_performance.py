"""
Performance tests for the Reality Checker WhatsApp bot.

These tests evaluate the system's performance under various load conditions,
measuring response times, throughput, and resource utilization.
"""

import pytest
import time
import asyncio
import statistics
import concurrent.futures
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.data_models import JobAnalysisResult, JobClassification
from tests.fixtures.job_ad_samples import JobAdFixtures, WebhookDataFixtures, TestPhoneNumbers


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Mock application configuration for performance tests."""
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


@pytest.mark.performance
class TestWebhookPerformance:
    """Performance tests for webhook endpoint."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_webhook_response_time(self, mock_twilio_service_class, mock_openai_service_class, 
                                 mock_get_config, client, mock_config):
        """Test webhook endpoint response time."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock with minimal delay
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.9
        )
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Create webhook data
        job_sample = JobAdFixtures.LEGITIMATE_JOBS[0]
        webhook_data = WebhookDataFixtures.create_text_webhook_data(
            message_sid="SM1234567890abcdef1234567890abcdef",
            from_number=TestPhoneNumbers.LEGITIMATE_USER,
            body=job_sample.content
        )
        
        # Measure response time for multiple requests
        response_times = []
        num_requests = 10
        
        for _ in range(num_requests):
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=webhook_data)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        
        # Log results
        print(f"Webhook Response Time Statistics (seconds):")
        print(f"  Average: {avg_response_time:.4f}")
        print(f"  Min: {min_response_time:.4f}")
        print(f"  Max: {max_response_time:.4f}")
        print(f"  P95: {p95_response_time:.4f}")
        
        # Assert performance requirements
        assert avg_response_time < 0.5, f"Average response time ({avg_response_time:.4f}s) exceeds threshold (0.5s)"
        assert p95_response_time < 1.0, f"P95 response time ({p95_response_time:.4f}s) exceeds threshold (1.0s)"
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_concurrent_request_handling(self, mock_twilio_service_class, mock_openai_service_class, 
                                       mock_get_config, client, mock_config):
        """Test handling of concurrent webhook requests."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock with simulated processing time
        mock_openai_service = AsyncMock()
        
        async def delayed_analysis(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API processing time
            return JobAnalysisResult(
                trust_score=85,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"],
                confidence=0.9
            )
        
        mock_openai_service.analyze_job_ad.side_effect = delayed_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Create different webhook data for concurrent requests
        webhook_data_list = []
        num_concurrent = 10
        
        for i in range(num_concurrent):
            job_sample = JobAdFixtures.LEGITIMATE_JOBS[0] if i % 3 == 0 else \
                        JobAdFixtures.SUSPICIOUS_JOBS[0] if i % 3 == 1 else \
                        JobAdFixtures.SCAM_JOBS[0]
            
            webhook_data = WebhookDataFixtures.create_text_webhook_data(
                message_sid=f"SM{i}234567890abcdef1234567890abcdef",
                from_number=f"whatsapp:+1987654{i:03d}",
                body=job_sample.content
            )
            webhook_data_list.append(webhook_data)
        
        # Function to send a single request
        def send_request(webhook_data):
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=webhook_data)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Send concurrent requests using ThreadPoolExecutor
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            results = list(executor.map(send_request, webhook_data_list))
        total_time = time.time() - start_time
        
        # Extract status codes and response times
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(num_concurrent * 0.95)]
        throughput = num_concurrent / total_time
        
        # Log results
        print(f"Concurrent Request Performance (n={num_concurrent}):")
        print(f"  Total Time: {total_time:.4f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Response Time: {avg_response_time:.4f}s")
        print(f"  Min Response Time: {min_response_time:.4f}s")
        print(f"  Max Response Time: {max_response_time:.4f}s")
        print(f"  P95 Response Time: {p95_response_time:.4f}s")
        
        # Assert all requests were successful
        assert all(status == 200 for status in status_codes), "Not all requests were successful"
        
        # Assert performance requirements
        assert throughput >= 5.0, f"Throughput ({throughput:.2f} req/s) below threshold (5.0 req/s)"
        assert p95_response_time < 2.0, f"P95 response time ({p95_response_time:.4f}s) exceeds threshold (2.0s)"
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_sustained_load(self, mock_twilio_service_class, mock_openai_service_class, 
                          mock_get_config, client, mock_config):
        """Test system performance under sustained load."""
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock with simulated processing time
        mock_openai_service = AsyncMock()
        
        async def delayed_analysis(*args, **kwargs):
            await asyncio.sleep(0.05)  # Simulate API processing time
            return JobAnalysisResult(
                trust_score=85,
                classification=JobClassification.LEGIT,
                reasons=["Reason 1", "Reason 2", "Reason 3"],
                confidence=0.9
            )
        
        mock_openai_service.analyze_job_ad.side_effect = delayed_analysis
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Test parameters
        num_requests = 50
        concurrency = 5
        
        # Create webhook data
        job_samples = [
            JobAdFixtures.LEGITIMATE_JOBS[0],
            JobAdFixtures.SUSPICIOUS_JOBS[0],
            JobAdFixtures.SCAM_JOBS[0]
        ]
        
        # Function to send a single request
        def send_request(i):
            job_sample = job_samples[i % len(job_samples)]
            webhook_data = WebhookDataFixtures.create_text_webhook_data(
                message_sid=f"SM{i}234567890abcdef1234567890abcdef",
                from_number=f"whatsapp:+1987654{i % 100:03d}",
                body=job_sample.content
            )
            
            start_time = time.time()
            response = client.post("/webhook/whatsapp", data=webhook_data)
            end_time = time.time()
            
            return response.status_code, end_time - start_time
        
        # Send requests in batches with specified concurrency
        all_response_times = []
        all_status_codes = []
        
        start_time = time.time()
        for batch_start in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - batch_start)
            batch_indices = range(batch_start, batch_start + batch_size)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                batch_results = list(executor.map(send_request, batch_indices))
            
            batch_status_codes = [result[0] for result in batch_results]
            batch_response_times = [result[1] for result in batch_results]
            
            all_status_codes.extend(batch_status_codes)
            all_response_times.extend(batch_response_times)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        avg_response_time = statistics.mean(all_response_times)
        max_response_time = max(all_response_times)
        min_response_time = min(all_response_times)
        p95_response_time = sorted(all_response_times)[int(num_requests * 0.95)]
        throughput = num_requests / total_time
        
        # Log results
        print(f"Sustained Load Performance (n={num_requests}, concurrency={concurrency}):")
        print(f"  Total Time: {total_time:.4f}s")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average Response Time: {avg_response_time:.4f}s")
        print(f"  Min Response Time: {min_response_time:.4f}s")
        print(f"  Max Response Time: {max_response_time:.4f}s")
        print(f"  P95 Response Time: {p95_response_time:.4f}s")
        
        # Assert all requests were successful
        assert all(status == 200 for status in all_status_codes), "Not all requests were successful"
        
        # Assert performance requirements for sustained load
        assert throughput >= 5.0, f"Throughput ({throughput:.2f} req/s) below threshold (5.0 req/s)"
        assert p95_response_time < 2.0, f"P95 response time ({p95_response_time:.4f}s) exceeds threshold (2.0s)"
        assert max_response_time < 5.0, f"Max response time ({max_response_time:.4f}s) exceeds threshold (5.0s)"


@pytest.mark.performance
class TestServicePerformance:
    """Performance tests for individual services."""
    
    @patch('app.services.openai_analysis.OpenAIAnalysisService.client')
    @pytest.mark.asyncio
    async def test_openai_service_performance(self, mock_client):
        """Test OpenAI analysis service performance."""
        from app.services.openai_analysis import OpenAIAnalysisService
        from app.models.data_models import AppConfig
        
        # Setup mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"trust_score": 85, "classification": "Legit", "reasons": ["Reason 1", "Reason 2", "Reason 3"], "confidence": 0.9}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Setup mock client
        mock_completions = AsyncMock()
        mock_completions.create.return_value = mock_response
        mock_client.chat.completions = mock_completions
        
        # Create service instance
        config = AppConfig(
            openai_api_key="test-api-key",
            twilio_account_sid="test-sid",
            twilio_auth_token="test-token",
            twilio_phone_number="+1234567890",
            openai_model="gpt-4"
        )
        service = OpenAIAnalysisService(config)
        
        # Test parameters
        num_requests = 20
        job_samples = [
            JobAdFixtures.LEGITIMATE_JOBS[0].content,
            JobAdFixtures.SUSPICIOUS_JOBS[0].content,
            JobAdFixtures.SCAM_JOBS[0].content
        ]
        
        # Measure performance for sequential requests
        start_time = time.time()
        for i in range(num_requests):
            job_text = job_samples[i % len(job_samples)]
            result = await service.analyze_job_ad(job_text)
            assert result.trust_score == 85
            assert result.classification == JobClassification.LEGIT
        
        sequential_time = time.time() - start_time
        sequential_throughput = num_requests / sequential_time
        
        # Measure performance for concurrent requests
        start_time = time.time()
        tasks = []
        for i in range(num_requests):
            job_text = job_samples[i % len(job_samples)]
            tasks.append(service.analyze_job_ad(job_text))
        
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        concurrent_throughput = num_requests / concurrent_time
        
        # Verify results
        assert len(results) == num_requests
        assert all(result.trust_score == 85 for result in results)
        assert all(result.classification == JobClassification.LEGIT for result in results)
        
        # Log results
        print(f"OpenAI Service Performance (n={num_requests}):")
        print(f"  Sequential Time: {sequential_time:.4f}s, Throughput: {sequential_throughput:.2f} req/s")
        print(f"  Concurrent Time: {concurrent_time:.4f}s, Throughput: {concurrent_throughput:.2f} req/s")
        print(f"  Speedup: {sequential_time / concurrent_time:.2f}x")
        
        # Assert performance requirements
        assert concurrent_throughput > sequential_throughput, "Concurrent processing should be faster than sequential"
        assert concurrent_throughput >= 10.0, f"Concurrent throughput ({concurrent_throughput:.2f} req/s) below threshold (10.0 req/s)"
    
    @patch('app.services.pdf_processing.httpx.AsyncClient.get')
    @patch('app.services.pdf_processing.pdfplumber.open')
    @pytest.mark.asyncio
    async def test_pdf_processing_performance(self, mock_pdf_open, mock_httpx_get):
        """Test PDF processing service performance."""
        from app.services.pdf_processing import PDFProcessingService
        from app.models.data_models import AppConfig
        from tests.fixtures.pdf_samples import PDFFixtures, PDFExtractionMocks
        
        # Setup mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4\nTest PDF content"
        mock_httpx_get.return_value = mock_response
        
        # Setup mock PDF extraction
        pdf_sample = PDFFixtures.VALID_PDF_SAMPLES[0]
        mock_pdf = PDFExtractionMocks.create_successful_extraction_mock(pdf_sample.extracted_text)
        mock_pdf_open.return_value = mock_pdf
        
        # Create service instance
        config = AppConfig(
            openai_api_key="test-api-key",
            twilio_account_sid="test-sid",
            twilio_auth_token="test-token",
            twilio_phone_number="+1234567890",
            max_pdf_size_mb=10
        )
        service = PDFProcessingService(config)
        
        # Test parameters
        num_requests = 20
        pdf_urls = [
            "https://example.com/job1.pdf",
            "https://example.com/job2.pdf",
            "https://example.com/job3.pdf"
        ]
        
        # Measure performance for sequential requests
        start_time = time.time()
        for i in range(num_requests):
            pdf_url = pdf_urls[i % len(pdf_urls)]
            text = await service.process_pdf_url(pdf_url)
            assert text == pdf_sample.extracted_text
        
        sequential_time = time.time() - start_time
        sequential_throughput = num_requests / sequential_time
        
        # Measure performance for concurrent requests
        start_time = time.time()
        tasks = []
        for i in range(num_requests):
            pdf_url = pdf_urls[i % len(pdf_urls)]
            tasks.append(service.process_pdf_url(pdf_url))
        
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        concurrent_throughput = num_requests / concurrent_time
        
        # Verify results
        assert len(results) == num_requests
        assert all(result == pdf_sample.extracted_text for result in results)
        
        # Log results
        print(f"PDF Processing Service Performance (n={num_requests}):")
        print(f"  Sequential Time: {sequential_time:.4f}s, Throughput: {sequential_throughput:.2f} req/s")
        print(f"  Concurrent Time: {concurrent_time:.4f}s, Throughput: {concurrent_throughput:.2f} req/s")
        print(f"  Speedup: {sequential_time / concurrent_time:.2f}x")
        
        # Assert performance requirements
        assert concurrent_throughput > sequential_throughput, "Concurrent processing should be faster than sequential"
        assert concurrent_throughput >= 5.0, f"Concurrent throughput ({concurrent_throughput:.2f} req/s) below threshold (5.0 req/s)"


@pytest.mark.performance
class TestMemoryUsage:
    """Tests for memory usage and resource utilization."""
    
    @patch('app.api.webhook.get_config')
    @patch('app.services.openai_analysis.OpenAIAnalysisService')
    @patch('app.services.twilio_response.TwilioResponseService')
    def test_memory_usage_under_load(self, mock_twilio_service_class, mock_openai_service_class, 
                                   mock_get_config, client, mock_config):
        """Test memory usage under load."""
        import psutil
        import os
        
        # Skip test if psutil is not available
        if not hasattr(psutil, 'Process'):
            pytest.skip("psutil not available for memory testing")
        
        # Setup configuration
        mock_get_config.return_value = mock_config
        
        # Setup OpenAI service mock
        mock_openai_service = AsyncMock()
        mock_openai_service.analyze_job_ad.return_value = JobAnalysisResult(
            trust_score=85,
            classification=JobClassification.LEGIT,
            reasons=["Reason 1", "Reason 2", "Reason 3"],
            confidence=0.9
        )
        mock_openai_service_class.return_value = mock_openai_service
        
        # Setup Twilio service mock
        mock_twilio_service = Mock()
        mock_twilio_service.send_analysis_result.return_value = True
        mock_twilio_service_class.return_value = mock_twilio_service
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Test parameters
        num_requests = 50
        
        # Create webhook data with varying content
        webhook_data_list = []
        for i in range(num_requests):
            job_sample = JobAdFixtures.LEGITIMATE_JOBS[0] if i % 3 == 0 else \
                        JobAdFixtures.SUSPICIOUS_JOBS[0] if i % 3 == 1 else \
                        JobAdFixtures.SCAM_JOBS[0]
            
            webhook_data = WebhookDataFixtures.create_text_webhook_data(
                message_sid=f"SM{i}234567890abcdef1234567890abcdef",
                from_number=f"whatsapp:+1987654{i % 100:03d}",
                body=job_sample.content
            )
            webhook_data_list.append(webhook_data)
        
        # Send requests and track memory usage
        memory_usage = []
        for i, webhook_data in enumerate(webhook_data_list):
            response = client.post("/webhook/whatsapp", data=webhook_data)
            assert response.status_code == 200
            
            # Measure memory every 10 requests
            if i % 10 == 0:
                memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_usage.append(memory)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory
        
        # Log results
        print(f"Memory Usage Test (n={num_requests}):")
        print(f"  Initial Memory: {initial_memory:.2f} MB")
        print(f"  Final Memory: {final_memory:.2f} MB")
        print(f"  Memory Increase: {memory_increase:.2f} MB")
        print(f"  Memory Usage Pattern: {memory_usage}")
        
        # Assert memory usage requirements
        # Note: These thresholds may need adjustment based on the actual application
        assert memory_increase < 100, f"Memory increase ({memory_increase:.2f} MB) exceeds threshold (100 MB)"
        
        # Check for memory leaks (continuous growth pattern)
        if len(memory_usage) >= 3:
            # Calculate differences between consecutive measurements
            diffs = [memory_usage[i+1] - memory_usage[i] for i in range(len(memory_usage)-1)]
            # Check if all differences are positive (indicating continuous growth)
            continuous_growth = all(diff > 0 for diff in diffs)
            assert not continuous_growth, "Memory usage shows continuous growth pattern, possible memory leak"


if __name__ == "__main__":
    pytest.main(["-v", __file__])