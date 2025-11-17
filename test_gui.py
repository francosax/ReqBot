import pytest
import os
# --- PySide6 Imports ---
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from PySide6.QtCore import Qt  # Import Qt directly from QtCore
# --- End PySide6 Imports ---

# Assuming your main application file is now named RequirementBotApp.py
# and the class is RequirementBotApp.
from main_app import RequirementBotApp

# Import version information (single source of truth)
from version import GUI_VERSION

@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture
def gui(app):
    gui = RequirementBotApp()
    gui.show()
    yield gui
    gui.close()

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