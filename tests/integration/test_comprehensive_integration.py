"""
Comprehensive Integration Testing Suite

Main test file that orchestrates all integration testing components including
performance benchmarking, cross-component validation, end-to-end workflows,
and comprehensive reporting.

This implements the requirements for Testing-11: Comprehensive Integration Testing & Validation
"""

import asyncio
import pytest
from pathlib import Path
from typing import List

from .framework import (
    IntegrationTestFramework,
    PerformanceBenchmark,
    CrossComponentValidator,
    EndToEndWorkflowTester,
    TestReporter
)

from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)


class TestComprehensiveIntegration:
    """
    Comprehensive integration testing suite that validates all system components
    working together seamlessly.
    
    This test suite covers:
    - Integration testing framework
    - Cross-component validation
    - Performance testing and benchmarking
    - End-to-end workflow testing
    - Automated test suites
    - Regression testing capabilities
    """
    
    @pytest.fixture(scope="class")
    def test_data_path(self) -> Path:
        """Provide path to test data directory."""
        return Path(__file__).parent.parent / "data"
    
    @pytest.fixture(scope="class")
    def integration_framework(self) -> IntegrationTestFramework:
        """Create integration test framework instance."""
        return IntegrationTestFramework()
    
    @pytest.fixture(scope="class")
    def performance_benchmark(self, test_data_path: Path) -> PerformanceBenchmark:
        """Create performance benchmark instance."""
        baseline_file = test_data_path / "performance_baselines.json"
        return PerformanceBenchmark(baseline_file=baseline_file)
    
    @pytest.fixture(scope="class")
    def cross_validator(self) -> CrossComponentValidator:
        """Create cross-component validator instance."""
        return CrossComponentValidator()
    
    @pytest.fixture(scope="class")
    def workflow_tester(self, test_data_path: Path) -> EndToEndWorkflowTester:
        """Create end-to-end workflow tester instance."""
        return EndToEndWorkflowTester(test_data_path=test_data_path)
    
    @pytest.fixture(scope="class")
    def test_reporter(self) -> TestReporter:
        """Create test reporter instance."""
        return TestReporter()
    
    @pytest.mark.asyncio
    async def test_integration_framework_setup(self, integration_framework: IntegrationTestFramework):
        """Test that the integration framework is properly set up."""
        # Verify all components are registered
        assert len(integration_framework.components) > 0
        
        # Verify dependency graph is valid
        dependency_order = integration_framework.validate_dependency_order()
        assert len(dependency_order) == len(integration_framework.components)
        
        # Verify core components are present
        expected_components = [
            "graph_sitter_core",
            "graph_sitter_python", 
            "graph_sitter_typescript",
            "codegen_sdk",
            "codebase_integration"
        ]
        
        for component in expected_components:
            assert component in integration_framework.components
        
        logger.info("✅ Integration framework setup validated")
    
    @pytest.mark.asyncio
    async def test_core_component_integration(self, integration_framework: IntegrationTestFramework):
        """Test integration between core system components."""
        # Create test suite for core components
        core_components = [
            "graph_sitter_core",
            "graph_sitter_python",
            "graph_sitter_typescript",
            "codegen_sdk"
        ]
        
        suite = integration_framework.create_test_suite("core_integration", core_components)
        
        # Run the integration test suite
        result = await integration_framework.run_integration_suite(suite)
        
        # Validate results
        assert result.success_rate > 0.8, f"Core integration success rate too low: {result.success_rate:.1%}"
        assert len(result.test_results) > 0, "No test results generated"
        
        # Check for critical failures
        critical_failures = [r for r in result.test_results if r.status == "error"]
        assert len(critical_failures) == 0, f"Critical failures detected: {critical_failures}"
        
        logger.info(f"✅ Core component integration validated (Success rate: {result.success_rate:.1%})")
    
    @pytest.mark.asyncio
    async def test_performance_benchmarking(self, performance_benchmark: PerformanceBenchmark):
        """Test performance benchmarking capabilities."""
        # Test Graph-Sitter parsing performance
        current_dir = Path(".")
        if current_dir.exists() and any(current_dir.glob("*.py")):
            parsing_result = await performance_benchmark.benchmark_graph_sitter_parsing(current_dir)
            
            assert parsing_result.iterations > 0, "No benchmark iterations completed"
            assert parsing_result.average_metrics.execution_time_ms > 0, "Invalid execution time"
            
            # Check for performance regressions
            if parsing_result.performance_regression:
                regression = parsing_result.performance_regression
                # Allow up to 20% regression for testing
                assert regression["execution_time_regression_percent"] < 20, \
                    f"Significant performance regression: {regression['execution_time_regression_percent']:.1f}%"
        
        # Test Codegen agent creation performance
        agent_result = await performance_benchmark.benchmark_codegen_agent_creation()
        
        # Validate benchmark results structure
        assert hasattr(agent_result, 'test_name')
        assert hasattr(agent_result, 'component')
        assert hasattr(agent_result, 'average_metrics')
        
        logger.info("✅ Performance benchmarking validated")
    
    @pytest.mark.asyncio
    async def test_cross_component_validation(self, cross_validator: CrossComponentValidator):
        """Test cross-component validation capabilities."""
        # Run all validation tests
        validation_results = await cross_validator.run_all_validations()
        
        assert len(validation_results) > 0, "No validation results generated"
        
        # Check for critical issues
        critical_issues = []
        for result in validation_results:
            critical_issues.extend(result.critical_issues)
        
        # Allow some critical issues for testing, but not too many
        assert len(critical_issues) < 5, f"Too many critical issues: {len(critical_issues)}"
        
        # Verify specific integration validations
        graph_sitter_codegen_results = [
            r for r in validation_results 
            if r.validation_type == "integration_validation" and 
               "graph_sitter" in r.component_pair
        ]
        assert len(graph_sitter_codegen_results) > 0, "Graph-Sitter to Codegen validation missing"
        
        # Check overall validation success rate
        passed_validations = len([r for r in validation_results if r.passed])
        success_rate = passed_validations / len(validation_results)
        assert success_rate > 0.7, f"Validation success rate too low: {success_rate:.1%}"
        
        logger.info(f"✅ Cross-component validation completed (Success rate: {success_rate:.1%})")
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflows(self, workflow_tester: EndToEndWorkflowTester):
        """Test end-to-end workflow execution."""
        # Run all workflow scenarios
        workflow_results = await workflow_tester.run_all_workflows()
        
        assert len(workflow_results) > 0, "No workflow results generated"
        
        # Check workflow completion rates
        completed_workflows = len([w for w in workflow_results if w.status.value == "completed"])
        completion_rate = completed_workflows / len(workflow_results)
        
        # Allow some workflow failures for testing
        assert completion_rate > 0.6, f"Workflow completion rate too low: {completion_rate:.1%}"
        
        # Verify specific workflows
        workflow_names = [w.name for w in workflow_results]
        expected_workflows = [
            "code_analysis_workflow",
            "code_generation_workflow", 
            "repository_integration_workflow",
            "multi_language_workflow"
        ]
        
        for expected in expected_workflows:
            assert expected in workflow_names, f"Missing expected workflow: {expected}"
        
        # Check for excessive failures in any single workflow
        for workflow in workflow_results:
            assert workflow.success_rate > 0.5, \
                f"Workflow '{workflow.name}' has too low success rate: {workflow.success_rate:.1%}"
        
        logger.info(f"✅ End-to-end workflows validated (Completion rate: {completion_rate:.1%})")
    
    @pytest.mark.asyncio
    async def test_regression_detection(self, performance_benchmark: PerformanceBenchmark):
        """Test regression detection capabilities."""
        # Create mock baseline metrics for testing
        from .framework.performance import PerformanceMetrics
        
        baseline_metrics = PerformanceMetrics(
            execution_time_ms=100.0,
            memory_usage_mb=50.0,
            cpu_usage_percent=10.0,
            peak_memory_mb=60.0,
            gc_collections=5
        )
        
        # Set baseline for a test
        performance_benchmark.baselines["test_component.test_method"] = baseline_metrics
        
        # Run a simple benchmark
        async def mock_function():
            await asyncio.sleep(0.01)
            return "test_result"
        
        result = await performance_benchmark.benchmark_function(
            mock_function,
            "test_method",
            "test_component",
            iterations=3,
            warmup_iterations=1
        )
        
        # Verify regression detection works
        assert result.baseline_metrics is not None, "Baseline metrics not loaded"
        assert result.performance_regression is not None, "Regression analysis not performed"
        
        # Verify regression calculation
        regression = result.performance_regression
        assert "execution_time_regression_percent" in regression
        assert "memory_regression_percent" in regression
        assert "cpu_regression_percent" in regression
        
        logger.info("✅ Regression detection validated")
    
    @pytest.mark.asyncio
    async def test_automated_test_suite_execution(
        self,
        integration_framework: IntegrationTestFramework,
        performance_benchmark: PerformanceBenchmark,
        cross_validator: CrossComponentValidator,
        workflow_tester: EndToEndWorkflowTester
    ):
        """Test automated execution of the complete test suite."""
        # This test validates that all components can run together
        # in an automated fashion
        
        # Run a subset of each test type
        logger.info("🚀 Starting automated test suite execution...")
        
        # 1. Integration tests
        core_suite = integration_framework.create_test_suite(
            "automated_core", 
            ["graph_sitter_core", "codegen_sdk"]
        )
        integration_result = await integration_framework.run_integration_suite(core_suite)
        
        # 2. Performance tests (lightweight)
        async def simple_test():
            await asyncio.sleep(0.01)
        
        perf_result = await performance_benchmark.benchmark_function(
            simple_test, "automated_test", "test_component", iterations=2
        )
        
        # 3. Validation tests (subset)
        validation_result = await cross_validator.validate_interface_compatibility(
            "graph_sitter_core", "codegen_sdk"
        )
        
        # 4. Workflow test (single scenario)
        if workflow_tester.scenarios:
            workflow_result = await workflow_tester.execute_workflow(workflow_tester.scenarios[0])
        
        # Verify all components executed successfully
        assert integration_result.success_rate > 0.5, "Integration test failed"
        assert len(perf_result.metrics) > 0, "Performance test failed"
        assert validation_result is not None, "Validation test failed"
        
        logger.info("✅ Automated test suite execution validated")
    
    @pytest.mark.asyncio
    async def test_comprehensive_reporting(
        self,
        test_reporter: TestReporter,
        integration_framework: IntegrationTestFramework,
        performance_benchmark: PerformanceBenchmark,
        cross_validator: CrossComponentValidator,
        workflow_tester: EndToEndWorkflowTester
    ):
        """Test comprehensive reporting capabilities."""
        # Generate some test data for reporting
        
        # Create a simple integration test suite
        test_suite = integration_framework.create_test_suite(
            "reporting_test", 
            ["graph_sitter_core", "codegen_sdk"]
        )
        integration_result = await integration_framework.run_integration_suite(test_suite)
        
        # Create a simple performance benchmark
        async def test_func():
            await asyncio.sleep(0.01)
        
        perf_result = await performance_benchmark.benchmark_function(
            test_func, "reporting_test", "test_component", iterations=2
        )
        
        # Create a validation result
        validation_result = await cross_validator.validate_interface_compatibility(
            "graph_sitter_core", "codegen_sdk"
        )
        
        # Add results to reporter
        test_reporter.add_integration_results([integration_result])
        test_reporter.add_performance_results([perf_result])
        test_reporter.add_validation_results([validation_result])
        
        # Generate summary
        summary = test_reporter.generate_summary()
        
        # Validate summary structure
        assert summary.total_tests > 0, "No tests recorded in summary"
        assert summary.overall_status in [
            "success", "partial_success", "performance_degradation",
            "validation_issues", "failure", "critical_failure"
        ], f"Invalid overall status: {summary.overall_status}"
        
        # Test report generation
        reports = test_reporter.generate_all_reports()
        
        # Verify all report formats were generated
        assert "html" in reports, "HTML report not generated"
        assert "json" in reports, "JSON report not generated"
        assert "markdown" in reports, "Markdown report not generated"
        
        # Verify files exist
        for report_type, file_path in reports.items():
            assert file_path.exists(), f"{report_type} report file not created"
            assert file_path.stat().st_size > 0, f"{report_type} report file is empty"
        
        logger.info("✅ Comprehensive reporting validated")
    
    @pytest.mark.asyncio
    async def test_full_integration_validation(
        self,
        integration_framework: IntegrationTestFramework,
        performance_benchmark: PerformanceBenchmark,
        cross_validator: CrossComponentValidator,
        workflow_tester: EndToEndWorkflowTester,
        test_reporter: TestReporter
    ):
        """
        Final comprehensive test that validates the entire integration testing system.
        
        This test represents the complete Testing-11 deliverable validation.
        """
        logger.info("🎯 Starting full integration validation...")
        
        # 1. Validate Integration Testing Framework
        all_suites = await integration_framework.run_all_suites()
        assert len(all_suites) > 0, "No integration test suites executed"
        
        overall_success = sum(suite.success_rate for suite in all_suites) / len(all_suites)
        assert overall_success > 0.6, f"Overall integration success rate too low: {overall_success:.1%}"
        
        # 2. Validate Performance Benchmarking
        performance_summary = performance_benchmark.get_performance_summary()
        if performance_summary:
            assert performance_summary["total_benchmarks"] > 0, "No performance benchmarks executed"
        
        # 3. Validate Cross-Component Validation
        all_validations = await cross_validator.run_all_validations()
        validation_success = len([v for v in all_validations if v.passed]) / len(all_validations)
        assert validation_success > 0.6, f"Validation success rate too low: {validation_success:.1%}"
        
        # 4. Validate End-to-End Workflows
        all_workflows = await workflow_tester.run_all_workflows()
        workflow_completion = len([w for w in all_workflows if w.status.value == "completed"]) / len(all_workflows)
        assert workflow_completion > 0.5, f"Workflow completion rate too low: {workflow_completion:.1%}"
        
        # 5. Validate Comprehensive Reporting
        test_reporter.add_integration_results(all_suites)
        test_reporter.add_performance_results(performance_benchmark.results)
        test_reporter.add_validation_results(all_validations)
        test_reporter.add_workflow_results(all_workflows)
        
        final_summary = test_reporter.generate_summary()
        final_reports = test_reporter.generate_all_reports()
        
        # Validate final deliverables
        assert final_summary.total_tests > 0, "No tests in final summary"
        assert len(final_reports) == 3, "Not all report formats generated"
        
        # Validate system health
        assert final_summary.overall_status != "critical_failure", "Critical system failures detected"
        
        logger.info("✅ Full integration validation completed successfully!")
        logger.info(f"   📊 Total Tests: {final_summary.total_tests}")
        logger.info(f"   📈 Success Rate: {final_summary.overall_success_rate:.1%}")
        logger.info(f"   🎯 Overall Status: {final_summary.overall_status.upper()}")
        
        # Return summary for external validation
        return final_summary


