# Unified Module Structure Design

## Overview

This document outlines the proposed unified module structure that eliminates duplication while preserving the clean layered architecture between `graph_sitter` (foundation) and `codegen` (AI layer).

## Current State Analysis

### Module Statistics
- **Total Modules**: 562
- **Graph_sitter Modules**: 442 (78.6%)
- **Codegen Modules**: 120 (21.4%)
- **Overlapping Modules**: 2 (0.36%)

### Overlapping Modules Identified
1. `cli` - Empty __init__.py files
2. `cli._env` - Environment configuration (codegen version more feature-rich)

## Proposed Unified Structure

### 1. Foundation Layer: graph_sitter
**Purpose**: Core SDK for code analysis and manipulation
**Stability**: High - serves as stable foundation

```
src/graph_sitter/
├── core/                    # Core codebase analysis engine
│   ├── codebase.py         # Main Codebase class
│   ├── symbol.py           # Symbol manipulation
│   └── ...
├── codebase/               # File and project analysis
├── python/                 # Python language support
├── typescript/             # TypeScript language support
├── git/                    # Git integration
├── cli/                    # Core development CLI
│   ├── commands/           # Core commands (init, config, run, etc.)
│   ├── auth/              # Development authentication
│   └── utils/             # Core utilities
├── extensions/             # Core extensions
│   ├── lsp/               # Language Server Protocol
│   ├── index/             # Code indexing
│   └── attribution/       # Code attribution
└── shared/                 # Shared utilities and types
```

### 2. AI Integration Layer: codegen
**Purpose**: AI-powered development agents and external integrations
**Stability**: Medium - evolves with AI capabilities

```
src/codegen/
├── agents/                 # AI agent implementations
│   ├── code_agent.py      # Main code agent
│   ├── chat_agent.py      # Chat-based agent
│   └── utils.py           # Agent utilities
├── cli/                    # AI-focused CLI
│   ├── commands/          # AI commands (agent, deploy, expert, etc.)
│   ├── auth/              # External service authentication
│   └── workspace/         # Project workspace management
├── extensions/             # External integrations
│   ├── github/            # GitHub integration
│   ├── linear/            # Linear integration
│   ├── slack/             # Slack integration
│   ├── langchain/         # LangChain integration
│   └── events/            # Event handling system
└── sdk/                    # SDK for external usage
```

## Consolidation Implementation

### Phase 1: Eliminate Overlapping Modules

#### 1.1 Resolve `cli` Module Overlap
**Action**: Remove empty `__init__.py` from codegen, use graph_sitter version
**Impact**: None - both are empty files
**Implementation**:
```bash
rm src/codegen/cli/__init__.py
# Update imports to reference graph_sitter.cli where needed
```

#### 1.2 Resolve `cli._env` Module Overlap
**Action**: Keep codegen version (more feature-rich), remove graph_sitter version
**Rationale**: Codegen version has score 10 vs graph_sitter score 9
**Implementation**:
```bash
rm src/graph_sitter/cli/_env.py
# Update graph_sitter imports to reference codegen._env
```

### Phase 2: Create Unified CLI Interface

#### 2.1 Unified Entry Point
Create a new unified CLI that routes commands appropriately:

```python
# bin/graph-sitter (new unified entry point)
#!/usr/bin/env python3
"""
Unified Graph-Sitter CLI
Routes commands to appropriate modules based on functionality
"""

import sys
import argparse
from typing import List

# AI-focused commands route to codegen
AI_COMMANDS = {
    'agent', 'deploy', 'expert', 'serve', 
    'run-agent', 'create-app', 'login', 'logout'
}

# Core development commands route to graph_sitter
CORE_COMMANDS = {
    'init', 'config', 'run', 'list', 'lsp', 
    'notebook', 'reset', 'start', 'update'
}

def route_command(args: List[str]) -> None:
    """Route command to appropriate module."""
    if not args:
        show_help()
        return
    
    command = args[0]
    
    if command in AI_COMMANDS:
        from codegen.cli.cli import main as codegen_main
        codegen_main(args)
    elif command in CORE_COMMANDS:
        from graph_sitter.cli.cli import main as graph_sitter_main
        graph_sitter_main(args)
    elif command == 'ai':
        # Special namespace for AI commands
        if len(args) > 1:
            from codegen.cli.cli import main as codegen_main
            codegen_main(args[1:])
        else:
            show_ai_help()
    else:
        print(f"Unknown command: {command}")
        show_help()

def show_help():
    """Show unified help."""
    print("""
Graph-Sitter Unified CLI

CORE DEVELOPMENT COMMANDS:
  init          Initialize a new project
  config        Manage configuration
  run           Execute codemods
  list          List codebase elements
  lsp           Language server operations
  notebook      Jupyter integration
  reset         Reset workspace
  start         Start development server
  update        Update dependencies

AI-POWERED COMMANDS:
  agent         Run AI development agents
  deploy        Deploy applications
  expert        Get expert AI assistance
  serve         Start AI services
  login         Authenticate with external services
  logout        Sign out

AI NAMESPACE:
  ai <command>  Access AI commands with explicit namespace

For detailed help on any command:
  graph-sitter <command> --help
""")

if __name__ == '__main__':
    route_command(sys.argv[1:])
```

