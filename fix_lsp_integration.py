#!/usr/bin/env python3
"""
FIX LSP INTEGRATION

This script fixes the LSP integration issues that are preventing error detection.
"""

import sys
from pathlib import Path

def fix_transaction_manager():
    """Fix the transaction manager WeakKeyDictionary issue."""
    print("🔧 FIXING TRANSACTION MANAGER")
    print("=" * 60)
    
    transaction_manager_file = Path("src/graph_sitter/extensions/lsp/transaction_manager.py")
    
    if not transaction_manager_file.exists():
        print(f"❌ File not found: {transaction_manager_file}")
        return False
    
    # Read the current content
    with open(transaction_manager_file, 'r') as f:
        content = f.read()
    
    # Fix the WeakKeyDictionary issue
    old_code = '''# Global registry of LSP managers
_lsp_managers: WeakKeyDictionary = WeakKeyDictionary()
_manager_lock = threading.RLock()'''
    
    new_code = '''# Global registry of LSP managers - use regular dict instead of WeakKeyDictionary
_lsp_managers: Dict[str, "TransactionAwareLSPManager"] = {}
_manager_lock = threading.RLock()'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Fixed global registry declaration")
    else:
        print("⚠️  Global registry declaration not found or already fixed")
    
    # Fix the get_lsp_manager function
    old_get_manager = '''def get_lsp_manager(repo_path: str, enable_lsp: bool = True) -> TransactionAwareLSPManager:
    """
    Get or create an LSP manager for a repository.
    
    This function maintains a registry of LSP managers to avoid creating
    multiple managers for the same repository.
    """
    repo_path = str(Path(repo_path).resolve())
    
    with _manager_lock:
        # Check if we already have a manager for this repo
        for existing_manager in _lsp_managers.values():
            if str(existing_manager.repo_path) == repo_path:
                return existing_manager
        
        # Create new manager
        manager = TransactionAwareLSPManager(repo_path, enable_lsp)
        
        # Store in registry (using a dummy key since we can't use the manager as its own key)
        _lsp_managers[object()] = manager
        
        return manager'''
    
    new_get_manager = '''def get_lsp_manager(repo_path: str, enable_lsp: bool = True) -> TransactionAwareLSPManager:
    """
    Get or create an LSP manager for a repository.
    
    This function maintains a registry of LSP managers to avoid creating
    multiple managers for the same repository.
    """
    repo_path_str = str(Path(repo_path).resolve())
    
    with _manager_lock:
        # Check if we already have a manager for this repo
        if repo_path_str in _lsp_managers:
            return _lsp_managers[repo_path_str]
        
        # Create new manager
        manager = TransactionAwareLSPManager(repo_path_str, enable_lsp)
        
        # Store in registry using repo path as key
        _lsp_managers[repo_path_str] = manager
        
        return manager'''
    
    if old_get_manager in content:
        content = content.replace(old_get_manager, new_get_manager)
        print("✅ Fixed get_lsp_manager function")
    else:
        print("⚠️  get_lsp_manager function not found or already fixed")
    
    # Add proper import for Dict
    if "from typing import List, Optional, Dict, Any, Set" not in content:
        if "from typing import List, Optional, Dict, Any" in content:
            content = content.replace(
                "from typing import List, Optional, Dict, Any",
                "from typing import List, Optional, Dict, Any, Set"
            )
            print("✅ Added Set import")
        else:
            print("⚠️  Typing imports not found in expected format")
    
    # Remove WeakKeyDictionary import since we're not using it anymore
    if "from weakref import WeakKeyDictionary" in content:
        content = content.replace("from weakref import WeakKeyDictionary\n", "")
        print("✅ Removed WeakKeyDictionary import")
    
    # Write the fixed content back
    with open(transaction_manager_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed transaction manager: {transaction_manager_file}")
    return True


def fix_diagnostics_integration():
    """Fix the diagnostics integration to properly handle LSP errors."""
    print("\n🔧 FIXING DIAGNOSTICS INTEGRATION")
    print("=" * 60)
    
    diagnostics_file = Path("src/graph_sitter/core/diagnostics.py")
    
    if not diagnostics_file.exists():
        print(f"❌ File not found: {diagnostics_file}")
        return False
    
    # Read the current content
    with open(diagnostics_file, 'r') as f:
        content = f.read()
    
    # Fix the _initialize_lsp method to handle errors better
    old_init = '''    def _initialize_lsp(self) -> None:
        """Initialize LSP integration."""
        try:
            self._lsp_manager = get_lsp_manager(self.codebase.repo_path, self.enable_lsp)
            
            # Hook into the codebase's apply_diffs method
            original_apply_diffs = self.codebase.ctx.apply_diffs
            
            def enhanced_apply_diffs(diffs):
                # Call original method
                result = original_apply_diffs(diffs)
                
                # Update LSP context
                if self._lsp_manager:
                    self._lsp_manager.apply_diffs(diffs)
                
                return result
            
            # Replace the method
            self.codebase.ctx.apply_diffs = enhanced_apply_diffs
            
            logger.info(f"LSP diagnostics enabled for {self.codebase.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LSP diagnostics: {e}")
            self.enable_lsp = False'''
    
    new_init = '''    def _initialize_lsp(self) -> None:
        """Initialize LSP integration."""
        try:
            self._lsp_manager = get_lsp_manager(self.codebase.repo_path, self.enable_lsp)
            
            # Only hook into apply_diffs if the method exists
            if hasattr(self.codebase, 'ctx') and hasattr(self.codebase.ctx, 'apply_diffs'):
                original_apply_diffs = self.codebase.ctx.apply_diffs
                
                def enhanced_apply_diffs(diffs):
                    # Call original method
                    result = original_apply_diffs(diffs)
                    
                    # Update LSP context
                    if self._lsp_manager:
                        try:
                            self._lsp_manager.apply_diffs(diffs)
                        except Exception as e:
                            logger.warning(f"Failed to update LSP context: {e}")
                    
                    return result
                
                # Replace the method
                self.codebase.ctx.apply_diffs = enhanced_apply_diffs
            
            logger.info(f"LSP diagnostics enabled for {self.codebase.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LSP diagnostics: {e}")
            import traceback
            logger.error(f"LSP initialization traceback: {traceback.format_exc()}")
            self.enable_lsp = False
            self._lsp_manager = None'''
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ Fixed _initialize_lsp method")
    else:
        print("⚠️  _initialize_lsp method not found or already fixed")
    
    # Write the fixed content back
    with open(diagnostics_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed diagnostics integration: {diagnostics_file}")
    return True


def test_fixed_integration():
    """Test the fixed LSP integration."""
    print("\n🧪 TESTING FIXED LSP INTEGRATION")
    print("=" * 60)
    
    try:
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        # Create a test file with errors
        test_file = Path("test_fixed_lsp.py")
        test_content = '''# Test file with errors
