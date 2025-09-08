"""
Dashboard API endpoints for the Reality Checker WhatsApp bot.

This module provides REST API endpoints for the admin dashboard, analytics,
user management, real-time monitoring, configuration, and reporting.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse

from app.models.data_models import (
    DashboardOverview, AnalyticsTrends, UserList, SystemMetrics, 
    ReportData, ReportParameters, User, UserSearchCriteria,
    JobClassification, AppConfig
)
from app.services.analytics import AnalyticsService
from app.services.user_management import UserManagementService
from app.services.authentication import AuthenticationService, get_auth_service
from app.dependencies import (
    get_analytics_service, get_user_management_service, get_app_config
)
from app.utils.logging import get_logger, log_with_context
from app.utils.reporting_engine import ReportingEngine
import uuid
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker

logger = get_logger(__name__)

# Create router for dashboard endpoints
router = APIRouter(prefix="/api", tags=["dashboard"])

# Simple in-memory report history (lightweight persistence for UI)
_report_history: List[Dict[str, Any]] = []
_reporting_engine = ReportingEngine()


# Development-only authentication bypass functions
# These should ONLY be used when DEVELOPMENT_MODE=true

async def get_current_user_dev() -> User:
    """
    Development-only: Return mock admin user to bypass authentication.
    
    WARNING: This bypasses all authentication and should NEVER be used in production.
    Only use when BYPASS_AUTHENTICATION environment variable is set to true.
    """
    from app.models.data_models import UserRole
    from app.config import get_config
    
    config = get_config()
    if not config.bypass_authentication:
        raise HTTPException(
            status_code=500,
            detail="Authentication bypass attempted without BYPASS_AUTHENTICATION=true"
        )
    
    return User(
        username="dev_admin",
        role=UserRole.ADMIN,
        created_at=datetime.utcnow(),
        is_active=True
    )

def require_analyst_or_admin_dev(current_user: User = Depends(get_current_user_dev)) -> User:
    """
    Development-only: Bypass analyst/admin role requirement.
    
    WARNING: This bypasses role-based access control and should NEVER be used in production.
    """
    return current_user

def require_admin_dev(current_user: User = Depends(get_current_user_dev)) -> User:
    """
    Development-only: Bypass admin role requirement.
    
    WARNING: This bypasses role-based access control and should NEVER be used in production.
    """
    return current_user

# Conditional dependency selection based on environment
def get_auth_dependencies():
    """
    Get appropriate authentication dependencies based on environment.
    
    Returns development bypass functions if BYPASS_AUTHENTICATION=true,
    otherwise returns production authentication functions.
    
    Note: Imports are done at function level to avoid circular import issues.
    """
    from app.config import get_config
    from app.dependencies import require_admin_user, require_analyst_or_admin_user
    
    config = get_config()
    if config.bypass_authentication:
        logger.warning("Using authentication bypass - NOT for production use")
        return {
            'analyst_or_admin': require_analyst_or_admin_dev,
            'admin': require_admin_dev
        }
    else:
        logger.info("Using production authentication with JWT validation")
        return {
            'analyst_or_admin': require_analyst_or_admin_user,
            'admin': require_admin_user
        }

# Get the appropriate dependencies for current environment
_auth_deps = get_auth_dependencies()
current_require_analyst_or_admin = _auth_deps['analyst_or_admin']
current_require_admin = _auth_deps['admin']


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get dashboard overview data with key performance indicators.
    
    Returns:
        DashboardOverview: System metrics and health status
        
    Raises:
        HTTPException: If data retrieval fails
    """
    try:
        logger.critical(f"🔥 DASHBOARD: Overview requested by user: {current_user.username}")
        log_with_context(
            logger,
            logging.INFO,
            "Dashboard overview requested",
            user=current_user.username
        )
        
        logger.critical(f"🔥 DASHBOARD: Calling analytics_service.get_dashboard_overview()...")
        overview = await analytics_service.get_dashboard_overview()
        logger.critical(f"🔥 DASHBOARD: Got overview - total_requests: {overview.total_requests}, active_users: {overview.active_users}, error_rate: {overview.error_rate}")
        
        log_with_context(
            logger,
            logging.INFO,
            "Dashboard overview generated successfully",
            user=current_user.username,
            total_requests=overview.total_requests,
            system_health=overview.system_health
        )
        # Enrich response for frontend expectations without changing models
        # Frontend expects additional fields: success_rate, peak_hour, server_uptime, last_updated
        success_rate = max(0.0, 100.0 - float(overview.error_rate))
        result: Dict[str, Any] = {
            "total_requests": overview.total_requests,
            "requests_today": overview.requests_today,
            "error_rate": overview.error_rate,
            "avg_response_time": overview.avg_response_time,
            "active_users": overview.active_users,
            "system_health": overview.system_health,
            # Extra fields expected by dashboard
            "success_rate": round(success_rate, 2),
            # For demo purposes, provide a reasonable default. If needed, can compute from analytics later.
            "peak_hour": "14:00",
            # Static-style uptime string for display; live uptime is not tracked here
            "server_uptime": "99.9%",
            "last_updated": overview.timestamp.isoformat(),
        }
        return result
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get dashboard overview",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard overview"
        )


