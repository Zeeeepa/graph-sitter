#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Example

This example demonstrates how to use the enhanced graph-sitter adapters
for comprehensive codebase analysis, including:

1. Function context analysis with issue detection
2. Interactive visualization and reporting
3. Training data generation for ML applications
4. Comprehensive analysis with all components integrated

Based on the patterns from: https://gist.github.com/Zeeeepa/3c2bf1e28c4503fd7ad81a2800668be3
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.unified_analyzer import (
    UnifiedCodebaseAnalyzer,
    analyze_codebase_comprehensive,
    quick_function_analysis
)
from graph_sitter.adapters.function_context import (
    get_function_context,
    get_enhanced_function_context,
    analyze_codebase_functions,
    create_training_example
)
from graph_sitter.adapters.codebase_visualization import (
    create_comprehensive_visualization,
    analyze_function_with_context
)


def demonstrate_function_context_analysis(codebase: Codebase):
    """Demonstrate function context analysis as shown in the gist."""
    print("\n" + "="*60)
    print("🔍 FUNCTION CONTEXT ANALYSIS")
    print("="*60)
    
    # Get first few functions for demonstration
    functions = list(codebase.functions)[:5]
    
    for function in functions:
        print(f"\n📋 Analyzing function: {function.name}")
        print("-" * 40)
        
        # Get basic function context (as shown in gist)
        context = get_function_context(function)
        
        print(f"📁 File: {context['implementation']['filepath']}")
        print(f"📏 Lines: {context['metrics'].get('line_count', 'N/A')}")
        print(f"🔗 Dependencies: {len(context['dependencies'])}")
        print(f"📞 Usages: {len(context['usages'])}")
        print(f"🎯 Call Sites: {len(context['call_sites'])}")
        print(f"🧮 Complexity: {context['metrics'].get('complexity_estimate', 'N/A')}")
        
        # Show dependencies
        if context['dependencies']:
            print("\n🔗 Dependencies:")
            for dep in context['dependencies'][:3]:  # Show first 3
                print(f"  - {dep.get('name', 'Unknown')} ({dep.get('filepath', 'N/A')})")
        
        # Show usages
        if context['usages']:
            print("\n📞 Usages:")
            for usage in context['usages'][:3]:  # Show first 3
                print(f"  - {usage.get('filepath', 'N/A')}")


def demonstrate_enhanced_function_analysis(codebase: Codebase):
    """Demonstrate enhanced function analysis with issue detection."""
    print("\n" + "="*60)
    print("🚨 ENHANCED FUNCTION ANALYSIS WITH ISSUE DETECTION")
    print("="*60)
    
    functions = list(codebase.functions)[:3]
    
    for function in functions:
        print(f"\n🔍 Enhanced analysis for: {function.name}")
        print("-" * 40)
        
        # Get enhanced context with issue detection
        enhanced_context = get_enhanced_function_context(function)
        
        print(f"📁 File: {enhanced_context.filepath}")
        print(f"⚡ Impact Score: {enhanced_context.impact_score:.2f}")
        print(f"⚠️ Risk Level: {enhanced_context.risk_level}")
        print(f"🐛 Issues Found: {len(enhanced_context.issues)}")
        
        # Show issues
        if enhanced_context.issues:
            print("\n🐛 Issues:")
            for issue in enhanced_context.issues:
                severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue['severity'], "⚪")
                print(f"  {severity_emoji} {issue['type']}: {issue['message']}")
                if issue.get('recommendation'):
                    print(f"    💡 Recommendation: {issue['recommendation']}")
        
        # Show recommendations
        if enhanced_context.recommendations:
            print("\n💡 Recommendations:")
            for rec in enhanced_context.recommendations[:3]:
                print(f"  - {rec}")


