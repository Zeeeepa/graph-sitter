# Enhanced Graph-Sitter Database Architecture

This directory contains the enhanced database schemas and initialization scripts for the graph-sitter system's **8 specialized databases**, specifically designed to support the complete GitHub project workflow orchestration.

## Overview

The enhanced graph-sitter system uses a **multi-database architecture** with 8 specialized databases, each optimized for specific domains and workflow stages:

| Database | Purpose | Key Features | Workflow Integration |
|----------|---------|--------------|---------------------|
| **Task DB** | Task management and workflow orchestration | Enhanced GitHub project workflow, requirements decomposition, Linear integration | ✅ Core workflow engine |
| **Projects DB** | Project management and repository tracking | Projects, repositories, team management, cross-project analytics | ✅ Project context |
| **Prompts DB** | Enhanced template management with Codegen SDK | Workflow-specific templates, prompt enhancement, accuracy boosting | ✅ Codegen SDK integration |
| **Codebase DB** | Code analysis results and metadata | Code elements, relationships, analysis runs, integration with adapters | ✅ Code analysis context |
| **Analytics DB** | OpenEvolve integration and step analysis | Real-time analytics, performance data, quality scoring | ✅ Performance monitoring |
| **Events DB** | Multi-source event tracking | GitHub, Linear, Notion, Slack event ingestion and aggregation | ✅ Event-driven workflow |
| **Learning DB** | Pattern recognition and improvement tracking | Learning models, training sessions, adaptations, evolution | ✅ Continuous improvement |
| **Workflows DB** | Complete workflow orchestration | End-to-end workflow management, stage tracking, integration coordination | ✅ **NEW** - Workflow orchestration |

## Complete Workflow Support

The enhanced architecture specifically supports your **GitHub Project Workflow**:

```
Project Selection → Requirements Input → Requirements Decomposition → 
Linear Issue Creation → Task Execution → PR Validation → Dev Branch Management → Completion
```

### Workflow Stages

1. **Project Selection**: GitHub project pinning and dashboard integration
2. **Requirements Input**: User requirements text input and saving
3. **Requirements Decomposition**: Codegen SDK-powered step breakdown
4. **Linear Integration**: Main issue and sub-issue creation
5. **Task Execution**: Step-by-step implementation with Codegen SDK
6. **PR Validation**: Code quality and requirements compliance checking
7. **Dev Branch Management**: Branch creation and merge coordination
8. **Completion**: Workflow finalization and cleanup

## Quick Start

### Prerequisites

- PostgreSQL 12+ installed and running
- TimescaleDB extension (optional, for time-series optimization)
- Sufficient permissions to create databases and users

### Setup All Enhanced Databases

Run the enhanced setup script to initialize all databases:

```bash
cd database
./setup_all_databases_enhanced.sh
```

### Environment Variables

You can customize the setup using environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_ADMIN_USER=postgres
export POSTGRES_ADMIN_PASSWORD=your_password

./setup_all_databases_enhanced.sh
```

## Enhanced Database Details

### 1. Enhanced Task DB (`task_db`)

**Purpose**: Comprehensive task management with **GitHub project workflow integration**.

**Enhanced Features**:
- **GitHub Projects Management**: Project pinning, dashboard integration
- **Requirements Decomposition**: Step-by-step breakdown with dependencies
- **Linear Integration**: Main issue and sub-issue tracking
- **PR Validation**: Code quality and compliance checking
- **Codegen SDK Integration**: Enhanced prompting and response tracking

**Key Tables**:
- `github_projects` - Dashboard project management
- `requirement_decompositions` - Requirements breakdown results
- `decomposed_steps` - Individual implementation steps
- `tasks` - Enhanced with workflow context
- `prompt_enhancements` - Prompt accuracy improvements

**User**: `task_user` / `task_secure_2024!`

### 2. Enhanced Prompts DB (`prompts_db`)

**Purpose**: **Codegen SDK-focused** template management with workflow-specific enhancements.

**Enhanced Features**:
- **Workflow-Specific Templates**: Templates for each workflow stage
- **Prompt Enhancement System**: Accuracy boosting, context injection
- **Codegen SDK Integration**: API token management, response tracking
- **Quality Metrics**: Factual accuracy, response quality scoring

**Key Tables**:
- `prompt_templates` - Enhanced with workflow stages and use cases
- `prompt_enhancements` - Accuracy and quality improvement rules
- `executions` - Codegen SDK execution tracking
- `prompt_collections` - Workflow-specific prompt sequences

**User**: `prompts_user` / `prompts_secure_2024!`

**Default Templates**:
- GitHub Project Analysis
- Requirements Decomposition
- PR Validation

### 3. **NEW** Workflows DB (`workflows_db`)

**Purpose**: **Complete workflow orchestration** and integration coordination.

**Features**:
- **End-to-End Workflow Management**: Complete GitHub project workflow
- **Stage Tracking**: Detailed progress through each workflow stage
- **Integration Coordination**: GitHub, Linear, Codegen SDK operations
- **Validation Checkpoints**: Quality control at each stage
- **Performance Monitoring**: Workflow metrics and analytics

**Key Tables**:
- `workflow_executions` - Main workflow tracking
- `workflow_stage_executions` - Individual stage progress
- `codegen_operations` - Codegen SDK operation tracking
- `linear_operations` - Linear integration operations
- `github_operations` - GitHub integration operations
- `workflow_validations` - Quality control checkpoints

**User**: `workflows_user` / `workflows_secure_2024!`

### 4-7. Other Enhanced Databases

All other databases (Projects, Codebase, Analytics, Events, Learning) remain as previously designed but with enhanced integration points for the workflow system.

## Codegen SDK Integration

### Enhanced Prompting System

The enhanced architecture provides **accurate and factual prompting** through:

1. **Context Injection**: Automatic context enhancement based on workflow stage
2. **Accuracy Boosters**: Validation instructions for factual accuracy
3. **Format Optimization**: Structured output for automated processing
4. **Workflow-Specific Templates**: Optimized prompts for each workflow stage

### API Token Management

- Secure encrypted storage of Codegen API tokens
- Organization-level token management
- Automatic token rotation support

### Response Tracking

- Complete execution tracking with quality metrics
- Accuracy verification and scoring
- Performance monitoring and optimization

## File Structure

```
database/
├── README_enhanced.md           # This enhanced documentation
├── init_databases_enhanced.sql  # Enhanced database and user creation
├── setup_all_databases_enhanced.sh  # Enhanced setup script
└── schemas/
    ├── 01_task_db_enhanced.sql      # Enhanced task database schema
    ├── 02_projects_db.sql           # Projects database schema
    ├── 03_prompts_db_enhanced.sql   # Enhanced prompts database schema
    ├── 04_codebase_db.sql           # Codebase database schema
    ├── 05_analytics_db.sql          # Analytics database schema
    ├── 06_events_db.sql             # Events database schema
    ├── 07_learning_db.sql           # Learning database schema
    └── 08_workflows_db.sql          # NEW - Workflows database schema
