"""
Core data models for the Reality Checker WhatsApp bot.

This module contains dataclasses for handling Twilio webhook requests,
OpenAI analysis results, and application configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
from enum import Enum
from datetime import datetime, timedelta


class JobClassification(Enum):
    """Enumeration for job ad classification types."""
    LEGIT = "Legit"
    SUSPICIOUS = "Suspicious"
    LIKELY_SCAM = "Likely Scam"


class UserRole(Enum):
    """Enumeration for user roles in the system."""
    ADMIN = "admin"
    ANALYST = "analyst"


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


@dataclass
class DashboardOverview:
    """
    Dataclass representing dashboard overview metrics.
    
    Contains key performance indicators for the admin dashboard.
    """
    total_requests: int
    requests_today: int
    error_rate: float
    avg_response_time: float
    active_users: int
    system_health: str
    timestamp: datetime
    
    def __post_init__(self):
        """Validate dashboard overview data after initialization."""
        if self.total_requests < 0:
            raise ValueError("Total requests cannot be negative")
        if self.requests_today < 0:
            raise ValueError("Requests today cannot be negative")
        if not (0.0 <= self.error_rate <= 100.0):
            raise ValueError("Error rate must be between 0.0 and 100.0")
        if self.avg_response_time < 0:
            raise ValueError("Average response time cannot be negative")
        if self.active_users < 0:
            raise ValueError("Active users cannot be negative")
        if self.system_health not in ["healthy", "warning", "critical"]:
            raise ValueError("System health must be 'healthy', 'warning', or 'critical'")


@dataclass
class AnalyticsTrends:
    """
    Dataclass representing analytics trends and statistics.
    
    Contains trend data for the analytics dashboard.
    """
    period: str
    classifications: Dict[str, int]
    daily_counts: List[Dict[str, Any]]
    peak_hours: List[int]
    user_engagement: Dict[str, float]
    
    def __post_init__(self):
        """Validate analytics trends data after initialization."""
        if self.period not in ["day", "week", "month", "year"]:
            raise ValueError("Period must be 'day', 'week', 'month', or 'year'")
        
        # Validate classifications
        expected_classifications = {"Legit", "Suspicious", "Likely Scam"}
        if not all(key in expected_classifications for key in self.classifications.keys()):
            raise ValueError("Classifications must contain only valid classification types")
        
        if any(count < 0 for count in self.classifications.values()):
            raise ValueError("Classification counts cannot be negative")
        
        # Validate daily counts structure
        for daily_count in self.daily_counts:
            if "date" not in daily_count or "count" not in daily_count:
                raise ValueError("Daily counts must contain 'date' and 'count' keys")
            if daily_count["count"] < 0:
                raise ValueError("Daily count values cannot be negative")
        
        # Validate peak hours (0-23)
        if any(hour < 0 or hour > 23 for hour in self.peak_hours):
            raise ValueError("Peak hours must be between 0 and 23")
        
        # Validate user engagement metrics
        if any(value < 0 for value in self.user_engagement.values()):
            raise ValueError("User engagement values cannot be negative")


@dataclass
class UsageStatistics:
    """
    Dataclass representing detailed usage statistics.
    
    Contains comprehensive usage metrics for reporting.
    """
    total_messages: int
    text_messages: int
    pdf_messages: int
    successful_analyses: int
    failed_analyses: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    unique_users: int
    returning_users: int
    blocked_users: int
    classification_breakdown: Dict[str, int]
    error_breakdown: Dict[str, int]
    hourly_distribution: Dict[int, int]
    daily_distribution: Dict[str, int]
    
    def __post_init__(self):
        """Validate usage statistics after initialization."""
        if any(value < 0 for value in [
            self.total_messages, self.text_messages, self.pdf_messages,
            self.successful_analyses, self.failed_analyses, self.unique_users,
            self.returning_users, self.blocked_users
        ]):
            raise ValueError("Count values cannot be negative")
        
        if any(value < 0 for value in [
            self.average_response_time, self.median_response_time, self.p95_response_time
        ]):
            raise ValueError("Response time values cannot be negative")
        
        if self.text_messages + self.pdf_messages != self.total_messages:
            raise ValueError("Text and PDF message counts must sum to total messages")
        
        # Validate hourly distribution (0-23 hours)
        if any(hour < 0 or hour > 23 for hour in self.hourly_distribution.keys()):
            raise ValueError("Hourly distribution keys must be between 0 and 23")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total_analyses = self.successful_analyses + self.failed_analyses
        if total_analyses == 0:
            return 0.0
        return (self.successful_analyses / total_analyses) * 100
    
    @property
    def pdf_usage_rate(self) -> float:
        """Calculate PDF usage rate percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.pdf_messages / self.total_messages) * 100
    
    @property
    def user_retention_rate(self) -> float:
        """Calculate user retention rate percentage."""
        if self.unique_users == 0:
            return 0.0
        return (self.returning_users / self.unique_users) * 100


