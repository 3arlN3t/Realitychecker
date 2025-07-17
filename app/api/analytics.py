"""
Analytics API endpoints for the Reality Checker WhatsApp bot.

This module provides REST API endpoints for advanced analytics features including:
- Pattern recognition
- A/B testing
- User behavior clustering
- Predictive analytics
- Custom report generation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse, FileResponse

from app.models.data_models import (
    DashboardOverview, AnalyticsTrends, UserList, SystemMetrics, 
    ReportData, ReportParameters, User, UserSearchCriteria,
    JobClassification, AppConfig
)
from app.services.analytics import AnalyticsService
from app.services.user_management import UserManagementService
from app.services.authentication import get_auth_service
from app.dependencies import (
    get_analytics_service, get_user_management_service, get_app_config
)
from app.utils.logging import get_logger, log_with_context
from app.utils.pattern_recognition import PatternRecognitionEngine
from app.utils.ab_testing import ABTesting
from app.utils.reporting_engine import ReportingEngine, ReportScheduler
from app.api.dashboard import get_current_user, require_admin, require_analyst_or_admin

logger = get_logger(__name__)

# Create router for analytics endpoints
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Initialize analytics engines
pattern_engine = PatternRecognitionEngine()
ab_testing_engine = ABTesting({})
reporting_engine = ReportingEngine()
report_scheduler = ReportScheduler(reporting_engine)


@router.get("/patterns")
async def detect_patterns(
    metric: str = Query(..., description="Metric name to analyze"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Detect patterns in time series data for a specific metric.
    
    Args:
        metric: Metric name to analyze
        days: Number of days to analyze
        
    Returns:
        Dictionary with detected patterns
        
    Raises:
        HTTPException: If parameters are invalid or pattern detection fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Pattern detection requested",
            user=current_user.username,
            metric=metric,
            days=days
        )
        
        # Get time series data for the metric
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get metric data from analytics service
        # This is a simplified example - in a real implementation, you would
        # retrieve actual time series data from your analytics service
        time_series = await analytics_service.get_metric_time_series(
            metric_name=metric,
            start_date=start_date,
            end_date=end_date
        )
        
        # Detect patterns
        patterns = await pattern_engine.detect_patterns(time_series, days)
        
        # Convert patterns to serializable format
        serializable_patterns = []
        for pattern in patterns:
            serializable_patterns.append({
                "pattern_type": pattern.pattern_type.value,
                "confidence": pattern.confidence,
                "start_time": pattern.start_time.isoformat(),
                "end_time": pattern.end_time.isoformat(),
                "magnitude": pattern.magnitude,
                "description": pattern.description,
                "supporting_data": pattern.supporting_data
            })
        
        log_with_context(
            logger,
            logging.INFO,
            "Pattern detection completed",
            user=current_user.username,
            metric=metric,
            patterns_found=len(serializable_patterns)
        )
        
        return {
            "metric": metric,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "patterns_found": len(serializable_patterns),
            "patterns": serializable_patterns
        }
        
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to detect patterns",
            user=current_user.username,
            metric=metric,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect patterns: {str(e)}"
        )


@router.post("/ab-tests")
async def create_ab_test(
    test_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Create a new A/B test.
    
    Args:
        test_config: A/B test configuration
        
    Returns:
        Created A/B test details
        
    Raises:
        HTTPException: If parameters are invalid or test creation fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "A/B test creation requested",
            user=current_user.username,
            test_name=test_config.get("name")
        )
        
        # Create test
        test = await ab_testing_engine.create_test(test_config)
        
        # Convert to serializable format
        serializable_test = {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "status": test.status.value,
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type.value,
                    "traffic_allocation": v.traffic_allocation
                }
                for v in test.variants
            ],
            "metrics": [
                {
                    "id": m.id,
                    "name": m.name,
                    "primary": m.primary
                }
                for m in test.metrics
            ],
            "created_at": test.created_at.isoformat(),
            "owner": test.owner
        }
        
        log_with_context(
            logger,
            logging.INFO,
            "A/B test created successfully",
            user=current_user.username,
            test_id=test.id,
            test_name=test.name
        )
        
        return serializable_test
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to create A/B test",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create A/B test: {str(e)}"
        )


@router.get("/ab-tests/{test_id}")
async def get_ab_test(
    test_id: str,
    current_user: User = Depends(require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Get details of an A/B test.
    
    Args:
        test_id: ID of the test
        
    Returns:
        A/B test details
        
    Raises:
        HTTPException: If test not found
    """
    try:
        if test_id not in ab_testing_engine.tests:
            raise HTTPException(
                status_code=404,
                detail=f"A/B test {test_id} not found"
            )
        
        test = ab_testing_engine.tests[test_id]
        
        # Calculate results if test is running or completed
        if test.status.value in ["running", "completed"]:
            await ab_testing_engine.calculate_test_results(test_id)
        
        # Convert to serializable format
        serializable_test = {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "status": test.status.value,
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type.value,
                    "traffic_allocation": v.traffic_allocation
                }
                for v in test.variants
            ],
            "metrics": [
                {
                    "id": m.id,
                    "name": m.name,
                    "primary": m.primary
                }
                for m in test.metrics
            ],
            "created_at": test.created_at.isoformat(),
            "updated_at": test.updated_at.isoformat(),
            "owner": test.owner,
            "start_date": test.start_date.isoformat() if test.start_date else None,
            "end_date": test.end_date.isoformat() if test.end_date else None
        }
        
        # Add results if available
        if test.results:
            serializable_results = {}
            for metric_id, results in test.results.items():
                serializable_results[metric_id] = [
                    {
                        "variant_id": r.variant_id,
                        "sample_size": r.sample_size,
                        "value": r.value,
                        "confidence_interval": r.confidence_interval,
                        "p_value": r.p_value,
                        "significant": r.significant,
                        "lift": r.lift
                    }
                    for r in results
                ]
            serializable_test["results"] = serializable_results
        
        return serializable_test
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to get A/B test details",
            user=current_user.username,
            test_id=test_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get A/B test details: {str(e)}"
        )


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(
    test_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Start an A/B test.
    
    Args:
        test_id: ID of the test to start
        
    Returns:
        Updated A/B test details
        
    Raises:
        HTTPException: If test not found or cannot be started
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "A/B test start requested",
            user=current_user.username,
            test_id=test_id
        )
        
        # Start test
        test = await ab_testing_engine.start_test(test_id)
        
        # Convert to serializable format
        serializable_test = {
            "id": test.id,
            "name": test.name,
            "status": test.status.value,
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat() if test.end_date else None
        }
        
        log_with_context(
            logger,
            logging.INFO,
            "A/B test started successfully",
            user=current_user.username,
            test_id=test.id,
            test_name=test.name
        )
        
        return serializable_test
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to start A/B test",
            user=current_user.username,
            test_id=test_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start A/B test: {str(e)}"
        )


