#!/usr/bin/env python3
"""
Import Organization Script for Contexten

This script organizes imports in Python files according to PEP 8 guidelines:
1. Standard library imports
2. Third-party imports  
3. Local application imports

Each group is sorted alphabetically and separated by blank lines.
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Standard library modules (Python 3.8+)
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses',
    'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils',
    'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler',
    'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
    'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
    'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
    'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
    'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
    'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'multiprocessing',
    'netrc', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
    'plistlib', 'poplib', 'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
    'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline',
    'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
    'sndhdr', 'socket', 'socketserver', 'sqlite3', 'ssl', 'stat', 'statistics',
    'string', 'stringprep', 'struct', 'subprocess', 'sunau', 'symbol', 'symtable',
    'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile',
    'termios', 'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token',
    'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo',
    'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
    'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
    'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib'
}

# Known third-party packages
THIRD_PARTY_MODULES = {
    'fastapi', 'uvicorn', 'pydantic', 'requests', 'aiohttp', 'httpx', 'flask',
    'django', 'sqlalchemy', 'alembic', 'pytest', 'numpy', 'pandas', 'matplotlib',
    'seaborn', 'scipy', 'sklearn', 'tensorflow', 'torch', 'transformers',
    'langchain', 'langchain_core', 'langchain_anthropic', 'langchain_openai',
    'anthropic', 'openai', 'click', 'typer', 'rich', 'tqdm', 'jinja2', 'yaml',
    'toml', 'boto3', 'redis', 'celery', 'prefect', 'modal', 'streamlit', 'gradio',
    'plotly', 'dash', 'jupyter', 'ipython', 'notebook', 'black', 'isort', 'flake8',
    'mypy', 'pylint', 'pytest_asyncio', 'pytest_mock', 'factory_boy', 'faker',
    'freezegun', 'responses', 'httpretty', 'vcr', 'cassette', 'betamax'
}


class ImportOrganizer:
    def __init__(self):
        self.future_imports = []
        self.stdlib_imports = []
        self.third_party_imports = []
        self.local_imports = []
        
    def categorize_import(self, import_line: str) -> str:
        """Categorize an import line into future, stdlib, third-party, or local."""
        # Handle __future__ imports
        if 'from __future__ import' in import_line:
            return 'future'
            
        # Extract module name
        if import_line.strip().startswith('from '):
            # from module import something
            match = re.match(r'from\s+([^\s]+)', import_line.strip())
            if match:
                module = match.group(1)
            else:
                return 'local'  # fallback
        elif import_line.strip().startswith('import '):
            # import module
            match = re.match(r'import\s+([^\s,]+)', import_line.strip())
            if match:
                module = match.group(1)
            else:
                return 'local'  # fallback
        else:
            return 'local'  # fallback
            
        # Get the top-level module name
        top_level = module.split('.')[0]
        
        # Check if it's a standard library module
        if top_level in STDLIB_MODULES:
            return 'stdlib'
            
        # Check if it's a known third-party module
        if top_level in THIRD_PARTY_MODULES:
            return 'third_party'
            
        # Check if it's a local import (starts with contexten, graph_sitter, or relative)
        if (module.startswith('contexten') or 
            module.startswith('graph_sitter') or 
            module.startswith('.')):
            return 'local'
            
        # Default to third-party for unknown modules
        return 'third_party'
    
    def organize_imports(self, content: str) -> str:
        """Organize imports in the given file content."""
        lines = content.split('\n')
        
        # Reset import lists
        self.future_imports = []
        self.stdlib_imports = []
        self.third_party_imports = []
        self.local_imports = []
        
        # Find import section
        import_start = None
        import_end = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                (stripped.startswith('#') and 'import' in stripped.lower())):
                if import_start is None:
                    import_start = i
                import_end = i
            elif import_start is not None and stripped and not stripped.startswith('#'):
                # Found non-import, non-comment line after imports started
                break
                
        if import_start is None:
            return content  # No imports found
            
        # Extract and categorize imports
        import_lines = []
        current_import = ""
        
        for i in range(import_start, import_end + 1):
            line = lines[i]
            stripped = line.strip()
            
            # Skip comments and empty lines in import section
            if not stripped or stripped.startswith('#'):
                continue
                
            # Handle multi-line imports
            if current_import:
                current_import += " " + stripped
                if not stripped.endswith('\\') and not stripped.endswith(','):
                    import_lines.append(current_import)
                    current_import = ""
            else:
                if stripped.endswith('\\') or (stripped.endswith(',') and '(' in stripped):
                    current_import = stripped
                else:
                    import_lines.append(stripped)
        
        # Add any remaining multi-line import
        if current_import:
            import_lines.append(current_import)
            
        # Categorize imports
        for import_line in import_lines:
            category = self.categorize_import(import_line)
            if category == 'future':
                self.future_imports.append(import_line)
            elif category == 'stdlib':
                self.stdlib_imports.append(import_line)
            elif category == 'third_party':
                self.third_party_imports.append(import_line)
            else:
                self.local_imports.append(import_line)
        
        # Sort each category
        self.future_imports.sort()
        self.stdlib_imports.sort()
        self.third_party_imports.sort()
        self.local_imports.sort()
        
        # Build organized import section
        organized_imports = []
        
        if self.future_imports:
            organized_imports.extend(self.future_imports)
            organized_imports.append("")
            
        if self.stdlib_imports:
            organized_imports.extend(self.stdlib_imports)
            organized_imports.append("")
            
        if self.third_party_imports:
            organized_imports.extend(self.third_party_imports)
            organized_imports.append("")
            
        if self.local_imports:
            organized_imports.extend(self.local_imports)
            organized_imports.append("")
        
        # Remove trailing empty line if it's the last element
        if organized_imports and organized_imports[-1] == "":
            organized_imports.pop()
            
        # Reconstruct file content
        result_lines = []
        
        # Add content before imports
        result_lines.extend(lines[:import_start])
        
        # Add organized imports
        result_lines.extend(organized_imports)
        
        # Add content after imports
        if import_end + 1 < len(lines):
            result_lines.extend(lines[import_end + 1:])
            
        return '\n'.join(result_lines)
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to organize its imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Skip files with no imports
            if not ('import ' in original_content or 'from ' in original_content):
                return False
                
            organized_content = self.organize_imports(original_content)
            
            # Only write if content changed
            if organized_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(organized_content)
                print(f"✅ Organized imports in: {file_path}")
                return True
            else:
                print(f"⏭️  No changes needed: {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False


def main():
    """Main function to organize imports in all Python files in contexten directory."""
    organizer = ImportOrganizer()
    
    # Find all Python files in contexten directory
    contexten_dir = Path("src/contexten")
    if not contexten_dir.exists():
        print(f"❌ Directory {contexten_dir} not found!")
        return
        
    python_files = list(contexten_dir.rglob("*.py"))
    
    if not python_files:
        print(f"❌ No Python files found in {contexten_dir}")
        return
        
    print(f"🔍 Found {len(python_files)} Python files in {contexten_dir}")
    print("🧹 Organizing imports...\n")
    
    processed_count = 0
    changed_count = 0
    
    for file_path in python_files:
        processed_count += 1
        if organizer.process_file(file_path):
            changed_count += 1
            
    print(f"\n📊 Summary:")
    print(f"   • Files processed: {processed_count}")
    print(f"   • Files modified: {changed_count}")
    print(f"   • Files unchanged: {processed_count - changed_count}")
    print("\n✨ Import organization complete!")


if __name__ == "__main__":
    main()

