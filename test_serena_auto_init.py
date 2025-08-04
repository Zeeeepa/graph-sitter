#!/usr/bin/env python3
"""
Test Serena Auto-Initialization

This script tests the auto-initialization process for Serena integration
to understand why the methods are not being added to the Codebase class.
"""

import os
import sys
import traceback
from pathlib import Path

def test_auto_init_import():
    """Test importing the auto_init module."""
    try:
        from graph_sitter.extensions.lsp.serena.auto_init import _initialized
        print(f"✅ Auto-init module imported successfully")
        print(f"   Initialization status: {_initialized}")
        return _initialized
    except ImportError as e:
        print(f"❌ Auto-init module import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Auto-init module error: {e}")
        traceback.print_exc()
        return False

def test_manual_initialization():
    """Test manual initialization of Serena integration."""
    try:
        from graph_sitter.extensions.lsp.serena.auto_init import initialize_serena_integration
        
        print("🔧 Testing manual initialization...")
        result = initialize_serena_integration()
        print(f"   Manual initialization result: {result}")
        
        return result
    except Exception as e:
        print(f"❌ Manual initialization failed: {e}")
        traceback.print_exc()
        return False

def test_codebase_after_init():
    """Test Codebase class after initialization."""
    try:
        from graph_sitter import Codebase
        
        print("🔍 Checking Codebase class for Serena methods...")
        
        serena_methods = [
            'get_serena_status', 'get_completions', 'get_hover_info',
            'rename_symbol', 'extract_method', 'semantic_search'
        ]
        
        found_methods = []
        missing_methods = []
        
        for method in serena_methods:
            if hasattr(Codebase, method):
                found_methods.append(method)
                print(f"   ✅ {method} found")
            else:
                missing_methods.append(method)
                print(f"   ❌ {method} missing")
        
        print(f"\n📊 Summary: {len(found_methods)}/{len(serena_methods)} methods found")
        
        return len(found_methods) > 0
        
    except Exception as e:
        print(f"❌ Error checking Codebase class: {e}")
        traceback.print_exc()
        return False

def test_import_dependencies():
    """Test importing the dependencies that auto_init needs."""
    dependencies = [
        ('graph_sitter.core.codebase', 'Codebase'),
        ('graph_sitter.extensions.lsp.serena.core', 'SerenaCore'),
        ('graph_sitter.extensions.lsp.serena.types', 'SerenaConfig'),
        ('graph_sitter.extensions.lsp.serena.lsp_integration', 'SerenaLSPIntegration'),
    ]
    
    print("🔍 Testing auto_init dependencies...")
    
    results = {}
    for module_name, class_name in dependencies:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            results[f"{module_name}.{class_name}"] = True
            print(f"   ✅ {module_name}.{class_name}")
        except ImportError as e:
            results[f"{module_name}.{class_name}"] = False
            print(f"   ❌ {module_name}.{class_name} - ImportError: {e}")
        except AttributeError as e:
            results[f"{module_name}.{class_name}"] = False
            print(f"   ❌ {module_name}.{class_name} - AttributeError: {e}")
        except Exception as e:
            results[f"{module_name}.{class_name}"] = False
            print(f"   ❌ {module_name}.{class_name} - Error: {e}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\n📊 Dependencies: {success_count}/{total_count} successful")
    
    return success_count == total_count

def test_serena_core_creation():
    """Test creating SerenaCore directly."""
    try:
        from graph_sitter.extensions.lsp.serena.core import SerenaCore
        from graph_sitter.extensions.lsp.serena.types import SerenaConfig
        
        print("🏗️ Testing SerenaCore creation...")
        
        config = SerenaConfig()
        print(f"   ✅ SerenaConfig created: {config}")
        
        # Try to create SerenaCore (this might be async)
        core = SerenaCore(".", config)
        print(f"   ✅ SerenaCore created: {core}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SerenaCore creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Testing Serena Auto-Initialization")
    print("=" * 50)
    
    # Test 1: Check dependencies
    print("\n🔍 Testing Dependencies")
    print("-" * 30)
    deps_ok = test_import_dependencies()
    
    # Test 2: Test auto-init import
    print("\n📦 Testing Auto-Init Import")
    print("-" * 35)
    auto_init_ok = test_auto_init_import()
    
    # Test 3: Test manual initialization
    print("\n🔧 Testing Manual Initialization")
    print("-" * 40)
    manual_init_ok = test_manual_initialization()
    
    # Test 4: Test SerenaCore creation
    print("\n🏗️ Testing SerenaCore Creation")
    print("-" * 40)
    core_ok = test_serena_core_creation()
    
    # Test 5: Check Codebase class
    print("\n🔍 Testing Codebase Class")
    print("-" * 30)
    codebase_ok = test_codebase_after_init()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"Auto-init import: {'✅' if auto_init_ok else '❌'}")
    print(f"Manual initialization: {'✅' if manual_init_ok else '❌'}")
    print(f"SerenaCore creation: {'✅' if core_ok else '❌'}")
    print(f"Codebase methods: {'✅' if codebase_ok else '❌'}")
    
    overall_success = deps_ok and (auto_init_ok or manual_init_ok) and codebase_ok
    print(f"\n🎉 Overall Auto-Init: {'✅ SUCCESS' if overall_success else '❌ NEEDS WORK'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
