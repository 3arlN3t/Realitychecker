#!/usr/bin/env python3
"""
Simple database setup and data population script.

This script creates the database tables and populates them with sample data
without using the complex initialization system that has circular imports.
"""

import asyncio
import sys
import random
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import models to register them
from app.database.models import Base, WhatsAppUser, UserInteraction, SystemMetric, ErrorLog, JobClassificationEnum
from app.models.data_models import JobClassification


async def create_database_and_tables():
    """Create database and tables."""
    print("Creating database and tables...")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create async engine
    database_url = "sqlite+aiosqlite:///data/reality_checker.db"
    engine = create_async_engine(database_url, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database and tables created")
    return engine


async def populate_sample_data(engine):
    """Populate database with sample data."""
    print("Populating sample data...")
    
    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Sample phone numbers
    phone_numbers = [
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
        "whatsapp:web-user-001",
        "whatsapp:web-user-002",
        "whatsapp:web-user-003",
        "whatsapp:web-user-004",
        "whatsapp:web-user-005"
    ]
    
    # Sample job texts
    job_texts = [
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
    legit_reasons = [
        "Company has verified business registration and physical address",
        "Salary range is realistic for the position and location", 
        "Job requirements match industry standards for the role"
    ]
    
    suspicious_reasons = [
        "Salary seems unusually high for the position requirements",
        "Limited company information provided in the job posting",
        "Some red flags present but not definitively a scam"
    ]
    
    scam_reasons = [
        "Requires upfront payment or fees from applicants",
        "Promises unrealistic earnings with minimal work required",
        "Uses high-pressure tactics and urgency to rush decisions"
    ]
    
    async with async_session() as session:
        # Create users and interactions
        for i, phone_number in enumerate(phone_numbers):
            print(f"Creating user {i+1}/{len(phone_numbers)}: {phone_number}")
            
            # Create user
            user = WhatsAppUser(
                phone_number=phone_number,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90)),
                last_interaction=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                blocked=False
            )
            session.add(user)
            await session.flush()  # Get the user ID
            
            # Create random number of interactions (1-15 per user)
            num_interactions = random.randint(1, 15)
            successful_count = 0
            failed_count = 0
            total_response_time = 0.0
            
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
                job_text = random.choice(job_texts)
                
                # Generate message SID
                if phone_number.startswith("whatsapp:web-"):
                    message_sid = f"web-{int(interaction_time.timestamp())}-{j}"
                else:
                    message_sid = f"SM{random.randint(10000000, 99999999)}"
                
                # Random response time (0.5 to 5 seconds)
                response_time = random.uniform(0.5, 5.0)
                total_response_time += response_time
                
                # Create interaction
                interaction = UserInteraction(
                    user_id=user.id,
                    timestamp=interaction_time,
                    message_sid=message_sid,
                    message_type=message_type,
                    message_content=job_text[:200],  # Truncated
                    response_time=response_time,
                    processing_time=response_time * 0.8
                )
                
                # 95% success rate
                if random.random() < 0.95:
                    # Successful analysis
                    successful_count += 1
                    
                    # Determine classification (60% legit, 25% suspicious, 15% scam)
                    rand = random.random()
                    if rand < 0.6:
                        classification = JobClassificationEnum.LEGITIMATE
                        trust_score = random.randint(70, 95) / 100.0
                        reasons = legit_reasons
                    elif rand < 0.85:
                        classification = JobClassificationEnum.SUSPICIOUS  
                        trust_score = random.randint(40, 70) / 100.0
                        reasons = suspicious_reasons
                    else:
                        classification = JobClassificationEnum.SCAM
                        trust_score = random.randint(5, 40) / 100.0
                        reasons = scam_reasons
                    
                    interaction.trust_score = trust_score
                    interaction.classification = classification
                    interaction.classification_reasons = {"reasons": reasons}
                    interaction.confidence = random.uniform(0.7, 0.95)
                else:
                    # Failed analysis
                    failed_count += 1
                    error_types = ["openai_error", "pdf_processing_error", "timeout_error"]
                    error_messages = [
                        "OpenAI API rate limit exceeded",
                        "Failed to extract text from PDF",
                        "Request timeout after 30 seconds"
                    ]
                    
                    interaction.error_type = random.choice(error_types)
                    interaction.error_message = random.choice(error_messages)
                
                session.add(interaction)
            
            # Update user statistics
            user.total_requests = num_interactions
            user.successful_requests = successful_count
            user.failed_requests = failed_count
            user.avg_response_time = total_response_time / num_interactions if num_interactions > 0 else 0.0
        
        # Block a couple of users for testing
        blocked_users = random.sample(phone_numbers, 2)
        for phone_number in blocked_users:
            result = await session.execute(
                text("UPDATE whatsapp_users SET blocked = true, notes = 'Suspicious activity detected' WHERE phone_number = :phone"),
                {"phone": phone_number}
            )
            print(f"Blocked user: {phone_number}")
        
        await session.commit()
        print(f"✅ Created {len(phone_numbers)} users with sample interactions")
    
    await engine.dispose()


async def main():
    """Main function."""
    print("🚀 Setting up database with sample data...")
    
    try:
        # Create database and tables
        engine = await create_database_and_tables()
        
        # Populate with sample data
        await populate_sample_data(engine)
        
        print("\n🎉 Database setup completed successfully!")
        print("\nYou can now:")
        print("1. Start the application: python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Visit the dashboard: http://localhost:8000/dashboard")
        print("3. View analytics: http://localhost:8000/analytics")
        
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())