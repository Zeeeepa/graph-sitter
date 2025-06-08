#!/usr/bin/env python3
"""
Enhanced analyzer with comprehensive analysis capabilities.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import from the correct path
from graph_sitter.configs.models.codebase import CodebaseConfig
import graph_sitter
from graph_sitter import Codebase

from .advanced_config import (
    AdvancedCodebaseConfig,
    create_debug_config,
    create_performance_config,
    create_comprehensive_analysis_config,
    create_typescript_analysis_config,
    create_ast_only_config
)


@graph_sitter.function("enhanced-comprehensive-analysis")
def enhanced_comprehensive_analysis(codebase_path: str, optimization_mode: str = "comprehensive"):
    """
    Run comprehensive analysis using advanced graph-sitter configuration settings.
    
    Args:
        codebase_path: Path to the codebase to analyze
        optimization_mode: Analysis optimization mode:
            - "comprehensive": Full analysis with all features enabled
            - "performance": Fast analysis optimized for large codebases
            - "debug": Debug mode with verbose logging and verification
            - "typescript": TypeScript-specific optimizations
            - "ast_only": AST-only analysis without graph construction
    
    Returns:
        Enhanced analysis results with configuration-specific insights
    """
    start_time = time.time()
    
    print(f"🚀 Starting enhanced analysis with {optimization_mode} mode...")
    
    # Select and create advanced configuration
    config = _get_config_for_mode(optimization_mode)
    codebase_config = config.create_config()
    
    # Initialize codebase with advanced configuration
    codebase = Codebase(codebase_path, config=codebase_config)
    
    results = {
        'metadata': {
            'analysis_timestamp': datetime.now().isoformat(),
            'optimization_mode': optimization_mode,
            'config_settings': vars(config),
            'analysis_duration': 0,
            'codebase_info': _get_codebase_info(codebase, config)
        },
        'enhanced_analysis': {},
        'performance_metrics': {},
        'configuration_insights': {},
        'recommendations': []
    }
    
    # Perform configuration-specific analysis
    if not config.disable_graph:
        # Graph-based analysis
        results['enhanced_analysis'] = _perform_graph_analysis(codebase, config)
        
        # Method usage analysis (if enabled)
        if config.method_usages:
            results['enhanced_analysis']['method_usage_analysis'] = _analyze_method_usages_enhanced(codebase)
        
        # Generic type analysis (if enabled)
        if config.generics:
            results['enhanced_analysis']['generic_type_analysis'] = _analyze_generic_types_enhanced(codebase)
        
        # Full range index analysis (if enabled)
        if config.full_range_index:
            results['enhanced_analysis']['range_index_analysis'] = _analyze_full_range_index(codebase)
        
        # External dependency analysis (if enabled)
        if config.allow_external or config.py_resolve_syspath:
            results['enhanced_analysis']['external_dependency_analysis'] = _analyze_external_dependencies_enhanced(codebase)
    
    # AST-only analysis (always available)
    results['enhanced_analysis']['ast_analysis'] = _perform_ast_analysis(codebase)
    
    # Performance metrics
    results['performance_metrics'] = _collect_performance_metrics(codebase, config, start_time)
    
    # Configuration insights
    results['configuration_insights'] = _generate_configuration_insights(config, results)
    
    # Enhanced recommendations
    results['recommendations'] = _generate_enhanced_recommendations(results, config)
    
    # Update metadata
    results['metadata']['analysis_duration'] = time.time() - start_time
    
    print(f"✅ Enhanced analysis complete in {results['metadata']['analysis_duration']:.2f} seconds")
    
    return results


def _get_config_for_mode(mode: str) -> AdvancedCodebaseConfig:
    """Get the appropriate configuration for the specified mode."""
    config_map = {
        "comprehensive": create_comprehensive_analysis_config(),
        "performance": create_performance_config(),
        "debug": create_debug_config(),
        "typescript": create_typescript_analysis_config(),
        "ast_only": create_ast_only_config()
    }
    
    if mode not in config_map:
        print(f"⚠️ Unknown mode '{mode}', using 'comprehensive'")
        return config_map["comprehensive"]
    
    return config_map[mode]


def _get_codebase_info(codebase: Codebase, config: AdvancedCodebaseConfig) -> Dict[str, Any]:
    """Get codebase information based on configuration capabilities."""
    info = {
        'total_files': len(codebase.files),
        'graph_enabled': not config.disable_graph,
        'file_parse_enabled': not config.disable_file_parse
    }
    
    if not config.disable_graph:
        try:
            info['total_functions'] = len(codebase.functions)
            info['total_classes'] = len(codebase.classes)
            info['total_imports'] = sum(len(file.imports) for file in codebase.files)
        except Exception as e:
            info['graph_error'] = str(e)
    else:
        info['total_functions'] = "N/A (graph disabled)"
        info['total_classes'] = "N/A (graph disabled)"
        info['total_imports'] = "N/A (graph disabled)"
    
    return info


def _perform_graph_analysis(codebase: Codebase, config: AdvancedCodebaseConfig) -> Dict[str, Any]:
    """Perform graph-based analysis using advanced configuration features."""
    analysis = {
        'dependency_resolution': {},
        'usage_tracking': {},
        'import_resolution': {},
        'graph_structure': {}
    }
    
    # Dependency resolution analysis
    if config.method_usages and config.generics:
        analysis['dependency_resolution'] = _analyze_dependency_resolution(codebase)
    
    # Usage tracking analysis
    if config.method_usages:
        analysis['usage_tracking'] = _analyze_usage_tracking(codebase)
    
    # Import resolution analysis
    if config.py_resolve_syspath or config.allow_external:
        analysis['import_resolution'] = _analyze_import_resolution(codebase, config)
    
    # Graph structure analysis
    if config.full_range_index:
        analysis['graph_structure'] = _analyze_graph_structure(codebase)
    
    return analysis


def _analyze_method_usages_enhanced(codebase: Codebase) -> Dict[str, Any]:
    """
    Enhanced method usage analysis using method_usages=True configuration.
    
    From documentation:
    "Enables and disables resolving method usages"
    """
    analysis = {
        'method_call_patterns': {},
        'inheritance_usage': {},
        'polymorphic_calls': {},
        'method_hotspots': []
    }
    
    method_calls = {}
    inheritance_calls = {}
    
    for cls in codebase.classes:
        for method in cls.methods:
            method_key = f"{cls.name}.{method.name}"
            
            # Count method usages
            usage_count = len(method.usages) if method.usages else 0
            method_calls[method_key] = usage_count
            
            # Analyze inheritance patterns
            if cls.superclasses:
                for parent in cls.superclasses:
                    parent_key = f"{parent.name}.{method.name}"
                    if parent_key not in inheritance_calls:
                        inheritance_calls[parent_key] = 0
                    inheritance_calls[parent_key] += usage_count
            
            # Identify hotspots (methods called more than 10 times)
            if usage_count > 10:
                analysis['method_hotspots'].append({
                    'class': cls.name,
                    'method': method.name,
                    'usage_count': usage_count,
                    'file': method.file.filepath
                })
    
    analysis['method_call_patterns'] = dict(sorted(method_calls.items(), key=lambda x: x[1], reverse=True)[:20])
    analysis['inheritance_usage'] = inheritance_calls
    
    # Analyze polymorphic calls
    polymorphic_methods = {}
    for method_key, count in method_calls.items():
        method_name = method_key.split('.')[-1]
        if method_name not in polymorphic_methods:
            polymorphic_methods[method_name] = []
        polymorphic_methods[method_name].append((method_key, count))
    
    # Find methods with same name across multiple classes
    analysis['polymorphic_calls'] = {
        name: calls for name, calls in polymorphic_methods.items() 
        if len(calls) > 1
    }
    
    return analysis


def _analyze_generic_types_enhanced(codebase: Codebase) -> Dict[str, Any]:
    """
    Enhanced generic type analysis using generics=True configuration.
    
    From documentation:
    "Enables and disables generic type resolution"
    """
    analysis = {
        'generic_classes': [],
        'generic_methods': [],
        'type_parameter_usage': {},
        'generic_instantiations': []
    }
    
    for cls in codebase.classes:
        # Check for generic classes
        if hasattr(cls, 'type_parameters') and cls.type_parameters:
            analysis['generic_classes'].append({
                'name': cls.name,
                'type_parameters': [tp.name for tp in cls.type_parameters] if hasattr(cls.type_parameters[0], 'name') else cls.type_parameters,
                'file': cls.file.filepath
            })
            
            # Analyze methods in generic classes
            for method in cls.methods:
                if hasattr(method, 'return_type') and method.return_type:
                    analysis['generic_methods'].append({
                        'class': cls.name,
                        'method': method.name,
                        'return_type': str(method.return_type),
                        'usage_count': len(method.usages) if method.usages else 0
                    })
        
        # Look for generic instantiations in usages
        for usage in cls.usages if cls.usages else []:
            if hasattr(usage, 'type_arguments') and usage.type_arguments:
                analysis['generic_instantiations'].append({
                    'class': cls.name,
                    'type_arguments': [str(arg) for arg in usage.type_arguments],
                    'location': usage.usage_symbol.file.filepath if hasattr(usage, 'usage_symbol') else 'unknown'
                })
    
    return analysis


def _analyze_full_range_index(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze full range index capabilities when full_range_index=True.
    
    From documentation:
    "Enabling full_range_index will create an additional index that maps 
    all tree-sitter ranges to nodes"
    """
    analysis = {
        'range_coverage': {},
        'node_precision': {},
        'location_mapping': []
    }
    
    total_nodes = 0
    nodes_with_ranges = 0
    
    for file in codebase.files:
        file_nodes = 0
        file_ranges = 0
        
        # Analyze functions
        for function in file.functions:
            file_nodes += 1
            if hasattr(function, 'start_point') and function.start_point:
                file_ranges += 1
                
                # Collect precise location examples
                if len(analysis['location_mapping']) < 10:
                    analysis['location_mapping'].append({
                        'type': 'function',
                        'name': function.name,
                        'file': file.filepath,
                        'start_point': function.start_point,
                        'end_point': function.end_point if hasattr(function, 'end_point') else None,
                        'byte_range': (function.start_byte, function.end_byte) if hasattr(function, 'start_byte') else None
                    })
        
        # Analyze classes
        for cls in file.classes:
            file_nodes += 1
            if hasattr(cls, 'start_point') and cls.start_point:
                file_ranges += 1
        
        total_nodes += file_nodes
        nodes_with_ranges += file_ranges
        
        analysis['range_coverage'][file.filepath] = {
            'total_nodes': file_nodes,
            'nodes_with_ranges': file_ranges,
            'coverage_percentage': (file_ranges / file_nodes * 100) if file_nodes > 0 else 0
        }
    
    analysis['node_precision'] = {
        'total_nodes': total_nodes,
        'nodes_with_ranges': nodes_with_ranges,
        'overall_coverage': (nodes_with_ranges / total_nodes * 100) if total_nodes > 0 else 0
    }
    
    return analysis


