# Contexten Dead Code Analysis Report

## 📊 Summary

- **Total Files Analyzed**: 189
- **Potentially Dead Files**: 63
- **Entry Points**: 36
- **Core Feature Categories**: 16
- **Potential Duplicates**: 161
- **Missing Features**: 5

## 🚪 Entry Points (Files that are executed directly)

These files are definitely NOT dead code as they serve as entry points:

- `dashboard.py`
- `dashboard.py`
- `cli/cli.py`
- `agents/codegen_config.py`
- `extensions/contexten_app.py`
- `dashboard/project_manager.py`
- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/flow_manager.py`
- `dashboard/enhanced_routes.py`
- `dashboard/advanced_analytics.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/enhanced_codebase_ai.py`
- `dashboard/workflow_automation.py`
- `dashboard/orchestrator_integration.py`
- `dashboard/chat_manager.py`
- `mcp/server.py`
- `mcp/server.py`
- `mcp/server.py`
- `mcp/codebase/codebase_tools.py`
- `mcp/codebase/codebase_mods.py`
- `mcp/codebase/codebase_agent.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/main.py`
- `extensions/open_evolve/database_agent/agent.py`
- `cli/commands/serve/main.py`
- `cli/commands/serve/main.py`
- `cli/commands/expert/main.py`
- `cli/commands/run_on_pr/main.py`
- `cli/commands/agent/main.py`
- `cli/commands/create/main.py`
- `cli/commands/profile/main.py`
- `cli/commands/run/main.py`
- `cli/commands/login/main.py`
- `cli/commands/deploy/main.py`


## 💀 Potentially Dead Code (63 files)

These files are not imported by any other files and may be dead code:


### Agents (17 files)

- `agents/data.py`
- `agents/langchain/graph.py`
- `agents/tools/commit.py`
- `agents/tools/create_file.py`
- `agents/tools/delete_file.py`
- `agents/tools/edit_file.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/create_pr_comment.py`
- `agents/tools/github/create_pr_review_comment.py`
- `agents/tools/github/search.py`
- `agents/tools/list_directory.py`
- `agents/tools/move_symbol.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/rename_file.py`
- `agents/tools/run_codemod.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/view_file.py`

### Cli (5 files)

- `cli/commands/run/render.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/sdk/pull_request.py`
- `cli/workspace/initialize_workspace.py`

### Extensions (40 files)

- `extensions/client.py`
- `extensions/github/events/manager.py`
- `extensions/github/github.py`
- `extensions/github/github_types.py`
- `extensions/github/types/commit.py`
- `extensions/github/types/enterprise.py`
- `extensions/github/types/events/pull_request.py`
- `extensions/github/types/events/push.py`
- `extensions/github/types/organization.py`
- `extensions/github/types/pull_request.py`
- `extensions/github/types/push.py`
- `extensions/github/webhook/processor.py`
- `extensions/github/workflow/automation.py`
- `extensions/linear/assignment/detector.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/mutations.py`
- `extensions/linear/queries.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/validator.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/workflow/automation.py`
- `extensions/linear/workflow_automation.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/open_evolve/code_generator/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/prefect/client.py`
- `extensions/prefect/config.py`
- `extensions/prefect/notifications.py`
- `extensions/prefect/tasks.py`
- `extensions/prefect/workflows.py`
- `extensions/slack/slack.py`

### Orchestration (1 files)

- `orchestration/prefect_client.py`


## 🎯 Core Features Analysis


### Dashboard (128 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/custom_tool_node.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/__init__.py`
- ... and 118 more files

### Agents (139 files)

- `agents/__init__.py`
- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/data.py`
- `agents/langchain/__init__.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/prompts.py`
- ... and 129 more files

### Orchestration (57 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/prompts.py`
- `agents/tools/reflection.py`
- `cli/api/client.py`
- `cli/api/schemas.py`
- `cli/auth/login.py`
- `cli/commands/agent/main.py`
- `dashboard.py`
- ... and 47 more files

### Extensions (108 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/tools/linear/linear.py`
- `agents/tools/link_annotation.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/search.py`
- ... and 98 more files

### Linear (76 files)

