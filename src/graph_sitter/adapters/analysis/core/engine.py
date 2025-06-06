#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS ENGINE 🚀

Unified analysis engine that consolidates all graph-sitter enhanced analysis capabilities
into a single, powerful, and easy-to-use system.

This engine combines:
- Enhanced graph-sitter integration
- Advanced codebase analysis
- Import loop detection
- Dead code detection
- Training data generation
- Comprehensive metrics
- Tree-sitter query patterns
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    import networkx as nx
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False
    # Create dummy classes for type hints
    class Codebase: pass
    class CodebaseConfig: pass
    class ExternalModule: pass
    class Import: pass
    class Symbol: pass
    class EdgeType: pass
    class SymbolType: pass


@dataclass
class AnalysisConfig:
    """Configuration for comprehensive analysis."""
    # Performance settings
    use_advanced_config: bool = True
    enable_method_usages: bool = True
    enable_generics: bool = True
    enable_sync: bool = True
    
    # Analysis features
    detect_import_loops: bool = True
    detect_dead_code: bool = True
    generate_training_data: bool = False
    analyze_graph_structure: bool = True
    
    # Output settings
    include_source_locations: bool = True
    include_metrics: bool = True
    include_visualizations: bool = False
    
    # Filtering
    ignore_external_modules: bool = True
    ignore_test_files: bool = False
    file_extensions: Optional[List[str]] = None


@dataclass
class ImportLoop:
    """Represents a circular import dependency."""
    files: List[str]
    loop_type: str  # 'static', 'dynamic', 'mixed'
    severity: str   # 'critical', 'warning', 'info'
    imports: List[Dict[str, Any]]


@dataclass
class DeadCodeItem:
    """Represents dead/unused code."""
    type: str  # 'function', 'class', 'variable'
    name: str
    file_path: str
    line_start: int
    line_end: int
    reason: str
    confidence: float


