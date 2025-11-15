# CLAUDE.md - AI Assistant Guide for ReqBot

> **Last Updated**: 2025-11-15
> **Purpose**: Comprehensive guide for AI assistants working with the ReqBot codebase

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [Development Workflows](#development-workflows)
6. [Code Conventions](#code-conventions)
7. [Testing](#testing)
8. [Common Tasks](#common-tasks)
9. [Important Quirks](#important-quirks)
10. [Dependencies](#dependencies)

---

## Project Overview

**ReqBot** is a desktop GUI application that automatically extracts requirements from PDF specification documents using NLP (Natural Language Processing). It generates compliance matrices in Excel format and creates annotated PDFs with highlighted requirements.

### Key Features
- **Automated Requirement Extraction**: Uses spaCy NLP to identify requirement sentences
- **Compliance Matrix Generation**: Creates Excel files with color-coded priorities and validation rules
- **PDF Annotation**: Generates highlighted PDFs with text annotations
- **Customizable Keywords**: User-configurable requirement keywords via `RBconfig.ini`
- **Multi-threaded Processing**: Non-blocking UI with background processing

### Tech Stack
- **UI**: PySide6 (Qt for Python)
- **PDF Processing**: PyMuPDF (fitz)
- **NLP**: spaCy with en_core_web_sm model
- **Data Handling**: Pandas, openpyxl
- **Testing**: pytest, pytest-qt

---

## Architecture

ReqBot follows a **three-layer architecture**:

```
┌─────────────────────────────────────┐
│   Presentation Layer                │
│   - main_app.py (PySide6 GUI)       │
│   - processing_worker.py (QThread)  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Business Logic Layer              │
│   - RB_coordinator.py (Orchestrator)│
│   - pdf_analyzer.py (NLP Extraction)│
│   - excel_writer.py (Matrix Gen)    │
│   - highlight_requirements.py       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Data/Utility Layer                │
│   - config_RB.py (Configuration)    │
│   - get_all_files.py (File Utils)   │
└─────────────────────────────────────┘
```

### Entry Points
- **GUI Application**: `main_app.py` - Direct GUI launch
- **Launcher Menu**: `run_app.py` - Interactive menu (GUI or tests)

---

## Core Modules

### main_app.py (386 lines)
**Purpose**: Main PySide6 GUI application

**Key Classes**:
- `QTextEditLogger`: Custom logging handler for GUI text widget
- `RequirementBotApp(QWidget)`: Main application window

**Important Methods**:
- `init_ui()`: Creates all GUI components
- `start_processing()`: Validates inputs and spawns worker thread
- `cancel_processing()`: Gracefully stops processing
- `_validate_inputs()`: Ensures valid folder paths and template file
- `_apply_stylesheet()`: Applies CSS-like styling

**Threading Model**: Qt Signal-Slot architecture for non-blocking UI

---

### processing_worker.py (109 lines)
**Purpose**: Background worker for PDF processing in separate thread

**Key Class**: `ProcessingWorker(QObject)`

**Signals**:
- `progress_updated(int)`: Progress percentage (0-100)
- `log_message(str, str)`: Log messages with level
- `finished(str)`: Success completion
- `error_occurred(str, str)`: Error reporting

**Processing Steps**:
1. Load keywords from configuration
2. Get all PDF files (excluding "Tagged" PDFs)
3. Process each PDF via `requirement_bot()`
4. Generate Excel and highlighted PDF outputs
5. Create summary LOG.txt file

**AI Assistant Note**: When debugging processing issues, check this worker's `run()` method first.

---

### RB_coordinator.py (49 lines)
**Purpose**: Orchestrates the main processing pipeline

**Key Function**: `requirement_bot(path_in, cm_path, words_to_find, path_out)`

**Pipeline Steps**:
1. **Extract**: Call `pdf_analyzer.requirement_finder()`
2. **Generate Excel**: Copy template and call `excel_writer.write_excel_file()`
3. **Annotate PDF**: Call `highlight_requirements.highlight_requirements()`

**Output Naming Convention**:
```
Format: YYYY.MM.DD_[Type]_[OriginalFilename].ext
Examples:
- 2025.11.15_Compliance Matrix_spec.xlsx
- 2025.11.15_Tagged_spec.pdf
```

**AI Assistant Note**: This is the central coordination point. Modifications to the processing workflow should start here.

---

### pdf_analyzer.py (76 lines)
**Purpose**: NLP-based requirement extraction from PDFs

**Key Function**: `requirement_finder(path, keywords_set, filename)`

**Algorithm**:
1. Extract text from PDF using PyMuPDF
2. Use spaCy to identify sentence boundaries
3. Filter sentences containing requirement keywords (case-insensitive)
4. Assign unique labels: `filename-Req#PageNum-ReqCount`
5. Determine priority based on keyword

**Priority Logic**:
```python
if "must" in text or "shall" in text:
    priority = "high"
elif "should" in text or "has to" in text:
    priority = "medium"
elif "security" in text:
    priority = "security"
else:
    priority = "low"
```

**Returns**: Pandas DataFrame with columns:
- `Label Number`, `Description`, `Page`, `Keyword`, `Raw`, `Note`, `Priority`

**AI Assistant Note**: This is where NLP magic happens. Consider here when improving extraction accuracy.

---

### excel_writer.py (192 lines)
**Purpose**: Excel compliance matrix generation

**Key Function**: `write_excel_file(df, excel_file)`

**Features**:
- Data written starting from **row 5** (rows 1-4 reserved for headers)
- **Color-coded priorities**:
  - High → Red (FF0000)
  - Medium → Yellow (FFFF00)
  - Low → Green (00FF00)
- **Data validations**: Dropdown lists in columns I-O, M-N, U, W
- **Formula insertion**: Column P calculates compliance scores

**Expected Excel Structure**:
- Sheet name: `"MACHINE COMP. MATRIX"`
- Template file must contain: `"Compliance_Matrix_Template_rev001.xlsx"`

**Data Validation Lists** (critical for Excel functionality):
- Column I: Technical, Procedure, Legal, SW, HW, Safety
- Column J: Machine, Product, Company
- Column K: Concept, UTM, UTS, UTE, SW
- Column M: Approved, Rejected, In discussion, Acquired
- Column N: yes, partially, no
- Column O: easy, medium, hard
- Column U: completed, on going, blocked, failed
- Column W: compliant, not compliant, partially compliant

**AI Assistant Note**: When modifying Excel output, test thoroughly - formulas are complex and interdependent.

---

### highlight_requirements.py (76 lines)
**Purpose**: Adds visual highlights and annotations to PDFs

**Key Function**: `highlight_requirements(filepath, requirements_list, note_list, page_list, out_pdf_name)`

**Process**:
1. Open original PDF with PyMuPDF
2. For each requirement:
   - Extract word coordinates from target page
   - Find consecutive word sequence matching requirement
   - Calculate bounding rectangle
   - Add yellow highlight annotation (type 8)
   - Add text note annotation (type 0) with label and description
3. Save encrypted PDF

**AI Assistant Note**: PDF coordinate system can be tricky. Bounding boxes use (x0, y0, x1, y1) format.

---

### config_RB.py (53 lines)
**Purpose**: Configuration management for requirement keywords

**Key Function**: `load_keyword_config()`

**Logic**:
1. If `RBconfig.ini` doesn't exist → create with defaults
2. If exists → read keywords
3. If empty/corrupted → reinitialize with defaults
4. Return set of normalized keywords

**Default Keywords**:
```
ensure, scope, recommended, must, has to, ensuring,
shall, should, ensures
```

**File Format**: INI file using Python's configparser
```ini
[DEFAULT_KEYWORD]
word_set = ensure,scope,recommended,must,has to,ensuring,shall,should,ensures
```

**AI Assistant Note**: To add new keywords, edit `RBconfig.ini` or modify defaults in this module.

---

### get_all_files.py (31 lines)
**Purpose**: Utility for recursive file enumeration

**Key Function**: `get_all(path, ext="")`

**Features**:
- Recursively finds files in directory tree
- Returns sorted list by modification time (oldest first)
- Optional extension filter
- Normalizes paths to forward slashes

---

### run_app.py (65 lines)
**Purpose**: Interactive launcher with menu system

**Functions**:
- `run_gui_app()`: Launches main_app.py in subprocess
- `run_tests()`: Runs pytest test suite

**AI Assistant Note**: Use this as entry point when testing the full application flow.

---

## Data Flow

### Complete Processing Pipeline

```
User Input (GUI)
    ↓
[main_app.py] - Validate inputs
    ↓
[processing_worker.py] - Background thread starts
    ↓
[get_all_files.py] - Enumerate PDFs (exclude "Tagged_*.pdf")
    ↓
FOR EACH PDF:
    │
    ├─→ [config_RB.py] - Load keywords from RBconfig.ini
    │
    ├─→ [RB_coordinator.py] - Orchestrate pipeline
    │    │
    │    ├─→ [pdf_analyzer.py]
    │    │    └─→ spaCy NLP processing
    │    │    └─→ Return: Pandas DataFrame
    │    │
    │    ├─→ [excel_writer.py]
    │    │    └─→ Load template Excel
    │    │    └─→ Add data, colors, validations, formulas
    │    │    └─→ Save: YYYY.MM.DD_Compliance Matrix_file.xlsx
    │    │
    │    └─→ [highlight_requirements.py]
    │         └─→ Add highlights and annotations
    │         └─→ Save: YYYY.MM.DD_Tagged_file.pdf
    │
    └─→ Update progress signals
    └─→ Write to LOG.txt

Final Output:
├─ Multiple *.xlsx (Compliance Matrices)
├─ Multiple *.pdf (Tagged PDFs)
└─ LOG.txt (Summary)
```

### Key Data Structure: Requirements DataFrame

```python
DataFrame columns:
{
    'Label Number': 'filename-Req#1-1',      # Unique ID
    'Description': 'The system shall...',    # Cleaned text
    'Page': 1,                               # Page number
    'Keyword': 'shall',                      # Matching keyword
    'Raw': ['The', 'system', 'shall', ...],  # Word list for highlighting
    'Note': 'filename-Req#1-1:The system...', # Combined label + description
    'Priority': 'high'                       # Calculated priority
}
```

**AI Assistant Note**: This DataFrame is the central data structure. All modules expect these exact column names.

---

## Development Workflows

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd ReqBot

# 2. Install dependencies (create requirements.txt if needed)
pip install PySide6 PyMuPDF spacy pandas openpyxl pytest pytest-qt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Run tests to verify setup
pytest

# 5. Launch application
python main_app.py
# OR
python run_app.py
```

### Running the Application

**Method 1: Direct GUI Launch**
```bash
python main_app.py
```

**Method 2: Interactive Menu**
```bash
python run_app.py
# Then select option 1 for GUI
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_gui.py
pytest test_excel_writer.py
pytest test_highlight_requirements.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=.
```

### Typical Modification Workflow

1. **Identify the module** to modify based on feature location:
   - GUI changes → `main_app.py`
   - Extraction logic → `pdf_analyzer.py`
   - Excel output → `excel_writer.py`
   - PDF annotation → `highlight_requirements.py`
   - Workflow changes → `RB_coordinator.py`

2. **Read existing code** to understand context

3. **Write/modify tests** first (TDD approach)

4. **Implement changes**

5. **Run tests** to verify

6. **Test manually** with sample PDFs in `sampleIO/`

7. **Commit changes** with descriptive message

### Adding New Features: Checklist

- [ ] Identify affected modules
- [ ] Update relevant test files
- [ ] Implement feature
- [ ] Update docstrings/comments
- [ ] Run test suite
- [ ] Test with real PDF files
- [ ] Update this CLAUDE.md if architecture changes
- [ ] Commit with clear message

---

## Code Conventions

### Naming Conventions

| Type | Convention | Examples |
|------|------------|----------|
| Functions | snake_case | `write_excel_file`, `requirement_finder` |
| Classes | PascalCase | `RequirementBotApp`, `ProcessingWorker` |
| Constants | UPPER_CASE | `CM_TEMPLATE_NAME`, `DEFAULT_KEYWORDS` |
| Private members | _leading_underscore | `_worker_thread`, `_is_running` |
| Module names | snake_case | `main_app.py`, `pdf_analyzer.py` |

### Design Patterns Used

1. **Observer Pattern**: Qt Signal-Slot mechanism
   ```python
   # Worker emits signals
   self.progress_updated.emit(50)

   # GUI connects slots
   self.worker.progress_updated.connect(self.update_progress)
   ```

2. **Factory Pattern**: `_create_path_selector()` creates UI components

3. **Singleton**: QApplication instance management

4. **Template Method**: `ProcessingWorker.run()` defines processing skeleton

### Code Style Guidelines

**Logging**:
```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Processing started")
logger.warning("Template missing column")
logger.error(f"Failed to process {filename}: {str(e)}")
```

**Error Handling**:
```python
try:
    # Processing code
    result = process_pdf(path)
except Exception as e:
    logger.error(f"Error processing: {str(e)}")
    self.error_occurred.emit(str(e), "Processing Error")
    return
```

**Threading**:
```python
# Main thread creates worker
self._worker = ProcessingWorker(...)
self._worker_thread = QThread()
self._worker.moveToThread(self._worker_thread)

# Connect signals BEFORE starting thread
self._worker.finished.connect(self.on_finished)

# Start thread
self._worker_thread.start()
```

**File Operations**:
```python
# Always use absolute paths
import os
abs_path = os.path.abspath(relative_path)

# Check existence before processing
if not os.path.exists(file_path):
    logger.error(f"File not found: {file_path}")
    return
```

### Important Constants and Magic Values

```python
# Excel writing
STARTING_ROW = 5  # Data starts at row 5 (1-4 are headers)
SHEET_NAME = "MACHINE COMP. MATRIX"  # Required sheet name

# File naming
DATE_FORMAT = "%Y.%m.%d"  # YYYY.MM.DD
CM_PREFIX = "Compliance Matrix"
TAGGED_PREFIX = "Tagged"

# Priority colors (RGB hex)
COLOR_HIGH = "FF0000"     # Red
COLOR_MEDIUM = "FFFF00"   # Yellow
COLOR_LOW = "00FF00"      # Green

# PDF annotation types
HIGHLIGHT_TYPE = 8        # Yellow highlight
TEXT_NOTE_TYPE = 0        # Text annotation

# Time estimation
ANALYSIS_TIME_PER_REQ = 5/60  # 5 minutes per requirement in hours
```

### Language Notes

**Mixed Language Comments**: Legacy code contains Italian comments:
- "requisiti" = requirements
- "cartella" = folder
- "percorso" = path
- "parola" = word

**AI Assistant Guideline**: When modifying code with Italian comments, you may translate to English for clarity, but preserve original meaning.

---

## Testing

### Test Structure

```
ReqBot/
├─ test_gui.py                    # GUI component tests (80 lines)
├─ test_excel_writer.py           # Excel generation tests (149 lines)
└─ test_highlight_requirements.py  # PDF highlighting tests (78 lines)
```

### Test Framework

- **Framework**: pytest
- **GUI Testing**: pytest-qt plugin
- **Fixtures**: Temporary files, mock dialogs
- **Isolation**: Each test creates/cleans up temporary resources

### Key Test Files

#### test_gui.py
**Tests**: GUI initialization, user interactions, threading

**Fixtures**:
```python
@pytest.fixture(scope="module")
def app():
    """QApplication instance for all tests"""

@pytest.fixture
def gui(app):
    """RequirementBotApp instance"""
```

**Key Tests**:
- `test_initial_state`: Verify default GUI state
- `test_input_folder_field`: Test folder selection
- `test_progress_bar_updates`: Test progress updates
- `test_task_finished_shows_messagebox`: Test completion message

**AI Assistant Note**: When adding GUI features, add corresponding tests here.

---

#### test_excel_writer.py
**Tests**: Excel file generation, formatting, formulas

**Fixtures**:
```python
@pytest.fixture
def empty_compliance_matrix_template(tmp_path):
    """Creates temporary Excel template"""
```

**Key Tests**:
- `test_write_excel_file_data_and_priority_fills`: Data writing + color coding
- `test_write_excel_file_data_validations`: Dropdown validation rules
- `test_write_excel_file_formulas`: Formula insertion

**Validation Checks**:
```python
# Verify data written
assert ws['A5'].value == expected_value

# Verify color coding
assert ws['H5'].fill.start_color.rgb == expected_color

# Verify data validation
assert ws['I5'].data_validation is not None

# Verify formulas
assert ws['P5'].value.startswith('=IF')
```

**AI Assistant Note**: Excel tests are critical - formulas are complex. Always run these after Excel modifications.

---

#### test_highlight_requirements.py
**Tests**: PDF highlighting and annotation

**Fixtures**:
```python
@pytest.fixture
def sample_pdf(tmp_path):
    """Creates temporary test PDF with sample text"""
```

**Key Tests**:
- `test_highlight_requirements_basic`: Successful highlighting
- `test_highlight_requirements_no_match`: Handles non-matching text

**Verification**:
```python
# Count annotations
highlight_count = sum(1 for annot in page.annots() if annot.type[0] == 8)
note_count = sum(1 for annot in page.annots() if annot.type[0] == 0)

assert highlight_count == expected_highlights
assert note_count == expected_notes
```

**AI Assistant Note**: PDF tests use PyMuPDF's annotation types. Type 8 = highlight, Type 0 = text note.

---

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest test_excel_writer.py

# Specific test
pytest test_gui.py::test_initial_state

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Coverage report
pytest --cov=. --cov-report=html
```

### Test-Driven Development (TDD) Workflow

1. **Write failing test** for new feature
2. **Run test** to confirm it fails
3. **Implement minimum code** to pass test
4. **Run test** to confirm it passes
5. **Refactor** if needed
6. **Run all tests** to ensure no regressions

**Example**:
```python
# 1. Write test in test_pdf_analyzer.py
def test_extract_security_requirements():
    """Test that 'security' keyword creates 'security' priority"""
    # Test implementation
    assert result['Priority'][0] == 'security'

# 2. Run: pytest test_pdf_analyzer.py::test_extract_security_requirements
# (fails because feature not implemented)

# 3. Implement in pdf_analyzer.py
def requirement_finder(...):
    # Add logic for security priority
    if 'security' in sentence_text.lower():
        priority = 'security'

# 4. Run test again (passes)

# 5. Run all tests: pytest
```

---

## Common Tasks

### Task 1: Adding a New Requirement Keyword

**Files to modify**: `config_RB.py`, `RBconfig.ini`

**Steps**:

1. **Edit RBconfig.ini**:
```ini
[DEFAULT_KEYWORD]
word_set = ensure,scope,recommended,must,has to,ensuring,shall,should,ensures,required
                                                                                 ^^^^^^^^ (add new keyword)
```

2. **Update default in config_RB.py** (optional, for auto-generation):
```python
default_word_set = "ensure,scope,recommended,must,has to,ensuring,shall,should,ensures,required"
```

3. **Test**: Process a PDF containing the new keyword

**AI Assistant Note**: Keywords are case-insensitive. The system will find "REQUIRED", "Required", "required".

---

### Task 2: Adding a New Priority Level

**Files to modify**: `pdf_analyzer.py`, `excel_writer.py`

**Steps**:

1. **Add logic in pdf_analyzer.py**:
```python
def requirement_finder(path, keywords_set, filename):
    # ...existing code...

    # Add new priority condition
    if "critical" in sentence_text.lower():
        priority = "critical"
    elif "must" in sentence_text.lower() or "shall" in sentence_text.lower():
        priority = "high"
    # ...rest of logic...
```

2. **Add color mapping in excel_writer.py**:
```python
priority_colors = {
    'critical': 'FF00FF',  # Magenta
    'high': 'FF0000',      # Red
    'medium': 'FFFF00',    # Yellow
    'low': '00FF00'        # Green
}

# Apply color
fill_color = priority_colors.get(priority, 'FFFFFF')  # White default
```

3. **Write tests**:
```python
def test_critical_priority():
    """Test that 'critical' keyword creates 'critical' priority"""
    # Test implementation
```

4. **Test manually** with sample PDF

**AI Assistant Note**: Consider backward compatibility with existing Excel templates.

---

### Task 3: Modifying Excel Output Columns

**Files to modify**: `excel_writer.py`, potentially `pdf_analyzer.py`

**Steps**:

1. **Update DataFrame columns** in `pdf_analyzer.py` (if adding data):
```python
df = pd.DataFrame({
    'Label Number': label_numbers,
    'Description': descriptions,
    'Page': pages,
    'Priority': priorities,
    'Custom_Field': custom_data,  # New column
    # ...
})
```

2. **Update excel_writer.py** to write new column:
```python
def write_excel_file(df, excel_file):
    # ...existing code...

    for index, row in df.iterrows():
        ws['A' + str(count)] = count - 4
        ws['B' + str(count)] = row['Page']
        # ... existing columns ...
        ws['Z' + str(count)] = row['Custom_Field']  # New column
```

3. **Update tests** in `test_excel_writer.py`:
```python
def test_write_custom_field():
    """Test that custom field is written to Excel"""
    # Test implementation
```

4. **Update Excel template** if necessary

**AI Assistant Note**: Be mindful of column letters and existing formulas that may reference them.

---

### Task 4: Improving NLP Extraction Accuracy

**Files to modify**: `pdf_analyzer.py`

**Strategies**:

1. **Improve sentence boundary detection**:
```python
# Use spaCy's sentence segmentation more carefully
for sent in doc.sents:
    # Filter out very short sentences
    if len(sent.text.split()) < 5:
        continue
    # Process sentence
```

2. **Add context-aware filtering**:
```python
# Exclude sentences in certain contexts (e.g., headers, footers)
if any(header_word in sentence.lower() for header_word in ['page', 'section', 'chapter']):
    continue
```

3. **Improve keyword matching**:
```python
# Use word boundaries to avoid partial matches
import re
def contains_keyword(text, keyword):
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))
```

4. **Add requirement pattern recognition**:
```python
# Look for requirement patterns (e.g., "The system shall...")
requirement_patterns = [
    r'The \w+ (shall|must|should)',
    r'\w+ (shall|must|should) (be|have|provide|support)',
]
```

**AI Assistant Note**: Always test with diverse PDF samples. NLP accuracy varies with document formatting.

---

### Task 5: Adding New Data Validation Dropdown

**Files to modify**: `excel_writer.py`

**Steps**:

1. **Add new validation list** in `write_excel_file()`:
```python
# Existing validations...

# Add new validation for column Y
dv_custom = DataValidation(type="list", formula1='"Option1,Option2,Option3"')
ws.add_data_validation(dv_custom)
for count in range(5, 5 + len(df)):
    dv_custom.add(ws['Y' + str(count)])
```

2. **Test** the validation:
```python
def test_write_excel_file_custom_validation():
    """Test that custom validation is added to column Y"""
    # ...create test DataFrame and Excel file...

    # Open and verify
    wb = load_workbook(excel_path)
    ws = wb.active

    # Check that validation exists
    assert ws['Y5'].data_validation is not None

    # Verify validation formula
    dv = ws['Y5'].data_validation
    assert 'Option1' in dv.formula1
```

**AI Assistant Note**: Excel data validations are powerful but can slow down large files. Test with realistic data sizes.

---

### Task 6: Debugging Processing Issues

**Common Issues and Solutions**:

**Issue**: "Processing stuck at X%"
- **Check**: `processing_worker.py` - Look for exceptions in `run()` method
- **Debug**: Add logging statements to identify where it's stuck
```python
logger.info(f"Processing file {i+1} of {total_files}")
logger.info(f"Starting requirement extraction for {pdf_path}")
```

**Issue**: "No requirements found in PDF"
- **Check**: `pdf_analyzer.py` - Verify text extraction is working
```python
# Debug text extraction
text = page.get_text("text")
logger.debug(f"Extracted text from page {page_num}: {text[:100]}...")
```
- **Check**: Keywords are correct in `RBconfig.ini`
- **Check**: spaCy model is loaded correctly

**Issue**: "Excel file corrupted or won't open"
- **Check**: `excel_writer.py` - Verify template path is correct
- **Check**: Sheet name matches exactly: "MACHINE COMP. MATRIX"
- **Debug**: Open Excel in openpyxl and inspect:
```python
from openpyxl import load_workbook
wb = load_workbook('output.xlsx')
print(wb.sheetnames)  # Verify sheet names
```

**Issue**: "PDF highlights not appearing"
- **Check**: `highlight_requirements.py` - Verify word matching logic
- **Debug**: Print bounding rectangles:
```python
logger.debug(f"Highlight rect: {rect}")
```
- **Check**: PDF might be scanned (image-based, not text)

**Issue**: "GUI freezes during processing"
- **Check**: Threading is working correctly in `main_app.py`
- **Verify**: Worker is moved to separate thread:
```python
assert self._worker.thread() == self._worker_thread
```

**AI Assistant Note**: Always check logs first (`application_gui.log`). Most issues are logged.

---

### Task 7: Adding Internationalization (i18n)

**Current State**: Mixed English/Italian comments, English UI

**To Add Full i18n**:

1. **Use Qt's translation system**:
```python
from PySide6.QtCore import QTranslator, QLocale

# In main_app.py
translator = QTranslator()
translator.load(QLocale.system(), 'reqbot', '_', 'translations')
app.installTranslator(translator)
```

2. **Wrap all user-facing strings**:
```python
# Before
self.start_btn.setText("Start Processing")

# After
self.start_btn.setText(self.tr("Start Processing"))
```

3. **Create translation files**:
```bash
pylupdate6 main_app.py -ts translations/reqbot_it.ts
pylupdate6 main_app.py -ts translations/reqbot_es.ts
```

4. **Translate with Qt Linguist** (GUI tool)

5. **Compile translations**:
```bash
lrelease translations/reqbot_it.ts -qm translations/reqbot_it.qm
```

**AI Assistant Note**: Consider standardizing all comments to English for better maintainability.

---

## Important Quirks

### Quirk 1: "Tagged" PDFs are Excluded

**Behavior**: PDFs with "Tagged" in the filename are automatically skipped during processing.

**Location**: `processing_worker.py`
```python
if "Tagged" in pdf_path:
    continue  # Skip already processed PDFs
```

**Reason**: Prevents re-processing of output PDFs that were previously highlighted.

**AI Assistant Note**: If you need to reprocess a tagged PDF, rename it to remove "Tagged" from the filename.

---

### Quirk 2: Excel Data Starts at Row 5

**Behavior**: All data is written starting from Excel row 5, not row 1.

**Location**: `excel_writer.py`
```python
STARTING_ROW = 5
for index, row in df.iterrows():
    count = index + STARTING_ROW
    ws['A' + str(count)] = ...
```

**Reason**: Rows 1-4 are reserved for headers and formatting in the template.

**AI Assistant Note**: When debugging Excel issues, remember row 1 ≠ first data row.

---

### Quirk 3: Mixed Language Comments

**Behavior**: Some code comments are in Italian, others in English.

**Examples**:
```python
# Italian
"# Trova tutti i file PDF nella cartella"  # Find all PDF files in folder

# English
"# Extract text from PDF page"
```

**AI Assistant Note**: When modifying code, you may translate Italian comments to English for consistency.

---

### Quirk 4: Hardcoded Excel Sheet Name

**Behavior**: Excel template MUST have a sheet named exactly "MACHINE COMP. MATRIX".

**Location**: `excel_writer.py`
```python
ws = wb['MACHINE COMP. MATRIX']  # Will fail if sheet doesn't exist
```

**Reason**: Legacy template structure.

**AI Assistant Note**: If changing sheet name, update both template and code. Consider making this configurable.

---

### Quirk 5: Time Estimation Formula

**Behavior**: LOG.txt contains estimated analysis time using magic number `5/60`.

**Location**: `processing_worker.py`
```python
estimated_time = len(df) * (5 / 60)  # 5 minutes per requirement in hours
```

**Reason**: Assumed 5 minutes of manual review per requirement.

**AI Assistant Note**: This is an estimate for human review time, not actual processing time.

---

### Quirk 6: Priority "security" Overrides Others

**Behavior**: If text contains "security", priority is "security" regardless of other keywords.

**Location**: `pdf_analyzer.py`
```python
if "security" in sentence_text.lower():
    priority = "security"
elif "must" in sentence_text.lower() or "shall" in sentence_text.lower():
    priority = "high"
# ...
```

**Implication**: A sentence like "The system must ensure security" → priority = "security", not "high"

**AI Assistant Note**: Consider if this priority hierarchy is intended or should be modified.

---

### Quirk 7: Relative Path Assumptions

**Behavior**: Code assumes `RBconfig.ini` is in the current working directory.

**Location**: `config_RB.py`
```python
parser.read('RBconfig.ini')  # Relative path
```

**Implication**: Application must be run from the project root directory.

**AI Assistant Note**: Consider using absolute paths or `__file__` for more robustness:
```python
import os
config_path = os.path.join(os.path.dirname(__file__), 'RBconfig.ini')
parser.read(config_path)
```

---

### Quirk 8: spaCy Model Must Be Downloaded

**Behavior**: Application requires `en_core_web_sm` spaCy model to be pre-downloaded.

**Installation**:
```bash
python -m spacy download en_core_web_sm
```

**Error if Missing**: Import will fail in `pdf_analyzer.py`:
```python
import spacy
nlp = spacy.load("en_core_web_sm")  # Fails if not downloaded
```

**AI Assistant Note**: Add this to setup instructions. Consider graceful fallback or auto-download.

---

### Quirk 9: Excel Formulas are Language-Dependent

**Behavior**: Excel formulas use English function names (IF, AND, OR).

**Location**: `excel_writer.py`
```python
formula = '=IF(AND(...), ...)'
```

**Implication**: May not work correctly in non-English Excel installations (e.g., Italian uses `SE` instead of `IF`).

**AI Assistant Note**: Excel formulas are stored in English and auto-translated by Excel. This should work across locales.

---

### Quirk 10: No Type Hints

**Behavior**: Codebase doesn't use Python type hints.

**Example**:
```python
# Current
def requirement_finder(path, keywords_set, filename):
    ...

# With type hints (not used)
def requirement_finder(path: str, keywords_set: set, filename: str) -> pd.DataFrame:
    ...
```

**AI Assistant Note**: Consider adding type hints in future refactoring for better IDE support and error detection.

---

## Dependencies

### Runtime Dependencies

| Library | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| **PySide6** | Latest | Qt GUI framework | `pip install PySide6` |
| **PyMuPDF (fitz)** | Latest | PDF reading/writing | `pip install PyMuPDF` |
| **spaCy** | Latest | NLP processing | `pip install spacy` |
| **en_core_web_sm** | Latest | spaCy English model | `python -m spacy download en_core_web_sm` |
| **Pandas** | Latest | DataFrame operations | `pip install pandas` |
| **openpyxl** | Latest | Excel file manipulation | `pip install openpyxl` |

### Development Dependencies

| Library | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| **pytest** | Latest | Test framework | `pip install pytest` |
| **pytest-qt** | Latest | Qt testing utilities | `pip install pytest-qt` |

### Standard Library Dependencies

- `configparser` - Configuration file parsing
- `logging` - Application logging
- `os`, `sys` - System operations
- `subprocess` - Process management
- `datetime` - Date/time handling
- `re` - Regular expressions

### Creating requirements.txt

**AI Assistant Note**: The repository doesn't currently have a `requirements.txt`. Here's a recommended one:

```txt
PySide6>=6.0.0
PyMuPDF>=1.18.0
spacy>=3.0.0
pandas>=1.3.0
openpyxl>=3.0.0
pytest>=6.0.0
pytest-qt>=4.0.0
```

**To install**:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## File Structure Reference

```
ReqBot/
├── .github/
│   ├── workflows/
│   │   └── qodana_code_quality.yml    # CI/CD pipeline
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
├── sampleIO/
│   ├── Compliance_Matrix_Template_rev001.xlsx  # Excel template
│   ├── test_output/                            # Example outputs
│   ├── Immagine.png                            # Screenshots
│   └── Immagine_2.png
├── main_app.py                        # GUI application (386 lines)
├── processing_worker.py               # Background worker (109 lines)
├── RB_coordinator.py                  # Pipeline orchestrator (49 lines)
├── pdf_analyzer.py                    # NLP extraction (76 lines)
├── excel_writer.py                    # Excel generation (192 lines)
├── highlight_requirements.py          # PDF annotation (76 lines)
├── config_RB.py                       # Configuration loader (53 lines)
├── get_all_files.py                   # File utilities (31 lines)
├── run_app.py                         # Launcher menu (65 lines)
├── test_gui.py                        # GUI tests (80 lines)
├── test_excel_writer.py               # Excel tests (149 lines)
├── test_highlight_requirements.py     # PDF tests (78 lines)
├── RBconfig.ini                       # Keyword configuration
├── qodana.yaml                        # Code quality config
├── README.md                          # Brief description
├── LICENSE                            # License file
├── .gitignore                         # Git ignore rules
└── CLAUDE.md                          # This file
```

**Total Lines of Code**: ~1,344 (excluding tests and config)

---

## Quick Reference: Module Dependencies

```
main_app.py
    └─→ processing_worker.py
            └─→ RB_coordinator.py
                    ├─→ pdf_analyzer.py (depends on: spacy, fitz, pandas)
                    ├─→ excel_writer.py (depends on: openpyxl, pandas)
                    └─→ highlight_requirements.py (depends on: fitz)
            └─→ config_RB.py (depends on: configparser)
            └─→ get_all_files.py (depends on: os)

run_app.py
    └─→ main_app.py (subprocess launch)
    └─→ pytest (subprocess launch)
```

---

## Best Practices for AI Assistants

### When Reading Code

1. **Start with RB_coordinator.py** - It's the orchestrator and shows the big picture
2. **Check tests** - They document expected behavior
3. **Read docstrings** - Even minimal ones provide context
4. **Follow imports** - Understand dependencies
5. **Check git history** - See why changes were made (if available)

### When Writing Code

1. **Match existing style** - Maintain consistency
2. **Add logging** - Use the existing logger, don't print()
3. **Update tests** - Add/modify tests for new features
4. **Handle errors** - Use try-except with logging
5. **Document changes** - Add comments for complex logic
6. **Test with real PDFs** - Don't trust unit tests alone

### When Debugging

1. **Check logs first** - `application_gui.log` contains valuable info
2. **Run tests** - Isolate issues with unit tests
3. **Use print debugging** - Add temporary logging statements
4. **Test incrementally** - Don't change multiple things at once
5. **Verify assumptions** - Check file paths, sheet names, column letters

### When Refactoring

1. **Run tests before** - Establish baseline
2. **Make small changes** - Incremental refactoring
3. **Run tests after each change** - Catch regressions early
4. **Update documentation** - Keep CLAUDE.md current
5. **Commit frequently** - Small, atomic commits

---

## Contact and Support

### Repository Information
- **Primary Language**: Python
- **GUI Framework**: PySide6 (Qt)
- **License**: See LICENSE file

### For AI Assistants

When helping users with ReqBot:

1. **Understand the context** - Is it a bug, feature request, or question?
2. **Reference this guide** - Use the information provided here
3. **Test your suggestions** - Verify code changes work as expected
4. **Explain trade-offs** - Help users make informed decisions
5. **Update this file** - If you discover new patterns or conventions

### Common User Questions

**Q: How do I add a new keyword?**
A: Edit `RBconfig.ini` and add the keyword to the `word_set` list.

**Q: Why aren't requirements being found?**
A: Check that keywords match the PDF text, spaCy model is installed, and PDF is text-based (not scanned images).

**Q: How do I change the Excel template?**
A: Edit the template file, but keep sheet name "MACHINE COMP. MATRIX" and preserve row 1-4 for headers.

**Q: Can I process scanned PDFs?**
A: Not currently. The tool requires text-based PDFs. Consider OCR preprocessing.

**Q: How do I change priority colors?**
A: Edit the color hex codes in `excel_writer.py` in the priority fill section.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-15 | Initial CLAUDE.md creation |

---

## Appendix: Useful Code Snippets

### Snippet 1: Creating a New Worker Thread

```python
from PySide6.QtCore import QObject, QThread, Signal

class CustomWorker(QObject):
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, data):
        super().__init__()
        self.data = data
        self._is_running = True

    def run(self):
        try:
            for i in range(100):
                if not self._is_running:
                    return
                # Do work
                self.progress.emit(i)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False

# In main GUI
self.worker = CustomWorker(data)
self.thread = QThread()
self.worker.moveToThread(self.thread)
self.thread.started.connect(self.worker.run)
self.worker.finished.connect(self.thread.quit)
self.worker.finished.connect(self.worker.deleteLater)
self.thread.finished.connect(self.thread.deleteLater)
self.thread.start()
```

### Snippet 2: Reading Configuration

```python
import configparser
import os

def load_config(config_file='config.ini', section='DEFAULT'):
    """Load configuration from INI file"""
    parser = configparser.ConfigParser()

    if not os.path.exists(config_file):
        # Create default config
        parser[section] = {'key': 'default_value'}
        with open(config_file, 'w') as f:
            parser.write(f)

    parser.read(config_file)
    return dict(parser[section])

# Usage
config = load_config('RBconfig.ini', 'DEFAULT_KEYWORD')
keywords = config.get('word_set', '').split(',')
```

### Snippet 3: Processing PDFs with PyMuPDF

```python
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF"""
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        all_text.append({
            'page': page_num + 1,
            'text': text
        })

    doc.close()
    return all_text

def add_highlight_to_pdf(input_pdf, output_pdf, page_num, rect):
    """Add yellow highlight to PDF"""
    doc = fitz.open(input_pdf)
    page = doc[page_num]

    # Create highlight annotation
    highlight = page.add_highlight_annot(rect)
    highlight.update()

    doc.save(output_pdf)
    doc.close()
```

### Snippet 4: Creating Excel with Formatting

```python
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.worksheet.datavalidation import DataValidation

def create_formatted_excel(output_path):
    """Create Excel with formatting and validations"""
    wb = Workbook()
    ws = wb.active

    # Write headers
    ws['A1'] = 'ID'
    ws['B1'] = 'Description'

    # Apply formatting
    header_fill = PatternFill(start_color="0000FF", end_color="0000FF", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    ws['A1'].fill = header_fill
    ws['A1'].font = header_font
    ws['B1'].fill = header_fill
    ws['B1'].font = header_font

    # Add data validation
    dv = DataValidation(type="list", formula1='"Option1,Option2,Option3"')
    ws.add_data_validation(dv)
    dv.add(ws['C2'])  # Apply to cell C2

    # Save
    wb.save(output_path)
```

### Snippet 5: Using spaCy for NLP

```python
import spacy

# Load model
nlp = spacy.load("en_core_web_sm")

def extract_sentences(text):
    """Extract sentences using spaCy"""
    doc = nlp(text)
    sentences = []

    for sent in doc.sents:
        sentences.append({
            'text': sent.text,
            'start': sent.start_char,
            'end': sent.end_char,
            'tokens': [token.text for token in sent]
        })

    return sentences

def filter_by_keywords(text, keywords):
    """Filter sentences containing keywords"""
    sentences = extract_sentences(text)
    matching_sentences = []

    for sent in sentences:
        sent_lower = sent['text'].lower()
        for keyword in keywords:
            if keyword.lower() in sent_lower:
                matching_sentences.append({
                    **sent,
                    'keyword': keyword
                })
                break

    return matching_sentences
```

---

**End of CLAUDE.md**

> **Note to AI Assistants**: This document is comprehensive but not exhaustive. When you discover new patterns, conventions, or important information, please update this file to help future AI assistants working on ReqBot.

**Last Updated**: 2025-11-15 by Claude (Sonnet 4.5)
