#!/usr/bin/env python3
"""
Test script for the comprehensive codebase analysis tool.
"""
import sys
import os
from comprehensive_codebase_analysis import CodebaseAnalyzer, IssueSeverity

def test_analyzer_initialization():
    """Test that the analyzer initializes correctly."""
    analyzer = CodebaseAnalyzer("test/repo")
    assert analyzer.repo_path == "test/repo"
    assert analyzer.language is None
    assert analyzer.codebase is None
    print("✅ Analyzer initialization test passed")

def test_issue_severity():
    """Test issue severity enum."""
    assert IssueSeverity.CRITICAL.value == "⚠️ Critical"
    assert IssueSeverity.MAJOR.value == "👉 Major"
    assert IssueSeverity.MINOR.value == "🔍 Minor"
    print("✅ Issue severity test passed")

def test_helper_methods():
    """Test helper methods."""
    analyzer = CodebaseAnalyzer("test/repo")
    
    # Test _is_test_file method
    class MockFile:
        def __init__(self, filepath):
            self.filepath = filepath
    
    test_file = MockFile("src/test_module.py")
    non_test_file = MockFile("src/main.py")
    
    assert analyzer._is_test_file(test_file) == True
    assert analyzer._is_test_file(non_test_file) == False
    print("✅ Helper methods test passed")

def main():
    """Run all tests."""
    print("Running comprehensive analysis tests...")
    
    try:
        test_analyzer_initialization()
        test_issue_severity()
        test_helper_methods()
        
        print("\n🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
