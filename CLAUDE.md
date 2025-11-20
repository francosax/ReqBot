# CLAUDE.md - AI Assistant Guide for ReqBot

> **Last Updated**: 2025-11-19
> **Version**: 2.3.0 (Released - Phase 1 Complete)
> **Status**: v2.3 Phase 1 complete (UX & Infrastructure), v3.0 features merged to main
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
- **Customizable Keywords**: User-configurable via `RBconfig.ini` or keyword profiles
- **Multi-threaded Processing**: Non-blocking UI with proper cleanup (v2.1.1 fix)
- **Recent Projects**: Quick access to last 5 used paths (v2.1.1)
- **HTML Processing Reports**: Comprehensive extraction reports with statistics (v2.1.1)
- **Keyword Profiles**: 6 predefined profiles + custom support (v2.2 - merged)
- **Requirement Categorization**: 9-category auto-classification (v2.2 - merged)
- **Drag & Drop Support**: Drag folders/files directly into GUI fields (v2.3.0)
- **Progress Details**: Real-time file and step tracking during processing (v2.3.0)
- **CI/CD Pipeline**: Automated testing on push/PR with multi-Python support (v2.3.0)
- **Multi-lingual Support**: Language detection and multi-language NLP (v3.0 - merged)
- **Database Backend**: SQLAlchemy ORM with full CRUD operations (v3.0 - merged)

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

### main_app.py (~650 lines)
**PySide6 GUI application**

**Key Classes**:
- `QTextEditLogger` - Custom logger for GUI
- `DragDropComboBox(QComboBox)` - **v2.3.0**: Custom combo box with drag & drop support
- `RequirementBotApp(QWidget)` - Main application window

**Critical Methods**:
- `init_ui()` - Creates GUI with confidence threshold controls (slider + spinbox)
- `start_processing()` - Validates inputs, spawns worker thread
- `cancel_processing()` - Stops processing gracefully
- `on_processing_finished()` - **v2.1.1**: Properly terminates thread with `quit()` + `wait()`, sets references to `None`
- `on_processing_error()` - **v2.1.1**: Same thread cleanup for error cases
- `update_progress_detail()` - **v2.3.0**: Updates progress detail label with current file/step

**Threading Model**: Qt Signal-Slot, QThread for background processing

**New in v2.1**:
- Confidence threshold slider/spinbox (0.0-1.0, default 0.5)
- Recent paths dropdown (last 5 folders/files)
- **v2.1.1 Fix**: Proper thread cleanup prevents "Processing In Progress" warning after completion

**New in v2.3**:
- **DragDropComboBox**: Custom widget supporting drag & drop for files and folders
- **Progress Details**: Real-time display of current file being processed and processing step
- File type validation (folders only for input/output, .xlsx only for CM)
- Visual feedback during drag operations

---

### processing_worker.py (~150 lines)
**Background worker for PDF processing**

**Signals**:
- `progress_updated(int)` - Progress percentage (0-100)
- `progress_detail_updated(str)` - **v2.3.0**: Detailed progress message (file name, step, counter)
- `log_message(str, str)` - Log messages with level
- `finished(str)` - Processing completion
- `error_occurred(str, str)` - Error handling

**Pipeline**: Load keywords → Get PDFs (exclude "Tagged") → Process each → Generate outputs → Create LOG.txt

**v2.3.0 Progress Details**:
- "Initializing processing..."
- "Found X PDF file(s) to process"
- "File N/X: Analyzing filename.pdf..."
- "File N/X: Extracting requirements from filename.pdf..."
- "File N/X: Completed filename.pdf (X requirements)"
- "Generating processing report..."

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

### get_all_files.py (23 lines)
**File system utilities**

**Key Function**: `get_all_files(path, extension)`

**Purpose**: Recursively find all files with specific extension, exclude files with "Tagged" in name

---

### version.py (24 lines)
**Single source of truth for version information**

