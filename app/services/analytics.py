"""
Analytics service for the Reality Checker WhatsApp bot.

This module provides the AnalyticsService class for data aggregation, trend analysis,
dashboard overview data collection, and report generation with multiple export formats.
"""

import logging
import json
import csv
import io
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import threading

from app.models.data_models import (
    DashboardOverview, AnalyticsTrends, UsageStatistics, ReportData,
    SystemMetrics, ReportParameters, UserDetails, UserInteraction,
    JobClassification, AppConfig
)
from app.services.user_management import UserManagementService
from app.utils.logging import get_logger, log_with_context


logger = get_logger(__name__)


class AnalyticsService:
    """
    Service for analytics data aggregation and trend analysis.
    
    This service provides functionality for:
    - Dashboard overview data collection and processing
    - Classification breakdown and usage statistics calculation
    - Trend analysis and user engagement metrics
    - Report generation with multiple export formats
    """
    
    def __init__(self, config: AppConfig, user_service: UserManagementService):
        """
        Initialize the analytics service.
        
        Args:
            config: Application configuration
            user_service: User management service for data access
        """
        self.config = config
        self.user_service = user_service
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache TTL for expensive calculations
        self._lock = threading.RLock()
        
        logger.info("AnalyticsService initialized")
    
    async def get_dashboard_overview(self) -> DashboardOverview:
        """
        Get dashboard overview data with key performance indicators.
        
        Returns:
            DashboardOverview object with current system metrics
        """
        try:
            # Check cache first
            cache_key = "dashboard_overview"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Get user statistics
            user_stats = await self.user_service.get_user_statistics()
            
            # Calculate today's requests
            today = datetime.utcnow().date()
            requests_today = await self._count_requests_for_date(today)
            
            # Calculate error rate
            error_rate = await self._calculate_error_rate()
            
            # Calculate average response time
            avg_response_time = await self._calculate_average_response_time()
            
            # Determine system health
            system_health = self._determine_system_health(error_rate, avg_response_time)
            
            overview = DashboardOverview(
                total_requests=user_stats["total_interactions"],
                requests_today=requests_today,
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                active_users=user_stats["active_users_7d"],
                system_health=system_health,
                timestamp=datetime.utcnow()
            )
            
            # Cache the result
            self._cache_data(cache_key, overview)
            
            log_with_context(
                logger,
                logging.INFO,
                "Dashboard overview generated",
                total_requests=overview.total_requests,
                requests_today=overview.requests_today,
                error_rate=overview.error_rate,
                system_health=overview.system_health
            )
            
            return overview
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate dashboard overview",
                error=str(e)
            )
            raise
    
    async def get_analytics_trends(self, 
                                 period: str, 
                                 start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> AnalyticsTrends:
        """
        Get analytics trends and statistics for the specified period.
        
        Args:
            period: Time period ("day", "week", "month", "year")
            start_date: Optional start date for custom range
            end_date: Optional end date for custom range
            
        Returns:
            AnalyticsTrends object with trend data
        """
        try:
            # Determine date range
            if start_date and end_date:
                date_range = (start_date, end_date)
            else:
                date_range = self._get_date_range_for_period(period)
            
            cache_key = f"analytics_trends_{period}_{date_range[0].isoformat()}_{date_range[1].isoformat()}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Get all users and their interactions
            user_list = await self.user_service.get_users(page=1, limit=10000)  # Get all users
            
            # Calculate classification breakdown
            classifications = await self._calculate_classification_breakdown(
                user_list.users, date_range
            )
            
            # Calculate daily counts
            daily_counts = await self._calculate_daily_counts(
                user_list.users, date_range
            )
            
            # Calculate peak hours
            peak_hours = await self._calculate_peak_hours(
                user_list.users, date_range
            )
            
            # Calculate user engagement metrics
            user_engagement = await self._calculate_user_engagement(
                user_list.users, date_range
            )
            
            trends = AnalyticsTrends(
                period=period,
                classifications=classifications,
                daily_counts=daily_counts,
                peak_hours=peak_hours,
                user_engagement=user_engagement
            )
            
            # Cache the result
            self._cache_data(cache_key, trends)
            
            log_with_context(
                logger,
                logging.INFO,
                "Analytics trends generated",
                period=period,
                date_range_start=date_range[0].isoformat(),
                date_range_end=date_range[1].isoformat(),
                total_classifications=sum(classifications.values())
            )
            
            return trends
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate analytics trends",
                period=period,
                error=str(e)
            )
            raise
    
    async def get_usage_statistics(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> UsageStatistics:
        """
        Get detailed usage statistics for the specified date range.
        
        Args:
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to now)
            
        Returns:
            UsageStatistics object with comprehensive metrics
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            cache_key = f"usage_statistics_{start_date.isoformat()}_{end_date.isoformat()}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Get all users and their interactions
            user_list = await self.user_service.get_users(page=1, limit=10000)
            date_range = (start_date, end_date)
            
            # Filter interactions within date range
            all_interactions = []
            unique_users = set()
            returning_users = set()
            blocked_users = 0
            
            for user in user_list.users:
                if user.blocked:
                    blocked_users += 1
                
                user_interactions = [
                    interaction for interaction in user.interaction_history
                    if start_date <= interaction.timestamp <= end_date
                ]
                
                if user_interactions:
                    unique_users.add(user.phone_number)
                    all_interactions.extend(user_interactions)
                    
                    # Check if returning user (has interactions before the period)
                    has_earlier_interactions = any(
                        interaction.timestamp < start_date
                        for interaction in user.interaction_history
                    )
                    if has_earlier_interactions:
                        returning_users.add(user.phone_number)
            
            # Calculate message type breakdown
            text_messages = sum(1 for i in all_interactions if i.message_type == "text")
            pdf_messages = sum(1 for i in all_interactions if i.message_type == "pdf")
            total_messages = len(all_interactions)
            
            # Calculate success/failure breakdown
            successful_analyses = sum(1 for i in all_interactions if i.was_successful)
            failed_analyses = total_messages - successful_analyses
            
            # Calculate response time statistics
            response_times = [i.response_time for i in all_interactions if i.response_time > 0]
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            median_response_time = statistics.median(response_times) if response_times else 0.0
            
            # Calculate 95th percentile response time
            if response_times:
                sorted_times = sorted(response_times)
                p95_index = int(0.95 * len(sorted_times))
                p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            else:
                p95_response_time = 0.0
            
            # Calculate classification breakdown
            classification_breakdown = await self._calculate_classification_breakdown(
                user_list.users, date_range
            )
            
            # Calculate error breakdown
            error_breakdown = self._calculate_error_breakdown(all_interactions)
            
            # Calculate hourly and daily distribution
            hourly_distribution = self._calculate_hourly_distribution(all_interactions)
            daily_distribution = self._calculate_daily_distribution(all_interactions)
            
            statistics_obj = UsageStatistics(
                total_messages=total_messages,
                text_messages=text_messages,
                pdf_messages=pdf_messages,
                successful_analyses=successful_analyses,
                failed_analyses=failed_analyses,
                average_response_time=avg_response_time,
                median_response_time=median_response_time,
                p95_response_time=p95_response_time,
                unique_users=len(unique_users),
                returning_users=len(returning_users),
                blocked_users=blocked_users,
                classification_breakdown=classification_breakdown,
                error_breakdown=error_breakdown,
                hourly_distribution=hourly_distribution,
                daily_distribution=daily_distribution
            )
            
            # Cache the result
            self._cache_data(cache_key, statistics_obj)
            
            log_with_context(
                logger,
                logging.INFO,
                "Usage statistics generated",
                total_messages=total_messages,
                unique_users=len(unique_users),
                success_rate=statistics_obj.success_rate,
                date_range_days=(end_date - start_date).days
            )
            
            return statistics_obj
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate usage statistics",
                error=str(e)
            )
            raise
    
    async def generate_report(self, parameters: ReportParameters) -> ReportData:
        """
        Generate a custom report based on the provided parameters.
        
        Args:
            parameters: Report generation parameters
            
        Returns:
            ReportData object with generated report
        """
        try:
            log_with_context(
                logger,
                logging.INFO,
                "Generating report",
                report_type=parameters.report_type,
                export_format=parameters.export_format,
                date_range_days=parameters.date_range_days
            )
            
            # Generate report data based on type
            if parameters.report_type == "usage_summary":
                report_data = await self._generate_usage_summary_report(parameters)
            elif parameters.report_type == "classification_analysis":
                report_data = await self._generate_classification_analysis_report(parameters)
            elif parameters.report_type == "user_behavior":
                report_data = await self._generate_user_behavior_report(parameters)
            elif parameters.report_type == "performance_metrics":
                report_data = await self._generate_performance_metrics_report(parameters)
            elif parameters.report_type == "error_analysis":
                report_data = await self._generate_error_analysis_report(parameters)
            elif parameters.report_type == "trend_analysis":
                report_data = await self._generate_trend_analysis_report(parameters)
            else:
                raise ValueError(f"Unsupported report type: {parameters.report_type}")
            
            # Create report object
            report = ReportData(
                report_type=parameters.report_type,
                generated_at=datetime.utcnow(),
                period=f"{parameters.start_date.date()} to {parameters.end_date.date()}",
                data=report_data,
                export_format=parameters.export_format
            )
            
            log_with_context(
                logger,
                logging.INFO,
                "Report generated successfully",
                report_type=parameters.report_type,
                data_points=len(report_data) if isinstance(report_data, (list, dict)) else 1
            )
            
            return report
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to generate report",
                report_type=parameters.report_type,
                error=str(e)
            )
            raise
    
    async def export_report_to_format(self, report: ReportData) -> str:
        """
        Export report data to the specified format.
        
        Args:
            report: ReportData object to export
            
        Returns:
            str: Exported data as string
        """
        try:
            if report.export_format == "json":
                return self._export_to_json(report)
            elif report.export_format == "csv":
                return self._export_to_csv(report)
            elif report.export_format == "pdf":
                return self._export_to_pdf(report)
            elif report.export_format == "xlsx":
                return self._export_to_xlsx(report)
            else:
                raise ValueError(f"Unsupported export format: {report.export_format}")
                
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Failed to export report",
                report_type=report.report_type,
                export_format=report.export_format,
                error=str(e)
            )
            raise
    
    # Private helper methods
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if it's still valid."""
        with self._lock:
            if cache_key in self._metrics_cache:
                cache_time = self._cache_timestamps.get(cache_key)
                if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                    return self._metrics_cache[cache_key]
                else:
                    # Remove expired cache
                    self._metrics_cache.pop(cache_key, None)
                    self._cache_timestamps.pop(cache_key, None)
            return None
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with timestamp."""
        with self._lock:
            self._metrics_cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.utcnow()
    
    async def _count_requests_for_date(self, date: datetime.date) -> int:
        """Count requests for a specific date."""
        user_list = await self.user_service.get_users(page=1, limit=10000)
        count = 0
        
        for user in user_list.users:
            for interaction in user.interaction_history:
                if interaction.timestamp.date() == date:
                    count += 1
        
        return count
    
    async def _calculate_error_rate(self) -> float:
        """Calculate overall error rate percentage."""
        user_list = await self.user_service.get_users(page=1, limit=10000)
        total_interactions = 0
        failed_interactions = 0
        
        for user in user_list.users:
            for interaction in user.interaction_history:
                total_interactions += 1
                if not interaction.was_successful:
                    failed_interactions += 1
        
        if total_interactions == 0:
            return 0.0
        
        return (failed_interactions / total_interactions) * 100
    
    async def _calculate_average_response_time(self) -> float:
        """Calculate average response time across all interactions."""
        user_list = await self.user_service.get_users(page=1, limit=10000)
        response_times = []
        
        for user in user_list.users:
            for interaction in user.interaction_history:
                if interaction.response_time > 0:
                    response_times.append(interaction.response_time)
        
        return statistics.mean(response_times) if response_times else 0.0
    
    def _determine_system_health(self, error_rate: float, avg_response_time: float) -> str:
        """Determine system health based on metrics."""
        if error_rate > 10.0 or avg_response_time > 5.0:
            return "critical"
        elif error_rate > 5.0 or avg_response_time > 3.0:
            return "warning"
        else:
            return "healthy"
    
    def _get_date_range_for_period(self, period: str) -> Tuple[datetime, datetime]:
        """Get date range for the specified period."""
        end_date = datetime.utcnow()
        
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        return start_date, end_date
    
    async def _calculate_classification_breakdown(self, 
                                                users: List[UserDetails], 
                                                date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        """Calculate classification breakdown for the date range."""
        classifications = {"Legit": 0, "Suspicious": 0, "Likely Scam": 0}
        
        for user in users:
            for interaction in user.interaction_history:
                if (date_range[0] <= interaction.timestamp <= date_range[1] and 
                    interaction.analysis_result):
                    classification = interaction.analysis_result.classification_text
                    classifications[classification] = classifications.get(classification, 0) + 1
        
        return classifications
    
    async def _calculate_daily_counts(self, 
                                    users: List[UserDetails], 
                                    date_range: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
        """Calculate daily interaction counts for the date range."""
        daily_counts = defaultdict(int)
        
        for user in users:
            for interaction in user.interaction_history:
                if date_range[0] <= interaction.timestamp <= date_range[1]:
                    date_str = interaction.timestamp.date().isoformat()
                    daily_counts[date_str] += 1
        
        # Convert to list format
        result = []
        current_date = date_range[0].date()
        end_date = date_range[1].date()
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            result.append({
                "date": date_str,
                "count": daily_counts.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        return result
    
    async def _calculate_peak_hours(self, 
                                  users: List[UserDetails], 
                                  date_range: Tuple[datetime, datetime]) -> List[int]:
        """Calculate peak usage hours for the date range."""
        hourly_counts = defaultdict(int)
        
        for user in users:
            for interaction in user.interaction_history:
                if date_range[0] <= interaction.timestamp <= date_range[1]:
                    hour = interaction.timestamp.hour
                    hourly_counts[hour] += 1
        
        # Find top 3 peak hours
        sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [hour for hour, count in sorted_hours[:3]]
        
        return sorted(peak_hours)  # Return sorted for consistency
    
    async def _calculate_user_engagement(self, 
                                       users: List[UserDetails], 
                                       date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        """Calculate user engagement metrics for the date range."""
        active_users = 0
        total_interactions = 0
        repeat_users = 0
        
        for user in users:
            user_interactions = [
                interaction for interaction in user.interaction_history
                if date_range[0] <= interaction.timestamp <= date_range[1]
            ]
            
            if user_interactions:
                active_users += 1
                total_interactions += len(user_interactions)
                
                if len(user_interactions) > 1:
                    repeat_users += 1
        
        avg_interactions_per_user = total_interactions / active_users if active_users > 0 else 0.0
        repeat_user_rate = (repeat_users / active_users * 100) if active_users > 0 else 0.0
        
        return {
            "active_users": float(active_users),
            "avg_interactions_per_user": round(avg_interactions_per_user, 2),
            "repeat_user_rate": round(repeat_user_rate, 2),
            "total_interactions": float(total_interactions)
        }
    
    def _calculate_error_breakdown(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Calculate breakdown of error types."""
        error_counts = defaultdict(int)
        
        for interaction in interactions:
            if interaction.error:
                # Categorize errors
                error_msg = interaction.error.lower()
                if "pdf" in error_msg:
                    error_counts["PDF Processing"] += 1
                elif "openai" in error_msg or "api" in error_msg:
                    error_counts["AI Analysis"] += 1
                elif "twilio" in error_msg:
                    error_counts["Message Sending"] += 1
                elif "timeout" in error_msg:
                    error_counts["Timeout"] += 1
                else:
                    error_counts["Other"] += 1
        
        return dict(error_counts)
    
    def _calculate_hourly_distribution(self, interactions: List[UserInteraction]) -> Dict[int, int]:
        """Calculate hourly distribution of interactions."""
        hourly_counts = defaultdict(int)
        
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hourly_counts[hour] += 1
        
        return dict(hourly_counts)
    
    def _calculate_daily_distribution(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Calculate daily distribution of interactions."""
        daily_counts = defaultdict(int)
        
        for interaction in interactions:
            day_name = interaction.timestamp.strftime("%A")
            daily_counts[day_name] += 1
        
        return dict(daily_counts)
    
    # Report generation methods
    
    async def _generate_usage_summary_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate usage summary report."""
        usage_stats = await self.get_usage_statistics(parameters.start_date, parameters.end_date)
        
        return {
            "summary": {
                "total_messages": usage_stats.total_messages,
                "unique_users": usage_stats.unique_users,
                "success_rate": usage_stats.success_rate,
                "pdf_usage_rate": usage_stats.pdf_usage_rate
            },
            "message_breakdown": {
                "text_messages": usage_stats.text_messages,
                "pdf_messages": usage_stats.pdf_messages
            },
            "performance": {
                "average_response_time": usage_stats.average_response_time,
                "median_response_time": usage_stats.median_response_time,
                "p95_response_time": usage_stats.p95_response_time
            },
            "classifications": usage_stats.classification_breakdown,
            "errors": usage_stats.error_breakdown
        }
    
    async def _generate_classification_analysis_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate classification analysis report."""
        usage_stats = await self.get_usage_statistics(parameters.start_date, parameters.end_date)
        
        total_classifications = sum(usage_stats.classification_breakdown.values())
        classification_percentages = {}
        
        for classification, count in usage_stats.classification_breakdown.items():
            percentage = (count / total_classifications * 100) if total_classifications > 0 else 0
            classification_percentages[classification] = round(percentage, 2)
        
        return {
            "total_analyses": total_classifications,
            "classification_counts": usage_stats.classification_breakdown,
            "classification_percentages": classification_percentages,
            "trends": await self.get_analytics_trends("month", parameters.start_date, parameters.end_date)
        }
    
    async def _generate_user_behavior_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate user behavior report."""
        usage_stats = await self.get_usage_statistics(parameters.start_date, parameters.end_date)
        
        return {
            "user_metrics": {
                "unique_users": usage_stats.unique_users,
                "returning_users": usage_stats.returning_users,
                "retention_rate": usage_stats.user_retention_rate,
                "blocked_users": usage_stats.blocked_users
            },
            "usage_patterns": {
                "hourly_distribution": usage_stats.hourly_distribution,
                "daily_distribution": usage_stats.daily_distribution
            },
            "engagement": {
                "avg_messages_per_user": usage_stats.total_messages / usage_stats.unique_users if usage_stats.unique_users > 0 else 0
            }
        }
    
    async def _generate_performance_metrics_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate performance metrics report."""
        usage_stats = await self.get_usage_statistics(parameters.start_date, parameters.end_date)
        dashboard_overview = await self.get_dashboard_overview()
        
        return {
            "response_times": {
                "average": usage_stats.average_response_time,
                "median": usage_stats.median_response_time,
                "p95": usage_stats.p95_response_time
            },
            "success_metrics": {
                "success_rate": usage_stats.success_rate,
                "total_successful": usage_stats.successful_analyses,
                "total_failed": usage_stats.failed_analyses
            },
            "system_health": {
                "current_status": dashboard_overview.system_health,
                "error_rate": dashboard_overview.error_rate
            }
        }
    
    async def _generate_error_analysis_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate error analysis report."""
        usage_stats = await self.get_usage_statistics(parameters.start_date, parameters.end_date)
        
        total_errors = sum(usage_stats.error_breakdown.values())
        error_percentages = {}
        
        for error_type, count in usage_stats.error_breakdown.items():
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            error_percentages[error_type] = round(percentage, 2)
        
        return {
            "total_errors": total_errors,
            "error_breakdown": usage_stats.error_breakdown,
            "error_percentages": error_percentages,
            "error_rate": (total_errors / usage_stats.total_messages * 100) if usage_stats.total_messages > 0 else 0
        }
    
    async def _generate_trend_analysis_report(self, parameters: ReportParameters) -> Dict[str, Any]:
        """Generate trend analysis report."""
        trends = await self.get_analytics_trends("month", parameters.start_date, parameters.end_date)
        
        return {
            "period": trends.period,
            "classification_trends": trends.classifications,
            "daily_activity": trends.daily_counts,
            "peak_hours": trends.peak_hours,
            "user_engagement": trends.user_engagement
        }
    
    # Export methods
    
    def _export_to_json(self, report: ReportData) -> str:
        """Export report to JSON format."""
        export_data = {
            "report_metadata": {
                "type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "period": report.period
            },
            "data": report.data
        }
        return json.dumps(export_data, indent=2, default=str)
    
    def _export_to_csv(self, report: ReportData) -> str:
        """Export report to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Report Type", report.report_type])
        writer.writerow(["Generated At", report.generated_at.isoformat()])
        writer.writerow(["Period", report.period])
        writer.writerow([])  # Empty row
        
        # Write data based on report type
        self._write_csv_data(writer, report.data)
        
        return output.getvalue()
    
    def _write_csv_data(self, writer: csv.writer, data: Dict[str, Any]) -> None:
        """Write data to CSV writer."""
        for section, section_data in data.items():
            writer.writerow([section.upper()])
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    writer.writerow([key, value])
            elif isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict):
                        if not hasattr(self, '_csv_headers_written'):
                            writer.writerow(list(item.keys()))
                            self._csv_headers_written = True
                        writer.writerow(list(item.values()))
                    else:
                        writer.writerow([item])
            else:
                writer.writerow([section_data])
            
            writer.writerow([])  # Empty row between sections
    
    def _export_to_pdf(self, report: ReportData) -> str:
        """Export report to PDF format (placeholder - would need PDF library)."""
        # This would require a PDF library like reportlab
        # For now, return a placeholder
        return f"PDF export not implemented. Report type: {report.report_type}"
    
    def _export_to_xlsx(self, report: ReportData) -> str:
        """Export report to Excel format (placeholder - would need Excel library)."""
        # This would require a library like openpyxl
        # For now, return a placeholder
        return f"Excel export not implemented. Report type: {report.report_type}"