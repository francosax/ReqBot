import logging
import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QFileDialog, QMessageBox, QVBoxLayout, \
    QLabel, QProgressBar

from RB_coordinator import requirement_bot
from config_RB import load_keyword_config
from get_all_files import get_all


class RequirementBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('RequirementBot 1.2')
        self.setGeometry(300, 300, 400, 200)

        self.folderPath_input = QLineEdit(self)
        self.folderPath_output = QLineEdit(self)
        self.CM_path = QLineEdit(self)

        self.inputFolderButton = QPushButton('Input Folder', self)
        self.inputFolderButton.setStyleSheet("background-color:blue")
        self.outputFolderButton = QPushButton('Output Folder', self)
        self.outputFolderButton.setStyleSheet("background-color:blue")
        self.loadCMButton = QPushButton('Load CM', self)
        self.loadCMButton.setStyleSheet("background-color:#008000 ")
        self.createButton = QPushButton('CREATE', self)
        self.createButton.setStyleSheet("background-color:red ")

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
        try:
            # folder_input = folderPath_input.get()
            folder_input = self.folderPath_input.text()
            # folder_output = folderPath_output.get()
            folder_output = self.folderPath_output.text()
            # CM_file = CM_path.get()
            CM_file = self.CM_path.text()
            parole_chiave = load_keyword_config()

            if 'Compliance_Matrix_Template_rev001.xlsx' not in CM_file:
                print('yo')
                QMessageBox.information(self, 'Error Message',
                                        'The chosen file is not the correct Compliance Matrix Template. Please select '
                                        'the correct file.')

                logging.error(
                    "The chosen file is not the correct Compliance Matrix Template.")
                return

            lista_file = get_all(folder_input, 'pdf')
            filtered_files = [file for file in lista_file if "Tagged" not in file]
            total_files = len(filtered_files)

            total_requirements = 0
            total_working_time = 0

            with open(folder_output + "/LOG.txt", "w") as f:
                f.write("Keyword: " + ', '.join(parole_chiave) + "\n\n")

                progress = 0

                for i in lista_file:
                    if "Tagged" not in i:
                        start_time = datetime.now()
                        try:
                            df = requirement_bot(i, CM_file, parole_chiave, folder_output)
                        except Exception as e:
                            logging.error(f"Error processing file {i}: {e}")
                            continue  # Skip this file and continue with the next

                        end_time = datetime.now()
                        execution_time = end_time - start_time
                        total_requirements += len(df)
                        total_working_time += round(len(df) * (5 / 60), 2)

                        # Write the PDF name, number of requirements, and computation time to the text file
                        f.write("PDF Name: " + os.path.basename(i) + "\n")
                        f.write("Number of Requirements: " + str(len(df)) + "\n")
                        f.write("Estimated Analysis time: " + str(round(len(df) * (5 / 60), 2)) + " hrs" + "\n")
                        f.write("Execution Time: " + str(execution_time) + " seconds\n\n")

                        progress += 1

                        progress_value = (progress / total_files) * 100  # Calculate progress as a percentage
                        self.progressBar.setValue(int(progress_value))

                        # self.progressBar.setValue(i)  # Assuming 'i' is the current progress value
                        QApplication.processEvents()

                # Write the total requirements and total working time to the text file
                f.write("Total Requirements: " + str(total_requirements) + "\n")
                f.write("Total Estimated Analysis time: " + str(total_working_time) + " hrs\n")

            # messagebox.showinfo("Alert Message", "Completed")
            QMessageBox.information(self, 'Processing Completed', 'The processing has been completed successfully.')
        except Exception as e:
            logging.error(f"An error occurred during processing: {e}")

    def closeEvent(self, event):
        # Custom close event handling
        if QMessageBox.question(self, 'Closing', 'Really close?') == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)  # Ensure the application quits when the last window is closed
    ex = RequirementBotApp()
    ex.show()
    sys.exit(app.exec_())
