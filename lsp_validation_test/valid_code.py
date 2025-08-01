#!/usr/bin/env python3
"""Valid Python code with minimal errors for LSP testing."""

import os
import sys
from pathlib import Path

def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply_numbers(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value: int) -> int:
        """Add a value to the result."""
        self.result += value
        return self.result
    
    def get_result(self) -> int:
        """Get the current result."""
        return self.result

def process_file(file_path: str) -> bool:
    """Process a file and return success status."""
    path = Path(file_path)
    if path.exists():
        content = path.read_text()
        return len(content) > 0
    return False

def main():
    """Main function."""
    calc = Calculator()
    calc.add(5)
    calc.add(3)
    print(f"Result: {calc.get_result()}")
    
    # Test file processing
    success = process_file(__file__)
    print(f"File processing: {success}")

if __name__ == "__main__":
    main()
