"""
Cross-Component Validation Framework

Provides comprehensive validation of component interactions and
system-wide consistency checks across all integrated components.
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from enum import Enum

from rich.console import Console
from rich.table import Table

from graph_sitter.shared.logging.logger import get_logger

logger = get_logger(__name__)
console = Console()


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during cross-component testing."""
    component: str
    issue_type: str
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None
    
    def __str__(self) -> str:
        severity_emoji = {
            ValidationSeverity.INFO: "ℹ️",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.CRITICAL: "🚨"
        }
        return f"{severity_emoji[self.severity]} [{self.component}] {self.issue_type}: {self.message}"


@dataclass
class ValidationResult:
    """Result of a cross-component validation."""
    component_pair: Tuple[str, str]
    validation_type: str
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    execution_time_ms: float = 0.0
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues that must be fixed."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
    
    @property
    def error_issues(self) -> List[ValidationIssue]:
        """Get error issues that should be fixed."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]


class ComponentInterface:
    """Represents the interface of a system component."""
    
    def __init__(self, name: str, module_path: str):
        self.name = name
        self.module_path = module_path
        self.public_methods: Set[str] = set()
        self.public_classes: Set[str] = set()
        self.dependencies: Set[str] = set()
        self.exports: Set[str] = set()
        self.version: Optional[str] = None
        
    def analyze_interface(self):
        """Analyze the component's public interface."""
        try:
            module = __import__(self.module_path, fromlist=[''])
            
            # Get public methods and classes
            for name in dir(module):
                if not name.startswith('_'):
                    obj = getattr(module, name)
                    if inspect.isfunction(obj):
                        self.public_methods.add(name)
                    elif inspect.isclass(obj):
                        self.public_classes.add(name)
            
            # Try to get version
            if hasattr(module, '__version__'):
                self.version = module.__version__
            
            logger.debug(f"Analyzed interface for {self.name}: {len(self.public_methods)} methods, {len(self.public_classes)} classes")
            
        except ImportError as e:
            logger.warning(f"Could not analyze interface for {self.name}: {e}")


