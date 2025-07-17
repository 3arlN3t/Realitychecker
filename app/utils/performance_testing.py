"""
Performance testing and benchmarking tools for Reality Checker application.

This module provides comprehensive performance testing capabilities including
load testing, benchmark comparison, and performance regression detection.
"""

import asyncio
import time
import statistics
import json
import csv
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import httpx
import psutil

from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_collector

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    test_name: str
    duration_seconds: float
    requests_per_second: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    errors: List[str] = field(default_factory=list)
    metrics: List[PerformanceMetric] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    target_url: str
    concurrent_users: int = 10
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 30
    request_timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Optional[Dict[str, Any]] = None
    method: str = "GET"


class PerformanceTester:
    """Comprehensive performance testing and benchmarking system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize performance tester.
        
        Args:
            base_url: Base URL for testing
        """
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
        self.metrics_collector = get_metrics_collector()
        
    async def run_load_test(self, config: LoadTestConfig) -> BenchmarkResult:
        """
        Run a comprehensive load test.
        
        Args:
            config: Load test configuration
            
        Returns:
            BenchmarkResult with test results
        """
        logger.info(f"Starting load test: {config.concurrent_users} users for {config.test_duration_seconds}s")
        
        start_time = time.time()
        results = []
        errors = []
        
        # Create semaphore to control concurrent requests
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def make_request(session: httpx.AsyncClient) -> Dict[str, Any]:
            """Make a single HTTP request."""
            async with semaphore:
                request_start = time.time()
                try:
                    if config.method.upper() == "POST":
                        response = await session.post(
                            config.target_url,
                            json=config.payload,
                            headers=config.headers,
                            timeout=config.request_timeout
                        )
                    else:
                        response = await session.get(
                            config.target_url,
                            headers=config.headers,
                            timeout=config.request_timeout
                        )
                    
                    response_time = time.time() - request_start
                    
                    return {
                        "success": response.status_code < 400,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "error": None
                    }
                    
                except Exception as e:
                    response_time = time.time() - request_start
                    error_msg = str(e)
                    errors.append(error_msg)
                    
                    return {
                        "success": False,
                        "status_code": 0,
                        "response_time": response_time,
                        "error": error_msg
                    }
        
        # Run load test with gradual ramp-up
        async with httpx.AsyncClient() as session:
            tasks = []
            test_end_time = start_time + config.test_duration_seconds
            
            # Gradual ramp-up
            users_per_second = config.concurrent_users / config.ramp_up_seconds if config.ramp_up_seconds > 0 else config.concurrent_users
            current_users = 0
            ramp_up_start = time.time()
            
            while time.time() < test_end_time:
                current_time = time.time()
                
                # Calculate how many users should be active
                if current_time - ramp_up_start < config.ramp_up_seconds:
                    target_users = min(config.concurrent_users, int((current_time - ramp_up_start) * users_per_second))
                else:
                    target_users = config.concurrent_users
                
                # Add new tasks if needed
                while current_users < target_users and time.time() < test_end_time:
                    task = asyncio.create_task(make_request(session))
                    tasks.append(task)
                    current_users += 1
                
                # Collect completed tasks
                if tasks:
                    done_tasks = [task for task in tasks if task.done()]
                    for task in done_tasks:
                        try:
                            result = await task
                            results.append(result)
                        except Exception as e:
                            errors.append(str(e))
                        tasks.remove(task)
                        current_users -= 1
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            
            # Wait for remaining tasks to complete
            if tasks:
                remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in remaining_results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                    else:
                        results.append(result)
        
        # Calculate statistics
        total_duration = time.time() - start_time
        successful_results = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in results if r["response_time"] is not None]
        
        if not response_times:
            response_times = [0.0]
        
        response_times.sort()
        
        benchmark_result = BenchmarkResult(
            test_name=f"Load Test - {config.concurrent_users} users",
            duration_seconds=total_duration,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            average_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p50_response_time=self._percentile(response_times, 0.5),
            p95_response_time=self._percentile(response_times, 0.95),
            p99_response_time=self._percentile(response_times, 0.99),
            success_rate=(len(successful_results) / len(results) * 100) if results else 0,
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(results) - len(successful_results),
            errors=list(set(errors))  # Remove duplicates
        )
        
        self.results.append(benchmark_result)
        logger.info(f"Load test completed: {benchmark_result.requests_per_second:.2f} RPS, {benchmark_result.success_rate:.1f}% success rate")
        
        return benchmark_result
    
    async def run_stress_test(self, max_users: int = 100, increment: int = 10, duration_per_level: int = 30) -> List[BenchmarkResult]:
        """
        Run a stress test with increasing load levels.
        
        Args:
            max_users: Maximum number of concurrent users
            increment: User increment per level
            duration_per_level: Duration for each stress level
            
        Returns:
            List of BenchmarkResult for each stress level
        """
        logger.info(f"Starting stress test: 0-{max_users} users, {increment} increment, {duration_per_level}s per level")
        
        stress_results = []
        health_endpoint = f"{self.base_url}/health"
        
        for users in range(increment, max_users + 1, increment):
            config = LoadTestConfig(
                target_url=health_endpoint,
                concurrent_users=users,
                test_duration_seconds=duration_per_level,
                ramp_up_seconds=5
            )
            
            result = await self.run_load_test(config)
            result.test_name = f"Stress Test - {users} users"
            stress_results.append(result)
            
            # Check if system is becoming unstable
            if result.success_rate < 50:
                logger.warning(f"Stress test stopped at {users} users due to high failure rate")
                break
            
            # Brief pause between stress levels
            await asyncio.sleep(2)
        
        return stress_results
    
    async def benchmark_endpoints(self, endpoints: List[str], requests_per_endpoint: int = 100) -> List[BenchmarkResult]:
        """
        Benchmark multiple endpoints for comparison.
        
        Args:
            endpoints: List of endpoint paths to benchmark
            requests_per_endpoint: Number of requests per endpoint
            
        Returns:
            List of BenchmarkResult for each endpoint
        """
        logger.info(f"Benchmarking {len(endpoints)} endpoints with {requests_per_endpoint} requests each")
        
        endpoint_results = []
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            config = LoadTestConfig(
                target_url=url,
                concurrent_users=10,
                test_duration_seconds=requests_per_endpoint // 10,  # Adjust duration based on requests
                ramp_up_seconds=2
            )
            
            result = await self.run_load_test(config)
            result.test_name = f"Endpoint Benchmark - {endpoint}"
            endpoint_results.append(result)
        
        return endpoint_results
    
    def benchmark_function(self, func: Callable, iterations: int = 1000, *args, **kwargs) -> BenchmarkResult:
        """
        Benchmark a Python function.
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            BenchmarkResult with function performance
        """
        logger.info(f"Benchmarking function {func.__name__} for {iterations} iterations")
        
        execution_times = []
        errors = []
        successful_runs = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                iteration_start = time.time()
                func(*args, **kwargs)
                execution_time = time.time() - iteration_start
                execution_times.append(execution_time)
                successful_runs += 1
            except Exception as e:
                errors.append(str(e))
                execution_times.append(0)  # Count failed executions as 0 time
        
        total_duration = time.time() - start_time
        
        if execution_times:
            execution_times.sort()
        else:
            execution_times = [0.0]
        
        result = BenchmarkResult(
            test_name=f"Function Benchmark - {func.__name__}",
            duration_seconds=total_duration,
            requests_per_second=iterations / total_duration if total_duration > 0 else 0,
            average_response_time=statistics.mean(execution_times),
            min_response_time=min(execution_times),
            max_response_time=max(execution_times),
            p50_response_time=self._percentile(execution_times, 0.5),
            p95_response_time=self._percentile(execution_times, 0.95),
            p99_response_time=self._percentile(execution_times, 0.99),
            success_rate=(successful_runs / iterations * 100) if iterations > 0 else 0,
            total_requests=iterations,
            successful_requests=successful_runs,
            failed_requests=iterations - successful_runs,
            errors=list(set(errors))
        )
        
        self.results.append(result)
        return result
    
    async def monitor_system_resources(self, duration_seconds: int = 60) -> List[PerformanceMetric]:
        """
        Monitor system resources during testing.
        
        Args:
            duration_seconds: Duration to monitor
            
        Returns:
            List of PerformanceMetric with system data
        """
        logger.info(f"Monitoring system resources for {duration_seconds}s")
        
        metrics = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            timestamp = datetime.now(timezone.utc)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            metrics.append(PerformanceMetric("cpu_usage", cpu_percent, "percent", timestamp))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(PerformanceMetric("memory_usage", memory.percent, "percent", timestamp))
            metrics.append(PerformanceMetric("memory_available", memory.available / 1024**3, "GB", timestamp))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.append(PerformanceMetric("disk_read_bytes", disk_io.read_bytes, "bytes", timestamp))
                metrics.append(PerformanceMetric("disk_write_bytes", disk_io.write_bytes, "bytes", timestamp))
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.append(PerformanceMetric("network_bytes_sent", network_io.bytes_sent, "bytes", timestamp))
                metrics.append(PerformanceMetric("network_bytes_recv", network_io.bytes_recv, "bytes", timestamp))
            
            await asyncio.sleep(1)  # Sample every second
        
        return metrics
    
    def compare_benchmarks(self, baseline: BenchmarkResult, current: BenchmarkResult) -> Dict[str, Any]:
        """
        Compare two benchmark results for regression detection.
        
        Args:
            baseline: Baseline benchmark result
            current: Current benchmark result
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "baseline_test": baseline.test_name,
            "current_test": current.test_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        # Compare key metrics
        metrics_to_compare = [
            ("requests_per_second", "higher_is_better"),
            ("average_response_time", "lower_is_better"),
            ("p95_response_time", "lower_is_better"),
            ("success_rate", "higher_is_better")
        ]
        
        for metric_name, direction in metrics_to_compare:
            baseline_value = getattr(baseline, metric_name)
            current_value = getattr(current, metric_name)
            
            if baseline_value == 0:
                change_percent = 0 if current_value == 0 else float('inf')
            else:
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
            
            is_improvement = (
                (direction == "higher_is_better" and change_percent > 0) or
                (direction == "lower_is_better" and change_percent < 0)
            )
            
            is_regression = (
                (direction == "higher_is_better" and change_percent < -5) or  # 5% threshold
                (direction == "lower_is_better" and change_percent > 5)
            )
            
            comparison["metrics"][metric_name] = {
                "baseline_value": baseline_value,
                "current_value": current_value,
                "change_percent": round(change_percent, 2),
                "is_improvement": is_improvement,
                "is_regression": is_regression
            }
        
        # Overall assessment
        regressions = [m for m in comparison["metrics"].values() if m["is_regression"]]
        improvements = [m for m in comparison["metrics"].values() if m["is_improvement"]]
        
        comparison["summary"] = {
            "has_regressions": len(regressions) > 0,
            "has_improvements": len(improvements) > 0,
            "regression_count": len(regressions),
            "improvement_count": len(improvements)
        }
        
        return comparison
    
    def export_results(self, filename: str, format: str = "json") -> None:
        """
        Export benchmark results to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
        """
        if format.lower() == "json":
            results_data = [asdict(result) for result in self.results]
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
        
        elif format.lower() == "csv":
            if not self.results:
                return
            
            fieldnames = [
                "test_name", "duration_seconds", "requests_per_second",
                "average_response_time", "p95_response_time", "success_rate",
                "total_requests", "successful_requests", "failed_requests"
            ]
            
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.results:
                    row = {field: getattr(result, field) for field in fieldnames}
                    writer.writerow(row)
        
        logger.info(f"Exported {len(self.results)} results to {filename}")
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive performance report.
        
        Returns:
            String containing formatted report
        """
        if not self.results:
            return "No benchmark results available."
        
        report = []
        report.append("PERFORMANCE TEST REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"Total Tests: {len(self.results)}")
        report.append("")
        
        for i, result in enumerate(self.results, 1):
            report.append(f"{i}. {result.test_name}")
            report.append("-" * len(f"{i}. {result.test_name}"))
            report.append(f"Duration: {result.duration_seconds:.2f}s")
            report.append(f"Requests/sec: {result.requests_per_second:.2f}")
            report.append(f"Avg Response Time: {result.average_response_time*1000:.2f}ms")
            report.append(f"P95 Response Time: {result.p95_response_time*1000:.2f}ms")
            report.append(f"Success Rate: {result.success_rate:.1f}%")
            report.append(f"Total Requests: {result.total_requests}")
            
            if result.errors:
                report.append(f"Errors: {len(result.errors)} unique error types")
            
            report.append("")
        
        return "\n".join(report)
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0.0
        
        index = int(percentile * (len(values) - 1))
        return values[index]


# Convenience functions for common testing scenarios
async def quick_load_test(url: str, users: int = 10, duration: int = 30) -> BenchmarkResult:
    """
    Run a quick load test with default settings.
    
    Args:
        url: URL to test
        users: Number of concurrent users
        duration: Test duration in seconds
        
    Returns:
        BenchmarkResult
    """
    tester = PerformanceTester()
    config = LoadTestConfig(
        target_url=url,
        concurrent_users=users,
        test_duration_seconds=duration
    )
    return await tester.run_load_test(config)


async def benchmark_application_endpoints() -> List[BenchmarkResult]:
    """
    Benchmark common application endpoints.
    
    Returns:
        List of BenchmarkResult for each endpoint
    """
    tester = PerformanceTester()
    endpoints = ["/health", "/api/webhook", "/api/dashboard/stats"]
    return await tester.benchmark_endpoints(endpoints)


async def run_comprehensive_test_suite() -> Dict[str, Any]:
    """
    Run a comprehensive performance test suite.
    
    Returns:
        Dictionary with all test results
    """
    logger.info("Starting comprehensive performance test suite")
    
    tester = PerformanceTester()
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": {}
    }
    
    # Quick load test
    load_result = await quick_load_test("http://localhost:8000/health", 10, 30)
    results["tests"]["load_test"] = asdict(load_result)
    
    # Endpoint benchmarks
    endpoint_results = await benchmark_application_endpoints()
    results["tests"]["endpoint_benchmarks"] = [asdict(r) for r in endpoint_results]
    
    # Stress test (shorter for comprehensive suite)
    stress_results = await tester.run_stress_test(max_users=50, increment=10, duration_per_level=15)
    results["tests"]["stress_test"] = [asdict(r) for r in stress_results]
    
    # Generate summary report
    tester.results.extend([load_result] + endpoint_results + stress_results)
    results["report"] = tester.generate_report()
    
    logger.info("Comprehensive test suite completed")
    return results