**Version Constants**: `__version__`, `__version_info__`, `MAJOR`, `MINOR`, `PATCH`, `GUI_VERSION`

**Current Version**: `2.2.0` - "Quality of Life & Performance"

**Purpose**: Centralized version management for all modules

---

### run_app.py (65 lines)
**Interactive launcher menu for ReqBot**

**Key Function**: `main()`

**Features**:
- Text-based menu interface
- Launch main GUI application
- Quick access to configuration files
- Help and documentation links

**Entry Point**: Alternative to direct `main_app.py` launch

---

### recent_projects.py (246 lines)
**Recent paths management with singleton pattern** *(v2.1.1)*

**Key Class**: `RecentProjects` (singleton)

**Key Methods**:
- `add_input_folder()`, `add_output_folder()`, `add_cm_file()`
- `get_recent_input_folders()` - Returns last 5 valid paths
- `load_from_config()`, `save_to_config()` - JSON persistence

**Storage**: `recents_config.json`

**GUI Integration**: QComboBox dropdowns in main_app.py

---

### report_generator.py (542 lines)
**HTML processing report generation** *(v2.1.1)*

**Key Function**: `generate_processing_report(results_list, output_path)`

**Report Sections**:
- **Summary Statistics**: Total requirements, avg confidence, file count
- **Quality Metrics**: Confidence distribution, priority breakdown
- **File Details**: Per-file extraction results
- **Warnings & Errors**: Issues encountered during processing

**Output Format**: HTML with embedded CSS, color-coded metrics

**Naming**: `YYYY.MM.DD_HHMMSS_Processing_Report.html`

---

### keyword_profiles.py (~150 lines estimated)
**Keyword profile management system** *(v2.2 - merged)*

**Key Functions**:
- `load_profiles()` - Load from `keyword_profiles.json`
- `save_profiles()` - Persist profile changes
- `get_profile_keywords(profile_name)` - Retrieve keyword set

**Predefined Profiles**:
1. **Generic**: Default keywords (shall, must, should, etc.)
2. **Aerospace**: DO-178C, DO-254 compliance keywords
3. **Medical**: IEC 62304, FDA compliance keywords
4. **Automotive**: ISO 26262, ASPICE keywords
5. **Software**: Agile, user story keywords
6. **Safety**: Safety-critical system keywords

**Custom Profiles**: User-defined profiles with custom keyword sets

**GUI Integration**: Profile selector dropdown + "Manage Profiles" dialog

---

### requirement_categorizer.py (~180 lines estimated)
**Automatic requirement categorization** *(v2.2 - merged)*

**Key Function**: `categorize_requirement(requirement_text)`

**9 Categories**:
1. **Functional**: Core system functionality
2. **Safety**: Safety-critical requirements
3. **Performance**: Speed, throughput, efficiency
4. **Security**: Authentication, encryption, access control
5. **Interface**: APIs, user interfaces, protocols
6. **Data**: Data management, storage, integrity
7. **Compliance**: Regulatory, standards compliance
8. **Documentation**: Documentation requirements
9. **Testing**: Test, verification requirements

**Algorithm**: Keyword matching + regex patterns

**Excel Integration**: Adds "Category" column (Column J)

---

### language_detector.py (~120 lines estimated)
**Language detection for multi-lingual support** *(v3.0 - merged)*

**Key Function**: `detect_language(text)`

**Dependencies**: `langdetect` library

**Supported Languages**: English, French, German, Italian, Spanish

**Returns**: ISO 639-1 language code (e.g., 'en', 'fr', 'de')

**Fallback**: Defaults to English if detection fails

**Purpose**: Enable language-specific NLP model selection

---

### language_config.py (~100 lines estimated)
**Multi-lingual configuration management** *(v3.0 - merged)*

**Key Data Structures**:
- `LANGUAGE_MODELS`: Maps language codes to spaCy models
- `DEFAULT_KEYWORDS`: Language-specific keyword sets
- `PRIORITY_KEYWORDS`: Language-specific priority detection

