# Codemods

This directory contains code modification tools (codemods) for automated refactoring.

`{codemod_folder} = src/graph_sitter/adapters/analysis/codemods/{type}/{name}`

## Repos

These are the inputs to run it against.
To add a test case, create a folder called `{codemod_folder}/test_{repo_name}`

### JSON test cases

Add a repo to the repos folder or use an existing one. Use the current ones as reference

### Local Test Cases

Add a folder to the test folder containing the original state of the repository
`{codemod_tests_folder}/test_{repo_name}/original`. Then add files (
ie: `{codemod_tests_folder}/test_{repo_name}/original/codebase.py`) to test on.

## Expected outputs

### Diffs

Diffs are difficult to parse, but you can add `{codemod_tests_folder}/test_{repo_name}/expected_diff.patch`

### Files

You can add all the changed files to a folder called `{codemod_folder}/test_{repo_name}/expected`. The test runner will attempt to
convert the previous into this format.

### Leaving it blank

This will cause a warning but is helpful for performance testing

## Profiles

`.profiles` will have HTML profiles for each codemod/test case. These get overwritten on each run

## Diff output

`.diffs` will have HTML diffs for each codemod/test case. These get overwritten on each run
