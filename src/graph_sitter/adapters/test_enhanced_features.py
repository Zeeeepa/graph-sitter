#!/usr/bin/env python3
"""
Test script to demonstrate enhanced graph-sitter features.

This script shows how to use the enhanced codebase analysis features
with practical examples.
"""

import json
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from enhanced_analyzer import EnhancedCodebaseAnalyzer
    from graph_sitter_enhancements import (
        get_codebase_summary_enhanced,
        detect_import_loops,
        detect_dead_code,
        generate_training_data,
        analyze_graph_structure
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Dependencies not available: {e}")
    print("This is expected if graph-sitter is not installed.")
    DEPENDENCIES_AVAILABLE = False


def demonstrate_enhanced_features():
    """Demonstrate the enhanced graph-sitter features."""
    print("🚀 Graph-Sitter Enhanced Codebase Analysis Demo")
    print("=" * 50)
    
    if not DEPENDENCIES_AVAILABLE:
        print("❌ Graph-sitter dependencies not available")
        print("To use enhanced features, install:")
        print("  pip install graph-sitter networkx")
        return
    
    # Use current directory as test path
    test_path = "."
    
    print(f"📁 Analyzing path: {test_path}")
    print()
    
    # Initialize enhanced analyzer
    print("🔧 Initializing Enhanced Analyzer...")
    analyzer = EnhancedCodebaseAnalyzer(use_advanced_config=True)
    print("✅ Enhanced analyzer initialized with advanced config")
    print()
    
    # Demonstrate different analysis types
    analyses = [
        ("Training Data Generation", "analyze_training_data"),
        ("Import Loop Detection", "analyze_import_loops"),
        ("Dead Code Detection", "analyze_dead_code"),
        ("Graph Structure Analysis", "analyze_graph_structure"),
        ("Enhanced Metrics", "analyze_enhanced_metrics"),
    ]
    
    results = {}
    
    for analysis_name, method_name in analyses:
        print(f"🔍 Running {analysis_name}...")
        try:
            method = getattr(analyzer, method_name)
            result = method(test_path)
            results[analysis_name] = result
            
            # Print summary
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ {analysis_name} completed successfully")
                
                # Print specific summaries
                if "summary" in result:
                    summary = result["summary"]
                    for key, value in summary.items():
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
                elif "metadata" in result:
                    metadata = result["metadata"]
                    for key, value in metadata.items():
                        if isinstance(value, (int, float)):
                            print(f"   • {key.replace('_', ' ').title()}: {value}")
                
        except Exception as e:
            print(f"❌ Error in {analysis_name}: {e}")
            results[analysis_name] = {"error": str(e)}
        
        print()
    
    # Demonstrate comprehensive analysis
    print("🎯 Running Comprehensive Enhanced Analysis...")
    try:
        comprehensive_result = analyzer.analyze_codebase_enhanced(test_path)
        results["Comprehensive Analysis"] = comprehensive_result
        
        if "error" not in comprehensive_result:
            print("✅ Comprehensive analysis completed")
            if "codebase_summary" in comprehensive_result:
                summary = comprehensive_result["codebase_summary"]
                if "basic_metrics" in summary:
                    metrics = summary["basic_metrics"]
                    print("📊 Basic Metrics:")
                    for key, value in metrics.items():
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"❌ Error: {comprehensive_result['error']}")
    except Exception as e:
        print(f"❌ Error in comprehensive analysis: {e}")
        results["Comprehensive Analysis"] = {"error": str(e)}
    
    print()
    
    # Save results
    output_file = "enhanced_analysis_demo_results.json"
    print(f"💾 Saving results to {output_file}...")
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    print()
    print("🎉 Demo completed!")
    print()
    print("📚 To use these features in your own analysis:")
    print("   python analyze_codebase_enhanced.py . --training-data --output training.json")
    print("   python analyze_codebase_enhanced.py . --import-loops --dead-code")
    print("   python analyze_codebase_enhanced.py . --enhanced-metrics --advanced-config")


def demonstrate_direct_api_usage():
    """Demonstrate direct API usage without the analyzer class."""
    print("🔧 Direct API Usage Demo")
    print("=" * 30)
    
    if not DEPENDENCIES_AVAILABLE:
        print("❌ Dependencies not available for direct API demo")
        return
    
    try:
        from graph_sitter import Codebase
        
        print("📁 Loading codebase...")
        codebase = Codebase(".")
        
        print("✅ Codebase loaded successfully")
        print()
        
        # Demonstrate pre-computed graph element access
        print("🔍 Accessing Pre-computed Graph Elements:")
        print(f"   • Functions: {len(list(codebase.functions))}")
        print(f"   • Classes: {len(list(codebase.classes))}")
        print(f"   • Imports: {len(list(codebase.imports))}")
        print(f"   • Files: {len(list(codebase.files))}")
        print(f"   • Symbols: {len(list(codebase.symbols))}")
        print(f"   • External Modules: {len(list(codebase.external_modules))}")
        print()
        
        # Demonstrate function analysis
        print("⚡ Function Analysis Examples:")
        functions = list(codebase.functions)
        if functions:
            func = functions[0]
            print(f"   • Function: {func.name}")
            print(f"   • Usages: {len(getattr(func, 'usages', []))}")
            print(f"   • Dependencies: {len(getattr(func, 'dependencies', []))}")
            print(f"   • Call Sites: {len(getattr(func, 'call_sites', []))}")
            print(f"   • Parameters: {len(getattr(func, 'parameters', []))}")
        else:
            print("   • No functions found in codebase")
        print()
        
        # Demonstrate class analysis
        print("🏗️ Class Analysis Examples:")
        classes = list(codebase.classes)
        if classes:
            cls = classes[0]
            print(f"   • Class: {cls.name}")
            print(f"   • Superclasses: {len(getattr(cls, 'superclasses', []))}")
            print(f"   • Methods: {len(getattr(cls, 'methods', []))}")
            print(f"   • Attributes: {len(getattr(cls, 'attributes', []))}")
            print(f"   • Usages: {len(getattr(cls, 'usages', []))}")
        else:
            print("   • No classes found in codebase")
        print()
        
        # Demonstrate import analysis
        print("📦 Import Analysis Examples:")
        files = list(codebase.files)
        if files:
            file = files[0]
            print(f"   • File: {file.name}")
            print(f"   • Imports: {len(getattr(file, 'imports', []))}")
            print(f"   • Symbols: {len(getattr(file, 'symbols', []))}")
        else:
            print("   • No files found in codebase")
        
    except Exception as e:
        print(f"❌ Error in direct API demo: {e}")
    
    print()


if __name__ == "__main__":
    print("🚀 Graph-Sitter Enhanced Features Test")
    print("=" * 60)
    print()
    
    # Run demonstrations
    demonstrate_enhanced_features()
    print()
    demonstrate_direct_api_usage()
    
    print("✨ Test completed!")
    print()
    print("📖 For more information, see:")
    print("   • README_ENHANCED.md")
    print("   • analyze_codebase_enhanced.py --help")

