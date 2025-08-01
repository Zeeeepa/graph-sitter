# Test fixture for type mismatch errors (T001, T002, T003, T004)
# These should be detected by type checkers like mypy, pyright

from typing import List, Dict, Optional

def test_assignment_type_mismatch():
    """Test incompatible assignment types."""
    x: int = "hello"  # ERROR: Cannot assign str to int
    y: str = 42  # ERROR: Cannot assign int to str
    z: List[int] = ["a", "b", "c"]  # ERROR: Cannot assign List[str] to List[int]
    return x, y, z

def test_function_argument_type_mismatch():
    """Test wrong function argument types."""
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    result1 = add_numbers("5", "10")  # ERROR: Cannot pass str arguments to int parameters
    result2 = add_numbers(5.5, 10.5)  # ERROR: Cannot pass float arguments to int parameters
    result3 = add_numbers([1, 2], [3, 4])  # ERROR: Cannot pass list arguments to int parameters
    return result1, result2, result3

def test_return_type_mismatch():
    """Test wrong return types."""
    def get_number() -> int:
        return "not a number"  # ERROR: Cannot return str when int expected
    
    def get_string() -> str:
        return 42  # ERROR: Cannot return int when str expected
    
    def get_list() -> List[str]:
        return [1, 2, 3]  # ERROR: Cannot return List[int] when List[str] expected
    
    return get_number(), get_string(), get_list()

def test_operator_type_mismatch():
    """Test incompatible operand types."""
    result1 = "hello" + 42  # ERROR: Cannot add str and int
    result2 = [1, 2, 3] - [1]  # ERROR: Cannot subtract lists
    result3 = "text" * "repeat"  # ERROR: Cannot multiply str by str
    result4 = {"a": 1} + {"b": 2}  # ERROR: Cannot add dictionaries
    return result1, result2, result3, result4

def test_comparison_type_mismatch():
    """Test incompatible comparison types."""
    result1 = "hello" > 42  # ERROR: Cannot compare str and int
    result2 = [1, 2] < "abc"  # ERROR: Cannot compare list and str
    result3 = {"a": 1} == [1, 2]  # WARNING: Comparing different types
    return result1, result2, result3

def test_container_type_mismatch():
    """Test container type mismatches."""
    numbers: List[int] = []
    numbers.append("string")  # ERROR: Cannot append str to List[int]
    
    mapping: Dict[str, int] = {}
    mapping[42] = "value"  # ERROR: Cannot use int key in Dict[str, int]
    mapping["key"] = "value"  # ERROR: Cannot assign str value to Dict[str, int]
    
    return numbers, mapping

def test_optional_type_mismatch():
    """Test Optional type handling."""
    def process_optional(value: Optional[str]) -> str:
        return value.upper()  # ERROR: Optional[str] might be None
    
    def require_string(text: str) -> str:
        return text.upper()
    
    optional_value: Optional[str] = None
    result = require_string(optional_value)  # ERROR: Cannot pass Optional[str] to str parameter
    return result

def test_generic_type_mismatch():
    """Test generic type mismatches."""
    from typing import TypeVar, Generic
    
    T = TypeVar('T')
    
    class Container(Generic[T]):
        def __init__(self, value: T):
            self.value = value
        
        def get(self) -> T:
            return self.value
    
    int_container: Container[int] = Container("string")  # ERROR: Cannot pass str to Container[int]
    str_container: Container[str] = Container(42)  # ERROR: Cannot pass int to Container[str]
    
    return int_container, str_container

def test_callable_type_mismatch():
    """Test callable type mismatches."""
    from typing import Callable
    
    def process_callback(callback: Callable[[int], str]) -> str:
        return callback(42)
    
    def wrong_callback(x: str) -> int:  # ERROR: Wrong parameter type
        return len(x)
    
    def another_wrong_callback(x: int) -> int:  # ERROR: Wrong return type
        return x * 2
    
    result1 = process_callback(wrong_callback)  # ERROR: Incompatible callback type
    result2 = process_callback(another_wrong_callback)  # ERROR: Incompatible callback type
    return result1, result2

# Expected LSP diagnostics (mypy/pyright):
# - Error at line 7: Incompatible types in assignment (expression has type "str", variable has type "int")
# - Error at line 8: Incompatible types in assignment (expression has type "int", variable has type "str")  
# - Error at line 9: List item 0 has incompatible type "str"; expected "int"
# - Error at line 16: Argument 1 to "add_numbers" has incompatible type "str"; expected "int"
# - Error at line 17: Argument 1 to "add_numbers" has incompatible type "float"; expected "int"
# - Error at line 18: Argument 1 to "add_numbers" has incompatible type "List[int]"; expected "int"
# - Error at line 23: Incompatible return value type (got "str", expected "int")
# - Error at line 26: Incompatible return value type (got "int", expected "str")
# - Error at line 29: List item 0 has incompatible type "int"; expected "str"
# - Error at line 34: Unsupported operand types for + ("str" and "int")
# - Error at line 35: Unsupported operand types for - ("List[int]" and "List[int]")
# - Error at line 36: Unsupported operand types for * ("str" and "str")
# - Error at line 37: Unsupported operand types for + ("Dict[str, int]" and "Dict[str, int]")
# - Error at line 42: Unsupported operand types for > ("str" and "int")
# - Error at line 43: Unsupported operand types for < ("List[int]" and "str")
# - Error at line 49: Argument 1 to "append" of "list" has incompatible type "str"; expected "int"
# - Error at line 52: Invalid index type "int" for "Dict[str, int]"; expected type "str"
# - Error at line 53: Incompatible types in assignment (expression has type "str", target has type "int")
# - Error at line 58: Item "None" of "Optional[str]" has no attribute "upper"
# - Error at line 64: Argument 1 to "require_string" has incompatible type "Optional[str]"; expected "str"
# - Error at line 78: Argument 1 to "Container" has incompatible type "str"; expected "int"
# - Error at line 79: Argument 1 to "Container" has incompatible type "int"; expected "str"
# - Error at line 92: Argument 1 to "process_callback" has incompatible type "Callable[[str], int]"; expected "Callable[[int], str]"
# - Error at line 93: Argument 1 to "process_callback" has incompatible type "Callable[[int], int]"; expected "Callable[[int], str]"

