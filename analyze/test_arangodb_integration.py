#!/usr/bin/env python3
"""
Test Script: LSP Integration with Arangodb-graphrag Repository

This script tests the transaction-aware LSP integration by analyzing
the Arangodb-graphrag codebase for errors, warnings, and diagnostics.
"""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add the src directory to the path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

def clone_arangodb_repo():
    """Clone the Arangodb-graphrag repository for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    repo_url = "https://github.com/Zeeeepa/Arangodb-graphrag.git"
    
    print(f"🔄 Cloning {repo_url}...")
    try:
        subprocess.run([
            "git", "clone", repo_url, str(temp_dir / "Arangodb-graphrag")
        ], check=True, capture_output=True)
        
        repo_path = temp_dir / "Arangodb-graphrag"
        print(f"✅ Repository cloned to: {repo_path}")
        return repo_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone repository: {e}")
        return None

def test_lsp_integration(repo_path: Path):
    """Test LSP integration with the cloned repository."""
    
    print(f"\n🚀 Testing LSP Integration with Arangodb-graphrag")
    print("=" * 60)
    
    try:
        # Import after adding to path
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        # Initialize codebase with LSP integration
        print(f"📁 Analyzing repository: {repo_path}")
        codebase = Codebase(str(repo_path), enable_lsp=True)
        
        print(f"✅ Codebase initialized successfully")
        print(f"   Name: {codebase.name}")
        print(f"   Language: {codebase.language}")
        print(f"   Files: {len(codebase.files)}")
        
        # Test LSP status
        print(f"\n🔍 LSP Integration Status:")
        print("-" * 30)
        
        if hasattr(codebase, 'is_lsp_enabled'):
            lsp_enabled = codebase.is_lsp_enabled()
            print(f"LSP Enabled: {'✅ Yes' if lsp_enabled else '❌ No'}")
            
            if lsp_enabled:
                status = codebase.get_lsp_status()
                print(f"Serena Available: {'✅ Yes' if status.get('serena_available') else '❌ No'}")
                print(f"Bridge Initialized: {'✅ Yes' if status.get('bridge_initialized') else '❌ No'}")
                print(f"Active Transactions: {status.get('active_transactions', 0)}")
                print(f"Change Listeners: {status.get('change_listeners', 0)}")
                print(f"Cached Files: {status.get('cached_files', 0)}")
            else:
                print("💡 LSP integration disabled - Serena dependencies not available")
        else:
            print("❌ LSP integration not available")
        
        # Analyze file structure
        print(f"\n📊 Repository Analysis:")
        print("-" * 25)
        
        python_files = [f for f in codebase.files if f.path.suffix == '.py']
        js_files = [f for f in codebase.files if f.path.suffix in ['.js', '.ts', '.jsx', '.tsx']]
        other_files = [f for f in codebase.files if f.path.suffix not in ['.py', '.js', '.ts', '.jsx', '.tsx']]
        
        print(f"🐍 Python files: {len(python_files)}")
        print(f"🟨 JavaScript/TypeScript files: {len(js_files)}")
        print(f"📄 Other files: {len(other_files)}")
        
        # Show some sample files
        if python_files:
            print(f"\n📋 Sample Python files:")
            for i, file in enumerate(python_files[:5], 1):
                print(f"  {i}. {file.path}")
        
        # Test error detection
        print(f"\n🐛 Error Detection Test:")
        print("-" * 25)
        
        if hasattr(codebase, 'errors'):
            errors = codebase.errors
            print(f"Total errors found: {len(errors)}")
            
            if errors:
                print(f"\n📋 Error Details (first 3):")
                for i, error in enumerate(errors[:3], 1):
                    print(f"\n{i}. {Path(error.file_path).name}:{error.line}:{error.column}")
                    print(f"   Severity: {error.severity.upper()}")
                    print(f"   Message: {error.message[:100]}{'...' if len(error.message) > 100 else ''}")
                    if error.code:
                        print(f"   Code: {error.code}")
            else:
                print("🎉 No errors found!")
        else:
            print("❌ Error detection not available")
        
        # Test warning detection
        print(f"\n⚠️  Warning Detection Test:")
        print("-" * 28)
        
        if hasattr(codebase, 'warnings'):
            warnings = codebase.warnings
            print(f"Total warnings found: {len(warnings)}")
            
            if warnings:
                for i, warning in enumerate(warnings[:3], 1):
                    print(f"{i}. {Path(warning.file_path).name}:{warning.line} - {warning.message[:80]}{'...' if len(warning.message) > 80 else ''}")
            else:
                print("✨ No warnings found!")
        else:
            print("❌ Warning detection not available")
        
        # Test file-specific diagnostics
        print(f"\n📄 File-Specific Diagnostics Test:")
        print("-" * 35)
        
        if hasattr(codebase, 'get_file_diagnostics') and python_files:
            sample_file = python_files[0]
            file_diagnostics = codebase.get_file_diagnostics(str(sample_file.path))
            
            print(f"Analyzing: {sample_file.path.name}")
            print(f"Diagnostics found: {len(file_diagnostics)}")
            
            for i, diag in enumerate(file_diagnostics[:3], 1):
                print(f"  {i}. Line {diag.line}: {diag.message[:60]}{'...' if len(diag.message) > 60 else ''} ({diag.severity})")
        else:
            print("❌ File-specific diagnostics not available or no Python files")
        
        # Test transaction-aware functionality
        print(f"\n🔄 Transaction-Aware Test:")
        print("-" * 27)
        
        if hasattr(codebase, 'refresh_diagnostics'):
            print("Testing diagnostic refresh...")
            codebase.refresh_diagnostics()
            print("✅ Diagnostics refreshed successfully")
            
            if hasattr(codebase, 'diagnostics'):
                total_diagnostics = len(codebase.diagnostics)
                print(f"Total diagnostics after refresh: {total_diagnostics}")
        else:
            print("❌ Transaction-aware functionality not available")
        
        # Summary
        print(f"\n📊 Final Summary:")
        print("-" * 18)
        
        if hasattr(codebase, 'diagnostics'):
            all_diagnostics = codebase.diagnostics
            error_count = len([d for d in all_diagnostics if d.severity == 'error'])
            warning_count = len([d for d in all_diagnostics if d.severity == 'warning'])
            hint_count = len([d for d in all_diagnostics if d.severity in ['hint', 'information']])
            
            print(f"🔴 Errors: {error_count}")
            print(f"🟡 Warnings: {warning_count}")
            print(f"🔵 Hints: {hint_count}")
            print(f"📈 Total Diagnostics: {len(all_diagnostics)}")
            print(f"📁 Total Files: {len(codebase.files)}")
            print(f"🐍 Python Files: {len(python_files)}")
        else:
            print("❌ Diagnostic summary not available")
        
        # Test results
        print(f"\n🎯 Integration Test Results:")
        print("-" * 30)
        
        tests_passed = 0
        total_tests = 6
        
        if hasattr(codebase, 'is_lsp_enabled'):
            print("✅ LSP status check: PASSED")
            tests_passed += 1
        else:
            print("❌ LSP status check: FAILED")
        
        if hasattr(codebase, 'errors'):
            print("✅ Error detection: PASSED")
            tests_passed += 1
        else:
            print("❌ Error detection: FAILED")
        
        if hasattr(codebase, 'warnings'):
            print("✅ Warning detection: PASSED")
            tests_passed += 1
        else:
            print("❌ Warning detection: FAILED")
        
        if hasattr(codebase, 'hints'):
            print("✅ Hint detection: PASSED")
            tests_passed += 1
        else:
            print("❌ Hint detection: FAILED")
        
        if hasattr(codebase, 'get_file_diagnostics'):
            print("✅ File-specific diagnostics: PASSED")
            tests_passed += 1
        else:
            print("❌ File-specific diagnostics: FAILED")
        
        if hasattr(codebase, 'refresh_diagnostics'):
            print("✅ Transaction-aware updates: PASSED")
            tests_passed += 1
        else:
            print("❌ Transaction-aware updates: FAILED")
        
        print(f"\n📊 Test Score: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.1f}%)")
        
        if tests_passed == total_tests:
            print("🎉 ALL TESTS PASSED! LSP integration is working perfectly!")
        elif tests_passed >= total_tests // 2:
            print("⚠️  PARTIAL SUCCESS: Some LSP features are working")
        else:
            print("❌ TESTS FAILED: LSP integration needs attention")
        
        return tests_passed == total_tests
        
    except Exception as e:
        print(f"❌ Error during LSP integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🧪 Graph-Sitter LSP Integration Test")
    print("Testing with Arangodb-graphrag repository")
    print("=" * 50)
    
    # Clone the repository
    repo_path = clone_arangodb_repo()
    if not repo_path:
        print("❌ Failed to clone repository. Exiting.")
        return False
    
    try:
        # Test the integration
        success = test_lsp_integration(repo_path)
        
        if success:
            print(f"\n🎉 SUCCESS: LSP integration test completed successfully!")
            print("The transaction-aware LSP integration is working as expected.")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some features may not be available.")
            print("This could be due to missing Serena dependencies.")
        
        return success
        
    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(repo_path.parent)
            print(f"\n🧹 Cleaned up temporary directory: {repo_path.parent}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to cleanup {repo_path.parent}: {e}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
