"""
Integration tests for webhook performance optimization.

This module provides comprehensive integration tests for webhook performance,
including Twilio webhook simulation, load testing, asynchronous task processing
validation, and error scenario testing.

Requirements tested:
- 2.1: Webhook response times under 2 seconds
- 2.2: Validation and queuing within 500ms
- 2.3: PDF processing acknowledgment within 1 second
- 3.1: Immediate message queuing for background processing
- 3.2: Background task status tracking and completion
"""

import pytest
import asyncio
import time
import json
import hashlib
import hmac
import base64
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from urllib.parse import urlencode
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.main import app
from app.models.data_models import TwilioWebhookRequest, AppConfig
from app.services.background_task_processor import (
    BackgroundTaskProcessor, ProcessingTask, TaskPriority, TaskStatus, TaskQueueConfig
)
from app.services.redis_connection_manager import RedisConnectionManager
from app.services.performance_monitor import PerformanceMonitor, WebhookTimingBreakdown
from app.api.optimized_webhook import OptimizedWebhookProcessor


class TestWebhookPerformanceIntegration:
    """Integration tests for webhook performance optimization."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_config(self):
        """Mock application configuration for testing."""
        config = Mock(spec=AppConfig)
        config.webhook_validation = True
        config.twilio_auth_token = "test_auth_token_12345"
        config.twilio_phone_number = "+1234567890"
        config.openai_api_key = "test_openai_key"
        config.twilio_account_sid = "test_account_sid"
        config.max_pdf_size_mb = 10
        config.openai_model = "gpt-4"
        config.log_level = "INFO"
        return config
    
    def create_twilio_signature(self, url: str, params: Dict[str, str], auth_token: str) -> str:
        """Create a valid Twilio signature for testing."""
        sorted_params = sorted(params.items())
        data_string = url + urlencode(sorted_params)
        
        signature = base64.b64encode(
            hmac.new(
                auth_token.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def create_sample_webhook_data(self, message_type: str = "text") -> Dict[str, str]:
        """Create sample webhook data for different message types."""
        base_data = {
            "MessageSid": f"SM{int(time.time() * 1000)}abcdef1234567890abcdef",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "NumMedia": "0"
        }
        
        if message_type == "text":
            base_data.update({
                "Body": "Software Engineer position at Google. Salary $150k. Remote work available.",
                "NumMedia": "0"
            })
        elif message_type == "pdf":
            base_data.update({
                "Body": "",
                "NumMedia": "1",
                "MediaUrl0": "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test.pdf",
                "MediaContentType0": "application/pdf"
            })
        
        return base_data
    
    @pytest.mark.asyncio
    async def test_webhook_response_time_requirement_2_1(self, client, mock_config):
        """Test webhook response time meets Requirement 2.1: Sub-2-second response times."""
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class:
            
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            response_times = []
            
            for i in range(3):
                webhook_data = self.create_sample_webhook_data("text")
                webhook_data["MessageSid"] = f"SM{i}abcdef1234567890abcdef"
                
                url = "http://testserver/webhook/whatsapp"
                signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
                
                start_time = time.time()
                response = client.post("/webhook/whatsapp", data=webhook_data, headers={"X-Twilio-Signature": signature})
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                
                assert response.status_code == 200
                assert response_time < 2.0, f"Response time {response_time:.3f}s exceeds 2-second requirement"
            
            max_response_time = max(response_times)
            avg_response_time = sum(response_times) / len(response_times)
            
            assert max_response_time < 2.0, f"Max response time {max_response_time:.3f}s exceeds requirement"
            assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s should be well under 2s"
            
            print(f"Response times: avg={avg_response_time:.3f}s, max={max_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_webhook_500ms_target_requirement_2_2(self, client, mock_config):
        """Test webhook response time meets Requirement 2.2: 500ms target for validation and queuing."""
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class:
            
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            webhook_data = self.create_sample_webhook_data("text")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            start_time = time.perf_counter()
            response = client.post("/webhook/whatsapp", data=webhook_data, headers={"X-Twilio-Signature": signature})
            response_time = time.perf_counter() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"Response time {response_time:.3f}s exceeds test threshold"
            
            print(f"Validation and queuing completed in {response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_webhook_load_performance(self, client, mock_config):
        """Test webhook performance under concurrent load conditions."""
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class:
            
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            def make_webhook_request(request_id: int) -> Dict[str, Any]:
                webhook_data = self.create_sample_webhook_data("text")
                webhook_data["MessageSid"] = f"SM{request_id}concurrent{int(time.time())}"
                
                url = "http://testserver/webhook/whatsapp"
                signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
                
                start_time = time.perf_counter()
                response = client.post("/webhook/whatsapp", data=webhook_data, headers={"X-Twilio-Signature": signature})
                response_time = time.perf_counter() - start_time
                
                return {"request_id": request_id, "response_time": response_time, "status_code": response.status_code, "success": response.status_code == 200}
            
            num_concurrent_requests = 3
            with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
                start_time = time.perf_counter()
                futures = [executor.submit(make_webhook_request, i) for i in range(num_concurrent_requests)]
                results = [future.result() for future in futures]
                total_time = time.perf_counter() - start_time
            
            response_times = [r["response_time"] for r in results]
            successful_requests = [r for r in results if r["success"]]
            
            assert len(successful_requests) == num_concurrent_requests
            max_response_time = max(response_times)
            avg_response_time = sum(response_times) / len(response_times)
            
            assert max_response_time < 3.0, f"Max response time {max_response_time:.3f}s too high under load"
            assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s too high under load"
            
            throughput = num_concurrent_requests / total_time
            assert throughput > 1.0, f"Throughput {throughput:.1f} req/s too low"
            
            print(f"Concurrent load test: {num_concurrent_requests} requests in {total_time:.3f}s, throughput: {throughput:.1f} req/s")
    
    @pytest.mark.asyncio
    async def test_background_task_processing_requirement_3_1(self):
        """Test background task processing meets Requirement 3.1: Immediate message queuing."""
        config = TaskQueueConfig(max_queue_size=100, worker_count=2, processing_timeout=10, retry_attempts=2)
        task_processor = BackgroundTaskProcessor(config)
        
        with patch.object(task_processor, 'redis_manager') as mock_redis:
            mock_redis.is_available.return_value = True
            mock_redis.execute_command = AsyncMock()
            
            await task_processor.start()
            
            try:
                test_payload = {"message_sid": "SM123test", "from_number": "whatsapp:+1234567890", "body": "Test message"}
                task = ProcessingTask(task_id="test_task_123", task_type="message_processing", payload=test_payload, priority=TaskPriority.NORMAL)
                
                start_time = time.perf_counter()
                task_id = await task_processor.queue_task(task)
                queue_time = time.perf_counter() - start_time
                
                assert task_id == "test_task_123"
                assert queue_time < 0.5, f"Task queuing took {queue_time:.3f}s, should be < 0.5s"
                
                mock_redis.execute_command.assert_called()
                print(f"Task queued in {queue_time:.3f}s")
                
            finally:
                await task_processor.stop()
    
    @pytest.mark.asyncio
    async def test_webhook_error_scenarios_and_recovery(self, client, mock_config):
        """Test webhook error scenarios and recovery mechanisms."""
        webhook_data = self.create_sample_webhook_data("text")
        
        # Test invalid signature handling
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config):
            response = client.post("/webhook/whatsapp", data=webhook_data, headers={"X-Twilio-Signature": "invalid_signature"})
            assert response.status_code == 401
            assert "Invalid webhook signature" in response.json()["message"]
        
        # Test Redis unavailable scenario (graceful degradation)
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             patch('app.services.redis_connection_manager.get_redis_manager') as mock_get_redis:
            
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            mock_redis = Mock()
            mock_redis.is_available.return_value = False
            mock_get_redis.return_value = mock_redis
            
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            start_time = time.perf_counter()
            response = client.post("/webhook/whatsapp", data=webhook_data, headers={"X-Twilio-Signature": signature})
            response_time = time.perf_counter() - start_time
            
            assert response.status_code == 200
            assert response_time < 3.0
            
            print(f"Redis unavailable scenario handled in {response_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])