#!/usr/bin/env python3
"""
Comprehensive Serena Demo with Enhanced Features

This demo showcases the full integration of Serena capabilities with graph-sitter,
including error detection, semantic analysis, and advanced codebase understanding.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False

# Try to import Serena components
SERENA_COMPONENTS = {}
try:
    from graph_sitter.extensions.serena.types import SerenaConfig, SerenaCapability
    SERENA_COMPONENTS['types'] = True
except ImportError:
    SERENA_COMPONENTS['types'] = False

try:
    from graph_sitter.extensions.serena.core import SerenaCore
    SERENA_COMPONENTS['core'] = True
except ImportError:
    SERENA_COMPONENTS['core'] = False

try:
    from graph_sitter.extensions.serena.intelligence import CodeIntelligence
    SERENA_COMPONENTS['intelligence'] = True
except ImportError:
    SERENA_COMPONENTS['intelligence'] = False

try:
    from graph_sitter.extensions.serena.auto_init import _initialized
    SERENA_COMPONENTS['auto_init'] = _initialized
except ImportError:
    SERENA_COMPONENTS['auto_init'] = False


class ComprehensiveCodebaseAnalyzer:
    """Comprehensive analyzer that works with available components."""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.errors_found: List[Dict[str, Any]] = []
        self.warnings_found: List[Dict[str, Any]] = []
        self.analysis_results: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
    def initialize_codebase(self) -> bool:
        """Initialize the codebase with available features."""
        try:
            print(f"🔍 Initializing codebase analysis for: {self.codebase_path}")
            
            if not GRAPH_SITTER_AVAILABLE:
                print("❌ Graph-sitter not available")
                return False
                
            self.codebase = Codebase(str(self.codebase_path))
            print("✅ Graph-sitter codebase initialized")
            
            # Check Serena availability
            serena_status = self._check_serena_status()
            print(f"📊 Serena status: {serena_status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def _check_serena_status(self) -> Dict[str, Any]:
        """Check what Serena components are available."""
        status = {
            'available_components': SERENA_COMPONENTS,
            'integration_active': False,
            'methods_available': []
        }
        
        if self.codebase:
            # Check if Serena methods are available on codebase
            serena_methods = [
                'get_serena_status', 'shutdown_serena', 'get_completions',
                'get_hover_info', 'get_signature_help', 'rename_symbol',
                'extract_method', 'semantic_search', 'generate_boilerplate'
            ]
            
            available_methods = []
            for method in serena_methods:
                if hasattr(self.codebase, method):
                    available_methods.append(method)
            
            status['methods_available'] = available_methods
            status['integration_active'] = len(available_methods) > 0
            
            # Try to get actual Serena status if available
            if hasattr(self.codebase, 'get_serena_status'):
                try:
                    serena_status = self.codebase.get_serena_status()
                    status['serena_internal_status'] = serena_status
                except Exception as e:
                    status['serena_error'] = str(e)
        
        return status
    
    def analyze_codebase_structure(self) -> Dict[str, Any]:
        """Analyze the basic structure of the codebase."""
        if not self.codebase:
            return {}
        
        print("\n📊 Analyzing codebase structure...")
        
        structure = {
            'total_files': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0,
            'languages': set(),
            'file_types': defaultdict(int),
            'largest_files': [],
            'most_complex_functions': [],
            'dependency_graph_stats': {}
        }
        
        try:
            # Get basic statistics
            if hasattr(self.codebase, 'files'):
                files = list(self.codebase.files)
                structure['total_files'] = len(files)
                
                # Analyze file types
                for file in files:
                    ext = Path(file.file_path).suffix
                    structure['file_types'][ext] += 1
                    
                    # Track languages
                    if ext == '.py':
                        structure['languages'].add('Python')
                    elif ext in ['.js', '.jsx']:
                        structure['languages'].add('JavaScript')
                    elif ext in ['.ts', '.tsx']:
                        structure['languages'].add('TypeScript')
                
                # Find largest files
                file_sizes = []
                for file in files:
                    try:
                        full_path = self.codebase_path / file.file_path
                        if full_path.exists():
                            size = full_path.stat().st_size
                            lines = len(full_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                            file_sizes.append({
                                'path': file.file_path,
                                'size_bytes': size,
                                'lines': lines
                            })
                    except Exception:
                        continue
                
                structure['largest_files'] = sorted(file_sizes, key=lambda x: x['lines'], reverse=True)[:10]
            
            # Get function and class statistics
            if hasattr(self.codebase, 'functions'):
                functions = list(self.codebase.functions)
                structure['total_functions'] = len(functions)
                
                # Find most complex functions (by name length as proxy)
                complex_functions = []
                for func in functions:
                    try:
                        func_name = getattr(func, 'name', 'unknown')
                        file_path = getattr(func, 'file_path', None) or getattr(func, 'filepath', None) or 'unknown'
                        complexity_score = len(func_name) + (file_path.count('/') * 2)
                        complex_functions.append({
                            'name': func_name,
                            'file': file_path,
                            'complexity_proxy': complexity_score
                        })
                    except Exception:
                        continue
                
                structure['most_complex_functions'] = sorted(
                    complex_functions, key=lambda x: x['complexity_proxy'], reverse=True
                )[:10]
            
            if hasattr(self.codebase, 'classes'):
                classes = list(self.codebase.classes)
                structure['total_classes'] = len(classes)
            
            if hasattr(self.codebase, 'imports'):
                imports = list(self.codebase.imports)
                structure['total_imports'] = len(imports)
            
            # Get dependency graph statistics
            if hasattr(self.codebase, 'graph'):
                graph = self.codebase.graph
                structure['dependency_graph_stats'] = {
                    'total_nodes': graph.num_nodes() if hasattr(graph, 'num_nodes') else 'N/A',
                    'total_edges': graph.num_edges() if hasattr(graph, 'num_edges') else 'N/A'
                }
            
            structure['languages'] = list(structure['languages'])
            
        except Exception as e:
            print(f"⚠️  Error analyzing structure: {e}")
            structure['error'] = str(e)
        
        return structure
    
    def detect_code_issues(self) -> Dict[str, Any]:
        """Detect various code issues and patterns."""
        if not self.codebase:
            return {}
        
        print("\n🔍 Detecting code issues...")
        
        issues = {
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'patterns': {
                'long_functions': [],
                'large_classes': [],
                'complex_imports': [],
                'potential_duplicates': []
            }
        }
        
        try:
            # Analyze functions for issues
            if hasattr(self.codebase, 'functions'):
                for func in self.codebase.functions:
                    try:
                        # Get file path safely
                        file_path = getattr(func, 'file_path', None) or getattr(func, 'filepath', None) or 'unknown'
                        func_name = getattr(func, 'name', 'unknown')
                        
                        # Check for long function names (potential code smell)
                        if len(func_name) > 50:
                            issues['warnings'].append({
                                'type': 'long_function_name',
                                'message': f"Function name is very long: {func_name}",
                                'file': file_path,
                                'function': func_name
                            })
                        
                        # Check for functions with many parameters (if available)
                        if hasattr(func, 'parameters') and len(func.parameters) > 7:
                            issues['warnings'].append({
                                'type': 'too_many_parameters',
                                'message': f"Function has {len(func.parameters)} parameters",
                                'file': file_path,
                                'function': func_name
                            })
                        
                        # Add to patterns
                        if len(func_name) > 30:
                            issues['patterns']['long_functions'].append({
                                'name': func_name,
                                'file': file_path,
                                'name_length': len(func_name)
                            })
                            
                    except Exception as e:
                        issues['errors'].append({
                            'type': 'function_analysis_error',
                            'message': f"Error analyzing function: {e}",
                            'file': 'unknown'
                        })
            
            # Analyze classes for issues
            if hasattr(self.codebase, 'classes'):
                for cls in self.codebase.classes:
                    try:
                        # Get file path and class name safely
                        file_path = getattr(cls, 'file_path', None) or getattr(cls, 'filepath', None) or 'unknown'
                        class_name = getattr(cls, 'name', 'unknown')
                        
                        # Check for very long class names
                        if len(class_name) > 40:
                            issues['warnings'].append({
                                'type': 'long_class_name',
                                'message': f"Class name is very long: {class_name}",
                                'file': file_path,
                                'class': class_name
                            })
                        
                        # Check for classes with many methods (if available)
                        if hasattr(cls, 'methods') and len(cls.methods) > 20:
                            issues['warnings'].append({
                                'type': 'large_class',
                                'message': f"Class has {len(cls.methods)} methods",
                                'file': file_path,
                                'class': class_name
                            })
                            
                            issues['patterns']['large_classes'].append({
                                'name': class_name,
                                'file': file_path,
                                'method_count': len(cls.methods)
                            })
                            
                    except Exception as e:
                        issues['errors'].append({
                            'type': 'class_analysis_error',
                            'message': f"Error analyzing class: {e}",
                            'file': 'unknown'
                        })
            
            # Analyze imports for issues
            if hasattr(self.codebase, 'imports'):
                import_counts = defaultdict(int)
                for imp in self.codebase.imports:
                    try:
                        # Get file path safely
                        file_path = getattr(imp, 'file_path', None) or getattr(imp, 'filepath', None) or 'unknown'
                        import_counts[file_path] += 1
                        
                        # Check for very long import statements
                        module_name = getattr(imp, 'module_name', None) or getattr(imp, 'name', None)
                        if module_name and len(module_name) > 50:
                            issues['suggestions'].append({
                                'type': 'long_import',
                                'message': f"Very long import: {module_name}",
                                'file': file_path
                            })
                    except Exception as e:
                        issues['errors'].append({
                            'type': 'import_analysis_error',
                            'message': f"Error analyzing import: {e}",
                            'file': 'unknown'
                        })
                
                # Find files with too many imports
                for file_path, count in import_counts.items():
                    if count > 30:
                        issues['warnings'].append({
                            'type': 'too_many_imports',
                            'message': f"File has {count} imports",
                            'file': file_path
                        })
                        
                        issues['patterns']['complex_imports'].append({
                            'file': file_path,
                            'import_count': count
                        })
            
            # Look for potential duplicate function names
            if hasattr(self.codebase, 'functions'):
                function_names = defaultdict(list)
                for func in self.codebase.functions:
                    function_names[func.name].append(func.file_path)
                
                for name, files in function_names.items():
                    if len(files) > 1:
                        issues['suggestions'].append({
                            'type': 'duplicate_function_name',
                            'message': f"Function '{name}' appears in {len(files)} files",
                            'function': name,
                            'files': files
                        })
                        
                        issues['patterns']['potential_duplicates'].append({
                            'name': name,
                            'files': files,
                            'count': len(files)
                        })
        
        except Exception as e:
            print(f"⚠️  Error detecting issues: {e}")
            issues['analysis_error'] = str(e)
        
        # Store results
        self.errors_found = issues['errors']
        self.warnings_found = issues['warnings']
        
        return issues
    
    def demonstrate_serena_features(self) -> Dict[str, Any]:
        """Demonstrate available Serena features."""
        if not self.codebase:
            return {'error': 'No codebase available'}
        
        print("\n🚀 Demonstrating Available Serena Features")
        print("=" * 50)
        
        demo_results = {
            'features_tested': [],
            'successful_features': [],
            'failed_features': [],
            'results': {}
        }
        
        # Test each available Serena method
        serena_methods = [
            ('get_serena_status', self._demo_serena_status),
            ('get_completions', self._demo_completions),
            ('get_hover_info', self._demo_hover_info),
            ('get_signature_help', self._demo_signature_help),
            ('semantic_search', self._demo_semantic_search),
            ('rename_symbol', self._demo_rename_symbol),
            ('extract_method', self._demo_extract_method),
            ('generate_boilerplate', self._demo_code_generation),
            ('organize_imports', self._demo_organize_imports)
        ]
        
        for method_name, demo_func in serena_methods:
            demo_results['features_tested'].append(method_name)
            
            if hasattr(self.codebase, method_name):
                try:
                    print(f"\n🧪 Testing {method_name}...")
                    result = demo_func()
                    demo_results['successful_features'].append(method_name)
                    demo_results['results'][method_name] = result
                    print(f"   ✅ {method_name} - Success")
                except Exception as e:
                    demo_results['failed_features'].append(method_name)
                    demo_results['results'][method_name] = {'error': str(e)}
                    print(f"   ❌ {method_name} - Failed: {e}")
            else:
                demo_results['failed_features'].append(method_name)
                demo_results['results'][method_name] = {'error': 'Method not available'}
                print(f"   ⚠️  {method_name} - Not available")
        
        return demo_results
    
    def _demo_serena_status(self) -> Dict[str, Any]:
        """Demo Serena status check."""
        if hasattr(self.codebase, 'get_serena_status'):
            status = self.codebase.get_serena_status()
            print(f"      Status: {status}")
            return status
        return {'error': 'Method not available'}
    
    def _demo_completions(self) -> Dict[str, Any]:
        """Demo code completions."""
        # Find a Python file to test with
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'get_completions'):
            result = self.codebase.get_completions(sample_file, 10, 0)
            if result and result.get('success'):
                completions = result.get('completions', [])
                print(f"      Found {len(completions)} completions")
                return {'completions_count': len(completions), 'sample': completions[:3]}
            else:
                return {'error': 'No completions available'}
        return {'error': 'Method not available'}
    
    def _demo_hover_info(self) -> Dict[str, Any]:
        """Demo hover information."""
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'get_hover_info'):
            result = self.codebase.get_hover_info(sample_file, 20, 10)
            if result and result.get('success'):
                print(f"      Hover info available")
                return {'hover_available': True, 'content_preview': str(result.get('contents', ''))[:100]}
            else:
                return {'error': 'No hover info available'}
        return {'error': 'Method not available'}
    
    def _demo_signature_help(self) -> Dict[str, Any]:
        """Demo signature help."""
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'get_signature_help'):
            result = self.codebase.get_signature_help(sample_file, 30, 15)
            if result and result.get('success'):
                print(f"      Signature help available")
                return {'signature_available': True}
            else:
                return {'error': 'No signature help available'}
        return {'error': 'Method not available'}
    
    def _demo_semantic_search(self) -> Dict[str, Any]:
        """Demo semantic search."""
        if hasattr(self.codebase, 'semantic_search'):
            search_terms = ['function', 'class', 'import']
            results = {}
            
            for term in search_terms:
                search_result = self.codebase.semantic_search(term, max_results=5)
                if search_result and search_result.get('success'):
                    results[term] = len(search_result.get('results', []))
                    print(f"      Search '{term}': {results[term]} results")
                else:
                    results[term] = 0
            
            return {'search_results': results}
        return {'error': 'Method not available'}
    
    def _demo_rename_symbol(self) -> Dict[str, Any]:
        """Demo symbol renaming (preview only)."""
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'rename_symbol'):
            result = self.codebase.rename_symbol(sample_file, 10, 5, 'new_name', preview=True)
            if result and result.get('success'):
                changes = result.get('changes', [])
                print(f"      Rename preview: {len(changes)} changes")
                return {'preview_changes': len(changes)}
            else:
                return {'error': 'Rename not available'}
        return {'error': 'Method not available'}
    
    def _demo_extract_method(self) -> Dict[str, Any]:
        """Demo method extraction (preview only)."""
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'extract_method'):
            result = self.codebase.extract_method(sample_file, 15, 25, 'extracted_method', preview=True)
            if result and result.get('success'):
                print(f"      Extract method preview available")
                return {'extract_available': True}
            else:
                return {'error': 'Extract method not available'}
        return {'error': 'Method not available'}
    
    def _demo_code_generation(self) -> Dict[str, Any]:
        """Demo code generation."""
        if hasattr(self.codebase, 'generate_boilerplate'):
            result = self.codebase.generate_boilerplate(
                'class',
                {'class_name': 'DemoClass', 'methods': ['__init__', 'process']},
                'demo_generated.py'
            )
            if result and result.get('success'):
                print(f"      Code generation available")
                return {'generation_available': True}
            else:
                return {'error': 'Code generation not available'}
        return {'error': 'Method not available'}
    
    def _demo_organize_imports(self) -> Dict[str, Any]:
        """Demo import organization."""
        sample_file = self._find_sample_python_file()
        if not sample_file:
            return {'error': 'No suitable Python file found'}
        
        if hasattr(self.codebase, 'organize_imports'):
            result = self.codebase.organize_imports(sample_file)
            if result and result.get('success'):
                print(f"      Import organization available")
                return {'organize_available': True}
            else:
                return {'error': 'Import organization not available'}
        return {'error': 'Method not available'}
    
    def _find_sample_python_file(self) -> Optional[str]:
        """Find a suitable Python file for testing."""
        if not self.codebase or not hasattr(self.codebase, 'files'):
            return None
        
        for file in self.codebase.files:
            if file.file_path.endswith('.py') and 'src/graph_sitter' in file.file_path:
                return file.file_path
        
        # Fallback to any Python file
        for file in self.codebase.files:
            if file.file_path.endswith('.py'):
                return file.file_path
        
        return None
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
        print("=" * 80)
        
        # Collect all analysis data
        start_time = time.time()
        
        structure = self.analyze_codebase_structure()
        issues = self.detect_code_issues()
        serena_demo = self.demonstrate_serena_features()
        
        analysis_time = time.time() - start_time
        
        # Create comprehensive report
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_time_seconds': round(analysis_time, 2),
            'codebase_path': str(self.codebase_path),
            'structure': structure,
            'issues': issues,
            'serena_features': serena_demo,
            'summary': {
                'total_files': structure.get('total_files', 0),
                'total_functions': structure.get('total_functions', 0),
                'total_classes': structure.get('total_classes', 0),
                'total_errors': len(issues.get('errors', [])),
                'total_warnings': len(issues.get('warnings', [])),
                'total_suggestions': len(issues.get('suggestions', [])),
                'serena_features_working': len(serena_demo.get('successful_features', [])),
                'serena_features_total': len(serena_demo.get('features_tested', []))
            }
        }
        
        # Print summary
        self._print_report_summary(report)
        
        return report
    
    def _print_report_summary(self, report: Dict[str, Any]):
        """Print a summary of the analysis report."""
        summary = report['summary']
        structure = report['structure']
        issues = report['issues']
        serena = report['serena_features']
        
        print(f"\n📈 ANALYSIS SUMMARY:")
        print(f"   Analysis Time: {report['analysis_time_seconds']} seconds")
        print(f"   Total Files: {summary['total_files']}")
        print(f"   Total Functions: {summary['total_functions']}")
        print(f"   Total Classes: {summary['total_classes']}")
        print(f"   Languages: {', '.join(structure.get('languages', []))}")
        
        print(f"\n🔍 ISSUE SUMMARY:")
        print(f"   Errors: {summary['total_errors']}")
        print(f"   Warnings: {summary['total_warnings']}")
        print(f"   Suggestions: {summary['total_suggestions']}")
        
        if issues.get('errors'):
            print(f"\n❌ TOP ERRORS:")
            for i, error in enumerate(issues['errors'][:5]):
                print(f"   {i+1}. {error.get('type', 'unknown')}: {error.get('message', 'No message')}")
        
        if issues.get('warnings'):
            print(f"\n⚠️  TOP WARNINGS:")
            for i, warning in enumerate(issues['warnings'][:5]):
                print(f"   {i+1}. {warning.get('type', 'unknown')}: {warning.get('message', 'No message')}")
        
        print(f"\n🚀 SERENA FEATURES:")
        print(f"   Working Features: {summary['serena_features_working']}/{summary['serena_features_total']}")
        print(f"   Successful: {', '.join(serena.get('successful_features', []))}")
        if serena.get('failed_features'):
            print(f"   Failed: {', '.join(serena.get('failed_features', []))}")
        
        if structure.get('largest_files'):
            print(f"\n📄 LARGEST FILES:")
            for i, file_info in enumerate(structure['largest_files'][:5]):
                print(f"   {i+1}. {file_info['path']} ({file_info['lines']} lines)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if summary['total_errors'] > 0:
            print(f"   🔴 Fix {summary['total_errors']} errors found")
        if summary['total_warnings'] > 10:
            print(f"   🟡 Address {summary['total_warnings']} warnings")
        if summary['serena_features_working'] < summary['serena_features_total']:
            print(f"   🔵 Improve Serena integration ({summary['serena_features_working']}/{summary['serena_features_total']} working)")
        
        print(f"\n✅ Comprehensive analysis complete!")


def main():
    """Main function to run the comprehensive demo."""
    print("🚀 COMPREHENSIVE SERENA CODEBASE ANALYZER")
    print("=" * 50)
    print("Advanced analysis of graph-sitter codebase with Serena integration")
    print("This demo works with available components and provides detailed insights.")
    print()
    
    # Show component availability
    print("📦 COMPONENT AVAILABILITY:")
    print(f"   Graph-sitter: {'✅' if GRAPH_SITTER_AVAILABLE else '❌'}")
    for component, available in SERENA_COMPONENTS.items():
        status = '✅' if available else '❌'
        print(f"   Serena {component}: {status}")
    print()
    
    # Initialize analyzer
    analyzer = ComprehensiveCodebaseAnalyzer(".")
    
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    try:
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        
        # Save report to file
        report_file = Path("codebase_analysis_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    # Cleanup
    try:
        if analyzer.codebase and hasattr(analyzer.codebase, 'shutdown_serena'):
            analyzer.codebase.shutdown_serena()
            print("\n🔄 Serena integration shutdown complete")
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
    
    print("\n🎉 Comprehensive Analysis Complete!")
    print("This demo showcased available Serena features and provided detailed codebase insights.")


if __name__ == "__main__":
    main()