def demonstrate_training_data_generation(codebase: Codebase):
    """Demonstrate training data generation for ML applications."""
    print("\n" + "="*60)
    print("🤖 TRAINING DATA GENERATION FOR ML")
    print("="*60)
    
    # Generate training data as shown in the gist
    print("📊 Generating training data...")
    summary = analyze_codebase_functions(codebase, "training_data_example.json")
    
    print(f"✅ Training data generated!")
    print(f"📈 Statistics:")
    print(f"  - Total functions: {summary['total_functions']}")
    print(f"  - Processed functions: {summary['processed_functions']}")
    print(f"  - Files analyzed: {summary['files_analyzed']}")
    print(f"  - Average dependencies: {summary['avg_dependencies']:.1f}")
    print(f"  - Average usages: {summary['avg_usages']:.1f}")
    print(f"  - Average complexity: {summary['avg_complexity']:.1f}")
    print(f"  - Training examples: {summary['training_examples']}")
    print(f"  - Output file: {summary['output_file']}")
    
    # Load and show example training data
    try:
        with open("training_data_example.json", "r") as f:
            training_data = json.load(f)
        
        if training_data['training_examples']:
            example = training_data['training_examples'][0]
            print(f"\n📝 Example training data structure:")
            print(f"  - Context dependencies: {len(example['context']['dependencies'])}")
            print(f"  - Context usages: {len(example['context']['usages'])}")
            print(f"  - Target function: {example['target']['name']}")
            print(f"  - Target file: {example['target']['filepath']}")
    except Exception as e:
        print(f"⚠️ Could not load training data example: {e}")


def demonstrate_comprehensive_analysis(codebase: Codebase):
    """Demonstrate comprehensive analysis with all components."""
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE CODEBASE ANALYSIS")
    print("="*60)
    
    print("🚀 Running comprehensive analysis with all components...")
    
    # Run comprehensive analysis
    results = analyze_codebase_comprehensive(
        codebase, 
        codebase_id="demo_analysis",
        output_dir="demo_comprehensive_analysis"
    )
    
    print("✅ Comprehensive analysis completed!")
    print(f"\n📊 Results Summary:")
    print(f"  - Codebase ID: {results.codebase_id}")
    print(f"  - Health Score: {results.health_score:.2f}/1.0")
    print(f"  - Functions Analyzed: {len(results.function_contexts)}")
    print(f"  - Total Issues: {sum(len(fc.issues) for fc in results.function_contexts)}")
    print(f"  - Risk Level: {results.risk_assessment['level'].title()}")
    print(f"  - Recommendations: {len(results.actionable_recommendations)}")
    
    # Show risk distribution
    print(f"\n⚠️ Risk Distribution:")
    for level, count in results.risk_assessment['distribution'].items():
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟠", "minimal": "🟢"}.get(level, "⚪")
        print(f"  {emoji} {level.title()}: {count} functions")
    
    # Show top recommendations
    print(f"\n💡 Top Recommendations:")
    for i, rec in enumerate(results.actionable_recommendations[:5], 1):
        print(f"  {i}. {rec}")
    
    # Show export files
    print(f"\n📁 Generated Files:")
    for name, path in results.export_paths.items():
        print(f"  - {name.replace('_', ' ').title()}: {path}")
    
    return results


def demonstrate_interactive_visualization(codebase: Codebase):
    """Demonstrate interactive visualization creation."""
    print("\n" + "="*60)
    print("📊 INTERACTIVE VISUALIZATION & REPORTING")
    print("="*60)
    
    print("🎨 Creating interactive visualizations...")
    
    # Create comprehensive visualization
    interactive_report = create_comprehensive_visualization(
        codebase, 
        output_dir="demo_visualizations"
    )
    
    print("✅ Interactive visualizations created!")
    print(f"\n📈 Visualization Summary:")
    print(f"  - Functions analyzed: {len(interactive_report.function_analysis)}")
    print(f"  - Dependency graph nodes: {interactive_report.dependency_graph.metadata['total_nodes']}")
    print(f"  - Dependency graph edges: {interactive_report.dependency_graph.metadata['total_edges']}")
    print(f"  - Call graph nodes: {interactive_report.call_graph.metadata['total_nodes']}")
    print(f"  - Call graph edges: {interactive_report.call_graph.metadata['total_edges']}")
    print(f"  - Issues found: {interactive_report.issue_dashboard['summary']['total_issues']}")
    
    # Show complexity metrics
    complexity_metrics = interactive_report.complexity_heatmap['metrics']
    print(f"\n🔥 Complexity Metrics:")
    print(f"  - Average complexity: {complexity_metrics['avg_complexity']:.1f}")
    print(f"  - Max complexity: {complexity_metrics['max_complexity']}")
    print(f"  - High complexity functions: {complexity_metrics['high_complexity_functions']}")
    
    print(f"\n📁 Interactive report saved to: demo_visualizations/interactive_report.html")
    print(f"🌐 Open the HTML file in a browser to explore the interactive dashboard!")