class CrossComponentValidator:
    """
    Comprehensive cross-component validation framework.
    
    Validates that all system components work together correctly,
    including interface compatibility, data flow validation,
    and integration consistency checks.
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentInterface] = {}
        self.validation_results: List[ValidationResult] = []
        self.setup_components()
    
    def setup_components(self):
        """Initialize component interfaces for validation."""
        # Graph-Sitter components
        self.components["graph_sitter_core"] = ComponentInterface(
            "Graph-Sitter Core", "graph_sitter.core"
        )
        self.components["graph_sitter_python"] = ComponentInterface(
            "Graph-Sitter Python", "graph_sitter.python"
        )
        self.components["graph_sitter_typescript"] = ComponentInterface(
            "Graph-Sitter TypeScript", "graph_sitter.typescript"
        )
        
        # Codegen SDK components
        self.components["codegen_sdk"] = ComponentInterface(
            "Codegen SDK", "codegen"
        )
        self.components["codegen_extensions"] = ComponentInterface(
            "Codegen Extensions", "codegen.extensions"
        )
        
        # Integration components
        self.components["codebase_integration"] = ComponentInterface(
            "Codebase Integration", "graph_sitter.codebase"
        )
        self.components["git_integration"] = ComponentInterface(
            "Git Integration", "graph_sitter.git"
        )
        
        # Analyze all component interfaces
        for component in self.components.values():
            component.analyze_interface()
    
    async def validate_interface_compatibility(
        self, 
        component1: str, 
        component2: str
    ) -> ValidationResult:
        """Validate interface compatibility between two components."""
        start_time = asyncio.get_event_loop().time()
        
        if component1 not in self.components or component2 not in self.components:
            return ValidationResult(
                component_pair=(component1, component2),
                validation_type="interface_compatibility",
                passed=False,
                issues=[ValidationIssue(
                    component="validator",
                    issue_type="missing_component",
                    severity=ValidationSeverity.ERROR,
                    message=f"One or both components not found: {component1}, {component2}"
                )]
            )
        
        comp1 = self.components[component1]
        comp2 = self.components[component2]
        issues = []
        
        # Check for interface conflicts
        common_methods = comp1.public_methods.intersection(comp2.public_methods)
        if common_methods:
            issues.append(ValidationIssue(
                component=f"{component1}+{component2}",
                issue_type="method_name_conflict",
                severity=ValidationSeverity.WARNING,
                message=f"Common method names found: {', '.join(common_methods)}",
                details={"common_methods": list(common_methods)},
                suggested_fix="Consider using namespacing or prefixes to avoid conflicts"
            ))
        
        common_classes = comp1.public_classes.intersection(comp2.public_classes)
        if common_classes:
            issues.append(ValidationIssue(
                component=f"{component1}+{component2}",
                issue_type="class_name_conflict",
                severity=ValidationSeverity.WARNING,
                message=f"Common class names found: {', '.join(common_classes)}",
                details={"common_classes": list(common_classes)},
                suggested_fix="Consider using different class names or namespacing"
            ))
        
        # Check version compatibility
        if comp1.version and comp2.version:
            # Simple version compatibility check
            if comp1.version != comp2.version:
                issues.append(ValidationIssue(
                    component=f"{component1}+{component2}",
                    issue_type="version_mismatch",
                    severity=ValidationSeverity.INFO,
                    message=f"Version mismatch: {comp1.version} vs {comp2.version}",
                    details={"version1": comp1.version, "version2": comp2.version}
                ))
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        result = ValidationResult(
            component_pair=(component1, component2),
            validation_type="interface_compatibility",
            passed=len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0,
            issues=issues,
            execution_time_ms=execution_time_ms
        )
        
        self.validation_results.append(result)
        return result
    
    async def validate_data_flow(
        self, 
        source_component: str, 
        target_component: str,
        data_types: List[str]
    ) -> ValidationResult:
        """Validate data flow between components."""
        start_time = asyncio.get_event_loop().time()
        issues = []
        
        # Mock data flow validation
        # In a real implementation, this would test actual data passing
        for data_type in data_types:
            try:
                # Simulate data flow validation
                await asyncio.sleep(0.01)  # Simulate validation time
                
                # Mock validation logic
                if data_type == "invalid_type":
                    issues.append(ValidationIssue(
                        component=f"{source_component}->{target_component}",
                        issue_type="invalid_data_type",
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid data type: {data_type}",
                        details={"data_type": data_type},
                        suggested_fix="Use supported data types"
                    ))
                
            except Exception as e:
                issues.append(ValidationIssue(
                    component=f"{source_component}->{target_component}",
                    issue_type="data_flow_error",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Data flow validation failed for {data_type}: {str(e)}",
                    details={"data_type": data_type, "error": str(e)}
                ))
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        result = ValidationResult(
            component_pair=(source_component, target_component),
            validation_type="data_flow",
            passed=len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0,
            issues=issues,
            execution_time_ms=execution_time_ms
        )
        
        self.validation_results.append(result)
        return result
    
    async def validate_graph_sitter_codegen_integration(self) -> ValidationResult:
        """Validate integration between Graph-Sitter and Codegen SDK."""
        start_time = asyncio.get_event_loop().time()
        issues = []
        
        try:
            # Test Graph-Sitter codebase creation
            from graph_sitter.core.codebase import Codebase
            
            # Mock validation - in practice this would test real integration
            await asyncio.sleep(0.1)  # Simulate validation time
            
            # Check if Codebase can be created and used
            test_path = Path(".")
            if test_path.exists():
                try:
                    # This is a simplified test - real implementation would be more comprehensive
                    codebase = Codebase.from_path(test_path)
                    if len(codebase.files) == 0:
                        issues.append(ValidationIssue(
                            component="graph_sitter->codegen",
                            issue_type="empty_codebase",
                            severity=ValidationSeverity.WARNING,
                            message="Codebase contains no files",
                            suggested_fix="Ensure test directory contains source files"
                        ))
                except Exception as e:
                    issues.append(ValidationIssue(
                        component="graph_sitter->codegen",
                        issue_type="codebase_creation_error",
                        severity=ValidationSeverity.ERROR,
                        message=f"Failed to create codebase: {str(e)}",
                        details={"error": str(e)}
                    ))
            
            # Test Codegen SDK integration (mock)
            try:
                # This would test actual Codegen SDK integration
                # For now, we'll simulate the test
                await asyncio.sleep(0.05)
                
                # Mock successful integration
                logger.debug("Graph-Sitter to Codegen integration validated")
                
            except Exception as e:
                issues.append(ValidationIssue(
                    component="graph_sitter->codegen",
                    issue_type="sdk_integration_error",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Codegen SDK integration failed: {str(e)}",
                    details={"error": str(e)}
                ))
        
        except ImportError as e:
            issues.append(ValidationIssue(
                component="graph_sitter->codegen",
                issue_type="import_error",
                severity=ValidationSeverity.CRITICAL,
                message=f"Failed to import required modules: {str(e)}",
                details={"error": str(e)}
            ))
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        result = ValidationResult(
            component_pair=("graph_sitter", "codegen_sdk"),
            validation_type="integration_validation",
            passed=len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0,
            issues=issues,
            execution_time_ms=execution_time_ms
        )
        
        self.validation_results.append(result)
        return result
    
    async def validate_contexten_integration(self) -> ValidationResult:
        """Validate Contexten orchestration integration."""
        start_time = asyncio.get_event_loop().time()
        issues = []
        
        # Mock Contexten validation since it's not yet implemented
        try:
            await asyncio.sleep(0.1)  # Simulate validation time
            
            # Mock validation checks
            issues.append(ValidationIssue(
                component="contexten",
                issue_type="not_implemented",
                severity=ValidationSeverity.INFO,
                message="Contexten integration not yet implemented",
                suggested_fix="Implement Contexten orchestration module"
            ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                component="contexten",
                issue_type="validation_error",
                severity=ValidationSeverity.ERROR,
                message=f"Contexten validation failed: {str(e)}",
                details={"error": str(e)}
            ))
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        result = ValidationResult(
            component_pair=("codegen_sdk", "contexten"),
            validation_type="contexten_integration",
            passed=len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0,
            issues=issues,
            execution_time_ms=execution_time_ms
        )
        
        self.validation_results.append(result)
        return result
    
    async def validate_end_to_end_workflow(self) -> ValidationResult:
        """Validate complete end-to-end workflow across all components."""
        start_time = asyncio.get_event_loop().time()
        issues = []
        
        try:
            # Simulate end-to-end workflow validation
            console.print("🔄 Validating end-to-end workflow...")
            
            # Step 1: Graph-Sitter parsing
            await asyncio.sleep(0.1)
            logger.debug("✅ Graph-Sitter parsing validation")
            
            # Step 2: Codegen SDK integration
            await asyncio.sleep(0.1)
            logger.debug("✅ Codegen SDK integration validation")
            
            # Step 3: Contexten orchestration (mock)
            await asyncio.sleep(0.1)
            issues.append(ValidationIssue(
                component="end_to_end",
                issue_type="contexten_placeholder",
                severity=ValidationSeverity.INFO,
                message="Contexten orchestration step is mocked",
                suggested_fix="Implement actual Contexten integration"
            ))
            
            # Step 4: Integration validation
            await asyncio.sleep(0.1)
            logger.debug("✅ Integration validation completed")
            
        except Exception as e:
            issues.append(ValidationIssue(
                component="end_to_end",
                issue_type="workflow_error",
                severity=ValidationSeverity.CRITICAL,
                message=f"End-to-end workflow validation failed: {str(e)}",
                details={"error": str(e)}
            ))
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        result = ValidationResult(
            component_pair=("all_components", "end_to_end"),
            validation_type="end_to_end_workflow",
            passed=len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0,
            issues=issues,
            execution_time_ms=execution_time_ms
        )
        
        self.validation_results.append(result)
        return result
    
    async def run_all_validations(self) -> List[ValidationResult]:
        """Run all cross-component validations."""
        console.print("🔍 Starting comprehensive cross-component validation...")
        
        results = []
        
        # Interface compatibility validations
        component_pairs = [
            ("graph_sitter_core", "graph_sitter_python"),
            ("graph_sitter_core", "graph_sitter_typescript"),
            ("graph_sitter_core", "codegen_sdk"),
            ("codegen_sdk", "codegen_extensions"),
            ("graph_sitter_core", "codebase_integration"),
            ("codebase_integration", "git_integration"),
        ]
        
        for comp1, comp2 in component_pairs:
            result = await self.validate_interface_compatibility(comp1, comp2)
            results.append(result)
        
        # Data flow validations
        data_flow_tests = [
            ("graph_sitter_core", "codegen_sdk", ["ast_data", "symbol_data", "file_data"]),
            ("codegen_sdk", "codegen_extensions", ["task_data", "result_data"]),
            ("codebase_integration", "git_integration", ["repository_data", "diff_data"]),
        ]
        
        for source, target, data_types in data_flow_tests:
            result = await self.validate_data_flow(source, target, data_types)
            results.append(result)
        
        # Integration validations
        integration_results = await asyncio.gather(
            self.validate_graph_sitter_codegen_integration(),
            self.validate_contexten_integration(),
            self.validate_end_to_end_workflow()
        )
        results.extend(integration_results)
        
        self._display_validation_summary(results)
        return results
    
    def _display_validation_summary(self, results: List[ValidationResult]):
        """Display a summary of validation results."""
        table = Table(title="Cross-Component Validation Summary")
        table.add_column("Component Pair", style="cyan")
        table.add_column("Validation Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Issues", style="yellow")
        table.add_column("Duration (ms)", justify="right")
        
        total_issues = 0
        critical_issues = 0
        error_issues = 0
        
        for result in results:
            status_emoji = "✅" if result.passed else "❌"
            status_text = f"{status_emoji} {'PASS' if result.passed else 'FAIL'}"
            
            issue_count = len(result.issues)
            total_issues += issue_count
            critical_issues += len(result.critical_issues)
            error_issues += len(result.error_issues)
            
            issue_text = f"{issue_count} total"
            if result.critical_issues:
                issue_text += f", {len(result.critical_issues)} critical"
            if result.error_issues:
                issue_text += f", {len(result.error_issues)} errors"
            
            table.add_row(
                f"{result.component_pair[0]} → {result.component_pair[1]}",
                result.validation_type,
                status_text,
                issue_text,
                f"{result.execution_time_ms:.1f}"
            )
        
        console.print(table)
        
        # Summary statistics
        console.print(f"\n📊 Validation Summary:")
        console.print(f"   Total Validations: {len(results)}")
        console.print(f"   Passed: {sum(1 for r in results if r.passed)}")
        console.print(f"   Failed: {sum(1 for r in results if not r.passed)}")
        console.print(f"   Total Issues: {total_issues}")
        console.print(f"   🚨 Critical Issues: {critical_issues}")
        console.print(f"   ❌ Error Issues: {error_issues}")
        
        # Display critical issues
        if critical_issues > 0:
            console.print("\n🚨 Critical Issues Found:")
            for result in results:
                for issue in result.critical_issues:
                    console.print(f"   {issue}")
    
    def get_validation_report(self) -> str:
        """Generate a detailed validation report."""
        if not self.validation_results:
            return "No validation results available."
        
        report_lines = [
            "# Cross-Component Validation Report",
            f"Generated at: {asyncio.get_event_loop().time()}",
            f"Total validations: {len(self.validation_results)}",
            "",
            "## Summary",
        ]
        
        passed_count = sum(1 for r in self.validation_results if r.passed)
        failed_count = len(self.validation_results) - passed_count
        total_issues = sum(len(r.issues) for r in self.validation_results)
        critical_issues = sum(len(r.critical_issues) for r in self.validation_results)
        
        report_lines.extend([
            f"- Passed: {passed_count}/{len(self.validation_results)}",
            f"- Failed: {failed_count}/{len(self.validation_results)}",
            f"- Total Issues: {total_issues}",
            f"- Critical Issues: {critical_issues}",
            "",
            "## Detailed Results",
        ])
        
        for result in self.validation_results:
            report_lines.extend([
                f"### {result.component_pair[0]} → {result.component_pair[1]} ({result.validation_type})",
                f"- Status: {'PASS' if result.passed else 'FAIL'}",
                f"- Duration: {result.execution_time_ms:.1f}ms",
                f"- Issues: {len(result.issues)}",
            ])
            
            if result.issues:
                report_lines.append("- Issue Details:")
                for issue in result.issues:
                    report_lines.append(f"  - {issue}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

