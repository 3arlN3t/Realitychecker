# Redis Performance Optimization - Load Testing Suite

This directory contains comprehensive load testing and benchmarking scripts to validate the Redis performance optimization implementation for the Reality Checker WhatsApp bot.

## Overview

The load testing suite validates the following requirements:
- **4.1**: Webhook response time tracking with detailed timing breakdowns
- **4.2**: Redis operation monitoring with latency measurements  
- **4.3**: Performance threshold alerts for critical metrics
- **5.1**: Connection pool management optimization
- **5.2**: Connection pool utilization monitoring

## Test Components

### 1. Webhook Load Testing (`webhook_load_test.py`)

Tests concurrent webhook processing to validate sub-2-second response times.

**Features:**
- Concurrent user simulation (configurable load levels)
- Realistic Twilio webhook request generation
- Burst testing for peak load scenarios
- Response time percentile analysis (P50, P95, P99)
- Success rate monitoring
- Performance threshold validation

**Key Metrics:**
- Target response time: 500ms (Requirement 2.2)
- Maximum response time: 2000ms (Requirement 2.1)
- Success rate threshold: 99%

### 2. Redis Benchmarking (`redis_benchmark.py`)

Comprehensive Redis performance testing under high throughput.

**Features:**
- Mixed operation workload (read/write/delete)
- Circuit breaker testing with failure injection
- Connection pool utilization monitoring
- Latency distribution analysis
- Throughput measurement
- Connection health monitoring

**Key Metrics:**
- Target latency: 5ms average
- Maximum latency: 50ms P99
- Minimum throughput: 1000 ops/second

### 3. System Capacity Testing (`system_capacity_test.py`)

Tests system behavior at capacity limits and during failures.

**Features:**
- Load progression testing to find capacity limits
- Failure scenario simulation (Redis/database outages)
- Recovery time measurement
- Resource utilization monitoring (CPU, memory)
- Graceful degradation validation
- Backpressure detection

**Key Metrics:**
- Maximum concurrent load capacity
- Recovery time under 60 seconds
- Success rate during failures > 90%

### 4. Baseline Validation (`baseline_metrics.py`)

Validates performance improvements against pre-optimization baseline.

**Features:**
- Performance comparison with baseline metrics
- Improvement percentage calculation
- Target achievement validation
- Regression detection
- Comprehensive improvement reporting

**Baseline Metrics (Pre-optimization):**
- Webhook P99 response time: 14+ seconds (reported issue)
- Redis connection failure rate: 30%
- System capacity: 20 concurrent users

## Usage

### Quick Start

Run all performance tests:
```bash
python tests/load_testing/run_performance_tests.py
```

### Individual Test Types

Run specific test categories:
```bash
# Webhook load testing only
python tests/load_testing/run_performance_tests.py --test-type webhook

# Redis benchmarking only  
python tests/load_testing/run_performance_tests.py --test-type redis

# System capacity testing only
python tests/load_testing/run_performance_tests.py --test-type capacity

# Baseline validation only
python tests/load_testing/run_performance_tests.py --test-type baseline
```

### Save Results

Save detailed results to JSON file:
```bash
python tests/load_testing/run_performance_tests.py --output-file results/performance_test_results.json
```

### Verbose Output

Enable detailed logging:
```bash
python tests/load_testing/run_performance_tests.py --verbose
```

## Configuration

### Webhook Load Test Configuration

```python
config = LoadTestConfig(
    concurrent_users=50,        # Number of concurrent users
    requests_per_user=20,       # Requests per user
    ramp_up_time=10,           # Ramp-up time in seconds
    enable_burst_testing=True,  # Enable burst load testing
    burst_intensity=100,        # Concurrent requests in burst
    target_response_time_ms=500.0,  # Target response time
    max_response_time_ms=2000.0     # Maximum acceptable response time
)
```

### Redis Benchmark Configuration

