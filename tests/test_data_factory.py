"""
Test data factory for creating consistent test data.

This module provides factory functions for creating test data objects
with consistent structure and realistic values for testing purposes.
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

from app.models.data_models import JobAnalysisResult, JobClassification


class TestDataFactory:
    """Factory class for generating test data."""
    
    @staticmethod
    def generate_phone_number() -> str:
        """Generate a random phone number in WhatsApp format."""
        country_code = random.choice(["+1", "+44", "+61", "+91"])
        number = ''.join(random.choices(string.digits, k=10))
        return f"whatsapp:{country_code}{number}"
    
    @staticmethod
    def generate_message_sid() -> str:
        """Generate a random Twilio message SID."""
        return f"SM{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"
    
    @staticmethod
    def generate_timestamp(days_ago: int = 0, hours_ago: int = 0, minutes_ago: int = 0) -> str:
        """Generate an ISO format timestamp for a time in the past."""
        now = datetime.now()
        past_time = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        return past_time.isoformat() + "Z"
    
    @staticmethod
    def generate_job_analysis_result(
        classification: Optional[JobClassification] = None,
        trust_score: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> JobAnalysisResult:
        """Generate a job analysis result with specified or random values."""
        if classification is None:
            classification = random.choice(list(JobClassification))
        
        if trust_score is None:
            if classification == JobClassification.LEGIT:
                trust_score = random.randint(70, 100)
            elif classification == JobClassification.SUSPICIOUS:
                trust_score = random.randint(30, 69)
            else:  # LIKELY_SCAM
                trust_score = random.randint(0, 29)
        
        if confidence is None:
            confidence = round(random.uniform(0.7, 0.99), 2)
        
        # Generate reasons based on classification
        if classification == JobClassification.LEGIT:
            reasons = [
                "Company has verifiable online presence",
                "Job description is detailed and professional",
                "Salary range is realistic for the position"
            ]
        elif classification == JobClassification.SUSPICIOUS:
            reasons = [
                "Limited company information available",
                "Salary seems unusually high for requirements",
                "Unusual application process"
            ]
        else:  # LIKELY_SCAM
            reasons = [
                "Requests upfront payment",
                "Promises unrealistic earnings",
                "No verifiable company contact information"
            ]
        
        return JobAnalysisResult(
            trust_score=trust_score,
            classification=classification,
            reasons=reasons,
            confidence=confidence
        )
    
    @staticmethod
    def generate_webhook_data(
        message_type: str = "text",
        body: Optional[str] = None,
        media_url: Optional[str] = None,
        media_content_type: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: str = "whatsapp:+1234567890",
        message_sid: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate Twilio webhook data for testing."""
        if message_sid is None:
            message_sid = TestDataFactory.generate_message_sid()
        
        if from_number is None:
            from_number = TestDataFactory.generate_phone_number()
        
        if message_type == "text":
            if body is None:
                body = "This is a test message for job analysis."
            
            return {
                "MessageSid": message_sid,
                "From": from_number,
                "To": to_number,
                "Body": body,
                "NumMedia": "0"
            }
        elif message_type == "media":
            if media_url is None:
                media_url = "https://api.twilio.com/media/test-job-posting.pdf"
            
            if media_content_type is None:
                media_content_type = "application/pdf"
            
            return {
                "MessageSid": message_sid,
                "From": from_number,
                "To": to_number,
                "Body": body or "",
                "NumMedia": "1",
                "MediaUrl0": media_url,
                "MediaContentType0": media_content_type
            }
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
    
    @staticmethod
    def generate_user_data(
        user_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        status: str = "active",
        interaction_count: Optional[int] = None,
        trust_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate user data for testing."""
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        if phone_number is None:
            phone_number = TestDataFactory.generate_phone_number().replace("whatsapp:", "")
        
        if interaction_count is None:
            interaction_count = random.randint(1, 50)
        
        if trust_score is None:
            trust_score = random.randint(0, 100)
        
        return {
            "id": user_id,
            "phoneNumber": phone_number,
            "status": status,
            "interactionCount": interaction_count,
            "lastInteraction": TestDataFactory.generate_timestamp(
                days_ago=random.randint(0, 30),
                hours_ago=random.randint(0, 23),
                minutes_ago=random.randint(0, 59)
            ),
            "trustScore": trust_score
        }
    
    @staticmethod
    def generate_user_interaction(
        interaction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        message_type: str = "text",
        content: Optional[str] = None,
        timestamp: Optional[str] = None,
        analysis_result: Optional[JobAnalysisResult] = None
    ) -> Dict[str, Any]:
        """Generate user interaction data for testing."""
        if interaction_id is None:
            interaction_id = str(uuid.uuid4())
        
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        if timestamp is None:
            timestamp = TestDataFactory.generate_timestamp(
                days_ago=random.randint(0, 30),
                hours_ago=random.randint(0, 23),
                minutes_ago=random.randint(0, 59)
            )
        
        if content is None:
            if message_type == "text":
                content = "This is a test message for job analysis."
            elif message_type == "pdf":
                content = "PDF content extracted from document."
            elif message_type == "response":
                content = "Analysis result: Legitimate job posting."
            else:
                content = "Generic interaction content."
        
        interaction = {
            "id": interaction_id,
            "userId": user_id,
            "timestamp": timestamp,
            "messageType": message_type,
            "content": content
        }
        
        if analysis_result:
            interaction["analysisResult"] = {
                "trustScore": analysis_result.trust_score,
                "classification": analysis_result.classification.value,
                "reasons": analysis_result.reasons,
                "confidence": analysis_result.confidence
            }
        
        return interaction
    
    @staticmethod
    def generate_system_metrics(
        total_requests: Optional[int] = None,
        requests_today: Optional[int] = None,
        error_rate: Optional[float] = None,
        avg_response_time: Optional[float] = None
    ) -> Dict[str, Union[int, float]]:
        """Generate system metrics data for testing."""
        if total_requests is None:
            total_requests = random.randint(1000, 10000)
        
        if requests_today is None:
            requests_today = random.randint(10, 500)
        
        if error_rate is None:
            error_rate = round(random.uniform(0.1, 5.0), 2)
        
        if avg_response_time is None:
            avg_response_time = round(random.uniform(0.5, 3.0), 2)
        
        return {
            "totalRequests": total_requests,
            "requestsToday": requests_today,
            "errorRate": error_rate,
            "avgResponseTime": avg_response_time
        }
    
    @staticmethod
    def generate_system_health(
        status: str = "healthy",
        services: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate system health data for testing."""
        if services is None:
            services = {
                "openai": {
                    "status": random.choice(["healthy", "degraded", "down"]),
                    "responseTime": random.randint(100, 500),
                    "lastCheck": TestDataFactory.generate_timestamp(minutes_ago=random.randint(1, 10)),
                    "errorCount": random.randint(0, 10)
                },
                "twilio": {
                    "status": random.choice(["healthy", "degraded", "down"]),
                    "responseTime": random.randint(50, 300),
                    "lastCheck": TestDataFactory.generate_timestamp(minutes_ago=random.randint(1, 10)),
                    "errorCount": random.randint(0, 5)
                },
                "database": {
                    "status": random.choice(["healthy", "degraded", "down"]),
                    "responseTime": random.randint(10, 200),
                    "lastCheck": TestDataFactory.generate_timestamp(minutes_ago=random.randint(1, 10)),
                    "errorCount": random.randint(0, 3)
                }
            }
        
        return {
            "status": status,
            "uptime": f"{random.uniform(95.0, 100.0):.1f}%",
            "lastUpdated": datetime.now().strftime("%H:%M:%S"),
            "memoryUsage": random.randint(30, 90),
            "cpuUsage": random.randint(20, 80),
            "services": services
        }
    
    @staticmethod
    def generate_classification_data() -> List[Dict[str, Any]]:
        """Generate classification breakdown data for testing."""
        legit_count = random.randint(300, 700)
        suspicious_count = random.randint(100, 300)
        scam_count = random.randint(50, 200)
        
        return [
            {"name": "Legitimate", "value": legit_count, "color": "#4caf50"},
            {"name": "Suspicious", "value": suspicious_count, "color": "#ff9800"},
            {"name": "Likely Scam", "value": scam_count, "color": "#f44336"}
        ]
    
    @staticmethod
    def generate_usage_trends_data(days: int = 30) -> List[Dict[str, Any]]:
        """Generate usage trends data for testing."""
        result = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Generate some realistic patterns (weekends have less traffic)
            is_weekend = current_date.weekday() >= 5
            base_requests = random.randint(30, 70) if is_weekend else random.randint(70, 150)
            
            # Add some randomness
            requests = max(0, int(base_requests * random.uniform(0.8, 1.2)))
            
            result.append({
                "date": date_str,
                "requests": requests,
                "scams": int(requests * random.uniform(0.05, 0.15)),
                "responseTime": round(random.uniform(0.5, 2.0), 2)
            })
        
        return result
    
    @staticmethod
    def generate_peak_hours_data() -> List[Dict[str, Any]]:
        """Generate peak hours data for testing."""
        result = []
        
        for hour in range(24):
            # Generate realistic traffic patterns
            if 0 <= hour < 6:  # Night (low traffic)
                base_requests = random.randint(5, 20)
            elif 6 <= hour < 9:  # Morning (increasing traffic)
                base_requests = random.randint(20, 50)
            elif 9 <= hour < 17:  # Work hours (high traffic)
                base_requests = random.randint(50, 100)
            elif 17 <= hour < 22:  # Evening (moderate traffic)
                base_requests = random.randint(30, 70)
            else:  # Late night (decreasing traffic)
                base_requests = random.randint(10, 30)
            
            # Add some randomness
            requests = max(0, int(base_requests * random.uniform(0.8, 1.2)))
            
            result.append({
                "hour": hour,
                "requests": requests
            })
        
        return result
    
    @staticmethod
    def generate_active_requests(count: int = 5) -> List[Dict[str, Any]]:
        """Generate active requests data for testing."""
        result = []
        
        for i in range(count):
            request_type = random.choice(["text_analysis", "pdf_processing"])
            status = random.choice(["processing", "completed", "failed"])
            
            # Generate realistic duration based on type and status
            if request_type == "text_analysis":
                base_duration = random.randint(1000, 5000)  # 1-5 seconds
            else:  # pdf_processing
                base_duration = random.randint(3000, 10000)  # 3-10 seconds
            
            if status == "processing":
                # Still running, so duration is current time elapsed
                duration = random.randint(100, base_duration)
            else:
                # Completed or failed, so full duration
                duration = base_duration
            
            result.append({
                "id": f"req-{uuid.uuid4()}",
                "type": request_type,
                "status": status,
                "startedAt": TestDataFactory.generate_timestamp(
                    minutes_ago=random.randint(0, 10),
                    seconds_ago=random.randint(0, 59)
                ),
                "duration": duration,
                "user": TestDataFactory.generate_phone_number().replace("whatsapp:", "")
            })
        
        return result
    
    @staticmethod
    def generate_error_rate_data(points: int = 20) -> List[Dict[str, Any]]:
        """Generate error rate time series data for testing."""
        result = []
        base_time = datetime.now() - timedelta(minutes=points)
        
        for i in range(points):
            current_time = base_time + timedelta(minutes=i)
            
            # Generate realistic error rate with occasional spikes
            if random.random() < 0.1:  # 10% chance of spike
                error_rate = random.uniform(3.0, 8.0)
            else:
                error_rate = random.uniform(0.1, 2.0)
            
            result.append({
                "time": current_time.isoformat() + "Z",
                "rate": round(error_rate, 2)
            })
        
        return result
    
    @staticmethod
    def generate_response_time_data(points: int = 20) -> List[Dict[str, Any]]:
        """Generate response time time series data for testing."""
        result = []
        base_time = datetime.now() - timedelta(minutes=points)
        
        for i in range(points):
            current_time = base_time + timedelta(minutes=i)
            
            # Generate realistic response times
            p50 = random.uniform(0.2, 0.8)
            p95 = p50 * random.uniform(1.5, 2.5)
            p99 = p95 * random.uniform(1.2, 2.0)
            
            result.append({
                "time": current_time.isoformat() + "Z",
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2)
            })
        
        return result


# Example usage
if __name__ == "__main__":
    # Generate some test data examples
    print("Example webhook data:")
    print(TestDataFactory.generate_webhook_data())
    print("\nExample job analysis result:")
    print(TestDataFactory.generate_job_analysis_result())
    print("\nExample user data:")
    print(TestDataFactory.generate_user_data())
    print("\nExample system metrics:")
    print(TestDataFactory.generate_system_metrics())