"""
Prefect-based Orchestration System

This module implements the core orchestration system using Prefect for managing
autonomous CI/CD workflows, integrating with Codegen SDK, Linear, and GitHub.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import asdict

import prefect
from prefect import flow, task, get_run_logger
from prefect.client.orchestration import PrefectClient
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule, IntervalSchedule
from prefect.blocks.system import Secret
from prefect_github import GitHubRepository
from prefect_slack import SlackWebhook

from codegen import Agent as CodegenAgent
from graph_sitter.shared.logging.get_logger import get_logger

from .workflow_definitions import (
    AutonomousWorkflowType, WorkflowConfig, WorkflowExecution, 
    WorkflowStatus, OrchestrationMetrics, DEFAULT_WORKFLOW_CONFIGS
)
from .monitoring import OrchestrationMonitor
from .recovery import RecoveryManager

logger = get_logger(__name__)


class PrefectOrchestrator:
    """
    Main orchestration system using Prefect for autonomous CI/CD workflows
    """
    
    def __init__(
        self,
        codegen_org_id: str,
        codegen_token: str,
        github_token: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        prefect_api_url: Optional[str] = None
    ):
        self.codegen_org_id = codegen_org_id
        self.codegen_token = codegen_token
        self.github_token = github_token
        self.slack_webhook_url = slack_webhook_url
        
        # Initialize Prefect client
        self.prefect_client = PrefectClient(api=prefect_api_url) if prefect_api_url else PrefectClient()
        
        # Initialize integrations
        self.codegen_agent = CodegenAgent(org_id=codegen_org_id, token=codegen_token)
        
        # Workflow management
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.deployments: Dict[str, Deployment] = {}
        
        # Monitoring and recovery
        self.monitor = OrchestrationMonitor(self)
        self.recovery_manager = RecoveryManager(self)
        
        # Metrics
        self.metrics = OrchestrationMetrics()
        
        # Load default configurations
        self._load_default_workflows()
    
    def _load_default_workflows(self):
        """Load default workflow configurations"""
        for workflow_type, config in DEFAULT_WORKFLOW_CONFIGS.items():
            self.workflow_configs[workflow_type.value] = config
            logger.info(f"Loaded default workflow: {config.name}")
    
    async def initialize(self):
        """Initialize the orchestration system"""
        logger.info("Initializing Prefect orchestration system...")
        
        try:
            # Setup Prefect blocks for secrets
            await self._setup_prefect_blocks()
            
            # Deploy workflows
            await self._deploy_workflows()
            
            # Start monitoring
            await self.monitor.start()
            
            # Initialize recovery manager
            await self.recovery_manager.initialize()
            
            logger.info("Prefect orchestration system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestration system: {e}")
            raise
    
    async def _setup_prefect_blocks(self):
        """Setup Prefect blocks for secrets and configurations"""
        
        # Store Codegen credentials
        codegen_secret = Secret(value=self.codegen_token)
        await codegen_secret.save("codegen-token", overwrite=True)
        
        if self.github_token:
            github_secret = Secret(value=self.github_token)
            await github_secret.save("github-token", overwrite=True)
        
        if self.slack_webhook_url:
            slack_webhook = SlackWebhook(url=self.slack_webhook_url)
            await slack_webhook.save("slack-webhook", overwrite=True)
        
        logger.info("Prefect blocks configured")
    
    async def _deploy_workflows(self):
        """Deploy all configured workflows"""
        
        for workflow_id, config in self.workflow_configs.items():
            try:
                deployment = await self._create_deployment(workflow_id, config)
                self.deployments[workflow_id] = deployment
                logger.info(f"Deployed workflow: {config.name}")
                
            except Exception as e:
                logger.error(f"Failed to deploy workflow {workflow_id}: {e}")
    
    async def _create_deployment(self, workflow_id: str, config: WorkflowConfig) -> Deployment:
        """Create a Prefect deployment for a workflow"""
        
        # Create the flow function dynamically
        flow_func = self._create_flow_function(workflow_id, config)
        
        # Determine schedule
        schedule = None
        for trigger in config.triggers:
            if trigger.trigger_type == "schedule":
                if trigger.cron_expression:
                    schedule = CronSchedule(cron=trigger.cron_expression)
                elif trigger.interval_seconds:
                    schedule = IntervalSchedule(interval=timedelta(seconds=trigger.interval_seconds))
                break
        
        # Create deployment
        deployment = Deployment.build_from_flow(
            flow=flow_func,
            name=f"{workflow_id}-deployment",
            schedule=schedule,
            parameters=config.parameters,
            tags=[config.workflow_type.value, f"priority-{config.priority.value}"],
            description=config.description
        )
        
        # Deploy
        deployment_id = await deployment.apply()
        logger.info(f"Created deployment {deployment_id} for workflow {workflow_id}")
        
        return deployment
    
    def _create_flow_function(self, workflow_id: str, config: WorkflowConfig):
        """Create a Prefect flow function for a workflow"""
        
        @flow(
            name=config.name,
            description=config.description,
            timeout_seconds=config.timeout_seconds,
            retries=config.retry_config.max_retries,
            retry_delay_seconds=config.retry_config.retry_delay_seconds
        )
        async def workflow_flow(parameters: Dict[str, Any] = None):
            """Generated Prefect flow for autonomous workflow"""
            
            logger = get_run_logger()
            execution_id = str(uuid.uuid4())
            
            # Create execution record
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_config=config,
                status=WorkflowStatus.RUNNING,
                started_at=datetime.now()
            )
            
            self.active_executions[execution_id] = execution
            
            try:
                logger.info(f"Starting workflow execution: {execution_id}")
                
                # Execute workflow based on type
                result = await self._execute_workflow_logic(
                    config.workflow_type, 
                    parameters or config.parameters,
                    execution_id
                )
                
                # Update execution
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now()
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                execution.result = result
                
                # Update metrics
                self.metrics.successful_workflows += 1
                
                logger.info(f"Workflow execution completed: {execution_id}")
                
                # Send notifications if configured
                if config.notification_config.on_success:
                    await self._send_notification(execution, "success")
                
                return result
                
            except Exception as e:
                logger.error(f"Workflow execution failed: {execution_id} - {e}")
                
                # Update execution
                execution.status = WorkflowStatus.FAILED
                execution.completed_at = datetime.now()
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                execution.error_message = str(e)
                execution.error_type = type(e).__name__
                
                # Update metrics
                self.metrics.failed_workflows += 1
                
                # Send failure notification
                if config.notification_config.on_failure:
                    await self._send_notification(execution, "failure")
                
                # Trigger recovery if needed
                await self.recovery_manager.handle_workflow_failure(execution)
                
                raise
            
            finally:
                # Clean up
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
        
        return workflow_flow
    
    async def _execute_workflow_logic(
        self, 
        workflow_type: AutonomousWorkflowType, 
        parameters: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute the core logic for different workflow types"""
        
        logger.info(f"Executing {workflow_type.value} workflow logic")
        
        if workflow_type == AutonomousWorkflowType.FAILURE_ANALYSIS:
            return await self._execute_failure_analysis(parameters, execution_id)
        
        elif workflow_type == AutonomousWorkflowType.PERFORMANCE_MONITORING:
            return await self._execute_performance_monitoring(parameters, execution_id)
        
        elif workflow_type == AutonomousWorkflowType.DEPENDENCY_MANAGEMENT:
            return await self._execute_dependency_management(parameters, execution_id)
        
        elif workflow_type == AutonomousWorkflowType.HEALTH_CHECK:
            return await self._execute_health_check(parameters, execution_id)
        
        elif workflow_type == AutonomousWorkflowType.CODEGEN_TASK_EXECUTION:
            return await self._execute_codegen_task(parameters, execution_id)
        
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    @task
    async def _execute_failure_analysis(self, parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute autonomous failure analysis workflow"""
        
        logger = get_run_logger()
        logger.info("Starting autonomous failure analysis")
        
        # Get workflow run ID from parameters or environment
        workflow_run_id = parameters.get("workflow_run_id") or os.environ.get("GITHUB_WORKFLOW_RUN_ID")
        
        if not workflow_run_id:
            raise ValueError("No workflow run ID provided for failure analysis")
        
        # Use Codegen agent to analyze the failure
        prompt = f"""
        Analyze the failed GitHub workflow run {workflow_run_id} and:
        1. Identify the root cause of the failure
        2. Determine if it's auto-fixable
        3. If auto-fixable and enabled, create a PR with the fix
        4. Provide detailed analysis and recommendations
        
        Parameters: {json.dumps(parameters, indent=2)}
        """
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Wait for completion with timeout
        timeout_seconds = 1800  # 30 minutes
        start_time = datetime.now()
        
        while task.status not in ['completed', 'failed']:
            if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                raise TimeoutError(f"Failure analysis timed out after {timeout_seconds} seconds")
            
            await asyncio.sleep(10)
            task.refresh()
        
        if task.status == 'failed':
            raise Exception(f"Codegen failure analysis failed: {task.result}")
        
        # Update metrics
        self.metrics.autonomous_fixes_applied += 1
        
        return {
            "analysis_result": task.result,
            "codegen_task_id": task.id,
            "workflow_run_id": workflow_run_id,
            "auto_fix_applied": parameters.get("auto_fix_enabled", False)
        }
    
    @task
    async def _execute_performance_monitoring(self, parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute performance monitoring workflow"""
        
        logger = get_run_logger()
        logger.info("Starting performance monitoring")
        
        # Use Codegen agent for performance analysis
        prompt = f"""
        Perform comprehensive performance monitoring and analysis:
        1. Analyze recent CI/CD performance metrics
        2. Compare against baseline from {parameters.get('baseline_branch', 'develop')}
        3. Detect any performance regressions above {parameters.get('alert_threshold_percent', 20)}%
        4. If auto-optimization is enabled, suggest or implement optimizations
        5. Generate performance report with recommendations
        
        Parameters: {json.dumps(parameters, indent=2)}
        """
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Wait for completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(10)
            task.refresh()
        
        if task.status == 'failed':
            raise Exception(f"Performance monitoring failed: {task.result}")
        
        # Update metrics
        self.metrics.performance_optimizations += 1
        
        return {
            "performance_report": task.result,
            "codegen_task_id": task.id,
            "baseline_branch": parameters.get('baseline_branch'),
            "optimizations_applied": parameters.get('auto_optimize', False)
        }
    
    @task
    async def _execute_dependency_management(self, parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute autonomous dependency management workflow"""
        
        logger = get_run_logger()
        logger.info("Starting dependency management")
        
        prompt = f"""
        Perform autonomous dependency management:
        1. Analyze current dependencies for security vulnerabilities
        2. Check for available updates using {parameters.get('update_strategy', 'smart')} strategy
        3. Prioritize security updates with {parameters.get('security_priority', 'high')} priority
        4. If test_before_merge is enabled, run tests before applying updates
        5. Create PRs for dependency updates with proper testing
        
        Parameters: {json.dumps(parameters, indent=2)}
        """
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Wait for completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(15)
            task.refresh()
        
        if task.status == 'failed':
            raise Exception(f"Dependency management failed: {task.result}")
        
        return {
            "dependency_report": task.result,
            "codegen_task_id": task.id,
            "updates_applied": True,
            "security_issues_resolved": 0  # Would be parsed from result
        }
    
    @task
    async def _execute_health_check(self, parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute system health check workflow"""
        
        logger = get_run_logger()
        logger.info("Starting system health check")
        
        # Perform comprehensive health check
        health_status = await self.monitor.check_system_health()
        
        # If health is degraded and auto-recovery is enabled, trigger recovery
        if health_status["overall_health"] < 80 and parameters.get("auto_recovery", True):
            logger.warning(f"System health degraded: {health_status['overall_health']}% - triggering recovery")
            await self.recovery_manager.trigger_recovery(health_status)
        
        # Update metrics
        self.metrics.system_health_score = health_status["overall_health"]
        self.metrics.last_health_check = datetime.now()
        
        return {
            "health_status": health_status,
            "recovery_triggered": health_status["overall_health"] < 80,
            "timestamp": datetime.now().isoformat()
        }
    
    @task
    async def _execute_codegen_task(self, parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute a Codegen task as part of orchestrated workflow"""
        
        logger = get_run_logger()
        logger.info("Executing Codegen task")
        
        prompt = parameters.get("prompt")
        if not prompt:
            raise ValueError("No prompt provided for Codegen task")
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Wait for completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(5)
            task.refresh()
        
        if task.status == 'failed':
            raise Exception(f"Codegen task failed: {task.result}")
        
        # Update metrics
        self.metrics.codegen_tasks_executed += 1
        
        return {
            "task_result": task.result,
            "codegen_task_id": task.id,
            "execution_time": task.duration if hasattr(task, 'duration') else None
        }
    
    async def _send_notification(self, execution: WorkflowExecution, status: str):
        """Send notifications for workflow execution"""
        
        try:
            if "slack" in execution.workflow_config.notification_config.channels:
                await self._send_slack_notification(execution, status)
            
            if "linear" in execution.workflow_config.notification_config.channels:
                await self._send_linear_notification(execution, status)
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def _send_slack_notification(self, execution: WorkflowExecution, status: str):
        """Send Slack notification"""
        
        if not self.slack_webhook_url:
            return
        
        try:
            slack_webhook = await SlackWebhook.load("slack-webhook")
            
            color = "good" if status == "success" else "danger"
            title = f"Workflow {status.title()}: {execution.workflow_config.name}"
            
            message = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "fields": [
                        {"title": "Execution ID", "value": execution.execution_id, "short": True},
                        {"title": "Duration", "value": f"{execution.duration_seconds:.1f}s", "short": True},
                        {"title": "Status", "value": execution.status.value, "short": True}
                    ]
                }]
            }
            
            await slack_webhook.notify(message)
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_linear_notification(self, execution: WorkflowExecution, status: str):
        """Send Linear notification by creating/updating issues"""
        
        # This would integrate with Linear API to create issues or comments
        # Implementation depends on Linear integration setup
        pass
    
    async def trigger_workflow(
        self, 
        workflow_type: Union[str, AutonomousWorkflowType], 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Manually trigger a workflow execution"""
        
        if isinstance(workflow_type, str):
            workflow_type = AutonomousWorkflowType(workflow_type)
        
        workflow_id = workflow_type.value
        
        if workflow_id not in self.workflow_configs:
            raise ValueError(f"Workflow {workflow_id} not configured")
        
        # Create flow run
        deployment = self.deployments.get(workflow_id)
        if not deployment:
            raise ValueError(f"No deployment found for workflow {workflow_id}")
        
        # Trigger the flow run
        flow_run = await self.prefect_client.create_flow_run_from_deployment(
            deployment.id,
            parameters=parameters or {}
        )
        
        logger.info(f"Triggered workflow {workflow_id} with run ID: {flow_run.id}")
        
        return str(flow_run.id)
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a workflow execution"""
        return self.active_executions.get(execution_id)
    
    async def get_metrics(self) -> OrchestrationMetrics:
        """Get current orchestration metrics"""
        
        # Update real-time metrics
        self.metrics.active_workflows = len(self.active_executions)
        self.metrics.total_workflows_executed = (
            self.metrics.successful_workflows + 
            self.metrics.failed_workflows + 
            self.metrics.cancelled_workflows
        )
        
        if self.metrics.total_workflows_executed > 0:
            self.metrics.error_rate_percent = (
                self.metrics.failed_workflows / self.metrics.total_workflows_executed * 100
            )
        
        return self.metrics
    
    async def shutdown(self):
        """Shutdown the orchestration system"""
        
        logger.info("Shutting down Prefect orchestration system...")
        
        # Stop monitoring
        await self.monitor.stop()
        
        # Cancel active executions
        for execution_id in list(self.active_executions.keys()):
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            del self.active_executions[execution_id]
        
        logger.info("Prefect orchestration system shutdown complete")

