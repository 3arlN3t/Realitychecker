#!/usr/bin/env python3
"""
Populate the database with sample data for testing the dashboard.

This script creates realistic sample data including users, interactions,
and analysis results to demonstrate the dashboard functionality.
"""

import asyncio
import sys
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.database import get_database
from app.database.repositories import WhatsAppUserRepository, UserInteractionRepository
from app.database.models import JobClassificationEnum
from app.models.data_models import JobAnalysisResult, JobClassification
from app.utils.logging import get_loggerlogger

logger = get_logger(__name__)


# Sample phone numbers (anonymized)
SAMPLE_PHONE_NUMBERS = [
    "whatsapp:+1234567890",
    "whatsapp:+1234567891", 
    "whatsapp:+1234567892",
    "whatsapp:+1234567893",
    "whatsapp:+1234567894",
    "whatsapp:+1234567895",
    "whatsapp:+1234567896",
    "whatsapp:+1234567897",
    "whatsapp:+1234567898",
    "whatsapp:+1234567899",
    "web-user-001",
    "web-user-002",
    "web-user-003",
    "web-user-004",
    "web-user-005"
]

# Sample job ad texts
SAMPLE_JOB_TEXTS = [
    "Legitimate software engineer position at tech company. Competitive salary, benefits, remote work options.",
    "Data entry work from home. $50/hour. No experience needed. Send $200 processing fee to get started.",
    "Marketing manager role at established company. 5+ years experience required. Apply through our website.",
    "URGENT! Make $5000/week working from home! No skills needed! Send money for starter kit!",
    "Customer service representative position. Full training provided. Apply with resume and cover letter.",
    "Investment opportunity! Double your money in 30 days! Send $1000 to start earning immediately!",
    "Graphic designer needed for creative agency. Portfolio required. Competitive salary and benefits.",
    "Mystery shopper job. Get paid to shop! Send $100 registration fee to begin earning $300/day!",
    "Software developer position at startup. Equity options available. Strong technical skills required.",
    "Work from home assembling products! Earn $25/hour! Pay $150 for materials and instructions!"
]

# Sample analysis reasons
LEGIT_REASONS = [
    "Company has verified business registration and physical address",
    "Salary range is realistic for the position and location", 
    "Job requirements match industry standards for the role"
]

SUSPICIOUS_REASONS = [
    "Salary seems unusually high for the position requirements",
    "Limited company information provided in the job posting",
    "Some red flags present but not definitively a scam"
]

SCAM_REASONS = [
    "Requires upfront payment or fees from applicants",
    "Promises unrealistic earnings with minimal work required",
    "Uses high-pressure tactics and urgency to rush decisions"
]


