#!/usr/bin/env python3
"""
Complete Serena System Analysis

This script analyzes all the specified codefiles including the complete Serena extension
directory to understand the full implementation and find consolidation opportunities.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Set, Any
import json
import ast

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def get_all_target_files():
    """Get all target files for analysis including the complete Serena directory."""
    repo_path = Path(__file__).parent
    
    # Specific files requested
    specific_files = [
        "src/graph_sitter/analysis/deep_analysis.py",
        "src/graph_sitter/extensions/serena/generation/code_generator.py",
        "src/graph_sitter/enhanced/codebase.py",
        "src/graph_sitter/core/diagnostics.py",
        "src/graph_sitter/ai/codebase_ai.py",
        "src/graph_sitter/codebase/codebase_analysis.py",
        "src/graph_sitter/codebase/codebase_ai.py",
        "src/graph_sitter/codebase/__init__.py",
        "src/graph_sitter/extensions/lsp/transaction_manager.py",
        "src/graph_sitter/extensions/lsp/serena_bridge.py",
        "src/graph_sitter/extensions/lsp/protocol/lsp_types.py",
        "src/graph_sitter/extensions/lsp/protocol/lsp_constants.py",
        "src/graph_sitter/extensions/lsp/language_servers/python_server.py",
        "src/graph_sitter/extensions/lsp/language_servers/base.py"
    ]
    
    # Find all files in the Serena extension directory
    serena_dir = repo_path / "src/graph_sitter/extensions/serena"
    serena_files = []
    
    if serena_dir.exists():
        print(f"🔍 Scanning Serena directory: {serena_dir}")
        for py_file in serena_dir.rglob("*.py"):
            relative_path = py_file.relative_to(repo_path)
            serena_files.append(str(relative_path))
        print(f"📁 Found {len(serena_files)} Python files in Serena directory")
    else:
        print(f"⚠️ Serena directory not found: {serena_dir}")
    
    # Combine all files
    all_files = specific_files + serena_files
    
    # Check which files exist
    existing_files = []
    missing_files = []
    
    for file_path in all_files:
        full_path = repo_path / file_path
        if full_path.exists():
            existing_files.append(str(full_path))
        else:
            missing_files.append(file_path)
    
    print(f"\n📊 File Analysis Summary:")
    print(f"• Total files requested: {len(all_files)}")
    print(f"• Files found: {len(existing_files)}")
    print(f"• Files missing: {len(missing_files)}")
    
    if missing_files:
        print(f"\n⚠️ Missing files:")
        for missing in missing_files:
            print(f"  • {missing}")
    
    return existing_files, serena_files

def analyze_file_structure(file_path: str) -> Dict[str, Any]:
    """Analyze the structure of a Python file."""
    analysis = {
        'file_path': file_path,
        'file_name': Path(file_path).name,
        'functions': [],
        'classes': [],
        'imports': [],
        'constants': [],
        'decorators': [],
        'docstring': None,
        'lines_of_code': 0,
        'complexity_score': 0,
        'issues': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis['lines_of_code'] = len(content.splitlines())
        
        # Parse AST
        tree = ast.parse(content)
        
        # Get module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            analysis['docstring'] = tree.body[0].value.value
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'docstring': ast.get_docstring(node),
                    'returns': ast.unparse(node.returns) if node.returns else None
                }
                analysis['functions'].append(func_info)
                
                # Add to decorators list
                for dec in node.decorator_list:
                    dec_name = ast.unparse(dec)
                    if dec_name not in analysis['decorators']:
                        analysis['decorators'].append(dec_name)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [ast.unparse(base) for base in node.bases],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list],
                    'methods': [],
                    'docstring': ast.get_docstring(node)
                }
                
                # Get methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'is_property': any('property' in ast.unparse(dec) for dec in item.decorator_list),
                            'is_static': any('staticmethod' in ast.unparse(dec) for dec in item.decorator_list),
                            'is_class': any('classmethod' in ast.unparse(dec) for dec in item.decorator_list)
                        }
                        class_info['methods'].append(method_info)
                
                analysis['classes'].append(class_info)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                else:  # ImportFrom
                    for alias in node.names:
                        analysis['imports'].append({
                            'type': 'from_import',
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
            
            elif isinstance(node, ast.Assign):
                # Look for constants (uppercase variables)
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        analysis['constants'].append({
                            'name': target.id,
                            'line': node.lineno,
                            'value': ast.unparse(node.value)[:100]  # Truncate long values
                        })
        
        # Calculate complexity score (simple heuristic)
        analysis['complexity_score'] = (
            len(analysis['functions']) * 2 +
            len(analysis['classes']) * 3 +
            sum(len(cls['methods']) for cls in analysis['classes']) +
            len(analysis['imports'])
        )
        
        return analysis
        
    except Exception as e:
        analysis['issues'].append(f"Analysis error: {e}")
        return analysis

def find_serena_patterns(file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find patterns specific to Serena implementation."""
    patterns = {
        'serena_classes': [],
        'serena_functions': [],
        'ai_integration_points': [],
        'lsp_integration_points': [],
        'code_generation_features': [],
        'analysis_features': [],
        'common_imports': {},
        'decorator_patterns': {},
        'naming_conventions': {}
    }
    
    # Analyze each file for Serena-specific patterns
    for analysis in file_analyses:
        file_name = analysis['file_name']
        
        # Look for Serena-specific classes
        for cls in analysis['classes']:
            if any(keyword in cls['name'].lower() for keyword in ['serena', 'ai', 'generation', 'analysis']):
                patterns['serena_classes'].append({
                    'file': file_name,
                    'class': cls['name'],
                    'methods': len(cls['methods']),
                    'bases': cls['bases']
                })
        
        # Look for Serena-specific functions
        for func in analysis['functions']:
            if any(keyword in func['name'].lower() for keyword in ['generate', 'analyze', 'ai', 'serena', 'completion']):
                patterns['serena_functions'].append({
                    'file': file_name,
                    'function': func['name'],
                    'args': len(func['args']),
                    'decorators': func['decorators']
                })
        
        # Look for AI integration points
        ai_keywords = ['openai', 'anthropic', 'llm', 'model', 'prompt', 'completion']
        for imp in analysis['imports']:
            module_name = imp.get('module', '').lower()
            if any(keyword in module_name for keyword in ai_keywords):
                patterns['ai_integration_points'].append({
                    'file': file_name,
                    'import': imp
                })
        
        # Look for LSP integration points
        lsp_keywords = ['lsp', 'language_server', 'diagnostic', 'completion', 'hover']
        for imp in analysis['imports']:
            module_name = imp.get('module', '').lower()
            if any(keyword in module_name for keyword in lsp_keywords):
                patterns['lsp_integration_points'].append({
                    'file': file_name,
                    'import': imp
                })
        
        # Count common imports
        for imp in analysis['imports']:
            module = imp.get('module', 'unknown')
            if module not in patterns['common_imports']:
                patterns['common_imports'][module] = 0
            patterns['common_imports'][module] += 1
        
        # Count decorator patterns
        for decorator in analysis['decorators']:
            if decorator not in patterns['decorator_patterns']:
                patterns['decorator_patterns'][decorator] = 0
            patterns['decorator_patterns'][decorator] += 1
    
    return patterns

