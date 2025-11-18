"""
Tests for report_generator.py module.

Tests the HTML report generation functionality including
statistics calculation, file tracking, warnings, and errors.
"""

import pytest
import os
import tempfile
from datetime import datetime
from report_generator import ProcessingReport, create_processing_report


class TestProcessingReport:
    """Test suite for ProcessingReport class."""

    def test_create_report_instance(self):
        """Test creating a ProcessingReport instance."""
        report = create_processing_report()
        assert isinstance(report, ProcessingReport)
        assert report.files_processed == []
        assert report.warnings == []
        assert report.errors == []
        assert report.start_time is None
        assert report.end_time is None

    def test_set_metadata(self):
        """Test setting report metadata."""
        report = create_processing_report()
        keywords = ['shall', 'must', 'should']
        threshold = 0.7

        report.set_metadata(keywords, threshold)

        assert report.keywords == keywords
        assert report.confidence_threshold == threshold

    def test_start_end_processing(self):
        """Test marking start and end of processing."""
        report = create_processing_report()

        report.start_processing()
        assert report.start_time is not None
        assert isinstance(report.start_time, datetime)

        report.end_processing()
        assert report.end_time is not None
        assert isinstance(report.end_time, datetime)
        assert report.end_time >= report.start_time

    def test_add_file_result(self):
        """Test adding file processing results."""
        report = create_processing_report()

        report.add_file_result(
            filename="test.pdf",
            req_count=10,
            avg_confidence=0.85,
            execution_time_seconds=2.5,
            file_warnings=["Warning 1"]
        )

        assert len(report.files_processed) == 1
        assert report.files_processed[0]['filename'] == "test.pdf"
        assert report.files_processed[0]['requirements'] == 10
        assert report.files_processed[0]['avg_confidence'] == 0.85
        assert report.files_processed[0]['execution_time'] == 2.5
        assert report.files_processed[0]['warnings'] == ["Warning 1"]

    def test_add_multiple_files(self):
        """Test adding results from multiple files."""
        report = create_processing_report()

        for i in range(5):
            report.add_file_result(
                filename=f"file{i}.pdf",
                req_count=i * 2,
                avg_confidence=0.7 + (i * 0.05),
                execution_time_seconds=1.0 + i
            )

        assert len(report.files_processed) == 5
        assert report.files_processed[0]['requirements'] == 0
        assert report.files_processed[4]['requirements'] == 8

    def test_add_warning(self):
        """Test adding warnings to report."""
        report = create_processing_report()

        report.add_warning("Warning message 1")
        report.add_warning("Warning message 2")

        assert len(report.warnings) == 2
        assert "Warning message 1" in report.warnings
        assert "Warning message 2" in report.warnings

    def test_add_error(self):
        """Test adding errors to report."""
        report = create_processing_report()

        report.add_error("Error message 1")
        report.add_error("Error message 2")

        assert len(report.errors) == 2
        assert "Error message 1" in report.errors
        assert "Error message 2" in report.errors

    def test_get_statistics_empty(self):
        """Test getting statistics with no files processed."""
        report = create_processing_report()
        stats = report.get_statistics()

        assert stats['total_files'] == 0
        assert stats['total_requirements'] == 0
        assert stats['avg_confidence'] == 0.0
        assert stats['min_confidence'] == 0.0
        assert stats['max_confidence'] == 0.0

    def test_get_statistics_single_file(self):
        """Test statistics calculation with single file."""
        report = create_processing_report()

        report.add_file_result(
            filename="test.pdf",
            req_count=10,
            avg_confidence=0.85,
            execution_time_seconds=2.5
        )

        stats = report.get_statistics()

        assert stats['total_files'] == 1
        assert stats['total_requirements'] == 10
        assert stats['avg_confidence'] == 0.85
        assert stats['min_confidence'] == 0.85
        assert stats['max_confidence'] == 0.85
        assert stats['avg_req_per_file'] == 10.0

    def test_get_statistics_multiple_files(self):
        """Test statistics calculation with multiple files."""
        report = create_processing_report()

        # Add files with different confidences
        report.add_file_result("file1.pdf", 10, 0.9, 1.0)
        report.add_file_result("file2.pdf", 20, 0.7, 2.0)
        report.add_file_result("file3.pdf", 15, 0.8, 1.5)

        stats = report.get_statistics()

        assert stats['total_files'] == 3
        assert stats['total_requirements'] == 45
        assert stats['min_confidence'] == 0.7
        assert stats['max_confidence'] == 0.9
        # Weighted average: (10*0.9 + 20*0.7 + 15*0.8) / 45 = 0.778
        assert abs(stats['avg_confidence'] - 0.778) < 0.001
        assert stats['avg_req_per_file'] == 15.0

    def test_generate_html_report(self, tmp_path):
        """Test HTML report generation."""
        report = create_processing_report()
        report.set_metadata(['shall', 'must'], 0.5)
        report.start_processing()

        # Add some data
        report.add_file_result("test1.pdf", 10, 0.85, 2.5)
        report.add_file_result("test2.pdf", 5, 0.65, 1.2)
        report.add_warning("Test warning")
        report.add_error("Test error")

        report.end_processing()

        # Generate report
        output_path = tmp_path / "test_report.html"
        success = report.generate_html_report(str(output_path))

        assert success
        assert output_path.exists()

        # Verify HTML content
        content = output_path.read_text(encoding='utf-8')
        assert "ReqBot Processing Report" in content
        assert "test1.pdf" in content
        assert "test2.pdf" in content
        assert "Test warning" in content
        assert "Test error" in content
        assert "shall" in content
        assert "must" in content

    def test_html_report_structure(self, tmp_path):
        """Test that generated HTML has proper structure."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.6)
        report.start_processing()
        report.add_file_result("sample.pdf", 8, 0.75, 1.5)
        report.end_processing()

        output_path = tmp_path / "structure_test.html"
        report.generate_html_report(str(output_path))

        content = output_path.read_text(encoding='utf-8')

        # Check for key HTML sections
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "<style>" in content
        assert "Overall Statistics" in content
        assert "Quality Metrics" in content
        assert "File Details" in content

    def test_html_report_confidence_colors(self, tmp_path):
        """Test that confidence scores get proper color coding."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.5)
        report.start_processing()

        # High confidence (green)
        report.add_file_result("high.pdf", 10, 0.95, 1.0)
        # Medium confidence (yellow)
        report.add_file_result("medium.pdf", 10, 0.7, 1.0)
        # Low confidence (red)
        report.add_file_result("low.pdf", 10, 0.4, 1.0)

        report.end_processing()

        output_path = tmp_path / "colors_test.html"
        report.generate_html_report(str(output_path))

        content = output_path.read_text(encoding='utf-8')

        # Check for confidence color classes
        assert "conf-high" in content or "#28a745" in content  # Green
        assert "conf-medium" in content or "#ffc107" in content  # Yellow
        assert "conf-low" in content or "#dc3545" in content  # Red

    def test_html_report_warnings_section(self, tmp_path):
        """Test that warnings section appears when warnings exist."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.5)
        report.start_processing()
        report.add_file_result("test.pdf", 5, 0.8, 1.0)

        # Add warnings
        report.add_warning("Warning 1")
        report.add_warning("Warning 2")

        report.end_processing()

        output_path = tmp_path / "warnings_test.html"
        report.generate_html_report(str(output_path))

        content = output_path.read_text(encoding='utf-8')

        assert "Warnings" in content
        assert "Warning 1" in content
        assert "Warning 2" in content

    def test_html_report_errors_section(self, tmp_path):
        """Test that errors section appears when errors exist."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.5)
        report.start_processing()
        report.add_file_result("test.pdf", 5, 0.8, 1.0)

        # Add errors
        report.add_error("Error 1")
        report.add_error("Error 2")

        report.end_processing()

        output_path = tmp_path / "errors_test.html"
        report.generate_html_report(str(output_path))

        content = output_path.read_text(encoding='utf-8')

        assert "Errors" in content
        assert "Error 1" in content
        assert "Error 2" in content

    def test_html_report_no_warnings_no_errors(self, tmp_path):
        """Test that warnings/errors sections don't appear when empty."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.5)
        report.start_processing()
        report.add_file_result("test.pdf", 5, 0.8, 1.0)
        report.end_processing()

        output_path = tmp_path / "clean_test.html"
        report.generate_html_report(str(output_path))

        content = output_path.read_text(encoding='utf-8')

        # Should have the structure but not the warning/error sections
        # Check that there are no warning or error list items
        assert content.count("warning-list") == 0
        assert content.count("error-list") == 0

    def test_statistics_weighted_average(self):
        """Test that confidence average is correctly weighted by requirement count."""
        report = create_processing_report()

        # 1 req at 1.0 confidence, 9 reqs at 0.0 confidence
        # Average should be (1*1.0 + 9*0.0) / 10 = 0.1
        report.add_file_result("file1.pdf", 1, 1.0, 1.0)
        report.add_file_result("file2.pdf", 9, 0.0, 1.0)

        stats = report.get_statistics()

        assert stats['total_requirements'] == 10
        assert abs(stats['avg_confidence'] - 0.1) < 0.001

    def test_file_result_with_no_warnings(self):
        """Test adding file result without warnings."""
        report = create_processing_report()

        report.add_file_result(
            filename="test.pdf",
            req_count=5,
            avg_confidence=0.8,
            execution_time_seconds=1.0
            # No file_warnings parameter
        )

        assert len(report.files_processed) == 1
        assert report.files_processed[0]['warnings'] == []

    def test_report_generation_with_zero_requirements(self, tmp_path):
        """Test report generation when no requirements were found."""
        report = create_processing_report()
        report.set_metadata(['shall'], 0.5)
        report.start_processing()

        # Add file with 0 requirements
        report.add_file_result("empty.pdf", 0, 0.0, 0.5)

        report.end_processing()

        output_path = tmp_path / "zero_reqs.html"
        success = report.generate_html_report(str(output_path))

        assert success
        assert output_path.exists()

        content = output_path.read_text(encoding='utf-8')
        assert "empty.pdf" in content


class TestFactoryFunction:
    """Test the factory function for creating reports."""

    def test_create_processing_report_returns_instance(self):
        """Test that factory function returns proper instance."""
        report = create_processing_report()
        assert isinstance(report, ProcessingReport)

    def test_create_multiple_independent_reports(self):
        """Test that factory creates independent instances."""
        report1 = create_processing_report()
        report2 = create_processing_report()

        report1.add_warning("Warning 1")
        report2.add_error("Error 2")

        assert len(report1.warnings) == 1
        assert len(report1.errors) == 0
        assert len(report2.warnings) == 0
        assert len(report2.errors) == 1


# Integration test
class TestReportIntegration:
    """Integration tests for report generation workflow."""

    def test_complete_workflow(self, tmp_path):
        """Test a complete reporting workflow from start to finish."""
        report = create_processing_report()

        # Setup
        keywords = ['shall', 'must', 'should']
        threshold = 0.65
        report.set_metadata(keywords, threshold)

        # Start processing
        report.start_processing()

        # Process multiple files
        report.add_file_result("spec1.pdf", 15, 0.92, 3.2, ["Low page count"])
        report.add_file_result("spec2.pdf", 8, 0.58, 1.5, ["Low confidence"])
        report.add_file_result("spec3.pdf", 22, 0.81, 5.1)

        # Add some warnings and errors
        report.add_warning("File spec4.pdf not found")
        report.add_error("Failed to load template")

        # End processing
        report.end_processing()

        # Generate report
        output_path = tmp_path / "integration_report.html"
        success = report.generate_html_report(str(output_path))

        # Verify
        assert success
        assert output_path.exists()

        stats = report.get_statistics()
        assert stats['total_files'] == 3
        assert stats['total_requirements'] == 45

        content = output_path.read_text(encoding='utf-8')
        assert "spec1.pdf" in content
        assert "spec2.pdf" in content
        assert "spec3.pdf" in content
        assert "File spec4.pdf not found" in content
        assert "Failed to load template" in content
        assert all(kw in content for kw in keywords)
