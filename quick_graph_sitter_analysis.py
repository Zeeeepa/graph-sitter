#!/usr/bin/env python3
"""
⚡ QUICK GRAPH-SITTER ANALYSIS ⚡

Fast analysis using graph-sitter features to find code errors and insights.
"""

import time
from datetime import datetime

def run_quick_analysis():
    """Run quick graph-sitter analysis."""
    
    print("⚡ QUICK GRAPH-SITTER ANALYSIS")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Import and create codebase
        from graph_sitter import Codebase
        print("📊 Loading codebase...")
        codebase = Codebase('.')
        
        print(f"✅ Loaded: {len(codebase.files)} files, {len(codebase.functions)} functions")
        
        # Quick import analysis
        from src.graph_sitter.adapters.analysis.import_analysis import analyze_import_relationships
        print("🔄 Analyzing imports...")
        import_result = analyze_import_relationships(codebase)
        
        # Quick dead code check
        from src.graph_sitter.adapters.analysis.dead_code_detection import analyze_unused_imports
        print("💀 Checking for unused imports...")
        dead_code = analyze_unused_imports(codebase)
        
        end_time = time.time()
        
        print(f"\n✅ ANALYSIS COMPLETE ({end_time - start_time:.1f}s)")
        print("=" * 50)
        
        # Results
        print(f"📁 Files: {len(codebase.files)}")
        print(f"🔧 Functions: {len(codebase.functions)}")
        print(f"📦 Classes: {len(codebase.classes)}")
        print(f"📝 Symbols: {len(codebase.symbols)}")
        print(f"📊 Imports: {import_result.get('total_imports', 0)}")
        print(f"🔄 Import loops: {len(import_result.get('import_loops', []))}")
        print(f"💀 Unused imports: {len(dead_code)}")
        
        # Show errors if found
        if import_result.get('import_loops'):
            print(f"\n⚠️  IMPORT LOOPS DETECTED:")
            for i, loop in enumerate(import_result['import_loops'][:3]):
                print(f"  {i+1}. {loop}")
        
        if dead_code:
            print(f"\n💀 UNUSED IMPORTS DETECTED:")
            for i, unused in enumerate(dead_code[:5]):
                file_path = unused.get('file', 'unknown')
                import_name = unused.get('import', 'unknown')
                print(f"  {i+1}. {file_path}: {import_name}")
        
        if not import_result.get('import_loops') and not dead_code:
            print(f"\n🎉 No critical issues found!")
        
        # Show some interesting stats
        print(f"\n📊 CODEBASE INSIGHTS:")
        print(f"  🏗️  Architecture: Large-scale Python project")
        print(f"  🔗 Dependencies: {import_result.get('total_imports', 0)} import statements")
        print(f"  📈 Complexity: {len(codebase.functions)} functions across {len(codebase.files)} files")
        print(f"  🎯 Quality: {'Good' if not dead_code else 'Needs cleanup'}")
        
        return {
            'files': len(codebase.files),
            'functions': len(codebase.functions),
            'classes': len(codebase.classes),
            'symbols': len(codebase.symbols),
            'imports': import_result.get('total_imports', 0),
            'import_loops': len(import_result.get('import_loops', [])),
            'unused_imports': len(dead_code),
            'analysis_time': end_time - start_time
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

if __name__ == "__main__":
    result = run_quick_analysis()
    if result:
        print(f"\n🚀 Graph-sitter analysis completed successfully!")
        print(f"📊 Use the full launcher for detailed analysis.")
    else:
        print(f"\n❌ Analysis failed.")

