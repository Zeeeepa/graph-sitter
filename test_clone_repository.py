#!/usr/bin/env python3
"""
Test script for the fixed clone_repository function
"""

import os
import shutil
import sys
from fixed_clone_repository import clone_repository

def test_clone_with_auto_detection():
    """Test cloning with automatic branch detection"""
    # Test with a repository that has 'develop' as the default branch
    repo_url = "https://github.com/Zeeeepa/graph-sitter"
    
    try:
        # Test auto-detection (no branch specified)
        repo_path = clone_repository(repo_url)
        print(f"✅ Successfully cloned repository to {repo_path}")
        
        # Verify that the repository was cloned correctly
        if os.path.exists(os.path.join(repo_path, ".git")):
            print("✅ Repository contains .git directory")
        else:
            print("❌ Repository does not contain .git directory")
        
        # Clean up
        shutil.rmtree(repo_path, ignore_errors=True)
        print("🧹 Cleaned up repository directory")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_clone_with_specific_branch():
    """Test cloning with a specific branch"""
    # Test with a repository and a specific branch
    repo_url = "https://github.com/Zeeeepa/graph-sitter"
    branch = "develop"  # Known to exist
    
    try:
        # Test with specific branch
        repo_path = clone_repository(repo_url, branch)
        print(f"✅ Successfully cloned repository with branch '{branch}' to {repo_path}")
        
        # Verify that the repository was cloned correctly
        if os.path.exists(os.path.join(repo_path, ".git")):
            print("✅ Repository contains .git directory")
        else:
            print("❌ Repository does not contain .git directory")
        
        # Clean up
        shutil.rmtree(repo_path, ignore_errors=True)
        print("🧹 Cleaned up repository directory")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_clone_with_nonexistent_branch():
    """Test cloning with a non-existent branch to verify fallback behavior"""
    # Test with a repository and a non-existent branch
    repo_url = "https://github.com/Zeeeepa/graph-sitter"
    branch = "nonexistent-branch"  # Known not to exist
    
    try:
        # Test with non-existent branch (should fall back to other branches)
        repo_path = clone_repository(repo_url, branch)
        print(f"✅ Successfully cloned repository despite non-existent branch '{branch}' to {repo_path}")
        
        # Verify that the repository was cloned correctly
        if os.path.exists(os.path.join(repo_path, ".git")):
            print("✅ Repository contains .git directory")
        else:
            print("❌ Repository does not contain .git directory")
        
        # Clean up
        shutil.rmtree(repo_path, ignore_errors=True)
        print("🧹 Cleaned up repository directory")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing clone_repository function with automatic branch detection...")
    auto_detection_result = test_clone_with_auto_detection()
    
    print("\n🧪 Testing clone_repository function with specific branch...")
    specific_branch_result = test_clone_with_specific_branch()
    
    print("\n🧪 Testing clone_repository function with non-existent branch...")
    nonexistent_branch_result = test_clone_with_nonexistent_branch()
    
    # Overall test result
    if auto_detection_result and specific_branch_result and nonexistent_branch_result:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

