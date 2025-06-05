# Phase 1: Dependency Analysis and Current Structure Report

## Executive Summary

This report provides a comprehensive analysis of the current file structure and import dependencies in `src/contexten/extensions/` as part of the refactoring initiative to implement a service-oriented architecture.

**Key Findings:**
- 40 Python files across 11 directories with mixed organizational patterns
- Clear service boundaries exist but are inconsistent with shared functional folders
- Low risk of breaking changes due to well-contained dependencies
- MCP folder is a good candidate for elevation to parent level

## Current File Structure

```
src/contexten/extensions/
├── clients/                    # 1 file
│   └── linear.py              # Linear API client
├── events/                     # 8 files - Central event handling
│   ├── contexten_app.py       # Main app orchestrator
│   ├── github.py              # GitHub event handler
│   ├── linear.py              # Linear event handler  
│   ├── slack.py               # Slack event handler
│   ├── client.py              # HTTP client utilities
│   ├── interface.py           # Event handler protocols
│   ├── github_types.py        # GitHub type definitions
│   └── modal/                 # Modal deployment utilities
│       ├── base.py
│       └── request_util.py
├── github/                     # 15 files - GitHub service
│   ├── __init__.py
│   └── types/                 # Type definitions
│       ├── base.py, commit.py, label.py, etc.
│       └── events/
│           ├── pull_request.py
│           └── push.py
├── linear/                     # 9 files - Linear service
│   ├── __init__.py
│   ├── linear_client.py       # Core client
│   ├── enhanced_client.py     # Enhanced functionality
│   ├── types.py               # Type definitions
│   ├── config.py              # Configuration
│   ├── integration_agent.py   # Main integration logic
│   ├── assignment_detector.py # Assignment detection
│   ├── webhook_processor.py   # Webhook handling
│   └── workflow_automation.py # Workflow automation
├── mcp/                        # 3 files - MCP server tools
│   ├── codebase_agent.py      # Agent functionality
│   ├── codebase_tools.py      # Tool definitions
│   └── codebase_mods.py       # Code modification tools
├── slack/                      # 1 file
│   └── types.py               # Slack type definitions
└── swebench/                   # 1 file
    └── README.md              # Documentation only
```

## Dependency Analysis

### 1. Cross-Service Dependencies

**Events → Services (High Coupling)**
```python
# events/contexten_app.py imports from all services
from .github import GitHub
from .linear import Linear  
from .slack import Slack

# events/linear.py imports from linear service
from contexten.extensions.linear.types import LinearEvent
from contexten.extensions.linear.config import get_linear_config
from contexten.extensions.linear.integration_agent import LinearIntegrationAgent

# events/github.py imports from github service
from contexten.extensions.github.types.base import GitHubInstallation, GitHubWebhookPayload

# events/slack.py imports from slack service
from contexten.extensions.slack.types import SlackWebhookPayload
```

**Services → Events (Medium Coupling)**
```python
# All event handlers import from events/interface.py
from contexten.extensions.events.interface import EventHandlerManagerProtocol
```

### 2. Internal Service Dependencies

**Linear Service (Well-Contained)**
- All files use relative imports within the service
- Strong internal cohesion with clear dependency chain:
  - `types.py` → Base types (no internal deps)
  - `config.py` → Configuration (no internal deps)  
  - `linear_client.py` → Uses types
  - `enhanced_client.py` → Uses config, types
  - `assignment_detector.py` → Uses config, types
  - `webhook_processor.py` → Uses config, types
  - `workflow_automation.py` → Uses config, types
  - `integration_agent.py` → Uses all above components
  - `__init__.py` → Exports all public interfaces

**GitHub Service (Type-Focused)**
- Primarily type definitions with minimal logic
- Clean internal hierarchy: base types → composite types → events
- No external dependencies within contexten

**Slack Service (Minimal)**
- Single types file with no internal dependencies

### 3. External Dependencies

**Graph-Sitter Dependencies (Consistent)**
```python
# Logging (used across all services)
from graph_sitter.shared.logging.get_logger import get_logger

# Core functionality (events and mcp)
from graph_sitter import Codebase
from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig

# Git operations (events/modal)
from graph_sitter.git.clients.git_repo_client import GitRepoClient
from graph_sitter.git.schemas.repo_config import RepoConfig

# Enums (mcp)
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
```

**Third-Party Dependencies**
- `pydantic`: Type validation (all services)
- `requests`: HTTP client (linear client)
- `fastapi`: Web framework (events)
- `modal`: Deployment platform (events/modal)
- `slack_sdk`: Slack integration (events/slack)
- `github`: GitHub API (events/github)

### 4. MCP Dependencies

**Contexten Agent Dependencies**
```python
from contexten.agents.tools import reveal_symbol
from contexten.agents.tools.search import search
from contexten.agents.langchain.agent import create_codebase_inspector_agent
```

