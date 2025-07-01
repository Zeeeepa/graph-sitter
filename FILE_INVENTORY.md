# File Inventory and Dependency Map

## Complete File Listing

### clients/ (1 file)
- **linear.py** - Linear API client with basic CRUD operations
  - Dependencies: `requests`, `pydantic`, `graph_sitter.shared.logging`
  - Purpose: HTTP client for Linear API
  - Risk: Low - Can be moved to Linear service

### events/ (8 files)
- **contexten_app.py** - Main application orchestrator
  - Dependencies: `fastapi`, `graph_sitter.Codebase`, local services
  - Imports: `./github`, `./linear`, `./slack`
  - Purpose: Central FastAPI app that coordinates all services
  - Risk: Medium - Central hub, needs careful refactoring

- **interface.py** - Protocol definitions for event handlers
  - Dependencies: `typing.Protocol`, `modal`
  - Purpose: Defines EventHandlerManagerProtocol interface
  - Risk: Low - Pure interface definition

- **client.py** - HTTP client utilities
  - Dependencies: `httpx`, `pydantic`
  - Purpose: Generic HTTP client functionality
  - Risk: Low - Utility class

- **github.py** - GitHub event handler
  - Dependencies: `github`, `fastapi`, local github types
  - Imports: `contexten.extensions.events.interface`, `contexten.extensions.github.types.base`
  - Purpose: Handles GitHub webhook events
  - Risk: Medium - Should move to Github service

- **linear.py** - Linear event handler
  - Dependencies: `pydantic`, local linear components
  - Imports: `contexten.extensions.events.interface`, `contexten.extensions.linear.*`
  - Purpose: Handles Linear webhook events
  - Risk: Medium - Should move to Linear service

- **slack.py** - Slack event handler
  - Dependencies: `slack_sdk`, local slack types
  - Imports: `contexten.extensions.events.interface`, `contexten.extensions.slack.types`
  - Purpose: Handles Slack webhook events
  - Risk: Medium - Should move to Slack service

- **github_types.py** - GitHub type definitions
  - Dependencies: `datetime`, `typing`
  - Purpose: Basic GitHub data types
  - Risk: Low - Should move to Github service

