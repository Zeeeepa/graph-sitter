"""
Formatter for GitHub PR comments.

This module provides utilities for formatting static analysis results
as GitHub comments.
"""

from typing import Any, Dict, List, Optional, Union

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CommentFormatter:
    """
    Formatter for GitHub PR comments.
    
    This class provides methods for formatting static analysis results
    as GitHub comments, with support for different comment types and
    formatting options.
    """
    
    _max_comment_length: int = 65000  # GitHub's limit is 65536
    
    def __init__(self, bot_name: str = "PR Static Analysis"):
        """
        Initialize the comment formatter.
        
        Args:
            bot_name: Name to use in comment headers
        """
        self._bot_name = bot_name
    
    def format_general_comment(
        self, 
        title: str,
        summary: str,
        details: Optional[List[Dict[str, Any]]] = None,
        conclusion: Optional[str] = None
    ) -> str:
        """
        Format a general PR comment with analysis results.
        
        Args:
            title: Comment title
            summary: Summary of analysis results
            details: Detailed analysis results
            conclusion: Conclusion or recommendation
            
        Returns:
            Formatted comment text
        """
        comment = f"## {self._bot_name}: {title}\n\n"
        comment += f"{summary}\n\n"
        
        if details:
            comment += "### Details\n\n"
            
            for item in details:
                item_type = item.get("type", "info")
                item_title = item.get("title", "")
                item_message = item.get("message", "")
                item_code = item.get("code")
                item_location = item.get("location")
                
                # Add item title with appropriate emoji
                emoji = self._get_emoji_for_type(item_type)
                comment += f"#### {emoji} {item_title}\n\n"
                
                # Add item message
                comment += f"{item_message}\n\n"
                
                # Add code snippet if provided
                if item_code:
                    language = item.get("language", "")
                    comment += f"```{language}\n{item_code}\n```\n\n"
                
                # Add location if provided
                if item_location:
                    file_path = item_location.get("file", "")
                    line_start = item_location.get("line_start")
                    line_end = item_location.get("line_end")
                    
                    location_str = f"**Location:** `{file_path}`"
                    if line_start:
                        if line_end and line_end != line_start:
                            location_str += f" (lines {line_start}-{line_end})"
                        else:
                            location_str += f" (line {line_start})"
                    
                    comment += f"{location_str}\n\n"
        
        if conclusion:
            comment += f"### Conclusion\n\n{conclusion}\n"
        
        # Ensure comment doesn't exceed GitHub's limit
        if len(comment) > self._max_comment_length:
            logger.warning(f"Comment exceeds GitHub's length limit ({len(comment)} > {self._max_comment_length})")
            comment = comment[:self._max_comment_length - 100] + "\n\n... (comment truncated due to length)"
        
        return comment
    
    def format_inline_comment(
        self,
        issue: str,
        suggestion: Optional[str] = None,
        code_snippet: Optional[str] = None,
        severity: str = "info"
    ) -> str:
        """
        Format an inline comment for a specific line.
        
        Args:
            issue: Description of the issue
            suggestion: Suggested fix
            code_snippet: Code snippet with the fix
            severity: Issue severity (info, warning, error)
            
        Returns:
            Formatted comment text
        """
        emoji = self._get_emoji_for_type(severity)
        comment = f"{emoji} **{self._bot_name}**: {issue}\n\n"
        
        if suggestion:
            comment += f"**Suggestion:** {suggestion}\n\n"
        
        if code_snippet:
            comment += f"```suggestion\n{code_snippet}\n```\n"
        
        return comment
    
    def format_summary_comment(
        self,
        issues_by_type: Dict[str, int],
        files_analyzed: int,
        total_issues: int
    ) -> str:
        """
        Format a summary comment with statistics.
        
        Args:
            issues_by_type: Count of issues by type
            files_analyzed: Number of files analyzed
            total_issues: Total number of issues found
            
        Returns:
            Formatted comment text
        """
        comment = f"## {self._bot_name} Summary\n\n"
        
        comment += f"Analyzed **{files_analyzed}** files and found **{total_issues}** issues.\n\n"
        
        if issues_by_type:
            comment += "### Issues by Type\n\n"
            
            for issue_type, count in issues_by_type.items():
                emoji = self._get_emoji_for_type(issue_type)
                comment += f"- {emoji} **{issue_type.capitalize()}**: {count}\n"
        
        return comment
    
    def format_error_comment(self, error_message: str, details: Optional[str] = None) -> str:
        """
        Format an error comment.
        
        Args:
            error_message: Error message
            details: Error details
            
        Returns:
            Formatted comment text
        """
        comment = f"## {self._bot_name} Error\n\n"
        comment += f"❌ **Error:** {error_message}\n\n"
        
        if details:
            comment += f"<details>\n<summary>Error Details</summary>\n\n```\n{details}\n```\n</details>\n"
        
        return comment
    
    def _get_emoji_for_type(self, item_type: str) -> str:
        """
        Get an appropriate emoji for an item type.
        
        Args:
            item_type: Item type (info, warning, error, etc.)
            
        Returns:
            Emoji string
        """
        type_lower = item_type.lower()
        
        if type_lower in ["error", "critical", "high"]:
            return "❌"
        elif type_lower in ["warning", "medium"]:
            return "⚠️"
        elif type_lower in ["info", "low"]:
            return "ℹ️"
        elif type_lower in ["success", "passed"]:
            return "✅"
        elif type_lower in ["suggestion", "improvement"]:
            return "💡"
        elif type_lower in ["security"]:
            return "🔒"
        elif type_lower in ["performance"]:
            return "⚡"
        elif type_lower in ["style"]:
            return "🎨"
        else:
            return "🔍"
    
    def group_comments_by_file(
        self, 
        comments: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group comments by file path.
        
        Args:
            comments: List of comment data
            
        Returns:
            Dictionary mapping file paths to lists of comments
        """
        grouped = {}
        
        for comment in comments:
            location = comment.get("location", {})
            file_path = location.get("file", "unknown")
            
            if file_path not in grouped:
                grouped[file_path] = []
                
            grouped[file_path].append(comment)
        
        return grouped
    
    def deduplicate_comments(
        self, 
        comments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate comments based on content and location.
        
        Args:
            comments: List of comment data
            
        Returns:
            Deduplicated list of comments
        """
        unique_comments = {}
        
        for comment in comments:
            # Create a unique key based on content and location
            location = comment.get("location", {})
            file_path = location.get("file", "")
            line_start = location.get("line_start")
            message = comment.get("message", "")
            
            key = f"{file_path}:{line_start}:{message}"
            
            # Only keep the first occurrence of each unique comment
            if key not in unique_comments:
                unique_comments[key] = comment
        
        return list(unique_comments.values())

