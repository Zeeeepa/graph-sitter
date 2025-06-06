#!/usr/bin/env python3
"""
Comprehensive Dashboard Validation Script
Analyzes every file, function, class, and parameter in the dashboard system.
"""

import ast
import os
import sys
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

class CodeAnalyzer:
    """Analyzes Python code files for functions, classes, and parameters."""
    
    def __init__(self):
        self.results = {
            "files_analyzed": 0,
            "files_with_errors": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_methods": 0,
            "import_errors": [],
            "syntax_errors": [],
            "file_details": {}
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file."""
        file_info = {
            "path": file_path,
            "exists": os.path.exists(file_path),
            "size_bytes": 0,
            "lines": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "syntax_valid": False,
            "import_test": {"success": False, "error": None},
            "errors": []
        }
        
        if not file_info["exists"]:
            file_info["errors"].append("File does not exist")
            return file_info
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_info["size_bytes"] = len(content)
            file_info["lines"] = len(content.splitlines())
            
            # Parse AST
            try:
                tree = ast.parse(content)
                file_info["syntax_valid"] = True
                
                # Analyze AST nodes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_info = self._analyze_function(node)
                        file_info["functions"].append(func_info)
                        self.results["total_functions"] += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        class_info = self._analyze_class(node)
                        file_info["classes"].append(class_info)
                        self.results["total_classes"] += 1
                    
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            file_info["imports"].append({
                                "type": "import",
                                "name": alias.name,
                                "alias": alias.asname
                            })
                    
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            file_info["imports"].append({
                                "type": "from_import",
                                "module": module,
                                "name": alias.name,
                                "alias": alias.asname
                            })
            
            except SyntaxError as e:
                file_info["syntax_valid"] = False
                file_info["errors"].append(f"Syntax error: {e}")
                self.results["syntax_errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
            
            # Test import
            self._test_import(file_path, file_info)
            
        except Exception as e:
            file_info["errors"].append(f"Analysis error: {e}")
            self.results["files_with_errors"] += 1
        
        self.results["files_analyzed"] += 1
        return file_info
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function definition."""
        func_info = {
            "name": node.name,
            "line_number": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "parameters": [],
            "decorators": [],
            "docstring": ast.get_docstring(node),
            "returns_annotation": None
        }
        
        # Analyze parameters
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": None
            }
            if arg.annotation:
                param_info["annotation"] = ast.unparse(arg.annotation)
            func_info["parameters"].append(param_info)
        
        # Analyze decorators
        for decorator in node.decorator_list:
            func_info["decorators"].append(ast.unparse(decorator))
        
        # Return annotation
        if node.returns:
            func_info["returns_annotation"] = ast.unparse(node.returns)
        
        return func_info
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze a class definition."""
        class_info = {
            "name": node.name,
            "line_number": node.lineno,
            "base_classes": [],
            "methods": [],
            "decorators": [],
            "docstring": ast.get_docstring(node)
        }
        
        # Base classes
        for base in node.bases:
            class_info["base_classes"].append(ast.unparse(base))
        
        # Methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(item)
                method_info["is_method"] = True
                class_info["methods"].append(method_info)
                self.results["total_methods"] += 1
        
        # Decorators
        for decorator in node.decorator_list:
            class_info["decorators"].append(ast.unparse(decorator))
        
        return class_info
    
    def _test_import(self, file_path: str, file_info: Dict[str, Any]):
        """Test if the file can be imported."""
        try:
            # Convert file path to module path
            rel_path = os.path.relpath(file_path, start=".")
            module_path = rel_path.replace(os.sep, ".").replace(".py", "")
            
            # Try to import
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                file_info["import_test"]["success"] = True
            else:
                file_info["import_test"]["error"] = "Could not create module spec"
        
        except Exception as e:
            file_info["import_test"]["error"] = str(e)
            self.results["import_errors"].append({
                "file": file_path,
                "error": str(e)
            })

class DashboardValidator:
    """Main validator for the dashboard system."""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.dashboard_root = "."  # Current directory when run from dashboard folder
    
    def validate_all_files(self) -> Dict[str, Any]:
        """Validate all Python files in the dashboard system."""
        print("🔍 Starting comprehensive dashboard validation...")
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(self.dashboard_root):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        for i, file_path in enumerate(python_files, 1):
            print(f"📄 [{i}/{len(python_files)}] Analyzing {file_path}")
            file_info = self.analyzer.analyze_file(file_path)
            self.analyzer.results["file_details"][file_path] = file_info
        
        return self.analyzer.results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DASHBOARD VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY:")
        report.append(f"   Files Analyzed: {results['files_analyzed']}")
        report.append(f"   Files with Errors: {results['files_with_errors']}")
        report.append(f"   Total Functions: {results['total_functions']}")
        report.append(f"   Total Classes: {results['total_classes']}")
        report.append(f"   Total Methods: {results['total_methods']}")
        report.append(f"   Syntax Errors: {len(results['syntax_errors'])}")
        report.append(f"   Import Errors: {len(results['import_errors'])}")
        report.append("")
        
        # Syntax Errors
        if results['syntax_errors']:
            report.append("❌ SYNTAX ERRORS:")
            for error in results['syntax_errors']:
                report.append(f"   {error['file']}: {error['error']}")
            report.append("")
        
        # Import Errors
        if results['import_errors']:
            report.append("❌ IMPORT ERRORS:")
            for error in results['import_errors']:
                report.append(f"   {error['file']}: {error['error']}")
            report.append("")
        
        # File Details
        report.append("📁 FILE ANALYSIS:")
        for file_path, file_info in results['file_details'].items():
            report.append(f"\n📄 {file_path}")
            report.append(f"   Size: {file_info['size_bytes']} bytes, {file_info['lines']} lines")
            report.append(f"   Syntax Valid: {'✅' if file_info['syntax_valid'] else '❌'}")
            report.append(f"   Import Test: {'✅' if file_info['import_test']['success'] else '❌'}")
            
            if file_info['import_test']['error']:
                report.append(f"   Import Error: {file_info['import_test']['error']}")
            
            if file_info['functions']:
                report.append(f"   Functions ({len(file_info['functions'])}):")
                for func in file_info['functions']:
                    params = [p['name'] for p in func['parameters']]
                    report.append(f"     - {func['name']}({', '.join(params)}) [line {func['line_number']}]")
            
            if file_info['classes']:
                report.append(f"   Classes ({len(file_info['classes'])}):")
                for cls in file_info['classes']:
                    report.append(f"     - {cls['name']} [line {cls['line_number']}]")
                    for method in cls['methods']:
                        params = [p['name'] for p in method['parameters']]
                        report.append(f"       * {method['name']}({', '.join(params)}) [line {method['line_number']}]")
            
            if file_info['errors']:
                report.append(f"   Errors:")
                for error in file_info['errors']:
                    report.append(f"     - {error}")
        
        return "\n".join(report)

def main():
    """Main validation function."""
    validator = DashboardValidator()
    results = validator.validate_all_files()
    
    # Generate report
    report = validator.generate_report(results)
    
    # Save report
    report_file = "VALIDATION_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save JSON results
    json_file = "validation_results.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Validation complete!")
    print(f"📄 Report saved to: {report_file}")
    print(f"📊 JSON results saved to: {json_file}")
    
    # Print summary
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Files: {results['files_analyzed']}")
    print(f"   Errors: {results['files_with_errors']}")
    print(f"   Functions: {results['total_functions']}")
    print(f"   Classes: {results['total_classes']}")
    print(f"   Methods: {results['total_methods']}")
    
    if results['syntax_errors'] or results['import_errors']:
        print(f"\n❌ CRITICAL ISSUES FOUND:")
        print(f"   Syntax Errors: {len(results['syntax_errors'])}")
        print(f"   Import Errors: {len(results['import_errors'])}")
        return 1
    else:
        print(f"\n✅ No critical syntax or import errors found!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
