import os
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread
import pandas as pd

# Assuming these are your core logic functions
from RB_coordinator import requirement_bot
from config_RB import load_keyword_config
from get_all_files import get_all
from report_generator import create_processing_report

# v3.0: Database services
from database.services.project_service import ProjectService
from database.services.session_service import ProcessingSessionService

# Set up logging for the worker
worker_logger = logging.getLogger(__name__)

class ProcessingWorker(QObject):
    # Signals to communicate with the GUI thread
    progress_updated = Signal(int)
    progress_detail_updated = Signal(str)  # v2.3: Detailed progress message (file, step)
    log_message = Signal(str, str)  # Message, Level (e.g., "info", "error")
    finished = Signal(str) # Message on successful completion
    error_occurred = Signal(str, str) # Error message, title for MessageBox

    def __init__(self, folder_input, folder_output, CM_file, confidence_threshold=0.5, keywords=None):
        super().__init__()
        self._folder_input = folder_input
        self._folder_output = folder_output
        self._CM_file = CM_file
        self._confidence_threshold = confidence_threshold  # Store confidence threshold
        self._keywords = keywords  # v2.2: Optional keywords set
        self._is_running = True

    def run(self):
        """
        This method will be executed in the separate QThread.
        Contains the core 'do_stuff' logic.
        """
        self.log_message.emit("Processing started...", "info")
        self.log_message.emit(f"Confidence threshold: {self._confidence_threshold:.2f}", "info")
        self.progress_detail_updated.emit("Initializing processing...")  # v2.3: Detailed progress

        # Create processing report instance
        report = create_processing_report()
        report.start_processing()

        # v3.0: Create or retrieve project
        project = None
        processing_session = None
        try:
            # Generate project name from input folder
            project_name = os.path.basename(self._folder_input.rstrip(os.sep))
            if not project_name:
                project_name = "ReqBot Project"

            # Get or create project
            project = ProjectService.get_or_create_project(
                name=project_name,
                input_folder_path=self._folder_input,
                output_folder_path=self._folder_output,
                compliance_matrix_template=self._CM_file
            )

            if project:
                self.log_message.emit(f"Project initialized: {project.name} (ID: {project.id})", "info")
            else:
                self.log_message.emit("Warning: Could not initialize database project", "warning")
        except Exception as e:
            worker_logger.error(f"Failed to initialize project: {str(e)}")
            self.log_message.emit("Warning: Database project creation failed, continuing without persistence", "warning")

        try:
            # v2.2: Use provided keywords if available, otherwise load from config
            if self._keywords:
                parole_chiave = self._keywords
                self.log_message.emit(f"Using selected keyword profile: {', '.join(parole_chiave)}", "info")
            else:
                parole_chiave = load_keyword_config()
                self.log_message.emit(f"Keywords loaded from config: {', '.join(parole_chiave)}", "info")

            # Set report metadata
            report.set_metadata(list(parole_chiave), self._confidence_threshold)

            lista_file = get_all(self._folder_input, 'pdf')
            filtered_files = [file for file in lista_file if "Tagged" not in file]
            total_files = len(filtered_files)

            if total_files == 0:
                warning_msg = "No untagged PDF files found in the input folder. Processing finished."
                self.log_message.emit(warning_msg, "warning")
                self.progress_detail_updated.emit("No PDF files found")  # v2.3
                report.add_warning(warning_msg)
                self.finished.emit("No PDFs found to process.")
                return

            # v2.3: Emit detail about files found
            self.progress_detail_updated.emit(f"Found {total_files} PDF file(s) to process")

            # v3.0: Create processing session
            if project:
                try:
                    processing_session = ProcessingSessionService.create_session(
                        project_id=project.id,
                        keywords_used=', '.join(parole_chiave),
                        confidence_threshold=self._confidence_threshold
                    )
                    if processing_session:
                        self.log_message.emit(f"Processing session created (ID: {processing_session.id})", "info")
                except Exception as e:
                    worker_logger.error(f"Failed to create processing session: {str(e)}")
                    self.log_message.emit("Warning: Could not create processing session", "warning")

            total_requirements = 0
            total_working_time = 0

            # Ensure the output directory exists
            os.makedirs(self._folder_output, exist_ok=True)
            log_file_path = os.path.join(self._folder_output, "LOG.txt")

            with open(log_file_path, "w") as f:
                f.write("Keyword: " + ', '.join(parole_chiave) + "\n\n")
                self.log_message.emit(f"Log file created at: {log_file_path}", "info")

                for i, file_path in enumerate(filtered_files):
                    if not self._is_running: # Allow stopping the process
                        cancel_msg = "Processing cancelled."
                        self.log_message.emit(cancel_msg, "warning")
                        report.add_warning(cancel_msg)
                        break

                    # Calculate base progress for this file (0-90% range, leaving 10% for report)
                    file_base_progress = int((i / total_files) * 90)
                    file_progress_range = int((1 / total_files) * 90)

                    # Update progress: Starting file
                    self.progress_updated.emit(file_base_progress)

                    start_time = datetime.now()
                    file_warnings = []
                    try:
                        # Step 1: Processing PDF (25% of file progress)
                        filename = os.path.basename(file_path)
                        self.log_message.emit(f"[{i+1}/{total_files}] Analyzing PDF: {filename}", "info")
                        self.progress_detail_updated.emit(f"File {i+1}/{total_files}: Analyzing {filename}...")  # v2.3
                        self.progress_updated.emit(file_base_progress + int(file_progress_range * 0.25))

                        # Step 2: Extracting requirements (main processing in requirement_bot)
                        # This includes PDF analysis, Excel writing, BASIL export, and highlighting
                        # v3.0: Pass project to requirement_bot for database persistence
                        self.progress_detail_updated.emit(f"File {i+1}/{total_files}: Extracting requirements from {filename}...")  # v2.3
                        df = requirement_bot(
                            file_path,
                            self._CM_file,
                            parole_chiave,
                            self._folder_output,
                            self._confidence_threshold,
                            project=project  # v3.0: Pass project for database persistence
                        )

                        # Step 3: File completed (100% of file progress)
                        self.progress_updated.emit(file_base_progress + file_progress_range)
                        self.progress_detail_updated.emit(f"File {i+1}/{total_files}: Completed {filename} ({len(df)} requirements)")  # v2.3
                        self.log_message.emit(f"[{i+1}/{total_files}] Completed {os.path.basename(file_path)}. Found {len(df)} requirements.", "info")

                        # Calculate average confidence for this file
                        avg_confidence = df['Confidence'].mean() if 'Confidence' in df.columns and len(df) > 0 else 0.0

                        # Check for low confidence warnings
                        if avg_confidence < 0.6 and len(df) > 0:
                            low_conf_msg = f"Low average confidence ({avg_confidence:.2f}) in {os.path.basename(file_path)}"
                            file_warnings.append(low_conf_msg)
                            report.add_warning(low_conf_msg)

                    except Exception as e:
                        worker_logger.exception(f"Error processing file {file_path}: {e}")
                        error_msg = f"Error processing {os.path.basename(file_path)}: {str(e)}"
                        self.log_message.emit(error_msg, "error")
                        report.add_error(error_msg)

                        # Still update progress even on error
                        self.progress_updated.emit(file_base_progress + file_progress_range)
                        continue # Skip this file and continue with the next

                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    total_requirements += len(df)
                    total_working_time += round(len(df) * (5 / 60), 2)

                    # Add file result to report
                    report.add_file_result(
                        filename=os.path.basename(file_path),
                        req_count=len(df),
                        avg_confidence=avg_confidence,
                        execution_time_seconds=execution_time.total_seconds(),
                        file_warnings=file_warnings
                    )

                    f.write("PDF Name: " + os.path.basename(file_path) + "\n")
                    f.write("Number of Requirements: " + str(len(df)) + "\n")
                    f.write("Average Confidence: " + str(round(avg_confidence, 3)) + "\n")
                    f.write("Estimated Analysis time: " + str(round(len(df) * (5 / 60), 2)) + " hrs" + "\n")
                    f.write("Execution Time: " + str(execution_time.total_seconds()) + " seconds\n\n")

                # Write final summary to the log file
                f.write("--- Summary ---\n")
                f.write("Total Requirements: " + str(total_requirements) + "\n")
                f.write("Total Estimated Analysis time: " + str(total_working_time) + " hrs\n")
                self.log_message.emit(f"Processing loop finished. Total requirements found: {total_requirements}", "info")

            # Mark end of processing
            report.end_processing()

            # v3.0: Complete processing session
            if processing_session:
                try:
                    # Calculate average confidence across all files
                    overall_avg_confidence = total_requirements / total_files if total_files > 0 else 0.0

                    ProcessingSessionService.complete_session(
                        session_id=processing_session.id,
                        documents_processed=total_files,
                        requirements_extracted=total_requirements,
                        report_output_path=None  # Will be set after report generation
                    )
                    self.log_message.emit(f"Processing session completed (ID: {processing_session.id})", "info")
                except Exception as e:
                    worker_logger.error(f"Failed to complete processing session: {str(e)}")
                    self.log_message.emit("Warning: Could not complete processing session", "warning")

            # Generate HTML report
            self.progress_updated.emit(95)
            self.progress_detail_updated.emit("Generating processing report...")  # v2.3
            self.log_message.emit("Generating processing report...", "info")
            report_date = datetime.now().strftime("%Y.%m.%d_%H%M%S")
            report_path = os.path.join(self._folder_output, f"{report_date}_Processing_Report.html")

            if report.generate_html_report(report_path):
                self.log_message.emit(f"HTML report generated: {report_path}", "info")

                # v3.0: Update session with report path
                if processing_session:
                    try:
                        proc_session = ProcessingSessionService.get_session_by_id(processing_session.id)
                        if proc_session:
                            proc_session.report_output_path = report_path
                    except Exception as e:
                        worker_logger.error(f"Failed to update session with report path: {str(e)}")
            else:
                warning_msg = "Failed to generate HTML report"
                self.log_message.emit(warning_msg, "warning")
                report.add_warning(warning_msg)

            self.progress_updated.emit(100)
            self.finished.emit('The processing has been completed successfully.')

        except FileNotFoundError as e:
            worker_logger.error(f"File Not Found Error: {e}")
            self.error_occurred.emit(f"The required file was not found: {e}", "File Not Found")
        except Exception as e:
            worker_logger.exception("An unexpected error occurred during processing.")
            self.error_occurred.emit(f"An unexpected error occurred: {e}", "Application Error")
        finally:
            self.progress_updated.emit(0) # Reset progress bar
            self._is_running = False # Ensure worker state is reset

    def stop(self):
        """Allows gracefully stopping the worker thread."""
        self._is_running = False