"""
REST API Endpoints for Graph-Sitter Analytics

Provides HTTP API for analytics operations:
- Analysis execution
- Results retrieval
- Dashboard generation
- Report export
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.logger import get_logger

from ..core.analytics_engine import AnalyticsEngine, AnalysisConfig
from ..core.analysis_result import AnalysisReport
from ..visualization.dashboard import AnalyticsDashboard

logger = get_logger(__name__)


class AnalyticsAPI:
    """
    REST API interface for Graph-Sitter Analytics.
    
    Provides endpoints for running analysis, retrieving results,
    and generating visualizations.
    """
    
    def __init__(self):
        self.engine = AnalyticsEngine()
        self.dashboard = AnalyticsDashboard()
        self._analysis_cache: Dict[str, AnalysisReport] = {}
        self._running_analyses: Dict[str, Dict[str, Any]] = {}
    
    def analyze_codebase(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start codebase analysis.
        
        Args:
            codebase: Codebase to analyze
            config: Analysis configuration
            
        Returns:
            Analysis job information
        """
        try:
            # Create analysis config
            analysis_config = AnalysisConfig()
            if config:
                # Update config with provided parameters
                for key, value in config.items():
                    if hasattr(analysis_config, key):
                        setattr(analysis_config, key, value)
            
            # Update engine config
            self.engine.config = analysis_config
            
            # Generate job ID
            job_id = f"analysis_{int(time.time())}_{hash(str(codebase))}"
            
            # Start analysis
            start_time = time.time()
            self._running_analyses[job_id] = {
                "status": "running",
                "start_time": start_time,
                "codebase_name": getattr(codebase, 'name', 'Unknown')
            }
            
            try:
                # Run analysis
                report = self.engine.analyze_codebase(codebase)
                
                # Cache result
                self._analysis_cache[job_id] = report
                
                # Update job status
                self._running_analyses[job_id].update({
                    "status": "completed",
                    "end_time": time.time(),
                    "execution_time": report.execution_time
                })
                
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "execution_time": report.execution_time,
                    "summary": report.get_summary_stats()
                }
                
            except Exception as e:
                # Update job status
                self._running_analyses[job_id].update({
                    "status": "failed",
                    "end_time": time.time(),
                    "error": str(e)
                })
                
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Failed to start analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_analysis_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get analysis job status.
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            Job status information
        """
        if job_id not in self._running_analyses:
            return {
                "status": "not_found",
                "error": f"Job {job_id} not found"
            }
        
        job_info = self._running_analyses[job_id].copy()
        
        # Add progress information if running
        if job_info["status"] == "running":
            elapsed = time.time() - job_info["start_time"]
            job_info["elapsed_time"] = elapsed
        
        return job_info
    
    def get_analysis_results(self, job_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Get analysis results.
        
        Args:
            job_id: Analysis job ID
            format: Result format (json, summary)
            
        Returns:
            Analysis results
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        report = self._analysis_cache[job_id]
        
        if format == "summary":
            return {
                "status": "success",
                "data": report.get_summary_stats()
            }
        elif format == "json":
            return {
                "status": "success",
                "data": report.to_dict()
            }
        else:
            return {
                "status": "error",
                "error": f"Unsupported format: {format}"
            }
    
    def get_analyzer_results(self, job_id: str, analyzer_name: str) -> Dict[str, Any]:
        """
        Get results from a specific analyzer.
        
        Args:
            job_id: Analysis job ID
            analyzer_name: Name of the analyzer
            
        Returns:
            Analyzer-specific results
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        report = self._analysis_cache[job_id]
        analyzer_result = report.get_analyzer_result(analyzer_name)
        
        if not analyzer_result:
            return {
                "status": "error",
                "error": f"Analyzer {analyzer_name} not found in results"
            }
        
        return {
            "status": "success",
            "data": analyzer_result.to_dict()
        }
    
    def get_findings_by_severity(self, job_id: str, severity: str) -> Dict[str, Any]:
        """
        Get findings filtered by severity.
        
        Args:
            job_id: Analysis job ID
            severity: Severity level (critical, high, medium, low)
            
        Returns:
            Filtered findings
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        report = self._analysis_cache[job_id]
        
        # Get findings by severity
        if severity.lower() == "critical":
            findings = report.critical_findings
        elif severity.lower() == "high":
            findings = report.high_findings
        else:
            # Get all findings and filter
            all_findings = []
            for result in report.analysis_results.values():
                all_findings.extend(result.findings)
            
            from ..core.analysis_result import Severity
            severity_map = {
                "medium": Severity.MEDIUM,
                "low": Severity.LOW
            }
            
            target_severity = severity_map.get(severity.lower())
            if target_severity:
                findings = [f for f in all_findings if f.severity == target_severity]
            else:
                return {
                    "status": "error",
                    "error": f"Invalid severity: {severity}"
                }
        
        return {
            "status": "success",
            "data": {
                "severity": severity,
                "count": len(findings),
                "findings": [f.to_dict() for f in findings]
            }
        }
    
    def get_findings_by_file(self, job_id: str, file_path: str) -> Dict[str, Any]:
        """
        Get findings for a specific file.
        
        Args:
            job_id: Analysis job ID
            file_path: Path to the file
            
        Returns:
            File-specific findings
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        report = self._analysis_cache[job_id]
        findings = report.get_findings_by_file(file_path)
        
        return {
            "status": "success",
            "data": {
                "file_path": file_path,
                "count": len(findings),
                "findings": [f.to_dict() for f in findings]
            }
        }
    
    def generate_dashboard(self, job_id: str) -> Dict[str, Any]:
        """
        Generate interactive dashboard.
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            Dashboard data
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        try:
            report = self._analysis_cache[job_id]
            dashboard_data = self.dashboard.create_comprehensive_dashboard(report)
            
            return {
                "status": "success",
                "data": dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_report(self, job_id: str, format: str = "json", output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export analysis report.
        
        Args:
            job_id: Analysis job ID
            format: Export format (json, html, markdown)
            output_path: Output file path
            
        Returns:
            Export status
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        try:
            report = self._analysis_cache[job_id]
            
            if not output_path:
                timestamp = int(time.time())
                output_path = f"analytics_report_{job_id}_{timestamp}.{format}"
            
            if format == "json":
                report.save_to_file(output_path, "json")
            elif format == "html":
                dashboard_data = self.dashboard.create_comprehensive_dashboard(report)
                self.dashboard.export_dashboard(dashboard_data, output_path, "html")
            elif format == "markdown":
                self._export_markdown_report(report, output_path)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported format: {format}"
                }
            
            return {
                "status": "success",
                "output_path": output_path,
                "format": format
            }
            
        except Exception as e:
            logger.error(f"Failed to export report: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_metrics_summary(self, job_id: str) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            Metrics summary
        """
        if job_id not in self._analysis_cache:
            return {
                "status": "error",
                "error": f"Results for job {job_id} not found"
            }
        
        report = self._analysis_cache[job_id]
        
        # Aggregate metrics from all analyzers
        metrics_summary = {
            "overall_quality_score": report.overall_quality_score,
            "total_findings": report.total_findings,
            "execution_time": report.execution_time,
            "analyzers": {}
        }
        
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                metrics_summary["analyzers"][analyzer_name] = {
                    "quality_score": result.metrics.quality_score,
                    "findings_count": len(result.findings),
                    "execution_time": result.metrics.execution_time,
                    "files_analyzed": result.metrics.files_analyzed
                }
        
        return {
            "status": "success",
            "data": metrics_summary
        }
    
    def list_analysis_jobs(self) -> Dict[str, Any]:
        """
        List all analysis jobs.
        
        Returns:
            List of analysis jobs
        """
        jobs = []
        
        for job_id, job_info in self._running_analyses.items():
            job_summary = {
                "job_id": job_id,
                "status": job_info["status"],
                "codebase_name": job_info.get("codebase_name", "Unknown"),
                "start_time": job_info["start_time"]
            }
            
            if "end_time" in job_info:
                job_summary["end_time"] = job_info["end_time"]
                job_summary["execution_time"] = job_info["end_time"] - job_info["start_time"]
            
            if "error" in job_info:
                job_summary["error"] = job_info["error"]
            
            jobs.append(job_summary)
        
        # Sort by start time (newest first)
        jobs.sort(key=lambda x: x["start_time"], reverse=True)
        
        return {
            "status": "success",
            "data": {
                "total_jobs": len(jobs),
                "jobs": jobs
            }
        }
    
    def delete_analysis_results(self, job_id: str) -> Dict[str, Any]:
        """
        Delete analysis results.
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            Deletion status
        """
        deleted_items = []
        
        if job_id in self._analysis_cache:
            del self._analysis_cache[job_id]
            deleted_items.append("results")
        
        if job_id in self._running_analyses:
            del self._running_analyses[job_id]
            deleted_items.append("job_info")
        
        if deleted_items:
            return {
                "status": "success",
                "message": f"Deleted {', '.join(deleted_items)} for job {job_id}"
            }
        else:
            return {
                "status": "error",
                "error": f"Job {job_id} not found"
            }
    
    def get_supported_analyzers(self) -> Dict[str, Any]:
        """
        Get list of supported analyzers.
        
        Returns:
            Supported analyzers information
        """
        analyzers_info = {}
        
        for analyzer_name, analyzer in self.engine.analyzers.items():
            analyzers_info[analyzer_name] = analyzer.get_analyzer_info()
        
        return {
            "status": "success",
            "data": {
                "total_analyzers": len(analyzers_info),
                "analyzers": analyzers_info
            }
        }
    
    def _export_markdown_report(self, report: AnalysisReport, output_path: str):
        """Export report as Markdown."""
        stats = report.get_summary_stats()
        
        markdown_content = f"""# Graph-Sitter Analytics Report
        
## Overview

- **Codebase**: {report.codebase_name}
- **Analysis Date**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}
- **Execution Time**: {report.execution_time:.2f} seconds
- **Overall Quality Score**: {report.overall_quality_score:.1f}/100

## Summary Statistics

- **Total Files Analyzed**: {stats['total_files']:,}
- **Total Lines Analyzed**: {stats['total_lines']:,}
- **Total Issues Found**: {stats['total_findings']}
  - Critical: {stats['critical_issues']}
  - High: {stats['high_issues']}
  - Medium: {stats['medium_issues']}
  - Low: {stats['low_issues']}

## Analyzer Results

"""
        
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                markdown_content += f"""### {analyzer_name.title()} Analysis

- **Status**: {result.status}
- **Quality Score**: {result.metrics.quality_score:.1f}/100
- **Issues Found**: {len(result.findings)}
- **Execution Time**: {result.metrics.execution_time:.2f}s

"""
                
                # Add top findings
                if result.findings:
                    markdown_content += "#### Top Issues:\n\n"
                    top_findings = sorted(result.findings, 
                                        key=lambda x: (x.severity.value, x.title))[:5]
                    
                    for finding in top_findings:
                        markdown_content += f"- **{finding.severity.value.title()}**: {finding.title}\n"
                        markdown_content += f"  - File: `{finding.file_path}`\n"
                        if finding.line_number:
                            markdown_content += f"  - Line: {finding.line_number}\n"
                        markdown_content += f"  - {finding.description}\n\n"
        
        # Add recommendations
        if report.recommendations:
            markdown_content += "## Recommendations\n\n"
            for i, rec in enumerate(report.recommendations, 1):
                markdown_content += f"{i}. {rec}\n"
        
        markdown_content += f"""
## Generated by Graph-Sitter Analytics
Report generated on {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(output_path, 'w') as f:
            f.write(markdown_content)

