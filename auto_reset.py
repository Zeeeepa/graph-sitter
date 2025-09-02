#!/usr/bin/env python3
"""
Automatic script to reset a GitHub repository branch to match its upstream parent.
Uses GITHUB_TOKEN environment variable without prompting.
"""

import os
import sys
import subprocess
import tempfile
import shutil

# Configuration - change these values as needed
REPO_URL = "https://github.com/Zeeeepa/graph-sitter.git"
UPSTREAM_URL = "https://github.com/codegen-sh/graph-sitter.git"
BRANCH = "develop"

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result

def main():
    # Get token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return 1
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"Working in temporary directory: {temp_dir}")
    
    try:
        # Set up Git authentication
        env = os.environ.copy()
        env["GIT_ASKPASS"] = "echo"
        env["GIT_USERNAME"] = "x-access-token"
        env["GIT_PASSWORD"] = token
        
        # Clone repository
        clone_url = REPO_URL.replace("https://", f"https://x-access-token:{token}@")
        run_command(f"git clone {clone_url} .", cwd=temp_dir)
        
        # Add upstream remote
        upstream_url = UPSTREAM_URL
        run_command(f"git remote add upstream {upstream_url}", cwd=temp_dir)
        
        # Fetch from upstream
        run_command("git fetch upstream", cwd=temp_dir)
        
        # Reset to upstream
        run_command(f"git checkout {BRANCH}", cwd=temp_dir)
        run_command(f"git reset --hard upstream/{BRANCH}", cwd=temp_dir)
        
        # Push to origin
        origin_url = REPO_URL.replace("https://", f"https://x-access-token:{token}@")
        run_command(f"git remote set-url origin {origin_url}", cwd=temp_dir)
        result = run_command(f"git push origin {BRANCH} --force", cwd=temp_dir)
        
        if result.returncode == 0:
            print("Successfully reset and pushed branch")
            # Get current HEAD commit
            head = run_command("git log -1 --oneline", cwd=temp_dir)
            print(f"Current HEAD: {head.stdout.strip()}")
        else:
            print("Failed to push changes")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

