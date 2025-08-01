#!/usr/bin/env python3
"""
Simplified Comprehensive Codebase Analysis Tool
===============================================

This script performs comprehensive analysis of the graph-sitter codebase to find:
- All errors and warnings (without LSP dependencies)
- Unused functions and dead code
- Wrong function calls and runtime errors
- Missing documentation and type annotations
- Code quality issues and potential bugs

Uses core graph-sitter libraries and existing analysis functions.
"""

import sys
import os
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import traceback
import time

# Add src to path for graph-sitter imports
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

try:
    # Core graph-sitter imports
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary
    )
    
    print("✅ Successfully imported graph-sitter libraries")
    
except ImportError as e:
    print(f"❌ Error importing graph-sitter libraries: {e}")
    print("Make sure you're running this from the graph-sitter project root")
    sys.exit(1)


@dataclass
class AnalysisResult:
    """Comprehensive analysis results."""
    # Summary information
    codebase_summary: str = ""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_symbols: int = 0
    
    # Dead code analysis
    dead_functions: List[Dict] = field(default_factory=list)
    unused_imports: List[Dict] = field(default_factory=list)
    unused_variables: List[Dict] = field(default_factory=list)
    
    # Function call analysis
    invalid_function_calls: List[Dict] = field(default_factory=list)
    missing_function_definitions: List[Dict] = field(default_factory=list)
    
    # Documentation analysis
    missing_docstrings: List[Dict] = field(default_factory=list)
    undocumented_functions: List[Dict] = field(default_factory=list)
    undocumented_classes: List[Dict] = field(default_factory=list)
    
    # Type annotation analysis
    untyped_functions: List[Dict] = field(default_factory=list)
    untyped_parameters: List[Dict] = field(default_factory=list)
    missing_return_types: List[Dict] = field(default_factory=list)
    
    # Code quality issues
    complex_functions: List[Dict] = field(default_factory=list)
    long_functions: List[Dict] = field(default_factory=list)
    code_smells: List[Dict] = field(default_factory=list)
    syntax_errors: List[Dict] = field(default_factory=list)
    
    # Performance metrics
    analysis_duration: float = 0.0
    files_analyzed: int = 0
    errors_found: int = 0


