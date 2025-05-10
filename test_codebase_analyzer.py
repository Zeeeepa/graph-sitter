#!/usr/bin/env python
"""
Test script for codebase_analyzer.py utility functions.

This script demonstrates how to use the utility functions in codebase_analyzer.py
with a mock codebase structure.
"""

import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Import utility functions
from codebase_analyzer import (
    find_all_paths_between_functions,
    get_max_call_chain,
    organize_imports,
    extract_shared_code,
    determine_appropriate_shared_module,
    break_circular_dependencies,
    analyze_module_coupling,
    calculate_type_coverage_percentages
)

# Mock classes to simulate a codebase structure
@dataclass
class MockSymbol:
    name: str
    is_type: bool = False
    is_constant: bool = False
    is_function: bool = False
    usages: List['MockUsage'] = field(default_factory=list)
    
    def move_to_file(self, file, strategy=None):
        print(f"Moving symbol {self.name} to {file.filepath}")
        return True

@dataclass
class MockUsage:
    file: 'MockFile'

@dataclass
class MockImport:
    source: str
    from_file: Optional['MockFile'] = None
    is_standard_library: bool = False
    is_third_party: bool = False
    module_name: str = ""
    
    def remove(self):
        print(f"Removing import: {self.source}")
        return True

@dataclass
class MockParameter:
    name: str
    is_typed: bool = False

@dataclass
class MockReturnType:
    is_typed: bool = False

@dataclass
class MockFunction:
    name: str
    parameters: List[MockParameter] = field(default_factory=list)
    return_type: Optional[MockReturnType] = None
    function_calls: List['MockFunctionCall'] = field(default_factory=list)
    return_statements: List[str] = field(default_factory=list)
    
    def set_return_type(self, type_str):
        print(f"Setting return type of {self.name} to {type_str}")
        self.return_type = MockReturnType(is_typed=True)

@dataclass
class MockFunctionCall:
    name: str
    function_definition: MockFunction
    args: List[str] = field(default_factory=list)

@dataclass
class MockAttribute:
    name: str
    is_typed: bool = False

@dataclass
class MockClass:
    name: str
    attributes: List[MockAttribute] = field(default_factory=list)
    superclasses: List['MockClass'] = field(default_factory=list)

@dataclass
class MockFile:
    filepath: str
    symbols: List[MockSymbol] = field(default_factory=list)
    imports: List[MockImport] = field(default_factory=list)
    functions: List[MockFunction] = field(default_factory=list)
    
    def add_import(self, source):
        print(f"Adding import to {self.filepath}: {source}")
        return True
    
    def insert_after_imports(self, text):
        print(f"Inserting after imports in {self.filepath}: '{text}'")
        return True

@dataclass
class MockCodebase:
    files: List[MockFile] = field(default_factory=list)
    functions: List[MockFunction] = field(default_factory=list)
    classes: List[MockClass] = field(default_factory=list)
    
    def has_directory(self, dir_path):
        return False
    
    def create_directory(self, dir_path):
        print(f"Creating directory: {dir_path}")
        return True
    
    def has_file(self, file_path):
        return any(file.filepath == file_path for file in self.files)
    
    def get_file(self, file_path):
        for file in self.files:
            if file.filepath == file_path:
                return file
        return None
    
    def create_file(self, file_path):
        new_file = MockFile(filepath=file_path)
        self.files.append(new_file)
        print(f"Created file: {file_path}")
        return new_file
    
    def get_function(self, function_name):
        for func in self.functions:
            if func.name == function_name:
                return func
        return None


