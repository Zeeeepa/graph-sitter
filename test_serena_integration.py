#!/usr/bin/env python3
"""
Test Serena Integration in Graph-Sitter

This script tests the Serena integration within graph-sitter to verify
that all components are working correctly.
"""

import os
import sys
import traceback
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_graph_sitter_import():
    """Test basic graph-sitter import."""
    try:
        from graph_sitter import Codebase
        print("✅ Graph-sitter import successful")
        return True
    except ImportError as e:
        print(f"❌ Graph-sitter import failed: {e}")
        return False

def test_serena_components():
    """Test Serena component imports."""
    components = {}
    
    # Test core Serena imports
    try:
        from graph_sitter.extensions.lsp.serena import SerenaCore
        components['SerenaCore'] = True
        print("✅ SerenaCore import successful")
    except ImportError as e:
        components['SerenaCore'] = False
        print(f"❌ SerenaCore import failed: {e}")
    
    try:
        from graph_sitter.extensions.lsp.serena.types import SerenaConfig, SerenaCapability
        components['SerenaTypes'] = True
        print("✅ Serena types import successful")
    except ImportError as e:
        components['SerenaTypes'] = False
        print(f"❌ Serena types import failed: {e}")
    
    try:
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        components['SerenaLSPBridge'] = True
        print("✅ Serena LSP Bridge import successful")
    except ImportError as e:
        components['SerenaLSPBridge'] = False
        print(f"❌ Serena LSP Bridge import failed: {e}")
    
    return components

def test_codebase_initialization():
    """Test codebase initialization with current directory."""
    try:
        from graph_sitter import Codebase
        codebase = Codebase(".")
        print("✅ Codebase initialization successful")
        
        # Test basic codebase properties
        if hasattr(codebase, 'files'):
            print(f"   📁 Found {len(codebase.files)} files")
        
        if hasattr(codebase, 'functions'):
            print(f"   🔧 Found {len(codebase.functions)} functions")
        
        if hasattr(codebase, 'classes'):
            print(f"   📦 Found {len(codebase.classes)} classes")
        
        return codebase
    except Exception as e:
        print(f"❌ Codebase initialization failed: {e}")
        traceback.print_exc()
        return None

def test_serena_methods(codebase):
    """Test available Serena methods on codebase."""
    if not codebase:
        return {}
    
    serena_methods = [
        'get_serena_status', 'shutdown_serena', 'get_completions',
        'get_hover_info', 'get_signature_help', 'rename_symbol',
        'extract_method', 'semantic_search', 'generate_boilerplate',
        'organize_imports', 'get_file_diagnostics', 'get_symbol_context',
        'analyze_symbol_impact', 'enable_realtime_analysis'
    ]
    
    available_methods = {}
    
    for method in serena_methods:
        if hasattr(codebase, method):
            available_methods[method] = True
            print(f"✅ Method {method} available")
        else:
            available_methods[method] = False
            print(f"❌ Method {method} not available")
    
    return available_methods

def test_serena_status(codebase):
    """Test getting Serena status."""
    if not codebase or not hasattr(codebase, 'get_serena_status'):
        print("⚠️  get_serena_status method not available")
        return None
    
    try:
        status = codebase.get_serena_status()
        print("✅ Serena status retrieved successfully")
        print(f"   Status: {status}")
        return status
    except Exception as e:
        print(f"❌ Failed to get Serena status: {e}")
        return None

def main():
    """Main test function."""
    print("🚀 Testing Serena Integration in Graph-Sitter")
    print("=" * 60)
    
    # Test 1: Basic imports
    print("\n📦 Testing Basic Imports")
    print("-" * 30)
    graph_sitter_ok = test_graph_sitter_import()
    
    # Test 2: Serena component imports
    print("\n🔧 Testing Serena Component Imports")
    print("-" * 40)
    serena_components = test_serena_components()
    
    # Test 3: Codebase initialization
    print("\n🏗️  Testing Codebase Initialization")
    print("-" * 40)
    codebase = test_codebase_initialization()
    
    # Test 4: Serena methods availability
    print("\n🎯 Testing Serena Methods Availability")
    print("-" * 45)
    serena_methods = test_serena_methods(codebase)
    
    # Test 5: Serena status
    print("\n📊 Testing Serena Status")
    print("-" * 30)
    serena_status = test_serena_status(codebase)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    print(f"Graph-sitter: {'✅' if graph_sitter_ok else '❌'}")
    
    for component, status in serena_components.items():
        print(f"{component}: {'✅' if status else '❌'}")
    
    print(f"Codebase initialization: {'✅' if codebase else '❌'}")
    
    if serena_methods:
        available_count = sum(1 for v in serena_methods.values() if v)
        total_count = len(serena_methods)
        print(f"Serena methods: {available_count}/{total_count} available")
    
    print(f"Serena status: {'✅' if serena_status else '❌'}")
    
    # Overall assessment
    overall_success = (
        graph_sitter_ok and
        any(serena_components.values()) and
        codebase is not None
    )
    
    print(f"\n🎉 Overall Integration: {'✅ SUCCESS' if overall_success else '❌ NEEDS WORK'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
