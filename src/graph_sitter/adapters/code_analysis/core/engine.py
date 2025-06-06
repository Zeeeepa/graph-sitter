"""
🔧 Core Analysis Engine

Consolidated analysis engine combining the best features from all existing tools:
- analyze_codebase.py comprehensive analysis
- analyze_codebase_enhanced.py graph-sitter integration
- enhanced_analyzer.py advanced features
- graph_sitter_enhancements.py specialized functions
- PR #211-215 advanced capabilities

This engine provides unified access to all analysis functionality.
"""

import logging
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    logger.warning("Graph-sitter not available. Some functionality will be limited.")
    GRAPH_SITTER_AVAILABLE = False
    Codebase = object
    CodebaseConfig = object

from .config import AnalysisConfig, AnalysisResult


class AnalysisEngine:
    """
    Core analysis engine that orchestrates all analysis components.
    
    Combines functionality from:
    - ComprehensiveCodebaseAnalyzer (analyze_codebase.py)
    - EnhancedCodebaseAnalyzer (enhanced_analyzer.py) 
    - Graph-sitter enhancements
    - All PR features
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.start_time = None
        self.codebase = None
        self.results = AnalysisResult()
        
        # Initialize components based on config
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize analysis components based on configuration"""
        # Import components dynamically to avoid circular imports
        if self.config.enable_metrics:
            from ..metrics.quality import QualityMetrics
            from ..metrics.complexity import ComplexityAnalyzer
            self.quality_metrics = QualityMetrics()
            self.complexity_analyzer = ComplexityAnalyzer()
        
        if self.config.enable_pattern_detection:
            from ..detection.patterns import PatternDetector
            from ..detection.dead_code import DeadCodeDetector
            from ..detection.import_loops import ImportLoopDetector
            self.pattern_detector = PatternDetector()
            self.dead_code_detector = DeadCodeDetector()
            self.import_loop_detector = ImportLoopDetector()
        
        if self.config.enable_ai_analysis:
            from ..ai.insights import AIAnalyzer
            from ..ai.training_data import TrainingDataGenerator
            self.ai_analyzer = AIAnalyzer(self.config.ai_config)
            self.training_data_generator = TrainingDataGenerator()
        
        if self.config.enable_visualization:
            from ..visualization.reports import HTMLReportGenerator
            self.report_generator = HTMLReportGenerator()
        
        if self.config.enable_graph_sitter and GRAPH_SITTER_AVAILABLE:
            from ..integration.graph_sitter_config import GraphSitterConfigManager
            self.graph_sitter_config = GraphSitterConfigManager()
    
    def analyze(self, path: str) -> AnalysisResult:
        """
        Perform comprehensive analysis on the given path.
        
        Args:
            path: Path to analyze (file or directory)
            
        Returns:
            AnalysisResult containing all analysis data
        """
        self.start_time = time.time()
        path_obj = Path(path)
        
        try:
            # Initialize results
            self.results = AnalysisResult()
            self.results.path = str(path_obj.absolute())
            self.results.analysis_config = self.config
            
            # Load codebase
            if self.config.enable_graph_sitter and GRAPH_SITTER_AVAILABLE:
                self._load_graph_sitter_codebase(path)
            else:
                self._load_ast_codebase(path)
            
            # Perform analysis phases
            self._analyze_structure()
            self._analyze_quality()
            self._analyze_patterns()
            self._analyze_dependencies()
            self._analyze_with_ai()
            self._generate_visualizations()
            
            # Finalize results
            self.results.analysis_duration = time.time() - self.start_time
            self.results.success = True
            
            return self.results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.results.success = False
            self.results.error = str(e)
            self.results.analysis_duration = time.time() - self.start_time
            return self.results
    
    def _load_graph_sitter_codebase(self, path: str):
        """Load codebase using graph-sitter"""
        try:
            # Create advanced config if specified
            if self.config.use_advanced_graph_sitter_config:
                gs_config = self.graph_sitter_config.create_advanced_config()
                self.codebase = Codebase(path, config=gs_config)
            else:
                self.codebase = Codebase(path)
            
            logger.info(f"Loaded codebase with graph-sitter: {len(self.codebase.files)} files")
            
        except Exception as e:
            logger.warning(f"Graph-sitter loading failed: {e}. Falling back to AST.")
            self._load_ast_codebase(path)
    
    def _load_ast_codebase(self, path: str):
        """Load codebase using AST parsing (fallback)"""
        # Implementation for AST-based loading
        # This would use the logic from analyze_codebase.py
        logger.info("Using AST-based analysis")
        self.codebase = None  # Placeholder
    
    def _analyze_structure(self):
        """Analyze codebase structure"""
        if not self.codebase:
            return
        
        try:
            # Basic structure analysis
            self.results.file_count = len(self.codebase.files)
            self.results.function_count = len(self.codebase.functions)
            self.results.class_count = len(self.codebase.classes)
            self.results.import_count = len(self.codebase.imports)
            
            # Detailed structure analysis
            self._analyze_files()
            self._analyze_functions()
            self._analyze_classes()
            self._analyze_imports()
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
    
    def _analyze_files(self):
        """Analyze individual files"""
        file_analysis = {}
        
        for file in self.codebase.files:
            try:
                analysis = {
                    'path': file.filepath,
                    'size': len(file.source) if hasattr(file, 'source') else 0,
                    'line_count': len(file.source.splitlines()) if hasattr(file, 'source') else 0,
                    'function_count': len(file.functions) if hasattr(file, 'functions') else 0,
                    'class_count': len(file.classes) if hasattr(file, 'classes') else 0,
                    'import_count': len(file.imports) if hasattr(file, 'imports') else 0
                }
                file_analysis[file.filepath] = analysis
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file.filepath}: {e}")
        
        self.results.file_analysis = file_analysis
    
    def _analyze_functions(self):
        """Analyze functions"""
        function_analysis = {}
        
        for function in self.codebase.functions:
            try:
                analysis = {
                    'name': function.name,
                    'file': function.filepath if hasattr(function, 'filepath') else 'unknown',
                    'line_count': len(function.source.splitlines()) if hasattr(function, 'source') else 0,
                    'parameter_count': len(function.parameters) if hasattr(function, 'parameters') else 0,
                    'dependency_count': len(function.dependencies) if hasattr(function, 'dependencies') else 0,
                    'usage_count': len(function.usages) if hasattr(function, 'usages') else 0,
                    'is_recursive': self._is_recursive_function(function),
                    'is_async': hasattr(function, 'is_async') and function.is_async
                }
                function_analysis[function.name] = analysis
                
            except Exception as e:
                logger.warning(f"Failed to analyze function {function.name}: {e}")
        
        self.results.function_analysis = function_analysis
    
    def _analyze_classes(self):
        """Analyze classes"""
        class_analysis = {}
        
        for cls in self.codebase.classes:
            try:
                analysis = {
                    'name': cls.name,
                    'file': cls.filepath if hasattr(cls, 'filepath') else 'unknown',
                    'method_count': len(cls.methods) if hasattr(cls, 'methods') else 0,
                    'attribute_count': len(cls.attributes) if hasattr(cls, 'attributes') else 0,
                    'parent_classes': cls.parent_class_names if hasattr(cls, 'parent_class_names') else [],
                    'subclass_count': len(cls.subclasses) if hasattr(cls, 'subclasses') else 0,
                    'is_abstract': self._is_abstract_class(cls)
                }
                class_analysis[cls.name] = analysis
                
            except Exception as e:
                logger.warning(f"Failed to analyze class {cls.name}: {e}")
        
        self.results.class_analysis = class_analysis
    
    def _analyze_imports(self):
        """Analyze imports"""
        import_analysis = {
            'total_imports': len(self.codebase.imports),
            'external_imports': 0,
            'internal_imports': 0,
            'import_graph': {}
        }
        
        for imp in self.codebase.imports:
            try:
                if hasattr(imp, 'is_external') and imp.is_external:
                    import_analysis['external_imports'] += 1
                else:
                    import_analysis['internal_imports'] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to analyze import: {e}")
        
        self.results.import_analysis = import_analysis
    
    def _analyze_quality(self):
        """Analyze code quality metrics"""
        if not self.config.enable_metrics:
            return
        
        try:
            # Calculate quality metrics for each file
            quality_results = {}
            
            for file in self.codebase.files:
                if hasattr(file, 'source'):
                    metrics = self.quality_metrics.calculate_file_metrics(
                        file.source, file.filepath
                    )
                    quality_results[file.filepath] = metrics
            
            # Calculate complexity metrics
            complexity_results = self.complexity_analyzer.analyze_codebase(self.codebase)
            
            self.results.quality_metrics = quality_results
            self.results.complexity_metrics = complexity_results
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
    
    def _analyze_patterns(self):
        """Analyze code patterns and detect issues"""
        if not self.config.enable_pattern_detection:
            return
        
        try:
            # Detect code patterns
            patterns = self.pattern_detector.detect_patterns(self.codebase)
            self.results.code_patterns = patterns
            
            # Detect dead code
            dead_code = self.dead_code_detector.find_dead_code(self.codebase)
            self.results.dead_code = dead_code
            
            # Detect import loops
            import_loops = self.import_loop_detector.detect_loops(self.codebase)
            self.results.import_loops = import_loops
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
    
    def _analyze_dependencies(self):
        """Analyze dependencies and relationships"""
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph()
            self.results.dependency_graph = dependency_graph
            
            # Analyze call graphs
            call_graphs = self._analyze_call_graphs()
            self.results.call_graphs = call_graphs
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
    
    def _analyze_with_ai(self):
        """Perform AI-powered analysis"""
        if not self.config.enable_ai_analysis:
            return
        
        try:
            # Generate AI insights
            ai_insights = self.ai_analyzer.analyze_codebase(self.codebase)
            self.results.ai_insights = ai_insights
            
            # Generate training data if requested
            if self.config.generate_training_data:
                training_data = self.training_data_generator.generate_data(self.codebase)
                self.results.training_data = training_data
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
    
    def _generate_visualizations(self):
        """Generate visualizations and reports"""
        if not self.config.enable_visualization:
            return
        
        try:
            # Generate HTML report
            if self.config.generate_html_report:
                report_path = self.report_generator.generate_report(self.results)
                self.results.report_path = report_path
            
            # Generate interactive visualizations
            if self.config.generate_interactive_viz:
                viz_data = self._prepare_visualization_data()
                self.results.visualization_data = viz_data
                
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
    
    def _is_recursive_function(self, function) -> bool:
        """Check if function is recursive"""
        try:
            if hasattr(function, 'function_calls'):
                return any(call.name == function.name for call in function.function_calls)
            return False
        except:
            return False
    
    def _is_abstract_class(self, cls) -> bool:
        """Check if class is abstract"""
        try:
            if hasattr(cls, 'source'):
                return 'abc.ABC' in cls.source or '@abstractmethod' in cls.source
            return False
        except:
            return False
    
    def _build_dependency_graph(self) -> Dict[str, Any]:
        """Build dependency graph"""
        # Implementation for dependency graph construction
        return {}
    
    def _analyze_call_graphs(self) -> Dict[str, Any]:
        """Analyze call graphs"""
        # Implementation for call graph analysis
        return {}
    
    def _prepare_visualization_data(self) -> Dict[str, Any]:
        """Prepare data for visualizations"""
        # Implementation for visualization data preparation
        return {}