@router.post("/ab-tests/{test_id}/stop")
async def stop_ab_test(
    test_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Stop an A/B test.
    
    Args:
        test_id: ID of the test to stop
        
    Returns:
        Updated A/B test details with results
        
    Raises:
        HTTPException: If test not found or cannot be stopped
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "A/B test stop requested",
            user=current_user.username,
            test_id=test_id
        )
        
        # Stop test
        test = await ab_testing_engine.stop_test(test_id)
        
        # Get recommendation
        recommendation = await ab_testing_engine.get_test_recommendation(test_id)
        
        # Convert to serializable format
        serializable_test = {
            "id": test.id,
            "name": test.name,
            "status": test.status.value,
            "start_date": test.start_date.isoformat() if test.start_date else None,
            "end_date": test.end_date.isoformat() if test.end_date else None,
            "recommendation": recommendation
        }
        
        # Add results
        serializable_results = {}
        for metric_id, results in test.results.items():
            serializable_results[metric_id] = [
                {
                    "variant_id": r.variant_id,
                    "sample_size": r.sample_size,
                    "value": r.value,
                    "confidence_interval": r.confidence_interval,
                    "p_value": r.p_value,
                    "significant": r.significant,
                    "lift": r.lift
                }
                for r in results
            ]
        serializable_test["results"] = serializable_results
        
        log_with_context(
            logger,
            logging.INFO,
            "A/B test stopped successfully",
            user=current_user.username,
            test_id=test.id,
            test_name=test.name
        )
        
        return serializable_test
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to stop A/B test",
            user=current_user.username,
            test_id=test_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop A/B test: {str(e)}"
        )


