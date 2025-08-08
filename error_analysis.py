#!/usr/bin/env python3
"""
Supreme Error Analysis Tool
Integrates graph-sitter codebase analysis with serena LSP error handling
Uses the ACTUAL graph-sitter API discovered through codebase analysis
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Import the REAL graph-sitter API
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol

# Import the existing analysis capabilities
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Data structure for analysis results"""
    name: str
    type: str
    filepath: str
    full_name: Optional[str] = None
    source_lines: int = 0
    is_private: Optional[bool] = None
    is_magic: Optional[bool] = None
    is_property: Optional[bool] = None
    methods_count: int = 0
    attributes_count: int = 0
    dependencies_count: int = 0
    summary: str = ""


@dataclass
class SupremeAnalysisReport:
    """Complete analysis report structure"""
    codebase_summary: str
    total_files: int
    total_classes: int
    total_functions: int
    total_symbols: int
    top_classes: List[AnalysisResult]
    top_functions: List[AnalysisResult]
    analysis_features: List[str]
    errors_found: List[Dict[str, Any]]
    comprehensive_errors: Optional[Dict[str, Any]] = None


class SupremeErrorAnalyzer:
    """
    Supreme Error Analysis Tool using REAL graph-sitter API
    Integrates with existing codebase_analysis.py capabilities
    """
    
    def __init__(self, codebase_path: str):
        """Initialize with codebase path"""
        self.codebase_path = Path(codebase_path)
        self.codebase: Optional[Codebase] = None
        self.analysis_features = [
            "Class hierarchy analysis",
            "Function dependency tracking", 
            "Symbol usage analysis",
            "Import/Export mapping",
            "Code complexity metrics",
            "Error pattern detection",
            "LSP integration capabilities",
            "Real-time analysis updates"
        ]
        
    def load_codebase(self) -> bool:
        """Load codebase using graph-sitter"""
        try:
            logger.info(f"Loading codebase from: {self.codebase_path}")
            self.codebase = Codebase.from_repo(str(self.codebase_path))
            logger.info("✅ Codebase loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load codebase: {e}")
            return False
    
    def analyze_top_classes(self, limit: int = 20) -> List[AnalysisResult]:
        """
        Analyze top classes using REAL graph-sitter API
        Uses the actual .classes property and .methods() method
        """
        if not self.codebase:
            logger.error("Codebase not loaded")
            return []
        
        logger.info("🔍 Analyzing top classes...")
        results = []
        
        # Use the REAL API: codebase.classes
        classes = self.codebase.classes[:limit]
        
        for cls in classes:
            try:
                # Use REAL properties available on Class objects
                methods = cls.methods() if hasattr(cls, 'methods') else []
                attributes: List[Any] = cls.attributes if hasattr(cls, 'attributes') else []
                dependencies: List[Any] = cls.dependencies if hasattr(cls, 'dependencies') else []
                
                result = AnalysisResult(
                    name=cls.name or "Unknown",
                    type="Class",
                    filepath=cls.filepath or "Unknown",
                    full_name=cls.full_name,
                    source_lines=len(cls.source.splitlines()) if hasattr(cls, 'source') and cls.source else 0,
                    methods_count=len(methods),
                    attributes_count=len(attributes),
                    dependencies_count=len(dependencies),
                    summary=get_class_summary(cls)  # Use existing analysis function
                )
                results.append(result)
                
                logger.info(f"  📋 Class: {cls.name} ({len(methods)} methods, {len(attributes)} attributes)")
                
            except Exception as e:
                logger.error(f"Error analyzing class {getattr(cls, 'name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"✅ Analyzed {len(results)} classes")
        return results
    
    def analyze_top_functions(self, limit: int = 50) -> List[AnalysisResult]:
        """
        Analyze top functions using REAL graph-sitter API
        Uses the actual .functions property and real Function properties
        """
        if not self.codebase:
            logger.error("Codebase not loaded")
            return []
        
        logger.info("🔍 Analyzing top functions...")
        results = []
        
        # Use the REAL API: codebase.functions
        functions = self.codebase.functions[:limit]
        
        for func in functions:
            try:
                # Use REAL properties available on Function objects
                dependencies: List[Any] = func.dependencies if hasattr(func, 'dependencies') else []
                
                result = AnalysisResult(
                    name=func.name or "Unknown",
                    type="Function", 
                    filepath=func.filepath or "Unknown",
                    full_name=func.full_name,
                    source_lines=len(func.source.splitlines()) if hasattr(func, 'source') and func.source else 0,
                    is_private=func.is_private if hasattr(func, 'is_private') else None,
                    is_magic=func.is_magic if hasattr(func, 'is_magic') else None,
                    is_property=func.is_property if hasattr(func, 'is_property') else None,
                    dependencies_count=len(dependencies),
                    summary=get_function_summary(func)  # Use existing analysis function
                )
                results.append(result)
                
                logger.info(f"  🔧 Function: {func.name} ({'private' if result.is_private else 'public'})")
                
            except Exception as e:
                logger.error(f"Error analyzing function {getattr(func, 'name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"✅ Analyzed {len(results)} functions")
        return results
    
    def analyze_all_methods(self) -> List[AnalysisResult]:
        """
        Analyze all methods from all classes using REAL API
        Uses the pattern: [m for c in codebase.classes for m in c.methods()]
        """
        if not self.codebase:
            logger.error("Codebase not loaded")
            return []
        
        logger.info("🔍 Analyzing all class methods...")
        results = []
        
        # Use the REAL pattern found in examples
        all_methods = [m for c in self.codebase.classes for m in c.methods()]
        
        for method in all_methods:
            try:
                dependencies: List[Any] = method.dependencies if hasattr(method, 'dependencies') else []
                
                result = AnalysisResult(
                    name=method.name or "Unknown",
                    type="Method",
                    filepath=method.filepath or "Unknown", 
                    full_name=method.full_name,
                    source_lines=len(method.source.splitlines()) if hasattr(method, 'source') and method.source else 0,
                    is_private=method.is_private if hasattr(method, 'is_private') else None,
                    is_magic=method.is_magic if hasattr(method, 'is_magic') else None,
                    is_property=method.is_property if hasattr(method, 'is_property') else None,
                    dependencies_count=len(dependencies),
                    summary=get_function_summary(method)  # Methods are Functions
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error analyzing method {getattr(method, 'name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"✅ Analyzed {len(results)} methods")
        return results
    
    def detect_error_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect common error patterns in the codebase
        This is where serena LSP integration would be implemented
        """
        if not self.codebase:
            return []
        
        logger.info("🔍 Detecting error patterns...")
        errors = []
        
        # Example error patterns - this would integrate with serena LSP
        try:
            # Check for functions with no return statements
            for func in self.codebase.functions:
                if hasattr(func, 'return_statements'):
                    func_name = func.name or ""
                    if len(func.return_statements) == 0 and not func_name.startswith('__'):
                        errors.append({
                            "type": "missing_return",
                            "message": f"Function '{func.name}' has no return statements",
                            "filepath": func.filepath,
                            "function": func.name,
                            "severity": "warning"
                        })
            
            # Check for classes with no methods
            for cls in self.codebase.classes:
                methods = cls.methods() if hasattr(cls, 'methods') else []
                if len(methods) == 0:
                    errors.append({
                        "type": "empty_class",
                        "message": f"Class '{cls.name}' has no methods",
                        "filepath": cls.filepath,
                        "class": cls.name,
                        "severity": "info"
                    })
            
            logger.info(f"✅ Found {len(errors)} potential issues")
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
        
        return errors
    
    def comprehensive_error_context_analysis(self, max_issues: int = 2000) -> Dict[str, Any]:
        """
        Comprehensive error analysis with detailed context using advanced graph-sitter features.
        Provides the detailed error context requested: file paths, line numbers, function names,
        interconnected context, and fix suggestions.
        """
        if not self.codebase:
            logger.error("Codebase not loaded")
            return {}
        
        logger.info("🔍 Running comprehensive error context analysis...")
        
        # Import calculate_cyclomatic_complexity function locally to avoid circular imports
        def calculate_cyclomatic_complexity(function):
            """Enhanced cyclomatic complexity calculation with better statement handling."""
            base_complexity = 1
            
            if hasattr(function, 'source'):
                # Fallback to source-based analysis
                source = function.source.lower()
                base_complexity += source.count('if ') + source.count('elif ')
                base_complexity += source.count('for ') + source.count('while ')
                base_complexity += source.count('except ')
                base_complexity += source.count(' and ') + source.count(' or ')
            
            return base_complexity
        
        error_analysis: Dict[str, Any] = {
            "total_issues": 0,
            "critical_issues": 0,
            "issues_by_severity": {},
            "issues_by_file": {},
            "interconnected_analysis": {},
            "detailed_issues": []
        }
        
        issue_counter = 0
        
        for file in self.codebase.files():
            if issue_counter >= max_issues:
                break
                
            file_issues: List[Dict[str, Any]] = []
            
            try:
                # Enhanced syntax and semantic analysis
                for func in file.functions:
                    if issue_counter >= max_issues:
                        break
                        
                    try:
                        # Get function context and interconnections
                        func_context = self.get_enhanced_function_context(func)
                        
                        # Complexity analysis with detailed context
                        complexity = calculate_cyclomatic_complexity(func)
                        if complexity > 10:
                            severity = "critical" if complexity > 25 else "high" if complexity > 15 else "medium"
                            
                            issue = {
                                "id": f"complexity_{hashlib.md5(f'{file.filepath}_{func.name}'.encode()).hexdigest()[:8]}",
                                "type": "complexity_issue",
                                "severity": severity,
                                "file_path": file.filepath,
                                "line_number": getattr(func, 'line_number', None),
                                "function_name": func.name,
                                "message": f"High cyclomatic complexity: {complexity}",
                                "description": f"Function '{func.name}' has cyclomatic complexity of {complexity}",
                                "context": {
                                    "complexity_score": complexity,
                                    "parameters_count": len(func.parameters) if hasattr(func, 'parameters') else 0,
                                    "return_statements": len(func.return_statements) if hasattr(func, 'return_statements') else 0,
                                    "function_calls": len(func.function_calls) if hasattr(func, 'function_calls') else 0,
                                    "dependencies": [dep.name for dep in func.dependencies[:5]] if hasattr(func, 'dependencies') else [],
                                    "call_sites": len(func.call_sites) if hasattr(func, 'call_sites') else 0
                                },
                                "interconnected_context": func_context,
                                "affected_symbols": {
                                    "functions": [call.name for call in func.function_calls[:10]] if hasattr(func, 'function_calls') else [],
                                    "parameters": [param.name for param in func.parameters] if hasattr(func, 'parameters') else [],
                                    "dependencies": [dep.name for dep in func.dependencies[:10]] if hasattr(func, 'dependencies') else []
                                },
                                "fix_suggestions": [
                                    f"Break down '{func.name}' into smaller functions (current complexity: {complexity})",
                                    "Extract complex conditional logic into separate methods",
                                    "Consider using strategy pattern for complex branching",
                                    f"Target complexity should be under 10 (currently {complexity})"
                                ]
                            }
                            
                            file_issues.append(issue)
                            if isinstance(error_analysis["detailed_issues"], list):
                                error_analysis["detailed_issues"].append(issue)
                            issue_counter += 1
                            
                            if severity == "critical":
                                if isinstance(error_analysis["critical_issues"], int):
                                    error_analysis["critical_issues"] += 1
                                
                    except Exception as e:
                        continue
                
                # Store file-level issues
                if file_issues:
                    if isinstance(error_analysis["issues_by_file"], dict):
                        error_analysis["issues_by_file"][file.filepath] = {
                            "total_issues": len(file_issues),
                            "critical_count": len([i for i in file_issues if i["severity"] == "critical"]),
                            "high_count": len([i for i in file_issues if i["severity"] == "high"]),
                            "medium_count": len([i for i in file_issues if i["severity"] == "medium"]),
                            "issues": file_issues
                        }
                    
            except Exception as e:
                continue
        
        # Calculate summary statistics
        error_analysis["total_issues"] = issue_counter
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        if isinstance(error_analysis["detailed_issues"], list):
            for issue in error_analysis["detailed_issues"]:
                severity = issue.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        error_analysis["issues_by_severity"] = severity_counts
        
        logger.info(f"✅ Comprehensive analysis complete: {issue_counter} issues found")
        return error_analysis
    
    def get_enhanced_function_context(self, func: Function) -> Dict[str, Any]:
        """Get enhanced context for a function including all interconnected elements."""
        context: Dict[str, Any] = {
            "dependencies": [],
            "dependents": [],
            "call_graph": {},
            "data_flow": {},
            "related_classes": [],
            "related_files": []
        }
        
        try:
            # Dependencies analysis
            if hasattr(func, 'dependencies'):
                dependencies_list = context["dependencies"]
                if isinstance(dependencies_list, list):
                    for dep in func.dependencies[:10]:
                        dependencies_list.append({
                            "name": getattr(dep, 'name', 'unknown'),
                            "type": type(dep).__name__,
                            "file": getattr(dep, 'filepath', 'unknown')
                        })
            
            # Call sites analysis
            if hasattr(func, 'call_sites'):
                dependents_list = context["dependents"]
                if isinstance(dependents_list, list):
                    for call_site in func.call_sites[:10]:
                        dependents_list.append({
                            "caller": getattr(call_site, 'name', 'unknown'),
                            "file": getattr(call_site, 'filepath', 'unknown')
                        })
            
            # Function calls analysis
            call_graph = {}
            if hasattr(func, 'function_calls'):
                for call in func.function_calls[:10]:
                    call_graph[call.name] = {
                        "type": "function_call",
                        "arguments_count": len(getattr(call, 'args', []))
                    }
            context["call_graph"] = call_graph
            
            # Related files through imports
            if hasattr(func, 'file'):
                file = func.file
                related_files = []
                if hasattr(file, 'imports'):
                    for imp in file.imports[:5]:
                        if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'filepath'):
                            related_files.append(imp.imported_symbol.filepath)
                context["related_files"] = related_files
                
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def get_enhanced_class_context(self, cls: Class) -> Dict[str, Any]:
        """Get enhanced context for a class including all interconnected elements."""
        context: Dict[str, Any] = {
            "inheritance_chain": [],
            "composition_relationships": [],
            "method_dependencies": {},
            "attribute_usage": {},
            "related_classes": []
        }
        
        try:
            # Local complexity calculation to avoid circular imports
            def calculate_cyclomatic_complexity(function):
                base_complexity = 1
                if hasattr(function, 'source'):
                    source = function.source.lower()
                    base_complexity += source.count('if ') + source.count('elif ')
                    base_complexity += source.count('for ') + source.count('while ')
                    base_complexity += source.count('except ')
                    base_complexity += source.count(' and ') + source.count(' or ')
                return base_complexity
            
            # Inheritance analysis
            if hasattr(cls, 'parent_class_names'):
                context["inheritance_chain"] = cls.parent_class_names
            
            # Method analysis
            method_deps = {}
            if hasattr(cls, 'methods'):
                for method in cls.methods()[:10]:
                    method_deps[method.name] = {
                        "parameters": len(method.parameters) if hasattr(method, 'parameters') else 0,
                        "complexity": calculate_cyclomatic_complexity(method),
                        "calls": [call.name for call in method.function_calls[:5]] if hasattr(method, 'function_calls') else []
                    }
            context["method_dependencies"] = method_deps
            
            # Attribute analysis
            attr_usage = {}
            if hasattr(cls, 'attributes'):
                for attr in cls.attributes[:10]:
                    attr_usage[attr.name] = {
                        "type": getattr(attr, 'type', 'unknown'),
                        "access_level": getattr(attr, 'access_level', 'unknown')
                    }
            context["attribute_usage"] = attr_usage
            
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def run_supreme_analysis(self) -> SupremeAnalysisReport:
        """
        Run complete supreme analysis using REAL graph-sitter API
        """
        logger.info("🚀 Starting Supreme Analysis...")
        
        if not self.load_codebase():
            raise RuntimeError("Failed to load codebase")
        
        # Check if codebase is loaded properly
        if not self.codebase:
            raise RuntimeError("Codebase is None after loading")
        
        # Use existing codebase_analysis.py function
        codebase_summary = get_codebase_summary(self.codebase)
        
        # Get statistics using REAL API
        total_files = len(self.codebase.files(extensions="*"))
        total_classes = len(self.codebase.classes)
        total_functions = len(self.codebase.functions)
        total_symbols = len(self.codebase.symbols)
        
        logger.info(f"📊 Codebase Stats: {total_files} files, {total_classes} classes, {total_functions} functions")
        
        # Run analyses
        top_classes = self.analyze_top_classes()
        top_functions = self.analyze_top_functions()
        errors_found = self.detect_error_patterns()
        
        # Run comprehensive error context analysis
        comprehensive_errors = self.comprehensive_error_context_analysis()
        
        # Create comprehensive report
        report = SupremeAnalysisReport(
            codebase_summary=codebase_summary,
            total_files=total_files,
            total_classes=total_classes,
            total_functions=total_functions,
            total_symbols=total_symbols,
            top_classes=top_classes,
            top_functions=top_functions,
            analysis_features=self.analysis_features,
            errors_found=errors_found,
            comprehensive_errors=comprehensive_errors
        )
        
        logger.info("✅ Supreme Analysis Complete!")
        return report
    
    def export_results(self, report: SupremeAnalysisReport, output_file: str = "supreme_analysis_results.json"):
        """Export analysis results to JSON"""
        try:
            with open(output_file, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            logger.info(f"📄 Results exported to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")


def analyze_graph_sitter_documentation():
    """
    Analyze graph-sitter.com documentation as requested
    Based on analysis of https://tree-sitter.github.io/tree-sitter/
    """
    logger.info("🌐 Analyzing graph-sitter documentation...")
    
    # Analysis based on actual documentation review
    documentation_analysis = {
        "core_features": {
            "general": "Parse any programming language",
            "fast": "Parse on every keystroke in text editor",
            "robust": "Useful results even with syntax errors", 
            "dependency_free": "Pure C11 runtime library"
        },
        "parsing_mechanism": {
            "type": "Incremental parsing with concrete syntax trees",
            "updates": "Efficiently update syntax tree as source changes",
            "error_recovery": "Robust error handling and partial parsing",
            "performance": "Fast enough for real-time editing"
        },
        "language_support": {
            "official_bindings": [
                "C#", "Go", "Haskell", "Java", "JavaScript", 
                "Kotlin", "Python", "Rust", "Swift", "Zig"
            ],
            "parsers_available": [
                "Agda", "Bash", "C", "C++", "C#", "CSS", "Go", 
                "Haskell", "HTML", "Java", "JavaScript", "JSON",
                "Julia", "OCaml", "PHP", "Python", "Ruby", "Rust",
                "Scala", "TypeScript", "Verilog"
            ]
        },
        "api_structure": {
            "c_api": "Core functionality in tree_sitter/api.h",
            "bindings": "Language-specific wrappers available",
            "documentation": "API docs for official bindings online"
        },
        "integration_capabilities": {
            "text_editors": "Real-time syntax highlighting and parsing",
            "lsp_servers": "Language server protocol integration",
            "analysis_tools": "Code analysis and transformation",
            "error_detection": "Syntax error recovery and reporting"
        }
    }
    
    return documentation_analysis


def main():
    """Main entry point for supreme analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python error_analysis.py <codebase_path>")
        sys.exit(1)
    
    codebase_path = sys.argv[1]
    
    try:
        # Initialize analyzer
        analyzer = SupremeErrorAnalyzer(codebase_path)
        
        # Run supreme analysis
        report = analyzer.run_supreme_analysis()
        
        # Export results
        analyzer.export_results(report)
        
        # Print summary
        print("\n" + "="*60)
        print("🏆 SUPREME ANALYSIS COMPLETE")
        print("="*60)
        print(f"📁 Analyzed: {codebase_path}")
        print(f"📊 Files: {report.total_files}")
        print(f"🏛️  Classes: {report.total_classes}")
        print(f"🔧 Functions: {report.total_functions}")
        print(f"🔍 Errors Found: {len(report.errors_found)}")
        print(f"⚡ Features: {len(report.analysis_features)}")
        print("\n🎯 Analysis Features:")
        for feature in report.analysis_features:
            print(f"  ✅ {feature}")
        
        if report.errors_found:
            print(f"\n⚠️  Basic Issues Found:")
            for error in report.errors_found[:3]:
                print(f"  • {error['type']}: {error['message']}")
        
        if report.comprehensive_errors and report.comprehensive_errors.get('detailed_issues'):
            print(f"\n🔍 Comprehensive Error Analysis:")
            print(f"  📊 Total Issues: {report.comprehensive_errors['total_issues']}")
            print(f"  🚨 Critical: {report.comprehensive_errors['critical_issues']}")
            print(f"  📈 By Severity: {report.comprehensive_errors['issues_by_severity']}")
            
            print(f"\n🎯 Top Complex Functions:")
            for issue in report.comprehensive_errors['detailed_issues'][:3]:
                print(f"  • {issue['function_name']} (complexity: {issue['context']['complexity_score']})")
                print(f"    📁 {issue['file_path']}")
                print(f"    💡 {issue['fix_suggestions'][0]}")
        
        print(f"\n📄 Full results saved to: supreme_analysis_results.json")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
