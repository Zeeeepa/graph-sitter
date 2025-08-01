# Test fixture for missing colon syntax errors (E001)
# These should be detected by LSP servers as syntax errors

# Missing colon after if statement
def test_missing_colon_if():
    x = 5
    if x > 3  # ERROR: Missing colon
        print("x is greater than 3")

# Missing colon after for loop
def test_missing_colon_for():
    items = [1, 2, 3]
    for item in items  # ERROR: Missing colon
        print(item)

# Missing colon after while loop
def test_missing_colon_while():
    count = 0
    while count < 5  # ERROR: Missing colon
        count += 1

# Missing colon after function definition
def test_missing_colon_function()  # ERROR: Missing colon
    return "Hello World"

# Missing colon after class definition
class TestClass  # ERROR: Missing colon
    def __init__(self):
        pass

# Missing colon after try/except
def test_missing_colon_try():
    try  # ERROR: Missing colon
        x = 1 / 0
    except ZeroDivisionError:
        print("Division by zero")

# Missing colon after except
def test_missing_colon_except():
    try:
        x = 1 / 0
    except ZeroDivisionError  # ERROR: Missing colon
        print("Division by zero")

# Missing colon after with statement
def test_missing_colon_with():
    with open("test.txt", "r") as f  # ERROR: Missing colon
        content = f.read()

# Expected LSP diagnostics:
# - Error at line 6: SyntaxError: invalid syntax
# - Error at line 11: SyntaxError: invalid syntax  
# - Error at line 16: SyntaxError: invalid syntax
# - Error at line 20: SyntaxError: invalid syntax
# - Error at line 23: SyntaxError: invalid syntax
# - Error at line 28: SyntaxError: invalid syntax
# - Error at line 33: SyntaxError: invalid syntax
# - Error at line 38: SyntaxError: invalid syntax

