#!/usr/bin/env python3
"""File with type errors for testing."""

# Error 1: String + int
def string_plus_int():
    return "hello" + 5

# Error 2: Division by zero
def division_by_zero():
    return 10 / 0

# Error 3: Calling non-callable
def call_non_callable():
    x = 5
    return x()

# Error 4: Index error
def index_error():
    lst = [1, 2, 3]
    return lst[10]

# Error 5: Key error
def key_error():
    d = {"a": 1, "b": 2}
    return d["non_existent_key"]

# Error 6: Attribute error
def attribute_error():
    x = 5
    return x.non_existent_method()
