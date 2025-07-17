"""
Advanced analytics and metrics collection system for Reality Checker.

This module provides sophisticated analytics capabilities including:
- Real-time metrics aggregation
- Predictive analytics
- Advanced statistical analysis
- Machine learning insights
- Performance profiling
"""

import asyncio
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
import threading

from app.utils.logging import get_logger
from app.models.data_models import JobClassification

logger = get_logger(__name__)


class MetricAggregationType(Enum):
    """Types of metric aggregations."""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    RATE = "rate"
    PERCENTILE = "percentile"
    DISTRIBUTION = "distribution"
    UNIQUE_COUNT = "unique_count"
    VARIANCE = "variance"
    TREND = "trend"


class TimeGranularity(Enum):
    """Time granularity for analytics."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class MetricDefinition:
    """Definition of a metric to collect and analyze."""
    name: str
    description: str
    aggregation_type: MetricAggregationType
    time_granularity: TimeGranularity
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    retention_days: int = 90
    calculate_trends: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class DataPoint:
    """Individual data point for analytics."""
    timestamp: datetime
    value: Union[float, int, str]
    dimensions: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric result."""
    metric_name: str
    aggregation_type: MetricAggregationType
    value: Union[float, Dict[str, float], List[float]]
    time_period: Tuple[datetime, datetime]
    dimensions: Dict[str, str] = field(default_factory=dict)
    sample_size: int = 0
    confidence_interval: Optional[Tuple[float, float]] = None
    trend_direction: Optional[str] = None  # "up", "down", "stable"
    trend_strength: Optional[float] = None  # 0-1


