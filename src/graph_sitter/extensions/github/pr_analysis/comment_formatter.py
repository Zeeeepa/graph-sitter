"""
Formatter for GitHub comments.
"""
from typing import Dict, List, Optional

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GitHubCommentFormatter:
    """Formatter for GitHub comments."""

    def format_results(self, results: List[Dict], pr_context: Dict) -> str:
        """Format analysis results as a GitHub comment.

        Args:
            results: List of analysis results
            pr_context: PR context information

        Returns:
            Formatted comment string
        """
        # Start with a header
        comment = f"# PR Analysis Results for #{pr_context['number']}\n\n"
        
        # If no issues found, return a success message
        if not results:
            comment += "No issues found! :white_check_mark:\n"
            return comment
            
        # Add a summary of issues found
        comment += "## Issues Found\n\n"
        
        # Group results by severity
        severity_groups = self._group_by_severity(results)
        
        # Add a summary table
        comment += "| Severity | Count |\n"
        comment += "| -------- | ----- |\n"
        for severity, items in severity_groups.items():
            icon = self._get_severity_icon(severity)
            comment += f"| {icon} {severity.capitalize()} | {len(items)} |\n"
        
        comment += "\n"
        
        # Add detailed results for each severity level
        for severity, items in severity_groups.items():
            icon = self._get_severity_icon(severity)
            comment += f"## {icon} {severity.capitalize()} Issues\n\n"
            
            for result in items:
                comment += self._format_result(result)
                comment += "\n"
        
        return comment

    def _format_result(self, result: Dict) -> str:
        """Format a single analysis result.

        Args:
            result: Analysis result

        Returns:
            Formatted result string
        """
        # Start with the rule ID and message
        formatted = f"### {result['rule_id']}: {result['message']}\n\n"
        
        # Add file information if available
        if result.get('file'):
            formatted += f"**File:** `{result['file']}`\n"
            
        # Add line information if available
        if result.get('line'):
            formatted += f"**Line:** {result['line']}\n"
            
        # Add code snippet if available
        if result.get('code_snippet'):
            formatted += "\n```\n"
            formatted += result['code_snippet']
            formatted += "\n```\n"
            
        # Add suggestion if available
        if result.get('suggestion'):
            formatted += "\n**Suggestion:** "
            formatted += result['suggestion']
            formatted += "\n"
            
        return formatted

    def _group_by_severity(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group results by severity.

        Args:
            results: List of analysis results

        Returns:
            Dictionary mapping severity to list of results
        """
        groups = {
            "error": [],
            "warning": [],
            "info": []
        }
        
        for result in results:
            severity = result.get('severity', 'info').lower()
            if severity not in groups:
                severity = 'info'
            groups[severity].append(result)
            
        # Return only non-empty groups
        return {k: v for k, v in groups.items() if v}

    def _get_severity_icon(self, severity: str) -> str:
        """Get an icon for a severity level.

        Args:
            severity: Severity level

        Returns:
            Icon string
        """
        if severity == "error":
            return ":x:"
        elif severity == "warning":
            return ":warning:"
        else:
            return ":information_source:"