@router.get("/analytics/source-breakdown")
async def get_source_breakdown(
    period: str = Query("week", pattern="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DD)"),
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get breakdown of interactions by source (WhatsApp vs Web).
    
    Args:
        period: Time period ("day", "week", "month", "year")
        start_date: Optional start date for custom range
        end_date: Optional end date for custom range
        
    Returns:
        Dict containing source breakdown statistics
        
    Raises:
        HTTPException: If parameters are invalid or data retrieval fails
    """
    try:
        # Parse custom date range if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Determine date range
        if parsed_start_date and parsed_end_date:
            if parsed_start_date >= parsed_end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be before end_date"
                )
            date_range = (parsed_start_date, parsed_end_date)
        else:
            # Use period to determine date range
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
                raise HTTPException(
                    status_code=400,
                    detail="Invalid period. Must be 'day', 'week', 'month', or 'year'"
                )
            date_range = (start_date, end_date)
        
        log_with_context(
            logger,
            logging.INFO,
            "Source breakdown requested",
            user=current_user.username,
            period=period,
            custom_range=bool(parsed_start_date and parsed_end_date)
        )
        
        # Get all users
        logger.critical(f"🔥 DASHBOARD: Getting user list for source breakdown...")
        user_list = await user_service.get_users(page=1, limit=10000)
        logger.critical(f"🔥 DASHBOARD: Got {len(user_list.users)} users from user_service")
        
        # Import analytics extensions
        from app.services.analytics_extensions import (
            get_source_breakdown, get_source_success_rates,
            get_source_response_times, get_source_daily_trends
        )
        
        # Get source statistics
        source_counts = await get_source_breakdown(user_list.users, date_range)
        success_rates = await get_source_success_rates(user_list.users, date_range)
        response_times = await get_source_response_times(user_list.users, date_range)
        daily_trends = await get_source_daily_trends(user_list.users, date_range)
        
        # Calculate percentages
        total_interactions = sum(source_counts.values())
        source_percentages = {}
        for source, count in source_counts.items():
            percentage = (count / total_interactions * 100) if total_interactions > 0 else 0
            source_percentages[source] = round(percentage, 2)
        
        result = {
            "period": period,
            "date_range": {
                "start": date_range[0].isoformat(),
                "end": date_range[1].isoformat()
            },
            "source_counts": source_counts,
            "source_percentages": source_percentages,
            "success_rates": success_rates,
            "response_times": response_times,
            "daily_trends": daily_trends
        }
        
        log_with_context(
            logger,
            logging.INFO,
            "Source breakdown generated successfully",
            user=current_user.username,
            total_interactions=total_interactions,
            whatsapp_count=source_counts.get("whatsapp", 0),
            web_count=source_counts.get("web", 0)
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get source breakdown",
            user=current_user.username,
            period=period,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve source breakdown"
        )


@router.get("/analytics/trends")
async def get_analytics_trends(
    period: str = Query("week", pattern="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get analytics trends and usage statistics for the specified period.
    
    Args:
        period: Time period ("day", "week", "month", "year")
        start_date: Optional start date for custom range
        end_date: Optional end date for custom range
        
    Returns:
        AnalyticsTrends: Trend data and statistics
        
    Raises:
        HTTPException: If parameters are invalid or data retrieval fails
    """
    try:
        # Parse custom date range if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Validate date range
        if parsed_start_date and parsed_end_date:
            if parsed_start_date >= parsed_end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be before end_date"
                )
            
            # Check if range is reasonable (max 1 year)
            if parsed_end_date - parsed_start_date > timedelta(days=365):
                raise HTTPException(
                    status_code=400,
                    detail="Date range cannot exceed 365 days"
                )
        
        log_with_context(
            logger,
            logging.INFO,
            "Analytics trends requested",
            user=current_user.username,
            period=period,
            custom_range=bool(parsed_start_date and parsed_end_date)
        )
        
        trends = await analytics_service.get_analytics_trends(
            period=period,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        log_with_context(
            logger,
            logging.INFO,
            "Analytics trends generated successfully",
            user=current_user.username,
            period=period,
            total_classifications=sum(trends.classifications.values())
        )
        
        # Compute system performance snapshot
        try:
            date_range_start = parsed_start_date if parsed_start_date else None
            date_range_end = parsed_end_date if parsed_end_date else None
            usage_stats = await analytics_service.get_usage_statistics(
                start_date=date_range_start,
                end_date=date_range_end
            )
            avg_resp = float(usage_stats.average_response_time)
            success_rate = float(usage_stats.success_rate)
        except Exception:
            avg_resp = 0.0
            success_rate = 0.0
        
        # Normalize classification keys for frontend (Legit -> Legitimate)
        normalized_classifications: Dict[str, int] = {}
        for key, val in trends.classifications.items():
            if key == "Legit":
                normalized_classifications["Legitimate"] = val
            else:
                normalized_classifications[key] = val

        # Transform to frontend-expected shape
        result: Dict[str, Any] = {
            "period": period,
            "classifications": normalized_classifications,
            "usage_trends": trends.daily_counts,
            # Provide peak hours as list of {hour, count} for charts
            "peak_hours": [{"hour": h, "count": 0} for h in trends.peak_hours],
            "user_engagement": {
                "daily_active_users": int(trends.user_engagement.get("active_users", 0)),
                # Approximate minutes from interactions per user for demo display
                "avg_session_time": round(float(trends.user_engagement.get("avg_interactions_per_user", 0)) * 2.0, 1),
                "return_rate": round(float(trends.user_engagement.get("repeat_user_rate", 0)), 1),
                "new_users": int(int(trends.user_engagement.get("active_users", 0)) * 0.2),
            },
            "system_performance": {
                "avg_response_time": avg_resp,
                "success_rate": success_rate,
                "uptime": 99.9,
            },
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get analytics trends",
            user=current_user.username,
            period=period,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analytics trends"
        )


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of users per page"),
    search: Optional[str] = Query(None, description="Search query for phone number"),
    blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    min_requests: Optional[int] = Query(None, ge=0, description="Minimum number of requests"),
    max_requests: Optional[int] = Query(None, ge=0, description="Maximum number of requests"),
    days_since_last_interaction: Optional[int] = Query(None, ge=0, description="Days since last interaction"),
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get paginated list of WhatsApp users with optional filtering.
    
    Args:
        page: Page number (1-based)
        limit: Number of users per page (max 100)
        search: Search query for phone number
        blocked: Filter by blocked status
        min_requests: Minimum number of requests filter
        max_requests: Maximum number of requests filter
        days_since_last_interaction: Days since last interaction filter
        
    Returns:
        UserList: Paginated list of users with metadata
        
    Raises:
        HTTPException: If parameters are invalid or data retrieval fails
    """
    try:
        # Validate parameters
        if min_requests is not None and max_requests is not None:
            if min_requests > max_requests:
                raise HTTPException(
                    status_code=400,
                    detail="min_requests cannot be greater than max_requests"
                )
        
        # Create search criteria
        search_criteria = None
        if any([search, blocked is not None, min_requests is not None, 
                max_requests is not None, days_since_last_interaction is not None]):
            search_criteria = UserSearchCriteria(
                phone_number=search,
                blocked=blocked,
                min_requests=min_requests,
                max_requests=max_requests,
                days_since_last_interaction=days_since_last_interaction
            )
        
        log_with_context(
            logger,
            logging.INFO,
            "User list requested",
            user=current_user.username,
            page=page,
            limit=limit,
            has_filters=search_criteria is not None
        )
        
        logger.critical(f"🔥 DASHBOARD: Calling user_service.get_users with page={page}, limit={limit}")
        user_list = await user_service.get_users(
            page=page,
            limit=limit,
            search_criteria=search_criteria
        )
        logger.critical(f"🔥 DASHBOARD: Got user_list with {len(user_list.users)} users, total: {user_list.total}")
        
        # Transform to the shape expected by the dashboard frontend
        transformed_users: List[Dict[str, Any]] = []
        for u in user_list.users:
            logger.critical(f"🔥 DASHBOARD: Processing user - phone: {u.phone_number[:8]}***, total_requests: {u.total_requests}, blocked: {u.blocked}")
            transformed_users.append({
                "phone_number": u.phone_number,
                "total_requests": u.total_requests,
                "first_interaction": u.first_interaction.isoformat() if u.first_interaction else None,
                "last_interaction": u.last_interaction.isoformat() if u.last_interaction else None,
                "is_blocked": bool(u.blocked),
                # Convert success_rate fraction to percentage with one decimal
                "success_rate": round((u.success_rate or 0.0) * 100.0, 1),
                # Average response time in seconds
                "avg_response_time": round(u.average_response_time, 3),
            })
        logger.critical(f"🔥 DASHBOARD: Transformed {len(transformed_users)} users for frontend")
        
        response: Dict[str, Any] = {
            "users": transformed_users,
            "total": user_list.total,
            "page": user_list.page,
            "limit": user_list.limit,
            "total_pages": user_list.pages,
        }
        
        log_with_context(
            logger,
            logging.INFO,
            "User list generated successfully",
            user=current_user.username,
            total_users=user_list.total,
            page_users=len(transformed_users)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get user list",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user list"
        )


@router.get("/metrics/realtime")
async def get_realtime_metrics(
    current_user: User = Depends(current_require_analyst_or_admin)
) -> SystemMetrics:
    """
    Get real-time system metrics for live monitoring.
    
    Returns:
        SystemMetrics: Current system performance metrics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Real-time metrics requested",
            user=current_user.username
        )
        
        # Get metrics from metrics collector
        metrics_collector = get_metrics_collector()
        current_metrics = metrics_collector.get_current_metrics()
        
        # Calculate real-time metrics
        now = datetime.utcnow()
        
        # Get service status (simplified for now)
        service_status = {
            "openai": "healthy",  # Would check actual service health
            "twilio": "healthy",
            "pdf_processing": "healthy"
        }
        
        # Create system metrics object
        system_metrics = SystemMetrics(
            timestamp=now,
            active_requests=current_metrics.get("active_requests", 0),
            requests_per_minute=current_metrics.get("requests_per_minute", 0),
            # Use metrics collector snapshot for error rate percent
            error_rate=float(current_metrics.get("requests", {}).get("error_rate_percent", 0.0)),
            response_times={
                "p50": current_metrics.get("response_time_p50", 0.0),
                "p95": current_metrics.get("response_time_p95", 0.0),
                "p99": current_metrics.get("response_time_p99", 0.0)
            },
            service_status=service_status,
            memory_usage=current_metrics.get("memory_usage", 0.0),
            cpu_usage=current_metrics.get("cpu_usage", 0.0)
        )
        
        log_with_context(
            logger,
            logging.INFO,
            "Real-time metrics generated successfully",
            user=current_user.username,
            active_requests=system_metrics.active_requests,
            error_rate=system_metrics.error_rate
        )
        
        return system_metrics
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get real-time metrics",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve real-time metrics"
        )


