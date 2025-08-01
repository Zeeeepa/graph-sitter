#!/usr/bin/env python3
"""
Real LSP Error Collection Script

This script actively runs LSP diagnostics on Python files to get actual errors,
not just empty collections.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Set, Any
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def get_python_files_to_analyze():
    """Get a focused list of Python files to analyze for LSP errors."""
    repo_path = Path(__file__).parent
    
    # Focus on core LSP files and some representative files
    target_files = [
        "src/graph_sitter/core/lsp_manager.py",
        "src/graph_sitter/core/lsp_types.py", 
        "src/graph_sitter/core/lsp_type_adapters.py",
        "src/graph_sitter/core/unified_diagnostics.py",
        "src/graph_sitter/extensions/lsp/serena_bridge.py",
        "src/graph_sitter/extensions/lsp/transaction_manager.py",
        "src/graph_sitter/enhanced/codebase.py",
        "src/graph_sitter/codebase/codebase_analysis.py",
        "src/graph_sitter/ai/codebase_ai.py",
        # Add some files that are likely to have issues
        "src/graph_sitter/core/diagnostics.py",
        "src/graph_sitter/core/codebase.py",
        "src/graph_sitter/extensions/lsp/language_servers/python_server.py",
        "src/graph_sitter/extensions/lsp/language_servers/base.py"
    ]
    
    existing_files = []
    for file_path in target_files:
        full_path = repo_path / file_path
        if full_path.exists():
            existing_files.append(str(full_path))
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"📁 Found {len(existing_files)} files to analyze")
    return existing_files

def run_pylsp_diagnostics(file_path: str) -> List[Dict[str, Any]]:
    """Run pylsp (Python LSP Server) diagnostics on a file."""
    diagnostics = []
    
    try:
        import subprocess
        import json
        
        # Try to run pylsp if available
        result = subprocess.run([
            'python', '-m', 'pylsp', '--help'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            print(f"  ⚠️ pylsp not available, trying alternative methods...")
            return run_alternative_diagnostics(file_path)
        
        # Run pylsp diagnostics
        result = subprocess.run([
            'python', '-m', 'pylsp', '--check', file_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.stdout:
            # Parse pylsp output
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    diagnostics.append({
                        'source': 'pylsp',
                        'file': file_path,
                        'message': line.strip(),
                        'severity': 'error' if 'error' in line.lower() else 'warning'
                    })
        
        return diagnostics
        
    except Exception as e:
        print(f"  ❌ Error running pylsp on {file_path}: {e}")
        return run_alternative_diagnostics(file_path)

def run_alternative_diagnostics(file_path: str) -> List[Dict[str, Any]]:
    """Run alternative diagnostic methods when pylsp is not available."""
    diagnostics = []
    
    try:
        # Method 1: Python syntax check
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            diagnostics.append({
                'source': 'python_compile',
                'file': file_path,
                'line': e.lineno,
                'character': e.offset or 0,
                'message': f"SyntaxError: {e.msg}",
                'severity': 'error'
            })
        
        # Method 2: Import analysis
        import_errors = check_import_errors(file_path, content)
        diagnostics.extend(import_errors)
        
        # Method 3: Basic static analysis
        static_issues = run_basic_static_analysis(file_path, content)
        diagnostics.extend(static_issues)
        
        return diagnostics
        
    except Exception as e:
        print(f"  ❌ Error in alternative diagnostics for {file_path}: {e}")
        return []

def check_import_errors(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for import-related errors."""
    import_errors = []
    
    try:
        import ast
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    # Try to resolve the import
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            try:
                                __import__(alias.name)
                            except ImportError as e:
                                import_errors.append({
                                    'source': 'import_check',
                                    'file': file_path,
                                    'line': node.lineno,
                                    'character': node.col_offset,
                                    'message': f"ImportError: {e}",
                                    'severity': 'error'
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            try:
                                module = __import__(node.module)
                                for alias in node.names:
                                    if not hasattr(module, alias.name):
                                        import_errors.append({
                                            'source': 'import_check',
                                            'file': file_path,
                                            'line': node.lineno,
                                            'character': node.col_offset,
                                            'message': f"ImportError: cannot import name '{alias.name}' from '{node.module}'",
                                            'severity': 'error'
                                        })
                            except ImportError as e:
                                import_errors.append({
                                    'source': 'import_check',
                                    'file': file_path,
                                    'line': node.lineno,
                                    'character': node.col_offset,
                                    'message': f"ImportError: {e}",
                                    'severity': 'error'
                                })
                except Exception:
                    # Skip import errors that are too complex to analyze
                    pass
        
        return import_errors
        
    except Exception as e:
        print(f"  ⚠️ Error checking imports in {file_path}: {e}")
        return []

def run_basic_static_analysis(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Run basic static analysis to find common issues."""
    issues = []
    
    try:
        import ast
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # Check for undefined variables (basic check)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                # This is a very basic check - in practice, this would need scope analysis
                pass
            
            # Check for unused imports (basic check)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if content.count(name) == 1:  # Only appears in import
                        issues.append({
                            'source': 'static_analysis',
                            'file': file_path,
                            'line': node.lineno,
                            'character': node.col_offset,
                            'message': f"Unused import: {name}",
                            'severity': 'warning'
                        })
        
        return issues
        
    except Exception as e:
        print(f"  ⚠️ Error in static analysis for {file_path}: {e}")
        return []

def run_serena_lsp_diagnostics():
    """Run diagnostics using our Serena LSP system."""
    print("\n🚨 Running Serena LSP Diagnostics...")
    serena_errors = []
    
    try:
        from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
        from graph_sitter.core.lsp_manager import LSPManager
        
        repo_path = str(Path(__file__).parent)
        
        # Initialize SerenaLSPBridge
        print("  🔧 Initializing SerenaLSPBridge...")
        bridge = SerenaLSPBridge(repo_path)
        
        if bridge.is_initialized:
            print(f"  ✅ SerenaLSPBridge initialized with {len(bridge.language_servers)} servers")
            
            # Get diagnostics for specific files
            files_to_check = get_python_files_to_analyze()
            
            for file_path in files_to_check[:5]:  # Check first 5 files
                print(f"  🔍 Checking {Path(file_path).name}...")
                try:
                    file_diagnostics = bridge.get_file_diagnostics(file_path)
                    print(f"    📊 Found {len(file_diagnostics)} diagnostics")
                    
                    for diag in file_diagnostics:
                        serena_errors.append({
                            'source': 'SerenaLSPBridge',
                            'file': file_path,
                            'line': getattr(diag, 'line', 'unknown'),
                            'character': getattr(diag, 'character', 'unknown'),
                            'message': diag.message,
                            'severity': str(diag.severity),
                            'error_type': str(getattr(diag, 'error_type', 'unknown'))
                        })
                except Exception as e:
                    print(f"    ❌ Error getting diagnostics for {file_path}: {e}")
            
            # Also try getting all diagnostics
            try:
                all_diagnostics = bridge.get_all_diagnostics()
                print(f"  📊 Total diagnostics from get_all_diagnostics(): {len(all_diagnostics)}")
                
                for diag in all_diagnostics:
                    if diag not in serena_errors:  # Avoid duplicates
                        serena_errors.append({
                            'source': 'SerenaLSPBridge_all',
                            'file': getattr(diag, 'file_path', 'unknown'),
                            'line': getattr(diag, 'line', 'unknown'),
                            'character': getattr(diag, 'character', 'unknown'),
                            'message': diag.message,
                            'severity': str(diag.severity),
                            'error_type': str(getattr(diag, 'error_type', 'unknown'))
                        })
            except Exception as e:
                print(f"  ❌ Error getting all diagnostics: {e}")
        else:
            print("  ⚠️ SerenaLSPBridge not initialized")
        
        # Try LSPManager
        print("  🔧 Trying LSPManager...")
        try:
            manager = LSPManager(repo_path)
            all_errors = manager.get_all_errors()
            print(f"  📊 LSPManager found {all_errors.total_count} errors")
            
            for error in all_errors.errors:
                serena_errors.append({
                    'source': 'LSPManager',
                    'file': error.file_path,
                    'line': error.range.start.line if hasattr(error, 'range') else 'unknown',
                    'character': error.range.start.character if hasattr(error, 'range') else 'unknown',
                    'message': error.message,
                    'severity': str(error.severity),
                    'error_type': str(error.error_type)
                })
        except Exception as e:
            print(f"  ❌ LSPManager error: {e}")
        
        return serena_errors
        
    except Exception as e:
        print(f"❌ Error running Serena LSP diagnostics: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main function to collect real LSP errors."""
    print("🚀 Collecting Real LSP/Serena Errors")
    print("=" * 60)
    
    all_errors = []
    
    # Get files to analyze
    files_to_analyze = get_python_files_to_analyze()
    
    # Method 1: Run Serena LSP diagnostics
    serena_errors = run_serena_lsp_diagnostics()
    all_errors.extend(serena_errors)
    
    # Method 2: Run alternative diagnostics on each file
    print(f"\n🔍 Running alternative diagnostics on {len(files_to_analyze)} files...")
    
    for i, file_path in enumerate(files_to_analyze[:10]):  # Limit to first 10 files
        print(f"\n📁 Analyzing {Path(file_path).name} ({i+1}/{min(10, len(files_to_analyze))})...")
        
        # Run alternative diagnostics
        file_errors = run_alternative_diagnostics(file_path)
        all_errors.extend(file_errors)
        
        print(f"  📊 Found {len(file_errors)} issues")
    
    # Generate report
    print("\n" + "="*80)
    print("📋 REAL LSP ERROR ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📊 SUMMARY")
    print("-" * 40)
    print(f"• Total errors found: {len(all_errors)}")
    print(f"• Files analyzed: {len(files_to_analyze)}")
    
    # Group by source
    by_source = {}
    for error in all_errors:
        source = error.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(error)
    
    print(f"\n🔍 ERRORS BY SOURCE")
    print("-" * 40)
    for source, errors in by_source.items():
        print(f"• {source}: {len(errors)} errors")
    
    # Group by severity
    by_severity = {}
    for error in all_errors:
        severity = error.get('severity', 'unknown')
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(error)
    
    print(f"\n⚠️ ERRORS BY SEVERITY")
    print("-" * 40)
    for severity, errors in by_severity.items():
        print(f"• {severity}: {len(errors)} errors")
    
    # Show sample errors
    if all_errors:
        print(f"\n🚨 SAMPLE ERRORS (first 10)")
        print("-" * 40)
        for i, error in enumerate(all_errors[:10]):
            file_name = Path(error.get('file', 'unknown')).name
            line = error.get('line', 'unknown')
            message = error.get('message', 'No message')[:80]
            severity = error.get('severity', 'unknown')
            print(f"{i+1:2d}. [{severity.upper()}] {file_name}:{line} - {message}")
    
    # Save detailed results
    try:
        with open("real_lsp_errors.json", 'w') as f:
            json.dump(all_errors, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: real_lsp_errors.json")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    print("\n" + "="*80)
    print("✅ Real LSP error collection complete!")
    print("="*80)
    
    return all_errors

if __name__ == "__main__":
    main()
