"""
🔄 Legacy Compatibility Layer

Provides backward compatibility with existing analysis tools:
- analyze_codebase.py
- analyze_codebase_enhanced.py
- enhanced_analyzer.py
- graph_sitter_enhancements.py

This module ensures existing code continues to work while providing
migration paths to the new consolidated system.
"""

import logging
import warnings
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Import the new system
from ..core.engine import CodebaseAnalyzer, AnalysisEngine
from ..core.config import AnalysisConfig, AnalysisResult, AnalysisPresets


class LegacyAnalyzerWrapper:
    """
    Wrapper that provides legacy API compatibility.
    
    This class maintains the same interface as the original tools
    while using the new consolidated system underneath.
    """
    
    def __init__(self, use_graph_sitter: bool = True):
        self.use_graph_sitter = use_graph_sitter
        self._setup_config()
    
    def _setup_config(self):
        """Setup configuration based on legacy preferences"""
        if self.use_graph_sitter:
            self.config = AnalysisPresets.enhanced()
        else:
            self.config = AnalysisPresets.standard()
            self.config.enable_graph_sitter = False
    
    def analyze_codebase(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Legacy analyze_codebase function compatibility.
        
        Maintains the same interface as the original analyze_codebase.py
        """
        warnings.warn(
            "analyze_codebase is deprecated. Use code_analysis.analyze_codebase instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Update config with legacy parameters
        self._update_config_from_kwargs(kwargs)
        
        # Run analysis
        analyzer = CodebaseAnalyzer(self.config)
        result = analyzer.analyze(path)
        
        # Convert to legacy format
        return self._convert_to_legacy_format(result)
    
    def analyze_codebase_enhanced(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Legacy analyze_codebase_enhanced function compatibility.
        
        Maintains the same interface as the original analyze_codebase_enhanced.py
        """
        warnings.warn(
            "analyze_codebase_enhanced is deprecated. Use code_analysis.comprehensive_analysis instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Use enhanced configuration
        self.config = AnalysisPresets.enhanced()
        self._update_config_from_kwargs(kwargs)
        
        analyzer = CodebaseAnalyzer(self.config)
        result = analyzer.analyze(path)
        
        return self._convert_to_legacy_format(result)
    
    def enhanced_analyzer_analyze(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Legacy EnhancedCodebaseAnalyzer compatibility.
        
        Maintains the same interface as the original enhanced_analyzer.py
        """
        warnings.warn(
            "EnhancedCodebaseAnalyzer is deprecated. Use code_analysis.CodebaseAnalyzer instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.config = AnalysisPresets.enhanced()
        self._update_config_from_kwargs(kwargs)
        
        analyzer = CodebaseAnalyzer(self.config)
        result = analyzer.analyze(path)
        
        return self._convert_to_enhanced_format(result)
    
    def _update_config_from_kwargs(self, kwargs: Dict[str, Any]):
        """Update configuration from legacy keyword arguments"""
        # Map legacy parameters to new config
        legacy_mapping = {
            'use_graph_sitter': 'enable_graph_sitter',
            'comprehensive': lambda v: setattr(self.config, 'analysis_level', 'comprehensive' if v else 'standard'),
            'visualize': 'enable_visualization',
            'export_html': lambda v: setattr(self.config.visualization_config, 'generate_html_report', v),
            'tree_sitter': 'enable_graph_sitter',
            'training_data': 'generate_training_data',
            'import_loops': lambda v: setattr(self.config.pattern_detection_config, 'detect_import_loops', v),
            'dead_code': lambda v: setattr(self.config.pattern_detection_config, 'detect_dead_code', v),
            'ai_analysis': 'enable_ai_analysis',
            'format': lambda v: None,  # Handled in output conversion
            'output': lambda v: setattr(self.config, 'output_directory', str(Path(v).parent) if v else './analysis_output')
        }
        
        for key, value in kwargs.items():
            if key in legacy_mapping:
                mapping = legacy_mapping[key]
                if callable(mapping):
                    mapping(value)
                elif hasattr(self.config, mapping):
                    setattr(self.config, mapping, value)
    
    def _convert_to_legacy_format(self, result: AnalysisResult) -> Dict[str, Any]:
        """Convert new AnalysisResult to legacy format"""
        legacy_result = {
            'analysis_id': result.analysis_id,
            'timestamp': result.timestamp,
            'path': result.path,
            'success': result.success,
            'duration': result.analysis_duration,
            
            # Basic statistics
            'file_count': result.file_count,
            'function_count': result.function_count,
            'class_count': result.class_count,
            'import_count': result.import_count,
            'total_lines': result.total_lines,
            
            # Analysis results
            'files': result.file_analysis,
            'functions': result.function_analysis,
            'classes': result.class_analysis,
            'imports': result.import_analysis,
            
            # Metrics
            'quality_metrics': {
                path: {
                    'maintainability_index': metrics.maintainability_index,
                    'cyclomatic_complexity': metrics.cyclomatic_complexity,
                    'halstead_difficulty': metrics.halstead_difficulty,
                    'halstead_effort': metrics.halstead_effort,
                    'halstead_volume': metrics.halstead_volume,
                    'comment_ratio': metrics.comment_ratio,
                    'quality_score': metrics.quality_score
                }
                for path, metrics in result.quality_metrics.items()
            },
            
            'complexity_metrics': {
                'total_complexity': result.complexity_metrics.total_complexity,
                'average_complexity': result.complexity_metrics.average_complexity,
                'max_complexity': result.complexity_metrics.max_complexity,
                'high_complexity_functions': result.complexity_metrics.high_complexity_functions
            },
            
            # Pattern detection
            'dead_code': result.dead_code,
            'import_loops': result.import_loops,
            'code_patterns': result.code_patterns.pattern_summary if result.code_patterns else {},
            
            # Legacy fields for compatibility
            'codebase_summary': self._generate_legacy_summary(result),
            'recursive_functions': self._extract_recursive_functions(result),
            'test_analysis': self._generate_test_analysis(result),
            'issues': self._extract_issues(result)
        }
        
        # Add AI results if available
        if result.ai_insights:
            legacy_result['ai_insights'] = {
                'insights': result.ai_insights.insights,
                'suggestions': result.ai_insights.suggestions,
                'issues': result.ai_insights.issues_detected
            }
        
        # Add training data if available
        if result.training_data:
            legacy_result['training_data'] = result.training_data
        
        return legacy_result
    
    def _convert_to_enhanced_format(self, result: AnalysisResult) -> Dict[str, Any]:
        """Convert to enhanced analyzer format"""
        enhanced_result = self._convert_to_legacy_format(result)
        
        # Add enhanced-specific fields
        enhanced_result.update({
            'graph_analysis': result.dependency_graph,
            'call_graphs': result.call_graphs,
            'enhanced_metrics': {
                'dependency_complexity': len(result.dependency_graph),
                'import_complexity': len(result.import_loops),
                'pattern_violations': len(result.code_patterns.code_smells) if result.code_patterns else 0
            },
            'visualization_data': result.visualization_data
        })
        
        return enhanced_result
    
    def _generate_legacy_summary(self, result: AnalysisResult) -> str:
        """Generate legacy-style codebase summary"""
        summary_lines = [
            f"📊 Codebase Analysis Summary",
            f"Files: {result.file_count}",
            f"Functions: {result.function_count}",
            f"Classes: {result.class_count}",
            f"Imports: {result.import_count}"
        ]
        
        if result.quality_metrics:
            avg_quality = sum(m.quality_score for m in result.quality_metrics.values()) / len(result.quality_metrics)
            summary_lines.append(f"Average Quality Score: {avg_quality:.1f}/10")
        
        if result.dead_code:
            summary_lines.append(f"Dead Code Items: {len(result.dead_code)}")
        
        if result.import_loops:
            summary_lines.append(f"Import Loops: {len(result.import_loops)}")
        
        return "\n".join(summary_lines)
    
    def _extract_recursive_functions(self, result: AnalysisResult) -> List[str]:
        """Extract recursive functions for legacy compatibility"""
        recursive_functions = []
        
        for func_name, func_data in result.function_analysis.items():
            if func_data.get('is_recursive', False):
                recursive_functions.append(func_name)
        
        return recursive_functions
    
    def _generate_test_analysis(self, result: AnalysisResult) -> Dict[str, Any]:
        """Generate test analysis for legacy compatibility"""
        test_functions = []
        test_classes = []
        
        # Extract test functions and classes
        for func_name, func_data in result.function_analysis.items():
            if func_name.startswith('test_') or 'test' in func_name.lower():
                test_functions.append(func_name)
        
        for class_name, class_data in result.class_analysis.items():
            if class_name.startswith('Test') or 'test' in class_name.lower():
                test_classes.append(class_name)
        
        return {
            'total_test_functions': len(test_functions),
            'total_test_classes': len(test_classes),
            'test_functions': test_functions,
            'test_classes': test_classes,
            'coverage_estimate': self._estimate_test_coverage(result)
        }
    
    def _estimate_test_coverage(self, result: AnalysisResult) -> float:
        """Estimate test coverage for legacy compatibility"""
        if result.function_count == 0:
            return 0.0
        
        test_count = len([f for f in result.function_analysis.keys() 
                         if 'test' in f.lower()])
        
        return min(100.0, (test_count / result.function_count) * 100)
    
    def _extract_issues(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """Extract issues for legacy compatibility"""
        issues = []
        
        # Add dead code as issues
        for dead_item in result.dead_code:
            issues.append({
                'type': 'dead_code',
                'severity': 'medium',
                'message': f'Unused code detected: {dead_item}',
                'location': dead_item
            })
        
        # Add import loops as issues
        for loop in result.import_loops:
            issues.append({
                'type': 'import_loop',
                'severity': 'high',
                'message': f'Circular import detected',
                'location': ' -> '.join(loop.get('files', []))
            })
        
        # Add pattern violations as issues
        if result.code_patterns:
            for smell in result.code_patterns.code_smells:
                issues.append({
                    'type': 'code_smell',
                    'severity': smell.get('severity', 'medium'),
                    'message': smell.get('message', 'Code smell detected'),
                    'location': smell.get('location', 'unknown')
                })
        
        # Add AI-detected issues
        if result.ai_insights and result.ai_insights.issues_detected:
            for ai_issue in result.ai_insights.issues_detected:
                issues.append({
                    'type': 'ai_detected',
                    'severity': ai_issue.get('severity', 'medium'),
                    'message': ai_issue.get('message', 'AI detected issue'),
                    'location': ai_issue.get('location', 'unknown')
                })
        
        return issues


# Legacy function wrappers for backward compatibility
def analyze_codebase(path: str, use_graph_sitter: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Legacy analyze_codebase function.
    
    DEPRECATED: Use code_analysis.analyze_codebase instead.
    """
    wrapper = LegacyAnalyzerWrapper(use_graph_sitter)
    return wrapper.analyze_codebase(path, **kwargs)


def analyze_codebase_enhanced(path: str, **kwargs) -> Dict[str, Any]:
    """
    Legacy analyze_codebase_enhanced function.
    
    DEPRECATED: Use code_analysis.comprehensive_analysis instead.
    """
    wrapper = LegacyAnalyzerWrapper(True)
    return wrapper.analyze_codebase_enhanced(path, **kwargs)


class EnhancedCodebaseAnalyzer:
    """
    Legacy EnhancedCodebaseAnalyzer class.
    
    DEPRECATED: Use code_analysis.CodebaseAnalyzer instead.
    """
    
    def __init__(self, use_advanced_config: bool = False):
        warnings.warn(
            "EnhancedCodebaseAnalyzer is deprecated. Use code_analysis.CodebaseAnalyzer instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.wrapper = LegacyAnalyzerWrapper(True)
        if use_advanced_config:
            self.wrapper.config = AnalysisPresets.enhanced()
    
    def analyze_codebase_enhanced(self, path: str, **kwargs) -> Dict[str, Any]:
        """Legacy enhanced analysis method"""
        return self.wrapper.enhanced_analyzer_analyze(path, **kwargs)
    
    def analyze_training_data(self, path: str) -> Dict[str, Any]:
        """Legacy training data analysis"""
        self.wrapper.config.generate_training_data = True
        result = self.wrapper.enhanced_analyzer_analyze(path)
        return result.get('training_data', {})
    
    def analyze_import_loops(self, path: str) -> Dict[str, Any]:
        """Legacy import loop analysis"""
        self.wrapper.config.pattern_detection_config.detect_import_loops = True
        result = self.wrapper.enhanced_analyzer_analyze(path)
        return {'import_loops': result.get('import_loops', [])}
    
    def analyze_dead_code(self, path: str) -> Dict[str, Any]:
        """Legacy dead code analysis"""
        self.wrapper.config.pattern_detection_config.detect_dead_code = True
        result = self.wrapper.enhanced_analyzer_analyze(path)
        return {'dead_code': result.get('dead_code', [])}


# Legacy graph-sitter enhancement functions
def detect_import_loops(codebase) -> List[Dict[str, Any]]:
    """
    Legacy detect_import_loops function.
    
    DEPRECATED: Use code_analysis.detect_import_loops instead.
    """
    warnings.warn(
        "detect_import_loops is deprecated. Use code_analysis.detect_import_loops instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from ..detection.import_loops import ImportLoopDetector
    detector = ImportLoopDetector()
    return detector.detect_loops(codebase)


def detect_dead_code(codebase) -> List[str]:
    """
    Legacy detect_dead_code function.
    
    DEPRECATED: Use code_analysis.find_dead_code instead.
    """
    warnings.warn(
        "detect_dead_code is deprecated. Use code_analysis.find_dead_code instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from ..detection.dead_code import DeadCodeDetector
    detector = DeadCodeDetector()
    return detector.find_dead_code(codebase)


def generate_training_data(codebase) -> Dict[str, Any]:
    """
    Legacy generate_training_data function.
    
    DEPRECATED: Use code_analysis.generate_training_data instead.
    """
    warnings.warn(
        "generate_training_data is deprecated. Use code_analysis.generate_training_data instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from ..ai.training_data import TrainingDataGenerator
    generator = TrainingDataGenerator()
    return generator.generate_data(codebase)


# Migration helper functions
def migrate_to_new_system():
    """
    Print migration guide for users of legacy tools.
    """
    print("""
🔄 Migration Guide: Legacy Tools → New Code Analysis System

The analysis tools have been consolidated into a unified system.
Here's how to migrate your code:

OLD (deprecated):
    from graph_sitter.adapters.analyze_codebase import analyze_codebase
    result = analyze_codebase("./src")

NEW (recommended):
    from graph_sitter.adapters.code_analysis import analyze_codebase
    result = analyze_codebase("./src")

OLD (deprecated):
    from graph_sitter.adapters.enhanced_analyzer import EnhancedCodebaseAnalyzer
    analyzer = EnhancedCodebaseAnalyzer()
    result = analyzer.analyze_codebase_enhanced("./src")

NEW (recommended):
    from graph_sitter.adapters.code_analysis import CodebaseAnalyzer, AnalysisPresets
    analyzer = CodebaseAnalyzer(AnalysisPresets.enhanced())
    result = analyzer.analyze("./src")

Benefits of the new system:
✅ Unified API across all analysis features
✅ Better performance and caching
✅ More comprehensive analysis options
✅ Improved visualization and reporting
✅ AI-powered insights (optional)
✅ Better error handling and logging

For more information, see the documentation in code_analysis/README.md
    """)


def check_legacy_usage():
    """
    Check if legacy imports are being used and warn users.
    """
    import sys
    import inspect
    
    # Get the calling frame
    frame = inspect.currentframe().f_back
    
    # Check for legacy imports in the calling module
    if frame and hasattr(frame, 'f_globals'):
        module_name = frame.f_globals.get('__name__', '')
        
        legacy_patterns = [
            'analyze_codebase',
            'analyze_codebase_enhanced', 
            'enhanced_analyzer',
            'graph_sitter_enhancements'
        ]
        
        for pattern in legacy_patterns:
            if pattern in module_name:
                warnings.warn(
                    f"You're using legacy module '{module_name}'. "
                    f"Consider migrating to 'code_analysis' for better features and performance.",
                    DeprecationWarning,
                    stacklevel=3
                )
                break

