"""
Requirement Service - Business logic for Requirement management

Handles all operations related to requirements including creation, querying,
version history tracking, and quality analysis.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_

from database.models import Requirement, RequirementHistory, Document, Priority, ChangeType
from database.database import DatabaseSession

logger = logging.getLogger(__name__)


class RequirementService:
    """Service class for Requirement-related operations."""

    @staticmethod
    def create_requirement(
        document_id: int,
        project_id: int,
        label_number: str,
        description: str,
        page_number: int,
        keyword: Optional[str] = None,
        priority: Optional[Priority] = None,
        category: Optional[str] = None,
        confidence_score: Optional[float] = None,
        raw_text: Optional[str] = None,
        extraction_method: str = 'spacy_nlp',
        additional_data: Optional[dict] = None,
        session: Optional[Session] = None
    ) -> Optional[Requirement]:
        """
        Create a new requirement.

        Args:
            document_id: ID of parent document
            project_id: ID of parent project
            label_number: Requirement label/identifier
            description: Requirement description text
            page_number: Page number in source document
            keyword: Matching keyword (optional)
            priority: Priority level (Priority enum: HIGH, MEDIUM, LOW, SECURITY)
            category: Category (Functional, Safety, etc.)
            confidence_score: Extraction confidence (0.0-1.0)
            raw_text: Original raw text (optional)
            extraction_method: Method used for extraction
            metadata: Additional metadata dict (optional)
            session: Database session (optional)

        Returns:
            Requirement: Created requirement or None if failed
        """
        def _create(session: Session) -> Requirement:
            req = Requirement(
                document_id=document_id,
                project_id=project_id,
                label_number=label_number,
                description=description,
                page_number=page_number,
                keyword=keyword,
                priority=priority,
                category=category,
                confidence_score=confidence_score,
                raw_text=raw_text,
                extraction_method=extraction_method,
                version=1,
                is_current=True
            )

            if additional_data:
                req.additional_data = additional_data

            session.add(req)
            session.flush()

            # Create initial history record
            RequirementService._create_history_record(
                session=session,
                requirement=req,
                change_type=ChangeType.CREATED,
                change_description='Initial extraction'
            )

            logger.info(f"Created requirement: {label_number} (ID: {req.id})")
            return req

        try:
            if session:
                return _create(session)
            else:
                with DatabaseSession() as session:
                    return _create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to create requirement '{label_number}': {e}")
            return None

    @staticmethod
    def create_requirements_bulk(
        requirements_data: List[dict],
        session: Optional[Session] = None
    ) -> List[Requirement]:
        """
        Create multiple requirements in bulk for better performance.

        Args:
            requirements_data: List of dicts with requirement data
            session: Database session (optional)

        Returns:
            List[Requirement]: Created requirements
        """
        def _create_bulk(session: Session) -> List[Requirement]:
            requirements = []

            for req_data in requirements_data:
                req = Requirement(**req_data)
                session.add(req)
                requirements.append(req)

            session.flush()

            # Create history records for all
            for req in requirements:
                RequirementService._create_history_record(
                    session=session,
                    requirement=req,
                    change_type=ChangeType.CREATED,
                    change_description='Initial extraction'
                )

            logger.info(f"Bulk created {len(requirements)} requirements")
            return requirements

        try:
            if session:
                return _create_bulk(session)
            else:
                with DatabaseSession() as session:
                    return _create_bulk(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to bulk create requirements: {e}")
            return []

    @staticmethod
    def _create_history_record(
        session: Session,
        requirement: Requirement,
        change_type: ChangeType,
        change_description: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> RequirementHistory:
        """
        Create a history record for a requirement.

        Args:
            session: Database session
            requirement: Requirement object
            change_type: Type of change (ChangeType enum)
            change_description: Description of change (optional)
            changed_by: User who made the change (optional)

        Returns:
            RequirementHistory: Created history record
        """
        # Create snapshot of current state
        snapshot_data = {
            'label_number': requirement.label_number,
            'description': requirement.description,
            'page_number': requirement.page_number,
            'keyword': requirement.keyword,
            'priority': requirement.priority,
            'category': requirement.category,
            'confidence_score': requirement.confidence_score,
            'raw_text': requirement.raw_text,
            'extraction_method': requirement.extraction_method,
            'additional_data': requirement.additional_data
        }

        history = RequirementHistory(
            requirement_id=requirement.id,
            version=requirement.version,
            description=requirement.description,
            priority=requirement.priority,
            category=requirement.category,
            confidence_score=requirement.confidence_score,
            change_type=change_type,
            change_description=change_description,
            changed_by=changed_by,
            snapshot_data=snapshot_data
        )

        session.add(history)
        return history

    @staticmethod
    def get_requirement_by_id(requirement_id: int, session: Optional[Session] = None) -> Optional[Requirement]:
        """Get a requirement by its ID."""
        def _get(session: Session) -> Optional[Requirement]:
            return session.query(Requirement).filter(Requirement.id == requirement_id).first()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def get_requirements_by_document(
        document_id: int,
        current_only: bool = True,
        session: Optional[Session] = None
    ) -> List[Requirement]:
        """Get all requirements for a document."""
        def _get(session: Session) -> List[Requirement]:
            query = session.query(Requirement).filter(Requirement.document_id == document_id)
            if current_only:
                query = query.filter(Requirement.is_current == True)
            return query.order_by(Requirement.page_number, Requirement.label_number).all()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get requirements for document {document_id}: {e}")
            return []

    @staticmethod
    def get_requirements_by_project(
        project_id: int,
        current_only: bool = True,
        session: Optional[Session] = None
    ) -> List[Requirement]:
        """Get all requirements for a project."""
        def _get(session: Session) -> List[Requirement]:
            query = session.query(Requirement).filter(Requirement.project_id == project_id)
            if current_only:
                query = query.filter(Requirement.is_current == True)
            return query.order_by(Requirement.label_number).all()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get requirements for project {project_id}: {e}")
            return []

    @staticmethod
    def filter_requirements(
        project_id: Optional[int] = None,
        document_id: Optional[int] = None,
        priority: Optional[Priority] = None,
        category: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        keyword: Optional[str] = None,
        current_only: bool = True,
        session: Optional[Session] = None
    ) -> List[Requirement]:
        """
        Filter requirements by multiple criteria.

        Args:
            project_id: Filter by project
            document_id: Filter by document
            priority: Filter by priority (Priority enum)
            category: Filter by category
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            keyword: Filter by keyword
            current_only: Only return current versions
            session: Database session (optional)

        Returns:
            List[Requirement]: Filtered requirements
        """
        def _filter(session: Session) -> List[Requirement]:
            query = session.query(Requirement)

            if project_id is not None:
                query = query.filter(Requirement.project_id == project_id)
            if document_id is not None:
                query = query.filter(Requirement.document_id == document_id)
            if priority is not None:
                query = query.filter(Requirement.priority == priority)
            if category is not None:
                query = query.filter(Requirement.category == category)
            if min_confidence is not None:
                query = query.filter(Requirement.confidence_score >= min_confidence)
            if max_confidence is not None:
                query = query.filter(Requirement.confidence_score <= max_confidence)
            if keyword is not None:
                query = query.filter(Requirement.keyword == keyword)
            if current_only:
                query = query.filter(Requirement.is_current == True)

            return query.order_by(Requirement.label_number).all()

        try:
            if session:
                return _filter(session)
            else:
                with DatabaseSession() as session:
                    return _filter(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to filter requirements: {e}")
            return []

    @staticmethod
    def update_requirement(
        requirement_id: int,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        category: Optional[str] = None,
        confidence_score: Optional[float] = None,
        is_manually_edited: bool = True,
        changed_by: Optional[str] = None,
        session: Optional[Session] = None
    ) -> Optional[Requirement]:
        """
        Update a requirement and create new version in history.

        Args:
            requirement_id: Requirement ID
            description: New description (optional)
            priority: New priority (Priority enum, optional)
            category: New category (optional)
            confidence_score: New confidence score (optional)
            is_manually_edited: Mark as manually edited
            changed_by: User who made the change (optional)
            session: Database session (optional)

        Returns:
            Requirement: Updated requirement or None if failed
        """
        def _update(session: Session) -> Optional[Requirement]:
            req = session.query(Requirement).filter(Requirement.id == requirement_id).first()

            if not req:
                logger.warning(f"Requirement {requirement_id} not found for update")
                return None

            # Track changes
            changes = []
            if description is not None and description != req.description:
                req.description = description
                changes.append('description')
            if priority is not None and priority != req.priority:
                req.priority = priority
                changes.append('priority')
            if category is not None and category != req.category:
                req.category = category
                changes.append('category')
            if confidence_score is not None and confidence_score != req.confidence_score:
                req.confidence_score = confidence_score
                changes.append('confidence_score')

            if changes:
                # Increment version
                req.version += 1
                req.is_manually_edited = is_manually_edited
                req.edited_at = datetime.now()

                # Create history record
                change_desc = f"Updated: {', '.join(changes)}"
                RequirementService._create_history_record(
                    session=session,
                    requirement=req,
                    change_type=ChangeType.UPDATED,
                    change_description=change_desc,
                    changed_by=changed_by
                )

                session.flush()
                logger.info(f"Updated requirement {requirement_id} (v{req.version}): {change_desc}")

            return req

        try:
            if session:
                return _update(session)
            else:
                with DatabaseSession() as session:
                    return _update(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def get_requirement_history(
        requirement_id: int,
        session: Optional[Session] = None
    ) -> List[RequirementHistory]:
        """
        Get full version history for a requirement.

        Args:
            requirement_id: Requirement ID
            session: Database session (optional)

        Returns:
            List[RequirementHistory]: History records ordered by version
        """
        def _get_history(session: Session) -> List[RequirementHistory]:
            return session.query(RequirementHistory).filter(
                RequirementHistory.requirement_id == requirement_id
            ).order_by(RequirementHistory.version).all()

        try:
            if session:
                return _get_history(session)
            else:
                with DatabaseSession() as session:
                    return _get_history(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get history for requirement {requirement_id}: {e}")
            return []

    @staticmethod
    def get_quality_statistics(
        project_id: int,
        session: Optional[Session] = None
    ) -> Optional[Dict]:
        """
        Get quality statistics for requirements in a project.

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            dict: Quality statistics including avg/min/max confidence, etc.
        """
        def _get_stats(session: Session) -> Optional[Dict]:
            stats = session.query(
                func.count(Requirement.id).label('total_count'),
                func.avg(Requirement.confidence_score).label('avg_confidence'),
                func.min(Requirement.confidence_score).label('min_confidence'),
                func.max(Requirement.confidence_score).label('max_confidence')
            ).filter(
                Requirement.project_id == project_id,
                Requirement.is_current == True
            ).first()

            if not stats or stats.total_count == 0:
                return None

            # Get counts by priority
            priority_counts = session.query(
                Requirement.priority,
                func.count(Requirement.id).label('count')
            ).filter(
                Requirement.project_id == project_id,
                Requirement.is_current == True
            ).group_by(Requirement.priority).all()

            # Get counts by category
            category_counts = session.query(
                Requirement.category,
                func.count(Requirement.id).label('count')
            ).filter(
                Requirement.project_id == project_id,
                Requirement.is_current == True
            ).group_by(Requirement.category).all()

            # Get low confidence count
            low_confidence_count = session.query(func.count(Requirement.id)).filter(
                Requirement.project_id == project_id,
                Requirement.is_current == True,
                Requirement.confidence_score < 0.6
            ).scalar()

            return {
                'total_requirements': stats.total_count,
                'avg_confidence': round(float(stats.avg_confidence), 3) if stats.avg_confidence else None,
                'min_confidence': round(float(stats.min_confidence), 3) if stats.min_confidence else None,
                'max_confidence': round(float(stats.max_confidence), 3) if stats.max_confidence else None,
                'low_confidence_count': low_confidence_count,
                'priority_breakdown': {p: c for p, c in priority_counts if p},
                'category_breakdown': {cat: c for cat, c in category_counts if cat}
            }

        try:
            if session:
                return _get_stats(session)
            else:
                with DatabaseSession() as session:
                    return _get_stats(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get quality statistics for project {project_id}: {e}")
            return None

    @staticmethod
    def search_requirements(
        search_text: str,
        project_id: Optional[int] = None,
        session: Optional[Session] = None
    ) -> List[Requirement]:
        """
        Search requirements by text in description.

        Args:
            search_text: Text to search for
            project_id: Limit search to project (optional)
            session: Database session (optional)

        Returns:
            List[Requirement]: Matching requirements
        """
        def _search(session: Session) -> List[Requirement]:
            query = session.query(Requirement).filter(
                Requirement.description.contains(search_text),
                Requirement.is_current == True
            )

            if project_id is not None:
                query = query.filter(Requirement.project_id == project_id)

            return query.order_by(Requirement.label_number).all()

        try:
            if session:
                return _search(session)
            else:
                with DatabaseSession() as session:
                    return _search(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to search requirements: {e}")
            return []

    @staticmethod
    def delete_requirement(requirement_id: int, session: Optional[Session] = None) -> bool:
        """
        Delete a requirement and its history.

        Args:
            requirement_id: Requirement ID
            session: Database session (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        def _delete(session: Session) -> bool:
            req = session.query(Requirement).filter(Requirement.id == requirement_id).first()

            if not req:
                logger.warning(f"Requirement {requirement_id} not found for deletion")
                return False

            session.delete(req)
            session.flush()
            logger.warning(f"Deleted requirement {requirement_id}")
            return True

        try:
            if session:
                return _delete(session)
            else:
                with DatabaseSession() as session:
                    return _delete(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete requirement {requirement_id}: {e}")
            return False
