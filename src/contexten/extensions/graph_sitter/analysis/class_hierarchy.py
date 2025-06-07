"""
Class Hierarchy Analysis Module

Analyzes class inheritance relationships, finds inheritance chains,
and provides insights into object-oriented design patterns.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.class_definition import Class
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    Class = Any


def analyze_inheritance_chains(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze inheritance chains and hierarchies in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with inheritance analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis = {
            "total_classes": 0,
            "classes_with_inheritance": 0,
            "inheritance_chains": [],
            "deepest_inheritance": None,
            "multiple_inheritance": [],
            "abstract_classes": [],
            "leaf_classes": [],
            "inheritance_tree": {}
        }
        
        classes = list(codebase.classes)
        analysis["total_classes"] = len(classes)
        
        inheritance_graph = defaultdict(list)  # child -> [parents]
        reverse_graph = defaultdict(list)      # parent -> [children]
        
        # Build inheritance graphs
        for cls in classes:
            if hasattr(cls, 'superclasses') and cls.superclasses:
                analysis["classes_with_inheritance"] += 1
                
                parent_names = [parent.name for parent in cls.superclasses]
                inheritance_graph[cls.name] = parent_names
                
                for parent_name in parent_names:
                    reverse_graph[parent_name].append(cls.name)
                
                # Check for multiple inheritance
                if len(parent_names) > 1:
                    analysis["multiple_inheritance"].append({
                        "class": cls.name,
                        "parents": parent_names,
                        "file": cls.file.filepath if hasattr(cls, 'file') else "unknown"
                    })
        
        # Find inheritance chains
        analysis["inheritance_chains"] = find_inheritance_chains(inheritance_graph)
        
        # Find deepest inheritance
        analysis["deepest_inheritance"] = find_deepest_inheritance(classes)
        
        # Find leaf classes (no children)
        all_parents = set(reverse_graph.keys())
        all_children = set(inheritance_graph.keys())
        analysis["leaf_classes"] = [
            {"class": cls.name, "file": cls.file.filepath if hasattr(cls, 'file') else "unknown"}
            for cls in classes
            if cls.name not in all_parents and cls.name in all_children
        ]
        
        # Find potential abstract classes (have children but no direct instantiation)
        analysis["abstract_classes"] = find_abstract_classes(classes, reverse_graph)
        
        # Build inheritance tree
        analysis["inheritance_tree"] = build_inheritance_tree(inheritance_graph, reverse_graph)
        
        return analysis
        
    except Exception as e:
        return {"error": f"Error analyzing inheritance chains: {str(e)}"}


def find_deepest_inheritance(classes: List[Class]) -> Optional[Dict[str, Any]]:
    """
    Find the class with the deepest inheritance chain.
    
    Args:
        classes: List of classes to analyze
        
    Returns:
        Dictionary with deepest inheritance information
    """
    try:
        deepest = None
        max_depth = 0
        
        for cls in classes:
            if hasattr(cls, 'superclasses'):
                depth = len(cls.superclasses)
                if depth > max_depth:
                    max_depth = depth
                    deepest = {
                        "class": cls.name,
                        "depth": depth,
                        "chain": [parent.name for parent in cls.superclasses],
                        "file": cls.file.filepath if hasattr(cls, 'file') else "unknown"
                    }
        
        return deepest
        
    except Exception as e:
        return {"error": f"Error finding deepest inheritance: {str(e)}"}


def find_inheritance_chains(inheritance_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Find all inheritance chains in the codebase.
    
    Args:
        inheritance_graph: Dictionary mapping child classes to parent classes
        
    Returns:
        List of inheritance chains
    """
    try:
        chains = []
        
        def build_chain(cls_name, current_chain):
            if cls_name in current_chain:
                # Circular inheritance detected
                return [{"error": f"Circular inheritance detected: {' -> '.join(current_chain + [cls_name])}"}]
            
            new_chain = current_chain + [cls_name]
            
            if cls_name not in inheritance_graph:
                # Leaf node - end of chain
                return [new_chain]
            
            all_chains = []
            for parent in inheritance_graph[cls_name]:
                parent_chains = build_chain(parent, new_chain)
                all_chains.extend(parent_chains)
            
            return all_chains
        
        # Find all leaf classes (classes that inherit but are not inherited from)
        all_parents = set()
        for parents in inheritance_graph.values():
            all_parents.update(parents)
        
        leaf_classes = [cls for cls in inheritance_graph.keys() if cls not in all_parents]
        
        # Build chains from each leaf class
        for leaf in leaf_classes:
            leaf_chains = build_chain(leaf, [])
            for chain in leaf_chains:
                if isinstance(chain, list) and len(chain) > 1:
                    chains.append({
                        "chain": chain,
                        "length": len(chain),
                        "leaf_class": leaf,
                        "root_class": chain[-1] if chain else None
                    })
        
        # Sort by chain length (longest first)
        chains.sort(key=lambda x: x.get("length", 0), reverse=True)
        
        return chains
        
    except Exception as e:
        return [{"error": f"Error finding inheritance chains: {str(e)}"}]


