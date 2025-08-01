# Test fixture for LSP false positives (F001, F002, F003, F010, F011, F012, F020, F021)
# These are patterns that LSP servers might incorrectly flag as errors

import sys
import types
from typing import Any, Dict

# F001: Temporary parsing errors during server startup
# These might show as errors initially but resolve after full indexing
def startup_sensitive_function():
    """Function that might show false errors during LSP startup."""
    # Complex imports that take time to resolve
    from collections.abc import Mapping
    from importlib import import_module
    
    # Dynamic module loading
    module_name = "json"
    module = import_module(module_name)
    return module.dumps({"test": "data"})

# F002: Incomplete indexing causing false undefined references
class DynamicClass:
    """Class with dynamic attributes that might confuse LSP."""
    
    def __init__(self):
        # Dynamic attribute creation
        for i in range(5):
            setattr(self, f"attr_{i}", i)
    
    def get_dynamic_attr(self, name: str):
        # This might show as error until LSP fully indexes
        return getattr(self, name, None)

# F010: Dynamic attribute access patterns
class DynamicAttributeAccess:
    """Class demonstrating dynamic attribute patterns."""
    
    def __init__(self):
        self.data = {"key1": "value1", "key2": "value2"}
    
    def __getattr__(self, name: str) -> Any:
        """Dynamic attribute access - LSP might flag as error."""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Dynamic attribute setting."""
        if name == "data":
            super().__setattr__(name, value)
        else:
            if not hasattr(self, "data"):
                super().__setattr__("data", {})
            self.data[name] = value

# F011: Metaprogramming patterns
class MetaClass(type):
    """Metaclass that creates dynamic methods."""
    
    def __new__(cls, name, bases, attrs):
        # Dynamic method creation
        for i in range(3):
            method_name = f"dynamic_method_{i}"
            attrs[method_name] = lambda self, x=i: f"Method {x} called"
        
        return super().__new__(cls, name, bases, attrs)

class DynamicMethodClass(metaclass=MetaClass):
    """Class with dynamically created methods."""
    pass

# F012: Runtime code generation
def create_function(name: str, operation: str):
    """Create function at runtime - LSP might not understand."""
    code = f"""
def {name}(x, y):
    return x {operation} y
"""
    
    namespace = {}
    exec(code, namespace)
    return namespace[name]

# F020: Python __getattr__ magic methods
class MagicMethodClass:
    """Class with magic methods that confuse static analysis."""
    
    def __init__(self):
        self._data = {}
    
    def __getattr__(self, name: str) -> Any:
        """Magic method - LSP might not understand dynamic access."""
        if name.startswith("get_"):
            key = name[4:]  # Remove "get_" prefix
            return lambda: self._data.get(key, f"No data for {key}")
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access."""
        return self._data.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-like setting."""
        self._data[key] = value

# F013: Monkey patching
def monkey_patch_example():
    """Monkey patching that LSP might not track."""
    # Add method to existing class
    def new_method(self):
        return "Monkey patched method"
    
    # This might confuse LSP
    str.monkey_method = new_method
    
    # Usage that might show as error
    result = "test".monkey_method()
    return result

# F003: Cache invalidation causing temporary errors
_cache = {}

def cached_function(key: str) -> Any:
    """Function with caching that might cause temporary LSP errors."""
    if key not in _cache:
        # Complex computation that might not be immediately available to LSP
        _cache[key] = globals().get(key, f"computed_{key}")
    
    return _cache[key]

# Conditional imports that might confuse LSP
try:
    # This might show as error if LSP doesn't understand the try/except
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    # Create mock numpy for type checking
    class MockNumpy:
        def array(self, data):
            return list(data)
    
    np = MockNumpy()
    HAS_NUMPY = False

def use_conditional_import():
    """Use conditionally imported module."""
    # LSP might flag this as error if it doesn't track the conditional import
    if HAS_NUMPY:
        return np.array([1, 2, 3])
    else:
        return [1, 2, 3]

# Dynamic module attribute access
def dynamic_module_access():
    """Access module attributes dynamically."""
    module_name = "sys"
    attr_name = "version"
    
    # LSP might not understand this dynamic access
    module = sys.modules[module_name]
    value = getattr(module, attr_name)
    return value

# Property decorators that might confuse LSP
class PropertyClass:
    """Class with complex property patterns."""
    
    def __init__(self):
        self._value = 0
    
    @property
    def computed_property(self) -> int:
        """Property that LSP might not immediately understand."""
        # Complex computation
        return self._value * 2 + 1
    
    @computed_property.setter
    def computed_property(self, value: int) -> None:
        """Setter that might confuse LSP."""
        self._value = (value - 1) // 2

# Usage examples that might trigger false positives
def test_false_positive_patterns():
    """Test usage of patterns that might trigger false positives."""
    
    # Dynamic attribute access
    obj = DynamicAttributeAccess()
    obj.dynamic_key = "dynamic_value"
    value = obj.dynamic_key  # Might show as error
    
    # Magic method usage
    magic_obj = MagicMethodClass()
    magic_obj["key"] = "value"
    getter = magic_obj.get_key()  # Might show as error
    
    # Dynamic method usage
    dynamic_obj = DynamicMethodClass()
    result = dynamic_obj.dynamic_method_0()  # Might show as error
    
    # Runtime function usage
    add_func = create_function("add", "+")
    sum_result = add_func(5, 3)  # Might show as error
    
    # Conditional import usage
    array_result = use_conditional_import()  # Might show as error
    
    return value, getter, result, sum_result, array_result

# Expected behavior:
# - These patterns should NOT be flagged as errors by a sophisticated LSP system
# - A naive LSP might incorrectly flag many of these as errors
# - The false positive detection system should recognize these patterns
# - Confidence scores should be lower for these "errors"
# - Context analysis should reveal these are legitimate Python patterns

