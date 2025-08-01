#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Script

This script uses graph-sitter SDK to analyze the codebase for:
- Untyped parameters and return types
- Dead code detection
- Import relationship analysis
- Class hierarchy exploration
- LSP/Serena error integration
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Set, Any
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_codebase():
    """Initialize the graph-sitter codebase."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        # Initialize codebase for current directory, excluding tests and codemods
        repo_path = Path(__file__).parent
        print(f"🔍 Initializing codebase analysis for: {repo_path}")
        
        # Create codebase instance
        cb = Codebase(str(repo_path))
        
        print(f"✅ Codebase initialized with {len(cb.files)} files")
        return cb
        
    except Exception as e:
        print(f"❌ Failed to initialize codebase: {e}")
        return None

def find_untyped_parameters(cb) -> List[Dict[str, Any]]:
    """Find parameters without type annotations."""
    print("\n🔍 Finding untyped parameters...")
    untyped_params = []
    
    try:
        for func in cb.functions:
            if hasattr(func, 'parameters'):
                for param in func.parameters:
                    if not hasattr(param, 'type_annotation') or not param.type_annotation:
                        untyped_params.append({
                            'function': func.name,
                            'parameter': param.name if hasattr(param, 'name') else str(param),
                            'file': func.file.path if hasattr(func, 'file') else 'unknown',
                            'line': func.line if hasattr(func, 'line') else 'unknown'
                        })
        
        print(f"📊 Found {len(untyped_params)} untyped parameters")
        return untyped_params
        
    except Exception as e:
        print(f"❌ Error finding untyped parameters: {e}")
        return []

def find_untyped_return_types(cb) -> List[Dict[str, Any]]:
    """Find functions without return type annotations."""
    print("\n🔍 Finding functions without return type annotations...")
    untyped_returns = []
    
    try:
        for func in cb.functions:
            if not hasattr(func, 'return_type_annotation') or not func.return_type_annotation:
                untyped_returns.append({
                    'function': func.name,
                    'file': func.file.path if hasattr(func, 'file') else 'unknown',
                    'line': func.line if hasattr(func, 'line') else 'unknown'
                })
        
        print(f"📊 Found {len(untyped_returns)} functions without return type annotations")
        return untyped_returns
        
    except Exception as e:
        print(f"❌ Error finding untyped return types: {e}")
        return []

def find_dead_code(cb) -> List[Dict[str, Any]]:
    """Find unused code (functions with no usages)."""
    print("\n🗑️ Finding dead code...")
    dead_functions = []
    
    try:
        for func in cb.functions:
            if hasattr(func, 'usages') and len(func.usages) == 0:
                # Skip special methods and common patterns that might not show usages
                if not (func.name.startswith('__') and func.name.endswith('__')):
                    if not func.name.startswith('test_'):
                        dead_functions.append({
                            'function': func.name,
                            'file': func.file.path if hasattr(func, 'file') else 'unknown',
                            'line': func.line if hasattr(func, 'line') else 'unknown',
                            'usages': len(func.usages) if hasattr(func, 'usages') else 0
                        })
        
        print(f"📊 Found {len(dead_functions)} potentially dead functions")
        return dead_functions
        
    except Exception as e:
        print(f"❌ Error finding dead code: {e}")
        return []

def analyze_import_relationships(cb) -> Dict[str, Any]:
    """Analyze import relationships for all files."""
    print("\n🔗 Analyzing import relationships...")
    import_analysis = {
        'files_with_imports': 0,
        'total_imports': 0,
        'circular_imports': [],
        'unused_imports': [],
        'file_relationships': {}
    }
    
    try:
        for file in cb.files:
            file_path = str(file.path) if hasattr(file, 'path') else str(file)
            if not file_path.endswith('.py'):
                continue
                
            file_info = {
                'inbound_imports': [],
                'outbound_imports': [],
                'import_count': 0
            }
            
            # Analyze inbound imports (files that import this file)
            if hasattr(file, 'inbound_imports'):
                for import_stmt in file.inbound_imports:
                    if hasattr(import_stmt, 'file'):
                        file_info['inbound_imports'].append(import_stmt.file.path)
            
            # Analyze outbound imports (files this file imports)
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    if hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                        if hasattr(import_stmt.resolved_symbol, 'file'):
                            file_info['outbound_imports'].append(import_stmt.resolved_symbol.file.path)
                            file_info['import_count'] += 1
            
            if file_info['import_count'] > 0:
                import_analysis['files_with_imports'] += 1
                import_analysis['total_imports'] += file_info['import_count']
                import_analysis['file_relationships'][file.path] = file_info
        
        print(f"📊 Analyzed {import_analysis['files_with_imports']} files with imports")
        print(f"📊 Total imports: {import_analysis['total_imports']}")
        return import_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing import relationships: {e}")
        return import_analysis

def explore_class_hierarchies(cb) -> Dict[str, Any]:
    """Explore class hierarchies and inheritance relationships."""
    print("\n🏗️ Exploring class hierarchies...")
    class_analysis = {
        'total_classes': 0,
        'base_classes': [],
        'inheritance_chains': {},
        'deep_hierarchies': []
    }
    
    try:
        for cls in cb.classes:
            class_analysis['total_classes'] += 1
            
            # Check if this is a base class (has subclasses)
            if hasattr(cls, 'subclasses') and len(cls.subclasses) > 0:
                base_info = {
                    'name': cls.name,
                    'file': cls.file.path if hasattr(cls, 'file') else 'unknown',
                    'subclasses': []
                }
                
                for subclass in cls.subclasses:
                    subclass_info = {
                        'name': subclass.name,
                        'file': subclass.file.path if hasattr(subclass, 'file') else 'unknown',
                        'sub_subclasses': []
                    }
                    
                    # Check for deeper inheritance
                    if hasattr(subclass, 'subclasses'):
                        for sub_subclass in subclass.subclasses:
                            subclass_info['sub_subclasses'].append({
                                'name': sub_subclass.name,
                                'file': sub_subclass.file.path if hasattr(sub_subclass, 'file') else 'unknown'
                            })
                    
                    base_info['subclasses'].append(subclass_info)
                
                class_analysis['base_classes'].append(base_info)
                class_analysis['inheritance_chains'][cls.name] = base_info
        
        print(f"📊 Found {class_analysis['total_classes']} classes")
        print(f"📊 Found {len(class_analysis['base_classes'])} base classes with inheritance")
        return class_analysis
        
    except Exception as e:
        print(f"❌ Error exploring class hierarchies: {e}")
        return class_analysis

def get_lsp_serena_errors(cb) -> List[Dict[str, Any]]:
    """Retrieve all LSP/Serena errors for the codebase."""
    print("\n🚨 Retrieving LSP/Serena errors...")
    lsp_errors = []
    
    try:
        # Try to use the LSP system we've been working on
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        from graph_sitter.core.lsp_manager import LSPManager
        
        # Initialize LSP for the current codebase
        repo_path = str(Path(__file__).parent)
        
        # Try SerenaLSPBridge first
        try:
            bridge = SerenaLSPBridge(repo_path)
            if bridge.is_initialized:
                diagnostics = bridge.get_all_diagnostics()
                for diag in diagnostics:
                    lsp_errors.append({
                        'source': 'SerenaLSPBridge',
                        'file': diag.file_path,
                        'line': diag.line if hasattr(diag, 'line') else 'unknown',
                        'character': diag.character if hasattr(diag, 'character') else 'unknown',
                        'message': diag.message,
                        'severity': str(diag.severity),
                        'error_type': str(diag.error_type) if hasattr(diag, 'error_type') else 'unknown'
                    })
                print(f"✅ Retrieved {len(diagnostics)} diagnostics from SerenaLSPBridge")
        except Exception as e:
            print(f"⚠️ SerenaLSPBridge not available: {e}")
        
        # Try LSPManager
        try:
            manager = LSPManager(repo_path)
            all_errors = manager.get_all_errors()
            for error in all_errors.errors:
                lsp_errors.append({
                    'source': 'LSPManager',
                    'file': error.file_path,
                    'line': error.range.start.line if hasattr(error, 'range') else 'unknown',
                    'character': error.range.start.character if hasattr(error, 'range') else 'unknown',
                    'message': error.message,
                    'severity': str(error.severity),
                    'error_type': str(error.error_type)
                })
            print(f"✅ Retrieved {len(all_errors.errors)} errors from LSPManager")
        except Exception as e:
            print(f"⚠️ LSPManager not available: {e}")
        
        print(f"📊 Total LSP/Serena errors: {len(lsp_errors)}")
        return lsp_errors
        
    except Exception as e:
        print(f"❌ Error retrieving LSP/Serena errors: {e}")
        return []

def analyze_function_effectiveness(cb, lsp_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze how effectively methods are implemented by correlating with errors."""
    print("\n📈 Analyzing function effectiveness...")
    effectiveness_analysis = {
        'total_functions': 0,
        'functions_with_errors': 0,
        'error_prone_functions': [],
        'clean_functions': [],
        'error_hotspots': {}
    }
    
    try:
        # Create a mapping of files to errors
        file_errors = {}
        for error in lsp_errors:
            file_path = error['file']
            if file_path not in file_errors:
                file_errors[file_path] = []
            file_errors[file_path].append(error)
        
        # Analyze each function
        for func in cb.functions:
            effectiveness_analysis['total_functions'] += 1
            func_file = func.file.path if hasattr(func, 'file') else 'unknown'
            func_line = func.line if hasattr(func, 'line') else 0
            
            # Check if this function has errors
            func_errors = []
            if func_file in file_errors:
                for error in file_errors[func_file]:
                    error_line = error.get('line', 0)
                    if isinstance(error_line, (int, str)) and str(error_line).isdigit():
                        error_line = int(error_line)
                        # Check if error is within function range (approximate)
                        if abs(error_line - func_line) <= 10:  # Within 10 lines
                            func_errors.append(error)
            
            func_info = {
                'name': func.name,
                'file': func_file,
                'line': func_line,
                'error_count': len(func_errors),
                'errors': func_errors,
                'usages': len(func.usages) if hasattr(func, 'usages') else 0
            }
            
            if len(func_errors) > 0:
                effectiveness_analysis['functions_with_errors'] += 1
                effectiveness_analysis['error_prone_functions'].append(func_info)
            else:
                effectiveness_analysis['clean_functions'].append(func_info)
        
        # Identify error hotspots (files with most errors)
        for file_path, errors in file_errors.items():
            if len(errors) > 5:  # Files with more than 5 errors
                effectiveness_analysis['error_hotspots'][file_path] = len(errors)
        
        print(f"📊 Analyzed {effectiveness_analysis['total_functions']} functions")
        print(f"📊 Functions with errors: {effectiveness_analysis['functions_with_errors']}")
        print(f"📊 Error hotspots: {len(effectiveness_analysis['error_hotspots'])}")
        return effectiveness_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing function effectiveness: {e}")
        return effectiveness_analysis

