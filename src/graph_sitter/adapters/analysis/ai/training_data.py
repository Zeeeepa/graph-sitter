"""
Training Data Generation Module

Generates training data for machine learning models from codebase analysis.
Creates datasets for code quality prediction, complexity estimation, and more.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates training data from codebase analysis."""
    
    def __init__(self):
        self.feature_extractors = {
            'function_features': self._extract_function_features,
            'class_features': self._extract_class_features,
            'file_features': self._extract_file_features,
            'complexity_features': self._extract_complexity_features,
            'quality_features': self._extract_quality_features
        }
        
        self.label_generators = {
            'complexity_label': self._generate_complexity_label,
            'quality_label': self._generate_quality_label,
            'maintainability_label': self._generate_maintainability_label,
            'refactoring_label': self._generate_refactoring_label
        }
    
    def generate_training_data(self, codebase, data_types: List[str] = None) -> Dict[str, Any]:
        """Generate training data from codebase analysis."""
        if data_types is None:
            data_types = ['function_analysis', 'complexity_prediction', 'quality_assessment']
        
        training_data = {
            'metadata': self._generate_metadata(codebase),
            'datasets': {}
        }
        
        try:
            if hasattr(codebase, 'functions'):
                training_data['datasets'] = self._generate_datasets_graph_sitter(codebase, data_types)
            else:
                training_data['datasets'] = self._generate_datasets_ast(codebase, data_types)
        except Exception as e:
            logger.error(f"Training data generation failed: {e}")
            training_data['error'] = str(e)
        
        return training_data
    
    def _generate_datasets_graph_sitter(self, codebase, data_types: List[str]) -> Dict[str, Any]:
        """Generate datasets using graph-sitter data."""
        datasets = {}
        
        if 'function_analysis' in data_types:
            datasets['function_analysis'] = self._create_function_dataset(codebase)
        
        if 'complexity_prediction' in data_types:
            datasets['complexity_prediction'] = self._create_complexity_dataset(codebase)
        
        if 'quality_assessment' in data_types:
            datasets['quality_assessment'] = self._create_quality_dataset(codebase)
        
        if 'refactoring_suggestions' in data_types:
            datasets['refactoring_suggestions'] = self._create_refactoring_dataset(codebase)
        
        if 'code_similarity' in data_types:
            datasets['code_similarity'] = self._create_similarity_dataset(codebase)
        
        return datasets
    
    def _generate_datasets_ast(self, file_analyses: Dict[str, Any], data_types: List[str]) -> Dict[str, Any]:
        """Generate datasets using AST data."""
        datasets = {}
        
        if 'function_analysis' in data_types:
            datasets['function_analysis'] = self._create_function_dataset_ast(file_analyses)
        
        if 'complexity_prediction' in data_types:
            datasets['complexity_prediction'] = self._create_complexity_dataset_ast(file_analyses)
        
        return datasets
    
    def _create_function_dataset(self, codebase) -> Dict[str, Any]:
        """Create function analysis training dataset."""
        dataset = {
            'description': 'Function analysis dataset for ML training',
            'features': [],
            'labels': [],
            'feature_names': self._get_function_feature_names(),
            'label_names': ['complexity', 'quality_score', 'maintainability'],
            'samples': []
        }
        
        for function in codebase.functions:
            try:
                features = self._extract_function_features(function)
                labels = self._generate_function_labels(function)
                
                sample = {
                    'id': self._generate_sample_id(function),
                    'name': function.name,
                    'file': function.filepath,
                    'features': features,
                    'labels': labels,
                    'metadata': {
                        'line_start': getattr(function, 'start_line', 0),
                        'line_end': getattr(function, 'end_line', 0),
                        'has_docstring': bool(getattr(function, 'docstring', None)),
                        'parameter_count': len(getattr(function, 'parameters', []))
                    }
                }
                
                dataset['samples'].append(sample)
                dataset['features'].append(features)
                dataset['labels'].append(labels)
            
            except Exception as e:
                logger.warning(f"Failed to process function {function.name}: {e}")
        
        return dataset
    
    def _create_complexity_dataset(self, codebase) -> Dict[str, Any]:
        """Create complexity prediction training dataset."""
        dataset = {
            'description': 'Complexity prediction dataset',
            'task_type': 'regression',
            'target': 'cyclomatic_complexity',
            'samples': []
        }
        
        for function in codebase.functions:
            try:
                features = self._extract_complexity_features(function)
                complexity = getattr(function, 'complexity', 1)
                
                sample = {
                    'id': self._generate_sample_id(function),
                    'features': features,
                    'target': complexity,
                    'metadata': {
                        'function_name': function.name,
                        'file': function.filepath,
                        'lines_of_code': len(function.source.splitlines()) if hasattr(function, 'source') else 0
                    }
                }
                
                dataset['samples'].append(sample)
            
            except Exception as e:
                logger.warning(f"Failed to process function {function.name} for complexity: {e}")
        
        return dataset
    
    def _create_quality_dataset(self, codebase) -> Dict[str, Any]:
        """Create code quality assessment training dataset."""
        dataset = {
            'description': 'Code quality assessment dataset',
            'task_type': 'classification',
            'classes': ['low', 'medium', 'high'],
            'samples': []
        }
        
        for function in codebase.functions:
            try:
                features = self._extract_quality_features(function)
                quality_label = self._generate_quality_label(function)
                
                sample = {
                    'id': self._generate_sample_id(function),
                    'features': features,
                    'label': quality_label,
                    'metadata': {
                        'function_name': function.name,
                        'file': function.filepath,
                        'has_docstring': bool(getattr(function, 'docstring', None)),
                        'has_type_hints': bool(getattr(function, 'return_type', None))
                    }
                }
                
                dataset['samples'].append(sample)
            
            except Exception as e:
                logger.warning(f"Failed to process function {function.name} for quality: {e}")
        
        return dataset
    
    def _create_refactoring_dataset(self, codebase) -> Dict[str, Any]:
        """Create refactoring suggestions training dataset."""
        dataset = {
            'description': 'Refactoring suggestions dataset',
            'task_type': 'multi_label_classification',
            'labels': ['extract_method', 'reduce_complexity', 'improve_naming', 'add_documentation'],
            'samples': []
        }
        
        for function in codebase.functions:
            try:
                features = self._extract_function_features(function)
                refactoring_labels = self._generate_refactoring_label(function)
                
                sample = {
                    'id': self._generate_sample_id(function),
                    'features': features,
                    'labels': refactoring_labels,
                    'metadata': {
                        'function_name': function.name,
                        'file': function.filepath,
                        'complexity': getattr(function, 'complexity', 1)
                    }
                }
                
                dataset['samples'].append(sample)
            
            except Exception as e:
                logger.warning(f"Failed to process function {function.name} for refactoring: {e}")
        
        return dataset
    
    def _create_similarity_dataset(self, codebase) -> Dict[str, Any]:
        """Create code similarity training dataset."""
        dataset = {
            'description': 'Code similarity dataset for duplicate detection',
            'task_type': 'similarity',
            'pairs': []
        }
        
        functions = list(codebase.functions)
        
        # Generate pairs of functions for similarity comparison
        for i, func1 in enumerate(functions):
            for j, func2 in enumerate(functions[i+1:], i+1):
                try:
                    features1 = self._extract_function_features(func1)
                    features2 = self._extract_function_features(func2)
                    
                    similarity_score = self._calculate_similarity(func1, func2)
                    
                    pair = {
                        'id': f"{self._generate_sample_id(func1)}_{self._generate_sample_id(func2)}",
                        'function1': {
                            'name': func1.name,
                            'file': func1.filepath,
                            'features': features1
                        },
                        'function2': {
                            'name': func2.name,
                            'file': func2.filepath,
                            'features': features2
                        },
                        'similarity_score': similarity_score,
                        'is_similar': similarity_score > 0.7
                    }
                    
                    dataset['pairs'].append(pair)
                    
                    # Limit pairs to prevent explosion
                    if len(dataset['pairs']) >= 1000:
                        break
                
                except Exception as e:
                    logger.warning(f"Failed to process function pair: {e}")
            
            if len(dataset['pairs']) >= 1000:
                break
        
        return dataset
    
    def _extract_function_features(self, function) -> List[float]:
        """Extract features from a function for ML training."""
        features = []
        
        # Basic metrics
        features.append(len(getattr(function, 'parameters', [])))  # Parameter count
        features.append(getattr(function, 'complexity', 1))  # Cyclomatic complexity
        features.append(1.0 if getattr(function, 'docstring', None) else 0.0)  # Has docstring
        features.append(1.0 if getattr(function, 'return_type', None) else 0.0)  # Has return type
        
        # Source code metrics
        if hasattr(function, 'source'):
            source = function.source
            features.append(len(source.splitlines()))  # Lines of code
            features.append(len(source))  # Character count
            features.append(source.count('if'))  # If statements
            features.append(source.count('for'))  # For loops
            features.append(source.count('while'))  # While loops
            features.append(source.count('try'))  # Try blocks
            features.append(source.count('def '))  # Nested functions
            features.append(source.count('class '))  # Nested classes
        else:
            features.extend([0.0] * 8)  # Default values
        
        # Name-based features
        name = function.name
        features.append(len(name))  # Name length
        features.append(1.0 if name.startswith('_') else 0.0)  # Is private
        features.append(1.0 if name.startswith('test_') else 0.0)  # Is test
        features.append(name.count('_'))  # Underscore count
        
        # Usage metrics
        usages = getattr(function, 'usages', [])
        features.append(len(usages))  # Usage count
        
        return features
    
    def _extract_class_features(self, cls) -> List[float]:
        """Extract features from a class for ML training."""
        features = []
        
        # Basic metrics
        methods = getattr(cls, 'methods', [])
        attributes = getattr(cls, 'attributes', [])
        superclasses = getattr(cls, 'superclasses', [])
        
        features.append(len(methods))  # Method count
        features.append(len(attributes))  # Attribute count
        features.append(len(superclasses))  # Inheritance depth
        features.append(1.0 if getattr(cls, 'docstring', None) else 0.0)  # Has docstring
        
        # Name-based features
        name = cls.name
        features.append(len(name))  # Name length
        features.append(1.0 if name.startswith('_') else 0.0)  # Is private
        features.append(1.0 if name.endswith('Test') else 0.0)  # Is test class
        
        return features
    
    def _extract_file_features(self, file) -> List[float]:
        """Extract features from a file for ML training."""
        features = []
        
        # Basic metrics
        functions = getattr(file, 'functions', [])
        classes = getattr(file, 'classes', [])
        imports = getattr(file, 'imports', [])
        
        features.append(len(functions))  # Function count
        features.append(len(classes))  # Class count
        features.append(len(imports))  # Import count
        
        # File path features
        filepath = file.filepath
        features.append(len(filepath.split('/')))  # Directory depth
        features.append(1.0 if 'test' in filepath.lower() else 0.0)  # Is test file
        features.append(1.0 if '__init__' in filepath else 0.0)  # Is init file
        
        return features
    
    def _extract_complexity_features(self, function) -> List[float]:
        """Extract features specifically for complexity prediction."""
        features = []
        
        if hasattr(function, 'source'):
            source = function.source
            
            # Control flow indicators
            features.append(source.count('if'))
            features.append(source.count('elif'))
            features.append(source.count('else'))
            features.append(source.count('for'))
            features.append(source.count('while'))
            features.append(source.count('try'))
            features.append(source.count('except'))
            features.append(source.count('and'))
            features.append(source.count('or'))
            features.append(source.count('not'))
            
            # Nesting indicators
            features.append(source.count('    '))  # Indentation count (rough nesting)
            features.append(len(source.splitlines()))  # Line count
            
        else:
            features.extend([0.0] * 12)
        
        # Function signature complexity
        features.append(len(getattr(function, 'parameters', [])))
        features.append(1.0 if getattr(function, 'return_type', None) else 0.0)
        
        return features
    
    def _extract_quality_features(self, function) -> List[float]:
        """Extract features specifically for quality assessment."""
        features = []
        
        # Documentation features
        features.append(1.0 if getattr(function, 'docstring', None) else 0.0)
        features.append(1.0 if getattr(function, 'return_type', None) else 0.0)
        
        # Complexity features
        features.append(getattr(function, 'complexity', 1))
        
        if hasattr(function, 'source'):
            source = function.source
            
            # Code quality indicators
            features.append(1.0 if 'TODO' in source or 'FIXME' in source else 0.0)
            features.append(len([line for line in source.splitlines() if line.strip().startswith('#')]))  # Comment lines
            features.append(source.count('assert'))  # Assertion count
            features.append(source.count('raise'))  # Exception raising
            
            # Magic numbers (simplified detection)
            import re
            magic_numbers = len(re.findall(r'\b\d{2,}\b', source))
            features.append(magic_numbers)
            
            # Line length variance (code style indicator)
            lines = source.splitlines()
            if lines:
                avg_line_length = sum(len(line) for line in lines) / len(lines)
                features.append(avg_line_length)
            else:
                features.append(0.0)
        else:
            features.extend([0.0] * 7)
        
        return features
    
    def _generate_function_labels(self, function) -> List[float]:
        """Generate labels for function analysis."""
        labels = []
        
        # Complexity label
        labels.append(getattr(function, 'complexity', 1))
        
        # Quality score (0-1)
        quality_score = self._calculate_quality_score(function)
        labels.append(quality_score)
        
        # Maintainability score (0-1)
        maintainability_score = self._calculate_maintainability_score(function)
        labels.append(maintainability_score)
        
        return labels
    
    def _generate_complexity_label(self, function) -> str:
        """Generate complexity label for classification."""
        complexity = getattr(function, 'complexity', 1)
        
        if complexity <= 5:
            return 'low'
        elif complexity <= 10:
            return 'medium'
        else:
            return 'high'
    
    def _generate_quality_label(self, function) -> str:
        """Generate quality label for classification."""
        score = self._calculate_quality_score(function)
        
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_maintainability_label(self, function) -> str:
        """Generate maintainability label for classification."""
        score = self._calculate_maintainability_score(function)
        
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_refactoring_label(self, function) -> List[int]:
        """Generate refactoring suggestions as multi-label."""
        labels = [0, 0, 0, 0]  # [extract_method, reduce_complexity, improve_naming, add_documentation]
        
        # Extract method suggestion
        if hasattr(function, 'source') and len(function.source.splitlines()) > 50:
            labels[0] = 1
        
        # Reduce complexity suggestion
        if getattr(function, 'complexity', 1) > 10:
            labels[1] = 1
        
        # Improve naming suggestion
        if len(function.name) < 3 or function.name.count('_') == 0:
            labels[2] = 1
        
        # Add documentation suggestion
        if not getattr(function, 'docstring', None):
            labels[3] = 1
        
        return labels
    
    def _calculate_quality_score(self, function) -> float:
        """Calculate quality score for a function."""
        score = 1.0
        
        # Deduct for missing docstring
        if not getattr(function, 'docstring', None):
            score -= 0.2
        
        # Deduct for missing type hints
        if not getattr(function, 'return_type', None):
            score -= 0.1
        
        # Deduct for high complexity
        complexity = getattr(function, 'complexity', 1)
        if complexity > 10:
            score -= 0.3
        elif complexity > 5:
            score -= 0.1
        
        # Deduct for long functions
        if hasattr(function, 'source'):
            lines = len(function.source.splitlines())
            if lines > 100:
                score -= 0.3
            elif lines > 50:
                score -= 0.1
        
        return max(0.0, score)
    
    def _calculate_maintainability_score(self, function) -> float:
        """Calculate maintainability score for a function."""
        score = 1.0
        
        # Factor in complexity
        complexity = getattr(function, 'complexity', 1)
        score -= min(0.5, complexity * 0.05)
        
        # Factor in documentation
        if getattr(function, 'docstring', None):
            score += 0.1
        
        # Factor in naming
        if len(function.name) >= 5 and '_' in function.name:
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _calculate_similarity(self, func1, func2) -> float:
        """Calculate similarity between two functions."""
        # Simple similarity based on feature comparison
        features1 = self._extract_function_features(func1)
        features2 = self._extract_function_features(func2)
        
        if len(features1) != len(features2):
            return 0.0
        
        # Euclidean distance normalized
        distance = sum((f1 - f2) ** 2 for f1, f2 in zip(features1, features2)) ** 0.5
        max_distance = (len(features1) ** 0.5) * 100  # Rough normalization
        
        similarity = max(0.0, 1.0 - (distance / max_distance))
        return similarity
    
    def _generate_sample_id(self, obj) -> str:
        """Generate unique ID for a sample."""
        identifier = f"{obj.filepath}::{obj.name}"
        return hashlib.md5(identifier.encode()).hexdigest()[:8]
    
    def _get_function_feature_names(self) -> List[str]:
        """Get names of function features."""
        return [
            'parameter_count', 'complexity', 'has_docstring', 'has_return_type',
            'lines_of_code', 'character_count', 'if_count', 'for_count',
            'while_count', 'try_count', 'nested_functions', 'nested_classes',
            'name_length', 'is_private', 'is_test', 'underscore_count', 'usage_count'
        ]
    
    def _generate_metadata(self, codebase) -> Dict[str, Any]:
        """Generate metadata for the training data."""
        if hasattr(codebase, 'files'):
            return {
                'total_files': len(codebase.files),
                'total_functions': len(codebase.functions),
                'total_classes': len(codebase.classes),
                'generation_timestamp': __import__('time').time(),
                'data_source': 'graph_sitter'
            }
        else:
            return {
                'total_files': len(codebase),
                'generation_timestamp': __import__('time').time(),
                'data_source': 'ast_analysis'
            }
    
    def _create_function_dataset_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create function dataset from AST data."""
        dataset = {
            'description': 'Function analysis dataset from AST (limited features)',
            'samples': []
        }
        
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                sample = {
                    'id': hashlib.md5(f"{filepath}::{func.get('name', 'unknown')}".encode()).hexdigest()[:8],
                    'name': func.get('name', 'unknown'),
                    'file': filepath,
                    'features': [
                        len(func.get('parameters', [])),
                        func.get('complexity', 1),
                        1.0 if func.get('docstring') else 0.0,
                        func.get('lines_of_code', 0)
                    ],
                    'labels': [func.get('complexity', 1)]
                }
                dataset['samples'].append(sample)
        
        return dataset
    
    def _create_complexity_dataset_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create complexity dataset from AST data."""
        dataset = {
            'description': 'Complexity prediction from AST data',
            'samples': []
        }
        
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                sample = {
                    'id': hashlib.md5(f"{filepath}::{func.get('name', 'unknown')}".encode()).hexdigest()[:8],
                    'features': [
                        len(func.get('parameters', [])),
                        func.get('lines_of_code', 0),
                        1.0 if func.get('docstring') else 0.0
                    ],
                    'target': func.get('complexity', 1)
                }
                dataset['samples'].append(sample)
        
        return dataset
    
    def export_training_data(self, training_data: Dict[str, Any], output_path: str, format: str = 'json'):
        """Export training data to file."""
        try:
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(training_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Training data exported to {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            raise

