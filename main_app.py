import logging
import os
import sys
from datetime import datetime

# --- PySide6 Imports ---
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QFileDialog,
    QMessageBox, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout,
    QGroupBox, QTextEdit, QSizePolicy, QDoubleSpinBox, QSlider,
    QComboBox  # NEW: For recent paths dropdown
)
from PySide6.QtCore import Qt, QThread # Import QThread
from PySide6.QtGui import QIcon # For potentially adding icons



# Import the worker class
from processing_worker import ProcessingWorker # <--- NEW IMPORT

# Import version information (single source of truth)
from version import GUI_VERSION

# Import recent projects manager (NEW)
from recent_projects import get_recents_manager

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
        self.recents_manager = get_recents_manager()  # NEW: Initialize recents manager
        self.init_logging() # Setup logging before UI
        self.init_ui()
        self._apply_stylesheet() # Apply stylesheet after UI is initialized
        self._load_recent_paths()  # NEW: Load recent paths into dropdowns

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
        self.setWindowTitle(f'RequirementBot {GUI_VERSION}')
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

        # --- Settings Group Box ---
        settings_group_box = QGroupBox("Processing Settings")
        settings_layout = QVBoxLayout()

        # Confidence Threshold Control
        confidence_layout = QHBoxLayout()
        confidence_label = QLabel("Minimum Confidence Threshold:")
        confidence_label.setToolTip("Requirements with confidence scores below this threshold will be filtered out.\nRange: 0.0 (no filtering) to 1.0 (very strict).\nRecommended: 0.4-0.6")

        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.0, 1.0)
        self.confidence_spinbox.setSingleStep(0.05)
        self.confidence_spinbox.setValue(0.5)  # Default value
        self.confidence_spinbox.setDecimals(2)
        self.confidence_spinbox.setFixedWidth(100)
        self.confidence_spinbox.setToolTip("Set the minimum confidence threshold (0.0 - 1.0)")

        # Add a slider for easier adjustment
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)  # 0-100 for percentage
        self.confidence_slider.setValue(50)  # Default 0.5 = 50%
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.setToolTip("Drag to adjust confidence threshold")

        # Connect slider and spinbox to sync
        self.confidence_slider.valueChanged.connect(
            lambda value: self.confidence_spinbox.setValue(value / 100.0)
        )
        self.confidence_spinbox.valueChanged.connect(
            lambda value: self.confidence_slider.setValue(int(value * 100))
        )

        # Info label showing current threshold value
        self.confidence_info_label = QLabel("(0.50 = 50% confidence)")
        self.confidence_info_label.setStyleSheet("color: #666; font-size: 12px;")
        self.confidence_spinbox.valueChanged.connect(
            lambda value: self.confidence_info_label.setText(
                f"({value:.2f} = {int(value * 100)}% confidence)"
            )
        )

        confidence_layout.addWidget(confidence_label)
        confidence_layout.addWidget(self.confidence_spinbox)
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_info_label)
        confidence_layout.addStretch()

        settings_layout.addLayout(confidence_layout)
        settings_group_box.setLayout(settings_layout)
        main_layout.addWidget(settings_group_box)

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
        """
        Helper to create a QLabel, QComboBox (with recent paths), and Browse/Clear buttons.

        NEW: Uses QComboBox instead of QLineEdit to show recent paths dropdown.
        """
        h_layout = QHBoxLayout()
        label = QLabel(label_text)

        # NEW: Use QComboBox instead of QLineEdit for recent paths support
        combo_box = QComboBox(self)
        combo_box.setEditable(True)  # Allow typing custom paths
        combo_box.setInsertPolicy(QComboBox.NoInsert)  # Don't auto-add to list when typing
        combo_box.lineEdit().setPlaceholderText(f"Select recent or browse for {label_text.lower().replace(':', '')}...")
        combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda: select_func(combo_box, dialog_title, file_filter))
        browse_button.setFixedWidth(100) # Fixed width for consistency

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: combo_box.clearEditText())
        clear_button.setFixedWidth(80)

        h_layout.addWidget(label)
        h_layout.addWidget(combo_box)
        h_layout.addWidget(browse_button)
        h_layout.addWidget(clear_button)
        parent_layout.addLayout(h_layout)
        return combo_box # Return the QComboBox for later access

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

    def get_folder_path_input(self, combo_box, dialog_title, file_filter):
        """
        Browse for input folder and update combo box.

        NEW: Works with QComboBox and adds to recent paths.
        """
        folder_selected = QFileDialog.getExistingDirectory(self, dialog_title)
        if folder_selected:
            normalized_path = os.path.normpath(folder_selected)
            combo_box.setEditText(normalized_path)  # Set text in editable combo box
            # Add to recent paths (will be saved when processing starts successfully)

    def get_folder_path_output(self, combo_box, dialog_title, file_filter):
        """
        Browse for output folder and update combo box.

        NEW: Works with QComboBox and adds to recent paths.
        """
        folder_selected = QFileDialog.getExistingDirectory(self, dialog_title)
        if folder_selected:
            normalized_path = os.path.normpath(folder_selected)
            combo_box.setEditText(normalized_path)
            # Add to recent paths (will be saved when processing starts successfully)

    def get_compliance_matrix(self, combo_box, dialog_title, file_filter):
        """
        Browse for compliance matrix file and update combo box.

        NEW: Works with QComboBox and adds to recent paths.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, dialog_title, "", file_filter)
        if file_path:
            normalized_path = os.path.normpath(file_path)
            combo_box.setEditText(normalized_path)
            # Add to recent paths (will be saved when processing starts successfully)

    def _load_recent_paths(self):
        """
        Load recent paths from RecentsManager and populate combo boxes.

        NEW: Called on GUI startup to populate recent paths dropdowns.
        """
        # Load recent input folders
        recent_inputs = self.recents_manager.get_input_folders()
        for path in recent_inputs:
            self.folderPath_input.addItem(path)

        # Load recent output folders
        recent_outputs = self.recents_manager.get_output_folders()
        for path in recent_outputs:
            self.folderPath_output.addItem(path)

        # Load recent CM files
        recent_cms = self.recents_manager.get_cm_files()
        for path in recent_cms:
            self.CM_path.addItem(path)

        # Log loaded recents
        self.logger.info(f"Loaded {len(recent_inputs)} recent input folders, "
                        f"{len(recent_outputs)} recent output folders, "
                        f"{len(recent_cms)} recent CM files")

    def _validate_inputs(self):
        """
        Validates all necessary input fields before starting processing.

        NEW: Uses currentText() for QComboBox widgets.
        """
        folder_input = self.folderPath_input.currentText()  # NEW: currentText() for QComboBox
        folder_output = self.folderPath_output.currentText()
        CM_file = self.CM_path.currentText()

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

        # Get current paths
        folder_input = self.folderPath_input.currentText()  # NEW: currentText() for QComboBox
        folder_output = self.folderPath_output.currentText()
        CM_file = self.CM_path.currentText()

        # NEW: Save current paths to recent projects
        self.recents_manager.add_project(folder_input, folder_output, CM_file)
        self.logger.info("Saved current paths to recent projects")

        # Get confidence threshold from UI
        confidence_threshold = self.confidence_spinbox.value()
        self.logger.info(f"Using confidence threshold: {confidence_threshold:.2f}")

        # Create a QThread and move the worker to it
        self._worker_thread = QThread()
        self._worker = ProcessingWorker(
            folder_input,
            folder_output,
            CM_file,
            confidence_threshold  # Pass confidence threshold to worker
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
        self.confidence_spinbox.setEnabled(enabled)  # Enable/disable confidence controls
        self.confidence_slider.setEnabled(enabled)
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