"""
Comprehensive Codebase Analysis Example

This example demonstrates the enhanced analysis capabilities following
graph-sitter.com patterns, including all the functions identified from
the documentation analysis.
"""

import graph_sitter
from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalysis


@graph_sitter.function("comprehensive-codebase-analysis")
def analyze_codebase_comprehensively(codebase: Codebase):
    """
    Perform comprehensive codebase analysis using all enhanced capabilities.
    
    This function demonstrates:
    - Function context analysis (dependencies, usages, implementation)
    - Import resolution and hop-through-imports functionality
    - Codebase statistics (classes, functions, imports)
    - Inheritance analysis
    - Test analysis
    - Dead code detection
    - Call site analysis
    - Recursive function detection
    - Database storage for analysis results
    """
    
    print("🚀 Starting Comprehensive Codebase Analysis")
    print("=" * 60)
    
    # Initialize enhanced analysis with database storage
    analysis = EnhancedCodebaseAnalysis(codebase, db_path="analysis_results.db")
    
    try:
        # 1. Run full comprehensive analysis
        print("\\n📊 Running Full Analysis...")
        results = analysis.run_full_analysis(store_in_db=True)
        
        # 2. Display codebase summary
        print("\\n📈 Codebase Summary:")
        summary = results['codebase_summary']
        print(f"  • Files: {summary['total_files']}")
        print(f"  • Functions: {summary['total_functions']}")
        print(f"  • Classes: {summary['total_classes']}")
        print(f"  • Average Function Complexity: {summary.get('average_function_complexity', 'N/A'):.2f}")
        print(f"  • Dead Functions: {summary.get('dead_functions_count', 0)}")
        print(f"  • Recursive Functions: {summary.get('recursive_functions_count', 0)}")
        
        # 3. Call Graph Analysis
        print("\\n📞 Call Graph Analysis:")
        call_metrics = results['call_graph_metrics']
        print(f"  • Total Function Calls: {call_metrics['total_calls']}")
        print(f"  • Max Call Depth: {call_metrics['max_call_depth']}")
        print(f"  • Most Called Function: {call_metrics['most_called_function']}")
        print(f"  • Most Calling Function: {call_metrics['most_calling_function']}")
        print(f"  • Entry Points: {len(call_metrics['entry_point_functions'])}")
        print(f"  • Dead End Functions: {len(call_metrics['dead_end_functions'])}")
        
        # 4. Dead Code Detection Results
        print("\\n💀 Dead Code Analysis:")
        dead_code = results['dead_code_report']
        print(f"  • Dead Functions: {len(dead_code['dead_functions'])}")
        print(f"  • Dead Classes: {len(dead_code['dead_classes'])}")
        print(f"  • Unused Imports: {len(dead_code['unused_imports'])}")
        print(f"  • Potential LOC Savings: {dead_code['total_potential_loc_savings']}")
        
        # 5. Dependency Analysis
        print("\\n🔗 Dependency Analysis:")
        dep_metrics = results['dependency_metrics']
        print(f"  • Total Dependencies: {dep_metrics['total_dependencies']}")
        print(f"  • Import Dependencies: {dep_metrics['import_dependencies']}")
        print(f"  • Call Dependencies: {dep_metrics['call_dependencies']}")
        print(f"  • Inheritance Dependencies: {dep_metrics['inheritance_dependencies']}")
        print(f"  • Circular Dependencies: {dep_metrics['circular_dependencies']}")
        print(f"  • Most Depended Upon: {dep_metrics['most_depended_upon']}")
        
        # 6. Import Analysis
        print("\\n📦 Import Analysis:")
        import_analysis = results['import_analysis']
        print(f"  • Total Imports: {import_analysis['total_imports']}")
        print(f"  • External Imports: {import_analysis['external_imports']}")
        print(f"  • Internal Imports: {import_analysis['internal_imports']}")
        print(f"  • Relative Imports: {import_analysis['relative_imports']}")
        print(f"  • External Dependency Ratio: {import_analysis['external_dependency_ratio']:.2f}")
        
        # 7. Circular Dependencies
        circular_deps = results['circular_dependencies']
        if circular_deps:
            print("\\n🔄 Circular Dependencies Found:")
            for i, dep in enumerate(circular_deps[:5], 1):  # Show top 5
                print(f"  {i}. {dep['cycle_description']} (Severity: {dep['severity']})")
        else:
            print("\\n✅ No Circular Dependencies Found!")
        
        # 8. Function Context Analysis Examples
        print("\\n🔧 Function Context Analysis Examples:")
        
        # Analyze a few functions in detail
        functions_to_analyze = list(codebase.functions)[:3]  # Analyze first 3 functions
        
        for func in functions_to_analyze:
            print(f"\\n  📋 Function: {func.qualified_name}")
            context = analysis.get_function_context_analysis(func.qualified_name)
            
            if context:
                metrics = context['metrics']
                print(f"    • Complexity: {metrics['cyclomatic_complexity']}")
                print(f"    • Lines of Code: {metrics['lines_of_code']}")
                print(f"    • Parameters: {metrics['parameters_count']}")
                print(f"    • Is Recursive: {metrics['is_recursive']}")
                print(f"    • Is Async: {metrics['is_async']}")
                
                call_context = context['call_context']
                print(f"    • Incoming Calls: {call_context['incoming_calls']}")
                print(f"    • Outgoing Calls: {call_context['outgoing_calls']}")
                
                dependencies = context['dependencies']
                print(f"    • Direct Dependencies: {dependencies.get('dependency_count', 0)}")
                print(f"    • Impact Score: {dependencies.get('impact_score', 0)}")
                
                recommendations = context['recommendations']
                if recommendations:
                    print(f"    • Recommendations: {len(recommendations)} suggestions")
        
        # 9. Codebase Health Score
        print("\\n🏥 Codebase Health Assessment:")
        health = analysis.get_codebase_health_score()
        print(f"  • Overall Health Score: {health['overall_health_score']}/100")
        print(f"  • Health Rating: {health['health_rating']}")
        print(f"  • Maintainability Score: {health['maintainability_score']}/100")
        print(f"  • Complexity Score: {health['complexity_score']}/100")
        print(f"  • Dead Code Score: {health['dead_code_score']}/100")
        
        if health['recommendations']:
            print("  • Recommendations:")
            for rec in health['recommendations']:
                print(f"    - {rec}")
        
        # 10. Database Query Examples
        print("\\n🗃️ Database Query Examples:")
        
        # Query dead code
        dead_code_items = analysis.query_analysis_data('dead_code')
        print(f"  • Dead Code Items in DB: {len(dead_code_items)}")
        
        # Query complex functions
        complex_functions = analysis.query_analysis_data('complex_functions', min_complexity=5)
        print(f"  • Complex Functions (>5 complexity): {len(complex_functions)}")
        
        # Query recursive functions
        recursive_functions = analysis.query_analysis_data('recursive_functions')
        print(f"  • Recursive Functions: {len(recursive_functions)}")
        
        # 11. Generate Analysis Report
        print("\\n📄 Generating Analysis Report...")
        markdown_report = analysis.generate_analysis_report('markdown')
        
        # Save report to file
        with open('codebase_analysis_report.md', 'w') as f:
            f.write(markdown_report)
        print("  • Report saved to: codebase_analysis_report.md")
        
        # 12. Key Insights
        print("\\n💡 Key Insights:")
        insights = results['analysis_insights']
        print(f"  • Code Quality: {insights['code_quality']}")
        
        if insights['main_issues']:
            print("  • Main Issues:")
            for issue in insights['main_issues']:
                print(f"    - {issue}")
        
        if insights['strengths']:
            print("  • Strengths:")
            for strength in insights['strengths']:
                print(f"    - {strength}")
        
        if insights['improvement_areas']:
            print("  • Improvement Areas:")
            for area in insights['improvement_areas']:
                print(f"    - {area}")
        
        # 13. Advanced Analysis Examples
        print("\\n🔬 Advanced Analysis Examples:")
        
        # Hop-through-imports example
        print("  📦 Import Resolution Examples:")
        for symbol in list(codebase.symbols)[:3]:  # First 3 symbols
            import_path = analysis.dependency_analyzer.hop_through_imports(
                symbol.qualified_name, max_hops=5
            )
            if len(import_path) > 1:
                print(f"    • {symbol.qualified_name}: {' -> '.join(import_path)}")
        
        # Call graph visualization
        print("  📊 Call Graph Visualization:")
        try:
            viz_file = analysis.call_graph_analyzer.visualize_call_graph(
                "call_graph_visualization.png", max_nodes=20
            )
            print(f"    • Call graph saved to: {viz_file}")
        except Exception as e:
            print(f"    • Call graph visualization failed: {e}")
        
        print("\\n✅ Comprehensive Analysis Complete!")
        print("=" * 60)
        
        # Return summary for further processing
        return {
            'analysis_complete': True,
            'codebase_health_score': health['overall_health_score'],
            'total_issues_found': len(dead_code['dead_functions']) + len(circular_deps),
            'database_path': 'analysis_results.db',
            'report_path': 'codebase_analysis_report.md'
        }
        
    finally:
        # Clean up database connection
        analysis.close()