async def create_sample_users_and_interactions():
    """Create sample users and their interactions."""
    print("Creating sample users and interactions...")
    
    db = get_database()
    await db.initialize()
    
    async with db.get_session() as session:
        user_repo = WhatsAppUserRepository(session)
        interaction_repo = UserInteractionRepository(session)
        
        # Create users and interactions
        for i, phone_number in enumerate(SAMPLE_PHONE_NUMBERS):
            print(f"Creating user {i+1}/{len(SAMPLE_PHONE_NUMBERS)}: {phone_number}")
            
            # Create or get user
            user = await user_repo.get_or_create_user(phone_number)
            
            # Create random number of interactions (1-10 per user)
            num_interactions = random.randint(1, 10)
            
            for j in range(num_interactions):
                # Random timestamp in the last 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                interaction_time = datetime.now(timezone.utc) - timedelta(
                    days=days_ago, 
                    hours=hours_ago, 
                    minutes=minutes_ago
                )
                
                # Random message type (80% text, 20% PDF)
                message_type = "text" if random.random() < 0.8 else "pdf"
                
                # Random job text
                job_text = random.choice(SAMPLE_JOB_TEXTS)
                
                # Generate message SID
                if phone_number.startswith("web-"):
                    message_sid = f"web-{interaction_time.timestamp()}-{j}"
                else:
                    message_sid = f"SM{random.randint(10000000, 99999999)}{random.randint(100000, 999999)}"
                
                # Create interaction
                interaction = await interaction_repo.create_interaction(
                    user_id=user.id,
                    message_sid=message_sid,
                    message_type=message_type,
                    message_content=job_text[:200]  # Truncated
                )
                
                # Set interaction timestamp
                interaction.timestamp = interaction_time
                
                # Determine classification (60% legit, 25% suspicious, 15% scam)
                rand = random.random()
                if rand < 0.6:
                    classification = JobClassificationEnum.LEGITIMATE
                    trust_score = random.randint(70, 95) / 100.0
                    reasons = LEGIT_REASONS
                elif rand < 0.85:
                    classification = JobClassificationEnum.SUSPICIOUS  
                    trust_score = random.randint(40, 70) / 100.0
                    reasons = SUSPICIOUS_REASONS
                else:
                    classification = JobClassificationEnum.SCAM
                    trust_score = random.randint(5, 40) / 100.0
                    reasons = SCAM_REASONS
                
                # Random response time (0.5 to 5 seconds)
                response_time = random.uniform(0.5, 5.0)
                
                # 95% success rate
                if random.random() < 0.95:
                    # Successful analysis
                    interaction.trust_score = trust_score
                    interaction.classification = classification
                    interaction.classification_reasons = {"reasons": reasons}
                    interaction.confidence = random.uniform(0.7, 0.95)
                    interaction.response_time = response_time
                    interaction.processing_time = response_time * 0.8
                    
                    # Update user stats
                    await user_repo.update_user_stats(user.id, True, response_time)
                else:
                    # Failed analysis
                    error_types = ["openai_error", "pdf_processing_error", "timeout_error"]
                    error_messages = [
                        "OpenAI API rate limit exceeded",
                        "Failed to extract text from PDF",
                        "Request timeout after 30 seconds"
                    ]
                    
                    error_type = random.choice(error_types)
                    error_message = random.choice(error_messages)
                    
                    await interaction_repo.record_error(
                        interaction.id,
                        error_type,
                        error_message
                    )
                    
                    # Update user stats for failed analysis
                    await user_repo.update_user_stats(user.id, False, response_time)
                
                await session.commit()
                
        print(f"✅ Created {len(SAMPLE_PHONE_NUMBERS)} users with sample interactions")


async def main():
    """Main function to populate sample data."""
    try:
        logger.info("Starting sample data population...")
        await create_sample_users_and_interactions()
        logger.info("Sample data population completed successfully")
        print("\n🎉 Sample data population completed!")
        print("You can now view the dashboard with realistic test data.")
        
    except Exception as e:
        logger.error(f"Error populating sample data: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())update_interaction_error(
                        interaction.id,
                        error_type,
                        error_message,
                        response_time
                    )
                    
                    # Update user stats
                    await user_repo.update_user_stats(user.id, False, response_time)
        
        # Block a couple of users for testing
        blocked_users = random.sample(SAMPLE_PHONE_NUMBERS, 2)
        for phone_number in blocked_users:
            user = await user_repo.get_by_phone_number(phone_number)
            if user:
                await user_repo.block_user(user.id, "Suspicious activity detected")
                print(f"Blocked user: {phone_number}")
        
        await session.commit()
        print(f"✅ Created {len(SAMPLE_PHONE_NUMBERS)} users with sample interactions")


