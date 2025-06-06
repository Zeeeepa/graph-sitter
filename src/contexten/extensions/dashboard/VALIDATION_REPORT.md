================================================================================
COMPREHENSIVE DASHBOARD VALIDATION REPORT
================================================================================

📊 SUMMARY:
   Files Analyzed: 31
   Files with Errors: 0
   Total Functions: 105
   Total Classes: 74
   Total Methods: 296
   Syntax Errors: 0
   Import Errors: 21

❌ IMPORT ERRORS:
   ./github_integration.py: attempted relative import with no known parent package
   ./consolidated_init.py: attempted relative import with no known parent package
   ./api.py: attempted relative import with no known parent package
   ./consolidated_dashboard.py: attempted relative import with no known parent package
   ./consolidated_api.py: attempted relative import with no known parent package
   ./dashboard.py: attempted relative import with no known parent package
   ./database.py: attempted relative import with no known parent package
   ./test_consolidated_system.py: No module named 'dotenv'
   ./codegen_integration.py: attempted relative import with no known parent package
   ./__init__.py: attempted relative import with no known parent package
   ./services/strands_orchestrator.py: attempted relative import beyond top-level package
   ./services/monitoring_service.py: attempted relative import beyond top-level package
   ./services/quality_service.py: attempted relative import beyond top-level package
   ./services/codegen_service.py: attempted relative import beyond top-level package
   ./services/__init__.py: attempted relative import beyond top-level package
   ./services/project_service.py: attempted relative import beyond top-level package
   ./workflows/__init__.py: attempted relative import beyond top-level package
   ./workflows/mcp_integration.py: attempted relative import beyond top-level package
   ./workflows/controlflow_integration.py: attempted relative import beyond top-level package
   ./workflows/orchestrator.py: attempted relative import beyond top-level package
   ./workflows/prefect_integration.py: attempted relative import beyond top-level package

📁 FILE ANALYSIS:

📄 ./github_integration.py
   Size: 14442 bytes, 397 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (1):
     - __init__(self, token) [line 29]
   Classes (1):
     - GitHubProjectManager [line 26]
       * __init__(self, token) [line 29]
       * initialize(self) [line 42]
       * get_user_repositories(self, per_page) [line 56]
       * get_repository_details(self, owner, repo) [line 124]
       * get_repository_prs(self, owner, repo, state) [line 151]
       * create_pull_request(self, owner, repo, title, body, head, base) [line 206]
       * create_issue(self, owner, repo, title, body, labels, assignees) [line 254]
       * get_repository_branches(self, owner, repo) [line 305]
       * handle_event(self, event_type, payload) [line 340]
       * _handle_pr_event(self, payload) [line 362]
       * _handle_issue_event(self, payload) [line 372]
       * _handle_push_event(self, payload) [line 382]
       * cleanup(self) [line 392]

📄 ./test_both_launchers.py
   Size: 3337 bytes, 115 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (2):
     - test_launcher(script_name, description) [line 12]
     - main() [line 64]

📄 ./consolidated_init.py
   Size: 2468 bytes, 91 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (1):
     - setup_dashboard(contexten_app) [line 67]

📄 ./models.py
   Size: 8989 bytes, 271 lines
   Syntax Valid: ✅
   Import Test: ✅
   Classes (21):
     - ProjectStatus [line 15]
     - FlowStatus [line 23]
     - WorkflowStatus [line 31]
     - TaskStatus [line 40]
     - QualityGateStatus [line 50]
     - PRStatus [line 58]
     - Project [line 67]
     - ProjectPin [line 83]
     - ProjectSettings [line 95]
     - WorkflowPlan [line 110]
     - WorkflowTask [line 129]
     - WorkflowExecution [line 152]
     - QualityGate [line 168]
     - PRInfo [line 184]
     - EventLog [line 205]
     - ProjectCreateRequest [line 218]
     - ProjectPinRequest [line 228]
     - WorkflowPlanRequest [line 234]
     - SettingsUpdateRequest [line 242]
     - EnvironmentVariablesRequest [line 255]
     - DashboardResponse [line 265]

📄 ./api.py
   Size: 13682 bytes, 386 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package

