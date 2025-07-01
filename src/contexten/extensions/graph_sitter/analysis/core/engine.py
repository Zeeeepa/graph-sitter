#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS ENGINE - ENHANCED WITH ADVANCED FEATURES 🚀

A unified analysis engine that consolidates all analysis capabilities:
- Core quality metrics (maintainability, complexity, Halstead, etc.)
- Advanced investigation features (function context, relationships)
- Import loop detection and circular dependency analysis
- Training data generation for LLMs
- Dead code detection using usage analysis
- Advanced graph structure analysis
- Tree-sitter query patterns and visualization
- Performance optimizations with lazy loading
- Enhanced configuration with CodebaseConfig

Enhanced Features from Legacy Integration:
- Graph-sitter pre-computed element access
- Function/class dependency and usage analysis
- Import relationship mapping and loop detection
- Training data extraction for ML models
- Advanced visualization and reporting
- Performance optimizations with caching

PHASE 2 ENHANCEMENTS:
- Tree-sitter query patterns for advanced syntax analysis
- Interactive HTML reports with D3.js integration
- Performance optimizations with caching and parallel processing
- Advanced CodebaseConfig usage with all flags
- Custom analysis pipelines and feature toggles
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import networkx, but make it optional
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available - advanced graph analysis will be limited")

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False
    # Create dummy classes for type hints
    class Codebase: pass
    class CodebaseConfig: pass


# Phase 2 imports - Advanced modules
try:
    from ..enhanced.tree_sitter_queries import (
        TreeSitterQueryEngine, QueryPattern, QueryResult, analyze_with_queries
    )
    from ..visualization.interactive_reports import (
        InteractiveReportGenerator, ReportConfig, create_interactive_report
    )
    from ..core.performance import (
        PerformanceOptimizer, PerformanceConfig, create_optimizer
    )
    from ..config.advanced_config import (
        AdvancedCodebaseConfig, create_optimized_config, create_production_config
    )
    PHASE2_MODULES_AVAILABLE = True
    logger.info("Phase 2 modules loaded successfully")
except ImportError as e:
    PHASE2_MODULES_AVAILABLE = False
    logger.warning(f"Phase 2 modules not available: {e}")

try:
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    # Create dummy classes for type hints
    class ExternalModule: pass
    class Import: pass
    class Symbol: pass
    class EdgeType: pass
    class SymbolType: pass


@dataclass
class AnalysisConfig:
    """Configuration for comprehensive analysis."""
    # Phase 1 features
    detect_import_loops: bool = True
    detect_dead_code: bool = True
    generate_training_data: bool = False
    analyze_graph_structure: bool = True
    use_advanced_config: bool = True
    
    # File filtering
    ignore_external_modules: bool = True
    ignore_test_files: bool = False
    file_extensions: Optional[List[str]] = None
    
    # Enhanced metrics
    enhanced_metrics: bool = True
    max_functions: int = 100
    max_classes: int = 100
    
    # Phase 2 features - Tree-sitter queries
    enable_query_patterns: bool = True
    query_categories: List[str] = field(default_factory=lambda: ["function", "class", "security", "performance"])
    custom_query_patterns: List[str] = field(default_factory=list)
    
    # Phase 2 features - Visualization
    generate_html_report: bool = False
    html_report_path: Optional[str] = None
    report_theme: str = "default"  # default, dark, light, professional
    include_interactive_charts: bool = True
    
    # Phase 2 features - Performance optimization
    enable_performance_optimization: bool = True
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    cache_backend: str = "memory"  # memory, file, redis
    max_workers: Optional[int] = None
    
    # Phase 2 features - Advanced configuration
    codebase_language: Optional[str] = None
    codebase_size: str = "medium"  # small, medium, large
    optimization_level: str = "balanced"  # minimal, balanced, aggressive
    enable_lazy_graph: bool = True
    enable_method_usages: bool = True
    enable_generics: bool = True


@dataclass
class ImportLoop:
    """Represents a circular import dependency."""
    files: List[str]
    loop_type: str  # 'static', 'dynamic', 'mixed'
    severity: str   # 'critical', 'warning', 'info'
    imports: List[Dict[str, Any]]


