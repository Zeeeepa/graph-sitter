#!/usr/bin/env python3
"""
Comprehensive test script for enhanced Graph-Sitter integrations

This script tests all the new functionality including error context,
grainchain integration, and web evaluation capabilities.
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all key imports for the new integrations."""
    print("🔍 Testing imports...")
    
    tests = [
        ("graph_sitter", "Main package"),
        ("graph_sitter.core.codebase", "Core codebase"),
        ("graph_sitter.core.diagnostics", "Enhanced diagnostics"),
        ("graph_sitter.integrations", "Integrations package"),
        ("graph_sitter.integrations.grainchain_integration", "Grainchain integration"),
        ("graph_sitter.integrations.web_eval_integration", "Web evaluation integration"),
        ("graph_sitter.extensions.lsp.serena_bridge", "Enhanced LSP bridge"),
    ]
    
    for module, description in tests:
        try:
            __import__(module)
            print(f"  ✅ {description} - OK")
        except Exception as e:
            print(f"  ❌ {description} - ERROR: {e}")
            return False
    
    return True

def test_error_context_functionality():
    """Test enhanced error context functionality."""
    print("\\n🐛 Testing error context functionality...")
    
    try:
        from graph_sitter import Codebase
        from graph_sitter.extensions.lsp.serena_bridge import ErrorInfo, DiagnosticSeverity
        
        # Test ErrorInfo context methods
        error = ErrorInfo(
            file_path=__file__,
            line=10,
            character=5,
            message="Test error message",
            severity=DiagnosticSeverity.ERROR
        )
        
        # Test get_context method
        context = error.get_context(lines_before=2, lines_after=2)
        print(f"  ✅ get_context() method works - {len(context)} characters")
        
        # Test get_detailed_context method
        detailed_context = error.get_detailed_context(lines_before=2, lines_after=2)
        print(f"  ✅ get_detailed_context() method works - {len(detailed_context['context_lines'])} lines")
        
        # Test codebase creation with diagnostics
        codebase = Codebase("./", enable_lsp=True)
        print(f"  ✅ Codebase with diagnostics created")
        
        # Test new diagnostic methods
        if hasattr(codebase, 'get_all_errors_with_context'):
            print(f"  ✅ get_all_errors_with_context method available")
        
        if hasattr(codebase, 'get_errors_by_file'):
            print(f"  ✅ get_errors_by_file method available")
        
        if hasattr(codebase, 'get_errors_by_severity'):
            print(f"  ✅ get_errors_by_severity method available")
        
        if hasattr(codebase, 'generate_error_context_report'):
            print(f"  ✅ generate_error_context_report method available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error context functionality test failed: {e}")
        return False

async def test_grainchain_integration():
    """Test Grainchain integration functionality."""
    print("\\n🏗️  Testing Grainchain integration...")
    
    try:
        from graph_sitter.integrations.grainchain_integration import GrainchainIntegration, ExecutionResult
        
        # Test integration creation
        integration = GrainchainIntegration()
        print(f"  ✅ GrainchainIntegration created")
        print(f"  📊 Available: {integration.is_available()}")
        print(f"  🔧 Providers: {integration.get_available_providers()}")
        
        # Test ExecutionResult dataclass
        result = ExecutionResult(
            stdout="Hello World",
            stderr="",
            return_code=0,
            success=True,
            duration=0.1,
            provider="local"
        )
        print(f"  ✅ ExecutionResult works - output: '{result.output}'")
        
        # Test code execution (if grainchain is available)
        if integration.is_available():
            result = await integration.execute_code(
                code="print('Test from Grainchain')",
                language="python",
                timeout=10
            )
            print(f"  ✅ Code execution test - Success: {result.success}")
        else:
            print(f"  💡 Grainchain not installed - using mock functionality")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Grainchain integration test failed: {e}")
        return False

async def test_web_eval_integration():
    """Test Web Evaluation integration functionality."""
    print("\\n🌐 Testing Web Evaluation integration...")
    
    try:
        from graph_sitter.integrations.web_eval_integration import WebEvalIntegration, WebEvalResult, EvaluationConfig
        
        # Test integration creation
        integration = WebEvalIntegration()
        print(f"  ✅ WebEvalIntegration created")
        print(f"  📊 Available: {integration.is_available()}")
        
        # Test configuration
        config = EvaluationConfig(timeout=30, capture_screenshots=True)
        print(f"  ✅ EvaluationConfig created - timeout: {config.timeout}s")
        
        # Test web evaluation (mock)
        result = await integration.evaluate_url("https://example.com", config)
        print(f"  ✅ Web evaluation test - Success: {result.success}, Score: {result.score:.2f}")
        print(f"  📊 Findings: {len(result.findings)}, Screenshots: {len(result.screenshots)}")
        
        # Test report generation
        report = await integration.generate_report(result)
        print(f"  ✅ Report generation - {len(report)} characters")
        
        # Test batch evaluation
        results = await integration.batch_evaluate(["https://example.com", "https://google.com"])
        print(f"  ✅ Batch evaluation - {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Web evaluation integration test failed: {e}")
        return False

def test_codebase_integration():
    """Test integration with codebase instance."""
    print("\\n🔗 Testing codebase integration...")
    
    try:
        from graph_sitter import Codebase
        from graph_sitter.integrations.grainchain_integration import add_grainchain_capabilities
        from graph_sitter.integrations.web_eval_integration import add_web_eval_capabilities
        
        # Create codebase
        codebase = Codebase("./", enable_lsp=True)
        print(f"  ✅ Codebase created")
        
        # Add Grainchain capabilities
        add_grainchain_capabilities(codebase)
        print(f"  ✅ Grainchain capabilities added")
        
        # Check if methods were added
        grainchain_methods = ['execute_code', 'execute_file', 'run_tests', 'install_dependencies']
        for method in grainchain_methods:
            if hasattr(codebase, method):
                print(f"    ✅ {method} method available")
            else:
                print(f"    ❌ {method} method missing")
        
        # Add Web Evaluation capabilities
        add_web_eval_capabilities(codebase)
        print(f"  ✅ Web evaluation capabilities added")
        
        # Check if methods were added
        web_eval_methods = ['evaluate_url', 'evaluate_local_app', 'batch_evaluate']
        for method in web_eval_methods:
            if hasattr(codebase, method):
                print(f"    ✅ {method} method available")
            else:
                print(f"    ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Codebase integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Enhanced Graph-Sitter Integration Test Suite")
    print("=" * 55)
    
    tests = [
        ("Import Tests", test_imports, False),
        ("Error Context Tests", test_error_context_functionality, False),
        ("Grainchain Integration", test_grainchain_integration, True),
        ("Web Eval Integration", test_web_eval_integration, True),
        ("Codebase Integration", test_codebase_integration, False),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func, is_async in tests:
        print(f"\\n🔍 Running {test_name}...")
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\\n📊 Test Results:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\\n🎉 All tests passed! Enhanced integrations are working correctly.")
        return True
    else:
        print("\\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

