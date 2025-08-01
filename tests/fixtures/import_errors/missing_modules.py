# Test fixture for missing module import errors (I001, I002, I003, I004)
# These should be detected by LSP servers as import errors

# Missing standard library module (typo)
import oss  # ERROR: No module named 'oss' (should be 'os')
import jsoon  # ERROR: No module named 'jsoon' (should be 'json')
import regx  # ERROR: No module named 'regx' (should be 're')

# Missing third-party package
import nonexistent_package  # ERROR: No module named 'nonexistent_package'
import fake_library  # ERROR: No module named 'fake_library'
import missing_dependency  # ERROR: No module named 'missing_dependency'

# Missing submodule
from os import nonexistent_submodule  # ERROR: cannot import name 'nonexistent_submodule' from 'os'
from json import fake_function  # ERROR: cannot import name 'fake_function' from 'json'
from sys import missing_attribute  # ERROR: cannot import name 'missing_attribute' from 'sys'

# Relative import beyond top-level package
from ...nonexistent import something  # ERROR: attempted relative import beyond top-level package
from ....parent import module  # ERROR: attempted relative import beyond top-level package

# Import from non-existent local module
from .missing_local_module import function  # ERROR: No module named 'missing_local_module'
from ..missing_parent_module import class_name  # ERROR: No module named 'missing_parent_module'

# Import with typos in module names
from collections import defaultdic  # ERROR: cannot import name 'defaultdic' from 'collections' (should be 'defaultdict')
from itertools import chian  # ERROR: cannot import name 'chian' from 'itertools' (should be 'chain')
from functools import reduc  # ERROR: cannot import name 'reduc' from 'functools' (should be 'reduce')

# Import from wrong module
from os import requests  # ERROR: cannot import name 'requests' from 'os'
from json import pandas  # ERROR: cannot import name 'pandas' from 'json'
from sys import numpy  # ERROR: cannot import name 'numpy' from 'sys'

# Conditional imports that might fail
import platform
if platform.system() == "Windows":
    import winsound  # This might be missing on non-Windows systems
    import msvcrt
else:
    import termios  # This might be missing on Windows
    import tty

# Try to import optional dependencies
try:
    import optional_missing_package  # ERROR: No module named 'optional_missing_package'
except ImportError:
    optional_missing_package = None

try:
    from optional_package import missing_function  # ERROR: No module named 'optional_package'
except ImportError:
    missing_function = None

# Import with alias from missing module
import nonexistent as ne  # ERROR: No module named 'nonexistent'
from missing_module import function as func  # ERROR: No module named 'missing_module'

# Multiple imports with some missing
from os import path, environ, missing_var  # ERROR: cannot import name 'missing_var' from 'os'
from sys import argv, path as sys_path, nonexistent_attr  # ERROR: cannot import name 'nonexistent_attr' from 'sys'

# Star import from missing module
from missing_star_module import *  # ERROR: No module named 'missing_star_module'

def test_usage_of_missing_imports():
    """Test usage of missing imports to trigger additional errors."""
    # These will cause additional NameError if imports fail
    result1 = oss.getcwd()  # ERROR: 'oss' is not defined
    result2 = jsoon.dumps({"key": "value"})  # ERROR: 'jsoon' is not defined
    result3 = nonexistent_package.some_function()  # ERROR: 'nonexistent_package' is not defined
    result4 = ne.some_method()  # ERROR: 'ne' is not defined
    
    return result1, result2, result3, result4

# Expected LSP diagnostics:
# - Error at line 5: ModuleNotFoundError: No module named 'oss'
# - Error at line 6: ModuleNotFoundError: No module named 'jsoon'
# - Error at line 7: ModuleNotFoundError: No module named 'regx'
# - Error at line 10: ModuleNotFoundError: No module named 'nonexistent_package'
# - Error at line 11: ModuleNotFoundError: No module named 'fake_library'
# - Error at line 12: ModuleNotFoundError: No module named 'missing_dependency'
# - Error at line 15: ImportError: cannot import name 'nonexistent_submodule' from 'os'
# - Error at line 16: ImportError: cannot import name 'fake_function' from 'json'
# - Error at line 17: ImportError: cannot import name 'missing_attribute' from 'sys'
# - Error at line 20: ImportError: attempted relative import beyond top-level package
# - Error at line 21: ImportError: attempted relative import beyond top-level package
# - Error at line 24: ModuleNotFoundError: No module named 'missing_local_module'
# - Error at line 25: ModuleNotFoundError: No module named 'missing_parent_module'
# - Error at line 28: ImportError: cannot import name 'defaultdic' from 'collections'
# - Error at line 29: ImportError: cannot import name 'chian' from 'itertools'
# - Error at line 30: ImportError: cannot import name 'reduc' from 'functools'
# - Error at line 33: ImportError: cannot import name 'requests' from 'os'
# - Error at line 34: ImportError: cannot import name 'pandas' from 'json'
# - Error at line 35: ImportError: cannot import name 'numpy' from 'sys'
# - Error at line 44: ModuleNotFoundError: No module named 'optional_missing_package'
# - Error at line 49: ModuleNotFoundError: No module named 'optional_package'
# - Error at line 54: ModuleNotFoundError: No module named 'nonexistent'
# - Error at line 55: ModuleNotFoundError: No module named 'missing_module'
# - Error at line 58: ImportError: cannot import name 'missing_var' from 'os'
# - Error at line 59: ImportError: cannot import name 'nonexistent_attr' from 'sys'
# - Error at line 62: ModuleNotFoundError: No module named 'missing_star_module'
# - Error at line 67: NameError: name 'oss' is not defined
# - Error at line 68: NameError: name 'jsoon' is not defined
# - Error at line 69: NameError: name 'nonexistent_package' is not defined
# - Error at line 70: NameError: name 'ne' is not defined

