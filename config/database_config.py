"""
Database Configuration for ReqBot v3.0

This module manages database configuration settings, supporting both
SQLite (default) and PostgreSQL databases.
"""

import os
from pathlib import Path

# ============================================================================
# Database Configuration
# ============================================================================

# Enable/disable database functionality
DATABASE_ENABLED = os.getenv('REQBOT_DB_ENABLED', 'true').lower() == 'true'

# Legacy mode: Skip database, use direct file export only
LEGACY_MODE = os.getenv('REQBOT_LEGACY_MODE', 'false').lower() == 'true'

# Database type: 'sqlite' or 'postgresql'
DATABASE_TYPE = os.getenv('REQBOT_DB_TYPE', 'sqlite')

# ============================================================================
# SQLite Configuration (Default)
# ============================================================================

# SQLite database file location
SQLITE_DB_PATH = os.getenv('REQBOT_SQLITE_PATH', 'reqbot.db')

# SQLite connection URL
SQLITE_URL = f'sqlite:///{SQLITE_DB_PATH}'

# SQLite specific settings
SQLITE_TIMEOUT = 30  # seconds
SQLITE_CHECK_SAME_THREAD = False  # Allow multi-threaded access

# ============================================================================
# PostgreSQL Configuration (Optional)
# ============================================================================

# PostgreSQL connection parameters
POSTGRES_HOST = os.getenv('REQBOT_PG_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('REQBOT_PG_PORT', '5432'))
POSTGRES_DB = os.getenv('REQBOT_PG_DB', 'reqbot')
POSTGRES_USER = os.getenv('REQBOT_PG_USER', 'reqbot')
POSTGRES_PASSWORD = os.getenv('REQBOT_PG_PASSWORD', '')

# PostgreSQL connection URL
POSTGRES_URL = (
    f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@'
    f'{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
)

# ============================================================================
# Active Database URL
# ============================================================================

def get_database_url():
    """
    Get the active database URL based on configuration.

    Returns:
        str: SQLAlchemy-compatible database URL
    """
    if DATABASE_TYPE == 'postgresql':
        return POSTGRES_URL
    else:
        return SQLITE_URL


DATABASE_URL = get_database_url()

# ============================================================================
# SQLAlchemy Configuration
# ============================================================================

# Connection pool settings
POOL_SIZE = int(os.getenv('REQBOT_DB_POOL_SIZE', '5'))
MAX_OVERFLOW = int(os.getenv('REQBOT_DB_MAX_OVERFLOW', '10'))
POOL_TIMEOUT = int(os.getenv('REQBOT_DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('REQBOT_DB_POOL_RECYCLE', '3600'))  # 1 hour

# Echo SQL statements for debugging
ECHO_SQL = os.getenv('REQBOT_DB_ECHO', 'false').lower() == 'true'

# ============================================================================
# Migration Configuration
# ============================================================================

# Alembic migration directory
MIGRATION_DIR = os.path.join(os.path.dirname(__file__), '..', 'database', 'migrations')

# ============================================================================
# Performance Settings
# ============================================================================

# Batch insert size for bulk operations
BATCH_INSERT_SIZE = 1000

# Enable query result caching
ENABLE_QUERY_CACHE = True

# Cache TTL in seconds
QUERY_CACHE_TTL = 300  # 5 minutes

# ============================================================================
# Backup Configuration
# ============================================================================

# Auto-backup before migrations (SQLite only)
AUTO_BACKUP_ENABLED = True

# Backup directory
BACKUP_DIR = os.getenv('REQBOT_BACKUP_DIR', 'backups')

# Maximum number of backups to keep
MAX_BACKUPS = 10

# ============================================================================
# Helper Functions
# ============================================================================

def get_sqlite_path():
    """
    Get the absolute path to the SQLite database file.

    Returns:
        Path: Absolute path to database file
    """
    return Path(SQLITE_DB_PATH).absolute()


def is_sqlite():
    """
    Check if using SQLite database.

    Returns:
        bool: True if using SQLite
    """
    return DATABASE_TYPE == 'sqlite'


def is_postgresql():
    """
    Check if using PostgreSQL database.

    Returns:
        bool: True if using PostgreSQL
    """
    return DATABASE_TYPE == 'postgresql'


def get_engine_options():
    """
    Get SQLAlchemy engine options based on database type.

    Returns:
        dict: Engine configuration options
    """
    base_options = {
        'echo': ECHO_SQL,
        'pool_pre_ping': True,  # Verify connections before using
    }

    if is_sqlite():
        base_options.update({
            'connect_args': {
                'timeout': SQLITE_TIMEOUT,
                'check_same_thread': SQLITE_CHECK_SAME_THREAD,
            }
        })
    elif is_postgresql():
        base_options.update({
            'pool_size': POOL_SIZE,
            'max_overflow': MAX_OVERFLOW,
            'pool_timeout': POOL_TIMEOUT,
            'pool_recycle': POOL_RECYCLE,
        })

    return base_options


# ============================================================================
# Configuration Summary
# ============================================================================

def print_config():
    """Print current database configuration (for debugging)."""
    print("=" * 60)
    print("ReqBot Database Configuration")
    print("=" * 60)
    print(f"Database Enabled: {DATABASE_ENABLED}")
    print(f"Legacy Mode: {LEGACY_MODE}")
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"Database URL: {DATABASE_URL}")
    if is_sqlite():
        print(f"SQLite Path: {get_sqlite_path()}")
    print(f"Echo SQL: {ECHO_SQL}")
    print("=" * 60)


if __name__ == '__main__':
    print_config()
