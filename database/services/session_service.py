"""
Processing Session Service - Business logic for Processing Session tracking

Handles tracking of processing runs including configuration, results, and metrics.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import ProcessingSession, SessionStatus
from database.database import DatabaseSession

logger = logging.getLogger(__name__)


class ProcessingSessionService:
    """Service class for ProcessingSession-related operations."""

    @staticmethod
    def create_session(
        project_id: int,
        keywords_used: Optional[str] = None,
        keyword_profile: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        additional_data: Optional[dict] = None,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """
        Create a new processing session.

        Args:
            project_id: ID of parent project
            keywords_used: Comma-separated keywords
            keyword_profile: Profile name used (e.g., "Aerospace")
            confidence_threshold: Confidence threshold used
            metadata: Additional metadata dict (optional)
            session: Database session (optional)

        Returns:
            ProcessingSession: Created session or None if failed
        """
        def _create(session: Session) -> ProcessingSession:
            proc_session = ProcessingSession(
                project_id=project_id,
                keywords_used=keywords_used,
                keyword_profile=keyword_profile,
                confidence_threshold=confidence_threshold,
                status=SessionStatus.RUNNING
            )

            if additional_data:
                proc_session.additional_data = additional_data

            session.add(proc_session)
            session.flush()
            logger.info(f"Created processing session: ID {proc_session.id} for project {project_id}")
            return proc_session

        try:
            if session:
                return _create(session)
            else:
                with DatabaseSession() as session:
                    return _create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to create processing session: {e}")
            return None

    @staticmethod
    def complete_session(
        session_id: int,
        documents_processed: int,
        requirements_extracted: int,
        avg_confidence: Optional[float] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        excel_output_path: Optional[str] = None,
        basil_output_path: Optional[str] = None,
        pdf_output_paths: Optional[List[str]] = None,
        report_output_path: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """
        Mark a processing session as completed and record results.

        Args:
            session_id: Processing session ID
            documents_processed: Number of documents processed
            requirements_extracted: Number of requirements extracted
            avg_confidence: Average confidence score
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            excel_output_path: Path to generated Excel file
            basil_output_path: Path to generated BASIL file
            pdf_output_paths: List of paths to generated PDFs
            report_output_path: Path to HTML report
            warnings: List of warning messages
            errors: List of error messages
            session: Database session (optional)

        Returns:
            ProcessingSession: Updated session or None if failed
        """
        def _complete(session: Session) -> Optional[ProcessingSession]:
            proc_session = session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

            if not proc_session:
                logger.warning(f"Processing session {session_id} not found")
                return None

            # Calculate processing time
            if proc_session.started_at:
                processing_time = (datetime.now() - proc_session.started_at).total_seconds()
                proc_session.processing_time_seconds = processing_time

            # Update results
            proc_session.completed_at = datetime.now()
            proc_session.status = SessionStatus.COMPLETED
            proc_session.documents_processed = documents_processed
            proc_session.requirements_extracted = requirements_extracted

            # Update quality metrics
            proc_session.avg_confidence_score = avg_confidence
            proc_session.min_confidence_score = min_confidence
            proc_session.max_confidence_score = max_confidence

            # Update output paths
            proc_session.excel_output_path = excel_output_path
            proc_session.basil_output_path = basil_output_path
            if pdf_output_paths:
                proc_session.pdf_output_paths = pdf_output_paths
            proc_session.report_output_path = report_output_path

            # Update warnings and errors
            if warnings:
                proc_session.warnings = warnings
                proc_session.warnings_count = len(warnings)
            if errors:
                proc_session.errors = errors
                proc_session.errors_count = len(errors)

            session.flush()
            logger.info(f"Completed processing session {session_id}: "
                       f"{requirements_extracted} requirements from {documents_processed} documents")
            return proc_session

        try:
            if session:
                return _complete(session)
            else:
                with DatabaseSession() as session:
                    return _complete(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to complete processing session {session_id}: {e}")
            return None

    @staticmethod
    def fail_session(
        session_id: int,
        error_message: str,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """
        Mark a processing session as failed.

        Args:
            session_id: Processing session ID
            error_message: Error message
            session: Database session (optional)

        Returns:
            ProcessingSession: Updated session or None if failed
        """
        def _fail(session: Session) -> Optional[ProcessingSession]:
            proc_session = session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

            if not proc_session:
                logger.warning(f"Processing session {session_id} not found")
                return None

            proc_session.status = SessionStatus.FAILED
            proc_session.completed_at = datetime.now()
            proc_session.errors = [error_message]
            proc_session.errors_count = 1

            # Calculate processing time
            if proc_session.started_at:
                processing_time = (datetime.now() - proc_session.started_at).total_seconds()
                proc_session.processing_time_seconds = processing_time

            session.flush()
            logger.error(f"Processing session {session_id} failed: {error_message}")
            return proc_session

        try:
            if session:
                return _fail(session)
            else:
                with DatabaseSession() as session:
                    return _fail(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to mark session {session_id} as failed: {e}")
            return None

    @staticmethod
    def cancel_session(
        session_id: int,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """
        Cancel a running processing session.

        Args:
            session_id: Processing session ID
            session: Database session (optional)

        Returns:
            ProcessingSession: Updated session or None if failed
        """
        def _cancel(session: Session) -> Optional[ProcessingSession]:
            proc_session = session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

            if not proc_session:
                logger.warning(f"Processing session {session_id} not found")
                return None

            proc_session.status = SessionStatus.CANCELLED
            proc_session.completed_at = datetime.now()

            # Calculate processing time
            if proc_session.started_at:
                processing_time = (datetime.now() - proc_session.started_at).total_seconds()
                proc_session.processing_time_seconds = processing_time

            session.flush()
            logger.info(f"Cancelled processing session {session_id}")
            return proc_session

        try:
            if session:
                return _cancel(session)
            else:
                with DatabaseSession() as session:
                    return _cancel(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to cancel session {session_id}: {e}")
            return None

    @staticmethod
    def get_session_by_id(
        session_id: int,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """Get a processing session by its ID."""
        def _get(session: Session) -> Optional[ProcessingSession]:
            return session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get processing session {session_id}: {e}")
            return None

    @staticmethod
    def get_sessions_by_project(
        project_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        session: Optional[Session] = None
    ) -> List[ProcessingSession]:
        """
        Get processing sessions for a project.

        Args:
            project_id: Project ID
            status: Filter by status (optional)
            limit: Limit number of results (optional)
            session: Database session (optional)

        Returns:
            List[ProcessingSession]: List of processing sessions
        """
        def _get(session: Session) -> List[ProcessingSession]:
            query = session.query(ProcessingSession).filter(
                ProcessingSession.project_id == project_id
            )

            if status:
                query = query.filter(ProcessingSession.status == status)

            query = query.order_by(ProcessingSession.started_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get sessions for project {project_id}: {e}")
            return []

    @staticmethod
    def get_latest_session(
        project_id: int,
        session: Optional[Session] = None
    ) -> Optional[ProcessingSession]:
        """
        Get the most recent processing session for a project.

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            ProcessingSession: Latest session or None if not found
        """
        def _get_latest(session: Session) -> Optional[ProcessingSession]:
            return session.query(ProcessingSession).filter(
                ProcessingSession.project_id == project_id
            ).order_by(ProcessingSession.started_at.desc()).first()

        try:
            if session:
                return _get_latest(session)
            else:
                with DatabaseSession() as session:
                    return _get_latest(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest session for project {project_id}: {e}")
            return None

    @staticmethod
    def get_session_summary(
        session_id: int,
        session: Optional[Session] = None
    ) -> Optional[Dict]:
        """
        Get a summary of a processing session.

        Args:
            session_id: Processing session ID
            session: Database session (optional)

        Returns:
            dict: Session summary or None if not found
        """
        def _get_summary(session: Session) -> Optional[Dict]:
            proc_session = session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

            if not proc_session:
                return None

            summary = {
                'session_id': proc_session.id,
                'project_id': proc_session.project_id,
                'status': proc_session.status,
                'started_at': proc_session.started_at.isoformat() if proc_session.started_at else None,
                'completed_at': proc_session.completed_at.isoformat() if proc_session.completed_at else None,
                'processing_time_seconds': proc_session.processing_time_seconds,
                'configuration': {
                    'keywords_used': proc_session.keywords_used,
                    'keyword_profile': proc_session.keyword_profile,
                    'confidence_threshold': proc_session.confidence_threshold
                },
                'results': {
                    'documents_processed': proc_session.documents_processed,
                    'requirements_extracted': proc_session.requirements_extracted,
                    'avg_confidence': proc_session.avg_confidence_score,
                    'min_confidence': proc_session.min_confidence_score,
                    'max_confidence': proc_session.max_confidence_score
                },
                'outputs': {
                    'excel': proc_session.excel_output_path,
                    'basil': proc_session.basil_output_path,
                    'pdfs': proc_session.pdf_output_paths,
                    'report': proc_session.report_output_path
                },
                'issues': {
                    'warnings_count': proc_session.warnings_count,
                    'errors_count': proc_session.errors_count,
                    'warnings': proc_session.warnings,
                    'errors': proc_session.errors
                }
            }

            return summary

        try:
            if session:
                return _get_summary(session)
            else:
                with DatabaseSession() as session:
                    return _get_summary(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get summary for session {session_id}: {e}")
            return None

    @staticmethod
    def delete_session(session_id: int, session: Optional[Session] = None) -> bool:
        """
        Delete a processing session.

        Args:
            session_id: Processing session ID
            session: Database session (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        def _delete(session: Session) -> bool:
            proc_session = session.query(ProcessingSession).filter(
                ProcessingSession.id == session_id
            ).first()

            if not proc_session:
                logger.warning(f"Processing session {session_id} not found for deletion")
                return False

            session.delete(proc_session)
            session.flush()
            logger.warning(f"Deleted processing session {session_id}")
            return True

        try:
            if session:
                return _delete(session)
            else:
                with DatabaseSession() as session:
                    return _delete(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete processing session {session_id}: {e}")
            return False
