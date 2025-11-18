# ReqBot 2.2.0

**Automatic Requirements Extraction Tool for PDF Specifications**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-2.2.0--dev-orange.svg)](TODO.md)
[![Development Status](https://img.shields.io/badge/status-in%20development-yellow.svg)](RELEASE_NOTES_v2.2.md)

ReqBot is a powerful desktop application that automatically extracts requirements from PDF specification documents using advanced NLP techniques. It generates compliance matrices in Excel format, BASIL-compatible SPDX exports, and creates annotated PDFs with highlighted requirements.

---

## ✨ What's New

### 🚧 Version 2.2.0 (In Development - Q2 2026)

Version 2.2.0 focuses on **quality of life improvements and performance**:

- 🔍 **Search & Filter in Results** (Planned) - Find and filter extracted requirements in GUI
- 🚀 **Parallel PDF Processing** (Planned) - 2-3x faster batch operations
- 🎯 **Drag & Drop Support** (Planned) - Drag PDFs directly into application
- 📺 **Real-Time Preview** (Planned) - Preview requirements during processing
- 🧪 **Enhanced Testing** (Planned) - 80%+ test coverage, CI/CD pipeline
- 📚 **Comprehensive Documentation** (Planned) - Video tutorials, user manual, FAQ

[📝 See Full v2.2 Release Notes](RELEASE_NOTES_v2.2.md)

### Version 2.1.1 (Released)

Critical bug fix for threading and UX enhancements:

- 🐛 **Fixed Threading Issue** - Users can now run multiple sequential extractions without restarting
- 📁 **Recent Files/Projects** - Quick access to last 5 used paths via dropdown menus
- 🎚️ **Adjustable Confidence Threshold** - Interactive slider control (0.0-1.0)

### Version 2.1.0 Features:

- 📁 **Recent Files/Projects** - Quick access to last 5 used paths via dropdown menus
- 🎚️ **Adjustable Confidence Threshold** - Interactive slider control (0.0-1.0) with real-time filtering
- 📊 **Confidence Display in Excel** - Color-coded confidence scores (Green/Yellow/Red) with auto-filtering
- 🔧 **Excel Column Corrections** - Fixed Priority column positioning after Confidence addition
- 🔗 **BASIL SPDX 3.0.1 Integration** - Automatic export of requirements to industry-standard SPDX format
- 📄 **HTML Processing Reports** - Automatic generation of detailed processing reports with statistics
- 🏷️ **Requirement Categorization** - Auto-categorize requirements into 9 categories (Functional, Safety, Performance, etc.)
- 🎯 **Keyword Profiles** - Predefined and custom keyword sets for different domains (Aerospace, Medical, Automotive, etc.)
- ✅ **Enhanced Testing** - 270+ tests organized in tests/ directory (including threading fix verification)

[📝 See v2.1 Changes](TODO.md)

---

## 🚀 Key Features

### Intelligent Extraction
- **NLP-Powered**: Uses spaCy for accurate sentence segmentation and requirement identification
- **Exact Word Matching**: Precise keyword matching with regex word boundaries
- **Pattern Recognition**: Detects 6 categories of requirement patterns (modal verbs, compliance indicators, etc.)
- **Quality Scoring**: Confidence scores (0.0-1.0) for every extracted requirement

### Advanced PDF Handling
- **Multi-Column Layout Support**: Correctly processes technical specs with multiple columns
- **Smart Text Preprocessing**: Handles hyphenated words, Unicode normalization, page number removal
- **Highlight Size Validation**: Prevents oversized highlights (max 40% page coverage)
- **Fallback Annotations**: Text-only notes when highlighting fails

### Excel Compliance Matrix
- **Color-Coded Priorities**: Visual priority indicators (High/Medium/Low/Security)
- **Confidence Scoring**: Color-coded confidence levels (Green ≥0.8, Yellow 0.6-0.8, Red <0.6)
- **Requirement Categorization**: Automatic classification into 9 categories (Functional, Safety, Performance, Security, Interface, Data, Compliance, Documentation, Testing)
- **Data Validations**: Dropdown lists for standardized input
- **Formula Integration**: Automated compliance score calculations
- **Template-Based**: Uses customizable Excel templates

### User Experience
- **Modern GUI**: PySide6-based desktop application
- **Background Processing**: Non-blocking UI with progress tracking
- **Comprehensive Logging**: Detailed logs for debugging and quality assurance
- **Recent Projects**: Quick access to last 5 used paths via dropdown menus
- **Keyword Profiles**: Predefined profiles for different domains (Aerospace, Medical, Automotive, Software, Safety, Generic)
- **Processing Reports**: Automatic HTML reports with statistics, quality metrics, and warnings

### BASIL SPDX 3.0.1 Integration
- **Industry Standard Export**: Automatic export to SPDX 3.0.1 JSON-LD format (BASIL-compatible)
- **Requirement Interchange**: Share requirements with other tools using standardized SPDX format
- **Import Support**: Import existing BASIL requirements with merge strategies (append, update, replace)
- **Validation**: Built-in SPDX format validation to ensure compliance
- **Traceability**: Maintains requirement IDs and metadata for traceability

---

## 📊 Performance Metrics

| Metric | Before v2.0 | After v2.0 | Improvement |
|--------|------------|-----------|-------------|
| Full-Page Highlight Errors | ~15% | <1% | **93% reduction** |
| False Positive Extractions | ~30% | ~5-8% | **73-83% reduction** |
| Processing Speed | Baseline | 3-5x | **300-400% faster** |
| PDF Parsing Quality | Fair | Excellent | **40-50% better** |

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** (Required for PySide6 compatibility)
- **Microsoft Build Tools 2022** (Windows only, for certain dependencies)

### Step 1: Clone the Repository

```bash
git clone https://github.com/francosax/ReqBot.git
cd ReqBot
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download spaCy Language Model

```bash
# Install specific version compatible with Python 3.8
pip install spacy==3.4.4

# Download the English language model
python -m spacy download en_core_web_sm
```

**Note**: `en_core_web_sm` is not a standard pip package. It's a pre-trained spaCy model installed via the `spacy download` command.

---

## 🎮 Usage

### Option 1: Launch via Menu (Recommended)

```bash
python run_app.py
```

This presents an interactive menu:
1. Run GUI Application
2. Run Tests
3. Exit

### Option 2: Direct GUI Launch

```bash
python main_app.py
```

### GUI Workflow

1. **Select Input Folder**: Choose folder containing PDF specification files (or use Recent dropdown)
2. **Select Output Folder**: Choose where to save results (or use Recent dropdown)
3. **Load Compliance Matrix Template**: Select Excel template file (or use Recent dropdown)
4. **Choose Keyword Profile** (Optional): Select from Generic, Aerospace, Medical, Automotive, Software, or Safety profiles
5. **Adjust Confidence Threshold** (Optional): Use slider to set minimum confidence (0.0-1.0, default 0.5)
6. **Start Processing**: Click "Start" to begin extraction
7. **Review Results**:
   - Excel compliance matrix with requirements, confidence scores, and categories
   - Annotated PDF with highlighted requirements
   - BASIL SPDX 3.0.1 JSON-LD export
   - HTML processing report with statistics and quality metrics

---

## 📁 Project Structure

```
ReqBot/
├── main_app.py                      # Main GUI application (v2.1.1 threading fix)
├── run_app.py                       # Interactive launcher menu
├── version.py                       # Version information (single source of truth)
├── RB_coordinator.py                # Processing pipeline orchestrator
├── pdf_analyzer.py                  # NLP extraction engine (v2.0 enhanced)
├── pdf_analyzer_multilingual.py     # Multilingual NLP extraction (v3.0 in progress)
├── highlight_requirements.py        # PDF annotation module (v2.0 enhanced)
├── excel_writer.py                  # Excel matrix generator
├── basil_integration.py             # BASIL SPDX 3.0.1 export/import
├── report_generator.py              # HTML processing report generator
├── requirement_categorizer.py       # Automatic requirement categorization
├── keyword_profiles.py              # Keyword profile management
├── recent_projects.py               # Recent files/folders manager
├── language_detector.py             # Language detection (v3.0 in progress)
├── language_config.py               # Language configuration (v3.0 in progress)
├── multilingual_nlp.py              # Multilingual NLP support (v3.0 in progress)
├── config_RB.py                     # Configuration manager
├── processing_worker.py             # Background thread worker
├── get_all_files.py                 # File utilities
├── RBconfig.ini                     # Keyword configuration
├── keyword_profiles.json            # Keyword profiles storage
├── recents_config.json              # Recent paths storage
├── template_compliance_matrix.xlsx  # Excel template
├── database/                        # Database backend (v3.0 in progress)
│   ├── __init__.py
│   ├── database.py                  # Database initialization
│   ├── models.py                    # SQLAlchemy models
│   └── services/                    # Database services
├── tests/                           # Test suite (270+ tests)
│   ├── conftest.py                  # Pytest configuration
│   ├── test_gui.py                  # GUI tests (8 tests)
│   ├── test_excel_writer.py         # Excel tests (3 tests)
│   ├── test_highlight_requirements.py # PDF highlighting tests (2 tests)
│   ├── test_basil_integration.py    # BASIL tests (25 tests)
│   ├── test_report_generator.py     # Report generator tests
│   ├── test_database_*.py           # Database tests (v3.0)
│   ├── test_language_*.py           # Language detection tests (v3.0)
│   ├── test_multilingual_nlp.py     # Multilingual NLP tests (v3.0)
│   └── test_integration*.py         # Integration tests
├── CLAUDE.md                        # Developer documentation
├── README.md                        # This file
├── TODO.md                          # Project roadmap
└── requirements.txt                 # Python dependencies
```

---

## ⚙️ Configuration

### Customize Requirement Keywords

Edit `RBconfig.ini` to customize requirement keywords:

```ini
[RequirementKeywords]
keywords = shall, must, should, will, has to, require, required
```

### Adjust Extraction Parameters

Edit constants in `pdf_analyzer.py`:

```python
MIN_REQUIREMENT_LENGTH_WORDS = 5    # Minimum sentence length
MAX_REQUIREMENT_LENGTH_WORDS = 100  # Maximum sentence length
```

Edit constants in `highlight_requirements.py`:

```python
MAX_HIGHLIGHT_COVERAGE_PERCENT = 40  # Maximum page coverage
```

---

## 📊 Output Format

### Excel Compliance Matrix

**Sheet Name**: `MACHINE COMP. MATRIX`

**Columns Include**:
- Label Number
- Description (requirement text)
- Page number
- Keyword that triggered extraction
- **Confidence score** with color coding (NEW in v2.0)
- Priority (High/Medium/Low/Security)
- **Category** (Functional, Safety, Performance, etc.) (NEW in v2.1)
- Compliance status fields
- Verification fields
- Notes and metadata

**Starting Row**: Data written from row 5 (rows 1-4 reserved for headers)

### Annotated PDF

- **Yellow highlights** on requirement text
- **Text annotations** with label and description
- **Fallback annotations** for oversized or unfound highlights

### Processing Report (HTML)

**Filename**: `YYYY.MM.DD_HHMMSS_Processing_Report.html`

**Contents**:
- Processing summary with total requirements extracted
- Average confidence score across all requirements
- File-by-file breakdown with statistics
- Warnings and errors encountered
- Quality metrics and visualizations
- Color-coded confidence indicators

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests (from project root)
pytest -v

# Specific test file
pytest tests/test_gui.py -v

# Specific test
pytest tests/test_gui.py::test_threading_fix_prevents_double_start -v

# With coverage
pytest --cov=. --cov-report=html
```

**Test Coverage** (270+ tests organized in `tests/` directory):
- ✅ GUI components (8 tests) - Threading, UI elements, user interactions
- ✅ Excel writer functionality (3 tests) - Matrix generation, formatting
- ✅ PDF highlighting (2 tests) - Annotation, highlight validation
- ✅ BASIL integration (25 tests) - Export, import, validation, merge strategies
- ✅ Report generator - HTML report generation with statistics
- ✅ Database models and services (v3.0 in progress) - SQLAlchemy ORM tests
- ✅ Language detection (v3.0 in progress) - Multilingual support tests
- ✅ Multilingual NLP (v3.0 in progress) - Multi-language extraction tests
- ✅ Integration tests - End-to-end workflow validation
- ✅ Thread safety tests - Concurrent operations validation

**Current Status**: 263 passing, 4 pre-existing failures (unrelated to core functionality), 3 pre-existing errors

---

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer guide for AI assistants
- **[NLP_IMPROVEMENT_ANALYSIS.md](NLP_IMPROVEMENT_ANALYSIS.md)** - Detailed technical analysis of improvements
- **[RELEASE_NOTES_v2.0.md](RELEASE_NOTES_v2.0.md)** - Version 2.0 release notes

---

## 🔧 Tech Stack

### Core Dependencies (v2.1.1)
- **UI Framework**: PySide6 (Qt for Python)
- **PDF Processing**: PyMuPDF (fitz)
- **NLP Engine**: spaCy 3.4.4 with en_core_web_sm model
- **Data Handling**: Pandas, openpyxl
- **Export Formats**: JSON-LD (SPDX 3.0.1), HTML reports
- **Testing**: pytest, pytest-qt (270+ tests)
- **Threading**: QThread for non-blocking operations
- **Configuration**: ConfigParser, JSON

### v3.0 Additional Dependencies (In Development)
- **Database**: SQLAlchemy (PostgreSQL/SQLite support)
- **Multilingual NLP**: spaCy models for FR, DE, IT, ES, PT
- **Language Detection**: langdetect, pycld2
- **Concurrency**: Threading locks for database operations

---

## 📈 NLP Improvements Timeline

### Phase 1: Critical Fixes (2025-11)
- Fixed substring keyword matching
- Added sentence length validation
- Added highlight size validation
- **Result**: 93% reduction in full-page highlights

### Phase 2: Performance & Quality (2025-11)
- Implemented spaCy model caching
- Added advanced text preprocessing
- Introduced confidence scoring system
- **Result**: 3-5x faster processing + quality metrics

### Phase 3: Advanced Features (2025-11)
- Multi-column layout handling
- Requirement pattern matching
- Missed sequence fallback
- **Result**: Complex PDF support + transparency

---

## 🎯 Use Cases

- **Regulatory Compliance**: Extract requirements from standards and regulations
- **Technical Specifications**: Process engineering specification documents
- **Contract Analysis**: Identify contractual requirements and obligations
- **Quality Assurance**: Create compliance matrices for verification
- **Requirements Engineering**: Support requirements management workflows

---

## 🐛 Known Limitations

- **PDF Format Requirements**: Works best with text-based PDFs (not scanned images). OCR support planned for v2.5+
- **Language Support**: Currently optimized for English documents. **Note**: Multilingual support (v3.0) is in active development with language detection and support for French, German, Italian, Spanish, and Portuguese
- **Template Dependency**: Excel template must contain "MACHINE COMP. MATRIX" sheet name exactly
- **Pattern-Enhanced Detection**: Uses combination of keywords and NLP patterns for requirement identification

## 🚧 Features in Development

The following features are actively being developed for v3.0:

- **Multilingual Extraction**: Language detection and NLP support for French, German, Italian, Spanish, Portuguese
  - Modules: `language_detector.py`, `language_config.py`, `multilingual_nlp.py`, `pdf_analyzer_multilingual.py`
  - Status: Core functionality implemented, integration testing in progress

- **Database Backend**: SQLAlchemy-based persistence layer with PostgreSQL/SQLite support
  - Modules: `database/models.py`, `database/services/`, `database/database.py`
  - Features: Project management, document tracking, requirement versioning, processing sessions, change history
  - Status: Models complete, services in development

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Testing**: Ensure all tests pass before submitting PR

```bash
pytest -v
```

---

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

**GPL-3.0**: You are free to use, modify, and distribute this software under the terms of the GPL-3.0 license. Any modifications or derivative works must also be released under GPL-3.0.

---

## 🙏 Acknowledgments

- **spaCy**: For the excellent NLP library
- **PyMuPDF**: For powerful PDF processing capabilities
- **PySide6/Qt**: For the robust GUI framework

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/francosax/ReqBot/issues)
- **Documentation**: See [CLAUDE.md](CLAUDE.md) for developer guide
- **Analysis**: See [NLP_IMPROVEMENT_ANALYSIS.md](NLP_IMPROVEMENT_ANALYSIS.md) for technical details

---

## 🔮 Roadmap

### ✅ Completed in v2.1:
- ✅ User-adjustable confidence thresholds in GUI
- ✅ Excel export with confidence score conditional formatting
- ✅ HTML processing reports with quality metrics
- ✅ Recent files/projects management
- ✅ Requirement categorization (9 categories)
- ✅ Keyword profile management
- ✅ BASIL SPDX 3.0.1 integration
- ✅ Thread cleanup fix for multiple sequential runs

### Planned for v2.2 (Q2 2026):
- Search/filter functionality in GUI
- Dark mode theme
- Performance optimizations

### In Development (v3.0 - 2027):
- 🚧 **Multi-language support** - Language detection and multilingual NLP (active development)
- 🚧 **Database backend** - SQLAlchemy-based persistence with PostgreSQL/SQLite support (active development)
- Web-based version with FastAPI/React
- REST API for programmatic access
- Machine learning-based requirement classifier
- OCR support for scanned PDFs
- Requirements traceability across documents

### Long-Term Vision:
- LLM integration (GPT-4/Claude) for smart extraction
- Collaborative workflows with multi-user support
- Platform integrations (Jira, Azure DevOps, Confluence)
- Cloud processing option
- Advanced analytics and reporting dashboard

---

## 📊 Version History

- **v2.2.0** (Q2 2026 - In Development) - Quality of life improvements, performance optimizations, enhanced testing
- **v2.1.1** (2025-11-18) - Bug fix: Thread cleanup for multiple sequential extractions
- **v2.1.0** (2025-11-17) - UX enhancements: Recent files/projects, adjustable confidence threshold, BASIL integration
- **v2.0.0** (2025-11-15) - Major NLP improvements: accuracy, performance, quality scoring
- **v1.2** (Previous) - Base functionality with GUI and Excel generation
- **v1.x** - Initial releases

---

**Built with ❤️ for requirements engineers and compliance professionals**

*Making requirement extraction accurate, fast, and reliable.*
