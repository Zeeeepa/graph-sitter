#!/usr/bin/env python3
"""
Basic Analysis Pipeline Prototype
Demonstrates core Graph-Sitter functionality for codebase analysis.
"""

import json
import time
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.enums import UsageType
except ImportError:
    print("Graph-Sitter not available. This is a prototype implementation.")
    # Mock classes for demonstration
    class Codebase:
        def __init__(self, path, config=None):
            self.path = path
            self.config = config
            
    class CodebaseConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
                
    class UsageType:
        DIRECT = "direct"
        INDIRECT = "indirect"
        CHAINED = "chained"
        ALIASED = "aliased"


@dataclass
class AnalysisMetrics:
    """Container for analysis metrics."""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_exports: int = 0
    lines_of_code: int = 0
    average_complexity: float = 0.0
    max_complexity: int = 0
    high_complexity_functions: int = 0
    dead_code_count: int = 0
    circular_dependencies: int = 0
    analysis_duration_seconds: float = 0.0
    memory_usage_mb: float = 0.0


@dataclass
class SymbolAnalysis:
    """Container for symbol analysis results."""
    name: str
    type: str
    file_path: str
    line_number: int
    complexity: int = 0
    dependencies_count: int = 0
    usages_count: int = 0
    is_dead_code: bool = False
    is_highly_coupled: bool = False


@dataclass
class DependencyAnalysis:
    """Container for dependency analysis results."""
    source_symbol: str
    target_symbol: str
    dependency_type: str
    usage_type: str
    file_path: str
    line_number: int
    confidence: float = 1.0