def _analyze_external_dependencies_enhanced(codebase: Codebase) -> Dict[str, Any]:
    """
    Enhanced external dependency analysis using allow_external and py_resolve_syspath.
    
    From documentation:
    "Enables resolving imports, files, modules, and directories from outside of the repo path"
    "Enables and disables resolution of imports from sys.path"
    """
    analysis = {
        'external_modules': {},
        'sys_path_imports': {},
        'dependency_graph': {},
        'resolution_success_rate': {}
    }
    
    external_count = 0
    sys_path_count = 0
    resolved_count = 0
    total_imports = 0
    
    for file in codebase.files:
        for imp in file.imports:
            total_imports += 1
            
            # Check for external imports
            if hasattr(imp, 'is_external') and imp.is_external:
                external_count += 1
                module_name = imp.module if hasattr(imp, 'module') else str(imp)
                
                if module_name not in analysis['external_modules']:
                    analysis['external_modules'][module_name] = {
                        'usage_count': 0,
                        'files': []
                    }
                
                analysis['external_modules'][module_name]['usage_count'] += 1
                analysis['external_modules'][module_name]['files'].append(file.filepath)
            
            # Check for sys.path imports
            if hasattr(imp, 'from_syspath') and imp.from_syspath:
                sys_path_count += 1
                module_name = imp.module if hasattr(imp, 'module') else str(imp)
                analysis['sys_path_imports'][module_name] = analysis['sys_path_imports'].get(module_name, 0) + 1
            
            # Check resolution success
            if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol:
                resolved_count += 1
    
    analysis['resolution_success_rate'] = {
        'total_imports': total_imports,
        'resolved_imports': resolved_count,
        'external_imports': external_count,
        'sys_path_imports': sys_path_count,
        'resolution_percentage': (resolved_count / total_imports * 100) if total_imports > 0 else 0
    }
    
    return analysis


