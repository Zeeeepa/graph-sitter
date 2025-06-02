#!/usr/bin/env python3
"""
Analyze agent tools usage and fix import paths.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in directory."""
    path = Path(directory)
    return list(path.rglob("*.py"))

def extract_imports(file_path: Path) -> Set[str]:
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"⚠️  Syntax error in {file_path}")
            return imports
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        full_import = f"{node.module}.{alias.name}"
                        imports.add(full_import)
                        imports.add(node.module)
                        
        # Also check for string-based imports (importlib, __import__, etc.)
        string_import_patterns = [
            r'importlib\.import_module\(["\']([^"\']+)["\']',
            r'__import__\(["\']([^"\']+)["\']',
        ]
        
        for pattern in string_import_patterns:
            matches = re.findall(pattern, content)
            imports.update(matches)
            
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        
    return imports

def analyze_agent_tools():
    """Analyze agent tools and their usage."""
    
    # List of potentially dead agent files
    dead_agent_files = [
        "agents/data.py",
        "agents/langchain/graph.py", 
        "agents/tools/commit.py",
        "agents/tools/create_file.py",
        "agents/tools/delete_file.py",
        "agents/tools/edit_file.py",
        "agents/tools/github/create_pr.py",
        "agents/tools/github/create_pr_comment.py",
        "agents/tools/github/create_pr_review_comment.py",
        "agents/tools/github/search.py",
        "agents/tools/list_directory.py",
        "agents/tools/move_symbol.py",
        "agents/tools/relace_edit_prompts.py",
        "agents/tools/rename_file.py",
        "agents/tools/run_codemod.py",
        "agents/tools/semantic_edit_prompts.py",
        "agents/tools/view_file.py",
    ]
    
    print("🔍 Analyzing agent tools usage...")
    
    # Find all Python files
    all_files = find_python_files("src/contexten")
    
    # Extract all imports from all files
    all_imports = set()
    file_imports = {}
    
    for file_path in all_files:
        imports = extract_imports(file_path)
        file_imports[str(file_path)] = imports
        all_imports.update(imports)
    
    print(f"📁 Found {len(all_files)} Python files")
    print(f"📦 Found {len(all_imports)} unique imports")
    
    # Analyze each potentially dead agent file
    results = {}
    
    for agent_file in dead_agent_files:
        full_path = f"src/contexten/{agent_file}"
        
        # Convert file path to module path
        module_path = agent_file.replace("/", ".").replace(".py", "")
        contexten_module = f"contexten.{module_path}"
        
        # Check various import patterns
        import_patterns = [
            module_path,
            contexten_module,
            agent_file,
            agent_file.replace(".py", ""),
            os.path.basename(agent_file).replace(".py", ""),
        ]
        
        # Check if any file imports this module
        found_imports = []
        importing_files = []
        
        for file_path, imports in file_imports.items():
            for pattern in import_patterns:
                if any(pattern in imp for imp in imports):
                    found_imports.extend([imp for imp in imports if pattern in imp])
                    if file_path not in importing_files:
                        importing_files.append(file_path)
        
        # Check if file exists
        exists = os.path.exists(full_path)
        
        # Check if it's in __init__.py files
        in_init = False
        init_files = [f for f in all_files if f.name == "__init__.py"]
        for init_file in init_files:
            init_imports = file_imports.get(str(init_file), set())
            if any(pattern in imp for imp in init_imports for pattern in import_patterns):
                in_init = True
                break
        
        results[agent_file] = {
            "exists": exists,
            "found_imports": list(set(found_imports)),
            "importing_files": importing_files,
            "in_init": in_init,
            "module_patterns": import_patterns
        }
    
    # Print results
    print("\n" + "="*80)
    print("🎯 AGENT TOOLS ANALYSIS RESULTS")
    print("="*80)
    
    actually_used = []
    truly_dead = []
    needs_investigation = []
    
    for agent_file, data in results.items():
        status = "❓ UNKNOWN"
        category = needs_investigation
        
        if not data["exists"]:
            status = "❌ MISSING"
            category = truly_dead
        elif data["found_imports"] or data["importing_files"] or data["in_init"]:
            status = "✅ USED"
            category = actually_used
        else:
            status = "💀 POTENTIALLY DEAD"
            category = truly_dead
            
        category.append(agent_file)
        
        print(f"\n{status} {agent_file}")
        if data["found_imports"]:
            print(f"   📦 Imports found: {data['found_imports'][:3]}{'...' if len(data['found_imports']) > 3 else ''}")
        if data["importing_files"]:
            print(f"   📁 Used by: {len(data['importing_files'])} files")
            for f in data["importing_files"][:2]:
                print(f"      - {f}")
            if len(data["importing_files"]) > 2:
                print(f"      - ... and {len(data['importing_files']) - 2} more")
        if data["in_init"]:
            print(f"   🔧 Found in __init__.py")
    
    print(f"\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Actually used: {len(actually_used)} files")
    print(f"💀 Potentially dead: {len(truly_dead)} files") 
    print(f"❓ Needs investigation: {len(needs_investigation)} files")
    
    if actually_used:
        print(f"\n✅ CONFIRMED USED FILES ({len(actually_used)}):")
        for f in actually_used:
            print(f"   - {f}")
    
    if truly_dead:
        print(f"\n💀 POTENTIALLY DEAD FILES ({len(truly_dead)}):")
        for f in truly_dead:
            print(f"   - {f}")
    
    if needs_investigation:
        print(f"\n❓ NEEDS INVESTIGATION ({len(needs_investigation)}):")
        for f in needs_investigation:
            print(f"   - {f}")
    
    # Check tools/__init__.py specifically
    print(f"\n" + "="*80)
    print("🔧 TOOLS __init__.py ANALYSIS")
    print("="*80)
    
    tools_init = "src/contexten/agents/tools/__init__.py"
    if os.path.exists(tools_init):
        with open(tools_init, 'r') as f:
            init_content = f.read()
        
        print("📦 Tools exported in __init__.py:")
        
        # Extract __all__ list
        all_match = re.search(r'__all__\s*=\s*\[(.*?)\]', init_content, re.DOTALL)
        if all_match:
            all_items = re.findall(r'["\']([^"\']+)["\']', all_match.group(1))
            for item in sorted(all_items):
                print(f"   - {item}")
        
        # Check imports in __init__.py
        print("\n📥 Imports in tools/__init__.py:")
        init_imports = extract_imports(Path(tools_init))
        for imp in sorted(init_imports):
            if "agents.tools" in imp or imp.startswith("."):
                print(f"   - {imp}")
    
    return results

if __name__ == "__main__":
    analyze_agent_tools()

