# Contexten Dead Code Analysis Report

## 📊 Summary

- **Total Files Analyzed**: 189
- **Potentially Dead Files**: 48
- **Entry Points**: 36
- **Core Feature Categories**: 16
- **Potential Duplicates**: 161
- **Missing Features**: 5

## 🚪 Entry Points (Files that are executed directly)

These files are definitely NOT dead code as they serve as entry points:

- `dashboard.py`
- `dashboard.py`
- `extensions/contexten_app.py`
- `mcp/server.py`
- `mcp/server.py`
- `mcp/server.py`
- `dashboard/chat_manager.py`
- `dashboard/project_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/enhanced_codebase_ai.py`
- `dashboard/orchestrator_integration.py`
- `dashboard/workflow_automation.py`
- `dashboard/advanced_analytics.py`
- `dashboard/enhanced_routes.py`
- `agents/codegen_config.py`
- `cli/cli.py`
- `cli/commands/profile/main.py`
- `cli/commands/serve/main.py`
- `cli/commands/serve/main.py`
- `cli/commands/run/main.py`
- `cli/commands/create/main.py`
- `cli/commands/deploy/main.py`
- `cli/commands/run_on_pr/main.py`
- `cli/commands/login/main.py`
- `cli/commands/agent/main.py`
- `cli/commands/expert/main.py`
- `mcp/codebase/codebase_mods.py`
- `mcp/codebase/codebase_agent.py`
- `mcp/codebase/codebase_tools.py`
- `extensions/open_evolve/main.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/database_agent/agent.py`


## 💀 Potentially Dead Code (48 files)

These files are not imported by any other files and may be dead code:


### Agents (16 files)

- `agents/data.py`
- `agents/langchain/graph.py`
- `agents/tools/commit.py`
- `agents/tools/create_file.py`
- `agents/tools/delete_file.py`
- `agents/tools/edit_file.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/create_pr_comment.py`
- `agents/tools/github/create_pr_review_comment.py`
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

### Extensions (26 files)

- `extensions/client.py`
- `extensions/github/events/manager.py`
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
- `extensions/linear/assignment_detector.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/validator.py`
- `extensions/linear/webhook_processor.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/open_evolve/code_generator/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/task_manager/agent.py`
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

### Extensions (110 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/tools/__init__.py`
- `agents/tools/linear/linear.py`
- `agents/tools/link_annotation.py`
- `agents/tools/relace_edit_prompts.py`
- ... and 100 more files

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

### Cli (112 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/__init__.py`
- `agents/tools/bash.py`
- `agents/tools/github/create_pr.py`
- ... and 102 more files

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

### Shared (145 files)

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
- ... and 135 more files

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

### Api (99 files)

- `agents/chat_agent.py`
- `agents/code_agent.py`
- `agents/codegen_config.py`
- `agents/langchain/graph.py`
- `agents/langchain/llm.py`
- `agents/langchain/prompts.py`
- `agents/langchain/tools.py`
- `agents/langchain/utils/get_langsmith_url.py`
- `agents/tools/__init__.py`
- `agents/tools/github/create_pr.py`
- ... and 89 more files

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
- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `extensions/client.py`
- `extensions/contexten_app.py`
- `extensions/contexten_app.py`
- `dashboard/chat_manager.py`
- `dashboard/chat_manager.py`
- `dashboard/project_manager.py`
- `dashboard/project_manager.py`
- `dashboard/project_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/app.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/enhanced_codebase_ai.py`
- `dashboard/orchestrator_integration.py`
- `dashboard/workflow_automation.py`
- `dashboard/advanced_analytics.py`
- `agents/tracer.py`
- `agents/code_agent.py`
- `agents/chat_agent.py`
- `cli/env/global_env.py`
- `cli/sdk/pull_request.py`
- `cli/api/client.py`
- `cli/auth/token_manager.py`
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
- `agents/langchain/llm.py`
- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`
- `extensions/slack/slack.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/github/github.py`
- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linearclient.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/linear_client.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/workflow_automation.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/assignment_detector.py`
- `extensions/prefect/client.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/validator.py`
- `extensions/linear/assignment/detector.py`
- `extensions/linear/events/manager.py`
- `extensions/linear/workflow/automation.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/webhook/processor.py`
- `extensions/github/events/manager.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/database_agent/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/code_generator/agent.py`

