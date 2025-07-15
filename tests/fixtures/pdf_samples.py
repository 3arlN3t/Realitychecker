"""
Test fixtures for PDF samples and processing scenarios.

This module provides test data for PDF processing including sample PDF content,
mock PDF responses, and various PDF-related error scenarios.
"""

import base64
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.models.data_models import JobClassification


@dataclass
class PDFSample:
    """Sample PDF data for testing."""
    filename: str
    url: str
    content_type: str
    size_bytes: int
    extracted_text: str
    expected_classification: JobClassification
    description: str
    should_process_successfully: bool
    error_type: Optional[str] = None


class PDFFixtures:
    """Collection of PDF test fixtures."""
    
    # Valid PDF samples with job content
    VALID_PDF_SAMPLES = [
        PDFSample(
            filename="legitimate_software_job.pdf",
            url="https://api.twilio.com/media/legitimate_software_job.pdf",
            content_type="application/pdf",
            size_bytes=2048,
            extracted_text="""
            Senior Software Engineer Position
            TechCorp Solutions Inc.
            
            Job Description:
            We are seeking an experienced Senior Software Engineer to join our growing development team.
            
            Responsibilities:
            • Design and implement scalable web applications
            • Collaborate with product managers and designers
            • Mentor junior developers
            • Participate in code reviews and architecture decisions
            • Maintain and improve existing systems
            
            Requirements:
            • Bachelor's degree in Computer Science or related field
            • 5+ years of software development experience
            • Proficiency in Python, JavaScript, and SQL
            • Experience with cloud platforms (AWS, Azure, or GCP)
            • Strong problem-solving and communication skills
            
            Compensation:
            • Salary: $110,000 - $140,000 annually
            • Health, dental, and vision insurance
            • 401(k) with company matching
            • Flexible PTO policy
            • Remote work options available
            
            About TechCorp Solutions:
            Founded in 2015, TechCorp Solutions is a leading provider of enterprise software solutions.
            We serve over 500 clients worldwide and have offices in San Francisco, New York, and Austin.
            
            To Apply:
            Please send your resume and cover letter to careers@techcorp-solutions.com
            Visit our website: www.techcorp-solutions.com
            """,
            expected_classification=JobClassification.LEGIT,
            description="Legitimate software engineering job with detailed requirements and company info",
            should_process_successfully=True
        ),
        
        PDFSample(
            filename="marketing_coordinator_job.pdf",
            url="https://api.twilio.com/media/marketing_coordinator_job.pdf",
            content_type="application/pdf",
            size_bytes=1536,
            extracted_text="""
            Marketing Coordinator - ABC Marketing Agency
            
            Position Overview:
            ABC Marketing Agency is looking for a creative and organized Marketing Coordinator
            to support our client campaigns and internal marketing initiatives.
            
            Key Responsibilities:
            - Assist in developing marketing campaigns for clients
            - Manage social media accounts and content calendars
            - Coordinate with graphic designers and copywriters
            - Track campaign performance and prepare reports
            - Support event planning and execution
            
            Qualifications:
            - Bachelor's degree in Marketing, Communications, or related field
            - 1-3 years of marketing experience
            - Proficiency in Adobe Creative Suite and social media platforms
            - Strong written and verbal communication skills
            - Detail-oriented with excellent organizational abilities
            
            What We Offer:
            - Competitive salary: $45,000 - $55,000
            - Health and dental benefits
            - Professional development opportunities
            - Collaborative work environment
            - Downtown office location with parking
            
            Application Process:
            Submit your resume, portfolio, and a brief cover letter explaining
            why you're interested in this position to hr@abcmarketing.com
            
            ABC Marketing Agency
            123 Business District, Suite 400
            Marketing City, MC 12345
            Phone: (555) 123-4567
            """,
            expected_classification=JobClassification.LEGIT,
            description="Entry-level marketing position with clear requirements and contact info",
            should_process_successfully=True
        ),
        
        PDFSample(
            filename="suspicious_work_from_home.pdf",
            url="https://api.twilio.com/media/suspicious_work_from_home.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            extracted_text="""
            WORK FROM HOME OPPORTUNITY - EARN $5000/WEEK!
            
            Are you tired of your 9-5 job? Ready to be your own boss?
            
            We have the perfect opportunity for you!
            
            What You'll Do:
            - Simple data entry tasks (no experience needed!)
            - Process online orders from home
            - Customer service via email and chat
            - Flexible schedule - work when you want!
            
            Earning Potential:
            - $5000+ per week possible
            - Weekly payments via PayPal
            - Bonuses for top performers
            - No income limits!
            
            Getting Started:
            To secure your position and receive training materials:
            1. Send $149 startup fee via Western Union
            2. Complete our online training course
            3. Start earning immediately!
            
            Limited Time Offer:
            Only 25 positions available in your area!
            This offer expires in 48 hours!
            
            Contact Information:
            Email: opportunity2024@fastcash.biz
            Text "START" to 555-MONEY
            WhatsApp: +1-800-RICH-NOW
            
            Don't miss out on this life-changing opportunity!
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            description="Work from home scam with upfront fees and unrealistic income promises",
            should_process_successfully=True
        ),
        
        PDFSample(
            filename="advance_fee_scam.pdf",
            url="https://api.twilio.com/media/advance_fee_scam.pdf",
            content_type="application/pdf",
            size_bytes=2560,
            extracted_text="""
            URGENT: GOVERNMENT CONTRACT POSITION AVAILABLE
            
            CONGRATULATIONS! You have been pre-selected for a high-paying government contract position.
            
            Position Details:
            - Title: Federal Security Consultant
            - Salary: $150,000 per year
            - Location: Work from anywhere
            - Start Date: Immediate
            - Contract Duration: 5 years guaranteed
            
            Special Selection Process:
            You were chosen based on your background and qualifications.
            No interviews or applications required!
            
            IMMEDIATE ACTION REQUIRED:
            To secure this position, you must:
            1. Pay $2,500 security clearance processing fee
            2. Provide Social Security Number and bank details
            3. Send copy of driver's license and passport
            4. Complete background check authorization
            
            Payment Instructions:
            - Method: Bitcoin or Western Union only (for security)
            - Recipient: Federal Processing Center
            - Reference: GOV2024-SECURE
            - Amount: $2,500 USD
            
            Important Notes:
            - This is a classified government program
            - Do not discuss with anyone
            - Offer expires in 24 hours
            - Processing fee is fully refundable after 30 days
            
            After Payment:
            - Receive official government contract
            - Get security clearance certificate
            - Start work immediately
            - First month's salary paid in advance
            
            Contact Immediately:
            Email: gov-contracts@federal-jobs.biz
            Phone: 1-800-GOV-JOBS (available 24/7)
            
            This is a once-in-a-lifetime opportunity!
            Act now before it's too late!
            """,
            expected_classification=JobClassification.LIKELY_SCAM,
            description="Classic advance fee scam disguised as government job opportunity",
            should_process_successfully=True
        )
    ]
    
    # Invalid or problematic PDF samples
    INVALID_PDF_SAMPLES = [
        PDFSample(
            filename="corrupted_file.pdf",
            url="https://api.twilio.com/media/corrupted_file.pdf",
            content_type="application/pdf",
            size_bytes=512,
            extracted_text="",
            expected_classification=JobClassification.SUSPICIOUS,
            description="Corrupted PDF file that cannot be processed",
            should_process_successfully=False,
            error_type="extraction_error"
        ),
        
        PDFSample(
            filename="empty_pdf.pdf",
            url="https://api.twilio.com/media/empty_pdf.pdf",
            content_type="application/pdf",
            size_bytes=256,
            extracted_text="",
            expected_classification=JobClassification.SUSPICIOUS,
            description="PDF file with no extractable text content",
            should_process_successfully=False,
            error_type="empty_content"
        ),
        
        PDFSample(
            filename="oversized_file.pdf",
            url="https://api.twilio.com/media/oversized_file.pdf",
            content_type="application/pdf",
            size_bytes=15 * 1024 * 1024,  # 15MB
            extracted_text="This file is too large to process",
            expected_classification=JobClassification.SUSPICIOUS,
            description="PDF file that exceeds size limits",
            should_process_successfully=False,
            error_type="size_limit_exceeded"
        ),
        
        PDFSample(
            filename="password_protected.pdf",
            url="https://api.twilio.com/media/password_protected.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            extracted_text="",
            expected_classification=JobClassification.SUSPICIOUS,
            description="Password-protected PDF that cannot be opened",
            should_process_successfully=False,
            error_type="password_protected"
        ),
        
        PDFSample(
            filename="non_job_content.pdf",
            url="https://api.twilio.com/media/non_job_content.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            extracted_text="""
            Recipe for Chocolate Chip Cookies
            
            Ingredients:
            - 2 cups all-purpose flour
            - 1 cup butter, softened
            - 3/4 cup brown sugar
            - 1/2 cup white sugar
            - 2 eggs
            - 2 tsp vanilla extract
            - 1 tsp baking soda
            - 1 tsp salt
            - 2 cups chocolate chips
            
            Instructions:
            1. Preheat oven to 375°F
            2. Mix dry ingredients in a bowl
            3. Cream butter and sugars
            4. Add eggs and vanilla
            5. Combine wet and dry ingredients
            6. Fold in chocolate chips
            7. Drop spoonfuls on baking sheet
            8. Bake for 9-11 minutes
            
            Enjoy your delicious cookies!
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            description="PDF with non-job-related content (recipe)",
            should_process_successfully=False,
            error_type="invalid_content"
        )
    ]
    
    @classmethod
    def get_all_samples(cls) -> List[PDFSample]:
        """Get all PDF samples."""
        return cls.VALID_PDF_SAMPLES + cls.INVALID_PDF_SAMPLES
    
    @classmethod
    def get_valid_samples(cls) -> List[PDFSample]:
        """Get only valid PDF samples that should process successfully."""
        return cls.VALID_PDF_SAMPLES
    
    @classmethod
    def get_invalid_samples(cls) -> List[PDFSample]:
        """Get only invalid PDF samples that should fail processing."""
        return cls.INVALID_PDF_SAMPLES
    
    @classmethod
    def get_sample_by_filename(cls, filename: str) -> PDFSample:
        """Get a specific PDF sample by filename."""
        for sample in cls.get_all_samples():
            if sample.filename == filename:
                return sample
        raise ValueError(f"No PDF sample found with filename: {filename}")
    
    @classmethod
    def get_samples_by_classification(cls, classification: JobClassification) -> List[PDFSample]:
        """Get PDF samples filtered by expected classification."""
        return [sample for sample in cls.get_all_samples() 
                if sample.expected_classification == classification]


