#!/usr/bin/env python3
"""
Test script for enhanced health check system.

This script tests the new health check endpoints to ensure all external APIs
are properly monitored.
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class HealthCheckTester:
    """Test the enhanced health check system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.health_endpoints = [
            "/health",
            "/health/detailed", 
            "/health/openai",
            "/health/twilio",
            "/health/database",
            "/health/redis",
            "/health/ngrok",
            "/health/external",
            "/health/metrics",
            "/health/readiness",
            "/health/liveness",
            "/health/circuit-breakers",
            "/health/alerts"
        ]
    
    async def test_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test a single health check endpoint."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                return {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status_code < 500,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "content_type": response.headers.get("content-type", ""),
                    "data": self._safe_parse_response(response)
                }
                
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "response_time_ms": 0,
                "error": str(e)
            }
    
    def _safe_parse_response(self, response) -> Any:
        """Safely parse response data."""
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return response.text[:200]
        except (json.JSONDecodeError, UnicodeDecodeError):
            return f"<unparseable content: {len(response.content)} bytes>"
    
    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all health check endpoints."""
        print("🔍 Testing enhanced health check endpoints...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        results = {}
        
        for endpoint in self.health_endpoints:
            print(f"Testing {endpoint}...")
            result = await self.test_endpoint(endpoint)
            results[endpoint] = result
            
            if result["success"]:
                print(f"✅ {endpoint}: {result['status_code']} ({result['response_time_ms']:.1f}ms)")
            else:
                print(f"❌ {endpoint}: {result.get('error', f'Status {result[\"status_code\"]}'}")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 HEALTH CHECK TEST SUMMARY")
        print("=" * 60)
        
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        print(f"Total endpoints tested: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success rate: {(successful/total)*100:.1f}%")
        
        # Show detailed results for key endpoints
        key_endpoints = ["/health", "/health/detailed", "/health/external"]
        
        print("\n🔍 Key Endpoint Details:")
        for endpoint in key_endpoints:
            if endpoint in results:
                result = results[endpoint]
                print(f"\n{endpoint}:")
                print(f"  Status: {'✅ Success' if result['success'] else '❌ Failed'}")
                print(f"  HTTP Code: {result['status_code']}")
                print(f"  Response Time: {result.get('response_time_ms', 0):.1f}ms")
                
                if result["success"] and "data" in result:
                    data = result["data"]
                    if isinstance(data, dict):
                        if "status" in data:
                            print(f"  Health Status: {data['status']}")
                        if "services" in data:
                            print(f"  Services Monitored: {list(data['services'].keys())}")
        
        # Show failed endpoints
        failed_endpoints = [ep for ep, r in results.items() if not r["success"]]
        if failed_endpoints:
            print(f"\n❌ Failed Endpoints:")
            for endpoint in failed_endpoints:
                result = results[endpoint]
                print(f"  {endpoint}: {result.get('error', f'HTTP {result[\"status_code\"]}')}")
        
        print("\n" + "=" * 60)
    
    async def test_service_specific_health(self):
        """Test individual service health endpoints."""
        print("\n🔍 Testing individual service health checks...")
        
        services = ["openai", "twilio", "database", "redis", "ngrok"]
        
        for service in services:
            endpoint = f"/health/{service}"
            result = await self.test_endpoint(endpoint)
            
            if result["success"] and isinstance(result.get("data"), dict):
                data = result["data"]
                status = data.get("status", "unknown")
                response_time = data.get("response_time_ms", 0)
                
                status_emoji = {
                    "healthy": "✅",
                    "degraded": "⚠️",
                    "unhealthy": "❌",
                    "not_configured": "⚙️",
                    "not_available": "🚫",
                    "error": "💥"
                }.get(status, "❓")
                
                print(f"{status_emoji} {service.upper()}: {status} ({response_time:.1f}ms)")
                
                if "message" in data:
                    print(f"   Message: {data['message']}")
            else:
                print(f"❌ {service.upper()}: Failed to get health status")


async def main():
    """Main test function."""
    tester = HealthCheckTester()
    
    print("🏥 Enhanced Health Check System Test")
    print("=" * 60)
    
    # Test all endpoints
    results = await tester.test_all_endpoints()
    
    # Test individual services
    await tester.test_service_specific_health()
    
    # Print summary
    tester.print_summary(results)
    
    print("\n💡 Tips:")
    print("- If ngrok shows 'not_available', that's normal for production")
    print("- If Redis shows 'unhealthy', check if Redis is running")
    print("- Check the detailed endpoint for comprehensive service status")
    print("- Use individual service endpoints for targeted monitoring")


if __name__ == "__main__":
    asyncio.run(main())