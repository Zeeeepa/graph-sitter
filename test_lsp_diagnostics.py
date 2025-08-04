#!/usr/bin/env python3
"""
Test LSP Diagnostics Integration

This script tests the LSP diagnostic capabilities in graph-sitter
to verify that Serena's LSP integration is working correctly.
"""

import os
import sys
import traceback
from pathlib import Path

def test_lsp_diagnostics():
    """Test LSP diagnostic functionality."""
    try:
        from graph_sitter import Codebase
        
        print("🔍 Initializing codebase for LSP diagnostics test...")
        codebase = Codebase(".")
        
        # Test if diagnostic method is available
        if not hasattr(codebase, 'get_file_diagnostics'):
            print("❌ get_file_diagnostics method not available")
            return False
        
        print("✅ get_file_diagnostics method available")
        
        # Find a Python file to test
        test_file = None
        for file in codebase.files:
            if file.file_path.endswith('.py') and 'test_serena_integration.py' in file.file_path:
                test_file = file.file_path
                break
        
        if not test_file:
            # Use any Python file
            for file in codebase.files:
                if file.file_path.endswith('.py'):
                    test_file = file.file_path
                    break
        
        if not test_file:
            print("❌ No Python files found for testing")
            return False
        
        print(f"🧪 Testing diagnostics on file: {test_file}")
        
        # Get diagnostics for the test file
        result = codebase.get_file_diagnostics(test_file)
        
        if result:
            print("✅ Diagnostic result received")
            print(f"   Result type: {type(result)}")
            print(f"   Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                if 'success' in result:
                    print(f"   Success: {result['success']}")
                
                if 'diagnostics' in result:
                    diagnostics = result['diagnostics']
                    print(f"   Diagnostics count: {len(diagnostics)}")
                    
                    # Show first few diagnostics
                    for i, diag in enumerate(diagnostics[:3]):
                        print(f"   Diagnostic {i+1}: {diag}")
                
                if 'error' in result:
                    print(f"   Error: {result['error']}")
            
            return True
        else:
            print("❌ No diagnostic result received")
            return False
            
    except Exception as e:
        print(f"❌ LSP diagnostics test failed: {e}")
        traceback.print_exc()
        return False

def test_lsp_bridge_directly():
    """Test LSP bridge directly."""
    try:
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        
        print("🌉 Testing LSP bridge directly...")
        bridge = SerenaLSPBridge(".")
        
        print(f"✅ LSP bridge created")
        print(f"   Initialized: {bridge.is_initialized}")
        print(f"   Language servers: {len(bridge.language_servers)}")
        
        for lang, server in bridge.language_servers.items():
            print(f"   - {lang}: {type(server).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ LSP bridge test failed: {e}")
        traceback.print_exc()
        return False

def test_serena_lsp_integration():
    """Test Serena LSP integration components."""
    try:
        from graph_sitter.extensions.lsp.serena.lsp_integration import SerenaLSPIntegration
        print("✅ SerenaLSPIntegration import successful")
        return True
    except ImportError as e:
        print(f"❌ SerenaLSPIntegration import failed: {e}")
        return False

def explore_lsp_structure():
    """Explore the LSP folder structure."""
    print("📁 Exploring LSP folder structure...")
    
    lsp_path = Path("src/graph_sitter/extensions/lsp")
    if not lsp_path.exists():
        print("❌ LSP path not found")
        return
    
    print(f"📂 LSP directory: {lsp_path}")
    
    # List all Python files in LSP directory
    for py_file in lsp_path.rglob("*.py"):
        rel_path = py_file.relative_to(lsp_path)
        print(f"   📄 {rel_path}")
    
    # Check Serena subdirectory
    serena_path = lsp_path / "serena"
    if serena_path.exists():
        print(f"\n📂 Serena directory: {serena_path}")
        for py_file in serena_path.rglob("*.py"):
            rel_path = py_file.relative_to(serena_path)
            print(f"   📄 {rel_path}")

def main():
    """Main test function."""
    print("🚀 Testing LSP Diagnostics Integration")
    print("=" * 50)
    
    # Test 1: Explore structure
    print("\n📁 Exploring LSP Structure")
    print("-" * 30)
    explore_lsp_structure()
    
    # Test 2: LSP bridge
    print("\n🌉 Testing LSP Bridge")
    print("-" * 25)
    bridge_ok = test_lsp_bridge_directly()
    
    # Test 3: Serena LSP integration
    print("\n🔗 Testing Serena LSP Integration")
    print("-" * 35)
    integration_ok = test_serena_lsp_integration()
    
    # Test 4: LSP diagnostics
    print("\n🔍 Testing LSP Diagnostics")
    print("-" * 30)
    diagnostics_ok = test_lsp_diagnostics()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    print(f"LSP Bridge: {'✅' if bridge_ok else '❌'}")
    print(f"Serena LSP Integration: {'✅' if integration_ok else '❌'}")
    print(f"LSP Diagnostics: {'✅' if diagnostics_ok else '❌'}")
    
    overall_success = bridge_ok and diagnostics_ok
    print(f"\n🎉 Overall LSP Integration: {'✅ SUCCESS' if overall_success else '❌ NEEDS WORK'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