def create_mock_codebase():
    """Create a mock codebase structure for testing."""
    codebase = MockCodebase()
    
    # Create functions
    main_func = MockFunction(name="main")
    process_data_func = MockFunction(name="process_data")
    validate_input_func = MockFunction(name="validate_input")
    format_output_func = MockFunction(name="format_output")
    save_result_func = MockFunction(name="save_result")
    
    # Create function calls
    main_func.function_calls = [
        MockFunctionCall(name="process_data", function_definition=process_data_func, args=["data"]),
        MockFunctionCall(name="save_result", function_definition=save_result_func, args=["result"])
    ]
    
    process_data_func.function_calls = [
        MockFunctionCall(name="validate_input", function_definition=validate_input_func, args=["data"]),
        MockFunctionCall(name="format_output", function_definition=format_output_func, args=["processed_data"])
    ]
    
    # Add parameters and return types
    main_func.parameters = [MockParameter(name="args", is_typed=True)]
    main_func.return_type = MockReturnType(is_typed=True)
    
    process_data_func.parameters = [MockParameter(name="data", is_typed=False)]
    process_data_func.return_type = MockReturnType(is_typed=False)
    
    validate_input_func.parameters = [MockParameter(name="data", is_typed=True)]
    validate_input_func.return_type = MockReturnType(is_typed=True)
    
    format_output_func.parameters = [MockParameter(name="data", is_typed=False)]
    
    save_result_func.parameters = [MockParameter(name="result", is_typed=True)]
    
    # Add functions to codebase
    codebase.functions = [main_func, process_data_func, validate_input_func, format_output_func, save_result_func]
    
    # Create files
    main_file = MockFile(filepath="app/main.py", functions=[main_func])
    utils_file = MockFile(filepath="app/utils.py", functions=[process_data_func, validate_input_func])
    output_file = MockFile(filepath="app/output.py", functions=[format_output_func, save_result_func])
    
    # Create imports
    main_file.imports = [
        MockImport(source="import sys", is_standard_library=True, module_name="sys"),
        MockImport(source="import os", is_standard_library=True, module_name="os"),
        MockImport(source="from app.utils import process_data", from_file=utils_file, module_name="app.utils"),
        MockImport(source="from app.output import save_result", from_file=output_file, module_name="app.output")
    ]
    
    utils_file.imports = [
        MockImport(source="import json", is_standard_library=True, module_name="json"),
        MockImport(source="from typing import Dict, List", is_standard_library=True, module_name="typing"),
        MockImport(source="from app.output import format_output", from_file=output_file, module_name="app.output")
    ]
    
    output_file.imports = [
        MockImport(source="import os", is_standard_library=True, module_name="os"),
        MockImport(source="from app.utils import validate_input", from_file=utils_file, module_name="app.utils")
    ]
    
    # Create symbols
    user_type = MockSymbol(name="UserType", is_type=True)
    config = MockSymbol(name="CONFIG", is_constant=True)
    helper_func = MockSymbol(name="helper_function", is_function=True)
    
    # Add usages
    user_type.usages = [
        MockUsage(file=main_file),
        MockUsage(file=utils_file),
        MockUsage(file=output_file)
    ]
    
    config.usages = [
        MockUsage(file=main_file),
        MockUsage(file=utils_file)
    ]
    
    helper_func.usages = [
        MockUsage(file=main_file),
        MockUsage(file=utils_file),
        MockUsage(file=output_file)
    ]
    
    # Add symbols to files
    utils_file.symbols = [user_type, config, helper_func]
    
    # Create classes
    base_class = MockClass(name="BaseClass")
    derived_class = MockClass(name="DerivedClass", superclasses=[base_class])
    
    # Add attributes
    base_class.attributes = [
        MockAttribute(name="id", is_typed=True),
        MockAttribute(name="name", is_typed=False)
    ]
    
    derived_class.attributes = [
        MockAttribute(name="extra_data", is_typed=True),
        MockAttribute(name="description", is_typed=False)
    ]
    
    # Add classes to codebase
    codebase.classes = [base_class, derived_class]
    
    # Add files to codebase
    codebase.files = [main_file, utils_file, output_file]
    
    return codebase


def test_find_all_paths_between_functions():
    """Test the find_all_paths_between_functions function."""
    codebase = create_mock_codebase()
    start_func = codebase.get_function("main")
    end_func = codebase.get_function("validate_input")
    
    print("\n=== Testing find_all_paths_between_functions ===")
    paths = find_all_paths_between_functions(start_func, end_func)
    
    print(f"Found {len(paths)} paths between {start_func.name} and {end_func.name}:")
    for i, path in enumerate(paths, 1):
        path_str = " -> ".join([func.name for func in path])
        print(f"  Path {i}: {path_str}")