## Risk Assessment

### Breaking Change Risk: **LOW**

| Component | Risk Level | Reason |
|-----------|------------|---------|
| Linear Service | Low | Well-contained with clear boundaries |
| GitHub Service | Low | Mostly type definitions, minimal logic |
| Slack Service | Low | Single file with no internal deps |
| Events Folder | Medium | Central hub but clear interfaces |
| MCP Folder | Low | Independent functionality |
| Clients Folder | Low | Single file, minimal dependencies |

### Refactoring Complexity: **MEDIUM**

**Easy Moves:**
- `mcp/` → `src/contexten/mcp/` (no breaking changes)
- `swebench/` → Remove (only README)
- `clients/linear.py` → `linear/client.py` (internal to linear)

**Moderate Complexity:**
- Service folders already well-organized
- Events folder needs careful handling of imports

**Challenging:**
- Updating import statements across codebase
- Ensuring all external references are updated

## Proposed Target Structure

```
src/contexten/
├── mcp/                       # Moved from extensions/mcp/
│   ├── codebase_agent.py
│   ├── codebase_tools.py
│   └── codebase_mods.py
└── extensions/
    ├── Contexten/             # Core functionality
    │   ├── contexten_app.py   # From events/
    │   ├── interface.py       # From events/
    │   ├── client.py          # From events/
    │   └── clients/           # Renamed from clients/
    │       └── linear.py      # Or move to Linear/
    ├── Linear/                # Linear service files
    │   ├── (all current linear/ files)
    │   └── events.py          # From events/linear.py
    ├── Github/                # GitHub service files  
    │   ├── (all current github/ files)
    │   └── events.py          # From events/github.py
    └── Slack/                 # Slack service files
        ├── types.py           # From slack/
        └── events.py          # From events/slack.py
```

## Import Update Requirements

### Files Requiring Import Updates

1. **External References** (outside extensions folder)
   - All example files importing from contexten.extensions
   - Documentation and tutorial files
   - Test files (if any)

2. **Internal Cross-References**
   - `events/contexten_app.py` → Update service imports
   - Service event handlers → Update interface imports
   - MCP files → Update agent tool imports

### Import Mapping Strategy

| Current Import | New Import |
|----------------|------------|
| `contexten.extensions.mcp.*` | `contexten.mcp.*` |
| `contexten.extensions.events.contexten_app` | `contexten.extensions.Contexten.contexten_app` |
| `contexten.extensions.events.linear` | `contexten.extensions.Linear.events` |
| `contexten.extensions.events.github` | `contexten.extensions.Github.events` |
| `contexten.extensions.events.slack` | `contexten.extensions.Slack.events` |
| `contexten.extensions.linear.*` | `contexten.extensions.Linear.*` |
| `contexten.extensions.github.*` | `contexten.extensions.Github.*` |
| `contexten.extensions.slack.*` | `contexten.extensions.Slack.*` |

## Files to be Moved

### Phase 1: MCP Elevation (Low Risk)
- `src/contexten/extensions/mcp/` → `src/contexten/mcp/`

### Phase 2: Service Consolidation (Medium Risk)
- `events/linear.py` → `Linear/events.py`
- `events/github.py` → `Github/events.py`  
- `events/slack.py` → `Slack/events.py`
- `clients/linear.py` → `Linear/client.py` (or keep in Contexten/)

### Phase 3: Core Restructuring (Medium Risk)
- `events/contexten_app.py` → `Contexten/contexten_app.py`
- `events/interface.py` → `Contexten/interface.py`
- `events/client.py` → `Contexten/client.py`
- `events/modal/` → `Contexten/modal/`

### Phase 4: Cleanup (Low Risk)
- Remove `swebench/` folder
- Update all import statements
- Update documentation

## Recommendations

1. **Start with MCP elevation** - Zero breaking changes, immediate benefit
2. **Implement service consolidation gradually** - One service at a time
3. **Update imports systematically** - Use automated tools where possible
4. **Maintain backward compatibility** - Consider deprecation warnings
5. **Test thoroughly** - Ensure all functionality remains intact

## Estimated Effort: 2-3 hours

- **Analysis**: ✅ Complete (1 hour)
- **MCP elevation**: 30 minutes
- **Service consolidation**: 1 hour  
- **Import updates**: 30-60 minutes
- **Testing and validation**: 30 minutes

## Next Steps

1. Review this analysis with stakeholders
2. Get approval for proposed structure
3. Begin with Phase 1 (MCP elevation)
4. Implement remaining phases incrementally
5. Update documentation and examples

---

*Generated on: 2025-06-05*  
*Analysis covers: 40 Python files, 11 directories*  
*Risk Level: LOW to MEDIUM*

