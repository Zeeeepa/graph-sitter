"""
TODO/FIXME/HACK tracker for identifying and managing technical debt.

Provides utilities for finding, categorizing, and tracking TODO items
across the codebase to help manage technical debt systematically.
"""

import re
import ast
from typing import List, Dict, Any, Optional, Set, NamedTuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TodoType(Enum):
    """Types of TODO items."""
    TODO = "TODO"
    FIXME = "FIXME"
    HACK = "HACK"
    XXX = "XXX"
    NOTE = "NOTE"
    BUG = "BUG"


class TodoPriority(Enum):
    """Priority levels for TODO items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TodoItem:
    """Represents a single TODO item found in code."""
    type: TodoType
    message: str
    file_path: str
    line_number: int
    column: int
    context: str  # Surrounding code context
    priority: TodoPriority = TodoPriority.MEDIUM
    assignee: Optional[str] = None
    created_date: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.type.value}: {self.message} ({self.file_path}:{self.line_number})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.type.value,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column': self.column,
            'context': self.context,
            'priority': self.priority.value,
            'assignee': self.assignee,
            'created_date': self.created_date,
        }


class TodoTracker:
    """
    Tracker for finding and managing TODO items in codebases.
    
    Provides comprehensive scanning, categorization, and reporting
    capabilities for technical debt management.
    """
    
    # Regex patterns for different TODO types
    TODO_PATTERNS = {
        TodoType.TODO: re.compile(r'#?\s*(TODO|todo)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
        TodoType.FIXME: re.compile(r'#?\s*(FIXME|fixme)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
        TodoType.HACK: re.compile(r'#?\s*(HACK|hack)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
        TodoType.XXX: re.compile(r'#?\s*(XXX|xxx)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
        TodoType.NOTE: re.compile(r'#?\s*(NOTE|note)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
        TodoType.BUG: re.compile(r'#?\s*(BUG|bug)(?:\s*\([^)]+\))?\s*:?\s*(.+)', re.IGNORECASE),
    }
    
    # Priority keywords that indicate high priority
    HIGH_PRIORITY_KEYWORDS = {
        'urgent', 'critical', 'important', 'asap', 'immediately',
        'security', 'vulnerability', 'performance', 'memory leak',
        'crash', 'error', 'exception', 'fail'
    }
    
    # Priority keywords that indicate low priority
    LOW_PRIORITY_KEYWORDS = {
        'nice to have', 'optional', 'future', 'someday', 'maybe',
        'enhancement', 'improvement', 'refactor', 'cleanup'
    }
    
    def __init__(self, file_extensions: Optional[Set[str]] = None):
        """
        Initialize TodoTracker.
        
        Args:
            file_extensions: Set of file extensions to scan (e.g., {'.py', '.js'})
        """
        self.file_extensions = file_extensions or {'.py', '.js', '.ts', '.tsx', '.jsx'}
        self.todos: List[TodoItem] = []
    
    def scan_file(self, file_path: Path) -> List[TodoItem]:
        """
        Scan a single file for TODO items.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of TodoItem objects found in the file
        """
        if file_path.suffix not in self.file_extensions:
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return []
        
        todos = []
        
        for line_num, line in enumerate(lines, 1):
            # Check each TODO pattern
            for todo_type, pattern in self.TODO_PATTERNS.items():
                match = pattern.search(line)
                if match:
                    message = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # Extract context (surrounding lines)
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 2)
                    context = ''.join(lines[context_start:context_end]).strip()
                    
                    # Determine priority
                    priority = self._determine_priority(message, line)
                    
                    # Extract assignee if present
                    assignee = self._extract_assignee(line)
                    
                    todo = TodoItem(
                        type=todo_type,
                        message=message,
                        file_path=str(file_path),
                        line_number=line_num,
                        column=match.start(),
                        context=context,
                        priority=priority,
                        assignee=assignee
                    )
                    
                    todos.append(todo)
                    break  # Only match first pattern per line
        
        return todos
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[TodoItem]:
        """
        Scan a directory for TODO items.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of all TodoItem objects found
        """
        todos = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                file_todos = self.scan_file(file_path)
                todos.extend(file_todos)
        
        self.todos = todos
        return todos
    
    def _determine_priority(self, message: str, line: str) -> TodoPriority:
        """Determine priority based on message content and context."""
        text = (message + " " + line).lower()
        
        # Check for high priority keywords
        if any(keyword in text for keyword in self.HIGH_PRIORITY_KEYWORDS):
            return TodoPriority.HIGH
        
        # Check for low priority keywords
        if any(keyword in text for keyword in self.LOW_PRIORITY_KEYWORDS):
            return TodoPriority.LOW
        
        # Check for critical indicators
        if any(word in text for word in ['critical', 'urgent', 'security']):
            return TodoPriority.CRITICAL
        
        return TodoPriority.MEDIUM
    
    def _extract_assignee(self, line: str) -> Optional[str]:
        """Extract assignee from TODO comment if present."""
        # Look for patterns like TODO(username): or TODO @username:
        assignee_patterns = [
            re.compile(r'TODO\s*\(([^)]+)\)', re.IGNORECASE),
            re.compile(r'TODO\s*@(\w+)', re.IGNORECASE),
            re.compile(r'FIXME\s*\(([^)]+)\)', re.IGNORECASE),
            re.compile(r'FIXME\s*@(\w+)', re.IGNORECASE),
        ]
        
        for pattern in assignee_patterns:
            match = pattern.search(line)
            if match:
                return match.group(1).strip()
        
        return None
    
    def get_todos_by_type(self, todo_type: TodoType) -> List[TodoItem]:
        """Get all TODOs of a specific type."""
        return [todo for todo in self.todos if todo.type == todo_type]
    
    def get_todos_by_priority(self, priority: TodoPriority) -> List[TodoItem]:
        """Get all TODOs of a specific priority."""
        return [todo for todo in self.todos if todo.priority == priority]
    
    def get_todos_by_file(self, file_path: str) -> List[TodoItem]:
        """Get all TODOs in a specific file."""
        return [todo for todo in self.todos if todo.file_path == file_path]
    
    def get_todos_by_assignee(self, assignee: str) -> List[TodoItem]:
        """Get all TODOs assigned to a specific person."""
        return [todo for todo in self.todos if todo.assignee == assignee]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about TODO items."""
        if not self.todos:
            return {'total': 0}
        
        stats = {
            'total': len(self.todos),
            'by_type': {},
            'by_priority': {},
            'by_file': {},
            'by_assignee': {},
        }
        
        # Count by type
        for todo_type in TodoType:
            count = len(self.get_todos_by_type(todo_type))
            if count > 0:
                stats['by_type'][todo_type.value] = count
        
        # Count by priority
        for priority in TodoPriority:
            count = len(self.get_todos_by_priority(priority))
            if count > 0:
                stats['by_priority'][priority.value] = count
        
        # Count by file (top 10)
        file_counts = {}
        for todo in self.todos:
            file_counts[todo.file_path] = file_counts.get(todo.file_path, 0) + 1
        
        stats['by_file'] = dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Count by assignee
        assignee_counts = {}
        for todo in self.todos:
            if todo.assignee:
                assignee_counts[todo.assignee] = assignee_counts.get(todo.assignee, 0) + 1
        
        stats['by_assignee'] = dict(sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True))
        
        return stats
    
    def generate_report(self, format: str = 'text') -> str:
        """
        Generate a comprehensive report of TODO items.
        
        Args:
            format: Report format ('text', 'markdown', 'json')
            
        Returns:
            Formatted report string
        """
        if format == 'json':
            import json
            return json.dumps([todo.to_dict() for todo in self.todos], indent=2)
        
        stats = self.get_summary_stats()
        
        if format == 'markdown':
            return self._generate_markdown_report(stats)
        else:
            return self._generate_text_report(stats)
    
    def _generate_text_report(self, stats: Dict[str, Any]) -> str:
        """Generate a text-based report."""
        lines = [
            "TODO Items Report",
            "=" * 50,
            f"Total TODO items: {stats['total']}",
            "",
        ]
        
        if stats['total'] == 0:
            lines.append("No TODO items found.")
            return "\n".join(lines)
        
        # By type
        lines.extend([
            "By Type:",
            "-" * 20,
        ])
        for todo_type, count in stats['by_type'].items():
            lines.append(f"  {todo_type}: {count}")
        
        lines.append("")
        
        # By priority
        lines.extend([
            "By Priority:",
            "-" * 20,
        ])
        for priority, count in stats['by_priority'].items():
            lines.append(f"  {priority}: {count}")
        
        lines.append("")
        
        # High priority items
        high_priority = self.get_todos_by_priority(TodoPriority.HIGH)
        critical_priority = self.get_todos_by_priority(TodoPriority.CRITICAL)
        
        if critical_priority or high_priority:
            lines.extend([
                "High Priority Items:",
                "-" * 30,
            ])
            
            for todo in critical_priority + high_priority:
                lines.append(f"  {todo.priority.value.upper()}: {todo.message}")
                lines.append(f"    File: {todo.file_path}:{todo.line_number}")
                lines.append("")
        
        # Top files with TODOs
        if stats['by_file']:
            lines.extend([
                "Files with Most TODOs:",
                "-" * 30,
            ])
            for file_path, count in list(stats['by_file'].items())[:5]:
                lines.append(f"  {file_path}: {count}")
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, stats: Dict[str, Any]) -> str:
        """Generate a markdown-based report."""
        lines = [
            "# TODO Items Report",
            "",
            f"**Total TODO items:** {stats['total']}",
            "",
        ]
        
        if stats['total'] == 0:
            lines.append("No TODO items found.")
            return "\n".join(lines)
        
        # By type
        lines.extend([
            "## By Type",
            "",
        ])
        for todo_type, count in stats['by_type'].items():
            lines.append(f"- **{todo_type}**: {count}")
        
        lines.append("")
        
        # By priority
        lines.extend([
            "## By Priority",
            "",
        ])
        for priority, count in stats['by_priority'].items():
            lines.append(f"- **{priority}**: {count}")
        
        lines.append("")
        
        # High priority items
        high_priority = self.get_todos_by_priority(TodoPriority.HIGH)
        critical_priority = self.get_todos_by_priority(TodoPriority.CRITICAL)
        
        if critical_priority or high_priority:
            lines.extend([
                "## High Priority Items",
                "",
            ])
            
            for todo in critical_priority + high_priority:
                lines.append(f"### {todo.priority.value.upper()}: {todo.message}")
                lines.append(f"**File:** `{todo.file_path}:{todo.line_number}`")
                lines.append("")
        
        # Top files with TODOs
        if stats['by_file']:
            lines.extend([
                "## Files with Most TODOs",
                "",
            ])
            for file_path, count in list(stats['by_file'].items())[:5]:
                lines.append(f"- `{file_path}`: {count}")
        
        return "\n".join(lines)
    
    def export_to_csv(self, output_path: Path) -> None:
        """Export TODO items to CSV file."""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['type', 'priority', 'message', 'file_path', 'line_number', 'assignee']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for todo in self.todos:
                writer.writerow({
                    'type': todo.type.value,
                    'priority': todo.priority.value,
                    'message': todo.message,
                    'file_path': todo.file_path,
                    'line_number': todo.line_number,
                    'assignee': todo.assignee or '',
                })
    
    def filter_todos(self, 
                    types: Optional[List[TodoType]] = None,
                    priorities: Optional[List[TodoPriority]] = None,
                    assignees: Optional[List[str]] = None,
                    file_patterns: Optional[List[str]] = None) -> List[TodoItem]:
        """
        Filter TODO items based on various criteria.
        
        Args:
            types: List of TodoType to include
            priorities: List of TodoPriority to include
            assignees: List of assignees to include
            file_patterns: List of file path patterns to match
            
        Returns:
            Filtered list of TodoItem objects
        """
        filtered = self.todos
        
        if types:
            filtered = [todo for todo in filtered if todo.type in types]
        
        if priorities:
            filtered = [todo for todo in filtered if todo.priority in priorities]
        
        if assignees:
            filtered = [todo for todo in filtered if todo.assignee in assignees]
        
        if file_patterns:
            import fnmatch
            filtered = [
                todo for todo in filtered
                if any(fnmatch.fnmatch(todo.file_path, pattern) for pattern in file_patterns)
            ]
        
        return filtered

