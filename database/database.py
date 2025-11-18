"""
Database Connection and Session Management for ReqBot v3.0

This module handles:
- Database engine creation
- Session management
- Database initialization
- Connection pooling
- Transaction management
"""

import logging
import threading
from contextlib import contextmanager
from typing import Generator, Optional
import os
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from config.database_config import (
    DATABASE_URL,
    DATABASE_ENABLED,
    LEGACY_MODE,
    get_engine_options,
    is_sqlite,
    get_sqlite_path,
    AUTO_BACKUP_ENABLED,
    BACKUP_DIR,
    MAX_BACKUPS
)
from database.models import Base

# ============================================================================
# Logger Setup
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# Global Engine and Session Factory
# ============================================================================

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_scoped_session_factory: Optional[scoped_session] = None

# Thread locks for singleton initialization
_engine_lock = threading.Lock()
_session_factory_lock = threading.Lock()
_scoped_session_lock = threading.Lock()

# ============================================================================
# SQLite Optimization
# ============================================================================

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set SQLite pragmas for better performance.
    Only applies to SQLite connections.
    """
    if is_sqlite():
        cursor = dbapi_conn.cursor()
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        # Use Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Synchronize less frequently for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size (10MB)
        cursor.execute("PRAGMA cache_size=-10000")
        # Enable memory-mapped I/O
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.close()
        logger.debug("SQLite pragmas set for optimization")


# ============================================================================
# Engine Creation
# ============================================================================

def create_db_engine() -> Engine:
    """
    Create and configure the SQLAlchemy engine with thread-safe singleton pattern.

    Returns:
        Engine: Configured SQLAlchemy engine

    Raises:
        Exception: If engine creation fails
    """
    global _engine

    # Double-checked locking pattern for thread safety
    if _engine is not None:
        return _engine

    with _engine_lock:
        # Check again inside lock
        if _engine is not None:
            return _engine

        try:
            engine_options = get_engine_options()

            # For SQLite, use StaticPool for better multi-threading
            if is_sqlite():
                engine_options['poolclass'] = StaticPool

            _engine = create_engine(DATABASE_URL, **engine_options)

            # Sanitize URL for logging (hide passwords)
            safe_url = DATABASE_URL
            if '@' in DATABASE_URL:
                # PostgreSQL: hide password
                parts = DATABASE_URL.split('@')
                if ':' in parts[0]:
                    # Format: postgresql://user:password@host
                    user_parts = parts[0].split(':')
                    safe_url = f"{':'.join(user_parts[:-1])}:***@{parts[1]}"
            else:
                # SQLite: just show it's sqlite
                safe_url = "sqlite:///<local_db>"

            logger.info(f"Database engine created successfully: {safe_url}")
            return _engine

        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise


def get_engine() -> Engine:
    """
    Get the global database engine, creating it if necessary.

    Returns:
        Engine: SQLAlchemy engine
    """
    if _engine is None:
        return create_db_engine()
    return _engine


# ============================================================================
# Session Factory Creation
# ============================================================================

def create_session_factory() -> sessionmaker:
    """
    Create the session factory for database sessions with thread-safe singleton pattern.

    Returns:
        sessionmaker: Session factory
    """
    global _session_factory

    # Double-checked locking pattern for thread safety
    if _session_factory is not None:
        return _session_factory

    with _session_factory_lock:
        # Check again inside lock
        if _session_factory is not None:
            return _session_factory

        engine = get_engine()
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        logger.info("Session factory created successfully")
        return _session_factory


def get_session_factory() -> sessionmaker:
    """
    Get the global session factory, creating it if necessary.

    Returns:
        sessionmaker: Session factory
    """
    if _session_factory is None:
        return create_session_factory()
    return _session_factory


# ============================================================================
# Scoped Session (Thread-Safe)
# ============================================================================

def create_scoped_session() -> scoped_session:
    """
    Create a thread-safe scoped session with thread-safe singleton pattern.

    Returns:
        scoped_session: Thread-safe session
    """
    global _scoped_session_factory

    # Double-checked locking pattern for thread safety
    if _scoped_session_factory is not None:
        return _scoped_session_factory

    with _scoped_session_lock:
        # Check again inside lock
        if _scoped_session_factory is not None:
            return _scoped_session_factory

        session_factory = get_session_factory()
        _scoped_session_factory = scoped_session(session_factory)

        logger.info("Scoped session factory created successfully")
        return _scoped_session_factory


def get_scoped_session() -> scoped_session:
    """
    Get the global scoped session, creating it if necessary.

    Returns:
        scoped_session: Thread-safe session
    """
    if _scoped_session_factory is None:
        return create_scoped_session()
    return _scoped_session_factory


# ============================================================================
# Session Management
# ============================================================================

def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: SQLAlchemy session

    Example:
        session = get_session()
        try:
            # Use session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    """
    factory = get_session_factory()
    return factory()


