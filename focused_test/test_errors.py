#!/usr/bin/env python3
"""Test file with known errors."""

# Syntax error: missing colon
def bad_function():
    return "error"

# Import error
import non_existent_module

# Name error
def use_undefined():
    return undefined_var

# Type error
def type_issue():
    return "string" + 5