### Shutdown

- `dashboard.py`
- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `dashboard/prefect_dashboard.py`
- `extensions/prefect/client.py`

### _Validate_Configuration

- `orchestration/config.py`
- `orchestration/autonomous_orchestrator.py`

### To_Dict

- `orchestration/config.py`
- `agents/tools/search.py`
- `extensions/linear/config.py`

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
- `extensions/linear/linearevents.py`
- `extensions/linear/integration_agent.py`

### Initialize

- `orchestration/prefect_client.py`
- `orchestration/autonomous_orchestrator.py`
- `orchestration/monitoring.py`
- `dashboard/prefect_dashboard.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/integration_agent.py`
- `extensions/prefect/client.py`
- `extensions/linear/assignment/detector.py`

### Trigger_Workflow

- `orchestration/prefect_client.py`
- `dashboard/prefect_dashboard.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/workflow/automation.py`
- `extensions/github/workflow/automation.py`

### Get_Workflow_Status

- `orchestration/prefect_client.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/workflow_automation.py`
- `extensions/prefect/client.py`

### Cancel_Workflow

- `orchestration/prefect_client.py`
- `dashboard/prefect_dashboard.py`
- `dashboard/workflow_automation.py`
- `extensions/prefect/client.py`

### List_Active_Workflows

- `orchestration/prefect_client.py`
- `extensions/prefect/client.py`

### Get_Workflow_History

- `orchestration/prefect_client.py`
- `dashboard/prefect_dashboard.py`
- `extensions/prefect/client.py`

### Get_Metrics

- `orchestration/prefect_client.py`
- `extensions/contexten_app.py`
- `dashboard/prefect_dashboard.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/integration_agent.py`

### Trigger_Component_Analysis

- `orchestration/prefect_client.py`
- `dashboard/prefect_dashboard.py`

### Get_System_Metrics

- `orchestration/autonomous_orchestrator.py`
- `extensions/contexten_app.py`
- `dashboard/enhanced_routes.py`
- `extensions/prefect/client.py`

### Close

- `extensions/client.py`
- `extensions/github/enhanced_client.py`
- `extensions/linear/enhanced_client.py`

### _Setup_Routes

- `extensions/contexten_app.py`
- `dashboard/prefect_dashboard.py`

### Start

- `extensions/contexten_app.py`
- `dashboard/orchestrator_integration.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/events/manager.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/events/manager.py`

### Stop

- `extensions/contexten_app.py`
- `dashboard/orchestrator_integration.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/webhook/processor.py`
- `extensions/linear/events/manager.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/events/manager.py`

### _Health_Check_Loop

- `extensions/contexten_app.py`
- `extensions/linear/integration_agent.py`

### Health_Check

- `extensions/contexten_app.py`
- `extensions/slack/enhanced_agent.py`
- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Docs

- `mcp/server.py`
- `cli/api/client.py`

### Improve_Codemod

- `mcp/server.py`
- `cli/api/client.py`

### Chat

- `dashboard/chat_manager.py`
- `dashboard/chat_manager.py`
- `agents/chat_agent.py`
- `agents/chat_agent.py`

### Stop_

- `dashboard/chat_manager.py`
- `dashboard/app.py`

### Get_Monitoring_Status

- `dashboard/chat_manager.py`
- `dashboard/app.py`

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

### Flowtemplate

- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`

### Start_Flow

- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Complete_Flow

- `dashboard/flow_manager.py`
- `dashboard/flow_manager.py`

### Create_Flow

- `dashboard/flow_manager.py`
- `dashboard/app.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Stop_Flow

- `dashboard/flow_manager.py`
- `dashboard/app.py`
- `dashboard/enhanced_routes.py`

### Get_Flow

- `dashboard/flow_manager.py`
- `dashboard/app.py`

### Get_Current_User

- `dashboard/app.py`
- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Dashboard_Home

