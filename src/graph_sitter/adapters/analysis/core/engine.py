"""
Core Analysis Engine

The main orchestrator for all codebase analysis functionality.
Consolidates features from analyze_codebase.py, analyze_codebase_enhanced.py, and enhanced_analyzer.py.
"""

import ast
import json
import logging
import os
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union

from ..metrics.quality import QualityAnalyzer
from ..metrics.complexity import ComplexityAnalyzer
from ..detection.patterns import PatternDetector
from ..detection.dead_code import DeadCodeDetector
from ..detection.import_loops import ImportLoopDetector
from ..visualization.tree_sitter import TreeSitterVisualizer
from ..ai.insights import AIInsightGenerator
from .config import AnalysisConfig, AnalysisResult

# Configure logging
logger = logging.getLogger(__name__)

# Try to import graph-sitter components
try:
    from graph_sitter import Codebase
    from graph_sitter.core.codebase import Codebase as CoreCodebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    filepath: str
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    dead_code: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class AnalysisEngine:
    """
    Main analysis engine that orchestrates all analysis components.
    
    Consolidates functionality from:
    - analyze_codebase.py: Core analysis and metrics
    - analyze_codebase_enhanced.py: Enhanced graph-sitter integration
    - enhanced_analyzer.py: Advanced detection features
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine with configuration."""
        self.config = config or AnalysisConfig()
        
        # Initialize analysis components
        self.quality_analyzer = QualityAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.pattern_detector = PatternDetector()
        self.dead_code_detector = DeadCodeDetector()
        self.import_loop_detector = ImportLoopDetector()
        self.tree_sitter_visualizer = TreeSitterVisualizer()
        self.ai_insight_generator = AIInsightGenerator()
        
        # Analysis state
        self.codebase = None
        self.file_analyses = {}
        self.start_time = None
        
    def analyze_codebase(self, path: str, **kwargs) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            path: Path to the codebase to analyze
            **kwargs: Additional analysis options
            
        Returns:
            AnalysisResult containing all analysis data
        """
        self.start_time = time.time()
        logger.info(f"Starting comprehensive analysis of: {path}")
        
        try:
            # Initialize codebase
            if GRAPH_SITTER_AVAILABLE and self.config.use_graph_sitter:
                self.codebase = Codebase(path)
                return self._analyze_with_graph_sitter()
            else:
                return self._analyze_with_ast_only(path)
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                success=False,
                error=str(e),
                analysis_time=time.time() - self.start_time
            )
    
    def _analyze_with_graph_sitter(self) -> AnalysisResult:
        """Perform analysis using graph-sitter integration."""
        logger.info("Using graph-sitter for enhanced analysis")
        
        # Core analysis
        file_analyses = self._analyze_files_graph_sitter()
        
        # Advanced analysis
        quality_metrics = self.quality_analyzer.analyze_codebase(self.codebase)
        complexity_metrics = self.complexity_analyzer.analyze_codebase(self.codebase)
        patterns = self.pattern_detector.detect_patterns(self.codebase)
        dead_code = self.dead_code_detector.find_dead_code(self.codebase)
        import_loops = self.import_loop_detector.detect_loops(self.codebase)
        
        # AI insights (if enabled)
        ai_insights = {}
        if self.config.enable_ai_analysis:
            ai_insights = self.ai_insight_generator.generate_insights(self.codebase)
        
        # Visualization data
        visualization_data = {}
        if self.config.generate_visualizations:
            visualization_data = self.tree_sitter_visualizer.generate_data(self.codebase)
        
        # Compile results
        return AnalysisResult(
            success=True,
            codebase_path=str(self.codebase.root_path) if hasattr(self.codebase, 'root_path') else "unknown",
            analysis_time=time.time() - self.start_time,
            file_analyses=file_analyses,
            quality_metrics=quality_metrics,
            complexity_metrics=complexity_metrics,
            patterns=patterns,
            dead_code=dead_code,
            import_loops=import_loops,
            ai_insights=ai_insights,
            visualization_data=visualization_data,
            summary=self._generate_summary(file_analyses, quality_metrics, complexity_metrics)
        )
    
    def _analyze_with_ast_only(self, path: str) -> AnalysisResult:
        """Perform analysis using AST parsing only (fallback mode)."""
        logger.info("Using AST-only analysis (graph-sitter not available)")
        
        # Find Python files
        python_files = self._find_python_files(path)
        
        # Analyze each file
        file_analyses = {}
        for file_path in python_files:
            try:
                file_analyses[file_path] = self._analyze_file_ast(file_path)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Generate basic metrics
        quality_metrics = self._calculate_basic_quality_metrics(file_analyses)
        complexity_metrics = self._calculate_basic_complexity_metrics(file_analyses)
        
        return AnalysisResult(
            success=True,
            codebase_path=path,
            analysis_time=time.time() - self.start_time,
            file_analyses=file_analyses,
            quality_metrics=quality_metrics,
            complexity_metrics=complexity_metrics,
            summary=self._generate_summary(file_analyses, quality_metrics, complexity_metrics)
        )
    
    def _analyze_files_graph_sitter(self) -> Dict[str, FileAnalysis]:
        """Analyze all files using graph-sitter."""
        file_analyses = {}
        
        for file in self.codebase.files:
            try:
                analysis = FileAnalysis(filepath=file.filepath)
                
                # Analyze functions
                for function in file.functions:
                    func_analysis = self._analyze_function_graph_sitter(function)
                    analysis.functions.append(func_analysis)
                
                # Analyze classes
                for cls in file.classes:
                    class_analysis = self._analyze_class_graph_sitter(cls)
                    analysis.classes.append(class_analysis)
                
                # Analyze imports
                for imp in file.imports:
                    import_analysis = self._analyze_import_graph_sitter(imp)
                    analysis.imports.append(import_analysis)
                
                # Calculate file-level metrics
                analysis.metrics = self._calculate_file_metrics(analysis)
                
                file_analyses[file.filepath] = analysis
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file.filepath}: {e}")
        
        return file_analyses
    
    def _analyze_file_ast(self, file_path: str) -> FileAnalysis:
        """Analyze a single file using AST parsing."""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return FileAnalysis(filepath=file_path)
        
        analysis = FileAnalysis(filepath=file_path)
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_analysis = self._analyze_function_ast(node, file_path, source.splitlines())
                analysis.functions.append(func_analysis)
            elif isinstance(node, ast.ClassDef):
                class_analysis = self._analyze_class_ast(node, file_path, source.splitlines())
                analysis.classes.append(class_analysis)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_analysis = self._analyze_import_ast(node)
                analysis.imports.append(import_analysis)
        
        # Calculate file-level metrics
        analysis.metrics = self._calculate_file_metrics(analysis)
        
        return analysis
    
    def _analyze_function_graph_sitter(self, function) -> Dict[str, Any]:
        """Analyze a function using graph-sitter."""
        return {
            'name': function.name,
            'line_start': getattr(function, 'start_line', 0),
            'line_end': getattr(function, 'end_line', 0),
            'complexity': self.complexity_analyzer.calculate_cyclomatic_complexity(function),
            'quality_metrics': self.quality_analyzer.analyze_function(function),
            'parameters': [p.name for p in getattr(function, 'parameters', [])],
            'return_type': getattr(function, 'return_type', None),
            'docstring': getattr(function, 'docstring', None),
            'is_async': getattr(function, 'is_async', False),
            'decorators': [d.name for d in getattr(function, 'decorators', [])],
            'usages': len(getattr(function, 'usages', [])),
            'dependencies': len(getattr(function, 'dependencies', []))
        }
    
    def _analyze_class_graph_sitter(self, cls) -> Dict[str, Any]:
        """Analyze a class using graph-sitter."""
        return {
            'name': cls.name,
            'line_start': getattr(cls, 'start_line', 0),
            'line_end': getattr(cls, 'end_line', 0),
            'methods': [m.name for m in getattr(cls, 'methods', [])],
            'attributes': [a.name for a in getattr(cls, 'attributes', [])],
            'superclasses': [s.name for s in getattr(cls, 'superclasses', [])],
            'subclasses': [s.name for s in getattr(cls, 'subclasses', [])],
            'docstring': getattr(cls, 'docstring', None),
            'is_abstract': getattr(cls, 'is_abstract', False),
            'inheritance_depth': len(getattr(cls, 'superclasses', [])),
            'usages': len(getattr(cls, 'usages', []))
        }
    
    def _analyze_import_graph_sitter(self, imp) -> Dict[str, Any]:
        """Analyze an import using graph-sitter."""
        return {
            'module': getattr(imp, 'module_name', 'unknown'),
            'symbols': [s.name for s in getattr(imp, 'imported_symbols', [])],
            'is_relative': getattr(imp, 'is_relative', False),
            'line_number': getattr(imp, 'line_number', 0),
            'resolved': getattr(imp, 'resolved_symbol', None) is not None
        }
    
    def _analyze_function_ast(self, node: ast.FunctionDef, file_path: str, source_lines: List[str]) -> Dict[str, Any]:
        """Analyze a function using AST."""
        return {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': getattr(node, 'end_lineno', node.lineno),
            'complexity': self._calculate_cyclomatic_complexity_ast(node),
            'parameters': [arg.arg for arg in node.args.args],
            'return_type': ast.unparse(node.returns) if node.returns else None,
            'docstring': ast.get_docstring(node),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'lines_of_code': (getattr(node, 'end_lineno', node.lineno) - node.lineno + 1)
        }
    
    def _analyze_class_ast(self, node: ast.ClassDef, file_path: str, source_lines: List[str]) -> Dict[str, Any]:
        """Analyze a class using AST."""
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        attributes = []
        
        # Find attributes
        for n in node.body:
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        return {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': getattr(node, 'end_lineno', node.lineno),
            'methods': methods,
            'attributes': attributes,
            'superclasses': [ast.unparse(base) for base in node.bases],
            'docstring': ast.get_docstring(node),
            'inheritance_depth': len(node.bases),
            'lines_of_code': (getattr(node, 'end_lineno', node.lineno) - node.lineno + 1)
        }
    
    def _analyze_import_ast(self, node: Union[ast.Import, ast.ImportFrom]) -> Dict[str, Any]:
        """Analyze an import using AST."""
        if isinstance(node, ast.Import):
            return {
                'module': node.names[0].name if node.names else 'unknown',
                'symbols': [alias.name for alias in node.names],
                'is_relative': False,
                'line_number': node.lineno
            }
        else:  # ast.ImportFrom
            return {
                'module': node.module or 'unknown',
                'symbols': [alias.name for alias in node.names] if node.names else [],
                'is_relative': node.level > 0,
                'line_number': node.lineno
            }
    
    def _calculate_cyclomatic_complexity_ast(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity from AST."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_file_metrics(self, analysis: FileAnalysis) -> Dict[str, Any]:
        """Calculate file-level metrics."""
        return {
            'function_count': len(analysis.functions),
            'class_count': len(analysis.classes),
            'import_count': len(analysis.imports),
            'issue_count': len(analysis.issues),
            'total_complexity': sum(f.get('complexity', 0) for f in analysis.functions),
            'average_complexity': sum(f.get('complexity', 0) for f in analysis.functions) / len(analysis.functions) if analysis.functions else 0,
            'lines_of_code': sum(f.get('lines_of_code', 0) for f in analysis.functions + analysis.classes)
        }
    
    def _calculate_basic_quality_metrics(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, Any]:
        """Calculate basic quality metrics for AST-only mode."""
        total_functions = sum(len(fa.functions) for fa in file_analyses.values())
        total_classes = sum(len(fa.classes) for fa in file_analyses.values())
        total_complexity = sum(fa.metrics.get('total_complexity', 0) for fa in file_analyses.values())
        
        return {
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_files': len(file_analyses),
            'average_complexity': total_complexity / total_functions if total_functions > 0 else 0,
            'maintainability_score': max(0, 100 - (total_complexity / total_functions * 5)) if total_functions > 0 else 100
        }
    
    def _calculate_basic_complexity_metrics(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, Any]:
        """Calculate basic complexity metrics for AST-only mode."""
        complexities = []
        for fa in file_analyses.values():
            for func in fa.functions:
                complexities.append(func.get('complexity', 1))
        
        if not complexities:
            return {'max_complexity': 0, 'min_complexity': 0, 'median_complexity': 0}
        
        complexities.sort()
        return {
            'max_complexity': max(complexities),
            'min_complexity': min(complexities),
            'median_complexity': complexities[len(complexities) // 2],
            'complexity_distribution': Counter(complexities)
        }
    
    def _generate_summary(self, file_analyses: Dict[str, FileAnalysis], 
                         quality_metrics: Dict[str, Any], 
                         complexity_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            'total_files': len(file_analyses),
            'total_functions': quality_metrics.get('total_functions', 0),
            'total_classes': quality_metrics.get('total_classes', 0),
            'average_complexity': quality_metrics.get('average_complexity', 0),
            'maintainability_score': quality_metrics.get('maintainability_score', 0),
            'max_complexity': complexity_metrics.get('max_complexity', 0),
            'analysis_timestamp': time.time(),
            'graph_sitter_enabled': GRAPH_SITTER_AVAILABLE and self.config.use_graph_sitter
        }
    
    def _find_python_files(self, path: str) -> List[str]:
        """Find all Python files in the given path."""
        python_files = []
        path_obj = Path(path)
        
        if path_obj.is_file() and path_obj.suffix == '.py':
            return [str(path_obj)]
        
        for root, dirs, files in os.walk(path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return python_files


def analyze_codebase(path: str, config: Optional[AnalysisConfig] = None, **kwargs) -> AnalysisResult:
    """
    Convenience function for codebase analysis.
    
    Args:
        path: Path to the codebase to analyze
        config: Analysis configuration
        **kwargs: Additional options
        
    Returns:
        AnalysisResult containing all analysis data
    """
    engine = AnalysisEngine(config)
    return engine.analyze_codebase(path, **kwargs)

