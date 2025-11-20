# ReqBot TODO List & Future Suggestions

**Last Updated**: 2025-11-19
**Current Version**: 2.3.0 (Released)
**Status**: v2.3 Phase 1 complete, v3.0 multilingual features merged to main

This document tracks future enhancements, feature requests, and improvements for ReqBot.

---

## 📋 Table of Contents

1. [Immediate Priorities (v2.1)](#immediate-priorities-v21)
2. [Short-Term Enhancements (v2.2)](#short-term-enhancements-v22)
3. [Phase 1 Complete (v2.3)](#phase-1-complete-v23)
4. [Phase 2 Planning (v2.4)](#phase-2-planning-v24)
5. [Medium-Term Features (v2.5)](#medium-term-features-v25)
6. [Long-Term Vision (v3.0)](#long-term-vision-v30)
7. [Technical Debt](#technical-debt)
8. [Documentation](#documentation)
9. [Testing](#testing)
10. [Performance Optimizations](#performance-optimizations)
11. [User Experience](#user-experience)
12. [Ideas Backlog](#ideas-backlog)

---

## 🔥 Immediate Priorities (v2.1)

**Target Release**: Q1 2026
**Focus**: Quick wins and user-requested features

### Features

- [x] **Display Confidence Scores in Excel Output** ✅ **COMPLETED**
  - Priority: High
  - Effort: 2-3 hours
  - ✅ Add conditional formatting (green/yellow/red) based on confidence
  - ✅ Add filter for low-confidence requirements (<0.6)
  - Location: `excel_writer.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: Confidence scores now displayed in column E with color coding (Green ≥0.8, Yellow 0.6-0.8, Red <0.6) and auto-filter enabled

- [x] **User-Adjustable Confidence Threshold in GUI** ✅ **COMPLETED**
  - Priority: High
  - Effort: 3-4 hours
  - ✅ Add slider/spinbox in GUI for minimum confidence (default: 0.5)
  - ✅ Filter requirements below threshold
  - Location: `main_app.py`, `processing_worker.py`, `RB_coordinator.py`, `pdf_analyzer.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: Added interactive slider and spinbox controls in GUI for real-time confidence threshold adjustment. Default value: 0.5 (50%). Range: 0.0-1.0. Requirements below threshold are filtered during extraction.

- [x] **Export Processing Report** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 4-5 hours
  - ✅ Generate summary HTML report after processing
  - ✅ Include: total requirements, avg confidence, warnings, errors
  - ✅ Color-coded confidence scores with visual styling
  - ✅ Per-file breakdown with warnings tracking
  - Location: `report_generator.py`, integrated in `processing_worker.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: HTML reports auto-generated after each processing run with comprehensive statistics, quality metrics, file details, warnings, and errors. Reports saved as YYYY.MM.DD_HHMMSS_Processing_Report.html

- [x] **Recent Files/Projects** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 2-3 hours
  - ✅ Remember last 5 input/output folders
  - ✅ Add dropdown or menu for quick access
  - ✅ Store in config file (JSON)
  - Location: `recent_projects.py`, `main_app.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: QComboBox dropdowns show last 5 recent paths for input folders, output folders, and compliance matrix files. Paths saved to recents_config.json automatically when processing starts. Non-existent paths automatically filtered from dropdown. Singleton pattern for global access.

### Bug Fixes

- [x] **Windows Fatal Exception on Test Cleanup** ✅ **ADDRESSED**
  - Priority: Low (doesn't affect functionality)
  - Effort: 2-4 hours
  - ✅ Investigated Qt cleanup issue on Windows
  - ✅ Added comprehensive cleanup code in test fixtures
  - ✅ Created conftest.py with session-wide Qt cleanup
  - ✅ Added proper thread cleanup and deleteLater() handling
  - Location: `tests/test_gui.py`, `tests/conftest.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: Enhanced Qt test cleanup with proper thread termination, event processing, and garbage collection. Should significantly reduce or eliminate Windows fatal exceptions during test cleanup.

- [x] **Progress Bar Not Always Accurate** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 1-2 hours
  - ✅ Improved progress tracking granularity
  - ✅ Added per-file progress breakdown with sub-steps
  - ✅ Reserved last 10% for report generation
  - ✅ Progress updates even on errors
  - ✅ File counter in log messages [1/5]
  - Location: `processing_worker.py`
  - **Implementation Date**: 2025-11-17
  - **Details**: Progress bar now shows more accurate progress with per-file tracking (0-90% for files, 90-100% for report generation), intermediate updates during file processing, and better handling of edge cases.

- [x] **Thread Cleanup Preventing Multiple Sequential Extractions** ✅ **COMPLETED**
  - Priority: High
  - Effort: 2-3 hours
  - ✅ Fixed thread event loop not terminating after processing
  - ✅ Added proper quit() and wait() calls in completion handlers
  - ✅ Added thread cleanup in error and cancel handlers
  - ✅ Memory leak prevention with proper object cleanup
  - Location: `main_app.py` (lines 550-580, 514-516)
  - **Implementation Date**: 2025-11-18
  - **Details**: Users can now run requirement extraction multiple times without restarting the application. Thread properly terminates with quit() + wait(), references set to None for garbage collection. Automated test confirms fix works correctly.
  - **Test**: `tests/test_gui.py::test_threading_fix_prevents_double_start` (PASSED)

---

## 🚀 Short-Term Enhancements (v2.2)

**Target Release**: Q2 2026
**Focus**: Quality of life improvements

### Features

- [ ] **Batch Processing Mode** ⏸️ **DEFERRED TO v3.0**
  - Priority: High
  - Effort: 1 week
  - Process multiple folders in one run
  - Generate combined compliance matrix
  - Progress tracking for batch operations
  - **Status**: Deferred to v3.0 - Focus shifted to enterprise features

- [x] **Requirement Categories/Tags** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 4-5 days
  - ✅ Auto-categorize requirements (functional, safety, performance, etc.)
  - ✅ Add category column to Excel output (Column J)
  - ✅ Use NLP patterns for categorization
  - Location: `requirement_categorizer.py`, integrated in `pdf_analyzer.py`, `excel_writer.py`
  - **Implementation Date**: 2025-11-18
  - **Details**: Automatic categorization into 9 categories (Functional, Safety, Performance, Security, Interface, Data, Compliance, Documentation, Testing) using keyword matching and regex patterns. Categories automatically added to Excel output in column J.

- [ ] **Search/Filter in Results**
  - Priority: Medium
  - Effort: 3-4 days
  - Add search functionality in GUI for extracted requirements
  - Filter by page, keyword, priority, confidence
  - Preview before exporting
  - **Status**: Deferred to future release (complex GUI work)

- [x] **Custom Keyword Sets** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 2-3 days
  - ✅ Allow multiple keyword profiles (aerospace, medical, automotive)
  - ✅ Save/load keyword sets from GUI
  - ✅ Predefined templates for common domains
  - Location: `keyword_profiles.py`, integrated in `main_app.py`, `processing_worker.py`
  - **Implementation Date**: 2025-11-18
  - **Details**: Full keyword profile management system with 6 predefined profiles (Generic, Aerospace, Medical, Automotive, Software, Safety). GUI includes profile selector dropdown and "Manage Profiles" dialog for creating, editing, and deleting custom profiles. Profiles saved to keyword_profiles.json.

- [ ] **Undo/Redo for Manual Edits** ⏸️ **DEFERRED TO v3.0**
  - Priority: Low
  - Effort: 1 week
  - Allow editing requirements before export
  - Undo/redo functionality
  - Mark manual edits differently
  - **Status**: Deferred to v3.0 - Will be part of web-based version

### Improvements

- [ ] **Dark Mode Theme** ⏸️ **DEFERRED TO v3.0**
  - Priority: Low
  - Effort: 2-3 days
  - Add dark theme option
  - System theme detection
  - User preference storage
  - **Status**: Deferred to v3.0 - Will be part of web UI redesign

- [ ] **Internationalization (i18n)** ⏸️ **DEFERRED TO v3.0**
  - Priority: Low
  - Effort: 1-2 weeks
  - Support for multiple languages
  - Start with Italian, German, French
  - Translation files structure
  - **Status**: Deferred to v3.0 - Will be implemented with web-based version

---

## 🎨 Phase 1 Complete (v2.3)

**Target Release**: Q1 2026
**Focus**: UX & Infrastructure improvements
**Status**: ✅ **RELEASED** (2025-11-19)

### Features Completed

- [x] **Drag & Drop Support** ✅ **COMPLETED**
  - Custom DragDropComboBox widget
  - Folder drag & drop for Input/Output fields
  - .xlsx file drag & drop for Compliance Matrix
  - Automatic validation and visual feedback
  - 11 unit tests + integration test

- [x] **Progress Details Enhancement** ✅ **COMPLETED**
  - Real-time file processing status
  - Current step display (analyzing, extracting, etc.)
  - File counter (e.g., "File 1/3")
  - Progress detail label in GUI
  - 6 unit tests + integration test

- [x] **CI/CD Pipeline** ✅ **COMPLETED**
  - GitHub Actions workflow
  - Multi-Python version testing (3.9, 3.10, 3.11)
  - Code quality checks (flake8, black, isort)
  - Build verification
  - Coverage reporting to Codecov

**Total Tests**: 280+ tests passing
**Release Date**: 2025-11-19
**Codename**: "UX & Infrastructure - Phase 1"

---

## 🧪 Phase 2 Planning (v2.4)

**Target Release**: Q2 2026
**Focus**: Quality Foundation
**Status**: 🔜 **PLANNED**

### Proposed Features

- [ ] **Increase Test Coverage to 80%+**
  - Priority: High
  - Effort: 1-2 weeks
  - Focus on: `RB_coordinator.py`, `pdf_analyzer.py`
  - Integration tests with real PDF samples
  - Performance and load tests

- [ ] **Additional GUI Polish**
  - Priority: Medium
  - Effort: 1 week
  - Modern UI refinements
  - Enhanced tooltips and help text
  - Improved error messages
  - Better visual feedback

- [ ] **Requirements Traceability**
  - Priority: Medium
  - Effort: 2-3 weeks
  - Link requirements across multiple documents
  - Track requirement changes over versions
  - Generate traceability matrix

---

## 📊 Medium-Term Features (v2.5)

**Target Release**: Q3-Q4 2026
**Focus**: Advanced capabilities

### Major Features

- [ ] **OCR Support for Scanned PDFs**
  - Priority: High
  - Effort: 2-3 weeks
  - Integrate Tesseract or similar OCR engine
  - Detect scanned vs text PDFs automatically
  - Quality indicator for OCR text
  - Dependencies: `pytesseract`, `pdf2image`

- [ ] **Machine Learning Requirement Classifier**
  - Priority: High
  - Effort: 3-4 weeks
  - Train ML model on labeled requirement data
  - Replace/augment keyword matching
  - Include confidence from ML model
  - Technologies: scikit-learn or spaCy's text classifier

- [ ] **Documentation Improvements**
  - Priority: Medium
  - Effort: 3-5 days
  - Update user manual
  - Create video tutorials
  - FAQ document
  - Configuration guide

- [ ] **Export to Multiple Formats**
  - Priority: Medium
  - Effort: 1-2 weeks
  - Support for: CSV, JSON, XML, Markdown
  - DOORS integration format
  - Jama Connect format
  - ReqIF standard format

- [ ] **Requirement Validation Rules**
  - Priority: Medium
  - Effort: 2 weeks
  - Check requirements against quality criteria
  - Detect ambiguous words (may, could, etc.)
  - Flag incomplete requirements
  - Suggest improvements

### Advanced NLP

- [ ] **Coreference Resolution**
  - Priority: Medium
  - Effort: 1-2 weeks
  - Resolve "it", "they", "this" references
  - Improve requirement context understanding

- [ ] **Negation Detection**
  - Priority: Medium
  - Effort: 1 week
  - Identify negative requirements ("shall not", "must not")
  - Mark negations in output
  - Separate priority category

- [ ] **Temporal Requirement Detection**
  - Priority: Low
  - Effort: 1 week
  - Detect time-based requirements ("within 5 seconds")
  - Extract temporal constraints
  - Add to Excel output

---

## 🌟 Long-Term Vision (v3.0)

**Target Release**: 2027
**Focus**: Enterprise features and platform

### Enterprise Features

- [ ] **Web-Based Version**
  - Priority: High
  - Effort: 2-3 months
  - FastAPI or Flask backend
  - React/Vue frontend
  - Multi-user support
  - Cloud storage integration

- [ ] **REST API**
  - Priority: High
  - Effort: 1 month
  - API for programmatic access
  - Webhook support
  - Integration with CI/CD pipelines

- [ ] **Database Backend**
  - Priority: Medium
  - Effort: 3-4 weeks
  - Store requirements in database (PostgreSQL/SQLite)
  - Version history tracking
  - Advanced querying capabilities

- [ ] **User Management & Permissions**
  - Priority: Medium (for web version)
  - Effort: 2-3 weeks
  - User authentication
  - Role-based access control
  - Audit logging

- [ ] **Collaborative Workflow**
  - Priority: Medium
  - Effort: 1-2 months
  - Multi-user editing
  - Comments and annotations
  - Approval workflows
  - Notification system

### AI/ML Enhancements

- [ ] **LLM Integration for Smart Extraction**
  - Priority: High
  - Effort: 1-2 months
  - Use GPT-4/Claude for requirement extraction
  - Fallback to traditional NLP
  - Hybrid approach for best results

- [ ] **Automatic Requirement Refinement**
  - Priority: Medium
  - Effort: 3-4 weeks
  - AI suggests improvements to requirements
  - Checks for SMART criteria
  - Reword ambiguous requirements

- [ ] **Semantic Similarity Search**
  - Priority: Medium
  - Effort: 2-3 weeks
  - Find similar requirements across documents
  - Detect duplicates
  - Suggest requirement consolidation

### Platform Integration

- [ ] **Jira Integration**
  - Priority: Medium
  - Effort: 2-3 weeks
  - Export requirements as Jira tickets
  - Bidirectional sync

- [ ] **Azure DevOps Integration**
  - Priority: Medium
  - Effort: 2-3 weeks
  - Export as work items
  - Integration with boards

- [ ] **Confluence Integration**
  - Priority: Low
  - Effort: 1-2 weeks
  - Export to Confluence pages
  - Auto-generate documentation

---

## 🔧 Technical Debt

### Code Quality

- [ ] **Type Hints Throughout Codebase**
  - Priority: Medium
  - Effort: 1 week
  - Add type hints to all functions
  - Use mypy for type checking
  - Improve IDE autocomplete

- [ ] **Refactor RB_coordinator.py**
  - Priority: Medium
  - Effort: 3-4 days
  - Break into smaller, focused modules
  - Improve testability
  - Better error handling

- [ ] **Async/Await for File Operations**
  - Priority: Low
  - Effort: 1 week
  - Use asyncio for non-blocking I/O
  - Improve GUI responsiveness
  - Better progress tracking

- [ ] **Dependency Injection**
  - Priority: Low
  - Effort: 1-2 weeks
  - Implement DI pattern
  - Improve testability
  - Reduce coupling

### Architecture

- [ ] **Plugin System**
  - Priority: Low
  - Effort: 2-3 weeks
  - Allow custom extractors
  - Custom export formats
  - Custom validation rules

- [ ] **Event Bus Architecture**
  - Priority: Low
  - Effort: 1-2 weeks
  - Decouple components
  - Easier extension
  - Better state management

---

## 📖 Documentation

### User Documentation

- [ ] **Video Tutorials**
  - Priority: High
  - Effort: 3-4 days
  - Getting started tutorial
  - Advanced features walkthrough
  - YouTube channel

- [ ] **User Manual (PDF)**
  - Priority: Medium
  - Effort: 1 week
  - Comprehensive user guide
  - Screenshots and examples
  - Troubleshooting section

- [ ] **FAQ Document**
  - Priority: Medium
  - Effort: 2-3 days
  - Common questions and answers
  - Best practices
  - Troubleshooting tips

- [ ] **Configuration Guide**
  - Priority: Medium
  - Effort: 1-2 days
  - RBconfig.ini explained
  - Advanced configuration options
  - Examples for different domains

### Developer Documentation

- [ ] **API Documentation (Sphinx)**
  - Priority: Medium
  - Effort: 1 week
  - Auto-generated from docstrings
  - Host on Read the Docs
  - Code examples

- [ ] **Architecture Diagrams**
  - Priority: Medium
  - Effort: 2-3 days
  - System architecture
  - Data flow diagrams
  - Sequence diagrams for key operations

- [ ] **Contributing Guide**
  - Priority: Medium
  - Effort: 1 day
  - How to contribute
  - Code style guidelines
  - PR process

- [ ] **Plugin Development Guide**
  - Priority: Low (after plugin system)
  - Effort: 3-4 days
  - How to create plugins
  - Examples
  - Best practices

---

## 🧪 Testing

### Test Coverage

- [ ] **Increase Test Coverage to 80%+**
  - Priority: High
  - Effort: 1-2 weeks
  - Current: ~40% (estimated)
  - Focus on: `RB_coordinator.py`, `pdf_analyzer.py`
  - Use coverage.py

- [ ] **Integration Tests**
  - Priority: High
  - Effort: 1 week
  - End-to-end workflow tests
  - Test with real PDF samples
  - Multiple document types

- [ ] **Performance Tests**
  - Priority: Medium
  - Effort: 3-4 days
  - Benchmark processing speed
  - Memory usage profiling
  - Large file handling (100+ pages)

- [ ] **Load/Stress Tests**
  - Priority: Low
  - Effort: 2-3 days
  - Batch processing many files
  - Concurrent operations
  - Resource limits

### Test Infrastructure

- [x] **Continuous Integration (CI)** ✅ **COMPLETED**
  - Priority: High
  - Effort: 1-2 days
  - ✅ GitHub Actions workflow configured
  - ✅ Automated testing on push and pull requests
  - ✅ Multi-Python version testing (3.9, 3.10, 3.11)
  - ✅ Code quality checks (flake8, black, isort)
  - ✅ Build verification
  - ✅ Coverage reporting to Codecov
  - Location: `.github/workflows/ci.yml`
  - **Implementation Date**: 2025-11-19
  - **Details**: Full CI/CD pipeline with automated testing, linting, and build verification. Runs on ubuntu-latest with Qt system dependencies. Includes pip package caching for faster builds and spaCy model download automation. Three jobs: Test, Lint, Build.

- [ ] **Test Fixtures Library**
  - Priority: Medium
  - Effort: 3-4 days
  - Sample PDFs for testing
  - Expected outputs
  - Edge cases collection

- [ ] **Mock Objects for External Dependencies**
  - Priority: Medium
  - Effort: 2-3 days
  - Mock file operations
  - Mock spaCy for faster tests
  - Mock PDF operations

---

## ⚡ Performance Optimizations

### Speed Improvements

- [ ] **Parallel PDF Processing**
  - Priority: High
  - Effort: 1 week
  - Process multiple PDFs in parallel
  - Use multiprocessing pool
  - Scale to available CPU cores

- [ ] **Cache Preprocessed Text**
  - Priority: Medium
  - Effort: 2-3 days
  - Cache cleaned PDF text
  - Avoid reprocessing on failures
  - Configurable cache location

- [ ] **Incremental Processing**
  - Priority: Medium
  - Effort: 1 week
  - Only reprocess changed PDFs
  - Track file hashes
  - Skip unchanged documents

- [ ] **Optimize spaCy Pipeline**
  - Priority: Medium
  - Effort: 3-4 days
  - Disable unused pipeline components
  - Use smaller model where appropriate
  - Custom pipeline for requirements

### Memory Optimization

- [ ] **Streaming PDF Processing**
  - Priority: Medium
  - Effort: 1 week
  - Process pages one at a time
  - Reduce memory footprint
  - Handle very large PDFs (1000+ pages)

- [ ] **Memory Profiling**
  - Priority: Low
  - Effort: 2-3 days
  - Identify memory leaks
  - Optimize data structures
  - Use memory_profiler

---

## 🎨 User Experience

### GUI Improvements

- [ ] **Modern UI Redesign**
  - Priority: Medium
  - Effort: 2-3 weeks
  - Qt Material theme
  - Better visual hierarchy
  - Icons and imagery

- [x] **Drag & Drop Support** ✅ **COMPLETED**
  - Priority: High
  - Effort: 1-2 days
  - ✅ Drag folders into Input/Output folder fields
  - ✅ Drag .xlsx files into Compliance Matrix field
  - ✅ Visual feedback during drag operations
  - ✅ Automatic file type validation
  - ✅ Path normalization for cross-platform compatibility
  - Location: `main_app.py` (DragDropComboBox class)
  - **Implementation Date**: 2025-11-19
  - **Details**: Custom DragDropComboBox widget with flexible configuration (accept_files, accept_folders, file_extension). Implements dragEnterEvent and dropEvent handlers with MIME data validation. Input/Output folders accept folders only, CM field accepts .xlsx files only. 11 unit tests added.

- [ ] **Real-Time Preview**
  - Priority: Medium
  - Effort: 1 week
  - Preview extracted requirements in GUI
  - Before exporting to Excel
  - Edit/remove before export

- [x] **Progress Details** ✅ **COMPLETED**
  - Priority: Medium
  - Effort: 2-3 days
  - ✅ Show current file being processed
  - ✅ Display current processing step (analyzing, extracting, etc.)
  - ✅ File counter display (e.g., "File 1/3")
  - ✅ Progress detail label below progress bar
  - ✅ Real-time status updates throughout pipeline
  - Location: `processing_worker.py`, `main_app.py`
  - **Implementation Date**: 2025-11-19
  - **Details**: New signal progress_detail_updated(str) emits detailed status messages. GUI displays progress detail label with current file, step, and counter. 7 progress detail emissions throughout processing pipeline. Automatic reset on completion/error/cancel. 6 unit tests added.

- [ ] **Wizard-Style Interface**
  - Priority: Low
  - Effort: 1 week
  - Step-by-step guided workflow
  - Tooltips and help text
  - Better onboarding

### Notifications

- [ ] **Desktop Notifications**
  - Priority: Low
  - Effort: 1-2 days
  - Notify when processing complete
  - Works when window minimized
  - Cross-platform (Windows, Linux, macOS)

- [ ] **Email Notifications**
  - Priority: Low
  - Effort: 2-3 days
  - Email results when done
  - For long-running processes
  - Configurable SMTP settings

---

## 💡 Ideas Backlog

**Unscheduled ideas for future consideration**

### Analysis Features

- [ ] Requirements complexity scoring
- [ ] Duplicate requirement detection
- [ ] Requirement dependencies visualization
- [ ] Gap analysis against standards
- [ ] Requirements metrics dashboard

### Export Features

- [ ] Word document export with highlighting
- [ ] PowerPoint presentation generation
- [ ] Mind map visualization of requirements
- [ ] PDF with interactive table of contents
- [ ] LaTeX export for academic papers

### Integration Features

- [ ] SharePoint integration
- [ ] Google Drive integration
- [ ] Slack notifications
- [ ] Microsoft Teams integration
- [ ] GitHub Issues export

### Quality Features

- [ ] Grammar checking for requirements
- [ ] Spell checking
- [ ] Readability scoring
- [ ] Consistency checking (terminology)
- [ ] Requirements quality report card

### Advanced NLP

- [x] **Multi-language support (beyond English)** 🚧 **IN PROGRESS - v3.0**
  - Priority: High
  - Effort: 3-4 weeks
  - Support for French, German, Italian, Spanish
  - Using per-language spaCy models
  - Auto-detection with langdetect
  - Offline/internet-independent approach
  - **Status**: Implementation started 2025-11-18
  - **Branch**: claude/multilingual-extraction-v3.0
  - Location: `language_detector.py`, `language_config.py`, `multilingual_nlp.py`
- [ ] Domain-specific language models
- [ ] Custom entity recognition
- [ ] Relationship extraction (dependencies)
- [ ] Automatic glossary generation

### Visualization

- [ ] Requirements heat map by confidence
- [ ] Sankey diagram of requirement flow
- [ ] Timeline visualization for temporal requirements
- [ ] Network graph of related requirements
- [ ] Coverage visualization on PDF pages

### Compliance

- [ ] ISO 26262 compliance checking
- [ ] DO-178C compliance templates
- [ ] IEC 62304 medical device compliance
- [ ] Automotive SPICE templates
- [ ] Custom compliance frameworks

---

## 📝 Notes

### How to Use This TODO List

1. **Pick items** based on priority and effort
2. **Create issues** on GitHub for tracking
3. **Update this file** when items are completed
4. **Move completed items** to CHANGELOG
5. **Add new ideas** as they come up

### Priority Levels

- **High**: Important for users, fixes critical issues
- **Medium**: Nice to have, improves experience
- **Low**: Future enhancements, low impact

### Effort Estimates

- **Hours**: Quick wins, can be done in one session
- **Days**: Medium tasks, 1-5 days
- **Weeks**: Large features, 1-4 weeks
- **Months**: Major initiatives, multi-month projects

### Version Targets

- **v2.1**: Quick wins and high-priority items
- **v2.2**: Quality of life improvements
- **v2.5**: Advanced features
- **v3.0**: Major overhaul or new platform

---

## 🎯 Suggested Next Steps

Based on current state and user needs, recommended order:

1. ✅ **v2.0 Complete** - NLP improvements done!
2. ✅ **v2.1 Complete** - Confidence scores, thresholds, reports, recent projects!
3. ✅ **v2.2 Complete** - Keyword profiles, categorization, multilingual prep!
4. ✅ **v2.3 Complete** - Drag & drop, progress details, CI/CD pipeline! (Phase 1)
5. 🔜 **v2.4** - Increase test coverage to 80%+, additional GUI polish
6. 🔜 **v2.5** - Parallel PDF processing, OCR support for scanned PDFs
7. 🔜 **v3.0** - Multi-lingual GUI integration, database backend, web version

---

**Last Updated**: 2025-11-19
**Maintained By**: Project maintainers
**Contributions**: Community suggestions welcome!

---

*This is a living document. Items may be added, removed, or reprioritized based on user feedback and project goals.*