- `agents/code_agent.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/__init__.py`
- `agents/tools/github/search.py`
- `agents/tools/linear/__init__.py`
- `agents/tools/linear/linear.py`
- `agents/tools/link_annotation.py`
- `cli/api/schemas.py`
- ... and 66 more files

### Github (82 files)

- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/tools.py`
- `agents/tools/__init__.py`
- `agents/tools/github/__init__.py`
- `agents/tools/github/checkout_pr.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/create_pr_comment.py`
- `agents/tools/github/create_pr_review_comment.py`
- `agents/tools/github/search.py`
- ... and 72 more files

### Slack (23 files)

- `agents/langchain/tools.py`
- `agents/tools/link_annotation.py`
- `cli/commands/serve/main.py`
- `dashboard.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`
- `dashboard/project_manager.py`
- `dashboard/workflow_automation.py`
- `extensions/client.py`
- `extensions/contexten_app.py`
- ... and 13 more files

### Cli (111 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/bash.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/linear/linear.py`
- ... and 101 more files

### Mcp (23 files)

- `agents/langchain/graph.py`
- `agents/loggers.py`
- `cli/api/client.py`
- `cli/commands/create/main.py`
- `cli/commands/expert/main.py`
- `cli/commands/run/run_cloud.py`
- `cli/commands/serve/main.py`
- `cli/utils/url.py`
- `dashboard.py`
- `dashboard/app.py`
- ... and 13 more files

### Shared (144 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/data.py`
- `agents/langchain/__init__.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- ... and 134 more files

### Logging (83 files)

- `agents/code_agent.py`
- `agents/loggers.py`
- `agents/tools/global_replacement_edit.py`
- `agents/tools/observation.py`
- `agents/tools/search.py`
- `agents/tools/search_files_by_name.py`
- `agents/tools/tool_output_types.py`
- `agents/tracer.py`
- `cli/api/schemas.py`
- `cli/auth/decorators.py`
- ... and 73 more files

### Config (78 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/tools.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/utils.py`
- `cli/api/client.py`
- ... and 68 more files

### Auth (77 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/custom_tool_node.py`
- `agents/langchain/utils/utils.py`
- `agents/tools/bash.py`
- ... and 67 more files

### Api (98 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/create_pr_comment.py`
- ... and 88 more files

### Database (60 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/custom_tool_node.py`
- `agents/langchain/utils/utils.py`
- `agents/tools/observation.py`
- `agents/tools/reflection.py`
- ... and 50 more files

### Testing (44 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/agent.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/tools.py`
- `agents/tools/reflection.py`
- `agents/tools/search_files_by_name.py`
- `agents/tools/semantic_edit.py`
- ... and 34 more files


## 🔄 Potential Duplicate Implementations


### Main

- `dashboard.py`
- `cli/cli.py`
- `extensions/open_evolve/main.py`

### __Init__

- `dashboard.py`
- `agents/tracer.py`
- `agents/chat_agent.py`
- `agents/code_agent.py`
- `extensions/contexten_app.py`
- `extensions/contexten_app.py`
- `extensions/client.py`
- `dashboard/project_manager.py`
- `dashboard/project_manager.py`
- `dashboard/project_manager.py`
- `dashboard/app.py`
- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/advanced_analytics.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/enhanced_codebase_ai.py`
- `dashboard/workflow_automation.py`
- `dashboard/orchestrator_integration.py`
- `dashboard/chat_manager.py`
- `dashboard/chat_manager.py`
- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `extensions/prefect/client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/github/github.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/slack/slack.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/linear_client.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/assignment/detector.py`
- `extensions/linear/workflow/automation.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/validator.py`
- `extensions/open_evolve/database_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/code_generator/agent.py`
- `extensions/github/events/manager.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/webhook/processor.py`
- `agents/langchain/llm.py`
- `agents/langchain/graph.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `cli/api/client.py`
- `cli/env/global_env.py`
- `cli/auth/token_manager.py`
- `cli/sdk/pull_request.py`

### Shutdown

- `dashboard.py`
- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `extensions/prefect/client.py`

### Chat

- `agents/chat_agent.py`
- `agents/chat_agent.py`
- `dashboard/chat_manager.py`
- `dashboard/chat_manager.py`

### _Should_Use_Codegen_Sdk

- `agents/chat_agent.py`
- `agents/code_agent.py`

### Run

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `cli/api/client.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`

