# Extensions Folder Structure

This document describes the new service-oriented folder structure for the contexten extensions module.

## New Service-Oriented Structure

The following new folders have been created to implement a clean service-oriented architecture:

### Service Folders

- **`Contexten/`** - Core functionality (contexten_app.py, clients/)
- **`Linear/`** - Linear service files and integrations
- **`Github/`** - GitHub service files and integrations  
- **`Slack/`** - Slack service files and integrations

### MCP Module

- **`src/contexten/mcp/`** - MCP (Model Context Protocol) moved to parent level for better organization

## Legacy Folders (To Be Refactored)

The following existing folders will be reorganized in subsequent phases:

- `clients/` - Will be moved to appropriate service folders
- `events/` - Service-specific files will be moved to respective service folders
- `github/` - Will be consolidated with new `Github/` folder
- `linear/` - Will be consolidated with new `Linear/` folder
- `slack/` - Will be consolidated with new `Slack/` folder
- `swebench/` - To be removed (redundant)
- `mcp/` - Already moved to parent level

## Implementation Status

✅ **Phase 2 Complete**: New folder structure created
- [x] Created `Contexten/`, `Linear/`, `Github/`, `Slack/` folders
- [x] Created `src/contexten/mcp/` at parent level
- [x] Added basic `__init__.py` files
- [x] Documented folder structure

## Next Steps

The following phases will handle file movement and import updates:
- Phase 3: Move core files to appropriate service folders
- Phase 4: Update imports and dependencies
- Phase 5: Remove redundant folders