@contextmanager
def DatabaseSession() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic transaction handling.

    Yields:
        Session: SQLAlchemy session

    Example:
        with DatabaseSession() as session:
            project = Project(name="My Project")
            session.add(project)
            # Automatically commits on success, rolls back on exception
    """
    session = get_session()
    try:
        yield session
        session.commit()
        logger.debug("Database transaction committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction rolled back due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


# ============================================================================
# Database Initialization
# ============================================================================

def backup_database() -> Optional[str]:
    """
    Create a backup of the SQLite database before major operations.

    Returns:
        str: Path to backup file, or None if backup not needed/failed
    """
    if not is_sqlite() or not AUTO_BACKUP_ENABLED:
        return None

    db_path = get_sqlite_path()
    if not db_path.exists():
        logger.debug("No database file to backup")
        return None

    try:
        # Create backup directory
        backup_dir = Path(BACKUP_DIR)
        backup_dir.mkdir(exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"reqbot_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        # Copy database file
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")

        # Clean up old backups
        cleanup_old_backups()

        return str(backup_path)

    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None


def cleanup_old_backups():
    """
    Remove old backup files, keeping only MAX_BACKUPS most recent.
    """
    try:
        backup_dir = Path(BACKUP_DIR)
        if not backup_dir.exists():
            return

        # Get all backup files
        backup_files = sorted(
            backup_dir.glob("reqbot_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Delete old backups
        for backup_file in backup_files[MAX_BACKUPS:]:
            backup_file.unlink()
            logger.debug(f"Deleted old backup: {backup_file}")

    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}")


def init_database(create_backup: bool = True) -> bool:
    """
    Initialize the database by creating all tables.

    Args:
        create_backup: Whether to backup existing database before init

    Returns:
        bool: True if initialization successful, False otherwise
    """
    if LEGACY_MODE or not DATABASE_ENABLED:
        logger.info("Database initialization skipped (legacy mode or disabled)")
        return False

    try:
        # Backup existing database if requested
        if create_backup and is_sqlite():
            backup_path = backup_database()
            if backup_path:
                logger.info(f"Database backup created: {backup_path}")

        # Get engine
        engine = get_engine()

        # Create all tables
        Base.metadata.create_all(engine)

        logger.info("Database initialized successfully")
        logger.info(f"Tables created: {', '.join(Base.metadata.tables.keys())}")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def drop_all_tables() -> bool:
    """
    Drop all database tables. Use with caution!

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create backup first
        backup_path = backup_database()
        if backup_path:
            logger.warning(f"Database backed up before dropping tables: {backup_path}")

        engine = get_engine()
        Base.metadata.drop_all(engine)

        logger.warning("All database tables dropped successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False


# ============================================================================
# Database Health Check
# ============================================================================

def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        logger.info("Database connection check: OK")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get information about the current database.

    Returns:
        dict: Database information
    """
    # Sanitize URL for display
    safe_url = DATABASE_URL
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        if ':' in parts[0]:
            user_parts = parts[0].split(':')
            safe_url = f"{':'.join(user_parts[:-1])}:***@{parts[1]}"
    else:
        safe_url = "sqlite:///<local_db>"

    info = {
        'enabled': DATABASE_ENABLED,
        'legacy_mode': LEGACY_MODE,
        'url': safe_url,
        'type': 'sqlite' if is_sqlite() else 'postgresql',
        'tables': list(Base.metadata.tables.keys()),
        'connection_ok': check_database_connection()
    }

    if is_sqlite():
        db_path = get_sqlite_path()
        info['sqlite_path'] = str(db_path)
        info['sqlite_exists'] = db_path.exists()
        if db_path.exists():
            info['sqlite_size_mb'] = db_path.stat().st_size / (1024 * 1024)

    return info


# ============================================================================
# Cleanup
# ============================================================================

def close_database():
    """
    Close database connections and cleanup resources.
    Call this when shutting down the application.
    """
    global _engine, _session_factory, _scoped_session_factory

    try:
        if _scoped_session_factory is not None:
            _scoped_session_factory.remove()
            _scoped_session_factory = None
            logger.debug("Scoped session removed")

        if _engine is not None:
            _engine.dispose()
            _engine = None
            logger.info("Database engine disposed")

        _session_factory = None

    except Exception as e:
        logger.error(f"Error closing database: {e}")


# ============================================================================
# Module-level Convenience Functions
# ============================================================================

def execute_in_transaction(func, *args, **kwargs):
    """
    Execute a function within a database transaction.

    Args:
        func: Function to execute (must accept session as first arg)
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments

    Returns:
        Result of the function

    Example:
        def create_project(session, name):
            project = Project(name=name)
            session.add(project)
            return project

        project = execute_in_transaction(create_project, "My Project")
    """
    with DatabaseSession() as session:
        return func(session, *args, **kwargs)


# ============================================================================
# Initialization Helper
# ============================================================================

def auto_initialize_database():
    """
    Auto-initialize database on application startup.

    This should be called explicitly from main_app.py or application entry point,
    NOT at module import time to avoid circular dependencies and test issues.

    Returns:
        bool: True if initialization successful, False otherwise
    """
    if LEGACY_MODE or not DATABASE_ENABLED:
        logger.info("Database auto-initialization skipped (legacy mode or disabled)")
        return False

    logger.info("Auto-initializing database...")
    try:
        # Create engine and check connection
        create_db_engine()
        create_session_factory()

        # Initialize database tables if needed
        if is_sqlite():
            db_path = get_sqlite_path()
            if not db_path.exists():
                logger.info("Database file not found, creating schema...")
                init_database(create_backup=False)

        logger.info("Database auto-initialization complete")
        return True
    except Exception as e:
        logger.error(f"Failed to auto-initialize database: {e}")
        return False


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Print database info
    print("\n" + "=" * 60)
    print("ReqBot Database Information")
    print("=" * 60)

    info = get_database_info()
    for key, value in info.items():
        print(f"{key}: {value}")

    print("=" * 60 + "\n")

    # Test connection
    if check_database_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