- **modal/** - Modal deployment utilities
  - **base.py** - Modal app base class
    - Dependencies: `modal`, `fastapi`, local contexten_app
    - Purpose: Base class for Modal deployments
    - Risk: Medium - Core infrastructure
  - **request_util.py** - FastAPI request utilities
    - Dependencies: `fastapi`, `json`
    - Purpose: Request processing utilities
    - Risk: Low - Utility functions

### github/ (15 files)
- **__init__.py** - Empty package initializer
- **types/** - Type definitions for GitHub API
  - **__init__.py** - Empty package initializer
  - **base.py** - Base GitHub types (Repository, User, etc.)
  - **author.py** - GitHub author type
  - **commit.py** - GitHub commit type
  - **enterprise.py** - GitHub enterprise type
  - **installation.py** - GitHub installation type
  - **label.py** - GitHub label type
  - **organization.py** - GitHub organization type
  - **pull_request.py** - GitHub pull request type
  - **push.py** - GitHub push event type
  - **pusher.py** - GitHub pusher type
  - **events/** - GitHub event types
    - **pull_request.py** - Pull request event types
    - **push.py** - Push event types

**GitHub Service Analysis:**
- All files are type definitions using Pydantic
- Clean internal dependency hierarchy
- No external contexten dependencies
- Risk: Low - Well-contained, mostly data structures

### linear/ (9 files)
- **__init__.py** - Package exports
  - Exports: All public classes and functions
  - Purpose: Public API surface

- **types.py** - Linear data types
  - Dependencies: `pydantic`, `datetime`, `enum`
  - Purpose: Core Linear data structures
  - Risk: Low - Pure data types

- **config.py** - Configuration management
  - Dependencies: `os`, `dataclasses`, `pathlib`
  - Purpose: Linear integration configuration
  - Risk: Low - Configuration only

- **linear_client.py** - Core Linear API client
  - Dependencies: `requests`, local types
  - Imports: `contexten.extensions.linear.types`
  - Purpose: Basic Linear API operations
  - Risk: Low - Self-contained

- **enhanced_client.py** - Enhanced Linear client
  - Dependencies: `asyncio`, `json`, `datetime`, local config/types
  - Purpose: Advanced Linear API operations
  - Risk: Low - Uses relative imports

- **assignment_detector.py** - Assignment detection logic
  - Dependencies: `asyncio`, `re`, `datetime`, local config/types
  - Purpose: Detects issue assignments and mentions
  - Risk: Low - Uses relative imports

- **webhook_processor.py** - Webhook processing
  - Dependencies: `asyncio`, `hashlib`, `hmac`, `json`, local config/types
  - Purpose: Processes Linear webhook payloads
  - Risk: Low - Uses relative imports

- **workflow_automation.py** - Workflow automation
  - Dependencies: `asyncio`, `uuid`, `datetime`, local config/types
  - Purpose: Automates Linear workflows
  - Risk: Low - Uses relative imports

- **integration_agent.py** - Main integration logic
  - Dependencies: All other linear components
  - Purpose: Orchestrates Linear integration functionality
  - Risk: Low - Uses relative imports, well-contained

**Linear Service Analysis:**
- Excellent internal organization with relative imports
- Clear dependency hierarchy
- No external contexten dependencies except for events
- Risk: Low - Ready for service-oriented architecture

### mcp/ (3 files)
- **codebase_tools.py** - MCP server tools
  - Dependencies: `mcp.server.fastmcp`, `graph_sitter.core.codebase`
  - Imports: `contexten.agents.tools.reveal_symbol`, `contexten.agents.tools.search`
  - Purpose: Exposes codebase tools via MCP
  - Risk: Low - Good candidate for elevation

- **codebase_agent.py** - MCP agent functionality
  - Dependencies: `mcp.server.fastmcp`, `graph_sitter`
  - Imports: `contexten.agents.langchain.agent`
  - Purpose: Exposes agent functionality via MCP
  - Risk: Low - Good candidate for elevation

- **codebase_mods.py** - Code modification tools
  - Dependencies: `mcp.server.fastmcp`, `graph_sitter.core.codebase`
  - Purpose: Exposes code modification tools via MCP
  - Risk: Low - Good candidate for elevation

**MCP Analysis:**
- Independent functionality
- Depends on contexten.agents (outside extensions)
- Perfect candidate for elevation to parent level
- Risk: Low - No breaking changes expected

### slack/ (1 file)
- **types.py** - Slack type definitions
  - Dependencies: `typing`, `pydantic`
  - Purpose: Slack webhook and event types
  - Risk: Low - Pure type definitions

### swebench/ (1 file)
- **README.md** - Documentation only
  - Purpose: Documentation for SWE-bench integration
  - Risk: None - Can be removed or moved

## Dependency Graph

```
External Dependencies:
├── graph_sitter (logging, codebase, configs, git, enums)
├── pydantic (data validation)
├── fastapi (web framework)
├── requests (HTTP client)
├── modal (deployment)
├── slack_sdk (Slack API)
├── github (GitHub API)
└── mcp (Model Context Protocol)

Internal Dependencies:
events/contexten_app.py
├── → events/github.py
├── → events/linear.py
└── → events/slack.py

events/github.py
├── → events/interface.py
└── → github/types/base.py

events/linear.py
├── → events/interface.py
├── → linear/types.py
├── → linear/config.py
└── → linear/integration_agent.py

events/slack.py
├── → events/interface.py
└── → slack/types.py

linear/integration_agent.py
├── → linear/config.py
├── → linear/enhanced_client.py
├── → linear/webhook_processor.py
├── → linear/assignment_detector.py
├── → linear/workflow_automation.py
└── → linear/types.py

mcp/*.py
├── → contexten.agents.tools.*
└── → contexten.agents.langchain.*
```

## Critical Dependencies for Refactoring

### High Impact (Require Careful Handling)
1. **events/contexten_app.py** - Central orchestrator
2. **events/linear.py** - Linear event handler
3. **events/github.py** - GitHub event handler
4. **events/slack.py** - Slack event handler

### Medium Impact (Straightforward Moves)
1. **mcp/** folder - Can be elevated with import updates
2. **clients/linear.py** - Can be moved to Linear service
3. **events/interface.py** - Can be moved to core

### Low Impact (Minimal Changes)
1. **github/types/** - Self-contained type definitions
2. **linear/** service files - Already well-organized
3. **slack/types.py** - Single file, no dependencies
4. **swebench/** - Can be removed

## Import Update Checklist

### Files That Import From Extensions
- [ ] `examples/comprehensive_linear_integration.py`
- [ ] `examples/examples/codegen_app/app.py`
- [ ] `examples/examples/github_checks/app.py`
- [ ] `examples/examples/pr_review_bot/app.py`
- [ ] All documentation files
- [ ] Test files (if any)

### Internal Cross-References
- [ ] `events/contexten_app.py` → Update service imports
- [ ] `events/linear.py` → Update interface import
- [ ] `events/github.py` → Update interface import
- [ ] `events/slack.py` → Update interface import
- [ ] `events/modal/base.py` → Update contexten_app import
- [ ] `linear/linear_client.py` → Update types import
- [ ] `mcp/*.py` → Update agent imports

---

*Total Files: 40*  
*Total Directories: 11*  
*Risk Assessment: LOW to MEDIUM*

