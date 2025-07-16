"""
Database models for the Reality Checker WhatsApp bot (SQLAlchemy 1.4 compatible).

This module contains SQLAlchemy models for persisting user interactions,
analysis results, system metrics, and other application data.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
import enum

from .database import Base
from app.models.data_models import JobClassification, UserRole


# Define enums for database storage
class JobClassificationEnum(enum.Enum):
    """Job classification enumeration for database storage."""
    LEGITIMATE = "legitimate"
    SCAM = "scam"
    SUSPICIOUS = "suspicious"
    UNCLEAR = "unclear"


class UserRoleEnum(enum.Enum):
    """User role enumeration for database storage."""
    ADMIN = "admin"
    VIEWER = "viewer"


class WhatsAppUser(Base):
    """WhatsApp user model for storing user information and statistics."""
    
    __tablename__ = "whatsapp_users"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_interaction = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Statistics
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    avg_response_time = Column(Float, default=0.0, nullable=False)
    
    # Status
    blocked = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    interactions = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_whatsapp_users_phone_number", "phone_number"),
        Index("idx_whatsapp_users_last_interaction", "last_interaction"),
        Index("idx_whatsapp_users_blocked", "blocked"),
        CheckConstraint("total_requests >= 0", name="check_total_requests_non_negative"),
        CheckConstraint("successful_requests >= 0", name="check_successful_requests_non_negative"),
        CheckConstraint("failed_requests >= 0", name="check_failed_requests_non_negative"),
        CheckConstraint("avg_response_time >= 0", name="check_avg_response_time_non_negative"),
    )
    
    @hybrid_property
    def sanitized_phone_number(self) -> str:
        """Return phone number with middle digits masked for privacy."""
        if len(self.phone_number) > 6:
            return self.phone_number[:3] + "*" * (len(self.phone_number) - 6) + self.phone_number[-3:]
        return self.phone_number
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class UserInteraction(Base):
    """User interaction model for storing message exchanges and analysis results."""
    
    __tablename__ = "user_interactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("whatsapp_users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Message information
    message_sid = Column(String(100), unique=True, nullable=False)
    message_type = Column(String(10), nullable=False)  # 'text' or 'pdf'
    message_content = Column(Text, nullable=True)  # Truncated for privacy
    media_url = Column(String(500), nullable=True)
    media_content_type = Column(String(50), nullable=True)
    
    # Analysis results
    trust_score = Column(Float, nullable=True)
    classification = Column(SQLEnum(JobClassificationEnum), nullable=True)
    classification_reasons = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Performance metrics
    response_time = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Error information
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("WhatsAppUser", back_populates="interactions")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_interactions_user_id", "user_id"),
        Index("idx_user_interactions_timestamp", "timestamp"),
        Index("idx_user_interactions_message_sid", "message_sid"),
        Index("idx_user_interactions_classification", "classification"),
        Index("idx_user_interactions_error_type", "error_type"),
        CheckConstraint("trust_score >= 0 AND trust_score <= 1", name="check_trust_score_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
        CheckConstraint("response_time >= 0", name="check_response_time_non_negative"),
        CheckConstraint("processing_time >= 0", name="check_processing_time_non_negative"),
    )


class SystemMetric(Base):
    """System metrics model for storing performance and health data."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # System performance metrics
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    
    # Application metrics
    active_connections = Column(Integer, default=0, nullable=False)
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    
    # Response time metrics
    avg_response_time = Column(Float, default=0.0, nullable=False)
    max_response_time = Column(Float, default=0.0, nullable=False)
    min_response_time = Column(Float, default=0.0, nullable=False)
    
    # External service metrics
    openai_requests = Column(Integer, default=0, nullable=False)
    openai_failures = Column(Integer, default=0, nullable=False)
    openai_avg_response_time = Column(Float, default=0.0, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_system_metrics_timestamp", "timestamp"),
        CheckConstraint("cpu_usage >= 0 AND cpu_usage <= 100", name="check_cpu_usage_range"),
        CheckConstraint("memory_usage >= 0 AND memory_usage <= 100", name="check_memory_usage_range"),
        CheckConstraint("disk_usage >= 0 AND disk_usage <= 100", name="check_disk_usage_range"),
        CheckConstraint("active_connections >= 0", name="check_active_connections_non_negative"),
        CheckConstraint("total_requests >= 0", name="check_total_requests_non_negative"),
        CheckConstraint("successful_requests >= 0", name="check_successful_requests_non_negative"),
        CheckConstraint("failed_requests >= 0", name="check_failed_requests_non_negative"),
    )


class AnalysisHistory(Base):
    """Analysis history model for storing detailed analysis results."""
    
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True)
    interaction_id = Column(Integer, ForeignKey("user_interactions.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Raw analysis data
    raw_text = Column(Text, nullable=True)
    extracted_features = Column(JSON, nullable=True)
    openai_request = Column(JSON, nullable=True)
    openai_response = Column(JSON, nullable=True)
    
    # Analysis metadata
    model_version = Column(String(50), nullable=True)
    processing_duration = Column(Float, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_analysis_history_interaction_id", "interaction_id"),
        Index("idx_analysis_history_timestamp", "timestamp"),
        CheckConstraint("processing_duration >= 0", name="check_processing_duration_non_negative"),
    )


class SystemUser(Base):
    """System user model for admin dashboard authentication."""
    
    __tablename__ = "system_users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRoleEnum), default=UserRoleEnum.VIEWER, nullable=False)
    
    # User metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_system_users_username", "username"),
        Index("idx_system_users_role", "role"),
        Index("idx_system_users_is_active", "is_active"),
    )


class ErrorLog(Base):
    """Error log model for storing application errors and exceptions."""
    
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Error information
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    component = Column(String(50), nullable=False)
    severity = Column(String(10), default="ERROR", nullable=False)
    
    # Context information
    user_id = Column(Integer, ForeignKey("whatsapp_users.id"), nullable=True)
    interaction_id = Column(Integer, ForeignKey("user_interactions.id"), nullable=True)
    stack_trace = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("WhatsAppUser")
    interaction = relationship("UserInteraction")
    
    # Indexes
    __table_args__ = (
        Index("idx_error_logs_timestamp", "timestamp"),
        Index("idx_error_logs_error_type", "error_type"),
        Index("idx_error_logs_component", "component"),
        Index("idx_error_logs_severity", "severity"),
        Index("idx_error_logs_user_id", "user_id"),
    )


class Configuration(Base):
    """Configuration model for storing application settings."""
    
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general", nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_configurations_key", "key"),
        Index("idx_configurations_category", "category"),
    )


class DataRetentionPolicy(Base):
    """Data retention policy model for managing data lifecycle."""
    
    __tablename__ = "data_retention_policies"
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    retention_days = Column(Integer, nullable=False)
    policy_type = Column(String(20), default="delete", nullable=False)  # 'delete' or 'archive'
    date_column = Column(String(50), default="timestamp", nullable=True)
    
    # Status and statistics
    is_active = Column(Boolean, default=True, nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    records_processed = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_data_retention_policies_table_name", "table_name"),
        Index("idx_data_retention_policies_is_active", "is_active"),
        UniqueConstraint("table_name", name="uq_data_retention_policies_table_name"),
        CheckConstraint("retention_days > 0", name="check_retention_days_positive"),
        CheckConstraint("policy_type IN ('delete', 'archive')", name="check_policy_type_valid"),
    )