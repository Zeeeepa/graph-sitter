#!/usr/bin/env python3
"""
Contexten Component Validator and Dead Code Analyzer

Comprehensive testing framework for contexten components that:
1. Validates component integrity and usability
2. Identifies dead code and unused imports
3. Analyzes coverage gaps and missing features
4. Tests integration points
5. Generates actionable recommendations

Usage:
    python contexten_component_validator.py
"""

import ast
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ComponentIssue:
    """Represents an issue found in a component"""
    severity: str  # 'critical', 'major', 'minor', 'info'
    category: str  # 'import', 'dead_code', 'missing_feature', 'integration', 'usability'
    description: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class ComponentMetrics:
    """Metrics for a component"""
    file_path: str
    lines_of_code: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    external_dependencies: int = 0
    internal_dependencies: int = 0
    complexity_score: float = 0.0
    test_coverage: float = 0.0
    issues: List[ComponentIssue] = field(default_factory=list)

@dataclass
class ValidationSummary:
    """Summary of validation results"""
    total_files: int = 0
    analyzed_files: int = 0
    critical_issues: int = 0
    major_issues: int = 0
    minor_issues: int = 0
    dead_code_files: List[str] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    integration_gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    components: Dict[str, ComponentMetrics] = field(default_factory=dict)

class ContextenValidator:
    """Main validator class for contexten components"""
    
    def __init__(self, base_path: str = "src/contexten"):
        self.base_path = Path(base_path)
        self.summary = ValidationSummary()
        self.dependency_graph = defaultdict(set)
        self.usage_graph = defaultdict(set)
        
    def validate_all_components(self) -> ValidationSummary:
        """Run comprehensive validation on all components"""
        logger.info("Starting comprehensive contexten component validation...")
        
        # Discover all Python files
        python_files = list(self.base_path.rglob("*.py"))
        python_files = [f for f in python_files if not f.name.startswith('__')]
        
        self.summary.total_files = len(python_files)
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        for file_path in python_files:
            try:
                metrics = self._analyze_file(file_path)
                self.summary.components[str(file_path)] = metrics
                self.summary.analyzed_files += 1
                
                # Count issues by severity
                for issue in metrics.issues:
                    if issue.severity == 'critical':
                        self.summary.critical_issues += 1
                    elif issue.severity == 'major':
                        self.summary.major_issues += 1
                    elif issue.severity == 'minor':
                        self.summary.minor_issues += 1
                        
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        # Perform cross-component analysis
        self._analyze_dependencies()
        self._detect_dead_code()
        self._identify_integration_gaps()
        self._generate_recommendations()
        
        logger.info("Validation complete!")
        return self.summary
    
    def _analyze_file(self, file_path: Path) -> ComponentMetrics:
        """Analyze a single Python file"""
        metrics = ComponentMetrics(file_path=str(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic metrics
            metrics.lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            # Parse AST
            tree = ast.parse(content)
            
            imports = []
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        metrics.imports += 1
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        full_import = f"{module}.{alias.name}" if module else alias.name
                        imports.append(full_import)
                        metrics.imports += 1
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    metrics.functions += 1
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    metrics.classes += 1
            
            # Categorize dependencies
            for imp in imports:
                if imp.startswith('contexten'):
                    metrics.internal_dependencies += 1
                    self.dependency_graph[str(file_path)].add(imp)
                elif not imp.startswith('.') and '.' in imp:
                    metrics.external_dependencies += 1
            
            # Calculate complexity score
            metrics.complexity_score = self._calculate_complexity(tree)
            
            # Detect issues
            self._detect_import_issues(file_path, content, imports, metrics)
            self._detect_dead_code_in_file(file_path, content, functions, classes, metrics)
            self._detect_missing_features(file_path, content, metrics)
            self._detect_usability_issues(file_path, content, metrics)
            
        except Exception as e:
            issue = ComponentIssue(
                severity='critical',
                category='import',
                description=f"Failed to parse file: {str(e)}",
                file_path=str(file_path),
                suggestion="Check file syntax and encoding"
            )
            metrics.issues.append(issue)
        
        return metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity score"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity / 10.0  # Normalize to 0-1 scale
    
    def _detect_import_issues(self, file_path: Path, content: str, imports: List[str], metrics: ComponentMetrics):
        """Detect import-related issues"""
        
        # Check for unused imports
        for imp in imports:
            import_name = imp.split('.')[-1]
            # Simple heuristic: if import name doesn't appear elsewhere in content
            if content.count(import_name) <= 1:  # Only in import statement
                issue = ComponentIssue(
                    severity='minor',
                    category='dead_code',
                    description=f"Potentially unused import: {imp}",
                    file_path=str(file_path),
                    suggestion=f"Remove unused import '{imp}' if not needed"
                )
                metrics.issues.append(issue)
        
        # Check for missing common imports
        if 'agent' in str(file_path).lower():
            if not any('async' in imp for imp in imports):
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Agent file missing async support imports",
                    file_path=str(file_path),
                    suggestion="Consider adding asyncio imports for async operations"
                )
                metrics.issues.append(issue)
        
        # Check for circular imports
        if str(file_path) in [imp for imp in imports if imp.startswith('contexten')]:
            issue = ComponentIssue(
                severity='major',
                category='import',
                description="Potential circular import detected",
                file_path=str(file_path),
                suggestion="Refactor to avoid circular dependencies"
            )
            metrics.issues.append(issue)
    
    def _detect_dead_code_in_file(self, file_path: Path, content: str, functions: List[str], classes: List[str], metrics: ComponentMetrics):
        """Detect dead code within a file"""
        
        # Check for unused private functions
        for func in functions:
            if func.startswith('_') and func != '__init__':
                if content.count(func) <= 1:  # Only defined, never called
                    issue = ComponentIssue(
                        severity='minor',
                        category='dead_code',
                        description=f"Potentially unused private function: {func}",
                        file_path=str(file_path),
                        suggestion=f"Remove function '{func}' if not needed"
                    )
                    metrics.issues.append(issue)
        
        # Check for empty classes
        for cls in classes:
            # Simple check for empty class bodies
            class_pattern = rf"class\s+{cls}.*?:\s*(?:pass\s*)?(?:\n|$)"
            if re.search(class_pattern, content, re.DOTALL):
                issue = ComponentIssue(
                    severity='minor',
                    category='dead_code',
                    description=f"Potentially empty class: {cls}",
                    file_path=str(file_path),
                    suggestion=f"Implement class '{cls}' or remove if not needed"
                )
                metrics.issues.append(issue)
    
    def _detect_missing_features(self, file_path: Path, content: str, metrics: ComponentMetrics):
        """Detect missing features based on file type and patterns"""
        
        file_str = str(file_path).lower()
        
        # Dashboard-specific checks
        if 'dashboard' in file_str:
            if 'websocket' not in content.lower():
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Dashboard missing WebSocket support for real-time updates",
                    file_path=str(file_path),
                    suggestion="Add WebSocket endpoints for real-time functionality"
                )
                metrics.issues.append(issue)
            
            if 'auth' not in content.lower() and 'login' not in content.lower():
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Dashboard missing authentication",
                    file_path=str(file_path),
                    suggestion="Implement authentication and authorization"
                )
                metrics.issues.append(issue)
        
        # Agent-specific checks
        if 'agent' in file_str:
            if 'error' not in content.lower() and 'exception' not in content.lower():
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Agent missing error handling",
                    file_path=str(file_path),
                    suggestion="Add comprehensive error handling and recovery"
                )
                metrics.issues.append(issue)
            
            if 'retry' not in content.lower():
                issue = ComponentIssue(
                    severity='minor',
                    category='missing_feature',
                    description="Agent missing retry logic",
                    file_path=str(file_path),
                    suggestion="Add retry logic for resilient operations"
                )
                metrics.issues.append(issue)
        
        # Integration-specific checks
        if any(service in file_str for service in ['linear', 'github', 'slack']):
            if 'rate' not in content.lower() and 'limit' not in content.lower():
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Integration missing rate limiting",
                    file_path=str(file_path),
                    suggestion="Implement rate limiting for API calls"
                )
                metrics.issues.append(issue)
            
            if 'webhook' in file_str and 'validate' not in content.lower():
                issue = ComponentIssue(
                    severity='major',
                    category='missing_feature',
                    description="Webhook handler missing validation",
                    file_path=str(file_path),
                    suggestion="Add webhook signature validation for security"
                )
                metrics.issues.append(issue)
    
    def _detect_usability_issues(self, file_path: Path, content: str, metrics: ComponentMetrics):
        """Detect usability issues"""
        
        # Check for missing docstrings
        if '"""' not in content and "'''" not in content:
            issue = ComponentIssue(
                severity='minor',
                category='usability',
                description="Missing module docstring",
                file_path=str(file_path),
                suggestion="Add module docstring for better documentation"
            )
            metrics.issues.append(issue)
        
        # Check for hardcoded values
        hardcoded_patterns = [
            r'http://localhost:\d+',
            r'https://api\.[a-zA-Z]+\.com',
            r'["\'][a-zA-Z0-9]{32,}["\']',  # Potential API keys
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, content):
                issue = ComponentIssue(
                    severity='major',
                    category='usability',
                    description="Hardcoded values detected",
                    file_path=str(file_path),
                    suggestion="Move hardcoded values to configuration"
                )
                metrics.issues.append(issue)
                break
    
    def _analyze_dependencies(self):
        """Analyze dependency relationships"""
        # Build usage graph
        for file_path, deps in self.dependency_graph.items():
            for dep in deps:
                self.usage_graph[dep].add(file_path)
    
    def _detect_dead_code(self):
        """Detect dead code across the entire codebase"""
        
        # Find files that are never imported
        all_files = set(self.summary.components.keys())
        imported_files = set()
        
        for deps in self.dependency_graph.values():
            for dep in deps:
                # Convert module name back to file path
                if dep.startswith('contexten'):
                    imported_files.add(dep)
        
        # Files that might be dead code
        for file_path in all_files:
            # Convert file path to module name for comparison
            module_name = self._file_path_to_module(file_path)
            
            if module_name not in imported_files:
                # Check if it's an entry point (has main, CLI, or app)
                metrics = self.summary.components[file_path]
                content = ""
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    continue
                
                is_entry_point = any(pattern in content for pattern in [
                    'if __name__ == "__main__"',
                    'def main(',
                    'app = ',
                    'cli = ',
                    'FastAPI(',
                    'Flask('
                ])
                
                if not is_entry_point:
                    self.summary.dead_code_files.append(file_path)
    
    def _file_path_to_module(self, file_path: str) -> str:
        """Convert file path to module name"""
        path = Path(file_path)
        if path.suffix == '.py':
            parts = path.parts
            # Find 'src' in path and start from there
            try:
                src_index = parts.index('src')
                module_parts = parts[src_index + 1:]
                if module_parts[-1].endswith('.py'):
                    module_parts = module_parts[:-1] + (module_parts[-1][:-3],)
                return '.'.join(module_parts)
            except ValueError:
                return str(path.stem)
        return str(path.stem)
    
    def _identify_integration_gaps(self):
        """Identify gaps in integration between components"""
        
        # Check for missing integration patterns
        linear_files = [f for f in self.summary.components.keys() if 'linear' in f]
        github_files = [f for f in self.summary.components.keys() if 'github' in f]
        slack_files = [f for f in self.summary.components.keys() if 'slack' in f]
        dashboard_files = [f for f in self.summary.components.keys() if 'dashboard' in f]
        
        # Linear integration gaps
        if linear_files:
            has_webhook = any('webhook' in f for f in linear_files)
            has_client = any('client' in f for f in linear_files)
            has_agent = any('agent' in f for f in linear_files)
            
            if not has_webhook:
                self.summary.integration_gaps.append("Linear integration missing webhook handling")
            if not has_client:
                self.summary.integration_gaps.append("Linear integration missing API client")
            if not has_agent:
                self.summary.integration_gaps.append("Linear integration missing agent implementation")
        
        # GitHub integration gaps
        if github_files:
            has_webhook = any('webhook' in f for f in github_files)
            has_events = any('event' in f for f in github_files)
            
            if not has_webhook:
                self.summary.integration_gaps.append("GitHub integration missing webhook handling")
            if not has_events:
                self.summary.integration_gaps.append("GitHub integration missing event processing")
        
        # Dashboard integration gaps
        if dashboard_files:
            has_api = any('api' in f or 'app' in f for f in dashboard_files)
            
            if not has_api:
                self.summary.integration_gaps.append("Dashboard missing API implementation")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Dead code recommendations
        if self.summary.dead_code_files:
            recommendations.append(f"🗑️ Remove or refactor {len(self.summary.dead_code_files)} potentially dead code files")
        
        # Critical issues
        if self.summary.critical_issues > 0:
            recommendations.append(f"🚨 Address {self.summary.critical_issues} critical issues immediately")
        
        # Major issues
        if self.summary.major_issues > 0:
            recommendations.append(f"⚠️ Fix {self.summary.major_issues} major issues for better reliability")
        
        # Integration gaps
        if self.summary.integration_gaps:
            recommendations.append(f"🔗 Address {len(self.summary.integration_gaps)} integration gaps")
        
        # Missing dependencies
        missing_deps = set()
        for metrics in self.summary.components.values():
            for issue in metrics.issues:
                if 'No module named' in issue.description:
                    dep = issue.description.split("'")[1] if "'" in issue.description else ""
                    if dep:
                        missing_deps.add(dep)
        
        if missing_deps:
            self.summary.missing_dependencies = list(missing_deps)
            recommendations.append(f"📦 Install {len(missing_deps)} missing dependencies: {', '.join(list(missing_deps)[:3])}...")
        
        # Code quality
        total_issues = self.summary.critical_issues + self.summary.major_issues + self.summary.minor_issues
        if total_issues > 50:
            recommendations.append("🔧 Consider implementing automated code quality checks")
        
        self.summary.recommendations = recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        
        # Header
        report.append("# Contexten Component Validation Report\n")
        report.append(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Executive Summary
        report.append("## 📊 Executive Summary")
        report.append(f"- **Total Files**: {self.summary.total_files}")
        report.append(f"- **Analyzed Files**: {self.summary.analyzed_files}")
        report.append(f"- **Critical Issues**: {self.summary.critical_issues}")
        report.append(f"- **Major Issues**: {self.summary.major_issues}")
        report.append(f"- **Minor Issues**: {self.summary.minor_issues}")
        report.append(f"- **Dead Code Files**: {len(self.summary.dead_code_files)}")
        report.append(f"- **Integration Gaps**: {len(self.summary.integration_gaps)}")
        report.append("")
        
        # Recommendations
        if self.summary.recommendations:
            report.append("## 🎯 Key Recommendations")
            for rec in self.summary.recommendations:
                report.append(f"- {rec}")
            report.append("")
        
        # Missing Dependencies
        if self.summary.missing_dependencies:
            report.append("## 📦 Missing Dependencies")
            for dep in self.summary.missing_dependencies:
                report.append(f"- `{dep}`")
            report.append("")
        
        # Integration Gaps
        if self.summary.integration_gaps:
            report.append("## 🔗 Integration Gaps")
            for gap in self.summary.integration_gaps:
                report.append(f"- ❌ {gap}")
            report.append("")
        
        # Dead Code Analysis
        if self.summary.dead_code_files:
            report.append("## 🗑️ Potential Dead Code")
            for file_path in self.summary.dead_code_files[:10]:  # Show first 10
                report.append(f"- `{file_path}`")
            if len(self.summary.dead_code_files) > 10:
                report.append(f"- ... and {len(self.summary.dead_code_files) - 10} more files")
            report.append("")
        
        # Critical Issues
        critical_issues = []
        for metrics in self.summary.components.values():
            for issue in metrics.issues:
                if issue.severity == 'critical':
                    critical_issues.append(issue)
        
        if critical_issues:
            report.append("## 🚨 Critical Issues")
            for issue in critical_issues[:10]:  # Show first 10
                report.append(f"### {issue.file_path}")
                report.append(f"- **Issue**: {issue.description}")
                if issue.suggestion:
                    report.append(f"- **Suggestion**: {issue.suggestion}")
                report.append("")
        
        # Component Metrics Summary
        report.append("## 📈 Component Metrics")
        report.append("| Component | LOC | Functions | Classes | Issues |")
        report.append("|-----------|-----|-----------|---------|--------|")
        
        for file_path, metrics in list(self.summary.components.items())[:20]:  # Show first 20
            issues_count = len(metrics.issues)
            short_path = file_path.split('/')[-2:] if '/' in file_path else [file_path]
            short_path_str = '/'.join(short_path)
            report.append(f"| {short_path_str} | {metrics.lines_of_code} | {metrics.functions} | {metrics.classes} | {issues_count} |")
        
        if len(self.summary.components) > 20:
            report.append(f"| ... and {len(self.summary.components) - 20} more components | | | | |")
        
        report.append("")
        
        return "\n".join(report)
    
    def generate_fixes(self) -> Dict[str, List[str]]:
        """Generate automated fixes for common issues"""
        fixes = defaultdict(list)
        
        for file_path, metrics in self.summary.components.items():
            for issue in metrics.issues:
                if issue.category == 'dead_code' and 'unused import' in issue.description:
                    # Generate fix for unused imports
                    import_name = issue.description.split(': ')[1]
                    fixes[file_path].append(f"Remove unused import: {import_name}")
                
                elif issue.category == 'missing_feature' and 'missing' in issue.description.lower():
                    # Generate fix suggestions for missing features
                    fixes[file_path].append(f"Implement: {issue.suggestion}")
        
        return dict(fixes)

def main():
    """Main entry point"""
    print("🔍 Starting Contexten Component Validation...")
    
    # Initialize validator
    validator = ContextenValidator()
    
    # Run validation
    summary = validator.validate_all_components()
    
    # Generate report
    report = validator.generate_report()
    
    # Save report
    report_file = "contexten_validation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Generate fixes
    fixes = validator.generate_fixes()
    fixes_file = "contexten_fixes.json"
    with open(fixes_file, 'w', encoding='utf-8') as f:
        json.dump(fixes, f, indent=2)
    
    # Print summary
    print(f"\n📊 Validation Complete!")
    print(f"📁 Analyzed: {summary.analyzed_files}/{summary.total_files} files")
    print(f"🚨 Critical: {summary.critical_issues}")
    print(f"⚠️  Major: {summary.major_issues}")
    print(f"ℹ️  Minor: {summary.minor_issues}")
    print(f"🗑️  Dead code: {len(summary.dead_code_files)} files")
    print(f"🔗 Integration gaps: {len(summary.integration_gaps)}")
    print(f"📄 Report: {report_file}")
    print(f"🔧 Fixes: {fixes_file}")
    
    # Print top recommendations
    if summary.recommendations:
        print(f"\n🎯 Top Recommendations:")
        for rec in summary.recommendations[:3]:
            print(f"  {rec}")

if __name__ == "__main__":
    main()

