#!/usr/bin/env python3
"""
Test script for webhook optimization performance.

This script tests the optimized webhook handler to ensure it meets the
sub-2-second response time requirements.
"""

import asyncio
import time
import json
import hmac
import hashlib
import base64
from urllib.parse import urlencode
from typing import Dict, Any

import httpx
import pytest


class WebhookPerformanceTester:
    """Test class for webhook performance validation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.webhook_url = f"{base_url}/webhook/whatsapp"
        self.test_auth_token = "test_auth_token_for_signature"
    
    def create_twilio_signature(self, url: str, params: Dict[str, str]) -> str:
        """Create a valid Twilio signature for testing."""
        # Sort parameters and create data string
        sorted_params = sorted(params.items())
        data_string = url + urlencode(sorted_params)
        
        # Create HMAC-SHA1 signature
        signature = base64.b64encode(
            hmac.new(
                self.test_auth_token.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    async def test_webhook_response_time(self, message_type: str = "text") -> Dict[str, Any]:
        """Test webhook response time for different message types."""
        
        # Prepare test data
        if message_type == "text":
            form_data = {
                "MessageSid": "SM1234567890abcdef1234567890abcdef",
                "From": "whatsapp:+1234567890",
                "To": "whatsapp:+0987654321",
                "Body": "This is a test message for performance testing. It contains enough text to trigger analysis.",
                "NumMedia": "0"
            }
        elif message_type == "pdf":
            form_data = {
                "MessageSid": "SM1234567890abcdef1234567890abcdef",
                "From": "whatsapp:+1234567890",
                "To": "whatsapp:+0987654321",
                "Body": "",
                "NumMedia": "1",
                "MediaUrl0": "https://api.twilio.com/test/media/pdf",
                "MediaContentType0": "application/pdf"
            }
        else:
            raise ValueError(f"Unknown message type: {message_type}")
        
        # Create signature
        signature = self.create_twilio_signature(self.webhook_url, form_data)
        
        headers = {
            "X-Twilio-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Measure response time
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    data=form_data,
                    headers=headers
                )
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "response_time_ms": response_time * 1000,
                "status_code": response.status_code,
                "message_type": message_type,
                "within_500ms": response_time <= 0.5,
                "within_2s": response_time <= 2.0,
                "response_headers": dict(response.headers)
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time_ms": response_time * 1000,
                "error": str(e),
                "message_type": message_type,
                "within_500ms": response_time <= 0.5,
                "within_2s": response_time <= 2.0
            }
    
    async def test_concurrent_requests(self, num_requests: int = 10) -> Dict[str, Any]:
        """Test webhook performance under concurrent load."""
        
        tasks = []
        for i in range(num_requests):
            message_type = "pdf" if i % 3 == 0 else "text"  # Mix of message types
            tasks.append(self.test_webhook_response_time(message_type))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        response_times = [r["response_time_ms"] for r in successful_requests]
        within_500ms = sum(1 for r in successful_requests if r["within_500ms"])
        within_2s = sum(1 for r in successful_requests if r["within_2s"])
        
        return {
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "exceptions": len(exceptions),
            "total_time_s": total_time,
            "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "within_500ms_count": within_500ms,
            "within_500ms_percentage": (within_500ms / len(successful_requests) * 100) if successful_requests else 0,
            "within_2s_count": within_2s,
            "within_2s_percentage": (within_2s / len(successful_requests) * 100) if successful_requests else 0,
            "requests_per_second": num_requests / total_time if total_time > 0 else 0
        }
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance tests."""
        print("🚀 Starting webhook performance tests...")
        
        results = {}
        
        # Test 1: Single text message
        print("📝 Testing single text message...")
        results["single_text"] = await self.test_webhook_response_time("text")
        
        # Test 2: Single PDF message
        print("📄 Testing single PDF message...")
        results["single_pdf"] = await self.test_webhook_response_time("pdf")
        
        # Test 3: Concurrent requests
        print("🔄 Testing concurrent requests...")
        results["concurrent_10"] = await self.test_concurrent_requests(10)
        
        # Test 4: Higher concurrency
        print("⚡ Testing higher concurrency...")
        results["concurrent_20"] = await self.test_concurrent_requests(20)
        
        return results


