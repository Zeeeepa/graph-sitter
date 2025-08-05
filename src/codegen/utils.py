"""
Utility functions for the Codegen SDK.
"""

import re
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone


def validate_org_id(org_id: str) -> bool:
    """
    Validate organization ID format.
    
    Args:
        org_id: Organization ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not org_id or not isinstance(org_id, str):
        return False
    
    # Org IDs should be alphanumeric with possible hyphens/underscores
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', org_id))


def validate_repository(repository: str) -> bool:
    """
    Validate repository format (owner/repo).
    
    Args:
        repository: Repository string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not repository or not isinstance(repository, str):
        return False
    
    # Repository should be in format "owner/repo"
    return bool(re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', repository))


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize a prompt string for API submission.
    
    Args:
        prompt: Raw prompt string
        
    Returns:
        Sanitized prompt string
    """
    if not prompt:
        return ""
    
    # Remove excessive whitespace
    prompt = re.sub(r'\s+', ' ', prompt.strip())
    
    # Limit length (API typically has limits)
    max_length = 10000
    if len(prompt) > max_length:
        prompt = prompt[:max_length] + "..."
    
    return prompt


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def parse_iso_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Parse ISO timestamp string to datetime object.
    
    Args:
        timestamp: ISO timestamp string
        
    Returns:
        Datetime object or None if parsing fails
    """
    if not timestamp:
        return None
    
    try:
        # Handle various ISO formats
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        
        return datetime.fromisoformat(timestamp)
    except ValueError:
        return None


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Backoff multiplier
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                break
            
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            time.sleep(delay)
    
    raise last_exception


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, with later ones taking precedence.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove keys with None values from a dictionary.
    
    Args:
        data: Dictionary to filter
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if v is not None}


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary for logging.
    
    Args:
        data: Dictionary to mask
        sensitive_keys: List of keys to mask (default: common sensitive keys)
        
    Returns:
        Dictionary with masked sensitive values
    """
    if sensitive_keys is None:
        sensitive_keys = ["token", "password", "secret", "key", "auth"]
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            if isinstance(value, str) and value:
                masked_data[key] = "***"
            else:
                masked_data[key] = "***"
    
    return masked_data