def demonstrate_specific_function_analysis(codebase: Codebase):
    """Demonstrate analysis of specific functions when they have issues."""
    print("\n" + "="*60)
    print("🔍 SPECIFIC FUNCTION ANALYSIS FOR ISSUES")
    print("="*60)
    
    # Find functions with issues
    functions_with_issues = []
    for function in list(codebase.functions)[:10]:  # Check first 10 functions
        try:
            context = get_enhanced_function_context(function)
            if context.issues:
                functions_with_issues.append((function, context))
        except Exception:
            continue
    
    if not functions_with_issues:
        print("🎉 No functions with issues found in the sample!")
        return
    
    print(f"🐛 Found {len(functions_with_issues)} functions with issues:")
    
    for function, context in functions_with_issues[:3]:  # Show first 3
        print(f"\n🔍 Function: {function.name}")
        print(f"📁 File: {context.filepath}")
        print(f"⚠️ Risk Level: {context.risk_level}")
        print(f"🐛 Issues ({len(context.issues)}):")
        
        for issue in context.issues:
            severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue['severity'], "⚪")
            print(f"  {severity_emoji} {issue['type']}: {issue['message']}")
        
        print(f"💡 Recommendations:")
        for rec in context.recommendations[:2]:
            print(f"  - {rec}")
        
        # Show function context for debugging
        basic_context = get_function_context(function)
        print(f"🔧 Context for debugging:")
        print(f"  - Dependencies: {len(basic_context['dependencies'])}")
        print(f"  - Usages: {len(basic_context['usages'])}")
        print(f"  - Complexity: {basic_context['metrics'].get('complexity_estimate', 'N/A')}")


def main():
    """Main demonstration function."""
    print("🚀 COMPREHENSIVE CODEBASE ANALYSIS DEMONSTRATION")
    print("=" * 80)
    print("This example demonstrates the enhanced graph-sitter adapters")
    print("for comprehensive codebase analysis and visualization.")
    print("=" * 80)
    
    # Initialize codebase (you can change this to analyze any repository)
    print("\n📂 Initializing codebase...")
    try:
        # Try to analyze the current project
        codebase = Codebase.from_directory(".")
        print(f"✅ Loaded codebase with {len(codebase.files)} files")
        print(f"   - Functions: {len(codebase.functions)}")
        print(f"   - Classes: {len(codebase.classes)}")
        print(f"   - Imports: {len(codebase.imports)}")
    except Exception as e:
        print(f"❌ Error loading codebase: {e}")
        print("💡 Make sure you're running this from a Python project directory")
        return
    
    # Run all demonstrations
    try:
        # 1. Basic function context analysis (from gist)
        demonstrate_function_context_analysis(codebase)
        
        # 2. Enhanced function analysis with issue detection
        demonstrate_enhanced_function_analysis(codebase)
        
        # 3. Training data generation for ML
        demonstrate_training_data_generation(codebase)
        
        # 4. Specific function analysis for issues
        demonstrate_specific_function_analysis(codebase)
        
        # 5. Interactive visualization
        demonstrate_interactive_visualization(codebase)
        
        # 6. Comprehensive analysis (combines everything)
        comprehensive_results = demonstrate_comprehensive_analysis(codebase)
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("📁 Generated files:")
        print("  - training_data_example.json - ML training data")
        print("  - demo_visualizations/ - Interactive visualizations")
        print("  - demo_comprehensive_analysis/ - Complete analysis results")
        print("\n🌐 Open demo_visualizations/interactive_report.html in your browser")
        print("   to explore the interactive codebase analysis dashboard!")
        print("\n💡 You can now use these patterns to analyze any codebase with")
        print("   comprehensive understanding, issue detection, and visualization.")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

