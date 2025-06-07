"""
Codebase Analyzer

High-level interface for codebase analysis operations.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from graph_sitter.core.codebase import Codebase

from ..config.analysis_config import AnalysisConfig
from .analysis_engine import AnalysisEngine, AnalysisResult


class CodebaseAnalyzer:
    """
    High-level interface for comprehensive codebase analysis.
    
    This class provides a simplified interface for performing various
    types of analysis on codebases using the underlying analysis engine.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the codebase analyzer.
        
        Args:
            config: Analysis configuration. If None, uses default configuration.
        """
        self.config = config or AnalysisConfig()
        self.engine = AnalysisEngine(self.config)
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, codebase_path: Union[str, Path], **kwargs) -> AnalysisResult:
        """
        Perform comprehensive analysis on a codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            **kwargs: Additional configuration overrides
            
        Returns:
            AnalysisResult containing all analysis data
        """
        # Apply any configuration overrides
        if kwargs:
            self._apply_config_overrides(kwargs)
        
        # Load the codebase
        codebase = self._load_codebase(codebase_path)
        
        # Perform analysis
        return self.engine.analyze_codebase(codebase)
    
    def quick_analysis(self, codebase_path: Union[str, Path]) -> AnalysisResult:
        """
        Perform a quick analysis with minimal features enabled.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            AnalysisResult with basic analysis data
        """
        # Use basic configuration for quick analysis
        original_config = self.config
        self.config = AnalysisConfig.get_basic_config()
        self.engine = AnalysisEngine(self.config)
        
        try:
            result = self.analyze(codebase_path)
            return result
        finally:
            # Restore original configuration
            self.config = original_config
            self.engine = AnalysisEngine(self.config)
    
    def comprehensive_analysis(self, codebase_path: Union[str, Path]) -> AnalysisResult:
        """
        Perform a comprehensive analysis with all features enabled.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            AnalysisResult with comprehensive analysis data
        """
        # Use comprehensive configuration
        original_config = self.config
        self.config = AnalysisConfig.get_comprehensive_config()
        self.engine = AnalysisEngine(self.config)
        
        try:
            result = self.analyze(codebase_path)
            return result
        finally:
            # Restore original configuration
            self.config = original_config
            self.engine = AnalysisEngine(self.config)
    
    def analyze_dependencies(self, codebase_path: Union[str, Path]) -> Dict[str, List[str]]:
        """
        Analyze only dependency relationships.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Dictionary mapping files to their dependencies
        """
        codebase = self._load_codebase(codebase_path)
        return self.engine._analyze_dependencies(codebase)
    
    def detect_dead_code(self, codebase_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Detect potentially dead code.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            List of dead code items found
        """
        codebase = self._load_codebase(codebase_path)
        return self.engine._detect_dead_code(codebase)
    
    def analyze_tests(self, codebase_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze test-related code.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Test analysis results
        """
        codebase = self._load_codebase(codebase_path)
        return self.engine._analyze_tests(codebase)
    
    def get_codebase_summary(self, codebase_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get a high-level summary of the codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Codebase summary data
        """
        codebase = self._load_codebase(codebase_path)
        return self.engine._analyze_codebase_summary(codebase)
    
    def analyze_file(self, codebase_path: Union[str, Path], file_name: str) -> Dict[str, Any]:
        """
        Analyze a specific file within the codebase.
        
        Args:
            codebase_path: Path to the codebase
            file_name: Name of the file to analyze
            
        Returns:
            File analysis data
        """
        codebase = self._load_codebase(codebase_path)
        
        # Find the specific file
        target_file = None
        for file in codebase.files:
            if file.name == file_name or str(file.filepath).endswith(file_name):
                target_file = file
                break
        
        if not target_file:
            raise ValueError(f"File '{file_name}' not found in codebase")
        
        # Analyze the file
        file_summaries = self.engine._analyze_files(codebase)
        return file_summaries.get(target_file.name, {})
    
    def analyze_function(self, codebase_path: Union[str, Path], function_name: str) -> Dict[str, Any]:
        """
        Analyze a specific function within the codebase.
        
        Args:
            codebase_path: Path to the codebase
            function_name: Name of the function to analyze
            
        Returns:
            Function analysis data
        """
        codebase = self._load_codebase(codebase_path)
        
        # Find the specific function
        target_function = None
        for function in codebase.functions:
            if function.name == function_name:
                target_function = function
                break
        
        if not target_function:
            raise ValueError(f"Function '{function_name}' not found in codebase")
        
        # Analyze the function
        function_summaries = self.engine._analyze_functions(codebase)
        return function_summaries.get(target_function.name, {})
    
    def analyze_class(self, codebase_path: Union[str, Path], class_name: str) -> Dict[str, Any]:
        """
        Analyze a specific class within the codebase.
        
        Args:
            codebase_path: Path to the codebase
            class_name: Name of the class to analyze
            
        Returns:
            Class analysis data
        """
        codebase = self._load_codebase(codebase_path)
        
        # Find the specific class
        target_class = None
        for cls in codebase.classes:
            if cls.name == class_name:
                target_class = cls
                break
        
        if not target_class:
            raise ValueError(f"Class '{class_name}' not found in codebase")
        
        # Analyze the class
        class_summaries = self.engine._analyze_classes(codebase)
        return class_summaries.get(target_class.name, {})
    
    def _load_codebase(self, codebase_path: Union[str, Path]) -> Codebase:
        """
        Load a codebase from the given path.
        
        Args:
            codebase_path: Path to the codebase
            
        Returns:
            Loaded Codebase object
        """
        try:
            path = Path(codebase_path)
            if not path.exists():
                raise ValueError(f"Codebase path does not exist: {path}")
            
            # Create codebase with graph-sitter configuration
            from codegen.configs import CodebaseConfig
            
            # Convert our config to CodebaseConfig
            gs_config = CodebaseConfig(**self.config.graph_sitter.to_dict())
            
            codebase = Codebase(str(path), config=gs_config)
            return codebase
            
        except Exception as e:
            self.logger.error(f"Failed to load codebase from {codebase_path}: {e}")
            raise
    
    def _apply_config_overrides(self, overrides: Dict[str, Any]):
        """
        Apply configuration overrides.
        
        Args:
            overrides: Dictionary of configuration overrides
        """
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.config.graph_sitter, key):
                setattr(self.config.graph_sitter, key, value)
            elif hasattr(self.config.performance, key):
                setattr(self.config.performance, key, value)
            else:
                self.logger.warning(f"Unknown configuration option: {key}")
        
        # Recreate engine with updated configuration
        self.engine = AnalysisEngine(self.config)