def analyze_consolidation_opportunities(file_analyses: List[Dict[str, Any]], patterns: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze opportunities for code consolidation."""
    opportunities = {
        'duplicate_functions': [],
        'similar_classes': [],
        'redundant_imports': [],
        'consolidation_candidates': [],
        'architectural_issues': []
    }
    
    # Find duplicate function names
    function_names = {}
    for analysis in file_analyses:
        for func in analysis['functions']:
            name = func['name']
            if name not in function_names:
                function_names[name] = []
            function_names[name].append({
                'file': analysis['file_name'],
                'line': func['line'],
                'args': func['args']
            })
    
    # Identify duplicates
    for name, occurrences in function_names.items():
        if len(occurrences) > 1:
            opportunities['duplicate_functions'].append({
                'function_name': name,
                'occurrences': occurrences,
                'count': len(occurrences)
            })
    
    # Find similar classes
    class_names = {}
    for analysis in file_analyses:
        for cls in analysis['classes']:
            name = cls['name']
            if name not in class_names:
                class_names[name] = []
            class_names[name].append({
                'file': analysis['file_name'],
                'line': cls['line'],
                'methods': len(cls['methods']),
                'bases': cls['bases']
            })
    
    for name, occurrences in class_names.items():
        if len(occurrences) > 1:
            opportunities['similar_classes'].append({
                'class_name': name,
                'occurrences': occurrences,
                'count': len(occurrences)
            })
    
    # Find redundant imports
    import_usage = {}
    for analysis in file_analyses:
        file_imports = {}
        for imp in analysis['imports']:
            module = imp.get('module', 'unknown')
            if module not in file_imports:
                file_imports[module] = 0
            file_imports[module] += 1
        
        for module, count in file_imports.items():
            if module not in import_usage:
                import_usage[module] = []
            import_usage[module].append({
                'file': analysis['file_name'],
                'count': count
            })
    
    # Identify consolidation candidates
    for analysis in file_analyses:
        file_name = analysis['file_name']
        
        # Files with high complexity might need refactoring
        if analysis['complexity_score'] > 50:
            opportunities['consolidation_candidates'].append({
                'file': file_name,
                'reason': 'High complexity',
                'complexity_score': analysis['complexity_score'],
                'functions': len(analysis['functions']),
                'classes': len(analysis['classes'])
            })
        
        # Files with many imports might have too many dependencies
        if len(analysis['imports']) > 20:
            opportunities['consolidation_candidates'].append({
                'file': file_name,
                'reason': 'Too many imports',
                'import_count': len(analysis['imports'])
            })
    
    return opportunities

def generate_comprehensive_report(file_analyses: List[Dict[str, Any]], patterns: Dict[str, Any], opportunities: Dict[str, Any], serena_files: List[str]):
    """Generate a comprehensive analysis report."""
    print("\n" + "="*100)
    print("📋 COMPLETE SERENA SYSTEM ANALYSIS REPORT")
    print("="*100)
    
    # Summary statistics
    total_files = len(file_analyses)
    total_functions = sum(len(analysis['functions']) for analysis in file_analyses)
    total_classes = sum(len(analysis['classes']) for analysis in file_analyses)
    total_lines = sum(analysis['lines_of_code'] for analysis in file_analyses)
    serena_file_count = len(serena_files)
    
    print(f"\n📊 SYSTEM OVERVIEW")
    print("-" * 50)
    print(f"• Total files analyzed: {total_files}")
    print(f"• Serena extension files: {serena_file_count}")
    print(f"• Total functions: {total_functions}")
    print(f"• Total classes: {total_classes}")
    print(f"• Total lines of code: {total_lines:,}")
    
    # Serena-specific analysis
    print(f"\n🤖 SERENA IMPLEMENTATION ANALYSIS")
    print("-" * 50)
    print(f"• Serena-specific classes: {len(patterns['serena_classes'])}")
    print(f"• Serena-specific functions: {len(patterns['serena_functions'])}")
    print(f"• AI integration points: {len(patterns['ai_integration_points'])}")
    print(f"• LSP integration points: {len(patterns['lsp_integration_points'])}")
    
    # Show key Serena classes
    if patterns['serena_classes']:
        print(f"\n🏗️ KEY SERENA CLASSES:")
        for cls in patterns['serena_classes'][:10]:  # Show top 10
            print(f"  • {cls['class']} ({cls['file']}) - {cls['methods']} methods")
    
    # Show key Serena functions
    if patterns['serena_functions']:
        print(f"\n⚙️ KEY SERENA FUNCTIONS:")
        for func in patterns['serena_functions'][:10]:  # Show top 10
            print(f"  • {func['function']} ({func['file']}) - {func['args']} args")
    
    # File complexity analysis
    print(f"\n📈 COMPLEXITY ANALYSIS")
    print("-" * 50)
    
    # Sort by complexity
    sorted_files = sorted(file_analyses, key=lambda x: x['complexity_score'], reverse=True)
    
    print(f"🔥 MOST COMPLEX FILES:")
    for analysis in sorted_files[:10]:
        print(f"  • {analysis['file_name']}: {analysis['complexity_score']} "
              f"({analysis['lines_of_code']} lines, {len(analysis['functions'])} funcs, {len(analysis['classes'])} classes)")
    
    # Consolidation opportunities
    print(f"\n🔄 CONSOLIDATION OPPORTUNITIES")
    print("-" * 50)
    
    duplicate_funcs = opportunities['duplicate_functions']
    similar_classes = opportunities['similar_classes']
    candidates = opportunities['consolidation_candidates']
    
    print(f"• Duplicate functions: {len(duplicate_funcs)}")
    print(f"• Similar classes: {len(similar_classes)}")
    print(f"• Consolidation candidates: {len(candidates)}")
    
    if duplicate_funcs:
        print(f"\n🔄 DUPLICATE FUNCTIONS (top 10):")
        for dup in duplicate_funcs[:10]:
            print(f"  • {dup['function_name']}: {dup['count']} occurrences")
            for occ in dup['occurrences'][:3]:  # Show first 3 occurrences
                print(f"    - {occ['file']}:{occ['line']}")
    
    if similar_classes:
        print(f"\n🏗️ SIMILAR CLASSES:")
        for sim in similar_classes[:5]:
            print(f"  • {sim['class_name']}: {sim['count']} occurrences")
    
    # Import analysis
    print(f"\n📦 IMPORT ANALYSIS")
    print("-" * 50)
    
    common_imports = sorted(patterns['common_imports'].items(), key=lambda x: x[1], reverse=True)
    print(f"🔗 MOST COMMON IMPORTS (top 15):")
    for module, count in common_imports[:15]:
        print(f"  • {module}: {count} files")
    
    # Architectural recommendations
    print(f"\n💡 ARCHITECTURAL RECOMMENDATIONS")
    print("-" * 50)
    
    recommendations = []
    
    # Based on duplicate functions
    if len(duplicate_funcs) > 5:
        recommendations.append(f"🔄 Consolidate {len(duplicate_funcs)} duplicate functions into shared utilities")
    
    # Based on complexity
    high_complexity_files = [f for f in sorted_files if f['complexity_score'] > 50]
    if high_complexity_files:
        recommendations.append(f"📊 Refactor {len(high_complexity_files)} high-complexity files")
    
    # Based on Serena structure
    if serena_file_count > 10:
        recommendations.append(f"🤖 Consider organizing {serena_file_count} Serena files into clearer modules")
    
    # Based on imports
    if len(common_imports) > 50:
        recommendations.append(f"📦 Review import structure - {len(common_imports)} different modules imported")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i:2d}. {rec}")
    
    print(f"\n🎯 PRIORITY ACTIONS")
    print("-" * 50)
    print("1. 🔥 Focus on highest complexity files first")
    print("2. 🔄 Consolidate duplicate utility functions")
    print("3. 🤖 Organize Serena extension structure")
    print("4. 📦 Standardize import patterns")
    print("5. 🏗️ Create clear architectural boundaries")
    
    print("\n" + "="*100)
    print("✅ Complete Serena system analysis finished!")
    print("="*100)

def main():
    """Main analysis function."""
    print("🚀 Complete Serena System Analysis")
    print("=" * 80)
    
    # Get all target files
    existing_files, serena_files = get_all_target_files()
    
    if not existing_files:
        print("❌ No files found to analyze!")
        return
    
    # Analyze each file
    print(f"\n🔍 Analyzing {len(existing_files)} files...")
    file_analyses = []
    
    for i, file_path in enumerate(existing_files):
        file_name = Path(file_path).name
        print(f"📁 Analyzing {file_name} ({i+1}/{len(existing_files)})...")
        
        analysis = analyze_file_structure(file_path)
        file_analyses.append(analysis)
    
    # Find Serena patterns
    print(f"\n🤖 Analyzing Serena-specific patterns...")
    patterns = find_serena_patterns(file_analyses)
    
    # Find consolidation opportunities
    print(f"\n🔄 Analyzing consolidation opportunities...")
    opportunities = analyze_consolidation_opportunities(file_analyses, patterns)
    
    # Generate comprehensive report
    generate_comprehensive_report(file_analyses, patterns, opportunities, serena_files)
    
    # Save detailed results
    results = {
        'file_analyses': file_analyses,
        'serena_patterns': patterns,
        'consolidation_opportunities': opportunities,
        'summary': {
            'total_files': len(file_analyses),
            'serena_files': len(serena_files),
            'total_functions': sum(len(analysis['functions']) for analysis in file_analyses),
            'total_classes': sum(len(analysis['classes']) for analysis in file_analyses),
            'total_lines': sum(analysis['lines_of_code'] for analysis in file_analyses)
        }
    }
    
    try:
        with open("complete_serena_analysis.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: complete_serena_analysis.json")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    print(f"\n🎉 Complete Serena system analysis finished!")

if __name__ == "__main__":
    main()
