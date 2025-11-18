"""
Pytest configuration file for ReqBot tests.

Provides common fixtures and configurations for Qt testing,
including proper cleanup to avoid Windows fatal exceptions.
"""

import pytest
import sys
import gc
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


@pytest.fixture(scope="session", autouse=True)
def qapp_session():
    """
    Session-scoped QApplication fixture.
    Ensures single QApplication instance for all tests.
    """
    # Get or create QApplication instance
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app

    # Session cleanup
    # Process all pending events
    app.processEvents()

    # Give Qt time to cleanup (helps on Windows)
    QTimer.singleShot(0, app.quit)
    app.processEvents()


@pytest.fixture(autouse=True)
def qt_cleanup(request, qapp_session):
    """
    Auto-use fixture that ensures Qt cleanup after each test.
    Helps prevent Windows fatal exception on test cleanup.
    """
    yield

    # Post-test cleanup
    app = qapp_session

    # Process any pending deleteLater() calls
    app.sendPostedEvents(None, 0)
    app.processEvents()

    # Force garbage collection to help cleanup Qt objects
    gc.collect()

    # Process events one more time
    app.processEvents()


def pytest_configure(config):
    """
    Pytest configuration hook.
    Adds custom markers for Qt tests.
    """
    config.addinivalue_line(
        "markers", "qt: mark test as requiring Qt (automatically applied to Qt tests)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_exception_interact(node, call, report):
    """
    Hook called when an exception was raised which can potentially be interactively handled.
    Ensures cleanup even when tests fail.
    """
    if call.excinfo is not None:
        # Try to cleanup Qt even on exceptions
        try:
            app = QApplication.instance()
            if app:
                app.processEvents()
        except:
            pass  # Ignore cleanup errors during exception handling
