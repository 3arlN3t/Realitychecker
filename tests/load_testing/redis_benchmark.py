"""
Redis performance benchmarking script.

This module implements comprehensive Redis performance testing to validate
connection management, circuit breaker functionality, and high-throughput operations.

Requirements tested:
- 4.2: Redis operation monitoring with latency measurements
- 5.1: Connection pool management optimization
- 5.2: Connection pool utilization monitoring
"""

import asyncio
import time
import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
import string

from app.services.redis_connection_manager import RedisConnectionManager, RedisConfig
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RedisBenchmarkConfig:
    """Configuration for Redis benchmarking."""
    # Connection settings
    redis_url: str = "redis://localhost:6379/0"
    pool_size: int = 20
    max_connections: int = 50
    
    # Test parameters
    concurrent_operations: int = 100
    operations_per_worker: int = 1000
    test_duration: int = 60  # seconds
    
    # Operation mix (percentages)
    read_percentage: int = 70
    write_percentage: int = 25
    delete_percentage: int = 5
    
    # Performance thresholds
    target_latency_ms: float = 5.0
    max_latency_ms: float = 50.0
    min_throughput_ops_sec: float = 1000.0
    
    # Circuit breaker testing
    test_circuit_breaker: bool = True
    failure_injection_rate: float = 0.1  # 10% failure rate


