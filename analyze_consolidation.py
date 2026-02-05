#!/usr/bin/env python3
"""
Self-Analysis Script: Use Graph-Sitter to analyze its own codebase
for consolidation planning.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_sitter import Codebase

def analyze_files():
    """Use Graph-Sitter to analyze the 6 analysis files."""
    
    print("=" * 80)
    print("STEP 2: Using Graph-Sitter to Extract Symbol Information")
    print("=" * 80)
    
    # Initialize codebase
    codebase = Codebase("./")
    
    # Files to analyze
    target_files = [
        "src/graph_sitter_analysis.py",
        "src/graph_sitter_backend.py",
        "src/lsp_diagnostics.py",
        "src/autogenlib_adapter.py",
        "src/analysisbig.py",
        "src/analysis.py"
    ]
    
    analysis_results = {}
    
    for filepath in target_files:
        print(f"\n📁 Analyzing: {filepath}")
        print("-" * 80)
        
        try:
            # Get the file
            file = codebase.get_file(filepath)
            if not file:
                print(f"  ⚠️  File not found: {filepath}")
                continue
            
            file_analysis = {
                "filepath": filepath,
                "classes": [],
                "functions": [],
                "imports": [],
                "total_symbols": 0
            }
            
            # Extract classes
            for symbol in codebase.symbols:
                if hasattr(symbol, 'filepath') and symbol.filepath == filepath:
                    if symbol.__class__.__name__ in ['PyClass', 'Class']:
                        file_analysis["classes"].append({
                            "name": symbol.name,
                            "type": symbol.__class__.__name__,
                            "docstring": symbol.docstring[:100] if symbol.docstring else None
                        })
                    elif symbol.__class__.__name__ in ['PyFunction', 'Function']:
                        file_analysis["functions"].append({
                            "name": symbol.name,
                            "type": symbol.__class__.__name__,
                            "docstring": symbol.docstring[:100] if symbol.docstring else None
                        })
            
            file_analysis["total_symbols"] = len(file_analysis["classes"]) + len(file_analysis["functions"])
            
            # Print summary
            print(f"  📊 Classes: {len(file_analysis['classes'])}")
            print(f"  📊 Functions: {len(file_analysis['functions'])}")
            print(f"  📊 Total Symbols: {file_analysis['total_symbols']}")
            
            if file_analysis['classes']:
                print(f"\n  Top Classes:")
                for cls in file_analysis['classes'][:5]:
                    print(f"    - {cls['name']}")
            
            if file_analysis['functions']:
                print(f"\n  Top Functions:")
                for func in file_analysis['functions'][:10]:
                    print(f"    - {func['name']}")
            
            analysis_results[filepath] = file_analysis
            
        except Exception as e:
            print(f"  ❌ Error analyzing {filepath}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results
    output_file = "analysis_step2_symbols.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\n✅ Symbol analysis saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_classes = sum(len(r['classes']) for r in analysis_results.values())
    total_functions = sum(len(r['functions']) for r in analysis_results.values())
    print(f"Total Classes: {total_classes}")
    print(f"Total Functions: {total_functions}")
    print(f"Total Symbols: {total_classes + total_functions}")
    
    return analysis_results

if __name__ == "__main__":
    analyze_files()

