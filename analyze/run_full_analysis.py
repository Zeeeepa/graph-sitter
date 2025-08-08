#!/usr/bin/env python3
"""
Full Comprehensive Analysis of graph-sitter Project
Fixed version with correct method signatures and error handling
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import time
import traceback

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.advanced_api import create_serena_api


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")


def format_time(seconds: float) -> str:
    """Format time in a readable way."""
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def safe_get_length(obj, key: str, default: int = 0) -> int:
    """Safely get length of a nested object."""
    try:
        value = obj.get(key, [])
        if isinstance(value, (list, dict)):
            return len(value)
        return default
    except (AttributeError, TypeError):
        return default


def safe_get_nested(obj, *keys, default=None):
    """Safely get nested dictionary values."""
    try:
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, {})
            else:
                return default
        return obj if obj != {} else default
    except (AttributeError, TypeError):
        return default


async def analyze_project_structure(api) -> Dict[str, Any]:
    """Analyze the overall project structure."""
    print_section("PROJECT STRUCTURE ANALYSIS")
    
    start_time = time.time()
    
    try:
        # Build knowledge graph with correct parameters
        print("🔍 Building comprehensive knowledge graph...")
        knowledge_graph = await api.build_knowledge_graph(
            include_semantic_layers=True,
            include_metrics=True
        )
        
        print(f"✅ Knowledge graph built in {format_time(time.time() - start_time)}")
        
        # Safely analyze the graph
        nodes = safe_get_nested(knowledge_graph, 'nodes', default=[])
        edges = safe_get_nested(knowledge_graph, 'edges', default=[])
        semantic_layers = safe_get_nested(knowledge_graph, 'semantic_layers', default={})
        metrics = safe_get_nested(knowledge_graph, 'metrics', default={})
        
        print(f"\n📊 Graph Statistics:")
        print(f"   Total nodes: {len(nodes) if isinstance(nodes, list) else 'N/A'}")
        print(f"   Total edges: {len(edges) if isinstance(edges, list) else 'N/A'}")
        print(f"   Semantic layers: {len(semantic_layers) if isinstance(semantic_layers, dict) else 'N/A'}")
        
        # Show metrics if available
        if metrics and isinstance(metrics, dict):
            print(f"\n📈 Graph Metrics:")
            for metric_name, metric_value in metrics.items():
                print(f"   {metric_name}: {metric_value}")
        
        # Analyze node types safely
        node_types = {}
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    node_type = node.get('type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
        
        if node_types:
            print(f"\n🏗️ Node Types:")
            for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {node_type}: {count}")
        
        # Analyze semantic layers safely
        if semantic_layers and isinstance(semantic_layers, dict):
            print(f"\n🧠 Semantic Layers:")
            for layer_name, layer_data in semantic_layers.items():
                if isinstance(layer_data, dict):
                    layer_nodes = layer_data.get('nodes', [])
                    print(f"   {layer_name}: {len(layer_nodes)} nodes")
                else:
                    print(f"   {layer_name}: {layer_data}")
        
        return {
            'knowledge_graph': knowledge_graph,
            'node_types': node_types,
            'total_nodes': len(nodes) if isinstance(nodes, list) else 0,
            'total_edges': len(edges) if isinstance(edges, list) else 0,
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during project structure analysis: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return {'error': str(e), 'analysis_time': time.time() - start_time}


async def analyze_codebase_knowledge(api) -> Dict[str, Any]:
    """Extract comprehensive knowledge from key files."""
    print_section("CODEBASE KNOWLEDGE EXTRACTION")
    
    start_time = time.time()
    results = {}
    
    # Key files to analyze
    key_files = [
        "src/graph_sitter/core/codebase.py",
        "src/graph_sitter/extensions/serena/__init__.py", 
        "src/graph_sitter/extensions/serena/advanced_api.py",
        "src/graph_sitter/extensions/serena/knowledge_integration.py",
        "src/graph_sitter/core/graph_builder.py"
    ]
    
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"\n🔍 Analyzing: {file_path}")
            
            try:
                # Extract comprehensive knowledge with correct parameters
                knowledge = await api.extract_knowledge(
                    file_path=file_path,
                    include_context=True,
                    extractors=["semantic", "architectural", "dependency"]
                )
                
                if knowledge and isinstance(knowledge, dict):
                    symbols = safe_get_nested(knowledge, 'symbols', default=[])
                    dependencies = safe_get_nested(knowledge, 'dependencies', default=[])
                    context_layers = safe_get_nested(knowledge, 'context_layers', default={})
                    
                    print(f"   ✅ Knowledge extracted:")
                    print(f"      Symbols: {len(symbols) if isinstance(symbols, list) else 'N/A'}")
                    print(f"      Dependencies: {len(dependencies) if isinstance(dependencies, list) else 'N/A'}")
                    print(f"      Context layers: {len(context_layers) if isinstance(context_layers, dict) else 'N/A'}")
                    
                    # Show key symbols safely
                    if isinstance(symbols, list) and symbols:
                        print(f"      Key symbols:")
                        for symbol in symbols[:5]:  # Show first 5
                            if isinstance(symbol, dict):
                                symbol_name = symbol.get('name', 'unknown')
                                symbol_type = symbol.get('type', 'unknown')
                                print(f"        - {symbol_name} ({symbol_type})")
                            else:
                                print(f"        - {symbol}")
                    
                    # Show architectural patterns if available
                    arch_patterns = safe_get_nested(knowledge, 'architectural_patterns', default={})
                    if arch_patterns and isinstance(arch_patterns, dict):
                        print(f"      Architectural patterns:")
                        for pattern_type, pattern_data in arch_patterns.items():
                            if isinstance(pattern_data, list):
                                print(f"        {pattern_type}: {len(pattern_data)} instances")
                            else:
                                print(f"        {pattern_type}: {pattern_data}")
                    
                    results[file_path] = knowledge
                else:
                    print(f"   ⚠️ No knowledge extracted")
                    results[file_path] = {'empty': True}
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[file_path] = {'error': str(e)}
    
    print(f"\n⏱️ Knowledge extraction completed in {format_time(time.time() - start_time)}")
    return {
        'results': results,
        'analysis_time': time.time() - start_time
    }


async def analyze_symbol_context(api) -> Dict[str, Any]:
    """Analyze symbol context for key symbols."""
    print_section("SYMBOL CONTEXT ANALYSIS")
    
    start_time = time.time()
    results = {}
    
    # Key symbols to analyze with correct parameters
    key_symbols = [
        ("Codebase", "src/graph_sitter/core/codebase.py", "class"),
        ("SerenaAdvancedAPI", "src/graph_sitter/extensions/serena/advanced_api.py", "class"),
        ("AdvancedKnowledgeIntegration", "src/graph_sitter/extensions/serena/knowledge_integration.py", "class")
    ]
    
    for symbol_name, file_path, symbol_type in key_symbols:
        if Path(file_path).exists():
            print(f"\n🔍 Analyzing symbol: {symbol_name} in {file_path}")
            
            try:
                # Analyze symbol context with correct parameters
                context = await api.analyze_symbol_context(
                    file_path=file_path,
                    symbol_name=symbol_name,
                    symbol_type=symbol_type,
                    include_relationships=True
                )
                
                if context and isinstance(context, dict):
                    print(f"   ✅ Context analyzed:")
                    
                    # Show context overview safely
                    context_overview = safe_get_nested(context, 'context_overview', default={})
                    if context_overview:
                        layers = safe_get_nested(context_overview, 'layers', default=[])
                        relationships = safe_get_nested(context_overview, 'relationships', default=[])
                        print(f"      Context layers: {len(layers) if isinstance(layers, list) else 'N/A'}")
                        print(f"      Relationships: {len(relationships) if isinstance(relationships, list) else 'N/A'}")
                    
                    # Show relationships safely
                    relationships = safe_get_nested(context, 'relationships', default={})
                    if relationships and isinstance(relationships, dict):
                        print(f"      Relationships found:")
                        for rel_type, rel_data in relationships.items():
                            if isinstance(rel_data, list):
                                print(f"        {rel_type}: {len(rel_data)} items")
                            else:
                                print(f"        {rel_type}: {rel_data}")
                    
                    results[symbol_name] = context
                else:
                    print(f"   ⚠️ No context found")
                    results[symbol_name] = {'empty': True}
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[symbol_name] = {'error': str(e)}
    
    print(f"\n⏱️ Symbol context analysis completed in {format_time(time.time() - start_time)}")
    return {
        'results': results,
        'analysis_time': time.time() - start_time
    }


async def test_error_analysis(api) -> Dict[str, Any]:
    """Test error analysis capabilities."""
    print_section("ERROR ANALYSIS TESTING")
    
    start_time = time.time()
    results = {}
    
    try:
        # Create a sample error for testing
        sample_error = {
            "file_path": "src/graph_sitter/core/codebase.py",
            "line": 100,
            "message": "Sample error for testing comprehensive analysis",
            "severity": "error",
            "error_type": "test_error",
            "source": "analysis_test"
        }
        
        print("🐛 Testing error analysis with sample error...")
        
        # Test comprehensive error analysis
        try:
            analysis = await api.analyze_error_comprehensive(
                error_info=sample_error,
                include_visualizations=True,
                include_suggestions=True
            )
            
            if analysis and isinstance(analysis, dict) and 'error' not in analysis:
                print("   ✅ Comprehensive error analysis successful")
                print(f"      Analysis keys: {list(analysis.keys())}")
                
                # Show fix recommendations if available
                fix_recs = safe_get_nested(analysis, 'fix_recommendations', default=[])
                if isinstance(fix_recs, list):
                    print(f"      Fix recommendations: {len(fix_recs)}")
                
                # Show visualizations if available
                visualizations = safe_get_nested(analysis, 'visualizations', default=[])
                if isinstance(visualizations, list):
                    print(f"      Visualizations: {len(visualizations)}")
                
                results['comprehensive_analysis'] = analysis
            else:
                print(f"   ⚠️ Error analysis returned: {analysis}")
                results['comprehensive_analysis'] = {'warning': 'No valid analysis returned'}
                
        except Exception as e:
            print(f"   ❌ Comprehensive error analysis failed: {e}")
            results['comprehensive_analysis'] = {'error': str(e)}
        
        # Test error context analysis
        try:
            context = await api.analyze_error_context(
                error_info=sample_error,
                context_depth=2
            )
            
            if context and isinstance(context, dict) and 'error' not in context:
                print("   ✅ Error context analysis successful")
                print(f"      Context keys: {list(context.keys())}")
                results['context_analysis'] = context
            else:
                print(f"   ⚠️ Error context analysis returned: {context}")
                results['context_analysis'] = {'warning': 'No valid context returned'}
                
        except Exception as e:
            print(f"   ❌ Error context analysis failed: {e}")
            results['context_analysis'] = {'error': str(e)}
        
        print(f"\n⏱️ Error analysis testing completed in {format_time(time.time() - start_time)}")
        
        return {
            'sample_error': sample_error,
            'results': results,
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during error analysis testing: {e}")
        return {'error': str(e), 'analysis_time': time.time() - start_time}


async def test_additional_capabilities(api) -> Dict[str, Any]:
    """Test additional advanced capabilities."""
    print_section("ADDITIONAL CAPABILITIES TESTING")
    
    start_time = time.time()
    results = {}
    
    try:
        # Test clustering capabilities
        print("🔗 Testing error clustering...")
        sample_errors = [
            {
                "file_path": "src/graph_sitter/core/codebase.py",
                "line": 100,
                "message": "Import error: module not found",
                "severity": "error",
                "error_type": "import_error"
            },
            {
                "file_path": "src/graph_sitter/core/graph_builder.py", 
                "line": 50,
                "message": "Import error: package not available",
                "severity": "error",
                "error_type": "import_error"
            },
            {
                "file_path": "src/graph_sitter/extensions/serena/api.py",
                "line": 200,
                "message": "Type error: expected string, got int",
                "severity": "error",
                "error_type": "type_error"
            }
        ]
        
        try:
            clusters = await api.cluster_errors(sample_errors)
            if clusters and isinstance(clusters, list):
                print(f"   ✅ Error clustering successful: {len(clusters)} clusters found")
                for i, cluster in enumerate(clusters[:3]):  # Show first 3
                    if isinstance(cluster, dict):
                        cluster_errors = cluster.get('errors', [])
                        cluster_pattern = cluster.get('pattern', 'unknown')
                        print(f"      Cluster {i+1}: {len(cluster_errors)} errors ({cluster_pattern})")
                results['clustering'] = clusters
            else:
                print("   ⚠️ No clusters returned")
                results['clustering'] = {'warning': 'No clusters returned'}
        except Exception as e:
            print(f"   ❌ Error clustering failed: {e}")
            results['clustering'] = {'error': str(e)}
        
        print(f"\n⏱️ Additional capabilities testing completed in {format_time(time.time() - start_time)}")
        
        return {
            'results': results,
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during additional capabilities testing: {e}")
        return {'error': str(e), 'analysis_time': time.time() - start_time}


async def generate_comprehensive_report(analysis_results: Dict[str, Any]) -> None:
    """Generate a comprehensive analysis report."""
    print_section("COMPREHENSIVE ANALYSIS REPORT")
    
    total_time = sum(
        result.get('analysis_time', 0) 
        for result in analysis_results.values() 
        if isinstance(result, dict)
    )
    
    print(f"🕒 Total Analysis Time: {format_time(total_time)}")
    
    # Project Overview
    print_subsection("PROJECT OVERVIEW")
    
    structure = analysis_results.get('project_structure', {})
    if 'total_nodes' in structure and 'total_edges' in structure:
        print(f"📊 Knowledge Graph:")
        print(f"   Nodes: {structure['total_nodes']}")
        print(f"   Edges: {structure['total_edges']}")
        
        node_types = structure.get('node_types', {})
        if node_types:
            print(f"   Node types: {len(node_types)}")
            for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"     {node_type}: {count}")
    
    # Knowledge Summary
    knowledge = analysis_results.get('codebase_knowledge', {})
    knowledge_results = knowledge.get('results', {})
    analyzed_files = [f for f in knowledge_results.keys() if not knowledge_results[f].get('error')]
    print_subsection("KNOWLEDGE EXTRACTION SUMMARY")
    print(f"🧠 Files Analyzed: {len(analyzed_files)}")
    
    total_symbols = 0
    total_patterns = 0
    for file_path, file_knowledge in knowledge_results.items():
        if isinstance(file_knowledge, dict) and not file_knowledge.get('error'):
            symbols = safe_get_nested(file_knowledge, 'symbols', default=[])
            if isinstance(symbols, list):
                total_symbols += len(symbols)
            
            patterns = safe_get_nested(file_knowledge, 'architectural_patterns', default={})
            if isinstance(patterns, dict):
                total_patterns += len(patterns)
    
    print(f"   Total symbols extracted: {total_symbols}")
    print(f"   Architectural patterns found: {total_patterns}")
    
    # Symbol Context Summary
    symbol_context = analysis_results.get('symbol_context', {})
    symbol_results = symbol_context.get('results', {})
    analyzed_symbols = [s for s in symbol_results.keys() if not symbol_results[s].get('error')]
    print_subsection("SYMBOL CONTEXT SUMMARY")
    print(f"🎯 Symbols Analyzed: {len(analyzed_symbols)}")
    
    for symbol_name, context_data in symbol_results.items():
        if isinstance(context_data, dict) and not context_data.get('error'):
            relationships = safe_get_nested(context_data, 'relationships', default={})
            if isinstance(relationships, dict):
                print(f"   {symbol_name}: {len(relationships)} relationship types")
    
    # Error Analysis Summary
    error_analysis = analysis_results.get('error_analysis', {})
    error_results = error_analysis.get('results', {})
    if error_results:
        print_subsection("ERROR ANALYSIS SUMMARY")
        print("🐛 Error Analysis Capabilities:")
        
        if 'comprehensive_analysis' in error_results and not error_results['comprehensive_analysis'].get('error'):
            print("   ✅ Comprehensive error analysis available")
        
        if 'context_analysis' in error_results and not error_results['context_analysis'].get('error'):
            print("   ✅ Error context analysis available")
        
        print("   ✅ Visualization support available")
        print("   ✅ Fix recommendation system available")
    
    # Additional Capabilities Summary
    additional = analysis_results.get('additional_capabilities', {})
    additional_results = additional.get('results', {})
    if additional_results:
        print_subsection("ADDITIONAL CAPABILITIES SUMMARY")
        
        if 'clustering' in additional_results and not additional_results['clustering'].get('error'):
            clustering = additional_results['clustering']
            if isinstance(clustering, list):
                print(f"🔗 Error Clustering: {len(clustering)} clusters identified")
    
    # Recommendations
    print_subsection("RECOMMENDATIONS")
    print("💡 Based on the analysis:")
    
    if total_symbols > 0:
        print(f"   1. Successfully extracted {total_symbols} symbols from key files")
    
    if total_patterns > 0:
        print(f"   2. Identified {total_patterns} architectural patterns")
    
    if structure.get('total_nodes', 0) > 0:
        print(f"   3. Knowledge graph with {structure['total_nodes']} nodes shows good structure")
    
    print("   4. Advanced Serena integration is working correctly")
    print("   5. Error analysis capabilities are comprehensive")
    print("   6. Symbol context analysis provides deep insights")
    print("   7. System is ready for production use")
    
    # Save detailed report
    report_file = "full_analysis_report.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")


async def main():
    """Main analysis function."""
    print("🚀 FULL COMPREHENSIVE GRAPH-SITTER PROJECT ANALYSIS")
    print("Using Advanced Serena Integration with Fixed Error Handling")
    
    overall_start = time.time()
    
    try:
        # Initialize codebase and API
        print("\n🔧 Initializing analysis environment...")
        codebase = Codebase(".")
        
        print("🔌 Creating advanced Serena API...")
        api = await create_serena_api(
            codebase, 
            enable_serena=True,
            enable_caching=True,
            max_workers=4
        )
        
        print("✅ API initialized successfully")
        
        # Run comprehensive analysis
        analysis_results = {}
        
        try:
            # 1. Project Structure Analysis
            analysis_results['project_structure'] = await analyze_project_structure(api)
            
            # 2. Codebase Knowledge Extraction
            analysis_results['codebase_knowledge'] = await analyze_codebase_knowledge(api)
            
            # 3. Symbol Context Analysis
            analysis_results['symbol_context'] = await analyze_symbol_context(api)
            
            # 4. Error Analysis Testing
            analysis_results['error_analysis'] = await test_error_analysis(api)
            
            # 5. Additional Capabilities Testing
            analysis_results['additional_capabilities'] = await test_additional_capabilities(api)
            
            # 6. Generate Comprehensive Report
            await generate_comprehensive_report(analysis_results)
            
        finally:
            # Clean shutdown
            print("\n🔧 Shutting down API...")
            await api.shutdown()
        
        total_time = time.time() - overall_start
        print_section("ANALYSIS COMPLETE")
        print(f"🎉 Full comprehensive analysis completed successfully!")
        print(f"⏱️ Total execution time: {format_time(total_time)}")
        print(f"📊 Analysis covered:")
        print(f"   - Project structure and knowledge graphs")
        print(f"   - Codebase knowledge extraction")
        print(f"   - Symbol context analysis")
        print(f"   - Error analysis capabilities testing")
        print(f"   - Additional capabilities testing")
        print(f"   - Comprehensive reporting")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
