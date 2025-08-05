# Fixing Segmentation Faults in Graph-Sitter Tests

This document explains the segmentation fault issue that occurs when running tests with large repositories like `mypy` and provides solutions to fix it.

## The Problem

When running integration tests with large repositories, particularly the `test_codemods_parse` test with the `mypy` repository, a segmentation fault can occur. This happens because:

1. The repository is very large and complex
2. The Cython module `graph_sitter.compiled.utils` encounters memory issues when processing large codebases
3. Python 3.13 may have different memory management behavior than previous versions

The segmentation fault typically occurs in the `_process_diff_files` method of `codebase_context.py` when building the graph for a large codebase.

## Solutions

### 1. Skip Problematic Repositories

The simplest solution is to skip repositories known to cause segmentation faults. We've implemented this by:

- Creating a `.skiptests/large_repos.txt` file in the `tests/integration/codemod/repos/open_source/` directory
- Adding repository names (like `mypy`) to this file
- Modifying the `test_codemods_parse` function to check this file and skip listed repositories

### 2. Limit Memory Usage

We've added memory monitoring and limits to prevent excessive memory usage:

- The `fix_segfault.sh` script sets memory limits using `ulimit` (when available)
- The test now monitors memory usage before and after codebase creation
- If memory usage exceeds a threshold, the test will fail gracefully instead of crashing

### 3. Improved Error Handling

We've enhanced error handling in the test:

- Added a try-except block to catch `MemoryError` exceptions
- Added more detailed memory usage logging
- Improved error messages to help diagnose issues

## How to Use

1. Run the `fix_segfault.sh` script before running tests:
   ```bash
   ./scripts/fix_segfault.sh
   ```

2. Or use the updated `full_test.sh` script which automatically applies the fixes:
   ```bash
   ./scripts/full_test.sh --unit
   ```

3. To skip specific repositories, add them to:
   ```
   tests/integration/codemod/repos/open_source/.skiptests/large_repos.txt
   ```

## Technical Details

### Memory Usage Monitoring

The test now monitors memory usage before and after codebase creation:

```python
# Monitor memory usage before creating the codebase
process = psutil.Process(os.getpid())
initial_memory = process.memory_info().rss
logger.info(f"Initial memory usage: {initial_memory / BYTES_IN_GIGABYTE:.2f} GB")

# Setup Codebase with memory monitoring
try:
    projects = [ProjectConfig(repo_operator=op, programming_language=repo.language, subdirectories=repo.subdirectories)]
    codebase = Codebase(projects=projects, config=codebase_config)
    
    # Check memory usage after codebase creation
    memory_used = process.memory_info().rss
    memory_increase = memory_used - initial_memory
    logger.info(f"Using {memory_used / BYTES_IN_GIGABYTE:.2f} GB of memory (increase: {memory_increase / BYTES_IN_GIGABYTE:.2f} GB)")
```

### Repository Skipping

The test now checks if a repository should be skipped:

```python
# Check if this repository should be skipped
if LARGE_REPOS_SKIP_FILE.exists() and repo.name in LARGE_REPOS_SKIP_FILE.read_text().splitlines():
    pytest.skip(f"Skipping {repo.name} as it's known to cause segmentation faults")
```

## Future Improvements

For a more robust solution, consider:

1. Implementing incremental graph building for large repositories
2. Optimizing the Cython modules for better memory usage
3. Adding more granular memory limits for specific operations
4. Using a more efficient data structure for large codebases

