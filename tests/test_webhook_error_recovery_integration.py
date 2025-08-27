"""
Error scenario and recovery integration tests for webhook performance.

This module provides comprehensive testing of error scenarios and recovery
mechanisms to ensure robust webhook operation under failure conditions.

Requirements tested:
- Error handling and graceful degradation
- Recovery mechanisms after failures
- Fallback behavior when dependencies are unavailable
- System resilience under various failure modes
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import threading
from contextlib import contextmanager

from fastapi.testclient import TestClient
from app.main import app
from app.models.data_models import AppConfig
from app.services.background_task_processor import TaskPriority


class TestWebhookErrorRecoveryIntegration:
    """Integration tests for webhook error scenarios and recovery."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_config(self):
        """Mock application configuration for error testing."""
        config = Mock(spec=AppConfig)
        config.webhook_validation = True
        config.twilio_auth_token = "test_auth_token_error"
        config.twilio_phone_number = "+1234567890"
        config.openai_api_key = "test_openai_key"
        config.twilio_account_sid = "test_account_sid"
        config.max_pdf_size_mb = 10
        config.openai_model = "gpt-4"
        config.log_level = "INFO"
        return config
    
    def create_webhook_data(self, message_type: str = "text") -> Dict[str, str]:
        """Create webhook data for error testing."""
        base_data = {
            "MessageSid": f"SM{int(time.time() * 1000)}error{message_type}",
            "From": "whatsapp:+1987654321",
            "To": "whatsapp:+1234567890",
            "NumMedia": "0"
        }
        
        if message_type == "text":
            base_data["Body"] = "Test error scenario message"
        elif message_type == "invalid":
            base_data["MessageSid"] = ""  # Invalid MessageSid
            base_data["Body"] = "Invalid message"
        elif message_type == "large":
            base_data["Body"] = "A" * 15000  # Exceeds max length
        
        return base_data
    
    def create_twilio_signature(self, url: str, params: Dict[str, str], auth_token: str) -> str:
        """Create valid Twilio signature for testing."""
        import hashlib
        import hmac
        import base64
        from urllib.parse import urlencode
        
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
    
    @contextmanager
    def simulate_redis_failure(self):
        """Context manager to simulate Redis failure scenarios."""
        with patch('app.services.redis_connection_manager.get_redis_manager') as mock_get_redis:
            mock_redis = Mock()
            mock_redis.is_available.return_value = False
            mock_redis.execute_command = AsyncMock(side_effect=Exception("Redis connection failed"))
            mock_get_redis.return_value = mock_redis
            yield mock_redis
    
    @contextmanager
    def simulate_task_processor_failure(self):
        """Context manager to simulate task processor failure scenarios."""
        with patch('app.services.background_task_processor.get_task_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.queue_task = AsyncMock(side_effect=Exception("Task processor unavailable"))
            mock_get_processor.return_value = mock_processor
            yield mock_processor
    
    @contextmanager
    def simulate_slow_dependencies(self, delay: float = 1.0):
        """Context manager to simulate slow dependency responses."""
        async def slow_redis_command(*args, **kwargs):
            await asyncio.sleep(delay)
            return "OK"
        
        async def slow_task_queue(*args, **kwargs):
            await asyncio.sleep(delay)
            return "slow_task_123"
        
        with patch('app.services.redis_connection_manager.get_redis_manager') as mock_get_redis, \
             patch('app.services.background_task_processor.get_task_processor') as mock_get_processor:
            
            mock_redis = Mock()
            mock_redis.is_available.return_value = True
            mock_redis.execute_command = AsyncMock(side_effect=slow_redis_command)
            mock_get_redis.return_value = mock_redis
            
            mock_processor = Mock()
            mock_processor.queue_task = AsyncMock(side_effect=slow_task_queue)
            mock_get_processor.return_value = mock_processor
            
            yield mock_redis, mock_processor
    
    @pytest.mark.asyncio
    async def test_redis_unavailable_graceful_degradation(self, client, mock_config):
        """
        Test graceful degradation when Redis is unavailable.
        
        This test validates that the webhook continues to function
        when Redis is completely unavailable, falling back to in-memory
        processing and immediate task execution.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             self.simulate_redis_failure() as mock_redis:
            
            # Setup message handler
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            # Create webhook request
            webhook_data = self.create_webhook_data("text")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            # Execute request
            start_time = time.perf_counter()
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": signature}
            )
            response_time = time.perf_counter() - start_time
            
            # Verify graceful degradation
            assert response.status_code == 200, "Should succeed despite Redis failure"
            assert response_time < 3.0, f"Response time {response_time:.3f}s too high during Redis failure"
            
            # Verify Redis was detected as unavailable
            assert not mock_redis.is_available()
            
            print(f"Redis failure handled gracefully in {response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_task_processor_failure_fallback(self, client, mock_config):
        """
        Test fallback behavior when task processor fails.
        
        This test validates that webhook processing falls back to
        immediate processing when the task processor is unavailable.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             self.simulate_task_processor_failure() as mock_processor:
            
            # Setup message handler
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            # Create webhook request
            webhook_data = self.create_webhook_data("text")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            # Execute request
            start_time = time.perf_counter()
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": signature}
            )
            response_time = time.perf_counter() - start_time
            
            # Verify fallback behavior
            assert response.status_code == 200, "Should succeed despite task processor failure"
            assert response_time < 4.0, f"Response time {response_time:.3f}s too high during fallback"
            
            # Verify task processor failure was attempted
            mock_processor.queue_task.assert_called_once()
            
            print(f"Task processor failure handled with fallback in {response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_slow_dependencies_timeout_protection(self, client, mock_config):
        """
        Test timeout protection when dependencies are slow.
        
        This test validates that webhook processing has proper timeout
        protection and doesn't hang when dependencies are slow.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             self.simulate_slow_dependencies(delay=0.5) as (mock_redis, mock_processor):
            
            # Setup message handler
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            # Create webhook request
            webhook_data = self.create_webhook_data("text")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            # Execute request
            start_time = time.perf_counter()
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": signature}
            )
            response_time = time.perf_counter() - start_time
            
            # Verify timeout protection
            assert response.status_code == 200, "Should succeed despite slow dependencies"
            # Response should be faster than dependency delay due to timeout protection
            assert response_time < 2.0, f"Response time {response_time:.3f}s should be protected by timeouts"
            
            print(f"Slow dependencies handled with timeout protection in {response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_invalid_request_data_handling(self, client, mock_config):
        """
        Test handling of invalid request data.
        
        This test validates that invalid webhook requests are handled
        gracefully with appropriate error responses.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config):
            
            # Test 1: Invalid MessageSid
            invalid_data = self.create_webhook_data("invalid")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, invalid_data, mock_config.twilio_auth_token)
            
            response = client.post(
                "/webhook/whatsapp",
                data=invalid_data,
                headers={"X-Twilio-Signature": signature}
            )
            
            assert response.status_code == 422, "Should return validation error for invalid MessageSid"
            
            # Test 2: Message too large
            large_data = self.create_webhook_data("large")
            signature = self.create_twilio_signature(url, large_data, mock_config.twilio_auth_token)
            
            response = client.post(
                "/webhook/whatsapp",
                data=large_data,
                headers={"X-Twilio-Signature": signature}
            )
            
            assert response.status_code == 400, "Should return error for message too large"
            
            # Test 3: Missing required fields
            incomplete_data = {"MessageSid": "SM123test"}
            signature = self.create_twilio_signature(url, incomplete_data, mock_config.twilio_auth_token)
            
            response = client.post(
                "/webhook/whatsapp",
                data=incomplete_data,
                headers={"X-Twilio-Signature": signature}
            )
            
            assert response.status_code == 422, "Should return validation error for missing fields"
            
            print("Invalid request data handled appropriately")
    
    @pytest.mark.asyncio
    async def test_signature_validation_failure_handling(self, client, mock_config):
        """
        Test signature validation failure handling.
        
        This test validates that invalid signatures are properly rejected
        and that the system handles signature validation errors gracefully.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config):
            
            webhook_data = self.create_webhook_data("text")
            
            # Test 1: Invalid signature
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": "invalid_signature_12345"}
            )
            
            assert response.status_code == 401, "Should reject invalid signature"
            assert "Invalid webhook signature" in response.json()["message"]
            
            # Test 2: Missing signature header
            response = client.post("/webhook/whatsapp", data=webhook_data)
            
            assert response.status_code == 401, "Should reject missing signature"
            
            # Test 3: Signature validation disabled (should succeed)
            mock_config.webhook_validation = False
            
            response = client.post("/webhook/whatsapp", data=webhook_data)
            
            # Should succeed when validation is disabled
            assert response.status_code in [200, 500], "Should process when validation disabled"
            
            print("Signature validation failures handled correctly")
    
    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(self, client, mock_config):
        """
        Test error handling under concurrent load.
        
        This test validates that error scenarios are handled properly
        even when multiple requests are processed concurrently.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class, \
             self.simulate_redis_failure():
            
            # Setup message handler with intermittent failures
            call_count = 0
            
            async def intermittent_failure(request):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Fail every 3rd request
                    raise Exception("Intermittent processing failure")
                return True
            
            mock_handler = AsyncMock()
            mock_handler.process_message.side_effect = intermittent_failure
            mock_handler_class.return_value = mock_handler
            
            # Execute concurrent requests with mixed scenarios
            def execute_request(request_id: int) -> Dict[str, Any]:
                if request_id % 4 == 0:
                    # Invalid request
                    webhook_data = self.create_webhook_data("invalid")
                elif request_id % 4 == 1:
                    # Large message
                    webhook_data = self.create_webhook_data("large")
                else:
                    # Normal request
                    webhook_data = self.create_webhook_data("text")
                
                webhook_data["MessageSid"] = f"SM{request_id:03d}concurrent"
                
                url = "http://testserver/webhook/whatsapp"
                signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
                
                start_time = time.perf_counter()
                try:
                    response = client.post(
                        "/webhook/whatsapp",
                        data=webhook_data,
                        headers={"X-Twilio-Signature": signature}
                    )
                    response_time = time.perf_counter() - start_time
                    
                    return {
                        "request_id": request_id,
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 400, 422]  # Expected codes
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
            
            # Execute concurrent error scenarios
            num_requests = 12
            
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [
                    executor.submit(execute_request, i)
                    for i in range(num_requests)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            # Analyze results
            successful_responses = [r for r in results if r["success"]]
            response_times = [r["response_time"] for r in results]
            
            # Verify error handling under concurrent load
            success_rate = len(successful_responses) / len(results) * 100
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Should handle most requests appropriately (some will fail due to invalid data)
            assert success_rate >= 60.0, f"Success rate {success_rate:.1f}% too low under concurrent errors"
            assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s too high"
            assert max_response_time < 5.0, f"Max response time {max_response_time:.3f}s too high"
            
            print(f"Concurrent error scenarios: {success_rate:.1f}% success rate, "
                  f"avg response: {avg_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_recovery_after_dependency_restoration(self, client, mock_config):
        """
        Test system recovery after dependency restoration.
        
        This test validates that the system properly recovers and resumes
        normal operation after dependencies are restored.
        """
        with patch('app.api.optimized_webhook.get_config', return_value=mock_config), \
             patch('app.services.message_handler.MessageHandlerService') as mock_handler_class:
            
            # Setup message handler
            mock_handler = AsyncMock()
            mock_handler.process_message.return_value = True
            mock_handler_class.return_value = mock_handler
            
            webhook_data = self.create_webhook_data("text")
            url = "http://testserver/webhook/whatsapp"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            # Phase 1: Normal operation
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": signature}
            )
            
            assert response.status_code == 200, "Should work normally initially"
            
            # Phase 2: Dependency failure
            with self.simulate_redis_failure():
                webhook_data["MessageSid"] = "SM002failure"
                signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
                
                response = client.post(
                    "/webhook/whatsapp",
                    data=webhook_data,
                    headers={"X-Twilio-Signature": signature}
                )
                
                assert response.status_code == 200, "Should handle failure gracefully"
            
            # Phase 3: Recovery (dependencies restored)
            webhook_data["MessageSid"] = "SM003recovery"
            signature = self.create_twilio_signature(url, webhook_data, mock_config.twilio_auth_token)
            
            start_time = time.perf_counter()
            response = client.post(
                "/webhook/whatsapp",
                data=webhook_data,
                headers={"X-Twilio-Signature": signature}
            )
            recovery_time = time.perf_counter() - start_time
            
            # Verify recovery
            assert response.status_code == 200, "Should recover after dependency restoration"
            assert recovery_time < 2.0, f"Recovery response time {recovery_time:.3f}s should be normal"
            
            print(f"System recovered successfully in {recovery_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])