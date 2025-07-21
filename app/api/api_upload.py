"""
API endpoints for job advertisement analysis without templates.

This module provides API endpoints for analyzing job advertisements
without requiring templates, for use in API-only scenarios.
"""

import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import get_config
from app.models.data_models import AppConfig, MessageType, AnalysisResult
from app.services.message_handler import MessageHandlerService
from app.dependencies import get_message_handler_service, get_app_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.error_handling import handle_error, ErrorCategory
from app.utils.security import SecurityValidator

logger = get_logger(__name__)

# Create router for API endpoints
router = APIRouter(prefix="/api/analyze", tags=["api"])


@router.get("/status")
async def api_status():
    """
    API status endpoint.
    
    Returns:
        Dict: API status information
    """
    return {
        "status": "online",
        "message": "Reality Checker API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/test")
async def api_test_page(request: Request):
    """
    Serve the API test page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered API test page
    """
    try:
        from fastapi.templating import Jinja2Templates
        import os
        
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        templates = Jinja2Templates(directory=templates_dir)
        
        return templates.TemplateResponse(
            "api_test.html",
            {"request": request, "title": "Reality Checker API Test"}
        )
    except Exception as e:
        logger.error(f"Error rendering API test page: {e}")
        return JSONResponse(
            content={
                "message": "API test page is not available",
                "error": str(e)
            }
        )


@router.post("/text")
async def analyze_text_api(
    request: Request,
    background_tasks: BackgroundTasks,
    job_text: str = Form(...),
    message_handler: MessageHandlerService = Depends(get_message_handler_service),
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Analyze job advertisement text via API.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        job_text: Job advertisement text to analyze
        message_handler: Injected MessageHandlerService instance
        config: Application configuration
        
    Returns:
        Dict containing analysis results or error information
        
    Raises:
        HTTPException: For validation or processing errors
    """
    correlation_id = get_correlation_id()
    analysis_id = str(uuid.uuid4())
    
    log_with_context(
        logger,
        logging.INFO,
        "Received API text analysis request",
        analysis_id=analysis_id,
        text_length=len(job_text) if job_text else 0,
        correlation_id=correlation_id
    )
    
    try:
        # Validate and sanitize input
        security_validator = SecurityValidator()
        sanitized_text = security_validator.sanitize_text(job_text)
        
        if not sanitized_text or len(sanitized_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Job advertisement text is too short. Please provide more details."
            )
        
        if len(sanitized_text) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Text is too long. Please limit to 10,000 characters."
            )
        
        # Create message data for processing
        message_data = {
            'message_type': MessageType.TEXT,
            'content': sanitized_text,
            'user_id': f"api-{request.client.host}",  # Anonymous user ID based on IP
            'source': 'web',
            'analysis_id': analysis_id,
            'correlation_id': correlation_id
        }
        
        # Process the message through the message handler service
        log_with_context(
            logger,
            logging.INFO,
            "Processing API text through MessageHandlerService",
            analysis_id=analysis_id,
            correlation_id=correlation_id
        )
        
        analysis_result = await message_handler.process_web_message(message_data)
        
        # Return analysis results
        return {
            "success": True,
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "result": {
                "trust_score": analysis_result.trust_score,
                "classification": analysis_result.classification,
                "reasoning": analysis_result.reasoning
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
        
    except Exception as e:
        # Handle unexpected errors with centralized error handler
        user_message, error_info = handle_error(
            e,
            {
                "analysis_id": analysis_id,
                "component": "api_text_analysis"
            },
            correlation_id
        )
        
        log_with_context(
            logger,
            logging.ERROR,
            "Error processing API text analysis",
            analysis_id=analysis_id,
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Analysis failed",
                "message": user_message,
                "analysis_id": analysis_id,
                "timestamp": datetime.now().isoformat()
            }
        )