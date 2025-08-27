"""
Baseline metrics validation script.

This module validates performance improvements against baseline metrics
and provides comprehensive performance comparison reporting.

Requirements tested:
- Validate performance improvements against baseline metrics
- Compare current performance with pre-optimization benchmarks
- Generate performance improvement reports
"""

import asyncio
import json
import time
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from tests.load_testing.webhook_load_test import run_webhook_load_test, LoadTestConfig
from tests.load_testing.redis_benchmark import run_redis_benchmark, RedisBenchmarkConfig
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BaselineMetrics:
    """Baseline performance metrics for comparison."""
    # Webhook performance
    webhook_avg_response_time_ms: float = 2000.0  # Pre-optimization: 2s average
    webhook_p95_response_time_ms: float = 5000.0  # Pre-optimization: 5s P95
    webhook_p99_response_time_ms: float = 14000.0  # Pre-optimization: 14s P99 (reported issue)
    webhook_success_rate: float = 85.0  # Pre-optimization: 85% due to timeouts
    webhook_throughput_rps: float = 10.0  # Pre-optimization: 10 requests/second
    
    # Redis performance
    redis_avg_latency_ms: float = 50.0  # Pre-optimization: 50ms average
    redis_p95_latency_ms: float = 200.0  # Pre-optimization: 200ms P95
    redis_p99_latency_ms: float = 500.0  # Pre-optimization: 500ms P99
    redis_success_rate: float = 70.0  # Pre-optimization: 70% due to connection issues
    redis_throughput_ops: float = 500.0  # Pre-optimization: 500 ops/second
    
    # System metrics
    system_max_concurrent_users: int = 20  # Pre-optimization: 20 concurrent users
    system_memory_usage_mb: float = 800.0  # Pre-optimization: 800MB peak
    system_cpu_usage_percent: float = 90.0  # Pre-optimization: 90% peak CPU
    
    # Error rates
    redis_connection_failure_rate: float = 30.0  # Pre-optimization: 30% connection failures
    webhook_timeout_rate: float = 15.0  # Pre-optimization: 15% timeout rate
    
    # Recovery times
    redis_recovery_time_s: float = 120.0  # Pre-optimization: 2 minutes
    system_recovery_time_s: float = 180.0  # Pre-optimization: 3 minutes


@dataclass
class PerformanceComparison:
    """Performance comparison between baseline and current metrics."""
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percent: float
    improvement_factor: float
    status: str  # "IMPROVED", "DEGRADED", "UNCHANGED"
    target_met: bool = False
    target_value: Optional[float] = None


@dataclass
class ValidationResults:
    """Results from baseline validation."""
    overall_improvement: bool = False
    total_metrics_tested: int = 0
    metrics_improved: int = 0
    metrics_degraded: int = 0
    metrics_unchanged: int = 0
    
    # Performance improvements
    webhook_performance_improved: bool = False
    redis_performance_improved: bool = False
    system_capacity_improved: bool = False
    
    # Detailed comparisons
    comparisons: List[PerformanceComparison] = field(default_factory=list)
    
    # Test results
    webhook_test_results: Optional[Dict[str, Any]] = None
    redis_test_results: Optional[Dict[str, Any]] = None
    capacity_test_results: Optional[Dict[str, Any]] = None


