#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Demo

This script demonstrates the full Analysis API functionality by running
a comprehensive analysis and generating detailed issue lists as requested.
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

# Add src to path
sys.path.insert(0, 'src')

class CodebaseIssue:
    """Represents a codebase issue with severity and location."""
    
    def __init__(self, severity: str, file_path: str, description: str, 
                 line_number: Optional[int] = None, function_name: Optional[str] = None):
        self.severity = severity
        self.file_path = file_path
        self.description = description
        self.line_number = line_number
        self.function_name = function_name
        
    def __str__(self):
        location = self.file_path
        if self.line_number:
            location += f":{self.line_number}"
        if self.function_name:
            location += f" in {self.function_name}()"
        return f"Severity: {self.severity} {location} {self.description}"

class ComprehensiveAnalyzer:
    """Comprehensive codebase analyzer that finds real issues."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.issues = []
        self.stats = {
            'total_files': 0,
            'total_python_files': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_lines': 0,
            'total_imports': 0
        }
        self.function_usage = defaultdict(set)  # function_name -> set of files using it
        self.function_definitions = {}  # function_name -> (file, line_number)
        self.import_usage = defaultdict(set)  # import_name -> set of files using it
        self.import_definitions = defaultdict(set)  # import_name -> set of files defining it
        
    def analyze_codebase(self) -> Dict[str, Any]:
        """Run comprehensive analysis on the codebase."""
        print("🔍 Starting comprehensive codebase analysis...")
        
        # Phase 1: Collect all Python files and basic stats
        python_files = self._collect_python_files()
        print(f"📁 Found {len(python_files)} Python files")
        
        # Phase 2: Parse files and extract information
        for file_path in python_files:
            self._analyze_file(file_path)
            
        # Phase 3: Find issues
        self._find_unused_functions()
        self._find_unused_imports()
        self._find_code_quality_issues()
        self._find_complexity_issues()
        self._find_naming_issues()
        self._find_documentation_issues()
        self._find_security_issues()
        self._find_performance_issues()
        
        # Phase 4: Generate comprehensive report
        return self._generate_report()
    
    def _collect_python_files(self) -> List[Path]:
        """Collect all Python files in the repository."""
        python_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
                    self.stats['total_python_files'] += 1
                    
                self.stats['total_files'] += 1
                
        return python_files
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Count lines
            lines = content.split('\n')
            self.stats['total_lines'] += len(lines)
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path, content, lines)
            except SyntaxError as e:
                self.issues.append(CodebaseIssue(
                    "High", str(file_path), f"Syntax error: {e.msg}", e.lineno
                ))
                
        except Exception as e:
            self.issues.append(CodebaseIssue(
                "Medium", str(file_path), f"File analysis failed: {str(e)}"
            ))
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path, content: str, lines: List[str]):
        """Analyze the AST of a file."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node, file_path, lines)
            elif isinstance(node, ast.ClassDef):
                self._analyze_class(node, file_path, lines)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._analyze_import(node, file_path)
            elif isinstance(node, ast.Call):
                self._analyze_function_call(node, file_path)
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str]):
        """Analyze a function definition."""
        self.stats['total_functions'] += 1
        
        func_name = node.name
        self.function_definitions[func_name] = (str(file_path), node.lineno)
        
        # Check function complexity
        complexity = self._calculate_complexity(node)
        if complexity > 10:
            self.issues.append(CodebaseIssue(
                "Medium", str(file_path), 
                f"Function '{func_name}' has high cyclomatic complexity ({complexity}). Consider refactoring.",
                node.lineno, func_name
            ))
        
        # Check function length
        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
        if func_lines > 50:
            self.issues.append(CodebaseIssue(
                "Low", str(file_path),
                f"Function '{func_name}' is too long ({func_lines} lines). Consider breaking it down.",
                node.lineno, func_name
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append(CodebaseIssue(
                "Low", str(file_path),
                f"Function '{func_name}' missing docstring documentation.",
                node.lineno, func_name
            ))
        
        # Check parameter count
        if len(node.args.args) > 7:
            self.issues.append(CodebaseIssue(
                "Medium", str(file_path),
                f"Function '{func_name}' has too many parameters ({len(node.args.args)}). Consider using a config object.",
                node.lineno, func_name
            ))
    
    def _analyze_class(self, node: ast.ClassDef, file_path: Path, lines: List[str]):
        """Analyze a class definition."""
        self.stats['total_classes'] += 1
        
        class_name = node.name
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append(CodebaseIssue(
                "Low", str(file_path),
                f"Class '{class_name}' missing docstring documentation.",
                node.lineno
            ))
        
        # Check class size
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 20:
            self.issues.append(CodebaseIssue(
                "Medium", str(file_path),
                f"Class '{class_name}' has too many methods ({len(methods)}). Consider splitting into smaller classes.",
                node.lineno
            ))
    
    def _analyze_import(self, node: ast.AST, file_path: Path):
        """Analyze import statements."""
        self.stats['total_imports'] += 1
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = alias.name
                self.import_definitions[import_name].add(str(file_path))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    import_name = f"{node.module}.{alias.name}"
                    self.import_definitions[import_name].add(str(file_path))
    
    def _analyze_function_call(self, node: ast.Call, file_path: Path):
        """Analyze function calls to track usage."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_usage[func_name].add(str(file_path))
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
                self.function_usage[func_name].add(str(file_path))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
                
        return complexity
    
    def _find_unused_functions(self):
        """Find functions that are defined but never used."""
        for func_name, (file_path, line_no) in self.function_definitions.items():
            # Skip special methods and common patterns
            if (func_name.startswith('_') or func_name in ['main', 'setup', 'teardown'] or
                func_name.startswith('test_')):
                continue
                
            # Check if function is used anywhere
            if func_name not in self.function_usage or len(self.function_usage[func_name]) == 0:
                self.issues.append(CodebaseIssue(
                    "High", file_path,
                    f"Function '{func_name}' is defined but never used. Consider removing it.",
                    line_no, func_name
                ))
            elif len(self.function_usage[func_name]) == 1 and file_path in self.function_usage[func_name]:
                # Function only used in the same file it's defined
                self.issues.append(CodebaseIssue(
                    "Medium", file_path,
                    f"Function '{func_name}' is only used locally. Consider making it private (_function_name).",
                    line_no, func_name
                ))
    
    def _find_unused_imports(self):
        """Find imports that are never used."""
        # This is a simplified version - real implementation would need more sophisticated tracking
        for import_name, defining_files in self.import_definitions.items():
            for file_path in defining_files:
                # Check if import is used (simplified check)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Simple heuristic: if import name appears in file content beyond import line
                    import_base = import_name.split('.')[-1]
                    if content.count(import_base) <= 1:  # Only appears in import line
                        self.issues.append(CodebaseIssue(
                            "Low", file_path,
                            f"Import '{import_name}' appears to be unused. Consider removing it."
                        ))
                except:
                    pass
    
    def _find_code_quality_issues(self):
        """Find general code quality issues."""
        for file_path in Path(self.repo_path).rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Long lines
                    if len(line) > 120:
                        self.issues.append(CodebaseIssue(
                            "Low", str(file_path),
                            f"Line too long ({len(line)} characters). Consider breaking it down.",
                            i
                        ))
                    
                    # TODO comments
                    if 'TODO' in line.upper() or 'FIXME' in line.upper():
                        self.issues.append(CodebaseIssue(
                            "Low", str(file_path),
                            f"TODO/FIXME comment found: {line.strip()}",
                            i
                        ))
                    
                    # Print statements (should use logging)
                    if re.search(r'\bprint\s*\(', line) and 'test' not in str(file_path).lower():
                        self.issues.append(CodebaseIssue(
                            "Low", str(file_path),
                            "Print statement found. Consider using logging instead.",
                            i
                        ))
                        
            except:
                pass
    
    def _find_complexity_issues(self):
        """Find complexity-related issues."""
        # Already handled in function analysis
        pass
    
    def _find_naming_issues(self):
        """Find naming convention issues."""
        for file_path in Path(self.repo_path).rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check snake_case for functions
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('_'):
                            self.issues.append(CodebaseIssue(
                                "Low", str(file_path),
                                f"Function '{node.name}' doesn't follow snake_case naming convention.",
                                node.lineno, node.name
                            ))
                    elif isinstance(node, ast.ClassDef):
                        # Check PascalCase for classes
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            self.issues.append(CodebaseIssue(
                                "Low", str(file_path),
                                f"Class '{node.name}' doesn't follow PascalCase naming convention.",
                                node.lineno
                            ))
            except:
                pass
    
    def _find_documentation_issues(self):
        """Find documentation-related issues."""
        # Already handled in function/class analysis
        pass
    
    def _find_security_issues(self):
        """Find potential security issues."""
        for file_path in Path(self.repo_path).rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Potential SQL injection
                    if re.search(r'execute\s*\(\s*["\'].*%.*["\']', line):
                        self.issues.append(CodebaseIssue(
                            "High", str(file_path),
                            "Potential SQL injection vulnerability. Use parameterized queries.",
                            i
                        ))
                    
                    # Hardcoded passwords/secrets
                    if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                        self.issues.append(CodebaseIssue(
                            "High", str(file_path),
                            "Potential hardcoded secret found. Use environment variables or secure storage.",
                            i
                        ))
                    
                    # eval() usage
                    if 'eval(' in line:
                        self.issues.append(CodebaseIssue(
                            "High", str(file_path),
                            "Use of eval() detected. This can be a security risk.",
                            i
                        ))
                        
            except:
                pass
    
    def _find_performance_issues(self):
        """Find potential performance issues."""
        for file_path in Path(self.repo_path).rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Inefficient string concatenation in loops
                    if '+=' in line and 'str' in line and ('for ' in content or 'while ' in content):
                        self.issues.append(CodebaseIssue(
                            "Medium", str(file_path),
                            "Potential inefficient string concatenation. Consider using join() or f-strings.",
                            i
                        ))
                        
            except:
                pass
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        # Sort issues by severity
        severity_order = {'High': 0, 'Medium': 1, 'Low': 2}
        self.issues.sort(key=lambda x: (severity_order.get(x.severity, 3), x.file_path, x.line_number or 0))
        
        # Count issues by severity
        severity_counts = Counter(issue.severity for issue in self.issues)
        
        # Generate file statistics
        file_stats = self._generate_file_stats()
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'repository_path': str(self.repo_path),
            'summary': {
                'total_issues': len(self.issues),
                'high_severity': severity_counts.get('High', 0),
                'medium_severity': severity_counts.get('Medium', 0),
                'low_severity': severity_counts.get('Low', 0),
            },
            'statistics': self.stats,
            'file_statistics': file_stats,
            'issues': [
                {
                    'id': i + 1,
                    'severity': issue.severity,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'function_name': issue.function_name,
                    'description': issue.description
                }
                for i, issue in enumerate(self.issues)
            ]
        }
        
        return report
    
    def _generate_file_stats(self) -> Dict[str, Any]:
        """Generate detailed file statistics."""
        return {
            'total_files': self.stats['total_files'],
            'total_python_files': self.stats['total_python_files'],
            'total_functions': self.stats['total_functions'],
            'total_classes': self.stats['total_classes'],
            'total_lines': self.stats['total_lines'],
            'total_imports': self.stats['total_imports'],
            'average_lines_per_file': self.stats['total_lines'] / max(self.stats['total_python_files'], 1),
            'average_functions_per_file': self.stats['total_functions'] / max(self.stats['total_python_files'], 1)
        }

def format_issue_list(report: Dict[str, Any]) -> str:
    """Format the issue list in the requested format."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("🔍 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
    output.append("=" * 80)
    
    # Summary
    summary = report['summary']
    output.append(f"\n📊 ISSUE SUMMARY")
    output.append(f"Issues: {summary['total_issues']}")
    output.append(f"  🔴 High Severity: {summary['high_severity']}")
    output.append(f"  🟡 Medium Severity: {summary['medium_severity']}")
    output.append(f"  🟢 Low Severity: {summary['low_severity']}")
    
    # Statistics
    stats = report['statistics']
    file_stats = report['file_statistics']
    output.append(f"\n📈 CODEBASE STATISTICS")
    output.append(f"Total Files: {stats['total_files']}")
    output.append(f"Total Python Files: {stats['total_python_files']}")
    output.append(f"Total Functions: {stats['total_functions']}")
    output.append(f"Total Classes: {stats['total_classes']}")
    output.append(f"Total Lines of Code: {stats['total_lines']:,}")
    output.append(f"Total Imports: {stats['total_imports']}")
    output.append(f"Average Lines per File: {file_stats['average_lines_per_file']:.1f}")
    output.append(f"Average Functions per File: {file_stats['average_functions_per_file']:.1f}")
    
    # Detailed Issue List
    output.append(f"\n🚨 DETAILED ISSUE LIST")
    output.append("=" * 80)
    
    if not report['issues']:
        output.append("✅ No issues found! Excellent code quality.")
    else:
        for issue in report['issues']:
            severity_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(issue['severity'], "⚪")
            
            location = issue['file_path']
            if issue['line_number']:
                location += f":{issue['line_number']}"
            if issue['function_name']:
                location += f" in {issue['function_name']}()"
            
            output.append(f"{issue['id']:3d}. {severity_icon} Severity: {issue['severity']} {location}")
            output.append(f"     {issue['description']}")
            output.append("")
    
    output.append("=" * 80)
    output.append(f"Analysis completed at: {report['analysis_timestamp']}")
    output.append("=" * 80)
    
    return "\n".join(output)

def main():
    """Main function to run comprehensive analysis."""
    print("🚀 Starting Comprehensive Codebase Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ComprehensiveAnalyzer(".")
    
    # Run analysis
    report = analyzer.analyze_codebase()
    
    # Format and display results
    formatted_output = format_issue_list(report)
    print(formatted_output)
    
    # Save detailed report
    report_file = "comprehensive_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed JSON report saved to: {report_file}")
    
    # Save formatted output
    output_file = "codebase_issues_report.txt"
    with open(output_file, 'w') as f:
        f.write(formatted_output)
    
    print(f"📄 Formatted report saved to: {output_file}")
    
    return report

if __name__ == "__main__":
    main()

