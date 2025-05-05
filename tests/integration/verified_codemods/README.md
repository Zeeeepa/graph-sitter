# Verified Codemods Test Data

This directory contains test data for verified codemods integration tests.

## Directory Structure

- `codemod_data/`: Contains JSON files with metadata about codemods
- `verified_codemod_diffs/`: Contains expected diffs for verified codemods

## Running Tests

To run integration tests including verified codemods tests:

```bash
./scripts/run_tests.sh --integration
```

To skip verified codemods tests (recommended for development):

```bash
./scripts/run_tests.sh --unit
```

## Adding Test Data

To add test data for verified codemods:

1. Create a JSON file in `codemod_data/` with the appropriate metadata
2. Add expected diffs in `verified_codemod_diffs/`
3. Update `repo_commits.json` with repository information

See existing test data for examples of the required format.

