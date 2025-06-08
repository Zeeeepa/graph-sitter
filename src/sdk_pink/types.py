"""
Pink Types - Data models for Pink analysis

Defines the data structures used by the Pink static analysis engine.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set


class IssueSeverity(Enum):
    """Severity levels for analysis issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PinkIssue:
    """Represents an issue found during Pink analysis."""
    severity: IssueSeverity
    message: str
    line: int
    column: int
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class PinkAnalysisResult:
    """Results from Pink static analysis."""
    file_path: str
    issues: List[PinkIssue]
    complexity_score: int
    analysis_time: float
    metadata: Optional[dict] = None


@dataclass
class PinkConfig:
    """Configuration for Pink analysis."""
    analyze_tests: bool = True
    max_complexity: int = 10
    max_line_length: int = 120
    excluded_dirs: Set[str] = None
    enabled_rules: Set[str] = None
    disabled_rules: Set[str] = None
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.excluded_dirs is None:
            self.excluded_dirs = {
                "__pycache__",
                ".git",
                ".pytest_cache",
                "node_modules",
                ".venv",
                "venv"
            }
        
        if self.enabled_rules is None:
            self.enabled_rules = {
                "line_length",
                "complexity",
                "todo_comments",
                "print_statements",
                "unused_imports",
                "undefined_variables"
            }
        
        if self.disabled_rules is None:
            self.disabled_rules = set()
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled.
        
        Args:
            rule_id: ID of the rule to check
            
        Returns:
            True if rule is enabled
        """
        return rule_id in self.enabled_rules and rule_id not in self.disabled_rules

