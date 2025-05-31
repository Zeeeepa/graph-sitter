#!/usr/bin/env python3
"""
Codegen SDK Integration Prototype
Demonstrates integration between Graph-Sitter analysis and Codegen SDK.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.enums import UsageType
except ImportError:
    print("Graph-Sitter not available. Using mock implementation.")
    # Mock implementation
    class Codebase:
        def __init__(self, path, config=None):
            self.path = path
            self.functions = [MockSymbol(f"function_{i}") for i in range(10)]
            self.classes = [MockSymbol(f"class_{i}") for i in range(5)]
    
    class MockSymbol:
        def __init__(self, name):
            self.name = name
            self.usages = []
            self.dependencies = []
            self.complexity = 5
            self.file_path = f"src/{name}.py"
            self.line_number = 10

try:
    from codegen import Agent
except ImportError:
    print("Codegen SDK not available. Using mock implementation.")
    # Mock implementation
    class Agent:
        def __init__(self, org_id: str, token: str):
            self.org_id = org_id
            self.token = token
        
        def run(self, prompt: str):
            return MockTask(f"task_{hash(prompt) % 1000}")
    
    class MockTask:
        def __init__(self, task_id: str):
            self.id = task_id
            self.status = "completed"
            self.result = f"Mock result for task {task_id}"
        
        def refresh(self):
            pass


class TaskType(Enum):
    """Types of automated tasks that can be created."""
    REMOVE_DEAD_CODE = "remove_dead_code"
    REFACTOR_COMPLEX_FUNCTION = "refactor_complex_function"
    RESOLVE_CIRCULAR_DEPENDENCY = "resolve_circular_dependency"
    ADD_TYPE_ANNOTATIONS = "add_type_annotations"
    IMPROVE_DOCUMENTATION = "improve_documentation"
    EXTRACT_FUNCTION = "extract_function"
    RENAME_SYMBOL = "rename_symbol"
    OPTIMIZE_IMPORTS = "optimize_imports"


@dataclass
class AnalysisInsight:
    """Container for analysis insights that can trigger automated tasks."""
    insight_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_symbols: List[str]
    file_paths: List[str]
    suggested_action: str
    automation_feasible: bool
    confidence_score: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


@dataclass
class AutomationTask:
    """Container for automated refactoring tasks."""
    task_id: str
    task_type: TaskType
    priority: int  # 1-10, higher is more important
    description: str
    target_symbols: List[str]
    target_files: List[str]
    estimated_effort_hours: float
    risk_level: str  # 'low', 'medium', 'high'
    prerequisites: List[str]
    validation_criteria: List[str]
    codegen_prompt: str
    created_at: str
    status: str = "pending"


class CodegenGraphSitterIntegration:
    """
    Integration layer between Graph-Sitter analysis and Codegen SDK.
    Provides automated code improvement suggestions and task creation.
    """
    
    def __init__(self, org_id: str, token: str, repo_path: str):
        """Initialize the integration."""
        self.org_id = org_id
        self.token = token
        self.repo_path = Path(repo_path)
        
        # Initialize Codegen agent
        self.agent = Agent(org_id=org_id, token=token)
        
        # Initialize Graph-Sitter codebase
        config = CodebaseConfig(
            parallel_processing=True,
            precompute_dependencies=True,
            lazy_loading=True
        )
        self.codebase = Codebase(str(repo_path), config=config)
        
        # Analysis results
        self.insights: List[AnalysisInsight] = []
        self.tasks: List[AutomationTask] = []
    
    def analyze_codebase_health(self) -> List[AnalysisInsight]:
        """Analyze codebase health and generate insights."""
        print("Analyzing codebase health...")
        
        insights = []
        
        # Dead code analysis
        dead_code_insights = self._analyze_dead_code()
        insights.extend(dead_code_insights)
        
        # Complexity analysis
        complexity_insights = self._analyze_complexity()
        insights.extend(complexity_insights)
        
        # Dependency analysis
        dependency_insights = self._analyze_dependencies()
        insights.extend(dependency_insights)
        
        # Documentation analysis
        documentation_insights = self._analyze_documentation()
        insights.extend(documentation_insights)
        
        # Type annotation analysis
        type_insights = self._analyze_type_annotations()
        insights.extend(type_insights)
        
        self.insights = insights
        return insights
    
    def _analyze_dead_code(self) -> List[AnalysisInsight]:
        """Analyze for dead code (unused functions/classes)."""
        insights = []
        
        # Find unused functions
        if hasattr(self.codebase, 'functions'):
            dead_functions = [
                f for f in self.codebase.functions 
                if hasattr(f, 'usages') and not f.usages
            ]
            
            if dead_functions:
                insight = AnalysisInsight(
                    insight_type="dead_code",
                    severity="medium",
                    description=f"Found {len(dead_functions)} unused functions that can be safely removed",
                    affected_symbols=[f.name for f in dead_functions],
                    file_paths=list(set(f.file_path for f in dead_functions if hasattr(f, 'file_path'))),
                    suggested_action="Remove unused functions to reduce codebase complexity",
                    automation_feasible=True,
                    confidence_score=0.9,
                    metadata={
                        "function_count": len(dead_functions),
                        "estimated_lines_removed": len(dead_functions) * 10  # Rough estimate
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_complexity(self) -> List[AnalysisInsight]:
        """Analyze function complexity."""
        insights = []
        
        if hasattr(self.codebase, 'functions'):
            high_complexity_functions = [
                f for f in self.codebase.functions
                if hasattr(f, 'complexity') and f.complexity > 15
            ]
            
            if high_complexity_functions:
                insight = AnalysisInsight(
                    insight_type="high_complexity",
                    severity="high",
                    description=f"Found {len(high_complexity_functions)} functions with high complexity (>15)",
                    affected_symbols=[f.name for f in high_complexity_functions],
                    file_paths=list(set(f.file_path for f in high_complexity_functions if hasattr(f, 'file_path'))),
                    suggested_action="Refactor high-complexity functions into smaller, more manageable pieces",
                    automation_feasible=True,
                    confidence_score=0.8,
                    metadata={
                        "max_complexity": max(f.complexity for f in high_complexity_functions),
                        "avg_complexity": sum(f.complexity for f in high_complexity_functions) / len(high_complexity_functions)
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_dependencies(self) -> List[AnalysisInsight]:
        """Analyze dependency issues."""
        insights = []
        
        # Check for circular dependencies
        if hasattr(self.codebase, 'find_circular_dependencies'):
            try:
                circular_deps = self.codebase.find_circular_dependencies()
                
                if circular_deps:
                    insight = AnalysisInsight(
                        insight_type="circular_dependencies",
                        severity="high",
                        description=f"Found {len(circular_deps)} circular dependency cycles",
                        affected_symbols=[],  # Would need to extract from circular_deps
                        file_paths=[],
                        suggested_action="Resolve circular dependencies by restructuring imports or extracting common code",
                        automation_feasible=False,  # Usually requires manual intervention
                        confidence_score=0.95,
                        metadata={
                            "cycle_count": len(circular_deps)
                        }
                    )
                    insights.append(insight)
            except Exception:
                pass  # Method might not be available in mock
        
        return insights
    
    def _analyze_documentation(self) -> List[AnalysisInsight]:
        """Analyze documentation coverage."""
        insights = []
        
        if hasattr(self.codebase, 'functions'):
            undocumented_functions = [
                f for f in self.codebase.functions
                if not hasattr(f, 'docstring') or not f.docstring
            ]
            
            if len(undocumented_functions) > len(self.codebase.functions) * 0.3:  # >30% undocumented
                insight = AnalysisInsight(
                    insight_type="poor_documentation",
                    severity="medium",
                    description=f"Found {len(undocumented_functions)} functions without documentation",
                    affected_symbols=[f.name for f in undocumented_functions],
                    file_paths=list(set(f.file_path for f in undocumented_functions if hasattr(f, 'file_path'))),
                    suggested_action="Add docstrings to improve code maintainability",
                    automation_feasible=True,
                    confidence_score=0.7,
                    metadata={
                        "undocumented_count": len(undocumented_functions),
                        "total_functions": len(self.codebase.functions),
                        "documentation_coverage": 1 - (len(undocumented_functions) / len(self.codebase.functions))
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_type_annotations(self) -> List[AnalysisInsight]:
        """Analyze type annotation coverage."""
        insights = []
        
        # This would require more sophisticated analysis in a real implementation
        # For now, we'll create a mock insight
        insight = AnalysisInsight(
            insight_type="missing_type_annotations",
            severity="low",
            description="Some functions lack type annotations",
            affected_symbols=[],
            file_paths=[],
            suggested_action="Add type annotations to improve code clarity and IDE support",
            automation_feasible=True,
            confidence_score=0.6,
            metadata={
                "estimated_coverage": 0.4
            }
        )
        insights.append(insight)
        
        return insights
    
    def create_automation_tasks(self, insights: Optional[List[AnalysisInsight]] = None) -> List[AutomationTask]:
        """Create automation tasks based on analysis insights."""
        if insights is None:
            insights = self.insights
        
        tasks = []
        
        for insight in insights:
            if not insight.automation_feasible:
                continue
            
            task = self._create_task_from_insight(insight)
            if task:
                tasks.append(task)
        
        self.tasks = tasks
        return tasks
    
    def _create_task_from_insight(self, insight: AnalysisInsight) -> Optional[AutomationTask]:
        """Create an automation task from an analysis insight."""
        task_id = f"task_{int(time.time())}_{hash(insight.description) % 1000}"
        
        if insight.insight_type == "dead_code":
            return AutomationTask(
                task_id=task_id,
                task_type=TaskType.REMOVE_DEAD_CODE,
                priority=6,
                description=f"Remove {len(insight.affected_symbols)} unused functions",
                target_symbols=insight.affected_symbols,
                target_files=insight.file_paths,
                estimated_effort_hours=0.5,
                risk_level="low",
                prerequisites=["Ensure comprehensive test coverage"],
                validation_criteria=["All tests pass", "No new import errors"],
                codegen_prompt=self._generate_dead_code_removal_prompt(insight),
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        elif insight.insight_type == "high_complexity":
            return AutomationTask(
                task_id=task_id,
                task_type=TaskType.REFACTOR_COMPLEX_FUNCTION,
                priority=8,
                description=f"Refactor {len(insight.affected_symbols)} high-complexity functions",
                target_symbols=insight.affected_symbols,
                target_files=insight.file_paths,
                estimated_effort_hours=2.0,
                risk_level="medium",
                prerequisites=["Review function logic", "Ensure test coverage"],
                validation_criteria=["Complexity reduced", "All tests pass", "Functionality preserved"],
                codegen_prompt=self._generate_complexity_refactor_prompt(insight),
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        elif insight.insight_type == "poor_documentation":
            return AutomationTask(
                task_id=task_id,
                task_type=TaskType.IMPROVE_DOCUMENTATION,
                priority=4,
                description=f"Add documentation to {len(insight.affected_symbols)} functions",
                target_symbols=insight.affected_symbols,
                target_files=insight.file_paths,
                estimated_effort_hours=1.0,
                risk_level="low",
                prerequisites=[],
                validation_criteria=["All functions have docstrings", "Documentation follows style guide"],
                codegen_prompt=self._generate_documentation_prompt(insight),
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        elif insight.insight_type == "missing_type_annotations":
            return AutomationTask(
                task_id=task_id,
                task_type=TaskType.ADD_TYPE_ANNOTATIONS,
                priority=3,
                description="Add type annotations to improve code clarity",
                target_symbols=insight.affected_symbols,
                target_files=insight.file_paths,
                estimated_effort_hours=1.5,
                risk_level="low",
                prerequisites=[],
                validation_criteria=["Type annotations added", "mypy checks pass"],
                codegen_prompt=self._generate_type_annotation_prompt(insight),
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        return None
    
    def _generate_dead_code_removal_prompt(self, insight: AnalysisInsight) -> str:
        """Generate Codegen prompt for dead code removal."""
        symbols = ", ".join(insight.affected_symbols[:5])  # Limit for prompt length
        if len(insight.affected_symbols) > 5:
            symbols += f" and {len(insight.affected_symbols) - 5} others"
        
        return f"""
        Remove unused functions from the codebase to reduce complexity and improve maintainability.
        
        The following functions appear to be unused (no references found):
        {symbols}
        
        Please:
        1. Verify that these functions are truly unused by checking for dynamic calls or external usage
        2. Remove the unused functions and any associated imports
        3. Update any related documentation or comments
        4. Ensure all tests still pass after removal
        
        Be careful to preserve any functions that might be used dynamically or by external systems.
        """
    
    def _generate_complexity_refactor_prompt(self, insight: AnalysisInsight) -> str:
        """Generate Codegen prompt for complexity refactoring."""
        max_complexity = insight.metadata.get('max_complexity', 'high')
        
        return f"""
        Refactor high-complexity functions to improve maintainability and readability.
        
        The following functions have high cyclomatic complexity (max: {max_complexity}):
        {', '.join(insight.affected_symbols[:3])}
        
        Please:
        1. Break down complex functions into smaller, single-purpose functions
        2. Extract common logic into helper functions
        3. Reduce nested conditionals and loops where possible
        4. Maintain the original functionality and behavior
        5. Ensure all tests continue to pass
        6. Add appropriate documentation to new functions
        
        Focus on improving readability while preserving the exact same functionality.
        """
    
    def _generate_documentation_prompt(self, insight: AnalysisInsight) -> str:
        """Generate Codegen prompt for documentation improvement."""
        coverage = insight.metadata.get('documentation_coverage', 0.5)
        
        return f"""
        Improve code documentation by adding comprehensive docstrings to functions.
        
        Current documentation coverage: {coverage:.1%}
        
        Please add docstrings to the following functions:
        {', '.join(insight.affected_symbols[:10])}
        
        For each function, include:
        1. A clear description of what the function does
        2. Parameters with types and descriptions
        3. Return value description and type
        4. Any exceptions that might be raised
        5. Usage examples for complex functions
        
        Follow the Google or NumPy docstring style guide for consistency.
        """
    
    def _generate_type_annotation_prompt(self, insight: AnalysisInsight) -> str:
        """Generate Codegen prompt for type annotation improvement."""
        return f"""
        Add type annotations to improve code clarity and enable better IDE support.
        
        Please:
        1. Add type hints to function parameters and return values
        2. Use appropriate types from the typing module for complex types
        3. Ensure compatibility with the current Python version
        4. Add necessary imports for typing constructs
        5. Verify that mypy or similar type checkers pass
        
        Focus on public APIs and commonly used functions first.
        """
    
    def execute_automation_tasks(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Execute automation tasks using Codegen SDK."""
        print(f"Executing {len(self.tasks)} automation tasks...")
        
        results = {
            'total_tasks': len(self.tasks),
            'completed': 0,
            'failed': 0,
            'task_results': []
        }
        
        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks[:max_concurrent]:  # Limit concurrent tasks
            try:
                print(f"Executing task: {task.description}")
                
                # Create Codegen task
                codegen_task = self.agent.run(prompt=task.codegen_prompt)
                
                # Update task status
                task.status = "submitted"
                
                # Wait for completion (in real implementation, this would be async)
                codegen_task.refresh()
                
                if codegen_task.status == "completed":
                    task.status = "completed"
                    results['completed'] += 1
                    
                    task_result = {
                        'task_id': task.task_id,
                        'task_type': task.task_type.value,
                        'status': 'completed',
                        'codegen_task_id': codegen_task.id,
                        'result': codegen_task.result
                    }
                else:
                    task.status = "failed"
                    results['failed'] += 1
                    
                    task_result = {
                        'task_id': task.task_id,
                        'task_type': task.task_type.value,
                        'status': 'failed',
                        'error': f"Codegen task failed with status: {codegen_task.status}"
                    }
                
                results['task_results'].append(task_result)
                
            except Exception as e:
                task.status = "failed"
                results['failed'] += 1
                
                task_result = {
                    'task_id': task.task_id,
                    'task_type': task.task_type.value,
                    'status': 'failed',
                    'error': str(e)
                }
                results['task_results'].append(task_result)
        
        return results
    
    def generate_integration_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive integration report."""
        report = {
            'metadata': {
                'repository_path': str(self.repo_path),
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'codegen_org_id': self.org_id,
                'integration_version': '1.0.0'
            },
            'analysis_insights': [asdict(insight) for insight in self.insights],
            'automation_tasks': [asdict(task) for task in self.tasks],
            'summary': {
                'total_insights': len(self.insights),
                'automatable_insights': len([i for i in self.insights if i.automation_feasible]),
                'total_tasks_created': len(self.tasks),
                'high_priority_tasks': len([t for t in self.tasks if t.priority >= 7]),
                'estimated_total_effort_hours': sum(t.estimated_effort_hours for t in self.tasks)
            },
            'recommendations': self._generate_integration_recommendations()
        }
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"Integration report saved to: {output_file}")
        
        return report
    
    def _generate_integration_recommendations(self) -> List[str]:
        """Generate recommendations for the integration."""
        recommendations = []
        
        high_severity_insights = [i for i in self.insights if i.severity in ['high', 'critical']]
        if high_severity_insights:
            recommendations.append(
                f"Address {len(high_severity_insights)} high-severity issues first for maximum impact"
            )
        
        automatable_tasks = [t for t in self.tasks if t.risk_level == 'low']
        if automatable_tasks:
            recommendations.append(
                f"Start with {len(automatable_tasks)} low-risk automation tasks for quick wins"
            )
        
        total_effort = sum(t.estimated_effort_hours for t in self.tasks)
        if total_effort > 0:
            recommendations.append(
                f"Total estimated effort: {total_effort:.1f} hours - consider spreading across multiple sprints"
            )
        
        if not recommendations:
            recommendations.append("Codebase is in good health - consider regular automated analysis")
        
        return recommendations
    
    def run_full_integration_workflow(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete integration workflow."""
        print("Starting Graph-Sitter + Codegen SDK integration workflow...")
        
        # Step 1: Analyze codebase
        insights = self.analyze_codebase_health()
        print(f"Found {len(insights)} analysis insights")
        
        # Step 2: Create automation tasks
        tasks = self.create_automation_tasks(insights)
        print(f"Created {len(tasks)} automation tasks")
        
        # Step 3: Execute high-priority tasks
        execution_results = self.execute_automation_tasks(max_concurrent=2)
        print(f"Executed tasks: {execution_results['completed']} completed, {execution_results['failed']} failed")
        
        # Step 4: Generate report
        report = self.generate_integration_report(output_path)
        
        # Step 5: Print summary
        self._print_integration_summary(report, execution_results)
        
        return {
            'insights': insights,
            'tasks': tasks,
            'execution_results': execution_results,
            'report': report
        }
    
    def _print_integration_summary(self, report: Dict[str, Any], execution_results: Dict[str, Any]):
        """Print integration workflow summary."""
        print("\n" + "="*80)
        print("GRAPH-SITTER + CODEGEN SDK INTEGRATION SUMMARY")
        print("="*80)
        print(f"Repository: {report['metadata']['repository_path']}")
        print(f"Analysis Time: {report['metadata']['analysis_timestamp']}")
        print()
        print("ANALYSIS RESULTS:")
        print(f"  Total Insights: {report['summary']['total_insights']}")
        print(f"  Automatable: {report['summary']['automatable_insights']}")
        print(f"  Tasks Created: {report['summary']['total_tasks_created']}")
        print(f"  High Priority: {report['summary']['high_priority_tasks']}")
        print(f"  Estimated Effort: {report['summary']['estimated_total_effort_hours']:.1f} hours")
        print()
        print("EXECUTION RESULTS:")
        print(f"  Tasks Completed: {execution_results['completed']}")
        print(f"  Tasks Failed: {execution_results['failed']}")
        print(f"  Success Rate: {execution_results['completed'] / max(1, execution_results['total_tasks']) * 100:.1f}%")
        print()
        print("RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        print("="*80)


def main():
    """Main function for running the integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Graph-Sitter + Codegen SDK Integration')
    parser.add_argument('repo_path', help='Path to the repository to analyze')
    parser.add_argument('--org-id', required=True, help='Codegen organization ID')
    parser.add_argument('--token', required=True, help='Codegen API token')
    parser.add_argument('--output', '-o', help='Output file for the integration report')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, do not execute tasks')
    
    args = parser.parse_args()
    
    # Create integration
    integration = CodegenGraphSitterIntegration(
        org_id=args.org_id,
        token=args.token,
        repo_path=args.repo_path
    )
    
    if args.analyze_only:
        # Only run analysis
        insights = integration.analyze_codebase_health()
        tasks = integration.create_automation_tasks(insights)
        report = integration.generate_integration_report(args.output)
        print(f"Analysis complete. Found {len(insights)} insights and created {len(tasks)} tasks.")
    else:
        # Run full workflow
        result = integration.run_full_integration_workflow(args.output)
    
    return 0


if __name__ == '__main__':
    exit(main())

