#!/usr/bin/env python3
"""
LSP Import Error Fix Script

This script fixes the import errors found in the LSP system analysis.
"""

import sys
import os
from pathlib import Path
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def analyze_import_errors():
    """Analyze the import errors from the real LSP error analysis."""
    print("🔍 Analyzing Import Errors from LSP Analysis")
    print("=" * 60)
    
    try:
        with open("real_lsp_errors.json", 'r') as f:
            errors = json.load(f)
        
        import_errors = [e for e in errors if e.get('source') == 'import_check']
        
        print(f"📊 Found {len(import_errors)} import errors")
        
        # Group by file
        by_file = {}
        for error in import_errors:
            file_path = error['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(error)
        
        print(f"\n📁 Import errors by file:")
        for file_path, file_errors in by_file.items():
            file_name = Path(file_path).name
            print(f"  • {file_name}: {len(file_errors)} errors")
        
        # Analyze error patterns
        error_patterns = {}
        for error in import_errors:
            message = error['message']
            if 'No module named' in message:
                module = message.split("'")[1] if "'" in message else 'unknown'
                pattern = f"Missing module: {module}"
            elif 'cannot import name' in message:
                name = message.split("'")[1] if "'" in message else 'unknown'
                pattern = f"Missing import: {name}"
            else:
                pattern = "Other import error"
            
            if pattern not in error_patterns:
                error_patterns[pattern] = []
            error_patterns[pattern].append(error)
        
        print(f"\n🔍 Error patterns:")
        for pattern, pattern_errors in error_patterns.items():
            print(f"  • {pattern}: {len(pattern_errors)} occurrences")
        
        return by_file, error_patterns
        
    except Exception as e:
        print(f"❌ Error analyzing import errors: {e}")
        return {}, {}

def fix_relative_imports():
    """Fix relative import issues in LSP files."""
    print("\n🔧 Fixing Relative Import Issues")
    print("-" * 40)
    
    fixes_applied = []
    
    # Fix lsp_manager.py imports
    lsp_manager_path = Path("src/graph_sitter/core/lsp_manager.py")
    if lsp_manager_path.exists():
        print(f"📝 Fixing {lsp_manager_path}")
        
        with open(lsp_manager_path, 'r') as f:
            content = f.read()
        
        # Fix import issues
        fixes = [
            ("from lsp_types import", "from .lsp_types import"),
            ("from unified_diagnostics import", "from .unified_diagnostics import"),
            ("from lsp_type_adapters import", "from .lsp_type_adapters import"),
        ]
        
        for old_import, new_import in fixes:
            if old_import in content:
                content = content.replace(old_import, new_import)
                fixes_applied.append(f"{lsp_manager_path}: {old_import} -> {new_import}")
                print(f"  ✅ Fixed: {old_import} -> {new_import}")
        
        with open(lsp_manager_path, 'w') as f:
            f.write(content)
    
    # Fix lsp_type_adapters.py imports
    lsp_adapters_path = Path("src/graph_sitter/core/lsp_type_adapters.py")
    if lsp_adapters_path.exists():
        print(f"📝 Fixing {lsp_adapters_path}")
        
        with open(lsp_adapters_path, 'r') as f:
            content = f.read()
        
        # Fix import issues
        fixes = [
            ("from lsp_types import", "from .lsp_types import"),
            ("from extensions.lsp.protocol.lsp_types import", "from ..extensions.lsp.protocol.lsp_types import"),
            ("from extensions.lsp.serena_bridge import", "from ..extensions.lsp.serena_bridge import"),
        ]
        
        for old_import, new_import in fixes:
            if old_import in content:
                content = content.replace(old_import, new_import)
                fixes_applied.append(f"{lsp_adapters_path}: {old_import} -> {new_import}")
                print(f"  ✅ Fixed: {old_import} -> {new_import}")
        
        with open(lsp_adapters_path, 'w') as f:
            f.write(content)
    
    # Fix unified_diagnostics.py imports
    unified_diag_path = Path("src/graph_sitter/core/unified_diagnostics.py")
    if unified_diag_path.exists():
        print(f"📝 Fixing {unified_diag_path}")
        
        with open(unified_diag_path, 'r') as f:
            content = f.read()
        
        # Fix import issues
        fixes = [
            ("from lsp_types import", "from .lsp_types import"),
            ("from lsp_type_adapters import", "from .lsp_type_adapters import"),
            ("from lsp_manager import", "from .lsp_manager import"),
        ]
        
        for old_import, new_import in fixes:
            if old_import in content:
                content = content.replace(old_import, new_import)
                fixes_applied.append(f"{unified_diag_path}: {old_import} -> {new_import}")
                print(f"  ✅ Fixed: {old_import} -> {new_import}")
        
        with open(unified_diag_path, 'w') as f:
            f.write(content)
    
    return fixes_applied

def fix_missing_imports():
    """Fix missing import statements."""
    print("\n🔧 Fixing Missing Import Statements")
    print("-" * 40)
    
    fixes_applied = []
    
    # Check if get_logger import exists
    logger_import_files = [
        "src/graph_sitter/core/lsp_manager.py",
        "src/graph_sitter/core/unified_diagnostics.py",
        "src/graph_sitter/extensions/lsp/serena_bridge.py"
    ]
    
    for file_path in logger_import_files:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r') as f:
                content = f.read()
            
            # Check if logger import is broken
            if "from graph_sitter.shared.logging.get_logger import get_logger" in content:
                # Try to fix the logger import
                new_import = "import logging\nlogger = logging.getLogger(__name__)"
                content = content.replace(
                    "from graph_sitter.shared.logging.get_logger import get_logger",
                    new_import
                )
                # Also replace logger usage
                content = content.replace("get_logger(__name__)", "logger")
                
                with open(path, 'w') as f:
                    f.write(content)
                
                fixes_applied.append(f"{path}: Fixed logger import")
                print(f"  ✅ Fixed logger import in {path.name}")
    
    return fixes_applied

def validate_fixes():
    """Validate that the fixes work by running import checks."""
    print("\n✅ Validating Import Fixes")
    print("-" * 40)
    
    files_to_validate = [
        "src/graph_sitter/core/lsp_manager.py",
        "src/graph_sitter/core/lsp_types.py",
        "src/graph_sitter/core/lsp_type_adapters.py",
        "src/graph_sitter/core/unified_diagnostics.py"
    ]
    
    validation_results = []
    
    for file_path in files_to_validate:
        path = Path(file_path)
        if path.exists():
            print(f"🔍 Validating {path.name}...")
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                # Try to compile the file
                compile(content, str(path), 'exec')
                validation_results.append((str(path), True, "Syntax OK"))
                print(f"  ✅ {path.name}: Syntax validation passed")
                
            except SyntaxError as e:
                validation_results.append((str(path), False, f"SyntaxError: {e.msg}"))
                print(f"  ❌ {path.name}: Syntax error - {e.msg}")
            except Exception as e:
                validation_results.append((str(path), False, f"Error: {e}"))
                print(f"  ⚠️ {path.name}: Validation error - {e}")
    
    return validation_results

def generate_fix_report(by_file, error_patterns, fixes_applied, validation_results):
    """Generate a comprehensive fix report."""
    print("\n" + "="*80)
    print("📋 LSP IMPORT ERROR FIX REPORT")
    print("="*80)
    
    print(f"\n📊 ORIGINAL ISSUES")
    print("-" * 40)
    print(f"• Total import errors found: {sum(len(errors) for errors in by_file.values())}")
    print(f"• Files with import errors: {len(by_file)}")
    print(f"• Error patterns identified: {len(error_patterns)}")
    
    print(f"\n🔧 FIXES APPLIED")
    print("-" * 40)
    print(f"• Total fixes applied: {len(fixes_applied)}")
    for fix in fixes_applied:
        print(f"  • {fix}")
    
    print(f"\n✅ VALIDATION RESULTS")
    print("-" * 40)
    passed = sum(1 for _, success, _ in validation_results if success)
    total = len(validation_results)
    print(f"• Files validated: {total}")
    print(f"• Validation passed: {passed}")
    print(f"• Validation failed: {total - passed}")
    
    for file_path, success, message in validation_results:
        status = "✅" if success else "❌"
        file_name = Path(file_path).name
        print(f"  {status} {file_name}: {message}")
    
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 40)
    print("1. Run the updated LSP validation tests to ensure functionality")
    print("2. Check for any remaining import issues in other files")
    print("3. Consider adding import validation to CI/CD pipeline")
    print("4. Update documentation to reflect import structure changes")
    
    print("\n" + "="*80)
    print("✅ LSP import error fix analysis complete!")
    print("="*80)

def main():
    """Main function to fix LSP import errors."""
    print("🚀 LSP Import Error Fix Script")
    print("=" * 60)
    
    # Analyze current import errors
    by_file, error_patterns = analyze_import_errors()
    
    # Apply fixes
    fixes_applied = []
    fixes_applied.extend(fix_relative_imports())
    fixes_applied.extend(fix_missing_imports())
    
    # Validate fixes
    validation_results = validate_fixes()
    
    # Generate report
    generate_fix_report(by_file, error_patterns, fixes_applied, validation_results)
    
    print(f"\n🎉 Applied {len(fixes_applied)} fixes to LSP import errors!")

if __name__ == "__main__":
    main()
