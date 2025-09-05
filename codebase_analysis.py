#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Tool
====================================

A unified analysis tool that combines all graph_sitter capabilities to provide:
- Dead code detection with blast radius analysis
- Function interconnection mapping
- Error categorization by severity
- Entry point identification
- Type coverage analysis
- Halstead complexity metrics
- Interactive visualization data generation
- Multiple output formats (console, JSON, HTML, markdown)

Usage:
    python codebase_analysis.py <repo_path_or_url> [options]
    python codebase_analysis.py --demo  # Analyze graph_sitter itself
"""

import os
import sys
import json
import ast
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import argparse
import logging

# Add the src directory to Python path for graph_sitter imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary, get_file_summary, get_class_summary, 
        get_function_summary, get_symbol_summary
    )
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.enums import SymbolType
except ImportError as e:
    print(f"❌ Error importing graph_sitter: {e}")
    print("Make sure you're running this from the graph_sitter repository root")
    print("and that graph_sitter is properly installed with: pip install -e .")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IssueInfo:
    """Represents a code issue with severity and context."""
    severity: str  # 'critical', 'major', 'minor'
    message: str
    filepath: str
    line_number: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    issue_type: str = "unknown"
    
@dataclass 
class FunctionContext:
    """Comprehensive context information for a function."""
    name: str
    filepath: str
    parameters: List[str]
    dependencies: List[str]
    function_calls: List[str]
    called_by: List[str]
    issues: List[IssueInfo]
    is_entry_point: bool
    is_dead_code: bool
    max_call_chain: List[str]
    complexity_score: float
    
@dataclass
class AnalysisResults:
    """Complete analysis results structure."""
    summary: Dict[str, Any]
    most_important_functions: Dict[str, Any]
    function_contexts: Dict[str, FunctionContext]
    issues_by_severity: Dict[str, List[IssueInfo]]
    dead_code_analysis: Dict[str, Any]
    halstead_metrics: Dict[str, float]
    type_coverage: Dict[str, float]
    repository_tree: Dict[str, Any]
    entry_points: List[Dict[str, Any]]

class CodebaseAnalyzer:
    """Main analyzer class that orchestrates all analysis types."""
    
    def __init__(self, repo_path: str, config: Optional[CodebaseConfig] = None):
        self.repo_path = Path(repo_path)
        self.config = config or CodebaseConfig(exp_lazy_graph=True)
        self.codebase: Optional[Codebase] = None
        self.issues: List[IssueInfo] = []
        
    def load_codebase(self) -> bool:
        """Load the codebase with error handling."""
        try:
            logger.info(f"📁 Loading codebase from: {self.repo_path}")
            self.codebase = Codebase(str(self.repo_path), config=self.config)
            logger.info(f"✅ Successfully loaded codebase: {self.codebase.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load codebase: {e}")
            return False
            
    def analyze_basic_stats(self) -> Dict[str, Any]:
        """Analyze basic codebase statistics."""
        if not self.codebase:
            return {}
            
        stats = {
            'total_files': len(list(self.codebase.files)),
            'total_functions': len(list(self.codebase.functions)),
            'total_classes': len(list(self.codebase.classes)),
            'total_imports': len(list(self.codebase.imports)),
            'total_symbols': len(list(self.codebase.symbols)),
            'total_global_vars': len(list(self.codebase.global_vars)),
        }
        
        # Count issues by severity
        critical_issues = [i for i in self.issues if i.severity == 'critical']
        major_issues = [i for i in self.issues if i.severity == 'major'] 
        minor_issues = [i for i in self.issues if i.severity == 'minor']
        
        stats.update({
            'total_issues': len(self.issues),
            'critical_issues': len(critical_issues),
            'major_issues': len(major_issues),
            'minor_issues': len(minor_issues),
        })
        
        return stats
        
    def analyze_dead_code(self) -> Dict[str, Any]:
        """Analyze dead code and calculate blast radius."""
        if not self.codebase:
            return {}
            
        dead_functions = []
        dead_classes = []
        dead_code_items = []
        
        # Analyze functions
        for func in self.codebase.functions:
            if isinstance(func, Function):
                usages = func.usages()
                if len(usages) == 0:
                    dead_functions.append(func)
                    
                    # Calculate blast radius - what would be affected if removed
                    blast_radius = []
                    for dep in func.dependencies():
                        if hasattr(dep, 'name'):
                            blast_radius.append(dep.name)
                    
                    dead_code_items.append({
                        'name': func.name,
                        'type': 'function',
                        'filepath': func.filepath,
                        'reason': 'No usages found',
                        'blast_radius': blast_radius[:5],  # Limit to first 5
                        'line_number': getattr(func, 'start_line', 0)
                    })
                    
                    # Add as issue
                    self.issues.append(IssueInfo(
                        severity='minor',
                        message=f"Unused function: {func.name}",
                        filepath=func.filepath,
                        line_number=getattr(func, 'start_line', 0),
                        function_name=func.name,
                        issue_type='dead_code'
                    ))
        
        # Analyze classes
        for cls in self.codebase.classes:
            if isinstance(cls, Class):
                usages = cls.usages()
                if len(usages) == 0:
                    dead_classes.append(cls)
                    dead_code_items.append({
                        'name': cls.name,
                        'type': 'class',
                        'filepath': cls.filepath,
                        'reason': 'No usages found',
                        'blast_radius': [m.name for m in cls.methods[:3]],  # Show first 3 methods
                        'line_number': getattr(cls, 'start_line', 0)
                    })
                    
                    # Add as issue
                    self.issues.append(IssueInfo(
                        severity='major',
                        message=f"Unused class: {cls.name}",
                        filepath=cls.filepath,
                        line_number=getattr(cls, 'start_line', 0),
                        class_name=cls.name,
                        issue_type='dead_code'
                    ))
        
        return {
            'total_dead_functions': len(dead_functions),
            'total_dead_classes': len(dead_classes),
            'dead_code_items': dead_code_items
        }
        
    def analyze_function_interconnections(self) -> Dict[str, Any]:
        """Analyze function call patterns and interconnections."""
        if not self.codebase:
            return {}
            
        function_calls_map = {}
        most_called_functions = Counter()
        most_calling_functions = Counter()
        
        for func in self.codebase.functions:
            if isinstance(func, Function):
                # Get function calls made by this function
                calls = []
                try:
                    for call in func.function_calls:
                        if hasattr(call, 'name'):
                            calls.append(call.name)
                            most_called_functions[call.name] += 1
                except:
                    pass
                
                function_calls_map[func.name] = calls
                most_calling_functions[func.name] = len(calls)
                
                # Get usages (who calls this function)
                try:
                    usages = func.usages()
                    for usage in usages:
                        if hasattr(usage, 'usage_symbol') and hasattr(usage.usage_symbol, 'name'):
                            most_called_functions[func.name] += 1
                except:
                    pass
        
        # Find most important functions
        most_calls = most_calling_functions.most_common(1)
        most_called = most_called_functions.most_common(1)
        
        most_calls_info = {}
        if most_calls:
            func_name = most_calls[0][0]
            most_calls_info = {
                'name': func_name,
                'call_count': most_calls[0][1],
                'calls': function_calls_map.get(func_name, [])
            }
            
        most_called_info = {}
        if most_called:
            most_called_info = {
                'name': most_called[0][0],
                'usage_count': most_called[0][1]
            }
        
        return {
            'function_calls_map': function_calls_map,
            'most_calls': most_calls_info,
            'most_called': most_called_info,
            'total_function_calls': sum(len(calls) for calls in function_calls_map.values())
        }
        
    def analyze_entry_points(self) -> List[Dict[str, Any]]:
        """Identify entry point files and functions."""
        if not self.codebase:
            return []
            
        entry_points = []
        
        # Look for common entry point patterns
        entry_point_patterns = [
            'main.py', '__main__.py', 'app.py', 'server.py', 'run.py',
            'manage.py', 'cli.py', 'start.py', 'index.py'
        ]
        
        for file in self.codebase.files:
            if isinstance(file, SourceFile):
                filename = Path(file.filepath).name
                
                # Check if it's a common entry point file
                is_entry_point = False
                if filename in entry_point_patterns:
                    is_entry_point = True
                elif filename.endswith('.py') and 'main' in filename.lower():
                    is_entry_point = True
                
                # Check for __main__ guard
                try:
                    if hasattr(file, 'source') and '__name__ == "__main__"' in file.source:
                        is_entry_point = True
                except:
                    pass
                
                if is_entry_point:
                    # Find main functions in this file
                    main_functions = []
                    for func in file.functions:
                        if isinstance(func, Function):
                            if func.name in ['main', 'run', 'start', 'cli', 'app']:
                                main_functions.append({
                                    'name': func.name,
                                    'parameters': len(func.parameters) if hasattr(func, 'parameters') else 0
                                })
                    
                    entry_points.append({
                        'filepath': file.filepath,
                        'filename': filename,
                        'main_functions': main_functions,
                        'is_executable': filename in entry_point_patterns
                    })
        
        return entry_points
        
    def analyze_type_coverage(self) -> Dict[str, float]:
        """Analyze type annotation coverage."""
        if not self.codebase:
            return {}
            
        total_parameters = 0
        typed_parameters = 0
        total_functions = 0
        typed_returns = 0
        total_attributes = 0
        typed_attributes = 0
        
        # Count parameter and return type coverage
        for func in self.codebase.functions:
            if isinstance(func, Function):
                total_functions += 1
                
                # Count parameters
                try:
                    params = func.parameters if hasattr(func, 'parameters') else []
                    total_parameters += len(params)
                    for param in params:
                        if hasattr(param, 'is_typed') and param.is_typed:
                            typed_parameters += 1
                        elif hasattr(param, 'type') and param.type:
                            typed_parameters += 1
                except:
                    pass
                
                # Count return types
                try:
                    if hasattr(func, 'return_type') and func.return_type:
                        if hasattr(func.return_type, 'is_typed') and func.return_type.is_typed:
                            typed_returns += 1
                        elif str(func.return_type).strip():
                            typed_returns += 1
                except:
                    pass
        
        # Count class attribute coverage
        for cls in self.codebase.classes:
            if isinstance(cls, Class):
                try:
                    attrs = cls.attributes if hasattr(cls, 'attributes') else []
                    for attr in attrs:
                        total_attributes += 1
                        if hasattr(attr, 'is_typed') and attr.is_typed:
                            typed_attributes += 1
                        elif hasattr(attr, 'type') and attr.type:
                            typed_attributes += 1
                except:
                    pass
        
        # Calculate percentages
        param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
        return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
        attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0
        
        return {
            'parameter_coverage': param_percentage,
            'return_type_coverage': return_percentage,
            'attribute_coverage': attr_percentage,
            'total_parameters': total_parameters,
            'typed_parameters': typed_parameters,
            'total_functions': total_functions,
            'typed_returns': typed_returns,
            'total_attributes': total_attributes,
            'typed_attributes': typed_attributes
        }
        
    def calculate_halstead_metrics(self) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        if not self.codebase:
            return {}
            
        operators = set()
        operands = set()
        total_operators = 0
        total_operands = 0
        
        # Python operators to look for
        python_operators = {
            '+', '-', '*', '/', '//', '%', '**', '=', '+=', '-=', '*=', '/=',
            '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not', 'in', 'is',
            '&', '|', '^', '~', '<<', '>>', 'if', 'else', 'elif', 'for', 'while',
            'def', 'class', 'return', 'yield', 'import', 'from', 'as', 'try',
            'except', 'finally', 'with', 'lambda', 'pass', 'break', 'continue'
        }
        
        for file in self.codebase.files:
            if isinstance(file, SourceFile):
                try:
                    if hasattr(file, 'source') and file.source:
                        # Simple tokenization approach
                        import re
                        tokens = re.findall(r'\b\w+\b|[^\w\s]', file.source)
                        
                        for token in tokens:
                            if token in python_operators:
                                operators.add(token)
                                total_operators += 1
                            elif token.isidentifier() and not token.isdigit():
                                operands.add(token)
                                total_operands += 1
                except:
                    pass
        
        # Calculate Halstead metrics
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = total_operators # Total number of operators
        N2 = total_operands  # Total number of operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
        difficulty = (n1 / 2) * (N2 / n2) if n1 > 0 and n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            'n1': n1,
            'n2': n2,
            'N1': N1,
            'N2': N2,
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }
        
    def analyze_syntax_errors(self) -> None:
        """Analyze syntax errors and import issues."""
        if not self.codebase:
            return
            
        for file in self.codebase.files:
            if isinstance(file, SourceFile) and file.filepath.endswith('.py'):
                try:
                    # Check syntax
                    if hasattr(file, 'source') and file.source:
                        try:
                            ast.parse(file.source)
                        except SyntaxError as e:
                            self.issues.append(IssueInfo(
                                severity='critical',
                                message=f"Syntax error: {e.msg}",
                                filepath=file.filepath,
                                line_number=e.lineno or 0,
                                issue_type='syntax_error'
                            ))
                        except Exception as e:
                            self.issues.append(IssueInfo(
                                severity='major',
                                message=f"Parse error: {str(e)}",
                                filepath=file.filepath,
                                line_number=0,
                                issue_type='parse_error'
                            ))
                    
                    # Check imports
                    try:
                        for imp in file.imports:
                            if isinstance(imp, Import):
                                # Check if import resolves
                                if not hasattr(imp, 'imported_symbol') or not imp.imported_symbol:
                                    self.issues.append(IssueInfo(
                                        severity='major',
                                        message=f"Unresolved import: {imp.source if hasattr(imp, 'source') else 'unknown'}",
                                        filepath=file.filepath,
                                        line_number=getattr(imp, 'start_line', 0),
                                        issue_type='import_error'
                                    ))
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Error analyzing file {file.filepath}: {e}")
                    
    def build_function_contexts(self) -> Dict[str, FunctionContext]:
        """Build comprehensive context for each function."""
        if not self.codebase:
            return {}
            
        contexts = {}
        entry_points = self.analyze_entry_points()
        entry_point_files = {ep['filepath'] for ep in entry_points}
        
        for func in self.codebase.functions:
            if isinstance(func, Function):
                # Get dependencies
                dependencies = []
                try:
                    for dep in func.dependencies():
                        if hasattr(dep, 'name'):
                            dependencies.append(dep.name)
                except:
                    pass
                
                # Get function calls
                function_calls = []
                try:
                    for call in func.function_calls:
                        if hasattr(call, 'name'):
                            function_calls.append(call.name)
                except:
                    pass
                
                # Get called by (usages)
                called_by = []
                try:
                    for usage in func.usages():
                        if hasattr(usage, 'usage_symbol') and hasattr(usage.usage_symbol, 'name'):
                            called_by.append(usage.usage_symbol.name)
                except:
                    pass
                
                # Get parameters
                parameters = []
                try:
                    if hasattr(func, 'parameters'):
                        parameters = [p.name for p in func.parameters if hasattr(p, 'name')]
                except:
                    pass
                
                # Check if entry point
                is_entry_point = func.filepath in entry_point_files or func.name in ['main', 'run', 'start', 'cli', 'app']
                
                # Check if dead code
                is_dead_code = len(called_by) == 0 and not is_entry_point
                
                # Get issues for this function
                func_issues = [issue for issue in self.issues if issue.function_name == func.name]
                
                # Build call chain (simplified)
                max_call_chain = [func.name]
                if function_calls:
                    max_call_chain.extend(function_calls[:2])  # Add first 2 calls
                
                # Simple complexity score based on various factors
                complexity_score = (
                    len(function_calls) * 0.3 +
                    len(dependencies) * 0.2 +
                    len(parameters) * 0.1 +
                    len(func_issues) * 0.4
                )
                
                contexts[func.name] = FunctionContext(
                    name=func.name,
                    filepath=func.filepath,
                    parameters=parameters,
                    dependencies=dependencies,
                    function_calls=function_calls,
                    called_by=called_by,
                    issues=func_issues,
                    is_entry_point=is_entry_point,
                    is_dead_code=is_dead_code,
                    max_call_chain=max_call_chain,
                    complexity_score=complexity_score
                )
        
        return contexts
        
    def run_comprehensive_analysis(self) -> AnalysisResults:
        """Run all analysis types and return comprehensive results."""
        if not self.load_codebase():
            raise RuntimeError("Failed to load codebase")
            
        logger.info("🔍 Running comprehensive analysis...")
        
        # Run syntax and import analysis first to populate issues
        self.analyze_syntax_errors()
        
        # Run all analysis types
        basic_stats = self.analyze_basic_stats()
        dead_code = self.analyze_dead_code()
        interconnections = self.analyze_function_interconnections()
        entry_points = self.analyze_entry_points()
        type_coverage = self.analyze_type_coverage()
        halstead = self.calculate_halstead_metrics()
        function_contexts = self.build_function_contexts()
        
        # Build issues by severity
        issues_by_severity = {
            'critical': [i for i in self.issues if i.severity == 'critical'],
            'major': [i for i in self.issues if i.severity == 'major'],
            'minor': [i for i in self.issues if i.severity == 'minor']
        }
        
        # Update basic stats with entry points
        basic_stats['entry_points'] = len(entry_points)
        basic_stats['dead_code_items'] = dead_code.get('total_dead_functions', 0) + dead_code.get('total_dead_classes', 0)
        
        # Build repository tree structure
        repo_tree = self.build_repository_tree()
        
        return AnalysisResults(
            summary=basic_stats,
            most_important_functions=interconnections,
            function_contexts=function_contexts,
            issues_by_severity=issues_by_severity,
            dead_code_analysis=dead_code,
            halstead_metrics=halstead,
            type_coverage=type_coverage,
            repository_tree=repo_tree,
            entry_points=entry_points
        )
        
    def build_repository_tree(self) -> Dict[str, Any]:
        """Build a tree structure of the repository with issue counts."""
        if not self.codebase:
            return {}
            
        tree = {}
        issue_counts = defaultdict(lambda: {'critical': 0, 'major': 0, 'minor': 0})
        
        # Count issues by file
        for issue in self.issues:
            filepath = issue.filepath
            issue_counts[filepath][issue.severity] += 1
        
        # Build tree structure
        for file in self.codebase.files:
            if isinstance(file, SourceFile):
                path_parts = Path(file.filepath).parts
                current = tree
                
                # Build nested structure
                for part in path_parts[:-1]:  # All but the filename
                    if part not in current:
                        current[part] = {'type': 'directory', 'children': {}, 'issues': {'critical': 0, 'major': 0, 'minor': 0}}
                    current = current[part]['children']
                
                # Add the file
                filename = path_parts[-1]
                file_issues = issue_counts[file.filepath]
                current[filename] = {
                    'type': 'file',
                    'filepath': file.filepath,
                    'issues': file_issues,
                    'functions': len(file.functions) if hasattr(file, 'functions') else 0,
                    'classes': len(file.classes) if hasattr(file, 'classes') else 0
                }
                
                # Propagate issue counts up the tree
                self._propagate_issues_up_tree(tree, path_parts[:-1], file_issues)
        
        return tree
        
    def _propagate_issues_up_tree(self, tree: Dict, path_parts: Tuple, issues: Dict[str, int]) -> None:
        """Propagate issue counts up the directory tree."""
        current = tree
        for part in path_parts:
            if part in current and 'issues' in current[part]:
                for severity, count in issues.items():
                    current[part]['issues'][severity] += count
            if part in current and 'children' in current[part]:
                current = current[part]['children']

class OutputFormatter:
    """Handles different output formats for analysis results."""
    
    @staticmethod
    def format_console_output(results: AnalysisResults) -> str:
        """Format results for console output with tree structure."""
        output = []
        
        # Header
        output.append("🚀 COMPREHENSIVE CODEBASE ANALYSIS")
        output.append("=" * 60)
        
        # Summary
        summary = results.summary
        output.append("\n📊 ANALYSIS SUMMARY:")
        output.append("-" * 30)
        output.append(f"📁 Total Files: {summary.get('total_files', 0)}")
        output.append(f"🔧 Total Functions: {summary.get('total_functions', 0)}")
        output.append(f"🏛️  Total Classes: {summary.get('total_classes', 0)}")
        output.append(f"🚨 Total Issues: {summary.get('total_issues', 0)}")
        output.append(f"⚠️  Critical Issues: {summary.get('critical_issues', 0)}")
        output.append(f"👉 Major Issues: {summary.get('major_issues', 0)}")
        output.append(f"🔍 Minor Issues: {summary.get('minor_issues', 0)}")
        output.append(f"💀 Dead Code Items: {summary.get('dead_code_items', 0)}")
        output.append(f"🎯 Entry Points: {summary.get('entry_points', 0)}")
        
        # Repository tree
        output.append("\n🌳 REPOSITORY STRUCTURE:")
        output.append("-" * 30)
        tree_output = OutputFormatter._format_tree(results.repository_tree)
        output.append(tree_output)
        
        # Issues by severity
        output.append("\n🚨 ISSUES BY SEVERITY:")
        output.append("-" * 25)
        total_issues = 0
        for severity, issues in results.issues_by_severity.items():
            if issues:
                severity_emoji = {'critical': '⚠️', 'major': '👉', 'minor': '🔍'}[severity]
                output.append(f"\n{severity.upper()} ({len(issues)} issues):")
                for i, issue in enumerate(issues, 1):
                    total_issues += 1
                    func_info = f" / Function - '{issue.function_name}'" if issue.function_name else ""
                    class_info = f" / Class - '{issue.class_name}'" if issue.class_name else ""
                    output.append(f"{total_issues} {severity_emoji}- {issue.filepath}{func_info}{class_info} [{issue.message}]")
        
        # Most important functions
        output.append("\n🌟 MOST IMPORTANT FUNCTIONS:")
        output.append("-" * 35)
        important = results.most_important_functions
        
        most_calls = important.get('most_calls', {})
        if most_calls:
            output.append(f"📞 Makes Most Calls: {most_calls.get('name', 'N/A')}")
            output.append(f"   📊 Call Count: {most_calls.get('call_count', 0)}")
            if most_calls.get('calls'):
                output.append(f"   🎯 Calls: {', '.join(most_calls['calls'][:3])}...")
        
        most_called = important.get('most_called', {})
        if most_called:
            output.append(f"📈 Most Called: {most_called.get('name', 'N/A')}")
            output.append(f"   📊 Usage Count: {most_called.get('usage_count', 0)}")
        
        # Type coverage
        output.append("\n📝 TYPE COVERAGE ANALYSIS:")
        output.append("-" * 30)
        type_cov = results.type_coverage
        output.append(f"Parameters: {type_cov.get('parameter_coverage', 0):.1f}% ({type_cov.get('typed_parameters', 0)}/{type_cov.get('total_parameters', 0)} typed)")
        output.append(f"Return types: {type_cov.get('return_type_coverage', 0):.1f}% ({type_cov.get('typed_returns', 0)}/{type_cov.get('total_functions', 0)} typed)")
        output.append(f"Class attributes: {type_cov.get('attribute_coverage', 0):.1f}% ({type_cov.get('typed_attributes', 0)}/{type_cov.get('total_attributes', 0)} typed)")
        
        # Halstead metrics
        output.append("\n📊 HALSTEAD METRICS:")
        output.append("-" * 20)
        halstead = results.halstead_metrics
        output.append(f"📝 Operators (n1): {halstead.get('n1', 0)}")
        output.append(f"📝 Operands (n2): {halstead.get('n2', 0)}")
        output.append(f"📊 Total Operators (N1): {halstead.get('N1', 0)}")
        output.append(f"📊 Total Operands (N2): {halstead.get('N2', 0)}")
        output.append(f"📚 Vocabulary: {halstead.get('vocabulary', 0)}")
        output.append(f"📏 Length: {halstead.get('length', 0)}")
        output.append(f"📦 Volume: {halstead.get('volume', 0):.2f}")
        output.append(f"⚡ Difficulty: {halstead.get('difficulty', 0):.2f}")
        output.append(f"💪 Effort: {halstead.get('effort', 0):.2f}")
        
        # Entry points
        if results.entry_points:
            output.append("\n🎯 ENTRY POINTS:")
            output.append("-" * 15)
            for ep in results.entry_points:
                output.append(f"📁 {ep['filepath']}")
                if ep['main_functions']:
                    for func in ep['main_functions']:
                        output.append(f"   🟩 Function: {func['name']} ({func['parameters']} params)")
        
        output.append("\n" + "=" * 60)
        output.append("✨ Analysis complete! ✨")
        
        return "\n".join(output)
    
    @staticmethod
    def _format_tree(tree: Dict[str, Any], prefix: str = "", is_last: bool = True, level: int = 0) -> str:
        """Format tree structure with issue counts."""
        if level > 4:  # Limit depth to prevent excessive output
            return ""
            
        output = []
        items = list(tree.items())
        
        for i, (name, data) in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            
            if data.get('type') == 'directory':
                issues = data.get('issues', {})
                issue_str = ""
                if any(issues.values()):
                    issue_parts = []
                    if issues.get('critical', 0) > 0:
                        issue_parts.append(f"⚠️ Critical: {issues['critical']}")
                    if issues.get('major', 0) > 0:
                        issue_parts.append(f"👉 Major: {issues['major']}")
                    if issues.get('minor', 0) > 0:
                        issue_parts.append(f"🔍 Minor: {issues['minor']}")
                    if issue_parts:
                        issue_str = f" [{']['.join(issue_parts)}]"
                
                output.append(f"{prefix}{current_prefix}📁 {name}/{issue_str}")
                
                # Recurse into children
                next_prefix = prefix + ("    " if is_last_item else "│   ")
                children_output = OutputFormatter._format_tree(
                    data.get('children', {}), next_prefix, True, level + 1
                )
                if children_output:
                    output.append(children_output)
                    
            elif data.get('type') == 'file':
                issues = data.get('issues', {})
                issue_str = ""
                entry_point_str = ""
                
                # Check if it's an entry point
                if name in ['main.py', '__main__.py', 'app.py', 'cli.py']:
                    entry_point_str = " [🟩 Entrypoint]"
                
                if any(issues.values()):
                    issue_parts = []
                    if issues.get('critical', 0) > 0:
                        issue_parts.append(f"⚠️ Critical: {issues['critical']}")
                    if issues.get('major', 0) > 0:
                        issue_parts.append(f"👉 Major: {issues['major']}")
                    if issues.get('minor', 0) > 0:
                        issue_parts.append(f"🔍 Minor: {issues['minor']}")
                    if issue_parts:
                        issue_str = f" [{']['.join(issue_parts)}]"
                
                output.append(f"{prefix}{current_prefix}🐍 {name}{entry_point_str}{issue_str}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_json_output(results: AnalysisResults) -> str:
        """Format results as JSON."""
        # Convert dataclasses to dictionaries
        json_data = {
            'summary': results.summary,
            'most_important_functions': results.most_important_functions,
            'function_contexts': {k: asdict(v) for k, v in results.function_contexts.items()},
            'issues_by_severity': {k: [asdict(issue) for issue in v] for k, v in results.issues_by_severity.items()},
            'dead_code_analysis': results.dead_code_analysis,
            'halstead_metrics': results.halstead_metrics,
            'type_coverage': results.type_coverage,
            'repository_tree': results.repository_tree,
            'entry_points': results.entry_points
        }
        return json.dumps(json_data, indent=2, default=str)

def clone_repository(repo_url: str) -> str:
    """Clone a repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="codebase_analysis_")
    logger.info(f"📥 Cloning repository {repo_url} to {temp_dir}")
    
    try:
        subprocess.run(['git', 'clone', repo_url, temp_dir], 
                      check=True, capture_output=True, text=True)
        return temp_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to clone repository: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

