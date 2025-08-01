#!/usr/bin/env python3
"""File with type errors for LSP testing."""

def type_mismatch_function():
    # Error 1: String + int
    result = "hello" + 5
    return result

def list_index_error():
    # Error 2: Invalid list indexing
    my_list = [1, 2, 3]
    return my_list["invalid_index"]

def dict_key_error():
    # Error 3: Missing dictionary key
    my_dict = {"a": 1, "b": 2}
    return my_dict["c"]

def function_call_error():
    # Error 4: Calling non-callable
    my_var = 42
    return my_var()

def attribute_error():
    # Error 5: Invalid attribute access
    my_string = "hello"
    return my_string.invalid_method()
