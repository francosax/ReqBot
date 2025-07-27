import os
import pytest
import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter
import tempfile  # <--- ADD THIS IMPORT

# Assuming write_excel_file is in a file named excel_writer.py
# Adjust this import path if your file is named differently or in a subfolder
from excel_writer import write_excel_file


@pytest.fixture
def empty_compliance_matrix_template():
    """
    Creates a temporary, empty Excel template file with the required sheet
    'MACHINE COMP. MATRIX' for testing.
    """
    fd, path = tempfile.mkstemp(suffix=".xlsx")  # This line now has tempfile imported
    os.close(fd)  # Close the file descriptor immediately

    book = Workbook()  # Create a new workbook
    # Remove the default 'Sheet' and add your specific sheet
    if 'Sheet' in book.sheetnames:
        del book['Sheet']
    matrix_sheet = book.create_sheet('MACHINE COMP. MATRIX', 0)  # Create as the first sheet

    # Add dummy headers that align with expected columns for formulas and data writing
    matrix_sheet['A1'] = "REQ_ID"
    matrix_sheet['B1'] = "Page"
    matrix_sheet['C1'] = "Label Number"
    matrix_sheet['D1'] = "Description"
    matrix_sheet['H1'] = "Priority"
    matrix_sheet['M1'] = "Status"
    matrix_sheet['N1'] = "Completeness"
    matrix_sheet['O1'] = "Difficulty"
    matrix_sheet['P1'] = "Calculated Value"

    book.save(path)
    yield path  # Provide the path to the test
    os.remove(path)  # Clean up the temporary file after the test


def test_write_excel_file_data_and_priority_fills(empty_compliance_matrix_template):
    """
    Tests if data from DataFrame is written correctly and priority-based fills are applied.
    """
    excel_file = empty_compliance_matrix_template

    data = {
        'Page': [1, 2, 3],
        'Label Number': ['L001', 'L002', 'L003'],
        'Description': ['Req 1', 'Req 2', 'Req 3'],
        'Priority': ['high', 'medium', 'low']
    }
    df = pd.DataFrame(data, index=['REQ-A', 'REQ-B', 'REQ-C'])

    write_excel_file(df, excel_file)

    # Load the updated workbook to assert changes
    book = load_workbook(excel_file)
    writer = book['MACHINE COMP. MATRIX']

    # Assert data written
    assert writer['A5'].value == 'REQ-A'
    assert writer['B5'].value == 1
    assert writer['H5'].value == 'high'

    assert writer['A6'].value == 'REQ-B'
    assert writer['B6'].value == 2
    assert writer['H6'].value == 'medium'

    assert writer['A7'].value == 'REQ-C'
    assert writer['B7'].value == 3
    assert writer['H7'].value == 'low'

    # Assert fill colors
    # Hexadecimal values for colors without alpha channel (AARRGGBB -> RRGGBB)
    fill_high_rgb = Color(rgb='FF0000')  # Red
    fill_medium_rgb = Color(rgb='FFFF00')  # Yellow
    fill_low_rgb = Color(rgb='00FF00')  # Green

    # Compare fill objects' start_color.rgb
    assert writer['H5'].fill.start_color.rgb == fill_high_rgb.rgb
    assert writer['H6'].fill.start_color.rgb == fill_medium_rgb.rgb
    assert writer['H7'].fill.start_color.rgb == fill_low_rgb.rgb

    book.close()


def test_write_excel_file_data_validations(empty_compliance_matrix_template):
    """
    Tests if data validations are added to the correct cells.
    Note: Checking the exact rules is complex without parsing XML.
    We'll check if validations exist for the specified ranges.
    """
    excel_file = empty_compliance_matrix_template

    data = {  # Minimal data just to get the function to run
        'Page': [1], 'Label Number': ['L001'], 'Description': ['Desc'], 'Priority': ['high']
    }
    df = pd.DataFrame(data, index=['REQ-X'])

    write_excel_file(df, excel_file)

    book = load_workbook(excel_file)
    writer = book['MACHINE COMP. MATRIX']

    # Assert that data validations exist
    # Check for presence of validation rules on the sheet
    validations = writer.data_validations.dataValidation
    assert len(validations) >= 8  # Expecting 8 data validation rules as defined

    book.close()


def test_write_excel_file_formulas(empty_compliance_matrix_template):
    """
    Tests if formulas are written to the correct cells.
    """
    excel_file = empty_compliance_matrix_template

    data = {
        'Page': [1, 2],
        'Label Number': ['L001', 'L002'],
        'Description': ['Req 1', 'Req 2'],
        'Priority': ['high', 'low']
    }
    df = pd.DataFrame(data, index=['REQ-A', 'REQ-B'])

    write_excel_file(df, excel_file)

    book = load_workbook(excel_file)
    writer = book['MACHINE COMP. MATRIX']

    # Expected column 'P' (16th column) starting from row 5
    col_p = get_column_letter(16)

    # Check that a formula string is present
    assert writer[f'{col_p}5'].value is not None
    assert writer[f'{col_p}5'].value.startswith('=ROUND(((')
    assert writer[f'{col_p}6'].value is not None
    assert writer[f'{col_p}6'].value.startswith('=ROUND(((')

    # Check number format
    assert writer[f'{col_p}5'].number_format == '0'

    book.close()