import pytest
import os
# --- PySide6 Imports ---
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from PySide6.QtCore import Qt  # Import Qt directly from QtCore
# --- End PySide6 Imports ---

# Assuming your main application file is now named RequirementBotApp.py
# and the class is RequirementBotApp.
from main_app import RequirementBotApp, DragDropComboBox

# Import version information (single source of truth)
from version import GUI_VERSION

# For drag & drop testing
from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import tempfile


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for tests."""
    app = QApplication.instance() or QApplication([])
    yield app
    # Cleanup: Process remaining events and deleteLater objects
    app.processEvents()


@pytest.fixture
def gui(app, qtbot, tmp_path):
    """Create RequirementBotApp instance for tests with proper cleanup."""
    # Clear recent projects before creating GUI to ensure clean state
    recents_config_path = os.path.join(os.getcwd(), 'recents_config.json')
    backup_path = recents_config_path + '.test_backup'

    # Backup existing config if it exists
    if os.path.exists(recents_config_path):
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(recents_config_path, backup_path)
    else:
        backup_path = None

    # Create GUI with clean recent projects state
    gui = RequirementBotApp()
    gui.show()
    yield gui

    # Proper cleanup to avoid Windows fatal exception
    try:
        # Close the window if it's still visible
        if gui.isVisible():
            gui.close()

        # Stop any running worker threads
        if hasattr(gui, '_worker_thread') and gui._worker_thread is not None:
            if gui._worker_thread.isRunning():
                if hasattr(gui, '_worker') and gui._worker is not None:
                    gui._worker.stop()
                gui._worker_thread.quit()
                gui._worker_thread.wait(1000)  # Wait up to 1 second

        # Process pending events
        app.processEvents()

        # Schedule for deletion
        gui.deleteLater()

        # Process deleteLater events
        app.processEvents()

        # Restore the recent projects config if it was backed up
        if backup_path and os.path.exists(backup_path):
            # Remove test-generated config
            if os.path.exists(recents_config_path):
                os.remove(recents_config_path)
            os.rename(backup_path, recents_config_path)

    except Exception as e:
        # Log but don't fail test on cleanup errors
        print(f"Warning: Cleanup error in test fixture: {e}")


@pytest.mark.smoke
def test_initial_state(gui):
    # NEW: Use currentText() for QComboBox widgets
    assert gui.folderPath_input.currentText() == ""
    assert gui.folderPath_output.currentText() == ""
    assert gui.CM_path.currentText() == ""
    # PySide6's QProgressBar has a default initial value of -1 when no range is set
    # or 0 when setValue(0) is explicitly called. Accept either value as valid initial state.
    assert gui.progressBar.value() in [-1, 0], f"Expected progressBar value to be -1 or 0, got {gui.progressBar.value()}"
    assert gui.windowTitle() == f"RequirementBot {GUI_VERSION}"


def test_input_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_input"
    # Monkeypatch for PySide6's QFileDialog
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    # Find the browse button for input folder (first Browse button in the UI)
    browse_buttons = [btn for btn in gui.findChildren(QPushButton) if btn.text() == "Browse..."]
    assert len(browse_buttons) >= 1, "Could not find Browse button for input folder"
    qtbot.mouseClick(browse_buttons[0], Qt.LeftButton)
    # Compare normalized paths (main_app.py uses os.path.normpath)
    # NEW: Use currentText() for QComboBox widgets
    assert gui.folderPath_input.currentText() == os.path.normpath(test_path)


def test_output_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_output"
    # Monkeypatch for PySide6's QFileDialog
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    # Find the browse button for output folder (second Browse button in the UI)
    browse_buttons = [btn for btn in gui.findChildren(QPushButton) if btn.text() == "Browse..."]
    assert len(browse_buttons) >= 2, "Could not find Browse button for output folder"
    qtbot.mouseClick(browse_buttons[1], Qt.LeftButton)
    # Compare normalized paths (main_app.py uses os.path.normpath)
    # NEW: Use currentText() for QComboBox widgets
    assert gui.folderPath_output.currentText() == os.path.normpath(test_path)


def test_cm_file_field(gui, qtbot, monkeypatch):
    test_file = "/tmp/cm.xlsx"
    # QFileDialog.getOpenFileName in PySide6 returns (filename, selected_filter_string)
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", lambda *a, **kw: (test_file, "Excel Files (*.xlsx)"))
    # Find the browse button for compliance matrix (third Browse button in the UI)
    browse_buttons = [btn for btn in gui.findChildren(QPushButton) if btn.text() == "Browse..."]
    assert len(browse_buttons) >= 3, "Could not find Browse button for compliance matrix"
    qtbot.mouseClick(browse_buttons[2], Qt.LeftButton)
    # Compare normalized paths (main_app.py uses os.path.normpath)
    # NEW: Use currentText() for QComboBox widgets
    assert gui.CM_path.currentText() == os.path.normpath(test_file)


@pytest.mark.smoke
def test_progress_bar_updates(gui):
    # Test that the progress bar can be updated
    # In the actual app, this is done via signals from the worker
    gui.progressBar.setValue(42)
    assert gui.progressBar.value() == 42


def test_task_finished_shows_messagebox(gui, qtbot, monkeypatch):
    shown = {}

    def fake_information(*args, **kwargs):
        shown['called'] = True
        # In PySide6, QMessageBox.information also returns a StandardButton,
        # so make sure the mocked function returns something compatible if needed.
        # For this test, simply setting 'called' is sufficient.
        return QMessageBox.StandardButton.Ok

    # Monkeypatch for PySide6's QMessageBox
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", fake_information)
    # Use the correct method name with required message parameter
    gui.on_processing_finished("Test completion message")
    assert shown.get('called', False)

def test_threading_fix_prevents_double_start(gui, qtbot, monkeypatch):
    """Test that starting processing while already running shows a warning."""
    # Mock the QThread to simulate a running thread
    from PySide6.QtCore import QThread

    # Create a mock thread that reports as running
    class MockThread:
        def isRunning(self):
            return True
        def wait(self):
            pass
        def quit(self):
            pass

    # Set the mock thread
    gui._worker_thread = MockThread()

    warning_shown = {}
    log_called = {}

    def fake_warning(*args, **kwargs):
        warning_shown['called'] = True
        warning_shown['title'] = args[1] if len(args) > 1 else None
        warning_shown['message'] = args[2] if len(args) > 2 else None
        return QMessageBox.StandardButton.Ok

    def fake_logger_warning(msg, *args, **kwargs):
        log_called['called'] = True
        log_called['message'] = msg
        # Don't actually emit to widget to avoid Qt deletion issues

    # Monkeypatch QMessageBox.warning and logger.warning
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning", fake_warning)
    monkeypatch.setattr(gui.logger, "warning", fake_logger_warning)

    # Try to start processing while "running"
    gui.start_processing()

    # Verify warning was shown
    assert warning_shown.get('called', False), "Warning dialog should be shown"
    assert warning_shown.get('title') == "Processing In Progress"
    assert "already running" in warning_shown.get('message', '').lower()

    # Verify log was called
    assert log_called.get('called', False), "Logger should be called"
    assert "already running" in log_called.get('message', '').lower()

    # Cleanup
    gui._worker_thread = None

# You might want to add a test for the closeEvent behavior if it's critical


def test_close_event(gui, qtbot, monkeypatch):
    # Mock QMessageBox.question to simulate clicking Yes
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes
    )
    # Call close() to trigger the closeEvent
    gui.close()
    # After accepting the close dialog, the window should not be visible
    assert not gui.isVisible()


# ========================================
# Drag & Drop Tests (v2.3.0)
# ========================================

@pytest.fixture
def temp_folder():
    """Create a temporary folder for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_xlsx_file():
    """Create a temporary .xlsx file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmpfile:
        tmpfile.write(b'test data')
        tmpfile_path = tmpfile.name
    yield tmpfile_path
    os.remove(tmpfile_path)


@pytest.fixture
def temp_pdf_file():
    """Create a temporary .pdf file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmpfile:
        tmpfile.write(b'test pdf data')
        tmpfile_path = tmpfile.name
    yield tmpfile_path
    os.remove(tmpfile_path)


