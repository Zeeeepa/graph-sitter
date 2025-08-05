"""
Input Validation Utilities

Provides validation functions for user inputs and data.
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_repository_url(url: str) -> bool:
    """
    Validate a repository URL.
    
    Supports:
    - GitHub URLs (https://github.com/owner/repo)
    - Local paths (/path/to/repo or ./path/to/repo)
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Check for GitHub URL
    github_pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
    if re.match(github_pattern, url):
        return True
    
    # Check for local path
    if url.startswith('/') or url.startswith('./') or url.startswith('../'):
        return True
    
    # Check for relative path
    if not url.startswith('http') and '/' in url:
        return True
    
    return False


def validate_analysis_id(analysis_id: str) -> bool:
    """Validate an analysis ID (should be a UUID)."""
    if not analysis_id or not isinstance(analysis_id, str):
        return False
    
    # UUID pattern
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, analysis_id.lower()))


def validate_severity_filter(severity: str) -> bool:
    """Validate a severity filter value."""
    valid_severities = {"all", "critical", "major", "minor"}
    return severity in valid_severities


def validate_issue_type_filter(issue_type: str) -> bool:
    """Validate an issue type filter value."""
    valid_types = {
        "all", "unused_function", "unused_class", "unused_import",
        "missing_type_annotation", "empty_function", "complexity",
        "parameter_mismatch", "circular_dependency"
    }
    return issue_type in valid_types


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe display."""
    if not filename:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:252] + "..."
    
    return sanitized


def validate_node_path(path: str) -> bool:
    """Validate a tree node path."""
    if not path or not isinstance(path, str):
        return False
    
    # Should not contain dangerous characters
    dangerous_chars = ['<', '>', '"', '|', '\0']
    return not any(char in path for char in dangerous_chars)

