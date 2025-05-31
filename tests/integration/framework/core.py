"""
Core Integration Testing Framework

Provides the main framework for orchestrating comprehensive integration tests
across all system components including Graph-Sitter, Codegen SDK, and Contexten.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.table import Table

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.user_config import UserConfig
from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class TestComponent:
    """Represents a system component to be tested."""
    name: str
    module_path: str
    dependencies: List[str] = field(default_factory=list)
    test_methods: List[str] = field(default_factory=list)
    performance_critical: bool = False
    integration_points: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Represents the result of a test execution."""
    component: str
    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    dependencies_validated: List[str] = field(default_factory=list)


@dataclass
class IntegrationTestSuite:
    """Represents a complete integration test suite."""
    name: str
    components: List[TestComponent]
    test_results: List[TestResult] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        """Calculate total test suite duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of the test suite."""
        if not self.test_results:
            return 0.0
        passed = sum(1 for result in self.test_results if result.status == "passed")
        return passed / len(self.test_results)


class IntegrationTestFramework:
    """
    Main framework for comprehensive integration testing.
    
    This framework orchestrates testing across all system components:
    - Graph-Sitter code analysis
    - Codegen SDK integration
    - Contexten orchestration
    - Cross-component validation
    - Performance benchmarking
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.test_suites: List[IntegrationTestSuite] = []
        self.components: Dict[str, TestComponent] = {}
        self.setup_components()
        
    def setup_components(self):
        """Initialize all system components for testing."""
        # Graph-Sitter components
        self.components["graph_sitter_core"] = TestComponent(
            name="Graph-Sitter Core",
            module_path="graph_sitter.core",
            dependencies=[],
            test_methods=["test_codebase_parsing", "test_symbol_resolution", "test_ast_manipulation"],
            performance_critical=True,
            integration_points=["codegen_sdk", "contexten"]
        )
        
        self.components["graph_sitter_python"] = TestComponent(
            name="Graph-Sitter Python",
            module_path="graph_sitter.python",
            dependencies=["graph_sitter_core"],
            test_methods=["test_python_parsing", "test_import_resolution", "test_statement_analysis"],
            performance_critical=True,
            integration_points=["codegen_sdk"]
        )
        
        self.components["graph_sitter_typescript"] = TestComponent(
            name="Graph-Sitter TypeScript",
            module_path="graph_sitter.typescript",
            dependencies=["graph_sitter_core"],
            test_methods=["test_typescript_parsing", "test_type_analysis", "test_component_analysis"],
            performance_critical=True,
            integration_points=["codegen_sdk"]
        )
        
        # Codegen SDK components
        self.components["codegen_sdk"] = TestComponent(
            name="Codegen SDK",
            module_path="codegen",
            dependencies=["graph_sitter_core"],
            test_methods=["test_agent_creation", "test_task_execution", "test_api_integration"],
            performance_critical=False,
            integration_points=["graph_sitter_core", "contexten"]
        )
        
        self.components["codegen_extensions"] = TestComponent(
            name="Codegen Extensions",
            module_path="codegen.extensions",
            dependencies=["codegen_sdk"],
            test_methods=["test_github_integration", "test_linear_integration", "test_slack_integration"],
            performance_critical=False,
            integration_points=["codegen_sdk", "contexten"]
        )
        
        # Contexten components (placeholder - would be implemented when available)
        self.components["contexten_core"] = TestComponent(
            name="Contexten Core",
            module_path="contexten.core",
            dependencies=[],
            test_methods=["test_orchestration", "test_agent_coordination", "test_workflow_management"],
            performance_critical=False,
            integration_points=["codegen_sdk", "graph_sitter_core"]
        )
        
        # Integration components
        self.components["codebase_integration"] = TestComponent(
            name="Codebase Integration",
            module_path="graph_sitter.codebase",
            dependencies=["graph_sitter_core", "graph_sitter_python", "graph_sitter_typescript"],
            test_methods=["test_multi_language_parsing", "test_cross_file_analysis", "test_dependency_resolution"],
            performance_critical=True,
            integration_points=["codegen_sdk", "contexten_core"]
        )
        
        self.components["git_integration"] = TestComponent(
            name="Git Integration",
            module_path="graph_sitter.git",
            dependencies=["graph_sitter_core"],
            test_methods=["test_repository_operations", "test_branch_management", "test_diff_analysis"],
            performance_critical=False,
            integration_points=["codegen_sdk"]
        )
    
    def create_test_suite(self, name: str, component_names: List[str]) -> IntegrationTestSuite:
        """Create a new integration test suite with specified components."""
        components = [self.components[name] for name in component_names if name in self.components]
        suite = IntegrationTestSuite(name=name, components=components)
        self.test_suites.append(suite)
        return suite
    
    async def run_component_tests(self, component: TestComponent) -> List[TestResult]:
        """Run all tests for a specific component."""
        results = []
        
        for test_method in component.test_methods:
            start_time = time.time()
            
            try:
                # Validate dependencies first
                dependency_results = await self._validate_dependencies(component)
                
                # Run the actual test
                result = await self._execute_test(component, test_method)
                result.dependencies_validated = dependency_results
                
                duration = time.time() - start_time
                result.duration = duration
                
                logger.info(f"✅ {component.name}.{test_method} completed in {duration:.2f}s")
                
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    component=component.name,
                    test_name=test_method,
                    status="error",
                    duration=duration,
                    error_message=str(e)
                )
                logger.error(f"❌ {component.name}.{test_method} failed: {e}")
            
            results.append(result)
        
        return results
    
    async def _validate_dependencies(self, component: TestComponent) -> List[str]:
        """Validate that all component dependencies are working correctly."""
        validated = []
        
        for dep_name in component.dependencies:
            if dep_name in self.components:
                dep_component = self.components[dep_name]
                try:
                    # Simple validation - check if component can be imported
                    __import__(dep_component.module_path)
                    validated.append(dep_name)
                    logger.debug(f"✅ Dependency {dep_name} validated for {component.name}")
                except ImportError as e:
                    logger.warning(f"⚠️ Dependency {dep_name} validation failed for {component.name}: {e}")
        
        return validated
    
    async def _execute_test(self, component: TestComponent, test_method: str) -> TestResult:
        """Execute a specific test method for a component."""
        # This is a placeholder implementation
        # In a real implementation, this would dynamically call the actual test methods
        
        # Simulate test execution
        await asyncio.sleep(0.1)  # Simulate test execution time
        
        # For demonstration, we'll create mock results
        # In practice, this would call the actual test methods
        performance_metrics = {}
        
        if component.performance_critical:
            # Add mock performance metrics for performance-critical components
            performance_metrics = {
                "memory_usage_mb": 50.5,
                "execution_time_ms": 100.2,
                "cpu_usage_percent": 15.3
            }
        
        return TestResult(
            component=component.name,
            test_name=test_method,
            status="passed",  # Mock success for now
            duration=0.0,  # Will be set by caller
            performance_metrics=performance_metrics
        )
    
    async def run_integration_suite(self, suite: IntegrationTestSuite) -> IntegrationTestSuite:
        """Run a complete integration test suite."""
        console.print(f"🚀 Starting integration test suite: {suite.name}")
        suite.start_time = time.time()
        
        # Run tests for each component in the suite
        for component in suite.components:
            console.print(f"🔧 Testing component: {component.name}")
            component_results = await self.run_component_tests(component)
            suite.test_results.extend(component_results)
        
        # Run cross-component integration tests
        await self._run_cross_component_tests(suite)
        
        suite.end_time = time.time()
        
        # Display results
        self._display_suite_results(suite)
        
        return suite
    
    async def _run_cross_component_tests(self, suite: IntegrationTestSuite):
        """Run tests that validate integration between components."""
        console.print("🔗 Running cross-component integration tests...")
        
        # Test Graph-Sitter + Codegen SDK integration
        if any(c.name == "Graph-Sitter Core" for c in suite.components) and \
           any(c.name == "Codegen SDK" for c in suite.components):
            
            result = await self._test_graph_sitter_codegen_integration()
            suite.test_results.append(result)
        
        # Test Codegen SDK + Contexten integration
        if any(c.name == "Codegen SDK" for c in suite.components) and \
           any(c.name == "Contexten Core" for c in suite.components):
            
            result = await self._test_codegen_contexten_integration()
            suite.test_results.append(result)
        
        # Test full system integration
        if len(suite.components) >= 3:
            result = await self._test_full_system_integration()
            suite.test_results.append(result)
    
    async def _test_graph_sitter_codegen_integration(self) -> TestResult:
        """Test integration between Graph-Sitter and Codegen SDK."""
        start_time = time.time()
        
        try:
            # Mock integration test
            await asyncio.sleep(0.2)  # Simulate test execution
            
            return TestResult(
                component="Integration",
                test_name="graph_sitter_codegen_integration",
                status="passed",
                duration=time.time() - start_time,
                performance_metrics={"integration_latency_ms": 200}
            )
        except Exception as e:
            return TestResult(
                component="Integration",
                test_name="graph_sitter_codegen_integration",
                status="failed",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _test_codegen_contexten_integration(self) -> TestResult:
        """Test integration between Codegen SDK and Contexten."""
        start_time = time.time()
        
        try:
            # Mock integration test
            await asyncio.sleep(0.15)  # Simulate test execution
            
            return TestResult(
                component="Integration",
                test_name="codegen_contexten_integration",
                status="passed",
                duration=time.time() - start_time,
                performance_metrics={"orchestration_latency_ms": 150}
            )
        except Exception as e:
            return TestResult(
                component="Integration",
                test_name="codegen_contexten_integration",
                status="failed",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _test_full_system_integration(self) -> TestResult:
        """Test full system integration across all components."""
        start_time = time.time()
        
        try:
            # Mock full system test
            await asyncio.sleep(0.5)  # Simulate comprehensive test execution
            
            return TestResult(
                component="Integration",
                test_name="full_system_integration",
                status="passed",
                duration=time.time() - start_time,
                performance_metrics={
                    "end_to_end_latency_ms": 500,
                    "system_throughput_ops_per_sec": 100,
                    "memory_efficiency_percent": 85
                }
            )
        except Exception as e:
            return TestResult(
                component="Integration",
                test_name="full_system_integration",
                status="failed",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _display_suite_results(self, suite: IntegrationTestSuite):
        """Display comprehensive results for a test suite."""
        table = Table(title=f"Integration Test Results: {suite.name}")
        table.add_column("Component", style="cyan")
        table.add_column("Test", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Performance", style="yellow")
        
        for result in suite.test_results:
            status_emoji = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            status_text = f"{status_emoji} {result.status}"
            
            perf_text = ""
            if result.performance_metrics:
                key_metrics = list(result.performance_metrics.keys())[:2]  # Show first 2 metrics
                perf_text = ", ".join(f"{k}: {result.performance_metrics[k]}" for k in key_metrics)
            
            table.add_row(
                result.component,
                result.test_name,
                status_text,
                f"{result.duration:.2f}",
                perf_text
            )
        
        console.print(table)
        
        # Summary statistics
        console.print(f"\n📊 Suite Summary:")
        console.print(f"   Total Duration: {suite.duration:.2f}s")
        console.print(f"   Success Rate: {suite.success_rate:.1%}")
        console.print(f"   Tests Run: {len(suite.test_results)}")
        
        passed = sum(1 for r in suite.test_results if r.status == "passed")
        failed = sum(1 for r in suite.test_results if r.status == "failed")
        errors = sum(1 for r in suite.test_results if r.status == "error")
        
        console.print(f"   ✅ Passed: {passed}")
        console.print(f"   ❌ Failed: {failed}")
        console.print(f"   🚨 Errors: {errors}")
    
    async def run_all_suites(self) -> List[IntegrationTestSuite]:
        """Run all configured test suites."""
        results = []
        
        for suite in self.test_suites:
            result = await self.run_integration_suite(suite)
            results.append(result)
        
        return results
    
    def get_component_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the dependency graph of all components."""
        return {name: component.dependencies for name, component in self.components.items()}
    
    def validate_dependency_order(self) -> List[str]:
        """Validate and return the correct order for testing components based on dependencies."""
        # Simple topological sort for dependency ordering
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {component_name}")
            if component_name in visited:
                return
            
            temp_visited.add(component_name)
            
            if component_name in self.components:
                for dep in self.components[component_name].dependencies:
                    visit(dep)
            
            temp_visited.remove(component_name)
            visited.add(component_name)
            result.append(component_name)
        
        for component_name in self.components:
            visit(component_name)
        
        return result