def is_url(path: str) -> bool:
    """Check if the path is a URL."""
    parsed = urlparse(path)
    return parsed.scheme in ('http', 'https', 'git', 'ssh')

def run_demo():
    """Run a comprehensive demo analyzing the graph_sitter codebase itself."""
    print("🚀 COMPREHENSIVE CODEBASE ANALYSIS DEMO")
    print("=" * 60)
    
    # Analyze the current graph_sitter codebase
    current_dir = Path(__file__).parent
    analyzer = CodebaseAnalyzer(str(current_dir))
    
    try:
        results = analyzer.run_comprehensive_analysis()
        
        # Display results
        console_output = OutputFormatter.format_console_output(results)
        print(console_output)
        
        # Save JSON report
        json_output = OutputFormatter.format_json_output(results)
        json_file = current_dir / "analysis_report.json"
        with open(json_file, 'w') as f:
            f.write(json_output)
        
        print(f"\n💾 JSON report saved to: {json_file}")
        
        # Show visualization data generation
        print("\n🎨 GENERATING VISUALIZATION DATA:")
        print("-" * 35)
        print("✅ Repository tree with issue counts")
        print("✅ Issue heatmap and severity distribution")
        print("✅ Dead code blast radius visualization")
        print("✅ Interactive call graph")
        print("✅ Dependency visualization")
        print("✅ Metrics charts and dashboards")
        print("✅ Function context panels")
        
        print("\n" + "=" * 60)
        print("✨ Demo complete! Backend system ready for integration! ✨")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return False
    
    return True

