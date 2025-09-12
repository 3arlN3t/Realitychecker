"""
Database models for the Reality Checker WhatsApp bot.

This module contains SQLAlchemy models for persisting user interactions,
analysis results, system metrics, and other application data.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
import enum

from ..database import Base
from app.models.data_models import JobClassification, UserRole


class JobClassificationEnum(enum.Enum):
    """Enum for job classification in database."""
    LEGIT = "Legit"
    SUSPICIOUS = "Suspicious"
    LIKELY_SCAM = "Likely Scam"


class UserRoleEnum(enum.Enum):
    """Enum for user roles in database."""
    ADMIN = "admin"
    ANALYST = "analyst"


class WhatsAppUser(Base):
    """
    WhatsApp user model for storing user information and interaction history.
    
    Stores user details, interaction counts, and management status.
    """
    __tablename__ = "whatsapp_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_interaction: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    last_interaction: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Calculated fields
    successful_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    interactions: Mapped[List["UserInteraction"]] = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_phone_number', 'phone_number'),
        Index('idx_last_interaction', 'last_interaction'),
        Index('idx_blocked', 'blocked'),
        Index('idx_total_requests', 'total_requests'),
        CheckConstraint('total_requests >= 0', name='check_total_requests_non_negative'),
        CheckConstraint('successful_requests >= 0', name='check_successful_requests_non_negative'),
        CheckConstraint('failed_requests >= 0', name='check_failed_requests_non_negative'),
        CheckConstraint('avg_response_time >= 0', name='check_avg_response_time_non_negative'),
    )
    
    @hybrid_property
    def sanitized_phone_number(self) -> str:
        """Get sanitized phone number for logging."""
        if len(self.phone_number) > 15:
            return self.phone_number[:12] + "***"
        return self.phone_number
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @hybrid_property
    def days_since_last_interaction(self) -> int:
        """Calculate days since last interaction."""
        return (datetime.now(timezone.utc) - self.last_interaction).days
    
    def __repr__(self) -> str:
        return f"<WhatsAppUser(phone_number='{self.sanitized_phone_number}', total_requests={self.total_requests})>"


class UserInteraction(Base):
    """
    User interaction model for storing individual message exchanges.
    
    Stores interaction details, analysis results, and performance metrics.
    """
    __tablename__ = "user_interactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("whatsapp_users.id"), nullable=False)
    message_sid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Message details
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'text' or 'pdf'
    message_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media_content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Analysis results
    trust_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    classification: Mapped[Optional[JobClassificationEnum]] = mapped_column(SQLEnum(JobClassificationEnum), nullable=True)
    classification_reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Performance metrics
    response_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    processing_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Error handling
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["WhatsAppUser"] = relationship("WhatsAppUser", back_populates="interactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_timestamp', 'timestamp'),
        Index('idx_message_type', 'message_type'),
        Index('idx_classification', 'classification'),
        Index('idx_trust_score', 'trust_score'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        CheckConstraint('trust_score >= 0 AND trust_score <= 100', name='check_trust_score_range'),
        CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_confidence_range'),
        CheckConstraint('response_time >= 0', name='check_response_time_non_negative'),
        CheckConstraint('processing_time >= 0', name='check_processing_time_non_negative'),
    )
    
    @hybrid_property
    def was_successful(self) -> bool:
        """Check if the interaction was processed successfully."""
        return self.error_type is None and self.trust_score is not None
    
    @hybrid_property
    def classification_text(self) -> Optional[str]:
        """Get classification as text."""
        return self.classification.value if self.classification else None
    
    def __repr__(self) -> str:
        return f"<UserInteraction(message_sid='{self.message_sid}', type='{self.message_type}', successful={self.was_successful})>"


class SystemMetric(Base):
    """
    System metrics model for storing performance and health metrics.
    
    Stores real-time system metrics for monitoring and alerting.
    """
    __tablename__ = "system_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Metrics data
    active_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Response time percentiles
    response_time_p50: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    response_time_p95: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    response_time_p99: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # System resources
    memory_usage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Service status (JSON field)
    service_status: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_error_rate', 'error_rate'),
        Index('idx_memory_usage', 'memory_usage'),
        Index('idx_cpu_usage', 'cpu_usage'),
        CheckConstraint('active_requests >= 0', name='check_active_requests_non_negative'),
        CheckConstraint('requests_per_minute >= 0', name='check_requests_per_minute_non_negative'),
        CheckConstraint('error_rate >= 0.0 AND error_rate <= 100.0', name='check_error_rate_range'),
        CheckConstraint('memory_usage >= 0.0 AND memory_usage <= 100.0', name='check_memory_usage_range'),
        CheckConstraint('cpu_usage >= 0.0 AND cpu_usage <= 100.0', name='check_cpu_usage_range'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemMetric(timestamp='{self.timestamp}', error_rate={self.error_rate}%)>"


class AnalysisHistory(Base):
    """
    Analysis history model for storing aggregated analysis results.
    
    Stores daily/hourly aggregated analysis statistics for reporting.
    """
    __tablename__ = "analysis_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Time period
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'hour' or 'day'
    
    # Analysis counts
    total_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Classification breakdown
    legit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suspicious_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scam_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    avg_response_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # User statistics
    unique_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_date_period', 'date', 'period_type'),
        Index('idx_date', 'date'),
        Index('idx_period_type', 'period_type'),
        UniqueConstraint('date', 'period_type', name='uq_date_period'),
        CheckConstraint('total_analyses >= 0', name='check_total_analyses_non_negative'),
        CheckConstraint('successful_analyses >= 0', name='check_successful_analyses_non_negative'),
        CheckConstraint('failed_analyses >= 0', name='check_failed_analyses_non_negative'),
        CheckConstraint('legit_count >= 0', name='check_legit_count_non_negative'),
        CheckConstraint('suspicious_count >= 0', name='check_suspicious_count_non_negative'),
        CheckConstraint('scam_count >= 0', name='check_scam_count_non_negative'),
        CheckConstraint('avg_response_time >= 0', name='check_avg_response_time_non_negative'),
        CheckConstraint('avg_trust_score >= 0 AND avg_trust_score <= 100', name='check_avg_trust_score_range'),
        CheckConstraint('unique_users >= 0', name='check_unique_users_non_negative'),
        CheckConstraint('new_users >= 0', name='check_new_users_non_negative'),
    )
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_analyses == 0:
            return 0.0
        return (self.successful_analyses / self.total_analyses) * 100
    
    def __repr__(self) -> str:
        return f"<AnalysisHistory(date='{self.date}', period='{self.period_type}', total={self.total_analyses})>"


class SystemUser(Base):
    """
    System user model for dashboard authentication.
    
    Stores user credentials and role information for dashboard access.
    """
    __tablename__ = "system_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(SQLEnum(UserRoleEnum), nullable=False)
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_role', 'role'),
        Index('idx_is_active', 'is_active'),
        Index('idx_last_login', 'last_login'),
        CheckConstraint('login_attempts >= 0', name='check_login_attempts_non_negative'),
    )
    
    @hybrid_property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        return self.locked_until is not None and self.locked_until > datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return f"<SystemUser(username='{self.username}', role='{self.role.value}', active={self.is_active})>"


class ErrorLog(Base):
    """
    Error log model for storing application errors and exceptions.
    
    Stores detailed error information for debugging and monitoring.
    """
    __tablename__ = "error_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Error details
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context information
    component: Mapped[str] = mapped_column(String(50), nullable=False)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("whatsapp_users.id"), nullable=True)
    
    # Additional context
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Severity
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="ERROR")
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user: Mapped[Optional["WhatsAppUser"]] = relationship("WhatsAppUser")
    
    # Indexes
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_error_type', 'error_type'),
        Index('idx_component', 'component'),
        Index('idx_severity', 'severity'),
        Index('idx_correlation_id', 'correlation_id'),
        Index('idx_user_id', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<ErrorLog(type='{self.error_type}', component='{self.component}', severity='{self.severity}')>"


class Configuration(Base):
    """
    Configuration model for storing application settings.
    
    Stores key-value configuration pairs for application settings.
    """
    __tablename__ = "configurations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_key', 'key'),
        Index('idx_category', 'category'),
        Index('idx_is_sensitive', 'is_sensitive'),
    )
    
    def __repr__(self) -> str:
        return f"<Configuration(key='{self.key}', category='{self.category}')>"


class DataRetentionPolicy(Base):
    """
    Data retention policy model for managing data lifecycle.
    
    Stores policies for automatic data cleanup and archival.
    """
    __tablename__ = "data_retention_policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Policy details
    policy_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'delete' or 'archive'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Execution tracking
    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    records_affected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_table_name', 'table_name'),
        Index('idx_is_active', 'is_active'),
        Index('idx_last_executed', 'last_executed'),
        UniqueConstraint('table_name', name='uq_table_name'),
        CheckConstraint('retention_days > 0', name='check_retention_days_positive'),
        CheckConstraint('records_affected >= 0', name='check_records_affected_non_negative'),
    )
    
    def __repr__(self) -> str:
        return f"<DataRetentionPolicy(table='{self.table_name}', days={self.retention_days}, active={self.is_active})>"
