import logging
import os
import sys
from datetime import datetime

# --- PySide6 Imports ---
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QFileDialog,
    QMessageBox, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout,
    QGroupBox, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QThread # Import QThread
from PySide6.QtGui import QIcon # For potentially adding icons



# Import the worker class
from processing_worker import ProcessingWorker # <--- NEW IMPORT

# --- Constants for paths, messages, etc. ---
CM_TEMPLATE_NAME = 'Compliance_Matrix_Template_rev001.xlsx'

class QTextEditLogger(logging.Handler):
    """Custom logging handler to send log messages to a QTextEdit."""
    def __init__(self, parent_text_edit):
        super().__init__()
        self.widget = parent_text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        # Append message in a thread-safe way (Qt's append doesn't block)
        self.widget.append(msg)
        # Scroll to the bottom
        self.widget.verticalScrollBar().setValue(self.widget.verticalScrollBar().maximum())


class RequirementBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self._worker_thread = None # Initialize worker thread as None
        self._worker = None        # Initialize worker object as None
        self.init_logging() # Setup logging before UI
        self.init_ui()
        self._apply_stylesheet() # Apply stylesheet after UI is initialized

    def init_logging(self):
        # Configure logging to console and file, and also to the QTextEdit
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler('application_gui.log'), # Log to a file
                                logging.StreamHandler(sys.stdout)          # Log to console
                            ])
        self.logger = logging.getLogger(__name__)


    def init_ui(self):
        self.setWindowTitle('RequirementBot 2.0')
        self.resize(800, 600) # Set a more appropriate initial size for the expanded UI

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Input Group Box ---
        input_group_box = QGroupBox("Configuration Paths")
        input_layout = QVBoxLayout()

        self.folderPath_input = self._create_path_selector(
            input_layout, "Input Folder:", self.get_folder_path_input, "Select Input Folder"
        )
        self.folderPath_output = self._create_path_selector(
            input_layout, "Output Folder:", self.get_folder_path_output, "Select Output Folder"
        )
        self.CM_path = self._create_path_selector(
            input_layout, "Compliance Matrix:", self.get_compliance_matrix, "Select Compliance Matrix File",
            file_filter="Excel Files (*.xlsx);;All Files (*)"
        )

        input_group_box.setLayout(input_layout)
        main_layout.addWidget(input_group_box)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.createButton = QPushButton('Start Processing')
        self.createButton.clicked.connect(self.start_processing)
        self.createButton.setMinimumHeight(50) # Make it taller
        self.createButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 18px;")

        self.cancelButton = QPushButton('Cancel Processing')
        self.cancelButton.clicked.connect(self.cancel_processing)
        self.cancelButton.setEnabled(False) # Disabled initially
        self.cancelButton.setMinimumHeight(50)
        self.cancelButton.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; font-size: 18px;")

        button_layout.addWidget(self.createButton)
        button_layout.addWidget(self.cancelButton)
        main_layout.addLayout(button_layout)


        # --- Progress Bar ---
        self.progressBar = QProgressBar(self)
        self.progressBar.setTextVisible(True)
        self.progressBar.setFormat("Progress: %p%") # Display percentage
        main_layout.addWidget(self.progressBar)

        # --- Log Display ---
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("Application logs and status messages will appear here...")
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow it to take available space
        main_layout.addWidget(self.log_display)

        # Connect custom logger to QTextEdit
        self.log_handler = QTextEditLogger(self.log_display)
        self.logger.addHandler(self.log_handler)
        # Also add to the worker logger to capture its messages
        logging.getLogger('processing_worker').addHandler(self.log_handler)

        self.setLayout(main_layout)
        self.setMinimumSize(600, 400) # Ensure a reasonable minimum size

    def _create_path_selector(self, parent_layout, label_text, select_func, dialog_title, file_filter="All Files (*.*)"):
        """Helper to create a QLabel, QLineEdit, and Browse/Clear buttons."""
        h_layout = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit(self)
        line_edit.setReadOnly(True)
        line_edit.setPlaceholderText(f"Click 'Browse' to select {label_text.lower().replace(':', '')}...")

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda: select_func(line_edit, dialog_title, file_filter))
        browse_button.setFixedWidth(100) # Fixed width for consistency

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: line_edit.clear())
        clear_button.setFixedWidth(80)

        h_layout.addWidget(label)
        h_layout.addWidget(line_edit)
        h_layout.addWidget(browse_button)
        h_layout.addWidget(clear_button)
        parent_layout.addLayout(h_layout)
        return line_edit # Return the QLineEdit for later access

    def _apply_stylesheet(self):
        """Applies a simple, modern stylesheet to the application."""
        stylesheet = """
        QWidget {
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
            font-size: 14px;
            color: #333;
        }
        QPushButton {
            background-color: #007bff; /* Blue */
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        QLineEdit {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 8px;
            background-color: #f8f8f8;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 10px;
            padding-top: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            margin-left: 5px;
            color: #007bff;
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 5px;
            text-align: center;
            background-color: #e0e0e0;
            color: #333;
        }
        QProgressBar::chunk {
            background-color: #28a745; /* Green */
            border-radius: 5px;
        }
        QTextEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            background-color: #fdfdfd;
            font-family: "Consolas", "Courier New", monospace; /* Monospace font for logs */
            font-size: 12px;
            color: #555;
        }
        QLabel {
            font-weight: bold;
        }
        """
        self.setStyleSheet(stylesheet)
        # Apply specific button styles that override the general QPushButton style
        self.createButton.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; font-size: 16px;") # Green
        self.cancelButton.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; font-size: 16px;") # Red
        # Re-apply default browse button style as it's part of the template
        for widget in self.findChildren(QPushButton):
            if "Browse" in widget.text() or "Clear" in widget.text():
                widget.setStyleSheet("background-color: #6c757d; color: white; border: none; padding: 5px 10px; border-radius: 4px;") # Greyish

    def get_folder_path_input(self, line_edit, dialog_title, file_filter):
        folder_selected = QFileDialog.getExistingDirectory(self, dialog_title)
        if folder_selected:
            line_edit.setText(os.path.normpath(folder_selected)) # Normalize path

    def get_folder_path_output(self, line_edit, dialog_title, file_filter):
        folder_selected = QFileDialog.getExistingDirectory(self, dialog_title)
        if folder_selected:
            line_edit.setText(os.path.normpath(folder_selected))

    def get_compliance_matrix(self, line_edit, dialog_title, file_filter):
        file_path, _ = QFileDialog.getOpenFileName(self, dialog_title, "", file_filter)
        if file_path:
            line_edit.setText(os.path.normpath(file_path))

    def _validate_inputs(self):
        """Validates all necessary input fields before starting processing."""
        folder_input = self.folderPath_input.text()
        folder_output = self.folderPath_output.text()
        CM_file = self.CM_path.text()

        if not os.path.isdir(folder_input):
            QMessageBox.warning(self, 'Input Error', 'Please select a valid Input Folder.')
            self.logger.warning(f"Invalid input folder: {folder_input}")
            return False

        if not os.path.isdir(folder_output):
            QMessageBox.warning(self, 'Input Error', 'Please select a valid Output Folder.')
            self.logger.warning(f"Invalid output folder: {folder_output}")
            return False

        if not os.path.exists(CM_file):
            QMessageBox.warning(self, 'Input Error', 'Please select a valid Compliance Matrix file.')
            self.logger.warning(f"CM file not found: {CM_file}")
            return False

        if CM_TEMPLATE_NAME not in CM_file:
            QMessageBox.information(self, 'Error Message',
                                    f'The chosen file is not the correct Compliance Matrix Template (expected "{CM_TEMPLATE_NAME}"). Please select the correct file.')
            self.logger.error(f"Incorrect CM template selected: {CM_file}")
            return False
        return True

    def start_processing(self):
        """Initiates the processing in a separate thread."""
        if not self._validate_inputs():
            return

        # Disable UI elements during processing
        self._set_ui_enabled(False)
        self.log_display.clear() # Clear previous logs
        self.progressBar.setValue(0)
        self.logger.info("Validation successful. Starting processing...")

        # Create a QThread and move the worker to it
        self._worker_thread = QThread()
        self._worker = ProcessingWorker(
            self.folderPath_input.text(),
            self.folderPath_output.text(),
            self.CM_path.text()
        )
        self._worker.moveToThread(self._worker_thread)

        # Connect signals from worker to GUI slots
        self._worker.progress_updated.connect(self.progressBar.setValue)
        self._worker.log_message.connect(self.handle_log_message)
        self._worker.finished.connect(self.on_processing_finished)
        self._worker.error_occurred.connect(self.on_processing_error)

        # Connect thread signals
        self._worker_thread.started.connect(self._worker.run) # Start worker's run method when thread starts
        self._worker_thread.finished.connect(self._worker_thread.deleteLater) # Clean up thread object
        self._worker_thread.finished.connect(self._worker.deleteLater) # Clean up worker object

        # Start the thread
        self._worker_thread.start()
        self.logger.info("Worker thread started.")


    def cancel_processing(self):
        """Sends a signal to the worker to stop processing."""
        if self._worker and self._worker_thread and self._worker_thread.isRunning():
            self._worker.stop()
            self._worker_thread.quit() # Request the thread to quit
            self._worker_thread.wait() # Wait for the thread to finish
            self.logger.warning("Processing cancelled by user.")
            QMessageBox.information(self, "Processing Cancelled", "The processing has been stopped.")
            self._set_ui_enabled(True) # Re-enable UI
            self.progressBar.setValue(0) # Reset progress
            self.log_display.append("<span style='color: orange;'>Processing cancelled by user.</span>")

    def _set_ui_enabled(self, enabled):
        """Enables/disables relevant UI elements."""
        self.folderPath_input.setEnabled(enabled)
        self.folderPath_output.setEnabled(enabled)
        self.CM_path.setEnabled(enabled)
        for button in self.findChildren(QPushButton):
            if "Browse" in button.text() or "Clear" in button.text():
                button.setEnabled(enabled)
        self.createButton.setEnabled(enabled)
        self.cancelButton.setEnabled(not enabled) # Cancel button is enabled when processing, disabled otherwise


    # --- Slots for Worker Signals ---
    def handle_log_message(self, message, level):
        """Receives log messages from worker and displays them in QTextEdit."""
        color = "black"
        if level == "info":
            color = "blue"
        elif level == "warning":
            color = "orange"
        elif level == "error":
            color = "red"
        self.log_display.append(f"<span style='color: {color};'>{message}</span>")

    def on_processing_finished(self, message):
        """Called when worker successfully finishes."""
        self.logger.info(f"Processing finished: {message}")
        QMessageBox.information(self, 'Processing Completed', message)
        self._set_ui_enabled(True) # Re-enable UI
        self.progressBar.setValue(0) # Reset progress
        self.log_display.append("<span style='color: green;'>Processing completed successfully!</span>")


    def on_processing_error(self, error_message, title):
        """Called when worker encounters a critical error."""
        self.logger.error(f"Processing error: {error_message}")
        QMessageBox.critical(self, title, error_message)
        self._set_ui_enabled(True) # Re-enable UI
        self.progressBar.setValue(0) # Reset progress
        self.log_display.append(f"<span style='color: red;'>Error: {error_message}</span>")


    def closeEvent(self, event):
        """Custom close event handling."""
        if self._worker_thread and self._worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirm Close',
                                         'Processing is still running. Do you want to cancel and exit?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_processing() # Attempt to cancel first
                event.accept()
            else:
                event.ignore()
        else:
            reply = QMessageBox.question(self, 'Closing', 'Really close?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()


if __name__ == '__main__':
    # Initial logging setup for main process (can be overridden by GUI handler)
    logging.basicConfig(filename='application_main.log', level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    ex = RequirementBotApp()
    ex.show()
    sys.exit(app.exec())