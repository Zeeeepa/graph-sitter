#!/usr/bin/env python3
"""
Comprehensive Analysis Example

This example demonstrates all the graph-sitter.com capabilities integrated
into a unified analysis system, including metrics, call graphs, dependencies,
dead code detection, and AI-powered insights.
"""

import asyncio
import json
from pathlib import Path

from graph_sitter import Codebase
from graph_sitter.analysis.enhanced_analysis import (
    EnhancedCodebaseAnalyzer,
    run_full_analysis,
    get_function_context_analysis,
    get_codebase_health_score,
    query_analysis_data,
    generate_analysis_report
)
from graph_sitter.analysis.metrics import (
    MetricsCalculator,
    calculate_cyclomatic_complexity,
    calculate_maintainability_index,
    analyze_function_metrics,
    analyze_class_metrics,
    get_codebase_summary
)
from graph_sitter.analysis.call_graph import (
    CallGraphAnalyzer,
    build_call_graph,
    traverse_call_graph
)
from graph_sitter.analysis.dependency_analyzer import (
    DependencyAnalyzer,
    hop_through_imports,
    find_dependency_paths,
    analyze_symbol_dependencies,
    find_circular_dependencies,
    analyze_imports
)
from graph_sitter.analysis.dead_code import (
    DeadCodeDetector,
    find_dead_code,
    find_unused_imports,
    estimate_cleanup_impact,
    get_removal_plan
)


