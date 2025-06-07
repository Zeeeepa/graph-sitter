"""
Class Hierarchy Analysis

Provides comprehensive class hierarchy analysis capabilities using tree-sitter.
"""

from typing import Dict, List, Optional, Any, Union
from ..core.models import ClassMetrics
from ..core.tree_sitter_core import get_tree_sitter_core
import logging

logger = logging.getLogger(__name__)

def analyze_inheritance_chains(codebase) -> Dict[str, Any]:
    """Analyze inheritance chains in the codebase."""
    try:
        inheritance_graph = {}
        classes = getattr(codebase, 'classes', [])
        
        # Build inheritance graph
        for cls in classes:
            class_name = cls.name
            superclasses = getattr(cls, 'superclasses', [])
            inheritance_graph[class_name] = [sc.name if hasattr(sc, 'name') else str(sc) for sc in superclasses]
        
        # Find inheritance chains
        chains = find_inheritance_chains(inheritance_graph)
        deepest = find_deepest_inheritance(classes)
        abstract_classes = find_abstract_classes(classes, inheritance_graph)
        
        return {
            'inheritance_graph': inheritance_graph,
            'inheritance_chains': chains,
            'deepest_inheritance': deepest,
            'abstract_classes': abstract_classes,
            'total_classes': len(classes),
            'classes_with_inheritance': len([c for c in classes if getattr(c, 'superclasses', [])])
        }
    except Exception as e:
        logger.error(f"Error analyzing inheritance chains: {e}")
        return {}

def find_deepest_inheritance(classes: List) -> Optional[Dict[str, Any]]:
    """Find the class with the deepest inheritance chain."""
    try:
        max_depth = 0
        deepest_class = None
        
        for cls in classes:
            depth = calculate_inheritance_depth(cls)
            if depth > max_depth:
                max_depth = depth
                deepest_class = cls
        
        if deepest_class:
            return {
                'class_name': deepest_class.name,
                'depth': max_depth,
                'inheritance_chain': get_inheritance_chain(deepest_class)
            }
        return None
    except Exception as e:
        logger.error(f"Error finding deepest inheritance: {e}")
        return None

