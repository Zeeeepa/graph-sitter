"""
Graph-Sitter Analysis Module

Consolidated analysis features for comprehensive codebase analysis using Tree-sitter
and graph-based insights. Provides unified interface for all analysis operations.
"""

import time
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol

from .codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_optimized_config,
    get_codebase_metrics,
    get_file_metrics,
    get_class_metrics,
    get_function_metrics,
    analyze_circular_dependencies,
    find_hotspot_functions,
    analyze_module_coupling,
    CodebaseMetrics,
    FunctionMetrics,
    ClassMetrics,
    FileMetrics
)

# Import existing analyzers for integration
from .dead_code_detector import detect_dead_code
from .complexity_analyzer import analyze_complexity, find_complex_functions, find_large_functions
from .dependency_analyzer import analyze_dependencies, detect_circular_dependencies as detect_circular_deps, analyze_module_coupling as analyze_coupling
from .security_analyzer import analyze_security, check_import_security
from .call_graph_analyzer import analyze_call_graph, find_hotspot_functions as find_hotspots


class Analysis:
    """
    Unified Analysis Interface
    
    Consolidates all analysis features from the official Tree-sitter documentation
    and graph-sitter extensions into a single, comprehensive analysis system.
    """
    
    def __init__(self, codebase: Optional[Codebase] = None):
        """
        Initialize the Analysis system.
        
        Args:
            codebase: Optional codebase to analyze. Can be set later.
        """
        self.codebase = codebase
        self.analysis_cache = {}
        self.config = get_optimized_config()
    
    def set_codebase(self, codebase: Codebase) -> None:
        """
        Set the codebase for analysis.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.analysis_cache.clear()  # Clear cache when codebase changes
    
    def comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive analysis using all available analyzers.
        
        Returns:
            Dict[str, Any]: Complete analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        start_time = time.time()
        
        print("🔍 Starting comprehensive codebase analysis...")
        
        results = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'codebase_info': self._get_basic_codebase_info(),
                'analysis_duration': 0,
                'config': asdict(self.config)
            },
            'summary': self.get_codebase_summary(),
            'metrics': asdict(self.get_codebase_metrics()),
            'dead_code': self.detect_dead_code(),
            'complexity': self.analyze_complexity(),
            'dependencies': self.analyze_dependencies(),
            'security': self.analyze_security(),
            'call_graph': self.analyze_call_graph(),
            'hotspots': self.find_hotspots(),
            'circular_dependencies': self.detect_circular_dependencies(),
            'module_coupling': self.analyze_module_coupling(),
            'recommendations': self._generate_recommendations()
        }
        
        # Calculate analysis duration
        results['metadata']['analysis_duration'] = time.time() - start_time
        
        print(f"✅ Analysis completed in {results['metadata']['analysis_duration']:.2f} seconds")
        
        return results
    
    def get_codebase_summary(self) -> str:
        """Get comprehensive codebase summary."""
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        return get_codebase_summary(self.codebase)
    
    def get_file_summary(self, file: SourceFile) -> str:
        """Get comprehensive file summary."""
        return get_file_summary(file)
    
    def get_class_summary(self, cls: Class) -> str:
        """Get comprehensive class summary."""
        return get_class_summary(cls)
    
    def get_function_summary(self, func: Function) -> str:
        """Get comprehensive function summary."""
        return get_function_summary(func)
    
    def get_symbol_summary(self, symbol: Symbol) -> str:
        """Get comprehensive symbol summary."""
        return get_symbol_summary(symbol)
    
    def get_codebase_metrics(self) -> CodebaseMetrics:
        """Get comprehensive codebase metrics."""
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        return get_codebase_metrics(self.codebase)
    
    def get_file_metrics(self, file: SourceFile) -> FileMetrics:
        """Get comprehensive file metrics."""
        return get_file_metrics(file)
    
    def get_class_metrics(self, cls: Class) -> ClassMetrics:
        """Get comprehensive class metrics."""
        return get_class_metrics(cls)
    
    def get_function_metrics(self, func: Function) -> FunctionMetrics:
        """Get comprehensive function metrics."""
        return get_function_metrics(func)
    
    def detect_dead_code(self) -> Dict[str, Any]:
        """
        Detect dead code in the codebase using existing analyzer.
        
        Returns:
            Dict[str, Any]: Dead code analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        print("🔍 Analyzing dead code...")
        
        try:
            # Use existing dead code detector
            dead_code_results = detect_dead_code(self.codebase)
            return dead_code_results
        except Exception as e:
            print(f"⚠️ Error in dead code analysis: {e}")
            # Fallback to basic analysis
            return self._basic_dead_code_analysis()
    
    def _basic_dead_code_analysis(self) -> Dict[str, Any]:
        """Basic dead code analysis fallback."""
        dead_functions = []
        dead_classes = []
        dead_variables = []
        
        # Find unused functions
        for func in self.codebase.functions:
            if len(func.symbol_usages) == 0 and len(func.call_sites) == 0:
                if not (func.name in ['main', '__init__', '__main__'] or func.name.startswith('test_')):
                    dead_functions.append({
                        'name': func.name,
                        'file': func.file.name if hasattr(func, 'file') else 'unknown',
                        'line': func.span.start.row if hasattr(func, 'span') and func.span else 0
                    })
        
        # Find unused classes
        for cls in self.codebase.classes:
            if len(cls.symbol_usages) == 0:
                if not (cls.name.endswith('Base') or cls.name.endswith('Exception') or cls.name.endswith('Error')):
                    dead_classes.append({
                        'name': cls.name,
                        'file': cls.file.name if hasattr(cls, 'file') else 'unknown',
                        'line': cls.span.start.row if hasattr(cls, 'span') and cls.span else 0
                    })
        
        return {
            'dead_functions': dead_functions,
            'dead_classes': dead_classes,
            'dead_variables': dead_variables,
            'summary': {
                'total_dead_functions': len(dead_functions),
                'total_dead_classes': len(dead_classes),
                'total_dead_variables': len(dead_variables),
                'total_dead_items': len(dead_functions) + len(dead_classes) + len(dead_variables)
            }
        }
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity using existing analyzer.
        
        Returns:
            Dict[str, Any]: Complexity analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        print("🔍 Analyzing complexity...")
        
        try:
            # Use existing complexity analyzer
            complexity_results = analyze_complexity(self.codebase)
            return complexity_results
        except Exception as e:
            print(f"⚠️ Error in complexity analysis: {e}")
            # Fallback to basic analysis
            return self._basic_complexity_analysis()
    
    def _basic_complexity_analysis(self) -> Dict[str, Any]:
        """Basic complexity analysis fallback."""
        complex_functions = []
        large_functions = []
        complex_classes = []
        
        # Analyze function complexity
        for func in self.codebase.functions:
            metrics = get_function_metrics(func)
            
            if metrics.complexity_score > 20:
                complex_functions.append({
                    'name': func.name,
                    'complexity_score': metrics.complexity_score,
                    'lines_of_code': metrics.lines_of_code,
                    'file': func.file.name if hasattr(func, 'file') else 'unknown'
                })
            
            if metrics.lines_of_code > 50:
                large_functions.append({
                    'name': func.name,
                    'lines_of_code': metrics.lines_of_code,
                    'complexity_score': metrics.complexity_score,
                    'file': func.file.name if hasattr(func, 'file') else 'unknown'
                })
        
        # Analyze class complexity
        for cls in self.codebase.classes:
            metrics = get_class_metrics(cls)
            
            if metrics.methods_count > 20 or metrics.dependencies_count > 15:
                complex_classes.append({
                    'name': cls.name,
                    'methods_count': metrics.methods_count,
                    'dependencies_count': metrics.dependencies_count,
                    'file': cls.file.name if hasattr(cls, 'file') else 'unknown'
                })
        
        return {
            'complex_functions': complex_functions[:10],
            'large_functions': large_functions[:10],
            'complex_classes': complex_classes[:10],
            'summary': {
                'total_complex_functions': len(complex_functions),
                'total_large_functions': len(large_functions),
                'total_complex_classes': len(complex_classes),
                'avg_function_complexity': sum(get_function_metrics(f).complexity_score for f in self.codebase.functions) / max(len(list(self.codebase.functions)), 1)
            }
        }
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """
        Analyze dependencies and imports using existing analyzer.
        
        Returns:
            Dict[str, Any]: Dependency analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        print("🔍 Analyzing dependencies...")
        
        try:
            # Use existing dependency analyzer
            dependency_results = analyze_dependencies(self.codebase)
            return dependency_results
        except Exception as e:
            print(f"⚠️ Error in dependency analysis: {e}")
            # Fallback to basic analysis
            return self._basic_dependency_analysis()
    
    def _basic_dependency_analysis(self) -> Dict[str, Any]:
        """Basic dependency analysis fallback."""
        external_deps = {}
        internal_deps = {}
        unused_imports = []
        
        # Analyze external dependencies
        for module in self.codebase.external_modules:
            external_deps[module.name] = {
                'usage_count': len(module.symbol_usages),
                'importing_files': []
            }
        
        # Analyze internal dependencies
        for file in self.codebase.files:
            file_deps = []
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol'):
                    symbol = imp.imported_symbol
                    if hasattr(symbol, 'name'):
                        file_deps.append(symbol.name)
            
            if file_deps:
                internal_deps[file.name] = file_deps
        
        return {
            'external_dependencies': external_deps,
            'internal_dependencies': internal_deps,
            'unused_imports': unused_imports,
            'circular_dependencies': self.detect_circular_dependencies(),
            'module_coupling': self.analyze_module_coupling(),
            'summary': {
                'total_external_deps': len(external_deps),
                'total_internal_deps': len(internal_deps),
                'total_unused_imports': len(unused_imports)
            }
        }
    
    def analyze_security(self) -> Dict[str, Any]:
        """
        Analyze security issues using existing analyzer.
        
        Returns:
            Dict[str, Any]: Security analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        print("🔍 Analyzing security...")
        
        try:
            # Use existing security analyzer
            security_results = analyze_security(self.codebase)
            return security_results
        except Exception as e:
            print(f"⚠️ Error in security analysis: {e}")
            # Fallback to basic analysis
            return self._basic_security_analysis()
    
    def _basic_security_analysis(self) -> Dict[str, Any]:
        """Basic security analysis fallback."""
        security_issues = []
        dangerous_imports = []
        
        # Check for dangerous imports
        dangerous_modules = {
            'eval', 'exec', 'subprocess', 'os.system', 'pickle', 'marshal',
            'shelve', 'tempfile', 'random', 'hashlib'
        }
        
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'name'):
                    module_name = imp.imported_symbol.name
                    if any(dangerous in module_name.lower() for dangerous in dangerous_modules):
                        dangerous_imports.append({
                            'module': module_name,
                            'file': file.name,
                            'line': imp.span.start.row if hasattr(imp, 'span') and imp.span else 0,
                            'risk_level': 'high' if module_name in ['eval', 'exec', 'pickle'] else 'medium'
                        })
        
        return {
            'dangerous_imports': dangerous_imports,
            'security_issues': security_issues,
            'summary': {
                'total_dangerous_imports': len(dangerous_imports),
                'total_security_issues': len(security_issues),
                'high_risk_items': len([item for item in dangerous_imports + security_issues if item.get('risk_level') == 'high'])
            }
        }
    
    def analyze_call_graph(self) -> Dict[str, Any]:
        """
        Analyze call graph using existing analyzer.
        
        Returns:
            Dict[str, Any]: Call graph analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        print("🔍 Analyzing call graph...")
        
        try:
            # Use existing call graph analyzer
            call_graph_results = analyze_call_graph(self.codebase)
            return call_graph_results
        except Exception as e:
            print(f"⚠️ Error in call graph analysis: {e}")
            # Fallback to basic analysis
            return self._basic_call_graph_analysis()
    
    def _basic_call_graph_analysis(self) -> Dict[str, Any]:
        """Basic call graph analysis fallback."""
        call_graph = {}
        function_metrics = {}
        
        # Build call graph
        for func in self.codebase.functions:
            calls = []
            for call in func.function_calls:
                if hasattr(call, 'name'):
                    calls.append(call.name)
            
            call_graph[func.name] = {
                'calls': calls,
                'called_by': [site.name for site in func.call_sites if hasattr(site, 'name')],
                'usage_count': len(func.symbol_usages),
                'call_count': len(func.call_sites)
            }
            
            # Calculate function metrics
            metrics = get_function_metrics(func)
            function_metrics[func.name] = asdict(metrics)
        
        return {
            'call_graph': call_graph,
            'function_metrics': function_metrics,
            'hotspots': self.find_hotspots(),
            'summary': {
                'total_functions': len(call_graph),
                'total_calls': sum(len(data['calls']) for data in call_graph.values()),
                'avg_calls_per_function': sum(len(data['calls']) for data in call_graph.values()) / max(len(call_graph), 1)
            }
        }
    
    def find_hotspots(self) -> List[Dict[str, Any]]:
        """Find function hotspots (heavily used functions)."""
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        try:
            # Use existing hotspot finder
            hotspot_functions = find_hotspots(self.codebase)
            return hotspot_functions
        except Exception as e:
            print(f"⚠️ Error finding hotspots: {e}")
            # Fallback to basic analysis
            hotspot_functions = find_hotspot_functions(self.codebase, threshold=5)
            
            return [
                {
                    'name': func.name,
                    'usage_count': len(func.symbol_usages),
                    'call_sites_count': len(func.call_sites),
                    'total_usage': len(func.symbol_usages) + len(func.call_sites),
                    'file': func.file.name if hasattr(func, 'file') else 'unknown'
                }
                for func in hotspot_functions[:20]  # Top 20 hotspots
            ]
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies."""
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        try:
            # Use existing circular dependency detector
            return detect_circular_deps(self.codebase)
        except Exception as e:
            print(f"⚠️ Error detecting circular dependencies: {e}")
            # Fallback to basic analysis
            return analyze_circular_dependencies(self.codebase)
    
    def analyze_module_coupling(self) -> Dict[str, Dict[str, int]]:
        """Analyze module coupling."""
        if not self.codebase:
            raise ValueError("No codebase set for analysis")
        
        try:
            # Use existing module coupling analyzer
            return analyze_coupling(self.codebase)
        except Exception as e:
            print(f"⚠️ Error analyzing module coupling: {e}")
            # Fallback to basic analysis
            return analyze_module_coupling(self.codebase)
    
    def export_analysis(self, filepath: str, analysis_results: Optional[Dict[str, Any]] = None) -> None:
        """
        Export analysis results to a file.
        
        Args:
            filepath: Path to export the results
            analysis_results: Optional analysis results. If None, runs comprehensive analysis.
        """
        if analysis_results is None:
            analysis_results = self.comprehensive_analysis()
        
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix.lower() == '.json':
            with open(output_path, 'w') as f:
                json.dump(analysis_results, f, indent=2, default=str)
        else:
            # Export as text report
            with open(output_path, 'w') as f:
                f.write(self._generate_text_report(analysis_results))
        
        print(f"📄 Analysis results exported to: {filepath}")
    
    def _get_basic_codebase_info(self) -> Dict[str, int]:
        """Get basic codebase information."""
        return {
            'total_files': len(list(self.codebase.files)),
            'total_functions': len(list(self.codebase.functions)),
            'total_classes': len(list(self.codebase.classes)),
            'total_symbols': len(list(self.codebase.symbols)),
            'total_imports': len(list(self.codebase.imports)),
            'total_external_modules': len(list(self.codebase.external_modules))
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if not self.codebase:
            return recommendations
        
        # Analyze metrics for recommendations
        metrics = get_codebase_metrics(self.codebase)
        
        # Complexity recommendations
        if metrics.total_edges / max(metrics.total_nodes, 1) > 3:
            recommendations.append("Consider refactoring to reduce code complexity - high edge-to-node ratio detected")
        
        # Dead code recommendations
        dead_code = self.detect_dead_code()
        if dead_code['summary']['total_dead_items'] > 0:
            recommendations.append(f"Remove {dead_code['summary']['total_dead_items']} dead code items to improve maintainability")
        
        # Security recommendations
        security = self.analyze_security()
        if security['summary']['high_risk_items'] > 0:
            recommendations.append(f"Review {security['summary']['high_risk_items']} high-risk security items")
        
        # Dependency recommendations
        circular_deps = self.detect_circular_dependencies()
        if circular_deps:
            recommendations.append(f"Resolve {len(circular_deps)} circular dependencies to improve architecture")
        
        # Performance recommendations
        hotspots = self.find_hotspots()
        if len(hotspots) > 10:
            recommendations.append("Consider optimizing hotspot functions - many heavily used functions detected")
        
        return recommendations
    
    def _generate_text_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a text report from analysis results."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE CODEBASE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {analysis_results['metadata']['analysis_timestamp']}")
        report.append(f"Duration: {analysis_results['metadata']['analysis_duration']:.2f} seconds")
        report.append("")
        
        # Summary
        report.append("CODEBASE SUMMARY")
        report.append("-" * 40)
        report.append(analysis_results['summary'])
        report.append("")
        
        # Dead Code
        if analysis_results['dead_code']['summary']['total_dead_items'] > 0:
            report.append("DEAD CODE ANALYSIS")
            report.append("-" * 40)
            report.append(f"Total dead items: {analysis_results['dead_code']['summary']['total_dead_items']}")
            report.append(f"Dead functions: {analysis_results['dead_code']['summary']['total_dead_functions']}")
            report.append(f"Dead classes: {analysis_results['dead_code']['summary']['total_dead_classes']}")
            report.append(f"Dead variables: {analysis_results['dead_code']['summary']['total_dead_variables']}")
            report.append("")
        
        # Complexity
        report.append("COMPLEXITY ANALYSIS")
        report.append("-" * 40)
        complexity = analysis_results['complexity']['summary']
        report.append(f"Complex functions: {complexity['total_complex_functions']}")
        report.append(f"Large functions: {complexity['total_large_functions']}")
        report.append(f"Complex classes: {complexity['total_complex_classes']}")
        report.append(f"Average function complexity: {complexity['avg_function_complexity']:.2f}")
        report.append("")
        
        # Security
        if analysis_results['security']['summary']['total_security_issues'] > 0:
            report.append("SECURITY ANALYSIS")
            report.append("-" * 40)
            security = analysis_results['security']['summary']
            report.append(f"Dangerous imports: {security['total_dangerous_imports']}")
            report.append(f"Security issues: {security['total_security_issues']}")
            report.append(f"High risk items: {security['high_risk_items']}")
            report.append("")
        
        # Recommendations
        if analysis_results['recommendations']:
            report.append("RECOMMENDATIONS")
            report.append("-" * 40)
            for i, rec in enumerate(analysis_results['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)


# Export main functions for backward compatibility
__all__ = [
    'Analysis',
    'get_codebase_summary',
    'get_file_summary', 
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'get_optimized_config',
    'CodebaseMetrics',
    'FunctionMetrics',
    'ClassMetrics',
    'FileMetrics'
]

