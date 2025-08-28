#!/usr/bin/env python3
"""
Serena adapter for code analysis and diagnostics.

This module provides an adapter for the Serena code analysis tool,
allowing it to be used to collect diagnostics and issues from codebases.
"""

import os
import sys
import json
import logging
import enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class DiagnosticLevel(enum.Enum):
    """Diagnostic severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "info"
    HINT = "hint"
    
    @classmethod
    def from_lsp_severity(cls, severity: int) -> "DiagnosticLevel":
        """Convert LSP severity to DiagnosticLevel."""
        if severity == 1:  # DiagnosticsSeverity.ERROR
            return cls.ERROR
        elif severity == 2:  # DiagnosticsSeverity.WARNING
            return cls.WARNING
        elif severity == 3:  # DiagnosticsSeverity.INFORMATION
            return cls.INFORMATION
        elif severity == 4:  # DiagnosticsSeverity.HINT
            return cls.HINT
        else:
            return cls.INFORMATION


class SerenaIssue:
    """Represents a diagnostic issue found by Serena."""
    
    def __init__(
        self,
        file_path: str,
        line: int,
        column: int,
        message: str,
        level: DiagnosticLevel,
        code: Optional[str] = None,
        source: Optional[str] = None,
    ):
        """Initialize a SerenaIssue."""
        self.file_path = file_path
        self.line = line
        self.column = column
        self.message = message
        self.level = level
        self.code = code
        self.source = source
    
    @classmethod
    def from_diagnostic(cls, diagnostic: Dict[str, Any], file_path: str) -> "SerenaIssue":
        """Create a SerenaIssue from an LSP diagnostic."""
        # Extract position information
        line = diagnostic.get("range", {}).get("start", {}).get("line", 0)
        column = diagnostic.get("range", {}).get("start", {}).get("character", 0)
        
        # Extract severity
        severity = diagnostic.get("severity", 3)  # Default to INFORMATION
        level = DiagnosticLevel.from_lsp_severity(severity)
        
        # Extract message and code
        message = diagnostic.get("message", "Unknown issue")
        code = diagnostic.get("code")
        source = diagnostic.get("source")
        
        return cls(
            file_path=file_path,
            line=line,
            column=column,
            message=message,
            level=level,
            code=code,
            source=source,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary."""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "level": self.level.value,
            "code": self.code,
            "source": self.source,
        }