```python
config = RedisBenchmarkConfig(
    concurrent_operations=100,      # Concurrent Redis operations
    operations_per_worker=1000,     # Operations per worker
    read_percentage=70,             # Read operation percentage
    write_percentage=25,            # Write operation percentage
    delete_percentage=5,            # Delete operation percentage
    test_circuit_breaker=True,      # Test circuit breaker
    failure_injection_rate=0.1      # Failure injection rate (10%)
)
```

### System Capacity Configuration

```python
config = CapacityTestConfig(
    max_concurrent_requests=500,    # Maximum concurrent requests
    load_ramp_steps=[10, 25, 50, 100, 200, 500],  # Load progression
    step_duration=30,               # Duration per load step
    enable_redis_failure=True,      # Test Redis failure scenarios
    enable_database_failure=True,   # Test database failure scenarios
    test_recovery=True              # Test recovery capabilities
)
```

## Test Results

### Performance Grades

- **EXCELLENT**: All targets met, significant improvements
- **GOOD**: Most targets met, good improvements
- **FAIR**: Mixed results, some improvements
- **POOR**: Below expectations, issues need attention

### Key Metrics Tracked

1. **Response Time Metrics**
   - Average, P50, P95, P99 response times
   - Target achievement rates
   - Timeout violations

2. **Throughput Metrics**
   - Requests per second (webhook)
   - Operations per second (Redis)
   - Concurrent user capacity

3. **Reliability Metrics**
   - Success rates
   - Error rates
   - Recovery times

4. **Resource Utilization**
   - CPU usage
   - Memory usage
   - Connection pool utilization

## Requirements Validation

The test suite validates specific requirements:

| Requirement | Test Component | Validation Method |
|-------------|----------------|-------------------|
| 4.1 | Webhook Load Test | Response time tracking and breakdown analysis |
| 4.2 | Redis Benchmark | Operation latency measurement and monitoring |
| 4.3 | Capacity Test | Performance threshold alerts and violations |
| 5.1 | Redis Benchmark + Capacity | Connection pool management under load |
| 5.2 | Capacity Test | Connection pool utilization monitoring |

## Expected Improvements

Based on the optimization implementation, expected improvements include:

1. **Webhook Performance**
   - 85% reduction in P99 response time (14s → 2s)
   - 75% reduction in average response time (2s → 500ms)
   - 14% improvement in success rate (85% → 99%)

2. **Redis Performance**
   - 90% reduction in average latency (50ms → 5ms)
   - 75% reduction in P95 latency (200ms → 50ms)
   - 29% improvement in success rate (70% → 99%)

3. **System Capacity**
   - 25x increase in concurrent user capacity (20 → 500)
   - 50% reduction in recovery time (120s → 60s)
   - Improved failure resilience

## Troubleshooting

### Common Issues

1. **Connection Refused Errors**
   - Ensure the application is running on localhost:8000
   - Check Redis is running on localhost:6379

2. **High Response Times**
   - Check system resources (CPU, memory)
   - Verify Redis connectivity
   - Review application logs

3. **Test Failures**
   - Check application configuration
   - Verify all dependencies are installed
   - Review error logs for specific issues

### Debug Mode

Enable verbose logging for detailed debugging:
```bash
python tests/load_testing/run_performance_tests.py --verbose
```

## Integration with CI/CD

The test suite can be integrated into CI/CD pipelines:

```bash
# Run performance tests and fail if grade is POOR
python tests/load_testing/run_performance_tests.py --output-file results.json
exit_code=$?

if [ $exit_code -eq 2 ]; then
    echo "Performance tests failed with POOR grade"
    exit 1
fi
```

Exit codes:
- 0: EXCELLENT or GOOD grade
- 1: FAIR grade  
- 2: POOR grade
- 130: Interrupted by user

## Contributing

When adding new performance tests:

1. Follow the existing pattern of configuration dataclasses
2. Include comprehensive error handling
3. Add detailed logging and metrics collection
4. Validate against specific requirements
5. Update this README with new test descriptions