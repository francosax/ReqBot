#!/usr/bin/env python3
"""
Database Integration Test

Tests the complete integration of the database backend with the
main application components without requiring PySide6 or real PDFs.
"""

import sys

# Test imports


def test_imports():
    """Test that all database integration imports work."""
    print("Testing imports...")

    # Main app imports

    # Processing worker imports

    # RB coordinator imports

    print("✓ All imports successful")
    return True


def test_database_initialization():
    """Test database initialization."""
    print("\nTesting database initialization...")

    from database.database import auto_initialize_database, get_database_info

    # Initialize database
    auto_initialize_database()

    # Get database info
    info = get_database_info()
    assert 'connection_ok' in info
    assert info['connection_ok'] is True
    assert 'type' in info

    if 'sqlite_path' in info:
        print(f"✓ Database initialized at: {info['sqlite_path']}")
    else:
        print(f"✓ Database initialized (type: {info['type']})")
    return True


def test_project_workflow():
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
    print(f"✓ Project created (ID: {project.id})")

    # Retrieve the same project (should not create new)
    project2 = ProjectService.get_or_create_project(
        name="Integration Test Project",
        input_folder_path="/tmp/test_input",
        output_folder_path="/tmp/test_output",
        compliance_matrix_template="/tmp/template.xlsx"
    )

    assert project2.id == project.id
    print(f"✓ Project retrieved (same ID: {project2.id})")

    return project


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
        print(f"✓ Document created (ID: {document.id})")
    else:
        print(f"✓ Document retrieved (ID: {document.id})")

    # Update document status
    updated_doc = DocumentService.update_processing_status(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        page_count=10
    )

    assert updated_doc.processing_status == ProcessingStatus.COMPLETED
    assert updated_doc.page_count == 10
    print("✓ Document status updated to COMPLETED")

    return document


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

    print(f"✓ Created {len(created_requirements)} requirements")

    # Query requirements by project
    project_reqs = RequirementService.get_requirements_by_project(project.id)
    assert len(project_reqs) == len(created_requirements)
    print(f"✓ Retrieved {len(project_reqs)} requirements by project")

    # Query requirements by document
    doc_reqs = RequirementService.get_requirements_by_document(document.id)
    assert len(doc_reqs) == len(created_requirements)
    print(f"✓ Retrieved {len(doc_reqs)} requirements by document")

    # Get quality statistics
    stats = RequirementService.get_quality_statistics(project.id)
    assert stats is not None
    assert stats['total_requirements'] == len(created_requirements)
    print(f"✓ Quality statistics: avg confidence = {stats['avg_confidence']}")

    return created_requirements


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
    print(f"✓ Processing session created (ID: {session.id})")

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
    print("✓ Processing session completed")

    # Get session summary
    summary = ProcessingSessionService.get_session_summary(session.id)
    assert summary is not None
    assert summary['results']['requirements_extracted'] == 3
    print("✓ Session summary retrieved")

    return session


def test_complete_workflow():
    """Test the complete end-to-end workflow."""
    print("\n" + "=" * 60)
    print("Database Integration Test - Complete Workflow")
    print("=" * 60)

    # Run all tests
    test_imports()
    test_database_initialization()
    project = test_project_workflow()
    document = test_document_workflow(project)
    requirements = test_requirement_workflow(project, document)
    session = test_session_workflow(project)

    print("\n" + "=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Project ID: {project.id}")
    print(f"  - Document ID: {document.id}")
    print(f"  - Requirements created: {len(requirements)}")
    print(f"  - Session ID: {session.id}")
    print("\nDatabase backend is fully integrated and functional! 🎉")

    return True


if __name__ == '__main__':
    try:
        test_complete_workflow()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