class SimplifiedCodebaseAnalyzer:
    """Simplified codebase analyzer using core graph-sitter capabilities."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.codebase = None
        self.results = AnalysisResult()
        self.python_files = []
        
    def initialize(self) -> bool:
        """Initialize the codebase and analysis components."""
        try:
            print(f"🚀 Initializing codebase analysis for: {self.repo_path}")
            
            # Create codebase instance
            self.codebase = Codebase(str(self.repo_path), language="python")
            print(f"✅ Codebase loaded: {len(list(self.codebase.files))} files found")
            
            # Get Python files for additional analysis
            self.python_files = [f for f in self.repo_path.rglob("*.py") if f.is_file()]
            print(f"✅ Found {len(self.python_files)} Python files for detailed analysis")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing analyzer: {e}")
            traceback.print_exc()
            return False
    
    def analyze_codebase_summary(self):
        """Analyze codebase summary using existing functions."""
        print("\n📊 Analyzing codebase summary...")
        
        try:
            # Get comprehensive codebase summary
            self.results.codebase_summary = get_codebase_summary(self.codebase)
            
            # Count basic metrics
            self.results.total_files = len(list(self.codebase.files))
            self.results.total_functions = len(list(self.codebase.functions))
            self.results.total_classes = len(list(self.codebase.classes))
            self.results.total_symbols = len(list(self.codebase.symbols))
            
            print(f"   📁 Files: {self.results.total_files}")
            print(f"   🔧 Functions: {self.results.total_functions}")
            print(f"   🏛️ Classes: {self.results.total_classes}")
            print(f"   🏷️ Symbols: {self.results.total_symbols}")
            
            # Show detailed codebase summary
            print("\n📋 Detailed Codebase Summary:")
            print(self.results.codebase_summary)
            
        except Exception as e:
            print(f"❌ Error analyzing codebase summary: {e}")
    
    def analyze_syntax_errors(self):
        """Analyze Python files for syntax errors."""
        print("\n🐍 Analyzing Python syntax errors...")
        
        syntax_error_count = 0
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to parse the file with AST
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    syntax_error_count += 1
                    self.results.syntax_errors.append({
                        'file': str(py_file.relative_to(self.repo_path)),
                        'line': e.lineno,
                        'column': e.offset,
                        'message': e.msg,
                        'error_type': 'SyntaxError'
                    })
                    
            except Exception as e:
                print(f"   ⚠️ Error reading {py_file}: {e}")
        
        print(f"   🐍 Syntax Errors Found: {syntax_error_count}")
    
    def find_dead_code(self):
        """Find unused functions and dead code using graph-sitter's find_dead_code approach."""
        print("\n💀 Finding dead code...")
        
        try:
            # Implementation of find_dead_code from documentation
            dead_functions = []
            for function in self.codebase.functions:
                try:
                    # Check if function has any call sites
                    call_sites = getattr(function, 'call_sites', [])
                    
                    if not call_sites:
                        # Check if it's a main function, test function, or special method
                        func_name = function.name
                        if not (func_name in ['main', '__main__'] or 
                               func_name.startswith('test_') or 
                               func_name.startswith('__') and func_name.endswith('__')):
                            
                            dead_functions.append(function)
                            self.results.dead_functions.append({
                                'name': func_name,
                                'file': function.filepath,
                                'line': getattr(function, 'line_number', 'unknown'),
                                'reason': 'No call sites found'
                            })
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing function {getattr(function, 'name', 'unknown')}: {e}")
            
            print(f"   💀 Dead Functions Found: {len(self.results.dead_functions)}")
            
            # Show some examples
            if self.results.dead_functions:
                print("   🔍 Sample Dead Functions:")
                for func in self.results.dead_functions[:5]:
                    print(f"      {func['name']} in {func['file']}")
            
            # Find unused imports using simple heuristics
            for file in self.codebase.files:
                try:
                    if hasattr(file, 'imports') and hasattr(file, 'content'):
                        for import_stmt in file.imports:
                            import_name = getattr(import_stmt, 'name', '')
                            if import_name:
                                # Simple check: if import name doesn't appear in content (excluding import line)
                                content_lines = file.content.split('\n')
                                import_lines = [line for line in content_lines if 'import' in line and import_name in line]
                                non_import_content = '\n'.join([line for line in content_lines if line not in import_lines])
                                
                                if import_name not in non_import_content:
                                    self.results.unused_imports.append({
                                        'import': import_name,
                                        'file': file.filepath,
                                        'line': getattr(import_stmt, 'line_number', 'unknown')
                                    })
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing imports in {getattr(file, 'filepath', 'unknown')}: {e}")
            
            print(f"   📦 Unused Imports Found: {len(self.results.unused_imports)}")
            
        except Exception as e:
            print(f"❌ Error finding dead code: {e}")
            traceback.print_exc()
    
    def analyze_function_calls(self):
        """Analyze function calls for errors and invalid calls."""
        print("\n📞 Analyzing function calls...")
        
        try:
            # Track all function definitions
            defined_functions = set()
            for function in self.codebase.functions:
                defined_functions.add(function.name)
            
            # Add common built-in functions
            builtin_functions = {
                'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
                'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
                'sum', 'min', 'max', 'abs', 'round', 'isinstance', 'hasattr', 'getattr',
                'setattr', 'open', 'input', 'type', 'id', 'hash', 'repr', 'format'
            }
            
            # Analyze function calls in each function
            for function in self.codebase.functions:
                try:
                    if hasattr(function, 'function_calls'):
                        for call in function.function_calls:
                            call_name = getattr(call, 'name', '')
                            
                            # Check if called function exists
                            if call_name and call_name not in defined_functions and call_name not in builtin_functions:
                                # Skip method calls and module calls for now
                                if not ('.' in call_name or call_name.startswith('_')):
                                    
                                    self.results.missing_function_definitions.append({
                                        'called_function': call_name,
                                        'calling_function': function.name,
                                        'file': function.filepath,
                                        'line': getattr(call, 'line_number', 'unknown')
                                    })
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing calls in {getattr(function, 'name', 'unknown')}: {e}")
            
            print(f"   📞 Missing Function Definitions: {len(self.results.missing_function_definitions)}")
            
            # Show some examples
            if self.results.missing_function_definitions:
                print("   🔍 Sample Missing Functions:")
                for func in self.results.missing_function_definitions[:5]:
                    print(f"      {func['called_function']} called from {func['calling_function']}")
            
        except Exception as e:
            print(f"❌ Error analyzing function calls: {e}")
            traceback.print_exc()
    
    def analyze_documentation(self):
        """Analyze missing documentation and docstrings."""
        print("\n📚 Analyzing documentation...")
        
        try:
            # Check functions for missing docstrings
            for function in self.codebase.functions:
                try:
                    docstring = getattr(function, 'docstring', None)
                    if not docstring or not docstring.strip():
                        # Skip magic methods and test functions
                        func_name = function.name
                        if not (func_name.startswith('__') and func_name.endswith('__') or
                               func_name.startswith('test_')):
                            
                            self.results.undocumented_functions.append({
                                'name': func_name,
                                'file': function.filepath,
                                'line': getattr(function, 'line_number', 'unknown'),
                                'type': 'function'
                            })
                
                except Exception as e:
                    print(f"   ⚠️ Error checking docstring for {getattr(function, 'name', 'unknown')}: {e}")
            
            # Check classes for missing docstrings
            for class_obj in self.codebase.classes:
                try:
                    docstring = getattr(class_obj, 'docstring', None)
                    if not docstring or not docstring.strip():
                        self.results.undocumented_classes.append({
                            'name': class_obj.name,
                            'file': class_obj.filepath,
                            'line': getattr(class_obj, 'line_number', 'unknown'),
                            'type': 'class'
                        })
                
                except Exception as e:
                    print(f"   ⚠️ Error checking docstring for {getattr(class_obj, 'name', 'unknown')}: {e}")
            
            print(f"   📚 Undocumented Functions: {len(self.results.undocumented_functions)}")
            print(f"   🏛️ Undocumented Classes: {len(self.results.undocumented_classes)}")
            
            # Show some examples
            if self.results.undocumented_functions:
                print("   🔍 Sample Undocumented Functions:")
                for func in self.results.undocumented_functions[:5]:
                    print(f"      {func['name']} in {func['file']}")
            
        except Exception as e:
            print(f"❌ Error analyzing documentation: {e}")
            traceback.print_exc()
    
    def analyze_type_annotations(self):
        """Analyze missing type annotations."""
        print("\n🏷️ Analyzing type annotations...")
        
        try:
            # Check functions for missing return type annotations
            for function in self.codebase.functions:
                try:
                    return_type = getattr(function, 'return_type', None)
                    if not return_type or str(return_type).strip() in ['', 'None', 'Any']:
                        # Skip magic methods and test functions
                        func_name = function.name
                        if not (func_name.startswith('__') and func_name.endswith('__') or
                               func_name.startswith('test_')):
                            
                            self.results.missing_return_types.append({
                                'name': func_name,
                                'file': function.filepath,
                                'line': getattr(function, 'line_number', 'unknown'),
                                'current_return_type': str(return_type) if return_type else 'None'
                            })
                    
                    # Check parameters for type annotations
                    if hasattr(function, 'parameters'):
                        for param in function.parameters:
                            param_type = getattr(param, 'type', None)
                            param_name = getattr(param, 'name', 'unknown')
                            
                            if not param_type and param_name not in ['self', 'cls']:
                                self.results.untyped_parameters.append({
                                    'parameter': param_name,
                                    'function': func_name,
                                    'file': function.filepath,
                                    'line': getattr(function, 'line_number', 'unknown')
                                })
                
                except Exception as e:
                    print(f"   ⚠️ Error checking types for {getattr(function, 'name', 'unknown')}: {e}")
            
            print(f"   🏷️ Missing Return Types: {len(self.results.missing_return_types)}")
            print(f"   📝 Untyped Parameters: {len(self.results.untyped_parameters)}")
            
            # Show some examples
            if self.results.missing_return_types:
                print("   🔍 Sample Functions Missing Return Types:")
                for func in self.results.missing_return_types[:5]:
                    print(f"      {func['name']} in {func['file']}")
            
        except Exception as e:
            print(f"❌ Error analyzing type annotations: {e}")
            traceback.print_exc()
    
    def analyze_code_quality(self):
        """Analyze code quality issues."""
        print("\n🔍 Analyzing code quality...")
        
        try:
            # Check for long functions
            for function in self.codebase.functions:
                try:
                    # Estimate function length from source
                    source = getattr(function, 'source', '')
                    if source:
                        line_count = len(source.split('\n'))
                        if line_count > 50:  # Threshold for long functions
                            self.results.long_functions.append({
                                'name': function.name,
                                'file': function.filepath,
                                'line_count': line_count,
                                'line': getattr(function, 'line_number', 'unknown')
                            })
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing function length for {getattr(function, 'name', 'unknown')}: {e}")
            
            print(f"   📏 Long Functions: {len(self.results.long_functions)}")
            
            # Look for common code smells in Python files
            for py_file in self.python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    rel_path = str(py_file.relative_to(self.repo_path))
                    
                    for i, line in enumerate(lines, 1):
                        line_stripped = line.strip()
                        
                        # Check for common code smells
                        if 'TODO' in line_stripped or 'FIXME' in line_stripped:
                            self.results.code_smells.append({
                                'type': 'TODO/FIXME',
                                'file': rel_path,
                                'line': i,
                                'content': line_stripped[:100]
                            })
                        
                        if line_stripped.startswith('print(') and any(word in line_stripped.lower() for word in ['debug', 'test', 'temp']):
                            self.results.code_smells.append({
                                'type': 'Debug print statement',
                                'file': rel_path,
                                'line': i,
                                'content': line_stripped[:100]
                            })
                        
                        # Check for bare except clauses
                        if re.match(r'^\s*except\s*:\s*$', line):
                            self.results.code_smells.append({
                                'type': 'Bare except clause',
                                'file': rel_path,
                                'line': i,
                                'content': line_stripped[:100]
                            })
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing code smells in {py_file}: {e}")
            
            print(f"   👃 Code Smells Found: {len(self.results.code_smells)}")
            
            # Show some examples
            if self.results.code_smells:
                print("   🔍 Sample Code Smells:")
                smell_types = defaultdict(int)
                for smell in self.results.code_smells:
                    smell_types[smell['type']] += 1
                
                for smell_type, count in smell_types.items():
                    print(f"      {smell_type}: {count}")
            
        except Exception as e:
            print(f"❌ Error analyzing code quality: {e}")
            traceback.print_exc()
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        print("\n📊 Generating comprehensive report...")
        
        total_issues = (len(self.results.syntax_errors) + len(self.results.dead_functions) + 
                       len(self.results.missing_function_definitions) + len(self.results.undocumented_functions) +
                       len(self.results.missing_return_types) + len(self.results.code_smells))
        
        report_lines = [
            "=" * 80,
            "🔍 COMPREHENSIVE CODEBASE ANALYSIS REPORT",
            "=" * 80,
            "",
            "📊 CODEBASE SUMMARY:",
            f"   📁 Total Files: {self.results.total_files}",
            f"   🔧 Total Functions: {self.results.total_functions}",
            f"   🏛️ Total Classes: {self.results.total_classes}",
            f"   🏷️ Total Symbols: {self.results.total_symbols}",
            f"   ⏱️ Analysis Duration: {self.results.analysis_duration:.2f}s",
            f"   🎯 Total Issues Found: {total_issues}",
            "",
            "🐍 SYNTAX ERROR ANALYSIS:",
            f"   ❌ Syntax Errors: {len(self.results.syntax_errors)}",
        ]
        
        if self.results.syntax_errors:
            report_lines.append("   🔍 Syntax Error Files:")
            for error in self.results.syntax_errors[:5]:
                report_lines.append(f"      {error['file']}:{error['line']} - {error['message']}")
        
        report_lines.extend([
            "",
            "💀 DEAD CODE ANALYSIS:",
            f"   💀 Dead Functions: {len(self.results.dead_functions)}",
            f"   📦 Unused Imports: {len(self.results.unused_imports)}",
        ])
        
        # Show some dead functions
        if self.results.dead_functions:
            report_lines.append("   🔍 Sample Dead Functions:")
            for func in self.results.dead_functions[:5]:
                report_lines.append(f"      {func['name']} in {func['file']}")
        
        report_lines.extend([
            "",
            "📞 FUNCTION CALL ANALYSIS:",
            f"   ❓ Missing Function Definitions: {len(self.results.missing_function_definitions)}",
        ])
        
        # Show some missing functions
        if self.results.missing_function_definitions:
            report_lines.append("   🔍 Sample Missing Functions:")
            for func in self.results.missing_function_definitions[:5]:
                report_lines.append(f"      {func['called_function']} called from {func['calling_function']}")
        
        report_lines.extend([
            "",
            "📚 DOCUMENTATION ANALYSIS:",
            f"   📚 Undocumented Functions: {len(self.results.undocumented_functions)}",
            f"   🏛️ Undocumented Classes: {len(self.results.undocumented_classes)}",
            "",
            "🏷️ TYPE ANNOTATION ANALYSIS:",
            f"   🏷️ Missing Return Types: {len(self.results.missing_return_types)}",
            f"   📝 Untyped Parameters: {len(self.results.untyped_parameters)}",
            "",
            "🔍 CODE QUALITY ANALYSIS:",
            f"   📏 Long Functions: {len(self.results.long_functions)}",
            f"   👃 Code Smells: {len(self.results.code_smells)}",
            "",
            "🎯 RECOMMENDATIONS:",
        ])
        
        # Generate recommendations
        recommendations = []
        if len(self.results.syntax_errors) > 0:
            recommendations.append(f"   🔴 CRITICAL: Fix {len(self.results.syntax_errors)} syntax errors")
        if len(self.results.dead_functions) > 10:
            recommendations.append(f"   🧹 CLEANUP: Remove {len(self.results.dead_functions)} unused functions")
        if len(self.results.missing_return_types) > 20:
            recommendations.append(f"   🏷️ TYPING: Add return type annotations to {len(self.results.missing_return_types)} functions")
        if len(self.results.undocumented_functions) > 20:
            recommendations.append(f"   📚 DOCUMENTATION: Add docstrings to {len(self.results.undocumented_functions)} functions")
        if len(self.results.code_smells) > 10:
            recommendations.append(f"   🔧 REFACTOR: Address {len(self.results.code_smells)} code quality issues")
        
        if not recommendations:
            recommendations.append("   ✅ Codebase is in excellent shape! Consider minor improvements above.")
        
        report_lines.extend(recommendations)
        report_lines.extend([
            "",
            "📋 DETAILED CODEBASE SUMMARY:",
            self.results.codebase_summary,
            "",
            "=" * 80,
            f"Analysis completed at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_detailed_results(self, output_file: str = "analysis_results.json"):
        """Save detailed results to JSON file."""
        try:
            # Convert results to JSON-serializable format
            results_dict = {
                'summary': {
                    'total_files': self.results.total_files,
                    'total_functions': self.results.total_functions,
                    'total_classes': self.results.total_classes,
                    'total_symbols': self.results.total_symbols,
                    'analysis_duration': self.results.analysis_duration,
                    'codebase_summary': self.results.codebase_summary,
                },
                'syntax_errors': self.results.syntax_errors,
                'dead_code': {
                    'dead_functions': self.results.dead_functions,
                    'unused_imports': self.results.unused_imports,
                },
                'function_calls': {
                    'missing_function_definitions': self.results.missing_function_definitions,
                },
                'documentation': {
                    'undocumented_functions': self.results.undocumented_functions,
                    'undocumented_classes': self.results.undocumented_classes,
                },
                'type_annotations': {
                    'missing_return_types': self.results.missing_return_types,
                    'untyped_parameters': self.results.untyped_parameters,
                },
                'code_quality': {
                    'long_functions': self.results.long_functions,
                    'code_smells': self.results.code_smells,
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(results_dict, f, indent=2)
            
            print(f"📄 Detailed results saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def run_full_analysis(self) -> bool:
        """Run complete codebase analysis."""
        start_time = time.time()
        
        print("🚀 Starting comprehensive codebase analysis...")
        print("=" * 60)
        
        try:
            # Initialize
            if not self.initialize():
                return False
            
            # Run all analysis phases
            self.analyze_codebase_summary()
            self.analyze_syntax_errors()
            self.find_dead_code()
            self.analyze_function_calls()
            self.analyze_documentation()
            self.analyze_type_annotations()
            self.analyze_code_quality()
            
            # Calculate duration
            self.results.analysis_duration = time.time() - start_time
            
            # Generate and display report
            report = self.generate_report()
            print("\n" + report)
            
            # Save detailed results
            self.save_detailed_results()
            
            print(f"\n✅ Analysis completed successfully in {self.results.analysis_duration:.2f}s")
            return True
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    print("🔍 Graph-Sitter Simplified Comprehensive Codebase Analyzer")
    print("=" * 60)
    
    # Get repository path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # Create and run analyzer
    analyzer = SimplifiedCodebaseAnalyzer(repo_path)
    success = analyzer.run_full_analysis()
    
    if success:
        print("\n🎉 Analysis completed successfully!")
        print("📄 Check analysis_results.json for detailed results")
        sys.exit(0)
    else:
        print("\n❌ Analysis failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