@dataclass
class TrainingDataItem:
    """Training data item for ML models."""
    implementation: Dict[str, str]
    dependencies: List[Dict[str, str]]
    usages: List[Dict[str, str]]
    metadata: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Comprehensive analysis results."""
    # Basic metrics
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    
    # Enhanced analysis
    import_loops: List[ImportLoop] = field(default_factory=list)
    dead_code: List[DeadCodeItem] = field(default_factory=list)
    training_data: List[TrainingDataItem] = field(default_factory=list)
    
    # Graph analysis
    graph_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Performance
    analysis_time: float = 0.0
    
    # Metadata
    config: Optional[AnalysisConfig] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save results to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())


class ComprehensiveAnalysisEngine:
    """
    Unified analysis engine that combines all enhanced analysis capabilities.
    
    This engine provides a single interface for:
    - Enhanced graph-sitter analysis
    - Import loop detection
    - Dead code detection
    - Training data generation
    - Comprehensive metrics
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine."""
        self.config = config or AnalysisConfig()
        self.codebase_config = self._create_codebase_config()
        
    def _create_codebase_config(self) -> Optional[CodebaseConfig]:
        """Create advanced CodebaseConfig with enhanced features."""
        if not GRAPH_SITTER_AVAILABLE or not self.config.use_advanced_config:
            return None
        
        try:
            return CodebaseConfig(
                # Performance optimizations
                method_usages=self.config.enable_method_usages,
                generics=self.config.enable_generics,
                sync_enabled=self.config.enable_sync,
                
                # Advanced analysis
                full_range_index=True,
                py_resolve_syspath=True,
                
                # Debugging disabled for performance
                debug=False,
                verify_graph=False,
                track_graph=False,
                
                # Experimental features
                exp_lazy_graph=False,
            )
        except Exception as e:
            logger.warning(f"Could not create advanced config: {e}")
            return None
    
    def analyze(self, path: Union[str, Path]) -> AnalysisResult:
        """
        Perform comprehensive analysis of a codebase.
        
        Args:
            path: Path to the codebase to analyze
            
        Returns:
            AnalysisResult containing all analysis data
        """
        if not GRAPH_SITTER_AVAILABLE:
            logger.error("Graph-sitter not available")
            return AnalysisResult()
        
        start_time = time.time()
        logger.info(f"Starting comprehensive analysis of: {path}")
        
        try:
            # Initialize codebase
            if self.codebase_config:
                codebase = Codebase(str(path), config=self.codebase_config)
                logger.info("Using advanced CodebaseConfig")
            else:
                codebase = Codebase(str(path))
                logger.info("Using default configuration")
            
            # Initialize result
            result = AnalysisResult(
                config=self.config,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Basic metrics
            result.total_files = len(codebase.files)
            result.total_functions = len(codebase.functions)
            result.total_classes = len(codebase.classes)
            result.total_imports = len(codebase.imports)
            
            logger.info(f"Found {result.total_files} files, {result.total_functions} functions, {result.total_classes} classes")
            
            # Enhanced analysis
            if self.config.detect_import_loops:
                result.import_loops = self._detect_import_loops(codebase)
                logger.info(f"Detected {len(result.import_loops)} import loops")
            
            if self.config.detect_dead_code:
                result.dead_code = self._detect_dead_code(codebase)
                logger.info(f"Found {len(result.dead_code)} dead code items")
            
            if self.config.analyze_graph_structure:
                result.graph_metrics = self._analyze_graph_structure(codebase)
                logger.info("Completed graph structure analysis")
            
            if self.config.generate_training_data:
                result.training_data = self._generate_training_data(codebase)
                logger.info(f"Generated {len(result.training_data)} training data items")
            
            # Record analysis time
            result.analysis_time = time.time() - start_time
            logger.info(f"Analysis completed in {result.analysis_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            result = AnalysisResult(
                config=self.config,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                analysis_time=time.time() - start_time
            )
            return result
    
    def _detect_import_loops(self, codebase) -> List[ImportLoop]:
        """Detect circular import dependencies."""
        loops = []
        
        try:
            # Build import graph
            import_graph = nx.DiGraph()
            
            for file in codebase.files:
                file_path = str(file.filepath)
                import_graph.add_node(file_path)
                
                for import_stmt in file.imports:
                    if hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                        if hasattr(import_stmt.resolved_symbol, 'file'):
                            target_file = str(import_stmt.resolved_symbol.file.filepath)
                            import_graph.add_edge(file_path, target_file)
            
            # Find cycles
            try:
                cycles = list(nx.simple_cycles(import_graph))
                for cycle in cycles:
                    if len(cycle) > 1:  # Ignore self-loops
                        loop = ImportLoop(
                            files=cycle,
                            loop_type='static',
                            severity='warning' if len(cycle) == 2 else 'critical',
                            imports=[]
                        )
                        loops.append(loop)
            except Exception as e:
                logger.warning(f"Error detecting cycles: {e}")
                
        except Exception as e:
            logger.warning(f"Error building import graph: {e}")
        
        return loops
    
    def _detect_dead_code(self, codebase) -> List[DeadCodeItem]:
        """Detect unused/dead code."""
        dead_code = []
        
        try:
            # Check for unused functions
            for function in codebase.functions:
                if hasattr(function, 'usages') and len(function.usages) == 0:
                    # Skip if it's a main function or has special decorators
                    if function.name in ['main', '__main__', '__init__']:
                        continue
                    
                    dead_item = DeadCodeItem(
                        type='function',
                        name=function.name,
                        file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
                        line_start=function.start_point[0] if hasattr(function, 'start_point') else 0,
                        line_end=function.end_point[0] if hasattr(function, 'end_point') else 0,
                        reason='No usages found',
                        confidence=0.8
                    )
                    dead_code.append(dead_item)
            
            # Check for unused classes
            for cls in codebase.classes:
                if hasattr(cls, 'usages') and len(cls.usages) == 0:
                    dead_item = DeadCodeItem(
                        type='class',
                        name=cls.name,
                        file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
                        line_start=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                        line_end=cls.end_point[0] if hasattr(cls, 'end_point') else 0,
                        reason='No usages found',
                        confidence=0.7
                    )
                    dead_code.append(dead_item)
                    
        except Exception as e:
            logger.warning(f"Error detecting dead code: {e}")
        
        return dead_code
    
    def _analyze_graph_structure(self, codebase) -> Dict[str, Any]:
        """Analyze the graph structure of the codebase."""
        metrics = {}
        
        try:
            # Basic graph metrics
            if hasattr(codebase, 'graph'):
                graph = codebase.graph
                metrics.update({
                    'total_nodes': graph.number_of_nodes() if hasattr(graph, 'number_of_nodes') else 0,
                    'total_edges': graph.number_of_edges() if hasattr(graph, 'number_of_edges') else 0,
                })
            
            # Symbol type distribution
            symbol_types = {}
            for symbol in codebase.symbols:
                symbol_type = symbol.__class__.__name__
                symbol_types[symbol_type] = symbol_types.get(symbol_type, 0) + 1
            
            metrics['symbol_distribution'] = symbol_types
            
            # File type distribution
            file_extensions = {}
            for file in codebase.files:
                ext = Path(file.filepath).suffix
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            metrics['file_extensions'] = file_extensions
            
        except Exception as e:
            logger.warning(f"Error analyzing graph structure: {e}")
        
        return metrics
    
    def _generate_training_data(self, codebase) -> List[TrainingDataItem]:
        """Generate training data for ML models."""
        training_data = []
        
        try:
            # Generate training data for functions
            for function in codebase.functions[:100]:  # Limit for performance
                try:
                    # Get function context
                    dependencies = []
                    if hasattr(function, 'dependencies'):
                        for dep in function.dependencies:
                            if hasattr(dep, 'name'):
                                dependencies.append({
                                    'name': dep.name,
                                    'type': dep.__class__.__name__
                                })
                    
                    usages = []
                    if hasattr(function, 'usages'):
                        for usage in function.usages:
                            if hasattr(usage, 'file'):
                                usages.append({
                                    'file': str(usage.file.filepath),
                                    'line': usage.start_point[0] if hasattr(usage, 'start_point') else 0
                                })
                    
                    training_item = TrainingDataItem(
                        implementation={
                            'name': function.name,
                            'source': function.source if hasattr(function, 'source') else '',
                            'filepath': str(function.filepath) if hasattr(function, 'filepath') else ''
                        },
                        dependencies=dependencies,
                        usages=usages,
                        metadata={
                            'is_method': hasattr(function, 'is_method') and function.is_method,
                            'is_async': hasattr(function, 'is_async') and function.is_async,
                            'parameter_count': len(function.parameters) if hasattr(function, 'parameters') else 0
                        }
                    )
                    training_data.append(training_item)
                    
                except Exception as e:
                    logger.debug(f"Error processing function {function.name}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error generating training data: {e}")
        
        return training_data


def analyze_codebase(path: Union[str, Path], config: Optional[AnalysisConfig] = None) -> AnalysisResult:
    """
    Convenience function for comprehensive codebase analysis.
    
    Args:
        path: Path to the codebase to analyze
        config: Optional analysis configuration
        
    Returns:
        AnalysisResult containing all analysis data
    """
    engine = ComprehensiveAnalysisEngine(config)
    return engine.analyze(path)


def quick_analysis(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Quick analysis with basic metrics only.
    
    Args:
        path: Path to the codebase to analyze
        
    Returns:
        Dictionary with basic analysis results
    """
    config = AnalysisConfig(
        detect_import_loops=False,
        detect_dead_code=False,
        generate_training_data=False,
        analyze_graph_structure=True
    )
    
    result = analyze_codebase(path, config)
    return {
        'files': result.total_files,
        'functions': result.total_functions,
        'classes': result.total_classes,
        'imports': result.total_imports,
        'analysis_time': result.analysis_time,
        'graph_metrics': result.graph_metrics
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python engine.py <path_to_analyze>")
        sys.exit(1)
    
    path = sys.argv[1]
    print(f"🚀 Analyzing codebase: {path}")
    
    result = analyze_codebase(path)
    
    print(f"\n📊 Analysis Results:")
    print(f"Files: {result.total_files}")
    print(f"Functions: {result.total_functions}")
    print(f"Classes: {result.total_classes}")
    print(f"Imports: {result.total_imports}")
    print(f"Import Loops: {len(result.import_loops)}")
    print(f"Dead Code Items: {len(result.dead_code)}")
    print(f"Analysis Time: {result.analysis_time:.2f}s")
    
    # Save results
    output_file = f"analysis_results_{int(time.time())}.json"
    result.save_to_file(output_file)
    print(f"\n💾 Results saved to: {output_file}")