### Get_Chat_History

- `agents/chat_agent.py`
- `dashboard/app.py`

### Get_Codegen_Status

- `agents/codegen_config.py`
- `dashboard/app.py`

### From_Env

- `agents/codegen_config.py`
- `extensions/linear/config.py`

### Validate

- `agents/codegen_config.py`
- `extensions/linear/config.py`
- `extensions/linear/types.py`

### _Setup_Routes

- `extensions/contexten_app.py`
- `dashboard/prefect_dashboard.py`

### Start

- `extensions/contexten_app.py`
- `dashboard/orchestrator_integration.py`
- `extensions/github/enhanced_agent.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/webhook/processor.py`
- `extensions/github/events/manager.py`
- `extensions/github/workflow/automation.py`

### Stop

- `extensions/contexten_app.py`
- `dashboard/orchestrator_integration.py`
- `extensions/github/enhanced_agent.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/webhook/processor.py`
- `extensions/github/events/manager.py`
- `extensions/github/workflow/automation.py`

### _Health_Check_Loop

- `extensions/contexten_app.py`
- `extensions/linear/integration_agent.py`

### Get_System_Metrics

- `extensions/contexten_app.py`
- `dashboard/enhanced_routes.py`
- `orchestration/autonomous_orchestrator.py`
- `extensions/prefect/client.py`

### Health_Check

- `extensions/contexten_app.py`
- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Metrics

- `extensions/contexten_app.py`
- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`

### Close

- `extensions/client.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/enhanced_client.py`

### Add_Requirement

- `dashboard/project_manager.py`
- `dashboard/project_manager.py`
- `dashboard/enhanced_routes.py`

### Get_Requirements

- `dashboard/project_manager.py`
- `dashboard/enhanced_routes.py`

### Get_Requirement_Stats

- `dashboard/project_manager.py`
- `dashboard/enhanced_routes.py`

### Update_Metrics

- `dashboard/project_manager.py`
- `extensions/open_evolve/selection_controller/agent.py`

### Pin_Project

- `dashboard/project_manager.py`
- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Unpin_Project

- `dashboard/project_manager.py`
- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Update_Project

- `dashboard/project_manager.py`
- `dashboard/enhanced_routes.py`

### Get_Current_User

- `dashboard/app.py`
- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Dashboard_Home

- `dashboard/app.py`
- `dashboard/prefect_dashboard.py`

### Get_Projects

- `dashboard/app.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Stop_

- `dashboard/app.py`
- `dashboard/chat_manager.py`

### Get_Monitoring_Status

- `dashboard/app.py`
- `dashboard/chat_manager.py`

### Get_Integration_Status

- `dashboard/app.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`

### Get_Flows

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Create_Flow

- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/flow_manager.py`
- `dashboard/enhanced_routes.py`

### Get_Flow

- `dashboard/app.py`
- `dashboard/flow_manager.py`

### Start_Flow

- `dashboard/app.py`
- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/enhanced_routes.py`

### Stop_Flow

- `dashboard/app.py`
- `dashboard/flow_manager.py`
- `dashboard/enhanced_routes.py`

### Get_Flow_Templates

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_Flow_Template

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_Pinned_Projects

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_Project_Dashboard

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Flow_Websocket

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_Flow_Details

- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_System_Status

- `dashboard/app.py`
- `dashboard/prefect_dashboard.py`

### Flowtemplate

- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`

### Complete_Flow

- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`

### _Analyze_Code_Quality

- `dashboard/advanced_analytics.py`
- `dashboard/enhanced_codebase_ai.py`
- `extensions/prefect/tasks.py`

### _Analyze_Security

- `dashboard/advanced_analytics.py`
- `extensions/prefect/tasks.py`

### _Analyze_Performance

- `dashboard/advanced_analytics.py`
- `extensions/prefect/tasks.py`

### _Generate_Recommendations

- `dashboard/advanced_analytics.py`
- `dashboard/orchestrator_integration.py`

### Initialize

- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `extensions/prefect/client.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/assignment/detector.py`

### Trigger_Workflow

- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/workflow/automation.py`
- `extensions/github/workflow/automation.py`

### Get_Workflow_Status

- `dashboard/prefect_dashboard.py`
- `dashboard/workflow_automation.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Cancel_Workflow