class CodebaseAnalyzer:
    """
    High-level analyzer that provides simple interface to the analysis engine.
    
    This is the main entry point for codebase analysis.
    """
    
    def __init__(self, config: AnalysisConfig = None):
        if config is None:
            from .config import AnalysisPresets
            config = AnalysisPresets.standard()
        
        self.config = config
        self.engine = AnalysisEngine(config)
    
    def analyze(self, path: str) -> AnalysisResult:
        """
        Analyze a codebase at the given path.
        
        Args:
            path: Path to analyze (file or directory)
            
        Returns:
            AnalysisResult containing all analysis data
        """
        return self.engine.analyze(path)
    
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """
        Analyze a repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            AnalysisResult containing all analysis data
        """
        return self.analyze(repo_path)
    
    def quick_analysis(self, path: str) -> AnalysisResult:
        """
        Perform quick analysis with basic metrics.
        
        Args:
            path: Path to analyze
            
        Returns:
            AnalysisResult with basic metrics
        """
        from .config import AnalysisPresets
        quick_config = AnalysisPresets.quick()
        quick_engine = AnalysisEngine(quick_config)
        return quick_engine.analyze(path)


# Convenience functions for backward compatibility
def analyze_codebase_comprehensive(path: str) -> AnalysisResult:
    """Comprehensive analysis (legacy compatibility)"""
    from .config import AnalysisPresets
    config = AnalysisPresets.comprehensive()
    analyzer = CodebaseAnalyzer(config)
    return analyzer.analyze(path)

def analyze_codebase_enhanced(path: str) -> AnalysisResult:
    """Enhanced analysis with graph-sitter (legacy compatibility)"""
    from .config import AnalysisPresets
    config = AnalysisPresets.enhanced()
    analyzer = CodebaseAnalyzer(config)
    return analyzer.analyze(path)

