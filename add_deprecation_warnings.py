#!/usr/bin/env python3
"""
Add deprecation warnings to old files
"""

import os

files_to_deprecate = {
    'src/lsp_diagnostics.py': 'lsp_adapter.py',
    'src/graph_sitter_analysis.py': 'codebase_analysis.py',
    'src/graph_sitter_backend.py': 'codebase_analysis.py',
}

deprecation_warning = '''# ================================================================================
# DEPRECATION WARNING
# ================================================================================
# This module has been consolidated into {new_module}.
# Please update your imports:
#   Old: from {old_import} import ...
#   New: from {new_import} import ...
#
# This file will be removed in a future release.
# ================================================================================

import warnings
warnings.warn(
    "This module is deprecated. Use {new_module} instead.",
    DeprecationWarning,
    stacklevel=2
)

'''

for old_file, new_file in files_to_deprecate.items():
    if os.path.exists(old_file):
        old_module = old_file.replace('src/', '').replace('.py', '')
        new_module = new_file.replace('.py', '')
        
        # Read existing content
        with open(old_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has deprecation warning
        if 'DEPRECATION WARNING' in content:
            print(f"✅ {old_file} already has deprecation warning")
            continue
        
        # Add deprecation warning at the top (after shebang/encoding if present)
        lines = content.split('\n')
        insert_pos = 0
        
        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_pos = 1
        
        # Skip encoding
        if insert_pos < len(lines) and 'coding' in lines[insert_pos]:
            insert_pos += 1
        
        # Insert warning
        warning = deprecation_warning.format(
            old_import=old_module,
            new_import=new_module,
            new_module=new_file
        )
        
        lines.insert(insert_pos, warning)
        
        # Write back
        with open(old_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Added deprecation warning to {old_file}")
    else:
        print(f"⚠️  {old_file} not found")

# Mark analysisbig.py as deprecated (it's already broken)
if os.path.exists('src/analysisbig.py'):
    broken_warning = '''# ================================================================================
# DEPRECATED - DO NOT USE
# ================================================================================
# This file has syntax errors and is not functional.
# It appears to be an incomplete/experimental version.
#
# This file will be removed in a future release.
# ================================================================================

'''
    
    try:
        with open('src/analysisbig.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'DEPRECATED - DO NOT USE' not in content:
            with open('src/analysisbig.py', 'w', encoding='utf-8') as f:
                f.write(broken_warning + content)
            print("✅ Marked analysisbig.py as deprecated")
        else:
            print("✅ analysisbig.py already marked as deprecated")
    except Exception as e:
        print(f"⚠️  Could not update analysisbig.py: {e}")

print("\n✅ Deprecation warnings added successfully!")

