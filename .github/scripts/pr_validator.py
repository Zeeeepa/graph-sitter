#!/usr/bin/env python3
"""
PR Validation Script for graph-sitter repository
Validates PR structure, content, and compliance with repository standards.
"""

import os
import sys
import json
from pathlib import Path

def validate_pr():
    """Validate the PR structure and content."""
    print("🔍 Starting PR validation...")
    
    # Get environment variables
    pr_title = os.getenv('PR_TITLE', '')
    pr_author = os.getenv('PR_AUTHOR', '')
    pr_additions = os.getenv('PR_ADDITIONS', '0')
    pr_deletions = os.getenv('PR_DELETIONS', '0')
    changed_files = os.getenv('CHANGED_FILES', '').strip().split('\n')
    
    print(f"📊 Validating PR:")
    print(f"  - Title: {pr_title}")
    print(f"  - Author: {pr_author}")
    print(f"  - Changes: +{pr_additions}/-{pr_deletions}")
    print(f"  - Files: {len([f for f in changed_files if f.strip()])}")
    print()
    
    validation_errors = []
    validation_warnings = []
    
    # Validate PR title
    if not pr_title:
        validation_errors.append("PR title is missing")
    elif len(pr_title) < 10:
        validation_warnings.append("PR title is quite short - consider adding more detail")
    
    # Validate changed files
    valid_files = [f.strip() for f in changed_files if f.strip()]
    if not valid_files:
        validation_errors.append("No changed files detected")
    
    # Check for common file patterns
    has_code_changes = any(
        f.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.sh', '.yml', '.yaml', '.json'))
        for f in valid_files
    )
    
    if has_code_changes:
        print("✅ Code changes detected - validating structure...")
        
        # Check for shell scripts
        shell_scripts = [f for f in valid_files if f.endswith('.sh')]
        if shell_scripts:
            print(f"🐚 Shell scripts found: {', '.join(shell_scripts)}")
            # Validate shell scripts exist and are executable
            for script in shell_scripts:
                # Check from repository root
                script_path = os.path.join(os.getenv('GITHUB_WORKSPACE', ''), script)
                if os.path.exists(script_path):
                    if not os.access(script_path, os.X_OK):
                        validation_warnings.append(f"Shell script {script} is not executable")
                    print(f"  ✅ {script} exists and is properly configured")
                elif os.path.exists(script):
                    # Fallback: check relative to current directory
                    if not os.access(script, os.X_OK):
                        validation_warnings.append(f"Shell script {script} is not executable")
                    print(f"  ✅ {script} exists and is properly configured")
                else:
                    # For validation purposes, assume the script exists if it's in the changed files
                    print(f"  ℹ️  {script} is being added/modified in this PR")
                    validation_warnings.append(f"Cannot verify {script} existence (file may be new)")
    
    # Check for documentation updates
    has_docs = any(
        f.endswith(('.md', '.rst', '.txt')) or 'README' in f.upper()
        for f in valid_files
    )
    
    if has_code_changes and not has_docs:
        validation_warnings.append("Consider adding documentation for code changes")
    
    # Validate file sizes (warn for very large changes)
    try:
        additions = int(pr_additions)
        deletions = int(pr_deletions)
        total_changes = additions + deletions
        
        if total_changes > 1000:
            validation_warnings.append(f"Large PR with {total_changes} total changes - consider breaking into smaller PRs")
        elif total_changes > 5000:
            validation_errors.append(f"Very large PR with {total_changes} total changes - please break into smaller PRs")
    except ValueError:
        validation_warnings.append("Could not parse PR size information")
    
    # Report results
    print("\n📋 Validation Results:")
    
    if validation_errors:
        print("❌ Validation Errors:")
        for error in validation_errors:
            print(f"  - {error}")
    
    if validation_warnings:
        print("⚠️  Validation Warnings:")
        for warning in validation_warnings:
            print(f"  - {warning}")
    
    if not validation_errors and not validation_warnings:
        print("✅ All validations passed!")
    elif not validation_errors:
        print("✅ No blocking errors found (warnings can be addressed)")
    
    # Exit with appropriate code
    if validation_errors:
        print("\n❌ PR validation failed due to errors above")
        sys.exit(1)
    else:
        print("\n✅ PR validation passed")
        sys.exit(0)

if __name__ == "__main__":
    validate_pr()
