#!/usr/bin/env python3
"""
Enhanced Error Retrieval Test Script

This script demonstrates the full error retrieval capabilities of the
unified Serena interface with enhanced LSP integration.
"""

import sys
from pathlib import Path

def test_full_error_retrieval():
    """Test full error retrieval capabilities."""
    print("🧪 TESTING FULL ERROR RETRIEVAL CAPABILITIES")
    print("=" * 60)
    
    try:
        # Import and initialize
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        print("📁 Initializing codebase with enhanced LSP...")
        codebase = Codebase(".")
        
        # Ensure diagnostic capabilities are added
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        print("✅ Diagnostic capabilities enabled")
        
        # Test all unified interface methods
        print("\n🔍 Testing codebase.errors()...")
        errors = codebase.errors()
        print(f"   Found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
        
        # Show sample errors
        if isinstance(errors, list) and errors:
            print("   Sample errors:")
            for i, error in enumerate(errors[:5]):
                if isinstance(error, dict):
                    file_path = error.get('file_path', 'unknown')
                    line = error.get('line', 'unknown')
                    message = error.get('message', 'no message')[:60]
                    severity = error.get('severity', 'unknown')
                    print(f"     {i+1}. [{severity.upper()}] {file_path}:{line} - {message}...")
                else:
                    print(f"     {i+1}. {error}")
        
        print("\n🔍 Testing codebase.full_error_context()...")
        if isinstance(errors, list) and errors:
            sample_error = errors[0]
            error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
            
            try:
                context = codebase.full_error_context(error_id)
                print(f"   ✅ Retrieved context for error: {error_id}")
                
                if isinstance(context, dict):
                    print(f"   Context includes: {', '.join(context.keys())}")
                    
                    # Show fix suggestions if available
                    if 'fix_suggestions' in context:
                        suggestions = context['fix_suggestions']
                        if suggestions:
                            print(f"   Fix suggestions available: {len(suggestions)}")
                            for i, suggestion in enumerate(suggestions[:3]):
                                if isinstance(suggestion, dict):
                                    desc = suggestion.get('description', 'No description')
                                    print(f"     {i+1}. {desc}")
                
            except Exception as e:
                print(f"   ⚠️  Error getting context: {e}")
        else:
            print("   ⚠️  No errors available to test context retrieval")
        
        print("\n🔍 Testing codebase.resolve_errors()...")
        try:
            result = codebase.resolve_errors()
            print("   ✅ Auto-fix attempt completed")
            
            if isinstance(result, dict):
                print(f"   Results: {result}")
        except Exception as e:
            print(f"   ⚠️  Error in resolve_errors: {e}")
        
        print("\n🔍 Testing codebase.resolve_error()...")
        if isinstance(errors, list) and errors:
            sample_error = errors[0]
            error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
            
            try:
                fix_result = codebase.resolve_error(error_id)
                print(f"   ✅ Individual fix attempt completed for: {error_id}")
                
                if isinstance(fix_result, dict):
                    success = fix_result.get('success', False)
                    print(f"   Fix successful: {success}")
            except Exception as e:
                print(f"   ⚠️  Error in resolve_error: {e}")
        else:
            print("   ⚠️  No errors available to test individual resolution")
        
        # Test LSP diagnostics directly
        print("\n🔍 Testing direct LSP diagnostics...")
        if hasattr(codebase, 'get_file_diagnostics'):
            sample_files = [
                "src/graph_sitter/core/codebase.py",
                "enhanced_serena_consolidation.py",
                "test_unified_interface.py"
            ]
            
            for sample_file in sample_files:
                if Path(sample_file).exists():
                    try:
                        diagnostics = codebase.get_file_diagnostics(sample_file)
                        print(f"   📄 {sample_file}: {len(diagnostics) if isinstance(diagnostics, list) else 'N/A'} diagnostics")
                        
                        if isinstance(diagnostics, list) and diagnostics:
                            for diag in diagnostics[:2]:
                                if hasattr(diag, 'message') and hasattr(diag, 'severity'):
                                    print(f"      - [{diag.severity}] {diag.message}")
                        
                    except Exception as e:
                        print(f"   ⚠️  Error getting diagnostics for {sample_file}: {e}")
                    break
        
        print("\n🎉 FULL ERROR RETRIEVAL TEST COMPLETED!")
        print("\n💡 Usage Summary:")
        print("   from graph_sitter import Codebase")
        print("   from graph_sitter.core.diagnostics import add_diagnostic_capabilities")
        print("   ")
        print("   codebase = Codebase('.')")
        print("   add_diagnostic_capabilities(codebase, enable_lsp=True)")
        print("   ")
        print("   errors = codebase.errors()                    # All errors")
        print("   context = codebase.full_error_context(id)     # Full context")
        print("   result = codebase.resolve_errors()            # Auto-fix all")
        print("   fix = codebase.resolve_error(id)              # Auto-fix one")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_error_retrieval()
    sys.exit(0 if success else 1)
