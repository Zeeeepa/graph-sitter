#!/usr/bin/env python3
"""
Simple Analysis: Use AST to analyze the files for consolidation planning.
"""

import ast
import json
from pathlib import Path
from collections import defaultdict

def extract_symbols(filepath):
    """Extract classes, functions, and imports from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        result = {
            "filepath": str(filepath),
            "classes": [],
            "functions": [],
            "imports": [],
            "total_lines": 0
        }
        
        # Count lines
        with open(filepath, 'r', encoding='utf-8') as f:
            result["total_lines"] = len(f.readlines())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                result["classes"].append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    "docstring": docstring[:100] if docstring else None
                })
            
            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                parent = None
                for n in ast.walk(tree):
                    if isinstance(n, ast.ClassDef) and node in n.body:
                        parent = n
                        break
                
                if parent is None:
                    docstring = ast.get_docstring(node)
                    result["functions"].append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": docstring[:100] if docstring else None
                    })
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname
                        })
                else:
                    module = node.module if node.module else ""
                    for alias in node.names:
                        result["imports"].append({
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname
                        })
        
        return result
        
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None

def analyze_tool_files():
    """Analyze the 8 tool files."""
    tool_dir = Path("src/graph_sitter/extensions/tools")
    target_tools = [
        "reveal_symbol_fn.py",
        "reveal_symbol.py",
        "mdx_docs_generation.py",
        "list_directory.py",
        "generate_docs_json.py",
        "document_functions.py",
        "current_code_codebase.py",
        "codegen_sdk_codebase.py"
    ]
    
    results = {}
    for tool in target_tools:
        filepath = tool_dir / tool
        if filepath.exists():
            results[str(filepath)] = extract_symbols(filepath)
    
    return results

def main():
    print("=" * 80)
    print("STEP 1-2: File Analysis Using AST")
    print("=" * 80)
    
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
    
    print("\n📊 Analyzing 6 Analysis Files:")
    print("-" * 80)
    
    for filepath in target_files:
        path = Path(filepath)
        if path.exists():
            print(f"\n📁 {filepath}")
            result = extract_symbols(path)
            if result:
                analysis_results[filepath] = result
                print(f"  Lines: {result['total_lines']}")
                print(f"  Classes: {len(result['classes'])}")
                print(f"  Functions: {len(result['functions'])}")
                print(f"  Imports: {len(result['imports'])}")
                
                if result['classes']:
                    print(f"  Top Classes: {', '.join([c['name'] for c in result['classes'][:5]])}")
                if result['functions']:
                    print(f"  Top Functions: {', '.join([f['name'] for f in result['functions'][:5]])}")
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print("\n\n📊 Analyzing 8 Tool Files:")
    print("-" * 80)
    
    tool_results = analyze_tool_files()
    for filepath, result in tool_results.items():
        if result:
            print(f"\n📁 {filepath}")
            print(f"  Lines: {result['total_lines']}")
            print(f"  Classes: {len(result['classes'])}")
            print(f"  Functions: {len(result['functions'])}")
            print(f"  Top Functions: {', '.join([f['name'] for f in result['functions'][:3]])}")
    
    # Combine results
    all_results = {
        "analysis_files": analysis_results,
        "tool_files": tool_results
    }
    
    # Save results
    output_file = "analysis_step1-2_complete.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\n✅ Complete analysis saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_lines = sum(r['total_lines'] for r in analysis_results.values())
    total_classes = sum(len(r['classes']) for r in analysis_results.values())
    total_functions = sum(len(r['functions']) for r in analysis_results.values())
    
    print(f"Analysis Files:")
    print(f"  Total Lines: {total_lines:,}")
    print(f"  Total Classes: {total_classes}")
    print(f"  Total Functions: {total_functions}")
    print(f"  Total Symbols: {total_classes + total_functions}")
    
    tool_lines = sum(r['total_lines'] for r in tool_results.values())
    tool_functions = sum(len(r['functions']) for r in tool_results.values())
    
    print(f"\nTool Files:")
    print(f"  Total Lines: {tool_lines:,}")
    print(f"  Total Functions: {tool_functions}")
    
    return all_results

if __name__ == "__main__":
    main()

