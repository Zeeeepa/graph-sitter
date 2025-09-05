#!/usr/bin/env python3
"""
Fix all import issues in src/graph_sitter/system-prompt.txt
This script fixes the remaining import errors where graph_sitter.* should be graph_sitter.*
"""

import re
from pathlib import Path


def fix_system_prompt_imports():
    """Fix all import issues in the system-prompt.txt file."""
    file_path = Path("src/graph_sitter/system-prompt.txt")
    
    print(f"🔧 Fixing imports in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Define the import mappings for system-prompt.txt
        import_mappings = {
            # Basic Codebase import
            r'from graph_sitter import Codebase': 'from graph_sitter import Codebase',
            
            # Config imports
            r'from graph_sitter\.configs import CodebaseConfig': 'from graph_sitter.configs import CodebaseConfig',
            r'from graph_sitter\.configs\.models\.codebase import CodebaseConfig': 'from graph_sitter.configs.models.codebase import CodebaseConfig',
            r'from graph_sitter\.configs\.models\.secrets import SecretsConfig': 'from graph_sitter.configs.models.secrets import SecretsConfig',
            
            # Git imports
            r'from graph_sitter\.git\.repo_operator\.local_repo_operator import LocalRepoOperator': 'from graph_sitter.git.repo_operator.local_repo_operator import LocalRepoOperator',
            r'from graph_sitter\.git\.schemas\.repo_config import BaseRepoConfig': 'from graph_sitter.git.schemas.repo_config import BaseRepoConfig',
            r'from graph_sitter\.git\.repo_operator\.repo_operator import RepoOperator': 'from graph_sitter.git.repo_operator.repo_operator import RepoOperator',
            r'from graph_sitter\.git\.schemas\.repo_config import RepoConfig': 'from graph_sitter.git.schemas.repo_config import RepoConfig',
            
            # SDK imports (should all be graph_sitter)
            r'from graph_sitter\.sdk import ExternalModule': 'from graph_sitter.core.external_module import ExternalModule',
            r'from graph_sitter\.sdk\.codebase\.config import ProjectConfig': 'from graph_sitter.sdk.codebase.config import ProjectConfig',
            r'from graph_sitter\.sdk\.core\.interfaces\.callable import FunctionCallDefinition': 'from graph_sitter.core.interfaces.callable import FunctionCallDefinition',
            r'from graph_sitter\.sdk\.core\.function import Function': 'from graph_sitter.core.function import Function',
            r'from graph_sitter\.sdk\.core\.external_module import ExternalModule': 'from graph_sitter.core.external_module import ExternalModule',
            r'from graph_sitter\.sdk\.core\.import_resolution import Import': 'from graph_sitter.core.import_resolution import Import',
            r'from graph_sitter\.sdk\.core\.symbol import Symbol': 'from graph_sitter.core.symbol import Symbol',
            
            # Shared imports
            r'from graph_sitter\.shared\.enums\.programming_language import ProgrammingLanguage': 'from graph_sitter.shared.enums.programming_language import ProgrammingLanguage',
            
            # Extension imports (these should all be graph_sitter.extensions)
            r'from graph_sitter\.extensions\.index\.file_index import FileIndex': 'from graph_sitter.extensions.index.file_index import FileIndex',
            r'from graph_sitter\.extensions\.lsp\.utils import get_path': 'from graph_sitter.extensions.lsp.utils import get_path',
            r'from graph_sitter\.extensions\.lsp\.codemods import ACTIONS': 'from graph_sitter.extensions.lsp.codemods import ACTIONS',
            r'from graph_sitter\.extensions\.lsp\.codemods\.base import CodeAction': 'from graph_sitter.extensions.lsp.codemods.base import CodeAction',
            r'from graph_sitter\.extensions\.lsp\.execute import execute_action': 'from graph_sitter.extensions.lsp.execute import execute_action',
            r'from graph_sitter\.extensions\.lsp\.io import LSPIO': 'from graph_sitter.extensions.lsp.io import LSPIO',
            r'from graph_sitter\.extensions\.lsp\.progress import LSPProgress': 'from graph_sitter.extensions.lsp.progress import LSPProgress',
            r'from graph_sitter\.extensions\.lsp\.range import get_tree_sitter_range': 'from graph_sitter.extensions.lsp.range import get_tree_sitter_range',
            r'from graph_sitter\.extensions\.index\.code_index import CodeIndex': 'from graph_sitter.extensions.index.code_index import CodeIndex',
            r'from graph_sitter\.extensions\.graph\.create_graph import create_codebase_graph': 'from graph_sitter.extensions.graph.create_graph import create_codebase_graph',
            r'from graph_sitter\.extensions\.graph\.neo4j_exporter import Neo4jExporter': 'from graph_sitter.extensions.graph.neo4j_exporter import Neo4jExporter',
            r'from graph_sitter\.extensions\.graph\.utils import Node, NodeLabel, Relation, RelationLabel, SimpleGraph': 'from graph_sitter.extensions.graph.utils import Node, NodeLabel, Relation, RelationLabel, SimpleGraph',
            r'from graph_sitter\.extensions\.graph\.utils import SimpleGraph': 'from graph_sitter.extensions.graph.utils import SimpleGraph',
            r'from graph_sitter\.extensions\.attribution\.main import add_attribution_to_symbols, analyze_ai_impact': 'from graph_sitter.extensions.attribution.main import add_attribution_to_symbols, analyze_ai_impact',
        }
        
        # Apply all the import fixes
        fixes_applied = 0
        for pattern, replacement in import_mappings.items():
            old_content = content
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                fixes_applied += 1
                print(f"  ✅ Fixed: {pattern} → {replacement}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n🎉 Applied {fixes_applied} fixes to {file_path}")
        else:
            print(f"\n✅ No fixes needed in {file_path}")
        
        return fixes_applied
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return 0


def verify_fixes():
    """Verify that all import issues are resolved."""
    file_path = Path("src/graph_sitter/system-prompt.txt")
    
    print(f"\n🔍 Verifying fixes in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for remaining problematic imports
        problematic_patterns = [
            r'from graph_sitter import Codebase',
            r'from graph_sitter\.configs',
            r'from graph_sitter\.git',
            r'from graph_sitter\.sdk',
            r'from graph_sitter\.shared',
            r'from graph_sitter\.extensions',
        ]
        
        remaining_issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in problematic_patterns:
                if re.search(pattern, line):
                    remaining_issues.append({
                        'line': line_num,
                        'content': line.strip(),
                        'pattern': pattern
                    })
        
        if remaining_issues:
            print(f"⚠️ Found {len(remaining_issues)} remaining issues:")
            for issue in remaining_issues:
                print(f"  Line {issue['line']}: {issue['content']}")
        else:
            print("🎉 All import issues resolved!")
        
        return len(remaining_issues) == 0
        
    except Exception as e:
        print(f"❌ Error verifying {file_path}: {e}")
        return False


def main():
    print("🚀 Starting system-prompt.txt import fixes...")
    
    fixes_applied = fix_system_prompt_imports()
    verification_passed = verify_fixes()
    
    if verification_passed:
        print(f"\n✅ Successfully fixed all imports in system-prompt.txt!")
        print(f"📊 Total fixes applied: {fixes_applied}")
    else:
        print(f"\n⚠️ Some issues may remain - please review manually")


if __name__ == "__main__":
    main()

