"""
Pink Analyzer - Static analysis engine

Provides comprehensive static analysis capabilities using the Pink engine.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from .types import PinkConfig, PinkAnalysisResult, PinkIssue, IssueSeverity

logger = logging.getLogger(__name__)


class PinkAnalyzer:
    """Pink static analysis engine."""
    
    def __init__(self, config: PinkConfig):
        """Initialize Pink analyzer.
        
        Args:
            config: Pink configuration
        """
        self.config = config
        logger.info("Initialized Pink analyzer")
    
    def analyze_file(self, file_path: Path) -> PinkAnalysisResult:
        """Analyze a single file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis results for the file
        """
        logger.debug(f"Analyzing file: {file_path}")
        
        if not file_path.exists():
            return PinkAnalysisResult(
                file_path=str(file_path),
                issues=[PinkIssue(
                    severity=IssueSeverity.ERROR,
                    message=f"File not found: {file_path}",
                    line=0,
                    column=0
                )],
                complexity_score=0,
                analysis_time=0.0
            )
        
        # Simulate Pink analysis
        issues = self._detect_issues(file_path)
        complexity = self._calculate_complexity(file_path)
        
        return PinkAnalysisResult(
            file_path=str(file_path),
            issues=issues,
            complexity_score=complexity,
            analysis_time=0.1  # Simulated analysis time
        )
    
    def analyze_codebase(self, repo_path: Path) -> PinkAnalysisResult:
        """Analyze entire codebase.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Aggregated analysis results for the codebase
        """
        logger.info(f"Analyzing codebase: {repo_path}")
        
        all_issues = []
        total_complexity = 0
        total_time = 0.0
        
        # Find all Python files
        python_files = list(repo_path.glob("**/*.py"))
        
        for file_path in python_files:
            if self._should_analyze_file(file_path):
                result = self.analyze_file(file_path)
                all_issues.extend(result.issues)
                total_complexity += result.complexity_score
                total_time += result.analysis_time
        
        return PinkAnalysisResult(
            file_path=str(repo_path),
            issues=all_issues,
            complexity_score=total_complexity,
            analysis_time=total_time
        )
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on config.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be analyzed
        """
        # Skip test files if configured
        if not self.config.analyze_tests and "test" in str(file_path):
            return False
        
        # Skip files in excluded directories
        for excluded_dir in self.config.excluded_dirs:
            if excluded_dir in str(file_path):
                return False
        
        return True
    
    def _detect_issues(self, file_path: Path) -> List[PinkIssue]:
        """Detect issues in a file.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            List of detected issues
        """
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Simple issue detection rules
                if len(line) > 120:
                    issues.append(PinkIssue(
                        severity=IssueSeverity.WARNING,
                        message="Line too long (>120 characters)",
                        line=line_num,
                        column=120
                    ))
                
                if "TODO" in line:
                    issues.append(PinkIssue(
                        severity=IssueSeverity.INFO,
                        message="TODO comment found",
                        line=line_num,
                        column=line.find("TODO")
                    ))
                
                if "print(" in line and not line.strip().startswith("#"):
                    issues.append(PinkIssue(
                        severity=IssueSeverity.WARNING,
                        message="Print statement found (consider using logging)",
                        line=line_num,
                        column=line.find("print(")
                    ))
        
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            issues.append(PinkIssue(
                severity=IssueSeverity.ERROR,
                message=f"Analysis error: {e}",
                line=0,
                column=0
            ))
        
        return issues
    
    def _calculate_complexity(self, file_path: Path) -> int:
        """Calculate complexity score for a file.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Complexity score
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Simple complexity calculation
            complexity = 1  # Base complexity
            
            # Add complexity for control structures
            complexity += content.count("if ")
            complexity += content.count("elif ")
            complexity += content.count("for ")
            complexity += content.count("while ")
            complexity += content.count("try:")
            complexity += content.count("except ")
            complexity += content.count("def ")
            complexity += content.count("class ")
            
            return complexity
            
        except Exception as e:
            logger.warning(f"Error calculating complexity for {file_path}: {e}")
            return 1

