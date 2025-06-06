"""
HTML Reporter

Generates comprehensive HTML reports with interactive visualizations.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Template = None
    Environment = None
    FileSystemLoader = None

from ..core.analysis_engine import AnalysisResult


class HTMLReporter:
    """
    Generates comprehensive HTML reports with interactive visualizations.
    
    Uses Jinja2 templates and D3.js for creating rich, interactive reports.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the HTML reporter.
        
        Args:
            template_dir: Directory containing HTML templates
        """
        self.logger = logging.getLogger(__name__)
        
        if not JINJA2_AVAILABLE:
            self.logger.warning("Jinja2 not available. HTML reporting will be limited.")
            self.env = None
        else:
            # Setup Jinja2 environment
            if template_dir:
                self.env = Environment(loader=FileSystemLoader(template_dir))
            else:
                # Use default template directory
                default_template_dir = Path(__file__).parent / "templates"
                self.env = Environment(loader=FileSystemLoader(str(default_template_dir)))
    
    def generate_report(
        self, 
        analysis_result: AnalysisResult, 
        output_path: str,
        title: Optional[str] = None,
        include_source: bool = False
    ) -> bool:
        """
        Generate a comprehensive HTML report.
        
        Args:
            analysis_result: Analysis results to report
            output_path: Path where to save the HTML report
            title: Custom title for the report
            include_source: Whether to include source code snippets
            
        Returns:
            True if report generated successfully, False otherwise
        """
        if not JINJA2_AVAILABLE:
            self.logger.error("Cannot generate HTML report: Jinja2 not available")
            return False
        
        try:
            # Prepare template data
            template_data = self._prepare_template_data(
                analysis_result, 
                title or "Codebase Analysis Report",
                include_source
            )
            
            # Load and render template
            template = self.env.get_template("analysis_report.html")
            html_content = template.render(**template_data)
            
            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            return False
    
    def generate_summary_report(
        self, 
        analysis_result: AnalysisResult, 
        output_path: str
    ) -> bool:
        """
        Generate a summary HTML report with key metrics only.
        
        Args:
            analysis_result: Analysis results to report
            output_path: Path where to save the HTML report
            
        Returns:
            True if report generated successfully, False otherwise
        """
        try:
            # Create a simplified template for summary
            summary_template = self._create_summary_template()
            
            # Prepare summary data
            summary_data = {
                'title': 'Codebase Analysis Summary',
                'timestamp': analysis_result.timestamp,
                'execution_time': f"{analysis_result.execution_time:.2f}",
                'codebase_summary': analysis_result.codebase_summary,
                'metrics': analysis_result.metrics,
                'issue_count': len(analysis_result.issues),
                'dead_code_count': len(analysis_result.dead_code),
                'test_coverage': analysis_result.test_analysis.get('coverage_estimate', 0.0)
            }
            
            # Render template
            html_content = summary_template.render(**summary_data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Summary HTML report generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary HTML report: {e}")
            return False
    
    def _prepare_template_data(
        self, 
        analysis_result: AnalysisResult, 
        title: str,
        include_source: bool
    ) -> Dict[str, Any]:
        """
        Prepare data for template rendering.
        
        Args:
            analysis_result: Analysis results
            title: Report title
            include_source: Whether to include source code
            
        Returns:
            Dictionary of template data
        """
        # Convert analysis result to template-friendly format
        template_data = {
            'title': title,
            'timestamp': analysis_result.timestamp,
            'execution_time': f"{analysis_result.execution_time:.2f}",
            'codebase_summary': analysis_result.codebase_summary,
            'file_summaries': self._format_file_summaries(analysis_result.file_summaries),
            'class_summaries': self._format_class_summaries(analysis_result.class_summaries),
            'function_summaries': self._format_function_summaries(analysis_result.function_summaries),
            'symbol_summaries': analysis_result.symbol_summaries,
            'metrics': analysis_result.metrics,
            'issues': self._format_issues(analysis_result.issues),
            'dependencies': analysis_result.dependencies,
            'dead_code': analysis_result.dead_code,
            'test_analysis': analysis_result.test_analysis,
            'chart_data': self._prepare_chart_data(analysis_result)
        }
        
        # Add source code if requested
        if include_source:
            template_data['include_source'] = True
            # Add source code snippets to relevant sections
            # This would be implemented based on specific requirements
        
        return template_data
    
    def _format_file_summaries(self, file_summaries: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format file summaries for template rendering."""
        formatted = []
        for name, data in file_summaries.items():
            if 'error' not in data:
                formatted.append({
                    'name': name,
                    'lines_of_code': data.get('lines_of_code', 0),
                    'functions': data.get('functions', 0),
                    'classes': data.get('classes', 0),
                    'complexity': f"{data.get('complexity', 0):.1f}",
                    'imports': data.get('imports', 0),
                    'symbols': data.get('symbols', 0)
                })
        return sorted(formatted, key=lambda x: x['lines_of_code'], reverse=True)
    
    def _format_class_summaries(self, class_summaries: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format class summaries for template rendering."""
        formatted = []
        for name, data in class_summaries.items():
            if 'error' not in data:
                formatted.append({
                    'name': name,
                    'methods': data.get('methods', 0),
                    'attributes': data.get('attributes', 0),
                    'inheritance_depth': data.get('inheritance_depth', 0),
                    'complexity': f"{data.get('complexity', 0):.1f}",
                    'usages': data.get('usages', 0),
                    'dependencies': data.get('dependencies', 0)
                })
        return sorted(formatted, key=lambda x: x['methods'], reverse=True)
    
    def _format_function_summaries(self, function_summaries: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format function summaries for template rendering."""
        formatted = []
        for name, data in function_summaries.items():
            if 'error' not in data:
                formatted.append({
                    'name': name,
                    'parameters': data.get('parameters', 0),
                    'function_calls': data.get('function_calls', 0),
                    'usages': data.get('usages', 0),
                    'complexity': f"{data.get('complexity', 0):.1f}",
                    'call_sites': data.get('call_sites', 0),
                    'is_recursive': data.get('is_recursive', False)
                })
        return sorted(formatted, key=lambda x: x['complexity'], reverse=True)
    
    def _format_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format issues for template rendering."""
        formatted = []
        for issue in issues:
            formatted.append({
                'type': issue.get('type', 'unknown').replace('_', ' ').title(),
                'target': issue.get('target', 'N/A'),
                'message': issue.get('message', ''),
                'severity': issue.get('severity', 'info')
            })
        return formatted
    
    def _prepare_chart_data(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Prepare data for D3.js charts."""
        chart_data = {
            'overview': {
                'nodes': analysis_result.codebase_summary.get('nodes', {}),
                'edges': analysis_result.codebase_summary.get('edges', {}),
                'complexity': analysis_result.codebase_summary.get('complexity_score', 0)
            },
            'metrics': analysis_result.metrics,
            'file_sizes': [
                {
                    'name': name, 
                    'size': data.get('lines_of_code', 0)
                }
                for name, data in analysis_result.file_summaries.items()
                if 'error' not in data
            ],
            'complexity_distribution': [
                {
                    'name': name,
                    'complexity': data.get('complexity', 0)
                }
                for name, data in analysis_result.function_summaries.items()
                if 'error' not in data
            ]
        }
        return chart_data
    
    def _create_summary_template(self) -> Template:
        """Create a simple summary template."""
        summary_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{title}}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .metric { display: inline-block; margin: 20px; padding: 20px; 
                         background: #f5f5f5; border-radius: 8px; text-align: center; }
                .metric-value { font-size: 2em; font-weight: bold; color: #333; }
                .metric-label { color: #666; margin-top: 5px; }
                .header { text-align: center; margin-bottom: 40px; }
                .timestamp { text-align: center; margin-top: 40px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{title}}</h1>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{codebase_summary.nodes.files}}</div>
                <div class="metric-label">Files</div>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{codebase_summary.nodes.functions}}</div>
                <div class="metric-label">Functions</div>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{codebase_summary.nodes.classes}}</div>
                <div class="metric-label">Classes</div>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{issue_count}}</div>
                <div class="metric-label">Issues</div>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{dead_code_count}}</div>
                <div class="metric-label">Dead Code</div>
            </div>
            
            <div class="metric">
                <div class="metric-value">{{(test_coverage * 100) | round(1)}}%</div>
                <div class="metric-label">Test Coverage</div>
            </div>
            
            <div class="timestamp">
                Generated on {{timestamp}} | Execution time: {{execution_time}}s
            </div>
        </body>
        </html>
        '''
        
        return Template(summary_html)
    
    def export_json_data(self, analysis_result: AnalysisResult, output_path: str) -> bool:
        """
        Export analysis data as JSON for external processing.
        
        Args:
            analysis_result: Analysis results to export
            output_path: Path where to save the JSON file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Convert analysis result to JSON-serializable format
            data = {
                'timestamp': analysis_result.timestamp,
                'execution_time': analysis_result.execution_time,
                'codebase_summary': analysis_result.codebase_summary,
                'file_summaries': analysis_result.file_summaries,
                'class_summaries': analysis_result.class_summaries,
                'function_summaries': analysis_result.function_summaries,
                'symbol_summaries': analysis_result.symbol_summaries,
                'metrics': analysis_result.metrics,
                'issues': analysis_result.issues,
                'dependencies': analysis_result.dependencies,
                'dead_code': analysis_result.dead_code,
                'test_analysis': analysis_result.test_analysis
            }
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON data exported: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON data: {e}")
            return False

