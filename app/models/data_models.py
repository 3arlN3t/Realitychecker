"""
Core data models for the Reality Checker WhatsApp bot.

This module contains dataclasses for handling Twilio webhook requests,
OpenAI analysis results, and application configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
from enum import Enum
from datetime import datetime


class JobClassification(Enum):
    """Enumeration for job ad classification types."""
    LEGIT = "Legit"
    SUSPICIOUS = "Suspicious"
    LIKELY_SCAM = "Likely Scam"


@dataclass
class TwilioWebhookRequest:
    """
    Dataclass representing a Twilio WhatsApp webhook request.
    
    Validates and structures incoming webhook data from Twilio.
    """
    MessageSid: str
    From: str
    To: str
    Body: str
    NumMedia: int
    MediaUrl0: Optional[str] = None
    MediaContentType0: Optional[str] = None
    
    def __post_init__(self):
        """Validate the webhook request data after initialization."""
        if not self.MessageSid:
            raise ValueError("MessageSid is required")
        if not self.From:
            raise ValueError("From phone number is required")
        if not self.To:
            raise ValueError("To phone number is required")
        if self.NumMedia < 0:
            raise ValueError("NumMedia cannot be negative")
        if self.NumMedia > 0 and not self.MediaUrl0:
            raise ValueError("MediaUrl0 is required when NumMedia > 0")
    
    @property
    def has_media(self) -> bool:
        """Check if the message contains media attachments."""
        return self.NumMedia > 0 and self.MediaUrl0 is not None
    
    @property
    def is_pdf_media(self) -> bool:
        """Check if the media attachment is a PDF."""
        return (self.has_media and 
                self.MediaContentType0 and 
                'pdf' in self.MediaContentType0.lower())


@dataclass
class JobAnalysisResult:
    """
    Dataclass representing the result of job ad scam analysis.
    
    Contains trust score, classification, and reasoning from OpenAI analysis.
    """
    trust_score: int
    classification: JobClassification
    reasons: List[str]
    confidence: float = 0.0
    
    def __post_init__(self):
        """Validate the analysis result data after initialization."""
        if not (0 <= self.trust_score <= 100):
            raise ValueError("Trust score must be between 0 and 100")
        if not isinstance(self.classification, JobClassification):
            raise ValueError("Classification must be a JobClassification enum")
        if len(self.reasons) != 3:
            raise ValueError("Exactly 3 reasons must be provided")
        if not all(isinstance(reason, str) and reason.strip() for reason in self.reasons):
            raise ValueError("All reasons must be non-empty strings")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    @property
    def classification_text(self) -> str:
        """Get the classification as a string."""
        return self.classification.value


@dataclass
class AppConfig:
    """
    Dataclass for application configuration loaded from environment variables.
    
    Manages all configuration settings including API keys and operational parameters.
    """
    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    max_pdf_size_mb: int = 10
    openai_model: str = "gpt-4"
    log_level: str = "INFO"
    webhook_validation: bool = True
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        if not self.twilio_account_sid:
            raise ValueError("Twilio Account SID is required")
        if not self.twilio_auth_token:
            raise ValueError("Twilio Auth Token is required")
        if not self.twilio_phone_number:
            raise ValueError("Twilio phone number is required")
        if self.max_pdf_size_mb <= 0:
            raise ValueError("Max PDF size must be positive")
        if not self.openai_model:
            raise ValueError("OpenAI model is required")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create AppConfig instance from environment variables.
        
        Returns:
            AppConfig: Configuration instance with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
            max_pdf_size_mb=int(os.getenv("MAX_PDF_SIZE_MB", "10")),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            webhook_validation=os.getenv("WEBHOOK_VALIDATION", "true").lower() == "true"
        )


@dataclass
class UserInteraction:
    """
    Dataclass representing a single user interaction with the bot.
    
    Tracks individual message exchanges and their analysis results.
    """
    timestamp: datetime
    message_type: str  # "text" or "pdf"
    message_content: Optional[str] = None  # Truncated for privacy
    analysis_result: Optional[JobAnalysisResult] = None
    response_time: float = 0.0  # Response time in seconds
    error: Optional[str] = None
    message_sid: Optional[str] = None
    
    def __post_init__(self):
        """Validate interaction data after initialization."""
        if self.message_type not in ["text", "pdf"]:
            raise ValueError("Message type must be 'text' or 'pdf'")
        if self.response_time < 0:
            raise ValueError("Response time cannot be negative")
        if self.message_content and len(self.message_content) > 200:
            # Truncate content for privacy and storage efficiency
            self.message_content = self.message_content[:200] + "..."
    
    @property
    def was_successful(self) -> bool:
        """Check if the interaction was processed successfully."""
        return self.error is None and self.analysis_result is not None
    
    @property
    def classification_text(self) -> Optional[str]:
        """Get the classification result as text."""
        return self.analysis_result.classification_text if self.analysis_result else None


@dataclass
class UserDetails:
    """
    Dataclass representing detailed information about a WhatsApp user.
    
    Contains user metadata, interaction history, and management status.
    """
    phone_number: str
    first_interaction: datetime
    last_interaction: datetime
    total_requests: int = 0
    blocked: bool = False
    interaction_history: List[UserInteraction] = field(default_factory=list)
    user_agent: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate user details after initialization."""
        if not self.phone_number:
            raise ValueError("Phone number is required")
        if not self.phone_number.startswith("whatsapp:"):
            raise ValueError("Phone number must be in WhatsApp format (whatsapp:+1234567890)")
        if self.total_requests < 0:
            raise ValueError("Total requests cannot be negative")
        if self.first_interaction > self.last_interaction:
            raise ValueError("First interaction cannot be after last interaction")
    
    @property
    def sanitized_phone_number(self) -> str:
        """Get sanitized phone number for logging."""
        if len(self.phone_number) > 15:
            return self.phone_number[:12] + "***"
        return self.phone_number
    
    @property
    def days_since_first_interaction(self) -> int:
        """Calculate days since first interaction."""
        return (datetime.utcnow() - self.first_interaction).days
    
    @property
    def days_since_last_interaction(self) -> int:
        """Calculate days since last interaction."""
        return (datetime.utcnow() - self.last_interaction).days
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time for successful interactions."""
        successful_interactions = [i for i in self.interaction_history if i.was_successful]
        if not successful_interactions:
            return 0.0
        return sum(i.response_time for i in successful_interactions) / len(successful_interactions)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of interactions."""
        if not self.interaction_history:
            return 0.0
        successful = sum(1 for i in self.interaction_history if i.was_successful)
        return successful / len(self.interaction_history)
    
    def add_interaction(self, interaction: UserInteraction) -> None:
        """
        Add a new interaction to the user's history.
        
        Args:
            interaction: UserInteraction to add
        """
        self.interaction_history.append(interaction)
        self.total_requests += 1
        self.last_interaction = interaction.timestamp
        
        # Keep only the last 50 interactions to manage memory
        if len(self.interaction_history) > 50:
            self.interaction_history = self.interaction_history[-50:]
    
    def get_recent_interactions(self, limit: int = 10) -> List[UserInteraction]:
        """
        Get the most recent interactions.
        
        Args:
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent UserInteraction objects
        """
        return sorted(self.interaction_history, key=lambda x: x.timestamp, reverse=True)[:limit]


