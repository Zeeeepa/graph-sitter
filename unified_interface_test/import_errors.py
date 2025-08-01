#!/usr/bin/env python3
"""File with import errors for unified interface testing."""

# Error 1: Non-existent module
import non_existent_module_xyz

# Error 2: Undefined variable
def use_undefined():
    return undefined_variable

# Error 3: Wrong function call
def wrong_call():
    return non_existent_function()
