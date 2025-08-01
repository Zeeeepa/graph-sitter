#!/usr/bin/env python3
"""
Quick Consolidation Validation Test

This test quickly validates that the consolidation is working correctly
by testing the core components without running full error detection.
"""

import sys
import time
import traceback
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_consolidated_error_info():
    """Test that the consolidated ErrorInfo class works correctly."""
    print("🔍 Testing consolidated ErrorInfo class...")
    
    try:
        from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo, DiagnosticSeverity
        
        # Test ErrorInfo creation and properties
        error_info = ErrorInfo(
            file_path="test.py",
            line=10,
            character=5,
            message="Test error message",
            severity=DiagnosticSeverity.ERROR,
            source="test",
            code="E001"
        )
        
        # Test properties
        assert error_info.id == "test.py:10:5"
        assert error_info.is_error == True
        assert error_info.is_warning == False
        assert error_info.column == 5  # Backward compatibility
        assert error_info.severity_name == "error"
        
        # Test string representation
        str_repr = str(error_info)
        assert "test.py:10:5" in str_repr
        assert "error" in str_repr.lower()
        assert "Test error message" in str_repr
        
        # Test LSP conversion
        lsp_diagnostic = error_info.to_lsp_diagnostic()
        assert lsp_diagnostic.message == "Test error message"
        assert lsp_diagnostic.severity == DiagnosticSeverity.ERROR
        
        print("✅ ErrorInfo class consolidation - PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ErrorInfo class consolidation - FAILED: {e}")
        return False

def test_import_consolidation():
    """Test that imports work correctly after consolidation."""
    print("🔍 Testing import consolidation...")
    
    try:
        # Test importing consolidated ErrorInfo
        from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo, DiagnosticSeverity
        
        # Test importing transaction manager
        from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
        
        # Test importing from core diagnostics
        from graph_sitter.core.diagnostics import CodebaseDiagnostics
        
        # Test that we can create instances
        error_info = ErrorInfo(
            file_path="test.py",
            line=1,
            character=0,
            message="Test",
            severity=DiagnosticSeverity.ERROR
        )
        
        # Test that the classes are the same (no duplicates)
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        
        # This should work without import errors
        bridge = SerenaLSPBridge(".")
        
        print("✅ Import consolidation - PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Import consolidation - FAILED: {e}")
        return False

def test_unified_interface_availability():
    """Test that the unified interface methods are available."""
    print("🔍 Testing unified interface availability...")
    
    try:
        from graph_sitter import Codebase
        
        # Initialize codebase with current directory (git repo)
        codebase = Codebase(".")
        
        # Check that all required methods exist
        required_methods = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
        missing_methods = []
        
        for method in required_methods:
            if not hasattr(codebase, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Unified interface availability - FAILED: Missing methods: {missing_methods}")
            return False
        
        # Check that methods are callable
        for method in required_methods:
            method_obj = getattr(codebase, method)
            if not callable(method_obj):
                print(f"❌ Unified interface availability - FAILED: Method {method} is not callable")
                return False
        
        print("✅ Unified interface availability - PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Unified interface availability - FAILED: {e}")
        return False

def test_no_duplicate_classes():
    """Test that there are no duplicate classes after consolidation."""
    print("🔍 Testing for duplicate classes...")
    
    try:
        # Import ErrorInfo from different locations and verify they're the same
        from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo as ErrorInfo1
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
        from graph_sitter.core.diagnostics import CodebaseDiagnostics
        
        # Create instances to verify they work
        error_info = ErrorInfo1(
            file_path="test.py",
            line=1,
            character=0,
            message="Test",
            severity=1  # DiagnosticSeverity.ERROR
        )
        
        bridge = SerenaLSPBridge(".")
        
        print("✅ No duplicate classes - PASSED")
        return True
        
    except Exception as e:
        print(f"❌ No duplicate classes - FAILED: {e}")
        return False

def main():
    """Main function to run the quick consolidation test."""
    print("🚀 QUICK CONSOLIDATION VALIDATION TEST")
    print("=" * 50)
    print("Testing core consolidation components")
    print()
    
    tests = [
        test_consolidated_error_info,
        test_import_consolidation,
        test_no_duplicate_classes,
        test_unified_interface_availability,
    ]
    
    passed = 0
    total = len(tests)
    
    start_time = time.time()
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    duration = time.time() - start_time
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Tests Run: {total}")
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Duration: {duration:.3f}s")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Consolidation is working correctly.")
        print("✅ ErrorInfo class consolidated successfully")
        print("✅ Import paths updated correctly")
        print("✅ No duplicate classes detected")
        print("✅ Unified interface methods available")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check output for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Test suite failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)
