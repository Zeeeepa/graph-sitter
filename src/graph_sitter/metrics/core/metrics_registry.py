"""Registry for managing metrics calculators."""

from __future__ import annotations

from typing import Dict, List, Optional, Type, Any
import logging

from .base_calculator import BaseMetricsCalculator

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """Registry for managing and organizing metrics calculators.
    
    The registry allows for dynamic registration and discovery of metrics
    calculators, enabling a plugin-like architecture for extending the
    metrics system.
    """
    
    def __init__(self):
        """Initialize the metrics registry."""
        self._calculators: Dict[str, BaseMetricsCalculator] = {}
        self._calculator_classes: Dict[str, Type[BaseMetricsCalculator]] = {}
        self._categories: Dict[str, List[str]] = {
            "complexity": [],
            "size": [],
            "quality": [],
            "maintainability": [],
            "inheritance": [],
            "testing": [],
            "custom": []
        }
    
    def register_calculator(
        self, 
        calculator_class: Type[BaseMetricsCalculator],
        category: str = "custom",
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a metrics calculator.
        
        Args:
            calculator_class: The calculator class to register.
            category: Category for organizing calculators.
            config: Optional configuration for the calculator instance.
        """
        try:
            # Create an instance to get the name
            temp_instance = calculator_class(config)
            name = temp_instance.name
            
            # Store the class and create instance
            self._calculator_classes[name] = calculator_class
            self._calculators[name] = calculator_class(config)
            
            # Add to category
            if category not in self._categories:
                self._categories[category] = []
            if name not in self._categories[category]:
                self._categories[category].append(name)
            
            logger.info(f"Registered metrics calculator: {name} in category: {category}")
            
        except Exception as e:
            logger.error(f"Failed to register calculator {calculator_class.__name__}: {str(e)}")
            raise
    
    def unregister_calculator(self, name: str) -> None:
        """Unregister a metrics calculator.
        
        Args:
            name: Name of the calculator to unregister.
        """
        if name in self._calculators:
            del self._calculators[name]
            del self._calculator_classes[name]
            
            # Remove from categories
            for category_calculators in self._categories.values():
                if name in category_calculators:
                    category_calculators.remove(name)
            
            logger.info(f"Unregistered metrics calculator: {name}")
        else:
            logger.warning(f"Calculator {name} not found in registry")
    
    def get_calculator(self, name: str) -> Optional[BaseMetricsCalculator]:
        """Get a calculator instance by name.
        
        Args:
            name: Name of the calculator.
            
        Returns:
            Calculator instance or None if not found.
        """
        return self._calculators.get(name)
    
    def get_calculators_by_category(self, category: str) -> List[BaseMetricsCalculator]:
        """Get all calculators in a specific category.
        
        Args:
            category: Category name.
            
        Returns:
            List of calculator instances in the category.
        """
        if category not in self._categories:
            return []
        
        return [
            self._calculators[name] 
            for name in self._categories[category] 
            if name in self._calculators
        ]
    
    def get_all_calculators(self) -> List[BaseMetricsCalculator]:
        """Get all registered calculators.
        
        Returns:
            List of all calculator instances.
        """
        return list(self._calculators.values())
    
    def get_calculator_names(self) -> List[str]:
        """Get names of all registered calculators.
        
        Returns:
            List of calculator names.
        """
        return list(self._calculators.keys())
    
    def get_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names.
        """
        return list(self._categories.keys())
    
    def get_calculators_for_language(self, language: str) -> List[BaseMetricsCalculator]:
        """Get calculators that support a specific language.
        
        Args:
            language: Programming language name.
            
        Returns:
            List of calculators that support the language.
        """
        return [
            calculator for calculator in self._calculators.values()
            if calculator.supports_language(language)
        ]
    
    def create_calculator_instance(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseMetricsCalculator]:
        """Create a new instance of a calculator with custom configuration.
        
        Args:
            name: Name of the calculator.
            config: Configuration for the new instance.
            
        Returns:
            New calculator instance or None if not found.
        """
        if name not in self._calculator_classes:
            return None
        
        try:
            return self._calculator_classes[name](config)
        except Exception as e:
            logger.error(f"Failed to create calculator instance {name}: {str(e)}")
            return None
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the registry state.
        
        Returns:
            Dictionary with registry information.
        """
        info = {
            "total_calculators": len(self._calculators),
            "categories": {},
            "calculators": {}
        }
        
        # Category information
        for category, calculator_names in self._categories.items():
            info["categories"][category] = {
                "count": len(calculator_names),
                "calculators": calculator_names
            }
        
        # Calculator information
        for name, calculator in self._calculators.items():
            info["calculators"][name] = {
                "description": calculator.description,
                "version": calculator.version,
                "class": calculator.__class__.__name__
            }
        
        return info
    
    def validate_calculators(self) -> Dict[str, List[str]]:
        """Validate all registered calculators.
        
        Returns:
            Dictionary with validation results (errors and warnings).
        """
        results = {
            "errors": [],
            "warnings": []
        }
        
        for name, calculator in self._calculators.items():
            try:
                # Basic validation
                if not calculator.name:
                    results["errors"].append(f"Calculator {name} has empty name")
                
                if not calculator.description:
                    results["warnings"].append(f"Calculator {name} has empty description")
                
                if not calculator.version:
                    results["warnings"].append(f"Calculator {name} has empty version")
                
                # Check if calculator has errors from previous operations
                if calculator.errors:
                    results["warnings"].append(
                        f"Calculator {name} has {len(calculator.errors)} errors"
                    )
                
            except Exception as e:
                results["errors"].append(f"Error validating calculator {name}: {str(e)}")
        
        return results
    
    def clear_registry(self) -> None:
        """Clear all registered calculators."""
        self._calculators.clear()
        self._calculator_classes.clear()
        for category in self._categories:
            self._categories[category].clear()
        
        logger.info("Cleared metrics registry")


# Global registry instance
_global_registry = MetricsRegistry()


def get_global_registry() -> MetricsRegistry:
    """Get the global metrics registry instance.
    
    Returns:
        Global MetricsRegistry instance.
    """
    return _global_registry


def register_calculator(
    calculator_class: Type[BaseMetricsCalculator],
    category: str = "custom",
    config: Optional[Dict[str, Any]] = None
) -> None:
    """Register a calculator in the global registry.
    
    Args:
        calculator_class: The calculator class to register.
        category: Category for organizing calculators.
        config: Optional configuration for the calculator instance.
    """
    _global_registry.register_calculator(calculator_class, category, config)

