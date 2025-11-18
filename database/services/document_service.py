"""
Document Service - Business logic for Document management

Handles operations related to PDF documents including creation, tracking
processing status, and duplicate detection via file hashing.
"""

import logging
import hashlib
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import Document
from database.database import DatabaseSession

logger = logging.getLogger(__name__)


class DocumentService:
    """Service class for Document-related operations."""

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Calculate MD5 hash of a file for change detection.

        Args:
            file_path: Path to file

        Returns:
            str: MD5 hash string
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    @staticmethod
    def create_document(
        project_id: int,
        filename: str,
        file_path: str,
        file_hash: Optional[str] = None,
        page_count: Optional[int] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None
    ) -> Optional[Document]:
        """
        Create a new document record.

        Args:
            project_id: ID of parent project
            filename: Document filename
            file_path: Full path to document
            file_hash: File hash (calculated if not provided)
            page_count: Number of pages (optional)
            metadata: Additional metadata dict (optional)
            session: Database session (optional)

        Returns:
            Document: Created document or None if failed
        """
        def _create(session: Session) -> Document:
            # Calculate hash if not provided
            if file_hash is None:
                computed_hash = DocumentService.calculate_file_hash(file_path)
            else:
                computed_hash = file_hash

            # Get file size
            file_size = None
            try:
                file_size = Path(file_path).stat().st_size
            except:
                pass

            doc = Document(
                project_id=project_id,
                filename=filename,
                file_path=file_path,
                file_hash=computed_hash,
                file_size_bytes=file_size,
                page_count=page_count,
                processing_status='pending'
            )

            if metadata:
                doc.metadata = metadata

            session.add(doc)
            session.flush()
            logger.info(f"Created document: {filename} (ID: {doc.id})")
            return doc

        try:
            if session:
                return _create(session)
            else:
                with DatabaseSession() as session:
                    return _create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to create document '{filename}': {e}")
            return None

    @staticmethod
    def get_or_create_document(
        project_id: int,
        filename: str,
        file_path: str,
        session: Optional[Session] = None
    ) -> tuple[Optional[Document], bool]:
        """
        Get existing document or create new one.

        Checks if document with same file hash already exists in project.
        If found and hash matches, returns existing document.
        If hash differs, updates the document.

        Args:
            project_id: Project ID
            filename: Document filename
            file_path: Full path to document
            session: Database session (optional)

        Returns:
            tuple: (Document, is_new) where is_new indicates if document was created
        """
        def _get_or_create(session: Session) -> tuple[Document, bool]:
            # Calculate current file hash
            current_hash = DocumentService.calculate_file_hash(file_path)

            # Check if document exists by filename
            existing_doc = session.query(Document).filter(
                Document.project_id == project_id,
                Document.filename == filename
            ).first()

            if existing_doc:
                # Check if file has changed
                if existing_doc.file_hash == current_hash:
                    logger.info(f"Document {filename} unchanged (hash match)")
                    return existing_doc, False
                else:
                    # File changed - update hash and reset status
                    logger.info(f"Document {filename} changed (hash mismatch)")
                    existing_doc.file_hash = current_hash
                    existing_doc.file_path = file_path
                    existing_doc.processing_status = 'pending'
                    existing_doc.processed_at = None
                    existing_doc.updated_at = datetime.now()

                    # Update file size
                    try:
                        existing_doc.file_size_bytes = Path(file_path).stat().st_size
                    except:
                        pass

                    session.flush()
                    return existing_doc, False

            # Create new document
            doc = DocumentService.create_document(
                project_id=project_id,
                filename=filename,
                file_path=file_path,
                file_hash=current_hash,
                session=session
            )
            return doc, True

        try:
            if session:
                return _get_or_create(session)
            else:
                with DatabaseSession() as session:
                    return _get_or_create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get or create document '{filename}': {e}")
            return None, False

    @staticmethod
    def update_processing_status(
        document_id: int,
        status: str,
        page_count: Optional[int] = None,
        session: Optional[Session] = None
    ) -> Optional[Document]:
        """
        Update document processing status.

        Args:
            document_id: Document ID
            status: New status (pending, processing, completed, failed)
            page_count: Number of pages (optional)
            session: Database session (optional)

        Returns:
            Document: Updated document or None if failed
        """
        def _update(session: Session) -> Optional[Document]:
            doc = session.query(Document).filter(Document.id == document_id).first()

            if not doc:
                logger.warning(f"Document {document_id} not found for status update")
                return None

            doc.processing_status = status
            doc.updated_at = datetime.now()

            if status == 'completed':
                doc.processed_at = datetime.now()

            if page_count is not None:
                doc.page_count = page_count

            session.flush()
            logger.info(f"Updated document {document_id} status to: {status}")
            return doc

        try:
            if session:
                return _update(session)
            else:
                with DatabaseSession() as session:
                    return _update(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update document {document_id} status: {e}")
            return None

    @staticmethod
    def get_document_by_id(document_id: int, session: Optional[Session] = None) -> Optional[Document]:
        """Get a document by its ID."""
        def _get(session: Session) -> Optional[Document]:
            return session.query(Document).filter(Document.id == document_id).first()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    @staticmethod
    def get_documents_by_project(
        project_id: int,
        status: Optional[str] = None,
        session: Optional[Session] = None
    ) -> List[Document]:
        """
        Get all documents for a project.

        Args:
            project_id: Project ID
            status: Filter by status (optional)
            session: Database session (optional)

        Returns:
            List[Document]: List of documents
        """
        def _get(session: Session) -> List[Document]:
            query = session.query(Document).filter(Document.project_id == project_id)

            if status:
                query = query.filter(Document.processing_status == status)

            return query.order_by(Document.created_at).all()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get documents for project {project_id}: {e}")
            return []

    @staticmethod
    def should_process_document(
        project_id: int,
        filename: str,
        file_path: str,
        session: Optional[Session] = None
    ) -> bool:
        """
        Check if a document should be processed.

        Returns True if:
        - Document doesn't exist in database
        - Document exists but file hash changed

        Args:
            project_id: Project ID
            filename: Document filename
            file_path: Full path to document
            session: Database session (optional)

        Returns:
            bool: True if document should be processed
        """
        def _should_process(session: Session) -> bool:
            # Calculate current hash
            current_hash = DocumentService.calculate_file_hash(file_path)

            # Check if document exists
            existing_doc = session.query(Document).filter(
                Document.project_id == project_id,
                Document.filename == filename
            ).first()

            if not existing_doc:
                logger.info(f"Document {filename} is new - should process")
                return True

            if existing_doc.file_hash != current_hash:
                logger.info(f"Document {filename} has changed - should process")
                return True

            if existing_doc.processing_status == 'failed':
                logger.info(f"Document {filename} previously failed - should reprocess")
                return True

            logger.info(f"Document {filename} unchanged - skip processing")
            return False

        try:
            if session:
                return _should_process(session)
            else:
                with DatabaseSession() as session:
                    return _should_process(session)
        except SQLAlchemyError as e:
            logger.error(f"Error checking if should process {filename}: {e}")
            return True  # Default to processing on error

    @staticmethod
    def delete_document(document_id: int, session: Optional[Session] = None) -> bool:
        """
        Delete a document and all its requirements.

        Args:
            document_id: Document ID
            session: Database session (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        def _delete(session: Session) -> bool:
            doc = session.query(Document).filter(Document.id == document_id).first()

            if not doc:
                logger.warning(f"Document {document_id} not found for deletion")
                return False

            session.delete(doc)
            session.flush()
            logger.warning(f"Deleted document {document_id} and all its requirements")
            return True

        try:
            if session:
                return _delete(session)
            else:
                with DatabaseSession() as session:
                    return _delete(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
