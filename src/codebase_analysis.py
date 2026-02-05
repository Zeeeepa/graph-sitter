#!/usr/bin/env python3
"""Codebase Analysis - Consolidated Analysis and Backend Module

This module consolidates all codebase analysis functionality:
- GraphSitterAnalyzer (main analysis engine with 76 methods)
- Backend API models and request/response types
- Complexity calculations and metrics
- Visualization generation
- Entry point detection
- Dead code analysis

Consolidates:
1. graph_sitter_analysis.py - GraphSitterAnalyzer class
2. graph_sitter_backend.py - Backend models and utility functions
3. analysis.py - Additional analysis functionality  
4. analysisbig.py - Experimental/additional features (if salvageable)

Total: ~13,000+ lines consolidated with dead code removal

This file imports from the other consolidated adapters:
- autogenlib_adapter (AutoGen integration)
- lsp_adapter (LSP diagnostics)
- graph_sitter_tools_adapter (All tools)

Author: Graph-Sitter Consolidation
"""

import os
import logging
import math
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from collections import defaultdict, Counter

# Core Graph-Sitter imports
from graph_sitter import Codebase
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.assignment import Assignment
from graph_sitter.core.function_call import FunctionCall

# Import from consolidated adapters
from autogenlib_adapter import (
    get_ai_fix_context,
    get_autogenlib_enhanced_context,
    resolve_diagnostic_with_ai
)
from lsp_adapter import (
    EnhancedDiagnostic,
    RuntimeErrorCollector,
    LSPDiagnosticsManager
)
from graph_sitter_tools_adapter import GraphSitterTools