def _perform_ast_analysis(codebase: Codebase) -> Dict[str, Any]:
    """Perform AST-only analysis (available even with disable_graph=True)."""
    analysis = {
        'file_structure': {},
        'syntax_patterns': {},
        'code_metrics': {}
    }
    
    # File structure analysis
    file_types = {}
    total_lines = 0
    
    for file in codebase.files:
        ext = file.filepath.split('.')[-1] if '.' in file.filepath else 'no_extension'
        file_types[ext] = file_types.get(ext, 0) + 1
        
        # Count lines (basic metric)
        try:
            lines = len(file.source.split('\n'))
            total_lines += lines
        except:
            pass
    
    analysis['file_structure'] = {
        'file_types': file_types,
        'total_files': len(codebase.files),
        'total_lines': total_lines,
        'avg_lines_per_file': total_lines / len(codebase.files) if codebase.files else 0
    }
    
    return analysis


def _collect_performance_metrics(codebase: Codebase, config: AdvancedCodebaseConfig, start_time: float) -> Dict[str, Any]:
    """Collect performance metrics based on configuration."""
    metrics = {
        'analysis_duration': time.time() - start_time,
        'configuration_impact': {},
        'memory_efficiency': {},
        'processing_speed': {}
    }
    
    # Configuration impact analysis
    enabled_features = []
    if config.method_usages:
        enabled_features.append('method_usages')
    if config.generics:
        enabled_features.append('generics')
    if config.full_range_index:
        enabled_features.append('full_range_index')
    if config.exp_lazy_graph:
        enabled_features.append('lazy_graph')
    
    metrics['configuration_impact'] = {
        'enabled_features': enabled_features,
        'feature_count': len(enabled_features),
        'performance_mode': 'optimized' if config.exp_lazy_graph else 'standard'
    }
    
    return metrics


