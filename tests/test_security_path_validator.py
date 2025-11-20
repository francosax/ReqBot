"""
Unit tests for security.path_validator module.

Tests comprehensive path validation functionality including:
- Path traversal prevention
- Suspicious pattern detection
- Extension validation
- Directory validation
- Output path validation
"""

import pytest
import os
import tempfile
from pathlib import Path

from security.path_validator import (
    PathValidationError,
    validate_safe_path,
    validate_output_path,
    validate_pdf_input,
    validate_excel_template,
    validate_directory,
    sanitize_path_for_logging,
    validate_batch_paths
)


class TestPathValidation:
    """Test suite for basic path validation."""

    def test_valid_file_path(self, tmp_path):
        """Test validation of a valid file path."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")

        validated = validate_safe_path(
            str(test_file),
            must_exist=True,
            path_type='file'
        )

        assert validated == test_file

    def test_valid_directory_path(self, tmp_path):
        """Test validation of a valid directory path."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        validated = validate_safe_path(
            str(test_dir),
            must_exist=True,
            path_type='directory'
        )

        assert validated == test_dir

    def test_nonexistent_path_fails(self, tmp_path):
        """Test that nonexistent paths fail validation."""
        nonexistent = tmp_path / "does_not_exist.pdf"

        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                str(nonexistent),
                must_exist=True
            )

        assert "does not exist" in str(excinfo.value).lower()

    def test_empty_path_fails(self):
        """Test that empty path string fails validation."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path("")

        assert "non-empty string" in str(excinfo.value).lower()

    def test_none_path_fails(self):
        """Test that None path fails validation."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(None)

        assert "non-empty string" in str(excinfo.value).lower()


class TestPathTraversalPrevention:
    """Test suite for path traversal attack prevention."""

    def test_path_traversal_with_base_dir(self, tmp_path):
        """Test that path traversal outside base directory is blocked."""
        base_dir = tmp_path / "safe_zone"
        base_dir.mkdir()

        # Try to access parent directory
        traversal_path = str(base_dir / ".." / ".." / "etc" / "passwd")

        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                traversal_path,
                base_dir=str(base_dir),
                must_exist=False
            )

        assert "outside allowed directory" in str(excinfo.value).lower()

    def test_path_within_base_dir_succeeds(self, tmp_path):
        """Test that paths within base directory are allowed."""
        base_dir = tmp_path / "safe_zone"
        base_dir.mkdir()

        safe_file = base_dir / "document.pdf"
        safe_file.write_text("test")

        validated = validate_safe_path(
            str(safe_file),
            base_dir=str(base_dir),
            must_exist=True
        )

        assert validated == safe_file