async def create_sample_system_metrics():
    """Create sample system metrics for the last 7 days."""
    print("Creating sample system metrics...")
    
    db = get_database()
    
    async with db.get_session() as session:
        from app.database.repositories import SystemMetricRepository
        metric_repo = SystemMetricRepository(session)
        
        # Create metrics for the last 7 days (every hour)
        now = datetime.now(timezone.utc)
        
        for day in range(7):
            for hour in range(24):
                metric_time = now - timedelta(days=day, hours=hour)
                
                # Simulate realistic metrics with some variation
                base_cpu = 30 + random.uniform(-10, 20)  # 20-50% CPU
                base_memory = 60 + random.uniform(-15, 25)  # 45-85% Memory
                base_disk = 40 + random.uniform(-10, 15)  # 30-55% Disk
                
                # Higher activity during business hours
                if 9 <= (metric_time.hour) <= 17:
                    base_cpu += 15
                    base_memory += 10
                
                # Clamp values to realistic ranges
                cpu_usage = max(5, min(95, base_cpu))
                memory_usage = max(20, min(90, base_memory))
                disk_usage = max(15, min(80, base_disk))
                
                # Request metrics
                total_requests = random.randint(50, 200) if 9 <= metric_time.hour <= 17 else random.randint(10, 50)
                successful_requests = int(total_requests * random.uniform(0.92, 0.98))
                failed_requests = total_requests - successful_requests
                
                # Response time metrics
                avg_response_time = random.uniform(0.8, 3.5)
                max_response_time = avg_response_time * random.uniform(2, 5)
                min_response_time = avg_response_time * random.uniform(0.3, 0.7)
                
                # OpenAI metrics
                openai_requests = int(total_requests * random.uniform(0.7, 0.9))
                openai_failures = int(openai_requests * random.uniform(0.02, 0.08))
                openai_avg_response_time = random.uniform(1.2, 4.0)
                
                await metric_repo.record_metric(
                    timestamp=metric_time,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    active_connections=random.randint(5, 25),
                    total_requests=total_requests,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    avg_response_time=avg_response_time,
                    max_response_time=max_response_time,
                    min_response_time=min_response_time,
                    openai_requests=openai_requests,
                    openai_failures=openai_failures,
                    openai_avg_response_time=openai_avg_response_time
                )
        
        await session.commit()
        print("✅ Created sample system metrics for the last 7 days")


async def create_sample_error_logs():
    """Create sample error logs."""
    print("Creating sample error logs...")
    
    db = get_database()
    
    async with db.get_session() as session:
        from app.database.repositories import ErrorLogRepository
        error_repo = ErrorLogRepository(session)
        
        error_types = [
            ("OpenAIError", "OpenAI API rate limit exceeded", "openai_service"),
            ("PDFProcessingError", "Failed to extract text from PDF file", "pdf_service"),
            ("TwilioError", "Failed to send WhatsApp message", "twilio_service"),
            ("DatabaseError", "Connection timeout to database", "database"),
            ("ValidationError", "Invalid phone number format", "webhook_handler"),
            ("TimeoutError", "Request processing timeout", "message_handler")
        ]
        
        # Create errors for the last 7 days
        now = datetime.now(timezone.utc)
        
        for day in range(7):
            # Random number of errors per day (0-10)
            num_errors = random.randint(0, 10)
            
            for _ in range(num_errors):
                error_time = now - timedelta(
                    days=day,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                error_type, error_message, component = random.choice(error_types)
                severity = random.choice(["ERROR", "ERROR", "ERROR", "CRITICAL"])  # Mostly ERROR
                
                await error_repo.log_error(
                    error_type=error_type,
                    error_message=error_message,
                    component=component,
                    severity=severity,
                    timestamp=error_time
                )
        
        await session.commit()
        print("✅ Created sample error logs")


async def main():
    """Main function to populate all sample data."""
    print("🚀 Populating database with sample data...")
    
    try:
        # Initialize database first
        print("Initializing database...")
        db = get_database()
        await db.initialize()
        print("✅ Database initialized")
        
        # Create sample data
        await create_sample_users_and_interactions()
        await create_sample_system_metrics()
        await create_sample_error_logs()
        
        print("\n🎉 Sample data population completed successfully!")
        print("\nYou can now:")
        print("1. Start the application: python -m uvicorn app.main:app --reload")
        print("2. Visit the dashboard: http://localhost:8000/dashboard")
        print("3. View analytics: http://localhost:8000/analytics")
        
    except Exception as e:
        print(f"❌ Failed to populate sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())