#!/usr/bin/env python3
"""
Real Codebase Analyzer for Graph-Sitter
This tool analyzes the actual Graph-Sitter codebase using real analysis techniques.
"""

import asyncio
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import time
from collections import defaultdict, Counter
import subprocess
import re

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import ClassDefinition
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    print("⚠️ Graph-Sitter modules not available, using fallback analysis")


class RealCodebaseAnalyzer:
    """Real codebase analyzer using actual analysis techniques."""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.analysis_results = {}
        self.files_analyzed = 0
        self.total_files = 0
        self.errors = []
        self.warnings = []
        self.symbols = []
        
        # Analysis metrics
        self.metrics = {
            'files': {'python': 0, 'javascript': 0, 'typescript': 0, 'other': 0},
            'lines_of_code': 0,
            'complexity': {'total': 0, 'average': 0, 'max': 0},
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'test_files': 0,
            'documentation_files': 0
        }
        
        # File patterns
        self.python_patterns = ['*.py']
        self.js_patterns = ['*.js', '*.jsx', '*.ts', '*.tsx']
        self.test_patterns = ['*test*.py', '*_test.py', 'test_*.py', '*spec*.py']
        self.doc_patterns = ['*.md', '*.rst', '*.txt']
        
    def scan_files(self) -> List[Path]:
        """Scan for all relevant files in the codebase."""
        print("🔍 Scanning codebase files...")
        
        all_files = []
        
        # Get all Python files
        for pattern in self.python_patterns:
            files = list(self.codebase_path.rglob(pattern))
            all_files.extend(files)
            self.metrics['files']['python'] += len(files)
        
        # Get all JS/TS files
        for pattern in self.js_patterns:
            files = list(self.codebase_path.rglob(pattern))
            all_files.extend(files)
            if pattern.endswith('.js') or pattern.endswith('.jsx'):
                self.metrics['files']['javascript'] += len(files)
            else:
                self.metrics['files']['typescript'] += len(files)
        
        # Count test files
        for pattern in self.test_patterns:
            test_files = list(self.codebase_path.rglob(pattern))
            self.metrics['test_files'] += len(test_files)
        
        # Count documentation files
        for pattern in self.doc_patterns:
            doc_files = list(self.codebase_path.rglob(pattern))
            self.metrics['documentation_files'] += len(doc_files)
        
        # Filter out common ignore patterns
        ignore_patterns = [
            '__pycache__', '.git', 'node_modules', '.pytest_cache',
            'build', 'dist', '.venv', 'venv', '.env'
        ]
        
        filtered_files = []
        for file_path in all_files:
            if not any(ignore in str(file_path) for ignore in ignore_patterns):
                filtered_files.append(file_path)
        
        self.total_files = len(filtered_files)
        print(f"📊 Found {self.total_files} files to analyze")
        print(f"   🐍 Python: {self.metrics['files']['python']}")
        print(f"   📜 JavaScript: {self.metrics['files']['javascript']}")
        print(f"   📘 TypeScript: {self.metrics['files']['typescript']}")
        print(f"   🧪 Test files: {self.metrics['test_files']}")
        print(f"   📚 Documentation: {self.metrics['documentation_files']}")
        
        return filtered_files
    
    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Analyze the AST
            analyzer = PythonASTAnalyzer()
            analyzer.visit(tree)
            
            # Calculate metrics
            lines = content.count('\n') + 1
            self.metrics['lines_of_code'] += lines
            
            file_analysis = {
                'path': str(file_path),
                'lines': lines,
                'functions': len(analyzer.functions),
                'classes': len(analyzer.classes),
                'imports': len(analyzer.imports),
                'complexity': analyzer.complexity,
                'functions_detail': analyzer.functions,
                'classes_detail': analyzer.classes,
                'imports_detail': analyzer.imports,
                'errors': analyzer.errors,
                'warnings': analyzer.warnings
            }
            
            # Update global metrics
            self.metrics['functions'] += len(analyzer.functions)
            self.metrics['classes'] += len(analyzer.classes)
            self.metrics['imports'] += len(analyzer.imports)
            self.metrics['complexity']['total'] += analyzer.complexity
            self.metrics['complexity']['max'] = max(
                self.metrics['complexity']['max'], 
                analyzer.complexity
            )
            
            # Collect errors and warnings
            self.errors.extend(analyzer.errors)
            self.warnings.extend(analyzer.warnings)
            
            # Collect symbols
            for func in analyzer.functions:
                self.symbols.append({
                    'name': func['name'],
                    'type': 'function',
                    'file': str(file_path),
                    'line': func['line'],
                    'complexity': func.get('complexity', 1)
                })
            
            for cls in analyzer.classes:
                self.symbols.append({
                    'name': cls['name'],
                    'type': 'class',
                    'file': str(file_path),
                    'line': cls['line'],
                    'methods': len(cls.get('methods', []))
                })
            
            return file_analysis
            
        except Exception as e:
            error = {
                'file': str(file_path),
                'line': 0,
                'message': f"Failed to analyze file: {str(e)}",
                'severity': 'error'
            }
            self.errors.append(error)
            return {'path': str(file_path), 'error': str(e)}
    
    def analyze_javascript_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a JavaScript/TypeScript file (basic analysis)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.count('\n') + 1
            self.metrics['lines_of_code'] += lines
            
            # Basic pattern matching for JS/TS
            functions = len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*\(.*?\)\s*=>', content))
            classes = len(re.findall(r'class\s+\w+', content))
            imports = len(re.findall(r'import\s+.*?from|require\s*\(', content))
            
            self.metrics['functions'] += functions
            self.metrics['classes'] += classes
            self.metrics['imports'] += imports
            
            return {
                'path': str(file_path),
                'lines': lines,
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'language': 'typescript' if file_path.suffix in ['.ts', '.tsx'] else 'javascript'
            }
            
        except Exception as e:
            error = {
                'file': str(file_path),
                'line': 0,
                'message': f"Failed to analyze JS/TS file: {str(e)}",
                'severity': 'error'
            }
            self.errors.append(error)
            return {'path': str(file_path), 'error': str(e)}
    
    async def analyze_files(self, files: List[Path], progress_callback=None):
        """Analyze all files with progress tracking."""
        print(f"\n🚀 Starting analysis of {len(files)} files...")
        
        for i, file_path in enumerate(files):
            if progress_callback:
                progress = (i / len(files)) * 100
                await progress_callback(f"Analyzing {file_path.name}...", progress)
            
            if file_path.suffix == '.py':
                analysis = self.analyze_python_file(file_path)
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                analysis = self.analyze_javascript_file(file_path)
            else:
                continue
            
            self.analysis_results[str(file_path)] = analysis
            self.files_analyzed += 1
            
            # Small delay to show progress
            await asyncio.sleep(0.01)
        
        # Calculate average complexity
        if self.files_analyzed > 0:
            self.metrics['complexity']['average'] = (
                self.metrics['complexity']['total'] / self.files_analyzed
            )
    
    def run_linting(self) -> List[Dict[str, Any]]:
        """Run linting tools on Python files."""
        print("\n🔍 Running linting analysis...")
        lint_results = []
        
        try:
            # Try to run flake8 if available
            python_files = [f for f in self.analysis_results.keys() if f.endswith('.py')]
            
            if python_files:
                # Sample a few files for linting to avoid overwhelming output
                sample_files = python_files[:10]
                
                for file_path in sample_files:
                    try:
                        result = subprocess.run(
                            ['python', '-m', 'flake8', '--select=E,W', file_path],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.stdout:
                            for line in result.stdout.strip().split('\n'):
                                if ':' in line:
                                    parts = line.split(':', 3)
                                    if len(parts) >= 4:
                                        lint_results.append({
                                            'file': parts[0],
                                            'line': int(parts[1]) if parts[1].isdigit() else 0,
                                            'column': int(parts[2]) if parts[2].isdigit() else 0,
                                            'message': parts[3].strip(),
                                            'severity': 'warning' if line.startswith('W') else 'error',
                                            'tool': 'flake8'
                                        })
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                        
        except Exception as e:
            print(f"⚠️ Linting failed: {e}")
        
        print(f"📊 Found {len(lint_results)} linting issues")
        return lint_results
    
    def analyze_with_graph_sitter(self) -> Dict[str, Any]:
        """Use Graph-Sitter for deeper analysis if available."""
        if not GRAPH_SITTER_AVAILABLE:
            return {}
        
        print("\n🌳 Running Graph-Sitter analysis...")
        
        try:
            # Initialize Graph-Sitter codebase
            codebase = Codebase(str(self.codebase_path))
            
            # Get functions and classes
            functions = codebase.get_functions()
            classes = codebase.get_classes()
            
            gs_analysis = {
                'functions_count': len(functions),
                'classes_count': len(classes),
                'functions_detail': [],
                'classes_detail': []
            }
            
            # Analyze functions
            for func in functions[:20]:  # Limit to first 20 for demo
                if hasattr(func, 'name') and hasattr(func, 'file_path'):
                    gs_analysis['functions_detail'].append({
                        'name': func.name,
                        'file': str(func.file_path),
                        'line': getattr(func, 'line_number', 0),
                        'parameters': getattr(func, 'parameters', []),
                        'docstring': getattr(func, 'docstring', '')
                    })
            
            # Analyze classes
            for cls in classes[:20]:  # Limit to first 20 for demo
                if hasattr(cls, 'name') and hasattr(cls, 'file_path'):
                    gs_analysis['classes_detail'].append({
                        'name': cls.name,
                        'file': str(cls.file_path),
                        'line': getattr(cls, 'line_number', 0),
                        'methods': getattr(cls, 'methods', []),
                        'docstring': getattr(cls, 'docstring', '')
                    })
            
            print(f"🌳 Graph-Sitter found {len(functions)} functions, {len(classes)} classes")
            return gs_analysis
            
        except Exception as e:
            print(f"⚠️ Graph-Sitter analysis failed: {e}")
            return {}
    
    def generate_health_metrics(self) -> Dict[str, Any]:
        """Generate codebase health metrics."""
        total_issues = len(self.errors) + len(self.warnings)
        
        # Calculate maintainability index (simplified)
        if self.files_analyzed > 0:
            error_ratio = len(self.errors) / self.files_analyzed
            warning_ratio = len(self.warnings) / self.files_analyzed
            complexity_factor = min(self.metrics['complexity']['average'] / 10, 1.0)
            
            maintainability = max(0, 100 - (error_ratio * 50) - (warning_ratio * 20) - (complexity_factor * 30))
        else:
            maintainability = 0
        
        # Technical debt score
        tech_debt = (len(self.errors) * 3) + (len(self.warnings) * 1)
        
        # Test coverage estimate (based on test file ratio)
        test_coverage = min(100, (self.metrics['test_files'] / max(1, self.files_analyzed)) * 100)
        
        health_status = (
            "Excellent" if maintainability > 90 else
            "Good" if maintainability > 70 else
            "Fair" if maintainability > 50 else
            "Poor"
        )
        
        return {
            'maintainability_index': round(maintainability, 1),
            'technical_debt_score': tech_debt,
            'test_coverage_estimate': round(test_coverage, 1),
            'health_status': health_status,
            'total_issues': total_issues,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'files_analyzed': self.files_analyzed,
            'lines_of_code': self.metrics['lines_of_code']
        }
    
    def get_top_complex_symbols(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most complex symbols."""
        complex_symbols = [s for s in self.symbols if 'complexity' in s]
        return sorted(complex_symbols, key=lambda x: x['complexity'], reverse=True)[:limit]
    
    def get_file_tree_with_issues(self) -> Dict[str, Any]:
        """Generate file tree with issue indicators."""
        tree = {}
        
        for file_path, analysis in self.analysis_results.items():
            path_obj = Path(file_path)
            relative_path = path_obj.relative_to(self.codebase_path)
            
            # Count issues in this file
            file_errors = len([e for e in self.errors if e.get('file') == file_path])
            file_warnings = len([w for w in self.warnings if w.get('file') == file_path])
            
            # Build tree structure
            parts = relative_path.parts
            current = tree
            
            for part in parts[:-1]:  # Directories
                if part not in current:
                    current[part] = {'type': 'directory', 'children': {}, 'issues': 0}
                current = current[part]['children']
            
            # File
            filename = parts[-1]
            current[filename] = {
                'type': 'file',
                'path': str(relative_path),
                'errors': file_errors,
                'warnings': file_warnings,
                'lines': analysis.get('lines', 0),
                'functions': analysis.get('functions', 0),
                'classes': analysis.get('classes', 0)
            }
        
        return tree
    
    async def run_full_analysis(self):
        """Run complete codebase analysis."""
        start_time = time.time()
        
        print("🚀 REAL GRAPH-SITTER CODEBASE ANALYSIS")
        print("=" * 60)
        print(f"📁 Analyzing: {self.codebase_path}")
        print(f"🌳 Graph-Sitter integration: {'✅ Available' if GRAPH_SITTER_AVAILABLE else '❌ Not available'}")
        
        # Phase 1: File scanning
        files = self.scan_files()
        
        # Phase 2: File analysis
        async def progress_callback(status, progress):
            print(f"\r📊 {status} ({progress:.1f}%)", end='', flush=True)
        
        await self.analyze_files(files, progress_callback)
        print()  # New line after progress
        
        # Phase 3: Linting
        lint_results = self.run_linting()
        self.warnings.extend(lint_results)
        
        # Phase 4: Graph-Sitter analysis
        gs_analysis = self.analyze_with_graph_sitter()
        
        # Phase 5: Generate metrics
        health_metrics = self.generate_health_metrics()
        
        analysis_time = time.time() - start_time
        
        # Final results
        print(f"\n✅ Analysis completed in {analysis_time:.2f} seconds")
        print("\n📊 ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"📁 Files analyzed: {self.files_analyzed}")
        print(f"📄 Lines of code: {self.metrics['lines_of_code']:,}")
        print(f"🔧 Functions: {self.metrics['functions']}")
        print(f"🏗️ Classes: {self.metrics['classes']}")
        print(f"📦 Imports: {self.metrics['imports']}")
        print(f"🧪 Test files: {self.metrics['test_files']}")
        
        print(f"\n🏥 Health Metrics:")
        print(f"   📈 Maintainability Index: {health_metrics['maintainability_index']}/100")
        print(f"   💳 Technical Debt Score: {health_metrics['technical_debt_score']}")
        print(f"   🧪 Test Coverage Estimate: {health_metrics['test_coverage_estimate']:.1f}%")
        print(f"   🎯 Overall Health: {health_metrics['health_status']}")
        
        print(f"\n🚨 Issues Found:")
        print(f"   🔴 Errors: {len(self.errors)}")
        print(f"   🟡 Warnings: {len(self.warnings)}")
        
        # Show top complex symbols
        complex_symbols = self.get_top_complex_symbols(5)
        if complex_symbols:
            print(f"\n🧩 Most Complex Symbols:")
            for symbol in complex_symbols:
                print(f"   🔴 {symbol['name']} ({symbol['type']}) - Complexity: {symbol['complexity']}")
                print(f"      📍 {symbol['file']}:{symbol['line']}")
        
        # Show some errors and warnings
        if self.errors:
            print(f"\n🔴 Sample Errors:")
            for error in self.errors[:5]:
                print(f"   • {error['message']}")
                print(f"     📍 {error['file']}:{error.get('line', 0)}")
        
        if self.warnings:
            print(f"\n🟡 Sample Warnings:")
            for warning in self.warnings[:5]:
                print(f"   • {warning['message']}")
                print(f"     📍 {warning['file']}:{warning.get('line', 0)}")
        
        # Graph-Sitter specific results
        if gs_analysis:
            print(f"\n🌳 Graph-Sitter Analysis:")
            print(f"   🔧 Functions detected: {gs_analysis.get('functions_count', 0)}")
            print(f"   🏗️ Classes detected: {gs_analysis.get('classes_count', 0)}")
        
        return {
            'metrics': self.metrics,
            'health': health_metrics,
            'errors': self.errors,
            'warnings': self.warnings,
            'symbols': self.symbols,
            'graph_sitter': gs_analysis,
            'analysis_time': analysis_time
        }


class PythonASTAnalyzer(ast.NodeVisitor):
    """AST analyzer for Python files."""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.complexity = 0
        self.errors = []
        self.warnings = []
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        func_complexity = self.calculate_complexity(node)
        
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'args': len(node.args.args),
            'complexity': func_complexity,
            'docstring': ast.get_docstring(node) or '',
            'decorators': len(node.decorator_list),
            'is_method': self.current_class is not None,
            'class': self.current_class
        }
        
        self.functions.append(func_info)
        self.complexity += func_complexity
        
        # Check for potential issues
        if func_complexity > 10:
            self.warnings.append({
                'file': '',  # Will be filled by caller
                'line': node.lineno,
                'message': f"Function '{node.name}' has high complexity ({func_complexity})",
                'severity': 'warning'
            })
        
        if len(node.args.args) > 7:
            self.warnings.append({
                'file': '',
                'line': node.lineno,
                'message': f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                'severity': 'warning'
            })
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions."""
        self.visit_FunctionDef(node)  # Same logic as regular functions
    
    def visit_ClassDef(self, node):
        """Visit class definitions."""
        old_class = self.current_class
        self.current_class = node.name
        
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
        
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'methods': methods,
            'bases': [self.get_name(base) for base in node.bases],
            'docstring': ast.get_docstring(node) or '',
            'decorators': len(node.decorator_list)
        }
        
        self.classes.append(class_info)
        
        # Check for potential issues
        if len(methods) > 20:
            self.warnings.append({
                'file': '',
                'line': node.lineno,
                'message': f"Class '{node.name}' has many methods ({len(methods)})",
                'severity': 'warning'
            })
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Import(self, node):
        """Visit import statements."""
        for alias in node.names:
            self.imports.append({
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from...import statements."""
        module = node.module or ''
        for alias in node.names:
            self.imports.append({
                'name': f"{module}.{alias.name}" if module else alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'from_import',
                'module': module
            })
        self.generic_visit(node)
    
    def calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        else:
            return str(node)


async def main():
    """Main function to run the real codebase analysis."""
    # Get the Graph-Sitter root directory
    current_dir = Path.cwd()
    
    # Look for the Graph-Sitter root
    if current_dir.name == "analyze":
        graph_sitter_root = current_dir.parent
    else:
        graph_sitter_root = current_dir
    
    print(f"🎯 Analyzing Graph-Sitter codebase at: {graph_sitter_root}")
    
    # Create analyzer
    analyzer = RealCodebaseAnalyzer(str(graph_sitter_root))
    
    # Run analysis
    results = await analyzer.run_full_analysis()
    
    print(f"\n🎉 Real codebase analysis complete!")
    print(f"📊 This demonstrates the actual capabilities of analyzing")
    print(f"   the Graph-Sitter codebase with real metrics and insights!")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
