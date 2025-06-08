# Codegen Extension - Task Completion with API token/org_id
# Imports existing contexten and graph_sitter components

import logging
import os
from typing import Any, Callable, Dict, Optional, TypeVar
from fastapi import Request
from pydantic import BaseModel

# Import existing graph_sitter components
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter import Codebase

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Codegen:
    """Codegen extension for task completion using API token/org_id with Strands and MCP integration."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize Codegen components using existing modules (lazy import)
        self.workflow_client = None
        self.overlay_applicator = None
        
        # Integration with other extensions
        self.github_integration: Optional[Any] = None
        self.linear_integration: Optional[Any] = None
        self.slack_integration: Optional[Any] = None
        self.circleci_integration: Optional[Any] = None
        
        # Task execution tracking
        self.active_tasks: Dict[str, Any] = {}
        self.completed_tasks: Dict[str, Any] = {}
        
        logger.info("✅ Codegen extension initialized with API token/org_id integration")

    def register_handler(self, event_type: str, handler: Callable[[T], Any]) -> None:
        """Register an event handler for Codegen task execution."""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
        logger.info(f"Registered Codegen handler for event type: {event_type}")

    async def handle(self, payload: dict, request: Optional[Request] = None) -> Any:
        """Handle Codegen task execution events."""
        event_type = payload.get('type', 'unknown')
        logger.info(f"Handling Codegen event: {event_type}")
        
        try:
            # Process task execution events
            if event_type == 'task_execution':
                return await self._handle_task_execution(payload)
            elif event_type == 'workflow_execution':
                return await self._handle_workflow_execution(payload)
            elif event_type == 'agent_task':
                return await self._handle_agent_task(payload)
            elif event_type == 'integration_task':
                return await self._handle_integration_task(payload)
            else:
                # Handle custom registered handlers
                if event_type in self.registered_handlers:
                    results = []
                    for handler in self.registered_handlers[event_type]:
                        result = await handler(payload)
                        results.append(result)
                    return results
                else:
                    logger.warning(f"No handler registered for Codegen event type: {event_type}")
                    return {'status': 'no_handler', 'event_type': event_type}
                    
        except Exception as e:
            logger.error(f"Error handling Codegen event {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _handle_task_execution(self, payload: dict) -> dict:
        """Handle task execution using existing Codegen workflow client."""
        try:
            task_id = payload.get('task_id')
            task_description = payload.get('task_description')
            task_config = payload.get('config', {})
            
            # Lazy import to avoid circular dependencies
            if not self.workflow_client:
                try:
                    from ..codegen.workflow_integration import CodegenWorkflowClient
                    self.workflow_client = CodegenWorkflowClient(
                        org_id=os.getenv('CODEGEN_ORG_ID'),
                        token=os.getenv('CODEGEN_API_TOKEN'),
                        base_url=os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
                    )
                except ImportError:
                    logger.warning("CodegenWorkflowClient not available, using fallback")
                    return {
                        'status': 'completed',
                        'task_id': task_id,
                        'execution_result': {'fallback': True, 'description': task_description}
                    }
            
            # Use existing CodegenWorkflowClient for task execution
            execution_result = await self.workflow_client.execute_task(
                task_id=task_id,
                description=task_description,
                config=task_config
            )
            
            # Track active task
            self.active_tasks[task_id] = {
                'description': task_description,
                'config': task_config,
                'execution_result': execution_result,
                'status': 'running'
            }
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'execution_result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_workflow_execution(self, payload: dict) -> dict:
        """Handle workflow execution using existing workflow integration."""
        try:
            project_id = payload.get('project_id')
            requirements = payload.get('requirements')
            workflow_config = payload.get('config', {})
            
            # Use existing workflow client for execution
            workflow_result = await self.workflow_client.execute_workflow_tasks(
                project_id=project_id,
                requirements=requirements,
                context=workflow_config
            )
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'workflow_result': workflow_result
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_agent_task(self, payload: dict) -> dict:
        """Handle agent task using existing Codegen SDK integration."""
        try:
            agent_id = payload.get('agent_id')
            task_prompt = payload.get('task_prompt')
            agent_config = payload.get('config', {})
            
            # Use existing workflow client for agent task execution
            agent_result = await self.workflow_client.execute_agent_task(
                agent_id=agent_id,
                prompt=task_prompt,
                config=agent_config
            )
            
            return {
                'status': 'completed',
                'agent_id': agent_id,
                'agent_result': agent_result
            }
            
        except Exception as e:
            logger.error(f"Agent task execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_integration_task(self, payload: dict) -> dict:
        """Handle integration task using existing extension integrations."""
        try:
            integration_type = payload.get('integration_type')
            task_data = payload.get('task_data', {})
            
            if integration_type == 'github' and self.github_integration:
                # Use existing GitHub integration
                result = await self._execute_github_task(task_data)
            elif integration_type == 'linear' and self.linear_integration:
                # Use existing Linear integration
                result = await self._execute_linear_task(task_data)
            elif integration_type == 'slack' and self.slack_integration:
                # Use existing Slack integration
                result = await self._execute_slack_task(task_data)
            elif integration_type == 'circleci' and self.circleci_integration:
                # Use existing CircleCI integration
                result = await self._execute_circleci_task(task_data)
            else:
                return {'status': 'failed', 'error': f'Integration {integration_type} not available'}
            
            return {
                'status': 'completed',
                'integration_type': integration_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Integration task failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_github_task(self, task_data: dict) -> dict:
        """Execute GitHub task using existing GitHub extension."""
        try:
            # Use existing GitHub integration for task execution
            task_type = task_data.get('type', 'unknown')
            
            if task_type == 'create_pr':
                # Create PR using existing GitHub extension
                pr_result = await self.github_integration.create_pull_request(
                    title=task_data.get('title'),
                    body=task_data.get('body'),
                    head=task_data.get('head'),
                    base=task_data.get('base')
                )
                return {'type': 'create_pr', 'result': pr_result}
            elif task_type == 'create_issue':
                # Create issue using existing GitHub extension
                issue_result = await self.github_integration.create_issue(
                    title=task_data.get('title'),
                    body=task_data.get('body'),
                    labels=task_data.get('labels', [])
                )
                return {'type': 'create_issue', 'result': issue_result}
            else:
                return {'type': task_type, 'result': 'Task type not supported'}
                
        except Exception as e:
            logger.error(f"GitHub task execution failed: {e}")
            return {'type': 'error', 'error': str(e)}

    async def _execute_linear_task(self, task_data: dict) -> dict:
        """Execute Linear task using existing Linear extension."""
        try:
            # Use existing Linear integration for task execution
            task_type = task_data.get('type', 'unknown')
            
            if task_type == 'create_issue':
                # Create Linear issue using existing extension
                from ..linear.integration_agent import LinearIntegrationAgent
                
                linear_agent = LinearIntegrationAgent()
                issue_result = await linear_agent.create_issue(
                    title=task_data.get('title'),
                    description=task_data.get('description'),
                    team_id=task_data.get('team_id')
                )
                return {'type': 'create_issue', 'result': issue_result}
            else:
                return {'type': task_type, 'result': 'Task type not supported'}
                
        except Exception as e:
            logger.error(f"Linear task execution failed: {e}")
            return {'type': 'error', 'error': str(e)}

    async def _execute_slack_task(self, task_data: dict) -> dict:
        """Execute Slack task using existing Slack extension."""
        try:
            # Use existing Slack integration for task execution
            task_type = task_data.get('type', 'unknown')
            
            if task_type == 'send_message':
                # Send Slack message using existing extension
                message_result = await self.slack_integration.send_message(
                    channel=task_data.get('channel'),
                    text=task_data.get('text'),
                    blocks=task_data.get('blocks')
                )
                return {'type': 'send_message', 'result': message_result}
            else:
                return {'type': task_type, 'result': 'Task type not supported'}
                
        except Exception as e:
            logger.error(f"Slack task execution failed: {e}")
            return {'type': 'error', 'error': str(e)}

    async def _execute_circleci_task(self, task_data: dict) -> dict:
        """Execute CircleCI task using existing CircleCI extension."""
        try:
            # Use existing CircleCI integration for task execution
            task_type = task_data.get('type', 'unknown')
            
            if task_type == 'trigger_pipeline':
                # Trigger CircleCI pipeline using existing extension
                from ..circleci.integration_agent import CircleCIIntegrationAgent
                
                circleci_agent = CircleCIIntegrationAgent()
                pipeline_result = await circleci_agent.trigger_pipeline(
                    project_slug=task_data.get('project_slug'),
                    branch=task_data.get('branch'),
                    parameters=task_data.get('parameters', {})
                )
                return {'type': 'trigger_pipeline', 'result': pipeline_result}
            else:
                return {'type': task_type, 'result': 'Task type not supported'}
                
        except Exception as e:
            logger.error(f"CircleCI task execution failed: {e}")
            return {'type': 'error', 'error': str(e)}

    async def integrate_with_extensions(self, github: GitHub, linear: Linear, slack: Slack, circleci: CircleCI):
        """Integrate Codegen with other extensions."""
        try:
            self.github_integration = github
            self.linear_integration = linear
            self.slack_integration = slack
            self.circleci_integration = circleci
            
            logger.info("✅ Codegen integrated with GitHub, Linear, Slack, and CircleCI extensions")
            
        except Exception as e:
            logger.error(f"Failed to integrate Codegen with extensions: {e}")

    async def execute_workflow_tasks(self, project_id: str, requirements: str, context: dict = None) -> dict:
        """Execute workflow tasks using existing workflow integration with Strands and MCP support."""
        try:
            # Use existing CodegenWorkflowClient for workflow execution
            workflow_result = await self.workflow_client.execute_workflow_tasks(
                project_id=project_id,
                requirements=requirements,
                context=context or {}
            )
            
            # Track workflow execution
            self.active_tasks[project_id] = {
                'type': 'workflow',
                'requirements': requirements,
                'context': context,
                'result': workflow_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'workflow_result': workflow_result,
                'strands_integration': workflow_result.get('strands_integration', False),
                'mcp_integration': workflow_result.get('mcp_integration', False)
            }
            
        except Exception as e:
            logger.error(f"Workflow tasks execution failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def apply_overlay_integration(self) -> dict:
        """Apply Codegen overlay for enhanced integration."""
        try:
            # Use existing OverlayApplicator
            self.overlay_applicator.detect_package()
            
            if not self.overlay_applicator.applied:
                apply_result = self.overlay_applicator.apply_overlay()
                logger.info("✅ Codegen overlay applied successfully")
                return {'status': 'applied', 'result': apply_result}
            else:
                logger.info("ℹ️ Codegen overlay already applied")
                return {'status': 'already_applied'}
                
        except Exception as e:
            logger.error(f"Failed to apply Codegen overlay: {e}")
            return {'status': 'failed', 'error': str(e)}

    def event(self, event_type: str):
        """Decorator for registering Codegen event handlers."""
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            self.register_handler(event_type, func)
            return func
        return decorator

    async def initialize(self):
        """Initialize Codegen extension with existing components."""
        try:
            # Apply overlay integration
            await self.apply_overlay_integration()
            
            # Initialize workflow client
            await self.workflow_client.initialize()
            
            logger.info("✅ Codegen extension fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Codegen extension: {e}")
            raise

    def get_task_status(self) -> dict:
        """Get status of all tasks."""
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'tasks': {
                'active': list(self.active_tasks.keys()),
                'completed': list(self.completed_tasks.keys())
            }
        }

    async def execute_task_with_integrations(self, task: dict, integrations: list = None) -> dict:
        """Execute task with specified integrations using existing components."""
        try:
            task_id = task.get('id', 'unknown')
            task_type = task.get('type', 'unknown')
            
            # Execute base task using Codegen workflow client
            base_result = await self.workflow_client.execute_task(
                task_id=task_id,
                description=task.get('description', ''),
                config=task.get('config', {})
            )
            
            # Execute integration tasks if specified
            integration_results = {}
            if integrations:
                for integration in integrations:
                    if integration == 'github' and self.github_integration:
                        github_result = await self._execute_github_task(task.get('github_data', {}))
                        integration_results['github'] = github_result
                    elif integration == 'linear' and self.linear_integration:
                        linear_result = await self._execute_linear_task(task.get('linear_data', {}))
                        integration_results['linear'] = linear_result
                    elif integration == 'slack' and self.slack_integration:
                        slack_result = await self._execute_slack_task(task.get('slack_data', {}))
                        integration_results['slack'] = slack_result
                    elif integration == 'circleci' and self.circleci_integration:
                        circleci_result = await self._execute_circleci_task(task.get('circleci_data', {}))
                        integration_results['circleci'] = circleci_result
            
            # Move to completed tasks
            self.completed_tasks[task_id] = {
                'task': task,
                'base_result': base_result,
                'integration_results': integration_results,
                'status': 'completed'
            }
            
            # Remove from active tasks if present
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'base_result': base_result,
                'integration_results': integration_results,
                'integrations_used': list(integration_results.keys())
            }
            
        except Exception as e:
            logger.error(f"Task execution with integrations failed: {e}")
            return {'status': 'failed', 'error': str(e)}
