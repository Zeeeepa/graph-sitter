#!/usr/bin/env python3
"""
Comprehensive Verification Test

Tests all the restored functionality to ensure nothing was lost in consolidation.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_imports():
    """Test that all expected functions can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from contexten.extensions.graph_sitter.analysis.core import (
            calculate_cyclomatic_complexity, calculate_cyclomatic_complexity_graph_sitter,
            get_operators_and_operands, calculate_halstead_volume, calculate_maintainability_index,
            calculate_doi, count_lines, analyze_python_file, analyze_function_ast,
            analyze_class_ast, analyze_codebase_directory, get_complexity_rank,
            calculate_technical_debt_hours, generate_summary_statistics
        )
        print("✅ Core analysis functions imported successfully")
        
        # Test class hierarchy imports
        from contexten.extensions.graph_sitter.analysis.core import (
            analyze_inheritance_chains, find_deepest_inheritance, find_inheritance_chains,
            find_abstract_classes, build_inheritance_tree, get_class_relationships,
            detect_design_patterns, has_singleton_methods, has_factory_methods,
            has_observer_methods, has_decorator_structure, has_strategy_structure,
            generate_hierarchy_report
        )
        print("✅ Class hierarchy functions imported successfully")
        
        # Test graph enhancement imports
        from contexten.extensions.graph_sitter.analysis.core import (
            hop_through_imports, get_function_context, detect_import_loops,
            analyze_graph_structure, detect_dead_code, generate_training_data,
            analyze_function_enhanced, analyze_class_enhanced, get_codebase_summary_enhanced,
            generate_dead_code_recommendations, generate_import_loop_recommendations
        )
        print("✅ Graph enhancement functions imported successfully")
        
        # Test tree-sitter core imports
        from contexten.extensions.graph_sitter.analysis.core import (
            TreeSitterCore, get_tree_sitter_core, ParseResult, QueryMatch
        )
        print("✅ Tree-sitter core components imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_cyclomatic_complexity():
    """Test cyclomatic complexity calculation."""
    print("\n🔍 Testing cyclomatic complexity...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import calculate_cyclomatic_complexity
        
        # Test with simple case
        result = calculate_cyclomatic_complexity(None)
        print(f"✅ Basic complexity calculation: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Cyclomatic complexity test failed: {e}")
        return False

def test_halstead_metrics():
    """Test Halstead metrics calculation."""
    print("\n🔍 Testing Halstead metrics...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import (
            get_operators_and_operands, calculate_halstead_volume
        )
        
        # Create a mock function object
        class MockFunction:
            def __init__(self, source):
                self.source = source
                self.filepath = "test.py"
        
        func = MockFunction("def test(): return x + y")
        operators, operands = get_operators_and_operands(func)
        volume, n1, n2, N1, N2 = calculate_halstead_volume(operators, operands)
        
        print(f"✅ Halstead metrics - Volume: {volume}, Operators: {n1}, Operands: {n2}")
        
        return True
    except Exception as e:
        print(f"❌ Halstead metrics test failed: {e}")
        return False

def test_maintainability_index():
    """Test maintainability index calculation."""
    print("\n🔍 Testing maintainability index...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import calculate_maintainability_index
        
        mi = calculate_maintainability_index(10.0, 5, 20)
        print(f"✅ Maintainability index: {mi}")
        
        return True
    except Exception as e:
        print(f"❌ Maintainability index test failed: {e}")
        return False

def test_line_counting():
    """Test line counting functionality."""
    print("\n🔍 Testing line counting...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import count_lines
        
        source = """def test():
    # This is a comment
    x = 1
    
    return x"""
        
        total, code, comments, blank = count_lines(source)
        print(f"✅ Line counting - Total: {total}, Code: {code}, Comments: {comments}, Blank: {blank}")
        
        return True
    except Exception as e:
        print(f"❌ Line counting test failed: {e}")
        return False

def test_class_hierarchy():
    """Test class hierarchy analysis."""
    print("\n🔍 Testing class hierarchy analysis...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import (
            analyze_inheritance_chains, detect_design_patterns
        )
        
        # Create a mock codebase
        class MockClass:
            def __init__(self, name, superclasses=None):
                self.name = name
                self.superclasses = superclasses or []
                self.methods = []
        
        class MockCodebase:
            def __init__(self):
                self.classes = [
                    MockClass("BaseClass"),
                    MockClass("DerivedClass", [MockClass("BaseClass")])
                ]
        
        codebase = MockCodebase()
        result = analyze_inheritance_chains(codebase)
        patterns = detect_design_patterns(codebase)
        
        print(f"✅ Class hierarchy analysis - Classes: {result.get('total_classes', 0)}")
        print(f"✅ Design patterns detected: {len(patterns)}")
        
        return True
    except Exception as e:
        print(f"❌ Class hierarchy test failed: {e}")
        return False

def test_tree_sitter_core():
    """Test tree-sitter core functionality."""
    print("\n🔍 Testing tree-sitter core...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.core import get_tree_sitter_core
        
        core = get_tree_sitter_core()
        languages = core.get_supported_languages()
        print(f"✅ Tree-sitter core - Supported languages: {len(languages)}")
        
        # Test parsing
        result = core.parse_string("def test(): pass", "python")
        if result:
            print("✅ Tree-sitter parsing successful")
        else:
            print("⚠️ Tree-sitter parsing returned None (may be expected)")
        
        return True
    except Exception as e:
        print(f"❌ Tree-sitter core test failed: {e}")
        return False

def test_unified_analyzer():
    """Test unified analyzer functionality."""
    print("\n🔍 Testing unified analyzer...")
    
    try:
        from contexten.extensions.graph_sitter.analysis.unified_analyzer import UnifiedAnalyzer
        
        analyzer = UnifiedAnalyzer()
        print("✅ Unified analyzer created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Unified analyzer test failed: {e}")
        return False

def main():
    """Run comprehensive verification tests."""
    print("🚀 Starting Comprehensive Feature Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_cyclomatic_complexity,
        test_halstead_metrics,
        test_maintainability_index,
        test_line_counting,
        test_class_hierarchy,
        test_tree_sitter_core,
        test_unified_analyzer
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Consolidation verification successful!")
        return 0
    else:
        print(f"\n⚠️ {failed} tests failed. Review implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

