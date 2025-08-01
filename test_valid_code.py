#!/usr/bin/env python3
"""
Test file with valid Python code to ensure error detection doesn't produce false positives.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional


class TestClass:
    """A test class with valid Python code."""
    
    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value
    
    def get_name(self) -> str:
        """Return the name."""
        return self.name
    
    def set_value(self, value: int) -> None:
        """Set the value."""
        self.value = value
    
    def calculate(self, x: int, y: int) -> int:
        """Calculate sum of x, y, and value."""
        return x + y + self.value


def process_data(data: List[Dict[str, any]]) -> Optional[Dict[str, int]]:
    """Process a list of data dictionaries."""
    if not data:
        return None
    
    result = {}
    for item in data:
        if 'key' in item and 'value' in item:
            result[item['key']] = item['value']
    
    return result


def main():
    """Main function."""
    test_obj = TestClass("test", 10)
    print(f"Name: {test_obj.get_name()}")
    
    test_data = [
        {'key': 'a', 'value': 1},
        {'key': 'b', 'value': 2},
        {'key': 'c', 'value': 3}
    ]
    
    result = process_data(test_data)
    if result:
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
