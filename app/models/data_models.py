"""
Core data models for the Reality Checker WhatsApp bot.

This module contains dataclasses for handling Twilio webhook requests,
OpenAI analysis results, and application configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import os
from enum import Enum


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