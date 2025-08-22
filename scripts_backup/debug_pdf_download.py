#!/usr/bin/env python3
"""
Debug script to test PDF download functionality and see what errors are occurring.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import get_config
from app.services.pdf_processing import PDFProcessingService, PDFDownloadError, PDFExtractionError, PDFValidationError
from app.utils.error_handling import handle_error
from app.utils.logging import get_logger

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

async def test_pdf_download():
    """Test PDF download with a sample Twilio media URL format."""
    
    print("🔍 Testing PDF Download Functionality")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test with a sample URL (this won't work but will show us the error)
    test_url = "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
    
    print(f"Testing with URL: {test_url}")
    print()
    
    try:
        # Try to download
        print("📥 Attempting PDF download...")
        pdf_content = await pdf_service.download_pdf(test_url)
        print(f"✅ Download successful! Size: {len(pdf_content)} bytes")
        
    except PDFDownloadError as e:
        print(f"❌ PDFDownloadError: {e}")
        
        # Test error handling
        print("\n🔧 Testing error handling...")
        user_message, error_info = handle_error(e)
        print(f"User message: {user_message}")
        print(f"Error category: {error_info.category}")
        print(f"Error severity: {error_info.severity}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        
        # Test error handling for unexpected errors
        print("\n🔧 Testing error handling for unexpected error...")
        user_message, error_info = handle_error(e)
        print(f"User message: {user_message}")
        print(f"Error category: {error_info.category}")
        print(f"Error severity: {error_info.severity}")

async def test_pdf_processing_with_real_file():
    """Test PDF processing with the test file we have."""
    
    print("\n🔍 Testing PDF Processing with Local File")
    print("=" * 50)
    
    # Check if we have a test PDF file
    test_files = ["test_job_posting.pdf", "test_scam_job.pdf"]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📄 Found test file: {test_file}")
            
            # Read the file
            with open(test_file, 'rb') as f:
                pdf_content = f.read()
            
            print(f"File size: {len(pdf_content)} bytes")
            
            # Test extraction
            config = get_config()
            pdf_service = PDFProcessingService(config)
            
            try:
                print("📝 Extracting text...")
                text = await pdf_service.extract_text(pdf_content)
                print(f"✅ Text extracted! Length: {len(text)} characters")
                print(f"First 200 chars: {text[:200]}...")
                
                # Test validation
                print("\n✅ Validating content...")
                is_valid = pdf_service.validate_pdf_content(text)
                print(f"Content valid: {is_valid}")
                
            except (PDFExtractionError, PDFValidationError) as e:
                print(f"❌ PDF processing error: {e}")
                
                # Test error handling
                user_message, error_info = handle_error(e)
                print(f"User message: {user_message}")
                
            except Exception as e:
                print(f"❌ Unexpected error: {type(e).__name__}: {e}")
                user_message, error_info = handle_error(e)
                print(f"User message: {user_message}")
            
            break
    else:
        print("❌ No test PDF files found")

if __name__ == "__main__":
    asyncio.run(test_pdf_download())
    asyncio.run(test_pdf_processing_with_real_file())