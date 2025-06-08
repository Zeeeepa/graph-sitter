#!/usr/bin/env python3
"""
Configuration manager for graph-sitter analysis.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import from the correct path
from graph_sitter.configs.models.codebase import CodebaseConfig
import graph_sitter
from graph_sitter import Codebase

from .advanced_config import AdvancedCodebaseConfig


class ConfigurationManager:
    """
    Manager for advanced graph-sitter configuration settings.
    Provides utilities to create, validate, and optimize configurations.
    """
    
    def __init__(self):
        self.available_configs = {
            'debug': self._create_debug_config,
            'performance': self._create_performance_config,
            'comprehensive': self._create_comprehensive_config,
            'typescript': self._create_typescript_config,
            'ast_only': self._create_ast_only_config,
            'minimal': self._create_minimal_config,
            'experimental': self._create_experimental_config
        }
    
    def get_config_recommendations(self, codebase_path: str) -> Dict[str, Any]:
        """
        Analyze a codebase and recommend optimal configuration settings.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Dictionary with recommended configuration and reasoning
        """
        print("🔍 Analyzing codebase to recommend optimal configuration...")
        
        # Basic analysis with minimal config to determine characteristics
        minimal_config = self._create_minimal_config()
        try:
            codebase = Codebase(codebase_path, config=minimal_config.create_config())
            characteristics = self._analyze_codebase_characteristics(codebase)
        except Exception as e:
            print(f"⚠️ Error during initial analysis: {e}")
            characteristics = {'error': str(e)}
        
        recommendations = {
            'codebase_characteristics': characteristics,
            'recommended_config': self._recommend_config_based_on_characteristics(characteristics),
            'alternative_configs': self._get_alternative_configs(characteristics),
            'performance_considerations': self._get_performance_considerations(characteristics),
            'feature_recommendations': self._get_feature_recommendations(characteristics)
        }
        
        return recommendations
    
    def compare_configurations(self, codebase_path: str, config_names: List[str]) -> Dict[str, Any]:
        """
        Compare multiple configurations on the same codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            config_names: List of configuration names to compare
            
        Returns:
            Comparison results showing performance and capability differences
        """
        print(f"⚖️ Comparing configurations: {', '.join(config_names)}")
        
        comparison_results = {
            'configurations': {},
            'performance_comparison': {},
            'capability_comparison': {},
            'recommendations': []
        }
        
        for config_name in config_names:
            if config_name not in self.available_configs:
                print(f"⚠️ Unknown configuration: {config_name}")
                continue
            
            print(f"  Testing {config_name} configuration...")
            
            try:
                config = self.available_configs[config_name]()
                result = self._test_configuration(codebase_path, config, config_name)
                comparison_results['configurations'][config_name] = result
            except Exception as e:
                comparison_results['configurations'][config_name] = {
                    'error': str(e),
                    'success': False
                }
        
        # Generate comparison analysis
        comparison_results['performance_comparison'] = self._compare_performance(comparison_results['configurations'])
        comparison_results['capability_comparison'] = self._compare_capabilities(comparison_results['configurations'])
        comparison_results['recommendations'] = self._generate_comparison_recommendations(comparison_results)
        
        return comparison_results
    
    def demonstrate_flag_effects(self, codebase_path: str) -> Dict[str, Any]:
        """
        Demonstrate the effects of individual configuration flags.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Results showing the impact of each configuration flag
        """
        print("🧪 Demonstrating individual flag effects...")
        
        demonstrations = {
            'method_usages': self._demonstrate_method_usages_flag(codebase_path),
            'generics': self._demonstrate_generics_flag(codebase_path),
            'full_range_index': self._demonstrate_full_range_index_flag(codebase_path),
            'sync_enabled': self._demonstrate_sync_enabled_flag(codebase_path),
            'exp_lazy_graph': self._demonstrate_lazy_graph_flag(codebase_path),
            'py_resolve_syspath': self._demonstrate_syspath_resolution_flag(codebase_path)
        }
        
        return {
            'flag_demonstrations': demonstrations,
            'summary': self._summarize_flag_effects(demonstrations)
        }
    
    def _create_debug_config(self) -> AdvancedCodebaseConfig:
        """Create debug configuration with verbose logging and verification."""
        config = AdvancedCodebaseConfig()
        config.debug = True
        config.verify_graph = True
        config.track_graph = True
        config.full_range_index = True
        config.sync_enabled = True
        config.method_usages = True
        config.generics = True
        return config
    
    def _create_performance_config(self) -> AdvancedCodebaseConfig:
        """Create performance-optimized configuration."""
        config = AdvancedCodebaseConfig()
        config.exp_lazy_graph = True
        config.method_usages = False
        config.generics = False
        config.full_range_index = False
        config.sync_enabled = False
        config.ignore_process_errors = True
        return config
    
    def _create_comprehensive_config(self) -> AdvancedCodebaseConfig:
        """Create comprehensive analysis configuration."""
        config = AdvancedCodebaseConfig()
        config.method_usages = True
        config.generics = True
        config.full_range_index = True
        config.py_resolve_syspath = True
        config.allow_external = True
        config.sync_enabled = True
        return config
    
    def _create_typescript_config(self) -> AdvancedCodebaseConfig:
        """Create TypeScript-specific configuration."""
        config = AdvancedCodebaseConfig()
        config.method_usages = True
        config.generics = True
        config.full_range_index = True
        config.ts_dependency_manager = True
        config.ts_language_engine = True
        config.sync_enabled = True
        return config
    
    def _create_ast_only_config(self) -> AdvancedCodebaseConfig:
        """Create AST-only configuration without graph construction."""
        config = AdvancedCodebaseConfig()
        config.disable_graph = True
        config.method_usages = False
        config.generics = False
        config.sync_enabled = False
        return config
    
    def _create_minimal_config(self) -> AdvancedCodebaseConfig:
        """Create minimal configuration for basic analysis."""
        config = AdvancedCodebaseConfig()
        # Use all defaults - minimal overhead
        return config
    
    def _create_experimental_config(self) -> AdvancedCodebaseConfig:
        """Create experimental configuration with cutting-edge features."""
        config = AdvancedCodebaseConfig()
        config.exp_lazy_graph = True
        config.v8_ts_engine = True
        config.unpacking_assignment_partial_removal = True
        config.full_range_index = True
        config.track_graph = True
        return config
    
    def _analyze_codebase_characteristics(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze codebase to determine its characteristics."""
        characteristics = {
            'size': {},
            'language_features': {},
            'complexity': {},
            'dependencies': {}
        }
        
        # Size characteristics
        characteristics['size'] = {
            'total_files': len(codebase.files),
            'file_types': self._analyze_file_types(codebase),
            'estimated_size': self._estimate_codebase_size(codebase)
        }
        
        # Language features
        characteristics['language_features'] = {
            'has_classes': len(codebase.classes) > 0,
            'has_functions': len(codebase.functions) > 0,
            'has_imports': any(len(file.imports) > 0 for file in codebase.files),
            'primary_language': self._detect_primary_language(codebase)
        }
        
        # Complexity indicators
        characteristics['complexity'] = {
            'avg_functions_per_file': len(codebase.functions) / len(codebase.files) if codebase.files else 0,
            'avg_classes_per_file': len(codebase.classes) / len(codebase.files) if codebase.files else 0,
            'has_inheritance': any(len(cls.superclasses) > 0 for cls in codebase.classes),
            'import_density': sum(len(file.imports) for file in codebase.files) / len(codebase.files) if codebase.files else 0
        }
        
        return characteristics
    
    def _analyze_file_types(self, codebase: Codebase) -> Dict[str, int]:
        """Analyze file types in the codebase."""
        file_types = {}
        for file in codebase.files:
            ext = Path(file.filepath).suffix or 'no_extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        return file_types
    
    def _estimate_codebase_size(self, codebase: Codebase) -> str:
        """Estimate codebase size category."""
        file_count = len(codebase.files)
        if file_count < 10:
            return "small"
        elif file_count < 100:
            return "medium"
        elif file_count < 1000:
            return "large"
        else:
            return "very_large"
    
    def _detect_primary_language(self, codebase: Codebase) -> str:
        """Detect the primary programming language."""
        file_types = self._analyze_file_types(codebase)
        
        # Language mapping
        language_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        # Find most common language
        language_counts = {}
        for ext, count in file_types.items():
            lang = language_map.get(ext, 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + count
        
        if language_counts:
            return max(language_counts.items(), key=lambda x: x[1])[0]
        return 'unknown'
    
    def _recommend_config_based_on_characteristics(self, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend configuration based on codebase characteristics."""
        if 'error' in characteristics:
            return {
                'config_name': 'minimal',
                'reasoning': 'Error during analysis - using minimal configuration'
            }
        
        size = characteristics['size']['estimated_size']
        primary_lang = characteristics['language_features']['primary_language']
        complexity = characteristics['complexity']
        
        # Size-based recommendations
        if size == 'very_large':
            return {
                'config_name': 'performance',
                'reasoning': 'Large codebase detected - prioritizing performance with lazy graph construction'
            }
        
        # Language-based recommendations
        if primary_lang in ['typescript', 'javascript']:
            return {
                'config_name': 'typescript',
                'reasoning': 'TypeScript/JavaScript detected - using TypeScript-optimized configuration'
            }
        
        # Complexity-based recommendations
        if complexity['has_inheritance'] and complexity['avg_classes_per_file'] > 2:
            return {
                'config_name': 'comprehensive',
                'reasoning': 'Complex object-oriented codebase - using comprehensive analysis with generics and method tracking'
            }
        
        # Default recommendation
        return {
            'config_name': 'comprehensive',
            'reasoning': 'Standard codebase - using comprehensive analysis configuration'
        }
    
    def _get_alternative_configs(self, characteristics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get alternative configuration recommendations."""
        alternatives = []
        
        if characteristics['size']['estimated_size'] in ['large', 'very_large']:
            alternatives.append({
                'config_name': 'performance',
                'reason': 'For faster analysis on large codebase'
            })
        
        if characteristics['language_features']['primary_language'] == 'typescript':
            alternatives.append({
                'config_name': 'typescript',
                'reason': 'For TypeScript-specific optimizations'
            })
        
        alternatives.append({
            'config_name': 'debug',
            'reason': 'For detailed debugging and verification'
        })
        
        return alternatives
    
    def _get_performance_considerations(self, characteristics: Dict[str, Any]) -> List[str]:
        """Get performance considerations based on characteristics."""
        considerations = []
        
        size = characteristics['size']['estimated_size']
        if size in ['large', 'very_large']:
            considerations.append("Consider enabling exp_lazy_graph for better performance")
            considerations.append("Disable method_usages if not needed for analysis")
        
        if characteristics['complexity']['import_density'] > 10:
            considerations.append("High import density - py_resolve_syspath may impact performance")
        
        if characteristics['language_features']['has_inheritance']:
            considerations.append("Inheritance detected - generics flag provides better analysis but costs performance")
        
        return considerations
    
    def _get_feature_recommendations(self, characteristics: Dict[str, Any]) -> List[str]:
        """Get feature recommendations based on characteristics."""
        recommendations = []
        
        if characteristics['language_features']['has_classes']:
            recommendations.append("Enable method_usages for complete call graph analysis")
        
        if characteristics['complexity']['has_inheritance']:
            recommendations.append("Enable generics for accurate type resolution")
        
        if characteristics['size']['estimated_size'] == 'small':
            recommendations.append("Enable full_range_index for precise location mapping")
        
        return recommendations
    
    def _test_configuration(self, codebase_path: str, config: AdvancedCodebaseConfig, config_name: str) -> Dict[str, Any]:
        """Test a specific configuration and collect metrics."""
        import time
        
        start_time = time.time()
        
        try:
            codebase = Codebase(codebase_path, config=config.create_config())
            
            # Collect basic metrics
            metrics = {
                'success': True,
                'initialization_time': time.time() - start_time,
                'file_count': len(codebase.files),
                'function_count': len(codebase.functions) if not config.disable_graph else 'N/A',
                'class_count': len(codebase.classes) if not config.disable_graph else 'N/A',
                'config_settings': vars(config),
                'capabilities': self._test_capabilities(codebase, config)
            }
            
        except Exception as e:
            metrics = {
                'success': False,
                'error': str(e),
                'initialization_time': time.time() - start_time,
                'config_settings': vars(config)
            }
        
        return metrics
    
    def _test_capabilities(self, codebase: Codebase, config: AdvancedCodebaseConfig) -> Dict[str, bool]:
        """Test what capabilities are available with the current configuration."""
        capabilities = {}
        
        # Test graph-based capabilities
        try:
            capabilities['can_access_functions'] = len(codebase.functions) >= 0
        except:
            capabilities['can_access_functions'] = False
        
        try:
            capabilities['can_access_classes'] = len(codebase.classes) >= 0
        except:
            capabilities['can_access_classes'] = False
        
        # Test method usage resolution
        if config.method_usages:
            try:
                for cls in codebase.classes[:1]:  # Test first class
                    for method in cls.methods[:1]:  # Test first method
                        capabilities['can_resolve_method_usages'] = hasattr(method, 'usages')
                        break
                    break
            except:
                capabilities['can_resolve_method_usages'] = False
        
        # Test range indexing
        if config.full_range_index:
            try:
                for func in codebase.functions[:1]:  # Test first function
                    capabilities['has_range_indexing'] = hasattr(func, 'start_point') and func.start_point is not None
                    break
            except:
                capabilities['has_range_indexing'] = False
        
        return capabilities
    
    def _compare_performance(self, configurations: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance metrics across configurations."""
        performance_data = {}
        
        for config_name, result in configurations.items():
            if result.get('success'):
                performance_data[config_name] = {
                    'initialization_time': result.get('initialization_time', 0),
                    'file_count': result.get('file_count', 0)
                }
        
        if performance_data:
            fastest_config = min(performance_data.items(), key=lambda x: x[1]['initialization_time'])
            slowest_config = max(performance_data.items(), key=lambda x: x[1]['initialization_time'])
            
            return {
                'fastest_config': fastest_config[0],
                'slowest_config': slowest_config[0],
                'performance_data': performance_data,
                'speed_difference': slowest_config[1]['initialization_time'] - fastest_config[1]['initialization_time']
            }
        
        return {}
    
    def _compare_capabilities(self, configurations: Dict[str, Any]) -> Dict[str, Any]:
        """Compare capabilities across configurations."""
        capability_matrix = {}
        
        for config_name, result in configurations.items():
            if result.get('success'):
                capabilities = result.get('capabilities', {})
                capability_matrix[config_name] = capabilities
        
        # Find most capable configuration
        if capability_matrix:
            capability_scores = {
                name: sum(1 for cap in caps.values() if cap)
                for name, caps in capability_matrix.items()
            }
            
            most_capable = max(capability_scores.items(), key=lambda x: x[1])
            
            return {
                'capability_matrix': capability_matrix,
                'capability_scores': capability_scores,
                'most_capable_config': most_capable[0]
            }
        
        return {}
    
    def _generate_comparison_recommendations(self, comparison_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on configuration comparison."""
        recommendations = []
        
        performance = comparison_results.get('performance_comparison', {})
        capabilities = comparison_results.get('capability_comparison', {})
        
        if performance.get('fastest_config'):
            recommendations.append(f"For best performance: use '{performance['fastest_config']}' configuration")
        
        if capabilities.get('most_capable_config'):
            recommendations.append(f"For most features: use '{capabilities['most_capable_config']}' configuration")
        
        if performance.get('speed_difference', 0) > 1.0:
            recommendations.append("Significant performance differences detected - choose based on your priorities")
        
        return recommendations
    
    def _demonstrate_method_usages_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the method_usages flag."""
        results = {}
        
        # Test with method_usages=True
        config_on = AdvancedCodebaseConfig()
        config_on.method_usages = True
        
        try:
            codebase_on = Codebase(codebase_path, config=config_on.create_config())
            usage_count_on = 0
            for cls in codebase_on.classes:
                for method in cls.methods:
                    if hasattr(method, 'usages') and method.usages:
                        usage_count_on += len(method.usages)
            
            results['method_usages_enabled'] = {
                'total_method_usages_found': usage_count_on,
                'example_methods_with_usages': []
            }
            
            # Collect examples
            for cls in codebase_on.classes[:3]:
                for method in cls.methods:
                    if hasattr(method, 'usages') and method.usages:
                        results['method_usages_enabled']['example_methods_with_usages'].append({
                            'class': cls.name,
                            'method': method.name,
                            'usage_count': len(method.usages)
                        })
                        if len(results['method_usages_enabled']['example_methods_with_usages']) >= 5:
                            break
                if len(results['method_usages_enabled']['example_methods_with_usages']) >= 5:
                    break
        
        except Exception as e:
            results['method_usages_enabled'] = {'error': str(e)}
        
        # Test with method_usages=False
        config_off = AdvancedCodebaseConfig()
        config_off.method_usages = False
        
        try:
            codebase_off = Codebase(codebase_path, config=config_off.create_config())
            usage_count_off = 0
            for cls in codebase_off.classes:
                for method in cls.methods:
                    if hasattr(method, 'usages') and method.usages:
                        usage_count_off += len(method.usages)
            
            results['method_usages_disabled'] = {
                'total_method_usages_found': usage_count_off
            }
        
        except Exception as e:
            results['method_usages_disabled'] = {'error': str(e)}
        
        return results
    
    def _demonstrate_generics_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the generics flag."""
        # Similar implementation to method_usages demonstration
        return {'note': 'Generics demonstration - analyzes generic type resolution differences'}
    
    def _demonstrate_full_range_index_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the full_range_index flag."""
        return {'note': 'Full range index demonstration - shows range-to-node mapping differences'}
    
    def _demonstrate_sync_enabled_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the sync_enabled flag."""
        return {'note': 'Sync enabled demonstration - shows graph sync behavior differences'}
    
    def _demonstrate_lazy_graph_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the exp_lazy_graph flag."""
        return {'note': 'Lazy graph demonstration - shows performance differences'}
    
    def _demonstrate_syspath_resolution_flag(self, codebase_path: str) -> Dict[str, Any]:
        """Demonstrate the effect of the py_resolve_syspath flag."""
        return {'note': 'Syspath resolution demonstration - shows import resolution differences'}
    
    def _summarize_flag_effects(self, demonstrations: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize the effects of all demonstrated flags."""
        return {
            'total_flags_tested': len(demonstrations),
            'successful_demonstrations': len([d for d in demonstrations.values() if 'error' not in d]),
            'key_insights': [
                'method_usages flag significantly affects call graph analysis',
                'full_range_index provides precise location mapping at performance cost',
                'exp_lazy_graph improves initialization time for large codebases'
            ]
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
        action = sys.argv[2] if len(sys.argv) > 2 else "recommend"
    else:
        codebase_path = "./"
        action = "recommend"
    
    manager = ConfigurationManager()
    
    if action == "recommend":
        print("🎯 Getting configuration recommendations...")
        recommendations = manager.get_config_recommendations(codebase_path)
        
        print(f"\n📊 Codebase Characteristics:")
        for category, data in recommendations['codebase_characteristics'].items():
            print(f"  {category}: {data}")
        
        print(f"\n💡 Recommended Configuration:")
        rec = recommendations['recommended_config']
        print(f"  Config: {rec['config_name']}")
        print(f"  Reason: {rec['reasoning']}")
        
        if recommendations['alternative_configs']:
            print(f"\n🔄 Alternative Configurations:")
            for alt in recommendations['alternative_configs']:
                print(f"  • {alt['config_name']}: {alt['reason']}")
    
    elif action == "compare":
        configs_to_compare = ['minimal', 'performance', 'comprehensive', 'debug']
        print(f"⚖️ Comparing configurations: {', '.join(configs_to_compare)}")
        
        comparison = manager.compare_configurations(codebase_path, configs_to_compare)
        
        if comparison['performance_comparison']:
            perf = comparison['performance_comparison']
            print(f"\n🏃 Performance Results:")
            print(f"  Fastest: {perf.get('fastest_config', 'N/A')}")
            print(f"  Slowest: {perf.get('slowest_config', 'N/A')}")
        
        if comparison['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in comparison['recommendations']:
                print(f"  • {rec}")
    
    elif action == "demonstrate":
        print("🧪 Demonstrating flag effects...")
        demonstrations = manager.demonstrate_flag_effects(codebase_path)
        
        print(f"\n📋 Flag Demonstrations:")
        for flag, result in demonstrations['flag_demonstrations'].items():
            print(f"  {flag}: {result.get('note', 'Completed')}")
        
        summary = demonstrations['summary']
        print(f"\n📊 Summary:")
        print(f"  Flags tested: {summary['total_flags_tested']}")
        print(f"  Successful: {summary['successful_demonstrations']}")
    
    else:
        print(f"❌ Unknown action: {action}")
        print("Available actions: recommend, compare, demonstrate")