**Supported spaCy Models**:
- English: `en_core_web_sm`
- French: `fr_core_news_sm`
- German: `de_core_news_sm`
- Italian: `it_core_news_sm`
- Spanish: `es_core_news_sm`

**Purpose**: Centralized language configuration

---

### multilingual_nlp.py (~250 lines estimated)
**Multi-language NLP processing engine** *(v3.0 - merged)*

**Key Class**: `MultilingualNLP`

**Key Methods**:
- `load_model(language_code)` - Load language-specific spaCy model
- `process_text(text, language)` - NLP processing with language detection
- `extract_sentences(doc)` - Language-aware sentence segmentation

**Features**:
- Lazy-loading of language models
- Model caching for performance
- Fallback to English for unsupported languages

**Integration**: Used by `pdf_analyzer_multilingual.py`

---

### pdf_analyzer_multilingual.py (~400 lines estimated)
**Multi-lingual PDF requirement extraction** *(v3.0 - merged)*

**Key Function**: `requirement_finder_multilingual(path, keywords_set, filename, language='auto')`

**Features**:
- Automatic language detection per PDF
- Language-specific keyword matching
- Multi-lingual confidence scoring
- Priority detection across languages

**Algorithm**: Similar to `pdf_analyzer.py` but language-aware

**Status**: Parallel implementation, not yet integrated into main pipeline

---

### database/ (5 files)
**SQLAlchemy ORM and database services** *(v3.0 - merged)*

#### database/database.py
- Database initialization and session management
- SQLite backend (default: `reqbot.db`)

#### database/models.py
**ORM Models**:
- `Project`: Project metadata and settings
- `Document`: PDF document information
- `Requirement`: Extracted requirements with full metadata
- `ProcessingSession`: Processing run history

#### database/services/ (4 service modules)
- **project_service.py**: CRUD operations for projects
- **document_service.py**: Document management
- **requirement_service.py**: Requirement queries and updates
- **session_service.py**: Processing session tracking

**Status**: Fully implemented, not yet integrated into main GUI

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
    'Category': 'Functional',  # NEW in v2.2 (merged)
    'Note': 'filename-Req#1-1:The system...'
}
```

**Note**: The `Category` field is added by `requirement_categorizer.py` and written to Excel column J.

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

All test files are located in the `tests/` directory:

- `tests/test_gui.py` - GUI components (8 tests)
- `tests/test_excel_writer.py` - Excel generation (3 tests)
- `tests/test_highlight_requirements.py` - PDF highlighting (2 tests)
- `tests/test_basil_integration.py` - BASIL integration (25 tests)
- `tests/test_integration*.py` - End-to-end workflows

### Running Tests

```bash
# All tests
pytest -v

# Specific file
pytest tests/test_gui.py

# Specific test
pytest tests/test_gui.py::test_threading_fix_prevents_double_start

