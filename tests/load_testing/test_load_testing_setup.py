#!/usr/bin/env python3
"""
Test script to verify load testing setup and dependencies.

This script performs basic validation of the load testing environment
to ensure all components are properly configured before running full tests.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import aiohttp
    import psutil
    from app.services.redis_connection_manager import get_redis_manager
    from app.utils.logging import get_logger
    print("✅ All required imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

logger = get_logger(__name__)


async def test_redis_connection():
    """Test Redis connection."""
    print("\n🔧 Testing Redis connection...")
    
    try:
        redis_manager = get_redis_manager()
        success = await redis_manager.initialize()
        
        if success:
            print("✅ Redis connection successful")
            
            # Test basic operations
            await redis_manager.execute_command('set', 'test_key', 'test_value')
            result = await redis_manager.execute_command('get', 'test_key')
            
            if result == 'test_value':
                print("✅ Redis operations working")
            else:
                print("⚠️  Redis operations may have issues")
            
            # Cleanup
            await redis_manager.execute_command('del', 'test_key')
            await redis_manager.cleanup()
            
        else:
            print("⚠️  Redis connection failed - tests will run in fallback mode")
            
    except Exception as e:
        print(f"⚠️  Redis test error: {e}")


async def test_webhook_endpoint():
    """Test webhook endpoint availability."""
    print("\n🌐 Testing webhook endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test GET request first (should be faster)
            async with session.get(
                "http://localhost:8000/webhook/whatsapp",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    print("✅ Webhook endpoint accessible")
                else:
                    print(f"⚠️  Webhook endpoint returned status {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to webhook endpoint at localhost:8000")
        print("   Make sure the application is running with: python -m app.main")
    except asyncio.TimeoutError:
        print("⚠️  Webhook endpoint timeout - may be slow")
    except Exception as e:
        print(f"⚠️  Webhook test error: {e}")


def test_system_resources():
    """Test system resource availability."""
    print("\n📊 Checking system resources...")
    
    try:
        # Check CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"✅ CPU: {cpu_count} cores, {cpu_percent:.1f}% usage")
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"✅ Memory: {memory_gb:.1f}GB total, {memory.percent:.1f}% used")
        
        # Check available memory for testing
        available_gb = memory.available / (1024**3)
        if available_gb < 1.0:
            print("⚠️  Low available memory - may affect test performance")
        else:
            print(f"✅ Available memory: {available_gb:.1f}GB")
            
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_gb = disk.free / (1024**3)
        print(f"✅ Disk space: {disk_gb:.1f}GB free")
        
    except Exception as e:
        print(f"⚠️  System resource check error: {e}")


def test_load_testing_modules():
    """Test load testing module imports."""
    print("\n📦 Testing load testing modules...")
    
    try:
        from tests.load_testing.webhook_load_test import WebhookLoadTester, LoadTestConfig
        print("✅ Webhook load test module imported")
        
        from tests.load_testing.redis_benchmark import RedisBenchmark, RedisBenchmarkConfig
        print("✅ Redis benchmark module imported")
        
        from tests.load_testing.system_capacity_test import SystemCapacityTester, CapacityTestConfig
        print("✅ System capacity test module imported")
        
        from tests.load_testing.baseline_metrics import BaselineValidator, BaselineMetrics
        print("✅ Baseline validation module imported")
        
        # Test configuration creation
        webhook_config = LoadTestConfig(concurrent_users=5, requests_per_user=2)
        redis_config = RedisBenchmarkConfig(concurrent_operations=5, operations_per_worker=10)
        capacity_config = CapacityTestConfig(max_concurrent_requests=10)
        baseline_metrics = BaselineMetrics()
        
        print("✅ Configuration objects created successfully")
        
    except Exception as e:
        print(f"❌ Load testing module error: {e}")
        return False
    
    return True


async def run_quick_test():
    """Run a quick performance test to verify functionality."""
    print("\n🚀 Running quick functionality test...")
    
    try:
        from tests.load_testing.webhook_load_test import WebhookLoadTester, LoadTestConfig
        
        # Very light test configuration
        config = LoadTestConfig(
            concurrent_users=2,
            requests_per_user=1,
            ramp_up_time=1,
            enable_burst_testing=False,
            timeout=10.0
        )
        
        async with WebhookLoadTester(config) as tester:
            # Just test one request
            result = await tester.send_webhook_request("text", 0)
            
            if result.success:
                print(f"✅ Quick test successful: {result.response_time_ms:.1f}ms response time")
            else:
                print(f"⚠️  Quick test failed: {result.error_message}")
                
    except Exception as e:
        print(f"⚠️  Quick test error: {e}")


def print_recommendations():
    """Print setup recommendations."""
    print("\n💡 Setup Recommendations:")
    print("   1. Ensure Redis is running: redis-server")
    print("   2. Start the application: python -m app.main")
    print("   3. For best results, close other applications to free resources")
    print("   4. Run tests during low system activity periods")
    print("   5. Consider running individual test types first before full suite")


async def main():
    """Main test function."""
    print("🔍 Load Testing Setup Verification")
    print("=" * 50)
    
    # Test system resources
    test_system_resources()
    
    # Test module imports
    modules_ok = test_load_testing_modules()
    
    if not modules_ok:
        print("\n❌ Module import issues detected - cannot proceed")
        sys.exit(1)
    
    # Test Redis connection
    await test_redis_connection()
    
    # Test webhook endpoint
    await test_webhook_endpoint()
    
    # Run quick functionality test
    await run_quick_test()
    
    # Print recommendations
    print_recommendations()
    
    print("\n🎯 Setup verification completed!")
    print("   You can now run the full performance test suite with:")
    print("   python tests/load_testing/run_performance_tests.py")


if __name__ == "__main__":
    asyncio.run(main())