async def main():
    """Main test function."""
    tester = WebhookPerformanceTester()
    
    try:
        # Check if server is running
        async with httpx.AsyncClient() as client:
            health_response = await client.get(f"{tester.base_url}/health")
            if health_response.status_code != 200:
                print(f"❌ Server health check failed: {health_response.status_code}")
                return
        
        print("✅ Server is running, starting performance tests...")
        
        # Run performance tests
        results = await tester.run_performance_tests()
        
        # Print results
        print("\n" + "="*60)
        print("📊 WEBHOOK PERFORMANCE TEST RESULTS")
        print("="*60)
        
        # Single message tests
        for test_name, result in [("single_text", results["single_text"]), ("single_pdf", results["single_pdf"])]:
            print(f"\n{test_name.upper()} MESSAGE:")
            if result["success"]:
                print(f"  ✅ Response time: {result['response_time_ms']:.1f}ms")
                print(f"  ✅ Status code: {result['status_code']}")
                print(f"  {'✅' if result['within_500ms'] else '❌'} Within 500ms target: {result['within_500ms']}")
                print(f"  {'✅' if result['within_2s'] else '❌'} Within 2s requirement: {result['within_2s']}")
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Concurrent tests
        for test_name, result in [("concurrent_10", results["concurrent_10"]), ("concurrent_20", results["concurrent_20"])]:
            print(f"\n{test_name.upper().replace('_', ' ')} REQUESTS:")
            print(f"  📈 Successful: {result['successful_requests']}/{result['total_requests']}")
            print(f"  ⏱️  Average response time: {result['avg_response_time_ms']:.1f}ms")
            print(f"  ⏱️  Max response time: {result['max_response_time_ms']:.1f}ms")
            print(f"  ⏱️  Min response time: {result['min_response_time_ms']:.1f}ms")
            print(f"  🎯 Within 500ms: {result['within_500ms_count']}/{result['successful_requests']} ({result['within_500ms_percentage']:.1f}%)")
            print(f"  🎯 Within 2s: {result['within_2s_count']}/{result['successful_requests']} ({result['within_2s_percentage']:.1f}%)")
            print(f"  🚀 Throughput: {result['requests_per_second']:.1f} req/s")
        
        # Overall assessment
        print("\n" + "="*60)
        print("📋 REQUIREMENTS ASSESSMENT")
        print("="*60)
        
        # Check Requirement 2.1: Sub-2-second response times
        all_within_2s = all(
            results[test]["within_2s"] if "within_2s" in results[test] 
            else results[test]["within_2s_percentage"] == 100.0
            for test in ["single_text", "single_pdf", "concurrent_10", "concurrent_20"]
        )
        print(f"  {'✅' if all_within_2s else '❌'} Requirement 2.1: Sub-2-second response times")
        
        # Check Requirement 2.2: 500ms target for validation and queuing
        most_within_500ms = (
            results["concurrent_10"]["within_500ms_percentage"] >= 80 and
            results["concurrent_20"]["within_500ms_percentage"] >= 70
        )
        print(f"  {'✅' if most_within_500ms else '❌'} Requirement 2.2: 500ms target (80%+ success rate)")
        
        # Check overall performance
        avg_response_time = (
            results["concurrent_10"]["avg_response_time_ms"] + 
            results["concurrent_20"]["avg_response_time_ms"]
        ) / 2
        print(f"  {'✅' if avg_response_time <= 1000 else '❌'} Overall performance: {avg_response_time:.1f}ms average")
        
        print("\n🎉 Performance testing completed!")
        
        # Save results to file
        with open("webhook_performance_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("📁 Results saved to webhook_performance_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())