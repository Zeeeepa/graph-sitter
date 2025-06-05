#!/usr/bin/env python3
"""
Script to update all imports after restructuring the adapters folder.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path):
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports for moved files
        replacements = {
            # Analysis imports
            r'from graph_sitter\.adapters\.enhanced_analysis': 'from graph_sitter.adapters.analysis.enhanced_analysis',
            r'from graph_sitter\.adapters\.metrics': 'from graph_sitter.adapters.analysis.metrics',
            r'from graph_sitter\.adapters\.dependency_analyzer': 'from graph_sitter.adapters.analysis.dependency_analyzer',
            r'from graph_sitter\.adapters\.call_graph': 'from graph_sitter.adapters.analysis.call_graph',
            r'from graph_sitter\.adapters\.dead_code': 'from graph_sitter.adapters.analysis.dead_code',
            r'from graph_sitter\.adapters\.function_context': 'from graph_sitter.adapters.analysis.function_context',
            
            # Visualization imports
            r'from graph_sitter\.adapters\.react_visualizations': 'from graph_sitter.adapters.visualizations.react_visualizations',
            r'from graph_sitter\.adapters\.codebase_visualization': 'from graph_sitter.adapters.visualizations.codebase_visualization',
            
            # Import statements
            r'import graph_sitter\.adapters\.enhanced_analysis': 'import graph_sitter.adapters.analysis.enhanced_analysis',
            r'import graph_sitter\.adapters\.metrics': 'import graph_sitter.adapters.analysis.metrics',
            r'import graph_sitter\.adapters\.dependency_analyzer': 'import graph_sitter.adapters.analysis.dependency_analyzer',
            r'import graph_sitter\.adapters\.call_graph': 'import graph_sitter.adapters.analysis.call_graph',
            r'import graph_sitter\.adapters\.dead_code': 'import graph_sitter.adapters.analysis.dead_code',
            r'import graph_sitter\.adapters\.function_context': 'import graph_sitter.adapters.analysis.function_context',
            r'import graph_sitter\.adapters\.react_visualizations': 'import graph_sitter.adapters.visualizations.react_visualizations',
            r'import graph_sitter\.adapters\.codebase_visualization': 'import graph_sitter.adapters.visualizations.codebase_visualization',
            
            # Codemods path updates
            r'src/graph_sitter/adapters/analysis/codemods': 'src/graph_sitter/adapters/analysis/codemods',
            r'src/graph_sitter/gsbuild': 'src/graph_sitter/gsbuild',
        }
        
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all imports."""
    print("🔄 Updating imports after adapters restructuring...")
    
    # Directories to scan
    directories = [
        "src/",
        "examples/",
        "tests/",
        "."  # Root directory for config files
    ]
    
    # File extensions to process
    extensions = ['.py', '.toml', '.md', '.txt', '.yaml', '.yml']
    
    updated_files = 0
    total_files = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'node_modules']):
                continue
                
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = Path(root) / file
                    total_files += 1
                    
                    if update_imports_in_file(file_path):
                        updated_files += 1
    
    print(f"\n📊 Import update summary:")
    print(f"  📝 Files processed: {total_files}")
    print(f"  ✅ Files updated: {updated_files}")
    print(f"  📁 Directories scanned: {len(directories)}")

if __name__ == "__main__":
    main()

