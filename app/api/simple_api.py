"""
Simple API endpoints for testing.

This module provides simple API endpoints that don't require authentication
or complex processing, just to test if the basic API functionality is working.
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime

router = APIRouter(prefix="/api/simple", tags=["simple"])


@router.get("/hello")
async def hello_world():
    """
    Simple hello world endpoint.
    
    Returns:
        Dict: Simple greeting message
    """
    return {
        "message": "Hello, world!",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }


@router.get("/test")
async def simple_test_page(request):
    """
    Serve the simple test page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered simple test page
    """
    try:
        from fastapi.templating import Jinja2Templates
        import os
        
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        templates = Jinja2Templates(directory=templates_dir)
        
        return templates.TemplateResponse(
            "simple_test.html",
            {"request": request, "title": "Simple API Test"}
        )
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "message": "Simple test page is not available",
                "error": str(e)
            }
        )


@router.get("/echo/{text}")
async def echo(text: str):
    """
    Echo the provided text.
    
    Args:
        text: Text to echo
        
    Returns:
        Dict: Echoed text
    """
    return {
        "echo": text,
        "timestamp": datetime.now().isoformat(),
        "length": len(text)
    }