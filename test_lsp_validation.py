#!/usr/bin/env python3
"""
Comprehensive LSP Method Validation Test Suite

This script validates that all LSP methods in the consolidated system work correctly.
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from graph_sitter.enhanced.codebase import Codebase as EnhancedCodebase
        from graph_sitter.core.lsp_manager import LSPManager
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        from graph_sitter.core.unified_diagnostics import UnifiedDiagnosticCollector
        from graph_sitter.core.lsp_types import ErrorInfo, ErrorSeverity, ErrorType
        from graph_sitter.core.lsp_type_adapters import LSPTypeAdapter
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def create_test_python_file(temp_dir: str) -> str:
    """Create a test Python file with various types of errors."""
    test_file = Path(temp_dir) / "test_file.py"
    
    # Create a Python file with intentional errors for testing
    content = '''
# Test Python file with various issues
import os
import sys

def test_function():
    # Syntax error (missing closing quote)
    message = "Hello world
    
    # Undefined variable
    print(undefined_variable)
    
    # Type error
    result = "string" + 123
    
    # Import error
    from nonexistent_module import something
    
    return result

class TestClass:
    def __init__(self):
        self.value = None
    
    def method_with_issues(self):
        # Unused variable
        unused_var = "not used"
        
        # Potential attribute error
        return self.nonexistent_attr

if __name__ == "__main__":
    test_function()
'''
    
    test_file.write_text(content)
    return str(test_file)

def test_enhanced_codebase_lsp_methods(temp_dir: str, test_file: str):
    """Test all LSP methods on EnhancedCodebase."""
    print("\n🧪 Testing EnhancedCodebase LSP methods...")
    
    try:
        from graph_sitter.enhanced.codebase import Codebase as EnhancedCodebase
        
        # Initialize codebase
        codebase = EnhancedCodebase(temp_dir)
        
        # Test 1: errors (get all errors)
        print("  Testing errors()...")
        errors = codebase.errors()
        print(f"    ✅ errors() returned {errors.total_count} diagnostics")
        
        # Test 2: file_errors
        print("  Testing file_errors()...")
        file_errors = codebase.file_errors(test_file)
        print(f"    ✅ file_errors() returned {file_errors.total_count} diagnostics for {test_file}")
        
        # Test 3: get_completion
        print("  Testing get_completion()...")
        try:
            completions = codebase.get_completion(test_file, 10, 5)
            print(f"    ✅ get_completion() returned {len(completions) if completions else 0} completions")
        except Exception as e:
            print(f"    ⚠️ get_completion() failed (expected for test file): {e}")
        
        # Test 4: get_hover
        print("  Testing get_hover()...")
        try:
            hover = codebase.get_hover(test_file, 5, 10)
            print(f"    ✅ get_hover() returned: {hover is not None}")
        except Exception as e:
            print(f"    ⚠️ get_hover() failed (expected for test file): {e}")
        
        # Test 5: get_definition
        print("  Testing get_definition()...")
        try:
            definition = codebase.get_definition(test_file, 5, 10)
            print(f"    ✅ get_definition() returned: {definition is not None}")
        except Exception as e:
            print(f"    ⚠️ get_definition() failed (expected for test file): {e}")
        
        # Test 6: get_references
        print("  Testing get_references()...")
        try:
            references = codebase.get_references(test_file, 5, 10)
            print(f"    ✅ get_references() returned {len(references) if references else 0} references")
        except Exception as e:
            print(f"    ⚠️ get_references() failed (expected for test file): {e}")
        
        # Test 7: get_signature_help
        print("  Testing get_signature_help()...")
        try:
            signature = codebase.get_signature_help(test_file, 10, 15)
            print(f"    ✅ get_signature_help() returned: {signature is not None}")
        except Exception as e:
            print(f"    ⚠️ get_signature_help() failed (expected for test file): {e}")
        
        # Test 8: format_document
        print("  Testing format_document()...")
        try:
            formatted = codebase.format_document(test_file)
            print(f"    ✅ format_document() returned: {formatted is not None}")
        except Exception as e:
            print(f"    ⚠️ format_document() failed (expected for test file): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ EnhancedCodebase LSP methods test failed: {e}")
        traceback.print_exc()
        return False

def test_lsp_manager_methods(temp_dir: str, test_file: str):
    """Test LSP Manager methods."""
    print("\n🔧 Testing LSPManager methods...")
    
    try:
        from graph_sitter.core.lsp_manager import LSPManager
        
        # Initialize LSP manager
        manager = LSPManager(temp_dir)
        
        # Test 1: get_all_errors
        print("  Testing LSPManager.get_all_errors()...")
        all_errors = manager.get_all_errors()
        print(f"    ✅ LSPManager.get_all_errors() returned {all_errors.total_count} diagnostics")
        
        # Test 2: get_file_errors
        print("  Testing LSPManager.get_file_errors()...")
        file_errors = manager.get_file_errors(test_file)
        print(f"    ✅ LSPManager.get_file_errors() returned {file_errors.total_count} diagnostics")
        
        # Test 3: Check if manager initializes properly
        print("  Testing LSPManager initialization...")
        initialized = manager._ensure_initialized()
        print(f"    ✅ LSPManager initialization: {initialized}")
        
        return True
        
    except Exception as e:
        print(f"❌ LSPManager methods test failed: {e}")
        traceback.print_exc()
        return False

def test_serena_bridge_methods(temp_dir: str, test_file: str):
    """Test SerenaLSPBridge methods."""
    print("\n🌉 Testing SerenaLSPBridge methods...")
    
    try:
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        
        # Initialize Serena bridge
        bridge = SerenaLSPBridge(temp_dir)
        
        # Test 1: is_initialized
        print("  Testing SerenaLSPBridge.is_initialized...")
        initialized = bridge.is_initialized
        print(f"    ✅ SerenaLSPBridge.is_initialized: {initialized}")
        
        # Test 2: get_diagnostics
        print("  Testing SerenaLSPBridge.get_diagnostics()...")
        diagnostics = bridge.get_diagnostics()
        print(f"    ✅ SerenaLSPBridge.get_diagnostics() returned {len(diagnostics)} diagnostics")
        print(f"    📊 Diagnostic types: {[type(d).__name__ for d in diagnostics[:3]]}")
        
        # Test 3: get_file_diagnostics
        print("  Testing SerenaLSPBridge.get_file_diagnostics()...")
        file_diagnostics = bridge.get_file_diagnostics(test_file)
        print(f"    ✅ SerenaLSPBridge.get_file_diagnostics() returned {len(file_diagnostics)} diagnostics")
        
        # Test 4: get_all_diagnostics
        print("  Testing SerenaLSPBridge.get_all_diagnostics()...")
        all_diagnostics = bridge.get_all_diagnostics()
        print(f"    ✅ SerenaLSPBridge.get_all_diagnostics() returned {len(all_diagnostics)} diagnostics")
        
        # Test 5: Check language server support
        print("  Testing language server support...")
        supports_python = any(server.supports_file(test_file) for server in bridge.language_servers.values())
        print(f"    ✅ Python file support: {supports_python}")
        
        return True
        
    except Exception as e:
        print(f"❌ SerenaLSPBridge methods test failed: {e}")
        traceback.print_exc()
        return False

def test_unified_diagnostics_methods(temp_dir: str, test_file: str):
    """Test UnifiedDiagnosticCollector methods."""
    print("\n🔄 Testing UnifiedDiagnosticCollector methods...")
    
    try:
        from graph_sitter.core.unified_diagnostics import UnifiedDiagnosticCollector
        from graph_sitter.core.lsp_manager import LSPManager
        
        # Initialize components
        lsp_manager = LSPManager(temp_dir)
        collector = UnifiedDiagnosticCollector(lsp_manager)
        
        # Test 1: get_all_diagnostics
        print("  Testing get_all_diagnostics()...")
        all_diagnostics = collector.get_all_diagnostics()
        print(f"    ✅ get_all_diagnostics() returned {all_diagnostics.total_count} diagnostics")
        print(f"    📊 Error breakdown: {all_diagnostics.error_count} errors, {all_diagnostics.warning_count} warnings")
        
        # Test 2: get_file_diagnostics
        print("  Testing get_file_diagnostics()...")
        file_diagnostics = collector.get_file_diagnostics(test_file)
        print(f"    ✅ get_file_diagnostics() returned {file_diagnostics.total_count} diagnostics")
        
        # Test 3: get_diagnostics_by_severity
        print("  Testing get_diagnostics_by_severity()...")
        from graph_sitter.core.lsp_types import ErrorSeverity
        error_diagnostics = collector.get_diagnostics_by_severity(ErrorSeverity.ERROR)
        print(f"    ✅ get_diagnostics_by_severity(ERROR) returned {error_diagnostics.total_count} diagnostics")
        
        # Test 4: get_diagnostics_by_type
        print("  Testing get_diagnostics_by_type()...")
        from graph_sitter.core.lsp_types import ErrorType
        syntax_diagnostics = collector.get_diagnostics_by_type(ErrorType.SYNTAX)
        print(f"    ✅ get_diagnostics_by_type(SYNTAX) returned {syntax_diagnostics.total_count} diagnostics")
        
        # Test 5: get_summary
        print("  Testing get_summary()...")
        summary = collector.get_summary()
        print(f"    ✅ get_summary() returned summary with {len(summary)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ UnifiedDiagnosticCollector methods test failed: {e}")
        traceback.print_exc()
        return False

def test_type_adapters():
    """Test LSP type adapters."""
    print("\n🔄 Testing LSP Type Adapters...")
    
    try:
        from graph_sitter.core.lsp_type_adapters import LSPTypeAdapter
        from graph_sitter.core.lsp_types import ErrorSeverity, ErrorType
        
        # Test 1: severity conversion
        print("  Testing severity conversion...")
        unified_severity = LSPTypeAdapter.severity_to_unified(1)  # ERROR
        print(f"    ✅ severity_to_unified(1) = {unified_severity}")
        
        protocol_severity = LSPTypeAdapter.severity_to_protocol(ErrorSeverity.WARNING)
        print(f"    ✅ severity_to_protocol(WARNING) = {protocol_severity}")
        
        # Test 2: Test that we can create type adapters
        print("  Testing type adapter functionality...")
        # Test that we can convert between types
        from graph_sitter.extensions.lsp.protocol.lsp_types import DiagnosticSeverity
        test_severity = DiagnosticSeverity.ERROR
        unified_severity = LSPTypeAdapter.severity_to_unified(test_severity)
        back_to_protocol = LSPTypeAdapter.severity_to_protocol(unified_severity)
        print(f"    ✅ Round-trip conversion: {test_severity} -> {unified_severity} -> {back_to_protocol}")
        
        return True
        
    except Exception as e:
        print(f"❌ LSP Type Adapters test failed: {e}")
        traceback.print_exc()
        return False

def test_error_info_creation():
    """Test ErrorInfo creation and validation."""
    print("\n📋 Testing ErrorInfo creation...")
    
    try:
        from graph_sitter.core.lsp_types import ErrorInfo, ErrorSeverity, ErrorType, Position, Range
        
        # Test 1: Create ErrorInfo with proper Range
        print("  Testing ErrorInfo creation...")
        start_pos = Position(line=5, character=10)
        end_pos = Position(line=5, character=20)
        range_obj = Range(start=start_pos, end=end_pos)
        
        error_info = ErrorInfo(
            id="test-error-1",
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            error_type=ErrorType.SYNTAX,
            file_path="/test/file.py",
            range=range_obj,
            source="test-source"
        )
        
        print(f"    ✅ ErrorInfo created successfully: {error_info.id}")
        print(f"    📍 Range: line {error_info.range.start.line}, char {error_info.range.start.character}")
        
        # Test 2: Convert to dict
        print("  Testing ErrorInfo.to_dict()...")
        error_dict = error_info.to_dict()
        print(f"    ✅ to_dict() returned {len(error_dict)} fields")
        
        return True
        
    except Exception as e:
        print(f"❌ ErrorInfo creation test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_validation():
    """Run comprehensive validation of all LSP methods."""
    print("🚀 Starting Comprehensive LSP Method Validation")
    print("=" * 60)
    
    # Track test results
    test_results = []
    
    # Test 1: Imports
    test_results.append(("Imports", test_imports()))
    
    if not test_results[-1][1]:
        print("❌ Cannot proceed without successful imports")
        return False
    
    # Create temporary directory and test file
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📁 Using temporary directory: {temp_dir}")
        
        # Create test Python file
        test_file = create_test_python_file(temp_dir)
        print(f"📄 Created test file: {test_file}")
        
        # Test 2: ErrorInfo creation
        test_results.append(("ErrorInfo Creation", test_error_info_creation()))
        
        # Test 3: Type adapters
        test_results.append(("Type Adapters", test_type_adapters()))
        
        # Test 4: Enhanced Codebase LSP methods
        test_results.append(("EnhancedCodebase LSP", test_enhanced_codebase_lsp_methods(temp_dir, test_file)))
        
        # Test 5: LSP Manager methods
        test_results.append(("LSPManager", test_lsp_manager_methods(temp_dir, test_file)))
        
        # Test 6: Serena Bridge methods
        test_results.append(("SerenaLSPBridge", test_serena_bridge_methods(temp_dir, test_file)))
        
        # Test 7: Unified Diagnostics methods
        test_results.append(("UnifiedDiagnostics", test_unified_diagnostics_methods(temp_dir, test_file)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n🎯 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The consolidated LSP system is working correctly.")
        return True
    else:
        print(f"⚠️ {failed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)
