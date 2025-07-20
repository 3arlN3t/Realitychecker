#!/usr/bin/env python3
"""
Debug script to test PDF download functionality and identify the issue.
"""

import asyncio
import logging
from app.services.pdf_processing import PDFProcessingService
from app.config import get_config
from app.utils.logging import setup_logging

# Setup logging
setup_logging("DEBUG")
logger = logging.getLogger(__name__)

async def test_pdf_download():
    """Test PDF download with various URLs to identify the issue."""
    
    print("🧪 Testing PDF Download Functionality...")
    
    # Initialize PDF service
    config = get_config()
    pdf_service = PDFProcessingService(config)
    
    # Test URLs - mix of working and potentially problematic ones
    test_urls = [
        {
            "name": "Simple test PDF",
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        },
        {
            "name": "Another test PDF",
            "url": "https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf"
        },
        {
            "name": "Mozilla test PDF",
            "url": "https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf"
        }
    ]
    
    for test_case in test_urls:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Test download
            print("   🔄 Downloading PDF...")
            pdf_content = await pdf_service.download_pdf(test_case['url'])
            print(f"   ✅ Download successful: {len(pdf_content)} bytes")
            
            # Test text extraction
            print("   🔄 Extracting text...")
            text = await pdf_service.extract_text(pdf_content)
            print(f"   ✅ Text extraction successful: {len(text)} characters")
            print(f"   📄 Text preview: {text[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            logger.exception(f"Error processing {test_case['name']}")
    
    print("\n" + "=" * 50)
    print("🔍 Testing complete. Check the output above for specific errors.")

if __name__ == "__main__":
    asyncio.run(test_pdf_download())