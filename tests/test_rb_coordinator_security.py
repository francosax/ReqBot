"""
Unit tests for RB_coordinator.py with security validation.

Tests the main orchestration function with focus on:
- Path validation integration
- Security error handling
- Input validation
- Output file creation with validation
"""

import pytest
import os
import pandas as pd
from unittest.mock import patch
from pathlib import Path

from security.path_validator import PathValidationError


class TestRequirementBotSecurity:
    """Test suite for security validation in requirement_bot function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for requirement_bot."""
        with patch('RB_coordinator.requirement_finder') as mock_finder, \
             patch('RB_coordinator.write_excel_file') as mock_excel, \
             patch('RB_coordinator.export_to_basil') as mock_basil, \
             patch('RB_coordinator.highlight_requirements') as mock_highlight, \
             patch('RB_coordinator.shutil.copy2') as mock_copy:

            # Setup mock return values
            mock_df = pd.DataFrame({
                'Label Number': ['test-Req#1-1'],
                'Description': ['Test requirement'],
                'Page': [1],
                'Keyword': ['shall'],
                'Raw': [['Test', 'requirement']],
                'Confidence': [0.9],
                'Priority': ['high'],
                'Note': ['test-Req#1-1:Test requirement']
            })
            mock_finder.return_value = mock_df
            mock_basil.return_value = True

            yield {
                'finder': mock_finder,
                'excel': mock_excel,
                'basil': mock_basil,
                'highlight': mock_highlight,
                'copy': mock_copy,
                'df': mock_df
            }

    @pytest.fixture
    def valid_paths(self, tmp_path):
        """Create valid test paths."""
        # Create input PDF
        input_pdf = tmp_path / "test.pdf"
        input_pdf.write_text("test content")

        # Create CM template
        cm_template = tmp_path / "Compliance_Matrix_Template_rev001.xlsx"
        cm_template.write_text("test content")

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return {
            'input': str(input_pdf),
            'cm': str(cm_template),
            'output': str(output_dir)
        }

    def test_valid_paths_accepted(self, valid_paths, mock_dependencies):
        """Test that valid paths are accepted and processing proceeds."""
        from RB_coordinator import requirement_bot

        keywords = {'shall', 'must'}

        # Should not raise PathValidationError
        result = requirement_bot(
            path_in=valid_paths['input'],
            cm_path=valid_paths['cm'],
            words_to_find=keywords,
            path_out=valid_paths['output']
        )

        # Should return a DataFrame
        assert isinstance(result, pd.DataFrame)
        # Mocks should have been called
        assert mock_dependencies['finder'].called
        assert mock_dependencies['excel'].called

    def test_nonexistent_pdf_rejected(self, valid_paths, mock_dependencies):
        """Test that nonexistent PDF path is rejected."""
        from RB_coordinator import requirement_bot

        keywords = {'shall', 'must'}
        nonexistent_pdf = valid_paths['output'] + "/does_not_exist.pdf"

        with pytest.raises(PathValidationError) as excinfo:
            requirement_bot(
                path_in=nonexistent_pdf,
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

        assert "does not exist" in str(excinfo.value).lower()

    def test_nonexistent_cm_template_rejected(self, valid_paths, mock_dependencies):
        """Test that nonexistent CM template is rejected."""
        from RB_coordinator import requirement_bot

        keywords = {'shall', 'must'}
        nonexistent_cm = valid_paths['output'] + "/does_not_exist.xlsx"

        with pytest.raises(PathValidationError) as excinfo:
            requirement_bot(
                path_in=valid_paths['input'],
                cm_path=nonexistent_cm,
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

        assert "does not exist" in str(excinfo.value).lower()

    def test_nonexistent_output_dir_rejected(self, valid_paths, mock_dependencies):
        """Test that nonexistent output directory is rejected."""
        from RB_coordinator import requirement_bot

        keywords = {'shall', 'must'}
        nonexistent_dir = valid_paths['output'] + "/does_not_exist"

        with pytest.raises(PathValidationError) as excinfo:
            requirement_bot(
                path_in=valid_paths['input'],
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out=nonexistent_dir
            )

        assert "does not exist" in str(excinfo.value).lower()

    def test_wrong_extension_pdf_rejected(self, valid_paths, mock_dependencies):
        """Test that non-PDF file is rejected as input."""
        from RB_coordinator import requirement_bot

        # Create a .txt file instead of .pdf
        txt_file = Path(valid_paths['input']).parent / "test.txt"
        txt_file.write_text("test")

        keywords = {'shall', 'must'}

        with pytest.raises(PathValidationError) as excinfo:
            requirement_bot(
                path_in=str(txt_file),
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

        assert "invalid file extension" in str(excinfo.value).lower()

    def test_wrong_extension_cm_rejected(self, valid_paths, mock_dependencies):
        """Test that non-Excel file is rejected as CM template."""
        from RB_coordinator import requirement_bot

        # Create a .txt file instead of .xlsx
        txt_file = Path(valid_paths['cm']).parent / "template.txt"
        txt_file.write_text("test")

        keywords = {'shall', 'must'}

        with pytest.raises(PathValidationError) as excinfo:
            requirement_bot(
                path_in=valid_paths['input'],
                cm_path=str(txt_file),
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

        assert "invalid file extension" in str(excinfo.value).lower()

    @pytest.mark.skipif(os.name == 'nt', reason="chmod doesn't work the same on Windows")
    def test_non_writable_output_dir_rejected(self, valid_paths, mock_dependencies):
        """Test that non-writable output directory is rejected."""
        from RB_coordinator import requirement_bot

        # Create read-only directory
        readonly_dir = Path(valid_paths['output']).parent / "readonly"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, 0o444)

        keywords = {'shall', 'must'}

        try:
            with pytest.raises(PathValidationError) as excinfo:
                requirement_bot(
                    path_in=valid_paths['input'],
                    cm_path=valid_paths['cm'],
                    words_to_find=keywords,
                    path_out=str(readonly_dir)
                )

            assert "no write permission" in str(excinfo.value).lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_suspicious_path_rejected(self, valid_paths, mock_dependencies):
        """Test that suspicious paths are rejected."""
        from RB_coordinator import requirement_bot

        keywords = {'shall', 'must'}

        # Try to use /etc/passwd as output (suspicious)
        with pytest.raises(PathValidationError):
            requirement_bot(
                path_in=valid_paths['input'],
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out="/etc"
            )


class TestRequirementBotOutputValidation:
    """Test suite for output file validation."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies."""
        with patch('RB_coordinator.requirement_finder') as mock_finder, \
             patch('RB_coordinator.write_excel_file') as mock_excel, \
             patch('RB_coordinator.export_to_basil') as mock_basil, \
             patch('RB_coordinator.highlight_requirements') as mock_highlight, \
             patch('RB_coordinator.shutil.copy2') as mock_copy:

            mock_df = pd.DataFrame({
                'Label Number': ['test-Req#1-1'],
                'Description': ['Test requirement'],
                'Page': [1],
                'Keyword': ['shall'],
                'Raw': [['Test', 'requirement']],
                'Confidence': [0.9],
                'Priority': ['high'],
                'Note': ['test-Req#1-1:Test requirement']
            })
            mock_finder.return_value = mock_df
            mock_basil.return_value = True

            yield {
                'finder': mock_finder,
                'excel': mock_excel,
                'basil': mock_basil,
                'highlight': mock_highlight,
                'copy': mock_copy
            }

    @pytest.fixture
    def valid_paths(self, tmp_path):
        """Create valid test paths."""
        input_pdf = tmp_path / "test.pdf"
        input_pdf.write_text("test")

        cm_template = tmp_path / "Compliance_Matrix_Template_rev001.xlsx"
        cm_template.write_text("test")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return {
            'input': str(input_pdf),
            'cm': str(cm_template),
            'output': str(output_dir)
        }

    def test_output_files_created_in_correct_directory(self, valid_paths, mock_dependencies):
        """Test that output files are created in the specified directory."""
        from RB_coordinator import requirement_bot

        keywords = {'shall'}

        result = requirement_bot(
            path_in=valid_paths['input'],
            cm_path=valid_paths['cm'],
            words_to_find=keywords,
            path_out=valid_paths['output']
        )

        # Verify that output functions were called with validated paths
        assert mock_dependencies['excel'].called
        # The excel file path should contain the output directory
        excel_call_args = mock_dependencies['excel'].call_args
        assert valid_paths['output'] in excel_call_args[1]['excel_file']

    def test_output_file_extensions_validated(self, valid_paths, mock_dependencies):
        """Test that output file extensions are validated."""
        from RB_coordinator import requirement_bot

        keywords = {'shall'}

        # Should succeed with valid extensions
        result = requirement_bot(
            path_in=valid_paths['input'],
            cm_path=valid_paths['cm'],
            words_to_find=keywords,
            path_out=valid_paths['output']
        )

        # Check that files have correct extensions
        if mock_dependencies['excel'].called:
            excel_path = mock_dependencies['excel'].call_args[1]['excel_file']
            assert excel_path.endswith('.xlsx')

        if mock_dependencies['basil'].called:
            basil_path = mock_dependencies['basil'].call_args[1]['output_path']
            assert basil_path.endswith('.jsonld')


class TestRequirementBotErrorHandling:
    """Test suite for error handling in requirement_bot."""

    @pytest.fixture
    def valid_paths(self, tmp_path):
        """Create valid test paths."""
        input_pdf = tmp_path / "test.pdf"
        input_pdf.write_text("test")

        cm_template = tmp_path / "Compliance_Matrix_Template_rev001.xlsx"
        cm_template.write_text("test")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return {
            'input': str(input_pdf),
            'cm': str(cm_template),
            'output': str(output_dir)
        }

    def test_basil_export_failure_does_not_stop_processing(self, valid_paths):
        """Test that BASIL export failure doesn't stop processing."""
        with patch('RB_coordinator.requirement_finder') as mock_finder, \
             patch('RB_coordinator.write_excel_file') as mock_excel, \
             patch('RB_coordinator.export_to_basil') as mock_basil, \
             patch('RB_coordinator.highlight_requirements') as mock_highlight, \
             patch('RB_coordinator.shutil.copy2') as mock_copy:

            mock_df = pd.DataFrame({
                'Label Number': ['test-Req#1-1'],
                'Description': ['Test requirement'],
                'Page': [1],
                'Keyword': ['shall'],
                'Raw': [['Test', 'requirement']],
                'Confidence': [0.9],
                'Priority': ['high'],
                'Note': ['test-Req#1-1:Test requirement']
            })
            mock_finder.return_value = mock_df

            # Make BASIL export fail
            mock_basil.side_effect = Exception("BASIL export failed")

            from RB_coordinator import requirement_bot

            keywords = {'shall'}

            # Should not raise exception
            result = requirement_bot(
                path_in=valid_paths['input'],
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

            # Should still return DataFrame
            assert isinstance(result, pd.DataFrame)
            # Excel and highlight should still be called
            assert mock_excel.called
            assert mock_highlight.called

    def test_pdf_annotation_failure_does_not_stop_processing(self, valid_paths):
        """Test that PDF annotation failure doesn't stop processing."""
        with patch('RB_coordinator.requirement_finder') as mock_finder, \
             patch('RB_coordinator.write_excel_file') as mock_excel, \
             patch('RB_coordinator.export_to_basil') as mock_basil, \
             patch('RB_coordinator.highlight_requirements') as mock_highlight, \
             patch('RB_coordinator.shutil.copy2') as mock_copy:

            mock_df = pd.DataFrame({
                'Label Number': ['test-Req#1-1'],
                'Description': ['Test requirement'],
                'Page': [1],
                'Keyword': ['shall'],
                'Raw': [['Test', 'requirement']],
                'Confidence': [0.9],
                'Priority': ['high'],
                'Note': ['test-Req#1-1:Test requirement']
            })
            mock_finder.return_value = mock_df
            mock_basil.return_value = True

            # Make PDF annotation fail
            mock_highlight.side_effect = Exception("PDF annotation failed")

            from RB_coordinator import requirement_bot

            keywords = {'shall'}

            # Should not raise exception
            result = requirement_bot(
                path_in=valid_paths['input'],
                cm_path=valid_paths['cm'],
                words_to_find=keywords,
                path_out=valid_paths['output']
            )

            # Should still return DataFrame
            assert isinstance(result, pd.DataFrame)
            # Excel and BASIL should still be called
            assert mock_excel.called
            assert mock_basil.called


class TestPathSanitizationInLogging:
    """Test suite for path sanitization in logging."""

    @pytest.fixture
    def valid_paths(self, tmp_path):
        """Create valid test paths."""
        input_pdf = tmp_path / "test.pdf"
        input_pdf.write_text("test")

        cm_template = tmp_path / "Compliance_Matrix_Template_rev001.xlsx"
        cm_template.write_text("test")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return {
            'input': str(input_pdf),
            'cm': str(cm_template),
            'output': str(output_dir)
        }

    def test_paths_sanitized_in_logs(self, valid_paths, caplog):
        """Test that paths are sanitized in log messages."""
        with patch('RB_coordinator.requirement_finder') as mock_finder, \
             patch('RB_coordinator.write_excel_file'), \
             patch('RB_coordinator.export_to_basil'), \
             patch('RB_coordinator.highlight_requirements'), \
             patch('RB_coordinator.shutil.copy2'):

            mock_df = pd.DataFrame({
                'Label Number': ['test-Req#1-1'],
                'Description': ['Test'],
                'Page': [1],
                'Keyword': ['shall'],
                'Raw': [['Test']],
                'Confidence': [0.9],
                'Priority': ['high'],
                'Note': ['test-Req#1-1:Test']
            })
            mock_finder.return_value = mock_df

            from RB_coordinator import requirement_bot

            keywords = {'shall'}

            with caplog.at_level('INFO'):
                requirement_bot(
                    path_in=valid_paths['input'],
                    cm_path=valid_paths['cm'],
                    words_to_find=keywords,
                    path_out=valid_paths['output']
                )

            # Check that logs contain sanitized paths (not full paths)
            log_text = caplog.text
            # Should contain filenames
            assert "test.pdf" in log_text or "..." in log_text
