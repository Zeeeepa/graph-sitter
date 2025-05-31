"""
Comprehensive Test Reporting Framework

Provides detailed reporting and analysis capabilities for integration tests,
performance benchmarks, validation results, and workflow executions.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .core import IntegrationTestSuite, TestResult
from .performance import BenchmarkResult, PerformanceMetrics
from .validation import ValidationResult, ValidationIssue, ValidationSeverity
from .workflows import WorkflowScenario, WorkflowStatus

from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class TestExecutionSummary:
    """Summary of all test executions."""
    timestamp: str
    total_duration_ms: float
    integration_tests: Dict[str, Any] = field(default_factory=dict)
    performance_tests: Dict[str, Any] = field(default_factory=dict)
    validation_tests: Dict[str, Any] = field(default_factory=dict)
    workflow_tests: Dict[str, Any] = field(default_factory=dict)
    overall_status: str = "unknown"
    
    @property
    def total_tests(self) -> int:
        """Calculate total number of tests executed."""
        return (
            self.integration_tests.get("total_tests", 0) +
            self.performance_tests.get("total_benchmarks", 0) +
            self.validation_tests.get("total_validations", 0) +
            self.workflow_tests.get("total_workflows", 0)
        )
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate across all test types."""
        total_passed = (
            self.integration_tests.get("passed_tests", 0) +
            self.performance_tests.get("successful_benchmarks", 0) +
            self.validation_tests.get("passed_validations", 0) +
            self.workflow_tests.get("completed_workflows", 0)
        )
        
        if self.total_tests == 0:
            return 0.0
        
        return total_passed / self.total_tests


