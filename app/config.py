"""Configuration management for the Reality Checker application."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class RedisConfig:
    """Redis connection and performance configuration."""
    url: str = "redis://localhost:6379/0"
    pool_size: int = 20
    max_connections: int = 50
    connection_timeout: float = 5.0
    socket_timeout: float = 5.0
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""
    webhook_timeout: float = 2.0
    webhook_acknowledgment_timeout: float = 0.5
    task_queue_max_size: int = 1000
    task_queue_worker_count: int = 5
    task_queue_batch_size: int = 10
    task_processing_timeout: int = 30
    task_retry_attempts: int = 3
    task_retry_backoff: float = 2.0
    monitoring_enabled: bool = True
    alert_threshold_webhook: float = 1.0
    alert_threshold_critical: float = 3.0


@dataclass
class DatabaseConfig:
    """Database connection pool configuration."""
    url: str = "sqlite+aiosqlite:///data/reality_checker.db"
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


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
    bypass_authentication: bool = False
    
    # Authentication configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_expiry_hours: int = 24
    jwt_refresh_expiry_days: int = 7
    admin_username: str = "admin"
    admin_password: str = "admin123"
    analyst_username: str = ""
    analyst_password: str = ""
    
    # Performance and infrastructure configuration
    redis: RedisConfig = None
    performance: PerformanceConfig = None
    database: DatabaseConfig = None
    
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
        
        # Create Redis configuration
        redis_config = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            pool_size=int(os.getenv("REDIS_POOL_SIZE", "20")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            connection_timeout=float(os.getenv("REDIS_CONNECTION_TIMEOUT", "5.0")),
            socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
            retry_attempts=int(os.getenv("REDIS_RETRY_ATTEMPTS", "3")),
            retry_backoff=float(os.getenv("REDIS_RETRY_BACKOFF", "1.0")),
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
            circuit_breaker_threshold=int(os.getenv("REDIS_CIRCUIT_BREAKER_THRESHOLD", "5")),
            circuit_breaker_timeout=int(os.getenv("REDIS_CIRCUIT_BREAKER_TIMEOUT", "60"))
        )
        
        # Create Performance configuration
        performance_config = PerformanceConfig(
            webhook_timeout=float(os.getenv("WEBHOOK_TIMEOUT", "2.0")),
            webhook_acknowledgment_timeout=float(os.getenv("WEBHOOK_ACKNOWLEDGMENT_TIMEOUT", "0.5")),
            task_queue_max_size=int(os.getenv("TASK_QUEUE_MAX_SIZE", "1000")),
            task_queue_worker_count=int(os.getenv("TASK_QUEUE_WORKER_COUNT", "5")),
            task_queue_batch_size=int(os.getenv("TASK_QUEUE_BATCH_SIZE", "10")),
            task_processing_timeout=int(os.getenv("TASK_PROCESSING_TIMEOUT", "30")),
            task_retry_attempts=int(os.getenv("TASK_RETRY_ATTEMPTS", "3")),
            task_retry_backoff=float(os.getenv("TASK_RETRY_BACKOFF", "2.0")),
            monitoring_enabled=os.getenv("PERFORMANCE_MONITORING_ENABLED", "true").lower() == "true",
            alert_threshold_webhook=float(os.getenv("PERFORMANCE_ALERT_THRESHOLD_WEBHOOK", "1.0")),
            alert_threshold_critical=float(os.getenv("PERFORMANCE_ALERT_THRESHOLD_CRITICAL", "3.0"))
        )
        
        # Create Database configuration
        database_config = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/reality_checker.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
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
            use_mock_twilio=os.getenv("USE_MOCK_TWILIO", "false").lower() == "true",
            bypass_authentication=os.getenv("BYPASS_AUTHENTICATION", "false").lower() == "true",
            redis=redis_config,
            performance=performance_config,
            database=database_config
        )


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = AppConfig.from_env()
    return config