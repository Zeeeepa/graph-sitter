#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS ENGINE - CONSOLIDATED FROM ALL PRs AND CODE FILES 🚀

This is the unified core analysis engine that consolidates the best features from:
- All PRs (#211, #212, #213, #214, #215)
- graph_sitter_enhancements.py
- legacy_analyze_codebase.py
- legacy_analyze_codebase_enhanced.py  
- legacy_enhanced_analyzer.py

Features:
- Advanced graph-sitter integration with pre-computed elements
- Tree-sitter query patterns and visualization
- Comprehensive quality metrics and complexity analysis
- Import loop detection and dead code analysis
- AI-powered insights and training data generation
- Interactive syntax tree visualization
- Advanced configuration with CodebaseConfig
- Performance optimizations and error handling
"""

import logging
import time
import json
import html
import tempfile
import webbrowser
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import networkx as nx

logger = logging.getLogger(__name__)

# Import analysis modules
try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    Codebase = None
    CodebaseConfig = None

# Import enhanced analysis functions
try:
    from ..metrics.quality import QualityAnalyzer
    from ..metrics.complexity import ComplexityAnalyzer
    from ..detection.patterns import PatternDetector
    from ..detection.dead_code import DeadCodeDetector
    from ..detection.import_loops import ImportLoopDetector
    from ..visualization.tree_sitter import TreeSitterVisualizer
    from ..ai.insights import AIInsightGenerator
    from ..ai.training_data import TrainingDataGenerator
    from ..integration.graph_sitter_config import GraphSitterConfigManager
    from .config import AnalysisConfig, AnalysisResult
    ANALYSIS_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Analysis modules not fully available: {e}")
    ANALYSIS_MODULES_AVAILABLE = False

# Enhanced data structures from all sources
@dataclass
class ImportLoop:
    """Represents a circular import dependency."""
    files: List[str]
    loop_type: str  # 'static', 'dynamic', 'mixed'
    severity: str   # 'critical', 'warning', 'info'
    imports: List[Dict[str, Any]]

@dataclass
class DeadCodeItem:
    """Represents a dead code item."""
    name: str
    type: str  # 'function', 'class', 'variable', 'import'
    file_path: str
    line_number: int
    reason: str
    confidence: float

@dataclass
class TrainingDataItem:
    """Training data item for ML models."""
    function_name: str
    function_code: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    quality_metrics: Dict[str, float]

@dataclass
class GraphAnalysisResult:
    """Result of graph structure analysis."""
    total_nodes: int
    total_edges: int
    connected_components: int
    average_degree: float
    clustering_coefficient: float
    graph_density: float
    centrality_metrics: Dict[str, Any]

@dataclass
class EnhancedFunctionMetrics:
    """Enhanced function metrics from all sources."""
    name: str
    complexity: Dict[str, float]
    quality: Dict[str, float]
    dependencies: List[str]
    usages: List[str]
    patterns: List[str]
    ai_insights: Optional[Dict[str, Any]] = None

@dataclass
class EnhancedClassMetrics:
    """Enhanced class metrics from all sources."""
    name: str
    methods: List[EnhancedFunctionMetrics]
    complexity: Dict[str, float]
    quality: Dict[str, float]
    inheritance: Dict[str, Any]
    patterns: List[str]
    ai_insights: Optional[Dict[str, Any]] = None

class AnalysisEngine:
    """
    Comprehensive Analysis Engine - Consolidated from all PRs and code files
    
    This engine provides unified access to all analysis capabilities:
    - Quality metrics and complexity analysis
    - Pattern detection and code smells
    - Import loop detection and dead code analysis
    - Tree-sitter visualization and query patterns
    - AI-powered insights and training data generation
    - Graph-sitter integration with advanced settings
    """
    
    def __init__(self, config: AnalysisConfig):
        """Initialize the analysis engine with configuration."""
        self.config = config
        self.modules = {}
        self.codebase = None
        self.results = None
        
        # Initialize analysis modules based on configuration
        self._initialize_modules()
        
        # Initialize graph-sitter configuration if available
        if GRAPH_SITTER_AVAILABLE and self.config.enable_graph_sitter:
            self._initialize_graph_sitter_config()
    
    def _initialize_modules(self):
        """Initialize analysis modules based on configuration."""
        
        try:
            if self.config.enable_metrics:
                self.modules['quality'] = QualityAnalyzer(self.config)
                self.modules['complexity'] = ComplexityAnalyzer(self.config)
            
            if self.config.enable_visualization:
                self.modules['tree_sitter'] = TreeSitterVisualizer(self.config)
            
            if self.config.enable_pattern_detection:
                self.modules['patterns'] = PatternDetector(self.config)
                self.modules['import_loops'] = ImportLoopDetector(self.config)
                self.modules['dead_code'] = DeadCodeDetector(self.config)
            
            if self.config.enable_ai_insights:
                self.modules['ai_insights'] = AIInsightGenerator(self.config)
                self.modules['training_data'] = TrainingDataGenerator(self.config)
            
            # Graph-sitter configuration manager
            if GRAPH_SITTER_AVAILABLE:
                self.modules['graph_sitter_config'] = GraphSitterConfigManager(self.config)
                
        except Exception as e:
            logger.warning(f"Failed to initialize some modules: {e}")
    
    def _initialize_graph_sitter_config(self):
        """Initialize advanced graph-sitter configuration."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
        
        try:
            # Create advanced CodebaseConfig with enhanced features
            config_options = {
                'debug': self.config.debug,
                'method_usages': True,
                'generics': True,
                'full_range_index': True,
                'exp_lazy_graph': self.config.lazy_loading,
                'ts_language_engine': True,
            }
            
            # Add additional advanced settings from graph-sitter.com
            if hasattr(self.config, 'advanced_graph_sitter_settings'):
                config_options.update(self.config.advanced_graph_sitter_settings)
            
            return CodebaseConfig(**config_options)
        except Exception as e:
            logger.warning(f"Failed to create advanced CodebaseConfig: {e}")
            return None

    def analyze_codebase(self, path: Union[str, Path]) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        This method consolidates all analysis capabilities from all PRs and code files:
        - Basic metrics and quality analysis
        - Advanced graph-sitter integration
        - Tree-sitter query patterns and visualization
        - Import loop detection and dead code analysis
        - AI-powered insights and training data generation
        """
        start_time = time.time()
        path = Path(path)
        
        logger.info(f"Starting comprehensive analysis of: {path}")
        
        try:
            # Initialize codebase with advanced configuration
            if GRAPH_SITTER_AVAILABLE and self.config.enable_graph_sitter:
                graph_config = self._initialize_graph_sitter_config()
                self.codebase = Codebase(str(path), config=graph_config)
            else:
                # Fallback to basic file system analysis
                self.codebase = self._create_basic_codebase(path)
            
            # Initialize result object
            self.results = AnalysisResult(
                path=str(path),
                timestamp=time.time(),
                config=self.config
            )
            
            # Perform analysis based on enabled modules
            if self.config.enable_metrics:
                self._analyze_metrics()
            
            if self.config.enable_pattern_detection:
                self._analyze_patterns()
            
            if self.config.enable_visualization:
                self._generate_visualizations()
            
            if self.config.enable_ai_insights:
                self._generate_ai_insights()
            
            # Calculate analysis duration
            self.results.analysis_duration = time.time() - start_time
            
            logger.info(f"Analysis completed in {self.results.analysis_duration:.2f} seconds")
            return self.results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            if self.config.debug:
                import traceback
                traceback.print_exc()
            raise

    def _create_basic_codebase(self, path: Path) -> Dict[str, Any]:
        """Create basic codebase representation when graph-sitter is not available."""
        codebase = {
            'path': str(path),
            'files': [],
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        # Basic file discovery
        for file_path in path.rglob('*.py'):
            if file_path.is_file():
                codebase['files'].append(str(file_path))
        
        return codebase

    def _analyze_metrics(self):
        """Analyze quality and complexity metrics."""
        logger.info("Analyzing quality and complexity metrics...")
        
        try:
            if 'quality' in self.modules:
                quality_results = self.modules['quality'].analyze(self.codebase)
                self.results.quality_metrics = quality_results
            
            if 'complexity' in self.modules:
                complexity_results = self.modules['complexity'].analyze(self.codebase)
                self.results.complexity_metrics = complexity_results
                
        except Exception as e:
            logger.warning(f"Metrics analysis failed: {e}")

    def _analyze_patterns(self):
        """Analyze code patterns, import loops, and dead code."""
        logger.info("Analyzing patterns and detecting issues...")
        
        try:
            if 'patterns' in self.modules:
                pattern_results = self.modules['patterns'].analyze(self.codebase)
                self.results.patterns = pattern_results
            
            if 'import_loops' in self.modules:
                import_loop_results = self.modules['import_loops'].analyze(self.codebase)
                self.results.import_loops = import_loop_results
            
            if 'dead_code' in self.modules:
                dead_code_results = self.modules['dead_code'].analyze(self.codebase)
                self.results.dead_code = dead_code_results
                
        except Exception as e:
            logger.warning(f"Pattern analysis failed: {e}")

    def _generate_visualizations(self):
        """Generate tree-sitter visualizations and interactive reports."""
        logger.info("Generating visualizations...")
        
        try:
            if 'tree_sitter' in self.modules:
                viz_results = self.modules['tree_sitter'].generate(self.codebase)
                self.results.visualizations = viz_results
                
        except Exception as e:
            logger.warning(f"Visualization generation failed: {e}")

    def _generate_ai_insights(self):
        """Generate AI-powered insights and training data."""
        logger.info("Generating AI insights...")
        
        try:
            if 'ai_insights' in self.modules:
                ai_results = self.modules['ai_insights'].analyze(self.codebase)
                self.results.ai_insights = ai_results
            
            if 'training_data' in self.modules:
                training_results = self.modules['training_data'].generate(self.codebase)
                self.results.training_data = training_results
                
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")

    # Enhanced analysis methods from all sources
    def analyze_function_enhanced(self, function_name: str) -> Optional[EnhancedFunctionMetrics]:
        """Analyze a specific function with enhanced metrics from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return None
        
        try:
            function = self.codebase.get_function(function_name)
            if not function:
                return None
            
            # Gather comprehensive metrics
            metrics = EnhancedFunctionMetrics(
                name=function.name,
                complexity={},
                quality={},
                dependencies=[],
                usages=[],
                patterns=[]
            )
            
            # Complexity analysis
            if 'complexity' in self.modules:
                metrics.complexity = self.modules['complexity'].analyze_function(function)
            
            # Quality analysis
            if 'quality' in self.modules:
                metrics.quality = self.modules['quality'].analyze_function(function)
            
            # Dependencies and usages
            metrics.dependencies = [dep.name for dep in function.dependencies if hasattr(dep, 'name')]
            metrics.usages = [usage.file.filepath for usage in function.usages if hasattr(usage, 'file')]
            
            # Pattern analysis
            if 'patterns' in self.modules:
                metrics.patterns = self.modules['patterns'].analyze_function(function)
            
            # AI insights
            if 'ai_insights' in self.modules and self.config.enable_ai_insights:
                metrics.ai_insights = self.modules['ai_insights'].analyze_function(function)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Enhanced function analysis failed for {function_name}: {e}")
            return None

    def analyze_class_enhanced(self, class_name: str) -> Optional[EnhancedClassMetrics]:
        """Analyze a specific class with enhanced metrics from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return None
        
        try:
            class_obj = self.codebase.get_class(class_name)
            if not class_obj:
                return None
            
            # Analyze all methods
            method_metrics = []
            for method in class_obj.methods:
                method_analysis = self.analyze_function_enhanced(method.name)
                if method_analysis:
                    method_metrics.append(method_analysis)
            
            # Gather comprehensive class metrics
            metrics = EnhancedClassMetrics(
                name=class_obj.name,
                methods=method_metrics,
                complexity={},
                quality={},
                inheritance={},
                patterns=[]
            )
            
            # Class-level complexity and quality
            if 'complexity' in self.modules:
                metrics.complexity = self.modules['complexity'].analyze_class(class_obj)
            
            if 'quality' in self.modules:
                metrics.quality = self.modules['quality'].analyze_class(class_obj)
            
            # Inheritance analysis
            metrics.inheritance = {
                'superclasses': [sc.name for sc in class_obj.superclasses if hasattr(sc, 'name')],
                'subclasses': [sc.name for sc in class_obj.subclasses if hasattr(sc, 'name')],
                'depth': len(class_obj.superclasses)
            }
            
            # Pattern analysis
            if 'patterns' in self.modules:
                metrics.patterns = self.modules['patterns'].analyze_class(class_obj)
            
            # AI insights
            if 'ai_insights' in self.modules and self.config.enable_ai_insights:
                metrics.ai_insights = self.modules['ai_insights'].analyze_class(class_obj)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Enhanced class analysis failed for {class_name}: {e}")
            return None

    def detect_import_loops_enhanced(self) -> List[ImportLoop]:
        """Detect import loops with enhanced analysis from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return []
        
        try:
            if 'import_loops' in self.modules:
                return self.modules['import_loops'].detect_comprehensive(self.codebase)
            return []
        except Exception as e:
            logger.warning(f"Import loop detection failed: {e}")
            return []

    def detect_dead_code_enhanced(self) -> List[DeadCodeItem]:
        """Detect dead code with enhanced analysis from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return []
        
        try:
            if 'dead_code' in self.modules:
                return self.modules['dead_code'].detect_comprehensive(self.codebase)
            return []
        except Exception as e:
            logger.warning(f"Dead code detection failed: {e}")
            return []

    def generate_training_data_enhanced(self) -> List[TrainingDataItem]:
        """Generate training data with enhanced features from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return []
        
        try:
            if 'training_data' in self.modules:
                return self.modules['training_data'].generate_comprehensive(self.codebase)
            return []
        except Exception as e:
            logger.warning(f"Training data generation failed: {e}")
            return []

    def analyze_graph_structure(self) -> Optional[GraphAnalysisResult]:
        """Analyze graph structure with enhanced metrics from all sources."""
        if not GRAPH_SITTER_AVAILABLE or not self.codebase:
            return None
        
        try:
            # Create NetworkX graph from codebase
            G = nx.DiGraph()
            
            # Add nodes for functions and classes
            for func in self.codebase.functions:
                G.add_node(func.name, type='function')
            
            for cls in self.codebase.classes:
                G.add_node(cls.name, type='class')
            
            # Add edges for dependencies
            for func in self.codebase.functions:
                for dep in func.dependencies:
                    if hasattr(dep, 'name'):
                        G.add_edge(func.name, dep.name)
            
            # Calculate graph metrics
            result = GraphAnalysisResult(
                total_nodes=G.number_of_nodes(),
                total_edges=G.number_of_edges(),
                connected_components=nx.number_weakly_connected_components(G),
                average_degree=sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
                clustering_coefficient=nx.average_clustering(G.to_undirected()),
                graph_density=nx.density(G),
                centrality_metrics={
                    'betweenness': dict(nx.betweenness_centrality(G)),
                    'closeness': dict(nx.closeness_centrality(G)),
                    'degree': dict(nx.degree_centrality(G))
                }
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Graph structure analysis failed: {e}")
            return None

    def export_results(self, output_path: Union[str, Path], format: str = 'json'):
        """Export analysis results in various formats."""
        if not self.results:
            logger.warning("No results to export")
            return
        
        output_path = Path(output_path)
        
        try:
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(asdict(self.results), f, indent=2, default=str)
            
            elif format.lower() == 'html':
                self._export_html_report(output_path)
            
            else:
                logger.warning(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")

    def _export_html_report(self, output_path: Path):
        """Export comprehensive HTML report with visualizations."""
        # This would generate an interactive HTML report
        # Implementation would include D3.js visualizations, charts, etc.
        html_content = self._generate_html_report()
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        if self.config.open_browser:
            webbrowser.open(f'file://{output_path.absolute()}')

    def _generate_html_report(self) -> str:
        """Generate comprehensive HTML report content."""
        # This would generate a rich HTML report with all analysis results
        # Including interactive visualizations, charts, and detailed metrics
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Codebase Analysis Report</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin: 10px 0; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>🚀 Comprehensive Codebase Analysis Report</h1>
            <p>Analysis completed at: {time.ctime(self.results.timestamp)}</p>
            <p>Analysis duration: {self.results.analysis_duration:.2f} seconds</p>
            
            <!-- Quality Metrics Section -->
            <h2>📊 Quality Metrics</h2>
            <div id="quality-metrics">
                {self._format_metrics_html(self.results.quality_metrics)}
            </div>
            
            <!-- Complexity Metrics Section -->
            <h2>🔧 Complexity Metrics</h2>
            <div id="complexity-metrics">
                {self._format_metrics_html(self.results.complexity_metrics)}
            </div>
            
            <!-- Pattern Analysis Section -->
            <h2>🔍 Pattern Analysis</h2>
            <div id="patterns">
                {self._format_patterns_html(self.results.patterns)}
            </div>
            
            <!-- Visualizations Section -->
            <h2>🎨 Visualizations</h2>
            <div id="visualizations">
                {self._format_visualizations_html(self.results.visualizations)}
            </div>
            
            <script>
                // Interactive D3.js visualizations would go here
                console.log('Comprehensive Analysis Report Loaded');
            </script>
        </body>
        </html>
        """

    def _format_metrics_html(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for HTML display."""
        if not metrics:
            return "<p>No metrics available</p>"
        
        html = "<ul>"
        for key, value in metrics.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html

    def _format_patterns_html(self, patterns: List[Any]) -> str:
        """Format patterns for HTML display."""
        if not patterns:
            return "<p>No patterns detected</p>"
        
        html = "<ul>"
        for pattern in patterns:
            html += f"<li>{pattern}</li>"
        html += "</ul>"
        return html

    def _format_visualizations_html(self, visualizations: Dict[str, Any]) -> str:
        """Format visualizations for HTML display."""
        if not visualizations:
            return "<p>No visualizations available</p>"
        
        # This would embed interactive visualizations
        return "<div>Interactive visualizations would be embedded here</div>"