📄 ./consolidated_dashboard.py
   Size: 4046 bytes, 133 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (4):
     - create_consolidated_dashboard(contexten_app) [line 108]
     - __init__(self, contexten_app) [line 22]
     - run(self) [line 57]
     - get_health_status(self) [line 88]
   Classes (1):
     - ConsolidatedDashboard [line 16]
       * __init__(self, contexten_app) [line 22]
       * start(self) [line 35]
       * run(self) [line 57]
       * stop(self) [line 76]
       * get_health_status(self) [line 88]

📄 ./start_dashboard_standalone.py
   Size: 17043 bytes, 451 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (4):
     - print_banner() [line 37]
     - validate_environment() [line 55]
     - create_standalone_dashboard() [line 100]
     - main() [line 410]

📄 ./main.py
   Size: 2394 bytes, 92 lines
   Syntax Valid: ✅
   Import Test: ✅

📄 ./consolidated_api.py
   Size: 27891 bytes, 653 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (5):
     - create_dashboard_app(contexten_app) [line 649]
     - __init__(self, contexten_app) [line 41]
     - _setup_routes(self) [line 79]
     - disconnect(self, websocket) [line 491]
     - _start_background_tasks(self) [line 553]
   Classes (1):
     - ConsolidatedDashboardAPI [line 35]
       * __init__(self, contexten_app) [line 41]
       * _setup_routes(self) [line 79]
       * connect(self, websocket) [line 477]
       * disconnect(self, websocket) [line 491]
       * _handle_websocket_message(self, websocket, message) [line 498]
       * _broadcast_event(self, event) [line 530]
       * _start_background_tasks(self) [line 553]
       * _system_health_monitor(self) [line 560]
       * _analyze_project_background(self, project_id) [line 573]
       * _monitor_workflow_execution(self, flow_id) [line 580]
       * _execute_codegen_task(self, task_id) [line 587]
       * _validate_quality_gates_background(self, project_id) [line 594]
       * _check_github_status(self) [line 606]
       * _check_linear_status(self) [line 615]
       * _check_slack_status(self) [line 624]
       * _check_codegen_status(self) [line 633]
       * _check_database_status(self) [line 640]

📄 ./start_dashboard.py
   Size: 4689 bytes, 156 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (5):
     - check_dependencies() [line 14]
     - install_frontend_deps() [line 44]
     - start_backend() [line 62]
     - start_frontend() [line 74]
     - main() [line 88]

📄 ./start_consolidated_dashboard.py
   Size: 5975 bytes, 187 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (4):
     - setup_logging(debug) [line 25]
     - check_environment() [line 43]
     - print_banner() [line 81]
     - main() [line 100]

📄 ./dashboard.py
   Size: 12927 bytes, 347 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (5):
     - setup_dashboard(contexten_app) [line 332]
     - __init__(self, contexten_app) [line 42]
     - _setup_routes(self) [line 63]
     - _setup_static_files(self) [line 82]
     - _get_fallback_html(self) [line 109]
   Classes (1):
     - Dashboard [line 28]
       * __init__(self, contexten_app) [line 42]
       * _setup_routes(self) [line 63]
       * _setup_static_files(self) [line 82]
       * _serve_dashboard_ui(self) [line 96]
       * _get_fallback_html(self) [line 109]
       * initialize(self) [line 233]
       * handle_github_event(self, event_type, payload) [line 251]
       * handle_linear_event(self, event_type, payload) [line 270]
       * handle_workflow_update(self, workflow_id, status, progress) [line 286]
       * get_dashboard_stats(self) [line 303]
       * cleanup(self) [line 321]

📄 ./database.py
   Size: 18724 bytes, 490 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (4):
     - __init__(self, database_url) [line 200]
     - _setup_async_engine(self) [line 218]
     - __init__(self, db_manager) [line 266]
     - __init__(self, db_manager) [line 395]
   Classes (3):
     - DatabaseManager [line 197]
       * __init__(self, database_url) [line 200]
       * _setup_async_engine(self) [line 218]
       * initialize_schema(self) [line 236]
       * get_session(self) [line 251]
       * close(self) [line 257]
     - ProjectRepository [line 263]
       * __init__(self, db_manager) [line 266]
       * create_project(self, project) [line 269]
       * get_project(self, project_id) [line 298]
       * get_projects_by_user(self, user_id) [line 328]
       * pin_project(self, project_pin) [line 363]
     - WorkflowRepository [line 392]
       * __init__(self, db_manager) [line 395]
       * create_plan(self, plan) [line 398]
       * get_plans_by_project(self, project_id) [line 435]

