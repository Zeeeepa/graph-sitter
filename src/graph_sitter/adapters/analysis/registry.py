"""
Analysis Registry for managing and discovering analysis components.

This module provides a centralized registry for all analysis components,
enabling dynamic discovery, loading, and execution of different analysis types.
"""

import importlib
from typing import Dict, List, Type, Optional, Any
from dataclasses import dataclass

from graph_sitter.adapters.analysis.base import BaseAnalyzer, AnalysisType, AnalysisResult
from graph_sitter.core.codebase import Codebase


@dataclass
class AnalyzerInfo:
    """Information about a registered analyzer."""
    
    name: str
    analyzer_class: Type[BaseAnalyzer]
    analysis_type: AnalysisType
    description: str
    supported_languages: List[str]
    dependencies: List[str]
    enabled: bool = True


class AnalysisRegistry:
    """
    Registry for managing analysis components.
    
    This class provides a centralized way to register, discover, and execute
    different types of analysis components.
    """
    
    def __init__(self):
        """Initialize the analysis registry."""
        self._analyzers: Dict[str, AnalyzerInfo] = {}
        self._load_builtin_analyzers()
    
    def register_analyzer(
        self,
        name: str,
        analyzer_class: Type[BaseAnalyzer],
        analysis_type: AnalysisType,
        description: str,
        supported_languages: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        enabled: bool = True
    ) -> None:
        """
        Register an analyzer with the registry.
        
        Args:
            name: Unique name for the analyzer
            analyzer_class: The analyzer class
            analysis_type: Type of analysis performed
            description: Human-readable description
            supported_languages: List of supported programming languages
            dependencies: List of required dependencies
            enabled: Whether the analyzer is enabled by default
        """
        if supported_languages is None:
            # Get supported languages from the analyzer class
            try:
                temp_instance = analyzer_class(None)  # type: ignore
                supported_languages = temp_instance.get_supported_languages()
            except:
                supported_languages = ["python"]  # Default fallback
        
        analyzer_info = AnalyzerInfo(
            name=name,
            analyzer_class=analyzer_class,
            analysis_type=analysis_type,
            description=description,
            supported_languages=supported_languages or [],
            dependencies=dependencies or [],
            enabled=enabled
        )
        
        self._analyzers[name] = analyzer_info
    
    def get_analyzer(self, name: str) -> Optional[AnalyzerInfo]:
        """
        Get analyzer information by name.
        
        Args:
            name: Name of the analyzer
            
        Returns:
            AnalyzerInfo if found, None otherwise
        """
        return self._analyzers.get(name)
    
    def list_analyzers(
        self,
        analysis_type: Optional[AnalysisType] = None,
        language: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[AnalyzerInfo]:
        """
        List available analyzers with optional filtering.
        
        Args:
            analysis_type: Filter by analysis type
            language: Filter by supported language
            enabled_only: Only return enabled analyzers
            
        Returns:
            List of matching analyzer information
        """
        analyzers = list(self._analyzers.values())
        
        if enabled_only:
            analyzers = [a for a in analyzers if a.enabled]
        
        if analysis_type:
            analyzers = [a for a in analyzers if a.analysis_type == analysis_type]
        
        if language:
            analyzers = [a for a in analyzers if language.lower() in [l.lower() for l in a.supported_languages]]
        
        return analyzers
    
    def create_analyzer(
        self,
        name: str,
        codebase: Codebase,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAnalyzer]:
        """
        Create an analyzer instance.
        
        Args:
            name: Name of the analyzer
            codebase: Codebase to analyze
            config: Configuration for the analyzer
            
        Returns:
            Analyzer instance if successful, None otherwise
        """
        analyzer_info = self.get_analyzer(name)
        if not analyzer_info or not analyzer_info.enabled:
            return None
        
        try:
            return analyzer_info.analyzer_class(codebase, config)
        except Exception as e:
            print(f"Failed to create analyzer '{name}': {e}")
            return None
    
    def run_analysis(
        self,
        name: str,
        codebase: Codebase,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[AnalysisResult]:
        """
        Run a specific analysis.
        
        Args:
            name: Name of the analyzer
            codebase: Codebase to analyze
            config: Configuration for the analyzer
            
        Returns:
            AnalysisResult if successful, None otherwise
        """
        analyzer = self.create_analyzer(name, codebase, config)
        if not analyzer:
            return None
        
        try:
            return analyzer.analyze()
        except Exception as e:
            print(f"Analysis '{name}' failed: {e}")
            return None
    
    def run_multiple_analyses(
        self,
        codebase: Codebase,
        analyzer_names: Optional[List[str]] = None,
        analysis_types: Optional[List[AnalysisType]] = None,
        language: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, AnalysisResult]:
        """
        Run multiple analyses.
        
        Args:
            codebase: Codebase to analyze
            analyzer_names: Specific analyzer names to run
            analysis_types: Analysis types to run
            language: Filter by language support
            config: Configuration for analyzers
            
        Returns:
            Dictionary mapping analyzer names to results
        """
        results = {}
        
        if analyzer_names:
            # Run specific analyzers
            for name in analyzer_names:
                result = self.run_analysis(name, codebase, config)
                if result:
                    results[name] = result
        else:
            # Run all matching analyzers
            analyzers = self.list_analyzers(
                analysis_type=analysis_types[0] if analysis_types and len(analysis_types) == 1 else None,
                language=language,
                enabled_only=True
            )
            
            for analyzer_info in analyzers:
                if analysis_types and analyzer_info.analysis_type not in analysis_types:
                    continue
                
                result = self.run_analysis(analyzer_info.name, codebase, config)
                if result:
                    results[analyzer_info.name] = result
        
        return results
    
    def enable_analyzer(self, name: str) -> bool:
        """
        Enable an analyzer.
        
        Args:
            name: Name of the analyzer
            
        Returns:
            True if successful, False otherwise
        """
        analyzer_info = self.get_analyzer(name)
        if analyzer_info:
            analyzer_info.enabled = True
            return True
        return False
    
    def disable_analyzer(self, name: str) -> bool:
        """
        Disable an analyzer.
        
        Args:
            name: Name of the analyzer
            
        Returns:
            True if successful, False otherwise
        """
        analyzer_info = self.get_analyzer(name)
        if analyzer_info:
            analyzer_info.enabled = False
            return True
        return False
    
    def _load_builtin_analyzers(self) -> None:
        """Load built-in analyzers."""
        
        # Try to load each built-in analyzer
        builtin_analyzers = [
            {
                'name': 'call_graph',
                'module': 'graph_sitter.adapters.analysis.call_graph',
                'class': 'CallGraphAnalyzer',
                'analysis_type': AnalysisType.CALL_GRAPH,
                'description': 'Analyzes function call relationships and dependencies'
            },
            {
                'name': 'dead_code',
                'module': 'graph_sitter.adapters.analysis.dead_code',
                'class': 'DeadCodeAnalyzer',
                'analysis_type': AnalysisType.DEAD_CODE,
                'description': 'Detects unused functions, classes, and variables'
            },
            {
                'name': 'dependencies',
                'module': 'graph_sitter.adapters.analysis.dependency_analyzer',
                'class': 'DependencyAnalyzer',
                'analysis_type': AnalysisType.DEPENDENCIES,
                'description': 'Analyzes import dependencies and circular imports'
            },
            {
                'name': 'metrics',
                'module': 'graph_sitter.adapters.analysis.metrics',
                'class': 'CodebaseMetrics',
                'analysis_type': AnalysisType.METRICS,
                'description': 'Calculates code complexity and quality metrics'
            },
            {
                'name': 'function_context',
                'module': 'graph_sitter.adapters.analysis.function_context',
                'class': 'FunctionContextAnalyzer',
                'analysis_type': AnalysisType.FUNCTION_CONTEXT,
                'description': 'Analyzes function contexts and documentation'
            }
        ]
        
        for analyzer_config in builtin_analyzers:
            try:
                # Import the module
                module = importlib.import_module(analyzer_config['module'])
                
                # Get the analyzer class
                analyzer_class = getattr(module, analyzer_config['class'])
                
                # Register the analyzer
                self.register_analyzer(
                    name=analyzer_config['name'],
                    analyzer_class=analyzer_class,
                    analysis_type=analyzer_config['analysis_type'],
                    description=analyzer_config['description']
                )
                
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load built-in analyzer '{analyzer_config['name']}': {e}")
                # Register a placeholder for missing analyzers
                self.register_analyzer(
                    name=analyzer_config['name'],
                    analyzer_class=type('PlaceholderAnalyzer', (BaseAnalyzer,), {
                        '_get_analysis_type': lambda self: analyzer_config['analysis_type'],
                        'analyze': lambda self: self.create_result([], [], {}, [f"Analyzer {analyzer_config['name']} not available"])
                    }),
                    analysis_type=analyzer_config['analysis_type'],
                    description=f"{analyzer_config['description']} (Not Available)",
                    enabled=False
                )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available analyzers.
        
        Returns:
            Dictionary with analyzer statistics and information
        """
        analyzers = list(self._analyzers.values())
        enabled_analyzers = [a for a in analyzers if a.enabled]
        
        analysis_types = {}
        for analyzer in analyzers:
            analysis_type = analyzer.analysis_type.value
            if analysis_type not in analysis_types:
                analysis_types[analysis_type] = {'total': 0, 'enabled': 0}
            analysis_types[analysis_type]['total'] += 1
            if analyzer.enabled:
                analysis_types[analysis_type]['enabled'] += 1
        
        languages = set()
        for analyzer in enabled_analyzers:
            languages.update(analyzer.supported_languages)
        
        return {
            'total_analyzers': len(analyzers),
            'enabled_analyzers': len(enabled_analyzers),
            'analysis_types': analysis_types,
            'supported_languages': sorted(list(languages)),
            'analyzer_list': [
                {
                    'name': a.name,
                    'type': a.analysis_type.value,
                    'description': a.description,
                    'enabled': a.enabled,
                    'languages': a.supported_languages
                }
                for a in analyzers
            ]
        }


# Global registry instance
_global_registry = None


def get_registry() -> AnalysisRegistry:
    """
    Get the global analysis registry instance.
    
    Returns:
        Global AnalysisRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AnalysisRegistry()
    return _global_registry


def register_analyzer(*args, **kwargs) -> None:
    """Register an analyzer with the global registry."""
    get_registry().register_analyzer(*args, **kwargs)


def list_analyzers(*args, **kwargs) -> List[AnalyzerInfo]:
    """List analyzers from the global registry."""
    return get_registry().list_analyzers(*args, **kwargs)


def run_analysis(*args, **kwargs) -> Optional[AnalysisResult]:
    """Run analysis using the global registry."""
    return get_registry().run_analysis(*args, **kwargs)

