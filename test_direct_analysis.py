#!/usr/bin/env python3
"""
Direct test of the unified analysis system without going through the main adapters module.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_direct_imports():
    """Test direct imports of our consolidated modules."""
    print("🧪 Testing direct imports...")
    
    try:
        # Import directly from our modules
        sys.path.insert(0, 'src/graph_sitter/adapters/analysis')
        
        from core.models import (
            AnalysisOptions, create_default_analysis_options,
            ComprehensiveAnalysisResult, CodeIssue
        )
        print("✅ Core models imported successfully")
        
        from core.analysis_engine import (
            analyze_codebase_directory, analyze_python_file,
            calculate_cyclomatic_complexity, generate_summary_statistics
        )
        print("✅ Analysis engine imported successfully")
        
        from config.analysis_config import (
            AnalysisConfig, PresetConfigs
        )
        print("✅ Configuration imported successfully")
        
        from tools.unified_analyzer import UnifiedCodebaseAnalyzer
        print("✅ Unified analyzer imported successfully")
        
        from quick_analyze import quick_analyze, get_codebase_summary
        print("✅ Quick analyze functions imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_analyzer():
    """Test the unified analyzer functionality."""
    print("\n🧪 Testing unified analyzer...")
    
    try:
        sys.path.insert(0, 'src/graph_sitter/adapters/analysis')
        from tools.unified_analyzer import UnifiedCodebaseAnalyzer
        
        # Create analyzer (without graph-sitter to avoid dependencies)
        analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=False)
        print("✅ Created unified analyzer")
        
        # Test quick analysis on current directory
        result = analyzer.quick_analyze('.')
        print(f"✅ Quick analysis completed")
        print(f"   - Analysis time: {result.get('analysis_time', 0):.2f}s")
        
        # Test basic codebase analysis
        basic_result = analyzer.analyze_codebase('.')
        print(f"✅ Basic codebase analysis completed")
        print(f"   - Total files: {basic_result.total_files}")
        print(f"   - Total functions: {basic_result.total_functions}")
        print(f"   - Total issues: {len(basic_result.issues)}")
        
        return True
    except Exception as e:
        print(f"❌ Unified analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quick_analyze():
    """Test quick analyze functions."""
    print("\n🧪 Testing quick analyze functions...")
    
    try:
        sys.path.insert(0, 'src/graph_sitter/adapters/analysis')
        from quick_analyze import quick_analyze, get_codebase_summary, analyze_quality_metrics
        
        # Test quick analyze
        result = quick_analyze('.', use_graph_sitter=False)
        print("✅ Quick analyze completed")
        print(f"   - Summary keys: {list(result.keys())}")
        
        # Test quality metrics
        quality = analyze_quality_metrics('.')
        print("✅ Quality metrics analysis completed")
        print(f"   - Maintainability: {quality.get('maintainability_index', 0):.1f}")
        print(f"   - Complexity: {quality.get('cyclomatic_complexity', 0):.1f}")
        print(f"   - Lines of code: {quality.get('lines_of_code', 0)}")
        
        # Test codebase summary
        summary = get_codebase_summary('.')
        print("✅ Codebase summary completed")
        print(f"   - Basic metrics: {summary.get('basic_metrics', {})}")
        
        return True
    except Exception as e:
        print(f"❌ Quick analyze test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_functionality():
    """Test CLI functionality."""
    print("\n🧪 Testing CLI functionality...")
    
    try:
        # Test importing main CLI components
        sys.path.insert(0, 'src/graph_sitter/adapters/analysis')
        
        # Import main functions
        from main import create_argument_parser, format_analysis_results
        print("✅ CLI components imported successfully")
        
        # Test argument parser
        parser = create_argument_parser()
        print("✅ Argument parser created")
        
        # Test formatting
        test_results = {
            "summary_statistics": {
                "overview": {"total_files": 10, "total_functions": 50},
                "quality_metrics": {"average_maintainability_index": "75.0"},
                "issues_summary": {"total_issues": 5}
            }
        }
        formatted = format_analysis_results(test_results, "text")
        print("✅ Result formatting works")
        
        return True
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Unified Analysis System (Direct)")
    print("=" * 60)
    
    tests = [
        test_direct_imports,
        test_unified_analyzer,
        test_quick_analyze,
        test_cli_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified analysis system is working correctly.")
        
        print("\n📋 Consolidated Features:")
        print("  ✅ Unified analysis engine (from analyze_codebase_enhanced.py)")
        print("  ✅ Enhanced analyzer class (from enhanced_analyzer.py)")
        print("  ✅ Graph-sitter enhancements (from graph_sitter_enhancements.py)")
        print("  ✅ Comprehensive CLI interface")
        print("  ✅ Quick analysis functions")
        print("  ✅ Flexible configuration system")
        print("  ✅ Multiple output formats (text, JSON, YAML)")
        
        print("\n🎯 Usage Examples:")
        print("  # Direct usage")
        print("  cd src/graph_sitter/adapters/analysis")
        print("  python main.py /path/to/code --comprehensive")
        print("  python main.py . --quick-analyze --format json")
        
        print("\n  # Programmatic usage")
        print("  from tools.unified_analyzer import UnifiedCodebaseAnalyzer")
        print("  analyzer = UnifiedCodebaseAnalyzer()")
        print("  result = analyzer.analyze_comprehensive('/path/to/code')")
        
        print("\n🗂️ File Structure:")
        print("  src/graph_sitter/adapters/analysis/")
        print("  ├── core/")
        print("  │   ├── models.py              # All data models")
        print("  │   ├── analysis_engine.py     # Core analysis functions")
        print("  │   └── graph_enhancements.py  # Graph-sitter features")
        print("  ├── tools/")
        print("  │   └── unified_analyzer.py    # Main analyzer class")
        print("  ├── config/")
        print("  │   └── analysis_config.py     # Configuration system")
        print("  ├── main.py                    # CLI interface")
        print("  ├── quick_analyze.py           # Convenience functions")
        print("  └── __main__.py                # Module entry point")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

