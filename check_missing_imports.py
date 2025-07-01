#!/usr/bin/env python3
"""
Check for missing imports in langchain/tools.py
"""

import os
import re
from pathlib import Path

def get_tools_in_directory():
    """Get all tool files in agents/tools directory."""
    tools_dir = Path("src/contexten/agents/tools")
    tool_files = []
    
    for file_path in tools_dir.rglob("*.py"):
        if file_path.name != "__init__.py":
            relative_path = file_path.relative_to(Path("src/contexten/agents"))
            tool_files.append(str(relative_path))
    
    return sorted(tool_files)

def get_imports_in_langchain_tools():
    """Get all imports from langchain/tools.py."""
    tools_file = "src/contexten/agents/langchain/tools.py"
    
    if not os.path.exists(tools_file):
        return []
    
    with open(tools_file, 'r') as f:
        content = f.read()
    
    # Find imports from contexten.agents.tools
    imports = []
    
    # Pattern for: from contexten.agents.tools.xxx import yyy
    pattern1 = r'from contexten\.agents\.tools\.([^\s]+) import'
    matches1 = re.findall(pattern1, content)
    imports.extend([f"tools/{match.replace('.', '/')}.py" for match in matches1])
    
    # Pattern for: from ..tools.xxx import yyy  
    pattern2 = r'from \.\.tools\.([^\s]+) import'
    matches2 = re.findall(pattern2, content)
    imports.extend([f"tools/{match.replace('.', '/')}.py" for match in matches2])
    
    # Pattern for: from ..tools import (...)
    pattern3 = r'from \.\.tools import \((.*?)\)'
    match3 = re.search(pattern3, content, re.DOTALL)
    if match3:
        imported_items = re.findall(r'(\w+)', match3.group(1))
        # These correspond to files in tools/ directory
        for item in imported_items:
            imports.append(f"tools/{item}.py")
    
    return sorted(list(set(imports)))

def get_tools_in_init():
    """Get tools exported in __init__.py."""
    init_file = "src/contexten/agents/tools/__init__.py"
    
    if not os.path.exists(init_file):
        return []
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Find imports
    imports = []
    
    # Pattern for: from .xxx import yyy
    pattern = r'from \.([^\s]+) import'
    matches = re.findall(pattern, content)
    imports.extend([f"tools/{match.replace('.', '/')}.py" for match in matches])
    
    return sorted(list(set(imports)))

def main():
    print("🔍 Checking for missing imports in langchain/tools.py...")
    
    # Get all tool files
    all_tools = get_tools_in_directory()
    print(f"\n📁 Found {len(all_tools)} tool files:")
    for tool in all_tools:
        print(f"   - {tool}")
    
    # Get imports in langchain/tools.py
    langchain_imports = get_imports_in_langchain_tools()
    print(f"\n📦 Found {len(langchain_imports)} imports in langchain/tools.py:")
    for imp in langchain_imports:
        print(f"   - {imp}")
    
    # Get tools in __init__.py
    init_imports = get_tools_in_init()
    print(f"\n🔧 Found {len(init_imports)} imports in tools/__init__.py:")
    for imp in init_imports:
        print(f"   - {imp}")
    
    # Find missing imports
    missing_from_langchain = []
    missing_from_init = []
    
    for tool in all_tools:
        if tool not in langchain_imports:
            missing_from_langchain.append(tool)
        if tool not in init_imports:
            missing_from_init.append(tool)
    
    print(f"\n" + "="*80)
    print("📊 ANALYSIS RESULTS")
    print("="*80)
    
    if missing_from_langchain:
        print(f"\n❌ Missing from langchain/tools.py ({len(missing_from_langchain)}):")
        for tool in missing_from_langchain:
            print(f"   - {tool}")
    else:
        print(f"\n✅ All tools are imported in langchain/tools.py")
    
    if missing_from_init:
        print(f"\n❌ Missing from tools/__init__.py ({len(missing_from_init)}):")
        for tool in missing_from_init:
            print(f"   - {tool}")
    else:
        print(f"\n✅ All tools are imported in tools/__init__.py")
    
    # Check for extra imports (imports that don't have corresponding files)
    extra_langchain = [imp for imp in langchain_imports if imp not in all_tools]
    extra_init = [imp for imp in init_imports if imp not in all_tools]
    
    if extra_langchain:
        print(f"\n⚠️  Extra imports in langchain/tools.py ({len(extra_langchain)}):")
        for imp in extra_langchain:
            print(f"   - {imp} (file not found)")
    
    if extra_init:
        print(f"\n⚠️  Extra imports in tools/__init__.py ({len(extra_init)}):")
        for imp in extra_init:
            print(f"   - {imp} (file not found)")
    
    # Summary
    print(f"\n" + "="*80)
    print("🎯 SUMMARY")
    print("="*80)
    
    if not missing_from_langchain and not missing_from_init and not extra_langchain and not extra_init:
        print("✅ All imports are correct and complete!")
    else:
        print("⚠️  Import issues found that need attention:")
        if missing_from_langchain:
            print(f"   - {len(missing_from_langchain)} tools missing from langchain/tools.py")
        if missing_from_init:
            print(f"   - {len(missing_from_init)} tools missing from tools/__init__.py")
        if extra_langchain:
            print(f"   - {len(extra_langchain)} extra imports in langchain/tools.py")
        if extra_init:
            print(f"   - {len(extra_init)} extra imports in tools/__init__.py")

if __name__ == "__main__":
    main()

