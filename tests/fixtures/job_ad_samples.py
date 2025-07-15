"""
Test fixtures for various job advertisement scenarios.

This module provides comprehensive test data for different types of job postings
including legitimate jobs, suspicious postings, and known scams.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from app.models.data_models import JobClassification


@dataclass
class JobAdSample:
    """Sample job advertisement for testing."""
    title: str
    content: str
    expected_classification: JobClassification
    expected_trust_score_range: tuple  # (min, max)
    description: str
    category: str


class JobAdFixtures:
    """Collection of job advertisement test fixtures."""
    
    # Legitimate Job Postings
    LEGITIMATE_JOBS = [
        JobAdSample(
            title="Software Engineer - Google",
            content="""
            Software Engineer - Google Inc.
            
            We are seeking a talented Software Engineer to join our team in Mountain View, CA.
            
            Responsibilities:
            - Design and develop scalable software solutions
            - Collaborate with cross-functional teams
            - Write clean, maintainable code
            - Participate in code reviews and technical discussions
            
            Requirements:
            - Bachelor's degree in Computer Science or related field
            - 3+ years of experience in software development
            - Proficiency in Python, Java, or C++
            - Experience with distributed systems
            - Strong problem-solving skills
            
            Salary: $120,000 - $180,000 per year
            Benefits: Health insurance, 401k, stock options, flexible PTO
            
            Contact: careers@google.com
            Apply through our official careers page
            """,
            expected_classification=JobClassification.LEGIT,
            expected_trust_score_range=(80, 100),
            description="Legitimate tech job with detailed requirements and realistic compensation",
            category="technology"
        ),
        
        JobAdSample(
            title="Marketing Manager - Established Company",
            content="""
            Marketing Manager Position - ABC Marketing Solutions
            
            ABC Marketing Solutions, established in 2010, is looking for an experienced Marketing Manager.
            
            About Us:
            - 50+ employees across 3 offices
            - Clients include Fortune 500 companies
            - Award-winning marketing campaigns
            
            Role Details:
            - Develop and execute marketing strategies
            - Manage social media campaigns
            - Analyze market trends and competitor activities
            - Lead a team of 5 marketing specialists
            
            Requirements:
            - Bachelor's degree in Marketing or Business
            - 5+ years of marketing experience
            - Experience with digital marketing tools
            - Strong analytical and communication skills
            
            Compensation:
            - Salary: $70,000 - $90,000 annually
            - Health and dental insurance
            - 3 weeks paid vacation
            - Professional development budget
            
            To apply, send resume to hr@abcmarketing.com
            Visit our website: www.abcmarketing.com
            """,
            expected_classification=JobClassification.LEGIT,
            expected_trust_score_range=(75, 95),
            description="Professional marketing role with company background and clear requirements",
            category="marketing"
        ),
        
        JobAdSample(
            title="Registered Nurse - Hospital",
            content="""
            Registered Nurse - St. Mary's Hospital
            
            St. Mary's Hospital is seeking a dedicated Registered Nurse for our ICU department.
            
            Position: Full-time, Day Shift (7am-7pm)
            Department: Intensive Care Unit
            
            Responsibilities:
            - Provide direct patient care in ICU setting
            - Monitor patient vital signs and conditions
            - Administer medications as prescribed
            - Collaborate with physicians and healthcare team
            - Maintain accurate patient records
            
            Requirements:
            - Current RN license in state
            - BSN preferred, ADN acceptable
            - 2+ years ICU experience preferred
            - BLS and ACLS certification required
            - Strong critical thinking skills
            
            Benefits:
            - Competitive salary: $65,000 - $85,000
            - Comprehensive health benefits
            - Retirement plan with matching
            - Tuition reimbursement
            - Shift differentials
            
            Apply online at stmarys-hospital.org/careers
            Contact: nursing-recruitment@stmarys.org
            """,
            expected_classification=JobClassification.LEGIT,
            expected_trust_score_range=(85, 100),
            description="Healthcare position with specific licensing requirements and professional details",
            category="healthcare"
        )
    ]
    
    # Suspicious Job Postings
    SUSPICIOUS_JOBS = [
        JobAdSample(
            title="Work From Home - High Pay",
            content="""
            WORK FROM HOME OPPORTUNITY - EARN BIG!
            
            Make $5000 per week working from home!
            No experience needed! Perfect for stay-at-home parents!
            
            What you'll do:
            - Simple data entry tasks
            - Process online orders
            - Customer service via email
            
            Requirements:
            - Must have computer and internet
            - Available 20+ hours per week
            - Motivated to earn extra income
            
            Getting Started:
            - Send $99 for training materials and software
            - Complete our online training course
            - Start earning immediately!
            
            This is a limited time offer! Only 50 positions available!
            
            Contact: opportunity123@gmail.com
            Text "START" to 555-MONEY for instant info
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            expected_trust_score_range=(30, 60),
            description="Work from home scam with upfront payment request and unrealistic income promises",
            category="work_from_home_scam"
        ),
        
        JobAdSample(
            title="Easy Money Online Job",
            content="""
            MAKE MONEY ONLINE - NO SKILLS REQUIRED!
            
            Earn $200-$500 per day from your computer!
            
            Job Description:
            - Click on ads and get paid
            - Share links on social media
            - Complete simple surveys
            - Refer friends for bonus money
            
            Why Choose Us:
            - Flexible schedule - work anytime
            - No boss or supervision
            - Get paid weekly via PayPal
            - Bonus for first 100 applicants
            
            To Get Started:
            - Pay $49 activation fee
            - Download our exclusive software
            - Watch training videos
            - Start earning today!
            
            Warning: This offer expires in 48 hours!
            
            Email: quickcash@fastmail.com
            WhatsApp: +1-800-GET-RICH
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            expected_trust_score_range=(20, 50),
            description="Online money-making scheme with activation fees and unrealistic promises",
            category="online_scam"
        ),
        
        JobAdSample(
            title="Mystery Shopper Job",
            content="""
            MYSTERY SHOPPER NEEDED - IMMEDIATE START
            
            Earn $300-$500 per assignment as a Mystery Shopper!
            
            Your Tasks:
            - Visit stores and evaluate service
            - Make purchases with provided funds
            - Complete detailed reports
            - Test money transfer services
            
            Assignment Details:
            - 2-3 assignments per week
            - Each assignment takes 2-4 hours
            - Reimbursement for all purchases
            - Keep products as bonus
            
            First Assignment:
            - Go to Walmart or Target
            - Purchase $500 gift cards
            - Test Western Union money transfer
            - Send funds to verify system
            - Keep $100 as payment
            
            Apply now! Limited positions in your area.
            
            Contact: mysteryshopper2024@outlook.com
            Include your full name and phone number
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            expected_trust_score_range=(25, 55),
            description="Mystery shopper scam involving money transfers and gift card purchases",
            category="mystery_shopper_scam"
        )
    ]
    
    # Likely Scam Job Postings
    SCAM_JOBS = [
        JobAdSample(
            title="Urgent - Send Money Now",
            content="""
            CONGRATULATIONS! YOU'VE BEEN SELECTED!
            
            You have been chosen for a $10,000/month data entry position!
            
            URGENT: This offer expires in 24 hours!
            
            Job Details:
            - Work from anywhere in the world
            - No experience or skills required
            - Guaranteed $10,000 monthly income
            - Start immediately after payment
            
            IMMEDIATE ACTION REQUIRED:
            - Send $500 processing fee NOW
            - Wire transfer to secure your position
            - Provide SSN and bank account details
            - Send copy of driver's license
            
            Payment Instructions:
            - Western Union to: John Smith
            - Location: Lagos, Nigeria
            - Reference: JOB2024
            - Amount: $500 USD
            
            After payment, you will receive:
            - Employment contract
            - Training materials
            - First month's salary advance
            
            DON'T MISS THIS OPPORTUNITY!
            
            Contact IMMEDIATELY: urgentjob@scammer.com
            """,
            expected_classification=JobClassification.LIKELY_SCAM,
            expected_trust_score_range=(0, 25),
            description="Classic advance fee scam with urgent payment demands and personal information requests",
            category="advance_fee_scam"
        ),
        
        JobAdSample(
            title="Fake Government Job",
            content="""
            GOVERNMENT JOB OPPORTUNITY - GUARANTEED POSITION
            
            The Department of Homeland Security is hiring!
            
            Position: Security Analyst
            Salary: $95,000 per year
            Benefits: Full government benefits package
            
            SPECIAL RECRUITMENT PROGRAM:
            - Bypass normal application process
            - Guaranteed job placement
            - Start within 30 days
            - No background check required
            
            REQUIREMENTS:
            - US Citizen (we can help with documentation)
            - High school diploma
            - Pass our online test
            - Pay $1,200 processing fee
            
            PROCESSING FEE COVERS:
            - Application processing
            - Security clearance expediting
            - Training materials
            - Uniform and equipment
            
            PAYMENT METHODS ACCEPTED:
            - Bitcoin (preferred for security)
            - Gift cards (iTunes, Amazon)
            - Wire transfer
            - Money order
            
            This is a LIMITED TIME government program!
            
            Contact: dhs-recruitment@govjobs.net
            Reference Code: DHS2024HIRE
            """,
            expected_classification=JobClassification.LIKELY_SCAM,
            expected_trust_score_range=(0, 20),
            description="Fake government job scam with processing fees and cryptocurrency payments",
            category="fake_government_job"
        ),
        
        JobAdSample(
            title="Investment Recovery Scam",
            content="""
            RECOVER YOUR LOST INVESTMENTS + EARN $50,000!
            
            Have you lost money to online scams? We can help!
            
            Our company specializes in recovering lost funds AND we have a job for you!
            
            JOB OFFER:
            - Investment Recovery Agent
            - Salary: $50,000 + commission
            - Work from home
            - Help other scam victims
            
            WE WILL:
            - Recover 100% of your lost money
            - Pay you $50,000 annual salary
            - Provide all training
            - Give you exclusive software
            
            TO START IMMEDIATELY:
            - Send $2,000 activation fee
            - Provide bank account information
            - Sign our exclusive contract
            - Give us power of attorney
            
            TESTIMONIALS:
            "I lost $10,000 to scammers but this company recovered it all plus paid me $50,000!" - Sarah M.
            "Best decision ever! Got my money back and a great job!" - Mike T.
            
            Act now! Limited positions available!
            
            Contact: recovery-jobs@scamrecovery.biz
            Phone: 1-800-GET-BACK (not a real number)
            """,
            expected_classification=JobClassification.LIKELY_SCAM,
            expected_trust_score_range=(0, 15),
            description="Recovery scam targeting previous scam victims with fake job offers",
            category="recovery_scam"
        )
    ]
    
    # Edge Cases and Special Scenarios
    EDGE_CASES = [
        JobAdSample(
            title="Minimal Information Job",
            content="""
            Job available. Good pay. Contact me.
            Email: job@email.com
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            expected_trust_score_range=(20, 40),
            description="Extremely vague job posting with minimal information",
            category="vague_posting"
        ),
        
        JobAdSample(
            title="Multilingual Job Posting",
            content="""
            Software Developer Position - TechCorp International
            
            English: We are hiring a software developer for our international team.
            Español: Estamos contratando un desarrollador de software para nuestro equipo internacional.
            Français: Nous embauchons un développeur de logiciels pour notre équipe internationale.
            
            Requirements:
            - 3+ years experience
            - Python, JavaScript
            - Remote work available
            
            Salary: $80,000 - $120,000
            Contact: careers@techcorp-intl.com
            """,
            expected_classification=JobClassification.LEGIT,
            expected_trust_score_range=(70, 90),
            description="Legitimate multilingual job posting for international company",
            category="multilingual"
        ),
        
        JobAdSample(
            title="Job with Typos and Grammar Issues",
            content="""
            Sofware Engeneer Postion - TechStartup
            
            We are lookng for a talanted sofware engeneer to join our team.
            
            Responsiblities:
            - Develope web aplications
            - Work with databses
            - Fix bugs and isues
            
            Requirments:
            - Bachelers degre in Computer Scince
            - 2+ yers experiance
            - Know Python and Java
            
            Salery: $70,000 - $90,000
            Benifits: Helth insuranse, 401k
            
            Contac: hr@techstartup.com
            Aply today!
            """,
            expected_classification=JobClassification.SUSPICIOUS,
            expected_trust_score_range=(40, 65),
            description="Job posting with multiple spelling and grammar errors",
            category="poor_grammar"
        )
    ]
    
    @classmethod
    def get_all_samples(cls) -> List[JobAdSample]:
        """Get all job advertisement samples."""
        return cls.LEGITIMATE_JOBS + cls.SUSPICIOUS_JOBS + cls.SCAM_JOBS + cls.EDGE_CASES
    
    @classmethod
    def get_samples_by_classification(cls, classification: JobClassification) -> List[JobAdSample]:
        """Get samples filtered by expected classification."""
        return [sample for sample in cls.get_all_samples() 
                if sample.expected_classification == classification]
    
    @classmethod
    def get_samples_by_category(cls, category: str) -> List[JobAdSample]:
        """Get samples filtered by category."""
        return [sample for sample in cls.get_all_samples() 
                if sample.category == category]
    
    @classmethod
    def get_sample_by_title(cls, title: str) -> JobAdSample:
        """Get a specific sample by title."""
        for sample in cls.get_all_samples():
            if sample.title == title:
                return sample
        raise ValueError(f"No sample found with title: {title}")


# Webhook data templates for testing
class WebhookDataFixtures:
    """Webhook request data templates for testing."""
    
    @staticmethod
    def create_text_webhook_data(message_sid: str, from_number: str, body: str) -> Dict[str, Any]:
        """Create webhook data for text message."""
        return {
            "MessageSid": message_sid,
            "From": from_number,
            "To": "whatsapp:+1234567890",
            "Body": body,
            "NumMedia": "0"
        }
    
    @staticmethod
    def create_media_webhook_data(message_sid: str, from_number: str, media_url: str, content_type: str = "application/pdf") -> Dict[str, Any]:
        """Create webhook data for media message."""
        return {
            "MessageSid": message_sid,
            "From": from_number,
            "To": "whatsapp:+1234567890",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": media_url,
            "MediaContentType0": content_type
        }
    
    @staticmethod
    def create_help_webhook_data(message_sid: str, from_number: str) -> Dict[str, Any]:
        """Create webhook data for help request."""
        return {
            "MessageSid": message_sid,
            "From": from_number,
            "To": "whatsapp:+1234567890",
            "Body": "help",
            "NumMedia": "0"
        }


# Test user phone numbers for different scenarios
class TestPhoneNumbers:
    """Test phone numbers for different user scenarios."""
    
    LEGITIMATE_USER = "whatsapp:+1987654321"
    SUSPICIOUS_USER = "whatsapp:+1987654322"
    SCAM_VICTIM = "whatsapp:+1987654323"
    HELP_SEEKER = "whatsapp:+1987654324"
    REPEAT_USER = "whatsapp:+1987654325"
    INTERNATIONAL_USER = "whatsapp:+44987654321"
    
    @classmethod
    def get_all_numbers(cls) -> List[str]:
        """Get all test phone numbers."""
        return [
            cls.LEGITIMATE_USER,
            cls.SUSPICIOUS_USER,
            cls.SCAM_VICTIM,
            cls.HELP_SEEKER,
            cls.REPEAT_USER,
            cls.INTERNATIONAL_USER
        ]