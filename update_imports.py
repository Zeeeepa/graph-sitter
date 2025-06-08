import os
import re

def update_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Replace the import
                if 'from .codemod import Codemod' in content:
                    content = content.replace(
                        'from .codemod import Codemod',
                        'from graph_sitter.codemods.codemod import Codemod'
                    )
                    
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"Updated imports in {filepath}")

if __name__ == '__main__':
    update_imports('src/graph_sitter/codemods')