def find_abstract_classes(classes: List[Class], reverse_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Find classes that appear to be abstract (have children but may not be directly instantiated).
    
    Args:
        classes: List of classes to analyze
        reverse_graph: Dictionary mapping parent classes to child classes
        
    Returns:
        List of potential abstract classes
    """
    try:
        abstract_classes = []
        
        for cls in classes:
            # Check if class has children
            if cls.name in reverse_graph and reverse_graph[cls.name]:
                # Check for abstract indicators
                is_abstract = False
                abstract_indicators = []
                
                # Check for abstract methods (simplified detection)
                if hasattr(cls, 'methods'):
                    for method in cls.methods:
                        if hasattr(method, 'source'):
                            source = method.source.lower()
                            if 'raise notimplementederror' in source or 'pass' in source:
                                is_abstract = True
                                abstract_indicators.append(f"Abstract method: {method.name}")
                
                # Check for ABC inheritance or decorators
                if hasattr(cls, 'superclasses'):
                    for parent in cls.superclasses:
                        if 'abc' in parent.name.lower() or 'abstract' in parent.name.lower():
                            is_abstract = True
                            abstract_indicators.append(f"Inherits from abstract class: {parent.name}")
                
                if hasattr(cls, 'decorators'):
                    for decorator in cls.decorators:
                        if 'abstractmethod' in str(decorator) or 'abc' in str(decorator):
                            is_abstract = True
                            abstract_indicators.append(f"Has abstract decorator: {decorator}")
                
                # If it has children and abstract indicators, consider it abstract
                if is_abstract or len(reverse_graph[cls.name]) > 2:  # Many children might indicate abstract
                    abstract_classes.append({
                        "class": cls.name,
                        "children": reverse_graph[cls.name],
                        "child_count": len(reverse_graph[cls.name]),
                        "indicators": abstract_indicators,
                        "file": cls.file.filepath if hasattr(cls, 'file') else "unknown"
                    })
        
        return abstract_classes
        
    except Exception as e:
        return [{"error": f"Error finding abstract classes: {str(e)}"}]


def build_inheritance_tree(inheritance_graph: Dict[str, List[str]], 
                          reverse_graph: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Build a tree representation of the inheritance hierarchy.
    
    Args:
        inheritance_graph: Dictionary mapping child classes to parent classes
        reverse_graph: Dictionary mapping parent classes to child classes
        
    Returns:
        Dictionary representing the inheritance tree
    """
    try:
        # Find root classes (classes with no parents)
        all_children = set(inheritance_graph.keys())
        all_parents = set()
        for parents in inheritance_graph.values():
            all_parents.update(parents)
        
        root_classes = all_parents - all_children
        
        def build_subtree(class_name):
            subtree = {
                "name": class_name,
                "children": []
            }
            
            if class_name in reverse_graph:
                for child in reverse_graph[class_name]:
                    subtree["children"].append(build_subtree(child))
            
            return subtree
        
        tree = {
            "roots": [build_subtree(root) for root in root_classes],
            "orphaned_classes": list(all_children - all_parents)  # Classes that inherit but their parents aren't in the codebase
        }
        
        return tree
        
    except Exception as e:
        return {"error": f"Error building inheritance tree: {str(e)}"}


def get_class_relationships(cls: Class) -> Dict[str, Any]:
    """
    Get detailed relationship information for a specific class.
    
    Args:
        cls: The class to analyze
        
    Returns:
        Dictionary with class relationship details
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        relationships = {
            "class_name": cls.name,
            "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
            "parents": [],
            "children": [],
            "siblings": [],
            "methods": [],
            "attributes": [],
            "inheritance_depth": 0
        }
        
        # Get parent classes
        if hasattr(cls, 'superclasses'):
            relationships["parents"] = [
                {
                    "name": parent.name,
                    "file": parent.file.filepath if hasattr(parent, 'file') else "unknown"
                }
                for parent in cls.superclasses
            ]
            relationships["inheritance_depth"] = len(cls.superclasses)
        
        # Get child classes
        if hasattr(cls, 'subclasses'):
            relationships["children"] = [
                {
                    "name": child.name,
                    "file": child.file.filepath if hasattr(child, 'file') else "unknown"
                }
                for child in cls.subclasses
            ]
        
        # Get sibling classes (classes with same parents)
        if hasattr(cls, 'superclasses'):
            for parent in cls.superclasses:
                if hasattr(parent, 'subclasses'):
                    for sibling in parent.subclasses:
                        if sibling.name != cls.name:
                            relationships["siblings"].append({
                                "name": sibling.name,
                                "file": sibling.file.filepath if hasattr(sibling, 'file') else "unknown",
                                "common_parent": parent.name
                            })
        
        # Get methods
        if hasattr(cls, 'methods'):
            relationships["methods"] = [
                {
                    "name": method.name,
                    "parameters": [p.name for p in method.parameters] if hasattr(method, 'parameters') else [],
                    "is_abstract": 'raise notimplementederror' in method.source.lower() if hasattr(method, 'source') else False
                }
                for method in cls.methods
            ]
        
        # Get attributes
        if hasattr(cls, 'attributes'):
            relationships["attributes"] = [
                {
                    "name": attr.name,
                    "type": getattr(attr, 'type', 'unknown')
                }
                for attr in cls.attributes
            ]
        
        return relationships
        
    except Exception as e:
        return {"error": f"Error getting class relationships: {str(e)}"}


def detect_design_patterns(codebase: Codebase) -> Dict[str, Any]:
    """
    Detect common object-oriented design patterns in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with detected design patterns
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        patterns = {
            "singleton_pattern": [],
            "factory_pattern": [],
            "observer_pattern": [],
            "decorator_pattern": [],
            "strategy_pattern": []
        }
        
        classes = list(codebase.classes)
        
        for cls in classes:
            class_name = cls.name.lower()
            
            # Detect Singleton pattern
            if 'singleton' in class_name or has_singleton_methods(cls):
                patterns["singleton_pattern"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "confidence": "medium"
                })
            
            # Detect Factory pattern
            if 'factory' in class_name or has_factory_methods(cls):
                patterns["factory_pattern"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "confidence": "medium"
                })
            
            # Detect Observer pattern
            if 'observer' in class_name or has_observer_methods(cls):
                patterns["observer_pattern"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "confidence": "medium"
                })
            
            # Detect Decorator pattern
            if 'decorator' in class_name or has_decorator_structure(cls):
                patterns["decorator_pattern"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "confidence": "low"
                })
            
            # Detect Strategy pattern
            if 'strategy' in class_name or has_strategy_structure(cls):
                patterns["strategy_pattern"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "confidence": "low"
                })
        
        return patterns
        
    except Exception as e:
        return {"error": f"Error detecting design patterns: {str(e)}"}