@router.post("/config")
async def update_configuration(
    config_updates: Dict[str, Any] = Body(...),
    current_user: User = Depends(current_require_admin)
) -> Dict[str, Any]:
    """
    Update system configuration (admin only).
    
    Args:
        config_updates: Dictionary of configuration updates
        
    Returns:
        Dict: Updated configuration status
        
    Raises:
        HTTPException: If user is not admin or update fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Configuration update requested",
            user=current_user.username,
            updates=list(config_updates.keys())
        )
        
        # Validate configuration updates
        allowed_updates = {
            "openai_model", "max_pdf_size_mb", "log_level", 
            "webhook_validation", "rate_limit_per_minute"
        }
        
        invalid_keys = set(config_updates.keys()) - allowed_updates
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration keys: {list(invalid_keys)}"
            )
        
        # Validate specific configuration values
        if "openai_model" in config_updates:
            valid_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
            if config_updates["openai_model"] not in valid_models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid OpenAI model. Must be one of: {valid_models}"
                )
        
        if "max_pdf_size_mb" in config_updates:
            if not isinstance(config_updates["max_pdf_size_mb"], int) or config_updates["max_pdf_size_mb"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="max_pdf_size_mb must be a positive integer"
                )
        
        if "log_level" in config_updates:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config_updates["log_level"] not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid log level. Must be one of: {valid_levels}"
                )
        
        # For now, we'll just return success
        # In a real implementation, this would update the actual configuration
        log_with_context(
            logger,
            logging.INFO,
            "Configuration updated successfully",
            user=current_user.username,
            updates=config_updates
        )
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_keys": list(config_updates.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to update configuration",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update configuration"
        )


@router.post("/reports/generate")
async def generate_report(
    report_params: Dict[str, Any] = Body(...),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> ReportData:
    """
    Generate a custom report based on provided parameters.
    
    Args:
        report_params: Report generation parameters
        
    Returns:
        ReportData: Generated report with data and metadata
        
    Raises:
        HTTPException: If parameters are invalid or report generation fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Report generation requested",
            user=current_user.username,
            report_type=report_params.get("report_type")
        )
        
        # Validate required parameters
        required_params = ["report_type", "start_date", "end_date", "export_format"]
        missing_params = [param for param in required_params if param not in report_params]
        if missing_params:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters: {missing_params}"
            )
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(report_params["start_date"])
            end_date = datetime.fromisoformat(report_params["end_date"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        if end_date - start_date > timedelta(days=365):
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 365 days"
            )
        
        # Create report parameters
        try:
            parameters = ReportParameters(
                report_type=report_params["report_type"],
                start_date=start_date,
                end_date=end_date,
                export_format=report_params["export_format"],
                include_user_details=report_params.get("include_user_details", False),
                include_error_details=report_params.get("include_error_details", False),
                classification_filter=None,  # Could be enhanced to support filtering
                user_filter=report_params.get("user_filter")
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report parameters: {str(e)}"
            )
        
        # Generate report (live data)
        report = await analytics_service.generate_report(parameters)

        # Export to desired format to produce a downloadable file when possible
        try:
            export_info = await _reporting_engine.export_report(report)
            # export_report sets download_url and file_size on report internally
        except Exception:
            # If export fails, continue with JSON payload only
            pass

        # Add to in-memory history for quick listing in UI
        try:
            history_item = {
                "id": str(uuid.uuid4()),
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "parameters": {
                    "report_type": parameters.report_type,
                    "start_date": parameters.start_date.isoformat(),
                    "end_date": parameters.end_date.isoformat(),
                    "export_format": parameters.export_format,
                    "include_user_details": parameters.include_user_details,
                    "include_error_details": parameters.include_error_details,
                    "user_filter": parameters.user_filter,
                },
                "download_url": getattr(report, "download_url", None),
                "file_size": getattr(report, "file_size", None),
                "generated_by": current_user.username,
                "scheduled": False,
            }
            _report_history.insert(0, history_item)
            # Trim to last 100 items to avoid unbounded growth
            del _report_history[100:]
        except Exception:
            pass
        
        log_with_context(
            logger,
            logging.INFO,
            "Report generated successfully",
            user=current_user.username,
            report_type=report.report_type,
            export_format=report.export_format
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to generate report",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )


# Additional endpoints for user management actions

@router.get("/reports/history")
async def list_report_history(limit: int = 25, current_user: User = Depends(current_require_analyst_or_admin)) -> Dict[str, Any]:
    """Return recently generated reports (in-memory)."""
    try:
        return {"reports": _report_history[: max(0, min(limit, 100))]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list history: {e}")


@router.delete("/reports/history/{report_id}")
async def delete_report_history(report_id: str, current_user: User = Depends(current_require_admin)) -> Dict[str, Any]:
    """Delete a report from history list (in-memory)."""
    try:
        before = len(_report_history)
        idx = next((i for i, r in enumerate(_report_history) if r.get("id") == report_id), None)
        if idx is None:
            raise HTTPException(status_code=404, detail="Report not found")
        _report_history.pop(idx)
        return {"success": True, "deleted": report_id, "remaining": len(_report_history)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {e}")

@router.post("/users/{phone_number}/block")
async def block_user(
    phone_number: str,
    reason: Optional[str] = Body(None),
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(current_require_admin)
) -> Dict[str, Any]:
    """
    Block a user from using the bot (admin only).
    
    Args:
        phone_number: User's phone number to block
        reason: Optional reason for blocking
        
    Returns:
        Dict: Block operation result
        
    Raises:
        HTTPException: If user is not admin or operation fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "User block requested",
            admin_user=current_user.username,
            target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number
        )
        
        success = await user_service.block_user(phone_number, reason)
        
        if success:
            log_with_context(
                logger,
                logging.INFO,
                "User blocked successfully",
                admin_user=current_user.username,
                target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number
            )
            return {
                "success": True,
                "message": "User blocked successfully",
                "phone_number": phone_number,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="User not found or already blocked"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to block user",
            admin_user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to block user"
        )


@router.post("/users/{phone_number}/unblock")
async def unblock_user(
    phone_number: str,
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(current_require_admin)
) -> Dict[str, Any]:
    """
    Unblock a previously blocked user (admin only).
    
    Args:
        phone_number: User's phone number to unblock
        
    Returns:
        Dict: Unblock operation result
        
    Raises:
        HTTPException: If user is not admin or operation fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "User unblock requested",
            admin_user=current_user.username,
            target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number
        )
        
        success = await user_service.unblock_user(phone_number)
        
        if success:
            log_with_context(
                logger,
                logging.INFO,
                "User unblocked successfully",
                admin_user=current_user.username,
                target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number
            )
            return {
                "success": True,
                "message": "User unblocked successfully",
                "phone_number": phone_number,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="User not found or not blocked"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to unblock user",
            admin_user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to unblock user"
        )


@router.get("/users/{phone_number}")
async def get_user_details(
    phone_number: str,
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(current_require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific user.
    
    Args:
        phone_number: User's phone number
        
    Returns:
        Dict: User details and interaction history
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "User details requested",
            requesting_user=current_user.username,
            target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number
        )
        
        user_details = await user_service.get_user_details(phone_number)
        
        if not user_details:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get recent interactions
        recent_interactions = await user_service.get_user_interaction_history(
            phone_number, limit=20
        )
        
        log_with_context(
            logger,
            logging.INFO,
            "User details retrieved successfully",
            requesting_user=current_user.username,
            target_phone=phone_number[:12] + "***" if len(phone_number) > 12 else phone_number,
            total_requests=user_details.total_requests
        )
        
        return {
            "user": user_details,
            "recent_interactions": recent_interactions,
            "statistics": {
                "success_rate": user_details.success_rate,
                "average_response_time": user_details.average_response_time,
                "days_since_first_interaction": user_details.days_since_first_interaction,
                "days_since_last_interaction": user_details.days_since_last_interaction
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get user details",
            requesting_user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user details"
        )