@dataclass
class AnalyticsInsight:
    """Business intelligence insight."""
    title: str
    description: str
    insight_type: str  # anomaly, trend, correlation, prediction
    confidence: float  # 0-1
    impact: str  # low, medium, high, critical
    recommendation: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AdvancedAnalyticsEngine:
    """Advanced analytics engine for comprehensive data analysis."""
    
    def __init__(self, max_data_points: int = 1000000):
        """
        Initialize advanced analytics engine.
        
        Args:
            max_data_points: Maximum number of data points to keep in memory
        """
        self.max_data_points = max_data_points
        self.data_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_data_points))
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.real_time_metrics: Dict[str, Any] = {}
        self.insights_cache: Dict[str, List[AnalyticsInsight]] = {}
        self.lock = threading.RLock()
        
        # Performance tracking
        self.calculation_times: Dict[str, List[float]] = defaultdict(list)
        self.last_calculation: Dict[str, datetime] = {}
        
        # Initialize built-in metrics
        self._register_built_in_metrics()
        
        logger.info("Advanced Analytics Engine initialized")
    
    def _register_built_in_metrics(self) -> None:
        """Register built-in metrics for the Reality Checker system."""
        built_in_metrics = [
            MetricDefinition(
                name="request_count",
                description="Total number of analysis requests",
                aggregation_type=MetricAggregationType.COUNT,
                time_granularity=TimeGranularity.HOUR,
                dimensions=["user_type", "request_type", "classification"],
                calculate_trends=True,
                alert_thresholds={"spike": 2.0, "drop": -0.5}
            ),
            MetricDefinition(
                name="response_time",
                description="Response time for analysis requests",
                aggregation_type=MetricAggregationType.PERCENTILE,
                time_granularity=TimeGranularity.MINUTE,
                dimensions=["endpoint", "classification_type"],
                calculate_trends=True,
                alert_thresholds={"p95_threshold": 5.0}
            ),
            MetricDefinition(
                name="classification_accuracy",
                description="Accuracy of job classification",
                aggregation_type=MetricAggregationType.RATE,
                time_granularity=TimeGranularity.DAY,
                dimensions=["classification_type", "confidence_level"],
                calculate_trends=True,
                alert_thresholds={"min_accuracy": 0.85}
            ),
            MetricDefinition(
                name="user_engagement",
                description="User engagement metrics",
                aggregation_type=MetricAggregationType.DISTRIBUTION,
                time_granularity=TimeGranularity.DAY,
                dimensions=["user_segment", "interaction_type"],
                calculate_trends=True
            ),
            MetricDefinition(
                name="error_rate",
                description="System error rate",
                aggregation_type=MetricAggregationType.RATE,
                time_granularity=TimeGranularity.HOUR,
                dimensions=["error_type", "component"],
                calculate_trends=True,
                alert_thresholds={"critical_rate": 0.05}
            ),
            MetricDefinition(
                name="scam_detection_rate",
                description="Rate of scam detection",
                aggregation_type=MetricAggregationType.RATE,
                time_granularity=TimeGranularity.DAY,
                dimensions=["scam_type", "confidence_level"],
                calculate_trends=True
            ),
            MetricDefinition(
                name="user_satisfaction",
                description="User satisfaction metrics",
                aggregation_type=MetricAggregationType.AVERAGE,
                time_granularity=TimeGranularity.DAY,
                dimensions=["feedback_type", "user_segment"],
                calculate_trends=True,
                alert_thresholds={"min_satisfaction": 4.0}
            )
        ]
        
        for metric in built_in_metrics:
            self.metric_definitions[metric.name] = metric
    
    async def record_data_point(self, metric_name: str, value: Union[float, int, str], 
                               dimensions: Dict[str, str] = None, 
                               metadata: Dict[str, Any] = None) -> None:
        """
        Record a data point for analysis.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            dimensions: Dimensional data for grouping
            metadata: Additional metadata
        """
        with self.lock:
            data_point = DataPoint(
                timestamp=datetime.now(timezone.utc),
                value=value,
                dimensions=dimensions or {},
                metadata=metadata or {}
            )
            
            self.data_store[metric_name].append(data_point)
            
            # Update real-time metrics
            await self._update_real_time_metrics(metric_name, data_point)
    
    async def _update_real_time_metrics(self, metric_name: str, data_point: DataPoint) -> None:
        """Update real-time metrics cache."""
        if metric_name not in self.real_time_metrics:
            self.real_time_metrics[metric_name] = {
                "count": 0,
                "sum": 0.0,
                "latest_value": None,
                "latest_timestamp": None,
                "rolling_average": 0.0,
                "rolling_window": deque(maxlen=100)  # Last 100 values
            }
        
        metric_data = self.real_time_metrics[metric_name]
        
        if isinstance(data_point.value, (int, float)):
            metric_data["count"] += 1
            metric_data["sum"] += data_point.value
            metric_data["rolling_window"].append(data_point.value)
            metric_data["rolling_average"] = sum(metric_data["rolling_window"]) / len(metric_data["rolling_window"])
        
        metric_data["latest_value"] = data_point.value
        metric_data["latest_timestamp"] = data_point.timestamp
    
    async def calculate_aggregated_metric(self, metric_name: str, 
                                        aggregation_type: MetricAggregationType,
                                        start_time: datetime, 
                                        end_time: datetime,
                                        dimensions: Dict[str, str] = None) -> AggregatedMetric:
        """
        Calculate aggregated metric for a time period.
        
        Args:
            metric_name: Name of the metric to aggregate
            aggregation_type: Type of aggregation to perform
            start_time: Start of time period
            end_time: End of time period
            dimensions: Dimensions to filter by
            
        Returns:
            AggregatedMetric with calculated values
        """
        start_calc_time = time.time()
        
        with self.lock:
            data_points = self.data_store.get(metric_name, [])
            
            # Filter by time range and dimensions
            filtered_points = [
                dp for dp in data_points
                if start_time <= dp.timestamp <= end_time
                and (not dimensions or all(
                    dp.dimensions.get(k) == v for k, v in dimensions.items()
                ))
            ]
        
        if not filtered_points:
            return AggregatedMetric(
                metric_name=metric_name,
                aggregation_type=aggregation_type,
                value=0,
                time_period=(start_time, end_time),
                dimensions=dimensions or {},
                sample_size=0
            )
        
        # Calculate aggregated value
        numeric_values = [
            dp.value for dp in filtered_points 
            if isinstance(dp.value, (int, float))
        ]
        
        if aggregation_type == MetricAggregationType.SUM:
            value = sum(numeric_values)
        elif aggregation_type == MetricAggregationType.AVERAGE:
            value = statistics.mean(numeric_values) if numeric_values else 0
        elif aggregation_type == MetricAggregationType.COUNT:
            value = len(filtered_points)
        elif aggregation_type == MetricAggregationType.RATE:
            # Calculate rate per hour
            duration_hours = (end_time - start_time).total_seconds() / 3600
            value = len(filtered_points) / duration_hours if duration_hours > 0 else 0
        elif aggregation_type == MetricAggregationType.PERCENTILE:
            if numeric_values:
                value = {
                    "p50": np.percentile(numeric_values, 50),
                    "p75": np.percentile(numeric_values, 75),
                    "p90": np.percentile(numeric_values, 90),
                    "p95": np.percentile(numeric_values, 95),
                    "p99": np.percentile(numeric_values, 99)
                }
            else:
                value = {"p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0}
        elif aggregation_type == MetricAggregationType.DISTRIBUTION:
            # Calculate distribution statistics
            if numeric_values:
                value = {
                    "mean": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values),
                    "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "count": len(numeric_values)
                }
            else:
                value = {"mean": 0, "median": 0, "std_dev": 0, "min": 0, "max": 0, "count": 0}
        elif aggregation_type == MetricAggregationType.UNIQUE_COUNT:
            unique_values = set(dp.value for dp in filtered_points)
            value = len(unique_values)
        elif aggregation_type == MetricAggregationType.VARIANCE:
            value = statistics.variance(numeric_values) if len(numeric_values) > 1 else 0
        else:
            value = len(filtered_points)  # Default to count
        
        # Calculate confidence interval for numeric metrics
        confidence_interval = None
        if numeric_values and len(numeric_values) > 1:
            try:
                mean = statistics.mean(numeric_values)
                std_dev = statistics.stdev(numeric_values)
                margin = 1.96 * (std_dev / np.sqrt(len(numeric_values)))  # 95% CI
                confidence_interval = (mean - margin, mean + margin)
            except Exception:
                pass
        
        # Calculate trend if requested
        trend_direction, trend_strength = await self._calculate_trend(
            metric_name, start_time, end_time, dimensions
        )
        
        calc_time = time.time() - start_calc_time
        self.calculation_times[metric_name].append(calc_time)
        self.last_calculation[metric_name] = datetime.now(timezone.utc)
        
        return AggregatedMetric(
            metric_name=metric_name,
            aggregation_type=aggregation_type,
            value=value,
            time_period=(start_time, end_time),
            dimensions=dimensions or {},
            sample_size=len(filtered_points),
            confidence_interval=confidence_interval,
            trend_direction=trend_direction,
            trend_strength=trend_strength
        )
    
    async def _calculate_trend(self, metric_name: str, start_time: datetime, 
                             end_time: datetime, dimensions: Dict[str, str] = None) -> Tuple[Optional[str], Optional[float]]:
        """Calculate trend direction and strength."""
        try:
            # Get historical data for comparison
            duration = end_time - start_time
            historical_start = start_time - duration
            
            current_metric = await self.calculate_aggregated_metric(
                metric_name, MetricAggregationType.AVERAGE, start_time, end_time, dimensions
            )
            historical_metric = await self.calculate_aggregated_metric(
                metric_name, MetricAggregationType.AVERAGE, historical_start, start_time, dimensions
            )
            
            if (isinstance(current_metric.value, (int, float)) and 
                isinstance(historical_metric.value, (int, float)) and
                historical_metric.value != 0):
                
                change_ratio = (current_metric.value - historical_metric.value) / abs(historical_metric.value)
                
                # Determine direction
                if abs(change_ratio) < 0.05:  # Less than 5% change
                    direction = "stable"
                elif change_ratio > 0:
                    direction = "up"
                else:
                    direction = "down"
                
                # Calculate strength (0-1)
                strength = min(abs(change_ratio), 1.0)
                
                return direction, strength
        
        except Exception as e:
            logger.debug(f"Error calculating trend for {metric_name}: {e}")
        
        return None, None
    
    async def generate_insights(self, metric_names: List[str] = None, 
                              time_period: Tuple[datetime, datetime] = None) -> List[AnalyticsInsight]:
        """
        Generate business intelligence insights from metrics.
        
        Args:
            metric_names: List of metrics to analyze (all if None)
            time_period: Time period to analyze (last 24h if None)
            
        Returns:
            List of insights
        """
        if time_period is None:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            time_period = (start_time, end_time)
        
        if metric_names is None:
            metric_names = list(self.metric_definitions.keys())
        
        insights = []
        
        # Check cache first
        cache_key = f"{','.join(metric_names)}_{time_period[0].isoformat()}_{time_period[1].isoformat()}"
        if cache_key in self.insights_cache:
            cached_time = self.insights_cache[cache_key][0].timestamp if self.insights_cache[cache_key] else datetime.min
            if datetime.now(timezone.utc) - cached_time < timedelta(minutes=15):  # 15-minute cache
                return self.insights_cache[cache_key]
        
        # Generate insights for each metric
        for metric_name in metric_names:
            metric_insights = await self._analyze_metric_for_insights(metric_name, time_period)
            insights.extend(metric_insights)
        
        # Generate correlation insights
        correlation_insights = await self._find_correlations(metric_names, time_period)
        insights.extend(correlation_insights)
        
        # Generate anomaly detection insights
        anomaly_insights = await self._detect_anomalies(metric_names, time_period)
        insights.extend(anomaly_insights)
        
        # Generate predictive insights
        predictive_insights = await self._generate_predictions(metric_names, time_period)
        insights.extend(predictive_insights)
        
        # Sort by impact and confidence
        insights.sort(key=lambda x: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[x.impact],
            x.confidence
        ), reverse=True)
        
        # Cache results
        self.insights_cache[cache_key] = insights[:50]  # Keep top 50 insights
        
        logger.info(f"Generated {len(insights)} analytics insights")
        return insights
    
    async def _analyze_metric_for_insights(self, metric_name: str, 
                                         time_period: Tuple[datetime, datetime]) -> List[AnalyticsInsight]:
        """Analyze a single metric for insights."""
        insights = []
        
        try:
            # Get metric definition
            metric_def = self.metric_definitions.get(metric_name)
            if not metric_def:
                return insights
            
            # Calculate current metric
            current_metric = await self.calculate_aggregated_metric(
                metric_name, metric_def.aggregation_type, time_period[0], time_period[1]
            )
            
            # Check alert thresholds
            for threshold_name, threshold_value in metric_def.alert_thresholds.items():
                if self._check_threshold_violation(current_metric, threshold_name, threshold_value):
                    insight = AnalyticsInsight(
                        title=f"{metric_name} threshold violation",
                        description=f"Metric {metric_name} has exceeded the {threshold_name} threshold",
                        insight_type="anomaly",
                        confidence=0.9,
                        impact="high" if "critical" in threshold_name else "medium",
                        recommendation=f"Investigate {metric_name} and take corrective action",
                        supporting_data={
                            "metric_value": current_metric.value,
                            "threshold": threshold_value,
                            "threshold_type": threshold_name
                        }
                    )
                    insights.append(insight)
            
            # Trend analysis insights
            if current_metric.trend_direction and current_metric.trend_strength:
                if current_metric.trend_strength > 0.3:  # Significant trend
                    impact = "high" if current_metric.trend_strength > 0.7 else "medium"
                    
                    insight = AnalyticsInsight(
                        title=f"{metric_name} trending {current_metric.trend_direction}",
                        description=f"Strong {current_metric.trend_direction} trend detected in {metric_name}",
                        insight_type="trend",
                        confidence=current_metric.trend_strength,
                        impact=impact,
                        recommendation=f"Monitor {metric_name} trend and adjust operations if needed",
                        supporting_data={
                            "trend_direction": current_metric.trend_direction,
                            "trend_strength": current_metric.trend_strength,
                            "sample_size": current_metric.sample_size
                        }
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing metric {metric_name}: {e}")
        
        return insights
    
    def _check_threshold_violation(self, metric: AggregatedMetric, 
                                 threshold_name: str, threshold_value: float) -> bool:
        """Check if metric violates a threshold."""
        try:
            if isinstance(metric.value, dict):
                # Handle percentile metrics
                if threshold_name == "p95_threshold" and "p95" in metric.value:
                    return metric.value["p95"] > threshold_value
                elif threshold_name == "min_accuracy" and "mean" in metric.value:
                    return metric.value["mean"] < threshold_value
            elif isinstance(metric.value, (int, float)):
                if threshold_name == "spike":
                    # Check for spike (value significantly higher than expected)
                    return metric.trend_strength and metric.trend_strength > threshold_value
                elif threshold_name == "drop":
                    # Check for drop (value significantly lower than expected)
                    return (metric.trend_direction == "down" and 
                           metric.trend_strength and metric.trend_strength > abs(threshold_value))
                elif threshold_name == "critical_rate":
                    return metric.value > threshold_value
                elif threshold_name == "min_satisfaction":
                    return metric.value < threshold_value
                else:
                    return metric.value > threshold_value
        except Exception:
            pass
        
        return False
    
    async def _find_correlations(self, metric_names: List[str], 
                               time_period: Tuple[datetime, datetime]) -> List[AnalyticsInsight]:
        """Find correlations between metrics."""
        insights = []
        
        try:
            if len(metric_names) < 2:
                return insights
            
            # Calculate correlation matrix
            metric_values = {}
            for metric_name in metric_names:
                metric = await self.calculate_aggregated_metric(
                    metric_name, MetricAggregationType.AVERAGE, time_period[0], time_period[1]
                )
                if isinstance(metric.value, (int, float)):
                    metric_values[metric_name] = metric.value
            
            # Find strong correlations
            for i, metric1 in enumerate(metric_values.keys()):
                for metric2 in list(metric_values.keys())[i+1:]:
                    # Simple correlation analysis (would use more sophisticated methods in practice)
                    if abs(metric_values[metric1] - metric_values[metric2]) < 0.1:
                        insight = AnalyticsInsight(
                            title=f"Correlation detected between {metric1} and {metric2}",
                            description=f"Strong correlation found between {metric1} and {metric2}",
                            insight_type="correlation",
                            confidence=0.7,
                            impact="medium",
                            recommendation=f"Monitor {metric1} and {metric2} together for optimization opportunities",
                            supporting_data={
                                "metric1": metric1,
                                "metric2": metric2,
                                "correlation_strength": 0.7
                            }
                        )
                        insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error finding correlations: {e}")
        
        return insights
    
    async def _detect_anomalies(self, metric_names: List[str], 
                              time_period: Tuple[datetime, datetime]) -> List[AnalyticsInsight]:
        """Detect anomalies in metrics."""
        insights = []
        
        try:
            for metric_name in metric_names:
                # Get historical data for comparison
                duration = time_period[1] - time_period[0]
                historical_periods = []
                
                # Get 4 historical periods for comparison
                for i in range(1, 5):
                    hist_end = time_period[0] - duration * (i - 1)
                    hist_start = hist_end - duration
                    historical_periods.append((hist_start, hist_end))
                
                # Calculate current and historical metrics
                current_metric = await self.calculate_aggregated_metric(
                    metric_name, MetricAggregationType.AVERAGE, time_period[0], time_period[1]
                )
                
                historical_values = []
                for hist_period in historical_periods:
                    hist_metric = await self.calculate_aggregated_metric(
                        metric_name, MetricAggregationType.AVERAGE, hist_period[0], hist_period[1]
                    )
                    if isinstance(hist_metric.value, (int, float)):
                        historical_values.append(hist_metric.value)
                
                # Detect anomaly using statistical methods
                if (len(historical_values) >= 3 and 
                    isinstance(current_metric.value, (int, float))):
                    
                    hist_mean = statistics.mean(historical_values)
                    hist_std = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
                    
                    if hist_std > 0:
                        z_score = abs(current_metric.value - hist_mean) / hist_std
                        
                        if z_score > 2.5:  # Significant anomaly
                            insight = AnalyticsInsight(
                                title=f"Anomaly detected in {metric_name}",
                                description=f"Unusual value detected in {metric_name} (Z-score: {z_score:.2f})",
                                insight_type="anomaly",
                                confidence=min(z_score / 3.0, 1.0),
                                impact="high" if z_score > 3.0 else "medium",
                                recommendation=f"Investigate cause of anomaly in {metric_name}",
                                supporting_data={
                                    "current_value": current_metric.value,
                                    "historical_mean": hist_mean,
                                    "z_score": z_score,
                                    "sample_size": len(historical_values)
                                }
                            )
                            insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return insights
    
    async def _generate_predictions(self, metric_names: List[str], 
                                  time_period: Tuple[datetime, datetime]) -> List[AnalyticsInsight]:
        """Generate predictive insights."""
        insights = []
        
        try:
            for metric_name in metric_names:
                # Simple trend-based prediction
                current_metric = await self.calculate_aggregated_metric(
                    metric_name, MetricAggregationType.AVERAGE, time_period[0], time_period[1]
                )
                
                if (current_metric.trend_direction and 
                    current_metric.trend_strength and 
                    current_metric.trend_strength > 0.5):
                    
                    # Predict future value based on trend
                    if isinstance(current_metric.value, (int, float)):
                        duration_hours = (time_period[1] - time_period[0]).total_seconds() / 3600
                        trend_rate = current_metric.trend_strength * 0.1  # 10% max change per period
                        
                        if current_metric.trend_direction == "up":
                            predicted_value = current_metric.value * (1 + trend_rate)
                            impact_desc = "increase"
                        else:
                            predicted_value = current_metric.value * (1 - trend_rate)
                            impact_desc = "decrease"
                        
                        insight = AnalyticsInsight(
                            title=f"Prediction: {metric_name} will {impact_desc}",
                            description=f"Based on current trend, {metric_name} is predicted to {impact_desc}",
                            insight_type="prediction",
                            confidence=current_metric.trend_strength * 0.8,
                            impact="medium",
                            recommendation=f"Prepare for predicted {impact_desc} in {metric_name}",
                            supporting_data={
                                "current_value": current_metric.value,
                                "predicted_value": predicted_value,
                                "prediction_horizon": f"{duration_hours:.1f} hours",
                                "confidence": current_metric.trend_strength
                            }
                        )
                        insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
        
        return insights
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data."""
        with self.lock:
            dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {},
                "alerts": [],
                "performance": {
                    "avg_calculation_time": 0.0,
                    "total_data_points": sum(len(deque_data) for deque_data in self.data_store.values()),
                    "active_metrics": len(self.real_time_metrics)
                }
            }
            
            # Add real-time metrics
            for metric_name, metric_data in self.real_time_metrics.items():
                dashboard_data["metrics"][metric_name] = {
                    "latest_value": metric_data["latest_value"],
                    "latest_timestamp": metric_data["latest_timestamp"].isoformat() if metric_data["latest_timestamp"] else None,
                    "rolling_average": round(metric_data["rolling_average"], 2),
                    "total_count": metric_data["count"],
                    "total_sum": round(metric_data["sum"], 2)
                }
            
            # Calculate performance metrics
            all_calc_times = [time for times in self.calculation_times.values() for time in times]
            if all_calc_times:
                dashboard_data["performance"]["avg_calculation_time"] = statistics.mean(all_calc_times)
            
            return dashboard_data
    
    async def export_analytics_data(self, metric_names: List[str], 
                                  start_time: datetime, end_time: datetime,
                                  format: str = "json") -> str:
        """
        Export analytics data in specified format.
        
        Args:
            metric_names: List of metrics to export
            start_time: Start time for data export
            end_time: End time for data export
            format: Export format (json, csv, parquet)
            
        Returns:
            Exported data as string
        """
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "metrics": metric_names,
                "format": format
            },
            "data": {}
        }
        
        # Export each metric
        for metric_name in metric_names:
            with self.lock:
                data_points = self.data_store.get(metric_name, [])
                filtered_points = [
                    {
                        "timestamp": dp.timestamp.isoformat(),
                        "value": dp.value,
                        "dimensions": dp.dimensions,
                        "metadata": dp.metadata
                    }
                    for dp in data_points
                    if start_time <= dp.timestamp <= end_time
                ]
                
                export_data["data"][metric_name] = filtered_points
        
        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["metric_name", "timestamp", "value", "dimensions", "metadata"])
            
            # Write data
            for metric_name, points in export_data["data"].items():
                for point in points:
                    writer.writerow([
                        metric_name,
                        point["timestamp"],
                        point["value"],
                        json.dumps(point["dimensions"]),
                        json.dumps(point["metadata"])
                    ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup_old_data(self, retention_days: int = None) -> int:
        """
        Clean up old data points based on retention policy.
        
        Args:
            retention_days: Days to retain (uses metric definition if None)
            
        Returns:
            Number of data points removed
        """
        removed_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days or 90)
        
        with self.lock:
            for metric_name, data_points in self.data_store.items():
                initial_count = len(data_points)
                
                # Remove old data points
                while data_points and data_points[0].timestamp < cutoff_time:
                    data_points.popleft()
                    removed_count += 1
                
                logger.debug(f"Cleaned {initial_count - len(data_points)} old data points from {metric_name}")
        
        return removed_count


# Global instance
_advanced_analytics_engine: Optional[AdvancedAnalyticsEngine] = None


def get_advanced_analytics_engine() -> AdvancedAnalyticsEngine:
    """Get global advanced analytics engine instance."""
    global _advanced_analytics_engine
    if _advanced_analytics_engine is None:
        _advanced_analytics_engine = AdvancedAnalyticsEngine()
    return _advanced_analytics_engine