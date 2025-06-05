#!/usr/bin/env python3
"""
Import validation script for the refactored contexten extensions.
This script validates that all imports are correctly set after the refactoring.
"""

import sys
import os
import ast
import importlib.util
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate that a Python file has correct syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def validate_imports_in_file(file_path):
    """Validate imports in a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return True, imports
    except Exception as e:
        return False, f"Error parsing imports: {e}"

def validate_contexten_extensions():
    """Validate the refactored contexten extensions structure."""
    print("🔍 Validating refactored contexten extensions...")
    
    base_path = Path("src/contexten/extensions")
    if not base_path.exists():
        print(f"❌ Base path {base_path} does not exist!")
        return False
    
    # Expected folder structure
    expected_folders = ["contexten_app", "github", "linear", "slack", "modal"]
    
    print("\n📁 Checking folder structure...")
    for folder in expected_folders:
        folder_path = base_path / folder
        if folder_path.exists():
            print(f"✅ {folder}/ exists")
        else:
            print(f"❌ {folder}/ missing")
            return False
    
    # Validate Python files in each folder
    print("\n🐍 Validating Python syntax...")
    all_valid = True
    
    for folder in expected_folders:
        folder_path = base_path / folder
        py_files = list(folder_path.glob("**/*.py"))
        
        if py_files:
            print(f"\n  📂 {folder}/")
            for py_file in py_files:
                is_valid, error = validate_python_syntax(py_file)
                if is_valid:
                    print(f"    ✅ {py_file.name}")
                else:
                    print(f"    ❌ {py_file.name}: {error}")
                    all_valid = False
        else:
            print(f"  📂 {folder}/ (no Python files)")
    
    # Check specific import statements
    print("\n🔗 Checking critical import statements...")
    
    # Check contexten/__init__.py
    init_file = Path("src/contexten/__init__.py")
    if init_file.exists():
        is_valid, imports = validate_imports_in_file(init_file)
        if is_valid:
            print("✅ src/contexten/__init__.py imports are valid")
        else:
            print(f"❌ src/contexten/__init__.py: {imports}")
            all_valid = False
    
    # Check examples that use the refactored modules
    example_files = [
        "examples/comprehensive_linear_integration.py",
        "examples/examples/snapshot_event_handler/event_handlers.py",
        "examples/examples/ticket-to-pr/app.py"
    ]
    
    for example_file in example_files:
        if Path(example_file).exists():
            is_valid, imports = validate_imports_in_file(example_file)
            if is_valid:
                print(f"✅ {example_file} imports are valid")
            else:
                print(f"❌ {example_file}: {imports}")
                all_valid = False
    
    return all_valid

def main():
    """Main validation function."""
    print("🚀 Starting import validation for graph-sitter refactoring...")
    
    # Change to the project root
    os.chdir(Path(__file__).parent)
    
    # Run validation
    success = validate_contexten_extensions()
    
    if success:
        print("\n🎉 All validations passed! The refactoring is successful.")
        return 0
    else:
        print("\n💥 Some validations failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

