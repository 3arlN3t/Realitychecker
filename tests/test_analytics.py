"""
Unit tests for the AnalyticsService.

This module contains comprehensive tests for analytics calculations,
report generation, and data aggregation functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from app.services.analytics import AnalyticsService
from app.services.user_management import UserManagementService
from app.models.data_models import (
    AppConfig, DashboardOverview, AnalyticsTrends, UsageStatistics,
    ReportData, ReportParameters, UserDetails, UserInteraction,
    JobAnalysisResult, JobClassification, UserList
)


class TestAnalyticsService:
    """Test cases for AnalyticsService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return AppConfig(
            openai_api_key="test-key",
            twilio_account_sid="test-sid",
            twilio_auth_token="test-token",
            twilio_phone_number="whatsapp:+1234567890",
            max_pdf_size_mb=10,
            openai_model="gpt-4",
            log_level="INFO"
        )
    
    @pytest.fixture
    def mock_user_service(self):
        """Create a mock user management service."""
        return Mock(spec=UserManagementService)
    
    @pytest.fixture
    def analytics_service(self, mock_config, mock_user_service):
        """Create an AnalyticsService instance for testing."""
        return AnalyticsService(mock_config, mock_user_service)
    
    @pytest.fixture
    def sample_users(self):
        """Create sample user data for testing."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # Create sample interactions
        interactions_user1 = [
            UserInteraction(
                timestamp=yesterday,
                message_type="text",
                message_content="Test job ad",
                analysis_result=JobAnalysisResult(
                    trust_score=85,
                    classification=JobClassification.LEGIT,
                    reasons=["Reason 1", "Reason 2", "Reason 3"],
                    confidence=0.9
                ),
                response_time=1.2
            ),
            UserInteraction(
                timestamp=now,
                message_type="pdf",
                analysis_result=JobAnalysisResult(
                    trust_score=25,
                    classification=JobClassification.LIKELY_SCAM,
                    reasons=["Reason 1", "Reason 2", "Reason 3"],
                    confidence=0.8
                ),
                response_time=2.1
            )
        ]
        
        interactions_user2 = [
            UserInteraction(
                timestamp=week_ago,
                message_type="text",
                analysis_result=JobAnalysisResult(
                    trust_score=60,
                    classification=JobClassification.SUSPICIOUS,
                    reasons=["Reason 1", "Reason 2", "Reason 3"],
                    confidence=0.7
                ),
                response_time=1.8,
                error="Test error"
            )
        ]
        
        users = [
            UserDetails(
                phone_number="whatsapp:+1234567890",
                first_interaction=week_ago,
                last_interaction=now,
                total_requests=2,
                blocked=False,
                interaction_history=interactions_user1
            ),
            UserDetails(
                phone_number="whatsapp:+0987654321",
                first_interaction=week_ago,
                last_interaction=week_ago,
                total_requests=1,
                blocked=True,
                interaction_history=interactions_user2
            )
        ]
        
        return users
    
    @pytest.fixture
    def sample_user_list(self, sample_users):
        """Create a sample UserList for testing."""
        return UserList(
            users=sample_users,
            total=len(sample_users),
            page=1,
            pages=1,
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_get_dashboard_overview(self, analytics_service, mock_user_service, sample_user_list):
        """Test dashboard overview generation."""
        # Mock user service responses
        mock_user_service.get_user_statistics.return_value = {
            "total_interactions": 100,
            "active_users_7d": 25,
            "success_rate": 85.5
        }
        mock_user_service.get_users.return_value = sample_user_list
        
        # Get dashboard overview
        overview = await analytics_service.get_dashboard_overview()
        
        # Assertions
        assert isinstance(overview, DashboardOverview)
        assert overview.total_requests == 100
        assert overview.active_users == 25
        assert overview.system_health in ["healthy", "warning", "critical"]
        assert overview.error_rate >= 0
        assert overview.avg_response_time >= 0
        assert isinstance(overview.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_get_analytics_trends(self, analytics_service, mock_user_service, sample_user_list):
        """Test analytics trends generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Get analytics trends
        trends = await analytics_service.get_analytics_trends("week")
        
        # Assertions
        assert isinstance(trends, AnalyticsTrends)
        assert trends.period == "week"
        assert isinstance(trends.classifications, dict)
        assert isinstance(trends.daily_counts, list)
        assert isinstance(trends.peak_hours, list)
        assert isinstance(trends.user_engagement, dict)
        
        # Check classification keys
        expected_classifications = {"Legit", "Suspicious", "Likely Scam"}
        assert set(trends.classifications.keys()).issubset(expected_classifications)
        
        # Check daily counts structure
        for daily_count in trends.daily_counts:
            assert "date" in daily_count
            assert "count" in daily_count
            assert isinstance(daily_count["count"], int)
    
    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, analytics_service, mock_user_service, sample_user_list):
        """Test usage statistics generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Get usage statistics
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        stats = await analytics_service.get_usage_statistics(start_date, end_date)
        
        # Assertions
        assert isinstance(stats, UsageStatistics)
        assert stats.total_messages >= 0
        assert stats.text_messages >= 0
        assert stats.pdf_messages >= 0
        assert stats.successful_analyses >= 0
        assert stats.failed_analyses >= 0
        assert stats.unique_users >= 0
        assert stats.returning_users >= 0
        assert stats.blocked_users >= 0
        
        # Check calculated properties
        assert 0 <= stats.success_rate <= 100
        assert 0 <= stats.pdf_usage_rate <= 100
        assert 0 <= stats.user_retention_rate <= 100
        
        # Check response time statistics
        assert stats.average_response_time >= 0
        assert stats.median_response_time >= 0
        assert stats.p95_response_time >= 0
        
        # Check data structures
        assert isinstance(stats.classification_breakdown, dict)
        assert isinstance(stats.error_breakdown, dict)
        assert isinstance(stats.hourly_distribution, dict)
        assert isinstance(stats.daily_distribution, dict)
    
    @pytest.mark.asyncio
    async def test_generate_usage_summary_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test usage summary report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="usage_summary",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "usage_summary"
        assert report.export_format == "json"
        assert isinstance(report.generated_at, datetime)
        assert isinstance(report.data, dict)
        
        # Check report data structure
        assert "summary" in report.data
        assert "message_breakdown" in report.data
        assert "performance" in report.data
        assert "classifications" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_classification_analysis_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test classification analysis report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="classification_analysis",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "classification_analysis"
        assert "total_analyses" in report.data
        assert "classification_counts" in report.data
        assert "classification_percentages" in report.data
        assert "trends" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_user_behavior_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test user behavior report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="user_behavior",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "user_behavior"
        assert "user_metrics" in report.data
        assert "usage_patterns" in report.data
        assert "engagement" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_performance_metrics_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test performance metrics report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        mock_user_service.get_user_statistics.return_value = {
            "total_interactions": 100,
            "active_users_7d": 25,
            "success_rate": 85.5
        }
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="performance_metrics",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "performance_metrics"
        assert "response_times" in report.data
        assert "success_metrics" in report.data
        assert "system_health" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_error_analysis_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test error analysis report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="error_analysis",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "error_analysis"
        assert "total_errors" in report.data
        assert "error_breakdown" in report.data
        assert "error_percentages" in report.data
        assert "error_rate" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_trend_analysis_report(self, analytics_service, mock_user_service, sample_user_list):
        """Test trend analysis report generation."""
        # Mock user service response
        mock_user_service.get_users.return_value = sample_user_list
        
        # Create report parameters
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        parameters = ReportParameters(
            report_type="trend_analysis",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        
        # Generate report
        report = await analytics_service.generate_report(parameters)
        
        # Assertions
        assert isinstance(report, ReportData)
        assert report.report_type == "trend_analysis"
        assert "period" in report.data
        assert "classification_trends" in report.data
        assert "daily_activity" in report.data
        assert "peak_hours" in report.data
        assert "user_engagement" in report.data
    
    def test_export_report_to_json(self, analytics_service):
        """Test JSON export functionality."""
        # Create sample report
        report = ReportData(
            report_type="usage_summary",
            generated_at=datetime.utcnow(),
            period="2025-01-01 to 2025-01-07",
            data={"test": "data"},
            export_format="json"
        )
        
        # Export to JSON
        json_output = analytics_service._export_to_json(report)
        
        # Assertions
        assert isinstance(json_output, str)
        assert "report_metadata" in json_output
        assert "data" in json_output
        assert report.report_type in json_output
    
    def test_export_report_to_csv(self, analytics_service):
        """Test CSV export functionality."""
        # Create sample report
        report = ReportData(
            report_type="usage_summary",
            generated_at=datetime.utcnow(),
            period="2025-01-01 to 2025-01-07",
            data={
                "summary": {"total_messages": 100, "unique_users": 25},
                "breakdown": {"text": 80, "pdf": 20}
            },
            export_format="csv"
        )
        
        # Export to CSV
        csv_output = analytics_service._export_to_csv(report)
        
        # Assertions
        assert isinstance(csv_output, str)
        assert "usage_summary" in csv_output
        assert "SUMMARY" in csv_output
        assert "100" in csv_output  # total_messages value
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, analytics_service, mock_user_service, sample_user_list):
        """Test that caching works correctly."""
        # Mock user service response
        mock_user_service.get_user_statistics.return_value = {
            "total_interactions": 100,
            "active_users_7d": 25,
            "success_rate": 85.5
        }
        mock_user_service.get_users.return_value = sample_user_list
        
        # First call - should hit the service
        overview1 = await analytics_service.get_dashboard_overview()
        
        # Second call - should use cache
        overview2 = await analytics_service.get_dashboard_overview()
        
        # Should be the same object (from cache)
        assert overview1.timestamp == overview2.timestamp
        
        # Verify service was called only once
        assert mock_user_service.get_user_statistics.call_count == 1
    
    @pytest.mark.asyncio
    async def test_date_range_validation(self, analytics_service):
        """Test date range validation in report parameters."""
        # Test invalid date range (start after end)
        with pytest.raises(ValueError, match="Start date must be before end date"):
            ReportParameters(
                report_type="usage_summary",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() - timedelta(days=1),
                export_format="json"
            )
        
        # Test date range too large (more than 1 year)
        with pytest.raises(ValueError, match="Date range cannot exceed 365 days"):
            ReportParameters(
                report_type="usage_summary",
                start_date=datetime.utcnow() - timedelta(days=400),
                end_date=datetime.utcnow(),
                export_format="json"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_report_type(self, analytics_service, mock_user_service):
        """Test handling of invalid report types."""
        # Create invalid report parameters should raise ValueError during construction
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Should raise ValueError for invalid report type during parameter creation
        with pytest.raises(ValueError, match="Report type must be one of"):
            ReportParameters(
                report_type="invalid_type",
                start_date=start_date,
                end_date=end_date,
                export_format="json"
            )
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self, analytics_service, mock_user_service):
        """Test handling of empty data sets."""
        # Mock empty user list
        empty_user_list = UserList(users=[], total=0, page=1, pages=1, limit=10)
        mock_user_service.get_users.return_value = empty_user_list
        mock_user_service.get_user_statistics.return_value = {
            "total_interactions": 0,
            "active_users_7d": 0,
            "success_rate": 0
        }
        
        # Get dashboard overview with empty data
        overview = await analytics_service.get_dashboard_overview()
        
        # Should handle empty data gracefully
        assert overview.total_requests == 0
        assert overview.active_users == 0
        assert overview.error_rate == 0
        assert overview.avg_response_time == 0
    
    def test_system_health_determination(self, analytics_service):
        """Test system health determination logic."""
        # Test healthy system
        health = analytics_service._determine_system_health(2.0, 1.5)
        assert health == "healthy"
        
        # Test warning system
        health = analytics_service._determine_system_health(7.0, 4.0)
        assert health == "warning"
        
        # Test critical system
        health = analytics_service._determine_system_health(15.0, 6.0)
        assert health == "critical"
    
    def test_date_range_for_period(self, analytics_service):
        """Test date range calculation for different periods."""
        # Test day period
        start, end = analytics_service._get_date_range_for_period("day")
        assert (end - start).days == 1
        
        # Test week period
        start, end = analytics_service._get_date_range_for_period("week")
        assert (end - start).days == 7
        
        # Test month period
        start, end = analytics_service._get_date_range_for_period("month")
        assert (end - start).days == 30
        
        # Test year period
        start, end = analytics_service._get_date_range_for_period("year")
        assert (end - start).days == 365
        
        # Test invalid period
        with pytest.raises(ValueError, match="Invalid period"):
            analytics_service._get_date_range_for_period("invalid")
    
    def test_error_breakdown_calculation(self, analytics_service):
        """Test error breakdown calculation."""
        # Create sample interactions with different error types
        interactions = [
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                error="PDF processing failed"
            ),
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                error="OpenAI API timeout"
            ),
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                error="Twilio webhook error"
            ),
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                error="Connection timeout"
            ),
            UserInteraction(
                timestamp=datetime.utcnow(),
                message_type="text",
                error="Unknown error occurred"
            )
        ]
        
        # Calculate error breakdown
        breakdown = analytics_service._calculate_error_breakdown(interactions)
        
        # Assertions
        assert "PDF Processing" in breakdown
        assert "AI Analysis" in breakdown
        assert "Message Sending" in breakdown
        assert "Timeout" in breakdown
        assert "Other" in breakdown
        
        assert breakdown["PDF Processing"] == 1
        assert breakdown["AI Analysis"] == 1
        assert breakdown["Message Sending"] == 1
        assert breakdown["Timeout"] == 1
        assert breakdown["Other"] == 1
    
    def test_hourly_distribution_calculation(self, analytics_service):
        """Test hourly distribution calculation."""
        # Create interactions at different hours
        interactions = [
            UserInteraction(
                timestamp=datetime(2025, 1, 1, 9, 0, 0),  # 9 AM
                message_type="text"
            ),
            UserInteraction(
                timestamp=datetime(2025, 1, 1, 14, 0, 0),  # 2 PM
                message_type="text"
            ),
            UserInteraction(
                timestamp=datetime(2025, 1, 1, 9, 30, 0),  # 9:30 AM
                message_type="text"
            )
        ]
        
        # Calculate hourly distribution
        distribution = analytics_service._calculate_hourly_distribution(interactions)
        
        # Assertions
        assert distribution[9] == 2  # Two interactions at 9 AM hour
        assert distribution[14] == 1  # One interaction at 2 PM hour
        assert len(distribution) == 2  # Only two different hours
    
    def test_daily_distribution_calculation(self, analytics_service):
        """Test daily distribution calculation."""
        # Create interactions on different days of the week
        monday = datetime(2025, 1, 6, 10, 0, 0)  # Monday
        tuesday = datetime(2025, 1, 7, 10, 0, 0)  # Tuesday
        
        interactions = [
            UserInteraction(timestamp=monday, message_type="text"),
            UserInteraction(timestamp=tuesday, message_type="text"),
            UserInteraction(timestamp=monday, message_type="pdf")
        ]
        
        # Calculate daily distribution
        distribution = analytics_service._calculate_daily_distribution(interactions)
        
        # Assertions
        assert distribution["Monday"] == 2
        assert distribution["Tuesday"] == 1
        assert len(distribution) == 2

    @pytest.mark.asyncio
    async def test_get_ab_test_results(self, analytics_service, mock_user_service, sample_user_list):
        analytics_service.config.AB_TESTING_CONFIG = {
            "test_experiment": {
                "variants": {
                    "A": 1,
                    "B": 1
                }
            }
        }

        mock_user_service.get_users.return_value = sample_user_list

        results = await analytics_service.get_ab_test_results("test_experiment")

        assert results["experiment_name"] == "test_experiment"
        assert "A" in results["results"]
        assert "B" in results["results"]

        assert results["results"]["A"]["users"] >= 0
        assert results["results"]["B"]["users"] >= 0
        assert results["results"]["A"]["conversions"] >= 0
        assert results["results"]["B"]["conversions"] >= 0
        assert results["results"]["A"]["conversion_rate"] >= 0
        assert results["results"]["B"]["conversion_rate"] >= 0


class TestAnalyticsDataModels:
    """Test cases for analytics data models."""
    
    def test_dashboard_overview_validation(self):
        """Test DashboardOverview validation."""
        # Valid data
        overview = DashboardOverview(
            total_requests=100,
            requests_today=10,
            error_rate=5.0,
            avg_response_time=1.5,
            active_users=25,
            system_health="healthy",
            timestamp=datetime.utcnow()
        )
        assert overview.total_requests == 100
        
        # Invalid error rate
        with pytest.raises(ValueError, match="Error rate must be between 0.0 and 100.0"):
            DashboardOverview(
                total_requests=100,
                requests_today=10,
                error_rate=150.0,
                avg_response_time=1.5,
                active_users=25,
                system_health="healthy",
                timestamp=datetime.utcnow()
            )
        
        # Invalid system health
        with pytest.raises(ValueError, match="System health must be"):
            DashboardOverview(
                total_requests=100,
                requests_today=10,
                error_rate=5.0,
                avg_response_time=1.5,
                active_users=25,
                system_health="invalid",
                timestamp=datetime.utcnow()
            )
    
    def test_usage_statistics_properties(self):
        """Test UsageStatistics calculated properties."""
        stats = UsageStatistics(
            total_messages=100,
            text_messages=80,
            pdf_messages=20,
            successful_analyses=85,
            failed_analyses=15,
            average_response_time=1.5,
            median_response_time=1.2,
            p95_response_time=3.0,
            unique_users=50,
            returning_users=30,
            blocked_users=5,
            classification_breakdown={"Legit": 60, "Suspicious": 20, "Likely Scam": 5},
            error_breakdown={"PDF Processing": 10, "AI Analysis": 5},
            hourly_distribution={9: 20, 14: 30, 18: 25},
            daily_distribution={"Monday": 40, "Tuesday": 35, "Wednesday": 25}
        )
        
        # Test calculated properties
        assert stats.success_rate == 85.0
        assert stats.pdf_usage_rate == 20.0
        assert stats.user_retention_rate == 60.0
    
    def test_report_parameters_validation(self):
        """Test ReportParameters validation."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Valid parameters
        params = ReportParameters(
            report_type="usage_summary",
            start_date=start_date,
            end_date=end_date,
            export_format="json"
        )
        assert params.date_range_days == 7
        
        # Invalid date range
        with pytest.raises(ValueError, match="Start date must be before end date"):
            ReportParameters(
                report_type="usage_summary",
                start_date=end_date,
                end_date=start_date,
                export_format="json"
            )
        
        # Invalid report type
        with pytest.raises(ValueError, match="Report type must be one of"):
            ReportParameters(
                report_type="invalid_type",
                start_date=start_date,
                end_date=end_date,
                export_format="json"
            )
    
    def test_system_metrics_validation(self):
        """Test SystemMetrics validation."""
        from app.models.data_models import SystemMetrics
        
        # Valid metrics
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            active_requests=5,
            requests_per_minute=120,
            error_rate=2.5,
            response_times={"p50": 1.0, "p95": 2.5, "p99": 4.0},
            service_status={"openai": "healthy", "twilio": "warning"},
            memory_usage=65.5,
            cpu_usage=45.2
        )
        assert metrics.active_requests == 5
        
        # Missing required percentiles
        with pytest.raises(ValueError, match="Response times must include p50, p95, and p99"):
            SystemMetrics(
                timestamp=datetime.utcnow(),
                active_requests=5,
                requests_per_minute=120,
                error_rate=2.5,
                response_times={"p50": 1.0, "p95": 2.5},  # Missing p99
                service_status={"openai": "healthy"},
                memory_usage=65.5,
                cpu_usage=45.2
            )
        
        # Invalid service status
        with pytest.raises(ValueError, match="Service status must be"):
            SystemMetrics(
                timestamp=datetime.utcnow(),
                active_requests=5,
                requests_per_minute=120,
                error_rate=2.5,
                response_times={"p50": 1.0, "p95": 2.5, "p99": 4.0},
                service_status={"openai": "invalid_status"},
                memory_usage=65.5,
                cpu_usage=45.2
            )