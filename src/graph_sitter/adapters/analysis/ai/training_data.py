"""
Training Data Generation Module

Generates training data for ML models from code analysis.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates training data from code analysis."""
    
    def __init__(self, config=None):
        """Initialize training data generator."""
        self.config = config
    
    def generate(self, codebase=None, analysis_result=None) -> List[Dict[str, Any]]:
        """
        Generate training data from analysis results.
        
        Args:
            codebase: Graph-sitter codebase object
            analysis_result: Analysis results
            
        Returns:
            List of training data items
        """
        logger.info("Generating training data")
        
        training_data = []
        
        # Generate training data from analysis results
        if analysis_result:
            # Function complexity training data
            if analysis_result.complexity_metrics:
                func_metrics = analysis_result.complexity_metrics.get('function_complexity', {})
                for func_key, metrics in func_metrics.items():
                    training_data.append({
                        'type': 'function_complexity',
                        'function': func_key,
                        'features': {
                            'cyclomatic_complexity': metrics.get('cyclomatic_complexity', 0),
                            'cognitive_complexity': metrics.get('cognitive_complexity', 0),
                            'code_lines': metrics.get('code_lines', 0),
                            'parameters_count': metrics.get('parameters_count', 0)
                        },
                        'label': self._classify_complexity(metrics.get('cyclomatic_complexity', 0))
                    })
            
            # Quality metrics training data
            if analysis_result.quality_metrics:
                file_metrics = analysis_result.quality_metrics.get('file_metrics', {})
                for file_path, metrics in file_metrics.items():
                    training_data.append({
                        'type': 'file_quality',
                        'file': file_path,
                        'features': {
                            'maintainability_index': metrics.get('maintainability_index', 0),
                            'comment_ratio': metrics.get('comment_ratio', 0),
                            'functions_count': metrics.get('functions_count', 0),
                            'classes_count': metrics.get('classes_count', 0)
                        },
                        'label': self._classify_quality(metrics.get('maintainability_index', 0))
                    })
        
        logger.info(f"Generated {len(training_data)} training data items")
        return training_data
    
    def _classify_complexity(self, complexity: int) -> str:
        """Classify complexity level."""
        if complexity <= 5:
            return 'low'
        elif complexity <= 10:
            return 'medium'
        else:
            return 'high'
    
    def _classify_quality(self, maintainability: float) -> str:
        """Classify quality level."""
        if maintainability >= 80:
            return 'high'
        elif maintainability >= 60:
            return 'medium'
        else:
            return 'low'