- `dashboard/prefect_dashboard.py`
- `dashboard/workflow_automation.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Get_Workflow_History

- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Trigger_Component_Analysis

- `dashboard/prefect_dashboard.py`
- `orchestration/prefect_client.py`

### Workflowtrigger

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### Workflowexecution

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### List_Executions

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### _Validate_Configuration

- `orchestration/config.py`
- `orchestration/autonomous_orchestrator.py`

### To_Dict

- `orchestration/config.py`
- `extensions/linear/config.py`
- `agents/tools/search.py`

### From_Dict

- `orchestration/config.py`
- `extensions/github/types.py`
- `extensions/github/types.py`
- `extensions/github/types.py`
- `extensions/github/types.py`

### Prefectorchestrator

- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Sync_With_Linear

- `orchestration/prefect_client.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`

### List_Active_Workflows

- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Get_Docs

- `mcp/server.py`
- `cli/api/client.py`

### Improve_Codemod

- `mcp/server.py`
- `cli/api/client.py`

### Enhancedgithub

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### _Periodic_Sync

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Sync_Data

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Get_Repositories

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_Repository

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Repository

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_Issues

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/enhanced_client.py`

### Create_Issue

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linear_client.py`
- `extensions/linear/enhanced_client.py`

### Update_Issue

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Pull_Requests

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Pull_Request

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Update_Pull_Request

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Issue_Comment

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Pr_Comment

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `agents/tools/github/create_pr_comment.py`

### Process_Webhook

- `extensions/github/enhanced_agent.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/enhanced_agent.py`

### Get_User

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_Organizations

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_Organization_Repositories

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_Branches

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Branch

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Get_File_Content

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Or_Update_File

- `extensions/github/enhanced_agent.py`
- `extensions/github/enhanced_client.py`

### Create_Codegen_Task

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Githubuser

- `extensions/github/types.py`
- `extensions/github/github_types.py`
- `extensions/github/types/base.py`

### Githubrepository

- `extensions/github/types.py`
- `extensions/github/github_types.py`
- `extensions/github/types/base.py`

### Githubissue

- `extensions/github/types.py`
- `extensions/github/types/base.py`

### Githubpullrequest

- `extensions/github/types.py`
- `extensions/github/types/base.py`

### Githubinstallation

- `extensions/github/github_types.py`
- `extensions/github/types/base.py`
- `extensions/github/types/installation.py`

### Unsubscribe_All_Handlers

- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/modal/interface.py`
- `extensions/linear/linearevents.py`

### Event

- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/events/manager.py`

### Handle

- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/linear/linearevents.py`

### Register_

- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook/processor.py`

### New_Func

- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/linear/linearevents.py`

### Emit

- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`

### Handle_Event

- `extensions/modal/base.py`
- `extensions/linear/webhook/handlers.py`

### Webhook

- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/processor.py`

### Unregister_

- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/processor.py`

### _Process_Event

- `extensions/linear/webhook_processor.py`
- `extensions/linear/events/manager.py`

### Process_Event_Directly

- `extensions/linear/webhook_processor.py`
- `extensions/linear/integration_agent.py`

### Get_Stats

- `extensions/linear/webhook_processor.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/webhook/processor.py`

### Cleanup

- `extensions/linear/webhook_processor.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`

### Enhancedlinear

- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Issue

- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/linear_client.py`

### Search_Issues

- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linear_client.py`

### Get_Teams

- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linear_client.py`
- `extensions/linear/enhanced_client.py`

### Linearintegrationconfig

- `extensions/linear/config.py`
- `extensions/linear/types.py`

### Linearuser

- `extensions/linear/linearclient.py`
- `extensions/linear/types.py`

### Linearcomment

- `extensions/linear/linearclient.py`
- `extensions/linear/types.py`

### Linearissue

- `extensions/linear/linearclient.py`
- `extensions/linear/types.py`

### Linear

- `extensions/linear/linearclient.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/linear_client.py`

### Get_Issue_Comments

- `extensions/linear/linearclient.py`
- `extensions/linear/linear_client.py`

### Comment_On_Issue

- `extensions/linear/linearclient.py`
- `extensions/linear/linear_client.py`

### Register_Webhook

- `extensions/linear/linearclient.py`
- `extensions/linear/linear_client.py`

