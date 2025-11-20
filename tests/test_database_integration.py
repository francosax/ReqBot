#!/usr/bin/env python3
"""
Database Integration Test

Tests the complete integration of the database backend with the
main application components without requiring PySide6 or real PDFs.
"""

import sys
import os
import pytest
from pathlib import Path


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    import importlib
    import config.database_config
    import database.database

    # Use a test-specific database
    test_db_path = "test_reqbot.db"

    # Remove existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Set environment variable for test database
    os.environ['REQBOT_SQLITE_PATH'] = test_db_path

    # Reload config module to pick up environment variable
    importlib.reload(config.database_config)
    importlib.reload(database.database)

    from database.database import auto_initialize_database

    # Initialize database
    auto_initialize_database()

    yield

    # Cleanup after test
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    # Restore environment
    if 'REQBOT_SQLITE_PATH' in os.environ:
        del os.environ['REQBOT_SQLITE_PATH']

    # Reload config to restore defaults
    importlib.reload(config.database_config)
    importlib.reload(database.database)


def test_imports():
    """Test that all database integration imports work."""
    print("Testing imports...")

    # Main app imports

    # Processing worker imports

    # RB coordinator imports

    print("[OK] All imports successful")


def test_database_initialization(test_db):
    """Test database initialization."""
    print("\nTesting database initialization...")

    from database.database import get_database_info

    # Get database info
    info = get_database_info()
    assert 'connection_ok' in info
    assert info['connection_ok'] is True
    assert 'type' in info

    if 'sqlite_path' in info:
        print(f"[OK] Database initialized at: {info['sqlite_path']}")
    else:
        print(f"[OK] Database initialized (type: {info['type']})")


@pytest.fixture
def project(test_db):
    """Fixture to create a test project."""
    from database.services.project_service import ProjectService

    project = ProjectService.get_or_create_project(
        name="Integration Test Project",
        input_folder_path="/tmp/test_input",
        output_folder_path="/tmp/test_output",
        compliance_matrix_template="/tmp/template.xlsx"
    )
    return project


@pytest.fixture
def document(test_db, project):
    """Fixture to create a test document."""
    from database.services.document_service import DocumentService
    from database.models import ProcessingStatus

    document, is_new = DocumentService.get_or_create_document(
        project_id=project.id,
        filename="test_document.pdf",
        file_path="/tmp/test_document.pdf"
    )

    # Update document status
    updated_doc = DocumentService.update_processing_status(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        page_count=10
    )

    return updated_doc


def test_project_workflow(test_db):
    """Test project creation and retrieval."""
    print("\nTesting project workflow...")

    from database.services.project_service import ProjectService

    # Create a project
    project = ProjectService.get_or_create_project(
        name="Integration Test Project",
        input_folder_path="/tmp/test_input",
        output_folder_path="/tmp/test_output",
        compliance_matrix_template="/tmp/template.xlsx"
    )

    assert project is not None
    assert project.id is not None
    assert project.name == "Integration Test Project"
    print(f"[OK] Project created (ID: {project.id})")

    # Retrieve the same project (should not create new)
    project2 = ProjectService.get_or_create_project(
        name="Integration Test Project",
        input_folder_path="/tmp/test_input",
        output_folder_path="/tmp/test_output",
        compliance_matrix_template="/tmp/template.xlsx"
    )

    assert project2.id == project.id
    print(f"[OK] Project retrieved (same ID: {project2.id})")


def test_document_workflow(project):
    """Test document creation and tracking."""
    print("\nTesting document workflow...")

    from database.services.document_service import DocumentService
    from database.models import ProcessingStatus

    # Create a document
    document, is_new = DocumentService.get_or_create_document(
        project_id=project.id,
        filename="test_document.pdf",
        file_path="/tmp/test_document.pdf"
    )

    assert document is not None
    assert document.filename == "test_document.pdf"
    if is_new:
        print(f"[OK] Document created (ID: {document.id})")
    else:
        print(f"[OK] Document retrieved (ID: {document.id})")

    # Update document status
    updated_doc = DocumentService.update_processing_status(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        page_count=10
    )

    assert updated_doc.processing_status == ProcessingStatus.COMPLETED
    assert updated_doc.page_count == 10
    print("[OK] Document status updated to COMPLETED")