@dataclass
class TrainingDataItem:
    """Training data item for ML models."""
    function_name: str
    file_path: str
    source_code: str
    dependencies: List[str]
    usages: List[str]
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeadCodeItem:
    """Represents potentially dead/unused code."""
    name: str
    type: str  # 'function', 'class', 'variable'
    file_path: str
    line_number: int
    reason: str
    confidence: float  # 0.0 to 1.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class GraphAnalysisResult:
    """Results from graph structure analysis."""
    total_nodes: int
    total_edges: int
    connected_components: int
    average_degree: float
    clustering_coefficient: float
    longest_path: int
    cycles: List[List[str]]
    central_nodes: List[str]
    isolated_nodes: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedFunctionMetrics:
    """Enhanced function metrics using graph-sitter."""
    name: str
    file_path: str
    line_count: int
    complexity: int
    dependencies: List[str]
    dependents: List[str]
    call_count: int
    parameter_count: int
    return_complexity: int
    docstring_quality: float
    test_coverage: float
    maintainability_index: float
    halstead_metrics: Dict[str, Any] = field(default_factory=dict)
    graph_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedClassMetrics:
    """Enhanced class metrics using graph-sitter."""
    name: str
    file_path: str
    method_count: int
    attribute_count: int
    inheritance_depth: int
    coupling: int
    cohesion: float
    complexity: int
    dependencies: List[str]
    dependents: List[str]
    test_coverage: float
    maintainability_index: float
    design_patterns: List[str] = field(default_factory=list)
    graph_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Results from comprehensive codebase analysis."""
    
    # Basic metrics
    path: str = ""
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_lines: int = 0
    
    # Enhanced analysis
    import_loops: List[ImportLoop] = field(default_factory=list)
    dead_code: List[DeadCodeItem] = field(default_factory=list)
    training_data: List[TrainingDataItem] = field(default_factory=list)
    
    # Graph analysis
    graph_analysis: Optional[GraphAnalysisResult] = None
    
    # Enhanced metrics
    enhanced_function_metrics: List[EnhancedFunctionMetrics] = field(default_factory=list)
    enhanced_class_metrics: List[EnhancedClassMetrics] = field(default_factory=list)
    
    # Summary and recommendations
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    # Performance
    analysis_time: float = 0.0
    
    # Configuration used
    config: Optional[AnalysisConfig] = None
    
    # Phase 2 results - Query patterns
    query_results: List[Any] = field(default_factory=list)  # List[QueryResult] when available
    pattern_matches: Dict[str, int] = field(default_factory=dict)
    
    # Phase 2 results - Visualization
    html_report_path: Optional[str] = None
    interactive_charts: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 2 results - Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    cache_statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComprehensiveAnalysisEngine:
    """
    Enhanced comprehensive analysis engine with advanced features.
    
    This engine consolidates all analysis capabilities including:
    - Import loop detection
    - Dead code analysis
    - Training data generation
    - Graph structure analysis
    - Enhanced function and class metrics
    - Performance optimizations
    
    Phase 2 enhancements:
    - Tree-sitter query patterns for advanced syntax analysis
    - Interactive HTML reports with D3.js integration
    - Performance optimizations with caching and parallel processing
    - Advanced CodebaseConfig usage with all flags
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine."""
        self.config = config or AnalysisConfig()
        self.codebase_config = self._create_advanced_config() if GRAPH_SITTER_AVAILABLE else None
        
        # Phase 2 components
        self.query_engine = None
        self.report_generator = None
        self.performance_optimizer = None
        
        if PHASE2_MODULES_AVAILABLE:
            self._initialize_phase2_components()
    
    def _initialize_phase2_components(self):
        """Initialize Phase 2 components."""
        try:
            # Initialize query engine
            if self.config.enable_query_patterns:
                self.query_engine = TreeSitterQueryEngine()
                logger.info("Tree-sitter query engine initialized")
            
            # Initialize report generator
            if self.config.generate_html_report:
                report_config = ReportConfig(
                    theme=self.config.report_theme,
                    include_navigation=True,
                    include_search=True,
                    include_filters=True
                )
                self.report_generator = InteractiveReportGenerator(report_config)
                logger.info("Interactive report generator initialized")
            
            # Initialize performance optimizer
            if self.config.enable_performance_optimization:
                perf_config = PerformanceConfig(
                    enable_caching=self.config.enable_caching,
                    enable_parallel=self.config.enable_parallel_processing,
                    cache_backend=self.config.cache_backend,
                    max_workers=self.config.max_workers
                )
                self.performance_optimizer = create_optimizer(perf_config)
                logger.info("Performance optimizer initialized")
        
        except Exception as e:
            logger.warning(f"Error initializing Phase 2 components: {e}")
    
    def _create_advanced_config(self) -> Optional[Any]:
        """Create advanced CodebaseConfig with Phase 2 enhancements."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
        
        try:
            if PHASE2_MODULES_AVAILABLE:
                # Use Phase 2 advanced configuration
                advanced_config = create_optimized_config(
                    language=self.config.codebase_language,
                    codebase_size=self.config.codebase_size,
                    optimization_level=self.config.optimization_level
                )
                
                # Apply specific flags from config
                advanced_config.exp_lazy_graph = self.config.enable_lazy_graph
                advanced_config.method_usages = self.config.enable_method_usages
                advanced_config.generics = self.config.enable_generics
                
                return advanced_config.to_codebase_config()
            else:
                # Fallback to basic configuration
                return self._create_basic_config()
        
        except Exception as e:
            logger.warning(f"Could not create advanced config: {e}")
            return None
    
    def _create_basic_config(self) -> Optional[Any]:
        """Create basic CodebaseConfig for fallback."""
        try:
            return CodebaseConfig(
                exp_lazy_graph=self.config.enable_lazy_graph,
                method_usages=self.config.enable_method_usages,
                generics=self.config.enable_generics,
                ignore_process_errors=True
            )
        except Exception as e:
            logger.warning(f"Could not create basic config: {e}")
            return None
    
    def analyze(self, path: Union[str, Path], config: Optional[AnalysisConfig] = None) -> AnalysisResult:
        """
        Perform comprehensive analysis of the codebase with enhanced features.
        
        Args:
            path: Path to the codebase to analyze
            config: Analysis configuration options
            
        Returns:
            AnalysisResult containing all analysis data including enhanced features
        """
        start_time = time.time()
        
        if config is None:
            config = AnalysisConfig()
        
        logger.info(f"🚀 Starting enhanced comprehensive analysis of: {path}")
        
        # Initialize performance optimizer if available
        if self.performance_optimizer:
            self.performance_optimizer.start_operation("comprehensive_analysis")
        
        # Initialize results
        result = AnalysisResult(
            path=str(path),
            total_files=0,
            total_functions=0,
            total_classes=0,
            total_lines=0,
            analysis_time=0.0,
            import_loops=[],
            dead_code=[],
            training_data=[],
            graph_analysis=None,
            enhanced_function_metrics=[],
            enhanced_class_metrics=[],
            summary={},
            recommendations=[],
            query_results=[],
            pattern_matches={},
            performance_metrics={},
            cache_statistics={}
        )
        
        try:
            # Load codebase with graph-sitter if available
            if GRAPH_SITTER_AVAILABLE:
                logger.info("📊 Loading codebase with graph-sitter...")
                codebase = Codebase(str(path))
                
                # Basic metrics
                result.total_files = len(codebase.files)
                result.total_functions = len(codebase.functions)
                result.total_classes = len(codebase.classes)
                
                # Calculate total lines
                total_lines = 0
                for file in codebase.files:
                    if hasattr(file, 'source'):
                        total_lines += len(file.source.split('\n'))
                result.total_lines = total_lines
                
                # Phase 1 analysis features
                if config.detect_import_loops:
                    logger.info("🔍 Detecting import loops...")
                    result.import_loops = self._detect_import_loops_advanced(codebase)
                
                if config.detect_dead_code:
                    logger.info("🗑️ Detecting dead code...")
                    result.dead_code = self._detect_dead_code(codebase)
                
                if config.generate_training_data:
                    logger.info("🤖 Generating training data...")
                    result.training_data = self._generate_training_data(codebase)
                
                if config.analyze_graph_structure:
                    logger.info("📈 Analyzing graph structure...")
                    result.graph_analysis = self._analyze_graph_structure_advanced(codebase)
                
                # Enhanced function and class metrics
                if config.enhanced_metrics:
                    logger.info("📊 Generating enhanced metrics...")
                    
                    # Enhanced function metrics
                    for function in codebase.functions[:config.max_functions]:  # Limit for performance
                        enhanced_metrics = self._analyze_function_enhanced(function)
                        result.enhanced_function_metrics.append(enhanced_metrics)
                    
                    # Enhanced class metrics
                    for cls in codebase.classes[:config.max_classes]:  # Limit for performance
                        enhanced_metrics = self._analyze_class_enhanced(cls)
                        result.enhanced_class_metrics.append(enhanced_metrics)
                
                # Phase 2 analysis features
                if PHASE2_MODULES_AVAILABLE:
                    # Tree-sitter query patterns
                    if config.enable_query_patterns and self.query_engine:
                        logger.info("🌳 Executing tree-sitter query patterns...")
                        result.query_results = self._execute_query_patterns(codebase, config)
                        result.pattern_matches = self._summarize_pattern_matches(result.query_results)
                
                # Generate summary
                result.summary = self._generate_enhanced_summary(result)
                
                # Generate recommendations
                result.recommendations = self._generate_enhanced_recommendations(result)
                
                # Phase 2 post-processing
                if PHASE2_MODULES_AVAILABLE:
                    # Generate interactive HTML report
                    if config.generate_html_report and self.report_generator:
                        logger.info("📊 Generating interactive HTML report...")
                        result.html_report_path = self._generate_html_report(result, config)
                    
                    # Collect performance metrics
                    if self.performance_optimizer:
                        result.performance_metrics = self.performance_optimizer.get_performance_report()
                        result.cache_statistics = self.performance_optimizer.cache.stats()
            
            else:
                logger.warning("Graph-sitter not available, performing basic analysis...")
                result = self._basic_analysis(path)
                
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            result.summary = {"error": str(e)}
        
        finally:
            # Finish performance optimization
            if self.performance_optimizer:
                self.performance_optimizer.finish_operation()
        
        # Calculate analysis time
        result.analysis_time = time.time() - start_time
        
        logger.info(f"✅ Analysis completed in {result.analysis_time:.2f} seconds")
        logger.info(f"📊 Found {result.total_functions} functions, {result.total_classes} classes in {result.total_files} files")
        
        if result.import_loops:
            logger.info(f"⚠️ Found {len(result.import_loops)} import loops")
        
        if result.dead_code:
            logger.info(f"🗑️ Found {len(result.dead_code)} potential dead code items")
        
        if result.query_results:
            total_matches = sum(result.pattern_matches.values())
            logger.info(f"🌳 Found {total_matches} pattern matches across {len(result.query_results)} patterns")
        
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
                        line_number=function.start_point[0] if hasattr(function, 'start_point') else 0,
                        reason='No usages found',
                        confidence=0.8,
                        suggestions=[]
                    )
                    dead_code.append(dead_item)
            
            # Check for unused classes
            for cls in codebase.classes:
                if hasattr(cls, 'usages') and len(cls.usages) == 0:
                    dead_item = DeadCodeItem(
                        type='class',
                        name=cls.name,
                        file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
                        line_number=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                        reason='No usages found',
                        confidence=0.7,
                        suggestions=[]
                    )
                    dead_code.append(dead_item)
                    
        except Exception as e:
            logger.warning(f"Error detecting dead code: {e}")
        
        return dead_code
    
    def _analyze_graph_structure(self, codebase) -> GraphAnalysisResult:
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
        
        return GraphAnalysisResult(**metrics)
    
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
                        function_name=function.name,
                        file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
                        source_code=function.source if hasattr(function, 'source') else '',
                        dependencies=dependencies,
                        usages=usages,
                        context={
                            'is_method': hasattr(function, 'is_method') and function.is_method,
                            'is_async': hasattr(function, 'is_async') and function.is_async,
                            'parameter_count': len(function.parameters) if hasattr(function, 'parameters') else 0
                        },
                        metadata={
                            'test_coverage': function.test_coverage if hasattr(function, 'test_coverage') else 0.0,
                            'maintainability_index': function.maintainability_index if hasattr(function, 'maintainability_index') else 0.0
                        }
                    )
                    training_data.append(training_item)
                    
                except Exception as e:
                    logger.debug(f"Error processing function {function.name}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error generating training data: {e}")
        
        return training_data
    
    def _detect_import_loops_advanced(self, codebase) -> List[ImportLoop]:
        """Advanced import loop detection using graph analysis."""
        import_loops = []
        
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available for advanced import loop detection")
            return import_loops
        
        if not DEPENDENCIES_AVAILABLE:
            logger.warning("Advanced dependencies not available for import loop detection")
            return import_loops
        
        try:
            # Build import graph
            import_graph = nx.DiGraph()
            file_imports = defaultdict(list)
            
            # Collect all imports
            for file in codebase.files:
                if hasattr(file, 'imports'):
                    for imp in file.imports:
                        if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol:
                            resolved = self._hop_through_imports(imp)
                            if hasattr(resolved, 'file') and resolved.file:
                                target_file = str(resolved.file.filepath)
                                source_file = str(file.filepath)
                                
                                if target_file != source_file:
                                    import_graph.add_edge(source_file, target_file)
                                    file_imports[source_file].append({
                                        'target': target_file,
                                        'symbol': imp.imported_symbol[0].name if imp.imported_symbol else 'unknown',
                                        'type': 'static'
                                    })
            
            # Find cycles in the import graph
            try:
                cycles = list(nx.simple_cycles(import_graph))
                for cycle in cycles:
                    if len(cycle) > 1:
                        # Determine loop severity
                        severity = 'critical' if len(cycle) <= 3 else 'warning'
                        loop_type = 'static'  # Could be enhanced to detect dynamic imports
                        
                        # Collect import details for this cycle
                        cycle_imports = []
                        for i, file in enumerate(cycle):
                            next_file = cycle[(i + 1) % len(cycle)]
                            for imp in file_imports.get(file, []):
                                if imp['target'] == next_file:
                                    cycle_imports.append(imp)
                        
                        import_loop = ImportLoop(
                            files=cycle,
                            loop_type=loop_type,
                            severity=severity,
                            imports=cycle_imports
                        )
                        import_loops.append(import_loop)
                        
            except Exception as e:
                logger.warning(f"Error detecting cycles: {e}")
                
        except Exception as e:
            logger.warning(f"Error in advanced import loop detection: {e}")
        
        return import_loops
    
    def _hop_through_imports(self, imp: Import) -> Union[Symbol, ExternalModule]:
        """Hop through import chains to find the root symbol."""
        if not DEPENDENCIES_AVAILABLE:
            return imp
            
        try:
            current = imp.resolved_symbol
            visited = set()
            
            while current and hasattr(current, 'definition') and current.definition:
                if id(current) in visited:
                    break
                visited.add(id(current))
                
                if isinstance(current.definition, Import):
                    current = current.definition.resolved_symbol
                else:
                    break
            
            return current or imp.resolved_symbol
        except Exception:
            return imp.resolved_symbol if hasattr(imp, 'resolved_symbol') else imp
    
    def _analyze_graph_structure_advanced(self, codebase) -> GraphAnalysisResult:
        """Advanced graph structure analysis."""
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available for advanced graph analysis")
            return GraphAnalysisResult(
                total_nodes=0, total_edges=0, connected_components=0,
                average_degree=0.0, clustering_coefficient=0.0, longest_path=0,
                cycles=[], central_nodes=[], isolated_nodes=[], metrics={}
            )
        
        if not DEPENDENCIES_AVAILABLE:
            logger.warning("Advanced dependencies not available for graph analysis")
            return GraphAnalysisResult(
                total_nodes=0, total_edges=0, connected_components=0,
                average_degree=0.0, clustering_coefficient=0.0, longest_path=0,
                cycles=[], central_nodes=[], isolated_nodes=[], metrics={}
            )
        
        try:
            # Build dependency graph
            graph = nx.DiGraph()
            
            # Add nodes for all symbols
            for function in codebase.functions:
                graph.add_node(function.name, type='function', file=str(function.filepath))
            
            for cls in codebase.classes:
                graph.add_node(cls.name, type='class', file=str(cls.filepath))
            
            # Add edges for dependencies
            for function in codebase.functions:
                if hasattr(function, 'dependencies'):
                    for dep in function.dependencies:
                        if hasattr(dep, 'name'):
                            graph.add_edge(function.name, dep.name)
            
            # Calculate graph metrics
            total_nodes = graph.number_of_nodes()
            total_edges = graph.number_of_edges()
            
            # Connected components
            connected_components = nx.number_weakly_connected_components(graph)
            
            # Average degree
            degrees = [d for n, d in graph.degree()]
            average_degree = sum(degrees) / len(degrees) if degrees else 0.0
            
            # Clustering coefficient (convert to undirected for this metric)
            undirected_graph = graph.to_undirected()
            clustering_coefficient = nx.average_clustering(undirected_graph) if undirected_graph.number_of_nodes() > 0 else 0.0
            
            # Longest path (approximate using diameter of largest component)
            longest_path = 0
            if graph.number_of_nodes() > 0:
                try:
                    largest_component = max(nx.weakly_connected_components(graph), key=len)
                    subgraph = graph.subgraph(largest_component)
                    if subgraph.number_of_nodes() > 1:
                        longest_path = nx.diameter(subgraph.to_undirected())
                except:
                    longest_path = 0
            
            # Find cycles
            cycles = []
            try:
                cycles = [list(cycle) for cycle in nx.simple_cycles(graph)]
            except:
                cycles = []
            
            # Central nodes (by degree centrality)
            centrality = nx.degree_centrality(graph)
            central_nodes = sorted(centrality.keys(), key=lambda x: centrality[x], reverse=True)[:10]
            
            # Isolated nodes
            isolated_nodes = list(nx.isolates(graph))
            
            # Additional metrics
            metrics = {
                'density': nx.density(graph),
                'transitivity': nx.transitivity(undirected_graph),
                'number_of_cliques': len(list(nx.find_cliques(undirected_graph))),
                'average_shortest_path_length': 0.0  # Computed separately if needed
            }
            
            return GraphAnalysisResult(
                total_nodes=total_nodes,
                total_edges=total_edges,
                connected_components=connected_components,
                average_degree=average_degree,
                clustering_coefficient=clustering_coefficient,
                longest_path=longest_path,
                cycles=cycles,
                central_nodes=central_nodes,
                isolated_nodes=isolated_nodes,
                metrics=metrics
            )
            
        except Exception as e:
            logger.warning(f"Error in advanced graph structure analysis: {e}")
            return GraphAnalysisResult(
                total_nodes=0, total_edges=0, connected_components=0,
                average_degree=0.0, clustering_coefficient=0.0, longest_path=0,
                cycles=[], central_nodes=[], isolated_nodes=[], metrics={}
            )
    
    def _analyze_function_enhanced(self, function) -> EnhancedFunctionMetrics:
        """Generate enhanced metrics for a function."""
        try:
            # Basic metrics
            line_count = len(function.source.split('\n')) if hasattr(function, 'source') else 0
            complexity = getattr(function, 'complexity', 1)
            parameter_count = len(function.parameters) if hasattr(function, 'parameters') else 0
            
            # Dependencies and dependents
            dependencies = []
            dependents = []
            
            if hasattr(function, 'dependencies'):
                dependencies = [dep.name for dep in function.dependencies if hasattr(dep, 'name')]
            
            if hasattr(function, 'usages'):
                dependents = [usage.name for usage in function.usages if hasattr(usage, 'name')]
            
            # Call count
            call_count = len(dependents)
            
            # Docstring quality (simple heuristic)
            docstring_quality = 0.0
            if hasattr(function, 'docstring') and function.docstring:
                docstring_length = len(function.docstring)
                if docstring_length > 100:
                    docstring_quality = 1.0
                elif docstring_length > 50:
                    docstring_quality = 0.7
                elif docstring_length > 20:
                    docstring_quality = 0.4
                else:
                    docstring_quality = 0.2
            
            # Placeholder values for metrics that would require more complex analysis
            return_complexity = min(complexity, 5)  # Simplified
            test_coverage = 0.0  # Would need test analysis
            maintainability_index = max(0.0, 100 - complexity * 5)  # Simplified formula
            
            # Halstead metrics (simplified)
            halstead_metrics = {
                'vocabulary': parameter_count + len(dependencies),
                'length': line_count,
                'difficulty': complexity,
                'effort': complexity * line_count
            }
            
            # Graph metrics
            graph_metrics = {
                'in_degree': len(dependencies),
                'out_degree': len(dependents),
                'betweenness_centrality': 0.0,  # Would need graph analysis
                'closeness_centrality': 0.0     # Would need graph analysis
            }
            
            return EnhancedFunctionMetrics(
                name=function.name,
                file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
                line_count=line_count,
                complexity=complexity,
                dependencies=dependencies,
                dependents=dependents,
                call_count=call_count,
                parameter_count=parameter_count,
                return_complexity=return_complexity,
                docstring_quality=docstring_quality,
                test_coverage=test_coverage,
                maintainability_index=maintainability_index,
                halstead_metrics=halstead_metrics,
                graph_metrics=graph_metrics
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing function {function.name}: {e}")
            return EnhancedFunctionMetrics(
                name=function.name,
                file_path='',
                line_count=0,
                complexity=1,
                dependencies=[],
                dependents=[],
                call_count=0,
                parameter_count=0,
                return_complexity=0,
                docstring_quality=0.0,
                test_coverage=0.0,
                maintainability_index=0.0,
                halstead_metrics={},
                graph_metrics={}
            )
    
    def _analyze_class_enhanced(self, cls) -> EnhancedClassMetrics:
        """Generate enhanced metrics for a class."""
        try:
            # Basic metrics
            method_count = len(cls.methods) if hasattr(cls, 'methods') else 0
            attribute_count = len(cls.attributes) if hasattr(cls, 'attributes') else 0
            
            # Inheritance depth
            inheritance_depth = 0
            if hasattr(cls, 'superclasses'):
                inheritance_depth = len(cls.superclasses)
            
            # Dependencies and dependents
            dependencies = []
            dependents = []
            
            if hasattr(cls, 'dependencies'):
                dependencies = [dep.name for dep in cls.dependencies if hasattr(dep, 'name')]
            
            if hasattr(cls, 'usages'):
                dependents = [usage.name for usage in cls.usages if hasattr(usage, 'name')]
            
            # Coupling (simplified as dependency count)
            coupling = len(dependencies)
            
            # Cohesion (simplified heuristic)
            cohesion = 1.0 if method_count > 0 else 0.0
            if method_count > 0 and attribute_count > 0:
                # Simple heuristic: methods that use attributes
                cohesion = min(1.0, attribute_count / method_count)
            
            # Complexity (sum of method complexities)
            complexity = method_count  # Simplified
            
            # Placeholder values
            test_coverage = 0.0
            maintainability_index = max(0.0, 100 - complexity * 2)
            
            # Design patterns (simple detection)
            design_patterns = []
            if hasattr(cls, 'methods'):
                method_names = [m.name for m in cls.methods if hasattr(m, 'name')]
                if 'getInstance' in method_names or '_instance' in [a.name for a in cls.attributes if hasattr(a, 'name')]:
                    design_patterns.append('Singleton')
                if any(name.startswith('create') for name in method_names):
                    design_patterns.append('Factory')
                if 'update' in method_names and 'notify' in method_names:
                    design_patterns.append('Observer')
            
            # Graph metrics
            graph_metrics = {
                'in_degree': len(dependencies),
                'out_degree': len(dependents),
                'betweenness_centrality': 0.0,
                'closeness_centrality': 0.0
            }
            
            return EnhancedClassMetrics(
                name=cls.name,
                file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
                method_count=method_count,
                attribute_count=attribute_count,
                inheritance_depth=inheritance_depth,
                coupling=coupling,
                cohesion=cohesion,
                complexity=complexity,
                dependencies=dependencies,
                dependents=dependents,
                test_coverage=test_coverage,
                maintainability_index=maintainability_index,
                design_patterns=design_patterns,
                graph_metrics=graph_metrics
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing class {cls.name}: {e}")
            return EnhancedClassMetrics(
                name=cls.name,
                file_path='',
                method_count=0,
                attribute_count=0,
                inheritance_depth=0,
                coupling=0,
                cohesion=0.0,
                complexity=0,
                dependencies=[],
                dependents=[],
                test_coverage=0.0,
                maintainability_index=0.0,
                design_patterns=[],
                graph_metrics={}
            )
    
    def _generate_enhanced_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Generate enhanced summary with advanced metrics."""
        summary = {
            "overview": {
                "total_files": result.total_files,
                "total_functions": result.total_functions,
                "total_classes": result.total_classes,
                "total_lines": result.total_lines,
                "analysis_time": result.analysis_time
            },
            "quality_metrics": {},
            "graph_metrics": {},
            "issues": {
                "import_loops": len(result.import_loops),
                "dead_code_items": len(result.dead_code),
                "critical_issues": 0,
                "warnings": 0
            },
            "enhanced_insights": {}
        }
        
        # Quality metrics from enhanced function analysis
        if result.enhanced_function_metrics:
            complexities = [f.complexity for f in result.enhanced_function_metrics]
            maintainability_scores = [f.maintainability_index for f in result.enhanced_function_metrics]
            docstring_qualities = [f.docstring_quality for f in result.enhanced_function_metrics]
            
            summary["quality_metrics"] = {
                "average_complexity": sum(complexities) / len(complexities) if complexities else 0,
                "average_maintainability": sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0,
                "average_docstring_quality": sum(docstring_qualities) / len(docstring_qualities) if docstring_qualities else 0,
                "high_complexity_functions": len([c for c in complexities if c > 10]),
                "low_maintainability_functions": len([m for m in maintainability_scores if m < 50])
            }
        
        # Graph metrics
        if result.graph_analysis:
            summary["graph_metrics"] = {
                "total_nodes": result.graph_analysis.total_nodes,
                "total_edges": result.graph_analysis.total_edges,
                "connected_components": result.graph_analysis.connected_components,
                "average_degree": result.graph_analysis.average_degree,
                "clustering_coefficient": result.graph_analysis.clustering_coefficient,
                "cycles_found": len(result.graph_analysis.cycles),
                "isolated_nodes": len(result.graph_analysis.isolated_nodes)
            }
        
        # Count critical issues
        critical_issues = 0
        warnings = 0
        
        for loop in result.import_loops:
            if loop.severity == 'critical':
                critical_issues += 1
            else:
                warnings += 1
        
        for dead_code in result.dead_code:
            if dead_code.confidence > 0.8:
                critical_issues += 1
            else:
                warnings += 1
        
        summary["issues"]["critical_issues"] = critical_issues
        summary["issues"]["warnings"] = warnings
        
        # Enhanced insights
        if result.enhanced_class_metrics:
            design_patterns = []
            for cls in result.enhanced_class_metrics:
                design_patterns.extend(cls.design_patterns)
            
            pattern_counts = {}
            for pattern in design_patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            summary["enhanced_insights"] = {
                "design_patterns_detected": pattern_counts,
                "average_class_coupling": sum(c.coupling for c in result.enhanced_class_metrics) / len(result.enhanced_class_metrics) if result.enhanced_class_metrics else 0,
                "average_class_cohesion": sum(c.cohesion for c in result.enhanced_class_metrics) / len(result.enhanced_class_metrics) if result.enhanced_class_metrics else 0
            }
        
        return summary
    
    def _generate_enhanced_recommendations(self, result: AnalysisResult) -> List[str]:
        """Generate enhanced recommendations based on analysis results."""
        recommendations = []
        
        # Import loop recommendations
        if result.import_loops:
            critical_loops = [loop for loop in result.import_loops if loop.severity == 'critical']
            if critical_loops:
                recommendations.append(f"🚨 CRITICAL: Fix {len(critical_loops)} critical import loops that can cause runtime errors")
            
            warning_loops = [loop for loop in result.import_loops if loop.severity == 'warning']
            if warning_loops:
                recommendations.append(f"⚠️ Consider refactoring {len(warning_loops)} import loops to improve code organization")
        
        # Dead code recommendations
        if result.dead_code:
            high_confidence = [item for item in result.dead_code if item.confidence > 0.8]
            if high_confidence:
                recommendations.append(f"🗑�� Remove {len(high_confidence)} high-confidence dead code items to reduce codebase size")
            
            medium_confidence = [item for item in result.dead_code if 0.5 < item.confidence <= 0.8]
            if medium_confidence:
                recommendations.append(f"🔍 Review {len(medium_confidence)} potential dead code items for removal")
        
        # Quality recommendations
        if result.enhanced_function_metrics:
            high_complexity = [f for f in result.enhanced_function_metrics if f.complexity > 10]
            if high_complexity:
                recommendations.append(f"🔧 Refactor {len(high_complexity)} high-complexity functions to improve maintainability")
            
            poor_documentation = [f for f in result.enhanced_function_metrics if f.docstring_quality < 0.3]
            if poor_documentation:
                recommendations.append(f"📝 Add documentation to {len(poor_documentation)} poorly documented functions")
            
            low_maintainability = [f for f in result.enhanced_function_metrics if f.maintainability_index < 50]
            if low_maintainability:
                recommendations.append(f"⚡ Improve maintainability of {len(low_maintainability)} functions with low maintainability scores")
        
        # Graph structure recommendations
        if result.graph_analysis:
            if result.graph_analysis.isolated_nodes:
                recommendations.append(f"🔗 Consider connecting {len(result.graph_analysis.isolated_nodes)} isolated components to improve code cohesion")
            
            if result.graph_analysis.cycles:
                recommendations.append(f"🔄 Review {len(result.graph_analysis.cycles)} dependency cycles for potential architectural improvements")
        
        # Class design recommendations
        if result.enhanced_class_metrics:
            high_coupling = [c for c in result.enhanced_class_metrics if c.coupling > 10]
            if high_coupling:
                recommendations.append(f"🔗 Reduce coupling in {len(high_coupling)} highly coupled classes")
            
            low_cohesion = [c for c in result.enhanced_class_metrics if c.cohesion < 0.3]
            if low_cohesion:
                recommendations.append(f"🎯 Improve cohesion in {len(low_cohesion)} classes with low cohesion")
        
        # Training data recommendations
        if result.training_data:
            recommendations.append(f"🤖 Generated {len(result.training_data)} training data items for ML model development")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Codebase appears to be in good shape! Consider running with more detailed analysis options.")
        
        return recommendations

    def _basic_analysis(self, path: Union[str, Path]) -> AnalysisResult:
        """Perform basic analysis of the codebase."""
        result = AnalysisResult(
            path=str(path),
            total_files=0,
            total_functions=0,
            total_classes=0,
            total_lines=0,
            analysis_time=0.0,
            import_loops=[],
            dead_code=[],
            training_data=[],
            graph_analysis=None,
            enhanced_function_metrics=[],
            enhanced_class_metrics=[],
            summary={},
            recommendations=[]
        )
        
        try:
            # Load codebase without graph-sitter
            codebase = Codebase(str(path))
            
            # Basic metrics
            result.total_files = len(codebase.files)
            result.total_functions = len(codebase.functions)
            result.total_classes = len(codebase.classes)
            
            # Calculate total lines
            total_lines = 0
            for file in codebase.files:
                if hasattr(file, 'source'):
                    total_lines += len(file.source.split('\n'))
            result.total_lines = total_lines
            
            # Enhanced analysis features
            if self.config.detect_import_loops:
                result.import_loops = self._detect_import_loops(codebase)
            
            if self.config.detect_dead_code:
                result.dead_code = self._detect_dead_code(codebase)
            
            if self.config.generate_training_data:
                result.training_data = self._generate_training_data(codebase)
            
            if self.config.analyze_graph_structure:
                result.graph_analysis = self._analyze_graph_structure(codebase)
            
            # Enhanced function and class metrics
            if self.config.enhanced_metrics:
                for function in codebase.functions[:self.config.max_functions]:  # Limit for performance
                    enhanced_metrics = self._analyze_function_enhanced(function)
                    result.enhanced_function_metrics.append(enhanced_metrics)
                
                for cls in codebase.classes[:self.config.max_classes]:  # Limit for performance
                    enhanced_metrics = self._analyze_class_enhanced(cls)
                    result.enhanced_class_metrics.append(enhanced_metrics)
            
            # Generate summary
            result.summary = self._generate_enhanced_summary(result)
            
            # Generate recommendations
            result.recommendations = self._generate_enhanced_recommendations(result)
        
        except Exception as e:
            logger.error(f"Error during basic analysis: {e}")
            result.summary = {"error": str(e)}
        
        return result
    
    def _execute_query_patterns(self, codebase, config: AnalysisConfig) -> List[Any]:
        """Execute tree-sitter query patterns on the codebase."""
        if not self.query_engine:
            return []
        
        try:
            query_results = []
            
            # Execute patterns by category
            for category in config.query_categories:
                category_results = self.query_engine.execute_patterns_by_category(category, codebase)
                query_results.extend(category_results)
            
            # Execute custom patterns
            if config.custom_query_patterns:
                custom_results = self.query_engine.execute_patterns(config.custom_query_patterns, codebase)
                query_results.extend(custom_results)
            
            logger.info(f"Executed {len(query_results)} query patterns")
            return query_results
        
        except Exception as e:
            logger.warning(f"Error executing query patterns: {e}")
            return []
    
    def _summarize_pattern_matches(self, query_results: List[Any]) -> Dict[str, int]:
        """Summarize pattern matches by category."""
        pattern_matches = {}
        
        try:
            for result in query_results:
                if hasattr(result, 'pattern') and hasattr(result, 'total_matches'):
                    category = result.pattern.category
                    pattern_matches[category] = pattern_matches.get(category, 0) + result.total_matches
        
        except Exception as e:
            logger.warning(f"Error summarizing pattern matches: {e}")
        
        return pattern_matches
    
    def _generate_html_report(self, result: AnalysisResult, config: AnalysisConfig) -> Optional[str]:
        """Generate interactive HTML report."""
        if not self.report_generator:
            return None
        
        try:
            # Determine output path
            if config.html_report_path:
                output_path = config.html_report_path
            else:
                output_path = f"analysis_report_{int(time.time())}.html"
            
            # Generate and save report
            self.report_generator.save_report(result, output_path)
            logger.info(f"HTML report saved to: {output_path}")
            return output_path
        
        except Exception as e:
            logger.warning(f"Error generating HTML report: {e}")
            return None


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


class AnalysisPresets:
    """Predefined analysis configurations for common use cases."""
    
    @staticmethod
    def comprehensive() -> AnalysisConfig:
        """Comprehensive analysis with all features enabled."""
        return AnalysisConfig(
            detect_import_loops=True,
            detect_dead_code=True,
            generate_training_data=True,
            analyze_graph_structure=True,
            enhanced_metrics=True,
            ignore_external_modules=True,
            ignore_test_files=False,
            file_extensions=None,
            max_functions=200,
            max_classes=100
        )
    
    @staticmethod
    def quality_focused() -> AnalysisConfig:
        """Quality-focused analysis for code review and improvement."""
        return AnalysisConfig(
            detect_import_loops=True,
            detect_dead_code=True,
            generate_training_data=False,
            analyze_graph_structure=True,
            enhanced_metrics=True,
            ignore_external_modules=True,
            ignore_test_files=True,
            file_extensions=None,
            max_functions=150,
            max_classes=75
        )
    
    @staticmethod
    def performance() -> AnalysisConfig:
        """Performance-optimized analysis for quick feedback."""
        return AnalysisConfig(
            detect_import_loops=True,
            detect_dead_code=False,
            generate_training_data=False,
            analyze_graph_structure=False,
            enhanced_metrics=True,
            ignore_external_modules=True,
            ignore_test_files=True,
            file_extensions=None,
            max_functions=50,
            max_classes=25
        )
    
    @staticmethod
    def minimal() -> AnalysisConfig:
        """Minimal analysis for basic metrics only."""
        return AnalysisConfig(
            detect_import_loops=False,
            detect_dead_code=False,
            generate_training_data=False,
            analyze_graph_structure=False,
            enhanced_metrics=False,
            ignore_external_modules=True,
            ignore_test_files=True,
            file_extensions=None,
            max_functions=25,
            max_classes=10
        )
    
    @staticmethod
    def training_data() -> AnalysisConfig:
        """Optimized for generating ML training data."""
        return AnalysisConfig(
            detect_import_loops=False,
            detect_dead_code=False,
            generate_training_data=True,
            analyze_graph_structure=True,
            enhanced_metrics=True,
            ignore_external_modules=True,
            ignore_test_files=True,
            file_extensions=None,
            max_functions=500,
            max_classes=200
        )


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
