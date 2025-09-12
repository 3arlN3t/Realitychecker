#!/usr/bin/env python3
"""
Test script for the unified dashboard to verify it's working correctly.
"""

import asyncio
import os
from typing import Any, Dict

import aiohttp

# Configuration
BASE_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000")
EXPECTED_HTML_CONTENT = ["Admin Dashboard", "Performance Metrics"]


async def test_html_endpoint(session: aiohttp.ClientSession, url: str, test_name: str, expected_content: list) -> bool:
    """Test HTML endpoint for expected content."""
    print(f"\n{test_name}...")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                if all(text in content for text in expected_content):
                    print("✅ Dashboard HTML loads correctly")
                    return True
                else:
                    print("❌ Dashboard HTML missing expected content")
                    return False
            else:
                print(f"❌ Dashboard HTML failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Dashboard HTML error: {e}")
        return False


async def test_json_endpoint(session: aiohttp.ClientSession, url: str, test_name: str) -> Dict[str, Any]:
    """Test JSON API endpoint and return data."""
    print(f"\n{test_name}...")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ API endpoint working")
                return data
            else:
                error_text = await response.text()
                print(f"❌ API failed: {response.status}")
                print(f"   Error: {error_text}")
                return {}
    except Exception as e:
        print(f"❌ API error: {e}")
        return {}


def print_health_data(data: Dict[str, Any]) -> None:
    """Print health check data in a formatted way."""
    print(f"   - Status: {data.get('status', 'unknown')}")


def print_overview_data(data: Dict[str, Any]) -> None:
    """Print dashboard overview data in a formatted way."""
    if data:
        print(f"   - Total requests: {data.get('total_requests', 'N/A')}")
        print(f"   - Active users: {data.get('active_users', 'N/A')}")
        print(f"   - Error rate: {data.get('error_rate', 'N/A')}%")
        print(f"   - System health: {data.get('system_health', 'N/A')}")


def print_detailed_health_data(data: Dict[str, Any]) -> None:
    """Print detailed health data in a formatted way."""
    if data:
        print(f"   - Overall status: {data.get('status', 'N/A')}")
        services = data.get('services', {})
        for service, info in services.items():
            status = info.get('status', 'unknown') if isinstance(info, dict) else info
            print(f"   - {service}: {status}")


def print_metrics_data(data: Dict[str, Any]) -> None:
    """Print real-time metrics data in a formatted way."""
    if data:
        print(f"   - Active requests: {data.get('active_requests', 'N/A')}")
        print(f"   - Memory usage: {data.get('memory_usage', 'N/A')}%")
        print(f"   - CPU usage: {data.get('cpu_usage', 'N/A')}%")


async def test_dashboard_endpoints():
    """Test all the endpoints that the unified dashboard uses."""
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Unified Dashboard Endpoints")
        print("=" * 50)
        
        # Test 1: Dashboard HTML page
        await test_html_endpoint(
            session, 
            f"{BASE_URL}/dashboard", 
            "1. Testing dashboard HTML page",
            EXPECTED_HTML_CONTENT
        )
        
        # Test 2: Health check
        health_data = await test_json_endpoint(
            session, 
            f"{BASE_URL}/health", 
            "2. Testing health endpoint"
        )
        print_health_data(health_data)
        
        # Test 3: Dashboard overview API
        overview_data = await test_json_endpoint(
            session, 
            f"{BASE_URL}/api/dashboard/overview", 
            "3. Testing dashboard overview API"
        )
        print_overview_data(overview_data)
        
        # Test 4: Detailed health API
        detailed_health_data = await test_json_endpoint(
            session, 
            f"{BASE_URL}/health/detailed", 
            "4. Testing detailed health API"
        )
        print_detailed_health_data(detailed_health_data)
        
        # Test 5: Real-time metrics API
        metrics_data = await test_json_endpoint(
            session, 
            f"{BASE_URL}/api/metrics/realtime", 
            "5. Testing real-time metrics API"
        )
        print_metrics_data(metrics_data)
        
        print("\n" + "=" * 50)
        print("🎯 Test Summary:")
        print("If all tests show ✅, your unified dashboard should be working!")
        print(f"Open your browser and go to: {BASE_URL}/dashboard")
        print("\n💡 Troubleshooting:")
        print("- If APIs fail, make sure DEVELOPMENT_MODE=true is set")
        print("- Check server logs for detailed error messages")
        print("- Verify all required environment variables are set")

if __name__ == "__main__":
    asyncio.run(test_dashboard_endpoints())