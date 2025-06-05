"""
Repository Analyzer - Enables the Codebase.from_repo.Analysis() syntax.

This module provides the RepositoryAnalyzer class that acts as an intermediary
to enable the chained method syntax for analysis operations.
"""

from typing import Literal, Optional, Union
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter.enums import ProgrammingLanguage


class RepositoryAnalyzer:
    """
    Intermediary class that enables the Codebase.from_repo.Analysis() syntax.
    
    This class is returned by Codebase.from_repo when the repo name contains 'Analysis'
    or when explicitly requested, allowing for the chained method call pattern.
    """
    
    def __init__(
        self,
        repo_full_name: str,
        tmp_dir: Optional[str] = "/tmp/codegen",
        commit: Optional[str] = None,
        language: Optional[Union[Literal["python", "typescript"], ProgrammingLanguage]] = None,
        config: Optional[CodebaseConfig] = None,
        secrets: Optional[SecretsConfig] = None,
        full_history: bool = False,
    ):
        """
        Initialize the RepositoryAnalyzer.
        
        Args:
            repo_full_name: Repository name in format "owner/repo"
            tmp_dir: Directory to clone the repo into
            commit: Specific commit hash to clone
            language: Programming language of the repo
            config: Configuration for the codebase
            secrets: Configuration for secrets
            full_history: Whether to clone full history
        """
        self.repo_full_name = repo_full_name
        self.tmp_dir = tmp_dir
        self.commit = commit
        self.language = language
        self.config = config
        self.secrets = secrets
        self.full_history = full_history
    
    def Analysis(self, auto_run: bool = True, **analysis_kwargs):
        """
        Create and optionally run comprehensive analysis.
        
        Args:
            auto_run: Whether to automatically run comprehensive analysis
            **analysis_kwargs: Additional arguments for Analysis configuration
            
        Returns:
            Analysis instance with results (if auto_run=True) or ready for analysis
        """
        # Import here to avoid circular imports
        from graph_sitter.core.analysis import Analysis, AnalysisConfig
        
        # Create analysis configuration
        config = AnalysisConfig(**analysis_kwargs)
        
        # Create Analysis instance from repository
        analysis = Analysis.from_repo(
            repo_full_name=self.repo_full_name,
            config=config,
            tmp_dir=self.tmp_dir,
            commit=self.commit,
            language=self.language,
            codebase_config=self.config,
            secrets=self.secrets,
            full_history=self.full_history,
        )
        
        # Auto-run comprehensive analysis if requested
        if auto_run:
            print(f"🔍 Auto-running comprehensive analysis for {self.repo_full_name}...")
            analysis.run_comprehensive_analysis()
        
        return analysis
    
    def __call__(self, **kwargs):
        """
        Allow the analyzer to be called directly as a function.
        
        This enables syntax like: Codebase.from_repo('repo')()
        """
        return self.Analysis(**kwargs)

