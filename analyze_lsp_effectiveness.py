#!/usr/bin/env python3
"""
LSP Implementation Effectiveness Analysis

This script analyzes how effectively the LSP methods are implemented
by examining the actual codebase and correlating with errors.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Set, Any
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def analyze_lsp_files():
    """Analyze LSP-specific files for implementation effectiveness."""
    print("🔍 Analyzing LSP Implementation Effectiveness")
    print("=" * 60)
    
    try:
        from graph_sitter.core.codebase import Codebase
        
        # Initialize codebase
        repo_path = Path(__file__).parent
        cb = Codebase(str(repo_path))
        
        # Focus on LSP-related files
        lsp_files = [
            "src/graph_sitter/core/lsp_manager.py",
            "src/graph_sitter/core/lsp_types.py", 
            "src/graph_sitter/core/lsp_type_adapters.py",
            "src/graph_sitter/core/unified_diagnostics.py",
            "src/graph_sitter/extensions/lsp/serena_bridge.py",
            "src/graph_sitter/extensions/lsp/transaction_manager.py",
            "src/graph_sitter/enhanced/codebase.py",
            "src/graph_sitter/codebase/codebase_analysis.py",
            "src/graph_sitter/codebase/codebase_ai.py",
            "src/graph_sitter/ai/codebase_ai.py"
        ]
        
        analysis_results = {
            'lsp_file_analysis': {},
            'function_analysis': {},
            'method_consistency': {},
            'error_patterns': [],
            'recommendations': []
        }
        
        print(f"📊 Analyzing {len(lsp_files)} LSP-related files...")
        
        for file_path in lsp_files:
            full_path = repo_path / file_path
            if full_path.exists():
                print(f"\n🔍 Analyzing: {file_path}")
                file_analysis = analyze_file_effectiveness(cb, file_path)
                analysis_results['lsp_file_analysis'][file_path] = file_analysis
            else:
                print(f"⚠️ File not found: {file_path}")
        
        # Analyze method consistency across files
        print("\n🔄 Analyzing method consistency...")
        consistency_analysis = analyze_method_consistency(analysis_results['lsp_file_analysis'])
        analysis_results['method_consistency'] = consistency_analysis
        
        # Generate recommendations
        print("\n💡 Generating recommendations...")
        recommendations = generate_recommendations(analysis_results)
        analysis_results['recommendations'] = recommendations
        
        # Generate report
        generate_lsp_effectiveness_report(analysis_results)
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ Error in LSP analysis: {e}")
        import traceback
        traceback.print_exc()
        return {}

def analyze_file_effectiveness(cb, file_path: str) -> Dict[str, Any]:
    """Analyze effectiveness of a specific LSP file."""
    file_analysis = {
        'functions': [],
        'classes': [],
        'method_patterns': {},
        'issues': []
    }
    
    try:
        # Find functions in this file
        file_functions = [f for f in cb.functions if hasattr(f, 'file') and str(f.file.path).endswith(file_path.split('/')[-1])]
        
        for func in file_functions:
            func_info = {
                'name': func.name,
                'line': func.line if hasattr(func, 'line') else 'unknown',
                'usages': len(func.usages) if hasattr(func, 'usages') else 0,
                'has_type_annotations': check_type_annotations(func),
                'is_diagnostic_method': is_diagnostic_method(func.name)
            }
            
            # Check for common LSP method patterns
            if func.name in ['get_diagnostics', 'get_all_diagnostics', 'get_all_errors', 'errors', 'get_file_diagnostics', 'get_file_errors']:
                func_info['is_core_lsp_method'] = True
                file_analysis['method_patterns'][func.name] = func_info
            
            file_analysis['functions'].append(func_info)
        
        # Find classes in this file
        file_classes = [c for c in cb.classes if hasattr(c, 'file') and str(c.file.path).endswith(file_path.split('/')[-1])]
        
        for cls in file_classes:
            class_info = {
                'name': cls.name,
                'line': cls.line if hasattr(cls, 'line') else 'unknown',
                'methods': len(cls.methods) if hasattr(cls, 'methods') else 0,
                'subclasses': len(cls.subclasses) if hasattr(cls, 'subclasses') else 0
            }
            file_analysis['classes'].append(class_info)
        
        print(f"  📊 Found {len(file_analysis['functions'])} functions, {len(file_analysis['classes'])} classes")
        
        return file_analysis
        
    except Exception as e:
        print(f"  ❌ Error analyzing {file_path}: {e}")
        return file_analysis

def check_type_annotations(func) -> bool:
    """Check if function has proper type annotations."""
    try:
        has_return_type = hasattr(func, 'return_type_annotation') and func.return_type_annotation
        has_param_types = True
        
        if hasattr(func, 'parameters'):
            for param in func.parameters:
                if not hasattr(param, 'type_annotation') or not param.type_annotation:
                    has_param_types = False
                    break
        
        return has_return_type and has_param_types
    except:
        return False

def is_diagnostic_method(func_name: str) -> bool:
    """Check if function name suggests it's a diagnostic method."""
    diagnostic_keywords = [
        'diagnostic', 'error', 'warning', 'issue', 'problem',
        'lint', 'check', 'validate', 'analyze', 'collect'
    ]
    
    return any(keyword in func_name.lower() for keyword in diagnostic_keywords)

