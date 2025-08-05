"""
Base analyzer class that all specific analyzers inherit from.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.logger import get_logger

from .analysis_result import AnalysisResult, AnalysisMetrics, Finding

logger = get_logger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for all codebase analyzers.
    
    Provides common functionality and defines the interface that
    all analyzers must implement.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.supported_languages = set()  # Override in subclasses
        self.version = "1.0.0"
        
    @abstractmethod
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """
        Perform analysis on the given codebase and files.
        
        Args:
            codebase: The codebase to analyze
            files: List of files to analyze (pre-filtered)
            
        Returns:
            AnalysisResult containing findings and metrics
        """
        pass
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        Check if a file is supported by this analyzer.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is supported, False otherwise
        """
        if not self.supported_languages:
            return True  # Support all languages if none specified
            
        from pathlib import Path
        
        file_ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".ts": "typescript", 
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala"
        }
        
        return lang_map.get(file_ext) in self.supported_languages
    
    def create_result(self, status: str = "completed") -> AnalysisResult:
        """
        Create a new AnalysisResult for this analyzer.
        
        Args:
            status: Status of the analysis
            
        Returns:
            New AnalysisResult instance
        """
        return AnalysisResult(
            analyzer_name=self.name,
            status=status,
            metrics=AnalysisMetrics()
        )
    
    def measure_execution_time(self, func):
        """
        Decorator to measure execution time of analysis functions.
        
        Args:
            func: Function to measure
            
        Returns:
            Decorated function that measures execution time
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if isinstance(result, AnalysisResult):
                    result.metrics.execution_time = execution_time
                    
                logger.info(f"{self.name} analysis completed in {execution_time:.2f} seconds")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{self.name} analysis failed after {execution_time:.2f} seconds: {str(e)}")
                raise
                
        return wrapper
    
    def get_file_content(self, file) -> str:
        """
        Get content of a file safely.
        
        Args:
            file: File object from Graph-Sitter
            
        Returns:
            File content as string, empty string if not available
        """
        try:
            if hasattr(file, 'content'):
                return file.content
            elif hasattr(file, 'filepath'):
                with open(file.filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
        except Exception as e:
            logger.warning(f"Could not read file content: {str(e)}")
            return ""
    
    def get_file_lines(self, file) -> List[str]:
        """
        Get lines of a file safely.
        
        Args:
            file: File object from Graph-Sitter
            
        Returns:
            List of lines in the file
        """
        content = self.get_file_content(file)
        return content.splitlines() if content else []
    
    def calculate_lines_of_code(self, content: str) -> int:
        """
        Calculate lines of code (excluding empty lines and comments).
        
        Args:
            content: File content
            
        Returns:
            Number of lines of code
        """
        lines = content.splitlines()
        loc = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('//'):
                loc += 1
                
        return loc
    
    def extract_code_snippet(self, content: str, line_number: int, context_lines: int = 3) -> str:
        """
        Extract a code snippet around a specific line.
        
        Args:
            content: File content
            line_number: Target line number (1-based)
            context_lines: Number of context lines before and after
            
        Returns:
            Code snippet with context
        """
        lines = content.splitlines()
        
        if line_number < 1 or line_number > len(lines):
            return ""
            
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{i + 1:4d}: {lines[i]}")
            
        return "\n".join(snippet_lines)
    
    def log_progress(self, current: int, total: int, item_name: str = "items"):
        """
        Log analysis progress.
        
        Args:
            current: Current item number
            total: Total number of items
            item_name: Name of items being processed
        """
        if total > 0 and current % max(1, total // 10) == 0:
            percentage = (current / total) * 100
            logger.info(f"{self.name}: Processed {current}/{total} {item_name} ({percentage:.1f}%)")
    
    def validate_codebase(self, codebase: Codebase) -> bool:
        """
        Validate that the codebase is suitable for analysis.
        
        Args:
            codebase: Codebase to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not codebase:
            logger.error("Codebase is None")
            return False
            
        if not hasattr(codebase, 'files'):
            logger.error("Codebase has no files attribute")
            return False
            
        files = list(codebase.files)
        if not files:
            logger.warning("Codebase contains no files")
            return False
            
        return True
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """
        Get information about this analyzer.
        
        Returns:
            Dictionary with analyzer information
        """
        return {
            "name": self.name,
            "version": self.version,
            "supported_languages": list(self.supported_languages),
            "description": self.__doc__ or "No description available"
        }