📄 ./websocket.py
   Size: 15798 bytes, 417 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (7):
     - __init__(self, websocket, user_id, connection_id) [line 30]
     - subscribe(self, topic) [line 45]
     - unsubscribe(self, topic) [line 50]
     - is_subscribed(self, topic) [line 55]
     - __init__(self) [line 63]
     - setup_routes(self, app) [line 71]
     - get_connection_stats(self) [line 382]
   Classes (2):
     - WebSocketConnection [line 27]
       * __init__(self, websocket, user_id, connection_id) [line 30]
       * send_message(self, message) [line 38]
       * subscribe(self, topic) [line 45]
       * unsubscribe(self, topic) [line 50]
       * is_subscribed(self, topic) [line 55]
     - WebSocketManager [line 60]
       * __init__(self) [line 63]
       * setup_routes(self, app) [line 71]
       * handle_connection(self, websocket, user_id) [line 80]
       * _handle_messages(self, connection) [line 119]
       * _process_message(self, connection, message) [line 135]
       * _subscribe_connection(self, connection, topic) [line 161]
       * _unsubscribe_connection(self, connection, topic) [line 179]
       * _send_status_update(self, connection) [line 198]
       * _cleanup_connection(self, connection_id) [line 218]
       * broadcast(self, message, topic) [line 243]
       * send_to_user(self, user_id, message) [line 279]
       * send_project_update(self, project_id, update_data) [line 314]
       * send_workflow_update(self, workflow_id, status, progress, details) [line 330]
       * send_pr_update(self, project_id, pr_data) [line 350]
       * send_quality_gate_update(self, task_id, gate_data) [line 366]
       * get_connection_stats(self) [line 382]
       * cleanup(self) [line 402]

📄 ./validate_everything.py
   Size: 8653 bytes, 277 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (9):
     - print_header(title) [line 14]
     - print_success(message) [line 20]
     - print_error(message) [line 24]
     - print_info(message) [line 28]
     - test_imports() [line 32]
     - test_dashboard_creation() [line 76]
     - test_server_startup() [line 105]
     - test_models() [line 173]
     - main() [line 225]

📄 ./test_consolidated_system.py
   Size: 11945 bytes, 367 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: No module named 'dotenv'
   Functions (1):
     - main() [line 352]

📄 ./codegen_integration.py
   Size: 16911 bytes, 442 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package
   Functions (2):
     - __init__(self, org_id, token) [line 28]
     - _build_plan_prompt(self, requirements, title, description, context) [line 111]
   Classes (1):
     - CodegenPlanGenerator [line 25]
       * __init__(self, org_id, token) [line 28]
       * initialize(self) [line 42]
       * generate_plan(self, project_id, requirements, title, description, context) [line 54]
       * _build_plan_prompt(self, requirements, title, description, context) [line 111]
       * _parse_codegen_result(self, result, requirements) [line 163]
       * _extract_tasks_from_result(self, result) [line 195]
       * _extract_summary_from_result(self, result) [line 248]
       * _calculate_complexity_score(self, result) [line 253]
       * _extract_duration_from_result(self, result) [line 258]
       * _extract_risks_from_result(self, result) [line 263]
       * _generate_fallback_plan(self, requirements, title, description) [line 272]
       * _analyze_requirements_for_tasks(self, requirements) [line 307]
       * create_linear_issues_from_plan(self, plan, project_id) [line 412]
       * create_github_issues_from_plan(self, plan, owner, repo) [line 427]

