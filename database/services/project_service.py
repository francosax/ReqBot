"""
Project Service - Business logic for Project management

Handles all operations related to ReqBot projects including creation,
retrieval, updates, and deletion.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import Project
from database.database import DatabaseSession

logger = logging.getLogger(__name__)


class ProjectService:
    """Service class for Project-related operations."""

    @staticmethod
    def create_project(
        name: str,
        input_folder_path: str,
        output_folder_path: str,
        compliance_matrix_template: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None
    ) -> Optional[Project]:
        """
        Create a new project.

        Args:
            name: Project name
            input_folder_path: Path to input folder containing PDFs
            output_folder_path: Path to output folder for results
            compliance_matrix_template: Path to Excel template (optional)
            description: Project description (optional)
            metadata: Additional metadata dict (optional)
            session: Database session (optional, creates new if None)

        Returns:
            Project: Created project object, or None if failed
        """
        def _create(session: Session) -> Project:
            project = Project(
                name=name,
                description=description,
                input_folder_path=input_folder_path,
                output_folder_path=output_folder_path,
                compliance_matrix_template=compliance_matrix_template
            )

            if metadata:
                project.metadata = metadata

            session.add(project)
            session.flush()  # Get the ID without committing
            logger.info(f"Created project: {project.name} (ID: {project.id})")
            return project

        try:
            if session:
                return _create(session)
            else:
                with DatabaseSession() as session:
                    return _create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to create project '{name}': {e}")
            return None

    @staticmethod
    def get_project_by_id(project_id: int, session: Optional[Session] = None) -> Optional[Project]:
        """
        Get a project by its ID.

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            Project: Project object or None if not found
        """
        def _get(session: Session) -> Optional[Project]:
            return session.query(Project).filter(Project.id == project_id).first()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    @staticmethod
    def get_project_by_name(name: str, session: Optional[Session] = None) -> Optional[Project]:
        """
        Get a project by its name.

        Args:
            name: Project name
            session: Database session (optional)

        Returns:
            Project: Project object or None if not found
        """
        def _get(session: Session) -> Optional[Project]:
            return session.query(Project).filter(Project.name == name).first()

        try:
            if session:
                return _get(session)
            else:
                with DatabaseSession() as session:
                    return _get(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get project '{name}': {e}")
            return None

    @staticmethod
    def get_or_create_project(
        name: str,
        input_folder_path: str,
        output_folder_path: str,
        compliance_matrix_template: Optional[str] = None,
        session: Optional[Session] = None
    ) -> Optional[Project]:
        """
        Get existing project by name or create new one if it doesn't exist.

        Args:
            name: Project name
            input_folder_path: Input folder path
            output_folder_path: Output folder path
            compliance_matrix_template: Template path (optional)
            session: Database session (optional)

        Returns:
            Project: Existing or newly created project
        """
        def _get_or_create(session: Session) -> Project:
            project = session.query(Project).filter(Project.name == name).first()

            if project:
                logger.info(f"Found existing project: {name} (ID: {project.id})")
                # Update paths if they've changed
                if project.input_folder_path != input_folder_path:
                    project.input_folder_path = input_folder_path
                if project.output_folder_path != output_folder_path:
                    project.output_folder_path = output_folder_path
                if compliance_matrix_template and project.compliance_matrix_template != compliance_matrix_template:
                    project.compliance_matrix_template = compliance_matrix_template
                project.updated_at = datetime.now()
            else:
                project = Project(
                    name=name,
                    input_folder_path=input_folder_path,
                    output_folder_path=output_folder_path,
                    compliance_matrix_template=compliance_matrix_template
                )
                session.add(project)
                session.flush()
                logger.info(f"Created new project: {name} (ID: {project.id})")

            return project

        try:
            if session:
                return _get_or_create(session)
            else:
                with DatabaseSession() as session:
                    return _get_or_create(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get or create project '{name}': {e}")
            return None

    @staticmethod
    def get_all_projects(
        active_only: bool = True,
        session: Optional[Session] = None
    ) -> List[Project]:
        """
        Get all projects.

        Args:
            active_only: Only return active projects (default: True)
            session: Database session (optional)

        Returns:
            List[Project]: List of projects
        """
        def _get_all(session: Session) -> List[Project]:
            query = session.query(Project)
            if active_only:
                query = query.filter(Project.is_active == True)
            return query.order_by(Project.created_at.desc()).all()

        try:
            if session:
                return _get_all(session)
            else:
                with DatabaseSession() as session:
                    return _get_all(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all projects: {e}")
            return []

    @staticmethod
    def update_project(
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_folder_path: Optional[str] = None,
        output_folder_path: Optional[str] = None,
        compliance_matrix_template: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[dict] = None,
        session: Optional[Session] = None
    ) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: Project ID
            name: New name (optional)
            description: New description (optional)
            input_folder_path: New input path (optional)
            output_folder_path: New output path (optional)
            compliance_matrix_template: New template path (optional)
            is_active: Active status (optional)
            metadata: New metadata dict (optional)
            session: Database session (optional)

        Returns:
            Project: Updated project or None if failed
        """
        def _update(session: Session) -> Optional[Project]:
            project = session.query(Project).filter(Project.id == project_id).first()

            if not project:
                logger.warning(f"Project {project_id} not found for update")
                return None

            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            if input_folder_path is not None:
                project.input_folder_path = input_folder_path
            if output_folder_path is not None:
                project.output_folder_path = output_folder_path
            if compliance_matrix_template is not None:
                project.compliance_matrix_template = compliance_matrix_template
            if is_active is not None:
                project.is_active = is_active
            if metadata is not None:
                project.metadata = metadata

            project.updated_at = datetime.now()
            session.flush()
            logger.info(f"Updated project {project_id}")
            return project

        try:
            if session:
                return _update(session)
            else:
                with DatabaseSession() as session:
                    return _update(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return None

    @staticmethod
    def deactivate_project(project_id: int, session: Optional[Session] = None) -> bool:
        """
        Deactivate a project (soft delete).

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        result = ProjectService.update_project(
            project_id=project_id,
            is_active=False,
            session=session
        )
        return result is not None

    @staticmethod
    def delete_project(project_id: int, session: Optional[Session] = None) -> bool:
        """
        Permanently delete a project and all related data.

        WARNING: This will cascade delete all documents, requirements, and
        processing sessions associated with this project.

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        def _delete(session: Session) -> bool:
            project = session.query(Project).filter(Project.id == project_id).first()

            if not project:
                logger.warning(f"Project {project_id} not found for deletion")
                return False

            session.delete(project)
            session.flush()
            logger.warning(f"Permanently deleted project {project_id} and all related data")
            return True

        try:
            if session:
                return _delete(session)
            else:
                with DatabaseSession() as session:
                    return _delete(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False

    @staticmethod
    def get_project_statistics(project_id: int, session: Optional[Session] = None) -> Optional[dict]:
        """
        Get statistics for a project.

        Args:
            project_id: Project ID
            session: Database session (optional)

        Returns:
            dict: Statistics including document count, requirement count, etc.
        """
        def _get_stats(session: Session) -> Optional[dict]:
            project = session.query(Project).filter(Project.id == project_id).first()

            if not project:
                return None

            stats = {
                'project_id': project.id,
                'project_name': project.name,
                'document_count': len(project.documents),
                'requirement_count': len(project.requirements),
                'processing_session_count': len(project.processing_sessions),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                'is_active': project.is_active
            }

            return stats

        try:
            if session:
                return _get_stats(session)
            else:
                with DatabaseSession() as session:
                    return _get_stats(session)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get statistics for project {project_id}: {e}")
            return None