class SerenaAdapter:
    """Adapter for the Serena code analysis tool."""
    
    def __init__(self, project_path: str):
        """Initialize the SerenaAdapter.
        
        Args:
            project_path: Path to the project to analyze.
        """
        self.project_path = os.path.abspath(project_path)
        self._project = None
        self._language_server = None
        self._initialized = False
        self._initialize()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()
    
    def _initialize(self):
        """Initialize the Serena project and language server."""
        try:
            # Import Serena components
            from serena.project import Project
            from serena.symbol import LanguageServerSymbol
            from serena.code_editor import LanguageServerCodeEditor
            from solidlsp import SolidLanguageServer
            
            # Load the Serena project
            self._project = Project.load(self.project_path)
            
            # Create a language server
            self._language_server = self._project.create_language_server()
            
            self._initialized = True
            log.info(f"Initialized SerenaAdapter for project at {self.project_path}")
        except ImportError as e:
            log.error(f"Failed to import Serena components: {e}")
            log.error("Make sure Serena is installed with: pip install git+https://github.com/oraios/serena.git")
            self._initialized = False
        except Exception as e:
            log.error(f"Failed to initialize SerenaAdapter: {e}")
            self._initialized = False
    
    def _cleanup(self):
        """Clean up resources."""
        if self._language_server:
            # Close the language server
            try:
                self._language_server.shutdown()
            except Exception as e:
                log.warning(f"Error shutting down language server: {e}")
    
    def get_file_diagnostics(self, file_path: str) -> List[SerenaIssue]:
        """Get diagnostics for a specific file.
        
        Args:
            file_path: Path to the file to analyze, relative to the project root.
            
        Returns:
            List of SerenaIssue objects representing the diagnostics.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return []
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return []
            
            # Get diagnostics from the language server
            diagnostics = self._language_server.request_text_document_diagnostics(file_path)
            
            # Convert to SerenaIssue objects
            issues = []
            for diagnostic in diagnostics:
                issue = SerenaIssue.from_diagnostic(diagnostic, file_path)
                issues.append(issue)
            
            return issues
        except Exception as e:
            log.error(f"Error getting diagnostics for {file_path}: {e}")
            return []
    
    def get_project_diagnostics(self, 
                               relative_path: str = "", 
                               filter_level: Optional[DiagnosticLevel] = None) -> List[SerenaIssue]:
        """Get diagnostics for the entire project or a subdirectory.
        
        Args:
            relative_path: Optional path to a subdirectory to analyze, relative to the project root.
            filter_level: Optional severity level to filter diagnostics by.
            
        Returns:
            List of SerenaIssue objects representing the diagnostics.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return []
        
        try:
            # Get all source files in the specified directory
            source_files = self._project.gather_source_files(relative_path)
            
            # Get diagnostics for each file
            all_issues = []
            for file_path in source_files:
                issues = self.get_file_diagnostics(file_path)
                all_issues.extend(issues)
            
            # Filter by severity level if specified
            if filter_level:
                all_issues = [issue for issue in all_issues if issue.level == filter_level]
            
            return all_issues
        except Exception as e:
            log.error(f"Error getting project diagnostics: {e}")
            return []
    
    def get_diagnostics_summary(self, issues: List[SerenaIssue]) -> Dict[str, int]:
        """Get a summary of diagnostics by severity level.
        
        Args:
            issues: List of SerenaIssue objects.
            
        Returns:
            Dictionary mapping severity levels to counts.
        """
        summary = {
            DiagnosticLevel.ERROR.value: 0,
            DiagnosticLevel.WARNING.value: 0,
            DiagnosticLevel.INFORMATION.value: 0,
            DiagnosticLevel.HINT.value: 0,
        }
        
        for issue in issues:
            summary[issue.level.value] += 1
        
        return summary
    
    def group_diagnostics_by_file(self, issues: List[SerenaIssue]) -> Dict[str, List[SerenaIssue]]:
        """Group diagnostics by file.
        
        Args:
            issues: List of SerenaIssue objects.
            
        Returns:
            Dictionary mapping file paths to lists of SerenaIssue objects.
        """
        grouped = defaultdict(list)
        
        for issue in issues:
            grouped[issue.file_path].append(issue)
        
        return dict(grouped)
    
    def get_file_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get symbols for a specific file.
        
        Args:
            file_path: Path to the file to analyze, relative to the project root.
            
        Returns:
            List of symbol information dictionaries.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return []
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return []
            
            # Get symbols from the language server
            symbols = self._language_server.request_document_symbols(file_path)
            return symbols
        except Exception as e:
            log.error(f"Error getting symbols for {file_path}: {e}")
            return []
    
    def get_document_overview(self, file_path: str) -> Dict[str, Any]:
        """Get an overview of a document.
        
        Args:
            file_path: Path to the file to analyze, relative to the project root.
            
        Returns:
            Dictionary containing document overview information.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return {}
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return {}
            
            # Get document overview from the language server
            overview = self._language_server.request_document_overview(file_path)
            return overview
        except Exception as e:
            log.error(f"Error getting document overview for {file_path}: {e}")
            return {}
    
    def analyze_codebase(self, 
                        relative_path: str = "", 
                        filter_level: Optional[DiagnosticLevel] = None) -> Dict[str, Any]:
        """Analyze the entire codebase or a subdirectory.
        
        Args:
            relative_path: Optional path to a subdirectory to analyze, relative to the project root.
            filter_level: Optional severity level to filter diagnostics by.
            
        Returns:
            Dictionary containing analysis results.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return {
                "error": "SerenaAdapter not initialized",
                "total_issues": 0,
                "summary": {},
                "issues_by_file": {},
            }
        
        try:
            # Get diagnostics for the project
            issues = self.get_project_diagnostics(relative_path, filter_level)
            
            # Get summary and group by file
            summary = self.get_diagnostics_summary(issues)
            issues_by_file = self.group_diagnostics_by_file(issues)
            
            # Convert issues to dictionaries
            issues_by_file_dict = {}
            for file_path, file_issues in issues_by_file.items():
                issues_by_file_dict[file_path] = [issue.to_dict() for issue in file_issues]
            
            return {
                "total_issues": len(issues),
                "summary": summary,
                "issues_by_file": issues_by_file_dict,
            }
        except Exception as e:
            log.error(f"Error analyzing codebase: {e}")
            return {
                "error": str(e),
                "total_issues": 0,
                "summary": {},
                "issues_by_file": {},
            }
    
    def get_references(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get references to a symbol at a specific position.
        
        Args:
            file_path: Path to the file containing the symbol.
            line: Line number of the symbol (0-based).
            character: Character position of the symbol (0-based).
            
        Returns:
            List of reference locations.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return []
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return []
            
            # Get references from the language server
            references = self._language_server.request_references(file_path, line, character)
            return references
        except Exception as e:
            log.error(f"Error getting references for {file_path}:{line}:{character}: {e}")
            return []
    
    def get_definition(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get the definition of a symbol at a specific position.
        
        Args:
            file_path: Path to the file containing the symbol.
            line: Line number of the symbol (0-based).
            character: Character position of the symbol (0-based).
            
        Returns:
            Definition location or None if not found.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return None
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return None
            
            # Get definition from the language server
            definition = self._language_server.request_definition(file_path, line, character)
            return definition
        except Exception as e:
            log.error(f"Error getting definition for {file_path}:{line}:{character}: {e}")
            return None
    
    def get_containing_symbol(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get the symbol containing a specific position.
        
        Args:
            file_path: Path to the file containing the position.
            line: Line number of the position (0-based).
            character: Character position (0-based).
            
        Returns:
            Symbol information or None if not found.
        """
        if not self._initialized:
            log.error("SerenaAdapter not initialized")
            return None
        
        try:
            # Normalize the file path
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, self.project_path)
            
            # Check if the file exists
            if not self._project.relative_path_exists(file_path):
                log.warning(f"File not found: {file_path}")
                return None
            
            # Get containing symbol from the language server
            symbol = self._language_server.request_containing_symbol(file_path, line, character)
            return symbol
        except Exception as e:
            log.error(f"Error getting containing symbol for {file_path}:{line}:{character}: {e}")
            return None


def setup_serena_environment():
    """Set up the Serena environment.
    
    This function checks if Serena is installed and provides instructions if it's not.
    
    Returns:
        bool: True if Serena is installed, False otherwise.
    """
    try:
        # Try to import Serena components
        from serena.project import Project
        from serena.symbol import LanguageServerSymbol
        from serena.code_editor import LanguageServerCodeEditor
        from solidlsp import SolidLanguageServer
        
        return True
    except ImportError:
        print("Serena is not installed. Please install it with the following steps:")
        print("\n1. Create a Python 3.11 virtual environment:")
        print("   python3.11 -m venv venv-serena")
        print("\n2. Activate the virtual environment:")
        print("   source venv-serena/bin/activate  # On Linux/macOS")
        print("   venv-serena\\Scripts\\activate  # On Windows")
        print("\n3. Install Serena:")
        print("   pip install git+https://github.com/oraios/serena.git")
        print("\n4. Run your script with the virtual environment's Python:")
        print("   venv-serena/bin/python your_script.py  # On Linux/macOS")
        print("   venv-serena\\Scripts\\python your_script.py  # On Windows")
        
        return False


if __name__ == "__main__":
    # Check if Serena is installed
    if not setup_serena_environment():
        sys.exit(1)
    
    # Parse command-line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze a codebase using Serena.")
    parser.add_argument("project_path", help="Path to the project to analyze")
    parser.add_argument(
        "--path", "-p", default="", help="Relative path within the project to analyze"
    )
    parser.add_argument(
        "--output", "-o", help="Output file for analysis results (JSON format)"
    )
    parser.add_argument(
        "--severity", "-s", choices=["error", "warning", "info", "hint"],
        help="Filter diagnostics by severity level"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate project path
    project_path = os.path.abspath(args.project_path)
    if not os.path.exists(project_path):
        log.error(f"Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Convert severity string to DiagnosticLevel enum
    filter_level = None
    if args.severity:
        filter_level = DiagnosticLevel(args.severity)
    
    # Initialize the adapter and analyze the codebase
    with SerenaAdapter(project_path) as adapter:
        # Check if adapter initialized successfully
        if not adapter._initialized:
            log.error("Failed to initialize SerenaAdapter")
            sys.exit(1)
        
        # Analyze the codebase
        results = adapter.analyze_codebase(args.path, filter_level)
        
        # Print summary
        log.info(f"Total issues found: {results['total_issues']}")
        log.info(f"Issues by severity: {results['summary']}")
        log.info(f"Issues found in {len(results['issues_by_file'])} files")
        
        # Print some sample issues
        for file_path, issues in results['issues_by_file'].items():
            if issues:
                log.info(f"\nIssues in {file_path}:")
                for i, issue in enumerate(issues[:5]):  # Show up to 5 issues per file
                    log.info(f"  [{issue['level'].upper()}] Line {issue['line']}:{issue['column']} - {issue['message']}")
                if len(issues) > 5:
                    log.info(f"  ... and {len(issues) - 5} more issues")
        
        # Output results
        if args.output:
            output_file = args.output
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            log.info(f"Analysis results saved to {output_file}")

