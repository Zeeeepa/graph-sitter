# Testing Guide for Graph-Sitter

This document provides guidance on running tests for the Graph-Sitter project, including how to handle memory-intensive tests that might cause segmentation faults.

## Quick Start

To run tests, use the `full_test.sh` script:

```bash
# Run unit tests (default)
./scripts/full_test.sh

# Run all tests
./scripts/full_test.sh --all

# Run with coverage
./scripts/full_test.sh --coverage

# Run specific tests
./scripts/full_test.sh --test=tests/unit/path/to/test.py
```

## Handling Memory Issues and Segmentation Faults

Some integration tests, particularly those involving large repositories like `mypy`, can consume significant memory and potentially cause segmentation faults. The `full_test.sh` script includes several fixes for these issues:

1. **Memory Monitoring**: The script monitors memory usage and gracefully terminates tests before they consume too much memory and cause a segmentation fault.

2. **Skip Large Repositories**: You can skip large repositories that are known to cause memory issues:

   ```bash
   ./scripts/full_test.sh --all --skip-large-repos
   ```

3. **Memory Limit**: You can set a custom memory limit (in GB):

   ```bash
   ./scripts/full_test.sh --all --max-memory-gb=24
   ```

4. **Reduce Parallel Workers**: You can reduce the number of parallel test workers to decrease memory usage:

   ```bash
   ./scripts/full_test.sh --all --cores=4
   ```

## Interactive Mode

Running `./scripts/full_test.sh` without arguments enters interactive mode, which guides you through:

1. Selecting which tests to run (unit, integration, all, or specific)
2. Setting the number of parallel processes
3. Enabling/disabling coverage
4. Enabling/disabling verbose output
5. Providing a GitHub token for tests that require authentication
6. Skipping large repositories to prevent segmentation faults
7. Setting a maximum memory limit

## Common Issues and Solutions

### Segmentation Faults

If you encounter segmentation faults during testing:

1. Try running with `--skip-large-repos` to skip memory-intensive repositories
2. Reduce the number of parallel workers with `--cores=4` or lower
3. Increase the memory limit if your system has enough RAM: `--max-memory-gb=40`
4. Run only unit tests: `./scripts/full_test.sh --unit`

### Coverage Errors

If you encounter SQLite errors when running with coverage:

1. Run without coverage (`./scripts/full_test.sh` without `--coverage`)
2. The script already includes fixes for common coverage issues, but some edge cases might still occur

### GitHub Authentication

Some integration tests require GitHub authentication. You can provide a GitHub token:

```bash
export GITHUB_TOKEN=your_github_token
./scripts/full_test.sh --all
```

Or use interactive mode and enter the token when prompted.

## Advanced Usage

### Running Specific Test Categories

```bash
# Run only integration tests
./scripts/full_test.sh --integration

# Run both unit and integration tests
./scripts/full_test.sh --unit --integration

# Run with verbose output
./scripts/full_test.sh --verbose
```

### Memory Monitoring

The script includes a memory monitor that tracks memory usage during test execution. If memory usage exceeds the specified limit, the tests will be gracefully terminated to prevent segmentation faults.

You can adjust the memory limit with the `--max-memory-gb` option or in interactive mode.

