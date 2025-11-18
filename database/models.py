"""
SQLAlchemy Models for ReqBot v3.0

This module defines all database models using SQLAlchemy ORM.
Supports both SQLite and PostgreSQL databases.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum
import logging

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON, Index, UniqueConstraint, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

# Logger for this module
logger = logging.getLogger(__name__)


# ============================================================================
# Enums for Type Safety
# ============================================================================

class ProcessingStatus(str, PyEnum):
    """Document processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(str, PyEnum):
    """Requirement priority enum."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SECURITY = "security"


class SessionStatus(str, PyEnum):
    """Processing session status enum."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChangeType(str, PyEnum):
    """Requirement change type enum."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    MERGED = "merged"


# ============================================================================
# Base Model
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# ============================================================================
# Project Model
# ============================================================================

class Project(Base):
    """
    Represents a ReqBot processing project.

    A project groups together related documents and their requirements,
    typically corresponding to a specification set or document collection.
    """
    __tablename__ = 'projects'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Project Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Paths
    input_folder_path: Mapped[str] = mapped_column(String(500), nullable=False)
    output_folder_path: Mapped[str] = mapped_column(String(500), nullable=False)
    compliance_matrix_template: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Additional Data (flexible JSON field for additional settings)
    # Note: 'metadata' is reserved by SQLAlchemy, so we use 'additional_data'
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    requirements: Mapped[List["Requirement"]] = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    processing_sessions: Mapped[List["ProcessingSession"]] = relationship("ProcessingSession", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_projects_created_at', 'created_at'),
        Index('ix_projects_is_active', 'is_active'),
        Index('ix_projects_name', 'name'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


# ============================================================================
# Document Model
# ============================================================================

class Document(Base):
    """
    Represents a source PDF document.

    Tracks individual PDF files and their processing status.
    """
    __tablename__ = 'documents'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Document Information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # MD5 or SHA256
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing Status
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Additional Data
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    requirements: Mapped[List["Requirement"]] = relationship("Requirement", back_populates="document", cascade="all, delete-orphan")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint('project_id', 'file_hash', name='uix_project_file_hash'),
        Index('ix_documents_project_id', 'project_id'),
        Index('ix_documents_file_hash', 'file_hash'),
        Index('ix_documents_processing_status', 'processing_status'),
        Index('ix_documents_processed_at', 'processed_at'),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"


# ============================================================================
# Requirement Model
# ============================================================================

class Requirement(Base):
    """
    Core model for extracted requirements.

    Stores individual requirements extracted from documents with full
    metadata including classification, quality metrics, and versioning.
    """
    __tablename__ = 'requirements'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Requirement Identification
    label_number: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "spec-Req#1-1"

    # Requirement Content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original extracted text

    # Location
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Classification
    keyword: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Matching keyword
    priority: Mapped[Optional[Priority]] = mapped_column(
        Enum(Priority),
        nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Functional, Safety, etc.

    # Quality Metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 to 1.0

    # Processing Info
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(100), default='spacy_nlp', nullable=False)

    # Version Control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_requirement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('requirements.id', ondelete='SET NULL'), nullable=True)

    # User Modifications
    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional Data
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="requirements")
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
    parent_requirement: Mapped[Optional["Requirement"]] = relationship("Requirement", remote_side=[id], backref="child_requirements")
    history: Mapped[List["RequirementHistory"]] = relationship("RequirementHistory", back_populates="requirement", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_requirements_document_id', 'document_id'),
        Index('ix_requirements_project_id', 'project_id'),
        Index('ix_requirements_is_current', 'is_current'),
        Index('ix_requirements_confidence_score', 'confidence_score'),
        Index('ix_requirements_priority', 'priority'),
        Index('ix_requirements_category', 'category'),
        Index('ix_requirements_extracted_at', 'extracted_at'),
        Index('ix_requirements_label_number', 'label_number'),
    )

    def __repr__(self):
        return f"<Requirement(id={self.id}, label='{self.label_number}', priority='{self.priority}')>"


# ============================================================================
# Requirement History Model
# ============================================================================

class RequirementHistory(Base):
    """
    Tracks all changes to requirements (version history).

    Creates a complete audit trail of requirement modifications.
    """
    __tablename__ = 'requirement_history'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False)

    # Version Info
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot of requirement at this version
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Optional[Priority]] = mapped_column(
        Enum(Priority),
        nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Change Tracking
    change_type: Mapped[ChangeType] = mapped_column(
        Enum(ChangeType),
        nullable=False
    )
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Future: user ID
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Full Snapshot (stores complete requirement state)
    snapshot_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="history")

    # Indexes
    __table_args__ = (
        Index('ix_requirement_history_requirement_id', 'requirement_id'),
        Index('ix_requirement_history_changed_at', 'changed_at'),
        Index('ix_requirement_history_version', 'version'),
    )

    def __repr__(self):
        return f"<RequirementHistory(id={self.id}, req_id={self.requirement_id}, v{self.version}, type='{self.change_type}')>"


# ============================================================================
# Processing Session Model
# ============================================================================

class ProcessingSession(Base):
    """
    Tracks each processing run for auditing and reporting.

    Records complete information about each time ReqBot processes documents.
    """
    __tablename__ = 'processing_sessions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Session Info
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.RUNNING,
        nullable=False
    )

    # Configuration
    keywords_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated
    keyword_profile: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Results
    documents_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requirements_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Quality Metrics
    avg_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Outputs
    excel_output_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    basil_output_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_output_paths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    report_output_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Performance
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Issues
    warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Additional Data
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="processing_sessions")

    # Indexes
    __table_args__ = (
        Index('ix_processing_sessions_project_id', 'project_id'),
        Index('ix_processing_sessions_started_at', 'started_at'),
        Index('ix_processing_sessions_status', 'status'),
    )

    def __repr__(self):
        return f"<ProcessingSession(id={self.id}, project_id={self.project_id}, status='{self.status}')>"


# ============================================================================
# Keyword Profile Model
# ============================================================================

class KeywordProfile(Base):
    """
    Stores custom keyword profiles for requirement extraction.

    Note: This may be superseded by the existing keyword_profiles.json
    file-based storage, but provides database option for future use.
    """
    __tablename__ = 'keyword_profiles'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Profile Information
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Keywords (JSON array)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False)

    # Profile Type
    is_predefined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('ix_keyword_profiles_name', 'name'),
    )

    def __repr__(self):
        return f"<KeywordProfile(id={self.id}, name='{self.name}')>"