@pytest.mark.smoke
def test_dragdrop_combo_accepts_folders(app, qtbot, temp_folder):
    """Test DragDropComboBox accepts folder drops when configured."""
    combo = DragDropComboBox(accept_files=False, accept_folders=True)
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with folder URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_folder)])

    # Simulate drag enter event
    drag_event = QDragEnterEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dragEnterEvent(drag_event)

    # Event should be accepted
    assert drag_event.isAccepted()


def test_dragdrop_combo_accepts_xlsx_files(app, qtbot, temp_xlsx_file):
    """Test DragDropComboBox accepts .xlsx file drops when configured."""
    combo = DragDropComboBox(accept_files=True, accept_folders=False, file_extension='.xlsx')
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with .xlsx file URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_xlsx_file)])

    # Simulate drag enter event
    drag_event = QDragEnterEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dragEnterEvent(drag_event)

    # Event should be accepted
    assert drag_event.isAccepted()


def test_dragdrop_combo_rejects_wrong_file_type(app, qtbot, temp_pdf_file):
    """Test DragDropComboBox rejects file drops with wrong extension."""
    combo = DragDropComboBox(accept_files=True, accept_folders=False, file_extension='.xlsx')
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with .pdf file URL (should be rejected)
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_pdf_file)])

    # Simulate drag enter event
    drag_event = QDragEnterEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dragEnterEvent(drag_event)

    # Event should be ignored
    assert not drag_event.isAccepted()