class BasicAnalysisPipeline:
    """
    Basic analysis pipeline demonstrating Graph-Sitter capabilities.
    """
    
    def __init__(self, repo_path: str, config: Optional[CodebaseConfig] = None):
        """Initialize the analysis pipeline."""
        self.repo_path = Path(repo_path)
        self.config = config or self._create_default_config()
        self.codebase: Optional[Codebase] = None
        self.metrics = AnalysisMetrics()
        
    def _create_default_config(self) -> CodebaseConfig:
        """Create default configuration for analysis."""
        return CodebaseConfig(
            debug=False,
            parallel_processing=True,
            precompute_dependencies=True,
            lazy_loading=True,
            memory_limit="2GB"
        )
    
    @contextmanager
    def performance_monitor(self):
        """Context manager for performance monitoring."""
        process = psutil.Process()
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            self.metrics.analysis_duration_seconds = end_time - start_time
            self.metrics.memory_usage_mb = end_memory - start_memory
    
    def initialize_codebase(self) -> bool:
        """Initialize and parse the codebase."""
        try:
            print(f"Initializing codebase analysis for: {self.repo_path}")
            
            with self.performance_monitor():
                self.codebase = Codebase(str(self.repo_path), config=self.config)
                
                # Validate analysis completeness
                if hasattr(self.codebase, 'is_analysis_complete'):
                    if not self.codebase.is_analysis_complete():
                        print("Warning: Codebase analysis may be incomplete")
                        return False
            
            print(f"Codebase initialized in {self.metrics.analysis_duration_seconds:.2f}s")
            print(f"Memory usage: {self.metrics.memory_usage_mb:.2f}MB")
            return True
            
        except Exception as e:
            print(f"Error initializing codebase: {e}")
            return False
    
    def extract_basic_metrics(self) -> AnalysisMetrics:
        """Extract basic codebase metrics."""
        if not self.codebase:
            return self.metrics
            
        try:
            # Basic counts
            if hasattr(self.codebase, 'files'):
                self.metrics.total_files = len(self.codebase.files)
                self.metrics.lines_of_code = sum(
                    getattr(f, 'line_count', 0) for f in self.codebase.files
                )
            
            if hasattr(self.codebase, 'functions'):
                self.metrics.total_functions = len(self.codebase.functions)
                
                # Complexity analysis
                complexities = [
                    getattr(f, 'complexity', 0) for f in self.codebase.functions
                ]
                if complexities:
                    self.metrics.average_complexity = sum(complexities) / len(complexities)
                    self.metrics.max_complexity = max(complexities)
                    self.metrics.high_complexity_functions = len([c for c in complexities if c > 10])
            
            if hasattr(self.codebase, 'classes'):
                self.metrics.total_classes = len(self.codebase.classes)
            
            if hasattr(self.codebase, 'imports'):
                self.metrics.total_imports = len(self.codebase.imports)
            
            if hasattr(self.codebase, 'exports'):
                self.metrics.total_exports = len(self.codebase.exports)
            
            # Dead code analysis
            if hasattr(self.codebase, 'functions'):
                dead_functions = [
                    f for f in self.codebase.functions 
                    if hasattr(f, 'usages') and not f.usages
                ]
                self.metrics.dead_code_count = len(dead_functions)
            
            # Circular dependencies
            if hasattr(self.codebase, 'find_circular_dependencies'):
                circular_deps = self.codebase.find_circular_dependencies()
                self.metrics.circular_dependencies = len(circular_deps)
            
        except Exception as e:
            print(f"Error extracting metrics: {e}")
        
        return self.metrics
    
    def analyze_symbols(self, limit: int = 100) -> List[SymbolAnalysis]:
        """Analyze symbols and their relationships."""
        if not self.codebase:
            return []
        
        symbol_analyses = []
        
        try:
            # Analyze functions
            if hasattr(self.codebase, 'functions'):
                for i, function in enumerate(self.codebase.functions[:limit]):
                    analysis = SymbolAnalysis(
                        name=getattr(function, 'name', f'function_{i}'),
                        type='function',
                        file_path=getattr(function, 'file_path', 'unknown'),
                        line_number=getattr(function, 'line_number', 0),
                        complexity=getattr(function, 'complexity', 0),
                        dependencies_count=len(getattr(function, 'dependencies', [])),
                        usages_count=len(getattr(function, 'usages', [])),
                        is_dead_code=not bool(getattr(function, 'usages', [])),
                        is_highly_coupled=len(getattr(function, 'dependencies', [])) > 10
                    )
                    symbol_analyses.append(analysis)
            
            # Analyze classes
            if hasattr(self.codebase, 'classes'):
                for i, cls in enumerate(self.codebase.classes[:limit]):
                    analysis = SymbolAnalysis(
                        name=getattr(cls, 'name', f'class_{i}'),
                        type='class',
                        file_path=getattr(cls, 'file_path', 'unknown'),
                        line_number=getattr(cls, 'line_number', 0),
                        dependencies_count=len(getattr(cls, 'dependencies', [])),
                        usages_count=len(getattr(cls, 'usages', [])),
                        is_dead_code=not bool(getattr(cls, 'usages', [])),
                        is_highly_coupled=len(getattr(cls, 'dependencies', [])) > 5
                    )
                    symbol_analyses.append(analysis)
                    
        except Exception as e:
            print(f"Error analyzing symbols: {e}")
        
        return symbol_analyses
    
    def analyze_dependencies(self, limit: int = 100) -> List[DependencyAnalysis]:
        """Analyze dependency relationships."""
        if not self.codebase:
            return []
        
        dependency_analyses = []
        
        try:
            if hasattr(self.codebase, 'functions'):
                for function in self.codebase.functions[:limit]:
                    if hasattr(function, 'dependencies'):
                        for dep in function.dependencies:
                            analysis = DependencyAnalysis(
                                source_symbol=getattr(function, 'name', 'unknown'),
                                target_symbol=getattr(dep, 'name', 'unknown'),
                                dependency_type='direct',  # Simplified for prototype
                                usage_type='reference',    # Simplified for prototype
                                file_path=getattr(function, 'file_path', 'unknown'),
                                line_number=getattr(function, 'line_number', 0)
                            )
                            dependency_analyses.append(analysis)
                            
        except Exception as e:
            print(f"Error analyzing dependencies: {e}")
        
        return dependency_analyses
    
    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        report = {
            'metadata': {
                'repository_path': str(self.repo_path),
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'graph_sitter_version': 'prototype',
                'configuration': asdict(self.config) if hasattr(self.config, '__dict__') else {}
            },
            'metrics': asdict(self.metrics),
            'symbols': [asdict(s) for s in self.analyze_symbols()],
            'dependencies': [asdict(d) for d in self.analyze_dependencies()],
            'recommendations': self._generate_recommendations()
        }
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"Report saved to: {output_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        if self.metrics.dead_code_count > 0:
            recommendations.append(
                f"Found {self.metrics.dead_code_count} unused functions that can be removed"
            )
        
        if self.metrics.high_complexity_functions > 0:
            recommendations.append(
                f"Found {self.metrics.high_complexity_functions} high-complexity functions "
                f"(complexity > 10) that should be refactored"
            )
        
        if self.metrics.circular_dependencies > 0:
            recommendations.append(
                f"Found {self.metrics.circular_dependencies} circular dependencies "
                f"that need resolution"
            )
        
        if self.metrics.average_complexity > 5:
            recommendations.append(
                f"Average function complexity ({self.metrics.average_complexity:.1f}) "
                f"is above recommended threshold (5)"
            )
        
        if not recommendations:
            recommendations.append("Codebase appears to be in good health!")
        
        return recommendations
    
    def run_analysis(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run complete analysis pipeline."""
        print("Starting Graph-Sitter analysis pipeline...")
        
        # Initialize codebase
        if not self.initialize_codebase():
            return {'error': 'Failed to initialize codebase'}
        
        # Extract metrics
        print("Extracting codebase metrics...")
        self.extract_basic_metrics()
        
        # Generate report
        print("Generating analysis report...")
        report = self.generate_report(output_path)
        
        # Print summary
        self._print_summary()
        
        return report
    
    def _print_summary(self):
        """Print analysis summary to console."""
        print("\n" + "="*60)
        print("GRAPH-SITTER ANALYSIS SUMMARY")
        print("="*60)
        print(f"Repository: {self.repo_path}")
        print(f"Analysis Duration: {self.metrics.analysis_duration_seconds:.2f}s")
        print(f"Memory Usage: {self.metrics.memory_usage_mb:.2f}MB")
        print()
        print("CODEBASE METRICS:")
        print(f"  Files: {self.metrics.total_files}")
        print(f"  Functions: {self.metrics.total_functions}")
        print(f"  Classes: {self.metrics.total_classes}")
        print(f"  Lines of Code: {self.metrics.lines_of_code}")
        print(f"  Imports: {self.metrics.total_imports}")
        print(f"  Exports: {self.metrics.total_exports}")
        print()
        print("QUALITY METRICS:")
        print(f"  Average Complexity: {self.metrics.average_complexity:.1f}")
        print(f"  Max Complexity: {self.metrics.max_complexity}")
        print(f"  High Complexity Functions: {self.metrics.high_complexity_functions}")
        print(f"  Dead Code Count: {self.metrics.dead_code_count}")
        print(f"  Circular Dependencies: {self.metrics.circular_dependencies}")
        print("="*60)


def main():
    """Main function for running the analysis pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Graph-Sitter Basic Analysis Pipeline')
    parser.add_argument('repo_path', help='Path to the repository to analyze')
    parser.add_argument('--output', '-o', help='Output file for the analysis report')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel processing')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create configuration
    config = CodebaseConfig(
        debug=args.debug,
        parallel_processing=args.parallel,
        precompute_dependencies=True,
        lazy_loading=True
    )
    
    # Run analysis
    pipeline = BasicAnalysisPipeline(args.repo_path, config)
    report = pipeline.run_analysis(args.output)
    
    if 'error' in report:
        print(f"Analysis failed: {report['error']}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

