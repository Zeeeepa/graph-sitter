"""
Comprehensive Integration Test Suite Runner

Orchestrates all integration tests and generates comprehensive reports
for system validation and quality assurance.
"""

import pytest
import time
import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    status: str  # success, failed, skipped
    duration: float
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[str]] = None


@dataclass
class TestSuiteReport:
    """Comprehensive test suite report."""
    suite_name: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration: float
    success_rate: float
    test_results: List[TestResult]
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    recommendations: List[str]


class IntegrationTestSuiteRunner:
    """Main test suite runner for integration testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.test_results: List[TestResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration for test suite."""
        return {
            "test_modules": [
                "test_module_integration",
                "test_database_integration", 
                "test_external_library_integration",
                "test_dashboard_ui_integration",
                "test_cicd_pipeline_integration",
                "test_end_to_end_workflows"
            ],
            "parallel_execution": True,
            "max_workers": 4,
            "timeout_per_test": 300,  # 5 minutes
            "retry_failed_tests": True,
            "max_retries": 2,
            "generate_artifacts": True,
            "performance_monitoring": True,
            "quality_gates": {
                "min_success_rate": 0.95,
                "max_avg_duration": 120,
                "max_memory_usage_mb": 1024
            }
        }
    
    def run_full_suite(self) -> TestSuiteReport:
        """Run the complete integration test suite."""
        print("🚀 Starting Comprehensive Integration Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        try:
            # Run all test modules
            if self.config["parallel_execution"]:
                self._run_tests_parallel()
            else:
                self._run_tests_sequential()
            
            # Generate comprehensive report
            report = self._generate_report()
            
            # Check quality gates
            self._check_quality_gates(report)
            
            # Generate artifacts
            if self.config["generate_artifacts"]:
                self._generate_artifacts(report)
            
            return report
            
        finally:
            self.end_time = time.time()
    
    def _run_tests_parallel(self):
        """Run tests in parallel for faster execution."""
        print("🔄 Running tests in parallel...")
        
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            futures = {}
            
            for module in self.config["test_modules"]:
                future = executor.submit(self._run_test_module, module)
                futures[future] = module
            
            for future in as_completed(futures):
                module = futures[future]
                try:
                    results = future.result()
                    self.test_results.extend(results)
                    print(f"✅ Completed {module}: {len(results)} tests")
                except Exception as e:
                    print(f"❌ Failed {module}: {e}")
                    self.test_results.append(TestResult(
                        test_name=f"{module}_suite",
                        status="failed",
                        duration=0,
                        error_message=str(e)
                    ))
    
    def _run_tests_sequential(self):
        """Run tests sequentially."""
        print("🔄 Running tests sequentially...")
        
        for module in self.config["test_modules"]:
            print(f"Running {module}...")
            try:
                results = self._run_test_module(module)
                self.test_results.extend(results)
                print(f"✅ Completed {module}: {len(results)} tests")
            except Exception as e:
                print(f"❌ Failed {module}: {e}")
                self.test_results.append(TestResult(
                    test_name=f"{module}_suite",
                    status="failed", 
                    duration=0,
                    error_message=str(e)
                ))
    
    def _run_test_module(self, module_name: str) -> List[TestResult]:
        """Run a specific test module."""
        module_path = f"tests/integration/system_validation/{module_name}.py"
        
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Test module not found: {module_path}")
        
        # Run pytest for the specific module
        cmd = [
            sys.executable, "-m", "pytest",
            module_path,
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file=/tmp/{module_name}_report.json"
        ]
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config["timeout_per_test"]
        )
        duration = time.time() - start_time
        
        # Parse pytest results
        return self._parse_pytest_results(module_name, result, duration)
    
    def _parse_pytest_results(self, module_name: str, result: subprocess.CompletedProcess, duration: float) -> List[TestResult]:
        """Parse pytest results into TestResult objects."""
        test_results = []
        
        # Try to load JSON report if available
        json_report_path = f"/tmp/{module_name}_report.json"
        if os.path.exists(json_report_path):
            try:
                with open(json_report_path, 'r') as f:
                    report_data = json.load(f)
                
                for test in report_data.get("tests", []):
                    test_results.append(TestResult(
                        test_name=test["nodeid"],
                        status="success" if test["outcome"] == "passed" else "failed",
                        duration=test.get("duration", 0),
                        error_message=test.get("call", {}).get("longrepr") if test["outcome"] == "failed" else None
                    ))
                
                os.unlink(json_report_path)  # Cleanup
                
            except Exception as e:
                print(f"Warning: Could not parse JSON report for {module_name}: {e}")
        
        # Fallback: parse from stdout/stderr
        if not test_results:
            if result.returncode == 0:
                test_results.append(TestResult(
                    test_name=f"{module_name}_suite",
                    status="success",
                    duration=duration
                ))
            else:
                test_results.append(TestResult(
                    test_name=f"{module_name}_suite",
                    status="failed",
                    duration=duration,
                    error_message=result.stderr or result.stdout
                ))
        
        return test_results
    
    def _generate_report(self) -> TestSuiteReport:
        """Generate comprehensive test suite report."""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.status == "success"])
        failed_tests = len([r for r in self.test_results if r.status == "failed"])
        skipped_tests = len([r for r in self.test_results if r.status == "skipped"])
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics()
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(success_rate, performance_metrics, quality_metrics)
        
        return TestSuiteReport(
            suite_name="Integration Test Suite",
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            total_duration=total_duration,
            success_rate=success_rate,
            test_results=self.test_results,
            performance_metrics=performance_metrics,
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics from test results."""
        durations = [r.duration for r in self.test_results if r.duration > 0]
        
        if not durations:
            return {}
        
        return {
            "average_test_duration": sum(durations) / len(durations),
            "max_test_duration": max(durations),
            "min_test_duration": min(durations),
            "total_execution_time": sum(durations),
            "tests_per_minute": len(durations) / (sum(durations) / 60) if sum(durations) > 0 else 0
        }
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate quality metrics from test results."""
        return {
            "test_coverage": self._estimate_test_coverage(),
            "code_quality_score": self._calculate_code_quality_score(),
            "reliability_score": self._calculate_reliability_score(),
            "maintainability_score": self._calculate_maintainability_score()
        }
    
    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage based on test modules."""
        # This is a simplified estimation
        expected_modules = [
            "module_integration",
            "database_integration", 
            "external_library_integration",
            "dashboard_ui_integration",
            "cicd_pipeline_integration",
            "end_to_end_workflows"
        ]
        
        covered_modules = len([m for m in self.config["test_modules"] if any(em in m for em in expected_modules)])
        return covered_modules / len(expected_modules)
    
    def _calculate_code_quality_score(self) -> float:
        """Calculate code quality score based on test results."""
        # Simplified scoring based on test success rate and error types
        success_rate = len([r for r in self.test_results if r.status == "success"]) / len(self.test_results)
        
        # Penalty for certain types of errors
        error_penalty = 0
        for result in self.test_results:
            if result.error_message:
                if "timeout" in result.error_message.lower():
                    error_penalty += 0.1
                elif "memory" in result.error_message.lower():
                    error_penalty += 0.15
                elif "connection" in result.error_message.lower():
                    error_penalty += 0.05
        
        return max(0, success_rate - error_penalty)
    
    def _calculate_reliability_score(self) -> float:
        """Calculate reliability score based on test stability."""
        # This would typically involve running tests multiple times
        # For now, use success rate as a proxy
        return len([r for r in self.test_results if r.status == "success"]) / len(self.test_results)
    
    def _calculate_maintainability_score(self) -> float:
        """Calculate maintainability score based on test structure."""
        # Simplified scoring based on test organization
        return 0.8  # Placeholder - would analyze test code structure
    
    def _generate_recommendations(self, success_rate: float, performance_metrics: Dict[str, Any], quality_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if success_rate < 0.95:
            recommendations.append("🔴 Success rate below 95%. Review and fix failing tests.")
        
        if performance_metrics.get("average_test_duration", 0) > 60:
            recommendations.append("🟡 Average test duration exceeds 60 seconds. Consider optimizing slow tests.")
        
        if quality_metrics.get("test_coverage", 0) < 0.8:
            recommendations.append("🟡 Test coverage below 80%. Add more comprehensive tests.")
        
        if quality_metrics.get("reliability_score", 0) < 0.9:
            recommendations.append("🔴 Reliability score below 90%. Investigate test flakiness.")
        
        # Add positive recommendations
        if success_rate >= 0.98:
            recommendations.append("✅ Excellent success rate! System is highly stable.")
        
        if performance_metrics.get("average_test_duration", 0) < 30:
            recommendations.append("✅ Great performance! Tests execute quickly.")
        
        return recommendations
    
    def _check_quality_gates(self, report: TestSuiteReport):
        """Check quality gates and fail if not met."""
        gates = self.config["quality_gates"]
        
        if report.success_rate < gates["min_success_rate"]:
            print(f"❌ Quality gate failed: Success rate {report.success_rate:.2%} < {gates['min_success_rate']:.2%}")
            sys.exit(1)
        
        avg_duration = report.performance_metrics.get("average_test_duration", 0)
        if avg_duration > gates["max_avg_duration"]:
            print(f"❌ Quality gate failed: Average duration {avg_duration:.1f}s > {gates['max_avg_duration']}s")
            sys.exit(1)
        
        print("✅ All quality gates passed!")
    
    def _generate_artifacts(self, report: TestSuiteReport):
        """Generate test artifacts and reports."""
        artifacts_dir = "test_artifacts"
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # Generate JSON report
        json_report_path = os.path.join(artifacts_dir, "integration_test_report.json")
        with open(json_report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = os.path.join(artifacts_dir, "integration_test_report.html")
        self._generate_html_report(report, html_report_path)
        
        # Generate CSV summary
        csv_report_path = os.path.join(artifacts_dir, "test_results.csv")
        self._generate_csv_report(report, csv_report_path)
        
        print(f"📊 Test artifacts generated in {artifacts_dir}/")
    
    def _generate_html_report(self, report: TestSuiteReport, output_path: str):
        """Generate HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Integration Test Report</h1>
        <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Suite: {report.suite_name}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Test Results</h3>
            <p>Total: {report.total_tests}</p>
            <p class="success">Successful: {report.successful_tests}</p>
            <p class="failed">Failed: {report.failed_tests}</p>
            <p>Success Rate: {report.success_rate:.2%}</p>
        </div>
        <div class="metric">
            <h3>Performance</h3>
            <p>Total Duration: {report.total_duration:.1f}s</p>
            <p>Avg Test Duration: {report.performance_metrics.get('average_test_duration', 0):.1f}s</p>
            <p>Tests/Minute: {report.performance_metrics.get('tests_per_minute', 0):.1f}</p>
        </div>
        <div class="metric">
            <h3>Quality</h3>
            <p>Coverage: {report.quality_metrics.get('test_coverage', 0):.2%}</p>
            <p>Reliability: {report.quality_metrics.get('reliability_score', 0):.2%}</p>
            <p>Code Quality: {report.quality_metrics.get('code_quality_score', 0):.2%}</p>
        </div>
    </div>
    
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
            {''.join(f'<li>{rec}</li>' for rec in report.recommendations)}
        </ul>
    </div>
    
    <h3>Detailed Test Results</h3>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Duration (s)</th>
            <th>Error Message</th>
        </tr>
        {''.join(f'''
        <tr>
            <td>{result.test_name}</td>
            <td class="{result.status}">{result.status}</td>
            <td>{result.duration:.2f}</td>
            <td>{result.error_message or ''}</td>
        </tr>
        ''' for result in report.test_results)}
    </table>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_csv_report(self, report: TestSuiteReport, output_path: str):
        """Generate CSV test report."""
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Test Name', 'Status', 'Duration', 'Error Message'])
            
            for result in report.test_results:
                writer.writerow([
                    result.test_name,
                    result.status,
                    result.duration,
                    result.error_message or ''
                ])
    
    def print_summary(self, report: TestSuiteReport):
        """Print test summary to console."""
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"📊 Total Tests: {report.total_tests}")
        print(f"✅ Successful: {report.successful_tests}")
        print(f"❌ Failed: {report.failed_tests}")
        print(f"⏭️  Skipped: {report.skipped_tests}")
        print(f"📈 Success Rate: {report.success_rate:.2%}")
        print(f"⏱️  Total Duration: {report.total_duration:.1f}s")
        
        if report.recommendations:
            print("\n🔍 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  {rec}")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point for running the integration test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run integration test suite")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per test in seconds")
    parser.add_argument("--no-artifacts", action="store_true", help="Skip artifact generation")
    parser.add_argument("--config", type=str, help="Path to custom config file")
    
    args = parser.parse_args()
    
    # Load custom config if provided
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override config with command line arguments
    if config is None:
        config = {}
    
    config.update({
        "parallel_execution": args.parallel,
        "max_workers": args.workers,
        "timeout_per_test": args.timeout,
        "generate_artifacts": not args.no_artifacts
    })
    
    # Run test suite
    runner = IntegrationTestSuiteRunner(config)
    report = runner.run_full_suite()
    runner.print_summary(report)
    
    # Exit with appropriate code
    if report.success_rate < 1.0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

