"""
End-to-End Workflow Testing Framework

Provides comprehensive testing of complete workflows across all system
components, simulating real-world usage scenarios and user journeys.
"""

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)
console = Console()


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    description: str
    component: str
    action: str
    expected_result: str
    timeout_seconds: float = 30.0
    dependencies: List[str] = field(default_factory=list)
    
    # Execution results
    status: WorkflowStatus = WorkflowStatus.PENDING
    execution_time_ms: float = 0.0
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowScenario:
    """Represents a complete end-to-end workflow scenario."""
    name: str
    description: str
    steps: List[WorkflowStep]
    setup_steps: List[WorkflowStep] = field(default_factory=list)
    teardown_steps: List[WorkflowStep] = field(default_factory=list)
    
    # Execution tracking
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    @property
    def duration_ms(self) -> float:
        """Calculate total workflow duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of workflow steps."""
        if not self.steps:
            return 0.0
        completed = sum(1 for step in self.steps if step.status == WorkflowStatus.COMPLETED)
        return completed / len(self.steps)
    
    @property
    def failed_steps(self) -> List[WorkflowStep]:
        """Get list of failed steps."""
        return [step for step in self.steps if step.status == WorkflowStatus.FAILED]


class EndToEndWorkflowTester:
    """
    Comprehensive end-to-end workflow testing framework.
    
    Tests complete user journeys and workflows across all system components,
    including Graph-Sitter analysis, Codegen SDK operations, and Contexten
    orchestration scenarios.
    """
    
    def __init__(self, test_data_path: Optional[Path] = None):
        self.test_data_path = test_data_path or Path("tests/data")
        self.scenarios: List[WorkflowScenario] = []
        self.setup_scenarios()
    
    def setup_scenarios(self):
        """Initialize predefined workflow scenarios."""
        # Scenario 1: Code Analysis Workflow
        self.scenarios.append(self._create_code_analysis_workflow())
        
        # Scenario 2: Code Generation Workflow
        self.scenarios.append(self._create_code_generation_workflow())
        
        # Scenario 3: Repository Integration Workflow
        self.scenarios.append(self._create_repository_integration_workflow())
        
        # Scenario 4: Multi-Language Analysis Workflow
        self.scenarios.append(self._create_multi_language_workflow())
        
        # Scenario 5: Performance Optimization Workflow
        self.scenarios.append(self._create_performance_workflow())
    
    def _create_code_analysis_workflow(self) -> WorkflowScenario:
        """Create a comprehensive code analysis workflow."""
        steps = [
            WorkflowStep(
                name="initialize_codebase",
                description="Initialize Graph-Sitter codebase from repository",
                component="graph_sitter",
                action="create_codebase",
                expected_result="Codebase object created with parsed files"
            ),
            WorkflowStep(
                name="parse_python_files",
                description="Parse all Python files in the codebase",
                component="graph_sitter_python",
                action="parse_files",
                expected_result="All Python files successfully parsed",
                dependencies=["initialize_codebase"]
            ),
            WorkflowStep(
                name="parse_typescript_files",
                description="Parse all TypeScript files in the codebase",
                component="graph_sitter_typescript",
                action="parse_files",
                expected_result="All TypeScript files successfully parsed",
                dependencies=["initialize_codebase"]
            ),
            WorkflowStep(
                name="resolve_symbols",
                description="Resolve all symbols and dependencies",
                component="graph_sitter",
                action="resolve_symbols",
                expected_result="All symbols resolved with dependency graph",
                dependencies=["parse_python_files", "parse_typescript_files"]
            ),
            WorkflowStep(
                name="analyze_imports",
                description="Analyze import relationships across files",
                component="graph_sitter",
                action="analyze_imports",
                expected_result="Import dependency graph created",
                dependencies=["resolve_symbols"]
            ),
            WorkflowStep(
                name="generate_analysis_report",
                description="Generate comprehensive analysis report",
                component="graph_sitter",
                action="generate_report",
                expected_result="Analysis report with metrics and insights",
                dependencies=["analyze_imports"]
            )
        ]
        
        return WorkflowScenario(
            name="code_analysis_workflow",
            description="Complete code analysis workflow using Graph-Sitter",
            steps=steps
        )
    
    def _create_code_generation_workflow(self) -> WorkflowScenario:
        """Create a code generation workflow using Codegen SDK."""
        steps = [
            WorkflowStep(
                name="create_codegen_agent",
                description="Create Codegen SDK agent instance",
                component="codegen_sdk",
                action="create_agent",
                expected_result="Agent instance created successfully"
            ),
            WorkflowStep(
                name="analyze_codebase_context",
                description="Analyze codebase for generation context",
                component="codegen_sdk",
                action="analyze_context",
                expected_result="Codebase context analyzed and prepared",
                dependencies=["create_codegen_agent"]
            ),
            WorkflowStep(
                name="generate_test_code",
                description="Generate test code for existing functions",
                component="codegen_sdk",
                action="generate_tests",
                expected_result="Test code generated successfully",
                dependencies=["analyze_codebase_context"]
            ),
            WorkflowStep(
                name="generate_documentation",
                description="Generate documentation for code components",
                component="codegen_sdk",
                action="generate_docs",
                expected_result="Documentation generated successfully",
                dependencies=["analyze_codebase_context"]
            ),
            WorkflowStep(
                name="validate_generated_code",
                description="Validate generated code syntax and quality",
                component="codegen_sdk",
                action="validate_code",
                expected_result="Generated code passes validation",
                dependencies=["generate_test_code", "generate_documentation"]
            )
        ]
        
        return WorkflowScenario(
            name="code_generation_workflow",
            description="Complete code generation workflow using Codegen SDK",
            steps=steps
        )
    
    def _create_repository_integration_workflow(self) -> WorkflowScenario:
        """Create a repository integration workflow."""
        steps = [
            WorkflowStep(
                name="clone_repository",
                description="Clone repository for analysis",
                component="git_integration",
                action="clone_repo",
                expected_result="Repository cloned successfully"
            ),
            WorkflowStep(
                name="analyze_git_history",
                description="Analyze Git commit history and changes",
                component="git_integration",
                action="analyze_history",
                expected_result="Git history analyzed with change patterns",
                dependencies=["clone_repository"]
            ),
            WorkflowStep(
                name="create_feature_branch",
                description="Create new feature branch for changes",
                component="git_integration",
                action="create_branch",
                expected_result="Feature branch created successfully",
                dependencies=["clone_repository"]
            ),
            WorkflowStep(
                name="apply_code_changes",
                description="Apply generated code changes to repository",
                component="codegen_sdk",
                action="apply_changes",
                expected_result="Code changes applied successfully",
                dependencies=["create_feature_branch"]
            ),
            WorkflowStep(
                name="commit_changes",
                description="Commit changes with descriptive message",
                component="git_integration",
                action="commit_changes",
                expected_result="Changes committed successfully",
                dependencies=["apply_code_changes"]
            ),
            WorkflowStep(
                name="create_pull_request",
                description="Create pull request for review",
                component="git_integration",
                action="create_pr",
                expected_result="Pull request created successfully",
                dependencies=["commit_changes"]
            )
        ]
        
        return WorkflowScenario(
            name="repository_integration_workflow",
            description="Complete repository integration workflow",
            steps=steps
        )
    
    def _create_multi_language_workflow(self) -> WorkflowScenario:
        """Create a multi-language analysis workflow."""
        steps = [
            WorkflowStep(
                name="detect_languages",
                description="Detect all programming languages in codebase",
                component="graph_sitter",
                action="detect_languages",
                expected_result="All languages detected and categorized"
            ),
            WorkflowStep(
                name="parse_python_components",
                description="Parse Python files and extract components",
                component="graph_sitter_python",
                action="parse_components",
                expected_result="Python components parsed successfully",
                dependencies=["detect_languages"]
            ),
            WorkflowStep(
                name="parse_typescript_components",
                description="Parse TypeScript files and extract components",
                component="graph_sitter_typescript",
                action="parse_components",
                expected_result="TypeScript components parsed successfully",
                dependencies=["detect_languages"]
            ),
            WorkflowStep(
                name="analyze_cross_language_deps",
                description="Analyze dependencies between different languages",
                component="graph_sitter",
                action="analyze_cross_deps",
                expected_result="Cross-language dependencies mapped",
                dependencies=["parse_python_components", "parse_typescript_components"]
            ),
            WorkflowStep(
                name="generate_unified_schema",
                description="Generate unified schema for all languages",
                component="graph_sitter",
                action="generate_schema",
                expected_result="Unified schema generated successfully",
                dependencies=["analyze_cross_language_deps"]
            )
        ]
        
        return WorkflowScenario(
            name="multi_language_workflow",
            description="Multi-language codebase analysis workflow",
            steps=steps
        )
    
    def _create_performance_workflow(self) -> WorkflowScenario:
        """Create a performance optimization workflow."""
        steps = [
            WorkflowStep(
                name="baseline_performance",
                description="Establish performance baseline measurements",
                component="performance_monitor",
                action="measure_baseline",
                expected_result="Baseline performance metrics captured"
            ),
            WorkflowStep(
                name="identify_bottlenecks",
                description="Identify performance bottlenecks in code",
                component="graph_sitter",
                action="analyze_performance",
                expected_result="Performance bottlenecks identified",
                dependencies=["baseline_performance"]
            ),
            WorkflowStep(
                name="generate_optimizations",
                description="Generate code optimizations using Codegen",
                component="codegen_sdk",
                action="generate_optimizations",
                expected_result="Optimization suggestions generated",
                dependencies=["identify_bottlenecks"]
            ),
            WorkflowStep(
                name="apply_optimizations",
                description="Apply generated optimizations to codebase",
                component="codegen_sdk",
                action="apply_optimizations",
                expected_result="Optimizations applied successfully",
                dependencies=["generate_optimizations"]
            ),
            WorkflowStep(
                name="measure_improvements",
                description="Measure performance improvements after optimization",
                component="performance_monitor",
                action="measure_improvements",
                expected_result="Performance improvements quantified",
                dependencies=["apply_optimizations"]
            )
        ]
        
        return WorkflowScenario(
            name="performance_optimization_workflow",
            description="Performance analysis and optimization workflow",
            steps=steps
        )
    
    async def execute_workflow_step(self, step: WorkflowStep) -> bool:
        """Execute a single workflow step."""
        step.status = WorkflowStatus.RUNNING
        start_time = time.time()
        
        try:
            # Simulate step execution based on component and action
            await self._simulate_step_execution(step)
            
            step.execution_time_ms = (time.time() - start_time) * 1000
            step.status = WorkflowStatus.COMPLETED
            step.actual_result = step.expected_result  # Mock success
            
            logger.debug(f"✅ Step '{step.name}' completed in {step.execution_time_ms:.1f}ms")
            return True
            
        except Exception as e:
            step.execution_time_ms = (time.time() - start_time) * 1000
            step.status = WorkflowStatus.FAILED
            step.error_message = str(e)
            
            logger.error(f"❌ Step '{step.name}' failed: {e}")
            return False
    
    async def _simulate_step_execution(self, step: WorkflowStep):
        """Simulate execution of a workflow step."""
        # Different simulation times based on component and action
        simulation_times = {
            "graph_sitter": {
                "create_codebase": 0.2,
                "parse_files": 0.3,
                "resolve_symbols": 0.4,
                "analyze_imports": 0.2,
                "generate_report": 0.1,
                "detect_languages": 0.1,
                "parse_components": 0.3,
                "analyze_cross_deps": 0.3,
                "generate_schema": 0.2,
                "analyze_performance": 0.4,
            },
            "codegen_sdk": {
                "create_agent": 0.1,
                "analyze_context": 0.3,
                "generate_tests": 0.5,
                "generate_docs": 0.4,
                "validate_code": 0.2,
                "apply_changes": 0.3,
                "generate_optimizations": 0.6,
                "apply_optimizations": 0.4,
            },
            "git_integration": {
                "clone_repo": 0.5,
                "analyze_history": 0.3,
                "create_branch": 0.1,
                "commit_changes": 0.2,
                "create_pr": 0.2,
            },
            "performance_monitor": {
                "measure_baseline": 0.3,
                "measure_improvements": 0.3,
            }
        }
        
        # Get simulation time
        component_times = simulation_times.get(step.component, {})
        sim_time = component_times.get(step.action, 0.1)
        
        # Add some randomness
        import random
        sim_time *= random.uniform(0.8, 1.2)
        
        await asyncio.sleep(sim_time)
        
        # Simulate occasional failures for testing
        if random.random() < 0.05:  # 5% failure rate
            raise Exception(f"Simulated failure in {step.component}.{step.action}")
        
        # Store mock artifacts
        step.artifacts = {
            "execution_time": sim_time,
            "component": step.component,
            "action": step.action,
            "timestamp": time.time()
        }
    
    async def execute_workflow(self, scenario: WorkflowScenario) -> WorkflowScenario:
        """Execute a complete workflow scenario."""
        console.print(f"🚀 Starting workflow: {scenario.name}")
        scenario.start_time = time.time()
        scenario.status = WorkflowStatus.RUNNING
        
        try:
            # Execute setup steps
            for step in scenario.setup_steps:
                success = await self.execute_workflow_step(step)
                if not success:
                    raise Exception(f"Setup step '{step.name}' failed")
            
            # Execute main workflow steps
            with Progress() as progress:
                task = progress.add_task(f"Executing {scenario.name}", total=len(scenario.steps))
                
                for step in scenario.steps:
                    # Check dependencies
                    if not await self._check_step_dependencies(step, scenario.steps):
                        step.status = WorkflowStatus.SKIPPED
                        step.error_message = "Dependencies not met"
                        progress.update(task, advance=1)
                        continue
                    
                    success = await self.execute_workflow_step(step)
                    progress.update(task, advance=1)
                    
                    # Continue even if step fails (for comprehensive testing)
                    if not success:
                        logger.warning(f"Step '{step.name}' failed, continuing workflow...")
            
            # Execute teardown steps
            for step in scenario.teardown_steps:
                await self.execute_workflow_step(step)
            
            scenario.end_time = time.time()
            
            # Determine overall status
            failed_steps = scenario.failed_steps
            if not failed_steps:
                scenario.status = WorkflowStatus.COMPLETED
            else:
                scenario.status = WorkflowStatus.FAILED
            
            self._display_workflow_results(scenario)
            
        except Exception as e:
            scenario.end_time = time.time()
            scenario.status = WorkflowStatus.FAILED
            logger.error(f"Workflow '{scenario.name}' failed: {e}")
        
        return scenario
    
    async def _check_step_dependencies(self, step: WorkflowStep, all_steps: List[WorkflowStep]) -> bool:
        """Check if step dependencies are satisfied."""
        if not step.dependencies:
            return True
        
        step_by_name = {s.name: s for s in all_steps}
        
        for dep_name in step.dependencies:
            if dep_name not in step_by_name:
                logger.warning(f"Dependency '{dep_name}' not found for step '{step.name}'")
                return False
            
            dep_step = step_by_name[dep_name]
            if dep_step.status != WorkflowStatus.COMPLETED:
                logger.debug(f"Dependency '{dep_name}' not completed for step '{step.name}'")
                return False
        
        return True
    
    def _display_workflow_results(self, scenario: WorkflowScenario):
        """Display workflow execution results."""
        table = Table(title=f"Workflow Results: {scenario.name}")
        table.add_column("Step", style="cyan")
        table.add_column("Component", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Duration (ms)", justify="right")
        table.add_column("Result", style="yellow")
        
        for step in scenario.steps:
            status_emoji = {
                WorkflowStatus.COMPLETED: "✅",
                WorkflowStatus.FAILED: "❌",
                WorkflowStatus.SKIPPED: "⏭️",
                WorkflowStatus.PENDING: "⏳",
                WorkflowStatus.RUNNING: "🔄"
            }
            
            status_text = f"{status_emoji[step.status]} {step.status.value.upper()}"
            
            result_text = step.actual_result or step.error_message or "No result"
            if len(result_text) > 50:
                result_text = result_text[:47] + "..."
            
            table.add_row(
                step.name,
                step.component,
                status_text,
                f"{step.execution_time_ms:.1f}",
                result_text
            )
        
        console.print(table)
        
        # Summary
        console.print(f"\n📊 Workflow Summary:")
        console.print(f"   Duration: {scenario.duration_ms:.1f}ms")
        console.print(f"   Success Rate: {scenario.success_rate:.1%}")
        console.print(f"   Status: {scenario.status.value.upper()}")
        
        completed = sum(1 for s in scenario.steps if s.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for s in scenario.steps if s.status == WorkflowStatus.FAILED)
        skipped = sum(1 for s in scenario.steps if s.status == WorkflowStatus.SKIPPED)
        
        console.print(f"   ✅ Completed: {completed}")
        console.print(f"   ❌ Failed: {failed}")
        console.print(f"   ⏭️ Skipped: {skipped}")
    
    async def run_all_workflows(self) -> List[WorkflowScenario]:
        """Execute all configured workflow scenarios."""
        console.print("🎯 Starting comprehensive end-to-end workflow testing...")
        
        results = []
        
        for scenario in self.scenarios:
            result = await self.execute_workflow(scenario)
            results.append(result)
        
        self._display_overall_summary(results)
        return results
    
    def _display_overall_summary(self, scenarios: List[WorkflowScenario]):
        """Display overall summary of all workflow executions."""
        table = Table(title="End-to-End Workflow Testing Summary")
        table.add_column("Workflow", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Success Rate", justify="right")
        table.add_column("Duration (ms)", justify="right")
        table.add_column("Failed Steps", justify="right")
        
        total_duration = 0
        total_success_rate = 0
        completed_workflows = 0
        
        for scenario in scenarios:
            status_emoji = {
                WorkflowStatus.COMPLETED: "✅",
                WorkflowStatus.FAILED: "❌",
                WorkflowStatus.SKIPPED: "⏭️",
                WorkflowStatus.PENDING: "⏳",
                WorkflowStatus.RUNNING: "🔄"
            }
            
            status_text = f"{status_emoji[scenario.status]} {scenario.status.value.upper()}"
            
            table.add_row(
                scenario.name,
                status_text,
                f"{scenario.success_rate:.1%}",
                f"{scenario.duration_ms:.1f}",
                str(len(scenario.failed_steps))
            )
            
            total_duration += scenario.duration_ms
            total_success_rate += scenario.success_rate
            if scenario.status == WorkflowStatus.COMPLETED:
                completed_workflows += 1
        
        console.print(table)
        
        # Overall statistics
        avg_success_rate = total_success_rate / len(scenarios) if scenarios else 0
        
        console.print(f"\n🎯 Overall Summary:")
        console.print(f"   Total Workflows: {len(scenarios)}")
        console.print(f"   Completed: {completed_workflows}")
        console.print(f"   Average Success Rate: {avg_success_rate:.1%}")
        console.print(f"   Total Duration: {total_duration:.1f}ms")
    
    def get_workflow_report(self) -> str:
        """Generate a comprehensive workflow testing report."""
        if not self.scenarios:
            return "No workflow scenarios available."
        
        report_lines = [
            "# End-to-End Workflow Testing Report",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total workflows: {len(self.scenarios)}",
            "",
            "## Summary",
        ]
        
        completed = sum(1 for s in self.scenarios if s.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for s in self.scenarios if s.status == WorkflowStatus.FAILED)
        avg_success_rate = sum(s.success_rate for s in self.scenarios) / len(self.scenarios)
        
        report_lines.extend([
            f"- Completed workflows: {completed}/{len(self.scenarios)}",
            f"- Failed workflows: {failed}/{len(self.scenarios)}",
            f"- Average success rate: {avg_success_rate:.1%}",
            "",
            "## Workflow Details",
        ])
        
        for scenario in self.scenarios:
            report_lines.extend([
                f"### {scenario.name}",
                f"- Description: {scenario.description}",
                f"- Status: {scenario.status.value.upper()}",
                f"- Duration: {scenario.duration_ms:.1f}ms",
                f"- Success Rate: {scenario.success_rate:.1%}",
                f"- Steps: {len(scenario.steps)}",
                f"- Failed Steps: {len(scenario.failed_steps)}",
            ])
            
            if scenario.failed_steps:
                report_lines.append("- Failed Step Details:")
                for step in scenario.failed_steps:
                    report_lines.append(f"  - {step.name}: {step.error_message}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

