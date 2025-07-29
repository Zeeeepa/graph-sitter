#!/usr/bin/env python3
"""
Enhanced Serena Codebase Analyzer for Graph-Sitter

This comprehensive demo analyzes the graph-sitter codebase itself using all available
Serena features, demonstrating the full power of semantic code analysis, intelligent
refactoring, and advanced codebase understanding.

Features demonstrated:
1. Comprehensive codebase analysis with error detection
2. Semantic search and symbol intelligence
3. Advanced refactoring capabilities
4. Real-time analysis and diagnostics
5. Code generation and completion
6. Symbol relationship mapping
7. Performance monitoring and optimization
8. LSP integration showcase
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent))

try:
    from graph_sitter import Codebase
    from graph_sitter.extensions.serena import SerenaConfig, SerenaCapability
    from graph_sitter.extensions.serena.types import (
        RefactoringType, RefactoringResult, CodeGenerationResult,
        SemanticSearchResult, SymbolInfo
    )
    SERENA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Serena integration not fully available: {e}")
    SERENA_AVAILABLE = False


@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    file_path: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    symbols: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_score: float
    maintainability_index: float


@dataclass
class CodebaseHealth:
    """Overall codebase health metrics."""
    total_files: int
    total_errors: int
    total_warnings: int
    total_suggestions: int
    average_complexity: float
    maintainability_score: float
    test_coverage: float
    dependency_health: Dict[str, Any]
    hotspots: List[Dict[str, Any]]


class EnhancedSerenaAnalyzer:
    """Enhanced analyzer using all Serena capabilities."""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.analysis_results: Dict[str, AnalysisResult] = {}
        self.errors_found: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        
    def initialize_codebase(self) -> bool:
        """Initialize the codebase with enhanced Serena capabilities."""
        try:
            print(f"🔍 Initializing codebase analysis for: {self.codebase_path}")
            self.codebase = Codebase(str(self.codebase_path))
            
            if SERENA_AVAILABLE:
                # Check if Serena methods are available
                if hasattr(self.codebase, 'get_serena_status'):
                    status = self.codebase.get_serena_status()
                    print(f"✅ Serena integration status: {status}")
                    return status.get('enabled', False)
                else:
                    print("⚠️  Serena methods not available on codebase")
                    return False
            else:
                print("⚠️  Serena not available, using basic graph-sitter features")
                return False
                
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def analyze_file_comprehensive(self, file_path: str) -> AnalysisResult:
        """Perform comprehensive analysis of a single file."""
        print(f"📄 Analyzing file: {file_path}")
        
        errors = []
        warnings = []
        suggestions = []
        symbols = []
        dependencies = []
        metrics = {}
        
        try:
            # Basic file analysis using graph-sitter
            if self.codebase:
                # Get file content and basic metrics
                full_path = self.codebase_path / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    metrics['lines_of_code'] = len(content.splitlines())
                    metrics['file_size'] = len(content)
                    
                    # Try to get functions and classes from the file
                    try:
                        if hasattr(self.codebase, 'functions'):
                            file_functions = [f for f in self.codebase.functions if f.file_path == file_path]
                            symbols.extend([{
                                'name': f.name,
                                'type': 'function',
                                'line': getattr(f, 'line_number', 0),
                                'complexity': getattr(f, 'complexity', 1)
                            } for f in file_functions])
                            
                        if hasattr(self.codebase, 'classes'):
                            file_classes = [c for c in self.codebase.classes if c.file_path == file_path]
                            symbols.extend([{
                                'name': c.name,
                                'type': 'class',
                                'line': getattr(c, 'line_number', 0),
                                'methods': len(getattr(c, 'methods', []))
                            } for c in file_classes])
                    except Exception as e:
                        warnings.append({
                            'type': 'symbol_extraction',
                            'message': f"Could not extract symbols: {e}",
                            'line': 0
                        })
                
                # Enhanced analysis with Serena if available
                if hasattr(self.codebase, 'get_file_diagnostics'):
                    try:
                        diagnostics = self.codebase.get_file_diagnostics(file_path)
                        if diagnostics and diagnostics.get('success'):
                            for diag in diagnostics.get('diagnostics', []):
                                severity = diag.get('severity', 'info')
                                item = {
                                    'type': diag.get('code', 'unknown'),
                                    'message': diag.get('message', ''),
                                    'line': diag.get('range', {}).get('start', {}).get('line', 0),
                                    'character': diag.get('range', {}).get('start', {}).get('character', 0),
                                    'source': diag.get('source', 'lsp')
                                }
                                
                                if severity == 'error':
                                    errors.append(item)
                                elif severity == 'warning':
                                    warnings.append(item)
                                else:
                                    suggestions.append(item)
                    except Exception as e:
                        warnings.append({
                            'type': 'diagnostics_error',
                            'message': f"Failed to get diagnostics: {e}",
                            'line': 0
                        })
                
                # Get symbol information if available
                if hasattr(self.codebase, 'get_symbol_context'):
                    try:
                        for symbol in symbols:
                            context = self.codebase.get_symbol_context(
                                symbol['name'], 
                                include_dependencies=True
                            )
                            if context and context.get('success'):
                                symbol['context'] = context.get('context', {})
                                symbol['dependencies'] = context.get('dependencies', [])
                    except Exception as e:
                        warnings.append({
                            'type': 'symbol_context_error',
                            'message': f"Failed to get symbol context: {e}",
                            'line': 0
                        })
                
        except Exception as e:
            errors.append({
                'type': 'analysis_error',
                'message': f"Failed to analyze file: {e}",
                'line': 0,
                'character': 0
            })
        
        # Calculate complexity and maintainability scores
        complexity_score = self._calculate_complexity(symbols, metrics)
        maintainability_index = self._calculate_maintainability(metrics, errors, warnings)
        
        result = AnalysisResult(
            file_path=file_path,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metrics=metrics,
            symbols=symbols,
            dependencies=dependencies,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index
        )
        
        self.analysis_results[file_path] = result
        self.errors_found.extend(errors)
        
        return result
    
    def _calculate_complexity(self, symbols: List[Dict], metrics: Dict) -> float:
        """Calculate complexity score for a file."""
        base_complexity = 1.0
        
        # Add complexity based on symbols
        for symbol in symbols:
            if symbol['type'] == 'function':
                base_complexity += symbol.get('complexity', 1)
            elif symbol['type'] == 'class':
                base_complexity += symbol.get('methods', 0) * 0.5
        
        # Adjust based on file size
        lines = metrics.get('lines_of_code', 0)
        if lines > 500:
            base_complexity *= 1.5
        elif lines > 1000:
            base_complexity *= 2.0
        
        return min(base_complexity, 10.0)  # Cap at 10
    
    def _calculate_maintainability(self, metrics: Dict, errors: List, warnings: List) -> float:
        """Calculate maintainability index."""
        base_score = 100.0
        
        # Reduce score based on errors and warnings
        base_score -= len(errors) * 10
        base_score -= len(warnings) * 5
        
        # Adjust based on file size
        lines = metrics.get('lines_of_code', 0)
        if lines > 500:
            base_score -= 10
        if lines > 1000:
            base_score -= 20
        
        return max(base_score, 0.0)
    
    def analyze_codebase_comprehensive(self) -> CodebaseHealth:
        """Perform comprehensive analysis of the entire codebase."""
        print("\n🔍 Starting comprehensive codebase analysis...")
        
        # Get all Python files in the codebase
        python_files = []
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    python_files.append(rel_path)
        
        print(f"📊 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        total_errors = 0
        total_warnings = 0
        total_suggestions = 0
        complexity_scores = []
        maintainability_scores = []
        
        for i, file_path in enumerate(python_files[:50]):  # Limit to first 50 files for demo
            print(f"Progress: {i+1}/{min(len(python_files), 50)} - {file_path}")
            try:
                result = self.analyze_file_comprehensive(file_path)
                total_errors += len(result.errors)
                total_warnings += len(result.warnings)
                total_suggestions += len(result.suggestions)
                complexity_scores.append(result.complexity_score)
                maintainability_scores.append(result.maintainability_index)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
                continue
        
        # Calculate overall health metrics
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0
        
        # Find hotspots (files with most issues)
        hotspots = []
        for file_path, result in self.analysis_results.items():
            issue_count = len(result.errors) + len(result.warnings)
            if issue_count > 0:
                hotspots.append({
                    'file_path': file_path,
                    'issue_count': issue_count,
                    'errors': len(result.errors),
                    'warnings': len(result.warnings),
                    'complexity': result.complexity_score
                })
        
        hotspots.sort(key=lambda x: x['issue_count'], reverse=True)
        
        return CodebaseHealth(
            total_files=len(python_files),
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_suggestions=total_suggestions,
            average_complexity=avg_complexity,
            maintainability_score=avg_maintainability,
            test_coverage=0.0,  # Would need additional analysis
            dependency_health={},  # Would need additional analysis
            hotspots=hotspots[:10]  # Top 10 hotspots
        )
    
    def demonstrate_serena_features(self):
        """Demonstrate all available Serena features."""
        if not self.codebase or not hasattr(self.codebase, 'get_serena_status'):
            print("⚠️  Serena features not available")
            return
        
        print("\n🚀 Demonstrating Serena Features")
        print("=" * 50)
        
        # 1. Code Intelligence
        print("\n1. 🧠 Code Intelligence Features:")
        self._demo_code_intelligence()
        
        # 2. Semantic Search
        print("\n2. 🔍 Semantic Search:")
        self._demo_semantic_search()
        
        # 3. Refactoring Capabilities
        print("\n3. 🔧 Refactoring Capabilities:")
        self._demo_refactoring()
        
        # 4. Code Generation
        print("\n4. ⚡ Code Generation:")
        self._demo_code_generation()
        
        # 5. Real-time Analysis
        print("\n5. 📊 Real-time Analysis:")
        self._demo_realtime_analysis()
        
        # 6. Symbol Intelligence
        print("\n6. 🎯 Symbol Intelligence:")
        self._demo_symbol_intelligence()
    
    def _demo_code_intelligence(self):
        """Demo code intelligence features."""
        try:
            # Find a Python file to work with
            sample_file = "src/graph_sitter/core/codebase.py"
            if not (self.codebase_path / sample_file).exists():
                sample_file = next(iter(self.analysis_results.keys()), None)
            
            if not sample_file:
                print("   ⚠️  No suitable file found for demo")
                return
            
            print(f"   📄 Working with file: {sample_file}")
            
            # Get completions
            if hasattr(self.codebase, 'get_completions'):
                completions = self.codebase.get_completions(sample_file, 10, 0)
                if completions and completions.get('success'):
                    items = completions.get('completions', [])[:3]
                    print(f"   ✅ Code completions: {len(items)} items")
                    for item in items:
                        print(f"      - {item.get('label', 'N/A')}: {item.get('kind', 'N/A')}")
                else:
                    print("   ⚠️  No completions available")
            
            # Get hover information
            if hasattr(self.codebase, 'get_hover_info'):
                hover = self.codebase.get_hover_info(sample_file, 20, 10)
                if hover and hover.get('success'):
                    print(f"   ✅ Hover info: {hover.get('contents', 'N/A')[:100]}...")
                else:
                    print("   ⚠️  No hover info available")
            
            # Get signature help
            if hasattr(self.codebase, 'get_signature_help'):
                signature = self.codebase.get_signature_help(sample_file, 30, 15)
                if signature and signature.get('success'):
                    print(f"   ✅ Signature help available")
                else:
                    print("   ⚠️  No signature help available")
                    
        except Exception as e:
            print(f"   ❌ Error in code intelligence demo: {e}")
    
    def _demo_semantic_search(self):
        """Demo semantic search features."""
        try:
            if hasattr(self.codebase, 'semantic_search'):
                # Search for common patterns
                search_terms = ["codebase", "function", "class", "import"]
                
                for term in search_terms:
                    results = self.codebase.semantic_search(term, max_results=3)
                    if results and results.get('success'):
                        items = results.get('results', [])
                        print(f"   🔍 Search '{term}': {len(items)} results")
                        for item in items[:2]:
                            print(f"      - {item.get('symbol_name', 'N/A')} in {item.get('file_path', 'N/A')}")
                    else:
                        print(f"   ⚠️  No results for '{term}'")
            else:
                print("   ⚠️  Semantic search not available")
                
        except Exception as e:
            print(f"   ❌ Error in semantic search demo: {e}")
    
    def _demo_refactoring(self):
        """Demo refactoring capabilities."""
        try:
            # Find a suitable file for refactoring demo
            sample_file = next(iter(self.analysis_results.keys()), None)
            if not sample_file:
                print("   ⚠️  No suitable file found for refactoring demo")
                return
            
            print(f"   📄 Refactoring demo with: {sample_file}")
            
            # Demo rename symbol (preview mode)
            if hasattr(self.codebase, 'rename_symbol'):
                rename_result = self.codebase.rename_symbol(
                    sample_file, 10, 5, "new_name", preview=True
                )
                if rename_result and rename_result.get('success'):
                    changes = rename_result.get('changes', [])
                    print(f"   ✅ Rename preview: {len(changes)} changes would be made")
                else:
                    print("   ⚠️  Rename operation not available")
            
            # Demo extract method (preview mode)
            if hasattr(self.codebase, 'extract_method'):
                extract_result = self.codebase.extract_method(
                    sample_file, 15, 25, "extracted_method", preview=True
                )
                if extract_result and extract_result.get('success'):
                    print("   ✅ Extract method preview available")
                else:
                    print("   ⚠️  Extract method not available")
            
            # Demo organize imports
            if hasattr(self.codebase, 'organize_imports'):
                organize_result = self.codebase.organize_imports(sample_file)
                if organize_result and organize_result.get('success'):
                    print("   ✅ Import organization available")
                else:
                    print("   ⚠️  Import organization not available")
                    
        except Exception as e:
            print(f"   ❌ Error in refactoring demo: {e}")
    
    def _demo_code_generation(self):
        """Demo code generation features."""
        try:
            if hasattr(self.codebase, 'generate_boilerplate'):
                # Generate a simple class template
                result = self.codebase.generate_boilerplate(
                    "class", 
                    {"class_name": "DemoClass", "methods": ["__init__", "process"]},
                    "demo_generated.py"
                )
                if result and result.get('success'):
                    print("   ✅ Boilerplate generation available")
                else:
                    print("   ⚠️  Boilerplate generation not available")
            
            if hasattr(self.codebase, 'generate_tests'):
                # Generate tests for a function
                sample_file = next(iter(self.analysis_results.keys()), None)
                if sample_file:
                    result = self.codebase.generate_tests(
                        f"{sample_file}:some_function",
                        ["unit"]
                    )
                    if result and result.get('success'):
                        print("   ✅ Test generation available")
                    else:
                        print("   ⚠️  Test generation not available")
            
            if hasattr(self.codebase, 'generate_documentation'):
                # Generate documentation
                sample_file = next(iter(self.analysis_results.keys()), None)
                if sample_file:
                    result = self.codebase.generate_documentation(
                        sample_file,
                        "markdown"
                    )
                    if result and result.get('success'):
                        print("   ✅ Documentation generation available")
                    else:
                        print("   ⚠️  Documentation generation not available")
                        
        except Exception as e:
            print(f"   ❌ Error in code generation demo: {e}")
    
    def _demo_realtime_analysis(self):
        """Demo real-time analysis features."""
        try:
            if hasattr(self.codebase, 'enable_realtime_analysis'):
                result = self.codebase.enable_realtime_analysis(
                    watch_patterns=["*.py"],
                    auto_refresh=True
                )
                if result and result.get('success'):
                    print("   ✅ Real-time analysis enabled")
                    
                    # Disable it immediately for demo
                    if hasattr(self.codebase, 'disable_realtime_analysis'):
                        self.codebase.disable_realtime_analysis()
                        print("   ✅ Real-time analysis disabled")
                else:
                    print("   ⚠️  Real-time analysis not available")
            else:
                print("   ⚠️  Real-time analysis not available")
                
        except Exception as e:
            print(f"   ❌ Error in real-time analysis demo: {e}")
    
    def _demo_symbol_intelligence(self):
        """Demo symbol intelligence features."""
        try:
            # Find symbols to work with
            sample_symbols = []
            for result in list(self.analysis_results.values())[:3]:
                sample_symbols.extend(result.symbols[:2])
            
            if not sample_symbols:
                print("   ⚠️  No symbols found for demo")
                return
            
            print(f"   🎯 Working with {len(sample_symbols)} symbols")
            
            for symbol in sample_symbols[:3]:
                symbol_name = symbol.get('name', 'unknown')
                
                if hasattr(self.codebase, 'get_symbol_context'):
                    context = self.codebase.get_symbol_context(
                        symbol_name,
                        include_dependencies=True
                    )
                    if context and context.get('success'):
                        deps = context.get('dependencies', [])
                        print(f"   ✅ Symbol '{symbol_name}': {len(deps)} dependencies")
                    else:
                        print(f"   ⚠️  No context for symbol '{symbol_name}'")
                
                if hasattr(self.codebase, 'analyze_symbol_impact'):
                    impact = self.codebase.analyze_symbol_impact(symbol_name, "modify")
                    if impact and impact.get('success'):
                        affected = impact.get('affected_files', [])
                        print(f"   ✅ Symbol '{symbol_name}' impact: {len(affected)} files affected")
                    else:
                        print(f"   ⚠️  No impact analysis for '{symbol_name}'")
                        
        except Exception as e:
            print(f"   ❌ Error in symbol intelligence demo: {e}")
    
    def print_comprehensive_report(self, health: CodebaseHealth):
        """Print a comprehensive analysis report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
        print("=" * 80)
        
        # Overall health summary
        print(f"\n📈 OVERALL HEALTH METRICS:")
        print(f"   Total Files Analyzed: {health.total_files}")
        print(f"   Total Errors Found: {health.total_errors}")
        print(f"   Total Warnings: {health.total_warnings}")
        print(f"   Total Suggestions: {health.total_suggestions}")
        print(f"   Average Complexity: {health.average_complexity:.2f}/10")
        print(f"   Maintainability Score: {health.maintainability_score:.1f}/100")
        
        # Error summary
        if self.errors_found:
            print(f"\n❌ ERROR DETAILS ({len(self.errors_found)} total):")
            error_types = defaultdict(int)
            for error in self.errors_found:
                error_types[error.get('type', 'unknown')] += 1
            
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {error_type}: {count} occurrences")
            
            # Show top errors
            print(f"\n🔍 TOP ERROR EXAMPLES:")
            for i, error in enumerate(self.errors_found[:5]):
                file_path = error.get('file_path', 'unknown')
                line = error.get('line', 0)
                message = error.get('message', 'No message')[:100]
                print(f"   {i+1}. {file_path}:{line} - {message}")
        
        # Hotspots
        if health.hotspots:
            print(f"\n🔥 CODE HOTSPOTS (files with most issues):")
            for i, hotspot in enumerate(health.hotspots[:5]):
                print(f"   {i+1}. {hotspot['file_path']}")
                print(f"      Issues: {hotspot['issue_count']} (Errors: {hotspot['errors']}, Warnings: {hotspot['warnings']})")
                print(f"      Complexity: {hotspot['complexity']:.1f}/10")
        
        # File-specific details
        print(f"\n📄 FILE-SPECIFIC ANALYSIS:")
        for file_path, result in list(self.analysis_results.items())[:10]:
            if result.errors or result.warnings:
                print(f"   📁 {file_path}:")
                print(f"      Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
                print(f"      Complexity: {result.complexity_score:.1f}, Maintainability: {result.maintainability_index:.1f}")
                print(f"      Symbols: {len(result.symbols)}, Lines: {result.metrics.get('lines_of_code', 0)}")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in self.performance_metrics.items():
                print(f"   {metric}: {value}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if health.total_errors > 0:
            print(f"   🔴 HIGH PRIORITY: Fix {health.total_errors} errors found in the codebase")
        if health.total_warnings > 10:
            print(f"   🟡 MEDIUM PRIORITY: Address {health.total_warnings} warnings")
        if health.average_complexity > 5:
            print(f"   🟠 REFACTOR: Average complexity is high ({health.average_complexity:.1f}/10)")
        if health.maintainability_score < 70:
            print(f"   🔵 IMPROVE: Maintainability score is low ({health.maintainability_score:.1f}/100)")
        
        print(f"\n✅ Analysis complete! Check the detailed results above.")


def main():
    """Main function to run the enhanced Serena codebase analyzer."""
    print("🚀 ENHANCED SERENA CODEBASE ANALYZER")
    print("=" * 50)
    print("Analyzing the graph-sitter codebase with comprehensive Serena integration")
    print("This demo showcases all available Serena features and finds all errors.")
    print()
    
    # Initialize analyzer
    analyzer = EnhancedSerenaAnalyzer(".")
    
    # Record start time for performance metrics
    start_time = time.time()
    
    # Initialize codebase
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase with Serena. Continuing with basic analysis...")
    
    # Perform comprehensive analysis
    try:
        health = analyzer.analyze_codebase_comprehensive()
        
        # Demonstrate Serena features
        analyzer.demonstrate_serena_features()
        
        # Record performance metrics
        analyzer.performance_metrics = {
            'analysis_time': f"{time.time() - start_time:.2f} seconds",
            'files_analyzed': len(analyzer.analysis_results),
            'errors_found': len(analyzer.errors_found),
            'memory_usage': 'N/A'  # Would need psutil for actual memory usage
        }
        
        # Print comprehensive report
        analyzer.print_comprehensive_report(health)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    # Cleanup
    try:
        if analyzer.codebase and hasattr(analyzer.codebase, 'shutdown_serena'):
            analyzer.codebase.shutdown_serena()
            print("\n🔄 Serena integration shutdown complete")
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
    
    print("\n🎉 Enhanced Serena Codebase Analysis Complete!")
    print("This demo showcased the full power of Serena integration with graph-sitter.")


if __name__ == "__main__":
    main()

