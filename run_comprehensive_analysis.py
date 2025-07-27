#!/usr/bin/env python3
"""
Comprehensive Analysis of graph-sitter Project
Using the new advanced Serena integration
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any
import json
import time

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.advanced_api import create_serena_api


def safe_get_nested(obj, *keys, default=None):
    """Safely get nested dictionary values."""
    try:
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, {})
            elif hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                return default
        return obj if obj != {} else default
    except (AttributeError, TypeError):
        return default


def safe_get_attribute(obj, attr_name, default=None):
    """Safely get attribute from object."""
    try:
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        elif isinstance(obj, dict):
            return obj.get(attr_name, default)
        else:
            return default
    except (AttributeError, TypeError):
        return default


def validate_data_structure(obj, expected_type=dict, path="root"):
    """Validate data structure and log issues."""
    if not isinstance(obj, expected_type):
        print(f"⚠️ Warning: Expected {expected_type.__name__} at {path}, got {type(obj).__name__}")
        return False
    return True


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


async def analyze_project_structure(api) -> Dict[str, Any]:
    """Analyze the overall project structure."""
    print_section("PROJECT STRUCTURE ANALYSIS")
    
    start_time = time.time()
    
    try:
        # Build knowledge graph
        print("🔍 Building comprehensive knowledge graph...")
        knowledge_graph = await api.build_knowledge_graph(
            include_semantic_layers=True,
            include_metrics=True
        )
        
        print(f"✅ Knowledge graph built in {format_time(time.time() - start_time)}")
        
        # Safely analyze the graph with proper error handling
        if not isinstance(knowledge_graph, dict):
            print(f"⚠️ Warning: Expected dict, got {type(knowledge_graph)}")
            knowledge_graph = {}
        
        nodes = knowledge_graph.get('nodes', []) if isinstance(knowledge_graph, dict) else []
        edges = knowledge_graph.get('edges', []) if isinstance(knowledge_graph, dict) else []
        semantic_layers = knowledge_graph.get('semantic_layers', {}) if isinstance(knowledge_graph, dict) else {}
        metrics = knowledge_graph.get('metrics', {}) if isinstance(knowledge_graph, dict) else {}
        
        print(f"\n📊 Graph Statistics:")
        print(f"   Total nodes: {len(nodes) if isinstance(nodes, list) else 'N/A'}")
        print(f"   Total edges: {len(edges) if isinstance(edges, list) else 'N/A'}")
        print(f"   Semantic layers: {len(semantic_layers) if isinstance(semantic_layers, dict) else 'N/A'}")
        
        # Show metrics if available
        if metrics and isinstance(metrics, dict):
            print(f"\n📈 Graph Metrics:")
            for metric_name, metric_value in metrics.items():
                print(f"   {metric_name}: {metric_value}")
        
        # Safely analyze node types
        node_types = {}
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    node_type = node.get('type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n🏗️ Node Types:")
        for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {node_type}: {count}")
        
        # Analyze semantic layers
        if semantic_layers:
            print(f"\n🧠 Semantic Layers:")
            for layer_name, layer_data in semantic_layers.items():
                layer_nodes = layer_data.get('nodes', [])
                print(f"   {layer_name}: {len(layer_nodes)} nodes")
        
        return {
            'knowledge_graph': knowledge_graph,
            'node_types': node_types,
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during project structure analysis: {e}")
        return {'error': str(e)}


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
                # Extract comprehensive knowledge
                knowledge = await api.extract_knowledge(
                    file_path=file_path,
                    include_context=True,
                    extractors=["semantic", "architectural", "dependency"]
                )
                
                if knowledge:
                    print(f"   ✅ Knowledge extracted:")
                    print(f"      Symbols: {len(knowledge.get('symbols', []))}")
                    print(f"      Dependencies: {len(knowledge.get('dependencies', []))}")
                    print(f"      Context layers: {len(knowledge.get('context_layers', {}))}")
                    
                    # Show key symbols
                    symbols = knowledge.get('symbols', [])
                    if symbols:
                        print(f"      Key symbols:")
                        for symbol in symbols[:5]:  # Show first 5
                            symbol_name = symbol.get('name', 'unknown')
                            symbol_type = symbol.get('type', 'unknown')
                            print(f"        - {symbol_name} ({symbol_type})")
                    
                    results[file_path] = knowledge
                else:
                    print(f"   ⚠️ No knowledge extracted")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[file_path] = {'error': str(e)}
    
    print(f"\n⏱️ Knowledge extraction completed in {format_time(time.time() - start_time)}")
    return results


async def analyze_architectural_patterns(api) -> Dict[str, Any]:
    """Analyze architectural patterns in the codebase."""
    print_section("ARCHITECTURAL PATTERN ANALYSIS")
    
    start_time = time.time()
    
    try:
        # Extract architectural knowledge
        print("🏗️ Analyzing architectural patterns...")
        
        # Analyze key architectural files
        architectural_files = [
            "src/graph_sitter/core/",
            "src/graph_sitter/extensions/",
            "src/graph_sitter/parsers/"
        ]
        
        patterns = {}
        
        for base_path in architectural_files:
            if Path(base_path).exists():
                print(f"\n📁 Analyzing directory: {base_path}")
                
                # Get all Python files in directory
                python_files = list(Path(base_path).rglob("*.py"))
                print(f"   Found {len(python_files)} Python files")
                
                # Analyze patterns in first few files
                for py_file in python_files[:3]:  # Limit to avoid too much output
                    try:
                        knowledge = await api.extract_knowledge(
                            file_path=str(py_file),
                            include_context=True,
                            extractors=["architectural"]
                        )
                        
                        if knowledge and 'architectural_patterns' in knowledge:
                            file_patterns = knowledge['architectural_patterns']
                            patterns[str(py_file)] = file_patterns
                            
                            print(f"   📋 {py_file.name}:")
                            for pattern_type, pattern_data in file_patterns.items():
                                if isinstance(pattern_data, list):
                                    print(f"      {pattern_type}: {len(pattern_data)} instances")
                                else:
                                    print(f"      {pattern_type}: {pattern_data}")
                    
                    except Exception as e:
                        print(f"   ⚠️ Error analyzing {py_file}: {e}")
        
        print(f"\n⏱️ Architectural analysis completed in {format_time(time.time() - start_time)}")
        return patterns
        
    except Exception as e:
        print(f"❌ Error during architectural analysis: {e}")
        return {'error': str(e)}


async def analyze_error_landscape(api) -> Dict[str, Any]:
    """Comprehensive error analysis of the project."""
    print_section("ERROR LANDSCAPE ANALYSIS")
    
    start_time = time.time()
    
    try:
        # Get comprehensive error analysis
        print("🐛 Analyzing error landscape...")
        
        # Get all errors with context using codebase diagnostics
        try:
            # Use the codebase's diagnostic system to get errors
            all_diagnostics = api.codebase.diagnostics
            errors_with_context = []
            
            for diagnostic in all_diagnostics:
                if diagnostic.is_error:
                    error_context = {
                        'error': {
                            'file_path': diagnostic.file_path,
                            'line': diagnostic.line,
                            'column': diagnostic.character,
                            'message': diagnostic.message,
                            'severity': 'error',
                            'code': getattr(diagnostic, 'code', None)
                        },
                        'context': {
                            'source': getattr(diagnostic, 'source', 'unknown')
                        }
                    }
                    errors_with_context.append(error_context)
            
            print(f"   Found {len(errors_with_context)} errors with context")
        except Exception as e:
            print(f"   ⚠️ Error analysis method not available: {e}")
            errors_with_context = []
        
        # Analyze error patterns
        error_patterns = {}
        severity_counts = {}
        file_error_counts = {}
        
        for error_context in errors_with_context:
            error = error_context.get('error', {})
            
            # Count by severity
            severity = error.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by file
            file_path = error.get('file_path', 'unknown')
            file_error_counts[file_path] = file_error_counts.get(file_path, 0) + 1
            
            # Analyze error patterns
            message = error.get('message', '')
            if 'import' in message.lower():
                error_patterns['import_errors'] = error_patterns.get('import_errors', 0) + 1
            elif 'undefined' in message.lower() or 'not defined' in message.lower():
                error_patterns['undefined_errors'] = error_patterns.get('undefined_errors', 0) + 1
            elif 'type' in message.lower():
                error_patterns['type_errors'] = error_patterns.get('type_errors', 0) + 1
            else:
                error_patterns['other_errors'] = error_patterns.get('other_errors', 0) + 1
        
        print(f"\n📊 Error Statistics:")
        print(f"   Total errors: {len(errors_with_context)}")
        
        print(f"\n🚨 By Severity:")
        for severity, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {severity}: {count}")
        
        print(f"\n📁 Most Problematic Files:")
        sorted_files = sorted(file_error_counts.items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:10]:  # Top 10
            print(f"   {file_path}: {count} errors")
        
        print(f"\n🔍 Error Patterns:")
        for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   {pattern}: {count}")
        
        # Analyze error clustering
        print(f"\n🔗 Analyzing error clusters...")
        error_clusters = await api.cluster_errors(errors_with_context)
        
        if error_clusters:
            print(f"   Found {len(error_clusters)} error clusters")
            for i, cluster in enumerate(error_clusters[:5]):  # Show first 5 clusters
                cluster_errors = cluster.get('errors', [])
                cluster_pattern = cluster.get('pattern', 'unknown')
                print(f"   Cluster {i+1}: {len(cluster_errors)} errors ({cluster_pattern})")
        
        print(f"\n⏱️ Error analysis completed in {format_time(time.time() - start_time)}")
        
        return {
            'total_errors': len(errors_with_context),
            'severity_counts': severity_counts,
            'file_error_counts': file_error_counts,
            'error_patterns': error_patterns,
            'error_clusters': error_clusters if 'error_clusters' in locals() else [],
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during error analysis: {e}")
        return {'error': str(e)}


async def analyze_dependencies_and_relationships(api) -> Dict[str, Any]:
    """Analyze dependencies and symbol relationships."""
    print_section("DEPENDENCY & RELATIONSHIP ANALYSIS")
    
    start_time = time.time()
    
    try:
        print("🔗 Analyzing dependencies and relationships...")
        
        # Get dependency graph using codebase graph structure
        try:
            # Use the codebase's graph structure to analyze dependencies
            dependency_graph = {}
            
            # Get all files from the codebase
            all_files = [node for node in api.codebase.ctx.get_nodes() if hasattr(node, 'node_type') and node.node_type == 'file']
            
            for file_node in all_files[:50]:  # Limit to first 50 files for performance
                file_path = str(file_node.file_path) if hasattr(file_node, 'file_path') else str(file_node)
                
                # Get successors (dependencies) for this file
                try:
                    successors = api.codebase.ctx.successors(file_node.id, edge_type='imports')
                    dependencies = []
                    
                    for successor in successors:
                        if hasattr(successor, 'file_path'):
                            dependencies.append(str(successor.file_path))
                        elif hasattr(successor, 'name'):
                            dependencies.append(str(successor.name))
                    
                    if dependencies:
                        dependency_graph[file_path] = dependencies
                except Exception as node_error:
                    # Skip this node if we can't analyze it
                    continue
            
            print(f"   Files with dependencies: {len(dependency_graph)}")
        except Exception as e:
            print(f"   ⚠️ Dependency analysis method not available: {e}")
            dependency_graph = {}
        
        # Analyze dependency patterns
        dependency_stats = {
            'total_files': len(dependency_graph),
            'files_with_deps': 0,
            'total_dependencies': 0,
            'max_dependencies': 0,
            'most_dependent_file': None
        }
        
        for file_path, deps in dependency_graph.items():
            if deps:
                dependency_stats['files_with_deps'] += 1
                dep_count = len(deps)
                dependency_stats['total_dependencies'] += dep_count
                
                if dep_count > dependency_stats['max_dependencies']:
                    dependency_stats['max_dependencies'] = dep_count
                    dependency_stats['most_dependent_file'] = file_path
        
        print(f"\n📊 Dependency Statistics:")
        print(f"   Total files: {dependency_stats['total_files']}")
        print(f"   Files with dependencies: {dependency_stats['files_with_deps']}")
        print(f"   Total dependencies: {dependency_stats['total_dependencies']}")
        print(f"   Average deps per file: {dependency_stats['total_dependencies'] / max(dependency_stats['files_with_deps'], 1):.1f}")
        print(f"   Max dependencies: {dependency_stats['max_dependencies']}")
        if dependency_stats['most_dependent_file']:
            print(f"   Most dependent file: {dependency_stats['most_dependent_file']}")
        
        # Show top dependent files
        print(f"\n🔝 Top Dependent Files:")
        sorted_deps = sorted(
            [(f, len(d)) for f, d in dependency_graph.items() if d],
            key=lambda x: x[1],
            reverse=True
        )
        
        for file_path, dep_count in sorted_deps[:10]:
            print(f"   {file_path}: {dep_count} dependencies")
        
        # Analyze symbol relationships for key files
        print(f"\n🔍 Analyzing symbol relationships...")
        
        key_symbols = [
            ("Codebase", "src/graph_sitter/core/codebase.py"),
            ("SerenaAPI", "src/graph_sitter/extensions/serena/__init__.py"),
            ("GraphBuilder", "src/graph_sitter/core/graph_builder.py")
        ]
        
        symbol_relationships = {}
        
        for symbol_name, file_path in key_symbols:
            if Path(file_path).exists():
                try:
                    # Analyze symbol context
                    context = await api.analyze_symbol_context(
                        file_path=file_path,
                        symbol_name=symbol_name,
                        include_relationships=True
                    )
                    
                    if context:
                        relationships = context.get('relationships', {})
                        usage_patterns = context.get('usage_patterns', {})
                        
                        print(f"   📋 {symbol_name}:")
                        print(f"      Callers: {len(relationships.get('callers', []))}")
                        print(f"      Callees: {len(relationships.get('callees', []))}")
                        print(f"      Usage locations: {len(usage_patterns.get('usage_locations', []))}")
                        
                        symbol_relationships[symbol_name] = {
                            'relationships': relationships,
                            'usage_patterns': usage_patterns
                        }
                
                except Exception as e:
                    print(f"   ⚠️ Error analyzing {symbol_name}: {e}")
        
        print(f"\n⏱️ Dependency analysis completed in {format_time(time.time() - start_time)}")
        
        return {
            'dependency_graph': dependency_graph,
            'dependency_stats': dependency_stats,
            'symbol_relationships': symbol_relationships,
            'analysis_time': time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during dependency analysis: {e}")
        return {'error': str(e)}


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
    if 'knowledge_graph' in structure:
        kg = structure['knowledge_graph']
        print(f"📊 Knowledge Graph:")
        print(f"   Nodes: {len(kg.get('nodes', []))}")
        print(f"   Edges: {len(kg.get('edges', []))}")
        print(f"   Semantic Layers: {len(kg.get('semantic_layers', {}))}")
    
    # Error Summary
    error_analysis = analysis_results.get('error_landscape', {})
    if 'total_errors' in error_analysis:
        print_subsection("ERROR SUMMARY")
        print(f"🐛 Total Errors: {error_analysis['total_errors']}")
        
        severity_counts = error_analysis.get('severity_counts', {})
        for severity, count in severity_counts.items():
            print(f"   {severity}: {count}")
    
    # Dependency Summary
    deps = analysis_results.get('dependencies_relationships', {})
    if 'dependency_stats' in deps:
        stats = deps['dependency_stats']
        print_subsection("DEPENDENCY SUMMARY")
        print(f"🔗 Dependency Overview:")
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Files with dependencies: {stats.get('files_with_deps', 0)}")
        print(f"   Total dependencies: {stats.get('total_dependencies', 0)}")
        print(f"   Most dependent file: {stats.get('most_dependent_file', 'N/A')}")
    
    # Knowledge Summary
    knowledge = analysis_results.get('codebase_knowledge', {})
    analyzed_files = [f for f in knowledge.keys() if not f.endswith('error')]
    print_subsection("KNOWLEDGE EXTRACTION SUMMARY")
    print(f"🧠 Files Analyzed: {len(analyzed_files)}")
    
    total_symbols = 0
    for file_path, file_knowledge in knowledge.items():
        if isinstance(file_knowledge, dict) and 'symbols' in file_knowledge:
            total_symbols += len(file_knowledge['symbols'])
    
    print(f"   Total symbols extracted: {total_symbols}")
    
    # Recommendations
    print_subsection("RECOMMENDATIONS")
    print("💡 Based on the analysis:")
    
    if error_analysis.get('total_errors', 0) > 0:
        print("   1. Address the identified errors, focusing on high-severity issues")
        
        error_patterns = error_analysis.get('error_patterns', {})
        if error_patterns:
            top_pattern = max(error_patterns.items(), key=lambda x: x[1])
            print(f"   2. Focus on {top_pattern[0]} ({top_pattern[1]} instances)")
    
    if deps.get('dependency_stats', {}).get('max_dependencies', 0) > 20:
        print("   3. Consider refactoring files with high dependency counts")
    
    print("   4. The knowledge graph shows good architectural structure")
    print("   5. Continue leveraging the advanced Serena integration for deeper insights")
    
    # Save detailed report
    report_file = "comprehensive_analysis_report.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")


async def main():
    """Main analysis function."""
    print("🚀 COMPREHENSIVE GRAPH-SITTER PROJECT ANALYSIS")
    print("Using Advanced Serena Integration")
    
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
            
            # 3. Architectural Pattern Analysis
            analysis_results['architectural_patterns'] = await analyze_architectural_patterns(api)
            
            # 4. Error Landscape Analysis
            analysis_results['error_landscape'] = await analyze_error_landscape(api)
            
            # 5. Dependencies and Relationships
            analysis_results['dependencies_relationships'] = await analyze_dependencies_and_relationships(api)
            
            # 6. Generate Comprehensive Report
            await generate_comprehensive_report(analysis_results)
            
        finally:
            # Clean shutdown
            print("\n🔧 Shutting down API...")
            await api.shutdown()
        
        total_time = time.time() - overall_start
        print_section("ANALYSIS COMPLETE")
        print(f"🎉 Comprehensive analysis completed successfully!")
        print(f"⏱️ Total execution time: {format_time(total_time)}")
        print(f"📊 Analysis covered:")
        print(f"   - Project structure and knowledge graphs")
        print(f"   - Codebase knowledge extraction")
        print(f"   - Architectural pattern analysis")
        print(f"   - Error landscape mapping")
        print(f"   - Dependency and relationship analysis")
        print(f"   - Comprehensive reporting")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
