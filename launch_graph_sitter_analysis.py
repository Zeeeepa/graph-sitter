#!/usr/bin/env python3
"""
🚀 GRAPH-SITTER FEATURES-BASED ANALYSIS LAUNCHER 🚀

This script launches the full graph-sitter features-based implementation
to analyze your codebase for errors, patterns, and insights.
"""

import json
import time
from datetime import datetime
from pathlib import Path

def run_comprehensive_graph_sitter_analysis():
    """Run comprehensive graph-sitter based analysis."""
    
    print("🚀 LAUNCHING GRAPH-SITTER FEATURES-BASED ANALYSIS")
    print("=" * 80)
    
    try:
        # Import graph-sitter modules
        from graph_sitter import Codebase
        from src.graph_sitter.adapters.analysis.import_analysis import analyze_import_relationships
        from src.graph_sitter.adapters.analysis.dead_code_detection import analyze_unused_imports
        from src.graph_sitter.adapters.analysis.symbol_analysis import analyze_symbol_usage, analyze_symbol_relationships
        from src.graph_sitter.adapters.analysis.class_hierarchy import analyze_inheritance_chains
        from src.graph_sitter.adapters.analysis.ai_analysis import analyze_codebase as ai_analyze_codebase
        
        print("✅ All graph-sitter modules loaded successfully!")
        
    except ImportError as e:
        print(f"❌ Error importing graph-sitter modules: {e}")
        return None
    
    # Start analysis
    start_time = time.time()
    
    print("\n📊 Creating Codebase instance with graph-sitter...")
    codebase = Codebase('.')
    
    print(f"✅ Codebase loaded: {len(codebase.files)} files, {len(codebase.functions)} functions")
    
    # Initialize results
    analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'codebase_stats': {
            'total_files': len(codebase.files),
            'total_functions': len(codebase.functions),
            'total_classes': len(codebase.classes),
            'total_symbols': len(codebase.symbols),
        },
        'analyses': {}
    }
    
    print("\n🔍 RUNNING COMPREHENSIVE ANALYSIS MODULES:")
    print("-" * 80)
    
    # 1. Import Analysis
    print("🔄 1. Import Relationship Analysis...")
    try:
        import_result = analyze_import_relationships(codebase)
        analysis_results['analyses']['imports'] = import_result
        print(f"   📦 Total imports: {import_result.get('total_imports', 0)}")
        print(f"   🔄 Import loops: {len(import_result.get('import_loops', []))}")
        if import_result.get('import_loops'):
            print("   ⚠️  Import loops detected!")
    except Exception as e:
        print(f"   ❌ Error in import analysis: {e}")
        analysis_results['analyses']['imports'] = {'error': str(e)}
    
    # 2. Dead Code Analysis
    print("💀 2. Dead Code Detection...")
    try:
        dead_code_result = analyze_unused_imports(codebase)
        analysis_results['analyses']['dead_code'] = dead_code_result
        print(f"   💀 Unused imports: {len(dead_code_result)}")
        if dead_code_result:
            print("   ⚠️  Unused imports found!")
    except Exception as e:
        print(f"   ❌ Error in dead code analysis: {e}")
        analysis_results['analyses']['dead_code'] = {'error': str(e)}
    
    # 3. Symbol Analysis
    print("🔍 3. Symbol Usage Analysis...")
    try:
        symbol_result = analyze_symbol_usage(codebase)
        symbol_relationships = analyze_symbol_relationships(codebase)
        analysis_results['analyses']['symbols'] = {
            'usage': symbol_result,
            'relationships': symbol_relationships
        }
        print(f"   🔍 Symbol usage patterns: {len(symbol_result.get('usage_patterns', []))}")
        print(f"   🔗 Symbol relationships: {len(symbol_relationships.get('relationships', []))}")
    except Exception as e:
        print(f"   ❌ Error in symbol analysis: {e}")
        analysis_results['analyses']['symbols'] = {'error': str(e)}
    
    # 4. Class Hierarchy Analysis
    print("📦 4. Class Hierarchy Analysis...")
    try:
        class_result = analyze_inheritance_chains(codebase)
        analysis_results['analyses']['classes'] = class_result
        print(f"   📦 Inheritance chains: {len(class_result.get('inheritance_chains', []))}")
        if class_result.get('inheritance_chains'):
            print(f"   🏗️  Complex inheritance detected!")
    except Exception as e:
        print(f"   ❌ Error in class hierarchy analysis: {e}")
        analysis_results['analyses']['classes'] = {'error': str(e)}
    
    # 5. AI-Powered Analysis
    print("🤖 5. AI-Powered Code Analysis...")
    try:
        ai_result = ai_analyze_codebase(codebase)
        analysis_results['analyses']['ai_analysis'] = ai_result
        print(f"   🤖 AI insights generated: {len(ai_result.get('insights', []))}")
        print(f"   🎯 AI recommendations: {len(ai_result.get('recommendations', []))}")
    except Exception as e:
        print(f"   ❌ Error in AI analysis: {e}")
        analysis_results['analyses']['ai_analysis'] = {'error': str(e)}
    
    # Calculate analysis time
    end_time = time.time()
    analysis_time = end_time - start_time
    analysis_results['analysis_time_seconds'] = analysis_time
    
    print(f"\n✅ COMPREHENSIVE ANALYSIS COMPLETE!")
    print("=" * 80)
    
    # Summary
    print(f"⏱️  Analysis completed in {analysis_time:.2f} seconds")
    print(f"📁 Files analyzed: {analysis_results['codebase_stats']['total_files']}")
    print(f"🔧 Functions analyzed: {analysis_results['codebase_stats']['total_functions']}")
    print(f"📦 Classes analyzed: {analysis_results['codebase_stats']['total_classes']}")
    print(f"📝 Symbols analyzed: {analysis_results['codebase_stats']['total_symbols']}")
    
    # Key findings
    print(f"\n🎯 KEY FINDINGS:")
    imports = analysis_results['analyses'].get('imports', {})
    dead_code = analysis_results['analyses'].get('dead_code', [])
    symbols = analysis_results['analyses'].get('symbols', {})
    classes = analysis_results['analyses'].get('classes', {})
    ai_analysis = analysis_results['analyses'].get('ai_analysis', {})
    
    print(f"   📦 Total imports analyzed: {imports.get('total_imports', 0)}")
    print(f"   🔄 Import loops detected: {len(imports.get('import_loops', []))}")
    print(f"   💀 Unused imports found: {len(dead_code) if isinstance(dead_code, list) else 0}")
    print(f"   🔍 Symbol patterns identified: {len(symbols.get('usage', {}).get('usage_patterns', []))}")
    print(f"   📦 Inheritance chains: {len(classes.get('inheritance_chains', []))}")
    print(f"   🤖 AI insights: {len(ai_analysis.get('insights', []))}")
    
    # Show critical issues
    critical_issues = []
    
    if imports.get('import_loops'):
        critical_issues.append(f"🔄 {len(imports['import_loops'])} import loops")
    
    if isinstance(dead_code, list) and dead_code:
        critical_issues.append(f"💀 {len(dead_code)} unused imports")
    
    if ai_analysis.get('recommendations'):
        critical_issues.append(f"🤖 {len(ai_analysis['recommendations'])} AI recommendations")
    
    if critical_issues:
        print(f"\n⚠️  CRITICAL ISSUES DETECTED:")
        for issue in critical_issues:
            print(f"   - {issue}")
    else:
        print(f"\n🎉 No critical issues detected! Your codebase looks healthy.")
    
    # Save results
    output_file = "graph_sitter_analysis_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        print(f"\n💾 Analysis results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
    
    # Show detailed findings
    print(f"\n📋 DETAILED FINDINGS:")
    
    if imports.get('import_loops'):
        print(f"\n🔄 IMPORT LOOPS (first 3):")
        for i, loop in enumerate(imports['import_loops'][:3]):
            print(f"   {i+1}. {loop}")
    
    if isinstance(dead_code, list) and dead_code:
        print(f"\n💀 UNUSED IMPORTS (first 5):")
        for i, unused in enumerate(dead_code[:5]):
            file_path = unused.get('file', 'unknown')
            import_name = unused.get('import', 'unknown')
            print(f"   {i+1}. {file_path}: {import_name}")
    
    if classes.get('inheritance_chains'):
        print(f"\n📦 COMPLEX INHERITANCE CHAINS (first 3):")
        for i, chain in enumerate(classes['inheritance_chains'][:3]):
            if isinstance(chain, dict):
                leaf = chain.get('leaf_class', 'unknown')
                root = chain.get('root_class', 'unknown')
                length = chain.get('length', 0)
                print(f"   {i+1}. {leaf} -> {root} (depth: {length})")
            else:
                print(f"   {i+1}. {chain}")
    
    if ai_analysis.get('insights'):
        print(f"\n🤖 AI INSIGHTS (first 3):")
        for i, insight in enumerate(ai_analysis['insights'][:3]):
            print(f"   {i+1}. {insight}")
    
    if ai_analysis.get('recommendations'):
        print(f"\n🎯 AI RECOMMENDATIONS (first 3):")
        for i, rec in enumerate(ai_analysis['recommendations'][:3]):
            print(f"   {i+1}. {rec}")
    
    print(f"\n🌟 GRAPH-SITTER ANALYSIS COMPLETE!")
    print(f"📊 Full results available in: {output_file}")
    
    return analysis_results

if __name__ == "__main__":
    results = run_comprehensive_graph_sitter_analysis()
    if results:
        print(f"\n🎉 Analysis successful! Check the results above and in the JSON file.")
    else:
        print(f"\n❌ Analysis failed. Please check the error messages above.")