@dataclass
class UserList:
    """
    Dataclass representing a paginated list of users.
    
    Used for API responses when listing users with pagination.
    """
    users: List[UserDetails]
    total: int
    page: int
    pages: int
    limit: int
    
    def __post_init__(self):
        """Validate user list data after initialization."""
        if self.page < 1:
            raise ValueError("Page number must be at least 1")
        if self.pages < 0:
            raise ValueError("Total pages cannot be negative")
        if self.limit < 1:
            raise ValueError("Limit must be at least 1")
        if self.total < 0:
            raise ValueError("Total count cannot be negative")
        if len(self.users) > self.limit:
            raise ValueError("Users list cannot exceed limit")


@dataclass
class UserSearchCriteria:
    """
    Dataclass for user search and filtering criteria.
    
    Used to filter users based on various criteria.
    """
    phone_number: Optional[str] = None
    blocked: Optional[bool] = None
    min_requests: Optional[int] = None
    max_requests: Optional[int] = None
    days_since_last_interaction: Optional[int] = None
    has_errors: Optional[bool] = None
    classification_filter: Optional[JobClassification] = None
    
    def matches_user(self, user: UserDetails) -> bool:
        """
        Check if a user matches the search criteria.
        
        Args:
            user: UserDetails to check against criteria
            
        Returns:
            bool: True if user matches all specified criteria
        """
        if self.phone_number and self.phone_number not in user.phone_number:
            return False
        
        if self.blocked is not None and user.blocked != self.blocked:
            return False
        
        if self.min_requests is not None and user.total_requests < self.min_requests:
            return False
        
        if self.max_requests is not None and user.total_requests > self.max_requests:
            return False
        
        if self.days_since_last_interaction is not None:
            if user.days_since_last_interaction < self.days_since_last_interaction:
                return False
        
        if self.has_errors is not None:
            user_has_errors = any(i.error is not None for i in user.interaction_history)
            if user_has_errors != self.has_errors:
                return False
        
        if self.classification_filter is not None:
            user_has_classification = any(
                i.analysis_result and i.analysis_result.classification == self.classification_filter
                for i in user.interaction_history
            )
            if not user_has_classification:
                return False
        
        return True