async def main():
    """Demonstrate comprehensive analysis capabilities."""
    
    print("🔍 Comprehensive Codebase Analysis Example")
    print("=" * 60)
    
    # Initialize codebase
    print("\n1. Initializing Codebase...")
    codebase = Codebase(".")
    
    print(f"✅ Loaded codebase with:")
    print(f"   📁 {len(list(codebase.files))} files")
    print(f"   🔧 {len(list(codebase.functions))} functions")
    print(f"   📦 {len(list(codebase.classes))} classes")
    print(f"   📥 {len(list(codebase.imports))} imports")
    print(f"   🔗 {len(list(codebase.symbols))} symbols")
    
    # Enhanced Analysis
    print("\n2. Running Enhanced Analysis...")
    analyzer = EnhancedCodebaseAnalyzer(codebase, "example-codebase")
    
    # Full analysis
    print("   🔄 Running full analysis...")
    full_report = analyzer.run_full_analysis()
    
    print(f"   ✅ Analysis complete!")
    print(f"   📊 Health Score: {full_report.health_score:.2f}")
    print(f"   🚨 Issues Found: {len(full_report.issues)}")
    print(f"   💡 Recommendations: {len(full_report.recommendations)}")
    
    # Metrics Analysis
    print("\n3. Detailed Metrics Analysis...")
    metrics_calc = MetricsCalculator(codebase)
    codebase_metrics = metrics_calc.get_codebase_summary()
    
    print(f"   📈 Codebase Metrics:")
    print(f"   ├── Average Complexity: {codebase_metrics.average_complexity:.1f}")
    print(f"   ├── Maintainability: {codebase_metrics.average_maintainability:.1f}")
    print(f"   ├── Documentation: {codebase_metrics.documentation_coverage:.1%}")
    print(f"   ├── Test Coverage: {codebase_metrics.test_coverage_estimate:.1%}")
    print(f"   ├── Dead Code: {codebase_metrics.dead_code_percentage:.1%}")
    print(f"   └── Technical Debt: {codebase_metrics.technical_debt_score:.2f}")
    
    # Function Analysis
    print("\n   🔧 Function Analysis:")
    functions = list(codebase.functions)[:5]  # Analyze first 5 functions
    
    for func in functions:
        try:
            func_metrics = analyze_function_metrics(func)
            complexity = calculate_cyclomatic_complexity(func)
            maintainability = calculate_maintainability_index(func)
            
            print(f"   ├── {func.name}:")
            print(f"   │   ├── Complexity: {complexity}")
            print(f"   │   ├── Maintainability: {maintainability:.1f}")
            print(f"   │   ├── Parameters: {func_metrics.parameter_count}")
            print(f"   │   ├── Lines: {func_metrics.line_count}")
            print(f"   │   └── Impact Score: {func_metrics.impact_score:.1f}")
        except Exception as e:
            print(f"   │   └── Error analyzing {func.name}: {e}")
    
    # Class Analysis
    print("\n   📦 Class Analysis:")
    classes = list(codebase.classes)[:3]  # Analyze first 3 classes
    
    for cls in classes:
        try:
            class_metrics = analyze_class_metrics(cls)
            
            print(f"   ├── {cls.name}:")
            print(f"   │   ├── Methods: {class_metrics.method_count}")
            print(f"   │   ├── Attributes: {class_metrics.attribute_count}")
            print(f"   │   ├── Inheritance Depth: {class_metrics.inheritance_depth}")
            print(f"   │   ├── Cohesion: {class_metrics.cohesion_score:.2f}")
            print(f"   │   └── Coupling: {class_metrics.coupling_score:.2f}")
        except Exception as e:
            print(f"   │   └── Error analyzing {cls.name}: {e}")
    
    # Call Graph Analysis
    print("\n4. Call Graph Analysis...")
    call_graph = CallGraphAnalyzer(codebase)
    
    # Find interesting patterns
    most_called = call_graph.find_most_called_function()
    most_calling = call_graph.find_most_calling_function()
    unused_functions = call_graph.find_unused_functions()
    recursive_functions = call_graph.find_recursive_functions()
    
    print(f"   📞 Call Graph Patterns:")
    print(f"   ├── Most Called: {most_called.name if most_called else 'None'}")
    print(f"   ├── Most Calling: {most_calling.name if most_calling else 'None'}")
    print(f"   ├── Unused Functions: {len(unused_functions)}")
    print(f"   └── Recursive Functions: {len(recursive_functions)}")
    
    if recursive_functions:
        print(f"   🔄 Recursive Functions:")
        for func in recursive_functions[:3]:
            print(f"   ├── {func.name}")
    
    # Call patterns
    patterns = call_graph.analyze_call_patterns()
    print(f"\n   📊 Call Patterns:")
    print(f"   �����── Total Functions: {patterns.get('total_functions', 0)}")
    print(f"   ├── Total Calls: {patterns.get('total_calls', 0)}")
    print(f"   ├── Average Calls/Function: {patterns.get('average_calls_per_function', 0):.1f}")
    print(f"   ├── Max Call Depth: {patterns.get('max_call_depth', 0)}")
    print(f"   ├── Entry Points: {patterns.get('entry_points', 0)}")
    print(f"   └── Hub Functions: {patterns.get('hub_functions', 0)}")
    
    # Call chains analysis
    call_chains = call_graph.analyze_call_chains()
    if call_chains.get('total_chains', 0) > 0:
        print(f"\n   ⛓️  Method Chaining:")
        print(f"   ├── Total Chains: {call_chains['total_chains']}")
        print(f"   ├── Average Length: {call_chains['average_chain_length']:.1f}")
        longest = call_chains.get('longest_chain')
        if longest:
            print(f"   └── Longest Chain: {longest['chain_length']} calls in {longest['function']}")
    
    # Dependency Analysis
    print("\n5. Dependency Analysis...")
    dep_analyzer = DependencyAnalyzer(codebase)
    
    # Import analysis
    import_analysis = analyze_imports(codebase)
    print(f"   📥 Import Analysis:")
    print(f"   ├── Total Imports: {import_analysis.total_imports}")
    print(f"   ├── External: {import_analysis.external_imports}")
    print(f"   ├── Internal: {import_analysis.internal_imports}")
    print(f"   ├── Unused: {import_analysis.unused_imports}")
    print(f"   ├── Circular: {import_analysis.circular_imports}")
    print(f"   ├── Average Depth: {import_analysis.import_depth_avg:.1f}")
    print(f"   └── Complexity Score: {import_analysis.import_complexity_score:.2f}")
    
    # Most imported modules
    if import_analysis.most_imported_modules:
        print(f"\n   📊 Most Imported Modules:")
        for module, count in import_analysis.most_imported_modules[:5]:
            print(f"   ├── {module}: {count} imports")
    
    # Circular dependencies
    circular_deps = find_circular_dependencies(codebase)
    if circular_deps:
        print(f"\n   🔄 Circular Dependencies Found: {len(circular_deps)}")
        for i, cd in enumerate(circular_deps[:3]):
            print(f"   ├── Cycle {i+1}: {len(cd.symbols)} symbols ({cd.severity} severity)")
            print(f"   │   └── {' → '.join([s.name for s in cd.symbols[:3]])}...")
    
    # Symbol dependency analysis
    if codebase.symbols:
        sample_symbol = list(codebase.symbols)[0]
        dep_context = analyze_symbol_dependencies(sample_symbol)
        if dep_context:
            print(f"\n   🔗 Sample Symbol Dependencies ({sample_symbol.name}):")
            print(f"   ├── Direct Dependencies: {dep_context.get('direct_dependencies', 0)}")
            print(f"   ├── Transitive Dependencies: {dep_context.get('transitive_dependencies', 0)}")
            print(f"   ├── Reverse Dependencies: {dep_context.get('reverse_dependencies', 0)}")
            print(f"   └── Dependency Depth: {dep_context.get('dependency_depth', 0)}")
    
    # Import hopping example
    if codebase.imports:
        sample_import = list(codebase.imports)[0]
        resolved = hop_through_imports(sample_import)
        print(f"\n   🔍 Import Resolution Example:")
        print(f"   ├── Original: {type(sample_import).__name__}")
        print(f"   └── Resolved: {type(resolved).__name__}")
    
    # Dead Code Analysis
    print("\n6. Dead Code Analysis...")
    dead_code_detector = DeadCodeDetector(codebase)
    
    # Find dead code
    dead_code_items = find_dead_code(codebase)
    print(f"   🗑️  Dead Code Detection:")
    print(f"   ├── Total Items: {len(dead_code_items)}")
    
    # Categorize by type
    by_type = {}
    for item in dead_code_items:
        by_type[item.type] = by_type.get(item.type, 0) + 1
    
    for code_type, count in by_type.items():
        print(f"   ├── {code_type.title()}: {count}")
    
    # Show sample dead code items
    if dead_code_items:
        print(f"\n   📋 Sample Dead Code Items:")
        for item in dead_code_items[:5]:
            print(f"   ├── {item.symbol.name} ({item.type})")
            print(f"   │   ├── Reason: {item.reason}")
            print(f"   │   ├── Confidence: {item.confidence:.1%}")
            print(f"   │   └── Safe to Remove: {item.safe_to_remove}")
    
    # Cleanup impact
    if dead_code_items:
        cleanup_impact = estimate_cleanup_impact(codebase, dead_code_items)
        print(f"\n   📊 Cleanup Impact:")
        print(f"   ├── Estimated Lines Saved: {cleanup_impact.get('estimated_lines_saved', 0)}")
        print(f"   ├── Files Affected: {cleanup_impact.get('files_affected', 0)}")
        print(f"   ├── Risk Level: {cleanup_impact.get('risk_level', 'unknown')}")
        
        # Removal plan
        removal_plan = get_removal_plan(codebase, dead_code_items)
        print(f"   └── Removal Plan: {len(removal_plan.items)} safe items")
        
        if removal_plan.warnings:
            print(f"   ⚠️  Warnings:")
            for warning in removal_plan.warnings[:3]:
                print(f"   ├── {warning}")
    
    # Function Context Analysis
    print("\n7. Function Context Analysis...")
    
    if codebase.functions:
        sample_function = list(codebase.functions)[0]
        context = get_function_context_analysis(codebase, sample_function.name)
        
        if 'error' not in context:
            print(f"   🔧 Function: {sample_function.name}")
            
            metrics = context.get('metrics', {})
            print(f"   ├── Complexity: {metrics.get('cyclomatic_complexity', 0)}")
            print(f"   ├── Maintainability: {metrics.get('maintainability_index', 0):.1f}")
            print(f"   ├── Documentation: {metrics.get('documentation_coverage', 0):.1%}")
            print(f"   ├── Impact Score: {metrics.get('impact_score', 0):.1f}")
            
            call_graph_info = context.get('call_graph', {})
            print(f"   ├── Call Depth: {call_graph_info.get('depth', 0)}")
            print(f"   ├── Incoming Calls: {call_graph_info.get('incoming_calls', 0)}")
            print(f"   ├── Outgoing Calls: {call_graph_info.get('outgoing_calls', 0)}")
            
            dependencies = context.get('dependencies', {})
            print(f"   ├── Dependencies: {dependencies.get('direct_dependencies', 0)}")
            print(f"   ├── Reverse Deps: {dependencies.get('reverse_dependencies', 0)}")
            print(f"   └── Dead Code: {context.get('is_dead_code', False)}")
    
    # Health Score Analysis
    print("\n8. Codebase Health Assessment...")
    health_assessment = get_codebase_health_score(codebase)
    
    if 'error' not in health_assessment:
        overall_score = health_assessment.get('overall_health_score', 0)
        grade = health_assessment.get('grade', 'F')
        
        print(f"   🏥 Health Assessment:")
        print(f"   ├── Overall Score: {overall_score:.2f} (Grade: {grade})")
        
        component_scores = health_assessment.get('component_scores', {})
        print(f"   ├── Component Scores:")
        for component, score in component_scores.items():
            print(f"   │   ├── {component.title()}: {score:.2f}")
        
        recommendations = health_assessment.get('recommendations', [])
        if recommendations:
            print(f"   └── Health Recommendations:")
            for rec in recommendations:
                print(f"       ├── {rec}")
    
    # AI-Powered Analysis (if available)
    print("\n9. AI-Powered Analysis...")
    
    try:
        # Example queries
        queries = [
            "What are the main quality issues in this codebase?",
            "Which functions have the highest complexity?",
            "What improvements would have the biggest impact?"
        ]
        
        for query in queries:
            print(f"   🤖 Query: {query}")
            try:
                result = await query_analysis_data(codebase, query)
                if 'error' not in result:
                    analysis = result.get('analysis', 'No analysis available')
                    print(f"   ├── Analysis: {analysis[:200]}...")
                else:
                    print(f"   ├── {result['error']}")
            except Exception as e:
                print(f"   ├── Error: {e}")
            print()
    except Exception as e:
        print(f"   ⚠️  AI analysis not available: {e}")
    
    # Report Generation
    print("\n10. Report Generation...")
    
    # Generate JSON report
    json_report = generate_analysis_report(codebase, 'json')
    json_file = Path("comprehensive_analysis_report.json")
    with open(json_file, 'w') as f:
        f.write(json_report)
    
    print(f"   ✅ JSON Report: {json_file}")
    print(f"   📊 Size: {len(json_report)} characters")
    
    # Generate Markdown report
    try:
        md_report = generate_analysis_report(codebase, 'markdown')
        md_file = Path("comprehensive_analysis_report.md")
        with open(md_file, 'w') as f:
            f.write(md_report)
        
        print(f"   ✅ Markdown Report: {md_file}")
        print(f"   📄 Size: {len(md_report)} characters")
    except Exception as e:
        print(f"   ⚠️  Markdown report error: {e}")
    
    # Summary Statistics
    print("\n11. Summary Statistics...")
    print("-" * 50)
    
    print(f"📊 Analysis Summary:")
    print(f"├── Health Score: {full_report.health_score:.2f} ({analyzer._score_to_grade(full_report.health_score)})")
    print(f"├── Total Issues: {len(full_report.issues)}")
    print(f"├── Recommendations: {len(full_report.recommendations)}")
    print(f"├��─ Dead Code Items: {len(dead_code_items)}")
    print(f"├── Circular Dependencies: {len(circular_deps)}")
    print(f"├── Unused Functions: {len(unused_functions)}")
    print(f"└── Recursive Functions: {len(recursive_functions)}")
    
    print(f"\n📈 Key Metrics:")
    print(f"├── Average Complexity: {codebase_metrics.average_complexity:.1f}")
    print(f"├── Maintainability: {codebase_metrics.average_maintainability:.1f}")
    print(f"├── Documentation: {codebase_metrics.documentation_coverage:.1%}")
    print(f"├── Test Coverage: {codebase_metrics.test_coverage_estimate:.1%}")
    print(f"└── Technical Debt: {codebase_metrics.technical_debt_score:.2f}")
    
    # Top Issues
    if full_report.issues:
        print(f"\n🚨 Top Issues:")
        for i, issue in enumerate(full_report.issues[:5]):
            print(f"{i+1}. {issue['description']} ({issue['severity']})")
    
    # Top Recommendations
    if full_report.recommendations:
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(full_report.recommendations[:5]):
            print(f"{i+1}. {rec}")
    
    print("\n🎉 Comprehensive Analysis Complete!")
    print("\nFiles generated:")
    print(f"├── {json_file} - Detailed JSON report")
    if 'md_file' in locals():
        print(f"└── {md_file} - Human-readable markdown report")
    
    print("\nUse these reports to:")
    print("├── Track code quality metrics over time")
    print("├── Identify areas for improvement")
    print("├── Plan refactoring efforts")
    print("├── Monitor technical debt")
    print("└── Make data-driven development decisions")


