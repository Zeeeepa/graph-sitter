#!/usr/bin/env python3
"""
Test file with intentional errors to demonstrate full error retrieval capabilities.
"""

# Import error - non-existent module
import non_existent_module

# Syntax error - missing colon
def function_with_syntax_error()
    return "missing colon"

# Type error - undefined variable
def function_with_undefined_var():
    return undefined_variable

# Indentation error
def function_with_indentation():
return "wrong indentation"

# Unused import
import os
import sys

# Unused variable
unused_var = "this is not used"

# Function with wrong number of arguments
def add_numbers(a, b):
    return a + b

result = add_numbers(1, 2, 3)  # Too many arguments

# Class with issues
class TestClass:
    def __init__(self):
        self.value = 10
    
    def method_with_error(self):
        # Accessing non-existent attribute
        return self.non_existent_attr
    
    def method_with_type_error(self):
        # Type error - can't add string and int
        return "hello" + 5

# More errors
print(undefined_function())  # Undefined function
x = 1 / 0  # Division by zero

