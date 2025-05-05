# Testing Guide for Graph-Sitter

This document provides guidance on running tests for the Graph-Sitter project, including how to handle memory-intensive tests that might cause segmentation faults.

## Running Tests

To run tests, use the `full_test.sh` script:

```bash
# Run unit tests (default)
./scripts/full_test.sh

# Run all tests
./scripts/full_test.sh --all

# Run with coverage
./scripts/full_test.sh --coverage

# Run specific test file or directory
./scripts/full_test.sh --test=tests/unit/path/to/test.py
```

## Handling Memory Issues and Segmentation Faults

Some integration tests, particularly those involving large repositories like `mypy`, can consume significant memory and potentially cause segmentation faults. The `full_test.sh` script includes several fixes for these issues:

1. **Memory Monitoring**: The script monitors memory usage and gracefully terminates tests before they consume too much memory and cause a segmentation fault.

2. **Skip Large Repositories**: You can skip large repositories that are known to cause memory issues:

```bash
./scripts/full_test.sh --all --skip-large-repos
```

3. **Configure Memory Limit**: You can set a custom memory limit (in GB):

```bash
./scripts/full_test.sh --all --max-memory-gb=24
```

4. **Adjust Parallel Processes**: You can reduce the number of parallel processes to decrease memory usage:

```bash
./scripts/full_test.sh --all --cores=4
```

5. **Force All Tests**: If you want to run ALL tests including memory-intensive ones:

```bash
./scripts/full_test.sh --force-all
```

6. **Incremental Testing**: Run tests one by one to avoid memory issues:

```bash
./scripts/full_test.sh --all --incremental
```

7. **Retry Failed Tests**: Set the number of retries for tests that fail:

```bash
./scripts/full_test.sh --all --retry=5
```

## Interactive Mode

Running `./scripts/full_test.sh` without arguments enters interactive mode, which guides you through:

1. Selecting test type (unit, integration, all, specific, or force all)
2. Setting the number of CPU cores for parallel testing
3. Enabling/disabling coverage
4. Enabling/disabling verbose output
5. Providing GitHub authentication for integration tests
6. Configuring memory limits
7. Enabling incremental testing
8. Setting retry count for failed tests

## Test Types

The script supports different test types:

```bash
# Run unit tests
./scripts/full_test.sh --unit

# Run integration tests
./scripts/full_test.sh --integration

# Run both unit and integration tests
./scripts/full_test.sh --unit --integration

# Run with verbose output
./scripts/full_test.sh --verbose
```

## Segmentation Faults

If you encounter segmentation faults during testing:

1. **Increase Memory Limit**: Use `--max-memory-gb` to increase the memory limit.
2. **Reduce Parallel Processes**: Use `--cores` to reduce the number of parallel processes.
3. **Use Incremental Testing**: Use `--incremental` to run tests one by one.
4. **Skip Large Repositories**: Use `--skip-large-repos` to skip memory-intensive tests.
5. **Check Memory Usage**: The script creates memory usage logs in `/tmp/memory_usage_*.log` that you can analyze.

## GitHub Authentication

Some integration tests require GitHub authentication. You can provide a GitHub token:

```bash
export GITHUB_TOKEN=your_github_token
./scripts/full_test.sh --all
```

Or use interactive mode to enter the token when prompted.

## Memory Monitoring

The script includes a memory monitor that tracks memory usage during test execution. If memory usage exceeds the specified limit, the tests will be gracefully terminated to prevent segmentation faults.

## Retry Mechanism

The script includes a retry mechanism for tests that fail. By default, it will retry failed tests 3 times. You can adjust this with the `--retry` option:

```bash
./scripts/full_test.sh --all --retry=5
```

## Incremental Testing

For very large test suites or environments with limited memory, you can use incremental testing to run tests one by one:

```bash
./scripts/full_test.sh --all --incremental
```

This will run each test file individually, cleaning up between tests to prevent memory buildup.

## Running All Tests Without Skipping Any

If you want to run all tests without skipping any, including memory-intensive ones, use the `--force-all` option:

```bash
./scripts/full_test.sh --force-all
```

This will run all tests, including those that might cause segmentation faults. You may want to combine this with other options to manage memory usage:

```bash
./scripts/full_test.sh --force-all --max-memory-gb=48 --cores=4
```

Or use incremental testing to run all tests one by one:

```bash
./scripts/full_test.sh --force-all --incremental
```
