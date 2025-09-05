#!/usr/bin/env python3
"""
Comprehensive test script for the upgraded Serena MCP integration.

This script tests all major components of the new MCP-based Serena integration
to ensure everything works correctly after the upgrade.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from graph_sitter.extensions.serena.core import SerenaCore
from graph_sitter.extensions.serena.mcp_bridge import SerenaMCPBridge
from graph_sitter.extensions.serena.semantic_tools import SemanticTools
from graph_sitter.core.codebase import Codebase


def test_mcp_bridge():
    """Test MCP bridge initialization and basic functionality."""
    print("🔧 Testing MCP Bridge...")
    
    try:
        bridge = SerenaMCPBridge(os.getcwd())
        
        # Test initialization
        assert bridge.is_initialized, "MCP bridge should be initialized"
        assert len(bridge.available_tools) > 0, "Should have available tools"
        
        # Test tool availability
        assert bridge.is_tool_available('read_file'), "read_file tool should be available"
        assert bridge.is_tool_available('find_symbol'), "find_symbol tool should be available"
        
        # Test basic tool call
        result = bridge.call_tool('read_file', {
            'file_path': 'src/graph_sitter/extensions/serena/core.py',
            'start_line': 1,
            'end_line': 5
        })
        assert result.success, "File reading should succeed"
        
        bridge.shutdown()
        print("✅ MCP Bridge tests passed")
        return True
        
    except Exception as e:
        print(f"❌ MCP Bridge test failed: {e}")
        return False


def test_semantic_tools():
    """Test semantic tools functionality."""
    print("🧠 Testing Semantic Tools...")
    
    try:
        bridge = SerenaMCPBridge(os.getcwd())
        semantic_tools = SemanticTools(bridge)
        
        # Test tool availability
        available_tools = semantic_tools.get_available_tools()
        assert len(available_tools) > 0, "Should have available tools"
        
        # Test pattern search (using available tool)
        if bridge.is_tool_available('search_for_pattern'):
            result = bridge.call_tool('search_for_pattern', {
                'pattern': 'class SerenaCore',
                'max_results': 5
            })
            assert result.success, "Pattern search should succeed"
        
        # Test symbol finding (using available tool)
        if bridge.is_tool_available('find_symbol'):
            result = bridge.call_tool('find_symbol', {
                'name_path': 'SerenaCore'
            })
            assert result.success, "Symbol finding should succeed"
        
        bridge.shutdown()
        print("✅ Semantic Tools tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Semantic Tools test failed: {e}")
        return False


def test_serena_core():
    """Test full SerenaCore integration."""
    print("🎯 Testing SerenaCore Integration...")
    
    try:
        # Create codebase (this might take a while)
        print("  📊 Building codebase graph...")
        codebase = Codebase(os.getcwd())
        
        # Initialize SerenaCore
        print("  🚀 Initializing SerenaCore...")
        serena = SerenaCore(codebase)
        
        # Test initialization
        assert serena.mcp_bridge.is_initialized, "MCP bridge should be initialized"
        assert len(serena.mcp_bridge.available_tools) > 0, "Should have tools available"
        
        # Test semantic tools integration
        available_tools = serena.semantic_tools.get_available_tools()
        assert len(available_tools) > 0, "Semantic tools should be available"
        
        # Test status
        status = serena.get_status()
        assert 'mcp_bridge_status' in status, "Status should include MCP bridge info"
        assert status['mcp_bridge_status']['initialized'], "MCP bridge should be initialized"
        
        # Test find_symbol method (even if it returns empty, it should not crash)
        symbols = serena.find_symbol('SerenaCore')
        assert isinstance(symbols, list), "find_symbol should return a list"
        
        # Test shutdown
        serena.shutdown()
        print("✅ SerenaCore Integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ SerenaCore Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that the API remains backward compatible."""
    print("🔄 Testing Backward Compatibility...")
    
    try:
        codebase = Codebase(os.getcwd())
        serena = SerenaCore(codebase)
        
        # Test that old API methods still exist and work
        methods_to_test = [
            'get_symbol_info',
            'get_completions', 
            'get_hover_info',
            'find_symbol',
            'get_status',
            'shutdown'
        ]
        
        for method_name in methods_to_test:
            assert hasattr(serena, method_name), f"Method {method_name} should exist"
        
        # Test some method calls (they might return empty results but shouldn't crash)
        symbol_info = serena.get_symbol_info('src/graph_sitter/extensions/serena/core.py', 10, 5)
        completions = serena.get_completions('src/graph_sitter/extensions/serena/core.py', 10, 5)
        hover_info = serena.get_hover_info('src/graph_sitter/extensions/serena/core.py', 10, 5)
        
        # These should return appropriate types even if empty
        assert symbol_info is None or isinstance(symbol_info, dict), "symbol_info should be dict or None"
        assert isinstance(completions, list), "completions should be a list"
        assert hover_info is None or isinstance(hover_info, dict), "hover_info should be dict or None"
        
        serena.shutdown()
        print("✅ Backward Compatibility tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Backward Compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Starting Serena MCP Integration Tests")
    print("=" * 50)
    
    tests = [
        test_mcp_bridge,
        test_semantic_tools,
        test_serena_core,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Serena MCP integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

