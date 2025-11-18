#!/usr/bin/env python3
"""
Unit Tests for Database Models

Tests all database models including:
- Model creation
- Relationships
- Constraints
- JSON field handling
- Enum validation
- Timestamps

Requires: SQLAlchemy, pytest
"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Skip all tests if SQLAlchemy not installed
pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import (
    Base, Project, Document, Requirement, RequirementHistory,
    ProcessingSession, KeywordProfile,
    ProcessingStatus, Priority, SessionStatus, ChangeType
)
from database.database import DatabaseSession


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """Create a test session."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


class TestEnums:
    """Test enum definitions."""
    
    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"
        
        # Test that it's a string subclass
        assert isinstance(ProcessingStatus.PENDING, str)
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"
        assert Priority.SECURITY == "security"
    
    def test_session_status_enum(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.RUNNING == "running"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.FAILED == "failed"
        assert SessionStatus.CANCELLED == "cancelled"
    
    def test_change_type_enum(self):
        """Test ChangeType enum values."""
        assert ChangeType.CREATED == "created"
        assert ChangeType.UPDATED == "updated"
        assert ChangeType.DELETED == "deleted"
        assert ChangeType.MERGED == "merged"


class TestProjectModel:
    """Test Project model."""
    
    def test_create_project(self, test_session):
        """Test creating a project."""
        project = Project(
            name="Test Project",
            description="Test description",
            input_folder_path="/input",
            output_folder_path="/output",
            compliance_matrix_template="/template.xlsx"
        )
        
        test_session.add(project)
        test_session.flush()
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.is_active is True
        assert project.created_at is not None
        assert project.updated_at is not None
    
    def test_project_metadata_json_field(self, test_session):
        """Test JSON metadata field handling."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        
        # Set metadata as dict (SQLAlchemy handles JSON conversion)
        project.additional_data = {"key1": "value1", "key2": 123}
        
        test_session.add(project)
        test_session.flush()
        test_session.refresh(project)
        
        # Read back as dict
        assert project.additional_data == {"key1": "value1", "key2": 123}
        assert isinstance(project.additional_data, dict)
    
    def test_project_repr(self, test_session):
        """Test project __repr__ method."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        
        test_session.add(project)
        test_session.flush()
        
        repr_str = repr(project)
        assert "Project" in repr_str
        assert "Test Project" in repr_str


class TestDocumentModel:
    """Test Document model."""
    
    def test_create_document(self, test_session):
        """Test creating a document."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123",
            file_size_bytes=1024,
            page_count=10,
            processing_status=ProcessingStatus.PENDING
        )
        
        test_session.add(doc)
        test_session.flush()
        
        assert doc.id is not None
        assert doc.processing_status == ProcessingStatus.PENDING
        assert doc.filename == "test.pdf"
    
    def test_document_status_enum(self, test_session):
        """Test document status uses enum."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123",
            processing_status=ProcessingStatus.COMPLETED
        )
        
        test_session.add(doc)
        test_session.flush()
        
        assert doc.processing_status == ProcessingStatus.COMPLETED
        assert isinstance(doc.processing_status, ProcessingStatus)
    
    def test_document_project_relationship(self, test_session):
        """Test document-project relationship."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        
        doc = Document(
            project=project,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        
        test_session.add(project)
        test_session.flush()
        
        assert doc in project.documents
        assert doc.project == project


class TestRequirementModel:
    """Test Requirement model."""
    
    def test_create_requirement(self, test_session):
        """Test creating a requirement."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        test_session.add(doc)
        test_session.flush()
        
        req = Requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="The system shall perform X",
            page_number=1,
            keyword="shall",
            priority=Priority.HIGH,
            confidence_score=0.85
        )
        
        test_session.add(req)
        test_session.flush()
        
        assert req.id is not None
        assert req.priority == Priority.HIGH
        assert req.confidence_score == 0.85
    
    def test_requirement_priority_enum(self, test_session):
        """Test requirement priority uses enum."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        test_session.add(doc)
        test_session.flush()
        
        req = Requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="Security requirement",
            page_number=1,
            priority=Priority.SECURITY
        )
        
        test_session.add(req)
        test_session.flush()
        
        assert req.priority == Priority.SECURITY
        assert isinstance(req.priority, Priority)


class TestRequirementHistoryModel:
    """Test RequirementHistory model."""
    
    def test_create_history_record(self, test_session):
        """Test creating a history record."""
        # Create project, document, and requirement
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        test_session.add(doc)
        test_session.flush()
        
        req = Requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="Original description",
            page_number=1,
            priority=Priority.HIGH
        )
        test_session.add(req)
        test_session.flush()
        
        # Create history record
        history = RequirementHistory(
            requirement_id=req.id,
            version=1,
            description="Original description",
            priority=Priority.HIGH,
            change_type=ChangeType.CREATED,
            change_description="Initial extraction"
        )
        
        test_session.add(history)
        test_session.flush()
        
        assert history.id is not None
        assert history.change_type == ChangeType.CREATED
        assert history.version == 1
    
    def test_history_snapshot_data_json(self, test_session):
        """Test history snapshot_data JSON field."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        test_session.add(doc)
        test_session.flush()
        
        req = Requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="Test",
            page_number=1
        )
        test_session.add(req)
        test_session.flush()
        
        history = RequirementHistory(
            requirement_id=req.id,
            version=1,
            description="Test",
            change_type=ChangeType.CREATED
        )
        
        # Set snapshot data as dict
        history.snapshot_data = {
            "old_description": "Original",
            "new_description": "Updated",
            "changed_fields": ["description"]
        }
        
        test_session.add(history)
        test_session.flush()
        test_session.refresh(history)
        
        assert history.snapshot_data["old_description"] == "Original"
        assert isinstance(history.snapshot_data, dict)