# External dependencies
import networkx as nx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# BACKEND API MODELS
# Consolidated from: graph_sitter_backend.py, analysis.py
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for codebase analysis."""
    codebase_path: str
    analysis_type: str = "full"
    include_visualization: bool = False
    include_dead_code: bool = False


class ErrorAnalysisResponse(BaseModel):
    """Response model for error analysis."""
    error_count: int
    errors_by_type: Dict[str, int]
    errors_by_file: Dict[str, int]
    critical_errors: List[Dict[str, Any]]
    recommendations: List[str]


class EntrypointAnalysisResponse(BaseModel):
    """Response model for entry point analysis."""
    entrypoint_functions: List[Dict[str, Any]]
    entrypoint_classes: List[Dict[str, Any]]
    entrypoint_files: List[str]
    entry_graph: Optional[Dict[str, Any]] = None


class TransformationRequest(BaseModel):
    """Request model for code transformation."""
    codebase_path: str
    transformation_type: str
    target_files: Optional[List[str]] = None
    parameters: Dict[str, Any] = {}


class VisualizationRequest(BaseModel):
    """Request model for visualization generation."""
    codebase_path: str
    visualization_type: str  # blast_radius, call_trace, dependency, etc.
    symbol_name: Optional[str] = None
    output_format: str = "html"


# ============================================================================
# UTILITY FUNCTIONS  
# Consolidated from: graph_sitter_backend.py, analysis.py
# ============================================================================

def clone_repository(repo_url: str, target_path: str) -> bool:
    """Clone a git repository for analysis.
    
    Args:
        repo_url: URL of the repository to clone
        target_path: Local path to clone to
        
    Returns:
        True if successful, False otherwise
    """
    # TODO: Move implementation from graph_sitter_backend.py/analysis.py
    pass


def calculate_doi(complexity: int, loc: int, changes: int) -> float:
    """Calculate Depth of Inheritance metric.
    
    Args:
        complexity: Cyclomatic complexity
        loc: Lines of code
        changes: Number of changes
        
    Returns:
        DOI score
    """
    # TODO: Move implementation from graph_sitter_backend.py/analysis.py
    pass


def get_operators_and_operands(source_code: str) -> Tuple[int, int]:
    """Extract operators and operands for Halstead metrics.
    
    Args:
        source_code: Source code to analyze
        
    Returns:
        Tuple of (unique_operators, unique_operands)
    """
    # TODO: Move implementation from graph_sitter_backend.py/analysis.py
    pass


def calculate_halstead_volume(operators: int, operands: int) -> float:
    """Calculate Halstead volume metric.
    
    Args:
        operators: Number of unique operators
        operands: Number of unique operands
        
    Returns:
        Halstead volume
    """
    # TODO: Move implementation from graph_sitter_backend.py/analysis.py
    pass


def cc_rank(complexity: int) -> str:
    """Rank cyclomatic complexity.
    
    Args:
        complexity: Cyclomatic complexity score
        
    Returns:
        Risk ranking (low, moderate, high, very_high)
    """
    if complexity <= 10:
        return "low"
    elif complexity <= 20:
        return "moderate"
    elif complexity <= 50:
        return "high"
    else:
        return "very_high"


# ============================================================================
# MAIN ANALYZER CLASS
# Consolidated from: graph_sitter_analysis.py
# ============================================================================

class GraphSitterAnalyzer:
    """
    Comprehensive analysis engine using all Graph-Sitter capabilities.
    
    Provides unified access to:
    - Codebase overview and summaries
    - Symbol, function, and class analysis
    - Complexity metrics and quality assessment
    - Visualization generation
    - Dead code detection
    - Documentation generation
    - Entry point identification
    
    This class consolidates the main GraphSitterAnalyzer from graph_sitter_analysis.py
    with 76 methods providing complete codebase analysis capabilities.
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize the analyzer with a Graph-Sitter codebase.
        
        Args:
            codebase: The Graph-Sitter Codebase instance to analyze
        """
        self.codebase = codebase
        self.tools = GraphSitterTools()
        self.logger = logging.getLogger(__name__)
        
        # Cache for analysis results
        self._overview_cache = None
        self._complexity_cache = {}
        self._dead_code_cache = None
    
    # ========================================================================
    # OVERVIEW AND SUMMARY METHODS
    # ========================================================================
    
    def get_codebase_overview(self) -> Dict[str, Any]:
        """Get comprehensive overview of the codebase.
        
        Returns:
            Dictionary with codebase statistics, structure, and quality metrics
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_file_details(self, filepath: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific file.
        
        Args:
            filepath: Path to the file to analyze
            
        Returns:
            Dictionary with file analysis
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_function_details(self, function_name: str, filepath: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific function.
        
        Args:
            function_name: Name of the function
            filepath: Path to file containing the function
            
        Returns:
            Dictionary with function analysis
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_class_details(self, class_name: str, filepath: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific class.
        
        Args:
            class_name: Name of the class
            filepath: Path to file containing the class
            
        Returns:
            Dictionary with class analysis
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_symbol_details(self, symbol_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed analysis of a symbol.
        
        Args:
            symbol_name: Name of the symbol
            filepath: Optional filepath to narrow search
            
        Returns:
            Dictionary with symbol analysis
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # VISUALIZATION METHODS
    # ========================================================================
    
    def create_blast_radius_visualization(self, symbol_name: str) -> str:
        """Create blast radius visualization for a symbol.
        
        Args:
            symbol_name: Name of the symbol to visualize
            
        Returns:
            Path to generated visualization
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def create_call_trace_visualization(self, function_name: str) -> str:
        """Create call trace visualization for a function.
        
        Args:
            function_name: Name of the function to trace
            
        Returns:
            Path to generated visualization
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def create_dependency_trace_visualization(self, symbol_name: str) -> str:
        """Create dependency trace visualization.
        
        Args:
            symbol_name: Name of the symbol
            
        Returns:
            Path to generated visualization
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def create_method_relationships_visualization(self, class_name: str) -> str:
        """Create method relationships visualization for a class.
        
        Args:
            class_name: Name of the class
            
        Returns:
            Path to generated visualization
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # FILE AND DIRECTORY OPERATIONS
    # ========================================================================
    
    def view_file_content(self, filepath: str, start_line: int = 1, end_line: Optional[int] = None) -> str:
        """View file content with line numbers.
        
        Args:
            filepath: Path to file
            start_line: Starting line number
            end_line: Ending line number
            
        Returns:
            Formatted file content
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def list_directory_contents(self, path: str = ".", max_depth: int = 3) -> Dict[str, Any]:
        """List directory contents with tree structure.
        
        Args:
            path: Directory path
            max_depth: Maximum depth to traverse
            
        Returns:
            Dictionary with directory structure
        """
        return self.tools.list_directory(self.codebase, path, max_depth)
    
    # ========================================================================
    # SYMBOL ANALYSIS AND REVELATION
    # ========================================================================
    
    def reveal_symbol_relationships(self, symbol_name: str, max_hops: int = 3) -> Dict[str, Any]:
        """Reveal symbol with import chain analysis.
        
        Args:
            symbol_name: Name of symbol to reveal
            max_hops: Maximum import hops
            
        Returns:
            Dictionary with symbol and relationships
        """
        return self.tools.reveal_symbol(self.codebase, symbol_name, max_hops=max_hops)
    
    def get_symbol_info_detailed(self, symbol_name: str) -> Dict[str, Any]:
        """Get detailed symbol information.
        
        Args:
            symbol_name: Name of the symbol
            
        Returns:
            Dictionary with symbol info
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_extended_symbol_context(self, symbol_name: str) -> str:
        """Get extended context for a symbol including related code.
        
        Args:
            symbol_name: Name of the symbol
            
        Returns:
            Extended context string
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # DOCUMENTATION GENERATION
    # ========================================================================
    
    def generate_docstrings_for_undocumented(self) -> List[Tuple[str, str]]:
        """Generate docstrings for undocumented functions and classes.
        
        Returns:
            List of (symbol_name, generated_docstring) tuples
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def generate_structured_docs(self) -> Dict[str, Any]:
        """Generate structured JSON documentation.
        
        Returns:
            Dictionary with structured docs
        """
        return self.tools.generate_json_documentation(self.codebase)
    
    def generate_mdx_documentation(self, output_dir: str = "docs") -> str:
        """Generate MDX documentation for entire codebase.
        
        Args:
            output_dir: Directory to output MDX files
            
        Returns:
            Path to generated documentation
        """
        return self.tools.generate_mdx_documentation(self.codebase, output_dir)
    
    # ========================================================================
    # DEAD CODE ANALYSIS
    # ========================================================================
    
    def find_dead_code(self) -> Dict[str, List[str]]:
        """Find dead code in the codebase.
        
        Returns:
            Dictionary mapping file paths to lists of dead code symbols
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        # This is one of the key features we'll use in the consolidation!
        pass
    
    # ========================================================================
    # COMPLEXITY AND QUALITY METRICS
    # ========================================================================
    
    def analyze_function_complexity(self, function_name: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            Dictionary with complexity metrics
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def analyze_class_structure(self, class_name: str) -> Dict[str, Any]:
        """Analyze class structure and quality metrics.
        
        Args:
            class_name: Name of the class
            
        Returns:
            Dictionary with class metrics
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def analyze_import_relationships(self) -> Dict[str, Any]:
        """Analyze import relationships across the codebase.
        
        Returns:
            Dictionary with import graph and circular dependency info
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # BASH COMMAND EXECUTION
    # ========================================================================
    
    def validate_bash_command(self, command: str) -> Tuple[bool, str]:
        """Validate a bash command for safety.
        
        Args:
            command: Bash command to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def run_bash_command(self, command: str) -> Dict[str, Any]:
        """Run a bash command safely.
        
        Args:
            command: Bash command to run
            
        Returns:
            Dictionary with command output and status
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # REFLECTION AND REASONING
    # ========================================================================
    
    def perform_reflection(self, prompt: str) -> Dict[str, Any]:
        """Perform reflection using AI reasoning.
        
        Args:
            prompt: Reflection prompt
            
        Returns:
            Dictionary with reflection results
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """Parse structured reflection response.
        
        Args:
            response: Raw reflection response
            
        Returns:
            Parsed reflection data
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    # ========================================================================
    # WORKSPACE AND CODEBASE ACCESS
    # ========================================================================
    
    def get_workspace_tools(self) -> List[str]:
        """Get list of available workspace tools.
        
        Returns:
            List of tool names
        """
        # TODO: Move implementation from graph_sitter_analysis.py
        pass
    
    def get_current_code_codebase(self) -> Codebase:
        """Get current code codebase instance.
        
        Returns:
            Codebase instance
        """
        return self.tools.get_current_codebase()
    
    def get_codegen_sdk_codebase(self) -> Codebase:
        """Get Codegen SDK codebase instance.
        
        Returns:
            Codebase instance
        """
        return self.tools.get_codegen_sdk_codebase()
    
    # NOTE: 76 methods total from graph_sitter_analysis.py
    # Additional private methods (_*) will be moved in implementation phase


# ============================================================================
# MODULE-LEVEL EXPORTS
# ============================================================================

__all__ = [
    # Main analyzer
    'GraphSitterAnalyzer',
    
    # API models
    'AnalyzeRequest',
    'ErrorAnalysisResponse',
    'EntrypointAnalysisResponse',
    'TransformationRequest',
    'VisualizationRequest',
    
    # Utility functions
    'clone_repository',
    'calculate_doi',
    'get_operators_and_operands',
    'calculate_halstead_volume',
    'cc_rank',
]