@dataclass
class ReportData:
    """
    Dataclass representing generated report data.
    
    Contains report metadata and data for export.
    """
    report_type: str
    generated_at: datetime
    period: str
    data: Dict[str, Any]
    export_format: str
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    
    def __post_init__(self):
        """Validate report data after initialization."""
        valid_report_types = [
            "usage_summary", "classification_analysis", "user_behavior",
            "performance_metrics", "error_analysis", "trend_analysis"
        ]
        if self.report_type not in valid_report_types:
            raise ValueError(f"Report type must be one of: {valid_report_types}")
        
        valid_formats = ["json", "csv", "pdf", "xlsx"]
        if self.export_format not in valid_formats:
            raise ValueError(f"Export format must be one of: {valid_formats}")
        
        if self.file_size is not None and self.file_size < 0:
            raise ValueError("File size cannot be negative")


@dataclass
class SystemMetrics:
    """
    Dataclass representing real-time system metrics.
    
    Contains performance and health metrics for monitoring.
    """
    timestamp: datetime
    active_requests: int
    requests_per_minute: int
    error_rate: float
    response_times: Dict[str, float]  # p50, p95, p99
    service_status: Dict[str, str]  # service_name -> status
    memory_usage: float
    cpu_usage: float
    
    def __post_init__(self):
        """Validate system metrics after initialization."""
        if self.active_requests < 0:
            raise ValueError("Active requests cannot be negative")
        if self.requests_per_minute < 0:
            raise ValueError("Requests per minute cannot be negative")
        if not (0.0 <= self.error_rate <= 100.0):
            raise ValueError("Error rate must be between 0.0 and 100.0")
        
        # Validate response time percentiles
        required_percentiles = {"p50", "p95", "p99"}
        if not required_percentiles.issubset(self.response_times.keys()):
            raise ValueError("Response times must include p50, p95, and p99")
        
        if any(value < 0 for value in self.response_times.values()):
            raise ValueError("Response time values cannot be negative")
        
        # Validate service status values
        valid_statuses = {"healthy", "warning", "critical", "unknown"}
        if any(status not in valid_statuses for status in self.service_status.values()):
            raise ValueError("Service status must be 'healthy', 'warning', 'critical', or 'unknown'")
        
        if not (0.0 <= self.memory_usage <= 100.0):
            raise ValueError("Memory usage must be between 0.0 and 100.0")
        if not (0.0 <= self.cpu_usage <= 100.0):
            raise ValueError("CPU usage must be between 0.0 and 100.0")


@dataclass
class ReportParameters:
    """
    Dataclass representing parameters for report generation.
    
    Contains configuration for custom report generation.
    """
    report_type: str
    start_date: datetime
    end_date: datetime
    export_format: str
    include_user_details: bool = False
    include_error_details: bool = False
    classification_filter: Optional[JobClassification] = None
    user_filter: Optional[str] = None
    
    def __post_init__(self):
        """Validate report parameters after initialization."""
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        
        # Check date range is reasonable (not more than 1 year)
        max_range = timedelta(days=365)
        if self.end_date - self.start_date > max_range:
            raise ValueError("Date range cannot exceed 365 days")
        
        valid_report_types = [
            "usage_summary", "classification_analysis", "user_behavior",
            "performance_metrics", "error_analysis", "trend_analysis"
        ]
        if self.report_type not in valid_report_types:
            raise ValueError(f"Report type must be one of: {valid_report_types}")
        
        valid_formats = ["json", "csv", "pdf", "xlsx"]
        if self.export_format not in valid_formats:
            raise ValueError(f"Export format must be one of: {valid_formats}")
    
    @property
    def date_range_days(self) -> int:
        """Get the number of days in the date range."""
        return (self.end_date - self.start_date).days


@dataclass
class User:
    """
    Dataclass representing a system user.
    
    Contains user information including credentials and role.
    """
    username: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not isinstance(self.role, UserRole):
            raise ValueError("Role must be a UserRole enum")


@dataclass
class AuthResult:
    """
    Dataclass representing authentication result.
    
    Contains authentication status and user information.
    """
    success: bool
    user: Optional[User] = None
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate auth result data after initialization."""
        if self.success and not self.user:
            raise ValueError("User must be provided for successful authentication")
        # Token is only required for authentication, not user creation
        if self.success and self.token is None and self.user and hasattr(self, '_require_token'):
            raise ValueError("Token must be provided for successful authentication")
        if not self.success and not self.error_message:
            raise ValueError("Error message must be provided for failed authentication")


@dataclass
class TokenValidation:
    """
    Dataclass representing token validation result.
    
    Contains validation status and decoded token information.
    """
    valid: bool
    user: Optional[User] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate token validation data after initialization."""
        if self.valid and not self.user:
            raise ValueError("User must be provided for valid token")
        if not self.valid and not self.error_message:
            raise ValueError("Error message must be provided for invalid token")