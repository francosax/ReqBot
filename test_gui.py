import pytest
# --- PySide6 Imports ---
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt  # Import Qt directly from QtCore
# --- End PySide6 Imports ---

# Assuming your main application file is now named RequirementBotApp.py
# and the class is RequirementBotApp.
from main_app import RequirementBotApp

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
    assert gui.folderPath_input.text() == ""
    assert gui.folderPath_output.text() == ""
    assert gui.CM_path.text() == ""
    # In PySide6 (and modern Qt), a QProgressBar's default initial value is 0, not -1
    # Unless you explicitly set it to -1 in your RequirementBotApp.__init__
    assert gui.progressBar.value() == 0 # Changed from -1 to 0
    assert gui.windowTitle() == "RequirementBot 1.2"

def test_input_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_input"
    # Monkeypatch for PySide6's QFileDialog
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    # Use Qt.LeftButton directly
    qtbot.mouseClick(gui.inputFolderButton, Qt.LeftButton)
    assert gui.folderPath_input.text() == test_path

def test_output_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_output"
    # Monkeypatch for PySide6's QFileDialog
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    qtbot.mouseClick(gui.outputFolderButton, Qt.LeftButton)
    assert gui.folderPath_output.text() == test_path

def test_cm_file_field(gui, qtbot, monkeypatch):
    test_file = "/tmp/cm.xlsx"
    # QFileDialog.getOpenFileName in PySide6 returns (filename, selected_filter_string)
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", lambda *a, **kw: (test_file, "Excel Files (*.xlsx)"))
    qtbot.mouseClick(gui.loadCMButton, Qt.LeftButton)
    assert gui.CM_path.text() == test_file

def test_progress_bar_updates(gui):
    gui.update_progress_bar(42)
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
    gui.on_task_finished()
    assert shown.get('called', False)

# You might want to add a test for the closeEvent behavior if it's critical
def test_close_event(gui, qtbot, monkeypatch):
    # Mock QMessageBox.question
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes # Simulate clicking Yes
    )
    qtbot.close(gui) # Simulate closing the window
    assert not gui.isVisible() # Check if it actually closed