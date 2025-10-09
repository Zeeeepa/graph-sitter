"""Protocol definitions for graph-sitter analysis system.

This module defines Protocol interfaces (PEP 544) for all major components,
enabling structural typing, better testing, and flexibility in implementation.
"""

from typing import Any, Protocol, runtime_checkable

from analysis_utils import AnalysisError


@runtime_checkable
class GraphSitterAnalyzerProtocol(Protocol):
    """Protocol for graph-sitter based code analysis."""
    
    def get_codebase_overview(self) -> dict[str, Any]:
        """Get comprehensive overview of the codebase structure."""
        ...
    
    def get_file_details(self, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of a specific file."""
        ...
    
    def get_function_details(self, function_name: str, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of a specific function."""
        ...
    
    def get_class_details(self, class_name: str, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of a specific class."""
        ...
    
    def get_symbol_details(self, symbol_name: str) -> dict[str, Any]:
        """Get detailed analysis of a specific symbol (function/class/variable)."""
        ...
    
    def create_blast_radius_visualization(self, symbol_name: str) -> dict[str, Any]:
        """Create visualization showing impact of changing a symbol."""
        ...
    
    def create_call_trace_visualization(self, function_name: str) -> dict[str, Any]:
        """Create visualization showing function call relationships."""
        ...
    
    def create_dependency_trace_visualization(self, module_name: str) -> dict[str, Any]:
        """Create visualization showing module dependencies."""
        ...
    
    def find_dead_code(self) -> list[dict[str, Any]]:
        """Identify unused code that can potentially be removed."""
        ...


@runtime_checkable
class AutoGenLibResolverProtocol(Protocol):
    """Protocol for AI-powered error resolution."""
    
    def resolve_error(
        self,
        error: AnalysisError,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Resolve a single error using AI assistance.
        
        Returns:
            Dictionary containing:
                - fix_code: str - The generated fix
                - explanation: str - Explanation of the fix
                - confidence: float - Confidence score (0-1)
                - applied: bool - Whether fix was applied
        """
        ...
    
    def resolve_multiple_errors(
        self,
        errors: list[AnalysisError],
        max_fixes: int = 10
    ) -> list[dict[str, Any]]:
        """Resolve multiple errors in batch."""
        ...
    
    def get_error_context(
        self,
        error: AnalysisError,
        include_related_symbols: bool = True
    ) -> dict[str, Any]:
        """Get comprehensive context for an error."""
        ...
    
    def generate_fix_strategy(
        self,
        errors: list[AnalysisError]
    ) -> dict[str, Any]:
        """Generate comprehensive fix strategy for multiple errors."""
        ...


@runtime_checkable
class ToolIntegrationProtocol(Protocol):
    """Protocol for static analysis tool integration."""
    
    def analyze(self, target_path: str) -> list[AnalysisError]:
        """Run analysis on target path and return standardized errors."""
        ...
    
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        ...
    
    def is_available(self) -> bool:
        """Check if tool is installed and available."""
        ...
    
    def get_version(self) -> str:
        """Get tool version string."""
        ...
    
    def supports_auto_fix(self) -> bool:
        """Check if tool supports automatic fixing."""
        ...
    
    def apply_fixes(self, errors: list[AnalysisError]) -> dict[str, Any]:
        """Apply automatic fixes for fixable errors."""
        ...


@runtime_checkable
class DiagnosticsProviderProtocol(Protocol):
    """Protocol for unified diagnostics/error context provider."""
    
    def collect_diagnostics(
        self,
        target_path: str,
        include_lsp: bool = True,
        include_runtime: bool = False
    ) -> list[AnalysisError]:
        """Collect all diagnostics from various sources."""
        ...
    
    def get_enhanced_diagnostic(
        self,
        error: AnalysisError
    ) -> dict[str, Any]:
        """Enhance diagnostic with additional context."""
        ...
    
    def get_error_statistics(self) -> dict[str, Any]:
        """Get statistics about errors (by type, severity, file, etc.)."""
        ...
    
    def categorize_errors(
        self,
        errors: list[AnalysisError]
    ) -> dict[str, list[AnalysisError]]:
        """Categorize errors by type/severity/source."""
        ...
    
    def find_error_patterns(
        self,
        errors: list[AnalysisError]
    ) -> list[dict[str, Any]]:
        """Identify common error patterns."""
        ...


@runtime_checkable
class AnalysisOrchestratorProtocol(Protocol):
    """Protocol for coordinating multiple analysis tools."""
    
    def run_analysis(
        self,
        target_path: str,
        tools: list[str] | None = None,
        parallel: bool = True
    ) -> dict[str, Any]:
        """Run analysis with selected tools.
        
        Args:
            target_path: Path to analyze (file or directory)
            tools: List of tool names to run (None = all enabled)
            parallel: Whether to run tools in parallel
            
        Returns:
            Dictionary containing:
                - errors: list[AnalysisError]
                - statistics: dict
                - tool_results: dict[str, list[AnalysisError]]
                - duration: float
        """
        ...
    
    def get_available_tools(self) -> list[str]:
        """Get list of available analysis tools."""
        ...
    
    def register_tool(self, tool: ToolIntegrationProtocol) -> None:
        """Register a new analysis tool."""
        ...
    
    def enable_tool(self, tool_name: str) -> None:
        """Enable a specific tool."""
        ...
    
    def disable_tool(self, tool_name: str) -> None:
        """Disable a specific tool."""
        ...


# Type aliases for common structures
ErrorContext = dict[str, Any]
VisualizationResult = dict[str, Any]
AnalysisResult = dict[str, Any]
FixResult = dict[str, Any]

