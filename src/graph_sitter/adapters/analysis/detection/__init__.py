"""Detection modules for code analysis."""

from .patterns import PatternDetector
from .import_loops import ImportLoopDetector
from .dead_code import DeadCodeDetector

__all__ = ['PatternDetector', 'ImportLoopDetector', 'DeadCodeDetector']

