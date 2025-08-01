#!/usr/bin/env python3
"""
DEBUG LSP INTEGRATION

Let's debug why the LSP integration is not detecting errors properly.
"""

import sys
import json
from pathlib import Path

def debug_lsp_integration():
    """Debug the LSP integration step by step."""
    print("🔍 DEBUGGING LSP INTEGRATION")
    print("=" * 60)
    
    try:
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        print("✅ Successfully imported graph-sitter components")
        
        # Create a simple test file with obvious errors
        test_file = Path("debug_test.py")
        test_content = '''# This file has obvious syntax errors
def broken_function()  # Missing colon
    return "broken"

import non_existent_module  # Import error

undefined_variable = some_undefined_var  # Name error
'''
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")
        
        # Initialize codebase
        print("\n🔧 Initializing codebase...")
        codebase = Codebase(".")
        print("✅ Codebase initialized")
        
        # Add diagnostic capabilities
        print("\n🔧 Adding diagnostic capabilities...")
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        print("✅ Diagnostic capabilities added")
        
        # Check LSP status
        print("\n📊 Checking LSP status...")
        if hasattr(codebase, 'get_lsp_status'):
            lsp_status = codebase.get_lsp_status()
            print(f"   LSP Status: {lsp_status}")
        
        if hasattr(codebase, 'is_lsp_enabled'):
            lsp_enabled = codebase.is_lsp_enabled()
            print(f"   LSP Enabled: {lsp_enabled}")
        
        # Check if LSP bridge exists
        if hasattr(codebase, '_lsp_bridge'):
            print(f"   LSP Bridge exists: {codebase._lsp_bridge is not None}")
            if codebase._lsp_bridge:
                print(f"   LSP Bridge type: {type(codebase._lsp_bridge)}")
        
        # Test direct file diagnostics
        print(f"\n🔍 Testing direct file diagnostics on {test_file.name}...")
        try:
            diagnostics = codebase.get_file_diagnostics(test_file.name)
            print(f"   Diagnostics result type: {type(diagnostics)}")
            print(f"   Diagnostics content: {diagnostics}")
            
            if isinstance(diagnostics, dict):
                if diagnostics.get('success'):
                    diag_list = diagnostics.get('diagnostics', [])
                    print(f"   Found {len(diag_list)} diagnostics")
                    for i, diag in enumerate(diag_list):
                        print(f"      {i+1}. {diag}")
                else:
                    print(f"   Diagnostics failed: {diagnostics.get('error', 'Unknown error')}")
            elif isinstance(diagnostics, list):
                print(f"   Found {len(diagnostics)} diagnostics (list format)")
                for i, diag in enumerate(diagnostics):
                    print(f"      {i+1}. {diag}")
            else:
                print(f"   Unexpected diagnostics format")
                
        except Exception as e:
            print(f"   ❌ Error getting diagnostics: {e}")
            import traceback
            traceback.print_exc()
        
        # Test unified interface
        print(f"\n🎯 Testing unified interface...")
        try:
            errors = codebase.errors()
            print(f"   Errors result type: {type(errors)}")
            print(f"   Errors count: {len(errors) if isinstance(errors, list) else 'N/A'}")
            if isinstance(errors, list) and errors:
                print(f"   First few errors: {errors[:3]}")
        except Exception as e:
            print(f"   ❌ Error with unified interface: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Python's built-in syntax checking
        print(f"\n🐍 Testing Python built-in syntax checking...")
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            compile(content, test_file.name, 'exec')
            print("   ✅ Python syntax check: PASSED")
        except SyntaxError as e:
            print(f"   ❌ Python syntax check: FAILED - {e}")
        except Exception as e:
            print(f"   ⚠️  Python syntax check error: {e}")
        
        # Check if LSP server is actually running
        print(f"\n🔍 Checking LSP server status...")
        try:
            if hasattr(codebase, '_lsp_bridge') and codebase._lsp_bridge:
                bridge = codebase._lsp_bridge
                if hasattr(bridge, 'language_servers'):
                    servers = bridge.language_servers
                    print(f"   Language servers: {len(servers)} configured")
                    for name, server in servers.items():
                        print(f"      {name}: {type(server)}")
                        if hasattr(server, 'is_running'):
                            print(f"         Running: {server.is_running()}")
                        if hasattr(server, 'get_diagnostics'):
                            print(f"         Has get_diagnostics: True")
        except Exception as e:
            print(f"   ⚠️  Error checking LSP servers: {e}")
        
        # Cleanup
        test_file.unlink()
        print(f"\n🧹 Cleaned up test file")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lsp_server_directly():
    """Test LSP server directly without graph-sitter wrapper."""
    print("\n🔍 TESTING LSP SERVER DIRECTLY")
    print("=" * 60)
    
    try:
        from graph_sitter.extensions.lsp.language_servers.python_server import PythonLanguageServer
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        
        print("✅ Successfully imported LSP components")
        
        # Create test file
        test_file = Path("direct_lsp_test.py")
        test_content = '''# Direct LSP test file
def broken_function()  # Missing colon - syntax error
    return "broken"

import non_existent_module_xyz  # Import error

result = undefined_variable_name  # Name error
'''
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")
        
        # Initialize LSP server directly
        print("\n🔧 Initializing Python LSP server directly...")
        python_server = PythonLanguageServer(".")
        print("✅ Python LSP server initialized")
        
        # Test diagnostics
        print(f"\n🔍 Getting diagnostics for {test_file.name}...")
        try:
            diagnostics = python_server.get_diagnostics(str(test_file))
            print(f"   Diagnostics type: {type(diagnostics)}")
            print(f"   Diagnostics content: {diagnostics}")
            
            if isinstance(diagnostics, list):
                print(f"   Found {len(diagnostics)} diagnostics")
                for i, diag in enumerate(diagnostics):
                    print(f"      {i+1}. {diag}")
            elif isinstance(diagnostics, dict):
                print(f"   Diagnostics dict keys: {diagnostics.keys()}")
            
        except Exception as e:
            print(f"   ❌ Error getting diagnostics: {e}")
            import traceback
            traceback.print_exc()
        
        # Cleanup
        test_file.unlink()
        print(f"\n🧹 Cleaned up test file")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run LSP debugging."""
    print("🔍 LSP INTEGRATION DEBUGGING")
    print("=" * 80)
    print("This will help us understand why error detection is not working.")
    print()
    
    # Debug main integration
    success1 = debug_lsp_integration()
    
    # Test LSP server directly
    success2 = test_lsp_server_directly()
    
    print(f"\n🎯 DEBUGGING SUMMARY:")
    print(f"   Main integration test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Direct LSP test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if not success1 and not success2:
        print(f"\n🚨 CRITICAL: Both tests failed - LSP integration is broken!")
    elif not success1:
        print(f"\n⚠️  WARNING: Main integration failed but direct LSP works - wrapper issue!")
    elif not success2:
        print(f"\n⚠️  WARNING: Direct LSP failed but integration works - server issue!")
    else:
        print(f"\n✅ Both tests passed - need to investigate why validation failed!")
    
    return success1 or success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