📄 ./consolidated_models.py
   Size: 13971 bytes, 422 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (6):
     - to_dict(self) [line 94]
     - to_dict(self) [line 154]
     - progress_percentage(self) [line 204]
     - to_dict(self) [line 211]
     - to_dict(self) [line 248]
     - to_dict(self) [line 295]
   Classes (24):
     - FlowStatus [line 14]
     - TaskStatus [line 25]
     - ServiceStatus [line 35]
     - ProjectStatus [line 43]
     - QualityGateStatus [line 51]
     - Project [line 61]
       * to_dict(self) [line 94]
     - Task [line 127]
       * to_dict(self) [line 154]
     - Flow [line 181]
       * progress_percentage(self) [line 204]
       * to_dict(self) [line 211]
     - QualityGate [line 234]
       * to_dict(self) [line 248]
     - UserSettings [line 266]
       * to_dict(self) [line 295]
     - ServiceStatusResponse [line 319]
     - ProjectCreateRequest [line 332]
     - ProjectUpdateRequest [line 339]
     - FlowStartRequest [line 346]
     - PlanGenerateRequest [line 354]
     - CodegenTaskRequest [line 361]
     - SystemHealthResponse [line 369]
     - DashboardResponse [line 380]
     - WebSocketEvent [line 389]
     - ProjectUpdateEvent [line 399]
     - FlowUpdateEvent [line 404]
     - TaskUpdateEvent [line 409]
     - QualityGateEvent [line 414]
     - SystemHealthEvent [line 419]

📄 ./__init__.py
   Size: 887 bytes, 38 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import with no known parent package

📄 ./comprehensive_validation.py
   Size: 12617 bytes, 328 lines
   Syntax Valid: ✅
   Import Test: ✅
   Functions (9):
     - main() [line 288]
     - __init__(self) [line 19]
     - analyze_file(self, file_path) [line 31]
     - _analyze_function(self, node) [line 111]
     - _analyze_class(self, node) [line 143]
     - _test_import(self, file_path, file_info) [line 172]
     - __init__(self) [line 198]
     - validate_all_files(self) [line 202]
     - generate_report(self, results) [line 223]
   Classes (2):
     - CodeAnalyzer [line 16]
       * __init__(self) [line 19]
       * analyze_file(self, file_path) [line 31]
       * _analyze_function(self, node) [line 111]
       * _analyze_class(self, node) [line 143]
       * _test_import(self, file_path, file_info) [line 172]
     - DashboardValidator [line 195]
       * __init__(self) [line 198]
       * validate_all_files(self) [line 202]
       * generate_report(self, results) [line 223]

📄 ./services/strands_orchestrator.py
   Size: 22084 bytes, 556 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (2):
     - __init__(self) [line 44]
     - _init_layer_managers(self) [line 52]
   Classes (5):
     - StrandsOrchestrator [line 35]
       * __init__(self) [line 44]
       * _init_layer_managers(self) [line 52]
       * start_workflow(self, project_id, requirements, flow_name, auto_execute) [line 96]
       * _init_strands_workflow(self, flow) [line 151]
       * _create_prefect_flow(self, flow) [line 166]
       * _setup_controlflow(self, flow) [line 184]
       * _generate_workflow_plan(self, flow) [line 202]
       * _execute_workflow(self, flow) [line 235]
       * get_workflow(self, flow_id) [line 275]
       * pause_workflow(self, flow_id) [line 279]
       * resume_workflow(self, flow_id) [line 303]
       * stop_workflow(self, flow_id) [line 327]
       * monitor_workflow_execution(self, flow_id) [line 357]
       * _update_workflow_status(self, flow) [line 372]
       * check_workflow_status(self) [line 408]
       * check_mcp_status(self) [line 419]
       * check_controlflow_status(self) [line 430]
       * check_prefect_status(self) [line 441]
     - MockStrandsWorkflowManager [line 454]
       * create_workflow(self, name, description, project_id) [line 457]
       * generate_plan(self, workflow_id, requirements) [line 462]
       * check_health(self) [line 487]
     - MockMCPManager [line 491]
       * execute_task(self, task_description, context) [line 494]
       * check_health(self) [line 499]
     - MockControlFlowManager [line 503]
       * create_flow(self, name, description, project_context) [line 506]
       * create_task(self, flow_id, name, description, task_type) [line 511]
       * pause_flow(self, flow_id) [line 516]
       * resume_flow(self, flow_id) [line 519]
       * cancel_flow(self, flow_id) [line 522]
       * get_task_status(self, task_id) [line 525]
       * check_health(self) [line 528]
     - MockPrefectManager [line 532]
       * create_flow_run(self, flow_name, parameters) [line 535]
       * start_flow_run(self, flow_run_id) [line 540]
       * pause_flow_run(self, flow_run_id) [line 543]
       * resume_flow_run(self, flow_run_id) [line 546]
       * cancel_flow_run(self, flow_run_id) [line 549]
       * get_flow_run_status(self, flow_run_id) [line 552]
       * check_health(self) [line 555]

