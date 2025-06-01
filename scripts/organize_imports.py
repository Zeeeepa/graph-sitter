#!/usr/bin/env python3
"""
Import Organization Script

This script organizes imports across the entire graph-sitter/src folder
according to PEP 8 standards:
1. Standard library imports
2. Third-party imports  
3. Local application imports

Each group is sorted alphabetically and separated by blank lines.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Standard library modules (comprehensive list)
STANDARD_LIBRARY_MODULES = {
    'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64', 'bisect',
    'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmd', 'code',
    'codecs', 'codeop', 'collections', 'colorsys', 'compileall', 'concurrent',
    'configparser', 'contextlib', 'copy', 'copyreg', 'csv', 'ctypes', 'curses',
    'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'doctest',
    'email', 'encodings', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp',
    'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac', 'html',
    'http', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
    'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
    'modulefinder', 'multiprocessing', 'netrc', 'numbers', 'operator', 'optparse',
    'os', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile', 'pstats',
    'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random',
    're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
    'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
    'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'sqlite3',
    'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
    'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'tabnanny', 'tarfile',
    'tempfile', 'termios', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
    'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
    'types', 'typing', 'typing_extensions', 'unicodedata', 'unittest', 'urllib',
    'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
    'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
    'zipimport', 'zlib'
}

# Known third-party packages
THIRD_PARTY_MODULES = {
    'aiofiles', 'aiohttp', 'anthropic', 'anyio', 'asyncpg', 'attrs', 'beautifulsoup4',
    'boto3', 'celery', 'click', 'cryptography', 'django', 'docker', 'fastapi',
    'flask', 'git', 'github', 'httpx', 'jinja2', 'langchain', 'langchain_anthropic',
    'langchain_core', 'langchain_openai', 'langchain_xai', 'lazy_object_proxy',
    'matplotlib', 'networkx', 'numpy', 'openai', 'pandas', 'pillow', 'plotly',
    'psycopg2', 'pydantic', 'pytest', 'redis', 'requests', 'rich', 'scipy',
    'sqlalchemy', 'starlette', 'tree_sitter', 'uvicorn', 'websockets'
}

# Local modules for this project
LOCAL_MODULES = {
    'graph_sitter', 'contexten', 'autogenlib'
}

def classify_import(import_line: str) -> str:
    """Classify an import as standard library, third-party, or local."""
    # Extract the module name
    if import_line.strip().startswith('import '):
        module = import_line.strip().split()[1].split('.')[0]
    elif import_line.strip().startswith('from '):
        module = import_line.strip().split()[1].split('.')[0]
    else:
        return 'other'
    
    if module in STANDARD_LIBRARY_MODULES:
        return 'standard'
    elif module in LOCAL_MODULES:
        return 'local'
    elif module in THIRD_PARTY_MODULES:
        return 'third_party'
    else:
        # Try to guess based on naming conventions
        if module.startswith('_') or '.' in module:
            return 'local'
        else:
            return 'third_party'

def organize_file_imports(content: str) -> str:
    """Organize imports in a Python file."""
    lines = content.split('\n')
    
    # Separate imports from other code
    std_lib_imports = []
    third_party_imports = []
    local_imports = []
    other_lines = []
    
    in_docstring = False
    docstring_char = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
                docstring_char = stripped[:3]
            elif stripped.endswith(docstring_char):
                in_docstring = False
            other_lines.append(line)
            continue
        elif in_docstring:
            other_lines.append(line)
            continue
        
        # Skip comments and empty lines at the top
        if stripped.startswith('#') or not stripped:
            other_lines.append(line)
            continue
        
        # Check if it's an import
        if stripped.startswith('import ') or stripped.startswith('from '):
            classification = classify_import(stripped)
            if classification == 'standard':
                std_lib_imports.append(stripped)
            elif classification == 'third_party':
                third_party_imports.append(stripped)
            elif classification == 'local':
                local_imports.append(stripped)
            else:
                other_lines.append(line)
        else:
            other_lines.append(line)
    
    # Sort each group
    std_lib_imports.sort()
    third_party_imports.sort()
    local_imports.sort()
    
    # Rebuild the file
    organized = []
    
    # Add file header (shebang, encoding, docstring)
    header_lines = []
    for line in other_lines:
        if (line.startswith('#!') or 
            line.startswith('# -*- coding:') or 
            line.startswith('# coding:') or
            line.strip().startswith('"""') or
            line.strip().startswith("'''") or
            line.strip() == '' and not organized):
            header_lines.append(line)
        else:
            break
    
    if header_lines:
        organized.extend(header_lines)
        if header_lines[-1].strip():  # Add blank line after header if needed
            organized.append('')
    
    # Add organized imports
    if std_lib_imports:
        organized.extend(std_lib_imports)
        organized.append('')
    
    if third_party_imports:
        organized.extend(third_party_imports)
        organized.append('')
    
    if local_imports:
        organized.extend(local_imports)
        organized.append('')
    
    # Add the rest of the code (skip header lines we already added)
    remaining_lines = other_lines[len(header_lines):]
    organized.extend(remaining_lines)
    
    # Clean up extra blank lines
    result = []
    prev_blank = False
    for line in organized:
        if line.strip() == '':
            if not prev_blank:
                result.append(line)
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    
    return '\n'.join(result)

def process_python_file(file_path: Path) -> bool:
    """Process a single Python file to organize its imports."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        organized_content = organize_file_imports(original_content)
        
        # Only write if content changed
        if organized_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(organized_content)
            print(f"✅ Organized imports in {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def organize_imports_in_directory(directory: Path) -> Tuple[int, int]:
    """Organize imports in all Python files in a directory."""
    processed = 0
    modified = 0
    
    for file_path in directory.rglob('*.py'):
        # Skip __pycache__ and other generated directories
        if '__pycache__' in str(file_path) or '.git' in str(file_path):
            continue
        
        processed += 1
        if process_python_file(file_path):
            modified += 1
    
    return processed, modified

def main():
    """Main function to organize imports across the src folder."""
    print("🔧 Import Organization Script")
    print("=" * 50)
    
    # Find the src directory
    script_dir = Path(__file__).parent
    src_dir = script_dir.parent / 'src'
    
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        sys.exit(1)
    
    print(f"📁 Processing directory: {src_dir}")
    print(f"🔍 Looking for Python files...")
    
    # Process all Python files
    processed, modified = organize_imports_in_directory(src_dir)
    
    print("\n📊 Summary:")
    print(f"📄 Files processed: {processed}")
    print(f"✏️  Files modified: {modified}")
    print(f"⏭️  Files unchanged: {processed - modified}")
    
    if modified > 0:
        print(f"\n✅ Successfully organized imports in {modified} files!")
    else:
        print("\n✅ All files already have organized imports!")
    
    print("\n🎯 Import organization complete!")

if __name__ == "__main__":
    main()