class TestReporter:
    """
    Comprehensive test reporting framework.
    
    Generates detailed reports for all types of integration testing including
    performance benchmarks, validation results, workflow executions, and
    overall system health assessments.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("test_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.integration_suites: List[IntegrationTestSuite] = []
        self.benchmark_results: List[BenchmarkResult] = []
        self.validation_results: List[ValidationResult] = []
        self.workflow_scenarios: List[WorkflowScenario] = []
        
        self.start_time = time.time()
    
    def add_integration_results(self, suites: List[IntegrationTestSuite]):
        """Add integration test results to the report."""
        self.integration_suites.extend(suites)
        logger.info(f"Added {len(suites)} integration test suites to report")
    
    def add_performance_results(self, results: List[BenchmarkResult]):
        """Add performance benchmark results to the report."""
        self.benchmark_results.extend(results)
        logger.info(f"Added {len(results)} benchmark results to report")
    
    def add_validation_results(self, results: List[ValidationResult]):
        """Add validation results to the report."""
        self.validation_results.extend(results)
        logger.info(f"Added {len(results)} validation results to report")
    
    def add_workflow_results(self, scenarios: List[WorkflowScenario]):
        """Add workflow execution results to the report."""
        self.workflow_scenarios.extend(scenarios)
        logger.info(f"Added {len(scenarios)} workflow scenarios to report")
    
    def generate_summary(self) -> TestExecutionSummary:
        """Generate a comprehensive test execution summary."""
        end_time = time.time()
        total_duration_ms = (end_time - self.start_time) * 1000
        
        # Integration test summary
        integration_summary = self._summarize_integration_tests()
        
        # Performance test summary
        performance_summary = self._summarize_performance_tests()
        
        # Validation test summary
        validation_summary = self._summarize_validation_tests()
        
        # Workflow test summary
        workflow_summary = self._summarize_workflow_tests()
        
        # Determine overall status
        overall_status = self._determine_overall_status(
            integration_summary, performance_summary, 
            validation_summary, workflow_summary
        )
        
        return TestExecutionSummary(
            timestamp=datetime.now().isoformat(),
            total_duration_ms=total_duration_ms,
            integration_tests=integration_summary,
            performance_tests=performance_summary,
            validation_tests=validation_summary,
            workflow_tests=workflow_summary,
            overall_status=overall_status
        )
    
    def _summarize_integration_tests(self) -> Dict[str, Any]:
        """Summarize integration test results."""
        if not self.integration_suites:
            return {"total_tests": 0, "passed_tests": 0, "failed_tests": 0}
        
        total_tests = sum(len(suite.test_results) for suite in self.integration_suites)
        passed_tests = sum(
            len([r for r in suite.test_results if r.status == "passed"])
            for suite in self.integration_suites
        )
        failed_tests = total_tests - passed_tests
        
        avg_duration = sum(suite.duration for suite in self.integration_suites) / len(self.integration_suites)
        avg_success_rate = sum(suite.success_rate for suite in self.integration_suites) / len(self.integration_suites)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_suites": len(self.integration_suites),
            "average_duration_ms": avg_duration * 1000,
            "average_success_rate": avg_success_rate
        }
    
    def _summarize_performance_tests(self) -> Dict[str, Any]:
        """Summarize performance benchmark results."""
        if not self.benchmark_results:
            return {"total_benchmarks": 0, "successful_benchmarks": 0, "regressions": 0}
        
        successful_benchmarks = len([r for r in self.benchmark_results if r.metrics])
        regressions = len([
            r for r in self.benchmark_results 
            if r.performance_regression and (
                r.performance_regression["execution_time_regression_percent"] > 10 or
                r.performance_regression["memory_regression_percent"] > 20
            )
        ])
        
        avg_execution_time = sum(
            r.average_metrics.execution_time_ms for r in self.benchmark_results
        ) / len(self.benchmark_results)
        
        avg_memory_usage = sum(
            r.average_metrics.memory_usage_mb for r in self.benchmark_results
        ) / len(self.benchmark_results)
        
        return {
            "total_benchmarks": len(self.benchmark_results),
            "successful_benchmarks": successful_benchmarks,
            "regressions": regressions,
            "average_execution_time_ms": avg_execution_time,
            "average_memory_usage_mb": avg_memory_usage
        }
    
    def _summarize_validation_tests(self) -> Dict[str, Any]:
        """Summarize validation test results."""
        if not self.validation_results:
            return {"total_validations": 0, "passed_validations": 0, "critical_issues": 0}
        
        passed_validations = len([r for r in self.validation_results if r.passed])
        total_issues = sum(len(r.issues) for r in self.validation_results)
        critical_issues = sum(len(r.critical_issues) for r in self.validation_results)
        error_issues = sum(len(r.error_issues) for r in self.validation_results)
        
        return {
            "total_validations": len(self.validation_results),
            "passed_validations": passed_validations,
            "failed_validations": len(self.validation_results) - passed_validations,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "error_issues": error_issues
        }
    
    def _summarize_workflow_tests(self) -> Dict[str, Any]:
        """Summarize workflow test results."""
        if not self.workflow_scenarios:
            return {"total_workflows": 0, "completed_workflows": 0, "failed_workflows": 0}
        
        completed_workflows = len([s for s in self.workflow_scenarios if s.status == WorkflowStatus.COMPLETED])
        failed_workflows = len([s for s in self.workflow_scenarios if s.status == WorkflowStatus.FAILED])
        
        avg_success_rate = sum(s.success_rate for s in self.workflow_scenarios) / len(self.workflow_scenarios)
        avg_duration = sum(s.duration_ms for s in self.workflow_scenarios) / len(self.workflow_scenarios)
        
        total_failed_steps = sum(len(s.failed_steps) for s in self.workflow_scenarios)
        
        return {
            "total_workflows": len(self.workflow_scenarios),
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "average_success_rate": avg_success_rate,
            "average_duration_ms": avg_duration,
            "total_failed_steps": total_failed_steps
        }
    
    def _determine_overall_status(self, integration: Dict, performance: Dict, 
                                validation: Dict, workflow: Dict) -> str:
        """Determine overall test execution status."""
        # Check for critical failures
        if validation.get("critical_issues", 0) > 0:
            return "critical_failure"
        
        # Check for significant failures
        integration_failure_rate = (
            integration.get("failed_tests", 0) / max(integration.get("total_tests", 1), 1)
        )
        workflow_failure_rate = (
            workflow.get("failed_workflows", 0) / max(workflow.get("total_workflows", 1), 1)
        )
        
        if integration_failure_rate > 0.2 or workflow_failure_rate > 0.3:
            return "failure"
        
        # Check for performance regressions
        if performance.get("regressions", 0) > 2:
            return "performance_degradation"
        
        # Check for validation issues
        if validation.get("error_issues", 0) > 5:
            return "validation_issues"
        
        # Check for partial success
        if (integration_failure_rate > 0.05 or workflow_failure_rate > 0.1 or 
            performance.get("regressions", 0) > 0):
            return "partial_success"
        
        return "success"
    
    def display_summary_dashboard(self, summary: TestExecutionSummary):
        """Display a comprehensive summary dashboard."""
        # Main title
        title_text = Text("🧪 Comprehensive Integration Testing Report", style="bold blue")
        console.print(Panel(title_text, expand=False))
        
        # Overall status
        status_colors = {
            "success": "green",
            "partial_success": "yellow", 
            "performance_degradation": "orange",
            "validation_issues": "orange",
            "failure": "red",
            "critical_failure": "bright_red"
        }
        
        status_emojis = {
            "success": "✅",
            "partial_success": "⚠️",
            "performance_degradation": "📉",
            "validation_issues": "🔍",
            "failure": "❌",
            "critical_failure": "🚨"
        }
        
        status_color = status_colors.get(summary.overall_status, "white")
        status_emoji = status_emojis.get(summary.overall_status, "❓")
        
        console.print(f"\n{status_emoji} Overall Status: [{status_color}]{summary.overall_status.upper()}[/{status_color}]")
        console.print(f"📊 Total Tests: {summary.total_tests}")
        console.print(f"⏱️  Total Duration: {summary.total_duration_ms:.1f}ms")
        console.print(f"📈 Overall Success Rate: {summary.overall_success_rate:.1%}")
        
        # Create summary table
        table = Table(title="Test Category Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Passed", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Success Rate", justify="right")
        table.add_column("Key Metrics", style="yellow")
        
        # Integration tests
        integration = summary.integration_tests
        table.add_row(
            "Integration Tests",
            str(integration.get("total_tests", 0)),
            str(integration.get("passed_tests", 0)),
            str(integration.get("failed_tests", 0)),
            f"{integration.get('average_success_rate', 0):.1%}",
            f"Avg: {integration.get('average_duration_ms', 0):.1f}ms"
        )
        
        # Performance tests
        performance = summary.performance_tests
        table.add_row(
            "Performance Tests",
            str(performance.get("total_benchmarks", 0)),
            str(performance.get("successful_benchmarks", 0)),
            str(performance.get("regressions", 0)),
            f"{(performance.get('successful_benchmarks', 0) / max(performance.get('total_benchmarks', 1), 1)):.1%}",
            f"Avg: {performance.get('average_execution_time_ms', 0):.1f}ms"
        )
        
        # Validation tests
        validation = summary.validation_tests
        table.add_row(
            "Validation Tests",
            str(validation.get("total_validations", 0)),
            str(validation.get("passed_validations", 0)),
            str(validation.get("failed_validations", 0)),
            f"{(validation.get('passed_validations', 0) / max(validation.get('total_validations', 1), 1)):.1%}",
            f"Issues: {validation.get('total_issues', 0)}"
        )
        
        # Workflow tests
        workflow = summary.workflow_tests
        table.add_row(
            "Workflow Tests",
            str(workflow.get("total_workflows", 0)),
            str(workflow.get("completed_workflows", 0)),
            str(workflow.get("failed_workflows", 0)),
            f"{workflow.get('average_success_rate', 0):.1%}",
            f"Avg: {workflow.get('average_duration_ms', 0):.1f}ms"
        )
        
        console.print(table)
        
        # Critical issues section
        if validation.get("critical_issues", 0) > 0:
            console.print(f"\n🚨 [red]Critical Issues Found: {validation['critical_issues']}[/red]")
            self._display_critical_issues()
        
        # Performance regressions
        if performance.get("regressions", 0) > 0:
            console.print(f"\n📉 [orange]Performance Regressions: {performance['regressions']}[/orange]")
            self._display_performance_regressions()
    
    def _display_critical_issues(self):
        """Display critical validation issues."""
        critical_issues = []
        for result in self.validation_results:
            critical_issues.extend(result.critical_issues)
        
        if critical_issues:
            console.print("\nCritical Issues:")
            for issue in critical_issues[:5]:  # Show first 5
                console.print(f"  🚨 {issue}")
            
            if len(critical_issues) > 5:
                console.print(f"  ... and {len(critical_issues) - 5} more")
    
    def _display_performance_regressions(self):
        """Display performance regressions."""
        regressions = []
        for result in self.benchmark_results:
            if result.performance_regression:
                regression = result.performance_regression
                if (regression["execution_time_regression_percent"] > 10 or
                    regression["memory_regression_percent"] > 20):
                    regressions.append((result, regression))
        
        if regressions:
            console.print("\nPerformance Regressions:")
            for result, regression in regressions[:3]:  # Show first 3
                console.print(f"  📉 {result.component}.{result.test_name}: "
                            f"Time: {regression['execution_time_regression_percent']:+.1f}%, "
                            f"Memory: {regression['memory_regression_percent']:+.1f}%")
    
    def generate_html_report(self, summary: TestExecutionSummary) -> Path:
        """Generate a comprehensive HTML report."""
        html_content = self._create_html_report(summary)
        
        report_file = self.output_dir / f"integration_test_report_{int(time.time())}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {report_file}")
        return report_file
    
    def _create_html_report(self, summary: TestExecutionSummary) -> str:
        """Create HTML content for the report."""
        # This is a simplified HTML template
        # In a real implementation, you'd use a proper templating engine
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Integration Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .status-success {{ color: green; }}
                .status-failure {{ color: red; }}
                .status-warning {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 Comprehensive Integration Testing Report</h1>
                <p>Generated: {summary.timestamp}</p>
                <p>Overall Status: <span class="status-{summary.overall_status.replace('_', '-')}">{summary.overall_status.upper()}</span></p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <strong>Total Tests:</strong> {summary.total_tests}
                </div>
                <div class="metric">
                    <strong>Duration:</strong> {summary.total_duration_ms:.1f}ms
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {summary.overall_success_rate:.1%}
                </div>
            </div>
            
            <h2>Test Categories</h2>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Success Rate</th>
                </tr>
                <tr>
                    <td>Integration Tests</td>
                    <td>{summary.integration_tests.get('total_tests', 0)}</td>
                    <td>{summary.integration_tests.get('passed_tests', 0)}</td>
                    <td>{summary.integration_tests.get('failed_tests', 0)}</td>
                    <td>{summary.integration_tests.get('average_success_rate', 0):.1%}</td>
                </tr>
                <tr>
                    <td>Performance Tests</td>
                    <td>{summary.performance_tests.get('total_benchmarks', 0)}</td>
                    <td>{summary.performance_tests.get('successful_benchmarks', 0)}</td>
                    <td>{summary.performance_tests.get('regressions', 0)}</td>
                    <td>{(summary.performance_tests.get('successful_benchmarks', 0) / max(summary.performance_tests.get('total_benchmarks', 1), 1)):.1%}</td>
                </tr>
                <tr>
                    <td>Validation Tests</td>
                    <td>{summary.validation_tests.get('total_validations', 0)}</td>
                    <td>{summary.validation_tests.get('passed_validations', 0)}</td>
                    <td>{summary.validation_tests.get('failed_validations', 0)}</td>
                    <td>{(summary.validation_tests.get('passed_validations', 0) / max(summary.validation_tests.get('total_validations', 1), 1)):.1%}</td>
                </tr>
                <tr>
                    <td>Workflow Tests</td>
                    <td>{summary.workflow_tests.get('total_workflows', 0)}</td>
                    <td>{summary.workflow_tests.get('completed_workflows', 0)}</td>
                    <td>{summary.workflow_tests.get('failed_workflows', 0)}</td>
                    <td>{summary.workflow_tests.get('average_success_rate', 0):.1%}</td>
                </tr>
            </table>
            
            <h2>Detailed Results</h2>
            <p>Detailed test results and logs are available in the JSON report.</p>
            
        </body>
        </html>
        """
        
        return html_template
    
    def generate_json_report(self, summary: TestExecutionSummary) -> Path:
        """Generate a detailed JSON report with all test data."""
        report_data = {
            "summary": asdict(summary),
            "integration_suites": [asdict(suite) for suite in self.integration_suites],
            "benchmark_results": [asdict(result) for result in self.benchmark_results],
            "validation_results": [asdict(result) for result in self.validation_results],
            "workflow_scenarios": [asdict(scenario) for scenario in self.workflow_scenarios]
        }
        
        report_file = self.output_dir / f"integration_test_data_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {report_file}")
        return report_file
    
    def generate_markdown_report(self, summary: TestExecutionSummary) -> Path:
        """Generate a markdown report suitable for documentation."""
        markdown_content = self._create_markdown_report(summary)
        
        report_file = self.output_dir / f"integration_test_report_{int(time.time())}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown report generated: {report_file}")
        return report_file
    
    def _create_markdown_report(self, summary: TestExecutionSummary) -> str:
        """Create markdown content for the report."""
        lines = [
            "# 🧪 Comprehensive Integration Testing Report",
            "",
            f"**Generated:** {summary.timestamp}",
            f"**Overall Status:** {summary.overall_status.upper()}",
            f"**Total Duration:** {summary.total_duration_ms:.1f}ms",
            f"**Overall Success Rate:** {summary.overall_success_rate:.1%}",
            "",
            "## Executive Summary",
            "",
            f"This report covers comprehensive integration testing across all system components including:",
            "- Graph-Sitter code analysis engine",
            "- Codegen SDK integration",
            "- Contexten orchestration (when available)",
            "- Cross-component validation",
            "- Performance benchmarking",
            "- End-to-end workflow testing",
            "",
            f"**Total Tests Executed:** {summary.total_tests}",
            "",
            "## Test Category Results",
            "",
            "| Category | Total | Passed | Failed | Success Rate |",
            "|----------|-------|--------|--------|--------------|",
        ]
        
        # Add table rows
        categories = [
            ("Integration Tests", summary.integration_tests),
            ("Performance Tests", summary.performance_tests),
            ("Validation Tests", summary.validation_tests),
            ("Workflow Tests", summary.workflow_tests)
        ]
        
        for name, data in categories:
            if name == "Performance Tests":
                total = data.get("total_benchmarks", 0)
                passed = data.get("successful_benchmarks", 0)
                failed = data.get("regressions", 0)
            elif name == "Workflow Tests":
                total = data.get("total_workflows", 0)
                passed = data.get("completed_workflows", 0)
                failed = data.get("failed_workflows", 0)
            else:
                total = data.get("total_tests", 0) or data.get("total_validations", 0)
                passed = data.get("passed_tests", 0) or data.get("passed_validations", 0)
                failed = data.get("failed_tests", 0) or data.get("failed_validations", 0)
            
            success_rate = passed / max(total, 1)
            lines.append(f"| {name} | {total} | {passed} | {failed} | {success_rate:.1%} |")
        
        lines.extend([
            "",
            "## Key Findings",
            "",
        ])
        
        # Add key findings based on results
        if summary.overall_status == "success":
            lines.append("✅ All tests passed successfully with no critical issues detected.")
        elif summary.overall_status == "critical_failure":
            lines.append("🚨 Critical failures detected that require immediate attention.")
        elif summary.validation_tests.get("critical_issues", 0) > 0:
            lines.append(f"🚨 {summary.validation_tests['critical_issues']} critical validation issues found.")
        
        if summary.performance_tests.get("regressions", 0) > 0:
            lines.append(f"📉 {summary.performance_tests['regressions']} performance regressions detected.")
        
        lines.extend([
            "",
            "## Recommendations",
            "",
        ])
        
        # Add recommendations based on results
        if summary.overall_status in ["failure", "critical_failure"]:
            lines.append("1. Address critical failures before proceeding with deployment")
            lines.append("2. Review failed test logs for specific error details")
        
        if summary.performance_tests.get("regressions", 0) > 0:
            lines.append("3. Investigate performance regressions and optimize affected components")
        
        if summary.validation_tests.get("error_issues", 0) > 5:
            lines.append("4. Review validation errors for potential integration issues")
        
        lines.extend([
            "",
            "---",
            "",
            "*This report was generated by the Comprehensive Integration Testing Framework*"
        ])
        
        return "\n".join(lines)
    
    def generate_all_reports(self) -> Dict[str, Path]:
        """Generate all report formats and return file paths."""
        summary = self.generate_summary()
        
        # Display dashboard
        self.display_summary_dashboard(summary)
        
        # Generate all report formats
        reports = {
            "html": self.generate_html_report(summary),
            "json": self.generate_json_report(summary),
            "markdown": self.generate_markdown_report(summary)
        }
        
        console.print(f"\n📄 Reports generated in: {self.output_dir}")
        for format_name, file_path in reports.items():
            console.print(f"   {format_name.upper()}: {file_path.name}")
        
        return reports

