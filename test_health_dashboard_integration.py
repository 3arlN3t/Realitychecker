#!/usr/bin/env python3
"""
Integration test for Health Check Dashboard API integration.

This script tests the integration between the health check API endpoints
and the dashboard frontend to ensure proper data flow and formatting.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

import httpx
import pytest


class HealthDashboardIntegrationTester:
    """Test the health check API integration with the dashboard."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_basic_health_endpoint(self) -> Dict[str, Any]:
        """Test the basic health check endpoint."""
        print("🔍 Testing basic health endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            # Validate required fields
            required_fields = ["status", "timestamp", "service", "version"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            assert data["status"] == "healthy", f"Expected healthy status, got {data['status']}"
            assert data["service"] == "reality-checker-whatsapp-bot"
            
            print(f"✅ Basic health check passed: {data['status']}")
            return data
            
        except Exception as e:
            print(f"❌ Basic health check failed: {e}")
            raise
    
    async def test_detailed_health_endpoint(self) -> Dict[str, Any]:
        """Test the detailed health check endpoint."""
        print("🔍 Testing detailed health endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/detailed")
            
            # Accept both 200 (healthy) and 503 (degraded/unhealthy) as valid responses
            assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"
            
            data = response.json()
            
            # Validate required fields for dashboard integration
            required_fields = [
                "status", "timestamp", "service", "version", 
                "health_check_duration_ms", "services", "metrics", "configuration"
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Validate services structure (required for dashboard)
            services = data["services"]
            required_services = ["openai", "twilio", "pdf_processing"]
            for service in required_services:
                assert service in services, f"Missing service: {service}"
                
                service_data = services[service]
                service_required_fields = ["status", "message", "response_time_ms"]
                for field in service_required_fields:
                    assert field in service_data, f"Missing field {field} in service {service}"
            
            # Validate metrics structure
            metrics = data["metrics"]
            assert "requests" in metrics, "Missing requests metrics"
            assert "services" in metrics, "Missing services metrics"
            
            # Validate configuration structure
            config = data["configuration"]
            config_required_fields = ["openai_model", "max_pdf_size_mb", "log_level", "webhook_validation"]
            for field in config_required_fields:
                assert field in config, f"Missing configuration field: {field}"
            
            print(f"✅ Detailed health check passed: {data['status']}")
            print(f"   Services: {list(services.keys())}")
            print(f"   Overall status: {data['status']}")
            print(f"   Response time: {data['health_check_duration_ms']}ms")
            
            return data
            
        except Exception as e:
            print(f"❌ Detailed health check failed: {e}")
            raise
    
    async def test_metrics_endpoint(self) -> Dict[str, Any]:
        """Test the metrics endpoint."""
        print("🔍 Testing metrics endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/metrics")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            # Validate metrics structure for dashboard
            assert "requests" in data or "services" in data, "Missing metrics data"
            
            print(f"✅ Metrics endpoint passed")
            return data
            
        except Exception as e:
            print(f"❌ Metrics endpoint failed: {e}")
            raise
    
    async def test_readiness_endpoint(self) -> Dict[str, Any]:
        """Test the readiness endpoint."""
        print("🔍 Testing readiness endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/readiness")
            
            # Accept both 200 (ready) and 503 (not ready) as valid responses
            assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"
            
            data = response.json()
            
            required_fields = ["ready", "timestamp", "message"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            print(f"✅ Readiness check passed: ready={data['ready']}")
            return data
            
        except Exception as e:
            print(f"❌ Readiness check failed: {e}")
            raise
    
    async def test_liveness_endpoint(self) -> Dict[str, Any]:
        """Test the liveness endpoint."""
        print("🔍 Testing liveness endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/liveness")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            required_fields = ["alive", "timestamp", "message"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            assert data["alive"] is True, "Application should be alive"
            
            print(f"✅ Liveness check passed: alive={data['alive']}")
            return data
            
        except Exception as e:
            print(f"❌ Liveness check failed: {e}")
            raise
    
    async def test_circuit_breakers_endpoint(self) -> Dict[str, Any]:
        """Test the circuit breakers endpoint."""
        print("🔍 Testing circuit breakers endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/circuit-breakers")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            required_fields = ["timestamp", "circuit_breakers"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            print(f"✅ Circuit breakers endpoint passed")
            return data
            
        except Exception as e:
            print(f"❌ Circuit breakers endpoint failed: {e}")
            raise
    
    async def test_alerts_endpoint(self) -> Dict[str, Any]:
        """Test the alerts endpoint."""
        print("🔍 Testing alerts endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health/alerts")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            required_fields = ["timestamp", "active_alerts", "alert_count"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            assert isinstance(data["active_alerts"], list), "active_alerts should be a list"
            assert isinstance(data["alert_count"], int), "alert_count should be an integer"
            
            print(f"✅ Alerts endpoint passed: {data['alert_count']} active alerts")
            return data
            
        except Exception as e:
            print(f"❌ Alerts endpoint failed: {e}")
            raise
    
    async def test_dashboard_data_transformation(self, detailed_health: Dict[str, Any]) -> None:
        """Test that the health data can be properly transformed for dashboard use."""
        print("🔍 Testing dashboard data transformation...")
        
        try:
            # Simulate the transformation that would happen in the dashboard
            services = detailed_health["services"]
            
            # Test service status mapping
            for service_name, service_data in services.items():
                status = service_data["status"]
                response_time = service_data["response_time_ms"]
                
                # Map API status to dashboard status
                dashboard_status = self._map_status_for_dashboard(status)
                assert dashboard_status in ["healthy", "warning", "critical", "unknown"]
                
                # Validate response time is numeric
                assert isinstance(response_time, (int, float)), f"Response time should be numeric for {service_name}"
                assert response_time >= 0, f"Response time should be non-negative for {service_name}"
            
            # Test overall health calculation
            overall_status = detailed_health["status"]
            dashboard_overall = self._map_status_for_dashboard(overall_status)
            assert dashboard_overall in ["healthy", "warning", "critical", "unknown"]
            
            # Test uptime calculation
            healthy_services = sum(1 for s in services.values() if s["status"] in ["healthy", "not_configured"])
            total_services = len(services)
            uptime_percentage = (healthy_services / total_services * 100) if total_services > 0 else 0
            
            assert 0 <= uptime_percentage <= 100, "Uptime percentage should be between 0 and 100"
            
            print(f"✅ Dashboard transformation passed:")
            print(f"   Overall status: {overall_status} -> {dashboard_overall}")
            print(f"   Healthy services: {healthy_services}/{total_services}")
            print(f"   Calculated uptime: {uptime_percentage:.1f}%")
            
        except Exception as e:
            print(f"❌ Dashboard transformation failed: {e}")
            raise
    
    def _map_status_for_dashboard(self, api_status: str) -> str:
        """Map API status to dashboard status."""
        status_mapping = {
            "healthy": "healthy",
            "degraded": "warning",
            "unhealthy": "critical",
            "not_configured": "warning",
            "circuit_open": "warning",
            "error": "critical"
        }
        return status_mapping.get(api_status, "unknown")
    
    async def test_performance_requirements(self) -> None:
        """Test that health endpoints meet performance requirements."""
        print("🔍 Testing performance requirements...")
        
        try:
            # Test basic health endpoint performance
            start_time = time.time()
            await self.client.get(f"{self.base_url}/health")
            basic_duration = (time.time() - start_time) * 1000
            
            assert basic_duration < 1000, f"Basic health check too slow: {basic_duration:.2f}ms"
            
            # Test detailed health endpoint performance
            start_time = time.time()
            await self.client.get(f"{self.base_url}/health/detailed")
            detailed_duration = (time.time() - start_time) * 1000
            
            assert detailed_duration < 5000, f"Detailed health check too slow: {detailed_duration:.2f}ms"
            
            print(f"✅ Performance requirements met:")
            print(f"   Basic health: {basic_duration:.2f}ms")
            print(f"   Detailed health: {detailed_duration:.2f}ms")
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            raise
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("🚀 Starting Health Dashboard Integration Tests")
        print("=" * 60)
        
        results = {}
        
        try:
            # Test all endpoints
            results["basic_health"] = await self.test_basic_health_endpoint()
            results["detailed_health"] = await self.test_detailed_health_endpoint()
            results["metrics"] = await self.test_metrics_endpoint()
            results["readiness"] = await self.test_readiness_endpoint()
            results["liveness"] = await self.test_liveness_endpoint()
            results["circuit_breakers"] = await self.test_circuit_breakers_endpoint()
            results["alerts"] = await self.test_alerts_endpoint()
            
            # Test dashboard integration
            await self.test_dashboard_data_transformation(results["detailed_health"])
            
            # Test performance
            await self.test_performance_requirements()
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED - Health Dashboard Integration is working correctly!")
            print("\nSummary:")
            print(f"   API Status: {results['detailed_health']['status']}")
            print(f"   Services: {len(results['detailed_health']['services'])}")
            print(f"   Response Time: {results['detailed_health']['health_check_duration_ms']}ms")
            print(f"   Active Alerts: {results['alerts']['alert_count']}")
            
            return results
            
        except Exception as e:
            print(f"\n❌ INTEGRATION TEST FAILED: {e}")
            raise


async def main():
    """Main test runner."""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Testing Health Dashboard Integration at: {base_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    async with HealthDashboardIntegrationTester(base_url) as tester:
        try:
            results = await tester.run_all_tests()
            
            # Save results for analysis
            with open("health_dashboard_integration_results.json", "w") as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n📊 Results saved to: health_dashboard_integration_results.json")
            
        except Exception as e:
            print(f"\n💥 Test suite failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())