class MockPDFResponses:
    """Mock HTTP responses for PDF downloads."""
    
    @staticmethod
    def create_successful_response(pdf_sample: PDFSample) -> Dict[str, Any]:
        """Create a successful HTTP response for PDF download."""
        # Create fake PDF content (just for testing)
        fake_pdf_content = f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n{pdf_sample.extracted_text}\n%%EOF"
        
        return {
            "status_code": 200,
            "headers": {
                "content-type": pdf_sample.content_type,
                "content-length": str(pdf_sample.size_bytes)
            },
            "content": fake_pdf_content.encode('utf-8')
        }
    
    @staticmethod
    def create_not_found_response() -> Dict[str, Any]:
        """Create a 404 not found response."""
        return {
            "status_code": 404,
            "headers": {"content-type": "text/html"},
            "content": b"<html><body><h1>404 Not Found</h1></body></html>"
        }
    
    @staticmethod
    def create_forbidden_response() -> Dict[str, Any]:
        """Create a 403 forbidden response."""
        return {
            "status_code": 403,
            "headers": {"content-type": "text/html"},
            "content": b"<html><body><h1>403 Forbidden</h1></body></html>"
        }
    
    @staticmethod
    def create_too_large_response() -> Dict[str, Any]:
        """Create a response indicating file is too large."""
        return {
            "status_code": 200,
            "headers": {
                "content-type": "application/pdf",
                "content-length": str(20 * 1024 * 1024)  # 20MB
            },
            "content": b"%PDF-1.4 fake large content"
        }
    
    @staticmethod
    def create_invalid_content_type_response() -> Dict[str, Any]:
        """Create a response with invalid content type."""
        return {
            "status_code": 200,
            "headers": {
                "content-type": "text/html",
                "content-length": "1024"
            },
            "content": b"<html><body>This is not a PDF file</body></html>"
        }


