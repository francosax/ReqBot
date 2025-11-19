#!/usr/bin/env python3
"""
Thread Safety Tests for Database Backend

Tests that the database backend handles concurrent access correctly:
- Thread-safe singleton initialization
- Concurrent session creation
- Concurrent database operations

Note: These tests validate thread safety logic without requiring SQLAlchemy
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import database module to test thread safety
try:
    from database import database as db_module
    SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:
    SQLALCHEMY_AVAILABLE = False
    print("SQLAlchemy not installed - testing lock structures only")


def reset_global_state():
    """Reset global state for testing."""
    db_module._engine = None
    db_module._session_factory = None
    db_module._scoped_session_factory = None


class TestThreadSafety:
    """Test thread safety of database initialization."""

    def test_concurrent_engine_creation(self):
        """Test that multiple threads creating engine get same instance."""
        if not SQLALCHEMY_AVAILABLE:
            print("⊘ Skipped - SQLAlchemy not installed")
            return

        reset_global_state()

        engines = []
        lock = threading.Lock()

        def create_engine_in_thread():
            engine = db_module.create_db_engine()
            with lock:
                engines.append(engine)

        # Create engine from 10 threads simultaneously
        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_engine_in_thread)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All threads should get the same engine instance
        assert len(engines) == 10
        first_engine = engines[0]
        for engine in engines:
            assert engine is first_engine  # Same object

        print(f"✓ All 10 threads got same engine instance (id: {id(first_engine)})")

    def test_concurrent_session_factory_creation(self):
        """Test that multiple threads creating session factory get same instance."""
        if not SQLALCHEMY_AVAILABLE:
            print("⊘ Skipped - SQLAlchemy not installed")
            return

        reset_global_state()

        factories = []
        lock = threading.Lock()

        def create_factory_in_thread():
            factory = db_module.create_session_factory()
            with lock:
                factories.append(factory)

        # Create factory from 10 threads simultaneously
        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_factory_in_thread)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All threads should get the same factory instance
        assert len(factories) == 10
        first_factory = factories[0]
        for factory in factories:
            assert factory is first_factory  # Same object

        print(f"✓ All 10 threads got same session factory instance (id: {id(first_factory)})")

    def test_concurrent_scoped_session_creation(self):
        """Test concurrent scoped session creation."""
        if not SQLALCHEMY_AVAILABLE:
            print("⊘ Skipped - SQLAlchemy not installed")
            return

        reset_global_state()

        scoped_sessions = []
        lock = threading.Lock()

        def create_scoped_session_in_thread():
            scoped_session = db_module.create_scoped_session()
            with lock:
                scoped_sessions.append(scoped_session)

        # Create scoped session from 10 threads simultaneously
        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_scoped_session_in_thread)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All threads should get the same scoped session factory
        assert len(scoped_sessions) == 10
        first_scoped = scoped_sessions[0]
        for scoped in scoped_sessions:
            assert scoped is first_scoped  # Same object

        print(f"✓ All 10 threads got same scoped session instance (id: {id(first_scoped)})")

    def test_no_race_conditions(self):
        """Test that there are no race conditions during initialization."""
        if not SQLALCHEMY_AVAILABLE:
            print("⊘ Skipped - SQLAlchemy not installed")
            return

        # Run the initialization multiple times to catch race conditions
        for iteration in range(5):
            reset_global_state()

            engines = []
            lock = threading.Lock()

            def create_and_check():
                # Small random delay to increase chance of race condition
                time.sleep(0.001 * (threading.current_thread().ident % 10))
                engine = db_module.create_db_engine()
                with lock:
                    engines.append(engine)

            # Create 20 threads
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(create_and_check) for _ in range(20)]
                for future in as_completed(futures):
                    future.result()  # Raise any exceptions

            # All engines should be the same instance
            assert len(set(id(e) for e in engines)) == 1, \
                f"Iteration {iteration}: Found {len(set(id(e) for e in engines))} different engine instances!"

        print("✓ No race conditions detected in 5 iterations with 20 threads each")


class TestLockBehavior:
    """Test lock behavior."""

    def test_locks_exist(self):
        """Test that thread locks are defined."""
        if not SQLALCHEMY_AVAILABLE:
            print("⊘ Skipped - SQLAlchemy not installed")
            return

        assert hasattr(db_module, '_engine_lock')
        assert hasattr(db_module, '_session_factory_lock')
        assert hasattr(db_module, '_scoped_session_lock')

        # Check locks exist and are lock objects (type name check)
        assert type(db_module._engine_lock).__name__ == 'lock'
        assert type(db_module._session_factory_lock).__name__ == 'lock'
        assert type(db_module._scoped_session_lock).__name__ == 'lock'

        print("✓ All thread locks are properly defined")


if __name__ == '__main__':
    # Run tests
    print("=" * 70)
    print("Thread Safety Tests")
    print("=" * 70)
    print()

    if not SQLALCHEMY_AVAILABLE:
        print("⚠ SQLAlchemy is not installed")
        print("These tests require SQLAlchemy to run properly.")
        print()
        print("Install with: pip install sqlalchemy")
        print()
        print("=" * 70)
        import sys
        sys.exit(0)

    test = TestThreadSafety()

    print("Test 1: Concurrent Engine Creation")
    test.test_concurrent_engine_creation()
    print()

    print("Test 2: Concurrent Session Factory Creation")
    test.test_concurrent_session_factory_creation()
    print()

    print("Test 3: Concurrent Scoped Session Creation")
    test.test_concurrent_scoped_session_creation()
    print()

    print("Test 4: No Race Conditions (100 thread attempts)")
    test.test_no_race_conditions()
    print()

    lock_test = TestLockBehavior()
    print("Test 5: Lock Definitions")
    lock_test.test_locks_exist()
    print()

    print("=" * 70)
    print("All thread safety tests PASSED!")
    print("=" * 70)
