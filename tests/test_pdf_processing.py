"""
Unit tests for PDF processing service.

Tests cover PDF download, text extraction, validation, and error handling
with various edge cases and mock scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

import httpx
import pdfplumber

from app.services.pdf_processing import (
    PDFProcessingService,
    PDFProcessingError,
    PDFDownloadError,
    PDFExtractionError,
    PDFValidationError
)
from app.models.data_models import AppConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AppConfig(
        openai_api_key="test-key",
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_phone_number="+1234567890",
        max_pdf_size_mb=5,  # 5MB for testing
        openai_model="gpt-4",
        log_level="INFO"
    )


@pytest.fixture
def pdf_service(mock_config):
    """Create PDF processing service instance for testing."""
    return PDFProcessingService(mock_config)


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    # This is a minimal PDF header - in real tests you'd use actual PDF bytes
    return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'


@pytest.fixture
def sample_job_text():
    """Create sample job ad text for testing."""
    return """
    Software Engineer Position
    
    We are hiring a Software Engineer to join our team.
    
    Responsibilities:
    - Develop web applications
    - Write clean code
    - Collaborate with team members
    
    Requirements:
    - 3+ years experience
    - Python and JavaScript skills
    - Bachelor's degree preferred
    
    Salary: $80,000 - $120,000
    Company: Tech Solutions Inc.
    """


class TestPDFProcessingService:
    """Test cases for PDFProcessingService class."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        service = PDFProcessingService(mock_config)
        assert service.config == mock_config
        assert service.max_size_bytes == 5 * 1024 * 1024  # 5MB in bytes
        assert service.timeout.read == 30.0
    
    @pytest.mark.asyncio
    async def test_download_pdf_success(self, pdf_service, sample_pdf_content):
        """Test successful PDF download."""
        mock_response = Mock()
        mock_response.content = sample_pdf_content
        mock_response.headers = {'content-length': str(len(sample_pdf_content))}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await pdf_service.download_pdf("https://example.com/test.pdf")
            
            assert result == sample_pdf_content
            mock_response.raise_for_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_pdf_empty_url(self, pdf_service):
        """Test download with empty URL."""
        with pytest.raises(PDFDownloadError, match="Media URL is required"):
            await pdf_service.download_pdf("")
    
    @pytest.mark.asyncio
    async def test_download_pdf_too_large_header(self, pdf_service):
        """Test download failure when content-length header indicates file too large."""
        mock_response = Mock()
        mock_response.headers = {'content-length': str(10 * 1024 * 1024)}  # 10MB
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(PDFDownloadError, match="PDF file too large"):
                await pdf_service.download_pdf("https://example.com/large.pdf")
    
    @pytest.mark.asyncio
    async def test_download_pdf_too_large_content(self, pdf_service):
        """Test download failure when actual content is too large."""
        large_content = b'%PDF-1.4' + b'x' * (6 * 1024 * 1024)  # 6MB+ content
        mock_response = Mock()
        mock_response.content = large_content
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(PDFDownloadError, match="PDF file too large"):
                await pdf_service.download_pdf("https://example.com/large.pdf")
    
    @pytest.mark.asyncio
    async def test_download_pdf_invalid_format(self, pdf_service):
        """Test download failure when file is not a valid PDF."""
        invalid_content = b'This is not a PDF file'
        mock_response = Mock()
        mock_response.content = invalid_content
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(PDFDownloadError, match="not a valid PDF"):
                await pdf_service.download_pdf("https://example.com/invalid.pdf")
    
    @pytest.mark.asyncio
    async def test_download_pdf_http_error(self, pdf_service):
        """Test download failure with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
            )
            
            with pytest.raises(PDFDownloadError, match="HTTP 404"):
                await pdf_service.download_pdf("https://example.com/notfound.pdf")
    
    @pytest.mark.asyncio
    async def test_download_pdf_timeout(self, pdf_service):
        """Test download failure with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            with pytest.raises(PDFDownloadError, match="timed out"):
                await pdf_service.download_pdf("https://example.com/slow.pdf")
    
    @pytest.mark.asyncio
    async def test_download_pdf_network_error(self, pdf_service):
        """Test download failure with network error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            
            with pytest.raises(PDFDownloadError, match="Network error"):
                await pdf_service.download_pdf("https://example.com/unreachable.pdf")
    
    @pytest.mark.asyncio
    async def test_extract_text_success(self, pdf_service, sample_pdf_content, sample_job_text):
        """Test successful text extraction from PDF."""
        with patch.object(pdf_service, '_extract_text_sync', return_value=sample_job_text):
            result = await pdf_service.extract_text(sample_pdf_content)
            assert result == sample_job_text
    
    @pytest.mark.asyncio
    async def test_extract_text_empty_content(self, pdf_service):
        """Test text extraction with empty PDF content."""
        with pytest.raises(PDFExtractionError, match="PDF content is required"):
            await pdf_service.extract_text(b"")
    
    @pytest.mark.asyncio
    async def test_extract_text_extraction_error(self, pdf_service, sample_pdf_content):
        """Test text extraction failure."""
        with patch.object(pdf_service, '_extract_text_sync', side_effect=Exception("Extraction failed")):
            with pytest.raises(PDFExtractionError, match="Failed to extract text"):
                await pdf_service.extract_text(sample_pdf_content)
    
    def test_extract_text_sync_success(self, pdf_service, sample_job_text):
        """Test synchronous text extraction success."""
        mock_page = Mock()
        mock_page.extract_text.return_value = sample_job_text
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            result = pdf_service._extract_text_sync(b'%PDF-test')
            assert result == sample_job_text.strip()
    
    def test_extract_text_sync_no_pages(self, pdf_service):
        """Test synchronous text extraction with no pages."""
        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            with pytest.raises(PDFExtractionError, match="PDF contains no pages"):
                pdf_service._extract_text_sync(b'%PDF-test')
    
    def test_extract_text_sync_no_text(self, pdf_service):
        """Test synchronous text extraction with no extractable text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            with pytest.raises(PDFExtractionError, match="No text content found"):
                pdf_service._extract_text_sync(b'%PDF-test')
    
    def test_extract_text_sync_multiple_pages(self, pdf_service):
        """Test synchronous text extraction with multiple pages."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            result = pdf_service._extract_text_sync(b'%PDF-test')
            assert result == "Page 1 content\n\nPage 2 content"
    
    def test_extract_text_sync_page_error(self, pdf_service):
        """Test synchronous text extraction with page extraction error."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.side_effect = Exception("Page error")
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Page 3 content"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            result = pdf_service._extract_text_sync(b'%PDF-test')
            assert result == "Page 1 content\n\nPage 3 content"
    
    def test_validate_pdf_content_success(self, pdf_service, sample_job_text):
        """Test successful PDF content validation."""
        result = pdf_service.validate_pdf_content(sample_job_text)
        assert result is True
    
    def test_validate_pdf_content_empty(self, pdf_service):
        """Test PDF content validation with empty text."""
        with pytest.raises(PDFValidationError, match="PDF text content is empty"):
            pdf_service.validate_pdf_content("")
        
        with pytest.raises(PDFValidationError, match="PDF text content is empty"):
            pdf_service.validate_pdf_content("   ")
    
    def test_validate_pdf_content_too_short(self, pdf_service):
        """Test PDF content validation with text too short."""
        short_text = "Short text"
        with pytest.raises(PDFValidationError, match="PDF text too short"):
            pdf_service.validate_pdf_content(short_text)
    
    def test_validate_pdf_content_no_job_keywords(self, pdf_service):
        """Test PDF content validation with no job-related keywords."""
        non_job_text = "This is a long text about cooking recipes and food preparation. " * 3
        # Should not raise error, just log warning
        result = pdf_service.validate_pdf_content(non_job_text)
        assert result is True
    
    def test_validate_pdf_content_minimal_job_keywords(self, pdf_service):
        """Test PDF content validation with minimal job keywords."""
        minimal_job_text = "Looking for a job opportunity in software development with good salary prospects."
        result = pdf_service.validate_pdf_content(minimal_job_text)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_process_pdf_url_success(self, pdf_service, sample_pdf_content, sample_job_text):
        """Test complete PDF processing workflow success."""
        with patch.object(pdf_service, 'download_pdf', return_value=sample_pdf_content) as mock_download, \
             patch.object(pdf_service, 'extract_text', return_value=sample_job_text) as mock_extract, \
             patch.object(pdf_service, 'validate_pdf_content', return_value=True) as mock_validate:
            
            result = await pdf_service.process_pdf_url("https://example.com/job.pdf")
            
            assert result == sample_job_text
            mock_download.assert_called_once_with("https://example.com/job.pdf")
            mock_extract.assert_called_once_with(sample_pdf_content)
            mock_validate.assert_called_once_with(sample_job_text)
    
    @pytest.mark.asyncio
    async def test_process_pdf_url_download_error(self, pdf_service):
        """Test complete PDF processing workflow with download error."""
        with patch.object(pdf_service, 'download_pdf', side_effect=PDFDownloadError("Download failed")):
            with pytest.raises(PDFDownloadError, match="Download failed"):
                await pdf_service.process_pdf_url("https://example.com/job.pdf")
    
    @pytest.mark.asyncio
    async def test_process_pdf_url_extraction_error(self, pdf_service, sample_pdf_content):
        """Test complete PDF processing workflow with extraction error."""
        with patch.object(pdf_service, 'download_pdf', return_value=sample_pdf_content), \
             patch.object(pdf_service, 'extract_text', side_effect=PDFExtractionError("Extraction failed")):
            
            with pytest.raises(PDFExtractionError, match="Extraction failed"):
                await pdf_service.process_pdf_url("https://example.com/job.pdf")
    
    @pytest.mark.asyncio
    async def test_process_pdf_url_validation_error(self, pdf_service, sample_pdf_content, sample_job_text):
        """Test complete PDF processing workflow with validation error."""
        with patch.object(pdf_service, 'download_pdf', return_value=sample_pdf_content), \
             patch.object(pdf_service, 'extract_text', return_value=sample_job_text), \
             patch.object(pdf_service, 'validate_pdf_content', side_effect=PDFValidationError("Validation failed")):
            
            with pytest.raises(PDFValidationError, match="Validation failed"):
                await pdf_service.process_pdf_url("https://example.com/job.pdf")
    
    @pytest.mark.asyncio
    async def test_process_pdf_url_unexpected_error(self, pdf_service):
        """Test complete PDF processing workflow with unexpected error."""
        with patch.object(pdf_service, 'download_pdf', side_effect=Exception("Unexpected error")):
            with pytest.raises(PDFProcessingError, match="PDF processing failed"):
                await pdf_service.process_pdf_url("https://example.com/job.pdf")


class TestPDFProcessingExceptions:
    """Test cases for PDF processing exception classes."""
    
    def test_pdf_processing_error(self):
        """Test base PDFProcessingError exception."""
        error = PDFProcessingError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
    
    def test_pdf_download_error(self):
        """Test PDFDownloadError exception."""
        error = PDFDownloadError("Download error")
        assert str(error) == "Download error"
        assert isinstance(error, PDFProcessingError)
    
    def test_pdf_extraction_error(self):
        """Test PDFExtractionError exception."""
        error = PDFExtractionError("Extraction error")
        assert str(error) == "Extraction error"
        assert isinstance(error, PDFProcessingError)
    
    def test_pdf_validation_error(self):
        """Test PDFValidationError exception."""
        error = PDFValidationError("Validation error")
        assert str(error) == "Validation error"
        assert isinstance(error, PDFProcessingError)