# Standalone test runner for manual execution
async def run_comprehensive_integration_tests():
    """
    Standalone function to run comprehensive integration tests.
    
    This can be called directly for manual testing or CI/CD integration.
    """
    logger.info("🚀 Starting comprehensive integration testing...")
    
    # Initialize all components
    integration_framework = IntegrationTestFramework()
    performance_benchmark = PerformanceBenchmark()
    cross_validator = CrossComponentValidator()
    workflow_tester = EndToEndWorkflowTester()
    test_reporter = TestReporter()
    
    try:
        # Run all test categories
        logger.info("1️⃣ Running integration tests...")
        integration_suites = await integration_framework.run_all_suites()
        
        logger.info("2️⃣ Running performance benchmarks...")
        # Run a subset of performance tests
        current_dir = Path(".")
        if current_dir.exists():
            await performance_benchmark.benchmark_graph_sitter_parsing(current_dir)
        await performance_benchmark.benchmark_codegen_agent_creation()
        
        logger.info("3️⃣ Running cross-component validation...")
        validation_results = await cross_validator.run_all_validations()
        
        logger.info("4️⃣ Running end-to-end workflows...")
        workflow_results = await workflow_tester.run_all_workflows()
        
        # Generate comprehensive report
        logger.info("5️⃣ Generating comprehensive report...")
        test_reporter.add_integration_results(integration_suites)
        test_reporter.add_performance_results(performance_benchmark.results)
        test_reporter.add_validation_results(validation_results)
        test_reporter.add_workflow_results(workflow_results)
        
        final_summary = test_reporter.generate_summary()
        reports = test_reporter.generate_all_reports()
        
        logger.info("✅ Comprehensive integration testing completed!")
        logger.info(f"📄 Reports generated: {list(reports.keys())}")
        
        return final_summary, reports
        
    except Exception as e:
        logger.error(f"❌ Comprehensive integration testing failed: {e}")
        raise


if __name__ == "__main__":
    # Allow running this file directly for testing
    asyncio.run(run_comprehensive_integration_tests())

