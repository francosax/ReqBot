#!/usr/bin/env python3
"""
Unit Tests for Database Services

Tests all service layer functionality including:
- ProjectService
- DocumentService
- RequirementService
- ProcessingSessionService

Requires: SQLAlchemy, pytest
"""

import pytest
from datetime import datetime

# Skip all tests if SQLAlchemy not installed
pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import (
    Base, Project, Document, Requirement,
    ProcessingStatus, Priority, SessionStatus, ChangeType
)
from database.services.project_service import ProjectService
from database.services.document_service import DocumentService
from database.services.requirement_service import RequirementService
from database.services.session_service import ProcessingSessionService


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine."""
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


class TestProjectService:
    """Test ProjectService methods."""
    
    def test_create_project(self, test_session):
        """Test creating a project via service."""
        project = ProjectService.create_project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output",
            description="Test description",
            session=test_session
        )
        
        assert project is not None
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.is_active is True
    
    def test_get_project_by_id(self, test_session):
        """Test getting project by ID."""
        project = ProjectService.create_project(
            name="Test Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        retrieved = ProjectService.get_project_by_id(
            project.id,
            session=test_session
        )
        
        assert retrieved is not None
        assert retrieved.id == project.id
        assert retrieved.name == "Test Project"
    
    def test_get_project_by_name(self, test_session):
        """Test getting project by name."""
        ProjectService.create_project(
            name="Unique Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        retrieved = ProjectService.get_project_by_name(
            "Unique Project",
            session=test_session
        )
        
        assert retrieved is not None
        assert retrieved.name == "Unique Project"
    
    def test_get_or_create_project(self, test_session):
        """Test get or create functionality."""
        # First call creates
        project1 = ProjectService.get_or_create_project(
            name="GetOrCreate Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        assert project1 is not None
        project1_id = project1.id
        
        # Second call retrieves
        project2 = ProjectService.get_or_create_project(
            name="GetOrCreate Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        assert project2.id == project1_id  # Same project
    
    def test_update_project(self, test_session):
        """Test updating a project."""
        project = ProjectService.create_project(
            name="Original Name",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        updated = ProjectService.update_project(
            project_id=project.id,
            name="Updated Name",
            description="New description",
            session=test_session
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "New description"
    
    def test_deactivate_project(self, test_session):
        """Test deactivating a project."""
        project = ProjectService.create_project(
            name="To Deactivate",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        result = ProjectService.deactivate_project(
            project.id,
            session=test_session
        )
        
        assert result is True
        
        # Verify it's deactivated
        updated = ProjectService.get_project_by_id(
            project.id,
            session=test_session
        )
        assert updated.is_active is False


class TestDocumentService:
    """Test DocumentService methods."""
    
    @pytest.fixture
    def test_project(self, test_session):
        """Create a test project."""
        return ProjectService.create_project(
            name="Doc Test Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
    
    def test_create_document(self, test_session, test_project):
        """Test creating a document via service."""
        doc = DocumentService.create_document(
            project_id=test_project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123",
            file_size_bytes=1024,
            page_count=10,
            session=test_session
        )
        
        assert doc is not None
        assert doc.filename == "test.pdf"
        assert doc.processing_status == ProcessingStatus.PENDING
    
    def test_update_processing_status(self, test_session, test_project):
        """Test updating document processing status."""
        doc = DocumentService.create_document(
            project_id=test_project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123",
            session=test_session
        )
        
        updated = DocumentService.update_processing_status(
            document_id=doc.id,
            status=ProcessingStatus.COMPLETED,
            session=test_session
        )
        
        assert updated is not None
        assert updated.processing_status == ProcessingStatus.COMPLETED
        assert updated.processed_at is not None


class TestRequirementService:
    """Test RequirementService methods."""
    
    @pytest.fixture
    def test_project_and_doc(self, test_session):
        """Create test project and document."""
        project = ProjectService.create_project(
            name="Req Test Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
        
        doc = DocumentService.create_document(
            project_id=project.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_hash="abc123",
            session=test_session
        )
        
        return project, doc
    
    def test_create_requirement(self, test_session, test_project_and_doc):
        """Test creating a requirement via service."""
        project, doc = test_project_and_doc
        
        req = RequirementService.create_requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="The system shall perform X",
            page_number=1,
            keyword="shall",
            priority=Priority.HIGH,
            confidence_score=0.85,
            session=test_session
        )
        
        assert req is not None
        assert req.priority == Priority.HIGH
        assert req.confidence_score == 0.85
        assert req.version == 1
    
    def test_update_requirement(self, test_session, test_project_and_doc):
        """Test updating a requirement."""
        project, doc = test_project_and_doc
        
        req = RequirementService.create_requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="Original description",
            page_number=1,
            session=test_session
        )
        
        updated = RequirementService.update_requirement(
            requirement_id=req.id,
            description="Updated description",
            priority=Priority.SECURITY,
            session=test_session
        )
        
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.priority == Priority.SECURITY
        assert updated.is_manually_edited is True
    
    def test_filter_requirements_by_priority(self, test_session, test_project_and_doc):
        """Test filtering requirements by priority."""
        project, doc = test_project_and_doc
        
        # Create requirements with different priorities
        RequirementService.create_requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-1",
            description="High priority req",
            page_number=1,
            priority=Priority.HIGH,
            session=test_session
        )
        
        RequirementService.create_requirement(
            document_id=doc.id,
            project_id=project.id,
            label_number="test-Req#1-2",
            description="Low priority req",
            page_number=1,
            priority=Priority.LOW,
            session=test_session
        )
        
        # Filter by HIGH priority
        high_reqs = RequirementService.filter_requirements(
            project_id=project.id,
            priority=Priority.HIGH,
            session=test_session
        )
        
        assert len(high_reqs) == 1
        assert high_reqs[0].priority == Priority.HIGH


class TestProcessingSessionService:
    """Test ProcessingSessionService methods."""
    
    @pytest.fixture
    def test_project(self, test_session):
        """Create a test project."""
        return ProjectService.create_project(
            name="Session Test Project",
            input_folder_path="/input",
            output_folder_path="/output",
            session=test_session
        )
    
    def test_create_session(self, test_session, test_project):
        """Test creating a processing session."""
        session_obj = ProcessingSessionService.create_session(
            project_id=test_project.id,
            keywords_used="shall,must,should",
            confidence_threshold=0.5,
            session=test_session
        )
        
        assert session_obj is not None
        assert session_obj.status == SessionStatus.RUNNING
        assert session_obj.keywords_used == "shall,must,should"
    
    def test_complete_session(self, test_session, test_project):
        """Test completing a processing session."""
        session_obj = ProcessingSessionService.create_session(
            project_id=test_project.id,
            session=test_session
        )
        
        completed = ProcessingSessionService.complete_session(
            session_id=session_obj.id,
            documents_processed=5,
            requirements_extracted=25,
            session=test_session
        )
        
        assert completed is not None
        assert completed.status == SessionStatus.COMPLETED
        assert completed.documents_processed == 5
        assert completed.requirements_extracted == 25
    
    def test_fail_session(self, test_session, test_project):
        """Test failing a processing session."""
        session_obj = ProcessingSessionService.create_session(
            project_id=test_project.id,
            session=test_session
        )
        
        failed = ProcessingSessionService.fail_session(
            session_id=session_obj.id,
            error_message="Test error",
            session=test_session
        )
        
        assert failed is not None
        assert failed.status == SessionStatus.FAILED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
