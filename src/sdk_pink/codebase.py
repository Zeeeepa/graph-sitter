"""
Pink-enhanced Codebase implementation

Provides enhanced codebase analysis capabilities using the Pink static analysis engine.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .analyzer import PinkAnalyzer
from .types import PinkConfig, PinkAnalysisResult

logger = logging.getLogger(__name__)


class Codebase:
    """Pink-enhanced codebase for advanced static analysis."""
    
    def __init__(self, repo_path: Path, config: Optional[PinkConfig] = None):
        """Initialize Pink codebase.
        
        Args:
            repo_path: Path to the repository
            config: Optional Pink configuration
        """
        self.repo_path = Path(repo_path)
        self.config = config or PinkConfig()
        self.analyzer = PinkAnalyzer(self.config)
        
        # Analysis cache
        self._analysis_cache: Dict[str, PinkAnalysisResult] = {}
        
        logger.info(f"Initialized Pink codebase at {self.repo_path}")
    
    def analyze(self, file_path: Optional[str] = None) -> PinkAnalysisResult:
        """Perform Pink analysis on the codebase or specific file.
        
        Args:
            file_path: Optional specific file to analyze
            
        Returns:
            Pink analysis results
        """
        cache_key = file_path or "full_codebase"
        
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        if file_path:
            result = self.analyzer.analyze_file(self.repo_path / file_path)
        else:
            result = self.analyzer.analyze_codebase(self.repo_path)
        
        self._analysis_cache[cache_key] = result
        return result
    
    def get_files(self, pattern: str = "**/*.py") -> List[Path]:
        """Get files matching the pattern.
        
        Args:
            pattern: Glob pattern for files
            
        Returns:
            List of matching file paths
        """
        return list(self.repo_path.glob(pattern))
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of all analysis results.
        
        Returns:
            Summary of analysis results
        """
        if not self._analysis_cache:
            # Perform full analysis if not done yet
            self.analyze()
        
        summary = {
            "total_files_analyzed": len(self._analysis_cache),
            "repo_path": str(self.repo_path),
            "config": self.config.dict() if hasattr(self.config, 'dict') else vars(self.config)
        }
        
        # Aggregate results from all analyses
        total_issues = 0
        total_complexity = 0
        
        for result in self._analysis_cache.values():
            total_issues += len(result.issues)
            total_complexity += result.complexity_score
        
        summary.update({
            "total_issues": total_issues,
            "average_complexity": total_complexity / len(self._analysis_cache) if self._analysis_cache else 0
        })
        
        return summary
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._analysis_cache.clear()
        logger.info("Cleared Pink analysis cache")
    
    def __str__(self) -> str:
        return f"PinkCodebase(path={self.repo_path})"
    
    def __repr__(self) -> str:
        return self.__str__()

