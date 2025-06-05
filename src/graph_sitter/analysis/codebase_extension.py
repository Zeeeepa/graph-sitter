"""
Codebase Analysis Extension - Adds Analysis methods to the Codebase class
"""

import os
from typing import Any, Dict, Optional

from graph_sitter.core.codebase import Codebase
from .orchestrator import AnalysisOrchestrator


def add_analysis_method(self, config: Optional[Dict[str, Any]] = None) -> AnalysisOrchestrator:
    """
    Create an Analysis orchestrator for comprehensive codebase analysis.
    
    This method enables the Analysis API pattern:
    - codebase = Codebase.from_repo('repo').Analysis()
    - codebase = Codebase('path/to/repo').Analysis()
    
    Args:
        config: Optional configuration for analysis
        
    Returns:
        AnalysisOrchestrator instance for running comprehensive analysis
        
    Example:
        >>> from graph_sitter import Codebase
        >>> # Analyze remote repository
        >>> analysis = Codebase.from_repo('fastapi/fastapi').Analysis()
        >>> report = analysis.run_comprehensive_analysis()
        >>> analysis.open_dashboard()
        >>> 
        >>> # Analyze local repository
        >>> analysis = Codebase('path/to/repo').Analysis()
        >>> report = analysis.run_comprehensive_analysis()
    """
    return AnalysisOrchestrator(self, config)


@classmethod
def analysis_from_path(cls, repo_path: str, config: Optional[Dict[str, Any]] = None) -> AnalysisOrchestrator:
    """
    Create an Analysis orchestrator directly from a repository path.
    
    This is a convenience method that combines codebase creation and analysis:
    - analysis = Codebase.AnalysisFromPath('path/to/repo')
    
    Args:
        repo_path: Path to the repository or repo name (owner/repo)
        config: Optional configuration for analysis
        
    Returns:
        AnalysisOrchestrator instance for running comprehensive analysis
        
    Example:
        >>> from graph_sitter import Codebase
        >>> # Analyze local repository
        >>> analysis = Codebase.AnalysisFromPath('path/to/repo')
        >>> report = analysis.run_comprehensive_analysis()
        >>> analysis.open_dashboard()
        >>> 
        >>> # Analyze remote repository
        >>> analysis = Codebase.AnalysisFromPath('fastapi/fastapi')
        >>> report = analysis.run_comprehensive_analysis()
    """
    # Determine if it's a local path or remote repo
    if '/' in repo_path and not os.path.exists(repo_path):
        # Assume it's a remote repo (owner/repo format)
        codebase = cls.from_repo(repo_path)
    else:
        # Assume it's a local path
        codebase = cls(repo_path)
    
    return AnalysisOrchestrator(codebase, config)


# Monkey patch the Codebase class to add Analysis methods
Codebase.Analysis = add_analysis_method
Codebase.AnalysisFromPath = analysis_from_path

