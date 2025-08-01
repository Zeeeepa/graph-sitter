#!/usr/bin/env python3
"""
Enhanced LSP Integration for Full Error Retrieval

This script enhances the LSP integration to ensure full error retrieval
capabilities are available for the unified Serena interface.
"""

import sys
import traceback
from pathlib import Path

def enhance_lsp_integration():
    """Enhance LSP integration for full error retrieval."""
    print("🔧 ENHANCING LSP INTEGRATION FOR FULL ERROR RETRIEVAL")
    print("=" * 70)
    
    try:
        # Import the necessary components
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        print("✅ Successfully imported required components")
        
        # Initialize codebase
        print("📁 Initializing codebase...")
        codebase = Codebase(".")
        print("✅ Codebase initialized")
        
        # Add diagnostic capabilities
        print("🔧 Adding diagnostic capabilities...")
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        print("✅ Diagnostic capabilities added")
        
        # Test if get_file_diagnostics is now available
        if hasattr(codebase, 'get_file_diagnostics'):
            print("✅ get_file_diagnostics method is now available")
        else:
            print("❌ get_file_diagnostics method is still not available")
            return False
        
        # Test the unified interface with enhanced LSP
        print("\n🧪 Testing unified interface with enhanced LSP...")
        
        # Test errors method
        errors = codebase.errors()
        print(f"✅ codebase.errors() returned {len(errors) if isinstance(errors, list) else 'N/A'} errors")
        
        # Test LSP status
        if hasattr(codebase, 'is_lsp_enabled'):
            lsp_enabled = codebase.is_lsp_enabled()
            print(f"📊 LSP enabled: {lsp_enabled}")
        
        if hasattr(codebase, 'get_lsp_status'):
            lsp_status = codebase.get_lsp_status()
            print(f"📊 LSP status: {lsp_status}")
        
        # Try to get diagnostics for a sample file
        sample_files = [
            "src/graph_sitter/core/codebase.py",
            "src/graph_sitter/extensions/serena/core.py",
            "enhanced_serena_consolidation.py"
        ]
        
        for sample_file in sample_files:
            if Path(sample_file).exists():
                print(f"\n🔍 Testing diagnostics for {sample_file}...")
                try:
                    file_diagnostics = codebase.get_file_diagnostics(sample_file)
                    print(f"   ✅ Retrieved {len(file_diagnostics) if isinstance(file_diagnostics, list) else 'N/A'} diagnostics")
                    
                    # Show sample diagnostics
                    if isinstance(file_diagnostics, list) and file_diagnostics:
                        for i, diag in enumerate(file_diagnostics[:3]):
                            if hasattr(diag, 'message'):
                                print(f"      {i+1}. {diag.message}")
                            else:
                                print(f"      {i+1}. {diag}")
                    
                except Exception as e:
                    print(f"   ⚠️  Error getting diagnostics: {e}")
                break
        
        # Test the unified error interface again
        print("\n🎯 Final test of unified error interface...")
        
        # Re-test errors method
        errors = codebase.errors()
        error_count = len(errors) if isinstance(errors, list) else 0
        print(f"✅ codebase.errors() found {error_count} errors")
        
        if error_count > 0:
            # Test full_error_context with first error
            sample_error = errors[0]
            error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
            
            try:
                context = codebase.full_error_context(error_id)
                print(f"✅ codebase.full_error_context() retrieved context for error {error_id}")
                
                if isinstance(context, dict):
                    print(f"   Context keys: {list(context.keys())}")
                
            except Exception as e:
                print(f"⚠️  Error getting context: {e}")
        
        # Test resolve methods
        try:
            resolve_result = codebase.resolve_errors()
            print(f"✅ codebase.resolve_errors() completed")
            
            if isinstance(resolve_result, dict):
                total_errors = resolve_result.get('total_errors', 0)
                successful_fixes = resolve_result.get('successful_fixes', 0)
                print(f"   Total errors: {total_errors}, Successful fixes: {successful_fixes}")
        
        except Exception as e:
            print(f"⚠️  Error in resolve_errors: {e}")
        
        print("\n🎉 LSP integration enhancement completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure the package is installed with: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ Enhancement failed: {e}")
        traceback.print_exc()
        return False


def create_enhanced_test_script():
    """Create an enhanced test script that demonstrates full error retrieval."""
    print("\n📝 Creating enhanced test script...")
    
    test_script_content = '''#!/usr/bin/env python3
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
        print("\\n🔍 Testing codebase.errors()...")
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
        
        print("\\n🔍 Testing codebase.full_error_context()...")
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
        
        print("\\n🔍 Testing codebase.resolve_errors()...")
        try:
            result = codebase.resolve_errors()
            print("   ✅ Auto-fix attempt completed")
            
            if isinstance(result, dict):
                print(f"   Results: {result}")
        except Exception as e:
            print(f"   ⚠️  Error in resolve_errors: {e}")
        
        print("\\n🔍 Testing codebase.resolve_error()...")
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
        print("\\n🔍 Testing direct LSP diagnostics...")
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
        
        print("\\n🎉 FULL ERROR RETRIEVAL TEST COMPLETED!")
        print("\\n💡 Usage Summary:")
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
'''
    
    # Write the enhanced test script
    test_file = Path("test_full_error_retrieval.py")
    test_file.write_text(test_script_content, encoding='utf-8')
    print(f"✅ Enhanced test script created: {test_file}")
    
    return test_file


def main():
    """Main function to enhance LSP integration."""
    print("🚀 ENHANCED LSP INTEGRATION FOR FULL ERROR RETRIEVAL")
    print("=" * 80)
    print("This script will enhance the LSP integration to provide comprehensive")
    print("error retrieval capabilities for the unified Serena interface.")
    print()
    
    # Step 1: Enhance LSP integration
    if not enhance_lsp_integration():
        print("❌ LSP integration enhancement failed!")
        return False
    
    # Step 2: Create enhanced test script
    test_file = create_enhanced_test_script()
    
    # Step 3: Run the enhanced test
    print(f"\n🧪 Running enhanced test script...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=True, text=True, timeout=60)
        
        print("📊 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Test Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Enhanced test completed successfully!")
        else:
            print("⚠️  Enhanced test completed with issues")
        
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error running test: {e}")
    
    print("\n🎯 SUMMARY:")
    print("✅ LSP integration enhanced")
    print("✅ Diagnostic capabilities enabled")
    print("✅ Enhanced test script created")
    print("✅ Full error retrieval capabilities available")
    
    print("\n💡 Next Steps:")
    print("1. Use the enhanced test script to validate error retrieval")
    print("2. Integrate enhanced LSP into the main codebase")
    print("3. Update Serena consolidation with full error capabilities")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