```

## Workflow Integration Points

### Dashboard Integration

The **Task DB** provides complete dashboard support:
- Project pinning and ordering
- Requirements input and saving
- Progress tracking and visualization
- Workflow stage monitoring

### Codegen SDK Integration

The **Prompts DB** provides enhanced Codegen SDK support:
- Workflow-specific prompt templates
- Automatic prompt enhancement
- Response quality tracking
- Accuracy verification

### Linear Integration

The **Workflows DB** coordinates Linear operations:
- Main issue creation from requirements
- Sub-issue creation from decomposed steps
- Issue status tracking and updates
- Cross-reference management

### GitHub Integration

The **Workflows DB** manages GitHub operations:
- Repository analysis and structure detection
- Development branch creation and management
- Pull request creation and validation
- Code quality assessment

## Database Connections (Enhanced)

| Database | User | Password | Purpose |
|----------|------|----------|---------|
| `task_db` | `task_user` | `task_secure_2024!` | Enhanced task management with workflow |
| `projects_db` | `projects_user` | `projects_secure_2024!` | Project tracking |
| `prompts_db` | `prompts_user` | `prompts_secure_2024!` | Enhanced template management |
| `codebase_db` | `codebase_user` | `codebase_secure_2024!` | Code analysis |
| `analytics_db` | `analytics_user` | `analytics_secure_2024!` | Analytics |
| `events_db` | `events_user` | `events_secure_2024!` | Event tracking |
| `learning_db` | `learning_user` | `learning_secure_2024!` | Learning/Evolution |
| `workflows_db` | `workflows_user` | `workflows_secure_2024!` | **NEW** - Workflow orchestration |

**Special Users:**
- `analytics_readonly` / `analytics_readonly_2024!` - Cross-database read access
- `graph_sitter_admin` / `admin_secure_2024!` - Database administration

## Workflow Monitoring

### Dashboard Views

- **Active Workflows**: Real-time workflow progress
- **Project Status**: GitHub project workflow stages
- **Step Execution**: Decomposed step progress
- **Integration Operations**: Codegen, Linear, GitHub operations

### Performance Metrics

- Workflow completion times
- Stage success rates
- Codegen SDK response quality
- Integration operation success rates

## Security Considerations (Enhanced)

- **API Token Security**: Encrypted storage of Codegen SDK tokens
- **Workflow Isolation**: Organization-level workflow separation
- **Integration Security**: Secure handling of GitHub and Linear credentials
- **Audit Logging**: Complete workflow operation tracking

## Troubleshooting (Enhanced)

### Common Workflow Issues

1. **Codegen SDK Integration**: Check API token configuration and organization ID
2. **Linear Integration**: Verify Linear API credentials and project access
3. **GitHub Integration**: Ensure repository access and webhook configuration
4. **Workflow Stalling**: Check stage validation requirements and dependencies

### Monitoring and Debugging

- **Workflow Execution Logs**: Detailed stage-by-stage execution tracking
- **Integration Operation Logs**: Specific operation success/failure tracking
- **Quality Metrics**: Prompt effectiveness and response quality monitoring
- **Performance Analytics**: Workflow timing and resource usage analysis

## Migration from Original Architecture

If migrating from the original 7-database architecture:

1. **Backup existing databases**
2. **Run enhanced initialization script**
3. **Migrate workflow-related data to new Workflows DB**
4. **Update application configuration for new database connections**
5. **Test workflow integration points**

---

This enhanced architecture provides complete support for your GitHub project workflow with robust Codegen SDK integration, accurate prompting, and comprehensive workflow orchestration. The system is designed to handle the complete lifecycle from project selection to completion with full automation and quality control.

For questions or issues, please refer to the main graph-sitter documentation or create an issue in the repository.