- `dashboard/app.py`
- `dashboard/prefect_dashboard.py`

### Get_Projects

- `dashboard/app.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Codegen_Status

- `dashboard/app.py`
- `agents/codegen_config.py`

### Get_Chat_History

- `dashboard/app.py`
- `agents/chat_agent.py`

### Get_Integration_Status

- `dashboard/app.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/integration_agent.py`

### Get_Flows

- `dashboard/app.py`
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

### _Analyze_Code_Quality

- `dashboard/enhanced_codebase_ai.py`
- `dashboard/advanced_analytics.py`
- `extensions/prefect/tasks.py`

### _Generate_Recommendations

- `dashboard/orchestrator_integration.py`
- `dashboard/advanced_analytics.py`

### Workflowtrigger

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### Workflowexecution

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### List_Executions

- `dashboard/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### _Analyze_Security

- `dashboard/advanced_analytics.py`
- `extensions/prefect/tasks.py`

### _Analyze_Performance

- `dashboard/advanced_analytics.py`
- `extensions/prefect/tasks.py`

### From_Env

- `agents/codegen_config.py`
- `extensions/linear/config.py`

### Validate

- `agents/codegen_config.py`
- `extensions/linear/config.py`
- `extensions/linear/types.py`

### _Should_Use_Codegen_Sdk

- `agents/code_agent.py`
- `agents/chat_agent.py`

### Run

- `agents/code_agent.py`
- `agents/chat_agent.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/api/client.py`

### __Repr__

- `cli/env/global_env.py`
- `agents/tools/observation.py`

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

### Lookup

- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/api/client.py`

### __Str__

- `cli/sdk/pull_request.py`
- `agents/tools/observation.py`

### Pullrequest

- `cli/sdk/function.py`
- `extensions/github/types/pull_request.py`

### Function

- `cli/sdk/function.py`
- `cli/sdk/functions.py`

### _Make_Request

- `cli/api/client.py`
- `extensions/linear/enhanced_client.py`

### Create

- `cli/api/client.py`
- `agents/langchain/graph.py`

### Run_On_Pr

- `cli/api/client.py`
- `cli/commands/run_on_pr/main.py`

### User

- `cli/api/schemas.py`
- `extensions/github/types/events/pull_request.py`

### Get_Workspace_Tools

- `agents/langchain/__init__.py`
- `agents/langchain/tools.py`

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

### Generate_Diff

- `agents/tools/replacement_edit.py`
- `agents/tools/global_replacement_edit.py`
- `agents/tools/semantic_edit.py`
- `agents/tools/relace_edit.py`

### Searchmatch

- `agents/tools/search.py`
- `agents/tools/tool_output_types.py`

### Search

- `agents/tools/search.py`
- `agents/tools/github/search.py`

### Render_As_String

- `agents/tools/search.py`
- `agents/tools/search.py`
- `agents/tools/list_directory.py`
- `agents/tools/observation.py`

### _Get_Details

- `agents/tools/search.py`
- `agents/tools/reflection.py`
- `agents/tools/list_directory.py`
- `agents/tools/reveal_symbol.py`
- `agents/tools/observation.py`
- `agents/tools/semantic_search.py`
- `agents/tools/linear/linear.py`
- `agents/tools/linear/linear.py`
- `agents/tools/linear/linear.py`

### Render

- `agents/tools/search.py`
- `agents/tools/reflection.py`
- `agents/tools/list_directory.py`
- `agents/tools/view_file.py`
- `agents/tools/semantic_edit.py`
- `agents/tools/observation.py`
- `agents/tools/relace_edit.py`
- `agents/tools/edit_file.py`

### Total

- `agents/tools/search_files_by_name.py`
- `agents/tools/github/search.py`

### Create_Pr_Comment

- `agents/tools/github/create_pr_comment.py`
- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Handle_Event

- `extensions/modal/base.py`
- `extensions/linear/webhook/handlers.py`

### Unsubscribe_All_Handlers

- `extensions/modal/interface.py`
- `extensions/slack/slack.py`
- `extensions/github/github.py`
- `extensions/linear/linearevents.py`

### Emit

- `extensions/open_evolve/app.py`
- `extensions/open_evolve/app.py`

### Handle

- `extensions/slack/slack.py`
- `extensions/github/github.py`
- `extensions/linear/linearevents.py`

### Event

- `extensions/slack/slack.py`
- `extensions/github/github.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/events/manager.py`

### Register_

- `extensions/slack/slack.py`
- `extensions/github/github.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/processor.py`

### New_Func

- `extensions/slack/slack.py`
- `extensions/github/github.py`
- `extensions/linear/linearevents.py`

### Enhancedgithub

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Repositories

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Repository

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Create_Repository

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Issues

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Create_Issue

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/linear_client.py`
- `extensions/linear/enhanced_client.py`

