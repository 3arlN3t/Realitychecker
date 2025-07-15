"""
PDF Processing Service for the Reality Checker WhatsApp bot.

This module handles downloading PDF files from URLs and extracting text content
for job ad analysis. Includes validation, error handling, and size limits.
"""

import asyncio
import logging
from typing import Optional
from io import BytesIO

import httpx
import pdfplumber
from pdfplumber.pdf import PDF

from app.models.data_models import AppConfig
from app.utils.logging import get_logger, get_correlation_id, log_with_context
from app.utils.security import SecurityValidator


logger = get_logger(__name__)


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PDFDownloadError(PDFProcessingError):
    """Exception raised when PDF download fails."""
    pass


class PDFExtractionError(PDFProcessingError):
    """Exception raised when PDF text extraction fails."""
    pass


class PDFValidationError(PDFProcessingError):
    """Exception raised when PDF validation fails."""
    pass


class PDFProcessingService:
    """
    Service for processing PDF files from WhatsApp media messages.
    
    Handles downloading PDFs from Twilio media URLs, extracting text content,
    and validating the extracted content for job ad analysis.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the PDF processing service.
        
        Args:
            config: Application configuration containing size limits and settings
        """
        self.config = config
        self.max_size_bytes = config.max_pdf_size_mb * 1024 * 1024
        self.timeout = httpx.Timeout(30.0)  # 30 second timeout
        
    async def download_pdf(self, media_url: str) -> bytes:
        """
        Download PDF content from a media URL.
        
        Args:
            media_url: URL to download the PDF from
            
        Returns:
            bytes: Raw PDF content
            
        Raises:
            PDFDownloadError: If download fails or file is too large
        """
        if not media_url:
            raise PDFDownloadError("Media URL is required")
        
        # Validate URL for security
        security_validator = SecurityValidator()
        is_valid, validation_error = security_validator.validate_url(media_url)
        if not is_valid:
            raise PDFDownloadError(f"Invalid media URL: {validation_error}")
        
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Downloading PDF from URL",
            url_preview=media_url[:50] + "..." if len(media_url) > 50 else media_url,
            max_size_mb=self.config.max_pdf_size_mb,
            correlation_id=correlation_id
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(media_url)
                response.raise_for_status()
                
                # Check content length header if available
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_size_bytes:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "PDF file too large (content-length header)",
                        content_length=int(content_length),
                        max_size_bytes=self.max_size_bytes,
                        correlation_id=correlation_id
                    )
                    raise PDFDownloadError(
                        f"PDF file too large: {content_length} bytes "
                        f"(max: {self.max_size_bytes} bytes)"
                    )
                
                pdf_content = response.content
                
                # Check actual content size
                if len(pdf_content) > self.max_size_bytes:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "PDF file too large (actual content)",
                        actual_size=len(pdf_content),
                        max_size_bytes=self.max_size_bytes,
                        correlation_id=correlation_id
                    )
                    raise PDFDownloadError(
                        f"PDF file too large: {len(pdf_content)} bytes "
                        f"(max: {self.max_size_bytes} bytes)"
                    )
                
                # Basic PDF header validation
                if not pdf_content.startswith(b'%PDF-'):
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Downloaded file is not a valid PDF",
                        file_header=pdf_content[:20].hex() if len(pdf_content) >= 20 else pdf_content.hex(),
                        correlation_id=correlation_id
                    )
                    raise PDFDownloadError("Downloaded file is not a valid PDF")
                
                log_with_context(
                    logger,
                    logging.INFO,
                    "Successfully downloaded PDF",
                    file_size=len(pdf_content),
                    correlation_id=correlation_id
                )
                return pdf_content
                
        except httpx.HTTPStatusError as e:
            log_with_context(
                logger,
                logging.ERROR,
                "HTTP error downloading PDF",
                status_code=e.response.status_code,
                error=str(e),
                correlation_id=correlation_id
            )
            raise PDFDownloadError(f"Failed to download PDF: HTTP {e.response.status_code}")
        except httpx.TimeoutException:
            log_with_context(
                logger,
                logging.ERROR,
                "Timeout downloading PDF",
                timeout_seconds=30.0,  # Default timeout value
                correlation_id=correlation_id
            )
            raise PDFDownloadError("PDF download timed out")
        except httpx.RequestError as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Network error downloading PDF",
                error=str(e),
                correlation_id=correlation_id
            )
            raise PDFDownloadError(f"Network error downloading PDF: {e}")
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error downloading PDF",
                error=str(e),
                correlation_id=correlation_id
            )
            raise PDFDownloadError(f"Unexpected error downloading PDF: {e}")
    
    async def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes.
        
        Args:
            pdf_content: Raw PDF content as bytes
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFExtractionError: If text extraction fails
        """
        if not pdf_content:
            raise PDFExtractionError("PDF content is required")
        
        correlation_id = get_correlation_id()
        
        log_with_context(
            logger,
            logging.INFO,
            "Extracting text from PDF",
            pdf_size=len(pdf_content),
            correlation_id=correlation_id
        )
        
        try:
            # Run PDF processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, self._extract_text_sync, pdf_content)
            
            log_with_context(
                logger,
                logging.INFO,
                "Successfully extracted text from PDF",
                text_length=len(text),
                correlation_id=correlation_id
            )
            return text
            
        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                "Error extracting text from PDF",
                error=str(e),
                pdf_size=len(pdf_content),
                correlation_id=correlation_id
            )
            raise PDFExtractionError(f"Failed to extract text from PDF: {e}")
    
    def _extract_text_sync(self, pdf_content: bytes) -> str:
        """
        Synchronous text extraction from PDF content.
        
        Args:
            pdf_content: Raw PDF content as bytes
            
        Returns:
            str: Extracted text content
        """
        pdf_buffer = BytesIO(pdf_content)
        text_parts = []
        
        with pdfplumber.open(pdf_buffer) as pdf:
            if not pdf.pages:
                raise PDFExtractionError("PDF contains no pages")
                
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text.strip())
                    logger.debug(f"Extracted text from page {page_num}: {len(page_text or '')} chars")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    continue
        
        full_text = '\n\n'.join(text_parts)
        
        if not full_text.strip():
            raise PDFExtractionError("No text content found in PDF")
            
        return full_text.strip()
    
    def validate_pdf_content(self, text: str) -> bool:
        """
        Validate that extracted PDF text contains sufficient content for analysis.
        
        Args:
            text: Extracted text content
            
        Returns:
            bool: True if content is valid for analysis
            
        Raises:
            PDFValidationError: If content validation fails
        """
        if not text or not text.strip():
            raise PDFValidationError("PDF text content is empty")
        
        # Check minimum length (at least 50 characters for meaningful job ad)
        min_length = 50
        if len(text.strip()) < min_length:
            raise PDFValidationError(
                f"PDF text too short for analysis: {len(text.strip())} chars "
                f"(minimum: {min_length} chars)"
            )
        
        # Check for job-related keywords (basic heuristic)
        job_keywords = [
            'job', 'position', 'role', 'career', 'employment', 'work',
            'salary', 'wage', 'company', 'employer', 'hiring', 'recruit',
            'experience', 'skills', 'qualifications', 'responsibilities'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in text_lower)
        
        if keyword_count < 2:
            logger.warning(f"PDF content may not be job-related (found {keyword_count} job keywords)")
            # Don't raise error, just log warning - let OpenAI decide if it's job-related
        
        logger.info(f"PDF content validation passed: {len(text)} chars, {keyword_count} job keywords")
        return True
    
    async def process_pdf_url(self, media_url: str) -> str:
        """
        Complete PDF processing workflow: download, extract, and validate.
        
        Args:
            media_url: URL to download the PDF from
            
        Returns:
            str: Validated text content ready for analysis
            
        Raises:
            PDFProcessingError: If any step of the processing fails
        """
        logger.info(f"Starting PDF processing for URL: {media_url[:50]}...")
        
        try:
            # Download PDF content
            pdf_content = await self.download_pdf(media_url)
            
            # Extract text from PDF
            text_content = await self.extract_text(pdf_content)
            
            # Validate extracted content
            self.validate_pdf_content(text_content)
            
            logger.info("PDF processing completed successfully")
            return text_content
            
        except PDFProcessingError:
            # Re-raise PDF processing errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in PDF processing: {e}")
            raise PDFProcessingError(f"PDF processing failed: {e}")