def find_inheritance_chains(inheritance_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Find all inheritance chains in the graph."""
    try:
        chains = []
        visited = set()
        
        for class_name in inheritance_graph:
            if class_name not in visited:
                chain = build_inheritance_chain(class_name, inheritance_graph, visited)
                if len(chain) > 1:  # Only include chains with actual inheritance
                    chains.append({
                        'chain': chain,
                        'length': len(chain),
                        'root_class': chain[0],
                        'leaf_class': chain[-1]
                    })
        
        return sorted(chains, key=lambda x: x['length'], reverse=True)
    except Exception as e:
        logger.error(f"Error finding inheritance chains: {e}")
        return []

def find_abstract_classes(classes: List, inheritance_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Find abstract classes (classes that are inherited but may not be instantiated)."""
    try:
        # Build reverse graph (who inherits from whom)
        reverse_graph = {}
        for child, parents in inheritance_graph.items():
            for parent in parents:
                if parent not in reverse_graph:
                    reverse_graph[parent] = []
                reverse_graph[parent].append(child)
        
        abstract_classes = []
        for cls in classes:
            class_name = cls.name
            if class_name in reverse_graph:  # Has children
                # Check if it has abstract methods or is likely abstract
                is_abstract = has_abstract_methods(cls)
                abstract_classes.append({
                    'class_name': class_name,
                    'children': reverse_graph[class_name],
                    'is_abstract': is_abstract,
                    'child_count': len(reverse_graph[class_name])
                })
        
        return sorted(abstract_classes, key=lambda x: x['child_count'], reverse=True)
    except Exception as e:
        logger.error(f"Error finding abstract classes: {e}")
        return []

def build_inheritance_tree(inheritance_graph: Dict[str, List[str]], root_class: Optional[str] = None) -> Dict[str, Any]:
    """Build a tree representation of the inheritance hierarchy."""
    try:
        if root_class is None:
            # Find root classes (classes with no parents)
            root_classes = [cls for cls, parents in inheritance_graph.items() if not parents]
            if not root_classes:
                return {}
            root_class = root_classes[0]  # Take the first root
        
        def build_subtree(class_name: str, visited: set) -> Dict[str, Any]:
            if class_name in visited:
                return {'name': class_name, 'children': [], 'circular': True}
            
            visited.add(class_name)
            children = []
            
            # Find all classes that inherit from this class
            for child, parents in inheritance_graph.items():
                if class_name in parents:
                    children.append(build_subtree(child, visited.copy()))
            
            return {
                'name': class_name,
                'children': children,
                'child_count': len(children)
            }
        
        return build_subtree(root_class, set())
    except Exception as e:
        logger.error(f"Error building inheritance tree: {e}")
        return {}

def get_class_relationships(cls) -> Dict[str, Any]:
    """Get detailed relationships for a specific class."""
    try:
        relationships = {
            'class_name': cls.name,
            'superclasses': [],
            'methods': [],
            'attributes': [],
            'inheritance_depth': 0
        }
        
        # Get superclasses
        if hasattr(cls, 'superclasses'):
            relationships['superclasses'] = [sc.name if hasattr(sc, 'name') else str(sc) for sc in cls.superclasses]
            relationships['inheritance_depth'] = len(relationships['superclasses'])
        
        # Get methods
        if hasattr(cls, 'methods'):
            relationships['methods'] = [method.name for method in cls.methods]
        
        # Get attributes
        if hasattr(cls, 'attributes'):
            relationships['attributes'] = [attr.name for attr in cls.attributes]
        
        return relationships
    except Exception as e:
        logger.error(f"Error getting class relationships: {e}")
        return {}

def detect_design_patterns(codebase) -> Dict[str, Any]:
    """Detect common design patterns in the codebase."""
    try:
        patterns = {
            'singleton': [],
            'factory': [],
            'observer': [],
            'decorator': [],
            'strategy': []
        }
        
        classes = getattr(codebase, 'classes', [])
        
        for cls in classes:
            # Check for Singleton pattern
            if has_singleton_methods(cls):
                patterns['singleton'].append({
                    'class_name': cls.name,
                    'confidence': 0.8
                })
            
            # Check for Factory pattern
            if has_factory_methods(cls):
                patterns['factory'].append({
                    'class_name': cls.name,
                    'confidence': 0.7
                })
            
            # Check for Observer pattern
            if has_observer_methods(cls):
                patterns['observer'].append({
                    'class_name': cls.name,
                    'confidence': 0.6
                })
            
            # Check for Decorator pattern
            if has_decorator_structure(cls):
                patterns['decorator'].append({
                    'class_name': cls.name,
                    'confidence': 0.7
                })
            
            # Check for Strategy pattern
            if has_strategy_structure(cls):
                patterns['strategy'].append({
                    'class_name': cls.name,
                    'confidence': 0.6
                })
        
        return patterns
    except Exception as e:
        logger.error(f"Error detecting design patterns: {e}")
        return {}

def has_singleton_methods(cls) -> bool:
    """Check if class has singleton pattern characteristics."""
    try:
        methods = getattr(cls, 'methods', [])
        method_names = [method.name for method in methods]
        
        # Look for singleton indicators
        singleton_indicators = ['getInstance', 'get_instance', '__new__']
        return any(indicator in method_names for indicator in singleton_indicators)
    except Exception:
        return False

def has_factory_methods(cls) -> bool:
    """Check if class has factory pattern characteristics."""
    try:
        methods = getattr(cls, 'methods', [])
        method_names = [method.name for method in methods]
        
        # Look for factory indicators
        factory_indicators = ['create', 'make', 'build', 'factory', 'get']
        return any(indicator in method_name.lower() for method_name in method_names for indicator in factory_indicators)
    except Exception:
        return False

def has_observer_methods(cls) -> bool:
    """Check if class has observer pattern characteristics."""
    try:
        methods = getattr(cls, 'methods', [])
        method_names = [method.name for method in methods]
        
        # Look for observer indicators
        observer_indicators = ['notify', 'update', 'subscribe', 'unsubscribe', 'addObserver', 'removeObserver']
        return any(indicator in method_name for method_name in method_names for indicator in observer_indicators)
    except Exception:
        return False

def has_decorator_structure(cls) -> bool:
    """Check if class has decorator pattern characteristics."""
    try:
        # Check if class wraps another object
        attributes = getattr(cls, 'attributes', [])
        attr_names = [attr.name for attr in attributes]
        
        # Look for wrapped object indicators
        wrapper_indicators = ['component', 'wrapped', 'target', 'delegate']
        return any(indicator in attr_name.lower() for attr_name in attr_names for indicator in wrapper_indicators)
    except Exception:
        return False

def has_strategy_structure(cls) -> bool:
    """Check if class has strategy pattern characteristics."""
    try:
        methods = getattr(cls, 'methods', [])
        method_names = [method.name for method in methods]
        
        # Look for strategy indicators
        strategy_indicators = ['execute', 'algorithm', 'strategy', 'perform']
        return any(indicator in method_name.lower() for method_name in method_names for indicator in strategy_indicators)
    except Exception:
        return False

def generate_hierarchy_report(codebase) -> str:
    """Generate a comprehensive hierarchy analysis report."""
    try:
        analysis = analyze_inheritance_chains(codebase)
        patterns = detect_design_patterns(codebase)
        
        report = []
        report.append("# Class Hierarchy Analysis Report")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total Classes: {analysis.get('total_classes', 0)}")
        report.append(f"- Classes with Inheritance: {analysis.get('classes_with_inheritance', 0)}")
        report.append(f"- Inheritance Chains: {len(analysis.get('inheritance_chains', []))}")
        report.append("")
        
        # Deepest inheritance
        deepest = analysis.get('deepest_inheritance')
        if deepest:
            report.append("## Deepest Inheritance")
            report.append(f"- Class: {deepest['class_name']}")
            report.append(f"- Depth: {deepest['depth']}")
            report.append("")
        
        # Design patterns
        report.append("## Design Patterns Detected")
        for pattern_name, instances in patterns.items():
            if instances:
                report.append(f"### {pattern_name.title()} Pattern")
                for instance in instances:
                    report.append(f"- {instance['class_name']} (confidence: {instance['confidence']})")
                report.append("")
        
        return "\n".join(report)
    except Exception as e:
        logger.error(f"Error generating hierarchy report: {e}")
        return "Error generating hierarchy report"

# Helper functions

def calculate_inheritance_depth(cls) -> int:
    """Calculate the inheritance depth of a class."""
    try:
        superclasses = getattr(cls, 'superclasses', [])
        return len(superclasses)
    except Exception:
        return 0

def get_inheritance_chain(cls) -> List[str]:
    """Get the full inheritance chain for a class."""
    try:
        chain = [cls.name]
        superclasses = getattr(cls, 'superclasses', [])
        for sc in superclasses:
            chain.append(sc.name if hasattr(sc, 'name') else str(sc))
        return chain
    except Exception:
        return [cls.name if hasattr(cls, 'name') else str(cls)]

def build_inheritance_chain(class_name: str, inheritance_graph: Dict[str, List[str]], visited: set) -> List[str]:
    """Build inheritance chain starting from a class."""
    try:
        if class_name in visited:
            return [class_name]
        
        visited.add(class_name)
        chain = [class_name]
        
        parents = inheritance_graph.get(class_name, [])
        for parent in parents:
            parent_chain = build_inheritance_chain(parent, inheritance_graph, visited.copy())
            chain.extend(parent_chain)
        
        return chain
    except Exception:
        return [class_name]

def has_abstract_methods(cls) -> bool:
    """Check if a class has abstract methods."""
    try:
        methods = getattr(cls, 'methods', [])
        for method in methods:
            # Check for abstract method indicators
            if hasattr(method, 'decorators'):
                decorators = [d.name if hasattr(d, 'name') else str(d) for d in method.decorators]
                if 'abstractmethod' in decorators:
                    return True
            
            # Check method body for abstract indicators
            if hasattr(method, 'source'):
                source = method.source.lower()
                if 'raise notimplementederror' in source or 'pass' in source:
                    return True
        
        return False
    except Exception:
        return False

