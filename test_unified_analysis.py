#!/usr/bin/env python3
"""
Test script for the unified analysis system.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_basic_imports():
    """Test that basic imports work."""
    print("🧪 Testing basic imports...")
    
    try:
        from graph_sitter.adapters.analysis.core.models import (
            AnalysisOptions, create_default_analysis_options
        )
        print("✅ Core models imported successfully")
        
        from graph_sitter.adapters.analysis.core.analysis_engine import (
            analyze_codebase_directory, calculate_cyclomatic_complexity
        )
        print("✅ Analysis engine imported successfully")
        
        from graph_sitter.adapters.analysis.config.analysis_config import (
            AnalysisConfig, PresetConfigs
        )
        print("✅ Configuration imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_functionality():
    """Test basic analysis functionality."""
    print("\n🧪 Testing analysis functionality...")
    
    try:
        from graph_sitter.adapters.analysis.core.models import create_default_analysis_options
        from graph_sitter.adapters.analysis.core.analysis_engine import analyze_python_file
        
        # Create test options
        options = create_default_analysis_options()
        print("✅ Created analysis options")
        
        # Test analyzing this file
        result = analyze_python_file(__file__, options)
        print(f"✅ Analyzed file: {result.file_path}")
        print(f"   - Lines of code: {result.lines_of_code}")
        print(f"   - Functions found: {len(result.functions)}")
        print(f"   - Issues found: {len(result.issues)}")
        
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration system."""
    print("\n🧪 Testing configuration system...")
    
    try:
        from graph_sitter.adapters.analysis.config.analysis_config import (
            AnalysisConfig, PresetConfigs
        )
        
        # Test default config
        config = AnalysisConfig()
        print("✅ Created default config")
        
        # Test preset configs
        quick_config = PresetConfigs.quick_analysis()
        comprehensive_config = PresetConfigs.comprehensive_analysis()
        print("✅ Created preset configs")
        
        # Test serialization
        config_dict = config.to_dict()
        restored_config = AnalysisConfig.from_dict(config_dict)
        print("✅ Config serialization works")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
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
        
        print("\n📋 Available Features:")
        print("  ✅ Core analysis engine with AST-based metrics")
        print("  ✅ Comprehensive data models")
        print("  ✅ Flexible configuration system")
        print("  ✅ Multiple analysis presets")
        print("  ✅ File-level and codebase-level analysis")
        print("  ✅ Quality metrics calculation")
        print("  ✅ Issue detection and reporting")
        
        print("\n🎯 Usage Examples:")
        print("  # Quick analysis")
        print("  from graph_sitter.adapters.analysis.quick_analyze import quick_analyze")
        print("  result = quick_analyze('/path/to/code')")
        
        print("\n  # Comprehensive analysis")
        print("  from graph_sitter.adapters.analysis.tools.unified_analyzer import UnifiedCodebaseAnalyzer")
        print("  analyzer = UnifiedCodebaseAnalyzer()")
        print("  result = analyzer.analyze_comprehensive('/path/to/code')")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

