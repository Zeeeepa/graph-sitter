"""
Pattern Recognition Engine for Continuous Learning System

This module implements advanced pattern recognition algorithms for identifying
code patterns, implementation strategies, and optimization opportunities.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class


class PatternType(Enum):
    """Types of patterns that can be recognized."""
    DESIGN_PATTERN = "design_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    ERROR_PATTERN = "error_pattern"
    REFACTORING_PATTERN = "refactoring_pattern"
    TESTING_PATTERN = "testing_pattern"
    ARCHITECTURAL_PATTERN = "architectural_pattern"


@dataclass
class CodePattern:
    """Represents a recognized code pattern."""
    pattern_id: str
    pattern_type: PatternType
    confidence: float
    frequency: int
    description: str
    examples: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary representation."""
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type.value,
            'confidence': self.confidence,
            'frequency': self.frequency,
            'description': self.description,
            'examples': self.examples,
            'metadata': self.metadata
        }


class PatternRecognizer(ABC):
    """Abstract base class for pattern recognition algorithms."""
    
    @abstractmethod
    def recognize_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Recognize patterns in the given codebase."""
        pass
    
    @abstractmethod
    def get_pattern_confidence(self, pattern: CodePattern) -> float:
        """Calculate confidence score for a pattern."""
        pass


class DesignPatternRecognizer(PatternRecognizer):
    """Recognizes common design patterns in code."""
    
    def __init__(self):
        self.known_patterns = {
            'singleton': self._detect_singleton,
            'factory': self._detect_factory,
            'observer': self._detect_observer,
            'strategy': self._detect_strategy,
            'decorator': self._detect_decorator
        }
    
    def recognize_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Recognize design patterns in the codebase."""
        patterns = []
        
        for pattern_name, detector in self.known_patterns.items():
            detected = detector(codebase)
            patterns.extend(detected)
        
        return patterns
    
    def get_pattern_confidence(self, pattern: CodePattern) -> float:
        """Calculate confidence based on pattern characteristics."""
        base_confidence = pattern.confidence
        frequency_boost = min(pattern.frequency * 0.1, 0.3)
        return min(base_confidence + frequency_boost, 1.0)
    
    def _detect_singleton(self, codebase: Codebase) -> List[CodePattern]:
        """Detect singleton pattern implementations."""
        patterns = []
        
        for cls in codebase.classes:
            if self._is_singleton_class(cls):
                pattern = CodePattern(
                    pattern_id=f"singleton_{cls.name}",
                    pattern_type=PatternType.DESIGN_PATTERN,
                    confidence=0.8,
                    frequency=1,
                    description=f"Singleton pattern in class {cls.name}",
                    examples=[cls.name],
                    metadata={'class_name': cls.name, 'file_path': cls.file.filepath}
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_singleton_class(self, cls: Class) -> bool:
        """Check if a class implements singleton pattern."""
        # Look for private constructor and getInstance method
        has_private_constructor = any(
            method.name == '__init__' and method.visibility == 'private'
            for method in cls.methods
        )
        
        has_get_instance = any(
            'instance' in method.name.lower() and method.is_static
            for method in cls.methods
        )
        
        return has_private_constructor or has_get_instance
    
    def _detect_factory(self, codebase: Codebase) -> List[CodePattern]:
        """Detect factory pattern implementations."""
        patterns = []
        
        for cls in codebase.classes:
            if self._is_factory_class(cls):
                pattern = CodePattern(
                    pattern_id=f"factory_{cls.name}",
                    pattern_type=PatternType.DESIGN_PATTERN,
                    confidence=0.7,
                    frequency=1,
                    description=f"Factory pattern in class {cls.name}",
                    examples=[cls.name],
                    metadata={'class_name': cls.name, 'file_path': cls.file.filepath}
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_factory_class(self, cls: Class) -> bool:
        """Check if a class implements factory pattern."""
        factory_keywords = ['factory', 'create', 'build', 'make']
        
        return any(
            any(keyword in method.name.lower() for keyword in factory_keywords)
            for method in cls.methods
        )
    
    def _detect_observer(self, codebase: Codebase) -> List[CodePattern]:
        """Detect observer pattern implementations."""
        # Implementation for observer pattern detection
        return []
    
    def _detect_strategy(self, codebase: Codebase) -> List[CodePattern]:
        """Detect strategy pattern implementations."""
        # Implementation for strategy pattern detection
        return []
    
    def _detect_decorator(self, codebase: Codebase) -> List[CodePattern]:
        """Detect decorator pattern implementations."""
        # Implementation for decorator pattern detection
        return []


class PerformancePatternRecognizer(PatternRecognizer):
    """Recognizes performance-related patterns in code."""
    
    def recognize_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Recognize performance patterns in the codebase."""
        patterns = []
        
        # Detect caching patterns
        patterns.extend(self._detect_caching_patterns(codebase))
        
        # Detect lazy loading patterns
        patterns.extend(self._detect_lazy_loading_patterns(codebase))
        
        # Detect optimization patterns
        patterns.extend(self._detect_optimization_patterns(codebase))
        
        return patterns
    
    def get_pattern_confidence(self, pattern: CodePattern) -> float:
        """Calculate confidence for performance patterns."""
        return pattern.confidence
    
    def _detect_caching_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Detect caching implementations."""
        patterns = []
        cache_keywords = ['cache', 'memoize', 'memo', 'lru']
        
        for func in codebase.functions:
            if any(keyword in func.name.lower() for keyword in cache_keywords):
                pattern = CodePattern(
                    pattern_id=f"cache_{func.name}",
                    pattern_type=PatternType.PERFORMANCE_PATTERN,
                    confidence=0.6,
                    frequency=1,
                    description=f"Caching pattern in function {func.name}",
                    examples=[func.name],
                    metadata={'function_name': func.name, 'file_path': func.file.filepath}
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_lazy_loading_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Detect lazy loading implementations."""
        # Implementation for lazy loading pattern detection
        return []
    
    def _detect_optimization_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Detect general optimization patterns."""
        # Implementation for optimization pattern detection
        return []


class PatternEngine:
    """Main pattern recognition engine that coordinates multiple recognizers."""
    
    def __init__(self):
        self.recognizers = [
            DesignPatternRecognizer(),
            PerformancePatternRecognizer()
        ]
        self.pattern_cache = {}
        self.learning_history = []
    
    def identify_patterns(self, codebase: Codebase) -> List[CodePattern]:
        """Identify all patterns in the given codebase."""
        codebase_id = self._get_codebase_id(codebase)
        
        # Check cache first
        if codebase_id in self.pattern_cache:
            return self.pattern_cache[codebase_id]
        
        all_patterns = []
        
        for recognizer in self.recognizers:
            patterns = recognizer.recognize_patterns(codebase)
            all_patterns.extend(patterns)
        
        # Remove duplicates and sort by confidence
        unique_patterns = self._deduplicate_patterns(all_patterns)
        sorted_patterns = sorted(unique_patterns, key=lambda p: p.confidence, reverse=True)
        
        # Cache results
        self.pattern_cache[codebase_id] = sorted_patterns
        
        return sorted_patterns
    
    def get_pattern_recommendations(self, codebase: Codebase) -> List[Dict[str, Any]]:
        """Get recommendations based on identified patterns."""
        patterns = self.identify_patterns(codebase)
        recommendations = []
        
        for pattern in patterns:
            if pattern.confidence > 0.7:
                recommendation = {
                    'type': 'pattern_application',
                    'pattern': pattern.to_dict(),
                    'suggestion': f"Consider applying {pattern.pattern_type.value} pattern",
                    'confidence': pattern.confidence,
                    'impact': self._estimate_impact(pattern)
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def update_pattern_confidence(self, pattern_id: str, feedback: float):
        """Update pattern confidence based on user feedback."""
        for patterns in self.pattern_cache.values():
            for pattern in patterns:
                if pattern.pattern_id == pattern_id:
                    # Update confidence using exponential moving average
                    pattern.confidence = 0.8 * pattern.confidence + 0.2 * feedback
                    
                    # Record learning event
                    self.learning_history.append({
                        'pattern_id': pattern_id,
                        'old_confidence': pattern.confidence,
                        'feedback': feedback,
                        'new_confidence': pattern.confidence,
                        'timestamp': np.datetime64('now')
                    })
    
    def _get_codebase_id(self, codebase: Codebase) -> str:
        """Generate a unique identifier for the codebase."""
        # Simple hash based on file count and symbol count
        file_count = len(list(codebase.files))
        symbol_count = len(list(codebase.symbols))
        return f"codebase_{file_count}_{symbol_count}"
    
    def _deduplicate_patterns(self, patterns: List[CodePattern]) -> List[CodePattern]:
        """Remove duplicate patterns based on pattern_id."""
        seen = set()
        unique_patterns = []
        
        for pattern in patterns:
            if pattern.pattern_id not in seen:
                seen.add(pattern.pattern_id)
                unique_patterns.append(pattern)
        
        return unique_patterns
    
    def _estimate_impact(self, pattern: CodePattern) -> str:
        """Estimate the impact of applying a pattern."""
        if pattern.pattern_type == PatternType.PERFORMANCE_PATTERN:
            return "High - Performance improvement expected"
        elif pattern.pattern_type == PatternType.DESIGN_PATTERN:
            return "Medium - Code maintainability improvement"
        else:
            return "Low - Minor improvement expected"
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the learning process."""
        return {
            'total_patterns_learned': len(self.learning_history),
            'cache_size': len(self.pattern_cache),
            'recognizers_count': len(self.recognizers),
            'average_confidence_improvement': self._calculate_avg_confidence_improvement()
        }
    
    def _calculate_avg_confidence_improvement(self) -> float:
        """Calculate average confidence improvement from feedback."""
        if not self.learning_history:
            return 0.0
        
        improvements = [
            event['new_confidence'] - event['old_confidence']
            for event in self.learning_history
        ]
        
        return sum(improvements) / len(improvements)

