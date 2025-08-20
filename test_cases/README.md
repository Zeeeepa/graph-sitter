# Test Cases for Codebase Analysis Tool

This directory contains test cases for validating the codebase analysis tool. The test cases cover various edge cases and scenarios to ensure the tool works correctly in all situations.

## Running the Tests

To run all tests:

```bash
python run_tests.py
```

## Test Cases

The following test cases are included:

1. **Empty Repository**: Tests how the tool handles an empty repository with no files.
2. **Single File**: Tests a repository with a single Python file.
3. **Circular Imports**: Tests detection of circular import dependencies.
4. **Dead Code**: Tests detection of unused functions and classes.
5. **Complex Inheritance**: Tests analysis of complex class inheritance hierarchies.
6. **Syntax Error**: Tests how the tool handles files with syntax errors.
7. **Large File**: Tests performance with a large file containing many functions.
8. **Mixed Languages**: Tests how the tool handles repositories with multiple programming languages.
9. **Nested Directories**: Tests analysis of repositories with nested directory structures.
10. **Dynamic Imports**: Tests detection and analysis of dynamic imports.
11. **Metaclasses**: Tests analysis of Python metaclasses.
12. **Decorators**: Tests analysis of Python decorators.

## Validation Criteria

Each test case validates the following aspects of the analysis:

- **File Count**: The number of files detected in the repository.
- **Function Count**: The number of functions detected.
- **Class Count**: The number of classes detected.
- **Entry Points**: The number and correctness of detected entry points.
- **Dead Code**: The number and correctness of detected dead code items.
- **Issues**: The number and correctness of detected issues.
- **Import Cycles**: The number and correctness of detected import cycles.

## Adding New Test Cases

To add a new test case:

1. Create a new test function in `run_tests.py` following the pattern of existing tests.
2. Define the test repository structure using the `run_test_case` function.
3. Specify the expected analysis results.
4. Add the new test function to the `tests` list in the `run_all_tests` function.

## Test Case Structure

Each test case follows this structure:

```python
def test_example():
    """Test case description."""
    return run_test_case(
        "example_name",  # Name of the test case
        {
            "file1.py": "file content",  # Files to create
            "file2.py": "file content",
        },
        {
            "summary": {
                "total_files": 2,  # Expected summary stats
                "total_functions": 3,
                "total_classes": 1,
            },
            "entrypoints": 2,  # Expected entry point count
            "dead_code": 1,  # Expected dead code count
            "issues": 0,  # Expected issue count
            "import_cycles": 0  # Expected import cycle count
        }
    )
```
