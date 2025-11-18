"""
ReqBot Database Package

This package provides database functionality for ReqBot v3.0, including:
- SQLAlchemy models for all database tables
- Database connection and session management
- Service layer for business logic
- Repository pattern for data access

Database support:
- SQLite (default, zero-configuration)
- PostgreSQL (optional, for enterprise deployments)
"""

from database.database import (
    get_engine,
    get_session,
    init_database,
    DatabaseSession
)

from database.models import (
    Project,
    Document,
    Requirement,
    RequirementHistory,
    ProcessingSession,
    KeywordProfile
)

__all__ = [
    # Database connection
    'get_engine',
    'get_session',
    'init_database',
    'DatabaseSession',

    # Models
    'Project',
    'Document',
    'Requirement',
    'RequirementHistory',
    'ProcessingSession',
    'KeywordProfile',
]

__version__ = '3.0.0'