📄 ./services/monitoring_service.py
   Size: 20999 bytes, 534 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (6):
     - __init__(self) [line 24]
     - _calculate_overall_status(self, system_metrics, services) [line 367]
     - _is_cache_valid(self, cache_key, now) [line 465]
     - _store_health_history(self, health_data) [line 475]
     - _start_background_monitoring(self) [line 483]
     - stop_monitoring(self) [line 530]
   Classes (1):
     - MonitoringService [line 18]
       * __init__(self) [line 24]
       * get_system_health(self) [line 44]
       * _get_system_metrics(self) [line 95]
       * _get_all_service_statuses(self) [line 171]
       * _check_service_health(self, service_name) [line 212]
       * _check_github_health(self) [line 243]
       * _check_linear_health(self) [line 256]
       * _check_slack_health(self) [line 267]
       * _check_codegen_health(self) [line 278]
       * _check_database_health(self) [line 289]
       * _check_orchestration_health(self, service_name) [line 298]
       * _get_workflow_statistics(self) [line 334]
       * _get_recent_error_count(self) [line 358]
       * _calculate_overall_status(self, system_metrics, services) [line 367]
       * _check_system_alerts(self, metrics) [line 400]
       * _create_alert(self, alert_type, message, level, data) [line 438]
       * _is_cache_valid(self, cache_key, now) [line 465]
       * _store_health_history(self, health_data) [line 475]
       * _start_background_monitoring(self) [line 483]
       * _background_health_monitor(self) [line 488]
       * get_alerts(self, limit) [line 502]
       * acknowledge_alert(self, alert_id) [line 506]
       * get_health_history(self, hours) [line 516]
       * update_alert_thresholds(self, thresholds) [line 525]
       * stop_monitoring(self) [line 530]

📄 ./services/quality_service.py
   Size: 19920 bytes, 468 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (5):
     - __init__(self) [line 22]
     - _init_default_quality_gates(self) [line 30]
     - _evaluate_condition(self, value, operator, threshold) [line 224]
     - _get_mock_metrics(self, project_id) [line 277]
     - _generate_recommendations(self, gate_results) [line 341]
   Classes (1):
     - QualityService [line 16]
       * __init__(self) [line 22]
       * _init_default_quality_gates(self) [line 30]
       * get_quality_gates(self, project_id) [line 99]
       * _create_default_gates_for_project(self, project_id) [line 107]
       * validate_all_gates(self, project_id) [line 125]
       * _validate_single_gate(self, gate, metrics) [line 175]
       * _evaluate_condition(self, value, operator, threshold) [line 224]
       * _get_project_metrics(self, project_id) [line 242]
       * _analyze_project_with_graph_sitter(self, project_id) [line 261]
       * _get_mock_metrics(self, project_id) [line 277]
       * _update_adaptive_thresholds(self, project_id, metrics) [line 308]
       * _generate_recommendations(self, gate_results) [line 341]
       * validate_pr_quality(self, project_id, pr_url) [line 377]
       * _run_pr_specific_checks(self, pr_url) [line 403]
       * get_validation_history(self, project_id) [line 425]
       * create_custom_gate(self, project_id, name, metric, threshold, operator, severity) [line 429]
       * delete_quality_gate(self, project_id, gate_id) [line 457]