### Workflowautomation

- `extensions/linear/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### Get_Active_Tasks

- `extensions/linear/workflow_automation.py`
- `extensions/linear/linearevents.py`

### Handle_Webhook

- `extensions/linear/integration_agent.py`
- `extensions/linear/linearevents.py`

### __Aenter__

- `extensions/linear/integration_agent.py`
- `extensions/linear/enhanced_client.py`

### __Aexit__

- `extensions/linear/integration_agent.py`
- `extensions/linear/enhanced_client.py`

### Is_Completed

- `extensions/linear/types.py`
- `extensions/linear/workflow/automation.py`

### _Make_Request

- `extensions/linear/enhanced_client.py`
- `cli/api/client.py`

### Assignmentdetector

- `extensions/linear/assignment_detector.py`
- `extensions/linear/assignment/detector.py`

### Get_Assignment_Stats

- `extensions/linear/assignment_detector.py`
- `extensions/linear/assignment/detector.py`

### Emit_Event

- `extensions/linear/events/manager.py`
- `extensions/github/events/manager.py`

### Process_Pending_Events

- `extensions/linear/events/manager.py`
- `extensions/github/events/manager.py`

### Is_Healthy

- `extensions/linear/events/manager.py`
- `extensions/linear/webhook/processor.py`
- `extensions/github/events/manager.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/webhook/processor.py`

### _Evaluate_Condition

- `extensions/linear/assignment/detector.py`
- `extensions/linear/workflow/automation.py`

### _Get_Nested_Value

- `extensions/linear/workflow/automation.py`
- `extensions/linear/workflow/automation.py`

### Validate_Signature

- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/validator.py`
- `extensions/github/webhook/processor.py`

### Process

- `extensions/linear/webhook/processor.py`
- `extensions/github/webhook/processor.py`

### Execute

- `extensions/open_evolve/database_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/code_generator/agent.py`

### Githubevent

- `extensions/github/events/manager.py`
- `extensions/github/types/base.py`

### Label

- `extensions/github/types/pull_request.py`
- `extensions/github/types/events/pull_request.py`

### Pullrequest

- `extensions/github/types/pull_request.py`
- `cli/sdk/function.py`

### Pullrequestlabeledevent

- `extensions/github/types/pull_request.py`
- `extensions/github/types/events/pull_request.py`

### Pushevent

- `extensions/github/types/push.py`
- `extensions/github/types/events/push.py`

### User

- `extensions/github/types/events/pull_request.py`
- `cli/api/schemas.py`

### Searchmatch

- `agents/tools/search.py`
- `agents/tools/tool_output_types.py`

### Search

- `agents/tools/search.py`
- `agents/tools/github/search.py`

### Render_As_String

- `agents/tools/search.py`
- `agents/tools/search.py`
- `agents/tools/observation.py`
- `agents/tools/list_directory.py`

### _Get_Details

- `agents/tools/search.py`
- `agents/tools/observation.py`
- `agents/tools/reveal_symbol.py`
- `agents/tools/reflection.py`
- `agents/tools/list_directory.py`
- `agents/tools/semantic_search.py`
- `agents/tools/linear/linear.py`
- `agents/tools/linear/linear.py`
- `agents/tools/linear/linear.py`

### Render

- `agents/tools/search.py`
- `agents/tools/edit_file.py`
- `agents/tools/semantic_edit.py`
- `agents/tools/observation.py`
- `agents/tools/view_file.py`
- `agents/tools/reflection.py`
- `agents/tools/relace_edit.py`
- `agents/tools/list_directory.py`

### Total

- `agents/tools/search_files_by_name.py`
- `agents/tools/github/search.py`

### Generate_Diff

- `agents/tools/semantic_edit.py`
- `agents/tools/relace_edit.py`
- `agents/tools/replacement_edit.py`
- `agents/tools/global_replacement_edit.py`

### __Str__

- `agents/tools/observation.py`
- `cli/sdk/pull_request.py`

### __Repr__

- `agents/tools/observation.py`
- `cli/env/global_env.py`

### Create

- `agents/langchain/graph.py`
- `cli/api/client.py`

### Get_Workspace_Tools

- `agents/langchain/tools.py`
- `agents/langchain/__init__.py`

### _Run

- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`
- `agents/langchain/tools.py`

### Lookup

- `cli/api/client.py`
- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`

### Run_On_Pr

- `cli/api/client.py`
- `cli/commands/run_on_pr/main.py`

### Pretty_Print_Output

- `cli/rich/pretty_print.py`
- `cli/commands/run/render.py`

### Pretty_Print_Logs

- `cli/rich/pretty_print.py`
- `cli/commands/run/render.py`

### Pretty_Print_Error

- `cli/rich/pretty_print.py`
- `cli/commands/run/render.py`

### Pretty_Print_Diff

- `cli/rich/pretty_print.py`
- `cli/commands/run/render.py`

### Function

- `cli/sdk/function.py`
- `cli/sdk/functions.py`


## ❓ Missing Features

- Authentication system
- Configuration management
- Error handling middleware
- Testing utilities
- Deployment scripts


## 🔍 Detailed Analysis by Category

### Dashboard Files
Found 128 dashboard-related files. 47 appear to be dead code:
- `extensions/client.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/config.py`
- `extensions/prefect/client.py`
- `extensions/prefect/tasks.py`
- `extensions/prefect/notifications.py`
- `extensions/prefect/workflows.py`
- `extensions/github/github_types.py`
- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/linear/queries.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/mutations.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/assignment/detector.py`
- `extensions/linear/workflow/automation.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/validator.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/code_generator/agent.py`
- `extensions/github/events/manager.py`
- `extensions/github/types/enterprise.py`
- `extensions/github/webhook/processor.py`
- `agents/tools/edit_file.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/create_file.py`
- `agents/tools/view_file.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/list_directory.py`
- `agents/langchain/graph.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/search.py`
- `cli/workspace/initialize_workspace.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/commands/run/render.py`


### Agent Files
Found 139 agent-related files. 42 appear to be dead code:
- `agents/data.py`
- `extensions/client.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/config.py`
- `extensions/prefect/tasks.py`
- `extensions/prefect/workflows.py`
- `extensions/github/github.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/workflow/automation.py`
- `extensions/linear/webhook/validator.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/code_generator/agent.py`
- `agents/tools/rename_file.py`
- `agents/tools/edit_file.py`
- `agents/tools/delete_file.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/create_file.py`
- `agents/tools/view_file.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/commit.py`
- `agents/tools/move_symbol.py`
- `agents/tools/run_codemod.py`
- `agents/tools/list_directory.py`
- `agents/langchain/graph.py`
- `agents/tools/github/create_pr_review_comment.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/search.py`
- `agents/tools/github/create_pr_comment.py`
- `cli/workspace/initialize_workspace.py`
- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/commands/run/render.py`


### CLI Files
Found 111 CLI-related files. 37 appear to be dead code:
- `extensions/client.py`
- `orchestration/prefect_client.py`
- `extensions/prefect/config.py`
- `extensions/prefect/client.py`
- `extensions/prefect/tasks.py`
- `extensions/prefect/notifications.py`
- `extensions/prefect/workflows.py`
- `extensions/github/github_types.py`
- `extensions/github/github.py`
- `extensions/slack/slack.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/linear/queries.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/mutations.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/assignment/detector.py`
- `extensions/linear/workflow/automation.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/code_generator/agent.py`
- `extensions/github/types/pull_request.py`
- `extensions/github/workflow/automation.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/langchain/graph.py`
- `agents/tools/github/create_pr.py`
- `cli/workspace/initialize_workspace.py`
- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/commands/run/render.py`


## 🎯 Recommendations

### High Priority Actions
1. **Review Entry Points**: Ensure all 36 entry points are necessary
2. **Investigate Dead Code**: Manually review 63 potentially dead files
3. **Consolidate Duplicates**: Review 161 potential duplicate implementations

### Dead Code Removal Strategy
1. **Start with smallest files**: Remove files with <10 lines of code first
2. **Test after each removal**: Ensure functionality isn't broken
3. **Keep backups**: Maintain backups of removed files
4. **Remove incrementally**: Don't remove all files at once

### False Positive Checks
Before removing any file, verify it's not:
- Dynamically imported
- Used in configuration files
- Required for deployment
- Part of a plugin system
- Used in tests that weren't analyzed

---

*Analysis completed on 189 Python files*
