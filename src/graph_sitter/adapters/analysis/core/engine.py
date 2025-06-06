"""
Core Analysis Engine

Main engine for codebase analysis that integrates all analysis modules
and provides a unified interface for comprehensive codebase analysis.
"""

import logging
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .config import AnalysisConfig, AnalysisResult

# Import analysis modules
try:
    from ..metrics.quality import QualityMetrics
    from ..metrics.complexity import ComplexityAnalyzer
    from ..visualization.tree_sitter import TreeSitterVisualizer
    from ..detection.patterns import PatternDetector
    from ..detection.import_loops import ImportLoopDetector
    from ..detection.dead_code import DeadCodeDetector
    from ..ai.insights import AIInsights
    from ..ai.training_data import TrainingDataGenerator
    from ..integration.graph_sitter_config import GraphSitterConfigManager
except ImportError:
    # Modules will be created in subsequent steps
    pass

# Graph-sitter integration
try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    Codebase = None

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """
    Main analysis engine that coordinates all analysis modules.
    
    Based on features from README2.md and graph-sitter advanced settings.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine."""
        self.config = config or AnalysisConfig()
        self.codebase: Optional[Codebase] = None
        self.result: Optional[AnalysisResult] = None
        
        # Initialize analysis modules
        self._init_modules()
        
        # Setup logging
        if self.config.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif self.config.verbose:
            logging.basicConfig(level=logging.INFO)
    
    def _init_modules(self):
        """Initialize analysis modules based on configuration."""
        self.modules = {}
        
        try:
            if self.config.enable_metrics:
                self.modules['quality'] = QualityMetrics(self.config)
                self.modules['complexity'] = ComplexityAnalyzer(self.config)
            
            if self.config.enable_visualization:
                self.modules['visualizer'] = TreeSitterVisualizer(self.config)
            
            if self.config.enable_pattern_detection:
                self.modules['patterns'] = PatternDetector(self.config)
            
            if self.config.enable_import_loop_detection:
                self.modules['import_loops'] = ImportLoopDetector(self.config)
            
            if self.config.enable_dead_code_detection:
                self.modules['dead_code'] = DeadCodeDetector(self.config)
            
            if self.config.enable_ai_insights:
                self.modules['ai_insights'] = AIInsights(self.config)
                self.modules['training_data'] = TrainingDataGenerator(self.config)
            
            # Graph-sitter configuration manager
            self.modules['graph_sitter_config'] = GraphSitterConfigManager(self.config)
            
        except ImportError as e:
            logger.warning(f"Some analysis modules not available: {e}")
    
    def analyze_codebase(self, path: Union[str, Path]) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            path: Path to codebase or repository
            
        Returns:
            AnalysisResult containing all analysis data
        """
        start_time = time.time()
        path = Path(path)
        
        logger.info(f"Starting analysis of codebase: {path}")
        
        # Initialize result
        self.result = AnalysisResult(
            codebase_path=str(path),
            language="unknown",
            total_files=0,
            total_lines=0,
            config_used=self.config.to_dict()
        )
        
        try:
            # Initialize codebase with graph-sitter if available
            if GRAPH_SITTER_AVAILABLE:
                self._init_graph_sitter_codebase(path)
            else:
                self._init_fallback_analysis(path)
            
            # Run analysis modules
            self._run_analysis_modules()
            
            # Calculate execution time
            self.result.analysis_time = time.time() - start_time
            
            logger.info(f"Analysis completed in {self.result.analysis_time:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            self.result.errors.append(error_msg)
            self.result.analysis_time = time.time() - start_time
        
        return self.result
    
    def _init_graph_sitter_codebase(self, path: Path):
        """Initialize codebase using graph-sitter."""
        try:
            # Get graph-sitter configuration
            codebase_config = self.config.to_codebase_config()
            secrets_config = self.config.to_secrets_config()
            
            # Initialize codebase
            self.codebase = Codebase(
                str(path),
                config=codebase_config,
                secrets=secrets_config
            )
            
            # Update result with codebase info
            self.result.language = getattr(self.codebase, 'language', 'unknown')
            self.result.total_files = len(list(self.codebase.files))
            
            # Calculate total lines
            total_lines = 0
            for file in self.codebase.files:
                try:
                    total_lines += len(file.content.splitlines())
                except Exception as e:
                    logger.warning(f"Could not read file {file.filepath}: {e}")
            
            self.result.total_lines = total_lines
            
            logger.info(f"Initialized graph-sitter codebase: {self.result.language}, "
                       f"{self.result.total_files} files, {self.result.total_lines} lines")
            
        except Exception as e:
            logger.error(f"Failed to initialize graph-sitter codebase: {e}")
            self.result.errors.append(f"Graph-sitter initialization failed: {e}")
            # Fall back to basic analysis
            self._init_fallback_analysis(path)
    
    def _init_fallback_analysis(self, path: Path):
        """Initialize basic analysis without graph-sitter."""
        logger.info("Using fallback analysis (graph-sitter not available)")
        
        # Count files and lines manually
        total_files = 0
        total_lines = 0
        
        for ext in self.config.file_extensions:
            for file_path in path.rglob(f"*{ext}"):
                if self._should_include_file(file_path):
                    total_files += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            total_lines += len(f.readlines())
                    except Exception as e:
                        logger.warning(f"Could not read file {file_path}: {e}")
        
        # Detect language from file extensions
        if any(ext in ['.py'] for ext in self.config.file_extensions):
            language = 'python'
        elif any(ext in ['.ts', '.tsx'] for ext in self.config.file_extensions):
            language = 'typescript'
        elif any(ext in ['.js', '.jsx'] for ext in self.config.file_extensions):
            language = 'javascript'
        else:
            language = 'unknown'
        
        self.result.language = language
        self.result.total_files = total_files
        self.result.total_lines = total_lines
        
        logger.info(f"Fallback analysis initialized: {language}, "
                   f"{total_files} files, {total_lines} lines")
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in analysis."""
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if pattern in str(file_path):
                return False
        
        # Check if it's a test file and tests are disabled
        if not self.config.include_tests and ('test' in str(file_path).lower()):
            return False
        
        # Check if it's a doc file and docs are disabled
        if not self.config.include_docs and any(doc_ext in str(file_path) 
                                               for doc_ext in ['.md', '.rst', '.txt']):
            return False
        
        return True
    
    def _run_analysis_modules(self):
        """Run all enabled analysis modules."""
        logger.info("Running analysis modules...")
        
        # Quality metrics
        if 'quality' in self.modules:
            try:
                logger.debug("Running quality metrics analysis")
                self.result.quality_metrics = self.modules['quality'].analyze(
                    self.codebase, self.result.codebase_path
                )
            except Exception as e:
                error_msg = f"Quality metrics analysis failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Complexity analysis
        if 'complexity' in self.modules:
            try:
                logger.debug("Running complexity analysis")
                self.result.complexity_metrics = self.modules['complexity'].analyze(
                    self.codebase, self.result.codebase_path
                )
            except Exception as e:
                error_msg = f"Complexity analysis failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Import loop detection
        if 'import_loops' in self.modules:
            try:
                logger.debug("Running import loop detection")
                self.result.import_loops = self.modules['import_loops'].detect(
                    self.codebase, self.result.codebase_path
                )
            except Exception as e:
                error_msg = f"Import loop detection failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Dead code detection
        if 'dead_code' in self.modules:
            try:
                logger.debug("Running dead code detection")
                self.result.dead_code = self.modules['dead_code'].detect(
                    self.codebase, self.result.codebase_path
                )
            except Exception as e:
                error_msg = f"Dead code detection failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Pattern detection
        if 'patterns' in self.modules:
            try:
                logger.debug("Running pattern detection")
                self.result.patterns = self.modules['patterns'].detect(
                    self.codebase, self.result.codebase_path
                )
            except Exception as e:
                error_msg = f"Pattern detection failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Tree-sitter visualization
        if 'visualizer' in self.modules:
            try:
                logger.debug("Running tree-sitter visualization")
                viz_data = self.modules['visualizer'].generate_visualization(
                    self.codebase, self.result.codebase_path
                )
                self.result.tree_structure = viz_data.get('tree_structure')
                self.result.dependency_graph = viz_data.get('dependency_graph')
            except Exception as e:
                error_msg = f"Visualization generation failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # AI insights
        if 'ai_insights' in self.modules:
            try:
                logger.debug("Running AI insights analysis")
                self.result.ai_insights = self.modules['ai_insights'].generate_insights(
                    self.codebase, self.result
                )
            except Exception as e:
                error_msg = f"AI insights generation failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
        
        # Training data generation
        if 'training_data' in self.modules:
            try:
                logger.debug("Running training data generation")
                self.result.training_data = self.modules['training_data'].generate(
                    self.codebase, self.result
                )
            except Exception as e:
                error_msg = f"Training data generation failed: {e}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
    
    def export_results(self, output_path: Optional[str] = None) -> str:
        """
        Export analysis results to file.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            Path to exported file
        """
        if not self.result:
            raise ValueError("No analysis results to export")
        
        if not output_path:
            timestamp = int(time.time())
            output_path = f"analysis_results_{timestamp}.{self.config.output_format}"
        
        output_path = Path(output_path)
        
        if self.config.output_format == 'json':
            import json
            with open(output_path, 'w') as f:
                json.dump(self.result.to_dict(), f, indent=2)
        
        elif self.config.output_format == 'html':
            self._export_html(output_path)
        
        elif self.config.output_format == 'text':
            self._export_text(output_path)
        
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")
        
        logger.info(f"Results exported to: {output_path}")
        return str(output_path)
    
    def _export_html(self, output_path: Path):
        """Export results as HTML."""
        # This will be implemented when visualization module is created
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin: 10px 0; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Results</h1>
            <h2>Summary</h2>
            <div class="metric">Path: {self.result.codebase_path}</div>
            <div class="metric">Language: {self.result.language}</div>
            <div class="metric">Files: {self.result.total_files}</div>
            <div class="metric">Lines: {self.result.total_lines}</div>
            <div class="metric">Analysis Time: {self.result.analysis_time:.2f}s</div>
            
            <h2>Errors</h2>
            {''.join(f'<div class="error">{error}</div>' for error in self.result.errors)}
            
            <h2>Warnings</h2>
            {''.join(f'<div class="warning">{warning}</div>' for warning in self.result.warnings)}
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _export_text(self, output_path: Path):
        """Export results as text."""
        content = f"""
Codebase Analysis Results
========================

Summary:
  Path: {self.result.codebase_path}
  Language: {self.result.language}
  Files: {self.result.total_files}
  Lines: {self.result.total_lines}
  Analysis Time: {self.result.analysis_time:.2f}s

Errors:
{chr(10).join(f"  - {error}" for error in self.result.errors)}

Warnings:
{chr(10).join(f"  - {warning}" for warning in self.result.warnings)}
        """
        
        with open(output_path, 'w') as f:
            f.write(content.strip())

