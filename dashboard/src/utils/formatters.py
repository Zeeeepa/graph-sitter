"""
Data Formatting Utilities

Provides functions for formatting data for display in the UI.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_number(number: int) -> str:
    """Format large numbers with commas."""
    return f"{number:,}"


def format_percentage(value: float, total: float) -> str:
    """Format a percentage with proper handling of zero division."""
    if total == 0:
        return "0%"
    return f"{(value / total * 100):.1f}%"


def format_issue_severity(severity: str) -> Dict[str, str]:
    """Format issue severity with appropriate styling."""
    severity_map = {
        "critical": {
            "label": "Critical",
            "color": "red",
            "icon": "⚠️",
            "bg_color": "red.50",
            "border_color": "red.200"
        },
        "major": {
            "label": "Major", 
            "color": "orange",
            "icon": "👉",
            "bg_color": "orange.50",
            "border_color": "orange.200"
        },
        "minor": {
            "label": "Minor",
            "color": "yellow",
            "icon": "🔍",
            "bg_color": "yellow.50", 
            "border_color": "yellow.200"
        }
    }
    
    return severity_map.get(severity.lower(), {
        "label": severity.title(),
        "color": "gray",
        "icon": "ℹ️",
        "bg_color": "gray.50",
        "border_color": "gray.200"
    })


def format_node_type(node_type: str) -> Dict[str, str]:
    """Format tree node type with appropriate styling."""
    type_map = {
        "folder": {
            "icon": "📁",
            "color": "blue.600"
        },
        "file": {
            "icon": "📄",
            "color": "gray.600"
        },
        "function": {
            "icon": "⚡",
            "color": "green.600"
        },
        "class": {
            "icon": "🏗️",
            "color": "purple.600"
        },
        "entry_point": {
            "icon": "🚀",
            "color": "yellow.600"
        },
        "important": {
            "icon": "⭐",
            "color": "orange.600"
        },
        "dead_code": {
            "icon": "💀",
            "color": "red.600"
        }
    }
    
    return type_map.get(node_type.lower(), {
        "icon": "📄",
        "color": "gray.600"
    })


def format_issue_type(issue_type: str) -> str:
    """Format issue type for display."""
    type_map = {
        "unused_function": "Unused Function",
        "unused_class": "Unused Class", 
        "unused_import": "Unused Import",
        "missing_type_annotation": "Missing Type Annotation",
        "empty_function": "Empty Function",
        "complexity": "High Complexity",
        "parameter_mismatch": "Parameter Mismatch",
        "circular_dependency": "Circular Dependency"
    }
    
    return type_map.get(issue_type, issue_type.replace("_", " ").title())


def format_file_path(file_path: str, max_length: int = 50) -> str:
    """Format file path for display with truncation if needed."""
    if not file_path:
        return ""
    
    if len(file_path) <= max_length:
        return file_path
    
    # Truncate from the middle, keeping the filename
    parts = file_path.split("/")
    filename = parts[-1]
    
    if len(filename) >= max_length - 3:
        return f"...{filename[-(max_length-3):]}"
    
    # Try to keep some directory structure
    remaining_length = max_length - len(filename) - 4  # 4 for ".../"
    
    for i in range(len(parts) - 2, -1, -1):
        if len(parts[i]) <= remaining_length:
            return f".../{parts[i]}/{filename}"
        remaining_length -= len(parts[i]) + 1
        if remaining_length <= 0:
            break
    
    return f".../{filename}"


def format_function_signature(func_name: str, parameters: List[Dict[str, Any]]) -> str:
    """Format a function signature for display."""
    if not parameters:
        return f"{func_name}()"
    
    param_strs = []
    for param in parameters[:3]:  # Limit to first 3 parameters
        param_name = param.get("name", "")
        param_type = param.get("type", "")
        
        if param_type:
            param_strs.append(f"{param_name}: {param_type}")
        else:
            param_strs.append(param_name)
    
    if len(parameters) > 3:
        param_strs.append("...")
    
    return f"{func_name}({', '.join(param_strs)})"


def format_timestamp(timestamp: Optional[datetime]) -> str:
    """Format timestamp for display."""
    if not timestamp:
        return "Unknown"
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if it exceeds max length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

