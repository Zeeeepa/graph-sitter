"""
Import migration helper for Contexten extensions refactoring.
Minimal script to help update import statements.
"""

import re
from pathlib import Path
from typing import Dict, List

# Import mapping for the refactored structure
IMPORT_MAPPINGS = {
    'contexten.extensions.github': 'contexten.extensions.Github',
    'contexten.extensions.linear': 'contexten.extensions.Linear', 
    'contexten.extensions.slack': 'contexten.extensions.Slack',
    'contexten.extensions.mcp': 'contexten.mcp',
    'contexten.extensions.events.contexten_app': 'contexten.extensions.Contexten.contexten_app',
    'contexten.extensions.events.client': 'contexten.extensions.Contexten.client',
    'contexten.extensions.events.interface': 'contexten.extensions.Contexten.interface',
    'contexten.extensions.events.modal': 'contexten.extensions.Contexten.modal',
    'contexten.extensions.events.github': 'contexten.extensions.Github.github',
    'contexten.extensions.events.linear': 'contexten.extensions.Linear.linear',
    'contexten.extensions.events.slack': 'contexten.extensions.Slack.slack',
    'contexten.extensions.clients.linear': 'contexten.extensions.Linear.client',
}

def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file. Returns True if changes were made."""
    try:
        content = file_path.read_text()
        original_content = content
        
        for old_import, new_import in IMPORT_MAPPINGS.items():
            # Handle 'from X import Y' statements
            pattern = rf'from\s+{re.escape(old_import)}'
            replacement = f'from {new_import}'
            content = re.sub(pattern, replacement, content)
            
            # Handle 'import X' statements
            pattern = rf'import\s+{re.escape(old_import)}'
            replacement = f'import {new_import}'
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def migrate_imports(root_path: str = "src/contexten") -> None:
    """Migrate imports in all Python files under the given path."""
    root = Path(root_path)
    updated_files = []
    
    for py_file in root.rglob("*.py"):
        if update_imports_in_file(py_file):
            updated_files.append(py_file)
    
    print(f"Updated imports in {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    migrate_imports()

