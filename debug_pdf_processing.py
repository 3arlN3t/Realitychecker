#!/usr/bin/env python3
"""
Debug script to test PDF processing functionality.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.services.pdf_processing import PDFProcessingService
from app.config import get_config

async def test_pdf_processing():
    """Test PDF processing with a sample PDF URL."""
    print("🧪 Testing PDF Processing Service")
    print("=" * 50)
    
    try:
        # Initialize service
        config = get_config()
        pdf_service = PDFProcessingService(config)
        print("✅ PDF service initialized")
        
        # Test with a simple PDF URL (you can replace this with an actual URL)
        test_url = input("Enter a PDF URL to test (or press Enter to skip): ").strip()
        
        if not test_url:
            print("ℹ️  No URL provided, skipping download test")
            return
        
        print(f"🔽 Downloading PDF from: {test_url}")
        
        # Test download
        pdf_content = await pdf_service.download_pdf(test_url)
        print(f"✅ Downloaded {len(pdf_content)} bytes")
        
        # Test complete PDF processing workflow
        extracted_text = await pdf_service.process_pdf_url(test_url)
        print(f"✅ Extracted {len(extracted_text)} characters")
        print(f"📄 First 200 characters: {extracted_text[:200]}...")
        
        print("\n✅ PDF processing test completed successfully!")
        
    except Exception as e:
        print(f"❌ PDF processing test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pdf_processing())