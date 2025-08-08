"""
Serena Integration for Codebase

Provides integration methods to add Serena capabilities to the main Codebase class.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase

from .core import SerenaCore, SerenaConfig

logger = get_logger(__name__)


class SerenaIntegration:
    """
    Integration class that adds Serena capabilities to Codebase.
    
    This class provides all Serena methods that will be added to the Codebase class.
    """
    
    def __init__(self, codebase: 'Codebase'):
        self.codebase = codebase
        self._serena_core: Optional[SerenaCore] = None
        self._serena_enabled = True
    
    def _ensure_serena_initialized(self) -> Optional[SerenaCore]:
        """Ensure Serena is initialized and return the core instance."""
        if not self._serena_enabled:
            return None
        
        if self._serena_core is None:
            try:
                config = SerenaConfig()  # Use default config for now
                self._serena_core = SerenaCore(self.codebase, config)
                logger.info("Serena LSP integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Serena: {e}")
                self._serena_enabled = False
                return None
        
        return self._serena_core
    
    # Intelligence Methods
    def get_completions(self, file_path: str, line: int, character: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get code completions at the specified position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
            **kwargs: Additional completion options
        
        Returns:
            List of completion items with details
        
        Example:
            >>> completions = codebase.get_completions("src/main.py", 10, 5)
            >>> for comp in completions:
            ...     print(f"{comp['label']}: {comp['detail']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.get_completions(file_path, line, character, **kwargs)
        return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get hover information for symbol at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Hover information or None if not available
        
        Example:
            >>> hover = codebase.get_hover_info("src/main.py", 15, 10)
            >>> if hover:
            ...     print(f"Symbol: {hover['symbolName']}")
            ...     print(f"Type: {hover['symbolType']}")
            ...     print(f"Documentation: {hover['documentation']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.get_hover_info(file_path, line, character)
        return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get signature help for function call at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Signature help information or None if not available
        
        Example:
            >>> sig = codebase.get_signature_help("src/main.py", 20, 15)
            >>> if sig:
            ...     print(f"Function: {sig['functionName']}")
            ...     for i, param in enumerate(sig['parameters']):
            ...         active = " <-- ACTIVE" if i == sig['activeParameter'] else ""
            ...         print(f"  {param['name']}: {param['typeAnnotation']}{active}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.get_signature_help(file_path, line, character)
        return None
    
    # Refactoring Methods
    def rename_symbol(self, file_path: str, line: int, character: int, new_name: str, preview: bool = False) -> Dict[str, Any]:
        """
        Rename symbol at position across all files.
        
        Args:
            file_path: Path to the file containing the symbol
            line: Line number (0-based)
            character: Character position (0-based)
            new_name: New name for the symbol
            preview: Whether to return preview without applying changes
        
        Returns:
            Refactoring result with changes and conflicts
        
        Example:
            >>> # Preview rename operation
            >>> result = codebase.rename_symbol("src/main.py", 10, 5, "new_function_name", preview=True)
            >>> if result['success']:
            ...     print(f"Will rename in {len(result['changes'])} locations")
            ...     # Apply the rename
            ...     result = codebase.rename_symbol("src/main.py", 10, 5, "new_function_name")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.rename_symbol(file_path, line, character, new_name, preview)
        return {"success": False, "error": "Serena not available"}
    
    def extract_method(self, file_path: str, start_line: int, end_line: int, method_name: str, **kwargs) -> Dict[str, Any]:
        """
        Extract selected code into a new method.
        
        Args:
            file_path: Path to the file
            start_line: Start line of selection (0-based)
            end_line: End line of selection (0-based)
            method_name: Name for the new method
            **kwargs: Additional options (target_class, visibility, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        
        Example:
            >>> result = codebase.extract_method("src/main.py", 15, 25, "calculate_total")
            >>> if result['success']:
            ...     print("Method extracted successfully")
            ...     for change in result['changes']:
            ...         print(f"Modified: {change['file']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.extract_method(file_path, start_line, end_line, method_name, **kwargs)
        return {"success": False, "error": "Serena not available"}
    
    def extract_variable(self, file_path: str, line: int, character: int, variable_name: str, **kwargs) -> Dict[str, Any]:
        """
        Extract expression into a variable.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
            variable_name: Name for the new variable
            **kwargs: Additional options (scope, type_annotation, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        
        Example:
            >>> result = codebase.extract_variable("src/main.py", 20, 10, "temp_result")
            >>> if result['success']:
            ...     print("Variable extracted successfully")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.extract_variable(file_path, line, character, variable_name, **kwargs)
        return {"success": False, "error": "Serena not available"}
    
    # Code Actions Methods
    def get_code_actions(self, file_path: str, start_line: int, end_line: int, context: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get available code actions for the specified range.
        
        Args:
            file_path: Path to the file
            start_line: Start line of range (0-based)
            end_line: End line of range (0-based)
            context: Optional context information
        
        Returns:
            List of available code actions
        
        Example:
            >>> actions = codebase.get_code_actions("src/main.py", 10, 15)
            >>> for action in actions:
            ...     print(f"{action['title']}: {action['description']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.get_code_actions(file_path, start_line, end_line, context or [])
        return []
    
    def apply_code_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Apply a specific code action.
        
        Args:
            action_id: ID of the action to apply
            file_path: Path to the file
            **kwargs: Additional action parameters
        
        Returns:
            Result of applying the code action
        
        Example:
            >>> result = codebase.apply_code_action("add_missing_import", "src/main.py")
            >>> if result['success']:
            ...     print("Code action applied successfully")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.apply_code_action(action_id, file_path, **kwargs)
        return {"success": False, "error": "Serena not available"}
    
    def organize_imports(self, file_path: str, remove_unused: bool = True, sort_imports: bool = True) -> Dict[str, Any]:
        """
        Organize imports in the specified file.
        
        Args:
            file_path: Path to the file
            remove_unused: Whether to remove unused imports
            sort_imports: Whether to sort imports
        
        Returns:
            Result of import organization
        
        Example:
            >>> result = codebase.organize_imports("src/main.py")
            >>> if result['success']:
            ...     print("Imports organized successfully")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.organize_imports(file_path, remove_unused, sort_imports)
        return {"success": False, "error": "Serena not available"}
    
    # Generation Methods
    def generate_boilerplate(self, template: str, context: Dict[str, Any], target_file: str = None) -> Dict[str, Any]:
        """
        Generate boilerplate code from template.
        
        Args:
            template: Template name or pattern
            context: Context variables for template
            target_file: Optional target file path
        
        Returns:
            Generated code and metadata
        
        Example:
            >>> result = codebase.generate_boilerplate("class", {
            ...     "class_name": "MyClass",
            ...     "base_class": "BaseClass"
            ... })
            >>> if result['success']:
            ...     print(result['generated_code'])
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.generate_boilerplate(template, context, target_file)
        return {"success": False, "error": "Serena not available"}
    
    def generate_tests(self, target_function: str, test_types: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate tests for the specified function.
        
        Args:
            target_function: Name of the function to test
            test_types: Types of tests to generate (unit, integration, etc.)
            **kwargs: Additional generation options
        
        Returns:
            Generated test code and metadata
        
        Example:
            >>> result = codebase.generate_tests("calculate_total", ["unit", "edge_cases"])
            >>> if result['success']:
            ...     for test in result['generated_tests']:
            ...         print(test)
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.generate_tests(target_function, test_types or ["unit"], **kwargs)
        return {"success": False, "error": "Serena not available"}
    
    def generate_documentation(self, target: str, format: str = "docstring", **kwargs) -> Dict[str, Any]:
        """
        Generate documentation for the specified target.
        
        Args:
            target: Target symbol or file to document
            format: Documentation format (docstring, markdown, etc.)
            **kwargs: Additional generation options
        
        Returns:
            Generated documentation and metadata
        
        Example:
            >>> result = codebase.generate_documentation("MyClass.my_method")
            >>> if result['success']:
            ...     print(result['generated_docs'])
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.generate_documentation(target, format, **kwargs)
        return {"success": False, "error": "Serena not available"}
    
    # Search Methods
    def semantic_search(self, query: str, language: str = "natural", **kwargs) -> List[Dict[str, Any]]:
        """
        Perform semantic search across the codebase.
        
        Args:
            query: Search query (natural language or code pattern)
            language: Query language type (natural, code, regex)
            **kwargs: Additional search options
        
        Returns:
            List of search results with relevance scores
        
        Example:
            >>> results = codebase.semantic_search("functions that handle authentication")
            >>> for result in results:
            ...     print(f"{result['file']}:{result['line']} - {result['match']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.semantic_search(query, language, **kwargs)
        return []
    
    def find_code_patterns(self, pattern: str, suggest_improvements: bool = False) -> List[Dict[str, Any]]:
        """
        Find code patterns matching the specified pattern.
        
        Args:
            pattern: Code pattern to search for
            suggest_improvements: Whether to suggest improvements
        
        Returns:
            List of pattern matches with optional improvement suggestions
        
        Example:
            >>> results = codebase.find_code_patterns("for.*in.*range", suggest_improvements=True)
            >>> for result in results:
            ...     print(f"Found pattern in {result['file']}")
            ...     if result['improvements']:
            ...         print(f"Suggestion: {result['improvements'][0]}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.find_code_patterns(pattern, suggest_improvements)
        return []
    
    def find_similar_code(self, reference_code: str, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Find code similar to the reference code.
        
        Args:
            reference_code: Reference code to find similarities to
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            List of similar code blocks with similarity scores
        
        Example:
            >>> reference = "def calculate_total(items): return sum(item.price for item in items)"
            >>> results = codebase.find_similar_code(reference, 0.7)
            >>> for result in results:
            ...     print(f"Similar code in {result['file']} (similarity: {result['similarity']})")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.find_similar_code(reference_code, similarity_threshold)
        return []
    
    # Symbol Intelligence Methods
    def get_symbol_context(self, symbol: str, include_dependencies: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Get comprehensive context for a symbol.
        
        Args:
            symbol: Symbol name to analyze
            include_dependencies: Whether to include dependency information
            **kwargs: Additional context options
        
        Returns:
            Comprehensive symbol context and relationships
        
        Example:
            >>> context = codebase.get_symbol_context("MyClass")
            >>> print(f"Symbol type: {context['type']}")
            >>> print(f"Dependencies: {context['dependencies']}")
            >>> print(f"Usages: {context['usages']}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.get_symbol_context(symbol, include_dependencies, **kwargs)
        return {}
    
    def analyze_symbol_impact(self, symbol: str, change_type: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing a symbol.
        
        Args:
            symbol: Symbol name to analyze
            change_type: Type of change (rename, delete, modify, etc.)
        
        Returns:
            Impact analysis with affected files and recommendations
        
        Example:
            >>> impact = codebase.analyze_symbol_impact("calculate_total", "rename")
            >>> print(f"Impact level: {impact['impact_level']}")
            >>> print(f"Affected files: {impact['affected_files']}")
            >>> for rec in impact['recommendations']:
            ...     print(f"Recommendation: {rec}")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.analyze_symbol_impact(symbol, change_type)
        return {}
    
    # Real-time Methods
    def enable_realtime_analysis(self, watch_patterns: List[str] = None, auto_refresh: bool = True) -> bool:
        """
        Enable real-time analysis with file watching.
        
        Args:
            watch_patterns: File patterns to watch (e.g., ["*.py", "*.ts"])
            auto_refresh: Whether to automatically refresh analysis on changes
        
        Returns:
            True if real-time analysis was enabled successfully
        
        Example:
            >>> success = codebase.enable_realtime_analysis(["*.py", "*.ts"])
            >>> if success:
            ...     print("Real-time analysis enabled")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.enable_realtime_analysis(watch_patterns, auto_refresh)
        return False
    
    def disable_realtime_analysis(self) -> bool:
        """
        Disable real-time analysis.
        
        Returns:
            True if real-time analysis was disabled successfully
        
        Example:
            >>> success = codebase.disable_realtime_analysis()
            >>> if success:
            ...     print("Real-time analysis disabled")
        """
        serena = self._ensure_serena_initialized()
        if serena:
            return serena.disable_realtime_analysis()
        return False
    
    # Utility Methods
    def get_serena_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of Serena integration.
        
        Returns:
            Status information for all Serena capabilities
        
        Example:
            >>> status = codebase.get_serena_status()
            >>> print(f"Serena enabled: {status.get('enabled', False)}")
            >>> for capability, details in status.get('capability_details', {}).items():
            ...     print(f"{capability}: {details}")
        """
        if not self._serena_enabled:
            return {"enabled": False, "error": "Serena is disabled"}
        
        serena = self._ensure_serena_initialized()
        if serena:
            status = serena.get_status()
            status["enabled"] = True
            return status
        else:
            return {"enabled": False, "error": "Serena initialization failed"}
    
    def shutdown_serena(self) -> None:
        """
        Shutdown Serena integration and cleanup resources.
        
        Example:
            >>> codebase.shutdown_serena()
            >>> print("Serena integration shutdown")
        """
        if self._serena_core:
            self._serena_core.shutdown()
            self._serena_core = None
        self._serena_enabled = False


def add_serena_to_codebase(codebase_class):
    """
    Add Serena methods to the Codebase class.
    
    This function dynamically adds all Serena methods to the Codebase class
    so they can be called directly on codebase instances.
    """
    
    def _get_serena_integration(self) -> SerenaIntegration:
        """Get or create Serena integration instance."""
        if not hasattr(self, '_serena_integration'):
            self._serena_integration = SerenaIntegration(self)
        return self._serena_integration
    
    # Add the integration getter
    codebase_class._get_serena_integration = _get_serena_integration
    
    # Add all Serena methods to the Codebase class
    integration_methods = [
        'get_completions', 'get_hover_info', 'get_signature_help',
        'rename_symbol', 'extract_method', 'extract_variable',
        'get_code_actions', 'apply_code_action', 'organize_imports',
        'generate_boilerplate', 'generate_tests', 'generate_documentation',
        'semantic_search', 'find_code_patterns', 'find_similar_code',
        'get_symbol_context', 'analyze_symbol_impact',
        'enable_realtime_analysis', 'disable_realtime_analysis',
        'get_serena_status', 'shutdown_serena'
    ]
    
    for method_name in integration_methods:
        def create_method(name):
            def method(self, *args, **kwargs):
                integration = self._get_serena_integration()
                return getattr(integration, name)(*args, **kwargs)
            method.__name__ = name
            method.__doc__ = getattr(SerenaIntegration, name).__doc__
            return method
        
        setattr(codebase_class, method_name, create_method(method_name))
    
    logger.info("Serena methods added to Codebase class")

