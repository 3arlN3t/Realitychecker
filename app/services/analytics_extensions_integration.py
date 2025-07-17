"""
Integration methods for the AnalyticsService class to delegate to the extensions.

This module provides methods that will be added to the AnalyticsService class
to delegate to the analytics extensions functionality.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


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
    return await self._extensions.get_metric_time_series(
        metric_name=metric_name,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions
    )


async def get_report(self, report_id: str):
    """
    Get a stored report by ID.
    
    Args:
        report_id: ID of the report
        
    Returns:
        ReportData if found, None otherwise
    """
    return await self._extensions.get_report(report_id)


async def store_report(self, report):
    """
    Store a generated report.
    
    Args:
        report: Report data to store
        
    Returns:
        Report ID
    """
    return await self._extensions.store_report(report)


async def list_reports(self, report_type=None, limit=20):
    """
    List stored reports.
    
    Args:
        report_type: Optional filter by report type
        limit: Maximum number of reports to return
        
    Returns:
        List of report metadata
    """
    return await self._extensions.list_reports(report_type, limit)


async def record_analytics_event(self, event_type, event_data):
    """
    Record an analytics event for advanced analysis.
    
    Args:
        event_type: Type of event
        event_data: Event data
    """
    return await self._extensions.record_analytics_event(event_type, event_data)


async def get_analytics_insights(self, metrics=None, days=7):
    """
    Get business intelligence insights from analytics data.
    
    Args:
        metrics: Optional list of metrics to analyze
        days: Number of days to analyze
        
    Returns:
        List of insights
    """
    return await self._extensions.get_analytics_insights(metrics, days)