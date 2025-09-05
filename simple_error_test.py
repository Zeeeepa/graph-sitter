#!/usr/bin/env python3
"""
Simple test to debug error detection
"""

import asyncio
import tempfile
import os
from pathlib import Path
from enhanced_analytics_api import SerenaErrorAnalyzer

async def test_direct_analysis():
    """Test error analysis directly."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    print(f"📁 Created test repository at: {temp_dir}")
    
    # Create Python file with errors
    python_file = Path(temp_dir) / "main.py"
    python_code = '''import os
import sys
import unused_module

def main():
    result = undefined_variable + 1
    return result
'''
    python_file.write_text(python_code)
    
    print(f"📝 Created file: {python_file}")
    print(f"📄 File content:\n{python_code}")
    
    # Test the analyzer
    analyzer = SerenaErrorAnalyzer()
    
    try:
        print(f"\n🔍 Testing codebase initialization...")
        
        # Try to create codebase directly
        from graph_sitter.core.codebase import Codebase
        
        print(f"Path exists: {os.path.exists(temp_dir)}")
        print(f"Files in directory: {list(os.listdir(temp_dir))}")
        
        # Initialize codebase using from_files
        files_dict = {}
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_dict[rel_path] = f.read()
        
        print(f"Files to analyze: {list(files_dict.keys())}")
        codebase = Codebase.from_files(files_dict)
        print(f"✅ Codebase created successfully")
        
        # Check files
        print(f"Files in codebase: {len(codebase.files)}")
        for file in codebase.files:
            print(f"  - {file.path} (suffix: {file.path.suffix})")
            print(f"    Source length: {len(file.source)}")
            print(f"    Source preview: {repr(file.source[:100])}")
        
        # Test static analysis directly
        print(f"\n🔍 Testing static analysis...")
        errors = analyzer._perform_static_analysis(codebase)
        print(f"Found {len(errors)} errors")
        
        for error in errors:
            print(f"  - {error.file_path}:{error.line_number} - {error.message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up test repository")

if __name__ == "__main__":
    asyncio.run(test_direct_analysis())
