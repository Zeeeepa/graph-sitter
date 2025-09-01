# Graph-Sitter Backend API Fix

## Issue Description

The Graph-Sitter Backend API script (`graph_sitter_backend.py`) has an issue with repository cloning. The script assumes that all repositories use `main` as their default branch, which causes failures when analyzing repositories that use different default branches (like `develop`, `master`, etc.).

The error appears as:

```
❌ Analysis failed: Clone failed: Git clone failed: Cloning into '/tmp/graph_sitter_7xr2unzp'...
warning: Could not find remote branch main to clone.
fatal: Remote branch main not found in upstream origin
```

## Solution

The fix involves modifying the `clone_repository` function to:

1. Automatically detect the default branch of a repository
2. Implement fallback mechanisms if the detection fails
3. Try common branch names if the specified branch doesn't exist

## How to Apply the Fix

Replace the existing `clone_repository` function in `graph_sitter_backend.py` with the improved version from `graph_sitter_backend_patch.py`.

### Option 1: Manual Replacement

1. Open `graph_sitter_backend.py` in your editor
2. Find the `clone_repository` function (around line 1230-1250)
3. Replace it with the function from `graph_sitter_backend_patch.py`

### Option 2: Using patch

```bash
# Create a patch file
diff -u graph_sitter_backend.py graph_sitter_backend_patch.py > fix_clone_repository.patch

# Apply the patch
patch graph_sitter_backend.py < fix_clone_repository.patch
```

## Testing

The fix has been tested with:

1. Automatic branch detection
2. Specific branch specification
3. Non-existent branch fallback behavior

All tests pass successfully, confirming that the fix works correctly.

## Benefits of the Fix

1. **Improved Reliability**: Works with repositories using any default branch name
2. **Better Error Handling**: Provides clear error messages and fallback mechanisms
3. **Automatic Detection**: Detects the default branch automatically, reducing the need for manual configuration
4. **Backward Compatibility**: Still works with the original API interface, no changes needed to calling code

## Implementation Details

The improved `clone_repository` function:

1. Uses `git ls-remote --symref` to detect the default branch
2. Falls back to common branch names if detection fails
3. Tries multiple branch names in sequence if the first attempt fails
4. As a last resort, tries cloning without specifying a branch

This ensures maximum compatibility with different repository configurations.