class PDFExtractionMocks:
    """Mock PDF text extraction scenarios."""
    
    @staticmethod
    def create_successful_extraction_mock(extracted_text: str):
        """Create a mock for successful PDF text extraction."""
        from unittest.mock import Mock
        
        mock_page = Mock()
        mock_page.extract_text.return_value = extracted_text
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        return mock_pdf
    
    @staticmethod
    def create_multi_page_extraction_mock(page_texts: List[str]):
        """Create a mock for multi-page PDF text extraction."""
        from unittest.mock import Mock
        
        mock_pages = []
        for text in page_texts:
            mock_page = Mock()
            mock_page.extract_text.return_value = text
            mock_pages.append(mock_page)
        
        mock_pdf = Mock()
        mock_pdf.pages = mock_pages
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        return mock_pdf
    
    @staticmethod
    def create_empty_extraction_mock():
        """Create a mock for PDF with no extractable text."""
        from unittest.mock import Mock
        
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        return mock_pdf
    
    @staticmethod
    def create_extraction_error_mock():
        """Create a mock that raises an exception during extraction."""
        from unittest.mock import Mock
        
        mock_pdf = Mock()
        mock_pdf.__enter__ = Mock(side_effect=Exception("PDF extraction failed"))
        mock_pdf.__exit__ = Mock(return_value=None)
        
        return mock_pdf
    
    @staticmethod
    def create_no_pages_mock():
        """Create a mock for PDF with no pages."""
        from unittest.mock import Mock
        
        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        return mock_pdf


