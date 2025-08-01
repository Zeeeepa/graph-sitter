#!/usr/bin/env python3
"""File with type errors for unified interface testing."""

def type_errors():
    # Error 1: String + int
    result = "hello" + 5
    
    # Error 2: Invalid indexing
    my_list = [1, 2, 3]
    item = my_list["invalid"]
    
    return result, item