def test_dragdrop_combo_rejects_files_when_folders_only(app, qtbot, temp_xlsx_file):
    """Test DragDropComboBox rejects file drops when only folders accepted."""
    combo = DragDropComboBox(accept_files=False, accept_folders=True)
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with file URL (should be rejected)
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_xlsx_file)])

    # Simulate drag enter event
    drag_event = QDragEnterEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dragEnterEvent(drag_event)

    # Event should be ignored
    assert not drag_event.isAccepted()


def test_dragdrop_combo_rejects_folders_when_files_only(app, qtbot, temp_folder):
    """Test DragDropComboBox rejects folder drops when only files accepted."""
    combo = DragDropComboBox(accept_files=True, accept_folders=False, file_extension='.xlsx')
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with folder URL (should be rejected)
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_folder)])

    # Simulate drag enter event
    drag_event = QDragEnterEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dragEnterEvent(drag_event)

    # Event should be ignored
    assert not drag_event.isAccepted()


def test_dragdrop_combo_populates_on_folder_drop(app, qtbot, temp_folder):
    """Test DragDropComboBox populates text field on successful folder drop."""
    combo = DragDropComboBox(accept_files=False, accept_folders=True)
    combo.setEditable(True)
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with folder URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_folder)])

    # Simulate drop event
    drop_event = QDropEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dropEvent(drop_event)

    # Combo box should now contain the dropped path
    assert combo.currentText() == os.path.normpath(temp_folder)
    assert drop_event.isAccepted()