def has_singleton_methods(cls: Class) -> bool:
    """Check if class has singleton-like methods."""
    if not hasattr(cls, 'methods'):
        return False
    
    method_names = [method.name.lower() for method in cls.methods]
    singleton_indicators = ['get_instance', 'instance', '__new__']
    
    return any(indicator in method_names for indicator in singleton_indicators)


def has_factory_methods(cls: Class) -> bool:
    """Check if class has factory-like methods."""
    if not hasattr(cls, 'methods'):
        return False
    
    method_names = [method.name.lower() for method in cls.methods]
    factory_indicators = ['create', 'build', 'make', 'get_instance']
    
    return any(indicator in ' '.join(method_names) for indicator in factory_indicators)


def has_observer_methods(cls: Class) -> bool:
    """Check if class has observer-like methods."""
    if not hasattr(cls, 'methods'):
        return False
    
    method_names = [method.name.lower() for method in cls.methods]
    observer_indicators = ['notify', 'update', 'subscribe', 'unsubscribe', 'add_observer', 'remove_observer']
    
    return any(indicator in method_names for indicator in observer_indicators)


def has_decorator_structure(cls: Class) -> bool:
    """Check if class has decorator-like structure."""
    if not hasattr(cls, 'methods') or not hasattr(cls, 'attributes'):
        return False
    
    # Look for wrapped object attribute
    attr_names = [attr.name.lower() for attr in cls.attributes]
    return any('wrapped' in attr or 'component' in attr for attr in attr_names)