@dataclass
class OperationResult:
    """Result of a single Redis operation."""
    operation: str
    latency_ms: float
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class BenchmarkResults:
    """Aggregated benchmark results."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    
    # Latency statistics
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Throughput metrics
    operations_per_second: float = 0.0
    test_duration: float = 0.0
    
    # Operation breakdown
    read_operations: int = 0
    write_operations: int = 0
    delete_operations: int = 0
    
    # Connection metrics
    peak_connections: int = 0
    connection_errors: int = 0
    circuit_breaker_trips: int = 0
    
    # Detailed results
    operation_results: List[OperationResult] = field(default_factory=list)


class RedisBenchmark:
    """Redis performance benchmark suite."""
    
    def __init__(self, config: RedisBenchmarkConfig):
        self.config = config
        self.redis_manager: Optional[RedisConnectionManager] = None
        self.results = BenchmarkResults()
        self._test_data_keys: List[str] = []
        
    async def setup(self):
        """Setup Redis connection manager and test data."""
        logger.info("Setting up Redis benchmark...")
        
        # Configure Redis connection manager
        redis_config = RedisConfig(
            primary_url=self.config.redis_url,
            pool_size=self.config.pool_size,
            max_connections=self.config.max_connections,
            connection_timeout=5.0,
            socket_timeout=5.0,
            command_timeout=2.0
        )
        
        self.redis_manager = RedisConnectionManager(redis_config)
        success = await self.redis_manager.initialize()
        
        if not success:
            raise RuntimeError("Failed to initialize Redis connection manager")
        
        # Pre-populate test data
        await self._populate_test_data()
        
        logger.info("✅ Redis benchmark setup completed")
    
    async def cleanup(self):
        """Cleanup test data and connections."""
        logger.info("Cleaning up Redis benchmark...")
        
        # Clean up test data
        await self._cleanup_test_data()
        
        # Cleanup Redis manager
        if self.redis_manager:
            await self.redis_manager.cleanup()
        
        logger.info("✅ Redis benchmark cleanup completed")
    
    async def _populate_test_data(self):
        """Pre-populate Redis with test data."""
        logger.info("Populating test data...")
        
        # Create test keys for read operations
        for i in range(1000):
            key = f"benchmark:read:{i}"
            value = f"test_value_{i}_{''.join(random.choices(string.ascii_letters, k=50))}"
            
            await self.redis_manager.execute_command('set', key, value)
            self._test_data_keys.append(key)
        
        logger.info(f"Created {len(self._test_data_keys)} test keys")
    
    async def _cleanup_test_data(self):
        """Clean up test data from Redis."""
        if not self._test_data_keys:
            return
        
        logger.info("Cleaning up test data...")
        
        # Delete test keys in batches
        batch_size = 100
        for i in range(0, len(self._test_data_keys), batch_size):
            batch = self._test_data_keys[i:i + batch_size]
            if batch:
                await self.redis_manager.execute_command('del', *batch)
        
        # Clean up any benchmark keys
        await self.redis_manager.execute_command('del', 'benchmark:*')
        
        logger.info("Test data cleanup completed")
    
    def _select_operation(self) -> str:
        """Select operation type based on configured percentages."""
        rand = random.randint(1, 100)
        
        if rand <= self.config.read_percentage:
            return "read"
        elif rand <= self.config.read_percentage + self.config.write_percentage:
            return "write"
        else:
            return "delete"
    
    async def _execute_read_operation(self) -> OperationResult:
        """Execute a read operation."""
        start_time = time.time()
        
        try:
            # Select random test key
            key = random.choice(self._test_data_keys)
            
            # Execute GET command
            result = await self.redis_manager.execute_command('get', key)
            
            latency_ms = (time.time() - start_time) * 1000
            success = result is not None
            
            return OperationResult(
                operation="read",
                latency_ms=latency_ms,
                success=success,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return OperationResult(
                operation="read",
                latency_ms=latency_ms,
                success=False,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _execute_write_operation(self) -> OperationResult:
        """Execute a write operation."""
        start_time = time.time()
        
        try:
            # Generate unique key and value
            key = f"benchmark:write:{int(time.time() * 1000000)}:{random.randint(1000, 9999)}"
            value = f"benchmark_value_{''.join(random.choices(string.ascii_letters + string.digits, k=100))}"
            
            # Execute SET command
            result = await self.redis_manager.execute_command('set', key, value)
            
            latency_ms = (time.time() - start_time) * 1000
            success = result == "OK"
            
            return OperationResult(
                operation="write",
                latency_ms=latency_ms,
                success=success,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return OperationResult(
                operation="write",
                latency_ms=latency_ms,
                success=False,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _execute_delete_operation(self) -> OperationResult:
        """Execute a delete operation."""
        start_time = time.time()
        
        try:
            # Create a key to delete
            key = f"benchmark:delete:{int(time.time() * 1000000)}:{random.randint(1000, 9999)}"
            
            # First set the key, then delete it
            await self.redis_manager.execute_command('set', key, "to_delete")
            result = await self.redis_manager.execute_command('del', key)
            
            latency_ms = (time.time() - start_time) * 1000
            success = result == 1
            
            return OperationResult(
                operation="delete",
                latency_ms=latency_ms,
                success=success,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return OperationResult(
                operation="delete",
                latency_ms=latency_ms,
                success=False,
                timestamp=datetime.now(),
                error_message=str(e)
            )  
  
    async def _execute_single_operation(self) -> OperationResult:
        """Execute a single Redis operation based on configured mix."""
        operation_type = self._select_operation()
        
        # Inject failures for circuit breaker testing
        if (self.config.test_circuit_breaker and 
            random.random() < self.config.failure_injection_rate):
            # Simulate failure by using invalid command
            start_time = time.time()
            try:
                await self.redis_manager.execute_command('invalid_command')
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                return OperationResult(
                    operation=f"{operation_type}_injected_failure",
                    latency_ms=latency_ms,
                    success=False,
                    timestamp=datetime.now(),
                    error_message=str(e)
                )
        
        # Execute normal operation
        if operation_type == "read":
            return await self._execute_read_operation()
        elif operation_type == "write":
            return await self._execute_write_operation()
        else:  # delete
            return await self._execute_delete_operation()
    
    async def _worker_task(self, worker_id: int, operations_count: int) -> List[OperationResult]:
        """Worker task that executes multiple Redis operations."""
        results = []
        
        logger.info(f"Worker {worker_id} starting {operations_count} operations")
        
        for i in range(operations_count):
            result = await self._execute_single_operation()
            results.append(result)
            
            # Log slow operations
            if result.latency_ms > self.config.target_latency_ms:
                logger.warning(
                    f"Slow {result.operation} operation: {result.latency_ms:.1f}ms "
                    f"(target: {self.config.target_latency_ms}ms)"
                )
            
            # Small delay to prevent overwhelming Redis
            await asyncio.sleep(0.001)  # 1ms delay
        
        logger.info(f"Worker {worker_id} completed {len(results)} operations")
        return results
    
    async def run_benchmark(self) -> BenchmarkResults:
        """Run comprehensive Redis benchmark."""
        logger.info(f"Starting Redis benchmark with {self.config.concurrent_operations} workers")
        logger.info(f"Target latency: {self.config.target_latency_ms}ms")
        logger.info(f"Target throughput: {self.config.min_throughput_ops_sec} ops/sec")
        
        test_start_time = time.time()
        
        # Create worker tasks
        tasks = []
        for worker_id in range(self.config.concurrent_operations):
            task = asyncio.create_task(
                self._worker_task(worker_id, self.config.operations_per_worker)
            )
            tasks.append(task)
        
        # Wait for all workers to complete
        worker_results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for worker_result_list in worker_results:
            all_results.extend(worker_result_list)
        
        test_duration = time.time() - test_start_time
        
        # Calculate results
        self.results = self._calculate_results(all_results, test_duration)
        
        # Get connection metrics from Redis manager
        if self.redis_manager:
            metrics = await self.redis_manager.get_metrics()
            self.results.peak_connections = metrics.max_connections_used
            self.results.connection_errors = metrics.failed_requests
            self.results.circuit_breaker_trips = getattr(metrics, 'circuit_breaker_trips', 0)
        
        logger.info(f"Benchmark completed in {test_duration:.1f}s")
        logger.info(f"Total operations: {self.results.total_operations}")
        logger.info(f"Operations per second: {self.results.operations_per_second:.1f}")
        logger.info(f"Average latency: {self.results.avg_latency_ms:.1f}ms")
        logger.info(f"P95 latency: {self.results.p95_latency_ms:.1f}ms")
        
        return self.results
    
    def _calculate_results(self, results: List[OperationResult], test_duration: float) -> BenchmarkResults:
        """Calculate aggregated benchmark results."""
        if not results:
            return BenchmarkResults()
        
        # Basic counts
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r.success)
        failed_operations = total_operations - successful_operations
        
        # Operation type breakdown
        read_ops = sum(1 for r in results if r.operation.startswith("read"))
        write_ops = sum(1 for r in results if r.operation.startswith("write"))
        delete_ops = sum(1 for r in results if r.operation.startswith("delete"))
        
        # Latency statistics (only for successful operations)
        successful_latencies = [r.latency_ms for r in results if r.success]
        
        if successful_latencies:
            min_latency = min(successful_latencies)
            max_latency = max(successful_latencies)
            avg_latency = statistics.mean(successful_latencies)
            p50_latency = statistics.median(successful_latencies)
            p95_latency = self._percentile(successful_latencies, 95)
            p99_latency = self._percentile(successful_latencies, 99)
        else:
            min_latency = max_latency = avg_latency = p50_latency = p95_latency = p99_latency = 0.0
        
        # Throughput
        ops_per_second = total_operations / test_duration if test_duration > 0 else 0
        
        return BenchmarkResults(
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            operations_per_second=ops_per_second,
            test_duration=test_duration,
            read_operations=read_ops,
            write_operations=write_ops,
            delete_operations=delete_ops,
            operation_results=results
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        # Performance assessment
        performance_grade = "PASS"
        issues = []
        
        # Check latency requirements
        if self.results.p95_latency_ms > self.config.target_latency_ms:
            performance_grade = "WARN" if performance_grade == "PASS" else performance_grade
            issues.append(f"P95 latency {self.results.p95_latency_ms:.1f}ms exceeds target {self.config.target_latency_ms}ms")
        
        if self.results.p99_latency_ms > self.config.max_latency_ms:
            performance_grade = "FAIL"
            issues.append(f"P99 latency {self.results.p99_latency_ms:.1f}ms exceeds maximum {self.config.max_latency_ms}ms")
        
        # Check throughput requirements
        if self.results.operations_per_second < self.config.min_throughput_ops_sec:
            performance_grade = "FAIL"
            issues.append(f"Throughput {self.results.operations_per_second:.1f} ops/sec below minimum {self.config.min_throughput_ops_sec}")
        
        # Check success rate
        success_rate = (self.results.successful_operations / self.results.total_operations * 100) if self.results.total_operations > 0 else 0
        if success_rate < 95.0:
            performance_grade = "FAIL"
            issues.append(f"Success rate {success_rate:.1f}% below 95% threshold")
        
        # Requirements validation
        requirements_status = {
            "4.2": {
                "description": "Redis operation monitoring with latency measurements",
                "status": "PASS" if self.results.avg_latency_ms > 0 else "FAIL",
                "metrics": {
                    "avg_latency_ms": self.results.avg_latency_ms,
                    "p95_latency_ms": self.results.p95_latency_ms,
                    "p99_latency_ms": self.results.p99_latency_ms,
                    "operations_monitored": self.results.total_operations
                }
            },
            "5.1": {
                "description": "Connection pool management optimization",
                "status": "PASS" if success_rate > 95 and self.results.connection_errors < self.results.total_operations * 0.01 else "FAIL",
                "metrics": {
                    "success_rate": success_rate,
                    "connection_errors": self.results.connection_errors,
                    "peak_connections": self.results.peak_connections,
                    "operations_per_second": self.results.operations_per_second
                }
            },
            "5.2": {
                "description": "Connection pool utilization monitoring",
                "status": "PASS" if self.results.peak_connections > 0 else "FAIL",
                "metrics": {
                    "peak_connections": self.results.peak_connections,
                    "configured_pool_size": self.config.pool_size,
                    "max_connections": self.config.max_connections,
                    "pool_utilization": (self.results.peak_connections / self.config.max_connections * 100) if self.config.max_connections > 0 else 0
                }
            }
        }
        
        return {
            "benchmark_summary": {
                "performance_grade": performance_grade,
                "test_duration": self.results.test_duration,
                "total_operations": self.results.total_operations,
                "operations_per_second": self.results.operations_per_second,
                "success_rate": success_rate,
                "issues": issues
            },
            "latency_metrics": {
                "min_ms": self.results.min_latency_ms,
                "max_ms": self.results.max_latency_ms,
                "avg_ms": self.results.avg_latency_ms,
                "p50_ms": self.results.p50_latency_ms,
                "p95_ms": self.results.p95_latency_ms,
                "p99_ms": self.results.p99_latency_ms
            },
            "operation_breakdown": {
                "read_operations": self.results.read_operations,
                "write_operations": self.results.write_operations,
                "delete_operations": self.results.delete_operations,
                "read_percentage": (self.results.read_operations / self.results.total_operations * 100) if self.results.total_operations > 0 else 0,
                "write_percentage": (self.results.write_operations / self.results.total_operations * 100) if self.results.total_operations > 0 else 0,
                "delete_percentage": (self.results.delete_operations / self.results.total_operations * 100) if self.results.total_operations > 0 else 0
            },
            "connection_metrics": {
                "peak_connections": self.results.peak_connections,
                "connection_errors": self.results.connection_errors,
                "circuit_breaker_trips": self.results.circuit_breaker_trips,
                "configured_pool_size": self.config.pool_size,
                "max_connections": self.config.max_connections
            },
            "performance_thresholds": {
                "target_latency_ms": self.config.target_latency_ms,
                "max_latency_ms": self.config.max_latency_ms,
                "min_throughput_ops_sec": self.config.min_throughput_ops_sec,
                "latency_violations": sum(1 for r in self.results.operation_results if r.success and r.latency_ms > self.config.target_latency_ms),
                "timeout_violations": sum(1 for r in self.results.operation_results if r.success and r.latency_ms > self.config.max_latency_ms)
            },
            "benchmark_config": {
                "concurrent_operations": self.config.concurrent_operations,
                "operations_per_worker": self.config.operations_per_worker,
                "read_percentage": self.config.read_percentage,
                "write_percentage": self.config.write_percentage,
                "delete_percentage": self.config.delete_percentage,
                "circuit_breaker_testing": self.config.test_circuit_breaker,
                "failure_injection_rate": self.config.failure_injection_rate
            },
            "requirements_validation": requirements_status,
            "timestamp": datetime.now().isoformat()
        }


async def run_redis_benchmark(config: Optional[RedisBenchmarkConfig] = None) -> Dict[str, Any]:
    """Run Redis benchmark and return results."""
    if config is None:
        config = RedisBenchmarkConfig()
    
    benchmark = RedisBenchmark(config)
    
    try:
        await benchmark.setup()
        results = await benchmark.run_benchmark()
        report = benchmark.generate_report()
        return report
    finally:
        await benchmark.cleanup()


if __name__ == "__main__":
    # Example usage
    async def main():
        # Configure benchmark parameters
        config = RedisBenchmarkConfig(
            redis_url="redis://localhost:6379/0",
            concurrent_operations=50,
            operations_per_worker=500,
            read_percentage=70,
            write_percentage=25,
            delete_percentage=5,
            test_circuit_breaker=True,
            failure_injection_rate=0.05  # 5% failure rate
        )
        
        # Run benchmark
        report = await run_redis_benchmark(config)
        
        # Print results
        print("\n" + "="*80)
        print("REDIS PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        print(json.dumps(report, indent=2))
        
        # Performance assessment
        grade = report["benchmark_summary"]["performance_grade"]
        print(f"\nPerformance Grade: {grade}")
        
        if report["benchmark_summary"]["issues"]:
            print("\nIssues Found:")
            for issue in report["benchmark_summary"]["issues"]:
                print(f"  - {issue}")
        
        print("\nRequirements Validation:")
        for req_id, req_data in report["requirements_validation"].items():
            status = req_data["status"]
            desc = req_data["description"]
            print(f"  {req_id}: {status} - {desc}")
    
    # Run the benchmark
    asyncio.run(main())