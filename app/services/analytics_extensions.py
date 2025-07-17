"""
Extensions to the AnalyticsService class for advanced analytics features.

This module provides additional methods for the AnalyticsService class to support:
- Time series data retrieval
- Report storage and retrieval
- Integration with advanced analytics engines
"""

import logging
import os
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import json

from app.models.data_models import (
    ReportData, ReportParameters, UserDetails, UserInteraction
)
from app.utils.logging import get_logger, log_with_context
from app.utils.advanced_analytics import AdvancedAnalyticsEngine
from app.utils.pattern_recognition import PatternRecognitionEngine
from app.utils.reporting_engine import ReportingEngine

logger = get_logger(__name__)


class AnalyticsServiceExtensions:
    """
    Extensions to the AnalyticsService class for advanced analytics.
    
    This class is designed to be mixed into the AnalyticsService class.
    """
    
    def __init__(self):
        """Initialize analytics service extensions."""
        self.reports_dir = os.path.join(tempfile.gettempdir(), "reality_checker_reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        self.stored_reports: Dict[str, ReportData] = {}
        self.advanced_analytics_engine = AdvancedAnalyticsEngine()
        self.pattern_engine = PatternRecognitionEngine()
        self.reporting_engine = ReportingEngine(self.reports_dir)
        
        logger.info("AnalyticsServiceExtensions initialized")
    
    async def get_metric_time_series(self, 
                                   metric_name: str,
                                   start_date: datetime,
                                   end_date: datetime,
                                   dimensions: Dict[str, str] = None) -> List[Tuple[datetime, float]]:
        """
        Get time series data for a specific metric.
        
        Args:
            metric_name: Name of the metric
            start_date: Start date for the time series
            end_date: End date for the time series
            dimensions: Optional dimensions for filtering
            
        Returns:
            List of (timestamp, value) tuples
        """
        try:
            # This is a simplified implementation that generates mock data
            # In a real implementation, you would retrieve actual time series data
            
            # Get all users and their interactions
            user_list = await self.user_service.get_users(page=1, limit=10000)
            
            # Generate time series based on metric name
            time_series = []
            
            if metric_name == "requests_count":
                # Count requests per hour
                current_time = start_date
                while current_time <= end_date:
                    next_time = current_time + timedelta(hours=1)
                    count = 0
                    
                    for user in user_list.users:
                        for interaction in user.interaction_history:
                            if current_time <= interaction.timestamp < next_time:
                                count += 1
                    
                    time_series.append((current_time, float(count)))
                    current_time = next_time
            
            elif metric_name == "response_time":
                # Average response time per hour
                current_time = start_date
                while current_time <= end_date:
                    next_time = current_time + timedelta(hours=1)
                    response_times = []
                    
                    for user in user_list.users:
                        for interaction in user.interaction_history:
                            if current_time <= interaction.timestamp < next_time and interaction.response_time > 0:
                                response_times.append(interaction.response_time)
                    
                    avg_time = sum(response_times) / len(response_times) if response_times else 0.0
                    time_series.append((current_time, avg_time))
                    current_time = next_time
            
            elif metric_name == "error_rate":
                # Error rate per hour
                current_time = start_date
                while current_time <= end_date:
                    next_time = current_time + timedelta(hours=1)
                    total = 0
                    errors = 0
                    
                    for user in user_list.users:
                        for interaction in user.interaction_history:
                            if current_time <= interaction.timestamp < next_time:
                                total += 1
                                if not interaction.was_successful:
                                    errors += 1
                    
                    error_rate = (errors / total * 100) if total > 0 else 0.0
                    time_series.append((current_time, error_rate))
                    current_time = next_time
            
            elif metric_name == "active_users":
                # Active users per day
                current_time = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                while current_time <= end_date:
                    next_time = current_time + timedelta(days=1)
                    active_users = set()
                    
                    for user in user_list.users:
                        for interaction in user.interaction_history:
                            if current_time <= interaction.timestamp < next_time:
                                active_users.add(user.phone_number)
                                break
                    
                    time_series.append((current_time, float(len(active_users))))
                    current_time = next_time
            
            elif metric_name == "classification_distribution":
                # Classification distribution per day
                current_time = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                while current_time <= end_date:
                    next_time = current_time + timedelta(days=1)
                    classifications = {"Legit": 0, "Suspicious": 0, "Likely Scam": 0}
                    
                    for user in user_list.users:
                        for interaction in user.interaction_history:
                            if (current_time <= interaction.timestamp < next_time and 
                                interaction.analysis_result):
                                classification = interaction.analysis_result.classification_text
                                classifications[classification] += 1
                    
                    # Use "Likely Scam" percentage as the metric
                    total = sum(classifications.values())
                    scam_percentage = (classifications["Likely Scam"] / total * 100) if total > 0 else 0.0
                    time_series.append((current_time, scam_percentage))
                    current_time = next_time
            
            else:
                # Default to random data
                import random
                current_time = start_date
                while current_time <= end_date:
                    time_series.append((current_time, random.uniform(0, 100)))
                    current_time += timedelta(hours=1)
            
            return time_series
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to get metric time series",
                metric_name=metric_name,
                error=str(e)
            )
            raise
    
    async def store_report(self, report: ReportData) -> str:
        """
        Store a generated report.
        
        Args:
            report: Report data to store
            
        Returns:
            Report ID
        """
        try:
            # Generate report ID
            report_id = str(uuid.uuid4())
            
            # Export report to file
            export_result = await self.reporting_engine.export_report(report)
            
            # Update report with export details
            report.download_url = export_result.get("file_path")
            report.file_size = export_result.get("file_size")
            
            # Store report
            self.stored_reports[report_id] = report
            
            # Also save report metadata to file for persistence
            metadata = {
                "id": report_id,
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "period": report.period,
                "export_format": report.export_format,
                "download_url": report.download_url,
                "file_size": report.file_size
            }
            
            metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return report_id
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to store report",
                report_type=report.report_type,
                error=str(e)
            )
            raise
    
    async def get_report(self, report_id: str) -> Optional[ReportData]:
        """
        Get a stored report by ID.
        
        Args:
            report_id: ID of the report
            
        Returns:
            ReportData if found, None otherwise
        """
        try:
            # Check in-memory cache first
            if report_id in self.stored_reports:
                return self.stored_reports[report_id]
            
            # Try to load from file
            metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Create report object
                report = ReportData(
                    report_type=metadata["report_type"],
                    generated_at=datetime.fromisoformat(metadata["generated_at"]),
                    period=metadata["period"],
                    data={},  # Data is not stored in metadata
                    export_format=metadata["export_format"],
                    download_url=metadata["download_url"],
                    file_size=metadata["file_size"]
                )
                
                # Cache report
                self.stored_reports[report_id] = report
                
                return report
            
            return None
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to get report",
                report_id=report_id,
                error=str(e)
            )
            return None
    
    async def list_reports(self, 
                         report_type: Optional[str] = None,
                         limit: int = 20) -> List[Dict[str, Any]]:
        """
        List stored reports.
        
        Args:
            report_type: Optional filter by report type
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata
        """
        try:
            reports = []
            
            # List report metadata files
            for filename in os.listdir(self.reports_dir):
                if filename.endswith("_metadata.json"):
                    metadata_path = os.path.join(self.reports_dir, filename)
                    
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Apply filter
                    if report_type and metadata["report_type"] != report_type:
                        continue
                    
                    reports.append(metadata)
            
            # Sort by generation time (newest first)
            reports.sort(key=lambda r: r["generated_at"], reverse=True)
            
            # Apply limit
            return reports[:limit]
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to list reports",
                error=str(e)
            )
            return []
    
    async def record_analytics_event(self, 
                                   event_type: str,
                                   event_data: Dict[str, Any]) -> None:
        """
        Record an analytics event for advanced analysis.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        try:
            # Record event in advanced analytics engine
            if event_type == "request":
                # Record request event
                await self.advanced_analytics_engine.record_data_point(
                    "request_count", 
                    1.0,
                    dimensions={
                        "user_type": event_data.get("user_type", "standard"),
                        "request_type": event_data.get("request_type", "unknown"),
                        "classification": event_data.get("classification", "unknown")
                    }
                )
                
                # Record response time if available
                if "response_time" in event_data:
                    await self.advanced_analytics_engine.record_data_point(
                        "response_time", 
                        event_data["response_time"],
                        dimensions={
                            "endpoint": event_data.get("endpoint", "unknown"),
                            "classification_type": event_data.get("classification", "unknown")
                        }
                    )
            
            elif event_type == "error":
                # Record error event
                await self.advanced_analytics_engine.record_data_point(
                    "error_rate", 
                    1.0,
                    dimensions={
                        "error_type": event_data.get("error_type", "unknown"),
                        "component": event_data.get("component", "unknown")
                    }
                )
            
            elif event_type == "classification":
                # Record classification event
                await self.advanced_analytics_engine.record_data_point(
                    "classification_accuracy", 
                    event_data.get("confidence", 0.0),
                    dimensions={
                        "classification_type": event_data.get("classification", "unknown"),
                        "confidence_level": "high" if event_data.get("confidence", 0.0) > 0.8 else "medium"
                    }
                )
            
            elif event_type == "user_engagement":
                # Record user engagement event
                await self.advanced_analytics_engine.record_data_point(
                    "user_engagement", 
                    event_data.get("engagement_score", 1.0),
                    dimensions={
                        "user_segment": event_data.get("user_segment", "standard"),
                        "interaction_type": event_data.get("interaction_type", "message")
                    }
                )
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to record analytics event",
                event_type=event_type,
                error=str(e)
            )
    
    async def get_analytics_insights(self, 
                                   metrics: Optional[List[str]] = None,
                                   days: int = 7) -> List[Dict[str, Any]]:
        """
        Get business intelligence insights from analytics data.
        
        Args:
            metrics: Optional list of metrics to analyze
            days: Number of days to analyze
            
        Returns:
            List of insights
        """
        try:
            # Set time period
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Get insights from advanced analytics engine
            insights = await self.advanced_analytics_engine.generate_insights(
                metric_names=metrics,
                time_period=(start_time, end_time)
            )
            
            # Convert to serializable format
            serializable_insights = []
            for insight in insights:
                serializable_insights.append({
                    "title": insight.title,
                    "description": insight.description,
                    "insight_type": insight.insight_type,
                    "confidence": insight.confidence,
                    "impact": insight.impact,
                    "recommendation": insight.recommendation,
                    "timestamp": insight.timestamp.isoformat()
                })
            
            return serializable_insights
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to get analytics insights",
                error=str(e)
            )
            return []