def demonstrate_specific_capabilities():
    """Demonstrate specific graph-sitter.com capabilities."""
    print("\n" + "="*60)
    print("🔧 Specific Capabilities Demonstration")
    print("="*60)
    
    codebase = Codebase(".")
    
    # Print overall stats (from graph-sitter.com examples)
    print("🔍 Codebase Analysis")
    print("=" * 50)
    print(f"📚 Total Classes: {len(list(codebase.classes))}")
    print(f"⚡ Total Functions: {len(list(codebase.functions))}")
    print(f"🔄 Total Imports: {len(list(codebase.imports))}")
    
    # Find class with most inheritance
    if codebase.classes:
        try:
            deepest_class = max(codebase.classes, key=lambda x: len(getattr(x, 'superclasses', [])))
            superclasses = getattr(deepest_class, 'superclasses', [])
            print(f"\n🌳 Class with most inheritance: {deepest_class.name}")
            print(f"   📊 Chain Depth: {len(superclasses)}")
            if superclasses:
                print(f"   ⛓️ Chain: {' -> '.join(s.name for s in superclasses)}")
        except Exception as e:
            print(f"   ⚠️ Error analyzing inheritance: {e}")
    
    # Find recursive functions
    try:
        recursive = []
        for f in list(codebase.functions)[:20]:  # Limit for performance
            try:
                function_calls = getattr(f, 'function_calls', [])
                if any(getattr(call, 'name', '') == f.name for call in function_calls):
                    recursive.append(f)
            except Exception:
                continue
        
        if recursive:
            print(f"\n🔄 Recursive functions:")
            for func in recursive[:5]:
                print(f"  - {func.name}")
    except Exception as e:
        print(f"   ⚠️ Error finding recursive functions: {e}")
    
    # Test analysis
    try:
        test_functions = [x for x in codebase.functions if x.name.startswith('test_')]
        test_classes = [x for x in codebase.classes if x.name.startswith('Test')]
        
        print("\n🧪 Test Analysis")
        print("=" * 50)
        print(f"📝 Total Test Functions: {len(test_functions)}")
        print(f"🔬 Total Test Classes: {len(test_classes)}")
        
        total_files = len(list(codebase.files))
        if total_files > 0:
            print(f"📊 Tests per File: {len(test_functions) / total_files:.1f}")
    except Exception as e:
        print(f"   ⚠️ Error analyzing tests: {e}")
    
    # Dead code analysis
    try:
        unused_functions = []
        for func in list(codebase.functions)[:20]:  # Limit for performance
            try:
                usages = getattr(func, 'usages', [])
                call_sites = getattr(func, 'call_sites', [])
                if not usages and not call_sites:
                    unused_functions.append(func)
            except Exception:
                continue
        
        if unused_functions:
            print(f"\n🗑️ Potential Dead Code:")
            for func in unused_functions[:5]:
                print(f"  - {func.name}")
    except Exception as e:
        print(f"   ⚠️ Error finding dead code: {e}")
    
    # Import analysis
    try:
        print(f"\n📥 Import Analysis:")
        external_modules = list(codebase.external_modules)
        print(f"  - External Modules: {len(external_modules)}")
        
        if external_modules:
            print(f"  - Sample External Modules:")
            for module in external_modules[:5]:
                print(f"    - {getattr(module, 'name', str(module))}")
    except Exception as e:
        print(f"   ⚠️ Error analyzing imports: {e}")


if __name__ == "__main__":
    # Run main comprehensive analysis
    asyncio.run(main())
    
    # Demonstrate specific capabilities
    demonstrate_specific_capabilities()
