"""
Web upload endpoint for job advertisement analysis.

This module provides endpoints for web-based uploads of job advertisements
for analysis, supporting both text input and PDF file uploads.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.config import get_config
from app.models.data_models import AppConfig, MessageType, AnalysisResult
from app.services.message_handler import MessageHandlerService
from app.dependencies import get_message_handler_service, get_app_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.error_handling import handle_error, ErrorCategory
from app.utils.security import SecurityValidator

logger = get_logger(__name__)

# Create router for web upload endpoints
router = APIRouter(prefix="/web", tags=["web"])

# Initialize templates
import os
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir, exist_ok=True)
    logger.warning(f"Created templates directory at {templates_dir}")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/")
async def web_upload_form(request: Request):
    """
    Render the web upload form for job advertisement analysis.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered HTML template for the upload form
    """
    try:
        return templates.TemplateResponse(
            "upload_form.html",
            {"request": request, "title": "Reality Checker - Job Ad Analysis"}
        )
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return JSONResponse(
            content={
                "message": "Web interface is not available. Templates directory may be missing.",
                "error": str(e)
            }
        )


@router.get("/api-status")
async def api_status():
    """
    Simple API status endpoint that doesn't require templates.
    
    Returns:
        JSONResponse: API status information
    """
    return {
        "status": "online",
        "message": "Reality Checker API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/simple")
async def simple_page(request: Request):
    """
    Simple test page to verify templates are working.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered simple HTML template
    """
    try:
        return templates.TemplateResponse(
            "simple.html",
            {"request": request, "title": "Simple Test Page"}
        )
    except Exception as e:
        logger.error(f"Error rendering simple template: {e}")
        return JSONResponse(
            content={
                "message": "Simple template rendering failed",
                "error": str(e)
            }
        )


@router.get("/index", include_in_schema=False)
@router.get("/home", include_in_schema=False)
async def home_page(request: Request):
    """
    Render the home page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered HTML template for the home page
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Reality Checker - Job Scam Detection"}
    )


@router.post("/analyze/text")
async def analyze_text(
    request: Request,
    background_tasks: BackgroundTasks,
    job_text: str = Form(...),
    message_handler: MessageHandlerService = Depends(get_message_handler_service),
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Analyze job advertisement text submitted via web form.
    
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
        "Received web text analysis request",
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
            'user_id': f"web-{request.client.host}",  # Anonymous user ID based on IP
            'source': 'web',
            'analysis_id': analysis_id,
            'correlation_id': correlation_id
        }
        
        # Process the message through the message handler service
        log_with_context(
            logger,
            logging.INFO,
            "Processing web text through MessageHandlerService",
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
                "component": "web_text_analysis"
            },
            correlation_id
        )
        
        log_with_context(
            logger,
            logging.ERROR,
            "Error processing web text analysis",
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


@router.post("/analyze/pdf")
async def analyze_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    message_handler: MessageHandlerService = Depends(get_message_handler_service),
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Analyze job advertisement PDF submitted via web form.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        pdf_file: Uploaded PDF file
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
        "Received web PDF analysis request",
        analysis_id=analysis_id,
        filename=pdf_file.filename,
        content_type=pdf_file.content_type,
        correlation_id=correlation_id
    )
    
    try:
        # Validate file type
        if not pdf_file.content_type or 'pdf' not in pdf_file.content_type.lower():
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported."
            )
        
        # Read file content
        pdf_content = await pdf_file.read()
        
        # Check file size
        max_size_bytes = config.max_pdf_size_mb * 1024 * 1024
        if len(pdf_content) > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"PDF file is too large. Maximum size is {config.max_pdf_size_mb}MB."
            )
        
        # Create message data for processing
        message_data = {
            'message_type': MessageType.PDF,
            'content': pdf_content,
            'user_id': f"web-{request.client.host}",  # Anonymous user ID based on IP
            'source': 'web',
            'analysis_id': analysis_id,
            'correlation_id': correlation_id,
            'filename': pdf_file.filename
        }
        
        # Process the message through the message handler service
        log_with_context(
            logger,
            logging.INFO,
            "Processing web PDF through MessageHandlerService",
            analysis_id=analysis_id,
            filename=pdf_file.filename,
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
                "filename": pdf_file.filename if pdf_file else "unknown",
                "component": "web_pdf_analysis"
            },
            correlation_id
        )
        
        log_with_context(
            logger,
            logging.ERROR,
            "Error processing web PDF analysis",
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