def has_strategy_structure(cls: Class) -> bool:
    """Check if class has strategy-like structure."""
    if not hasattr(cls, 'methods'):
        return False
    
    method_names = [method.name.lower() for method in cls.methods]
    strategy_indicators = ['execute', 'algorithm', 'strategy', 'process']
    
    return any(indicator in method_names for indicator in strategy_indicators)


def generate_hierarchy_report(codebase: Codebase) -> str:
    """
    Generate a formatted report of class hierarchy analysis.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string report
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "❌ Graph-sitter not available for hierarchy analysis"
    
    try:
        analysis = analyze_inheritance_chains(codebase)
        patterns = detect_design_patterns(codebase)
        
        report = []
        report.append("🏗️ Class Hierarchy Analysis Report")
        report.append("=" * 50)
        
        if "error" not in analysis:
            report.append(f"📊 Total Classes: {analysis['total_classes']}")
            report.append(f"🔗 Classes with Inheritance: {analysis['classes_with_inheritance']}")
            report.append("")
            
            # Deepest inheritance
            if analysis["deepest_inheritance"]:
                deepest = analysis["deepest_inheritance"]
                report.append("🌳 Deepest Inheritance Chain:")
                report.append("-" * 30)
                report.append(f"  Class: {deepest['class']}")
                report.append(f"  Depth: {deepest['depth']}")
                report.append(f"  Chain: {' → '.join(deepest['chain'])}")
                report.append("")
            
            # Multiple inheritance
            if analysis["multiple_inheritance"]:
                report.append("🔀 Multiple Inheritance:")
                report.append("-" * 30)
                for item in analysis["multiple_inheritance"][:5]:
                    report.append(f"  • {item['class']} inherits from: {', '.join(item['parents'])}")
                report.append("")
            
            # Abstract classes
            if analysis["abstract_classes"]:
                report.append("🎭 Potential Abstract Classes:")
                report.append("-" * 30)
                for item in analysis["abstract_classes"][:5]:
                    report.append(f"  • {item['class']} ({item['child_count']} children)")
                report.append("")
        
        # Design patterns
        if "error" not in patterns:
            pattern_found = False
            for pattern_type, instances in patterns.items():
                if instances:
                    if not pattern_found:
                        report.append("🎨 Design Patterns Detected:")
                        report.append("-" * 30)
                        pattern_found = True
                    
                    pattern_name = pattern_type.replace('_', ' ').title()
                    report.append(f"  {pattern_name}:")
                    for instance in instances[:3]:
                        report.append(f"    • {instance['class']} (confidence: {instance['confidence']})")
            
            if not pattern_found:
                report.append("🎨 No obvious design patterns detected")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Error generating hierarchy report: {str(e)}"