def demonstrate_specific_capabilities(codebase: Codebase):
    """
    Demonstrate specific capabilities identified from graph-sitter.com documentation.
    """
    
    print("\\n🎯 Demonstrating Specific Graph-sitter.com Capabilities")
    print("=" * 60)
    
    # 1. Function Call and Call Site Analysis
    print("\\n📞 Function Call Analysis:")
    
    # Find the most called function
    functions_with_calls = [(f, len(f.call_sites) if hasattr(f, 'call_sites') else 0) 
                           for f in codebase.functions]
    if functions_with_calls:
        most_called = max(functions_with_calls, key=lambda x: x[1])
        print(f"  • Most called function: {most_called[0].name} ({most_called[1]} call sites)")
        
        # Show call sites
        if hasattr(most_called[0], 'call_sites') and most_called[0].call_sites:
            print("    Call sites:")
            for call in list(most_called[0].call_sites)[:3]:  # Show first 3
                caller = getattr(call, 'parent_function', None)
                if caller:
                    line = getattr(call, 'start_point', [0])[0] if hasattr(call, 'start_point') else 0
                    print(f"      - {caller.name} at line {line}")
    
    # Find function that makes the most calls
    functions_making_calls = [(f, len(f.function_calls) if hasattr(f, 'function_calls') else 0) 
                             for f in codebase.functions]
    if functions_making_calls:
        most_calling = max(functions_making_calls, key=lambda x: x[1])
        print(f"  • Function making most calls: {most_calling[0].name} ({most_calling[1]} calls)")
    
    # 2. Class Analysis with Inheritance
    print("\\n🏗️ Class Inheritance Analysis:")
    
    for class_def in list(codebase.classes)[:3]:  # First 3 classes
        print(f"  📋 Class: {class_def.name}")
        
        # Methods analysis
        if hasattr(class_def, 'methods'):
            methods = list(class_def.methods)
            print(f"    • Methods: {len(methods)}")
            
            # Method visibility
            public_methods = [m for m in methods if not m.name.startswith('_')]
            private_methods = [m for m in methods if m.name.startswith('_')]
            print(f"    • Public methods: {len(public_methods)}")
            print(f"    • Private methods: {len(private_methods)}")
        
        # Attributes analysis
        if hasattr(class_def, 'attributes'):
            attributes = list(class_def.attributes)
            print(f"    • Attributes: {len(attributes)}")
        
        # Inheritance analysis
        if hasattr(class_def, 'parent_class_names'):
            parents = class_def.parent_class_names
            print(f"    • Parent classes: {[str(p) for p in parents]}")
        
        if hasattr(class_def, 'subclasses'):
            children = list(class_def.subclasses)
            print(f"    • Child classes: {len(children)}")
    
    # 3. Import and Dependency Analysis
    print("\\n📦 Import and Dependency Analysis:")
    
    # Analyze imports
    total_imports = 0
    external_imports = 0
    
    for file in codebase.files:
        if hasattr(file, 'imports'):
            file_imports = list(file.imports)
            total_imports += len(file_imports)
            
            # Count external imports (simplified heuristic)
            for imp in file_imports:
                if hasattr(imp, 'imported_symbol'):
                    symbol = imp.imported_symbol
                    # Consider it external if it's not in our codebase files
                    if not any(symbol.name in f.name for f in codebase.files):
                        external_imports += 1
    
    print(f"  • Total imports: {total_imports}")
    print(f"  • External imports: {external_imports}")
    print(f"  • Internal imports: {total_imports - external_imports}")
    
    # 4. Symbol Usage Analysis
    print("\\n🔍 Symbol Usage Analysis:")
    
    # Analyze symbol usages
    symbols_with_usages = []
    for symbol in list(codebase.symbols)[:10]:  # First 10 symbols
        if hasattr(symbol, 'symbol_usages'):
            usage_count = len(symbol.symbol_usages)
            symbols_with_usages.append((symbol, usage_count))
    
    if symbols_with_usages:
        # Sort by usage count
        symbols_with_usages.sort(key=lambda x: x[1], reverse=True)
        
        print("  Top used symbols:")
        for symbol, usage_count in symbols_with_usages[:5]:
            print(f"    • {symbol.name}: {usage_count} usages")
    
    # 5. File Analysis
    print("\\n📁 File Analysis:")
    
    for file in list(codebase.files)[:3]:  # First 3 files
        print(f"  📄 File: {file.name}")
        
        # Count different symbol types
        if hasattr(file, 'functions'):
            functions = list(file.functions)
            print(f"    • Functions: {len(functions)}")
        
        if hasattr(file, 'classes'):
            classes = list(file.classes)
            print(f"    • Classes: {len(classes)}")
        
        if hasattr(file, 'imports'):
            imports = list(file.imports)
            print(f"    • Imports: {len(imports)}")
        
        if hasattr(file, 'global_vars'):
            global_vars = list(file.global_vars)
            print(f"    • Global variables: {len(global_vars)}")
    
    print("\\n✅ Specific Capabilities Demonstration Complete!")


if __name__ == "__main__":
    # Example usage
    codebase = Codebase(".")
    
    # Run comprehensive analysis
    result = analyze_codebase_comprehensively(codebase)
    print(f"\\nAnalysis result: {result}")
    
    # Demonstrate specific capabilities
    demonstrate_specific_capabilities(codebase)