class BaselineValidator:
    """Validator for performance improvements against baseline metrics."""
    
    def __init__(self, baseline: Optional[BaselineMetrics] = None):
        self.baseline = baseline or BaselineMetrics()
        self.results = ValidationResults()
        
    def calculate_improvement(self, baseline_value: float, current_value: float, 
                            lower_is_better: bool = True) -> Tuple[float, float, str]:
        """
        Calculate improvement percentage and factor.
        
        Args:
            baseline_value: Original baseline value
            current_value: Current measured value
            lower_is_better: True if lower values are better (e.g., latency)
            
        Returns:
            Tuple of (improvement_percent, improvement_factor, status)
        """
        if baseline_value == 0:
            return 0.0, 1.0, "UNCHANGED"
        
        if lower_is_better:
            # For metrics where lower is better (latency, error rates)
            improvement_percent = ((baseline_value - current_value) / baseline_value) * 100
            improvement_factor = baseline_value / current_value if current_value > 0 else float('inf')
        else:
            # For metrics where higher is better (throughput, success rate)
            improvement_percent = ((current_value - baseline_value) / baseline_value) * 100
            improvement_factor = current_value / baseline_value if baseline_value > 0 else float('inf')
        
        # Determine status
        if abs(improvement_percent) < 5:  # Less than 5% change
            status = "UNCHANGED"
        elif improvement_percent > 0:
            status = "IMPROVED"
        else:
            status = "DEGRADED"
        
        return improvement_percent, improvement_factor, status
    
    def add_comparison(self, metric_name: str, baseline_value: float, current_value: float,
                      lower_is_better: bool = True, target_value: Optional[float] = None):
        """Add a performance comparison."""
        improvement_percent, improvement_factor, status = self.calculate_improvement(
            baseline_value, current_value, lower_is_better
        )
        
        target_met = False
        if target_value is not None:
            if lower_is_better:
                target_met = current_value <= target_value
            else:
                target_met = current_value >= target_value
        
        comparison = PerformanceComparison(
            metric_name=metric_name,
            baseline_value=baseline_value,
            current_value=current_value,
            improvement_percent=improvement_percent,
            improvement_factor=improvement_factor,
            status=status,
            target_met=target_met,
            target_value=target_value
        )
        
        self.results.comparisons.append(comparison)
        
        # Update counters
        self.results.total_metrics_tested += 1
        if status == "IMPROVED":
            self.results.metrics_improved += 1
        elif status == "DEGRADED":
            self.results.metrics_degraded += 1
        else:
            self.results.metrics_unchanged += 1
    
    async def run_current_performance_tests(self) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        """Run current performance tests to get latest metrics."""
        logger.info("Running current performance tests for baseline comparison...")
        
        # Run webhook load test
        webhook_config = LoadTestConfig(
            concurrent_users=50,
            requests_per_user=20,
            ramp_up_time=10,
            enable_burst_testing=True,
            burst_intensity=100
        )
        webhook_results = await run_webhook_load_test(webhook_config)
        
        # Run Redis benchmark
        redis_config = RedisBenchmarkConfig(
            concurrent_operations=100,
            operations_per_worker=500,
            test_duration=60
        )
        redis_results = await run_redis_benchmark(redis_config)
        
        # Capacity test would be run here if needed
        capacity_results = None
        
        return webhook_results, redis_results, capacity_results
    
    async def validate_against_baseline(self) -> ValidationResults:
        """Validate current performance against baseline metrics."""
        logger.info("Starting baseline validation...")
        
        # Run current performance tests
        webhook_results, redis_results, capacity_results = await self.run_current_performance_tests()
        
        # Store test results
        self.results.webhook_test_results = webhook_results
        self.results.redis_test_results = redis_results
        self.results.capacity_test_results = capacity_results
        
        # Extract current metrics from test results
        webhook_metrics = webhook_results["response_time_metrics"]
        redis_metrics = redis_results["latency_metrics"]
        
        # Webhook performance comparisons
        self.add_comparison(
            "Webhook Average Response Time",
            self.baseline.webhook_avg_response_time_ms,
            webhook_metrics["avg_ms"],
            lower_is_better=True,
            target_value=500.0  # Target: 500ms
        )
        
        self.add_comparison(
            "Webhook P95 Response Time",
            self.baseline.webhook_p95_response_time_ms,
            webhook_metrics["p95_ms"],
            lower_is_better=True,
            target_value=1000.0  # Target: 1s
        )
        
        self.add_comparison(
            "Webhook P99 Response Time",
            self.baseline.webhook_p99_response_time_ms,
            webhook_metrics["p99_ms"],
            lower_is_better=True,
            target_value=2000.0  # Target: 2s (requirement)
        )
        
        self.add_comparison(
            "Webhook Success Rate",
            self.baseline.webhook_success_rate,
            webhook_results["test_summary"]["success_rate"],
            lower_is_better=False,
            target_value=99.0  # Target: 99%
        )
        
        self.add_comparison(
            "Webhook Throughput",
            self.baseline.webhook_throughput_rps,
            webhook_results["test_summary"]["requests_per_second"],
            lower_is_better=False,
            target_value=100.0  # Target: 100 RPS
        )
        
        # Redis performance comparisons
        self.add_comparison(
            "Redis Average Latency",
            self.baseline.redis_avg_latency_ms,
            redis_metrics["avg_ms"],
            lower_is_better=True,
            target_value=5.0  # Target: 5ms
        )
        
        self.add_comparison(
            "Redis P95 Latency",
            self.baseline.redis_p95_latency_ms,
            redis_metrics["p95_ms"],
            lower_is_better=True,
            target_value=20.0  # Target: 20ms
        )
        
        self.add_comparison(
            "Redis P99 Latency",
            self.baseline.redis_p99_latency_ms,
            redis_metrics["p99_ms"],
            lower_is_better=True,
            target_value=50.0  # Target: 50ms
        )
        
        self.add_comparison(
            "Redis Success Rate",
            self.baseline.redis_success_rate,
            redis_results["benchmark_summary"]["success_rate"],
            lower_is_better=False,
            target_value=99.5  # Target: 99.5%
        )
        
        self.add_comparison(
            "Redis Throughput",
            self.baseline.redis_throughput_ops,
            redis_results["benchmark_summary"]["operations_per_second"],
            lower_is_better=False,
            target_value=2000.0  # Target: 2000 ops/sec
        )
        
        # Evaluate overall improvements
        self._evaluate_improvements()
        
        logger.info("Baseline validation completed")
        return self.results
    
    def _evaluate_improvements(self):
        """Evaluate overall improvement status."""
        # Webhook performance evaluation
        webhook_comparisons = [c for c in self.results.comparisons if "Webhook" in c.metric_name]
        webhook_improved = sum(1 for c in webhook_comparisons if c.status == "IMPROVED")
        self.results.webhook_performance_improved = webhook_improved >= len(webhook_comparisons) * 0.7  # 70% improved
        
        # Redis performance evaluation
        redis_comparisons = [c for c in self.results.comparisons if "Redis" in c.metric_name]
        redis_improved = sum(1 for c in redis_comparisons if c.status == "IMPROVED")
        self.results.redis_performance_improved = redis_improved >= len(redis_comparisons) * 0.7  # 70% improved
        
        # Overall improvement evaluation
        total_improved = self.results.metrics_improved
        total_tested = self.results.total_metrics_tested
        
        self.results.overall_improvement = (
            total_improved >= total_tested * 0.6 and  # 60% of metrics improved
            self.results.metrics_degraded <= total_tested * 0.1  # Less than 10% degraded
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive baseline validation report."""
        # Calculate improvement summary
        avg_improvement = statistics.mean([c.improvement_percent for c in self.results.comparisons])
        
        # Find best and worst improvements
        best_improvement = max(self.results.comparisons, key=lambda c: c.improvement_percent, default=None)
        worst_improvement = min(self.results.comparisons, key=lambda c: c.improvement_percent, default=None)
        
        # Count targets met
        targets_met = sum(1 for c in self.results.comparisons if c.target_met)
        targets_total = sum(1 for c in self.results.comparisons if c.target_value is not None)
        
        # Performance grade
        if self.results.overall_improvement and targets_met >= targets_total * 0.8:
            performance_grade = "EXCELLENT"
        elif self.results.overall_improvement:
            performance_grade = "GOOD"
        elif self.results.metrics_improved > self.results.metrics_degraded:
            performance_grade = "FAIR"
        else:
            performance_grade = "POOR"
        
        return {
            "validation_summary": {
                "performance_grade": performance_grade,
                "overall_improvement": self.results.overall_improvement,
                "webhook_performance_improved": self.results.webhook_performance_improved,
                "redis_performance_improved": self.results.redis_performance_improved,
                "system_capacity_improved": self.results.system_capacity_improved,
                "average_improvement_percent": avg_improvement,
                "targets_met": targets_met,
                "targets_total": targets_total,
                "target_achievement_rate": (targets_met / targets_total * 100) if targets_total > 0 else 0
            },
            "metrics_summary": {
                "total_metrics_tested": self.results.total_metrics_tested,
                "metrics_improved": self.results.metrics_improved,
                "metrics_degraded": self.results.metrics_degraded,
                "metrics_unchanged": self.results.metrics_unchanged,
                "improvement_rate": (self.results.metrics_improved / self.results.total_metrics_tested * 100) if self.results.total_metrics_tested > 0 else 0
            },
            "best_improvements": {
                "metric": best_improvement.metric_name if best_improvement else "None",
                "improvement_percent": best_improvement.improvement_percent if best_improvement else 0,
                "improvement_factor": best_improvement.improvement_factor if best_improvement else 1
            },
            "worst_improvements": {
                "metric": worst_improvement.metric_name if worst_improvement else "None",
                "improvement_percent": worst_improvement.improvement_percent if worst_improvement else 0,
                "improvement_factor": worst_improvement.improvement_factor if worst_improvement else 1
            },
            "detailed_comparisons": [
                {
                    "metric_name": c.metric_name,
                    "baseline_value": c.baseline_value,
                    "current_value": c.current_value,
                    "improvement_percent": round(c.improvement_percent, 1),
                    "improvement_factor": round(c.improvement_factor, 2),
                    "status": c.status,
                    "target_met": c.target_met,
                    "target_value": c.target_value
                }
                for c in self.results.comparisons
            ],
            "baseline_metrics": {
                "webhook_avg_response_time_ms": self.baseline.webhook_avg_response_time_ms,
                "webhook_p99_response_time_ms": self.baseline.webhook_p99_response_time_ms,
                "webhook_success_rate": self.baseline.webhook_success_rate,
                "redis_avg_latency_ms": self.baseline.redis_avg_latency_ms,
                "redis_success_rate": self.baseline.redis_success_rate,
                "system_max_concurrent_users": self.baseline.system_max_concurrent_users
            },
            "test_results": {
                "webhook_test_available": self.results.webhook_test_results is not None,
                "redis_test_available": self.results.redis_test_results is not None,
                "capacity_test_available": self.results.capacity_test_results is not None
            },
            "timestamp": datetime.now().isoformat()
        }


async def validate_performance_improvements(baseline: Optional[BaselineMetrics] = None) -> Dict[str, Any]:
    """Validate performance improvements against baseline metrics."""
    validator = BaselineValidator(baseline)
    results = await validator.validate_against_baseline()
    report = validator.generate_report()
    return report


if __name__ == "__main__":
    # Example usage
    async def main():
        # Use default baseline metrics (pre-optimization values)
        baseline = BaselineMetrics()
        
        # Run validation
        report = await validate_performance_improvements(baseline)
        
        # Print results
        print("\n" + "="*80)
        print("BASELINE PERFORMANCE VALIDATION RESULTS")
        print("="*80)
        print(json.dumps(report, indent=2))
        
        # Summary
        summary = report["validation_summary"]
        print(f"\nPerformance Grade: {summary['performance_grade']}")
        print(f"Overall Improvement: {summary['overall_improvement']}")
        print(f"Average Improvement: {summary['average_improvement_percent']:.1f}%")
        print(f"Targets Met: {summary['targets_met']}/{summary['targets_total']} ({summary['target_achievement_rate']:.1f}%)")
        
        print("\nKey Improvements:")
        for comparison in report["detailed_comparisons"]:
            if comparison["status"] == "IMPROVED":
                print(f"  - {comparison['metric_name']}: {comparison['improvement_percent']:.1f}% improvement")
        
        print("\nAreas Needing Attention:")
        for comparison in report["detailed_comparisons"]:
            if comparison["status"] == "DEGRADED":
                print(f"  - {comparison['metric_name']}: {abs(comparison['improvement_percent']):.1f}% degradation")
    
    # Run the validation
    asyncio.run(main())