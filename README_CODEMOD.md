# Codemod Deduplication Tool

This tool performs intelligent deduplication and import management between `src/codegen` and `src/graph_sitter` directories.

## Features

- 🔍 **Comprehensive Analysis**: Scans both codebases to understand module structure
- 🎯 **Intelligent Deduplication**: Identifies overlapping modules and determines which version to keep based on features
- 🗑️ **Smart Removal**: Removes duplicates while preserving feature-rich versions in codegen
- 🔧 **Import Updates**: Updates imports in codegen to properly reference graph_sitter when appropriate
- 📚 **Library Preservation**: Leaves graph_sitter imports unchanged (as it's the library used by codegen)

## Usage

### Basic Usage
```bash
# Run the codemod (makes actual changes)
python codemod_deduplication_tool.py

# Dry run to see what would be changed
python codemod_deduplication_tool.py --dry-run

# Verbose output with detailed analysis
python codemod_deduplication_tool.py --verbose

# Dry run with verbose output (recommended first run)
python codemod_deduplication_tool.py --dry-run --verbose
```

### Options

- `--dry-run`: Show what would be done without making changes
- `--verbose`: Show detailed analysis and progress
- `--help`: Show help message

## How It Works

### 1. Module Analysis
The tool scans both `src/codegen` and `src/graph_sitter` directories to:
- Map all Python modules and their paths
- Analyze file features (size, classes, functions, imports, docstrings, comments)
- Calculate feature scores for comparison

### 2. Overlap Detection
For modules that exist in both directories, the tool:
- Compares feature scores between versions
- Keeps the version with more features in codegen (if significantly better)
- Otherwise uses the graph_sitter version

### 3. Deduplication
The tool removes duplicate files by:
- Removing files from graph_sitter where codegen has better versions
- Removing files from graph_sitter where graph_sitter has equivalent/better versions
- Cleaning up empty directories after file removal

### 4. Import Updates
Updates imports in codegen files to:
- Reference graph_sitter for shared modules that exist there
- Keep codegen imports for unique modules or feature-rich versions kept in codegen
- Maintain proper import hierarchy (graph_sitter as library, codegen as consumer)

## Example Output

```
🔧 COMPREHENSIVE CODEMOD FOR DEDUPLICATION
============================================================
🚀 Starting comprehensive deduplication...

🔍 Scanning module structure...
  📁 Codegen modules: 97
  📁 Graph_sitter modules: 470

🔍 Analyzing overlapping modules...
  📊 Overlapping modules: 7
    ✅ Keep in codegen: cli.commands.create.main - more features (score: 5363 vs 3723)
    ➡️ Use from graph_sitter: cli.mcp.resources.system_setup_instructions
    ✅ Keep in codegen: cli.mcp.server - more features (score: 4033 vs 2243)

🗑️ Removing duplicate files...
  ✅ Removed from graph_sitter: cli.commands.create.main
  ✅ Removed from graph_sitter: cli.mcp.resources.system_setup_instructions

🔧 Updating imports in codegen files...
  ✅ Updated: agents/code_agent.py
  ✅ Updated: cli/commands/run/run_cloud.py

📊 Import update summary:
  📝 Files updated: 93
  🔄 Total import changes: 189

✅ Deduplication completed!
```

## Safety Features

- **Dry Run Mode**: Test the tool without making changes using `--dry-run`
- **Verbose Logging**: See exactly what the tool is doing with `--verbose`
- **Feature-Based Decisions**: Keeps versions with more functionality
- **Error Handling**: Graceful handling of file system errors
- **Directory Validation**: Ensures you're running from the correct location

## Prerequisites

- Python 3.6+
- Must be run from the root of the graph-sitter repository
- Both `src/codegen` and `src/graph_sitter` directories must exist

## What Gets Changed

### Files Removed
- Duplicate files where one version is clearly better
- Empty directories after file removal

### Files Modified
- Python files in `src/codegen` with updated import statements
- Only imports that reference modules moved to graph_sitter

### Files Preserved
- All unique functionality in both codegen and graph_sitter
- Feature-rich versions are kept in codegen
- Graph_sitter files are never modified (import-wise)

## Troubleshooting

### "Must be run from the root of the graph-sitter repository"
Make sure you're in the directory that contains both `src/codegen` and `src/graph_sitter` folders.

### Permission Errors
Ensure you have write permissions to both source directories.

### Import Errors After Running
If you encounter import errors after running the tool, check:
1. The module actually exists in the expected location
2. The import path is correct
3. Run with `--verbose` to see detailed decisions

## Reverting Changes

If you need to revert changes:
1. Use git to restore the previous state: `git checkout HEAD -- src/`
2. Or restore from your backup if you made one before running

## Contributing

This tool was created by Codegen Bot for the graph-sitter project. For issues or improvements, please create an issue in the repository.

