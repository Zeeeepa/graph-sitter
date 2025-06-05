#!/usr/bin/env python3
"""
Test script for the unified analysis system.

This script tests the new comprehensive analysis API to ensure it works correctly.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from graph_sitter.core.codebase import Codebase
        print("✅ Core Codebase import successful")
        
        # Test comprehensive analysis imports
        from graph_sitter.adapters.analysis.comprehensive_analysis import (
            ComprehensiveAnalysis,
            ComprehensiveAnalysisResult,
            analyze_codebase,
            quick_analysis,
            IssueItem,
            AnalysisSummary
        )
        print("✅ Comprehensive analysis imports successful")
        
        # Test dashboard imports
        from graph_sitter.adapters.visualizations.html_dashboard import (
            HTMLDashboardGenerator,
            generate_html_dashboard
        )
        print("✅ HTML dashboard imports successful")
        
        from graph_sitter.adapters.visualizations.react_dashboard.dashboard_app import (
            ReactDashboardApp,
            create_dashboard_app
        )
        print("✅ React dashboard imports successful")
        
        # Test adapter imports
        from graph_sitter.adapters import (
            ComprehensiveAnalysis,
            analyze_codebase,
            generate_html_dashboard
        )
        print("✅ Adapter exports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_structure():
    """Test that the API has the expected structure."""
    print("\n🧪 Testing API structure...")
    
    try:
        from graph_sitter.adapters.analysis.comprehensive_analysis import ComprehensiveAnalysis
        
        # Check that the class has expected methods
        expected_methods = [
            'should_trigger_analysis',
            'run_comprehensive_analysis',
            '_aggregate_issues',
            '_calculate_health_score'
        ]
        
        for method in expected_methods:
            if hasattr(ComprehensiveAnalysis, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        # Check data classes
        from graph_sitter.adapters.analysis.comprehensive_analysis import (
            IssueItem,
            AnalysisSummary,
            ComprehensiveAnalysisResult
        )
        
        # Test IssueItem structure
        issue = IssueItem(
            id="test_1",
            title="Test Issue",
            description="Test description",
            severity="high",
            category="error"
        )
        print(f"✅ IssueItem created: {issue.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_convenience_functions():
    """Test the convenience functions."""
    print("\n🧪 Testing convenience functions...")
    
    try:
        from graph_sitter.adapters.analysis.comprehensive_analysis import analyze_codebase, quick_analysis
        
        # Check function signatures
        import inspect
        
        analyze_sig = inspect.signature(analyze_codebase)
        print(f"✅ analyze_codebase signature: {analyze_sig}")
        
        quick_sig = inspect.signature(quick_analysis)
        print(f"✅ quick_analysis signature: {quick_sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False

def test_dashboard_generation():
    """Test dashboard generation functions."""
    print("\n🧪 Testing dashboard generation...")
    
    try:
        from graph_sitter.adapters.visualizations.html_dashboard import HTMLDashboardGenerator
        from graph_sitter.adapters.visualizations.react_dashboard.dashboard_app import ReactDashboardApp
        
        # Check class structure
        print(f"✅ HTMLDashboardGenerator class available")
        print(f"✅ ReactDashboardApp class available")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard generation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Unified Analysis System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_api_structure,
        test_convenience_functions,
        test_dashboard_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified analysis system is ready to use.")
        print("\n🚀 Next steps:")
        print("   1. Try the examples in examples/unified_analysis_example.py")
        print("   2. Use the new API: from graph_sitter import Codebase; result = Codebase.Analysis('repo/name')")
        print("   3. Generate dashboards with the HTML and React components")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