class PDFTestScenarios:
    """Complete test scenarios combining PDF samples with expected behaviors."""
    
    SUCCESSFUL_PROCESSING_SCENARIOS = [
        {
            "name": "legitimate_job_pdf",
            "pdf_sample": PDFFixtures.VALID_PDF_SAMPLES[0],
            "http_response": MockPDFResponses.create_successful_response(PDFFixtures.VALID_PDF_SAMPLES[0]),
            "extraction_mock": PDFExtractionMocks.create_successful_extraction_mock(PDFFixtures.VALID_PDF_SAMPLES[0].extracted_text),
            "expected_result": PDFFixtures.VALID_PDF_SAMPLES[0].extracted_text
        },
        {
            "name": "marketing_job_pdf",
            "pdf_sample": PDFFixtures.VALID_PDF_SAMPLES[1],
            "http_response": MockPDFResponses.create_successful_response(PDFFixtures.VALID_PDF_SAMPLES[1]),
            "extraction_mock": PDFExtractionMocks.create_successful_extraction_mock(PDFFixtures.VALID_PDF_SAMPLES[1].extracted_text),
            "expected_result": PDFFixtures.VALID_PDF_SAMPLES[1].extracted_text
        }
    ]
    
    ERROR_SCENARIOS = [
        {
            "name": "pdf_not_found",
            "pdf_sample": PDFFixtures.INVALID_PDF_SAMPLES[0],
            "http_response": MockPDFResponses.create_not_found_response(),
            "extraction_mock": None,
            "expected_error": "Failed to download PDF"
        },
        {
            "name": "pdf_too_large",
            "pdf_sample": PDFFixtures.INVALID_PDF_SAMPLES[2],
            "http_response": MockPDFResponses.create_too_large_response(),
            "extraction_mock": None,
            "expected_error": "PDF file is too large"
        },
        {
            "name": "extraction_failure",
            "pdf_sample": PDFFixtures.INVALID_PDF_SAMPLES[0],
            "http_response": MockPDFResponses.create_successful_response(PDFFixtures.INVALID_PDF_SAMPLES[0]),
            "extraction_mock": PDFExtractionMocks.create_extraction_error_mock(),
            "expected_error": "Failed to extract text from PDF"
        },
        {
            "name": "empty_content",
            "pdf_sample": PDFFixtures.INVALID_PDF_SAMPLES[1],
            "http_response": MockPDFResponses.create_successful_response(PDFFixtures.INVALID_PDF_SAMPLES[1]),
            "extraction_mock": PDFExtractionMocks.create_empty_extraction_mock(),
            "expected_error": "PDF contains no readable text"
        }
    ]
    
    @classmethod
    def get_all_scenarios(cls):
        """Get all test scenarios."""
        return cls.SUCCESSFUL_PROCESSING_SCENARIOS + cls.ERROR_SCENARIOS
    
    @classmethod
    def get_successful_scenarios(cls):
        """Get only successful processing scenarios."""
        return cls.SUCCESSFUL_PROCESSING_SCENARIOS
    
    @classmethod
    def get_error_scenarios(cls):
        """Get only error scenarios."""
        return cls.ERROR_SCENARIOS