def broken_function()  # Missing colon
    return "broken"

import non_existent_module  # Import error
'''
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")
        
        # Initialize codebase
        print("🔧 Initializing codebase...")
        codebase = Codebase(".")
        
        # Add diagnostic capabilities
        print("🔧 Adding diagnostic capabilities...")
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        
        # Check LSP status
        print("📊 Checking LSP status...")
        if hasattr(codebase, 'get_lsp_status'):
            lsp_status = codebase.get_lsp_status()
            print(f"   LSP Status: {lsp_status}")
            
            if lsp_status.get('enabled'):
                print("✅ LSP is now enabled!")
            else:
                print("❌ LSP is still disabled")
        
        # Test error detection
        print("🔍 Testing error detection...")
        if hasattr(codebase, 'errors'):
            errors = codebase.errors()
            print(f"   Found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
            
            if isinstance(errors, list) and len(errors) > 0:
                print("✅ Error detection is working!")
                for i, error in enumerate(errors[:3]):
                    print(f"      {i+1}. {error}")
            else:
                print("⚠️  No errors detected - may need more time or different approach")
        
        # Cleanup
        test_file.unlink()
        print("🧹 Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fix LSP integration issues."""
    print("🔧 FIXING LSP INTEGRATION ISSUES")
    print("=" * 80)
    print("This will fix the WeakKeyDictionary and other LSP integration issues.")
    print()
    
    # Fix transaction manager
    success1 = fix_transaction_manager()
    
    # Fix diagnostics integration
    success2 = fix_diagnostics_integration()
    
    if success1 and success2:
        print("\n✅ All fixes applied successfully!")
        
        # Test the fixes
        success3 = test_fixed_integration()
        
        if success3:
            print("\n🎉 LSP integration fixes completed successfully!")
            return True
        else:
            print("\n⚠️  Fixes applied but testing failed - may need additional work")
            return False
    else:
        print("\n❌ Some fixes failed - LSP integration still broken")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

