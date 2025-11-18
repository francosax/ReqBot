# CLAUDE.md - AI Assistant Guide for ReqBot

> **Last Updated**: 2025-11-18
> **Version**: 2.1.1
> **Purpose**: Concise guide for AI assistants working with the ReqBot codebase

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [Development Workflows](#development-workflows)
6. [Testing](#testing)
7. [Common Tasks](#common-tasks)
8. [Important Notes](#important-notes)
9. [Dependencies](#dependencies)

---

## Project Overview

**ReqBot** is a desktop GUI application that automatically extracts requirements from PDF specification documents using NLP. It generates compliance matrices in Excel format, BASIL-compatible SPDX 3.0.1 exports, and creates annotated PDFs with highlighted requirements.

### Key Features
- **Automated Extraction**: spaCy NLP with confidence scoring (0.0-1.0)
- **Excel Compliance Matrix**: Color-coded priorities, data validations, formulas
- **BASIL SPDX 3.0.1 Export**: Industry-standard requirement export
- **PDF Annotation**: Highlighted PDFs with text annotations
- **Customizable Keywords**: User-configurable via `RBconfig.ini`
- **Multi-threaded Processing**: Non-blocking UI with proper cleanup (v2.1.1 fix)

### Tech Stack
- **UI**: PySide6 (Qt), **PDF**: PyMuPDF (fitz), **NLP**: spaCy en_core_web_sm
- **Data**: Pandas, openpyxl, **Export**: JSON-LD SPDX 3.0.1, **Tests**: pytest, pytest-qt

### Key Constants
```python
# pdf_analyzer.py
MIN_REQUIREMENT_LENGTH_WORDS = 5
MAX_REQUIREMENT_LENGTH_WORDS = 100

# highlight_requirements.py
MAX_HIGHLIGHT_COVERAGE_PERCENT = 40
```

---

## Architecture

ReqBot follows a **three-layer architecture**:

```
┌─────────────────────────────────────┐
│ Presentation Layer                  │
│ main_app.py, processing_worker.py   │
├─────────────────────────────────────┤
│ Business Logic Layer                │
│ RB_coordinator.py, pdf_analyzer.py  │
│ excel_writer.py, highlight_*.py     │
├─────────────────────────────────────┤
│ Data/Utility Layer                  │
│ config_RB.py, get_all_files.py      │
└─────────────────────────────────────┘
```

**Entry Points**: `main_app.py` (direct GUI), `run_app.py` (launcher menu)

---

## Core Modules

### main_app.py (~580 lines)
**PySide6 GUI application**

**Key Classes**: `QTextEditLogger`, `RequirementBotApp(QWidget)`

**Critical Methods**:
- `init_ui()` - Creates GUI with confidence threshold controls (slider + spinbox)
- `start_processing()` - Validates inputs, spawns worker thread
- `cancel_processing()` - Stops processing gracefully
- `on_processing_finished()` - **v2.1.1**: Properly terminates thread with `quit()` + `wait()`, sets references to `None`
- `on_processing_error()` - **v2.1.1**: Same thread cleanup for error cases

**Threading Model**: Qt Signal-Slot, QThread for background processing

**New in v2.1**:
- Confidence threshold slider/spinbox (0.0-1.0, default 0.5)
- Recent paths dropdown (last 5 folders/files)
- **v2.1.1 Fix**: Proper thread cleanup prevents "Processing In Progress" warning after completion

---

### processing_worker.py (109 lines)
**Background worker for PDF processing**

**Signals**: `progress_updated(int)`, `log_message(str, str)`, `finished(str)`, `error_occurred(str, str)`

**Pipeline**: Load keywords → Get PDFs (exclude "Tagged") → Process each → Generate outputs → Create LOG.txt

---

### RB_coordinator.py (~72 lines)
**Orchestrates processing pipeline**

**Main Function**: `requirement_bot(path_in, cm_path, words_to_find, path_out)`

**Pipeline Steps**:
1. Extract: `pdf_analyzer.requirement_finder()`
2. Excel: `excel_writer.write_excel_file()`
3. BASIL: `basil_integration.export_to_basil()` (try-except wrapped)
4. Annotate: `highlight_requirements.highlight_requirements()`

**Output Naming**: `YYYY.MM.DD_[Type]_[OriginalFilename].ext`

---

### pdf_analyzer.py (~330 lines)
**NLP-based requirement extraction with quality controls**

**Key Functions**:
- `get_nlp_model()` - Lazy-load cached spaCy model
- `preprocess_pdf_text(text)` - Clean/normalize (fix hyphens, remove page numbers)
- `extract_text_with_layout(page)` - Multi-column support
- `matches_requirement_pattern(sentence)` - Pattern detection (modal verbs, compliance indicators)
- `calculate_requirement_confidence(...)` - Quality scoring (0.0-1.0)
- `requirement_finder(path, keywords_set, filename)` - Main extraction

**Algorithm**: Extract text → Preprocess → Segment sentences → Validate length → Filter by keywords → Calculate confidence → Pattern match → Assign priority

**Priority Logic**:
- `must/shall` → high
- `should/has to` → medium
- `security` → security (overrides)
- else → low

**Returns**: DataFrame with columns: `Label Number, Description, Page, Keyword, Raw, Confidence, Priority, Note`

---

### excel_writer.py (192 lines)
**Excel compliance matrix generation**

**Key Function**: `write_excel_file(df, excel_file)`

**Features**:
- Data starts at **row 5** (rows 1-4 for headers)
- Color-coded priorities: High=Red, Medium=Yellow, Low=Green
- Data validations: Dropdowns in columns I-O, M-N, U, W
- Formula in column P for compliance scores
- Required sheet: `"MACHINE COMP. MATRIX"`

---

### highlight_requirements.py (~125 lines)
**Adds highlights and annotations to PDFs**

**Main Function**: `highlight_requirements(filepath, requirements_list, note_list, page_list, out_pdf_name)`

**Safety Features**:
- Validates highlight size (max 40% page coverage)
- Fallback text annotations if text not found or too large
- Comprehensive logging

**Annotation Types**: Type 8 (highlight), Type 0 (text note)

---

### basil_integration.py (465 lines)
**Import/export requirements to/from BASIL SPDX 3.0.1 format**

**Key Functions**:
- `export_to_basil(df, output_path, created_by, document_name)` - Export to JSON-LD
- `import_from_basil(input_path)` - Import from JSON-LD
- `validate_basil_format(data)` - Validate SPDX compliance
- `merge_basil_requirements(existing_df, imported_df, strategy)` - Merge strategies

**Merge Strategies**: `append` (add all), `update` (update matching IDs), `replace` (replace all)

---

### config_RB.py (53 lines)
**Configuration management**

**Key Function**: `load_keyword_config()`

**Default Keywords**: `ensure, scope, recommended, must, has to, ensuring, shall, should, ensures`

**File Format**: INI using configparser

---

## Data Flow

### Complete Processing Pipeline

```
User Input (GUI)
    ↓
[main_app.py] Validate inputs
    ↓
[processing_worker.py] Background thread
    ↓
FOR EACH PDF:
    ├─ [config_RB.py] Load keywords
    ├─ [RB_coordinator.py] Orchestrate:
    │   ├─ [pdf_analyzer.py] Extract → DataFrame
    │   ├─ [excel_writer.py] Generate compliance matrix
    │   ├─ [basil_integration.py] Export SPDX JSON-LD
    │   └─ [highlight_requirements.py] Annotate PDF
    └─ Update progress
    ↓
Output: *.xlsx, *.jsonld, *_Tagged.pdf, LOG.txt
```

### Requirements DataFrame Structure

```python
{
    'Label Number': 'filename-Req#1-1',
    'Description': 'The system shall...',
    'Page': 1,
    'Keyword': 'shall',
    'Raw': ['The', 'system', 'shall', ...],
    'Confidence': 0.85,  # NEW in v2.0
    'Priority': 'high',
    'Note': 'filename-Req#1-1:The system...'
}
```

---

## Development Workflows

### Setup

```bash
# 1. Clone and setup
git clone <repository-url>
cd ReqBot
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Run tests
pytest

# 3. Launch app
python main_app.py
```

### Typical Modification Workflow

1. **Identify module**: GUI→main_app.py, Extraction→pdf_analyzer.py, Excel→excel_writer.py, etc.
2. **Write/modify tests** first (TDD)
3. **Implement changes**
4. **Run tests**: `pytest -v`
5. **Test manually** with sample PDFs in `sampleIO/`
6. **Commit** with descriptive message

### Adding New Features Checklist

- [ ] Identify affected modules
- [ ] Update relevant test files
- [ ] Implement feature
- [ ] Update docstrings/comments
- [ ] Run test suite
- [ ] Test with real PDF files
- [ ] Update CLAUDE.md if architecture changes
- [ ] Commit with clear message

---

## Testing

### Test Structure

- `test_gui.py` - GUI components (8 tests)
- `test_excel_writer.py` - Excel generation (3 tests)
- `test_highlight_requirements.py` - PDF highlighting (2 tests)
- `test_basil_integration.py` - BASIL integration (25 tests)
- `test_integration*.py` - End-to-end workflows

### Running Tests

```bash
# All tests
pytest -v

# Specific file
pytest test_gui.py

# Specific test
pytest test_gui.py::test_threading_fix_prevents_double_start

# With coverage
pytest --cov=. --cov-report=html
```

### Key Test: Threading Fix (v2.1.1)

```python
# test_gui.py::test_threading_fix_prevents_double_start
def test_threading_fix_prevents_double_start(gui):
    """Verify double-start prevention and thread cleanup"""
    # Simulate processing
    # Verify warning shown on double-click
    # Verify logger warning generated
```

---

## Common Tasks

### Task 1: Add New Keyword

**File**: `RBconfig.ini`

```ini
[DEFAULT_KEYWORD]
word_set = ensure,scope,...,new_keyword
```

Keywords are case-insensitive. Restart processing to apply.

---

### Task 2: Add New Priority Level

**Files**: `pdf_analyzer.py`, `excel_writer.py`

```python
# pdf_analyzer.py - Add condition
if "critical" in sentence_text.lower():
    priority = "critical"

# excel_writer.py - Add color
priority_colors = {
    'critical': 'FF00FF',  # Magenta
    'high': 'FF0000',
    # ...
}
```

---

### Task 3: Modify Excel Output

**Files**: `pdf_analyzer.py` (if adding data), `excel_writer.py`

```python
# Add column to DataFrame
df['Custom_Field'] = custom_data

# Write to Excel
ws['Z' + str(count)] = row['Custom_Field']
```

**Note**: Mind column letters and existing formulas.

---

### Task 4: Debug Processing Issues

**Common Issues**:

| Issue | Check | Solution |
|-------|-------|----------|
| Stuck at X% | `processing_worker.py` logging | Add debug statements |
| No requirements found | Keywords in `RBconfig.ini` | Verify keywords match |
| Excel corrupted | Sheet name exact match | Must be `"MACHINE COMP. MATRIX"` |
| No PDF highlights | Text-based PDF? | Check if scanned (OCR needed) |
| GUI freezes | Threading working? | Verify worker moved to thread |

**Always check**: `application_gui.log` first

---

## Important Notes

### Critical Quirks

1. **"Tagged" PDFs Excluded**: Files with "Tagged" in name are skipped during processing
2. **Excel Row 5 Start**: Data written from row 5 (rows 1-4 reserved for headers)
3. **Sheet Name Required**: Excel template MUST have sheet `"MACHINE COMP. MATRIX"`
4. **spaCy Model Required**: Must run `python -m spacy download en_core_web_sm`
5. **Thread Cleanup (v2.1.1)**: `quit()` + `wait()` + set to `None` required for proper cleanup
6. **Priority "security" Overrides**: If text contains "security", priority is "security" regardless of other keywords

### File Naming Convention

```
YYYY.MM.DD_[Type]_[OriginalFilename].ext

Examples:
- 2025.11.18_Compliance Matrix_spec.xlsx
- 2025.11.18_BASIL_Export_spec.jsonld
- 2025.11.18_Tagged_spec.pdf
```

### Code Style

**Naming**: Functions=snake_case, Classes=PascalCase, Constants=UPPER_CASE

**Logging**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing started")
logger.error(f"Failed: {str(e)}")
```

**Error Handling**:
```python
try:
    result = process_pdf(path)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    self.error_occurred.emit(str(e), "Error Title")
```

---

## Dependencies

### Runtime

| Library | Purpose |
|---------|---------|
| PySide6 | Qt GUI framework |
| PyMuPDF | PDF reading/writing |
| spaCy + en_core_web_sm | NLP processing |
| Pandas | DataFrame operations |
| openpyxl | Excel manipulation |

### Development

- pytest, pytest-qt

### Installation

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## File Structure

```
ReqBot/
├── main_app.py              # GUI application (v2.1.1 threading fix)
├── processing_worker.py     # Background thread worker
├── RB_coordinator.py        # Pipeline orchestrator
├── pdf_analyzer.py          # NLP extraction (enhanced v2.0)
├── excel_writer.py          # Excel matrix generator
├── highlight_requirements.py # PDF annotation (enhanced v2.0)
├── basil_integration.py     # BASIL SPDX 3.0.1 export/import
├── config_RB.py             # Configuration manager
├── get_all_files.py         # File utilities
├── RBconfig.ini             # Keyword configuration
├── CLAUDE.md                # This file (AI assistant guide)
├── README.md                # Project README
├── TODO.md                  # Project roadmap
└── tests/                   # Test suite (270+ tests)
```

---

## Module Dependencies

```
main_app.py
 └─ processing_worker.py
     └─ RB_coordinator.py
         ├─ pdf_analyzer.py (spacy, fitz, pandas)
         ├─ excel_writer.py (openpyxl, pandas)
         ├─ basil_integration.py (json, pandas)
         └─ highlight_requirements.py (fitz)
     └─ config_RB.py (configparser)
     └─ get_all_files.py (os)
```

---

## Best Practices for AI Assistants

### When Reading Code
1. Start with `RB_coordinator.py` for big picture
2. Check tests for expected behavior
3. Read docstrings for context
4. Follow imports to understand dependencies

### When Writing Code
1. Match existing style
2. Add logging (use logger, not print())
3. Update tests for new features
4. Handle errors with try-except + logging
5. Document complex logic
6. Test with real PDFs

### When Debugging
1. Check `application_gui.log` first
2. Run tests to isolate issues
3. Add temporary logging
4. Test incrementally
5. Verify assumptions (file paths, sheet names, etc.)

### When Refactoring
1. Run tests before (establish baseline)
2. Small changes (incremental)
3. Run tests after each change
4. Update documentation
5. Commit frequently

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.1 | 2025-11-18 | Thread cleanup fix for multiple sequential extractions |
| 2.1.0 | 2025-11-17 | UX enhancements, confidence threshold, BASIL integration |
| 2.0.0 | 2025-11-15 | Major NLP improvements, confidence scoring |
| 1.x | Previous | Base functionality |

---

## Quick Reference

### Running the App
```bash
python main_app.py              # Direct launch
python run_app.py               # Interactive menu
```

### Running Tests
```bash
pytest -v                       # All tests
pytest test_gui.py -v           # GUI tests only
pytest --cov=.                  # With coverage
```

### Git Workflow
```bash
git add <files>
git commit -m "Type: Description"
git push origin main
```

### Common Commands
```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Clean up
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete

# Check code
pylint *.py
mypy *.py  # (if type hints added)
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/francosax/ReqBot/issues)
- **Documentation**: See this file (CLAUDE.md) and README.md
- **TODO/Roadmap**: See TODO.md

---

**Last Updated**: 2025-11-18
**Maintained By**: Project maintainers
**AI Assistant Version**: Optimized for Claude Code

---

*This is a living document. Update as the codebase evolves.*
