#!/usr/bin/env python3
"""
Test script for the unified analysis system.
"""

import sys
import os
sys.path.insert(0, 'src')

from contexten.extensions.graph_sitter.analysis.core.models import (
    AnalysisOptions,
    ComprehensiveAnalysisResult,
    FileAnalysis,
    FunctionMetrics,
    create_default_analysis_options,
)
from contexten.extensions.graph_sitter.analysis.core.analysis_engine import (
    analyze_python_file,
    calculate_cyclomatic_complexity,
)

def test_basic_imports():
    """Test that basic imports work."""
    try:
        from contexten.extensions.graph_sitter.analysis.core.models import (
            AnalysisOptions,
            ComprehensiveAnalysisResult,
            FileAnalysis,
            FunctionMetrics,
            create_default_analysis_options,
        )
        from contexten.extensions.graph_sitter.analysis.core.analysis_engine import (
            analyze_python_file,
            calculate_cyclomatic_complexity,
        )
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_analysis_functionality():
    """Test basic analysis functionality."""
    print("\n🔬 Testing analysis functionality...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core.models import create_default_analysis_options
        from contexten.extensions.graph_sitter.analysis.core.analysis_engine import analyze_python_file, calculate_cyclomatic_complexity
        
        # Create test options
        options = create_default_analysis_options()
        print(f"✅ Created analysis options: {type(options)}")
        
        # Test file analysis (using this test file itself)
        test_file = __file__
        if test_file.endswith('.py'):
            try:
                result = analyze_python_file(test_file, options)
                print(f"✅ Analyzed file: {result.file_path}")
                print(f"   Functions: {len(result.functions)}")
                print(f"   Classes: {len(result.classes)}")
                print(f"   Lines: {result.lines_of_code}")
                return True
            except Exception as e:
                print(f"⚠️ File analysis failed: {e}")
                return False
        else:
            print("⚠️ No Python file to analyze")
            return False
            
    except Exception as e:
        print(f"❌ Analysis functionality test failed: {e}")
        return False


def test_configuration():
    """Test configuration functionality."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core.models import create_default_analysis_options
        
        # Test creating default options
        options = create_default_analysis_options()
        print(f"✅ Created default analysis options: {type(options)}")
        
        # Test options attributes
        if hasattr(options, 'include_metrics'):
            print(f"   Include metrics: {options.include_metrics}")
        if hasattr(options, 'include_complexity'):
            print(f"   Include complexity: {options.include_complexity}")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Unified Analysis System")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_analysis_functionality,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified analysis system is working correctly.")
        
        print("\n📚 Usage Examples:")
        print("  from contexten.extensions.graph_sitter.analysis.quick_analyze import quick_analyze")
        print("  result = quick_analyze('/path/to/code')")
        print()
        print("  from contexten.extensions.graph_sitter.analysis.tools.unified_analyzer import UnifiedCodebaseAnalyzer")
        print("  analyzer = UnifiedCodebaseAnalyzer()")
        print("  result = analyzer.analyze('/path/to/code')")
        
        print("\n🎯 Usage Examples:")
        print("  # Quick analysis")
        print("  from contexten.extensions.graph_sitter.analysis.quick_analyze import quick_analyze")
        print("  result = quick_analyze('/path/to/code')")
        print()
        print("  # Detailed analysis")
        print("  from contexten.extensions.graph_sitter.analysis.tools.unified_analyzer import UnifiedCodebaseAnalyzer")
        print("  analyzer = UnifiedCodebaseAnalyzer()")
        print("  result = analyzer.analyze('/path/to/code')")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
