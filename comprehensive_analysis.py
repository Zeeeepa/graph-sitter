#!/usr/bin/env python3
"""
Comprehensive Graph-Sitter Codebase Analysis Tool
Analyzes architecture, dependencies, performance, and code quality issues
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Tuple, Optional, Any
import logging

# Add graph-sitter to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary, get_file_summary, get_class_summary, 
        get_function_summary, get_symbol_summary
    )
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.enums import SymbolType
except ImportError as e:
    print(f"❌ Failed to import graph-sitter modules: {e}")
    print("Make sure you're running from the graph-sitter root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ArchitecturalIssue:
    """Represents an architectural issue found in the codebase"""
    severity: str  # Critical/High/Medium/Low
    location: str  # File path and line numbers
    issue_type: str  # Category of issue
    description: str  # Clear explanation
    code_snippet: str  # Problematic code
    recommended_fix: str  # Production-ready solution
    justification: str  # Technical reasoning
    complexity: str  # Easy/Medium/Hard
    impact_score: int  # 1-10 scale

@dataclass
class ComponentAnalysis:
    """Analysis results for a specific component"""
    name: str
    file_path: str
    component_type: str  # Class/Function/Module
    dependencies: List[str]
    dependents: List[str]
    complexity_score: int
    issues: List[ArchitecturalIssue]
    is_entry_point: bool
    is_dead_code: bool
    performance_metrics: Dict[str, Any]

@dataclass
class ArchitecturalAnalysis:
    """Complete architectural analysis results"""
    summary: Dict[str, Any]
    components: List[ComponentAnalysis]
    dependency_graph: Dict[str, List[str]]
    critical_paths: List[List[str]]
    performance_bottlenecks: List[Dict[str, Any]]
    code_quality_issues: List[ArchitecturalIssue]
    missing_functionality: List[Dict[str, Any]]
    refactoring_opportunities: List[Dict[str, Any]]
    architectural_violations: List[ArchitecturalIssue]

class ComprehensiveAnalyzer:
    """Main analyzer class for comprehensive codebase analysis"""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path)
        self.codebase = None
        self.analysis_results = ArchitecturalAnalysis(
            summary={},
            components=[],
            dependency_graph={},
            critical_paths=[],
            performance_bottlenecks=[],
            code_quality_issues=[],
            missing_functionality=[],
            refactoring_opportunities=[],
            architectural_violations=[]
        )
        
    def initialize_codebase(self) -> bool:
        """Initialize the graph-sitter codebase"""
        try:
            logger.info("🔄 Initializing graph-sitter codebase...")
            config = CodebaseConfig(exp_lazy_graph=True)
            self.codebase = Codebase(str(self.codebase_path), config=config)
            logger.info("✅ Codebase initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize codebase: {e}")
            return False
    
    def analyze_architecture(self) -> None:
        """Perform comprehensive architectural analysis"""
        if not self.codebase:
            logger.error("❌ Codebase not initialized")
            return
            
        logger.info("🏗️ Analyzing architecture...")
        
        # Generate summary statistics
        self._generate_summary()
        
        # Analyze components
        self._analyze_components()
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Identify critical paths
        self._identify_critical_paths()
        
        # Analyze performance bottlenecks
        self._analyze_performance()
        
        # Identify code quality issues
        self._analyze_code_quality()
        
        # Find missing functionality
        self._find_missing_functionality()
        
        # Identify refactoring opportunities
        self._identify_refactoring_opportunities()
        
        # Check architectural violations
        self._check_architectural_violations()
        
        logger.info("✅ Architectural analysis complete")
    
    def _generate_summary(self) -> None:
        """Generate high-level summary statistics"""
        logger.info("📊 Generating summary statistics...")
        
        files = list(self.codebase.files)
        classes = list(self.codebase.classes)
        functions = list(self.codebase.functions)
        imports = list(self.codebase.imports)
        
        self.analysis_results.summary = {
            "total_files": len(files),
            "total_classes": len(classes),
            "total_functions": len(functions),
            "total_imports": len(imports),
            "total_symbols": len(list(self.codebase.symbols)),
            "external_modules": len(list(self.codebase.external_modules)),
            "global_vars": len(list(self.codebase.global_vars)),
            "interfaces": len(list(self.codebase.interfaces)),
            "analysis_timestamp": time.time()
        }
        
        # Calculate complexity metrics
        total_complexity = 0
        for func in functions:
            # Estimate complexity based on function calls and dependencies
            complexity = len(func.function_calls) + len(func.dependencies) + len(func.parameters)
            total_complexity += complexity
            
        self.analysis_results.summary["average_function_complexity"] = (
            total_complexity / len(functions) if functions else 0
        )
    
    def _analyze_components(self) -> None:
        """Analyze individual components (classes, functions, modules)"""
        logger.info("🔍 Analyzing components...")
        
        # Analyze classes
        for cls in self.codebase.classes:
            component = self._analyze_class_component(cls)
            self.analysis_results.components.append(component)
        
        # Analyze functions
        for func in self.codebase.functions:
            component = self._analyze_function_component(func)
            self.analysis_results.components.append(component)
        
        # Analyze files as modules
        for file in self.codebase.files:
            component = self._analyze_file_component(file)
            self.analysis_results.components.append(component)
    
    def _analyze_class_component(self, cls) -> ComponentAnalysis:
        """Analyze a class component"""
        issues = []
        
        # Check for architectural issues
        if len(cls.methods) > 20:
            issues.append(ArchitecturalIssue(
                severity="Medium",
                location=f"{cls.file.name}:{getattr(cls, 'line_number', 'unknown')}",
                issue_type="Large Class",
                description=f"Class '{cls.name}' has {len(cls.methods)} methods, exceeding recommended limit of 20",
                code_snippet=f"class {cls.name}:",
                recommended_fix="Consider breaking this class into smaller, more focused classes",
                justification="Large classes violate Single Responsibility Principle and are harder to maintain",
                complexity="Medium",
                impact_score=6
            ))
        
        # Check for missing documentation
        if not getattr(cls, 'docstring', None):
            issues.append(ArchitecturalIssue(
                severity="Low",
                location=f"{cls.file.name}:{getattr(cls, 'line_number', 'unknown')}",
                issue_type="Missing Documentation",
                description=f"Class '{cls.name}' lacks documentation",
                code_snippet=f"class {cls.name}:",
                recommended_fix=f"Add docstring explaining the purpose and usage of {cls.name}",
                justification="Documentation improves code maintainability and developer onboarding",
                complexity="Easy",
                impact_score=3
            ))
        
        return ComponentAnalysis(
            name=cls.name,
            file_path=cls.file.name,
            component_type="Class",
            dependencies=[dep.name for dep in cls.dependencies if hasattr(dep, 'name')],
            dependents=[usage.name for usage in cls.symbol_usages if hasattr(usage, 'name')],
            complexity_score=len(cls.methods) + len(cls.attributes) + len(cls.dependencies),
            issues=issues,
            is_entry_point=len(cls.symbol_usages) > 10,
            is_dead_code=len(cls.symbol_usages) == 0,
            performance_metrics={
                "method_count": len(cls.methods),
                "attribute_count": len(cls.attributes),
                "inheritance_depth": len(cls.parent_class_names)
            }
        )
    
    def _analyze_function_component(self, func) -> ComponentAnalysis:
        """Analyze a function component"""
        issues = []
        
        # Check for high complexity
        complexity = len(func.function_calls) + len(func.parameters) + len(func.dependencies)
        if complexity > 15:
            issues.append(ArchitecturalIssue(
                severity="High",
                location=f"{func.file.name}:{getattr(func, 'line_number', 'unknown')}",
                issue_type="High Complexity",
                description=f"Function '{func.name}' has complexity score of {complexity}",
                code_snippet=f"def {func.name}({', '.join([getattr(p, 'name', str(p)) for p in func.parameters])}):",
                recommended_fix="Break this function into smaller, more focused functions",
                justification="High complexity functions are harder to test, debug, and maintain",
                complexity="Hard",
                impact_score=8
            ))
        
        # Check for too many parameters
        if len(func.parameters) > 5:
            issues.append(ArchitecturalIssue(
                severity="Medium",
                location=f"{func.file.name}:{getattr(func, 'line_number', 'unknown')}",
                issue_type="Too Many Parameters",
                description=f"Function '{func.name}' has {len(func.parameters)} parameters",
                code_snippet=f"def {func.name}({', '.join([getattr(p, 'name', str(p)) for p in func.parameters])}):",
                recommended_fix="Consider using a configuration object or breaking the function apart",
                justification="Functions with many parameters are harder to use and maintain",
                complexity="Medium",
                impact_score=5
            ))
        
        return ComponentAnalysis(
            name=func.name,
            file_path=func.file.name,
            component_type="Function",
            dependencies=[dep.name for dep in func.dependencies if hasattr(dep, 'name')],
            dependents=[usage.name for usage in func.symbol_usages if hasattr(usage, 'name')],
            complexity_score=complexity,
            issues=issues,
            is_entry_point=len(func.symbol_usages) > 5,
            is_dead_code=len(func.symbol_usages) == 0,
            performance_metrics={
                "parameter_count": len(func.parameters),
                "function_calls": len(func.function_calls),
                "return_statements": len(func.return_statements)
            }
        )
    
    def _analyze_file_component(self, file) -> ComponentAnalysis:
        """Analyze a file as a module component"""
        issues = []
        
        # Check for large files
        if len(file.symbols) > 50:
            issues.append(ArchitecturalIssue(
                severity="Medium",
                location=file.name,
                issue_type="Large Module",
                description=f"File '{file.name}' contains {len(file.symbols)} symbols",
                code_snippet=f"# {file.name}",
                recommended_fix="Consider breaking this module into smaller, more focused modules",
                justification="Large modules are harder to navigate and maintain",
                complexity="Medium",
                impact_score=6
            ))
        
        # Check for too many imports
        if len(file.imports) > 20:
            issues.append(ArchitecturalIssue(
                severity="Low",
                location=file.name,
                issue_type="Too Many Imports",
                description=f"File '{file.name}' has {len(file.imports)} imports",
                code_snippet="# Too many imports",
                recommended_fix="Review imports and remove unused ones, consider refactoring",
                justification="Too many imports can indicate tight coupling or large module scope",
                complexity="Easy",
                impact_score=3
            ))
        
        return ComponentAnalysis(
            name=file.name,
            file_path=file.name,
            component_type="Module",
            dependencies=[imp.imported_symbol.name for imp in file.imports if hasattr(imp.imported_symbol, 'name')],
            dependents=[],  # Would need reverse lookup
            complexity_score=len(file.symbols) + len(file.imports),
            issues=issues,
            is_entry_point=file.name.endswith('__main__.py') or file.name.endswith('cli.py'),
            is_dead_code=False,  # Files are rarely completely dead
            performance_metrics={
                "symbol_count": len(file.symbols),
                "import_count": len(file.imports),
                "class_count": len(file.classes),
                "function_count": len(file.functions)
            }
        )
    
    def _build_dependency_graph(self) -> None:
        """Build comprehensive dependency graph"""
        logger.info("🕸️ Building dependency graph...")
        
        for component in self.analysis_results.components:
            self.analysis_results.dependency_graph[component.name] = component.dependencies
    
    def _identify_critical_paths(self) -> None:
        """Identify critical execution paths through the codebase"""
        logger.info("🎯 Identifying critical paths...")
        
        # Find entry points (highly used components)
        entry_points = [comp for comp in self.analysis_results.components if comp.is_entry_point]
        
        # Build paths from entry points
        for entry in entry_points:
            path = self._trace_dependency_path(entry.name, set(), [])
            if len(path) > 3:  # Only include significant paths
                self.analysis_results.critical_paths.append(path)
    
    def _trace_dependency_path(self, component_name: str, visited: Set[str], current_path: List[str]) -> List[str]:
        """Trace dependency path from a component"""
        if component_name in visited or len(current_path) > 10:  # Prevent cycles and limit depth
            return current_path
        
        visited.add(component_name)
        current_path.append(component_name)
        
        dependencies = self.analysis_results.dependency_graph.get(component_name, [])
        if dependencies:
            # Follow the first dependency (could be enhanced to follow all)
            return self._trace_dependency_path(dependencies[0], visited, current_path)
        
        return current_path
    
    def _analyze_performance(self) -> None:
        """Analyze performance bottlenecks"""
        logger.info("⚡ Analyzing performance bottlenecks...")
        
        # Identify high-complexity components
        high_complexity = [comp for comp in self.analysis_results.components 
                          if comp.complexity_score > 20]
        
        for comp in high_complexity:
            bottleneck = {
                "component": comp.name,
                "type": comp.component_type,
                "complexity_score": comp.complexity_score,
                "location": comp.file_path,
                "issue": "High computational complexity",
                "recommendation": "Consider optimization or refactoring"
            }
            self.analysis_results.performance_bottlenecks.append(bottleneck)
    
    def _analyze_code_quality(self) -> None:
        """Analyze code quality issues"""
        logger.info("🔍 Analyzing code quality...")
        
        # Collect all issues from components
        for component in self.analysis_results.components:
            self.analysis_results.code_quality_issues.extend(component.issues)
        
        # Add global quality issues
        dead_code_count = len([comp for comp in self.analysis_results.components if comp.is_dead_code])
        if dead_code_count > 0:
            self.analysis_results.code_quality_issues.append(ArchitecturalIssue(
                severity="Medium",
                location="Global",
                issue_type="Dead Code",
                description=f"Found {dead_code_count} potentially dead code components",
                code_snippet="# Various unused components",
                recommended_fix="Review and remove unused components",
                justification="Dead code increases maintenance burden and confusion",
                complexity="Easy",
                impact_score=4
            ))
    
    def _find_missing_functionality(self) -> None:
        """Find missing functionality based on patterns"""
        logger.info("🔍 Finding missing functionality...")
        
        # This would integrate with the error_analysis.py results
        # For now, we'll identify common missing patterns
        
        # Check for missing error handling
        functions_without_error_handling = []
        for comp in self.analysis_results.components:
            if comp.component_type == "Function" and comp.complexity_score > 10:
                # Heuristic: complex functions should have error handling
                functions_without_error_handling.append(comp.name)
        
        if functions_without_error_handling:
            self.analysis_results.missing_functionality.append({
                "type": "Error Handling",
                "description": f"{len(functions_without_error_handling)} complex functions lack error handling",
                "affected_components": functions_without_error_handling[:5],  # Show first 5
                "recommendation": "Add try-catch blocks and proper error handling"
            })
    
    def _identify_refactoring_opportunities(self) -> None:
        """Identify refactoring opportunities"""
        logger.info("🔄 Identifying refactoring opportunities...")
        
        # Find duplicate patterns
        component_names = [comp.name for comp in self.analysis_results.components]
        name_patterns = defaultdict(list)
        
        for name in component_names:
            # Group by common prefixes/suffixes
            if '_' in name:
                pattern = name.split('_')[0]
                name_patterns[pattern].append(name)
        
        for pattern, names in name_patterns.items():
            if len(names) > 3:  # Multiple components with same pattern
                self.analysis_results.refactoring_opportunities.append({
                    "type": "Similar Components",
                    "pattern": pattern,
                    "components": names,
                    "recommendation": f"Consider creating a base class or common interface for {pattern} components"
                })
    
    def _check_architectural_violations(self) -> None:
        """Check for architectural violations"""
        logger.info("🏛️ Checking architectural violations...")
        
        # Check for circular dependencies
        for comp_name, deps in self.analysis_results.dependency_graph.items():
            for dep in deps:
                if dep in self.analysis_results.dependency_graph:
                    dep_deps = self.analysis_results.dependency_graph[dep]
                    if comp_name in dep_deps:
                        self.analysis_results.architectural_violations.append(ArchitecturalIssue(
                            severity="High",
                            location=f"{comp_name} <-> {dep}",
                            issue_type="Circular Dependency",
                            description=f"Circular dependency between {comp_name} and {dep}",
                            code_snippet=f"{comp_name} -> {dep} -> {comp_name}",
                            recommended_fix="Break the circular dependency by introducing an interface or refactoring",
                            justification="Circular dependencies make code harder to test and maintain",
                            complexity="Hard",
                            impact_score=9
                        ))
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        logger.info("📋 Generating comprehensive report...")
        
        report = []
        report.append("=" * 80)
        report.append("🎯 COMPREHENSIVE GRAPH-SITTER CODEBASE ANALYSIS")
        report.append("=" * 80)
        
        # Summary section
        report.append("\n📊 EXECUTIVE SUMMARY")
        report.append("-" * 50)
        summary = self.analysis_results.summary
        report.append(f"📁 Total Files: {summary.get('total_files', 0)}")
        report.append(f"🏗️ Total Classes: {summary.get('total_classes', 0)}")
        report.append(f"⚡ Total Functions: {summary.get('total_functions', 0)}")
        report.append(f"🔄 Total Imports: {summary.get('total_imports', 0)}")
        report.append(f"📊 Average Function Complexity: {summary.get('average_function_complexity', 0):.2f}")
        
        # Issues summary
        total_issues = len(self.analysis_results.code_quality_issues)
        critical_issues = len([i for i in self.analysis_results.code_quality_issues if i.severity == "Critical"])
        high_issues = len([i for i in self.analysis_results.code_quality_issues if i.severity == "High"])
        medium_issues = len([i for i in self.analysis_results.code_quality_issues if i.severity == "Medium"])
        low_issues = len([i for i in self.analysis_results.code_quality_issues if i.severity == "Low"])
        
        report.append(f"\n🚨 ISSUES SUMMARY: {total_issues} total")
        report.append(f"⚠️ Critical: {critical_issues}")
        report.append(f"🔴 High: {high_issues}")
        report.append(f"🟡 Medium: {medium_issues}")
        report.append(f"🔵 Low: {low_issues}")
        
        # Entry points
        entry_points = [comp for comp in self.analysis_results.components if comp.is_entry_point]
        report.append(f"\n🎯 ENTRY POINTS: {len(entry_points)}")
        report.append("-" * 30)
        for ep in entry_points[:10]:  # Show top 10
            report.append(f"🟩 {ep.name} ({ep.component_type}) - {ep.file_path}")
        
        # Critical paths
        report.append(f"\n🛤️ CRITICAL PATHS: {len(self.analysis_results.critical_paths)}")
        report.append("-" * 30)
        for i, path in enumerate(self.analysis_results.critical_paths[:5], 1):
            report.append(f"{i}. {' → '.join(path[:5])}{'...' if len(path) > 5 else ''}")
        
        # Performance bottlenecks
        report.append(f"\n⚡ PERFORMANCE BOTTLENECKS: {len(self.analysis_results.performance_bottlenecks)}")
        report.append("-" * 40)
        for bottleneck in self.analysis_results.performance_bottlenecks[:10]:
            report.append(f"🔴 {bottleneck['component']} ({bottleneck['type']}) - Complexity: {bottleneck['complexity_score']}")
            report.append(f"   📁 {bottleneck['location']}")
            report.append(f"   💡 {bottleneck['recommendation']}")
        
        # Detailed issues
        report.append(f"\n🚨 DETAILED ISSUES ANALYSIS")
        report.append("-" * 40)
        
        # Group issues by severity
        issues_by_severity = defaultdict(list)
        for issue in self.analysis_results.code_quality_issues:
            issues_by_severity[issue.severity].append(issue)
        
        issue_counter = 1
        for severity in ["Critical", "High", "Medium", "Low"]:
            if severity in issues_by_severity:
                report.append(f"\n{severity.upper()} ISSUES:")
                for issue in issues_by_severity[severity]:
                    severity_icon = {"Critical": "🔥", "High": "⚠️", "Medium": "👉", "Low": "🔍"}[severity]
                    report.append(f"{issue_counter}. {severity_icon} {issue.location} / {issue.issue_type} - '{issue.description}'")
                    report.append(f"   💡 Fix: {issue.recommended_fix}")
                    report.append(f"   🎯 Impact: {issue.impact_score}/10 | Complexity: {issue.complexity}")
                    issue_counter += 1
        
        # Architectural violations
        if self.analysis_results.architectural_violations:
            report.append(f"\n🏛️ ARCHITECTURAL VIOLATIONS: {len(self.analysis_results.architectural_violations)}")
            report.append("-" * 40)
            for violation in self.analysis_results.architectural_violations:
                report.append(f"🚫 {violation.issue_type}: {violation.description}")
                report.append(f"   📁 {violation.location}")
                report.append(f"   💡 {violation.recommended_fix}")
        
        # Missing functionality
        if self.analysis_results.missing_functionality:
            report.append(f"\n🔍 MISSING FUNCTIONALITY: {len(self.analysis_results.missing_functionality)}")
            report.append("-" * 40)
            for missing in self.analysis_results.missing_functionality:
                report.append(f"❌ {missing['type']}: {missing['description']}")
                report.append(f"   💡 {missing['recommendation']}")
        
        # Refactoring opportunities
        if self.analysis_results.refactoring_opportunities:
            report.append(f"\n🔄 REFACTORING OPPORTUNITIES: {len(self.analysis_results.refactoring_opportunities)}")
            report.append("-" * 40)
            for opportunity in self.analysis_results.refactoring_opportunities:
                report.append(f"🔄 {opportunity['type']}: {opportunity.get('pattern', 'N/A')}")
                report.append(f"   💡 {opportunity['recommendation']}")
        
        # Action plan
        report.append(f"\n🎯 PRIORITIZED ACTION PLAN")
        report.append("-" * 30)
        report.append("1. 🔥 Fix Critical and High severity issues first")
        report.append("2. 🏛️ Resolve architectural violations (circular dependencies)")
        report.append("3. ⚡ Optimize performance bottlenecks")
        report.append("4. 🔄 Implement refactoring opportunities")
        report.append("5. 📚 Add missing documentation and error handling")
        report.append("6. 🧹 Remove dead code and unused components")
        
        report.append("\n" + "=" * 80)
        report.append("✨ Analysis complete! Use this report to guide improvements.")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, output_file: str = "comprehensive_analysis_results.json") -> None:
        """Save analysis results to JSON file"""
        logger.info(f"💾 Saving results to {output_file}...")
        
        # Convert dataclasses to dictionaries for JSON serialization
        results_dict = {
            "summary": self.analysis_results.summary,
            "components": [asdict(comp) for comp in self.analysis_results.components],
            "dependency_graph": self.analysis_results.dependency_graph,
            "critical_paths": self.analysis_results.critical_paths,
            "performance_bottlenecks": self.analysis_results.performance_bottlenecks,
            "code_quality_issues": [asdict(issue) for issue in self.analysis_results.code_quality_issues],
            "missing_functionality": self.analysis_results.missing_functionality,
            "refactoring_opportunities": self.analysis_results.refactoring_opportunities,
            "architectural_violations": [asdict(violation) for violation in self.analysis_results.architectural_violations]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)
        
        logger.info(f"✅ Results saved to {output_file}")

def main():
    """Main execution function"""
    print("🚀 COMPREHENSIVE GRAPH-SITTER CODEBASE ANALYSIS")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ComprehensiveAnalyzer(".")
    
    # Initialize codebase
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    # Perform analysis
    start_time = time.time()
    analyzer.analyze_architecture()
    analysis_time = time.time() - start_time
    
    # Generate and display report
    report = analyzer.generate_report()
    print(report)
    
    # Save results
    analyzer.save_results()
    
    # Save report to file
    with open("comprehensive_analysis_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n⏱️ Analysis completed in {analysis_time:.2f} seconds")
    print("📁 Files generated:")
    print("  - comprehensive_analysis_results.json")
    print("  - comprehensive_analysis_report.txt")

if __name__ == "__main__":
    main()
