"""
Direct API endpoints for job advertisement analysis.

This module provides API endpoints that directly use the OpenAI service
without going through the message handler, for simpler testing.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Form, Request
from fastapi.responses import JSONResponse

from app.config import get_config
from app.models.data_models import AppConfig
from app.services.enhanced_ai_analysis import EnhancedAIAnalysisService
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