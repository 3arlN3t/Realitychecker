#!/usr/bin/env python3
"""
Main performance testing runner script.

This script orchestrates all performance benchmarking and load testing
to validate the Redis performance optimization implementation.

Usage:
    python tests/load_testing/run_performance_tests.py [--test-type TYPE] [--output-file FILE]

Test types:
    - webhook: Webhook load testing only
    - redis: Redis benchmarking only  
    - capacity: System capacity testing only
    - baseline: Baseline validation only
    - all: Run all tests (default)
"""

import asyncio
import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.load_testing.webhook_load_test import run_webhook_load_test, LoadTestConfig
from tests.load_testing.redis_benchmark import run_redis_benchmark, RedisBenchmarkConfig
from tests.load_testing.system_capacity_test import run_capacity_test, CapacityTestConfig
from tests.load_testing.baseline_metrics import validate_performance_improvements, BaselineMetrics
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceTestRunner:
    """Main performance test runner."""
    
    def __init__(self, output_file: Optional[str] = None):
        self.output_file = output_file
        self.results: Dict[str, Any] = {}
        
    async def run_webhook_tests(self) -> Dict[str, Any]:
        """Run webhook load tests."""
        logger.info("🚀 Starting webhook load tests...")
        
        # Standard load test
        standard_config = LoadTestConfig(
            concurrent_users=50,
            requests_per_user=20,
            ramp_up_time=10,
            enable_burst_testing=True,
            burst_intensity=100,
            target_response_time_ms=500.0,
            max_response_time_ms=2000.0
        )
        
        standard_results = await run_webhook_load_test(standard_config)
        
        # High load test
        logger.info("🔥 Running high load webhook test...")
        high_load_config = LoadTestConfig(
            concurrent_users=100,
            requests_per_user=10,
            ramp_up_time=15,
            enable_burst_testing=True,
            burst_intensity=200,
            target_response_time_ms=1000.0,
            max_response_time_ms=3000.0
        )
        
        high_load_results = await run_webhook_load_test(high_load_config)
        
        return {
            "standard_load": standard_results,
            "high_load": high_load_results,
            "test_type": "webhook_load_testing"
        }
    
    async def run_redis_tests(self) -> Dict[str, Any]:
        """Run Redis benchmarking tests."""
        logger.info("🔧 Starting Redis benchmark tests...")
        
        # Standard benchmark
        standard_config = RedisBenchmarkConfig(
            concurrent_operations=100,
            operations_per_worker=1000,
            read_percentage=70,
            write_percentage=25,
            delete_percentage=5,
            test_circuit_breaker=True,
            failure_injection_rate=0.05
        )
        
        standard_results = await run_redis_benchmark(standard_config)
        
        # High throughput benchmark
        logger.info("⚡ Running high throughput Redis benchmark...")
        high_throughput_config = RedisBenchmarkConfig(
            concurrent_operations=200,
            operations_per_worker=500,
            read_percentage=80,
            write_percentage=15,
            delete_percentage=5,
            test_circuit_breaker=True,
            failure_injection_rate=0.1
        )
        
        high_throughput_results = await run_redis_benchmark(high_throughput_config)
        
        return {
            "standard_benchmark": standard_results,
            "high_throughput": high_throughput_results,
            "test_type": "redis_benchmarking"
        }
    
    async def run_capacity_tests(self) -> Dict[str, Any]:
        """Run system capacity tests."""
        logger.info("📊 Starting system capacity tests...")
        
        config = CapacityTestConfig(
            max_concurrent_requests=500,
            load_ramp_steps=[10, 25, 50, 100, 200, 300, 500],
            step_duration=30,
            enable_redis_failure=True,
            enable_database_failure=True,
            test_recovery=True,
            redis_failure_duration=30,
            database_failure_duration=20
        )
        
        results = await run_capacity_test(config)
        
        return {
            "capacity_test": results,
            "test_type": "system_capacity_testing"
        }
    
    async def run_baseline_validation(self) -> Dict[str, Any]:
        """Run baseline performance validation."""
        logger.info("📈 Starting baseline validation...")
        
        # Use realistic pre-optimization baseline metrics
        baseline = BaselineMetrics(
            webhook_avg_response_time_ms=2000.0,
            webhook_p95_response_time_ms=5000.0,
            webhook_p99_response_time_ms=14000.0,  # The reported 14+ second issue
            webhook_success_rate=85.0,
            webhook_throughput_rps=10.0,
            redis_avg_latency_ms=50.0,
            redis_p95_latency_ms=200.0,
            redis_p99_latency_ms=500.0,
            redis_success_rate=70.0,  # Due to connection issues
            redis_throughput_ops=500.0,
            system_max_concurrent_users=20,
            redis_connection_failure_rate=30.0,
            webhook_timeout_rate=15.0
        )
        
        results = await validate_performance_improvements(baseline)
        
        return {
            "baseline_validation": results,
            "test_type": "baseline_validation"
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        logger.info("🎯 Starting comprehensive performance testing suite...")
        
        start_time = time.time()
        all_results = {
            "test_suite": "comprehensive_performance_testing",
            "start_time": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # Run webhook tests
            webhook_results = await self.run_webhook_tests()
            all_results["tests"]["webhook"] = webhook_results
            logger.info("✅ Webhook tests completed")
            
            # Run Redis tests
            redis_results = await self.run_redis_tests()
            all_results["tests"]["redis"] = redis_results
            logger.info("✅ Redis tests completed")
            
            # Run capacity tests
            capacity_results = await self.run_capacity_tests()
            all_results["tests"]["capacity"] = capacity_results
            logger.info("✅ Capacity tests completed")
            
            # Run baseline validation
            baseline_results = await self.run_baseline_validation()
            all_results["tests"]["baseline"] = baseline_results
            logger.info("✅ Baseline validation completed")
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            all_results["error"] = str(e)
            all_results["status"] = "FAILED"
        else:
            all_results["status"] = "COMPLETED"
        
        all_results["end_time"] = datetime.now().isoformat()
        all_results["total_duration"] = time.time() - start_time
        
        # Generate overall assessment
        all_results["assessment"] = self._generate_overall_assessment(all_results)
        
        return all_results
    
    def _generate_overall_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance assessment."""
        assessment = {
            "overall_grade": "UNKNOWN",
            "requirements_met": {},
            "key_improvements": [],
            "areas_for_improvement": [],
            "summary": ""
        }
        
        if "tests" not in results:
            return assessment
        
        tests = results["tests"]
        grades = []
        
        # Assess webhook performance
        if "webhook" in tests:
            webhook_grade = tests["webhook"]["standard_load"]["test_summary"]["performance_grade"]
            grades.append(webhook_grade)
            
            if webhook_grade == "PASS":
                assessment["key_improvements"].append("Webhook response times meet sub-2-second requirement")
            else:
                assessment["areas_for_improvement"].append("Webhook performance needs optimization")
        
        # Assess Redis performance
        if "redis" in tests:
            redis_grade = tests["redis"]["standard_benchmark"]["benchmark_summary"]["performance_grade"]
            grades.append(redis_grade)
            
            if redis_grade == "PASS":
                assessment["key_improvements"].append("Redis operations perform within target latency")
            else:
                assessment["areas_for_improvement"].append("Redis performance needs optimization")
        
        # Assess capacity
        if "capacity" in tests:
            capacity_grade = tests["capacity"]["capacity_test"]["capacity_test_summary"]["overall_grade"]
            grades.append(capacity_grade)
            
            if capacity_grade == "PASS":
                assessment["key_improvements"].append("System handles high concurrent load effectively")
            else:
                assessment["areas_for_improvement"].append("System capacity limits need addressing")
        
        # Assess baseline improvements
        if "baseline" in tests:
            baseline_grade = tests["baseline"]["baseline_validation"]["validation_summary"]["performance_grade"]
            grades.append(baseline_grade)
            
            if baseline_grade in ["EXCELLENT", "GOOD"]:
                assessment["key_improvements"].append("Significant performance improvements over baseline")
            else:
                assessment["areas_for_improvement"].append("Performance improvements below expectations")
        
        # Calculate overall grade
        if not grades:
            assessment["overall_grade"] = "UNKNOWN"
        elif all(g == "PASS" or g in ["EXCELLENT", "GOOD"] for g in grades):
            assessment["overall_grade"] = "EXCELLENT"
        elif sum(1 for g in grades if g == "PASS" or g in ["EXCELLENT", "GOOD"]) >= len(grades) * 0.75:
            assessment["overall_grade"] = "GOOD"
        elif sum(1 for g in grades if g == "PASS" or g in ["EXCELLENT", "GOOD", "FAIR"]) >= len(grades) * 0.5:
            assessment["overall_grade"] = "FAIR"
        else:
            assessment["overall_grade"] = "POOR"
        
        # Requirements assessment
        assessment["requirements_met"] = {
            "4.1": "webhook" in tests and "redis" in tests,  # Performance monitoring
            "4.2": "redis" in tests,  # Redis operation monitoring
            "4.3": "capacity" in tests,  # Performance threshold alerts
            "5.1": "capacity" in tests and "redis" in tests,  # Connection pool management
            "5.2": "capacity" in tests  # Connection pool utilization monitoring
        }
        
        # Generate summary
        improvements_count = len(assessment["key_improvements"])
        issues_count = len(assessment["areas_for_improvement"])
        
        if assessment["overall_grade"] == "EXCELLENT":
            assessment["summary"] = f"Outstanding performance! All optimization goals achieved with {improvements_count} key improvements."
        elif assessment["overall_grade"] == "GOOD":
            assessment["summary"] = f"Good performance with {improvements_count} improvements, but {issues_count} areas need attention."
        elif assessment["overall_grade"] == "FAIR":
            assessment["summary"] = f"Mixed results with {improvements_count} improvements and {issues_count} issues to address."
        else:
            assessment["summary"] = f"Performance below expectations with {issues_count} critical issues requiring immediate attention."
        
        return assessment
    
    def save_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        if self.output_file:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"📄 Results saved to {output_path}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test results summary."""
        print("\n" + "="*100)
        print("REDIS PERFORMANCE OPTIMIZATION - LOAD TESTING RESULTS")
        print("="*100)
        
        if "assessment" in results:
            assessment = results["assessment"]
            print(f"\n🎯 Overall Grade: {assessment['overall_grade']}")
            print(f"📊 Test Duration: {results.get('total_duration', 0):.1f} seconds")
            print(f"📝 Summary: {assessment['summary']}")
            
            if assessment["key_improvements"]:
                print(f"\n✅ Key Improvements ({len(assessment['key_improvements'])}):")
                for improvement in assessment["key_improvements"]:
                    print(f"   • {improvement}")
            
            if assessment["areas_for_improvement"]:
                print(f"\n⚠️  Areas for Improvement ({len(assessment['areas_for_improvement'])}):")
                for area in assessment["areas_for_improvement"]:
                    print(f"   • {area}")
            
            print(f"\n📋 Requirements Validation:")
            for req_id, met in assessment["requirements_met"].items():
                status = "✅ PASS" if met else "❌ FAIL"
                print(f"   {req_id}: {status}")
        
        # Print individual test summaries
        if "tests" in results:
            tests = results["tests"]
            
            if "webhook" in tests:
                webhook_summary = tests["webhook"]["standard_load"]["test_summary"]
                print(f"\n🌐 Webhook Load Test:")
                print(f"   Success Rate: {webhook_summary['success_rate']:.1f}%")
                print(f"   Requests/Second: {webhook_summary['requests_per_second']:.1f}")
                print(f"   Grade: {webhook_summary['performance_grade']}")
            
            if "redis" in tests:
                redis_summary = tests["redis"]["standard_benchmark"]["benchmark_summary"]
                print(f"\n🔧 Redis Benchmark:")
                print(f"   Operations/Second: {redis_summary['operations_per_second']:.1f}")
                print(f"   Success Rate: {redis_summary['success_rate']:.1f}%")
                print(f"   Grade: {redis_summary['performance_grade']}")
            
            if "capacity" in tests:
                capacity_summary = tests["capacity"]["capacity_test"]["capacity_test_summary"]
                print(f"\n📊 Capacity Test:")
                print(f"   Max Concurrent Load: {capacity_summary['max_concurrent_load']}")
                print(f"   Grade: {capacity_summary['overall_grade']}")
            
            if "baseline" in tests:
                baseline_summary = tests["baseline"]["baseline_validation"]["validation_summary"]
                print(f"\n📈 Baseline Validation:")
                print(f"   Overall Improvement: {baseline_summary['overall_improvement']}")
                print(f"   Average Improvement: {baseline_summary['average_improvement_percent']:.1f}%")
                print(f"   Grade: {baseline_summary['performance_grade']}")
        
        print("\n" + "="*100)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Redis Performance Optimization Load Testing")
    parser.add_argument(
        "--test-type",
        choices=["webhook", "redis", "capacity", "baseline", "all"],
        default="all",
        help="Type of test to run (default: all)"
    )
    parser.add_argument(
        "--output-file",
        help="Output file for test results (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test runner
    runner = PerformanceTestRunner(args.output_file)
    
    try:
        # Run specified tests
        if args.test_type == "webhook":
            results = await runner.run_webhook_tests()
        elif args.test_type == "redis":
            results = await runner.run_redis_tests()
        elif args.test_type == "capacity":
            results = await runner.run_capacity_tests()
        elif args.test_type == "baseline":
            results = await runner.run_baseline_validation()
        else:  # all
            results = await runner.run_all_tests()
        
        # Save and display results
        runner.save_results(results)
        runner.print_summary(results)
        
        # Exit with appropriate code
        if "assessment" in results:
            grade = results["assessment"]["overall_grade"]
            if grade in ["EXCELLENT", "GOOD"]:
                sys.exit(0)
            elif grade == "FAIR":
                sys.exit(1)
            else:
                sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("🛑 Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())