"""
Advanced reporting engine for Reality Checker.

This module provides comprehensive reporting capabilities including:
- Multiple export formats (JSON, CSV, PDF, Excel)
- Customizable report templates
- Scheduled report generation
- Interactive data visualization
- Report sharing and distribution
"""

import json
import csv
import io
import logging
import os
import tempfile
from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import xlsxwriter

from app.utils.logging import get_logger
from app.models.data_models import ReportData, ReportParameters

logger = get_logger(__name__)


class ReportFormat:
    """Report export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XLSX = "xlsx"


@dataclass
class ReportTemplate:
    """Template for report generation."""
    id: str
    name: str
    description: str
    sections: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    creator: str = "system"


class ReportingEngine:
    """Engine for generating and exporting reports."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the reporting engine.
        
        Args:
            output_dir: Directory for report output files
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        self.templates: Dict[str, ReportTemplate] = {}
        self._register_default_templates()
        logger.info("Reporting Engine initialized")
    
    def _register_default_templates(self) -> None:
        """Register default report templates."""
        usage_summary_template = ReportTemplate(
            id="usage_summary",
            name="Usage Summary Report",
            description="Summary of system usage statistics",
            sections=[
                {
                    "title": "Overview",
                    "type": "summary",
                    "metrics": ["total_messages", "unique_users", "success_rate"]
                },
                {
                    "title": "Message Breakdown",
                    "type": "pie_chart",
                    "data_key": "message_breakdown"
                },
                {
                    "title": "Performance Metrics",
                    "type": "metrics_table",
                    "data_key": "performance"
                },
                {
                    "title": "Classification Distribution",
                    "type": "bar_chart",
                    "data_key": "classifications"
                }
            ]
        )
        
        classification_analysis_template = ReportTemplate(
            id="classification_analysis",
            name="Classification Analysis Report",
            description="Detailed analysis of job ad classifications",
            sections=[
                {
                    "title": "Classification Summary",
                    "type": "summary",
                    "metrics": ["total_analyses"]
                },
                {
                    "title": "Classification Distribution",
                    "type": "pie_chart",
                    "data_key": "classification_percentages"
                },
                {
                    "title": "Classification Trends",
                    "type": "line_chart",
                    "data_key": "trends.daily_counts",
                    "x_key": "date",
                    "y_key": "count"
                },
                {
                    "title": "Classification Details",
                    "type": "table",
                    "data_key": "classification_counts"
                }
            ]
        )
        
        user_behavior_template = ReportTemplate(
            id="user_behavior",
            name="User Behavior Report",
            description="Analysis of user engagement and behavior patterns",
            sections=[
                {
                    "title": "User Metrics",
                    "type": "summary",
                    "metrics": ["unique_users", "returning_users", "retention_rate"]
                },
                {
                    "title": "Usage by Hour",
                    "type": "bar_chart",
                    "data_key": "usage_patterns.hourly_distribution"
                },
                {
                    "title": "Usage by Day",
                    "type": "bar_chart",
                    "data_key": "usage_patterns.daily_distribution"
                },
                {
                    "title": "User Engagement",
                    "type": "metrics_table",
                    "data_key": "engagement"
                }
            ]
        )
        
        performance_metrics_template = ReportTemplate(
            id="performance_metrics",
            name="Performance Metrics Report",
            description="System performance and reliability metrics",
            sections=[
                {
                    "title": "Response Time Metrics",
                    "type": "metrics_table",
                    "data_key": "response_times"
                },
                {
                    "title": "Success Metrics",
                    "type": "metrics_table",
                    "data_key": "success_metrics"
                },
                {
                    "title": "Response Time Distribution",
                    "type": "histogram",
                    "data_key": "response_time_distribution"
                },
                {
                    "title": "Error Rate Trend",
                    "type": "line_chart",
                    "data_key": "error_rate_trend",
                    "x_key": "date",
                    "y_key": "rate"
                }
            ]
        )
        
        # Register templates
        self.templates[usage_summary_template.id] = usage_summary_template
        self.templates[classification_analysis_template.id] = classification_analysis_template
        self.templates[user_behavior_template.id] = user_behavior_template
        self.templates[performance_metrics_template.id] = performance_metrics_template
    
    async def export_report(self, report: ReportData) -> Dict[str, Any]:
        """
        Export a report to the specified format.
        
        Args:
            report: Report data to export
            
        Returns:
            Dictionary with export details
        """
        try:
            export_format = report.export_format.lower()
            
            if export_format == ReportFormat.JSON:
                result = await self._export_to_json(report)
            elif export_format == ReportFormat.CSV:
                result = await self._export_to_csv(report)
            elif export_format == ReportFormat.PDF:
                result = await self._export_to_pdf(report)
            elif export_format == ReportFormat.XLSX:
                result = await self._export_to_xlsx(report)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Update report with export details
            report.download_url = result.get("file_path")
            report.file_size = result.get("file_size")
            
            logger.info(f"Report exported successfully: {report.report_type} to {export_format}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            raise
    
    async def _export_to_json(self, report: ReportData) -> Dict[str, Any]:
        """Export report to JSON format."""
        try:
            # Create report dictionary
            report_dict = {
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "period": report.period,
                "data": report.data
            }
            
            # Write to file
            filename = f"{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join(self.output_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "format": ReportFormat.JSON,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": "application/json"
            }
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    async def _export_to_csv(self, report: ReportData) -> Dict[str, Any]:
        """Export report to CSV format."""
        try:
            # Convert report data to DataFrame
            df = self._convert_to_dataframe(report.data)
            
            # Write to file
            filename = f"{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = os.path.join(self.output_dir, filename)
            
            df.to_csv(file_path, index=False)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "format": ReportFormat.CSV,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": "text/csv"
            }
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    async def _export_to_pdf(self, report: ReportData) -> Dict[str, Any]:
        """Export report to PDF format."""
        try:
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            
            # Set up fonts
            pdf.set_font("Arial", "B", 16)
            
            # Title
            title = f"{report.report_type.replace('_', ' ').title()} Report"
            pdf.cell(0, 10, title, 0, 1, "C")
            
            # Period
            pdf.set_font("Arial", "I", 12)
            pdf.cell(0, 10, f"Period: {report.period}", 0, 1, "C")
            pdf.cell(0, 10, f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
            
            # Add line
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            # Add report data
            pdf.set_font("Arial", "", 12)
            
            # Get template for this report type
            template = self.templates.get(report.report_type)
            
            if template:
                # Generate PDF based on template sections
                for section in template.sections:
                    self._add_pdf_section(pdf, section, report.data)
            else:
                # Generic PDF generation
                self._add_generic_pdf_content(pdf, report.data)
            
            # Write to file
            filename = f"{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(self.output_dir, filename)
            
            pdf.output(file_path)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "format": ReportFormat.PDF,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": "application/pdf"
            }
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise
    
    def _add_pdf_section(self, pdf: FPDF, section: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Add a section to the PDF based on template."""
        # Add section title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, section["title"], 0, 1)
        pdf.set_font("Arial", "", 12)
        
        section_type = section["type"]
        
        if section_type == "summary":
            # Summary section with key metrics
            metrics = section.get("metrics", [])
            for metric in metrics:
                if metric in data:
                    pdf.cell(0, 8, f"{metric.replace('_', ' ').title()}: {data[metric]}", 0, 1)
                elif "." in metric:
                    # Handle nested metrics
                    keys = metric.split(".")
                    value = data
                    for key in keys:
                        if key in value:
                            value = value[key]
                        else:
                            value = "N/A"
                            break
                    pdf.cell(0, 8, f"{keys[-1].replace('_', ' ').title()}: {value}", 0, 1)
        
        elif section_type == "table":
            # Table section
            data_key = section.get("data_key")
            if data_key:
                table_data = self._get_nested_data(data, data_key)
                if isinstance(table_data, dict):
                    # Convert dict to table
                    pdf.ln(5)
                    col_width = 95
                    row_height = 10
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(col_width, row_height, "Key", 1)
                    pdf.cell(col_width, row_height, "Value", 1)
                    pdf.ln(row_height)
                    pdf.set_font("Arial", "", 12)
                    
                    for key, value in table_data.items():
                        pdf.cell(col_width, row_height, str(key).replace('_', ' ').title(), 1)
                        pdf.cell(col_width, row_height, str(value), 1)
                        pdf.ln(row_height)
        
        elif section_type == "metrics_table":
            # Metrics table section
            data_key = section.get("data_key")
            if data_key:
                metrics_data = self._get_nested_data(data, data_key)
                if isinstance(metrics_data, dict):
                    # Convert metrics to table
                    pdf.ln(5)
                    col_width = 95
                    row_height = 10
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(col_width, row_height, "Metric", 1)
                    pdf.cell(col_width, row_height, "Value", 1)
                    pdf.ln(row_height)
                    pdf.set_font("Arial", "", 12)
                    
                    for key, value in metrics_data.items():
                        pdf.cell(col_width, row_height, str(key).replace('_', ' ').title(), 1)
                        pdf.cell(col_width, row_height, str(value), 1)
                        pdf.ln(row_height)
        
        # Add space after section
        pdf.ln(10)
    
    def _add_generic_pdf_content(self, pdf: FPDF, data: Dict[str, Any]) -> None:
        """Add generic content to PDF when no template is available."""
        for key, value in data.items():
            if isinstance(value, dict):
                # Section header
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, key.replace('_', ' ').title(), 0, 1)
                pdf.set_font("Arial", "", 12)
                
                # Nested content
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        pdf.set_font("Arial", "I", 12)
                        pdf.cell(0, 8, sub_key.replace('_', ' ').title(), 0, 1)
                        pdf.set_font("Arial", "", 12)
                        
                        for k, v in sub_value.items():
                            pdf.cell(0, 8, f"{k.replace('_', ' ').title()}: {v}", 0, 1)
                    else:
                        pdf.cell(0, 8, f"{sub_key.replace('_', ' ').title()}: {sub_value}", 0, 1)
                
                # Add space after section
                pdf.ln(5)
            else:
                # Simple key-value
                pdf.cell(0, 8, f"{key.replace('_', ' ').title()}: {value}", 0, 1)
    
    async def _export_to_xlsx(self, report: ReportData) -> Dict[str, Any]:
        """Export report to Excel format."""
        try:
            # Create Excel file
            filename = f"{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = os.path.join(self.output_dir, filename)
            
            # Create workbook
            workbook = xlsxwriter.Workbook(file_path)
            
            # Add summary sheet
            summary_sheet = workbook.add_worksheet("Summary")
            
            # Add title
            title_format = workbook.add_format({'bold': True, 'font_size': 16})
            summary_sheet.write(0, 0, f"{report.report_type.replace('_', ' ').title()} Report", title_format)
            summary_sheet.write(1, 0, f"Period: {report.period}")
            summary_sheet.write(2, 0, f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Add data sheets based on report structure
            row = 4
            for key, value in report.data.items():
                if isinstance(value, dict):
                    # Create sheet for this section
                    sheet_name = key[:31]  # Excel sheet name length limit
                    sheet = workbook.add_worksheet(sheet_name)
                    
                    # Add link to sheet
                    summary_sheet.write(row, 0, key.replace('_', ' ').title())
                    summary_sheet.write(row, 1, f'See "{sheet_name}" sheet')
                    row += 1
                    
                    # Add data to sheet
                    self._add_dict_to_sheet(sheet, value)
                else:
                    # Add to summary
                    summary_sheet.write(row, 0, key.replace('_', ' ').title())
                    summary_sheet.write(row, 1, str(value))
                    row += 1
            
            # Close workbook
            workbook.close()
            
            file_size = os.path.getsize(file_path)
            
            return {
                "format": ReportFormat.XLSX,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise
    
    def _add_dict_to_sheet(self, sheet, data: Dict[str, Any], start_row: int = 0, start_col: int = 0) -> int:
        """Add dictionary data to Excel sheet."""
        row = start_row
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Add subheader
                sheet.write(row, start_col, key.replace('_', ' ').title())
                row += 1
                # Add nested dict
                row = self._add_dict_to_sheet(sheet, value, row, start_col + 1)
                row += 1
            elif isinstance(value, list):
                # Add subheader
                sheet.write(row, start_col, key.replace('_', ' ').title())
                row += 1
                
                # Check if list contains dicts
                if value and isinstance(value[0], dict):
                    # Get all possible keys
                    all_keys = set()
                    for item in value:
                        all_keys.update(item.keys())
                    
                    # Write headers
                    for col, header in enumerate(all_keys):
                        sheet.write(row, start_col + col, header.replace('_', ' ').title())
                    row += 1
                    
                    # Write data
                    for item in value:
                        for col, header in enumerate(all_keys):
                            sheet.write(row, start_col + col, item.get(header, ""))
                        row += 1
                else:
                    # Simple list
                    for col, item in enumerate(value):
                        sheet.write(row, start_col + col, item)
                    row += 1
            else:
                # Simple key-value
                sheet.write(row, start_col, key.replace('_', ' ').title())
                sheet.write(row, start_col + 1, value)
                row += 1
        
        return row
    
    def _convert_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert report data to pandas DataFrame."""
        # Flatten nested dictionaries
        flat_data = {}
        
        def flatten_dict(d, prefix=""):
            for key, value in d.items():
                if isinstance(value, dict):
                    flatten_dict(value, f"{prefix}{key}_")
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # Skip lists of dicts for now
                    pass
                else:
                    flat_data[f"{prefix}{key}"] = value
        
        flatten_dict(data)
        
        # Create DataFrame
        df = pd.DataFrame([flat_data])
        
        return df
    
    def _get_nested_data(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get nested data using dot notation."""
        if "." not in key_path:
            return data.get(key_path)
        
        keys = key_path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


class ReportScheduler:
    """Scheduler for automated report generation."""
    
    def __init__(self, reporting_engine: ReportingEngine):
        """
        Initialize the report scheduler.
        
        Args:
            reporting_engine: ReportingEngine instance
        """
        self.reporting_engine = reporting_engine
        self.scheduled_reports = []
        logger.info("Report Scheduler initialized")
    
    async def schedule_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a report for automated generation.
        
        Args:
            report_config: Report configuration
            
        Returns:
            Scheduled report details
        """
        # Validate config
        required_fields = ["report_type", "schedule", "export_format"]
        for field in required_fields:
            if field not in report_config:
                raise ValueError(f"Missing required field: {field}")
        
        # Create schedule entry
        schedule_id = f"schedule_{len(self.scheduled_reports) + 1}"
        
        schedule_entry = {
            "id": schedule_id,
            "report_type": report_config["report_type"],
            "schedule": report_config["schedule"],
            "export_format": report_config["export_format"],
            "parameters": report_config.get("parameters", {}),
            "recipients": report_config.get("recipients", []),
            "created_at": datetime.now(),
            "last_run": None,
            "next_run": self._calculate_next_run(report_config["schedule"]),
            "status": "active"
        }
        
        self.scheduled_reports.append(schedule_entry)
        
        logger.info(f"Report scheduled: {schedule_id} - {report_config['report_type']}")
        return schedule_entry
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time based on schedule."""
        now = datetime.now()
        
        if schedule == "daily":
            return datetime(now.year, now.month, now.day, 0, 0) + timedelta(days=1)
        elif schedule == "weekly":
            days_ahead = 7 - now.weekday()
            if days_ahead == 0:
                days_ahead = 7
            return datetime(now.year, now.month, now.day, 0, 0) + timedelta(days=days_ahead)
        elif schedule == "monthly":
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1, 0, 0)
            else:
                next_month = datetime(now.year, now.month + 1, 1, 0, 0)
            return next_month
        else:
            # Default to tomorrow
            return datetime(now.year, now.month, now.day, 0, 0) + timedelta(days=1)
"""