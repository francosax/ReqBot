import pytest
from PyQt5 import QtCore  # <-- Add this import
from PyQt5.QtWidgets import QApplication
from RequirementBot_GUI2 import RequirementBotApp

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
    assert gui.progressBar.value() == -1
    assert gui.windowTitle() == "RequirementBot 1.2"

def test_input_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_input"
    monkeypatch.setattr("PyQt5.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    qtbot.mouseClick(gui.inputFolderButton, QtCore.Qt.LeftButton)  # <-- Use QtCore.Qt.LeftButton
    assert gui.folderPath_input.text() == test_path

def test_output_folder_field(gui, qtbot, monkeypatch):
    test_path = "/tmp/test_output"
    monkeypatch.setattr("PyQt5.QtWidgets.QFileDialog.getExistingDirectory", lambda *a, **kw: test_path)
    qtbot.mouseClick(gui.outputFolderButton, QtCore.Qt.LeftButton)
    assert gui.folderPath_output.text() == test_path

def test_cm_file_field(gui, qtbot, monkeypatch):
    test_file = "/tmp/cm.xlsx"
    monkeypatch.setattr("PyQt5.QtWidgets.QFileDialog.getOpenFileName", lambda *a, **kw: (test_file, "Text Files (*.xlsx)"))
    qtbot.mouseClick(gui.loadCMButton, QtCore.Qt.LeftButton)
    assert gui.CM_path.text() == test_file

def test_progress_bar_updates(gui):
    gui.update_progress_bar(42)
    assert gui.progressBar.value() == 42

def test_task_finished_shows_messagebox(gui, qtbot, monkeypatch):
    shown = {}

    def fake_information(*args, **kwargs):
        shown['called'] = True
        return None

    monkeypatch.setattr("PyQt5.QtWidgets.QMessageBox.information", fake_information)
    gui.on_task_finished()
    assert shown.get('called', False)