def test_get_max_call_chain():
    """Test the get_max_call_chain function."""
    codebase = create_mock_codebase()
    start_func = codebase.get_function("main")
    
    print("\n=== Testing get_max_call_chain ===")
    longest_chain = get_max_call_chain(start_func)
    
    print("Longest call chain:")
    chain_str = " -> ".join([func.name for func in longest_chain])
    print(f"  {chain_str}")


def test_organize_imports():
    """Test the organize_imports function."""
    codebase = create_mock_codebase()
    file = codebase.get_file("app/main.py")
    
    print("\n=== Testing organize_imports ===")
    print("Before organization:")
    for imp in file.imports:
        print(f"  {imp.source}")
    
    organize_imports(file)
    
    print("\nAfter organization (simulated):")
    for imp in file.imports:
        print(f"  {imp.source}")


def test_extract_shared_code():
    """Test the extract_shared_code function."""
    codebase = create_mock_codebase()
    
    print("\n=== Testing extract_shared_code ===")
    extracted = extract_shared_code(codebase, min_usages=2)
    
    print("Extracted symbols:")
    for module, symbols in extracted.items():
        print(f"  Module: {module}")
        for symbol in symbols:
            print(f"    - {symbol}")


def test_determine_appropriate_shared_module():
    """Test the determine_appropriate_shared_module function."""
    codebase = create_mock_codebase()
    utils_file = codebase.get_file("app/utils.py")
    
    print("\n=== Testing determine_appropriate_shared_module ===")
    for symbol in utils_file.symbols:
        module = determine_appropriate_shared_module(symbol)
        print(f"  Symbol '{symbol.name}' should go in module: {module}")


def test_break_circular_dependencies():
    """Test the break_circular_dependencies function."""
    codebase = create_mock_codebase()
    
    print("\n=== Testing break_circular_dependencies ===")
    broken_cycles = break_circular_dependencies(codebase)
    
    print(f"Broke {len(broken_cycles)} circular dependencies:")
    for cycle in broken_cycles:
        print(f"  {' -> '.join(cycle)}")


def test_analyze_module_coupling():
    """Test the analyze_module_coupling function."""
    codebase = create_mock_codebase()
    
    print("\n=== Testing analyze_module_coupling ===")
    coupling = analyze_module_coupling(codebase)
    
    print("Module coupling analysis:")
    for file_path, metrics in sorted(coupling.items(), key=lambda x: x[1]['score'], reverse=True):
        print(f"  {file_path}:")
        print(f"    Score: {metrics['score']}")
        print(f"    Afferent coupling: {metrics['afferent']}")
        print(f"    Efferent coupling: {metrics['efferent']}")
        print(f"    Instability: {metrics['instability']:.2f}")


def test_calculate_type_coverage_percentages():
    """Test the calculate_type_coverage_percentages function."""
    codebase = create_mock_codebase()
    
    print("\n=== Testing calculate_type_coverage_percentages ===")
    coverage = calculate_type_coverage_percentages(codebase)
    
    print("Type coverage analysis:")
    print(f"  Overall: {coverage['overall']['percentage']:.1f}% ({coverage['overall']['typed']}/{coverage['overall']['total']})")
    print(f"  Parameters: {coverage['parameters']['percentage']:.1f}% ({coverage['parameters']['typed']}/{coverage['parameters']['total']})")
    print(f"  Return types: {coverage['returns']['percentage']:.1f}% ({coverage['returns']['typed']}/{coverage['returns']['total']})")
    print(f"  Attributes: {coverage['attributes']['percentage']:.1f}% ({coverage['attributes']['typed']}/{coverage['attributes']['total']})")


def main():
    """Run all tests."""
    test_find_all_paths_between_functions()
    test_get_max_call_chain()
    test_organize_imports()
    test_extract_shared_code()
    test_determine_appropriate_shared_module()
    test_break_circular_dependencies()
    test_analyze_module_coupling()
    test_calculate_type_coverage_percentages()


if __name__ == "__main__":
    main()

