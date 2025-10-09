"""Integrated Analysis - Unified interface for graph-sitter + LSP + AutoGenLib.

This module provides a single, clean API that combines:
1. Graph-sitter codebase analysis (AST, symbols, dependencies)
2. SolidLSP language server diagnostics (type checking, linting)
3. AutoGenLib AI-powered error resolution

Usage:
    from integrated_analysis import IntegratedAnalyzer
    
    analyzer = IntegratedAnalyzer("/path/to/repo")
    
    # Full analysis pipeline
    results = analyzer.full_analysis()
    
    # Or individual components
    structure = analyzer.analyze_structure()
    diagnostics = analyzer.get_diagnostics()
    fixes = analyzer.generate_fixes()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Graph-sitter core
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary

# LSP integration - use existing adapter
try:
    from lsp_adapter import LSPAdapter, LSPDiagnostic as Diagnostic
except ImportError:
    from src.lsp_adapter import LSPAdapter, LSPDiagnostic as Diagnostic

# AutoGenLib integration - use existing adapter
try:
    from autogenlib_adapter import AutoGenLibAdapter
except ImportError:
    from src.autogenlib_adapter import AutoGenLibAdapter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResults:
    """Complete analysis results combining all sources."""
    
    # Structural analysis
    file_count: int
    function_count: int
    class_count: int
    symbol_count: int
    dependency_graph: Dict[str, List[str]]
    
    # LSP diagnostics
    errors: List[Diagnostic]
    warnings: List[Diagnostic]
    info: List[Diagnostic]
    
    # AI fixes (if requested)
    suggested_fixes: Optional[List[Dict[str, Any]]] = None
    
    # Raw data for advanced usage
    raw_structure: Optional[Dict] = None
    raw_diagnostics: Optional[Dict] = None


class IntegratedAnalyzer:
    """Unified analyzer combining graph-sitter, LSP, and AutoGenLib.
    
    This class provides a single entry point for comprehensive code analysis,
    integrating structural analysis, type checking, and AI-powered fixes.
    
    Args:
        repo_path: Path to the repository to analyze
        enable_lsp: Whether to enable LSP diagnostics (default: True)
        enable_autogenlib: Whether to enable AI fixes (default: False)
        lsp_servers: List of LSP servers to use (default: ["pyright"])
    
    Example:
        >>> analyzer = IntegratedAnalyzer("./my-project")
        >>> results = analyzer.full_analysis()
        >>> print(f"Found {len(results.errors)} errors")
        >>> 
        >>> # Apply AI fixes
        >>> if results.errors:
        ...     fixes = analyzer.generate_fixes(results.errors[:5])
        ...     analyzer.apply_fixes(fixes)
    """
    
    def __init__(
        self,
        repo_path: str,
        enable_lsp: bool = True,
        enable_autogenlib: bool = False,
        lsp_servers: Optional[List[str]] = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.enable_lsp = enable_lsp
        self.enable_autogenlib = enable_autogenlib
        
        # Initialize graph-sitter codebase
        logger.info(f"Initializing codebase analysis for {self.repo_path}")
        self.codebase = Codebase(str(self.repo_path))
        
        # Initialize LSP if enabled
        self.lsp_adapter = None
        if self.enable_lsp:
            logger.info("Initializing LSP adapter")
            try:
                self.lsp_adapter = LSPAdapter(str(self.repo_path))
            except Exception as e:
                logger.warning(f"Could not initialize LSP adapter: {e}")
                self.enable_lsp = False
        
        # Initialize AutoGenLib if enabled
        self.autogenlib_adapter = None
        if self.enable_autogenlib:
            logger.info("Initializing AutoGenLib adapter")
            try:
                self.autogenlib_adapter = AutoGenLibAdapter(
                    codebase_path=str(self.repo_path)
                )
            except Exception as e:
                logger.warning(f"Could not initialize AutoGenLib adapter: {e}")
                self.enable_autogenlib = False
    
    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze code structure using graph-sitter.
        
        Returns comprehensive structural information including:
        - Files, functions, classes, symbols
        - Dependencies and imports
        - Code metrics
        
        Returns:
            Dictionary containing structural analysis results
        """
        logger.info("Running structural analysis...")
        
        # Get high-level summary
        summary = get_codebase_summary(self.codebase)
        
        # Build dependency graph
        dep_graph = {}
        for file in self.codebase.files:
            deps = [str(imp.resolved_symbol) for imp in file.imports if imp.resolved_symbol]
            dep_graph[file.filepath] = deps
        
        return {
            "summary": summary,
            "dependencies": dep_graph,
            "files": [f.filepath for f in self.codebase.files],
            "file_count": len(self.codebase.files),
            "function_count": len(self.codebase.functions),
            "class_count": len(self.codebase.classes),
        }
    
    def get_diagnostics(self) -> Dict[str, List[Diagnostic]]:
        """Get LSP diagnostics (errors, warnings, info).
        
        Runs configured LSP servers to collect type checking, linting,
        and other diagnostic information.
        
        Returns:
            Dictionary with keys "errors", "warnings", "info" containing diagnostics
        """
        if not self.enable_lsp or not self.lsp_adapter:
            logger.warning("LSP not enabled, skipping diagnostics")
            return {"errors": [], "warnings": [], "info": []}
        
        logger.info("Collecting LSP diagnostics...")
        
        try:
            all_diagnostics = self.lsp_adapter.get_all_diagnostics()
            
            # Categorize by severity
            errors = [d for d in all_diagnostics if d.severity.lower() == "error"]
            warnings = [d for d in all_diagnostics if d.severity.lower() == "warning"]
            info = [d for d in all_diagnostics if d.severity.lower() in ("information", "hint")]
            
            return {
                "errors": errors,
                "warnings": warnings,
                "info": info,
            }
        except Exception as e:
            logger.error(f"Error collecting diagnostics: {e}")
            return {"errors": [], "warnings": [], "info": []}
    
    def generate_fixes(
        self,
        diagnostics: Optional[List[Diagnostic]] = None,
        max_fixes: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered fixes for diagnostics.
        
        Uses AutoGenLib to generate fixes for errors and warnings.
        Includes rich context from graph-sitter symbol analysis.
        
        Args:
            diagnostics: List of diagnostics to fix (default: all errors)
            max_fixes: Maximum number of fixes to generate
        
        Returns:
            List of fix suggestions with code and context
        """
        if not self.enable_autogenlib or not self.autogenlib_adapter:
            logger.warning("AutoGenLib not enabled, cannot generate fixes")
            return []
        
        if diagnostics is None:
            # Get all errors by default
            diag_dict = self.get_diagnostics()
            diagnostics = diag_dict["errors"]
        
        if not diagnostics:
            logger.info("No diagnostics to fix")
            return []
        
        logger.info(f"Generating fixes for {min(len(diagnostics), max_fixes)} diagnostics...")
        
        fixes = []
        for diagnostic in diagnostics[:max_fixes]:
            try:
                # Convert diagnostic to AnalysisError format
                error = diagnostic.to_analysis_error()
                
                # Generate fix using AutoGenLib adapter
                fix_result = self.autogenlib_adapter.resolve_error(error)
                
                if fix_result and fix_result.get("status") == "success":
                    fixes.append({
                        "diagnostic": diagnostic,
                        "fix": fix_result["fix"],
                        "context": fix_result.get("context", {}),
                    })
            except Exception as e:
                logger.error(f"Error generating fix for {diagnostic}: {e}")
        
        return fixes
    
    def apply_fixes(self, fixes: List[Dict[str, Any]]) -> int:
        """Apply generated fixes to the codebase.
        
        Args:
            fixes: List of fix suggestions from generate_fixes()
        
        Returns:
            Number of fixes successfully applied
        """
        if not fixes:
            return 0
        
        logger.info(f"Applying {len(fixes)} fixes...")
        
        applied_count = 0
        for fix_data in fixes:
            try:
                # Extract fix information
                fix = fix_data["fix"]
                diagnostic = fix_data["diagnostic"]
                
                # Apply fix to file
                file = self.codebase.get_file(diagnostic.filepath)
                if file:
                    file.edit(fix["code"])
                    applied_count += 1
                    logger.info(f"Applied fix to {diagnostic.filepath}")
            except Exception as e:
                logger.error(f"Error applying fix: {e}")
        
        # Commit changes
        if applied_count > 0:
            logger.info("Committing changes...")
            self.codebase.commit()
        
        return applied_count
    
    def full_analysis(
        self,
        generate_fixes: bool = False,
        max_fixes: int = 10
    ) -> AnalysisResults:
        """Run complete analysis pipeline.
        
        Combines structural analysis, LSP diagnostics, and optionally
        AI-powered fix generation into a single comprehensive result.
        
        Args:
            generate_fixes: Whether to generate AI fixes for errors
            max_fixes: Maximum number of fixes to generate
        
        Returns:
            AnalysisResults containing all analysis data
        """
        logger.info("Starting full analysis pipeline...")
        
        # 1. Structural analysis
        structure = self.analyze_structure()
        
        # 2. LSP diagnostics
        diagnostics_dict = self.get_diagnostics()
        
        # 3. AI fixes (if requested)
        fixes = None
        if generate_fixes and self.enable_autogenlib:
            fixes = self.generate_fixes(
                diagnostics_dict["errors"],
                max_fixes=max_fixes
            )
        
        # Build results
        results = AnalysisResults(
            file_count=structure["file_count"],
            function_count=structure["function_count"],
            class_count=structure["class_count"],
            symbol_count=len(self.codebase.symbols),
            dependency_graph=structure["dependencies"],
            errors=diagnostics_dict["errors"],
            warnings=diagnostics_dict["warnings"],
            info=diagnostics_dict["info"],
            suggested_fixes=fixes,
            raw_structure=structure,
            raw_diagnostics=diagnostics_dict,
        )
        
        logger.info(f"Analysis complete: {results.file_count} files, "
                   f"{len(results.errors)} errors, {len(results.warnings)} warnings")
        
        return results
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all analysis components.
        
        Returns:
            Dictionary indicating status of each component
        """
        return {
            "codebase": self.codebase is not None,
            "lsp": self.lsp_adapter is not None,
            "autogenlib": self.autogenlib_adapter is not None,
        }


# Convenience function for quick analysis
def analyze_repository(
    repo_path: str,
    enable_lsp: bool = True,
    enable_autogenlib: bool = False,
    generate_fixes: bool = False,
    max_fixes: int = 10,
) -> AnalysisResults:
    """Quick analysis of a repository with sensible defaults.
    
    This is a convenience function that creates an IntegratedAnalyzer
    and runs a full analysis with common settings.
    
    Args:
        repo_path: Path to repository
        enable_lsp: Enable LSP diagnostics
        enable_autogenlib: Enable AI fix generation
        generate_fixes: Generate fixes for errors
        max_fixes: Maximum fixes to generate
    
    Returns:
        Complete analysis results
    
    Example:
        >>> results = analyze_repository("./my-project", generate_fixes=True)
        >>> print(f"Files: {results.file_count}, Errors: {len(results.errors)}")
    """
    analyzer = IntegratedAnalyzer(
        repo_path,
        enable_lsp=enable_lsp,
        enable_autogenlib=enable_autogenlib
    )
    
    return analyzer.full_analysis(
        generate_fixes=generate_fixes,
        max_fixes=max_fixes
    )


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python integrated_analysis.py <repo_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    print(f"Analyzing {repo_path}...")
    results = analyze_repository(repo_path, enable_lsp=True)
    
    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}")
    print(f"Files: {results.file_count}")
    print(f"Functions: {results.function_count}")
    print(f"Classes: {results.class_count}")
    print(f"Errors: {len(results.errors)}")
    print(f"Warnings: {len(results.warnings)}")
    
    if results.errors:
        print(f"\nTop 5 errors:")
        for err in results.errors[:5]:
            print(f"  - {err.filepath}:{err.line}: {err.message}")