@router.post("/user-clustering")
async def cluster_users(
    clustering_params: Dict[str, Any] = Body(...),
    user_service: UserManagementService = Depends(get_user_management_service),
    current_user: User = Depends(require_analyst_or_admin)
) -> Dict[str, Any]:
    """
    Cluster users based on behavior features.
    
    Args:
        clustering_params: Clustering parameters
        
    Returns:
        Clustering results with user segments
        
    Raises:
        HTTPException: If parameters are invalid or clustering fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "User clustering requested",
            user=current_user.username,
            features=clustering_params.get("features")
        )
        
        # Validate parameters
        if "features" not in clustering_params:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameter: features"
            )
        
        features = clustering_params["features"]
        
        # Get user data
        user_list = await user_service.get_users(page=1, limit=10000)
        
        # Extract user features
        user_data = []
        for user in user_list.users:
            user_features = {
                "user_id": user.phone_number,
                "total_requests": user.total_requests,
                "days_since_first": user.days_since_first_interaction,
                "days_since_last": user.days_since_last_interaction,
                "avg_response_time": user.average_response_time,
                "success_rate": user.success_rate
            }
            
            # Add message type counts
            text_messages = sum(1 for i in user.interaction_history if i.message_type == "text")
            pdf_messages = sum(1 for i in user.interaction_history if i.message_type == "pdf")
            user_features["text_messages"] = text_messages
            user_features["pdf_messages"] = pdf_messages
            
            # Add classification counts
            classifications = {"Legit": 0, "Suspicious": 0, "Likely Scam": 0}
            for interaction in user.interaction_history:
                if interaction.analysis_result:
                    classification = interaction.analysis_result.classification_text
                    classifications[classification] = classifications.get(classification, 0) + 1
            
            user_features["legit_count"] = classifications["Legit"]
            user_features["suspicious_count"] = classifications["Suspicious"]
            user_features["scam_count"] = classifications["Likely Scam"]
            
            user_data.append(user_features)
        
        # Perform clustering
        from app.utils.pattern_recognition import UserBehaviorClusteringEngine
        clustering_engine = UserBehaviorClusteringEngine()
        
        clustering_result = await clustering_engine.cluster_users(user_data, features)
        
        if not clustering_result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=f"Clustering failed: {clustering_result.get('reason', 'Unknown error')}"
            )
        
        # Identify user segments
        segments = await clustering_engine.identify_user_segments(clustering_result)
        
        log_with_context(
            logger,
            logging.INFO,
            "User clustering completed",
            user=current_user.username,
            clusters=clustering_result.get("n_clusters"),
            segments=len(segments)
        )
        
        return {
            "clustering_result": clustering_result,
            "user_segments": segments,
            "features_used": features,
            "total_users": len(user_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to cluster users",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cluster users: {str(e)}"
        )


@router.post("/reports/schedule")
async def schedule_report(
    schedule_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Schedule a report for automated generation.
    
    Args:
        schedule_config: Report schedule configuration
        
    Returns:
        Scheduled report details
        
    Raises:
        HTTPException: If parameters are invalid or scheduling fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Report scheduling requested",
            user=current_user.username,
            report_type=schedule_config.get("report_type"),
            schedule=schedule_config.get("schedule")
        )
        
        # Add owner to config
        schedule_config["owner"] = current_user.username
        
        # Schedule report
        schedule = await report_scheduler.schedule_report(schedule_config)
        
        # Convert to serializable format
        serializable_schedule = {
            "id": schedule["id"],
            "report_type": schedule["report_type"],
            "schedule": schedule["schedule"],
            "export_format": schedule["export_format"],
            "created_at": schedule["created_at"].isoformat(),
            "next_run": schedule["next_run"].isoformat(),
            "status": schedule["status"],
            "owner": schedule["owner"]
        }
        
        log_with_context(
            logger,
            logging.INFO,
            "Report scheduled successfully",
            user=current_user.username,
            schedule_id=schedule["id"],
            report_type=schedule["report_type"]
        )
        
        return serializable_schedule
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to schedule report",
            user=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule report: {str(e)}"
        )


@router.get("/reports/download/{report_id}")
async def download_report(
    report_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(require_analyst_or_admin)
) -> FileResponse:
    """
    Download a generated report file.
    
    Args:
        report_id: ID of the report to download
        
    Returns:
        File response with the report
        
    Raises:
        HTTPException: If report not found or download fails
    """
    try:
        log_with_context(
            logger,
            logging.INFO,
            "Report download requested",
            user=current_user.username,
            report_id=report_id
        )
        
        # Get report details
        report = await analytics_service.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found"
            )
        
        if not report.download_url:
            raise HTTPException(
                status_code=400,
                detail=f"Report {report_id} has no download URL"
            )
        
        # Get file path from download URL
        file_path = report.download_url
        
        # Check if file exists
        import os
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Report file not found"
            )
        
        # Determine media type
        media_type = None
        if file_path.endswith(".json"):
            media_type = "application/json"
        elif file_path.endswith(".csv"):
            media_type = "text/csv"
        elif file_path.endswith(".pdf"):
            media_type = "application/pdf"
        elif file_path.endswith(".xlsx"):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Generate filename
        filename = os.path.basename(file_path)
        
        log_with_context(
            logger,
            logging.INFO,
            "Report download successful",
            user=current_user.username,
            report_id=report_id,
            file_path=file_path
        )
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to download report",
            user=current_user.username,
            report_id=report_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report: {str(e)}"
        )