### Update_Issue

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/enhanced_client.py`

### Get_Pull_Requests

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Create_Pull_Request

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Update_Pull_Request

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Create_Issue_Comment

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_User

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Organizations

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Organization_Repositories

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_Branches

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Create_Branch

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Get_File_Content

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Create_Or_Update_File

- `extensions/github/enhanced_client.py`
- `extensions/github/enhanced_agent.py`

### Githubrepository

- `extensions/github/github_types.py`
- `extensions/github/types.py`
- `extensions/github/types/base.py`

### Githubinstallation

- `extensions/github/github_types.py`
- `extensions/github/types/base.py`
- `extensions/github/types/installation.py`

### Githubuser

- `extensions/github/github_types.py`
- `extensions/github/types.py`
- `extensions/github/types/base.py`

### _Periodic_Sync

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Sync_Data

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Process_Webhook

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`
- `extensions/linear/webhook_processor.py`

### Create_Codegen_Task

- `extensions/github/enhanced_agent.py`
- `extensions/linear/enhanced_agent.py`

### Githubissue

- `extensions/github/types.py`
- `extensions/github/types/base.py`

### Githubpullrequest

- `extensions/github/types.py`
- `extensions/github/types/base.py`

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

### Cleanup

- `extensions/linear/linearevents.py`
- `extensions/linear/integration_agent.py`
- `extensions/linear/webhook_processor.py`

### Get_Active_Tasks

- `extensions/linear/linearevents.py`
- `extensions/linear/workflow_automation.py`

### Handle_Webhook

- `extensions/linear/linearevents.py`
- `extensions/linear/integration_agent.py`

### Linearintegrationconfig

- `extensions/linear/config.py`
- `extensions/linear/types.py`

### Process_Event_Directly

- `extensions/linear/integration_agent.py`
- `extensions/linear/webhook_processor.py`

### __Aenter__

- `extensions/linear/integration_agent.py`
- `extensions/linear/enhanced_client.py`

### __Aexit__

- `extensions/linear/integration_agent.py`
- `extensions/linear/enhanced_client.py`

### Workflowautomation

- `extensions/linear/workflow_automation.py`
- `extensions/linear/workflow/automation.py`

### Get_Stats

- `extensions/linear/workflow_automation.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/webhook/processor.py`

### Webhook

- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/processor.py`

### Unregister_

- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/processor.py`

### _Process_Event

- `extensions/linear/webhook_processor.py`
- `extensions/linear/events/manager.py`

### Is_Completed

- `extensions/linear/types.py`
- `extensions/linear/workflow/automation.py`

### Assignmentdetector

- `extensions/linear/assignment_detector.py`
- `extensions/linear/assignment/detector.py`

### Get_Assignment_Stats

- `extensions/linear/assignment_detector.py`
- `extensions/linear/assignment/detector.py`

### Validate_Signature

- `extensions/linear/webhook/processor.py`
- `extensions/linear/webhook/validator.py`
- `extensions/github/webhook/processor.py`

### Process

- `extensions/linear/webhook/processor.py`
- `extensions/github/webhook/processor.py`

### Is_Healthy

- `extensions/linear/webhook/processor.py`
- `extensions/linear/events/manager.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/webhook/processor.py`
- `extensions/github/events/manager.py`

### _Evaluate_Condition

