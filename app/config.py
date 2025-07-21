"""Configuration management for the Reality Checker application."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""
    
    # Required OpenAI configuration
    openai_api_key: str
    
    # Required Twilio configuration
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    
    # Optional configuration with defaults
    max_pdf_size_mb: int = 10
    openai_model: str = "gpt-4"
    log_level: str = "INFO"
    webhook_validation: bool = True
    
    # Development mode settings
    development_mode: bool = False
    use_mock_twilio: bool = False
    
    # Authentication configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_expiry_hours: int = 24
    jwt_refresh_expiry_days: int = 7
    admin_username: str = "admin"
    admin_password: str = "admin123"
    analyst_username: str = ""
    analyst_password: str = ""
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        # Check for required environment variables
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API key is required",
            "TWILIO_ACCOUNT_SID": "Twilio Account SID is required", 
            "TWILIO_AUTH_TOKEN": "Twilio Auth Token is required",
            "TWILIO_PHONE_NUMBER": "Twilio Phone Number is required"
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"{var}: {description}")
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables:\n" + 
                "\n".join(f"  - {var}" for var in missing_vars)
            )
        
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER"),
            max_pdf_size_mb=int(os.getenv("MAX_PDF_SIZE_MB", "10")),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            webhook_validation=os.getenv("WEBHOOK_VALIDATION", "true").lower() == "true",
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            jwt_expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            jwt_refresh_expiry_days=int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7")),
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password=os.getenv("ADMIN_PASSWORD", "admin123"),
            analyst_username=os.getenv("ANALYST_USERNAME", ""),
            analyst_password=os.getenv("ANALYST_PASSWORD", ""),
            development_mode=os.getenv("DEVELOPMENT_MODE", "false").lower() == "true",
            use_mock_twilio=os.getenv("USE_MOCK_TWILIO", "false").lower() == "true"
        )


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = AppConfig.from_env()
    return config