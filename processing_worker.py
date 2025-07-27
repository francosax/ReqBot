import os
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread
import pandas as pd

# Assuming these are your core logic functions
from RB_coordinator import requirement_bot
from config_RB import load_keyword_config
from get_all_files import get_all

# Set up logging for the worker
worker_logger = logging.getLogger(__name__)

class ProcessingWorker(QObject):
    # Signals to communicate with the GUI thread
    progress_updated = Signal(int)
    log_message = Signal(str, str)  # Message, Level (e.g., "info", "error")
    finished = Signal(str) # Message on successful completion
    error_occurred = Signal(str, str) # Error message, title for MessageBox

    def __init__(self, folder_input, folder_output, CM_file):
        super().__init__()
        self._folder_input = folder_input
        self._folder_output = folder_output
        self._CM_file = CM_file
        self._is_running = True

    def run(self):
        """
        This method will be executed in the separate QThread.
        Contains the core 'do_stuff' logic.
        """
        self.log_message.emit("Processing started...", "info")
        try:
            parole_chiave = load_keyword_config()
            self.log_message.emit(f"Keywords loaded: {', '.join(parole_chiave)}", "info")

            lista_file = get_all(self._folder_input, 'pdf')
            filtered_files = [file for file in lista_file if "Tagged" not in file]
            total_files = len(filtered_files)

            if total_files == 0:
                self.log_message.emit("No untagged PDF files found in the input folder. Processing finished.", "warning")
                self.finished.emit("No PDFs found to process.")
                return

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
                        self.log_message.emit("Processing cancelled.", "warning")
                        break

                    start_time = datetime.now()
                    try:
                        self.log_message.emit(f"Processing PDF: {os.path.basename(file_path)}", "info")
                        df = requirement_bot(file_path, self._CM_file, parole_chiave, self._folder_output)
                        self.log_message.emit(f"Processed {os.path.basename(file_path)}. Found {len(df)} requirements.", "info")

                    except Exception as e:
                        worker_logger.exception(f"Error processing file {file_path}: {e}")
                        self.log_message.emit(f"Error processing {os.path.basename(file_path)}: {e}", "error")
                        continue # Skip this file and continue with the next

                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    total_requirements += len(df)
                    total_working_time += round(len(df) * (5 / 60), 2)

                    f.write("PDF Name: " + os.path.basename(file_path) + "\n")
                    f.write("Number of Requirements: " + str(len(df)) + "\n")
                    f.write("Estimated Analysis time: " + str(round(len(df) * (5 / 60), 2)) + " hrs" + "\n")
                    f.write("Execution Time: " + str(execution_time.total_seconds()) + " seconds\n\n")

                    # Emit progress update
                    progress_value = int(((i + 1) / total_files) * 100)
                    self.progress_updated.emit(progress_value)

                # Write final summary to the log file
                f.write("--- Summary ---\n")
                f.write("Total Requirements: " + str(total_requirements) + "\n")
                f.write("Total Estimated Analysis time: " + str(total_working_time) + " hrs\n")
                self.log_message.emit(f"Processing loop finished. Total requirements found: {total_requirements}", "info")


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