📄 ./services/codegen_service.py
   Size: 23306 bytes, 645 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (10):
     - __init__(self) [line 24]
     - _create_plan_prompt(self, project_id, requirements, include_quality_gates) [line 275]
     - _create_task_prompt(self, task) [line 335]
     - _create_pr_validation_prompt(self, pr_url, quality_criteria) [line 364]
     - _create_followup_prompt(self, completed_task, result) [line 401]
     - _parse_plan_result(self, result) [line 452]
     - _parse_validation_result(self, result) [line 481]
     - _parse_followup_tasks(self, result) [line 510]
     - __init__(self, org_id, token) [line 528]
     - __init__(self, task_id, prompt) [line 555]
   Classes (3):
     - CodegenService [line 18]
       * __init__(self) [line 24]
       * check_status(self) [line 35]
       * _get_agent(self) [line 52]
       * generate_plan(self, project_id, requirements, include_quality_gates) [line 71]
       * create_task(self, task_type, project_id, prompt, context) [line 111]
       * execute_task(self, task_id) [line 135]
       * get_task(self, task_id) [line 184]
       * get_all_tasks(self) [line 188]
       * cancel_task(self, task_id) [line 192]
       * validate_pr(self, pr_url, quality_criteria) [line 219]
       * create_followup_tasks(self, completed_task, result) [line 249]
       * _create_plan_prompt(self, project_id, requirements, include_quality_gates) [line 275]
       * _create_task_prompt(self, task) [line 335]
       * _create_pr_validation_prompt(self, pr_url, quality_criteria) [line 364]
       * _create_followup_prompt(self, completed_task, result) [line 401]
       * _wait_for_task_completion(self, task, timeout) [line 428]
       * _parse_plan_result(self, result) [line 452]
       * _parse_validation_result(self, result) [line 481]
       * _parse_followup_tasks(self, result) [line 510]
     - MockCodegenAgent [line 525]
       * __init__(self, org_id, token) [line 528]
       * run(self, prompt) [line 533]
       * cancel_task(self, task_id) [line 547]
     - MockCodegenTask [line 552]
       * __init__(self, task_id, prompt) [line 555]
       * _simulate_completion(self) [line 565]
       * refresh(self) [line 642]

📄 ./services/__init__.py
   Size: 462 bytes, 19 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package

📄 ./services/project_service.py
   Size: 16584 bytes, 400 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (3):
     - __init__(self) [line 26]
     - _init_github_client(self) [line 35]
     - _parse_repo_url(self, repo_url) [line 245]
   Classes (2):
     - ProjectService [line 20]
       * __init__(self) [line 26]
       * _init_github_client(self) [line 35]
       * get_all_projects(self) [line 57]
       * get_pinned_projects(self) [line 61]
       * get_project(self, project_id) [line 65]
       * create_project(self, repo_url, requirements, auto_pin) [line 69]
       * update_project(self, project_id, requirements, is_pinned, flow_status) [line 127]
       * delete_project(self, project_id) [line 152]
       * analyze_project(self, project_id) [line 160]
       * get_github_repositories(self) [line 183]
       * get_user_settings(self) [line 222]
       * update_user_settings(self, settings) [line 226]
       * _parse_repo_url(self, repo_url) [line 245]
       * _fetch_github_repo_details(self, owner, repo_name) [line 277]
     - MockGitHubClient [line 322]
       * get_repositories(self) [line 325]
       * get_repo_details(self, owner, repo_name) [line 381]

📄 ./workflows/__init__.py
   Size: 788 bytes, 24 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package

📄 ./workflows/mcp_integration.py
   Size: 21055 bytes, 571 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (2):
     - __init__(self) [line 30]
     - _build_agent_prompt(self, task) [line 298]
   Classes (1):
     - MCPAgentManager [line 27]
       * __init__(self) [line 30]
       * initialize(self) [line 40]
       * _setup_default_tools(self) [line 56]
       * execute_task(self, task, execution_id) [line 99]
       * _get_or_create_mcp_client(self, execution_id) [line 144]
       * _create_agent_config(self, task) [line 158]
       * _create_agent(self, mcp_client, agent_config) [line 202]
       * _execute_task_with_agent(self, task, agent_id, mcp_client) [line 222]
       * _run_agent_task(self, agent_id, task, mcp_client) [line 270]
       * _build_agent_prompt(self, task) [line 298]
       * get_task_progress(self, task_id) [line 344]
       * cancel_execution(self, execution_id) [line 369]
       * pause_execution(self, execution_id) [line 413]
       * resume_execution(self, execution_id) [line 435]
       * get_execution_logs(self, execution_id) [line 457]
       * get_metrics(self, execution_id) [line 499]
       * get_stats(self) [line 539]
       * cleanup(self) [line 554]

