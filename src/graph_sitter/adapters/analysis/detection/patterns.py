"""
Pattern Detection Module

Detects code patterns, anti-patterns, and best practices in codebases.
Identifies common design patterns and potential code smells.
"""

import ast
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects various code patterns and anti-patterns."""
    
    def __init__(self):
        # Design patterns to detect
        self.design_patterns = {
            'singleton': self._detect_singleton,
            'factory': self._detect_factory,
            'observer': self._detect_observer,
            'decorator': self._detect_decorator_pattern,
            'strategy': self._detect_strategy,
            'adapter': self._detect_adapter
        }
        
        # Anti-patterns to detect
        self.anti_patterns = {
            'god_class': self._detect_god_class,
            'long_method': self._detect_long_method,
            'duplicate_code': self._detect_duplicate_code,
            'large_class': self._detect_large_class,
            'feature_envy': self._detect_feature_envy,
            'data_class': self._detect_data_class,
            'refused_bequest': self._detect_refused_bequest
        }
        
        # Code smells to detect
        self.code_smells = {
            'magic_numbers': self._detect_magic_numbers,
            'long_parameter_list': self._detect_long_parameter_list,
            'deep_nesting': self._detect_deep_nesting,
            'complex_conditionals': self._detect_complex_conditionals,
            'primitive_obsession': self._detect_primitive_obsession,
            'inappropriate_intimacy': self._detect_inappropriate_intimacy
        }
    
    def detect_patterns(self, codebase) -> List[Dict[str, Any]]:
        """Detect all patterns in the codebase."""
        patterns = []
        
        try:
            if hasattr(codebase, 'files'):
                patterns.extend(self._detect_patterns_graph_sitter(codebase))
            else:
                patterns.extend(self._detect_patterns_ast(codebase))
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
        
        return patterns
    
    def _detect_patterns_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Detect patterns using graph-sitter."""
        patterns = []
        
        # Detect design patterns
        for pattern_name, detector in self.design_patterns.items():
            try:
                detected = detector(codebase)
                for item in detected:
                    patterns.append({
                        'type': 'design_pattern',
                        'pattern': pattern_name,
                        'severity': 'info',
                        'confidence': item.get('confidence', 0.5),
                        **item
                    })
            except Exception as e:
                logger.warning(f"Failed to detect {pattern_name}: {e}")
        
        # Detect anti-patterns
        for pattern_name, detector in self.anti_patterns.items():
            try:
                detected = detector(codebase)
                for item in detected:
                    patterns.append({
                        'type': 'anti_pattern',
                        'pattern': pattern_name,
                        'severity': item.get('severity', 'major'),
                        'confidence': item.get('confidence', 0.7),
                        **item
                    })
            except Exception as e:
                logger.warning(f"Failed to detect {pattern_name}: {e}")
        
        # Detect code smells
        for smell_name, detector in self.code_smells.items():
            try:
                detected = detector(codebase)
                for item in detected:
                    patterns.append({
                        'type': 'code_smell',
                        'pattern': smell_name,
                        'severity': item.get('severity', 'minor'),
                        'confidence': item.get('confidence', 0.8),
                        **item
                    })
            except Exception as e:
                logger.warning(f"Failed to detect {smell_name}: {e}")
        
        return patterns
    
    def _detect_patterns_ast(self, file_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect patterns using AST data."""
        patterns = []
        
        for filepath, analysis in file_analyses.items():
            # Detect patterns in functions
            for func in analysis.get('functions', []):
                patterns.extend(self._analyze_function_patterns(func, filepath))
            
            # Detect patterns in classes
            for cls in analysis.get('classes', []):
                patterns.extend(self._analyze_class_patterns(cls, filepath))
        
        return patterns
    
    def _analyze_function_patterns(self, func: Dict[str, Any], filepath: str) -> List[Dict[str, Any]]:
        """Analyze patterns in a single function."""
        patterns = []
        
        # Long method detection
        lines = func.get('lines_of_code', 0)
        if lines > 50:
            patterns.append({
                'type': 'anti_pattern',
                'pattern': 'long_method',
                'severity': 'major' if lines > 100 else 'minor',
                'confidence': 0.9,
                'message': f"Method '{func['name']}' is {lines} lines long",
                'file': filepath,
                'line': func.get('line_start', 0),
                'function': func['name']
            })
        
        # Long parameter list detection
        param_count = len(func.get('parameters', []))
        if param_count > 5:
            patterns.append({
                'type': 'code_smell',
                'pattern': 'long_parameter_list',
                'severity': 'minor',
                'confidence': 0.8,
                'message': f"Method '{func['name']}' has {param_count} parameters",
                'file': filepath,
                'line': func.get('line_start', 0),
                'function': func['name']
            })
        
        # High complexity detection
        complexity = func.get('complexity', 1)
        if complexity > 10:
            patterns.append({
                'type': 'code_smell',
                'pattern': 'complex_method',
                'severity': 'major' if complexity > 20 else 'minor',
                'confidence': 0.9,
                'message': f"Method '{func['name']}' has high cyclomatic complexity ({complexity})",
                'file': filepath,
                'line': func.get('line_start', 0),
                'function': func['name']
            })
        
        return patterns
    
    def _analyze_class_patterns(self, cls: Dict[str, Any], filepath: str) -> List[Dict[str, Any]]:
        """Analyze patterns in a single class."""
        patterns = []
        
        # Large class detection
        lines = cls.get('lines_of_code', 0)
        method_count = len(cls.get('methods', []))
        
        if lines > 500 or method_count > 20:
            patterns.append({
                'type': 'anti_pattern',
                'pattern': 'large_class',
                'severity': 'major',
                'confidence': 0.8,
                'message': f"Class '{cls['name']}' is large ({lines} lines, {method_count} methods)",
                'file': filepath,
                'line': cls.get('line_start', 0),
                'class': cls['name']
            })
        
        # Data class detection (simple heuristic)
        attribute_count = len(cls.get('attributes', []))
        if method_count <= 3 and attribute_count > 5:
            patterns.append({
                'type': 'code_smell',
                'pattern': 'data_class',
                'severity': 'minor',
                'confidence': 0.6,
                'message': f"Class '{cls['name']}' appears to be a data class",
                'file': filepath,
                'line': cls.get('line_start', 0),
                'class': cls['name']
            })
        
        return patterns
    
    # Design Pattern Detectors
    
    def _detect_singleton(self, codebase) -> List[Dict[str, Any]]:
        """Detect Singleton pattern."""
        singletons = []
        
        for cls in codebase.classes:
            if self._is_singleton_class(cls):
                singletons.append({
                    'message': f"Singleton pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.8
                })
        
        return singletons
    
    def _detect_factory(self, codebase) -> List[Dict[str, Any]]:
        """Detect Factory pattern."""
        factories = []
        
        for cls in codebase.classes:
            if self._is_factory_class(cls):
                factories.append({
                    'message': f"Factory pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.7
                })
        
        return factories
    
    def _detect_observer(self, codebase) -> List[Dict[str, Any]]:
        """Detect Observer pattern."""
        observers = []
        
        for cls in codebase.classes:
            if self._is_observer_class(cls):
                observers.append({
                    'message': f"Observer pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.6
                })
        
        return observers
    
    def _detect_decorator_pattern(self, codebase) -> List[Dict[str, Any]]:
        """Detect Decorator pattern."""
        decorators = []
        
        for cls in codebase.classes:
            if self._is_decorator_class(cls):
                decorators.append({
                    'message': f"Decorator pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.7
                })
        
        return decorators
    
    def _detect_strategy(self, codebase) -> List[Dict[str, Any]]:
        """Detect Strategy pattern."""
        strategies = []
        
        for cls in codebase.classes:
            if self._is_strategy_class(cls):
                strategies.append({
                    'message': f"Strategy pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.6
                })
        
        return strategies
    
    def _detect_adapter(self, codebase) -> List[Dict[str, Any]]:
        """Detect Adapter pattern."""
        adapters = []
        
        for cls in codebase.classes:
            if self._is_adapter_class(cls):
                adapters.append({
                    'message': f"Adapter pattern detected in class '{cls.name}'",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'confidence': 0.7
                })
        
        return adapters
    
    # Anti-Pattern Detectors
    
    def _detect_god_class(self, codebase) -> List[Dict[str, Any]]:
        """Detect God Class anti-pattern."""
        god_classes = []
        
        for cls in codebase.classes:
            method_count = len(getattr(cls, 'methods', []))
            attribute_count = len(getattr(cls, 'attributes', []))
            
            # Heuristic: class with many methods and attributes
            if method_count > 30 or attribute_count > 20:
                god_classes.append({
                    'message': f"God class detected: '{cls.name}' ({method_count} methods, {attribute_count} attributes)",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'severity': 'critical',
                    'confidence': 0.8
                })
        
        return god_classes
    
    def _detect_long_method(self, codebase) -> List[Dict[str, Any]]:
        """Detect Long Method anti-pattern."""
        long_methods = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                lines = len(function.source.splitlines())
                if lines > 50:
                    severity = 'critical' if lines > 100 else 'major'
                    long_methods.append({
                        'message': f"Long method detected: '{function.name}' ({lines} lines)",
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'function': function.name,
                        'severity': severity,
                        'confidence': 0.9
                    })
        
        return long_methods
    
    def _detect_duplicate_code(self, codebase) -> List[Dict[str, Any]]:
        """Detect duplicate code."""
        duplicates = []
        
        # Simple duplicate detection based on function similarity
        function_hashes = defaultdict(list)
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                # Create a simple hash of the function structure
                func_hash = self._create_function_hash(function.source)
                function_hashes[func_hash].append(function)
        
        for func_hash, functions in function_hashes.items():
            if len(functions) > 1:
                duplicates.append({
                    'message': f"Potential duplicate code detected in {len(functions)} functions",
                    'functions': [f.name for f in functions],
                    'files': [f.filepath for f in functions],
                    'severity': 'major',
                    'confidence': 0.6
                })
        
        return duplicates
    
    def _detect_large_class(self, codebase) -> List[Dict[str, Any]]:
        """Detect Large Class anti-pattern."""
        large_classes = []
        
        for cls in codebase.classes:
            method_count = len(getattr(cls, 'methods', []))
            
            if method_count > 20:
                large_classes.append({
                    'message': f"Large class detected: '{cls.name}' ({method_count} methods)",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'severity': 'major',
                    'confidence': 0.8
                })
        
        return large_classes
    
    def _detect_feature_envy(self, codebase) -> List[Dict[str, Any]]:
        """Detect Feature Envy anti-pattern."""
        # This is a complex pattern that requires call graph analysis
        # Simplified implementation
        return []
    
    def _detect_data_class(self, codebase) -> List[Dict[str, Any]]:
        """Detect Data Class anti-pattern."""
        data_classes = []
        
        for cls in codebase.classes:
            methods = getattr(cls, 'methods', [])
            attributes = getattr(cls, 'attributes', [])
            
            # Heuristic: many attributes, few methods
            if len(attributes) > 5 and len(methods) <= 3:
                data_classes.append({
                    'message': f"Data class detected: '{cls.name}' ({len(attributes)} attributes, {len(methods)} methods)",
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'class': cls.name,
                    'severity': 'minor',
                    'confidence': 0.6
                })
        
        return data_classes
    
    def _detect_refused_bequest(self, codebase) -> List[Dict[str, Any]]:
        """Detect Refused Bequest anti-pattern."""
        # This requires inheritance analysis
        # Simplified implementation
        return []
    
    # Code Smell Detectors
    
    def _detect_magic_numbers(self, codebase) -> List[Dict[str, Any]]:
        """Detect magic numbers."""
        magic_numbers = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                numbers = re.findall(r'\b(?<![\w.])\d{2,}\b(?![\w.])', function.source)
                if numbers:
                    magic_numbers.append({
                        'message': f"Magic numbers detected in '{function.name}': {', '.join(set(numbers))}",
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'function': function.name,
                        'numbers': list(set(numbers)),
                        'severity': 'minor',
                        'confidence': 0.8
                    })
        
        return magic_numbers
    
    def _detect_long_parameter_list(self, codebase) -> List[Dict[str, Any]]:
        """Detect long parameter lists."""
        long_params = []
        
        for function in codebase.functions:
            params = getattr(function, 'parameters', [])
            if len(params) > 5:
                long_params.append({
                    'message': f"Long parameter list in '{function.name}': {len(params)} parameters",
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'function': function.name,
                    'parameter_count': len(params),
                    'severity': 'minor',
                    'confidence': 0.9
                })
        
        return long_params
    
    def _detect_deep_nesting(self, codebase) -> List[Dict[str, Any]]:
        """Detect deep nesting."""
        deep_nesting = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                max_depth = self._calculate_nesting_depth(function.source)
                if max_depth > 4:
                    deep_nesting.append({
                        'message': f"Deep nesting detected in '{function.name}': {max_depth} levels",
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'function': function.name,
                        'nesting_depth': max_depth,
                        'severity': 'major' if max_depth > 6 else 'minor',
                        'confidence': 0.8
                    })
        
        return deep_nesting
    
    def _detect_complex_conditionals(self, codebase) -> List[Dict[str, Any]]:
        """Detect complex conditional statements."""
        complex_conditionals = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                complexity = self._analyze_conditional_complexity(function.source)
                if complexity > 3:
                    complex_conditionals.append({
                        'message': f"Complex conditionals in '{function.name}': complexity {complexity}",
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'function': function.name,
                        'conditional_complexity': complexity,
                        'severity': 'minor',
                        'confidence': 0.7
                    })
        
        return complex_conditionals
    
    def _detect_primitive_obsession(self, codebase) -> List[Dict[str, Any]]:
        """Detect primitive obsession."""
        # This requires type analysis - simplified implementation
        return []
    
    def _detect_inappropriate_intimacy(self, codebase) -> List[Dict[str, Any]]:
        """Detect inappropriate intimacy between classes."""
        # This requires detailed class relationship analysis
        return []
    
    # Helper Methods
    
    def _is_singleton_class(self, cls) -> bool:
        """Check if class implements Singleton pattern."""
        methods = getattr(cls, 'methods', [])
        method_names = [m.name for m in methods]
        
        # Look for common singleton indicators
        return ('getInstance' in method_names or 
                'get_instance' in method_names or
                any('instance' in name.lower() for name in method_names))
    
    def _is_factory_class(self, cls) -> bool:
        """Check if class implements Factory pattern."""
        class_name = cls.name.lower()
        methods = getattr(cls, 'methods', [])
        method_names = [m.name for m in methods]
        
        return ('factory' in class_name or
                any('create' in name.lower() for name in method_names) or
                any('build' in name.lower() for name in method_names))
    
    def _is_observer_class(self, cls) -> bool:
        """Check if class implements Observer pattern."""
        methods = getattr(cls, 'methods', [])
        method_names = [m.name for m in methods]
        
        observer_methods = {'notify', 'update', 'observe', 'subscribe', 'unsubscribe'}
        return len(set(method_names) & observer_methods) >= 2
    
    def _is_decorator_class(self, cls) -> bool:
        """Check if class implements Decorator pattern."""
        class_name = cls.name.lower()
        return 'decorator' in class_name or 'wrapper' in class_name
    
    def _is_strategy_class(self, cls) -> bool:
        """Check if class implements Strategy pattern."""
        class_name = cls.name.lower()
        return 'strategy' in class_name or 'algorithm' in class_name
    
    def _is_adapter_class(self, cls) -> bool:
        """Check if class implements Adapter pattern."""
        class_name = cls.name.lower()
        return 'adapter' in class_name or 'wrapper' in class_name
    
    def _create_function_hash(self, source: str) -> str:
        """Create a simple hash of function structure for duplicate detection."""
        # Remove whitespace and comments for comparison
        normalized = re.sub(r'#.*$', '', source, flags=re.MULTILINE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return str(hash(normalized))
    
    def _calculate_nesting_depth(self, source: str) -> int:
        """Calculate maximum nesting depth in source code."""
        try:
            tree = ast.parse(source)
            max_depth = 0
            
            def visit_node(node, depth=0):
                nonlocal max_depth
                max_depth = max(max_depth, depth)
                
                if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    depth += 1
                
                for child in ast.iter_child_nodes(node):
                    visit_node(child, depth)
            
            visit_node(tree)
            return max_depth
        except:
            return 0
    
    def _analyze_conditional_complexity(self, source: str) -> int:
        """Analyze complexity of conditional statements."""
        try:
            tree = ast.parse(source)
            complexity = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.Compare):
                    complexity += len(node.ops)
            
            return complexity
        except:
            return 0

