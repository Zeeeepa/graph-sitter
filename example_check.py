#!/usr/bin/env python3
"""
Example script to demonstrate PyStaticCheck usage.

This script contains various issues that can be detected by PyStaticCheck.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def process_data(data: Dict[str, Any], output_file: str = None) -> Optional[Dict[str, Any]]:
    """
    Process the input data and optionally write to a file.
    
    Args:
        data: The input data to process
        output_file: Optional file to write the results to
        
    Returns:
        Processed data or None if output_file is provided
    """
    # Unused variable (detected by ruff, pylint, vulture)
    unused_var = "This variable is never used"
    
    # Security issue (detected by bandit)
    exec("print('Hello, world!')")  # nosec
    
    # Type issue (detected by mypy, pyright)
    result: Dict[str, int] = {}
    result["count"] = "not an integer"  # type: ignore
    
    # Potential bug (detected by pylint, ruff)
    if data:
        print("Data is not empty")
    else:
        print("Data is empty")
        return None
        print("This code is unreachable")
    
    # Write to file if output_file is provided
    if output_file:
        with open(output_file, "w") as f:
            json.dump(data, f)
        return None
    
    return data


class ExampleClass:
    """Example class with various issues."""
    
    def __init__(self, name: str, value: int):
        """Initialize the class."""
        self.name = name
        self.value = value
        # Unused attribute (detected by pylint, vulture)
        self.unused_attr = "This attribute is never used"
    
    def get_name(self):
        """Return the name."""
        return self.name
    
    # Missing docstring (detected by pydocstyle)
    def get_value(self):
        return self.value
    
    # Unused method (detected by pylint, vulture)
    def unused_method(self):
        """This method is never called."""
        return "This method is never used"


def main():
    """Main function."""
    # Misspelled variable (detected by codespell)
    mesage = "This variable name has a typo"
    
    # Create an instance of ExampleClass
    example = ExampleClass("example", 42)
    
    # Process some data
    data = {"name": example.get_name(), "value": example.get_value()}
    result = process_data(data)
    
    # Print the result
    print(f"Result: {result}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