def generate_report(analysis_results: Dict[str, Any]) -> None:
    """Generate a comprehensive analysis report."""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
    print("="*80)
    
    # Summary statistics
    print("\n📊 SUMMARY STATISTICS")
    print("-" * 40)
    
    untyped_params = analysis_results.get('untyped_parameters', [])
    untyped_returns = analysis_results.get('untyped_returns', [])
    dead_functions = analysis_results.get('dead_code', [])
    import_analysis = analysis_results.get('import_analysis', {})
    class_analysis = analysis_results.get('class_analysis', {})
    lsp_errors = analysis_results.get('lsp_errors', [])
    effectiveness = analysis_results.get('effectiveness', {})
    
    print(f"• Untyped parameters: {len(untyped_params)}")
    print(f"• Functions without return types: {len(untyped_returns)}")
    print(f"• Potentially dead functions: {len(dead_functions)}")
    print(f"• Total imports analyzed: {import_analysis.get('total_imports', 0)}")
    print(f"• Total classes: {class_analysis.get('total_classes', 0)}")
    print(f"• LSP/Serena errors: {len(lsp_errors)}")
    print(f"• Functions with errors: {effectiveness.get('functions_with_errors', 0)}")
    
    # Top issues
    print("\n🚨 TOP ISSUES TO ADDRESS")
    print("-" * 40)
    
    # Show top error-prone functions
    error_prone = effectiveness.get('error_prone_functions', [])
    if error_prone:
        print("\n🔥 Most Error-Prone Functions:")
        sorted_functions = sorted(error_prone, key=lambda x: x['error_count'], reverse=True)[:10]
        for func in sorted_functions:
            print(f"  • {func['name']} ({func['file']}) - {func['error_count']} errors")
    
    # Show error hotspots
    hotspots = effectiveness.get('error_hotspots', {})
    if hotspots:
        print("\n🎯 Error Hotspot Files:")
        sorted_hotspots = sorted(hotspots.items(), key=lambda x: x[1], reverse=True)[:10]
        for file_path, error_count in sorted_hotspots:
            print(f"  • {file_path} - {error_count} errors")
    
    # Show dead code
    if dead_functions:
        print(f"\n🗑️ Dead Code Functions (showing first 10 of {len(dead_functions)}):")
        for func in dead_functions[:10]:
            print(f"  • {func['function']} ({func['file']})")
    
    # Show inheritance hierarchies
    base_classes = class_analysis.get('base_classes', [])
    if base_classes:
        print(f"\n🏗️ Class Inheritance Hierarchies (showing first 5 of {len(base_classes)}):")
        for base_class in base_classes[:5]:
            print(f"  • {base_class['name']} ({len(base_class['subclasses'])} subclasses)")
            for subclass in base_class['subclasses'][:3]:  # Show first 3 subclasses
                print(f"    └─ {subclass['name']}")
    
    print("\n" + "="*80)
    print("✅ Analysis complete! Check the detailed results above.")
    print("="*80)

def save_detailed_results(analysis_results: Dict[str, Any]) -> None:
    """Save detailed analysis results to JSON file."""
    try:
        output_file = "codebase_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """Main analysis function."""
    print("🚀 Starting Comprehensive Codebase Analysis")
    print("=" * 60)
    
    # Initialize codebase
    cb = setup_codebase()
    if not cb:
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    # Run all analyses
    analysis_results = {}
    
    print("\n🔍 Running analysis phases...")
    analysis_results['untyped_parameters'] = find_untyped_parameters(cb)
    analysis_results['untyped_returns'] = find_untyped_return_types(cb)
    analysis_results['dead_code'] = find_dead_code(cb)
    analysis_results['import_analysis'] = analyze_import_relationships(cb)
    analysis_results['class_analysis'] = explore_class_hierarchies(cb)
    analysis_results['lsp_errors'] = get_lsp_serena_errors(cb)
    analysis_results['effectiveness'] = analyze_function_effectiveness(cb, analysis_results['lsp_errors'])
    
    # Generate report
    generate_report(analysis_results)
    
    # Save detailed results
    save_detailed_results(analysis_results)
    
    print("\n🎉 Comprehensive analysis completed successfully!")

if __name__ == "__main__":
    main()