def _analyze_dependency_resolution(codebase: Codebase) -> Dict[str, Any]:
    """Analyze dependency resolution capabilities."""
    resolution_stats = {
        'function_dependencies': 0,
        'class_dependencies': 0,
        'unresolved_dependencies': 0,
        'dependency_chains': []
    }
    
    for function in codebase.functions:
        if hasattr(function, 'dependencies') and function.dependencies:
            resolution_stats['function_dependencies'] += len(function.dependencies)
            
            # Analyze dependency chains
            if len(function.dependencies) > 3:  # Functions with many dependencies
                resolution_stats['dependency_chains'].append({
                    'function': function.name,
                    'dependency_count': len(function.dependencies),
                    'file': function.file.filepath
                })
    
    return resolution_stats


def _analyze_usage_tracking(codebase: Codebase) -> Dict[str, Any]:
    """Analyze usage tracking capabilities."""
    usage_stats = {
        'functions_with_usages': 0,
        'total_usage_sites': 0,
        'unused_functions': 0,
        'high_usage_functions': []
    }
    
    for function in codebase.functions:
        if hasattr(function, 'usages') and function.usages:
            usage_stats['functions_with_usages'] += 1
            usage_count = len(function.usages)
            usage_stats['total_usage_sites'] += usage_count
            
            if usage_count > 5:  # High usage threshold
                usage_stats['high_usage_functions'].append({
                    'function': function.name,
                    'usage_count': usage_count,
                    'file': function.file.filepath
                })
        else:
            usage_stats['unused_functions'] += 1
    
    return usage_stats


def _analyze_import_resolution(codebase: Codebase, config: AdvancedCodebaseConfig) -> Dict[str, Any]:
    """Analyze import resolution capabilities."""
    import_stats = {
        'total_imports': 0,
        'resolved_imports': 0,
        'external_imports': 0,
        'resolution_paths_used': config.import_resolution_paths,
        'resolution_overrides_used': config.import_resolution_overrides
    }
    
    for file in codebase.files:
        for imp in file.imports:
            import_stats['total_imports'] += 1
            
            if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol:
                import_stats['resolved_imports'] += 1
            
            if hasattr(imp, 'is_external') and imp.is_external:
                import_stats['external_imports'] += 1
    
    return import_stats


def _analyze_graph_structure(codebase: Codebase) -> Dict[str, Any]:
    """Analyze graph structure with full range indexing."""
    graph_stats = {
        'node_count': 0,
        'edge_count': 0,
        'range_indexed_nodes': 0,
        'connectivity_metrics': {}
    }
    
    # Count nodes with range information
    for file in codebase.files:
        for function in file.functions:
            graph_stats['node_count'] += 1
            if hasattr(function, 'start_point') and function.start_point:
                graph_stats['range_indexed_nodes'] += 1
            
            # Count edges (dependencies and usages)
            if hasattr(function, 'dependencies'):
                graph_stats['edge_count'] += len(function.dependencies)
            if hasattr(function, 'usages'):
                graph_stats['edge_count'] += len(function.usages)
    
    return graph_stats


