#!/usr/bin/env python3
"""
Create a test PDF with job posting content for testing the bot.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_job_pdf():
    """Create a PDF with a legitimate job posting."""
    
    filename = "test_job_posting.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add job posting content
    job_content = [
        "Software Developer Position",
        "",
        "Company: TechCorp Solutions",
        "Location: San Francisco, CA",
        "Salary: $80,000 - $120,000 per year",
        "",
        "Job Description:",
        "We are seeking a skilled Software Developer to join our growing team.",
        "",
        "Requirements:",
        "• Bachelor's degree in Computer Science or related field",
        "• 3+ years of experience in Python/JavaScript",
        "• Experience with React and Node.js",
        "• Strong problem-solving skills",
        "",
        "Responsibilities:",
        "• Develop and maintain web applications",
        "• Collaborate with cross-functional teams",
        "• Write clean, maintainable code",
        "• Participate in code reviews",
        "",
        "Benefits:",
        "• Health insurance",
        "• 401(k) matching",
        "• Flexible work hours",
        "• Professional development opportunities",
        "",
        "To apply, please send your resume to careers@techcorp.com",
        "or visit our website at www.techcorp.com/careers",
        "",
        "Company: TechCorp Solutions",
        "Founded: 2015",
        "Employees: 50-100",
        "Website: www.techcorp.com"
    ]
    
    # Write content to PDF
    y_position = height - 50
    for line in job_content:
        c.drawString(50, y_position, line)
        y_position -= 20
        
        # Start new page if needed
        if y_position < 50:
            c.showPage()
            y_position = height - 50
    
    c.save()
    print(f"✅ Created test job PDF: {filename}")
    print(f"📄 Content length: {len(' '.join(job_content))} characters")
    return filename

def create_scam_job_pdf():
    """Create a PDF with a scam job posting."""
    
    filename = "test_scam_job.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add scam job content
    scam_content = [
        "🚨 URGENT HIRING! 🚨",
        "WORK FROM HOME - EARN $5000/WEEK!",
        "NO EXPERIENCE NEEDED!",
        "",
        "Make $5000-8000 per week working from home!",
        "Only 2-3 hours per day required!",
        "No experience or qualifications needed!",
        "Start immediately!",
        "",
        "What you'll do:",
        "• Simple data entry",
        "• Copy and paste work",
        "• Process payments online",
        "",
        "Requirements:",
        "• Must have smartphone",
        "• Must be 18+",
        "• Must be willing to earn BIG MONEY!",
        "",
        "GUARANTEED INCOME! NO RISK!",
        "First week payment GUARANTEED!",
        "",
        "Contact immediately:",
        "Email: easymoney@fastcash.biz",
        "Phone: 555-SCAM-123",
        "",
        "⚠️ Limited spots available! Apply NOW!",
        "💰 Start earning TODAY!",
        "🏠 Work from anywhere!",
        "",
        "*Must pay $99 registration fee to secure position*",
        "*Training materials cost $199 (refundable)*"
    ]
    
    # Write content to PDF
    y_position = height - 50
    for line in scam_content:
        c.drawString(50, y_position, line)
        y_position -= 20
        
        # Start new page if needed
        if y_position < 50:
            c.showPage()
            y_position = height - 50
    
    c.save()
    print(f"✅ Created test scam PDF: {filename}")
    print(f"📄 Content length: {len(' '.join(scam_content))} characters")
    return filename

if __name__ == "__main__":
    print("📝 Creating test job PDFs...")
    
    try:
        legit_pdf = create_job_pdf()
        scam_pdf = create_scam_job_pdf()
        
        print(f"\n🎯 Test these PDFs with your WhatsApp bot:")
        print(f"   1. Legitimate job: {legit_pdf}")
        print(f"   2. Scam job: {scam_pdf}")
        
    except ImportError:
        print("❌ Missing reportlab library. Install it with:")
        print("   pip install reportlab")
    except Exception as e:
        print(f"❌ Error creating PDFs: {e}")