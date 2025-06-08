#!/usr/bin/env python3
"""
📤 EXPORTERS MODULE 📤

Comprehensive export capabilities for analysis results and visualizations.
Supports multiple output formats for different use cases and stakeholders.

Features:
- ReportExporter: Core export engine with multiple format support
- HTML export with interactive features
- PDF export for documentation and reports
- JSON export for data interchange
- SVG export for vector graphics
- CSV export for spreadsheet analysis
- Markdown export for documentation
"""

import logging
import json
import csv
import base64
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path
from datetime import datetime
import tempfile
import zipfile

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not available - PDF export will be limited")

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
    logger.warning("CairoSVG not available - SVG to PNG conversion will be limited")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available - advanced data export will be limited")

@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: str = "html"  # html, pdf, json, svg, csv, markdown
    include_metadata: bool = True
    include_timestamp: bool = True
    compress: bool = False
    quality: str = "high"  # low, medium, high
    custom_css: str = ""
    custom_template: str = ""
    output_dir: Optional[Path] = None

@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    format: str = ""
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class ReportExporter:
    """
    Core export engine supporting multiple output formats.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize the report exporter."""
        self.config = config or ExportConfig()
        self.supported_formats = ["html", "json", "csv", "markdown"]
        
        # Add PDF support if WeasyPrint is available
        if WEASYPRINT_AVAILABLE:
            self.supported_formats.append("pdf")
        
        # Add SVG support if CairoSVG is available
        if CAIROSVG_AVAILABLE:
            self.supported_formats.extend(["svg", "png"])
    
    def export(self, data: Dict[str, Any], output_path: Path, format: Optional[str] = None) -> ExportResult:
        """
        Export data to the specified format and path.
        
        Args:
            data: Data to export
            output_path: Output file path
            format: Export format (overrides config)
        
        Returns:
            ExportResult with operation details
        """
        export_format = format or self.config.format
        
        if export_format not in self.supported_formats:
            return ExportResult(
                success=False,
                error_message=f"Unsupported format: {export_format}. Supported: {self.supported_formats}"
            )
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata if requested
            if self.config.include_metadata:
                data = self._add_metadata(data)
            
            # Export based on format
            if export_format == "html":
                return self._export_html(data, output_path)
            elif export_format == "pdf":
                return self._export_pdf(data, output_path)
            elif export_format == "json":
                return self._export_json(data, output_path)
            elif export_format == "csv":
                return self._export_csv(data, output_path)
            elif export_format == "markdown":
                return self._export_markdown(data, output_path)
            elif export_format == "svg":
                return self._export_svg(data, output_path)
            else:
                return ExportResult(
                    success=False,
                    error_message=f"Export method not implemented for format: {export_format}"
                )
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e)
            )
    
    def _add_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata to the export data."""
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": self.config.format,
            "export_config": self.config.__dict__,
            "data_summary": {
                "total_keys": len(data),
                "data_types": {key: type(value).__name__ for key, value in data.items()}
            }
        }
        
        # Create a copy to avoid modifying original data
        export_data = data.copy()
        export_data["_export_metadata"] = metadata
        
        return export_data
    
    def _export_html(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as HTML."""
        html_content = self._generate_html_content(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="html"
        )
    
    def _export_pdf(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as PDF."""
        if not WEASYPRINT_AVAILABLE:
            return ExportResult(
                success=False,
                error_message="WeasyPrint not available for PDF export"
            )
        
        # Generate HTML first
        html_content = self._generate_html_content(data, for_pdf=True)
        
        # Convert to PDF
        try:
            weasyprint.HTML(string=html_content).write_pdf(str(output_path))
            file_size = output_path.stat().st_size
            
            return ExportResult(
                success=True,
                file_path=output_path,
                file_size=file_size,
                format="pdf"
            )
        except Exception as e:
            return ExportResult(
                success=False,
                error_message=f"PDF generation failed: {e}"
            )
    
    def _export_json(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="json"
        )
    
    def _export_csv(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as CSV."""
        # Convert data to tabular format
        rows = self._flatten_data_for_csv(data)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="csv"
        )
    
    def _export_markdown(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as Markdown."""
        markdown_content = self._generate_markdown_content(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="markdown"
        )
    
    def _export_svg(self, data: Dict[str, Any], output_path: Path) -> ExportResult:
        """Export data as SVG."""
        svg_content = self._generate_svg_content(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="svg"
        )
    
    def _generate_html_content(self, data: Dict[str, Any], for_pdf: bool = False) -> str:
        """Generate HTML content from data."""
        title = data.get('title', 'Analysis Report')
        
        # Use custom template if provided
        if self.config.custom_template:
            # TODO: Implement template rendering
            pass
        
        # Basic HTML structure
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .metric-name {{ font-weight: bold; color: #333; }}
                .metric-value {{ font-size: 1.2em; color: #007bff; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f2f2f2; }}
                .chart-container {{ margin: 20px 0; text-align: center; }}
                {self.config.custom_css}
            </style>
            {'' if for_pdf else '<script src="https://d3js.org/d3.v7.min.js"></script>'}
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                {f'<p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>' if self.config.include_timestamp else ''}
            </div>
        """
        
        # Add content sections
        for key, value in data.items():
            if key.startswith('_'):  # Skip metadata
                continue
            
            html += f'<div class="section">'
            html += f'<h2>{key.replace("_", " ").title()}</h2>'
            
            if isinstance(value, dict):
                html += self._dict_to_html(value)
            elif isinstance(value, list):
                html += self._list_to_html(value)
            else:
                html += f'<p>{value}</p>'
            
            html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_content(self, data: Dict[str, Any]) -> str:
        """Generate Markdown content from data."""
        title = data.get('title', 'Analysis Report')
        
        markdown = f"# {title}\n\n"
        
        if self.config.include_timestamp:
            markdown += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        for key, value in data.items():
            if key.startswith('_'):  # Skip metadata
                continue
            
            markdown += f"## {key.replace('_', ' ').title()}\n\n"
            
            if isinstance(value, dict):
                markdown += self._dict_to_markdown(value)
            elif isinstance(value, list):
                markdown += self._list_to_markdown(value)
            else:
                markdown += f"{value}\n\n"
        
        return markdown
    
    def _generate_svg_content(self, data: Dict[str, Any]) -> str:
        """Generate SVG content from data."""
        # Basic SVG structure for data visualization
        svg = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="white"/>
            <text x="400" y="50" text-anchor="middle" font-size="24" font-weight="bold">
                Analysis Report
            </text>
        """
        
        # Add simple bar chart for numeric data
        y_offset = 100
        numeric_data = self._extract_numeric_data(data)
        
        if numeric_data:
            max_value = max(numeric_data.values()) if numeric_data.values() else 1
            bar_width = 600 / len(numeric_data) if numeric_data else 0
            
            for i, (key, value) in enumerate(numeric_data.items()):
                x = 100 + i * bar_width
                height = (value / max_value) * 300
                y = 500 - height
                
                svg += f"""
                <rect x="{x}" y="{y}" width="{bar_width * 0.8}" height="{height}" 
                      fill="steelblue" stroke="white" stroke-width="1"/>
                <text x="{x + bar_width * 0.4}" y="{520}" text-anchor="middle" font-size="12">
                    {key[:10]}
                </text>
                <text x="{x + bar_width * 0.4}" y="{y - 5}" text-anchor="middle" font-size="10">
                    {value}
                </text>
                """
        
        svg += "</svg>"
        return svg
    
    def _dict_to_html(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to HTML table."""
        html = '<table class="table">'
        for key, value in data.items():
            html += f'<tr><td class="metric-name">{key}</td><td class="metric-value">{value}</td></tr>'
        html += '</table>'
        return html
    
    def _list_to_html(self, data: List[Any]) -> str:
        """Convert list to HTML."""
        if not data:
            return '<p>No data available</p>'
        
        if isinstance(data[0], dict):
            # Create table for list of dictionaries
            html = '<table class="table">'
            if data:
                # Header
                html += '<tr>'
                for key in data[0].keys():
                    html += f'<th>{key}</th>'
                html += '</tr>'
                
                # Rows
                for item in data:
                    html += '<tr>'
                    for value in item.values():
                        html += f'<td>{value}</td>'
                    html += '</tr>'
            html += '</table>'
        else:
            # Simple list
            html = '<ul>'
            for item in data:
                html += f'<li>{item}</li>'
            html += '</ul>'
        
        return html
    
    def _dict_to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to Markdown table."""
        markdown = "| Key | Value |\n|-----|-------|\n"
        for key, value in data.items():
            markdown += f"| {key} | {value} |\n"
        markdown += "\n"
        return markdown
    
    def _list_to_markdown(self, data: List[Any]) -> str:
        """Convert list to Markdown."""
        if not data:
            return "No data available\n\n"
        
        if isinstance(data[0], dict):
            # Create table for list of dictionaries
            if data:
                keys = list(data[0].keys())
                markdown = "| " + " | ".join(keys) + " |\n"
                markdown += "|" + "---|" * len(keys) + "\n"
                
                for item in data:
                    values = [str(item.get(key, '')) for key in keys]
                    markdown += "| " + " | ".join(values) + " |\n"
                markdown += "\n"
        else:
            # Simple list
            markdown = ""
            for item in data:
                markdown += f"- {item}\n"
            markdown += "\n"
        
        return markdown
    
    def _flatten_data_for_csv(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested data structure for CSV export."""
        rows = []
        
        def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
            flat = {}
            for key, value in d.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    flat.update(flatten_dict(value, new_key))
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        # Handle list of dictionaries
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                flat.update(flatten_dict(item, f"{new_key}.{i}"))
                            else:
                                flat[f"{new_key}.{i}"] = item
                    else:
                        flat[new_key] = ", ".join(map(str, value))
                else:
                    flat[new_key] = value
            return flat
        
        # If data contains lists of dictionaries, use them as rows
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value:
                    row = flatten_dict(item)
                    row['_section'] = key
                    rows.append(row)
        
        # If no suitable list found, create single row from all data
        if not rows:
            rows.append(flatten_dict(data))
        
        return rows
    
    def _extract_numeric_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric data for visualization."""
        numeric_data = {}
        
        def extract_numbers(d: Dict[str, Any], prefix: str = ""):
            for key, value in d.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (int, float)):
                    numeric_data[new_key] = float(value)
                elif isinstance(value, dict):
                    extract_numbers(value, new_key)
        
        extract_numbers(data)
        return numeric_data

def export_to_html(data: Dict[str, Any], output_path: Path, config: Optional[ExportConfig] = None) -> ExportResult:
    """
    Export data to HTML format.
    
    Args:
        data: Data to export
        output_path: Output file path
        config: Export configuration
    
    Returns:
        ExportResult with operation details
    """
    config = config or ExportConfig(format="html")
    exporter = ReportExporter(config)
    return exporter.export(data, output_path, "html")

def export_to_pdf(data: Dict[str, Any], output_path: Path, config: Optional[ExportConfig] = None) -> ExportResult:
    """
    Export data to PDF format.
    
    Args:
        data: Data to export
        output_path: Output file path
        config: Export configuration
    
    Returns:
        ExportResult with operation details
    """
    config = config or ExportConfig(format="pdf")
    exporter = ReportExporter(config)
    return exporter.export(data, output_path, "pdf")

def export_to_json(data: Dict[str, Any], output_path: Path, config: Optional[ExportConfig] = None) -> ExportResult:
    """
    Export data to JSON format.
    
    Args:
        data: Data to export
        output_path: Output file path
        config: Export configuration
    
    Returns:
        ExportResult with operation details
    """
    config = config or ExportConfig(format="json")
    exporter = ReportExporter(config)
    return exporter.export(data, output_path, "json")

def export_to_svg(data: Dict[str, Any], output_path: Path, config: Optional[ExportConfig] = None) -> ExportResult:
    """
    Export data to SVG format.
    
    Args:
        data: Data to export
        output_path: Output file path
        config: Export configuration
    
    Returns:
        ExportResult with operation details
    """
    config = config or ExportConfig(format="svg")
    exporter = ReportExporter(config)
    return exporter.export(data, output_path, "svg")

def export_multiple_formats(
    data: Dict[str, Any], 
    output_dir: Path, 
    formats: List[str], 
    base_name: str = "report"
) -> Dict[str, ExportResult]:
    """
    Export data to multiple formats.
    
    Args:
        data: Data to export
        output_dir: Output directory
        formats: List of formats to export
        base_name: Base name for output files
    
    Returns:
        Dictionary mapping format to ExportResult
    """
    results = {}
    
    for format_name in formats:
        output_path = output_dir / f"{base_name}.{format_name}"
        config = ExportConfig(format=format_name)
        exporter = ReportExporter(config)
        results[format_name] = exporter.export(data, output_path, format_name)
    
    return results

def create_export_package(
    data: Dict[str, Any], 
    output_path: Path, 
    formats: List[str] = None,
    include_raw_data: bool = True
) -> ExportResult:
    """
    Create a ZIP package with exports in multiple formats.
    
    Args:
        data: Data to export
        output_path: Output ZIP file path
        formats: List of formats to include
        include_raw_data: Whether to include raw JSON data
    
    Returns:
        ExportResult for the ZIP package
    """
    formats = formats or ["html", "json", "csv", "markdown"]
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Export to all formats
            results = export_multiple_formats(data, temp_path, formats)
            
            # Create ZIP package
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for format_name, result in results.items():
                    if result.success and result.file_path:
                        zipf.write(result.file_path, result.file_path.name)
                
                # Add raw data if requested
                if include_raw_data:
                    raw_data_path = temp_path / "raw_data.json"
                    with open(raw_data_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    zipf.write(raw_data_path, "raw_data.json")
        
        file_size = output_path.stat().st_size
        
        return ExportResult(
            success=True,
            file_path=output_path,
            file_size=file_size,
            format="zip",
            metadata={"included_formats": formats, "include_raw_data": include_raw_data}
        )
    
    except Exception as e:
        return ExportResult(
            success=False,
            error_message=f"Failed to create export package: {e}"
        )

