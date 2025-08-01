#!/usr/bin/env python3
"""File with import and name errors for testing."""

# Error 1: Import non-existent module
import non_existent_module_12345

# Error 2: Import from non-existent module
from another_fake_module import fake_function

# Error 3: Undefined variable
def use_undefined_variable():
    return undefined_variable_name

# Error 4: Undefined function call
def call_undefined_function():
    return some_undefined_function()

# Error 5: Wrong number of arguments
def add_two_numbers(a, b):
    return a + b

def call_with_wrong_args():
    return add_two_numbers(1, 2, 3, 4)  # Too many args

# Error 6: Accessing undefined attribute
class TestClass:
    def __init__(self):
        self.value = 10

def access_undefined_attr():
    obj = TestClass()
    return obj.non_existent_attribute