# With coverage
pytest --cov=. --cov-report=html
```

### Key Test: Threading Fix (v2.1.1)

```python
# tests/test_gui.py::test_threading_fix_prevents_double_start
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
├── main_app.py                    # GUI application (v2.1.1 threading fix)
├── run_app.py                     # Interactive launcher menu (v2.1.1)
├── processing_worker.py           # Background thread worker
├── RB_coordinator.py              # Pipeline orchestrator
├── version.py                     # Version management (v2.1.1)
│
├── pdf_analyzer.py                # NLP extraction (enhanced v2.0)
├── pdf_analyzer_multilingual.py  # Multi-lingual extraction (v3.0 merged)
├── excel_writer.py                # Excel matrix generator
├── highlight_requirements.py     # PDF annotation (enhanced v2.0)
├── basil_integration.py           # BASIL SPDX 3.0.1 export/import
│
├── config_RB.py                   # Configuration manager
├── get_all_files.py               # File utilities
├── recent_projects.py             # Recent paths manager (v2.1.1)
├── report_generator.py            # HTML report generator (v2.1.1)
│
├── keyword_profiles.py            # Keyword profile system (v2.2 merged)
├── requirement_categorizer.py    # Requirement categorization (v2.2 merged)
│
├── language_detector.py           # Language detection (v3.0 merged)
├── language_config.py             # Multi-lingual config (v3.0 merged)
├── multilingual_nlp.py            # Multi-lingual NLP engine (v3.0 merged)
│
├── database/                      # Database backend (v3.0 merged)
│   ├── database.py                # DB initialization
│   ├── models.py                  # SQLAlchemy ORM models
│   └── services/                  # Database services
│       ├── project_service.py
│       ├── document_service.py
│       ├── requirement_service.py
│       └── session_service.py
│
├── config/                        # Configuration files
├── tests/                         # Test suite (263 passing, 24 files)
│
├── RBconfig.ini                   # Keyword configuration
├── CLAUDE.md                      # This file (AI assistant guide)
├── README.md                      # Project README
├── TODO.md                        # Project roadmap
└── RELEASE_NOTES_v2.2.md         # v2.2.0 release notes
```

---

## Module Dependencies

```
main_app.py (version.py)
 ├─ recent_projects.py (singleton)
 └─ processing_worker.py
     ├─ keyword_profiles.py (v2.2 merged)
     ├─ report_generator.py (v2.1.1)
     ├─ config_RB.py (configparser)
     ├─ get_all_files.py (os)
     └─ RB_coordinator.py
         ├─ pdf_analyzer.py (spacy, fitz, pandas)
         │   └─ requirement_categorizer.py (v2.2 merged)
         ├─ pdf_analyzer_multilingual.py (v3.0 merged - not integrated yet)
         │   ├─ language_detector.py (langdetect)
         │   ├─ language_config.py
         │   └─ multilingual_nlp.py (multi-language spacy)
         ├─ excel_writer.py (openpyxl, pandas)
         ├─ basil_integration.py (json, pandas)
         └─ highlight_requirements.py (fitz)

database/ (v3.0 merged - not integrated yet)
 ├─ database.py (SQLAlchemy)
 ├─ models.py (ORM: Project, Document, Requirement, ProcessingSession)
 └─ services/
     ├─ project_service.py
     ├─ document_service.py
     ├─ requirement_service.py
     └─ session_service.py

run_app.py (v2.1.1 - standalone launcher)
 └─ main_app.py
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

| Version | Date | Status | Changes |
|---------|------|--------|---------|
| 3.0.0 | TBD | In Development | Multi-lingual extraction, database backend (features merged to main) |
| 2.3.0 | 2025-11-19 | **Released** | Phase 1 Complete: Drag & Drop support, Progress Details, CI/CD Pipeline (280+ tests) |
| 2.2.0 | 2025-11-18 | Released | Keyword profiles, requirement categorization (9 categories) |
| 2.1.1 | 2025-11-18 | Released | Thread cleanup fix, recent projects, HTML reports, confidence threshold UI |
| 2.1.0 | 2025-11-17 | Released | UX enhancements, confidence scoring, BASIL integration |
| 2.0.0 | 2025-11-15 | Released | Major NLP improvements, confidence scoring system |
| 1.x | Previous | Released | Base functionality |

**Note**: v2.3.0 "UX & Infrastructure - Phase 1" is complete with drag & drop, progress details, and CI/CD pipeline. v3.0 features (multilingual, database) have been merged to main branch but not yet integrated into the GUI. v2.4 (Quality Foundation) planned for Q2 2026.

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
pytest tests/test_gui.py -v     # GUI tests only
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

**Last Updated**: 2025-11-19
**Maintained By**: Project maintainers
**AI Assistant Version**: Optimized for Claude Code

---

*This is a living document. Update as the codebase evolves.*
