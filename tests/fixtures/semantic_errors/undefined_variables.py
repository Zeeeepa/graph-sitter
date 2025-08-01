# Test fixture for undefined variable semantic errors (S001)
# These should be detected by LSP servers as semantic errors

def test_undefined_variable():
    """Test undefined variable usage."""
    print(undefined_var)  # ERROR: 'undefined_var' is not defined
    return undefined_var

def test_undefined_in_expression():
    """Test undefined variable in expression."""
    x = 5
    result = x + unknown_variable  # ERROR: 'unknown_variable' is not defined
    return result

def test_undefined_in_condition():
    """Test undefined variable in conditional."""
    if missing_condition:  # ERROR: 'missing_condition' is not defined
        return True
    return False

def test_undefined_in_loop():
    """Test undefined variable in loop."""
    for item in undefined_list:  # ERROR: 'undefined_list' is not defined
        print(item)

def test_undefined_function_call():
    """Test undefined function call."""
    result = nonexistent_function()  # ERROR: 'nonexistent_function' is not defined
    return result

def test_undefined_method_call():
    """Test undefined method on object."""
    obj = "hello"
    result = obj.undefined_method()  # ERROR: 'str' object has no attribute 'undefined_method'
    return result

def test_undefined_attribute():
    """Test undefined attribute access."""
    class TestClass:
        def __init__(self):
            self.existing_attr = "exists"
    
    obj = TestClass()
    value = obj.nonexistent_attr  # ERROR: 'TestClass' object has no attribute 'nonexistent_attr'
    return value

def test_undefined_in_assignment():
    """Test undefined variable in assignment."""
    new_var = old_undefined_var + 10  # ERROR: 'old_undefined_var' is not defined
    return new_var

def test_undefined_in_return():
    """Test undefined variable in return statement."""
    return return_undefined_var  # ERROR: 'return_undefined_var' is not defined

def test_undefined_global():
    """Test undefined global variable."""
    global global_undefined
    print(global_undefined)  # ERROR: 'global_undefined' is not defined

def test_undefined_in_f_string():
    """Test undefined variable in f-string."""
    name = "World"
    message = f"Hello {undefined_name}!"  # ERROR: 'undefined_name' is not defined
    return message

def test_undefined_in_list_comprehension():
    """Test undefined variable in list comprehension."""
    squares = [x**2 for x in undefined_range]  # ERROR: 'undefined_range' is not defined
    return squares

def test_undefined_in_lambda():
    """Test undefined variable in lambda."""
    func = lambda x: x + undefined_constant  # ERROR: 'undefined_constant' is not defined
    return func

# Expected LSP diagnostics:
# - Error at line 5: NameError: name 'undefined_var' is not defined
# - Error at line 6: NameError: name 'undefined_var' is not defined
# - Error at line 11: NameError: name 'unknown_variable' is not defined
# - Error at line 16: NameError: name 'missing_condition' is not defined
# - Error at line 21: NameError: name 'undefined_list' is not defined
# - Error at line 26: NameError: name 'nonexistent_function' is not defined
# - Error at line 31: AttributeError: 'str' object has no attribute 'undefined_method'
# - Error at line 40: AttributeError: 'TestClass' object has no attribute 'nonexistent_attr'
# - Error at line 44: NameError: name 'old_undefined_var' is not defined
# - Error at line 48: NameError: name 'return_undefined_var' is not defined
# - Error at line 53: NameError: name 'global_undefined' is not defined
# - Error at line 58: NameError: name 'undefined_name' is not defined
# - Error at line 63: NameError: name 'undefined_range' is not defined
# - Error at line 68: NameError: name 'undefined_constant' is not defined

