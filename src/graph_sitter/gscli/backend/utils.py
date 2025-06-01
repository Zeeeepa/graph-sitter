########################################################################################################################
# MISC
########################################################################################################################

import os
from pathlib import Path


def filepath_to_modulename(filepath: str) -> str:
    """Used to convert a an app ref passed in as a filepath to a module
    
    Args:
        filepath: File path to convert (e.g., "src/mymodule/file.py")
        
    Returns:
        Module name (e.g., "src.mymodule.file")
        
    Raises:
        ValueError: If filepath is empty or contains invalid characters
    """
    if not filepath or not isinstance(filepath, str):
        raise ValueError("Filepath must be a non-empty string")
    
    # Normalize path separators and remove any leading/trailing whitespace
    filepath = filepath.strip()
    
    # Basic validation for dangerous characters
    if any(char in filepath for char in ['..', '~', '$']):
        raise ValueError("Filepath contains potentially dangerous characters")
    
    # Convert to Path for normalization
    try:
        normalized_path = str(Path(filepath).as_posix())
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid filepath format: {e}")
    
    # Remove .py extension if present
    module = normalized_path.removesuffix(".py")
    
    # Convert path separators to dots
    return module.replace("/", ".")
