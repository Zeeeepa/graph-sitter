#!/usr/bin/env python3
"""
Comprehensive test of graph-sitter with all fixes applied
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all key imports"""
    print("🔍 Testing imports...")
    
    tests = [
        ("graph_sitter", "Main package"),
        ("graph_sitter.core.codebase", "Core codebase"),
        ("graph_sitter.extensions.serena", "Serena extension"),
        ("graph_sitter.extensions.serena.integration", "Serena integration module"),
        ("graph_sitter.core.diagnostics", "Diagnostics"),
        ("graph_sitter.extensions.lsp.transaction_manager", "LSP transaction manager"),
    ]
    
    for module, description in tests:
        try:
            __import__(module)
            print(f"  ✅ {description} - OK")
        except Exception as e:
            print(f"  ❌ {description} - ERROR: {e}")
            return False
    
    return True

def test_codebase_creation():
    """Test codebase creation with Serena integration"""
    print("\n🏗️  Testing codebase creation...")
    
    try:
        from graph_sitter import Codebase
        codebase = Codebase("./")
        print(f"  ✅ Codebase created: {codebase.name}")
        print(f"  📁 Path: {codebase.repo_path}")
        print(f"  🔧 Language: {codebase.language}")
        print(f"  📄 Files: {len(codebase.files)}")
        return True
    except Exception as e:
        print(f"  ❌ Codebase creation failed: {e}")
        return False

def test_pink_sdk():
    """Test pink SDK integration"""
    print("\n📦 Testing pink SDK integration...")
    
    try:
        from graph_sitter.configs.models.codebase import PinkMode
        print(f"  ✅ PinkMode enum imported: {list(PinkMode)}")
        
        # Test that the import fix is working
        from graph_sitter.core.codebase import Codebase
        print("  ✅ Pink SDK import fix verified")
        return True
    except Exception as e:
        print(f"  ❌ Pink SDK test failed: {e}")
        return False

def test_serena_features():
    """Test Serena features"""
    print("\n🚀 Testing Serena features...")
    
    try:
        from graph_sitter.extensions.serena import SerenaIntegration, SerenaCore
        print("  ✅ Serena classes imported")
        
        # Test that we can create a SerenaIntegration (mock)
        class MockCodebase:
            def __init__(self):
                self.repo_path = Path("./")
        
        mock_codebase = MockCodebase()
        integration = SerenaIntegration(mock_codebase)
        print("  ✅ SerenaIntegration created")
        return True
    except Exception as e:
        print(f"  ❌ Serena features test failed: {e}")
        return False

def test_lsp_manager():
    """Test LSP manager without weak reference issues"""
    print("\n🔧 Testing LSP manager...")
    
    try:
        from graph_sitter.extensions.lsp.transaction_manager import get_lsp_manager
        
        # This should not raise the weak reference error anymore
        manager = get_lsp_manager("./", enable_lsp=True)
        print("  ✅ LSP manager created without weak reference error")
        return True
    except Exception as e:
        print(f"  ❌ LSP manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Comprehensive Graph-Sitter Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_pink_sdk,
        test_lsp_manager,
        test_serena_features,
        test_codebase_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("📊 Test Results:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Graph-sitter is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
