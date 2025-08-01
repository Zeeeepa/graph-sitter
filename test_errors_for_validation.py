#!/usr/bin/env python3
"""
Test file with real Python errors for LSP validation.
This file contains various types of errors that should be detected by LSP servers.
"""

import os
import sys
import nonexistent_module  # Import error - module doesn't exist
from typing import List, Dict
import unused_import  # Unused import error

# Syntax errors
def function_missing_colon()  # Missing colon syntax error
    return "hello"

def function_with_indentation_error():
return "bad indentation"  # Indentation error

# Name errors
def name_error_function():
    result = undefined_variable + 5  # Name error - undefined variable
    return result

# Type errors
def type_error_function():
    text = "hello"
    number = 42
    result = text + number  # Type error - can't add string and int
    return result

# Unused variables
def unused_variable_function():
    unused_var = "this variable is never used"  # Unused variable warning
    used_var = "this is used"
    return used_var

# Missing imports
def missing_import_function():
    data = json.loads('{"key": "value"}')  # Name error - json not imported
    return data

# Duplicate function definitions
def duplicate_function():
    return "first"

def duplicate_function():  # Duplicate function definition
    return "second"

# Invalid syntax patterns
class InvalidClass
    pass  # Missing colon

# Unreachable code
def unreachable_code():
    return "early return"
    print("This code is unreachable")  # Unreachable code warning

# Wrong number of arguments
def function_with_args(a, b, c):
    return a + b + c

result = function_with_args(1, 2)  # Missing argument error

# Invalid escape sequences
invalid_string = "\z"  # Invalid escape sequence

# Comparison with None using ==
def bad_none_comparison(value):
    if value == None:  # Should use 'is None'
        return True
    return False

# Mutable default arguments
def mutable_default_arg(items=[]):  # Mutable default argument
    items.append("new item")
    return items

# Bare except clause
def bare_except():
    try:
        risky_operation()
    except:  # Bare except clause
        pass

# Undefined function call
def undefined_function_call():
    return nonexistent_function()  # Undefined function

# Class with missing methods
class IncompleteClass:
    def __init__(self):
        self.value = 42
    
    def method_with_typo(self):
        return self.vlaue  # Typo in attribute name

# String formatting errors
def string_format_error():
    name = "Alice"
    age = 30
    # Wrong number of format arguments
    message = "Hello {}, you are {} years old and live in {}".format(name, age)
    return message

# Lambda syntax error
bad_lambda = lambda x y: x + y  # Missing comma in lambda parameters

# Dictionary key errors
def dict_key_error():
    data = {"a": 1, "b": 2}
    return data["c"]  # KeyError - key doesn't exist

# List index errors
def list_index_error():
    items = [1, 2, 3]
    return items[10]  # IndexError - index out of range

# Division by zero
def division_by_zero():
    return 10 / 0  # ZeroDivisionError

# Circular import (would need another file, but we can simulate)
# from test_errors_for_validation import some_function  # Circular import

# Missing return statement
def missing_return_statement(x):
    if x > 0:
        return "positive"
    # Missing return for negative/zero case

# Inconsistent return types
def inconsistent_returns(flag):
    if flag:
        return "string"
    else:
        return 42  # Different return type

# Using undefined class
def undefined_class_usage():
    obj = UndefinedClass()  # Undefined class
    return obj

# Wrong method call
def wrong_method_call():
    text = "hello"
    return text.nonexistent_method()  # Method doesn't exist

# Incorrect super() usage
class Parent:
    def __init__(self, value):
        self.value = value

class Child(Parent):
    def __init__(self, value, extra):
        super().__init__()  # Missing required argument
        self.extra = extra

# File operation without proper handling
def file_operation_error():
    with open("nonexistent_file.txt") as f:  # File doesn't exist
        content = f.read()
    return content

# Invalid regular expression
import re
def regex_error():
    pattern = r"[invalid regex"  # Invalid regex pattern
    return re.compile(pattern)

# Incorrect use of global
global_var = 10

def global_usage_error():
    global global_var
    global_var += undefined_local_var  # Undefined variable

# Missing __all__ export
__all__ = ["exported_function", "nonexistent_function"]  # nonexistent_function not defined

def exported_function():
    return "exported"

# Incorrect docstring format
def bad_docstring():
    """
    This function has a malformed docstring.
    
    Args:
        nonexistent_param: This parameter doesn't exist
    
    Returns:
        Something that's not actually returned
    """
    return None

# Using deprecated features (Python 2 style)
def deprecated_usage():
    # Using print as statement (Python 2 style) - would be syntax error in Python 3
    # print "This is Python 2 style"  # Commented out to avoid syntax error
    
    # Using old string formatting
    message = "Hello %s, you are %d years old" % ("Alice",)  # Missing argument

# Incorrect exception handling
def bad_exception_handling():
    try:
        risky_operation()
    except ValueError, e:  # Python 2 style exception handling - syntax error in Python 3
        print(e)

# Missing self parameter
class BadClass:
    def method_missing_self():  # Missing self parameter
        return "bad method"

# Incorrect property usage
class PropertyError:
    @property
    def bad_property(self, value):  # Property setter with wrong signature
        return value

# Using reserved keywords as variables
def reserved_keyword_usage():
    class = "this is a reserved keyword"  # Using 'class' as variable name
    return class

if __name__ == "__main__":
    print("This file contains various Python errors for LSP validation testing.")
    print("It should NOT be executed as it contains intentional errors.")