def _generate_configuration_insights(config: AdvancedCodebaseConfig, results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate insights about the configuration choices."""
    insights = {
        'optimization_effectiveness': {},
        'feature_utilization': {},
        'performance_recommendations': []
    }
    
    # Analyze optimization effectiveness
    if config.exp_lazy_graph:
        insights['optimization_effectiveness']['lazy_graph'] = "Enabled for performance optimization"
    
    if config.method_usages:
        method_analysis = results.get('enhanced_analysis', {}).get('method_usage_analysis', {})
        if method_analysis:
            hotspot_count = len(method_analysis.get('method_hotspots', []))
            insights['feature_utilization']['method_usages'] = f"Detected {hotspot_count} method hotspots"
    
    if config.generics:
        generic_analysis = results.get('enhanced_analysis', {}).get('generic_type_analysis', {})
        if generic_analysis:
            generic_count = len(generic_analysis.get('generic_classes', []))
            insights['feature_utilization']['generics'] = f"Analyzed {generic_count} generic classes"
    
    # Performance recommendations
    if not config.exp_lazy_graph and results['metadata']['codebase_info']['total_files'] > 100:
        insights['performance_recommendations'].append("Consider enabling exp_lazy_graph for large codebases")
    
    if config.full_range_index and not config.debug:
        insights['performance_recommendations'].append("full_range_index adds overhead - only enable if needed")
    
    return insights


def _generate_enhanced_recommendations(results: Dict[str, Any], config: AdvancedCodebaseConfig) -> List[Dict[str, Any]]:
    """Generate enhanced recommendations based on configuration and analysis."""
    recommendations = []
    
    # Configuration-based recommendations
    if config.method_usages:
        method_analysis = results.get('enhanced_analysis', {}).get('method_usage_analysis', {})
        hotspots = method_analysis.get('method_hotspots', [])
        if hotspots:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': f'Optimize {len(hotspots)} method hotspots',
                'description': 'Methods with high usage counts may benefit from optimization',
                'action': 'Review and optimize frequently called methods',
                'config_feature': 'method_usages'
            })
    
    if config.generics:
        generic_analysis = results.get('enhanced_analysis', {}).get('generic_type_analysis', {})
        generic_classes = generic_analysis.get('generic_classes', [])
        if generic_classes:
            recommendations.append({
                'category': 'architecture',
                'priority': 'medium',
                'title': f'Review {len(generic_classes)} generic type implementations',
                'description': 'Generic types detected - ensure proper type safety',
                'action': 'Validate generic type usage and constraints',
                'config_feature': 'generics'
            })
    
    if config.full_range_index:
        range_analysis = results.get('enhanced_analysis', {}).get('range_index_analysis', {})
        if range_analysis:
            coverage = range_analysis.get('node_precision', {}).get('overall_coverage', 0)
            if coverage < 90:
                recommendations.append({
                    'category': 'quality',
                    'priority': 'medium',
                    'title': f'Improve range coverage ({coverage:.1f}%)',
                    'description': 'Some nodes lack precise location information',
                    'action': 'Review parsing configuration and file structure',
                    'config_feature': 'full_range_index'
                })
    
    return recommendations


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    else:
        codebase_path = "./"
        mode = "comprehensive"
    
    print(f"🔧 Running enhanced analysis with {mode} mode...")
    
    try:
        results = enhanced_comprehensive_analysis(codebase_path, mode)
        
        print(f"\n📊 Enhanced Analysis Results:")
        print(f"Mode: {results['metadata']['optimization_mode']}")
        print(f"Duration: {results['metadata']['analysis_duration']:.2f} seconds")
        print(f"Files: {results['metadata']['codebase_info']['total_files']}")
        
        # Show enabled configuration features
        enabled_features = [k for k, v in results['metadata']['config_settings'].items() 
                          if v and k not in ['import_resolution_paths', 'import_resolution_overrides']]
        print(f"Enabled features: {', '.join(enabled_features)}")
        
        # Show key insights
        if results['configuration_insights']:
            print(f"\n💡 Configuration Insights:")
            for category, insights in results['configuration_insights'].items():
                if isinstance(insights, dict):
                    for key, value in insights.items():
                        print(f"  {key}: {value}")
                elif isinstance(insights, list):
                    for insight in insights:
                        print(f"  • {insight}")
        
        # Show recommendations
        if results['recommendations']:
            print(f"\n🎯 Enhanced Recommendations:")
            for rec in results['recommendations'][:3]:
                print(f"  • {rec['title']} (via {rec['config_feature']})")
    
    except Exception as e:
        print(f"❌ Error during enhanced analysis: {e}")
        import traceback
        traceback.print_exc()