- `extensions/linear/assignment/detector.py`
- `extensions/linear/workflow/automation.py`

### Emit_Event

- `extensions/linear/events/manager.py`
- `extensions/github/events/manager.py`

### Process_Pending_Events

- `extensions/linear/events/manager.py`
- `extensions/github/events/manager.py`

### _Get_Nested_Value

- `extensions/linear/workflow/automation.py`
- `extensions/linear/workflow/automation.py`

### Githubevent

- `extensions/github/events/manager.py`
- `extensions/github/types/base.py`

### Label

- `extensions/github/types/pull_request.py`
- `extensions/github/types/events/pull_request.py`

### Pullrequestlabeledevent

- `extensions/github/types/pull_request.py`
- `extensions/github/types/events/pull_request.py`

### Pushevent

- `extensions/github/types/push.py`
- `extensions/github/types/events/push.py`

### Execute

- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/database_agent/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/code_generator/agent.py`


## ❓ Missing Features

- Authentication system
- Configuration management
- Error handling middleware
- Testing utilities
- Deployment scripts


## 🔍 Detailed Analysis by Category

### Dashboard Files
Found 128 dashboard-related files. 32 appear to be dead code:
- `orchestration/prefect_client.py`
- `extensions/client.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/workspace/initialize_workspace.py`
- `cli/commands/run/render.py`
- `agents/langchain/graph.py`
- `agents/tools/list_directory.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/view_file.py`
- `agents/tools/create_file.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/edit_file.py`
- `agents/tools/github/create_pr.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/slack/slack.py`
- `extensions/github/github_types.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/assignment_detector.py`
- `extensions/linear/webhook/handlers.py`
- `extensions/linear/webhook/validator.py`
- `extensions/github/webhook/processor.py`
- `extensions/github/events/manager.py`
- `extensions/github/types/enterprise.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/code_generator/agent.py`


### Agent Files
Found 139 agent-related files. 34 appear to be dead code:
- `orchestration/prefect_client.py`
- `extensions/client.py`
- `agents/data.py`
- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/workspace/initialize_workspace.py`
- `cli/commands/run/render.py`
- `agents/langchain/graph.py`
- `agents/tools/list_directory.py`
- `agents/tools/rename_file.py`
- `agents/tools/delete_file.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/view_file.py`
- `agents/tools/run_codemod.py`
- `agents/tools/create_file.py`
- `agents/tools/move_symbol.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/commit.py`
- `agents/tools/edit_file.py`
- `agents/tools/github/create_pr.py`
- `agents/tools/github/create_pr_review_comment.py`
- `agents/tools/github/create_pr_comment.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/webhook/validator.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/config/settings.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/code_generator/agent.py`


### CLI Files
Found 112 CLI-related files. 25 appear to be dead code:
- `orchestration/prefect_client.py`
- `extensions/client.py`
- `cli/sdk/pull_request.py`
- `cli/sdk/function.py`
- `cli/sdk/functions.py`
- `cli/workspace/initialize_workspace.py`
- `cli/commands/run/render.py`
- `agents/langchain/graph.py`
- `agents/tools/relace_edit_prompts.py`
- `agents/tools/semantic_edit_prompts.py`
- `agents/tools/github/create_pr.py`
- `extensions/modal/base.py`
- `extensions/modal/request_util.py`
- `extensions/slack/slack.py`
- `extensions/github/github_types.py`
- `extensions/linear/linearevents.py`
- `extensions/linear/webhook_processor.py`
- `extensions/linear/assignment_detector.py`
- `extensions/github/workflow/automation.py`
- `extensions/github/types/pull_request.py`
- `extensions/open_evolve/task_manager/agent.py`
- `extensions/open_evolve/prompt_designer/agent.py`
- `extensions/open_evolve/evaluator_agent/agent.py`
- `extensions/open_evolve/selection_controller/agent.py`
- `extensions/open_evolve/code_generator/agent.py`


## 🎯 Recommendations

### High Priority Actions
1. **Review Entry Points**: Ensure all 36 entry points are necessary
2. **Investigate Dead Code**: Manually review 48 potentially dead files
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
