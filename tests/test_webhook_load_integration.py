"""
Load testing integration tests for webhook performance.

This module provides comprehensive load testing for webhook performance
under various stress conditions and concurrent load scenarios.

Requirements tested:
- 2.1: Webhook response times under load
- 2.2: Performance under concurrent requests
- 3.1: Task queuing under high load
- 4.1: Performance monitoring under stress
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass

from fastapi.testclient import TestClient
from app.main import app
from app.models.data_models import AppConfig


@dataclass
class LoadTestResult:
    """Result of a load test execution."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float


class TestWebhookLoadIntegration:
    """Load testing integration tests for webhook performance."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_config(self):
        """Mock application configuration for load testing."""
        config = Mock(spec=AppConfig)
        config.webhook_validation = False  # Disable for load testing
        config.twilio_auth_token = "test_auth_token_load"
        config.twilio_phone_number = "+1234567890"
        config.openai_api_key = "test_openai_key"
        config.twilio_account_sid = "test_account_sid"
        config.max_pdf_size_mb = 10
        config.openai_model = "gpt-4"
        config.log_level = "WARNING"  # Reduce logging overhead
        return config
    
    def create_load_test_data(self, request_id: int) -> Dict[str, str]:
        """Create webhook data for load testing."""
        return {
            "MessageSid": f"SM{request_id:06d}load{int(time.time())}",
            "From": f"whatsapp:+198765432{request_id % 10}",
            "To": "whatsapp:+1234567890",
            "Body": f"Load test message {request_id} - Software Engineer position",
            "NumMedia": "0"
        }
    
    def execute_single_request(self, client: TestClient, request_id: int) -> Dict[str, Any]:
        """Execute a single webhook request and measure performance."""
        webhook_data = self.create_load_test_data(request_id)
        
        start_time = time.perf_counter()
        try:
            response = client.post("/webhook/whatsapp", data=webhook_data)
            response_time = time.perf_counter() - start_time
            
            return {
                "request_id": request_id,
                "response_time": response_time,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "error": None
            }
        except Exception as e:
            response_time = time.perf_counter() - start_time
            return {
                "request_id": request_id,
                "response_time": response_time,
                "status_code": 500,
                "success": False,
                "error": str(e)
            }
    
    def analyze_load_test_results(self, results: List[Dict[str, Any]], 
                                 total_time: float) -> LoadTestResult:
        """Analyze load test results and calculate performance metrics."""
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = total_requests - successful_requests
        
        response_times = [r["response_time"] for r in results if r["success"]]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p95_response_time = p99_response_time = 0.0
        
        throughput = total_requests / total_time if total_time > 0 else 0.0
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0.0
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate
        )
    
    @pytest.mark.asyncio
    async def test_moderate_concurrent_load(self, client, mock_config):
        """
        Test webhook performance under moderate concurrent load.
        
        This test validates performance with 20 concurrent requests
        to ensure the system handles typical load scenarios.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             patch('app.services.background_task_processor.get_task_processor') as mock_get_processor:
            
            # Setup fast mocks
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            mock_processor = Mock()
            mock_processor.queue_task = AsyncMock(return_value="load_task")
            mock_get_processor.return_value = mock_processor
            
            # Execute moderate load test
            num_requests = 20
            max_workers = 10
            
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.execute_single_request, client, i)
                    for i in range(num_requests)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.perf_counter() - start_time
            
            # Analyze results
            load_result = self.analyze_load_test_results(results, total_time)
            
            # Verify performance requirements
            assert load_result.successful_requests == num_requests, \
                f"Only {load_result.successful_requests}/{num_requests} requests succeeded"
            
            assert load_result.error_rate == 0.0, f"Error rate {load_result.error_rate}% too high"
            
            # Performance requirements under moderate load
            assert load_result.avg_response_time < 1.0, \
                f"Average response time {load_result.avg_response_time:.3f}s too high"
            
            assert load_result.p95_response_time < 2.0, \
                f"95th percentile response time {load_result.p95_response_time:.3f}s too high"
            
            assert load_result.throughput > 10.0, \
                f"Throughput {load_result.throughput:.1f} req/s too low"
            
            # Print results
            print(f"Moderate Load Test Results:")
            print(f"  Requests: {load_result.total_requests}")
            print(f"  Success Rate: {100 - load_result.error_rate:.1f}%")
            print(f"  Avg Response Time: {load_result.avg_response_time:.3f}s")
            print(f"  95th Percentile: {load_result.p95_response_time:.3f}s")
            print(f"  Throughput: {load_result.throughput:.1f} req/s")
    
    @pytest.mark.asyncio
    async def test_high_concurrent_load(self, client, mock_config):
        """
        Test webhook performance under high concurrent load.
        
        This test validates performance with 50 concurrent requests
        to test system limits and stress handling.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             patch('app.services.background_task_processor.get_task_processor') as mock_get_processor:
            
            # Setup fast mocks
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            mock_processor = Mock()
            mock_processor.queue_task = AsyncMock(return_value="high_load_task")
            mock_get_processor.return_value = mock_processor
            
            # Execute high load test
            num_requests = 50
            max_workers = 20
            
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.execute_single_request, client, i)
                    for i in range(num_requests)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.perf_counter() - start_time
            
            # Analyze results
            load_result = self.analyze_load_test_results(results, total_time)
            
            # Verify performance requirements (more lenient under high load)
            success_rate = (load_result.successful_requests / load_result.total_requests) * 100
            assert success_rate >= 95.0, f"Success rate {success_rate:.1f}% too low under high load"
            
            assert load_result.error_rate <= 5.0, f"Error rate {load_result.error_rate}% too high"
            
            # Performance requirements under high load (more lenient)
            assert load_result.avg_response_time < 2.0, \
                f"Average response time {load_result.avg_response_time:.3f}s too high under load"
            
            assert load_result.p95_response_time < 4.0, \
                f"95th percentile response time {load_result.p95_response_time:.3f}s too high under load"
            
            assert load_result.throughput > 8.0, \
                f"Throughput {load_result.throughput:.1f} req/s too low under high load"
            
            # Print results
            print(f"High Load Test Results:")
            print(f"  Requests: {load_result.total_requests}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Avg Response Time: {load_result.avg_response_time:.3f}s")
            print(f"  95th Percentile: {load_result.p95_response_time:.3f}s")
            print(f"  99th Percentile: {load_result.p99_response_time:.3f}s")
            print(f"  Throughput: {load_result.throughput:.1f} req/s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])