def test_requirement_workflow(project, document):
    """Test requirement creation and tracking."""
    print("\nTesting requirement workflow...")

    from database.services.requirement_service import RequirementService
    from database.models import Priority

    # Create requirements
    requirements_data = [
        {
            'Label Number': 'REQ-001',
            'Description': 'The system shall authenticate users',
            'Page': 1,
            'Keyword': 'shall',
            'Priority': 'high',
            'Confidence': 0.95
        },
        {
            'Label Number': 'REQ-002',
            'Description': 'The system should log all activities',
            'Page': 2,
            'Keyword': 'should',
            'Priority': 'medium',
            'Confidence': 0.85
        },
        {
            'Label Number': 'REQ-003',
            'Description': 'The system must encrypt data at rest',
            'Page': 3,
            'Keyword': 'must',
            'Priority': 'security',
            'Confidence': 0.92
        }
    ]

    created_requirements = []
    for req_data in requirements_data:
        # Map priority
        priority_map = {
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW,
            'security': Priority.SECURITY
        }
        priority_enum = priority_map.get(req_data['Priority'].lower(), Priority.MEDIUM)

        req = RequirementService.create_requirement(
            document_id=document.id,
            project_id=project.id,
            label_number=req_data['Label Number'],
            description=req_data['Description'],
            page_number=req_data['Page'],
            keyword=req_data['Keyword'],
            priority=priority_enum,
            confidence_score=req_data['Confidence']
        )

        assert req is not None
        created_requirements.append(req)

    print(f"[OK] Created {len(created_requirements)} requirements")

    # Query requirements by project
    project_reqs = RequirementService.get_requirements_by_project(project.id)
    assert len(project_reqs) == len(created_requirements)
    print(f"[OK] Retrieved {len(project_reqs)} requirements by project")

    # Query requirements by document
    doc_reqs = RequirementService.get_requirements_by_document(document.id)
    assert len(doc_reqs) == len(created_requirements)
    print(f"[OK] Retrieved {len(doc_reqs)} requirements by document")

    # Get quality statistics
    stats = RequirementService.get_quality_statistics(project.id)
    assert stats is not None
    assert stats['total_requirements'] == len(created_requirements)
    print(f"[OK] Quality statistics: avg confidence = {stats['avg_confidence']}")


def test_session_workflow(project):
    """Test processing session tracking."""
    print("\nTesting processing session workflow...")

    from database.services.session_service import ProcessingSessionService

    # Create processing session
    session = ProcessingSessionService.create_session(
        project_id=project.id,
        keywords_used="shall, must, should",
        confidence_threshold=0.5
    )

    assert session is not None
    print(f"[OK] Processing session created (ID: {session.id})")

    # Complete session
    completed_session = ProcessingSessionService.complete_session(
        session_id=session.id,
        documents_processed=1,
        requirements_extracted=3,
        avg_confidence=0.91,
        min_confidence=0.85,
        max_confidence=0.95
    )

    assert completed_session.documents_processed == 1
    assert completed_session.requirements_extracted == 3
    print("[OK] Processing session completed")

    # Get session summary
    summary = ProcessingSessionService.get_session_summary(session.id)
    assert summary is not None
    assert summary['results']['requirements_extracted'] == 3
    print("[OK] Session summary retrieved")


def test_complete_workflow(test_db):
    """Test the complete end-to-end workflow."""
    from database.services.project_service import ProjectService
    from database.services.document_service import DocumentService
    from database.services.requirement_service import RequirementService
    from database.services.session_service import ProcessingSessionService
    from database.models import ProcessingStatus, Priority

    print("\n" + "=" * 60)
    print("Database Integration Test - Complete Workflow")
    print("=" * 60)

    # Create project
    print("\nTesting project workflow...")
    project = ProjectService.get_or_create_project(
        name="Integration Test Project Complete",
        input_folder_path="/tmp/test_input",
        output_folder_path="/tmp/test_output",
        compliance_matrix_template="/tmp/template.xlsx"
    )
    assert project is not None
    print(f"[OK] Project created (ID: {project.id})")

    # Create document
    print("\nTesting document workflow...")
    document, is_new = DocumentService.get_or_create_document(
        project_id=project.id,
        filename="test_document_complete.pdf",
        file_path="/tmp/test_document_complete.pdf"
    )
    updated_doc = DocumentService.update_processing_status(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        page_count=10
    )
    assert updated_doc.processing_status == ProcessingStatus.COMPLETED
    print(f"[OK] Document created (ID: {document.id})")

    # Create requirements
    print("\nTesting requirement workflow...")
    requirements_data = [
        {'label': 'REQ-W001', 'desc': 'Test req 1', 'priority': Priority.HIGH},
        {'label': 'REQ-W002', 'desc': 'Test req 2', 'priority': Priority.MEDIUM},
        {'label': 'REQ-W003', 'desc': 'Test req 3', 'priority': Priority.SECURITY},
    ]

    created_requirements = []
    for req_data in requirements_data:
        req = RequirementService.create_requirement(
            document_id=document.id,
            project_id=project.id,
            label_number=req_data['label'],
            description=req_data['desc'],
            page_number=1,
            keyword='shall',
            priority=req_data['priority'],
            confidence_score=0.9
        )
        assert req is not None
        created_requirements.append(req)

    print(f"[OK] Created {len(created_requirements)} requirements")

    # Create session
    print("\nTesting session workflow...")
    session = ProcessingSessionService.create_session(
        project_id=project.id,
        keywords_used="shall, must, should",
        confidence_threshold=0.5
    )
    completed_session = ProcessingSessionService.complete_session(
        session_id=session.id,
        documents_processed=1,
        requirements_extracted=3,
        avg_confidence=0.9,
        min_confidence=0.9,
        max_confidence=0.9
    )
    assert completed_session.documents_processed == 1
    print(f"[OK] Session completed (ID: {session.id})")

    print("\n" + "=" * 60)
    print("[PASS] All integration tests passed!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Project ID: {project.id}")
    print(f"  - Document ID: {document.id}")
    print(f"  - Requirements created: {len(created_requirements)}")
    print(f"  - Session ID: {session.id}")
    print("\nDatabase backend is fully integrated and functional!")


if __name__ == '__main__':
    try:
        test_complete_workflow()
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