def test_dragdrop_combo_populates_on_file_drop(app, qtbot, temp_xlsx_file):
    """Test DragDropComboBox populates text field on successful file drop."""
    combo = DragDropComboBox(accept_files=True, accept_folders=False, file_extension='.xlsx')
    combo.setEditable(True)
    combo.show()
    qtbot.addWidget(combo)

    # Create mime data with .xlsx file URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_xlsx_file)])

    # Simulate drop event
    drop_event = QDropEvent(
        combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    combo.dropEvent(drop_event)

    # Combo box should now contain the dropped path
    assert combo.currentText() == os.path.normpath(temp_xlsx_file)
    assert drop_event.isAccepted()


def test_gui_input_folder_accepts_drag_drop(gui, qtbot, temp_folder):
    """Test GUI input folder field accepts folder drag & drop."""
    # Get the input folder combo box
    input_combo = gui.folderPath_input

    # Verify it's a DragDropComboBox
    assert isinstance(input_combo, DragDropComboBox)

    # Create mime data with folder URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_folder)])

    # Simulate drag enter
    drag_event = QDragEnterEvent(
        input_combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    input_combo.dragEnterEvent(drag_event)
    assert drag_event.isAccepted()

    # Simulate drop
    drop_event = QDropEvent(
        input_combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    input_combo.dropEvent(drop_event)

    # Verify path was set
    assert input_combo.currentText() == os.path.normpath(temp_folder)


def test_gui_cm_path_accepts_xlsx_drag_drop(gui, qtbot, temp_xlsx_file):
    """Test GUI compliance matrix field accepts .xlsx file drag & drop."""
    # Get the CM path combo box
    cm_combo = gui.CM_path

    # Verify it's a DragDropComboBox
    assert isinstance(cm_combo, DragDropComboBox)

    # Create mime data with .xlsx file URL
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(temp_xlsx_file)])

    # Simulate drag enter
    drag_event = QDragEnterEvent(
        cm_combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    cm_combo.dragEnterEvent(drag_event)
    assert drag_event.isAccepted()

    # Simulate drop
    drop_event = QDropEvent(
        cm_combo.rect().center(),
        Qt.CopyAction,
        mime_data,
        Qt.LeftButton,
        Qt.NoModifier
    )
    cm_combo.dropEvent(drop_event)

    # Verify path was set
    assert cm_combo.currentText() == os.path.normpath(temp_xlsx_file)


# ========================================
# Progress Details Tests (v2.3.0)
# ========================================

@pytest.mark.smoke
def test_progress_detail_label_exists(gui):
    """Test that progress detail label exists in GUI."""
    assert hasattr(gui, 'progress_detail_label')
    assert gui.progress_detail_label is not None


def test_progress_detail_label_initial_state(gui):
    """Test progress detail label initial text."""
    assert gui.progress_detail_label.text() == "Ready to process"


def test_update_progress_detail_method(gui):
    """Test update_progress_detail method updates label."""
    test_message = "File 1/3: Analyzing document.pdf..."
    gui.update_progress_detail(test_message)
    assert gui.progress_detail_label.text() == test_message


def test_progress_detail_label_reset_on_completion(gui):
    """Test progress detail label resets after processing completion."""
    # Set a custom message
    gui.update_progress_detail("Processing file...")

    # Simulate processing finished
    gui.on_processing_finished("Processing completed")

    # Label should be reset
    assert gui.progress_detail_label.text() == "Ready to process"


def test_progress_detail_label_reset_on_error(gui):
    """Test progress detail label resets after processing error."""
    # Set a custom message
    gui.update_progress_detail("Processing file...")

    # Simulate processing error
    gui.on_processing_error("Test error", "Error")

    # Label should be reset
    assert gui.progress_detail_label.text() == "Ready to process"


def test_progress_detail_label_reset_on_cancel(gui):
    """Test progress detail label resets after processing cancellation."""
    # Set a custom message
    gui.update_progress_detail("Processing file...")

    # Create a mock worker and thread to avoid actual processing
    from unittest.mock import MagicMock
    gui._worker = MagicMock()
    gui._worker_thread = MagicMock()
    gui._worker_thread.isRunning.return_value = True

    # Simulate cancel
    gui.cancel_processing()

    # Label should be reset
    assert gui.progress_detail_label.text() == "Ready to process"