#### 2.2 Backward Compatibility
Maintain existing entry points for backward compatibility:
- `codegen` command continues to work
- `graph-sitter` command continues to work
- New unified `graph-sitter` becomes primary interface

### Phase 3: Shared Infrastructure Optimization

#### 3.1 Authentication Consolidation
Create shared authentication system for common services:

```python
# src/shared/auth/unified_auth.py
class UnifiedAuthManager:
    """Manages authentication across both modules."""
    
    def __init__(self):
        self.codegen_auth = CodegenAuthManager()
        self.graph_sitter_auth = GraphSitterAuthManager()
    
    def get_github_token(self) -> str:
        """Get GitHub token from either auth system."""
        return (self.codegen_auth.get_github_token() or 
                self.graph_sitter_auth.get_github_token())
    
    def get_linear_token(self) -> str:
        """Get Linear token from codegen auth."""
        return self.codegen_auth.get_linear_token()
```

#### 3.2 Configuration Unification
Create shared configuration system:

```python
# src/shared/config/unified_config.py
class UnifiedConfig:
    """Unified configuration for both modules."""
    
    def __init__(self):
        self.graph_sitter_config = GraphSitterConfig()
        self.codegen_config = CodegenConfig()
    
    def get_workspace_path(self) -> Path:
        """Get workspace path with fallback logic."""
        return (self.codegen_config.workspace_path or 
                self.graph_sitter_config.workspace_path or
                Path.cwd())
```

## Migration Strategy

### Step 1: Apply Automated Deduplication
```bash
# Run the existing deduplication tool
python codemod_deduplication_tool.py --verbose

# Verify changes
git diff --name-only
git status
```

### Step 2: Implement Unified CLI
1. Create new unified entry point script
2. Update package configuration to use unified CLI
3. Add routing logic for command dispatch
4. Maintain backward compatibility aliases

### Step 3: Update Documentation
1. Update README files to reference unified CLI
2. Create migration guide for existing users
3. Document the layered architecture
4. Provide workflow examples

### Step 4: Testing and Validation
1. Test all existing workflows with unified CLI
2. Verify backward compatibility
3. Test cross-module integrations
4. Validate user experience improvements

## Benefits of Unified Structure

### For Users
- **Single Entry Point**: One CLI to learn and use
- **Clear Command Organization**: Logical grouping of functionality
- **Contextual Help**: Better guidance on which commands to use
- **Seamless Workflows**: Easy transition between core and AI operations

### For Developers
- **Reduced Duplication**: Eliminate the 2 overlapping modules
- **Clear Architecture**: Maintain clean layered design
- **Better Maintainability**: Centralized CLI logic
- **Extensibility**: Easy to add new commands and features

### For the Project
- **Improved Onboarding**: Clearer entry point for new users
- **Better Documentation**: Unified documentation structure
- **Reduced Confusion**: Clear separation of concerns
- **Future Growth**: Scalable architecture for new features

## Implementation Timeline

### Week 1: Foundation
- Apply deduplication tool
- Create unified CLI entry point
- Basic command routing

### Week 2: Integration
- Implement shared authentication
- Create unified configuration
- Update documentation

### Week 3: Testing
- Comprehensive testing of all workflows
- User acceptance testing
- Performance validation

### Week 4: Deployment
- Gradual rollout with feature flags
- Monitor user feedback
- Address any issues

## Success Criteria

### Technical Metrics
- ✅ Zero overlapping modules
- ✅ 100% backward compatibility maintained
- ✅ All existing functionality preserved
- ✅ Unified CLI routes commands correctly

### User Experience Metrics
- 📈 Reduced time to first successful command
- 📈 Decreased support requests about CLI confusion
- 📈 Improved user satisfaction scores
- 📈 Faster onboarding for new developers

## Risk Mitigation

### Potential Risks
1. **Breaking Changes**: CLI changes might break existing scripts
2. **Performance Impact**: Command routing might add latency
3. **Complexity**: Unified CLI might become complex to maintain

### Mitigation Strategies
1. **Backward Compatibility**: Maintain all existing entry points
2. **Performance Testing**: Benchmark command routing overhead
3. **Modular Design**: Keep routing logic simple and well-tested
4. **Gradual Migration**: Allow users to migrate at their own pace

## Conclusion

The unified module structure design preserves the strong architectural foundations while eliminating duplication and improving user experience. The layered architecture remains intact, with clear separation between the core SDK (graph_sitter) and AI integration layer (codegen).

The implementation focuses on interface unification rather than module merging, ensuring we maintain the benefits of the current architecture while addressing the identified issues.