class TestProcessingSessionModel:
    """Test ProcessingSession model."""
    
    def test_create_session(self, test_session):
        """Test creating a processing session."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        proc_session = ProcessingSession(
            project_id=project.id,
            status=SessionStatus.RUNNING,
            keywords_used="shall,must,should",
            confidence_threshold=0.5,
            documents_processed=0,
            requirements_extracted=0
        )
        
        test_session.add(proc_session)
        test_session.flush()
        
        assert proc_session.id is not None
        assert proc_session.status == SessionStatus.RUNNING
    
    def test_session_json_fields(self, test_session):
        """Test session JSON list fields."""
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        proc_session = ProcessingSession(
            project_id=project.id,
            status=SessionStatus.COMPLETED
        )
        
        # Set JSON list fields
        proc_session.pdf_output_paths = ["/out/file1.pdf", "/out/file2.pdf"]
        proc_session.warnings = ["Warning 1", "Warning 2"]
        proc_session.errors = ["Error 1"]
        proc_session.additional_data = {"custom_key": "custom_value"}
        
        test_session.add(proc_session)
        test_session.flush()
        test_session.refresh(proc_session)
        
        assert len(proc_session.pdf_output_paths) == 2
        assert proc_session.pdf_output_paths[0] == "/out/file1.pdf"
        assert len(proc_session.warnings) == 2
        assert len(proc_session.errors) == 1
        assert proc_session.additional_data["custom_key"] == "custom_value"


class TestKeywordProfileModel:
    """Test KeywordProfile model."""
    
    def test_create_keyword_profile(self, test_session):
        """Test creating a keyword profile."""
        profile = KeywordProfile(
            name="Standard",
            description="Standard requirement keywords",
            keywords=["shall", "must", "should"],
            is_predefined=True
        )
        
        test_session.add(profile)
        test_session.flush()
        
        assert profile.id is not None
        assert len(profile.keywords) == 3
        assert "shall" in profile.keywords
    
    def test_keyword_profile_unique_name(self, test_session):
        """Test that profile names are unique."""
        profile1 = KeywordProfile(
            name="Standard",
            keywords=["shall"]
        )
        
        test_session.add(profile1)
        test_session.flush()
        
        # Try to create duplicate
        profile2 = KeywordProfile(
            name="Standard",
            keywords=["must"]
        )
        
        test_session.add(profile2)
        
        with pytest.raises(Exception):  # Will raise IntegrityError
            test_session.flush()


class TestCascadeDeletes:
    """Test cascade delete behavior."""
    
    def test_delete_project_cascades(self, test_session):
        """Test that deleting project cascades to documents and requirements."""
        # Create project with document and requirement
        project = Project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output"
        )
        test_session.add(project)
        test_session.flush()
        
        doc = Document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123"
        )
        test_session.add(doc)
        test_session.flush()
        
        req = Requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="Test",
            page_number=1
        )
        test_session.add(req)
        test_session.flush()
        
        doc_id = doc.id
        req_id = req.id
        
        # Delete project
        test_session.delete(project)
        test_session.flush()
        
        # Verify document and requirement are also deleted
        assert test_session.query(Document).filter_by(id=doc_id).first() is None
        assert test_session.query(Requirement).filter_by(id=req_id).first() is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
