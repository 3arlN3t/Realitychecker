"""
Direct API endpoints for job advertisement analysis.

This module provides API endpoints that directly use the OpenAI service
without going through the message handler, for simpler testing.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Form, Request, File, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_config
from app.models.data_models import AppConfig
from app.services.enhanced_ai_analysis import EnhancedAIAnalysisService
from app.services.pdf_processing import PDFProcessingService
from app.dependencies import get_app_config
from app.utils.logging import get_logger, get_correlation_id, log_with_context

logger = get_logger(__name__)

# Create router for direct API endpoints
router = APIRouter(prefix="/api/direct", tags=["direct"])


def get_openai_service(config: AppConfig = Depends(get_app_config)) -> EnhancedAIAnalysisService:
    """
    Get OpenAI service instance.
    
    Args:
        config: Application configuration
        
    Returns:
        EnhancedAIAnalysisService: OpenAI service instance
    """
    return EnhancedAIAnalysisService(config)


def get_pdf_service(config: AppConfig = Depends(get_app_config)) -> PDFProcessingService:
    """
    Get PDF processing service instance.
    
    Args:
        config: Application configuration
        
    Returns:
        PDFProcessingService: PDF processing service instance
    """
    return PDFProcessingService(config)


@router.get("/test")
async def direct_test_page(request: Request):
    """
    Serve the direct test page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered direct test page
    """
    try:
        from fastapi.templating import Jinja2Templates
        import os
        
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        templates = Jinja2Templates(directory=templates_dir)
        
        return templates.TemplateResponse(
            "direct_test.html",
            {"request": request, "title": "Direct API Test"}
        )
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "message": "Direct test page is not available",
                "error": str(e)
            }
        )


@router.post("/analyze")
async def analyze_text_direct(
    job_text: str = Form(...),
    openai_service: EnhancedAIAnalysisService = Depends(get_openai_service)
) -> Dict[str, Any]:
    """
    Analyze job advertisement text directly using OpenAI service.
    
    Args:
        job_text: Job advertisement text to analyze
        openai_service: OpenAI service instance
        
    Returns:
        Dict containing analysis results
        
    Raises:
        HTTPException: For validation or processing errors
    """
    correlation_id = get_correlation_id()
    
    log_with_context(
        logger,
        logging.INFO,
        "Received direct analysis request",
        text_length=len(job_text) if job_text else 0,
        correlation_id=correlation_id
    )
    
    try:
        # Validate input
        if not job_text or len(job_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Job advertisement text is too short. Please provide more details."
            )
        
        if len(job_text) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Text is too long. Please limit to 10,000 characters."
            )
        
        # Analyze the text
        log_with_context(
            logger,
            logging.INFO,
            "Starting direct OpenAI analysis",
            correlation_id=correlation_id
        )
        
        analysis_result = await openai_service.analyze_job_ad(job_text)
        
        # Return the results
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "result": {
                "trust_score": analysis_result.trust_score,
                "classification": analysis_result.classification_text,
                "reasoning": analysis_result.reasons
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        log_with_context(
            logger,
            logging.ERROR,
            "Error in direct analysis",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Analysis failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/analyze-pdf")
async def analyze_pdf_direct(
    pdf_file: UploadFile = File(...),
    openai_service: EnhancedAIAnalysisService = Depends(get_openai_service),
    pdf_service: PDFProcessingService = Depends(get_pdf_service),
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Analyze job advertisement PDF directly using PDF and OpenAI services.
    
    Args:
        pdf_file: Uploaded PDF file
        openai_service: OpenAI service instance
        pdf_service: PDF processing service instance
        config: Application configuration
        
    Returns:
        Dict containing analysis results
        
    Raises:
        HTTPException: For validation or processing errors
    """
    correlation_id = get_correlation_id()
    
    log_with_context(
        logger,
        logging.INFO,
        "Received direct PDF analysis request",
        uploaded_filename=pdf_file.filename,
        content_type=pdf_file.content_type,
        correlation_id=correlation_id
    )
    
    try:
        # Validate file type
        if not pdf_file.content_type or 'pdf' not in pdf_file.content_type.lower():
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported. Please upload a PDF file."
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
        
        # Validate PDF content is not empty
        if len(pdf_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="PDF file appears to be empty."
            )
        
        # Process PDF to extract text
        log_with_context(
            logger,
            logging.INFO,
            "Starting PDF text extraction",
            uploaded_filename=pdf_file.filename,
            file_size=len(pdf_content),
            correlation_id=correlation_id
        )
        
        text_content = await pdf_service.process_pdf_bytes(pdf_content, pdf_file.filename or "upload.pdf")
        
        # Analyze the extracted text
        log_with_context(
            logger,
            logging.INFO,
            "Starting direct OpenAI analysis for PDF content",
            text_length=len(text_content),
            correlation_id=correlation_id
        )
        
        analysis_result = await openai_service.analyze_job_ad(text_content)
        
        # Return the results
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "filename": pdf_file.filename,
            "text_length": len(text_content),
            "result": {
                "trust_score": analysis_result.trust_score,
                "classification": analysis_result.classification_text,
                "reasoning": analysis_result.reasons
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        log_with_context(
            logger,
            logging.ERROR,
            "Error in direct PDF analysis",
            uploaded_filename=pdf_file.filename,
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "PDF analysis failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )