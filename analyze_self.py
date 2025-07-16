#!/usr/bin/env python3
"""
Self-analysis script for graph-sitter codebase
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter import Codebase
    
    print("🔍 Analyzing graph-sitter codebase...")
    print("=" * 50)
    
    # Initialize codebase
    codebase = Codebase("./")
    
    print(f"✅ Codebase initialized: {codebase.name}")
    print(f"📁 Repository path: {codebase.repo_path}")
    print(f"🔧 Language: {codebase.language}")
    print(f"📄 Total files: {len(codebase.files)}")
    
    # Analyze file types
    file_types = {}
    for file in codebase.files:
        ext = file.path.suffix
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print("\n📊 File type distribution:")
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {ext or '(no extension)'}: {count}")
    
    # Look for Python files with potential issues
    python_files = [f for f in codebase.files if f.path.suffix == '.py']
    print(f"\n🐍 Python files: {len(python_files)}")
    
    # Check for common patterns that might indicate issues
    issues_found = []
    
    for file in python_files[:20]:  # Check first 20 Python files
        try:
            content = file.content
            if content:
                # Check for TODO/FIXME comments
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if any(keyword in line.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
                        issues_found.append(f"{file.path}:{i} - {line.strip()}")
                    
                    # Check for potential import issues
                    if 'import' in line and ('graph_sitter_sdk_pink' in line or 'codegen_sdk_pink' in line):
                        issues_found.append(f"{file.path}:{i} - Potential pink SDK import: {line.strip()}")
        except Exception as e:
            issues_found.append(f"{file.path} - Error reading file: {e}")
    
    if issues_found:
        print(f"\n⚠️  Potential issues found ({len(issues_found)}):")
        for issue in issues_found[:10]:  # Show first 10 issues
            print(f"  {issue}")
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more")
    else:
        print("\n✅ No obvious issues found in analyzed files")
    
    # Check for specific patterns
    print(f"\n🔍 Checking for specific patterns...")
    
    # Look for pink SDK usage
    pink_usage = []
    for file in python_files:
        try:
            content = file.content
            if content and ('pink' in content.lower() or 'codegen_sdk_pink' in content or 'graph_sitter_sdk_pink' in content):
                pink_usage.append(str(file.path))
        except:
            pass
    
    if pink_usage:
        print(f"📦 Files using pink SDK: {len(pink_usage)}")
        for file in pink_usage[:5]:
            print(f"  {file}")
    
    print(f"\n✅ Analysis complete!")
    
except Exception as e:
    print(f"❌ Error during analysis: {e}")
    import traceback
    traceback.print_exc()
