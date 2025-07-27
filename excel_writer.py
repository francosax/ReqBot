import os
from openpyxl import load_workbook, Workbook # Import Workbook
from openpyxl.styles import PatternFill
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
import pandas as pd # You'll need pandas to create a DataFrame easily

def write_excel_file(df, excel_file):
    """
    Loads an Excel workbook, updates a specific sheet with data from a DataFrame,
    applies conditional formatting based on priority, adds data validations,
    and inserts formulas.

    Args:
        df (pandas.DataFrame): The DataFrame containing data to write.
                               Expected columns: 'Page', 'Label Number', 'Description', 'Priority'.
                               The DataFrame index is used for 'A' column.
        excel_file (str): The path to the existing Excel file to be updated.
    """
    try:
        # Carica il workbook e accedi al foglio di lavoro da aggiornare
        book = load_workbook(excel_file)
        # Ensure the sheet exists, otherwise this will raise a KeyError
        if 'MACHINE COMP. MATRIX' not in book.sheetnames:
            print(f"Error: Sheet 'MACHINE COMP. MATRIX' not found in {excel_file}")
            return

        writer = book['MACHINE COMP. MATRIX']

        fill_high = PatternFill(start_color=Color(rgb='00FF0000'), end_color=Color(rgb='00FF0000'), fill_type='solid') # Red
        fill_medium = PatternFill(start_color=Color(rgb='00FFFF00'), end_color=Color(rgb='00FFFF00'), fill_type='solid') # Yellow
        fill_low = PatternFill(start_color=Color(rgb='0000FF00'), end_color=Color(rgb='0000FF00'), fill_type='solid') # Green

        # Update the Compliance Matrix with the requirements
        # Starting from row 5
        for i, (value1, value2, value3, value4, value5) in enumerate(
                zip(df.index, df['Page'], df['Label Number'], df['Description'], df['Priority']), start=5):

            writer[f'A{i}'] = value1         # df.index
            writer[f'B{i}'] = value2         # Page
            writer[f'C{i}'] = value3         # Label Number
            writer[f'D{i}'] = value4         # Description
            writer[f'H{i}'] = value5         # Priority

            # Apply fill based on priority
            priority = str(value5).lower() # Ensure priority is string and lowercase for comparison
            if priority == 'high':
                writer[f'H{i}'].fill = fill_high
            elif priority == 'medium':
                writer[f'H{i}'].fill = fill_medium
            elif priority == 'low':
                writer[f'H{i}'].fill = fill_low

        # Aggiungi qui le definizioni della Data Validation
        # Max row for Excel is 1048576, using this for full column validation
        dv1 = DataValidation(type="list",
                             formula1='"Technical,Procedure,Legal,SW,HW,Safety,Documentation,Safety,Warning,N.A."',
                             allow_blank=True)
        dv1.add('I5:I1048576')

        dv2 = DataValidation(type="list", formula1='"Machine,Product,Company"', allow_blank=True)
        dv2.add('J5:J1048576')

        dv3 = DataValidation(type="list", formula1='"Concept,UTM,UTS,UTE,SW,Testing,Process,Assembly,Logistic,Quality,PM,Purchasing,Sales,Service"', allow_blank=True)
        dv3.add('K5:K1048576')

        dv4 = DataValidation(type="list", formula1='"Approved,Rejected,In discussion,Acquired"', allow_blank=True)
        dv4.add('M5:M1048576')

        dv5 = DataValidation(type="list", formula1='"yes,partially,no"', allow_blank=True)
        dv5.add('N5:N1048576')

        dv6 = DataValidation(type="list", formula1='"easy,medium,hard"', allow_blank=True)
        dv6.add('O5:O1048576')

        dv7 = DataValidation(type="list", formula1='"completed,on going,blocked,failed"', allow_blank=True)
        dv7.add('U5:U1048576')

        dv8 = DataValidation(type="list", formula1='"compliant,not compliant,partially compliant"', allow_blank=True)
        dv8.add('W5:W1048576')

        writer.add_data_validation(dv1)
        writer.add_data_validation(dv2)
        writer.add_data_validation(dv3)
        writer.add_data_validation(dv4)
        writer.add_data_validation(dv5)
        writer.add_data_validation(dv6)
        writer.add_data_validation(dv7)
        writer.add_data_validation(dv8)

        # Apply formulas
        for i in range(5, writer.max_row + 1):
            col_h = get_column_letter(8)  # H (Priority)
            col_m = get_column_letter(13) # M (Status - Approved/Rejected/In discussion/Acquired)
            col_n = get_column_letter(14) # N (Completeness - yes/partially/no)
            col_o = get_column_letter(15) # O (Difficulty - easy/medium/hard)
            col_p = get_column_letter(16) # P (Output column for formula)

            # Construct the formula string. Be careful with double quotes inside
            # the formula if they are part of string literals for Excel.
            # Using single quotes for Python string and escaping double quotes for Excel string literals.
            formula = (
                f'=ROUND((('
                f'(IF({col_h}{i}="high", 3, IF({col_h}{i}="medium", 2, IF({col_h}{i}="low", 1, 0))) * 4/3) + ' # Priority
                f'(IF({col_n}{i}="yes", 1, IF({col_n}{i}="partially", 2, IF({col_n}{i}="no", 3, 0))) * 3/3) + ' # Completeness
                f'(IF({col_o}{i}="hard", 3, IF({col_o}{i}="medium", 2, IF({col_o}{i}="easy", 1, 0))) * 2/3)' # Difficulty
                f') - 3) * '
                f'IF({col_m}{i}="Approved", 1, IF({col_m}{i}="Rejected", 0, IF({col_m}{i}="In discussion", 1, IF({col_m}{i}="Acquired", 1, 0))))'
                f'), 2)'
            )

            writer[f'{col_p}{i}'].value = None  # Clear existing value
            writer[f'{col_p}{i}'].value = formula  # Insert the formula
            writer[f'{col_p}{i}'].number_format = '0' # Ensure it's formatted as a number

        # Salva il workbook
        book.save(excel_file)
        print(f"Excel file '{excel_file}' updated successfully.")

    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    excel_template_path = "template_compliance_matrix.xlsx"

    print(f"Script is running from: {os.getcwd()}")
    print(f"Attempting to create/update file at: {os.path.abspath(excel_template_path)}")

    if not os.path.exists(excel_template_path):
        print(f"Creating a dummy template: {excel_template_path}")
        dummy_book = Workbook() # <--- CORRECTED: Use openpyxl.Workbook() for new workbook
        dummy_book.create_sheet('MACHINE COMP. MATRIX', 0) # Create at the first position
        # Remove the default 'Sheet' created by Workbook() constructor
        if 'Sheet' in dummy_book.sheetnames:
            del dummy_book['Sheet']

        dummy_sheet = dummy_book['MACHINE COMP. MATRIX']
        # Add some headers that match your expected data structure
        dummy_sheet['A1'] = "REQ_ID"
        dummy_sheet['B1'] = "Page"
        dummy_sheet['C1'] = "Label Number"
        dummy_sheet['D1'] = "Description"
        dummy_sheet['H1'] = "Priority"
        dummy_sheet['M1'] = "Status"
        dummy_sheet['N1'] = "Completeness"
        dummy_sheet['O1'] = "Difficulty"
        dummy_sheet['P1'] = "Calculated Value" # For the formula output

        # Add a few rows of dummy data starting from row 5
        dummy_sheet['A5'] = "DUMMY-001"
        dummy_sheet['B5'] = 1
        dummy_sheet['C5'] = "L001"
        dummy_sheet['D5'] = "Sample Req Desc 1"
        dummy_sheet['H5'] = "high"
        dummy_sheet['M5'] = "Approved"
        dummy_sheet['N5'] = "yes"
        dummy_sheet['O5'] = "easy"

        dummy_sheet['A6'] = "DUMMY-002"
        dummy_sheet['B6'] = 2
        dummy_sheet['C6'] = "L002"
        dummy_sheet['D6'] = "Sample Req Desc 2"
        dummy_sheet['H6'] = "medium"
        dummy_sheet['M6'] = "Rejected"
        dummy_sheet['N6'] = "partially"
        dummy_sheet['O6'] = "hard"

        # Corrected placement for saving the dummy book
        dummy_book.save(excel_template_path)
        print("Dummy template created with initial data and headers.")
    else:
        print(f"File '{excel_template_path}' already exists. Updating it.")


    data = {
        'Page': [1, 1, 2, 3],
        'Label Number': ['L001', 'L002', 'L003', 'L004'],
        'Description': ['Login feature', 'Registration feature', 'Data logging', 'Error handling'],
        'Priority': ['high', 'medium', 'low', 'high']
    }
    df = pd.DataFrame(data, index=['REQ-001', 'REQ-002', 'REQ-003', 'REQ-004'])

    print("Attempting to write to Excel file...")
    write_excel_file(df, excel_template_path)
    print("Script finished.")

    if os.path.exists(excel_template_path):
        print(f"File successfully saved at: {os.path.abspath(excel_template_path)}")
    else:
        print("File was not found after script execution, check for errors above.")