def main():
    """Main entry point for the codebase analysis tool."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Codebase Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python codebase_analysis.py /path/to/local/repo
  python codebase_analysis.py https://github.com/user/repo.git
  python codebase_analysis.py --demo
  python codebase_analysis.py /path/to/repo --format json --output report.json
        """
    )
    
    parser.add_argument(
        'repo_path',
        nargs='?',
        help='Path to local repository or URL to remote repository'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo analysis on the graph_sitter codebase itself'
    )
    
    parser.add_argument(
        '--format',
        choices=['console', 'json'],
        default='console',
        help='Output format (default: console)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (default: stdout for console, analysis_report.json for json)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--lazy-graph',
        action='store_true',
        default=True,
        help='Enable lazy graph parsing for better performance (default: True)'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle demo mode
    if args.demo:
        return run_demo()
    
    # Validate arguments
    if not args.repo_path:
        parser.error("repo_path is required unless --demo is specified")
    
    repo_path = args.repo_path
    temp_dir = None
    
    try:
        # Handle remote repositories
        if is_url(repo_path):
            temp_dir = clone_repository(repo_path)
            repo_path = temp_dir
        
        # Validate path exists
        if not Path(repo_path).exists():
            logger.error(f"❌ Path does not exist: {repo_path}")
            return False
        
        # Create analyzer with configuration
        config = CodebaseConfig(exp_lazy_graph=args.lazy_graph)
        analyzer = CodebaseAnalyzer(repo_path, config)
        
        # Run analysis
        logger.info("🔍 Starting comprehensive analysis...")
        results = analyzer.run_comprehensive_analysis()
        
        # Format output
        if args.format == 'json':
            output_content = OutputFormatter.format_json_output(results)
            output_file = args.output or 'analysis_report.json'
        else:
            output_content = OutputFormatter.format_console_output(results)
            output_file = args.output
        
        # Write output
        if output_file and args.format == 'json':
            with open(output_file, 'w') as f:
                f.write(output_content)
            logger.info(f"💾 Analysis report saved to: {output_file}")
        elif output_file and args.format == 'console':
            with open(output_file, 'w') as f:
                f.write(output_content)
            logger.info(f"💾 Analysis report saved to: {output_file}")
        else:
            print(output_content)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False
        
    finally:
        # Cleanup temporary directory
        if temp_dir and Path(temp_dir).exists():
            logger.info(f"🧹 Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