def analyze_method_consistency(file_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze consistency of method names and patterns across files."""
    consistency_analysis = {
        'diagnostic_methods': {},
        'naming_inconsistencies': [],
        'duplicate_functionality': [],
        'missing_methods': []
    }
    
    # Collect all diagnostic methods
    all_diagnostic_methods = {}
    
    for file_path, analysis in file_analyses.items():
        for pattern_name, method_info in analysis.get('method_patterns', {}).items():
            if pattern_name not in all_diagnostic_methods:
                all_diagnostic_methods[pattern_name] = []
            all_diagnostic_methods[pattern_name].append({
                'file': file_path,
                'info': method_info
            })
    
    consistency_analysis['diagnostic_methods'] = all_diagnostic_methods
    
    # Identify naming inconsistencies
    method_variants = {
        'get_diagnostics': ['get_diagnostics', 'get_all_diagnostics', 'diagnostics'],
        'get_errors': ['get_errors', 'get_all_errors', 'errors'],
        'get_file_diagnostics': ['get_file_diagnostics', 'get_file_errors', 'file_diagnostics', 'file_errors']
    }
    
    for base_method, variants in method_variants.items():
        found_variants = []
        for variant in variants:
            if variant in all_diagnostic_methods:
                found_variants.append(variant)
        
        if len(found_variants) > 1:
            consistency_analysis['naming_inconsistencies'].append({
                'base_method': base_method,
                'variants_found': found_variants,
                'files_affected': [method['file'] for variant in found_variants for method in all_diagnostic_methods[variant]]
            })
    
    return consistency_analysis

def generate_recommendations(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []
    
    # Method naming consistency recommendations
    inconsistencies = analysis_results.get('method_consistency', {}).get('naming_inconsistencies', [])
    for inconsistency in inconsistencies:
        recommendations.append({
            'type': 'naming_consistency',
            'priority': 'high',
            'title': f"Standardize {inconsistency['base_method']} method naming",
            'description': f"Found variants: {', '.join(inconsistency['variants_found'])}. Choose one canonical name and create adapters for others.",
            'affected_files': inconsistency['files_affected'],
            'action': f"Standardize on 'get_all_diagnostics' and create backward compatibility adapters"
        })
    
    # Type annotation recommendations
    for file_path, analysis in analysis_results.get('lsp_file_analysis', {}).items():
        untyped_functions = [f for f in analysis.get('functions', []) if not f.get('has_type_annotations', True)]
        if untyped_functions:
            recommendations.append({
                'type': 'type_annotations',
                'priority': 'medium',
                'title': f"Add type annotations to {file_path}",
                'description': f"Found {len(untyped_functions)} functions without proper type annotations",
                'affected_files': [file_path],
                'action': f"Add type hints to improve code quality and IDE support"
            })
    
    # Dead code recommendations
    for file_path, analysis in analysis_results.get('lsp_file_analysis', {}).items():
        unused_functions = [f for f in analysis.get('functions', []) if f.get('usages', 0) == 0 and not f['name'].startswith('_')]
        if unused_functions:
            recommendations.append({
                'type': 'dead_code',
                'priority': 'low',
                'title': f"Remove unused functions in {file_path}",
                'description': f"Found {len(unused_functions)} potentially unused functions",
                'affected_files': [file_path],
                'action': f"Review and remove unused functions: {', '.join([f['name'] for f in unused_functions[:5]])}"
            })
    
    return recommendations

def generate_lsp_effectiveness_report(analysis_results: Dict[str, Any]) -> None:
    """Generate a comprehensive LSP effectiveness report."""
    print("\n" + "="*80)
    print("📋 LSP IMPLEMENTATION EFFECTIVENESS REPORT")
    print("="*80)
    
    # Summary statistics
    total_files = len(analysis_results.get('lsp_file_analysis', {}))
    total_functions = sum(len(analysis.get('functions', [])) for analysis in analysis_results.get('lsp_file_analysis', {}).values())
    total_classes = sum(len(analysis.get('classes', [])) for analysis in analysis_results.get('lsp_file_analysis', {}).values())
    
    print(f"\n📊 SUMMARY")
    print("-" * 40)
    print(f"• LSP files analyzed: {total_files}")
    print(f"• Total functions: {total_functions}")
    print(f"• Total classes: {total_classes}")
    
    # Method consistency analysis
    consistency = analysis_results.get('method_consistency', {})
    diagnostic_methods = consistency.get('diagnostic_methods', {})
    inconsistencies = consistency.get('naming_inconsistencies', [])
    
    print(f"\n🔄 METHOD CONSISTENCY")
    print("-" * 40)
    print(f"• Diagnostic method variants found: {len(diagnostic_methods)}")
    print(f"• Naming inconsistencies: {len(inconsistencies)}")
    
    if diagnostic_methods:
        print("\n📋 Diagnostic Methods Found:")
        for method_name, implementations in diagnostic_methods.items():
            print(f"  • {method_name}: {len(implementations)} implementations")
            for impl in implementations:
                file_name = impl['file'].split('/')[-1]
                usages = impl['info'].get('usages', 0)
                print(f"    - {file_name} (usages: {usages})")
    
    if inconsistencies:
        print("\n⚠️ Naming Inconsistencies:")
        for inconsistency in inconsistencies:
            print(f"  • {inconsistency['base_method']}: {', '.join(inconsistency['variants_found'])}")
    
    # Recommendations
    recommendations = analysis_results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS ({len(recommendations)} total)")
        print("-" * 40)
        
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
        low_priority = [r for r in recommendations if r.get('priority') == 'low']
        
        if high_priority:
            print(f"\n🔥 HIGH PRIORITY ({len(high_priority)}):")
            for rec in high_priority:
                print(f"  • {rec['title']}")
                print(f"    {rec['description']}")
                print(f"    Action: {rec['action']}")
        
        if medium_priority:
            print(f"\n⚠️ MEDIUM PRIORITY ({len(medium_priority)}):")
            for rec in medium_priority[:3]:  # Show first 3
                print(f"  • {rec['title']}")
        
        if low_priority:
            print(f"\n📝 LOW PRIORITY ({len(low_priority)}):")
            for rec in low_priority[:3]:  # Show first 3
                print(f"  • {rec['title']}")
    
    print("\n" + "="*80)
    print("✅ LSP effectiveness analysis complete!")
    print("="*80)

def main():
    """Main analysis function."""
    print("🚀 Starting LSP Implementation Effectiveness Analysis")
    
    # Run LSP-focused analysis
    results = analyze_lsp_files()
    
    # Save results
    try:
        with open("lsp_effectiveness_analysis.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: lsp_effectiveness_analysis.json")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    print("\n🎉 LSP effectiveness analysis completed!")

if __name__ == "__main__":
    main()