📄 ./workflows/controlflow_integration.py
   Size: 16395 bytes, 451 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (4):
     - __init__(self) [line 32]
     - _select_agent_for_task(self, task) [line 153]
     - _build_task_instructions(self, task) [line 171]
     - _build_task_context(self, task) [line 204]
   Classes (1):
     - ControlFlowManager [line 29]
       * __init__(self) [line 32]
       * initialize(self) [line 42]
       * _setup_default_agents(self) [line 58]
       * execute_task(self, task, execution_id) [line 94]
       * _get_or_create_flow(self, execution_id) [line 141]
       * _select_agent_for_task(self, task) [line 153]
       * _build_task_instructions(self, task) [line 171]
       * _build_task_context(self, task) [line 204]
       * _execute_task_async(self, task, cf_task, execution_id) [line 226]
       * get_task_status(self, task_id) [line 254]
       * cancel_execution(self, execution_id) [line 289]
       * pause_execution(self, execution_id) [line 320]
       * resume_execution(self, execution_id) [line 339]
       * get_execution_logs(self, execution_id) [line 358]
       * get_metrics(self, execution_id) [line 388]
       * get_stats(self) [line 419]
       * cleanup(self) [line 434]

📄 ./workflows/orchestrator.py
   Size: 17898 bytes, 475 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (2):
     - __init__(self) [line 39]
     - _calculate_execution_time(self, execution_id) [line 328]
   Classes (2):
     - OrchestrationLayer [line 22]
     - WorkflowOrchestrator [line 29]
       * __init__(self) [line 39]
       * initialize(self) [line 50]
       * execute_workflow(self, plan, execution_config) [line 63]
       * _register_execution_callbacks(self, execution_id) [line 119]
       * execute_task_layer(self, task, execution_id, layer) [line 130]
       * get_execution_status(self, execution_id) [line 161]
       * cancel_execution(self, execution_id) [line 172]
       * pause_execution(self, execution_id) [line 207]
       * resume_execution(self, execution_id) [line 232]
       * get_execution_logs(self, execution_id) [line 257]
       * get_execution_metrics(self, execution_id) [line 284]
       * _calculate_execution_time(self, execution_id) [line 328]
       * _on_task_started(self, execution_id, task_id, layer) [line 341]
       * _on_task_completed(self, execution_id, task_id, layer, result) [line 359]
       * _on_task_failed(self, execution_id, task_id, layer, error) [line 377]
       * _on_workflow_progress(self, execution_id, progress) [line 395]
       * cleanup_completed_executions(self, max_age_hours) [line 403]
       * get_orchestrator_stats(self) [line 430]
       * cleanup(self) [line 459]

📄 ./workflows/prefect_integration.py
   Size: 15474 bytes, 434 lines
   Syntax Valid: ✅
   Import Test: ❌
   Import Error: attempted relative import beyond top-level package
   Functions (2):
     - __init__(self) [line 38]
     - _count_completed_tasks(self, state) [line 390]
   Classes (1):
     - PrefectFlowManager [line 35]
       * __init__(self) [line 38]
       * initialize(self) [line 47]
       * _register_workflow_flows(self) [line 65]
       * start_workflow_flow(self, plan, execution_id, config) [line 152]
       * get_flow_status(self, flow_run_id) [line 205]
       * cancel_flow(self, flow_run_id) [line 238]
       * pause_flow(self, execution_id) [line 263]
       * resume_flow(self, execution_id) [line 293]
       * get_execution_logs(self, execution_id) [line 323]
       * get_metrics(self, execution_id) [line 356]
       * _count_completed_tasks(self, state) [line 390]
       * get_stats(self) [line 401]
       * cleanup(self) [line 415]