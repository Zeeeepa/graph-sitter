#!/usr/bin/env python3
"""
Patch for the Graph-Sitter Backend API to fix repository cloning issues.

This script contains only the fixed clone_repository function that should replace
the existing function in the graph_sitter_backend.py file.
"""

def clone_repository(repo_url: str, branch: str = None) -> str:
    """
    Clone GitHub repository to temporary directory with automatic default branch detection.
    
    Args:
        repo_url: URL of the repository to clone
        branch: Optional branch name to checkout. If None, will detect the default branch.
    
    Returns:
        Path to the cloned repository
    
    Raises:
        Exception: If cloning fails
    """
    import os
    import tempfile
    import subprocess
    import shutil
    
    try:
        temp_dir = tempfile.mkdtemp(prefix="graph_sitter_")
        
        # First, try to detect the default branch if none is specified
        if branch is None:
            try:
                # Use git ls-remote to detect the default branch
                cmd = ["git", "ls-remote", "--symref", repo_url, "HEAD"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and result.stdout:
                    # Parse the output to extract the default branch name
                    # Example output: ref: refs/heads/develop  HEAD
                    for line in result.stdout.splitlines():
                        if "ref:" in line and "HEAD" in line:
                            # Extract branch name from refs/heads/branch_name
                            parts = line.split()
                            if len(parts) >= 2:
                                ref_path = parts[1]
                                if ref_path.startswith("refs/heads/"):
                                    branch = ref_path.replace("refs/heads/", "")
                                    print(f"✅ Detected default branch: {branch}")
                                    break
            
            except Exception as e:
                print(f"⚠️ Could not detect default branch: {e}")
                # Fall back to common branch names if detection fails
                branch = "main"  # First try main
        
        # If we still don't have a branch (detection failed), use fallback sequence
        if branch is None:
            branch = "main"  # Default fallback
        
        print(f"🔄 Cloning repository with branch: {branch}")
        
        # Try to clone with the specified/detected branch
        clone_cmd = ["git", "clone", "--depth", "1", "--branch", branch, repo_url, temp_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        # If the first attempt fails, try common fallback branches
        if result.returncode != 0:
            # Clean up the failed attempt
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = tempfile.mkdtemp(prefix="graph_sitter_")
            
            fallback_branches = ["master", "develop", "trunk", "default"]
            if branch in fallback_branches:
                fallback_branches.remove(branch)  # Don't try the same branch twice
            
            # Try each fallback branch
            for fallback in fallback_branches:
                print(f"🔄 First branch failed, trying fallback branch: {fallback}")
                clone_cmd = ["git", "clone", "--depth", "1", "--branch", fallback, repo_url, temp_dir]
                result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ Successfully cloned using fallback branch: {fallback}")
                    branch = fallback  # Update the branch name for reporting
                    break
            
            # If all fallbacks fail, try cloning without specifying a branch
            if result.returncode != 0:
                print("🔄 All branch attempts failed, trying to clone without branch specification")
                shutil.rmtree(temp_dir, ignore_errors=True)
                temp_dir = tempfile.mkdtemp(prefix="graph_sitter_")
                
                clone_cmd = ["git", "clone", "--depth", "1", repo_url, temp_dir]
                result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        # Final check if cloning succeeded
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        print(f"✅ Successfully cloned {repo_url} to {temp_dir} using branch {branch}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        raise Exception("Repository clone timed out")
    except Exception as e:
        raise Exception(f"Clone failed: {str(e)}")

# Usage example:
# repo_path = clone_repository("https://github.com/username/repo", branch="main")

