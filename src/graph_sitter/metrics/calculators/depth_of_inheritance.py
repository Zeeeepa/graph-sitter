"""Depth of Inheritance Calculator.

from collections import defaultdict, deque
from typing import TYPE_CHECKING, Optional, Dict, Any, Set, List

from ..core.base_calculator import BaseMetricsCalculator

from __future__ import annotations
from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.metrics.models.metrics_data import (

Calculates the Depth of Inheritance (DOI) metric which measures how deep
a class is in the inheritance hierarchy. This metric helps assess the
complexity of the inheritance structure and potential maintenance issues.

Key metrics:
- Depth of Inheritance: Number of superclasses in the inheritance chain
- Number of Children: Count of direct subclasses
- Inheritance Tree Analysis: Overall inheritance structure complexity
"""

if TYPE_CHECKING:
        FunctionMetrics,
        ClassMetrics,
        FileMetrics,
        CodebaseMetrics,
    )

class DepthOfInheritanceCalculator(BaseMetricsCalculator):
    """Calculator for Depth of Inheritance metrics."""
    
    @property
    def name(self) -> str:
        return "depth_of_inheritance"
    
    @property
    def description(self) -> str:
        return "Calculates depth of inheritance and inheritance tree complexity metrics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration options
        self.include_external_classes = self.config.get("include_external_classes", False)
        self.max_depth_threshold = self.config.get("max_depth_threshold", 10)
        self.analyze_multiple_inheritance = self.config.get("analyze_multiple_inheritance", True)
        
        # Cache for inheritance relationships
        self._inheritance_cache: Dict[str, Dict[str, Any]] = {}
        self._class_hierarchy: Dict[str, Set[str]] = defaultdict(set)  # parent -> children
        self._reverse_hierarchy: Dict[str, Set[str]] = defaultdict(set)  # child -> parents
    
    def _clear_cache(self) -> None:
        """Clear the inheritance cache."""
        self._inheritance_cache.clear()
        self._class_hierarchy.clear()
        self._reverse_hierarchy.clear()
    
    def _get_class_parents(self, class_def: Class) -> List[str]:
        """Get the parent classes of a class.
        
        Args:
            class_def: Class to analyze.
            
        Returns:
            List of parent class names.
        """
        parents = []
        
        try:
            # Try different ways to get parent classes
            if hasattr(class_def, 'parent_class_names') and class_def.parent_class_names:
                parents.extend(class_def.parent_class_names)
            elif hasattr(class_def, 'base_classes') and class_def.base_classes:
                for base_class in class_def.base_classes:
                    if hasattr(base_class, 'name'):
                        parents.append(base_class.name)
                    else:
                        parents.append(str(base_class))
            elif hasattr(class_def, 'superclasses') and class_def.superclasses:
                for superclass in class_def.superclasses:
                    if hasattr(superclass, 'name'):
                        parents.append(superclass.name)
                    else:
                        parents.append(str(superclass))
            
            # Filter out built-in classes if not including external classes
            if not self.include_external_classes:
                parents = [p for p in parents if not self._is_builtin_class(p)]
            
        except Exception as e:
            self.add_warning(f"Error getting parent classes for {class_def.name}: {str(e)}")
        
        return parents
    
    def _is_builtin_class(self, class_name: str) -> bool:
        """Check if a class name refers to a built-in class.
        
        Args:
            class_name: Name of the class to check.
            
        Returns:
            True if the class is a built-in.
        """
        # Common built-in classes across languages
        builtin_classes = {
            # Python
            "object", "type", "int", "float", "str", "list", "dict", "tuple", "set",
            "Exception", "BaseException", "ValueError", "TypeError", "AttributeError",
            
            # Java
            "Object", "String", "Integer", "Double", "Float", "Boolean", "Character",
            "Exception", "RuntimeException", "Throwable",
            
            # JavaScript/TypeScript
            "Object", "Array", "String", "Number", "Boolean", "Function", "Error",
            
            # C++
            "std::string", "std::vector", "std::map", "std::set", "std::exception",
        }
        
        return class_name in builtin_classes or class_name.startswith("std::")
    
    def _build_inheritance_hierarchy(self, classes: List[Class]) -> None:
        """Build the inheritance hierarchy from a list of classes.
        
        Args:
            classes: List of classes to analyze.
        """
        self._clear_cache()
        
        # First pass: collect all parent-child relationships
        for class_def in classes:
            class_name = class_def.name
            parents = self._get_class_parents(class_def)
            
            for parent in parents:
                self._class_hierarchy[parent].add(class_name)
                self._reverse_hierarchy[class_name].add(parent)
    
    def _calculate_depth_of_inheritance(self, class_name: str, visited: Optional[Set[str]] = None) -> int:
        """Calculate the depth of inheritance for a class.
        
        Args:
            class_name: Name of the class.
            visited: Set of visited classes to detect cycles.
            
        Returns:
            Depth of inheritance (0 for root classes).
        """
        if visited is None:
            visited = set()
        
        if class_name in visited:
            # Cycle detected
            self.add_warning(f"Inheritance cycle detected involving class {class_name}")
            return 0
        
        if class_name in self._inheritance_cache:
            return self._inheritance_cache[class_name].get("depth", 0)
        
        visited.add(class_name)
        
        parents = self._reverse_hierarchy.get(class_name, set())
        if not parents:
            # Root class
            depth = 0
        else:
            # Calculate maximum depth from all parents
            max_parent_depth = 0
            for parent in parents:
                parent_depth = self._calculate_depth_of_inheritance(parent, visited.copy())
                max_parent_depth = max(max_parent_depth, parent_depth)
            depth = max_parent_depth + 1
        
        # Cache the result
        if class_name not in self._inheritance_cache:
            self._inheritance_cache[class_name] = {}
        self._inheritance_cache[class_name]["depth"] = depth
        
        visited.remove(class_name)
        return depth
    
    def _calculate_number_of_children(self, class_name: str) -> int:
        """Calculate the number of direct children for a class.
        
        Args:
            class_name: Name of the class.
            
        Returns:
            Number of direct children.
        """
        return len(self._class_hierarchy.get(class_name, set()))
    
    def _calculate_total_descendants(self, class_name: str, visited: Optional[Set[str]] = None) -> int:
        """Calculate the total number of descendants for a class.
        
        Args:
            class_name: Name of the class.
            visited: Set of visited classes to detect cycles.
            
        Returns:
            Total number of descendants.
        """
        if visited is None:
            visited = set()
        
        if class_name in visited:
            return 0
        
        visited.add(class_name)
        
        children = self._class_hierarchy.get(class_name, set())
        total_descendants = len(children)
        
        for child in children:
            total_descendants += self._calculate_total_descendants(child, visited.copy())
        
        visited.remove(class_name)
        return total_descendants
    
    def _analyze_inheritance_complexity(self, classes: List[Class]) -> Dict[str, Any]:
        """Analyze the overall inheritance complexity.
        
        Args:
            classes: List of classes to analyze.
            
        Returns:
            Dictionary with complexity analysis.
        """
        if not classes:
            return {
                "total_classes": 0,
                "root_classes": 0,
                "leaf_classes": 0,
                "max_depth": 0,
                "average_depth": 0.0,
                "inheritance_tree_count": 0,
                "multiple_inheritance_classes": 0,
            }
        
        self._build_inheritance_hierarchy(classes)
        
        depths = []
        root_classes = 0
        leaf_classes = 0
        multiple_inheritance_classes = 0
        
        for class_def in classes:
            class_name = class_def.name
            
            # Calculate depth
            depth = self._calculate_depth_of_inheritance(class_name)
            depths.append(depth)
            
            # Check if root class (no parents)
            if not self._reverse_hierarchy.get(class_name):
                root_classes += 1
            
            # Check if leaf class (no children)
            if not self._class_hierarchy.get(class_name):
                leaf_classes += 1
            
            # Check for multiple inheritance
            if len(self._reverse_hierarchy.get(class_name, set())) > 1:
                multiple_inheritance_classes += 1
        
        # Calculate inheritance trees (connected components)
        inheritance_tree_count = self._count_inheritance_trees(classes)
        
        return {
            "total_classes": len(classes),
            "root_classes": root_classes,
            "leaf_classes": leaf_classes,
            "max_depth": max(depths) if depths else 0,
            "average_depth": sum(depths) / len(depths) if depths else 0.0,
            "inheritance_tree_count": inheritance_tree_count,
            "multiple_inheritance_classes": multiple_inheritance_classes,
        }
    
    def _count_inheritance_trees(self, classes: List[Class]) -> int:
        """Count the number of separate inheritance trees.
        
        Args:
            classes: List of classes to analyze.
            
        Returns:
            Number of inheritance trees.
        """
        visited = set()
        tree_count = 0
        
        for class_def in classes:
            class_name = class_def.name
            if class_name not in visited:
                # Start a new tree traversal
                self._traverse_inheritance_tree(class_name, visited)
                tree_count += 1
        
        return tree_count
    
    def _traverse_inheritance_tree(self, class_name: str, visited: Set[str]) -> None:
        """Traverse an inheritance tree and mark all connected classes as visited.
        
        Args:
            class_name: Starting class name.
            visited: Set of visited classes.
        """
        if class_name in visited:
            return
        
        visited.add(class_name)
        
        # Visit all parents
        for parent in self._reverse_hierarchy.get(class_name, set()):
            self._traverse_inheritance_tree(parent, visited)
        
        # Visit all children
        for child in self._class_hierarchy.get(class_name, set()):
            self._traverse_inheritance_tree(child, visited)
    
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Functions don't have inheritance metrics."""
        return existing_metrics
    
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate depth of inheritance metrics for a class."""
        if existing_metrics is None:
            return None
        
        try:
            # For individual class calculation, we need context of other classes
            # This is better handled at the file or codebase level
            # For now, calculate basic metrics
            
            parents = self._get_class_parents(class_def)
            existing_metrics.depth_of_inheritance = len(parents)  # Simple approximation
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating inheritance metrics for class {class_def.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate inheritance metrics for classes in a file."""
        if existing_metrics is None:
            return None
        
        try:
            # Get all classes in the file
            classes = []
            if hasattr(file, 'classes'):
                classes = list(file.classes)
            
            if not classes:
                return existing_metrics
            
            # Build inheritance hierarchy for classes in this file
            self._build_inheritance_hierarchy(classes)
            
            # Update class metrics with accurate inheritance information
            for class_metrics in existing_metrics.class_metrics:
                class_name = class_metrics.name
                
                # Calculate accurate depth of inheritance
                depth = self._calculate_depth_of_inheritance(class_name)
                class_metrics.depth_of_inheritance = depth
                
                # Calculate number of children
                num_children = self._calculate_number_of_children(class_name)
                class_metrics.number_of_children = num_children
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating inheritance metrics for file {getattr(file, 'path', 'unknown')}: {str(e)}")
            return existing_metrics
    
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate inheritance metrics for the entire codebase."""
        if existing_metrics is None:
            return None
        
        try:
            # Get all classes in the codebase
            all_classes = []
            if hasattr(codebase, 'classes'):
                all_classes = list(codebase.classes)
            
            if not all_classes:
                return existing_metrics
            
            # Analyze inheritance complexity
            complexity_analysis = self._analyze_inheritance_complexity(all_classes)
            
            # Store analysis results in codebase metrics
            # Note: The base CodebaseMetrics class might need to be extended
            # to include inheritance-specific metrics
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating inheritance metrics for codebase: {str(e)}")
            return existing_metrics
    
    def get_inheritance_analysis(self, classes: List[Class]) -> Dict[str, Any]:
        """Get detailed inheritance analysis for a set of classes.
        
        Args:
            classes: List of classes to analyze.
            
        Returns:
            Dictionary with detailed inheritance analysis.
        """
        analysis = self._analyze_inheritance_complexity(classes)
        
        # Add detailed class information
        class_details = {}
        for class_def in classes:
            class_name = class_def.name
            depth = self._calculate_depth_of_inheritance(class_name)
            children_count = self._calculate_number_of_children(class_name)
            total_descendants = self._calculate_total_descendants(class_name)
            parents = list(self._reverse_hierarchy.get(class_name, set()))
            
            class_details[class_name] = {
                "depth_of_inheritance": depth,
                "direct_children": children_count,
                "total_descendants": total_descendants,
                "parents": parents,
                "is_root": len(parents) == 0,
                "is_leaf": children_count == 0,
                "has_multiple_inheritance": len(parents) > 1,
            }
        
        analysis["class_details"] = class_details
        
        # Add quality indicators
        max_depth = analysis["max_depth"]
        avg_depth = analysis["average_depth"]
        
        if max_depth <= 3:
            analysis["depth_quality"] = "good"
        elif max_depth <= 6:
            analysis["depth_quality"] = "moderate"
        else:
            analysis["depth_quality"] = "poor"
        
        if avg_depth <= 2.0:
            analysis["average_depth_quality"] = "good"
        elif avg_depth <= 4.0:
            analysis["average_depth_quality"] = "moderate"
        else:
            analysis["average_depth_quality"] = "poor"
        
        return analysis
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator."""
        return {
            "type": "object",
            "properties": {
                "include_external_classes": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to include external/built-in classes in inheritance analysis"
                },
                "max_depth_threshold": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum inheritance depth before flagging as problematic"
                },
                "analyze_multiple_inheritance": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to analyze multiple inheritance patterns"
                }
            },
            "additionalProperties": False
        }
