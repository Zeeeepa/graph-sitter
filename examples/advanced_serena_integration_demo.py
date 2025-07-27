#!/usr/bin/env python3
"""
Advanced Serena Integration Demo

This demo showcases the comprehensive Serena integration capabilities
including knowledge extraction, error analysis, context inclusion,
and relationship mapping.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena import (
    SerenaAdvancedAPI,
    create_serena_api,
    quick_error_analysis,
    quick_knowledge_extraction
)


async def demo_knowledge_extraction(api: SerenaAdvancedAPI, codebase: Codebase):
    """Demonstrate comprehensive knowledge extraction."""
    print("=" * 60)
    print("🧠 KNOWLEDGE EXTRACTION DEMO")
    print("=" * 60)
    
    # Get a sample file for demonstration
    sample_file = None
    for file in codebase.files:
        if file.functions:  # Find a file with functions
            sample_file = file
            break
    
    if not sample_file:
        print("No suitable file found for demo")
        return
    
    print(f"📁 Analyzing file: {sample_file.name}")
    
    # Extract comprehensive knowledge
    knowledge = await api.extract_knowledge(
        file_path=sample_file.filepath,
        symbol_name=sample_file.functions[0].name if sample_file.functions else None,
        include_context=True
    )
    
    print(f"🔍 Knowledge extractors used: {knowledge.get('extractors_used', [])}")
    
    # Display semantic knowledge
    if 'semantic' in knowledge:
        semantic = knowledge['semantic']
        print(f"🎯 Semantic Analysis:")
        print(f"  - Symbol semantics: {len(semantic.get('symbol_semantics', {}))}")
        print(f"  - Usage patterns: {len(semantic.get('usage_patterns', {}))}")
        print(f"  - Relationships: {len(semantic.get('semantic_relationships', {}))}")
    
    # Display architectural knowledge
    if 'architectural' in knowledge:
        architectural = knowledge['architectural']
        print(f"🏗️ Architectural Analysis:")
        print(f"  - Design patterns: {architectural.get('design_patterns', {})}")
        print(f"  - Coupling analysis: {architectural.get('coupling_analysis', {})}")
    
    # Display dependency knowledge
    if 'dependency' in knowledge:
        dependency = knowledge['dependency']
        print(f"🔗 Dependency Analysis:")
        print(f"  - Direct dependencies: {len(dependency.get('direct_dependencies', {}))}")
        print(f"  - Impact analysis: {dependency.get('impact_analysis', {})}")
    
    print()


async def demo_knowledge_graph(api: SerenaAdvancedAPI):
    """Demonstrate knowledge graph construction."""
    print("=" * 60)
    print("🕸️ KNOWLEDGE GRAPH DEMO")
    print("=" * 60)
    
    # Build knowledge graph
    graph = await api.build_knowledge_graph(
        include_semantic_layers=True,
        include_metrics=True
    )
    
    print(f"📊 Graph Statistics:")
    print(f"  - Total nodes: {len(graph.get('nodes', {}))}")
    print(f"  - Total edges: {len(graph.get('edges', []))}")
    print(f"  - Clusters: {len(graph.get('clusters', {}))}")
    
    if 'metrics' in graph:
        metrics = graph['metrics']
        print(f"  - Node types: {metrics.get('node_types', {})}")
        print(f"  - Edge types: {metrics.get('edge_types', {})}")
        print(f"  - Graph density: {metrics.get('density', 0):.3f}")
    
    # Display semantic layers if available
    if 'semantic_layers' in graph and graph['semantic_layers']:
        print(f"🧠 Semantic Layers:")
        for layer_name, layer_data in graph['semantic_layers'].items():
            print(f"  - {layer_name}: {type(layer_data).__name__}")
    
    print()


async def demo_error_analysis(api: SerenaAdvancedAPI, codebase: Codebase):
    """Demonstrate comprehensive error analysis."""
    print("=" * 60)
    print("🐛 ERROR ANALYSIS DEMO")
    print("=" * 60)
    
    # Create a sample error for demonstration
    sample_error = {
        "id": "demo_error_001",
        "type": "complexity_issue",
        "severity": "high",
        "file_path": list(codebase.files)[0].filepath if codebase.files else "unknown",
        "line_number": 42,
        "function_name": list(codebase.functions)[0].name if codebase.functions else "demo_function",
        "message": "High cyclomatic complexity detected",
        "description": "Function has cyclomatic complexity of 25, exceeding recommended threshold"
    }
    
    print(f"🔍 Analyzing error: {sample_error['id']}")
    
    # Perform comprehensive error analysis
    analysis = await api.analyze_error_comprehensive(
        error_info=sample_error,
        include_visualizations=True,
        include_suggestions=True
    )
    
    # Display error overview
    if 'error_overview' in analysis:
        overview = analysis['error_overview']
        print(f"📋 Error Overview:")
        print(f"  - Type: {overview.get('basic_info', {}).get('type', 'unknown')}")
        print(f"  - Severity: {overview.get('basic_info', {}).get('severity', 'unknown')}")
        print(f"  - Location: {overview.get('location', {}).get('file_path', 'unknown')}")
    
    # Display context analysis
    if 'context_analysis' in analysis:
        context = analysis['context_analysis']
        print(f"🔍 Context Analysis:")
        if 'function_context' in context and context['function_context']:
            func_info = context['function_context'].get('function_info', {})
            print(f"  - Function complexity: {func_info.get('complexity', 0)}")
            print(f"  - Parameters: {func_info.get('parameter_count', 0)}")
        
        if 'file_context' in context and context['file_context']:
            file_info = context['file_context'].get('file_info', {})
            print(f"  - File size: {file_info.get('size', 0)} characters")
            print(f"  - Line count: {file_info.get('line_count', 0)}")
    
    # Display fix recommendations
    if 'fix_recommendations' in analysis:
        recommendations = analysis['fix_recommendations']
        print(f"💡 Fix Recommendations:")
        
        immediate_fixes = recommendations.get('immediate_fixes', [])
        if immediate_fixes:
            print(f"  - Immediate fixes: {len(immediate_fixes)}")
            for fix in immediate_fixes[:3]:  # Show first 3
                print(f"    • {fix.get('description', 'No description')}")
        
        best_practices = recommendations.get('best_practices', [])
        if best_practices:
            print(f"  - Best practices: {len(best_practices)}")
            for practice in best_practices[:3]:  # Show first 3
                print(f"    • {practice}")
    
    # Display visualizations
    if 'visualizations' in analysis:
        visualizations = analysis['visualizations']
        print(f"📊 Visualizations: {len(visualizations)} available")
        for viz in visualizations:
            print(f"  - {viz.get('visual_type', 'unknown')}: {viz.get('error_id', 'unknown')}")
    
    print()


async def demo_context_analysis(api: SerenaAdvancedAPI, codebase: Codebase):
    """Demonstrate context analysis capabilities."""
    print("=" * 60)
    print("🎯 CONTEXT ANALYSIS DEMO")
    print("=" * 60)
    
    # Get a sample function for demonstration
    sample_function = None
    sample_file = None
    
    for file in codebase.files:
        if file.functions:
            sample_file = file
            sample_function = file.functions[0]
            break
    
    if not sample_function:
        print("No suitable function found for demo")
        return
    
    print(f"🔍 Analyzing symbol: {sample_function.name}")
    
    # Analyze symbol context
    context = await api.analyze_symbol_context(
        file_path=sample_file.filepath,
        symbol_name=sample_function.name,
        symbol_type="function",
        include_relationships=True
    )
    
    print(f"📋 Symbol Info:")
    symbol_info = context.get('symbol_info', {})
    print(f"  - Name: {symbol_info.get('name', 'unknown')}")
    print(f"  - Type: {symbol_info.get('type', 'unknown')}")
    print(f"  - File: {Path(symbol_info.get('file_path', '')).name}")
    
    # Display context layers
    if 'context' in context:
        ctx = context['context']
        
        if 'function' in ctx and ctx['function']:
            func_ctx = ctx['function']
            func_info = func_ctx.get('function_info', {})
            print(f"🔧 Function Context:")
            print(f"  - Parameters: {func_info.get('parameter_count', 0)}")
            print(f"  - Complexity: {func_info.get('complexity', 0)}")
            print(f"  - Return statements: {func_info.get('return_statements', 0)}")
        
        if 'file' in ctx and ctx['file']:
            file_ctx = ctx['file']
            file_info = file_ctx.get('file_info', {})
            print(f"📁 File Context:")
            print(f"  - Functions: {file_ctx.get('symbols', {}).get('functions', 0)}")
            print(f"  - Classes: {file_ctx.get('symbols', {}).get('classes', 0)}")
            print(f"  - Imports: {file_ctx.get('symbols', {}).get('imports', 0)}")
    
    # Display relationships
    if 'relationships' in context:
        relationships = context['relationships']
        print(f"🔗 Relationships:")
        print(f"  - Related symbols: {len(relationships.get('related_symbols', []))}")
        print(f"  - Dependency chain: {len(relationships.get('dependency_chain', []))}")
    
    print()


async def demo_dependency_analysis(api: SerenaAdvancedAPI, codebase: Codebase):
    """Demonstrate dependency analysis."""
    print("=" * 60)
    print("🔗 DEPENDENCY ANALYSIS DEMO")
    print("=" * 60)
    
    # Get a sample file for demonstration
    sample_file = None
    for file in codebase.files:
        if file.imports:  # Find a file with imports
            sample_file = file
            break
    
    if not sample_file:
        print("No suitable file found for demo")
        return
    
    print(f"📁 Analyzing dependencies for: {sample_file.name}")
    
    # Analyze dependencies
    dependencies = await api.analyze_dependencies(
        file_path=sample_file.filepath,
        include_transitive=True,
        max_depth=3
    )
    
    # Display direct dependencies
    if 'direct_dependencies' in dependencies:
        direct_deps = dependencies['direct_dependencies']
        print(f"📦 Direct Dependencies:")
        
        imports = direct_deps.get('imports', [])
        if imports:
            print(f"  - Imports: {len(imports)}")
            for imp in imports[:5]:  # Show first 5
                print(f"    • {imp}")
        
        function_calls = direct_deps.get('function_calls', [])
        if function_calls:
            print(f"  - Function calls: {len(function_calls)}")
    
    # Display impact analysis
    if 'impact_analysis' in dependencies:
        impact = dependencies['impact_analysis']
        print(f"💥 Impact Analysis:")
        print(f"  - Change impact: {impact.get('change_impact', 'unknown')}")
        
        affected_components = impact.get('affected_components', [])
        if affected_components:
            print(f"  - Affected components: {len(affected_components)}")
    
    print()


async def demo_architectural_analysis(api: SerenaAdvancedAPI):
    """Demonstrate architectural analysis."""
    print("=" * 60)
    print("🏗️ ARCHITECTURAL ANALYSIS DEMO")
    print("=" * 60)
    
    # Analyze project architecture
    architecture = await api.analyze_architecture(
        scope="project",
        include_patterns=True,
        include_metrics=True
    )
    
    print(f"🏢 Project Architecture:")
    
    # Display structure
    if 'structure' in architecture:
        structure = architecture['structure']
        print(f"📊 Structure:")
        print(f"  - Total files: {structure.get('total_files', 0)}")
        print(f"  - Total components: {structure.get('total_components', 0)}")
        print(f"  - Modules: {structure.get('modules', 0)}")
    
    # Display patterns
    if 'patterns' in architecture:
        patterns = architecture['patterns']
        print(f"🎨 Detected Patterns:")
        for pattern in patterns:
            print(f"  - {pattern}")
    
    # Display metrics
    if 'metrics' in architecture:
        metrics = architecture['metrics']
        print(f"📈 Metrics:")
        print(f"  - Graph density: {metrics.get('density', 0):.3f}")
        
        node_types = metrics.get('node_types', {})
        if node_types:
            print(f"  - Node distribution:")
            for node_type, count in node_types.items():
                print(f"    • {node_type}: {count}")
    
    print()


async def demo_quick_functions(codebase: Codebase):
    """Demonstrate quick convenience functions."""
    print("=" * 60)
    print("⚡ QUICK FUNCTIONS DEMO")
    print("=" * 60)
    
    # Quick error analysis
    sample_error = {
        "id": "quick_demo_error",
        "type": "performance_issue",
        "severity": "medium",
        "file_path": list(codebase.files)[0].filepath if codebase.files else "unknown",
        "message": "Potential performance bottleneck detected"
    }
    
    print("🚀 Quick Error Analysis:")
    quick_analysis = await quick_error_analysis(codebase, sample_error)
    
    if 'error_overview' in quick_analysis:
        overview = quick_analysis['error_overview']
        print(f"  - Error type: {overview.get('basic_info', {}).get('type', 'unknown')}")
        print(f"  - Severity: {overview.get('basic_info', {}).get('severity', 'unknown')}")
    
    # Quick knowledge extraction
    if codebase.files:
        sample_file = list(codebase.files)[0]
        print(f"🧠 Quick Knowledge Extraction for: {sample_file.name}")
        
        quick_knowledge = await quick_knowledge_extraction(
            codebase, 
            sample_file.filepath,
            sample_file.functions[0].name if sample_file.functions else None
        )
        
        print(f"  - Extractors used: {quick_knowledge.get('extractors_used', [])}")
        print(f"  - Context included: {'contextual_analysis' in quick_knowledge}")
    
    print()


async def main():
    """Main demo function."""
    print("🚀 ADVANCED SERENA INTEGRATION DEMO")
    print("=" * 60)
    print("This demo showcases the comprehensive Serena integration capabilities")
    print("including knowledge extraction, error analysis, and context inclusion.")
    print()
    
    # Create a sample codebase (you would normally load from a real project)
    try:
        # Try to load from current directory or a sample project
        codebase = Codebase.from_directory(".")
    except Exception:
        print("⚠️ Could not load codebase from current directory.")
        print("Please run this demo from a Python project directory.")
        return
    
    print(f"📊 Loaded codebase with:")
    print(f"  - Files: {len(list(codebase.files))}")
    print(f"  - Functions: {len(list(codebase.functions))}")
    print(f"  - Classes: {len(list(codebase.classes))}")
    print()
    
    # Create advanced API instance
    api = await create_serena_api(
        codebase=codebase,
        enable_serena=True,  # Set to False if Serena MCP is not available
        enable_caching=True,
        max_workers=4
    )
    
    try:
        # Run all demos
        await demo_knowledge_extraction(api, codebase)
        await demo_knowledge_graph(api)
        await demo_error_analysis(api, codebase)
        await demo_context_analysis(api, codebase)
        await demo_dependency_analysis(api, codebase)
        await demo_architectural_analysis(api)
        await demo_quick_functions(codebase)
        
        # Show API status
        print("=" * 60)
        print("📊 API STATUS")
        print("=" * 60)
        status = api.get_api_status()
        print(f"✅ API initialized: {status['initialized']}")
        print(f"🔧 Serena enabled: {status['serena_enabled']}")
        print(f"💾 Caching enabled: {status['caching_enabled']}")
        print(f"🧩 Components: {status['components']}")
        print()
        
        print("🎉 Demo completed successfully!")
        print("=" * 60)
        
    finally:
        # Cleanup
        await api.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