class TestSuspiciousPatternDetection:
    """Test suite for suspicious path pattern detection."""

    @pytest.mark.parametrize("suspicious_path", [
        "/etc/passwd",
        "/etc/shadow",
        "C:\\Windows\\System32\\config.sys",
        "/home/user/.ssh/id_rsa",
        "~/.ssh/authorized_keys",
    ])
    def test_suspicious_patterns_blocked(self, suspicious_path):
        """Test that suspicious system paths are blocked."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                suspicious_path,
                must_exist=False
            )

        assert "suspicious pattern" in str(excinfo.value).lower()

    def test_normal_path_with_system_string_allowed(self, tmp_path):
        """Test that normal paths containing 'system' are allowed."""
        # This should be allowed since it's just a directory name
        normal_dir = tmp_path / "my_system_docs"
        normal_dir.mkdir()

        validated = validate_safe_path(
            str(normal_dir),
            must_exist=True,
            path_type='directory'
        )

        assert validated == normal_dir


class TestExtensionValidation:
    """Test suite for file extension validation."""

    def test_allowed_extension_succeeds(self, tmp_path):
        """Test that files with allowed extensions pass validation."""
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_text("test")

        validated = validate_safe_path(
            str(pdf_file),
            allowed_extensions=['.pdf', '.PDF'],
            must_exist=True
        )

        assert validated == pdf_file

    def test_disallowed_extension_fails(self, tmp_path):
        """Test that files with disallowed extensions fail validation."""
        exe_file = tmp_path / "malware.exe"
        exe_file.write_text("test")

        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                str(exe_file),
                allowed_extensions=['.pdf', '.xlsx'],
                must_exist=True
            )

        assert "invalid file extension" in str(excinfo.value).lower()

    def test_case_insensitive_extension(self, tmp_path):
        """Test that extension validation is case-insensitive."""
        pdf_file = tmp_path / "document.PDF"  # Uppercase
        pdf_file.write_text("test")

        validated = validate_safe_path(
            str(pdf_file),
            allowed_extensions=['.pdf'],  # Lowercase
            must_exist=True
        )

        assert validated == pdf_file


class TestOutputPathValidation:
    """Test suite for output path validation."""

    def test_valid_output_path(self, tmp_path):
        """Test validation of valid output path."""
        output_file = tmp_path / "output.xlsx"

        validated = validate_output_path(
            str(output_file),
            allowed_extensions=['.xlsx']
        )

        assert validated == output_file

    def test_nonexistent_output_directory_fails(self, tmp_path):
        """Test that output path with nonexistent directory fails."""
        nonexistent_dir = tmp_path / "does_not_exist"
        output_file = nonexistent_dir / "output.xlsx"

        with pytest.raises(PathValidationError) as excinfo:
            validate_output_path(str(output_file))

        assert "directory does not exist" in str(excinfo.value).lower()

    def test_non_writable_directory_fails(self, tmp_path):
        """Test that non-writable directory fails validation."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        # Make directory read-only
        os.chmod(readonly_dir, 0o444)

        output_file = readonly_dir / "output.xlsx"

        try:
            with pytest.raises(PathValidationError) as excinfo:
                validate_output_path(
                    str(output_file),
                    check_writable=True
                )

            assert "no write permission" in str(excinfo.value).lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_suspicious_output_path_blocked(self):
        """Test that suspicious output paths are blocked."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_output_path(
                "/etc/passwd",
                check_writable=False
            )

        assert "system directory" in str(excinfo.value).lower()


class TestConvenienceFunctions:
    """Test suite for convenience validation functions."""

    def test_validate_pdf_input(self, tmp_path):
        """Test PDF-specific validation function."""
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_text("test")

        validated = validate_pdf_input(str(pdf_file))

        assert validated == pdf_file

    def test_validate_pdf_wrong_extension_fails(self, tmp_path):
        """Test that non-PDF files fail PDF validation."""
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("test")

        with pytest.raises(PathValidationError) as excinfo:
            validate_pdf_input(str(txt_file))

        assert "invalid file extension" in str(excinfo.value).lower()

    def test_validate_excel_template(self, tmp_path):
        """Test Excel-specific validation function."""
        xlsx_file = tmp_path / "template.xlsx"
        xlsx_file.write_text("test")

        validated = validate_excel_template(str(xlsx_file))

        assert validated == xlsx_file

    def test_validate_directory(self, tmp_path):
        """Test directory-specific validation function."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        validated = validate_directory(str(test_dir))

        assert validated == test_dir

    def test_validate_directory_with_file_fails(self, tmp_path):
        """Test that file path fails directory validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(PathValidationError) as excinfo:
            validate_directory(str(test_file))

        assert "expected a directory" in str(excinfo.value).lower()


class TestBatchValidation:
    """Test suite for batch path validation."""

    def test_validate_multiple_valid_paths(self, tmp_path):
        """Test validation of multiple valid paths."""
        files = []
        for i in range(3):
            f = tmp_path / f"test{i}.pdf"
            f.write_text("test")
            files.append(str(f))

        validated = validate_batch_paths(
            files,
            allowed_extensions=['.pdf']
        )

        assert len(validated) == 3
        assert all(isinstance(p, Path) for p in validated)

    def test_batch_validation_fails_on_invalid(self, tmp_path):
        """Test that batch validation fails if any path is invalid."""
        valid_file = tmp_path / "valid.pdf"
        valid_file.write_text("test")

        invalid_file = tmp_path / "does_not_exist.pdf"

        with pytest.raises(PathValidationError) as excinfo:
            validate_batch_paths(
                [str(valid_file), str(invalid_file)],
                allowed_extensions=['.pdf']
            )

        assert "validation failed" in str(excinfo.value).lower()


class TestPathSanitization:
    """Test suite for path sanitization for logging."""

    def test_sanitize_absolute_path(self):
        """Test sanitization of absolute path."""
        path = "/home/username/secret/document.pdf"
        sanitized = sanitize_path_for_logging(path)

        # Should not contain username
        assert "username" not in sanitized
        # Should contain filename
        assert "document.pdf" in sanitized

    def test_sanitize_relative_path(self):
        """Test sanitization of relative path."""
        path = "documents/report.xlsx"
        sanitized = sanitize_path_for_logging(path)

        # Should just return filename for relative paths
        assert sanitized == "report.xlsx"

    def test_sanitize_windows_path(self):
        """Test sanitization of Windows path."""
        path = "C:\\Users\\JohnDoe\\Documents\\secret.pdf"
        sanitized = sanitize_path_for_logging(path)

        # Should not contain username
        assert "JohnDoe" not in sanitized
        # Should contain filename
        assert "secret.pdf" in sanitized

    def test_sanitize_invalid_path(self):
        """Test sanitization handles invalid paths gracefully."""
        sanitized = sanitize_path_for_logging(None)

        assert sanitized == "unknown"


class TestPathTypeValidation:
    """Test suite for path type validation."""

    def test_file_type_validation_with_file(self, tmp_path):
        """Test that file type validation succeeds with file."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        validated = validate_safe_path(
            str(test_file),
            path_type='file'
        )

        assert validated == test_file

    def test_file_type_validation_with_directory_fails(self, tmp_path):
        """Test that file type validation fails with directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                str(test_dir),
                path_type='file'
            )

        assert "expected a file" in str(excinfo.value).lower()

    def test_directory_type_validation_with_directory(self, tmp_path):
        """Test that directory type validation succeeds with directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        validated = validate_safe_path(
            str(test_dir),
            path_type='directory'
        )

        assert validated == test_dir

    def test_directory_type_validation_with_file_fails(self, tmp_path):
        """Test that directory type validation fails with file."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        with pytest.raises(PathValidationError) as excinfo:
            validate_safe_path(
                str(test_file),
                path_type='directory'
            )

        assert "expected a directory" in str(excinfo.value).lower()
