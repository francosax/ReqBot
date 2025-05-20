import sys
import time

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QProgressBar, QVBoxLayout, QMessageBox, \
    QLineEdit, QFileDialog, QLabel  # Import QLabel here


class Worker(QObject):
    progress = pyqtSignal(int)  # Signal to update progress bar
    finished = pyqtSignal()  # Signal to indicate task completion

    @pyqtSlot()
    def do_work(self):
        # Simulate a long-running task
        for i in range(100):
            time.sleep(0.1)  # Simulate work
            self.progress.emit(i)  # Emit progress signal
        self.finished.emit()  # Emit finished signal


class RequirementBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = Worker()
        self.worker.progress.connect(self.update_progress_bar)
        self.worker.finished.connect(self.on_task_finished)

    def init_ui(self):
        self.setWindowTitle('RequirementBot 1.1')
        self.setGeometry(300, 300, 400, 200)

        self.folderPath_input = QLineEdit(self)
        self.folderPath_output = QLineEdit(self)
        self.CM_path = QLineEdit(self)

        self.inputFolderButton = QPushButton('Input Folder', self)
        self.outputFolderButton = QPushButton('Output Folder', self)
        self.loadCMButton = QPushButton('Load CM', self)
        self.createButton = QPushButton('CREATE', self)

        self.inputFolderButton.clicked.connect(self.get_folder_path_input)
        self.outputFolderButton.clicked.connect(self.get_folder_path_output)
        self.loadCMButton.clicked.connect(self.get_compliance_matrix)
        self.createButton.clicked.connect(self.do_stuff)

        # Create a progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30, 120, 340, 25)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('IN'))
        layout.addWidget(self.folderPath_input)
        layout.addWidget(self.inputFolderButton)
        layout.addWidget(QLabel('OUT'))
        layout.addWidget(self.folderPath_output)
        layout.addWidget(self.outputFolderButton)
        layout.addWidget(QLabel('Compliance Matrix'))
        layout.addWidget(self.CM_path)
        layout.addWidget(self.loadCMButton)
        layout.addWidget(self.createButton)
        layout.addWidget(self.progressBar)  # Add the progress bar to the layout
        self.setLayout(layout)

    def get_folder_path_input(self):
        folder_selected_input = QFileDialog.getExistingDirectory(self, 'Select an input folder')
        self.folderPath_input.setText(folder_selected_input)

    def get_folder_path_output(self):
        folder_selected_output = QFileDialog.getExistingDirectory(self, 'Select an output folder')
        self.folderPath_output.setText(folder_selected_output)

    def get_compliance_matrix(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "Text Files (*.xlsx);;All Files (*)")
        self.CM_path.setText(file_path)

    def do_stuff(self):
        self.worker.start()

    def update_progress_bar(self, value):
        self.progressBar.setValue(value)

    def on_task_finished(self):
        QMessageBox.information(self, "Alert Message", "Completed")

    def close_event(self, event):
        if QMessageBox.question(self, 'Closing', 'Really close?') == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RequirementBotApp()
    ex.show()
    sys.exit(app.exec_())
