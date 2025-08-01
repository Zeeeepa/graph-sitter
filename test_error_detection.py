#!/usr/bin/env python3
"""
Test file with intentional errors to validate LSP error detection.
This file contains various types of Python errors that should be detected.
"""

# Syntax Error: Missing closing parenthesis
def broken_function(
    print("This should cause a syntax error")

# Undefined variable error
def undefined_var_function():
    return undefined_variable

# Import error
import nonexistent_module
from nonexistent_module import something

# Indentation error (mixed tabs and spaces)
def indentation_issue():
    if True:
        print("correct indentation")
	print("incorrect indentation - tab instead of spaces")

# Another syntax error: invalid syntax
def another_syntax_error():
    x = 1 +
    return x

# Valid function for comparison
def valid_function():
    """This function should not have any errors."""
    x = 10
    y = 20
    return x + y

if __name__ == "__main__":
    print("Testing error detection...")
    valid_function()
