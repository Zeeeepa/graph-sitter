# Test fixture for missing brackets/parentheses syntax errors (E004, E005)
# These should be detected by LSP servers as syntax errors

# Missing closing parenthesis in function call
def test_missing_closing_paren():
    result = print("Hello World"  # ERROR: Missing closing parenthesis
    return result

# Missing opening parenthesis in function call
def test_missing_opening_paren():
    result = print "Hello World")  # ERROR: Missing opening parenthesis
    return result

# Missing closing bracket in list
def test_missing_closing_bracket():
    items = [1, 2, 3, 4, 5  # ERROR: Missing closing bracket
    return items

# Missing opening bracket in list
def test_missing_opening_bracket():
    items = 1, 2, 3, 4, 5]  # ERROR: Missing opening bracket
    return items

# Missing closing brace in dictionary
def test_missing_closing_brace():
    data = {"key1": "value1", "key2": "value2"  # ERROR: Missing closing brace
    return data

# Missing opening brace in dictionary
def test_missing_opening_brace():
    data = "key1": "value1", "key2": "value2"}  # ERROR: Missing opening brace
    return data

# Nested missing brackets
def test_nested_missing_brackets():
    result = max([1, 2, 3], [4, 5, 6  # ERROR: Missing closing bracket and parenthesis
    return result

# Missing parenthesis in function definition
def test_missing_paren_in_def(param1, param2  # ERROR: Missing closing parenthesis
    return param1 + param2

# Missing bracket in list comprehension
def test_missing_bracket_comprehension():
    squares = [x**2 for x in range(10)  # ERROR: Missing closing bracket
    return squares

# Missing parenthesis in tuple
def test_missing_paren_tuple():
    coordinates = (10, 20, 30  # ERROR: Missing closing parenthesis
    return coordinates

# Expected LSP diagnostics:
# - Error at line 5: SyntaxError: '(' was never closed
# - Error at line 9: SyntaxError: invalid syntax
# - Error at line 13: SyntaxError: '[' was never closed
# - Error at line 17: SyntaxError: invalid syntax
# - Error at line 21: SyntaxError: '{' was never closed
# - Error at line 25: SyntaxError: invalid syntax
# - Error at line 29: SyntaxError: '(' was never closed
# - Error at line 32: SyntaxError: '(' was never closed
# - Error at line 36: SyntaxError: '[' was never closed
# - Error at line 40: SyntaxError: '(' was never closed

