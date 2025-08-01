#!/usr/bin/env python3
"""File with intentional syntax errors for LSP testing."""

# Error 1: Missing colon in function definition
def function_missing_colon()
    return "This should cause a syntax error"

# Error 2: Invalid indentation
def function_with_bad_indentation():
return "Wrong indentation"

# Error 3: Unclosed parenthesis
def function_unclosed_paren():
    result = some_function(arg1, arg2
    return result

# Error 4: Invalid syntax - missing quotes
def function_missing_quotes():
    message = Hello World
    return message

# Error 5: Invalid operator
def function_invalid_operator():
    result = 5 ++ 3
    return result
