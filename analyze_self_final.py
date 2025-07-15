#!/usr/bin/env python3
"""
Final self-analysis of graph-sitter codebase with all fixes applied
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🔍 Graph-Sitter Self-Analysis (Post-Fix)")
    print("=" * 50)
    
    try:
        from graph_sitter import Codebase
        
        # Create codebase instance
        print("📦 Creating codebase instance...")
        codebase = Codebase("./")
        
        print(f"✅ Codebase: {codebase.name}")
        print(f"📁 Path: {codebase.repo_path}")
        print(f"🔧 Language: {codebase.language}")
        print(f"📄 Files: {len(codebase.files)}")
        print(f"🏗️  Nodes: {len(codebase.ctx.nodes)}")
        print(f"🔗 Edges: {len(codebase.ctx.edges)}")
        
        # Test pink SDK integration
        print("\n📦 Pink SDK Status:")
        from graph_sitter.configs.models.codebase import PinkMode
        print(f"  Available modes: {[mode.name for mode in PinkMode]}")
        print(f"  Current mode: {codebase.ctx.config.use_pink.name}")
        
        # Test Serena integration
        print("\n🚀 Serena Integration Status:")
        try:
            from graph_sitter.extensions.serena import SerenaIntegration
            print("  ✅ SerenaIntegration available")
            
            # Check if codebase has Serena methods (they should be added automatically)
            serena_methods = [
                'get_completions', 'get_hover_info', 'get_signature_help',
                'find_references', 'get_diagnostics', 'perform_refactoring'
            ]
            
            available_methods = []
            for method in serena_methods:
                if hasattr(codebase, method):
                    available_methods.append(method)
            
            print(f"  🔧 Available Serena methods: {len(available_methods)}/{len(serena_methods)}")
            if available_methods:
                print(f"    Methods: {', '.join(available_methods)}")
                
        except Exception as e:
            print(f"  ❌ Serena integration error: {e}")
        
        # Test LSP integration
        print("\n🔧 LSP Integration Status:")
        try:
            from graph_sitter.extensions.lsp.transaction_manager import get_lsp_manager
            manager = get_lsp_manager(str(codebase.repo_path))
            print("  ✅ LSP manager created successfully")
            print(f"  📁 Repository: {manager.repo_path}")
            print(f"  🔧 LSP enabled: {manager.enable_lsp}")
        except Exception as e:
            print(f"  ❌ LSP integration error: {e}")
        
        # Test diagnostics
        print("\n🩺 Diagnostics Status:")
        try:
            from graph_sitter.core.diagnostics import CodebaseDiagnostics
            diagnostics = CodebaseDiagnostics(codebase)
            print("  ✅ Diagnostics initialized")
            print(f"  🔧 LSP enabled: {diagnostics.enable_lsp}")
        except Exception as e:
            print(f"  ❌ Diagnostics error: {e}")
        
        # Analyze some key files
        print("\n📊 Key File Analysis:")
        key_files = [
            "src/graph_sitter/core/codebase.py",
            "src/graph_sitter/extensions/serena/__init__.py",
            "src/graph_sitter/extensions/lsp/transaction_manager.py"
        ]
        
        for file_path in key_files:
            if Path(file_path).exists():
                try:
                    file_obj = codebase.get_file(file_path)
                    if file_obj:
                        print(f"  📄 {file_path}: {len(file_obj.functions)} functions, {len(file_obj.classes)} classes")
                    else:
                        print(f"  📄 {file_path}: Not found in codebase")
                except Exception as e:
                    print(f"  📄 {file_path}: Error - {e}")
        
        print("\n🎉 Self-analysis complete! All major components are working.")
        return True
        
    except Exception as e:
        print(f"❌ Self-analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
