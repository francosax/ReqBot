"""
Processing Report Generator for ReqBot

Generates comprehensive HTML and PDF reports after processing PDFs,
including statistics, warnings, errors, and quality metrics.

Features:
- HTML report generation with charts and tables
- PDF export capability
- Statistics: total requirements, average confidence, processing time
- Warnings and errors summary
- Per-file breakdown
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ProcessingReport:
    """
    Manages the generation of processing reports for ReqBot.
    """

    def __init__(self):
        """Initialize the ProcessingReport generator."""
        self.files_processed: List[Dict] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.keywords: List[str] = []
        self.confidence_threshold: float = 0.5

    def set_metadata(self, keywords: List[str], confidence_threshold: float):
        """
        Set processing metadata.

        Args:
            keywords: List of keywords used for extraction
            confidence_threshold: Minimum confidence threshold
        """
        self.keywords = keywords
        self.confidence_threshold = confidence_threshold

    def start_processing(self):
        """Mark the start of processing."""
        self.start_time = datetime.now()

    def end_processing(self):
        """Mark the end of processing."""
        self.end_time = datetime.now()

    def add_file_result(self, filename: str, req_count: int, avg_confidence: float,
                        execution_time_seconds: float, file_warnings: List[str] = None):
        """
        Add results from processing a single file.

        Args:
            filename: Name of the processed PDF file
            req_count: Number of requirements extracted
            avg_confidence: Average confidence score (0.0-1.0)
            execution_time_seconds: Time taken to process the file
            file_warnings: List of warnings for this file
        """
        self.files_processed.append({
            'filename': filename,
            'requirements': req_count,
            'avg_confidence': avg_confidence,
            'execution_time': execution_time_seconds,
            'warnings': file_warnings or []
        })

    def add_warning(self, message: str):
        """Add a warning message to the report."""
        self.warnings.append(message)

    def add_error(self, message: str):
        """Add an error message to the report."""
        self.errors.append(message)

    def get_statistics(self) -> Dict:
        """
        Calculate overall statistics.

        Returns:
            Dictionary containing statistics
        """
        if not self.files_processed:
            return {
                'total_files': 0,
                'total_requirements': 0,
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'total_execution_time': 0.0,
                'avg_req_per_file': 0.0,
                'estimated_manual_time_hrs': 0.0
            }

        total_reqs = sum(f['requirements'] for f in self.files_processed)
        total_time = sum(f['execution_time'] for f in self.files_processed)

        # Calculate average confidence (weighted by number of requirements)
        total_weighted_conf = sum(f['avg_confidence'] * f['requirements']
                                  for f in self.files_processed if f['requirements'] > 0)
        avg_confidence = total_weighted_conf / total_reqs if total_reqs > 0 else 0.0

        confidences = [f['avg_confidence'] for f in self.files_processed if f['requirements'] > 0]

        # Calculate estimated manual analysis time (5 minutes per requirement)
        estimated_manual_time = round(total_reqs * (5 / 60), 2)  # Convert to hours

        return {
            'total_files': len(self.files_processed),
            'total_requirements': total_reqs,
            'avg_confidence': round(avg_confidence, 3),
            'min_confidence': round(min(confidences), 3) if confidences else 0.0,
            'max_confidence': round(max(confidences), 3) if confidences else 0.0,
            'total_execution_time': round(total_time, 2),
            'avg_req_per_file': round(total_reqs / len(self.files_processed), 1),
            'estimated_manual_time_hrs': estimated_manual_time
        }

    def generate_html_report(self, output_path: str) -> bool:
        """
        Generate an HTML report and save to file.

        Args:
            output_path: Path where HTML report will be saved

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            stats = self.get_statistics()
            processing_time = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0.0

            html_content = self._generate_html_content(stats, processing_time)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML report generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return False

    def _generate_html_content(self, stats: Dict, processing_time: float) -> str:
        """
        Generate HTML content for the report.

        Args:
            stats: Statistics dictionary
            processing_time: Total processing time in seconds

        Returns:
            HTML content as string
        """
        # Confidence score color coding
        avg_conf = stats['avg_confidence']
        if avg_conf >= 0.8:
            conf_color = '#28a745'  # Green
            conf_label = 'Excellent'
        elif avg_conf >= 0.6:
            conf_color = '#ffc107'  # Yellow
            conf_label = 'Good'
        else:
            conf_color = '#dc3545'  # Red
            conf_label = 'Needs Review'

        # Generate file table rows
        file_rows = ""
        for f in self.files_processed:
            conf = f['avg_confidence']
            conf_class = 'high' if conf >= 0.8 else ('medium' if conf >= 0.6 else 'low')

            warning_count = len(f['warnings'])
            warning_badge = f'<span class="badge warning">{warning_count}</span>' if warning_count > 0 else '-'

            file_rows += f"""
                <tr>
                    <td>{f['filename']}</td>
                    <td>{f['requirements']}</td>
                    <td class="conf-{conf_class}">{conf:.3f}</td>
                    <td>{f['execution_time']:.2f}s</td>
                    <td>{warning_badge}</td>
                </tr>
            """

        # Generate warnings section
        warnings_section = ""
        if self.warnings:
            warnings_list = "".join([f"<li>{w}</li>" for w in self.warnings])
            warnings_section = f"""
                <div class="section warnings-section">
                    <h2>⚠️ Warnings ({len(self.warnings)})</h2>
                    <ul class="warning-list">
                        {warnings_list}
                    </ul>
                </div>
            """

        # Generate errors section
        errors_section = ""
        if self.errors:
            errors_list = "".join([f"<li>{e}</li>" for e in self.errors])
            errors_section = f"""
                <div class="section errors-section">
                    <h2>❌ Errors ({len(self.errors)})</h2>
                    <ul class="error-list">
                        {errors_list}
                    </ul>
                </div>
            """

        # HTML template
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReqBot Processing Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}

        .section:last-child {{
            border-bottom: none;
        }}

        h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .stat-card.primary {{
            border-left-color: #667eea;
        }}

        .stat-card.success {{
            border-left-color: #28a745;
        }}

        .stat-card.warning {{
            border-left-color: #ffc107;
        }}

        .stat-card.info {{
            border-left-color: #17a2b8;
        }}

        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .confidence-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
            background-color: {conf_color};
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .conf-high {{
            color: #28a745;
            font-weight: bold;
        }}

        .conf-medium {{
            color: #ffc107;
            font-weight: bold;
        }}

        .conf-low {{
            color: #dc3545;
            font-weight: bold;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge.warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .warning-list, .error-list {{
            list-style: none;
            padding: 0;
        }}

        .warning-list li, .error-list li {{
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}

        .error-list li {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}

        .warnings-section h2, .errors-section h2 {{
            color: #856404;
        }}

        .errors-section h2 {{
            color: #721c24;
        }}

        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}

        .metadata {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}

        .metadata-item {{
            margin-bottom: 8px;
        }}

        .metadata-label {{
            font-weight: 600;
            color: #004085;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ReqBot Processing Report</h1>
            <div class="subtitle">Requirement Extraction Analysis</div>
            <div class="subtitle">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="section">
            <h2>📈 Overall Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total Files Processed</div>
                    <div class="stat-value">{stats['total_files']}</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Total Requirements</div>
                    <div class="stat-value">{stats['total_requirements']}</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Avg Requirements/File</div>
                    <div class="stat-value">{stats['avg_req_per_file']}</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Processing Time</div>
                    <div class="stat-value">{processing_time:.1f}s</div>
                </div>
                <div class="stat-card" style="background: white; border-left-color: #764ba2;">
                    <div class="stat-label">Estimated Time for Manual Analysis</div>
                    <div class="stat-value">{stats['estimated_manual_time_hrs']:.2f} hrs</div>
                    <div style="margin-top: 5px; font-size: 0.8em; color: #6c757d;">~{int(stats['estimated_manual_time_hrs'] * 60)} minutes</div>
                </div>
            </div>

            <div class="metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Keywords Used:</span> {', '.join(self.keywords)}
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Confidence Threshold:</span> {self.confidence_threshold:.2f}
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🎯 Quality Metrics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Average Confidence</div>
                    <div class="stat-value">{stats['avg_confidence']:.3f}</div>
                    <div style="margin-top: 10px;">
                        <span class="confidence-badge">{conf_label}</span>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Min Confidence</div>
                    <div class="stat-value">{stats['min_confidence']:.3f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Max Confidence</div>
                    <div class="stat-value">{stats['max_confidence']:.3f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Issues</div>
                    <div class="stat-value">{len(self.warnings) + len(self.errors)}</div>
                    <div style="margin-top: 10px; font-size: 0.85em; color: #6c757d;">
                        {len(self.warnings)} warnings, {len(self.errors)} errors
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📄 File Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Requirements</th>
                        <th>Avg Confidence</th>
                        <th>Execution Time</th>
                        <th>Warnings</th>
                    </tr>
                </thead>
                <tbody>
                    {file_rows}
                </tbody>
            </table>
        </div>

        {warnings_section}
        {errors_section}

        <div class="footer">
            Generated by ReqBot v2.1 • Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
        """

        return html


def create_processing_report() -> ProcessingReport:
    """
    Factory function to create a new ProcessingReport instance.

    Returns:
        ProcessingReport instance
    """
    return ProcessingReport()
