#!/usr/bin/env python3
"""
Test RefactoringResult constructor fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter.extensions.serena.types import RefactoringResult, RefactoringType, RefactoringChange, RefactoringConflict

def test_refactoring_result_constructor():
    """Test that RefactoringResult can be constructed with all expected parameters."""
    
    print("🧪 Testing RefactoringResult constructor...")
    
    # Test basic constructor
    try:
        result = RefactoringResult(
            success=True,
            refactoring_type=RefactoringType.RENAME,
            changes=[],
            conflicts=[]
        )
        print("   ✅ Basic constructor works")
    except Exception as e:
        print(f"   ❌ Basic constructor failed: {e}")
        return False
    
    # Test with warnings parameter (previously failing)
    try:
        result = RefactoringResult(
            success=False,
            refactoring_type=RefactoringType.RENAME,
            changes=[],
            conflicts=[],
            warnings=["Test warning"]
        )
        print("   ✅ Constructor with warnings works")
    except Exception as e:
        print(f"   ❌ Constructor with warnings failed: {e}")
        return False
    
    # Test with preview_available parameter (previously failing)
    try:
        result = RefactoringResult(
            success=True,
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            changes=[],
            conflicts=[],
            warnings=[],
            preview_available=True
        )
        print("   ✅ Constructor with preview_available works")
    except Exception as e:
        print(f"   ❌ Constructor with preview_available failed: {e}")
        return False
    
    # Test with error_message parameter (previously failing)
    try:
        result = RefactoringResult(
            success=False,
            refactoring_type=RefactoringType.RENAME,
            changes=[],
            conflicts=[],
            warnings=[],
            error_message="Test error"
        )
        print("   ✅ Constructor with error_message works")
    except Exception as e:
        print(f"   ❌ Constructor with error_message failed: {e}")
        return False
    
    # Test all parameters together
    try:
        result = RefactoringResult(
            success=True,
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            changes=[],
            conflicts=[],
            message="Test message",
            metadata={"test": "data"},
            warnings=["Warning 1", "Warning 2"],
            preview_available=True,
            error_message=None
        )
        print("   ✅ Constructor with all parameters works")
        
        # Test properties
        assert result.success == True
        assert result.refactoring_type == RefactoringType.EXTRACT_METHOD
        assert result.warnings == ["Warning 1", "Warning 2"]
        assert result.preview_available == True
        assert result.has_conflicts == False
        assert result.files_changed == []
        
        print("   ✅ All properties work correctly")
        
    except Exception as e:
        print(f"   ❌ Constructor with all parameters failed: {e}")
        return False
    
    print("🎉 All RefactoringResult tests passed!")
    return True

if __name__ == "__main__":
    success = test_refactoring_result_constructor()
    sys.exit(0 if success else 1)

